from __future__ import annotations

from generator.data import compact_languages, contribution_series, streaks
from generator.sections.svg import PALETTES, document, rect, section_heading, text

WEEKDAYS = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")


def render(data: dict, theme: str) -> str:
    palette = PALETTES[theme]
    days = contribution_series(data)
    total = int(data.get("total_contributions", sum(day["count"] for day in days)))
    active = sum(day["count"] > 0 for day in days)
    current, longest = streaks(days)
    commits = int(data.get("commits", 0))
    prs = int(data.get("pull_requests", 0))
    body = section_heading("02", "Live telemetry", "stream.github  ● DAILY", palette)
    cards = [
        ("CONTRIBUTIONS · 365D", f"{total:,}", f"≈ {total / 365:.1f} per day · best {max((d['count'] for d in days), default=0)}"),
        ("ACTIVE DAYS", f"{active} / 365", f"{active * 100 // 365}% of the year · {365 - active} quiet"),
        ("STREAK", f"{current} days", f"longest {longest} · current run"),
        ("COMMITS & PRS", f"{commits:,} commits", f"{prs:,} pull requests opened"),
    ]
    x_positions = (30, 320, 610, 900)
    for index, ((label, value, detail), x) in enumerate(zip(cards, x_positions)):
        body += rect(x, 98, 270, 192, palette["panel"], 18, palette["line"])
        body += text(x + 22, 130, label, 12, palette["faint"], "mono", 700, 'letter-spacing="1"')
        body += text(x + 22, 185, value, 30, palette["ink"], "sans", 700)
        body += text(x + 22, 212, detail, 12, palette["muted"], "sans")
        if index == 0:
            bars = days[-60:]
            max_value = max((item["count"] for item in bars), default=1) or 1
            for bar_index, item in enumerate(bars):
                height = 8 + 30 * item["count"] / max_value
                body += rect(x + 22 + bar_index * 3.65, 274 - height, 2.2, height,
                             palette["cyan"], 1, extra='opacity=".78"')
        elif index == 1:
            for day_index, item in enumerate(days[-56:]):
                row, col = divmod(day_index, 14)
                opacity = min(.9, .18 + item["count"] / 10)
                body += rect(x + 23 + col * 15, 235 + row * 9, 6, 5, palette["violet"], 1,
                             extra=f'opacity="{opacity:.2f}"')
        elif index == 2:
            for dot in range(14):
                cx, cy = x + 26 + (dot % 7) * 29, 246 + (dot // 7) * 19
                body += f'<circle cx="{cx}" cy="{cy}" r="5" fill="{palette["panel2"]}" stroke="{palette["line"]}"/>'
        else:
            total_activity = max(commits + prs, 1)
            commit_width = 224 * commits / total_activity
            body += rect(x + 22, 247, commit_width, 13, palette["cyan"], 5)
            body += rect(x + 22 + commit_width, 247, max(0, 224 - commit_width), 13,
                         palette["violet"], 5)
    body += rect(30, 310, 700, 198, palette["panel"], 18, palette["line"])
    body += text(54, 343, f'LANGUAGES · BYTES · {data.get("language_repo_count", 0)} REPOS'
                 f'{" (INCL. PRIVATE)" if data.get("language_scope") == "all" else ""}',
                 12, palette["faint"], "mono", 700, 'letter-spacing="1"')
    languages = compact_languages(data.get("languages", []), 7)
    total_bytes = sum(item["bytes"] for item in languages) or 1
    cursor = 0
    language_colors = (palette["blue"], "#427ca8", palette["orange"], "#ed5535",
                       palette["gold"], palette["violet"], palette["faint"], palette["line"])
    for idx, item in enumerate(languages):
        width = 650 * item["bytes"] / total_bytes
        body += rect(54 + cursor, 365, width, 15, language_colors[idx % len(language_colors)], 2)
        cursor += width
        col = idx // 4
        row = idx % 4
        xpos = 54 + col * 340
        ypos = 414 + row * 23
        body += rect(xpos, ypos - 10, 11, 11, language_colors[idx % len(language_colors)], 3)
        body += text(xpos + 20, ypos, item["name"], 13, palette["ink"])
        body += text(xpos + 292, ypos, f'{item["percent"]:.1f}%', 13, palette["muted"],
                     "mono", 500, 'text-anchor="end"')
    body += rect(750, 310, 420, 198, palette["panel"], 18, palette["line"])
    weekly = data.get("weekly", [0] * 7)
    weekly = (weekly + [0] * 7)[:7]
    max_weekday = max(weekly, default=0) or 1
    busiest = WEEKDAYS[max(range(7), key=lambda index: weekly[index])]
    body += text(775, 343, "WEEKLY RHYTHM", 12, palette["faint"], "mono", 700, 'letter-spacing="1"')
    body += text(1145, 343, f"busiest: {busiest.title()}", 12, palette["violet"], "mono", 600,
                 'text-anchor="end"')
    for index, (day, value) in enumerate(zip(WEEKDAYS, weekly)):
        x = 777 + index * 51
        height = 100 * value / max_weekday
        body += text(x + 16, 377 - height, str(value), 11, palette["muted"], "mono", 500,
                     'text-anchor="middle"')
        body += rect(x, 389 - height, 32, height, palette["violet"] if index == weekly.index(max(weekly))
                     else palette["line"], 5)
        body += text(x + 16, 433, day, 9, palette["faint"], "mono", 500, 'text-anchor="middle"')
    date_text = data.get("generated_at", "snapshot") or "snapshot"
    body += text(34, 539, f"source: GitHub GraphQL API · snapshot {date_text} · regenerated daily by GitHub Actions",
                 11, palette["faint"], "mono")
    return document(theme, "telemetry", "Live GitHub telemetry", "Contribution, repository, language, and rhythm metrics.",
                    1200, 570, body)
