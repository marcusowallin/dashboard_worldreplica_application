"""Sentences for the story steps (D3: steps 1-3), filled from model output - never written by AI.

Each step: a headline that states its number, a body of at most ~40 words, and the numbers it used (so the
"How we calculated this" toggle and the tests can show them).
"""
from math import floor

from src.model.guidance import MATERIALITY_THRESHOLD, is_material
from src.model.run import PEERS, US
from src.story.exposure import premium_exposed_range, unhedged_range
from src.story.price_split import compare_to_history, today_share
from src.story.profit import span
from src.ui.format import (
    _half_up, approx_fraction, story_eur_m_range, story_eur_share_range, story_margin, story_mt, story_mt_range, story_pct_range,
    story_pct, story_pp_range,
)
from src.ui.theme import AIRLINE_SHORT

FACTOR_NAMES = {"recapture": "pass-through", "profit base": "margin cushion", "hedge ratio": "hedge cover",
                "hedge quality": "hedge quality"}   # same names as src/story/hero.py and the charts

BASELINE_LABEL = "27 July"
SIMILAR_MARGIN = 0.003    # margin moves (a fraction: 0.003 = 0.3 pp) are "similar" only if all three airlines are this close


def hook_text(moves):
    """The opening: the question and the stakes, with no answer in it. moves = live['moves'] or None (feeds down)."""
    body = ("Around 27 July, just before their Q2 results, Lufthansa, Air France-KLM and IAG each set out what they "
            "expected to pay for fuel. All three hedge, and all three raise fares when costs rise - but not in the "
            "same way. This page follows one standard fuel shock from the price of a tonne to each airline's "
            "earnings, one step at a time, and ends with the answer and how far to trust it. About five minutes.")
    if not moves:
        return {"headline": "A jump in jet fuel hurts airlines unequally. Is Lufthansa more exposed than "
                            "Air France-KLM and IAG?", "body": body}
    change = moves["d_jet"] / moves["baseline"]["jet"]
    if change >= 0:
        return {"headline": f"Jet fuel is up {change * 100:.0f}% since {BASELINE_LABEL}. Is Lufthansa hit harder "
                            "than its rivals?", "body": body}
    return {"headline": f"Jet fuel is down {abs(change) * 100:.0f}% since {BASELINE_LABEL}. Does Lufthansa gain "
                        "less than its rivals?", "body": body}


def price_step(moves, scenario_move):
    """Step 1 - the price move since 27 July. moves = live['moves'] or None (feeds down).

    Also introduces the standard shock the rest of the page applies to all three airlines, because the answer
    (Step 9) comes last."""
    standard = (f"To compare the three fairly, every step applies the same standard shock to each: "
                f"{'+' if scenario_move >= 0 else '-'}USD {abs(scenario_move):,.0f}/t from {BASELINE_LABEL}.")
    if not moves:
        return {"headline": "Live prices are unavailable right now.",
                "body": f"{standard} Today's move will show here as soon as the price feeds respond."}
    change = moves["d_jet"] / moves["baseline"]["jet"]
    direction = "up" if change >= 0 else "down"
    ratio = abs(moves["d_jet"]) / abs(scenario_move) if scenario_move else float("inf")
    size = (f"{ratio:.1f} times that" if ratio >= 1.1 else "about that size" if ratio >= 0.9 else "smaller than that")
    return {"headline": (f"Jet fuel is {direction} {abs(change) * 100:.0f}% "
                         f"({'+' if moves['d_jet'] >= 0 else '-'}USD {abs(moves['d_jet']):,.0f}/t) since {BASELINE_LABEL}."),
            "body": (f"All three airlines are measured from the same day, {BASELINE_LABEL}. {standard} "
                     f"Today's actual move is {size}."),
            "change": change, "ratio": ratio}


def split_step(moves, scenario_split, stats=None):
    """Step 2 - what moved: crude (Brent) or the jet premium (crack), today vs the past two years' large moves.

    stats = src/story/price_split.benchmark_split output (None or fallback: no history comparison).
    """
    why = ("Jet fuel costs crude oil plus a refining premium (the jet 'crack'). It matters because a crude hedge "
           "covers only the crude part.")
    if stats and not stats["fallback"]:
        history = (f"In the {stats['n']} large moves of the {stats['years']} years before {BASELINE_LABEL}, crude made up a median "
                   f"{stats['median'] * 100:.0f}% (middle half {stats['q1'] * 100:.0f}-{stats['q3'] * 100:.0f}%); "
                   + (f"the scenario uses that median: +{scenario_split[0]:.0f} crude / +{scenario_split[1]:.0f} premium."
                      if tuple(scenario_split) == tuple(stats["split"]) else
                      f"the standard shock uses {scenario_split[0]:+.0f} crude / {scenario_split[1]:+.0f} premium "
                      "(set in Step 11)."))
    else:
        history = (f"Price history is unavailable, so the scenario uses a neutral +{scenario_split[0]:.0f} crude / "
                   f"+{scenario_split[1]:.0f} premium.")
    if not moves:
        return {"headline": "Jet fuel = crude oil (Brent) + the jet premium (crack).", "body": f"{history} {why}"}
    brent, crack = moves["d_brent"], moves["d_crack"]
    position = compare_to_history(today_share(moves), stats) if stats else None
    tail = f", {position} for the {stats['years']} years before." if position else "."
    if brent > 0 and crack > 0:
        share = brent / (brent + crack)
        headline = (f"{approx_fraction(share).capitalize()} of today's rise is crude, "
                    f"{approx_fraction(1 - share)} the jet premium{tail}")
    else:
        headline = (f"Since {BASELINE_LABEL} crude moved {'+' if brent >= 0 else '-'}USD {abs(brent):,.0f}/t and the jet "
                    f"premium {'+' if crack >= 0 else '-'}USD {abs(crack):,.0f}/t{tail}")
    return {"headline": headline, "body": f"{history} {why}"}


def exposure_step(exposure):
    """Step 3 - exposed fuel in tonnes (Lufthansa first; peers in the chart)."""
    lh = exposure[US]
    rest26 = unhedged_range(lh["FY2026"])
    fy27 = unhedged_range(lh["FY2027"])
    premium27 = premium_exposed_range(lh["FY2027"])
    return {"headline": (f"Hedges roll off: Lufthansa's unhedged fuel rises from {story_mt(rest26[1])} for the rest "
                         f"of 2026 to {story_mt_range(*fy27)} in 2027."),
            "body": (f"Its crude hedges leave the jet premium open, so {story_mt_range(*premium27)} of its 2027 fuel is "
                     "exposed to the premium. Only Lufthansa discloses its hedge mix; for the peers the hedged part "
                     "shows as 'mix unknown'."),
            "unhedged_2026": rest26, "unhedged_2027": fy27, "premium_2027": premium27}


def _overlaps(a, b):
    return a[0] <= b[1] and b[0] <= a[1]


def _mag(rng):
    """(low, high) of magnitudes - rises and falls are worded from the same numbers."""
    return tuple(sorted(abs(x) for x in rng))


def cost_step(costs27, costs26, neutral, falling=False):
    """Step 4 - extra fuel cost after hedging (gross), with the size-neutral comparison.

    costs27/costs26: {airline: (gross_low, gross_high)}; neutral: {airline: size_neutral(...)} for 2027.
    """
    cents_of = {a: _mag(neutral[a]["cents_per_ask"]) for a in neutral}
    lh, peers = cents_of[US], [cents_of[p] for p in PEERS]
    unit = "per seat-km"
    if all(_overlaps(lh, p) for p in peers):
        relative = f"about the same {unit} as its peers"
    elif lh[0] > max(p[1] for p in peers):
        relative = f"more {unit} than either peer"
    elif lh[1] < min(p[0] for p in peers):
        relative = f"less {unit} than either peer"
    else:
        relative = f"{unit} within the peers' range"
    cents = lambda r: f"{r[0]:.2f}\u2013{r[1]:.2f}"                      # noqa: E731
    opex = {a: story_pct_range(*_mag(neutral[a]["pct_opex"])) for a in neutral}
    opex_text = (f"{opex[US]} of operating costs for all three" if len(set(opex.values())) == 1
                 else f"{opex[US]} of Lufthansa's operating costs")
    amount = story_eur_m_range(*_mag(costs27[US]))
    verb = f"cuts {amount} from" if falling else f"adds {amount} to"
    return {"headline": f"After hedging, the scenario {verb} Lufthansa's 2027 fuel bill - {relative}.",
            "body": (f"That is {cents(lh)} euro cents per seat-km ("
                     + ", ".join(f"{AIRLINE_SHORT[p]} {cents(cents_of[p])}" for p in PEERS)
                     + f") and {opex_text}. Rest of 2026: {story_eur_m_range(*_mag(costs26[US]))}, the upper end from its "
                     "options."),
            "relative": relative}


def passthrough_step(net27, recapture, net_at_low27, falling=False):
    """Step 5 - gross -> recovered through fares -> net. Net figures = the hero's (same function, same rounding)."""
    top = max(PEERS, key=lambda p: recapture[p])
    word = "circa " if top == "afklm" else "about "
    lh, peer = story_eur_m_range(*_mag(net27[US])), story_eur_m_range(*_mag(net27[top]))
    if falling:
        headline = (f"Passing on about {recapture[US] * 100:.0f}% of the saving to passengers leaves Lufthansa {lh} "
                    f"better off; {AIRLINE_SHORT[top]}, passing on {word}{recapture[top] * 100:.0f}%, keeps {peer}.")
    else:
        headline = (f"Passing on about {recapture[US] * 100:.0f}% leaves Lufthansa with {lh} net; {AIRLINE_SHORT[top]}, "
                    f"passing on {word}{recapture[top] * 100:.0f}%, keeps {peer}.")
    body = ("These pass-through rates look backwards: Air France-KLM's circa 85% is one quarter (Q2 2026); "
            "Lufthansa's and IAG's ~60% are their own estimates. Light marks: at 50% pass-through "
            f"{AIRLINE_SHORT[top]} would keep {story_eur_m_range(*_mag(net_at_low27[top]))}.")
    return {"headline": headline, "body": body}


def profit_step(p27, falling=False):
    """Step 6 - profit and ratios. p27: {airline: profit_cases rows for FY2027}. Carries the Step 4-5 finding:
    the same fuel shock, but different damage depending on pass-through and the margin cushion."""
    pp = {a: span(rows, "margin_pp") for a, rows in p27.items()}
    pp_mag = {a: _mag(v) for a, v in pp.items()}
    margin = {a: rows[0]["margin_before"] for a, rows in p27.items()}
    op = {a: _mag(span(rows, "op_share")) for a, rows in p27.items()}
    peer_pp = (min(pp_mag[p][0] for p in PEERS), max(pp_mag[p][1] for p in PEERS))
    moves, word = ("rise", "rises") if falling else ("slip", "falls")
    if _overlaps(pp_mag[US], peer_pp):
        every = list(pp_mag.values())
        low, high = min(m[0] for m in every), max(m[1] for m in every)
        # "similar" only when all three sit within 0.3 pp of each other; a 0.2-0.8 pp spread is not similar
        if high - low <= SIMILAR_MARGIN:
            slip = f"margins {moves} by similar amounts"
        elif high < 0.01:
            slip = f"margins {moves} by under 1 pp at all three"
        else:
            slip = f"margins {moves} by different amounts"
    elif pp_mag[US][0] > peer_pp[1]:
        slip = f"Lufthansa's margin {word} the most"
    else:
        slip = f"Lufthansa's margin {word} the least"
    thin = ("thin " if margin[US] == min(margin.values()) else "")
    peers_op = (min(op[p][0] for p in PEERS), max(op[p][1] for p in PEERS))
    lead, effect = (("Same fuel relief, different gain", "adds") if falling
                    else ("Same fuel shock, different damage", "costs"))
    to_of = "to" if falling else "of"
    headline = (f"{lead}: {slip}, but on Lufthansa's {thin}{story_margin(margin[US])} margin that {effect} "
                f"{story_pct_range(*op[US])} {to_of} its 2027 operating profit, versus {story_pct_range(*peers_op)} for "
                "its peers.")
    eps = {a: _mag(span(rows, "eps_share")) for a, rows in p27.items()}
    body = ("Operating margin: " + ", ".join(f"{AIRLINE_SHORT[a]} {story_pp_range(*pp[a], signed=falling)}"
                                            for a in (US, *PEERS))
            + f". EPS: Lufthansa {'+' if falling else ''}{story_eur_share_range(*span(p27[US], 'd_eps'))} a share, "
            f"{story_pct_range(*eps[US])} of consensus; "
            + ", ".join(f"{AIRLINE_SHORT[p]} {story_pct_range(*eps[p])}" for p in PEERS) + ".")
    return {"headline": headline, "body": body, "slip": slip}


GLOSS = {"recapture": "pass-through is how much of the extra cost goes into fares",
         "profit base": "margin cushion is how much profit there is to absorb it",
         "hedge ratio": "hedge cover is how much of the fuel is hedged",
         "hedge quality": "hedge quality is what the hedges pay out on"}


def comparison_step(r27, reasons, condition, hq_swing, falling=False):
    """Step 7 - the comparison. The numbers are in the chart and already known from Steps 5-6, so the headline says
    WHY the three differ (pass-through vs Air France-KLM, margin cushion vs IAG; hedge quality small and uncertain)."""
    named = [(p, f) for p, f in reasons.items() if f]
    word = "gain" if falling else "hit"
    if named:
        clauses = [f"against {AIRLINE_SHORT[p]} it is mainly {FACTOR_NAMES[f]}" for p, f in named]
        headline = f"Why the {word} differs: " + ", ".join(clauses) + "."
        gloss = "; ".join(GLOSS[f] for f in dict.fromkeys(f for _, f in named))      # each factor once, in order
        driver_text = gloss[0].upper() + gloss[1:] + ". "
    else:
        headline = f"Why the {word} differs depends on the assumptions."
        driver_text = ""
    hq = (f"Hedge quality moves it by {story_pp_range(hq_swing['low'], hq_swing['high'])}, uncertain because the "
          "peers don't disclose their mix. ")
    return {"headline": headline, "body": driver_text + hq + condition}


def so_what_cards(margin, passthrough, cover, hq_swing, falling=False, pass_through_largest=True, runner_up=None):
    """Step 10 - four cards, each: one model number, one plain sentence, one observation (not advice).

    pass_through_largest: from the Step 8 tornado - the 'biggest lever' title is used only if a pass-through bar is
    the largest; otherwise the card says 'a major lever' (no claim stronger than the evidence).
    runner_up: optional qualifier under the title, e.g. 'hedge cover close behind' (Step 8, Lufthansa's own loss)."""
    ratio = (round(margin["ratio"][0]), round(margin["ratio"][1]))
    times = f"{ratio[0]}" if ratio[0] == ratio[1] else f"{ratio[0]}\u2013{ratio[1]}"
    point = 0.01 / margin["margin_us"]
    per_step, at_peer = _mag(passthrough["per_step"]), _mag(passthrough["at_peer_rate"])
    diff = abs(cover["net_difference"])
    net_word = "net saving" if falling else "net cost"
    return [
        {"title": "Thin margins amplify fuel shocks", "icon": "gauge",
         "number": f"{story_margin(margin['margin_us'])} vs {story_margin(margin['margin_peer'])}",
         "sentence": (f"Lufthansa's expected 2027 operating margin is {story_margin(margin['margin_us'])}, "
                      f"{AIRLINE_SHORT[margin['peer']]}'s {story_margin(margin['margin_peer'])}: "
                      + (f"a similar margin gain is worth {times} times as much of Lufthansa's profit." if falling else
                         f"a similar margin loss costs Lufthansa {times} times the share of its profit.")),
         "note": (f"Observation: at a {story_margin(margin['margin_us'])} margin, each percentage point of margin is "
                  f"about {story_pct(point)} of operating profit.")},
        {"title": "Pricing power is the biggest lever" if pass_through_largest else "Pricing power is a major lever",
         "icon": "fare", "sub": runner_up,
         "number": f"{story_eur_m_range(*per_step)} per {passthrough['step'] * 100:.0f} pp",
         "sentence": (f"Each {passthrough['step'] * 100:.0f} points of pass-through change Lufthansa's 2027 {net_word} by "
                      f"{story_eur_m_range(*per_step)}, {story_pct_range(*_mag(passthrough['per_step_share']))} of "
                      "expected operating profit."),
         "note": (f"Observation: at Air France-KLM's circa {passthrough['peer_rate'] * 100:.0f}% (one quarter), "
                  f"Lufthansa's 2027 {net_word} would be {story_eur_m_range(*at_peer)} "
                  f"{'smaller' if falling else 'lower'}.")},
        {"title": "2027 hedge cover still matters for the level", "icon": "volume",
         "number": story_eur_m_range(diff, diff),
         "sentence": ("Between the printed 29% and the reported ~50% 2027 hedge cover, Lufthansa's 2027 "
                      f"{net_word} differs by {story_eur_m_range(diff, diff)} ({story_pct(abs(cover['share']))} of "
                      "expected operating profit)."),
         "note": "Observation: the 29% dates from December 2025; an updated 2027 hedge ratio would narrow this range."},
        {"title": "Disclosure gaps limit the comparison", "icon": "news",
         "number": "up to \u00b1" + _half_up_1(hq_swing["max_abs"] * 100) + " pp",
         "sentence": ("Only Lufthansa discloses its hedge mix; the peers' unknown mix moves the gap by "
                      f"{story_pp_range(hq_swing['low'], hq_swing['high'])} of expected profit."),
         "note": "Observation: until the peers publish their instrument mix, hedge quality can only be compared as a range."},
    ]


def _half_up_1(value):
    return f"{_half_up(value, 0.1):.1f}"


def tornado_step(result, falling=False):
    """Step 8 - what could change the answer. result = src/story/tornado.tornado(...)."""
    bars = result["bars"]
    top = bars[0]
    closes = [b for b in bars if b["low"] <= 0]
    gap_word = "gains" if falling else "loses"
    if "pass-through" in top["label"]:
        name = top["label"].split(" pass-through")[0]
        headline = (f"The order depends most on pass-through: {name}'s alone changes the gap between Lufthansa and "
                    f"its peers by {top['swing'] * 100:.0f} pp.")
    else:
        headline = (f"The order depends most on {top['label']}, which alone changes the gap between Lufthansa and its "
                    f"peers by {top['swing'] * 100:.0f} pp.")
    body = (f"The gap is how many points more of its expected 2027 operating profit Lufthansa {gap_word} than the "
            f"peers on average ({result['base_gap'] * 100:.0f} pp at the base case). Each bar moves one assumption "
            "across its range and holds the others fixed. "
            + ("No single assumption closes the gap." if not closes else
               f"{len(closes)} assumption{'s' if len(closes) > 1 else ''} could close it on {'their' if len(closes) > 1 else 'its'} own.")
            )
    own = sorted(bars, key=lambda b: b["lh_swing"], reverse=True)
    runner = own[1] if len(own) > 1 else None
    close = bool(runner and own[0]["lh_swing"] and runner["lh_swing"] >= 0.75 * own[0]["lh_swing"])
    return {"headline": headline, "body": body, "pass_through_largest": "pass-through" in top["label"],
            "own_top": own[0], "own_runner_up": runner, "runner_up_close": close}


CLOSE_TO_THRESHOLD = 0.9      # not material, but at least this fraction of the threshold in some case: say so


def materiality_step(p27):
    """Would an always-on monitor raise an alert? The brief's rule (02_SPEC.md): material when the hit is at least 5% of
    expected operating profit or 5% of consensus EPS. p27: {airline: profit_cases rows for FY2027}.

    Each hedging case is tested; an airline is 'yes' if every case is material, 'no' if none is, otherwise 'depends'
    (the verdict then rests on an assumption the page shows as a range). A 'no' within 10% of the threshold is reported
    as 'close' with its largest share, rounded DOWN so a 4.99% never reads as 5.0%. Output: {"status": {airline: ...},
    "sentence": str}.
    """
    status, largest = {}, {}
    for airline, rows in p27.items():
        flags = [is_material(r["op_share"], r["eps_share"]) for r in rows]
        largest[airline] = max(abs(x) for r in rows for x in (r["op_share"], r["eps_share"]) if x is not None)
        if all(flags):
            status[airline] = "yes"
        elif any(flags):
            status[airline] = "depends"
        else:
            status[airline] = "close" if largest[airline] >= CLOSE_TO_THRESHOLD * MATERIALITY_THRESHOLD else "no"
    words = {"yes": "yes", "no": "no", "depends": "depends on the assumptions"}
    parts = [f"{AIRLINE_SHORT[a]}: " + (f"no, but close (up to {floor(largest[a] * 1000) / 10:.1f}%)" if status[a] == "close"
                                        else words[status[a]]) for a in (US, *PEERS)]
    return {"status": status,
            "sentence": (f"Would an always-on monitor raise an alert? The rule is a hit of at least "
                         f"{MATERIALITY_THRESHOLD * 100:.0f}% of expected operating profit or of consensus EPS. "
                         + "; ".join(parts) + ".")}
