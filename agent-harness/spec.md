# Spec

## Goal of This Change

Redesign the platform's visual identity end to end — palette, typography, card and
chart styling — replacing the ad-hoc dark neutral/amber theme with a single deliberate
light direction, "Fresh Current":

1. Introduce centralized semantic color tokens in `globals.css` (Tailwind v4 `@theme`)
   instead of scattered inline `neutral-*`/`amber-*`/`emerald-*`/`red-4*` literals.
2. Swap the loaded fonts (Geist/Geist Mono, effectively dead behind a hardcoded Arial
   body override) for Plus Jakarta Sans (display) + Inter (body), and fix the override.
3. Apply the new tokens/fonts across Nav, roster, influencer detail, trends, and login
   pages, plus the Recharts follower-growth chart's hardcoded hex values.
4. Give the login page a small signature moment (gradient wordmark + gradient CTA) as
   the one deliberate accent, per the frontend-design skill's "spend your boldness in
   one place" principle.

## Why This Matters

The user asked for a full visual redesign with metrics presentation as clean and
scannable as a reference tool (Kolsquare) they use for comparison. The existing UI had
no central palette — every color was a repeated Tailwind literal — making it look
generic and inconsistent, and a leftover Arial override meant the loaded Geist fonts
were never actually rendering.

## Intended User

Agency staff and talent reading the platform dashboard daily.

## Process

Five distinct directions (Fresh Current, Madrid Editorial, Studio Ink, Ledger, Sol)
were mocked up as an HTML artifact against the real page layouts with representative
data, reviewed with the user, and "Fresh Current" was selected.

## Success Criteria

1. `globals.css` defines `canvas`, `card`, `border`, `ink`, `muted`, `accent`,
   `accent-2`, `positive`, `positive-soft`, `negative`, `negative-soft` tokens; a `.card`
   helper class centralizes the repeated card shadow/radius/border.
2. `app/layout.tsx` loads Plus Jakarta Sans + Inter; `body` font-family resolves to the
   loaded font (no Arial override).
3. No `neutral-*`/`amber-*`/`emerald-*`/`red-4*` classes remain anywhere in `app/`.
4. `FollowerChart.tsx` grid/axis/tooltip/line colors updated to the new palette with a
   two-stop gradient line.
5. `npm run build`, `npm run lint` pass; existing Playwright suite (5/5) passes
   unmodified (behavior didn't change, only styling).
6. Scraper pytest suite (64/64) unaffected — confirms the change stayed platform-only.
7. Roster and influencer detail pages visually verified against a running dev server.

## Non-Goals / Out of Scope

- No new pages, features, or data changes — visual layer only.
- No auth/session model changes.
- No dark mode / theme toggle — one fixed light theme.
- No changes to scraper/, metrics calculations, or recommendation generation.

## Open Questions

None — user selected "Fresh Current" from the five mocked-up directions on 2026-07-07.
