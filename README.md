# Airline fuel shock monitor

> **Draft (P2).** Company figures are still being verified against the source pages; the page
> shows how many are verified. Not investment advice. Not affiliated with any company shown.

**Question.** Is Lufthansa Group more or less exposed to the 2026 jet fuel shock than Air France-KLM
and IAG, and what does it do to each company's earnings per share versus consensus, for FY2026 and FY2027?

## What it shows
Three pages. **The story** asks the question first and builds the answer from the bottom up, so the conclusion is
earned before it is stated:
1. **The question.** Jet fuel is up since 27 July; is Lufthansa hit harder than its rivals?
2. **The evidence.** How big the move is; what it is made of (crude oil or the refining premium, which a crude hedge
   does not cover); how much of each airline's fuel is actually protected.
3. **The analysis.** The extra fuel bill after hedging; how much airlines recover through fares; what is left of
   profit, margin and EPS; and why the three differ.
4. **The assumptions.** Which one could change the order, shown as a bar per assumption.
5. **The answer**, a fixed-template sentence filled with model outputs (never written by AI), with the confidence
   label next to it. A ranking or driver is named only if it holds across the whole range of assumptions.
6. **What it means**, including whether an always-on monitor would raise an alert (a hit of at least 5% of
   expected operating profit or EPS), and a set of controls to change the scenario yourself.

**Method & sources** holds every source, assumption and check behind the numbers; small markers in the story link to
the matching entry. The **News room** is a separate prototype: an AI model labels headlines about the airlines and
jet fuel, every quote is checked against the headline in code, and nothing from it feeds a number in the story.

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
- **Tests**: 290 automated tests (`pytest`), including a run of the page itself; the network is mocked.

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
- A licensed consensus API (EPS, EBIT, revenue with per-estimate dates) instead of dated page snapshots
  refreshed by hand - the provider pages block automated access.
- Market-reaction validation (share prices on fuel-event days). Not in v1: free price feeds such as
  Tiingo's standard plans are licensed for internal use only, not public display.
- Monte Carlo over the uncertain assumptions (g, recapture, FY2027 volume) for an EPS range.
- Valuation view (EV/EBIT, implied equity value); ETS/SAF cost drivers as an ESG extension.
- Quarterly capacity (ASK) weighting instead of equal quarters; more carriers (Ryanair, Turkish, Gulf).
- Adversarial reviewer agent that challenges every alert before it is shown.

## Run locally
```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
python -m pytest
```
