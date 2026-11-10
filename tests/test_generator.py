from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

from generator.data import (
    _fetch_github,
    clean_text,
    compact_languages,
    contribution_series,
    fetch_live_data,
    streaks,
)
from generator.content import CONTENT
from generator.__main__ import refresh_snapshot
from generator.readme import ASSET_BASE, SECTIONS, build_readme
from generator.sections import hero, render_sections

ROOT = Path(__file__).resolve().parent.parent


class GeneratorTests(unittest.TestCase):
    def test_rendered_svgs_are_well_formed_and_have_no_external_assets(self):
        rendered = render_sections({})
        self.assertEqual(len(rendered), 16)
        for name, svg in rendered.items():
            with self.subTest(asset=name):
                root = ET.fromstring(svg)
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                self.assertNotIn("<image", svg)
                self.assertNotRegex(svg, r"url\((?:https?:)?//")
                self.assertNotRegex(svg, r"<image[^>]+(?:href|xlink:href)=['\"]https?://")
                self.assertIn("data:font/woff2;base64,", svg)

    def test_font_subsetting_is_deterministic(self):
        self.assertEqual(hero.render({}, "dark"), hero.render({}, "dark"))

    def test_readme_references_each_theme_asset(self):
        readme = build_readme({"feed": []})
        for name, _ in SECTIONS:
            for theme in ("dark", "light"):
                self.assertIn(f"{ASSET_BASE}/{name}-{theme}.svg", readme)
        self.assertEqual(readme.count("<picture>"), len(SECTIONS))
        for retired_service in (
            "github-readme-stats", "streak-stats", "readme-typing-svg",
            "activity-graph", "komarev.com",
        ):
            self.assertNotIn(retired_service, readme)

    def test_profile_content_keeps_career_dates_and_all_certifications(self):
        periods = {role["period"] for role in CONTENT["career"]}
        self.assertIn("NOV 2024 → NOW", periods)
        self.assertIn("AUG 2023 → NOV 2024", periods)
        self.assertEqual(len(CONTENT["certification"]), 9)

    def test_feed_markdown_escapes_urls_and_titles(self):
        readme = build_readme({"feed": [{
            "title": "[Update] <unsafe>",
            "url": "https://geekindata.com/posts/a)[fake](https://evil.example)",
        }]})
        self.assertIn(r"\[Update\] &lt;unsafe&gt;", readme)
        self.assertIn("https://geekindata.com/posts/a%29%5Bfake%5D%28https://evil.example%29", readme)
        self.assertNotIn("[fake]", readme)

    def test_generated_content_has_no_em_dashes(self):
        readme = build_readme({"feed": [{"title": "A — B", "url": "https://example.com/post"}]})
        self.assertNotIn("—", readme)
        self.assertNotIn("–", readme)
        self.assertNotIn("—", "\n".join(render_sections({}).values()))

    def test_feed_text_is_normalized_and_markup_removed(self):
        self.assertEqual(clean_text("<b>Lakehouse</b> — field notes"), "Lakehouse - field notes")

    def test_contribution_series_covers_exactly_365_days(self):
        series = contribution_series({"contributions": [
            {"date": "2025-01-01", "contributionCount": 4},
        ]}, today=date(2025, 12, 31))
        self.assertEqual(len(series), 365)
        self.assertEqual(series[0]["date"], "2025-01-01")
        self.assertEqual(series[0]["count"], 4)
        self.assertEqual(series[-1]["date"], "2025-12-31")

    def test_contribution_series_stays_on_snapshot_window_when_refresh_is_stale(self):
        series = contribution_series({
            "window_end": "2025-12-31",
            "contributions": [{"date": "2025-01-01", "contributionCount": 4}],
        })
        self.assertEqual(series[0]["date"], "2025-01-01")
        self.assertEqual(series[-1]["date"], "2025-12-31")
        self.assertEqual(series[0]["count"], 4)

    def test_streaks_count_current_and_longest_runs(self):
        self.assertEqual(streaks([
            {"count": 1}, {"count": 2}, {"count": 0}, {"count": 3},
        ]), (1, 2))
        self.assertEqual(streaks([]), (0, 0))

    def test_language_breakdown_groups_long_tail(self):
        languages = compact_languages([
            {"name": name, "bytes": size}
            for name, size in (("Python", 80), ("SQL", 10), ("Scala", 5), ("Go", 5))
        ], limit=2)
        self.assertEqual([item["name"] for item in languages], ["Python", "SQL", "Other"])
        self.assertAlmostEqual(sum(item["percent"] for item in languages), 100)

    def test_refresh_failure_does_not_replace_full_scope_language_snapshot(self):
        previous = {
            "language_scope": "all",
            "languages": [{"name": "Python", "bytes": 40}],
            "language_repo_count": 8,
        }
        with mock.patch("generator.data._fetch_github", return_value={
            "contributions": [], "total_contributions": 0, "commits": 0, "pull_requests": 0,
            "languages": [], "language_repo_count": 3, "language_scope": "public",
        }), mock.patch("generator.data._fetch_feed", side_effect=RuntimeError("feed is unavailable")):
            with self.assertRaises(RuntimeError):
                fetch_live_data("token", previous)
        self.assertEqual(previous["languages"], [{"name": "Python", "bytes": 40}])

    def test_cli_retains_previous_snapshot_when_refresh_fails(self):
        previous = {"total_contributions": 7}
        with mock.patch("generator.__main__.fetch_live_data", side_effect=RuntimeError("API error")):
            snapshot, refreshed = refresh_snapshot("token", previous)
        self.assertIs(snapshot, previous)
        self.assertFalse(refreshed)

    def test_live_refresh_reuses_full_scope_languages_without_private_token(self):
        previous = {
            "language_scope": "all",
            "languages": [{"name": "Python", "bytes": 40}],
            "language_repo_count": 8,
        }
        with mock.patch("generator.data._fetch_github", return_value={
            "contributions": [], "total_contributions": 0, "commits": 0, "pull_requests": 0,
            "languages": [], "language_repo_count": 3, "language_scope": "public",
        }), mock.patch("generator.data._fetch_feed", return_value=[]):
            refreshed = fetch_live_data("token", previous)
        self.assertEqual(refreshed["languages"], previous["languages"])
        self.assertEqual(refreshed["language_scope"], "all")
        self.assertEqual(refreshed["language_repo_count"], 8)

    def test_graphql_query_uses_public_filter_only_without_private_token(self):
        response_body = {
            "data": {"user": {
                "contributionsCollection": {
                    "totalCommitContributions": 1,
                    "totalPullRequestContributions": 2,
                    "contributionCalendar": {"totalContributions": 3, "weeks": []},
                },
                "repositories": {"totalCount": 0, "nodes": [],
                                 "pageInfo": {"hasNextPage": False, "endCursor": None}},
            }}
        }
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(response_body).encode()
        for include_private, expected_filter in ((False, "privacy: PUBLIC"), (True, None)):
            with self.subTest(include_private=include_private), mock.patch(
                "generator.data.urllib.request.urlopen", return_value=response
            ) as urlopen:
                _fetch_github("test-token", date(2025, 1, 1), date(2025, 12, 31), include_private)
                request = urlopen.call_args.args[0]
                query = json.loads(request.data)["query"]
                if expected_filter:
                    self.assertIn(expected_filter, query)
                else:
                    self.assertNotIn("privacy:", query)
                self.assertEqual(request.get_header("Authorization"), "Bearer " + "test-token")

    def test_graphql_language_query_paginates_all_repositories(self):
        first_page = {
            "data": {"user": {
                "contributionsCollection": {
                    "totalCommitContributions": 1,
                    "totalPullRequestContributions": 2,
                    "contributionCalendar": {"totalContributions": 3, "weeks": []},
                },
                "repositories": {
                    "totalCount": 101,
                    "nodes": [{"languages": {"edges": [{"size": 20, "node": {"name": "Python"}}]}}],
                    "pageInfo": {"hasNextPage": True, "endCursor": "next-page"},
                },
            }}
        }
        second_page = {
            "data": {"user": {
                "repositories": {
                    "totalCount": 101,
                    "nodes": [{"languages": {"edges": [{"size": 10, "node": {"name": "SQL"}}]}}],
                    "pageInfo": {"hasNextPage": False, "endCursor": "next-page"},
                },
            }}
        }

        def response_for(payload):
            response = mock.MagicMock()
            response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
            return response

        with mock.patch(
            "generator.data.urllib.request.urlopen",
            side_effect=(response_for(first_page), response_for(second_page)),
        ) as urlopen:
            result = _fetch_github("test-token", date(2025, 1, 1), date(2025, 12, 31), False)

        self.assertEqual(urlopen.call_count, 2)
        first_query = json.loads(urlopen.call_args_list[0].args[0].data)
        second_query = json.loads(urlopen.call_args_list[1].args[0].data)
        self.assertIn("contributionsCollection", first_query["query"])
        self.assertNotIn("contributionsCollection", second_query["query"])
        self.assertEqual(second_query["variables"]["cursor"], "next-page")
        self.assertEqual(result["language_repo_count"], 101)
        self.assertEqual({item["name"] for item in result["languages"]}, {"Python", "SQL"})


if __name__ == "__main__":
    unittest.main()
