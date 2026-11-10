"""Hero: an aurora over the Oslofjord drawn from the last 365 days of contributions."""

from __future__ import annotations

import math
import random

from ..fonts import face
from ..svg import Doc, el, fmt, g, rr

W, H, H0 = 880, 420, 316  # H0 = horizon


def _ridge(rng: random.Random, base: float, amp: float, step: float = 5, fjord: float = 0.0) -> list[tuple[float, float]]:
    """Layered-sine mountain line; `fjord` lowers the middle like a valley opening to the sea."""
    waves = [(rng.uniform(70, 160), rng.uniform(0, 6.28), 1.0),
             (rng.uniform(30, 60), rng.uniform(0, 6.28), 0.45),
             (rng.uniform(11, 19), rng.uniform(0, 6.28), 0.15)]
    pts = []
    x = -10.0
    while x <= W + 10:
        y = sum(a * math.sin(x / p + ph) for p, ph, a in waves) / 1.6
        valley = 1 - fjord * (1 - abs(2 * x / W - 1) ** 1.4)
        pts.append((x, base - amp * valley * (0.55 + 0.45 * y)))
        x += step
    return pts


def _poly(points, close_y) -> str:
    d = f"M{fmt(points[0][0])},{fmt(close_y)}"
    d += "".join(f"L{fmt(x)},{fmt(y)}" for x, y in points)
    return d + f"L{fmt(points[-1][0])},{fmt(close_y)}Z"


def _rolling_max(vals: list[float], k: int) -> list[float]:
    return [max(vals[max(0, i - k):i + k + 1]) for i in range(len(vals))]


def _smooth(vals: list[float], k: int) -> list[float]:
    out = []
    for i in range(len(vals)):
        lo, hi = max(0, i - k), min(len(vals), i + k + 1)
        out.append(sum(vals[lo:hi]) / (hi - lo))
    return out


def grad(id_, stops, x1=0, y1=0, x2=0, y2=0) -> str:
    inner = "".join(el("stop", offset=o, stop_color=c, stop_opacity=a) for o, c, a in stops)
    return el("linearGradient", inner, id=id_, gradientUnits="userSpaceOnUse", x1=x1, y1=y1, x2=x2, y2=y2)


def render(t, content, s) -> str:
    p = content["profile"]
    a = t.aurora
    rng = random.Random(59)
    n_days = len(s["days"])
    doc = Doc(W, H, f"{p['name_first']} {p['name_last']}, {p['role']}",
              f"An animated aurora over the Oslofjord. Each ray is one day of GitHub activity over the last "
              f"{n_days} days ({s['total']:,} contributions); taller rays mean busier days.", t)

    clip, sky, rays_g, glow_g, ghost_g, blur, blur2, fade, name_g, veil, veil_m = (
        doc.uid(x) for x in ("clip", "sky", "ray", "glow", "ghost", "blur", "blurb", "fade", "name", "veil", "veilm"))

    yb = H0 - 6
    top_span = 230
    peak = 0.95 if t.dark else 0.8
    doc.defs(
        el("clipPath", rr(0, 0, W, H, 18), id=clip),
        grad(sky, [(0, t.sky[0], 1), (1, t.sky[1], 1)], y2=H0),
        grad(rays_g, [(0, a[0], 0), (0.06, a[0], peak), (0.38, a[1], peak * 0.9), (0.6, a[2], peak * 0.75),
                      (0.8, a[3], peak * 0.55), (1, a[4], 0)], y1=yb, y2=yb - top_span),
        grad(glow_g, [(0, a[0], 0.0), (0.1, a[0], 0.8), (0.5, a[2], 0.55), (1, a[4], 0)], y1=yb, y2=yb - top_span),
        grad(ghost_g, [(0, a[3], 0), (0.2, a[3], 0.7), (0.6, a[4], 0.5), (1, a[5], 0)], y1=yb, y2=yb - top_span),
        el("filter", el("feGaussianBlur", stdDeviation=9), id=blur, x="-5%", y="-40%", width="110%", height="180%"),
        el("filter", el("feGaussianBlur", stdDeviation=18), id=blur2, x="-5%", y="-60%", width="110%", height="220%"),
        el("filter", el("feGaussianBlur", stdDeviation=2.6), id=f"{blur}b", x="-5%", y="-10%", width="110%", height="120%"),
        el("mask", rr(0, H0, W, H - H0, fill=f"url(#{fade}g)"), id=fade),
        grad(f"{fade}g", [(0, "#fff", 0.95), (0.85, "#fff", 0.1), (1, "#fff", 0)], y1=H0, y2=H),
        grad(veil, [(0, t.sky[0], 0.94 if t.dark else 0.9), (0.5, t.sky[0], 0.78), (0.82, t.sky[0], 0)], x2=640),
        el("mask", rr(0, 0, W, H0, fill=f"url(#{veil_m}g)"), id=veil_m),
        grad(f"{veil_m}g", [(0, "#fff", 1), (0.7, "#fff", 1), (1, "#fff", 0)], y2=H0 - 30),
    )

    # --- aurora geometry from data
    x0, x1 = 22.0, W - 22.0
    dx = (x1 - x0) / max(n_days - 1, 1)
    max_log = math.log1p(s["max_day"]) or 1
    heights = []
    for i, (_, c) in enumerate(s["days"]):
        if c:
            heights.append(26 + 150 * math.log1p(c) / max_log)
        else:  # quiet days keep a low, breathing curtain so the aurora stays continuous
            heights.append((7 + 7 * math.sin(i / 7.3) + 4 * math.sin(i / 2.9 + 1)) * rng.uniform(0.6, 1.0) + 3)
    xs = [x0 + i * dx for i in range(n_days)]
    curtain = _smooth(_rolling_max(heights, 5), 6)
    glow_pts = [(x, yb - 24 - h * 0.92) for x, h in zip(xs, curtain)]
    ghost_pts = [(x + 30, yb - 40 - h * 0.85) for x, h in zip(xs, _smooth(_rolling_max(heights, 11), 14))]

    groups = 9
    paths = [[] for _ in range(groups)]
    for i, (x, h) in enumerate(zip(xs, heights)):
        paths[i % groups].append(f"M{fmt(x)},{fmt(yb)}V{fmt(yb - 24 - h)}")
    ray_paths = "".join(
        el("path", d="".join(ps), class_=f"ray r{k}", stroke=f"url(#{rays_g})", stroke_width=round(dx * 0.62, 2))
        for k, ps in enumerate(paths)
    )
    aurora_id, rays_id = doc.uid("aur"), doc.uid("rays")
    aurora = g(
        el("path", d=_poly(ghost_pts, yb), fill=f"url(#{ghost_g})", filter=f"url(#{blur2})", class_="sway2",
           opacity=0.55 if t.dark else 0.35)
        + el("path", d=_poly(glow_pts, yb), fill=f"url(#{glow_g})", filter=f"url(#{blur})", class_="sway",
             opacity=0.8 if t.dark else 0.5)
        + el("use", href=f"#{rays_id}", filter=f"url(#{blur}b)", opacity=0.9 if t.dark else 0.6)
        + g(ray_paths, id=rays_id),
        id=aurora_id,
    )

    far = _ridge(rng, H0 - 10, 58, fjord=0.7)
    near = _ridge(rng, H0 + 1, 22, 4, fjord=0.85)
    ridges_id = doc.uid("rdg")
    ridges = g(el("path", d=_poly(far, H0 + 1), fill=t.ridge_far) + el("path", d=_poly(near, H0 + 1), fill=t.ridge_near),
               id=ridges_id)

    # --- css
    doc.css(
        f".ray{{fill:none;transform-box:view-box;transform-origin:0 {yb}px;"
        "animation:rise 2s cubic-bezier(.2,.8,.2,1) both,shim 5s ease-in-out infinite}",
        "@keyframes rise{from{transform:scaleY(0)}to{transform:scaleY(1)}}",
        "@keyframes shim{0%,100%{opacity:.62}50%{opacity:1}}",
        *(f".r{k}{{animation-delay:{k * 0.07:.2f}s,-{k * 0.61:.2f}s;animation-duration:2s,{4.2 + (k % 4) * 0.55:.2f}s}}"
          for k in range(groups)),
        ".sway{animation:sway 11s ease-in-out infinite alternate}",
        ".sway2{animation:sway 17s ease-in-out infinite alternate-reverse}",
        "@keyframes sway{from{transform:translateX(-10px)}to{transform:translateX(10px)}}",
        ".tw{animation:tw 3.8s ease-in-out infinite}",
        "@keyframes tw{50%{opacity:.12}}",
        ".rip{animation:rip 7s ease-in-out infinite alternate}",
        "@keyframes rip{from{transform:translateX(-14px)}to{transform:translateX(14px)}}",
        ".pulse{transform-box:fill-box;transform-origin:center;animation:pulse 2.2s ease-out infinite}",
        "@keyframes pulse{from{transform:scale(1);opacity:.75}to{transform:scale(3.2);opacity:0}}",
        ".in{animation:in 1.1s cubic-bezier(.2,.8,.2,1) both}",
        "@keyframes in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}",
    )

    # --- sky
    body = [rr(0, 0, W, H0 + 1, fill=f"url(#{sky})")]
    if t.dark:
        stars = []
        for i in range(150):
            x, y = rng.uniform(0, W), (rng.random() ** 1.25) * (H0 - 70)
            r, o = rng.uniform(0.35, 1.25), rng.uniform(0.25, 0.9)
            attrs = {"class_": "tw", "style": f"animation-delay:-{rng.uniform(0, 4):.2f}s"} if i % 4 == 0 else {}
            stars.append(el("circle", cx=round(x, 1), cy=round(y, 1), r=round(r, 2), fill="#fff", opacity=round(o, 2),
                            **attrs))
        body.append(g("".join(stars)))
    else:
        sun = doc.uid("sun")
        doc.defs(el("radialGradient", el("stop", offset=0, stop_color="#FFD9A8", stop_opacity=0.9)
                    + el("stop", offset=1, stop_color="#FFD9A8", stop_opacity=0), id=sun))
        body.append(el("circle", cx=742, cy=H0, r=230, fill=f"url(#{sun})"))

    # --- water + reflection
    water = doc.uid("water")
    doc.defs(grad(water, [(0, t.ridge_far if t.dark else t.water, 1), (1, t.water if t.dark else "#F7F9FB", 1)],
                  y1=H0, y2=H))
    body += [
        aurora,
        ridges,
        rr(0, H0, W, H - H0, fill=f"url(#{water})"),
        g(g(el("use", href=f"#{aurora_id}") + el("use", href=f"#{ridges_id}"),
            transform=f"matrix(1 0 0 -0.42 0 {fmt(H0 * 1.42)})"),
          mask=f"url(#{fade})", opacity=0.5 if t.dark else 0.4),
        el("line", x1=0, y1=H0 + 0.5, x2=W, y2=H0 + 0.5, stroke=a[1], stroke_opacity=0.35),
    ]
    ripples = []
    for _ in range(18):
        y = rng.uniform(H0 + 8, H - 30)
        x = rng.uniform(20, W - 160)
        ripples.append(el("line", x1=round(x), y1=round(y, 1), x2=round(x + rng.uniform(30, 140)), y2=round(y, 1),
                          stroke=t.ink, stroke_opacity=round(rng.uniform(0.04, 0.1), 3), stroke_width=1))
    body.append(g("".join(ripples), class_="rip"))

    # --- month ticks along the horizon
    ticks = []
    for i, (d, _) in enumerate(s["days"]):
        if d.day == 1 and 0 < i < n_days - 6:
            label = d.strftime("%b").upper() + (f" ’{d:%y}" if d.month == 1 else "")
            ticks.append(el("line", x1=round(xs[i], 1), y1=H0 + 5, x2=round(xs[i], 1), y2=H0 + 10, stroke=t.ink3))
            ticks.append(doc.text(round(xs[i] + 3, 1), H0 + 21, label, "mono", 9, t.ink2, tracking=0.6,
                                  stroke=t.water, stroke_width=3, paint_order="stroke", stroke_linejoin="round"))
    body.append(g("".join(ticks)))

    # --- left veil for legibility, then type
    body.append(rr(0, 0, 640, H0, fill=f"url(#{veil})", mask=f"url(#{veil_m})"))
    last_w = face("serif-i").width(p["name_last"], 70)
    doc.defs(grad(name_g, [(0, a[0], 1), (0.35, a[2], 1), (0.7, a[4], 1), (1, a[5], 1)], x1=40, x2=40 + last_w))
    body.append(g(
        doc.text(44, 62, p["coordinates"], "mono", 11, t.ink2, tracking=2.2)
        + doc.text(40, 134, p["name_first"], "serif", 70, t.ink)
        + doc.text(40, 198, p["name_last"], "serif-i", 70, f"url(#{name_g})")
        + doc.text(44, 238, p["role"], "sans-m", 16.5, t.ink)
        + doc.text(44, 263, p["pitch"], "sans", 14, t.ink2),
        class_="in",
    ))

    # --- "now" pill
    pill_runs = [("NOW", "mono-m", t.accent["ok"]), ("  ·  " + p["now"], "mono", t.ink2)]
    pw = sum(face(f).width(txt, 11) for txt, f, _ in pill_runs) + 46
    px, py = W - 28 - pw, 36
    body.append(g(
        rr(px, py, pw, 28, 14, fill=t.panel, fill_opacity=0.72, stroke=t.line2)
        + el("circle", cx=px + 17, cy=py + 14, r=3.5, fill=t.accent["ok"], class_="pulse")
        + el("circle", cx=px + 17, cy=py + 14, r=3.5, fill=t.accent["ok"])
        + doc.spans(px + 29, py + 18, pill_runs, 11),
        class_="in", style="animation-delay:.3s",
    ))

    # --- caption
    body.append(doc.spans(28, H - 18, [
        ("↑ THE AURORA IS DATA", "mono-m", a[1]),
        ("  one ray per day on GitHub · height = contributions (log)", "mono", t.ink2),
    ], 10))
    body.append(doc.text(W - 28, H - 18, f"{s['total']:,} contributions · {s['start']:%d %b %Y} → {s['end']:%d %b %Y}",
                         "mono", 10, t.ink3, anchor="end"))

    doc.add(g("".join(body), clip_path=f"url(#{clip})"), rr(0.5, 0.5, W - 1, H - 1, 18, fill="none", stroke=t.line2))
    return doc.render()
