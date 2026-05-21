"""Apply URL rules: company career pages and ATS only — never LinkedIn/job boards."""
import re
from urllib.parse import urlparse

# Never allow as Apply link
BLOCKED_HOST_PARTS = (
    "linkedin.com",
    "lnkd.in",
    "licdn.com",
    "indeed.com",
    "glassdoor.com",
    "ziprecruiter.com",
    "monster.com",
    "careerbuilder.com",
    "dice.com",
    "simplyhired.com",
    "talent.com",
    "jooble.org",
    "flexjobs.com",
    "theladders.com",
    "builtin.com",
    "wellfound.com",
    "angellist.com",
)

BLOCKED_SITE_PARTS = (
    "jobright.ai",
    "jobright.com",
    "simplify.jobs",
)

# Company / ATS career platforms (not LinkedIn)
EMPLOYER_PLATFORM_HOST_PARTS = (
    "greenhouse.io",
    "lever.co",
    "myworkdayjobs.com",
    "myworkdaysite.com",
    "ashbyhq.com",
    "smartrecruiters.com",
    "bamboohr.com",
    "icims.com",
    "jobvite.com",
    "taleo.net",
    "successfactors.com",
    "oraclecloud.com",
    "pinpointhq.com",
    "amazon.jobs",
    "careers.microsoft.com",
    "apply.careers.microsoft.com",
    "rippling.com",
    "workable.com",
    "recruitee.com",
    "jobs2web.com",
    "metacareers.com",
    "ultipro.com",
    "paylocity.com",
    "dayforcehcm.com",
    "csod.com",
)

CAREER_PATH_SEGMENTS = frozenset(
    {
        "jobs",
        "job",
        "careers",
        "career",
        "apply",
        "positions",
        "position",
        "openings",
        "opening",
        "requisition",
        "requisitions",
        "opportunities",
        "vacancies",
        "vacancy",
        "roles",
        "role",
        "join-us",
        "work-with-us",
        "open-positions",
        "postings",
        "posting",
        "employment",
        "recruit",
        "hiring",
        "jobdetail",
        "candidateexperience",
    }
)


def _host(url):
    return urlparse(url).netloc.lower().replace("www.", "", 1)


def _path_segments(url):
    path = urlparse(url).path.lower().strip("/")
    if not path:
        return []
    return [s for s in path.split("/") if s]


def is_blocked_apply_host(url):
    if not url:
        return True
    low = url.lower()
    for part in BLOCKED_SITE_PARTS:
        if part in low:
            return True
    host = _host(url)
    if not host:
        return True
    for blocked in BLOCKED_HOST_PARTS:
        b = blocked.split("/")[0]
        if b in host or host.endswith("." + b):
            return True
    return False


def _company_hosts(company_url):
    if not company_url or not str(company_url).startswith("http"):
        return set()
    netloc = urlparse(company_url).netloc.lower()
    if not netloc:
        return set()
    base = netloc.replace("www.", "", 1)
    return {netloc, base, f"www.{base}"}


def _host_on_company_domain(host, company_url):
    company_hosts = _company_hosts(company_url)
    if not company_hosts:
        return False
    h = host.replace("www.", "", 1)
    for ch in company_hosts:
        cb = ch.replace("www.", "", 1)
        if h == cb or h.endswith(f".{cb}"):
            return True
    return False


def _has_career_segment(url):
    segs = _path_segments(url)
    if not segs:
        return False
    if any(s in CAREER_PATH_SEGMENTS for s in segs):
        return True
    low = url.lower()
    return "jobdetail" in low or "candidateexperience" in low


def _is_ats_url(url, ats_domains):
    host = _host(url)
    for domain in ats_domains:
        d = domain.lower().lstrip(".")
        if host == d or host.endswith("." + d) or d in host:
            return True
    return False


def _is_employer_platform_url(url):
    host = _host(url)
    for part in EMPLOYER_PLATFORM_HOST_PARTS:
        if part in host:
            return _has_career_segment(url)
    if host.endswith("google.com") and "/careers/" in url.lower():
        return True
    return False


def is_valid_apply_url(url, ats_domains, company_url=""):
    """
    Allowed: ATS + employer career platforms + company's own career site.
    Blocked: LinkedIn and job aggregators only.
    """
    if not url or not str(url).strip().startswith("http"):
        return False
    url = url.strip()
    if is_blocked_apply_host(url):
        return False

    host = _host(url)
    if _is_ats_url(url, ats_domains) or _is_employer_platform_url(url):
        return True

    if company_url and _host_on_company_domain(host, company_url):
        if _has_career_segment(url):
            return True
        if re.search(r"/(jobs?|positions?|openings?|requisitions?)/[^/]+", urlparse(url).path, re.I):
            return True

    return False


def is_valid_final_apply_url(url, ats_domains, company_url=""):
    return is_valid_apply_url(url, ats_domains, company_url)
