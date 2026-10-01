# Data register - company-disclosed figures (researched 29 Sep 2026)

Scope: Lufthansa Group (us), Air France-KLM, IAG.

RULE (changed 29 Sep 2026): SOURCE HIERARCHY - use the highest available level and record it:
  L1 company's own printed documents (always preferred) | L2 company-compiled consensus on own IR
  site (dated PDF snapshot) | L3 other official sources (exchange/regulator, ESEF, central banks) |
  L4 reputable third party (only if L1-3 empty, or decided explicitly; agent asks first) |
  L5 labelled assumption. Figures exactly as printed, with document/URL + page + verbatim quote.
  L3-4: URL, access date, dated snapshot in sources/third-party/, status "third-party".
  Level is L1 for every row below unless stated otherwise.

Status vocabulary (same as 02_SPEC.md):
  verified = I checked it on the PDF page | found = seen in the company's own document, not yet
  checked by me | not-disclosed | assumption | derived | third-party (L3-4) | to-extract = not yet looked for.
Everything below marked "found" still needs my check against the PDF.

## PRIORITY CHECKS (do these first - they decide how strong the headline can be)
1. FY2027 hedge ratios PRINTED for Lufthansa and IAG? (AF-KLM prints 40%.) IAG: ANSWERED - quarterly
   2027 ratios on H1 presentation slide 30 (FY27 derived, see IAG table). LH: still to check in the 2nd
   interim report. If LH not printed: FY27 comparison is partial - lead with FY26.
2. Hedge instrument mix for IAG and the % mix for AF-KLM (LH prints it; AF-KLM names instruments but no %).
3. Jet fuel volumes for IAG (AF-KLM derivable from slide 16).
4. Company-compiled consensus polls: latest for all three.
5. Lufthansa hedge ratio definitions (81% FY vs 82% Q3 vs "YTG 85%"). DECIDED 29 Sep 2026 - see LH
   "Hedge instrument mix" row.
6. For all three: hedge instrument TYPE (swaps vs options/collars), price after hedge per period,
   hedge result - see 06_METHODOLOGY.md section 2b for why each matters.

## Source documents to download into sources/
| Airline | Document | Date | URL |
|---|---|---|---|
| Lufthansa | Q2 2026 results charts | 04 Aug 2026 | https://investor-relations.lufthansagroup.com/fileadmin/downloads/en/charts-speeches/LH-QR-2026-2-charts.pdf |
| Lufthansa | 2nd Interim Report Jan-Jun 2026 | Aug 2026 | https://investor-relations.lufthansagroup.com/fileadmin/downloads/en/financial-reports/interims-reports/LH-QR-2026-2-e.pdf |
| Lufthansa | Analyst consensus poll Q2 2026 (downloaded: sources/lufthansa/2026-Q2/) | 16 Jul 2026 | https://investor-relations.lufthansagroup.com/fileadmin/downloads/en/financial-reports/consensus/LHG-Consensus-Q2-2026.pdf |
| Lufthansa | Annual report 2025 (tax rate, shares, EPS, minorities) (downloaded: sources/lufthansa/2025-FY/) | 2026 | https://investor-relations.lufthansagroup.com/fileadmin/downloads/en/financial-reports/annual-reports/LH-AR-2025-e.pdf |
| Air France-KLM | Q2 2026 press release | 30 Jul 2026 | https://www.airfranceklm.com/sites/default/files/2026-07/20260729-2026-q2-afklm-press-release-1.pdf |
| Air France-KLM | Q2 2026 results presentation | 30 Jul 2026 | https://www.airfranceklm.com/sites/default/files/2026-07/q2_2026-afklm-results-presentation.pdf |
| Air France-KLM | Q1 2026 results presentation (backtest) | Apr 2026 | https://www.airfranceklm.com/sites/default/files/2026-04/afklm_q1_2026_results-presentation.pdf |
| Air France-KLM | Q1 2026 press release (hedge instruments) - downloaded by you: sources/afklm/2026-Q1/q1-2026-afklm-press-release.pdf | Apr 2026 | https://www.airfranceklm.com/sites/default/files/2026-04/q1-2026-afklm-press-release.pdf |
| Air France-KLM | FY2025 results press release - downloaded by you: sources/afklm/2025-FY/afklm_full_year_2025_press_release_english.pdf | 19 Feb 2026 | https://www.airfranceklm.com/sites/default/files/2026-02/afklm_full_year_2025_press_release_english.pdf |
| Air France-KLM | Universal Registration Document 2025 (tax, shares, EPS) - downloaded by you: sources/afklm/2025-FY/urd-2025-veng.pdf (536 pages); direct PDF URL not recorded - please add | 2026 | https://www.airfranceklm.com/en/finance/publications/latest-annual-semi-annual-documents |
| Air France-KLM | H1 2026 financial statements and notes - skipped (URD covers FY25 shares, EPS, tax) | Jul 2026 | - |
| Air France-KLM | Consensus - web page; not saved (optional - cross-check only) | collected 7-14 Jul 2026 (search snippet, to check) | https://www.airfranceklm.com/en/finance/investors-and-analysts/consensus |
| IAG | H1 2026 results press release | 31 Jul 2026 | https://www.iairgroup.com/press-releases/2026/iag-half-year-results-2026/ |
| IAG | H1 2026 results presentation | 31 Jul 2026 | https://www.iairgroup.com/media/pwslnxy2/iag-results-presentation-q2-2026.pdf |
| IAG | H1 2026 results call TRANSCRIPT (company-published PDF - counts as printed) (downloaded: sources/iag/2026-H1/) | 31 Jul 2026 | https://www.iairgroup.com/media/ymmjb2dv/iag-h1-2026-results-call-transcript.pdf |
| IAG | FY2025 results release (downloaded: sources/iag/2025-FY/) | Feb 2026 | https://www.iairgroup.com/media/wd4dsjef/full-year-results-release-for-the-year-to-31-december-2025.pdf |
| IAG | Annual Report and Accounts 2025 (downloaded: sources/iag/2025-FY/) | 2026 | https://www.iairgroup.com/media/ktnlp1jx/iag-annual-report-and-accounts-2025.pdf |
| IAG | Consensus - web page with charts; not saved (optional - cross-check only) | updated 24 Jul 2026; collected 6-13 Jul 2026 | https://www.iairgroup.com/investors-and-shareholders/analysts-consensus/ |

## Lufthansa Group (us)
| Field | Value as printed | Where | Status |
|---|---|---|---|
| FY26 expected total fuel expense | EUR 8.66bn (fossil 8.46 + mandatory SAF 0.20); 27 Jul 2026 curve; 1.151 USD/EUR | Q2 charts, slide 17 | found |
| Jet fuel volume | FY26 9.42m t; Q3'26 2.68m t | Q2 charts, slide 17 | found |
| Air France-KLM Group capacity (ASK m) | Q1-26 78,565 (+4.0%); Q2-26 86,993 (+2.6%), H1 165,558 (+3.3%); Q4-25 83,962; FY25 336,521; FY26 guided +2% to +3% | Q1 and Q2 2026 press releases p.3, FY2025 press release p.3, Q2 presentation slide 19 | found; used only to derive AF-KLM Q3/Q4 2026 fuel volume (A11) |
| Hedge ratio | FY26 81%; Q3'26 (YTG) 82% as of 27 Jul; slide 18 text "YTG 85% hedged". Table cells (slide 17, "as of July 27, 2026"): "Hedge ratio [%] - YTG only 82%" (Q3 '26), "81%" (FY 2026). Slide 18: "YTG 85% hedged with majority in refined products" | Q2 charts, slides 17-18 | found - model uses YTG 82% (decision 29 Sep 2026); 85% shown as sensitivity |
| Hedge instrument mix (printed) | Footnote 2 verbatim: "Hegde ratio for remaining FY 2026 comprises 48% hedge on gasoil and 33% hedge on Brent." (typo as printed; sums to 81%) | Q2 charts, slide 17 footnote 2 | found |
| hG, hB used in model (rest of FY26) | Footnote 2 read as the instrument SPLIT of the hedge book (gasoil 48/81, Brent 33/81), applied to the YTG ratio 82%: hG = 0.82 x 48/81 = 48.6%; hB = 0.82 x 33/81 = 33.4%; hJ = 0. Sensitivity at 85% (slide 18): hG = 0.85 x 48/81 = 50.4%; hB = 0.85 x 33/81 = 34.6% | derived from slide 17 fn 2 + table, slide 18 | derived (formula above). LIMITATION: footnote says "remaining FY 2026" but its total (81%) equals the FY column, not the YTG 82% |
| Jet price after hedge | FY26 USD 1,036/t; Q3 USD 1,005/t | Q2 charts, slide 17 | found |
| Curve assumptions | Avg 2026 Brent future 84 USD/bbl; jet crack future 64 USD/bbl (reporting date). Fn 4: "Average 2026 Brent ICE Crude oil future in $/bbl as of reporting date: 84 $/bbl." Fn 5: "Average 2026 Jet Crack Future as of reporting date: 64 $/bbl." | Q2 charts, slide 17 footnotes 4-5 | found - context + validation only (baseline = our 27 Jul spot, decision 29 Sep 2026) |
| Sensitivity table | Jet rate after hedge by Brent (44-114 USD/bbl) x crack (44-84 USD/bbl) | Q2 charts, slide 17 | found - validation target |
| Hedge ratio FY27 - lower end (L1) | Printed only as of 31 Dec 2025: 29% (2027 hedges 2,948 thousand t). NOT printed as of 27 Jul 2026 in Q2 charts or 2nd interim report (searched 29 Sep 2026). Verbatim AR p.90: "Around 29% of the forecast fuel requirement for 2027 was hedged at that time." ("at that time" = "As of 31 December 2025"); AR p.331 T181: "Hedging instruments in 1,000 tonnes 7,446 2,948" (2026, 2027) | Annual report 2025 p.90, p.331 | found - lower end of RANGE, labelled "stale - as of Dec 2025" (decision 29 Sep 2026) |
| Hedge ratio FY27 - upper end (L4) | "a bit more than 50%" -> 50% used as upper end ONLY; label "reported remark, not printed" | Reuters article (29 Sep 2026) reprinted by The Star, credited "- Reuters"; snapshot sources/third-party/2026-09-29_reuters-via-thestar_lufthansa-fuel-hedge-2027.pdf; URL https://www.thestar.com.my/business/business-news/2026/09/29/lufthansa-ceo-says-jet-fuel-hit-to-top-15-billion-forecast (reuters.com not reachable by our tools); accessed 29 Sep 2026 | third-party. Verbatim: "Lufthansa Chief Financial Officer Till Streichert told analysts in August the group's fuel hedge ratio for 2026 was 86% and a bit more than 50% in 2027." |
| Hedge policy and instrument type | Rules-based, up to 24 months, target 85% (Passenger Airlines, 31 Dec 2025); mainly gas oil and crude oil with OPTION combinations. Verbatim AR p.90: "The Lufthansa Group uses rules-based fuel hedging with a time horizon of up to 24 months. The target hedging level for fuel hedging was 85% as of 31 December 2025 for the Passenger Airlines."; "Hedges are mainly in gas oil and crude oil with option combinations for reasons of market liquidity." | Annual report 2025 p.90 | found |
| Hedge ratio current year (interim report) | "around 86% of the volume of kerosene required for the current year is already covered by fuel hedging through derivatives on various oil products" - a fourth figure next to 81/82/85% | 2nd interim report p.29 | found - context only |
| Recapture rate | ~60% (Q2 Network Airlines bridge) | Q2 charts, slide 13 | found |
| Adj. EBIT guidance FY26 | EUR 1.7 - 2.2bn | Q2 charts, slide 20 | found |
| Adj. EBIT FY25 | EUR 1,960m | Q2 charts, slide 30 | found |
| Extra fuel cost vs PY | EUR 1.5bn (27 Jul curve) | Q2 charts, slide 17 | found |
| Leverage definition | Net debt incl. 50% hybrid equity credit / adj. EBITDA; 2.0x at 30 Jun 2026 | Q2 charts, slide 16 | found |
| Liquidity target | EUR 8 - 10bn | Q2 charts, slide 16 | found |
| Tax rate (marginal, model input) | Expected tax rate 25% (group parent tax group: 15.825% corporation tax/solidarity + 9.175% trade tax). Reported effective rate FY25 29% (context: deferred-tax revaluation from the resolved future German corporation tax cut) | Annual report 2025 p.282 (T109), p.44 | found. Verbatim p.282: "The expected tax expense is calculated by multiplying profit before income taxes by a tax rate of 25% (previous year: 25%)."; p.44: "At 29%, the effective tax ratio for continuing operations was above the expected tax rate of 25%." |
| Minorities FY25 | Non-controlling interests EUR 24m of profit after income taxes EUR 1,363m -> m = 24 / 1,363 = 1.8% | Annual report 2025 p.257 | derived. Verbatim: "Profit/loss after income taxes 1,363 1,393"; "Profit/loss attributable to non-controlling interests 24 13" |
| EPS FY25 | EUR 1.12 (basic = diluted) | Annual report 2025 p.257 | found. Verbatim: "“Basic”/“diluted” earnings per share in € 16 1.12 1.15" |
| Diluted shares | - | Annual report 2025 note 16 | to-extract (Prompt 2) |

## Air France-KLM
Documents: R = Q2 2026 press release (sources/afklm/2026-Q2/20260729-2026-q2-afklm-press-release-1 (1).pdf);
P2 = Q2 2026 results presentation; P1 = Q1 2026 results presentation. Checked by the agent against
the PDF text on 29 Sep 2026 (text extraction); status stays "found" until you verify.
Slide 16 / slide 14 column order as extracted: FY 2025 | Q1 2026 | Q2 2026 | Q3 2026 | Q4 2026 | FY 2026.

| Field | Value as printed | Where | Verbatim quote / table cells | Status |
|---|---|---|---|---|
| FY26 fuel bill after hedge excl. SAF | ~USD 8,900m (27 Jul curve); prev. ~USD 9,300m (24 Apr curve); FY25 USD 6,900m | P2 slide 16; P1 slide 14; R p.1 + fn 3 | P2 s.16: "Fuel bill after hedge excl SAF ($m) 6,900 ~8,900"; R p.1: "Fuel bill is expected at USD 8.9bn 3 in FY 2026, compared to previous quarter indication of USD 9.3bn³. The current expected fuel bill reflects an increase of USD 2.0bn" | found |
| Curve date | 27 July 2026 - CONFIRMED | R p.1 fn 3; R p.7 fn 1; P2 slide 16 | R p.1 fn 3: "Based on the current hedges and forward curve of 27 July and subject to change given geopolitical uncertainty"; P2 s.16: "Based on forward curve on 27th July 2026. Jet fuel price including into plane cost, excluding SAF premium." | found |
| Hedge ratio by quarter (27 Jul) | Q1 71%, Q2 71%, Q3 66%, Q4 61%, FY26 67%; FY25 69% | P2 slide 16 | "% of consumption already hedged 69% 71% 71% 66% 61% 67%" | found |
| Hedge ratio FY27 | 40% (27 Jul); was 33% on 24 Apr curve | R p.7; P2 slide 16; P1 slide 14 | R p.7: "The percentage of fuel consumption already hedged for 2026 is 67% and 40% for 2027."; P2 s.16: "FY 2027 40% hedged"; P1 s.14: "FY 2027 33% hedged" | found |
| Jet price after hedge (USD/t) | Q1 773, Q2 1,209, Q3 1,039, Q4 1,053, FY26 1,024; FY25 808 | P2 slide 16 | "Price after hedge ... Jet fuel ($ per metric ton) 808 773 1,209 1,039 1,053 1,024" | found |
| Market price assumptions (27 Jul) | Brent Q3 84 / Q4 81 / FY26 85 USD/bbl; jet Q3 1,243 / Q4 1,212 / FY26 1,205 USD/t | P2 slide 16 | "Brent ($ per bbl) 68 78 97 84 81 85"; "Jet fuel ($ per metric ton) 792 866 1,470 1,243 1,212 1,205" | found - context + validation only (baseline = our 27 Jul spot) |
| Hedge result (USD m) | Q1 186, Q2 565, Q3 478, Q4 343, FY26 1,572; FY25 -138 | P2 slide 16; R p.7 | "Hedge result (in $ m) -138 186 565 478 343 1,572"; R p.7: "the full year 2026 hedging result amounts to USD 1.6bn" | found |
| Backtest table (24 Apr curve) | FY bill ~9,300; hedge Q3 65% / Q4 60% / FY 66%; after hedge Q3 1,147 / Q4 1,032 / FY 1,061; market jet Q3 1,328 / Q4 1,157 / FY 1,238; Brent Q3 88 / Q4 83 / FY 87 | P1 slide 14 | "Based on forward curve at 24th April 2026."; "Brent ($ per bbl) 68 78 98 88 83 87"; "Jet fuel ($ per metric ton) 792 864 1,559 1,328 1,157 1,238"; "Price after hedge 808 771 1,260 1,147 1,032 1,061"; "% of consumption already hedged 69% 71% 70% 65% 60% 66%"; "~9,300" | found - backtest input |
| Hedge instruments | Brent ICE, Gasoil ICE and Jet CIF NWE components (no % mix printed) | Q1 2026 press release p.6 | "The Group has a rolling fuel hedging policy in place, using Brent ICE, Gasoil ICE and Jet CIF NWE components." Also: "jet fuel prices rising significantly more sharply than those of gaso il and brent" | found (% mix not-disclosed at L1) -> hedge quality as RANGE jet-equivalent to crude-only (ASSUMPTIONS.md A5) |
| Volume FY26 | Not printed. Derived: USD 8,900m / USD 1,024/t = 8.69m t (~8.7m t). Note: 8,900 is printed as "~" (rounded) | derived from P2 slide 16 | - | derived (formula above) |
| Recapture rate | "circa 85%" (Q2): unit revenue +EUR 672m vs fuel price -EUR 804m incl. ETS EUR 26m | R p.1, p.4; P2 slide 8 | R p.1: "Fuel price recapture via revenues at circa 85%, above the estimated 60%."; R p.4: "an increase in unit revenue of €672 million which was fully offset by a fuel price increase of €804 million (including ETS €26 million)" | found |
| Profit guidance | None. Printed: capacity +2% to +3%, unit cost 0% to +2%, net capex below EUR 3bn, leverage 1.5x-2.0x | R p.1 (and p.7) | "Capacity up by +2% to +3% compared to 2025 (previously +2% to +4%)."; "Unit cost1 up between 0% and +2%, including +0.5% from premiumization (unchanged)."; "Net capital expenditures below €3bn (unchanged)."; "Leverage ratio between 1.5x - 2.0x (unchanged)." | not-disclosed (profit) |
| Adjusted operating profit FY25 | EUR 2,069m (after IFRS 18); EUR 2,004m before IFRS 18. USE 2,069 (same basis as 2026) | R p.15; P2 slide 23 | P2 s.23 "IMPLEMENTATION IFRS18 AS OF Q2 2026": "CURRENT OPERATING INCOME (BEFORE IFRS 18) ... 2,004"; "ADJUSTED OPERATING PROFIT (AFTER IFRS 18) ... 2,069" (column "Full Year 2025") | found |
| Net income H1 2026 | Group part EUR -133m; non-controlling interests EUR 72m | R p.17 | "Net income – Non-controlling interests 35 43 -19 % 37 44 -16 % 72 87 -17 %"; "Net income – Group part -286 -291 -2 % 153 605 -75 % -133 314 nm" (last pair = H1 2026 vs H1 2025) | found |
| Leverage | Net debt/Adjusted EBITDA 1.6x (30 Jun 2026); net debt EUR 8,376m; adj. EBITDA LTM EUR 5,204m | R p.3 | "Net Debt (€m) 8,376 8,392"; "Adjusted EBITDA trailing 12 months (€m) 5,204 5,058"; "Net Debt/Adjusted EBITDA ratio 1.6x 1.7x" | found |
| Currency split of costs | ~30% USD, ~70% other (mainly EUR), FY25 | P2 slide 27 | text extraction ambiguous (chart labels) - check the slide visually | found - check visually |
| Diluted shares FY25 | 280,566,634 (weighted average, diluted); basic 262,603,131 | URD 2025 p.408 (Note 14) | "Number of ordinary and potential ordinary shares used to calculate diluted earnings per share 280,566,634"; "Number of shares used to calculate basic earnings per share 262,603,131" | found |
| EPS FY25 | Basic EUR 5.83, diluted EUR 5.50 (Group part) | URD 2025 p.378, p.408 | "Earnings per share – Equity holders of Air France-KLM (in euros) • basic 14 5.83 ... • diluted 14 5.50"; p.408: "the basic earnings per share amounts to €5.83 and the diluted earnings per share amounts to €5.50." | found |
| Net income for EPS FY25 | Group part EUR 1,593m; less perpetual coupons EUR 61m = basic EUR 1,532m; diluted EUR 1,544m. Perpetual coupons are fixed, so they do not change with fuel | URD 2025 p.408 | "Net income for the period – Equity holders of Air France-KLM 1,593"; "Coupons on perpetual net after tax (61)"; "...taken for calculation of diluted earnings per share) 1,544" | found |
| Tax rate FY25 | Effective 6.6% (income tax EUR 123m on income before tax EUR 1,863m), depressed by a EUR 404m deferred tax release; statutory France 25.83% | URD 2025 p.406 (Note 13.3); FY25 release p.21 | "Effective tax rate 6.6% 14.2 %"; "Standard tax rate in France 25.83% 25.83%"; "Add / (Release) of deferred tax 404 94" | found - model uses statutory 25.83% (marginal, decision 29 Sep 2026); 6.6% shown as context (one-off deferred-tax release) |
| Minorities FY25 | Non-controlling interests EUR 161m of net income EUR 1,754m -> m = 161 / 1,754 = 9.2% | URD 2025 p.378; FY25 release p.21 | "Net income – Non-controlling interests 161 172"; "Net income for the period 1,754 489" | derived (formula above) - approved 29 Sep 2026 |

## IAG
| Field | Value as printed | Where | Status |
|---|---|---|---|
| FY26 fuel cost | EUR 8.3bn (30 Jun curve) to EUR 8.6bn (27 Jul curve), incl. emissions/sustainability costs | H1 press release | found |
| Hedge ratio by quarter (27 Jul curve) | Q3 2026 74%, Q4 2026 65%, Q1 2027 55%, Q2 2027 48%, Q3 2027 39%, Q4 2027 31% | H1 presentation slide 30 | found. Verbatim: title "Fuel hedging - c70% hedged for 2026"; header "As per 27/07/26 jet curve Q3 2026 Q4 2026 Q1 2027 Q2 2027 Q3 2027 Q4 2027"; row "Hedge ratio  74 %  65 %  55 %  48 %  39 %  31 %" (same ratios in the 30/06/26 block) |
| Jet price scenario and after-hedge price (27 Jul curve, USD/mt) | Scenario Q3 26 1,150, Q4 26 1,180, Q1 27 1,050, Q2 27 950, Q3 27 900, Q4 27 900; effective blended price post fuel and FX hedging 905, 975, 925, 915, 885, 885; USD/EUR scenario 1.143 | H1 presentation slide 30 | found. Verbatim: "Jet fuel price scenario $1,150/mt $1,180/mt $1,050/mt $950/mt $900/mt $900/mt"; "Effective blended price post fuel and FX hedging* $905/mt $975/mt $925/mt $915/mt $885/mt $885/mt"; "* Effective blended price excluding into plane cost" |
| Hedge ratio FY27 (model input) | 43.25% = simple average of Q1-Q4 2027 (55 + 48 + 39 + 31) / 4. IAG prints no quarterly 2027 capacity or fuel-volume weights, so equal weights | derived from H1 presentation slide 30 | derived (labelled; equal-weight assumption) |
| Hedge ratio 2026 / 2027 (call) | ~70% rest of 2026 / ~40% 2027 - printed CROSS-CHECK only; primary = derived 43.25% from slide 30 (decision 29 Sep 2026) | H1 call transcript p.4 | found. Verbatim: "Looking forward, we are around 70% heads for the remainder of 2026 and around 40% hedge for 2027." ("heads" as printed - transcript typo for "hedged") |
| Hedge instruments | Near term more jet derivatives; further out Brent and gasoil proxies; some options (no % mix) -> hedge quality as RANGE jet-equivalent to crude-only (ASSUMPTIONS.md A5) | H1 results announcement p.10 | found. Verbatim: "In the near-term, the Group hedges its anticipated jet fuel exposure using a greater proportion of jet fuel derivatives. Further out, the Group uses more liquid proxy instruments, primarily Brent crude oil and gasoil, with positions progressively transitioned into jet fuel hedges, where possible, as delivery approaches." Also: "the use of option structures for a proportion of the hedging undertaken" (% mix not-disclosed) |
| Hedging gains H1 | EUR 769m | H1 press release | found |
| Recapture rate | ~60% (H1 and FY expectation) | H1 press release | found |
| Profit guidance | Operating margin within 12-15% target range | H1 press release | found |
| H1 operating profit before exceptional items | EUR 1,757m (six months to 30 Jun 2026) - CONFIRMED by you 29 Sep 2026 | H1 results announcement p.1, p.2 | found. Verbatim p.1: "Operating profit before exceptional items of €1,757 million (H1 2025 €1,878 million)"; p.2 table "Six months to 30 June": "Operating profit before exceptional items  1,757  1,878 (6.4)%". Checked 29 Sep 2026: KEEP 1,757 (the EUR 1,406m is Q2, next row) |
| Q2 operating profit before exceptional items | EUR 1,406m (three months to 30 Jun 2026) | H1 results announcement p.1, p.2 | found. Verbatim p.1: "Operating profit before exceptional items decreased by 16.3% to €1,406 million mainly due to the impact of higher fuel costs"; p.2 table "Three months to 30 June": "1,406  1,680 (16.3)%" |
| Operating profit FY25 | EUR 5,024m (before exceptional items), margin 15.1% | IAG IR homepage 2025 KPIs + FY25 release | found |
| Fuel vs emissions split | H1 2026 only: emissions (ETS + CORSIA) EUR 233m within "Fuel costs and emissions charges" EUR 3,956m. No FY26 split for the EUR 8.3-8.6bn scenarios | H1 results announcement p.10 | found. Verbatim: "The cost of complying with various emissions trading schemes and the Carbon Offsetting and Reduction Scheme for International Aviation (CORSIA) was €233 million, up from €185 million in the first six months of 2025" |
| Jet fuel volume FY25 | 8.61 million tonnes (incl. SAF 291.1 kt); FY24 8.55 | Annual report 2025 p.286 | found. Verbatim: "Total jet fuel consumed MT fuel 8.61 8.55 9.65" (2025, 2024, 2019) |
| Volume FY26 / FY27 (model input) | Not printed. APPROVED 29 Sep 2026: FY26 = FY25 8.61m t, because capacity is guided flat - H1 presentation slide 28: "Capacity (ASK) now expected to be flat in 2026 compared to 2025". FY27 = FY26 (methodology section 4 assumption) | derived from AR p.286 + slide 28 | assumption - flat capacity guidance (slide 28) (ASSUMPTIONS.md A9, A10) |
| Fuel vs emissions split FY25 | FY25 "Fuel costs and emissions charges" EUR 7,083m include ETS/CORSIA EUR 378m and SAF premia EUR 222m | Annual report 2025 p.35 (also FY25 release p.14) | found. Verbatim: "The premia paid for the use of Sustainable Aviation Fuel (SAF) are included within Fuel costs and emissions charges; in 2025 this cost was €222 million"; "(CORSIA) was €378 million, up €77 million versus 2024." |
| Tax rate (marginal, model input) | Expected tax rate 24% (Spain 25%, UK 25%, Ireland 12.5%, profit mix). Reported effective rate FY25 25.8% (context) | Annual report 2025 p.37; note 10 p.183 | found. Verbatim p.37: "The geographical distribution of profits and losses in the Group results in the expected tax rate being 24% for the year."; "the effective tax rate was 25.8% (2024: 23.3%)" |
| Minorities FY25 | Nil -> m = 0 | Annual report 2025 p.154 | found. Verbatim: "Attributable to: Equity holders of the parent 3,342 ... Non-controlling interest – –" |
| EPS FY25 | Basic 71.3, diluted 69.5 (EUR CENTS) | Annual report 2025 p.154 | found. Verbatim: "Basic earnings per share (€ cents) 11 71.3 55.7"; "Diluted earnings per share (€ cents) 11 69.5 55.5" |
| Diluted shares, net debt/EBITDA | - | FY25 annual report | to-extract (Prompt 2) |

## Company-compiled consensus (EPS baseline)
| Airline | What is published | Date | Status |
|---|---|---|---|
| Lufthansa | PDF "ANALYST CONSENSUS POLL Q2 2026": Average / Median / Low / High / # of estimates for Total Revenue, Adjusted EBIT (group + segments), Adj. EBIT margin, Adj. FCF - FY26, FY27, FY28. NO net income, NO EPS. Numbers in European format ("1.897" = 1,897). Group Adj. EBIT median: FY26 1.897 (16 estimates), FY27 2.493 (15). Verbatim: "in mEUR FY 2026 ... Adjusted EBIT 1.864 1.897 1.029 2.251 16"; "in mEUR FY 2027 ... Adjusted EBIT 2.394 2.493 2.091 2.657 15" | "Date of Publication: July 16, 2026" (before the 27 Jul baseline) | found - EPS baseline needs a decision (no NI/EPS) |
| Air France-KLM | Web page (13 analysts per search snippet); metrics and statistics not yet seen (site blocks automated access) | collected 7-14 Jul 2026 (to check) | to-extract (you: save page as PDF) |
| IAG | Web page with charts; straight AVERAGE (no median); Q2 2026 and FY 2026 only, no 2027 | updated 24 Jul 2026; collected 6-13 Jul 2026 | to-extract (you: save page as PDF) |
Role since 29 Sep 2026: CROSS-CHECK only (L2). EPS baseline = third-party consensus (L4), below.

## Third-party consensus EPS (L4, decided explicitly 29 Sep 2026) - provider MarketScreener
Snapshots: taken 30 Sep 2026 by the agent in the in-app browser (headless browser was blocked with
"Access Denied"; no consent banner was clicked by the agent). Saved as dated screenshots (the pane
cannot print to PDF) in sources/third-party/2026-09-30_marketscreener_<airline>_1-header.jpg (name,
exchange, price timestamp) and _2-eps.jpg (EPS row incl. 2026-2027 estimates). Values read from the
page text and checked against the screenshots. Status "third-party".
| Airline | URL | FY26 EPS | FY27 EPS | # analysts | Date stamp on page | Statistic | EPS basis |
|---|---|---|---|---|---|---|---|
| Lufthansa | https://www.marketscreener.com/quote/stock/LUFTHANSA-436827/finances/ | 0.9221 EUR | 1.299 EUR | 18 | "Market Closed - Xetra 11:36:15 2026-09-29 am EDT" | not stated | reported diluted (see note) |
| Air France-KLM | https://www.marketscreener.com/quote/stock/AIR-FRANCE-KLM-4604/finances/ | 3.004 EUR | 4.418 EUR | 19 | "Market Closed - Euronext Paris 11:55:00 2026-09-29 am EDT" | not stated | reported diluted (see note) |
| IAG | https://www.marketscreener.com/quote/stock/INTERNATIONAL-CONSOLIDATE-7184685/finances/ | 0.6097 EUR | 0.7839 EUR | 15 | "Market Closed - BME 11:35:06 2026-09-29 am EDT" | not stated | reported diluted (see note) |
Verbatim EPS rows (page text, EUR, columns 2021-2028): LH "EPS 1 -2.99 0.66 1.4 1.15 1.12 0.9221 1.299 1.589";
AF-KLM "EPS 1 -59.5 3.1 4.1 0.93 5.5 3.004 4.418 5.285"; IAG "EPS 1 -0.591 0.061 0.506 0.555 0.695 0.6097 0.7839 0.9343".
Date check: no "last updated" stamp for the estimates is shown on any page; the only dates are the
price timestamps above - all three the SAME day (29 Sep 2026). Lufthansa is NOT older than the others.
The earlier "as of March 6, 2026" was the provider's "Announcement Date" of FY2025 results (3/6/26),
not an estimate date - resolved, no flag.
EPS basis note: the provider labels no basis. Its 2025 column equals each company's REPORTED DILUTED EPS -
LH 1.12 (AR p.257, basic = diluted), AF-KLM 5.5 (URD p.378: diluted 5.50; basic 5.83), IAG 0.695 EUR
(AR p.154: diluted 69.5 EUR cents; basic 71.3) - so estimates are treated as reported diluted EPS.
Currency: EUR per share for all three (the provider shows IAG in EUR, not cents).
Analysts: "Number of Analysts" on each page (covers the stock; EPS-specific count not shown).
Cross-check (threshold 10%): LH provider EBIT FY26 1,809 vs company poll median Adj. EBIT 1,897 -> -4.6% (within).
Fallback if the provider has no figure: last full-year actual EPS (printed, L1), labelled.

## Yardstick: expected operating profit per year (decision 30 Sep 2026, ASSUMPTIONS.md A26)
Hierarchy per airline and year: company's printed projection (L1) -> MarketScreener consensus EBIT (L4, same
snapshot as EPS) -> last actual (labelled). Consensus EBIT read from the snapshot screenshots
sources/third-party/2026-09-30_marketscreener_<airline>_3-revenue.jpg (EBIT row visible; pages price-stamped 29 Sep 2026).
| Airline | FY2026 (value, level) | FY2027 (value, level) | Verbatim | EBIT basis check (provider 2025 column vs printed FY25) |
|---|---|---|---|---|
| Lufthansa | Adj. EBIT guidance EUR 1.7-2.2bn -> midpoint 1,950m, L1 (Q2 charts slide 20) | consensus EBIT 2,281m, L4 | "EBIT 1 2,682 1,645 1,960 1,809 2,281 2,708" (2023-2028) | 1,960 = Adjusted EBIT FY25 (slide 30) - same basis |
| Air France-KLM | consensus EBIT 1,791m, L4 (no profit guidance printed) | consensus EBIT 2,140m, L4 | "EBIT 1 1,601 2,004 1,791 2,140 2,473" (2024-2028) | 2,004 = "CURRENT OPERATING INCOME (BEFORE IFRS 18)" FY25 (Q2 presentation slide 23), not adjusted operating profit after IFRS 18 2,069 -> ~3% basis gap, labelled (A27) |
| IAG | margin guidance 12-15% x consensus revenue 34,260m -> 4,625m (4,111-5,139m), L1 x L4 | consensus EBIT 5,054m, L4 | "EBIT 1 4,283 5,024 4,481 5,054 5,427" (2024-2028) | 5,024 = operating profit before exceptional items FY25 (FY25 release p.2) - same basis |
Cross-check (10% rule): LH provider FY27 EBIT 2,281m vs company poll median Adjusted EBIT FY 2027 2,493m
(LHG-Consensus-Q2-2026.pdf p.1, "Adjusted EBIT 2.394 2.493 2.091 2.657 15", published 16 Jul 2026, L2) -> -8.5%, within.
Consensus revenue FY2027 (added 1 Oct 2026 for the Step 6 margin, same snapshot, Net sales row): LH 44,153; AF-KLM 36,752;
IAG 35,971 EUR m (read again by the refresh script's OCR - identical).
Stored in data/airlines.yaml: consensus_ebit_fy26, consensus_ebit_fy27, consensus_revenue_fy27 (all three, third-party), poll_ebit_fy27
(LH found L2; peers not-applicable). Refresh: you save dated provider PDFs; a script shows old vs new (planned D2).

## FY2025 cost, revenue and capacity bases (Steps 4-6; decision 1 Oct 2026) - level 1, status "found"
Page numbers = PDF pages (as elsewhere in this register).
| Airline | Total operating costs FY25 | Revenue FY25 | Capacity FY25 (ASK) | Definition check |
|---|---|---|---|---|
| Lufthansa (AR 2025) | EUR 40,799m - p.43 T020 "Total operating expenses 40,799 39,097 4 100" | EUR 39,597m - p.3 "Total revenue in €m 39,597 37,581 5" | 338,552m - p.3 "Available seat-kilometres millions 338,552 326,176 4" | Adjusted: excludes extraordinary items (reported IFRS EUR 40,890m, T022 p.46) = cost base of Adjusted EBIT; other operating income NOT netted in; group incl. MRO, Logistics, Catering; fuel EUR 7,271m inside |
| Air France-KLM (URD 2025) | EUR 31,003m - p.378 "Operating expenses (31,003) (29,858)"; same in p.376 net-cost table | EUR 33,007m - p.378 "Revenues from ordinary activities 6.1 33,007 31,459" | 336,577m - p.376 "Capacity produced, reported in ASK 336,577 320,678" | Pre-IFRS 18 subtotal (33,007 - 31,003 = current operating income 2,004); NETS "other current operating income and expenses" +1,512 into the total -> gross ~32,515 (+4.9%); ASK = passenger network + Transavia; FY25 press release p.3 prints 336,521m (-0.02%) |
| IAG (AR 2025) | EUR 28,189m - p.154 "Total expenditure on operations 28,189 27,817" | EUR 33,213m - p.154 "Total revenue 5 33,213 32,100" | 351,435m - p.253 "Available seat km (ASK) million 351,435 343,253 ..." | No exceptional items in 2025 (p.229); includes fuel and emissions charges EUR 7,083m; other revenue in revenue, not netted |
Comparability: all three are group figures (non-airline businesses included); revenue - operating costs reconciles to each
company's operating profit measure (LH Adjusted EBIT also adds other operating income and equity results). Stored as
operating_costs_fy25, revenue_fy25, ask_fy25 (unit "million ASK") in data/airlines.yaml.

## News sources (decided 1 Oct 2026, D8b) - news headlines only; no number on the page comes from news
| Source | Verdict | Reason (as recorded) |
|---|---|---|
| GDELT DOC 2.0 API | **Kept - the only automatic feed** | Free, no key, headlines + links usable for display, English / German / French coverage; already integrated and tested. Split into 3 short queries (GDELT rejects long ones), 6 s apart (its limit: 1 request per 5 s). Known risk: 429 rate limits from some IPs - handled with a message, the page never depends on it. |
| Major outlets (Reuters, Bloomberg, Financial Times, WSJ, Handelsblatt, Les Echos, BBC) | **On request only, via web search** ("Search the web" button) | No free licensed feed; reached through Anthropic's web search tool on demand. Only headline, outlet, date and link are kept - no article text. Caps (approved): 3 searches per click, 1 click per 30 minutes and 5 per day for all visitors; estimated USD 0.03-0.08 per click (Anthropic price list read 1 Oct 2026: USD 10 per 1,000 searches + results as input tokens on Claude Haiku 4.5). |
| Aviation Week | **Not used** | Owner's decision 1 Oct 2026 ("skip Aviation Week"); the detailed reasoning from the earlier session was not saved to a file - add it here if it should be on the method page. |
| Company IR newsrooms (RSS) | Not built | Earlier fallback idea for GDELT outages (REVIEW_BACKLOG R8); not needed while GDELT + web search cover the case. |
Pre-AI keyword rule (src/news_keywords.py): airline / subsidiary name, or aviation-fuel term, or market / disruption term
together with an aviation word; place-name exclusions (e.g. "New Iberia", seen 1 Oct 2026). Duplicates merged by story,
other outlets shown as "also reported by". AI tags (Claude Haiku 4.5) are classifications only and are checked in code.

## Decisions taken from this research
1. Materiality reference: last full-year actual ADJUSTED operating profit for all three (LH adj. EBIT
   EUR 1,960m; AF-KLM adj. operating profit EUR 2,069m after IFRS 18; IAG EUR 5,024m before exceptional items).
2. Baseline date 27 Jul 2026 - curve date for all three (AF-KLM confirmed: R p.1 fn 3). Baseline PRICE =
   our own 27 Jul spot for all three; printed curve assumptions (LH, AF-KLM) are context + validation only.
3. Two peers, both European network groups with calendar years - clean comparison.
4. Validation targets: LH sensitivity table (slide 17); AF-KLM USD 9.3bn -> 8.9bn.
5. Recapture differs: AF-KLM circa 85%, LH ~60%, IAG ~60%.
6. Hedge quality matters: LH's remaining FY26 hedge is gasoil + Brent, no jet swaps printed.
7. Only Lufthansa discloses its hedge instrument mix (%). Peers' hedge quality is a range
   (jet-equivalent to crude-only); a finding shown on the page (decision 29 Sep 2026).
8. LH FY27 instrument split = FY26 split (assumption; AR 2025 p.90 wording).

## Comparability traps
Currency (AF-KLM in USD); fuel bill definitions (LH incl. mandatory SAF; IAG incl. emissions and
sustainability costs; AF-KLM "fuel bill"); rest-of-year vs full-year hedge ratios; different
curve dates; adjusted vs reported operating profit definitions; leverage definitions.
