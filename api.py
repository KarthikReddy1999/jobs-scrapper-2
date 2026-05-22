"""FastAPI wrapper for Simplify scraper — deployed on Hugging Face Spaces (port 7860)."""
import asyncio
import logging
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobscraper.settings")
import django
django.setup()

from fastapi import FastAPI, Header, HTTPException

from jobs.models import Job, ScraperState
from jobs.scraper import is_scraper_running, start_scraper, stop_scraper
from supabase_push import push_jobs_to_supabase

app = FastAPI(title="Simplify Scraper", version="1.0.0")
logger = logging.getLogger(__name__)

API_SECRET = os.environ["WEBHOOK_SECRET"]


async def _push_when_done() -> None:
    """Poll until the scraper subprocess finishes, then push all jobs to Supabase."""
    while is_scraper_running():
        await asyncio.sleep(30)
    state = ScraperState.get_singleton()
    logger.info("Scraper finished — %d jobs saved — pushing to Supabase", state.jobs_saved)
    try:
        push_jobs_to_supabase()
    except Exception as exc:
        logger.error("Supabase push failed: %s", exc)


@app.get("/")
def health():
    state = ScraperState.get_singleton()
    return {
        "status": "running",
        "service": "simplify-scraper",
        "scraper_status": state.status,
        "jobs_saved": state.jobs_saved,
    }


@app.post("/scrape/all")
async def trigger_scrape(x_api_key: str = Header(None)):
    """Start a fresh scrape run (GitHub Actions cron calls this every hour)."""
    _check_auth(x_api_key)
    if is_scraper_running():
        return {"status": "already_running"}
    ok, msg = start_scraper(resume=False)
    if ok:
        asyncio.create_task(_push_when_done())
    return {"status": "started" if ok else "error", "message": msg}


@app.post("/scrape/stop")
async def stop(x_api_key: str = Header(None)):
    _check_auth(x_api_key)
    ok, msg = stop_scraper()
    return {"status": "stopped" if ok else "error", "message": msg}


@app.get("/status")
def status(x_api_key: str = Header(None)):
    _check_auth(x_api_key)
    state = ScraperState.get_singleton()
    return {
        "scraper_status": state.status,
        "current_keyword": state.current_keyword,
        "keyword_index": state.keyword_index,
        "jobs_saved": state.jobs_saved,
        "jobs_skipped": state.jobs_skipped,
        "running": is_scraper_running(),
    }


def _check_auth(key: str | None) -> None:
    if key != API_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
