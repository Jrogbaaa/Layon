# Session

## Current Goal

You First Gersh Influencer Insights Platform v1. See CONSTITUTION.md for the full
product scope (metrics, creative recommendations, trend intelligence).

## Current State

Project foundations complete: CONSTITUTION.md, CLAUDE.md, and agent-harness/ (this
directory) are in place, adapted from the user's existing harness at
`/Users/JackEllis/ui/agent-harness/`. No feature code has been built yet.

## Last Completed Work

- CONSTITUTION.md — mission, three pillars, non-negotiables, stack rationale, definition
  of done.
- CLAUDE.md — Karpathy guidelines applied to this project, repo layout, security/testing
  checklist.
- agent-harness/ — full Planner/Generator/Evaluator structure adapted for this project
  (contract.md, rubric.md, prompts/, decisions.md, open-questions.md, trace.jsonl,
  progress.json, notes.md).

## Next Action

Run a Planner pass to write `spec.md` + `featurelist.json` for feature_001: the Phase 1
Instagram + trend scraper (Instaloader → Supabase, plus the two trend-report sources).

## Important Context

- One active harness session at a time.
- Harness files are git-tracked — never write API keys, Supabase service keys, or
  scraped personal data into them.
- Evaluator runs as a separate subagent, headless only for any Playwright runs.
- Trivial changes (one-liners, typos, renames) skip the harness.

## Files Changed

`CONSTITUTION.md`, `CLAUDE.md`, `agent-harness/*` (new).

---

*This file is overwritten at the start of each session. History is in git.*
