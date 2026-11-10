"""Smoke tests: `python -m unittest discover -s generator/tests -t .`"""

from __future__ import annotations

import re
import unittest
from datetime import date, timedelta
from xml.etree import ElementTree

from generator import live, readme
from generator.__main__ import assets, load_content
from generator.sections import stack
from generator.theme import THEMES


def fake_data(counts: list[int]) -> dict:
    start = date(2026, 1, 1)
    return {
        "days": [[(start + timedelta(i)).isoformat(), c] for i, c in enumerate(counts)],
        "fetched": (start + timedelta(len(counts) - 1)).isoformat(),
        "languages": [["Python", 300, "#3572A5"], ["TypeScript", 100, "#3178c6"]],
        "languages_include_private": False,
        "commits": 10, "pull_requests": 4, "repos": 3,
        "notes": [{"title": "A note \u2014 with a dash", "link": "https://example.com/a", "date": "2026-01-02",
                   "summary": "Summary " * 30}],
        "notes_total": 1,
    }


class DeriveTest(unittest.TestCase):
    def test_streaks_ignore_an_unfinished_today(self):
        s = live.derive(fake_data([0, 1, 1, 1, 0, 2, 3, 0]))
        self.assertEqual(s["longest_streak"], 3)
        self.assertEqual(s["current_streak"], 2)
        self.assertEqual(s["active"], 5)
        self.assertEqual(s["total"], 8)

    def test_language_shares_sum_to_one(self):
        s = live.derive(fake_data([1] * 10))
        self.assertAlmostEqual(sum(p for _, p, _ in s["languages"]), 1.0)


class LayoutTest(unittest.TestCase):
    def test_every_stack_element_gets_a_unique_slot(self):
        st = load_content()["stack"]
        placed = stack.layout(st["categories"], st["elements"])
        self.assertEqual(len(placed), len(st["elements"]))
        self.assertEqual(len({(r, c) for r, c, _ in placed}), len(placed))


class RefreshTest(unittest.TestCase):
    def test_public_only_token_keeps_private_languages_and_failures_keep_snapshot(self):
        import json
        import os
        import tempfile
        from pathlib import Path
        from unittest import mock

        snap = fake_data([1, 2, 3])
        snap["languages"] = [["TypeScript", 900, "#3178c6"]]
        snap["languages_include_private"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "live.json"
            path.write_text(json.dumps(snap))
            public = {**fake_data([4, 5, 6]), "languages": [["Python", 10, "#3572A5"]],
                      "languages_include_private": False}
            with mock.patch.object(live, "SNAPSHOT", path), mock.patch.dict(os.environ, {"GH_TOKEN": "x"}), \
                    mock.patch.object(live, "fetch_github", return_value=public), \
                    mock.patch.object(live, "fetch_notes", side_effect=OSError("offline")):
                data = live.refresh("someone", "https://example.com/rss.xml", 5)
            self.assertEqual(data["languages"], [["TypeScript", 900, "#3178c6"]])
            self.assertEqual([c for _, c in data["days"]], [4, 5, 6])
            self.assertEqual(data["notes"], snap["notes"])


class OutputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = load_content()
        cls.stats = live.derive(live.load_snapshot())
        cls.svgs = {f"{stem}-{t.name}": render(t) for stem, render in assets(cls.content, cls.stats) for t in THEMES}
        cls.readme = readme.render(cls.content, cls.stats)

    def test_svgs_are_well_formed_and_self_contained(self):
        for name, svg in self.svgs.items():
            with self.subTest(name):
                ElementTree.fromstring(svg)
                # GitHub serves SVGs with default-src 'none': nothing external may load.
                self.assertNotRegex(svg, r"url\((?!#|data:)")
                self.assertNotIn("<script", svg)

    def test_readme_references_only_generated_assets(self):
        refs = set(re.findall(r"/assets/([\w-]+)\.svg", self.readme))
        self.assertTrue(refs)
        self.assertLessEqual(refs, set(self.svgs))

    def test_no_em_dashes_anywhere(self):
        for name, text in {**self.svgs, "README.md": self.readme}.items():
            with self.subTest(name):
                self.assertNotIn("\u2014", text)

    def test_feed_text_is_normalised(self):
        s = live.derive(fake_data([1, 2]))
        s["notes"] = [{**n, "title": live.no_em_dash(n["title"])} for n in s["notes"]]
        self.assertNotIn("\u2014", readme.notes_md(s))


if __name__ == "__main__":
    unittest.main()
