# Decisions

Record durable decisions here. Append — never overwrite.

## Format

### YYYY-MM-DD — Decision Title

**Decision:** What was decided.

**Reason:** Why.

**Tradeoffs:** What this means / what was rejected.

---

### 2026-07-06 — Database: Supabase over Neon

**Decision:** Use Supabase (hosted Postgres) as the database, purely as a data store
(no Supabase Auth).

**Reason:** Free hosted Postgres with the least wiring for a small internal tool. Neon
was considered and is equally viable technically, but would require adding a separate
auth library; since the platform uses a single shared password instead of per-user
accounts, Supabase's extra auth features aren't needed either way — Supabase was chosen
mainly to avoid a second vendor decision.

**Tradeoffs:** Rejected Neon + Auth.js. Accepted: tied to Supabase's free-tier limits.

### 2026-07-06 — Scheduling via launchd, not a third-party automation service

**Decision:** Run the daily scraper via a macOS LaunchAgent (`launchd`,
`StartCalendarInterval`), not a cloud scheduler.

**Reason:** The scraper runs on Jack's desktop (not a server). `launchd` is native,
free, and automatically catches up a missed run when the Mac wakes from sleep — matches
the "once a day" requirement without new infrastructure.

**Tradeoffs:** The scrape only happens when the laptop is on/wakes that day. A
cloud-scheduled scraper is a possible v2 if this becomes a problem.

### 2026-07-06 — Recommendations use Gemini, not OpenAI

**Decision:** Use the Google Gemini API for creative recommendations.

**Reason:** User has a Google API key and prefers Gemini over OpenAI.

**Tradeoffs:** None significant — recommendation quality is comparable; swappable later
if needed since the call is isolated to one module.

### 2026-07-06 — Platform auth: single shared password, not per-user accounts

**Decision:** Gate the platform with one shared password (`LAYCC`) via Next.js
middleware, not individual staff/talent logins.

**Reason:** Simpler for v1; the user explicitly said email logins aren't needed.

**Tradeoffs:** No per-user audit trail or personalized access; anyone with the password
sees everything. Acceptable since only public Instagram metrics are shown.

### 2026-07-06 — Influencer-brand matching excluded from this project

**Decision:** Brand matching is not built here.

**Reason:** Already exists in Project-X (github.com/Jrogbaaa/Project-X). Duplicating it
here would be redundant scope.

**Tradeoffs:** If the team wants matching alongside these dashboards later, it should be
integrated as a v2, reusing Project-X rather than rebuilt from scratch.

### 2026-07-06 — File lifecycle: overwrite working files, rely on git for history

**Decision:** `spec.md`, `findings.md`, `progress.json`, and `session.md` are
overwritten by each new change. `trace.jsonl` and `decisions.md` are append-only. No
per-feature archive directories.

**Reason:** Avoids file accumulation. Full history is always recoverable via `git log` /
`git show`.

**Tradeoffs:** History requires git, not in-tree browsing. (Adopted from the same
pattern used in the user's `/Users/JackEllis/ui/agent-harness` setup.)

### 2026-07-06 — Instagram scraping paused: Instaloader is currently broken against Instagram

**Decision:** Added authenticated-session support to the scraper (`IG_USERNAME` +
`instagram_scraper.build_loader()`, session created once via
`instaloader --login=<user>`), but a live run still fails for every profile —
including verified-real accounts like `cristiano` — with Instagram returning `200 OK`
but an empty GraphQL body, which Instaloader misreports as
`ProfileNotExistsException`. Confirmed via web research this is a known, currently
**unresolved** Instaloader bug
([instaloader/instaloader#2682](https://github.com/instaloader/instaloader/issues/2682)),
not a bug in this codebase or a wrong handle. An unmerged community fix exists
(PR #2652) but has no official release. User chose to pause Instagram scraping here
rather than adopt the unstable PR branch or switch to a paid scraping API immediately.

**Reason:** This is an external, unresolved library/Instagram-API incompatibility
affecting all Instaloader users right now, not something fixable by more code in this
repo. Trend scraping and the Supabase/Gemini pipeline around it are unaffected and
confirmed working against the real Supabase project.

**Tradeoffs:** The Instagram side of the pipeline cannot produce real data until either
(a) Instaloader ships an official fix, (b) the user accepts the unmerged PR #2652
branch's stability risk, or (c) the project switches to a paid scraping API (e.g.
Apify). `instagram_scraper.py` and `run_daily.py`'s error-handling/session-loading code
is correct and tested (27/27 pytest passing with mocks) and needs no rework once the
underlying blocker is resolved — only the scraping call itself is affected.

### 2026-07-06 — Instagram scraping unblocked: real browser session replaces `instaloader --login`

**Decision:** Instead of the `instaloader --login` session (which Instagram serves
empty GraphQL bodies to, per #2682), extracted the live cookies (`sessionid`,
`csrftoken`, `ds_user_id`, `mid`, `ig_did`) from the user's already-authenticated
`beautifullfootball` session in the Comet browser, using `browser_cookie3`'s
`ChromiumBased` loader pointed at Comet's `Cookies` SQLite file and macOS Keychain
entry (`Comet Safe Storage`). Built a fresh Instaloader session file from those cookies
and replaced `~/.config/instaloader/session-beautifullfootball` (old one backed up
alongside it). This is the same workaround multiple users on the upstream issue thread
reported as fixing this exact failure.

Separately found and fixed a second, narrower bug this surfaced: `instagram_scraper.py`
called Instaloader's `post.comments` property, which expects an
`edge_media_to_parent_comment` field that isn't present on this (migrated) timeline
endpoint's response shape — forcing a fallback per-post metadata fetch that itself
still fails upstream. The timeline edge already carries the count directly under a
plain `comments` key, so `instagram_scraper.py` now reads `post._node["comments"]`
directly (`_comment_count()`), skipping the broken fallback fetch entirely.

**Reason:** User asked to try running the scraper with real login credentials
ourselves before switching to Apify. The browser-cookie approach requires no code
changes to the pipeline itself (session file is a drop-in swap) and confirmed working
against real, verified accounts (`cristiano`: 671M followers, real post data) and 5 of
6 roster handles end-to-end into Supabase.

**Verification:** 27/27 pytest still passing. Full `run_daily` run against real
Supabase: 5/6 roster handles scraped successfully (`dante_caro`, `mariavalero`,
`antonlofer`: 12 posts each with real likes/comments/captions; `cristinapedroche`,
`mariaacosta`: profile data, 0 posts — accounts appear to have no public posts).
`ferminadueleguer` still fails with `ProfileNotExistsException` — verified this handle
genuinely does not exist on Instagram (a roster data-quality issue, unrelated to the
scraping blocker).

**Tradeoffs:** Browser-cookie sessions are known (per the upstream issue thread) to
degrade or get invalidated over time — this is not a permanent fix, just a working
path that avoids Apify for now. If the daily run starts failing again, re-extracting
cookies from a fresh browser login is the first thing to try; if that stops working
too, Apify (or another paid API) is the fallback already discussed above. The
`beautifullfootball` account is now the one making all scrape requests — same
authenticated-account risk profile as before, just with a session Instagram doesn't
immediately reject.

### 2026-07-06 — Deep baseline via one-time backfill; deterministic highlights; hard-delete stale roster row

**Decision:** (feature_005) Build the per-influencer baseline with a **one-time 36-post
backfill** (`python -m youfirst_scraper.backfill`) rather than raising the daily
`POSTS_PER_INFLUENCER` cap; compute "highlights" as **deterministic Python functions**
in `metrics.py` (persisted to a new `highlights` table, rendered on the dashboard, and
fed into the Gemini prompt) rather than asking the LLM to invent insights; and
**hard-delete** the stale `cristinapedroche` impostor row (snapshots included, via FK
cascade) rather than flipping it `active=false`.

**Reason:** The daily run's job is catching new posts and refreshing recent metrics —
tripling its cap forever would triple daily Instagram load for a baseline that only
needs building once. Deterministic highlights keep the numbers trustworthy (real
arithmetic on real rows) while Gemini gets them as grounded context. The impostor row
is data-quality noise, not history worth keeping: 41 followers on a typo handle, never
the real account.

**Tradeoffs:** Backfill is a manual one-off (36 x 5 profiles, ~several minutes at 20s
delay) with throttling risk on the browser-cookie session — accepted, reported honestly
if it happens. Deleted impostor history is unrecoverable — accepted, it was worthless.
Per-post growth-over-time highlights need >= ~6 days of capture history, so day one
will only show outperformance-vs-median and views-based highlights.
