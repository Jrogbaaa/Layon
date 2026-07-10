# Spec

## Goal of This Change

Ground daily creative recommendations in specific, current, real Spain events instead of
generic placeholders (e.g. "adapt a currently trending Spanish TV show" with no named
show). Two changes:

1. Replace the four evergreen "social media trends 2026" marketing-blog sources in
   `config.TREND_SOURCES` with live, real-time feeds that name actual shows, people, and
   events happening in Spain right now (Google Trends Spain RSS, 20minutos Gente RSS,
   El País Cultura RSS — all verified live and current as of 2026-07-10).
2. Pipe the distilled `trend_headlines` into each influencer's recommendation prompt
   (`recommendations.build_prompt`), with an explicit instruction that any trend
   reference must NAME the specific show/person/event from the supplied list — never a
   vague placeholder. This closes the gap where `run_daily.py` scrapes trends and
   generates headlines but never passes them into the recommendation generator.

Each influencer's existing persona and metrics context stay in the same prompt, so
Gemini picks which of today's named trends (if any) fit that influencer's brand —
customization by influencer is inherited from the existing per-influencer prompt
structure, not new logic.

## Why This Matters

The agency's recommendations are meant to give talent concrete, actionable ideas.
Generic instructions to "adapt a trending show" with no name are useless — a talent
manager can't act on them. Grounding in real, current Spain-specific events (feed items
scraped the same day) makes each daily bullet something a team can execute immediately,
while staying on-brand per influencer.

## Intended User

Agency staff and talent reading daily recommendations in the platform dashboard.

## Non-Goals

- No new Supabase tables or schema changes (reuse `trend_snapshots` / `trend_headlines`).
- No new third-party dependencies (RSS parsed with stdlib `xml.etree.ElementTree`).
- No per-influencer trend-source targeting — one shared trend list per day, filtered by
  Gemini per persona in the prompt, as with existing persona/format guidance.
- No change to auth, platform UI, or scrape frequency (still once daily).
- No influencer-brand matching system (out of scope per CONSTITUTION.md).

## Success Criteria

1. `trend_scraper.scrape_trend_source` parses RSS (Content-Type or `<?xml`/`<rss`
   sniffed) via a new branch, alongside the existing HTML path — both return
   `{"title", "content_text"}`.
2. `config.TREND_SOURCES` holds the three verified live feeds.
3. `trend_headlines.build_prompt` instructs Gemini to name specific shows/people/events,
   not generic themes.
4. `recommendations.build_prompt` / `generate_recommendation` accept `trend_items` and
   render a "What's trending in Spain today" section instructing bullets to name the
   specific trend item, never a vague placeholder.
5. `run_daily.run_recommendations` fetches the latest stored `trend_headlines` row once
   per run and passes its English texts into every influencer's recommendation call.
6. pytest green in `scraper/`, including updated/added tests for the RSS branch, the new
   prompt sections, and the `run_daily` wiring.
7. A live `run_daily` (or targeted manual script) run shows trend_snapshots/trend_headlines
   containing named current items, and at least one recommendation bullet naming a
   specific trend.

## Open Questions

None — direction confirmed with the user 2026-07-10; RSS feed URLs verified live via curl
before being locked into the plan.
