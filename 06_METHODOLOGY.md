# Methodology: from a jet fuel move to EPS vs baseline

This file defines exactly what we calculate and why. 02_SPEC.md says what to build;
this file says how the numbers work. All company inputs are printed figures (see CLAUDE.md).

---------------------------------------------------------------------------------------------
## 1. The question, split into answerable parts
---------------------------------------------------------------------------------------------
Headline: "Is Lufthansa Group (us) more or less exposed to the jet fuel shock than Air France-KLM
and IAG - and what does it do to each company's earnings per share versus its baseline?"
Baseline = company-compiled consensus EPS (fallback: last full-year EPS); guidance is context
only (section 6).

Sub-questions (each is one output on screen):
Q1 Sensitivity   - What does a USD 100/t move in jet fuel do to each airline's EBIT, net income and
                   EPS for the rest of FY2026 and for FY2027 (before and after recapture)?
Q2 Live variance - How much has the actual price move since the baseline date (27 Jul 2026,
                   the date of the curves behind each company's fuel guidance) changed its
                   expected EPS versus baseline? (Position within guidance shown as context.)
                   Favourable or unfavourable, and is it material?
Q3 Why           - Decompose each airline's exposure into: hedge ratio, hedge quality (crude vs
                   jet), recapture, currency, profit and share-count cushion.
Q4 Balance sheet - What does the move do to cash, net debt, leverage and equity (hedge reserve)?
                   (P4)
Context          - Locked-in hedge price levels (competitive cost position), shown, not modelled.

---------------------------------------------------------------------------------------------
## 2. Notation and inputs (per airline, per period p = rest of FY26, FY27)
---------------------------------------------------------------------------------------------
Prices (USD per metric tonne)
  J  = jet fuel price;  J = B + C
  B  = Brent expressed in USD/t of jet-equivalent volume (convert USD/bbl -> USD/t with one
       stated factor, ~7.9 bbl per tonne of jet fuel; labelled assumption, used consistently)
  C  = jet crack (jet minus Brent), USD/t
  dB, dC, dJ = moves versus the baseline price (our spot series on 27 Jul 2026, section 4)

Volumes and hedges (printed where available)
  V_p   = jet fuel volume in period p (tonnes). If not printed: derived as fuel bill excl.
          emissions/SAF (USD) / average jet price after hedge (USD/t), both printed; status
          "derived". Else split FY volume by quarterly capacity (ASK), status "assumption".
  hB_p  = share of V_p hedged with Brent instruments
  hG_p  = share hedged with gasoil instruments
  hJ_p  = share hedged with jet instruments (swaps)
  h_p   = total hedge ratio = hB + hG + hJ  (if only the total is printed: instrument mix
          "not disclosed" -> RANGE, see section 3 "Undisclosed instrument mix" - decided 29 Sep 2026)
  Airline-specific rules (decided 29 Sep 2026; values and formulas in 03_DATA_REGISTER.md):
    Lufthansa rest of FY26: printed split (slide 17 fn 2: gasoil 48, Brent 33 of 81) applied to
      the YTG hedge ratio 82%: hG = 0.82 x 48/81, hB = 0.82 x 33/81, hJ = 0 (derived).
      Sensitivity: same split on 85% (slide 18). Footnote-vs-table conflict = stated limitation.
    IAG FY27: h = simple average of printed quarterly 2027 ratios (slide 30) = 43.25% (derived;
      no quarterly weights printed). Transcript "around 40%" = printed cross-check.
    Lufthansa FY27 (decided 29 Sep 2026): h is a RANGE, computed at both ends:
      lower 29% (AR 2025 p.90, "stale - as of Dec 2025", L1) and upper 50% (CFO remark "a bit
      more than 50%", Aug 2026, Reuters - "reported remark, not printed", L4, upper end only).
      The one-line answer names a FY27 ranking only if it holds at BOTH ends; otherwise it says
      "the FY27 ranking depends on Lufthansa's current hedge cover".
  All assumptions and derived values: ASSUMPTIONS.md (IDs A1, A2, ...).
  g     = share of the jet crack move that a gasoil hedge offsets (assumption, default 0.8,
          sensitivity shown 0.6-1.0; jet crack and gasoil crack are correlated but not identical)

Financials (printed)
  X      = USD per EUR rate (live ECB; company's own planning rate shown for reference)
  r      = recapture rate (printed; range: printed value and 0%)
  t      = MARGINAL tax rate (decided 29 Sep 2026): the rate the company itself prints as the
           expected/applicable/standard rate in its tax reconciliation note; if no group rate is
           printed, the statutory rate of its home country, labelled. Reason: we calculate the
           effect of a cost change, not the reported tax charge. The reported effective rate is
           shown alongside as context (e.g. AF-KLM 6.6%, depressed by a one-off deferred-tax release).
  m      = share of net income attributable to minorities = non-controlling interests / net
           income for the period, last full year (derived from printed figures; 0 if immaterial,
           labelled)
  N      = diluted weighted average shares (printed)
  EBIT_G = guided operating profit (where printed) ; EPS_G = guidance-implied EPS (section 6)

---------------------------------------------------------------------------------------------
## 2b. Hedging primer - what each hedge datapoint means and how we use it
---------------------------------------------------------------------------------------------
Hedge ratio (% of expected fuel volume hedged, per period)
  -> Drives sensitivity: for swaps, only the UNHEDGED share feels a further price move. (sec. 3)
Instrument / underlying (Brent crude, gasoil, jet fuel)
  -> Drives hedge QUALITY: a crude hedge does not protect against the jet crack. (sec. 3)
Instrument type (swaps/forwards vs options: calls/caps, collars)
  -> Swaps lock a price both ways. Options only protect above the strike (and a collar also gives
     up savings below a floor). Protection is non-linear. v1 treats all as swaps (labelled);
     if the mix is printed, show it and flag the limitation.
Hedged price / price after hedge (e.g. LH FY26 USD 1,036/t; AF-KLM hedged vs market per quarter)
  -> Does NOT change the sensitivity to a further move (for swaps), but sets the COST LEVEL:
     who locked in cheaper fuel has a competitive cost advantage. Used for:
     (a) context table (locked-in cost position), (b) deriving volume where not printed
     (fuel bill / price after hedge), (c) reconciliation check: volume x price after hedge
     ~ printed fuel bill (report the gap).
Hedge result / hedging gain (e.g. AF-KLM FY26 USD 1.6bn; IAG H1 EUR 769m)
  -> How much the hedges saved vs market. Context and a cross-check, not a model input.
Hedge horizon and policy (e.g. rolling 2-3 years, target % per quarter ahead)
  -> Explains why next year's cover is lower and how it will likely build up. Context only.
Mark-to-market / hedge reserve (derivative value in equity, OCI)
  -> Balance-sheet effect when prices move (section 7, P4).

Worked intuition (hypothetical): need 100 t; 80 t swapped at USD 1,000; market USD 1,200.
  Average cost = 0.8 x 1,000 + 0.2 x 1,200 = USD 1,040/t.
  Market rises to 1,300: average = 0.8 x 1,000 + 0.2 x 1,300 = USD 1,060/t (+20 = 20% x 100).
  -> The move only hits the unhedged 20%; the swap price (1,000) sets the level, not the change.
  If the 80 t were Brent swaps instead, a crack-driven jump would hit all 100 t.

---------------------------------------------------------------------------------------------
## 3. Layer 1 + 2: fuel cost change after hedge quality
---------------------------------------------------------------------------------------------
Unprotected share against each price component:
  u_B = 1 - hB - hG - hJ                  (Brent move: all three instrument types protect)
  u_C = 1 - g*hG - hJ                     (crack move: Brent hedges do NOT protect;
                                           gasoil hedges partly; jet swaps fully)

Fuel cost change in USD for period p:
  dFuel_USD_p = V_p * ( u_B * dB + u_C * dC )

In EUR:
  dFuel_EUR_p = dFuel_USD_p / X

Why this matters: in this crisis the jet crack moved far more than Brent. An airline reporting
"80% hedged" in Brent is ~0% protected against the crack. This is the key analytical point.

Undisclosed instrument mix (decided 29 Sep 2026 - AF-KLM and IAG; only Lufthansa prints its mix):
  Hedge quality is shown as a RANGE, never as jet-equivalent by default (that would make the one
  airline that discloses more look worse):
    upper = jet-equivalent: hJ = h, hB = hG = 0  -> u_C = 1 - h      (full crack protection)
    lower = crude-only:     hB = h, hG = hJ = 0  -> u_C = 1          (no crack protection)
    central = midpoint of the two dFuel results (status "assumption")
  u_B = 1 - h in all three cases (every instrument protects against a Brent move), so the range
  only affects the crack component: dFuel range = V * h * dC (per period).
  Printed qualitative wording is shown as context (AF-KLM Q1 2026 release p.6: Brent ICE, Gasoil
  ICE and Jet CIF NWE components; IAG: greater proportion of jet derivatives near term, Brent and
  gasoil further out). The page states: "Only Lufthansa discloses its hedge instrument mix."
  Lufthansa FY27 mix: same gasoil/Brent split as FY26 (48/81, 33/81), status "assumption",
  reason AR 2025 p.90: "mainly in gas oil and crude oil with option combinations".

Lufthansa option effect (decided 30 Sep 2026, after validation T2): central case = swap model for
all three (identical method); Lufthansa FY2026 also gets a "company table" case using the
exposures implied by its own slide 17 table next to the centre (ASSUMPTIONS.md A24). Robustness
rule applies across this range too. FY2027 not adjusted (table covers FY2026 only).

Options/collars: treated as swaps (linear) - labelled limitation; caps give less protection
on the downside and full protection above the strike, not modelled in v1.

---------------------------------------------------------------------------------------------
## 4. Time split for FY2026 versus baseline (P1: remaining months; P2: + realised part)
---------------------------------------------------------------------------------------------
Company fuel guidance was priced on the 27 Jul 2026 curve. Since then:
  (a) REALISED part (Aug - today): fuel already bought at actual prices.
      dFuel_realised = sum over elapsed months of V_month * (u_B*dB_month + u_C*dC_month)
      where dB_month, dC_month = actual monthly average minus baseline.
  (b) REMAINING part (today - 31 Dec): priced at today's level vs baseline.
  FY26 variance vs baseline = (a) + (b).
Baseline price (decided 29 Sep 2026): our own spot series on 27 Jul 2026 for ALL three
airlines (flat-curve assumption, labelled), so the move is measured identically for everyone.
Printed curve assumptions (Lufthansa: average 2026 Brent future 84 USD/bbl and jet crack
future 64 USD/bbl as of the reporting date; Air France-KLM where printed) are shown as
context and used in validation (section 9), NOT as the baseline. Any crack or Brent printed in
USD/bbl is converted to USD/t with the single stated factor from section 2.
Quarterly volume (decided 30 Sep 2026, extended 1 Oct 2026): printed quarterly volume where available (LH prints
Q3 2.68m t, FY 9.42m t). Where the company prints quarterly capacity (ASK) but not fuel, Q3 and Q4 are the FY volume
times each quarter's share of FY capacity, assuming the same fuel per seat-km in every quarter (status "derived"):
AF-KLM only (Q3 2.37m t, Q4 2.15m t; function h2_quarter_shares, inputs and formula quoted in the twins file). Every
other quarter = FY volume / 4 (equal quarters, status "assumption"): LH Q4 (a capacity cross-check gives 2.36m t vs
2.355m t, no material difference) and IAG (only FY25 and Q4 2025 group ASK are in the saved documents; its printed
Q4 2025 share is 24.4% vs 25%, so the equal split overstates Q4 by about 2%).
Remaining part of a quarter = remaining days after the as-of date / days in the quarter; the
remaining hedge ratio is volume-weighted over the remaining quarters. At 30 Sep 2026 the P1
"remaining" period is Q4 only (Aug-Sep is the realised part, P2).

FY2027: volume = FY26 volume (assumption, labelled) unless guided; hedge ratios = printed
2027 cover; baseline = 27 Jul level; move = current level (parallel shift assumption).
Forward curves are not freely available; using spot moves as a parallel shift of the curve is
a stated limitation (v2: licensed forward curve).


---------------------------------------------------------------------------------------------
## 5. Income statement: EBIT -> net income -> EPS
---------------------------------------------------------------------------------------------
  dRevenue_p  = r * dFuel_EUR_p                 (recapture via fares/surcharges; lagged in
                                                 reality - v1 assumes same period, labelled;
                                                 assumed symmetric when prices fall)
  dEBIT_p     = -dFuel_EUR_p + dRevenue_p
              = -(1 - r) * dFuel_EUR_p
  dEBT_p      = dEBIT_p   (+ second-order interest on lower cash: ignored, labelled)
  dNI_p       = dEBT_p * (1 - t) * (1 - m)
  dEPS_p      = dNI_p / N

Notes:
- Hedge accounting (IFRS 9 cash flow hedges): effective hedge gains/losses sit in equity (OCI)
  and are recycled into fuel cost when the fuel is consumed. Our "after hedge" cost already
  reflects that. Hedge ineffectiveness (e.g. crude hedges vs jet exposure) can hit the P&L
  outside adjusted EBIT - flagged, not modelled.
- ETS/SAF costs are not driven by the jet price move - excluded from dFuel.
- Adjusted vs reported: we work on each company's adjusted operating profit definition.

---------------------------------------------------------------------------------------------
## 6. EPS versus baseline: favourable / unfavourable
---------------------------------------------------------------------------------------------
Only some companies guide profit, and none guides EPS directly. So:

EPS baseline hierarchy (changed 29 Sep 2026):
  1. PRIMARY - third-party consensus EPS (source level 4, decided explicitly - see CLAUDE.md
     source hierarchy). ONE provider for all three airlines (proposed: MarketScreener, pending
     approval), FY26 and FY27, snapshots taken the same day and saved as dated PDFs in
     sources/third-party/ with URL. Record: statistic (mean/median), number of analysts, currency
     and unit (EUR vs euro cents), adjusted vs reported EPS. Status "third-party".
     Why: none of the company-compiled consensus sources gives EPS for all three (LH poll: no
     net income/EPS; IAG page: average only, FY26 only; AF-KLM page: to check).
  2. CROSS-CHECK - company-compiled consensus (source level 2: LH poll PDF; AF-KLM and IAG
     consensus pages as dated PDF snapshots). Compare like with like (e.g. LH poll median Adj.
     EBIT vs provider EBIT) and report any gap > 10% (threshold confirmed 29 Sep 2026; shown on page). Not the baseline.
  3. CONTEXT - company guidance where printed (LH Adj. EBIT EUR 1.7-2.2bn; IAG margin 12-15%):
     shown as a range on screen, and "position within guidance range" is still calculated.
  4. FALLBACK - where the provider shows no figure: last full-year actual EPS (printed, level 1),
     labelled "not consensus".

Headline measures: dEPS in EUR/share (needs no baseline), dEPS as % of consensus EPS (primary %),
and dEBIT as % of adjusted EBIT (secondary; uses the profit reference, section 6 flag below).

Timing caveat (show on screen): the baseline date is 27 Jul 2026, but a third-party consensus
snapshot taken later may already partly reflect fuel moves after 27 Jul (and company polls taken
before 27 Jul miss part of the move). The snapshot date is shown next to the baseline; the
variance is always computed from the 27 Jul price baseline regardless.

Guidance-implied EPS (context only, LH): (EBIT_G - net financial result - adjustments)
  x (1 - t) x (1 - m) / N, using last printed run-rates, labelled.

Outputs per airline:
  dEPS (EUR/share)            - robust: needs no baseline level
  dEPS % of baseline EPS      - needs baseline (above)
  Position in guidance range  - e.g. "live move shifts LH from mid-point to lower half"
                                 (dEBIT vs the EUR 1.7-2.2bn range); IAG: margin impact in pp =
                                 dEBIT / consensus FY26 revenue (MarketScreener, level 4,
                                 decided 30 Sep 2026), positioned in the 12-15% range from its
                                 midpoint
  Fuel bill vs guided bill    - LH EUR 8.66bn, AF-KLM USD 8.9bn, IAG EUR 8.6bn (all on the 27 Jul
                                curve; AF-KLM curve date confirmed, Q2 release p.1 fn 3)
  Flag: FAVOURABLE if dEPS > 0, UNFAVOURABLE if < 0; MATERIAL if |dEBIT| ≥ 5% of the
        profit reference or |dEPS %| ≥ 5%.
        Profit reference = last full-year actual adjusted operating profit (each company's
        own adjusted definition), for all three airlines.

Competitive gap (sign fixed 30 Sep 2026): our dEPS % - peer dEPS % (positive = peer hurt MORE
than us). Example: us -5%, peer -3% -> -2 pp (we are hurt more). Plus the driver that explains
most of the gap (from section 8).

---------------------------------------------------------------------------------------------
### 6b. Story headline yardstick (decision 30 Sep 2026; ASSUMPTIONS.md A25-A29)
The redesigned page leads with X = operating-profit loss from a USD 100/t jet move (+40 Brent/+60 crack, A28) as
% of the operating profit EXPECTED for the same year - never a past year. Yardstick hierarchy per airline and year:
company's printed projection (amount: midpoint, range kept; margin: x revenue from the same hierarchy) -> one
provider's consensus EBIT for all three (MarketScreener, same snapshot as EPS; EBIT basis checked against each
company's adjusted operating profit; LH cross-checked vs its own poll, 10% rule) -> last actual, labelled.
Robustness: hedge cover x hedge mix x Brent/crack split x recapture (50% to printed, A25) x guidance range; "hit
hardest in every case" only if it holds in every combination, otherwise the headline names what it depends on.
Attribution of the gap: Shapley values over hedge ratio, hedge quality, recapture, profit base (A29).
The v1 materiality flag above (last actual as profit reference) is unchanged until the v1 table is replaced (D9).
Code: src/story/yardstick.py, src/story/robustness.py.

### 6c. Benchmark split from price data (decision 1 Oct 2026, lookback changed 2 Oct 2026; ASSUMPTIONS.md A28)
The USD 100/t scenario is split into crude and jet premium by the median crude share of large jet fuel moves in the
5 years BEFORE the baseline day (27 Jul 2026) - 5 years is the longest window used anywhere on the page: FRED jet and
Brent in USD/t, 5-trading-day average, moves of >= USD 75/t within 60 days found by a chronological non-overlapping
scan, crude share = Brent move / jet move, median (interquartile range shown). Moves after 27 July are the current
shock: compared with the benchmark (the Step 2 chart marks today's split), never part of it. Lookback sensitivity
2 / 3 / 5 years on the Method & sources page (fewer than 8 moves -> neutral 50/50, labelled). Co-movement of crude
and premium (correlation, variance shares by horizon) shown for 5 and 2 years. The ranking is also checked for
every split from all-crude to all-premium (answer toggle). Code: src/story/price_split.py.

## 7. Cash flow and balance sheet (simplified) - P4
---------------------------------------------------------------------------------------------
Cash flow:
  dCFO_p ~ dNI_p (fuel paid in cash within the period; tax paid in period - labelled)
  Working-capital timing (fuel payables, advance ticket sales) - noted, not modelled.
  Capex unchanged (management may cut capex - LH already lowered net capex guidance; shown as
  context, not modelled).
  dFCF_p = dCFO_p
Balance sheet:
  dNetDebt   = -dFCF
  dLeverage  = (NetDebt + dNetDebt) / (EBITDA + dEBIT) - NetDebt / EBITDA
               (using each company's printed leverage definition; LH: net debt incl. 50%
               hybrid equity credit / adj. EBITDA; AF-KLM: net debt / EBITDA)
  Hedge reserve (equity, OCI): mark-to-market on hedges for future periods rises when prices
  rise: dMTM ~ remaining hedged volume x covered price move / X. Shown as indicative:
  equity goes UP via OCI while net income goes DOWN - a useful nuance to explain.
  Liquidity headroom vs printed target (LH target EUR 8-10bn) - context.

---------------------------------------------------------------------------------------------
## 8. Decomposition: why airlines differ (Q3) - P1: one-sentence main driver; P4: full waterfall
---------------------------------------------------------------------------------------------
For each airline, dEPS % is attributed step by step (waterfall), changing one factor at a time
from LUFTHANSA's value to the peer's value (decided 30 Sep 2026: the reference is "us"), so each
bar explains part of the peer's gap to Lufthansa:
  hedge ratio -> hedge quality (instrument mix) -> recapture -> profit cushion (volume, shares and
  baseline EPS together = exposure relative to earnings) -> tax and minorities
The waterfall is order-dependent (a stated limitation); the order above is fixed.
Robustness rule (decided 29 Sep 2026): a driver or ranking is named in the one-line answer only if
it holds across the full range of every uncertain input that feeds it:
  - hedge quality: across the peers' jet-equivalent-to-crude-only range (section 3); otherwise the
    answer says the comparison "depends on undisclosed instrument mixes";
  - FY27 ranking: across Lufthansa's FY27 hedge range 29%-50% (section 2); otherwise it says the
    FY27 ranking "depends on Lufthansa's current hedge cover".
The largest bar is named in the one-line answer, e.g.
  "IAG's larger FY27 hit is mainly lower hedge cover; LH's is hedge quality (crude-based)."

---------------------------------------------------------------------------------------------
## 9. Validation
---------------------------------------------------------------------------------------------
Numbering: 02_SPEC.md "Trust layer" is the master list. Items below give the spec number [T#].
0. [T9] Fuel bill reconciliation per airline: volume x price after hedge vs printed fuel bill
   (P2; report the gap; explains definition differences such as emissions and SAF costs).
1. [T2] Reproduce Lufthansa's own sensitivity table (Q2 charts, slide 17: jet rate after hedge by
   Brent x crack) with layers 1-2. Report the error per cell. Calibrate g only if explained.
2. [T3] AF-KLM: fuel bill USD 9.3bn (24 Apr curve) -> USD 8.9bn: predict the change from the price
   move between curve dates; report predicted vs printed.
3. [T4] Reconciliation: dNI and dEPS recomputed independently in a test from printed inputs.
4. [unit tests, P1] Sign and unit tests: price up -> EBIT down; recapture 100% -> dEBIT 0; USD/EUR conversion.
Do NOT tune to fit. Report gaps and explain them.

---------------------------------------------------------------------------------------------
## 10. Illustrative walk-through (hypothetical numbers - NOT real data)
---------------------------------------------------------------------------------------------
Airline X, rest of year: V = 2.0m t; hB 30%, hG 40%, hJ 10%; g = 0.8
Move: dB = +40 USD/t, dC = +60 USD/t (dJ = +100)
  u_B = 1 - 0.3 - 0.4 - 0.1 = 0.20
  u_C = 1 - 0.8*0.4 - 0.1   = 0.58
  dFuel_USD = 2.0m * (0.20*40 + 0.58*60) = 2.0m * 42.8 = USD 85.6m
  X = 1.15 -> dFuel_EUR = EUR 74.4m
  Note: the "reported" hedge ratio is 80%, but the effective protection against this move
  is only 57% (42.8 of 100 USD/t unprotected).
  r = 60% -> dEBIT = -0.4 * 74.4 = EUR -29.8m
  t = 25%, m = 0 -> dNI = EUR -22.3m
  N = 1,200m shares -> dEPS = EUR -0.019 ; vs baseline EPS 1.00 -> -1.9% -> unfavourable,
  not material (below the ≥ 5% threshold).

---------------------------------------------------------------------------------------------
## 11. Extra inputs to extract (printed) - verified by hand first (Prompt 2); automated in P5
---------------------------------------------------------------------------------------------
Per airline: hedge instrument TYPE (swaps vs options/collars) and strike levels if printed;
hedge result by period; latest company-compiled consensus poll (date, median/mean, number of estimates,
fields incl. net income/EPS) - or "not published"; hedge instrument mix by period; hedged
price after hedge by period; volumes by period (or inputs to derive them); effective tax
rate; minorities' share of net income; diluted weighted average shares; net financial result
(latest run-rate); adjustments guidance if any; last full-year EPS; net debt, EBITDA and the
company's leverage definition; liquidity and target; any printed curve assumptions (Brent,
crack, USD/EUR); FX hedge cover on fuel where printed.

---------------------------------------------------------------------------------------------
## 12. Limitations to state on screen
---------------------------------------------------------------------------------------------
Spot moves used as parallel curve shifts; US Gulf Coast jet as price proxy; options treated as
swaps; recapture assumed contemporaneous and at the printed rate (range shown); volumes held
constant (no capacity response); second-order interest and working-capital effects ignored;
FY27 volumes assumed equal to FY26.
Lufthansa hedge split: slide 17 footnote 2 says "remaining FY 2026" but its total (81%) equals the
FY column, not the YTG 82%; we apply the split to 82% and show 85% as a sensitivity.
IAG FY27 hedge ratio is an equal-weight average of printed quarters (no weights printed).
Recapture rates are not like-for-like (LH: Q2 Network Airlines bridge; AF-KLM: Q2 actual,
revenue only; IAG: FY expectation incl. cost initiatives) - shown with the 0%-printed range.
EPS baseline is third-party consensus (level 4): provider methodology not ours; snapshot may
include fuel moves after 27 Jul 2026. Lufthansa hedges use option combinations (AR 2025 p.90),
treated as swaps.

---------------------------------------------------------------------------------------------
## 13. Confidence label per airline (P2) - rule shown on the page
---------------------------------------------------------------------------------------------
Counts only the inputs actually used in that airline's EPS chain for the period shown
(sections 3-6: volume, hedge ratios and mix, g, recapture, tax, minorities, shares, FX,
baseline EPS).
  confidence share = inputs with status "verified" / all inputs used
  "assumption", "derived", "third-party" and "found" inputs all count as not verified.
  Label: HIGH if share ≥ 80%, MEDIUM if 50% to < 80%, LOW if < 50%  (thresholds accepted
  29 Sep 2026). The page shows the share, the label, and the list of non-verified inputs.
It measures how well-sourced the inputs are, not how right the model is.

