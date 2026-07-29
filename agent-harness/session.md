# Session

## Current Goal

Talent Coaching Cockpit Program — Features 019 through 022 complete.

## Current State

All four features have independent PASS verdicts. PR review remediation now covers recommendation
shortcode provenance, feedback/outcome idea referents, partial strategy coverage, and the integrated
oldest-500 snapshot cutoff. Weekly evidence uses the newest bounded snapshot window plus a paginated
complete stored-shortcode index. Pytest is 230/230, Playwright 33/33, lint/type-check/build pass,
and live newest-window/index reads match. Independent PR re-review returned APPROVE at 9fa066c.

## Generator Guardrails

- Goal: create one bilingual Madrid-week portfolio review on the first successful run and make
  portfolio coaching health visible on the shared roster.
- Non-goals: no notifications/exports, portal/accounts, CRM/campaigns/brand matching, private
  notes, new networks, or legacy briefing rewrites.
- Likely files: additive briefing schema/types, weekly evidence builder/generator and daily-run
  guard, roster data/KPI aggregation and review UI, plus scraper/Playwright tests.
- Risk areas: timezone/week boundaries, missed-Monday recovery, duplicate generation, legacy JSON,
  small/zero experiment denominator, stale-strategy definitions, and evidence-link integrity.

## Next Action

Merge approved PR #19 into main.
