"""Income statement chain: dFuel -> dEBIT -> dNI -> dEPS (06_METHODOLOGY.md section 5).

All rates are fractions (0.60, not 60). Amounts in EUR. Pure functions.

  dRevenue = r * dFuel_EUR                 (recapture via fares/surcharges, same period, symmetric)
  dEBIT    = -dFuel_EUR + dRevenue = -(1 - r) * dFuel_EUR
  dEBT     = dEBIT                         (second-order interest effect ignored - labelled)
  dNI      = dEBT * (1 - t) * (1 - m)      (t = marginal tax rate, m = minorities' share)
  dEPS     = dNI / N                       (N = diluted weighted average shares)
Sign convention: dFuel > 0 means fuel cost goes UP, so dEBIT, dNI and dEPS go DOWN.
"""


def _check_fraction(name, value):
    """Raise ValueError unless 0 <= value <= 1."""
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")


def ebit_change(d_fuel_eur, recapture):
    """dEBIT = -(1 - r) * dFuel. Recapture r = share of the fuel change passed on to customers."""
    _check_fraction("recapture", recapture)
    return -(1 - recapture) * d_fuel_eur


def net_income_change(d_ebit, tax_rate, minority_share):
    """dNI (attributable to shareholders) = dEBIT * (1 - t) * (1 - m)."""
    _check_fraction("tax_rate", tax_rate)
    _check_fraction("minority_share", minority_share)
    return d_ebit * (1 - tax_rate) * (1 - minority_share)


def eps_change(d_net_income, diluted_shares):
    """dEPS in EUR per share = dNI / N. N is a count of shares (not thousands)."""
    if diluted_shares <= 0:
        raise ValueError(f"diluted shares must be positive, got {diluted_shares}")
    return d_net_income / diluted_shares


def income_chain(d_fuel_eur, recapture, tax_rate, minority_share, diluted_shares):
    """Run the whole chain and return every step (for the page's evidence chain).

    Output keys: d_fuel_eur, d_revenue, d_ebit, d_net_income, d_eps.
    """
    d_ebit = ebit_change(d_fuel_eur, recapture)
    d_net_income = net_income_change(d_ebit, tax_rate, minority_share)
    return {
        "d_fuel_eur": d_fuel_eur,
        "d_revenue": recapture * d_fuel_eur,
        "d_ebit": d_ebit,
        "d_net_income": d_net_income,
        "d_eps": eps_change(d_net_income, diluted_shares),
    }
