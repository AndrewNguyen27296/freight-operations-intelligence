# 📊 Pillar 1: Automated Data Pipeline & Interactive Executive Dashboard

> **The North Star:** *"Zero-Click Operational Clarity."*  
> An operations manager or executive opens this dashboard at 8:00 AM, sees the complete pulse of their logistics and shipping costs in 5 seconds, filters down to root causes of delays in 2 clicks, and gets an AI-generated strategic briefing without touching Excel.

---

## 🧭 1. Vision & The Strategic "Why"

### The Target Persona (The Buyer):
* **Who:** VP of Operations, Supply Chain Director, or E-Commerce Brand Founder.
* **Their Daily Hell:** They have 5 different CSV exports from shipping carriers, warehouse portals, and Shopify. Every Monday morning, an analyst spends 4 hours combining them, fixing broken date formats, and making ugly static charts.
* **The Transformed State:** An automated pipeline ingests raw files nightly, cleans and normalizes schema discrepancies, calculates true unit economics, and renders an executive-ready dashboard with live AI commentary.

### The 60-Second "Wow Moment" (Your Demo North Star):
1. The prospective client opens the live Streamlit URL.
2. They drag a date slider and select a carrier $\rightarrow$ **all Plotly charts animate instantly with sub-second latency**.
3. They click **"Generate AI Executive Briefing"** $\rightarrow$ Claude streams a 3-bullet analysis that uncovers a non-obvious business insight:
   > *"⚠️ Carrier DHL has experienced a 28% increase in transit delays on Friday dispatches to Central Europe, causing an estimated $3,800 in late-delivery penalties."*
4. Client reaction: *"This is exactly what I spend my entire Monday trying to figure out."*

---

## 🏛 2. Architectural Invariants (The Non-Negotiables During Vibe Coding)

When vibe coding with AI, enforce these technical guardrails:

1. **Domain Invariant:** Zero energy, smart meter, or carbon data. Keep the domain strictly to **Global Logistics, Freight Shipping, or Multi-Channel E-Commerce**.
2. **Deterministic Data Transformations:** No silently dropped rows. Every transformation (missing value imputation, outlier detection, currency conversions) must log what was cleaned.
3. **Sub-Second Filter Latency:** All aggregated metrics and charts must update in `< 500ms` using `@st.cache_data`. The client must never experience a freezing screen.
4. **No Visual Clutter:** Maximum of 4 KPI cards at the top. Two primary charts on the first fold. Details live in collapsible tabs.

---

## 🗺 3. Phased Roadmap: From Vibe Coding to Paid Client Delivery

```
[V0: Walking Skeleton] ──► [V1: Client-Ready Hero Demo] ──► [V2: Commercial Offering]
(1 Evening - 2 Hours)      (1 Evening - 3 Hours)             (What You Sell for $1,500)
```

### Phase V0: The Walking Skeleton (Evening 1 — Fast MVP)
* [x] **Generate Realistic Synthetic Data:** Create `pipeline/generate_data.py` producing 5,000 realistic shipment rows (`order_id`, `date`, `carrier`, `origin`, `destination`, `freight_cost`, `transit_days`, `status`).
* [x] **Core Cleaning Pipeline:** Script in `pipeline/clean.py` that normalizes dates, handles nulls, and computes core aggregates.
* [x] **Minimal Streamlit App:** Display 4 KPI metrics (`Total Spend`, `Average Delay`, `Total Orders`, `On-Time %`) and one basic Plotly bar chart.

### Phase V1: The Client-Ready Hero Demo (Evening 2 — Visual Delight)
* [x] **Polished Executive Layout:** Modern dark/light UI styling with custom CSS metrics and clean card hierarchy.
* [x] **Interactive Visuals:** 
  * Plotly trend: weekly cost and on-time delivery as **two panels sharing one
    x-axis** — not a dual axis, which would invent a correlation out of where
    the two scales happen to be pinned. Weekly rather than daily because a
    daily on-time rate over ~9 shipments is sample noise.
  * Plotly heatmap: carrier x destination **late** rate on a single-hue
    sequential ramp, so the darkest cells are the lanes that need attention.
    Lanes under 8 shipments are masked rather than shown as noise.
* [~] **AI Summary Layer (`utils/ai_insights.py`):** Streamed executive brief on
  the currently filtered view. **Detection is done and deterministic** — a
  search over carriers x regions x weekday, ranked by money at stake, that
  rediscovers the seeded signal without being told where to look, and a test
  asserts every quoted figure traces back to computed evidence. The model call
  is not wired yet: `narrate()` is the single function it replaces, and it gets
  phrasing only, never arithmetic. Detection stays in Python where it can be
  unit-tested, because finding the signal is the hard part and a model is the
  wrong tool for it.
* [ ] **Deploy to Streamlit Cloud:** Public live URL with pre-loaded mock data so anyone can test it with zero friction.

### Phase V2: Commercial Enterprise Delivery (The Upsell Package)
* [ ] **Multi-Source Ingestion:** Automated webhook ingestion from Google Drive, Dropbox, or S3 bucket.
* [ ] **Automated Daily Email/Slack Alerts:** Send a PDF snapshot or Slack webhook alert when delay thresholds exceed 15%.
* [ ] **Export Center:** Download filtered slice directly to formatted Excel or CSV.

---

## 📂 4. Project Directory Blueprint

```text
Pillar 1 - Data Pipeline Dashboard/
├── README.md                 # This North Star document
├── requirements.txt          # Python dependencies
├── .env.example              # API keys template
├── sample_data/              # COMMITTED — 3 client-style exports, 3 schemas
├── data/
│   └── processed/            # GITIGNORED — rebuilt on first run
├── pipeline/
│   ├── generate_data.py      # Script to generate realistic logistics data
│   └── clean.py              # Schema normalization & metric aggregations
├── docs/
│   └── design-system.md      # The design system the UI implements: tokens, components, chart theme
├── utils/
│   ├── ai_insights.py        # Deterministic findings and executive summary (the LLM seam)
│   ├── metrics.py            # Pure pandas analytics
│   ├── theme.py              # Design tokens, component CSS, Plotly templates (dark default, light alternative)
│   ├── ui.py                 # HTML components: masthead, KPI tile, findings panel, tables
│   ├── charts.py             # The three figures and the Chart / Table card
│   └── fmt.py                # Every number, currency and date format
├── tests/test_pipeline.py    # Verification checks
└── app.py                    # Streamlit interactive UI (entrypoint)
```

---

## 📦 5. Starter Dependencies (`requirements.txt`)

```text
streamlit==1.50.0
pandas==2.3.3
numpy==2.4.6
plotly==6.9.0
pyarrow==21.0.0
```

Pinned exactly, and every one of them is imported somewhere. `anthropic` and
`python-dotenv` were removed: V1 computes the briefing deterministically and
makes no network call, so shipping them would slow the Community Cloud cold
start for nothing. `anthropic` goes back in when `narrate()` is wired to a
model.

---

## 🎥 6. The 60-Second Client Pitch Script

> *"Hi! In this quick 60-second walkthrough, I'm showing an automated operational intelligence dashboard I built using Python, Streamlit, and Claude.*
> 
> *Instead of relying on messy weekly spreadsheets, this pipeline automatically ingests operational shipment logs, cleans missing data, and aggregates key business KPIs in real time.*
> 
> *Stakeholders can filter by carrier, destination, or date range, and the entire interface updates instantly. Notice the 'AI Executive Briefing' button—it translates current data trends into actionable leadership bullet points in seconds.*
> 
> *I can build a custom automated pipeline and dashboard like this for your specific dataset within 5 to 7 days. Try the live link below to test it yourself!"*
