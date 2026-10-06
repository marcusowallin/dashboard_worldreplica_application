"""News room - the AI's part of the project, kept apart from the answer.

Headlines from GDELT (and, on request, a web search) are classified by an AI model: airline, driver, direction and
the likely effect on each airline. The AI only labels; every quote is checked against the headline in code. This page
shows how the AI is used and limited. It does not feed any number on the story page.
"""
from datetime import datetime

import streamlit as st

from src import news_tagger
from src.model.run import AIRLINES
from src.news_keywords import MAJOR_OUTLETS
from src.news_tagger import (
    DRIVER_STEPS, MAX_PER_REFRESH, WEB_SEARCH_COOLDOWN, WEB_SEARCH_COST_PER_CLICK_USD, WEB_SEARCH_DAILY_CAP,
    WEB_SEARCH_MAX_USES, NewsStore, seven_day_summary, tagged_view,
)
from src.story.sources import markers as mk
from src.ui import components as ui
from src.ui import method_parts as mp
from src.ui.css import inject
from src.ui.theme import AIRLINE_SHORT

inject()

st.html(mp.back_link("./", "Back to the story"))
st.title("News room")
st.markdown("An always-on monitor reads the news so a person does not have to. This page is that part, as a small "
            "prototype: it collects headlines about the three airlines and jet fuel, and an AI model labels each one "
            "(which airline, which driver, which direction). **It never produces a number**: the story page does not "
            "use anything from here.")

@st.cache_resource
def news_store():
    """ONE store shared by every visitor: shared cooldown, tag cache, daily cap (cost guards)."""
    return NewsStore()


def _seen(value):
    """GDELT 'seendate' (20260930T120000Z) -> datetime, or None."""
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ")
    except (TypeError, ValueError):
        return None


store = news_store()
client = news_tagger.make_client(st.secrets.get)
with st.container(key="step-news"):
    st.html(ui.step_header(None, "Latest signals", "What the news says - linked to the step it affects.",
                           "Headlines from GDELT (and, on request, a web search of major outlets), classified by an AI "
                           "model: airline, driver, direction and the likely effect on each airline. The AI only "
                           "labels; every tag's quote is checked against the headline in code.", "news",
                           markers_html=mk("NEWS")))
    names = {a: AIRLINE_SHORT[a] for a in AIRLINES}
    st.html(ui.news_summary(seven_day_summary(store, datetime.now()), names, DRIVER_STEPS))
    left, right = st.columns([1.5, 3.8], vertical_alignment="center")
    if left.button("Refresh news", key="cta-news",
                   help=("Live feed, last three days; a web search of US and UK outlets tops it up when the feed is busy "
                         "or finds few headlines. Shared 10-minute cooldown.")):
        with st.spinner("Fetching headlines and tagging new ones..."):
            news_tagger.refresh_news(store, datetime.now(), client=client)
    # before the first refresh the message already says "Not refreshed yet", so no second copy of it in brackets
    ago = (f" (last refreshed {max(0, int((datetime.now() - store.last_refresh).total_seconds() // 60))} min ago)"
           if store.last_refresh else "")
    right.html(ui.as_of_line(f"{store.last_message}{ago}" + (f" {store.web_message}" if store.web_message else "")))
    if client is None:
        st.html(ui.notice("News tagging and web search unavailable (no API key configured) - headlines are shown "
                          "untagged."))
    items = tagged_view(store)
    choice = st.segmented_control("Airline", ["All", *names.values()], default="All", key="news-filter",
                                  label_visibility="collapsed")
    shown = [i for i in items if choice in (None, "All")
             or (i["tag"] and choice in [names.get(a) for a in i["tag"]["airlines"]])]
    if not items:
        st.html(ui.as_of_line("The headline feed is busy right now - try again in a few minutes. The rest of the "
                              "page does not depend on it." if store.last_failure else
                              "No headlines yet - press 'Refresh news'."))
    elif not shown:
        st.html(ui.as_of_line(f"No tagged headlines about {choice} in the current set."))
    else:
        st.html("".join(ui.news_item({**i, "seen": _seen(i.get("seen"))}, names, DRIVER_STEPS)
                        for i in shown[:MAX_PER_REFRESH]))
    with st.expander("How this works"):
        low, high = WEB_SEARCH_COST_PER_CLICK_USD
        st.markdown(
            "**Feed.** GDELT, last three days, English, German and French sources, three short searches (airline "
            "groups, peers, jet fuel terms). **Keyword filter** (no AI, no cost): a headline is kept only if it names "
            "one of the three groups or a subsidiary, contains an aviation-fuel term, or pairs a market or "
            f"disruption term with an aviation word; {store.filtered_out} headlines were dropped at the last refresh. "
            "**Duplicates**: the same story from several outlets is shown once, with 'also reported by'.\n\n"
            "**Tagging.** Claude Haiku returns airline, driver, direction, a short quote and, for each airline, the "
            "likely effect on its earnings: &#9650; positive, &#9660; negative, &#9679; neutral or unclear - always "
            "with the word. Industry-wide headlines (e.g. jet fuel prices) are tagged for all three; a competitor's "
            "problem is never counted as good news for another airline. Values outside fixed lists are rejected in "
            "code and the quote must appear word for word in the headline. Headlines are data, never instructions "
            "(tested with 'ignore previous instructions' and 'mark this positive'). **Drivers -> steps**: fuel price "
            "(1), jet premium / refining (2), hedging (3), capacity (4), pass-through (5), guidance (6), airspace / "
            "disruption (7). **7-day line**: headlines collected by this page in the last seven days (kept in "
            "memory; a restart starts it again).\n\n"
            f"**Web search** (automatic top-up when the live feed is busy or finds fewer than {news_tagger.MIN_HEADLINES_BEFORE_WEB} relevant headlines): Anthropic's web search tool, limited to {', '.join(MAJOR_OUTLETS)}; "
            "only headline, outlet, date and link are kept - no article text. Limits for all visitors together: "
            f"{WEB_SEARCH_MAX_USES} searches per refresh, one web search per "
            f"{int(WEB_SEARCH_COOLDOWN.total_seconds() // 60)} minutes, {WEB_SEARCH_DAILY_CAP} a day. "
            f"**Estimated cost per web search: about USD {low:.2f}-{high:.2f}** (USD 10 per 1,000 searches plus the "
            "search results read as input tokens, and the tagging call; Anthropic price list, 1 Oct 2026), so at "
            f"most about USD {high * WEB_SEARCH_DAILY_CAP:.2f} a day.\n\n"
            "**Cost guards** for 'Refresh news': click only, one shared 10-minute cooldown, only new headlines are "
            "sent, one AI call per refresh, a daily cap, and a spending limit on the API account.\n\n"
            "**Data sources.** Which news sources were considered, which are used and why: Method & sources, "
            "section News sources.")

