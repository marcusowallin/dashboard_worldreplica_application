"""Live prices: FRED jet fuel and Brent, ECB USD/EUR via Frankfurter.

Every fetch returns a FeedResult with the data, the source name and URL, the as-of date and an
error message. A failed fetch never raises: data is None and `error` says what went wrong, so
the page can show the message and fall back to the labelled scenario.

Units: FRED jet fuel is USD per US gallon (US Gulf Coast kerosene-type jet, proxy for Europe),
Brent is USD per barrel. Both are converted to USD per tonne with ONE stated factor (A12):
7.9 bbl per tonne of jet fuel, i.e. 7.9 x 42 = 331.8 US gallons per tonne.
Jet crack = jet - Brent, both in USD/t.
"""
import csv
import io
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import requests

from src.model.fuel import BBL_PER_TONNE

GALLONS_PER_BARREL = 42
GALLONS_PER_TONNE = BBL_PER_TONNE * GALLONS_PER_BARREL   # 331.8

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}&cosd={start}"
FRED_PAGE = "https://fred.stlouisfed.org/series/{series}"
FX_URL = "https://api.frankfurter.dev/v1/{day}?base=EUR&symbols=USD"
JET_SERIES, BRENT_SERIES = "DJFUELUSGULF", "DCOILBRENTEU"
TIMEOUT_S = 10          # per request; three requests run one after another, so a full outage costs at most about 30 s once a minute


@dataclass
class FeedResult:
    """Outcome of one fetch. data is None when the fetch failed (see error)."""
    data: object
    source: str
    url: str
    as_of: date = None
    error: str = None


def fetch_fred(series_id, start, get=requests.get):
    """Daily FRED series from `start` as a list of (date, value); missing days ('.') skipped."""
    url = FRED_CSV.format(series=series_id, start=start.isoformat())
    source = f"FRED {series_id} ({FRED_PAGE.format(series=series_id)})"
    try:
        response = get(url, timeout=TIMEOUT_S)
        response.raise_for_status()
        rows = list(csv.reader(io.StringIO(response.text)))
        data = [(datetime.strptime(d, "%Y-%m-%d").date(), float(v))
                for d, v in rows[1:] if v not in (".", "")]
    except Exception as err:  # network, HTTP or parse error: report, never crash
        return FeedResult(None, source, url, error=f"{series_id} could not be loaded: {err}")
    if not data:
        return FeedResult(None, source, url, error=f"{series_id} returned no observations")
    return FeedResult(data, source, url, as_of=data[-1][0])


def fetch_usd_per_eur(day="latest", get=requests.get):
    """ECB reference rate USD per 1 EUR for `day` (a date or 'latest'), via Frankfurter."""
    label = day if isinstance(day, str) else day.isoformat()
    url = FX_URL.format(day=label)
    source = "ECB reference rate via Frankfurter"
    try:
        response = get(url, timeout=TIMEOUT_S)
        response.raise_for_status()
        payload = response.json()
        rate = float(payload["rates"]["USD"])
        as_of = datetime.strptime(payload["date"], "%Y-%m-%d").date()
    except Exception as err:
        return FeedResult(None, source, url, error=f"USD/EUR could not be loaded: {err}")
    return FeedResult(rate, source, url, as_of=as_of)


def jet_usd_per_t(usd_per_gallon):
    """USD/gal -> USD/t (x 331.8)."""
    return usd_per_gallon * GALLONS_PER_TONNE


def brent_usd_per_t(usd_per_bbl):
    """USD/bbl -> USD/t (x 7.9)."""
    return usd_per_bbl * BBL_PER_TONNE


def daily_prices_per_t(jet, brent):
    """Align jet and Brent on common dates: {date: (jet USD/t, brent USD/t, crack USD/t)}."""
    brent_by_day = dict(brent)
    out = {}
    for day, jet_gal in jet:
        if day in brent_by_day:
            j, b = jet_usd_per_t(jet_gal), brent_usd_per_t(brent_by_day[day])
            out[day] = (j, b, j - b)
    return out


def value_on_or_before(prices, day):
    """(date, prices) for the last observation on or before `day`, or None."""
    earlier = [d for d in prices if d <= day]
    return (max(earlier), prices[max(earlier)]) if earlier else None


def moves_since_baseline(prices, baseline_day):
    """Baseline and latest prices and the latest move (USD/t), all with their dates.

    Baseline = last observation on or before the baseline day (27 Jul 2026).
    """
    base = value_on_or_before(prices, baseline_day)
    if base is None or not prices:
        return None
    latest_day = max(prices)
    (b_day, (bj, bb, bc)), (lj, lb, lc) = base, prices[latest_day]
    return {"baseline_day": b_day, "latest_day": latest_day,
            "baseline": {"jet": bj, "brent": bb, "crack": bc},
            "latest": {"jet": lj, "brent": lb, "crack": lc},
            "d_jet": lj - bj, "d_brent": lb - bb, "d_crack": lc - bc}


def monthly_average_moves(prices, baseline_day, until):
    """Average daily move vs baseline per calendar month, for days after the baseline to `until`.

    Output: {(year, month): {"d_brent": .., "d_crack": .., "observations": n}}.
    """
    base = value_on_or_before(prices, baseline_day)
    if base is None:
        return {}
    _, (_, bb, bc) = base
    buckets = {}
    for day, (_, b, c) in sorted(prices.items()):
        if baseline_day < day <= until:
            buckets.setdefault((day.year, day.month), []).append((b - bb, c - bc))
    return {m: {"d_brent": sum(x for x, _ in v) / len(v), "d_crack": sum(y for _, y in v) / len(v),
                "observations": len(v)} for m, v in buckets.items()}


def load_live_prices(baseline_day, get=requests.get, history_start=None):
    """Fetch everything the live page needs. Returns a dict with results and any errors.

    history_start: fetch from this date instead (the story page needs ~2 years for the benchmark split,
    src/story/price_split.py); default = two weeks before the baseline.
    """
    start = min(history_start or baseline_day, baseline_day - timedelta(days=14))
    jet, brent = fetch_fred(JET_SERIES, start, get), fetch_fred(BRENT_SERIES, start, get)
    fx = fetch_usd_per_eur("latest", get)
    errors = [r.error for r in (jet, brent, fx) if r.error]
    prices = daily_prices_per_t(jet.data, brent.data) if jet.data and brent.data else {}
    moves = moves_since_baseline(prices, baseline_day) if prices else None
    if prices and moves is None:
        errors.append("No price observation on or before the baseline date")
    return {"jet": jet, "brent": brent, "fx": fx, "prices": prices, "moves": moves,
            "monthly": monthly_average_moves(prices, baseline_day, max(prices)) if moves else {},
            "errors": errors, "ok": not errors}
