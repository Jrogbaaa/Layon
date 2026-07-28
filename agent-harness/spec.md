# Spec - Feature 018: Accurate Paid Media / Organic Classification

## Previous Feature Context

Feature_017 added an `is_ad` boolean column and UI badges driven by Instaloader's
`post.is_sponsored` flag, evaluated PASS at the time. In practice `is_sponsored` almost
never fires (Instagram-declared paid partnerships only), so a same-session follow-up
built a Gemini multimodal classifier — but its first prompt flagged any visible brand
logo as an ad (e.g. a MotoGP racer's sponsor-covered gear scored 98% ads), which is
this feature's starting problem.

## Goal

Replace the over-aggressive ad-detection prompt with a strict, decidable rubric —
"is a product deliberately featured or mentioned?" — and rename the UI from "Ad" to
"Paid Media" / "Organic" throughout. Retroactively reclassify every stored post against
the new rubric, surfacing genuinely ambiguous posts for manual user review instead of
guessing.

## Why It Matters / User Problem

Agency managers need to trust the paid/organic split to evaluate genuine audience
traction vs. commercial engagements. A classifier that treats incidental brand
visibility (sponsor logos, background signage, venue mentions) as "paid" produces
unusable, misleading data — a false positive rate the user immediately spotted and
rejected.

## Intended User

Agency talent managers reviewing daily roster performance.

## Rubric (replaces Feature 017's Gemini prompt)

- **paid**: a product is deliberately featured — held up/used/presented as the subject
  of the shot, or mentioned/promoted in the caption (including discount codes, links,
  brand @mentions presenting a product, or disclosure tags: #ad, #sponsored, #publi,
  #publicidad, #colaboración, "paid partnership").
- **organic**: no product featured or mentioned. Explicitly organic even with visible
  brand imagery: athletes/public figures in professional gear/uniforms covered in
  sponsor logos; logos/storefronts/signage in the background; mentioning a venue,
  event, or friend's account without promoting a product.
- **unsure**: genuinely ambiguous — never guessed. Collected and reported to the user
  with the post's Instagram link for a manual verdict.

## Scope

- `scraper/youfirst_scraper/ad_detection.py` — rewritten prompt (reason-first JSON,
  three-way classification), `detect_ad` returns `"paid" | "organic" | "unsure"`.
- `scraper/youfirst_scraper/backfill_ads.py` — re-checks every stored post (not just
  previously-unflagged ones); re-derives media via one profile re-scrape per
  influencer (post_snapshots never persisted `thumbnail_url`/`video_url`), matching
  by shortcode with an early-stop once every needed shortcode for that influencer is
  found; writes `is_ad` back unconditionally per snapshot row; logs a per-influencer
  paid/organic/unsure breakdown and a full unsure list with Instagram links.
- `scraper/youfirst_scraper/run_daily.py` — session-expiry notification points at the
  cookie-import recovery command instead of the blocked `--login` flow.
- `scraper/youfirst_scraper/instagram_scraper.py`, `config.py`, `scraper/README.md` —
  documentation updated to `instaloader --load-cookies Chrome` as the only supported
  auth path; `--login` explicitly called out as broken for this account.
- `platform/app/components/EngagementChart.tsx` — tooltip shows "· Paid Media" or
  "· Organic"; `PublicationDetails` badge renders "Paid Media" or an "Organic" variant
  (muted, no amber fill); dot aria-label says "Paid media, ...".
- `platform/app/components/RecentPostsTable.tsx`,
  `platform/app/(app)/influencer/[handle]/page.tsx` — badge text "Ad" → "Paid Media"
  (shown only on paid posts, per the Signal Rule).
- `platform/e2e/dashboard.spec.ts` — updated assertions for "Paid Media" text, added an
  assertion that a non-ad point's tooltip shows "· Organic".

## Non-Goals / Out of Scope

- No three-way `is_ad` column (stays boolean: paid → true, organic/unsure → false).
- No automated resolution of "unsure" posts — always a human verdict.
- No change to how `is_ad` propagates through `data.ts`/`types.ts` (unchanged from
  Feature 017).
- No Instagram Graph API migration or paid scraping provider (evaluated as a possible
  future step in agent-harness/decisions.md, not built).

## Acceptance Criteria

1. `ad_detection.detect_ad` returns "paid"/"organic"/"unsure" per the rubric above; a
   platform-declared paid partnership (`post.is_sponsored`) short-circuits to "paid".
2. `backfill_ads.py` re-classifies every unique (influencer, shortcode) pair in
   `post_snapshots`, updates `is_ad` on all matching rows, and prints a per-influencer
   paid/organic/unsure count plus a full unsure list with Instagram links.
3. A post with only incidental brand visibility (e.g. sponsor-logo gear) classifies
   organic; a post with an explicit disclosure tag or product-holding shot classifies
   paid.
4. Chart tooltip/details card show "Paid Media" or "Organic"; table/Greatest Hits show
   a "Paid Media" badge only (no "Organic" badge, to keep the amber accent scarce).
5. `pytest`, `npm run lint`, `npx tsc --noEmit`, and `npx playwright test` all pass.
6. Instagram auth path documented and working end-to-end via cookie import; no code or
   docs reference `instaloader --login` as the recovery path.

## Verification Plan

- `pytest` in `scraper/` for unit coverage.
- `python -m youfirst_scraper.backfill_ads` against real Supabase/Instagram data —
  review the per-influencer breakdown and the unsure list with the user before
  committing.
- `npx playwright test` for the renamed-label e2e coverage.
- Manual dev-server check: hover a paid vs. organic chart point, confirm labels.
