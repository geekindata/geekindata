"""Credentials: holographic certification cards plus a row of other certificates."""

from __future__ import annotations

import math

from ..fonts import face, wrap
from ..svg import FADE_UP, Doc, card, chip, el, g, rr

W = 880
GAP = 14
CH = 196


def _hexagon(cx, cy, r) -> str:
    pts = " ".join(f"{cx + r * math.cos(math.radians(60 * k - 90)):.2f},{cy + r * math.sin(math.radians(60 * k - 90)):.2f}"
                   for k in range(6))
    return pts


def render(t, content: dict) -> str:
    certs = content["certs"]
    also = content["credentials"]["also"]
    cw = (W - GAP * (len(certs) - 1)) / len(certs)

    # lay out the "also" chips first to know the height
    chip_rows, row, x = [], [], 0.0
    for item in also:
        w = face("mono").width(item, 10.5) + 18
        if row and x + w > W:
            chip_rows.append(row)
            row, x = [], 0.0
        row.append((x, item))
        x += w + 8
    chip_rows.append(row)
    H = CH + 46 + len(chip_rows) * 30

    doc = Doc(W, H, "Credentials",
              "; ".join(f"{c['issuer']} {c['name']} ({c['code']}, {c['year']})" for c in certs)
              + ". Also: " + "; ".join(also) + ".", t)
    doc.css(
        FADE_UP,
        ".sheen{animation:sheen 7s ease-in-out infinite}",
        "@keyframes sheen{0%{transform:translateX(-60px)}45%,100%{transform:translateX(460px)}}",
    )
    holo = doc.uid("holo")
    doc.defs(el("linearGradient",
                "".join(el("stop", offset=o, stop_color=c, stop_opacity=a) for o, c, a in [
                    (0, "#fff", 0), (0.45, t.aurora[2], 0.0), (0.5, "#fff", 0.16 if t.dark else 0.5),
                    (0.55, t.aurora[4], 0.0), (1, "#fff", 0)]),
                id=holo, x1=0, y1=0, x2=1, y2=0.35))

    parts = []
    for i, c in enumerate(certs):
        x = i * (cw + GAP)
        color = t.accent[c["cat"]]
        clip = doc.uid("cc")
        doc.defs(el("clipPath", rr(x, 0, cw, CH, 16), id=clip))
        body = [
            card(t, x, 0, cw, CH, 16),
            g(rr(x, 0, cw, 4, fill=color, fill_opacity=0.9), clip_path=f"url(#{clip})"),
            el("polygon", points=_hexagon(x + 48, 56, 32), fill=color, fill_opacity=0.12, stroke=color,
               stroke_width=1.5),
            el("polygon", points=_hexagon(x + 48, 56, 26), fill="none", stroke=color, stroke_opacity=0.35),
            doc.text(x + 48, 59.8, c["code"], "mono-m", 10.5, color, anchor="middle"),
            doc.text(x + cw - 18, 40, c["year"], "mono", 11, t.ink3, anchor="end"),
            doc.text(x + cw - 18, 58, "CERTIFIED", "mono-m", 9, t.accent["ok"], anchor="end", tracking=1.2),
        ]
        for j, ln in enumerate(wrap(c["name"], "serif", 21, cw - 36)[:3]):
            body.append(doc.text(x + 18, 116 + j * 23, ln, "serif", 21, t.ink))
        body.append(doc.text(x + 18, CH - 20, c["issuer"].upper(), "mono-m", 10, t.ink3, tracking=1.4))
        body.append(g(rr(x - 200, 0, 200, CH, fill=f"url(#{holo})", class_="sheen",
                         style=f"animation-delay:{1 + i * 0.6:.1f}s"), clip_path=f"url(#{clip})"))
        parts.append(g("".join(body), class_="up", style=f"animation-delay:{i * 0.09:.2f}s"))

    parts.append(doc.text(2, CH + 30, "MORE CERTIFICATES", "mono-m", 10, t.ink3, tracking=1.4))
    for r, row in enumerate(chip_rows):
        for x, item in row:
            c, _ = chip(doc, x, CH + 42 + r * 30, item, t.ink2, t.panel, "mono", 10.5, h=22, pad=9, stroke=t.line)
            parts.append(c)
    doc.add(*parts)
    return doc.render()
