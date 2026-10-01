"""Layers 1-2: fuel cost change after hedge quality (06_METHODOLOGY.md section 3).

All shares are fractions (0.82, not 82). All prices are USD per tonne; volumes in tonnes.
Converting from the twins file ("82" with unit "%", "9.42" with unit "million t") is the
caller's job. Pure functions: numbers in, numbers out, nothing read from files.

Key idea: a hedge only protects against the price component it is written on.
  Brent move  -> every hedge instrument protects (Brent, gasoil and jet all move with crude)
  Crack move  -> Brent hedges do NOT protect; gasoil protects a share g; jet swaps protect fully
"""

# One stated conversion factor for every USD/bbl -> USD/t conversion (ASSUMPTIONS.md A12):
# barrels of crude-equivalent per metric tonne of jet fuel.
BBL_PER_TONNE = 7.9


def usd_per_bbl_to_usd_per_t(usd_per_bbl):
    """Convert a price or price move from USD per barrel to USD per tonne (x 7.9, A12)."""
    return usd_per_bbl * BBL_PER_TONNE


def unprotected_shares(h_brent, h_gasoil, h_jet, g=0.8):
    """Return (u_B, u_C): the share of volume NOT protected against a Brent move and a crack move.

    u_B = 1 - hB - hG - hJ         (all instruments protect against Brent)
    u_C = 1 - g * hG - hJ          (Brent hedges give no crack protection)

    Inputs: hedge shares of volume by instrument (fractions), g = share of a jet crack move that
    a gasoil hedge offsets (assumption A6, default 0.8).
    Raises ValueError if a share is outside 0-1, the total exceeds 1, or g is outside 0-1.
    """
    for name, share in (("h_brent", h_brent), ("h_gasoil", h_gasoil), ("h_jet", h_jet), ("g", g)):
        if not 0 <= share <= 1:
            raise ValueError(f"{name} must be between 0 and 1, got {share}")
    total = h_brent + h_gasoil + h_jet
    if total > 1 + 1e-9:
        raise ValueError(f"total hedge ratio cannot exceed 1, got {total}")
    u_brent = 1 - total
    u_crack = 1 - g * h_gasoil - h_jet
    return u_brent, u_crack


def fuel_cost_change_usd(volume_t, u_brent, u_crack, d_brent, d_crack):
    """Change in fuel cost in USD: dFuel = V * (u_B * dB + u_C * dC).

    Inputs: volume in tonnes, unprotected shares, price moves in USD per tonne versus the
    baseline (positive = price up). Output: USD (positive = cost goes up).
    """
    if volume_t < 0:
        raise ValueError(f"volume cannot be negative, got {volume_t}")
    return volume_t * (u_brent * d_brent + u_crack * d_crack)


def usd_to_eur(amount_usd, usd_per_eur):
    """Convert USD to EUR with a rate quoted as USD per 1 EUR (e.g. 1.15): EUR = USD / rate."""
    if usd_per_eur <= 0:
        raise ValueError(f"USD per EUR rate must be positive, got {usd_per_eur}")
    return amount_usd / usd_per_eur


def scale_printed_mix(total_ratio, printed_parts):
    """Apply a printed instrument split to a (possibly different) total hedge ratio.

    Lufthansa rule (assumption A1): slide 17 footnote splits 81% into gasoil 48 and Brent 33;
    we keep those proportions and apply them to the year-to-go ratio 82%:
      hG = 0.82 * 48/81,  hB = 0.82 * 33/81.
    Inputs: total_ratio as a fraction (0.82); printed_parts as a dict of printed numbers,
    e.g. {"gasoil": 48, "brent": 33, "jet": 0}. Output: dict of fractions summing to total_ratio.
    """
    printed_total = sum(printed_parts.values())
    if printed_total <= 0:
        raise ValueError("printed parts must add up to more than zero")
    return {name: total_ratio * part / printed_total for name, part in printed_parts.items()}


def undisclosed_mix_range(volume_t, hedge_ratio, d_brent, d_crack):
    """Fuel cost change when the instrument mix is not disclosed (assumption A5).

    Two bounds and their midpoint (USD):
      upper protection = jet-equivalent: all hedges are jet swaps  -> u_C = 1 - h
      lower protection = crude-only:     all hedges are Brent       -> u_C = 1
      central = midpoint of the two results (status "assumption")
    u_B = 1 - h in every case, so only the crack part differs; range width = V * h * dC.
    Output: dict with keys "jet_equivalent", "crude_only", "central".
    """
    u_b_jet, u_c_jet = unprotected_shares(0, 0, hedge_ratio)
    u_b_crude, u_c_crude = unprotected_shares(hedge_ratio, 0, 0)
    jet = fuel_cost_change_usd(volume_t, u_b_jet, u_c_jet, d_brent, d_crack)
    crude = fuel_cost_change_usd(volume_t, u_b_crude, u_c_crude, d_brent, d_crack)
    return {"jet_equivalent": jet, "crude_only": crude, "central": (jet + crude) / 2}


def effective_protection(u_brent, u_crack, d_brent, d_crack):
    """Share of a price move that the hedges actually absorb (for "reported vs effective").

    = 1 - (u_B * dB + u_C * dC) / (dB + dC). Example (methodology section 10): reported 80%
    hedged, but only 57% protected against a +40 Brent / +60 crack move.
    Raises ValueError if the total move is zero (protection is undefined).
    """
    total_move = d_brent + d_crack
    if total_move == 0:
        raise ValueError("total price move is zero - protection is undefined")
    return 1 - (u_brent * d_brent + u_crack * d_crack) / total_move
