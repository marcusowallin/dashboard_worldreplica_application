"""The public-export script (scripts/export_public.py): what it refuses, and that the tracked files are clean."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import export_public as ex  # noqa: E402

import pytest  # noqa: E402

IN_CHECKOUT = (ROOT / ".git").exists()          # false in an unpacked archive (the export is tested before it gets a .git)


def test_deny_list_catches_private_planning_files_sources_and_secrets():
    for path in ("CLAUDE.md", "STATUS.md", "FULL_REVIEW.md", "02_SPEC.md", "sources/lufthansa/report.pdf",
                 ".streamlit/secrets.toml", "notes/annual.pdf", "design-reference.zip", ".env.local"):
        assert ex.denied(path), path
    for path in ("README.md", "ASSUMPTIONS.md", "data/airlines.yaml", ".streamlit/secrets.toml.example", "src/story/steps.py",
                 "03_DATA_REGISTER.md", "06_METHODOLOGY.md"):                         # these two are public documents
        assert not ex.denied(path), path


def test_scan_flags_secrets_and_forbidden_terms_without_printing_the_term(tmp_path):
    (tmp_path / "ok.py").write_text("print('fine')\n")
    (tmp_path / "key.py").write_text("KEY = 'sk-ant-" + "a" * 30 + "'\n")
    (tmp_path / "placeholder.toml").write_text('ANTHROPIC_API_KEY = "sk-ant-your-key-here"\n')
    (tmp_path / "text.md").write_text("line one\nthe quick brown fox\n")
    problems = ex.scan_files(tmp_path, ["ok.py", "key.py", "placeholder.toml", "text.md", "STATUS.md"], [r"brown\s+fox"])
    kinds = {(p[0], p[1]) for p in problems}
    assert ("key.py", "looks like a secret") in kinds and ("text.md", "forbidden term") in kinds
    assert ("STATUS.md", "denied path") in kinds
    assert not any(p[0] in ("ok.py", "placeholder.toml") for p in problems)          # a placeholder is not a secret
    assert all("brown" not in str(p) for p in problems)                              # the term itself is never printed
    assert ("text.md", "forbidden term", "line 2") in problems


@pytest.mark.skipif(not IN_CHECKOUT, reason="needs a git checkout")
def test_private_term_list_is_optional_and_never_part_of_the_export(tmp_path):
    assert ex.load_forbidden(tmp_path / "missing.txt") is None
    (tmp_path / "terms.txt").write_text("alpha\n\nbeta gamma\n")
    assert ex.load_forbidden(tmp_path / "terms.txt") == ["alpha", "beta gamma"]
    tracked = ex.tracked_files(ROOT)
    assert "tests/private_forbidden.txt" not in tracked


def test_build_refuses_a_destination_inside_the_repo_or_without_public_in_its_name(tmp_path, capsys):
    assert ex.build(ROOT / "dist") is False
    assert ex.build(tmp_path / "somewhere") is False
    assert "refusing" in capsys.readouterr().out


@pytest.mark.skipif(not IN_CHECKOUT, reason="needs a git checkout")
def test_the_tracked_files_of_this_repository_are_clean():
    """No denied path, no secret and (where the private list exists) no forbidden term in anything git tracks."""
    problems = ex.scan_files(ROOT, ex.tracked_files(ROOT), ex.load_forbidden())
    assert problems == [], problems
