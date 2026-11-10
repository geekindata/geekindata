from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from generator.data import fetch_live_data
from generator.readme import build_readme
from generator.sections import render_sections

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "live.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the self-hosted profile README.")
    parser.add_argument("--offline", action="store_true", help="Render from the checked-in snapshot.")
    args = parser.parse_args()
    snapshot = load_snapshot()

    if not args.offline:
        token = os.environ.get("PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if token:
            updated, refreshed = refresh_snapshot(
                token,
                snapshot,
                include_private=bool(os.environ.get("PROFILE_TOKEN")),
            )
            if refreshed:
                snapshot = updated
                SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
                SNAPSHOT.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        else:
            print("No GitHub token found; rendering from the checked-in snapshot.", file=sys.stderr)

    sections = render_sections(snapshot)
    for theme, svg in sections.items():
        (ROOT / "assets" / f"{theme}.svg").write_text(svg, encoding="utf-8")
    (ROOT / "README.md").write_text(build_readme(snapshot), encoding="utf-8")
    return 0


def refresh_snapshot(token: str, previous: dict, include_private: bool = False) -> tuple[dict, bool]:
    try:
        return fetch_live_data(token, previous, include_private), True
    except Exception as error:
        print(f"Live data refresh failed; retaining the previous snapshot: {error}", file=sys.stderr)
        return previous, False


def load_snapshot() -> dict:
    if not SNAPSHOT.exists():
        return {}
    with SNAPSHOT.open(encoding="utf-8") as snapshot_file:
        return json.load(snapshot_file)


if __name__ == "__main__":
    raise SystemExit(main())
