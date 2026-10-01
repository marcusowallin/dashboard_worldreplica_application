"""Tests for the data-driven benchmark split (src/story/price_split.py). Synthetic prices, known answers."""
from datetime import date, timedelta

import pytest

from src.story.price_split import (
    MIN_EPISODES, benchmark_split, co_movement, compare_to_history, find_episodes, smooth, today_share,
)
from src.ui.charts import split_history

D0 = date(2025, 1, 1)


def series(jet_steps, brent_steps, start_jet=1000.0, start_brent=600.0):
    """{date: (jet, brent, crack)} from daily increments (one entry per calendar day)."""
    out, jet, brent = {}, start_jet, start_brent
    for i, (dj, db) in enumerate(zip(jet_steps, brent_steps)):
        jet, brent = jet + dj, brent + db
        out[D0 + timedelta(days=i)] = (jet, brent, jet - brent)
    return out


def test_smooth_is_a_trailing_average():
    prices = series([0, 10, 10, 10, 10, 10], [0] * 6)
    s = smooth(prices, n=5)
    assert min(s) == D0 + timedelta(days=4)                        # first n-1 days dropped
    assert s[D0 + timedelta(days=4)][0] == pytest.approx(1000 + (0 + 10 + 20 + 30 + 40) / 5)


def test_episode_ends_on_first_day_reaching_the_threshold_and_does_not_overlap():
    # jet +10/day (Brent +6/day) for 20 days: +75 is first reached on day 8 (+80), then again 8 days later
    prices = series([0] + [10] * 20, [0] + [6] * 20)
    eps = find_episodes(prices, D0, D0 + timedelta(days=30), threshold=75, window_days=60)
    assert [(e["start"], e["end"]) for e in eps] == [(D0, D0 + timedelta(days=8)),
                                                      (D0 + timedelta(days=8), D0 + timedelta(days=16))]
    assert all(e["crude_share"] == pytest.approx(0.6) for e in eps)
    assert eps[0]["end"] == eps[1]["start"]                        # touching, never sharing days


def test_slow_drift_beyond_the_window_is_not_an_episode():
    prices = series([1] * 200, [0.5] * 200)                      # +1/day: +75 needs 75 days > 60
    assert find_episodes(prices, D0, D0 + timedelta(days=200), threshold=75, window_days=60) == []


def test_falls_count_with_the_same_share_and_opposite_moves_can_exceed_one():
    prices = series([0, -40, -40, 20, 20, 20, 20], [0, -40, -40, 0, 0, 0, 0])
    eps = find_episodes(prices, D0, D0 + timedelta(days=10), threshold=75, window_days=60)
    assert eps[0]["d_jet"] == -80 and eps[0]["crude_share"] == pytest.approx(1.0)


def _episodes_prices(shares, gap_days=70):
    """One clean +80 USD/t jump per share, far apart, flat in between (each jump = one episode)."""
    out, jet, brent, day = {}, 1000.0, 600.0, D0
    for share in shares:
        for _ in range(gap_days):
            out[day] = (jet, brent, jet - brent)
            day += timedelta(days=1)
        jet, brent = jet + 80, brent + 80 * share
    for _ in range(10):        # a few days after the last jump: the 5-day average needs them to see it fully
        out[day] = (jet, brent, jet - brent)
        day += timedelta(days=1)
    return out, day - timedelta(days=1)


def test_benchmark_split_is_the_median_with_iqr_and_rounds_to_whole_usd():
    shares = [0.1, 0.3, 0.5, 0.55, 0.6, 0.7, 0.9, 0.2, 0.8]
    prices, last = _episodes_prices(shares)
    stats = benchmark_split(prices, last, years=5)
    assert stats["n"] == len(shares) and not stats["fallback"]
    assert stats["median"] == pytest.approx(0.55, abs=1e-9)
    assert stats["split"] == (55.0, 45.0)
    assert stats["q1"] < stats["median"] < stats["q3"]


def test_too_few_episodes_falls_back_to_neutral_labelled():
    prices, last = _episodes_prices([0.6] * (MIN_EPISODES - 1))
    stats = benchmark_split(prices, last, years=5)
    assert stats["fallback"] and stats["split"] == (50.0, 50.0) and stats["median"] is None


def test_lookback_excludes_older_moves():
    prices, last = _episodes_prices([0.9] * 5 + [0.3] * 9)        # old crude-heavy moves, recent premium-heavy
    recent = benchmark_split(prices, last, years=1.8)
    assert recent["median"] == pytest.approx(0.3, abs=1e-9)


def test_compare_today_with_history():
    stats = {"fallback": False, "q1": 0.25, "q3": 0.75, "median": 0.5}
    assert compare_to_history(0.65, stats) == "within the usual range"
    assert compare_to_history(0.9, stats) == "more crude-heavy than usual"
    assert compare_to_history(0.1, stats) == "more premium-heavy than usual"
    assert compare_to_history(0.5, {"fallback": True}) is None
    assert today_share({"d_brent": 175.0, "d_jet": 271.0}) == pytest.approx(175 / 271)


def test_co_movement_correlation_and_variance_shares():
    # premium = 0.5 x crude change every day -> correlation +1, beta 0.5, crude explains 2/3 of jet variance
    steps = [((-1) ** i) * (i % 7 + 1) for i in range(60)]
    prices = series([1.5 * s for s in steps], steps)
    out = co_movement(prices, D0, D0 + timedelta(days=60), horizons=((1, "1 day"),))
    assert out[0]["correlation"] == pytest.approx(1.0) and out[0]["beta"] == pytest.approx(0.5)
    assert out[0]["crude_share_of_variance"] == pytest.approx(2 / 3)
    assert out[0]["crude_share_of_variance"] + out[0]["premium_share_of_variance"] == pytest.approx(1.0)


def test_split_history_chart_is_a_histogram_with_median_and_today():
    prices, last = _episodes_prices([0.1, 0.3, 0.5, 0.55, 0.6, 0.7, 0.9, 0.2, 0.8])
    stats = benchmark_split(prices, last, years=5)
    fig = split_history(stats, {"day": last, "share": 0.65, "d_jet": 271.0})
    assert len(fig.data) == 1 and fig.data[0].type == "histogram"
    assert len(fig.data[0].x) == stats["n"] == 9                       # every large move is counted once
    texts = [a.text for a in fig.layout.annotations]
    assert texts == ["median 55% = the scenario split", "today 65%"]    # one label per line, nothing else
    lines = sorted(s.x0 for s in fig.layout.shapes if s.type == "line")
    assert lines == pytest.approx([55.0, 65.0])
    assert fig.layout.xaxis.range == (-60, 160)                         # no empty years, no empty axis


def test_split_history_clips_extreme_shares_to_the_edge_bars():
    prices, last = _episodes_prices([-2.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 3.0])
    stats = benchmark_split(prices, last, years=5)
    fig = split_history(stats, None)
    assert min(fig.data[0].x) == -50.0 and max(fig.data[0].x) == 150.0
    assert [a.text for a in fig.layout.annotations] == ["median 50% = the scenario split"]


def test_moves_after_the_baseline_are_reported_but_not_in_the_benchmark():
    from src.story.price_split import lookback_table  # noqa: F401  (import check)
    prices, last = _episodes_prices([0.5] * 9 + [0.0, 0.0, 0.0])    # last three jumps: premium-only
    cut = last - timedelta(days=3 * 70 + 5)                        # baseline before the last three jumps
    stats = benchmark_split(prices, cut, years=5, latest_day=last)
    assert stats["n"] == 9 and stats["median"] == pytest.approx(0.5)
    assert len(stats["after"]) == 3 and all(e["crude_share"] == pytest.approx(0.0) for e in stats["after"])
    assert all(e["end"] <= cut for e in stats["episodes"]) and all(e["start"] >= cut for e in stats["after"])
    fig = split_history(stats, None)
    assert len(fig.data) == 1 and len(fig.data[0].x) == 9              # the three later moves are not in the chart


def test_lookback_table_reports_each_window():
    from src.story.price_split import lookback_table
    prices, last = _episodes_prices([0.9] * 9 + [0.3] * 9)        # 70 days apart: ~3.5 years in total
    rows = {r["years"]: r for r in lookback_table(prices, last, years=(1.69, 5))}   # 1.69 y = last nine jumps only
    assert rows[1.69]["n"] == 9 and rows[1.69]["median"] == pytest.approx(0.3)
    assert rows[5]["n"] == 18 and rows[5]["median"] == pytest.approx(0.6)


def test_median_interval_contains_the_median_is_repeatable_and_widens_with_noise():
    from src.story.price_split import median_interval
    tight = [0.5] * 20
    assert median_interval(tight) == (0.5, 0.5)
    noisy = [0.1, 0.3, 0.5, 0.55, 0.6, 0.7, 0.9, 0.2, 0.8, 0.45, 0.65, 0.35]
    lo, hi = median_interval(noisy)
    assert lo <= 0.525 <= hi and hi - lo > 0.05                      # median of the sample is 0.525
    assert median_interval(noisy) == (lo, hi)                        # fixed seed: same every run
    prices, last = _episodes_prices([0.1, 0.3, 0.5, 0.55, 0.6, 0.7, 0.9, 0.2, 0.8])
    stats = benchmark_split(prices, last, years=5)
    assert stats["interval"][0] <= stats["median"] <= stats["interval"][1]
