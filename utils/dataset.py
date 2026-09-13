"""
Shared I/O for the processed shipment dataset.

Parquet is the intended storage format (fast, typed, small). Two guarantees
sit on top of it:

1. THE FALLBACK IS BIDIRECTIONAL. A gzipped CSV is written alongside the
   parquet every time, and `processed_path()` will only hand back the parquet
   if an engine is actually installed to read it. Previously the writer
   checked for an engine but the reader did not, so a machine with a parquet
   file and no pyarrow crashed on startup with a perfectly readable CSV
   sitting next to it — the exact failure the fallback exists to prevent.

2. A FRESH CLONE BOOTSTRAPS ITSELF. `data/processed/` is gitignored, so a
   clone has raw CSVs and no dataset. `ensure_processed()` builds it on first
   use, which is what makes a zero-friction Streamlit Cloud deploy possible.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "sample_data"
RAW_DIR = SAMPLE_DIR  # kept as an alias; sample_data is the committed input
PROCESSED_DIR = ROOT / "data" / "processed"
PARQUET_PATH = PROCESSED_DIR / "shipments.parquet"
CSV_PATH = PROCESSED_DIR / "shipments.csv.gz"
LOG_PATH = PROCESSED_DIR / "cleaning_log.json"

DATE_COLUMNS = ["ship_date", "delivery_date", "ship_week", "ship_month"]

# Columns whose dtype does not survive a CSV round-trip and must be restored.
NULLABLE_INT_COLUMNS = ["transit_days"]
TEXT_COLUMNS = [
    "order_id", "carrier", "origin_city", "origin_country", "destination_city",
    "destination_country", "service_level", "customer_segment", "currency",
    "status", "lane", "ship_weekday", "source_file",
]
BOOL_COLUMNS = [
    "is_cancelled", "is_late", "is_on_time", "is_billable",
    "cost_is_outlier", "cost_is_imputed", "transit_days_imputed",
    "is_central_europe",
]


def parquet_available() -> bool:
    try:
        import pyarrow  # noqa: F401
        return True
    except ImportError:
        try:
            import fastparquet  # noqa: F401
            return True
        except ImportError:
            return False


def write_processed(df: pd.DataFrame) -> list[Path]:
    """Write the processed dataset. Returns every path written, primary first.

    When parquet is available we write the CSV fallback too. They are produced
    from the same frame in the same call, so the two can never drift apart, and
    the demo survives an environment that cannot read parquet.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if parquet_available():
        df.to_parquet(PARQUET_PATH, index=False)
        written.append(PARQUET_PATH)
    df.to_csv(CSV_PATH, index=False, compression="gzip")
    written.append(CSV_PATH)
    return written


def processed_path() -> Path:
    """The processed dataset this runtime can actually read."""
    if PARQUET_PATH.exists() and parquet_available():
        return PARQUET_PATH
    if CSV_PATH.exists():
        return CSV_PATH
    if PARQUET_PATH.exists():
        raise RuntimeError(
            "Found shipments.parquet but no engine to read it, and no CSV fallback.\n"
            "Either install an engine:  pip install pyarrow\n"
            "or rebuild the dataset:    python pipeline/clean.py"
        )
    raise FileNotFoundError(
        "No processed dataset found. Run:\n"
        "    python pipeline/generate_data.py\n"
        "    python pipeline/clean.py"
    )


def sample_files() -> list[Path]:
    """The committed sample exports, in a stable order."""
    return sorted(SAMPLE_DIR.glob("*.csv"))


def ensure_processed() -> list[str]:
    """Build the dataset if it is missing. Returns a list of steps taken.

    data/processed/ is gitignored, so a fresh clone (or a Streamlit Cloud
    deploy) starts with the committed sample exports and nothing else. Rather
    than greeting a prospective client with a stack trace, build it once on
    first load. Imports are deferred to keep this module free of a circular
    import with pipeline.clean.
    """
    steps: list[str] = []
    try:
        existing: Path | None = processed_path()
    except FileNotFoundError:
        existing = None

    if existing is not None:
        if not _is_stale(existing):
            return steps
        # A processed dataset older than the exports or the pipeline that
        # built it shows yesterday's numbers and looks fine doing it. Rebuild.
        steps.append("rebuilt: processed dataset was older than its inputs")

    if not any(SAMPLE_DIR.glob("*.csv")):
        from pipeline import generate_data
        generate_data.write_exports(generate_data.generate())
        steps.append("generated raw shipment exports")

    from pipeline import clean
    clean.main()
    steps.append("built processed dataset and cleaning log")
    return steps


def _is_stale(processed: Path) -> bool:
    """True when any input export or pipeline module is newer than the dataset."""
    inputs = list(SAMPLE_DIR.glob("*.csv")) + list((ROOT / "pipeline").glob("*.py"))
    if not inputs:
        return False
    newest_input = max(p.stat().st_mtime for p in inputs)
    return processed.stat().st_mtime < newest_input


def dataset_signature() -> str:
    """A cheap cache key that changes whenever the dataset on disk changes.

    Deliberately a stat() call, not a hash of the frame: this is what lets the
    Streamlit cache key on scalars instead of hashing several hundred thousand
    rows on every rerun.
    """
    path = processed_path()
    stat = path.stat()
    return f"{path.name}:{stat.st_mtime_ns}:{stat.st_size}"


def normalize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Pin the dtypes the analytics layer relies on.

    Two reasons this is a named, shared step rather than incidental:

    * Storage parity. Parquet round-trips pandas extension dtypes and gzipped
      CSV does not, so without this the same data read through the two paths
      produces frames that differ by dtype — and a test asserting the two agree
      fails on a difference that means nothing.
    * Nullable booleans are a footgun. A `boolean` column carrying NA
      propagates it through `~` and `&`, so a single missing flag can quietly
      turn a row neither on-time nor late. Flags are hard booleans; only
      transit_days is legitimately nullable, and it is typed as such.
    """
    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in NULLABLE_INT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype("Int64")
    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype("string")
    for col in BOOL_COLUMNS:
        if col in df.columns:
            if df[col].isna().any():
                raise ValueError(
                    f"Flag column `{col}` contains nulls. A flag must be True or "
                    "False — investigate the pipeline rather than coercing it."
                )
            df[col] = df[col].astype(bool)
    return df


def read_processed() -> pd.DataFrame:
    path = processed_path()
    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path, compression="gzip")
    return normalize_dtypes(df)
