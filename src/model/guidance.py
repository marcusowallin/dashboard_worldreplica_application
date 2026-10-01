"""EPS versus baseline, flags and competitive gap (06_METHODOLOGY.md section 6).

All inputs in model units: EUR amounts, EUR per share, fractions (0.05 = 5%). Pure functions.

Baseline hierarchy: third-party consensus EPS (primary), else last full-year EPS (fallback,
labelled "not consensus"). Guidance is context only (position within the range).
"""

MATERIALITY_THRESHOLD = 0.05   # |dEBIT| >= 5% of profit reference, or |dEPS| >= 5% of baseline EPS
_TOLERANCE = 1e-12             # so that exactly 5.0% counts as material despite float rounding


def select_baseline_eps(consensus_eps, fallback_eps):
    """Pick the EPS baseline and say where it came from.

    Returns (value, source) with source "consensus" or "fallback: last full-year EPS (not consensus)",
    or (None, "no baseline") if neither is available.
    """
    if consensus_eps is not None:
        return consensus_eps, "consensus"
    if fallback_eps is not None:
        return fallback_eps, "fallback: last full-year EPS (not consensus)"
    return None, "no baseline"


def change_as_share(change, base):
    """change / base as a fraction, or None when base is missing, zero or negative.

    A percentage of a negative or zero baseline is not meaningful (the sign flips), so the page
    shows "n/m" instead of a misleading number.
    """
    if base is None or base <= 0:
        return None
    return change / base


def favourability(d_eps):
    """'favourable' if dEPS > 0, 'unfavourable' if < 0, 'neutral' if exactly 0."""
    if d_eps > 0:
        return "favourable"
    if d_eps < 0:
        return "unfavourable"
    return "neutral"


def is_material(d_ebit_share, d_eps_share, threshold=MATERIALITY_THRESHOLD):
    """Material if |dEBIT / profit reference| >= threshold OR |dEPS / baseline EPS| >= threshold.

    Either share may be None (not meaningful); a None never makes the flag True on its own.
    """
    for share in (d_ebit_share, d_eps_share):
        if share is not None and abs(share) >= threshold - _TOLERANCE:
            return True
    return False


def position_in_range(low, high, value):
    """Where a value sits in a guidance range: 0 = low end, 1 = high end (can be <0 or >1).

    Returns (position, label) with label "below range", "lower half", "upper half" or "above range".
    """
    if high <= low:
        raise ValueError(f"guidance range must have high > low, got {low}-{high}")
    position = (value - low) / (high - low)
    if position < 0:
        label = "below range"
    elif position > 1:
        label = "above range"
    elif position < 0.5:
        label = "lower half"
    else:
        label = "upper half"
    return position, label


def guidance_shift(low, high, change, anchor=None):
    """Move a guidance anchor (default: the range midpoint) by a change and locate the result.

    Example: LH Adj. EBIT guidance EUR 1.7-2.2bn, midpoint 1.95bn; a dEBIT of -0.2bn moves it to
    1.75bn -> position 0.10, "lower half". Returns (new_value, position, label).
    """
    start = (low + high) / 2 if anchor is None else anchor
    new_value = start + change
    position, label = position_in_range(low, high, new_value)
    return new_value, position, label


def competitive_gap(peer_share, our_share):
    """Our dEPS % minus the peer's dEPS % (methodology section 6, sign fixed 30 Sep 2026).

    Positive = the peer is hurt MORE than us. dEPS shares are negative when fuel rises:
      us -5%, peer -6% -> gap +1 pp: the peer is hurt more (we are less exposed).
      us -5%, peer -3% -> gap -2 pp: we are hurt more than the peer.
    Returns None if either share is None.
    """
    if peer_share is None or our_share is None:
        return None
    return our_share - peer_share
