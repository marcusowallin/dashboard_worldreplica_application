"""Why airlines differ: main driver of the gap to Lufthansa (06_METHODOLOGY.md section 8, P1 part).

Method (decided 30 Sep 2026, ASSUMPTIONS.md A23): start from Lufthansa's inputs and swap one
factor group at a time to the peer's values, in a fixed order. Each swap's change in dEPS % is
that factor's "bar"; the bars add up exactly to the peer's dEPS % minus ours. The largest bar is
the main driver - named only if it is the same in every range case (robustness rule, section 8).

Inputs per airline (model units, see src/twins.get_model_value):
  volume_t      remaining volume in tonnes for the period
  hedge_ratio   total hedge ratio for the period (fraction)
  mix           split of the HEDGE BOOK by instrument, fractions summing to 1:
                {"brent": .., "gasoil": .., "jet": ..}
                Undisclosed mix (A5): jet-equivalent {"jet": 1}, crude-only {"brent": 1};
                the central case (midpoint of the two results) equals {"brent": 0.5, "jet": 0.5}
                because the fuel cost is linear in the crack exposure.
  recapture, tax, minority      fractions
  shares        diluted share count
  baseline_eps  EUR per share (consensus, or fallback)
  u_override    optional {"u_brent", "u_crack"} replacing the computed unprotected shares
                (Lufthansa "company table" case, A24); None otherwise
"""
from src.model.fuel import fuel_cost_change_usd, unprotected_shares, usd_to_eur
from src.model.guidance import change_as_share
from src.model.income import income_chain

FACTOR_GROUPS = (
    ("hedge ratio", ("hedge_ratio",)),
    ("hedge quality", ("mix", "u_override")),
    ("recapture", ("recapture",)),
    ("profit cushion", ("volume_t", "shares", "baseline_eps")),
    ("tax and minorities", ("tax", "minority")),
)


def eps_impact_share(inputs, d_brent, d_crack, usd_per_eur, g=0.8):
    """Run one airline's chain and return dEPS (EUR/share) and dEPS as a share of baseline EPS.

    Output: {"d_eps": float, "d_eps_share": float or None}.
    """
    mix = inputs["mix"]
    if abs(sum(mix.values()) - 1) > 1e-9:
        raise ValueError(f"hedge book mix must sum to 1, got {sum(mix.values())}")
    h = inputs["hedge_ratio"]
    u_b, u_c = unprotected_shares(h * mix.get("brent", 0), h * mix.get("gasoil", 0),
                                  h * mix.get("jet", 0), g)
    override = inputs.get("u_override")
    if override:  # e.g. Lufthansa's company-table case: exposures implied by its own table
        u_b, u_c = override["u_brent"], override["u_crack"]
    d_fuel_eur = usd_to_eur(fuel_cost_change_usd(inputs["volume_t"], u_b, u_c, d_brent, d_crack),
                            usd_per_eur)
    chain = income_chain(d_fuel_eur, inputs["recapture"], inputs["tax"], inputs["minority"],
                         inputs["shares"])
    return {"d_eps": chain["d_eps"], "d_eps_share": change_as_share(chain["d_eps"], inputs["baseline_eps"])}


def waterfall(ours, peer, d_brent, d_crack, usd_per_eur, g=0.8):
    """Bars explaining the peer's dEPS % minus ours, one factor group at a time.

    Output: {"start": our dEPS %, "end": peer dEPS %, "bars": [(factor, change), ...]}.
    Raises ValueError if a dEPS % is not meaningful (missing or non-positive baseline EPS).
    """
    current = dict(ours)
    start = _share(current, d_brent, d_crack, usd_per_eur, g)
    previous = start
    bars = []
    for factor, keys in FACTOR_GROUPS:
        for key in keys:
            current[key] = peer.get(key)  # optional keys (u_override) default to None
        value = _share(current, d_brent, d_crack, usd_per_eur, g)
        bars.append((factor, value - previous))
        previous = value
    return {"start": start, "end": previous, "bars": bars}


def main_driver(bars):
    """Name of the factor with the largest absolute bar."""
    return max(bars, key=lambda bar: abs(bar[1]))[0]


def robust_driver(waterfalls):
    """The main driver if it is the same in every case (range ends), else None.

    None means the one-line answer must say the comparison depends on the uncertain inputs
    (undisclosed instrument mixes, Lufthansa's current FY27 hedge cover).
    """
    drivers = {main_driver(w["bars"]) for w in waterfalls}
    return drivers.pop() if len(drivers) == 1 else None


def _share(inputs, d_brent, d_crack, usd_per_eur, g):
    share = eps_impact_share(inputs, d_brent, d_crack, usd_per_eur, g)["d_eps_share"]
    if share is None:
        raise ValueError("dEPS % is not meaningful (baseline EPS missing or not positive)")
    return share
