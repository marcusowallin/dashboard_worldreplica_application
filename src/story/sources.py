"""Source markers: every small superscript on the story page points to an entry on the Method & sources page.

One registry serves both pages, so a marker can never point to an entry that does not exist:
  - "A26" etc. -> the assumption with that ID in ASSUMPTIONS.md (parsed here, rendered with an anchor on the
    method page; an unknown ID raises KeyError, so a typo fails in the tests)
  - "L1".."L5" -> the data-source level sections;  "FRED", "ECB" -> the market-data feeds
  - "T2", "T9", "ROBUST" -> validation items;  "YARD" -> the yardstick;  "NEWS" -> the news sources
"""
import re
from functools import lru_cache
from pathlib import Path

from src.ui.components import source_marker

ROOT = Path(__file__).resolve().parents[2]
ASSUMPTIONS_FILE = ROOT / "ASSUMPTIONS.md"
METHOD_PAGE = "method"           # url path of the Method & sources page (see app.py)

STATIC = {                       # ref -> (anchor on the method page, tooltip)
    "L1": ("data-l1", "Company's own documents (source level 1)"),
    "L2": ("data-l2", "Company-compiled consensus (source level 2)"),
    "L3": ("data-l3", "Other official sources (source level 3)"),
    "L4": ("data-l4", "Reputable third parties (source level 4)"),
    "L5": ("data-l5", "Labelled assumptions (source level 5)"),
    "FRED": ("feed-fred", "Market data: FRED jet fuel and Brent"),
    "ECB": ("feed-ecb", "Market data: ECB USD/EUR rate"),
    "YARD": ("method-yardstick", "Expected operating profit: the yardstick hierarchy"),
    "T2": ("validation-t2", "Validation: Lufthansa's own sensitivity table"),
    "T9": ("validation-t9", "Validation: fuel bill reconciliation"),
    "ROBUST": ("validation-robustness", "Validation: robustness of the ranking"),
    "NEWS": ("news-sources", "News sources, keyword rule and source decisions"),
}


@lru_cache(maxsize=1)
def assumptions(path=ASSUMPTIONS_FILE):
    """Every assumption in ASSUMPTIONS.md, in ID order.

    Output: list of {"id", "number", "group", "what", "why", "level", "where", "sensitivity"}. A table row that does
    not have exactly six cells raises ValueError (so a malformed row cannot silently disappear from the page).
    """
    group, rows = "", []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            group = line[3:].strip()
        match = re.match(r"\| (A\d+) \|", line)
        if not match:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
        if len(cells) != 6:
            raise ValueError(f"{match.group(1)}: expected 6 cells, found {len(cells)}")
        rows.append({"id": cells[0], "number": int(cells[0][1:]), "group": group, "what": cells[1], "why": cells[2],
                     "level": cells[3], "where": cells[4], "sensitivity": cells[5]})
    return sorted(rows, key=lambda r: r["number"])


def assumption_groups(path=ASSUMPTIONS_FILE):
    """The assumptions split by section, each section once, in the order it first appears.

    Output: list of (group name, rows in ID order). Needed because the IDs are not contiguous within a section (A26 and
    A27 sit under 'Baseline and consensus' but come after A23-A25 under 'Method choices'), so walking the ID-sorted list
    and printing a heading at every change would print the same heading, and the same anchor, twice.
    """
    groups = {}
    for row in assumptions(path):
        groups.setdefault(row["group"], []).append(row)
    return list(groups.items())


def assumption(ref):
    for row in assumptions():
        if row["id"] == ref:
            return row
    raise KeyError(f"unknown assumption {ref}")


def anchor(ref):
    """Anchor id on the method page for a marker reference. Raises KeyError for an unknown reference."""
    if ref in STATIC:
        return STATIC[ref][0]
    return assumption(ref)["id"].lower()


def tooltip(ref):
    if ref in STATIC:
        return STATIC[ref][1]
    first = re.split(r"[:;(.]", assumption(ref)["what"], maxsplit=1)[0].strip()
    return f"Assumption {ref}: {first[:70]}"


def markers(*refs):
    """HTML for a run of small superscript markers, each linking (new tab) to its entry on the method page."""
    return "".join(source_marker(ref, f"{METHOD_PAGE}#{anchor(ref)}", tooltip(ref)) for ref in refs)


def all_refs():
    """Every reference a marker may use (for tests and the method page)."""
    return list(STATIC) + [row["id"] for row in assumptions()]
