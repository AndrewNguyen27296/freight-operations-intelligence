"""
Synthetic logistics shipment generator for Pillar 1.

Produces realistic — and deliberately messy — freight shipment exports that
mimic what a client actually hands over: two CSVs from different systems, with
different header conventions, mixed date formats, missing values, duplicate
order IDs, carrier-name variants and multi-currency freight costs.

A single non-obvious business signal is seeded into the data so the V1 AI
briefing has something real to find:

    Nordfrakt shipments dispatched on FRIDAY to Central Europe (DE/AT/CH/PL/CZ)
    run ~28% longer in transit than the same lane on other weekdays.

Domain is strictly logistics / freight. No energy, meter or carbon data.

Usage:
    python pipeline/generate_data.py [--rows 5000] [--seed 42]
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
# Sample exports live at the repo root and ARE committed: a prospective client
# must be able to run the whole pipeline one click after opening the demo,
# without uploading anything of their own.
RAW_DIR = ROOT / "sample_data"

DEFAULT_ROWS = 5_000
DEFAULT_SEED = 42
START_DATE = date(2025, 3, 1)
END_DATE = date(2026, 8, 31)

# --- Reference data -------------------------------------------------------

# Invented carriers. Naming real freight companies and then publishing
# fabricated performance figures about them, on a public demo, is a claim
# about a real business that happens not to be true. Fictional names cost
# nothing and read just as convincingly to a prospect.
CARRIERS = {
    "Nordfrakt": 0.27,
    "Meridian Express": 0.19,
    "Vantage Freight": 0.18,
    "Baltica Logistics": 0.15,
    "Kestrel Parcel": 0.13,
    "Hanseatic Line": 0.08,
}

# Real exports never spell a carrier the same way twice.
CARRIER_VARIANTS = {
    "Nordfrakt": ["Nordfrakt", "nordfrakt", " Nordfrakt ", "Nordfrakt AB"],
    "Meridian Express": ["Meridian Express", "MERIDIAN EXPRESS", "Meridian Expr", " Meridian Express"],
    "Vantage Freight": ["Vantage Freight", "vantage freight", "Vantage", "Vantage Freight Ltd"],
    "Baltica Logistics": ["Baltica Logistics", "baltica", "Baltica Log.", "Baltica Logistics A/S"],
    "Kestrel Parcel": ["Kestrel Parcel", "KESTREL PARCEL", "Kestrel Parcels AB", "kestrel"],
    "Hanseatic Line": ["Hanseatic Line", "HANSEATIC", "Hanseatic Lines", "hanseatic line"],
}

# Carrier reliability multiplier applied to baseline transit days.
CARRIER_SPEED = {
    "Nordfrakt": 0.95,
    "Meridian Express": 0.92,
    "Vantage Freight": 0.98,
    "Baltica Logistics": 1.08,
    "Kestrel Parcel": 1.15,
    "Hanseatic Line": 1.45,
}

ORIGINS = [
    ("Gothenburg", "SE", 0.34),
    ("Rotterdam", "NL", 0.24),
    ("Hamburg", "DE", 0.19),
    ("Milan", "IT", 0.13),
    ("Barcelona", "ES", 0.10),
]

# destination country -> (cities, baseline transit days, share)
DESTINATIONS = {
    "DE": (["Berlin", "Munich", "Frankfurt", "Cologne"], 3.0, 0.16),
    "AT": (["Vienna", "Graz"], 3.6, 0.06),
    "CH": (["Zurich", "Geneva"], 3.8, 0.06),
    "PL": (["Warsaw", "Krakow", "Gdansk"], 4.0, 0.08),
    "CZ": (["Prague", "Brno"], 3.7, 0.05),
    "SE": (["Stockholm", "Malmo", "Gothenburg"], 2.0, 0.13),
    "NO": (["Oslo", "Bergen"], 3.2, 0.06),
    "DK": (["Copenhagen", "Aarhus"], 2.4, 0.06),
    "FI": (["Helsinki", "Tampere"], 4.2, 0.05),
    "NL": (["Amsterdam", "Eindhoven"], 2.6, 0.07),
    "FR": (["Paris", "Lyon", "Marseille"], 3.4, 0.08),
    "ES": (["Madrid", "Valencia"], 4.4, 0.05),
    "IT": (["Rome", "Turin"], 4.1, 0.05),
    "GB": (["London", "Manchester"], 3.9, 0.04),
}

CENTRAL_EUROPE = {"DE", "AT", "CH", "PL", "CZ"}

# service level -> (transit multiplier, cost multiplier, promised days, share)
SERVICE_LEVELS = {
    "Express": (0.62, 1.85, 2, 0.22),
    "Standard": (1.00, 1.00, 4, 0.53),
    "Economy": (1.42, 0.68, 7, 0.25),
}

CUSTOMER_SEGMENTS = ["E-Commerce", "Retail", "Industrial", "Wholesale"]

# Currency the source system recorded the cost in, and the rate back to EUR.
CURRENCIES = {"EUR": 1.0, "USD": 0.92, "SEK": 0.087}
CURRENCY_SHARE = [0.72, 0.17, 0.11]

# The seeded insight: how much longer Friday Nordfrakt dispatches to Central Europe run.
FRIDAY_CENTRAL_EU_PENALTY = 1.32


def _weighted_choice(rng: np.random.Generator, options: list, weights: list, size: int):
    w = np.asarray(weights, dtype=float)
    w = w / w.sum()
    idx = rng.choice(len(options), size=size, p=w)
    return [options[i] for i in idx]


def _format_date(d: date, style: int) -> str:
    """Four different date conventions, because four different systems wrote them."""
    if style == 0:
        return d.isoformat()                       # 2025-03-14
    if style == 1:
        return d.strftime("%d/%m/%Y")              # 14/03/2025
    if style == 2:
        return d.strftime("%b %d, %Y")             # Mar 14, 2025
    return d.strftime("%Y-%m-%d 00:00:00")         # 2025-03-14 00:00:00


def generate(rows: int = DEFAULT_ROWS, seed: int = DEFAULT_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    span_days = (END_DATE - START_DATE).days

    # --- dispatch dates: weekday-heavy, as a real dispatch calendar is ---
    raw_offsets = rng.integers(0, span_days + 1, size=rows)
    dispatch_dates = [START_DATE + timedelta(days=int(o)) for o in raw_offsets]
    # Push ~70% of weekend dispatches onto the following Monday.
    for i, d in enumerate(dispatch_dates):
        if d.weekday() >= 5 and rng.random() < 0.70:
            dispatch_dates[i] = d + timedelta(days=(7 - d.weekday()))

    carriers = _weighted_choice(rng, list(CARRIERS), list(CARRIERS.values()), rows)

    origin_opts = [(c, cc) for c, cc, _ in ORIGINS]
    origin_w = [w for _, _, w in ORIGINS]
    origins = _weighted_choice(rng, origin_opts, origin_w, rows)

    dest_codes = _weighted_choice(
        rng, list(DESTINATIONS), [v[2] for v in DESTINATIONS.values()], rows
    )
    services = _weighted_choice(
        rng, list(SERVICE_LEVELS), [v[3] for v in SERVICE_LEVELS.values()], rows
    )

    records = []
    for i in range(rows):
        carrier = carriers[i]
        dest_cc = dest_codes[i]
        dest_cities, base_days, _ = DESTINATIONS[dest_cc]
        svc = services[i]
        transit_mult, cost_mult, promised, _ = SERVICE_LEVELS[svc]
        dispatch = dispatch_dates[i]

        # --- transit days -------------------------------------------------
        transit = base_days * transit_mult * CARRIER_SPEED[carrier]
        transit *= rng.normal(1.0, 0.16)

        # The seeded signal.
        is_friday = dispatch.weekday() == 4
        if carrier == "Nordfrakt" and is_friday and dest_cc in CENTRAL_EUROPE:
            transit *= FRIDAY_CENTRAL_EU_PENALTY

        # Mild seasonal peak in Nov/Dec.
        if dispatch.month in (11, 12):
            transit *= 1.09

        transit_days = max(1, int(round(transit)))

        # --- freight cost -------------------------------------------------
        weight_kg = float(np.round(rng.gamma(shape=2.1, scale=13.0) + 0.6, 2))
        cost_eur = (18.0 + base_days * 6.4 + weight_kg * 1.35) * cost_mult
        cost_eur *= rng.normal(1.0, 0.13)
        if dispatch.month in (11, 12):
            cost_eur *= 1.07
        cost_eur = max(9.0, cost_eur)

        currency = _weighted_choice(rng, list(CURRENCIES), CURRENCY_SHARE, 1)[0]
        cost_native = round(cost_eur / CURRENCIES[currency], 2)

        # --- status -------------------------------------------------------
        if transit_days > promised:
            status = "Delayed"
        elif rng.random() < 0.02:
            status = "In Transit"
        else:
            status = "Delivered"
        if rng.random() < 0.014:
            status = "Cancelled"

        records.append(
            {
                "order_id": f"ORD-{100000 + i}",
                "ship_date": dispatch,
                "carrier": carrier,
                "origin_city": origins[i][0],
                "origin_country": origins[i][1],
                "destination_city": dest_cities[int(rng.integers(0, len(dest_cities)))],
                "destination_country": dest_cc,
                "service_level": svc,
                "customer_segment": CUSTOMER_SEGMENTS[int(rng.integers(0, len(CUSTOMER_SEGMENTS)))],
                "weight_kg": weight_kg,
                "freight_cost": cost_native,
                "currency": currency,
                "transit_days": transit_days,
                "promised_days": promised,
                "status": status,
            }
        )

    df = pd.DataFrame.from_records(records)
    return _add_realistic_mess(df, rng)


def _add_realistic_mess(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Inject the defects a real client export always has."""
    n = len(df)

    # Carrier spelling variants.
    df["carrier"] = [
        CARRIER_VARIANTS[c][int(rng.integers(0, len(CARRIER_VARIANTS[c])))]
        for c in df["carrier"]
    ]

    # Mixed date formats, and ~1.2% missing ship dates.
    styles = rng.integers(0, 4, size=n)
    df["ship_date"] = [_format_date(d, int(s)) for d, s in zip(df["ship_date"], styles)]
    df.loc[rng.random(n) < 0.012, "ship_date"] = None

    # Cancelled shipments never got a transit time.
    df.loc[df["status"] == "Cancelled", "transit_days"] = np.nan
    # Plus ~1.8% simply never recorded one.
    df.loc[rng.random(n) < 0.018, "transit_days"] = np.nan

    # ~1.5% missing freight cost.
    df.loc[rng.random(n) < 0.015, "freight_cost"] = np.nan

    # ~0.5% fat-finger cost outliers (extra zero keyed in).
    outlier_mask = rng.random(n) < 0.005
    df.loc[outlier_mask, "freight_cost"] = df.loc[outlier_mask, "freight_cost"] * 10

    # A handful of impossible negative transit days.
    neg_idx = rng.choice(n, size=6, replace=False)
    df.loc[neg_idx, "transit_days"] = -df.loc[neg_idx, "transit_days"].abs()

    # Whitespace and casing noise in free-text columns.
    pad = rng.random(n) < 0.06
    df.loc[pad, "destination_city"] = " " + df.loc[pad, "destination_city"] + " "
    upper = rng.random(n) < 0.04
    df.loc[upper, "status"] = df.loc[upper, "status"].str.upper()

    # ~0.4% duplicated rows re-exported by the source system.
    dup_idx = rng.choice(n, size=max(1, int(n * 0.004)), replace=False)
    df = pd.concat([df, df.iloc[dup_idx]], ignore_index=True)

    return df.sample(frac=1.0, random_state=7).reset_index(drop=True)


# A third system, run by a parcel broker, that shares no vocabulary with the
# other two: different words for the same fields, and semicolon-separated
# because it was exported from a European spreadsheet locale. This is the file
# that proves schema normalisation rather than merely asserting it.
BROKER_HEADERS = {
    "order_id": "CONSIGNMENT_NO",
    "ship_date": "DESPATCH_DATE",
    "carrier": "HAULIER",
    "origin_city": "COLLECT_CITY",
    "origin_country": "COLLECT_CC",
    "destination_city": "DELIVER_CITY",
    "destination_country": "DELIVER_CC",
    "service_level": "SERVICE",
    "customer_segment": "ACCOUNT_TYPE",
    "weight_kg": "GROSS_WEIGHT_KG",
    "freight_cost": "NET_CHARGE",
    "currency": "CCY",
    "transit_days": "DAYS_IN_TRANSIT",
    "promised_days": "SLA_DAYS",
    "status": "CONSIGNMENT_STATUS",
}


def write_exports(df: pd.DataFrame) -> list[Path]:
    """Split into three exports with different header conventions.

    Three systems, three vocabularies, one analysis-ready table — which is the
    thing being sold. The split is by date so the row count still reconciles.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    parsed_year = pd.to_datetime(df["ship_date"], format="mixed", dayfirst=True, errors="coerce")
    is_2026 = parsed_year.dt.year.eq(2026).fillna(False)

    legacy = df.loc[~is_2026].copy()          # older WMS export, snake_case
    modern_all = df.loc[is_2026].copy()       # newer TMS export, Title Case
    # Carve the last third of 2026 off to the broker's system.
    broker_cut = int(len(modern_all) * 0.66)
    modern = modern_all.iloc[:broker_cut].copy()
    broker = modern_all.iloc[broker_cut:].copy()

    modern = modern.rename(
        columns={
            "order_id": "Order ID",
            "ship_date": "Ship Date",
            "carrier": "Carrier",
            "origin_city": "Origin City",
            "origin_country": "Origin Country",
            "destination_city": "Destination City",
            "destination_country": "Destination Country",
            "service_level": "Service Level",
            "customer_segment": "Customer Segment",
            "weight_kg": "Weight (kg)",
            "freight_cost": "Freight Cost",
            "currency": "Currency",
            "transit_days": "Transit Days",
            "promised_days": "Promised Days",
            "status": "Status",
        }
    )
    modern = modern[
        [
            "Order ID", "Carrier", "Ship Date", "Service Level", "Status",
            "Origin City", "Origin Country", "Destination City", "Destination Country",
            "Customer Segment", "Weight (kg)", "Freight Cost", "Currency",
            "Transit Days", "Promised Days",
        ]
    ]

    broker = broker.rename(columns=BROKER_HEADERS)[list(BROKER_HEADERS.values())]

    paths = [
        RAW_DIR / "wms_export_2025.csv",
        RAW_DIR / "tms_export_2026.csv",
        RAW_DIR / "parcel_broker_export_2026.csv",
    ]
    legacy.to_csv(paths[0], index=False)
    modern.to_csv(paths[1], index=False)
    # Semicolon-separated, as a European spreadsheet locale exports it. The
    # reader sniffs the delimiter, so this is one more thing nobody has to
    # hand-fix before the dashboard works.
    broker.to_csv(paths[2], index=False, sep=";")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic logistics shipment data.")
    parser.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    df = generate(rows=args.rows, seed=args.seed)
    paths = write_exports(df)

    print(f"Generated {len(df):,} rows ({args.rows:,} base + duplicates).")
    for p in paths:
        rows = sum(1 for _ in p.open(encoding="utf-8")) - 1
        print(f"  {p.relative_to(ROOT)}  ->  {rows:,} rows")


if __name__ == "__main__":
    main()
