"""The choices that can move the answer (src/story/choices.py): each checked against a hand calculation."""
from datetime import date, timedelta

import pytest

from src.model.fuel import unprotected_shares
from src.model.run import _lufthansa_mix
from src.story.choices import (
    LH_VARIANTS, lufthansa_range, net_cost_per_tonne, options_fade_factors, pass_through_base, persistence_table,
    smoothed_move,
)
from src.story.costs import cost_cases
from src.story.robustness import benchmark_market, loss_ranges
from src.twins import get_model_value, load_twins
from src.validation import remaining_share, table_implied_exposures

TWINS = load_twins()
FX = 1.1298
SPLIT = (41.0, 59.0)


def test_persistence_scales_every_loss_and_never_changes_the_order():
    rows = {r["share"]: r for r in persistence_table(TWINS, FX, SPLIT)}
    full, half = rows[1.0]["ranges"], rows[0.5]["ranges"]
    for airline in full:                                    # the model is linear in the move: half the shock, half the loss
        assert half[airline]["low"] == pytest.approx(full[airline]["low"] / 2)
        assert half[airline]["cost_high"] == pytest.approx(full[airline]["cost_high"] / 2)
    assert full == loss_ranges(TWINS, "FY2027", FX, SPLIT)  # 100% is the hero
    assert all(r["lufthansa_hardest"] for r in rows.values())


def test_options_fade_factors_by_hand():
    market = benchmark_market(SPLIT, FX)
    share = remaining_share(get_model_value(TWINS, "lufthansa", "fuel_volume_fy26"),
                            get_model_value(TWINS, "lufthansa", "fuel_volume_q3_26"))
    table = table_implied_exposures(share, brent_up=True, crack_up=True)
    h, mix = get_model_value(TWINS, "lufthansa", "hedge_ratio_rest_fy26"), _lufthansa_mix(TWINS)
    u_b, u_c = unprotected_shares(h * mix["brent"], h * mix["gasoil"], h * mix["jet"], 0.8)
    f_b, f_c = options_fade_factors(TWINS, market)
    assert f_b == pytest.approx((1 - table["u_brent"]) / (1 - u_b)) and f_c == pytest.approx((1 - table["u_crack"]) / (1 - u_c))
    assert 0 < f_b < f_c < 1                                # options protect less than swaps, Brent worst (validation T2)


def test_lufthansa_range_brackets_the_hero_and_orders_the_variants():
    result = lufthansa_range(TWINS, FX, SPLIT)
    by = {v["name"]: v for v in result["variants"]}
    hero = loss_ranges(TWINS, "FY2027", FX, SPLIT)["lufthansa"]
    assert [v["name"] for v in result["variants"]] == list(LH_VARIANTS)
    assert by["printed mix"]["low"] == pytest.approx(hero["low"]) and by["printed mix"]["cost_high"] == pytest.approx(hero["cost_high"])
    assert by["all gasoil hedges"]["high"] < by["printed mix"]["high"] < by["all Brent hedges"]["high"]   # gasoil protects the crack
    assert by["options fade"]["low"] > by["printed mix"]["low"] and by["options fade"]["high"] > by["printed mix"]["high"]
    assert result["full"]["low"] == min(v["low"] for v in result["variants"]) and result["full"]["high"] == by["options fade"]["high"]
    assert result["full"]["low"] < hero["low"] and result["full"]["high"] > hero["high"]      # the honest range is wider


def test_lufthansa_range_stays_below_nothing_but_above_the_peers():
    """Even the mildest Lufthansa variant is above the peers' worst case at the printed pass-through."""
    result = lufthansa_range(TWINS, FX, SPLIT)
    peers = loss_ranges(TWINS, "FY2027", FX, SPLIT)
    assert result["full"]["low"] > max(peers["afklm"]["high"], peers["iag"]["high"])


def test_pass_through_base_by_hand_and_the_flip():
    result = pass_through_base(TWINS, FX, SPLIT)
    market = benchmark_market(SPLIT, FX)
    nets = cost_cases(TWINS, "FY2027", FX, SPLIT)
    for airline, rows in nets.items():                                         # 'model' is exactly Step 5's net cost
        assert result[airline]["model"] == pytest.approx((min(r["net"] for r in rows), max(r["net"] for r in rows)))
    # Air France-KLM, jet-equivalent mix, by hand: gross - r x V x move / FX
    afklm = get_model_value(TWINS, "afklm", "recapture_rate")
    volume = get_model_value(TWINS, "afklm", "fuel_volume_fy26")                  # tonnes
    expected = min(r["gross"] - afklm * volume * (market["d_brent"] + market["d_crack"]) / FX for r in nets["afklm"])
    assert result["afklm"]["market"][0] == pytest.approx(expected)
    assert result["afklm"]["flips"] and not result["lufthansa"]["flips"]      # AF-KLM turns from cost to gain


def test_net_cost_per_tonne_is_net_cost_over_volume():
    per_t = net_cost_per_tonne(TWINS, FX, SPLIT)
    nets = cost_cases(TWINS, "FY2027", FX, SPLIT)["lufthansa"]
    volume = get_model_value(TWINS, "lufthansa", "fuel_volume_fy26")              # tonnes
    assert per_t["lufthansa"] == pytest.approx((min(r["net"] for r in nets) / volume, max(r["net"] for r in nets) / volume))
    assert per_t["afklm"][1] < per_t["lufthansa"][0]                          # Air France-KLM is the least exposed per tonne


def test_smoothed_move_differs_from_the_single_day_move_when_the_baseline_day_is_a_dip():
    from src.data_sources import moves_since_baseline
    base = date(2026, 7, 27)
    prices = {base - timedelta(days=i): (1000.0, 700.0, 300.0) for i in range(30, 0, -1)}   # flat before the baseline
    prices[base] = (900.0, 650.0, 250.0)                                                     # one-day dip on 27 July
    prices.update({base + timedelta(days=i): (1300.0, 800.0, 500.0) for i in range(1, 11)})  # then a jump that stays
    raw = moves_since_baseline(prices, base)["d_jet"]
    smooth_move = smoothed_move(prices, base)["d_jet"]
    assert raw == pytest.approx(400.0)                       # 1,300 - 900
    assert smooth_move < raw and smooth_move > 0              # baseline = average of five days (dip + four flat days)
    assert smoothed_move({}, base) is None
