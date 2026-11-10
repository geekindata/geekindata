"""`whoami` as a lakehouse notebook cell: a SQL query and its result grid."""

from __future__ import annotations

import re

from ..fonts import face, wrap
from ..svg import FADE_UP, Doc, card, check_path, chip, el, g, rr

W = 880
KEYWORDS = {"SELECT", "FROM", "WHERE", "AND", "%%sql"}
TOKEN = re.compile(r"(--.*$)|('[^']*')|(%%sql|\b[A-Z]{3,}\b)|(\s+)|([^\s']+)")


def highlight(t, line: str) -> list[tuple]:
    runs = []
    for m in TOKEN.finditer(line):
        comment, string, kw, space, other = m.groups()
        if comment:
            runs.append((comment, "mono", t.ink3))
        elif string:
            runs.append((string, "mono", t.accent["data"]))
        elif kw and kw in KEYWORDS:
            runs.append((kw, "mono-m", t.accent["ai"]))
        else:
            runs.append((m.group(0), "mono", t.ink))
    return runs


def render(t, content: dict) -> str:
    who = content["whoami"]
    rows = who["rows"]
    code = who["query"]
    key_x, val_x, val_w = 46, 196, W - 196 - 28
    line_h = 21

    wrapped = [wrap(v, "sans", 14, val_w) for _, v in rows]
    head_h = 46
    code_top = head_h + 30
    code_bottom = code_top + (len(code) - 1) * 22 + 22
    out_top = code_bottom
    table_top = out_top + 48
    row_heights = [20 + len(lines) * line_h for lines in wrapped]
    table_bottom = table_top + 30 + sum(row_heights)
    H = table_bottom + 40

    doc = Doc(W, H, "whoami: profile as a notebook cell",
              "A SQL notebook cell selecting my profile row: " + "; ".join(f"{k}: {v}" for k, v in rows), t)
    doc.css(
        FADE_UP,
        ".blink{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}",
    )

    parts = [card(t, 0, 0, W, H, 16)]
    # cell toolbar
    parts.append(rr(1, 1, W - 2, head_h - 1, 15, fill=t.panel2))
    parts.append(rr(1, head_h - 16, W - 2, 16, fill=t.panel2))
    parts.append(rr(0, head_h, W, 1, fill=t.line))
    parts.append(doc.text(20, 28, "[1]", "mono", 11.5, t.ink3))
    c, cw = chip(doc, 52, 13, "SQL", t.accent["ai"], f"{t.accent['ai']}22", "mono-m", 10)
    parts.append(c)
    parts.append(doc.text(52 + cw + 10, 28, "whoami.ipynb", "sans-m", 13, t.ink2))
    parts.append(doc.text(W - 20, 28, "Succeeded · 0.42 s", "mono", 11, t.ink3, anchor="end"))
    sw = face("mono").width("Succeeded · 0.42 s", 11)
    parts.append(check_path(W - 20 - sw - 18, 18, 10, t.accent["ok"]))

    # code
    for i, line in enumerate(code):
        y = code_top + i * 22
        parts.append(doc.text(30, y, str(i + 1), "mono", 12, t.ink3, anchor="end"))
        parts.append(doc.spans(46, y, highlight(t, line), 13.5))
    last_w = face("mono").width(code[-1], 13.5)
    parts.append(rr(46 + last_w + 4, code_top + (len(code) - 1) * 22 - 13, 8, 17, fill=t.accent["data"],
                    class_="blink"))

    # output header
    parts.append(rr(0, out_top, W, 1, fill=t.line))
    parts.append(doc.text(20, out_top + 30, "Out[1]", "mono", 11.5, t.ink3))
    c, cw = chip(doc, 74, out_top + 15, "TABLE", t.accent["data"], f"{t.accent['data']}22", "mono-m", 10,
                 tracking=0.8)
    parts.append(c)
    parts.append(doc.text(W - 20, out_top + 30, f"{len(rows)} rows · 2 columns", "mono", 11, t.ink3, anchor="end"))

    # grid
    parts.append(rr(16, table_top, W - 32, 30, 8, fill=t.panel2))
    parts.append(doc.text(key_x, table_top + 19.5, "COLUMN_NAME", "mono-m", 10, t.ink3, tracking=1.1))
    parts.append(doc.text(val_x, table_top + 19.5, "VALUE", "mono-m", 10, t.ink3, tracking=1.1))
    parts.append(doc.text(W - 30, table_top + 19.5, "STRING", "mono", 10, t.ink3, anchor="end", tracking=1.1))
    y = table_top + 30
    for i, ((key, _), lines, rh) in enumerate(zip(rows, wrapped, row_heights)):
        row = [rr(16, y + rh - 1, W - 32, 1, fill=t.line)]
        row.append(doc.text(24, y + 25, str(i + 1), "mono", 10, t.ink3))
        row.append(doc.text(key_x, y + 25, key, "mono", 12.5, t.accent["data"]))
        for j, ln in enumerate(lines):
            row.append(doc.text(val_x, y + 25 + j * line_h, ln, "sans-m" if key == "name" else "sans", 14, t.ink))
        parts.append(g("".join(row), class_="up", style=f"animation-delay:{0.25 + i * 0.07:.2f}s"))
        y += rh
    parts.append(doc.text(20, H - 16, f"{len(rows)} rows returned from gold.people", "mono", 10.5, t.ink3))
    parts.append(el("circle", cx=W - 24, cy=H - 19.5, r=3, fill=t.accent["ok"]))
    parts.append(doc.text(W - 34, H - 16, "spark session · oslo-1", "mono", 10.5, t.ink3, anchor="end"))
    doc.add(g("".join(parts)))
    return doc.render()
