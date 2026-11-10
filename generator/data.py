from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
import json
import urllib.request
import xml.etree.ElementTree as ET

API_URL = "https://api.github.com/graphql"
USER_AGENT = "geekindata-profile-generator"


class _TextOnly(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def clean_text(value: str) -> str:
    parser = _TextOnly()
    parser.feed(value)
    text = " ".join("".join(parser.parts).split())
    return text.replace("—", "-").replace("–", "-").replace("−", "-")


def _request(url: str, headers: dict[str, str]) -> bytes:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def _fetch_github(token: str, start: date, end: date, include_private: bool) -> dict:
    privacy_filter = "" if include_private else ", privacy: PUBLIC"
    collection = None
    repo_count = 0
    language_bytes: dict[str, int] = {}
    cursor = None
    while True:
        contribution_fields = ""
        if cursor is None:
            contribution_fields = f"""
            contributionsCollection(from: "{start.isoformat()}T00:00:00Z", to: "{end.isoformat()}T23:59:59Z") {{
              totalCommitContributions
              totalPullRequestContributions
              contributionCalendar {{
                totalContributions
                weeks {{
                  contributionDays {{ date contributionCount weekday }}
                }}
              }}
            }}
            }}"""
        query = f"""
        query($cursor: String) {{
          user(login: "geekindata") {{
            {contribution_fields}
            repositories(first: 100, after: $cursor, ownerAffiliations: OWNER{privacy_filter}, isFork: false) {{
              totalCount
              pageInfo {{ hasNextPage endCursor }}
              nodes {{ languages(first: 100, orderBy: {{field: SIZE, direction: DESC}}) {{
                edges {{ size node {{ name }} }}
              }} }}
            }}
          }}
        }}
        """
        payload = json.dumps({"query": query, "variables": {"cursor": cursor}}).encode("utf-8")
        request = urllib.request.Request(API_URL, data=payload, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        })
        with urllib.request.urlopen(request, timeout=30) as result:
            data = json.loads(result.read())
        if data.get("errors"):
            raise RuntimeError("GitHub GraphQL returned an error.")
        user = data.get("data", {}).get("user")
        if not user:
            raise RuntimeError("GitHub GraphQL did not return the profile user.")
        if collection is None:
            collection = user["contributionsCollection"]
        repositories = user["repositories"]
        repo_count = repositories.get("totalCount", repo_count)
        for repository in repositories.get("nodes", []):
            for edge in repository.get("languages", {}).get("edges", []):
                name = edge["node"]["name"]
                language_bytes[name] = language_bytes.get(name, 0) + edge["size"]
        page_info = repositories["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        next_cursor = page_info.get("endCursor")
        if not next_cursor or next_cursor == cursor:
            raise RuntimeError("GitHub repository pagination did not advance.")
        cursor = next_cursor

    calendar = collection["contributionCalendar"]
    days = [day for week in calendar.get("weeks", []) for day in week.get("contributionDays", [])]
    return {
        "contributions": days,
        "total_contributions": calendar.get("totalContributions", 0),
        "commits": collection.get("totalCommitContributions", 0),
        "pull_requests": collection.get("totalPullRequestContributions", 0),
        "languages": [
            {"name": name, "bytes": size}
            for name, size in sorted(language_bytes.items(), key=lambda item: (-item[1], item[0]))
        ],
        "language_repo_count": repo_count,
        "language_scope": "all" if include_private else "public",
    }


def _fetch_feed(url: str) -> list[dict[str, str]]:
    data = _request(url, {"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml"})
    root = ET.fromstring(data)
    posts = []
    for item in root.findall(".//item")[:5]:
        title = clean_text(item.findtext("title", ""))
        link = item.findtext("link", "").strip()
        if title and link.startswith(("https://", "http://")):
            posts.append({"title": title, "url": link})
    if not posts:
        atom = "{http://www.w3.org/2005/Atom}"
        for entry in root.findall(f".//{atom}entry")[:5]:
            title = clean_text(entry.findtext(f"{atom}title", ""))
            link = next((node.get("href", "") for node in entry.findall(f"{atom}link")
                         if node.get("rel", "alternate") == "alternate"), "")
            if title and link.startswith(("https://", "http://")):
                posts.append({"title": title, "url": link})
    return posts


def fetch_live_data(token: str, previous: dict, include_private: bool = False) -> dict:
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=364)
    github = _fetch_github(token, start, end, include_private)
    from generator.content import profile
    feed = _fetch_feed(profile["rss"])

    if not include_private and previous.get("language_scope") == "all":
        github["languages"] = previous.get("languages", [])
        github["language_repo_count"] = previous.get("language_repo_count", github["language_repo_count"])
        github["language_scope"] = "all"
    return {
        "username": "geekindata",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        **github,
        "weekly": _weekday_totals(github["contributions"]),
        "feed": feed,
    }


def _weekday_totals(days: list[dict]) -> list[int]:
    totals = [0] * 7
    for item in days:
        try:
            day = date.fromisoformat(item["date"])
            totals[day.weekday()] += int(item.get("contributionCount", 0))
        except (KeyError, TypeError, ValueError):
            continue
    return totals


def contribution_series(snapshot: dict, today: date | None = None) -> list[dict]:
    snapshot_end = snapshot.get("window_end")
    if not snapshot_end and snapshot.get("generated_at"):
        snapshot_end = snapshot["generated_at"][:10]
    try:
        end = today or date.fromisoformat(snapshot_end)
    except (TypeError, ValueError):
        end = today or datetime.now(timezone.utc).date()
    start = end - timedelta(days=364)
    values = {}
    for item in snapshot.get("contributions", []):
        try:
            values[date.fromisoformat(item["date"])] = max(0, int(item.get("contributionCount", 0)))
        except (KeyError, TypeError, ValueError):
            continue
    return [
        {"date": (start + timedelta(days=index)).isoformat(),
         "count": values.get(start + timedelta(days=index), 0)}
        for index in range(365)
    ]


def streaks(days: list[dict]) -> tuple[int, int]:
    counts = [max(0, int(item.get("count", 0))) for item in days]
    longest = current = run = 0
    for count in counts:
        run = run + 1 if count else 0
        longest = max(longest, run)
    trailing = len(counts)
    if trailing and counts[-1] == 0:
        trailing -= 1
    for count in reversed(counts[:trailing]):
        if count == 0:
            break
        current += 1
    return current, longest


def compact_languages(languages: list[dict], limit: int = 8) -> list[dict[str, int | str]]:
    valid = [
        {"name": str(item["name"]), "bytes": max(0, int(item.get("bytes", 0)))}
        for item in languages
        if item.get("name") and int(item.get("bytes", 0)) > 0
    ]
    valid.sort(key=lambda item: (-item["bytes"], item["name"]))
    top = valid[:limit]
    other_bytes = sum(item["bytes"] for item in valid[limit:])
    if other_bytes:
        top.append({"name": "Other", "bytes": other_bytes})
    total = sum(item["bytes"] for item in top)
    for item in top:
        item["percent"] = round(item["bytes"] * 100 / total, 1) if total else 0
    return top
