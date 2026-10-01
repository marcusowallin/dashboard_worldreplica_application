# Airline fuel shock monitor

> **Draft (P2).** Company figures are still being verified against the source pages; the page
> shows how many are verified. Not investment advice. Not affiliated with any company shown.

**Question.** Is Lufthansa Group more or less exposed to the 2026 jet fuel shock than Air France-KLM
and IAG, and what does it do to each company's earnings per share versus consensus, for FY2026 and FY2027?

## What it shows
Three pages. **The story** asks the question first and builds the answer from the bottom up, so the conclusion is
earned before it is stated:
1. **The question.** Jet fuel is up since 27 July; is Lufthansa hit harder than its rivals? The page applies one
   hypothetical shock (USD 100 a tonne) to all three airlines and says so up front.
2. **The evidence** (steps 1-2). How big the move is and what it is made of (crude oil or the jet premium, which a
   crude hedge does not cover); how much of each airline's fuel is actually protected.
3. **The analysis** (steps 3-5). The fuel bill after hedging and what fares give back; what is left of profit and EPS;
   why the three differ.
4. **What the result rests on** (step 6). A tornado of the assumptions, plus the choices that change the levels - how much
   of the shock lasts into 2027, what "pass-through" is applied to (for Air France-KLM it decides whether it pays or
   gains), Lufthansa's undisclosed hedge mix and its options - and a short list of what the model cannot tell you.
5. **The answer** (step 7), a template sentence filled with model outputs (never written by AI), with the confidence
   score next to it. A ranking or driver is named only if it holds across the whole range of assumptions.
6. **What it means** (step 8), including whether an always-on monitor would raise an alert (a hit of at least 5% of
   expected operating profit or EPS), and **controls to change the scenario yourself** (step 9).

**Method & sources** holds every source, assumption and check behind the numbers, including how the confidence score
is calculated; small markers in the story link to the matching entry. The **News room** is a separate prototype: an AI
model labels headlines about the airlines and jet fuel, every quote is checked against the headline in code, and nothing
from it feeds a number in the story.

## How it works (pipeline)
The pipeline follows the six steps of a typical always-on impact monitor, on a small scale:

| Step | Here |
|---|---|
| 1. News and data | Live jet fuel and Brent (FRED), USD/EUR (ECB); company documents |
| 2. Research agent | *P3:* news headlines classified by an LLM (classification only, evidence-checked in code) |
| 3. Digital twins | `data/airlines.yaml`: identical fields per airline, each value as printed, with document, page and quote |
| 4. Strategy / impact model | Deterministic Python model, identical for every airline (`src/model/`) |
| 5. Alert | EPS impact versus consensus, flagged material only at 5% or more |
| 6. User | The story page (question, evidence, analysis, assumptions, answer), sources on a second page, the AI news room on a third (`app.py`, `story.py`, `method.py`, `news.py`) |

## Method in brief
Full detail in [06_METHODOLOGY.md](06_METHODOLOGY.md); every assumption in [ASSUMPTIONS.md](ASSUMPTIONS.md).
1. **Hedge quality.** A jet fuel move = Brent move + jet crack move. All hedges protect against Brent;
   Brent hedges do *not* protect against the crack; gasoil hedges protect a share g = 0.8; jet hedges fully.
2. **Fuel cost change** = volume x (unprotected share x Brent move + unprotected share x crack move).
3. **EBIT** = -(1 - recapture) x fuel cost change; **net income** = EBIT x (1 - marginal tax) x
   (1 - minorities); **EPS** = net income / diluted shares.
4. **Periods.** FY2026 = months since 27 Jul 2026 at actual monthly average moves + the rest of the year
   at the latest move; FY2027 = full year at the latest move (parallel shift).
5. **Ranges, not false precision.** Peers' undisclosed instrument mix (jet-equivalent to crude-only);
   Lufthansa's FY2027 hedge cover (29% printed Dec 2025 to ~50% reported); Lufthansa's option effect
   (its own sensitivity table).

## Sources
Company figures come from the companies' own documents (source level 1) and are used exactly as printed.
Where nothing is printed, the fallback order is: company-compiled consensus, official filings, reputable
third parties (with a dated snapshot), then a labelled assumption. The level and status of every figure
is on the page.

| Company | Documents used |
|---|---|
| Lufthansa | Q2 2026 results charts (4 Aug 2026), 2nd interim report 2026, Annual Report 2025, analyst consensus poll (16 Jul 2026, cross-check) |
| Air France-KLM | Q2 2026 press release and presentation (30 Jul 2026), Q1 2026 press release and presentation, FY2025 press release, Universal Registration Document 2025 |
| IAG | H1 2026 results announcement, presentation and call transcript (31 Jul 2026), FY2025 results release, Annual Report 2025 |
| Third party | Consensus EPS and revenue: MarketScreener (snapshot 30 Sep 2026); Lufthansa FY2027 hedge remark: Reuters (29 Sep 2026) |
| Market data | FRED DJFUELUSGULF and DCOILBRENTEU; ECB reference rate via Frankfurter |

Company PDFs are not republished; the page links to the originals with page numbers.

## Validation
- **T2 - reproduce Lufthansa's own sensitivity table** (Q2 charts, slide 17), cell by cell, no tuning.
  The crack sensitivity fits; the Brent sensitivity does not. Lufthansa's own numbers imply far less
  protection against a Brent rise than a swap model assumes, and less the higher prices go, consistent
  with its option combinations. The Method & sources page shows the grid, and the model adds a "company table" case for Lufthansa.
- **T4 - independent EPS reconciliation** from printed inputs (automated test).
- **T9 - fuel bill reconciliation**: Lufthansa volume x price after hedge = EUR 8.48bn vs printed fossil
  fuel expense EUR 8.46bn (+0.2%). Not possible or not independent for the peers (explained on the page).
- **Tests**: 320 automated tests (`pytest`), including a run of the page itself; the network is mocked.

## Limitations
Spot moves as a parallel shift of the forward curve; US Gulf Coast jet as proxy for European jet; options
treated as swaps (see T2); peers' instrument mix not disclosed; recapture rates not like-for-like; volumes
held constant, equal quarters where not printed; consensus snapshot dated after most of the move; Lufthansa
FY2027 hedge cover not printed as of the baseline date. Full list on the page.

## Roadmap
- **P3 - news room agent**: refresh-on-click headlines, LLM tagging (airline, driver, direction, severity,
  verbatim evidence checked in code), cost guards, evaluation against hand labels.
- **P4 - depth**: Air France-KLM backtest (April vs July curve), full driver waterfall, balance sheet panel
  (cash flow, net debt, leverage, hedge reserve).
- **P5 - disclosure agent**: extract figures from new company documents with validation in code and
  human approval before anything reaches the twins.

## Ideas for improvement
- Licensed European jet fuel (NWE CIF) and forward curves instead of spot proxies.
- One source of truth for consensus: every consensus input (EPS, EBIT, revenue) from MarketScreener or a similar
  provider, on one date and read by one method. A licensed API with per-estimate dates would make the refresh
  automatic - the provider pages block automated access, so snapshots are saved by hand today.
- Market-reaction validation (share prices on fuel-event days). Not in v1: free price feeds such as
  Tiingo's standard plans are licensed for internal use only, not public display.
- Monte Carlo over the uncertain assumptions (g, recapture, FY2027 volume) for an EPS range.
- Valuation view (EV/EBIT, implied equity value); ETS/SAF cost drivers as an ESG extension.
- Quarterly capacity (ASK) weighting instead of equal quarters; more carriers (Ryanair, Turkish, Gulf).
- Adversarial reviewer agent that challenges every alert before it is shown.

## Deploy (Streamlit Community Cloud)
Main file `app.py`; Python 3.14 if offered (the pins were tested on 3.14.7; CI also runs 3.13). The runtime needs only
`requirements.txt`. The app runs without secrets; to switch the News room's AI labels on, add `ANTHROPIC_API_KEY` in the
app's secrets and set a spending limit for the key in the Anthropic console (the app also caps its own calls: 20 tagging
calls a day, 5 web searches a day, shared by all visitors, kept in memory).

## Data and licences
Prices: FRED (jet fuel `DJFUELUSGULF`, Brent `DCOILBRENTEU`) and the ECB reference rate via Frankfurter, fetched live.
News headlines: GDELT. Company figures are typed into `data/airlines.yaml` from the companies' own reports, each with
document, page and quote; the reports themselves are not republished. Consensus figures from MarketScreener are
transcribed by hand with a snapshot date; no screenshots or tables are redistributed. Fonts load from Google Fonts at
runtime. Check each provider's terms before reusing the data.

## Run locally
```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt          # enough to run the app
streamlit run app.py
pip install -r requirements-dev.txt      # adds the test tools
python -m pytest
```
Changes under `src/` need the app restarted: Streamlit does not reload imported modules.
