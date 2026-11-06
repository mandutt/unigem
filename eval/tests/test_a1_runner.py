"""Unit tests for the A1 runner's epoch order and checkpoint helpers."""
from __future__ import annotations

import unittest

from runner.c5_a1_lora import build_order


class A1RunnerContractTests(unittest.TestCase):
    def test_order_is_deterministic_per_seed_and_epoch(self) -> None:
        a = build_order(17, seed=42, epoch=0)
        b = build_order(17, seed=42, epoch=0)
        self.assertEqual(a, b)
        self.assertEqual(sorted(a), list(range(17)))

    def test_order_changes_between_epochs(self) -> None:
        e0 = build_order(17, seed=42, epoch=0)
        e1 = build_order(17, seed=42, epoch=1)
        self.assertNotEqual(e0, e1)
        self.assertEqual(sorted(e1), list(range(17)))


if __name__ == "__main__":
    unittest.main()
