"""The hero: the answer as sentences filled from model output (never written by AI), with wording variants.

Chain shown (bottom-up, DESIGN_BRIEF.md section 7): scenario -> net cost in EUR after hedging and pass-through
-> % of the operating profit expected for the same year. Then the why (driver attribution) and the condition
(robustness). Rounding: story helpers in src/ui/format.py (whole numbers).

Wording variants for the ranking (robustness rule, 06_METHODOLOGY.md 6b):
  "everywhere"   Lufthansa is hit hardest in every combination -> "This holds in every case we model."
  "at_printed"   hardest at the reported pass-through rates for every Brent/crack split, but a peer's lower
                 pass-through (still >= 50%) would put it level -> the condition names that peer and threshold
  "not_settled"  ranges overlap even at the reported pass-through -> the sentence says what it depends on
"""
from src.model.run import PEERS, US
from src.story.robustness import (
    BENCHMARK_SPLIT, RECAPTURE_LOW, SPLITS, attribution, break_even_recapture, loss_ranges, ranking_grid,
)
from src.story.yardstick import expected_operating_profit, expected_revenue
from src.ui.format import approx_fraction, story_eur_bn_range, story_eur_m_range, story_pct_range
from src.ui.theme import AIRLINE_SHORT

WHY_PHRASE = {
    "recapture": "passes on less of the cost",
    "profit base": "runs on a thinner margin",          # attribution factor: fuel burned per euro of expected profit
    "hedge ratio": "has hedged less of its fuel",
    "hedge quality": "holds hedges that leave more of the jet premium open",
}
# Reader-facing names of the attribution factors: src/story/steps.FACTOR_NAMES (one place).


def ranking_status(twins, period, usd_per_eur, splits=SPLITS):
    """Which wording variant applies, and which peers could draw level through lower pass-through.

    Output: {"status": "everywhere" | "at_printed" | "not_settled",
             "flips": {peer: break-even recapture (worst split)} for peers that flip inside the tested range}.
    """
    at_printed = all(
        r[US]["low"] > max(r[p]["high"] for p in PEERS)
        for r in (loss_ranges(twins, period, usd_per_eur, split) for split in splits))
    everywhere = all(row["holds"] for row in ranking_grid(twins, period, usd_per_eur, splits))
    flips = {}
    if at_printed and not everywhere:
        for peer in PEERS:
            r_star = max(break_even_recapture(twins, period, peer, usd_per_eur, split) for split in splits)
            if r_star > RECAPTURE_LOW:
                flips[peer] = r_star
    status = "everywhere" if everywhere else "at_printed" if at_printed else "not_settled"
    return {"status": status, "flips": flips}


def main_reasons(twins, period, usd_per_eur, split=BENCHMARK_SPLIT):
    """Largest driver of the gap per peer, named only if it is the same (and positive) in every range case.

    Output: {peer: factor name or None}.
    """
    reasons = {}
    for peer in PEERS:
        rows = attribution(twins, period, peer, usd_per_eur, split)
        tops = {max(r["parts"], key=r["parts"].get) for r in rows}
        positive = all(r["gap"] > 0 and max(r["parts"].values()) > 0 for r in rows)
        reasons[peer] = tops.pop() if len(tops) == 1 and positive else None
    return reasons


def _peers_phrase(ranges, connector="versus"):
    texts = {p: story_pct_range(ranges[p]["low"], ranges[p]["high"]) for p in PEERS}
    names = [AIRLINE_SHORT[p] for p in PEERS]
    if len(set(texts.values())) == 1:
        return f"{connector} {texts[PEERS[0]]} for {names[0]} and {names[1]}".strip()
    return f"{connector} {texts[PEERS[0]]} for {names[0]} and {texts[PEERS[1]]} for {names[1]}".strip()


def _phrase(factor, peer, margins):
    """Why-phrase for one peer; 'much thinner margin' when Lufthansa's expected margin is under half the peer's."""
    phrase = WHY_PHRASE[factor]
    if factor == "profit base" and margins and margins.get(US) is not None and margins.get(peer):
        if margins[US] < 0.5 * margins[peer]:
            phrase = phrase.replace("a thinner", "a much thinner")
    return phrase


def why_sentence(reasons, margins=None, falling=False):
    """'Mainly because it passes on less of the cost than Air France-KLM and runs on a much thinner margin than IAG.'

    margins: expected 2027 operating margins {airline: fraction} (Step 6), for 'much thinner'.
    """
    named = {p: f for p, f in reasons.items() if f}
    fix = (lambda t: t.replace("of the cost", "of the saving")) if falling else (lambda t: t)  # noqa: E731
    if not named:
        return "The main reasons depend on the assumptions (see the comparison below)."
    if len(named) == len(PEERS) and len(set(named.values())) == 1:
        return fix(f"Mainly because it {WHY_PHRASE[named[PEERS[0]]]} than both peers.")
    parts = [f"{_phrase(f, p, margins)} than {AIRLINE_SHORT[p]}" for p, f in named.items()]
    sentence = "Mainly because it " + " and ".join(parts) + "."
    unnamed = [AIRLINE_SHORT[p] for p in PEERS if p not in named]
    if unnamed:
        sentence += f" Against {unnamed[0]} the main reason depends on the assumptions."
    return fix(sentence)


def condition_sentence(status, falling=False):
    """Robustness wording; falling=True mirrors it for a fall in jet fuel ('gain as much')."""
    if status["status"] == "everywhere":
        return "This holds in every case we model."
    if status["status"] == "not_settled":
        return (f"Which airline {'gains most' if falling else 'is hit hardest'} depends mainly on hedging assumptions: "
                "the peers' undisclosed hedge mix and Lufthansa's 2027 hedge cover.")
    flips = status["flips"]
    if not flips:
        return "This holds at the pass-through rates the airlines report."
    clauses = [f"{AIRLINE_SHORT[p]}'s pass-through fell below {approx_fraction(r)}" for p, r in flips.items()]
    subject = "it" if len(flips) == 1 else "they"
    return f"If {' or '.join(clauses)}, {subject} would {'gain' if falling else 'be hit'} as {'much' if falling else 'hard'}."


def fy26_sentence(ranges, status):
    """One sentence for the rest of 2026, stated honestly."""
    lh = story_pct_range(ranges[US]["low"], ranges[US]["high"])
    if len({story_pct_range(ranges[p]["low"], ranges[p]["high"]) for p in PEERS}) == 1:
        texts = story_pct_range(ranges[PEERS[0]]["low"], ranges[PEERS[0]]["high"])
        peers = f"{AIRLINE_SHORT[PEERS[0]]} and {AIRLINE_SHORT[PEERS[1]]} about {texts}"
    else:
        peers = " and ".join(f"{AIRLINE_SHORT[p]} {story_pct_range(ranges[p]['low'], ranges[p]['high'])}"
                             for p in PEERS)
    head = f"Rest of 2026: Lufthansa {lh}, {peers} of expected profit"
    if status["status"] == "everywhere":
        return head + ", the same order in every case we model."
    if status["status"] == "at_printed" and status["flips"]:
        who = "either" if len(status["flips"]) == len(PEERS) else AIRLINE_SHORT[next(iter(status["flips"]))]
        return head + f", but lower pass-through could put {who} level with it."
    if status["status"] == "at_printed":
        return head + ", at the pass-through rates the airlines report."
    return head + "; the order is not settled."


def build_hero(twins, usd_per_eur, split=BENCHMARK_SPLIT, as_of_label=""):
    """Everything the hero shows, as text and numbers. Split = (Brent, crack) move in USD/t.

    Rises and falls: all ranges are magnitudes (src/story/robustness.direction); a fall reads 'saves', 'gains',
    'passes on less of the saving'. A zero move gets a plain sentence and no ranking claims.
    """
    move = split[0] + split[1]
    falling = move < 0
    r27, r26 = loss_ranges(twins, "FY2027", usd_per_eur, split), loss_ranges(twins, "FY2026", usd_per_eur, split)
    status27, status26 = ranking_status(twins, "FY2027", usd_per_eur), ranking_status(twins, "FY2026", usd_per_eur)
    lh = r27[US]
    cost = story_eur_m_range(lh["cost_low"], lh["cost_high"])
    share = story_pct_range(lh["low"], lh["high"])
    move_text = f"{chr(0x2212) if falling else '+'}USD {abs(move):,.0f}/t"
    if abs(move) < 0.5:
        sentence = "Scenario: jet fuel unchanged since 27 July - no extra fuel cost to compare."
    elif falling:
        sentence = (f"Scenario: jet fuel {move_text}. That saves Lufthansa about *{cost}* of 2027 costs after hedging "
                    f"and pass-through, {share} of its expected 2027 operating profit, {_peers_phrase(r27)}.")
    else:
        sentence = (f"Scenario: jet fuel {move_text}. That adds about *{cost}* to Lufthansa's 2027 costs after hedging "
                    f"and pass-through, {share} of its expected 2027 operating profit, {_peers_phrase(r27)}.")
    reasons = main_reasons(twins, "FY2027", usd_per_eur, split)
    margins = expected_margins(twins, "FY2027")
    return {
        "sentence": sentence,
        "why": ("" if abs(move) < 0.5 else
                why_sentence(reasons, margins, falling) + " " + condition_sentence(status27, falling)),
        "margins": margins, "falling": falling,
        "fy26": "" if abs(move) < 0.5 else fy26_sentence(r26, status26),
        "label": f"vs expected 2027 operating profit (company guidance or analyst consensus, as of {as_of_label})",
        "rows": [{"airline": a, "cost": story_eur_m_range(r27[a]["cost_low"], r27[a]["cost_high"]),
                  "share": story_pct_range(r27[a]["low"], r27[a]["high"])} for a in (US, *PEERS)],
        "ranges": {"FY2027": r27, "FY2026": r26}, "status": {"FY2027": status27, "FY2026": status26},
        "reasons": reasons, "move": move, "split": split,
    }


def live_line(twins_run_output, moves):
    """'Since the airlines last reported (27 Jul), jet fuel is up 23% ...' from a live run (run_all output).

    Extra fuel bill = after hedging, before pass-through (d_fuel_eur), Lufthansa, FY2026 since 27 Jul + FY2027.
    """
    results = twins_run_output["results"]
    fy26 = [r["d_fuel_eur"] for r in results["FY2026"][US].values()]
    fy27 = [r["d_fuel_eur"] for r in results["FY2027"][US].values()]
    low, high = min(fy26) + min(fy27), max(fy26) + max(fy27)
    change = moves["d_jet"] / moves["baseline"]["jet"]
    direction = "up" if change >= 0 else "down"
    bill = "extra fuel bill would be about" if high >= 0 else "fuel bill would be lower by about"
    amount = story_eur_bn_range(abs(low), abs(high)) if min(abs(low), abs(high)) >= 1e9 else \
        story_eur_m_range(abs(low), abs(high))
    return (f"Since the airlines last reported ({moves['baseline_day']:%d %b}), jet fuel is {direction} "
            f"{abs(change) * 100:.0f}% ({'+' if moves['d_jet'] >= 0 else '-'}USD {abs(moves['d_jet']):,.0f}/t, to "
            f"{moves['latest_day']:%d %b}). If today's price held for all of 2026\u201327, before any additional "
            f"pass-through, Lufthansa's {bill} {amount}.")


def consensus_as_of(twins):
    """Newest as_of among the consensus fields used for the yardstick and baselines (YYYY-MM-DD)."""
    fields = ("consensus_ebit_fy26", "consensus_ebit_fy27", "consensus_eps_fy26", "consensus_eps_fy27",
              "consensus_revenue_fy26")
    return max(twins["airlines"][a]["fields"][f]["as_of"] for a in twins["airlines"] for f in fields
               if twins["airlines"][a]["fields"][f]["as_of"])


def company_reports_as_of(twins):
    """Date of the newest company document (level 1) behind any field (YYYY-MM-DD)."""
    docs = {f["document"] for a in twins["airlines"].values() for f in a["fields"].values() if f.get("level") == 1}
    return max(str(twins["documents"][d]["date"]) for d in docs if d in twins["documents"])


def split_check(twins, usd_per_eur, splits=SPLITS):
    """Hero toggle: loss range per airline at the reported pass-through for every Brent/crack split of the move.

    Output: list of {"split", "ranges": {airline: (low, high)}, "lufthansa_hardest": bool}.
    """
    rows = []
    for split in splits:
        r = loss_ranges(twins, "FY2027", usd_per_eur, split)
        rows.append({"split": split, "ranges": {a: (r[a]["low"], r[a]["high"]) for a in r},
                     "lufthansa_hardest": r[US]["low"] > max(r[p]["high"] for p in PEERS)})
    return rows


def expected_margins(twins, period):
    """Expected operating margin per airline = expected operating profit / expected revenue (as in Step 6)."""
    return {a: expected_operating_profit(twins, a, period)["value"] / expected_revenue(twins, a, period)["value"]
            for a in (US, *PEERS)}
