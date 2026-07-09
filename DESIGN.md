---
name: Look After You — Influencer Insights Platform
description: A nocturnal, editorial triage tool — the night watch for a roster of stars
colors:
  accent: "#e3b04b"
  accent-bright: "#f0c96a"
  accent-deep: "#94691f"
  canvas: "#120b0d"
  canvas-deep: "#0a0506"
  surface: "#1b1214"
  surface-2: "#241819"
  border: "#362527"
  border-faint: "#271b1d"
  ink: "#f4ede2"
  muted: "#b5a69b"
  faint: "#97897f"
  garnet: "#7e2230"
  garnet-deep: "#4a141d"
  positive: "#63d6a4"
  positive-soft: "rgba(99, 214, 164, 0.12)"
  negative: "#ff7d6b"
  negative-soft: "rgba(255, 125, 107, 0.12)"
typography:
  display:
    fontFamily: "Fraunces, Georgia, serif"
    fontWeight: 400
    letterSpacing: "-0.015em"
    note: "Variable axes: opsz 144 + WONK 1 for hero sizes (.display-hero)"
  body:
    fontFamily: "Archivo, -apple-system, Segoe UI, sans-serif"
    fontWeight: 400
    lineHeight: 1.5
  mono:
    fontFamily: "Spline Sans Mono, ui-monospace, monospace"
    note: "All data readouts, labels-as-slugs, timestamps. Tabular numerals via .tnum"
rounded:
  panel: "0.625rem"
  control: "0.375rem"
spacing:
  sm: "0.5rem"
  md: "1rem"
  lg: "1.5rem"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.canvas-deep}"
    rounded: "{rounded.control}"
    padding: "0.625rem 1.25rem"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
---

# Design System: Medianoche

## 1. Overview

**Creative North Star: "Medianoche" — the night watch for a roster of stars.**

A cinematic, nocturnal, editorial instrument. The agency watches its talent overnight —
the scraper runs while Madrid sleeps — and the interface embraces that: a deep
garnet-black canvas, warm ivory type, and one gilded signal color. It reads like a
couture house's internal terminal: a fashion-magazine masthead married to a trading
floor's tape.

The system still serves triage first — "who needs attention" is answerable at a
glance — but the presentation is a deliberate showcase of craft: a live WebGL silk
shader on the gate, AI-generated key art, view-transition morphs between roster and
profile, draw-on sparklines, and odometer count-ups. Motion always enhances
already-visible content and always respects `prefers-reduced-motion`.

**Key Characteristics:**
- Near-black garnet canvas (`#120b0d`); depth via tone and hairlines, not shadows.
- One accent: gilded amber. It means "signal" — never decoration in bulk.
- Serif display (Fraunces, high optical size) + grotesque body (Archivo) + mono data
  (Spline Sans Mono). Three voices, three jobs.
- Semantic mint/vermillion reserved strictly for trend direction and alarm.
- A fixed film-grain overlay (`.grain`) gives every page its nocturnal texture.

## 2. Colors

### Primary
- **Gilded Amber** (#e3b04b): the signal — links, active nav, section slugs, primary
  button fill (with near-black text; white text on amber fails AA).
- **Amber Bright** (#f0c96a): hover state of the signal.
- **Amber Deep** (#94691f): gradient partner in the avatar ring; never text.

### Canvas & Surfaces
- **Canvas** (#120b0d): the page. **Canvas Deep** (#0a0506): login backdrop, button text.
- **Surface** (#1b1214) / **Surface 2** (#241819): the panel and its hover tone.
- **Border** (#362527) / **Border Faint** (#271b1d): hairlines. Faint is the default.

### Ink
- **Ink** (#f4ede2): primary text — warm ivory, ≥15:1 on canvas.
- **Muted** (#b5a69b): secondary prose (~8:1). **Faint** (#97897f): small labels,
  timestamps, rank numbers (~5:1 — never body copy).

### Accent Support
- **Garnet** (#7e2230) / **Garnet Deep** (#4a141d): the shader palette, avatar-ring
  gradient, fallback avatar fill. Large fills only, never text.

### Semantic
- **Positive** (#63d6a4) / **Negative** (#ff7d6b): trend direction, watchlist markers,
  error states. Soft variants are 12% alpha tints for rare badge fills.

### Named Rules
**The Signal Rule.** Amber is scarce: slugs, links, the active nav underline, one
button. If amber exceeds a tenth of a screen, something is decorated, not designed.
**The Noise Rule.** Deltas under max(5, 0.01% of audience) render neutral — alarm
colors are reserved for meaningful movement.

## 3. Typography

**Display:** Fraunces (variable; `opsz` 144, `WONK` 1 at hero sizes via `.display-hero`)
**Body/UI:** Archivo
**Data:** Spline Sans Mono (`.font-mono`, tabular numerals via `.tnum`)

### Hierarchy
- **Masthead** (`.display-hero`, text-6xl–7xl): page titles ("The Roster", "The Wire"),
  profile names, trend headlines. Line-height 0.98, balanced wrap.
- **Pull-quote** (Fraunces italic, text-2xl+): the dispatch summary.
- **Section slugs** (mono, text-xs, tracking-widest, uppercase): "THE DISPATCH",
  "WATCHLIST", "TONIGHT'S INDEX", "TRAJECTORY". This is the system's one label
  vocabulary — a newsroom-wire cadence, used as the heading itself, never as an
  eyebrow above a second heading.
- **Data readouts** (mono, tnum): every number in the interface is mono.
- **Body** (Archivo, text-sm/base): prose, table cells, form labels. Cap at 65–75ch.

### Named Rules
**The Three Voices Rule.** Serif speaks (titles, quotes), grotesque explains (prose,
UI), mono measures (numbers, labels). Never swap jobs.

## 4. Elevation

Flat. Depth comes from surface tone steps (canvas → surface → surface-2) and
hairlines. The single `.panel` treatment adds only an inset top highlight
(`inset 0 1px 0 rgba(244,237,226,0.04)`). No drop shadows anywhere.

## 5. Advanced Material

These are first-class parts of the system, each with a graceful floor:

- **SilkCanvas** (login): raw-WebGL domain-warped fbm shader in garnet/gold. Pauses
  off-screen and on hidden tabs; renders a single still under reduced motion; CSS
  radial-gradient fallback without WebGL.
- **Key art** (login): AI-generated "Seda en la medianoche" plate (`/silk.jpg`),
  captioned like a gallery piece, drifting at 26s (`.silk-drift`).
- **The Tape** (`Tape.tsx`): trading-floor ticker of every talent's overnight move,
  under the nav. 40s linear loop, pauses on hover/focus, duplicate strip aria-hidden,
  static under reduced motion.
- **View transitions**: avatar morphs roster→profile (React `ViewTransition`,
  `experimental.viewTransition`).
- **Reveal / CountUp / Sparkline**: IO-triggered entrance, odometer numerals, draw-on
  sparklines. Content is always visible without JS; reduced motion disables all three.

## 6. Components

- **Panels** (`.panel`): 0.625rem radius, surface fill, faint hairline. Used sparingly —
  the index list and the brief; most sections sit directly on canvas with slug headers.
- **Buttons:** amber fill, canvas-deep text, semibold, 0.375rem radius; hover → bright.
- **Inputs:** dark translucent fill, border hairline → amber on focus, no ring. Autofill
  is overridden to stay dark (`-webkit-autofill` inset shadow).
- **Focus:** global 2px amber `outline` on `:focus-visible`.
- **Nav:** sticky, blurred canvas at 85%, wordmark in Fraunces ("You" in amber), active
  link ivory with amber underline; mono date at left of links.
- **Index rows:** rank number (mono faint), avatar, Fraunces name, mono followers,
  noise-gated delta, sparkline. Hover: surface-2 fill + name → amber.
- **Tables:** mono uppercase faint header row, hairline dividers, right-aligned mono
  numerals, hover row fill.

## 7. Do's and Don'ts

### Do:
- **Do** keep every number in mono with `.tnum`.
- **Do** gate alarm colors behind the Noise Rule.
- **Do** give every animation a reduced-motion floor and keep content visible pre-JS.
- **Do** use full exact numerals when a chart's range is too tight for compact ticks.

### Don't:
- **Don't** use gradient text, glassmorphism-as-decoration, or drop shadows.
- **Don't** put white text on amber (2.5:1) — amber fills take canvas-deep text.
- **Don't** add a second accent hue; garnet is a material, not a message.
- **Don't** use the mono slug as an eyebrow above another heading — it IS the heading.
- **Don't** warm the canvas toward brown/cream; it stays garnet-black.
