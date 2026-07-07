# Findings — feature_007 Content-Grounded Recommendation Bullets + Roster Attention Alerts

## Verdict: PASS (with follow-ups)

**Evaluator:** separate subagent pass (fresh context, per contract.md/evaluator.md).

## Restated Goal / Non-Goals / Acceptance Criteria

**Goal:** Analyze the video/audio of each influencer's top-performing posts with Gemini
so recommendations can cite what a reel was actually about, rewrite the recommendation
prompt/output as short Spanish-only data-grounded bullets (dropping trend-report
context), and surface engagement-drop/posting-gap "needs attention" signals at the
roster level.

**Non-goals:** no email/push alert digest; no comparable-creator scraping; the
trend-scraper module itself is not removed, only unhooked from the recommendation
prompt; no language toggle (Spanish only); no Apify/third-party scraping API migration
(fetch/analyze kept as separate functions for a possible future swap, not built now).

**Acceptance criteria** (featurelist.json `feature_007`, 8 items): content_analysis.py
selection/cap/Gemini-JSON/skip-on-failure behavior; `post_content` table in schema.sql;
`build_prompt` cites top performers + content summaries + multiple-of-median + weakest
contrast with the trend section removed; `generate_recommendation` requests Gemini JSON
mode returning `{bullets:[{text,reason,shortcode}]}` (3-5 Spanish bullets tied to data),
falling back to raw text on malformed JSON; `RecommendationContent.tsx` renders bullets
as a list with Instagram links, falls back to markdown for legacy prose;
`metrics.compute_highlights` gains `engagement_drop`/`posting_gap` with a `severity`
field; roster page shows a needs-attention indicator from recent highlights; pytest
green including new content-analysis/alert tests, Playwright covers bullet rendering +
fallback + roster badges.

## Goal Alignment: PASS

The implementation is squarely aimed at the stated problem: `content_analysis.py`
genuinely grounds the model in what a post's video/audio is about (not just captions),
`recommendations.build_prompt` cites top performers with content summaries and a
weakest-post contrast, and the trend-report section is fully removed from this prompt
(confirmed by a dedicated `test_build_prompt_has_no_trend_report_section` test and by
`test_run_recommendations_does_not_fetch_trends` asserting `get_latest_trend_snapshots`
is never called). No brand-matching, per-user auth, or scope creep found. The
fetch/analyze split in `content_analysis.py` correctly keeps a future Apify swap
possible without being built now.

## Tests

| Suite | Result |
|-------|--------|
| `scraper/` `pytest` | 62/62 pass |
| `platform/` `npx playwright test` (against already-running dev server) | 5/5 pass |

`.env` present in both `scraper/` and `platform/`. Dev server was already running
(not started by this Evaluator pass).

## Critical Issues

None found.

## Bugs / Gaps

1. **Disclosed gap (not new): no live run against real Instagram/Gemini/Supabase for
   this feature.** The JSON-bullet path (`generate_recommendation` JSON mode, and the
   full `content_analysis.analyze_post` video-download-to-Gemini round trip) is only
   exercised through mocked pytest. The one thing verified live is the *fallback*
   render path, against a pre-existing bilingual-prose recommendation row from before
   this feature. This is a real, material gap for a change whose core deliverable is
   "does Gemini reliably return valid `{bullets:...}` JSON for a real video" — that
   question is still open. Consistent with what was disclosed going in; factored into
   Data Integrity and Goal Alignment below rather than treated as newly discovered.
2. **Playwright coverage for bullets/badges is weaker than the acceptance criterion
   implies.** `e2e/dashboard.spec.ts`'s roster test is explicitly a "loads without
   crashing" check — its own comment says it does not assert the attention strip
   renders, and no test asserts the JSON-bullet list actually renders as a list (vs.
   the markdown fallback) since no live data with JSON-bullet content exists yet. The
   acceptance criterion says "Playwright covers bullet rendering + fallback + roster
   badges" — only the fallback half is meaningfully covered. This is a direct
   consequence of gap #1 (no real JSON-bullet row exists to assert against) rather than
   a separate defect, but it means the stated test-coverage acceptance criterion is
   only partially met today.
3. **Prior features (005/006) were never committed to git.** Diffing against `HEAD`
   shows `schema.sql`, `db.py`, and `instagram_scraper.py` at the last commit have none
   of the `views` column, `highlights` table, or `post_content` table — meaning the
   working tree currently bundles feature_005 + feature_006 + feature_007 together as
   one large uncommitted diff. This isn't a defect introduced by feature_007's code,
   but it's a process/maintainability issue worth flagging: it makes it impossible to
   review feature_007 in isolation via `git diff`, and `featurelist.json` records
   005/006 as `built_and_live_verified`/`built_and_verified` when their code has never
   actually landed on `main`.

No other bugs found. Idempotency for `post_content` is enforced by a
`unique(influencer_id, shortcode)` constraint plus an explicit
`get_analyzed_shortcodes` pre-filter, so a same-day re-run (or a future retry) won't
double-analyze or violate the constraint. `run_daily.py`'s already-ran-today guard and
per-influencer/per-trend-source try/except blocks correctly wrap the new
content-analysis and highlights steps.

## UX Issues

None found in what's renderable today. `RecommendationContent.tsx`'s bullet vs.
markdown branch is a reasonable, cheap heuristic (`JSON.parse` + `Array.isArray`) that
degrades safely to markdown on any non-bullet-shaped content (reasoned through
non-object/number JSON edge cases — no dedicated frontend unit test for it, Playwright
doesn't have a real bullet row to exercise it against per gap #2).

## Missing Requirements

- Live verification of the Gemini JSON-bullet contract and the video-analysis pipeline
  (gap #1) — planner/user already aware, needs a go-ahead to spend Gemini quota / touch
  Instagram.
- A Playwright assertion that actually exercises the JSON-bullet render path and the
  "needs attention" strip's conditional rendering, once real data exists (gap #2).

## Scope Drift

None. Everything built traces directly to spec.md's 4 numbered success criteria and the
8 featurelist.json acceptance criteria.

## Rubric Scores

| Area | Score | Notes |
|---|---|---|
| 0. Goal Alignment | 4 | Solves the stated problem and stays in scope; capped at 4 rather than 5 because the core new capability (Gemini JSON bullets citing real content) is unverified against a live call |
| 1. Requirement Fit | 4 | All 8 acceptance criteria implemented in code; test-coverage criterion only partially met (gap #2) |
| 2. Simplicity | 5 | `content_analysis.py`/`recommendations.py` split is clean; no speculative abstractions; fetch/analyze kept separate per the stated future-Apify non-goal without over-building it now |
| 3. User Workflow | 4 | Bullets + Instagram links + roster badges are scannable and match the "low-patience reader" goal; unverified in the browser with real bullet data |
| 4. Data Integrity | 4 | `post_content` unique constraint + pre-filter set correctly prevent duplicate/idempotency issues; unverified against a real Gemini response shape |
| 5. Error Handling | 5 | Per-post analysis failures, per-influencer failures, and malformed-JSON responses all degrade gracefully and are tested |
| 6. Security / Privacy | 5 | No keys hardcoded or logged; `.env` files gitignored; only public IG data (video/thumbnail of public posts) is fetched and stored |
| 7. Maintainability | 4 | Clear module boundaries; docked one point for the uncommitted-prior-features issue (gap #3) making the current diff hard to review in isolation |

**Average: 4.375**

## Verdict Detail

**Did this accomplish the stated goal?** Yes, for everything that can be verified
without spending Gemini quota or touching Instagram: the prompt is genuinely grounded
in content summaries and top-performer stats, trend context is removed, the bullet/
fallback rendering logic is sound, and the new alert signals compute and surface
correctly with a severity field. Goal Alignment (4) and the average (4.375) both clear
the bar, no critical bugs, no secret exposure, and test results are recorded per
contract.md's pass rule. The live-verification gap was disclosed up front rather than
discovered, and error handling/rollback paths around it are solid — so this is a PASS
with concrete follow-ups, not a FAIL.

## Recommended Next Generator Task

1. With user go-ahead: run `python -m youfirst_scraper.run_daily` once for real,
   confirm at least one influencer gets a `post_content` row with real Gemini
   `{summary, topic, format, hook}` output and one real `{bullets:[...]}` recommendation
   row, and verify that row's render on `/influencer/<handle>` in the browser (not just
   the pre-existing prose fallback).
2. Add a Playwright test (or extend `dashboard.spec.ts`) that seeds/asserts against a
   JSON-bullet-shaped recommendation content string directly (e.g. via a test fixture
   or by asserting on the real row from step 1) so "bullet rendering" is actually
   covered, not just "renders without crashing."
3. Retroactively commit the feature_005/006 work still sitting uncommitted so future
   diffs (including this one) can be reviewed in isolation, and so `featurelist.json`'s
   `built_and_live_verified`/`built_and_verified` statuses reflect what's actually on
   `main`.
