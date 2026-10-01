"""Tests for src/data_sources.py - the network is always mocked."""
from datetime import date

import pytest
import requests

from src.data_sources import (
    GALLONS_PER_TONNE, brent_usd_per_t, daily_prices_per_t, fetch_fred, fetch_usd_per_eur,
    jet_usd_per_t, load_live_prices, monthly_average_moves, moves_since_baseline,
)


class FakeResponse:
    def __init__(self, text="", payload=None, status=200):
        self.text, self._payload, self.status = text, payload, status

    def raise_for_status(self):
        if self.status >= 400:
            raise requests.HTTPError(f"HTTP {self.status}")

    def json(self):
        return self._payload


JET_CSV = ("observation_date,DJFUELUSGULF\n2026-07-24,3.600\n2026-07-27,3.582\n"
           "2026-08-03,3.700\n2026-08-04,.\n2026-09-01,4.000\n2026-09-22,4.354\n")
BRENT_CSV = ("observation_date,DCOILBRENTEU\n2026-07-24,90.00\n2026-07-27,92.00\n"
             "2026-08-03,95.00\n2026-09-01,105.00\n2026-09-22,114.89\n")


def fake_get(url, timeout=None):
    if "DJFUELUSGULF" in url:
        return FakeResponse(JET_CSV)
    if "DCOILBRENTEU" in url:
        return FakeResponse(BRENT_CSV)
    if "frankfurter" in url:
        return FakeResponse(payload={"date": "2026-09-29", "rates": {"USD": 1.1355}})
    raise AssertionError(url)


def failing_get(url, timeout=None):
    raise requests.ConnectionError("network down")


def test_conversion_factors():
    assert GALLONS_PER_TONNE == pytest.approx(331.8)
    assert jet_usd_per_t(3.582) == pytest.approx(1188.5, abs=0.1)
    assert brent_usd_per_t(92) == pytest.approx(726.8)


def test_fetch_fred_parses_and_skips_missing():
    r = fetch_fred("DJFUELUSGULF", date(2026, 7, 13), fake_get)
    assert r.error is None
    assert (date(2026, 8, 4), None) not in r.data and len(r.data) == 5
    assert r.as_of == date(2026, 9, 22)
    assert "fred.stlouisfed.org" in r.url


def test_fetch_failures_return_message_not_exception():
    r = fetch_fred("DJFUELUSGULF", date(2026, 7, 13), failing_get)
    assert r.data is None and "network down" in r.error
    fx = fetch_usd_per_eur("latest", failing_get)
    assert fx.data is None and "USD/EUR" in fx.error


def test_http_error_is_reported():
    r = fetch_fred("X", date(2026, 7, 13), lambda url, timeout=None: FakeResponse(status=500))
    assert r.data is None and "500" in r.error


def test_fx_rate_and_date():
    fx = fetch_usd_per_eur("latest", fake_get)
    assert fx.data == 1.1355 and fx.as_of == date(2026, 9, 29)


def test_moves_since_baseline_by_hand():
    prices = daily_prices_per_t(fetch_fred("DJFUELUSGULF", date(2026, 7, 13), fake_get).data,
                                fetch_fred("DCOILBRENTEU", date(2026, 7, 13), fake_get).data)
    m = moves_since_baseline(prices, date(2026, 7, 27))
    # jet 3.582 -> 4.354 USD/gal: +0.772 * 331.8 = +256.15 USD/t
    # Brent 92.00 -> 114.89: +22.89 * 7.9 = +180.83 USD/t; crack = 256.15 - 180.83 = +75.32
    assert m["d_jet"] == pytest.approx(256.15, abs=0.01)
    assert m["d_brent"] == pytest.approx(180.83, abs=0.01)
    assert m["d_crack"] == pytest.approx(m["d_jet"] - m["d_brent"])
    assert m["baseline_day"] == date(2026, 7, 27) and m["latest_day"] == date(2026, 9, 22)


def test_monthly_average_moves():
    prices = daily_prices_per_t(fetch_fred("DJFUELUSGULF", date(2026, 7, 13), fake_get).data,
                                fetch_fred("DCOILBRENTEU", date(2026, 7, 13), fake_get).data)
    months = monthly_average_moves(prices, date(2026, 7, 27), date(2026, 9, 22))
    assert set(months) == {(2026, 8), (2026, 9)}
    # August: one day (3 Aug), Brent +3 * 7.9 = +23.7
    assert months[(2026, 8)]["d_brent"] == pytest.approx(23.7)
    assert months[(2026, 9)]["observations"] == 2


def test_load_live_prices_ok_and_failure():
    live = load_live_prices(date(2026, 7, 27), fake_get)
    assert live["ok"] and live["moves"]["latest_day"] == date(2026, 9, 22)
    down = load_live_prices(date(2026, 7, 27), failing_get)
    assert not down["ok"] and len(down["errors"]) == 3 and down["moves"] is None


def test_a_feed_outage_is_remembered_for_a_minute_and_update_data_tries_again(monkeypatch):
    """During an outage every page rerun must not wait for three slow requests: the failure is cached for DOWN_CACHE_S."""
    import src.data_sources as ds
    import src.live_state as ls
    import streamlit as st
    st.cache_data.clear()
    st.cache_resource.clear()
    calls = []

    def failing(day, **kwargs):
        calls.append(day)
        return {"ok": False, "errors": ["FRED answered HTTP 500"]}

    monkeypatch.setattr(ds, "load_live_prices", failing)
    live, fetched, notice = ls.current_prices()
    assert live is None and "unavailable" in notice and len(calls) == 1
    ls.current_prices()
    ls.current_prices()
    assert len(calls) == 1                                       # remembered: no new requests within the minute
    assert ls.DOWN_CACHE_S == 60 and ds.TIMEOUT_S == 10
    ls.update_prices()                                           # the visitor asks explicitly
    ls.current_prices()
    assert len(calls) == 2
    st.cache_data.clear()
    st.cache_resource.clear()
