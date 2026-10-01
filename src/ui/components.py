"""HTML components for the story (design notes). Each function returns an HTML string.

Render with st.html(...). Native widgets (charts, buttons, expanders) cannot sit inside custom HTML, so
cards that hold them are keyed containers styled by src/ui/css.py:
    with st.container(key="step-01"):   -> dashed card + rail + dot
        st.html(step_header(...)); st.plotly_chart(...); st.expander("How we calculated this")
    with st.container(key="hero"):      -> hero panel with glow
    st.button(..., key="update-data")   -> arrow-box button

Safety: every text argument is escaped with html.escape - numbers and sentences come from templates, but
the same components will show news headlines later. Arguments named *_html are trusted HTML built by
these functions only.
"""
from html import escape

from src.ui.icons import icon_img
from src.ui.theme import AIRLINE_COLORS, AIRLINE_SHORT


def _e(text):
    return escape(str(text), quote=True)


def eyebrow(text, step_no=None):
    """Small mono label above a headline: 'STEP 03 · EXPOSED FUEL'."""
    number = f'<span class="fsm-step-no">STEP {step_no:02d}</span> · ' if step_no is not None else ""
    return f'<div class="fsm-eyebrow">{number}{_e(text)}</div>'


def airline_name(airline):
    """Airline name with the '(us)' tag for Lufthansa - colour never carries the meaning alone."""
    tag = '<span class="fsm-us-tag">US</span>' if airline == "lufthansa" else ""
    return f"{_e(AIRLINE_SHORT[airline])}{tag}"


def source_marker(ref, href="#", title=None):
    """Tiny superscript source marker, e.g. [A26], [L1], [FRED], linking to its entry on the method page.

    Opens in a new tab so the reader keeps their place and their scenario settings on the story page.
    """
    tip = title or f"Source: {ref}"
    return (f'<sup class="fsm-src"><a href="{_e(href)}" target="_blank" rel="noopener" title="{_e(tip)}">'
            f'[{_e(ref)}]</a></sup>')


def chip(label, value, tone="default", note=None):
    """Pill with a mono label and a value. With a note: hover (desktop) or tap/focus (phone) shows it."""
    css = "fsm-chip warn" if tone == "warn" else "fsm-chip"
    attrs = f' tabindex="0" aria-label="{_e(label)}: {_e(value)}. {_e(note)}"' if note else ""
    tip = f'<span class="fsm-tip" role="tooltip">{_e(note)}</span>' if note else ""
    return (f'<span class="{css}"{attrs}>'
            f'<span class="fsm-chip-label">{_e(label)}</span><span class="fsm-chip-value">{_e(value)}</span>{tip}</span>')


def chips(*chip_html):
    return f'<div class="fsm-chips">{"".join(chip_html)}</div>'


def number_row(items):
    """Three-number row. items: list of {"airline", "value" (big figure), "sub" (optional second figure,
    e.g. the % that goes with a euro amount), "caption"} - all formatted text."""
    cells = []
    for item in items:
        airline = item["airline"]
        us = " us" if airline == "lufthansa" else ""
        sub = f'<div class="fsm-num-sub">{_e(item["sub"])}</div>' if item.get("sub") else ""
        marks = item.get("markers_html", "")                      # trusted: built by source_marker
        cells.append(
            f'<div class="fsm-num{us}" style="--fsm-airline: {AIRLINE_COLORS[airline]}">'
            f'<div class="fsm-num-airline">{airline_name(airline)}</div>'
            f'<div class="fsm-num-value">{_e(item["value"])}</div>{sub}'
            f'<div class="fsm-num-caption">{_e(item["caption"])}{marks}</div></div>')
    return f'<div class="fsm-numbers">{"".join(cells)}</div>'


def hero_text(eyebrow_text, sentence, why, label, markers_html="", label_markers_html="", step_no=None):
    """Hero copy block: eyebrow, the one-sentence answer, the why/condition line, the yardstick label.

    sentence may mark the key number with *...* (rendered in the accent colour); everything is escaped first.
    """
    parts = _e(sentence).split("*")
    sentence_html = "".join(f"<em>{p}</em>" if i % 2 else p for i, p in enumerate(parts))
    return (f'{eyebrow(eyebrow_text, step_no)}<p class="fsm-hero-sentence">{sentence_html}{markers_html}</p>'
            f'<p class="fsm-hero-why">{_e(why)}</p><p class="fsm-label">{_e(label)}{label_markers_html}</p>')


def hero_line(text, kind=""):
    """A secondary hero line (FY2026 caveat; kind="live" for the live-move line)."""
    css = "fsm-hero-line live" if kind == "live" else "fsm-hero-line"
    return f'<p class="{css}">{_e(text)}</p>'


def skip_link(text, target_step):
    return f'<a class="fsm-skip" href="#step-{target_step:02d}">{_e(text)} &darr;</a>'


def hook(eyebrow_text, headline, body):
    """The opening of the page: the question and what is at stake. Deliberately contains no answer."""
    return (f'{eyebrow(eyebrow_text)}<h1 class="fsm-hook">{_e(headline)}</h1>'
            f'<p class="fsm-hook-body">{_e(body)}</p>')


def bridge(text):
    """One line closing a chapter: the question the next chapter answers."""
    return f'<p class="fsm-bridge">{_e(text)}</p>'


def step_header(step_no, eyebrow_text, headline, body, icon, markers_html=""):
    """Header inside a step container: anchor, dot-grid icon, eyebrow, headline with the number, <=40 words."""
    anchor = f'<div class="fsm-anchor" id="step-{step_no:02d}"></div>' if step_no is not None else ""
    return (f'{anchor}'
            f'<div class="fsm-step-head">{icon_img(icon)}<div>{eyebrow(eyebrow_text, step_no)}'
            f'<div class="fsm-step-title">{_e(headline)}{markers_html}</div>'
            f'<p class="fsm-step-body">{_e(body)}</p></div></div>')


def airline_card(airline, rows):
    """Ratio card. rows: list of {"label", "before", "after", "change", "direction" ("up"/"down"/None)}.

    direction describes the effect on the company: "down" = worse (shown in the cost-up colour, with the
    signed change in text), "up" = better.
    """
    body = []
    for row in rows:
        tone = {"down": " fsm-up", "up": " fsm-down"}.get(row.get("direction"), "")
        body.append(f'<div class="fsm-row"><span class="fsm-row-label">{_e(row["label"])}</span>'
                    f'<span class="fsm-row-change{tone}">{_e(row["change"])}</span>'
                    f'<span class="fsm-row-ba">{_e(row["before"])} &rarr; {_e(row["after"])}</span></div>')
    us = " us" if airline == "lufthansa" else ""
    return (f'<div class="fsm-card{us}"><div class="fsm-card-title">{airline_name(airline)}</div>'
            f'{"".join(body)}</div>')


def takeaway_card(title, body, icon, number=None, note=None, sub=None):
    """'So what' card: icon, short title, optional qualifier, optional big number, one sentence, optional observation."""
    sub_html = f'<div class="fsm-card-sub">{_e(sub)}</div>' if sub else ""
    number_html = f'<div class="fsm-card-number">{_e(number)}</div>' if number else ""
    note_html = f'<div class="fsm-card-note">{_e(note)}</div>' if note else ""
    return (f'<div class="fsm-card"><div class="fsm-card-title">{icon_img(icon, size=22)}{_e(title)}</div>'
            f'{sub_html}{number_html}<div class="fsm-card-body">{_e(body)}</div>{note_html}</div>')


def cards(*card_html, columns=None):
    """Card grid; columns=2 forces a 2 x 2 layout (one column on phones)."""
    css = "fsm-cards two" if columns == 2 else "fsm-cards"
    return f'<div class="{css}">{"".join(card_html)}</div>'


def link_button(text, href):
    """Arrow-box link button (HTML); for actions use st.button with key 'update-data' or 'cta-...'."""
    return f'<a class="fsm-btn" href="{_e(href)}">{_e(text)}</a>'


def as_of_line(text):
    """Small grey 'Data as of ...' line."""
    return f'<p class="fsm-asof">{_e(text)}</p>'


def notice(text):
    """Short warning line (e.g. live feeds down, showing the last good data)."""
    return f'<p class="fsm-notice" role="status">{_e(text)}</p>'


DIRECTION_WORDS = {"cost_up": "cost up", "cost_down": "cost down", "unclear": "direction unclear"}
# Impact on each airline's earnings (D8b): a symbol AND a word - never the symbol or colour alone.
IMPACT_MARKERS = {"positive": ("&#9650;", "positive"), "negative": ("&#9660;", "negative"),
                  "neutral": ("&#9679;", "neutral")}


def news_item(item, airline_names, driver_steps):
    """One calm feed row: headline (link), source and date, tags, verified-quote marker, link to the story step.

    item: {"title", "url", "domain", "outlet", "also_reported_by", "source", "seen" (datetime or None),
           "tag" (validated tag or None)}. Each tagged airline carries its impact marker with the word.
    """
    title = _e(item["title"])
    url = item.get("url") or ""
    safe = url.startswith(("https://", "http://"))                # feed URLs are data: no javascript: or data: links
    head = f'<a class="fsm-news-title" href="{_e(url)}" target="_blank" rel="noopener">{title}</a>' if safe \
        else f'<span class="fsm-news-title">{title}</span>'
    seen = item.get("seen")
    outlet = item.get("outlet") or item.get("domain") or ""
    via = "via web search" if item.get("source") == "web search" else ""
    meta = " · ".join(x for x in (_e(outlet), f"{seen:%-d %b %Y}" if seen else "", via) if x)
    also = item.get("also_reported_by") or []
    if also:
        meta += f' · <span class="fsm-news-also">also reported by {_e(", ".join(also))}</span>'
    tag = item.get("tag")
    if tag is None:
        tags = '<span class="fsm-news-tag muted">untagged</span>'
        link = ""
    elif not tag["relevant"]:
        tags = '<span class="fsm-news-tag muted">not relevant to the three airlines</span>'
        link = ""
    else:
        step, driver_label = driver_steps.get(tag["driver"], (None, tag["driver"]))
        parts = []
        for a in tag["airlines"]:
            impact = tag.get("impacts", {}).get(a, "neutral")
            symbol, word = IMPACT_MARKERS.get(impact, IMPACT_MARKERS["neutral"])
            parts.append(f'<span class="fsm-news-tag airline impact-{impact}" title="Likely effect on '
                         f'{_e(airline_names.get(a, a))}\'s earnings: {word}">{_e(airline_names.get(a, a))} '
                         f'<span class="fsm-impact" aria-hidden="true">{symbol}</span> {word}</span>')
        parts += [f'<span class="fsm-news-tag">{_e(driver_label)}</span>',
                  f'<span class="fsm-news-tag">{_e(DIRECTION_WORDS.get(tag["direction"], tag["direction"]))}</span>']
        if tag.get("evidence_ok"):
            parts.append(f'<span class="fsm-news-tag ok" title="Quote checked in code: &quot;{_e(tag["evidence"])}&quot;">'
                         "&#10003; verified quote</span>")
        else:
            parts.append('<span class="fsm-news-tag warn">quote not found - tag unconfirmed</span>')
        tags = "".join(parts)
        link = f'<a class="fsm-news-step" href="./#step-{step:02d}">Step {step} &rarr;</a>' if step else ""
    return (f'<div class="fsm-news"><div class="fsm-news-head">{head}{link}</div>'
            f'<div class="fsm-news-meta">{meta}</div><div class="fsm-news-tags">{tags}</div></div>')


def footer(method_href, source_lines, disclaimer, author, extra_links=()):
    """Page footer: method link (and other pages in extra_links = [(text, href)]), data sources with as-of dates,
    disclaimer, author."""
    sources = "".join(f"<li>{_e(line)}</li>" for line in source_lines)
    more = "".join(f'<a class="fsm-btn" href="{_e(href)}">{_e(text)}</a>' for text, href in extra_links)
    return (f'<footer class="fsm-footer"><a class="fsm-btn" href="{_e(method_href)}">Method &amp; sources</a>{more}'
            f'<ul class="fsm-footer-sources">{sources}</ul><p class="fsm-footer-note">{_e(disclaimer)}</p>'
            f'<p class="fsm-footer-note">{_e(author)}</p></footer>')


def news_summary(summary, airline_names, driver_steps, days=7):
    """The 7-day summary line: '12 relevant headlines in 7 days. Lufthansa 5 negative, 1 positive ...'."""
    if not summary["headlines"]:
        text = f"No tagged headlines collected in the last {days} days yet."
        return f'<p class="fsm-news-summary">{_e(text)}</p>'
    parts = []
    for airline, counts in summary["impacts"].items():
        bits = [f"{counts[k]} {k}" for k in ("negative", "positive", "neutral") if counts[k]]
        if bits:
            parts.append(f"{airline_names.get(airline, airline)} {', '.join(bits)}")
    step, label = driver_steps.get(summary["top_driver"], (None, summary["top_driver"]))
    text = (f"Last {days} days: {summary['headlines']} relevant headline{'s' if summary['headlines'] != 1 else ''}"
            + (f" - {'; '.join(parts)}" if parts else "") + f". Most frequent topic: {label}"
            + (f" (Step {step})." if step else "."))
    if summary.get("untagged"):
        text += f" {summary['untagged']} untagged."
    return f'<p class="fsm-news-summary">{_e(text)}</p>'
