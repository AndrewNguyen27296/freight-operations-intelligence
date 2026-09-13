"""
Design tokens, component CSS and Plotly templates. The implementation of
docs/design-system.md, sections 1, 4 and 5.

Two themes, dark by default. Which one is active is decided per build by
.streamlit/config.toml (theme.base), and everything here reads that one
setting, so the CSS custom properties, Streamlit's own widget colours and the
Plotly template can never disagree.

Colour follows the entity: every carrier owns one categorical slot for the
life of the dataset, so a filter that removes a carrier never repaints the
survivors. The six slots and the sequential ramp were validated against
each theme's surface before they were written down here; the contrast
figures are in Appendix B of the design system document. Do not add a
seventh hue. The tail folds into "Other".
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

# --- Entities ---------------------------------------------------------------

# Fixed slot order. The order IS the colour-vision safety mechanism.
CARRIER_ORDER = [
    "Nordfrakt", "Meridian Express", "Vantage Freight",
    "Baltica Logistics", "Kestrel Parcel", "Hanseatic Line",
]

# --- Colour tokens, by role ------------------------------------------------

DARK = {
    "plane": "#0f1115", "surface": "#16181d", "raised": "#1c1f26",
    "surface_hover": "#1f2126", "surface_pressed": "#282a2e",
    "line_hairline": "#262a33", "line_control": "#5c6270", "line_strong": "#6f7787",
    "ink": "#f2f4f7", "ink_secondary": "#a3aab8", "ink_muted": "#6f7787",
    "ink_inverse": "#0f1115", "ink_link": "#3987e5",
    "accent": "#3987e5", "accent_hover": "#4c92e7", "accent_active": "#3277ca",
    "accent_tint": "#1c2a3d", "accent_selection": "#1e334d", "focus": "#3987e5",
    "action_fill": "#3987e5", "action_fill_hover": "#4c92e7",
    "action_fill_active": "#3277ca", "action_ink": "#0f1115",
    "good_fill": "#0ca30c", "good_ink": "#0ca30c", "good_tint": "#142e1a",
    "warning_fill": "#fab219", "warning_ink": "#fab219", "warning_tint": "#3a311c",
    "serious_fill": "#ec835a", "serious_ink": "#ec835a", "serious_tint": "#382927",
    "critical_fill": "#d03b3b", "critical_ink": "#d95f5f", "critical_tint": "#341e22",
    "neutral_ink": "#a3aab8", "neutral_tint": "#1c1f26",
    "series": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300"],
    "series_other": "#6f7787",
    # Anchor flipped: step 1 is the lowest value and the darkest cell.
    "seq": ["#0d366b", "#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb", "#eef5fd"],
    "seq_ink_flip": 5,
    "shadow_1": "0 2px 8px rgba(0,0,0,.45), 0 0 0 1px #262a33",
    "shadow_2": "0 8px 24px rgba(0,0,0,.55), 0 0 0 1px #262a33",
    "weight_body": 450,
}

LIGHT = {
    "plane": "#f7f8fa", "surface": "#ffffff", "raised": "#f2f4f7",
    "surface_hover": "#f6f6f6", "surface_pressed": "#ececed",
    "line_hairline": "#e3e6eb", "line_control": "#8f96a3", "line_strong": "#7b8291",
    "ink": "#12151a", "ink_secondary": "#4a515e", "ink_muted": "#7b8291",
    "ink_inverse": "#ffffff", "ink_link": "#2770c7",
    "accent": "#2a78d6", "accent_hover": "#266cc1", "accent_active": "#2262af",
    "accent_tint": "#eaf2fb", "accent_selection": "#d9e7f8", "focus": "#2a78d6",
    "action_fill": "#2262af", "action_fill_hover": "#1f5ea6",
    "action_fill_active": "#184f95", "action_ink": "#ffffff",
    "good_fill": "#0ca30c", "good_ink": "#0a820a", "good_tint": "#e7f6e7",
    "warning_fill": "#fab219", "warning_ink": "#92680f", "warning_tint": "#fef7e8",
    "serious_fill": "#ec835a", "serious_ink": "#a65c3f", "serious_tint": "#fdf3ee",
    "critical_fill": "#d03b3b", "critical_ink": "#cc3a3a", "critical_tint": "#faebeb",
    "neutral_ink": "#4a515e", "neutral_tint": "#f2f4f7",
    "series": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"],
    "series_other": "#7b8291",
    "seq": ["#eef5fd", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"],
    "seq_ink_flip": 6,
    "shadow_1": "0 2px 8px rgba(18,21,26,.10), 0 0 0 1px #e3e6eb",
    "shadow_2": "0 8px 24px rgba(18,21,26,.16), 0 0 0 1px #e3e6eb",
    "weight_body": 400,
}

THEMES = {"dark": DARK, "light": LIGHT}

FONT_DISPLAY = '"Space Grotesk", "Segoe UI Variable Display", "Segoe UI", "Helvetica Neue", system-ui, sans-serif'
FONT_UI = '"IBM Plex Sans", "Segoe UI", "Helvetica Neue", "Noto Sans", system-ui, sans-serif'
FONT_MONO = '"IBM Plex Mono", "Cascadia Mono", "SF Mono", Consolas, Menlo, "DejaVu Sans Mono", monospace'

FONT_IMPORT = (
    "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600"
    "&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"
)


def active_theme() -> str:
    """'dark' or 'light', from the build's config.toml. Dark when unset."""
    try:
        import streamlit as st
        base = st.get_option("theme.base")
    except Exception:  # noqa: BLE001 - outside a Streamlit run there is no config
        base = None
    return "light" if base == "light" else "dark"


def tokens(theme: str | None = None) -> dict:
    return THEMES[theme or active_theme()]


def series(theme: str | None = None) -> list[str]:
    return list(tokens(theme)["series"])


def carrier_colors(theme: str | None = None) -> dict[str, str]:
    """Carrier -> hex for the active theme. Unknown carriers take the 'Other' slot."""
    t = tokens(theme)
    return {c: t["series"][i] for i, c in enumerate(CARRIER_ORDER)}


def color_for(carrier: str, theme: str | None = None) -> str:
    return carrier_colors(theme).get(carrier, tokens(theme)["series_other"])


def seq_colorscale(theme: str | None = None) -> list[list]:
    steps = tokens(theme)["seq"]
    return [[i / (len(steps) - 1), c] for i, c in enumerate(steps)]


# Kept for callers that predate the theme split. Dark is the default theme.
SERIES = DARK["series"]
CARRIER_COLORS = {c: SERIES[i] for i, c in enumerate(CARRIER_ORDER)}


# --- CSS -------------------------------------------------------------------

def _token_block(t: dict) -> str:
    s = [f"  --fo-series-{i + 1}: {c};" for i, c in enumerate(t["series"])]
    q = [f"  --fo-seq-{i + 1}: {c};" for i, c in enumerate(t["seq"])]
    return "\n".join([
        ":root {",
        f"  --fo-font-display: {FONT_DISPLAY};",
        f"  --fo-font-ui: {FONT_UI};",
        f"  --fo-font-mono: {FONT_MONO};",
        "  --fo-text-2xs: 11px; --fo-text-xs: 12px; --fo-text-sm: 13px; --fo-text-md: 14px; --fo-text-lg: 17px;",
        "  --fo-text-xl: 20px; --fo-text-2xl: 24px; --fo-text-3xl: 29px; --fo-text-4xl: 35px; --fo-text-5xl: 42px;",
        "  --fo-leading-2xs: 16px; --fo-leading-xs: 16px; --fo-leading-sm: 20px; --fo-leading-md: 20px; --fo-leading-lg: 24px;",
        "  --fo-leading-xl: 28px; --fo-leading-2xl: 32px; --fo-leading-3xl: 36px; --fo-leading-4xl: 40px; --fo-leading-5xl: 48px;",
        f"  --fo-weight-body: {t['weight_body']}; --fo-weight-regular: 400; --fo-weight-medium: 500; --fo-weight-semibold: 600;",
        "  --fo-tracking-tight: -0.02em; --fo-tracking-snug: -0.01em; --fo-tracking-wide: 0.08em;",
        "  --fo-space-1: 4px; --fo-space-2: 8px; --fo-space-3: 12px; --fo-space-4: 16px; --fo-space-5: 20px;",
        "  --fo-space-6: 24px; --fo-space-8: 32px; --fo-space-10: 40px; --fo-space-12: 48px; --fo-space-16: 64px;",
        "  --fo-radius-1: 3px; --fo-radius-2: 6px; --fo-radius-pill: 999px;",
        "  --fo-border-hairline: 1px; --fo-border-control: 1px; --fo-border-focus: 2px; --fo-focus-offset: 2px;",
        "  --fo-duration-instant: 80ms; --fo-duration-short: 160ms; --fo-duration-medium: 240ms; --fo-duration-enter: 320ms; --fo-stagger: 40ms;",
        "  --fo-ease-standard: cubic-bezier(0.2, 0, 0, 1); --fo-ease-exit: cubic-bezier(0.4, 0, 1, 1);",
        "  --fo-icon-sm: 16px; --fo-icon-md: 20px; --fo-icon-lg: 24px;",
        "  --fo-content-max: 1360px; --fo-gutter: 16px; --fo-margin: 24px;",
        "  --fo-control-height: 36px; --fo-control-height-sm: 28px; --fo-row-height: 32px; --fo-row-height-compact: 28px;",
        f"  --fo-plane: {t['plane']}; --fo-surface: {t['surface']}; --fo-raised: {t['raised']};",
        f"  --fo-surface-hover: {t['surface_hover']}; --fo-surface-pressed: {t['surface_pressed']};",
        f"  --fo-line-hairline: {t['line_hairline']}; --fo-line-control: {t['line_control']}; --fo-line-strong: {t['line_strong']};",
        f"  --fo-ink: {t['ink']}; --fo-ink-secondary: {t['ink_secondary']}; --fo-ink-muted: {t['ink_muted']};",
        f"  --fo-ink-inverse: {t['ink_inverse']}; --fo-ink-link: {t['ink_link']};",
        f"  --fo-accent: {t['accent']}; --fo-accent-hover: {t['accent_hover']}; --fo-accent-active: {t['accent_active']};",
        f"  --fo-accent-tint: {t['accent_tint']}; --fo-accent-selection: {t['accent_selection']}; --fo-focus: {t['focus']};",
        f"  --fo-action-primary-fill: {t['action_fill']}; --fo-action-primary-fill-hover: {t['action_fill_hover']};",
        f"  --fo-action-primary-fill-active: {t['action_fill_active']}; --fo-action-primary-ink: {t['action_ink']};",
        f"  --fo-status-good-fill: {t['good_fill']}; --fo-status-good-ink: {t['good_ink']}; --fo-status-good-tint: {t['good_tint']};",
        f"  --fo-status-warning-fill: {t['warning_fill']}; --fo-status-warning-ink: {t['warning_ink']}; --fo-status-warning-tint: {t['warning_tint']};",
        f"  --fo-status-serious-fill: {t['serious_fill']}; --fo-status-serious-ink: {t['serious_ink']}; --fo-status-serious-tint: {t['serious_tint']};",
        f"  --fo-status-critical-fill: {t['critical_fill']}; --fo-status-critical-ink: {t['critical_ink']}; --fo-status-critical-tint: {t['critical_tint']};",
        f"  --fo-status-neutral-ink: {t['neutral_ink']}; --fo-status-neutral-tint: {t['neutral_tint']};",
        *s,
        f"  --fo-series-other: {t['series_other']};",
        *q,
        f"  --fo-chart-grid: {t['line_hairline']}; --fo-chart-baseline: {t['line_strong']}; --fo-chart-tick-ink: {t['ink_secondary']};",
        f"  --fo-shadow-1: {t['shadow_1']}; --fo-shadow-2: {t['shadow_2']};",
        "}",
    ])


# Component CSS. Selectors on data-testid and data-baseweb are Streamlit
# 1.50.0's and are semi-stable; the version is pinned in requirements.txt, so
# treat any upgrade as a visual regression event.
COMPONENT_CSS = r"""
@media (prefers-reduced-motion: reduce) {
  :root { --fo-duration-instant: 0ms; --fo-duration-short: 0ms; --fo-duration-medium: 0ms; --fo-duration-enter: 0ms; }
}

/* ---- page ---- */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: var(--fo-plane); }
[data-testid="stHeader"] { background: var(--fo-plane); }
.stApp, .stApp p, .stApp li, .stApp label, .stApp input { font-family: var(--fo-font-ui); }
.stApp { color: var(--fo-ink); font-weight: var(--fo-weight-body); }
.block-container { max-width: var(--fo-content-max); padding: var(--fo-space-6) var(--fo-margin) var(--fo-space-12); }
[data-testid="stVerticalBlock"] { gap: var(--fo-space-4); }
[data-testid="stHorizontalBlock"] { gap: var(--fo-gutter); }
[data-testid="stMarkdownContainer"] p { margin-bottom: 0; }
h1, h2, h3, .stApp h1, .stApp h2, .stApp h3 { font-family: var(--fo-font-display); letter-spacing: var(--fo-tracking-snug); color: var(--fo-ink); }
.stApp a, .stApp a:visited { color: var(--fo-ink-link); }
svg.fo-ic { width: var(--fo-icon-sm); height: var(--fo-icon-sm); fill: none; stroke: currentColor; stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; flex: none; vertical-align: -3px; }
svg.fo-ic.md { width: var(--fo-icon-md); height: var(--fo-icon-md); }
svg.fo-ic.lg { width: var(--fo-icon-lg); height: var(--fo-icon-lg); }
.fo-vh { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0; }
.fo-num { font-family: var(--fo-font-mono); font-variant-numeric: tabular-nums lining-nums; }
:where(button, input, select, textarea, a, summary, [role="tab"], [role="radio"], [tabindex]):focus-visible { outline: var(--fo-border-focus) solid var(--fo-focus) !important; outline-offset: var(--fo-focus-offset); box-shadow: none !important; }

/* ---- sidebar ---- */
[data-testid="stSidebar"] { background: var(--fo-surface); border-right: var(--fo-border-hairline) solid var(--fo-line-hairline); }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: var(--fo-space-3); }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { font: var(--fo-weight-semibold) var(--fo-text-lg)/var(--fo-leading-lg) var(--fo-font-ui); }
/* Long file names in a 336 px sidebar: one line, ellipsis, full name in the title attribute Streamlit sets. */
[data-testid="stSidebar"] button[data-testid="stBaseButton-tertiary"] { max-width: 100%; justify-content: flex-start; }
[data-testid="stSidebar"] button[data-testid="stBaseButton-tertiary"] p { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; }
.stApp .fo-mast__title a, .stApp .fo-finding__claim a, .stApp .fo-section__title a, .stApp .fo-card__title a { display: none !important; }

/* ---- masthead, running header, summary ---- */
.fo-mast__over { display: flex; gap: var(--fo-space-3); align-items: center; font: var(--fo-weight-medium) var(--fo-text-2xs)/var(--fo-leading-2xs) var(--fo-font-ui); letter-spacing: var(--fo-tracking-wide); text-transform: uppercase; color: var(--fo-ink-secondary); margin-bottom: var(--fo-space-2); }
.fo-mast__over i { width: 1px; height: 10px; background: var(--fo-line-control); display: inline-block; }
.fo-mast__title { font: var(--fo-weight-semibold) var(--fo-text-2xl)/var(--fo-leading-2xl) var(--fo-font-display); letter-spacing: var(--fo-tracking-snug); color: var(--fo-ink); margin: 0; }
[data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] > [data-testid="stMarkdownContainer"] > .fo-cond) { position: sticky; top: 3.75rem; z-index: 5; }
.fo-cond { display: flex; flex-wrap: wrap; align-items: center; gap: var(--fo-space-1) var(--fo-space-5); background: var(--fo-plane); border-top: var(--fo-border-hairline) solid var(--fo-line-hairline); border-bottom: var(--fo-border-hairline) solid var(--fo-line-hairline); padding: var(--fo-space-2) 0; color: var(--fo-ink-secondary); font-size: var(--fo-text-xs); line-height: var(--fo-leading-xs); }
.fo-cond b { color: var(--fo-ink); font-weight: var(--fo-weight-medium); }
.fo-cond__f { margin-left: auto; font: var(--fo-weight-semibold) var(--fo-text-lg)/var(--fo-leading-lg) var(--fo-font-display); letter-spacing: var(--fo-tracking-snug); font-variant-numeric: tabular-nums; color: var(--fo-ink); }
.fo-cond__f .fo-unit { font-size: var(--fo-text-xs); }
.fo-over { font: var(--fo-weight-medium) var(--fo-text-2xs)/var(--fo-leading-2xs) var(--fo-font-ui); letter-spacing: var(--fo-tracking-wide); text-transform: uppercase; color: var(--fo-ink-secondary); margin: 0 0 var(--fo-space-3); }
.fo-hero { font: var(--fo-weight-semibold) var(--fo-text-5xl)/var(--fo-leading-5xl) var(--fo-font-display); letter-spacing: var(--fo-tracking-tight); font-variant-numeric: tabular-nums lining-nums; white-space: nowrap; color: var(--fo-ink); margin: 0; }
.fo-hero .fo-unit { font-size: var(--fo-text-xl); margin-right: var(--fo-space-2); }
.fo-hero-label { font: var(--fo-weight-medium) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); margin: var(--fo-space-2) 0 0; color: var(--fo-ink); }
.fo-hero-basis { color: var(--fo-ink-secondary); font-size: var(--fo-text-xs); line-height: var(--fo-leading-xs); margin: 2px 0 0; }
.fo-comp { margin-top: var(--fo-space-5); }
.fo-comp__bar { display: flex; height: 10px; gap: 1px; border-radius: 2px; overflow: hidden; }
.fo-comp__bar i { display: block; height: 100%; }
.fo-comp__legend { display: flex; flex-wrap: wrap; gap: var(--fo-space-1) var(--fo-space-4); margin-top: var(--fo-space-2); font-size: var(--fo-text-xs); line-height: var(--fo-leading-xs); color: var(--fo-ink-secondary); }
.fo-comp__legend i { display: inline-block; width: 8px; height: 8px; border-radius: 1px; margin-right: 6px; }
.fo-comp__legend .fo-num { color: var(--fo-ink); margin-left: 4px; }
.fo-lead { font: var(--fo-weight-body) var(--fo-text-lg)/var(--fo-leading-lg) var(--fo-font-ui); max-width: 66ch; color: var(--fo-ink); margin: 0 0 var(--fo-space-3); text-wrap: pretty; }
.fo-lead b { font-weight: var(--fo-weight-semibold); }
.fo-summary-foot { color: var(--fo-ink-secondary); font-size: var(--fo-text-xs); line-height: var(--fo-leading-xs); margin: var(--fo-space-2) 0 0; }
.fo-summary-foot b { color: var(--fo-ink); font-weight: var(--fo-weight-medium); }
.fo-unit { font-size: var(--fo-text-lg); font-weight: var(--fo-weight-medium); letter-spacing: 0; color: var(--fo-ink-secondary); margin-right: var(--fo-space-1); }

/* ---- KPI tile ---- */
.fo-kpi { background: var(--fo-surface); border: var(--fo-border-hairline) solid var(--fo-line-hairline); border-radius: var(--fo-radius-2); padding: var(--fo-space-4) var(--fo-space-5); min-height: 112px; display: flex; flex-direction: column; gap: var(--fo-space-2); }
.fo-kpi__label { display: flex; align-items: center; gap: var(--fo-space-2); font: var(--fo-weight-medium) var(--fo-text-2xs)/var(--fo-leading-2xs) var(--fo-font-ui); letter-spacing: var(--fo-tracking-wide); text-transform: uppercase; color: var(--fo-ink-secondary); }
.fo-kpi__mark { display: inline-flex; align-items: center; gap: 4px; letter-spacing: 0; text-transform: none; font-size: var(--fo-text-xs); margin-left: auto; }
.fo-kpi__row { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--fo-space-3); }
.fo-kpi__value { font: var(--fo-weight-semibold) var(--fo-text-4xl)/var(--fo-leading-4xl) var(--fo-font-display); letter-spacing: var(--fo-tracking-tight); font-variant-numeric: tabular-nums lining-nums; color: var(--fo-ink); white-space: nowrap; }
.fo-kpi__delta { display: flex; align-items: center; gap: var(--fo-space-1); font: var(--fo-weight-regular) var(--fo-text-xs)/var(--fo-leading-xs) var(--fo-font-mono); font-variant-numeric: tabular-nums; color: var(--fo-ink-secondary); }
.fo-kpi__basis { font-family: var(--fo-font-ui); color: var(--fo-ink-secondary); margin-left: var(--fo-space-1); }
.fo-kpi__note { font: var(--fo-weight-regular) var(--fo-text-xs)/var(--fo-leading-xs) var(--fo-font-ui); color: var(--fo-ink-secondary); margin: 0; }
.fo-kpi__absent { font: var(--fo-weight-medium) var(--fo-text-md)/var(--fo-leading-4xl) var(--fo-font-ui); color: var(--fo-ink-muted); }
.fo-spark { width: 96px; height: 30px; flex: none; overflow: visible; }
.fo-spark path { fill: none; stroke: var(--fo-ink-muted); stroke-width: 1.5; stroke-linejoin: round; stroke-linecap: round; }
.fo-spark circle { fill: var(--fo-ink); stroke: var(--fo-surface); stroke-width: 1.5; }
.fo-spark line { stroke: var(--fo-line-control); stroke-dasharray: 2 3; }
.fo-good { color: var(--fo-status-good-ink); } .fo-warning { color: var(--fo-status-warning-ink); }
.fo-serious { color: var(--fo-status-serious-ink); } .fo-critical { color: var(--fo-status-critical-ink); }
@media (max-width: 1023px) { .fo-kpi__value { font-size: var(--fo-text-2xl); line-height: var(--fo-leading-2xl); letter-spacing: var(--fo-tracking-snug); } }

/* ---- section, card ---- */
.fo-section { display: flex; align-items: baseline; gap: var(--fo-space-3); padding-bottom: var(--fo-space-2); border-bottom: var(--fo-border-hairline) solid var(--fo-line-hairline); margin: var(--fo-space-6) 0 0; }
.fo-section__title { font: var(--fo-weight-medium) var(--fo-text-xl)/var(--fo-leading-xl) var(--fo-font-display); letter-spacing: var(--fo-tracking-snug); color: var(--fo-ink); margin: 0; }
.fo-section__meta { color: var(--fo-ink-secondary); font-size: var(--fo-text-xs); margin-left: auto; text-align: right; }
/* st.container(border=True) puts its border on the stVerticalBlock itself in 1.50, with nothing else to
   select on, so every card opens with an invisible marker element and the card is the block that owns it. */
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] > [data-testid="stMarkdown"] > [data-testid="stMarkdownContainer"] > .fo-card-mark) { background: var(--fo-surface); border: var(--fo-border-hairline) solid var(--fo-line-hairline) !important; border-radius: var(--fo-radius-2); padding: var(--fo-space-4) var(--fo-space-5); gap: var(--fo-space-3); }
[data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] > [data-testid="stMarkdownContainer"] > .fo-card-mark) { display: none; }
/* Streamlit decorates every heading with an anchor link. A briefing is not a wiki. */
[data-testid="stHeaderActionElements"], .stApp h1 > a, .stApp h2 > a, .stApp h3 > a { display: none !important; }
.fo-card__title { font: var(--fo-weight-semibold) var(--fo-text-lg)/var(--fo-leading-lg) var(--fo-font-ui); color: var(--fo-ink); margin: 0; }
.fo-card__sub { font: var(--fo-weight-regular) var(--fo-text-xs)/var(--fo-leading-xs) var(--fo-font-ui); color: var(--fo-ink-secondary); margin: var(--fo-space-1) 0 0; }
.fo-caption { font: var(--fo-weight-regular) var(--fo-text-xs)/var(--fo-leading-xs) var(--fo-font-ui); color: var(--fo-ink-secondary); margin: 0; }
.fo-caption b { color: var(--fo-ink); font-weight: var(--fo-weight-medium); }
.fo-empty { min-height: 200px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--fo-space-2); color: var(--fo-ink-secondary); text-align: center; }
.fo-empty .fo-ic { color: var(--fo-ink-muted); }
.fo-space-4 { height: var(--fo-space-4); } .fo-space-6 { height: var(--fo-space-6); } .fo-space-8 { height: var(--fo-space-8); }

/* ---- badge, meter ---- */
.fo-badge { display: inline-flex; align-items: center; gap: var(--fo-space-1); height: 20px; padding: 0 var(--fo-space-2); border-radius: var(--fo-radius-1); border: var(--fo-border-hairline) solid; font: var(--fo-weight-medium) var(--fo-text-xs)/var(--fo-leading-xs) var(--fo-font-ui); color: var(--fo-ink); white-space: nowrap; vertical-align: middle; }
.fo-badge .fo-ic { width: 12px; height: 12px; vertical-align: 0; }
.fo-badge--neutral { background: var(--fo-status-neutral-tint); border-color: var(--fo-line-hairline); }
.fo-badge--good { background: var(--fo-status-good-tint); border-color: var(--fo-status-good-ink); } .fo-badge--good .fo-ic { color: var(--fo-status-good-ink); }
.fo-badge--warning { background: var(--fo-status-warning-tint); border-color: var(--fo-status-warning-ink); } .fo-badge--warning .fo-ic { color: var(--fo-status-warning-ink); }
.fo-badge--serious { background: var(--fo-status-serious-tint); border-color: var(--fo-status-serious-ink); } .fo-badge--serious .fo-ic { color: var(--fo-status-serious-ink); }
.fo-badge--critical { background: var(--fo-status-critical-tint); border-color: var(--fo-status-critical-ink); } .fo-badge--critical .fo-ic { color: var(--fo-status-critical-ink); }
.fo-badge--count { background: var(--fo-raised); border-color: transparent; font-family: var(--fo-font-mono); font-variant-numeric: tabular-nums; }
.fo-meter { margin-top: var(--fo-space-4); max-width: 260px; }
.fo-meter__track { position: relative; height: 4px; background: var(--fo-line-hairline); border-radius: 2px; }
.fo-meter__fill { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 2px; background: var(--fo-ink-secondary); }
.fo-meter__fill.fo-critical { background: var(--fo-status-critical-ink); } .fo-meter__fill.fo-serious { background: var(--fo-status-serious-ink); }
.fo-meter__fill.fo-warning { background: var(--fo-status-warning-ink); } .fo-meter__fill.fo-good { background: var(--fo-status-good-ink); }
.fo-meter__tick { position: absolute; top: -3px; width: 1px; height: 10px; background: var(--fo-line-control); }
.fo-meter__label { font-size: var(--fo-text-xs); line-height: var(--fo-leading-xs); color: var(--fo-ink-secondary); margin: var(--fo-space-2) 0 0; }
.fo-meter__label b { color: var(--fo-ink); font-weight: var(--fo-weight-medium); }

/* ---- alert ---- */
.fo-alert { display: grid; grid-template-columns: 20px 1fr; gap: var(--fo-space-3); padding: var(--fo-space-3) var(--fo-space-4); border-radius: var(--fo-radius-2); border: var(--fo-border-hairline) solid; align-items: start; }
.fo-alert .fo-ic { width: var(--fo-icon-md); height: var(--fo-icon-md); }
.fo-alert__title { font: var(--fo-weight-semibold) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); color: var(--fo-ink); margin: 0; }
.fo-alert__body { font: var(--fo-weight-body) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); color: var(--fo-ink); margin: var(--fo-space-1) 0 0; }
.fo-alert--neutral { background: var(--fo-status-neutral-tint); border-color: var(--fo-line-hairline); } .fo-alert--neutral .fo-ic { color: var(--fo-status-neutral-ink); }
.fo-alert--good { background: var(--fo-status-good-tint); border-color: var(--fo-status-good-ink); } .fo-alert--good .fo-ic { color: var(--fo-status-good-ink); }
.fo-alert--warning { background: var(--fo-status-warning-tint); border-color: var(--fo-status-warning-ink); } .fo-alert--warning .fo-ic { color: var(--fo-status-warning-ink); }
.fo-alert--serious { background: var(--fo-status-serious-tint); border-color: var(--fo-status-serious-ink); } .fo-alert--serious .fo-ic { color: var(--fo-status-serious-ink); }
.fo-alert--critical { background: var(--fo-status-critical-tint); border-color: var(--fo-status-critical-ink); } .fo-alert--critical .fo-ic { color: var(--fo-status-critical-ink); }
[data-testid="stAlert"] { border-radius: var(--fo-radius-2); }

/* ---- table ---- */
.fo-table-wrap { overflow-x: auto; max-height: 480px; overflow-y: auto; border: var(--fo-border-hairline) solid var(--fo-line-hairline); border-radius: var(--fo-radius-1); }
.fo-table { width: 100%; border-collapse: collapse; font: var(--fo-weight-body) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); color: var(--fo-ink); margin: 0; }
.fo-table th { position: sticky; top: 0; z-index: 1; background: var(--fo-raised); color: var(--fo-ink-secondary); font-weight: var(--fo-weight-medium); text-align: left; height: var(--fo-row-height); padding: 0 var(--fo-space-3); border-bottom: var(--fo-border-hairline) solid var(--fo-line-hairline); white-space: nowrap; }
.fo-table td { height: var(--fo-row-height); padding: 0 var(--fo-space-3); border-bottom: var(--fo-border-hairline) solid var(--fo-line-hairline); vertical-align: middle; white-space: nowrap; max-width: 320px; overflow: hidden; text-overflow: ellipsis; }
.fo-table tbody tr:hover td { background: var(--fo-surface-hover); }
.fo-table .fo-num { font-size: var(--fo-text-sm); text-align: right; }
.fo-table .fo-date { font-family: var(--fo-font-mono); font-size: var(--fo-text-sm); }
.fo-table tfoot td { font-weight: var(--fo-weight-medium); border-top: var(--fo-border-hairline) solid var(--fo-line-strong); border-bottom: 0; }
.fo-table--compact th, .fo-table--compact td { height: var(--fo-row-height-compact); }
.fo-table td.fo-cite { background: var(--fo-accent-tint); font-weight: var(--fo-weight-medium); }
[data-testid="stDataFrame"] { border-radius: var(--fo-radius-1); }

/* ---- finding ---- */
.fo-finding__head { display: flex; align-items: center; gap: var(--fo-space-3); margin-bottom: var(--fo-space-3); }
.fo-finding__num { font: var(--fo-weight-medium) var(--fo-text-2xs)/var(--fo-leading-2xs) var(--fo-font-display); letter-spacing: var(--fo-tracking-wide); color: var(--fo-ink-secondary); font-variant-numeric: tabular-nums; }
.fo-finding__kind { font: var(--fo-weight-medium) var(--fo-text-2xs)/var(--fo-leading-2xs) var(--fo-font-ui); letter-spacing: var(--fo-tracking-wide); text-transform: uppercase; color: var(--fo-ink-secondary); }
.fo-finding__claim { font: var(--fo-weight-medium) var(--fo-text-xl)/var(--fo-leading-xl) var(--fo-font-display); letter-spacing: var(--fo-tracking-snug); color: var(--fo-ink); margin: 0 0 var(--fo-space-3); max-width: 62ch; text-wrap: balance; }
.fo-finding__support { font: var(--fo-weight-body) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); color: var(--fo-ink); margin: 0 0 var(--fo-space-2); max-width: 68ch; }
.fo-finding__action-lead { font: var(--fo-weight-medium) var(--fo-text-2xs)/var(--fo-leading-2xs) var(--fo-font-ui); letter-spacing: var(--fo-tracking-wide); text-transform: uppercase; color: var(--fo-ink-secondary); margin: var(--fo-space-4) 0 var(--fo-space-1); }
.fo-finding__action { font: var(--fo-weight-semibold) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); color: var(--fo-ink); margin: 0; max-width: 68ch; }
.fo-finding__figure { font: var(--fo-weight-semibold) var(--fo-text-3xl)/var(--fo-leading-3xl) var(--fo-font-display); letter-spacing: var(--fo-tracking-snug); font-variant-numeric: tabular-nums lining-nums; color: var(--fo-ink); margin: 0; white-space: nowrap; }
.fo-finding__figure-label, .fo-finding__figure-basis { font: var(--fo-weight-regular) var(--fo-text-xs)/var(--fo-leading-xs) var(--fo-font-ui); color: var(--fo-ink-secondary); margin: var(--fo-space-1) 0 0; }

/* ---- Streamlit widgets ---- */
button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-secondary"], button[data-testid="stBaseButton-tertiary"] {
  min-height: var(--fo-control-height); height: var(--fo-control-height); padding: 0 var(--fo-space-4); border-radius: var(--fo-radius-1);
  font: var(--fo-weight-medium) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui);
  transition: background-color var(--fo-duration-instant) var(--fo-ease-standard), border-color var(--fo-duration-instant) var(--fo-ease-standard), color var(--fo-duration-instant) var(--fo-ease-standard);
}
button[data-testid="stBaseButton-primary"] { background: var(--fo-action-primary-fill); color: var(--fo-action-primary-ink); border: none; }
button[data-testid="stBaseButton-primary"]:hover { background: var(--fo-action-primary-fill-hover); color: var(--fo-action-primary-ink); }
button[data-testid="stBaseButton-primary"]:active { background: var(--fo-action-primary-fill-active); }
button[data-testid="stBaseButton-primary"]:disabled { background: var(--fo-raised); color: var(--fo-ink-muted); border: var(--fo-border-control) solid var(--fo-line-hairline); cursor: not-allowed; }
button[data-testid="stBaseButton-secondary"] { background: transparent; color: var(--fo-ink); border: var(--fo-border-control) solid var(--fo-line-control); }
button[data-testid="stBaseButton-secondary"]:hover { background: var(--fo-surface-hover); border-color: var(--fo-line-strong); color: var(--fo-ink); }
button[data-testid="stBaseButton-secondary"]:active { background: var(--fo-surface-pressed); }
button[data-testid="stBaseButton-secondary"]:disabled { color: var(--fo-ink-muted); border-color: var(--fo-line-hairline); cursor: not-allowed; }
button[data-testid="stBaseButton-tertiary"] { background: transparent; color: var(--fo-ink-link); border: none; padding: 0 var(--fo-space-2); }
button[data-testid="stBaseButton-tertiary"]:hover { text-decoration: underline; text-underline-offset: 3px; color: var(--fo-ink-link); background: transparent; }
button[data-testid="stBaseButton-tertiary"]:active { color: var(--fo-accent-active); }
button[data-testid="stBaseButton-tertiary"]:disabled { color: var(--fo-ink-muted); text-decoration: none; cursor: not-allowed; }
.fo-compact button[data-testid^="stBaseButton-"] { height: var(--fo-control-height-sm); min-height: var(--fo-control-height-sm); padding: 0 var(--fo-space-3); font-size: var(--fo-text-xs); line-height: var(--fo-leading-xs); }

[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label { font: var(--fo-weight-medium) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); color: var(--fo-ink); }
[data-testid="stTextInput"] [data-baseweb="input"], [data-testid="stNumberInput"] [data-baseweb="input"], [data-testid="stDateInput"] [data-baseweb="input"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div, [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
  background: var(--fo-raised); border: var(--fo-border-control) solid var(--fo-line-control); border-radius: var(--fo-radius-1); min-height: var(--fo-control-height);
  color: var(--fo-ink); font: var(--fo-weight-body) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui);
  transition: border-color var(--fo-duration-instant) var(--fo-ease-standard);
}
[data-testid="stDateInput"] input { font-family: var(--fo-font-mono); font-variant-numeric: tabular-nums; }
[data-baseweb="input"]:hover, [data-baseweb="select"] > div:hover { border-color: var(--fo-line-strong); }
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within { border-color: var(--fo-accent); }
[data-baseweb="input"] input::placeholder { color: var(--fo-ink-secondary); opacity: 1; }
[data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="popover"] [data-baseweb="calendar"], [data-baseweb="popover"] > div { background: var(--fo-raised); box-shadow: var(--fo-shadow-1); border-radius: var(--fo-radius-2); }
[data-baseweb="menu"] [role="option"] { min-height: 32px; color: var(--fo-ink); }
[data-baseweb="menu"] [role="option"]:hover { background: var(--fo-surface-hover); }
[data-baseweb="menu"] [role="option"][aria-selected="true"] { background: var(--fo-accent-selection); }
[data-baseweb="tag"] { background: var(--fo-accent-tint) !important; border: var(--fo-border-hairline) solid var(--fo-line-hairline); border-radius: var(--fo-radius-1); color: var(--fo-ink) !important; height: 24px; font-size: var(--fo-text-xs); }
[data-baseweb="tag"] span { color: var(--fo-ink) !important; }
[data-baseweb="tag"]:hover { background: var(--fo-accent-selection) !important; }
[data-testid="stMultiSelect"] [data-baseweb="select"] > div > div:first-child { max-height: 36px; overflow: hidden; }

[data-testid="stButtonGroup"] [data-baseweb="button-group"] { border: var(--fo-border-control) solid var(--fo-line-control); border-radius: var(--fo-radius-1); background: transparent; padding: 0; gap: 0; overflow: hidden; display: inline-flex; flex-wrap: nowrap; }
button[data-testid="stBaseButton-segmented_control"], button[data-testid="stBaseButton-segmented_controlActive"] { height: calc(var(--fo-control-height) - 2px); min-height: 0; border: none !important; border-radius: 0 !important; color: var(--fo-ink-secondary); background: transparent; font: var(--fo-weight-medium) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); box-shadow: none; padding: 0 var(--fo-space-3); margin: 0; transition: background-color var(--fo-duration-instant) var(--fo-ease-standard), color var(--fo-duration-instant) var(--fo-ease-standard); }
[data-baseweb="button-group"] button + button { border-left: var(--fo-border-hairline) solid var(--fo-line-hairline) !important; }
button[data-testid="stBaseButton-segmented_control"]:hover { background: var(--fo-surface-hover); color: var(--fo-ink); }
button[data-testid="stBaseButton-segmented_controlActive"], button[data-testid="stBaseButton-segmented_controlActive"]:hover { background: var(--fo-raised); color: var(--fo-ink); box-shadow: inset 0 -2px 0 0 var(--fo-accent); }
button[data-testid^="stBaseButton-segmented_control"] p { font-size: var(--fo-text-md); color: inherit; }
button[data-testid="stBaseButton-segmented_control"]:disabled, button[data-testid="stBaseButton-segmented_controlActive"]:disabled { color: var(--fo-ink-muted); box-shadow: none; }
/* Chart / Table controls inside card headers are the small size and sit right. */
[data-testid="stColumn"]:has(> [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] .fo-compact) [data-testid="stButtonGroup"] { display: flex; justify-content: flex-end; }
[data-testid="stColumn"]:has(> [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] .fo-compact) button[data-testid^="stBaseButton-segmented_control"] { height: 26px; padding: 0 var(--fo-space-2); }
[data-testid="stColumn"]:has(> [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] .fo-compact) button[data-testid^="stBaseButton-segmented_control"] p { font-size: var(--fo-text-xs); }
[data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] > [data-testid="stMarkdownContainer"] > .fo-compact) { display: none; }

[data-testid="stRadio"] [role="radiogroup"] { gap: var(--fo-space-1); }
[data-testid="stRadio"] label { font: var(--fo-weight-body) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); color: var(--fo-ink); }

[data-baseweb="tab-list"] { gap: var(--fo-space-6); border-bottom: var(--fo-border-hairline) solid var(--fo-line-hairline); }
[data-baseweb="tab"] { height: 40px; padding: 0 !important; background: transparent !important; color: var(--fo-ink-secondary); font: var(--fo-weight-medium) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); }
[data-baseweb="tab"] p { font-size: var(--fo-text-md); }
[data-baseweb="tab"]:hover { color: var(--fo-ink); box-shadow: inset 0 -2px 0 0 var(--fo-line-strong); }
[data-baseweb="tab"][aria-selected="true"] { color: var(--fo-ink); }
[data-baseweb="tab-highlight"] { background: var(--fo-accent); height: 2px; }
[data-baseweb="tab-border"] { display: none; }
[data-baseweb="tab-panel"] { padding-top: var(--fo-space-4); }

[data-testid="stExpander"] { border: none !important; border-top: var(--fo-border-hairline) solid var(--fo-line-hairline) !important; border-radius: 0 !important; background: transparent; }
[data-testid="stExpander"] details { border: none; background: transparent; }
[data-testid="stExpander"] summary { height: 40px; padding: 0; font: var(--fo-weight-medium) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); color: var(--fo-ink); }
[data-testid="stExpander"] summary p { font-size: var(--fo-text-md); font-weight: var(--fo-weight-medium); }
[data-testid="stExpander"] summary:hover { background: var(--fo-surface-hover); color: var(--fo-ink); }
/* Streamlit draws the expander chevron with its Material icon font. One icon style per page, so it is
   replaced by the system's stroke chevron, masked so it takes the ink token. */
[data-testid="stExpander"] summary [data-testid="stIconMaterial"], [data-testid="stExpander"] summary > span > span:has(> [data-testid="stIconMaterial"]) { display: none; }
[data-testid="stExpander"] summary > span::before { content: ""; display: inline-block; flex: none; width: 16px; height: 16px; margin-right: var(--fo-space-2); background: var(--fo-ink-secondary); -webkit-mask: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='M9 6l6 6-6 6'/></svg>") center / contain no-repeat; mask: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='M9 6l6 6-6 6'/></svg>") center / contain no-repeat; transition: transform var(--fo-duration-short) var(--fo-ease-standard); }
[data-testid="stExpander"] details[open] summary > span::before { transform: rotate(90deg); }
[data-testid="stExpanderDetails"] { padding: var(--fo-space-3) 0 0; }

[data-testid="stFileUploaderDropzone"] { background: var(--fo-raised); border: var(--fo-border-control) dashed var(--fo-line-control); border-radius: var(--fo-radius-2); min-height: 120px; padding: var(--fo-space-4); transition: background-color var(--fo-duration-instant) var(--fo-ease-standard), border-color var(--fo-duration-instant) var(--fo-ease-standard); }
[data-testid="stFileUploaderDropzone"]:hover { background: var(--fo-accent-tint); border-color: var(--fo-accent); }
[data-testid="stFileUploaderDropzoneInstructions"] span, [data-testid="stFileUploaderDropzoneInstructions"] div { color: var(--fo-ink); font-family: var(--fo-font-ui); }
[data-testid="stFileUploaderDropzoneInstructions"] small { color: var(--fo-ink-secondary); font-size: var(--fo-text-xs); }
[data-testid="stFileUploaderFile"] { min-height: var(--fo-row-height); border-bottom: var(--fo-border-hairline) solid var(--fo-line-hairline); }
[data-testid="stFileUploaderFileName"] { color: var(--fo-ink); }
[data-testid="stFileUploaderFileData"] small { color: var(--fo-ink-secondary); font-family: var(--fo-font-mono); }

[data-testid="stStatusWidget"], [data-testid="stStatus"] { border-radius: var(--fo-radius-2); }
[data-testid="stToast"] { background: var(--fo-raised); color: var(--fo-ink); box-shadow: var(--fo-shadow-2); border-radius: var(--fo-radius-2); font: var(--fo-weight-body) var(--fo-text-md)/var(--fo-leading-md) var(--fo-font-ui); }
[data-testid="stCaptionContainer"] p { color: var(--fo-ink-secondary); font-size: var(--fo-text-xs); line-height: var(--fo-leading-xs); }
[data-testid="stSpinner"] p { color: var(--fo-ink-secondary); }
hr { border-color: var(--fo-line-hairline); margin: var(--fo-space-4) 0; }

@media (max-width: 1023px) {
  .block-container { padding-left: var(--fo-space-4); padding-right: var(--fo-space-4); }
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: calc(50% - var(--fo-gutter) / 2) !important; flex: 1 1 calc(50% - var(--fo-gutter) / 2) !important; }
}
@media (max-width: 767px) {
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 100% !important; flex: 1 1 100% !important; }
}
"""

# The first run of a session settles in, block by block, from a visible resting
# state. On every later rerun the animation is left out, because Streamlit
# re-renders the whole page on each interaction and a filter change is not an
# arrival.
ENTER_CSS = r"""
@keyframes fo-enter { from { opacity: .35; transform: translateY(8px); } to { opacity: 1; transform: none; } }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] > * { animation: fo-enter var(--fo-duration-enter) var(--fo-ease-standard) both; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] > :nth-child(2) { animation-delay: calc(1 * var(--fo-stagger)); }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] > :nth-child(3) { animation-delay: calc(2 * var(--fo-stagger)); }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] > :nth-child(4) { animation-delay: calc(3 * var(--fo-stagger)); }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] > :nth-child(5) { animation-delay: calc(4 * var(--fo-stagger)); }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] > :nth-child(6) { animation-delay: calc(5 * var(--fo-stagger)); }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] > :nth-child(7) { animation-delay: calc(6 * var(--fo-stagger)); }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] > :nth-child(8) { animation-delay: calc(7 * var(--fo-stagger)); }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] > :nth-child(n+9) { animation-delay: calc(8 * var(--fo-stagger)); }
@media (prefers-reduced-motion: reduce) { [data-testid="stMainBlockContainer"] * { animation: none !important; } }
"""


import re as _re

_FO_SELECTOR = _re.compile(r"(^|\}|,)(\s*)\.fo-", _re.M)


def _boost(css_text: str) -> str:
    """Prefix every .fo-* rule with .stApp.

    Streamlit styles markdown paragraphs with a class-plus-element selector
    (specificity 0,1,1), which outranks a bare .fo-class (0,1,0). Adding the
    app root makes every component rule 0,2,0 without touching its intent.
    Selectors inside :has() are untouched because they follow a combinator,
    not a rule boundary.
    """
    return _FO_SELECTOR.sub(lambda m: f"{m.group(1)}{m.group(2)}.stApp .fo-", css_text)


def css(theme: str | None = None, first_run: bool = False) -> str:
    t = tokens(theme)
    parts = [f"@import url('{FONT_IMPORT}');", _token_block(t), _boost(COMPONENT_CSS)]
    if first_run:
        parts.append(ENTER_CSS)
    return "<style>\n" + "\n".join(parts) + "\n</style>"


def inject(theme: str | None = None) -> str:
    """Emit the stylesheet once per run. Returns the theme name in use."""
    import streamlit as st
    theme = theme or active_theme()
    first_run = "fo_booted" not in st.session_state
    st.session_state["fo_booted"] = True
    st.markdown(css(theme, first_run=first_run), unsafe_allow_html=True)
    return theme


# --- Plotly ------------------------------------------------------------------

PLOTLY_CONFIG = {"displayModeBar": False, "displaylogo": False, "responsive": True}


def _template(t: dict) -> go.layout.Template:
    axis_common = dict(
        showline=False, zeroline=False, automargin=True,
        ticks="", ticklen=0,
        tickfont=dict(family=FONT_UI, size=12, color=t["ink_secondary"]),
        title=dict(font=dict(family=FONT_UI, size=12, color=t["ink_secondary"]), standoff=8),
        showspikes=False,
    )
    return go.layout.Template(layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_UI, size=13, color=t["ink"]),
        colorway=t["series"],
        margin=dict(l=8, r=8, t=8, b=8),
        xaxis=dict(axis_common, showgrid=False, showline=True,
                   linecolor=t["line_strong"], linewidth=1),
        yaxis=dict(axis_common, showgrid=True, gridcolor=t["line_hairline"], gridwidth=1, nticks=5,
                   tickfont=dict(family=FONT_MONO, size=12, color=t["ink_secondary"]),
                   rangemode="tozero"),
        legend=dict(orientation="h", x=0, xanchor="left", y=1.0, yanchor="bottom",
                    font=dict(family=FONT_UI, size=12, color=t["ink_secondary"]),
                    bgcolor="rgba(0,0,0,0)", itemclick="toggle", itemdoubleclick=False,
                    itemsizing="constant", tracegroupgap=0, title=None),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=t["raised"], bordercolor=t["line_hairline"],
                        font=dict(family=FONT_MONO, size=12, color=t["ink"]),
                        align="left", namelength=-1),
        hoverdistance=24, spikedistance=-1,
        barcornerradius=2, bargap=0.35, bargroupgap=0.08,
        colorscale=dict(sequential=[[i / 7, c] for i, c in enumerate(t["seq"])]),
        coloraxis=dict(colorbar=dict(thickness=8, len=1, outlinewidth=0, ticks="",
                                     tickfont=dict(family=FONT_MONO, size=11, color=t["ink_secondary"]))),
        annotationdefaults=dict(font=dict(family=FONT_UI, size=12, color=t["ink_secondary"]),
                                showarrow=False),
        uniformtext=dict(minsize=11, mode="hide"),
        transition=dict(duration=0),
    ))


def register_templates() -> None:
    if "fo_dark" not in pio.templates:
        pio.templates["fo_dark"] = _template(DARK)
        pio.templates["fo_light"] = _template(LIGHT)


def plotly_template(theme: str | None = None) -> str:
    register_templates()
    name = f"fo_{theme or active_theme()}"
    pio.templates.default = name
    return name
