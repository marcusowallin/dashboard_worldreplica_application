"""Download the company documents listed in 03_DATA_REGISTER.md into sources/.

Run from the project folder with the project's venv:   .venv/bin/python get_sources.py
(The old system Python 3.8 on this Mac fails with SSL certificate errors.)
Uses only Python's standard library - nothing to install.
Existing files are skipped, so it is safe to run again.
Company documents are for personal analysis: sources/ is git-ignored and never pushed.
"""
import os
import urllib.request

DOCS = [
    # (airline, period, filename, url)
    ("lufthansa", "2026-Q2", "LH-Q2-2026-results-charts.pdf",
     "https://investor-relations.lufthansagroup.com/fileadmin/downloads/en/charts-speeches/LH-QR-2026-2-charts.pdf"),
    ("lufthansa", "2026-Q2", "LH-2nd-interim-report-2026.pdf",
     "https://investor-relations.lufthansagroup.com/fileadmin/downloads/en/financial-reports/interims-reports/LH-QR-2026-2-e.pdf"),
    ("afklm", "2026-Q2", "20260729-2026-q2-afklm-press-release-1 (1).pdf",
     "https://www.airfranceklm.com/sites/default/files/2026-07/20260729-2026-q2-afklm-press-release-1.pdf"),
    ("afklm", "2026-Q2", "q2_2026-afklm-results-presentation.pdf",
     "https://www.airfranceklm.com/sites/default/files/2026-07/q2_2026-afklm-results-presentation.pdf"),
    ("afklm", "2026-Q1", "afklm_q1_2026_results-presentation.pdf",
     "https://www.airfranceklm.com/sites/default/files/2026-04/afklm_q1_2026_results-presentation.pdf"),
    # Note: the file saved under this name is actually a 50-page PDF (the full H1 results
    # announcement), not an HTML page. Name kept to match the file in sources/.
    ("iag", "2026-H1", "IAG-H1-2026-press-release.html",
     "https://www.iairgroup.com/press-releases/2026/iag-half-year-results-2026/"),
    ("iag", "2026-H1", "IAG-H1-2026-results-presentation.pdf",
     "https://www.iairgroup.com/media/pwslnxy2/iag-results-presentation-q2-2026.pdf"),
    # Added in a later step (29 Sep 2026) - links found on the companies' own IR sites
    ("lufthansa", "2025-FY", "LH-AR-2025-e.pdf",
     "https://investor-relations.lufthansagroup.com/fileadmin/downloads/en/financial-reports/annual-reports/LH-AR-2025-e.pdf"),
    ("lufthansa", "2026-Q2", "LHG-Consensus-Q2-2026.pdf",
     "https://investor-relations.lufthansagroup.com/fileadmin/downloads/en/financial-reports/consensus/LHG-Consensus-Q2-2026.pdf"),
    ("iag", "2025-FY", "iag-annual-report-and-accounts-2025.pdf",
     "https://www.iairgroup.com/media/ktnlp1jx/iag-annual-report-and-accounts-2025.pdf"),
    ("iag", "2025-FY", "full-year-results-release-for-the-year-to-31-december-2025.pdf",
     "https://www.iairgroup.com/media/wd4dsjef/full-year-results-release-for-the-year-to-31-december-2025.pdf"),
    ("iag", "2026-H1", "iag-h1-2026-results-call-transcript.pdf",
     "https://www.iairgroup.com/media/ymmjb2dv/iag-h1-2026-results-call-transcript.pdf"),
]

# No fixed link found yet - find on the investor-relations sites (or ask Claude Code to find them)
TO_FIND = [
    # Air France-KLM blocks automated downloads (Cloudflare check) - download in your browser.
    # Already in sources/afklm/: 2025-FY/afklm_full_year_2025_press_release_english.pdf,
    # 2025-FY/urd-2025-veng.pdf, 2026-Q1/q1-2026-afklm-press-release.pdf
    "Air France-KLM - H1 2026 financial statements and notes -> sources/afklm/2026-Q2/",
    "Air France-KLM - consensus page as dated PDF -> sources/afklm/2026-Q2/"
    "  https://www.airfranceklm.com/en/finance/investors-and-analysts/consensus",
    "IAG - consensus page as dated PDF -> sources/iag/2026-H1/"
    "  https://www.iairgroup.com/investors-and-shareholders/analysts-consensus/",
    "Third-party consensus EPS snapshots (after approval) -> sources/third-party/",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (personal research; fuel-shock-monitor prototype)"}


def download(airline, period, filename, url):
    folder = os.path.join("sources", airline, period)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return "skipped (already there)", path
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    with open(path, "wb") as f:
        f.write(data)
    return f"downloaded ({len(data) // 1024} KB)", path


def main():
    failed = []
    for airline, period, filename, url in DOCS:
        try:
            status, path = download(airline, period, filename, url)
            print(f"OK    {path}  - {status}")
        except Exception as e:  # network errors, blocked sites, moved files
            print(f"FAIL  {filename}  - {e}")
            failed.append((filename, url))

    if failed:
        print("\nDownload these manually in your browser (save into the same folder names):")
        for filename, url in failed:
            print(f"  {filename}: {url}")

    print("\nStill to find on the investor-relations sites:")
    for item in TO_FIND:
        print(f"  - {item}")
    print("\nTip: check each PDF opens, and that the file date matches the register.")


if __name__ == "__main__":
    main()
