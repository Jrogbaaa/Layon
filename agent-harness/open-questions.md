# Open Questions

Questions that require human judgment. Append active questions; move to Resolved when answered.

## Active Questions

None.

## Resolved Questions

- **Feature 014 date display timezone and format?** → `Europe/Madrid`, with compact
  month/day axis labels and full month/day/year selected detail. (2026-07-13)
- **How should Feature 014 persistent selection be cleared?** → Selection persists until
  another post is selected; `Escape` is the explicit clear action. Pointer exit and
  blank chart space do not clear it. (2026-07-13)
- **Should Feature 014 hover commit selection?** → Yes. Hover, click, and keyboard focus
  select the same post, and the last hovered post remains selected. (2026-07-13)

- **instagram-php-scraper or a maintained alternative?** → Instaloader (actively
  maintained). (2026-07-06)
- **Database: Supabase or Neon?** → Supabase. (2026-07-06)
- **Recommendations LLM: OpenAI or Gemini?** → Gemini (Google API key). (2026-07-06)
- **Scrape frequency: on every laptop open, or scheduled?** → Once daily via `launchd`,
  which catches up on wake. (2026-07-06)
- **Where do trend reports come from?** → newengen.com/insights/instagram-trends/ and
  modash.io/content-library/country/spanish-examples, scraped daily. (2026-07-06)
- **Is influencer-brand matching in scope?** → No, removed — already covered by
  Project-X. (2026-07-06)
- **Platform auth model?** → Single shared password (`LAYCC`), no per-user accounts.
  (2026-07-06)
