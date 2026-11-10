"""Link pills: one small SVG per link so each stays individually clickable."""

from __future__ import annotations

import re

from ..fonts import face
from ..svg import Doc, arrow_ne, el, rr

H = 32
SIZE = 10.5
TRACK = 1.1


def slug(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def render(t, link: dict) -> str:
    label = link["label"].upper()
    tw = face("mono-m").width(label, SIZE, TRACK)
    w = round(26 + tw + 10 + 7 + 13)
    doc = Doc(w, H, link["label"], f"{link['label']}: {link['url']}", t)
    color = t.accent[link["accent"]]
    doc.add(
        rr(0.5, 0.5, w - 1, H - 1, H / 2, fill=t.panel, stroke=t.line2),
        el("circle", cx=15, cy=H / 2, r=3.2, fill=color),
        doc.text(26, H / 2 + 3.9, label, "mono-m", SIZE, t.ink, tracking=TRACK),
        arrow_ne(26 + tw + 10, H / 2 - 3.5, 7, t.ink3),
    )
    return doc.render()
