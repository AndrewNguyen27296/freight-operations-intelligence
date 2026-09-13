# Freight Operations Intelligence. Design system v1.0

Status: specification, ready to implement.
Target runtime: Streamlit 1.50.0, Plotly 6.9.0 (both already pinned in `requirements.txt`).
Default theme: dark. Alternative theme: light. Both are complete.

How to read this document

- Every rule ends with its reason in one clause. If the reason no longer holds, the rule is up for review.
- `JUDGEMENT CALL` marks a decision where another designer might reasonably choose differently. Each one names the rejected alternative and why.
- Three decisions depended on the product owner and were settled with them. Section 8 lists them.
- `STREAMLIT LIMIT` marks a place where the ideal component cannot be built from Streamlit primitives plus CSS. The nearest buildable alternative follows immediately.
- Token names carry the prefix `--fo-` so they never collide with Streamlit's own custom properties.
- Contrast figures quoted here were computed with the WCAG 2.x relative luminance formula against the exact hex values in the token block. Recompute after any token change, because a token that drifts by two hex digits can drop a pair below a gate. Appendix B is the register.

Nothing in this document waits on an unanswered question.

---

## 0. Foundations restated, plus the derived tokens they required

The settled palettes are used exactly as given. Building on them exposed six gaps that a token set must close before a single component can be specified. These are the only additions to the colour foundation.

| Gap | Why it exists | Resolution |
|---|---|---|
| `ink-muted` fails 4.5:1 for text on every surface in both themes (3.94 dark, 3.86 light). | The settled value was chosen for tertiary emphasis, not for body copy. | `ink-muted` is restricted to icons at 3:1, disabled text, and text at 24 px or larger. Captions, notes and placeholders use `ink-secondary`. |
| The accent fails 4.5:1 as text in light (4.42 on white). | Accent was validated as a mark colour, and marks need only 3:1. | A separate `--fo-ink-link` token exists for accent-coloured text. In dark it equals the accent. In light it is `#2770c7`, the least-darkened value that clears 4.5:1 on all three surfaces. |
| Neither accent can host a 14 px button label at 4.5:1 (white on `#3987e5` is 3.64, white on `#2a78d6` is 4.42). | Same reason as above. | Primary button fill is its own token. Dark fills with the accent and sets the label in `#0f1115` (5.19:1). Light fills with `#2262af` and sets the label in white (6.12:1). See JUDGEMENT CALL in 4.3. |
| Warning and serious fail 3:1 as marks on light surfaces (1.83 and 2.64 on white). | The status hues are tuned to read on dark. | Each status colour gets a `-fill` token (the reserved hex, unchanged) and an `-ink` token used for icons, text and borders. Dark `-ink` equals `-fill` except critical, which lightens to `#d95f5f` to reach 4.5:1 as text. Light `-ink` darkens each hue to the least value that clears 4.5:1 on all three surfaces. The reserved hue remains the only hue used for that meaning. |
| Alerts, badges and finding severity need a background that carries status without failing text contrast. | A solid status fill cannot host both dark and light text consistently. | `-tint` tokens mix the status fill into `surface` at 16% (dark) or 10% (light). Ink on every tint stays above 11:1. |
| Inputs need a boundary at 3:1 and hovered rows need a surface step, and neither exists in the settled set. | The settled hairline reads at 1.2:1, which is correct for dividers and wrong for control boundaries. | `--fo-line-control` at 3:1 on `plane`, plus `--fo-surface-hover`, `--fo-surface-pressed`, `--fo-accent-tint` and `--fo-accent-selection`. |

Everything else in colour is the settled foundation, renamed by role.

---

## 1. Token set

### 1.1 Scales, stated once

| Scale | Base | Ratio or step | Reason |
|---|---|---|---|
| Type | 14 px | 1.2 (minor third), each step rounded to a whole pixel | Whole pixels keep hairlines and baselines crisp; 1.2 gives enough steps between 12 and 42 for an analytics UI that needs many small distinctions. |
| Line height | 4 px grid | Each type step gets the nearest multiple of 4 that yields 1.3 to 1.5 | Multiples of 4 let text blocks and controls share one vertical rhythm. |
| Spacing | 4 px | Linear to 24 (4, 8, 12, 16, 20, 24), then 32, 40, 48, 64 | Small steps are needed inside controls, large steps only between sections. |
| Radius | 3 px | 0, 3, 6, pill | Small radii read as an instrument; anything above 6 px reads as consumer software. |
| Border | 1 px | 1 for hairline and control, 2 for focus | A 1 px line is the finest a display renders reliably; 2 px is the WCAG 2.4.13 focus minimum. |
| Motion | 80 ms | 80, 160, 240 | Hover feedback should feel instant; layout changes need a beat to be followed by the eye. |
| Icon | 16 px | 16, 20, 24 | One stroke weight across three sizes keeps icons from competing with type. |

### 1.2 Copy-pasteable CSS

Dark is `:root`. Light is a second `:root` block emitted after it when the light theme is selected. A later declaration of the same custom property wins, so no attribute on `<html>` is needed, which matters because Streamlit gives no way to set one.

```css
/* =========================================================
   Freight Operations Intelligence. Design tokens.
   Dark theme is the default and lives on :root.
   ========================================================= */

@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600&family=IBM+Plex+Sans:wght@400..600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  /* ---- Font stacks. Fallbacks chosen for close x-height and width. ---- */
  --fo-font-display: "Space Grotesk", "Segoe UI Variable Display", "Segoe UI", "Helvetica Neue", system-ui, sans-serif;
  --fo-font-ui:      "IBM Plex Sans", "Segoe UI", "Helvetica Neue", "Noto Sans", system-ui, sans-serif;
  --fo-font-mono:    "IBM Plex Mono", "Cascadia Mono", "SF Mono", Consolas, Menlo, "DejaVu Sans Mono", monospace;

  /* ---- Type sizes. Ratio 1.2, base 14, whole pixels. ---- */
  --fo-text-2xs: 11px;   /* overline only. Floor exception, see 2.1 */
  --fo-text-xs:  12px;
  --fo-text-sm:  13px;   /* tabular figures only, see 2.1 */
  --fo-text-md:  14px;   /* base */
  --fo-text-lg:  17px;
  --fo-text-xl:  20px;
  --fo-text-2xl: 24px;
  --fo-text-3xl: 29px;
  --fo-text-4xl: 35px;
  --fo-text-5xl: 42px;

  /* ---- Line heights, on the 4 px grid. ---- */
  --fo-leading-2xs: 16px;
  --fo-leading-xs:  16px;
  --fo-leading-sm:  20px;
  --fo-leading-md:  20px;
  --fo-leading-lg:  24px;
  --fo-leading-xl:  28px;
  --fo-leading-2xl: 32px;
  --fo-leading-3xl: 36px;
  --fo-leading-4xl: 40px;
  --fo-leading-5xl: 48px;

  /* ---- Weights. Body weight is theme dependent, see 2.1. ---- */
  --fo-weight-body:     450;
  --fo-weight-regular:  400;
  --fo-weight-medium:   500;
  --fo-weight-semibold: 600;

  /* ---- Letter spacing. ---- */
  --fo-tracking-tight:  -0.02em;  /* display 35 px and up */
  --fo-tracking-snug:   -0.01em;  /* display 20 to 29 px */
  --fo-tracking-normal:  0;
  --fo-tracking-wide:    0.08em;  /* overline, uppercase */

  /* ---- Spacing. Base 4. ---- */
  --fo-space-0: 0;
  --fo-space-1: 4px;
  --fo-space-2: 8px;
  --fo-space-3: 12px;
  --fo-space-4: 16px;
  --fo-space-5: 20px;
  --fo-space-6: 24px;
  --fo-space-8: 32px;
  --fo-space-10: 40px;
  --fo-space-12: 48px;
  --fo-space-16: 64px;

  /* ---- Radii. ---- */
  --fo-radius-0: 0;         /* table cells */
  --fo-radius-1: 3px;       /* controls, chips, badges */
  --fo-radius-2: 6px;       /* cards, panels, dropzone, alerts */
  --fo-radius-pill: 999px;  /* pills only */

  /* ---- Borders. ---- */
  --fo-border-hairline: 1px;
  --fo-border-control:  1px;
  --fo-border-focus:    2px;
  --fo-focus-offset:    2px;

  /* ---- Motion. ---- */
  --fo-duration-instant: 80ms;
  --fo-duration-short:   160ms;
  --fo-duration-medium:  240ms;
  --fo-duration-enter:   320ms;   /* page-load settle, see 1.4 */
  --fo-stagger:          40ms;    /* per block, capped at 12 steps */
  --fo-ease-standard: cubic-bezier(0.2, 0, 0, 1);
  --fo-ease-exit:     cubic-bezier(0.4, 0, 1, 1);

  /* ---- Icon sizes and stroke. ---- */
  --fo-icon-sm: 16px;
  --fo-icon-md: 20px;
  --fo-icon-lg: 24px;
  --fo-icon-stroke: 1.5;    /* in viewBox units, not px */

  /* ---- Layout. ---- */
  --fo-content-max: 1360px;
  --fo-gutter: 16px;
  --fo-margin: 24px;
  --fo-control-height: 36px;
  --fo-control-height-sm: 28px;
  --fo-row-height: 32px;
  --fo-row-height-compact: 28px;

  /* =========================================================
     DARK COLOUR (default)
     ========================================================= */

  /* Surfaces */
  --fo-plane:   #0f1115;   /* page background */
  --fo-surface: #16181d;   /* cards, tiles, panels */
  --fo-raised:  #1c1f26;   /* popovers, selected segments, table header, control fill */
  --fo-surface-hover:   #1f2126;   /* ink at 4% over surface */
  --fo-surface-pressed: #282a2e;   /* ink at 8% over surface */
  --fo-scrim: rgba(15, 17, 21, 0.72);

  /* Lines */
  --fo-line-hairline: #262a33;   /* dividers, card borders, gridlines. 1.24:1 on surface, intentionally below 3:1 */
  --fo-line-control:  #5c6270;   /* input and control boundaries. 3.09:1 on plane. Controls sit on plane or in a raised fieldset, never bare on surface, see 4.4 */
  --fo-line-strong:   #6f7787;   /* chart baseline, hover boundaries, totals rule. 3.94:1 on surface */

  /* Ink */
  --fo-ink:           #f2f4f7;   /* 16.1:1 on surface */
  --fo-ink-secondary: #a3aab8;   /* 7.6:1 on surface. Captions, labels, placeholders */
  --fo-ink-muted:     #6f7787;   /* 3.9:1 on surface. Icons, disabled text, text 24 px and larger only */
  --fo-ink-inverse:   #0f1115;   /* text on light ramp cells */
  --fo-ink-link:      #3987e5;   /* 4.88:1 on surface */

  /* Accent */
  --fo-accent:           #3987e5;
  --fo-accent-hover:     #4c92e7;
  --fo-accent-active:    #3277ca;
  --fo-accent-tint:      #1c2a3d;   /* accent at 16% over surface */
  --fo-accent-selection: #1e334d;   /* accent at 24% over surface */
  --fo-focus:            #3987e5;   /* 4.88:1 on surface, 5.19:1 on plane */

  /* Action fills (buttons). Separate from accent so labels can clear 4.5:1 */
  --fo-action-primary-fill:        #3987e5;
  --fo-action-primary-fill-hover:  #4c92e7;
  --fo-action-primary-fill-active: #3277ca;
  --fo-action-primary-ink:         #0f1115;   /* 5.19:1 on fill */

  /* Status. -fill is the reserved hue. -ink clears 4.5:1 on every surface. -tint is a background */
  --fo-status-good-fill:     #0ca30c;
  --fo-status-good-ink:      #0ca30c;   /* 5.29:1 on surface */
  --fo-status-good-tint:     #142e1a;
  --fo-status-warning-fill:  #fab219;
  --fo-status-warning-ink:   #fab219;   /* 9.68:1 */
  --fo-status-warning-tint:  #3a311c;
  --fo-status-serious-fill:  #ec835a;
  --fo-status-serious-ink:   #ec835a;   /* 6.73:1 */
  --fo-status-serious-tint:  #382927;
  --fo-status-critical-fill: #d03b3b;
  --fo-status-critical-ink:  #d95f5f;   /* 4.86:1. The fill alone is 3.70:1, enough for a mark, not for text */
  --fo-status-critical-tint: #341e22;
  --fo-status-neutral-ink:   #a3aab8;   /* "no data" and "info" carry no status */
  --fo-status-neutral-tint:  #1c1f26;

  /* Categorical series. Fixed slots. Colour follows the entity */
  --fo-series-1: #3987e5;
  --fo-series-2: #d95926;
  --fo-series-3: #199e70;
  --fo-series-4: #c98500;
  --fo-series-5: #d55181;
  --fo-series-6: #008300;
  --fo-series-other: #6f7787;   /* the folded tail, never a seventh hue */

  /* Sequential ramp. Dark anchor flipped: step 1 is the lowest value and darkest */
  --fo-seq-1: #0d366b;
  --fo-seq-2: #184f95;
  --fo-seq-3: #256abf;
  --fo-seq-4: #3987e5;
  --fo-seq-5: #6da7ec;
  --fo-seq-6: #9ec5f4;
  --fo-seq-7: #cde2fb;
  --fo-seq-8: #eef5fd;
  --fo-seq-ink-flip: 5;   /* from this step upward the cell label uses --fo-ink-inverse */

  /* Chart chrome */
  --fo-chart-grid:      #262a33;
  --fo-chart-baseline:  #6f7787;
  --fo-chart-tick-ink:  #a3aab8;
  --fo-chart-crosshair: #6f7787;
  --fo-chart-hover-bg:  #1c1f26;

  /* Elevation. Used only where a surface floats above another */
  --fo-shadow-1: 0 2px 8px rgba(0, 0, 0, 0.45), 0 0 0 1px #262a33;   /* popover, menu, calendar */
  --fo-shadow-2: 0 8px 24px rgba(0, 0, 0, 0.55), 0 0 0 1px #262a33;  /* toast */
}

/* =========================================================
   LIGHT COLOUR. Emitted after the block above when selected.
   Every value re-chosen against light surfaces, not inverted.
   ========================================================= */
:root {
  --fo-weight-body: 400;   /* dark text on light needs no optical thickening */

  --fo-plane:   #f7f8fa;
  --fo-surface: #ffffff;
  --fo-raised:  #f2f4f7;
  --fo-surface-hover:   #f6f6f6;
  --fo-surface-pressed: #ececed;
  --fo-scrim: rgba(18, 21, 26, 0.48);

  --fo-line-hairline: #e3e6eb;   /* 1.25:1 on surface */
  --fo-line-control:  #8f96a3;   /* 3.02:1 on plane, 2.97:1 on white, see 4.4 */
  --fo-line-strong:   #7b8291;   /* 3.86:1 */

  --fo-ink:           #12151a;   /* 18.3:1 */
  --fo-ink-secondary: #4a515e;   /* 8.0:1 */
  --fo-ink-muted:     #7b8291;   /* 3.86:1. Same restriction as dark */
  --fo-ink-inverse:   #ffffff;
  --fo-ink-link:      #2770c7;   /* 4.50:1 on raised, 4.99:1 on white. The accent itself is 4.42:1 */

  --fo-accent:           #2a78d6;
  --fo-accent-hover:     #266cc1;
  --fo-accent-active:    #2262af;
  --fo-accent-tint:      #eaf2fb;
  --fo-accent-selection: #d9e7f8;
  --fo-focus:            #2a78d6;   /* 4.42:1 on white, 4.16:1 on plane */

  --fo-action-primary-fill:        #2262af;
  --fo-action-primary-fill-hover:  #1f5ea6;
  --fo-action-primary-fill-active: #184f95;
  --fo-action-primary-ink:         #ffffff;   /* 6.12:1 on fill */

  --fo-status-good-fill:     #0ca30c;
  --fo-status-good-ink:      #0a820a;   /* 4.99:1 on white, 4.53:1 on raised */
  --fo-status-good-tint:     #e7f6e7;
  --fo-status-warning-fill:  #fab219;
  --fo-status-warning-ink:   #92680f;   /* 4.99:1. The fill is 1.83:1 and never carries meaning alone in light */
  --fo-status-warning-tint:  #fef7e8;
  --fo-status-serious-fill:  #ec835a;
  --fo-status-serious-ink:   #a65c3f;   /* 4.97:1 */
  --fo-status-serious-tint:  #fdf3ee;
  --fo-status-critical-fill: #d03b3b;
  --fo-status-critical-ink:  #cc3a3a;   /* 4.96:1 */
  --fo-status-critical-tint: #faebeb;
  --fo-status-neutral-ink:   #4a515e;
  --fo-status-neutral-tint:  #f2f4f7;

  --fo-series-1: #2a78d6;
  --fo-series-2: #eb6834;
  --fo-series-3: #1baf7a;
  --fo-series-4: #eda100;
  --fo-series-5: #e87ba4;
  --fo-series-6: #008300;
  --fo-series-other: #7b8291;

  --fo-seq-1: #eef5fd;
  --fo-seq-2: #cde2fb;
  --fo-seq-3: #9ec5f4;
  --fo-seq-4: #6da7ec;
  --fo-seq-5: #3987e5;
  --fo-seq-6: #256abf;
  --fo-seq-7: #184f95;
  --fo-seq-8: #0d366b;
  --fo-seq-ink-flip: 6;   /* from this step upward the cell label uses --fo-ink-inverse */

  --fo-chart-grid:      #e3e6eb;
  --fo-chart-baseline:  #7b8291;
  --fo-chart-tick-ink:  #4a515e;
  --fo-chart-crosshair: #7b8291;
  --fo-chart-hover-bg:  #ffffff;

  --fo-shadow-1: 0 2px 8px rgba(18, 21, 26, 0.10), 0 0 0 1px #e3e6eb;
  --fo-shadow-2: 0 8px 24px rgba(18, 21, 26, 0.16), 0 0 0 1px #e3e6eb;
}

/* Motion respects the operating system setting, because a user who turned animation off did so for a reason. */
@media (prefers-reduced-motion: reduce) {
  :root {
    --fo-duration-instant: 0ms;
    --fo-duration-short:   0ms;
    --fo-duration-medium:  0ms;
    --fo-duration-enter:   0ms;
  }
}
```

### 1.3 Streamlit theme configuration

Streamlit paints its own widgets from `.streamlit/config.toml`, not from CSS custom properties, so the same values are declared there. Both files ship. Dark is the default `config.toml`.

```toml
# .streamlit/config.toml  (dark, default)
[theme]
base = "dark"
primaryColor = "#3987e5"
backgroundColor = "#0f1115"
secondaryBackgroundColor = "#16181d"
textColor = "#f2f4f7"
linkColor = "#3987e5"
borderColor = "#262a33"
showWidgetBorder = true
baseRadius = "6px"
buttonRadius = "3px"
baseFontSize = 14
baseFontWeight = 450
font = "IBM Plex Sans, Segoe UI, Helvetica Neue, Noto Sans, system-ui, sans-serif"
headingFont = "Space Grotesk, Segoe UI Variable Display, Segoe UI, Helvetica Neue, system-ui, sans-serif"
codeFont = "IBM Plex Mono, Cascadia Mono, SF Mono, Consolas, Menlo, monospace"
codeFontSize = "13px"
codeBackgroundColor = "#1c1f26"
dataframeBorderColor = "#262a33"
dataframeHeaderBackgroundColor = "#1c1f26"
chartCategoricalColors = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300"]
chartSequentialColors = ["#0d366b", "#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb", "#eef5fd"]
headingFontSizes = ["24px", "20px", "17px", "14px", "14px", "12px"]
headingFontWeights = [600, 500, 600, 600, 500, 500]

# Semantic colours. Streamlit's own alerts, st.badge and markdown colour directives
# read these, so a stray st.warning() lands on the status palette instead of Streamlit's.
# red = critical, orange = serious, yellow = warning, green = good, blue = accent, gray = neutral.
redColor = "#d95f5f"
redBackgroundColor = "#341e22"
redTextColor = "#f2f4f7"
orangeColor = "#ec835a"
orangeBackgroundColor = "#382927"
orangeTextColor = "#f2f4f7"
yellowColor = "#fab219"
yellowBackgroundColor = "#3a311c"
yellowTextColor = "#f2f4f7"
greenColor = "#0ca30c"
greenBackgroundColor = "#142e1a"
greenTextColor = "#f2f4f7"
blueColor = "#3987e5"
blueBackgroundColor = "#1c2a3d"
blueTextColor = "#f2f4f7"
grayColor = "#a3aab8"
grayBackgroundColor = "#1c1f26"
grayTextColor = "#f2f4f7"
violetColor = "#a3aab8"          # violet is not in the palette; mapped to neutral so it can never appear by accident
violetBackgroundColor = "#1c1f26"
violetTextColor = "#f2f4f7"

[server]
runOnSave = true
```

```toml
# .streamlit/config.light.toml  (light alternative)
[theme]
base = "light"
primaryColor = "#2a78d6"
backgroundColor = "#f7f8fa"
secondaryBackgroundColor = "#ffffff"
textColor = "#12151a"
linkColor = "#2770c7"
borderColor = "#e3e6eb"
showWidgetBorder = true
baseRadius = "6px"
buttonRadius = "3px"
baseFontSize = 14
baseFontWeight = 400
font = "IBM Plex Sans, Segoe UI, Helvetica Neue, Noto Sans, system-ui, sans-serif"
headingFont = "Space Grotesk, Segoe UI Variable Display, Segoe UI, Helvetica Neue, system-ui, sans-serif"
codeFont = "IBM Plex Mono, Cascadia Mono, SF Mono, Consolas, Menlo, monospace"
codeFontSize = "13px"
codeBackgroundColor = "#f2f4f7"
dataframeBorderColor = "#e3e6eb"
dataframeHeaderBackgroundColor = "#f2f4f7"
chartCategoricalColors = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
chartSequentialColors = ["#eef5fd", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
headingFontSizes = ["24px", "20px", "17px", "14px", "14px", "12px"]
headingFontWeights = [600, 500, 600, 600, 500, 500]

# Semantic colours, light values. Same mapping as dark. Text stays ink, because the tints are pale.
redColor = "#cc3a3a"
redBackgroundColor = "#faebeb"
redTextColor = "#12151a"
orangeColor = "#a65c3f"
orangeBackgroundColor = "#fdf3ee"
orangeTextColor = "#12151a"
yellowColor = "#92680f"
yellowBackgroundColor = "#fef7e8"
yellowTextColor = "#12151a"
greenColor = "#0a820a"
greenBackgroundColor = "#e7f6e7"
greenTextColor = "#12151a"
blueColor = "#2a78d6"
blueBackgroundColor = "#eaf2fb"
blueTextColor = "#12151a"
grayColor = "#4a515e"
grayBackgroundColor = "#f2f4f7"
grayTextColor = "#12151a"
violetColor = "#4a515e"
violetBackgroundColor = "#f2f4f7"
violetTextColor = "#12151a"
```

Notes for the engineer

- Verify each key against `streamlit config show` on 1.50.0 before relying on it, because the theme namespace grew quickly between 1.45 and 1.50 and a misspelt key fails silently.
- Streamlit's `font` key only names a family. The face itself must load. The `@import` line at the top of the token block does this, injected once per run through `st.markdown(..., unsafe_allow_html=True)`. The alternative, `[[theme.fontFaces]]` entries pointing at self-hosted woff2 files under `static/` with `enableStaticServing = true`, is the right choice for a customer who blocks Google Fonts at the proxy. Note for the owner: several EU data protection authorities treat Google Fonts calls as a personal data transfer. Fonts loading from Google is a settled foundation and is kept, but self-hosting is the recommended change for on-premise builds.
- `page_icon` in `st.set_page_config` currently takes an emoji. Replace it with a 32 px PNG or SVG of the product mark, because emoji are banned in this system and render differently on every platform.

Theme selection. Decided: the theme is chosen per build. A customer's build ships either `config.toml` (dark) or `config.light.toml` renamed to `config.toml` (light), and the token injection helper reads `theme.base` from `st.get_option` to emit the matching `:root` block, because the buyer pays per build, a build has one audience, and Streamlit has no supported runtime theme switch. The rejected alternative, a sidebar toggle calling `st._config.set_option("theme.base", ...)` and `st.rerun()`, uses a private API that can break on a minor upgrade.

Streamlit's own settings menu offers viewers its stock light and dark themes, which ignore every token here. Both config files therefore also carry:

```toml
[client]
toolbarMode = "minimal"
```

This removes the menu for viewers, because a theme picker that bypasses the design system is a bug with a UI.

### 1.4 Motion rules

Motion in this product has three jobs: confirm a pointer action, follow a layout change, and settle the page on load. Nothing else moves.

| Motion | Duration | Easing | Where | Reason |
|---|---|---|---|---|
| State feedback | `--fo-duration-instant` 80 ms | standard | hover, active, focus on every control; colour, background and border only | Feedback should feel simultaneous with the pointer. |
| State change | `--fo-duration-short` 160 ms | standard | segmented selection, tab indicator, chevron rotation, condensed header in and out | A change the reader caused should be followable but not waited for. |
| Layout change | `--fo-duration-medium` 240 ms | standard | expander open, table view swap | Content that moves other content needs a beat so the eye can track it. |
| Entrance | `--fo-duration-enter` 320 ms, staggered `--fo-stagger` 40 ms per block, capped at 12 steps | standard | each top-level block of the briefing on first load, from opacity 0.35 and 8 px below to rest | The page settles rather than snaps, and it settles top to bottom in reading order. The start state is visible, so a thumbnail or a slow connection never shows an empty page. |

Rules

- Numbers never animate. No count-up on a KPI or a hero figure, because a number in motion is read as a number that is changing.
- Nothing is linked to scroll position. No parallax, no reveal-on-scroll, no scroll-driven progress, because scroll-linked motion is the signature of a marketing page, the reader is here to check figures, and Streamlit exposes no scroll position to build it with anyway. The condensed header (4.12) is the one scroll-aware element, and it changes state, not position.
- `prefers-reduced-motion: reduce` sets every duration to 0 and removes the entrance animation, because a user who turned motion off did so for a reason.
- Plotly transitions are off (`transition.duration=0`), because a chart that animates between filter states implies continuity between two different datasets.
- No easing other than the two tokens. `--fo-ease-standard` for anything entering or changing, `--fo-ease-exit` for anything leaving.

---

## 2. Type ramp

Space Grotesk carries display sizes and every large numeral. IBM Plex Sans carries interface text. IBM Plex Mono carries every figure that sits in a column, because column figures must align and Plex Mono's fixed advance guarantees it where `tnum` only approximates it.

### 2.1 The ramp

| Step | Font | Size / line | Weight | Tracking | One job |
|---|---|---|---|---|---|
| `kpi-hero` | Space Grotesk | 42 / 48 | 600 | -0.02em | The single most important figure on the page, used at most once per view. |
| `kpi-value` | Space Grotesk | 35 / 40 | 600 | -0.02em | The value in a KPI tile at 4 tiles or fewer per row. |
| `kpi-value-compact` | Space Grotesk | 24 / 32 | 600 | -0.01em | KPI value at 5 or more tiles per row, or below the 1024 px breakpoint. |
| `figure` | Space Grotesk | 29 / 36 | 600 | -0.01em | The pulled-out figure in a findings panel. |
| `h1` | Space Grotesk | 24 / 32 | 600 | -0.01em | Page title, once per page. |
| `h2` | Space Grotesk | 20 / 28 | 500 | -0.01em | Section heading and the headline claim of a finding. |
| `h3` | IBM Plex Sans | 17 / 24 | 600 | 0 | Card title. |
| `h4` | IBM Plex Sans | 14 / 20 | 600 | 0 | Sub-heading inside a card, table title, alert title. |
| `lead` | IBM Plex Sans | 17 / 24 | 450 dark, 400 light | 0 | Executive summary sentences only, at most three per view. |
| `body` | IBM Plex Sans | 14 / 20 | 450 dark, 400 light | 0 | Paragraph text, finding support sentences, input values. |
| `body-strong` | IBM Plex Sans | 14 / 20 | 600 | 0 | Inline emphasis, the recommended action. |
| `label` | IBM Plex Sans | 14 / 20 | 500 | 0 | Control labels, button labels, tab labels, table header text. |
| `label-sm` | IBM Plex Sans | 12 / 16 | 500 | 0 | Small button, badge, chip, pill. |
| `caption` | IBM Plex Sans | 12 / 16 | 400 | 0 | Notes under charts, source lines, helper text, timestamps. Colour `ink-secondary`, never `ink-muted`. |
| `overline` | IBM Plex Sans | 11 / 16 | 500 | +0.08em, uppercase | KPI tile label, finding number, action lead-in. The only uppercase in the system. |
| `tabular` | IBM Plex Mono | 13 / 20 | 400 | 0 | Every number in a table cell, including the header unit. |
| `tabular-strong` | IBM Plex Mono | 13 / 20 | 500 | 0 | Totals row, the cell a finding cites. |
| `tabular-sm` | IBM Plex Mono | 12 / 16 | 400 | 0 | Chart tick labels on numeric axes, tooltip figures, KPI delta figure. |

Rules

- `overline` sits below the ramp's 12 px floor at 11 px. It is permitted only because uppercase with wide tracking restores legibility at that size, and only for three slots, because more uppercase reads as shouting.
- `tabular` is 13 px, not 14, because Plex Mono is wider than Plex Sans and 13 px mono matches the optical size of 14 px sans in a mixed row.
- Body weight is 450 in dark and 400 in light, because light text on dark loses apparent weight through halation and 450 compensates without reading as bold.
- Nothing is set below 11 px, because 11 px is the floor at which Plex Sans keeps its counters open on a 1x display.
- Headings never skip a level, because a page that jumps from 14 to 29 has no middle for the eye to rest on.

### 2.2 Large-number treatment (KPI values)

```css
.fo-kpi__value {
  font-family: var(--fo-font-display);
  font-size: var(--fo-text-4xl);
  line-height: var(--fo-leading-4xl);
  font-weight: var(--fo-weight-semibold);
  letter-spacing: var(--fo-tracking-tight);
  font-variant-numeric: tabular-nums lining-nums;
  font-feature-settings: "tnum" 1, "lnum" 1;
  color: var(--fo-ink);
  white-space: nowrap;
}
.fo-kpi__value .fo-unit {   /* currency code or % attached to the value */
  font-size: var(--fo-text-lg);
  font-weight: var(--fo-weight-medium);
  letter-spacing: 0;
  color: var(--fo-ink-secondary);
  margin-right: var(--fo-space-1);   /* unit precedes the value, see 6.2 */
}
```

- Tabular figures are forced on so that two tiles with the same digit count align, which lets the eye compare across the strip.
- The unit is set smaller and in `ink-secondary`, because the reader has already read the label and the unit is confirmation, not news.
- Values never wrap, because a wrapped number is read as two numbers. If a value does not fit at `kpi-value`, the tile drops to `kpi-value-compact`. If it still does not fit, the formatter abbreviates (section 6), not the type.

### 2.3 Tabular treatment (tables)

```css
.fo-table td.fo-num, .fo-table th.fo-num {
  font-family: var(--fo-font-mono);
  font-size: var(--fo-text-sm);
  line-height: var(--fo-leading-sm);
  font-variant-numeric: tabular-nums lining-nums;
  text-align: right;
  padding-right: var(--fo-space-3);
}
```

- Numeric columns are right-aligned, because magnitude is read from the decimal point leftwards.
- The header of a numeric column is also right-aligned and carries the unit in parentheses, because a unit in every cell doubles the ink for no information.
- Negatives use the true minus sign U+2212, because a hyphen is narrower and breaks column alignment.
- Negatives are not coloured red, because red is a status colour and a negative variance is not always bad.

---

## 3. Spacing and layout

### 3.1 Container

- Content max width 1360 px, centred, because a 13 px mono table becomes hard to scan past roughly 1300 px of row width.
- Page margin 24 px each side at and above 1024 px, 16 px below, because Streamlit's default padding wastes space on a dashboard.
- The Streamlit sidebar stays collapsed by default and holds only data source, theme and export controls, because the executive reader should see findings, not plumbing.

```css
.block-container {
  max-width: var(--fo-content-max);
  padding: var(--fo-space-6) var(--fo-margin) var(--fo-space-12);
}
[data-testid="stVerticalBlock"] { gap: var(--fo-space-4); }
[data-testid="stHorizontalBlock"] { gap: var(--fo-gutter); }
```

### 3.2 Grid

Streamlit has no grid; it has `st.columns` with ratios, and it stacks all columns below 640 px. The system therefore defines a 12-unit conceptual grid and maps every layout to `st.columns` ratios that reproduce it.

| Layout | `st.columns` call | Grid units |
|---|---|---|
| KPI strip, 4 tiles | `st.columns(4, gap="small")` | 3 + 3 + 3 + 3 |
| KPI strip, 5 tiles | `st.columns(5, gap="small")` | 2.4 each; tiles drop to `kpi-value-compact` |
| Chart pair | `st.columns([5, 7], gap="medium")` | 5 + 7 |
| Finding text and figure | `st.columns([8, 4], gap="medium")` | 8 + 4 |
| Filter bar | `st.columns([3, 3, 4, 2], gap="small")` | date range, carrier, lane, action |
| Full width | no columns | 12 |

Streamlit's `gap` values are overridden by the CSS above so that `small`, `medium` and `large` all render as 16 px, because a dashboard needs one gutter and three sizes invite drift. If a wider separation is needed, insert vertical space, not a wider gutter.

### 3.3 Vertical rhythm

| Between | Space |
|---|---|
| Page title and first content | 24 px |
| Sections (KPI strip and findings, findings and charts) | 32 px |
| Cards in the same section | 16 px |
| Card border and card content (padding) | 20 px horizontal, 16 px vertical |
| Card title and card content | 12 px |
| Paragraphs inside a finding | 8 px |
| Label and its control | 4 px |
| Controls in a filter bar | 16 px (the gutter) |

Vertical space is inserted with a spacer element (`st.markdown('<div class="fo-space-8"></div>', unsafe_allow_html=True)`) rather than `st.write("")`, because an empty write still consumes the 16 px block gap and produces untrackable spacing.

### 3.4 Density

One density. Tables have two row heights, because tables are the one place where a reader chooses between scanning and reading.

| Setting | Row height | Where |
|---|---|---|
| Default | 32 px | Any table a reader interacts with |
| Compact | 28 px | Evidence tables inside a findings panel, audit tabs |

A density toggle for the whole UI is rejected, because it doubles the QA surface for a product sold in a fixed number of builds.

### 3.5 Breakpoints

| Breakpoint | Name | What changes |
|---|---|---|
| 1440 px and up | wide | Nothing beyond the container max. Excess is margin. |
| 1024 to 1439 px | desktop | Reference layout. All ratios above hold. |
| 768 to 1023 px | narrow | KPI strip wraps to two rows of two, values drop to `kpi-value-compact`. Chart pair stacks. Filter bar wraps to two rows. Page margin drops to 16 px. Finding figure moves above the claim. Legends move below the chart. |
| 640 to 767 px | Streamlit-stack | Streamlit stacks every column. KPI tiles become full width in one column. Tables scroll horizontally inside their card. |
| under 640 px | phone | Out of scope for the paid build. The page must still render without horizontal scroll and without truncated numbers. Nothing else is promised. |

```css
@media (max-width: 1023px) {
  .block-container { padding-left: var(--fo-space-4); padding-right: var(--fo-space-4); }
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
    min-width: calc(50% - var(--fo-gutter) / 2) !important;
    flex: 1 1 calc(50% - var(--fo-gutter) / 2) !important;
  }
  .fo-kpi__value { font-size: var(--fo-text-2xl); line-height: var(--fo-leading-2xl); letter-spacing: var(--fo-tracking-snug); }
}
@media (max-width: 767px) {
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 100% !important; flex: 1 1 100% !important; }
}
```

Breakpoints test `max-width` on the viewport, not on the container, because Streamlit gives no container query hook and the sidebar, when open, reduces the container by 336 px. The narrow breakpoint therefore also applies whenever the sidebar is open at 1024 to 1359 px. Accept this. It errs toward more room for numbers.

---

## 4. Component specifications

Conventions for every table in this section

- Each component lists its Streamlit primitive first and its CSS hooks second. Hooks are `data-testid` and `data-baseweb` attributes as they exist in Streamlit 1.50.0. They are semi-stable. The version is pinned, so treat any upgrade as a visual regression event.
- "Rest" is the default state. States not listed do not exist for that component.
- Focus is always the same: `outline: var(--fo-border-focus) solid var(--fo-focus); outline-offset: var(--fo-focus-offset)`, because one focus treatment means a keyboard user learns it once.
- Focus is drawn with `:focus-visible`, not `:focus`, because a mouse click should not paint a ring the pointer user did not ask for.
- Disabled is `opacity: 1` with explicit disabled tokens, never `opacity: .5`, because opacity stacks unpredictably on tinted surfaces.
- Transitions run on colour, background and border only, at `--fo-duration-instant`, because transitions on size or position make numbers appear to move.

Shared focus rule, injected once

```css
:where(button, [role="button"], input, select, textarea, [role="tab"], [role="radio"], [role="option"], a, summary, [tabindex]):focus-visible {
  outline: var(--fo-border-focus) solid var(--fo-focus);
  outline-offset: var(--fo-focus-offset);
  box-shadow: none;
}
```

### 4.1 KPI tile and KPI strip

Purpose. A KPI tile states one measured quantity for the selected period and how it moved. The strip is the row of them at the top of the briefing.

Primitive. `JUDGEMENT CALL`: a tile is HTML rendered through `st.markdown(unsafe_allow_html=True)`, not `st.metric`. `st.metric` was rejected because its delta colours are fixed to green-up and red-down with only an `inverse` switch, it cannot host a status icon, and its label cannot be an overline. The strip is `st.columns(n, gap="small")`.

Anatomy

1. Label. `overline`, `ink-secondary`. Max 24 characters.
2. Value. `kpi-value` with optional `.fo-unit`. Max 8 characters including unit.
3. Delta row. A direction glyph (16 px stroke icon `arrow-up-right`, `arrow-down-right` or `minus`), the delta figure in `tabular-sm`, and the comparison basis in `caption`. Max 12 characters for the figure, 20 for the basis.
4. Status mark, optional. A 16 px status icon plus one word, placed right of the label. Present only when the metric has a defined threshold.
5. Footnote, optional. `caption`, `ink-secondary`. One line. Basis or exclusion, such as "excl. 3% missing cost".
6. Sparkline, optional. 96 by 30 px inline SVG right of the value, 13 weekly points, 1.5 px stroke in `--fo-ink-muted`, a 3 px endpoint dot in `--fo-ink` with a 1.5 px `--fo-surface` ring, and a dashed 1 px `--fo-line-control` reference line when the metric has a target or contract. No axis, no labels, no fill, because the tile's value and delta already give the numbers and the sparkline only gives the shape. In Streamlit the SVG is emitted by the same HTML helper as the tile.

Sizes

| Size | Height | Value step | Padding | When |
|---|---|---|---|---|
| Default | auto, min 112 px | `kpi-value` | 16 px 20 px | 4 or fewer tiles in a row at 1024 px and up |
| Compact | auto, min 96 px | `kpi-value-compact` | 12 px 16 px | 5 or more tiles, or the narrow breakpoint |

States

| State | Background | Border | Label | Value | Delta | Notes |
|---|---|---|---|---|---|---|
| Rest | `--fo-surface` | 1px `--fo-line-hairline` | `--fo-ink-secondary` | `--fo-ink` | glyph and figure `--fo-ink-secondary`; if a threshold exists, glyph and figure take `--fo-status-*-ink` | The direction glyph is mandatory so that colour is never the only carrier. |
| Hover | unchanged | unchanged | unchanged | unchanged | unchanged | Tiles are not interactive, so hover changes nothing. A tile that navigates is a link and follows 4.3 tertiary. |
| Focus | not focusable | | | | | |
| Active | none | | | | | |
| Disabled | none | | | | | |
| Loading | `--fo-surface` | hairline | text | `--fo-raised` block 96×40 px in place of the value | hidden | No shimmer, because animation on a number slot implies the number is changing. A plain block. |
| Error | `--fo-surface` | hairline | text | "Not computed" at `label`, `--fo-ink-muted` | hidden | Footnote carries the reason in one sentence. |
| Empty | `--fo-surface` | hairline | text | "No data" at `label`, `--fo-ink-muted` | hidden | Footnote says what would populate it. |

`ink-muted` is permitted for the two placeholder words above because they are not information the reader needs to read at 4.5:1; they mark an absence.

```css
.fo-kpi { background: var(--fo-surface); border: var(--fo-border-hairline) solid var(--fo-line-hairline); border-radius: var(--fo-radius-2); padding: var(--fo-space-4) var(--fo-space-5); min-height: 112px; display: flex; flex-direction: column; gap: var(--fo-space-2); }
.fo-kpi__label { display: flex; align-items: center; gap: var(--fo-space-2); font: var(--fo-weight-medium) var(--fo-text-2xs)/var(--fo-leading-2xs) var(--fo-font-ui); letter-spacing: var(--fo-tracking-wide); text-transform: uppercase; color: var(--fo-ink-secondary); margin: 0; }
.fo-kpi__delta { display: flex; align-items: center; gap: var(--fo-space-1); font: var(--fo-weight-regular) var(--fo-text-xs)/var(--fo-leading-xs) var(--fo-font-mono); font-variant-numeric: tabular-nums; color: var(--fo-ink-secondary); }
.fo-kpi__delta svg { width: var(--fo-icon-sm); height: var(--fo-icon-sm); }
.fo-kpi__delta--good { color: var(--fo-status-good-ink); }
.fo-kpi__delta--warning { color: var(--fo-status-warning-ink); }
.fo-kpi__delta--serious { color: var(--fo-status-serious-ink); }
.fo-kpi__delta--critical { color: var(--fo-status-critical-ink); }
.fo-kpi__basis { font-family: var(--fo-font-ui); color: var(--fo-ink-secondary); margin-left: var(--fo-space-1); }
.fo-kpi__note { font: var(--fo-weight-regular) var(--fo-text-xs)/var(--fo-leading-xs) var(--fo-font-ui); color: var(--fo-ink-secondary); margin: 0; }
.fo-kpi__skeleton { width: 96px; height: 40px; background: var(--fo-raised); border-radius: var(--fo-radius-1); }
.fo-kpi--compact { padding: var(--fo-space-3) var(--fo-space-4); min-height: 96px; }
.fo-kpi--compact .fo-kpi__value { font-size: var(--fo-text-2xl); line-height: var(--fo-leading-2xl); letter-spacing: var(--fo-tracking-snug); }
```

Strip rules

- 3 to 5 tiles. Two is a comparison, not a strip. Six forces compact at desktop and the strip stops reading as a summary.
- All tiles in a strip share one value step, because mixed sizes imply a hierarchy the data does not have.
- Order: money first, then volume, then rate, then time, because the buyer reads cost before anything else.
- The strip has no title. The page title above it is the title.

Accessibility

- The tile root is `<div role="group" aria-label="{label}">`. The value has `aria-label` with the unabbreviated number, because "1.2M" read by a screen reader is not a number.
- Delta direction is in text: `<span class="fo-visually-hidden">up</span>` beside the glyph.
- The status mark contains the word, not only the icon.

Wrong usage. A tile with value "12" and label "Findings". A count of findings is navigation, not a KPI. Use the section header count in 4.2 instead.

### 4.2 Card and section header

Purpose. A card bounds one chart, table or panel. A section header names a group of cards.

Primitive. `st.container(border=True)`, styled through `[data-testid="stVerticalBlockBorderWrapper"]`. Header content is `st.markdown` HTML inside the container.

Anatomy of a card

1. Header row. Title in `h3`, optional count badge (4.10), optional right-aligned actions (a tertiary button or a Chart/Table segmented control).
2. Optional subtitle. `caption`, `ink-secondary`. One line stating the measure, unit and period.
3. Body. The chart, table or content.
4. Optional footer. `caption`. Source line and exclusions.

Anatomy of a section header

1. Title in `h2`.
2. Optional count in a `count` badge.
3. Optional right-aligned action.
4. A hairline below, full width, 16 px above the first card.

Sizes. One size. Card padding 16 px vertical, 20 px horizontal. Radius `--fo-radius-2`.

States

| State | Background | Border | Title | Notes |
|---|---|---|---|---|
| Rest | `--fo-surface` | 1px `--fo-line-hairline` | `--fo-ink` | No shadow. Elevation is not needed for a card that sits in the page. |
| Hover | unchanged | unchanged | unchanged | Cards are not interactive. |
| Focus | not focusable | | | |
| Active | none | | | |
| Disabled | none | | | |
| Loading | `--fo-surface` | hairline | `--fo-ink` | Body shows `st.spinner` text in `caption`. Height held with `min-height` equal to the expected chart height, because a card that collapses and re-expands moves every card below it. |
| Error | `--fo-surface` | hairline | `--fo-ink` | Body shows an inline alert (4.9) of kind `critical`. Title stays. |
| Empty | `--fo-surface` | hairline | `--fo-ink` | Body shows the chart empty state (5.8). |

```css
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--fo-surface);
  border: var(--fo-border-hairline) solid var(--fo-line-hairline);
  border-radius: var(--fo-radius-2);
  padding: var(--fo-space-4) var(--fo-space-5);
}
.fo-card__head  { display: flex; align-items: center; justify-content: space-between; gap: var(--fo-space-3); }
.fo-card__title { font: var(--fo-weight-semibold) var(--fo-text-lg)/var(--fo-leading-lg) var(--fo-font-ui); color: var(--fo-ink); margin: 0; }
.fo-card__sub   { font: var(--fo-weight-regular) var(--fo-text-xs)/var(--fo-leading-xs) var(--fo-font-ui); color: var(--fo-ink-secondary); margin: var(--fo-space-1) 0 var(--fo-space-3); }
.fo-card__foot  { font: var(--fo-weight-regular) var(--fo-text-xs)/var(--fo-leading-xs) var(--fo-font-ui); color: var(--fo-ink-secondary); margin: var(--fo-space-3) 0 0; }
.fo-section { display: flex; align-items: baseline; gap: var(--fo-space-2); padding-bottom: var(--fo-space-2); border-bottom: var(--fo-border-hairline) solid var(--fo-line-hairline); margin: var(--fo-space-8) 0 var(--fo-space-4); }
.fo-section__title { font: var(--fo-weight-medium) var(--fo-text-xl)/var(--fo-leading-xl) var(--fo-font-display); letter-spacing: var(--fo-tracking-snug); color: var(--fo-ink); margin: 0; flex: 1; }
```

Accessibility. Card title is an `<h3>`, section title an `<h2>`, in document order, because screen reader users navigate analytics pages by heading. Never skip a level.

Wrong usage. A card inside a card to separate a chart from its table twin. Nesting doubles the hairlines and halves the content width. Use the segmented control in the card header to switch between chart and table in one body.

### 4.3 Button, three levels

Primitive. `st.button(type="primary" | "secondary" | "tertiary")`, plus `st.download_button` which takes the same `type`. Hooks: `button[data-testid="stBaseButton-primary"]`, `stBaseButton-secondary`, `stBaseButton-tertiary`.

Mapping

| Level | Streamlit type | Job | Per view |
|---|---|---|---|
| Primary | `primary` | The one action the view exists for: "Run reconciliation", "Generate briefing". | At most one visible at a time. |
| Secondary | `secondary` | Actions that change what is shown or export it: "Apply filters", "Export table". | Any number. |
| Tertiary | `tertiary` | Actions that reveal or reset: "View as table", "Reset filters", "Download CSV". | Any number. Renders as text with an underline on hover. |

`JUDGEMENT CALL`: primary is a solid fill with a dark label in dark theme and a white label on a deeper fill in light theme. A single fill and label pair across both themes was rejected because no blue in the accent family hosts a 14 px label at 4.5:1 on both a near-black and a white surrounding while staying at 3:1 against that surrounding. The two fills share hue; only lightness differs.

Sizes

| Size | Height | Padding | Label step | Icon |
|---|---|---|---|---|
| Default | 36 px | 0 16 px | `label` 14/20 | 16 px, 8 px gap |
| Small | 28 px | 0 12 px | `label-sm` 12/16 | 16 px, 6 px gap |

Small is reached by placing the button inside a container that carries the class hook `.fo-compact` and scoping the CSS, because `st.button` has no size argument.

States, primary

| State | Fill | Border | Label | Notes |
|---|---|---|---|---|
| Rest | `--fo-action-primary-fill` | none | `--fo-action-primary-ink` | |
| Hover | `--fo-action-primary-fill-hover` | none | same | |
| Focus | rest fill | none | same | Shared focus ring. |
| Active | `--fo-action-primary-fill-active` | none | same | |
| Disabled | `--fo-raised` | 1px `--fo-line-hairline` | `--fo-ink-muted` | `cursor: not-allowed`. The reason must be visible nearby in `caption`. |
| Loading | rest fill | none | label replaced by a 16 px stroke spinner and the word "Working" | Width held to the rest width, because a button that shrinks moves its neighbours. Streamlit disables the button while a callback runs; set the label from `st.session_state` before the run. |

States, secondary

| State | Fill | Border | Label |
|---|---|---|---|
| Rest | transparent | 1px `--fo-line-control` | `--fo-ink` |
| Hover | `--fo-surface-hover` | 1px `--fo-line-strong` | `--fo-ink` |
| Focus | transparent | 1px `--fo-line-control` | `--fo-ink` |
| Active | `--fo-surface-pressed` | 1px `--fo-line-strong` | `--fo-ink` |
| Disabled | transparent | 1px `--fo-line-hairline` | `--fo-ink-muted` |
| Loading | as rest | | spinner and "Working" |

States, tertiary

| State | Fill | Border | Label |
|---|---|---|---|
| Rest | transparent | none | `--fo-ink-link` |
| Hover | transparent | none | `--fo-ink-link`, underline 1px, offset 3px |
| Focus | transparent | none | `--fo-ink-link` |
| Active | transparent | none | `--fo-accent-active` |
| Disabled | transparent | none | `--fo-ink-muted` |

```css
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-secondary"],
button[data-testid="stBaseButton-tertiary"] {
  min-height: var(--fo-control-height); height: var(--fo-control-height);
  padding: 0 var(--fo-space-4); border-radius: var(--fo-radius-1);
  font: var(--fo-weight-medium) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui);
  transition: background-color var(--fo-duration-instant) var(--fo-ease-standard),
              border-color var(--fo-duration-instant) var(--fo-ease-standard),
              color var(--fo-duration-instant) var(--fo-ease-standard);
}
button[data-testid="stBaseButton-primary"] { background: var(--fo-action-primary-fill); color: var(--fo-action-primary-ink); border: none; }
button[data-testid="stBaseButton-primary"]:hover { background: var(--fo-action-primary-fill-hover); }
button[data-testid="stBaseButton-primary"]:active { background: var(--fo-action-primary-fill-active); }
button[data-testid="stBaseButton-primary"]:disabled { background: var(--fo-raised); color: var(--fo-ink-muted); border: var(--fo-border-control) solid var(--fo-line-hairline); cursor: not-allowed; }
button[data-testid="stBaseButton-secondary"] { background: transparent; color: var(--fo-ink); border: var(--fo-border-control) solid var(--fo-line-control); }
button[data-testid="stBaseButton-secondary"]:hover { background: var(--fo-surface-hover); border-color: var(--fo-line-strong); }
button[data-testid="stBaseButton-secondary"]:active { background: var(--fo-surface-pressed); }
button[data-testid="stBaseButton-secondary"]:disabled { color: var(--fo-ink-muted); border-color: var(--fo-line-hairline); cursor: not-allowed; }
button[data-testid="stBaseButton-tertiary"] { background: transparent; color: var(--fo-ink-link); border: none; padding: 0 var(--fo-space-2); }
button[data-testid="stBaseButton-tertiary"]:hover { text-decoration: underline; text-underline-offset: 3px; }
button[data-testid="stBaseButton-tertiary"]:active { color: var(--fo-accent-active); }
button[data-testid="stBaseButton-tertiary"]:disabled { color: var(--fo-ink-muted); text-decoration: none; cursor: not-allowed; }
.fo-compact button[data-testid^="stBaseButton-"] { height: var(--fo-control-height-sm); min-height: var(--fo-control-height-sm); padding: 0 var(--fo-space-3); font-size: var(--fo-text-xs); line-height: var(--fo-leading-xs); }
```

Accessibility

- Label is a verb phrase in sentence case, max 20 characters, because a screen reader announces "button" after it and a long label buries the verb.
- Icon-only buttons are not used, because `st.button` cannot take an `aria-label` separate from its visible label. If an icon is wanted, the label stays visible beside it.
- Disabled buttons keep 3:1 between `ink-muted` and `raised` (3.66 dark, 3.50 light) so the reader can still read what is unavailable.

Wrong usage. Two primary buttons side by side: "Generate briefing" and "Export PDF". Export is secondary. If both are primary, neither is.

### 4.4 Input, select, multiselect chip, date range

Primitives. `st.text_input`, `st.number_input`, `st.selectbox`, `st.multiselect`, `st.date_input(value=(start, end))`. Hooks: `[data-testid="stTextInput"]`, `[data-testid="stNumberInput"]`, `[data-testid="stSelectbox"]`, `[data-testid="stMultiSelect"]`, `[data-testid="stDateInput"]`, and inside them BaseWeb's `[data-baseweb="input"]`, `[data-baseweb="select"]`, `[data-baseweb="tag"]`, `[data-baseweb="popover"]`, `[data-baseweb="menu"]`, `[data-baseweb="calendar"]`.

Boundary contrast. `--fo-line-control` reads 3.09:1 on dark `plane` and 3.02:1 on light `plane`, but 2.91:1 and 2.97:1 on `surface`. The rule that closes the gap: controls sit on `plane` (filter bar, sidebar) or inside a `.fo-fieldset` that paints `raised` with the control itself filled `surface`, so the boundary always meets a background it clears. `JUDGEMENT CALL`: a darker boundary that clears 3:1 on every surface was rejected because at 3.9:1 (`ink-muted`) every input outline competes with the numbers around it.

Shared anatomy

1. Label. `label` step, `ink`, 4 px above the control. Required fields carry the word "required" in `caption`, not an asterisk, because an asterisk is a learned symbol and colour is often its only emphasis.
2. Control. 36 px high, radius `--fo-radius-1`, 1px `--fo-line-control` border, `raised` fill on plane, `surface` fill inside a fieldset.
3. Value text. `body`, `ink`. Placeholder `body`, `ink-secondary`.
4. Helper or error line. `caption`, 4 px below. Error line is `--fo-status-critical-ink` with a 16 px `alert-circle` icon and starts with the field name.

Shared states

| State | Fill | Border | Text | Notes |
|---|---|---|---|---|
| Rest | `--fo-raised` on plane, `--fo-surface` in fieldset | 1px `--fo-line-control` | `--fo-ink`; placeholder `--fo-ink-secondary` | |
| Hover | same | 1px `--fo-line-strong` | same | |
| Focus | same | 1px `--fo-accent` plus the shared ring | same | The inner border also turns accent so focus stays visible when the ring is clipped by a Streamlit container. |
| Active (menu open) | same | 1px `--fo-accent` | same | Chevron rotates 180° over `--fo-duration-short`. |
| Disabled | `--fo-surface` | 1px `--fo-line-hairline` | `--fo-ink-muted` | |
| Loading | rest | rest | | Not a state inputs have. Options loading is shown by disabling the select with placeholder "Loading carriers". |
| Error | rest | 1px `--fo-status-critical-ink` | `--fo-ink` | Error line below. Icon and text, never the border alone. |
| Empty (select with no options) | disabled appearance | | placeholder "No carriers in this period" | |

Select menu (popover)

| Part | Token |
|---|---|
| Menu surface | `--fo-raised`, `--fo-shadow-1`, radius `--fo-radius-2`, 4 px padding |
| Option rest | transparent, `body`, `--fo-ink`, height 32 px, padding 0 12 px |
| Option hover | `--fo-surface-hover` |
| Option selected | `--fo-accent-selection` fill, `--fo-ink`, 16 px `check` icon right-aligned in `--fo-ink-link` |
| Option focused (keyboard) | `--fo-surface-hover` plus 2px inset outline `--fo-focus` |
| Group heading | `overline`, `--fo-ink-secondary` |

Multiselect chip (`[data-baseweb="tag"]`)

| State | Fill | Border | Text | Remove icon |
|---|---|---|---|---|
| Rest | `--fo-accent-tint` | 1px `--fo-line-hairline` | `label-sm`, `--fo-ink` | 16 px `x`, `--fo-ink-secondary` |
| Hover | `--fo-accent-selection` | same | same | `--fo-ink` |
| Focus | rest | | | ring on the remove control |
| Disabled | `--fo-raised` | hairline | `--fo-ink-muted` | hidden |

- Chips are 24 px high, radius `--fo-radius-1`, max 24 characters with ellipsis.
- Chips never take a series colour, because the filter and the chart are different channels and a blue chip beside a blue bar claims a link that is not there.
- `STREAMLIT LIMIT`: a "+n more" collapse after five chips is not native; `st.multiselect` shows every chip. Nearest alternative: `max-height: 36px; overflow: hidden` on the value container, plus a `caption` under the control that reads "n carriers selected". Ship that.

Date range control

- `st.date_input` with a tuple value renders one field and a two-month calendar popover.
- Field text reads `2026-06-01 to 2026-08-31`, ISO, with the word "to", because ISO is unambiguous across the locales the buyer works in and a dash between dates is the one dash nobody agrees on.
- Calendar popover uses the menu tokens. Selected day: `--fo-accent-selection` fill, `--fo-ink`. Range fill between endpoints: `--fo-accent-tint`. Today: 1px `--fo-line-strong` ring. Disabled day (outside data): `--fo-ink-muted`.
- Presets ("Last 4 weeks", "Last quarter", "Year to date") are a segmented control (4.5) beside the field, not inside the popover, because Streamlit cannot inject controls into the calendar.
- `STREAMLIT LIMIT`: the field cannot show the range in two separate boxes and cannot change its display format from Streamlit's `format` options (`YYYY/MM/DD`, `DD/MM/YYYY`, `MM/DD/YYYY`). Use `format="YYYY/MM/DD"`, the closest to ISO, and state the ISO range in a `caption` under the field. One field is the buildable form.

```css
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stNumberInput"] [data-baseweb="input"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div,
[data-testid="stDateInput"] [data-baseweb="input"] {
  background: var(--fo-raised); border: var(--fo-border-control) solid var(--fo-line-control);
  border-radius: var(--fo-radius-1); min-height: var(--fo-control-height);
  font: var(--fo-weight-body) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); color: var(--fo-ink);
  transition: border-color var(--fo-duration-instant) var(--fo-ease-standard);
}
.fo-fieldset { background: var(--fo-raised); border-radius: var(--fo-radius-2); padding: var(--fo-space-4); }
.fo-fieldset [data-baseweb="input"], .fo-fieldset [data-baseweb="select"] > div { background: var(--fo-surface); }
[data-baseweb="input"]:hover, [data-baseweb="select"] > div:hover { border-color: var(--fo-line-strong); }
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within { border-color: var(--fo-accent); }
[data-baseweb="input"] input::placeholder { color: var(--fo-ink-secondary); opacity: 1; }
[data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="calendar"] { background: var(--fo-raised); box-shadow: var(--fo-shadow-1); border-radius: var(--fo-radius-2); }
[data-baseweb="menu"] [role="option"] { min-height: 32px; color: var(--fo-ink); }
[data-baseweb="menu"] [role="option"]:hover { background: var(--fo-surface-hover); }
[data-baseweb="menu"] [role="option"][aria-selected="true"] { background: var(--fo-accent-selection); }
[data-baseweb="tag"] { background: var(--fo-accent-tint); border: var(--fo-border-hairline) solid var(--fo-line-hairline); border-radius: var(--fo-radius-1); color: var(--fo-ink); height: 24px; font-size: var(--fo-text-xs); }
[data-baseweb="tag"]:hover { background: var(--fo-accent-selection); }
[data-testid="stMultiSelect"] [data-baseweb="select"] > div > div:first-child { max-height: 36px; overflow: hidden; }
```

Accessibility. Every control has a visible label (`label_visibility="visible"`), because Streamlit's collapsed label removes the accessible name too. Error text is tied by proximity and starts with the field name, because Streamlit gives no `aria-describedby` hook.

Wrong usage. A multiselect of carriers where each chip is painted in the carrier's series colour. The chips would re-colour when the selection changes, and the rule that colour follows the entity would be true in the chart and false in the filter.

### 4.5 Radio and segmented control

Primitives. `st.radio` for a vertical list of 2 to 5 exclusive options that need explanation. `st.segmented_control` for 2 to 4 exclusive options with one-word labels shown inline, such as Chart/Table or period presets. Hooks: `[data-testid="stRadio"]`, `[data-testid="stSegmentedControl"]`, `[data-testid="stSegmentedControl"] button`.

Radio anatomy. 16 px circle indicator, 8 px gap, `body` label, optional `caption` description on a second line. Row height 28 px, 4 px between rows.

Radio states

| State | Indicator border | Indicator fill | Dot | Label |
|---|---|---|---|---|
| Rest, unselected | 1px `--fo-line-control` | `--fo-raised` | none | `--fo-ink` |
| Rest, selected | 1px `--fo-accent` | `--fo-raised` | 8 px `--fo-accent` | `--fo-ink` |
| Hover | 1px `--fo-line-strong` (unselected) | `--fo-surface-hover` | | |
| Focus | as rest | | | ring on the indicator |
| Active | 1px `--fo-accent` | `--fo-accent-tint` | | |
| Disabled | 1px `--fo-line-hairline` | `--fo-surface` | `--fo-ink-muted` if selected | `--fo-ink-muted` |
| Error | group-level error line below in `--fo-status-critical-ink` with icon | | | |

Segmented control anatomy. A 36 px track (28 px small) with 1px `--fo-line-control` border, radius `--fo-radius-1`, containing equal-width segments with `label` text and optional 16 px icon left of the text.

Segmented states

| State | Segment fill | Segment text | Notes |
|---|---|---|---|
| Rest, unselected | transparent | `--fo-ink-secondary` | |
| Rest, selected | `--fo-raised` | `--fo-ink` | Plus a 2 px bottom inset line in `--fo-accent`, because `raised` on `surface` is 1.08:1 and the selected state must not depend on that step alone. |
| Hover, unselected | `--fo-surface-hover` | `--fo-ink` | |
| Focus | as rest | | ring on the segment |
| Active | `--fo-surface-pressed` | `--fo-ink` | |
| Disabled | transparent | `--fo-ink-muted` | whole control |

- Selection is required and non-null (`selection_mode="single"`, `default` set), because a segmented control with nothing selected is a row of buttons.
- Segments have 1px `--fo-line-hairline` dividers between them, because equal-width text without dividers reads as one label.

```css
[data-testid="stSegmentedControl"] > div { border: var(--fo-border-control) solid var(--fo-line-control); border-radius: var(--fo-radius-1); background: transparent; padding: 0; gap: 0; overflow: hidden; }
[data-testid="stSegmentedControl"] button { height: calc(var(--fo-control-height) - 2px); border: none; border-radius: 0; color: var(--fo-ink-secondary); background: transparent; font: var(--fo-weight-medium) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); box-shadow: none; padding: 0 var(--fo-space-3); }
[data-testid="stSegmentedControl"] button + button { border-left: var(--fo-border-hairline) solid var(--fo-line-hairline); }
[data-testid="stSegmentedControl"] button:hover { background: var(--fo-surface-hover); color: var(--fo-ink); }
[data-testid="stSegmentedControl"] button[aria-checked="true"],
[data-testid="stSegmentedControl"] button[kind="segmented_controlActive"] { background: var(--fo-raised); color: var(--fo-ink); box-shadow: inset 0 -2px 0 0 var(--fo-accent); }
```

Accessibility. Streamlit renders the segmented control as a button group. It is keyboard-reachable per segment with Tab, not with arrow keys as a true radiogroup would be. Accept this and keep segments to 4, because Tab through 4 is tolerable and through 8 is not. `st.radio` renders a proper radiogroup with arrow-key movement.

Wrong usage. A segmented control with labels "Cost per shipment", "Late delivery rate", "Reconciled volume". The labels wrap and the control is wider than the chart it switches. Use `st.radio` horizontal, or tabs (4.6).

### 4.6 Tab bar

Primitive. `st.tabs([...])`. Hooks: `[data-testid="stTabs"]`, `[data-baseweb="tab-list"]`, `[data-baseweb="tab"]`, `[data-baseweb="tab-highlight"]`, `[data-baseweb="tab-border"]`, `[data-baseweb="tab-panel"]`.

Anatomy. A horizontal list of tab labels in `label`, 40 px high, with a 2 px active indicator on the bottom edge, sitting on a full-width hairline.

States

| State | Text | Indicator | Fill |
|---|---|---|---|
| Rest, inactive | `--fo-ink-secondary` | none | transparent |
| Rest, active | `--fo-ink` | 2px `--fo-accent` | transparent |
| Hover, inactive | `--fo-ink` | 2px `--fo-line-strong` | transparent |
| Focus | as rest | as rest | ring on the tab |
| Active (pressed) | `--fo-ink` | 2px `--fo-accent` | `--fo-surface-hover` |
| Disabled | not supported by `st.tabs` | | Omit the tab rather than showing a dead one. |
| Loading | tab panel shows `st.spinner` | | |
| Empty | tab panel shows the empty state; the tab label carries "(0)" | | |

- Tabs carry a count in parentheses when the content is a list: "Lanes (14)". The count is text, not a badge, because a badge inside a tab looks like a notification.
- Max 6 tabs and max 16 characters per label, because Streamlit's tab list scrolls horizontally past that and a hidden tab is a lost tab.
- Tabs do not survive a rerun unless the active index is stored in `st.session_state`. Store it.

```css
[data-baseweb="tab-list"] { gap: var(--fo-space-6); border-bottom: var(--fo-border-hairline) solid var(--fo-line-hairline); }
[data-baseweb="tab"] { height: 40px; padding: 0; background: transparent; color: var(--fo-ink-secondary); font: var(--fo-weight-medium) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); }
[data-baseweb="tab"]:hover { color: var(--fo-ink); box-shadow: inset 0 -2px 0 0 var(--fo-line-strong); }
[data-baseweb="tab"][aria-selected="true"] { color: var(--fo-ink); }
[data-baseweb="tab-highlight"] { background: var(--fo-accent); height: 2px; }
[data-baseweb="tab-border"] { display: none; }   /* the list draws its own hairline */
[data-baseweb="tab-panel"] { padding-top: var(--fo-space-4); }
```

Accessibility. BaseWeb tabs implement `role="tablist"` with arrow-key movement. Do not override the keyboard handling. The active tab is announced by `aria-selected` and is also the only tab in `ink` with an indicator, so the state has two visual carriers.

Wrong usage. Tabs "Dark" and "Light" to switch theme. Tabs switch content of equal kind. Theme is a setting and belongs in the sidebar as a segmented control.

### 4.7 Table

Two renderers, one visual language.

| Renderer | Use when | Gives up |
|---|---|---|
| HTML table via `st.markdown(df.to_html(...))` with class `fo-table` | 60 rows or fewer, no user sorting needed, the table must match tokens exactly: evidence tables, KPI breakdowns, chart twins | Sorting, column resize, virtual scroll |
| `st.dataframe` with `column_config` | More than 60 rows, or the user must sort, search or resize: audit tab, full shipment log | Mono numerals, exact hairline control, row height below 35 px |

`STREAMLIT LIMIT`: `st.dataframe` renders to a canvas. CSS cannot reach its cells. It takes fonts and colours only from `config.toml`. Its numeric cells use the UI font, not Plex Mono, and its minimum row height is 35 px. Nearest alternative is the HTML renderer for every table where the tokens matter, which is every table a finding points at.

`JUDGEMENT CALL`: hairline, not zebra. Zebra striping was rejected because it adds a second rhythm the eye has to discount before reading the numbers, and because `st.dataframe` cannot do it, which would make the two renderers look like two products.

Anatomy

1. Optional title row. `h4` and a `caption` unit statement, 8 px below.
2. Header row. `label` for text columns; `tabular` for numeric column headers with the unit in parentheses. Fill `--fo-raised`. Height 32 px. Sticky when the table scrolls.
3. Body rows. 32 px default, 28 px compact. Hairline between rows.
4. Optional totals row. `tabular-strong`, rule above in `--fo-line-strong`.
5. Optional footer. `caption`: row count, exclusions, source.

Column rules

| Content | Font | Align | Format |
|---|---|---|---|
| Text, identifiers | `body` | left | Truncate with ellipsis at the column width, full value in `title`. |
| Integers, money, percentages, durations | `tabular` | right | Section 6. Same decimal count within a column. |
| Dates | `tabular` | left | ISO. Left because dates are read as labels, not magnitudes. |
| Status | badge (4.10) | left | Icon plus word. |
| Delta | `tabular` | right | Sign always shown: minus U+2212, plus U+002B. |

States

| State | Row fill | Border | Text | Notes |
|---|---|---|---|---|
| Rest | `--fo-surface` | 1px `--fo-line-hairline` between rows | `--fo-ink` | |
| Hover (row) | `--fo-surface-hover` | | | HTML renderer only. Hover on a row aids reading across, so it applies even though rows are not interactive. |
| Focus | HTML tables are not focusable. `st.dataframe` receives the shared ring on its wrapper. | | | |
| Active / selected | `--fo-accent-selection` | | `--fo-ink` | `st.dataframe` with `on_select` only. |
| Cited (the cell a finding names) | cell fill `--fo-accent-tint`, text `tabular-strong` | | | Never a status colour, because the finding's severity is already stated in the finding. |
| Disabled | not a table state | | | |
| Loading | header rendered; body replaced by three rows of `--fo-raised` blocks | | | Height held. |
| Error | header rendered; body shows an inline alert `critical` spanning all columns | | | |
| Empty | header rendered; body one row: "No rows match the current filters." in `body`, `--fo-ink-secondary`, plus a tertiary "Reset filters" | | | The header stays so the reader knows what would have been shown. |

```css
.fo-table-wrap { overflow-x: auto; max-height: 480px; overflow-y: auto; border: var(--fo-border-hairline) solid var(--fo-line-hairline); border-radius: var(--fo-radius-1); }
.fo-table { width: 100%; border-collapse: collapse; font: var(--fo-weight-body) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); color: var(--fo-ink); }
.fo-table th { position: sticky; top: 0; z-index: 1; background: var(--fo-raised); color: var(--fo-ink-secondary); font-weight: var(--fo-weight-medium); text-align: left; height: var(--fo-row-height); padding: 0 var(--fo-space-3); border-bottom: var(--fo-border-hairline) solid var(--fo-line-hairline); white-space: nowrap; }
.fo-table td { height: var(--fo-row-height); padding: 0 var(--fo-space-3); border-bottom: var(--fo-border-hairline) solid var(--fo-line-hairline); vertical-align: middle; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fo-table tbody tr:hover td { background: var(--fo-surface-hover); }
.fo-table .fo-num { font-family: var(--fo-font-mono); font-size: var(--fo-text-sm); font-variant-numeric: tabular-nums lining-nums; text-align: right; }
.fo-table tfoot td { font-weight: var(--fo-weight-medium); border-top: var(--fo-border-hairline) solid var(--fo-line-strong); border-bottom: none; }
.fo-table--compact th, .fo-table--compact td { height: var(--fo-row-height-compact); }
.fo-table td.fo-cite { background: var(--fo-accent-tint); font-weight: var(--fo-weight-medium); }
.fo-table__empty td { color: var(--fo-ink-secondary); text-align: center; height: 72px; }
```

`st.dataframe` configuration for the other renderer

```python
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    height=min(35 * (len(df) + 1) + 2, 560),
    column_config={
        "cost_eur":  st.column_config.NumberColumn("Cost (EUR)", format="%d"),
        "late_rate": st.column_config.NumberColumn("Late (%)", format="%.1f"),
        "ship_date": st.column_config.DateColumn("Shipped", format="YYYY-MM-DD"),
    },
)
```

Accessibility

- HTML tables use `<th scope="col">` and a `<caption>` (visually hidden if a title row exists), because a screen reader announces column context from `scope`.
- `st.dataframe` exposes a grid role from Glide. Its keyboard model is Glide's. Do not fight it.
- Truncated text keeps the full value in `title` and in the CSV export.

Wrong usage. A table of six carriers with cost, volume and late rate rendered with `st.dataframe`. Six rows need no sorting and a finding cites a cell in it. Render it as `.fo-table` so the cited cell can be highlighted and the numbers align in mono.

### 4.8 File dropzone

Primitive. `st.file_uploader(accept_multiple_files=True, type=["csv", "xlsx"])`. Hooks: `[data-testid="stFileUploader"]`, `[data-testid="stFileUploaderDropzone"]`, `[data-testid="stFileUploaderDropzoneInstructions"]`, `[data-testid="stFileUploaderFile"]`, `[data-testid="stFileUploaderDeleteBtn"]`.

Anatomy

1. Label. `label`, above.
2. Zone. Min height 120 px, 1px dashed `--fo-line-control` border, radius `--fo-radius-2`, `--fo-raised` fill.
3. Instruction. 24 px `upload` icon in `--fo-ink-secondary`, then `body` "Drop shipment exports here or browse", then `caption` "CSV or XLSX, up to 200 MB each. Carrier, TMS and ERP exports are reconciled together."
4. Browse button. Secondary, small.
5. File list. One row per file: 16 px `file` icon, name in `body`, size in `tabular-sm` and `--fo-ink-secondary`, remove control (tertiary, 16 px `x` with visible label "Remove").
6. Processing panel. `st.status("Reconciling 3 files", expanded=True)` below the zone, containing `caption` steps.

States

| State | Fill | Border | Icon and text | Notes |
|---|---|---|---|---|
| Empty (rest) | `--fo-raised` | 1px dashed `--fo-line-control` | icon `--fo-ink-secondary`; text `--fo-ink` and `--fo-ink-secondary` | |
| Hover, and drag-over | `--fo-accent-tint` | 1px dashed `--fo-accent` | icon `--fo-ink-link` | `STREAMLIT LIMIT`: the drag-over state has no stable hook in 1.50, so hover and drag-over share this appearance. |
| Focus | rest | rest | | ring on the browse button, the only focusable element |
| Active (files present) | rest | 1px solid `--fo-line-hairline` | zone shrinks to 72 px and reads "Add more files" | File list below. |
| Disabled | `--fo-surface` | 1px dashed `--fo-line-hairline` | `--fo-ink-muted` | While a reconciliation runs. |
| Processing | rest | rest | | `st.status` panel: label `h4`, steps in `caption`; each finished step gets a 16 px `check` icon in `--fo-status-good-ink`. Step text names the file and the count: "Nordfrakt_Q3.csv: 4 812 rows, 3 columns renamed". |
| Error | `--fo-status-critical-tint` | 1px solid `--fo-status-critical-ink` | 16 px `alert-octagon` in `--fo-status-critical-ink` | Text in `body`, `--fo-ink`, names the file and the reason: "Meridian_Aug.xlsx: no date column recognised. Expected one of ship_date, pickup, delivered." Then a tertiary "Remove file". |
| Loading (upload in flight) | rest | rest | Streamlit's progress bar recoloured to `--fo-accent` | |

```css
[data-testid="stFileUploaderDropzone"] { background: var(--fo-raised); border: var(--fo-border-control) dashed var(--fo-line-control); border-radius: var(--fo-radius-2); min-height: 120px; padding: var(--fo-space-5); transition: background-color var(--fo-duration-instant) var(--fo-ease-standard), border-color var(--fo-duration-instant) var(--fo-ease-standard); }
[data-testid="stFileUploaderDropzone"]:hover { background: var(--fo-accent-tint); border-color: var(--fo-accent); }
[data-testid="stFileUploaderDropzoneInstructions"] span { color: var(--fo-ink); font: var(--fo-weight-body) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); }
[data-testid="stFileUploaderDropzoneInstructions"] small { color: var(--fo-ink-secondary); font-size: var(--fo-text-xs); }
[data-testid="stFileUploaderFile"] { height: var(--fo-row-height); border-bottom: var(--fo-border-hairline) solid var(--fo-line-hairline); }
[data-testid="stFileUploader"] [data-testid="stProgressBar"] > div > div { background: var(--fo-accent); }
.fo-dropzone--error [data-testid="stFileUploaderDropzone"] { background: var(--fo-status-critical-tint); border: var(--fo-border-control) solid var(--fo-status-critical-ink); }
```

Accessibility. The browse button carries the label "Browse files". Processing progress is announced because `st.status` updates a live region. Error text sits in the document flow directly under the zone, not in a toast, because a toast disappears before a screen reader user reaches it.

Wrong usage. A dropzone that accepts a file and immediately renders the dashboard with no processing panel. The buyer needs to see that 4 812 rows became 4 790 and why, because that trace is what makes the numbers checkable.

### 4.9 Inline alert and toast

Inline alert primitive. `JUDGEMENT CALL`: HTML through `st.markdown`, not `st.info` / `st.warning` / `st.error` / `st.success`, because Streamlit's alerts cannot take a stroke SVG icon and their four kinds cover only four of the five levels (there is no `serious`). The rejected path is not unusable: with the semantic colour keys in 1.3, `st.error` lands on the critical tint and ink, `st.warning` on warning, `st.success` on good and `st.info` on accent, so a stray Streamlit alert from a library or an uncaught exception still reads as part of the system. It lacks only the icon and the `serious` level. Use it for uncaught exceptions; use the HTML alert for everything the product itself says.

Anatomy

1. Icon, 20 px, in `--fo-status-*-ink`, top-aligned to the first text line.
2. Title, `h4`, `--fo-ink`. Max 48 characters. Starts with the status word for non-neutral kinds: "Warning: 3% of rows lack a cost".
3. Body, `body`, `--fo-ink`. Max 200 characters. States the consequence and what the reader can do.
4. Optional action, a tertiary button, on its own line below the body.
5. Optional dismiss, 16 px `x` with visible label "Dismiss", only when the alert is neutral and the reader loses nothing by dismissing it.

Mapping

| Kind | Icon | Ink | Tint | Border | When |
|---|---|---|---|---|---|
| neutral | `info` | `--fo-status-neutral-ink` | `--fo-status-neutral-tint` | 1px `--fo-line-hairline` | Context, definitions, "Sample data loaded". |
| good | `check-circle` | `--fo-status-good-ink` | `--fo-status-good-tint` | 1px `--fo-status-good-ink` | Reconciliation complete with no exclusions. |
| warning | `alert-triangle` | `--fo-status-warning-ink` | `--fo-status-warning-tint` | 1px `--fo-status-warning-ink` | Data is usable with a stated caveat. |
| serious | `alert-circle` | `--fo-status-serious-ink` | `--fo-status-serious-tint` | 1px `--fo-status-serious-ink` | A figure on the page is affected and should be read with care. |
| critical | `alert-octagon` | `--fo-status-critical-ink` | `--fo-status-critical-tint` | 1px `--fo-status-critical-ink` | Something failed and a figure could not be produced. |

The border runs on all four sides at 1px, because a coloured left edge alone is a house rule violation and a full border is also what makes the alert readable as a bounded object.

States

| State | Notes |
|---|---|
| Rest | As mapped. |
| Hover | No change. Alerts are not interactive; their action button is. |
| Focus | On the action or dismiss control only. |
| Dismissed | Removed from the flow with no animation, because motion on removal draws the eye to a thing that is gone. |
| Loading | Not a state. A running process uses `st.status`, not an alert. |

```css
.fo-alert { display: grid; grid-template-columns: var(--fo-icon-md) 1fr; gap: var(--fo-space-3); padding: var(--fo-space-3) var(--fo-space-4); border-radius: var(--fo-radius-2); border: var(--fo-border-hairline) solid; align-items: start; }
.fo-alert svg { width: var(--fo-icon-md); height: var(--fo-icon-md); margin-top: 0; }
.fo-alert__title { font: var(--fo-weight-semibold) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); color: var(--fo-ink); margin: 0; }
.fo-alert__body  { font: var(--fo-weight-body) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); color: var(--fo-ink); margin: var(--fo-space-1) 0 0; }
.fo-alert--neutral  { background: var(--fo-status-neutral-tint);  border-color: var(--fo-line-hairline); }         .fo-alert--neutral  svg { color: var(--fo-status-neutral-ink); }
.fo-alert--good     { background: var(--fo-status-good-tint);     border-color: var(--fo-status-good-ink); }     .fo-alert--good     svg { color: var(--fo-status-good-ink); }
.fo-alert--warning  { background: var(--fo-status-warning-tint);  border-color: var(--fo-status-warning-ink); }  .fo-alert--warning  svg { color: var(--fo-status-warning-ink); }
.fo-alert--serious  { background: var(--fo-status-serious-tint);  border-color: var(--fo-status-serious-ink); }  .fo-alert--serious  svg { color: var(--fo-status-serious-ink); }
.fo-alert--critical { background: var(--fo-status-critical-tint); border-color: var(--fo-status-critical-ink); } .fo-alert--critical svg { color: var(--fo-status-critical-ink); }
```

Toast primitive. `st.toast(body)`. Hook: `[data-testid="stToast"]`.

`STREAMLIT LIMIT`: `st.toast` takes markdown without HTML and an `icon` argument that accepts only emoji or Material Symbols. Neither is permitted. Its kind cannot be targeted in CSS. Therefore toasts are neutral only, carry no icon, and never carry status. The outcome is in the first word of the text: "Done. Table exported as CSV." Anything that is a warning or worse is an inline alert next to its cause, because a toast vanishes after four seconds and a problem should not.

Toast spec

| Part | Token |
|---|---|
| Surface | `--fo-raised`, `--fo-shadow-2`, radius `--fo-radius-2`, padding 12 px 16 px, max width 360 px |
| Text | `body`, `--fo-ink`, max 60 characters |
| Position | bottom right, Streamlit default |
| Duration | 4 s, Streamlit default, not configurable |
| Motion | Streamlit's own slide-in. Not tunable. The only motion in the system not under token control. |

```css
[data-testid="stToast"] { background: var(--fo-raised); color: var(--fo-ink); box-shadow: var(--fo-shadow-2); border-radius: var(--fo-radius-2); font: var(--fo-weight-body) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); }
```

Accessibility. Inline alerts of kind serious and critical carry `role="alert"` so they are announced on insertion. Neutral, good and warning carry `role="status"`. Toasts are announced by Streamlit's own live region.

Wrong usage. `st.toast("Error: file could not be parsed")`. The reader looks up from the dropzone to find the toast already gone. Use the dropzone error state.

### 4.10 Badge and pill

Two shapes with two jobs.

| Component | Shape | Job | Interactive |
|---|---|---|---|
| Badge | radius `--fo-radius-1`, 20 px high | Status or category of the thing it sits beside: "Critical", "Reconciled", "Estimated" | Never |
| Pill | radius `--fo-radius-pill`, 24 px high | A toggleable value from a small visible set: a lane, a carrier | Yes |

Primitive. HTML through `st.markdown` for badges. `st.pills(selection_mode="multi")` for interactive pills. Hooks: `[data-testid="stPills"] button`. `st.badge` and the `:red-badge[...]` markdown directive are second choice: with the semantic colour keys in 1.3 their colours do land on the status tints and inks, but they cannot carry the stroke icon and `st.badge` accepts only emoji or Material icons, so a status badge built with them would carry meaning by colour and word alone. Acceptable inside `st.dataframe` cells and tab labels, where HTML cannot reach; the HTML badge everywhere else.

Badge anatomy. Optional 12 px status icon, 4 px gap, `label-sm` text in `--fo-ink`, padding 0 8 px, 1px border. Max 12 characters.

Badge variants

| Variant | Fill | Border | Icon |
|---|---|---|---|
| neutral | `--fo-status-neutral-tint` | `--fo-line-hairline` | none |
| good | `--fo-status-good-tint` | `--fo-status-good-ink` | `check-circle` in `--fo-status-good-ink` |
| warning | `--fo-status-warning-tint` | `--fo-status-warning-ink` | `alert-triangle` |
| serious | `--fo-status-serious-tint` | `--fo-status-serious-ink` | `alert-circle` |
| critical | `--fo-status-critical-tint` | `--fo-status-critical-ink` | `alert-octagon` |
| count | `--fo-raised` | none | none; `tabular-sm` text |

Badges have no hover, focus, active, disabled or loading state, because they are text. A badge that responds to a pointer is a pill.

Pill states

| State | Fill | Border | Text |
|---|---|---|---|
| Rest, unselected | transparent | 1px `--fo-line-control` | `--fo-ink` |
| Rest, selected | `--fo-accent-selection` | 1px `--fo-accent` | `--fo-ink`, with a 16 px `check` left of the text |
| Hover | `--fo-surface-hover` | 1px `--fo-line-strong` | `--fo-ink` |
| Focus | as rest | | ring |
| Active | `--fo-surface-pressed` | | |
| Disabled | transparent | 1px `--fo-line-hairline` | `--fo-ink-muted` |

The check icon on a selected pill is mandatory, because selection is otherwise carried by fill alone. `STREAMLIT LIMIT`: `st.pills` cannot inject an SVG per state. Nearest alternative: `st.pills` options are created with a leading check mark character (U+2713) for selected values by rebuilding the option labels on each rerun, or the selected count is stated in a `caption` under the control ("3 of 14 lanes selected"). Ship the caption; it is honest and cheap.

```css
.fo-badge { display: inline-flex; align-items: center; gap: var(--fo-space-1); height: 20px; padding: 0 var(--fo-space-2); border-radius: var(--fo-radius-1); border: var(--fo-border-hairline) solid; font: var(--fo-weight-medium) var(--fo-text-xs)/var(--fo-leading-xs) var(--fo-font-ui); color: var(--fo-ink); white-space: nowrap; vertical-align: middle; }
.fo-badge svg { width: 12px; height: 12px; }
.fo-badge--neutral  { background: var(--fo-status-neutral-tint);  border-color: var(--fo-line-hairline); }
.fo-badge--good     { background: var(--fo-status-good-tint);     border-color: var(--fo-status-good-ink); }     .fo-badge--good     svg { color: var(--fo-status-good-ink); }
.fo-badge--warning  { background: var(--fo-status-warning-tint);  border-color: var(--fo-status-warning-ink); }  .fo-badge--warning  svg { color: var(--fo-status-warning-ink); }
.fo-badge--serious  { background: var(--fo-status-serious-tint);  border-color: var(--fo-status-serious-ink); }  .fo-badge--serious  svg { color: var(--fo-status-serious-ink); }
.fo-badge--critical { background: var(--fo-status-critical-tint); border-color: var(--fo-status-critical-ink); } .fo-badge--critical svg { color: var(--fo-status-critical-ink); }
.fo-badge--count    { background: var(--fo-raised); border-color: transparent; font-family: var(--fo-font-mono); font-variant-numeric: tabular-nums; }
[data-testid="stPills"] button { height: 24px; border-radius: var(--fo-radius-pill); border: var(--fo-border-control) solid var(--fo-line-control); background: transparent; color: var(--fo-ink); font: var(--fo-weight-medium) var(--fo-text-xs)/var(--fo-leading-xs) var(--fo-font-ui); padding: 0 var(--fo-space-3); }
[data-testid="stPills"] button:hover { background: var(--fo-surface-hover); border-color: var(--fo-line-strong); }
[data-testid="stPills"] button[aria-checked="true"], [data-testid="stPills"] button[kind="pillsActive"] { background: var(--fo-accent-selection); border-color: var(--fo-accent); }
```

Accessibility. A status badge's text is the status word, so the icon is reinforcement. `st.pills` renders buttons with `aria-checked`, which is announced.

Wrong usage. A badge reading "Nordfrakt" in series slot 1 blue. Carrier identity in a badge should be neutral, because the moment one badge takes a series colour every neutral badge on the page starts to look like a series without one.

### 4.11 Findings panel

This is the product. A finding is a numbered analytical claim that names where money leaks, shows the number, says what to do, and lets a sceptical reader open the evidence and check.

Primitive. `st.container(border=True)` for the panel; `st.markdown` HTML for header, claim, support, action and figure; `st.expander("Evidence (n rows)")` for the collapsible table, containing an `.fo-table--compact` and a tertiary download button. Hooks: `[data-testid="stExpander"]`, `[data-testid="stExpander"] summary`, `[data-testid="stExpanderDetails"]`.

Layout. At 1024 px and up the panel is two columns inside the container, `st.columns([8, 4], gap="medium")`: text left, figure right. Below 1024 px the figure moves above the claim, because a number should be seen before the sentence about it when there is no room for both at once.

Anatomy, numbered as it reads

```
+----------------------------------------------------------------------+
| 01  FINDING   [critical badge]                                        |
|                                                                       |
| Headline claim in h2, one sentence,          |  EUR 184k              |
| names the leak and its size.                 |  figure, 29/36         |
|                                              |  Estimated annual      |
| Support sentence one. Support sentence       |  leakage               |
| two. Support sentence three.                 |  Q3 2026, 3 lanes,     |
|                                              |  1 204 shipments       |
| RECOMMENDED ACTION                                                    |
| One sentence starting with a verb.                                    |
|                                                                       |
| > Evidence (14 rows)                                                  |
|   [collapsed by default; opens to .fo-table--compact, a method line   |
|    and a Download CSV tertiary button]                                |
+----------------------------------------------------------------------+
```

Slots and their constraints

| Slot | Type step | Colour | Max length | Content rule |
|---|---|---|---|---|
| Number | `overline` in Space Grotesk 500 | `--fo-ink-secondary` | "01" to "12" | Two digits, zero-padded, so a stack of findings aligns. Findings are ordered by money at stake, descending, because the buyer reads the first one. |
| Kind word | `overline` | `--fo-ink-secondary` | 12 characters | "Finding", or "Observation" when there is no money figure. |
| Severity badge | badge (4.10) | status variant | 12 characters | Severity is set by a stated rule (6.6), not by the writer. |
| Headline claim | `h2` | `--fo-ink` | 90 characters | One sentence. Contains the entity, the direction and the figure or rate. No adjectives of degree. |
| Support | `body` | `--fo-ink` | 3 sentences, 160 characters each | Sentence one: the comparison basis. Sentence two: the mechanism or driver. Sentence three: the exclusion or uncertainty. Each sentence contains at least one number, because a support sentence without a number is an opinion. |
| Action lead-in | `overline` | `--fo-ink-secondary` | | Reads "Recommended action". |
| Recommended action | `body-strong` | `--fo-ink` | 120 characters | Starts with a verb. Names who acts if known. Contains the expected effect as a number where the model gives one. |
| Figure | `figure` | `--fo-ink` | 10 characters | The money or rate the headline names, formatted per section 6. One per finding. |
| Figure label | `caption` | `--fo-ink-secondary` | 32 characters | What the figure is: "Estimated annual leakage". |
| Figure basis | `caption` | `--fo-ink-secondary` | 40 characters | Period and scope: "Q3 2026, 3 lanes, 1 204 shipments". |
| Severity meter | 4 px track | track `--fo-line-hairline`, fill `--fo-status-*-ink`, ticks `--fo-line-control` | max width 260 px | Under the figure basis. Linear scale 0 to 1.2% of period spend with ticks at the 0.1, 0.3 and 1.0% thresholds; a value above 1.2% fills the track. A `caption` below states the share and the band: "3.8% of period spend. Critical above 1%." The meter puts the severity rule in form so that the badge is never the only carrier of how far over the line a finding is; the caption puts it in text so the meter is never the only carrier either. |
| Evidence summary | `label` | `--fo-ink` | | "Evidence (14 rows)". The count is text. |
| Evidence table | `.fo-table--compact` | | 60 rows or fewer | Columns ordered: entity, period, the measure the claim uses, the comparison value, the difference. The cited cells carry `.fo-cite`. |
| Evidence footer | `caption` | `--fo-ink-secondary` | 2 sentences | Method in one sentence and exclusions in one: "Late fee estimated as 1.5% of invoice where the carrier fee column was empty (312 rows)." |

`JUDGEMENT CALL`: the figure is not coloured by severity. It stays in `ink`, because a red 184k and a red 12k would look equally urgent, and the badge already carries severity. The rejected alternative, a figure in `--fo-status-*-ink`, would make the panel read as an alarm rather than a measurement.

`JUDGEMENT CALL`: evidence is collapsed by default. Open by default was rejected because a briefing of eight findings with eight open tables is a report, not a briefing, and the buyer who wants to check opens exactly the one they doubt.

States

| State | Panel | Number and badge | Claim | Figure | Evidence | Notes |
|---|---|---|---|---|---|---|
| Rest | `--fo-surface`, 1px `--fo-line-hairline`, radius `--fo-radius-2`, padding 20 px 24 px | as specified | `--fo-ink` | `--fo-ink` | collapsed; summary row 40 px with 16 px `chevron-right` | |
| Hover | no change to the panel | | | | summary row `--fo-surface-hover` | Only the expander summary and its buttons are interactive. |
| Focus | | | | | ring on the summary and on the buttons inside | |
| Active (evidence open) | | | | | chevron rotates 90° over `--fo-duration-short` | `STREAMLIT LIMIT`: `st.expander` animates its own height and CSS cannot reliably stop it. Accept it. |
| Disabled | not a state | | | | | |
| Loading | number and kind word drawn; claim replaced by two `--fo-raised` blocks 70% and 45% wide, 20 px high; figure block 120×36 px; no badge; no evidence | | | | | Blocks are static. Panel height matches a typical finding so that eight loading panels do not reflow when they fill. |
| Error | panel drawn; claim reads "This finding could not be computed." in `body`; support gives the reason in one sentence; no figure; badge `neutral` "Not computed" | | | | | The panel stays, because a briefing that silently drops finding 03 renumbers 04, and the reader who remembers "finding 4" is now misled. |
| Empty (no findings at all) | one panel, number "00", kind word "No findings", claim "No leakage above the reporting threshold was found in this period." in `h2`; support states the threshold and the coverage; badge `good` | | | | | A briefing that found nothing is a result and gets the same treatment as one that did. |
| Insufficient data | as Error, with badge `neutral` "Insufficient data" and support naming the minimum: "Requires at least 30 shipments per lane; 12 found." | | | | | |

```css
.fo-finding__head { display: flex; align-items: center; gap: var(--fo-space-3); margin-bottom: var(--fo-space-3); }
.fo-finding__num  { font: var(--fo-weight-medium) var(--fo-text-2xs)/var(--fo-leading-2xs) var(--fo-font-display); letter-spacing: var(--fo-tracking-wide); color: var(--fo-ink-secondary); font-variant-numeric: tabular-nums; }
.fo-finding__kind { font: var(--fo-weight-medium) var(--fo-text-2xs)/var(--fo-leading-2xs) var(--fo-font-ui); letter-spacing: var(--fo-tracking-wide); text-transform: uppercase; color: var(--fo-ink-secondary); }
.fo-finding__claim { font: var(--fo-weight-medium) var(--fo-text-xl)/var(--fo-leading-xl) var(--fo-font-display); letter-spacing: var(--fo-tracking-snug); color: var(--fo-ink); margin: 0 0 var(--fo-space-3); max-width: 62ch; }
.fo-finding__support { font: var(--fo-weight-body) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); color: var(--fo-ink); margin: 0 0 var(--fo-space-2); max-width: 68ch; }
.fo-finding__action-lead { font: var(--fo-weight-medium) var(--fo-text-2xs)/var(--fo-leading-2xs) var(--fo-font-ui); letter-spacing: var(--fo-tracking-wide); text-transform: uppercase; color: var(--fo-ink-secondary); margin: var(--fo-space-4) 0 var(--fo-space-1); }
.fo-finding__action { font: var(--fo-weight-semibold) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); color: var(--fo-ink); margin: 0; max-width: 68ch; }
.fo-finding__figure { font: var(--fo-weight-semibold) var(--fo-text-3xl)/var(--fo-leading-3xl) var(--fo-font-display); letter-spacing: var(--fo-tracking-snug); font-variant-numeric: tabular-nums lining-nums; color: var(--fo-ink); margin: 0; white-space: nowrap; }
.fo-finding__figure .fo-unit { font-size: var(--fo-text-lg); font-weight: var(--fo-weight-medium); color: var(--fo-ink-secondary); letter-spacing: 0; margin-right: var(--fo-space-1); }
.fo-finding__figure-label, .fo-finding__figure-basis { font: var(--fo-weight-regular) var(--fo-text-xs)/var(--fo-leading-xs) var(--fo-font-ui); color: var(--fo-ink-secondary); margin: var(--fo-space-1) 0 0; }
.fo-finding__skeleton { background: var(--fo-raised); border-radius: var(--fo-radius-1); height: 20px; margin-bottom: var(--fo-space-2); }
[data-testid="stExpander"] { border: none; border-top: var(--fo-border-hairline) solid var(--fo-line-hairline); border-radius: 0; margin-top: var(--fo-space-4); background: transparent; }
[data-testid="stExpander"] summary { height: 40px; padding: 0; font: var(--fo-weight-medium) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); color: var(--fo-ink); }
[data-testid="stExpander"] summary:hover { background: var(--fo-surface-hover); color: var(--fo-ink); }
[data-testid="stExpander"] summary svg { color: var(--fo-ink-secondary); transition: transform var(--fo-duration-short) var(--fo-ease-standard); }
[data-testid="stExpanderDetails"] { padding: var(--fo-space-3) 0 0; }
```

Reference implementation shape (Python, presentation only)

```python
def finding(n, kind, severity, claim, support, action, figure, figure_label, figure_basis,
            evidence_df, cite_cells, method, exclusions):
    with st.container(border=True):
        left, right = st.columns([8, 4], gap="medium")
        with left:
            st.markdown(f'''
            <section aria-labelledby="finding-{n}-claim">
            <div class="fo-finding__head">
              <span class="fo-visually-hidden">Finding {n} of {TOTAL}</span>
              <span class="fo-finding__num" aria-hidden="true">{n:02d}</span>
              <span class="fo-finding__kind">{kind}</span>
              {badge(severity)}
            </div>
            <h2 id="finding-{n}-claim" class="fo-finding__claim">{claim}</h2>
            {"".join(f'<p class="fo-finding__support">{s}</p>' for s in support)}
            <p class="fo-finding__action-lead">Recommended action</p>
            <p class="fo-finding__action">{action}</p>
            </section>''', unsafe_allow_html=True)
        with right:
            st.markdown(f'''
            <p class="fo-finding__figure" aria-label="{figure_spoken}">{figure}</p>
            <p class="fo-finding__figure-label">{figure_label}</p>
            <p class="fo-finding__figure-basis">{figure_basis}</p>''', unsafe_allow_html=True)
        with st.expander(f"Evidence ({len(evidence_df)} rows)"):
            st.markdown(html_table(evidence_df, compact=True, cite=cite_cells), unsafe_allow_html=True)
            st.markdown(f'<p class="fo-card__foot">{method} {exclusions}</p>', unsafe_allow_html=True)
            st.download_button("Download CSV", evidence_df.to_csv(index=False),
                               file_name=f"finding-{n:02d}.csv", type="tertiary")
```

Accessibility

- The panel root is `<section aria-labelledby="finding-{n}-claim">`. The claim is an `<h2>` with that id, so the findings list is navigable by heading.
- The position is in a visually hidden prefix "Finding 1 of 8".
- Severity is text in the badge, so no colour-only carrier exists.
- The figure has `aria-label` with the unabbreviated value and unit.
- The expander summary is a `<summary>` in `<details>` and is keyboard operable by default.
- Cited cells carry a visually hidden "cited" so the highlight has a text equivalent.

Wrong usage, three of them because this is the hero

1. Headline "Significant cost overrun on Baltic lanes". No number, an adjective of degree. Correct: "Baltic lanes cost EUR 184k more than the contracted rate in Q3 2026."
2. Figure coloured red for a critical finding. The badge already says critical. The red figure makes the panel a warning light rather than a measurement and fails to distinguish 184k from 12k.
3. Evidence table replaced by a chart. The reader opened the evidence to check a number against the row that produced it. A chart cannot be checked against; a table can. The chart belongs in the analysis section, with the table as its twin.

### 4.12 Masthead and executive summary

Purpose. The masthead names the document, its audience and its basis. The summary states the one figure the briefing exists for and the three sentences an executive reads if they read nothing else. Together they make the page open like a report that was prepared for someone, not a dashboard that happens to be on.

Primitive. `st.markdown` HTML for both. The masthead actions are `st.download_button(type="secondary")` and `st.button(type="tertiary")` in a right-aligned `st.columns([8, 4])`.

Masthead anatomy

1. Overline row. Three `overline` items separated by 1 px by 10 px `--fo-line-control` marks: the document kind ("Executive briefing"), the audience ("Prepared for Nordholm Retail AB"), the build date ("Build 2026-09-11"). The audience is the customer's legal name as they write it, because a briefing addressed to the wrong entity is not trusted.
2. Title row. `h1` left; actions right: a secondary "Download briefing as PDF" and a tertiary "Share with finance".
3. Meta row. `caption` items with the value in `--fo-ink` at weight 500 and the label in `--fo-ink-secondary`: period and ISO week span, source count and row counts, data freshness with zone, report currency and rate date.

Summary anatomy. A two-column block, `st.columns([4, 8], gap="large")`, bounded above and below by hairlines, 32 px padding, 24 px below the masthead.

| Slot | Type step | Colour | Max length | Content rule |
|---|---|---|---|---|
| Overline | `overline` | `--fo-ink-secondary` | 24 characters | Names what the hero figure is: "Leaking against contract". |
| Hero figure | `kpi-hero` 42/48 | `--fo-ink` | 10 characters | The sum the findings account for, per the formatter. Once per view; this is the slot `kpi-hero` exists for. |
| Hero label | `label` | `--fo-ink` | 40 characters | The figure as a share with its basis: "4.8% of Q3 2026 freight spend". |
| Hero basis | `caption` | `--fo-ink-secondary` | 60 characters | Finding count, shipment count and the range: "Across 3 findings, 2 506 shipments. Range EUR 219k to 244k." |
| Composition bar | 10 px stacked bar | series slot of each entity, 1 px `--fo-surface` gaps | | One segment per finding, in finding order, coloured by the entity the finding names. A legend below in `caption` with the figure per segment in `--fo-ink`. This is the one place a finding takes a series colour, because the bar answers "who" and the series palette is the "who" channel. |
| Summary sentences | `lead` | `--fo-ink` | 3 sentences, 180 characters each | Sentence one: the total and its split by severity. Sentence two: the largest finding and its mechanism. Sentence three: the operational measure that moved and the single cause. Numbers in bold at weight 600, at most two per sentence. |
| Summary footer | `caption` | `--fo-ink-secondary` | 120 characters | The recoverable amount and the deadline, plus a tertiary link to how severity is set. |

States. The summary has the same loading, error and empty treatment as a finding (4.11): static `--fo-raised` blocks in the figure and sentence slots; "Could not be computed" with a reason; or the no-findings claim with a `good` badge. The masthead has no states, because it is drawn from configuration, not from data.

Condensed header. When the masthead scrolls out of view a 44 px bar fixed to the top of the viewport carries the title in `h4` weight on Space Grotesk, the period and audience in `caption`, and the hero figure right-aligned in `h3` size, on `--fo-plane` with a hairline below. It appears over `--fo-duration-short` from a 6 px offset and disappears when the briefing itself scrolls out. It exists so the number the page is about is never off screen while the reader is in the findings, which is what an executive scrolling for a detail actually loses. In Streamlit it is a `position: sticky` markdown element at the top of the block container; the fixed variant needs the scroll position, which Streamlit does not expose, so the sticky form is the buildable one and it stays visible from the top of the page rather than appearing on scroll.

Wrong usage. A summary whose three sentences repeat the KPI strip: "Freight spend was EUR 4.82M. Cost per shipment was EUR 1 002. Late rate was 12.4%." Those are readings, not findings. The summary states what leaks, who is responsible and what moved.

---

## 5. Chart theme

### 5.1 Plotly layout defaults

Both themes are Plotly templates registered at startup. Charts inherit everything from the template and set only their data and titles, because a chart that sets its own colours drifts from the system within a sprint.

```python
import plotly.graph_objects as go
import plotly.io as pio

FONT_UI   = "IBM Plex Sans, Segoe UI, Helvetica Neue, Noto Sans, system-ui, sans-serif"
FONT_MONO = "IBM Plex Mono, Cascadia Mono, SF Mono, Consolas, Menlo, monospace"

def make_template(t: dict) -> go.layout.Template:
    axis_common = dict(
        showline=False, zeroline=False, automargin=True,
        ticks="", ticklen=0,
        tickfont=dict(family=FONT_UI, size=12, color=t["tick_ink"]),
        title=dict(font=dict(family=FONT_UI, size=12, color=t["ink_secondary"]), standoff=8),
        showspikes=False,
    )
    return go.layout.Template(layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",        # the card behind the chart is the surface
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_UI, size=13, color=t["ink"]),
        colorway=t["series"],
        margin=dict(l=8, r=8, t=8, b=8),      # a floor; automargin grows it to fit labels
        xaxis=dict(axis_common, showgrid=False, showline=True,
                   linecolor=t["baseline"], linewidth=1),
        yaxis=dict(axis_common, showgrid=True, gridcolor=t["grid"], gridwidth=1, nticks=5,
                   tickfont=dict(family=FONT_MONO, size=12, color=t["tick_ink"]),
                   rangemode="tozero"),
        legend=dict(orientation="h", x=0, xanchor="left", y=1.0, yanchor="bottom",
                    font=dict(family=FONT_UI, size=12, color=t["ink_secondary"]),
                    bgcolor="rgba(0,0,0,0)", itemclick="toggle", itemdoubleclick=False,
                    itemsizing="constant", tracegroupgap=0, title=None),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=t["hover_bg"], bordercolor=t["grid"],
                        font=dict(family=FONT_MONO, size=12, color=t["ink"]),
                        align="left", namelength=-1),
        hoverdistance=24, spikedistance=-1,
        barcornerradius=2, bargap=0.35, bargroupgap=0.08,
        colorscale=dict(sequential=t["seq"]),
        coloraxis=dict(colorbar=dict(thickness=8, len=1, outlinewidth=0, ticks="",
                                     tickfont=dict(family=FONT_MONO, size=11, color=t["tick_ink"]))),
        annotationdefaults=dict(font=dict(family=FONT_UI, size=12, color=t["ink_secondary"]),
                                showarrow=False),
        uniformtext=dict(minsize=11, mode="hide"),
        transition=dict(duration=0),
    ))

DARK = dict(
    ink="#f2f4f7", ink_secondary="#a3aab8", tick_ink="#a3aab8", grid="#262a33",
    baseline="#6f7787", hover_bg="#1c1f26", surface="#16181d",
    series=["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300"],
    seq=[[0, "#0d366b"], [1/7, "#184f95"], [2/7, "#256abf"], [3/7, "#3987e5"],
         [4/7, "#6da7ec"], [5/7, "#9ec5f4"], [6/7, "#cde2fb"], [1, "#eef5fd"]],
)
LIGHT = dict(
    ink="#12151a", ink_secondary="#4a515e", tick_ink="#4a515e", grid="#e3e6eb",
    baseline="#7b8291", hover_bg="#ffffff", surface="#ffffff",
    series=["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"],
    seq=[[0, "#eef5fd"], [1/7, "#cde2fb"], [2/7, "#9ec5f4"], [3/7, "#6da7ec"],
         [4/7, "#3987e5"], [5/7, "#256abf"], [6/7, "#184f95"], [1, "#0d366b"]],
)

pio.templates["fo_dark"]  = make_template(DARK)
pio.templates["fo_light"] = make_template(LIGHT)
pio.templates.default = "fo_dark"

PLOTLY_CONFIG = {"displayModeBar": False, "displaylogo": False, "responsive": True}
```

Render every figure with `st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)`, because the modebar is chrome the buyer never asked for and the table twin plus the download button replace its only useful function.

Tick label ink is `ink-secondary`, not `ink-muted`, because tick labels are text at 12 px and must clear 4.5:1 (7.6 dark, 8.0 light).

### 5.2 Axis and gridline treatment

| Element | Treatment | Reason |
|---|---|---|
| Y gridlines | 1 px, `--fo-chart-grid`, solid, 4 to 6 lines | Dashed gridlines add texture that competes with the marks. |
| X gridlines | none | Time is read from the baseline, and vertical lines fight with bars. |
| X baseline | 1 px, `--fo-chart-baseline` | The one line that anchors the marks. |
| Y axis line | none | The gridlines already give the scale. |
| Zero line | off; if data crosses zero, draw a 1 px `--fo-chart-baseline` line shape at y=0 | Plotly's zero line has its own styling that drifts. |
| Ticks | none; tick labels outside, 8 px standoff | Tick marks duplicate the gridlines. |
| Y range | from zero for magnitudes (`rangemode="tozero"`); from data for rates and indices, stated in the card subtitle | A bar that does not start at zero lies about proportion. |
| Axis titles | omitted when the card subtitle names the measure and unit; otherwise `caption` style | A title on the axis and one on the card is one too many. |
| Y tick count | `nticks=5` | Five labels fit a 240 px chart without collision. |
| Date ticks | ISO `%Y-%m-%d` daily, `W%V` weekly, `%Y-%m` monthly, via `tickformatstops` | The buyer thinks in ISO weeks. |
| Money ticks | explicit `tickvals` and `ticktext` produced by the section 6 formatter | Plotly's SI prefixes use "G" for billions and never write "bn", which does not match the formatter. |

### 5.3 Mark specifications

| Mark | Specification | Reason |
|---|---|---|
| Line | width 2 px; `line.shape="linear"`; no smoothing | A spline invents values between measurements. |
| Line markers | hidden above 24 points; at 24 or fewer, 6 px diameter with a 1.5 px outline in the surface colour | Markers on dense series become a caterpillar. |
| Line end label | annotation at the last point with the series name in `caption`, `ink-secondary`, when there are 4 or fewer series | A direct label beats a legend, because the eye does not travel. |
| Bar | `bargap=0.35` single series; `bargroupgap=0.08` grouped; `barcornerradius=2` (Plotly rounds the free end only) | A 35% gap keeps bars readable as separate items; a 2 px radius softens without making bars look like pills. |
| Bar outline | `marker.line.width=1`, colour = the surface hex for the active theme | The one-pixel surface gap separates stacked segments and adjacent groups without a border colour. |
| Stacked segment gap | same 1 px surface line | |
| Heatmap cell gap | `xgap=1, ygap=1` | The gap is the grid. |
| Heatmap cell label | always on; `tabular-sm`; ink chosen per cell by the `--fo-seq-ink-flip` step | Colour alone cannot carry a heatmap. |
| Marker minimum | 6 px diameter; scatter with more than 400 points drops to 4 px at 70% opacity and states the count in the subtitle | Below 6 px a marker's colour cannot be identified. |
| Area fills | not used | Area under a line implies a cumulative quantity where there is none. |
| Reference line | 1 px `--fo-line-strong`, dash "4,4", labelled at its right end in `caption` | The only dashed line in the system, so that it reads as "not data". |
| Target band | `--fo-accent-tint` rectangle shape, labelled | |
| Highlighted series | the others drop to 35% opacity; the highlighted one keeps its own colour and width | Never repaint the highlighted series, because colour follows the entity. |
| Text on bars, light theme | mandatory for every bar chart in light; `textposition="outside"`, `tabular-sm`, `--fo-ink` | Three light slots sit under 3:1 on white and the value label is the relief channel. Dark charts show labels when the card is a single series with 12 or fewer bars. |

Series slot assignment

- Every entity that can appear in a categorical chart is assigned a slot once, at data load, from the carrier master's order, never from magnitude, because magnitude changes with filters and identity must not.
- Entities beyond six fold into "Other", drawn in `--fo-series-other`, because a seventh hue was rejected by the palette validation.
- A chart with one series uses slot 1 unless the series is an entity with an assigned slot, in which case it keeps its slot.

### 5.4 Tooltip and crosshair

| Behaviour | Specification |
|---|---|
| Mode | `hovermode="x unified"` for time series and grouped bars; `"closest"` for scatter and heatmap |
| Tooltip surface | `--fo-chart-hover-bg`, 1 px `--fo-chart-grid` border, `tabular-sm` figures, `caption` labels, 8 px series swatch |
| Tooltip content | header: the x value formatted per section 6; rows: series name and value with unit; never a trace's internal name |
| Row order | descending by value at that x, because the reader asks "who is highest here" |
| Crosshair | time series only: `xaxis.showspikes=True, spikemode="across", spikesnap="cursor", spikethickness=1, spikedash="solid", spikecolor=--fo-chart-crosshair`; no y spike |
| Hover on bars | no change to the bar; Plotly 6 has no hover style for bar traces and a fake one via events is not buildable in Streamlit |
| Touch | tooltips follow tap; the table twin is the primary path on touch devices |

The hover template is set once per trace type in a helper, never inline in a chart, because one wrong `%{y:,.2f}` in a money chart produces cents where the rest of the product shows euros.

### 5.5 Legend rules

- Legend sits above the plot, left-aligned, horizontal, because the eye reads the legend then the chart and top-left is where it starts.
- Legend appears only when there are 2 to 6 series and direct labels are not possible, because a one-series legend is noise and direct labels always beat legends.
- Legend order equals slot order, not value order, because a legend that reorders by value moves between periods.
- Clicking a legend item toggles that series and nothing else re-colours, because colour follows the entity.
- Legend text is `caption` in `ink-secondary`; swatches are constant size (`itemsizing="constant"`).
- A hidden series stays in the legend at Plotly's default reduced opacity, because the reader must be able to bring it back.

### 5.6 Two measures, two panels

Never a dual axis. Two measures of different scale become `make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12)`. Each panel gets a `caption` annotation at its top-left naming the measure and unit. The x axis is drawn once, on the lower panel; the upper panel's x tick labels are hidden. Both panels use slot colours for the same entity, because the point of stacking is to compare one entity across two measures.

### 5.7 Chart and table twin

Every chart card has a segmented control in its header: "Chart | Table". The table view renders the chart's exact data as `.fo-table`, with the same column order as the legend, the same number formatting as the tooltip, and a "Download CSV" tertiary button. The control's state lives in `st.session_state` keyed by the card id, because a rerun that forgets which cards were in table view is a rerun the reader notices.

The twin is not optional and not behind an expander, because it is the relief channel for the light palette and the only path to exact values for anyone who cannot use hover.

### 5.8 Empty and insufficient-data states

| State | Rule | Rendering |
|---|---|---|
| No data | The filtered frame has zero rows. | No Plotly figure. A 240 px tall area with a 24 px `chart` icon in `--fo-ink-muted`, `body` "No shipments match the current filters." in `--fo-ink-secondary`, and a tertiary "Reset filters". The Chart/Table control is disabled. |
| Insufficient data | Any series has fewer points than the chart type's minimum: lines need 3 points per series, bars need 1, heatmaps need 2×2, scatter needs 10. | No chart. The area shows `body` "Not enough data to draw this chart. 2 weeks of data; 3 needed." and the table twin is shown in its place, because a table is honest at any row count. |
| Partial data | Some series meet the minimum and some do not. | The chart draws the qualifying series. A `caption` under the chart names the omitted series and why. Omitted series appear in the legend with "(insufficient)" appended. |
| All zero | Every value is zero. | The chart draws with the y range fixed to [0, 1] so the baseline is visible, and a caption says "All values are zero for this period." |
| Loading | Data is being computed. | The card holds its height; `st.spinner("Computing")` inside. No skeleton chart, because a fake chart shape reads as data for the half second it is visible. |

An empty chart never shows Plotly's default empty axes, because an axis with no marks looks like a broken chart, not an honest one.

---

## 6. Content and voice rules

### 6.1 Numbers by magnitude

Number locale. Decided: an English-language UI with SI-style grouping, a narrow no-break space (U+202F) as the thousands separator and a full stop as the decimal mark, so "1 204 812.5", because it is the one form every reader in the market reads the same way. The rejected alternatives: en-GB commas ("1,204,812.5"), which a Danish or German reader misreads as a decimal, and continental points ("1.204.812,5"), which a British reader misreads the other way. The current `eur()` helper in `utils/metrics.py` uses commas and changes to match.

| Magnitude | KPI and finding figure | Table cell | Tooltip and axis tick |
|---|---|---|---|
| 0 to 999 | integer: "812" | integer: "812" | integer |
| 1 000 to 9 999 | one decimal in thousands: "1.5k" | full: "1 530" | "1.5k" |
| 10 000 to 999 999 | integer thousands: "184k" | full: "184 212" | "184k" |
| 1 000 000 to 9 999 999 | two decimals in millions: "1.24M" | full: "1 240 000" | "1.24M" |
| 10 000 000 and above | one decimal in millions: "12.4M" | full | "12.4M" |
| 1 000 000 000 and above | one decimal in billions: "1.2bn" | full | "1.2bn" |

- Abbreviations are lowercase "k", uppercase "M", lowercase "bn", because that is what a Nordic CFO writes and none collides with a unit.
- Three significant figures is the ceiling for any abbreviated figure, because a fourth digit on a KPI is precision the estimate does not have.
- Tables never abbreviate, because a table exists to be checked.
- Rates: one decimal ("12.4%"), two when under 1% ("0.42%"). No space before the percent sign. `JUDGEMENT CALL`: the SI convention puts a space ("12.4 %"); it was rejected because it reads as a typo to the English-reading half of the audience, and ASK 2 already covers the Nordic reader's grouping.
- Ratios: two decimals ("1.34").
- Shipment counts: full integers with grouping, never abbreviated below 100 000.
- Durations: "3.2 days", "14 h", "45 min". Never "3d 4h".
- Zero is "0", never a dash, because a dash means "no data" and zero is data.
- No data in a cell is the word "none" in `ink-secondary`. Never a hyphen or dash.
- Negative: true minus U+2212. Positive deltas: explicit "+".
- Rounding: half away from zero, applied once at display, never in the pipeline.

### 6.2 Currency

- ISO code, never a symbol: "EUR 184k", "SEK 1.2M", because the data spans EUR, SEK, NOK and DKK and "kr" is three currencies.
- Code before the value, separated by a narrow no-break space.
- One currency per chart. Mixed-currency data is converted to the report currency at a stated rate, and the rate and its date appear in the card footer.
- Table headers carry the code once: "Cost (EUR)". Cells carry only the figure.
- Never cents in a KPI or finding. Tables show cents only where the source is invoice-line data and the column title says "(EUR, incl. cents)".

### 6.3 Dates and ranges

- Dates are ISO 8601, "2026-09-11", everywhere a date is data: tables, filters, tooltips, axes.
- In prose: day, month name, year: "11 September 2026". Never numeric day/month order, because 11/09 is two dates.
- Ranges use the word "to": "2026-06-01 to 2026-08-31". In prose: "1 June to 31 August 2026". Never a dash of any length.
- Weeks are ISO weeks with year: "W36 2026". Quarters: "Q3 2026". Months: "September 2026" in prose, "2026-09" in tables and axes.
- Relative time is never used in a briefing ("last month"), because the briefing is read weeks later. Filter presets may say "Last 4 weeks" because the resolved dates appear in the field.
- Timestamps carry the zone: "2026-09-11 14:32 CET". Freshness line: "Data as of 2026-09-11 06:00 CET, 4 sources."

### 6.4 Case

| Context | Case | Example |
|---|---|---|
| Page title | Sentence | "Freight operations briefing" |
| Section and card titles | Sentence | "Cost per shipment by carrier" |
| Finding claims and support | Sentence | |
| Buttons, tabs, segments, pills | Sentence | "View as table" |
| Overlines | Uppercase via CSS; written in sentence case in source | "Recommended action" |
| Table headers | Sentence | "Late rate (%)" |
| Proper nouns, ISO codes, product name | As they are | "Nordfrakt", "EUR", "Freight Operations Intelligence" |

Title case is never used, because it reads as marketing and because it hides which words are names.

### 6.5 Maximum lengths

| Slot | Max characters | Overflow behaviour |
|---|---|---|
| Page title | 40 | Not permitted; shorten. |
| Section title | 40 | Shorten. |
| Card title | 40 | Ellipsis with `title`. |
| Card subtitle | 80 | Wrap to two lines. |
| KPI label | 24 | Shorten. |
| KPI value | 8 incl. unit | Formatter abbreviates. |
| KPI delta figure | 12 | |
| KPI basis | 20 | |
| KPI footnote | 60 | Wrap to two lines. |
| Finding headline | 90 | Wrap to two lines at 62ch; never three. |
| Finding support sentence | 160, max 3 sentences | |
| Recommended action | 120 | |
| Figure | 10 | Formatter. |
| Figure label | 32 | |
| Figure basis | 40 | |
| Button label | 20 | |
| Tab label | 16 | |
| Segment label | 12 | |
| Badge | 12 | |
| Chip | 24 | Ellipsis. |
| Pill | 20 | |
| Alert title | 48 | |
| Alert body | 200 | |
| Toast | 60 | |
| Table cell text | column width | Ellipsis with `title`. |
| Chart subtitle | 80 | |
| Chart caption or footnote | 120 | |
| Empty state message | 80 | |

### 6.6 Voice

- Lead with the number and the entity: "Baltic lanes cost EUR 184k more than contract in Q3 2026", not "We observed elevated costs".
- State the basis with every figure: period, scope, comparison. A number without a basis is not a claim.
- Name exclusions in the same breath: "excl. 312 rows without a carrier fee".
- No adjectives of degree: significant, notable, considerable, dramatic, huge. The number is the degree.
- No hedges as filler: "it appears", "somewhat". Uncertainty is quantified or given as a range: "EUR 160k to 210k".
- Verbs, not nouns, in actions: "Renegotiate the Baltic rate card with Nordfrakt before the November tender."
- Second person is never used in findings. The finding is about the operation, not the reader.
- Exclamation marks, rhetorical questions and emoji never appear.
- Severity is set by rule, not by tone. The measure is leakage as a share of freight spend in the same period, because a share scales from a customer spending 500k to one spending 50M where an absolute figure does not. Critical: 1% or more, or any contractual breach regardless of size. Serious: 0.3% to 1%. Warning: 0.1% to 0.3%, or any level where data quality caps confidence in the figure. Good: under 0.1%. Recalibrate after the first three real builds, because the right cut-offs depend on how noisy customer data proves to be.
- Errors name the object, the cause and the remedy: "Meridian_Aug.xlsx: no date column recognised. Rename the column to ship_date or map it in Settings."

---

## 7. Usage guidance

| Component | Use when | Use instead | Wrong usage, worked |
|---|---|---|---|
| KPI tile | A quantity the reader compares across periods, with a defined basis, that the briefing refers to. | Section header count for counts of things on the page. Finding figure for a number that needs a sentence. | Tile "Findings: 8". Eight is not a measurement of the operation. Replace with a section header "Findings (8)". |
| KPI strip | 3 to 5 tiles at the top of a view, once per view. | A table when there are more than 5 quantities. | A second strip halfway down the page for "Carrier KPIs". Two strips means two summaries. Move carrier figures into a table in the carrier tab. |
| Card | One chart, table or panel that needs a title and a boundary. | Plain flow for prose. Findings panel for a claim. | A card around the page's single introductory paragraph. Prose does not need a border. |
| Section header | Grouping 2 or more cards under one theme. | Card title when there is one card. | Section "Overview" above the KPI strip. The strip is self-explanatory and the page title is the heading. |
| Primary button | The one action the view exists for. | Secondary for everything else. | "Apply filters" as primary beside "Generate briefing" as primary. Filters are secondary. |
| Secondary button | Actions that change what is shown or export it. | Tertiary for reveal and reset. | "Reset filters" as secondary. Reset is a reveal-class action. Tertiary. |
| Tertiary button | Reveal, reset, download inside a card. | Segmented control when the reveal is a toggle between two persistent views. | "View as table" as a tertiary that swaps the chart and offers no way back. Use the Chart/Table segmented control. |
| Text input | Free text: a search term, a threshold value. | Select when the values are known. Number input for numbers. | Text input for "Report currency". Four known values. Select. |
| Select | One of 3 to 30 known values. | Segmented control for 2 to 4 short values shown inline. Radio when options need descriptions. | Select for "Period preset: 4 weeks, quarter, YTD". Three short values. Segmented control. |
| Multiselect | Zero or more of a known set: carriers, lanes. | Pills when the set is 6 or fewer and always visible. | Multiselect of 200 lanes with no search hint. Add the placeholder "Type to search lanes" and the selected-count caption. |
| Date range | Any period filter. | Nothing else. | Two separate date inputs "From" and "To". They can be set in the wrong order and take twice the width. |
| Radio | 2 to 5 exclusive options where at least one needs a sentence of explanation. | Segmented control when labels are one word. | Radio for "Chart / Table". Segmented control. |
| Segmented control | 2 to 4 exclusive one-word options that switch a view inline. | Tabs when each option has substantial, different content. | Segmented control "Lanes / Carriers / Trend / Audit". Four sections of different content. Tabs. |
| Tab bar | 2 to 6 sections of content that are peers and need not be seen together. | Sections in flow when the reader should see all of them. Segmented control for a view toggle inside one card. | Tabs "Briefing" and "Charts". The briefing is the page; the charts support it. Put them in flow. |
| Table, HTML | 60 rows or fewer, exact tokens, cited cells, chart twin. | `st.dataframe` above 60 rows or when sorting is needed. | `.fo-table` for a 4 800 row shipment log. Unscrollable and slow. `st.dataframe`. |
| Table, `st.dataframe` | Large or sortable data. | HTML table where a finding cites a cell. | `st.dataframe` for the evidence table. The cited cell cannot be highlighted. HTML. |
| File dropzone | The data ingest step, once per view. | Sample data buttons beside it for the demo path. | A dropzone in every tab "in case the user wants to add data here". One ingest point. |
| Inline alert | A condition attached to a place on the page: a caveat under a chart, a failed file under the dropzone. | Toast for a transient confirmation. Findings panel when the condition is a finding. | Alert `warning` at the top of the page reading "Some data may be incomplete". No object, no number, no place. Attach it to the card it affects and say "312 of 4 812 rows lack a carrier fee". |
| Toast | Confirmation of a completed action with no consequence to read: "Table exported". | Inline alert for anything the reader must act on. | Toast "3 files failed to parse". Gone in four seconds. Dropzone error state. |
| Badge | A status or category word beside the thing it describes. | Pill when it is toggleable. Count badge for counts. | Badge "Click to filter". A badge is not interactive. Pill. |
| Pill | A toggleable filter value from a small visible set. | Multiselect when the set is large. | Pills for 40 lanes. Multiselect. |
| Findings panel | An analytical claim with a number, an action and evidence. | Inline alert for a data-quality condition. KPI tile for a bare figure. | Finding "Data quality: 3% of rows lack cost". That is a caveat about the data, not a finding about the operation. Inline alert `warning` under the KPI strip. |
| Line chart | A measure over time, 6 or fewer series, 3 or more points each. | Bar chart for 12 or fewer periods of one series. Table when under 3 points. | Line chart of 6 carriers over 2 months of monthly data. Two points per line. Grouped bars. |
| Bar chart | Comparison across categories or 12 or fewer periods. | Line for long time series. Heatmap for two categorical dimensions. | Bars for 52 weeks. Line. |
| Heatmap | Magnitude across two categorical dimensions: lane by week late rate. | Bars when one dimension has 3 or fewer values. | Heatmap of 2 carriers by 4 quarters. Eight cells. Grouped bars with labels. |
| Two-panel chart | Two measures of different scale on the same x. | One chart when scales match. Two cards when the x differs. | Cost and late rate on one chart with a second y axis. Banned. Two panels sharing x. |

---

## 8. Decisions taken with the owner

Three points depended on the product owner and were settled on 11 September 2026. No open questions remain.

1. Theme selection (1.3). Per build. Each customer build ships one `config.toml`. Streamlit's stock theme picker is removed with `toolbarMode = "minimal"`.
2. Number locale (6.1). SI grouping with a narrow no-break space and a point decimal: "1 204 812.5". The `eur()` helper changes to match.
3. Severity thresholds (6.6). Share of period freight spend: critical at 1% or on any contractual breach, serious from 0.3%, warning from 0.1% or on capped confidence, good below. Recalibrate after three real builds.

Two further items are not blocking and are recorded so they are not lost.

- The existing `.brief-card` in `app.py` uses a 3 px coloured left border, which the house rules prohibit. The findings panel (4.11) replaces it. The `page_icon` emoji should be replaced by a PNG mark.
- `utils/theme.py` carries Inter as its font stack and a light-only palette. It should be replaced by the two Plotly templates in 5.1 and a token injection helper that emits the CSS in 1.2.

---

## 9. Change log

v1.1, 11 September 2026. A pass for a more premium, business-grade read, requested by the owner. Fonts, palettes and the house rules are unchanged; every addition is composition, analytics or motion.

- Added 4.12 Masthead and executive summary, with the hero figure, the composition bar and the condensed header.
- Added the `lead` type step for summary sentences.
- Added the sparkline to the KPI tile (4.1) and the severity meter to the findings panel (4.11).
- Added 1.4 Motion rules, including the entrance stagger and the explicit refusal of scroll-linked motion.
- Added `--fo-duration-enter` and `--fo-stagger` tokens.
- Chart / Table twin is wired on every chart card in the specimen, and the weekly two-panel chart carries a live crosshair and tooltip.
- Section spacing between the findings and analysis raised from 32 to 40 px.

Considered and rejected in this pass: parallax and reveal-on-scroll (not buildable in Streamlit, and marketing-page motion on an instrument); count-up numbers (a number in motion reads as a number changing); a different display face or palette (the settled foundations are validated, and a change reopens every gate in Appendix B).

v1.2, 11 September 2026. Implemented in the Streamlit app. What the real DOM of Streamlit 1.50.0 changed, recorded so the selectors in section 4 are read against it.

- Tokens, component CSS and both Plotly templates live in `utils/theme.py`; HTML components in `utils/ui.py`; figures and the Chart / Table card in `utils/charts.py`; every format in `utils/fmt.py`. The theme is read from `theme.base` in `config.toml`, so CSS, Streamlit widgets and Plotly can never disagree.
- Component rules are emitted with an `.stApp` prefix, because Streamlit styles markdown paragraphs with a class-plus-element selector (0,1,1) that outranks a bare component class (0,1,0).
- `st.container(border=True)` draws its border on the `stVerticalBlock` itself, with no attribute to select on. Every card therefore opens with an invisible marker element (`ui.card_mark()`), and the card is the block whose first child is that marker. `stVerticalBlockBorderWrapper` in 4.2 and 4.11 does not exist in 1.50.
- The segmented control is `[data-testid="stButtonGroup"] [data-baseweb="button-group"]` with buttons `stBaseButton-segmented_control` and `stBaseButton-segmented_controlActive`. `stSegmentedControl` in 4.5 does not exist in 1.50.
- Streamlit adds an anchor link to every heading, including HTML headings in markdown. They are hidden.
- The expander chevron is a Material icon font glyph. It is hidden and replaced by the system's stroke chevron through a CSS mask, so one icon style holds.
- The running header (4.12) is the sticky form: an `st.empty()` slot under the masthead, filled once the hero figure is known, sticky at the height of Streamlit's header bar. It carries the masthead's meta row, so in flow it is the meta row and when stuck it is the running header, with no duplication.
- The sidebar holds data ingest and opens by default (`initial_sidebar_state="auto"`), because the upload path is a selling point and a collapsed sidebar hides it. Section 3.1 said collapsed; this supersedes it.
- The entrance animation runs on the first script run of a session only, because Streamlit re-renders the page on every interaction and a filter change is not an arrival.
- Heatmap label ink is chosen per cell against the interpolated cell colour, whichever of `ink` and `ink-inverse` clears the higher contrast, because Plotly interpolates between ramp steps and a fixed flip step would leave mid-ramp cells under 4.5:1.
- The `eur()` and `eur_exact()` helpers now produce the section 6 format; the tests were updated to match, and the traceability test treats the narrow no-break space as a grouping character.
- Fixed in passing: `ensure_processed()` now rebuilds a processed dataset that is older than its inputs, which the tests expected and which had been serving stale carrier names.

## Appendix A. Icon set

Stroke icons, 24-unit viewBox, 1.5 unit stroke, round caps and joins, `currentColor`, rendered at 16, 20 or 24 px. One style, because two icon styles on one page read as two products. Every icon carries `aria-hidden="true"`, because the text beside it is the accessible name.

```html
<!-- check-circle: good -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/></svg>
<!-- alert-triangle: warning -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3.5l9 16H3l9-16z"/><path d="M12 9.5v4.5"/><path d="M12 17h.01"/></svg>
<!-- alert-circle: serious -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7.5v5"/><path d="M12 16h.01"/></svg>
<!-- alert-octagon: critical -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3h8l5 5v8l-5 5H8l-5-5V8l5-5z"/><path d="M12 7.5v5"/><path d="M12 16h.01"/></svg>
<!-- info: neutral -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/></svg>
<!-- chevron-right -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>
<!-- chevron-down -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>
<!-- x -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>
<!-- check -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>
<!-- upload -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 16V4m0 0l-4 4m4-4l4 4"/><path d="M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3"/></svg>
<!-- download -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4v12m0 0l-4-4m4 4l4-4"/><path d="M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3"/></svg>
<!-- file -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a1 1 0 00-1 1v16a1 1 0 001 1h10a1 1 0 001-1V8l-4-5z"/><path d="M14 3v5h4"/></svg>
<!-- table -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="1"/><path d="M3.5 9.5h17M3.5 14.5h17M9.5 9.5v10"/></svg>
<!-- chart -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20V4"/><path d="M4 20h16"/><path d="M8 16v-5M12 16V8M16 16v-3"/></svg>
<!-- filter -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5h16l-6 7v6l-4 2v-8L4 5z"/></svg>
<!-- calendar -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.5" y="5.5" width="17" height="15" rx="1"/><path d="M3.5 10.5h17M8 3.5v4M16 3.5v4"/></svg>
<!-- search -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="M16 16l4 4"/></svg>
<!-- arrow-up-right -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17L17 7"/><path d="M9 7h8v8"/></svg>
<!-- arrow-down-right -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 7l10 10"/><path d="M17 9v8H9"/></svg>
<!-- minus -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 12h12"/></svg>
<!-- refresh -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 12a8 8 0 01-14.5 4.6"/><path d="M4 12a8 8 0 0114.5-4.6"/><path d="M18.5 3.5v4h-4M5.5 20.5v-4h4"/></svg>
```

Icons sit at `--fo-icon-sm` inside text, `--fo-icon-md` in alerts, `--fo-icon-lg` in empty states and the dropzone. The stroke stays 1.5 viewBox units at every size, so it renders at 1 px, 1.25 px and 1.5 px respectively, because scaling the stroke with the icon would make the 24 px icons heavier than the type beside them.

```css
.fo-visually-hidden { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0; }
```

## Appendix B. Contrast register

Every text and mark pair the system uses, with its computed ratio. Pairs below a gate are listed with the rule that keeps them out of text.

| Pair | Dark | Light | Gate | Status |
|---|---|---|---|---|
| ink on surface | 16.12 | 18.29 | 4.5 | pass |
| ink on raised | 14.97 | 16.60 | 4.5 | pass |
| ink-secondary on surface | 7.61 | 7.99 | 4.5 | pass |
| ink-secondary on raised | 7.07 | 7.25 | 4.5 | pass |
| ink-muted on surface | 3.94 | 3.86 | 3.0 as mark | pass as mark; excluded from text under 24 px |
| ink-muted on raised (disabled) | 3.66 | 3.50 | 3.0 | pass |
| ink-link on surface | 4.88 | 4.99 | 4.5 | pass |
| ink-link on raised | 4.53 | 4.50 | 4.5 | pass |
| focus ring on plane | 5.19 | 4.16 | 3.0 | pass |
| focus ring on surface | 4.88 | 4.42 | 3.0 | pass |
| primary label on primary fill | 5.19 | 6.12 | 4.5 | pass |
| primary fill against plane | 5.19 | 3.09 | 3.0 | pass |
| line-control on plane | 3.09 | 3.02 | 3.0 | pass; controls never sit bare on surface |
| line-control on surface | 2.91 | 2.97 | 3.0 | fail; hence the fieldset rule in 4.4 |
| status-good-ink on surface | 5.29 | 4.99 | 4.5 | pass |
| status-good-ink on raised | 4.92 | 4.53 | 4.5 | pass |
| status-warning-ink on surface | 9.68 | 4.99 | 4.5 | pass |
| status-serious-ink on surface | 6.73 | 4.97 | 4.5 | pass |
| status-critical-ink on surface | 4.86 | 4.96 | 4.5 | pass |
| status-critical-ink on raised | 4.52 | 4.50 | 4.5 | pass |
| status-critical-fill on surface | 3.70 | 4.80 | 3.0 as mark | pass |
| status-warning-fill on surface | 9.68 | 1.83 | 3.0 as mark | fails light; the fill never carries meaning alone in light |
| status-serious-fill on surface | 6.73 | 2.64 | 3.0 as mark | fails light; same rule |
| ink on every status tint | 11.65 or more | 15.34 or more | 4.5 | pass |
| ink on accent-tint | 13.16 | 16.20 | 4.5 | pass |
| ink on accent-selection | 11.65 | 14.58 | 4.5 | pass |
| accent on accent-selection (check icon) | 3.53 | 3.52 | 3.0 | pass |
| series 1 to 6 on surface | 4.50 to 5.78 | 2.17 to 4.95 | 3.0 as mark | dark passes all six; light fails slots 3, 4 and 5 and ships value labels and the table twin |
| chart tick ink on surface | 7.61 | 7.99 | 4.5 | pass |
| chart baseline on surface | 3.94 | 3.86 | 3.0 | pass |
| seq steps 5 to 8 with ink-inverse (dark) | 5.19 to 17.20 | | 4.5 | pass |
| seq steps 1 to 4 with ink (dark) | 4.90 to 10.85 | | 4.5 | pass |
| seq steps 6 to 8 with ink-inverse (light) | | 5.39 to 11.95 | 4.5 | pass |
| seq steps 1 to 5 with ink (light) | | 5.03 to 16.65 | 4.5 | pass |
