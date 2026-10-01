"""Number formats - one helper per kind, used everywhere (design notes).

Inputs are in model units: EUR amounts in EUR, shares as fractions (0.117 = 11.7%).
Negatives use a true minus sign (U+2212); ranges use an en dash, or "to" when a sign is involved.
None (missing) always prints as "n/a" - never as 0.
"""
import math
from decimal import ROUND_HALF_UP, Decimal

MINUS = "−"
DASH = "–"
NA = "n/a"


def _signed(text, value, signed):
    if value < 0:
        return MINUS + text
    return ("+" + text) if signed and value > 0 else text


def eur_m(amount_eur, signed=False):
    """1_334e6 -> 'EUR 1,334m'."""
    if amount_eur is None:
        return NA
    return _signed(f"EUR {abs(amount_eur) / 1e6:,.0f}m", round(amount_eur / 1e6), signed)


def eur_bn(amount_eur, signed=False):
    """1_613e6 -> 'EUR 1.6bn' (sentences only; tables use eur_m)."""
    if amount_eur is None:
        return NA
    return _signed(f"EUR {abs(amount_eur) / 1e9:,.1f}bn", round(amount_eur / 1e9, 1), signed)


def pct(share, signed=False, decimals=1):
    """0.1172 -> '11.7%'."""
    if share is None:
        return NA
    return _signed(f"{abs(share) * 100:.{decimals}f}%", round(share * 100, decimals), signed)


def pp(share_difference, signed=True):
    """0.05 -> '+5.0 pp' (difference of two shares, in percentage points)."""
    if share_difference is None:
        return NA
    return _signed(f"{abs(share_difference) * 100:.1f} pp", round(share_difference * 100, 1), signed)


def eur_per_share(value, signed=False):
    """-0.3281 -> '-EUR 0.33'."""
    if value is None:
        return NA
    return _signed(f"EUR {abs(value):.2f}", round(value, 2), signed)


def usd_per_t(value, signed=True):
    """271.2 -> '+USD 271/t'."""
    if value is None:
        return NA
    return _signed(f"USD {abs(value):,.0f}/t", round(value), signed)


def pct_range(low, high, decimals=1):
    """(0.096, 0.117) -> '9.6-11.7%' with an en dash; a single value if both round the same."""
    if low is None or high is None:
        return NA
    low, high = sorted((low, high))
    a, b = f"{low * 100:.{decimals}f}", f"{high * 100:.{decimals}f}"
    if a == b:
        return pct(low, decimals=decimals)
    if low < 0 or high < 0:
        return f"{pct(low, decimals=decimals)} to {pct(high, decimals=decimals)}"
    return f"{a}{DASH}{b}%"


def eur_m_range(low, high):
    """(1_334e6, 1_718e6) -> 'EUR 1,334-1,718m'."""
    if low is None or high is None:
        return NA
    low, high = sorted((low, high))
    if low < 0 or high < 0:
        return f"{eur_m(low)} to {eur_m(high)}"
    a, b = f"{low / 1e6:,.0f}", f"{high / 1e6:,.0f}"
    return f"EUR {a}m" if a == b else f"EUR {a}{DASH}{b}m"


# --- story page: whole numbers (decision 30 Sep 2026); one decimal only on "Method & sources" -------------


def _half_up(value, step=1):
    """Round to the nearest multiple of `step`, halves away from zero (4.5 -> 5, not Python's 4)."""
    return float((Decimal(str(value)) / Decimal(str(step))).quantize(Decimal(1), rounding=ROUND_HALF_UP)
                 * Decimal(str(step)))


def eur_m_step(amount_eur):
    """Rounding step for EUR m on the story page: 1m below 100m, 5m below 1,000m, 10m above."""
    size = abs(amount_eur) / 1e6
    return 1 if size < 100 else 5 if size < 1000 else 10


def story_eur_m(amount_eur):
    """219.4e6 -> 'EUR 220m' (story rounding)."""
    if amount_eur is None:
        return NA
    rounded = _half_up(amount_eur / 1e6, eur_m_step(amount_eur))
    return _signed(f"EUR {abs(rounded):,.0f}m", rounded, False)


def _outward(low, high, step):
    """Round a range outward - low end down, high end up - so the printed range always contains the computed one."""
    return math.floor(round(low / step, 9)) * step, math.ceil(round(high / step, 9)) * step


def story_eur_m_range(low, high):
    """(218.5e6, 266.8e6) -> 'EUR 215-270m'; outward rounding, one step size for both ends (the larger end decides)."""
    if low is None or high is None:
        return NA
    low, high = sorted((low, high))
    step = eur_m_step(max(abs(low), abs(high)))
    a, b = _outward(low / 1e6, high / 1e6, step)
    if a == b:
        return _signed(f"EUR {abs(a):,.0f}m", a, False)
    if a < 0 or b < 0:
        return (f"{_signed(f'EUR {abs(a):,.0f}m', a, False)} to {_signed(f'EUR {abs(b):,.0f}m', b, False)}")
    return f"EUR {a:,.0f}{DASH}{b:,.0f}m"


def story_pct(share):
    """0.117 -> '12%' (whole number, halves up)."""
    if share is None:
        return NA
    rounded = _half_up(share * 100)
    return _signed(f"{abs(rounded):.0f}%", rounded, False)


def story_pct_range(low, high):
    """(0.096, 0.117) -> '10-12%'; nearest whole number at both ends (outward rounding would turn a computed 0.6-1.2%
    into '0-2%'); collapses to one value when both ends round the same ('1%')."""
    if low is None or high is None:
        return NA
    low, high = sorted((low, high))
    a, b = _half_up(low * 100) + 0.0, _half_up(high * 100) + 0.0         # + 0.0 turns a negative zero into 0
    if a == b:
        return story_pct(low)
    if a < 0 or b < 0:
        return f"{story_pct(low)} to {story_pct(high)}"
    return f"{a:.0f}{DASH}{b:.0f}%"


def story_eur_bn_range(low, high):
    """(1_613e6, 2_266e6) -> 'EUR 1.6-2.3bn' (sentences)."""
    if low is None or high is None:
        return NA
    low, high = sorted((low, high))
    a, b = _half_up(low / 1e9, 0.1), _half_up(high / 1e9, 0.1)
    return f"EUR {a:.1f}bn" if a == b else f"EUR {a:.1f}{DASH}{b:.1f}bn"


def approx_fraction(share):
    """Plain-words version of a threshold: 0.68 -> 'about two-thirds', 0.51 -> 'about half', else 'about 70%'."""
    words = ((0.5, "half"), (2 / 3, "two-thirds"), (0.75, "three-quarters"), (1 / 3, "a third"), (0.25, "a quarter"))
    for value, word in words:
        if abs(share - value) <= 0.035:
            return f"about {word}"
    return f"about {_half_up(share * 100, 5):.0f}%"


def story_mt(tonnes):
    """2_355_000 -> '2.4m t' (million tonnes, one decimal - volumes need it to be readable)."""
    if tonnes is None:
        return NA
    return f"{_half_up(tonnes / 1e6, 0.1):.1f}m t"


def story_mt_range(low, high):
    """(4.71e6, 6.69e6) -> '4.7-6.7m t'."""
    if low is None or high is None:
        return NA
    low, high = sorted((low, high))
    a, b = _half_up(low / 1e6, 0.1), _half_up(high / 1e6, 0.1)
    return f"{a:.1f}m t" if a == b else f"{a:.1f}{DASH}{b:.1f}m t"


# Exceptions to whole numbers on the story page (decision 1 Oct 2026): margins and percentage points keep one
# decimal (a 0.5 pp change would otherwise read as 1 pp), EPS keeps euro cents.
def story_margin(share):
    """0.0517 -> '5.2%'."""
    return NA if share is None else _signed(f"{abs(_half_up(share * 100, 0.1)):.1f}%", share, False)


def story_pp_range(low, high, signed=False):
    """(-0.0063, -0.0051) -> '-0.6 to -0.5 pp' (one decimal)."""
    if low is None or high is None:
        return NA
    low, high = sorted((low, high))
    a, b = _half_up(low * 100, 0.1), _half_up(high * 100, 0.1)
    spans_zero = a < 0 < b
    fmt = lambda v: _signed(f"{abs(v):.1f}", v, spans_zero or signed)             # noqa: E731  (+ only when the range spans 0)
    return f"{fmt(a)} pp" if a == b else f"{fmt(a)} to {fmt(b)} pp"


def story_margin_range(low, high):
    """(0.0454, 0.0466) -> '4.5-4.7%'."""
    if low is None or high is None:
        return NA
    low, high = sorted((low, high))
    a, b = _half_up(low * 100, 0.1), _half_up(high * 100, 0.1)
    return f"{a:.1f}%" if a == b else f"{a:.1f}{DASH}{b:.1f}%"


def story_eur_share_range(low, high):
    """EUR per share, two decimals: (1.138, 1.170) -> 'EUR 1.14-1.17'; negatives '-EUR 0.16 to -EUR 0.13'."""
    if low is None or high is None:
        return NA
    low, high = sorted((low, high))
    a, b = _half_up(low, 0.01), _half_up(high, 0.01)
    if a == b:
        return eur_per_share(a)
    if a < 0 or b < 0:
        return f"{eur_per_share(a)} to {eur_per_share(b)}"
    return f"EUR {a:.2f}{DASH}{b:.2f}"
