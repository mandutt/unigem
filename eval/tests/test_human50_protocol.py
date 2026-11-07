"""Tests for the D-085 frozen manifest and analysis helpers."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_human50_single_rater_analysis import (  # noqa: E402
    cohen_kappa,
    icc21,
    quadratic_weighted_kappa,
)

MANIFEST = ROOT / "reports/provenance/C5_human50/manifest.json"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"


class TestHuman50Manifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.splits = json.loads(SPLITS.read_text(encoding="utf-8"))

    def test_counts(self) -> None:
        self.assertEqual(self.m["sample_n"], 50)
        self.assertEqual(self.m["targeted_n"], 20)
        self.assertEqual(self.m["random_n"], 30)
        self.assertEqual(self.m["repeat_n"], 10)
        self.assertEqual(self.m["primary_ratings"], 200)
        self.assertEqual(self.m["repeat_ratings"], 40)
        self.assertEqual(self.m["total_ratings"], 240)

    def test_unique_sample_and_no_test(self) -> None:
        ids = [x["id"] for x in self.m["targeted"] + self.m["random"]]
        self.assertEqual(len(ids), 50)
        self.assertEqual(len(set(ids)), 50)
        self.assertFalse(set(ids) & set(self.splits["test"]))

    def test_repeat_unique_and_subset(self) -> None:
        ids = [x["id"] for x in self.m["repeat"]]
        sample = {x["id"] for x in self.m["targeted"] + self.m["random"]}
        self.assertEqual(len(ids), 10)
        self.assertEqual(len(set(ids)), 10)
        self.assertTrue(set(ids) <= sample)
        self.assertEqual(sum(1 for x in self.m["repeat"] if x["stratum"] == "targeted"), 6)
        self.assertEqual(sum(1 for x in self.m["repeat"] if x["stratum"] == "random30"), 4)

    def test_sessions(self) -> None:
        primary = self.m["sessions"]["primary"]
        repeat = self.m["sessions"]["repeat"]
        self.assertEqual(len(primary), 5)
        self.assertTrue(all(len(v) == 10 for v in primary.values()))
        self.assertEqual(len(repeat), 2)
        self.assertTrue(all(len(v) == 5 for v in repeat.values()))
        self.assertEqual(sum(len(v) for v in primary.values()), 50)
        self.assertEqual(sum(len(v) for v in repeat.values()), 10)

    def test_arm_order(self) -> None:
        for x in self.m["targeted"] + self.m["random"]:
            self.assertEqual(sorted(x["arm_order"]), sorted(self.m["arms"]))
            self.assertEqual(len(set(x["arm_order"])), 4)
        for x in self.m["repeat"]:
            self.assertEqual(sorted(x["arm_order"]), sorted(self.m["arms"]))
            self.assertEqual(len(set(x["arm_order"])), 4)

    def test_train_prefix(self) -> None:
        self.assertEqual(self.m["train_prefix_n"], 16)
        self.assertEqual(len(self.m["train_prefix_ids"]), 16)
        self.assertTrue(set(self.m["train_prefix_ids"]) <= set(self.splits["val"]))

    def test_hashes(self) -> None:
        ids = [x["id"] for x in self.m["targeted"] + self.m["random"]]
        self.assertEqual(set(self.m["hashes"]), set(ids))
        self.assertTrue(all(len(v["source_sha256"]) == 64 for v in self.m["hashes"].values()))
        self.assertTrue(all(len(v["target_sha256"]) == 64 for v in self.m["hashes"].values()))

    def test_frozen_flags(self) -> None:
        self.assertEqual(self.m["status"], "FROZEN")
        self.assertTrue(self.m["frozen_before_ratings"])
        self.assertEqual(self.m["rater_count"], 1)
        self.assertEqual(self.m["inter_rater_reliability"], "NOT_AVAILABLE")
        self.assertEqual(self.m["test_163"], "SEALED")


class TestAnalysisHelpers(unittest.TestCase):
    def test_icc_perfect(self) -> None:
        m = np.array([[1, 1], [2, 2], [3, 3], [4, 4]], dtype=float)
        self.assertAlmostEqual(icc21(m), 1.0)

    def test_weighted_kappa_perfect(self) -> None:
        y = [0, 1, 2, 3, 4, 0, 1, 2]
        self.assertAlmostEqual(quadratic_weighted_kappa(y, y), 1.0)

    def test_binary_kappa_perfect(self) -> None:
        y = [0, 1, 0, 1, 0, 1]
        self.assertAlmostEqual(cohen_kappa(y, y), 1.0)


if __name__ == "__main__":
    unittest.main()
