from __future__ import annotations

from pathlib import Path
import tomllib

CONTENT_PATH = Path(__file__).with_name("content.toml")

with CONTENT_PATH.open("rb") as content_file:
    CONTENT = tomllib.load(content_file)

profile = CONTENT["profile"]
