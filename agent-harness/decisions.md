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
