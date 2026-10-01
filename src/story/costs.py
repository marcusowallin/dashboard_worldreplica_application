"""Steps 4-5: extra fuel cost in EUR (gross, after hedging), then pass-through to net cost.

Same inputs and the same gross-cost function as the hero (src/story/robustness.py), so the net cost here equals the
hero's euro figure exactly (tested):
  gross     = extra fuel cost after hedging (EUR)            Step 4
  recovered = pass-through rate x gross                      Step 5 (printed rate; light case: 50%, A25)
  net       = gross - recovered = hero 'net cost'            Step 5 -> hero
Size-neutral views of the 2027 gross cost (FY2025 bases, printed, ASSUMPTIONS.md A30):
  % of total operating costs = gross / FY2025 operating costs
  euro cents per seat-km     = gross / FY2025 ASK x 100
Lufthansa FY2026 includes its options effect: the 'company table' case (A24, its own sensitivity table) next to
the swap view. For FY2027 no such table is printed, so the swap view stands (a stated limitation).
"""
from src.model.run import AIRLINES, cases_for
from src.story.robustness import BENCHMARK_SPLIT, RECAPTURE_LOW, benchmark_market, case_inputs, gross_fuel_cost_eur
from src.twins import get_model_value


def cost_cases(twins, period, usd_per_eur, split=BENCHMARK_SPLIT):
    """Every range case per airline: gross, recovered and net at the printed rate, and net at 50%.

    Output: {airline: [{"case", "gross", "recapture", "recovered", "net", "net_at_low"}]} in EUR.
    """
    market = benchmark_market(split, usd_per_eur)
    out = {}
    for airline in AIRLINES:
        rows = []
        for case in cases_for(airline, period):
            inputs = case_inputs(twins, airline, period, case, market)
            gross = gross_fuel_cost_eur(inputs, market)
            r = inputs["recapture"]
            rows.append({"case": case, "gross": gross, "recapture": r, "recovered": r * gross,
                         "net": (1 - r) * gross, "net_at_low": (1 - min(RECAPTURE_LOW, r)) * gross})
        out[airline] = rows
    return out


def summary(rows, key):
    """(min, max) of one quantity over an airline's cases."""
    values = [r[key] for r in rows]
    return min(values), max(values)


def size_neutral(twins, airline, gross_low, gross_high):
    """Gross cost as % of FY2025 operating costs and in euro cents per FY2025 seat-km (low, high)."""
    opex = get_model_value(twins, airline, "operating_costs_fy25")
    ask = get_model_value(twins, airline, "ask_fy25")
    return {"pct_opex": (gross_low / opex, gross_high / opex) if opex else None,
            "cents_per_ask": (gross_low / ask * 100, gross_high / ask * 100) if ask else None}
