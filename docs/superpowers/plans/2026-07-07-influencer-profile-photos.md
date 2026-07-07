# Influencer Profile Photos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show each influencer's Instagram profile photo on their roster card and on their individual profile page.

**Architecture:** The scraper downloads each influencer's Instagram avatar during its
existing per-handle scrape loop and re-uploads it to a stable path in a public Supabase
Storage bucket (`avatars/{handle}.jpg`), then stores that stable public URL on the
`influencers` row. The platform reads `avatar_url` alongside the rest of the roster/
dashboard data it already fetches and renders it through one shared `Avatar` component
(circular photo, or an initials fallback when `avatar_url` is null) used on both the
roster cards and the influencer detail page header.

**Tech Stack:** Python (Instaloader, `requests`, `supabase-py`) for the scraper; Next.js
App Router + Tailwind v4 tokens for the platform; pytest and Playwright for tests.

## Global Constraints

- Photo uploads/lookups must never fail the scrape run for that influencer — catch and
  log, continue to the next influencer (matches existing `except Exception: logger.exception(...)` pattern in `run_daily.py` / `backfill.py`).
- No `next/image` — plain `<img>`, to avoid adding a remote-pattern host to `next.config.ts`.
- No manual upload path, no image resizing/cropping, no photo history — scraper-sourced only, latest photo overwrites the previous one in place.
- Match existing code style: scraper functions take `client: Client` as first arg like
  the rest of `db.py`; platform components use the existing `--color-*` tokens from
  `globals.css` (`accent`, `accent-2`, `card`, `border`, `ink`, `muted`), not new ad-hoc colors.

---

## File Structure

- Modify: `scraper/schema.sql` — add `avatar_url` column to `influencers`.
- Modify: `scraper/youfirst_scraper/instagram_scraper.py` — capture `avatar_source_url` in `scrape_profile()`'s returned profile dict.
- Modify: `scraper/youfirst_scraper/db.py` — add `upload_avatar()` and `update_influencer_avatar()`.
- Create: `scraper/tests/test_db.py` — unit tests for the two new `db.py` functions (no existing test file for `db.py` yet).
- Modify: `scraper/tests/test_instagram_scraper.py` — test `avatar_source_url` is included.
- Modify: `scraper/youfirst_scraper/run_daily.py` — call avatar upload+update inside `run_instagram_scrape()`.
- Modify: `scraper/youfirst_scraper/backfill.py` — same call inside `run_backfill_scrape()`.
- Modify: `scraper/tests/test_run_daily.py` — cover the new calls (and their failure isolation).
- Modify: `scraper/tests/test_backfill.py` — same coverage for backfill's loop.
- Modify: `platform/app/lib/types.ts` — add `avatar_url` to `Influencer`.
- Modify: `platform/app/lib/data.ts` — select `avatar_url` in `getRoster()` and `getInfluencerDashboard()`.
- Create: `platform/app/components/Avatar.tsx` — shared circular photo/initials component.
- Modify: `platform/app/(app)/page.tsx` — render `Avatar` on each roster card.
- Modify: `platform/app/(app)/influencer/[handle]/page.tsx` — render `Avatar` next to the handle heading.
- Modify: `platform/e2e/dashboard.spec.ts` — assert an avatar element renders on both pages.

---

## Task 1: Schema — add `avatar_url` column

**Files:**
- Modify: `scraper/schema.sql:4-11`

**Interfaces:**
- Produces: `influencers.avatar_url` (nullable text column) that Task 3 writes to and Task 8 reads from.

- [ ] **Step 1: Add the column to the `influencers` table definition**

Edit `scraper/schema.sql` lines 4-11 to:

```sql
create table if not exists influencers (
  id bigint generated always as identity primary key,
  handle text not null unique,
  display_name text,
  persona text,
  avatar_url text,
  active boolean not null default true,
  created_at timestamptz not null default now()
);
```

- [ ] **Step 2: Add an idempotent `alter table` for existing databases**

This repo's `schema.sql` is run with `create table if not exists`, which won't retrofit
existing tables. Add directly below the `influencers` table definition (before the
`profile_snapshots` table, i.e. after the new line 12):

```sql
alter table influencers add column if not exists avatar_url text;
```

- [ ] **Step 3: Commit**

```bash
git add scraper/schema.sql
git commit -m "schema: add avatar_url column to influencers"
```

**Note for the user (not an automated step):** this SQL must be run manually against
the Supabase project (SQL Editor), and a public Storage bucket named `avatars` must be
created manually in the Supabase dashboard (Storage → New bucket → name `avatars`,
Public bucket: on). No task in this plan can do this for you — call it out in the final
summary.

---

## Task 2: Scraper — capture the Instagram avatar source URL

**Files:**
- Modify: `scraper/youfirst_scraper/instagram_scraper.py:81-90`
- Test: `scraper/tests/test_instagram_scraper.py`

**Interfaces:**
- Produces: `scrape_profile()`'s returned dict gains `profile["avatar_source_url"]: str | None`, consumed by Task 4/5.

- [ ] **Step 1: Write the failing test**

Add to `scraper/tests/test_instagram_scraper.py`:

```python
def test_scrape_profile_includes_avatar_source_url(monkeypatch):
    fake_profile = MagicMock()
    fake_profile.followers = 100
    fake_profile.followees = 10
    fake_profile.mediacount = 5
    fake_profile.biography = "bio"
    fake_profile.profile_pic_url = "https://instagram.example/pic.jpg"
    fake_profile.get_posts.return_value = []

    monkeypatch.setattr(
        instagram_scraper.instaloader.Profile, "from_username", lambda ctx, handle: fake_profile
    )

    result = instagram_scraper.scrape_profile(MagicMock(), "somehandle")

    assert result["profile"]["avatar_source_url"] == "https://instagram.example/pic.jpg"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scraper && python -m pytest tests/test_instagram_scraper.py::test_scrape_profile_includes_avatar_source_url -v`
Expected: FAIL with `KeyError: 'avatar_source_url'`

- [ ] **Step 3: Add the field in `scrape_profile()`**

In `scraper/youfirst_scraper/instagram_scraper.py`, change the `profile_data` dict
(currently lines 83-88):

```python
    profile_data = {
        "followers": profile.followers,
        "following": profile.followees,
        "media_count": profile.mediacount,
        "bio": profile.biography,
        "avatar_source_url": profile.profile_pic_url,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scraper && python -m pytest tests/test_instagram_scraper.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add scraper/youfirst_scraper/instagram_scraper.py scraper/tests/test_instagram_scraper.py
git commit -m "scraper: capture Instagram avatar source URL in scrape_profile"
```

---

## Task 3: Scraper — `db.py` avatar upload + influencer update

**Files:**
- Modify: `scraper/youfirst_scraper/db.py`
- Create: `scraper/tests/test_db.py`

**Interfaces:**
- Consumes: `supabase.Client` (already used throughout `db.py`); `client.storage.from_("avatars")` Storage API (`upload`, `get_public_url`) from the `supabase` package already in `requirements.txt`.
- Produces:
  - `upload_avatar(client: Client, handle: str, image_bytes: bytes) -> str` — uploads/overwrites `{handle}.jpg` in the `avatars` bucket, returns the public URL.
  - `update_influencer_avatar(client: Client, influencer_id: int, avatar_url: str) -> None` — updates `influencers.avatar_url` for that row.
  Both are consumed by Task 4 and Task 5.

- [ ] **Step 1: Write the failing tests**

Create `scraper/tests/test_db.py`:

```python
from unittest.mock import MagicMock

from youfirst_scraper import db


def test_upload_avatar_uploads_and_returns_public_url():
    client = MagicMock()
    bucket = client.storage.from_.return_value
    bucket.get_public_url.return_value = "https://supabase.example/storage/v1/object/public/avatars/somehandle.jpg"

    result = db.upload_avatar(client, "somehandle", b"fake-image-bytes")

    client.storage.from_.assert_called_with("avatars")
    bucket.upload.assert_called_once()
    args, kwargs = bucket.upload.call_args
    assert args[0] == "somehandle.jpg"
    assert args[1] == b"fake-image-bytes"
    assert kwargs["file_options"]["upsert"] == "true"
    assert result == "https://supabase.example/storage/v1/object/public/avatars/somehandle.jpg"


def test_update_influencer_avatar_updates_by_id():
    client = MagicMock()
    table = client.table.return_value
    update = table.update.return_value

    db.update_influencer_avatar(client, 42, "https://example.com/a.jpg")

    client.table.assert_called_with("influencers")
    table.update.assert_called_with({"avatar_url": "https://example.com/a.jpg"})
    update.eq.assert_called_with("id", 42)
    update.eq.return_value.execute.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd scraper && python -m pytest tests/test_db.py -v`
Expected: FAIL with `AttributeError: module 'youfirst_scraper.db' has no attribute 'upload_avatar'`

- [ ] **Step 3: Implement both functions**

Add to `scraper/youfirst_scraper/db.py`, after `delete_influencer_by_handle` (after line 22):

```python
def upload_avatar(client: Client, handle: str, image_bytes: bytes) -> str:
    path = f"{handle}.jpg"
    client.storage.from_("avatars").upload(
        path,
        image_bytes,
        file_options={"content-type": "image/jpeg", "upsert": "true"},
    )
    return client.storage.from_("avatars").get_public_url(path)


def update_influencer_avatar(client: Client, influencer_id: int, avatar_url: str) -> None:
    client.table("influencers").update({"avatar_url": avatar_url}).eq("id", influencer_id).execute()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd scraper && python -m pytest tests/test_db.py -v`
Expected: both PASS

- [ ] **Step 5: Commit**

```bash
git add scraper/youfirst_scraper/db.py scraper/tests/test_db.py
git commit -m "scraper: add upload_avatar and update_influencer_avatar to db.py"
```

---

## Task 4: Scraper — wire avatar download+upload into `run_daily.py`

**Files:**
- Modify: `scraper/youfirst_scraper/run_daily.py:23-56`
- Test: `scraper/tests/test_run_daily.py`

**Interfaces:**
- Consumes: `instagram_scraper.scrape_profile()` (Task 2's `avatar_source_url` field), `db.upload_avatar`, `db.update_influencer_avatar` (Task 3).
- Produces: nothing consumed elsewhere — this is a leaf integration.

- [ ] **Step 1: Write the failing test**

Add to `scraper/tests/test_run_daily.py`:

```python
def test_run_instagram_scrape_uploads_avatar(monkeypatch):
    monkeypatch.setattr(run_daily.config, "load_roster", lambda: ["good_handle"])
    monkeypatch.setattr(run_daily.config, "PROFILE_REQUEST_DELAY_SECONDS", 0)

    monkeypatch.setattr(
        run_daily.instagram_scraper,
        "scrape_profile",
        lambda loader, handle: {
            "profile": {
                "followers": 1,
                "following": 2,
                "media_count": 3,
                "bio": "",
                "avatar_source_url": "https://instagram.example/pic.jpg",
            },
            "posts": [],
        },
    )

    monkeypatch.setattr(run_daily.db, "get_or_create_influencer", lambda c, h: 7)
    monkeypatch.setattr(run_daily.db, "insert_profile_snapshot", lambda c, i, p: None)
    monkeypatch.setattr(run_daily.db, "insert_post_snapshots", lambda c, i, p: None)
    monkeypatch.setattr(run_daily.db, "get_analyzed_shortcodes", lambda c, i: set())
    monkeypatch.setattr(run_daily.content_analysis, "analyze_posts", lambda posts, analyzed: [])
    monkeypatch.setattr(run_daily.db, "insert_post_content", lambda c, i, a: None)
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_all_post_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "insert_highlights", lambda c, i, h: None)

    fake_response = MagicMock()
    fake_response.content = b"fake-image-bytes"
    fake_response.raise_for_status = lambda: None
    monkeypatch.setattr(run_daily.requests, "get", lambda url, timeout=None: fake_response)

    upload_calls = []
    monkeypatch.setattr(
        run_daily.db,
        "upload_avatar",
        lambda c, handle, image_bytes: upload_calls.append((handle, image_bytes)) or "https://cdn.example/good_handle.jpg",
    )
    avatar_update_calls = []
    monkeypatch.setattr(
        run_daily.db,
        "update_influencer_avatar",
        lambda c, influencer_id, url: avatar_update_calls.append((influencer_id, url)),
    )

    with patch("instaloader.Instaloader"):
        run_daily.run_instagram_scrape(MagicMock())

    assert upload_calls == [("good_handle", b"fake-image-bytes")]
    assert avatar_update_calls == [(7, "https://cdn.example/good_handle.jpg")]


def test_run_instagram_scrape_continues_when_avatar_download_fails(monkeypatch):
    monkeypatch.setattr(run_daily.config, "load_roster", lambda: ["good_handle"])
    monkeypatch.setattr(run_daily.config, "PROFILE_REQUEST_DELAY_SECONDS", 0)

    monkeypatch.setattr(
        run_daily.instagram_scraper,
        "scrape_profile",
        lambda loader, handle: {
            "profile": {
                "followers": 1,
                "following": 2,
                "media_count": 3,
                "bio": "",
                "avatar_source_url": "https://instagram.example/pic.jpg",
            },
            "posts": [],
        },
    )

    monkeypatch.setattr(run_daily.db, "get_or_create_influencer", lambda c, h: 7)
    monkeypatch.setattr(run_daily.db, "insert_profile_snapshot", lambda c, i, p: None)
    monkeypatch.setattr(run_daily.db, "insert_post_snapshots", lambda c, i, p: None)
    monkeypatch.setattr(run_daily.db, "get_analyzed_shortcodes", lambda c, i: set())
    monkeypatch.setattr(run_daily.content_analysis, "analyze_posts", lambda posts, analyzed: [])
    monkeypatch.setattr(run_daily.db, "insert_post_content", lambda c, i, a: None)
    monkeypatch.setattr(run_daily.db, "get_profile_snapshots", lambda c, i: [])
    monkeypatch.setattr(run_daily.db, "get_all_post_snapshots", lambda c, i: [])
    highlight_calls = []
    monkeypatch.setattr(run_daily.db, "insert_highlights", lambda c, i, h: highlight_calls.append(i))

    def raise_network_error(url, timeout=None):
        raise Exception("network error")

    monkeypatch.setattr(run_daily.requests, "get", raise_network_error)

    with patch("instaloader.Instaloader"):
        run_daily.run_instagram_scrape(MagicMock())

    assert highlight_calls == [7]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd scraper && python -m pytest tests/test_run_daily.py -v`
Expected: FAIL — `AttributeError: module 'youfirst_scraper.run_daily' has no attribute 'requests'` (and the upload/update calls are never made)

- [ ] **Step 3: Wire the avatar fetch into `run_instagram_scrape`**

In `scraper/youfirst_scraper/run_daily.py`, add `import requests` to the top-level
imports (line 1-6 becomes):

```python
import logging
import time
from datetime import date, datetime

import requests

from . import config, content_analysis, db, instagram_scraper, metrics, recommendations, trend_scraper
```

Then, inside `run_instagram_scrape`'s per-handle `try` block (currently lines 32-49),
insert the avatar step right after `influencer_id = db.get_or_create_influencer(client, handle)`:

```python
            influencer_id = db.get_or_create_influencer(client, handle)

            avatar_source_url = result["profile"].get("avatar_source_url")
            if avatar_source_url:
                try:
                    response = requests.get(avatar_source_url, timeout=10)
                    response.raise_for_status()
                    avatar_url = db.upload_avatar(client, handle, response.content)
                    db.update_influencer_avatar(client, influencer_id, avatar_url)
                except Exception:
                    logger.exception("Failed to update avatar for %s — continuing", handle)

            db.insert_profile_snapshot(client, influencer_id, result["profile"])
```

(The rest of the `try` block after `insert_profile_snapshot` is unchanged.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd scraper && python -m pytest tests/test_run_daily.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add scraper/youfirst_scraper/run_daily.py scraper/tests/test_run_daily.py
git commit -m "scraper: download and store influencer avatars during daily run"
```

---

## Task 5: Scraper — wire the same avatar step into `backfill.py`

**Files:**
- Modify: `scraper/youfirst_scraper/backfill.py:1-38`
- Test: `scraper/tests/test_backfill.py`

**Interfaces:**
- Consumes: same as Task 4 (`db.upload_avatar`, `db.update_influencer_avatar`, `requests.get`).

- [ ] **Step 1: Write the failing test**

`scraper/tests/test_backfill.py` currently only covers `run_recommendations` (it has no
existing test for `run_backfill_scrape`), so this test is additive — no existing
pattern to match. Add to `scraper/tests/test_backfill.py`:

```python
def test_run_backfill_scrape_uploads_avatar(monkeypatch):
    monkeypatch.setattr(backfill.config, "load_roster", lambda: ["good_handle"])
    monkeypatch.setattr(backfill.config, "PROFILE_REQUEST_DELAY_SECONDS", 0)

    monkeypatch.setattr(
        backfill.instagram_scraper,
        "scrape_profile",
        lambda loader, handle, post_limit=None: {
            "profile": {
                "followers": 1,
                "following": 2,
                "media_count": 3,
                "bio": "",
                "avatar_source_url": "https://instagram.example/pic.jpg",
            },
            "posts": [],
        },
    )

    monkeypatch.setattr(backfill.db, "get_or_create_influencer", lambda c, h: 9)
    monkeypatch.setattr(backfill.db, "insert_profile_snapshot", lambda c, i, p: None)
    monkeypatch.setattr(backfill.db, "insert_post_snapshots", lambda c, i, p: None)
    monkeypatch.setattr(backfill.db, "get_profile_snapshots", lambda c, i: [])
    monkeypatch.setattr(backfill.db, "get_all_post_snapshots", lambda c, i: [])
    monkeypatch.setattr(backfill.db, "insert_highlights", lambda c, i, h: None)

    fake_response = MagicMock()
    fake_response.content = b"fake-image-bytes"
    fake_response.raise_for_status = lambda: None
    monkeypatch.setattr(backfill.requests, "get", lambda url, timeout=None: fake_response)

    upload_calls = []
    monkeypatch.setattr(
        backfill.db,
        "upload_avatar",
        lambda c, handle, image_bytes: upload_calls.append((handle, image_bytes)) or "https://cdn.example/good_handle.jpg",
    )
    avatar_update_calls = []
    monkeypatch.setattr(
        backfill.db,
        "update_influencer_avatar",
        lambda c, influencer_id, url: avatar_update_calls.append((influencer_id, url)),
    )

    with patch("instaloader.Instaloader"):
        backfill.run_backfill_scrape(MagicMock())

    assert upload_calls == [("good_handle", b"fake-image-bytes")]
    assert avatar_update_calls == [(9, "https://cdn.example/good_handle.jpg")]
```

Add the needed imports at the top of `scraper/tests/test_backfill.py` if not already
present: `from unittest.mock import MagicMock, patch` and `from youfirst_scraper import backfill`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd scraper && python -m pytest tests/test_backfill.py -v`
Expected: FAIL (no `requests` attribute on `backfill`, no avatar calls made)

- [ ] **Step 3: Apply the same wiring as Task 4 to `backfill.py`**

Add `import requests` to `scraper/youfirst_scraper/backfill.py`'s imports (lines 1-3
become):

```python
import logging
import time

import requests

from . import config, db, instagram_scraper, metrics, recommendations
```

Then in `run_backfill_scrape`'s `try` block (currently lines 20-33), insert the same
block after `influencer_id = db.get_or_create_influencer(client, handle)`:

```python
            influencer_id = db.get_or_create_influencer(client, handle)

            avatar_source_url = result["profile"].get("avatar_source_url")
            if avatar_source_url:
                try:
                    response = requests.get(avatar_source_url, timeout=10)
                    response.raise_for_status()
                    avatar_url = db.upload_avatar(client, handle, response.content)
                    db.update_influencer_avatar(client, influencer_id, avatar_url)
                except Exception:
                    logger.exception("Failed to update avatar for %s — continuing", handle)

            db.insert_profile_snapshot(client, influencer_id, result["profile"])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd scraper && python -m pytest tests/test_backfill.py -v`
Expected: all PASS

- [ ] **Step 5: Run the full scraper test suite**

Run: `cd scraper && python -m pytest -v`
Expected: all PASS (no regressions in `test_run_daily.py`, `test_instagram_scraper.py`, `test_db.py`)

- [ ] **Step 6: Commit**

```bash
git add scraper/youfirst_scraper/backfill.py scraper/tests/test_backfill.py
git commit -m "scraper: download and store influencer avatars during backfill"
```

---

## Task 6: Platform — `avatar_url` in types and data queries

**Files:**
- Modify: `platform/app/lib/types.ts:1-5`
- Modify: `platform/app/lib/data.ts:16-21,53-58`

**Interfaces:**
- Produces: `Influencer.avatar_url: string | null`, present on every `RosterEntry.influencer` and `InfluencerDashboard.influencer` returned by `getRoster()` / `getInfluencerDashboard()` — consumed by Task 8/9.

- [ ] **Step 1: Add the field to the type**

Edit `platform/app/lib/types.ts:1-5`:

```typescript
export type Influencer = {
  id: number;
  handle: string;
  display_name: string | null;
  avatar_url: string | null;
};
```

- [ ] **Step 2: Select it in `getRoster()`**

In `platform/app/lib/data.ts`, change the `influencers` select (currently lines 18-21):

```typescript
  const { data: influencers } = await client
    .from("influencers")
    .select("id, handle, display_name, avatar_url")
    .eq("active", true)
    .order("handle");
```

- [ ] **Step 3: Select it in `getInfluencerDashboard()`**

In `platform/app/lib/data.ts`, change the single-influencer select (currently around
lines 55-58):

```typescript
  const { data: influencer } = await client
    .from("influencers")
    .select("id, handle, display_name, avatar_url")
    .eq("handle", handle)
    .single();
```

- [ ] **Step 4: Type-check**

Run: `cd platform && npx tsc --noEmit`
Expected: no errors

- [ ] **Step 5: Commit**

```bash
git add platform/app/lib/types.ts platform/app/lib/data.ts
git commit -m "platform: select avatar_url for roster and influencer dashboard queries"
```

---

## Task 7: Platform — shared `Avatar` component

**Files:**
- Create: `platform/app/components/Avatar.tsx`

**Interfaces:**
- Consumes: nothing project-specific (pure presentational component).
- Produces: `Avatar({ handle, avatarUrl, size }: { handle: string; avatarUrl: string | null; size: "sm" | "lg" })` — a React component, default export not used (named export `Avatar`), consumed by Task 8 and Task 9.

- [ ] **Step 1: Write the component**

Create `platform/app/components/Avatar.tsx`:

```tsx
const SIZE_CLASSES = {
  sm: "h-10 w-10 text-sm",
  lg: "h-16 w-16 text-xl",
} as const;

export function Avatar({
  handle,
  avatarUrl,
  size,
}: {
  handle: string;
  avatarUrl: string | null;
  size: "sm" | "lg";
}) {
  const sizeClass = SIZE_CLASSES[size];

  if (avatarUrl) {
    return (
      <img
        src={avatarUrl}
        alt={`@${handle}`}
        className={`${sizeClass} shrink-0 rounded-full border border-border object-cover`}
      />
    );
  }

  return (
    <div
      className={`${sizeClass} flex shrink-0 items-center justify-center rounded-full border border-border bg-gradient-to-r from-accent-2 to-accent font-display font-bold uppercase text-white`}
    >
      {handle.charAt(0)}
    </div>
  );
}
```

- [ ] **Step 2: Type-check**

Run: `cd platform && npx tsc --noEmit`
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add platform/app/components/Avatar.tsx
git commit -m "platform: add shared Avatar component with initials fallback"
```

---

## Task 8: Platform — render `Avatar` on roster cards

**Files:**
- Modify: `platform/app/(app)/page.tsx:1-4,48-64`
- Modify: `platform/e2e/dashboard.spec.ts`

**Interfaces:**
- Consumes: `Avatar` (Task 7), `influencer.avatar_url` (Task 6).

- [ ] **Step 1: Write the failing Playwright assertion**

Add to `platform/e2e/dashboard.spec.ts`, after the existing `"roster page loads..."` test:

```typescript
test("roster cards render an avatar for each influencer", async ({ page }) => {
  await login(page);

  const firstCard = page.locator('a[href^="/influencer/"]').first();
  await expect(firstCard.locator("img, div.rounded-full").first()).toBeVisible();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd platform && npx playwright test dashboard.spec.ts -g "roster cards render an avatar"`
Expected: FAIL — no `img` or `div.rounded-full` inside the card yet

(If the dev server isn't already running for Playwright, start it first: `cd platform && npm run dev` in a separate terminal, matching however the existing suite is normally run.)

- [ ] **Step 3: Import `Avatar` and render it on each card**

In `platform/app/(app)/page.tsx`, add the import after the existing `HighlightContent`
import (line 4):

```typescript
import { Avatar } from "@/app/components/Avatar";
```

Then change the card header block (currently lines 55-65):

```tsx
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Avatar handle={influencer.handle} avatarUrl={influencer.avatar_url} size="sm" />
                    <p className="text-lg font-semibold">@{influencer.handle}</p>
                  </div>
                  {hasWarning ? (
                    <span className="rounded-full bg-negative-soft px-2 py-0.5 text-xs font-medium text-negative">
                      attention
                    </span>
                  ) : hasGood ? (
                    <span className="rounded-full bg-positive-soft px-2 py-0.5 text-xs font-medium text-positive">
                      breakout
                    </span>
                  ) : null}
                </div>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd platform && npx playwright test dashboard.spec.ts -g "roster cards render an avatar"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add "platform/app/(app)/page.tsx" platform/e2e/dashboard.spec.ts
git commit -m "platform: render influencer avatar on roster cards"
```

---

## Task 9: Platform — render `Avatar` on the influencer detail page

**Files:**
- Modify: `platform/app/(app)/influencer/[handle]/page.tsx:1-42`
- Modify: `platform/e2e/dashboard.spec.ts`

**Interfaces:**
- Consumes: `Avatar` (Task 7), `influencer.avatar_url` (Task 6).

- [ ] **Step 1: Write the failing Playwright assertion**

Add to `platform/e2e/dashboard.spec.ts`, after the `"influencer page shows overhauled dashboard sections"` test:

```typescript
test("influencer detail page renders an avatar next to the handle", async ({ page }) => {
  await login(page);

  const firstCard = page.locator('a[href^="/influencer/"]').first();
  await firstCard.click();

  await expect(page.locator("h1 img, h1 + * img, main div.rounded-full").first()).toBeVisible();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd platform && npx playwright test dashboard.spec.ts -g "influencer detail page renders an avatar"`
Expected: FAIL

- [ ] **Step 3: Import `Avatar` and render it beside the heading**

In `platform/app/(app)/influencer/[handle]/page.tsx`, add the import after the existing
`FollowerChart` import (line 10):

```typescript
import { Avatar } from "@/app/components/Avatar";
```

Then change the heading block (currently lines 37-42):

```tsx
      <div className="mb-8 flex items-center gap-4">
        <Avatar handle={influencer.handle} avatarUrl={influencer.avatar_url} size="lg" />
        <h1 className="font-display text-2xl font-bold tracking-tight">
          @{influencer.handle}
          {influencer.display_name ? (
            <span className="ml-2 text-lg font-normal text-muted">{influencer.display_name}</span>
          ) : null}
        </h1>
      </div>
```

(Remove the old standalone `mb-8` from the `h1` since the wrapping `div` now owns that
spacing — the replacement above already drops it from the `h1` className.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd platform && npx playwright test dashboard.spec.ts -g "influencer detail page renders an avatar"`
Expected: PASS

- [ ] **Step 5: Run the full Playwright suite**

Run: `cd platform && npx playwright test`
Expected: all tests PASS (no regressions from the heading markup change)

- [ ] **Step 6: Type-check and build**

Run: `cd platform && npx tsc --noEmit && npm run build`
Expected: no errors, build succeeds

- [ ] **Step 7: Commit**

```bash
git add "platform/app/(app)/influencer/[handle]/page.tsx" platform/e2e/dashboard.spec.ts
git commit -m "platform: render influencer avatar on the detail page header"
```

---

## Task 10: Manual verification against real data

**Files:** none (verification only)

- [ ] **Step 1: Confirm the user has applied the schema change and created the bucket**

Ask the user to confirm they've run the `scraper/schema.sql` changes from Task 1
against their Supabase project and created the public `avatars` Storage bucket. This
plan's automated tests cannot do this — it's a manual, one-time action against their
project.

- [ ] **Step 2: Run one real scrape for a single handle**

Run: `cd scraper && python -m youfirst_scraper.backfill` (or trigger `run_daily`'s
`run_instagram_scrape` for a single test handle per the existing scraper README) and
confirm in the logs that no `"Failed to update avatar"` warning appears for at least
one handle.

- [ ] **Step 3: Confirm the photo appears in the running dev server**

Run: `cd platform && npm run dev`, log in, and visually confirm a real Instagram photo
(not the initials fallback) renders on that influencer's roster card and on their
detail page.

- [ ] **Step 4: State results**

Report: pytest result counts (scraper), Playwright result counts (platform), tsc/build
result, and what was visually confirmed in the dev server — per the repo's Post-Task
Checklist in `CLAUDE.md`.

---

## Self-Review Notes

- **Spec coverage:** schema column ✅ (Task 1), scraper capture + download + upload ✅
  (Tasks 2-5), platform type/query ✅ (Task 6), shared component with fallback ✅ (Task
  7), roster card placement ✅ (Task 8), detail page placement ✅ (Task 9), manual
  rollout/testing note ✅ (Task 1 note + Task 10).
- **Placeholder scan:** no TBD/TODO; every step has literal code or an exact command.
- **Type consistency:** `avatar_source_url` (scraper dict key) used consistently across
  Tasks 2, 4, 5; `avatar_url` (DB column / TS field) used consistently across Tasks 1,
  3, 6, 7, 8, 9; `Avatar({ handle, avatarUrl, size })` prop names match between Task 7's
  definition and Tasks 8-9's call sites.
