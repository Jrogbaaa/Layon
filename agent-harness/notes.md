# Agent Harness Notes

## Core Thesis

The future of coding agents is not only stronger models.

It is better harnesses.

A harness is the operating system around the model:

- planning
- tools
- files
- memory
- tests
- evaluators
- permissions
- hooks
- sessions
- trace logs

The model is only one component.

The harness determines whether the system can produce durable, auditable, resumable work.

## The Winning Pattern

```
Human prompt
→ Planner creates spec
→ Generator builds
→ Evaluator tests/critiques
→ Findings go back to Generator
→ Repeat until good
```

Equivalent human workflow: PM → Engineer → QA

Equivalent agent workflow: Planner → Builder → Evaluator

The important insight is that coding agents need separation of duties.

## Key Rule

**Do not let the builder judge its own work.**

Self-evaluation is weak. The same agent that built something will often rationalize why it is good enough.

Better pattern:

- Generator = builds
- Evaluator = attacks

The evaluator should have:

- separate context
- separate prompt
- separate role
- separate output file

This creates cleaner judgment.

In Claude Code, this means running the Evaluator as a **separate subagent** (its own context window), not a role switch within the same session.

## Docs Must Preserve the Goal of the Change

Every harness document should keep the goal of the change visible.

Agents can follow instructions mechanically but still drift away from the actual purpose. Good docs prevent that.

The docs should not only say what to build. They should also say:

- why this change matters
- what user/business problem it solves
- what should not change
- how success will be judged

Without the goal, agents may optimize the wrong thing. They may:

- add unnecessary features
- refactor unrelated code
- solve a technical problem but miss the product problem
- make the platform more complex
- break the original workflow
- declare success because code was written

The goal acts as the north star.

Before building, the generator should ask: **What is the goal of this change?**

Before passing, the evaluator should ask: **Did the change accomplish that goal?**

This prevents the common agent failure: *successful implementation of the wrong thing.*

For this project, every change should be judged against the core question:

> Does this help a You First influencer understand their own performance and get a
> genuinely useful, specific creative recommendation?

If not, it is probably complexity disguised as progress.

## Harness Architecture

```
/agent-harness
  spec.md           ← current feature goal/scope (overwritten each change)
  contract.md       ← permanent constraints (references CONSTITUTION.md/CLAUDE.md)
  featurelist.json  ← machine-readable feature registry
  rubric.md         ← how quality is judged (Goal Alignment = axis 0)
  progress.json     ← current state (overwritten each change)
  findings.md       ← evaluator output (overwritten each change)
  session.md        ← resume instructions (overwritten each change)
  decisions.md      ← append-only permanent decision log
  open-questions.md ← active human-judgment questions
  trace.jsonl       ← append-only event log
  notes.md          ← this file
  prompts/
    planner.md
    generator.md
    evaluator.md
```

## Files Are the Memory

Chat context rots. Files persist. The harness treats files as the source of truth.

**Working files** (overwritten each change): `spec.md`, `progress.json`, `findings.md`, `session.md`

**Append-only logs** (permanent record): `trace.jsonl`, `decisions.md`

**Permanent reference** (updated rarely): `contract.md`, `rubric.md`, `featurelist.json`

**History without buildup:** When a feature finishes, working files are overwritten by the next change. History is recoverable via `git log` / `git show`. No `spec-2.md` accumulation.

## File Lifecycle

One active harness session at a time. `spec.md`/`progress.json`/`session.md` describe the single in-flight change. Multiple parallel worktrees are fine, but only one drives the harness.

## Security Constraint on Harness Files

Harness files are git-tracked. **Never** write raw test output, signed URLs, API keys, tokens,
or Instagram credentials into any harness file. Record only:

- pass/fail counts
- spec/test names
- short human-readable notes
