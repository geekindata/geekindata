"""Section headers: index, editorial serif title and a catalog-style table name."""

from __future__ import annotations

from ..fonts import face
from ..svg import Doc, el, g, rr

W, H = 880, 78
ACCENTS = ["data", "ai", "eng", "bi", "pink", "data", "ai", "eng"]


def render(t, index: int, title: str, table: str) -> str:
    name, _, cadence = table.partition(" · ")
    accent = t.accent[ACCENTS[(index - 1) % len(ACCENTS)]]
    doc = Doc(W, H, f"{index:02d} · {title}", f"Section {index}: {title}", t)
    seg = doc.uid("seg")
    doc.defs(el("linearGradient", el("stop", offset=0, stop_color=accent)
                + el("stop", offset=1, stop_color=accent, stop_opacity=0), id=seg))
    doc.css(
        ".grow{transform-box:fill-box;transform-origin:left;animation:grow 1.4s cubic-bezier(.2,.8,.2,1) both}",
        "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}",
        ".pulse{transform-box:fill-box;transform-origin:center;animation:pulse 2.2s ease-out infinite}",
        "@keyframes pulse{from{transform:scale(1);opacity:.7}to{transform:scale(3);opacity:0}}",
    )
    parts = [
        doc.text(0, 52, f"{index:02d}", "mono-m", 13, accent, tracking=1),
        doc.text(34, 54, title, "serif-i", 40, t.ink),
    ]
    right = W
    if cadence:
        label = cadence.upper()
        lw = face("mono-m").width(label, 10, 1.2)
        parts.append(doc.text(right, 50, label, "mono-m", 10, t.accent["ok"], anchor="end", tracking=1.2))
        cx = right - lw - 12
        parts += [el("circle", cx=cx, cy=46.5, r=3, fill=t.accent["ok"], class_="pulse"),
                  el("circle", cx=cx, cy=46.5, r=3, fill=t.accent["ok"])]
        right = cx - 16
    parts.append(doc.text(right, 50, name, "mono", 11.5, t.ink3, anchor="end", tracking=0.4))
    parts.append(rr(0, 68, W, 1, fill=t.line2))
    parts.append(rr(0, 67, 220, 3, 1.5, fill=f"url(#{seg})", class_="grow"))
    doc.add(g("".join(parts)))
    return doc.render()
