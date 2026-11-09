"""Unit tests for the frozen C5 Phase 6 D0 mechanics."""

from __future__ import annotations

import ast
import math
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_pm_phase6 import (  # noqa: E402
    ARMS,
    D0_SEED,
    K_M_L,
    K_M_NATIVE,
    arm_spec,
    assert_allowed_ids,
    d0_flags,
)
from runner.c5_pm_stats import (  # noqa: E402
    bootstrap_paired_v2,
    documents_positive,
    registered_seeds_positive,
    tail_metrics,
    t_proj_seconds,
)


class StatsTests(unittest.TestCase):
    def test_bootstrap_matches_manual_pcg64(self) -> None:
        values = [0.4, -0.2, 0.1, 0.7, 0.0]
        got = bootstrap_paired_v2(values, n_boot=200, seed=20261109)
        arr = np.asarray(values, dtype=np.float64)
        rng = np.random.default_rng(20261109)
        means = np.asarray(
            [arr[rng.integers(0, arr.size, size=arr.size)].mean() for _ in range(200)]
        )
        lo, hi = np.percentile(means, [2.5, 97.5], method="linear")
        self.assertAlmostEqual(got["mean"], float(arr.mean()))
        self.assertAlmostEqual(got["ci_lower"], float(lo))
        self.assertAlmostEqual(got["ci_upper"], float(hi))
        self.assertEqual(got["n"], 5)
        self.assertEqual(got["n_boot"], 200)
        self.assertEqual(got["rng"], "PCG64")

    def test_bootstrap_rejects_nonfinite(self) -> None:
        with self.assertRaises(ValueError):
            bootstrap_paired_v2([1.0, math.nan])

    def test_positive_helpers(self) -> None:
        self.assertEqual(documents_positive([0.1, -0.1, 0.0, 2.0]), 2)
        self.assertEqual(registered_seeds_positive([0.1, -1.0, 0.0]), 1)

    def test_tail_false_when_flat(self) -> None:
        got = tail_metrics({str(i): 1.0 for i in range(7)})
        self.assertFalse(got["tail_driven"])
        self.assertAlmostEqual(got["top3_abs_share"], 3 / 7)

    def test_tail_true_when_concentrated(self) -> None:
        got = tail_metrics({"a": 10.0, "b": 9.0, "c": 8.0, "d": 1.0})
        self.assertTrue(got["tail_driven"])
        self.assertEqual(got["top3_ids"], ["a", "b", "c"])
        self.assertAlmostEqual(got["leave_top3_mean"], 1.0)

    def test_tail_na_for_short_cohort(self) -> None:
        got = tail_metrics({"a": 3.0, "b": 2.0, "c": 1.0})
        self.assertIsNone(got["leave_top3_mean"])
        self.assertIsNone(got["tail_driven"])

    def test_t_proj_arithmetic(self) -> None:
        terms = {
            "t_train_arm": 1,
            "t_step0_eval_20x5_arm": 1,
            "t_step100_eval_20x5_arm": 1,
            "t_M_build_arm": 1,
            "t_initial_M_ce_arm": 1,
            "t_generate_20x256_arm": 1,
            "t_primary_replay_arm": 1,
            "t_replay_15x5x2x2x2_arm": 1,
            "t_overhead_arm": 1,
        }
        got = t_proj_seconds({arm: dict(terms) for arm in ARMS})
        self.assertAlmostEqual(got, 108.0)

    def test_t_proj_rejects_missing_arm(self) -> None:
        with self.assertRaises(ValueError):
            t_proj_seconds({"F": {}})


class Phase6ContractTests(unittest.TestCase):
    def test_arm_table(self) -> None:
        self.assertEqual(arm_spec("F")["m_k"], K_M_L)
        self.assertFalse(arm_spec("F")["lora"])
        self.assertTrue(arm_spec("F")["adapter"])
        self.assertTrue(arm_spec("L")["lora"])
        self.assertFalse(arm_spec("P")["adapter"])
        self.assertTrue(arm_spec("P")["lora"])
        self.assertEqual(arm_spec("P")["m_k"], K_M_NATIVE)
        self.assertTrue(arm_spec("PA")["adapter"])
        self.assertTrue(arm_spec("PA")["lora"])

    def test_allowlist_rejects_test_id(self) -> None:
        assert_allowed_ids(["a", "b"], {"a", "b"})
        with self.assertRaises(RuntimeError):
            assert_allowed_ids(["a", "test-only"], {"a", "b"})

    def test_d0_flags(self) -> None:
        flags = d0_flags()
        self.assertEqual(flags["mode"], "d0_zero_update")
        self.assertEqual(flags["updates"], 0)
        self.assertEqual(flags["seed"], D0_SEED)
        self.assertFalse(flags["registered_seed_used"])
        self.assertFalse(flags["labels_computed"])
        self.assertTrue(flags["not_a_result"])
        self.assertFalse(flags["test_split_used"])
        self.assertFalse(flags["p1_used"])

    def test_no_forbidden_imports_or_calls(self) -> None:
        path = ROOT / "runner/c5_pm_phase6.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        forbidden = {"train_arm", "evaluate_arm", "bootstrap_paired"}
        imported: set[str] = set()
        calls: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported.update(alias.name for alias in node.names)
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    calls.add(func.id)
                elif isinstance(func, ast.Attribute):
                    calls.add(func.attr)
        self.assertFalse(imported & forbidden, imported & forbidden)
        self.assertFalse(calls & forbidden, calls & forbidden)

    def test_no_legacy_bootstrap_in_stats(self) -> None:
        path = ROOT / "runner/c5_pm_stats.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertNotIn("bootstrap_paired", calls)
        self.assertIn("bootstrap_paired_v2", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
