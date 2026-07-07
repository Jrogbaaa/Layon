# Influencer Profile Photos — Design

## Goal

Show each influencer's Instagram profile photo on their roster card (main dashboard)
and on their individual profile page, so the platform is visually identifiable at a
glance instead of handle-text-only.

## Why This Matters

The roster and detail pages currently show only `@handle` text. Agency staff scanning
the roster have to read handles rather than recognizing faces, which slows browsing
and makes the dashboard feel less like a real talent-management tool.

## Non-Goals

- No manual photo upload/override UI — photos are fully scraper-sourced.
- No image resizing/cropping pipeline — store the photo as Instagram returns it.
- No historical photo versioning — only the latest photo is kept per influencer.

## Design

### 1. Database

- `influencers` table gains a nullable column: `avatar_url text`.
- A new public Supabase Storage bucket, `avatars`, holds one object per influencer at
  a stable path: `avatars/{handle}.jpg`. Public read, service-key write (same trust
  model as the rest of the scraper's Supabase access).
- Because the storage path is keyed by handle (not by scrape timestamp), the public
  URL for a given influencer never changes — daily re-uploads simply overwrite the
  object in place, so `influencers.avatar_url` is set once and then stays valid.

### 2. Scraper (`scraper/youfirst_scraper/`)

- `instagram_scraper.py`: `scrape_profile()` adds `profile.profile_pic_url` to the
  returned `profile_data` dict as `avatar_source_url`.
- `db.py`: new function `upload_avatar(client, handle, image_bytes) -> str` that
  uploads to the `avatars` bucket at `{handle}.jpg` with `upsert=True` and returns the
  bucket's public URL. `insert_profile_snapshot` is unaffected; a new
  `update_influencer_avatar(client, influencer_id, avatar_url)` upserts the URL onto
  the `influencers` row.
- `run_daily.py` (and `backfill.py`, which shares the same per-influencer scrape
  step): after `scrape_profile()` returns, download `avatar_source_url` via `requests`
  (same pattern as other HTTP calls already in the codebase), and on success call
  `upload_avatar` + `update_influencer_avatar`. On any failure (network error, 403,
  missing URL) log a warning and continue — a missing photo must never fail the scrape
  run for that influencer.

### 3. Platform (`platform/app/`)

- `lib/types.ts`: `Influencer` gains `avatar_url: string | null`.
- `lib/data.ts`: both `getRoster()` and `getInfluencerDashboard()` add `avatar_url` to
  their `influencers` select.
- New component `Avatar.tsx`: takes `{ handle, avatarUrl, size }`. Renders a circular
  `<img>` when `avatarUrl` is set; otherwise renders a circular fallback showing the
  first letter of the handle, styled with the existing token palette (matches the
  "Fresh Current" redesign in progress — no ad-hoc colors).
- Roster page (`(app)/page.tsx`): small `Avatar` (e.g. 40px) placed to the left of
  `@handle` inside each card.
- Influencer detail page (`(app)/influencer/[handle]/page.tsx`): larger `Avatar` (e.g.
  64px) placed to the left of the `@handle` heading.
- Plain `<img>` tag, not `next/image` — avoids adding a remote-pattern entry to
  `next.config.ts` for a single external host, consistent with "simplicity first."

## Testing

- `scraper/`: unit tests for `upload_avatar` / `update_influencer_avatar` in `db.py`
  (mocked Supabase client, as with existing tests) and for the `avatar_source_url`
  field being present in `scrape_profile()`'s output (mocked Instaloader profile).
- `platform/`: extend existing Playwright coverage to assert an `<img>` (or fallback
  initials element) renders on both the roster card and the influencer detail page.
- Manual: after schema migration + one real scraper run, confirm actual Instagram
  photos render correctly in a running dev server for at least one real handle.

## Rollout

1. Apply the schema migration (`avatar_url` column) and create the `avatars` bucket in
   Supabase — manual, one-time, done by the user against their project.
2. Ship scraper + platform changes together (avatar_url will be `null` for all
   influencers until the next scraper run, which the fallback initials handle
   gracefully).
