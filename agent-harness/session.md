# Session

## Current Goal

You First Gersh Influencer Insights Platform v1: daily Instagram + trend scraper,
metrics + Gemini creative recommendations, password-gated Next.js platform.

## Current State

**Built, verified with mocks/manual browser driving, pending live credential
verification.** All three pillars are implemented:

- `scraper/` — Instaloader-based Instagram scraper + trend-report scraper + Supabase
  writer + Gemini recommendation generator, orchestrated by `run_daily.py` with a
  once-per-day guard. 24/24 pytest tests pass (all mocked).
- `scraper/com.youfirstgersh.dailyscraper.plist` + `install_launchagent.sh` — daily
  `launchd` scheduling, not yet installed (needs real credentials first).
- `platform/` — Next.js app, password-gated via `proxy.ts` (Next 16's renamed
  Middleware) checking an HMAC-signed session cookie. Roster, per-influencer, and
  trends pages read from Supabase server-side. Verified end-to-end in a real browser
  via Playwright MCP tools: wrong password rejected, correct password (`LAYCC`) grants
  access, session persists, logout works, unauthenticated redirect works, unknown
  influencer 404s. `next build`/`tsc`/`eslint` all clean.

## What's NOT yet done

- No live run against real Instagram, Supabase, or Gemini — blocked on the user
  creating a Supabase project and providing `SUPABASE_URL`/`SUPABASE_SERVICE_KEY`, plus
  a `GOOGLE_API_KEY`.
- No checked-in Playwright suite for `platform/` yet (this session used manual
  MCP-driven browser verification instead — see `findings.md`).
- The Evaluator pass in `findings.md` was same-session, not a separate subagent per
  `contract.md` — treat it as provisional.

## Next Action

Once the user provides Supabase + Google credentials: run the scraper manually, verify
real Supabase rows, install the LaunchAgent, then point the platform at the same
Supabase project and verify real data renders. See `progress.json.next_actions`.

## Important Context

- One active harness session at a time.
- Harness files are git-tracked — never write API keys, Supabase service keys, or
  scraped personal data into them.
- Trivial changes (one-liners, typos, renames) skip the harness.

## Files Changed

`CONSTITUTION.md`, `CLAUDE.md`, `agent-harness/*`; `scraper/*` (new package);
`platform/*` (new Next.js app).

---

*This file is overwritten at the start of each session. History is in git.*
