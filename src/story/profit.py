"""Step 6: what the net cost does to profit and ratios - operating profit, operating margin, net income, EPS.

Bottom-up from Steps 4-5, through the model's own income chain (src/model/income.py), per airline, period and case:
  operating profit change = -net cost                        (Step 5; = the hero's euro figure for 2027)
  revenue change          = recovered through fares          (Step 5; pass-through raises revenue)
  margin after            = (expected op. profit - net) / (expected revenue + recovered)
  net income change       = op. profit change x (1 - marginal tax) x (1 - minorities)
  EPS change              = net income change / diluted shares;  % of consensus EPS (MarketScreener)
Expected operating profit and revenue: same hierarchy as the hero (src/story/yardstick.py, A26, A31).
"""
from src.model.income import income_chain
from src.model.run import AIRLINES, build_inputs
from src.story.costs import cost_cases
from src.story.robustness import BENCHMARK_SPLIT, benchmark_market
from src.story.yardstick import expected_operating_profit, expected_revenue


def profit_cases(twins, period, usd_per_eur, split=BENCHMARK_SPLIT):
    """Every case per airline. Output: {airline: [{"case", "net", "d_ebit", "d_revenue", "d_net_income", "d_eps",
    "op_before", "op_after", "op_share", "rev_before", "margin_before", "margin_after", "margin_pp",
    "eps_before", "eps_after", "eps_share", "eps_source", "tax", "minority", "shares"}]}."""
    costs = cost_cases(twins, period, usd_per_eur, split)
    market = benchmark_market(split, usd_per_eur)
    out = {}
    for airline in AIRLINES:
        op = expected_operating_profit(twins, airline, period)["value"]
        rev = expected_revenue(twins, airline, period)["value"]
        rows = []
        for c in costs[airline]:
            inputs = build_inputs(twins, airline, period, c["case"], market)
            chain = income_chain(c["gross"], c["recapture"], inputs["tax"], inputs["minority"], inputs["shares"])
            eps = inputs["baseline_eps"]
            margin_before = op / rev
            margin_after = (op + chain["d_ebit"]) / (rev + chain["d_revenue"])
            rows.append({
                "case": c["case"], "net": c["net"], "d_ebit": chain["d_ebit"], "d_revenue": chain["d_revenue"],
                "d_net_income": chain["d_net_income"], "d_eps": chain["d_eps"],
                "op_before": op, "op_after": op + chain["d_ebit"], "op_share": chain["d_ebit"] / op,
                "rev_before": rev, "margin_before": margin_before, "margin_after": margin_after,
                "margin_pp": margin_after - margin_before,
                "eps_before": eps, "eps_after": eps + chain["d_eps"] if eps else None,
                "eps_share": chain["d_eps"] / eps if eps and eps > 0 else None,
                "eps_source": inputs["baseline_source"],
                "tax": inputs["tax"], "minority": inputs["minority"], "shares": inputs["shares"]})
        out[airline] = rows
    return out


def span(rows, key):
    """(min, max) over cases, ignoring None."""
    values = [r[key] for r in rows if r[key] is not None]
    return (min(values), max(values)) if values else None
