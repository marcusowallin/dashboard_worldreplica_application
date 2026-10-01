"""Method & sources page, source markers, retired v1 page, public-content check. Network and AI are mocked."""
import json
import re
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import src.data_sources
from src.data_sources import load_live_prices as REAL_LOADER
from src.story import method_content as mc
from src.story import sources
from src.twins import load_twins
from src.ui import method_parts as mp
from tests.test_data_sources import fake_get

ROOT = Path(__file__).resolve().parent.parent
APP = str(ROOT / "app.py")
TWINS = load_twins()

# Words that belong to the private planning files, never to the public page or public docs. The context-specific
# terms live in tests/private_forbidden.txt (git-ignored, one regex per line) so a published copy of this repo does not
# carry them; when that file is absent only the generic list below is checked.
FORBIDDEN = [r"\bprompt \d", r"02_spec", r"claude\.md", r"status\.md", r"04_prompts", r"start_here", r"review_backlog",
             r"design_brief", r"\byour (rule|decision)\b", r"\byou verified\b", r"downloaded by you"]
_PRIVATE = Path(__file__).resolve().parent / "private_forbidden.txt"
if _PRIVATE.exists():
    FORBIDDEN += [ln.strip() for ln in _PRIVATE.read_text(encoding="utf-8").splitlines() if ln.strip()]
# ids that Streamlit's HTML sanitiser strips because they collide with built-in DOM names (seen with 'method')
CLOBBERING = {"method", "name", "action", "target", "submit", "elements", "length", "form", "id", "title", "value"}


@pytest.fixture()
def fresh(monkeypatch):
    st.cache_data.clear()
    st.cache_resource.clear()
    monkeypatch.setattr(src.data_sources, "load_live_prices", lambda day, **kw: REAL_LOADER(day, fake_get, **kw))
    yield
    st.cache_data.clear()
    st.cache_resource.clear()


def _html(at):
    return " ".join(h.proto.body for h in at.get("html"))


def _all_text(at):
    parts = [_html(at)] + [m.value for m in at.markdown] + [t.value for t in at.title]
    parts += [f"{m.label} {m.value}" for m in at.metric] + [e.label for e in at.expander]
    return "\n".join(parts)


# --- assumptions registry and markers -----------------------------------------------------------------

def test_every_assumption_row_is_parsed():
    text = (ROOT / "ASSUMPTIONS.md").read_text(encoding="utf-8")
    in_file = re.findall(r"^\| (A\d+) \|", text, flags=re.M)
    parsed = [r["id"] for r in sources.assumptions()]
    assert sorted(parsed, key=lambda x: int(x[1:])) == parsed and sorted(in_file) == sorted(parsed)
    assert len(set(parsed)) == len(parsed) >= 30
    for r in sources.assumptions():
        assert all(r[k] for k in ("what", "why", "level", "where", "sensitivity", "group"))


def test_each_assumption_section_appears_once_with_all_its_rows():
    """A26/A27 belong to 'Baseline and consensus' but follow A23-A25 ('Method choices'): the page must not repeat a
    heading (and its anchor) because the IDs interleave."""
    groups = sources.assumption_groups()
    names = [g for g, _ in groups]
    assert len(names) == len(set(names))
    assert sorted(r["id"] for _, rows in groups for r in rows) == sorted(r["id"] for r in sources.assumptions())
    by_name = dict(groups)
    assert {"A26", "A27"} <= {r["id"] for r in by_name["Baseline and consensus"]}
    for _, rows in groups:
        assert [r["number"] for r in rows] == sorted(r["number"] for r in rows)


def test_markers_link_to_new_tab_anchor_and_unknown_refs_fail_loudly():
    html = sources.markers("A26", "L1", "FRED")
    assert 'href="method#a26"' in html and 'href="method#data-l1"' in html and 'href="method#feed-fred"' in html
    assert html.count('target="_blank"') == 3 and 'rel="noopener"' in html
    with pytest.raises(KeyError):
        sources.markers("A99")
    with pytest.raises(KeyError):
        sources.anchor("nonsense")
    assert not CLOBBERING & {sources.anchor(r) for r in sources.all_refs()}


def test_marker_component_escapes_everything():
    html = mp._e('<img src=x onerror=1>')
    assert "<img" not in html


# --- content module -------------------------------------------------------------------------------------------

def test_every_twin_field_has_a_label_and_a_source_row():
    for airline in TWINS["airlines"].values():
        assert set(airline["fields"]) <= set(mc.FIELD_LABELS)
    rows = mc.source_rows(TWINS)
    assert sum(len(items) for by in rows.values() for items in by.values()) == 35 * 3
    assert sum(sum(c.values()) for c in mc.status_table(TWINS).values()) == 35 * 3


def test_source_links_are_external_and_every_document_has_one():
    for key, doc in TWINS["documents"].items():
        assert str(doc["url"]).startswith("https://"), key                 # never a local path
    assert TWINS["documents"]["af_urd_2025"]["url_note"]                    # the page link is labelled honestly
    for by in mc.source_rows(TWINS).values():
        for items in by.values():
            for row in items:
                assert row["url"] is None or row["url"].startswith("https://")
                assert not re.search(r"(sources/|file:|\.\./|~/|/Users/)", row["url"] or "")
                if row["status"] in ("found", "verified", "third-party", "derived"):
                    assert row["document"] and row["url"], row["field"]


def test_source_row_html_has_value_status_document_quote_and_escapes():
    row = {"label": "<b>x</b>", "value": "1 m", "status": "found", "status_text": "read", "period": "FY2026",
           "as_of": "2026-07-27", "document": "Doc <script>", "url": "https://example.com/a.pdf", "url_note": None,
           "page": "p.3", "quote": 'He said "<i>hi</i>"', "note": "n"}
    html = mp.source_row(row)
    assert "<script>" not in html and "<b>x</b>" not in html and "<i>" not in html
    assert 'href="https://example.com/a.pdf"' in html and "p.3" in html and "<details>" in html
    bad = mp.source_row({**row, "url": "javascript:alert(1)"})
    assert "javascript:" not in bad.replace("&", "") or 'href="javascript' not in bad


def test_value_text_as_printed():
    f = TWINS["airlines"]["lufthansa"]["fields"]
    assert mc.value_text(f["diluted_shares"]) == "1,198,342,268 shares"
    assert mc.value_text(f["consensus_eps_fy27"]).startswith("1.299 per share")
    assert mc.value_text(TWINS["airlines"]["afklm"]["fields"]["guidance_low"]) == "not available"


def test_md_table_is_safe_and_aligned():
    table = mc.md_table([{"a": "x|y", "b": None}, {"a": "z\nw", "b": 2}])
    assert table.splitlines()[0] == "| a | b |" and "x/y" in table and "z w" in table
    assert mc.md_table([]) == ""


def test_source_decisions_cover_the_agreed_list():
    names = " ".join(v[0] for v in mc.SOURCE_VERDICTS)
    for source in ("GDELT", "Reuters", "Lufthansa Group", "OPEC", "Travel Weekly", "IAG", "A4E", "EASA", "EIA", "IATA",
                   "Airline Weekly", "AeroTime", "Simple Flying", "Aviation Week", "Google News RSS"):
        assert source in names, source
    verdicts = {v[0]: v[1] for v in mc.SOURCE_VERDICTS}
    assert verdicts["GDELT"] == "in" and verdicts["Aviation Week"] == "out" and verdicts["Google News RSS"] == "out"
    assert all(v[2] for v in mc.SOURCE_VERDICTS)


def test_tagger_report_states(tmp_path):
    csv_path, tags_path = tmp_path / "l.csv", tmp_path / "t.json"
    head = "id,title,url,collected,label_relevant,label_airlines,label_driver,label_direction,label_severity,label_impact\n"
    csv_path.write_text(head + "1,T,u,c,,,,,,\n", encoding="utf-8")
    assert "waiting for labels" in mc.tagger_report(csv_path, tags_path)["note"]
    csv_path.write_text(head + "1,T,u,c,yes,lufthansa,fuel_price,cost_up,2,lufthansa:negative\n", encoding="utf-8")
    note = mc.tagger_report(csv_path, tags_path)["note"]
    assert "has not been run" in note and "needs an API key" in note and "labelled by hand" in note
    (tmp_path / "labelled_by.txt").write_text("Labels drafted by the coding agent; not yet reviewed.\n", encoding="utf-8")
    assert "drafted by the coding agent" in mc.tagger_report(csv_path, tags_path)["note"]          # provenance is shown
    tags_path.write_text(json.dumps([{"relevant": True, "airlines": ["lufthansa"], "driver": "fuel_price",
                                      "direction": "cost_up", "severity": 2, "impacts": {"lufthansa": "negative"}}]))
    report = mc.tagger_report(csv_path, tags_path)
    assert report["agreement"]["driver"] == (1, 1) and report["agreement"]["impacts"] == (1, 1)
    assert "drafted by the coding agent" in report["note"]
    tags_path.write_text("[]")
    assert "do not match" in mc.tagger_report(csv_path, tags_path)["note"]
    assert "missing" in mc.tagger_report(tmp_path / "none.csv", tags_path)["note"]


# --- the two pages through the app ------------------------------------------------------------------------------

def test_app_has_story_and_method_pages_and_retired_v1(fresh):
    at = AppTest.from_file(APP, default_timeout=90).run()
    assert not at.exception and "A hypothetical jet fuel rise of +USD 100/t" in _html(at)
    at.switch_page("method.py").run()
    assert not at.exception and "Contents" in _html(at) and at.title[0].value == "Method & sources"
    # the first dashboard is gone from the app: no "Answer" subheader / old section titles
    for page in ("story.py", "method.py"):
        text = (ROOT / page).read_text(encoding="utf-8")
        assert "src.narrative" not in text and "one_line_answer" not in text
    assert not (ROOT / "src" / "narrative.py").exists()


def test_every_story_marker_has_an_entry_on_the_method_page(fresh):
    story = AppTest.from_file(APP, default_timeout=90).run()
    wanted = set(re.findall(r'href="method#([^"]+)"', _html(story)))
    assert len(wanted) >= 15                                                   # markers really are on the page
    method = AppTest.from_file(APP, default_timeout=90).run().switch_page("method.py").run()
    ids = set(re.findall(r'\bid="([^"]+)"', _html(method)))
    assert wanted <= ids, sorted(wanted - ids)
    toc = set(re.findall(r'<a href="#([^"]+)"', _html(method)))
    assert toc <= ids, sorted(toc - ids)
    assert not CLOBBERING & ids, sorted(CLOBBERING & ids)
    assert {r["id"].lower() for r in sources.assumptions()} <= ids             # every assumption has its anchor


def test_method_page_content_and_honesty(fresh):
    at = AppTest.from_file(APP, default_timeout=90).run().switch_page("method.py").run()
    text = _all_text(at)
    for needle in ("not yet checked", "This is not a probability", "Aviation Week", "Google News RSS",
                   "Lufthansa's own sensitivity table", "Expected operating profit", "AF-KLM", "Level 1"):
        assert needle.replace("AF-KLM", "Air France-KLM") in text or needle in text, needle
    assert "The confidence label on the story is therefore MEDIUM" in text           # computed, never typed in
    assert re.search(r"\d+ are \*\*verified\*\*", text) and "data/verification_log.csv" in text
    assert re.search(r"hit hardest in \d+%-\d+% of them", text)               # the share, explained, on this page only
    story = _all_text(AppTest.from_file(APP, default_timeout=90).run())
    assert "of the combinations" not in story and "not a probability" not in story


def test_public_content_has_nothing_from_the_private_files(fresh):
    story = AppTest.from_file(APP, default_timeout=90).run()
    method = AppTest.from_file(APP, default_timeout=90).run().switch_page("method.py").run()
    public = {"story page": _all_text(story), "method page": _all_text(method),
              "ASSUMPTIONS.md": (ROOT / "ASSUMPTIONS.md").read_text(encoding="utf-8"),
              "README.md": (ROOT / "README.md").read_text(encoding="utf-8"),
              "data/airlines.yaml": (ROOT / "data" / "airlines.yaml").read_text(encoding="utf-8"),
              "LABELLING_GUIDE": (ROOT / "data" / "LABELLING_GUIDE.md").read_text(encoding="utf-8")}
    for place, text in public.items():
        for pattern in FORBIDDEN:
            hit = re.search(pattern, text, flags=re.I)
            assert not hit, f"{place}: '{hit.group(0)}' found"


def test_method_page_survives_feeds_down(monkeypatch):
    st.cache_data.clear()
    st.cache_resource.clear()

    def broken(url, **kwargs):
        raise ConnectionError("offline")
    monkeypatch.setattr(src.data_sources, "load_live_prices", lambda day, **kw: REAL_LOADER(day, broken, **kw))
    at = AppTest.from_file(APP, default_timeout=90).run().switch_page("method.py").run()
    assert not at.exception and "live prices unavailable" in _html(at)
    st.cache_data.clear()
    st.cache_resource.clear()
