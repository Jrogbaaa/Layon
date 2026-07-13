---
target: platform/app/components/EngagementChart.tsx
total_score: 21
p0_count: 0
p1_count: 3
timestamp: 2026-07-13T12-16-44Z
slug: platform-app-components-engagementchart-tsx
---
## Design Health Score

| Heuristic | Score |
|---|---:|
| Visibility of System Status | 2/4 |
| Match System / Real World | 2/4 |
| User Control and Freedom | 3/4 |
| Consistency and Standards | 3/4 |
| Error Prevention | 2/4 |
| Recognition Rather Than Recall | 1/4 |
| Flexibility and Efficiency | 2/4 |
| Aesthetic and Minimalist Design | 3/4 |
| Error Recovery | 2/4 |
| Help and Documentation | 1/4 |
| **Total** | **21/40** |

## Anti-Patterns Verdict

Low AI-slop risk. The Medianoche register is coherent and distinctive. The chart's area-fill-plus-median composition is acceptable for the data, but the interaction model is more decorative than instrument-like. The deterministic detector found 0 issues in EngagementChart.tsx.

## Overall Impression

The chart makes spikes visible but does not make their identity visible. The plotted point, date axis, tooltip, and publication rail are separate interaction zones, so the user must remember horizontal position while cross-referencing another control.

## Strengths

- Garnet-black surfaces, scarce amber, mono data, and hairlines form a coherent Medianoche tool.
- Major outliers are visually legible and the chart has a clear position in the page hierarchy.
- Native publication-marker buttons, accessible names, focus styles, and live details are a strong accessibility foundation.

## Priority Issues

### [P1] No persistent one-to-one spike identity

Share one selected-post state between the chart and rail. Selecting either surface should highlight the matching point and marker, add a restrained vertical guide, and keep one detail panel visible until another selection or Escape.

### [P1] Thirty identical markers collapse on mobile

At 390px marker cells measure about 9px wide. Keep every post accessible, but emphasize only the selected point and meaningful outliers, preserve same-day distinction, and give the interaction a larger touch target.

### [P1] Date axis and tooltip do not support mobile reading

The axis shows only six labels and misses the latest plotted dates; the mobile tooltip can extend 23px past the viewport. Use deterministic date formatting, restrained label cadence, and a bounded detail/tooltip treatment.

### [P2] Instruction copy describes the control, not the task

Replace “Hover or focus a marker to inspect when the post was published” with task language such as “Select a point to identify the post.” Include engagement magnitude in accessible labels.

## Persona Red Flags

- Power users cannot jump from the largest spike to its post without precise hover and cross-reference.
- Mobile users see an ambiguous bead string and clipped tooltip content.
- Keyboard users can traverse markers, but the visual relationship to chart magnitude is not communicated.

## Questions

- Should hover commit the selection or preview until click/focus?
- Should Escape be the only way to clear a persistent selection?
- Is the chart primarily an outlier triage tool or a chronology audit?
