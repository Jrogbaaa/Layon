# Spec

## Goal of This Change

Make the daily Instagram scrape resilient to failures and incapable of silently writing
bad data. Five concrete mechanisms (feature_010, "Phase 1" of the scraper-reliability
audit, 2026-07-13):

1. **Same-day retry of failed handles.** `mark_ran_today()` only fires when every roster
   handle succeeded. The launchd plist gains two extra fire times (13:00, 17:00) so an
   incomplete morning run is re-attempted the same day. Retry runs are idempotent
   per-handle: a handle with a profile snapshot already captured today is skipped, so no
   handle is ever scraped more than once per day (contract: no scraping more than once
   daily).
2. **Run-completeness alerting.** At the end of each run, if any roster handle is missing
   today's snapshot, log an ERROR summary and fire a macOS notification (osascript) so a
   failure is visible without opening log files.
3. **Fail loud on Instagram response-shape drift.** `_comment_count` raises instead of
   silently returning 0 when the `comments` key is missing from the timeline node.
   `_view_count` logs a warning when a video post has no view-count key (still returns
   None — views are genuinely absent on some posts).
4. **Anomaly gate before profile writes.** Before inserting a profile snapshot, compare
   against the latest stored snapshot: reject (raise, handle marked failed and retried
   later) if followers is missing/zero or swings more than 50% day-over-day. A rejected
   snapshot is never written; the alert in (2) surfaces it.
5. **Transient-error retry + session-expiry distinction.** `scrape_profile` calls get up
   to 3 attempts with backoff for connection-class errors. Instaloader login/challenge
   exceptions abort the whole roster loop immediately with a distinct "session expired —
   re-login required" alert instead of grinding through identical per-handle failures.

## Why This Matters

The scraper is the platform's sole data source. The 2026-07-08 run failed for all five
influencers (network outage at fire time), marked itself complete anyway, never retried,
and alerted no one — that day's data is permanently gone. Four other days that week were
partially missing. Separately, the private-field reads (`post._node`) default to 0/None
on shape changes, which would silently corrupt every engagement metric downstream.

## Intended User

Agency staff (data completeness/trust) and the developer operating the pipeline.

## Non-Goals

- No Instagram Graph API migration (Phase 2 — explicitly declined by the user).
- No third-party scraping APIs, no email/webhook infrastructure, no new dependencies.
- No change to scrape volume: each handle at most once per day, same post counts, same
  20s pacing (roster-growth pacing/jitter work is out of scope).
- No restructuring of the per-handle write sequence (raw vs derived split — audit H3).
- No platform/UI staleness indicator (audit M5).
- No automatic wiring of `backfill.py` (deep history catch-up stays manual; same-day
  retry above covers daily gaps).

## Success Criteria

1. A run where any handle fails does NOT write `.last_run`; a later same-day run
   re-attempts only the missed handles and marks the day done once all have snapshots.
2. Plist has 9:00 / 13:00 / 17:00 fire times; a fully successful 9:00 run makes the
   later fires no-ops via the existing `already_ran_today()` guard.
3. An incomplete run produces an ERROR log line naming the missing handles and posts a
   macOS notification.
4. `_comment_count` raises on a missing `comments` key (test asserts this); a video
   node with no view key logs a warning.
5. A profile payload with followers 0/None, or >50% away from the latest stored
   snapshot, is rejected before insert (tests assert both rejection and normal pass).
6. Connection-class errors are retried up to 3 attempts with backoff;
   login/challenge exceptions abort the roster loop with the distinct session alert
   (tests assert both).
7. pytest green in `scraper/` (existing + new tests).

## Open Questions

None — mechanism choices (extra launchd fire times, osascript notification, 50%
threshold, 3 attempts) recorded in decisions.md; all reversible constants.
