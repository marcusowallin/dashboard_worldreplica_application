"""Evaluate the news tagger against your hand labels (trust item T6).

1. Fill the label_* columns in data/labelled_headlines.csv (see src/news_tagger.parse_label).
2. Put ANTHROPIC_API_KEY in .streamlit/secrets.toml (or the environment). The key is read, never printed.
3. Run:  .venv/bin/python scripts/evaluate_tagger.py
Prints agreement per field and saves the tags next to the CSV (data/labelled_headlines_tags.json).
Cost: one API call per 20 headlines (claude-haiku-4-5), a few cents at most.
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.news_tagger import (  # noqa: E402
    AIRLINES, DIRECTIONS, DRIVERS, IMPACTS, MAX_PER_REFRESH, agreement, classify, make_client, parse_label,
    validate_tag,
)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def secret_lookup(name):
    """Read one value from .streamlit/secrets.toml (git-ignored). Never printed."""
    import tomllib
    path = ROOT / ".streamlit" / "secrets.toml"
    if not path.exists():
        return None
    with open(path, "rb") as fh:
        return tomllib.load(fh).get(name)


def label_problems(labels):
    """Label values outside the allowed categories (e.g. an old driver name) - fix these before trusting the report."""
    problems = []
    for i, lab in enumerate(labels, start=1):
        if lab["driver"] and lab["driver"] not in DRIVERS:
            problems.append(f"row {i}: driver '{lab['driver']}' not in {', '.join(DRIVERS)}")
        if lab["direction"] and lab["direction"] not in DIRECTIONS:
            problems.append(f"row {i}: direction '{lab['direction']}' not in {', '.join(DIRECTIONS)}")
        for a in lab["airlines"] or ():
            if a not in AIRLINES:
                problems.append(f"row {i}: airline '{a}' not in {', '.join(AIRLINES)}")
        for a, impact in (lab.get("impacts") or {}).items():
            if a not in AIRLINES or impact not in IMPACTS:
                problems.append(f"row {i}: impact '{a}:{impact}' - use airline:positive/negative/neutral")
            elif lab["airlines"] is not None and a not in lab["airlines"]:
                problems.append(f"row {i}: impact for '{a}', which is not in label_airlines")
    return problems


def main():
    rows = list(csv.DictReader(open(DATA / "labelled_headlines.csv", encoding="utf-8")))
    labels = [parse_label(r) for r in rows]
    if not any(v is not None for lab in labels for v in lab.values()):
        print("No labels filled in yet: fill the label_* columns first.")
        return 1
    problems = label_problems(labels)
    if problems:
        print("Fix these labels first:\n  " + "\n  ".join(problems))
        return 1
    client = make_client(secret_lookup)
    if client is None:
        print("No API key found: add ANTHROPIC_API_KEY to .streamlit/secrets.toml (or the environment).")
        return 1
    headlines = [{"title": r["title"]} for r in rows]
    tags = []
    for start in range(0, len(headlines), MAX_PER_REFRESH):
        batch = headlines[start:start + MAX_PER_REFRESH]
        raw, error = classify(batch, client)
        if error:
            print(f"Tagging failed: {error}")
            return 1
        by_id = {t.get("id"): t for t in raw}
        tags += [validate_tag(by_id.get(i), h)[0] if i in by_id else None for i, h in enumerate(batch)]
    (DATA / "labelled_headlines_tags.json").write_text(json.dumps(tags, indent=2), encoding="utf-8")
    print("Agreement with your labels (agree / labelled):")
    for name, (agree, total) in agreement(labels, tags).items():
        share = f"{agree / total:.0%}" if total else "n/a"
        print(f"  {name:10s} {agree:3d} / {total:3d}  {share}")
    print("Driver agreement by your label (agree / labelled):")
    for driver in DRIVERS:
        pairs = [(lab, t) for lab, t in zip(labels, tags) if lab["driver"] == driver]
        if pairs:
            agree = sum(1 for lab, t in pairs if t and t["driver"] == driver)
            print(f"  {driver:13s} {agree:3d} / {len(pairs):3d}")
    evidence_ok = sum(1 for t in tags if t and t["evidence_ok"])
    print(f"Evidence found verbatim: {evidence_ok} / {sum(1 for t in tags if t)} tags")
    return 0


if __name__ == "__main__":
    sys.exit(main())
