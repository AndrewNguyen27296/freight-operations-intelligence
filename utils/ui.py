"""
HTML components of the design system, rendered through st.markdown.

Everything here returns a string of HTML built from the tokens in
utils/theme.py, so a component looks the same wherever it is used. Nothing
here computes a number; callers pass values already formatted by utils/fmt.

Streamlit primitives are used where they exist (containers, expanders,
buttons, segmented controls). HTML is used where Streamlit's own widget cannot
carry the token or the icon: KPI tiles, badges, alerts, findings, tables.
Every icon is stroke SVG on a 24 unit grid at 1.5 unit stroke. There are no
emoji anywhere in this file, and there must never be.
"""

from __future__ import annotations

import html
from typing import Iterable, Sequence

import pandas as pd

from utils import fmt

# --- Icons -------------------------------------------------------------------

_ICON_PATHS = {
    "check-circle": '<circle cx="12" cy="12" r="9"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/>',
    "alert-triangle": '<path d="M12 3.5l9 16H3l9-16z"/><path d="M12 9.5v4.5"/><path d="M12 17h.01"/>',
    "alert-circle": '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5"/><path d="M12 16h.01"/>',
    "alert-octagon": '<path d="M8 3h8l5 5v8l-5 5H8l-5-5V8l5-5z"/><path d="M12 7.5v5"/><path d="M12 16h.01"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/>',
    "chevron-right": '<path d="M9 6l6 6-6 6"/>',
    "chevron-down": '<path d="M6 9l6 6 6-6"/>',
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "upload": '<path d="M12 16V4m0 0l-4 4m4-4l4 4"/><path d="M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3"/>',
    "download": '<path d="M12 4v12m0 0l-4-4m4 4l4-4"/><path d="M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3"/>',
    "file": '<path d="M14 3H7a1 1 0 00-1 1v16a1 1 0 001 1h10a1 1 0 001-1V8l-4-5z"/><path d="M14 3v5h4"/>',
    "table": '<rect x="3.5" y="4.5" width="17" height="15" rx="1"/><path d="M3.5 9.5h17M3.5 14.5h17M9.5 9.5v10"/>',
    "chart": '<path d="M4 20V4"/><path d="M4 20h16"/><path d="M8 16v-5M12 16V8M16 16v-3"/>',
    "filter": '<path d="M4 5h16l-6 7v6l-4 2v-8L4 5z"/>',
    "calendar": '<rect x="3.5" y="5.5" width="17" height="15" rx="1"/><path d="M3.5 10.5h17M8 3.5v4M16 3.5v4"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4 4"/>',
    "arrow-up-right": '<path d="M7 17L17 7"/><path d="M9 7h8v8"/>',
    "arrow-down-right": '<path d="M7 7l10 10"/><path d="M17 9v8H9"/>',
    "minus": '<path d="M6 12h12"/>',
    "refresh": '<path d="M20 12a8 8 0 01-14.5 4.6"/><path d="M4 12a8 8 0 0114.5-4.6"/><path d="M18.5 3.5v4h-4M5.5 20.5v-4h4"/>',
}

STATUS_ICON = {
    "good": "check-circle", "warning": "alert-triangle", "serious": "alert-circle",
    "critical": "alert-octagon", "neutral": "info",
}

STATUS_WORD = {
    "good": "Good", "warning": "Warning", "serious": "Serious",
    "critical": "Critical", "neutral": "Note",
}


def icon(name: str, size: str = "sm", cls: str = "") -> str:
    """Inline stroke icon. `size` is sm (16), md (20) or lg (24)."""
    size_cls = "" if size == "sm" else f" {size}"
    return (f'<svg class="fo-ic{size_cls}{" " + cls if cls else ""}" viewBox="0 0 24 24" '
            f'aria-hidden="true">{_ICON_PATHS[name]}</svg>')


def esc(text) -> str:
    return html.escape(str(text), quote=True)


def vh(text: str) -> str:
    """Visually hidden text for screen readers."""
    return f'<span class="fo-vh">{esc(text)}</span>'


# --- Text blocks -------------------------------------------------------------

def unit(code: str) -> str:
    return f'<span class="fo-unit">{esc(code)}</span>'


def caption(text: str) -> str:
    return f'<p class="fo-caption">{text}</p>'


def spacer(step: int = 4) -> str:
    return f'<div class="fo-space-{step}"></div>'


def overline(text: str) -> str:
    return f'<p class="fo-over">{esc(text)}</p>'


def masthead(kind: str, audience: str | None, build_date: str, title: str) -> str:
    items = [esc(kind)]
    if audience:
        items.append(f"Prepared for {esc(audience)}")
    items.append(f"Build {esc(build_date)}")
    over = "<i></i>".join(f"<span>{i}</span>" for i in items)
    return (f'<div class="fo-mast"><div class="fo-mast__over">{over}</div>'
            f'<h1 class="fo-mast__title">{esc(title)}</h1></div>')


def running_header(meta: Sequence[tuple[str, str]], figure_html: str | None) -> str:
    """The meta strip under the masthead. Sticks to the top when scrolled past.

    Each item is (label, value); the value is set in ink, the label in
    ink-secondary. A `figure_html` on the right keeps the headline number on
    screen while the reader is in the findings.
    """
    parts = "".join(
        f"<span>{esc(label)} <b>{value}</b></span>" if label else f"<span><b>{value}</b></span>"
        for label, value in meta
    )
    fig = f'<span class="fo-cond__f">{figure_html}</span>' if figure_html else ""
    return f'<div class="fo-cond">{parts}{fig}</div>'


def section(title: str, count: int | None = None, meta: str | None = None) -> str:
    badge_html = f'<span class="fo-badge fo-badge--count">{fmt.count(count)}</span>' if count is not None else ""
    meta_html = f'<span class="fo-section__meta">{esc(meta)}</span>' if meta else ""
    return (f'<div class="fo-section"><h2 class="fo-section__title">{esc(title)}</h2>'
            f'{badge_html}{meta_html}</div>')


def card_mark() -> str:
    """The first element inside every st.container(border=True).

    Streamlit 1.50 draws the border on the block itself with nothing else to
    select on, so the stylesheet identifies a card as the block whose first
    child is this marker. The marker's own container is hidden by CSS.
    """
    return '<div class="fo-card-mark"></div>'


def card_head(title: str, sub: str | None = None) -> str:
    sub_html = f'<p class="fo-card__sub">{sub}</p>' if sub else ""
    return f'<h3 class="fo-card__title">{esc(title)}</h3>{sub_html}'


def empty_state(message: str, icon_name: str = "chart") -> str:
    return f'<div class="fo-empty">{icon(icon_name, "lg")}<span>{esc(message)}</span></div>'


# --- Badge, alert, meter ----------------------------------------------------

def badge(kind: str, text: str | None = None, with_icon: bool = True) -> str:
    label = text if text is not None else STATUS_WORD[kind]
    ic = icon(STATUS_ICON[kind]) if with_icon and kind != "neutral" else ""
    return f'<span class="fo-badge fo-badge--{kind}">{ic}{esc(label)}</span>'


def alert(kind: str, title: str, body: str, role: str | None = None) -> str:
    role = role or ("alert" if kind in ("serious", "critical") else "status")
    return (f'<div class="fo-alert fo-alert--{kind}" role="{role}">{icon(STATUS_ICON[kind], "md")}'
            f'<div><p class="fo-alert__title">{esc(title)}</p><p class="fo-alert__body">{body}</p></div></div>')


# Severity thresholds live with the analytics (utils/ai_insights.py), so the
# meter and the badge can never disagree about where a band starts.
from utils.ai_insights import THRESHOLDS  # noqa: E402

METER_MAX = 1.2


def meter(share_pct: float, kind: str) -> str:
    """Share of period spend against the three thresholds. Text says what the bar shows."""
    width = max(0.0, min(100.0, 100.0 * share_pct / METER_MAX))
    ticks = "".join(
        f'<i class="fo-meter__tick" style="left:{100.0 * v / METER_MAX:.1f}%"></i>'
        for v in THRESHOLDS.values()
    )
    band = {
        "critical": "Critical above 1%.",
        "serious": "Serious from 0.3%.",
        "warning": "Warning from 0.1%.",
        "good": "Below the 0.1% reporting threshold.",
    }[kind]
    return (f'<div class="fo-meter" role="img" aria-label="{fmt.pct(share_pct)} of period spend, {esc(band)}">'
            f'<div class="fo-meter__track"><div class="fo-meter__fill fo-{kind}" style="width:{width:.1f}%"></div>{ticks}</div>'
            f'<p class="fo-meter__label"><b>{fmt.pct(share_pct)}</b> of period spend. {esc(band)}</p></div>')


# --- KPI tile ---------------------------------------------------------------

def sparkline(values: Iterable[float], ref: float | None = None, label: str = "") -> str:
    vals = [float(v) for v in values if v is not None and not pd.isna(v)]
    if len(vals) < 3:
        return ""
    w, h, pad = 96, 30, 3
    pool = vals + ([float(ref)] if ref is not None else [])
    lo, hi = min(pool), max(pool)
    span = (hi - lo) or 1.0

    def x(i: int) -> float:
        return pad + i * (w - 2 * pad) / (len(vals) - 1)

    def y(v: float) -> float:
        return h - pad - (v - lo) * (h - 2 * pad) / span

    d = "".join(f"{'L' if i else 'M'}{x(i):.1f} {y(v):.1f}" for i, v in enumerate(vals))
    ref_html = (f'<line x1="{pad}" y1="{y(float(ref)):.1f}" x2="{w - pad}" y2="{y(float(ref)):.1f}"/>'
                if ref is not None else "")
    return (f'<svg class="fo-spark" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
            f'{ref_html}<path d="{d}"/><circle cx="{x(len(vals) - 1):.1f}" cy="{y(vals[-1]):.1f}" r="3"/></svg>')


def kpi(
    label: str,
    value: str,
    unit_code: str | None = None,
    unit_after: str | None = None,
    spoken: str | None = None,
    delta: str | None = None,
    direction: str | None = None,
    basis: str | None = None,
    status: str | None = None,
    mark: tuple[str, str] | None = None,
    note: str | None = None,
    spark: Iterable[float] | None = None,
    spark_ref: float | None = None,
    spark_label: str = "13 week trend",
) -> str:
    """One KPI tile.

    `direction` is up, down or flat and always draws a glyph, so colour is never
    the only carrier. `status` colours the delta when a threshold exists.
    `mark` is (status, word) shown right of the label.
    """
    mark_html = ""
    if mark:
        mark_html = (f'<span class="fo-kpi__mark fo-{mark[0]}">{icon(STATUS_ICON[mark[0]])}'
                     f'{esc(mark[1])}</span>')
    pre = unit(unit_code) if unit_code else ""
    post = f'<span class="fo-unit" style="margin:0 0 0 4px">{esc(unit_after)}</span>' if unit_after else ""
    aria = f' aria-label="{esc(spoken)}"' if spoken else ""
    value_html = f'<div class="fo-kpi__value"{aria}>{pre}{esc(value)}{post}</div>'
    spark_html = sparkline(spark, spark_ref, spark_label) if spark is not None else ""
    delta_html = ""
    if delta is not None:
        glyph = {"up": "arrow-up-right", "down": "arrow-down-right"}.get(direction or "flat", "minus")
        word = {"up": "up", "down": "down"}.get(direction or "flat", "unchanged")
        cls = f" fo-{status}" if status else ""
        basis_html = f'<span class="fo-kpi__basis">{esc(basis)}</span>' if basis else ""
        delta_html = (f'<div class="fo-kpi__delta{cls}">{icon(glyph)}{vh(word)}{esc(delta)}{basis_html}</div>')
    note_html = f'<p class="fo-kpi__note">{esc(note)}</p>' if note else ""
    return (f'<div class="fo-kpi" role="group" aria-label="{esc(label)}">'
            f'<div class="fo-kpi__label">{esc(label)}{mark_html}</div>'
            f'<div class="fo-kpi__row">{value_html}{spark_html}</div>{delta_html}{note_html}</div>')


def kpi_absent(label: str, word: str, note: str | None = None) -> str:
    note_html = f'<p class="fo-kpi__note">{esc(note)}</p>' if note else ""
    return (f'<div class="fo-kpi" role="group" aria-label="{esc(label)}"><div class="fo-kpi__label">{esc(label)}</div>'
            f'<div class="fo-kpi__absent">{esc(word)}</div>{note_html}</div>')


# --- Summary ------------------------------------------------------------------

def hero(value: str, unit_code: str | None, spoken: str, label: str, basis: str) -> str:
    pre = unit(unit_code) if unit_code else ""
    return (f'<p class="fo-hero" aria-label="{esc(spoken)}">{pre}{esc(value)}</p>'
            f'<p class="fo-hero-label">{esc(label)}</p><p class="fo-hero-basis">{esc(basis)}</p>')


def composition(parts: Sequence[tuple[str, float, str]], value_fmt=fmt.money) -> str:
    """A stacked bar of (name, value, colour). One segment per entity, colour follows the entity."""
    parts = [p for p in parts if p[1] > 0]
    if not parts:
        return ""
    bar = "".join(f'<i style="flex:{v:.3f};background:{c}"></i>' for _, v, c in parts)
    legend = "".join(
        f'<span><i style="background:{c}"></i>{esc(n)}<span class="fo-num">{value_fmt(v)}</span></span>'
        for n, v, c in parts
    )
    spoken = ", ".join(f"{n} {value_fmt(v)}" for n, v, _ in parts)
    return (f'<div class="fo-comp" role="img" aria-label="Composition: {esc(spoken)}">'
            f'<div class="fo-comp__bar">{bar}</div><div class="fo-comp__legend">{legend}</div></div>')


def lead(sentences: Sequence[str]) -> str:
    return "".join(f'<p class="fo-lead">{s}</p>' for s in sentences)


def strong(text: str) -> str:
    return f"<b>{esc(text)}</b>"


# --- Table -------------------------------------------------------------------

def html_table(
    df: pd.DataFrame,
    columns: Sequence[tuple[str, str, str]],
    compact: bool = False,
    cite: Iterable[tuple[int, str]] = (),
    totals: dict | None = None,
    caption_text: str | None = None,
    formats: dict | None = None,
) -> str:
    """A .fo-table from a DataFrame.

    `columns` is a sequence of (column_name, header_text, kind) where kind is
    text, num, date or badge. Numeric headers are right-aligned and carry
    the unit in parentheses in the header text. `cite` lists (row_position,
    column_name) cells to highlight. `totals` maps column_name to a formatted
    string for a totals row. `formats` maps column_name to a callable.
    """
    formats = formats or {}
    cite_set = set(cite)

    def cell(kind: str, value, col: str, r: int) -> str:
        f = formats.get(col)
        if kind == "badge":
            kind_word = str(value)
            body = badge(kind_word) if kind_word in STATUS_ICON else esc(value)
            return f"<td>{body}</td>"
        if f is not None:
            text = f(value)
        elif kind == "num":
            text = fmt.group(value, 0)
        elif kind == "date":
            text = fmt.iso(value)
        else:
            text = esc(fmt.plain(value))
        cls = {"num": "fo-num", "date": "fo-date"}.get(kind, "")
        if (r, col) in cite_set:
            cls = (cls + " fo-cite").strip()
            text += vh(" cited")
        attr = f' class="{cls}"' if cls else ""
        return f"<td{attr}>{text}</td>"

    head_cells = []
    for _, header, kind in columns:
        num_cls = ' class="fo-num"' if kind == "num" else ""
        head_cells.append(f'<th scope="col"{num_cls}>{esc(header)}</th>')
    head = "".join(head_cells)
    body_rows = []
    for r, (_, row) in enumerate(df.iterrows()):
        body_rows.append("<tr>" + "".join(cell(kind, row[col], col, r) for col, _, kind in columns) + "</tr>")
    if not body_rows:
        body_rows.append(f'<tr class="fo-table__empty"><td colspan="{len(columns)}">No rows match the current filters.</td></tr>')
    foot = ""
    if totals:
        cells = []
        for col, _, kind in columns:
            v = totals.get(col, "")
            cls = ' class="fo-num"' if kind == "num" else ""
            cells.append(f"<td{cls}>{v}</td>")
        foot = "<tfoot><tr>" + "".join(cells) + "</tr></tfoot>"
    cap = f'<caption class="fo-vh">{esc(caption_text)}</caption>' if caption_text else ""
    compact_cls = " fo-table--compact" if compact else ""
    return (f'<div class="fo-table-wrap"><table class="fo-table{compact_cls}">{cap}'
            f'<thead><tr>{head}</tr></thead><tbody>{"".join(body_rows)}</tbody>{foot}</table></div>')
