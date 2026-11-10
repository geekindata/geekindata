"""Tiny SVG document builder that tracks glyph usage for font subsetting."""

from __future__ import annotations

from collections import defaultdict
from xml.sax.saxutils import escape

from .fonts import FACES, face

REDUCED_MOTION = "@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}"


def fmt(v) -> str:
    if isinstance(v, float):
        s = f"{v:.2f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    return str(v)


def esc(s) -> str:
    return escape(str(s), {'"': "&quot;"})


def el(tag: str, content: str | None = None, **attrs) -> str:
    """Build an element. `stroke_width=1` -> stroke-width, `class_=` -> class."""
    parts = []
    for k, v in attrs.items():
        if v is None or v is False:
            continue
        name = k.rstrip("_").replace("_", "-")
        parts.append(f' {name}="{esc(fmt(v))}"')
    a = "".join(parts)
    return f"<{tag}{a}/>" if content is None else f"<{tag}{a}>{content}</{tag}>"


def g(content: str, **attrs) -> str:
    return el("g", content, **attrs)


class Doc:
    def __init__(self, width: float, height: float, title: str, desc: str, theme):
        self.w = width
        self.h = height
        self.title = title
        self.desc = desc
        self.t = theme
        self._defs: list[str] = []
        self._css: list[str] = []
        self._body: list[str] = []
        self._used: dict[str, set[str]] = defaultdict(set)
        self._n = 0

    def uid(self, prefix: str = "i") -> str:
        self._n += 1
        return f"{prefix}{self._n}"

    def add(self, *parts: str) -> None:
        self._body.extend(parts)

    def defs(self, *parts: str) -> None:
        self._defs.extend(parts)

    def css(self, *rules: str) -> None:
        self._css.extend(rules)

    def text(self, x, y, s: str, font: str = "sans", size: float = 14, fill: str | None = None,
             anchor: str | None = None, tracking: float = 0, **attrs) -> str:
        s = str(s)
        self._used[font].update(s)
        cls = f"f-{font}" + (f" {attrs.pop('class_')}" if "class_" in attrs else "")
        return el("text", esc(s), x=x, y=y, class_=cls, font_size=size, fill=fill or self.t.ink,
                  text_anchor=anchor if anchor and anchor != "start" else None,
                  letter_spacing=tracking or None, **attrs)

    def spans(self, x, y, runs: list[tuple], size: float = 14, anchor: str | None = None, **attrs) -> str:
        """runs: (text, font, fill[, size]) tuples rendered as one <text> line."""
        inner = []
        for run in runs:
            s, font, fill = run[0], run[1], run[2]
            rsize = run[3] if len(run) > 3 else None
            self._used[font].update(s)
            inner.append(el("tspan", esc(s), class_=f"f-{font}", fill=fill, font_size=rsize))
        return el("text", "".join(inner), x=x, y=y, font_size=size,
                  text_anchor=anchor if anchor and anchor != "start" else None, **attrs)

    def textpath(self, href: str, s: str, font: str, size: float, fill: str, tracking: float = 0) -> str:
        self._used[font].update(s)
        tp = el("textPath", esc(s), href=f"#{href}")
        return el("text", tp, class_=f"f-{font}", font_size=size, fill=fill, letter_spacing=tracking or None)

    def render(self) -> str:
        font_css = []
        for key in sorted(self._used):
            chars = "".join(self._used[key])
            f = face(key)
            fam = "g" + key.replace("-", "")
            weight = FACES[key][1] or 400
            style = "italic" if f.italic else "normal"
            font_css.append(
                f"@font-face{{font-family:{fam};src:url({f.woff2_data_uri(chars)}) format('woff2');"
                f"font-weight:{weight};font-style:{style};font-display:block}}"
            )
            font_css.append(f".f-{key}{{font-family:{fam},{f.fallback};font-weight:{weight};font-style:{style}}}")
        css = "".join(font_css + self._css + [REDUCED_MOTION])
        head = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{fmt(self.w)}" height="{fmt(self.h)}" '
            f'viewBox="0 0 {fmt(self.w)} {fmt(self.h)}" role="img" aria-labelledby="title desc">'
        )
        return "".join([
            head,
            el("title", esc(self.title), id="title"),
            el("desc", esc(self.desc), id="desc"),
            f"<style>{css}</style>",
            f"<defs>{''.join(self._defs)}</defs>" if self._defs else "",
            *self._body,
            "</svg>",
        ])


def rr(x, y, w, h, r=0, **attrs) -> str:
    return el("rect", x=x, y=y, width=w, height=h, rx=r or None, **attrs)


def card(t, x, y, w, h, r=14, **attrs) -> str:
    return rr(x + 0.5, y + 0.5, w - 1, h - 1, r, fill=t.panel, stroke=t.line, **attrs)


def chip(doc: "Doc", x, y, text: str, fg: str, bg: str | None = None, font: str = "mono", size: float = 10.5,
         h: float = 20, pad: float = 8, stroke: str | None = None, tracking: float = 0) -> tuple[str, float]:
    """Pill with text; (x, y) is the top-left. Returns (svg, width)."""
    w = face(font).width(text, size, tracking) + pad * 2
    svg = rr(x, y, w, h, h / 2, fill=bg or "none", stroke=stroke) + doc.text(
        x + pad, y + h / 2 + size * 0.36, text, font, size, fg, tracking=tracking)
    return svg, w


FADE_UP = ("@keyframes up{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}"
           ".up{animation:up .9s cubic-bezier(.2,.8,.2,1) both}")


def check_path(x: float, y: float, s: float, color: str, width: float = 1.6) -> str:
    """A checkmark drawn as a path (no font has U+2713)."""
    d = f"M{fmt(x)},{fmt(y + s * 0.55)} L{fmt(x + s * 0.38)},{fmt(y + s * 0.9)} L{fmt(x + s)},{fmt(y + s * 0.12)}"
    return el("path", d=d, fill="none", stroke=color, stroke_width=width, stroke_linecap="round",
              stroke_linejoin="round")


def arrow_ne(x: float, y: float, s: float, color: str, width: float = 1.4) -> str:
    d = (f"M{fmt(x)},{fmt(y + s)} L{fmt(x + s)},{fmt(y)} M{fmt(x + s * 0.3)},{fmt(y)} "
         f"L{fmt(x + s)},{fmt(y)} L{fmt(x + s)},{fmt(y + s * 0.7)}")
    return el("path", d=d, fill="none", stroke=color, stroke_width=width, stroke_linecap="round",
              stroke_linejoin="round")
