# Profile generator

Builds every image on the [profile README](../README.md) from scratch: no third-party
stats services. All 48 SVGs (dark and light) are rendered by Python with embedded,
subsetted fonts, so they work under GitHub's strict image CSP.

```sh
pip install -r generator/requirements.txt
GH_TOKEN=$(gh auth token) python -m generator   # fetch live data, then build
python -m generator --offline                   # rebuild from data/live.json only
python -m unittest discover -s generator/tests -t .
```

| Path | What it is |
| :--- | :--- |
| `content.toml` | Hand-written content: links, projects, talks, career, certifications, stack |
| `live.py` | GitHub GraphQL (contribution calendar, languages) and blog RSS, snapshotted to `data/live.json` |
| `sections/` | One renderer per SVG: hero aurora, notebook, telemetry, periodic table, work, stage, lineage, credentials, footer |
| `readme.py` | Writes `README.md` with `<picture>` dark/light pairs |
| `fonts/` | Geist, Geist Mono and Instrument Serif (SIL Open Font License) |

`.github/workflows/profile.yml` runs the tests and the build every day and commits any
changes. Add an optional `PROFILE_TOKEN` secret (a fine-grained PAT with read-only access
to your repositories) to keep private repositories in the language mix. Without it, the
last full snapshot is reused.

Edit `content.toml`, not `README.md` or `assets/`: both are overwritten on every build.
