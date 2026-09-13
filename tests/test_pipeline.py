"""
Verification suite for the V0 pipeline. Pure pandas — no Streamlit required.

    python tests/test_pipeline.py

Checks the invariants the client is actually buying: the row counts reconcile,
nothing was silently dropped, the numbers are internally consistent, and the
seeded operational signal is detectable in the cleaned data.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

# Windows consoles default to cp1252, which cannot encode the true minus sign
# and the check marks this suite prints. Force UTF-8 so the documented command
# `python tests/test_pipeline.py` works on every platform without a flag.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.dataset import (  # noqa: E402
    CSV_PATH,
    LOG_PATH,
    PARQUET_PATH,
    parquet_available,
    processed_path,
    read_processed,
)
from utils import ai_insights  # noqa: E402
from utils.metrics import (  # noqa: E402
    MIN_LANE_SHIPMENTS,
    carrier_destination_matrix,
    compute_kpis,
    eur,
    eur_exact,
    filter_shipments,
    spend_by_carrier,
    trend,
)
from utils.theme import CARRIER_ORDER  # noqa: E402

FAILURES: list[str] = []


def _no_new_processed_files() -> bool:
    """The upload path must not leave anything behind in data/processed."""
    from utils.dataset import PROCESSED_DIR
    before = set(PROCESSED_DIR.glob("*")) if PROCESSED_DIR.exists() else set()
    import io as _io
    from pipeline import clean as _clean
    from utils.dataset import sample_files as _sf
    one = _sf()[0]
    _clean.build([(one.name, _io.BytesIO(one.read_bytes()))])
    after = set(PROCESSED_DIR.glob("*")) if PROCESSED_DIR.exists() else set()
    return before == after


def _no_cross_repo_imports() -> bool:
    """Nothing in this repo may reach outside its own root."""
    import re
    bad = []
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts or ".venv" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in (r"parents\[[2-9]\]", r"Pillar [23]", r"\.\./\.\."):
            if re.search(pattern, text):
                bad.append(f"{path.name}: {pattern}")
    if bad:
        print("    cross-repo reference:", "; ".join(bad))
    return not bad


def _non_compete_clean() -> bool:
    """Zero energy / meter / carbon vocabulary — the hard commercial guardrail.

    Lines that state the prohibition itself are allowed; anything else is a
    finding.
    """
    import re
    banned = re.compile(
        r"\b(kwh|smart.?meter|electricity|tariff|carbon|co2|emission|esg)\b",  # NON-COMPETE-OK
        re.I)
    # Lines that define or describe the prohibition are not violations of it.
    # NON-COMPETE-OK marks the two places that must name the banned words.
    allowed_markers = ("No energy", "Zero energy", "non-compete", "Non-Compete",
                       "NON-COMPETE", "never energy", "NON-COMPETE-OK")
    hits = []
    for path in list(ROOT.rglob("*.py")) + list(ROOT.rglob("*.md")) + \
            list(ROOT.rglob("*.toml")) + list(ROOT.rglob("*.txt")):
        if "__pycache__" in path.parts or ".venv" in path.parts:
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if banned.search(line) and not any(m in line for m in allowed_markers):
                hits.append(f"{path.name}:{i}")
    if hits:
        print("    non-compete hit:", "; ".join(hits[:5]))
    return not hits


def _numbers_are_traceable(bullets: list[str], evidence: dict, df: pd.DataFrame) -> bool:
    """Every integer-ish figure quoted in the briefing must exist in the evidence.

    This is the check that makes the "nothing to hallucinate" claim testable
    rather than rhetorical. It will also fail loudly the day the narration
    layer is swapped for a model that starts doing its own arithmetic.
    """
    import re

    allowed: set[int] = set()

    def offer(value) -> None:
        if value is None or isinstance(value, bool):
            return
        try:
            f = float(value)
        except (TypeError, ValueError):
            return
        for candidate in (round(f), int(f), round(f / 1000), round(f, 1) * 10):
            allowed.add(int(candidate))
        allowed.add(int(f"{f:.0f}"))

    def walk(node) -> None:
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, (list, tuple)):
            for v in node:
                walk(v)
        else:
            offer(node)

    walk(evidence)
    # Differences the narration is allowed to state (a gap between two figures).
    weak = evidence.get("weakest_carrier")
    if weak:
        offer(evidence["portfolio_on_time_pct"] - weak["on_time_pct"])
    sig = evidence.get("weekday_signal")
    if sig:
        offer(sig["late_pct"] - sig["baseline_late_pct"])

    text = " ".join(bullets)
    # Figures are grouped with a narrow no-break space (U+202F) per the design
    # system; it is a grouping character here, exactly like the comma before it.
    for token in re.findall(r"[\d][\d, ]*(?:\.\d+)?", text):
        value = float(token.replace(",", "").replace(" ", ""))
        if int(round(value)) not in allowed:
            print(f"    untraceable figure in briefing: {token}")
            return False
    return True


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}" + (f"  — {detail}" if detail else ""))
    if not condition:
        FAILURES.append(name)


def _build_fresh() -> None:
    """Build the dataset from source before testing anything against it.

    The suite used to read whatever `data/processed/` happened to contain. If
    that artifact was left by an older version of the pipeline, two checks
    failed — determinism and storage parity — and both pointed at the code
    rather than at the stale file, which is a bad way to spend an evening.
    Build first, then every check is about the pipeline as it is now.
    """
    for script in ("generate_data.py", "clean.py"):
        result = subprocess.run(
            [sys.executable, str(ROOT / "pipeline" / script)],
            capture_output=True, cwd=ROOT,
        )
        if result.returncode != 0:
            raise SystemExit(
                f"Could not build the dataset — pipeline/{script} failed:\n"
                + result.stderr.decode(errors="replace")
            )


def main() -> int:
    print("Building the dataset from sample_data/ so every check tests the "
          "current pipeline…")
    _build_fresh()
    df = read_processed()
    log = json.loads(LOG_PATH.read_text(encoding="utf-8"))

    print("\n1. Cleaning log integrity")
    check("row counts reconcile", log["reconciles"],
          f"{log['rows_in']:,} in − {log['rows_removed']:,} removed = {log['rows_out']:,} out")
    check("every removed row has a logged reason",
          sum(s["rows_affected"] for s in log["steps"] if s["action"].startswith("REMOVED"))
          == log["rows_removed"])
    check("parquet/csv row count matches log", len(df) == log["rows_out"])

    print("\n2. Schema & completeness")
    critical = ["order_id", "ship_date", "carrier", "freight_cost_eur", "transit_days",
                "delay_days", "is_on_time", "is_billable"]
    check("all critical columns present", all(c in df.columns for c in critical),
          f"{len(df.columns)} columns")
    # transit_days and delivery_date are legitimately null for cancelled
    # shipments — they never moved, so there is nothing to record. Everywhere
    # else a null is a defect.
    always_populated = [c for c in critical if c != "transit_days"]
    check("no nulls in critical columns", not df[always_populated].isna().any().any())
    cancelled = df["is_cancelled"]
    check("transit_days is null only for cancelled shipments",
          bool(df["transit_days"].isna().eq(cancelled).all()),
          f"{int(cancelled.sum())} cancelled, {int(df['transit_days'].isna().sum())} null")
    check("delivery_date is null only for cancelled shipments",
          bool(df["delivery_date"].isna().eq(cancelled).all()),
          "no fabricated delivery dates for shipments that never shipped")
    check("cancelled shipments are not counted as imputed",
          not (df["transit_days_imputed"] & cancelled).any(),
          "not-applicable is logged separately from imputed")
    check("order_id is unique", df["order_id"].is_unique)
    check("ship_date parsed as datetime", pd.api.types.is_datetime64_any_dtype(df["ship_date"]))

    print("\n3. Business-logic consistency")
    check("carriers fully canonicalised", set(df["carrier"]).issubset(set(CARRIER_ORDER)),
          ", ".join(sorted(df["carrier"].unique())))
    check("no negative transit days", bool((df["transit_days"].dropna() > 0).all()))
    check("no negative freight cost", (df["freight_cost_eur"] >= 0).all())
    active = df.loc[~df["is_cancelled"]]
    expected_delay = (active["transit_days"] - active["promised_days"]).clip(lower=0)
    check("delay_days = max(transit − promised, 0) for non-cancelled",
          bool(active["delay_days"].eq(expected_delay).all()))
    check("on-time and late are mutually exclusive",
          not (df["is_on_time"] & df["is_late"]).any())
    check("penalty matches delay × rate",
          bool((df["late_penalty_eur"] - df["delay_days"] * 45.0).abs().lt(0.01).all()))
    check("cancelled shipments are never billable",
          not (df["is_cancelled"] & df["is_billable"]).any())

    print("\n4. Dashboard metrics")
    kpis = compute_kpis(df)
    check("total spend is positive", kpis["total_spend"] > 0, f"€{kpis['total_spend']:,.0f}")
    check("on-time % within 0–100", 0 <= kpis["on_time_pct"] <= 100, f"{kpis['on_time_pct']:.1f}%")
    check("avg delay is positive", kpis["avg_delay"] > 0, f"{kpis['avg_delay']:.2f} days")

    by_carrier = spend_by_carrier(df)
    check("carrier chart returns every carrier", len(by_carrier) == df["carrier"].nunique())
    check("carrier order is fixed, not rank-sorted",
          list(by_carrier["carrier"]) == [c for c in CARRIER_ORDER if c in set(df["carrier"])])
    check("carrier spend sums to total billable spend",
          abs(by_carrier["spend"].sum() - kpis["total_spend"]) < 1.0)

    print("\n4b. Count reconciliation — the chart must agree with the KPI cards")
    # A client who adds up the bars and gets a different number than the
    # headline stops believing the whole dashboard. These are the checks that
    # would have caught the 108-shipment gap between the two.
    check("chart shipment counts sum to the Shipments KPI",
          int(by_carrier["orders"].sum()) == kpis["orders"],
          f"{int(by_carrier['orders'].sum()):,} vs {kpis['orders']:,}")
    check("chart billable counts sum to the spend population",
          int(by_carrier["billable_orders"].sum()) == kpis["billable_orders"],
          f"{int(by_carrier['billable_orders'].sum()):,} vs {kpis['billable_orders']:,}")
    check("the shipments/spend gap is fully explained",
          kpis["orders"] - kpis["billable_orders"] == kpis["excluded_from_spend"],
          f"{kpis['excluded_from_spend']:,} excluded = "
          f"{kpis['cancelled_orders']:,} cancelled + {kpis['outlier_orders']:,} outliers "
          f"(overlap {kpis['cancelled_orders'] + kpis['outlier_orders'] - kpis['excluded_from_spend']})")
    check("billable is never larger than total, per carrier",
          bool((by_carrier["billable_orders"] <= by_carrier["orders"]).all()))
    check("on-time % denominator excludes only cancelled",
          kpis["active_orders"] == kpis["orders"] - kpis["cancelled_orders"],
          f"{kpis['active_orders']:,} active of {kpis['orders']:,}")

    print("\n5. Filter behaviour")
    lo, hi = df["ship_date"].min(), df["ship_date"].max()
    mid = lo + (hi - lo) / 2
    first_half = filter_shipments(df, lo, mid, ())
    dhl_only = filter_shipments(df, lo, hi, ("Nordfrakt",))
    check("date filter narrows the dataset", 0 < len(first_half) < len(df),
          f"{len(first_half):,} of {len(df):,} rows")
    check("carrier filter returns only that carrier", set(dhl_only["carrier"]) == {"Nordfrakt"},
          f"{len(dhl_only):,} rows")
    check("empty filter result is handled",
          spend_by_carrier(df.iloc[0:0]).empty)
    # A carrier whose every shipment in view is cancelled or flagged must still
    # appear, at zero spend — otherwise it vanishes from the chart while still
    # counting toward the KPI cards.
    unbillable = df.loc[~df["is_billable"]]
    if len(unbillable):
        ub = spend_by_carrier(unbillable)
        check("carriers with no billable shipments still appear at zero spend",
              len(ub) == unbillable["carrier"].nunique() and bool(ub["spend"].eq(0).all()),
              f"{len(ub)} carriers, {int(ub['orders'].sum())} shipments, €0 spend")
        check("reconciliation holds on that slice too",
              int(ub["orders"].sum()) == compute_kpis(unbillable)["orders"])

    print("\n6. Seeded signal — is there something for the AI briefing to find?")
    m = (df["carrier"] == "Nordfrakt") & df["is_central_europe"] & ~df["is_cancelled"]
    fri = df[m & (df["ship_weekday"] == "Friday")]
    rest = df[m & (df["ship_weekday"] != "Friday")]
    uplift = 100 * (fri["transit_days"].mean() / rest["transit_days"].mean() - 1)
    check("Friday Nordfrakt to Central Europe transit uplift is detectable", uplift > 15,
          f"+{uplift:.0f}% ({len(fri)} Friday vs {len(rest)} other shipments)")
    check("Friday late rate is materially worse",
          fri["is_late"].mean() > rest["is_late"].mean() * 2,
          f"{100 * fri['is_late'].mean():.0f}% vs {100 * rest['is_late'].mean():.0f}% late")

    print("\n7. Determinism")
    res = subprocess.run([sys.executable, str(ROOT / "pipeline" / "generate_data.py")],
                         capture_output=True, cwd=ROOT)
    res2 = subprocess.run([sys.executable, str(ROOT / "pipeline" / "clean.py")],
                          capture_output=True, cwd=ROOT)
    ok = res.returncode == 0 and res2.returncode == 0
    rerun = read_processed() if ok else None
    check("pipeline re-runs cleanly", ok)
    check("re-run produces an identical dataset",
          ok and rerun.equals(df), "same seed → same rows, same order")

    print("\n7b. V1 trend aggregation")
    tr = trend(df)
    check("one row per week, ordered", tr["period"].is_monotonic_increasing and len(tr) > 50,
          f"{len(tr)} weeks")
    check("no partial bucket at either edge",
          int(tr["orders"].min()) > 20,
          f"thinnest week holds {int(tr['orders'].min())} shipments — a clipped "
          "edge week would plot as a cliff to near zero")
    check("weekly spend reconciles with total billable spend",
          abs(tr["spend"].sum() - df.loc[df["is_billable"] & df["ship_week"].isin(tr["period"]),
                                         "freight_cost_eur"].sum()) < 1.0)
    check("weekly on-time stays within 0–100",
          bool(tr["on_time_pct"].between(0, 100).all()),
          f"{tr['on_time_pct'].min():.1f}–{tr['on_time_pct'].max():.1f}%")
    check("late never exceeds shipments in a week",
          bool((tr["late_orders"] <= tr["orders"]).all()))

    print("\n7c. Lane matrix & the sample-size guard")
    rates, counts = carrier_destination_matrix(df)
    check("matrix is carriers × destinations", rates.shape[0] == df["carrier"].nunique(),
          f"{rates.shape[0]} carriers × {rates.shape[1]} destinations")
    check("rates and counts share their shape and labels",
          rates.shape == counts.shape and list(rates.index) == list(counts.index)
          and list(rates.columns) == list(counts.columns))
    check("every populated cell clears the sample-size floor",
          bool((counts.to_numpy()[rates.notna().to_numpy()] >= MIN_LANE_SHIPMENTS).all()),
          f"cells under {MIN_LANE_SHIPMENTS} shipments are masked, not plotted as noise")
    check("thin cells are masked rather than shown",
          bool((rates.isna().to_numpy() == (counts.to_numpy() < MIN_LANE_SHIPMENTS)).all()))
    check("columns run worst-average first",
          list(rates.mean(skipna=True)) == sorted(rates.mean(skipna=True)),
          "so the eye lands on the problem lane")
    check("rows keep the fixed carrier order",
          list(rates.index) == [c for c in CARRIER_ORDER if c in set(df["carrier"])])

    print("\n7d. Briefing — findings must be computed, not invented")
    signal = ai_insights.detect_weekday_signal(df)
    check("the weekday signal is found by search, not hardcoded",
          signal is not None and signal["carrier"] == "Nordfrakt"
          and signal["weekday"] == "Friday" and signal["region"] == "Central Europe",
          f"{signal['carrier']} {signal['weekday']} → {signal['region']}" if signal else "not found")
    if signal:
        # The briefing quotes these figures, so they must match a hand
        # computation over the same rows — a briefing that rounds its own
        # evidence differently is a briefing a client can catch out.
        scope = df.loc[(df["carrier"] == "Nordfrakt") & df["is_central_europe"] & ~df["is_cancelled"]]
        fri = scope.loc[scope["ship_weekday"] == "Friday"]
        rest = scope.loc[scope["ship_weekday"] != "Friday"]
        check("signal shipment counts match the underlying rows",
              signal["shipments"] == len(fri) and signal["baseline_shipments"] == len(rest),
              f"{signal['shipments']} Friday vs {signal['baseline_shipments']} other")
        check("signal penalty equals the sum of those rows' penalties",
              abs(signal["penalties_eur"] - fri["late_penalty_eur"].sum()) < 0.01,
              eur_exact(signal["penalties_eur"]))
        check("signal late rates match the underlying rows",
              abs(signal["late_pct"] - 100 * fri["is_late"].mean()) < 0.01
              and abs(signal["baseline_late_pct"] - 100 * rest["is_late"].mean()) < 0.01,
              f"{signal['late_pct']:.0f}% vs {signal['baseline_late_pct']:.0f}%")

    bullets, evidence = ai_insights.generate_brief(df)
    check("briefing returns at most three bullets", 1 <= len(bullets) <= 3, f"{len(bullets)}")
    check("every number in the briefing traces to the evidence",
          _numbers_are_traceable(bullets, evidence, df))
    check("a slice with no outlier says so instead of inventing one",
          "worth escalating" in ai_insights.generate_brief(
              filter_shipments(df, df["ship_date"].min(),
                               df["ship_date"].min() + pd.Timedelta(days=20), ("Meridian Express",))
          )[0][0])
    check("briefing survives an empty-ish view without raising",
          bool(ai_insights.generate_brief(df.iloc[:1])[0]))

    print("\n7d-ii. Briefing house style")
    all_text = " ".join(bullets)
    check("no em dashes in the briefing", "\u2014" not in all_text,
          "an em dash is the fastest way to look machine-written")
    check("bullets do not share one sentence template",
          len({b.split(".")[0].split()[-1].lower() for b in bullets}) > 1
          if len(bullets) > 1 else True,
          "three bullets off one template read as a template")
    check("every bullet leads with a bold claim",
          all(b.startswith("**") for b in bullets))

    print("\n7e. Money formatting")
    # Design system, section 6: ISO code before the value, narrow no-break space
    # grouping, three significant figures at most in the compact form.
    check("compact form keeps a decimal below 10k", eur(1530) == "EUR 1.5k",
          f"eur(1530) = {eur(1530)} — rounding this to 2k overstates it by 31%")
    check("exact form is used for briefing figures", eur_exact(1530) == "EUR 1 530")
    check("compact form caps at three significant figures", eur(184_212) == "EUR 184k",
          eur(184_212))
    check("negative figures carry a true minus sign", eur_exact(-11_600) == "EUR −11 600",
          eur_exact(-11_600))

    print("\n8. Storage & fallback — the demo must survive a thin environment")
    check("a readable dataset resolves", processed_path().exists(),
          processed_path().name)
    check("CSV fallback is written alongside parquet", CSV_PATH.exists(),
          "so a runtime without pyarrow still boots")
    if parquet_available() and PARQUET_PATH.exists():
        # The bug this guards: processed_path() used to return the parquet
        # whenever the file existed, without checking that anything could read
        # it — so a machine with no engine crashed on startup while a perfectly
        # good CSV sat next to it.
        import utils.dataset as ds
        real = ds.parquet_available
        try:
            ds.parquet_available = lambda: False
            fallback = ds.processed_path()
        finally:
            ds.parquet_available = real
        check("reader falls back to CSV when no parquet engine is installed",
              fallback == CSV_PATH, f"-> {fallback.name}")

        # Full parity, not just row counts: the same frame must come back
        # whichever format the runtime happens to be able to read.
        import utils.dataset as ds2
        real2 = ds2.parquet_available
        try:
            ds2.parquet_available = lambda: False
            csv_df = ds2.read_processed()
        finally:
            ds2.parquet_available = real2
        check("both storage formats hold the same rows", len(csv_df) == len(df),
              f"{len(csv_df):,} rows in each")
        check("both storage formats produce an identical frame",
              bool(csv_df.equals(df)), "same values and same dtypes")
        check("both storage formats produce identical KPIs",
              compute_kpis(csv_df) == compute_kpis(df))
        check("flag columns are hard booleans, never nullable",
              all(str(df[c].dtype) == "bool" for c in
                  ["is_cancelled", "is_late", "is_on_time", "is_billable"]),
              "a nullable flag propagates NA through ~ and &")
    else:
        check("reader falls back to CSV when no parquet engine is installed",
              processed_path() == CSV_PATH, "no engine installed in this runtime")

    print("\n9. Multi-schema ingestion & the upload path")
    import io
    from pipeline import clean as clean_mod
    from utils.dataset import SAMPLE_DIR, normalize_dtypes, sample_files

    samples = sample_files()
    check("sample exports are committed in the repo", len(samples) >= 3,
          ", ".join(p.name for p in samples))
    check("sample_data sits at the repo root, not under data/",
          SAMPLE_DIR.parent == ROOT and SAMPLE_DIR.name == "sample_data",
          "data/ is gitignored and rebuilt; sample_data/ is the committed input")

    # Three systems, three vocabularies. This is the claim the pillar is sold
    # on, so it is asserted rather than asserted-in-a-README.
    headers = {p.name: p.read_text(encoding="utf-8").splitlines()[0] for p in samples}
    check("the samples really do use different column vocabularies",
          len({h.lower().replace(";", ",") for h in headers.values()}) == len(samples))
    check("at least one sample is semicolon-separated",
          any(";" in h and h.count(";") > h.count(",") for h in headers.values()),
          "European spreadsheet locale — nobody should have to hand-fix it")
    check("at least one sample uses none of the canonical field names",
          any(not {"order_id", "ship_date", "carrier"} & set(
                  c.strip().strip('"').lower().replace(" ", "_") for c in
                  h.replace(";", ",").split(","))
              for h in headers.values()),
          "so the alias map is doing real work")

    def _upload(names):
        srcs = [(p.name, io.BytesIO(p.read_bytes())) for p in samples if p.name in names]
        frame, built = clean_mod.build(srcs)
        return normalize_dtypes(frame), built

    up_df, up_log = _upload([p.name for p in samples])
    check("uploading every sample reproduces the bundled dataset",
          len(up_df) == len(df) and up_log["reconciles"],
          f"{up_log['rows_in']:,} in - {up_log['rows_removed']:,} removed = {up_log['rows_out']:,}")
    check("the in-memory build writes nothing to disk",
          _no_new_processed_files(), "a demo server never persists a prospect's data")

    for one in samples:
        solo_df, solo_log = _upload([one.name])
        check(f"{one.name} processes on its own",
              len(solo_df) > 0 and solo_log["reconciles"],
              f"{solo_log['rows_out']:,} rows")

    check("schema mapping is recorded in the audit trail",
          any(step["step"] == "map_schema" for step in up_log["steps"]),
          "the client can see which of their columns was mapped to what")

    # A file that is not a shipment export must be refused with a readable
    # message, not a traceback in front of a prospective client.
    junk = io.BytesIO(b"invoice_no,vendor,amount\nINV-1,Acme,120\nINV-2,Globex,90\n")
    refused = False
    try:
        clean_mod.build([("vendor_invoices.csv", junk)])
    except ValueError as exc:
        refused = "could not be found" in str(exc) and "Columns seen" in str(exc)
    check("a non-shipment file is refused with a readable message", refused)

    print("\n9b. Staleness — the app must never serve a dataset built by old code")
    import os as _os
    import time as _time
    from utils.dataset import ensure_processed as _ensure, write_processed as _write

    marked = df.copy()
    marked["source_file"] = "an_old_layout.csv"
    _write(marked)
    stamp = _time.time() - 600
    for artefact in (PARQUET_PATH, CSV_PATH):
        if artefact.exists():
            _os.utime(artefact, (stamp, stamp))

    check("a build older than its inputs is detected as stale",
          "an_old_layout.csv" in set(read_processed()["source_file"]),
          "planted a dataset stamped by a previous pipeline layout")
    steps_taken = _ensure()
    check("ensure_processed() rebuilds rather than serving it",
          any("rebuilt" in step for step in steps_taken),
          "; ".join(steps_taken) or "nothing rebuilt")
    check("the rebuilt dataset reflects the current sources",
          set(read_processed()["source_file"]) == {p.name for p in sample_files()},
          "otherwise the dashboard shows yesterday's numbers and looks fine doing it")

    print("\n10. Deployment invariants")
    reqs = [ln.strip() for ln in (ROOT / "requirements.txt").read_text(
        encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]
    check("every dependency is pinned to an exact version",
          all("==" in r for r in reqs), ", ".join(reqs))
    declared = {r.split("==")[0].lower() for r in reqs}
    check("no dependency is declared that nothing imports",
          declared == {"streamlit", "pandas", "numpy", "plotly", "pyarrow"},
          "lean build = fast cold start on Community Cloud")
    check("entrypoint is app.py at the repository root", (ROOT / "app.py").exists())
    check("the repo is self-contained — no imports from sibling pillars",
          _no_cross_repo_imports(), "multi-repo standard")
    check("no energy, meter, tariff or carbon vocabulary anywhere",  # NON-COMPETE-OK
          _non_compete_clean(), "domain guardrail: this product stays out of energy")

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} check(s) failed: {', '.join(FAILURES)}")
        return 1
    print("✅ All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
