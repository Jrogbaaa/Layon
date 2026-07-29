# Spec — Feature 022: Weekly Portfolio Review

## Goal

Generate exactly one evidence-backed bilingual coaching review per Madrid calendar week on the
first successful daily run, and make portfolio review health visible on the shared roster.

## Why It Matters

Talent strategy, feedback, and experiments are useful individually, but an agency also needs a
weekly ritual: which three conversations matter most, what worked, what is at risk, and where
the operating system is stale. The review turns daily evidence into that portfolio agenda.

## Intended Users

Agency managers and talent sharing the existing password-gated product. The review contains
only non-sensitive strategy, feedback, experiment, and public Instagram evidence.

## Scope

- Add nullable `period_start` and `period_end` to `roster_briefings`, plus uniqueness for rows
  with a period start. Legacy rows remain unchanged and readable.
- Compute Madrid calendar-week Monday/Sunday boundaries. On every successful daily pipeline,
  check whether the current week exists; generate only when absent. This naturally recovers on
  Tuesday or later after a missed Monday.
- Build structured evidence from current roster state, public performance, latest unanswered
  recommendation bullets, strategy freshness, warning signals, experiment review dates, and
  evaluated outcomes.
- Gemini returns one bilingual JSON payload with top three priorities, strongest creative win,
  primary risk, due/recently evaluated experiments, stale strategy profiles, suggested talent
  conversations, and supporting handles/metrics/post links.
- Upsert/insert the review idempotently by Madrid-week period. A generation/validation/storage
  failure keeps the previous review and does not fail the daily pipeline.
- The roster renders the new weekly payload and legacy briefing format. It also shows strategy
  coverage, unresolved recommendation count, active experiment count, and experiment hit rate.

## Non-Goals

- No Slack, email, export, reminder, calendar event, or external delivery.
- No separate talent portal, individual accounts, roles, task owners, or private notes.
- No CRM, campaign management, brand matching, or additional social networks.
- No rewrite/backfill of legacy briefing content or daily duplicate review.

## Decisions and Invariants

1. Madrid-week periods are Monday 00:00 through Sunday 23:59:59.999 by calendar date; stored
   period fields are inclusive date values (`YYYY-MM-DD`).
2. Uniqueness is on `period_start` only for non-null rows, so legacy null-period rows coexist.
3. Generation is attempted after scrape, tagging, experiment evaluation, and recommendations,
   so the review sees the newest successful-run evidence.
4. A week is considered present only after a valid review row is stored. A failed Monday run
   therefore retries on the next successful daily fire.
5. Hit rate denominator includes evaluated outcomes with a non-null interaction delta; a hit is
   directional/strong evidence with positive interaction delta. Empty denominator displays `—`,
   never 0%.
6. Strategy coverage is profiles with at least one substantive current field divided by active
   talent count. Unresolved recommendations count current structured bullets lacking an action.
7. All payload evidence links use stored shortcodes/source URLs; Gemini may summarize but may not
   invent handles, metrics, or links.

## Acceptance Criteria

1. Additive/idempotent schema adds nullable period dates and a partial unique Madrid-week index;
   legacy rows and content formats remain intact.
2. Pure Madrid-week calculation passes Sunday/Monday, month/year, DST, and timezone-boundary
   tests for `Europe/Madrid`.
3. The daily pipeline checks after current evidence stages and creates at most one review for the
   current week; missed Monday recovers later; failures log/continue and do not mark a phantom week.
4. Weekly evidence and validated bilingual payload contain all seven required sections with
   supporting handles, metrics, and post links constrained to supplied evidence.
5. Existing legacy `summary/patterns/actions` briefing JSON still renders, while the new payload
   renders bilingual sections and period labels safely.
6. Roster KPI calculations correctly handle zero roster/strategy/experiment denominators and
   report strategy coverage, unresolved bullets, active experiments, and experiment hit rate.
7. Platform delivery is the only delivery; no connector, notification, export, account, or CRM
   code is added.
8. Scraper tests cover week boundaries, first-run/recovery/idempotency, payload validation,
   evidence shaping, and failure preservation. Platform tests cover both briefing formats,
   bilingual review, period display, and KPI edge states.
9. Pytest, lint, TypeScript, build, Playwright, live additive schema/read verification, a marked
   weekly idempotency check with exact cleanup, and independent Evaluator review pass.

## Verification Plan

- Scraper: pure timezone/period/evidence/payload tests and mocked daily idempotency/failure tests;
  full pytest.
- Platform: deterministic legacy/new review and KPI fixtures; full Playwright/lint/tsc/build.
- Live: apply additive schema; insert/upsert the same marked non-current historical period twice,
  prove one row, then remove only that marker row. Do not create the real current-week review as
  part of testing.
- Evaluator: fresh independent subagent must record PASS before the program is complete.
