---
target: roster page
total_score: 24
p0_count: 1
p1_count: 2
timestamp: 2026-07-08T08-48-10Z
slug: platform-app-app-page-tsx
---
Method: dual-agent (A: ad7df466587ae8456 · B: a7903b1442e2ea599)

# Critique: Roster page (`platform/app/(app)/page.tsx`)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Timestamp shown, but no data-freshness on cards |
| 2 | Match System / Real World | 2 | "scrape", "gemini-2.5-flash", raw unformatted numbers, "down -92%" double negative |
| 3 | User Control and Freedom | 2 | Briefing can't be collapsed; attention items can't be acknowledged |
| 4 | Consistency and Standards | 2 | "breakout" badge contradicts briefing narrative; hover shadow violates One Shadow Rule |
| 5 | Error Prevention | 3 | Read-only page |
| 6 | Recognition Rather Than Recall | 3 | Raw engagement numbers force mental math |
| 7 | Flexibility and Efficiency | 2 | No sort/filter; won't scale past ~5 cards |
| 8 | Aesthetic and Minimalist Design | 2 | Briefing dominates; same 5 people described 3× in 3 sections |
| 9 | Error Recovery | 3 | Malformed briefing silently vanishes |
| 10 | Help and Documentation | 2 | "breakout"/"attention" criteria unexplained; empty-state copy addresses developers |
| **Total** | | **24/40** | **Acceptable — significant improvements needed** |

## Anti-Patterns Verdict

**LLM assessment:** mostly clean. The roster grid is a legitimate data grid (live differentiated data), not a marketing card grid. One residue: `Avatar.tsx:29` fallback badge still uses the retired teal→blue gradient with white initials (~2.1:1 at the teal end).

**Deterministic scan:** CLI detector clean (exit 0) on all five source files. Live browser overlay: 6× `low-contrast` (4.1:1, muted #6b7684 text on canvas #eef3f6 in briefing action tiles — the strongest objective finding), 14× `line-length` (146–170 chars/line in briefing prose), 8× `gpt-thin-border-wide-shadow` (the sanctioned card treatment; stylistic), 1× `overused-font` (expected in a single-typeface system).

**Agreement:** the overlay's low-contrast and line-length hits land on exactly the briefing prose the design review identified as the page's dominating element.

## Overall Impression

Visually the page honors the Trading Floor system — restrained accents, real data cards, clean chrome. The failures are informational, not decorative: the triage signal is below the fold, the three sections contradict each other, and the smallest semantic text fails contrast.

## What's Working

- Palette discipline: Signal Blue only on wordmark and links; semantic red/green reserved for trends. The Signal Rule holds.
- Everything deep-links: handles → detail pages, actions → Instagram posts. Triage-to-action is one click.
- Edge states handled in code: null briefing, malformed JSON, empty roster all degrade gracefully.

## Priority Issues

- **[P0] Triage inversion: "Needs attention" is below the fold.** Briefing (~880px tall) renders first; attention section starts at y≈1077 on an 800px viewport. PRODUCT.md's first principle fails. Fix: reorder (attention first) or collapse the briefing to its summary with a disclosure. Files: page.tsx, RosterBriefing.tsx. Suggested command: /impeccable layout.
- **[P1] Contradictory severity signals.** Card badges read highlight severity; briefing reads weekly data — "breakout" on the account the briefing calls the worst performer; "-1 since last scrape" vs "-160 this week" on the same person, neither timeframe labeled. Fix: one severity source per influencer used everywhere; label delta windows. Suggested command: /impeccable clarify + layout.
- **[P1] WCAG AA contrast failures on the most semantic small text.** Measured: "breakout" badge ≈3.1:1, "attention" badge ≈3.9:1, accent links #2e8ff0 on white ≈3.3:1, muted text on canvas ≈4.1–4.3:1, avatar fallback ≈2.1:1. Fix: darker badge text, accent-strong for small links, muted text only on white, solid accent-strong avatar fallback. Suggested command: /impeccable polish.
- **[P2] Card hover violates the One Shadow Rule** (`hover:shadow-lg` at page.tsx:59). Fix: keep the translate, drop the shadow escalation. Suggested command: /impeccable polish.
- **[P2] Machine-voiced copy.** "@dante_caro — @dante_caro's engagement is down -92%…", unformatted 28178/373881, "gemini-2.5-flash" and seconds-precision timestamp exposed, "since last scrape". Fix: humanize ("Engagement down 92% (28.2K vs 373.9K avg)", "Updated this morning", "since yesterday"). Suggested command: /impeccable clarify.

## Persona Red Flags

**Alex (Power User):** no sort/filter on the roster; 14 readable items describing 5 people ≈ 3 touches per person per scan; can't collapse the briefing he's already read.

**Sam (Accessibility):** status badges, small links, and briefing rationale text all below AA; avatar initials at 2.1:1.

**Marta (project persona: talent manager, morning scan):** lands looking for "who's in trouble", meets a wall of prose (possibly in the other language — briefing persists last user's language while chrome stays English); finds the contradiction between "breakout" badge and briefing narrative and stops trusting the page.

## Minor Observations

- LanguageToggle shows current language, not destination; ES state is permanently mixed-language (section headings stay English).
- A -1 follower delta renders full negative red — noise gets the same alarm color as a crisis; add a dead-zone.
- Empty-roster copy addresses a developer ("Run the scraper, see scraper/README.md"), not the manager.

## Questions to Consider

- Should the briefing be a collapsed digest ("3 things need your eyes today") rather than a report?
- What is THE severity source of truth — highlights or weekly deltas?
- What does this page look like with 25 influencers instead of 5?
