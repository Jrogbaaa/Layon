# Spec - Feature 015: Direct Instagram Links from Engagement Chart Posts

## Previous Feature Context

Feature_014 synchronized chart-point and publication-rail selection inside
`EngagementChart.tsx` (hover/click/focus select the same post, persistent detail panel,
Europe/Madrid dates, deterministic fixture route). Its evaluator returned PASS (4.75/5)
with the default Playwright suite 16/16.

Alongside this feature (below the triviality threshold, no spec required): the nav tab
label "Trends" is renamed to "Tips" in `NavLinks.tsx`. The `/trends` route, page
content, and data flow are unchanged.

## Goal

Let a staff member jump from a plotted post on the engagement chart straight to the
actual Instagram post, so a spike can be inspected at the source in one click.

## Why It Matters / User Problem

The chart identifies which post spiked and when, but verifying *what* the post was
still requires leaving the dashboard and searching Instagram manually. Post shortcodes
are already stored on every `PostSnapshot`; the dashboard just never exposes them from
the chart (only the Greatest Hits and Recent Posts tables link out today).

## Intended User

Agency staff triaging influencer performance on desktop and mobile.

## Design / Interaction Direction

- Chart dots become links: clicking (or pressing Enter on) a chart point opens
  `https://www.instagram.com/p/{shortcode}/` in a new tab (`rel="noopener noreferrer"`).
  Hover/focus still select the post exactly as in feature_014; selection state and the
  Escape-to-clear behavior are unchanged.
- The selected-post detail panel gains a quiet "View on Instagram →" link for the same
  URL, so mobile users driving selection through the marker rail / arrow controls can
  reach the post without needing to hit a small chart dot.
- Accessible names change from "Select post: …" to "Open Instagram post: …" to match
  the new activation behavior. Selection state moves from `aria-pressed` (invalid on
  links) to a `data-selected` attribute; rail markers keep `aria-pressed`.
- Amber stays scarce: the new detail-panel link uses the existing accent link
  treatment already used elsewhere (e.g. "Source →", "View →").

## Scope

- `platform/app/components/EngagementChart.tsx` only (add `shortcode` to the local
  chart point mapping, convert the dot `<g role="button">` to an SVG `<a>`, add the
  detail-panel link).
- `platform/app/components/NavLinks.tsx` label rename (trivial, bundled).
- Update existing Playwright assertions in `platform/e2e/dashboard.spec.ts` that
  checked `aria-pressed` on chart points; add coverage that a chart dot and the detail
  panel expose the Instagram href.

## Non-Goals / Out of Scope

- No database, query, scraper, or schema changes — `shortcode` is already fetched.
- No route rename: `/trends` keeps its URL; only the visible tab label changes.
- No changes to the marker rail interaction model, tooltip content, Audience Log,
  or any other dashboard section.
- No link-validity checking against Instagram (deleted posts will 404 there; accepted).

## Acceptance Criteria

1. Clicking a chart dot opens the post's Instagram URL in a new tab; hover and focus
   still drive the synchronized selection from feature_014.
2. Each dot is keyboard reachable and activates as a link with an accessible name
   naming the post's date/format/engagement.
3. The selected-post detail panel shows a "View on Instagram →" link with the correct
   `https://www.instagram.com/p/{shortcode}/` href.
4. The nav tab reads "Tips" and still routes to `/trends` with active-state styling.
5. Existing chart behaviors (selection sync, Escape clear, mobile arrows, invalid
   timing states, empty/one-post states) remain green in the Playwright suite.
6. `npm run lint`, `npx tsc --noEmit`, `npm run build`, and `npx playwright test`
   pass in `platform/`.

## Verification Plan

- Update and run the Playwright dashboard + trends suites locally against the dev
  server, including the fixture scenarios.
- Manually confirm on localhost that a dot click opens the expected Instagram URL and
  the nav shows "Tips".
