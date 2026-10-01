"""Page CSS for the story (design notes). Injected once per page with inject().

Hooks: Streamlit's data-testid attributes and keyed containers (st.container(key="step-01") gets the class
"st-key-step-01"). Our own HTML uses "fsm-" classes. No JavaScript: the active-step highlight uses CSS
scroll-driven animations where the browser supports them and is simply absent elsewhere.
"""
from src.ui.theme import COLORS, FONTS, hex_to_rgba


def root_variables():
    """CSS custom properties from the design tokens (single source: src/ui/theme.py)."""
    lines = [f"  --fsm-{name.replace('_', '-')}: {value};" for name, value in COLORS.items()]
    lines += [f"  --fsm-font-{name}: {value};" for name, value in FONTS.items()]
    lines.append(f"  --fsm-glow: {hex_to_rgba(COLORS['accent'], 0.10)};")
    return ":root {\n" + "\n".join(lines) + "\n}"


RULES = """
/* ---- page frame ---------------------------------------------------------------------------- */
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { max-width: 980px; padding-top: 3rem; padding-bottom: 5rem; }
.stApp { background: var(--fsm-bg); }
body, .stApp { font-feature-settings: "tnum" 1, "cv11" 1; }
h1, h2, h3, .fsm-heading { font-family: var(--fsm-font-heading); letter-spacing: -0.01em; }

/* ---- small building blocks ---------------------------------------------------------------- */
.fsm-eyebrow { font-family: var(--fsm-font-mono); font-size: 12px; letter-spacing: .08em;
  text-transform: uppercase; color: var(--fsm-text-3); }
.fsm-eyebrow .fsm-step-no { color: var(--fsm-accent); }
.fsm-muted { color: var(--fsm-text-2); }
.fsm-label { color: var(--fsm-text-3); font-size: 13px; }
.fsm-us-tag { font-family: var(--fsm-font-mono); font-size: 11px; color: var(--fsm-bg);
  background: var(--fsm-accent); border-radius: 4px; padding: 1px 5px; margin-left: 6px; vertical-align: 2px; }
.fsm-src { font-family: var(--fsm-font-mono); font-size: 10px; margin-left: 2px; }
.fsm-src a { color: var(--fsm-text-3); text-decoration: none; border-bottom: 1px dotted var(--fsm-text-3); }
.fsm-step-title .fsm-src, .fsm-hero-sentence .fsm-src { font-size: 10px; font-weight: 500; margin-left: 3px; }
.fsm-src a:hover, .fsm-src a:focus { color: var(--fsm-accent); border-color: var(--fsm-accent); }
.fsm-skip { font-size: 14px; color: var(--fsm-text-2); text-decoration: none; }
.st-key-step-news::before, .st-key-step-news::after { display: none; }
.fsm-hook { font-family: var(--fsm-font-heading); font-size: 34px; line-height: 1.2; font-weight: 700; margin: 6px 0 14px;
  max-width: 24em; }
.fsm-hook-body { color: var(--fsm-text-2); font-size: 17px; line-height: 1.6; max-width: 62ch; margin: 0 0 10px; }
.fsm-bridge { color: var(--fsm-text-2); font-size: 15px; line-height: 1.5; margin: 18px 0 0; padding-top: 12px;
  border-top: 1px dashed var(--fsm-line); }
.fsm-bridge::before { content: "Next → "; color: var(--fsm-accent); font-family: var(--fsm-font-mono);
  font-size: 12px; letter-spacing: .06em; text-transform: uppercase; }
.fsm-skip:hover, .fsm-skip:focus { color: var(--fsm-accent); }
.fsm-icon { flex: none; }

/* ---- chips (with an optional hover / tap note) --------------------------------------------- */
.fsm-chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 4px 0; }
.fsm-chip { position: relative; display: inline-flex; gap: 6px; align-items: baseline; padding: 5px 11px;
  border: 1px solid var(--fsm-line); border-radius: 999px; background: var(--fsm-surface);
  font-size: 13px; color: var(--fsm-text); white-space: nowrap; }
.fsm-chip .fsm-chip-label { font-family: var(--fsm-font-mono); font-size: 11px; letter-spacing: .06em;
  text-transform: uppercase; color: var(--fsm-text-3); }
.fsm-chip.warn { border-color: var(--fsm-warn); }
.fsm-chip.warn .fsm-chip-value { color: var(--fsm-warn); font-weight: 600; }
.fsm-chip[tabindex] { cursor: help; }
.fsm-chip[tabindex]:focus { outline: 2px solid var(--fsm-accent); outline-offset: 2px; }
.fsm-tip { display: none; position: absolute; left: 0; top: calc(100% + 8px); z-index: 60; width: min(320px, 80vw);
  white-space: normal; padding: 10px 12px; border: 1px solid var(--fsm-line); border-radius: 10px;
  background: var(--fsm-surface-2); color: var(--fsm-text-2); font-size: 13px; line-height: 1.45;
  box-shadow: 0 8px 24px rgba(0,0,0,.45); }
.fsm-chip:hover .fsm-tip, .fsm-chip:focus .fsm-tip, .fsm-chip:focus-within .fsm-tip { display: block; }
/* lift the whole column that holds an open note above its neighbours (e.g. the Update data button) */
[data-testid="stColumn"]:has(.fsm-chip:hover), [data-testid="stColumn"]:has(.fsm-chip:focus),
[data-testid="stElementContainer"]:has(.fsm-chip:hover), [data-testid="stElementContainer"]:has(.fsm-chip:focus) {
  position: relative; z-index: 50; }

/* ---- hero ------------------------------------------------------------------------------------ */
.st-key-hero { position: relative; padding: 32px 32px 24px; border: 1px solid var(--fsm-line);
  border-radius: 16px; background:
    radial-gradient(600px 300px at 0% 0%, var(--fsm-glow), transparent 70%), var(--fsm-surface-2); }
.fsm-hero-sentence { font-family: var(--fsm-font-heading); font-size: 28px; line-height: 1.3; font-weight: 600;
  color: var(--fsm-text); margin: 10px 0 12px; }
.fsm-hero-sentence em { font-style: normal; color: var(--fsm-accent); }
.fsm-hero-why { color: var(--fsm-text-2); font-size: 17px; line-height: 1.55; margin: 0 0 8px; }
.fsm-hero-line { color: var(--fsm-text-2); font-size: 15px; line-height: 1.5; margin: 8px 0; }
.fsm-hero-line.live { border-left: 2px solid var(--fsm-accent); padding-left: 12px; }
.fsm-asof { color: var(--fsm-text-3); font-size: 12px; line-height: 1.5; margin: 6px 0 0; }
.fsm-notice { color: var(--fsm-warn); font-size: 13px; margin: 6px 0; }

/* ---- three-number row -------------------------------------------------------------------- */
.fsm-numbers { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 20px 0 8px; }
.fsm-num { padding: 14px 16px 12px; border: 1px solid var(--fsm-line); border-radius: 12px;
  background: var(--fsm-surface); border-top: 3px solid var(--fsm-airline, var(--fsm-line)); }
.fsm-num .fsm-num-airline { font-size: 14px; color: var(--fsm-text-2); }
.fsm-num .fsm-num-value { white-space: nowrap; font-size: 28px; line-height: 1.1; font-weight: 600; color: var(--fsm-text);
  margin: 6px 0 4px; letter-spacing: -0.02em; }
.fsm-num.us .fsm-num-value { color: var(--fsm-accent); }
.fsm-num .fsm-num-sub { font-size: 17px; font-weight: 600; color: var(--fsm-text); margin: 0 0 6px; }
.fsm-num .fsm-num-caption { font-size: 13px; color: var(--fsm-text-3); line-height: 1.4; }

/* ---- story steps: dashed card, left rail, dot ------------------------------------------ */
[class*="st-key-step-"] { position: relative; margin: 0 0 28px 0; padding: 24px 24px 20px 64px;
  border: 1px dashed var(--fsm-line); border-radius: 14px; background: transparent; }
[class*="st-key-step-"]::before { content: ""; position: absolute; left: 31px; top: -29px; bottom: -29px;
  width: 1px; background: linear-gradient(var(--fsm-accent), var(--fsm-accent)); opacity: .55; }
[class*="st-key-step-"]::after { content: ""; position: absolute; left: 26px; top: 30px; width: 11px; height: 11px;
  border-radius: 50%; background: var(--fsm-bg); border: 2px solid var(--fsm-accent); box-sizing: border-box; }
.fsm-step-head { display: flex; gap: 14px; align-items: flex-start; }
.fsm-step-title { font-family: var(--fsm-font-heading); font-size: 25px; line-height: 1.3; font-weight: 700;
  color: var(--fsm-text); margin: 4px 0 6px; }
.fsm-step-body { color: var(--fsm-text-2); font-size: 16px; line-height: 1.55; max-width: 68ch; margin: 0; }
.fsm-anchor { position: relative; top: -80px; }

/* active step: accent outline + filled dot while the step is in the middle of the screen */
@supports (animation-timeline: view()) {
  [class*="st-key-step-"] { animation: fsm-step-active linear both; animation-timeline: view();
    animation-range: cover 20% cover 80%; }
  [class*="st-key-step-"]::after { animation: fsm-dot-active linear both; animation-timeline: view();
    animation-range: cover 20% cover 80%; }
}
@keyframes fsm-step-active { 0%, 100% { border-color: var(--fsm-line); border-style: dashed; }
  15%, 85% { border-color: var(--fsm-accent); border-style: solid; } }
@keyframes fsm-dot-active { 0%, 100% { background: var(--fsm-bg); } 15%, 85% { background: var(--fsm-accent); } }
@media (prefers-reduced-motion: reduce) {
  [class*="st-key-step-"], [class*="st-key-step-"]::after { animation: none !important; } }

/* ---- cards (airline ratio card, takeaway card) ---------------------------------------------- */
.fsm-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }
.fsm-cards.two { grid-template-columns: repeat(2, minmax(0, 1fr)); }
@media (max-width: 640px) { .fsm-cards.two { grid-template-columns: 1fr; } }
.fsm-card { padding: 16px; border: 1px solid var(--fsm-line); border-radius: 12px; background: var(--fsm-surface); }
.fsm-card.us { border-color: var(--fsm-accent); }
.fsm-card-title { font-weight: 600; color: var(--fsm-text); margin-bottom: 10px; display: flex; gap: 10px;
  align-items: center; }
.fsm-card-body { color: var(--fsm-text-2); font-size: 15px; line-height: 1.5; }
.fsm-card-sub { color: var(--fsm-text-3); font-size: 13px; margin: -6px 0 6px 32px; }
.fsm-card-number { font-size: 22px; line-height: 1.25; font-weight: 600; color: var(--fsm-accent); margin: 2px 0 8px; }
.fsm-card-note { color: var(--fsm-text-3); font-size: 13px; line-height: 1.45; margin-top: 10px; padding-top: 8px;
  border-top: 1px solid var(--fsm-line); }
.fsm-row { display: grid; grid-template-columns: 1fr auto; gap: 2px 12px; padding: 7px 0;
  border-top: 1px solid var(--fsm-line); font-size: 14px; }
.fsm-row .fsm-row-label { color: var(--fsm-text-3); }
.fsm-row .fsm-row-change { font-weight: 600; text-align: right; }
.fsm-row .fsm-row-ba { grid-column: 1 / -1; color: var(--fsm-text-2); }
.fsm-up { color: var(--fsm-cost-up); } .fsm-down { color: var(--fsm-cost-down); }

/* ---- buttons: arrow-box (native st.button with key "update-data" or "cta-*", and HTML links) --- */
.st-key-update-data button, [class*="st-key-cta-"] button, a.fsm-btn {
  position: relative; background: var(--fsm-text); color: var(--fsm-bg); border: 1px solid var(--fsm-text);
  border-radius: 10px; padding: 8px 54px 8px 16px; font-weight: 600; text-decoration: none;
  transition: background .3s ease, color .3s ease; }
.st-key-update-data button p, [class*="st-key-cta-"] button p { color: inherit; font-weight: 600; }
.st-key-update-data button::after, [class*="st-key-cta-"] button::after, a.fsm-btn::after {
  content: "\\2192"; position: absolute; right: 4px; top: 4px; bottom: 4px; width: 34px; display: grid;
  place-items: center; border-radius: 7px; background: var(--fsm-bg); color: var(--fsm-text);
  transition: color .3s ease; }
.st-key-update-data button:hover, [class*="st-key-cta-"] button:hover, a.fsm-btn:hover,
.st-key-update-data button:focus-visible, [class*="st-key-cta-"] button:focus-visible, a.fsm-btn:focus-visible {
  background: var(--fsm-bg); color: var(--fsm-text); border-color: var(--fsm-text); }
.st-key-update-data button:hover::after, [class*="st-key-cta-"] button:hover::after, a.fsm-btn:hover::after {
  color: var(--fsm-accent); }

/* ---- "How we calculated this" expander ---------------------------------------------------- */
[data-testid="stExpander"] details { border: 1px solid var(--fsm-line); border-radius: 10px;
  background: var(--fsm-surface); }
[data-testid="stExpander"] summary { font-size: 14px; color: var(--fsm-text-2); }

/* ---- news feed ---------------------------------------------------------------------------------- */
.fsm-news { padding: 12px 0; border-top: 1px solid var(--fsm-line); }
.fsm-news-head { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }
.fsm-news-title { color: var(--fsm-text); font-weight: 500; text-decoration: none; line-height: 1.4; }
a.fsm-news-title:hover { color: var(--fsm-accent); }
.fsm-news-step { flex: none; font-size: 13px; color: var(--fsm-accent); text-decoration: none; white-space: nowrap; }
.fsm-news-meta { font-size: 12px; color: var(--fsm-text-3); margin: 3px 0 6px; }
.fsm-news-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.fsm-news-tag { font-size: 12px; padding: 2px 8px; border: 1px solid var(--fsm-line); border-radius: 999px;
  color: var(--fsm-text-2); }
.fsm-news-tag.airline { color: var(--fsm-text); }
.fsm-news-tag.ok { color: var(--fsm-cost-down); border-color: var(--fsm-cost-down); cursor: help; }
.fsm-news-tag.warn { color: var(--fsm-warn); border-color: var(--fsm-warn); }
.fsm-news-tag.muted { color: var(--fsm-text-3); }
.fsm-news-tag.impact-negative .fsm-impact { color: var(--fsm-cost-up); }
.fsm-news-tag.impact-positive .fsm-impact { color: var(--fsm-cost-down); }
.fsm-news-tag.impact-neutral .fsm-impact { color: var(--fsm-text-3); }
.fsm-news-also { color: var(--fsm-text-2); }
.fsm-news-summary { color: var(--fsm-text-2); font-size: 14px; margin: 4px 0 10px; padding: 8px 12px;
  border-left: 2px solid var(--fsm-accent); }

/* ---- footer --------------------------------------------------------------------------------------- */
.fsm-footer { margin-top: 40px; padding-top: 24px; border-top: 1px solid var(--fsm-line); }
.fsm-footer-sources { color: var(--fsm-text-3); font-size: 13px; line-height: 1.6; padding-left: 18px; margin: 16px 0; }
.fsm-footer-note { color: var(--fsm-text-3); font-size: 13px; margin: 4px 0; }

/* ---- Method & sources page ------------------------------------------------------------------ */
.st-key-method-layout [data-testid="stHorizontalBlock"] { align-items: stretch !important; }
.st-key-method-layout [data-testid="stColumn"] > [data-testid="stVerticalBlock"] { height: 100%; }
/* Wide tables and long formulas scroll inside their own box instead of widening the whole page (seen at 375px). */
[data-testid="stMarkdownContainer"] table { display: block; max-width: 100%; overflow-x: auto; }
[data-testid="stMarkdownContainer"] .katex-display { overflow-x: auto; overflow-y: hidden; max-width: 100%; }
/* Streamlit wraps every keyed container in a layout wrapper as tall as the container: the WRAPPER must be sticky */
[data-testid="stLayoutWrapper"]:has(> .st-key-toc) { position: sticky; top: 4.5rem; align-self: flex-start; }
.fsm-toc ul { list-style: none; padding: 0; margin: 8px 0 0; }
.fsm-toc li { margin: 0; line-height: 1.35; }
.fsm-toc li a { display: block; padding: 3px 0 3px 10px; border-left: 1px solid var(--fsm-line);
  color: var(--fsm-text-2); text-decoration: none; font-size: 13px; }
.fsm-toc li.l1 a { padding-left: 22px; font-size: 12px; color: var(--fsm-text-3); }
.fsm-toc li a:hover, .fsm-toc li a:focus { color: var(--fsm-accent); border-left-color: var(--fsm-accent); }
.fsm-mh { font-family: var(--fsm-font-heading); color: var(--fsm-text); scroll-margin-top: 4.5rem; }
.fsm-mh2 { font-size: 26px; font-weight: 700; margin: 40px 0 8px; padding-top: 8px;
  border-top: 1px solid var(--fsm-line); }
.fsm-mh3 { font-size: 19px; font-weight: 600; margin: 26px 0 6px; }
.fsm-anchor, .fsm-srow[id], .fsm-assume, .fsm-verdicts[id] { scroll-margin-top: 4.5rem; }
:target { outline: 1px solid var(--fsm-accent); outline-offset: 4px; border-radius: 6px; }
.fsm-srow { padding: 9px 0; border-top: 1px solid var(--fsm-line); font-size: 14px; }
.fsm-srow-main { display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.fsm-srow-label { color: var(--fsm-text); font-weight: 500; }
.fsm-srow-value { font-variant-numeric: tabular-nums; color: var(--fsm-text); }
.fsm-srow-meta { color: var(--fsm-text-3); font-size: 12.5px; margin-top: 2px; line-height: 1.5; }
.fsm-srow a, .fsm-verdicts a, .fsm-assume a { color: var(--fsm-text-2); text-decoration-color: var(--fsm-text-3); }
.fsm-srow a:hover { color: var(--fsm-accent); }
.fsm-srow-label a { color: var(--fsm-text); }
.fsm-faint { color: var(--fsm-text-3); font-size: 12.5px; }
.fsm-quote { color: var(--fsm-text-2); font-size: 13px; margin: 6px 0 2px; }
.fsm-srow details { margin-top: 4px; }
.fsm-srow summary, .fsm-assume summary { cursor: pointer; font-size: 12.5px; color: var(--fsm-text-3); }
.fsm-srow summary:hover { color: var(--fsm-accent); }
.fsm-status { font-family: var(--fsm-font-mono); font-size: 11px; letter-spacing: .04em; padding: 1px 7px;
  border: 1px solid var(--fsm-line); border-radius: 999px; color: var(--fsm-text-2); white-space: nowrap; }
.fsm-status.s-found, .fsm-status.s-third-party { border-color: var(--fsm-warn); color: var(--fsm-warn); }
.fsm-status.s-verified, .fsm-status.v-in { border-color: var(--fsm-cost-down); color: var(--fsm-cost-down); }
.fsm-status.v-out { border-color: var(--fsm-cost-up); color: var(--fsm-cost-up); }
.fsm-status.v-on-request { border-color: var(--fsm-accent); color: var(--fsm-accent); }
.fsm-assume { margin: 10px 0; padding: 14px 16px; border: 1px solid var(--fsm-line); border-radius: 12px;
  background: var(--fsm-surface); }
.fsm-assume header { display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap; }
.fsm-assume-id { font-family: var(--fsm-font-mono); font-weight: 600; color: var(--fsm-accent); }
.fsm-assume-what { color: var(--fsm-text); font-size: 14.5px; line-height: 1.55; margin: 6px 0; }
.fsm-assume dl { margin: 6px 0 0; display: grid; grid-template-columns: 9rem 1fr; gap: 4px 12px; }
.fsm-assume dt { color: var(--fsm-text-3); font-size: 12.5px; }
.fsm-assume dd { margin: 0; color: var(--fsm-text-2); font-size: 13.5px; line-height: 1.5; }
.fsm-verdicts { margin: 8px 0; }
.fsm-verdict { display: grid; grid-template-columns: 1.3fr 7rem 2fr; gap: 6px 14px; padding: 9px 0;
  border-top: 1px solid var(--fsm-line); font-size: 14px; align-items: start; }
.fsm-verdict-source { color: var(--fsm-text); font-weight: 500; }
.fsm-verdict-why { color: var(--fsm-text-2); }
.fsm-list { color: var(--fsm-text-2); line-height: 1.55; padding-left: 20px; }
.fsm-list li { margin: 4px 0; }
.fsm-mp { color: var(--fsm-text-2); font-size: 15.5px; line-height: 1.6; max-width: 72ch; }

/* ---- phone ------------------------------------------------------------------------------------ */
@media (max-width: 640px) {
  [data-testid="stMainBlockContainer"] { padding-left: 16px; padding-right: 16px; padding-top: 2rem; }
  .st-key-hero { padding: 22px 18px 18px; }
  .fsm-hero-sentence { font-size: 22px; }
  .fsm-hook { font-size: 26px; }
  .fsm-numbers { grid-template-columns: 1fr; }
  .fsm-num .fsm-num-value { font-size: 28px; }
  [class*="st-key-step-"] { padding: 40px 16px 16px 16px; }
  [class*="st-key-step-"]::before { left: 22px; top: -29px; bottom: auto; height: 29px; }
  [class*="st-key-step-"]::after { left: 17px; top: -6px; }
  .fsm-step-title { font-size: 21px; }
  [data-testid="stLayoutWrapper"]:has(> .st-key-toc) { position: static; }
  .fsm-assume dl { grid-template-columns: 1fr; }
  .fsm-verdict { grid-template-columns: 1fr; }
  .fsm-mh2 { font-size: 22px; }
}
"""


def page_css():
    """The complete stylesheet (variables + rules)."""
    return root_variables() + RULES


def inject():
    """Add the stylesheet to the current Streamlit page (call once, near the top)."""
    import streamlit as st
    st.html(f"<style>{page_css()}</style>")
