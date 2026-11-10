"""Unit tests for C5 F0.3 E00/E10 reference decomposition."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner import c5_pm_f0_3_reference as f03  # noqa: E402


class TestF03(unittest.TestCase):
    def test_scope(self):
        self.assertEqual(f03.CELLS, ("E00", "E10"))
        self.assertEqual(f03.UPDATES, {"E00": 0, "E10": 400})
        self.assertEqual(f03.ADAPTER_LR, 1e-3)
        self.assertEqual(f03.FIT_RATIO, 0.35)
        self.assertEqual(f03.CAP_SECONDS, 3600)
        self.assertEqual(len(f03.CELLS) * len(f03.SEEDS), 6)

    def test_step_seed(self):
        self.assertEqual(f03.step_seed(20261108, 0), 0x9F02514D)

    def test_descriptive_contract(self):
        self.assertFalse(hasattr(f03, "compute_labels"))
        self.assertFalse(hasattr(f03, "PASS_POSITIVE"))

    def test_freeze_manifest(self):
        freeze = f03.read_json(f03.FREEZE)
        self.assertEqual(freeze["status"], "owner_approved")
        self.assertEqual(freeze["plan_sha256"], f03.sha256_bytes(f03.PLAN.read_bytes()))


if __name__ == "__main__":
    unittest.main()
