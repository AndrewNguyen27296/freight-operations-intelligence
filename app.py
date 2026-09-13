"""
Pillar 1. Automated Data Pipeline and Interactive Executive Dashboard (V1).

North Star: "Zero-Click Operational Clarity."

The page is the briefing. It opens like a report prepared for someone: a
masthead, the one figure the page exists for, three sentences, four KPI tiles,
the findings a sceptical reader can open and check, and the analysis behind
them. Data ingest lives in the sidebar. Detail tables live in tabs.

Every visual decision here is the implementation of docs/design-system.md.
Tokens and Streamlit widget styling: utils/theme.py. HTML components:
utils/ui.py. Figures: utils/charts.py. Formatting: utils/fmt.py.

All analytics live in utils/metrics.py and utils/ai_insights.py (pure pandas,
unit-tested). This file is presentation only.

Run:
    streamlit run app.py
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import ai_insights, charts, fmt, metrics, theme, ui  # noqa: E402
from utils.dataset import (  # noqa: E402
    LOG_PATH,
    dataset_signature,
    ensure_processed,
    normalize_dtypes,
    read_processed,
    sample_files,
)

st.set_page_config(
    page_title="Freight Operations Intelligence",
    layout="wide",
    initial_sidebar_state="auto",
)

# The audience named in the masthead. Set per build; blank hides the line.
CLIENT_NAME = os.environ.get("FOI_CLIENT_NAME", "").strip()

# Formatter names carried by findings (utils/ai_insights.py) resolve here, so a
# finding stays picklable for st.cache_data.
FORMATTERS = {
    ai_insights.F_INT: lambda v: fmt.group(v, 0),
    ai_insights.F_1DP: lambda v: fmt.group(v, 1),
    ai_insights.F_MONEY: lambda v: fmt.money(v, exact=True),
    ai_insights.F_PCT1: lambda v: fmt.pct(v, 1),
}

# Below this many shipments in the comparison window a delta is noise.
MIN_PRIOR_SHIPMENTS = 20


def md(html_text: str) -> None:
    st.markdown(html_text, unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Cached data access. The cache key is the whole game here.
# --------------------------------------------------------------------------
#
# Streamlit builds a cache key by hashing every argument it is given, so a
# cached function that takes the DataFrame by value pays to hash the entire
# frame on every rerun: about 18ms at 5k rows, but around 830ms at 500k, which
# is the scale a real client's annual shipment log arrives at. So the frame is
# passed as `_df`, which Streamlit excludes from the key, and the key is carried
# by cheap scalars: the filter values plus a dataset signature.

@st.cache_data(show_spinner="Preparing the sample dataset")
def load_data() -> pd.DataFrame:
    ensure_processed()
    return read_processed()


@st.cache_data(show_spinner=False)
def load_cleaning_log(_signature: str) -> dict | None:
    if LOG_PATH.exists():
        return json.loads(LOG_PATH.read_text(encoding="utf-8"))
    return None


@st.cache_data(show_spinner="Reconciling your exports")
def load_uploads(_payloads: tuple, digest: str) -> tuple[pd.DataFrame, dict]:
    """Run the full pipeline over uploaded exports, entirely in memory.

    Nothing touches disk. Streamlit Cloud's filesystem is ephemeral anyway,
    and a prospect's shipment data has no business being persisted on a demo
    server, which is also the honest answer when they ask.
    """
    from pipeline import clean  # deferred: only needed on the upload path

    sources = [(name, io.BytesIO(data)) for name, data in _payloads]
    df, log = clean.build(sources)
    return normalize_dtypes(df), log


@st.cache_data(show_spinner=False)
def sample_bytes(path_name: str) -> bytes:
    return (next(p for p in sample_files() if p.name == path_name)).read_bytes()


@st.cache_data(show_spinner=False)
def build_view(
    _df: pd.DataFrame,
    signature: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    carriers: tuple[str, ...],
) -> dict:
    """Filter once, then derive everything from that one slice."""
    view = metrics.filter_shipments(_df, start, end, carriers)
    if view.empty:
        return {"view": view}
    rates, counts = metrics.carrier_destination_matrix(view)
    findings = ai_insights.build_findings(view)

    # The window of equal length before this one, for the KPI deltas. Below
    # MIN_PRIOR_SHIPMENTS the comparison is noise and the tile says nothing.
    span = end - start
    prior = metrics.filter_shipments(_df, start - span - pd.Timedelta(days=1),
                                     start - pd.Timedelta(days=1), carriers)
    return {
        "view": view,
        "kpis": metrics.compute_kpis(view),
        "prior_kpis": metrics.compute_kpis(prior) if len(prior) >= MIN_PRIOR_SHIPMENTS else None,
        "prior_days": int(span.days) + 1,
        "by_carrier": metrics.spend_by_carrier(view),
        "trend": metrics.trend(view),
        "rates": rates,
        "counts": counts,
        "findings": findings,
        "summary": ai_insights.executive_summary(view, findings),
    }


# --------------------------------------------------------------------------
# Sidebar: data sources
# --------------------------------------------------------------------------

def sidebar_source() -> tuple[pd.DataFrame, dict | None, str] | None:
    """Returns (df, cleaning_log, cache signature), or None while waiting for files.

    The bundled sample is the default and loads with no clicks at all, which
    is the whole point: a prospective client opening the live URL sees a
    working briefing before deciding whether to trust it with their own file.
    """
    with st.sidebar:
        md(ui.card_head("Data sources", "Carrier, TMS and ERP exports are reconciled together."))
        if "source_mode" not in st.session_state:
            st.session_state["source_mode"] = "Sample"
        mode = st.segmented_control(
            "Source", ["Sample", "Your exports"], key="source_mode", label_visibility="collapsed",
        )

        if mode != "Your exports":
            df = load_data()
            signature = dataset_signature()
            log = load_cleaning_log(signature)
            names = [p.name for p in sample_files()]
            md(ui.caption(f"Running on <b>{len(names)}</b> bundled exports: {ui.esc(', '.join(names))}. "
                          "Three systems with three column vocabularies, normalised into one table."))
            md(ui.spacer(4))
            md(ui.caption("Try the upload path with one of the samples:"))
            for path in sample_files():
                st.download_button(path.name, data=sample_bytes(path.name), file_name=path.name,
                                   mime="text/csv", type="tertiary", key=f"dl-{path.name}")
            return df, log, signature

        uploaded = st.file_uploader(
            "Drop shipment exports here or browse",
            type=["csv"], accept_multiple_files=True,
            help="Comma or semicolon separated CSV. Column names are mapped onto the canonical "
                 "schema, so they do not have to match ours.",
        )
        if not uploaded:
            md(ui.alert("neutral", "No files yet",
                        "Drop one or more CSV exports above. Nothing is written to disk; the pipeline "
                        "runs in memory and the result lives only in this session."))
            return None

        payloads = tuple((f.name, f.getvalue()) for f in uploaded)
        digest = hashlib.sha256(b"".join(name.encode() + data for name, data in payloads)).hexdigest()[:16]
        try:
            df, log = load_uploads(payloads, digest)
        except ValueError as exc:
            md(ui.alert("critical", "Critical: the files could not be read", ui.esc(str(exc))))
            return None
        except Exception as exc:  # noqa: BLE001 - a demo must not show a traceback
            md(ui.alert("critical", "Critical: the files could not be processed", ui.esc(str(exc))))
            return None

        md(ui.alert("good", "Reconciliation complete",
                    f"{fmt.count(log['rows_in'])} rows from {len(payloads)} file{'s' if len(payloads) != 1 else ''} "
                    f"became {fmt.count(log['rows_out'])} analysis-ready shipments. Every removed row has a logged "
                    "reason in the Data lineage tab."))
        return df, log, f"upload:{digest}"


# --------------------------------------------------------------------------
# Filters
# --------------------------------------------------------------------------

def filters(df: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp, tuple[str, ...]]:
    min_date: date = df["ship_date"].min().date()
    max_date: date = df["ship_date"].max().date()

    # Labels are one or two words so the control never wraps or truncates in a
    # 3-of-12 column beside an open sidebar; the caption below states the range.
    presets = {
        "All data": (min_date, max_date),
        "13 weeks": (max(min_date, max_date - timedelta(weeks=13)), max_date),
        "4 weeks": (max(min_date, max_date - timedelta(weeks=4)), max_date),
    }

    # Widget state is initialised here, not through `value=`, so a preset or a
    # reset can set it from a callback without Streamlit's duplicate-default warning.
    if "date_range" not in st.session_state:
        st.session_state["date_range"] = presets["All data"]
    if "preset" not in st.session_state:
        st.session_state["preset"] = "All data"
    if "carriers" not in st.session_state:
        st.session_state["carriers"] = []

    # A dataset switch can leave a stored range outside the new bounds.
    lo, hi = st.session_state["date_range"] if isinstance(st.session_state["date_range"], (tuple, list)) \
        and len(st.session_state["date_range"]) == 2 else presets["All data"]
    st.session_state["date_range"] = (max(min_date, min(lo, max_date)), min(max_date, max(hi, min_date)))

    def apply_preset() -> None:
        chosen = st.session_state.get("preset")
        if chosen in presets:
            st.session_state["date_range"] = presets[chosen]

    def reset() -> None:
        st.session_state["date_range"] = presets["All data"]
        st.session_state["preset"] = "All data"
        st.session_state["carriers"] = []

    present = sorted(df["carrier"].dropna().unique())
    options = [c for c in theme.CARRIER_ORDER if c in present] + [c for c in present if c not in theme.CARRIER_ORDER]
    st.session_state["carriers"] = [c for c in st.session_state["carriers"] if c in options]

    c1, c2, c3, c4 = st.columns([3, 3, 4, 2], vertical_alignment="bottom")
    with c1:
        picked = st.date_input("Period", key="date_range", min_value=min_date, max_value=max_date,
                               format="YYYY/MM/DD")
    with c2:
        st.segmented_control("Preset", list(presets), key="preset", on_change=apply_preset)
    with c3:
        st.multiselect("Carriers", options=options, key="carriers", placeholder="All carriers")
    with c4:
        st.button("Reset filters", type="tertiary", on_click=reset, use_container_width=True)

    if isinstance(picked, (tuple, list)) and len(picked) == 2:
        start, end = pd.Timestamp(picked[0]), pd.Timestamp(picked[1])
    else:
        # Mid-drag the picker returns a single date. Hold the full range rather
        # than flashing an empty dashboard in front of a client.
        start, end = pd.Timestamp(min_date), pd.Timestamp(max_date)

    carriers = tuple(st.session_state["carriers"])
    selected = f"{len(carriers)} of {len(options)} carriers selected" if carriers else "All carriers"
    md(ui.caption(f"{fmt.iso_range(start, end)}, {fmt.week_range(start, end)}. {selected}."))
    return start, end, carriers


# --------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------

def render_summary(summary: dict, th: str) -> None:
    left, right = st.columns([4, 8], gap="large")
    with left:
        md(ui.overline("Leaking to late-delivery penalties")
           + ui.hero(fmt.compact(summary["hero_eur"]), "EUR",
                     f"{fmt.money(summary['hero_eur'], exact=True)}",
                     summary["hero_label"], summary["hero_basis"])
           + ui.composition([(name, value, theme.color_for(name, th) if name != "Other"
                              else theme.tokens(th)["series_other"])
                             for name, value in summary["composition"]]))
    with right:
        md(ui.overline("Summary") + ui.lead(summary["sentences"])
           + f'<p class="fo-summary-foot">{summary["footer"]}</p>')


def render_kpis(bundle: dict) -> None:
    k, p, days = bundle["kpis"], bundle["prior_kpis"], bundle["prior_days"]
    tr = bundle["trend"].tail(13)
    basis = f"vs prior {days} days" if p else None

    def change(new, old, kind: str):
        """(delta text, direction) for a KPI against the prior window, or (None, None)."""
        if not p:
            return None, None
        if kind == "pct":
            d = fmt.signed_pct_change(new, old)
            return d, ("up" if new > old else "down" if new < old else "flat") if d else (None, None)
        diff = float(new) - float(old)
        direction = "up" if diff > 0.05 else "down" if diff < -0.05 else "flat"
        text = fmt.pts(diff) if kind == "pts" else (("+" if diff > 0 else "") + fmt.group(diff, 1) + " days")
        return text, direction

    d_spend, dir_spend = change(k["total_spend"], p["total_spend"] if p else None, "pct")
    d_ot, dir_ot = change(k["on_time_pct"], p["on_time_pct"] if p else None, "pts")
    d_delay, dir_delay = change(k["avg_delay"], p["avg_delay"] if p else None, "days")
    d_orders, dir_orders = change(k["orders"], p["orders"] if p else None, "pct")

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(ui.kpi(
        "Freight spend", fmt.compact(k["total_spend"]), unit_code="EUR",
        spoken=fmt.money(k["total_spend"], exact=True), delta=d_spend, direction=dir_spend, basis=basis,
        spark=tr["spend"], spark_label="Weekly freight spend, last 13 weeks",
        note=f"Billable shipments only, {fmt.count(k['billable_orders'])} of {fmt.count(k['orders'])}.",
    ), unsafe_allow_html=True)
    c2.markdown(ui.kpi(
        "On-time delivery", fmt.pct(k["on_time_pct"]).rstrip("%"), unit_after="%",
        spoken=f"{fmt.pct(k['on_time_pct'])} on time", delta=d_ot, direction=dir_ot, basis=basis,
        status=("good" if dir_ot == "up" else "warning" if dir_ot == "down" else None),
        spark=tr["on_time_pct"], spark_ref=k["on_time_pct"], spark_label="Weekly on-time rate against the period average",
    ), unsafe_allow_html=True)
    c3.markdown(ui.kpi(
        "Delay when late", fmt.group(k["avg_delay"], 1), unit_after="days",
        spoken=fmt.days(k["avg_delay"]), delta=d_delay, direction=dir_delay, basis=basis,
        status=("warning" if dir_delay == "up" else "good" if dir_delay == "down" else None),
        spark=tr["avg_delay"], spark_label="Weekly mean delay of late shipments",
        note=f"{fmt.count(k['late_orders'])} late shipments, {fmt.money(k['penalties'])} in penalties.",
    ), unsafe_allow_html=True)
    c4.markdown(ui.kpi(
        "Shipments", fmt.count(k["orders"]), spoken=f"{fmt.count(k['orders'])} shipments",
        delta=d_orders, direction=dir_orders, basis=basis,
        spark=tr["orders"], spark_label="Weekly shipment count",
        note=f"{fmt.count(k['cancelled_orders'])} cancelled, {fmt.count(k['outlier_orders'])} cost outliers.",
    ), unsafe_allow_html=True)


def render_finding(n: int, total: int, f: dict) -> None:
    with st.container(border=True):
        md(ui.card_mark())
        left, right = st.columns([8, 4], gap="medium")
        with left:
            head = (f'<div class="fo-finding__head">{ui.vh(f"Finding {n} of {total}")}'
                    f'<span class="fo-finding__num" aria-hidden="true">{n:02d}</span>'
                    f'<span class="fo-finding__kind">{ui.esc(f["kind"])}</span>{ui.badge(f["severity"])}</div>')
            support = "".join(f'<p class="fo-finding__support">{ui.esc(s)}</p>' for s in f["support"])
            md(head
               + f'<h2 id="finding-{n}" class="fo-finding__claim">{ui.esc(f["claim"])}</h2>'
               + support
               + '<p class="fo-finding__action-lead">Recommended action</p>'
               + f'<p class="fo-finding__action">{ui.esc(f["action"])}</p>')
        with right:
            md(f'<p class="fo-finding__figure" aria-label="{ui.esc(fmt.money(f["figure_eur"], exact=True))}">'
               f'{ui.unit("EUR")}{fmt.compact(f["figure_eur"])}</p>'
               f'<p class="fo-finding__figure-label">{ui.esc(f["figure_label"])}</p>'
               f'<p class="fo-finding__figure-basis">{ui.esc(f["figure_basis"])}</p>'
               + ui.meter(f["share_pct"], f["severity"]))
        evidence: pd.DataFrame = f["evidence"]
        with st.expander(f"Evidence ({fmt.count(len(evidence))} rows)"):
            formats = {col: FORMATTERS[name] for col, name in f["formats"].items()}
            md(ui.html_table(evidence, f["columns"], compact=True, cite=f["cite"], formats=formats,
                             caption_text=f["claim"]))
            md(ui.caption(f"{ui.esc(f['method'])} {ui.esc(f['exclusions'])}"))
            st.download_button("Download CSV", evidence.to_csv(index=False).encode("utf-8"),
                               file_name=f"finding-{n:02d}.csv", mime="text/csv", type="tertiary",
                               key=f"finding-{n}-csv")


def render_no_findings(summary: dict, period: str) -> None:
    with st.container(border=True):
        md(ui.card_mark())
        md('<div class="fo-finding__head"><span class="fo-finding__num">00</span>'
           '<span class="fo-finding__kind">No findings</span>' + ui.badge("good") + '</div>'
           '<h2 class="fo-finding__claim">No leakage above the reporting threshold was found in this period.</h2>'
           f'<p class="fo-finding__support">Threshold {fmt.pct(ai_insights.THRESHOLDS["warning"])} of period freight spend. '
           f'{ui.esc(period)}. {summary["footer"]}</p>')


def render_analysis(bundle: dict, th: str) -> None:
    by_carrier = bundle["by_carrier"].copy()
    by_carrier["cost_per"] = by_carrier["spend"] / by_carrier["billable_orders"].replace(0, pd.NA)
    kpis = bundle["kpis"]
    left, right = st.columns([5, 7], gap="medium")
    with left:
        charts.chart_card(
            "cost", "Cost per shipment by carrier",
            f"EUR per billable shipment. Dashed line is the book at {fmt.money(kpis['total_spend'] / max(kpis['billable_orders'], 1), exact=True)}.",
            lambda: charts.carrier_cost_chart(by_carrier, th) if len(by_carrier) else None,
            ui.html_table(by_carrier, [("carrier", "Carrier", "text"), ("billable_orders", "Billable shipments", "num"),
                                       ("spend", "Spend (EUR)", "num"), ("cost_per", "Per shipment (EUR)", "num"),
                                       ("on_time_pct", "On time (%)", "num")],
                          formats={"billable_orders": FORMATTERS[ai_insights.F_INT], "spend": FORMATTERS[ai_insights.F_INT],
                                   "cost_per": FORMATTERS[ai_insights.F_INT], "on_time_pct": FORMATTERS[ai_insights.F_1DP]}),
            foot=f"Spend covers {fmt.count(kpis['billable_orders'])} billable shipments; cancelled and cost-outlier rows are excluded.",
        )
    with right:
        tr = bundle["trend"]
        table = ui.html_table(
            tr, [("period", "Week", "text"), ("spend", "Spend (EUR)", "num"), ("on_time_pct", "On time (%)", "num"),
                 ("orders", "Shipments", "num"), ("late_orders", "Late", "num")],
            formats={"period": fmt.week, "spend": FORMATTERS[ai_insights.F_INT], "on_time_pct": FORMATTERS[ai_insights.F_1DP],
                     "orders": FORMATTERS[ai_insights.F_INT], "late_orders": FORMATTERS[ai_insights.F_INT]},
        ) if len(tr) <= 60 else None
        charts.chart_card(
            "trend", "Freight spend and on-time delivery by week",
            "Two measures, two panels sharing one week axis. Edge weeks clipped by the filter are dropped.",
            lambda: charts.trend_two_panel(tr, kpis["on_time_pct"], th),
            table if table is not None else ui.caption("Weekly figures above 60 rows are in the Weekly figures tab."),
            foot="Weekly buckets hold enough shipments for a rate to mean something; a daily rate on nine shipments is noise.",
            insufficient=(f"Not enough data to draw this chart. {len(tr)} weeks of data; 3 needed." if len(tr) < 3 else None),
        )

    rates, counts = bundle["rates"], bundle["counts"]
    late = (100 - rates).reset_index() if not rates.empty else pd.DataFrame()
    cols = [("carrier", "Carrier", "text")] + [(c, str(c), "num") for c in (rates.columns if not rates.empty else [])]
    charts.chart_card(
        "lanes", "Late rate by carrier and destination",
        f"Share of shipments delivered late, %. Lanes under {metrics.MIN_LANE_SHIPMENTS} shipments read none. "
        "Columns run worst average first.",
        lambda: charts.late_heatmap(rates, counts, th, metrics.MIN_LANE_SHIPMENTS) if not rates.empty else None,
        ui.html_table(late, cols, compact=True, formats={c: FORMATTERS[ai_insights.F_1DP] for c in (rates.columns if not rates.empty else [])})
        if not rates.empty else ui.empty_state("No delivered shipments in this view."),
        foot="One late shipment out of two is 50% late, which is noise, not a signal, so thin lanes are masked rather than shown.",
        insufficient=None if not rates.empty else "No delivered shipments in this view.",
    )


def render_tabs(bundle: dict, cleaning_log: dict | None) -> None:
    tab_carriers, tab_weeks, tab_lineage = st.tabs(["Carrier detail", "Weekly figures", "Data lineage"])
    with tab_carriers:
        bc = bundle["by_carrier"].copy()
        pen = bundle["view"].loc[~bundle["view"]["is_cancelled"]].groupby("carrier")["late_penalty_eur"].sum()
        bc["penalties"] = bc["carrier"].map(pen).fillna(0.0)
        md(ui.html_table(bc, [("carrier", "Carrier", "text"), ("orders", "Shipments", "num"), ("billable_orders", "Billable", "num"),
                              ("spend", "Spend (EUR)", "num"), ("on_time_pct", "On time (%)", "num"), ("penalties", "Penalties (EUR)", "num")],
                         formats={"orders": FORMATTERS[ai_insights.F_INT], "billable_orders": FORMATTERS[ai_insights.F_INT],
                                  "spend": FORMATTERS[ai_insights.F_INT], "on_time_pct": FORMATTERS[ai_insights.F_1DP],
                                  "penalties": FORMATTERS[ai_insights.F_INT]},
                         totals={"carrier": "Total", "orders": fmt.count(bc["orders"].sum()),
                                 "billable_orders": fmt.count(bc["billable_orders"].sum()),
                                 "spend": fmt.group(bc["spend"].sum()), "penalties": fmt.group(bc["penalties"].sum())}))
        md(ui.caption("Shipments counts every row for the carrier; spend covers billable rows only. Both are stated so the columns reconcile with the KPI tiles."))
    with tab_weeks:
        tr = bundle["trend"].copy()
        tr["period"] = tr["period"].dt.date
        st.dataframe(
            tr, use_container_width=True, hide_index=True, height=min(35 * (len(tr) + 1) + 2, 560),
            column_config={
                "period": st.column_config.DateColumn("Week starting", format="YYYY-MM-DD"),
                "spend": st.column_config.NumberColumn("Spend (EUR)", format="%d"),
                "on_time_pct": st.column_config.NumberColumn("On time (%)", format="%.1f"),
                "orders": st.column_config.NumberColumn("Shipments", format="%d"),
                "late_orders": st.column_config.NumberColumn("Late", format="%d"),
                "penalties": st.column_config.NumberColumn("Penalties (EUR)", format="%d"),
                "avg_delay": st.column_config.NumberColumn("Delay when late (days)", format="%.1f"),
            },
        )
        md(ui.caption(f"{fmt.count(len(tr))} weeks. Above 60 rows this table renders with st.dataframe for sorting; "
                      "it keeps the same columns as the chart."))
    with tab_lineage:
        log = cleaning_log
        if not log:
            md(ui.alert("neutral", "No cleaning log found", "Re-run <code>python pipeline/clean.py</code> to produce one."))
            return
        a, b, c = st.columns(3)
        a.markdown(ui.kpi("Rows ingested", fmt.count(log["rows_in"]), spoken=f"{fmt.count(log['rows_in'])} rows"), unsafe_allow_html=True)
        b.markdown(ui.kpi("Rows removed", fmt.count(log["rows_removed"]), spoken=f"{fmt.count(log['rows_removed'])} rows",
                          note="Every removed row has a logged reason."), unsafe_allow_html=True)
        c.markdown(ui.kpi("Rows in the briefing", fmt.count(log["rows_out"]), spoken=f"{fmt.count(log['rows_out'])} rows"), unsafe_allow_html=True)
        kind = "good" if log["reconciles"] else "critical"
        title = "Row counts reconcile" if log["reconciles"] else "Critical: row counts do not reconcile"
        md(ui.alert(kind, title, f"Sources: {ui.esc(', '.join(log['sources']))}. Built {ui.esc(str(log.get('generated_at_utc', 'unknown')))} UTC."
                    + ("" if log["reconciles"] else " Investigate before sharing.")))
        steps = pd.DataFrame(log["steps"])
        md(ui.html_table(steps, [("step", "Step", "text"), ("action", "Action", "text"), ("rows_affected", "Rows", "num"), ("detail", "Detail", "text")],
                         compact=True, formats={"rows_affected": FORMATTERS[ai_insights.F_INT]}))


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------

def main() -> None:
    th = theme.inject()
    theme.plotly_template(th)

    try:
        chosen = sidebar_source()
    except (FileNotFoundError, RuntimeError) as exc:
        md(ui.alert("critical", "Critical: the dataset could not be loaded", ui.esc(str(exc))))
        st.stop()

    build_date = fmt.iso(pd.Timestamp.now(tz="UTC"))
    md(ui.masthead("Executive briefing", CLIENT_NAME or None, build_date, "Freight operations briefing"))
    running = st.empty()

    if chosen is None:
        running.markdown(ui.running_header([("", "Waiting for shipment exports")], None), unsafe_allow_html=True)
        md(ui.alert("neutral", "Drop your exports in the sidebar",
                    "The briefing appears here once the files are reconciled. Nothing is stored."))
        st.stop()
    df, cleaning_log, signature = chosen

    start, end, carriers = filters(df)
    bundle = build_view(df, signature, start, end, carriers)
    view = bundle["view"]
    if view.empty:
        running.markdown(ui.running_header([("Period", fmt.week_range(start, end))], None), unsafe_allow_html=True)
        md(ui.alert("neutral", "No shipments match the current filters",
                    "Widen the period or clear the carrier selection."))
        st.stop()

    kpis, summary = bundle["kpis"], bundle["summary"]
    freshness = cleaning_log.get("generated_at_utc") if cleaning_log else None
    running.markdown(ui.running_header(
        [("Period", fmt.week_range(view["ship_date"].min(), view["ship_date"].max())),
         ("", f"{fmt.count(kpis['orders'])} shipments, {fmt.count(kpis['excluded_from_spend'])} excluded from spend"),
         ("Data as of", f"{ui.esc(str(freshness))} UTC" if freshness else fmt.iso(view['ship_date'].max())),
         ("Report currency", "EUR")],
        f"{ui.unit('EUR')}{fmt.compact(summary['hero_eur'])} leaking",
    ), unsafe_allow_html=True)

    render_summary(summary, th)
    render_kpis(bundle)

    if kpis["excluded_from_spend"]:
        md(ui.alert(
            "warning",
            f"Warning: {fmt.count(kpis['excluded_from_spend'])} of {fmt.count(kpis['orders'])} shipments are excluded from spend",
            f"{fmt.count(kpis['cancelled_orders'])} cancelled and {fmt.count(kpis['outlier_orders'])} flagged as cost outliers. "
            "They stay in the shipment count and are left out of every spend figure, including the findings.",
        ))

    findings = bundle["findings"]
    md(ui.section("Findings", len(findings),
                  "Ordered by money at stake. Severity is the share of period spend: warning from 0.1%, serious from 0.3%, critical from 1%."))
    if findings:
        for i, f in enumerate(findings, start=1):
            render_finding(i, len(findings), f)
    else:
        render_no_findings(summary, ai_insights.period_label(view))
    md(ui.caption("Every figure above is computed from the filtered view by utils/ai_insights.py. "
                  "Detection is deterministic pandas, not a language model, so there is nothing here to hallucinate."))

    md(ui.section("Analysis"))
    render_analysis(bundle, th)

    md(ui.section("Detail"))
    render_tabs(bundle, cleaning_log)


if __name__ == "__main__":
    main()
