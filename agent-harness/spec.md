# Spec

## Goal of This Change

Make recommendations content-grounded and scannable, and surface daily-scraping value
as roster-level attention alerts:

1. Analyze the video/audio of each influencer's top-performing recent posts with
   Gemini so the system knows *what a reel was about*, not just its caption.
2. Rewrite the Gemini recommendation prompt to cite top performers (with content
   summaries and how they compare to the median) instead of the 5 most recent
   captions, drop the generic trend-report context, and require short Spanish-only
   bullet output instead of bilingual prose.
3. Render those bullets as a scannable list in the influencer page, with a link back
   to the referenced post.
4. Add negative/attention signals (engagement drop, posting gap) alongside the
   existing positive highlights, and surface them on the roster page so the agency
   can see who needs attention without opening every influencer.

## Why This Matters

The daily scraper already collects rich day-over-day data (new posts, follower deltas,
per-post engagement growth), but today's recommendations only look at the most recent
captions and generic Spanish trend articles — they can't say "your reel about X got 4×
your median views, do a follow-up," because the system never learns what any reel is
about. Output is also bilingual markdown prose rendered as a dense wall of text, which
agency staff and talent (with limited patience) don't read. And daily-collected
performance data has no roster-level surface — nothing today tells the agency "who
needs attention."

## Intended User

Agency staff and talent reading the platform dashboard.

## Success Criteria

1. **Content analysis**: `content_analysis.py` downloads video (or thumbnail for
   non-video posts) for each new post at/above median engagement (capped ~4/run/
   influencer), sends it to Gemini for a Spanish `{summary, topic, format, hook}`,
   stores it once per shortcode in a new `post_content` table. Failures (download,
   Gemini) log and skip without aborting the run.
2. **Grounded prompt**: `recommendations.build_prompt` includes a "top performers"
   section (shortcode, format, stats, multiple-of-median, content summary) and a
   weakest-post contrast; trend-report context removed from this prompt.
3. **Structured Spanish bullets**: Gemini called with JSON response mode, returns
   `{"bullets": [{"text", "reason", "shortcode"}]}`, 3-5 bullets, Spanish only, each
   tied to a specific stat or post. Malformed JSON stored as raw text (old behavior).
4. **Frontend bullets**: `RecommendationContent.tsx` parses JSON bullets into a short
   list with Instagram links; falls back to existing markdown rendering for legacy
   prose rows.
5. **Attention alerts**: `metrics.compute_highlights` gains `engagement_drop` (≥30%
   below baseline) and `posting_gap` (no post in >2x cadence, min 7 days) signals with
   a `severity` field; roster page shows a "needs attention" indicator per influencer
   using the last 7 days of highlights.
6. **Tests**: pytest covers content-analysis selection/caps/failure-skip, prompt
   content (top performers, no trends section), JSON parse + fallback, new alert
   thresholds; Playwright covers bullet rendering + fallback + roster badges.

## Non-Goals / Out of Scope

- No email/push digest of alerts.
- No comparable-creator scraping.
- No removal of the trend-scraper module — only unhooked from the recommendation
  prompt.
- No language toggle — Spanish only.
- No swap to a third-party scraping API (e.g. Apify) — fetch/analyze are kept as
  separate functions so that can happen later without touching analysis logic, but
  it is not built now.

## Open Questions

None — user confirmed scope (content analysis + bullets + roster alerts, drop trend
scraping from recs), Spanish-only output, and full video+audio analysis (not just
thumbnails) on 2026-07-07.
