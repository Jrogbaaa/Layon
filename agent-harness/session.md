# Session

## Current Goal

You First Gersh Influencer Insights Platform v1: daily Instagram + trend scraper,
metrics + Gemini creative recommendations, password-gated Next.js platform.

## Current State

**Paused on a real external blocker: Instagram profile scraping doesn't work right
now, for anyone, via Instaloader.**

What's confirmed working against the real, live Supabase project (not mocks):
- Schema applied, all 5 tables reachable.
- Trend scraper: wrote real rows for both configured trend sources.
- Gemini API key: confirmed working with a real `generate_content` call.
- Platform: password gate, session persistence, logout, 404s — all verified in a real
  browser via Playwright MCP.

What's blocked: **Instagram scraping fails for every handle**, including
verified-real, massively public accounts (`cristiano`), even with an authenticated
session (`beautifullfootball`, logged in via `instaloader --login`). Instagram returns
`200 OK` with an empty GraphQL body; Instaloader misreports this as
`ProfileNotExistsException`. Confirmed via web research this is
[instaloader/instaloader#2682](https://github.com/instaloader/instaloader/issues/2682),
a known, currently unresolved upstream bug — not a bug in this codebase, not a wrong
handle. An unmerged fix (PR #2652) exists with no official release.

User was offered three paths (paid scraping API, unmerged PR branch, or pause) and
chose to **pause here** rather than commit to either workaround yet.

## Next Action

Wait for the user's decision on how to handle the Instagram blocker (see
`decisions.md` 2026-07-06 entry and `progress.json.next_actions`). No further scraper
work should start until that's resolved — the code itself (session loading, per-handle
error isolation, metrics, recommendations) is correct and doesn't need changes for this
issue.

## Important Context

- One active harness session at a time.
- Harness files are git-tracked — never write API keys, Supabase service keys, or
  scraped personal data into them.
- `scraper/.env` and `platform/.env.local` now hold real credentials (Supabase, Gemini,
  IG_USERNAME) — both gitignored, confirmed not committed.
- Trivial changes (one-liners, typos, renames) skip the harness.

## Files Changed (this session, since last commit)

`scraper/youfirst_scraper/config.py`, `instagram_scraper.py`, `run_daily.py` (added
`IG_USERNAME` + `build_loader()`); `scraper/tests/test_instagram_scraper.py` (3 new
tests); `scraper/.env.example`, `scraper/README.md` (login instructions).

---

*This file is overwritten at the start of each session. History is in git.*
