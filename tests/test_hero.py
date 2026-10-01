"""Tests for the hero (src/story/hero.py), the story rounding helpers and the story page (story.py)."""
from datetime import date
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import src.data_sources
from src.data_sources import load_live_prices as REAL_LOADER
from src.model.run import Scenario, run_all
from src.story.hero import (
    build_hero, company_reports_as_of, condition_sentence, consensus_as_of, fy26_sentence, live_line,
    ranking_status, why_sentence,
)
from src.story.robustness import loss_ranges
from src.twins import load_twins
from src.ui.format import (
    approx_fraction, story_eur_bn_range, story_eur_m, story_eur_m_range, story_pct, story_pct_range,
)
from tests.test_data_sources import fake_get

FX = 1.1355
TWINS = load_twins()
STORY = str(Path(__file__).resolve().parent.parent / "story.py")


# --- story rounding (whole numbers, decision 30 Sep 2026) ------------------------------------------

def test_story_rounding_steps():
    assert story_eur_m(87.4e6) == "EUR 87m"            # below 100m: nearest 1m
    assert story_eur_m(219.4e6) == "EUR 220m"          # below 1,000m: nearest 5m
    assert story_eur_m(1_718e6) == "EUR 1,720m"        # above: nearest 10m
    assert story_eur_m_range(218.5e6, 266.4e6) == "EUR 220–265m"
    assert story_eur_bn_range(1_613e6, 2_266e6) == "EUR 1.6–2.3bn"


def test_story_percent_rounds_half_up_and_collapses():
    assert story_pct(0.045) == "5%"                    # Python's round() would give 4
    assert story_pct_range(0.096, 0.117) == "10–12%"
    assert story_pct_range(0.005, 0.014) == "1%"       # both ends round to 1
    assert story_pct_range(-0.011, -0.006) == "−1%"


def test_approx_fraction_words():
    assert approx_fraction(0.68) == "about two-thirds" and approx_fraction(0.52) == "about half"
    assert approx_fraction(0.42) == "about 40%"


# --- hero numbers come from the model ------------------------------------------------------------

def test_hero_numbers_match_the_model_and_each_other():
    hero = build_hero(TWINS, FX, as_of_label="29 Sep 2026")
    r = loss_ranges(TWINS, "FY2027", FX)["lufthansa"]
    cost, share = story_eur_m_range(r["cost_low"], r["cost_high"]), story_pct_range(r["low"], r["high"])
    lh_row = hero["rows"][0]
    assert lh_row == {"airline": "lufthansa", "cost": cost, "share": share}
    assert f"*{cost}*" in hero["sentence"] and share in hero["sentence"]          # sentence == number row
    assert hero["sentence"].startswith("Scenario: jet fuel +USD 100/t.")
    # net cost = loss share x expected operating profit (bottom-up chain)
    assert r["cost_high"] == pytest.approx(r["high"] * 2_281e6)


def test_hero_today_uses_the_at_printed_variant_with_afklm_condition():
    hero = build_hero(TWINS, FX)
    assert hero["status"]["FY2027"]["status"] == "at_printed"
    assert set(hero["status"]["FY2027"]["flips"]) == {"afklm"}
    assert "If Air France-KLM's pass-through fell below about two-thirds, it would be hit as hard." in hero["why"]
    assert hero["reasons"] == {"afklm": "recapture", "iag": "profit base"}
    assert "passes on less of the cost than Air France-KLM" in hero["why"]
    assert "runs on a much thinner margin than IAG" in hero["why"]          # 5.2% vs 14.1% expected 2027


def test_ranking_status_everywhere_when_recapture_is_fixed(monkeypatch):
    monkeypatch.setattr("src.story.robustness.RECAPTURE_LOW", 1.0)
    monkeypatch.setattr("src.story.hero.RECAPTURE_LOW", 1.0)
    assert ranking_status(TWINS, "FY2027", FX)["status"] == "everywhere"


# --- wording variants -------------------------------------------------------------------------

def test_condition_variants():
    assert condition_sentence({"status": "everywhere", "flips": {}}) == "This holds in every case we model."
    assert "depends mainly on hedging" in condition_sentence({"status": "not_settled", "flips": {}})
    both = condition_sentence({"status": "at_printed", "flips": {"afklm": 0.68, "iag": 0.52}})
    assert both == ("If Air France-KLM's pass-through fell below about two-thirds or IAG's pass-through fell "
                    "below about half, they would be hit as hard.")


def test_why_variants():
    assert why_sentence({"afklm": "recapture", "iag": "profit base"}, {"lufthansa": 0.05, "afklm": 0.06, "iag": 0.08}) \
        == "Mainly because it passes on less of the cost than Air France-KLM and runs on a thinner margin than IAG."
    assert why_sentence({"afklm": "recapture", "iag": "recapture"}) == \
        "Mainly because it passes on less of the cost than both peers."
    partly = why_sentence({"afklm": "recapture", "iag": None})
    assert "than Air France-KLM" in partly and "Against IAG the main reason depends" in partly
    assert "depend on the assumptions" in why_sentence({"afklm": None, "iag": None})


def test_fy26_sentence_is_one_sentence_per_variant():
    ranges = {"lufthansa": {"low": 0.017, "high": 0.034}, "afklm": {"low": 0.006, "high": 0.012},
              "iag": {"low": 0.005, "high": 0.014}}
    either = fy26_sentence(ranges, {"status": "at_printed", "flips": {"afklm": 0.8, "iag": 0.55}})
    assert either == ("Rest of 2026: Lufthansa 2–3%, Air France-KLM and IAG about 1% of expected profit, "
                      "but lower pass-through could put either level with it.")
    assert fy26_sentence(ranges, {"status": "not_settled", "flips": {}}).endswith("the order is not settled.")
    assert fy26_sentence(ranges, {"status": "everywhere", "flips": {}}).endswith("every case we model.")
    for s in (either,):
        assert s.count(". ") == 0


def test_live_line_wording_and_sum_of_periods():
    live = REAL_LOADER(date(2026, 7, 27), fake_get)
    out = run_all(TWINS, Scenario(usd_per_eur=FX), live)
    text = live_line(out, live["moves"])
    assert "If today's price held for all of 2026–27, before any additional pass-through" in text
    lh = out["results"]
    low = min(r["d_fuel_eur"] for r in lh["FY2026"]["lufthansa"].values()) + \
        min(r["d_fuel_eur"] for r in lh["FY2027"]["lufthansa"].values())
    high = max(r["d_fuel_eur"] for r in lh["FY2026"]["lufthansa"].values()) + \
        max(r["d_fuel_eur"] for r in lh["FY2027"]["lufthansa"].values())
    assert story_eur_bn_range(low, high) in text


def test_as_of_helpers():
    assert consensus_as_of(TWINS) == "2026-09-29"
    assert company_reports_as_of(TWINS) == "2026-08-04"


# --- the story page ------------------------------------------------------------------------------

@pytest.fixture()
def fresh_caches():
    st.cache_data.clear()
    st.cache_resource.clear()
    yield
    st.cache_data.clear()
    st.cache_resource.clear()


def test_story_page_shows_the_hero_with_live_prices(monkeypatch, fresh_caches):
    calls = []
    monkeypatch.setattr(src.data_sources, "load_live_prices",
                        lambda day, **kw: calls.append(day) or REAL_LOADER(day, fake_get, **kw))
    at = AppTest.from_file(STORY, default_timeout=30).run()
    assert not at.exception
    html = " ".join(h.proto.body for h in at.get("html"))
    assert "Scenario: jet fuel +USD 100/t." in html and "before any additional pass-through" in html
    assert "Jet fuel is up 22%" in html and "the jet premium" in html and "Hedges roll off" in html  # steps 1-3
    assert "After hedging, the scenario adds" in html and "Passing on about 60% leaves Lufthansa" in html  # 4-5
    assert "Same fuel shock, different damage" in html and "Operating margin" in html and "EPS vs consensus" in html  # step 6
    assert "Why the hit differs" in html and "Thin margins amplify fuel shocks" in html  # 7-8
    assert 'class="fsm-chip warn"' in html and ">LOW<" in html and "What raises it" in html
    assert len(calls) == 1
    at.button(key="update-data").click().run()                 # Update data -> re-fetch once
    assert not at.exception and len(calls) == 2
    at.button(key="update-data").click().run()                 # within the cooldown -> no fetch
    assert len(calls) == 2
    assert "next update possible" in " ".join(h.proto.body for h in at.get("html"))


def test_story_page_survives_feeds_down(monkeypatch, fresh_caches):
    def broken(url, **kwargs):
        raise ConnectionError("offline")
    monkeypatch.setattr(src.data_sources, "load_live_prices", lambda day, **kw: REAL_LOADER(day, broken, **kw))
    at = AppTest.from_file(STORY, default_timeout=30).run()
    assert not at.exception
    html = " ".join(h.proto.body for h in at.get("html"))
    assert "Live feeds unavailable" in html and "Scenario: jet fuel +USD 100/t." in html
    assert "planning rate" in html
    assert "Live prices are unavailable right now." in html and "Hedges roll off" in html
