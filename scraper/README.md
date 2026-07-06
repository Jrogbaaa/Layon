# You First Gersh — Scraper

Daily pipeline: scrapes the Instagram roster + trend-report sources, computes metrics,
and generates Gemini creative recommendations. Writes everything to Supabase.

## Setup

```bash
cd scraper
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # fill in SUPABASE_URL, SUPABASE_SERVICE_KEY, GOOGLE_API_KEY
```

Run the Supabase schema once against your project (SQL Editor, or `supabase db push`):
`schema.sql`.

Edit `influencers.txt` to change the roster.

### Instagram login (required — anonymous scraping is blocked)

Instagram aggressively blocks not-logged-in scraping (403 on public GraphQL queries).
Create a reusable session once, interactively, in your own terminal — this codebase
never sees or stores your password:

```bash
.venv/bin/instaloader --login=YOUR_INSTAGRAM_USERNAME
```

This prompts for your password (and 2FA if enabled) and saves a session file under
`~/.config/instaloader/`. Then set `IG_USERNAME=YOUR_INSTAGRAM_USERNAME` in `.env`.
Use a dedicated agency account rather than a personal one if possible.

## Run manually

```bash
.venv/bin/python -m youfirst_scraper.run_daily
```

Safe to re-run the same day — it will log "already ran today" and exit.

## Run once a day automatically (macOS)

```bash
./install_launchagent.sh
```

This installs a LaunchAgent that fires daily at 09:00. If the Mac is asleep at that
time, `launchd` runs the job on next wake — no need to have the laptop open at an exact
moment. `run_daily.py`'s own `already_ran_today()` guard prevents double-running if the
Mac wakes more than once in a day.

To check status: `launchctl list | grep youfirstgersh`
To uninstall: `launchctl unload ~/Library/LaunchAgents/com.youfirstgersh.dailyscraper.plist`

## Tests

```bash
.venv/bin/python -m pytest
```
