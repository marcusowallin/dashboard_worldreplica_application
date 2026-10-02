"""T8: end-to-end integration test with mocked feeds and a mocked AI.

data (mocked FRED + ECB, real twins) -> AI tags (mocked GDELT + mocked Claude) -> model ->
the story page itself (via the app's navigation). Key numbers are recomputed by hand below.
"""
from datetime import date, datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import src.data_sources
import src.news_tagger
from src.data_sources import load_live_prices as REAL_LOADER
from src.model.run import run_all
from src.news_tagger import NewsStore, refresh, tagged_view
from src.twins import load_twins
from tests.test_data_sources import fake_get
from tests.test_tagger import FakeClient, H1, H2, tag

APP = str(Path(__file__).resolve().parent.parent / "app.py")
NEWS = str(Path(__file__).resolve().parent.parent / "news.py")

# Mocked prices (tests/test_data_sources.py): 27 Jul jet 3.582 USD/gal, Brent 92.00 USD/bbl;
# 22 Sep jet 4.354, Brent 114.89; ECB 1.1355.
#   dBrent = 22.89 * 7.9 = 180.831 USD/t; dJet = 0.772 * 331.8 = 256.1496; dCrack = 75.3186
# Lufthansa FY2027, stale 29% hedge, mix 48/81 gasoil, 33/81 Brent, g 0.8:
#   hB = 0.29*33/81 = 0.118148, hG = 0.29*48/81 = 0.171852
#   uB = 1 - 0.29 = 0.71;  uC = 1 - 0.8*0.171852 = 0.862519
#   per t = 0.71*180.831 + 0.862519*75.3186 = 128.390 + 64.964 = 193.354 USD
#   dFuel = 9.42m t * 193.354 = USD 1,821.39m -> EUR 1,604.04m at 1.1355
#   dEBIT = -0.4 * 1,604.04 = -641.62m; dNI = x 0.75 x (1 - 24/1,363) = -472.73m
#   dEPS = -472.73m / 1,198,342,268 = -0.39449 EUR/share -> -30.37% of 1.299


def by_hand_lh_fy27_stale():
    d_brent, d_crack = 22.89 * 7.9, 0.772 * 331.8 - 22.89 * 7.9
    u_b, u_c = 1 - 0.29, 1 - 0.8 * 0.29 * 48 / 81
    d_fuel_eur = 9_420_000 * (u_b * d_brent + u_c * d_crack) / 1.1355
    # minorities as stored in the twins: 1.76% (= 24 / 1,363 rounded to two decimals)
    d_ni = -(1 - 0.60) * d_fuel_eur * (1 - 0.25) * (1 - 0.0176)
    return d_ni / 1_198_342_268


@pytest.fixture()
def fake_world(monkeypatch):
    """Patch every outside dependency: price feeds, news feed, AI client."""
    monkeypatch.setattr(src.data_sources, "load_live_prices", lambda day, **kw: REAL_LOADER(day, fake_get, **kw))
    monkeypatch.setattr(src.news_tagger, "fetch_headlines", lambda: ([dict(H1), dict(H2)], None))
    client = FakeClient([tag(0, "jet fuel costs will top"),
                         tag(1, "hedging softens fuel spike", airlines=("iag",), direction="cost_down", severity=1)])
    monkeypatch.setattr(src.news_tagger, "make_client", lambda lookup=None: client)
    return client


def test_model_numbers_end_to_end():
    live = REAL_LOADER(date(2026, 7, 27), fake_get)
    out = run_all(load_twins(), live=live)
    r = out["results"]["FY2027"]["lufthansa"]["stale 29%"]
    assert r["d_eps"] == pytest.approx(by_hand_lh_fy27_stale(), rel=1e-6)
    assert r["d_eps"] == pytest.approx(-0.39449, abs=5e-5)
    assert r["d_eps_share"] == pytest.approx(-0.3037, abs=5e-4)
    assert r["d_eps"] < 0 and abs(r["d_eps_share"]) > 0.05          # material: well above 5% of consensus EPS


def test_news_pipeline_end_to_end(fake_world):
    store = NewsStore()
    refresh(store, datetime(2026, 9, 30, 9), client=src.news_tagger.make_client())
    view = tagged_view(store)
    assert fake_world.calls == 1
    assert view[0]["tag"]["airlines"] == ["lufthansa"] and view[0]["tag"]["evidence_ok"]
    assert view[1]["tag"]["direction"] == "cost_down"


def _html(at):
    return " ".join(h.proto.body for h in at.get("html"))


def test_page_end_to_end(fake_world):
    """App -> story page (answer from the model, live prices) and news page (refresh with mocked headlines and tags)."""
    import streamlit as st
    st.cache_data.clear()
    st.cache_resource.clear()
    at = AppTest.from_file(APP, default_timeout=90).run()
    assert not at.exception
    html = _html(at)
    assert "A hypothetical jet fuel rise of +USD 100/t" in html and "before any additional pass-through" in html
    detail = " ".join(m.value for m in at.markdown)
    assert "Data as of 22 Sep 2026" in html and "Prices to 29 Sep 2026" not in detail and "Prices to 22 Sep 2026" in detail
    assert 'id="step-07"' in html and html.index("fsm-hook") < html.index("fsm-hero-sentence")    # the answer comes last
    news = AppTest.from_file(NEWS, default_timeout=90).run()                          # the news room is its own page
    assert not news.exception
    news.button(key="cta-news").click().run()
    assert not news.exception
    html = _html(news)
    assert H1["title"] in html and "verified quote" in html and fake_world.calls == 1


def test_story_reads_bottom_up_and_ends_with_the_answer(fake_world):
    """The order of the chapters is the design: question first, evidence and analysis, assumptions, answer, meaning."""
    import re
    import streamlit as st
    st.cache_data.clear()
    st.cache_resource.clear()
    at = AppTest.from_file(APP, default_timeout=90).run()
    assert not at.exception
    html = _html(at)
    numbers = [int(n) for n in re.findall(r'fsm-step-no">STEP (\d+)</span>', html)]
    assert numbers == sorted(numbers) == [1, 2, 3, 4, 5, 6, 7, 8, 9]                    # no chapter out of order
    assert html.index("fsm-hook") < html.index('fsm-step-no">STEP 01') < html.index("fsm-hero-sentence")
    assert html.index('fsm-step-no">STEP 06') < html.index("fsm-hero-sentence") < html.index('fsm-step-no">STEP 08')   # evidence, assumptions, then the answer
    assert html.count('class="fsm-bridge"') == 8                                        # chapters 1-6, the answer, meaning
    hook_part = html[html.index("fsm-hook"):html.index('fsm-step-no">STEP 01')]
    assert "Yes:" not in hook_part and "net cost" not in hook_part and "hypothetical shock" in hook_part   # no answer; honest


def test_no_chart_on_any_page_can_be_zoomed(fake_world):
    """Dragging a rectangle zooms a chart in with no way back. Every chart figure must be locked (figure level, because
    Streamlit's theme can replace a template) and the config must keep the mouse wheel for page scrolling."""
    import json
    import streamlit as st
    from src.ui.charts import CONFIG
    st.cache_data.clear()
    st.cache_resource.clear()
    assert CONFIG["scrollZoom"] is False and CONFIG["doubleClick"] is False
    at = AppTest.from_file(APP, default_timeout=90).run()
    assert not at.exception
    charts = at.get("plotly_chart")
    assert len(charts) >= 7                                              # the story's charts (seven with the mocked feed)
    for chart in charts:
        layout = json.loads(chart.proto.spec)["layout"]
        assert layout["dragmode"] is False
        assert layout["xaxis"]["fixedrange"] is True and layout["yaxis"]["fixedrange"] is True
        assert json.loads(chart.proto.config)["scrollZoom"] is False


def test_the_word_pass_through_is_defined_before_it_is_used_on_the_story_page(fake_world):
    import streamlit as st
    from src.story.steps import PASS_THROUGH_DEFINITION
    st.cache_data.clear()
    st.cache_resource.clear()
    html = _html(AppTest.from_file(APP, default_timeout=90).run()).lower()
    first_use = html.index("pass-through")
    assert first_use == html.index(PASS_THROUGH_DEFINITION.lower()[:12])             # the first use IS the definition
