"""Company twins: load and validate data/airlines.yaml (02_SPEC.md "Company twin fields").

The twins file holds one record per airline with identical fields. Every field is a small
record: value, unit, currency, period, as_of, document, page, quote, url, level, status, note.
Values are stored exactly as printed (e.g. 82 with unit "%"); converting units is the model's job.

This module only reads and checks. It never changes or invents a number.
"""
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "airlines.yaml"

FIELD_KEYS = (
    "value", "unit", "currency", "period", "as_of", "document",
    "page", "quote", "url", "level", "status", "note",
)

# Statuses where the field carries a number, and where it must be empty (null).
STATUSES_WITH_VALUE = {"verified", "found", "derived", "assumption", "third-party"}
STATUSES_WITHOUT_VALUE = {"not-disclosed", "not-applicable", "to-extract"}
ALLOWED_STATUSES = STATUSES_WITH_VALUE | STATUSES_WITHOUT_VALUE

# Units as printed in the companies' documents. Adding a new unit is a deliberate choice.
ALLOWED_UNITS = {
    "million t", "per t", "bn", "m", "%", "% of volume", "% operating margin",
    "shares", "thousand shares", "per share", "cents per share", "USD per EUR", "million ASK",
}


class TwinsError(ValueError):
    """Raised when the twins file is missing or breaks a rule. The message lists every problem."""


def load_twins(path=DEFAULT_PATH):
    """Read the twins file and validate it.

    Input: path to the YAML file (defaults to data/airlines.yaml).
    Output: the parsed file as a dictionary (keys "meta", "documents", "airlines").
    Raises TwinsError if the file is missing, unreadable or fails any check.
    """
    path = Path(path)
    if not path.exists():
        raise TwinsError(f"Twins file not found: {path}")
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as err:
        raise TwinsError(f"Twins file is not valid YAML: {err}") from err
    problems = validate_twins(data)
    if problems:
        raise TwinsError("Twins file failed validation:\n- " + "\n- ".join(problems))
    return data


def validate_twins(data):
    """Check the whole file and return a list of problems (empty list = all good).

    Checks: identical field names for every airline, then each field on its own
    (see check_field).
    """
    if not isinstance(data, dict) or "airlines" not in data:
        return ["File has no 'airlines' section."]
    airlines = data["airlines"]
    documents = set((data.get("documents") or {}).keys())
    problems = []

    field_sets = {name: set((record.get("fields") or {}).keys()) for name, record in airlines.items()}
    reference_name, reference_fields = next(iter(field_sets.items()))
    for name, fields in field_sets.items():
        if fields != reference_fields:
            missing = sorted(reference_fields - fields)
            extra = sorted(fields - reference_fields)
            problems.append(f"{name}: fields differ from {reference_name} (missing {missing}, extra {extra})")

    for name, record in airlines.items():
        for field_name, field in (record.get("fields") or {}).items():
            problems.extend(check_field(f"{name}.{field_name}", field, documents))
    return problems


def check_field(label, field, documents):
    """Check one field record and return a list of problems.

    Input: a label for messages (e.g. "iag.tax_rate_marginal"), the field dictionary,
    and the set of known document IDs.
    """
    if not isinstance(field, dict):
        return [f"{label}: not a field record"]
    problems = []
    missing_keys = [key for key in FIELD_KEYS if key not in field]
    if missing_keys:
        problems.append(f"{label}: missing keys {missing_keys}")

    status = field.get("status")
    value = field.get("value")
    if status not in ALLOWED_STATUSES:
        problems.append(f"{label}: unknown status '{status}'")
    elif status in STATUSES_WITH_VALUE and not _is_number(value):
        problems.append(f"{label}: status '{status}' needs a numeric value, got {value!r}")
    elif status in STATUSES_WITHOUT_VALUE and value is not None:
        problems.append(f"{label}: status '{status}' must have value null, got {value!r}")

    if field.get("unit") not in ALLOWED_UNITS:
        problems.append(f"{label}: unknown unit '{field.get('unit')}'")

    if value is not None:
        if field.get("level") not in (1, 2, 3, 4, 5):
            problems.append(f"{label}: source level must be 1-5, got {field.get('level')!r}")
        if field.get("document") not in documents:
            problems.append(f"{label}: document '{field.get('document')}' is not in the documents list")
    return problems


def get_field(twins, airline, field_name):
    """Return the full field record (value plus source) for one airline, or raise TwinsError."""
    try:
        return twins["airlines"][airline]["fields"][field_name]
    except KeyError as err:
        raise TwinsError(f"No field '{field_name}' for airline '{airline}'") from err


def get_value(twins, airline, field_name):
    """Return the value exactly as stored, or None if the field has no value.

    None means "missing" (not disclosed, not applicable, or not yet extracted); callers
    decide what to show instead of crashing.
    """
    return get_field(twins, airline, field_name)["value"]


# How to turn each printed unit into the model's units (fractions, tonnes, currency units,
# share counts, currency per share). The model never sees "%", "million t" or "cents".
MODEL_UNIT_FACTORS = {
    "%": 0.01, "% of volume": 0.01, "% operating margin": 0.01,
    "million t": 1_000_000, "per t": 1,
    "bn": 1_000_000_000, "m": 1_000_000,
    "shares": 1, "thousand shares": 1_000,
    "per share": 1, "cents per share": 0.01,
    "USD per EUR": 1,
    "million ASK": 1_000_000,
}


def get_model_value(twins, airline, field_name):
    """Return the value converted to model units, or None if the field has no value.

    Examples: 82 "%" -> 0.82; 9.42 "million t" -> 9,420,000 t; 5,031,980 "thousand shares"
    -> 5,031,980,000 shares; 69.5 "cents per share" -> 0.695 per share; 1,960 "m" -> 1.96e9.
    Currency is not converted here (USD stays USD); see the field's "currency" key.
    """
    field = get_field(twins, airline, field_name)
    if field["value"] is None:
        return None
    return field["value"] * MODEL_UNIT_FACTORS[field["unit"]]


def _is_number(value):
    """True for int or float, but not for True/False (which YAML could produce)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)
