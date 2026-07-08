---
target: login page
total_score: 28
p0_count: 0
p1_count: 2
timestamp: 2026-07-08T08-34-43Z
slug: platform-app-login-page-tsx
---
Method: dual-agent (A: a78d15d3946c3a183 · B: acfaaeb81925406f0)

# Critique: Login page (`platform/app/login/page.tsx`)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Pending/error states exist, but no `aria-live`; field silently clears on failure |
| 2 | Match System / Real World | 3 | "Enter" CTA reads like the keyboard key; otherwise plain language |
| 3 | User Control and Freedom | 2 | No show-password toggle; failed attempt discards typed password |
| 4 | Consistency and Standards | 4 | Near-perfect DESIGN.md adherence |
| 5 | Error Prevention | 2 | Only `required`; blind masked entry of a shared password |
| 6 | Recognition Rather Than Recall | 4 | One labeled field, autoFocus |
| 7 | Flexibility and Efficiency | 2 | Missing `autocomplete="current-password"` blocks password managers |
| 8 | Aesthetic and Minimalist Design | 4 | Calm, centered, zero decoration |
| 9 | Error Recovery | 3 | "Incorrect password." is honest but offers no next step |
| 10 | Help and Documentation | 1 | No hint anywhere how to obtain the shared password |
| **Total** | | **28/40** | **Good — solid foundation, address weak areas** |

## Anti-Patterns Verdict

**LLM assessment:** PASS. No gradient text (the wordmark fix held), no glassmorphism, no hero-metric template, no eyebrows. Reads as a restrained internal tool, not AI slop.

**Deterministic scan:** CLI detector on the source file: exit 0, zero findings. Live browser-DOM overlay found 3 runtime findings: `gpt-thin-border-wide-shadow` (1px border + 24px shadow blur — this is the system's sanctioned Card Ambient shadow; false positive), `ai-color-palette` ("cyan gradient background" — the button fill; sanctioned by DESIGN.md but see the contrast issue below), `flat-type-hierarchy` (14/16/20px, ratio 1.4:1 — acceptable for a minimal login card; false positive in context).

**Where they agree:** the detector's gradient flag and the design review's contrast measurement point at the same element — the teal→blue button is the page's one real visual liability.

## Overall Impression

Aesthetically excellent and genuinely on-system. The work needed is not visual redesign but accessibility and failure-moment hardening: button contrast, error announcement, autocomplete, and one line of recovery copy.

## What's Working

- Disciplined system adherence: solid wordmark, canvas-bg input, border-only focus, single shadow.
- States actually handled: pending label, disabled opacity, inline server error, required + autoFocus.
- Composition holds at 1280px and 390px; clean hierarchy, nothing to remove.

## Priority Issues

- **[P1] Button text contrast fails WCAG AA** (login/page.tsx:34). White 16px semibold on the teal→blue gradient: 2.13:1 at the teal end, 3.33:1 at the blue end — both below 4.5:1. System-level: DESIGN.md canonically specifies this gradient. Fix: darken both gradient stops for button use in the token layer. Suggested command: /impeccable polish (system-level fix).
- **[P1] Error invisible to assistive tech** (login/page.tsx:29). No `role="alert"`, `aria-invalid`, or `aria-describedby`. Screen-reader users get silence on a failed login. Fix: add all three. Suggested command: /impeccable harden.
- **[P2] Missing `autocomplete="current-password"`** (login/page.tsx:23). Password managers can't offer to fill the shared password. Fix: add the attribute. Suggested command: /impeccable harden.
- **[P2] Error injection causes ~35px layout shift** (login/page.tsx:29). The error paragraph pushes the button down at the moment of re-click. Fix: reserve the line height or place the error below the button. Suggested command: /impeccable polish.
- **[P3] Copy: no recovery path, terse CTA.** "Enter" → "Sign in"; add one muted line about how to get the team password. Suggested command: /impeccable clarify.

## Persona Red Flags

**Jordan (First-Timer):** told "the dashboard is at this URL," hits the gate with no password and finds zero guidance — dead end at step 1. The cleared-on-error field forces a full blind retype.

**Sam (Accessibility-Dependent):** submits a wrong password and hears nothing (no live region); primary button contrast below AA; button relies on default browser focus outline while the input has a custom one.

## Minor Observations

- "Checking..." uses three ASCII periods, not an ellipsis; could become "Signing in…" if the CTA is renamed.
- Two focus vocabularies on a two-control page (custom border on input, browser default on button).

## Questions to Consider

- Should the primary-button gradient survive at all, or would a solid Signal Blue fill be more "Trading Floor"?
- What does a teammate without the password do — is there a canonical person/channel to name in the recovery copy?
