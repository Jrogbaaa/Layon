# Findings — feature_010 Scraper Reliability Hardening (retry, alerting, anomaly gates)

## Verdict: PASS

**Evaluator:** separate subagent pass (fresh context, per contract.md/evaluator.md).

## Restated Goal / Non-Goals / Acceptance Criteria

**Goal:** Make the daily Instagram scrape resilient and incapable of silently writing
bad data, via five mechanisms: (1) `.last_run` only written when every roster handle
succeeded, with 13:00/17:00 launchd fires retrying missed handles same-day, idempotent
per-handle (skip handles already snapshotted today); (2) incomplete runs log an ERROR
naming missing handles and post a macOS notification via osascript; (3) `_comment_count`
raises on a missing `comments` key instead of silently recording 0, `_view_count` warns
on a video with no view key; (4) profile snapshots with followers 0/None or a >50%
day-over-day swing are rejected before insert; (5) connection-class errors get up to 3
attempts with backoff, login/challenge exceptions abort the roster loop with a distinct
session-expired alert.

**Non-goals:** no Graph API migration; no third-party scraping APIs, email/webhook
infra, or new dependencies; no increase in scrape volume (each handle at most once per
day); no restructuring of the per-handle write sequence (audit H3); no platform/UI
staleness indicator (audit M5); no automatic `backfill.py` wiring.

**Acceptance criteria** (featurelist.json `feature_010`, 6 items): completeness-gated
`mark_ran_today` + retry fires skipping already-scraped handles; ERROR log + macOS
notification on incomplete runs; `_comment_count` raise / `_view_count` warn;
followers-0/None and >50%-swing rejection before insert; 3-attempt retry for
connection errors and roster-loop abort with distinct session alert; pytest green
including new tests for each mechanism.

## Goal Alignment: PASS

All five mechanisms are implemented exactly where the spec places them
(`scraper/youfirst_scraper/run_daily.py`, `instagram_scraper.py`, `db.py`
`profile_scraped_today`, `com.youfirstgersh.dailyscraper.plist`), each with dedicated
tests. Diff scope is exactly the listed files plus README/install-script doc updates —
no scope creep, no new dependencies (osascript via stdlib `subprocess`), no extra
scraping (skip guard verified by test), no auth or schema changes.

## Tests (run independently by the Evaluator)

| Suite | Result |
|-------|--------|
| `scraper/` `.venv/bin/python -m pytest tests/ -q` | 144/144 pass (up from 125; new retry/validation/gating/abort/notify tests all present) |
| Live `run_daily` integration | not run by Evaluator — being executed separately in the Generator's session per task instructions |

`.env` present in `scraper/`.

## Independent Verification Highlights

1. **Retry except-ordering is correct against the real instaloader hierarchy.**
   Verified in the venv that `TooManyRequestsException` subclasses
   `ConnectionException`; `_scrape_with_retry` catches session exceptions and the 429
   before the `ConnectionException` branch, so rate limits are never hammered
   (asserted by `test_scrape_with_retry_does_not_retry_rate_limit`).
2. **Anomaly gate edge cases hold.** `not followers` rejects both 0 and None; first-ever
   snapshot (empty history) passes; `if previous and ...` guards the division against a
   None/0 prior row; `get_profile_snapshots` returns ascending order so `[-1]` really is
   the latest snapshot. All four cases are unit-tested plus one integration-style test
   asserting a rejected snapshot is never inserted and the handle lands in `failed`.
3. **No infinite/double-scrape interaction.** Failed days retry at most twice more
   (fixed fire times, no loop); retry runs skip handles with a snapshot today
   (`profile_scraped_today`, tested); a fully successful run writes `.last_run` making
   later fires no-ops; session death short-circuits remaining handles (one notification,
   no further Instagram traffic) and marks them failed for the next fire.
4. **Plist semantics valid.** `StartCalendarInterval` as an array of dicts is the
   documented launchd form for multiple fire times; missed fires coalesce to one run on
   wake, which the `.last_run` / per-handle guards absorb.
5. **Tests assert the acceptance criteria directly**, including
   `test_main_does_not_mark_done_when_handles_failed` (no `.last_run`, notification
   names the missing handle) and `test_main_marks_done_when_all_handles_succeed`.

## Critical Issues

None found.

## Bugs / Gaps (ranked)

1. **[Medium] The historically observed session-death mode won't trigger the distinct
   session alert.** Per decisions.md (2026-07-06, instaloader #2682), a dead
   browser-cookie session presents as `ProfileNotExistsException` (200 OK, empty
   GraphQL body) — not `LoginRequiredException`/`LoginException`. In that mode the run
   grinds through all handles as generic per-handle failures instead of aborting with
   the "re-login required" alert. The completeness alert (mechanism 2) still fires, so
   the failure is visible either way — this weakens mechanism 5's *distinctness* in the
   most likely real failure mode, not safety. Spec asked only for login/challenge
   exceptions, so this is a hardening follow-up, not a spec miss.
2. **[Low/Medium] Partial-write finalization (known non-goal H3, but interaction is new).**
   If a handle fails *after* `insert_profile_snapshot` but before
   `insert_post_snapshots`, it's marked failed — but the retry run sees
   `profile_scraped_today` true, skips it, and the day marks complete with that
   handle's posts/content/highlights missing. The write-sequence restructure is an
   explicit non-goal; flagging because the new completeness gate now *silently
   finalizes* this case rather than leaving it visibly incomplete.
3. **[Low] Backoff is linear, decisions.md says exponential.** Delays are 30s, 60s
   (`base * attempt`). spec.md only requires "backoff," so this is a decisions.md
   wording mismatch, not a defect.
4. **[Low] Mixed date semantics.** `.last_run` uses local `date.today()`;
   `profile_scraped_today` uses the UTC day boundary. Safe for the 9/13/17 local fire
   times in any plausible timezone for this Mac (Spain/US), but the two "today"
   definitions could disagree at extreme UTC offsets.
5. **[Low] Anomaly gate ignores snapshot age.** After a multi-day outage the >50% check
   compares against a days-old snapshot, so a legitimate cumulative swing could be
   rejected for the whole day. Unlikely at these follower magnitudes; threshold is a
   documented reversible constant.
6. **[Low] Minor test-coverage gaps.** No test that `requests.RequestException` is
   retried (only `ConnectionException`); backoff growth values untested (sleep patched
   to 0); the ERROR log line is asserted only indirectly via the notification message.

## UX Issues

None. Notification strings are short, name the missing handles, and give the exact
re-login command for the session case.

## Missing Requirements

None in code. The live integration run (contract.md: manual run against real
Instagram/Supabase) is pending in the Generator's session and its result must be
recorded in progress.json before featurelist status moves past
`built_pending_live_verification`.

## Scope Drift

None. Every changed line traces to one of the five spec mechanisms or their docs.

## Rubric Scores

| Area | Score | Notes |
|---|---|---|
| 0. Goal Alignment | 5 | Solves the exact 2026-07-08 failure story; all five mechanisms present; zero scope creep |
| 1. Requirement Fit | 5 | All 6 acceptance criteria implemented and directly tested |
| 2. Simplicity | 5 | Module-level constants, two small helpers, one new db query; no speculative abstraction |
| 3. User Workflow | 5 | Failures now surface as notifications with actionable text; successful days unchanged |
| 4. Data Integrity | 4 | Gate + per-handle idempotency are solid; docked for the partial-write finalization interaction (gap #2, deferred H3) |
| 5. Error Handling | 4 | Correct exception ordering and graceful degradation; docked for the #2682 session-death mode bypassing the distinct alert (gap #1) |
| 6. Security / Privacy | 5 | No secrets in code/logs/notifications; osascript args passed as a list (no shell); only public IG data |
| 7. Maintainability | 5 | Constants documented with rationale; README/install script updated to match; tests readable |

**Average: 4.75**

## Verdict Detail

**Did this accomplish the stated goal?** Yes. The exact 2026-07-08 failure — all
handles fail, run marks itself complete, no retry, no alert — is now impossible: the
run cannot mark complete with failures, two more same-day fires retry only the missed
handles, and the failure is pushed to the screen. Shape-drift and anomalous snapshots
now fail loud before corrupting Supabase. 144/144 pytest, no critical bugs, no secret
exposure, Goal Alignment 5, average 4.75 — passes the rubric's pass rule. PASS is
contingent on the Generator's in-flight live run being recorded honestly in
progress.json; findings #1–#2 are recommended follow-ups, not blockers.

## Recommended Next Generator Task

1. Record the live `run_daily` result (per-handle outcomes, whether `.last_run` was
   written, notification observed) in progress.json and flip feature_010 status
   accordingly.
2. Follow-up (small): treat a run where *every* handle fails with
   `ProfileNotExistsException` as probable session death (issue #1) — e.g. emit the
   session-expired notification text when all failures share that type — so the
   known #2682 mode gets the actionable alert.
3. Optional, when audit H3 is picked up: make `profile_scraped_today` (or a successor
   check) consider post snapshots too, closing the partial-write finalization gap (#2).
