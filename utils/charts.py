"""
Plotly figures and the chart card. Section 5 of docs/design-system.md.

Every figure inherits the active template from utils.theme and sets only its
data and its labels, so a chart cannot drift from the system by setting its
own colours. Every chart card carries a Chart / Table control, because the
table is the relief channel for the light palette and the only path to exact
values for anyone who cannot use hover.

Never a dual axis. Two measures of different scale are two panels sharing one
x axis (trend_two_panel).
"""

from __future__ import annotations

from typing import Callable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from utils import fmt, theme, ui

HOVER_MONEY = "%{customdata[0]}"


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _interp_hex(steps: list[str], frac: float) -> str:
    """The colour Plotly draws at `frac` of a ramp with evenly spaced steps."""
    frac = min(1.0, max(0.0, float(frac)))
    pos = frac * (len(steps) - 1)
    i = min(int(pos), len(steps) - 2)
    w = pos - i
    a, b = _hex_to_rgb(steps[i]), _hex_to_rgb(steps[i + 1])
    return "#" + "".join(f"{round(a[k] * (1 - w) + b[k] * w):02x}" for k in range(3))


def _luminance(h: str) -> float:
    def ch(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = _hex_to_rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def _contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _money_ticks(max_value: float) -> tuple[list[float], list[str]]:
    """Five or fewer ticks whose labels follow the section 6 formatter."""
    if max_value <= 0:
        return [0.0], ["0"]
    import math
    raw = max_value / 4
    magnitude = 10 ** math.floor(math.log10(raw))
    step = next(s * magnitude for s in (1, 2, 2.5, 5, 10) if s * magnitude >= raw)
    vals = [i * step for i in range(0, int(max_value // step) + 2)]
    return vals, [fmt.compact(v) for v in vals]


def carrier_cost_chart(by_carrier: pd.DataFrame, th: str) -> go.Figure:
    """Cost per billable shipment by carrier. Horizontal bars, direct labels, one reference line."""
    t = theme.tokens(th)
    data = by_carrier.copy()
    data["cost_per"] = data["spend"] / data["billable_orders"].replace(0, pd.NA)
    data = data.dropna(subset=["cost_per"])
    book = float(data["spend"].sum() / max(int(data["billable_orders"].sum()), 1))
    colors = [theme.color_for(c, th) for c in data["carrier"]]
    fig = go.Figure(go.Bar(
        y=data["carrier"], x=data["cost_per"], orientation="h",
        marker=dict(color=colors, line=dict(color=t["surface"], width=1)),
        text=[fmt.money(v, exact=True) for v in data["cost_per"]],
        textposition="outside", cliponaxis=False,
        textfont=dict(family=theme.FONT_MONO, size=12, color=t["ink"]),
        customdata=list(zip(
            [fmt.money(v, exact=True) for v in data["cost_per"]],
            [fmt.count(v) for v in data["billable_orders"]],
            [fmt.money(v, exact=True) for v in data["spend"]],
        )),
        hovertemplate="<b>%{y}</b><br>%{customdata[0]} per shipment<br>%{customdata[1]} billable shipments<br>%{customdata[2]} spend<extra></extra>",
    ))
    fig.add_vline(x=book, line=dict(color=t["line_strong"], width=1, dash="4,4"))
    fig.add_annotation(x=book, y=1.0, yref="paper", yanchor="bottom", xanchor="left",
                       text=f"Book {fmt.money(book, exact=True)}", showarrow=False, xshift=4,
                       font=dict(color=t["ink_secondary"], size=12))
    fig.update_layout(
        height=max(200, 44 + 32 * len(data)), hovermode="closest", showlegend=False,
        margin=dict(l=8, r=64, t=24, b=8),
    )
    # Every carrier is labelled, for the same reason the heatmap forces its own
    # ticks: Plotly thins categorical ticks when it judges them crowded, and a
    # bar nobody can name is a bar nobody can act on — least of all the carrier
    # the findings above are about.
    fig.update_yaxes(autorange="reversed", showline=False, showgrid=False, ticks="",
                     tickmode="array", tickvals=list(data["carrier"]), ticktext=list(data["carrier"]),
                     tickfont=dict(family=theme.FONT_UI, size=12, color=t["ink_secondary"]))
    vals, labels = _money_ticks(float(data["cost_per"].max()) if len(data) else 0.0)
    fig.update_xaxes(showgrid=True, gridcolor=t["line_hairline"], showline=False, tickvals=vals,
                     ticktext=labels, rangemode="tozero",
                     tickfont=dict(family=theme.FONT_MONO, size=12, color=t["ink_secondary"]))
    fig.add_shape(type="line", x0=0, x1=0, y0=0, y1=1, xref="x", yref="paper",
                  line=dict(color=t["line_strong"], width=1))
    return fig


def trend_two_panel(trend: pd.DataFrame, book_on_time: float, th: str) -> go.Figure:
    """Weekly spend (bars) and on-time rate (line) as two panels sharing one week axis."""
    t = theme.tokens(th)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.16, row_heights=[0.5, 0.5])
    weeks = [fmt.week(p) for p in trend["period"]]
    fig.add_trace(go.Bar(
        x=trend["period"], y=trend["spend"], name="Freight spend",
        marker=dict(color=t["series"][0], line=dict(color=t["surface"], width=1)),
        customdata=list(zip(weeks, [fmt.money(v, exact=True) for v in trend["spend"]])),
        hovertemplate="%{customdata[1]}<extra>Freight spend</extra>",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=trend["period"], y=trend["on_time_pct"], name="On time", mode="lines+markers" if len(trend) <= 24 else "lines",
        line=dict(color=t["series"][0], width=2, shape="linear"),
        marker=dict(size=6, color=t["series"][0], line=dict(color=t["surface"], width=1.5)),
        customdata=list(zip([fmt.count(v) for v in trend["orders"]], [fmt.count(v) for v in trend["late_orders"]])),
        hovertemplate="%{y:.1f}% on time<br>%{customdata[1]} late of %{customdata[0]}<extra>On time</extra>",
    ), row=2, col=1)
    fig.add_hline(y=book_on_time, row=2, col=1, line=dict(color=t["line_strong"], width=1, dash="4,4"),
                  annotation_text=f"Book {fmt.pct(book_on_time)}", annotation_position="top right",
                  annotation_font=dict(color=t["ink_secondary"], size=12))
    for text, y in (("Freight spend, EUR", 1.0), ("On-time delivery, %", 0.42)):
        fig.add_annotation(text=text, xref="paper", yref="paper", x=0, y=y, xanchor="left", yanchor="bottom",
                           showarrow=False, font=dict(color=t["ink_secondary"], size=12), yshift=6)
    fig.update_layout(height=380, showlegend=False, hovermode="x unified", margin=dict(l=8, r=8, t=24, b=8))
    fig.update_xaxes(row=1, col=1, showticklabels=False, showline=True, linecolor=t["line_strong"])
    # ISO week over ISO year on two lines, from the same formatter the tables
    # use, because a range longer than a year repeats every week number and a
    # bare "W14" is then two different weeks. Plotly's own %G is not supported.
    step = max(1, len(trend) // 7) if len(trend) else 1
    ticks = list(trend["period"].iloc[::step]) if len(trend) else []
    fig.update_xaxes(row=2, col=1, showline=True, linecolor=t["line_strong"], tickmode="array",
                     tickvals=ticks, ticktext=[fmt.week(p).replace(" ", "<br>") for p in ticks],
                     hoverformat="W%V %Y", tickfont=dict(family=theme.FONT_MONO, size=12, color=t["ink_secondary"]))
    vals, labels = _money_ticks(float(trend["spend"].max()) if len(trend) else 0.0)
    fig.update_yaxes(row=1, col=1, tickvals=vals, ticktext=labels, rangemode="tozero")
    # A rate does not anchor at zero: nobody ships at 0% on time, and the panel
    # would spend its height on empty space. Floor under the data, ceiling at 100.
    floor = max(0.0, float(trend["on_time_pct"].min()) - 6.0) if len(trend) else 0.0
    fig.update_yaxes(row=2, col=1, range=[floor, 100.5], ticksuffix="%")
    return fig


def late_heatmap(rates: pd.DataFrame, counts: pd.DataFrame, th: str, min_shipments: int) -> go.Figure:
    """Late rate per carrier and destination on the sequential ramp, every cell labelled."""
    t = theme.tokens(th)
    late = 100 - rates
    z = late.to_numpy(dtype=float)
    zmax = float(max(30.0, pd.Series(z.ravel()).max(skipna=True) or 30.0))
    steps = t["seq"]
    fig = go.Figure(go.Heatmap(
        z=z, x=list(late.columns), y=list(late.index),
        colorscale=theme.seq_colorscale(th), zmin=0, zmax=zmax, xgap=1, ygap=1,
        customdata=counts.to_numpy(),
        hovertemplate="<b>%{y} to %{x}</b><br>%{z:.1f}% late<br>%{customdata} shipments<extra></extra>",
        hoverongaps=False, showscale=False,
    ))
    for r, carrier in enumerate(late.index):
        for c, dest in enumerate(late.columns):
            value = z[r][c]
            if pd.isna(value):
                fig.add_annotation(x=dest, y=carrier, text="none", showarrow=False,
                                   font=dict(size=11, family=theme.FONT_UI, color=t["ink_muted"]))
                continue
            # Plotly interpolates between ramp steps, so the label ink is chosen
            # against the cell's actual colour: whichever ink clears the higher
            # contrast. Colour alone never carries the value; the label does.
            cell = _interp_hex(steps, value / zmax)
            ink = max((t["ink"], t["ink_inverse"]), key=lambda c: _contrast(c, cell))
            fig.add_annotation(x=dest, y=carrier, text=f"{value:.1f}", showarrow=False,
                               font=dict(size=11, family=theme.FONT_MONO, color=ink))
    fig.update_layout(height=max(180, 40 + 30 * len(late.index)), hovermode="closest",
                      margin=dict(l=8, r=8, t=8, b=8))
    fig.update_xaxes(side="bottom", showline=False, showgrid=False,
                     tickfont=dict(family=theme.FONT_MONO, size=12, color=t["ink_secondary"]))
    # Every carrier is labelled. Plotly thins categorical ticks when it judges
    # them crowded, and a heatmap row without its name is a row nobody can cite.
    fig.update_yaxes(autorange="reversed", showgrid=False, showline=False, ticks="",
                     tickmode="array", tickvals=list(late.index), ticktext=list(late.index),
                     tickfont=dict(family=theme.FONT_UI, size=12, color=t["ink_secondary"]))
    fig.update_xaxes(tickmode="array", tickvals=list(late.columns), ticktext=[str(c) for c in late.columns])
    return fig


def chart_card(
    key: str,
    title: str,
    sub: str,
    build: Callable[[], go.Figure | None],
    table_html: str,
    foot: str | None = None,
    insufficient: str | None = None,
) -> None:
    """A card with a title, a Chart / Table control and a footer.

    `build` returns the figure, or None when there is nothing honest to draw.
    `insufficient` is the sentence shown in place of the chart when the data
    is under the chart type's minimum; the table twin is shown in its place.
    """
    with st.container(border=True):
        st.markdown(ui.card_mark(), unsafe_allow_html=True)
        head, ctrl = st.columns([5, 2])
        head.markdown(ui.card_head(title, sub), unsafe_allow_html=True)
        with ctrl:
            st.markdown('<div class="fo-compact"></div>', unsafe_allow_html=True)
            view = st.segmented_control(
                "View", ["Chart", "Table"], default="Chart", key=f"{key}-view",
                label_visibility="collapsed", disabled=insufficient is not None,
            )
        if insufficient is not None:
            st.markdown(ui.caption(ui.esc(insufficient)), unsafe_allow_html=True)
            st.markdown(table_html, unsafe_allow_html=True)
        elif view == "Table":
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            fig = build()
            if fig is None:
                st.markdown(ui.empty_state("No shipments match the current filters."), unsafe_allow_html=True)
            else:
                st.plotly_chart(fig, use_container_width=True, config=theme.PLOTLY_CONFIG, key=f"{key}-fig")
        if foot:
            st.markdown(ui.caption(foot), unsafe_allow_html=True)
