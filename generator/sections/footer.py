"""Footer: a quiet fjord at night (or under the midnight sun) with a sign-off."""

from __future__ import annotations

import math
import random

from ..svg import Doc, el, g, rr
from .hero import _poly, _ridge, _rolling_max, _smooth, grad

W, H, H0 = 880, 210, 140


def render(t, content: dict, s: dict) -> str:
    a = t.aurora
    rng = random.Random(10)
    doc = Doc(W, H, "Takk for besøket (thanks for visiting)",
              f"Footer landscape. Assets regenerated {s['as_of']:%d %b %Y} by GitHub Actions.", t)
    clip, sky, glow, fade = (doc.uid(x) for x in ("clip", "sky", "glow", "fade"))
    doc.defs(
        el("clipPath", rr(0, 0, W, H, 18), id=clip),
        grad(sky, [(0, t.sky[0], 1), (1, t.sky[1], 1)], y2=H0),
        grad(glow, [(0, a[0], 0), (0.15, a[0], 0.7), (0.6, a[3], 0.35), (1, a[4], 0)], y1=H0, y2=H0 - 110),
        el("filter", el("feGaussianBlur", stdDeviation=10), id=f"{glow}b", x="-5%", y="-50%", width="110%",
           height="200%"),
        el("mask", rr(0, H0, W, H - H0, fill=f"url(#{fade}g)"), id=fade),
        grad(f"{fade}g", [(0, "#fff", 0.8), (1, "#fff", 0)], y1=H0, y2=H),
    )
    doc.css(
        ".sway{animation:sway 13s ease-in-out infinite alternate}",
        "@keyframes sway{from{transform:translateX(-12px)}to{transform:translateX(12px)}}",
        ".tw{animation:tw 4s ease-in-out infinite}@keyframes tw{50%{opacity:.15}}",
        ".in{animation:in 1.2s cubic-bezier(.2,.8,.2,1) both}",
        "@keyframes in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}",
    )
    counts = [c for _, c in s["days"]]
    top = math.log1p(max(counts) or 1)
    hs = _smooth(_rolling_max([8 + 70 * math.log1p(c) / top if c else 6 for c in counts], 6), 8)
    dx = W / max(len(hs) - 1, 1)
    curtain = [(i * dx, H0 - 12 - h) for i, h in enumerate(hs)]

    body = [rr(0, 0, W, H0 + 1, fill=f"url(#{sky})")]
    if t.dark:
        stars = []
        for i in range(90):
            x, y = rng.uniform(0, W), rng.uniform(4, H0 - 30)
            r, o, delay = rng.uniform(0.3, 1.1), rng.uniform(0.2, 0.8), rng.uniform(0, 4)
            if 220 < x < W - 220 and y < 104:  # keep the sign-off clear
                continue
            stars.append(el("circle", cx=round(x, 1), cy=round(y, 1), r=round(r, 2), fill="#fff", opacity=round(o, 2),
                            **({"class_": "tw", "style": f"animation-delay:-{delay:.1f}s"} if i % 3 == 0 else {})))
        body.append(g("".join(stars)))
    aur = doc.uid("aur")
    body.append(g(el("path", d=_poly(curtain, H0), fill=f"url(#{glow})", filter=f"url(#{glow}b)", class_="sway",
                     opacity=0.7 if t.dark else 0.45), id=aur))
    ridges = doc.uid("rdg")
    body.append(g(el("path", d=_poly(_ridge(rng, H0 - 4, 40, fjord=0.8), H0 + 1), fill=t.ridge_far)
                  + el("path", d=_poly(_ridge(rng, H0 + 1, 16, 4, fjord=0.9), H0 + 1), fill=t.ridge_near), id=ridges))
    body.append(rr(0, H0, W, H - H0, fill=t.water))
    body.append(g(g(el("use", href=f"#{aur}") + el("use", href=f"#{ridges}"),
                    transform=f"matrix(1 0 0 -0.5 0 {H0 * 1.5})"), mask=f"url(#{fade})", opacity=0.45))
    body.append(el("line", x1=0, y1=H0 + 0.5, x2=W, y2=H0 + 0.5, stroke=a[1], stroke_opacity=0.3))
    body.append(g(
        doc.text(W / 2, 62, "Takk for besøket.", "serif-i", 40, t.ink, anchor="middle")
        + doc.text(W / 2, 90, "THANKS FOR STOPPING BY · HA DET BRA", "mono", 10.5, t.ink2, anchor="middle",
                   tracking=2.4),
        class_="in"))
    body.append(doc.text(26, H - 20, f"assets regenerated {s['as_of']:%d %b %Y} · python -m generator", "mono", 10,
                         t.ink3))
    body.append(doc.text(W - 26, H - 20, "set in Geist & Instrument Serif", "mono", 10, t.ink3, anchor="end"))
    doc.add(g("".join(body), clip_path=f"url(#{clip})"), rr(0.5, 0.5, W - 1, H - 1, 18, fill="none", stroke=t.line2))
    return doc.render()
