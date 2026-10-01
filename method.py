"""Method & sources - the page behind every number on the story page.

Sections: summary, data sources by level, method, assumptions register, validation, limitations / confidence / data
status, news sources, ideas. Small superscript markers on the story link to the entries here (src/story/sources.py).
Run through app.py (navigation); every figure comes from data/airlines.yaml or the model, none is typed in.
"""
from datetime import datetime, timedelta

import streamlit as st

from src import news_tagger
from src.live_state import FALLBACK_FX, current_prices
from src.model.run import AIRLINES, BASELINE_DAY
from src.news_keywords import AIRLINE_TERMS, AVIATION_CONTEXT, EXCLUDE_TERMS, FUEL_STRONG, GENERAL_TERMS, MAJOR_OUTLETS
from src.story import method_content as mc
from src.story.hero import company_reports_as_of, consensus_as_of, split_check
from src.story.price_split import (
    LOOKBACK_YEARS, THRESHOLD_USD_T, WINDOW_DAYS, benchmark_split, co_movement, lookback_table, today_share,
)
from src.story.robustness import RECAPTURE_LOW, SPLITS, break_even_recapture, ranking_grid
from src.story.sources import assumption_groups
from src.story.yardstick import expected_operating_profit, expected_revenue, poll_cross_check
from src.twins import TwinsError, load_twins
from src.ui import method_parts as mp
from src.ui.charts import plot, split_history
from src.ui.css import inject
from src.ui.format import eur_m, pct, pct_range
from src.ui.theme import AIRLINE_LABELS
from src.validation import (
    BRENT_ROWS, CONFIDENCE_RULE, CREDIT_SCALE, CRACK_COLS, PRINTED, SOURCE, confidence_breakdown, confidence_label,
    fuel_bill_reconciliation,
    lufthansa_validation,
)

inject()

SECTIONS = (
    ("summary", "Summary", 0),
    ("data-sources", "Data sources by level", 0),
    ("data-l1", "Level 1 - company documents", 1), ("data-l2", "Level 2 - company consensus", 1),
    ("data-l3", "Level 3 - market data", 1), ("data-l4", "Level 4 - third parties", 1),
    ("data-l5", "Level 5 - assumptions", 1), ("data-none", "No value available", 1),
    ("method-chain", "Method", 0), ("method-yardstick", "Expected operating profit", 1),
    ("assumptions", "Assumptions register", 0),
    ("validation", "Validation", 0), ("validation-t2", "Lufthansa's own table", 1),
    ("validation-t9", "Fuel bill reconciliation", 1), ("validation-eps", "EPS reconciliation", 1),
    ("validation-robustness", "Robustness of the ranking", 1), ("validation-tagger", "News tagger accuracy", 1),
    ("limitations", "Limitations, confidence, data status", 0), ("confidence", "How the confidence score is calculated", 1),
    ("news-sources", "News sources", 0), ("ideas", "Ideas for improvement", 0),
)

try:
    twins = load_twins()
except TwinsError as err:
    st.error(f"Company data could not be loaded, so this page cannot show the sources.\n\n{err}")
    st.stop()

live, fetched, feed_notice = current_prices()
fx = live["fx"].data if live else FALLBACK_FX
H = lambda anchor, text, level=2: st.html(mp.heading(anchor, text, level))      # noqa: E731

st.html(mp.back_link("./", "Back to the story"))
st.title("Method & sources")
with st.container(key="method-layout"):
    nav, body = st.columns([1, 3.4], gap="large")
    with nav:
        with st.container(key="toc"):
            st.html(mp.toc(SECTIONS) + mp.scroll_to_hash(), unsafe_allow_javascript=True)
    with body:
        # --- summary -------------------------------------------------------------------------------------
        H("summary", "Summary")
        status = mc.status_table(twins)
        total = sum(sum(c.values()) for s, c in status.items() if s not in ("not-disclosed", "not-applicable"))
        found = sum(status.get("found", {}).values())
        verified_n = sum(status.get("verified", {}).values())
        lowest_label = min((confidence_label(twins, a)[0] for a in AIRLINES), key={"LOW": 0, "MEDIUM": 1, "HIGH": 2}.get)
        st.markdown(
            "This page documents every number on the story page: where each company figure comes from and how "
            "sure we are of it, every assumption, the calculation step by step, the checks that were run, what the "
            "analysis cannot do, and how the news is collected. The small superscript markers on the story, such as "
            "**[A26]** or **[L1]**, open the matching entry here in a new tab.\n\n"
            f"**Where things stand.** {total} company figures carry a value. {verified_n} are **verified**: checked "
            "against the company's own document (the quoted words found on the cited page, plus a reasonability test) "
            "or, for consensus EPS, against the dated MarketScreener snapshot and the live MarketScreener page. "
            f"{found} are read from a document but not yet checked, "
            f"{sum(status.get('third-party', {}).values())} are other third-party figures (analyst consensus on revenue "
            f"and profit, one press report), {sum(status.get('derived', {}).values())} are calculated from printed "
            f"figures, {sum(status.get('assumption', {}).values())} is an assumption and "
            f"{sum(status.get('not-disclosed', {}).values())} are not disclosed by the company. The confidence label "
            f"on the story is therefore {lowest_label}, and says so. Company figures are used exactly "
            "as printed; nothing is estimated by an AI model - the AI only classifies news headlines.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Figures with a value", total)
        c2.metric("Verified", verified_n)
        c3.metric("Not verified (calculated, third-party, assumed, undisclosed or not yet checked)", total - verified_n)
        st.html(f'<p class="fsm-faint">Company reports to {datetime.strptime(company_reports_as_of(twins), "%Y-%m-%d"):%-d %b %Y}'
                f' · analyst consensus snapshot {datetime.strptime(consensus_as_of(twins), "%Y-%m-%d"):%-d %b %Y}'
                + (f' · prices to {live["moves"]["latest_day"]:%-d %b %Y}' if live else " · live prices unavailable")
                + "</p>")

        # --- data sources ---------------------------------------------------------------------------------
        H("data-sources", "Data sources by level")
        st.markdown(
            "Every company figure is taken from the highest level available. Levels 1-5, from most to least "
            "reliable, are explained below. Each value is shown as printed (number, unit, period), with its status, "
            "the date, the document and page, and the exact quote in a toggle. Links go to the companies' own "
            "pages (or the provider's).")
        rows = mc.source_rows(twins)
        for level in (1, 2, 3, 4, 5):
            title, text = mc.LEVELS[level]
            H(f"data-l{level}", title, 3)
            st.markdown(text)
            if level == 3:
                anchors = {"FRED": "feed-fred", "ECB": "feed-ecb"}      # the first row of each feed carries its anchor
                for feed in mc.FEEDS:
                    st.html(mp.feed_row(feed, anchors.pop(feed["ref"], None)))
                continue
            by_airline = rows.get(level, {})
            if not by_airline:
                st.html('<p class="fsm-faint">No value in this project is taken from this level.</p>')
            for airline in AIRLINES:
                items = by_airline.get(airline)
                if items:
                    with st.expander(f"{mc.NAMES[airline]} - {len(items)} value{'s' if len(items) != 1 else ''}"):
                        st.html("".join(mp.source_row(r) for r in items))
        H("data-none", "No value available", 3)
        st.markdown("Figures the companies do not disclose, or that do not apply. They are left empty - never filled "
                    "with an estimate - and the model uses a labelled range instead (see the assumptions).")
        for airline in AIRLINES:
            items = rows.get(None, {}).get(airline)
            if items:
                with st.expander(f"{mc.NAMES[airline]} - {len(items)} fields"):
                    st.html("".join(mp.source_row(r) for r in items))

        # --- method -----------------------------------------------------------------------------------------
        H("method-chain", "Method")
        st.markdown(
            "The page follows one chain, the way a finance team would build it: **price move -> exposed fuel -> "
            "extra cost -> pass-through -> profit and EPS -> comparison**. Every step is the same calculation for "
            "all three airlines.")
        st.markdown("**1. Price split (Step 1).** A jet fuel move is crude oil plus the jet premium (the 'crack'), "
                    "both in USD per tonne from daily FRED prices (jet x 331.8 gallons per tonne, Brent x 7.9 barrels "
                    "per tonne). The baseline is 27 July 2026. The headline scenario is a USD 100/t rise split like the "
                    f"typical large move of the past {LOOKBACK_YEARS} years (A28); 'today's move' uses the actual split.")
        st.latex(r"\Delta \text{Jet} = \Delta \text{Brent} + \Delta \text{Crack}")
        st.markdown("**2. Exposed fuel (Step 2).** For each period, the share of fuel still open to a crude move and "
                    "to a premium move depends on the hedge ratio *h* and which instruments the hedges are. A Brent "
                    "hedge covers crude only; a gasoil hedge covers crude and a share *g* = 0.8 of the premium (A6); a jet "
                    "hedge covers both. With *h* split into Brent, gasoil and jet parts:")
        st.latex(r"u_B = 1 - h_B - h_G - h_J \qquad u_C = 1 - g\,h_G - h_J")
        st.markdown("Only Lufthansa discloses its split; for Air France-KLM and IAG the answer is a range from "
                    "all-jet to all-crude (A5). Rest of 2026 covers the days after the latest price; 2027 is a full year "
                    "with the move held (a parallel shift, A14).")
        st.markdown("**3. Extra fuel cost, gross (Step 3).** Volume *V* in tonnes times the unprotected shares times "
                    "the price moves, converted to euros:")
        st.latex(r"\Delta \text{Fuel} = V \,\big(u_B\,\Delta \text{Brent} + u_C\,\Delta \text{Crack}\big)\,/\,\text{FX}")
        st.markdown("It is also shown as a share of FY2025 operating costs and in euro cents per seat-kilometre "
                    "(A30). Lufthansa's options protect less as prices rise; for the rest of 2026 the answer includes a "
                    "case built from Lufthansa's own sensitivity table (A24).")
        st.markdown("**4. Pass-through (Step 3).** Airlines recover part of the extra cost through fares and "
                    "surcharges. With the printed rate *r* (and 50% as a cautious case, A25):")
        st.latex(r"\text{Net cost} = (1-r)\,\Delta \text{Fuel} \qquad \Delta \text{EBIT} = -\,\text{Net cost}")
        st.markdown("The net cost is the euro figure in the answer; Step 3 and the answer use the same function and a "
                    "test checks that they agree to the cent.")
        st.markdown("**5. Profit and EPS (Step 4).** The net cost comes off the operating profit expected for the same "
                    "year (see below). The operating margin uses expected revenue plus the revenue recovered through "
                    "fares (A31). Net income and EPS follow the income statement:")
        st.latex(r"\Delta NI = \Delta \text{EBIT}\,(1-t)(1-m) \qquad \Delta \text{EPS} = \Delta NI \,/\, N")
        st.markdown("*t* is the marginal tax rate each company prints (A17), *m* the minorities' share (A18), *N* the "
                    "diluted share count; the change is also shown as a share of consensus EPS (A20, A21).")

        H("method-yardstick", "The yardstick: expected operating profit", 3)
        st.markdown(
            "Every 'percent of operating profit' compares the cost with the profit expected for the **same year**, "
            "never a past year (A26). The hierarchy, per airline and year: **1.** the company's own printed projection "
            "(Lufthansa's adjusted EBIT range, midpoint; IAG's margin range times consensus revenue); **2.** "
            "otherwise the analyst consensus from one provider for all three; **3.** only as a last resort the last "
            "actual year, labelled.")
        yard = []
        for airline in AIRLINES:
            for period in ("FY2026", "FY2027"):
                e, r = expected_operating_profit(twins, airline, period), expected_revenue(twins, airline, period)
                span = "" if e["low"] == e["high"] else f" (range {e['low'] / 1e6:,.0f}-{e['high'] / 1e6:,.0f}m)"
                yard.append({"Airline": AIRLINE_LABELS[airline], "Year": period[2:],
                             "Expected operating profit": eur_m(e["value"]) + span, "Level": str(e["level"]),
                             "Basis (as of)": f"{e['source']}{' - FALLBACK' if e['fallback'] else ''} ({e['as_of']})",
                             "Expected revenue": eur_m(r["value"])})
        st.markdown(mc.md_table(yard))
        check = poll_cross_check(twins)
        if check:
            st.markdown(f"**Cross-check (10% rule).** Lufthansa publishes its own analyst poll. For 2027 the provider's "
                        f"consensus EBIT ({eur_m(check['provider'])}) is {check['difference']:+.1%} against the poll median "
                        f"({eur_m(check['poll'])}, published before the fuel move): "
                        f"{'within' if check['within'] else 'outside'} the 10% tolerance.")

        H("method-drivers", "Comparison and drivers (Steps 5-6)", 3)
        st.markdown(
            "**Why one airline is hit harder** is split into four factors by swapping Lufthansa's inputs for a "
            "peer's one at a time, in every possible order, and averaging (Shapley values; the parts add up exactly to "
            "the gap): pass-through, margin cushion (fuel burned per euro of expected profit), hedge cover and hedge "
            "quality (A29). **Robustness rule:** a ranking or a driver is named only if it holds in every range case; "
            "otherwise the text says what it depends on. **Step 6** varies one assumption at a time across its range "
            "to show which could change the answer (A32). **Step 9** recomputes the page for any scenario "
            "(A33).")

        # --- assumptions -----------------------------------------------------------------------------------------
        H("assumptions", "Assumptions register")
        st.markdown("Every assumption and derived value used by the model, with why it was made, how reliable the "
                    "source is, where it is used and what happens if it is wrong. The story's superscripts such as "
                    "[A26] point to these entries.")
        for group, rows in assumption_groups():
            H(f"assumptions-{group.lower().replace(' ', '-')}", group, 3)
            for row in rows:
                st.html(mp.assumption_card(row))

        # --- validation -------------------------------------------------------------------------------------------
        H("validation", "Validation")
        H("validation-t2", "Can the model reproduce Lufthansa's own sensitivity table?", 3)
        v = lufthansa_validation(twins)
        grid_cols = [f"crack {c}" for c in CRACK_COLS]
        for title, grid in (("Printed (USD/t)", [PRINTED[b] for b in BRENT_ROWS]),
                            ("Model (USD/t)", [[round(x) for x in v["predicted"][b]] for b in BRENT_ROWS]),
                            ("Model minus printed (USD/t)", [[round(x) for x in v["errors"][b]] for b in BRENT_ROWS])):
            st.markdown(f"**{title}**")
            st.markdown(mc.md_table([{"": f"Brent {b}", **dict(zip(grid_cols, row))}
                                     for b, row in zip(BRENT_ROWS, grid)]))
        s = v["summary"]
        st.markdown(
            f"Source: {SOURCE}; axes in USD/bbl for months not yet realised, as of 27 Jul 2026. The level is anchored "
            f"at the printed centre (Brent 84, crack 64 = 1,036); everything else is predicted, no tuning. Mean absolute "
            f"error {s['mean_abs']:.0f} USD/t, largest {s['max_abs']:.0f} USD/t (Brent {s['worst_cell'][0]}, crack "
            f"{s['worst_cell'][1]}).\n\n**What it means.** The crack sensitivity fits: the table implies "
            f"{v['slopes']['crack']['54->64']}-{v['slopes']['crack']['64->74']} USD/t per +10 USD/bbl near the centre, "
            f"the model {v['share'] * 79 * v['u_crack']:.0f}. The Brent sensitivity does not: the table implies "
            f"{v['slopes']['brent']['74->84']}-{v['slopes']['brent']['84->94']} USD/t near the centre, rising to "
            f"{v['slopes']['brent']['104->114']} at high prices; the model only {v['share'] * 79 * v['u_brent']:.0f}. "
            "Lufthansa hedges with option combinations (Annual Report 2025 p.90), whose protection fades as prices "
            "rise; the model treats hedges as swaps, so it understates Lufthansa's exposure to a Brent-led rise. This "
            "is why Lufthansa's rest-of-2026 range includes the 'company table' case (A24).")

        H("validation-t9", "Fuel bill reconciliation", 3)
        st.markdown("Volume times price after hedging, compared with the fuel bill the company printed.")
        for airline in AIRLINES:
            r = fuel_bill_reconciliation(twins, airline)
            if "computed" in r:
                st.markdown(f"- {mc.NAMES[airline]}: EUR {r['computed'] / 1e9:.2f}bn computed vs EUR "
                            f"{r['printed'] / 1e9:.2f}bn printed (fossil fuel) -> gap {r['gap_share']:+.1%}.")
            else:
                st.markdown(f"- {mc.NAMES[airline]}: {r['note']}")

        H("validation-eps", "EPS reconciliation", 3)
        st.markdown(
            "Three automated checks run on every change: (1) an independent hand calculation of the whole chain "
            "(price move -> fuel cost -> EBIT -> net income -> EPS) from printed inputs reproduces the model; (2) "
            "the net cost in Step 3 equals the euro figures in the answer (Step 7) exactly, and Step 4's chain equals the "
            "core model for every case; (3) the answer, every step and the scenario controls give the same numbers "
            "for any setting of the Step 9 controls.")

        H("validation-robustness", "Robustness of the ranking", 3)
        checks = split_check(twins, fx)
        grid = ranking_grid(twins, "FY2027", fx)
        st.markdown(
            "The same USD 100/t rise, split every way from all-crude to all-premium. The first three columns show each airline's loss as a share of expected 2027 operating profit at its "
            "reported pass-through rate. 'Any rate' lets each airline's rate range from 50% up to its reported "
            "rate, with every hedge case and profit range.")
        st.markdown(mc.md_table([{
            "Split (crude / premium)": f"{c['split'][0]:.0f} / {c['split'][1]:.0f}",
            "Lufthansa": pct_range(*c["ranges"]["lufthansa"]), "Air France-KLM": pct_range(*c["ranges"]["afklm"]),
            "IAG": pct_range(*c["ranges"]["iag"]),
            "Lufthansa hardest, reported rates": "yes" if c["lufthansa_hardest"] else "no",
            "Lufthansa hardest, any rate": "yes" if g["holds"] else "no",
            "Share of combinations": f"{g['share_lh_hardest']:.0%}"} for c, g in zip(checks, grid)]))
        shares = [g["share_lh_hardest"] for g in grid]
        st.markdown(
            f"**How to read the share.** Across the combinations in this grid Lufthansa is hit hardest in "
            f"{min(shares):.0%}-{max(shares):.0%} of them, depending on the split (last column). **This is not a probability.** It counts "
            "cells of a grid we chose - hedge cases, pass-through values from 50% up to the reported rates, guidance "
            "ranges - each cell weighted equally, although they are not equally likely (the reported rates are more "
            "plausible than 50%) and the real values may lie outside the grid. It shows how wide the uncertainty is, "
            "nothing more; the story never quotes it.")
        be = {peer: [break_even_recapture(twins, "FY2027", peer, fx, sp) for sp in SPLITS] for peer in ("afklm", "iag")}
        st.markdown(
            "**What decides the ranking:** the peers' pass-through. Lufthansa stays hit hardest unless Air France-KLM "
            f"passes on less than about {pct(min(be['afklm']))}-{pct(max(be['afklm']))} of the extra cost (it reported "
            f"circa 85% for one quarter) or IAG less than about {pct(min(be['iag']))}-{pct(max(be['iag']))} "
            f"(it expects around 60%); the range depends on the split. The lower end of the tested range is "
            f"{RECAPTURE_LOW:.0%}.")
        if live and live["moves"]:
            stats = benchmark_split(live["prices"], BASELINE_DAY, latest_day=live["moves"]["latest_day"])
            if not stats["fallback"]:
                st.markdown(
                    f"**Benchmark split.** The scenario's {stats['split'][0]:.0f} / {stats['split'][1]:.0f} is the median "
                    f"crude share of {stats['n']} large moves (jet fuel at least USD {THRESHOLD_USD_T:.0f}/t within "
                    f"{WINDOW_DAYS} days) in the {LOOKBACK_YEARS} years before 27 July; middle half "
                    f"{pct(stats['q1'], decimals=0)}-{pct(stats['q3'], decimals=0)}; a bootstrap 95% interval for the median is "
                    f"{pct(stats['interval'][0], decimals=0)}-{pct(stats['interval'][1], decimals=0)} (A28). The moves are not "
                    "independent (36 of the 81 end in 2022), so treat the interval as a guide to how loose the median is. "
                    "How the past moves split between crude and the premium, with today's move:")
                moves_now = live["moves"]
                plot(split_history(stats, {"day": moves_now["latest_day"], "share": today_share(moves_now),
                                           "d_jet": moves_now["d_jet"]}))
                st.markdown("Sensitivity to the lookback:")
                st.markdown(mc.md_table([{"Lookback": f"{r['years']} years", "From": f"{r['start']:%b %Y}",
                                          "Large moves": r["n"], "Median crude share": pct(r["median"], decimals=0),
                                          "Middle half": f"{pct(r['q1'], decimals=0)}-{pct(r['q3'], decimals=0)}"}
                                         for r in lookback_table(live["prices"], BASELINE_DAY)]))
                st.markdown(
                    "**Do crude and the jet premium move together?** Changes over non-overlapping periods before 27 "
                    "July. A positive correlation means the premium tends to rise with crude, so moves compound and a "
                    "crude-only hedge leaves the correlated premium part open. Read the table across horizons: over days and "
                    "weeks there is almost no link, and the link appears at one to two months - strongest in the last "
                    "two years, which is a recent pattern on few observations (see the observation counts).")
                rows = []
                for years in (LOOKBACK_YEARS, 2):
                    start = BASELINE_DAY - timedelta(days=round(365.25 * years))
                    rows += [{"Lookback": f"{years} years", "Horizon": c["label"], "Observations": c["n"],
                              "Correlation": f"{c['correlation']:+.2f}",
                              "Premium move per USD 1 crude": f"{c['beta']:+.2f}",
                              "Crude share of jet variance": pct(c["crude_share_of_variance"], decimals=0)}
                             for c in co_movement(live["prices"], start, BASELINE_DAY)]
                st.markdown(mc.md_table(rows))

        H("validation-tagger", "News tagger accuracy", 3)
        report = mc.tagger_report()
        st.markdown(report["note"])
        if report["agreement"]:
            st.markdown(mc.md_table([{"Field": name, "Agree": a, "Labelled": n,
                                      "Share": f"{a / n:.0%}" if n else "n/a"}
                                     for name, (a, n) in report["agreement"].items()]))
        st.markdown("Hand labels cover the airline, topic, direction, severity and the effect on each airline. Until "
                    "they exist, the tags and impact markers are indications only.")

        # --- limitations, confidence, status --------------------------------------------------------------------
        H("limitations", "Limitations, confidence and data status")
        st.markdown("\n".join(f"- {item}" for item in mc.LIMITATIONS))
        H("confidence", "How the confidence score is calculated", 3)
        st.markdown(CONFIDENCE_RULE)
        st.markdown(mc.md_table([{"Input is...": name, "Credit": f"{credit:.2f}", "Meaning": why}
                                 for name, credit, why in CREDIT_SCALE]))
        cc = st.columns(3)
        for col, airline in zip(cc, AIRLINES):
            label, score, _ = confidence_label(twins, airline)
            col.metric(f"Confidence: {mc.NAMES[airline]}", label, f"score {score:.0%}", delta_color="off")
        grid = {a: {r["field"]: r for r in confidence_breakdown(twins, a)} for a in AIRLINES}
        order = list(dict.fromkeys(f for a in AIRLINES for f in grid[a]))
        rows = [{"Input behind the 2027 answer": mc.FIELD_LABELS.get(f, f),
                 **{mc.NAMES[a]: (f"{grid[a][f]['credit']:.2f} ({grid[a][f]['status']})" if f in grid[a] else "n/a")
                    for a in AIRLINES}} for f in order]
        rows.append({"Input behind the 2027 answer": "**Score (average)**",
                     **{mc.NAMES[a]: f"**{confidence_label(twins, a)[1]:.0%}**" for a in AIRLINES}})
        st.markdown(mc.md_table(rows))
        st.markdown("All inputs weigh the same. A weighting by influence on the answer (from the tornado, Step 6) "
                    "would be fairer and is listed under ideas. The score for the rest of 2026 is "
                    + ", ".join(f"{mc.NAMES[a]} {confidence_label(twins, a, 'FY2026')[1]:.0%}" for a in AIRLINES) + ".")
        st.markdown("**Data status** - number of fields by status (meaning in brackets):")
        table = mc.status_table(twins)
        st.markdown(mc.md_table([{"Status": f"{s} ({mc.STATUS_WORDS[s]})",
                                  **{mc.NAMES[a]: n for a, n in counts.items()}} for s, counts in table.items()]))

        # --- news sources -----------------------------------------------------------------------------------------
        H("news-sources", "News sources")
        st.markdown(
            "News is context only: no number on the story comes from it. Sources were checked for whether an "
            "automatic, permitted feed exists. Decisions of 1 October 2026:")
        st.html(mp.verdict_table(mc.SOURCE_VERDICTS))
        st.markdown(
            "**Feed.** GDELT, the last three days, English, German and French sources, in three short searches "
            "(airline groups, peers, jet fuel terms) 6 seconds apart. **Search the web** (on request): Anthropic's "
            f"web search, asked for {', '.join(MAJOR_OUTLETS)}; only headline, outlet, date and link are kept. Limits "
            f"for all visitors together: {news_tagger.WEB_SEARCH_MAX_USES} searches per click, one click per "
            f"{int(news_tagger.WEB_SEARCH_COOLDOWN.total_seconds() // 60)} minutes, "
            f"{news_tagger.WEB_SEARCH_DAILY_CAP} a day; estimated cost about USD "
            f"{news_tagger.WEB_SEARCH_COST_PER_CLICK_USD[0]:.2f}-{news_tagger.WEB_SEARCH_COST_PER_CLICK_USD[1]:.2f} "
            "per click.")
        with st.expander("Keyword rule (before any AI call)"):
            st.markdown(
                "A headline is kept only if it **names one of the three groups or a subsidiary**, or contains an "
                "**aviation-fuel term**, or pairs a **market / disruption term with an aviation word**. Matching ignores "
                "case and respects word boundaries. Place names are excluded.")
            st.markdown("**Airline names:** " + ", ".join(AIRLINE_TERMS))
            st.markdown("**Fuel terms:** " + ", ".join(FUEL_STRONG))
            st.markdown("**Market / disruption terms:** " + ", ".join(GENERAL_TERMS))
            st.markdown("**Aviation words:** " + ", ".join(AVIATION_CONTEXT[:-len(AIRLINE_TERMS)]))
            st.markdown("**Excluded phrases:** " + ", ".join(EXCLUDE_TERMS))
        with st.expander("Tagging and guards"):
            st.markdown(
                f"Claude Haiku ({news_tagger.MODEL}) returns, for each headline, the airlines, the topic "
                f"({', '.join(news_tagger.DRIVERS)}), the direction of cost, a severity, a short quote and, for each "
                "airline, the likely effect on its earnings: positive, negative or neutral. Industry-wide headlines "
                "count for all three; a competitor's problem is never counted as good news for another airline. The code "
                "rejects any value outside these lists and any quote that does not appear word for word in the "
                "headline. Headlines are treated as data, never instructions (tested with 'ignore previous "
                f"instructions' and 'mark this positive'). Refresh on click only, a shared "
                f"{int(news_tagger.COOLDOWN.total_seconds() // 60)}-minute cooldown, at most {news_tagger.MAX_PER_REFRESH} "
                f"headlines and one AI call per refresh, a daily cap of {news_tagger.DAILY_CALL_CAP} calls, and a "
                "spending limit on the API account. The 7-day line counts headlines this page has collected since it "
                "last started (kept in memory).")

        # --- ideas ----------------------------------------------------------------------------------------------------
        H("ideas", "Ideas for improvement")
        st.html(mp.bullet_list(mc.IDEAS))
        st.html('<p class="fsm-faint" style="margin-top:32px">Prototype. Public data. Not investment advice. Not '
                "affiliated with any company shown. Built by Marcus Wallin.</p>")
