from generator.content import CONTENT
from generator.sections.svg import PALETTES, document, line, rect, section_heading, text


def render(data: dict, theme: str) -> str:
    palette = PALETTES[theme]
    roles = CONTENT["career"]
    body = section_heading("06", "The career", "git log --graph", palette)
    body += line(80, 120, 80, 480, palette["violet"], 2)
    for index, role in enumerate(roles):
        y = 128 + index * 94
        color = palette["cyan"] if index == 0 else palette["blue"]
        body += f'<circle cx="80" cy="{y}" r="7" fill="{palette["bg"]}" stroke="{color}" stroke-width="3"/>'
        body += text(112, y + 5, f'* {role["period"]}', 12, color, "mono", 700,
                     'letter-spacing=".7"')
        body += rect(310, y - 28, 850, 72, palette["panel"], 14, palette["line"])
        body += text(334, y, role["role"], 17, palette["ink"], "sans", 700)
        body += text(1138, y, role["company"], 13, palette["violet"], "mono", 600,
                     'text-anchor="end"')
        body += text(334, y + 24, role["description"], 12, palette["muted"])
    return document(theme, "career", "Career timeline", "Career history as a Git log graph.",
                    1200, 550, body)
