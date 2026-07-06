# Session

## Current Goal

You First Gersh Influencer Insights Platform v1: daily Instagram + trend scraper,
metrics + Gemini creative recommendations, password-gated Next.js platform.

## Current State

**Instagram scraping blocker resolved — real data now flowing end-to-end into Supabase.**

What's confirmed working against the real, live Supabase project (not mocks):
- Schema applied, all 5 tables reachable.
- Trend scraper: wrote real rows for both configured trend sources.
- Gemini API key: confirmed working with a real `generate_content` call.
- Platform: password gate, session persistence, logout, 404s — all verified in a real
  browser via Playwright MCP.
- **Instagram scraping: 6 of 6 roster handles now scrape successfully**, after
  correcting a wrong roster handle (`ferminadueleguer` -> `ferminaldeguer_54`, confirmed
  via a real profile lookup). `dante_caro`, `mariavalero`, `antonlofer`,
  `ferminaldeguer_54`: 12 posts each with real likes/comments/captions;
  `cristinapedroche`, `mariaacosta`: profile data, 0 posts — genuinely no public posts.
  Full `run_daily` pipeline run end-to-end, writing real `profile_snapshots`,
  `post_snapshots`, and `recommendations` rows for all 6.
- **Platform verified against real data via Playwright**: Roster page lists all 6
  influencers with real follower counts; influencer detail page
  (`/influencer/ferminaldeguer_54`) renders real stats (412,693 followers, 8.1%
  engagement), post-format breakdown, and a full bilingual Gemini creative
  recommendation. `platform/.env.local` already pointed at the same Supabase project as
  `scraper/.env` — no config change needed.

Fix: replaced the `instaloader --login` session (broken per #2682 — Instagram serves
empty GraphQL bodies to it) with a session built from live cookies extracted out of the
user's already-authenticated `beautifullfootball` session in the Comet browser
(`browser_cookie3` + macOS Keychain). Also fixed a second bug this surfaced: Instaloader's
`post.comments` property expects a field this endpoint doesn't return, forcing a broken
fallback fetch — `instagram_scraper.py` now reads the comment count directly from the
timeline edge instead. See `decisions.md` 2026-07-06 "Instagram scraping unblocked" entry
for full detail.

## Next Action

Browser-cookie sessions can degrade over time (per the upstream issue thread) — if the
daily run starts failing again, re-extract cookies from a fresh browser login first;
Apify remains the fallback if that stops working too. Remaining v1 work: install the
launchd LaunchAgent (`install_launchagent.sh`), then deploy the platform to Vercel.

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
tests); `scraper/.env.example`, `scraper/README.md` (login instructions);
`instagram_scraper.py` again (`_comment_count()` fix, this session).
Not in git: `~/.config/instaloader/session-beautifullfootball` replaced with a
browser-cookie-derived session (old one kept as a timestamped `.bak` alongside it).

---

*This file is overwritten at the start of each session. History is in git.*
