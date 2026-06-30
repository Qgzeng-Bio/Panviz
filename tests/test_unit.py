"""Unit tests for the Panviz Python package (standard-library ``unittest``).

Run with:  python3 -m unittest discover -s tests -p 'test_*.py'
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from panviz.config import DEFAULTS, REPO_ROOT, detect_browser, resolve_config
from panviz.discover import LocusInput, discover_loci
from panviz.gfa import gfa_to_payload, parse_gfa_tags, parse_path_token
from panviz.validate import has_errors, png_dimensions, validate_locus_input

TOY_ROOT = REPO_ROOT / "examples" / "toy_data"
BASELINE_CONFIG = REPO_ROOT / "config" / "mainfig_baseline.json"


def _toy() -> LocusInput:
    return next(iter(discover_loci(TOY_ROOT, ["toy_locus"])))


class ConfigTests(unittest.TestCase):
    def test_override_beats_default(self):
        self.assertEqual(resolve_config(None, {"x_compression": 0.5}).x_compression, 0.5)

    def test_unset_override_falls_back_to_default(self):
        cfg = resolve_config(None, {"x_compression": None})
        self.assertEqual(cfg.x_compression, float(DEFAULTS["x_compression"]))

    def test_config_relative_path_anchored_at_repo_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "c.json"
            cfg_path.write_text(json.dumps({"out_root": "results/unit"}))
            cfg = resolve_config(cfg_path, {})
            self.assertEqual(cfg.out_root, REPO_ROOT / "results" / "unit")

    def test_unknown_config_key_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "c.json"
            cfg_path.write_text(json.dumps({"nope": 1}))
            with self.assertRaises(ValueError):
                resolve_config(cfg_path, {})

    def test_panviz_browser_is_authoritative(self):
        os.environ["PANVIZ_BROWSER"] = "/tmp/panviz_no_such_chrome"
        try:
            self.assertEqual(detect_browser(), "/tmp/panviz_no_such_chrome")
        finally:
            del os.environ["PANVIZ_BROWSER"]


class GfaTests(unittest.TestCase):
    def test_parse_path_token_orientation(self):
        self.assertEqual(parse_path_token("bb0+"), "bb0")
        self.assertEqual(parse_path_token("bb0-"), "-bb0")
        with self.assertRaises(ValueError):
            parse_path_token("bb0")

    def test_parse_gfa_tags_types(self):
        tags = parse_gfa_tags(["LN:i:100", "TYPE:Z:DEL"])
        self.assertEqual(tags["LN"], 100)
        self.assertEqual(tags["TYPE"], "DEL")

    def test_toy_payload_counts(self):
        cfg = resolve_config(BASELINE_CONFIG, {})
        payload, counts, _ = gfa_to_payload(_toy(), cfg)
        self.assertEqual(counts, {"nodes": 15, "tracks": 6})
        self.assertEqual(payload["mainFigure"]["xCompression"], 0.32)
        self.assertEqual(payload["tracks"][0]["name"], "Ref")


class DiscoverTests(unittest.TestCase):
    def test_finds_toy_locus(self):
        self.assertEqual([item.locus for item in discover_loci(TOY_ROOT, None)], ["toy_locus"])

    def test_missing_locus_raises(self):
        with self.assertRaises(FileNotFoundError):
            discover_loci(TOY_ROOT, ["does_not_exist"])


class ValidateTests(unittest.TestCase):
    def test_toy_has_no_errors(self):
        self.assertFalse(has_errors(validate_locus_input(_toy())))

    def test_dangling_segment_reference_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "x_pathcollapsed_SV1kb.gfa").write_text("S\tA\t*\tLN:i:10\nP\tRef\tA+,B+\t*\n")
            (d / "x_pathcollapsed_SV1kb.path_groups.tsv").write_text("collapsed_path\nRef\n")
            (d / "region.txt").write_text(
                "reference_coordinate=c:1-2\nrecommended_SequenceTubeMap_region=c:1-2\n"
            )
            item = LocusInput(
                "x",
                d / "x_pathcollapsed_SV1kb.gfa",
                d / "x_pathcollapsed_SV1kb.path_groups.tsv",
                d / "region.txt",
            )
            self.assertTrue(has_errors(validate_locus_input(item)))

    def test_reversed_region_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            region = Path(tmp) / "region.txt"
            region.write_text(
                "reference_coordinate=c:200-100\nrecommended_SequenceTubeMap_region=c:200-100\n"
            )
            item = LocusInput("x", Path(tmp) / "missing.gfa", Path(tmp) / "missing.tsv", region)
            self.assertTrue(has_errors(validate_locus_input(item)))

    def _locus_with_gfa(self, tmp: str, gfa_text: str) -> LocusInput:
        d = Path(tmp)
        (d / "x_pathcollapsed_SV1kb.gfa").write_text(gfa_text)
        (d / "x_pathcollapsed_SV1kb.path_groups.tsv").write_text("collapsed_path\nRef\n")
        (d / "region.txt").write_text(
            "reference_coordinate=c:1-2\nrecommended_SequenceTubeMap_region=c:1-2\n"
        )
        return LocusInput(
            "x",
            d / "x_pathcollapsed_SV1kb.gfa",
            d / "x_pathcollapsed_SV1kb.path_groups.tsv",
            d / "region.txt",
        )

    def test_duplicate_segment_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            gfa = "S\tA\t*\tLN:i:5\nS\tA\t*\tLN:i:5\nP\tRef\tA+\t*\n"
            self.assertTrue(has_errors(validate_locus_input(self._locus_with_gfa(tmp, gfa))))

    def test_non_positive_ln_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            gfa = "S\tA\t*\tLN:i:0\nP\tRef\tA+\t*\n"
            self.assertTrue(has_errors(validate_locus_input(self._locus_with_gfa(tmp, gfa))))

    def test_unoriented_token_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            gfa = "S\tA\t*\tLN:i:5\nP\tRef\tA\t*\n"
            self.assertTrue(has_errors(validate_locus_input(self._locus_with_gfa(tmp, gfa))))


class PngTests(unittest.TestCase):
    def test_toy_preview_png_dimensions(self):
        wh = png_dimensions(REPO_ROOT / "examples" / "toy_locus.png")
        self.assertIsNotNone(wh)
        self.assertEqual(wh[0], 3600)  # panel_width 1800 * device_scale_factor 2

    def test_non_png_returns_none(self):
        self.assertIsNone(png_dimensions(REPO_ROOT / "README.md"))


if __name__ == "__main__":
    unittest.main()
