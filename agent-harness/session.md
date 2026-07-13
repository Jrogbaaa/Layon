# Session

## Current Goal

feature_010 — scraper reliability hardening: same-day retry, alerting, fail-loud on
shape drift, anomaly gate, session-expiry handling (see spec.md).

## Current State

**Built, evaluated (PASS, avg 4.75), and live-verified 2026-07-13.**

- `run_daily.py`: `run_instagram_scrape` returns failed handles; per-handle skip via new
  `db.profile_scraped_today`; `_scrape_with_retry` (3 attempts, linear 30s/60s backoff,
  no retry on 429/session death); `_validate_profile` anomaly gate (followers 0/None or
  >50% day-over-day swing rejected); `_notify` macOS notification; `main()` only writes
  `.last_run` on a complete roster, else logs ERROR + notifies.
- `instagram_scraper.py`: `_comment_count` raises on missing key; `_view_count` warns.
- Plist: fires 9:00/13:00/17:00 (later fires retry missed handles).
- pytest 144/144; Evaluator findings in findings.md (non-blocking follow-ups: treat
  all-handles ProfileNotExistsException as probable session death; partial-write
  finalization gap deferred with audit H3).
- Live verification: healed the real 2026-07-13 dante_caro gap — retry run skipped the
  4 already-captured handles, scraped only the missing one, then marked the day done.

## Next Action

User: re-run `scraper/install_launchagent.sh` once so launchd picks up the new
13:00/17:00 fire times. Changes are uncommitted on
`feature/trend-grounded-recommendations`.

---

*This file is overwritten at the start of each session. History is in git.*
