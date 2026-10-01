"""Design tokens (DESIGN_BRIEF.md sections 2-3): one place for colours, fonts and airline labels.

.streamlit/config.toml repeats the base colours for Streamlit's own widgets - change both together.
Colour never carries meaning alone: every airline is also named in text, "Lufthansa (us)".
"""

COLORS = {
    "bg": "#0B0C10",          # page
    "surface": "#111318",     # cards, chart plot area
    "surface_2": "#171A20",   # hero panel, toggles
    "line": "#262930",        # card borders, dividers
    "grid": "#1D2027",        # chart gridlines, dot grid
    "text": "#F3F4F6",        # headlines, numbers
    "text_2": "#A9ADB5",      # body
    "text_3": "#80858E",      # labels, captions, "STEP n"
    "accent": "#2DD4E0",      # Lufthansa = us, rail, buttons
    "peer_a": "#9D92D8",      # Air France-KLM
    "peer_b": "#D3A35E",      # IAG
    "range": "#4A4F5A",       # range whiskers / bands
    "cost_up": "#F07A6E",     # unfavourable (always with sign + word)
    "cost_down": "#5CCB8A",   # favourable (same rule)
    "warn": "#E8C35A",        # confidence LOW / MEDIUM, "depends"
}

FONTS = {
    "text": "Inter, system-ui, sans-serif",
    "heading": "Manrope, Inter, system-ui, sans-serif",
    "mono": "'JetBrains Mono', ui-monospace, monospace",
}

AIRLINE_COLORS = {"lufthansa": COLORS["accent"], "afklm": COLORS["peer_a"], "iag": COLORS["peer_b"]}
AIRLINE_LABELS = {"lufthansa": "Lufthansa (us)", "afklm": "Air France-KLM", "iag": "IAG"}
AIRLINE_SHORT = {"lufthansa": "Lufthansa", "afklm": "Air France-KLM", "iag": "IAG"}


def _luminance(hex_color):
    """Relative luminance (WCAG 2.x) of a #RRGGBB colour."""
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground, background):
    """WCAG contrast ratio between two #RRGGBB colours (1 to 21). AA body text needs >= 4.5."""
    lighter, darker = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def hex_to_rgba(hex_color, alpha):
    """'#2DD4E0', 0.1 -> 'rgba(45,212,224,0.1)' (for glows and translucent fills)."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha})"
