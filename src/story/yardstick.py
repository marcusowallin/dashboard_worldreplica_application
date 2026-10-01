"""Yardstick: the operating profit EXPECTED for the same year, used as the base for "% of operating profit".

Hierarchy per airline and year (decision 30 Sep 2026, ASSUMPTIONS.md A26):
  1. the company's own printed projection for that year
       - an amount (Lufthansa FY2026 Adj. EBIT EUR 1.7-2.2bn): midpoint, range kept
       - a margin (IAG FY2026 12-15%): margin x revenue, revenue from the same hierarchy
         (no printed revenue projection -> consensus revenue, level 4)
  2. analyst consensus EBIT from one provider for all three (MarketScreener, level 4)
  3. last actual year (FY2025 adjusted operating profit), labelled as a fallback
Guidance exists only for FY2026; FY2027 always starts at step 2.
All amounts in EUR (model units).
"""
from src.twins import get_field, get_model_value

CROSS_CHECK_THRESHOLD = 0.10   # 06_METHODOLOGY.md section 6: consensus cross-check within 10%
_SUFFIX = {"FY2026": "fy26", "FY2027": "fy27"}


def expected_operating_profit(twins, airline, period):
    """Expected operating profit for one airline and year, with its range, level and source.

    Output: {"value", "low", "high" (EUR), "level" (int or "L1 x L4"), "source" (short label),
             "as_of" (date string of the youngest input), "fallback" (True if last actual used)}.
    """
    suffix = _SUFFIX[period]
    if period == "FY2026":
        guided = _from_guidance(twins, airline)
        if guided:
            return guided
    consensus = get_model_value(twins, airline, f"consensus_ebit_{suffix}")
    if consensus is not None:
        field = get_field(twins, airline, f"consensus_ebit_{suffix}")
        return {"value": consensus, "low": consensus, "high": consensus, "level": field["level"],
                "source": "analyst consensus EBIT (MarketScreener)", "as_of": field["as_of"],
                "fallback": False}
    actual = get_model_value(twins, airline, "adj_operating_profit_fy25")
    field = get_field(twins, airline, "adj_operating_profit_fy25")
    return {"value": actual, "low": actual, "high": actual, "level": field["level"],
            "source": "last actual (FY2025 adjusted operating profit) - fallback", "as_of": field["as_of"],
            "fallback": True}


def _from_guidance(twins, airline):
    """Level-1 projection from printed guidance, or None if the airline gives none."""
    low_field = get_field(twins, airline, "guidance_low")
    low = get_model_value(twins, airline, "guidance_low")
    high = get_model_value(twins, airline, "guidance_high")
    if low is None or high is None:
        return None
    if low_field["unit"] == "% operating margin":
        revenue = get_model_value(twins, airline, "consensus_revenue_fy26")
        if revenue is None:
            return None
        revenue_field = get_field(twins, airline, "consensus_revenue_fy26")
        return {"value": (low + high) / 2 * revenue, "low": low * revenue, "high": high * revenue,
                "level": "L1 x L4",
                "source": (f"company margin guidance {low_field['value']}-{get_field(twins, airline, 'guidance_high')['value']}% "
                           "x analyst consensus revenue (MarketScreener)"),
                "as_of": max(low_field["as_of"], revenue_field["as_of"]), "fallback": False}
    return {"value": (low + high) / 2, "low": low, "high": high, "level": low_field["level"],
            "source": "company guidance (midpoint of the printed range)", "as_of": low_field["as_of"],
            "fallback": False}


def poll_cross_check(twins, airline="lufthansa"):
    """Provider consensus FY2027 EBIT vs the company's own poll median (10% rule).

    Output: {"provider", "poll", "difference" (fraction, provider vs poll), "within" (bool)} or None.
    """
    provider = get_model_value(twins, airline, "consensus_ebit_fy27")
    poll = get_model_value(twins, airline, "poll_ebit_fy27")
    if provider is None or poll is None:
        return None
    difference = provider / poll - 1
    return {"provider": provider, "poll": poll, "difference": difference,
            "within": abs(difference) <= CROSS_CHECK_THRESHOLD}


def expected_revenue(twins, airline, period):
    """Revenue expected for the same year, for the operating margin (Step 6). Same hierarchy as the profit:
    company projection (none printed for revenue) -> MarketScreener consensus revenue (L4) -> FY2025 actual.

    Output: {"value", "level", "source", "as_of", "fallback"}.
    """
    suffix = _SUFFIX[period]
    consensus = get_model_value(twins, airline, f"consensus_revenue_{suffix}")
    if consensus is not None:
        field = get_field(twins, airline, f"consensus_revenue_{suffix}")
        return {"value": consensus, "level": field["level"], "source": "analyst consensus revenue (MarketScreener)",
                "as_of": field["as_of"], "fallback": False}
    field = get_field(twins, airline, "revenue_fy25")
    return {"value": get_model_value(twins, airline, "revenue_fy25"), "level": field["level"],
            "source": "last actual (FY2025 revenue) - fallback", "as_of": field["as_of"], "fallback": True}
