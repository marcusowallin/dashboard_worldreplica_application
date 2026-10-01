"""Consensus refresh: read dated MarketScreener snapshots and propose updates to data/airlines.yaml.

You save the provider pages in sources/third-party/ as
    YYYY-MM-DD_marketscreener_<airline>_<part>.(jpg|png|pdf)
The reader turns each file into positioned text tokens (images: Apple Vision OCR, on-device, macOS only;
PDFs: the PDF's own text layer), finds the year header and the rows "Net sales", "EBIT" and "EPS", and maps
every number to the year column above it by position. Nothing is written without approval
(scripts/refresh_consensus.py shows old vs new first). No AI model produces these numbers; OCR only reads
what is on the saved page, and every value is shown to you before it is used.
"""
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

SNAPSHOT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_marketscreener_(lufthansa|afklm|iag)_.+\.(jpg|jpeg|png|pdf)$", re.I)
NUMBER_RE = re.compile(r"^-?(\d{1,3}(,\d{3})+|\d+)(\.\d+)?$")
DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
MIN_CONFIDENCE = 0.9

# (row label key, year) -> twins field. Row keys come from normalise_label().
FIELD_MAP = {
    ("eps", 2026): "consensus_eps_fy26", ("eps", 2027): "consensus_eps_fy27",
    ("netsales", 2026): "consensus_revenue_fy26", ("netsales", 2027): "consensus_revenue_fy27",
    ("ebit", 2026): "consensus_ebit_fy26", ("ebit", 2027): "consensus_ebit_fy27",
}
_LOOKALIKES = str.maketrans({"І": "I", "і": "i", "Е": "E", "е": "e", "Т": "T", "В": "B", "Р": "P", "С": "C",
                             "с": "c", "о": "o", "О": "O", "а": "a", "Ѕ": "S", "ѕ": "s"})


@dataclass
class Token:
    """One piece of text on the page. x, y, w, h are fractions of the page (y from the top)."""
    text: str
    x: float
    y: float
    w: float
    h: float
    confidence: float = 1.0

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2


def normalise_label(text):
    """'EBІT1' -> 'ebit', 'Net sales !' -> 'netsales', 'EPS 1' -> 'eps'; other labels -> None.

    Handles Cyrillic look-alike letters and the footnote mark "1" (which OCR may read as 'l' or 'I').
    Exact match only, so 'EBITDA', 'EPS Estimates' or 'Earnings before Tax' never pass as a wanted row.
    """
    clean = re.sub(r"[^a-z]", "", text.translate(_LOOKALIKES).lower())
    for key in ("netsales", "ebitda", "ebit", "eps"):
        if clean in (key, key + "l", key + "i"):
            return key
    return None


def parse_number(text):
    """'1,809' -> 1809.0, '0.6097' -> 0.6097, '-234.9' -> -234.9; anything else -> None."""
    cleaned = text.strip().lstrip("•").replace("−", "-").strip()
    return float(cleaned.replace(",", "")) if NUMBER_RE.match(cleaned) else None


def _same_row(a, b):
    return abs(a.cy - b.cy) <= max(a.h, b.h) * 0.6


def year_headers(tokens):
    """Rows of year tokens (at least 3 years on one line), top to bottom: [{"y", "cols": [(year, x)]}]."""
    years = [t for t in tokens if re.fullmatch(r"20\d{2}", t.text.strip())]
    rows = []
    for t in sorted(years, key=lambda t: t.cy):
        for row in rows:
            if _same_row(row[0], t):
                row.append(t)
                break
        else:
            rows.append([t])
    return [{"y": min(t.cy for t in r), "cols": [(int(t.text), t.cx) for t in sorted(r, key=lambda t: t.cx)]}
            for r in rows if len(r) >= 3]


def read_table(tokens):
    """{(row key, year): (value, confidence, row text)} for the rows in FIELD_MAP.

    Each number goes to the nearest year column of the closest header ABOVE its row, and only if it sits within
    45% of a column's spacing (so partly cut-off columns at the left edge are ignored, never shifted).
    """
    headers = year_headers(tokens)
    found = {}
    for label in tokens:
        key = normalise_label(label.text)
        if key not in ("eps", "netsales", "ebit"):
            continue
        above = [h for h in headers if h["y"] < label.cy]
        if not above:
            continue
        cols = above[-1]["cols"]
        spacing = min(b[1] - a[1] for a, b in zip(cols, cols[1:]))
        cells = sorted((t for t in tokens if t is not label and _same_row(label, t)
                        and parse_number(t.text) is not None and t.x > label.x + label.w * 0.5),
                       key=lambda t: t.cx)
        row_text = " ".join([label.text] + [c.text for c in cells])
        for cell in cells:
            year, x = min(cols, key=lambda yx: abs(yx[1] - cell.cx))
            if abs(x - cell.cx) <= spacing * 0.45:
                found[(key, year)] = (parse_number(cell.text), cell.confidence, row_text)
    return found


def price_stamp_date(tokens):
    """The first YYYY-MM-DD on the page (MarketScreener's price timestamp), or None."""
    for t in sorted(tokens, key=lambda t: t.cy):
        match = DATE_RE.search(t.text)
        if match:
            return match.group(1)
    return None


# --- reading files ------------------------------------------------------------------------------

def tokens_from_image(path):
    """On-device OCR with Apple Vision (macOS). Raises RuntimeError elsewhere."""
    try:
        import Quartz
        import Vision
        from Foundation import NSURL
    except ImportError as err:   # not macOS / pyobjc not installed (requirements-dev.txt)
        raise RuntimeError("Image snapshots need macOS OCR: pip install -r requirements-dev.txt") from err
    source = Quartz.CGImageSourceCreateWithURL(NSURL.fileURLWithPath_(str(path)), None)
    image = Quartz.CGImageSourceCreateImageAtIndex(source, 0, None)
    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(False)
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(image, None)
    handler.performRequests_error_([request], None)
    tokens = []
    for obs in request.results() or []:
        top = obs.topCandidates_(1)[0]
        box = obs.boundingBox()          # origin bottom-left, fractions of the image
        tokens.append(Token(str(top.string()), box.origin.x, 1 - box.origin.y - box.size.height,
                            box.size.width, box.size.height, float(top.confidence())))
    return tokens


def tokens_from_pdf(path):
    """Words from the PDF's text layer (pdfplumber), page by page, as page fractions."""
    import pdfplumber
    tokens = []
    with pdfplumber.open(path) as pdf:
        for number, page in enumerate(pdf.pages):
            for w in page.extract_words(keep_blank_chars=False, use_text_flow=False):
                tokens.append(Token(w["text"], w["x0"] / page.width, number + w["top"] / page.height,
                                    (w["x1"] - w["x0"]) / page.width, (w["bottom"] - w["top"]) / page.height))
    return tokens


def read_snapshot(path):
    """Tokens for one saved file (image or PDF)."""
    path = Path(path)
    return tokens_from_pdf(path) if path.suffix.lower() == ".pdf" else tokens_from_image(path)


def latest_snapshots(folder):
    """{airline: (date, [files])} using the newest date per airline."""
    by_airline = {}
    for path in sorted(Path(folder).iterdir()):
        match = SNAPSHOT_RE.match(path.name)
        if match:
            day, airline = match.group(1), match.group(2).lower()
            by_airline.setdefault(airline, {}).setdefault(day, []).append(path)
    return {a: (max(days), days[max(days)]) for a, days in by_airline.items()}


def proposals(folder, twins, reader=read_snapshot):
    """Compare the newest snapshot values with the twins.

    Output: list of {"airline", "field", "old", "new", "as_of", "file", "confidence", "row_text", "problem"}.
    Missing rows are reported with new=None and a problem text - never silently skipped.
    """
    out = []
    for airline, (day, files) in sorted(latest_snapshots(folder).items()):
        values, stamp = {}, None
        for path in files:
            tokens = reader(path)
            stamp = stamp or price_stamp_date(tokens)
            for key, found in read_table(tokens).items():
                values.setdefault(key, found + (path.name,))
        for key, field in FIELD_MAP.items():
            old = twins["airlines"][airline]["fields"][field]["value"]
            if key not in values:
                out.append({"airline": airline, "field": field, "old": old, "new": None, "as_of": stamp or day,
                            "file": None, "confidence": None, "row_text": None,
                            "problem": f"row '{key[0]}' / {key[1]} not found in the {day} snapshot"})
                continue
            new, confidence, row_text, name = values[key]
            problem = None if confidence >= MIN_CONFIDENCE else f"low OCR confidence {confidence:.2f} - check by eye"
            out.append({"airline": airline, "field": field, "old": old, "new": new, "as_of": stamp or day,
                        "file": name, "confidence": confidence, "row_text": row_text, "problem": problem})
    return out


# --- writing the twins (only after approval) ----------------------------------------------------------

def update_field_text(text, airline, field, value, as_of, quote):
    """Return the YAML text with one field's value, as_of and quote replaced (everything else untouched)."""
    start = text.index(f"\n  {airline}:\n")
    field_start = text.index(f"\n      {field}:\n", start)
    next_field = re.search(r"\n {6}\w+:\n|\n {2}\w+:\n|\n\w", text[field_start + 1:])
    end = field_start + 1 + next_field.start() if next_field else len(text)
    block = text[field_start:end]
    number = int(value) if float(value).is_integer() else value
    block = re.sub(r"(\n {8}value: ).*", lambda m: m.group(1) + str(number), block, count=1)
    block = re.sub(r"(\n {8}as_of: ).*", lambda m: m.group(1) + yaml_quote(as_of), block, count=1)
    block = re.sub(r"(\n {8}quote: ).*", lambda m: m.group(1) + yaml_quote(quote), block, count=1)
    return text[:field_start] + block + text[end:]


def yaml_quote(text):
    """Single-quoted YAML scalar (apostrophes doubled)."""
    return "'" + str(text).replace("'", "''") + "'"


def check_round_trip(text):
    """The edited text must still parse; returns the parsed data."""
    return yaml.safe_load(text)
