# CLAUDE.md — You First Gersh Influencer Insights Platform

See [CONSTITUTION.md](./CONSTITUTION.md) for mission, scope, and stack rationale. This
file is the operating manual for working in this repo.

## Karpathy Guidelines (inherited, project-specific application)

1. **Think before coding** — state assumptions, surface tradeoffs, ask when unclear.
2. **Simplicity first** — smallest code that solves the problem. No speculative features,
   no config that wasn't requested, no error handling for scenarios that can't happen.
3. **Surgical changes** — touch only what the task requires. Match existing style. Don't
   refactor unrelated code. Remove only the imports/vars your own change orphaned.
4. **Goal-driven execution** — turn tasks into verifiable goals (write the test that
   proves it, then make it pass), not "make it work."
5. **Agent discipline** — after each step, state what's done, what's verified, what's
   left. Never claim "tests pass" without having run them.

## Process: Spec-Driven Development via agent-harness/

Every feature-sized or multi-file change goes through
[`agent-harness/`](./agent-harness/):

1. **Planner** (`agent-harness/prompts/planner.md`) turns a request into `spec.md` +
   `featurelist.json` — goal, why, non-goals, acceptance criteria.
2. **Generator** (`agent-harness/prompts/generator.md`) builds the smallest version that
   satisfies the spec.
3. **Evaluator** (`agent-harness/prompts/evaluator.md`) runs as a separate subagent,
   attacks the implementation, runs tests, scores `agent-harness/rubric.md`, writes
   `agent-harness/findings.md`.

Guardrails live in `agent-harness/contract.md`. One-line fixes, typos, and doc edits skip
this flow — see the Triviality Threshold in contract.md.

## Repo Layout

- `scraper/` — Python: Instaloader-based Instagram scraper, trend-report scraper,
  Gemini-based recommendation generator, Supabase writes. Run daily via `launchd`.
- `platform/` — Next.js dashboard (App Router + Tailwind), deployed to Vercel. Password-
  gated (`LAYCC`) via `proxy.ts` (Next.js 16 renamed Middleware to Proxy — same
  mechanism, new filename/export), reads from Supabase server-side.
- `agent-harness/` — Planner/Generator/Evaluator process state and prompts.
- `docs/superpowers/specs/` — design docs from brainstorming sessions.

## Data & Security

- Supabase service key is server-side only — never exposed to the browser or committed.
- Only public Instagram data is stored (no private accounts, no DMs).
- Platform auth is a single shared password (`LAYCC`) via middleware — not per-user
  accounts. Do not add email/OAuth login without a new spec.
- Never commit `.env` files or API keys.

## Testing

- `scraper/`: pytest. Mock Instaloader/Gemini/Supabase calls in unit tests; a manual run
  against real Instagram is the integration check (see CONSTITUTION.md Definition of Done).
- `platform/`: Playwright for the password gate and dashboard rendering.

## Post-Task Checklist

Before calling anything done:
- [ ] Ran the relevant tests (pytest and/or Playwright) — state the actual result.
- [ ] For scraper changes: confirm behavior against real Supabase data, not just mocks.
- [ ] For platform changes: confirm in a running dev server, not just a type-check.
- [ ] No new speculative features beyond what was asked.
- [ ] No secrets committed.
