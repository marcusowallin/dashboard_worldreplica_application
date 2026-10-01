"""Hero robustness: operating-profit impact of the USD 100/t benchmark across every uncertain input.

X (DESIGN_BRIEF.md section 6) = operating-profit change from a jet fuel move, as a share of the operating
profit expected for the same year (src/story/yardstick.py). Reported here as a positive LOSS share
(0.12 = the move costs 12% of expected operating profit).

Grid (decision 30 Sep 2026):
  split       Brent/crack split of the USD 100/t move, all-Brent to all-crack (market-wide, common to all)
  hedge case  Lufthansa: FY2027 cover 29% / ~50% (A2), FY2026 swap model / company table (A24);
              peers: hedge mix jet-equivalent / central / crude-only (A5)
  recapture   each airline from 50% up to its printed rate (A25)
  profit base yardstick low / high where a range is printed (LH FY26 guidance, IAG FY26 margin)
Every input except the split is airline-specific and independent, so "Lufthansa is hit hardest in
every combination" holds exactly when, for every split, Lufthansa's smallest loss exceeds each
peer's largest loss.

Attribution of the gap (Lufthansa loss - peer loss): Shapley values over four factor groups -
hedge ratio, hedge quality, recapture, profit base - i.e. the average of the one-at-a-time swap from
Lufthansa's inputs to the peer's over every possible swap order. Order-independent (unlike the
fixed-order waterfall, A23) and the four parts add up exactly to the gap.
"""
from itertools import combinations, product
from math import factorial

from src.model.fuel import fuel_cost_change_usd, unprotected_shares, usd_to_eur
from src.model.run import AIRLINES, PEERS, US, Scenario, build_inputs, cases_for, market_from
from src.story.yardstick import expected_operating_profit
from src.twins import get_model_value

BENCHMARK_USD_PER_T = 100.0
BENCHMARK_SPLIT = (50.0, 50.0)                       # neutral split, labelled assumption A28 (decision 1 Oct 2026)
SPLITS = tuple((b, BENCHMARK_USD_PER_T - b) for b in (100.0, 80.0, 60.0, 50.0, 40.0, 20.0, 0.0))
RECAPTURE_LOW = 0.50                                 # A25: lower end of the recapture range

FACTORS = {
    "hedge ratio": ("hedge_ratio",),
    "hedge quality": ("mix", "u_override"),
    "recapture": ("recapture",),
    "profit base": ("volume_t", "base"),
}


def benchmark_market(split, usd_per_eur):
    """Scenario market for one Brent/crack split of the benchmark move."""
    return market_from(Scenario(d_brent=split[0], d_crack=split[1], usd_per_eur=usd_per_eur))


def case_inputs(twins, airline, period, case, market, recapture=None, base=None):
    """Aggregated one-segment inputs for the loss share (exact for a uniform scenario move).

    Fuel cost is linear in the hedge ratio, so the volume-weighted ratio reproduces the per-segment
    result when every segment has the same move (always true for the benchmark).
    """
    inputs = build_inputs(twins, airline, period, case, market)
    return {"volume_t": inputs["volume_t"], "hedge_ratio": inputs["hedge_ratio"], "mix": inputs["mix"],
            "u_override": inputs["u_override"],
            "recapture": inputs["recapture"] if recapture is None else recapture,
            "base": expected_operating_profit(twins, airline, period)["value"] if base is None else base}


def gross_fuel_cost_eur(inputs, market):
    """Extra fuel cost in EUR after hedging, before any pass-through (the 'gross' cost of Steps 4-5)."""
    if inputs["u_override"]:
        u_b, u_c = inputs["u_override"]["u_brent"], inputs["u_override"]["u_crack"]
    else:
        h, mix = inputs["hedge_ratio"], inputs["mix"]
        u_b, u_c = unprotected_shares(h * mix.get("brent", 0), h * mix.get("gasoil", 0),
                                      h * mix.get("jet", 0), market["g"])
    return usd_to_eur(fuel_cost_change_usd(inputs["volume_t"], u_b, u_c, market["d_brent"], market["d_crack"]),
                      market["usd_per_eur"])


def loss_share(inputs, market):
    """Operating-profit loss as a share of the yardstick: (1 - r) x extra fuel cost (EUR) / base."""
    return (1 - inputs["recapture"]) * gross_fuel_cost_eur(inputs, market) / inputs["base"]


def direction(market):
    """+1 for a rise in jet fuel, -1 for a fall. Losses below are MAGNITUDES (a fall's gain counts like a rise's loss),
    so rankings, ranges and attributions read the same way; the wording decides 'costs' or 'saves'."""
    return -1.0 if market["d_brent"] + market["d_crack"] < 0 else 1.0


def recapture_range(twins, airline):
    """(low, high): 50% up to the printed rate (A25). Never above the printed rate."""
    printed = get_model_value(twins, airline, "recapture_rate")
    return (min(RECAPTURE_LOW, printed), printed)


def airline_losses(twins, airline, period, market):
    """Every combination for one airline: list of (label dict, loss share)."""
    yardstick = expected_operating_profit(twins, airline, period)
    bases = sorted({yardstick["low"], yardstick["high"]})
    out = []
    for case, recapture, base in product(cases_for(airline, period), recapture_range(twins, airline), bases):
        inputs = case_inputs(twins, airline, period, case, market, recapture, base)
        out.append(({"case": case, "recapture": recapture, "base": base}, direction(market) * loss_share(inputs, market)))
    return out


def ranking_grid(twins, period, usd_per_eur, splits=SPLITS):
    """For each split: loss range per airline, whether Lufthansa is hit hardest in every combination,
    and the share of joint combinations in which it is.

    Output: list of {"split", "ranges": {airline: (min, max)}, "holds": bool, "share_lh_hardest": float}.
    """
    rows = []
    for split in splits:
        market = benchmark_market(split, usd_per_eur)
        losses = {a: [loss for _, loss in airline_losses(twins, a, period, market)] for a in AIRLINES}
        lh = losses[US]
        hardest = sum(sum(1 for x in losses[PEERS[0]] if x < v) * sum(1 for x in losses[PEERS[1]] if x < v)
                      for v in lh)
        total = len(lh) * len(losses[PEERS[0]]) * len(losses[PEERS[1]])
        rows.append({"split": split, "ranges": {a: (min(v), max(v)) for a, v in losses.items()},
                     "holds": min(lh) > max(max(losses[p]) for p in PEERS),
                     "share_lh_hardest": hardest / total})
    return rows


def break_even_recapture(twins, period, peer, usd_per_eur, split=BENCHMARK_SPLIT):
    """Recapture below which the peer's worst hedge/base case loses more than Lufthansa's best case.

    Loss is proportional to (1 - r), so r* = 1 - (Lufthansa's smallest loss) / (peer's loss at r = 0).
    Output: r* as a fraction (can be negative: then no recapture level flips the ranking).
    """
    market = benchmark_market(split, usd_per_eur)
    lh_best = min(loss for _, loss in airline_losses(twins, US, period, market))
    peer_worst_at_zero = max(
        direction(market) * loss_share(case_inputs(twins, peer, period, case, market, 0.0, base), market)
        for case in cases_for(peer, period)
        for base in {expected_operating_profit(twins, peer, period)[k] for k in ("low", "high")})
    return 1 - lh_best / peer_worst_at_zero


def shapley_gap(ours, peer, market):
    """Split (our loss - peer loss) into the four FACTORS; the parts add up exactly to the gap.

    Output: {"gap": float, "parts": {factor: contribution}}; positive = the factor makes us lose more.
    """
    names = list(FACTORS)
    n = len(names)

    def value(swapped):
        mixed = dict(ours)
        for name in swapped:
            for key in FACTORS[name]:
                mixed[key] = peer.get(key)
        return direction(market) * loss_share(mixed, market)

    parts = {}
    for name in names:
        others = [x for x in names if x != name]
        total = 0.0
        for size in range(n):
            weight = factorial(size) * factorial(n - size - 1) / factorial(n)
            for subset in combinations(others, size):
                total += weight * (value(subset + (name,)) - value(subset))
        parts[name] = -total          # swapping towards the peer lowers our loss by what we "owe" to it
    return {"gap": direction(market) * (loss_share(ours, market) - loss_share(peer, market)), "parts": parts}


def attribution(twins, period, peer, usd_per_eur, split=BENCHMARK_SPLIT):
    """Shapley parts for every combination of range cases (recapture at printed rates).

    Output: list of {"lh_case", "peer_case", "gap", "parts"}.
    """
    market = benchmark_market(split, usd_per_eur)
    rows = []
    for lh_case, peer_case in product(cases_for(US, period), cases_for(peer, period)):
        result = shapley_gap(case_inputs(twins, US, period, lh_case, market),
                             case_inputs(twins, peer, period, peer_case, market), market)
        rows.append({"lh_case": lh_case, "peer_case": peer_case, **result})
    return rows


def loss_ranges(twins, period, usd_per_eur, split=BENCHMARK_SPLIT):
    """Hero ranges per airline for a scenario move, at the printed recapture, plus the wider end.

    Output: {airline: {"low", "high" (loss as a fraction of expected operating profit, printed recapture),
                       "cost_low", "cost_high" (net cost in EUR after hedging and pass-through = loss x base),
                       "ext_high" (largest loss with recapture down to 50%)}}.
    """
    market = benchmark_market(split, usd_per_eur)
    out = {}
    for airline in AIRLINES:
        losses = airline_losses(twins, airline, period, market)
        printed = recapture_range(twins, airline)[1]
        at_printed = [(label, loss) for label, loss in losses if label["recapture"] == printed]
        costs = [loss * label["base"] for label, loss in at_printed]          # magnitudes (see direction)
        out[airline] = {"low": min(loss for _, loss in at_printed), "high": max(loss for _, loss in at_printed),
                        "cost_low": min(costs), "cost_high": max(costs),
                        "ext_high": max(loss for _, loss in losses)}
    return out
