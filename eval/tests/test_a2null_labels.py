"""Contract tests for A2-null target labels.

The tokenizer adds <bos> but not <eos>. The trainer must produce
content + exactly one <eos>, with no <bos>, and mask everything after EOS.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_a2null_full_train import make_batch  # noqa: E402

T5 = ROOT / "data/models/t5gemma-2-270m-270m"


class TestA2NullLabels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tok = AutoTokenizer.from_pretrained(str(T5), local_files_only=True)

    def test_content_plus_one_eos_without_bos(self):
        target = "테스트 문장입니다."
        by_id = {"r1": {"summary": target}}
        rec = {"id": "r1", "z": np.zeros((2, 768), dtype=np.float32), "length": 2}
        z, mask, labels = make_batch([rec], by_id, self.tok, max_memory=4, max_target=32)
        lab = labels[0]
        n = len(self.tok(target, add_special_tokens=False)["input_ids"])
        self.assertEqual(z.shape[0], 1)
        self.assertGreaterEqual(z.shape[1], 2)
        self.assertTrue(bool(mask[0, :2].all()))
        self.assertNotIn(self.tok.bos_token_id, lab.tolist())
        self.assertEqual(int((lab == self.tok.eos_token_id).sum()), 1)
        self.assertEqual(int(lab[n].item()), self.tok.eos_token_id)
        self.assertTrue(bool((lab[n + 1 :] == -100).all()))


if __name__ == "__main__":
    unittest.main()
