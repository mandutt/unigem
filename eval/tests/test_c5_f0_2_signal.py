"""Unit tests for C5 F0.2 matched-optimization signal re-test."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner import c5_pm_f0_2_signal as f02  # noqa: E402


class TestF02(unittest.TestCase):
    def test_scope(self):
        self.assertEqual(f02.CELLS, ("E01", "E11"))
        self.assertEqual(f02.UPDATES, 400)
        self.assertEqual(f02.LORA_LR, 3e-4)
        self.assertEqual(f02.ADAPTER_LR, 1e-3)
        self.assertEqual(f02.FIT_RATIO, 0.35)
        self.assertEqual(f02.CAP_SECONDS, 3600)
        self.assertEqual(len(f02.CELLS) * len(f02.SEEDS), 6)

    def test_step_seed_golden(self):
        self.assertEqual(f02.step_seed(20261108, 0), 0x9F02514D)
        self.assertEqual(f02.step_seed(20261108, 1), 0x3D5BDB86)

    def test_no_m_phase7_generation(self):
        self.assertFalse(hasattr(f02, "m_records_for"))
        self.assertFalse(hasattr(f02, "phase7_records_for"))
        self.assertFalse(hasattr(f02, "generate_f0"))

    def test_freeze_manifest(self):
        freeze = f02.read_json(f02.FREEZE)
        self.assertEqual(freeze["status"], "owner_approved")
        self.assertEqual(freeze["plan_sha256"], f02.sha256_bytes(f02.PLAN.read_bytes()))


if __name__ == "__main__":
    unittest.main()
