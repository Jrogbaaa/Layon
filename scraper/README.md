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
Create a reusable session by importing your browser's trusted cookies — log into
instagram.com in Chrome (a normal window, stay logged in), then run:

```bash
pip install browser_cookie3   # one-time dependency for cookie import
.venv/bin/instaloader --load-cookies Chrome
```

This saves a session file under `~/.config/instaloader/`. Then set
`IG_USERNAME=YOUR_INSTAGRAM_USERNAME` in `.env`.
Use a dedicated agency account rather than a personal one if possible.

Do NOT use `instaloader --login=...`: Instagram checkpoint-blocks its login endpoint
for this account (each retry re-arms the block, and browser verification does not
clear it — learned the hard way on 2026-07-15). The cookie import above skips that
endpoint entirely. If the session ever dies again (the scraper sends a macOS
notification), repeat the cookie import — never retry `--login`.

## Run manually

```bash
.venv/bin/python -m youfirst_scraper.run_daily
```

Safe to re-run the same day — it will log "already ran today" and exit.

## Run once a day automatically (macOS)

```bash
./install_launchagent.sh
```

This installs a LaunchAgent that fires daily at 09:00, 13:00, and 17:00. The later
fires exist to retry handles the 09:00 run missed: a run only writes `.last_run` when
every roster handle succeeded, and retry runs skip handles already captured today, so
no handle is scraped more than once per day. If the Mac is asleep at a fire time,
`launchd` runs the job on next wake. An incomplete run logs an ERROR and posts a macOS
notification naming the missing handles.

To check status: `launchctl list | grep youfirstgersh`
To uninstall: `launchctl unload ~/Library/LaunchAgents/com.youfirstgersh.dailyscraper.plist`

## Tests

```bash
.venv/bin/python -m pytest
```
