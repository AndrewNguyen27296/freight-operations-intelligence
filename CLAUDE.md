# Pillar 1 - Data Pipeline Dashboard

Freight operations briefing built from three client-style CSV exports with three
different column vocabularies. Live at <https://freight-operations-intelligence-gr6t94nmogzgzh3cgy2plf.streamlit.app/>.
Repo: <https://github.com/AndrewNguyen27296/freight-operations-intelligence>.

Read `README.md` for the product vision, `QUICKSTART.md` for how to run it, and
`docs/design-system.md` for every visual decision the UI implements.

## The portfolio this belongs to

Three Streamlit products, built as proof-of-work to win freelance B2B data/AI
engagements in Sweden, the Nordics and Europe. Each has one 60-second "wow
moment" it exists to deliver. They are sold through three tiers: advisory audits
(~$500/day), turnkey builds ($1,000-$4,000), and managed retainers
($250-$600/month).

| Pillar | What it is | Code | Repo | Live URL |
| :--- | :--- | :--- | :--- | :--- |
| 1. Data Pipeline Dashboard | Freight ops briefing from messy multi-schema CSVs | V1 | yes | **live** |
| 2. Invoice & Vision Parser | Zero-manual-entry AP with an arithmetic audit | V1 | not yet | not yet |
| 3. Chat with Docs RAG | Cited, hallucination-free answers over company docs | V1 | not yet | not yet |

Pillar 1 is live at https://freight-operations-intelligence-gr6t94nmogzgzh3cgy2plf.streamlit.app/.

## The plan, in order

The bottleneck is not building. All three are built. The bottleneck is that a
prospect cannot reach them, so work top-down and resist polishing.

**Phase A - ship what exists.** git init, push to GitHub, deploy to Streamlit
Community Cloud, smoke-test the live URL cold. Done for Pillar 1; Pillars 2 and
3 still need it.

**Phase B - turn demos into conversations.** A 60-second screen recording per
pillar. A one-page offer with price and timeline. A list of 25-30 Nordic
companies in the safe verticals. Then send it.

**Phase C - product work, but only what a prospect actually asks for.** Export
centres, multi-source ingestion, alerting. Do not start Phase C before Phase B
has produced a real conversation; the audit is what tells you which of these is
worth building.

The fastest first revenue is a Tier 1 audit. It needs no further product work at
all - the live demos are credibility, not the deliverable.

## Deploying to Streamlit Community Cloud

Proven on Pillar 1. The recipe:

1. `git init -b main`, then pin the identity **repo-locally** so the repo cannot
   inherit a work identity later:
   `git config user.email nguyenhuuthien27296@gmail.com`
2. Check `.gitignore` covers `.venv/`, `__pycache__/`, `.env`,
   `.streamlit/secrets.toml` and any derived data directory. Confirm with
   `git add -A && git diff --cached --name-only` before the first commit.
3. Create an **empty** repo at github.com/new under the personal account
   (`AndrewNguyen27296`) - no README, no .gitignore, no licence, or the first
   push conflicts.
4. `git remote add origin <url> && git push -u origin main`
5. share.streamlit.io -> New app -> pick the repo, branch `main`, main file
   `app.py`.

**The trap that cost Pillar 1 its first deploy:** Community Cloud builds on
**Python 3.14**. A pinned dependency with no cp314 wheel makes pip fall back to
compiling from source, and the build image has no `cmake`. `pyarrow==21.0.0`
ships wheels only to cp313, so the build died. Fixed by moving to
`pyarrow==25.0.1`, which covers 3.10-3.14.

Before deploying anything, check every pin for a 3.14 wheel against
`https://pypi.org/pypi/<pkg>/<version>/json`. Wheels tagged `py3-none-*` or
`cp39-abi3` are version-agnostic and fine; a wheel range ending at cp313 is not.

Note that `streamlit` itself depends on `pyarrow>=7.0`, so pyarrow is installed
whether or not it is listed - the only real choice is which version.

## Hard rules

- **Domain restriction.** No energy consumption, electricity tariff, smart-meter,
  building-meter, or carbon/ESG data or vocabulary anywhere in these
  repositories - not in code, samples, docs or test fixtures. Safe verticals are
  logistics and freight, e-commerce, retail, corporate travel, and professional
  services. Pillar 1 enforces this with a test that greps every tracked file.
- **Never commit the parent `AI Startup/` folder.** It holds private strategy
  notes. One repository per pillar, rooted in that pillar's own directory.
- **Public repos.** These are or will be public. Do not write the author's
  employer, work email, or client names into any tracked file. Commit as the
  personal identity above, never the work one.
- **Personal equipment and personal hours only.**

## Where this pillar stands

**V1 shipped and live.** Phase A is complete for this pillar.

- 82 verification checks pass: `python tests/test_pipeline.py` (no flag needed;
  the suite forces UTF-8 on stdout for Windows consoles).
- Findings are computed deterministically in pandas. No model is called, so
  nothing in the briefing can be hallucinated. `narrate()` in
  `utils/ai_insights.py` is the single seam an LLM would replace, and it gets
  phrasing only, never arithmetic.
- A filter change round-trips in ~810 ms in production, network included.

Known open items, none blocking:

- `build_findings` costs ~186 ms at 5k rows but ~466 ms at 49k, because it
  recomputes aggregates `app.build_view` already holds. The README's <500 ms
  invariant holds at demo scale, not at a large client's annual book. Only worth
  fixing when a real client file is actually slow.
- Every `st.download_button` payload is fetched on page load rather than on
  click, so each visitor pulls ~570 KB of sample CSVs before seeing anything.
  Collapsing the sidebar samples into an `st.expander` would defer it.
- Three product judgements are open: findings 1 and 2 are the same story (both
  the same carrier), the seeded Friday/Central-Europe insight that the whole
  pitch is built on ranks last by money, and the cost-per-carrier chart has no
  spread in it (all six carriers land at EUR 84-86).

## Next action here

Phase A is done here. This pillar's remaining value is in **Phase B** - record
the 60-second walkthrough using the script in `README.md` section 6, against the
live URL.

Do not start Phase C work on this pillar before Phase B has produced a real
prospect conversation.
