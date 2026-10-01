"""Step 10 - try it yourself: the user's scenario as overrides on a COPY of the twins (the model never changes).

  move           crude (Brent) and jet premium moves in USD/t -> the scenario split
  pass_shift_pp  added to every airline's printed pass-through rate (clipped 0-100%), keeping their differences
  lh_hedge       Lufthansa's 2027 hedge cover range (low, high) in % - replaces 29% (printed) / ~50% (reported)
Every number on the page is recomputed from the copy, so hero and steps always agree.
"""
import copy

from src.model.run import US

PRESET_MOVES = (50.0, 100.0, 200.0, -100.0)          # USD/t, split like the benchmark (median crude share)


def apply_overrides(twins, pass_shift_pp=0.0, lh_hedge=None):
    """A modified copy of the twins (values in their printed units). The original is untouched."""
    out = copy.deepcopy(twins)
    if pass_shift_pp:
        for record in out["airlines"].values():
            field = record["fields"]["recapture_rate"]
            if field["value"] is not None:
                field["value"] = min(100.0, max(0.0, field["value"] + pass_shift_pp))
                field["note"] = f"Scenario (Step 9): printed rate {pass_shift_pp:+.0f} pp"
    if lh_hedge:
        fields = out["airlines"][US]["fields"]
        fields["hedge_ratio_fy27"]["value"], fields["hedge_ratio_fy27_upper"]["value"] = float(lh_hedge[0]), float(lh_hedge[1])
        fields["hedge_ratio_fy27"]["note"] = fields["hedge_ratio_fy27_upper"]["note"] = "Scenario (Step 9)"
    return out


def preset_split(move, benchmark_split):
    """A preset move split like the benchmark: (crude, premium) USD/t, whole numbers."""
    total = benchmark_split[0] + benchmark_split[1]
    crude = round(move * benchmark_split[0] / total) if total else round(move / 2)
    return float(crude), float(move - crude)


def _signed(value):
    """+51 / \u221249 (true minus sign, whole number)."""
    return f"{'+' if value >= 0 else chr(0x2212)}{abs(value):,.0f}"


def describe(split, pass_shift_pp, lh_hedge, defaults):
    """One line for the hero chip: what differs from the default scenario."""
    move = split[0] + split[1]
    parts = [f"jet fuel {_signed(move)[0]}USD {abs(move):,.0f}/t "
             f"({_signed(split[0])} crude / {_signed(split[1])} premium)"]
    if pass_shift_pp:
        parts.append(f"pass-through {_signed(pass_shift_pp)} pp")
    if tuple(lh_hedge) != tuple(defaults["lh_hedge"]):
        parts.append(f"Lufthansa 2027 hedge {lh_hedge[0]:.0f}-{lh_hedge[1]:.0f}%")
    return " · ".join(parts)
