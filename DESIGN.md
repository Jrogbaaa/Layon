---
name: You First Gersh — Influencer Insights Platform
description: A calm, data-forward dashboard for triaging influencer roster health
colors:
  accent: "#2e8ff0"
  accent-strong: "#1c6fc4"
  accent-2: "#18c8a8"
  canvas: "#eef3f6"
  card: "#ffffff"
  border: "#e1e7ed"
  ink: "#12181f"
  muted: "#6b7684"
  positive: "#0e9c7f"
  positive-soft: "#e3f7f1"
  negative: "#d14343"
  negative-soft: "#fbeaea"
typography:
  display:
    fontFamily: "Plus Jakarta Sans, -apple-system, Segoe UI, sans-serif"
    fontWeight: 700
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Inter, -apple-system, Segoe UI, sans-serif"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  card: "1.125rem"
  control: "0.5rem"
spacing:
  sm: "0.5rem"
  md: "1rem"
  lg: "1.5rem"
components:
  button-primary:
    backgroundColor: "{colors.accent-strong}"
    textColor: "#ffffff"
    rounded: "{rounded.control}"
    padding: "0.5rem 0.75rem"
  card:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.card}"
---

# Design System: You First Gersh

## 1. Overview

**Creative North Star: "The Trading Floor"**

A calm, high-signal instrument for people making real decisions about real careers. Talent managers scan dozens of influencers a day; the system's job is to make "who needs attention" answerable at a glance, then get out of the way. Density is embraced, but never at the cost of scanability — every screen is a triage screen first, a report second.

This system explicitly rejects generic AI-dashboard scaffolding: gradient text, decorative glassmorphism, hero-metric-template stat blocks, and identical icon-card grids that could belong to any SaaS product. Restraint is deliberate: the blue/teal accent pair is a signal, not decoration, and its rarity is what keeps it meaningful.

**Key Characteristics:**
- Cool, near-white canvas with a single card surface — no visual competition with the data.
- One accent hue pair (blue primary, teal secondary) used sparingly and consistently as the signal color.
- Semantic color (positive/negative) reserved strictly for trend direction, never decoration.
- Plus Jakarta Sans for display weight, Inter for everything read at length.

## 2. Colors

A cool, restrained palette: a near-white blue-gray canvas, a single white card surface, and one accent pair that carries all brand and interactive signal.

### Primary
- **Signal Blue** (#2e8ff0): the primary accent — links, focus rings, the "Gersh" wordmark. Used deliberately, not decoratively.
- **Signal Blue Deep** (#1c6fc4): the fill color for primary buttons — a darkened Signal Blue that holds white text at ≥4.5:1 contrast (WCAG AA).

### Secondary
- **Signal Teal** (#18c8a8): paired with Signal Blue in button fills and chart accents. Never used for text-on-transparent gradients (see Don'ts).

### Neutral
- **Canvas** (#eef3f6): the page background — a cool, barely-tinted blue-gray, not a warm neutral.
- **Card White** (#ffffff): the single surface color for cards, the nav bar, and form fields.
- **Border Mist** (#e1e7ed): all hairline borders and dividers.
- **Ink** (#12181f): primary text color, near-black with a cool undertone.
- **Muted Slate** (#6b7684): secondary text — labels, timestamps, nav links at rest.

### Semantic
- **Positive** (#0e9c7f) / **Positive Soft** (#e3f7f1): upward trend deltas, growth badges.
- **Negative** (#d14343) / **Negative Soft** (#fbeaea): downward trend deltas, error states, attention flags.

### Named Rules
**The Signal Rule.** Signal Blue and Signal Teal together account for a small minority of any screen's surface. If the accent pair is more than a fifth of what's visible, something has been decorated instead of designed.

## 3. Typography

**Display Font:** Plus Jakarta Sans (with -apple-system, Segoe UI fallback)
**Body Font:** Inter (with -apple-system, Segoe UI fallback)

**Character:** A geometric display face paired with a humanist body face — confident headings, highly legible long-form data and copy. The pairing reads as precise without feeling cold.

### Hierarchy
- **Display** (700, tracking -0.02em): page titles, the wordmark, influencer names on the detail header.
- **Title** (600–700, text-lg to text-xl): section headings, card titles.
- **Body** (400, text-sm to text-base, line-height 1.5): stat labels, table content, recommendation copy. Cap prose at 65–75ch.
- **Label** (500, text-sm): nav links, form labels, muted metadata.

### Named Rules
**The Solid Text Rule.** Text is always a solid color from the palette. Gradients are reserved for fills (buttons, subtle chart accents) and never applied to text via `background-clip: text`.

## 4. Elevation

Flat by default with one soft, layered ambient shadow reserved for the card surface — no shadow escalation on hover, no drop-shadow-per-state vocabulary. Depth is conveyed primarily through the canvas/card contrast and hairline borders, not stacked shadows.

### Shadow Vocabulary
- **Card Ambient** (`box-shadow: 0 1px 2px rgba(20,30,45,0.04), 0 8px 24px -12px rgba(20,30,45,0.12)`): the only shadow in the system, applied uniformly to `.card`.

### Named Rules
**The One Shadow Rule.** There is exactly one elevation level. Introducing a second (e.g. a heavier "modal" shadow) requires a deliberate reason, not a hover-state reflex.

## 5. Components

Solid and tactile: buttons and inputs carry a touch more visual weight than a purely minimal system — filled buttons, visible borders on inputs, a clear focus state — while cards themselves stay quiet.

### Buttons
- **Shape:** rounded corners (0.5rem / `rounded-lg`).
- **Primary:** solid Signal Blue Deep fill (`bg-accent-strong`), white text, semibold weight, `px-3 py-2`. The teal→blue gradient fill was retired from buttons: white text on it measured 2.1:1 at the teal end, failing WCAG AA.
- **Hover / Focus:** opacity dip to 90% on hover; disabled state at 50% opacity.
- **Ghost (nav actions):** no fill, muted text at rest, ink text on hover (e.g. "Log out").

### Cards / Containers
- **Corner Style:** 1.125rem radius — noticeably soft, the system's signature shape.
- **Background:** Card White on Canvas.
- **Shadow Strategy:** Card Ambient (see Elevation).
- **Border:** 1px Border Mist.
- **Internal Padding:** 1.5–2rem depending on card density (roster cards tighter, login/detail cards looser).

### Inputs / Fields
- **Style:** 1px Border Mist, Canvas-colored background (not white — keeps forms visually part of the page, not a floating overlay), 0.5rem radius.
- **Focus:** border shifts to Signal Blue, no glow/ring.
- **Error:** Negative-colored helper text beneath the field; the field border itself stays neutral unless the project later adds inline validation.

### Navigation
- Single-row top bar, Card White background, Border Mist bottom hairline. Wordmark in Display weight (solid Signal Blue "Gersh", Ink "You First" — no gradient). Nav links in Muted Slate at rest, Ink on hover, no underline.

## 6. Do's and Don'ts

### Do:
- **Do** keep Signal Blue and Signal Teal rare and intentional — the Signal Rule.
- **Do** use Signal Blue Deep (#1c6fc4) for any fill that carries white text; plain Signal Blue and the teal→blue gradient both fail AA under white text.
- **Do** use the single Card Ambient shadow for every elevated surface; don't invent a second shadow scale.
- **Do** reserve Positive/Negative color strictly for trend direction and error states.

### Don't:
- **Don't** use gradient text (`background-clip: text` + gradient). This was present on the wordmark and has been replaced with solid Signal Blue.
- **Don't** add tiny uppercase tracked eyebrows above sections — not part of this system's vocabulary.
- **Don't** build identical icon+heading+text card grids; roster and detail layouts are data-first, not marketing-card-first.
- **Don't** use glassmorphism or decorative blur — the system is flat and opaque.
- **Don't** reach for the hero-metric-template (big number + small label + gradient accent) for stat tiles; let the number and its trend delta carry the weight without extra chrome.
- **Don't** introduce a warm-tinted neutral background; Canvas stays cool (blue-gray), matching the "Trading Floor" register.
