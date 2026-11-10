from __future__ import annotations

from datetime import date
import math

from generator.content import profile
from generator.data import contribution_series
from generator.sections.svg import PALETTES, document, line, rect, text


MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")


def render(data: dict, theme: str) -> str:
    palette = PALETTES[theme]
    days = contribution_series(data)
    left, plot_width = 32, 1136
    base_y, max_height = 405, 205
    cell = plot_width / len(days)
    bars = []
    reflections = []
    months = []
    for index, item in enumerate(days):
        x = left + index * cell
        count = item["count"]
        height = math.log1p(count) / math.log1p(max((day["count"] for day in days), default=0) or 1) * max_height
        fill = palette["cyan"] if count > 0 else palette["line"]
        bars.append(rect(x, base_y - height, max(1.2, cell * .67), max(1, height), fill, 1,
                         extra=f'opacity="{.34 + .66 * min(1, count / 8):.2f}"'))
        if count:
            reflections.append(rect(x, base_y + 50, max(1.2, cell * .67), max(1, height * .32),
                                    palette["blue"], 1, extra='opacity=".24"'))
        current_date = date.fromisoformat(item["date"])
        if current_date.day == 1:
            months.append(text(x, 470, MONTHS[current_date.month - 1], 12, palette["muted"],
                               "mono", 600, 'letter-spacing=".7"'))
    total = int(data.get("total_contributions", sum(item["count"] for item in days)))
    begin = date.fromisoformat(days[0]["date"])
    finish = date.fromisoformat(days[-1]["date"])
    body = (
        text(58, 68, f'{profile["latitude"]}° N · {profile["longitude"]}° E · {profile["location"].upper()}',
             13, palette["muted"], "mono", 600, 'letter-spacing="2"')
        + text(56, 154, profile["first_name"], 64, palette["ink"], "serif")
        + text(56, 224, profile["surname"], 66, palette["cyan"], "serif", 600, 'font-style="italic"')
        + text(58, 272, f'{profile["role"]} · {profile["company"]}', 19, palette["ink"], "sans", 700)
        + text(58, 305, profile["focus"], 16, palette["muted"], "sans", 400)
        + rect(710, 42, 430, 42, palette["panel2"], 21, palette["line"])
        + f'<circle cx="735" cy="63" r="5" fill="{palette["green"]}"/>'
        + text(754, 69, "NOW · building Foundry agent front doors", 13, palette["muted"], "mono", 600)
        + f'<path class="aurora" d="M30 378 Q180 280 340 366 T650 355 T940 336 T1170 370 V410 H30Z" '
          f'fill="url(#hero-aurora)" opacity=".16"/>'
        + "".join(bars)
        + line(32, base_y, 1168, base_y, palette["line"], 2)
        + rect(28, base_y + 1, 1144, 53, palette["water"])
        + "".join(reflections)
        + "".join(months)
        + text(58, 524, "↑ THE AURORA IS DATA", 12, palette["cyan"], "mono", 700, 'letter-spacing="1"')
        + text(225, 524, "one ray per day on GitHub · height = contributions (log)", 12, palette["muted"], "mono")
        + text(1140, 524, f"{total:,} contributions · {begin:%d %b %Y} → {finish:%d %b %Y}",
               12, palette["faint"], "mono", 500, 'text-anchor="end"')
    )
    css = (
        '@keyframes aurora{0%,100%{opacity:.82}50%{opacity:1}}'
        '.aurora{animation:aurora 8s ease-in-out infinite}'
        '@media(prefers-reduced-motion:reduce){.aurora{animation:none}}'
    )
    return document(theme, "hero", profile["name"], "A year of GitHub contributions over the Oslofjord.",
                    1200, 560, body, css)
