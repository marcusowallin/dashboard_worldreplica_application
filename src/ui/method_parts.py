"""HTML parts for the Method & sources page. Every text value is escaped; links must be http(s) URLs.

Document links always go to the companies' (or providers') own pages - never to files in this project.
"""
from html import escape


def _e(text):
    return escape(str(text), quote=True)


def _link(url, text):
    """An external link, or just the text when the URL is missing or not http(s)."""
    if url and str(url).startswith(("https://", "http://")):
        return f'<a href="{_e(url)}" target="_blank" rel="noopener">{_e(text)}</a>'
    return _e(text)


def toc(items):
    """Contents list. items: [(anchor, label, level)] with level 0 (section) or 1 (sub-item)."""
    rows = "".join(f'<li class="l{lvl}"><a href="#{_e(anchor)}">{_e(label)}</a></li>' for anchor, label, lvl in items)
    return f'<nav class="fsm-toc" aria-label="Contents"><div class="fsm-eyebrow">Contents</div><ul>{rows}</ul></nav>'


def heading(anchor, text, level=2):
    """A section heading with an anchor id (scroll offset set in the CSS)."""
    return f'<h{level} class="fsm-mh fsm-mh{level}" id="{_e(anchor)}">{_e(text)}</h{level}>'


def anchor_only(anchor):
    """An invisible anchor for an entry that has no heading of its own."""
    return f'<div class="fsm-anchor" id="{_e(anchor)}"></div>'


def source_row(row):
    """One company figure: label and value, status line with the document link, quote and note in a toggle."""
    meta = [f'<span class="fsm-status s-{_e(row["status"])}">{_e(row["status"])}</span>']
    if row.get("period"):
        meta.append(_e(row["period"]))
    if row.get("as_of"):
        meta.append(f'as of {_e(row["as_of"])}')
    if row.get("document"):
        doc = _link(row.get("url"), row["document"])
        if row.get("page"):
            doc += f', {_e(row["page"])}'
        if row.get("url_note"):
            doc += f' <span class="fsm-faint">({_e(row["url_note"])})</span>'
        meta.append(doc)
    elif row.get("url"):
        meta.append(_link(row["url"], "link"))
    detail = ""
    parts = []
    if row.get("quote"):
        parts.append(f'<p class="fsm-quote">&ldquo;{_e(row["quote"])}&rdquo;</p>')
    if row.get("note"):
        parts.append(f'<p class="fsm-faint">{_e(row["note"])}</p>')
    parts.append(f'<p class="fsm-faint">{_e(row["status_text"]).capitalize()}.</p>')
    if parts:
        detail = f'<details><summary>Quote and note</summary>{"".join(parts)}</details>'
    return (f'<div class="fsm-srow"><div class="fsm-srow-main"><span class="fsm-srow-label">{_e(row["label"])}</span>'
            f'<span class="fsm-srow-value">{_e(row["value"])}</span></div>'
            f'<div class="fsm-srow-meta">{" · ".join(meta)}</div>{detail}</div>')


def assumption_card(row):
    """One entry of the assumptions register, with the anchor the source markers point to."""
    def item(term, text):
        return f"<dt>{_e(term)}</dt><dd>{_e(text)}</dd>"
    return (f'<article class="fsm-assume" id="{_e(row["id"].lower())}"><header><span class="fsm-assume-id">'
            f'{_e(row["id"])}</span><span class="fsm-faint">{_e(row["group"])} · {_e(row["level"])}</span></header>'
            f'<p class="fsm-assume-what">{_e(row["what"])}</p><dl>'
            f'{item("Why", row["why"])}{item("Used in", row["where"])}{item("If it is wrong", row["sensitivity"])}'
            f'</dl></article>')


def feed_row(feed, anchor=None):
    """A market-data feed; the first row of each feed carries the anchor the source markers point to."""
    ident = f' id="{_e(anchor)}"' if anchor else ""
    return (f'<div class="fsm-srow"{ident}><div class="fsm-srow-main"><span class="fsm-srow-label">'
            f'{_link(feed["url"], feed["name"])}</span></div>'
            f'<div class="fsm-srow-meta"><span class="fsm-status s-found">level {_e(feed["level"])}</span> · '
            f'{_e(feed["use"])}</div></div>')


def verdict_table(verdicts):
    """News sources: source, verdict (word, not colour alone) and reason."""
    rows = "".join(
        f'<div class="fsm-verdict"><div class="fsm-verdict-source">{_e(src)}</div>'
        f'<div><span class="fsm-status v-{_e(v.replace(" ", "-"))}">{_e(v)}</span></div>'
        f'<div class="fsm-verdict-why">{_e(why)}</div></div>' for src, v, why in verdicts)
    return f'<div class="fsm-verdicts">{rows}</div>'


def bullet_list(items):
    return "<ul class=\"fsm-list\">" + "".join(f"<li>{_e(i)}</li>" for i in items) + "</ul>"


def back_link(href, text):
    return f'<a class="fsm-skip" href="{_e(href)}">&larr; {_e(text)}</a>'


# A source marker opens this page in a NEW TAB with #anchor. Streamlit does not scroll to an anchor on a fresh load
# (the content below the top is still being built), so this small static script keeps scrolling to the anchor while
# the page fills in and stops the moment the reader scrolls or presses a key. No data is interpolated into it.
SCROLL_TO_HASH_JS = """
(function () {
  var id = decodeURIComponent((location.hash || "").slice(1));
  if (!id) { return; }
  var stopped = false, tries = 0;
  function stop() { stopped = true; }
  ["wheel", "touchstart", "keydown", "mousedown"].forEach(function (name) {
    window.addEventListener(name, stop, { once: true, passive: true });
  });
  var timer = setInterval(function () {
    var el = document.getElementById(id);
    if (el && !stopped) { el.scrollIntoView({ block: "start" }); }
    if (stopped || ++tries > 80) { clearInterval(timer); }
  }, 250);
})();
"""


def scroll_to_hash():
    """The script element (render with st.html(..., unsafe_allow_javascript=True))."""
    return f"<script>{SCROLL_TO_HASH_JS}</script>"
