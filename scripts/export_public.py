"""Build the clean public copy of this repository, or check the tracked files for anything that must not be public.

    .venv/bin/python scripts/export_public.py                 # build ../fuel-shock-monitor-public (one fresh commit)
    .venv/bin/python scripts/export_public.py --check         # scan the tracked files only (also run by CI)
    .venv/bin/python scripts/export_public.py --out DIR --skip-tests

The export contains only what git tracks. A new copy is one commit with no history; an existing copy (a folder that
already has a .git) gets one normal new commit on top, so it can be pushed without a force push. It stops, and writes nothing, when:
  - the working tree has uncommitted changes (the copy must be exactly a commit);
  - a tracked path is on the deny list (planning notes, source PDFs, secrets, archives);
  - a file contains something that looks like a secret (API keys, tokens, private keys);
  - a file contains a forbidden term. The terms come from tests/private_forbidden.txt, which is git-ignored so it never
    leaves the machine that has it; without that file the term check is skipped and says so;
  - the tests fail inside the copy.
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVATE_TERMS = ROOT / "tests" / "private_forbidden.txt"

# Paths that must never be tracked in the public repository.
DENY_PATHS = (
    r"^sources/", r"(^|/)secrets\.toml$", r"^\.env", r"\.pdf$", r"\.zip$", r"^design/reference/",
    r"^(CLAUDE|STATUS|PROMPT_LOG|REVIEW|REVIEW_BACKLOG|DESIGN_BRIEF|DESIGN_REVIEW|FULL_REVIEW|VERIFY_CHECKLIST|START_HERE)\.md$",
    r"^(00|01|02|04|05|07|08)_[A-Za-z_]+\.(md|txt)$",       # the private planning kit (03 and 06 are public documents)
)
# Things that look like credentials. The placeholder in .streamlit/secrets.toml.example is allowed.
SECRET_PATTERNS = (r"sk-ant-[A-Za-z0-9_-]{20,}", r"ghp_[A-Za-z0-9]{30,}", r"github_pat_[A-Za-z0-9_]{30,}",
                   r"AKIA[0-9A-Z]{16}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".yaml", ".yml", ".csv", ".json", ".cfg", ".ini", ".html", ".css", ""}


def load_forbidden(path=PRIVATE_TERMS):
    """Regexes from the private term list (one per line), or None when the list is not on this machine."""
    if not Path(path).exists():
        return None
    return [ln.strip() for ln in Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()]


def denied(relative_path):
    """The deny-list rule that a tracked path breaks, or None."""
    for rule in DENY_PATHS:
        if re.search(rule, relative_path):
            return rule
    return None


def scan_files(root, relative_paths, forbidden=None):
    """Problems in the given files under root: [(path, kind, detail)]. Deny list on the path, secrets and terms in text."""
    problems = []
    for rel in relative_paths:
        rule = denied(rel)
        if rule:
            problems.append((rel, "denied path", rule))
            continue
        path = Path(root) / rel
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, text):
                problems.append((rel, "looks like a secret", pattern))
        for term in forbidden or ():
            hit = re.search(term, text, flags=re.IGNORECASE)
            if hit:
                problems.append((rel, "forbidden term", f"line {text.count(chr(10), 0, hit.start()) + 1}"))   # never print the term
    return problems


def tracked_files(repo):
    out = subprocess.check_output(["git", "-C", str(repo), "ls-files", "-z"], text=True)
    return [p for p in out.split("\0") if p]


def report(problems):
    for rel, kind, detail in problems:
        print(f"  {kind}: {rel} ({detail})")


def check(repo=ROOT):
    """Scan the tracked files. Returns True when clean."""
    forbidden = load_forbidden()
    if forbidden is None:
        print("note: tests/private_forbidden.txt not found - forbidden-term check skipped (deny list and secrets still run)")
    problems = scan_files(repo, tracked_files(repo), forbidden)
    report(problems)
    print("clean" if not problems else f"{len(problems)} problem(s)")
    return not problems


def build(out, skip_tests=False):
    """Export HEAD to `out` as a single fresh commit. Returns True on success."""
    out = Path(out).resolve()
    if out == ROOT or ROOT in out.parents or "public" not in out.name:
        print(f"refusing: --out must be a separate folder whose name contains 'public', got {out}")
        return False
    if subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True).strip():
        print("refusing: the working tree has uncommitted changes - commit first so the copy is exactly a commit")
        return False
    forbidden = load_forbidden()
    if forbidden is None:
        print("refusing: tests/private_forbidden.txt is missing, so the forbidden-term check cannot run")
        return False
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "head.tar"
        subprocess.check_call(["git", "-C", str(ROOT), "archive", "--format=tar", "-o", str(archive), "HEAD"])
        staged = Path(tmp) / "tree"
        staged.mkdir()
        subprocess.check_call(["tar", "-xf", str(archive), "-C", str(staged)])
        files = sorted(str(p.relative_to(staged)) for p in staged.rglob("*") if p.is_file())
        problems = scan_files(staged, files, forbidden)
        if problems:
            report(problems)
            print("refusing: the export is not clean")
            return False
        if not skip_tests:
            print("running the tests inside the copy ...")
            result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=staged)
            if result.returncode != 0:
                print("refusing: the tests fail in the copy")
                return False
        updating = (out / ".git").exists()
        if updating:                                      # an existing public copy: a normal new commit on top, no force push
            for item in out.iterdir():
                if item.name != ".git":
                    shutil.rmtree(item) if item.is_dir() else item.unlink()
            for item in staged.iterdir():
                shutil.copytree(item, out / item.name) if item.is_dir() else shutil.copy2(item, out / item.name)
        else:
            if out.exists():
                shutil.rmtree(out)
            shutil.copytree(staged, out)
    author = subprocess.check_output(["git", "-C", str(ROOT), "log", "-1", "--format=%an%n%ae%n%h"], text=True).split("\n")
    if updating:
        subprocess.check_call(["git", "add", "-A"], cwd=out)
        if not subprocess.check_output(["git", "status", "--porcelain"], cwd=out, text=True).strip():
            print(f"{out} is already up to date")
            return True
        subprocess.check_call(["git", "commit", "-q", "-m", f"Update ({author[2]})"], cwd=out)
        print(f"updated {out}: {len(files)} files, one new commit on top of the existing history")
        return True
    for cmd in (["git", "init", "-q", "-b", "main"], ["git", "config", "user.name", author[0]],
                ["git", "config", "user.email", author[1]], ["git", "add", "-A"],
                ["git", "commit", "-q", "-m", "Airline fuel shock monitor"]):
        subprocess.check_call(cmd, cwd=out)
    print(f"built {out}: {len(files)} files, one commit")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(ROOT.parent / "fuel-shock-monitor-public"))
    parser.add_argument("--check", action="store_true", help="only scan the tracked files")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args(argv)
    return 0 if (check() if args.check else build(args.out, args.skip_tests)) else 1


if __name__ == "__main__":
    sys.exit(main())
