# Spec

## Goal of This Change

Make creative recommendations on-brand per influencer and grounded in Spanish-market
trend sources: add a `persona` column to `influencers`, switch `TREND_SOURCES` to
Spanish-market reports, and rework the Gemini prompt to tailor recommendations to each
influencer's persona and a Spain/Spanish-speaking audience.

## Why This Matters

Recommendations currently read the same trend context for every influencer and lean on
US-centric sources. A polished TV presenter should not be told to do meme dances; a
comedian should get trends adapted into sketch formats. The agency's audience is Spain,
not the USA — the trend inputs and the prompt must reflect both.

## Intended User

Agency staff and talent reading recommendations on the platform. The change itself is in
the scraper pipeline (`scraper/`).

## Success Criteria

1. `config.TREND_SOURCES` contains exactly these 4 Spanish-market URLs (newengen.com
   removed):
   - `https://www.modash.io/content-library/country/spanish-examples` (kept)
   - `https://www.garajedoce.com/blog/estudio-iab-spain-redes-sociales/`
   - `https://lagahe.com/blog/novedades-instagram-2026-hashtags/`
   - `https://venizecomunicacion.com/tendencias-en-redes-sociales-2026-instagram-ante-el-gran-reto-de-la-saturacion/`
   All 3 new URLs verified scrapable (HTTP 200, clean text via existing
   `scrape_trend_source`) on 2026-07-06.
2. `influencers` table gains a nullable `persona text` column (`schema.sql` updated plus
   a one-off `alter table` applied to live Supabase), seeded for the 5 roster handles:
   - `cristipedroche` — elite/polished TV presenter; premium, aspirational content; no
     meme dances or low-fi trends
   - `antonlofer` — comedian; adapt trends into comedic sketches, not serious/aesthetic
     formats
   - `dante_caro` — comedy creator (ex-Vine, Madrid); parodies and humor videos
   - `mariavalero` — comedian/actress (Valencia); relatable everyday-life and
     relationship sketches
   - `ferminaldeguer_54` — MotoGP rider; athlete content: racing, training,
     behind-the-scenes paddock life
3. `recommendations.build_prompt` includes the influencer's persona and instructs the
   model to (a) only suggest formats/trends that fit the persona, adapting trends rather
   than forcing off-brand formats, and (b) target a Spain/Spanish-speaking audience, not
   a US one. Bilingual Spanish/English output is kept. When `persona` is null the prompt
   omits the persona section and still works.
4. `run_daily.py` / `db.py` pass persona from the influencer row into
   `generate_recommendation` — trend snapshot fetch already scales via
   `len(config.TREND_SOURCES)` (no change needed there beyond the config edit).
5. pytest: prompt-builder tests assert persona text and Spain-audience instruction appear
   in the prompt (and that a null persona degrades gracefully); a config test locks
   `len(TREND_SOURCES) == 4`. All existing tests still pass.
6. Live check: one manual `run_daily` produces 4 `trend_snapshots` rows (one per source)
   and a recommendation for at least one influencer that reflects their persona.

## Non-Goals / Out of Scope

- No JS-rendered sources (Google Trends explore etc.) — the scraper is requests +
  BeautifulSoup only.
- No new source types (APIs, RSS) — URL scraping only.
- No platform UI changes for persona (display/editing) — separate spec if wanted.
- No profile images feature — queued as its own spec after this one.
- No per-influencer trend-source targeting — all influencers share the same 4 sources.

## Open Questions

None — sources, personas, and prompt behavior confirmed with the user on 2026-07-06.
