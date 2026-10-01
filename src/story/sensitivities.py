"""Numbers for the 'so what' cards (Step 8) - each one from the same model functions as Steps 4-7.

  margin_multiplier   how many times IAG's profit hit a similar margin loss means for Lufthansa (Step 6 rows)
  pass_through        Lufthansa 2027 net cost change per 10 pp of pass-through = 0.10 x gross (Step 4-5 chain:
                      net = (1 - r) x gross, so d net / d r = -gross); and the change at Air France-KLM's printed rate
  hedge_cover         Lufthansa 2027 net cost at 29% minus at ~50% hedge cover (the two Step 4-5 cases)
  hedge_quality_swing largest effect of the peers' undisclosed hedge mix on the gap (attribution, A29), in pp
"""
from src.model.run import PEERS, US
from src.story.costs import cost_cases
from src.story.profit import profit_cases
from src.story.robustness import BENCHMARK_SPLIT, attribution
from src.story.yardstick import expected_operating_profit
from src.twins import get_model_value

STEP_PP = 0.10


def margin_multiplier(twins, usd_per_eur, split=BENCHMARK_SPLIT, peer="iag"):
    """Expected 2027 margins and the ratio of profit hits (Lufthansa's % / the peer's %), over all case pairs."""
    p27 = profit_cases(twins, "FY2027", usd_per_eur, split)
    ratios = [l_row["op_share"] / p_row["op_share"] for l_row in p27[US] for p_row in p27[peer]]
    return {"margin_us": p27[US][0]["margin_before"], "margin_peer": p27[peer][0]["margin_before"],
            "ratio": (min(ratios), max(ratios)), "peer": peer}


def pass_through(twins, usd_per_eur, split=BENCHMARK_SPLIT, step=STEP_PP, reference_peer="afklm"):
    """Lufthansa 2027: net cost change per `step` of pass-through, and at the reference peer's printed rate.

    Output: {"per_step": (low, high) EUR, "per_step_share": (low, high) of expected op. profit,
             "at_peer_rate": (low, high) EUR lower net cost, "peer_rate", "own_rate"}.
    """
    rows = cost_cases(twins, "FY2027", usd_per_eur, split)[US]
    base = expected_operating_profit(twins, US, "FY2027")["value"]
    own, peer_rate = rows[0]["recapture"], get_model_value(twins, reference_peer, "recapture_rate")
    per_step = sorted(step * r["gross"] for r in rows)
    at_peer = sorted((peer_rate - own) * r["gross"] for r in rows)
    return {"per_step": (per_step[0], per_step[-1]), "per_step_share": (per_step[0] / base, per_step[-1] / base),
            "at_peer_rate": (at_peer[0], at_peer[-1]), "peer_rate": peer_rate, "own_rate": own, "step": step}


def hedge_cover(twins, usd_per_eur, split=BENCHMARK_SPLIT):
    """Lufthansa 2027 net cost at 29% (printed) minus at ~50% (reported) hedge cover, EUR and % of expected profit."""
    rows = {r["case"]: r for r in cost_cases(twins, "FY2027", usd_per_eur, split)[US]}
    diff = rows["stale 29%"]["net"] - rows["reported ~50%"]["net"]
    base = expected_operating_profit(twins, US, "FY2027")["value"]
    return {"net_difference": diff, "share": diff / base,
            "gross_difference": rows["stale 29%"]["gross"] - rows["reported ~50%"]["gross"]}


def hedge_quality_swing(twins, usd_per_eur, split=BENCHMARK_SPLIT):
    """Range of the hedge-quality part of the gap (pp of expected profit) over both peers and all cases."""
    parts = [r["parts"]["hedge quality"] for p in PEERS for r in attribution(twins, "FY2027", p, usd_per_eur, split)]
    return {"low": min(parts), "high": max(parts), "max_abs": max(abs(x) for x in parts)}
