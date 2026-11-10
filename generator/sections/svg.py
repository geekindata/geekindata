from __future__ import annotations

import base64
from html import escape
from io import BytesIO
import logging
import os
from pathlib import Path
import re

PALETTES = {
    "dark": {
        "bg": "#0c1016", "panel": "#10161f", "panel2": "#151d29", "ink": "#e6edf5",
        "muted": "#97a5b5", "faint": "#647284", "line": "#2a3440", "cyan": "#27d3c0",
        "blue": "#4aa9ff", "violet": "#ad83f5", "gold": "#f4cf4f", "orange": "#ff7048",
        "green": "#42c96b", "water": "#101b2a",
    },
    "light": {
        "bg": "#f3f6f7", "panel": "#ffffff", "panel2": "#eaf0f2", "ink": "#14212d",
        "muted": "#536575", "faint": "#778794", "line": "#d2dce0", "cyan": "#087f78",
        "blue": "#146bb3", "violet": "#7752b5", "gold": "#ae7900", "orange": "#bd4529",
        "green": "#18813d", "water": "#c7dbe0",
    },
}

FONT_FILES = {
    "ProfileSans": os.environ.get("PROFILE_FONT_SANS", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    "ProfileMono": os.environ.get("PROFILE_FONT_MONO", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    "ProfileSerif": os.environ.get("PROFILE_FONT_SERIF", "/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Italic.ttf"),
}


def esc(value: object) -> str:
    return escape(str(value), quote=True)


def text(x: float, y: float, value: object, size: int = 18, fill: str | None = None,
         family: str = "sans", weight: int = 400, extra: str = "") -> str:
    fonts = {"sans": "ProfileSans, sans-serif", "mono": "ProfileMono, monospace",
             "serif": "ProfileSerif, Georgia, serif"}
    color = f' fill="{fill}"' if fill else ""
    value = str(value)
    if "\n" in value:
        spans = "".join(
            f'<tspan x="{x:g}" dy="{0 if index == 0 else size * 1.15:g}">{esc(part)}</tspan>'
            for index, part in enumerate(value.splitlines())
        )
    else:
        spans = esc(value)
    return (f'<text x="{x:g}" y="{y:g}" font-family="{fonts[family]}" font-size="{size}" '
            f'font-weight="{weight}"{color} {extra}>{spans}</text>')


def rect(x: float, y: float, width: float, height: float, fill: str,
         radius: int = 0, stroke: str | None = None, extra: str = "") -> str:
    outline = f' stroke="{stroke}"' if stroke else ""
    return (f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" rx="{radius}" '
            f'fill="{fill}"{outline} {extra}/>')


def line(x1: float, y1: float, x2: float, y2: float, color: str,
         width: float = 1, extra: str = "") -> str:
    return (f'<path d="M{x1:g},{y1:g} L{x2:g},{y2:g}" fill="none" stroke="{color}" '
            f'stroke-width="{width:g}" {extra}/>')


def _embedded_fonts(svg_text: str) -> str:
    try:
        from fontTools import subset
        from fontTools.ttLib import TTFont
    except ImportError:
        return ""
    rules = []
    for family, path in FONT_FILES.items():
        font_path = Path(path)
        if not font_path.is_file():
            continue
        try:
            options = subset.Options()
            options.flavor = "woff2"
            font = TTFont(str(font_path))
            subsetter = subset.Subsetter(options=options)
            subsetter.populate(text=svg_text)
            logger = logging.getLogger("fontTools.subset")
            previous_level = logger.level
            logger.setLevel(logging.ERROR)
            try:
                subsetter.subset(font)
            finally:
                logger.setLevel(previous_level)
            font.flavor = "woff2"
            output = BytesIO()
            font.save(output)
        except Exception:
            continue
        encoded = base64.b64encode(output.getvalue()).decode("ascii")
        rules.append(
            f"@font-face{{font-family:'{family}';src:url(data:font/woff2;base64,{encoded}) format('woff2');font-display:swap}}"
        )
    return "".join(rules)


def document(theme: str, section: str, title: str, description: str,
             width: int, height: int, body: str, css: str = "") -> str:
    palette = PALETTES[theme]
    normalized = (title + description + body).replace("—", "-").replace("–", "-")
    font_css = _embedded_fonts(normalized)
    safe_section = re.sub(r"[^a-z0-9-]", "", section)
    background = rect(0, 0, width, height, f"url(#{safe_section}-bg)")
    border = rect(1, 1, width - 2, height - 2, "none", 24, palette["line"], 'stroke-width="1"')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="{safe_section}-title {safe_section}-desc">'
        f'<title id="{safe_section}-title">{esc(title)}</title>'
        f'<desc id="{safe_section}-desc">{esc(description)}</desc>'
        '<defs>'
        f'<linearGradient id="{safe_section}-bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{palette["bg"]}"/><stop offset="1" stop-color="{palette["panel"]}"/>'
        '</linearGradient>'
        f'<linearGradient id="{safe_section}-aurora" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{palette["cyan"]}"/><stop offset=".52" stop-color="{palette["blue"]}"/>'
        f'<stop offset="1" stop-color="{palette["violet"]}"/></linearGradient>'
        '</defs>'
        f'<style>{font_css}{css}</style>'
        f'{background}{border}'
        f'{body}</svg>'
    )


def section_heading(number: str, title: str, eyebrow: str, palette: dict) -> str:
    return (
        text(32, 54, number, 15, palette["violet"], "mono", 700, 'letter-spacing="1.5"')
        + text(78, 60, title, 36, palette["ink"], "serif")
        + text(1168, 53, eyebrow, 12, palette["faint"], "mono", 700,
               'text-anchor="end" letter-spacing="1.4"')
        + line(30, 78, 1170, 78, palette["line"], 1.5)
    )
