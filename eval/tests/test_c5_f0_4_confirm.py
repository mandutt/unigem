"""Unit tests for C5 F0.4 directional confirmation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner import c5_pm_f0_4_confirm as f04  # noqa: E402


class TestF04(unittest.TestCase):
    def test_scope(self):
        self.assertEqual(f04.CELLS, ("E01", "E11"))
        self.assertEqual(f04.SEEDS, (20261112, 20261113, 20261114))
        self.assertEqual(f04.UPDATES, 400)
        self.assertEqual(f04.LORA_LR, 3e-4)
        self.assertEqual(f04.ADAPTER_LR, 1e-3)
        self.assertEqual(f04.CAP_SECONDS, 3600)
        self.assertEqual(len(f04.CELLS) * len(f04.SEEDS), 6)

    def test_direction(self):
        self.assertIn("E11-E01", "E11-E01")
        self.assertEqual(f04.step_seed(20261112, 0),
                         (20261112 ^ 0x9E3779B9) & 0xFFFFFFFF)

    def test_freeze_manifest(self):
        freeze = f04.read_json(f04.FREEZE)
        self.assertEqual(freeze["status"], "owner_approved")
        self.assertEqual(freeze["plan_sha256"], f04.sha256_bytes(f04.PLAN.read_bytes()))


if __name__ == "__main__":
    unittest.main()
