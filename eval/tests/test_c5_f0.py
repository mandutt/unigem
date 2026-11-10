"""Unit tests for C5 F0 D0 mechanics."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner import c5_pm_f0 as f0  # noqa: E402


class TestF0D0(unittest.TestCase):
    def test_cell_specs(self):
        self.assertEqual(f0.cell_spec("E00")["trainable"], "none")
        self.assertEqual(f0.cell_spec("E10")["trainable"], "adapter")
        self.assertEqual(f0.cell_spec("E01")["trainable"], "lora")
        self.assertEqual(f0.cell_spec("E11")["trainable"], "adapter+lora")
        self.assertEqual(f0.cell_spec("E00")["updates_d1"], 0)
        for cell in ("E10", "E01", "E11"):
            self.assertEqual(f0.cell_spec(cell)["updates_d1"], 1)

    def test_cell_names_frozen(self):
        self.assertEqual(f0.CELLS, ("E00", "E10", "E01", "E11"))
        self.assertEqual(f0.D0_SEED, 20261111)
        self.assertEqual(f0.K_M, 753)
        self.assertEqual(f0.EXPECTED_LORA_MODULES, 64)

    def test_freeze_hashes_match(self):
        freeze = f0.check_freeze()
        self.assertEqual(freeze["status"], "owner_approved_unreviewed")
        self.assertEqual(freeze["review_status"], "3AI_not_run_owner_accepts_risk")

    def test_freeze_rejects_plan_mutation(self):
        old = (f0.PLAN, f0.ANNEX, f0.FREEZE)
        try:
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td)
                plan = tmp / "plan.md"
                annex = tmp / "annex.md"
                freeze = tmp / "freeze.json"
                plan.write_text("changed", encoding="utf-8")
                annex.write_text("annex", encoding="utf-8")
                freeze.write_text(json.dumps({
                    "status": "owner_approved_unreviewed",
                    "plan_sha256": "0" * 64,
                    "annex_sha256": f0.sha256_bytes(annex.read_bytes()),
                }), encoding="utf-8")
                f0.PLAN, f0.ANNEX, f0.FREEZE = plan, annex, freeze
                with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
                    f0.check_freeze()
        finally:
            f0.PLAN, f0.ANNEX, f0.FREEZE = old

    def test_no_d1_mode(self):
        old = sys.argv
        try:
            sys.argv = ["c5_pm_f0", "--mode", "d1"]
            with self.assertRaises(SystemExit):
                f0.main()
        finally:
            sys.argv = old


if __name__ == "__main__":
    unittest.main()
