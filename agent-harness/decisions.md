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

### 2026-07-13 — Scraper reliability: same-day retry via extra launchd fires, not automated backfill

**Decision:** For feature_010, failed daily runs are recovered by (a) only writing
`.last_run` when every roster handle succeeded, (b) adding 13:00 and 17:00
`StartCalendarInterval` entries to the plist, and (c) making retry runs idempotent
per-handle (skip any handle with a profile snapshot captured today, mirroring
`trend_source_scraped_today`). Alerting is a macOS notification via `osascript` plus an
ERROR log line — no email/webhook infrastructure. Anomaly gate threshold: reject profile
snapshots with followers 0/None or >50% day-over-day swing. Transient errors get 3
attempts with linear backoff (30s, 60s); instaloader login/challenge exceptions abort the
roster loop with a distinct session-expired alert. Retry runs re-run the downstream
Gemini steps (headlines/recommendations/briefing), so a completed roster refreshes any
outputs generated earlier from partial data.

**Reason:** launchd fires once at 9:00, so "don't mark done" alone retries nothing until
the next day; extra fire times + per-handle skip give same-day recovery while honoring
the once-per-day-per-handle contract. osascript needs zero new dependencies and the
pipeline already runs on Jack's Mac. The 90%-drop corruption class is caught by the
50% gate without being so tight that real follower swings trip it.

**Tradeoffs:** Rejected automated `backfill.py` wiring (historical catch-up stays
manual), webhook/email alerts (new infra), and Graph API migration (Phase 2, declined).
On a failure day, Gemini steps may run up to 3x. If the Mac is asleep at all three fire
times, the day is still lost — accepted, matches existing launchd decision.

### 2026-07-13 — Feature 014 planning: keep post selection local to EngagementChart

**Decision:** Plan one selected-post interaction model shared by the engagement chart
and publication rail inside `EngagementChart.tsx`; do not lift selection into the
influencer page or change the post data contract.

**Reason:** The problem is local to the two existing visual surfaces. Keeping the state
local makes the change surgical, preserves the existing `chartPosts`/`posted_at` data
flow, and avoids unrelated dashboard state or schema work.

**Tradeoffs:** The selection is intentionally ephemeral UI state and will not be
deep-linkable or shared with other dashboard sections. Approved interaction details:
dates use `Europe/Madrid`; hover commits the same persistent selection as click/focus;
and `Escape` clears it while pointer exit and blank chart space do not.

### 2026-07-14 — Feature 017 planning: database column for ad status, subtle styling badges

**Decision:** Store ad status using a new `is_ad` boolean column in `post_snapshots` (and `top_posts` view) rather than parsing the caption client-side. Render as a scarce low-opacity amber badge next to format names and '· Ad' text on tooltips.

**Reason:** Querying and storing `is_ad` directly in the database is more robust than parsing captions client-side for hashtags. Instaloader's `is_sponsored` property evaluates this cleanly. Displaying the ad status in tooltips, details card, tables, and Greatest Hits listings satisfies the requirements without introducing clutter.

**Tradeoffs:** Requires executing a database schema migration. Historical posts already in the database will have `is_ad` set to false by default unless re-scraped or manually updated.

### 2026-07-15 — Ad detection rebuilt as strict product-presence rubric, relabeled Paid Media / Organic

**Decision:** Replace Feature 017's `is_sponsored`-only detection (which almost never fires) with a Gemini multimodal classifier (`scraper/youfirst_scraper/ad_detection.py`) using a strict rubric: a post is "paid" only if a product is deliberately featured/held up or mentioned in the caption (including disclosure tags). Incidental brand visibility — sponsor logos on an athlete's gear, background signage, venue mentions — is always "organic," never paid, regardless of how much brand imagery is present. Genuinely ambiguous posts return "unsure" rather than a guessed boolean, and are surfaced to the user for a manual verdict instead of silently defaulting either way. UI labels renamed from "Ad" to "Paid Media" / "Organic" throughout (`is_ad` column/type name kept as-is; only Gemini's called it "unsure" internally, `is_ad` stores false for both organic and unsure).

**Reason:** The original Feature 017 prompt flagged any visible brand/logo as an ad — e.g. a MotoGP racer's sponsor-covered helmet and racing suit scored 98% ads for `ferminaldeguer_54`, which is unusable. The user's own bar for "organic" is "no product mentions," decidable by a simple look at the image/caption — the rubric now matches that directly instead of a fuzzier "promotional intent" judgment call the model previously had to make on its own.

**Tradeoffs:** Requires a full retroactive re-classification (`backfill_ads.py`) of every stored post, not just previously-unflagged ones, since old `is_ad` values are untrustworthy. `post_snapshots` never persisted `thumbnail_url`/`video_url` (Feature 017 gap, only surfaced now) so the backfill re-derives media by re-scraping each influencer's profile once and matching by shortcode, stopping early once every needed shortcode for that influencer is found — this trades one extra live Instagram request per influencer (not per post) for not needing a schema/scraper change to persist media URLs going forward. "Unsure" posts require a human pass rather than being fully automated end-to-end.

### 2026-07-15 — Instagram auth: cookie import (`--load-cookies`), not `instaloader --login`

**Decision:** Standardize Instagram session creation/renewal on `instaloader --load-cookies Chrome` (importing an already-logged-in browser session), and stop using `instaloader --login=<user>` entirely.

**Reason:** During the Feature 017 refinement backfill, an early mistake (looping `instaloader.Post.from_shortcode()` over ~1000 individual posts) got the `beautifullfootball` account checkpoint-locked. Recovery via `--login` failed repeatedly — browser verification, an overnight cooldown, a fresh session file, and confirming "this was me" on login-activity all failed to clear it, and each `--login` retry appeared to re-arm the block, since Instagram checkpoint-blocks that specific login endpoint independent of whether the account itself is fine in a browser. `--load-cookies` (via the `browser_cookie3` package) imports the browser's already-trusted session and never touches the flagged endpoint, and worked on the first attempt.

**Tradeoffs:** Requires staying logged into the scraping account in a real (non-incognito) Chrome window on the machine running the scraper/backfill, and one extra pip dependency (`browser_cookie3`). Documented in `scraper/README.md`, `instagram_scraper.py` docstrings/warnings, and `run_daily.py`'s session-expiry notification so the recovery path is never confused with the blocked `--login` flow again.

