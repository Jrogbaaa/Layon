# Spec

## Goal of This Change

Build the Phase 1 daily data pipeline: scrape the 6-influencer Instagram roster and the
2 trend-report sources, and persist everything to Supabase.

## Why This Matters

This is the foundation the other two pillars (recommendations, dashboard) depend on.
Without reliable daily snapshots, there are no metrics to show and no fresh trend
context to ground creative recommendations in.

## Intended User

Developer (this pipeline has no direct UI — it's the data layer). Indirect beneficiary:
agency staff and talent, who will read the resulting data via the platform in a later
phase.

## Success Criteria

1. Supabase schema exists (`influencers`, `profile_snapshots`, `post_snapshots`,
   `trend_snapshots`, `recommendations`) matching `scraper/schema.sql`.
2. `scraper/` Python package, run manually, produces one `profile_snapshots` row and up
   to ~12 `post_snapshots` rows per handle in `influencers.txt` (the 6 roster handles),
   using Instaloader.
3. A separate trend scraper fetches both trend URLs and stores one `trend_snapshots` row
   per source per run.
4. Re-running the same day does not duplicate `trend_snapshots` rows for the same source
   (idempotent per day); profile/post snapshots are append-only (time series by design).
5. If one influencer handle fails (typo, private, rate-limited), the run logs the failure
   and continues with the remaining handles — it does not abort the whole run.
6. If one trend source fails, the run logs it and continues with the Instagram scrape
   (and vice versa).
7. Config (Supabase URL/key, roster list) lives in `.env` / `influencers.txt`, never
   hardcoded.
8. A `launchd` LaunchAgent plist exists that runs the pipeline once daily
   (`StartCalendarInterval`) and skips re-running if it already ran today.
9. pytest suite exists for the scraper's pure logic (metric calculations, idempotency
   guard, error-skip behavior) using mocked Instaloader/requests/Supabase calls.

## Non-Goals / Out of Scope

- No recommendations generation yet (Phase 2 — separate spec).
- No web platform / dashboard yet (Phase 3 — separate spec).
- No influencer-brand matching (permanently out of scope, see CONSTITUTION.md).
- No cloud-hosted scheduler — `launchd` only, per CONSTITUTION.md.
- No Instagram login/session persistence beyond what Instaloader needs for public-profile
  scraping (no attempt to access private accounts).
- No retry-with-backoff beyond simple conservative delays between requests.

## Open Questions

None — scope confirmed with the user (Instaloader, Supabase, Gemini for later phases,
launchd daily schedule, the two named trend URLs).
