"""
Deterministic cleaning + normalisation pipeline for Pillar 1.

Reads every CSV in data/raw/ (regardless of header convention), normalises the
schema, and writes a single analysis-ready parquet plus a cleaning log.

ARCHITECTURAL INVARIANT — NO SILENT ROW DROPS.
Every transformation records what it touched in data/processed/cleaning_log.json.
Row counts reconcile: rows_in = rows_out + rows_removed, and every removal has
a named reason. Running this twice on the same input produces byte-identical
output.

Usage:
    python pipeline/clean.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.dataset import (  # noqa: E402
    LOG_PATH,
    PROCESSED_DIR,
    normalize_dtypes,
    write_processed,
)

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "sample_data"

# --- Business assumptions (documented, not hidden in code) ----------------
LATE_PENALTY_EUR_PER_DAY = 45.0   # contractual SLA penalty per day late, per shipment
FX_TO_EUR = {"EUR": 1.0, "USD": 0.92, "SEK": 0.087}
OUTLIER_IQR_MULTIPLIER = 3.0      # cost outlier threshold within a service level

CENTRAL_EUROPE = {"DE", "AT", "CH", "PL", "CZ"}

CANONICAL_CARRIERS = {
    "nordfrakt": "Nordfrakt", "nordfraktab": "Nordfrakt",
    "meridianexpress": "Meridian Express", "meridianexpr": "Meridian Express",
    "vantagefreight": "Vantage Freight", "vantage": "Vantage Freight",
    "vantagefreightltd": "Vantage Freight",
    "balticalogistics": "Baltica Logistics", "baltica": "Baltica Logistics",
    "balticalog": "Baltica Logistics", "balticalogisticsas": "Baltica Logistics",
    "kestrelparcel": "Kestrel Parcel", "kestrelparcels": "Kestrel Parcel",
    "kestrelparcelsab": "Kestrel Parcel", "kestrel": "Kestrel Parcel",
    "hanseaticline": "Hanseatic Line", "hanseatic": "Hanseatic Line",
    "hanseaticlines": "Hanseatic Line",
}

# Every source system invents its own vocabulary. Rather than demanding the
# client rename their columns before the dashboard will look at them, map the
# names they actually use onto the canonical schema. Keys are the snake_cased
# form of whatever the header said; unknown columns are kept and reported, not
# silently dropped.
COLUMN_ALIASES = {
    # identity
    "consignment_no": "order_id", "consignment": "order_id", "order_ref": "order_id",
    "shipment_id": "order_id", "awb": "order_id", "tracking_no": "order_id",
    # dates
    "despatch_date": "ship_date", "dispatch_date": "ship_date", "shipped": "ship_date",
    "shipped_on": "ship_date", "date_shipped": "ship_date", "collection_date": "ship_date",
    # carrier
    "haulier": "carrier", "carrier_name": "carrier", "service_provider": "carrier",
    # origin / destination
    "collect_city": "origin_city", "collection_city": "origin_city",
    "collect_cc": "origin_country", "collect_country": "origin_country",
    "deliver_city": "destination_city", "delivery_city": "destination_city",
    "deliver_cc": "destination_country", "delivery_country": "destination_country",
    "dest_country": "destination_country",
    # commercial
    "service": "service_level", "service_type": "service_level",
    "account_type": "customer_segment", "segment": "customer_segment",
    "gross_weight_kg": "weight_kg", "weight": "weight_kg", "gross_weight": "weight_kg",
    "net_charge": "freight_cost", "charge": "freight_cost", "cost": "freight_cost",
    "freight_charge": "freight_cost",
    "ccy": "currency", "currency_code": "currency",
    # service performance
    "days_in_transit": "transit_days", "transit": "transit_days",
    "sla_days": "promised_days", "promised_transit_days": "promised_days",
    "consignment_status": "status", "shipment_status": "status",
}

REQUIRED_COLUMNS = [
    "order_id", "ship_date", "carrier", "origin_city", "origin_country",
    "destination_city", "destination_country", "service_level",
    "customer_segment", "weight_kg", "freight_cost", "currency",
    "transit_days", "promised_days", "status",
]


class CleaningLog:
    """Append-only record of every transformation, for client-facing auditability."""

    def __init__(self) -> None:
        self.entries: list[dict] = []
        self.rows_in = 0
        self.rows_removed = 0

    def record(self, step: str, action: str, rows_affected: int, detail: str = "") -> None:
        self.entries.append(
            {
                "step": step,
                "action": action,
                "rows_affected": int(rows_affected),
                "detail": detail,
            }
        )

    def remove(self, step: str, reason: str, rows_affected: int, detail: str = "") -> None:
        self.rows_removed += int(rows_affected)
        self.record(step, f"REMOVED — {reason}", rows_affected, detail)

    def to_dict(self, rows_out: int, sources: list[str]) -> dict:
        return {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sources": sources,
            "rows_in": self.rows_in,
            "rows_removed": self.rows_removed,
            "rows_out": rows_out,
            "reconciles": self.rows_in - self.rows_removed == rows_out,
            "assumptions": {
                "late_penalty_eur_per_day": LATE_PENALTY_EUR_PER_DAY,
                "fx_to_eur": FX_TO_EUR,
                "outlier_iqr_multiplier": OUTLIER_IQR_MULTIPLIER,
            },
            "steps": self.entries,
        }


def _snake(name: str) -> str:
    name = name.strip().lower()
    name = name.replace("(kg)", "kg").replace("(", " ").replace(")", " ")
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def read_source(handle, name: str, log: CleaningLog) -> pd.DataFrame:
    """Read one export, whatever delimiter and column vocabulary it uses.

    `handle` is anything pandas can read — a path, or the file object Streamlit
    hands over from an upload — so the same code path serves the bundled
    samples and a client's own file dropped into the browser.
    """
    # Sniff the separator: European exports are frequently semicolon-separated,
    # and a client should not have to know that to use the dashboard.
    raw = pd.read_csv(handle, dtype=str, sep=None, engine="python")
    original = list(raw.columns)
    raw.columns = [_snake(c) for c in raw.columns]
    renamed = {c: COLUMN_ALIASES[c] for c in raw.columns if c in COLUMN_ALIASES}
    if renamed:
        raw = raw.rename(columns=renamed)
        log.record(
            "map_schema", "mapped source column names onto the canonical schema",
            len(raw), f"{name}: " + ", ".join(f"{k} -> {v}" for k, v in sorted(renamed.items())),
        )
    raw["source_file"] = name
    log.record("ingest", "read source file", len(raw),
               f"{name} ({len(original)} columns)")
    return raw


def ingest(log: CleaningLog, sources: list | None = None) -> tuple[pd.DataFrame, list[str]]:
    """Read every source and align them onto one schema.

    `sources` is an optional list of (name, handle) pairs — used for uploaded
    files. When omitted, every CSV in sample_data/ is read.
    """
    if sources is None:
        files = sorted(RAW_DIR.glob("*.csv"))
        if not files:
            raise FileNotFoundError(
                f"No CSVs found in {RAW_DIR}. Run `python pipeline/generate_data.py` first."
            )
        sources = [(p.name, p) for p in files]

    frames = [read_source(handle, name, log) for name, handle in sources]
    df = pd.concat(frames, ignore_index=True)
    log.rows_in = len(df)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "These required fields could not be found in the uploaded files: "
            + ", ".join(missing)
            + ".\nColumns seen: " + ", ".join(sorted(c for c in df.columns if c != "source_file"))
            + ".\nAdd the mapping to COLUMN_ALIASES in pipeline/clean.py."
        )
    return df, [name for name, _ in sources]


def clean(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    # --- 1. Text normalisation --------------------------------------------
    text_cols = [
        "order_id", "carrier", "origin_city", "origin_country", "destination_city",
        "destination_country", "service_level", "customer_segment", "currency", "status",
    ]
    padded = int(sum(df[c].fillna("").str.len().ne(df[c].fillna("").str.strip().str.len()).sum() for c in text_cols))
    for col in text_cols:
        df[col] = df[col].astype("string").str.strip()
    log.record("normalise_text", "trimmed leading/trailing whitespace", padded, f"across {len(text_cols)} text columns")

    for col in ("origin_country", "destination_country", "currency"):
        df[col] = df[col].str.upper()
    df["status"] = df["status"].str.title()
    df["service_level"] = df["service_level"].str.title()

    # --- 2. Carrier canonicalisation --------------------------------------
    key = df["carrier"].fillna("").str.lower().str.replace(r"[^a-z]", "", regex=True)
    canonical = key.map(CANONICAL_CARRIERS)
    unmapped = int(canonical.isna().sum())
    if unmapped:
        log.record("canonicalise_carrier", "FLAGGED unrecognised carrier name (kept as-is)",
                   unmapped, sorted(df.loc[canonical.isna(), "carrier"].dropna().unique().tolist())[:10])
    changed = int((canonical.notna() & canonical.ne(df["carrier"])).sum())
    df["carrier"] = canonical.fillna(df["carrier"])
    log.record("canonicalise_carrier", "mapped spelling variants to canonical name", changed,
               f"{df['carrier'].nunique()} distinct carriers after mapping")

    # --- 3. Dates ---------------------------------------------------------
    parsed = pd.to_datetime(df["ship_date"], format="mixed", dayfirst=True, errors="coerce")
    unparseable = int(parsed.isna().sum())
    df["ship_date"] = parsed.dt.normalize()
    log.record("parse_dates", "parsed mixed date formats to datetime", int(parsed.notna().sum()),
               "handled ISO, DD/MM/YYYY, 'Mon DD, YYYY' and timestamped variants")

    # A shipment with no date cannot sit on a time axis — removed, and counted.
    if unparseable:
        df = df.loc[parsed.notna()].copy()
        log.remove("parse_dates", "ship_date missing or unparseable", unparseable,
                   "cannot be placed on the time axis; excluded from all date-filtered views")

    # --- 4. Duplicates ----------------------------------------------------
    dup_mask = df.duplicated(subset=["order_id"], keep="first")
    n_dupes = int(dup_mask.sum())
    if n_dupes:
        df = df.loc[~dup_mask].copy()
        log.remove("deduplicate", "duplicate order_id re-exported by source system", n_dupes,
                   "kept the first occurrence of each order_id")

    # --- 5. Numeric coercion ----------------------------------------------
    for col in ("weight_kg", "freight_cost", "transit_days", "promised_days"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Impossible negative transit — void the value, keep the row.
    neg = int((df["transit_days"] < 0).sum())
    if neg:
        df.loc[df["transit_days"] < 0, "transit_days"] = np.nan
        log.record("validate_transit", "voided negative transit_days (data-entry error)", neg,
                   "row retained; value imputed from lane median below")

    # --- 6. Currency normalisation ----------------------------------------
    unknown_ccy = int((~df["currency"].isin(FX_TO_EUR)).sum())
    if unknown_ccy:
        log.record("convert_currency", "FLAGGED unknown currency (cost left null)", unknown_ccy,
                   sorted(df.loc[~df["currency"].isin(FX_TO_EUR), "currency"].dropna().unique().tolist()))
    rate = df["currency"].map(FX_TO_EUR)
    df["freight_cost_eur"] = (df["freight_cost"] * rate).round(2)
    converted = int((df["currency"].ne("EUR") & df["freight_cost_eur"].notna()).sum())
    log.record("convert_currency", "converted non-EUR costs at fixed reference rates", converted,
               f"rates: {FX_TO_EUR}")

    # --- 7. Cost outliers --------------------------------------------------
    df["cost_is_outlier"] = False
    for svc, grp in df.groupby("service_level", dropna=True):
        vals = grp["freight_cost_eur"].dropna()
        if len(vals) < 20:
            continue
        q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
        upper = q3 + OUTLIER_IQR_MULTIPLIER * (q3 - q1)
        mask = grp["freight_cost_eur"] > upper
        df.loc[mask[mask].index, "cost_is_outlier"] = True
    n_outliers = int(df["cost_is_outlier"].sum())
    log.record("flag_outliers", "FLAGGED freight cost outliers (rows retained, excluded from spend KPIs)",
               n_outliers, f"IQR rule per service level, multiplier {OUTLIER_IQR_MULTIPLIER}")

    # --- 8. Imputation (flagged, never silent) -----------------------------
    df["lane"] = df["origin_country"] + " → " + df["destination_country"]

    # A cancelled shipment has no transit time because it never moved. That is
    # NOT a missing value to be imputed — imputing it would invent a delivery
    # date for a shipment that does not exist, and bury not-applicable rows
    # inside an "imputed" count. Leave them null and say so in the log.
    cancelled_mask = df["status"].eq("Cancelled")
    missing_transit = df["transit_days"].isna()

    df["transit_days_imputed"] = missing_transit & ~cancelled_mask
    lane_median = df.groupby(["lane", "service_level"])["transit_days"].transform("median")
    global_median = df["transit_days"].median()
    filled = df["transit_days"].fillna(lane_median).fillna(global_median)
    df["transit_days"] = filled.where(~cancelled_mask, other=pd.NA)

    log.record("impute", "imputed missing transit_days from lane × service-level median",
               int(df["transit_days_imputed"].sum()), "flagged in column `transit_days_imputed`")
    log.record("impute", "left transit_days NULL for cancelled shipments (not applicable)",
               int((missing_transit & cancelled_mask).sum()),
               "never dispatched, so no transit time exists to impute; delivery_date left null too")

    df["cost_is_imputed"] = df["freight_cost_eur"].isna()
    cost_median = df.groupby(["carrier", "service_level"])["freight_cost_eur"].transform("median")
    df["freight_cost_eur"] = df["freight_cost_eur"].fillna(cost_median).fillna(
        df["freight_cost_eur"].median()
    ).round(2)
    log.record("impute", "imputed missing freight cost from carrier × service-level median",
               int(df["cost_is_imputed"].sum()), "flagged in column `cost_is_imputed`")

    # --- 9. Derived business metrics ---------------------------------------
    # Nullable Int64, because transit_days is genuinely absent for cancelled rows.
    df["transit_days"] = df["transit_days"].round().astype("Int64")
    df["promised_days"] = df["promised_days"].fillna(df["promised_days"].median()).astype("int64")

    df["is_cancelled"] = df["status"].eq("Cancelled")
    delay = (df["transit_days"] - df["promised_days"]).clip(lower=0)
    df["delay_days"] = delay.where(~df["is_cancelled"], other=0).fillna(0).astype("int64")
    df["is_late"] = df["delay_days"].gt(0) & ~df["is_cancelled"]
    df["is_on_time"] = ~df["is_late"] & ~df["is_cancelled"]
    df["late_penalty_eur"] = (df["delay_days"] * LATE_PENALTY_EUR_PER_DAY).round(2)

    # Null for cancelled shipments, by construction — never a fabricated date.
    df["delivery_date"] = df["ship_date"] + pd.to_timedelta(
        df["transit_days"].astype("Float64"), unit="D"
    )
    df["ship_weekday"] = df["ship_date"].dt.day_name()
    df["ship_week"] = df["ship_date"].dt.to_period("W").dt.start_time
    df["ship_month"] = df["ship_date"].dt.to_period("M").dt.start_time
    df["is_central_europe"] = df["destination_country"].isin(CENTRAL_EUROPE)
    df["cost_per_kg"] = (df["freight_cost_eur"] / df["weight_kg"].replace(0, np.nan)).round(2)

    # Rows that count toward spend KPIs: not cancelled, not a cost outlier.
    df["is_billable"] = ~df["is_cancelled"] & ~df["cost_is_outlier"]
    log.record("derive_metrics", "computed delay, on-time, penalty and calendar dimensions", len(df),
               f"late penalty assumption: €{LATE_PENALTY_EUR_PER_DAY:.0f} per shipment per day late")

    df = df.sort_values(["ship_date", "order_id"]).reset_index(drop=True)
    return normalize_dtypes(df)


def build(sources: list | None = None) -> tuple[pd.DataFrame, dict]:
    """Run the whole pipeline and return (dataframe, cleaning log) in memory.

    Nothing is written to disk. This is what the app calls for uploaded files:
    Streamlit Cloud's filesystem is ephemeral and a client's data has no
    business being persisted on a demo server.
    """
    log = CleaningLog()
    raw, names = ingest(log, sources)
    df = clean(raw, log)
    return df, log.to_dict(rows_out=len(df), sources=names)


def main() -> None:
    log = CleaningLog()
    raw, sources = ingest(log)
    df = clean(raw, log)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    written = write_processed(df)

    payload = log.to_dict(rows_out=len(df), sources=sources)
    LOG_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Rows in:      {payload['rows_in']:,}")
    print(f"Rows removed: {payload['rows_removed']:,}")
    print(f"Rows out:     {payload['rows_out']:,}")
    print(f"Reconciles:   {payload['reconciles']}")
    print()
    for path in written:
        print(f"Wrote {path.relative_to(ROOT)}")
    print(f"Wrote {LOG_PATH.relative_to(ROOT)}  ({len(payload['steps'])} logged steps)")


if __name__ == "__main__":
    main()
