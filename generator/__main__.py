"""Build every profile asset: `python -m generator [--offline]`."""

from __future__ import annotations

import argparse
import logging
import sys
import tomllib
from pathlib import Path

from . import live, readme
from .sections import credentials, footer, header, hero, lineage, nav, notebook, stack, stage, telemetry, work
from .theme import THEMES

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ASSETS = ROOT / "assets"

SECTIONS = [
    ("whoami", "In the notebook", "gold.people"),
    ("telemetry", "Live telemetry", "stream.github · daily"),
    ("stack", "The stack", "silver.stack"),
    ("work", "Selected work", "gold.projects"),
    ("stage", "On stage", "gold.talks"),
    ("notes", "Field notes", "feed.geekindata · daily"),
    ("lineage", "Lineage", "lineage.career"),
    ("credentials", "Credentials", "silver.certifications"),
]


def load_content() -> dict:
    content = tomllib.loads((HERE / "content.toml").read_text())
    content["sections"] = SECTIONS
    return content


def assets(content: dict, s: dict):
    """Yield (file stem, render(theme) -> svg)."""
    yield "hero", lambda t: hero.render(t, content, s)
    for link in content["links"]:
        yield f"link-{nav.slug(link['label'])}", lambda t, link=link: nav.render(t, link)
    for i, (key, title, table) in enumerate(SECTIONS, 1):
        yield f"h-{key}", lambda t, i=i, title=title, table=table: header.render(t, i, title, table)
    yield "whoami", lambda t: notebook.render(t, content)
    yield "telemetry", lambda t: telemetry.render(t, s)
    yield "stack", lambda t: stack.render(t, content)
    yield "work", lambda t: work.render(t, content)
    yield "stage", lambda t: stage.render(t, content)
    yield "lineage", lambda t: lineage.render(t, content)
    yield "credentials", lambda t: credentials.render(t, content)
    yield "footer", lambda t: footer.render(t, content, s)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true", help="use data/live.json without calling any API")
    args = ap.parse_args(argv)

    logging.getLogger("fontTools").setLevel(logging.ERROR)
    content = load_content()
    p = content["profile"]
    data = live.refresh(p["login"], p["feed"], p["notes_limit"], offline=args.offline)
    s = live.derive(data)

    ASSETS.mkdir(exist_ok=True)
    written = set()
    for stem, render in assets(content, s):
        for t in THEMES:
            path = ASSETS / f"{stem}-{t.name}.svg"
            path.write_text(render(t))
            written.add(path.name)
    stale = [f for f in ASSETS.glob("*.svg") if f.name not in written]
    for f in stale:
        f.unlink()

    readme.update(ROOT / "README.md", content, s)
    total_kb = sum((ASSETS / n).stat().st_size for n in written) / 1024
    print(f"wrote {len(written)} SVGs ({total_kb:.0f} KB) · {s['total']:,} contributions · "
          f"{len(s['notes'])} field notes · as of {s['as_of']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
