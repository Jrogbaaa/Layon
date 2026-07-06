# Contract

## Goal Discipline

Every change must preserve the stated goal.

Before changing code, the Generator must:

1. Quote the goal + non-goals from `spec.md` / `featurelist.json` into its own output
2. Identify what problem this change solves
3. Identify who the change is for (agency staff / talent / developer)
4. Identify what should remain unchanged
5. Identify what would count as unnecessary scope expansion

If the implementation does not serve the goal, it should not be built.

## Non-Negotiables

- Do not add influencer-brand matching (out of scope — see CONSTITUTION.md).
- Do not add per-user accounts / email login — the platform uses a single shared
  password gate (`LAYCC`). Do not change auth model without a new spec.
- Do not invent unsupported data fields.
- Do not add unnecessary complexity.
- Prefer simple, durable implementation.
- Do not scrape more frequently than once per day.
- One active harness session at a time (`spec.md`/`progress.json`/`session.md` describe
  the single in-flight change).

## Design Constraints

See [CONSTITUTION.md](../CONSTITUTION.md) for the three pillars (metrics, creative
recommendations, trend intelligence) and stack rationale. New UI should feel like a
polished, premium internal tool — see `frontend-design`/`dataviz` guidance during
implementation.

## Security Constraints

See [CLAUDE.md §Data & Security](../CLAUDE.md) — the authoritative list.

Harness-specific: **never** write raw API keys, Supabase service keys, Instagram
session data, or scraped personal data into harness files. Record only pass/fail counts
and short notes.

## Data Constraints

Respect the schema in `scraper/schema.sql`; do not create duplicate sources of truth.
Every new persisted field needs a reason. Only public Instagram data may be stored.

## Testing Requirements

See [CLAUDE.md §Testing](../CLAUDE.md) — the authoritative checklist.

Harness-specific:
- The Evaluator runs as a **separate subagent**, its own context.
- Scraper changes: pytest, plus a manual run against real Instagram/Supabase where
  feasible (state explicitly if not run).
- Platform changes: Playwright against a local dev server.
- Infra failures (missing `.env`, dev server not running) are recorded as **"not run,"**
  never as bugs.
- Only pass/fail counts and test names go into `findings.md`. No raw output or secrets.

## Triviality Threshold

One-line fixes, typo/doc edits, and simple renames skip the full harness flow. The
harness applies to features, multi-file changes, and behavioral changes.
