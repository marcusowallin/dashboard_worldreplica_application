"""Tests for Steps 9-10: scenario overrides, presets, falling-price wording, hero = steps under any setting, tornado."""
from datetime import date
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import src.data_sources
from src.data_sources import load_live_prices as REAL_LOADER
from src.model.run import AIRLINES
from src.story.costs import cost_cases, summary
from src.story.hero import build_hero, condition_sentence
from src.story.profit import profit_cases, span
from src.story.scenario import apply_overrides, preset_split
from src.story.steps import bill_step, comparison_step, profit_step, tornado_step
from src.story.tornado import base_params, gap, losses, tornado
from src.twins import get_model_value, load_twins
from src.ui.format import story_eur_m_range, story_pct_range
from tests.test_data_sources import fake_get

FX = 1.1355
TWINS = load_twins()
NEWS = str(Path(__file__).resolve().parent.parent / "news.py")
STORY = str(Path(__file__).resolve().parent.parent / "story.py")


def mag(rng):
    return tuple(sorted(abs(x) for x in rng))


# --- overrides and presets ---------------------------------------------------------------------------

def test_overrides_change_a_copy_only():
    s = apply_overrides(TWINS, pass_shift_pp=-10, lh_hedge=(35, 60))
    assert get_model_value(s, "afklm", "recapture_rate") == pytest.approx(0.75)
    assert get_model_value(s, "lufthansa", "hedge_ratio_fy27") == pytest.approx(0.35)
    assert get_model_value(s, "lufthansa", "hedge_ratio_fy27_upper") == pytest.approx(0.60)
    assert get_model_value(TWINS, "afklm", "recapture_rate") == pytest.approx(0.85)          # original untouched
    assert get_model_value(apply_overrides(TWINS, 50), "afklm", "recapture_rate") == 1.0       # clipped at 100%


def test_presets_split_like_the_benchmark():
    assert preset_split(200, (51.0, 49.0)) == (102.0, 98.0)
    assert preset_split(-100, (51.0, 49.0)) == (-51.0, -49.0)
    assert preset_split(50, (51.0, 49.0)) == (26.0, 24.0)


# --- falling prices ----------------------------------------------------------------------------------

def test_falling_price_wording_in_hero_and_steps():
    split = (-51.0, -49.0)
    hero = build_hero(TWINS, FX, split, as_of_label="x")
    assert hero["sentence"].startswith("A hypothetical jet fuel fall of −USD 100/t saves Lufthansa about *EUR")
    assert "passes on less of the saving" in hero["why"] and "would gain as much" in hero["why"]
    rise = build_hero(TWINS, FX, (51.0, 49.0), as_of_label="x")
    assert [r["share"] for r in hero["rows"]] == [r["share"] for r in rise["rows"]]          # same magnitudes
    c27 = cost_cases(TWINS, "FY2027", FX, split)
    from src.story.choices import net_cost_per_tonne
    bill = bill_step({a: summary(r, "gross") for a, r in c27.items()}, {a: summary(r, "net") for a, r in c27.items()},
                     {a: get_model_value(TWINS, a, "recapture_rate") for a in AIRLINES},
                     {a: summary(r, "net_at_low") for a, r in c27.items()}, net_cost_per_tonne(TWINS, FX, split), True)
    assert "the fall cuts" in bill["headline"] and "of the saving" in bill["headline"] and "better off" in bill["headline"]
    ps = profit_step(profit_cases(TWINS, "FY2027", FX, split), True)
    assert ps["headline"].startswith("Same fuel relief, different gain: margins rise by under 1 pp at all three")
    assert "+0.5 to +0.6 pp" in ps["body"]
    from src.story.robustness import loss_ranges
    from src.story.sensitivities import hedge_quality_swing
    cs = comparison_step(loss_ranges(TWINS, "FY2027", FX, split), hero["reasons"],
                         condition_sentence(hero["status"]["FY2027"], True), hedge_quality_swing(TWINS, FX, split), True)
    assert cs["headline"].startswith("Why the gain differs: against Air France-KLM")


def test_zero_move_makes_no_claims():
    hero = build_hero(TWINS, FX, (0.0, 0.0), as_of_label="x")
    assert "unchanged" in hero["sentence"] and hero["why"] == "" and hero["fy26"] == ""


# --- hero = steps under any slider setting -----------------------------------------------------------

@pytest.mark.parametrize("split,shift,hedge", [
    ((51.0, 49.0), 0, (29, 50)), ((102.0, 98.0), 0, (29, 50)), ((-51.0, -49.0), 0, (29, 50)),
    ((150.0, -30.0), -10, (35, 60)), ((20.0, 180.0), 15, (10, 40)), ((-120.0, 40.0), -30, (50, 50)),
])
def test_hero_matches_steps_under_any_setting(split, shift, hedge):
    twins = apply_overrides(TWINS, shift, hedge)
    hero = build_hero(twins, FX, split, as_of_label="x")
    costs = cost_cases(twins, "FY2027", FX, split)
    profits = profit_cases(twins, "FY2027", FX, split)
    for row in hero["rows"]:
        a = row["airline"]
        assert row["cost"] == story_eur_m_range(*mag(summary(costs[a], "net")))           # Step 5 = hero EUR
        assert row["share"] == story_pct_range(*mag(span(profits[a], "op_share")))       # Step 6 = hero %
        for c, p in zip(costs[a], profits[a]):
            assert p["d_ebit"] == pytest.approx(-c["net"])


# --- Step 9 tornado ---------------------------------------------------------------------------------

def test_tornado_base_and_ordering():
    split = (51.0, 49.0)
    result = tornado(TWINS, FX, split, (0.14, 0.76))
    swings = [b["swing"] for b in result["bars"]]
    assert swings == sorted(swings, reverse=True) and len(result["bars"]) == 14
    assert result["bars"][0]["label"].startswith("Air France-KLM pass-through")       # the largest lever
    assert tornado_step(result)["pass_through_largest"] is True
    # the base gap is the loss gap at the middle of Lufthansa's hedge range, peers central - by hand
    p = base_params(TWINS)
    assert p["lh_hedge"] == pytest.approx((0.29 + 0.50) / 2)
    assert result["base_gap"] == pytest.approx(gap(losses(TWINS, FX, split, p)))
    # each bar contains the base value
    assert all(b["low"] - 1e-12 <= result["base_gap"] <= b["high"] + 1e-12 for b in result["bars"])


def test_tornado_new_bars_persistence_lufthansa_book_and_pass_through_base():
    split = (51.0, 49.0)
    result = tornado(TWINS, FX, split, (0.14, 0.76))
    bars = {b["key"]: b for b in result["bars"]}
    assert {"persistence", "lh_book", "pt_base"} <= set(bars)
    # the model is linear in the move: half the shock persisting halves the gap exactly, and 100% is the base
    assert bars["persistence"]["low"] == pytest.approx(result["base_gap"] / 2)
    assert bars["persistence"]["high"] == pytest.approx(result["base_gap"])
    # Lufthansa's book: an options fade makes it lose MORE (gap up), all-gasoil LESS (gap down), the base sits between
    assert bars["lh_book"]["low"] < result["base_gap"] < bars["lh_book"]["high"]
    # pass-through on the market price shrinks every loss; the gap to the peers barely moves, but Lufthansa's own loss does
    assert bars["pt_base"]["lh_low"] < bars["pt_base"]["lh_high"] and bars["pt_base"]["swing"] < 0.01
    assert bars["pt_base"]["lh_swing"] > 0.04


def test_tornado_bar_ends_by_hand_for_lufthansa_profit():
    """+10% expected profit -> Lufthansa's loss shrinks by 1/1.1; the peers' are unchanged."""
    split = (51.0, 49.0)
    p = base_params(TWINS)
    base = losses(TWINS, FX, split, p)
    up = losses(TWINS, FX, split, {**p, "profit_factor": {**p["profit_factor"], "lufthansa": 1.1}})
    assert up["lufthansa"] == pytest.approx(base["lufthansa"] / 1.1) and up["iag"] == pytest.approx(base["iag"])


# --- the page: presets, reset, sliders ---------------------------------------------------------------

@pytest.fixture()
def page(monkeypatch):
    st.cache_data.clear()
    st.cache_resource.clear()
    monkeypatch.setattr(src.data_sources, "load_live_prices", lambda day, **kw: REAL_LOADER(day, fake_get, **kw))
    at = AppTest.from_file(STORY, default_timeout=60).run()
    yield at
    st.cache_data.clear()
    st.cache_resource.clear()


def _html(at):
    return " ".join(h.proto.body for h in at.get("html"))


def test_page_presets_and_reset(page):
    at = page
    assert not at.exception and "adds about" in _html(at)
    at.button(key="preset--100").click().run()
    assert not at.exception and "saves Lufthansa about" in _html(at)
    assert "Same fuel relief, different gain" in _html(at) and "changed in Step 9" in _html(at)
    at.button(key="preset-+200").click().run()
    assert "A hypothetical jet fuel rise of +USD 200/t" in _html(at)
    at.button(key="scenario-reset").click().run()
    assert "A hypothetical jet fuel rise of +USD 100/t" in _html(at) and "changed in Step 9" not in _html(at)


def test_page_sliders_drive_every_number(page):
    at = page
    at.slider(key="sc_pt").set_value(-20).run()
    twins = apply_overrides(TWINS, -20, (29, 50))
    assert not at.exception and "pass-through −20 pp" in _html(at)
    fx = REAL_LOADER(date(2026, 7, 27), fake_get)["fx"].data
    split = (float(at.session_state["sc_crude"]), float(at.session_state["sc_premium"]))
    expected = build_hero(twins, fx, split, as_of_label="x")["rows"][0]["cost"]
    assert f"*{expected}*".strip("*") in _html(at)


# --- the news room is its own page; the story's footer links to it ----------------------------------------------------

def test_page_news_room_and_footer(monkeypatch):
    import src.news_tagger as nt
    from tests.test_tagger import FakeClient, H1, H2, tag
    st.cache_data.clear()
    st.cache_resource.clear()
    monkeypatch.setattr(src.data_sources, "load_live_prices", lambda day, **kw: REAL_LOADER(day, fake_get, **kw))
    monkeypatch.setattr(nt, "fetch_headlines", lambda: ([dict(H1, domain="reuters.com", seen="20260930T080000Z"),
                                                         dict(H2, domain="ft.com", seen="20260930T090000Z")], None))
    monkeypatch.setattr(nt, "make_client", lambda lookup=None: None)
    story = AppTest.from_file(STORY, default_timeout=60).run()
    html = _html(story)
    assert not story.exception and "Prototype. Public data. Not investment advice." in html and "Built by Marcus Wallin" in html
    assert "Method &amp; sources" in html and 'href="news"' in html and "cta-news" not in html     # linked, not embedded
    at = AppTest.from_file(NEWS, default_timeout=60).run()
    assert "News tagging and web search unavailable" in _html(at)
    at.button(key="cta-news").click().run()
    assert "untagged" in _html(at) and "Reuters" in _html(at)        # outlet name, not the bare domain
    st.cache_resource.clear()
    client = FakeClient([tag(0, "jet fuel costs will top", driver="guidance"),
                         tag(1, "hedging softens fuel spike", airlines=("iag",), driver="hedging")])
    monkeypatch.setattr(nt, "make_client", lambda lookup=None: client)
    at = AppTest.from_file(NEWS, default_timeout=60).run()
    at.button(key="cta-news").click().run()
    html = _html(at)
    assert client.calls == 1 and "verified quote" in html and 'href="./#step-04"' in html and 'href="./#step-02"' in html
    st.cache_data.clear()
    st.cache_resource.clear()
