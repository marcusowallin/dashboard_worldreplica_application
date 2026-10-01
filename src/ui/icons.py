"""Our own 7x7 dot-grid icons (DESIGN_BRIEF.md section 4) - simple shapes drawn in code, one per story step.

Each icon is 7 rows of 7 characters: '#' = lit dot, '.' = faint grid dot. Decorative only
(aria-hidden): the step label always says in words what the step is about.
"""
from base64 import b64encode

from src.ui.theme import COLORS

BITMAPS = {
    "price": ("......#", ".....#.", "....#..", ".#.#...", "#.#....", ".......", "#######"),
    "split": ("#.....#", ".#...#.", "..#.#..", "...#...", "...#...", "...#...", "...#..."),
    "volume": (".#####.", "#.....#", ".#####.", "#.....#", ".#####.", "#.....#", ".#####."),
    "euro": ("..####.", ".#.....", "#####..", ".#.....", "#####..", ".#.....", "..####."),
    "fare": ("####...", "#...#..", "#.#..#.", "#.....#", ".#...#.", "..#.#..", "...#..."),
    "gauge": (".......", "..###..", ".#...#.", "#..#..#", "#...#.#", "#.....#", ".#####."),
    "compare": ("...#...", "#######", "#..#..#", "#..#..#", "##.#.##", "...#...", ".#####."),
    "flag": ("#......", "####...", "#####..", "####...", "#......", "#......", "#......"),
    "tornado": ("#######", ".#####.", ".#####.", "..###..", "..###..", "...#...", "...#..."),
    "sliders": (".#.....", "#######", ".#.....", ".......", "....#..", "#######", "....#.."),
    "news": ("#######", "#.....#", "#.###.#", "#.....#", "#.###.#", "#.....#", "#######"),
}


def icon_svg(name, color=COLORS["accent"], size=28):
    """Standalone SVG for one icon. Raises KeyError for an unknown name (a typo should fail loudly)."""
    rows = BITMAPS[name]
    dots = []
    for y, row in enumerate(rows):
        for x, cell in enumerate(row):
            fill, opacity = (color, 1) if cell == "#" else (COLORS["text_3"], 0.18)
            dots.append(f'<circle cx="{x + 0.5}" cy="{y + 0.5}" r="0.3" fill="{fill}" opacity="{opacity}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 7 7">'
            f'{"".join(dots)}</svg>')


def icon_img(name, color=COLORS["accent"], size=28):
    """The icon as an <img> with a data URI - st.html strips inline <svg>, but keeps images.

    alt="" marks it as decorative for screen readers (the step label says the same in words).
    """
    data = b64encode(icon_svg(name, color, size).encode()).decode()
    return (f'<img class="fsm-icon" src="data:image/svg+xml;base64,{data}" width="{size}" height="{size}" '
            f'alt="" aria-hidden="true">')
