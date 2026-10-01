"""Airline fuel shock monitor - the story, told bottom-up (rebuilt 2 Oct 2026 after the full review).

Run locally:  streamlit run app.py
Nine chapters. The page opens with the question, builds the evidence (1-2) and the analysis (3-5), shows what the
result rests on (6), and only then gives the answer (7), what it means (8) and lets the reader change the scenario (9).
Every number and sentence comes from the model and the templates in src/story/ - nothing is typed into the page. The
news room is its own page (news.py); sources, assumptions and checks are on Method & sources (method.py).
"""
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from src.data_sources import monthly_average_moves
from src.live_state import FALLBACK_FX, current_prices, update_prices
from src.model.run import AIRLINES, BASELINE_DAY, PEERS, Scenario, run_all
from src.story.choices import lufthansa_range, net_cost_per_tonne, pass_through_base, persistence_table, smoothed_move
from src.story.costs import cost_cases, size_neutral, summary
from src.story.exposure import chart_rows, exposure
from src.story.hero import (
    build_hero, company_reports_as_of, condition_sentence, consensus_as_of, live_line, split_check,
)
from src.story.method_content import md_table
from src.story.price_split import LOOKBACK_YEARS, THRESHOLD_USD_T, WINDOW_DAYS, benchmark_split, smooth
from src.story.profit import profit_cases, span
from src.story.robustness import RECAPTURE_LOW, SPLITS, attribution, break_even_recapture, loss_ranges
from src.story.scenario import PRESET_MOVES, apply_overrides, describe, preset_split
from src.story.sensitivities import hedge_cover, hedge_quality_swing, margin_multiplier, pass_through
from src.story.sources import markers as mk
from src.story.steps import (
    BAR_NAMES, FACTOR_NAMES, bill_step, comparison_step, exposure_step, hook_text, limits_lines, materiality_step,
    profit_step, sensitivity_sentences, sensitivity_table, shock_step, so_what_cards, tornado_step,
)
from src.story.tornado import tornado
from src.story.yardstick import expected_operating_profit
from src.twins import TwinsError, get_model_value, load_twins
from src.ui import components as ui
from src.ui.charts import contribution_bars, exposure_bars, plot, price_lines, range_rows, split_bars, tornado_bars
from src.ui.css import inject
from src.ui.format import story_eur_m_range, story_eur_share_range, story_pct_range
from src.ui.theme import AIRLINE_COLORS, AIRLINE_LABELS, AIRLINE_SHORT, COLORS
from src.validation import confidence_label

inject()

CONFIDENCE_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
ANSWER_STEP = 7

try:
    twins = load_twins()
except TwinsError as err:
    st.error(f"Company data could not be loaded, so no results are shown.\n\n{err}")
    st.stop()

# --- data -------------------------------------------------------------------------------------------
message = None
if st.session_state.pop("update_clicked", False):
    message = update_prices()
live, fetched, feed_notice = current_prices()
fx = live["fx"].data if live else FALLBACK_FX
fx_text = (f"USD/EUR {fx:.4f} (ECB, {live['fx'].as_of:%d %b %Y})" if live
           else f"USD/EUR {fx:.3f} (Lufthansa planning rate - ECB feed down)")
consensus_date = datetime.strptime(consensus_as_of(twins), "%Y-%m-%d")
moves = live["moves"] if live else None
smoothed = smoothed_move(live["prices"]) if live else None
split_stats = (benchmark_split(live["prices"], BASELINE_DAY, latest_day=moves["latest_day"]) if moves else
               {"split": (50.0, 50.0), "fallback": True, "n": 0, "episodes": [], "after": []})

# --- the scenario (Step 9 controls; defaults = the benchmark) --------------------------------------
twins_printed = twins
defaults = {"sc_crude": split_stats["split"][0], "sc_premium": split_stats["split"][1], "sc_pt": 0,
            "sc_hedge": (int(round(get_model_value(twins_printed, "lufthansa", "hedge_ratio_fy27") * 100)),
                         int(round(get_model_value(twins_printed, "lufthansa", "hedge_ratio_fy27_upper") * 100)))}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)
split = (float(st.session_state["sc_crude"]), float(st.session_state["sc_premium"]))
twins = apply_overrides(twins_printed, st.session_state["sc_pt"], st.session_state["sc_hedge"])
changed = (split != tuple(split_stats["split"]) or st.session_state["sc_pt"] != 0
           or tuple(st.session_state["sc_hedge"]) != defaults["sc_hedge"])
scenario_move = split[0] + split[1]
falling = scenario_move < 0
hero = build_hero(twins, fx, split, as_of_label=f"{consensus_date:%-d %b %Y}")
labels = {a: confidence_label(twins, a) for a in AIRLINES}
lowest = min((label for label, _, _ in labels.values()), key=CONFIDENCE_ORDER.get)
lowest_airline = min(AIRLINES, key=lambda a: labels[a][1])
scores = ", ".join(f"{AIRLINE_SHORT[a]} {labels[a][1] * 100:.0f}%" for a in AIRLINES)

# --- the hook: the question and the stakes, no answer yet -------------------------------------------
hook = hook_text(moves, scenario_move)
with st.container(key="hook"):
    st.html(ui.hook("Airline fuel shock monitor", hook["headline"], hook["body"]))
    left, right = st.columns([4, 1.3], vertical_alignment="center")
    left.html(ui.chips(ui.chip("Data as of", f"{moves['latest_day']:%-d %b %Y}" if moves else f"{consensus_date:%-d %b %Y}")))
    if right.button("Update data", key="update-data", help="Re-load jet fuel, Brent and USD/EUR and recompute"):
        st.session_state["update_clicked"] = True
        st.rerun()
    if message:
        st.html(ui.notice(message))
    if feed_notice:
        st.html(ui.notice(feed_notice))
    st.html(ui.skip_link("Skip to the answer", ANSWER_STEP))

st.write("")

# --- Step 1 - how big is the shock, and what is it made of -------------------------------------------
step = shock_step(moves, scenario_move, split, split_stats, smoothed)
with st.container(key="step-01"):
    st.html(ui.step_header(1, "How big is the shock, and what is it made of?", step["headline"], step["body"], "price",
                           markers_html=mk("FRED", "A12", "A13", "A15", "A28")))
    if live:
        recent = {d: v for d, v in live["prices"].items() if d >= BASELINE_DAY - timedelta(days=14)}
        plot(price_lines(recent, BASELINE_DAY, scenario_move))
    if moves:
        plot(split_bars([{"label": "Today, since 27 Jul", "brent": moves["d_brent"], "crack": moves["d_crack"]},
                         {"label": "The hypothetical shock used on this page", "brent": split[0], "crack": split[1]}]))
    st.html(ui.bridge("A crude hedge pays on crude, not on the jet premium. So how much fuel is actually protected?"))
    with st.expander("How we calculated this"):
        st.markdown(
            "Jet fuel: FRED series DJFUELUSGULF (US Gulf Coast kerosene-type jet fuel, USD per gallon x 331.8 gallons "
            "per tonne). Brent: FRED DCOILBRENTEU (USD per barrel x 7.9 barrels per tonne, A12). Jet premium (crack) = "
            "jet - Brent, per tonne. Baseline = the last price on or before 27 Jul 2026 (A13); US Gulf Coast jet stands "
            "in for European jet (A15). A jet fuel move = Brent move + jet premium move; Brent hedges cover the Brent part "
            "only, gasoil hedges cover Brent and a share g = 0.8 of the premium (A6), jet hedges cover both.\n\n"
            f"**The hypothetical shock (A28).** Daily FRED prices, 5-trading-day average; every move of jet fuel of at "
            f"least USD {THRESHOLD_USD_T:.0f}/t within {WINDOW_DAYS} calendar days in the {LOOKBACK_YEARS} years before "
            "27 July, counted without overlap. Crude share = Brent move / jet move. The shock uses the median share. "
            "Moves after 27 July are the current shock and are not part of the benchmark. History, lookback sensitivity "
            "and the link between crude and the premium: Method & sources.")
        if moves:
            st.dataframe(pd.DataFrame({
                "USD per tonne": ["Jet fuel", "Brent", "Jet premium"],
                f"{moves['baseline_day']:%d %b %Y}": [moves["baseline"][k] for k in ("jet", "brent", "crack")],
                f"{moves['latest_day']:%d %b %Y}": [moves["latest"][k] for k in ("jet", "brent", "crack")],
                "Move": [moves[k] for k in ("d_jet", "d_brent", "d_crack")]}).round(0), hide_index=True)

# --- Step 2 - what do the hedges cover ----------------------------------------------------------------
tonnes = exposure(twins, fx, split)
step = exposure_step(tonnes)
with st.container(key="step-02"):
    st.html(ui.step_header(2, "What do the hedges cover?", step["headline"], step["body"], "volume",
                           markers_html=mk("A2", "A5", "L1")))
    plot(exposure_bars(chart_rows(tonnes, {a: AIRLINE_LABELS[a] for a in AIRLINES})))
    st.html(ui.bridge("What is not protected hits the fuel bill. How big is that, and how much do fares give back?"))
    with st.expander("How we calculated this"):
        st.markdown(
            "Per period: volume x hedge ratio = hedged tonnes. Of those, jet hedges plus 80% of gasoil hedges protect "
            "against the jet premium too; Brent hedges (and 20% of gasoil hedges) leave it open. Unhedged = volume - "
            "hedged. Lufthansa's mix: 48 of 81 points gasoil, 33 Brent, no jet (Q2 charts slide 17, footnote 2; A1 for the "
            "rest of 2026, A3 for 2027). Air France-KLM and IAG do not disclose their mix (A5). Rest of 2026 = the remaining "
            "days of Q4; volumes from the companies' guidance (A9-A11).")
        st.dataframe(pd.DataFrame([{
            "Airline": AIRLINE_LABELS[a], "Period": "rest of 2026" if p == "FY2026" else "2027",
            "Case": r["case"] if a == "lufthansa" else "mix not disclosed",
            "Volume (m t)": r["volume"] / 1e6, "Hedged": r["hedged"] / r["volume"],
            "Unhedged (m t)": r["unhedged"] / 1e6,
            "Protected (m t)": None if r["protected"] is None else r["protected"] / 1e6,
            "Premium open (m t)": None if r["premium_open"] is None else r["premium_open"] / 1e6}
            for a, periods in tonnes.items() for p, rows in periods.items() for r in rows]),
            hide_index=True, column_config={
                "Hedged": st.column_config.NumberColumn(format="percent"),
                **{c: st.column_config.NumberColumn(format="%.1f") for c in
                   ("Volume (m t)", "Unhedged (m t)", "Protected (m t)", "Premium open (m t)")}})

# --- Step 3 - the fuel bill, fares, and what is left --------------------------------------------------
c27 = cost_cases(twins, "FY2027", fx, split)
gross27 = {a: summary(rows, "gross") for a, rows in c27.items()}
net27 = {a: summary(rows, "net") for a, rows in c27.items()}
low27 = {a: summary(rows, "net_at_low") for a, rows in c27.items()}
rec27 = {a: summary(rows, "recovered") for a, rows in c27.items()}
recapture = {a: get_model_value(twins, a, "recapture_rate") for a in AIRLINES}
neutral = {a: size_neutral(twins, a, *gross27[a]) for a in AIRLINES}
per_tonne = net_cost_per_tonne(twins, fx, split)
mag = lambda rng: tuple(sorted(abs(x) for x in rng))  # noqa: E731  (charts draw magnitudes; words say up or down)
step = bill_step(gross27, net27, recapture, low27, per_tonne, falling)
with st.container(key="step-03"):
    st.html(ui.step_header(3, "What lands on the fuel bill, and how much do fares give back?", step["headline"],
                           step["body"], "euro", markers_html=mk("A30", "A24", "A19", "A25")))
    rows = []
    for a in AIRLINES:
        rows += [
            {"label": f"{AIRLINE_SHORT[a]} · extra fuel {'saving' if falling else 'cost'} after hedging",
             "low": mag(gross27[a])[0] / 1e6, "high": mag(gross27[a])[1] / 1e6,
             "color": COLORS["text_3"], "text": story_eur_m_range(*mag(gross27[a]))},
            {"label": f"{'passed on to passengers' if falling else 'recovered through fares'} ({recapture[a] * 100:.0f}%)",
             "low": mag(rec27[a])[0] / 1e6, "high": mag(rec27[a])[1] / 1e6, "color": COLORS["cost_down"],
             "text": story_eur_m_range(*mag(rec27[a]))},
            {"label": "net saving kept" if falling else "net cost", "low": mag(net27[a])[0] / 1e6,
             "high": mag(net27[a])[1] / 1e6, "color": AIRLINE_COLORS[a], "text": story_eur_m_range(*mag(net27[a])),
             "marks": (mag(low27[a])[0] / 1e6, mag(low27[a])[1] / 1e6),
             "mark_text": f"net at 50% pass-through: {story_eur_m_range(*mag(low27[a]))}"}]
    plot(range_rows(rows, "EUR m, 2027 (diamonds: net cost at 50% pass-through)", height_per_row=42))
    st.html(ui.bridge("What fares do not give back comes out of profit. How big is that for each airline?"))
    with st.expander("How we calculated this"):
        st.markdown(
            "Extra fuel cost = tonnes still exposed (Step 2) x the price move: unhedged tonnes take the whole move, "
            "hedged-but-premium-open tonnes take the premium part (Step 1). Converted at the latest ECB USD/EUR. Ranges: "
            "Lufthansa's 2027 hedge cover (29-50%) and the peers' undisclosed hedge mix. Lufthansa's options: for the rest "
            "of 2026 the upper end uses its own sensitivity table (A24); none is printed for 2027 (see Step 6). "
            "**Recovered** = pass-through rate x extra fuel cost; **net cost** = the rest - the euro figure in the answer "
            "(Step 7). Rates as printed and not like-for-like (A19): Lufthansa ~60% (Network Airlines, Q2 2026 bridge), "
            "Air France-KLM circa 85% (Q2 2026 actual, via revenue only, helped by premium demand), IAG ~60% (full-year "
            "2026 expectation, via revenue and cost initiatives). The robustness check uses 50% up to each printed rate "
            "(A25). **Per tonne** = net cost / fuel volume. **Size-neutral views** (A30): 2027 extra cost / FY2025 "
            "operating costs and / FY2025 seat-km; definitions differ (Air France-KLM nets other operating income into "
            "its costs, Lufthansa's are adjusted, IAG's include emissions charges; costs are whole-group while seat-km are "
            "passenger).")
        st.dataframe(pd.DataFrame([{
            "Airline": AIRLINE_LABELS[a], "Case": r["case"], "Extra fuel cost (EUR m)": r["gross"] / 1e6,
            "Pass-through": r["recapture"], "Recovered (EUR m)": r["recovered"] / 1e6, "Net (EUR m)": r["net"] / 1e6,
            "Net at 50% (EUR m)": r["net_at_low"] / 1e6} for a in AIRLINES for r in c27[a]]), hide_index=True,
            column_config={**{c: st.column_config.NumberColumn(format="%,.0f") for c in (
                "Extra fuel cost (EUR m)", "Recovered (EUR m)", "Net (EUR m)", "Net at 50% (EUR m)")},
                "Pass-through": st.column_config.NumberColumn(format="percent")})
        st.dataframe(pd.DataFrame([{
            "Airline": AIRLINE_LABELS[a],
            "Operating costs FY25 (EUR m)": get_model_value(twins, a, "operating_costs_fy25") / 1e6,
            "Seat-km FY25 (bn)": get_model_value(twins, a, "ask_fy25") / 1e9,
            "2027 extra cost, % of operating costs": f"{neutral[a]['pct_opex'][0] * 100:.1f}-{neutral[a]['pct_opex'][1] * 100:.1f}%",
            "2027 extra cost, euro cents per seat-km": f"{neutral[a]['cents_per_ask'][0]:.3f}-{neutral[a]['cents_per_ask'][1]:.3f}"}
            for a in AIRLINES]), hide_index=True, column_config={
            "Operating costs FY25 (EUR m)": st.column_config.NumberColumn(format="%,.0f"),
            "Seat-km FY25 (bn)": st.column_config.NumberColumn(format="%.1f")})

# --- Step 4 - what is left of profit ------------------------------------------------------------------
profits = {"FY2027": profit_cases(twins, "FY2027", fx, split), "FY2026": profit_cases(twins, "FY2026", fx, split)}
step = profit_step(profits["FY2027"], falling)


def ratio_card(airline, rows):
    """Before -> after card for one airline and period (ranges over the hedge cases): operating profit and EPS."""
    op_after, op_share = span(rows, "op_after"), span(rows, "op_share")
    eps_after, eps_share = span(rows, "eps_after"), span(rows, "eps_share")
    first = rows[0]
    direction = "up" if falling else "down"
    return ui.airline_card(airline, [
        {"label": "Operating profit", "before": story_eur_m_range(first["op_before"], first["op_before"]),
         "after": story_eur_m_range(*op_after), "change": story_pct_range(*op_share), "direction": direction},
        {"label": "EPS vs consensus", "before": story_eur_share_range(first["eps_before"], first["eps_before"]),
         "after": story_eur_share_range(*eps_after) if eps_after else "n/a",
         "change": story_pct_range(*eps_share) if eps_share else "n/a", "direction": direction}])


with st.container(key="step-04"):
    st.html(ui.step_header(4, "What is left of profit?", step["headline"], step["body"], "gauge",
                           markers_html=mk("A31", "A17", "A18", "A34")))
    tab27, tab26 = st.tabs(["2027", "Rest of 2026"])
    with tab27:
        st.html(ui.cards(*(ratio_card(a, profits["FY2027"][a]) for a in AIRLINES)))
    with tab26:
        st.html(ui.cards(*(ratio_card(a, profits["FY2026"][a]) for a in AIRLINES)))
        st.html('<p class="fsm-label">2026 = full-year expected figures; the shock hits only the rest of the year (Q4). '
                "Lufthansa's range includes its options case (Step 3).</p>")
    st.html(ui.bridge("The three hits differ in size. Why?"))
    with st.expander("How we calculated this"):
        st.markdown(
            "**Chain** (src/model/income.py): operating profit change = - net cost (Step 3); revenue change = recovered "
            "through fares; net income change = operating profit change x (1 - tax rate) x (1 - minorities' share); EPS "
            "change = net income change / diluted shares.\n\n"
            "**Before**: expected operating profit (company guidance, else MarketScreener consensus EBIT) and expected "
            "revenue (consensus - no company prints a revenue projection), consensus EPS (MarketScreener, snapshot 29 Sep "
            "2026). **Margin after** = (profit - net cost) / (revenue + recovered revenue).\n\n"
            "**Tax: marginal, not effective** (A17): Lufthansa 25%, Air France-KLM 25.83%, IAG 24%; reported effective rates "
            "are distorted by one-offs. **Minorities** (A18): Lufthansa 1.8%, Air France-KLM 9.2%, IAG 0%. **Shares** (A34): "
            "Air France-KLM's count excludes the convertible it redeemed in November 2025; the others carry FY2025 forward.\n\n"
            "**Consensus timing** (A21): the 29 Sep snapshot follows most of the price rise since 27 July, so analysts may "
            "already have cut their estimates - the 'before' may be too low and the % changes too high. EUR amounts do "
            "not depend on it. **Leverage** is not shown: the three define it differently.")
        st.dataframe(pd.DataFrame([{
            "Airline": AIRLINE_LABELS[a], "Year": "2027" if p == "FY2027" else "2026", "Case": r["case"],
            "Net cost (EUR m)": r["net"] / 1e6, "Op. profit change (EUR m)": r["d_ebit"] / 1e6,
            "Expected op. profit (EUR m)": r["op_before"] / 1e6, "Expected revenue (EUR m)": r["rev_before"] / 1e6,
            "Margin change (pp)": r["margin_pp"] * 100, "Tax": r["tax"], "Minorities": r["minority"],
            "Net income change (EUR m)": r["d_net_income"] / 1e6, "Diluted shares (m)": r["shares"] / 1e6,
            "EPS change (EUR)": r["d_eps"], "Consensus EPS (EUR)": r["eps_before"]}
            for p in ("FY2027", "FY2026") for a in AIRLINES for r in profits[p][a]]), hide_index=True,
            column_config={**{c: st.column_config.NumberColumn(format="%,.1f") for c in (
                "Net cost (EUR m)", "Op. profit change (EUR m)", "Expected op. profit (EUR m)",
                "Expected revenue (EUR m)", "Net income change (EUR m)", "Diluted shares (m)")},
                "Margin change (pp)": st.column_config.NumberColumn(format="%.2f"),
                "Tax": st.column_config.NumberColumn(format="percent"),
                "Minorities": st.column_config.NumberColumn(format="percent"),
                "EPS change (EUR)": st.column_config.NumberColumn(format="%.3f"),
                "Consensus EPS (EUR)": st.column_config.NumberColumn(format="%.4f")})

# --- Step 5 - why the three differ ---------------------------------------------------------------------
r27 = loss_ranges(twins, "FY2027", fx, split)
hq = hedge_quality_swing(twins, fx, split)
step = comparison_step(r27, hero["reasons"], condition_sentence(hero["status"]["FY2027"], falling), hq, falling)
with st.container(key="step-05"):
    st.html(ui.step_header(5, "Why do the three differ?", step["headline"], step["body"], "compare",
                           markers_html=mk("A29", "A25")))
    attr = {p: attribution(twins, "FY2027", p, fx, split) for p in PEERS}
    avg = [{"peer": p, "parts": {f: sum(r["parts"][f] for r in rows) / len(rows) for f in rows[0]["parts"]}}
           for p, rows in attr.items()]
    plot(contribution_bars(avg, "pp of expected 2027 operating profit by which Lufthansa loses more"))
    st.html(ui.bridge("Every number leans on assumptions. Which could change the order?"))
    with st.expander("How we calculated this"):
        st.markdown(
            "**Why the gap** (A29): the gap to each peer is split into four drivers by swapping Lufthansa's inputs for the "
            "peer's one at a time, averaged over every order of the swaps, so the parts add up exactly to the gap. Shown: the "
            "average over the hedging cases (Lufthansa 29% / ~50%, the peers' mix jet-equivalent / central / crude-only); the "
            "table gives every case. Drivers: **pass-through** (recapture rate), **margin cushion** (fuel burned per euro of "
            "expected operating profit), **hedge cover** (hedge ratio), **hedge quality** (instrument mix - the peers' is "
            "undisclosed, so it can change sign).")
        st.dataframe(pd.DataFrame([{
            "Peer": AIRLINE_LABELS[p], "Lufthansa case": r["lh_case"], "Peer mix": r["peer_case"],
            "Gap (pp)": r["gap"] * 100, **{FACTOR_NAMES[f].capitalize() + " (pp)": v * 100 for f, v in r["parts"].items()}}
            for p, rows in attr.items() for r in rows]), hide_index=True,
            column_config={c: st.column_config.NumberColumn(format="%+.1f") for c in
                           ["Gap (pp)"] + [FACTOR_NAMES[f].capitalize() + " (pp)" for f in attr["afklm"][0]["parts"]]})
        st.markdown("**When would a peer be hit as hard?** Pass-through below which the peer's worst case loses as much as "
                    "Lufthansa's best case, by crude/premium split:")
        st.dataframe(pd.DataFrame([{
            "Split (crude / premium)": f"{sp[0]:.0f} / {sp[1]:.0f}",
            **{AIRLINE_LABELS[p]: break_even_recapture(twins, "FY2027", p, fx, sp) for p in PEERS}} for sp in SPLITS]),
            hide_index=True, column_config={AIRLINE_LABELS[p]: st.column_config.NumberColumn(format="percent")
                                            for p in PEERS})

# --- Step 6 - what the answer rests on ------------------------------------------------------------------
margin_info, pt_info, cover_info = margin_multiplier(twins, fx, split), pass_through(twins, fx, split), hedge_cover(twins, fx, split)
torn = tornado(twins, fx, split, (split_stats["q1"], split_stats["q3"]) if not split_stats["fallback"] else None)
step6 = tornado_step(torn, falling)
persist = persistence_table(twins, fx, split)
pt_base = pass_through_base(twins, fx, split)
lh_range = lufthansa_range(twins, fx, split)
flat = {a: loss_ranges(twins, 'FY2027', fx, split)[a] for a in AIRLINES}
sens_rows = sensitivity_table(persist, pt_base, lh_range, flat)
sens_text = sensitivity_sentences(pt_base, lh_range, flat)


def _runner_up_text(step):
    """'hedge cover close behind' when the runner-up on Lufthansa's own loss is within 25% of the top bar."""
    if not step["runner_up_close"]:
        return None
    name = BAR_NAMES.get(step["own_runner_up"]["key"], step["own_runner_up"]["label"])
    return (f"{name} close behind ({step['own_runner_up']['lh_swing'] * 100:.1f} vs "
            f"{step['own_top']['lh_swing'] * 100:.1f} pp in Step 6)")


cards_data = so_what_cards(margin_info, pt_info, cover_info, hq, falling, step6["pass_through_largest"],
                           _runner_up_text(step6))
with st.container(key="step-06"):
    st.html(ui.step_header(6, "What does the answer rest on?", step6["headline"], step6["body"], "tornado",
                           markers_html=mk("A32", "A35", "A36", "A37")))
    plot(tornado_bars(torn, axis_title=f"Lufthansa's {'gain' if falling else 'loss'} minus the peer average, "
                                       "pp of expected 2027 operating profit"))
    st.markdown("**Choices that change the levels** (% of expected 2027 operating profit; minus = a gain)")
    st.markdown(md_table(sens_rows))
    st.markdown(sens_text["pass_through"])
    st.markdown(sens_text["lufthansa"])
    st.markdown("**What this cannot tell you.**")
    st.markdown("\n".join(f"- {line}" for line in limits_lines()))
    st.html(ui.bridge("That is the evidence and its limits. Here is the answer."))
    with st.expander("How we calculated this"):
        st.markdown(
            "One assumption at a time moves across its range (ASSUMPTIONS.md), the others stay at the base case: Lufthansa's "
            "2027 hedge cover at the middle of its range, the printed hedge mix, the peers' central mix, the shock's split, "
            "printed pass-through applied to the cost after hedging, g = 0.8, the expected profit, today's USD/EUR, the "
            "volumes, the whole shock lasting through 2027. Same calculation as the answer. The three tables above use the "
            "same building blocks (src/story/choices.py): persistence scales the move (the model is linear in it); the "
            "pass-through reading replaces (1 - r) x cost after hedging by cost - r x volume x market move; Lufthansa's "
            "options fade scales its swap protection by what its own FY2026 sensitivity table implies "
            f"(Brent {lh_range['fade'][0]:.0%}, crack {lh_range['fade'][1]:.0%} of the swap protection; A36).")
        st.dataframe(pd.DataFrame([{
            "Assumption": b["label"], "Gap, low end (pp)": b["low"] * 100, "Gap, high end (pp)": b["high"] * 100,
            "Swing (pp)": b["swing"] * 100, "Lufthansa's own, low (%)": b["lh_low"] * 100,
            "Lufthansa's own, high (%)": b["lh_high"] * 100, "Swing on Lufthansa (pp)": b["lh_swing"] * 100}
            for b in torn["bars"]]), hide_index=True, column_config={
            c: st.column_config.NumberColumn(format="%.1f") for c in (
                "Gap, low end (pp)", "Gap, high end (pp)", "Swing (pp)", "Lufthansa's own, low (%)",
                "Lufthansa's own, high (%)", "Swing on Lufthansa (pp)")})
        plot(tornado_bars(torn, key=("lh_low", "lh_high"), base_key="base_lh",
                          axis_title="Lufthansa's own loss, % of expected 2027 operating profit"))

# --- Step 7 - the answer --------------------------------------------------------------------------------
full = lh_range["full"]
with st.container(key="hero"):
    st.html(f'<div class="fsm-anchor" id="step-{ANSWER_STEP:02d}"></div>' + ui.hero_text(
        "The answer · 2027", hero["sentence"], hero["why"], hero["label"], markers_html=mk("A28", "A25"),
        label_markers_html=mk("YARD", "L4"), step_no=ANSWER_STEP))
    st.html(ui.number_row([
        {"airline": row["airline"], "value": row["cost"],
         "sub": f"{row['share']} of expected 2027 operating profit",
         "caption": ("net saving kept" if falling else "net cost") + " after hedging and pass-through",
         "markers_html": mk("A19")}
        for row in hero["rows"]]))
    if not hero["mixed"] and not falling:
        st.html(ui.hero_line("Including Lufthansa's undisclosed hedge mix and an options fade (Step 6): "
                             f"{story_pct_range(full['low'], full['high'])} of expected profit, "
                             f"{story_eur_m_range(full['cost_low'], full['cost_high'])}."))
    st.html(ui.hero_line(hero["fy26"]))
    st.html(ui.chips(
        *([ui.chip("Scenario (changed in Step 9)", describe(split, st.session_state["sc_pt"], st.session_state["sc_hedge"],
                                                             {"lh_hedge": defaults["sc_hedge"]}))] if changed else []),
        ui.chip("Confidence", lowest, tone="warn" if lowest != "HIGH" else "default",
                note=(f"Why {lowest}: confidence is a score of how well the inputs behind the 2027 answer are sourced "
                      f"({scores}); the label follows the least-sourced airline, {AIRLINE_SHORT[lowest_airline]}. "
                      "Checked company figures count fully, checked consensus and calculated figures three quarters, "
                      "assumptions half, and figures a company does not disclose a quarter (the result then carries "
                      "them as a range). What raises it: more of the remaining inputs being checked or disclosed. "
                      "The full calculation is on Method & sources. Rule: HIGH from 80%, MEDIUM from 50%."))))
    if hero["mixed"]:
        st.html(ui.notice("Crude and the jet premium move in opposite directions in this scenario, so the page shows the "
                          "net effect and makes no ranking claim; the step headlines assume a clean rise or fall."))
    price_part = (f"Prices to {moves['latest_day']:%-d %b %Y} (FRED jet fuel and Brent, fetched {fetched:%-d %b %H:%M} UTC)"
                  if moves else "Live prices unavailable")
    st.html(ui.as_of_line(f"Data as of {moves['latest_day']:%-d %b %Y} (FRED, ECB) · consensus {consensus_date:%-d %b %Y} "
                          "(MarketScreener) · company reports to "
                          f"{datetime.strptime(company_reports_as_of(twins), '%Y-%m-%d'):%-d %b %Y}. Sources and detail: "
                          "Method & sources." if moves else f"Live prices unavailable ({fx_text}). Sources and detail: Method & sources."))
    st.html(ui.bridge("What does that mean - and would a monitor raise an alert?"))
    with st.expander("How we calculated this"):
        st.markdown(hero["base_note"])
        st.markdown(f"{price_part} · {fx_text}." if moves else "Live prices are unavailable.")
        st.markdown(
            f"**The shock.** Jet fuel {scenario_move:+,.0f} USD/t from 27 Jul 2026, split {split[0]:+.0f} crude (Brent) / "
            f"{split[1]:+.0f} jet premium - the median split of large jet fuel moves in the {LOOKBACK_YEARS} years before "
            "27 July (Step 1, A28). **Net cost** = extra fuel cost after hedging (Steps 2-3) x (1 - pass-through rate). "
            "**% of expected operating profit** = net cost / the operating profit expected for 2027: company guidance where "
            "printed, otherwise one provider's analyst consensus (A26). Ranges: Lufthansa's 2027 hedge cover 29-50% and the "
            "peers' undisclosed hedge mix. **Why** comes from the driver attribution (Step 5, A29).")
        st.dataframe(pd.DataFrame([{
            "Airline": AIRLINE_LABELS[a],
            "Expected 2027 operating profit (EUR m)": expected_operating_profit(twins, a, "FY2027")["value"] / 1e6,
            "Source": expected_operating_profit(twins, a, "FY2027")["source"],
            "As of": expected_operating_profit(twins, a, "FY2027")["as_of"]} for a in AIRLINES]),
            hide_index=True, column_config={"Expected 2027 operating profit (EUR m)":
                                            st.column_config.NumberColumn(format="%,.0f")})
        checks = split_check(twins, fx)
        holds = all(c["lufthansa_hardest"] for c in checks)
        st.markdown(
            "**Does the split of the shock matter?** The same USD 100/t move, split every way from all-crude to "
            "all-premium, at the reported pass-through rates: Lufthansa loses the largest share of expected profit "
            + ("in every split." if holds else "in some splits only.")
            + f" What can change the order is pass-through: from {RECAPTURE_LOW:.0%} up to each airline's reported rate "
            "(Steps 3 and 5).")
        st.dataframe(pd.DataFrame([{
            "Split (crude / premium, USD/t)": f"{c['split'][0]:.0f} / {c['split'][1]:.0f}",
            **{AIRLINE_LABELS[a]: story_pct_range(*c["ranges"][a]) for a in AIRLINES},
            "Lufthansa hit hardest": "yes" if c["lufthansa_hardest"] else "no"} for c in checks]), hide_index=True)

# --- Step 8 - what it means ------------------------------------------------------------------------------
with st.container(key="step-08"):
    st.html(ui.step_header(8, "What does it mean?", "What it means for Lufthansa, and for a monitor watching it",
                           "Two observations from the numbers on this page - not recommendations.", "flag",
                           markers_html=mk("A32")))
    st.html(ui.cards(*(ui.takeaway_card(c["title"], c["sentence"], c["icon"], number=c["number"], note=c["note"],
                                        sub=c.get("sub")) for c in cards_data[:2]), columns=2))
    st.html(ui.hero_line(materiality_step(profits["FY2027"])["sentence"]))
    st.html(ui.bridge("Now change the assumptions yourself."))
    with st.expander("How we calculated this"):
        st.markdown(
            "**Thin margins**: expected 2027 margins (Step 4); the multiple compares Lufthansa's and IAG's % of expected profit "
            "lost, over every pair of hedging cases. **Pass-through**: net cost = (1 - pass-through) x extra fuel cost "
            "(Step 3), so 10 points of pass-through move it by 10% of the extra fuel cost. **Hedge cover and disclosure** "
            "(Step 6): Lufthansa's 2027 net cost at 29% minus at ~50% cover, and the hedge-quality part of the gap in Step 5, "
            "smallest and largest over both peers and all cases.\n\n**'Biggest lever' depends on the tested ranges** "
            "(Step 6): pass-through is the largest bar for the gap to the peers; on Lufthansa's own loss another assumption "
            "can be close or larger (persistence, its hedge book), and Lufthansa's pass-through is tested only from 50% to "
            "its reported ~60%. If another assumption ever becomes the largest bar for the gap, the card says 'a major "
            "lever' instead.")


# --- Step 9 - try it yourself ----------------------------------------------------------------------------
def _set_move(crude, premium):
    st.session_state["sc_crude"], st.session_state["sc_premium"] = float(crude), float(premium)


def _reset():
    for key, value in defaults.items():
        st.session_state[key] = value


with st.container(key="step-09"):
    st.html(ui.step_header(9, "Try it yourself", "Change the scenario - every number on this page follows.",
                           "Presets split a move like the typical large move; the sliders set crude and premium "
                           "separately, shift every airline's pass-through, or change Lufthansa's 2027 hedge cover.",
                           "sliders", markers_html=mk("A33")))
    st.html(ui.notice("Result with the settings below - " + " · ".join(
        f"{AIRLINE_SHORT.get(row['airline'], row['airline'])}: {row['cost']} ({row['share']})" for row in hero["rows"])))
    cols = st.columns(len(PRESET_MOVES) + 2)
    for col, move in zip(cols, PRESET_MOVES):
        col.button(f"{'+' if move > 0 else chr(0x2212)}{abs(move):.0f} USD/t", key=f"preset-{move:+.0f}",
                   on_click=_set_move, args=preset_split(move, split_stats["split"]), use_container_width=True)
    cols[-2].button("Today", key="preset-today", disabled=not moves, use_container_width=True,
                    on_click=_set_move, args=((round(moves["d_brent"]), round(moves["d_crack"])) if moves else (0, 0)),
                    help="The actual move since 27 July (Step 1)")
    cols[-1].button("Reset", key="scenario-reset", on_click=_reset, use_container_width=True)
    left, right = st.columns(2)
    left.slider("Crude (Brent) move, USD/t", -300.0, 400.0, step=1.0, format="%+.0f", key="sc_crude")
    right.slider("Jet premium move, USD/t", -200.0, 300.0, step=1.0, format="%+.0f", key="sc_premium")
    left.slider("Pass-through, pp vs each airline's reported rate", -30, 20, step=5, format="%+d", key="sc_pt",
                help="Shifts all three airlines' rates by the same points (each is kept between 0% and 100%).")
    right.slider("Lufthansa 2027 hedge cover, % (range)", 0, 90, step=1, key="sc_hedge",
                 help="Printed 29% (Dec 2025) to ~50% (reported) by default.")
    if live and moves:
        live_run = run_all(twins_printed, Scenario(usd_per_eur=fx), live)
        smooth_run = None
        if smoothed:
            prices_smooth = smooth(live["prices"])
            smooth_run = run_all(twins_printed, Scenario(usd_per_eur=fx), {
                **live, "moves": smoothed,
                "monthly": monthly_average_moves(prices_smooth, BASELINE_DAY, max(prices_smooth))})
        st.html(ui.hero_line(live_line(live_run, moves, smooth_run), kind="live"))

# --- footer -----------------------------------------------------------------------------------------
st.html(ui.footer(
    "method",
    ["Jet fuel and Brent: FRED (DJFUELUSGULF, DCOILBRENTEU), prices to "
     + (f"{moves['latest_day']:%-d %b %Y}" if moves else "n/a (feed down)"),
     "USD/EUR: ECB reference rate via Frankfurter" + (f", {live['fx'].as_of:%-d %b %Y}" if live else " (feed down)"),
     f"Company figures: annual reports, Q2 / H1 2026 reports and presentations (to "
     f"{datetime.strptime(company_reports_as_of(twins), '%Y-%m-%d'):%-d %b %Y}); figures checked against the documents "
     "(see Method & sources)",
     f"Analyst consensus: MarketScreener, snapshot {consensus_date:%-d %b %Y}"],
    "Prototype. Public data. Not investment advice. Not affiliated with any company shown.",
    "Built by Marcus Wallin.", extra_links=[("News room (AI prototype)", "news")]))
