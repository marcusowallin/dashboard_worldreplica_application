"""Refresh analyst consensus (EPS, revenue, EBIT) from your dated MarketScreener snapshots.

1. Save the provider pages into sources/third-party/ as YYYY-MM-DD_marketscreener_<airline>_<part>.jpg/.png/.pdf
   (lufthansa / afklm / iag; include the page header so the price date is on it).
2. Dry run - shows old vs new, nothing is written:
       .venv/bin/python scripts/refresh_consensus.py
3. After you have checked the table:
       .venv/bin/python scripts/refresh_consensus.py --apply
   It asks once more, writes value / as_of / quote of the changed fields, re-validates the twins file and restores
   the original if anything fails. Then update 03_DATA_REGISTER.md (the script prints what changed).
Images are read with on-device OCR (macOS): pip install -r requirements-dev.txt. PDFs use their text layer.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.consensus_reader import check_round_trip, proposals, update_field_text  # noqa: E402
from src.twins import DEFAULT_PATH, TwinsError, load_twins  # noqa: E402

LARGE_CHANGE = 0.25   # flag moves above 25% for a second look (not an error: estimates can move a lot)


def table(rows):
    lines = [f"{'airline':10} {'field':23} {'old':>10} {'new':>10} {'change':>8}  as_of       note"]
    for r in rows:
        change = "" if r["new"] is None or not r["old"] else f"{r['new'] / r['old'] - 1:+.1%}"
        note = r["problem"] or ("unchanged" if r["new"] == r["old"] else "CHANGED")
        if r["new"] is not None and r["old"] and abs(r["new"] / r["old"] - 1) > LARGE_CHANGE:
            note += " - large move, check the page"
        old, new = (f"{v:g}" if v is not None else "-" for v in (r["old"], r["new"]))
        lines.append(f"{r['airline']:10} {r['field']:23} {old:>10} {new:>10} {change:>8}  "
                     f"{r['as_of']:10}  {note}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write the changed values after a confirmation")
    parser.add_argument("--folder", default=str(ROOT / "sources" / "third-party"))
    args = parser.parse_args()

    twins = load_twins()
    rows = proposals(args.folder, twins)
    print(table(rows))
    changes = [r for r in rows if r["new"] is not None and r["new"] != r["old"] and not r["problem"]]
    problems = [r for r in rows if r["problem"]]
    print(f"\n{len(changes)} change(s), {len(problems)} problem(s).")
    if not args.apply or not changes:
        print("Dry run - nothing written." if not args.apply else "Nothing to write.")
        return
    if input(f"Write {len(changes)} change(s) to {DEFAULT_PATH.name}? [y/N] ").strip().lower() != "y":
        print("Cancelled - nothing written.")
        return
    original = DEFAULT_PATH.read_text(encoding="utf-8")
    text = original
    for r in changes:
        quote = f"{r['row_text']} (OCR/text of {r['file']})"
        text = update_field_text(text, r["airline"], r["field"], r["new"], r["as_of"], quote)
    try:
        check_round_trip(text)
        DEFAULT_PATH.write_text(text, encoding="utf-8")
        load_twins()
    except (TwinsError, Exception) as err:          # any failure: put the original back
        DEFAULT_PATH.write_text(original, encoding="utf-8")
        sys.exit(f"Validation failed, original restored: {err}")
    print("Written and validated. Update 03_DATA_REGISTER.md for:")
    for r in changes:
        print(f"  {r['airline']} {r['field']}: {r['old']} -> {r['new']} (as of {r['as_of']}, {r['file']})")


if __name__ == "__main__":
    main()
