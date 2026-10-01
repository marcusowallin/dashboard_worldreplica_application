"""Tests for steps 4-5 (src/story/costs.py, cost_step / passthrough_step, range_rows chart)."""
import pytest

from src.model.run import AIRLINES
from src.story.costs import cost_cases, size_neutral, summary
from src.story.hero import build_hero
from src.story.robustness import loss_ranges
from src.story.steps import cost_step, passthrough_step
from src.twins import get_field, get_model_value, load_twins
from src.ui.charts import range_rows
from src.ui.format import story_eur_m_range

FX, SPLIT = 1.1355, (51.0, 49.0)
TWINS = load_twins()


def test_step5_net_equals_the_hero_exactly():
    """The euro figures in the answer and at the end of Step 5 come from the same numbers - to the last cent."""
    hero = build_hero(TWINS, FX, SPLIT, as_of_label="x")
    ranges = loss_ranges(TWINS, "FY2027", FX, SPLIT)
    costs = cost_cases(TWINS, "FY2027", FX, SPLIT)
    for row in hero["rows"]:
        a = row["airline"]
        net = summary(costs[a], "net")
        assert net == (ranges[a]["cost_low"], ranges[a]["cost_high"])          # exact floats
        assert story_eur_m_range(*net) == row["cost"]                          # same printed text


def test_gross_recovered_net_add_up_and_follow_the_printed_rate():
    for rows in cost_cases(TWINS, "FY2027", FX, SPLIT).values():
        for r in rows:
            assert r["recovered"] + r["net"] == pytest.approx(r["gross"])
            assert r["net_at_low"] >= r["net"]                                 # 50% keeps at least as much
    lh = cost_cases(TWINS, "FY2027", FX, SPLIT)["lufthansa"][0]
    assert lh["recovered"] == pytest.approx(0.60 * lh["gross"])


def test_lufthansa_2026_includes_the_options_case():
    rows = cost_cases(TWINS, "FY2026", FX, SPLIT)["lufthansa"]
    by_case = {r["case"]: r["gross"] for r in rows}
    assert set(by_case) == {"base", "company table"} and by_case["company table"] > by_case["base"]


def test_size_neutral_uses_printed_fy25_bases():
    neutral = size_neutral(TWINS, "iag", 500e6, 600e6)
    assert neutral["pct_opex"] == pytest.approx((500 / 28_189, 600 / 28_189))
    assert neutral["cents_per_ask"] == pytest.approx((500e6 / 351_435e6 * 100, 600e6 / 351_435e6 * 100))


def test_new_fy25_fields_are_level_1_with_page_and_quote():
    for a in AIRLINES:
        for f in ("operating_costs_fy25", "revenue_fy25", "ask_fy25"):
            field = get_field(TWINS, a, f)
            assert field["level"] == 1 and field["status"] == "found" and field["page"] and field["quote"]
    assert get_model_value(TWINS, "lufthansa", "ask_fy25") == 338_552e6


def test_step_texts():
    c27, c26 = cost_cases(TWINS, "FY2027", FX, SPLIT), cost_cases(TWINS, "FY2026", FX, SPLIT)
    g27 = {a: summary(r, "gross") for a, r in c27.items()}
    g26 = {a: summary(r, "gross") for a, r in c26.items()}
    neutral = {a: size_neutral(TWINS, a, *g27[a]) for a in AIRLINES}
    step = cost_step(g27, g26, neutral)
    assert step["relative"] == "about the same per seat-km as its peers"
    assert story_eur_m_range(*g27["lufthansa"]) in step["headline"] and len(step["body"].split()) <= 40
    p = passthrough_step({a: summary(r, "net") for a, r in c27.items()},
                         {a: get_model_value(TWINS, a, "recapture_rate") for a in AIRLINES},
                         {a: summary(r, "net_at_low") for a, r in c27.items()})
    assert "Air France-KLM, passing on circa 85%" in p["headline"] and "one quarter" in p["body"]
    assert story_eur_m_range(*summary(c27["lufthansa"], "net")) in p["headline"]


def test_range_rows_chart():
    fig = range_rows([{"label": "a", "low": 10, "high": 20, "color": "#2DD4E0", "text": "EUR 10-20m",
                       "marks": (15, 30), "mark_text": "50%"}], "EUR m")
    assert len(fig.data) == 3 and fig.layout.xaxis.range[1] == pytest.approx(30 * 1.35)


# --- Step 6: net cost -> operating profit -> net income -> EPS (reconciliation) -------------------------

def test_step6_chain_reconciles_with_steps_4_5_hero_and_core_model():
    from src.model.run import Scenario, run_all
    from src.story.profit import profit_cases
    core = run_all(TWINS, Scenario(d_brent=SPLIT[0], d_crack=SPLIT[1], usd_per_eur=FX))
    ranges = loss_ranges(TWINS, "FY2027", FX, SPLIT)
    for period in ("FY2026", "FY2027"):
        costs = cost_cases(TWINS, period, FX, SPLIT)
        profits = profit_cases(TWINS, period, FX, SPLIT)
        for a in AIRLINES:
            for c, p in zip(costs[a], profits[a]):
                t, m, n = p["tax"], p["minority"], p["shares"]
                assert p["d_ebit"] == pytest.approx(-c["net"])                     # Step 5 -> operating profit
                assert p["d_revenue"] == pytest.approx(c["recovered"])
                assert p["d_net_income"] == pytest.approx(p["d_ebit"] * (1 - t) * (1 - m))
                assert p["d_eps"] == pytest.approx(p["d_net_income"] / n)
                model = core["results"][period][a][p["case"]]                      # the v1 model, same inputs
                assert p["d_eps"] == pytest.approx(model["d_eps"], rel=1e-9)
                assert p["d_ebit"] == pytest.approx(model["d_ebit"], rel=1e-9)
            if period == "FY2027":                                                  # hero's % of expected profit
                shares = [-p["op_share"] for p in profits[a]]
                assert (min(shares), max(shares)) == pytest.approx((ranges[a]["low"], ranges[a]["high"]))


def test_step6_margin_and_eps_by_hand_for_iag_central():
    from src.story.profit import profit_cases
    p = next(r for r in profit_cases(TWINS, "FY2027", FX, SPLIT)["iag"] if r["case"] == "central")
    assert p["margin_before"] == pytest.approx(5_054 / 35_971)
    assert p["margin_after"] == pytest.approx((5_054e6 - p["net"]) / (35_971e6 + p["d_revenue"]))
    assert p["eps_share"] == pytest.approx(p["d_eps"] / 0.7839)
    assert p["eps_after"] == pytest.approx(0.7839 + p["d_eps"])


def test_profit_step_carries_the_same_shock_message():
    from src.story.profit import profit_cases
    from src.story.steps import profit_step
    step = profit_step(profit_cases(TWINS, "FY2027", FX, SPLIT))
    # LH -0.6..-0.5, AF-KLM -0.3..-0.2, IAG -0.8..-0.6 pp: a spread of 0.6 pp is not "similar", so it says what is true
    assert step["headline"].startswith("Same fuel shock, different damage: margins slip by under 1 pp at all three")
    assert "thin 5.2% margin" in step["headline"] and "9–11% of its 2027 operating profit" in step["headline"]
    assert len(step["body"].split()) <= 40


# --- Step 8 sensitivities (reconcile with Steps 4-6) ------------------------------------------------------

def test_pass_through_sensitivity_matches_a_recomputed_chain():
    """+10 pp of pass-through, recomputed through the hero's own loss_share, lowers net cost by 0.10 x gross."""
    from src.story.robustness import benchmark_market, case_inputs, loss_share
    from src.story.sensitivities import pass_through
    pt = pass_through(TWINS, FX, SPLIT)
    market = benchmark_market(SPLIT, FX)
    drops = []
    for case in ("stale 29%", "reported ~50%"):
        base_in = case_inputs(TWINS, "lufthansa", "FY2027", case, market)
        up_in = case_inputs(TWINS, "lufthansa", "FY2027", case, market, recapture=base_in["recapture"] + 0.10)
        drops.append((loss_share(base_in, market) - loss_share(up_in, market)) * base_in["base"])
    assert pt["per_step"] == pytest.approx((min(drops), max(drops)))
    gross = [r["gross"] for r in cost_cases(TWINS, "FY2027", FX, SPLIT)["lufthansa"]]
    assert pt["at_peer_rate"] == pytest.approx((0.25 * min(gross), 0.25 * max(gross)))   # 85% - 60%


def test_hedge_cover_effect_is_the_difference_of_the_two_step5_cases():
    from src.story.sensitivities import hedge_cover
    rows = {r["case"]: r for r in cost_cases(TWINS, "FY2027", FX, SPLIT)["lufthansa"]}
    cover = hedge_cover(TWINS, FX, SPLIT)
    assert cover["net_difference"] == pytest.approx(rows["stale 29%"]["net"] - rows["reported ~50%"]["net"])
    assert cover["net_difference"] > 0
    assert cover["share"] == pytest.approx(cover["net_difference"] / 2_281e6)


def test_margin_multiplier_and_hedge_quality_swing():
    from src.story.sensitivities import hedge_quality_swing, margin_multiplier
    m = margin_multiplier(TWINS, FX, SPLIT)
    assert m["margin_us"] == pytest.approx(2_281 / 44_153) and m["margin_peer"] == pytest.approx(5_054 / 35_971)
    assert 1.5 < m["ratio"][0] < m["ratio"][1] < 4
    hq = hedge_quality_swing(TWINS, FX, SPLIT)
    assert hq["low"] < 0 < hq["high"] and hq["max_abs"] == pytest.approx(max(-hq["low"], hq["high"]))


def test_comparison_and_so_what_text():
    from src.story.hero import build_hero, condition_sentence
    from src.story.sensitivities import hedge_cover, hedge_quality_swing, margin_multiplier, pass_through
    from src.story.steps import comparison_step, so_what_cards
    hero = build_hero(TWINS, FX, SPLIT, as_of_label="x")
    hq = hedge_quality_swing(TWINS, FX, SPLIT)
    step = comparison_step(loss_ranges(TWINS, "FY2027", FX, SPLIT), hero["reasons"],
                           condition_sentence(hero["status"]["FY2027"]), hq)
    assert step["headline"] == ("Why the hit differs: against Air France-KLM it is mainly pass-through, "
                                "against IAG it is mainly margin cushion.")          # the numbers are in the chart
    assert "9–11%" not in step["headline"]                                             # Step 6 already said them
    assert "Pass-through is how much of the extra cost goes into fares" in step["body"]
    assert "margin cushion is how much profit there is to absorb it" in step["body"]
    assert "about two-thirds" in step["body"]
    cards = so_what_cards(margin_multiplier(TWINS, FX, SPLIT), pass_through(TWINS, FX, SPLIT),
                          hedge_cover(TWINS, FX, SPLIT), hq)
    assert [c["title"] for c in cards] == ["Thin margins amplify fuel shocks", "Pricing power is the biggest lever",
                                           "2027 hedge cover still matters for the level",
                                           "Disclosure gaps limit the comparison"]
    assert all(c["note"].startswith("Observation:") and c["number"] for c in cards)


def _synthetic_p27(margin_moves):
    """profit_step input with one row per airline; margin_moves = {airline: margin change as a fraction}."""
    return {a: [{"margin_pp": m, "margin_before": 0.06, "op_share": -0.05, "eps_share": -0.06, "d_eps": -0.1}]
            for a, m in margin_moves.items()}


def test_profit_step_says_similar_only_when_all_three_margins_are_close():
    from src.story.steps import profit_step
    close = profit_step(_synthetic_p27({"lufthansa": -0.0050, "afklm": -0.0045, "iag": -0.0055}))
    assert "margins slip by similar amounts" in close["headline"]            # spread 0.1 pp
    spread = profit_step(_synthetic_p27({"lufthansa": -0.0060, "afklm": -0.0025, "iag": -0.0080}))
    assert "similar" not in spread["headline"]                                # spread 0.55 pp: say what is true
    assert "under 1 pp at all three" in spread["headline"]
    big = profit_step(_synthetic_p27({"lufthansa": -0.0150, "afklm": -0.0140, "iag": -0.0025}))
    assert "similar" not in big["headline"] and "under 1 pp" not in big["headline"]
