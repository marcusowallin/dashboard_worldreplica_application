"""Benchmark split from price data (decision 1 Oct 2026, ASSUMPTIONS.md A28, 06_METHODOLOGY.md 6c).

How much of a typical large jet fuel move comes from crude (Brent) and how much from the jet premium (crack)?
  1. Prices: FRED jet fuel (USD/gal x 331.8) and Brent (USD/bbl x 7.9) in USD/t, days with both.
  2. Smoothing: 5-trading-day trailing average - the US Gulf Coast series has one-day spikes (e.g. -350 USD/t
     in a day in Oct 2022) that would otherwise count as separate "moves". Side effect: a jump in the last few
     days is counted only once the average has caught up (up to 4 trading days later).
  3. Lookback: the 5 years BEFORE the baseline day (27 July 2026) - never longer anywhere (decision 2 Oct 2026:
     older markets are not a fair guide to today's). Moves after 27 July are the current shock: they are
     compared with the benchmark, never part of it (decision 1 Oct 2026). 2 and 3 years are shown as a
     sensitivity (lookback_table). 'Update data' re-fetches the history and recomputes everything (only data
     revisions can change the benchmark itself).
  4. Large move ("episode"): jet fuel moves at least USD 75/t (three-quarters of the USD 100/t scenario)
     within 60 calendar days (about the time between the airlines' quarterly reports, and the length of
     today's move since 27 July).
  5. No double counting: a chronological scan. From a start day, the episode ends on the FIRST day the move
     reaches USD 75/t; the next search starts on that end day. Episodes never share days; a move that keeps
     going counts again only after another full USD 75/t. If no day within 60 days reaches the threshold,
     the start moves on by one trading day.
  6. Crude share of an episode = Brent move / jet move (rises and falls alike; it can be below 0 or above 1
     when crude and the premium move in opposite directions - the median is robust to that).
  7. Benchmark split for the USD 100/t scenario = the median crude share (clipped to 0-100%), rounded to whole
     USD; typical range = the interquartile range. Fewer than MIN_EPISODES -> neutral 50/50, labelled.
"""
from datetime import timedelta
from statistics import median, quantiles

SMOOTHING_DAYS = 5
THRESHOLD_USD_T = 75.0
WINDOW_DAYS = 60
LOOKBACK_YEARS = 5            # the longest window used anywhere on the page (decision 2 Oct 2026)
SENSITIVITY_YEARS = (2, 3, 5)
MIN_EPISODES = 8
FALLBACK_SPLIT = (50.0, 50.0)


def smooth(prices, n=SMOOTHING_DAYS):
    """n-trading-day trailing average of {date: (jet, brent, crack)}; the first n-1 days are dropped."""
    days = sorted(prices)
    return {days[i]: tuple(sum(prices[d][k] for d in days[i - n + 1:i + 1]) / n for k in range(3))
            for i in range(n - 1, len(days))}


def find_episodes(prices, start, end, threshold=THRESHOLD_USD_T, window_days=WINDOW_DAYS):
    """Non-overlapping large jet fuel moves between start and end (see module docstring, step 5).

    Output: list of {"start", "end", "d_jet", "d_brent", "d_crack", "crude_share"}.
    """
    days = [d for d in sorted(prices) if start <= d <= end]
    episodes, i = [], 0
    while i < len(days):
        t0, found = days[i], None
        for j in range(i + 1, len(days)):
            if (days[j] - t0).days > window_days:
                break
            if abs(prices[days[j]][0] - prices[t0][0]) >= threshold:
                found = j
                break
        if found is None:
            i += 1
            continue
        t1 = days[found]
        d_jet, d_brent = prices[t1][0] - prices[t0][0], prices[t1][1] - prices[t0][1]
        episodes.append({"start": t0, "end": t1, "d_jet": d_jet, "d_brent": d_brent, "d_crack": d_jet - d_brent,
                         "crude_share": d_brent / d_jet})
        i = found
    return episodes


def benchmark_split(prices, end_day, move=100.0, years=LOOKBACK_YEARS, latest_day=None):
    """The data-driven split for the scenario move: large moves in the `years` before `end_day` (the baseline).

    latest_day: if given, the moves after end_day up to it are returned separately as "after" (shown on the
    Step 2 chart, hollow; NOT used for the median).
    Output: {"split": (crude, premium) USD/t, "median", "q1", "q3", "n", "episodes", "after", "start", "end",
             "years", "fallback": bool}.
    """
    start = end_day - timedelta(days=round(365.25 * years))
    smoothed = smooth({d: v for d, v in prices.items() if d <= (latest_day or end_day)})
    episodes = find_episodes(smoothed, start, end_day)
    after = find_episodes(smoothed, end_day, latest_day) if latest_day and latest_day > end_day else []
    shares = [e["crude_share"] for e in episodes]
    base = {"n": len(shares), "episodes": episodes, "after": after, "start": start, "end": end_day, "years": years}
    if len(shares) < MIN_EPISODES:
        return {**base, "split": FALLBACK_SPLIT, "median": None, "q1": None, "q3": None, "fallback": True}
    q1, _, q3 = quantiles(shares, n=4)
    mid = median(shares)
    crude = round(min(max(mid, 0.0), 1.0) * move)
    return {**base, "split": (float(crude), float(move - crude)), "median": mid, "q1": q1, "q3": q3,
            "fallback": False}


def lookback_table(prices, end_day, years=SENSITIVITY_YEARS):
    """Sensitivity: median, middle half and number of moves for each lookback (same end day)."""
    out = []
    for y in years:
        stats = benchmark_split(prices, end_day, years=y)
        out.append({"years": y, "n": stats["n"], "median": stats["median"], "q1": stats["q1"], "q3": stats["q3"],
                    "start": stats["start"], "first_day": min(prices) if prices else None})
    return out


def today_share(moves):
    """Crude share of the actual move since the baseline (None if jet did not move)."""
    return moves["d_brent"] / moves["d_jet"] if moves and moves["d_jet"] else None


def compare_to_history(share, stats):
    """'within the usual range' / 'more crude-heavy than usual' / 'more premium-heavy than usual'."""
    if share is None or stats["fallback"]:
        return None
    if share > stats["q3"]:
        return "more crude-heavy than usual"
    if share < stats["q1"]:
        return "more premium-heavy than usual"
    return "within the usual range"


HORIZONS = ((1, "1 day"), (5, "1 week"), (20, "1 month"), (42, "2 months"))


def co_movement(prices, start, end, horizons=HORIZONS):
    """Do crude and the jet premium move together? Non-overlapping changes over each horizon (trading days).

    Output per horizon: {"label", "n", "correlation", "beta" (premium move per USD 1 crude move),
    "crude_share_of_variance", "premium_share_of_variance"} - the two variance shares split jet fuel's
    variance (Var jet = Var crude + Var premium + 2 Cov), each taking half of the covariance. Unsmoothed prices.
    """
    days = [d for d in sorted(prices) if start <= d <= end]
    out = []
    for h, label in horizons:
        idx = range(0, len(days) - h, h)
        d_b = [prices[days[i + h]][1] - prices[days[i]][1] for i in idx]
        d_c = [prices[days[i + h]][2] - prices[days[i]][2] for i in idx]
        if len(d_b) < 3:
            continue
        mb, mc = sum(d_b) / len(d_b), sum(d_c) / len(d_c)
        var_b = sum((b - mb) ** 2 for b in d_b) / len(d_b)
        var_c = sum((c - mc) ** 2 for c in d_c) / len(d_c)
        cov = sum((b - mb) * (c - mc) for b, c in zip(d_b, d_c)) / len(d_b)
        var_j = var_b + var_c + 2 * cov
        out.append({"label": label, "n": len(d_b),
                    "correlation": cov / (var_b * var_c) ** 0.5 if var_b and var_c else None,
                    "beta": cov / var_b if var_b else None,
                    "crude_share_of_variance": (var_b + cov) / var_j if var_j else None,
                    "premium_share_of_variance": (var_c + cov) / var_j if var_j else None})
    return out
