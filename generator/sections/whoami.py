from generator.content import CONTENT, profile
from generator.sections.svg import PALETTES, document, line, rect, section_heading, text


def render(data: dict, theme: str) -> str:
    palette = PALETTES[theme]
    details = CONTENT["whoami"]
    body = section_heading("01", "whoami", "notebook.sql", palette)
    body += rect(30, 96, 1140, 176, palette["panel"], 18, palette["line"])
    body += text(58, 128, "In [01]:", 13, palette["violet"], "mono", 600)
    body += text(160, 128, "SELECT", 15, palette["blue"], "mono", 700)
    body += text(225, 128, "name, role, location, focus", 15, palette["ink"], "mono")
    body += text(160, 156, "FROM", 15, palette["blue"], "mono", 700)
    body += text(220, 156, "sai.prudhvi_neelakantam;", 15, palette["gold"], "mono")
    body += line(58, 174, 1142, 174, palette["line"], 1)
    body += text(58, 206, f'{profile["name"]}  ·  {profile["role"]}', 18, palette["ink"], "sans", 700)
    body += text(58, 237, f'{profile["location"]}  ·  {details["degree"]}', 14, palette["muted"])
    body += text(58, 258, f'{details["languages"]}  ·  {details["interests"]}', 13, palette["faint"])
    return document(theme, "whoami", "Who I am", "Profile details in a SQL notebook cell.",
                    1200, 300, body)
