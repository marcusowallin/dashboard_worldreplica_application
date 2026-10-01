"""Tests for the consensus refresh reader (src/consensus_reader.py). OCR itself is tested only on macOS."""
from pathlib import Path

import pytest
import yaml

from src.consensus_reader import (
    Token, latest_snapshots, normalise_label, parse_number, price_stamp_date, proposals, read_table,
    update_field_text,
)
from src.twins import DEFAULT_PATH, load_twins, validate_twins

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOTS = ROOT / "sources" / "third-party"


def row(label, y, values, x0=0.30, step=0.125, h=0.024):
    """Tokens for one table row: the label at the left, values in columns from x0."""
    out = [Token(label, 0.02, y, 0.1, h)]
    out += [Token(v, x0 + i * step, y + 0.002, 0.06, h) for i, v in enumerate(values) if v is not None]
    return out


HEADER = [Token(str(year), 0.30 + i * 0.125, 0.35, 0.058, 0.02) for i, year in enumerate(range(2023, 2029))]


def test_labels_are_normalised_strictly():
    assert normalise_label("EBІT1") == "ebit"              # Cyrillic I + footnote
    assert normalise_label("EBITDA!") == "ebitda"
    assert normalise_label("Net sales !") == "netsales"
    assert normalise_label("EPS 1") == "eps"
    assert normalise_label("EPS Estimates") is None
    assert normalise_label("Earnings before Tax") is None


def test_numbers():
    assert parse_number("1,809") == 1809 and parse_number("0.6097") == 0.6097
    assert parse_number("-234.9") == -234.9 and parse_number("•2.97") == 2.97
    assert parse_number(").9218") is None and parse_number("3/6/26") is None and parse_number("8.15%") is None


def test_read_table_maps_by_column_and_ignores_ebitda():
    tokens = HEADER + row("EBITDA 1", 0.47, ["4,910", "3,982", "4,329", "4,310", "4,934", "5,471"]) \
        + row("EBIT 1", 0.55, ["2,682", "1,645", "1,960", "1,809", "2,281", "2,708"]) \
        + row("EPS 1", 0.62, [None, None, "1.12", "0.9221", "1.299", "1.589"])
    found = read_table(tokens)
    assert found[("ebit", 2026)][0] == 1809 and found[("ebit", 2027)][0] == 2281
    assert found[("eps", 2027)][0] == 1.299 and ("eps", 2024) not in found
    assert not any(key == "ebitda" for key, _ in found)


def test_cut_off_column_is_ignored_not_shifted():
    tokens = HEADER + row("EPS 1", 0.62, ["1.12", "0.9221", "1.299"], x0=0.30 + 3 * 0.125)
    tokens.append(Token(".15", 0.5065, 0.622, 0.02, 0.024))    # half-visible cell midway between two columns
    found = read_table(tokens)
    assert found[("eps", 2026)][0] == 1.12 and found[("eps", 2027)][0] == 0.9221
    assert ("eps", 2025) not in found and ("eps", 2024) not in found


def test_price_stamp_date():
    assert price_stamp_date([Token("Market Closed - Xetra 11:36:15 2026-09-29 am EDT", 0, 0.1, 0.5, 0.02)]) == \
        "2026-09-29"


def test_update_field_text_changes_only_that_field():
    text = DEFAULT_PATH.read_text(encoding="utf-8")
    new = update_field_text(text, "iag", "consensus_ebit_fy27", 5100, "2026-10-15", "EBIT 1 ... 5,100 (test)")
    data = yaml.safe_load(new)
    field = data["airlines"]["iag"]["fields"]["consensus_ebit_fy27"]
    assert (field["value"], field["as_of"], field["quote"]) == (5100, "2026-10-15", "EBIT 1 ... 5,100 (test)")
    assert data["airlines"]["iag"]["fields"]["consensus_ebit_fy26"]["value"] == 4481
    assert data["airlines"]["lufthansa"]["fields"]["consensus_ebit_fy27"]["value"] == 2281
    assert validate_twins(data) == []
    assert len(new.splitlines()) == len(text.splitlines())


def test_proposals_report_changes_and_missing_rows(tmp_path):
    for name in ("2026-10-15_marketscreener_iag_2-eps.png", "2026-09-30_marketscreener_iag_2-eps.png"):
        (tmp_path / name).write_bytes(b"")

    def reader(path):
        assert "2026-10-15" in path.name                      # only the newest snapshot is read
        return HEADER + row("EPS 1", 0.62, [None, None, "0.695", "0.65", "0.80", "0.93"])
    rows = {r["field"]: r for r in proposals(tmp_path, load_twins(), reader)}
    assert rows["consensus_eps_fy26"]["new"] == 0.65 and rows["consensus_eps_fy26"]["old"] == 0.6097
    assert rows["consensus_ebit_fy27"]["new"] is None and "not found" in rows["consensus_ebit_fy27"]["problem"]
    assert list(latest_snapshots(tmp_path)) == ["iag"]


def _vision_available():
    try:
        import Vision  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _vision_available(), reason="macOS Vision OCR not installed (requirements-dev.txt)")
@pytest.mark.skipif(not any(SNAPSHOTS.glob("*.jpg")), reason="saved snapshot images are not part of the published repo")
def test_ocr_of_saved_snapshots_reproduces_the_twins():
    """The existing 30 Sep 2026 screenshots must read back exactly the values stored in the twins."""
    rows = proposals(SNAPSHOTS, load_twins())
    assert len(rows) == 18
    assert all(r["new"] == r["old"] and r["problem"] is None for r in rows), \
        [(r["airline"], r["field"], r["old"], r["new"], r["problem"]) for r in rows if r["new"] != r["old"]]
    assert {r["as_of"] for r in rows} == {"2026-09-29"}
