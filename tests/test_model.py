"""Tests for the model (src/model/). Start: fuel cost with hedge quality (methodology section 3)."""
from datetime import date

import pytest

from src.model.decomposition import (
    eps_impact_share, main_driver, robust_driver, waterfall,
)
from src.model.fuel import (
    effective_protection, fuel_cost_change_usd, scale_printed_mix,
    undisclosed_mix_range, unprotected_shares, usd_to_eur,
)
from src.model.income import ebit_change, eps_change, income_chain, net_income_change
from src.model.periods import (
    monthly_volume, quarter_bounds, quarter_volumes, realised_month_fractions,
    remaining_hedge_ratio, remaining_quarter_shares, remaining_volume,
)
from src.model.guidance import (
    change_as_share, competitive_gap, favourability, guidance_shift, is_material,
    position_in_range, select_baseline_eps,
)


# --- Methodology section 10 walk-through (hypothetical numbers, NOT real data) ------------
# Airline X, rest of year: V = 2.0m t; hB 30%, hG 40%, hJ 10%; g = 0.8
# Move: dB = +40 USD/t, dC = +60 USD/t (dJ = +100)
#   u_B = 1 - 0.3 - 0.4 - 0.1 = 0.20
#   u_C = 1 - 0.8*0.4 - 0.1   = 0.58
#   dFuel_USD = 2.0m * (0.20*40 + 0.58*60) = 2.0m * 42.8 = USD 85.6m
#   X = 1.15 -> dFuel_EUR = 85.6m / 1.15 = EUR 74.43m
#   Effective protection = 1 - 42.8/100 = 57.2% (reported hedge ratio 80%)

def test_walkthrough_section_10():
    u_b, u_c = unprotected_shares(0.3, 0.4, 0.1, g=0.8)
    assert u_b == pytest.approx(0.20)
    assert u_c == pytest.approx(0.58)
    d_fuel = fuel_cost_change_usd(2_000_000, u_b, u_c, 40, 60)
    assert d_fuel == pytest.approx(85_600_000)
    assert usd_to_eur(d_fuel, 1.15) == pytest.approx(74_434_783, rel=1e-6)
    assert effective_protection(u_b, u_c, 40, 60) == pytest.approx(0.572)


# --- signs ---------------------------------------------------------------------------------

def test_price_up_raises_cost_price_down_lowers_it():
    u_b, u_c = unprotected_shares(0.3, 0.3, 0.0)
    assert fuel_cost_change_usd(1_000, u_b, u_c, 50, 50) > 0
    assert fuel_cost_change_usd(1_000, u_b, u_c, -50, -50) < 0


def test_fully_jet_hedged_has_no_exposure():
    u_b, u_c = unprotected_shares(0, 0, 1.0)
    assert fuel_cost_change_usd(1_000, u_b, u_c, 40, 60) == 0


def test_unhedged_pays_the_full_move():
    u_b, u_c = unprotected_shares(0, 0, 0)
    assert fuel_cost_change_usd(1_000, u_b, u_c, 40, 60) == pytest.approx(100_000)


def test_brent_hedge_gives_no_crack_protection():
    # 100% Brent-hedged: protected against Brent, fully exposed to the crack
    u_b, u_c = unprotected_shares(1.0, 0, 0)
    assert (u_b, u_c) == (0, 1)


def test_gasoil_protects_share_g_of_crack():
    _, u_c = unprotected_shares(0, 1.0, 0, g=0.8)
    assert u_c == pytest.approx(0.2)


# --- units and invalid inputs ----------------------------------------------------------------

def test_usd_to_eur_divides_by_usd_per_eur():
    assert usd_to_eur(115, 1.15) == pytest.approx(100)


@pytest.mark.parametrize("rate", [0, -1.1])
def test_usd_to_eur_rejects_bad_rate(rate):
    with pytest.raises(ValueError):
        usd_to_eur(100, rate)


@pytest.mark.parametrize("shares", [(0.5, 0.4, 0.2), (-0.1, 0, 0), (0, 1.2, 0)])
def test_unprotected_shares_rejects_impossible_hedges(shares):
    with pytest.raises(ValueError):
        unprotected_shares(*shares)


def test_negative_volume_rejected():
    with pytest.raises(ValueError):
        fuel_cost_change_usd(-1, 0.2, 0.5, 10, 10)


def test_effective_protection_undefined_for_zero_move():
    with pytest.raises(ValueError):
        effective_protection(0.2, 0.5, 30, -30)


# --- approved rules A1 and A5 ----------------------------------------------------------------

def test_scale_printed_mix_lufthansa_rule():
    # A1: 0.82 * 48/81 = 0.48593 gasoil; 0.82 * 33/81 = 0.33407 Brent; sums to 0.82
    mix = scale_printed_mix(0.82, {"gasoil": 48, "brent": 33, "jet": 0})
    assert mix["gasoil"] == pytest.approx(0.485926, rel=1e-5)
    assert mix["brent"] == pytest.approx(0.334074, rel=1e-5)
    assert mix["jet"] == 0
    assert sum(mix.values()) == pytest.approx(0.82)


def test_undisclosed_mix_range():
    # A5: V = 1,000 t, h = 0.67, dB = 40, dC = 60
    # jet-equivalent: 1,000 * (0.33*40 + 0.33*60) = 33,000
    # crude-only:     1,000 * (0.33*40 + 1.00*60) = 73,200
    # central = 53,100; width = V * h * dC = 1,000 * 0.67 * 60 = 40,200
    r = undisclosed_mix_range(1_000, 0.67, 40, 60)
    assert r["jet_equivalent"] == pytest.approx(33_000)
    assert r["crude_only"] == pytest.approx(73_200)
    assert r["central"] == pytest.approx(53_100)
    assert r["crude_only"] - r["jet_equivalent"] == pytest.approx(1_000 * 0.67 * 60)


# --- Income statement chain (methodology section 5) -----------------------------------------

# Section 10 walk-through continued (hypothetical):
#   dFuel_EUR = 85.6m / 1.15 = 74.4348m
#   r = 60%      -> dEBIT = -0.4 * 74.4348m = -29.7739m
#   t = 25%, m=0 -> dNI   = -29.7739m * 0.75 = -22.3304m
#   N = 1,200m   -> dEPS  = -22.3304m / 1,200m = -0.018609 EUR/share

def test_walkthrough_section_10_income_chain():
    d_fuel_eur = 85_600_000 / 1.15
    chain = income_chain(d_fuel_eur, recapture=0.60, tax_rate=0.25, minority_share=0.0,
                         diluted_shares=1_200_000_000)
    assert chain["d_revenue"] == pytest.approx(44_660_870, rel=1e-6)
    assert chain["d_ebit"] == pytest.approx(-29_773_913, rel=1e-6)
    assert chain["d_net_income"] == pytest.approx(-22_330_435, rel=1e-6)
    assert chain["d_eps"] == pytest.approx(-0.018609, rel=1e-4)


def test_recapture_zero_passes_full_cost_to_ebit():
    assert ebit_change(100.0, 0.0) == -100.0


def test_recapture_full_leaves_ebit_unchanged():
    assert ebit_change(100.0, 1.0) == 0.0


def test_fuel_price_fall_raises_ebit():
    assert ebit_change(-100.0, 0.6) == pytest.approx(40.0)


def test_minorities_reduce_shareholders_share():
    # dEBIT -100, t 25%, m 10% -> -100 * 0.75 * 0.90 = -67.5
    assert net_income_change(-100.0, 0.25, 0.10) == pytest.approx(-67.5)


@pytest.mark.parametrize("bad", [-0.1, 1.2])
def test_rates_outside_zero_one_rejected(bad):
    with pytest.raises(ValueError):
        ebit_change(100.0, bad)
    with pytest.raises(ValueError):
        net_income_change(-100.0, bad, 0.0)
    with pytest.raises(ValueError):
        net_income_change(-100.0, 0.25, bad)


def test_zero_shares_rejected():
    with pytest.raises(ValueError):
        eps_change(-1.0, 0)


# --- EPS vs baseline and flags (methodology section 6) ---------------------------------------


def test_baseline_prefers_consensus_then_fallback():
    assert select_baseline_eps(0.92, 1.12) == (0.92, "consensus")
    assert select_baseline_eps(None, 1.12)[1].startswith("fallback")
    assert select_baseline_eps(None, None) == (None, "no baseline")


def test_walkthrough_section_10_eps_share():
    # dEPS -0.018609 on baseline 1.00 -> -1.86% -> unfavourable, not material at 5%
    share = change_as_share(-0.018609, 1.00)
    assert share == pytest.approx(-0.018609)
    assert favourability(-0.018609) == "unfavourable"
    assert is_material(None, share) is False


@pytest.mark.parametrize("base", [0, -0.5, None])
def test_share_of_zero_negative_or_missing_base_is_not_meaningful(base):
    assert change_as_share(-0.1, base) is None


def test_materiality_exactly_at_five_percent_is_material():
    # dEBIT -98m on profit reference 1,960m = exactly 5.0%
    assert is_material(change_as_share(-98, 1_960), None) is True


def test_materiality_just_below_threshold_is_not_material():
    assert is_material(change_as_share(-97.9, 1_960), -0.0499) is False


def test_materiality_eps_alone_can_trigger():
    assert is_material(-0.01, -0.06) is True


def test_favourability_signs():
    assert favourability(0.01) == "favourable"
    assert favourability(0.0) == "neutral"


def test_guidance_shift_lufthansa_example():
    # Guidance 1.7-2.2bn, midpoint 1.95bn, dEBIT -0.2bn -> 1.75bn -> position 0.10, lower half
    value, position, label = guidance_shift(1.7, 2.2, -0.2)
    assert value == pytest.approx(1.75)
    assert position == pytest.approx(0.10)
    assert label == "lower half"


def test_position_labels_outside_range():
    assert position_in_range(1.7, 2.2, 1.6)[1] == "below range"
    assert position_in_range(1.7, 2.2, 2.3)[1] == "above range"
    with pytest.raises(ValueError):
        position_in_range(2.2, 1.7, 2.0)


def test_competitive_gap_sign():
    # gap = ours - peer's; positive = peer hurt more than us
    assert competitive_gap(-0.06, -0.05) == pytest.approx(0.01)   # peer hurt more
    assert competitive_gap(-0.03, -0.05) == pytest.approx(-0.02)  # we are hurt more
    assert competitive_gap(None, -0.05) is None


# --- Time split (methodology section 4, P1 part) ---------------------------------------------

def test_quarter_bounds():
    assert quarter_bounds(2026, 4) == (date(2026, 10, 1), date(2026, 12, 31))
    assert quarter_bounds(2026, 1) == (date(2026, 1, 1), date(2026, 3, 31))


def test_quarter_volumes_printed_and_equal_split():
    # LH: FY 9.42m t, printed Q3 2.68m t -> other quarters 9.42/4 = 2.355m t (A11)
    q = quarter_volumes(9_420_000, {3: 2_680_000})
    assert q[3] == 2_680_000
    assert q[4] == pytest.approx(2_355_000)


def test_remaining_at_end_of_september_is_q4_only():
    assert remaining_quarter_shares(date(2026, 9, 30), 2026) == {1: 0, 2: 0, 3: 0, 4: 1}


def test_remaining_mid_quarter_by_days():
    # as of 15 Nov: 16 Nov-31 Dec = 46 days of Q4's 92
    shares = remaining_quarter_shares(date(2026, 11, 15), 2026)
    assert shares[4] == pytest.approx(46 / 92)
    assert shares[3] == 0


def test_remaining_from_baseline_date():
    # as of 27 Jul: 28 Jul-30 Sep = 65 days of Q3's 92; Q4 whole
    shares = remaining_quarter_shares(date(2026, 7, 27), 2026)
    assert shares[3] == pytest.approx(65 / 92)
    assert shares[4] == 1


def test_remaining_volume_and_weighted_hedge_ratio():
    # IAG-like: FY 8.61m t, equal quarters 2.1525m t; as of 27 Jul; Q3 74%, Q4 65%
    # volume = 2.1525m * 65/92 + 2.1525m = 1.52079m + 2.1525m = 3.67329m t
    # ratio = (1.52079*0.74 + 2.1525*0.65) / 3.67329 = 0.68726
    vols = quarter_volumes(8_610_000)
    shares = remaining_quarter_shares(date(2026, 7, 27), 2026)
    assert remaining_volume(vols, shares) == pytest.approx(3_673_288, rel=1e-5)
    ratio = remaining_hedge_ratio(vols, shares, {3: 0.74, 4: 0.65})
    assert ratio == pytest.approx(0.68726, rel=1e-4)


def test_remaining_hedge_ratio_needs_a_ratio_for_each_remaining_quarter():
    vols = quarter_volumes(8_000_000)
    shares = remaining_quarter_shares(date(2026, 7, 27), 2026)
    with pytest.raises(ValueError):
        remaining_hedge_ratio(vols, shares, {4: 0.65})


def test_nothing_remaining_returns_none():
    vols = quarter_volumes(8_000_000)
    shares = remaining_quarter_shares(date(2026, 12, 31), 2026)
    assert remaining_volume(vols, shares) == 0
    assert remaining_hedge_ratio(vols, shares, {}) is None


# --- Main driver waterfall (methodology section 8, P1 part) ---------------------------------

BASE = {  # hypothetical airline, round numbers
    "volume_t": 1_000_000, "hedge_ratio": 0.8, "mix": {"brent": 0.5, "gasoil": 0.5, "jet": 0.0},
    "recapture": 0.6, "tax": 0.25, "minority": 0.0, "shares": 1_000_000_000, "baseline_eps": 1.0,
}


def test_eps_impact_share_by_hand():
    # hB 0.4, hG 0.4, hJ 0; g 0.8 -> uB 0.2, uC 1 - 0.32 = 0.68
    # move +40 / +60: per tonne 0.2*40 + 0.68*60 = 48.8 -> USD 48.8m -> EUR 48.8m at 1.0
    # dEBIT = -0.4 * 48.8m = -19.52m; dNI = -14.64m; dEPS = -0.01464 -> -1.464% of 1.00
    r = eps_impact_share(BASE, 40, 60, 1.0)
    assert r["d_eps"] == pytest.approx(-0.01464)
    assert r["d_eps_share"] == pytest.approx(-0.01464)


def test_waterfall_bars_add_up_to_the_gap():
    peer = dict(BASE, hedge_ratio=0.4, mix={"jet": 1.0}, recapture=0.85, tax=0.24,
                baseline_eps=0.8)
    w = waterfall(BASE, peer, 40, 60, 1.0)
    assert sum(change for _, change in w["bars"]) == pytest.approx(w["end"] - w["start"])
    assert w["end"] == pytest.approx(eps_impact_share(peer, 40, 60, 1.0)["d_eps_share"])


def test_only_one_difference_gives_one_bar():
    peer = dict(BASE, recapture=0.85)
    w = waterfall(BASE, peer, 40, 60, 1.0)
    bars = dict(w["bars"])
    assert bars["hedge ratio"] == 0 and bars["hedge quality"] == 0
    assert bars["recapture"] != 0
    assert main_driver(w["bars"]) == "recapture"


def test_central_case_equals_midpoint_of_range():
    jet = eps_impact_share(dict(BASE, mix={"jet": 1.0}), 40, 60, 1.0)["d_eps"]
    crude = eps_impact_share(dict(BASE, mix={"brent": 1.0}), 40, 60, 1.0)["d_eps"]
    mid = eps_impact_share(dict(BASE, mix={"brent": 0.5, "jet": 0.5}), 40, 60, 1.0)["d_eps"]
    assert mid == pytest.approx((jet + crude) / 2)


def test_robust_driver_only_when_all_cases_agree():
    a = {"bars": [("hedge ratio", -0.02), ("recapture", 0.01)]}
    b = {"bars": [("hedge ratio", -0.03), ("recapture", 0.01)]}
    c = {"bars": [("hedge ratio", -0.01), ("recapture", 0.02)]}
    assert robust_driver([a, b]) == "hedge ratio"
    assert robust_driver([a, c]) is None


def test_waterfall_refuses_meaningless_baseline():
    with pytest.raises(ValueError):
        waterfall(BASE, dict(BASE, baseline_eps=-0.5), 40, 60, 1.0)


def test_mix_must_sum_to_one():
    with pytest.raises(ValueError):
        eps_impact_share(dict(BASE, mix={"brent": 0.5}), 40, 60, 1.0)


def test_realised_month_fractions_by_hand():
    # after 27 Jul, until 22 Sep: 28-31 Jul = 4/31, all of Aug, 1-22 Sep = 22/30
    f = realised_month_fractions(date(2026, 7, 27), date(2026, 9, 22))
    assert f == {(2026, 7): pytest.approx(4 / 31), (2026, 8): 1.0, (2026, 9): pytest.approx(22 / 30)}


def test_realised_and_remaining_cover_the_year_after_baseline():
    # realised (to 22 Sep) + remaining (after 22 Sep) = everything after 27 Jul
    vols = quarter_volumes(8_000_000)
    realised = sum(monthly_volume(vols, m) * f
                   for (_, m), f in realised_month_fractions(date(2026, 7, 27), date(2026, 9, 22)).items())
    remaining = remaining_volume(vols, remaining_quarter_shares(date(2026, 9, 22), 2026))
    after_baseline = remaining_volume(vols, remaining_quarter_shares(date(2026, 7, 27), 2026))
    assert realised + remaining == pytest.approx(after_baseline, rel=2e-3)  # month vs quarter day-count rounding


# --- capacity-weighted Q3 / Q4 volumes (assumption A11) ----------------------------------------------------------

AFKLM_ASK = dict(ask_fy_prev=336_521, ask_q1_prev=78_565 / 1.040, ask_q2_prev=86_993 / 1.026, ask_q4_prev=83_962,
                 ask_h1_now=165_558)       # the printed Group capacity figures quoted in data/airlines.yaml


def test_h2_quarter_shares_hand_calculation():
    from src.model.periods import h2_quarter_shares
    shares = h2_quarter_shares(**AFKLM_ASK, fy_growth=0.025)
    q3_prev = 336_521 - 78_565 / 1.040 - 86_993 / 1.026 - 83_962            # 92,227
    h2_now = 336_521 * 1.025 - 165_558                                       # 179,376
    assert shares[3] == pytest.approx(h2_now * q3_prev / (q3_prev + 83_962) / (336_521 * 1.025))
    assert shares[3] == pytest.approx(0.2722, abs=1e-4) and shares[4] == pytest.approx(0.2478, abs=1e-4)
    assert shares[3] > shares[4]                                              # Q3 is the bigger quarter


def test_h2_quarter_shares_rejects_inconsistent_inputs():
    from src.model.periods import h2_quarter_shares
    with pytest.raises(ValueError):
        h2_quarter_shares(**{**AFKLM_ASK, "ask_h1_now": 400_000}, fy_growth=0.025)      # H1 above the full year
    with pytest.raises(ValueError):
        h2_quarter_shares(**{**AFKLM_ASK, "ask_q4_prev": 300_000}, fy_growth=0.025)     # last year's quarters overshoot


def test_afklm_quarter_volumes_in_the_twins_match_the_capacity_calculation():
    from src.model.periods import h2_quarter_shares
    from src.twins import load_twins
    fields = load_twins()["airlines"]["afklm"]["fields"]
    fy = fields["fuel_volume_fy26"]["value"]
    for growth, tolerance in ((0.025, 0.005), (0.02, 0.02), (0.03, 0.02)):   # stored = midpoint of the guided +2% to +3%
        shares = h2_quarter_shares(**AFKLM_ASK, fy_growth=growth)
        for q in (3, 4):
            assert fields[f"fuel_volume_q{q}_26"]["value"] == pytest.approx(fy * shares[q], abs=tolerance)
    assert fields["fuel_volume_q3_26"]["status"] == fields["fuel_volume_q4_26"]["status"] == "derived"


def test_model_uses_the_derived_quarters_for_afklm_only():
    from src.model.run import _segments
    from src.twins import load_twins
    twins = load_twins()
    market = {"mode": "scenario", "d_brent": 40.0, "d_crack": 60.0, "split_day": date(2026, 9, 30)}
    afklm = _segments(twins, "afklm", "FY2026", "central", market)
    assert sum(s["volume_t"] for s in afklm) == pytest.approx(2.15e6, rel=0.01)       # all of Q4, none of Q3 left
    lh = _segments(twins, "lufthansa", "FY2026", "central", market)
    assert sum(s["volume_t"] for s in lh) == pytest.approx(9.42e6 / 4, rel=0.01)      # unchanged: FY/4
