"""Selected work: client project cards in a 2-column bento."""

from __future__ import annotations

from ..fonts import face, fit_size, wrap
from ..svg import FADE_UP, Doc, card, chip, el, g, rr

W = 880
GAP = 16
CH = 186


def render(t, content: dict) -> str:
    work = content["work"]
    cw = (W - GAP) / 2
    rows = (len(work) + 1) // 2
    earlier = wrap(content["earlier"]["text"], "mono", 10.5, W - 8)
    grid_h = rows * CH + (rows - 1) * GAP
    H = grid_h + 18 + len(earlier) * 16 + 4
    doc = Doc(W, H, "Selected work",
              " ".join(f"{p['client']}: {p['title']}. {p['summary']}" for p in work) + " " + content["earlier"]["text"], t)
    doc.css(FADE_UP)

    parts = []
    for i, p in enumerate(work):
        x = (i % 2) * (cw + GAP)
        y = (i // 2) * (CH + GAP)
        color = t.accent[p["cat"]]
        body = [card(t, x, y, cw, CH, 16)]
        # periodic tile glyph echoes the stack section
        body.append(rr(x + 20, y + 20, 44, 44, 9, fill=color, fill_opacity=0.14, stroke=color, stroke_opacity=0.5))
        body.append(doc.text(x + 42, y + 49, p["sym"], "sans-sb", 19, color, anchor="middle", tracking=-0.3))
        body.append(doc.text(x + 78, y + 35, p["client"].upper(), "mono-m", 10, t.ink3, tracking=1.3))
        status = p["status"].upper()
        live = status == "ONGOING"
        sw = face("mono-m").width(status, 9.5, 1) + (26 if live else 16)
        sx = x + cw - 20 - sw
        body.append(rr(sx, y + 21, sw, 20, 10, fill="none", stroke=t.accent["ok"] if live else t.line2))
        if live:
            body.append(el("circle", cx=sx + 10, cy=y + 31, r=2.6, fill=t.accent["ok"]))
        body.append(doc.text(sx + (18 if live else 8), y + 34.5, status, "mono-m", 9.5,
                             t.accent["ok"] if live else t.ink3, tracking=1))
        title_size = fit_size(p["title"], "serif", 25, x + cw - 20 - (x + 78), 19)
        body.append(doc.text(x + 78, y + 60, p["title"], "serif", title_size, t.ink))
        for j, ln in enumerate(wrap(p["summary"], "sans", 13.5, cw - 40)[:3]):
            body.append(doc.text(x + 20, y + 92 + j * 20, ln, "sans", 13.5, t.ink2))
        tx = x + 20
        for tag in p["tags"]:
            tw = face("mono").width(tag, 10.5) + 16
            if tx + tw > x + cw - 16:
                break
            c, tw = chip(doc, tx, y + CH - 38, tag, t.ink2, t.panel2, "mono", 10.5, stroke=t.line)
            body.append(c)
            tx += tw + 6
        parts.append(g("".join(body), class_="up", style=f"animation-delay:{i * 0.08:.2f}s"))

    for j, ln in enumerate(earlier):
        parts.append(doc.text(4, grid_h + 26 + j * 16, ln, "mono", 10.5, t.ink3))
    doc.add(*parts)
    return doc.render()
