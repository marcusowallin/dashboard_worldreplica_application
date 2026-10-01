"""Time split: remaining part of FY2026 and FY2027 (06_METHODOLOGY.md section 4, P1 part).

P1 prices only the REMAINING part of FY2026 (after the as-of date to 31 Dec) plus FY2027.
The realised part (27 Jul to the as-of date) is P2. Calendar fiscal years (all three airlines).

Quarterly volume rule (assumption A11): printed quarterly volume where available, every other
quarter = FY volume / 4. Remaining share of a quarter = remaining days after the as-of date /
days in the quarter (the as-of day itself counts as passed).
"""
from datetime import date, timedelta

QUARTERS = (1, 2, 3, 4)


def quarter_bounds(year, quarter):
    """First and last day of a calendar quarter, e.g. (2026-10-01, 2026-12-31) for Q4 2026."""
    if quarter not in QUARTERS:
        raise ValueError(f"quarter must be 1-4, got {quarter}")
    start = date(year, 3 * quarter - 2, 1)
    next_start = date(year + 1, 1, 1) if quarter == 4 else date(year, 3 * quarter + 1, 1)
    return start, next_start - timedelta(days=1)


def quarter_volumes(fy_volume, printed_quarters=None):
    """Volume per quarter: printed where given, otherwise FY volume / 4 (assumption A11).

    Inputs: FY volume (tonnes); printed_quarters = {quarter: tonnes}, e.g. {3: 2_680_000}.
    Output: {1: t, 2: t, 3: t, 4: t}. The quarters need not add up to FY when one is printed
    (the equal split is a simple rule, not a reconciliation) - see ASSUMPTIONS.md A11.
    """
    if fy_volume < 0:
        raise ValueError(f"FY volume cannot be negative, got {fy_volume}")
    printed = printed_quarters or {}
    for q in printed:
        if q not in QUARTERS:
            raise ValueError(f"printed quarter must be 1-4, got {q}")
    return {q: printed.get(q, fy_volume / 4) for q in QUARTERS}


def h2_quarter_shares(ask_fy_prev, ask_q1_prev, ask_q2_prev, ask_q4_prev, ask_h1_now, fy_growth):
    """Share of the FY fuel volume falling in Q3 and in Q4, from capacity (ASK) - assumption A11.

    Fuel use is taken as proportional to capacity (the same fuel per seat-km in every quarter). Steps: last year's Q3 is
    the full year minus Q1, Q2 and Q4 (so rounding in the first three is absorbed there); this year's full-year ASK is
    last year's grown by the guided rate; the second half is what is left after the H1 actually flown; and it is split
    between Q3 and Q4 the way last year's second half was.

    Inputs: ASK of last year (full year, Q1, Q2, Q4), ASK actually flown in H1 this year, guided growth for this year
    (e.g. 0.025 for +2.5%). Output: {3: share, 4: share} of this year's full-year volume (Q1 + Q2 + Q3 + Q4 = 1).
    """
    ask_q3_prev = ask_fy_prev - ask_q1_prev - ask_q2_prev - ask_q4_prev
    ask_h2_prev = ask_q3_prev + ask_q4_prev
    if ask_q3_prev <= 0 or ask_h2_prev <= 0:
        raise ValueError("last year's quarters do not add up to its full year")
    ask_fy_now = ask_fy_prev * (1 + fy_growth)
    ask_h2_now = ask_fy_now - ask_h1_now
    if ask_h2_now <= 0:
        raise ValueError("guided full-year capacity is below the first half already flown")
    return {3: ask_h2_now * ask_q3_prev / ask_h2_prev / ask_fy_now,
            4: ask_h2_now * ask_q4_prev / ask_h2_prev / ask_fy_now}


def remaining_quarter_shares(as_of, year):
    """Share of each quarter of `year` still ahead after `as_of` (0 = fully passed, 1 = all ahead).

    Example: as_of 2026-09-30 -> {1: 0, 2: 0, 3: 0, 4: 1}. as_of 2026-11-15 -> Q4 = 46/92.
    """
    shares = {}
    for q in QUARTERS:
        start, end = quarter_bounds(year, q)
        days_in_quarter = (end - start).days + 1
        first_remaining_day = max(start, as_of + timedelta(days=1))
        remaining_days = max(0, (end - first_remaining_day).days + 1)
        shares[q] = remaining_days / days_in_quarter
    return shares


def remaining_volume(volumes_by_quarter, shares_by_quarter):
    """Tonnes still to be bought: sum over quarters of volume x remaining share."""
    return sum(volumes_by_quarter[q] * shares_by_quarter[q] for q in QUARTERS)


def remaining_hedge_ratio(volumes_by_quarter, shares_by_quarter, ratios_by_quarter):
    """Volume-weighted hedge ratio over the remaining part of the year.

    ratios_by_quarter: {quarter: fraction}; only quarters with remaining volume need a ratio.
    Returns None if nothing remains. Raises ValueError if a remaining quarter has no ratio.
    """
    weights = {q: volumes_by_quarter[q] * shares_by_quarter[q] for q in QUARTERS}
    total = sum(weights.values())
    if total == 0:
        return None
    missing = [q for q in QUARTERS if weights[q] > 0 and ratios_by_quarter.get(q) is None]
    if missing:
        raise ValueError(f"no hedge ratio for remaining quarter(s) {missing}")
    return sum(weights[q] * ratios_by_quarter[q] for q in QUARTERS if weights[q] > 0) / total


def month_bounds(year, month):
    """First and last day of a calendar month."""
    start = date(year, month, 1)
    next_start = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, next_start - timedelta(days=1)


def realised_month_fractions(after, until):
    """Share of each calendar month inside the realised window (after `after`, up to `until`).

    Example: after 27 Jul, until 22 Sep 2026 -> Jul 4/31, Aug 1, Sep 22/30.
    Output: {(year, month): fraction}; months with no days in the window are left out.
    """
    out = {}
    year, month = after.year, after.month
    while date(year, month, 1) <= until:
        start, end = month_bounds(year, month)
        first, last = max(start, after + timedelta(days=1)), min(end, until)
        if first <= last:
            out[(year, month)] = ((last - first).days + 1) / ((end - start).days + 1)
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return out


def monthly_volume(volumes_by_quarter, month):
    """Volume of one month = its quarter's volume / 3 (equal months within a quarter, A11)."""
    return volumes_by_quarter[(month - 1) // 3 + 1] / 3
