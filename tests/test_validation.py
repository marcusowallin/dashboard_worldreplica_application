"""Validation tests (02_SPEC.md trust layer). T4: independent EPS reconciliation."""
import pytest

from src.model.income import income_chain
from src.twins import get_value, load_twins


def test_t4_independent_eps_reconciliation_lufthansa():
    """T4: recompute dNI and dEPS by hand from the printed inputs and compare with the chain.

    Printed inputs (data/airlines.yaml, status still 'found' until verified):
      marginal tax 25% (AR 2025 p.282), minorities 24 / 1,363 (AR p.257),
      diluted shares 1,198,342,268 (AR p.284), recapture ~60% (Q2 charts slide 13).
    Test move: dFuel = EUR 100m (round number for the check, not a forecast).
    Independent formula, written out in one line:
      dEPS = -(100m - 0.60 * 100m) * (1 - 0.25) * (1 - 24/1,363) / 1,198,342,268
           = -40m * 0.75 * 0.982392 / 1,198,342,268 = -0.024594 EUR/share
    """
    twins = load_twins()
    tax = get_value(twins, "lufthansa", "tax_rate_marginal") / 100
    minority = get_value(twins, "lufthansa", "minority_share") / 100
    shares = get_value(twins, "lufthansa", "diluted_shares")
    recapture = get_value(twins, "lufthansa", "recapture_rate") / 100

    chain = income_chain(100_000_000, recapture, tax, minority, shares)

    by_hand_ni = -(100_000_000 - 0.60 * 100_000_000) * (1 - 0.25) * (1 - 0.0176)
    by_hand_eps = by_hand_ni / 1_198_342_268
    assert chain["d_net_income"] == pytest.approx(by_hand_ni, rel=1e-3)
    assert chain["d_eps"] == pytest.approx(by_hand_eps, rel=1e-3)
    assert chain["d_eps"] == pytest.approx(-0.024594, rel=1e-3)


def test_t4_share_counts_reproduce_printed_eps():
    """Share counts in the twins reproduce each company's printed FY25 EPS (net income / shares).

    LH: 1,339m / 1,198,342,268 = 1.117 (printed 1.12, AR p.257/284)
    AF-KLM: 1,544m / 280,566,634 = 5.503 (printed diluted 5.50, URD p.408)
    IAG: 3,500m / 5,031,980 thousand = 0.6956 EUR = 69.56 cents (printed diluted 69.5, AR p.187)
    """
    twins = load_twins()
    assert 1_339e6 / get_value(twins, "lufthansa", "diluted_shares") == pytest.approx(1.12, abs=0.005)
    assert 1_544e6 / get_value(twins, "afklm", "diluted_shares") == pytest.approx(5.50, abs=0.005)
    iag_shares = get_value(twins, "iag", "diluted_shares") * 1_000  # printed in thousands
    assert 3_500e6 / iag_shares * 100 == pytest.approx(69.5, abs=0.1)


# --- T2: reproduce Lufthansa's slide 17 sensitivity table -----------------------------------
from src.model.fuel import usd_per_bbl_to_usd_per_t
from src.validation import (
    BRENT_ROWS, CRACK_COLS, PRINTED, error_grid, implied_unprotected, lufthansa_validation,
    predict_grid, printed_slopes, remaining_share, table_implied_exposures,
)


def test_printed_table_centre_matches_printed_fy_price():
    # Centre cell (Brent 84, crack 64) = FY26 jet price after hedge 1,036 (slide 17)
    assert PRINTED[84][CRACK_COLS.index(64)] == 1036
    assert len(PRINTED) == len(BRENT_ROWS) and all(len(r) == len(CRACK_COLS) for r in PRINTED.values())


def test_bbl_conversion():
    assert usd_per_bbl_to_usd_per_t(10) == pytest.approx(79)


def test_remaining_share_by_hand():
    # as of 27 Jul: Q3 2.68m * 65/92 = 1.8935m + Q4 9.42m/4 = 2.355m -> 4.2485m / 9.42m = 0.4510
    assert remaining_share(9_420_000, 2_680_000) == pytest.approx(0.4510, abs=1e-4)


def test_prediction_is_anchored_at_centre_and_linear():
    grid = predict_grid(0.2, 0.6, 0.5)
    assert grid[84][CRACK_COLS.index(64)] == 1036
    # +10 USD/bbl Brent -> +0.5 * 79 * 0.2 = +7.9 USD/t
    assert grid[94][CRACK_COLS.index(64)] - 1036 == pytest.approx(7.9)


def test_perfect_model_has_zero_error():
    assert all(e == 0 for row in error_grid(PRINTED).values() for e in row)


def test_printed_slopes_and_implied_exposure():
    slopes = printed_slopes()
    assert slopes["crack"]["54->64"] == 22 and slopes["brent"]["84->94"] == 23
    assert implied_unprotected(23, 0.451) == pytest.approx(23 / (0.451 * 79))


def test_lufthansa_validation_runs_on_twins():
    v = lufthansa_validation(load_twins())
    assert v["u_brent"] == pytest.approx(0.18)
    assert v["summary"]["max_abs"] > 0          # the gap is reported, not tuned away


def test_table_implied_exposures_by_hand():
    # share 0.451: Brent 84->94 = 23 -> 23 / (0.451*79) = 0.6455; crack 64->74 = 26 -> 0.7297
    u = table_implied_exposures(0.451)
    assert u["u_brent"] == pytest.approx(0.6455, abs=1e-3)
    assert u["u_crack"] == pytest.approx(0.7297, abs=1e-3)


# --- T9 and T10 --------------------------------------------------------------------------------
from src.validation import confidence_label, fuel_bill_reconciliation


def test_t9_lufthansa_fuel_bill_by_hand():
    # 9.42m t x USD 1,036/t = USD 9,759.1m / 1.151 = EUR 8,478.8m vs fossil EUR 8,460m -> +0.22%
    r = fuel_bill_reconciliation(load_twins(), "lufthansa")
    assert r["computed"] == pytest.approx(8_478.8e6, rel=1e-4)
    assert r["gap_share"] == pytest.approx(0.0022, abs=1e-4)


def test_t9_not_possible_is_explained():
    twins = load_twins()
    assert "zero by construction" in fuel_bill_reconciliation(twins, "afklm")["note"]
    assert "computed" not in fuel_bill_reconciliation(twins, "afklm")
    assert "computed" not in fuel_bill_reconciliation(twins, "iag")


def test_t10_confidence_low_until_verified():
    label, share, missing = confidence_label(load_twins(), "lufthansa")
    assert label == "LOW" and share == 0 and "recapture_rate" in missing


def test_t10_thresholds():
    twins = load_twins()
    fields = twins["airlines"]["iag"]["fields"]
    for name in fields:
        if fields[name]["status"] == "found":
            fields[name]["status"] = "verified"
    label, share, _ = confidence_label(twins, "iag")
    assert label in {"LOW", "MEDIUM", "HIGH"} and 0 < share <= 1
