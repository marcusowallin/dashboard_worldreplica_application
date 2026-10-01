"""Tests for src/twins.py: loading and validating the company twins."""
import copy

import pytest
import yaml

from src.twins import (
    ALLOWED_UNITS, MODEL_UNIT_FACTORS, TwinsError, check_field, get_field, get_model_value,
    get_value, load_twins, validate_twins,
)


def good_field(value=10, status="found", unit="%"):
    """A minimal valid field record for small hand-made test files."""
    return {
        "value": value, "unit": unit, "currency": None, "period": "FY2026", "as_of": "2026-07-27",
        "document": "doc1", "page": "p.1", "quote": "10%", "url": "https://example.com",
        "level": 1, "status": status, "note": None,
    }


def small_twins():
    """Two airlines, one field each, one document - valid."""
    return {
        "documents": {"doc1": {"title": "Test doc", "date": "2026-07-27", "url": "https://example.com"}},
        "airlines": {
            "a": {"fields": {"hedge_ratio_fy26": good_field()}},
            "b": {"fields": {"hedge_ratio_fy26": good_field(20)}},
        },
    }


def write_yaml(tmp_path, data):
    path = tmp_path / "airlines.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


# --- the real file ---------------------------------------------------------------

def test_real_file_loads_and_fields_are_identical():
    twins = load_twins()
    field_sets = [set(a["fields"]) for a in twins["airlines"].values()]
    assert len(field_sets) == 3
    assert field_sets[0] == field_sets[1] == field_sets[2]


def test_real_file_values_as_printed():
    twins = load_twins()
    assert get_value(twins, "lufthansa", "hedge_ratio_rest_fy26") == 81
    assert get_field(twins, "lufthansa", "hedge_ratio_rest_fy26")["unit"] == "%"
    assert get_value(twins, "iag", "eps_fy25") == 69.5  # EUR cents, as printed


def test_missing_values_load_as_none():
    twins = load_twins()
    assert get_value(twins, "afklm", "planning_fx_usd_per_eur") is None   # not-disclosed
    assert get_value(twins, "afklm", "hedge_ratio_fy27_upper") is None    # not-applicable


# --- hand-made files ---------------------------------------------------------------

def test_small_valid_file_has_no_problems(tmp_path):
    assert validate_twins(small_twins()) == []
    assert load_twins(write_yaml(tmp_path, small_twins()))["airlines"]["b"]["fields"]


def test_unknown_status_raises(tmp_path):
    data = small_twins()
    data["airlines"]["a"]["fields"]["hedge_ratio_fy26"]["status"] = "guessed"
    with pytest.raises(TwinsError, match="unknown status 'guessed'"):
        load_twins(write_yaml(tmp_path, data))


def test_different_fields_raise(tmp_path):
    data = small_twins()
    data["airlines"]["b"]["fields"]["extra_field"] = good_field()
    with pytest.raises(TwinsError, match="fields differ"):
        load_twins(write_yaml(tmp_path, data))


def test_unknown_unit_is_reported():
    problems = check_field("a.x", good_field(unit="percent"), {"doc1"})
    assert any("unknown unit 'percent'" in p for p in problems)


def test_value_with_not_disclosed_status_is_reported():
    problems = check_field("a.x", good_field(value=5, status="not-disclosed"), {"doc1"})
    assert any("must have value null" in p for p in problems)


def test_found_status_without_value_is_reported():
    problems = check_field("a.x", good_field(value=None, status="found"), {"doc1"})
    assert any("needs a numeric value" in p for p in problems)


def test_unknown_document_is_reported():
    field = copy.deepcopy(good_field())
    field["document"] = "doc_nowhere"
    problems = check_field("a.x", field, {"doc1"})
    assert any("not in the documents list" in p for p in problems)


def test_missing_file_raises_clear_error(tmp_path):
    with pytest.raises(TwinsError, match="not found"):
        load_twins(tmp_path / "nope.yaml")


def test_get_field_unknown_name_raises():
    with pytest.raises(TwinsError, match="No field"):
        get_field(load_twins(), "lufthansa", "does_not_exist")


# --- conversion to model units ---------------------------------------------------------------

def test_every_allowed_unit_has_a_conversion():
    assert set(MODEL_UNIT_FACTORS) == ALLOWED_UNITS


def test_model_values_are_converted():
    twins = load_twins()
    assert get_model_value(twins, "lufthansa", "hedge_ratio_rest_fy26") == pytest.approx(0.81)
    assert get_model_value(twins, "lufthansa", "fuel_volume_fy26") == pytest.approx(9_420_000)
    assert get_model_value(twins, "iag", "diluted_shares") == 5_031_980_000
    assert get_model_value(twins, "iag", "eps_fy25") == pytest.approx(0.695)
    assert get_model_value(twins, "iag", "consensus_eps_fy26") == pytest.approx(0.6097)  # already EUR
    assert get_model_value(twins, "lufthansa", "adj_operating_profit_fy25") == pytest.approx(1.96e9)
    assert get_model_value(twins, "afklm", "fuel_bill_fy26") == pytest.approx(8.9e9)       # USD


def test_model_value_missing_is_none():
    assert get_model_value(load_twins(), "afklm", "guidance_low") is None
