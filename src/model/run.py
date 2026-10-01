"""Assemble model inputs from the twins and run the model for every airline, period and range case.

This is the only place where twins values meet the model. Everything is labelled:
  - company inputs come from data/airlines.yaml (converted by get_model_value)
  - prices: LIVE (FRED + ECB, moves since 27 Jul 2026) when the feeds work, otherwise a
    labelled illustrative SCENARIO
  - range cases: undisclosed instrument mix for the peers (A5), Lufthansa FY27 hedge cover (A2),
    Lufthansa FY26 company-table exposures (A24)

Periods (06_METHODOLOGY.md section 4):
  FY2026, live mode:     realised months (27 Jul -> latest price date, monthly average moves)
                         + remaining quarters (after the latest price date, latest move)
  FY2026, scenario mode: remaining part of the year after the as-of date, scenario move
  FY2027:                full year, volume = FY26 volume (A10), latest/scenario move as a
                         parallel shift (A14)
Each period is a list of segments (volume, hedge ratio, move); the chain runs exactly per segment.
The driver waterfall uses volume-weighted aggregates and one common move per period
(attribution only - a stated approximation).
"""
from dataclasses import dataclass
from datetime import date
from itertools import product

from src.model.decomposition import robust_driver, waterfall
from src.model.fuel import fuel_cost_change_usd, unprotected_shares, usd_to_eur
from src.model.guidance import (
    change_as_share, competitive_gap, favourability, guidance_shift, is_material,
    select_baseline_eps,
)
from src.model.income import income_chain
from src.model.periods import (
    monthly_volume, quarter_volumes, realised_month_fractions, remaining_quarter_shares,
)
from src.twins import get_model_value
from src.validation import remaining_share, table_implied_exposures

US = "lufthansa"
PEERS = ("afklm", "iag")
AIRLINES = (US,) + PEERS
PERIODS = ("FY2026", "FY2027")
BASELINE_DAY = date(2026, 7, 27)

# Undisclosed hedge-book mix (A5). "central" = midpoint of the two bounds (same as 50/50).
PEER_MIX_CASES = {
    "jet-equivalent": {"jet": 1.0},
    "central": {"brent": 0.5, "jet": 0.5},
    "crude-only": {"brent": 1.0},
}


@dataclass(frozen=True)
class Scenario:
    """A fixed price move versus the 27 Jul 2026 baseline, in USD per tonne, plus FX and g."""
    d_brent: float = 40.0
    d_crack: float = 60.0
    usd_per_eur: float = 1.151
    g: float = 0.8
    label: str = ("Illustrative scenario: jet fuel +USD 100/t vs 27 Jul 2026 (+40 Brent, +60 crack); "
                  "USD/EUR 1.151 (Lufthansa's printed planning rate); g = 0.8. Not live prices.")


def market_from(scenario, live=None, as_of=None):
    """One description of prices for the run: live if the feeds worked, else the scenario."""
    if live and live.get("ok"):
        m = live["moves"]
        return {"mode": "live", "d_brent": m["d_brent"], "d_crack": m["d_crack"],
                "monthly": live["monthly"], "split_day": m["latest_day"],
                "usd_per_eur": live["fx"].data, "g": scenario.g,
                "label": (f"Live prices: moves since {m['baseline_day']:%d %b %Y} to {m['latest_day']:%d %b %Y} "
                          f"(FRED US Gulf Coast jet and Brent, converted at 7.9 bbl/t); jet "
                          f"{m['d_jet']:+.0f} USD/t (Brent {m['d_brent']:+.0f}, crack {m['d_crack']:+.0f}); "
                          f"USD/EUR {live['fx'].data:.4f} (ECB, {live['fx'].as_of:%d %b %Y}); g = {scenario.g}.")}
    return {"mode": "scenario", "d_brent": scenario.d_brent, "d_crack": scenario.d_crack, "monthly": {},
            "split_day": as_of or date.today(), "usd_per_eur": scenario.usd_per_eur, "g": scenario.g,
            "label": scenario.label}


def period_label(market, period):
    if period == "FY2027":
        return "FY2027"
    if market["mode"] == "live":
        return f"FY2026 since 27 Jul (realised to {market['split_day']:%d %b} + remaining)"
    return f"FY2026 remaining (after {market['split_day']:%d %b %Y})"


def _v(twins, airline, field):
    return get_model_value(twins, airline, field)


def _lufthansa_mix(twins):
    """Lufthansa's printed hedge-book split (slide 17 fn 2): gasoil 48/81, Brent 33/81, jet 0."""
    parts = {k: _v(twins, US, f"hedge_mix_{k}") for k in ("brent", "gasoil", "jet")}
    total = sum(parts.values())
    return {k: v / total for k, v in parts.items()}


def cases_for(airline, period):
    """Names of the range cases for one airline and period."""
    if airline == US:
        return ("stale 29%", "reported ~50%") if period == "FY2027" else ("base", "company table")
    return tuple(PEER_MIX_CASES)


def _fy26_ratios(twins, airline):
    """Hedge ratio per quarter for the rest of FY26: LH one year-to-go ratio; peers per quarter."""
    rest = _v(twins, airline, "hedge_ratio_rest_fy26")
    if rest is not None:
        return {3: rest, 4: rest}
    return {3: _v(twins, airline, "hedge_ratio_q3_26"), 4: _v(twins, airline, "hedge_ratio_q4_26")}


def _segments(twins, airline, period, case, market):
    """List of {volume_t, hedge_ratio, d_brent, d_crack} for one airline, period and case."""
    fy_volume = _v(twins, airline, "fuel_volume_fy26")
    if period == "FY2027":
        if airline == US:
            ratio = _v(twins, US, "hedge_ratio_fy27" if case == "stale 29%" else "hedge_ratio_fy27_upper")
        else:
            ratio = _v(twins, airline, "hedge_ratio_fy27")
        return [{"volume_t": fy_volume, "hedge_ratio": ratio,
                 "d_brent": market["d_brent"], "d_crack": market["d_crack"]}]

    printed = {q: _v(twins, airline, f"fuel_volume_q{q}_26") for q in (3, 4)}      # printed or capacity-derived
    vols = quarter_volumes(fy_volume, {q: v for q, v in printed.items() if v is not None})
    ratios = _fy26_ratios(twins, airline)
    segments = []
    if market["mode"] == "live":
        for (_, month), fraction in realised_month_fractions(BASELINE_DAY, market["split_day"]).items():
            move = market["monthly"].get((2026, month), market)
            segments.append({"volume_t": monthly_volume(vols, month) * fraction,
                             "hedge_ratio": ratios[(month - 1) // 3 + 1],
                             "d_brent": move["d_brent"], "d_crack": move["d_crack"]})
    for quarter, share in remaining_quarter_shares(market["split_day"], 2026).items():
        if share > 0:
            segments.append({"volume_t": vols[quarter] * share, "hedge_ratio": ratios[quarter],
                             "d_brent": market["d_brent"], "d_crack": market["d_crack"]})
    return segments


def build_inputs(twins, airline, period, case, market):
    """Model inputs for one airline, period and case: segments plus volume-weighted aggregates."""
    segments = _segments(twins, airline, period, case, market)
    total = sum(s["volume_t"] for s in segments)

    def weighted(key):
        return sum(s["volume_t"] * s[key] for s in segments) / total if total else 0.0

    consensus_field = "consensus_eps_fy27" if period == "FY2027" else "consensus_eps_fy26"
    baseline, baseline_source = select_baseline_eps(_v(twins, airline, consensus_field),
                                                    _v(twins, airline, "eps_fy25"))
    override = None
    if airline == US and case == "company table":
        override = table_implied_exposures(
            remaining_share(_v(twins, US, "fuel_volume_fy26"), _v(twins, US, "fuel_volume_q3_26")),
            brent_up=market["d_brent"] >= 0, crack_up=market["d_crack"] >= 0)
    return {
        "segments": segments, "volume_t": total, "hedge_ratio": weighted("hedge_ratio"),
        "d_brent": weighted("d_brent"), "d_crack": weighted("d_crack"),
        "mix": _lufthansa_mix(twins) if airline == US else PEER_MIX_CASES[case],
        "recapture": _v(twins, airline, "recapture_rate"), "tax": _v(twins, airline, "tax_rate_marginal"),
        "minority": _v(twins, airline, "minority_share"), "shares": _v(twins, airline, "diluted_shares"),
        "baseline_eps": baseline, "baseline_source": baseline_source, "u_override": override,
    }


def _unprotected(inputs, hedge_ratio, g):
    if inputs.get("u_override"):
        return inputs["u_override"]["u_brent"], inputs["u_override"]["u_crack"]
    mix = inputs["mix"]
    return unprotected_shares(hedge_ratio * mix.get("brent", 0), hedge_ratio * mix.get("gasoil", 0),
                              hedge_ratio * mix.get("jet", 0), g)


def run_case(inputs, market):
    """Exact chain over all segments: hedges -> fuel -> EBIT -> NI -> EPS, plus protection."""
    d_fuel_usd, full_move_usd = 0.0, 0.0
    for s in inputs["segments"]:
        u_b, u_c = _unprotected(inputs, s["hedge_ratio"], market["g"])
        d_fuel_usd += fuel_cost_change_usd(s["volume_t"], u_b, u_c, s["d_brent"], s["d_crack"])
        full_move_usd += s["volume_t"] * (s["d_brent"] + s["d_crack"])
    chain = income_chain(usd_to_eur(d_fuel_usd, market["usd_per_eur"]), inputs["recapture"],
                         inputs["tax"], inputs["minority"], inputs["shares"])
    chain.update({
        "volume_t": inputs["volume_t"], "hedge_ratio": inputs["hedge_ratio"],
        "effective_protection": (1 - d_fuel_usd / full_move_usd) if full_move_usd else None,
        "d_eps_share": change_as_share(chain["d_eps"], inputs["baseline_eps"]),
        "baseline_eps": inputs["baseline_eps"], "baseline_source": inputs["baseline_source"],
        "segments": len(inputs["segments"]),
    })
    return chain


def run_all(twins, scenario=Scenario(), live=None, as_of=None):
    """Run every airline x period x case. Returns results, summaries, market and period labels."""
    market = market_from(scenario, live, as_of)
    results = {p: {a: {c: run_case(build_inputs(twins, a, p, c, market), market) for c in cases_for(a, p)}
                   for a in AIRLINES} for p in PERIODS}
    summary = {p: {a: summarise(twins, a, p, results[p][a]) for a in AIRLINES} for p in PERIODS}
    for p in PERIODS:
        for peer in PEERS:
            summary[p][peer].update(peer_comparison(twins, p, peer, market))
    return {"market": market, "as_of": market["split_day"], "results": results, "summary": summary,
            "period_labels": {p: period_label(market, p) for p in PERIODS}}


def summarise(twins, airline, period, cases):
    """Central value and range for one airline/period, plus flags."""
    shares = [r["d_eps_share"] for r in cases.values()]
    central_case = next((c for c in ("central", "base") if c in cases), next(iter(cases)))
    central = cases[central_case] if (airline != US or period != "FY2027") else None
    reference = get_model_value(twins, airline, "adj_operating_profit_fy25")
    ebit_shares = [change_as_share(r["d_ebit"], reference) for r in cases.values()]
    return {
        "central": central,
        "range_eps_share": (min(shares), max(shares)) if None not in shares else None,
        "range_d_eps": (min(r["d_eps"] for r in cases.values()), max(r["d_eps"] for r in cases.values())),
        "favourability": favourability(sum(r["d_eps"] for r in cases.values())),
        "material": _all_some_none([is_material(e, s) for e, s in zip(ebit_shares, shares)]),
        "range_ebit_share": (min(ebit_shares), max(ebit_shares)) if None not in ebit_shares else None,
        "guidance": guidance_position(twins, airline, period, cases),
    }


def guidance_position(twins, airline, period, cases):
    """Position within printed guidance (FY2026 only; context). None where not applicable."""
    if period != "FY2026":
        return None
    low, high = get_model_value(twins, airline, "guidance_low"), get_model_value(twins, airline, "guidance_high")
    if low is None or high is None:
        return None
    d_ebits = [r["d_ebit"] for r in cases.values()]
    if airline == "iag":  # margin guidance: dEBIT / consensus FY26 revenue (A22)
        revenue = get_model_value(twins, airline, "consensus_revenue_fy26")
        changes = [d / revenue for d in d_ebits]
    else:
        changes = d_ebits
    positions = [guidance_shift(low, high, c) for c in changes]
    return {"low": low, "high": high, "unit": "margin" if airline == "iag" else "EUR",
            "change_range": (min(changes), max(changes)),
            "labels": sorted({p[2] for p in positions}),
            "position_range": (min(p[1] for p in positions), max(p[1] for p in positions))}


def peer_comparison(twins, period, peer, market):
    """Competitive gap vs Lufthansa (ours - peer's) and robust main driver across all range cases.

    The waterfall uses each input set's volume-weighted aggregates and ONE common move per period
    (Lufthansa's weighted move), so that bars reflect airline differences, not price timing.
    """
    gaps, waterfalls = [], []
    for oc, pc in product(cases_for(US, period), cases_for(peer, period)):
        ours = build_inputs(twins, US, period, oc, market)
        theirs = build_inputs(twins, peer, period, pc, market)
        w = waterfall(ours, theirs, ours["d_brent"], ours["d_crack"], market["usd_per_eur"], market["g"])
        waterfalls.append(w)
        gaps.append(competitive_gap(run_case(theirs, market)["d_eps_share"],
                                    run_case(ours, market)["d_eps_share"]))
    return {"gap_range": (min(gaps), max(gaps)), "driver_vs_us": robust_driver(waterfalls)}


def _meaningful_shares(results_for_period):
    """[(airline, dEPS %)] per airline, or None if any case has no meaningful % (then no ranking)."""
    per_airline = [[(a, r["d_eps_share"]) for r in results_for_period[a].values()] for a in AIRLINES]
    if any(share is None for cases in per_airline for _, share in cases):
        return None
    return per_airline


def _all_some_none(flags):
    """'yes' if every case is True, 'no' if none, 'depends on range' otherwise."""
    if all(flags):
        return "yes"
    if not any(flags):
        return "no"
    return "depends on range"


def robust_extremes(results_for_period):
    """(most hurt, least hurt) airline, each None if it changes somewhere in the ranges."""
    most, least = set(), set()
    per_airline = _meaningful_shares(results_for_period)
    if per_airline is None:
        return None, None
    for combo in product(*per_airline):
        ordered = sorted(combo, key=lambda x: x[1])
        most.add(ordered[0][0])
        least.add(ordered[-1][0])
    return (most.pop() if len(most) == 1 else None, least.pop() if len(least) == 1 else None)


def ranking_is_robust(results_for_period):
    """Order of airlines from most to least hurt (dEPS %), if identical in every case combination."""
    per_airline = _meaningful_shares(results_for_period)
    if per_airline is None:
        return None
    orders = set()
    for combo in product(*per_airline):
        orders.add(tuple(a for a, _ in sorted(combo, key=lambda x: x[1])))
    return orders.pop() if len(orders) == 1 else None
