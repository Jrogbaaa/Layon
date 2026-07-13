# Spec

## Goal of This Change

Ground-up visual redesign of `platform/` as a showcase of advanced web design craft
("Medianoche" direction), replacing the light "Fresh Current"/"Trading Floor" theme
with a cinematic, nocturnal, editorial identity:

1. New token system in `globals.css` (Tailwind v4 `@theme`): deep garnet-black canvas,
   warm ivory ink, gilded amber signal accent, mint/vermillion semantics. OKLCH-derived.
2. New type system: Fraunces (expressive variable serif, display), Archivo (UI/body),
   Spline Sans Mono (data readouts) — replacing Plus Jakarta Sans + Inter.
3. Advanced visual techniques as first-class design material:
   - Custom WebGL (raw, dependency-light) shader background on login — flowing
     silk/aurora in the brand palette, with static fallback + reduced-motion respect.
   - AI-generated key art (GPT Image) and/or Higgsfield-animated loop as login panel art.
   - Draw-on chart animations, odometer count-ups, staggered reveals that enhance
     already-visible content, View Transitions where cheap.
4. Redesigned pages: login (cinematic gate), roster (editorial call-sheet + triage rail),
   influencer detail (magazine profile), trends (headline wire). Same data, same routes,
   same auth.

## Why This Matters

The user explicitly requested a fundamentally different redesign demonstrating
state-of-the-art web design capability (3D, animation, palette, typography), to be
shown publicly, with full creative autonomy delegated. Showcase quality is the
acceptance bar; the dashboard must still function as a daily triage tool.

## Intended User

Primary: the public audience the user will show this to (capability demonstration).
Secondary: agency staff still using it daily for triage.

## Non-Goals

- No auth model change (shared password stays).
- No new data fields, endpoints, or scraper changes.
- No influencer-brand matching.
- No removal of existing functionality (language toggle, briefing, highlights, tables).

## Success Criteria

1. All four surfaces (login, roster, detail, trends) fully restyled as one coherent system.
2. Playwright e2e suite passes (updated where selectors/copy changed).
3. prefers-reduced-motion honored on every animation; content never gated on JS reveal.
4. Body text contrast ≥ 4.5:1 verified on the dark canvas.
5. `npm run build` and `npm run lint` pass.
6. At least three fine-toothed iteration passes with browser screenshots before done.

## Open Questions

None — user delegated all creative decisions ("total creative freedom … do not ask
me for anything until it's done", 2026-07-09).
