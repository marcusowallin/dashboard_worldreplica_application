"""Tests for the story numbers (src/story/): yardstick, hero loss share, robustness grid, attribution."""
import copy

import pytest

from src.story.robustness import (
    BENCHMARK_SPLIT, SPLITS, airline_losses, attribution, benchmark_market, break_even_recapture,
    case_inputs, loss_share, ranking_grid, recapture_range, shapley_gap,
)
from src.story.yardstick import expected_operating_profit, poll_cross_check
from src.twins import load_twins

FX = 1.1355
TWINS = load_twins()


# --- yardstick ---------------------------------------------------------------------------------

def test_lufthansa_fy26_uses_guidance_midpoint_with_range():
    y = expected_operating_profit(TWINS, "lufthansa", "FY2026")
    assert (y["value"], y["low"], y["high"], y["level"]) == (1.95e9, 1.7e9, 2.2e9, 1)


def test_iag_fy26_converts_margin_guidance_with_consensus_revenue():
    y = expected_operating_profit(TWINS, "iag", "FY2026")
    assert y["value"] == pytest.approx(0.135 * 34_260e6)
    assert (y["low"], y["high"]) == pytest.approx((0.12 * 34_260e6, 0.15 * 34_260e6))
    assert y["level"] == "L1 x L4"


def test_no_guidance_or_fy27_uses_provider_consensus():
    assert expected_operating_profit(TWINS, "afklm", "FY2026")["value"] == 1_791e6
    for airline, value in (("lufthansa", 2_281e6), ("afklm", 2_140e6), ("iag", 5_054e6)):
        y = expected_operating_profit(TWINS, airline, "FY2027")
        assert y["value"] == value and y["level"] == 4 and not y["fallback"]


def test_missing_consensus_falls_back_to_last_actual_labelled():
    twins = copy.deepcopy(TWINS)
    field = twins["airlines"]["afklm"]["fields"]["consensus_ebit_fy27"]
    field.update(value=None, status="not-disclosed")
    y = expected_operating_profit(twins, "afklm", "FY2027")
    assert y["value"] == 2_069e6 and y["fallback"] and "fallback" in y["source"]


def test_lufthansa_poll_cross_check_within_ten_percent():
    check = poll_cross_check(TWINS)
    assert check["difference"] == pytest.approx(2_281 / 2_493 - 1) and check["within"]


# --- hero loss share ---------------------------------------------------------------------------

def test_iag_fy27_central_loss_share_by_hand():
    """Independent hand calculation: IAG FY27, central mix (50% Brent / 50% jet hedges), +50/+50."""
    market = benchmark_market(BENCHMARK_SPLIT, FX)
    h = 0.4325
    u_brent, u_crack = 1 - h, 1 - h / 2                   # all hedges cover Brent; only jet half covers crack
    d_fuel_eur = 8.61e6 * (u_brent * 50 + u_crack * 50) / FX
    expected = (1 - 0.60) * d_fuel_eur / 5_054e6
    assert loss_share(case_inputs(TWINS, "iag", "FY2027", "central", market), market) == pytest.approx(expected)


def test_recapture_range_is_fifty_percent_up_to_printed():
    assert recapture_range(TWINS, "afklm") == (0.50, 0.85)
    assert recapture_range(TWINS, "lufthansa") == (0.50, 0.60)


def test_airline_losses_cover_every_case_recapture_and_base():
    market = benchmark_market(BENCHMARK_SPLIT, FX)
    assert len(airline_losses(TWINS, "iag", "FY2026", market)) == 3 * 2 * 2     # mix x recapture x base
    assert len(airline_losses(TWINS, "afklm", "FY2027", market)) == 3 * 2 * 1


# --- robustness and attribution ----------------------------------------------------------------

def test_ranking_grid_flags_overlap_from_recapture():
    rows = ranking_grid(TWINS, "FY2027", FX)
    assert [r["split"] for r in rows] == list(SPLITS)
    for r in rows:
        lh_min = r["ranges"]["lufthansa"][0]
        assert r["holds"] == (lh_min > max(r["ranges"]["afklm"][1], r["ranges"]["iag"][1]))
        assert 0 <= r["share_lh_hardest"] <= 1


def test_ranking_holds_when_recapture_is_fixed_at_printed_rates(monkeypatch):
    with_range = ranking_grid(TWINS, "FY2027", FX, splits=(BENCHMARK_SPLIT,))
    monkeypatch.setattr("src.story.robustness.RECAPTURE_LOW", 1.0)    # range collapses to the printed rate
    fixed = ranking_grid(TWINS, "FY2027", FX, splits=(BENCHMARK_SPLIT,))
    assert fixed[0]["holds"] and not with_range[0]["holds"]


def test_break_even_recapture_equalises_losses():
    r_star = break_even_recapture(TWINS, "FY2027", "afklm", FX)
    market = benchmark_market(BENCHMARK_SPLIT, FX)
    lh_best = min(loss for _, loss in airline_losses(TWINS, "lufthansa", "FY2027", market))
    peer = case_inputs(TWINS, "afklm", "FY2027", "crude-only", market, recapture=r_star)
    assert loss_share(peer, market) == pytest.approx(lh_best)


def test_shapley_parts_add_up_to_the_gap():
    for row in attribution(TWINS, "FY2027", "iag", FX) + attribution(TWINS, "FY2026", "afklm", FX):
        assert sum(row["parts"].values()) == pytest.approx(row["gap"])


def test_shapley_is_zero_for_identical_factor():
    market = benchmark_market(BENCHMARK_SPLIT, FX)
    ours = case_inputs(TWINS, "lufthansa", "FY2027", "stale 29%", market)
    peer = dict(ours, recapture=0.85)                    # only recapture differs
    result = shapley_gap(ours, peer, market)
    assert result["parts"]["recapture"] == pytest.approx(result["gap"])
    assert all(v == pytest.approx(0) for k, v in result["parts"].items() if k != "recapture")


def test_loss_ranges_printed_inside_wider_case():
    from src.story.robustness import loss_ranges
    ranges = loss_ranges(TWINS, "FY2027", FX)
    for r in ranges.values():
        assert 0 < r["low"] <= r["high"] <= r["ext_high"]
    # Lufthansa's printed-recapture range sits above both peers' (the hero claim at printed rates)
    assert ranges["lufthansa"]["low"] > max(ranges["afklm"]["high"], ranges["iag"]["high"])
