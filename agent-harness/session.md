# Session

## Current Goal

Talent Coaching Cockpit Program — Features 019 through 022 complete.

## Current State

All four features have independent PASS verdicts. A separate PR review subsequently requested
changes for recommendation shortcode provenance, missing feedback/outcome idea referents, and
partial strategies being excluded from coverage. All three are remediated. Pytest is 228/228,
Playwright 33/33, lint/type-check/build pass, and the live bounded relation reads include their
recommendation referents. PR re-review is pending before merge.

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

Commit and push the verified PR-review remediation, then obtain an independent APPROVE before
marking PR #19 ready and merging.
