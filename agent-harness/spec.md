# Spec - Feature 014: Synchronized Post Selection on the Engagement Chart

## Previous Feature Context

Feature_012 replaced the short follower-growth chart with the post-level
`EngagementChart`, preserving the up-to-30 deduplicated `chartPosts` dataset in
chronological order and adding the Audience Log grid.

Feature_013 added a restrained publication marker rail with accessible markers,
publication dates, post format, and relative intervals derived only from `posted_at`.
Its independent evaluator returned PASS (4.5 average), with build, lint, TypeScript,
Playwright (12/12), diff, and localhost/mobile checks passing. The evaluator's
non-blocking follow-ups were fixture-driven coverage for timestamp edge cases and an
explicit timezone convention. Feature_014 addresses the remaining interaction gap:
the chart tooltip and marker rail currently manage separate active states, so a spike
and its publication detail are not visibly one selected post.

## Goal

Make it obvious which engagement spike corresponds to which influencer post and date,
especially on mobile, by giving the chart and publication rail one synchronized
selected-post interaction model.

## Review Remediation — 2026-07-13

The pre-merge review found four gaps inside the approved goal: permissive JavaScript
date parsing, loss of persistent details when every timestamp is invalid, undersized
dense mobile marker targets, and live-data-dependent Playwright coverage. The user
approved correcting all four before merge. This remediation keeps the existing chart
contract and adds a development-only fixture route for deterministic browser coverage;
it does not add a production feature or data source.

## Why It Matters / User Problem

Agency staff use the chart to triage content performance. They should be able to move
from a spike to its post date and back without guessing at x-axis positions or losing
the detail when a pointer leaves the chart. The interaction should clarify timing and
cadence without implying that publication caused engagement.

## Intended User

Agency staff reviewing influencer performance and deciding which posts merit attention.
The change serves the internal dashboard workflow; it is not a new talent-facing or
developer-facing tool.

## What Success Looks Like

On desktop and a narrow mobile viewport, a staff member can select a chart point or its
publication marker and immediately see the same post highlighted in both places, with a
quiet vertical guide and a bounded detail treatment showing the post date, format, and
engagement context. The detail remains available until another post is selected, while
idle points stay legible and amber remains a scarce emphasis color.

## Design / Interaction Direction

- Keep one selected-post state inside `EngagementChart`, shared by the Recharts chart
  and the existing publication rail. Do not lift state into the page or change the
  data contract.
- Add subtle idle point affordances so posts read as inspectable without turning every
  point or rail marker into an amber accent. Use amber primarily for the selected point,
  selected marker, and selected vertical guide; retain the garnet-black canvas and
  existing Medianoche surface/hairline treatment.
- Synchronize hover, click, and keyboard focus from either surface to the same post.
  The selected point, corresponding marker, guide, and detail must agree. The selected
  detail persists after pointer exit or focus movement until another post is selected,
  subject to the clear-selection behavior approved in `open-questions.md`.
- Improve the date-axis labels with a restrained, deterministic cadence that remains
  readable for dense 30-post ranges. Full publication detail remains interaction-only;
  do not create a persistent label wall.
- Keep the mobile tooltip/detail inside the viewport with a bounded width and wrapping
  content. Preserve a useful fallback when the chart has no posts or timing is invalid.
- Keep the publication rail's accessible markers. Each marker remains keyboard
  reachable, has a meaningful accessible name, and selects the same post as its chart
  point; focus indication must not depend on hover.

## Scope

- Surgical interaction, presentation, and local data-mapping changes in
  `platform/app/components/EngagementChart.tsx` only.
- Focused Playwright coverage in the existing `platform/e2e/dashboard.spec.ts` for
  chart/rail synchronization, persistent selected detail, keyboard accessibility,
  selected guide/affordance state, improved axis/tooltip behavior, and a 390px mobile
  smoke check.
- A development-only `platform/app/test-fixtures/engagement-chart/page.tsx` route may
  provide deterministic edge-case inputs to the real component. It must return 404 in
  production and must not query or persist data.
- `platform/playwright.config.ts` may serialize the browser suite when required to make
  the documented default `npx playwright test` command deterministic against the shared
  local dashboard environment.
- Reuse the existing `PostSnapshot`, `chartPosts`, `posted_at`, engagement, ER, format,
  and caption data. No new persisted fields or schema changes.

## Non-Goals / Out of Scope

- No database, Supabase query, scraper, schema, or post-selection changes.
- No backfill or repair of missing/invalid `posted_at` values, and no use of
  `captured_at` as a publication-time proxy.
- No influencer-brand matching, recommendation logic, automated spike attribution, or
  causal claim about publication timing.
- No new timeline chart, post cards, always-visible date labels, navigation/auth
  changes, Audience Log changes, or unrelated dashboard work.
- No broad Recharts refactor, new dependency, new production component, or redesign of
  the surrounding dashboard.

## Acceptance Criteria

1. The existing up-to-30 chronological `chartPosts` dataset, Likes + Comments
   engagement series, median reference line, empty state, and Audience Log remain
   unchanged in purpose and data source.
2. Each plotted post has a subtle, discoverable point affordance; idle points and rail
   markers remain quiet enough that amber is reserved for active emphasis.
3. Selecting a chart point by hover, click, or keyboard focus selects the corresponding
   rail marker, and selecting a rail marker selects the corresponding chart point.
   Both surfaces expose the same post date, format, engagement/ER context, and relative
   interval when timing is valid.
4. The selected post has a clearly visible vertical guide and coordinated selected
   styling in the chart and rail. Selected detail persists after hover/focus leaves
   the control until another post is selected, with the approved clear behavior.
5. Publication markers remain keyboard reachable with meaningful accessible names and
   visible focus state; the synchronized selection is usable without a mouse or hover.
6. Date-axis labels use the approved deterministic display convention and restrained
   cadence; labels do not collide or become an unreadable wall across a 30-post range.
7. The chart tooltip and/or selected detail stays within the viewport at the existing
   narrow/mobile width, wraps long content, and does not obscure the selected marker or
   make the chart horizontally scroll.
8. Same-day posts remain distinct and independently selectable. Missing, malformed, or
   non-finite `posted_at` values never create fabricated dates or intervals; their
   engagement remains usable and timing is reported as unavailable.
9. No-post and one-post states render without exceptions; a valid first plotted post
   still uses clear first-post wording rather than a misleading interval.
10. Focused Playwright coverage verifies bidirectional chart/rail selection, persistence,
    keyboard/focus behavior, accessible marker names, selected-guide state, and the
    mobile-width tooltip/detail bounds. `npm run lint`, `npx tsc --noEmit`, and
    `npm run build` remain green in `platform/`.

## Open Questions Requiring User Approval

See `agent-harness/open-questions.md`. The plan recommends `Europe/Madrid` for display
formatting because the intended users are Spain-based agency staff, but this is not
treated as final until approved.

## Verification Plan

- Run the focused dashboard Playwright coverage against the local authenticated
  dashboard, including keyboard selection, chart-to-rail and rail-to-chart sync,
  persistence after pointer exit, and a 390px viewport.
- Run `npx tsc --noEmit`, `npm run lint`, and `npm run build` from `platform/`.
- Manually inspect an influencer detail page on localhost for a high-engagement point,
  a dense date range, and tooltip/detail bounds on mobile. If same-day, invalid-date,
  or no-post live data is unavailable, record it as not run rather than a product bug.
- The Evaluator must independently review the implementation and update
  `agent-harness/findings.md` before the feature is considered complete.
