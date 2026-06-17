import logging
import os
import random
import re
import threading
import time
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from django.conf import settings
from django.db import IntegrityError, close_old_connections
from fake_useragent import UserAgent
from playwright.sync_api import sync_playwright

from jobscraper.scraper_process import (
    clear_stop_flag,
    is_stop_requested,
    pid_is_alive,
    request_stop,
    spawn_worker,
    terminate_pid,
)

from jobscraper.apply_urls import is_blocked_apply_host, is_valid_apply_url as _valid_apply

from .models import Job, ScraperState
from .time_utils import format_posted_time, is_within_24h

logger = logging.getLogger("scraper")

_stop_event = threading.Event()
_active_browser = None
_active_lock = threading.Lock()
_ua = UserAgent()


def _should_stop():
    return _stop_event.is_set() or is_stop_requested()

JOBS_PER_PAGE = 20


def _close_active_browser():
    global _active_browser
    with _active_lock:
        browser = _active_browser
        _active_browser = None
    if browser:
        try:
            browser.close()
        except Exception:
            pass


def is_scraper_running():
    state = ScraperState.get_singleton()
    return pid_is_alive(state.worker_pid)


def is_usa_location(locations):
    if not locations:
        return False
    for loc in locations:
        s = str(loc).lower()
        if any(
            x in s
            for x in (
                "usa",
                "united states",
                "remote in usa",
                ", us",
                "u.s.",
            )
        ):
            return True
        if re.search(r",\s*[A-Z]{2},\s*USA", str(loc)):
            return True
    return False


def is_valid_apply_url(url, company_url=""):
    return _valid_apply(url, settings.ALLOWED_ATS, company_url=company_url)


def job_exists(title, company, location, apply_url):
    close_old_connections()
    if Job.objects.filter(apply_url=apply_url).exists():
        return True
    return Job.objects.filter(title=title, company=company, location=location).exists()


class SimplifyScraper:
    MULTI_SEARCH = "https://js-ha.simplify.jobs/multi_search?use_cache=true&x-typesense-api-key={key}"
    PER_PAGE = 50

    def __init__(self, resume=False):
        self.resume = resume
        self.state = ScraperState.get_singleton()
        raw = self.state.processed_ids or ""
        self.processed = set(x for x in raw.split(",") if x)
        self.api_key = None
        if resume:
            self._hydrate_processed_from_db()

    def _hydrate_processed_from_db(self):
        """On resume, never re-process Simplify job IDs already saved in DB."""
        close_old_connections()
        before = len(self.processed)
        for sid in Job.objects.exclude(simplify_job_id="").values_list(
            "simplify_job_id", flat=True
        ).iterator(chunk_size=5000):
            if sid:
                self.processed.add(sid)
        added = len(self.processed) - before
        logger.info("Resume: %s IDs in state, +%s from DB (total %s)", before, added, len(self.processed))

    def _cutoff_24h(self):
        return int(time.time()) - 86400

    def _save_state(self, **kwargs):
        close_old_connections()
        for k, v in kwargs.items():
            setattr(self.state, k, v)
        self.state.processed_ids = ",".join(sorted(self.processed)[-80000:])
        self.state.save()

    def _check_stop(self):
        if _should_stop():
            raise StopIteration

    def _human_delay(self, lo=0.25, hi=0.9):
        end = time.time() + random.uniform(lo, hi)
        while time.time() < end:
            if _should_stop():
                raise StopIteration
            time.sleep(0.12)

    def _scroll_page(self, page):
        for _ in range(random.randint(2, 4)):
            page.mouse.wheel(0, random.randint(200, 600))
            end = time.time() + random.uniform(0.2, 0.6)
            while time.time() < end:
                if _should_stop():
                    raise StopIteration
                time.sleep(0.1)

    def _capture_api_key(self, page):
        self._check_stop()
        captured = []

        def on_request(req):
            if "multi_search" in req.url and "x-typesense-api-key=" in req.url:
                captured.append(req.url.split("x-typesense-api-key=")[1].split("&")[0])

        page.on("request", on_request)
        page.goto(
            "https://simplify.jobs/jobs?location=United%20States&experienceLevel="
            "Entry%20Level%2FNew%20Grad%3BJunior%3BMid%20Level",
            wait_until="domcontentloaded",
            timeout=90000,
        )
        self._scroll_page(page)
        page.wait_for_timeout(2000)
        if not captured:
            raise RuntimeError("Could not capture Typesense API key")
        return captured[-1]

    def _search_jobs(self, request_ctx, keyword, page_num):
        self._check_stop()
        cutoff = self._cutoff_24h()
        body = {
            "searches": [
                {
                    "query_by": "title,company_name,functions,locations",
                    "per_page": self.PER_PAGE,
                    "sort_by": "updated_date:desc",
                    "collection": "jobs",
                    "q": keyword,
                    "filter_by": (
                        "countries:=[`United States`] && "
                        "experience_level:=[`Entry Level/New Grad`,`Junior`,`Mid Level`] && "
                        f"updated_date:>{cutoff}"
                    ),
                    "page": page_num,
                }
            ]
        }
        url = self.MULTI_SEARCH.format(key=self.api_key)
        resp = request_ctx.post(url, data=body)
        if resp.status != 200:
            logger.error("Typesense search failed: %s %s status=%s", keyword, page_num, resp.status)
            return [], 0
        data = resp.json()
        result = data["results"][0]
        return result.get("hits", []), result.get("found", 0)

    def _extract_apply_url(self, page, job_id):
        self._check_stop()
        click = f"https://simplify.jobs/jobs/click/{job_id}"
        try:
            if _should_stop():
                return None
            resp = page.context.request.get(click, max_redirects=15, timeout=45000)
            final = resp.url
            if is_blocked_apply_host(final):
                return None
            if resp.ok and is_valid_apply_url(final):
                return final
            page.goto(click, wait_until="domcontentloaded", timeout=45000)
            final = page.url
            if is_blocked_apply_host(final):
                return None
            if is_valid_apply_url(final):
                return final
            soup = BeautifulSoup(page.content(), "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("//"):
                    href = "https:" + href
                if is_blocked_apply_host(href):
                    continue
                if is_valid_apply_url(href):
                    return href
        except Exception as exc:
            logger.warning("ATS fail %s: %s", job_id, exc)
        return None

    def _parse_hit(self, hit):
        doc = hit.get("document", hit)
        locs = doc.get("locations") or []
        loc_str = "; ".join(locs) if locs else "United States"
        updated = doc.get("updated_date")
        start = doc.get("start_date")
        # 24h filter: listing must be recently updated on Simplify
        activity_ts = updated or start
        # Display: prefer start_date (when job went live), fallback to updated
        posted_ts = start or updated
        raw_desc = doc.get("description") or doc.get("job_description") or ""
        description = BeautifulSoup(raw_desc, "html.parser").get_text(separator="\n", strip=True) if raw_desc else ""
        return {
            "id": doc.get("id") or doc.get("posting_id"),
            "title": doc.get("title", "").strip(),
            "company": doc.get("company_name", "").strip(),
            "location": loc_str,
            "locations": locs,
            "updated_date": activity_ts,
            "posted_ts": posted_ts,
            "description": description,
        }

    def _process_keyword(self, page, request_ctx, keyword, ki, total_keywords, start_page=1):
        """Scrape all pages for one keyword. Returns number of jobs saved."""
        saved_before = self.state.jobs_saved
        page_num = max(1, start_page)

        max_pages = getattr(settings, "MAX_PAGES_PER_KEYWORD", 40)
        empty_streak = 0

        while not _should_stop():
            hits, found = self._search_jobs(request_ctx, keyword, page_num)
            if not hits:
                empty_streak += 1
                if empty_streak >= 2:
                    break
                page_num += 1
                continue
            empty_streak = 0

            self._save_state(
                current_page=page_num,
                last_message=f"[{ki + 1}/{total_keywords}] {keyword} — page {page_num} ({found} matches)",
            )
            logger.info("[%s/%s] %s page %s: %s hits (found %s)", ki + 1, total_keywords, keyword, page_num, len(hits), found)

            saved_this_page = 0
            for hit in hits:
                if _should_stop():
                    raise StopIteration
                job = self._parse_hit(hit)
                jid = job["id"]
                if not jid or jid in self.processed:
                    continue
                if not is_usa_location(job["locations"]):
                    continue
                if not is_within_24h(job["updated_date"]):
                    continue

                posted_label = format_posted_time(job["posted_ts"])
                if not posted_label:
                    continue

                self.processed.add(jid)
                self._human_delay(0.15, 0.5)

                apply_url = self._extract_apply_url(page, jid)
                if not apply_url:
                    self.state.jobs_skipped += 1
                    self._save_state(jobs_skipped=self.state.jobs_skipped)
                    continue

                if job_exists(job["title"], job["company"], job["location"], apply_url):
                    self.state.jobs_skipped += 1
                    self._save_state(jobs_skipped=self.state.jobs_skipped)
                    continue

                close_old_connections()
                try:
                    Job.objects.create(
                        title=job["title"],
                        company=job["company"],
                        location=job["location"],
                        apply_url=apply_url,
                        source="Simplify Jobs",
                        keyword=keyword,
                        posted_time=posted_label,
                        posted_at=int(job["posted_ts"]),
                        simplify_job_id=jid,
                        description=job.get("description", ""),
                    )
                except IntegrityError:
                    self.state.jobs_skipped += 1
                    self._save_state(jobs_skipped=self.state.jobs_skipped)
                    logger.info("Duplicate skipped (DB): %s", apply_url[:80])
                    continue
                self.state.jobs_saved += 1
                saved_this_page += 1
                self._save_state(jobs_saved=self.state.jobs_saved)
                logger.info("Saved: %s @ %s (%s)", job["title"], job["company"], posted_label)

            max_page = max(1, (found + self.PER_PAGE - 1) // self.PER_PAGE)
            if page_num >= max_page or page_num >= max_pages:
                break
            if saved_this_page == 0 and page_num >= 3:
                break
            page_num += 1
            self._human_delay(0.4, 0.8)

        return self.state.jobs_saved - saved_before

    def _scrape_role_requests(self, page, request_ctx) -> None:
        from role_requests import fetch_pending_role_requests, notify_role_complete
        pending = fetch_pending_role_requests()
        if not pending:
            return
        logger.info("Role requests: %d role(s) to scrape", len(pending))
        for req in pending:
            self._check_stop()
            role = req["normalized_role"]
            terms = req["search_terms"] or []
            saved_before = self.state.jobs_saved
            for i, term in enumerate(terms):
                self._check_stop()
                try:
                    self._process_keyword(page, request_ctx, term, i, len(terms))
                except StopIteration:
                    raise
                except Exception as exc:
                    logger.error("Role request term failed '%s': %s", term, exc)
            notify_role_complete(role, self.state.jobs_saved - saved_before)

    def run(self):
        global _active_browser
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        close_old_connections()
        keywords = list(settings.KEYWORDS)
        total = len(keywords)
        start_idx = self.state.keyword_index if self.resume else 0

        if not self.resume:
            self.processed.clear()
            self._save_state(
                status=ScraperState.STATUS_RUNNING,
                keyword_index=0,
                current_page=1,
                jobs_saved=0,
                jobs_skipped=0,
                last_message=f"Starting — {total} keywords (24h USA only)",
            )
        else:
            kw = self.state.current_keyword or (keywords[start_idx] if start_idx < total else "")
            pg = max(1, self.state.current_page)
            self._save_state(
                status=ScraperState.STATUS_RUNNING,
                last_message=(
                    f"Resuming keyword {start_idx + 1}/{total}: '{kw}' from page {pg}"
                ),
            )

        logger.info(
            "Scraper started (resume=%s) keyword %s/%s page %s",
            self.resume,
            start_idx + 1,
            total,
            self.state.current_page if self.resume else 1,
        )

        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                with _active_lock:
                    _active_browser = browser
                context = browser.new_context(
                    user_agent=_ua.random,
                    viewport={"width": 1400, "height": 900},
                )
                page = context.new_page()
                request_ctx = context.request

                try:
                    self.api_key = self._capture_api_key(page)

                    self._scrape_role_requests(page, request_ctx)

                    for ki in range(start_idx, total):
                        self._check_stop()
                        keyword = keywords[ki]
                        start_page = 1
                        if self.resume and ki == start_idx:
                            start_page = max(1, self.state.current_page)
                        self._save_state(
                            current_keyword=keyword,
                            keyword_index=ki,
                            current_page=start_page,
                            last_message=f"[{ki + 1}/{total}] Searching: {keyword} (page {start_page})",
                        )

                        try:
                            n_saved = self._process_keyword(
                                page, request_ctx, keyword, ki, total, start_page=start_page
                            )
                            self._save_state(
                                keyword_index=ki + 1,
                                current_page=1,
                                last_message=f"[{ki + 1}/{total}] Done '{keyword}' — +{n_saved} jobs (24h)",
                            )
                            logger.info("Finished keyword %s/%s: %s (+ %s jobs)", ki + 1, total, keyword, n_saved)
                        except StopIteration:
                            raise
                        except Exception as exc:
                            logger.exception("Keyword failed %s: %s", keyword, exc)
                            self._save_state(
                                keyword_index=ki + 1,
                                last_message=f"[{ki + 1}/{total}] Error on '{keyword}': {str(exc)[:120]}",
                            )

                        self.resume = False
                        if not _should_stop():
                            self._human_delay(0.5, 1.0)

                finally:
                    try:
                        context.close()
                    except Exception:
                        pass
                    try:
                        browser.close()
                    except Exception:
                        pass
                    with _active_lock:
                        _active_browser = None

                if not _should_stop():
                    self._save_state(
                        status=ScraperState.STATUS_IDLE,
                        keyword_index=total,
                        current_keyword="",
                        last_message=f"Completed all {total} keywords (24h USA jobs only)",
                    )
                    logger.info("Scraper finished all %s keywords", total)

        except StopIteration:
            kw = self.state.current_keyword or "—"
            pg = max(1, self.state.current_page)
            ki = self.state.keyword_index
            self._save_state(
                status=ScraperState.STATUS_STOPPED,
                keyword_index=ki,
                current_page=pg,
                last_message=(
                    f"Stopped — Resume will continue keyword {ki + 1}: '{kw}' page {pg}"
                ),
            )
            logger.info("Scraper stopped at keyword %s page %s", kw, pg)
        except Exception as exc:
            if _should_stop():
                self._save_state(status=ScraperState.STATUS_STOPPED, last_message="Scraper stopped by user")
            else:
                self._save_state(status=ScraperState.STATUS_STOPPED, last_message=str(exc)[:500])
                logger.exception("Scraper error: %s", exc)
        finally:
            _close_active_browser()


def start_scraper(resume=False):
    if is_scraper_running():
        return False, "Scraper already running (separate process)"

    clear_stop_flag()
    _stop_event.clear()
    state = ScraperState.get_singleton()
    total = len(settings.KEYWORDS)
    if not resume:
        close_old_connections()
        deleted, _ = Job.objects.all().delete()
        state.status = ScraperState.STATUS_RUNNING
        state.keyword_index = 0
        state.current_page = 1
        state.current_keyword = ""
        state.jobs_saved = 0
        state.jobs_skipped = 0
        state.processed_ids = ""
        state.last_message = (
            f"Fresh start — deleted {deleted} jobs, keyword 1/{total}"
        )
        start_msg = (
            f"Started fresh: cleared {deleted} jobs, scraping from keyword 1/{total}"
        )
    else:
        start_msg = None
        state.status = ScraperState.STATUS_RUNNING
        kw = state.current_keyword or "—"
        pg = max(1, state.current_page)
        idx = state.keyword_index
        state.last_message = (
            f"Resuming keyword {idx + 1}/{total}: '{kw}' from page {pg} (no duplicates)"
        )

    pid = spawn_worker(resume=resume)
    state.worker_pid = pid
    state.save()
    if start_msg:
        return True, start_msg
    return True, (
        f"Resumed in background (PID {pid}) — continues from saved keyword/page"
    )


def stop_scraper():
    state = ScraperState.get_singleton()
    if not is_scraper_running() and state.status != ScraperState.STATUS_RUNNING:
        return True, "Scraper is not running"

    request_stop()
    _stop_event.set()
    terminate_pid(state.worker_pid)
    state.worker_pid = 0
    kw = state.current_keyword or "—"
    pg = max(1, state.current_page)
    idx = state.keyword_index
    state.status = ScraperState.STATUS_STOPPED
    state.worker_pid = 0
    state.last_message = (
        f"Stopped — click Resume to continue keyword {idx + 1}: '{kw}' page {pg}"
    )
    state.save()
    logger.info("Stop requested for Simplify worker")
    return True, "Scraper stopped"
