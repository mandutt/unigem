"""Unit tests for frozen C5 Phase 6 label/gate primitives."""

from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_pm_labels import (  # noqa: E402
    and_n, or_n, not3, l_signal_consensus, l_predicate, m_evaluable,
    m_valid, control_status, validity_status, signal_status, signal_tail,
)


class TriStateTests(unittest.TestCase):
    def test_and_or_not(self) -> None:
        self.assertFalse(and_n([True, False, None]))
        self.assertIsNone(and_n([True, None]))
        self.assertTrue(and_n([True, True]))
        self.assertTrue(or_n([False, True, None]))
        self.assertIsNone(or_n([False, None]))
        self.assertFalse(or_n([False, False]))
        self.assertFalse(not3(True))
        self.assertIsNone(not3(None))

    def test_l_consensus_table(self) -> None:
        self.assertEqual(l_signal_consensus(True, True)["l_signal"], True)
        self.assertEqual(l_signal_consensus(False, False)["l_signal"], False)
        self.assertIsNone(l_signal_consensus(True, False)["l_signal"])
        self.assertTrue(l_signal_consensus(True, False)["copy_only"])
        self.assertTrue(l_signal_consensus(False, True)["full_only"])
        self.assertIsNone(l_signal_consensus(True, None)["copy_only"])

    def test_l_predicate_copy_threshold(self) -> None:
        docs = [0.1] * 15
        seeds = [0.1, 0.1, 0.1]
        got = l_predicate(docs, seeds, [0.01] * 15, copy=True)
        self.assertTrue(got["value"])
        got2 = l_predicate([0.01] * 15, seeds, [0.01] * 15, copy=True)
        self.assertFalse(got2["value"])
        got3 = l_predicate([0.1] * 15, seeds, [-0.01] * 15, copy=True)
        self.assertFalse(got3["value"])

    def test_tail(self) -> None:
        got = signal_tail({"a": 10.0, "b": 9.0, "c": 8.0, "d": 1.0})
        self.assertTrue(got["tail_driven"])
        self.assertEqual(got["top3_ids"], ["a", "b", "c"])


class GateTests(unittest.TestCase):
    def test_control_status(self) -> None:
        self.assertEqual(control_status(True, True, True, True, True), "M_CONTROL_PASS")
        self.assertEqual(control_status(True, True, True, False, True), "M_CONTROL_INVALID")
        self.assertEqual(control_status(False, True, True, True, True), "M_NOT_EVALUABLE")
        self.assertEqual(control_status(True, False, True, True, True), "M_NOT_EVALUABLE")
        self.assertEqual(control_status(True, None, True, True, True), "NOT_ASSESSABLE")

    def test_validity(self) -> None:
        self.assertEqual(validity_status(True, True, True, True, True, True, False), "VALID")
        self.assertEqual(validity_status(True, True, True, True, False, True, False), "P_STEP100_NOT_VALID")
        self.assertEqual(validity_status(True, True, True, False, True, True, False), "PA_STEP100_NOT_VALID")
        self.assertEqual(validity_status(True, False, True, True, True, True, False), "ASSAY_INVALID")
        self.assertEqual(validity_status(True, True, None, True, True, True, False), "NOT_ASSESSABLE")

    def test_signal_dispatch(self) -> None:
        self.assertEqual(signal_status(15, True, False, False, "VALID", "M_CONTROL_PASS"), "EXPLORATORY_L_SIGNAL")
        self.assertEqual(signal_status(15, False, False, False, "VALID", "M_CONTROL_PASS"), "MEAN_CONTRAST_ONLY")
        self.assertEqual(signal_status(14, True, False, False, "VALID", "M_CONTROL_PASS"), "INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL")
        self.assertEqual(signal_status(15, None, False, False, "VALID", "M_CONTROL_PASS"), "NOT_ASSESSABLE")

    def test_m_gates(self) -> None:
        self.assertTrue(m_evaluable(True, True, True, True, True))
        self.assertFalse(m_evaluable(True, False, True, True, True))
        self.assertTrue(m_valid(True, True, True, True))
        self.assertFalse(m_valid(True, True, True, False))


if __name__ == "__main__":
    unittest.main()
