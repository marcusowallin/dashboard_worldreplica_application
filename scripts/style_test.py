"""D1 style test: every component of the design system on one page (not the story itself).

Run from the project root:  streamlit run scripts/style_test.py --server.port 8502
Numbers shown come from the model (benchmark +USD 100/t, +40 Brent / +60 crack), not typed in; the company
figures behind them are still unverified. Layout and wording are placeholders for D2-D8.
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.data_sources import fetch_usd_per_eur  # noqa: E402
from src.story.robustness import BENCHMARK_SPLIT, PEERS, attribution, loss_ranges  # noqa: E402
from src.story.yardstick import expected_operating_profit  # noqa: E402
from src.twins import load_twins  # noqa: E402
from src.ui import components as ui  # noqa: E402
from src.ui.charts import CONFIG, contribution_bars, range_bars  # noqa: E402
from src.ui.css import inject  # noqa: E402
from src.ui.format import eur_m, eur_m_range, pct, pct_range  # noqa: E402
from src.ui.icons import BITMAPS, icon_img  # noqa: E402
from src.ui.theme import COLORS, contrast_ratio  # noqa: E402

st.set_page_config(page_title="Style test - Airline fuel shock monitor", layout="wide")
inject()

FALLBACK_FX = 1.151   # Lufthansa's printed planning rate, used only if the ECB feed is down (labelled)


@st.cache_data(ttl=6 * 3600)
def _fx():
    result = fetch_usd_per_eur()
    return (result.data, f"ECB, {result.as_of:%d %b %Y}") if result.data else (FALLBACK_FX, "LH planning rate - ECB feed down")


fx, fx_label = _fx()
twins = load_twins()
ranges = loss_ranges(twins, "FY2027", fx)
ranges_26 = loss_ranges(twins, "FY2026", fx)
base_date = expected_operating_profit(twins, "lufthansa", "FY2027")["as_of"]

st.html(ui.eyebrow("Style test · D1 design system") +
        '<p class="fsm-label">Components only. Figures from the model on the USD 100/t benchmark '
        f"(+{BENCHMARK_SPLIT[0]:.0f} Brent / +{BENCHMARK_SPLIT[1]:.0f} crack, USD/EUR {fx:.4f}, {fx_label}); "
        "company figures not yet verified. Wording is draft.</p>")

# --- hero -------------------------------------------------------------------------------------
with st.container(key="hero"):
    lh, af, ia = ranges["lufthansa"], ranges["afklm"], ranges["iag"]
    peers_low, peers_high = min(af["low"], ia["low"]), max(af["high"], ia["high"])
    st.html(ui.hero_text(
        "The answer · FY2027",
        f"A USD 100/t rise in jet fuel costs Lufthansa *{pct_range(lh['low'], lh['high'], 0)}* of its expected "
        f"2027 operating profit, versus {pct_range(peers_low, peers_high, 0)} for Air France-KLM and IAG.",
        "Mainly because it passes on less of the cost than Air France-KLM and earns less profit per tonne of fuel "
        "than IAG. If Air France-KLM's pass-through fell below about two-thirds, it would be hit as hard.",
        f"vs expected 2027 operating profit (company guidance or analyst consensus, as of {base_date})"))
    st.html(ui.number_row([
        {"airline": a, "value": pct_range(ranges[a]["low"], ranges[a]["high"]),
         "caption": f"of expected 2027 operating profit; up to {pct(ranges[a]['ext_high'])} at 50% pass-through"}
        for a in ("lufthansa", "afklm", "iag")]))
    st.html(ui.hero_line(
        f"2026: the order is not settled. At the reported pass-through rates Lufthansa loses "
        f"{pct_range(ranges_26['lufthansa']['low'], ranges_26['lufthansa']['high'])} of expected 2026 operating "
        f"profit, Air France-KLM {pct_range(ranges_26['afklm']['low'], ranges_26['afklm']['high'])} and IAG "
        f"{pct_range(ranges_26['iag']['low'], ranges_26['iag']['high'])}, but lower pass-through could put either "
        "peer level with it."))
    st.html(ui.hero_line("[Live line - built in D2 from the live feeds.]"))
    left, right = st.columns([4, 1.3], vertical_alignment="center")
    left.html(ui.chips(
        ui.chip("Jet fuel", "live move - D2"),
        ui.chip("Headline year", "2027"),
        ui.chip("Confidence", "LOW", tone="warn",
                note="Why LOW: the company figures behind these numbers are not yet checked against the source "
                     "PDFs. What raises it: that verification (tracked as B1 in the review backlog)."),
        ui.chip("Yardstick as of", base_date)))
    if right.button("Update data", key="update-data"):
        st.toast("Update data is wired to the live feeds in D2.")
    st.html(ui.skip_link("Skip to the comparison", 7))

# --- steps --------------------------------------------------------------------------------------
st.write("")
with st.container(key="step-01"):
    st.html(ui.step_header(1, "Headline range", "Range bars: solid at reported pass-through, light to 50%",
                           "One visual per step, one headline with the number, at most about forty words of body text "
                           "under it. The rail and the dot on the left join the steps.", "compare"))
    rows = [{"airline": a, **ranges[a]} for a in ("lufthansa", "afklm", "iag")]
    st.plotly_chart(range_bars(rows, "% of expected 2027 operating profit"), config=CONFIG)
    with st.expander("How we calculated this"):
        st.dataframe(pd.DataFrame([
            {"Airline": a, "Reported pass-through": pct_range(ranges[a]["low"], ranges[a]["high"]),
             "Down to 50%": pct(ranges[a]["ext_high"]),
             "Yardstick": eur_m(expected_operating_profit(twins, a, "FY2027")["value"])}
            for a in ("lufthansa", "afklm", "iag")]), hide_index=True)

with st.container(key="step-02"):
    st.html(ui.step_header(2, "Attribution", "Why the gap differs by peer",
                           "Stacked drivers of the gap in percentage points. Example case: Lufthansa hedge cover 29%, "
                           "peers central hedge mix, reported pass-through.", "tornado"))
    chosen = [next(r for r in attribution(twins, "FY2027", p, fx)
                   if r["lh_case"] == "stale 29%" and r["peer_case"] == "central") | {"peer": p} for p in PEERS]
    st.plotly_chart(contribution_bars(chosen, "pp of the gap"), config=CONFIG)

with st.container(key="step-03"):
    st.html(ui.step_header(3, "Ratio cards", "Before and after, per airline",
                           "Cards carry the airline name in text; colour only supports it.", "gauge"))
    card_html = []
    for a in ("lufthansa", "afklm", "iag"):
        base = expected_operating_profit(twins, a, "FY2027")["value"]
        card_html.append(ui.airline_card(a, [{
            "label": "Operating profit 2027", "before": eur_m(base),
            "after": eur_m_range(base * (1 - ranges[a]["high"]), base * (1 - ranges[a]["low"])),
            "change": pct_range(-ranges[a]["high"], -ranges[a]["low"]), "direction": "down"}]))
    st.html(ui.cards(*card_html))

with st.container(key="step-04"):
    st.html(ui.step_header(4, "Takeaway cards", "What it means for management",
                           "Titles as approved; the text under each is written in D6.", "flag"))
    st.html(ui.cards(
        ui.takeaway_card("Thin margins amplify fuel shocks", "[D6 text]", "gauge"),
        ui.takeaway_card("Pricing power is the biggest lever", "[D6 text]", "fare"),
        ui.takeaway_card("2027 hedge cover still matters for the level", "[D6 text]", "volume"),
        ui.takeaway_card("Disclosure gaps limit the comparison", "[D6 text]", "news")))

with st.container(key="step-12"):
    from src.news_tagger import DRIVER_STEPS  # noqa: E402
    st.html(ui.step_header(12, "News room components (D8b)", "Impact markers, also reported by, 7-day line",
                           "SAMPLE TAG for the component demo - not an AI classification. Live tags appear on the "
                           "story page once an API key is configured.", "news"))
    names = {"lufthansa": "Lufthansa", "afklm": "Air France-KLM", "iag": "IAG"}
    st.html(ui.news_summary({"headlines": 3, "impacts": {"lufthansa": {"negative": 2, "positive": 0, "neutral": 1},
                                                         "afklm": {"negative": 1, "positive": 0, "neutral": 0},
                                                         "iag": {"negative": 1, "positive": 0, "neutral": 1}},
                             "top_driver": "guidance", "untagged": 0}, names, DRIVER_STEPS))
    st.html(ui.news_item({"title": "Lufthansa CEO says jet fuel hit to top €1.5bn forecast",
                          "url": "https://www.timeslive.co.za/news/world/2026-09-29-lufthansa-ceo-says-jet-fuel-hit-to-top-15bn-forecast/",
                          "outlet": "timeslive.co.za", "also_reported_by": ["Reuters", "Handelsblatt"], "source": "GDELT",
                          "seen": None,
                          "tag": {"relevant": True, "airlines": ["lufthansa"], "driver": "guidance",
                                  "direction": "cost_up", "severity": 3, "evidence": "jet fuel hit to top",
                                  "evidence_ok": True, "impacts": {"lufthansa": "negative"}}}, names, DRIVER_STEPS))

with st.container(key="step-05"):
    st.html(ui.step_header(5, "Tokens", "Palette, type and icons",
                           "Contrast ratios are computed against the page background (AA body text needs 4.5).",
                           "sliders"))
    swatches = "".join(
        f'<div style="display:flex;gap:10px;align-items:center;margin:4px 0">'
        f'<span style="width:28px;height:18px;border-radius:4px;background:{hexv};border:1px solid {COLORS["line"]}"></span>'
        f'<span class="fsm-label" style="width:90px">{name}</span><span class="fsm-muted">{hexv}</span>'
        f'<span class="fsm-label">{contrast_ratio(hexv, COLORS["bg"]):.1f}:1</span></div>'
        for name, hexv in COLORS.items())
    icons = "".join(f'<span title="{n}" style="margin-right:10px">{icon_img(n)}</span>' for n in BITMAPS)
    st.html(f'<div class="fsm-cards"><div class="fsm-card">{swatches}</div><div class="fsm-card">'
            '<div class="fsm-heading" style="font-size:28px;font-weight:700;color:var(--fsm-text)">Manrope headline 28</div>'
            '<div style="font-size:40px;font-weight:600;color:var(--fsm-accent)">11.7% 1,334</div>'
            '<p class="fsm-muted">Inter body 16 with tabular figures: 1,111.1 / 9,999.9</p>'
            f'{ui.eyebrow("JetBrains Mono label")}<p>Source marker{ui.source_marker("A26")}</p>'
            f'<div style="margin:14px 0">{icons}</div>{ui.link_button("Method & sources", "#step-01")}</div></div>')

st.html('<p class="fsm-label" style="margin-top:32px">Not investment advice. Not affiliated with any company '
        "shown. Built by Marcus Wallin.</p>")
