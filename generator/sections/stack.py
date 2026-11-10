"""The stack as a periodic table: four category blocks, core elements glow."""

from __future__ import annotations

from ..fonts import fit_size
from ..svg import Doc, el, g, rr

W = 880
COLS, ROWS, GAP = 10, 4, 6
# periodic-table silhouette: which columns are present in each row
SHAPE = [
    {0, 9},
    {0, 1, 6, 7, 8, 9},
    set(range(10)),
    set(range(10)),
]


def layout(categories: list[dict], elements: list[dict]) -> list[tuple[int, int, dict]]:
    """Place each category's elements into its column block, row-major (first element top-left)."""
    placed = []
    for cat in categories:
        slots = [(r, c) for r in range(ROWS) for c in cat["cols"] if c in SHAPE[r]]
        items = [e for e in elements if e["cat"] == cat["key"]]
        if len(items) > len(slots):
            raise ValueError(f"category {cat['key']} has {len(items)} elements but {len(slots)} slots")
        placed += [(r, c, e) for (r, c), e in zip(slots, items)]
    return placed


def render(t, content: dict) -> str:
    st = content["stack"]
    cats = st["categories"]
    tile = (W - (COLS - 1) * GAP) / COLS
    H = round(ROWS * tile + (ROWS - 1) * GAP + 2)
    placed = layout(cats, st["elements"])
    order = sorted(placed, key=lambda p: (p[0], p[1]))
    number = {id(e): i + 1 for i, (_, _, e) in enumerate(order)}

    doc = Doc(W, H, "The periodic table of my stack",
              "; ".join(f"{c['label']}: " + ", ".join(e["name"] for e in st["elements"] if e["cat"] == c["key"])
                        for c in cats), t)
    doc.css(
        ".el{animation:el .7s cubic-bezier(.2,.8,.2,1) both}",
        "@keyframes el{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}",
        ".core{animation:glow 3.6s ease-in-out infinite}",
        "@keyframes glow{0%,100%{stroke-opacity:.55}50%{stroke-opacity:1}}",
    )
    parts = []
    for r, c, e in placed:
        x, y = c * (tile + GAP), r * (tile + GAP)
        color = t.accent[e["cat"]]
        core = e.get("core", False)
        size = fit_size(e["name"], "sans", 10.5, tile - 10)
        body = [
            rr(x + 0.5, y + 0.5, tile - 1, tile - 1, 10, fill=color, fill_opacity=0.16 if core else 0.07,
               stroke=color, stroke_opacity=0.55 if core else 0.28, stroke_width=1.5 if core else 1,
               class_="core" if core else None),
            doc.text(x + 9, y + 17, str(number[id(e)]), "mono", 10, t.ink3),
            doc.text(x + tile / 2, y + tile / 2 + 9, e["sym"], "sans-sb", 28, color if core else t.ink,
                     anchor="middle", tracking=-0.5),
            doc.text(x + tile / 2, y + tile - 11, e["name"], "sans", size, t.ink2, anchor="middle"),
        ]
        if core:
            body.append(el("circle", cx=x + tile - 12, cy=y + 13, r=3, fill=color))
        parts.append(g("".join(body), class_="el", style=f"animation-delay:{(r + c) * 0.045:.2f}s"))

    # title block in the gap of row 0, legend in the gap of row 1
    tx = tile + GAP + 18
    parts.append(doc.text(tx, 38, "The periodic table of my stack", "serif-i", 30, t.ink))
    parts.append(doc.text(tx, 62, f"{len(placed)} ELEMENTS · GROUPED BY WHAT THEY DO · CORE ELEMENTS GLOW", "mono", 10,
                          t.ink3, tracking=1))
    lx, ly = 2 * (tile + GAP) + 14, tile + GAP + 30
    for i, cat in enumerate(cats):
        cx, cy = lx + (i % 2) * 170, ly + (i // 2) * 28
        color = t.accent[cat["key"]]
        parts.append(rr(cx, cy - 10, 12, 12, 3, fill=color, fill_opacity=0.25, stroke=color))
        parts.append(doc.text(cx + 20, cy, cat["label"], "sans-m", 13, t.ink))
    doc.add(*parts)
    return doc.render()
