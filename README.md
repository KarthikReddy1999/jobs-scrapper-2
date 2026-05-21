# Simplify Jobs USA Scraper

Standalone Django app — **port 8000**, own `db.sqlite3`, no shared code with Jobright or MigrateMate.

| | Simplify | Jobright | MigrateMate |
|---|----------|----------|-------------|
| Folder | `simplify/` | `../Jobright_new/` | `../MigrateMate_new/` |
| Port | **8000** | **8001** | **8002** |

See `../PROJECTS.md` for running all three.

## What it does

- Scrapes [simplify.jobs](https://simplify.jobs) via Playwright (Typesense search API in-browser).
- **~82 keywords** in `jobscraper/settings.py`.
- Filters: **USA**, **last 24 hours**, experience **0–5 years** (Entry / Junior / Mid).
- Apply URL: `https://simplify.jobs/jobs/click/{id}` redirect → **company career page or ATS only** (LinkedIn / job boards blocked).
- Typical yield: **thousands of jobs** per full run (high listing volume vs Jobright/MigrateMate).
- Duplicate protection: unique `apply_url` + title/company/location.

## Setup

```powershell
cd simplify
pip install -r requirements.txt
playwright install chromium
python manage.py migrate
python manage.py runserver 8000 --noreload
```

Or double-click `start_server.bat`.

Dashboard: **http://127.0.0.1:8000/**

## Dashboard

| Button | Action |
|--------|--------|
| **Start** | Clear all jobs, reset state, scrape from keyword 1 |
| **Resume** | Continue from last keyword/page (no duplicates) |
| **Stop** | Save progress and stop background worker |
| **Clear All Jobs** | Delete jobs only (scraper must be stopped) |

Use **`--noreload`** when the scraper is running so Django reload does not kill the browser worker.

## Management commands

```powershell
python manage.py run_simplify_scraper          # foreground scraper
python manage.py run_simplify_scraper --resume
python manage.py purge_invalid_apply_urls      # remove LinkedIn / blocked board URLs
```

## Configuration (`jobscraper/settings.py`)

- `KEYWORDS` — search titles
- `MAX_PAGES_PER_KEYWORD` — default **40** (more pages = more jobs, slower run)
- `ALLOWED_ATS` — accepted apply hosts after redirect

## Logs

- `logs/scraper.log` — scraper output (not committed; see `.gitignore`)

## Admin

http://127.0.0.1:8000/admin/ — optional `createsuperuser` for `Job` / `ScraperState`.
