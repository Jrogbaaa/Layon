# Spec - Feature 016: Platform UX and Frontend Overhaul

## Previous Feature Context

Feature_015 added direct Instagram links from the engagement chart points and renamed the nav tab from "Trends" to "Tips". Its evaluator pass was verified successfully.

## Goal

Resolve the key usability flaws, responsive blindspots, interaction bugs, underutilized data, and terminology discrepancies identified during the comprehensive UX audit.

## Why It Matters / User Problem

1.  **Mobile Triage:** Staff checking metrics on mobile screens are currently blind to overnight delta changes and trends.
2.  **Chart Usability:** Clicking links inside the engagement chart details box is nearly impossible because mouse movements hijack selection.
3.  **Findability:** Finding influencers in a growing list without search/filter takes too much time.
4.  **Information Completeness:** The platform hides influencer bios, followings, and post counts that the daily scraper collects.
5.  **Perceived Quality:** Page titles and navigations use inconsistent wording ("Tips" vs "Wire").

## Intended User

Agency talent managers reviewing daily roster performance on desktop and mobile viewports.

## Design & Interaction Direction

*   **Global Language Toggle:** Render the bilingual EN/ES toggle inside the global `Nav` header (on the right next to the logout button). Remove the local selectors from "The Dispatch" card on the Roster page, "The Brief" on the Influencer page, and "The Wire" page head to unify the control.
*   **Term Standardizations:** Rename navigation tab "Tips" to "Wire". The URL remains `/trends`, and the page header stays "The Wire".
*   **Roster Table Headers & Mobile Layout:**
    *   Add an uppercase, mono-font table header row: `01 · TALENT · FOLLOWERS · OVERNIGHT CHANGE · TRAJECTORY`.
    *   Add responsive grid columns. On mobile screens (`max-width: 639px`), the overnight delta value is displayed on a second row stacked underneath the handle or next to the followers count.
*   **Sort:**
    *   Introduce client-side sorting: sort by Followers (desc), Overnight Change (desc), or Handle (asc). The "Needs Attention" warnings filter checkbox was removed/omitted to keep the controls simple.
*   **Influencer Profile Completeness:**
    *   Expose bio text under the display name.
    *   Expose "Following" and "Total Posts" count metrics in the stats band.
*   **Engagement Chart Lock:**
    *   Implement hover-for-tooltip and click-to-lock interactions.
    *   Clicking a point sets a `lockedIndex` and renders a persistent guide line. Hovering over adjacent points changes tooltips but *does not* override the locked selection details card at the bottom.
    *   Add a close button (`×`) in the details card, and support pressing `Escape` or clicking empty chart areas to clear selection lock.
*   **Skeleton Loading Page:**
    *   Add a Next.js dynamic loading skeleton component (`loading.tsx`) to show skeleton outlines when fetching data from Supabase.
*   **Login password field:** Add a show/hide eye-toggle to change input type between `password` and `text`.

## Scope

- `platform/app/components/Nav.tsx`, `platform/app/components/NavLinks.tsx` (global navigation modifications).
- `platform/app/(app)/page.tsx` (roster filter, sort, headers, and mobile deltas).
- `platform/app/(app)/influencer/[handle]/page.tsx` (metadata titles, bio display, stats band, language toggle cleanup).
- `platform/app/(app)/trends/page.tsx` (metadata titles, local language toggle removal, fallback tags).
- `platform/app/components/EngagementChart.tsx` (hover tooltip + click lock, Escape/close button).
- `platform/app/login/page.tsx` (password visibility toggle).
- `platform/app/(app)/loading.tsx` (NEW loader skeleton).
- `platform/app/trends/` and `platform/app/influencer/` (DELETE placeholder directories).
- `platform/e2e/dashboard.spec.ts` and `platform/e2e/trends.spec.ts` (E2E assertions update).

## Non-Goals / Out of Scope

- No scraper logic modifications or third-party metrics scrapers.
- No Supabase database schema modifications.

## Acceptance Criteria

1.  Language setting is unified in the global header, and all localized card toggles are deleted.
2.  Navigation link text is "Wire" and routes to `/trends` successfully.
3.  The Roster page features table headers, warnings filter, and sorting dropdown.
4.  Follower overnight delta is visible on mobile viewports for each roster row.
5.  Influencer profile page displays bio text, following count, and post count.
6.  The engagement chart locks the selection details on click, allowing users to hover other points and click the details links without selection hijacking. An "Escape" key or "x" button clears lock.
7.  The LoginPage has a password show/hide visibility toggle.
8.  Next.js loader skeleton renders dynamically during routing delays.
9.  Orphan empty folders `platform/app/trends` and `platform/app/influencer` are removed.
10. All Playwright E2E tests, TypeScript compilation, and linting pass green.

## Verification Plan

*   Run `npx playwright test` and ensure E2E tests cover search inputs, mobile view changes, and details link clicking.
*   Manually check localhost behavior on mobile sizes.
