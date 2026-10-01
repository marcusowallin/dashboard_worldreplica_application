"""One Plotly template for every chart (design notes) plus the story's chart builders.

Rules: transparent paper, surface plot area, thin gridlines, Inter, accent for Lufthansa (us), muted peers,
grey for ranges, direct labels instead of legends. Chart builders take numbers that were already computed by
the model / src/story - they never compute anything themselves.
"""
import plotly.graph_objects as go
import plotly.io as pio

from src.ui.format import pct, pct_range, story_pct, story_pct_range
from src.ui.theme import AIRLINE_COLORS, AIRLINE_SHORT, COLORS, hex_to_rgba

TEMPLATE = "fsm"
# pass to st.plotly_chart(config=CONFIG). No zoom of any kind: dragging a rectangle zooms in with no way back, and the
# mouse wheel must keep scrolling the page. Hover tooltips stay.
CONFIG = {"displayModeBar": False, "responsive": True, "scrollZoom": False, "doubleClick": False}
FACTOR_LABELS = {"recapture": "pass-through", "profit base": "margin cushion", "hedge ratio": "hedge cover",
                 "hedge quality": "hedge quality (peers' mix unknown)"}
FACTOR_COLORS = {"recapture": COLORS["accent"], "profit base": COLORS["peer_b"],
                 "hedge ratio": COLORS["peer_a"], "hedge quality": COLORS["range"]}


def lock_zoom(fig):
    """No drag-to-zoom or pan on any axis (a rectangle zoom has no way back). Set on the figure itself, not only in the
    template, because Streamlit's own chart theme can replace the template in the browser. Returns the figure."""
    fig.update_layout(dragmode=False)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def plot(fig):
    """Show a chart the way every chart on the pages is shown: zoom locked, shared config, hover tooltips kept."""
    import streamlit as st
    st.plotly_chart(lock_zoom(fig), config=CONFIG)


def register_template():
    """Register the 'fsm' template and make it the default. Safe to call more than once."""
    axis = dict(gridcolor=COLORS["grid"], linecolor=COLORS["line"], zerolinecolor=COLORS["line"],
                tickfont=dict(color=COLORS["text_3"], size=12), title_font=dict(color=COLORS["text_3"], size=12),
                ticks="", showline=False, fixedrange=True)
    pio.templates[TEMPLATE] = go.layout.Template(layout=dict(
        font=dict(family="Inter, system-ui, sans-serif", size=13, color=COLORS["text_2"]),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=COLORS["surface"],
        colorway=[COLORS["accent"], COLORS["peer_a"], COLORS["peer_b"], COLORS["range"]],
        xaxis=axis, yaxis=axis, showlegend=False, margin=dict(l=8, r=8, t=8, b=8), dragmode=False,
        hoverlabel=dict(bgcolor=COLORS["surface_2"], bordercolor=COLORS["line"],
                        font=dict(family="Inter, system-ui, sans-serif", color=COLORS["text"])),
        separators=".,",
    ))
    pio.templates.default = TEMPLATE
    return TEMPLATE


def range_bars(rows, axis_title):
    """Horizontal range bars, one per airline, Lufthansa first; the airline name sits above its bar.

    rows: list of {"airline", "low", "high", "ext_high" (optional wider end, drawn lighter)} as fractions.
    The solid part is the main range; the light extension is the wider case (e.g. pass-through down to 50%).
    Names are annotations (not y tick labels), so no left margin is needed and phones keep the full width.
    """
    register_template()
    fig = go.Figure()
    for i, r in enumerate(rows):
        name, color, ext = _axis_name(r["airline"]), AIRLINE_COLORS[r["airline"]], r.get("ext_high")
        if ext is not None and ext > r["high"]:
            fig.add_trace(go.Bar(y=[i], x=[(ext - r["high"]) * 100], base=[r["high"] * 100], orientation="h",
                                 marker=dict(color=hex_to_rgba(color, 0.25), line=dict(width=0)), width=0.34,
                                 hovertemplate=f"{name}: up to {pct(ext)} in the wider case<extra></extra>"))
        fig.add_trace(go.Bar(y=[i], x=[max(r["high"] - r["low"], 0.002) * 100], base=[r["low"] * 100],
                             orientation="h", marker=dict(color=color, line=dict(width=0)), width=0.34,
                             hovertemplate=f"{name}: {pct_range(r['low'], r['high'])}<extra></extra>"))
        fig.add_annotation(y=i, x=0, xref="paper", xshift=2, yshift=19, xanchor="left", align="left", showarrow=False, text=name,
                           font=dict(color=COLORS["text"], size=13))
        label = story_pct_range(r["low"], r["high"]) + (f" · up to {story_pct(ext)} at 50% pass-through"
                                                        if ext is not None and ext > r["high"] else "")
        fig.add_annotation(y=i, x=max(ext or 0, r["high"]) * 100, text=label,
                           xanchor="left", align="left", xshift=6, showarrow=False, font=dict(color=COLORS["text"], size=13))
    top = max(max(r.get("ext_high") or 0, r["high"]) for r in rows) * 100
    fig.update_layout(barmode="overlay", height=50 + 64 * len(rows), margin=dict(l=10, r=4, t=14, b=8),
                      xaxis=dict(title=axis_title, range=[0, top * 1.9], ticksuffix="%"),
                      yaxis=dict(visible=False, autorange="reversed"))
    return fig


def contribution_bars(rows, axis_title):
    """Gap to a peer split into drivers (stacked, diverging around zero), one bar per peer.

    rows: list of {"peer", "parts": {factor: pp as fraction}}; positive = the factor makes Lufthansa lose more.
    """
    register_template()
    fig = go.Figure()
    for factor, color in FACTOR_COLORS.items():
        values = [r["parts"].get(factor, 0) * 100 for r in rows]
        name = FACTOR_LABELS[factor]
        fig.add_trace(go.Bar(y=list(range(len(rows))), x=values, name=name, orientation="h",
                             marker=dict(color=color), width=0.38,
                             hovertemplate=f"{name}: %{{x:+.1f}} pp<extra></extra>"))
    for i, r in enumerate(rows):
        fig.add_annotation(y=i, x=0, xref="paper", xshift=2, yshift=21, xanchor="left", align="left", showarrow=False,
                           text=f"vs {AIRLINE_SHORT[r['peer']]}", font=dict(color=COLORS["text"], size=13))
    fig.update_layout(barmode="relative", height=110 + 72 * len(rows), showlegend=True,
                      margin=dict(l=10, r=4, t=8, b=8),
                      legend=dict(orientation="h", yanchor="bottom", y=1.04, x=0, xanchor="left", entrywidth=0.5,
                                  entrywidthmode="fraction", font=dict(color=COLORS["text_2"], size=12)),
                      xaxis=dict(title=axis_title, ticksuffix=" pp", zeroline=True, zerolinewidth=1),
                      yaxis=dict(visible=False, autorange="reversed"))
    return fig


def _axis_name(airline):
    return f"{AIRLINE_SHORT[airline]} (us)" if airline == "lufthansa" else AIRLINE_SHORT[airline]


# --- D3: steps 1-3 ---------------------------------------------------------------------------------
SEGMENT_COLORS = {"protected": COLORS["cost_down"], "premium_open": COLORS["warn"],
                  "undisclosed": COLORS["range"], "unhedged": COLORS["cost_up"]}
SEGMENT_LABELS = {"protected": "hedged, protected", "premium_open": "hedged, premium open",
                  "undisclosed": "hedged, mix unknown", "unhedged": "unhedged"}


def price_lines(prices, baseline_day, scenario_move):
    """Step 1: jet fuel and Brent in USD/t since mid-July, 27 July marked, the scenario move as a band.

    prices: {date: (jet, brent, crack)} USD/t (src/data_sources.daily_prices_per_t).
    """
    register_template()
    days = sorted(prices)
    jet, brent = [prices[d][0] for d in days], [prices[d][1] for d in days]
    base = max(d for d in days if d <= baseline_day)
    base_jet = prices[base][0]
    fig = go.Figure()
    fig.add_hrect(y0=base_jet, y1=base_jet + scenario_move, x0=base, x1=days[-1], line_width=0,
                  fillcolor=hex_to_rgba(COLORS["warn"], 0.2))
    fig.add_annotation(x=base, y=base_jet + scenario_move, xanchor="left", align="left", yanchor="bottom", showarrow=False,
                       text=f"scenario: {'+' if scenario_move >= 0 else chr(0x2212)}USD {abs(scenario_move):,.0f}/t", font=dict(color=COLORS["warn"], size=12))
    fig.add_trace(go.Scatter(x=days, y=jet, mode="lines", line=dict(color=COLORS["text"], width=2),
                             hovertemplate="Jet fuel %{x|%d %b}: USD %{y:,.0f}/t<extra></extra>"))
    fig.add_trace(go.Scatter(x=days, y=brent, mode="lines", line=dict(color=COLORS["text_3"], width=2, dash="dot"),
                             hovertemplate="Brent %{x|%d %b}: USD %{y:,.0f}/t<extra></extra>"))
    fig.add_vline(x=base, line=dict(color=COLORS["accent"], width=1, dash="dash"))
    fig.add_annotation(x=base, y=1, yref="paper", xanchor="left", align="left", yanchor="top", showarrow=False,
                       text=f" {base:%d %b}", font=dict(color=COLORS["accent"], size=12))
    for series, values, color in (("Jet fuel", jet, COLORS["text"]), ("Brent", brent, COLORS["text_3"])):
        fig.add_annotation(x=days[-1], y=values[-1], xanchor="right", yanchor="bottom", showarrow=False, yshift=4,
                           text=f"{series} {values[-1]:,.0f}", font=dict(color=color, size=12))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10),
                      yaxis=dict(title="USD per tonne", tickformat=",.0f"), xaxis=dict(tickformat="%d %b"))
    return fig


def split_bars(rows):
    """Step 2: crude vs jet premium per row. rows: list of {"label", "brent", "crack"} in USD/t."""
    register_template()
    fig = go.Figure()
    labels = list(range(len(rows)))
    for key, name, color in (("brent", "crude (Brent)", COLORS["text_3"]), ("crack", "jet premium", COLORS["warn"])):
        values = [r[key] for r in rows]
        fig.add_trace(go.Bar(y=labels, x=values, name=name, orientation="h", width=0.42, marker=dict(color=color),
                             text=[f"{name} {v:+,.0f}" for v in values], textposition="inside",
                             insidetextanchor="middle", textfont=dict(color=COLORS["bg"], size=12),
                             hovertemplate=f"{name}: %{{x:+,.0f}} USD/t<extra></extra>"))
    for i, r in enumerate(rows):
        fig.add_annotation(y=i, x=0, xref="paper", xshift=2, yshift=21, xanchor="left", align="left", showarrow=False,
                           text=f"{r['label']}: {r['brent'] + r['crack']:+,.0f} USD/t",
                           font=dict(color=COLORS["text"], size=13))
    fig.update_layout(barmode="relative", height=70 + 70 * len(rows), margin=dict(l=10, r=4, t=14, b=8),
                      uniformtext=dict(minsize=11, mode="hide"),
                      xaxis=dict(title="USD per tonne since 27 Jul", zeroline=True),
                      yaxis=dict(visible=False, autorange="reversed"))
    return fig


def exposure_bars(rows):
    """Step 3: tonnes per airline and period, stacked by what the hedges cover.

    rows: list of {"airline", "label", "protected", "premium_open", "undisclosed", "unhedged"} in tonnes
    (None or 0 where a block does not apply).
    """
    register_template()
    fig = go.Figure()
    ys = list(range(len(rows)))
    for key in ("protected", "premium_open", "undisclosed", "unhedged"):
        values = [(r.get(key) or 0) / 1e6 for r in rows]
        if not any(values):
            continue
        fig.add_trace(go.Bar(y=ys, x=values, name=SEGMENT_LABELS[key], orientation="h", width=0.5,
                             marker=dict(color=SEGMENT_COLORS[key],
                                         pattern=dict(shape="/" if key == "undisclosed" else "",
                                                      fgcolor=COLORS["text_3"], size=6)),
                             hovertemplate=f"{SEGMENT_LABELS[key]}: %{{x:.1f}}m t<extra></extra>"))
    for i, r in enumerate(rows):
        fig.add_annotation(y=i, x=0, xref="paper", xshift=2, yshift=19, xanchor="left", align="left", showarrow=False,
                           text=r["label"], font=dict(color=COLORS["text"], size=12))
    fig.update_layout(barmode="stack", height=90 + 56 * len(rows), showlegend=True, margin=dict(l=10, r=4, t=8, b=8),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, xanchor="left", entrywidth=0.5,
                                  entrywidthmode="fraction", traceorder="normal",
                                  font=dict(color=COLORS["text_2"], size=12)),
                      xaxis=dict(title="million tonnes of jet fuel"), yaxis=dict(visible=False, autorange="reversed"))
    return fig


def split_history(stats, today=None):
    """Step 2: how past large jet fuel moves split between crude and the jet premium.

    A histogram of the crude share of every large move in the lookback (bars), the middle half of them (shaded), the
    median (dashed - the scenario's split) and today's move since 27 July (solid). Time is not shown: the question is
    whether today's split is a usual one, not when the old ones happened. Shares are clipped to -50%..150% for display
    (the bars at the edges collect everything beyond; the hover says so).

    stats: src/story/price_split.benchmark_split output; today: {"day", "share", "d_jet"} or None.
    """
    register_template()
    fig = go.Figure()
    clip = lambda v: max(-50.0, min(150.0, v * 100))      # noqa: E731
    fig.add_trace(go.Histogram(
        x=[clip(e["crude_share"]) for e in stats["episodes"]], xbins=dict(start=-60, end=160, size=20),
        marker=dict(color=hex_to_rgba(COLORS["text_2"], 0.55), line=dict(color=COLORS["bg"], width=1)),
        hovertemplate="%{y} large moves with a crude share of about %{x}% (edge bars include anything beyond)"
                      "<extra></extra>"))
    labels = []
    if not stats["fallback"]:
        fig.add_vrect(x0=stats["q1"] * 100, x1=stats["q3"] * 100, line_width=0, layer="below",
                      fillcolor=hex_to_rgba(COLORS["text_3"], 0.18))
        fig.add_vline(x=clip(stats["median"]), line=dict(color=COLORS["warn"], width=2, dash="dash"))
        labels.append((clip(stats["median"]), f"median {stats['median'] * 100:.0f}% = the scenario split",
                       COLORS["warn"]))
    if today and today.get("share") is not None:
        fig.add_vline(x=clip(today["share"]), line=dict(color=COLORS["accent"], width=3))
        labels.append((clip(today["share"]), f"today {today['share'] * 100:.0f}%", COLORS["accent"]))
    # one label above each line, pointing away from the other so they never collide
    for i, (x, text, color) in enumerate(sorted(labels)):
        fig.add_annotation(x=x, y=1, yref="paper", yanchor="bottom", showarrow=False,
                           xanchor="right" if (i == 0 and len(labels) == 2) else "left" if len(labels) == 2 else "center",
                           xshift=-6 if (i == 0 and len(labels) == 2) else 6 if len(labels) == 2 else 0,
                           text=text, font=dict(color=color, size=13))
    fig.update_layout(height=300, showlegend=False, bargap=0.08, margin=dict(l=10, r=10, t=34, b=10),
                      yaxis=dict(title="large moves", rangemode="tozero", dtick=2),
                      xaxis=dict(title="crude share of the move (shaded: the middle half of past moves; the end bars include anything beyond)",
                                 range=[-60, 160], tickvals=[-50, 0, 50, 100, 150], ticksuffix="%"))
    return fig


# --- D4: steps 4-5 ---------------------------------------------------------------------------------
def range_rows(rows, axis_title, height_per_row=50):
    """Horizontal range rows: a solid bar from 0 to the low end, a lighter extension to the high end, a label
    above each bar and the formatted range at its end. Optional light marks (e.g. the 50% pass-through case).

    rows: list of {"label", "low", "high", "color", "text", "marks": (low, high) or None, "mark_text"} in EUR m
    (or any unit - the chart only draws what it is given).
    """
    register_template()
    fig = go.Figure()
    for i, r in enumerate(rows):
        fig.add_trace(go.Bar(y=[i], x=[r["low"]], orientation="h", width=0.42, marker=dict(color=r["color"]),
                             hovertemplate=f"{r['label']}: {r['text']}<extra></extra>"))
        if r["high"] > r["low"]:
            fig.add_trace(go.Bar(y=[i], x=[r["high"] - r["low"]], base=[r["low"]], orientation="h", width=0.42,
                                 marker=dict(color=hex_to_rgba(r["color"], 0.35)),
                                 hovertemplate=f"{r['label']}: {r['text']}<extra></extra>"))
        fig.add_annotation(y=i, x=0, xref="paper", xshift=2, yshift=18, xanchor="left", align="left", showarrow=False,
                           text=r["label"], font=dict(color=COLORS["text"], size=12))
        end = max(r["high"], (r.get("marks") or (0, 0))[1])
        fig.add_annotation(y=i, x=end, xanchor="left", align="left", xshift=10, showarrow=False, text=r["text"],
                           font=dict(color=COLORS["text_2"], size=12))
        if r.get("marks"):
            lo, hi = r["marks"]
            fig.add_trace(go.Scatter(x=[lo, hi], y=[i, i], mode="lines+markers",
                                     line=dict(color=COLORS["text_3"], width=1, dash="dot"),
                                     marker=dict(symbol="diamond-open", size=10, color=COLORS["text_2"]),
                                     hovertemplate=f"{r.get('mark_text', '')}<extra></extra>"))
    top = max(max(r["high"], (r.get("marks") or (0, 0))[1]) for r in rows)
    fig.update_layout(barmode="overlay", height=40 + height_per_row * len(rows), margin=dict(l=10, r=10, t=14, b=8),
                      xaxis=dict(title=axis_title, range=[0, top * 1.35], tickformat=",.0f"),
                      yaxis=dict(visible=False, autorange="reversed"))
    return fig


def tornado_bars(result, top_n=6, key=("low", "high"), base_key="base_gap", axis_title=""):
    """Step 9: horizontal bars from the low to the high end of each assumption, around the base value (line).
    Labels above each bar; the end values at its ends. result = src/story/tornado.tornado(...)."""
    register_template()
    fig = go.Figure()
    bars = result["bars"][:top_n]
    base = result[base_key] * 100
    for i, b in enumerate(bars):
        lo, hi = b[key[0]] * 100, b[key[1]] * 100
        fig.add_trace(go.Bar(y=[i], x=[max(hi - lo, 0.02)], base=[lo], orientation="h", width=0.45,
                             marker=dict(color=COLORS["accent"] if i == 0 else COLORS["text_3"]),
                             hovertemplate=f"{b['label']}: {lo:.1f} to {hi:.1f} pp<extra></extra>"))
        fig.add_annotation(y=i, x=0, xref="paper", xshift=2, yshift=19, xanchor="left", align="left", showarrow=False,
                           text=b["label"], font=dict(color=COLORS["text"], size=12))
        fig.add_annotation(y=i, x=hi, xanchor="left", align="left", xshift=6, showarrow=False,
                           text=f"{lo:.1f} to {hi:.1f} pp", font=dict(color=COLORS["text_2"], size=12))
    fig.add_vline(x=base, line=dict(color=COLORS["warn"], width=1, dash="dash"))
    fig.add_annotation(x=base, y=1, yref="paper", yanchor="bottom", showarrow=False, text=f"base {base:.1f} pp",
                       font=dict(color=COLORS["warn"], size=11))
    lo_all = min(b[key[0]] for b in bars) * 100
    hi_all = max(b[key[1]] for b in bars) * 100
    fig.update_layout(barmode="overlay", height=60 + 52 * len(bars), margin=dict(l=10, r=10, t=24, b=8),
                      xaxis=dict(title=axis_title, range=[min(0, lo_all) - 0.5, hi_all + (hi_all - min(0, lo_all)) * 0.45],
                                 ticksuffix=" pp", zeroline=True),
                      yaxis=dict(visible=False, autorange="reversed"))
    return fig
