"""Step 3: how much fuel is still exposed - tonnes split by what the hedges cover (bottom-up, before any price).

For each period segment (volume V, hedge ratio h, hedge-book mix brent / gasoil / jet, gasoil quality g):
  protected            = V x h x (jet + g x gasoil)          covered against crude AND the jet premium
  hedged, premium open = V x h x (brent + (1 - g) x gasoil)  crude covered, jet premium (crack) open
  unhedged             = V x (1 - h)                         open to both
The three add up to V. They are the tonnes behind the model's unprotected shares (src/model/fuel.py):
  crude-exposed tonnes   = unhedged                    = V x u_brent
  premium-exposed tonnes = unhedged + premium open     = V x u_crack
Peers do not disclose their hedge mix (A5): their hedged tonnes are shown as one "mix not disclosed" block
(somewhere between all protected and all premium-open), never split by assumption.
Lufthansa's FY2026 "company table" case (options, A24) is a price sensitivity, not a tonnage split - not shown here.
"""
from src.model.run import PEERS, US, build_inputs, cases_for
from src.story.robustness import BENCHMARK_SPLIT, benchmark_market

PERIODS = ("FY2026", "FY2027")


def tonnes_split(segments, mix, g):
    """{'volume', 'protected', 'premium_open', 'unhedged', 'hedged'} in tonnes for a list of segments."""
    volume = sum(s["volume_t"] for s in segments)
    hedged = sum(s["volume_t"] * s["hedge_ratio"] for s in segments)
    protected = hedged * (mix.get("jet", 0) + g * mix.get("gasoil", 0))
    premium_open = hedged * (mix.get("brent", 0) + (1 - g) * mix.get("gasoil", 0))
    return {"volume": volume, "hedged": hedged, "protected": protected, "premium_open": premium_open,
            "unhedged": volume - hedged}


def exposure(twins, usd_per_eur, split=BENCHMARK_SPLIT):
    """Tonnes per airline and period, for every hedge-cover case.

    Output: {airline: {period: [{"case", "volume", "hedged", "unhedged", "protected" (None if mix undisclosed),
                                 "premium_open" (None if undisclosed), "mix_disclosed"}]}}.
    FY2026 = the rest of the year after today (same segments as the benchmark), FY2027 = full year.
    """
    market = benchmark_market(split, usd_per_eur)
    out = {}
    for airline in (US, *PEERS):
        out[airline] = {}
        for period in PERIODS:
            rows = []
            cases = [c for c in cases_for(airline, period) if c != "company table"]
            if airline != US:
                cases = cases[:1]               # hedge ratio and volume do not depend on the (unknown) mix
            for case in cases:
                inputs = build_inputs(twins, airline, period, case, market)
                split_t = tonnes_split(inputs["segments"], inputs["mix"], market["g"])
                disclosed = airline == US
                rows.append({"case": case, "volume": split_t["volume"], "hedged": split_t["hedged"],
                             "unhedged": split_t["unhedged"],
                             "protected": split_t["protected"] if disclosed else None,
                             "premium_open": split_t["premium_open"] if disclosed else None,
                             "mix_disclosed": disclosed})
            out[airline][period] = rows
    return out


def unhedged_range(rows):
    """(min, max) unhedged tonnes over the cases of one airline-period."""
    values = [r["unhedged"] for r in rows]
    return min(values), max(values)


def premium_exposed_range(rows):
    """(min, max) tonnes exposed to the jet premium (unhedged + premium open); None if the mix is undisclosed."""
    if not rows[0]["mix_disclosed"]:
        return None
    values = [r["unhedged"] + r["premium_open"] for r in rows]
    return min(values), max(values)


CASE_LABELS = {"stale 29%": "2027 at 29% (printed)", "reported ~50%": "2027 at ~50% (reported)"}


def chart_rows(exposure_by_airline, names):
    """Rows for the Step 3 chart: Lufthansa's cases first, then the peers; peers' hedged part 'undisclosed'."""
    rows = []
    for airline, periods in exposure_by_airline.items():
        for period, cases in periods.items():
            for r in cases:
                when = "rest of 2026" if period == "FY2026" else CASE_LABELS.get(r["case"], "2027")
                rows.append({"airline": airline, "label": f"{names[airline]} · {when}".replace(" (us)", ""),
                             "protected": r["protected"], "premium_open": r["premium_open"],
                             "undisclosed": None if r["mix_disclosed"] else r["hedged"], "unhedged": r["unhedged"]})
    return rows
