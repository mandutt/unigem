"""Unit tests for C5 F0.1 optimization diagnostic."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner import c5_pm_f0_1_opt as f01  # noqa: E402


class TestF01(unittest.TestCase):
    def test_condition_matrix(self):
        self.assertEqual(len(f01.CONDITIONS), 5)
        self.assertEqual(len(f01.STAGE_CONDITIONS["a"]) * len(f01.SEEDS), 9)
        self.assertEqual(len(f01.STAGE_CONDITIONS["b"]) * len(f01.SEEDS), 6)
        self.assertEqual({c["id"] for c in f01.CONDITIONS}, {"C1", "C2", "C3", "C4", "C5"})
        self.assertEqual(f01.FIT_RATIO, 0.35)
        self.assertEqual(f01.CAP_SECONDS, 2700)
        self.assertEqual(f01.STAGE_CAP, {"a": 2700, "b": 3600})

    def test_step_seed_golden(self):
        self.assertEqual(f01.step_seed(20261108, 0), 0x9F02514D)
        self.assertEqual(f01.step_seed(20261108, 1), 0x3D5BDB86)
        self.assertEqual(f01.step_seed(20261108, 2), 0xDB9345DF)

    def test_no_signal_contract(self):
        # F0.1 is a training-fit diagnostic, never a signal/PASS experiment.
        self.assertFalse(hasattr(f01, "eval_signal"))
        self.assertFalse(hasattr(f01, "compute_labels"))

    def test_freeze_manifest(self):
        freeze = f01.read_json(f01.FREEZE)
        self.assertEqual(freeze["status"], "owner_approved")
        self.assertEqual(freeze["stage"], "a")
        self.assertEqual(freeze["plan_sha256"], f01.sha256_bytes(f01.PLAN.read_bytes()))


if __name__ == "__main__":
    unittest.main()
