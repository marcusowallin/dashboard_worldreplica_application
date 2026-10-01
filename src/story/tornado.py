"""Step 5: what the answer rests on (what could change it) - one assumption at a time, everything else at its base value.

Metric (primary): Lufthansa's gap to the peer average = Lufthansa's loss - mean of the peers' losses, in pp of
expected 2027 operating profit (positive = Lufthansa hit harder). Second view: Lufthansa's own loss.
Losses are magnitudes (a falling price gives the same bars with 'gain' instead of 'loss').

Base case: Lufthansa 2027 hedge cover at the middle of its range, the peers' central hedge mix, the current scenario
split, printed pass-through rates, g = 0.8, the yardstick, today's USD/EUR, the twins' volumes.
Ranges (ASSUMPTIONS.md): pass-through 50% to printed per airline (A25), Lufthansa 2027 hedge cover (A2), peers' hedge
mix jet-equivalent to crude-only (A5), crude share of the move = historical middle half (A28), g 0.6-1.0 (A6),
expected profit +/-10% (A26), USD/EUR +/-5% (A16), fuel volumes +/-5% (A9/A10), the share of the shock still there in 2027
50%-100% (A14, A35), Lufthansa's hedge book all-gasoil to options-fade (A3, A36), and what pass-through is applied to:
the after-hedge cost or the market price rise (A19, A37).
Same building blocks as the hero (case_inputs, loss_share) - the base gap equals the hero's numbers at that point.
"""
from src.model.run import PEER_MIX_CASES, PEERS, US
from src.story.choices import lufthansa_variant
from src.story.robustness import RECAPTURE_LOW, benchmark_market, case_inputs, gross_fuel_cost_eur, loss_share
from src.twins import get_model_value


def _sign(split):
    return -1.0 if split[0] + split[1] < 0 else 1.0


def losses(twins, usd_per_eur, split, p):
    """Loss magnitude per airline for one parameter set p (see base_params)."""
    market = dict(benchmark_market((split[0] * p["persistence"], split[1] * p["persistence"]), usd_per_eur * p["fx_factor"]))
    market["g"] = p["g"]
    move = market["d_brent"] + market["d_crack"]
    out = {}
    for airline in (US, *PEERS):
        case = "stale 29%" if airline == US else "central"
        inputs = case_inputs(twins, airline, "FY2027", case, market, recapture=p["recapture"][airline])
        if airline == US:
            inputs["hedge_ratio"] = p["lh_hedge"]
            inputs = lufthansa_variant(twins, inputs, market, p["lh_variant"])
        else:
            inputs["mix"] = PEER_MIX_CASES[p["peer_mix"]]
        inputs["volume_t"] *= p["volume_factor"]
        inputs["base"] *= p["profit_factor"][airline]
        if p["pt_base"] == "market":              # r applied to the whole market price rise, not the after-hedge cost
            net = gross_fuel_cost_eur(inputs, market) - inputs["recapture"] * inputs["volume_t"] * move / market["usd_per_eur"]
            out[airline] = _sign(split) * net / inputs["base"]
        else:
            out[airline] = _sign(split) * loss_share(inputs, market)
    return out


def gap(loss):
    return loss[US] - sum(loss[p] for p in PEERS) / len(PEERS)


def base_params(twins):
    """The base case (middle of Lufthansa's 2027 hedge range, peers central, printed pass-through)."""
    lo = get_model_value(twins, US, "hedge_ratio_fy27")
    hi = get_model_value(twins, US, "hedge_ratio_fy27_upper")
    return {"lh_hedge": (lo + hi) / 2, "peer_mix": "central", "g": 0.8, "fx_factor": 1.0, "volume_factor": 1.0,
            "persistence": 1.0, "lh_variant": "printed mix", "pt_base": "model",
            "recapture": {a: get_model_value(twins, a, "recapture_rate") for a in (US, *PEERS)},
            "profit_factor": {a: 1.0 for a in (US, *PEERS)}}


def assumptions(twins, split_q):
    """(label, list of (end label, parameter change), key) for each assumption. split_q = (q1, q3) crude shares or None."""
    rec = {a: get_model_value(twins, a, "recapture_rate") for a in (US, *PEERS)}
    lo = get_model_value(twins, US, "hedge_ratio_fy27")
    hi = get_model_value(twins, US, "hedge_ratio_fy27_upper")
    names = {"lufthansa": "Lufthansa", "afklm": "Air France-KLM", "iag": "IAG"}
    items = []
    for a in ("afklm", US, "iag"):
        low = min(RECAPTURE_LOW, rec[a])
        items.append((f"{names[a]} pass-through {low:.0%}-{rec[a]:.0%}",
                      [(f"{low:.0%}", {"recapture": {**rec, a: low}}), (f"{rec[a]:.0%}", {"recapture": rec})], f"pt:{a}"))
    items += [
        (f"Lufthansa 2027 hedge cover {lo:.0%}-{hi:.0%}", [(f"{lo:.0%}", {"lh_hedge": lo}), (f"{hi:.0%}", {"lh_hedge": hi})],
         "lh_cover"),
        ("Peers' hedge mix: all jet to all crude", [("all jet", {"peer_mix": "jet-equivalent"}),
                                                    ("all crude", {"peer_mix": "crude-only"})], "peer_mix"),
        ("Gasoil hedges cover of the premium (g) 0.6-1.0", [("0.6", {"g": 0.6}), ("1.0", {"g": 1.0})], "g"),
        ("Lufthansa expected 2027 profit ±10%", [("-10%", {"profit_factor": {US: 0.9}}),
                                                      ("+10%", {"profit_factor": {US: 1.1}})], "lh_profit"),
        ("Peers' expected 2027 profit ±10%", [("-10%", {"profit_factor": {p: 0.9 for p in PEERS}}),
                                                   ("+10%", {"profit_factor": {p: 1.1 for p in PEERS}})], "peer_profit"),
        ("USD/EUR ±5%", [("-5%", {"fx_factor": 0.95}), ("+5%", {"fx_factor": 1.05})], "fx"),
        ("Fuel volumes ±5% (all)", [("-5%", {"volume_factor": 0.95}), ("+5%", {"volume_factor": 1.05})], "volume"),
        ("Share of the shock still there in 2027: 50%-100%", [("50%", {"persistence": 0.5}), ("100%", {"persistence": 1.0})],
         "persistence"),
        ("Lufthansa's hedge book: all gasoil to options fade",
         [("all gasoil", {"lh_variant": "all gasoil hedges"}), ("options fade", {"lh_variant": "options fade"})], "lh_book"),
        ("What pass-through applies to: after-hedge cost or market price",
         [("after-hedge cost", {"pt_base": "model"}), ("market price", {"pt_base": "market"})], "pt_base"),
    ]
    if split_q:
        items.append((f"Crude share of the move {split_q[0]:.0%}-{split_q[1]:.0%} (past middle half)",
                      [(f"{split_q[0]:.0%}", {"crude_share": split_q[0]}), (f"{split_q[1]:.0%}", {"crude_share": split_q[1]})],
                      "crude_share"))
    return items


def tornado(twins, usd_per_eur, split, split_q=None):
    """Bars sorted by size. Output: {"base_gap", "base_lh", "bars": [{"label", "ends": [(end, gap, lh_loss)],
    "low", "high", "swing", "lh_low", "lh_high", "lh_swing"}]}."""
    base = base_params(twins)
    base_loss = losses(twins, usd_per_eur, split, base)
    bars = []
    for label, ends, key in assumptions(twins, split_q):
        results = []
        for end_label, change in ends:
            p = {**base, **{k: v for k, v in change.items() if k != "crude_share"}}
            if "profit_factor" in change:
                p["profit_factor"] = {**base["profit_factor"], **change["profit_factor"]}
            sp = split
            if "crude_share" in change:
                move = split[0] + split[1]
                sp = (move * change["crude_share"], move * (1 - change["crude_share"]))
            loss = losses(twins, usd_per_eur, sp, p)
            results.append((end_label, gap(loss), loss[US]))
        gaps, lh = [r[1] for r in results], [r[2] for r in results]
        bars.append({"label": label, "key": key, "ends": results, "low": min(gaps), "high": max(gaps),
                     "swing": max(gaps) - min(gaps), "lh_low": min(lh), "lh_high": max(lh),
                     "lh_swing": max(lh) - min(lh)})
    bars.sort(key=lambda b: b["swing"], reverse=True)
    return {"base_gap": gap(base_loss), "base_lh": base_loss[US], "bars": bars}
