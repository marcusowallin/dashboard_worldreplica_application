"""Model run on the real twins: hand-checked numbers, range cases, live/scenario modes, robustness rules."""
from datetime import date
from pathlib import Path

import pytest

from src.model.run import ranking_is_robust, robust_extremes, run_all
from src.twins import load_twins
from src.data_sources import load_live_prices as REAL_LOADER
from tests.test_data_sources import fake_get

AS_OF = date(2026, 9, 30)


@pytest.fixture(scope="module")
def output():
    return run_all(load_twins(), as_of=AS_OF)


def test_lufthansa_fy26_remaining_by_hand(output):
    # Q4 volume 9.42m/4 = 2.355m t; year-to-go hedge 81% = 48% gasoil + 33% Brent as printed (slide 17 fn 2);
    # uB = 1 - 0.81 = 0.19, uC = 1 - 0.8*0.48 = 0.616; per t: 0.19*40 + 0.616*60 = 44.56 -> USD 104.94m -> EUR 91.17m at 1.151
    # dEBIT -36.47m (40% not recaptured); dNI x0.75 x(1-24/1363) = -26.87m; dEPS / 1,198,342,268 = -0.02242
    r = output["results"]["FY2026"]["lufthansa"]["base"]
    assert r["volume_t"] == pytest.approx(2_355_000)
    assert r["d_fuel_eur"] == pytest.approx(91.17e6, rel=1e-3)
    assert r["d_eps"] == pytest.approx(-0.02242, rel=1e-3)
    assert r["d_eps_share"] == pytest.approx(-0.02242 / 0.9221, rel=1e-3)


def test_all_impacts_unfavourable_for_a_price_rise(output):
    for period in output["results"].values():
        for cases in period.values():
            assert all(r["d_eps"] < 0 for r in cases.values())


def test_peer_ranges_bracket_the_central_case(output):
    for period in output["results"].values():
        for airline in ("afklm", "iag"):
            c = period[airline]
            assert c["crude-only"]["d_eps"] <= c["central"]["d_eps"] <= c["jet-equivalent"]["d_eps"]


def test_robust_extremes_and_ranking(output):
    most, least = robust_extremes(output["results"]["FY2027"])
    assert most == "lufthansa"
    assert least is None                       # AF-KLM vs IAG depends on undisclosed mixes
    assert ranking_is_robust(output["results"]["FY2027"]) is None


def fake_live(baseline_day):
    """Live prices from the mocked feeds in test_data_sources (no network in tests)."""
    return REAL_LOADER(baseline_day, fake_get)


def test_lufthansa_company_table_case_is_harsher(output):
    # A24: exposures implied by LH's own table (Brent 84->94, crack 64->74) exceed the swap model's
    cases = output["results"]["FY2026"]["lufthansa"]
    assert cases["company table"]["d_eps"] < cases["base"]["d_eps"]
    assert cases["company table"]["effective_protection"] < cases["base"]["effective_protection"]


def test_lufthansa_still_hardest_hit_fy26_with_company_case(output):
    assert robust_extremes(output["results"]["FY2026"])[0] == "lufthansa"


def test_live_mode_splits_realised_and_remaining():
    # Mocked prices to 22 Sep: realised = 28 Jul-22 Sep by month (monthly average moves),
    # remaining = 23-30 Sep + Q4 at the latest move. LH volumes: Q3 printed 2.68m t, Q4 2.355m t.
    live = fake_live(date(2026, 7, 27))
    out = run_all(load_twins(), live=live)
    assert out["market"]["mode"] == "live"
    r = out["results"]["FY2026"]["lufthansa"]["base"]
    # realised: Jul 4/31, Aug, Sep 22/30 of 2.68m/3 -> 0.1153 + 0.8933 + 0.6551 = 1.6637m t
    # remaining: Q3 8/92 * 2.68m = 0.2330m + Q4 2.355m = 2.5880m -> total 4.2517m t
    assert r["segments"] == 5
    assert r["volume_t"] == pytest.approx(4_251_700, rel=1e-3)
    assert "Live prices" in out["market"]["label"]
    assert out["period_labels"]["FY2026"].startswith("FY2026 since 27 Jul")


def test_failed_feeds_fall_back_to_scenario():
    from src.data_sources import load_live_prices
    from tests.test_data_sources import failing_get
    out = run_all(load_twins(), live=load_live_prices(date(2026, 7, 27), failing_get), as_of=AS_OF)
    assert out["market"]["mode"] == "scenario"


def test_no_ranking_when_a_percentage_is_not_meaningful(output):
    import copy
    broken = copy.deepcopy(output["results"]["FY2027"])
    broken["iag"]["central"]["d_eps_share"] = None
    assert robust_extremes(broken) == (None, None) and ranking_is_robust(broken) is None
