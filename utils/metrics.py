"""
Pure analytics layer — no Streamlit, no Plotly.

Everything the dashboard shows is computed here so it can be unit-tested
without a browser or a running app. app.py only wraps these in @st.cache_data.

ONE RULE GOVERNS THIS FILE: every count the UI can display must reconcile
with every other count the UI can display. Three different populations are
legitimately in play —

    all        every shipment in the filtered view          -> "Shipments" KPI
    active     all minus cancelled (never delivered)        -> on-time %, delay
    billable   active minus flagged cost outliers           -> spend

— and mixing them silently is how a dashboard loses a client's trust. So each
function states which population it used, and `compute_kpis` returns the
exclusion counts so the UI can show its working.
"""

from __future__ import annotations

import pandas as pd

from utils import fmt
from utils.theme import CARRIER_ORDER


def filter_shipments(
    df: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    carriers: tuple[str, ...] = (),
) -> pd.DataFrame:
    mask = df["ship_date"].between(start, end)
    if carriers:
        mask &= df["carrier"].isin(carriers)
    return df.loc[mask]


def compute_kpis(df: pd.DataFrame) -> dict:
    """The four headline numbers, plus everything needed to explain them.

    `orders` counts every shipment in view. `billable_orders` is the population
    behind `total_spend`; the difference is broken out as `cancelled_orders`
    and `outlier_orders` so the UI never shows an unexplained gap.
    """
    active = df.loc[~df["is_cancelled"]]
    billable = df.loc[df["is_billable"]]
    late = active.loc[active["is_late"]]
    return {
        "total_spend": float(billable["freight_cost_eur"].sum()),
        "orders": int(len(df)),
        "billable_orders": int(len(billable)),
        "active_orders": int(len(active)),
        "cancelled_orders": int(df["is_cancelled"].sum()),
        "outlier_orders": int(df["cost_is_outlier"].sum()),
        "excluded_from_spend": int((df["is_cancelled"] | df["cost_is_outlier"]).sum()),
        "on_time_pct": float(100 * active["is_on_time"].mean()) if len(active) else 0.0,
        "avg_delay": float(late["delay_days"].mean()) if len(late) else 0.0,
        "late_orders": int(len(late)),
        "penalties": float(active["late_penalty_eur"].sum()),
    }


def spend_by_carrier(df: pd.DataFrame) -> pd.DataFrame:
    """Spend, volume and on-time rate per carrier, in fixed carrier order.

    `orders` counts every shipment for that carrier, so the column sums to the
    "Shipments" KPI. `spend` covers only `billable_orders` of them, and
    `on_time_pct` only the non-cancelled ones — both stated per row rather than
    left for the client to discover by adding up the bars.

    Every carrier present in the view is returned even if none of its shipments
    are billable, so a narrow filter can never drop a carrier from the chart
    while it still counts toward the KPI cards.
    """
    cols = ["carrier", "spend", "orders", "billable_orders", "on_time_pct"]
    if df.empty:
        return pd.DataFrame(columns=cols)

    out = df.groupby("carrier").agg(orders=("order_id", "count")).reset_index()

    billable = (
        df.loc[df["is_billable"]]
        .groupby("carrier")
        .agg(spend=("freight_cost_eur", "sum"), billable_orders=("order_id", "count"))
        .reset_index()
    )
    on_time = (
        df.loc[~df["is_cancelled"]]
        .groupby("carrier")["is_on_time"]
        .mean()
        .mul(100)
        .rename("on_time_pct")
        .reset_index()
    )

    out = out.merge(billable, on="carrier", how="left").merge(on_time, on="carrier", how="left")
    out["spend"] = out["spend"].fillna(0.0)
    out["billable_orders"] = out["billable_orders"].fillna(0).astype("int64")

    rank = {c: i for i, c in enumerate(CARRIER_ORDER)}
    out["_rank"] = out["carrier"].map(rank).fillna(len(rank))
    return out.sort_values("_rank").drop(columns="_rank")[cols].reset_index(drop=True)


# --------------------------------------------------------------------------
# V1 analytics
# --------------------------------------------------------------------------

# Below this many shipments a percentage is noise, not a signal. One late
# shipment on a two-shipment lane is 50% late, which would paint the heatmap
# with alarming cells that mean nothing. Sparse cells are masked, not shown.
MIN_LANE_SHIPMENTS = 8


def trend(df: pd.DataFrame, grain: str = "week") -> pd.DataFrame:
    """Spend and on-time rate over time, one row per period.

    Weekly by default, deliberately. The dataset averages ~9 shipments a day,
    so a daily on-time rate swings between 0% and 100% on sample size alone —
    a chart of noise that invites the client to read a story into it. Weekly
    buckets hold ~60 shipments each, which is enough for the rate to mean
    something.
    """
    column = {"day": "ship_date", "week": "ship_week", "month": "ship_month"}[grain]
    if df.empty:
        return pd.DataFrame(columns=["period", "spend", "on_time_pct", "orders", "late_orders",
                                     "penalties", "avg_delay"])

    active = df.loc[~df["is_cancelled"]]
    billable = df.loc[df["is_billable"]]
    late = active.loc[active["is_late"]]

    spend = billable.groupby(column)["freight_cost_eur"].sum().rename("spend")
    service = active.groupby(column).agg(
        on_time_pct=("is_on_time", lambda s: 100 * s.mean()),
        orders=("order_id", "count"),
        late_orders=("is_late", "sum"),
        penalties=("late_penalty_eur", "sum"),
    )
    # Mean delay over the late shipments only, so a week with no late
    # shipments is a gap in the sparkline rather than a zero.
    avg_delay = late.groupby(column)["delay_days"].mean().rename("avg_delay")
    out = pd.concat([spend, service, avg_delay], axis=1).reset_index()
    out = out.rename(columns={column: "period"}).sort_values("period")
    out["spend"] = out["spend"].fillna(0.0)
    out = out.reset_index(drop=True)

    # Drop partial buckets at either end. The first and last period are usually
    # clipped by the filter window, so they hold a fraction of a week's
    # shipments and plot as a cliff down to near zero — an artefact of the
    # calendar that reads as a collapse in business. Only trimmed when enough
    # periods remain for the trend to still mean something.
    if grain != "day" and len(out) >= 4:
        span = {"week": pd.Timedelta(days=6), "month": pd.offsets.MonthEnd(0)}[grain]
        first, last = out["period"].iloc[0], out["period"].iloc[-1]
        drop_first = first < df["ship_date"].min().normalize()
        drop_last = (last + span) > df["ship_date"].max().normalize()
        if drop_first:
            out = out.iloc[1:]
        if drop_last and len(out) > 2:
            out = out.iloc[:-1]
        out = out.reset_index(drop=True)
    return out


def carrier_destination_matrix(
    df: pd.DataFrame, min_shipments: int = MIN_LANE_SHIPMENTS
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """On-time % per carrier × destination country, plus the shipment counts.

    Returns (rates, counts) with identical shape and labels. Cells thinner than
    `min_shipments` are NaN in `rates` — the count is still returned so the UI
    can say "too few shipments" rather than leaving an unexplained hole.

    Columns are ordered worst-performing first, so the lane that costs money is
    the one the reader's eye lands on.
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    active = df.loc[~df["is_cancelled"]]
    if active.empty:
        return pd.DataFrame(), pd.DataFrame()

    counts = active.pivot_table(
        index="carrier", columns="destination_country",
        values="order_id", aggfunc="count", fill_value=0,
    )
    rates = active.pivot_table(
        index="carrier", columns="destination_country",
        values="is_on_time", aggfunc="mean",
    ) * 100
    rates = rates.where(counts >= min_shipments)

    order = [c for c in CARRIER_ORDER if c in rates.index]
    order += [c for c in rates.index if c not in order]
    rates, counts = rates.reindex(order), counts.reindex(order)

    # Worst lanes first — the reader should not have to hunt for the problem.
    col_order = rates.mean(axis=0, skipna=True).sort_values().index
    return rates[col_order], counts[col_order]


WEEKDAYS_TESTED = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def weekday_effects(df: pd.DataFrame, regions: dict[str, set[str]]) -> list[dict]:
    """Every carrier-by-region weekday comparison, from one grouped pass.

    The comparison itself is unchanged: within one carrier's shipments into one
    region, each weekday's mean transit is measured against that same scope's
    other days, so a slow lane is judged against its own baseline rather than
    against the portfolio. This is the shape of finding the briefing exists to
    surface. Only the arithmetic moved.

    It used to re-slice the frame for every carrier, region and weekday in turn
    -- around two hundred full-frame copies per filter change, 1.4s of a 1.6s
    rerun at 5k rows, and worse in proportion on a client's real book. The same
    numbers fall out of a single groupby, because "the other days" is just the
    scope total minus the day, and a total does not need slicing twice.

    Returns the strongest day per carrier and region, ordered by carrier then by
    the order of `regions`, so a caller ranking these breaks ties exactly where
    the nested loops did.
    """
    needed = ["carrier", "destination_country", "ship_weekday",
              "transit_days", "is_late", "late_penalty_eur"]
    active = df.loc[~df["is_cancelled"], needed]
    if active.empty:
        return []

    # A country could in principle be listed under two regions, so rows are
    # exploded onto their regions rather than assigned one. Disjoint regions
    # copy nothing; this only stops an overlapping edit from losing rows.
    membership: dict[str, list[str]] = {}
    for region, countries in regions.items():
        for country in countries:
            membership.setdefault(country, []).append(region)
    active = active.assign(region=active["destination_country"].map(membership))
    active = active.dropna(subset=["region"]).explode("region")
    if active.empty:
        return []

    # dropna=False keeps rows carrying no weekday inside the scope totals. They
    # are never the subject day, but they are part of "the other days" -- which
    # is what the row-by-row version did when it tested `weekday != day`.
    cells = active.groupby(["carrier", "region", "ship_weekday"],
                           observed=True, dropna=False).agg(
        n=("is_late", "size"),
        transit_sum=("transit_days", "sum"),
        transit_n=("transit_days", "count"),
        late_n=("is_late", "sum"),
        penalties=("late_penalty_eur", "sum"),
    )
    scopes = cells.groupby(level=["carrier", "region"], observed=True).sum().to_dict("index")
    cells = cells.to_dict("index")

    out: list[dict] = []
    for carrier in sorted(df["carrier"].dropna().unique()):
        for region, countries in regions.items():
            scope = scopes.get((carrier, region))
            if scope is None or scope["n"] < MIN_LANE_SHIPMENTS * 2:
                continue
            best: dict | None = None
            for day in WEEKDAYS_TESTED:
                cell = cells.get((carrier, region, day))
                if cell is None:
                    continue
                subject_n = int(cell["n"])
                rest_n = int(scope["n"]) - subject_n
                if subject_n < MIN_LANE_SHIPMENTS or rest_n < MIN_LANE_SHIPMENTS:
                    continue
                rest_transit_n = scope["transit_n"] - cell["transit_n"]
                base_transit = ((scope["transit_sum"] - cell["transit_sum"]) / rest_transit_n
                                if rest_transit_n else float("nan"))
                if not base_transit:
                    continue
                subject_transit = (cell["transit_sum"] / cell["transit_n"]
                                   if cell["transit_n"] else float("nan"))
                finding = {
                    "carrier": carrier,
                    "weekday": day,
                    "region": region,
                    "destinations": sorted(countries) if countries else None,
                    "shipments": subject_n,
                    "baseline_shipments": rest_n,
                    "transit_uplift_pct": 100 * (subject_transit / base_transit - 1),
                    "late_pct": 100 * float(cell["late_n"]) / subject_n,
                    "baseline_late_pct": 100 * float(scope["late_n"] - cell["late_n"]) / rest_n,
                    "penalties_eur": float(cell["penalties"]),
                }
                if best is None or finding["transit_uplift_pct"] > best["transit_uplift_pct"]:
                    best = finding
            if best is not None:
                out.append(best)
    return out


def worst_lanes(df: pd.DataFrame, limit: int = 3) -> pd.DataFrame:
    """The carrier × destination lanes losing the most money to late delivery."""
    active = df.loc[~df["is_cancelled"]]
    if active.empty:
        return pd.DataFrame(columns=["carrier", "destination_country", "orders",
                                     "late_pct", "penalties"])
    lanes = (
        active.groupby(["carrier", "destination_country"])
        .agg(
            orders=("order_id", "count"),
            late_pct=("is_late", lambda s: 100 * s.mean()),
            penalties=("late_penalty_eur", "sum"),
        )
        .reset_index()
    )
    lanes = lanes.loc[lanes["orders"] >= MIN_LANE_SHIPMENTS]
    return lanes.sort_values("penalties", ascending=False).head(limit).reset_index(drop=True)


def eur(value: float) -> str:
    """Compact money, for KPI cards and axis labels: 'EUR 1.5k', 'EUR 184k'.

    Formatting rules live in utils/fmt.py (design system, section 6). This
    stays as the analytics layer's name for them.
    """
    return fmt.money(value)


def eur_exact(value: float) -> str:
    """Money to the euro, for the briefing: 'EUR 1 530'.

    A briefing is read as a claim, so it quotes the figure rather than a
    rounded shape of it. "EUR 1 530 in penalties" survives being checked
    against the table; "EUR 2k" does not.
    """
    return fmt.money(value, exact=True)
