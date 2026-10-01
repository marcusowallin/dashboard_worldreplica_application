"""Validation T2: reproduce Lufthansa's own sensitivity table (Q2 2026 charts, slide 17).

The slide prints Lufthansa's expected FY2026 "mixed JET rate" after hedging (USD/t) for a grid
of average Brent (rows) and jet crack (columns), in USD/bbl, "for months not yet realized",
as of 27 July 2026. Centre cell: Brent 84, crack 64 -> 1,036 USD/t (= printed FY26 price after hedge).

We predict the grid with the linear model of 06_METHODOLOGY.md section 3. Only the LEVEL is
anchored at the printed centre (we have no model of Lufthansa's absolute fuel price); every other
cell is predicted from the sensitivities. No tuning to fit (section 9).

  predicted(B, C) = 1,036 + s * 7.9 * (u_B * (B - 84) + u_C * (C - 64))
  s = share of FY26 volume not yet realised (months after the as-of date, periods.py)
"""
from datetime import date

from src.model.fuel import BBL_PER_TONNE, scale_printed_mix, unprotected_shares
from src.model.periods import quarter_volumes, remaining_quarter_shares, remaining_volume

SOURCE = "Lufthansa Q2 2026 results charts, slide 17 (table 'LH mixed JET rate (vs. 2026 FCT) in $/mt')"
BRENT_ROWS = (114, 104, 94, 84, 74, 64, 54)        # USD/bbl, avg 2026 Brent for months not yet realised
CRACK_COLS = (44, 54, 64, 74, 84)                  # USD/bbl, avg 2026 jet crack
PRINTED = {                                        # USD/t, read by position from the PDF (30 Sep 2026)
    114: (1057, 1083, 1110, 1137, 1164),
    104: (1030, 1055, 1082, 1108, 1135),
    94: (1012, 1033, 1059, 1085, 1112),
    84: (1004, 1014, 1036, 1062, 1088),
    74: (995, 1005, 1017, 1039, 1065),
    64: (981, 991, 1003, 1018, 1040),
    54: (968, 978, 990, 1006, 1026),
}
CENTRE = (84, 64)
TABLE_AS_OF = date(2026, 7, 27)


def remaining_share(fy_volume_t, q3_volume_t, as_of=TABLE_AS_OF):
    """Share of FY2026 volume not yet realised after `as_of` (printed Q3, other quarters FY/4)."""
    vols = quarter_volumes(fy_volume_t, {3: q3_volume_t})
    return remaining_volume(vols, remaining_quarter_shares(as_of, 2026)) / fy_volume_t


def predict_grid(u_brent, u_crack, share, centre_price=None):
    """Predicted mixed jet rate (USD/t) for every printed cell."""
    centre_price = PRINTED[CENTRE[0]][CRACK_COLS.index(CENTRE[1])] if centre_price is None else centre_price
    return {b: tuple(centre_price + share * BBL_PER_TONNE * (u_brent * (b - CENTRE[0]) + u_crack * (c - CENTRE[1]))
                     for c in CRACK_COLS) for b in BRENT_ROWS}


def error_grid(predicted):
    """Predicted minus printed, per cell (USD/t)."""
    return {b: tuple(p - q for p, q in zip(predicted[b], PRINTED[b])) for b in BRENT_ROWS}


def error_summary(errors):
    """Mean absolute error, max absolute error (USD/t) and the cell where the max occurs."""
    cells = [(abs(e), b, c) for b in BRENT_ROWS for c, e in zip(CRACK_COLS, errors[b])]
    worst = max(cells)
    return {"mean_abs": sum(e for e, _, _ in cells) / len(cells), "max_abs": worst[0],
            "worst_cell": (worst[1], worst[2])}


def printed_slopes():
    """USD/t per +10 USD/bbl step, read straight off the printed table (no model).

    brent: along the crack-64 column, from each row to the next higher row.
    crack: along the Brent-84 row, from each column to the next.
    """
    col = CRACK_COLS.index(CENTRE[1])
    rows = sorted(BRENT_ROWS)
    brent = {f"{a}->{b}": PRINTED[b][col] - PRINTED[a][col] for a, b in zip(rows, rows[1:])}
    row = PRINTED[CENTRE[0]]
    crack = {f"{a}->{b}": row[i + 1] - row[i] for i, (a, b) in enumerate(zip(CRACK_COLS, CRACK_COLS[1:]))}
    return {"brent": brent, "crack": crack}


def implied_unprotected(slope_per_10_bbl, share):
    """Unprotected share implied by a printed slope: slope / (share * 7.9 * 10)."""
    return slope_per_10_bbl / (share * BBL_PER_TONNE * 10)


def lufthansa_validation(twins, g=0.8):
    """Run T2 with the twins' printed inputs. Returns everything the page and tests need."""
    from src.twins import get_model_value
    fy = get_model_value(twins, "lufthansa", "fuel_volume_fy26")
    q3 = get_model_value(twins, "lufthansa", "fuel_volume_q3_26")
    ratio = get_model_value(twins, "lufthansa", "hedge_ratio_rest_fy26")
    parts = {k: get_model_value(twins, "lufthansa", f"hedge_mix_{k}") for k in ("brent", "gasoil", "jet")}
    mix = scale_printed_mix(ratio, parts)
    u_b, u_c = unprotected_shares(mix["brent"], mix["gasoil"], mix["jet"], g)
    share = remaining_share(fy, q3)
    predicted = predict_grid(u_b, u_c, share)
    errors = error_grid(predicted)
    return {"u_brent": u_b, "u_crack": u_c, "share": share, "predicted": predicted,
            "errors": errors, "summary": error_summary(errors), "slopes": printed_slopes()}


def table_implied_exposures(share, brent_up=True, crack_up=True):
    """Unprotected shares implied by Lufthansa's own table for a move away from the centre.

    Uses the printed step next to the centre in the direction of the move:
      Brent up 84->94 (down 74->84); crack up 64->74 (down 54->64).
    Status "derived" (level 1): slope / (share * 7.9 * 10). Used as Lufthansa's
    "company table" case for FY2026 remaining (decision 30 Sep 2026, ASSUMPTIONS.md A24).
    """
    slopes = printed_slopes()
    brent_step = slopes["brent"]["84->94" if brent_up else "74->84"]
    crack_step = slopes["crack"]["64->74" if crack_up else "54->64"]
    return {"u_brent": min(1.0, implied_unprotected(brent_step, share)),
            "u_crack": min(1.0, implied_unprotected(crack_step, share))}


# --- T9: fuel bill reconciliation ------------------------------------------------------------

def fuel_bill_reconciliation(twins, airline):
    """Volume x printed price after hedge vs the printed fuel bill (trust item T9).

    Returns {"computed", "printed", "gap_share", "note"} or {"note"} when not possible.
    Lufthansa: USD volume x price converted at its own planning rate, vs fossil fuel expense
    (excl. mandatory SAF). AF-KLM: volume is DERIVED from the bill, so the check is circular.
    IAG: no full-year price after hedge printed.
    """
    from src.twins import get_field, get_model_value
    if airline == "afklm":
        return {"note": "Not an independent check: AF-KLM volume is derived from its printed bill "
                        "(USD 8,900m / USD 1,024/t), so the reconciliation is zero by construction."}
    if airline == "iag":
        return {"note": "Not possible: IAG prints no full-year price after hedge (only Q3/Q4 prices on "
                        "slide 30), and its fuel cost includes emissions charges."}
    volume = get_model_value(twins, airline, "fuel_volume_fy26")
    price = get_model_value(twins, airline, "jet_price_after_hedge_fy26")
    fx = get_model_value(twins, airline, "planning_fx_usd_per_eur")
    printed_total = get_model_value(twins, airline, "fuel_bill_fy26")
    # Slide 17 prints fossil 8.46bn + mandatory SAF 0.20bn = 8.66bn; volume x price covers fossil fuel.
    fossil = printed_total - 0.20e9
    computed = volume * price / fx
    return {"computed": computed, "printed": fossil, "gap_share": computed / fossil - 1,
            "note": f"{get_field(twins, airline, 'fuel_bill_fy26')['note']} Compared with fossil fuel "
                    f"expense EUR 8.46bn (slide 17), converted at LH's planning rate 1.151."}


# --- T10: confidence score per airline (graded rule, 2 Oct 2026; 06_METHODOLOGY.md section 13) -------------------

# The inputs behind each headline period. Market prices (FRED, ECB) and model constants (g, 7.9 bbl/t) are not counted;
# they are listed in ASSUMPTIONS.md. Fields that do not apply to an airline are left out of its score.
CONFIDENCE_INPUTS = {
    "FY2027": (
        "fuel_volume_fy26", "hedge_ratio_fy27", "hedge_ratio_fy27_upper", "hedge_mix_gasoil", "hedge_mix_brent",
        "hedge_mix_jet", "recapture_rate", "tax_rate_marginal", "minority_share", "diluted_shares_forward",
        "consensus_eps_fy27", "consensus_ebit_fy27",
    ),
    "FY2026": (
        "fuel_volume_fy26", "fuel_volume_q3_26", "fuel_volume_q4_26", "hedge_ratio_rest_fy26", "hedge_ratio_q3_26",
        "hedge_ratio_q4_26", "hedge_mix_gasoil", "hedge_mix_brent", "hedge_mix_jet", "recapture_rate",
        "tax_rate_marginal", "minority_share", "diluted_shares_forward", "consensus_eps_fy26", "consensus_ebit_fy26",
    ),
}
# credit per input by how it is sourced; 'verified' is split by source level in input_credit()
CREDIT_SCALE = (
    ("verified, company or official document (levels 1-3)", 1.00,
     "the figure was checked against the document: quoted words on the cited page, number, unit and period"),
    ("verified, third-party consensus (level 4)", 0.75,
     "checked against the dated provider snapshot and the live provider page, but an analyst projection"),
    ("derived", 0.75, "calculated from printed figures; the formula is in the data file and reproduces the value"),
    ("assumption or third-party figure not checked", 0.50, "labelled, with its reasoning, and tested in the sensitivities"),
    ("found: read from a document, not yet checked", 0.25, "may be right, but nobody has compared it with the page"),
    ("not disclosed", 0.25, "unknown; the result carries it as a range instead of a point"),
)
HIGH_AT, MEDIUM_AT = 0.80, 0.50
CONFIDENCE_RULE = ("Confidence is a score of how well the inputs behind the headline year are sourced. Each input gets "
                   "credit by how it is sourced - checked company figure 1.00; checked consensus or calculated from "
                   "printed figures 0.75; labelled assumption or unchecked third-party figure 0.50; read from a document "
                   "but not yet checked 0.25; not disclosed (carried as a range) 0.25 - and the score is the average. "
                   "HIGH from 80% (and no unchecked input), MEDIUM from 50%, otherwise LOW. It measures how well the "
                   "inputs are sourced, not how right the model is. Market prices and model constants (g, 7.9 bbl/t) are "
                   "not counted (ASSUMPTIONS.md). The table below shows every input.")


def input_credit(field):
    """(credit, why) for one twin field, or None when the field does not apply."""
    status, level = field["status"], field["level"]
    if status in ("not-applicable", "to-extract"):
        return None
    if status == "verified":
        return (1.00, CREDIT_SCALE[0][2]) if (level or 1) <= 3 else (0.75, CREDIT_SCALE[1][2])
    credit = {"derived": 0.75, "third-party": 0.50, "assumption": 0.50, "found": 0.25, "not-disclosed": 0.25}[status]
    why = {"derived": CREDIT_SCALE[2][2], "third-party": "an analyst or press figure, not checked against the document",
           "assumption": CREDIT_SCALE[3][2], "found": CREDIT_SCALE[4][2], "not-disclosed": CREDIT_SCALE[5][2]}[status]
    return credit, why


def confidence_breakdown(twins, airline, period="FY2027"):
    """One row per input used for the period: {"field", "status", "level", "credit", "why"} (not-applicable left out)."""
    fields = twins["airlines"][airline]["fields"]
    rows = []
    for name in CONFIDENCE_INPUTS[period]:
        graded = input_credit(fields[name])
        if graded:
            rows.append({"field": name, "status": fields[name]["status"], "level": fields[name]["level"],
                         "credit": graded[0], "why": graded[1]})
    return rows


def confidence_label(twins, airline, period="FY2027"):
    """(label, score 0-1, fields with less than full credit) - 06_METHODOLOGY.md section 13."""
    rows = confidence_breakdown(twins, airline, period)
    score = sum(r["credit"] for r in rows) / len(rows) if rows else 0.0
    unchecked = any(r["status"] == "found" for r in rows)
    label = "HIGH" if score >= HIGH_AT and not unchecked else "MEDIUM" if score >= MEDIUM_AT else "LOW"
    return label, score, [r["field"] for r in rows if r["credit"] < 1.0]
