from generator.content import CONTENT
from generator.sections.svg import PALETTES, document, rect, section_heading, text


def render(data: dict, theme: str) -> str:
    palette = PALETTES[theme]
    accents = {
        "cyan": palette["cyan"], "gold": palette["gold"], "violet": palette["violet"],
        "blue": palette["blue"], "green": palette["green"],
    }
    certificates = CONTENT["certification"]
    body = section_heading("07", "Proof of craft", "verified.credentials", palette)
    for index, cert in enumerate(certificates):
        col, row = index % 3, index // 3
        x, y = 30 + col * 385, 110 + row * 178
        accent = accents[cert["accent"]]
        body += rect(x, y, 360, 148, palette["panel"], 18, accent)
        body += rect(x + 1, y + 1, 358, 4, accent, 2, extra='opacity=".8"')
        body += f'<circle cx="{x + 323}" cy="{y + 34}" r="16" fill="{accent}" opacity=".16"/>'
        body += text(x + 323, y + 40, "✓", 17, accent, "sans", 700, 'text-anchor="middle"')
        body += text(x + 24, y + 43, cert["issuer"], 11, accent, "mono", 700,
                     'letter-spacing="1.5"')
        body += text(x + 24, y + 83, cert["name"], 20, palette["ink"], "serif")
        body += text(x + 24, y + 120, "CERTIFIED · CONTINUOUSLY CURIOUS", 9,
                     palette["faint"], "mono", 600, 'letter-spacing=".8"')
    return document(theme, "certifications", "Professional certifications",
                    "Microsoft, Databricks, SAS, and SQL credentials.",
                    1200, 670, body)
