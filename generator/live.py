"""Fetch live data (GitHub GraphQL + blog RSS) and derive profile stats.

The result is snapshotted to data/live.json so builds also work offline and
a failed API call never wipes the profile.
"""

from __future__ import annotations

import json
import math
import os
import sys
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree

SNAPSHOT = Path(__file__).resolve().parent.parent / "data" / "live.json"

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        isPrivate
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def _http(url: str, data: bytes | None = None, headers: dict | None = None) -> bytes:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "geekindata-profile", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def fetch_github(login: str, token: str) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    raw = _http("https://api.github.com/graphql", body, {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
    })
    payload = json.loads(raw)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    user = payload["data"]["user"]
    cc = user["contributionsCollection"]
    days = [
        [d["date"], d["contributionCount"]]
        for w in cc["contributionCalendar"]["weeks"]
        for d in w["contributionDays"]
    ]
    langs: Counter = Counter()
    colors: dict[str, str] = {}
    repos = user["repositories"]["nodes"]
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            langs[edge["node"]["name"]] += edge["size"]
            colors[edge["node"]["name"]] = edge["node"]["color"] or "#8b949e"
    return {
        "days": days,
        "total": cc["contributionCalendar"]["totalContributions"],
        "commits": cc["totalCommitContributions"],
        "pull_requests": cc["totalPullRequestContributions"],
        "reviews": cc["totalPullRequestReviewContributions"],
        "issues": cc["totalIssueContributions"],
        "repos": user["repositories"]["totalCount"],
        "languages": [[name, size, colors[name]] for name, size in langs.most_common()],
        "languages_include_private": any(r["isPrivate"] for r in repos),
    }


def no_em_dash(text: str) -> str:
    return text.replace(" \u2014 ", ", ").replace("\u2014", ", ")


def fetch_notes(feed_url: str, limit: int) -> dict:
    root = ElementTree.fromstring(_http(feed_url))
    items = root.findall("./channel/item")
    notes = []
    for item in items[:limit]:
        published = parsedate_to_datetime(item.findtext("pubDate", ""))
        notes.append({
            "title": no_em_dash(item.findtext("title", "").strip()),
            "link": item.findtext("link", "").strip(),
            "date": published.date().isoformat(),
            "summary": no_em_dash(item.findtext("description", "").strip()),
        })
    return {"notes": notes, "notes_total": len(items)}


def load_snapshot() -> dict:
    return json.loads(SNAPSHOT.read_text()) if SNAPSHOT.exists() else {}


def refresh(login: str, feed_url: str, note_limit: int, offline: bool = False) -> dict:
    """Return live data, refreshing each source independently when possible."""
    data = load_snapshot()
    if offline:
        return data
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        try:
            gh = fetch_github(login, token)
            # A repo-scoped Actions token can't see private repos; keep the last
            # full-scope language mix instead of silently shrinking it.
            if not gh["languages_include_private"] and data.get("languages_include_private"):
                gh["languages"] = data["languages"]
                gh["languages_include_private"] = True
            data.update(gh)
            data["fetched"] = datetime.now(timezone.utc).date().isoformat()
        except Exception as exc:  # noqa: BLE001 - keep the snapshot on any failure
            print(f"warning: GitHub fetch failed, using snapshot: {exc}", file=sys.stderr)
    else:
        print("warning: no GH_TOKEN/GITHUB_TOKEN, using snapshot GitHub data", file=sys.stderr)
    try:
        data.update(fetch_notes(feed_url, note_limit))
    except Exception as exc:  # noqa: BLE001
        print(f"warning: RSS fetch failed, using snapshot notes: {exc}", file=sys.stderr)
    if not data.get("days"):
        raise SystemExit("no contribution data available (no token and no snapshot)")
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(data, indent=1) + "\n")
    return data


# ---------------------------------------------------------------- derived stats

def derive(data: dict) -> dict:
    days = [(date.fromisoformat(d), c) for d, c in data["days"]]
    as_of = date.fromisoformat(data.get("fetched") or days[-1][0].isoformat())
    days = [(d, c) for d, c in days if d <= as_of][-365:]
    counts = [c for _, c in days]

    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    current = 0
    tail = counts[:-1] if counts and counts[-1] == 0 else counts  # today isn't over yet
    for c in reversed(tail):
        if not c:
            break
        current += 1

    weekday = [0] * 7
    for d, c in days:
        weekday[d.weekday()] += c
    weekly = [sum(counts[i:i + 7]) for i in range(0, len(counts), 7)]
    best_day, best_count = max(days, key=lambda x: x[1])

    langs = data.get("languages", [])
    total_bytes = sum(s for _, s, _ in langs) or 1
    top = [(n, s / total_bytes, c) for n, s, c in langs[:6]]
    rest = 1 - sum(p for _, p, _ in top)
    if rest > 0.001:
        top.append(("Other", rest, None))

    total = sum(counts)
    return {
        "days": days,
        "start": days[0][0],
        "end": days[-1][0],
        "total": total,
        "active": sum(1 for c in counts if c),
        "per_day": total / max(len(counts), 1),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best_day,
        "best_count": best_count,
        "weekday": weekday,
        "weekly": weekly,
        "languages": top,
        "languages_private": data.get("languages_include_private", False),
        "commits": data.get("commits", 0),
        "pull_requests": data.get("pull_requests", 0),
        "reviews": data.get("reviews", 0),
        "repos": data.get("repos", 0),
        "notes": data.get("notes", []),
        "notes_total": data.get("notes_total", 0),
        "as_of": as_of,
        "max_day": max(counts) if counts else 0,
        "intensity": [math.sqrt(c) for c in counts],
    }
