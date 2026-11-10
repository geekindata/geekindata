"""Live telemetry bento: KPIs, mini heatmap, streak, language mix and weekly rhythm."""

from __future__ import annotations

import math

from ..fonts import face
from ..svg import FADE_UP, Doc, card, el, g, rr

W = 880
GAP = 14
DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _value(doc, t, x, y, big: str, small: str = "") -> str:
    out = doc.text(x, y, big, "sans-sb", 36, t.ink, tracking=-0.8)
    if small:
        bw = face("sans-sb").width(big, 36, -0.8)
        out += doc.text(x + bw + 6, y, small, "sans-m", 15, t.ink3)
    return out


def _label(doc, t, x, y, text, color=None) -> str:
    return doc.text(x, y, text.upper(), "mono-m", 10, color or t.ink3, tracking=1.2)


def render(t, s: dict) -> str:
    tw = (W - 3 * GAP) / 4
    th = 150
    r2 = th + GAP
    bh = 176
    H = r2 + bh + 34
    doc = Doc(W, H, "Live GitHub telemetry",
              f"{s['total']:,} contributions in the last 365 days across {s['active']} active days; "
              f"current streak {s['current_streak']} days, longest {s['longest_streak']}; "
              f"{s['commits']:,} commits and {s['pull_requests']:,} pull requests. Top languages: "
              + ", ".join(f"{n} {p:.0%}" for n, p, _ in s["languages"]) + ".", t)
    doc.css(
        FADE_UP,
        ".bar{transform-box:fill-box;transform-origin:bottom;animation:barup 1.2s cubic-bezier(.2,.8,.2,1) both}",
        "@keyframes barup{from{transform:scaleY(0)}to{transform:scaleY(1)}}",
        ".seg{transform-box:fill-box;transform-origin:left;animation:segx 1.2s cubic-bezier(.2,.8,.2,1) both}",
        "@keyframes segx{from{transform:scaleX(0)}to{transform:scaleX(1)}}",
        ".cell{animation:pop .5s ease-out both}@keyframes pop{from{opacity:0}to{opacity:1}}",
    )
    data, ai, eng = t.accent["data"], t.accent["ai"], t.accent["eng"]
    parts = []

    def tile(i, body):
        x = i * (tw + GAP)
        parts.append(g(card(t, x, 0, tw, th) + body(x), class_="up", style=f"animation-delay:{i * 0.08:.2f}s"))

    # 1 contributions + weekly bars
    def t1(x):
        out = _label(doc, t, x + 18, 28, "Contributions · 365d") + _value(doc, t, x + 18, 76, f"{s['total']:,}")
        out += doc.text(x + 18, 99, f"≈ {s['per_day']:.1f} per day · best {s['best_count']}", "sans", 12.5, t.ink2)
        weeks = s["weekly"]
        top = max(weeks) or 1
        bw = (tw - 36) / len(weeks)
        bars = []
        for j, v in enumerate(weeks):
            h = 2 + 22 * math.log1p(v) / math.log1p(top)
            bars.append(rr(round(x + 18 + j * bw, 2), round(134 - h, 2), round(bw * 0.7, 2), round(h, 2), 0.6,
                           fill=data, fill_opacity=round(0.35 + 0.65 * (v / top) ** 0.5, 2)))
        return out + g("".join(bars), class_="bar", style="animation-delay:.3s")

    # 2 active days + mini heatmap
    def t2(x):
        pct = s["active"] / max(len(s["days"]), 1)
        out = _label(doc, t, x + 18, 28, "Active days") + _value(doc, t, x + 18, 76, str(s["active"]), f"/ {len(s['days'])}")
        out += doc.text(x + 18, 99, f"{pct:.0%} of the year · {len(s['days']) - s['active']} quiet", "sans", 12.5, t.ink2)
        days = s["days"]
        lead = days[0][0].weekday()
        cols = math.ceil((len(days) + lead) / 7)
        cell = (tw - 36) / cols
        top = s["max_day"] or 1
        cells = []
        for j, (_, c) in enumerate(days):
            k = j + lead
            cx, cy = x + 18 + (k // 7) * cell, 110 + (k % 7) * cell
            op = 0.1 if not c else 0.35 + 0.65 * math.log1p(c) / math.log1p(top)
            cells.append(rr(round(cx, 2), round(cy, 2), round(cell * 0.82, 2), round(cell * 0.82, 2), 0.5,
                            fill=ai if c else t.ink3, fill_opacity=round(op, 2)))
        return out + g("".join(cells), class_="cell", style="animation-delay:.4s")

    # 3 streak + last 28 days
    def t3(x):
        cur = s["current_streak"]
        out = _label(doc, t, x + 18, 28, "Streak") + _value(doc, t, x + 18, 76, str(cur), "day" if cur == 1 else "days")
        out += doc.text(x + 18, 99, f"longest {s['longest_streak']} · busiest {s['best_day']:%d %b}", "sans", 12.5,
                        t.ink2)
        last = s["days"][-28:]
        step = (tw - 36) / 14
        dots = []
        for j, (_, c) in enumerate(last):
            cx, cy = x + 18 + (j % 14) * step + 4, 116 + (j // 14) * 13
            dots.append(el("circle", cx=round(cx, 2), cy=cy, r=4, fill=eng if c else "none",
                           stroke=eng if c else t.line2, stroke_width=1))
        return out + g("".join(dots), class_="cell", style="animation-delay:.5s")

    # 4 commits / PRs split
    def t4(x):
        out = _label(doc, t, x + 18, 28, "Commits & PRs") + _value(doc, t, x + 18, 76, f"{s['commits']:,}", "commits")
        out += doc.text(x + 18, 99, f"{s['pull_requests']:,} pull requests opened", "sans", 12.5, t.ink2)
        total = (s["commits"] + s["pull_requests"]) or 1
        span = tw - 36
        cw = span * s["commits"] / total
        out += g(rr(x + 18, 116, cw - 2, 10, 3, fill=data) + rr(x + 18 + cw, 116, span - cw, 10, 3, fill=t.accent["pink"]),
                 class_="seg", style="animation-delay:.6s")
        out += doc.text(x + 18, 143, "commits", "mono", 9.5, t.ink3)
        out += doc.text(x + tw - 18, 143, "pull requests", "mono", 9.5, t.ink3, anchor="end")
        return out

    for i, fn in enumerate((t1, t2, t3, t4)):
        tile(i, fn)

    # languages
    lw = 520
    langs = s["languages"]
    scope = "incl. private" if s["languages_private"] else "public"
    lang = [card(t, 0, r2, lw, bh), _label(doc, t, 18, r2 + 28, f"Languages · bytes · {s['repos']} repos ({scope})")]
    x = 18.0
    span = lw - 36
    segs = []
    for name, pct, color in langs:
        w = span * pct
        segs.append(rr(round(x, 2), r2 + 46, round(max(w - 2, 1), 2), 12, 2, fill=color or t.ink3))
        x += w
    lang.append(g("".join(segs), class_="seg", style="animation-delay:.35s"))
    per_col = math.ceil(len(langs) / 2)
    for j, (name, pct, color) in enumerate(langs):
        cx = 18 + (j // per_col) * 250
        cy = r2 + 88 + (j % per_col) * 23
        lang.append(rr(cx, cy - 9, 9, 9, 2, fill=color or t.ink3))
        lang.append(doc.text(cx + 17, cy, name, "sans", 13, t.ink))
        lang.append(doc.text(cx + 222, cy, f"{pct * 100:.1f}%", "mono", 11.5, t.ink2, anchor="end"))
    parts.append(g("".join(lang), class_="up", style="animation-delay:.3s"))

    # weekly rhythm
    rx = lw + GAP
    rw = W - rx
    wk = s["weekday"]
    top = max(wk) or 1
    best = wk.index(top)
    rhythm = [card(t, rx, r2, rw, bh), _label(doc, t, rx + 18, r2 + 28, "Weekly rhythm"),
              doc.text(rx + rw - 18, r2 + 28, f"busiest: {DAY_NAMES[best]}", "mono-m", 10, ai, anchor="end")]
    slot = (rw - 36) / 7
    bw = slot * 0.56
    base = r2 + 142
    bars = []
    for j, v in enumerate(wk):
        h = max(3, 82 * v / top)
        bx = rx + 18 + j * slot + (slot - bw) / 2
        bars.append(g(rr(round(bx, 2), round(base - h, 2), round(bw, 2), round(h, 2), 4,
                         fill=ai if j == best else t.ink3, fill_opacity=1 if j == best else 0.35),
                      class_="bar", style=f"animation-delay:{0.4 + j * 0.06:.2f}s"))
        bars.append(doc.text(round(bx + bw / 2, 2), round(base - h - 7, 2), str(v), "mono", 10,
                             t.ink if j == best else t.ink3, anchor="middle"))
        bars.append(doc.text(round(bx + bw / 2, 2), base + 20, DAYS[j], "mono", 9.5, t.ink3, anchor="middle",
                             tracking=0.8))
    rhythm += bars
    parts.append(g("".join(rhythm), class_="up", style="animation-delay:.38s"))

    parts.append(doc.text(4, H - 10, f"source: GitHub GraphQL API · window {s['start']:%d %b %Y} → {s['end']:%d %b %Y} "
                                     "· regenerated daily by GitHub Actions", "mono", 10, t.ink3))
    doc.add(*parts)
    return doc.render()
