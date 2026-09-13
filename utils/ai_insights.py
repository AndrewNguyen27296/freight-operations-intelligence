"""
Executive briefing layer.

WHAT THIS IS, PRECISELY
-----------------------
The findings below are *computed*, not generated. Every number in a briefing
comes out of pandas, and every sentence is assembled from those numbers by
`narrate()` or `build_findings()`. Nothing is inferred by a language model, so
nothing can be hallucinated, which is the architectural invariant this whole
portfolio is sold on. The UI says so too; claiming an LLM wrote this would be
a lie a client could catch.

THE SEAM FOR THE LLM
--------------------
`build_evidence()` produces a JSON-serialisable dict of established facts, and
`PROMPT` wraps it in an instruction that forbids inventing numbers. When the
Anthropic call is wired up, it replaces exactly one function, `narrate()`, and
the model's job is phrasing, never arithmetic. Detection stays here in Python,
where it can be unit-tested. That split is the point: the hard part of "AI
insights" is finding the signal, and a model is the wrong tool for it.

TWO OUTPUTS, ONE SET OF FACTS
-----------------------------
`generate_brief()` returns three markdown bullets, the original form and the
one the tests trace number by number. `build_findings()` returns the same
findings as structured records for the findings panel of the design system:
a headline claim, support sentences, a recommended action, a pulled-out figure
with its basis, a severity set by rule, and the evidence table the reader
opens to check the claim. Both are built from `build_evidence()`.

HOUSE STYLE
-----------
Blunt operator. Number first, money second, action third. No hedging, no
"it appears", no adjectives of degree. Sentence case. No em dashes, because
nothing marks text as machine-written faster. Short sentences do the same job
and read harder.
"""

from __future__ import annotations

import textwrap
from typing import Iterator

import pandas as pd

from utils import fmt, metrics

# Regions worth testing for a weekday effect. Keys are what a reader calls the
# place; the briefing quotes the key, not the country codes.
REGIONS: dict[str, set[str]] = {
    "Central Europe": {"DE", "AT", "CH", "PL", "CZ"},
    "the Nordics": {"SE", "NO", "DK", "FI"},
    "Southern Europe": {"IT", "ES", "FR"},
}

PREVIOUS_DAY = {
    "Monday": "the Friday before", "Tuesday": "Monday", "Wednesday": "Tuesday",
    "Thursday": "Wednesday", "Friday": "Thursday",
}

# A weekday effect below this is within normal variation, not worth a client's
# attention, and quoting it would train them to distrust the ones that matter.
MIN_UPLIFT_PCT = 12.0
MIN_LATE_GAP_PCT = 8.0

# Severity is set by rule, not by tone. The measure is leakage as a share of
# freight spend in the same period, because a share scales from a customer
# spending 500k to one spending 50M where an absolute figure does not.
# Recalibrate after the first three real builds.
THRESHOLDS = {"warning": 0.1, "serious": 0.3, "critical": 1.0}

PENALTY_PER_DAY_EUR = 45.0


def severity(share_pct: float) -> str:
    if share_pct >= THRESHOLDS["critical"]:
        return "critical"
    if share_pct >= THRESHOLDS["serious"]:
        return "serious"
    if share_pct >= THRESHOLDS["warning"]:
        return "warning"
    return "good"


# --------------------------------------------------------------------------
# Detection, pure pandas, unit-testable, no model involved
# --------------------------------------------------------------------------

def detect_weekday_signal(df: pd.DataFrame) -> dict | None:
    """Scan every carrier and region for a weekday that behaves differently.

    Deliberately a search, not a lookup: the dashboard has to find this on a
    client's data, where nobody has told it what to look for. Ranked by the
    money at stake rather than by the size of the percentage, because a 40%
    uplift on six shipments is trivia.
    """
    candidates: list[dict] = []
    for carrier in sorted(df["carrier"].dropna().unique()):
        for region, countries in REGIONS.items():
            finding = metrics.weekday_effect(df, carrier, countries)
            if finding is None:
                continue
            gap = finding["late_pct"] - finding["baseline_late_pct"]
            if finding["transit_uplift_pct"] < MIN_UPLIFT_PCT or gap < MIN_LATE_GAP_PCT:
                continue
            finding["region"] = region
            finding["late_gap_pct"] = gap
            candidates.append(finding)

    if not candidates:
        return None
    return max(candidates, key=lambda f: f["penalties_eur"])


def build_evidence(df: pd.DataFrame) -> dict:
    """Everything established about the current view, as plain data.

    This is what would be handed to a model: facts only, already computed.
    """
    kpis = metrics.compute_kpis(df)
    by_carrier = metrics.spend_by_carrier(df)

    weakest = None
    if not by_carrier.empty and by_carrier["on_time_pct"].notna().any():
        row = by_carrier.loc[by_carrier["on_time_pct"].idxmin()]
        weakest = {
            "carrier": str(row["carrier"]),
            "on_time_pct": float(row["on_time_pct"]),
            "orders": int(row["orders"]),
            "spend": float(row["spend"]),
        }

    lanes = metrics.worst_lanes(df, limit=3)
    return {
        "period": {
            "from": df["ship_date"].min().strftime("%d %b %Y"),
            "to": df["ship_date"].max().strftime("%d %b %Y"),
        },
        "kpis": kpis,
        "weekday_signal": detect_weekday_signal(df),
        "weakest_carrier": weakest,
        "worst_lanes": lanes.to_dict("records"),
        "portfolio_on_time_pct": kpis["on_time_pct"],
    }


# --------------------------------------------------------------------------
# Narration, the one function an LLM would replace
# --------------------------------------------------------------------------

PROMPT = textwrap.dedent(
    """
    You are writing a freight operations briefing for a VP of Operations.

    Below is EVIDENCE: figures already computed from the client's shipment
    data. Write at most three bullets in this house style:

      - Lead with the number. Then the money. Then what to do about it.
      - No hedging, no "it appears", no restating the question.
      - One sentence of action per bullet, phrased as an instruction.

    HARD RULE: every figure you write must appear verbatim in the EVIDENCE.
    You may not calculate, estimate, extrapolate or round differently. If the
    evidence does not support a point, omit the bullet. Inventing a number is
    the only unrecoverable failure here.

    EVIDENCE:
    {evidence}
    """
).strip()


def narrate(evidence: dict) -> list[str]:
    """Compose the briefing from the evidence. Deterministic by design."""
    bullets: list[str] = []
    kpis = evidence["kpis"]

    signal = evidence.get("weekday_signal")
    if signal:
        where = f" {signal['region']}" if signal.get("region") else ""
        day_before = PREVIOUS_DAY.get(signal["weekday"], "the previous day")
        bullets.append(
            f"**{signal['weekday']} is where{where} is losing you money.** "
            f"{signal['late_pct']:.0f}% of {signal['carrier']}'s {signal['weekday']} "
            f"dispatches land late. Any other weekday it is "
            f"{signal['baseline_late_pct']:.0f}%. Transit runs "
            f"{signal['transit_uplift_pct']:.0f}% longer across "
            f"{signal['shipments']:,} shipments and the penalties come to "
            f"{metrics.eur_exact(signal['penalties_eur'])}. "
            f"Shift {signal['weekday']} volume to {day_before} and get a written "
            f"cut-off time out of {signal['carrier']}."
        )

    lanes = evidence.get("worst_lanes") or []
    if lanes:
        top = lanes[0]
        already = signal and top["carrier"] == signal["carrier"]
        bullets.append(
            f"**Your worst single lane is {top['carrier']} into "
            f"{top['destination_country']}.** {top['late_pct']:.0f}% late across "
            f"{top['orders']:,} shipments, {metrics.eur_exact(top['penalties'])} "
            "in penalties. "
            + (
                "Same carrier as the point above, so make it one commercial "
                "conversation rather than two."
                if already
                else f"Re-tender it, or price the penalty into what you pay "
                     f"{top['carrier']}."
            )
        )

    weak = evidence.get("weakest_carrier")
    if weak and weak["on_time_pct"] < evidence["portfolio_on_time_pct"] - 10:
        gap = evidence["portfolio_on_time_pct"] - weak["on_time_pct"]
        # If the worst lane belongs to this carrier, say so. Three bullets that
        # circle one carrier without naming the pattern reads as padding.
        shared = bool(lanes) and lanes[0]["carrier"] == weak["carrier"]
        lead = (
            f"**{weak['carrier']} is not one bad lane.** It runs {gap:.0f} points "
            f"below the book at {weak['on_time_pct']:.0f}% on time."
            if shared
            else f"**{weak['carrier']} runs {gap:.0f} points below the book, at "
                 f"{weak['on_time_pct']:.0f}% on time.**"
        )
        bullets.append(
            f"{lead} That is {weak['orders']:,} shipments and "
            f"{metrics.eur(weak['spend'])} of spend riding on the weakest service "
            "in the book. Cap its share of time-critical freight and put the "
            "contract on the next review agenda."
        )

    if not bullets:
        bullets.append(
            f"**Nothing in this view is worth escalating.** "
            f"{kpis['on_time_pct']:.1f}% on time across {kpis['orders']:,} shipments, "
            f"with {metrics.eur_exact(kpis['penalties'])} of penalties. "
            "Widen the date range or clear the carrier filter to go looking."
        )
    return bullets[:3]


def generate_brief(df: pd.DataFrame) -> tuple[list[str], dict]:
    """The briefing and the evidence it was built from."""
    evidence = build_evidence(df)
    return narrate(evidence), evidence


def stream_brief(df: pd.DataFrame, chunk_words: int = 3) -> Iterator[str]:
    """Yield the briefing in chunks, for st.write_stream.

    A generator rather than a finished string so that swapping in a real
    streaming API later changes nothing above this line.
    """
    bullets, _ = generate_brief(df)
    for i, bullet in enumerate(bullets):
        if i:
            yield "\n\n"
        words = bullet.split(" ")
        for j in range(0, len(words), chunk_words):
            yield " ".join(words[j:j + chunk_words]) + " "


# --------------------------------------------------------------------------
# Structured findings for the findings panel (design system 4.11)
# --------------------------------------------------------------------------

# Formatter names, resolved by the UI. Names rather than callables so that a
# finding survives st.cache_data, which pickles what it stores.
F_INT, F_1DP, F_MONEY, F_PCT1 = "int", "1dp", "money_exact", "pct1"


def period_label(df: pd.DataFrame) -> str:
    return fmt.week_range(df["ship_date"].min(), df["ship_date"].max())


def _share(eur: float, spend: float) -> float:
    return 100.0 * eur / spend if spend else 0.0


def _n_words(n: int) -> str:
    return {0: "No", 1: "One", 2: "Two", 3: "Three"}.get(n, str(n))


def build_findings(df: pd.DataFrame) -> list[dict]:
    """The findings a reader can open and check, ordered by money at stake.

    Each record carries: kind, severity, share_pct, leak_eur, claim, support
    (list), action, figure_eur, figure_label, figure_basis, evidence (frame),
    columns (for the table), formats, cite, method, exclusions.
    """
    if df.empty:
        return []
    evidence = build_evidence(df)
    kpis = evidence["kpis"]
    spend = float(kpis["total_spend"])
    period = period_label(df)
    active = df.loc[~df["is_cancelled"]]
    penalties_by_carrier = active.groupby("carrier")["late_penalty_eur"].sum()
    total_pen = float(kpis["penalties"])
    findings: list[dict] = []

    # 1. The weakest carrier in the book.
    weak = evidence.get("weakest_carrier")
    if weak and weak["on_time_pct"] < kpis["on_time_pct"] - 10:
        carrier = weak["carrier"]
        pen = float(penalties_by_carrier.get(carrier, 0.0))
        gap = kpis["on_time_pct"] - weak["on_time_pct"]
        rows = active.loc[active["carrier"] == carrier]
        late_n = int(rows["is_late"].sum())
        lanes_c = metrics.worst_lanes(df.loc[df["carrier"] == carrier], limit=1)
        by_carrier = metrics.spend_by_carrier(df)
        by_carrier["penalties"] = by_carrier["carrier"].map(penalties_by_carrier).fillna(0.0)
        row_pos = int(by_carrier.index[by_carrier["carrier"] == carrier][0])
        worst_lane = (
            f"Its worst lane is {lanes_c.iloc[0]['destination_country']} at "
            f"{fmt.pct(lanes_c.iloc[0]['late_pct'])} late across {fmt.count(lanes_c.iloc[0]['orders'])} shipments."
            if len(lanes_c) else "No single lane carries enough shipments to rank."
        )
        findings.append({
            "key": "weakest_carrier", "kind": "Finding", "leak_eur": pen,
            "claim": (f"{carrier} runs {gap:.0f} points below the book at {fmt.pct(weak['on_time_pct'])} on time, "
                      f"with {fmt.money(pen, exact=True)} in late penalties across {fmt.count(weak['orders'])} shipments."),
            "support": [
                (f"The book runs at {fmt.pct(kpis['on_time_pct'])} on time across {fmt.count(kpis['orders'])} shipments; "
                 f"{carrier} carries {fmt.pct(100.0 * weak['orders'] / kpis['orders'])} of them and "
                 f"{fmt.pct(_share(pen, total_pen))} of all penalties."),
                worst_lane,
                (f"{fmt.count(late_n)} of its shipments arrived late. Penalties are {fmt.money(PENALTY_PER_DAY_EUR, exact=True)} "
                 f"per day late; cancelled shipments are excluded."),
            ],
            "action": (f"Cap {carrier}'s share of time-critical freight and put the contract on the next review agenda, "
                       f"with the {fmt.money(pen, exact=True)} in penalties as the opening figure."),
            "figure_eur": pen, "figure_label": f"Late penalties on {carrier}",
            "figure_basis": f"{period}, {fmt.count(weak['orders'])} shipments",
            "evidence": by_carrier,
            "columns": [("carrier", "Carrier", "text"), ("orders", "Shipments", "num"),
                        ("spend", "Spend (EUR)", "num"), ("on_time_pct", "On time (%)", "num"),
                        ("penalties", "Penalties (EUR)", "num")],
            "formats": {"orders": F_INT, "spend": F_INT, "on_time_pct": F_1DP, "penalties": F_INT},
            "cite": [(row_pos, "on_time_pct"), (row_pos, "penalties")],
            "method": "On time is the share of non-cancelled shipments delivered by the promised date. Spend covers billable shipments only.",
            "exclusions": f"{fmt.count(kpis['cancelled_orders'])} cancelled and {fmt.count(kpis['outlier_orders'])} cost-outlier shipments excluded from spend.",
        })

    # 2. A weekday that behaves differently.
    signal = evidence.get("weekday_signal")
    if signal:
        carrier, day, region = signal["carrier"], signal["weekday"], signal["region"]
        pen = float(signal["penalties_eur"])
        scope = active.loc[(active["carrier"] == carrier) & active["destination_country"].isin(REGIONS[region])]
        table = (
            scope.groupby("ship_weekday")
            .agg(shipments=("order_id", "count"), late_pct=("is_late", lambda s: 100 * s.mean()),
                 transit_days=("transit_days", "mean"), penalties=("late_penalty_eur", "sum"))
            .reindex(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
            .dropna(subset=["shipments"]).reset_index().rename(columns={"ship_weekday": "weekday"})
        )
        row_pos = int(table.index[table["weekday"] == day][0]) if (table["weekday"] == day).any() else 0
        findings.append({
            "key": "weekday", "kind": "Finding", "leak_eur": pen,
            "claim": (f"{carrier} {day} dispatches to {region} arrive late {fmt.pct(signal['late_pct'])} of the time, "
                      f"against {fmt.pct(signal['baseline_late_pct'])} on other weekdays."),
            "support": [
                (f"Transit runs {fmt.pct(signal['transit_uplift_pct'])} longer on {day} across "
                 f"{fmt.count(signal['shipments'])} shipments; the other weekdays hold {fmt.count(signal['baseline_shipments'])}."),
                f"Penalties on those {day} dispatches come to {fmt.money(pen, exact=True)} in the period.",
                (f"A weekday under {metrics.MIN_LANE_SHIPMENTS} shipments is not tested, so the comparison covers "
                 f"{fmt.count(signal['shipments'] + signal['baseline_shipments'])} shipments."),
            ],
            "action": (f"Shift {day} volume to {PREVIOUS_DAY.get(day, 'the previous day')} and get a written "
                       f"cut-off time from {carrier} for {region}."),
            "figure_eur": pen, "figure_label": f"Late penalties on {day} dispatches",
            "figure_basis": f"{period}, {fmt.count(signal['shipments'])} shipments",
            "evidence": table,
            "columns": [("weekday", "Dispatch weekday", "text"), ("shipments", "Shipments", "num"),
                        ("late_pct", "Late (%)", "num"), ("transit_days", "Mean transit (days)", "num"),
                        ("penalties", "Penalties (EUR)", "num")],
            "formats": {"shipments": F_INT, "late_pct": F_1DP, "transit_days": F_1DP, "penalties": F_INT},
            "cite": [(row_pos, "late_pct"), (row_pos, "penalties")],
            "method": f"Scope is {carrier} shipments into {region}, cancelled shipments excluded. Late is delivery after the promised date.",
            "exclusions": "Weekdays under the minimum shipment count are shown but not compared.",
        })

    # 3. The single lane losing the most.
    lanes = metrics.worst_lanes(df, limit=5)
    if len(lanes):
        top = lanes.iloc[0]
        pen = float(top["penalties"])
        book_late = 100.0 * float(active["is_late"].mean()) if len(active) else 0.0
        same = any(f["key"] == "weakest_carrier" and top["carrier"] in f["claim"] for f in findings)
        findings.append({
            "key": "worst_lane", "kind": "Finding", "leak_eur": pen,
            "claim": (f"{top['carrier']} into {top['destination_country']} is the lane losing most to late delivery: "
                      f"{fmt.pct(top['late_pct'])} late across {fmt.count(top['orders'])} shipments."),
            "support": [
                f"Penalties on the lane are {fmt.money(pen, exact=True)}, {fmt.pct(_share(pen, total_pen))} of all penalties in the period.",
                f"The network late rate is {fmt.pct(book_late)}, so the lane runs {fmt.pct(float(top['late_pct']) - book_late)} points above it.",
                f"Lanes under {metrics.MIN_LANE_SHIPMENTS} shipments are excluded from the ranking.",
            ],
            "action": (
                f"Same carrier as the finding above; make it one commercial conversation and put the lane on the agenda."
                if same else
                f"Re-tender the {top['destination_country']} lane, or price the penalty into what you pay {top['carrier']}."
            ),
            "figure_eur": pen, "figure_label": "Late penalties on the lane",
            "figure_basis": f"{period}, {fmt.count(top['orders'])} shipments",
            "evidence": lanes,
            "columns": [("carrier", "Carrier", "text"), ("destination_country", "Destination", "text"),
                        ("orders", "Shipments", "num"), ("late_pct", "Late (%)", "num"), ("penalties", "Penalties (EUR)", "num")],
            "formats": {"orders": F_INT, "late_pct": F_1DP, "penalties": F_INT},
            "cite": [(0, "late_pct"), (0, "penalties")],
            "method": "Lanes ranked by late penalties, cancelled shipments excluded.",
            "exclusions": f"Lanes under {metrics.MIN_LANE_SHIPMENTS} shipments are not ranked.",
        })

    # Only findings above the reporting threshold are findings. Order by money.
    kept = []
    for f in findings:
        f["share_pct"] = _share(f["leak_eur"], spend)
        if f["share_pct"] >= THRESHOLDS["warning"]:
            f["severity"] = severity(f["share_pct"])
            kept.append(f)
    kept.sort(key=lambda f: f["leak_eur"], reverse=True)
    return kept


def executive_summary(df: pd.DataFrame, findings: list[dict]) -> dict:
    """The hero figure and the three sentences an executive reads first."""
    kpis = metrics.compute_kpis(df)
    spend = float(kpis["total_spend"])
    pen = float(kpis["penalties"])
    period = period_label(df)
    active = df.loc[~df["is_cancelled"]]
    by_carrier = active.groupby("carrier")["late_penalty_eur"].sum().sort_values(ascending=False)
    top = by_carrier.head(3)
    composition = [(str(c), float(v)) for c, v in top.items() if v > 0]
    rest = float(by_carrier.iloc[3:].sum()) if len(by_carrier) > 3 else 0.0
    if rest > 0:
        composition.append(("Other", rest))

    addressed = float(sum(f["leak_eur"] for f in findings))
    counts = {k: sum(1 for f in findings if f["severity"] == k) for k in ("critical", "serious", "warning")}
    parts = []
    for k, word in (("critical", "critical"), ("serious", "serious"), ("warning", "a warning" if counts["warning"] == 1 else "warnings")):
        if counts[k]:
            verb = "is" if counts[k] == 1 else "are"
            parts.append(f"{_n_words(counts[k]).lower()} {verb} {word}")
    sev_sentence = (", ".join(parts[:-1]) + (" and " if len(parts) > 1 else "") + parts[-1]).capitalize() + "." if parts else ""

    if findings:
        s1 = (f"{_n_words(len(findings))} finding{'s' if len(findings) != 1 else ''} account{'s' if len(findings) == 1 else ''} for "
              f"<b>{fmt.money(addressed)}</b> of late-delivery penalties in {period}, {fmt.pct(_share(addressed, spend))} of freight spend. {sev_sentence}")
        s2 = findings[0]["claim"]
    else:
        s1 = f"No leakage above the {fmt.pct(THRESHOLDS['warning'])} reporting threshold was found in {period}."
        s2 = f"Late-delivery penalties total <b>{fmt.money(pen)}</b> across {fmt.count(kpis['late_orders'])} late shipments."
    s3 = (f"On-time delivery is <b>{fmt.pct(kpis['on_time_pct'])}</b> across {fmt.count(kpis['active_orders'])} "
          f"non-cancelled shipments; {fmt.count(kpis['late_orders'])} arrived late by {fmt.days(kpis['avg_delay'])} on average.")

    footer = (f"Recommended actions address <b>{fmt.money(addressed)}</b> of the {fmt.money(pen)} in penalties."
              if findings else f"Penalties total {fmt.money(pen)}; none concentrates enough in one carrier, lane or weekday to act on.")
    return {
        "hero_eur": pen,
        "hero_label": f"{fmt.pct(_share(pen, spend))} of {period} freight spend",
        "hero_basis": (f"{fmt.count(kpis['late_orders'])} late shipments of {fmt.count(kpis['active_orders'])}. "
                       f"Penalties at {fmt.money(PENALTY_PER_DAY_EUR, exact=True)} per day late; cancelled shipments excluded."),
        "composition": composition,
        "sentences": [s1, s2, s3],
        "footer": footer,
        "addressed_eur": addressed,
    }
