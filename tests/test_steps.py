"""Tests for story steps 1-3 (src/story/exposure.py, src/story/steps.py) and their charts."""
from datetime import date

import pytest

from src.data_sources import load_live_prices as REAL_LOADER
from src.model.run import BASELINE_DAY
from src.story.exposure import chart_rows, exposure, premium_exposed_range, tonnes_split, unhedged_range
from src.story.steps import exposure_step, price_step, split_step
from src.twins import load_twins
from src.ui.charts import exposure_bars, price_lines, split_bars
from src.ui.theme import AIRLINE_LABELS
from tests.test_data_sources import fake_get

FX = 1.1355
TWINS = load_twins()
LIVE = REAL_LOADER(date(2026, 7, 27), fake_get)


def test_tonnes_split_adds_up_and_matches_unprotected_shares():
    """Lufthansa FY2027 at 29%: by hand from the printed mix (48 gasoil, 33 Brent of 81) and g = 0.8."""
    mix = {"gasoil": 48 / 81, "brent": 33 / 81, "jet": 0.0}
    t = tonnes_split([{"volume_t": 9.42e6, "hedge_ratio": 0.29}], mix, 0.8)
    assert t["unhedged"] == pytest.approx(9.42e6 * 0.71)
    assert t["protected"] == pytest.approx(9.42e6 * 0.29 * 0.8 * 48 / 81)
    assert t["protected"] + t["premium_open"] + t["unhedged"] == pytest.approx(9.42e6)
    # premium-exposed tonnes = V x u_crack of the model (1 - g x hG - hJ)
    assert t["unhedged"] + t["premium_open"] == pytest.approx(9.42e6 * (1 - 0.8 * 0.29 * 48 / 81))


def test_exposure_hides_undisclosed_mix_and_shows_both_lufthansa_cases():
    e = exposure(TWINS, FX)
    assert [r["case"] for r in e["lufthansa"]["FY2027"]] == ["stale 29%", "reported ~50%"]
    assert e["afklm"]["FY2027"][0]["protected"] is None and e["iag"]["FY2026"][0]["premium_open"] is None
    assert unhedged_range(e["lufthansa"]["FY2027"]) == pytest.approx((9.42e6 * 0.5, 9.42e6 * 0.71))
    assert premium_exposed_range(e["afklm"]["FY2027"]) is None
    rows = chart_rows(e, AIRLINE_LABELS)
    assert len(rows) == 7 and rows[0]["label"] == "Lufthansa · rest of 2026"
    assert rows[-1]["undisclosed"] == pytest.approx(e["iag"]["FY2027"][0]["hedged"])


def test_price_step_wording():
    step = price_step(LIVE["moves"], 100)
    assert step["headline"] == "Jet fuel is up 22% (+USD 256/t) since 27 July."   # fake feed: 3.582 -> 4.354 USD/gal
    assert "same standard shock" in step["body"] and "+USD 100/t" in step["body"] and "2.6 times that" in step["body"]
    down = dict(LIVE["moves"], d_jet=-50.0)
    assert price_step(down, 100)["headline"].startswith("Jet fuel is down")
    assert "unavailable" in price_step(None, 100)["headline"] and "+USD 100/t" in price_step(None, 100)["body"]


def test_split_step_words_and_signs():
    step = split_step(LIVE["moves"], (40, 60))
    # fake feed: Brent +180.8 of jet +256.1 = 71% -> not near a simple fraction, so a rounded percentage
    assert step["headline"] == "About 70% of today's rise is crude, about 30% the jet premium."
    mixed = dict(LIVE["moves"], d_brent=120.0, d_crack=-20.0)
    assert "premium -USD 20/t" in split_step(mixed, (40, 60))["headline"]
    assert "+40 crude / +60 premium" in split_step(None, (40, 60))["body"]


def test_exposure_step_states_the_roll_off():
    step = exposure_step(exposure(TWINS, FX))
    assert "in 2027." in step["headline"] and "4.7–6.7m t" in step["headline"]
    assert "7.2–8.1m t" in step["body"] and len(step["body"].split()) <= 40


def test_step_charts_build():
    fig = price_lines(LIVE["prices"], BASELINE_DAY, 100)
    assert len(fig.data) == 2 and any("scenario" in a.text for a in fig.layout.annotations)
    fig = split_bars([{"label": "Scenario", "brent": 40, "crack": 60}])
    assert [t.name for t in fig.data] == ["crude (Brent)", "jet premium"]
    fig = exposure_bars(chart_rows(exposure(TWINS, FX), AIRLINE_LABELS))
    assert {t.name for t in fig.data} == {"hedged, protected", "hedged, premium open",
                                          "hedged, mix unknown", "unhedged"}


# --- the opening and the closing line of the argument (design review 2 Oct 2026) ------------------------------

def test_hook_asks_the_question_and_gives_no_answer():
    from src.story.steps import hook_text
    up = hook_text(LIVE["moves"])
    assert up["headline"] == "Jet fuel is up 22% since 27 July. Is Lufthansa hit harder than its rivals?"
    down = hook_text(dict(LIVE["moves"], d_jet=-50.0))
    assert down["headline"].startswith("Jet fuel is down") and "gain less" in down["headline"]
    assert "unequally" in hook_text(None)["headline"]                       # feeds down: no invented number
    for text in (up, down, hook_text(None)):
        said = (text["headline"] + " " + text["body"]).lower()
        assert not any(word in said for word in ("eur ", "%  of", "thinner", "hit hardest", "pass-through rate"))
    assert "%" not in up["body"]


def test_materiality_uses_the_five_percent_rule_per_hedging_case():
    from src.story.steps import materiality_step

    def rows(*shares):
        return [{"op_share": s, "eps_share": s} for s in shares]

    out = materiality_step({"lufthansa": rows(-0.09, -0.11), "afklm": rows(-0.03, -0.04), "iag": rows(-0.03, -0.055)})
    assert out["status"] == {"lufthansa": "yes", "afklm": "no", "iag": "depends"}
    assert "at least 5%" in out["sentence"] and "IAG: depends on the assumptions" in out["sentence"]
    # either measure can trigger it: operating profit share small, EPS share large
    mixed = materiality_step({a: [{"op_share": -0.01, "eps_share": -0.06}] for a in ("lufthansa", "afklm", "iag")})
    assert set(mixed["status"].values()) == {"yes"}


def test_bridge_and_hook_are_escaped_html():
    from src.ui.components import bridge, hook
    assert bridge("a <b>") == '<p class="fsm-bridge">a &lt;b&gt;</p>'
    assert "<script>" not in hook("x", "<script>", "y")


def test_materiality_says_close_when_a_no_is_a_near_miss():
    from src.story.steps import materiality_step

    def rows(op, eps):
        return [{"op_share": op, "eps_share": eps}]

    out = materiality_step({"lufthansa": rows(-0.10, -0.11), "afklm": rows(-0.0323, -0.0499), "iag": rows(-0.02, -0.02)})
    assert out["status"] == {"lufthansa": "yes", "afklm": "close", "iag": "no"}
    assert "Air France-KLM: no, but close (up to 4.9%)" in out["sentence"] and "IAG: no;" not in out["sentence"]
    assert out["sentence"].endswith("IAG: no.")


def test_tornado_step_headline_is_plain_and_defines_the_gap():
    from src.story.steps import tornado_step
    bars = [{"label": "Air France-KLM pass-through 50%-85%", "low": 0.02, "high": 0.064, "swing": 0.044,
             "lh_low": 0.09, "lh_high": 0.1, "lh_swing": 0.01},
            {"label": "Lufthansa 2027 hedge cover 29%-50%", "low": 0.05, "high": 0.07, "swing": 0.02,
             "lh_low": 0.09, "lh_high": 0.115, "lh_swing": 0.025}]
    out = tornado_step({"bars": bars, "base_gap": 0.064})
    assert out["headline"] == ("The order depends most on pass-through: Air France-KLM's alone changes the gap "
                               "between Lufthansa and its peers by 4 pp.")
    assert "how many points more of its expected 2027 operating profit Lufthansa loses" in out["body"]
    assert "(6 pp at the base case)" in out["body"] and "No single assumption closes the gap." in out["body"]
