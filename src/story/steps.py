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
    DASH,
    _half_up, approx_fraction, story_eur_m_range, story_eur_share_range, story_margin, story_mt, story_mt_range, story_pct_range,
    story_pct, story_pp_range,
)
from src.ui.theme import AIRLINE_SHORT

FACTOR_NAMES = {"recapture": "pass-through", "profit base": "margin cushion", "hedge ratio": "hedge cover",
                "hedge quality": "hedge quality"}   # same names as src/story/hero.py and the charts

BASELINE_LABEL = "27 July"
SIMILAR_MARGIN = 0.003    # margin moves (a fraction: 0.003 = 0.3 pp) are "similar" only if all three airlines are this close


def hook_text(moves, scenario_move=100.0):
    """The opening: the question and the stakes, with no answer in it - and honest that the euro figures on the page
    are for a hypothetical, standard shock, not a forecast. moves = live['moves'] or None (feeds down)."""
    standard = (f"This page applies one hypothetical shock - jet fuel {'+' if scenario_move >= 0 else '-'}USD "
                f"{abs(scenario_move):,.0f} a tonne - to all three and follows it from the price of a tonne to each "
                "airline's earnings, ending with the answer and how far to trust it. ")
    if moves and scenario_move:
        ratio = abs(moves["d_jet"]) / abs(scenario_move)
        standard += (f"Today's actual move is {ratio:.1f} times that, so the euro amounts compare the airlines; they "
                     "are not a forecast. ")
    body = ("Around 27 July, just before their Q2 results, Lufthansa, Air France-KLM and IAG each set out what they "
            "expected to pay for fuel. All three hedge and raise fares when costs rise - but not in the same way. "
            + standard + "About five minutes.")
    if not moves:
        return {"headline": "A jump in jet fuel hurts airlines unequally. Is Lufthansa more exposed than "
                            "Air France-KLM and IAG?", "body": body}
    change = moves["d_jet"] / moves["baseline"]["jet"]
    if change >= 0:
        return {"headline": f"Jet fuel is up {change * 100:.0f}% since {BASELINE_LABEL}. Is Lufthansa hit harder "
                            "than its rivals?", "body": body}
    return {"headline": f"Jet fuel is down {abs(change) * 100:.0f}% since {BASELINE_LABEL}. Does Lufthansa gain "
                        "less than its rivals?", "body": body}


def shock_step(moves, scenario_move, scenario_split, stats=None, smoothed=None):
    """Step 1 - how big is the shock and what is it made of (price move, crude vs jet premium, the standard shock).

    moves = live['moves'] or None (feeds down); stats = price_split.benchmark_split output; smoothed = the move on
    five-day averages (choices.smoothed_move) or None. The page applies the same hypothetical shock to all three airlines
    because the answer (Step 7) comes last, so it is introduced here.
    """
    standard = f"{'+' if scenario_move >= 0 else '-'}USD {abs(scenario_move):,.0f}/t"
    split_text = f"{scenario_split[0]:+.0f} crude / {scenario_split[1]:+.0f} premium"
    history = ""
    if stats and not stats["fallback"]:
        lo, hi = stats["interval"]
        history = (f"Crude made a median {stats['median'] * 100:.0f}% of the {stats['n']} large moves of the "
                   f"{stats['years']} years before (middle half {stats['q1'] * 100:.0f}-{stats['q3'] * 100:.0f}%; the median "
                   f"itself is uncertain, {lo * 100:.0f}-{hi * 100:.0f}%). ")
    if not moves:
        return {"headline": "Live prices are unavailable right now.",
                "body": (f"{history}Every step applies the same hypothetical shock to all three airlines: jet fuel "
                         f"{standard} from {BASELINE_LABEL}, split {split_text}. Today's move will show here when the "
                         "feeds respond.")}
    change = moves["d_jet"] / moves["baseline"]["jet"]
    direction = "up" if change >= 0 else "down"
    ratio = abs(moves["d_jet"]) / abs(scenario_move) if scenario_move else float("inf")
    headline = (f"Jet fuel is {direction} {abs(change) * 100:.0f}% ({'+' if moves['d_jet'] >= 0 else '-'}USD "
                f"{abs(moves['d_jet']):,.0f}/t) since {BASELINE_LABEL}")
    brent, crack = moves["d_brent"], moves["d_crack"]
    if brent > 0 and crack > 0:
        share = brent / (brent + crack)
        headline += f" - {approx_fraction(share)} of it crude oil, {approx_fraction(1 - share)} the jet premium."
        position = compare_to_history(today_share(moves), stats) if stats else None
        history += f"Today's split is {position} for that history. " if position else ""
    else:
        headline += f": crude {brent:+,.0f}, jet premium {crack:+,.0f} USD/t."
    size = (f"{ratio:.1f} times that" if ratio >= 1.1 else "about that size" if ratio >= 0.9 else "smaller than that")
    smooth_text = (f" On five-day averages at both ends the move is {smoothed['d_jet']:+,.0f} USD/t."
                   if smoothed else "")
    return {"headline": headline,
            "body": (f"{history}The page applies {standard}, split {split_text}, to all three airlines; today's actual "
                     f"move is {size}.{smooth_text}"),
            "change": change, "ratio": ratio}


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


def bill_step(gross27, net27, recapture, net_at_low27, per_tonne, falling=False):
    """Step 3 - the fuel bill after hedging, what fares recover, and what is left (net = the answer's euro figures).

    gross27/net27/net_at_low27: {airline: (low, high)} in EUR; recapture: printed rates; per_tonne: {airline: (low, high)}
    net cost per tonne of fuel (choices.net_cost_per_tonne), the size-neutral exposure."""
    top = max(PEERS, key=lambda p: recapture[p])
    word = "circa " if top == "afklm" else "about "
    gross, lh = story_eur_m_range(*_mag(gross27[US])), story_eur_m_range(*_mag(net27[US]))
    peer = story_eur_m_range(*_mag(net27[top]))
    if falling:
        headline = (f"After hedging, the fall cuts {gross} from Lufthansa's 2027 fuel bill; passing on about "
                    f"{recapture[US] * 100:.0f}% of the saving leaves it {lh} better off. {AIRLINE_SHORT[top]}, passing on "
                    f"{word}{recapture[top] * 100:.0f}%, is {peer} better off.")
    else:
        headline = (f"After hedging, the shock adds {gross} to Lufthansa's 2027 fuel bill; passing on about "
                    f"{recapture[US] * 100:.0f}% leaves {lh} net. {AIRLINE_SHORT[top]}, passing on {word}"
                    f"{recapture[top] * 100:.0f}%, is left with {peer}.")
    tonne = lambda a: f"EUR {_mag(per_tonne[a])[0]:.0f}{DASH}{_mag(per_tonne[a])[1]:.0f}"      # noqa: E731
    body = (f"Per tonne of fuel the net cost is {tonne(US)} at Lufthansa, {tonne('afklm')} at {AIRLINE_SHORT['afklm']} and "
            f"{tonne('iag')} at IAG. {AIRLINE_SHORT[top]}'s circa 85% is one quarter's actual; the other rates are the "
            f"airlines' own estimates. At 50%, {AIRLINE_SHORT[top]} would be left with "
            f"{story_eur_m_range(*_mag(net_at_low27[top]))}.")
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

    pass_through_largest: from the Step 6 tornado - the 'biggest lever' title is used only if a pass-through bar is
    the largest; otherwise the card says 'a major lever' (no claim stronger than the evidence).
    runner_up: optional qualifier under the title, e.g. 'hedge cover close behind' (Step 6, Lufthansa's own loss)."""
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


BAR_NAMES = {"persistence": "how much of today's shock lasts into 2027", "lh_book": "Lufthansa's hedge book (its undisclosed "
             "2027 mix and its options)", "lh_cover": "Lufthansa's 2027 hedge cover", "lh_profit": "Lufthansa's expected profit",
             "peer_profit": "the peers' expected profit", "peer_mix": "the peers' undisclosed hedge mix",
             "pt_base": "what pass-through is applied to", "g": "how much of the premium gasoil hedges cover",
             "fx": "the USD/EUR rate", "volume": "fuel volumes", "crude_share": "the crude share of the move"}


def tornado_step(result, falling=False):
    """Step 6 - what the answer rests on. result = src/story/tornado.tornado(...).

    Resolves the apparent clash with the ranking claim: no single assumption closes the gap to the peers' AVERAGE, but the
    ranking against Air France-KLM alone can flip if its pass-through is low (the answer says so); both are stated."""
    bars = result["bars"]
    top = bars[0]
    closes = [b for b in bars if b["low"] <= 0]
    gap_word = "gains" if falling else "loses"
    if top["key"].startswith("pt:"):
        name = top["label"].split(" pass-through")[0]
        headline = (f"The result is most sensitive to pass-through: {name}'s alone changes the gap between Lufthansa and "
                    f"its peers by {top['swing'] * 100:.1f} pp.")
    else:
        headline = (f"The result is most sensitive to {BAR_NAMES.get(top['key'], top['label'])}, which alone changes the "
                    f"gap between Lufthansa and its peers by {top['swing'] * 100:.1f} pp.")
    closest = min(bars, key=lambda b: b["low"])
    body = (f"The gap is how many points more of its expected 2027 operating profit Lufthansa {gap_word} than the "
            f"peers on average ({result['base_gap'] * 100:.1f} pp at the base case). Each bar moves one assumption "
            "across its range and holds the others fixed. "
            + (f"No single assumption closes it; the closest, {closest['label']}, narrows it "
               f"to {closest['low'] * 100:.1f} pp." if not closes else
               f"{len(closes)} assumption{'s' if len(closes) > 1 else ''} could close it on {'their' if len(closes) > 1 else 'its'} own."))
    own = sorted(bars, key=lambda b: b["lh_swing"], reverse=True)
    runner = own[1] if len(own) > 1 else None
    close = bool(runner and own[0]["lh_swing"] and runner["lh_swing"] >= 0.75 * own[0]["lh_swing"])
    return {"headline": headline, "body": body, "pass_through_largest": top["key"].startswith("pt:"),
            "own_top": own[0], "own_runner_up": runner, "runner_up_close": close}


def sensitivity_table(persistence, pt_base, lh_range, flat_ranges):
    """The one table under the tornado: choices that change the LEVELS of the answer - and, for the pass-through reading,
    whether Lufthansa is still clearly the hardest hit. Values are % of expected 2027 operating profit; negative = a gain.

    persistence = choices.persistence_table; pt_base = choices.pass_through_base; lh_range = choices.lufthansa_range;
    flat_ranges = loss_ranges for the page's own scenario. Output: list of row dicts (formatted strings).
    """
    names = {US: "Lufthansa", "afklm": AIRLINE_SHORT["afklm"], "iag": "IAG"}

    def row(label, ranges):
        peers_high = max(ranges[p][1] for p in PEERS)
        return {"If...": label, **{names[a]: story_pct_range(*ranges[a]) for a in (US, *PEERS)},
                "Lufthansa clearly hit hardest": "yes" if ranges[US][0] > peers_high else "ranges overlap"}

    rng = lambda r: {a: (r[a]["low"], r[a]["high"]) for a in (US, *PEERS)}                        # noqa: E731
    rows = [row("the page's own case", rng(flat_ranges))]
    for r in persistence:
        if r["share"] < 1.0:
            rows.append(row(f"only {r['share'] * 100:.0f}% of the shock lasts into 2027", rng(r["ranges"])))
    rows.append(row("pass-through applies to the market price rise, not the cost after hedging",
                    {a: pt_base[a]["share_market"] for a in (US, *PEERS)}))
    full = lh_range["full"]
    widest = {**rng(flat_ranges), US: (full["low"], full["high"])}
    rows.append(row("Lufthansa's undisclosed hedge mix and an options fade are included", widest))
    return rows


def sensitivity_sentences(pt_base, lh_range, flat_ranges):
    """Two sentences for the findings the table cannot say in numbers."""
    names = {US: "Lufthansa", "afklm": AIRLINE_SHORT["afklm"], "iag": "IAG"}
    flips = _flip_clause(pt_base, names)
    full = lh_range["full"]
    printed = next(v for v in lh_range["variants"] if v["name"] == "printed mix")
    return {
        "pass_through": ("The companies say they recover about 60-85% of 'the higher fuel cost'. If that means the market "
                         "price rise, an airline that hedged recovers more than it lost" + flips + ". The reading decides "
                         "the sign for the airlines that hedged most; the page uses the cost after hedging."),
        "lufthansa": (f"Lufthansa's hedges are options, which protect less than swaps as prices rise: with its undisclosed "
                      f"2027 mix and an options fade its range widens from {story_pct_range(printed['low'], printed['high'])} "
                      f"to {story_pct_range(full['low'], full['high'])}."),
    }


def _flip_clause(pt_base, names):
    """': X would gain instead of paying; Y could, in some hedge cases' - or '' when no sign changes."""
    whole = [names[a] for a in pt_base if pt_base[a]["flips"] and pt_base[a]["market"][1] < 0]
    part = [names[a] for a in pt_base if pt_base[a]["flips"] and pt_base[a]["market"][1] >= 0]
    bits = []
    if whole:
        bits.append(f"{' and '.join(whole)} would gain instead of paying")
    if part:
        bits.append(f"{' and '.join(part)} could, in some hedge cases")
    return ": " + "; ".join(bits) if bits else ""


def limits_lines():
    """The three limits that matter, on the story page (the full list is on Method & sources)."""
    return [
        "Options are modelled as swaps (Lufthansa's own table shows its protection fading), so its euro figures lean low.",
        "The 2027 effect assumes the shock lasts the year, while forward prices slope down - see the table above.",
        "The profit base is consensus taken after most of the price rise, and Air France-KLM's 85% pass-through is one quarter.",
    ]


CLOSE_TO_THRESHOLD = 0.9      # not material, but at least this fraction of the threshold in some case: say so


def materiality_step(p27):
    """Would an always-on monitor raise an alert? The brief's rule: material when the hit is at least 5% of
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
