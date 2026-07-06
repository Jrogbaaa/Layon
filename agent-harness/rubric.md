# Evaluation Rubric

Score each area from 1 to 5.

## 0. Goal Alignment

Does the implementation actually serve the stated goal of the change?

**High score (4–5):** The change solves the intended problem, stays within scope, the
user/business reason is preserved, no unnecessary complexity was added.

**Low score (1–2):** The agent built something technically functional but strategically
wrong; the change drifted from the original purpose; the implementation expanded scope
without justification (e.g. sneaking in brand-matching, per-user auth, or extra scrape
frequency).

## 1. Requirement Fit

Does the implementation match the spec?

## 2. Simplicity

Is the solution as simple as it reasonably can be?

## 3. User Workflow

Can the intended user (agency staff, or the talent themselves) complete the task
without confusion?

## 4. Data Integrity

Is data saved, read, and updated correctly? Are snapshots idempotent (re-running the
scraper doesn't corrupt or duplicate history)?

## 5. Error Handling

Are failures handled clearly? Does a single broken profile or trend source fail
gracefully without aborting the whole daily run?

## 6. Security / Privacy

Does the implementation avoid exposing sensitive data (API keys, Supabase service key,
the shared password) client-side? Does it only store public Instagram data?

## 7. Maintainability

Can another developer understand and extend this?

## Pass Rule

A feature passes only if **all** of the following are true:

- No critical bugs
- No privacy/secret-exposure failures
- Goal Alignment score ≥ 4
- Average score across all areas ≥ 4
- All high-priority acceptance criteria satisfied
- Test results recorded (pytest/Playwright pass counts, or "not run" explicitly stated
  with reason)
