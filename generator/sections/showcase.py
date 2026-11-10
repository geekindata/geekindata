from __future__ import annotations

from generator.content import CONTENT, profile
from generator.sections.svg import PALETTES, document, rect, section_heading, text


def render_stack(data: dict, theme: str) -> str:
    palette = PALETTES[theme]
    groups = {
        "Data platform": palette["cyan"], "Analytics & BI": palette["gold"],
        "AI & agents": palette["violet"], "Engineering": palette["blue"],
    }
    items = CONTENT["stack"]
    body = section_heading("03", "The stack", "silver.stack", palette)
    body += text(150, 128, "The periodic table of my stack", 31, palette["ink"], "serif")
    body += text(152, 157, f"{len(items)} ELEMENTS · GROUPED BY WHAT THEY DO · CORE ELEMENTS GLOW",
                 12, palette["faint"], "mono", 600, 'letter-spacing="1"')
    for index, item in enumerate(items):
        row, col = divmod(index, 7)
        x, y = 30 + col * 163, 183 + row * 104
        color = groups[item["group"]]
        body += rect(x, y, 150, 92, palette["panel"], 15, color if item.get("core") else palette["line"],
                     f'stroke-width="{2 if item.get("core") else 1}"')
        body += text(x + 12, y + 20, f"{index + 1}", 10, palette["faint"], "mono")
        if item.get("core"):
            body += f'<circle cx="{x + 132}" cy="{y + 16}" r="4" fill="{color}"/>'
        body += text(x + 75, y + 53, item["symbol"], 30, color if item.get("core") else palette["ink"],
                     "sans", 700, 'text-anchor="middle"')
        body += text(x + 75, y + 76, item["name"], 11, palette["muted"], "sans", 500,
                     'text-anchor="middle"')
    return document(theme, "stack", "The stack", "Technology periodic table, grouped by role.",
                    1200, 620, body)


def render_projects(data: dict, theme: str) -> str:
    palette = PALETTES[theme]
    projects = CONTENT["project"]
    body = section_heading("04", "Selected work", "lakehouse.projects", palette)
    colors = (palette["cyan"], palette["violet"], palette["blue"], palette["gold"])
    for index, project in enumerate(projects):
        col, row = index % 2, index // 2
        x, y = 30 + col * 570, 100 + row * 174
        color = colors[index % len(colors)]
        body += rect(x, y, 550, 152, palette["panel"], 18, palette["line"])
        body += rect(x, y, 5, 152, color, 3)
        body += text(x + 26, y + 32, project["eyebrow"], 11, color, "mono", 700,
                     'letter-spacing="1"')
        body += text(x + 26, y + 69, project["name"], 25, palette["ink"], "serif")
        body += text(x + 26, y + 98, project["description"], 13, palette["muted"])
        body += text(x + 26, y + 127, project["tools"], 11, palette["faint"], "mono")
    return document(theme, "projects", "Selected work", "Selected data platform and AI projects.",
                    1200, 470, body)


def render_talks(data: dict, theme: str) -> str:
    palette = PALETTES[theme]
    talks = CONTENT["talk"]
    body = section_heading("05", "On the road", "talks.setlist", palette)
    for index, talk in enumerate(talks):
        x = 30 + index * 285
        accent = (palette["cyan"], palette["violet"], palette["gold"], palette["blue"])[index]
        body += rect(x, 106, 265, 266, palette["panel"], 16, palette["line"])
        body += text(x + 22, 139, f"{int(talk['year']):04d} / 0{index + 1}", 12, accent,
                     "mono", 700, 'letter-spacing="1"')
        body += text(x + 22, 197, _wrap(talk["title"], 25), 22, palette["ink"], "serif")
        body += text(x + 22, 315, _wrap(talk["event"], 31), 12, palette["muted"], "sans", 500)
        body += line_at(x + 22, 342, x + 105, accent, palette)
    body += f'<a href="{profile["sessionize"]}" target="_blank" rel="noopener">'
    body += f'<circle class="spin" cx="1080" cy="434" r="68" fill="none" stroke="{palette["violet"]}" '
    body += 'stroke-width="1.5" stroke-dasharray="3 7"/>'
    body += f'<circle cx="1080" cy="434" r="62" fill="{palette["panel2"]}" stroke="{palette["violet"]}" stroke-width="2"/>'
    body += text(1080, 427, "SESSIONIZE", 12, palette["violet"], "mono", 700,
                 'text-anchor="middle" letter-spacing="1"')
    body += text(1080, 449, "SPEAKER", 12, palette["ink"], "mono", 600, 'text-anchor="middle"')
    body += "</a>"
    body += text(54, 442, "Fabric · Azure AI · Databricks · Nordic data community", 13,
                 palette["faint"], "mono")
    css = (
        '@keyframes spin{to{transform:rotate(360deg)}}'
        '.spin{transform-origin:1080px 434px;animation:spin 24s linear infinite}'
        '@media(prefers-reduced-motion:reduce){.spin{animation:none}}'
    )
    return document(theme, "talks", "Conference talks", "Selected conference talks and speaking topics.",
                    1200, 500, body, css)


def line_at(x: int, y: int, width: int, color: str, palette: dict) -> str:
    return f'<path d="M{x},{y} h{width}" stroke="{color}" stroke-width="3"/>' + \
        f'<path d="M{x},{y + 7} h{width + 35}" stroke="{palette["line"]}" stroke-width="1"/>'


def _wrap(value: str, limit: int) -> str:
    words = value.split()
    lines, line = [], ""
    for word in words:
        if len(line) + len(word) + bool(line) > limit:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        lines.append(line)
    return "\n".join(lines)
