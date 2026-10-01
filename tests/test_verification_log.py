"""The evidence behind every 'verified' status (data/verification_log.csv) cannot drift from the twins file."""
import csv
import re
from pathlib import Path

from src.twins import load_twins

LOG = Path(__file__).resolve().parent.parent / "data" / "verification_log.csv"
TWINS = load_twins()


def _log():
    with open(LOG, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_every_verified_figure_has_a_matching_log_row_and_nothing_else_does():
    verified = {(a, f): x for a, v in TWINS["airlines"].items() for f, x in v["fields"].items()
                if x["status"] == "verified"}
    rows = {(r["airline"], r["field"]): r for r in _log()}
    assert set(rows) == set(verified) and len(rows) == len(_log())          # one row per figure, no orphans
    for key, row in rows.items():
        field = verified[key]
        assert float(row["value"]) == float(field["value"])                  # the value checked is the value used
        assert row["document"] == field["document"] and row["page"] == str(field["page"])
        assert row["result"] == "match" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["checked_on"])
        assert row["check"] and row["reasonability"]


def test_consensus_eps_is_verified_against_marketscreener_and_stays_level_4():
    for airline, v in TWINS["airlines"].items():
        for name in ("consensus_eps_fy26", "consensus_eps_fy27"):
            field = v["fields"][name]
            assert field["status"] == "verified" and field["level"] == 4         # checked, and still labelled third-party
            row = next(r for r in _log() if (r["airline"], r["field"]) == (airline, name))
            assert "MarketScreener" in row["check"]


def test_figures_that_cannot_be_checked_against_a_document_are_never_marked_verified():
    for v in TWINS["airlines"].values():
        for name, field in v["fields"].items():
            if field["status"] in ("derived", "assumption", "not-disclosed", "not-applicable"):
                assert field["status"] != "verified"
    ranges = [TWINS["airlines"]["lufthansa"]["fields"]["hedge_ratio_fy27_upper"]]   # the Reuters remark: a press report
    assert all(f["status"] == "third-party" for f in ranges)
