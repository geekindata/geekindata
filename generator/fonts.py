"""Font loading, text measurement and per-SVG woff2 subsetting.

Fonts are embedded as base64 woff2 data URIs: GitHub serves SVGs with
`default-src 'none'`, so only self-contained fonts render inside <img>.
"""

from __future__ import annotations

import base64
import io
from functools import lru_cache
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FONT_DIR = Path(__file__).parent / "fonts"

# key -> (file, wght for variable fonts, css generic fallback)
FACES = {
    "sans": ("Geist.ttf", 400, "system-ui,-apple-system,'Segoe UI',sans-serif"),
    "sans-m": ("Geist.ttf", 500, "system-ui,-apple-system,'Segoe UI',sans-serif"),
    "sans-sb": ("Geist.ttf", 600, "system-ui,-apple-system,'Segoe UI',sans-serif"),
    "mono": ("GeistMono.ttf", 400, "ui-monospace,SFMono-Regular,Menlo,monospace"),
    "mono-m": ("GeistMono.ttf", 500, "ui-monospace,SFMono-Regular,Menlo,monospace"),
    "serif": ("InstrumentSerif-Regular.ttf", None, "Georgia,'Times New Roman',serif"),
    "serif-i": ("InstrumentSerif-Italic.ttf", None, "Georgia,'Times New Roman',serif"),
}


class Face:
    def __init__(self, key: str):
        file, wght, fallback = FACES[key]
        tt = TTFont(FONT_DIR / file)
        if wght is not None and "fvar" in tt:
            tt = instancer.instantiateVariableFont(tt, {"wght": wght})
        buf = io.BytesIO()
        tt.save(buf)
        self.key = key
        self.fallback = fallback
        self.italic = key.endswith("-i")
        self._blob = buf.getvalue()
        self._cmap = tt.getBestCmap()
        self._hmtx = tt["hmtx"].metrics
        self._upm = tt["head"].unitsPerEm
        self._missing_w = self._hmtx.get(".notdef", (self._upm // 2, 0))[0]

    def has(self, ch: str) -> bool:
        return ord(ch) in self._cmap

    def advance(self, ch: str) -> int:
        glyph = self._cmap.get(ord(ch))
        return self._hmtx[glyph][0] if glyph else self._missing_w

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        if not text:
            return 0.0
        units = sum(self.advance(c) for c in text)
        return units / self._upm * size + tracking * (len(text) - 1)

    def woff2_data_uri(self, chars: str) -> str:
        return _subset(self.key, "".join(sorted(set(chars))))


@lru_cache(maxsize=None)
def face(key: str) -> Face:
    return Face(key)


@lru_cache(maxsize=None)
def _subset(key: str, chars: str) -> str:
    f = face(key)
    tt = TTFont(io.BytesIO(f._blob))
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.hinting = False
    opts.desubroutinize = True
    opts.name_IDs = [1, 2]
    opts.layout_features = ["kern"]
    sub = subset.Subsetter(opts)
    sub.populate(text=chars + " ")
    sub.subset(tt)
    tt.flavor = "woff2"
    out = io.BytesIO()
    tt.save(out)
    return "data:font/woff2;base64," + base64.b64encode(out.getvalue()).decode()


def wrap(text: str, key: str, size: float, max_width: float, tracking: float = 0.0) -> list[str]:
    """Greedy word wrap using real glyph advances."""
    f = face(key)
    lines: list[str] = []
    line = ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if line and f.width(trial, size, tracking) > max_width:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return lines


def fit_size(text: str, key: str, size: float, max_width: float, min_size: float = 7.0) -> float:
    """Shrink font size until text fits max_width."""
    f = face(key)
    while size > min_size and f.width(text, size) > max_width:
        size -= 0.25
    return size
