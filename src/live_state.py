"""Live prices shared by every page and every visitor: one cached fetch, one 'Update data' cooldown.

Used by the story page and the Method & sources page, so both show the same data and one fetch serves both.
A FAILED fetch is never cached (the cached function raises instead of returning it); if the feeds are down the
last good data is shown with a notice, or none. The loader is looked up on the module at call time so tests can
replace it.
"""
import threading
from datetime import datetime, timedelta, timezone

import streamlit as st

from src import data_sources
from src.model.run import BASELINE_DAY
from src.story.price_split import LOOKBACK_YEARS

FALLBACK_FX = 1.151            # Lufthansa's printed planning rate - only if the ECB feed is down (labelled)
UPDATE_COOLDOWN_S = 60         # one shared re-fetch per minute at most, whoever clicks


class FeedsDown(Exception):
    """Raised inside the cached fetch so that a FAILED fetch is never cached."""


@st.cache_data(ttl=6 * 3600, show_spinner="Loading prices (FRED, ECB)...")
def _fetch_prices():
    history = BASELINE_DAY - timedelta(days=round(365.25 * LOOKBACK_YEARS) + 40)
    live = data_sources.load_live_prices(BASELINE_DAY, history_start=history)
    if not live["ok"]:
        raise FeedsDown(live)
    return live, datetime.now(timezone.utc)


@st.cache_resource
def _shared():
    """Shared by every visitor: the last good prices and the Update-data cooldown."""
    return {"last_good": None, "last_update": None, "lock": threading.Lock()}


def update_prices():
    """'Update data': drop the cached prices (at most once a minute across all visitors). Returns a message."""
    shared = _shared()
    with shared["lock"]:
        now = datetime.now(timezone.utc)
        if shared["last_update"] and (now - shared["last_update"]).total_seconds() < UPDATE_COOLDOWN_S:
            wait = UPDATE_COOLDOWN_S - (now - shared["last_update"]).total_seconds()
            return f"Prices were just updated - next update possible in {wait:.0f} s."
        shared["last_update"] = now
        _fetch_prices.clear()
    return None


def current_prices():
    """(live, fetched_at, notice). Falls back to the last good data, then to no live data - never crashes."""
    shared = _shared()
    try:
        live, fetched = _fetch_prices()
        shared["last_good"] = (live, fetched)
        return live, fetched, None
    except FeedsDown as down:
        errors = "; ".join(down.args[0]["errors"])
        if shared["last_good"]:
            live, fetched = shared["last_good"]
            return live, fetched, (f"Live feeds unavailable right now ({errors}). Showing the last good data, "
                                   f"fetched {fetched:%d %b %Y %H:%M} UTC.")
        return None, None, f"Live feeds unavailable right now ({errors}). The scenario below does not need them."
