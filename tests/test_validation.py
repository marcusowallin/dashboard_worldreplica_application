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
    assert v["u_brent"] == pytest.approx(0.19)               # 1 - 81% year-to-go hedge ratio (slide 17, FY column)
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


def test_t10_graded_score_by_hand():
    """Credit per input: verified L1 1.00; verified L4 or derived 0.75; third-party or assumption 0.50; found or
    not disclosed 0.25; average of the 12 inputs behind FY2027 (not-applicable left out)."""
    twins = load_twins()
    # Lufthansa: volume 1, hedge 1, upper (third-party) .5, gasoil 1, brent 1, jet (derived) .75, recapture 1, tax 1,
    #            minorities (derived: 24 / 1,363) .75, forward shares (derived) .75, consensus EPS (verified L4) .75, consensus EBIT (third-party) .5
    label, score, weaker = confidence_label(twins, "lufthansa")
    assert score == pytest.approx((1 + 1 + .5 + 1 + 1 + .75 + 1 + 1 + .75 + .75 + .75 + .5) / 12) and label == "HIGH"
    assert set(weaker) == {"hedge_ratio_fy27_upper", "hedge_mix_jet", "diluted_shares_forward", "consensus_eps_fy27",
                           "consensus_ebit_fy27", "minority_share"}
    # Air France-KLM: volume derived .75, hedge 1, mix not disclosed 3 x .25, recapture 1, tax 1, minorities derived .75,
    #                 forward shares verified 1, EPS .75, EBIT .5  (hedge_ratio_fy27_upper does not apply)
    label, score, _ = confidence_label(twins, "afklm")
    assert score == pytest.approx((.75 + 1 + .75 + 1 + 1 + .75 + 1 + .75 + .5) / 11) and label == "MEDIUM"
    assert confidence_label(twins, "iag")[0] == "MEDIUM"


def test_t10_high_needs_every_input_checked_and_nothing_checked_means_low():
    twins = load_twins()
    fields = twins["airlines"]["lufthansa"]["fields"]
    fields["recapture_rate"]["status"] = "found"                    # one unchecked input blocks HIGH ...
    label, score, _ = confidence_label(twins, "lufthansa")
    assert score > 0.8 - 0.1 and label == "MEDIUM"                    # ... even though the score is still high
    for v in twins["airlines"].values():                            # nothing sourced at all -> LOW
        for field in v["fields"].values():
            if field["status"] not in ("not-applicable",):
                field["status"] = "not-disclosed"
    assert confidence_label(twins, "lufthansa")[:2] == ("LOW", pytest.approx(0.25))


def test_t10_breakdown_matches_the_label_and_hides_fields_that_do_not_apply():
    from src.validation import confidence_breakdown
    twins = load_twins()
    rows = confidence_breakdown(twins, "afklm")
    assert "hedge_ratio_fy27_upper" not in [r["field"] for r in rows]       # not-applicable for the peers
    assert sum(r["credit"] for r in rows) / len(rows) == pytest.approx(confidence_label(twins, "afklm")[1])
    assert all(0 < r["credit"] <= 1 and r["why"] for r in rows)


def test_t10_thresholds():
    twins = load_twins()
    fields = twins["airlines"]["iag"]["fields"]
    for name in fields:
        if fields[name]["status"] == "found":
            fields[name]["status"] = "verified"
    label, share, _ = confidence_label(twins, "iag")
    assert label in {"LOW", "MEDIUM", "HIGH"} and 0 < share <= 1
