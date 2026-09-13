# Quickstart — Pillar 1 V1

```bash
# 1. Install
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt

# 2. (Optional) rebuild the sample exports and the dataset.
#    Not needed to run: sample_data/ is committed and app.py builds
#    data/processed/ itself on first launch.
python pipeline/generate_data.py     # -> sample_data/*.csv  (5,020 messy rows, 3 exports)
python pipeline/clean.py             # -> data/processed/shipments.parquet + cleaning_log.json

# 3. Verify
python tests/test_pipeline.py        # 82 checks, no Streamlit needed

# 4. Run the dashboard
streamlit run app.py
```

## What V1 contains

| File | Role |
| :--- | :--- |
| `pipeline/generate_data.py` | 5,000 synthetic freight shipments across 6 carriers and 14 destination countries, written into `sample_data/` as **three CSVs from three different systems** — a legacy WMS (snake_case), a newer TMS (Title Case), and a parcel broker (UPPER_SNAKE, semicolon-separated, completely different field names) — to prove schema normalisation rather than assert it. Deliberately messy: 4 date formats, carrier spelling variants, multi-currency costs, nulls, fat-finger outliers, negative transit days, duplicate order IDs. |
| `pipeline/clean.py` | Deterministic normalisation. Every transformation is written to `data/processed/cleaning_log.json` with a row count and a reason. `rows_in − rows_removed = rows_out` is asserted. |
| `utils/metrics.py` | Pure pandas analytics — no Streamlit, so it is unit-testable. |
| `utils/theme.py` | Design tokens for both themes, the component CSS and the Plotly templates. Carriers map to fixed colour slots, so filtering never repaints the survivors. The full specification is `docs/design-system.md`. |
| `utils/ui.py` | HTML components of the design system: masthead, KPI tile, findings panel, badges, alerts, tables. |
| `utils/charts.py` | The three figures and the Chart / Table card. |
| `utils/fmt.py` | Every number, currency and date format. One place, so a tile and a table never disagree. |
| `utils/dataset.py` | Parquet I/O with a gzipped-CSV fallback that is written every time and actually *read* when no parquet engine is present. Also `ensure_processed()`, which builds the dataset on first use so a fresh clone or a Streamlit Cloud deploy starts without a stack trace. |
| `utils/ai_insights.py` | The executive briefing. Detection is a **search** over carriers x regions x weekday, ranked by money at stake, so it finds the signal on a client's data rather than looking up a known answer. Narration is deterministic composition from those figures — see the note below. |
| `app.py` | Streamlit UI: filter row, 4 KPI cards, the briefing, two primary charts on the first fold, details in four tabs. Cache keys are scalars, never the frame, so rerun cost does not scale with row count. |
| `tests/test_pipeline.py` | 82 verification checks: determinism, signal detection, count reconciliation between the chart and the KPI cards, and storage-format parity. |

## The seeded insight (for the V1 AI briefing)

The generator plants one non-obvious operational signal:

> **DHL shipments dispatched on Fridays to Central Europe (DE/AT/CH/PL/CZ) run
> ~27% longer in transit than the same lanes on other weekdays — a 39% late rate
> versus 4%, worth roughly €1.5k in SLA penalties.**

This is what the "Generate AI Executive Briefing" button is meant to surface in
V1. Verified detectable by `tests/test_pipeline.py` section 6.

## Repository layout (standalone, multi-repo standard)

```text
.
├── app.py                 # entrypoint — Streamlit Cloud points here
├── requirements.txt       # 5 packages, all pinned, all imported
├── sample_data/           # COMMITTED. 3 client-style exports, 3 schemas.
├── pipeline/              # generate_data.py, clean.py
├── utils/                 # dataset, metrics, theme, ai_insights
├── tests/test_pipeline.py
└── data/                  # GITIGNORED. Rebuilt on first run.
```

Nothing imports from outside this folder, and nothing here depends on the
other pillars. Sections 9 and 10 of the test suite enforce that, along with
the pinned-and-lean dependency rule and the domain vocabulary ban — and
all three guardrails are verified to fail on a planted violation, so they are
gates rather than decoration.

## Two ways in (zero-friction client demo)

1. **Sample freight book (default).** Opens already working — no upload, no
   click. `sample_data/` is committed and `ensure_processed()` builds the
   analysis table on first launch, so a fresh clone and a cold Streamlit Cloud
   deploy both boot straight to a populated dashboard.
2. **Upload your own exports.** The same pipeline, run **entirely in memory** —
   nothing a prospect uploads is written to disk. The delimiter is sniffed and
   column names are mapped through `COLUMN_ALIASES` in `pipeline/clean.py`, so
   a client's file does not have to match our field names. A file that is not
   a shipment export is refused with a readable message naming the fields it
   could not find and the columns it did see. The upload panel also offers the
   three sample files as downloads, so the upload path can be demonstrated in
   two clicks without anyone's real data.

## The briefing: what is and is not "AI"

`utils/ai_insights.py` computes every figure in the briefing with pandas and
composes the sentences from those figures. **No language model is called**, so
there is nothing in the output that can be hallucinated — which is the
invariant this portfolio is sold on.

The split is deliberate and is the part worth explaining to a client: finding
the signal is the hard problem and it belongs in testable Python; phrasing it
is the easy problem and is the only thing a model would be handed. When the
Anthropic call is wired up it replaces exactly one function, `narrate()`, and
`PROMPT` already forbids it from doing arithmetic. `build_evidence()` is the
handover format.

Section 7d of the test suite enforces this: it re-derives the signal's figures
from the raw rows, and asserts that **every number quoted in the briefing
appears in the evidence**. That check is verified to fail on a fabricated
figure, so it is a real gate rather than a comment.

## Chart decisions worth knowing

* **The trend is two stacked panels, not a dual axis.** Plotting euros and
  percent against two y-scales on one plot invents a correlation out of where
  the scales happen to be pinned. Two panels sharing an x-axis show the same
  comparison honestly.
* **Weekly, not daily, buckets.** The data averages ~9 shipments a day, so a
  daily on-time rate swings 0-100% on sample size alone. Weekly buckets hold
  ~60 shipments. Partial buckets at either edge are trimmed — they otherwise
  plot as a cliff to near zero that reads as a business collapse.
* **The heatmap encodes LATE rate, not on-time rate.** Same information, but a
  sequential ramp puts the darkest cells where attention is needed. Plot
  on-time and the failing lanes become the palest cells on the grid.
* **Lanes under 8 shipments are left blank.** One late shipment out of two is
  "50% late", which would paint the grid with alarming cells that mean nothing.
* **Carrier colours are fixed slots**, validated against this app's white
  surface (worst adjacent CVD dE 9.1, normal-vision dE 19.6). Three of the six
  sit below 3:1 contrast, so every chart using them ships direct value labels
  and a table view as the relief channel. Never add a seventh by inventing a
  hue.

## Reconciliation rules

Three populations are in play, and the UI states which one every number uses:

| Population | Definition | Drives |
| :--- | :--- | :--- |
| all | every shipment in the filtered view | the **Shipments** KPI, and the chart's shipment counts |
| active | all minus cancelled | on-time %, average delay, penalties |
| billable | active minus flagged cost outliers | **Total freight spend**, and the bar heights |

The chart's shipment counts sum to the Shipments KPI, and the gap to the spend
population is broken out in the caption rather than left for the client to
find. `tests/test_pipeline.py` section 4b enforces this.

Cancelled shipments keep a null `transit_days` and a null `delivery_date` —
they never moved, so there is nothing to impute. They are logged separately
from genuinely missing values.

## Business assumptions (documented, not hidden)

* Late-delivery penalty: **€45 per shipment per day late** (`LATE_PENALTY_EUR_PER_DAY` in `clean.py`).
* FX to EUR: USD 0.92, SEK 0.087 — fixed reference rates, not live.
* Cost outliers: IQR rule per service level, multiplier 3.0. Flagged and excluded
  from spend KPIs, **never deleted**.

## Not yet done (V1)

* Plotly line chart (daily cost vs on-time trend) and carrier × destination heatmap
* `utils/ai_insights.py` — streamed executive briefing
* Streamlit Cloud deployment

## Not yet done

* **Wire the Anthropic call.** Replace `narrate()`; keep detection in Python.
  `ANTHROPIC_API_KEY` goes in `.env` locally and in Streamlit Cloud secrets.
* **Deploy to Streamlit Cloud.** The app is deploy-ready: `data/processed/` is
  gitignored and `ensure_processed()` rebuilds it on first load, so a fresh
  clone boots with no error page.
* **V2:** multi-source ingestion, Slack/email alerts, Excel export centre.
