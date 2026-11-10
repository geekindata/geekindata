"""On stage: talks as a tour-poster setlist, with a spinning speaker sticker."""

from __future__ import annotations

import math

from ..fonts import face, fit_size, wrap
from ..svg import FADE_UP, Doc, card, el, g, rr

W = 880
LEFT = 268
ROW = 50


def render(t, content: dict) -> str:
    st = content["stage"]
    talks = st["talks"]
    top = 34
    H = top + len(talks) * ROW + 30
    distinct = len({x["title"] for x in talks})
    doc = Doc(W, H, "On stage: conference and user group talks",
              f"{len(talks)} sessions, {distinct} talks. Sessionize Most Active Speaker 2024. "
              + " ".join(f"{x['when']}: {x['title']} at {x['event']}." for x in talks), t)
    hot, ai = t.accent["hot"], t.accent["ai"]
    cx, cy, rad = LEFT / 2, H - 100, 78
    doc.css(
        FADE_UP,
        f".spin{{transform-box:view-box;transform-origin:{cx}px {cy}px;animation:spin 40s linear infinite}}",
        "@keyframes spin{to{transform:rotate(360deg)}}",
        ".blink{animation:bl 1.6s ease-in-out infinite}@keyframes bl{50%{opacity:.35}}",
    )
    parts = [card(t, 0, 0, W, H, 18)]

    # poster column
    parts.append(rr(1, 1, LEFT - 1, H - 2, 17, fill=t.panel2))
    parts.append(rr(LEFT - 18, 1, 18, H - 2, fill=t.panel2))
    parts.append(rr(LEFT, 0, 1, H, fill=t.line))
    parts.append(doc.text(26, 44, "LIVE ON STAGE · 2024 → NOW", "mono-m", 10, hot, tracking=1.6))
    parts.append(doc.text(24, 96, "The", "serif", 50, t.ink))
    parts.append(doc.text(24, 142, "setlist.", "serif-i", 50, t.ink))
    for j, ln in enumerate(wrap(st["blurb"], "sans", 13, LEFT - 52)):
        parts.append(doc.text(26, 176 + j * 19, ln, "sans", 13, t.ink2))
    stats_y = 176 + len(wrap(st["blurb"], "sans", 13, LEFT - 52)) * 19 + 16
    parts.append(doc.spans(26, stats_y, [(f"{len(talks)}", "sans-sb", t.ink, 22), (" sessions   ", "mono", t.ink3, 10.5),
                                         (f"{distinct}", "sans-sb", t.ink, 22), (" talks", "mono", t.ink3, 10.5)], 10.5))

    # rotating sticker
    ring = doc.uid("ring")
    tr = rad - 16
    doc.defs(el("path", id=ring, d=f"M{cx - tr},{cy} a{tr},{tr} 0 1,1 {2 * tr},0 a{tr},{tr} 0 1,1 {-2 * tr},0"))
    text = st["sticker"]
    natural = face("mono-m").width(text, 10)
    tracking = (2 * math.pi * tr - natural) / len(text)
    mic = (f"M{cx - 6},{cy - 34} a6,6 0 0 1 12,0 v12 a6,6 0 0 1 -12,0 z "
           f"M{cx - 11},{cy - 24} a11,11 0 0 0 22,0 M{cx},{cy - 13} v6")
    sticker = [
        el("circle", cx=cx, cy=cy, r=rad, fill=hot, fill_opacity=0.12, stroke=hot, stroke_opacity=0.6),
        el("circle", cx=cx, cy=cy, r=rad - 30, fill="none", stroke=hot, stroke_opacity=0.35, stroke_dasharray="2 4"),
        g(doc.textpath(ring, text, "mono-m", 10, hot, tracking=round(tracking, 3)), class_="spin"),
        el("path", d=mic, fill="none", stroke=t.ink, stroke_width=1.6, stroke_linecap="round"),
        doc.text(cx, cy + 22, "2024", "serif-i", 24, t.ink, anchor="middle"),
    ]
    parts.append(g("".join(sticker)))

    # setlist
    x0 = LEFT + 28
    for i, talk in enumerate(talks):
        y = top + i * ROW
        row = []
        if i:
            row.append(el("line", x1=x0, y1=y, x2=W - 24, y2=y, stroke=t.line2, stroke_dasharray="1 5",
                          stroke_linecap="round"))
        up = talk.get("upcoming", False)
        row.append(doc.text(x0, y + 22, talk["when"], "mono-m", 10.5, hot if up else t.ink3, tracking=0.8))
        tx = x0 + 104
        right = W - 24 - (92 if up else 0)
        size = fit_size(talk["title"], "sans-m", 14.5, right - tx, 12)
        row.append(doc.text(tx, y + 22, talk["title"], "sans-m", size, t.ink))
        row.append(doc.text(tx, y + 40, talk["event"], "sans", 12.5, t.ink2))
        if up:
            label = "UPCOMING"
            lw = face("mono-m").width(label, 9.5, 1) + 26
            bx = W - 24 - lw
            row.append(rr(bx, y + 9, lw, 20, 10, fill=hot, fill_opacity=0.14, stroke=hot, stroke_opacity=0.6))
            row.append(el("circle", cx=bx + 10, cy=y + 19, r=2.6, fill=hot, class_="blink"))
            row.append(doc.text(bx + 18, y + 22.5, label, "mono-m", 9.5, hot, tracking=1))
        parts.append(g("".join(row), class_="up", style=f"animation-delay:{0.1 + i * 0.06:.2f}s"))
    doc.add(*parts)
    return doc.render()
