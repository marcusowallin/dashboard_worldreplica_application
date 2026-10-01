"""Content for the Method & sources page: everything that is not a calculation, prepared as plain data.

Streamlit-free so it can be tested. Company numbers come only from data/airlines.yaml (via the twins); the
news-source decisions, limitations and ideas are written here once.
"""
import csv
import json
from pathlib import Path

from src.model.run import AIRLINES
from src.news_tagger import agreement, parse_label

ROOT = Path(__file__).resolve().parents[2]

LEVELS = {
    1: ("Level 1 - the company's own documents",
        "Results releases, presentations, annual and interim reports, published transcripts. Always preferred, "
        "never overridden by a lower level. Used exactly as printed (same number, unit, period, rounding)."),
    2: ("Level 2 - company-compiled consensus",
        "Analyst consensus the company itself publishes on its investor-relations site (dated snapshot)."),
    3: ("Level 3 - other official sources",
        "Exchange or regulator filings, central banks. Here: the ECB exchange rate and the FRED price series "
        "(Federal Reserve Bank of St. Louis), listed under Market data."),
    4: ("Level 4 - reputable third parties",
        "Used only where levels 1-3 have nothing, or where decided explicitly: consensus estimates "
        "(MarketScreener, one provider for all three airlines) and one press report. Always labelled 'third-party' "
        "and counted as not verified."),
    5: ("Level 5 - labelled assumptions",
        "Where nothing is printed anywhere. Each is listed in the assumptions register with its sensitivity."),
}

STATUS_WORDS = {
    "verified": "verified by hand against the source", "found": "read from the source, not yet checked by hand",
    "derived": "calculated from printed figures", "assumption": "assumption", "third-party": "third-party figure",
    "not-disclosed": "not disclosed by the company", "not-applicable": "does not apply",
    "to-extract": "not yet extracted",
}

FIELD_LABELS = {
    "fuel_volume_fy26": "Fuel consumption FY2026", "fuel_volume_q3_26": "Fuel consumption Q3 2026", "fuel_volume_q4_26": "Fuel consumption Q4 2026",
    "fuel_bill_fy26": "Fuel bill FY2026 (guided)", "jet_price_after_hedge_fy26": "Jet fuel price after hedging FY2026",
    "hedge_ratio_fy26": "Hedge ratio FY2026 (full year)", "hedge_ratio_rest_fy26": "Hedge ratio, rest of FY2026",
    "hedge_ratio_q3_26": "Hedge ratio Q3 2026", "hedge_ratio_q4_26": "Hedge ratio Q4 2026",
    "hedge_ratio_fy27": "Hedge ratio FY2027", "hedge_ratio_fy27_upper": "Hedge ratio FY2027, upper end",
    "hedge_mix_gasoil": "Hedge book: gasoil part", "hedge_mix_brent": "Hedge book: Brent part",
    "hedge_mix_jet": "Hedge book: jet part", "recapture_rate": "Pass-through (recapture) rate",
    "tax_rate_marginal": "Tax rate used (marginal)", "tax_rate_effective_fy25": "Effective tax rate FY2025",
    "minority_share": "Minorities' share of net income", "diluted_shares": "Diluted shares",
    "eps_fy25": "Diluted EPS FY2025", "consensus_eps_fy26": "Consensus EPS FY2026",
    "consensus_eps_fy27": "Consensus EPS FY2027", "consensus_ebit_fy26": "Consensus EBIT FY2026",
    "consensus_ebit_fy27": "Consensus EBIT FY2027", "poll_ebit_fy27": "Company poll: adjusted EBIT FY2027 (median)",
    "operating_costs_fy25": "Total operating costs FY2025", "revenue_fy25": "Revenue FY2025",
    "ask_fy25": "Capacity FY2025 (available seat-km)", "consensus_revenue_fy26": "Consensus revenue FY2026",
    "consensus_revenue_fy27": "Consensus revenue FY2027", "adj_operating_profit_fy25": "Adjusted operating profit FY2025",
    "guidance_low": "Profit guidance FY2026, low end", "guidance_high": "Profit guidance FY2026, high end",
    "planning_fx_usd_per_eur": "Planning exchange rate (USD per EUR)",
}

NAMES = {"lufthansa": "Lufthansa Group", "afklm": "Air France-KLM", "iag": "IAG"}

FEEDS = (
    {"ref": "FRED", "name": "FRED DJFUELUSGULF - US Gulf Coast kerosene-type jet fuel", "level": "3",
     "url": "https://fred.stlouisfed.org/series/DJFUELUSGULF",
     "use": "Daily, USD per gallon; x 331.8 gallons per tonne. Stands in for European jet fuel (A15)."},
    {"ref": "FRED", "name": "FRED DCOILBRENTEU - Brent crude", "level": "3",
     "url": "https://fred.stlouisfed.org/series/DCOILBRENTEU",
     "use": "Daily, USD per barrel; x 7.9 barrels per tonne (A12). Jet premium (crack) = jet - Brent."},
    {"ref": "ECB", "name": "ECB euro reference rate, via the Frankfurter API", "level": "3",
     "url": "https://api.frankfurter.dev/v1/latest?base=EUR&symbols=USD",
     "use": "USD per EUR, latest business day; converts USD fuel costs to euros (A16)."},
)

# The news-source decisions (1 Oct 2026). Verdict: "in", "out", "on request".
SOURCE_VERDICTS = (
    ("GDELT", "in", "The existing feed: free, no key, headlines and links, English / German / French coverage."),
    ("Reuters, Bloomberg, Financial Times, WSJ, Les Echos, BBC", "on request",
     "Did not appear through GDELT in the test run, so they are reached only on request through web search "
     "(headline, outlet, date and link only), with strict limits."),
    ("Lufthansa Group, Air France-KLM, OPEC, Travel Weekly", "out", "Automated access is blocked (HTTP 403)."),
    ("IAG, Airlines for Europe (A4E), EASA (incl. conflict-zone bulletins)", "out",
     "No feed; we do not scrape their pages."),
    ("EIA", "out", "robots.txt disallows the feed (/rss)."),
    ("IATA", "out", "A feed exists, but the terms forbid use of the content on other websites without written consent."),
    ("Airline Weekly (Skift), AeroTime", "out", "The terms forbid automated collection."),
    ("Simple Flying", "out", "robots.txt prohibits automated retrieval and AI use."),
    ("Aviation Week", "out", "Terms page not found; not checked, so not used (owner's decision)."),
    ("Google News RSS", "out", "robots.txt disallows crawling and blocks AI agents by name."),
)

LIMITATIONS = (
    "Spot moves are applied as a parallel shift of the price curve for the rest of 2026 and all of 2027 (no free "
    "forward curves). Printed curves are steeply backwardated (IAG's presentation shows jet falling from about "
    "USD 1,150/t in Q3 2026 to about USD 900/t in Q4 2027 on 27 Jul), so the 2027 effects are probably overstated for "
    "all three airlines; the ranking is less affected than the levels (A14).",
    "US Gulf Coast jet fuel stands in for European jet fuel; Brent and jet are converted with one factor, "
    "7.9 barrels per tonne (A12, A15). Moves, not levels, matter; the proxy's own basis risk cannot be measured with "
    "free data.",
    "Options and collars are treated as swaps. Lufthansa's own sensitivity table shows its protection fading as "
    "prices rise (validation T2); the 'company table' case shows this for the rest of 2026 only, and at today's "
    "prices may itself understate the effect (A24).",
    "Only Lufthansa discloses its hedge instrument mix. For Air France-KLM and IAG hedge quality is a range, from "
    "all-jet to all-crude (A5), which is why it is called small and uncertain rather than a driver.",
    "Pass-through (recapture) is taken at the rates the companies printed, in the same period and symmetric. The "
    "three rates are not like-for-like (Lufthansa: a Q2 segment bridge; Air France-KLM: one quarter's actual, "
    "revenue only; IAG: a full-year expectation including cost initiatives) and are backward-looking, so the "
    "answer also shows 50% (A19, A25).",
    "Volumes are held constant (no capacity response). Unprinted quarters are a quarter of the year; the rest of 2026 "
    "is weighted by days; 2027 volume equals 2026 (A9-A11).",
    "Second-order interest and working-capital effects are ignored.",
    "Analyst consensus (MarketScreener, 29 Sep 2026) may already include part of the fuel move since 27 Jul. That "
    "would lower the expected profit and EPS bases and so overstate the percentages; the euro figures do not "
    "depend on it (A21).",
    "Lufthansa's 2027 hedge cover was not printed as of 27 July: 29% (printed, December 2025) to about 50% (a "
    "press-reported remark) (A2).",
    "Air France-KLM's consensus EBIT is on a basis about 3% below its adjusted operating profit (A27).",
    "The typical split of a large jet fuel move is descriptive, from past prices; it is not a forecast of the next "
    "move (A28).",
    "News tags and the effect on each airline are an AI model's classification of a headline, checked in code for "
    "allowed values and a verbatim quote. Whether the judgement is right is measured against hand labels, once "
    "labelled; until then treat the markers as indications.",
    "Company figures are read from the source documents but not all are yet checked by hand against the pages "
    "(see Data status below); the confidence label says so.",
)

IDEAS = (
    "Licensed European jet fuel (NWE) prices and forward curves instead of US Gulf Coast spot as a proxy.",
    "A licensed consensus API (EPS, EBIT, revenue with per-estimate dates) instead of hand-saved dated snapshots; "
    "the provider pages block automated access.",
    "Backtest: apply the method to an earlier fuel spike and compare with what the airlines then reported.",
    "Balance sheet view: cash flow, net debt and leverage impact (each company defines leverage differently).",
    "Market-reaction check: share-price moves on fuel-event days (needs a price feed licensed for public display).",
    "Monte Carlo over the uncertain assumptions (hedge mix, pass-through, volumes) for a probability range.",
    "Valuation view (EV/EBIT, implied equity value); ETS and SAF costs as further cost drivers.",
    "Quarterly capacity (seat-km) weighting instead of equal quarters; more carriers.",
    "Extraction of figures from new company documents with validation in code and human approval before use.",
    "A curve-adjusted 2027 case using the printed backwardation (limitation above).",
    "A persistent news archive and a feed of the companies' own newsrooms where they allow it.",
    "A second reviewer step that challenges each news tag before it is shown.",
)


def field_label(key):
    """Readable name of a twin field. Raises KeyError for a field without a label (a test catches new fields)."""
    return FIELD_LABELS[key]


def value_text(field):
    """The value as printed, with unit and currency; 'not available' for fields without a value."""
    value = field["value"]
    if value is None:
        return "not available"
    number = f"{value:,}" if isinstance(value, int) else f"{value:,.6f}".rstrip("0").rstrip(".")
    unit = f" {field['unit']}" if field.get("unit") else ""
    currency = f" ({field['currency']})" if field.get("currency") else ""
    return f"{number}{unit}{currency}"


def source_rows(twins):
    """Every company field as one row, grouped for the page: {level (int or None): {airline: [row, ...]}}.

    Fields without a value (not disclosed / not applicable) sit under level None, so nothing is hidden.
    Output row: {"field", "label", "value", "status", "status_text", "period", "as_of", "document", "url", "url_note",
                 "page", "quote", "note"}.
    """
    documents = twins["documents"]
    out = {}
    for airline in AIRLINES:
        for key, f in twins["airlines"][airline]["fields"].items():
            doc = documents.get(f["document"], {}) if f["document"] else {}
            row = {"field": key, "label": field_label(key), "value": value_text(f), "status": f["status"],
                   "status_text": STATUS_WORDS.get(f["status"], f["status"]), "period": f.get("period"),
                   "as_of": f.get("as_of"), "document": doc.get("title"),
                   "url": f.get("url") or doc.get("url"), "url_note": doc.get("url_note"),
                   "page": f.get("page"), "quote": f.get("quote"), "note": f.get("note")}
            out.setdefault(f["level"], {}).setdefault(airline, []).append(row)
    return out


def status_table(twins):
    """Counts of fields per status and airline: {status: {airline: n}}, in a fixed status order."""
    order = ("verified", "found", "derived", "third-party", "assumption", "not-disclosed", "not-applicable",
             "to-extract")
    table = {s: {a: 0 for a in AIRLINES} for s in order}
    for airline in AIRLINES:
        for f in twins["airlines"][airline]["fields"].values():
            table[f["status"]][airline] += 1
    return {s: counts for s, counts in table.items() if any(counts.values())}


def tagger_report(csv_path=ROOT / "data" / "labelled_headlines.csv",
                  tags_path=ROOT / "data" / "labelled_headlines_tags.json"):
    """Agreement of the AI tags with the hand labels, or None-values while nothing is labelled yet.

    Output: {"rows": n, "labelled": n, "agreement": {field: (agree, labelled)} or None, "note": text}.
    The tags file is written by scripts/evaluate_tagger.py (needs the labels and an API key).
    """
    try:
        rows = list(csv.DictReader(open(csv_path, encoding="utf-8", newline="")))
    except OSError:
        return {"rows": 0, "labelled": 0, "agreement": None, "note": "The labelled headline file is missing."}
    labels = [parse_label(r) for r in rows]
    labelled = sum(1 for lab in labels if any(v is not None for v in lab.values()))
    if not labelled:
        return {"rows": len(rows), "labelled": 0, "agreement": None,
                "note": f"Not measured yet: {len(rows)} real headlines are waiting for hand labels."}
    try:
        tags = json.loads(Path(tags_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"rows": len(rows), "labelled": labelled, "agreement": None,
                "note": f"{labelled} of {len(rows)} headlines are labelled; the evaluation has not been run yet."}
    if len(tags) != len(rows):
        return {"rows": len(rows), "labelled": labelled, "agreement": None,
                "note": "The saved tags do not match the labelled file; run the evaluation again."}
    return {"rows": len(rows), "labelled": labelled, "agreement": agreement(labels, tags),
            "note": f"Agreement of the AI tags with {labelled} hand-labelled real headlines."}


def md_table(rows):
    """A markdown table from a list of dicts with the same keys (wraps on narrow screens, unlike a data grid).

    Pipes and line breaks inside cells are neutralised; None prints as an empty cell.
    """
    if not rows:
        return ""
    cols = list(rows[0])

    def cell(value):
        return ("" if value is None else str(value)).replace("|", "/").replace("\n", " ")
    lines = ["| " + " | ".join(cell(c) for c in cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    lines += ["| " + " | ".join(cell(r.get(c)) for c in cols) + " |" for r in rows]
    return "\n".join(lines)
