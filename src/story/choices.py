"""Choices that can move the answer more than any single input (design review, 2 Oct 2026).

The story's headline uses one reading of three things that the companies do not settle. Each is computed here with the
same building blocks as the hero (case_inputs, gross_fuel_cost_eur, loss_share), so the base case reproduces the hero:

  persistence        How much of today's shock is still there in 2027? The page applies the whole move to 2027 (A14) but
                     the forward curves slope down. The model is linear in the move, so a fraction p of the shock
                     scales every loss by p: the LEVELS change, the ORDER does not.
  pass-through base  The companies print "we recover about 60% of the higher fuel cost". The page reads that as 60% of
                     the cost they pay AFTER hedging (A19). If it meant 60% of the MARKET price rise, an airline that
                     hedged would recover more than it lost: Air France-KLM would gain. The reading decides the sign.
  Lufthansa's range  Its 2027 hedge mix is not printed (the FY26 split is borrowed, A3) and its hedges are options, which
                     protect less than swaps as prices rise (its own table, validation T2). Add-on cases: all-Brent,
                     all-gasoil, and an "options fade" that scales the swap protection by what Lufthansa's FY26 table
                     implies (A36).
Plus: net cost per tonne (a size-neutral view) and the price move on five-day averages (the single-day 27 July print is a
local high).
All losses are MAGNITUDES (a fall in price mirrors a rise); sign words are the caller's.
"""
from src.data_sources import moves_since_baseline
from src.model.fuel import unprotected_shares
from src.model.run import AIRLINES, BASELINE_DAY, PEERS, US, _lufthansa_mix, cases_for
from src.story.price_split import smooth
from src.story.robustness import (
    BENCHMARK_SPLIT, benchmark_market, case_inputs, direction, gross_fuel_cost_eur, loss_ranges, loss_share,
)
from src.twins import get_model_value
from src.validation import remaining_share, table_implied_exposures

PERSISTENCE_SHARES = (1.0, 0.75, 0.5)
LH_VARIANTS = ("printed mix", "all Brent hedges", "all gasoil hedges", "options fade")


def _scaled(split, p):
    return (split[0] * p, split[1] * p)


def persistence_table(twins, usd_per_eur, split=BENCHMARK_SPLIT, shares=PERSISTENCE_SHARES):
    """Loss ranges for FY2027 when only a share p of the shock persists. Output: list of
    {"share", "ranges": {airline: {"low", "high" (fractions of expected profit), "cost_low", "cost_high" (EUR)}},
     "lufthansa_hardest": bool}."""
    rows = []
    for p in shares:
        r = loss_ranges(twins, "FY2027", usd_per_eur, _scaled(split, p))
        rows.append({"share": p, "ranges": r, "lufthansa_hardest": r[US]["low"] > max(r[q]["high"] for q in PEERS)})
    return rows


def options_fade_factors(twins, market):
    """(f_brent, f_crack): the share of the SWAP model's protection that Lufthansa's own FY26 sensitivity table implies.

    The swap model says 19% of FY26 fuel is unprotected against Brent (A1); the table implies far more (A24). The ratio of
    protected shares, table / swap, is the fade. It is derived from printed figures; applying it to FY2027 assumes the
    2027 hedge book is built like the 2026 one (A36).
    """
    share = remaining_share(get_model_value(twins, US, "fuel_volume_fy26"), get_model_value(twins, US, "fuel_volume_q3_26"))
    table = table_implied_exposures(share, brent_up=market["d_brent"] >= 0, crack_up=market["d_crack"] >= 0)
    h, mix = get_model_value(twins, US, "hedge_ratio_rest_fy26"), _lufthansa_mix(twins)
    u_b, u_c = unprotected_shares(h * mix["brent"], h * mix["gasoil"], h * mix["jet"], market["g"])
    f_b = max(0.0, min(1.0, (1 - table["u_brent"]) / (1 - u_b)))
    f_c = max(0.0, min(1.0, (1 - table["u_crack"]) / (1 - u_c)))
    return f_b, f_c


def lufthansa_variant(twins, inputs, market, variant):
    """A copy of Lufthansa's FY2027 case inputs under one add-on variant (see LH_VARIANTS)."""
    out = dict(inputs)
    h = inputs["hedge_ratio"]
    if variant == "printed mix":
        return out
    if variant == "all Brent hedges":
        out["mix"] = {"brent": 1.0}
    elif variant == "all gasoil hedges":
        out["mix"] = {"gasoil": 1.0}
    elif variant == "options fade":
        mix = inputs["mix"]
        u_b, u_c = unprotected_shares(h * mix.get("brent", 0), h * mix.get("gasoil", 0), h * mix.get("jet", 0), market["g"])
        f_b, f_c = options_fade_factors(twins, market)
        out["u_override"] = {"u_brent": 1 - f_b * (1 - u_b), "u_crack": 1 - f_c * (1 - u_c)}
    else:
        raise ValueError(f"unknown Lufthansa variant: {variant}")
    return out


def lufthansa_range(twins, usd_per_eur, split=BENCHMARK_SPLIT):
    """Lufthansa's 2027 loss under each add-on variant, over its two hedge-cover cases, at the printed pass-through.

    Output: {"variants": [{"name", "low", "high" (fractions), "cost_low", "cost_high" (EUR)}],
             "full": {"low", "high", "cost_low", "cost_high"}, "fade": (f_brent, f_crack)}.
    """
    market = benchmark_market(split, usd_per_eur)
    rows = []
    for name in LH_VARIANTS:
        losses = []
        for case in cases_for(US, "FY2027"):
            inputs = lufthansa_variant(twins, case_inputs(twins, US, "FY2027", case, market), market, name)
            losses.append(direction(market) * loss_share(inputs, market))
        base = case_inputs(twins, US, "FY2027", cases_for(US, "FY2027")[0], market)["base"]
        rows.append({"name": name, "low": min(losses), "high": max(losses),
                     "cost_low": min(losses) * base, "cost_high": max(losses) * base})
    full = {"low": min(r["low"] for r in rows), "high": max(r["high"] for r in rows),
            "cost_low": min(r["cost_low"] for r in rows), "cost_high": max(r["cost_high"] for r in rows)}
    return {"variants": rows, "full": full, "fade": options_fade_factors(twins, market)}


def pass_through_base(twins, usd_per_eur, split=BENCHMARK_SPLIT):
    """FY2027 net cost under the two readings of 'we recover r of the higher fuel cost'.

    model  = (1 - r) x extra fuel cost after hedging                  (the page; the companies' wording)
    market = extra fuel cost after hedging - r x volume x market move  (r applied to the whole price rise)
    Output: {airline: {"model": (low, high), "market": (low, high), "share_model", "share_market" (fractions of expected
    profit), "flips": bool (the market reading turns a cost into a gain)}} in EUR; positive = cost.
    """
    market = benchmark_market(split, usd_per_eur)
    move = market["d_brent"] + market["d_crack"]
    out = {}
    for airline in AIRLINES:
        model, mkt, base = [], [], None
        for case in cases_for(airline, "FY2027"):
            inputs = case_inputs(twins, airline, "FY2027", case, market)
            gross, r = gross_fuel_cost_eur(inputs, market), inputs["recapture"]
            model.append((1 - r) * gross)
            mkt.append(gross - r * inputs["volume_t"] * move / market["usd_per_eur"])
            base = inputs["base"]
        out[airline] = {"model": (min(model), max(model)), "market": (min(mkt), max(mkt)),
                        "share_model": (min(model) / base, max(model) / base),
                        "share_market": (min(mkt) / base, max(mkt) / base),
                        "flips": min(model) > 0 > min(mkt)}
    return out


def net_cost_per_tonne(twins, usd_per_eur, split=BENCHMARK_SPLIT):
    """FY2027 net cost per tonne of fuel (EUR/t): the size-neutral exposure. Output: {airline: (low, high)}."""
    market = benchmark_market(split, usd_per_eur)
    out = {}
    for airline in AIRLINES:
        per_t = []
        for case in cases_for(airline, "FY2027"):
            inputs = case_inputs(twins, airline, "FY2027", case, market)
            per_t.append((1 - inputs["recapture"]) * gross_fuel_cost_eur(inputs, market) / inputs["volume_t"])
        out[airline] = (min(per_t), max(per_t))
    return out


def smoothed_move(prices, baseline_day=BASELINE_DAY):
    """The move since the baseline on five-day average prices at both ends, or None. The single-day 27 July print is a local
    high, so this is smaller than the headline move (data_sources.moves_since_baseline on raw prices)."""
    return moves_since_baseline(smooth(prices), baseline_day) if prices else None
