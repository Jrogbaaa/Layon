---
target: influencer detail page
total_score: 27
p0_count: 1
p1_count: 2
timestamp: 2026-07-08T11-27-36Z
slug: platform-app-app-influencer-handle-page-tsx
---
Method: dual-agent (A: a10ace95c06296189 · B: ad7bb0bc8bd6004f7)

# Critique: Influencer detail page (`platform/app/(app)/influencer/[handle]/page.tsx`)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Clear stats/chart/empty states, undercut by raw timestamp + model exposure |
| 2 | Match System / Real World | 2 | Raw model name, raw timestamp, "scrape" jargon in two empty states |
| 3 | User Control and Freedom | 3 | Clear back-link, language toggle |
| 4 | Consistency and Standards | 3 | text-accent link contrast and copy patterns inconsistent with fixes already applied on roster/login |
| 5 | Error Prevention | 3 | Read-only page |
| 6 | Recognition Rather Than Recall | 3 | Domain-appropriate labels for expert users |
| 7 | Flexibility and Efficiency | 2 | Posts table has no sort/filter/collapse |
| 8 | Aesthetic and Minimalist Design | 3 | Calm overall; triplicated highlights inject noise |
| 9 | Error Recovery | 3 | Not heavily exercised |
| 10 | Help and Documentation | 2 | No inline explanation of methodology (cadence, eng. rate) |
| **Total** | | **27/40** | **Acceptable — significant improvements needed** |

## Anti-Patterns Verdict

**LLM assessment:** mostly clean — no gradient text, avatar fallback solid, no hover-shadow escalation, no hero-metric templates. But two patterns already fixed elsewhere in the app have NOT propagated here: raw timestamp + exposed model name (`page.tsx:101-104`, same pattern fixed on the roster briefing), and "scrape" pipeline jargon in two empty states (`page.tsx:109`, `FollowerChart.tsx:16`).

**Deterministic scan:** CLI clean (exit 0) on all six files. Live overlay: `gpt-thin-border-wide-shadow` ×9 (the sanctioned card token, applied consistently — not 9 separate defects), `overused-font` (expected, single-typeface system), `nested-cards` ×2 (Performance-by-format's format cards nested in the outer section card — a deliberate grouping pattern, likely a false positive), `low-contrast 4.1:1 on #6b7684/#eef3f6` — **stale**: verified live via `getComputedStyle` that `--muted` is now `#5b6675` (contrast ≈5.2:1), which already resolves this from the roster-page token fix; the overlay evidence pre-dates or cached before that change propagated.

**Where they agree:** both flag the same class of contrast issue that turned out to be already-fixed at the token level, confirming the muted-text fix from the roster pass carries through here too — the remaining live contrast issue is the two `text-accent` links B didn't isolate but A pinpointed exactly (RecentPostsTable, RecommendationContent).

## Overall Impression

The strongest page in the app on substance — real evidence-linked recommendations, correct shadow/avatar discipline — undermined by two regressions of fixes already made elsewhere (timestamp/model exposure, scrape jargon) and one new, real trust problem: highlights repeat the same event three times with three different numbers.

## What's Working

- Avatar fallback and shadow discipline consistently applied — no regressions there.
- Recommendations are evidence-linked (shortcodes, % deltas) rather than generic AI-speak.
- Stat tones and Muted Slate all measure well above 4.5:1 on white after the AA darkening pass.

## Priority Issues

- **[P0] Triplicated highlights undermine the high-signal promise** (`page.tsx:126-135`). No dedup — 3 of 4 rows for one influencer described the same post spike with three different percentages/medians from repeated daily captures. Fix: dedupe by post shortcode (keep most recent/most extreme) before rendering, or cap to top-N distinct highlights. Suggested command: /impeccable harden.
- **[P1] `text-accent` link contrast fails AA, same defect class as elsewhere** (`RecentPostsTable.tsx:51` "View" link, `RecommendationContent.tsx:46` "Ver post →" link — both #2e8ff0 on white ≈3.3:1). `HighlightContent.tsx:23` already uses the corrected `text-accent-strong`. Fix: change both to `text-accent-strong`. Suggested command: /impeccable polish.
- **[P1] Exposed raw timestamp + model name, a regressed pattern** (`page.tsx:101-104`: "Generated 7/8/2026, 9:48:01 AM · gemini-2.5-flash"). The roster briefing already solved this with "Updated Jul 8." Fix: reuse the same friendly-date formatting; drop the model name from user-facing copy. Suggested command: /impeccable clarify.
- **[P2] "Scrape" jargon leaks into two empty states** (`page.tsx:109`, `FollowerChart.tsx:16`). Fix: reword to outcome-language ("needs a few more days of tracking data"). Suggested command: /impeccable clarify.
- **[P3] Mobile Recent Posts table drops columns with no affordance** (`RecentPostsTable.tsx`). Eng. rate and Views columns disappear at 390px with no scroll hint. Fix: add a horizontal-scroll fade/shadow cue, or keep the column and let it scroll. Suggested command: /impeccable adapt.

## Persona Red Flags

**Alex (Power User):** Recent Posts table has no sort/filter/collapse; will not scale past a handful of posts.

**Riley (Stress Tester):** clicked into an "attention"-flagged influencer expecting one clear signal and instead found the same data point reported three times with three different numbers — exactly the kind of inconsistency this persona documents methodically and loses trust over.

## Minor Observations

- `page.tsx:61` "need 2+ posts" is more clipped/technical than the friendlier tone used at `page.tsx:123` ("No standout highlights yet — growth-over-time insights need a few days of daily captures") on the same page.
- React key at `page.tsx:129` could collide once near-duplicate highlights share a timestamp and similar leading text — fragile, no visible breakage yet, but worth revisiting once the P0 dedup fix lands.
- Nested "card-in-card" on Performance-by-format tiles is a live overlay flag; not a rule violation, but worth a second look against the system's flat-surface preference.

## Questions to Consider

- Should highlights be deduped at the data layer (scraper) or the render layer? Render-layer is in scope for this pass; true root-cause dedup may belong in scraper/.
- Is there a shared "PageMeta" pattern worth extracting so timestamp/model formatting can't silently diverge between roster and detail pages again?
