"""Tests for the design system (src/ui/): formats, contrast, icons, components, charts, style-test page."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.ui import components as ui
from src.ui.charts import contribution_bars, range_bars, register_template
from src.ui.css import page_css
from src.ui.format import eur_bn, eur_m, eur_m_range, eur_per_share, pct, pct_range, pp, usd_per_t
from src.ui.icons import BITMAPS, icon_img, icon_svg
from src.ui.theme import AIRLINE_LABELS, COLORS, contrast_ratio, hex_to_rgba

ROOT = Path(__file__).resolve().parent.parent


# --- number formats ------------------------------------------------------------------------------

def test_formats():
    assert eur_m(1_334.4e6) == "EUR 1,334m" and eur_m(-534e6) == "−EUR 534m"
    assert eur_m(534e6, signed=True) == "+EUR 534m"
    assert eur_bn(1_613e6) == "EUR 1.6bn"
    assert pct(0.1172) == "11.7%" and pct(-0.096) == "−9.6%" and pct(0.05, signed=True) == "+5.0%"
    assert pp(0.0485) == "+4.9 pp"
    assert eur_per_share(-0.3281) == "−EUR 0.33"
    assert usd_per_t(271.2) == "+USD 271/t"


def test_ranges_and_missing_values():
    assert pct_range(0.117, 0.096) == "9.6–11.7%"                   # sorted, en dash
    assert pct_range(0.1, 0.1) == "10.0%"
    assert pct_range(-0.117, -0.096) == "−11.7% to −9.6%"
    assert eur_m_range(1_334e6, 1_718e6) == "EUR 1,334–1,718m"
    for f in (eur_m, eur_bn, pct, pp, eur_per_share, usd_per_t):
        assert f(None) == "n/a"                                         # missing is never shown as 0
    assert pct_range(None, 0.1) == "n/a"


# --- accessibility --------------------------------------------------------------------------------

def test_contrast_ratio_reference_values():
    assert contrast_ratio("#FFFFFF", "#000000") == pytest.approx(21)
    assert contrast_ratio("#777777", "#777777") == pytest.approx(1)


@pytest.mark.parametrize("token", ["text", "text_2", "text_3", "accent", "peer_a", "peer_b",
                                   "cost_up", "cost_down", "warn"])
def test_text_colours_meet_wcag_aa_on_every_surface(token):
    for surface in ("bg", "surface", "surface_2"):
        assert contrast_ratio(COLORS[token], COLORS[surface]) >= 4.5, (token, surface)


def test_us_is_named_in_text():
    assert "(us)" in AIRLINE_LABELS["lufthansa"]
    assert "US" in ui.airline_name("lufthansa") and "US" not in ui.airline_name("iag")


# --- icons ----------------------------------------------------------------------------------------

def test_icons_are_7x7_and_drawn_from_bitmaps():
    for name, rows in BITMAPS.items():
        assert len(rows) == 7 and all(len(r) == 7 and set(r) <= {"#", "."} for r in rows), name
        svg = icon_svg(name)
        assert svg.count("<circle") == 49 and svg.count(f'fill="{COLORS["accent"]}"') == "".join(rows).count("#")


def test_icon_img_is_decorative_data_uri():
    html = icon_img("price")
    assert html.startswith("<img") and "data:image/svg+xml;base64," in html and 'alt=""' in html
    with pytest.raises(KeyError):
        icon_svg("no-such-icon")


# --- components -----------------------------------------------------------------------------------

def test_components_escape_text():
    evil = '<script>alert(1)</script>"'
    for html in (ui.eyebrow(evil), ui.chip(evil, evil, note=evil), ui.hero_line(evil),
                 ui.step_header(1, evil, evil, evil, "price"), ui.takeaway_card(evil, evil, "flag"),
                 ui.airline_card("iag", [{"label": evil, "before": evil, "after": evil, "change": evil}]),
                 ui.hero_text(evil, evil, evil, evil), ui.source_marker(evil), ui.link_button(evil, evil)):
        assert "<script>" not in html and "&lt;script&gt;" in html


def test_chip_note_is_focusable_and_readable():
    html = ui.chip("Confidence", "LOW", tone="warn", note="Why LOW: not verified.")
    assert 'tabindex="0"' in html and "fsm-tip" in html and "aria-label" in html and "warn" in html
    assert "tabindex" not in ui.chip("Headline year", "2027")


def test_hero_marks_key_number_in_accent():
    html = ui.hero_text("The answer", "costs Lufthansa *10-12%* of profit", "why", "label")
    assert "<em>10-12%</em>" in html


def test_step_header_has_anchor_for_skip_link():
    assert 'id="step-07"' in ui.step_header(7, "x", "y", "z", "compare")
    assert 'href="#step-07"' in ui.skip_link("Skip to the comparison", 7)


def test_number_row_marks_only_lufthansa_as_us():
    html = ui.number_row([{"airline": "lufthansa", "value": "9.6%", "caption": "c"},
                          {"airline": "iag", "value": "3.4%", "caption": "c"}])
    assert html.count('class="fsm-num us"') == 1 and html.count('class="fsm-num"') == 1


# --- CSS and charts --------------------------------------------------------------------------------

def test_css_uses_tokens_and_respects_reduced_motion():
    css = page_css()
    assert f"--fsm-accent: {COLORS['accent']};" in css
    assert "prefers-reduced-motion" in css and "@media (max-width: 640px)" in css
    assert "<" not in css                                               # nothing that could close <style>


def test_hex_to_rgba():
    assert hex_to_rgba("#2DD4E0", 0.1) == "rgba(45,212,224,0.1)"


def test_range_bars_one_solid_trace_per_airline_plus_extension():
    rows = [{"airline": "lufthansa", "low": 0.096, "high": 0.117, "ext_high": 0.146},
            {"airline": "iag", "low": 0.034, "high": 0.05, "ext_high": None}]
    fig = range_bars(rows, "axis")
    assert len(fig.data) == 3                                           # LH solid + extension, IAG solid
    assert fig.layout.template.layout.plot_bgcolor == COLORS["surface"]
    texts = [a.text for a in fig.layout.annotations]
    assert "Lufthansa (us)" in texts and any(t.startswith("10–12% · up to 15% at 50%") for t in texts)


def test_contribution_bars_stack_every_factor():
    fig = contribution_bars([{"peer": "afklm", "parts": {"recapture": 0.064, "hedge ratio": 0.009}}], "pp")
    assert [t.name for t in fig.data] == ["pass-through", "margin cushion", "hedge cover",
                                          "hedge quality (peers' mix unknown)"]
    assert fig.data[0].x[0] == pytest.approx(6.4)


def test_register_template_is_idempotent():
    assert register_template() == register_template() == "fsm"


# --- the style-test page runs -------------------------------------------------------------------

def test_style_test_page_runs_without_network(monkeypatch):
    from datetime import date
    from streamlit.testing.v1 import AppTest
    import src.data_sources as ds
    monkeypatch.setattr(ds, "fetch_usd_per_eur",
                        lambda *a, **k: SimpleNamespace(data=1.1355, as_of=date(2026, 9, 30)))
    at = AppTest.from_file(str(ROOT / "scripts" / "style_test.py"), default_timeout=30).run()
    assert not at.exception
    assert any("fsm-hero-sentence" in h.proto.body for h in at.get("html"))


def test_story_margin_pp_and_eps_formats():
    from src.ui.format import story_eur_share_range, story_margin, story_margin_range, story_pp_range
    assert story_margin(0.0517) == "5.2%" and story_margin_range(0.0454, 0.0466) == "4.5–4.7%"
    assert story_pp_range(-0.0063, -0.0051) == "−0.6 to −0.5 pp" and story_pp_range(-0.003, -0.003) == "−0.3 pp"
    assert story_eur_share_range(1.138, 1.170) == "EUR 1.14–1.17"
    assert story_eur_share_range(-0.161, -0.129) == "−EUR 0.16 to −EUR 0.13"
