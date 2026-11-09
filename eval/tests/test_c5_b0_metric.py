"""Regression tests for the C5 B0 mT5 copy metric."""
from __future__ import annotations

import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "data/models/mt5-small"


@unittest.skipUnless(MODEL.exists(), "local mT5-small model is unavailable")
class B0MetricAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from runner.c5_mt5_lora_b0 import load_base, token_losses
        from runner.c5_mt5_layer_probe import make_labels

        cls.tok, cls.model = load_base()
        cls.labels = make_labels(cls.tok, "테스트 요약입니다.", 32)
        cls.memory = torch.zeros(8, 512)
        cls.token_losses = staticmethod(token_losses)

    def test_same_position_ce_matches_builtin_loss(self) -> None:
        with torch.no_grad():
            full, per_token = self.token_losses(self.model, self.memory, self.labels)
        valid = self.labels != -100
        manual = per_token[valid].mean().item()
        self.assertAlmostEqual(full, manual, places=5)

    def test_copy_mask_is_not_shifted(self) -> None:
        from runner.c5_mt5_lora_b0 import shifted_copy_mask

        copymask = torch.ones_like(self.labels, dtype=torch.bool)
        got = shifted_copy_mask(copymask, self.labels)
        expected = self.labels != -100
        self.assertTrue(torch.equal(got, expected))

    def test_copy_ce_uses_same_position_losses(self) -> None:
        from runner.c5_mt5_lora_b0 import copy_ce

        labels = torch.tensor([[10, 11, 12, 13, 14, 15, -100]])
        losses = torch.tensor([[1.0, 2.0, 3.0, 4.0, 5.0, 999.0, 999.0]])
        copymask = torch.tensor([[True, True, True, True, True, False, False]])
        self.assertAlmostEqual(copy_ce(losses, labels, copymask), 3.0)

    def test_generation_record_has_telemetry(self) -> None:
        from runner.c5_mt5_lora_b0 import generation_record

        gen_ids = torch.tensor([[0, 10, 11, 1]])
        record = generation_record(gen_ids, self.tok, 3)
        for key in ("token_ids", "gen_len", "eos", "cap_hit", "special_count", "surface_empty", "rep4", "decoding"):
            self.assertIn(key, record)
        self.assertEqual(record["token_ids"], [0, 10, 11, 1])
        self.assertEqual(record["gen_len"], 4)
        self.assertTrue(record["eos"])
        self.assertTrue(record["cap_hit"])
        self.assertGreaterEqual(record["special_count"], 1)
        self.assertEqual(record["decoding"]["max_new_tokens"], 3)

    def test_training_mode_is_symmetric(self) -> None:
        from runner.c5_mt5_lora_b0 import (
            EXPECTED_LORA_MODULES,
            attach_decoder_lora_mt5,
            make_adapter,
            set_training_mode,
        )

        adapter = make_adapter(17)
        frozen_policy = set_training_mode(self.model, adapter, "frozen")
        self.assertFalse(frozen_policy["base_decoder_training"])
        self.assertTrue(frozen_policy["adapter_training"])
        self.assertFalse(frozen_policy["lora_training"])

        attached = attach_decoder_lora_mt5(self.model)
        self.assertEqual(len(attached), EXPECTED_LORA_MODULES)
        lora_policy = set_training_mode(self.model, adapter, "lora")
        self.assertFalse(lora_policy["base_decoder_training"])
        self.assertTrue(lora_policy["adapter_training"])
        self.assertTrue(lora_policy["lora_training"])
        self.assertTrue(lora_policy["lora_dropout_training"])
        self.assertEqual(lora_policy["lora_modules"], EXPECTED_LORA_MODULES)
        self.assertEqual(lora_policy["trainable_base_parameters"], 0)


if __name__ == "__main__":
    unittest.main()
