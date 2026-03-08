# Splunk Design System — Fonts and Sizes Reference

This document summarizes typography, spacing, and related tokens from the **Splunk Design System** and **@splunk/themes** / **@splunk/react-ui** so the Use Case Repository UI can align with official guidance.

## Design system sources

- **Splunk UI Design System:** [splunkui.splunk.com](https://splunkui.splunk.com/) — Components, design tokens (@splunk/themes), icons, blueprints.
- **Typography:** [splunkui.splunk.com/Packages/react-ui/Typography](https://splunkui.splunk.com/Packages/react-ui/Typography)
- **Accessibility (Color):** [splunkui.splunk.com/DesignSystem/Accessibility/Color](https://splunkui.splunk.com/DesignSystem/Accessibility/Color) — Contrast and Color+ guidance.
- **Packages:** `@splunk/react-ui`, `@splunk/themes` (theme variables and mixins).

---

## Font families

From **@splunk/react-ui** and **@splunk/themes** (Prisma and Enterprise themes):

| Role    | Token / usage | Official stack |
|--------|----------------|----------------|
| **Sans (default)** | `sansFontFamily` / `fontFamily` | `'Splunk Platform Sans', 'Proxima Nova', Roboto, Droid, 'Helvetica Neue', Helvetica, Arial, sans-serif` (Enterprise); Prisma uses `'Splunk Data Sans'` instead of Proxima Nova. |
| **Mono** | `monoFontFamily` | `'Splunk Platform Mono', Inconsolata, Consolas, 'Droid Sans Mono', Monaco, 'Courier New', Courier, monospace` |
| **Serif** | `serifFontFamily` | `Georgia, 'Times New Roman', Times, serif` |

**Note:** “Splunk Platform Sans” is an alias for **Proxima Nova** (licensed). For public or unlicensed use, the library does not bundle fonts; you load them via `@font-face`. A common open alternative for the sans stack is **Source Sans 3** or **Source Sans Pro** (Adobe, SIL license), then the same fallbacks.

---

## Font sizes (typography scale)

From **@splunk/themes** (`prisma/base.js`, `enterprise/light.js`). All sizes are in **rem** (relative to root):

| Token           | Value      | Approx at 16px root | Use |
|-----------------|------------|----------------------|-----|
| `fontSizeSmall` | **0.75rem**  | 12px | Small labels, captions |
| `fontSize`      | **0.875rem** | 14px | **Default body text** |
| `fontSizeLarge` | **1rem**     | 16px | Large body, emphasis |
| `fontSizeXLarge`| **1.25rem**  | 20px | Subheadings |
| `fontSizeXXLarge` | **1.5rem** | 24px | Headings |

So the **default UI font size** in the design system is **0.875rem (14px at 16px root)**, not 16px.

---

## Font weights

From design-tokens typography:

| Token              | Value |
|--------------------|-------|
| `fontWeightLight`  | 300   |
| `fontWeightNormal` | 400   |
| `fontWeightSemiBold` | 500 |
| `fontWeightBold`    | 700   |
| `fontWeightHeavy`  | 800   |
| `fontWeightExtraBold` | 900 |

---

## Line heights

From **@splunk/themes**:

| Token                 | Value    | Use |
|-----------------------|----------|-----|
| `lineHeight` / `lineHeightNormal` | **1.5** | Default body |
| `lineHeightSingle`    | 1       | Buttons, badges, compact labels |
| `lineHeightTight`     | 1.2     | Tight headings |
| `lineHeightSnug`      | 1.25    | Slightly compact |
| `lineHeightComfortable` | 1.333 | Comfortable text |
| `lineHeightRelaxed`   | 1.375   | Relaxed text |
| `lineHeightSpacious`  | 1.429   | Larger text / headings |

---

## Spacing (design-tokens)

From **design-tokens/spacing-sizing.js**:

| Token            | Value  |
|------------------|--------|
| `spacingXSmall`  | 4px    |
| `spacingSmall`   | 8px    |
| `spacingMedium`  | 12px   |
| `spacingLarge`   | 16px   |
| `spacingXLarge`  | 24px   |
| `spacingXXLarge` | 32px   |
| `spacingXXXLarge`| 40px   |

---

## Accessibility (color and contrast)

From [Design System → Accessibility → Color](https://splunkui.splunk.com/DesignSystem/Accessibility/Color):

- **4.5:1** contrast for functional text **14 pt or smaller** and for focus borders &lt; 3px.
- **3:1** for focus borders ≥ 3px, graphical elements, and text **14 pt bold or larger than 18 pt**.
- **7:1** for text and images in **high-contrast mode**.
- **Color+:** Do not rely on color alone; combine with underline, bold, patterns, or icons.

---

## Summary for this repo

- **Fonts:** Use a Splunk-aligned stack: **Source Sans 3** (or similar) as first choice for sans, **Inconsolata** for mono, with the standard fallbacks above.
- **Sizes:** Prefer **rem** with scale: **0.75rem, 0.875rem, 1rem, 1.25rem, 1.5rem**; default body **0.875rem (14px at 16px root)**.
- **Line height:** Default **1.5** for body.
- **Spacing:** 4, 8, 12, 16, 24, 32, 40 px.
- **Contrast:** Meet WCAG 2.1 for text (e.g. 4.5:1 for small text) and follow Color+ for meaning.
