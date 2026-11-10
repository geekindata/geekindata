"""Career lineage rendered as `git log --graph --decorate`."""

from __future__ import annotations

import hashlib

from ..fonts import face, fit_size
from ..svg import FADE_UP, Doc, card, el, g, rr

W = 880
ROW = 52
TOP = 62
LANE_X = (34, 64)


def short_sha(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:7]


def render(t, content: dict) -> str:
    rows = content["lineage"]
    H = TOP + len(rows) * ROW + 18
    lane_color = (t.accent["data"], t.accent["ai"])
    doc = Doc(W, H, "Lineage: career as a git graph",
              " ".join(f"{r['when']}: {r['title']} ({r['org']})." for r in rows), t)
    doc.css(
        FADE_UP,
        ".draw{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 1.8s cubic-bezier(.4,0,.2,1) .2s forwards}",
        "@keyframes draw{to{stroke-dashoffset:0}}",
        ".head{transform-box:fill-box;transform-origin:center;animation:hp 2.4s ease-out infinite}",
        "@keyframes hp{from{transform:scale(1);opacity:.7}to{transform:scale(2.6);opacity:0}}",
        "@media (prefers-reduced-motion:reduce){.draw{stroke-dashoffset:0}}",
    )
    ys = [TOP + i * ROW + 16 for i in range(len(rows))]
    lanes_used = {r["lane"]: [i for i, x in enumerate(rows) if x["lane"] == r["lane"]] for r in rows}

    parts = [card(t, 0, 0, W, H, 16)]
    parts.append(doc.spans(24, 36, [("$ ", "mono", t.accent["ok"]), ("git log --graph --decorate ", "mono", t.ink),
                                    ("career", "mono", t.accent["ai"])], 12.5))
    parts.append(doc.text(W - 24, 36, f"{len(rows)} commits · 2 branches", "mono", 11, t.ink3, anchor="end"))
    parts.append(rr(0, 52, W, 1, fill=t.line))

    # edges
    edges = []
    main = lanes_used[0]
    edges.append((f"M{LANE_X[0]},{ys[main[0]]} V{ys[main[-1]]}", lane_color[0]))
    side = lanes_used.get(1, [])
    if side:
        first, last = side[0], side[-1]
        edges.append((f"M{LANE_X[1]},{ys[first]} V{ys[last]}", lane_color[1]))
        merge = next(i for i, r in enumerate(rows) if r.get("merge"))
        fork = next(i for i in range(last + 1, len(rows)) if rows[i]["lane"] == 0)
        mid = ROW * 0.55
        edges.append((f"M{LANE_X[1]},{ys[first]} C{LANE_X[1]},{ys[first] - mid} {LANE_X[0]},{ys[merge] + mid} "
                      f"{LANE_X[0]},{ys[merge]}", lane_color[1]))
        edges.append((f"M{LANE_X[0]},{ys[fork]} C{LANE_X[0]},{ys[fork] - mid} {LANE_X[1]},{ys[last] + mid} "
                      f"{LANE_X[1]},{ys[last]}", lane_color[1]))
    for d, color in edges:
        parts.append(el("path", d=d, fill="none", stroke=color, stroke_width=2, stroke_linecap="round",
                        pathLength=1, class_="draw"))

    # commits
    for i, (r, y) in enumerate(zip(rows, ys)):
        lx = LANE_X[r["lane"]]
        color = lane_color[r["lane"]]
        node = []
        if i == 0:
            node.append(el("circle", cx=lx, cy=y, r=6, fill=color, class_="head"))
        if r.get("merge"):
            node.append(el("circle", cx=lx, cy=y, r=7, fill=t.panel, stroke=color, stroke_width=2))
            node.append(el("circle", cx=lx, cy=y, r=3, fill=color))
        else:
            node.append(el("circle", cx=lx, cy=y, r=5.5, fill=t.panel if r.get("branch") else color, stroke=color,
                           stroke_width=2))
        tx = 96
        node.append(doc.text(tx, y + 4.5, short_sha(r["title"] + r["when"]), "mono", 11, t.ink3))
        tx += 66
        for ref in r.get("refs", []):
            ref_color = t.accent["ok"] if ref.startswith("HEAD") else color
            rw = face("mono-m").width(ref, 10) + 14
            node.append(rr(tx, y - 9, rw, 18, 4, fill=ref_color, fill_opacity=0.14, stroke=ref_color,
                           stroke_opacity=0.5))
            node.append(doc.text(tx + 7, y + 3.8, ref, "mono-m", 10, ref_color))
            tx += rw + 8
        font = "mono" if r.get("branch") else "sans-m"
        date_w = face("mono").width(r["when"], 11) + 30
        size = fit_size(r["title"], font, 14.5, W - date_w - tx - 10, 12)
        node.append(doc.text(tx, y + 5, r["title"], font, size, t.ink))
        node.append(doc.text(162, y + 25, r["org"], "sans", 12.5, t.ink2))
        node.append(doc.text(W - 24, y + 5, r["when"], "mono", 11, t.ink2, anchor="end"))
        parts.append(g("".join(node), class_="up", style=f"animation-delay:{0.15 + i * 0.07:.2f}s"))
    doc.add(*parts)
    return doc.render()
