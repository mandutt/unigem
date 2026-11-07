"""Tests for D-086 hybrid manifest and AI prompt inputs."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MANIFEST = ROOT / "reports/provenance/C5_hybrid/manifest.json"
D085 = ROOT / "reports/provenance/C5_human50/manifest.json"
SPLITS = ROOT / "reports/provenance/C5_clean/splits.json"
INPUTS = ROOT / "reports/provenance/C5_hybrid/ai_inputs"


class TestHybridManifest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.d085 = json.loads(D085.read_text(encoding="utf-8"))
        cls.splits = json.loads(SPLITS.read_text(encoding="utf-8"))

    def test_counts(self) -> None:
        self.assertEqual(self.m["sample_n"], 50)
        self.assertEqual(self.m["ai_panel"]["total_ratings"], 600)
        self.assertEqual(self.m["human_calibration"]["ratings"], 80)
        self.assertEqual(self.m["human_repeat"]["ratings"], 20)
        self.assertEqual(self.m["human_total_ratings"], 100)
        self.assertEqual(len(self.m["ai_panel"]["judges"]), 3)

    def test_calibration_and_repeat_are_subsets(self) -> None:
        sample = {x["id"] for x in self.d085["targeted"] + self.d085["random"]}
        calib = set(self.m["calibration_ids"])
        repeat = set(self.m["repeat_ids"])
        self.assertEqual(len(calib), 20)
        self.assertEqual(len(repeat), 5)
        self.assertTrue(calib <= sample)
        self.assertTrue(repeat <= calib)

    def test_no_test(self) -> None:
        sample = set(self.m["calibration_ids"]) | set(self.m["repeat_ids"])
        self.assertFalse(sample & set(self.splits["test"]))

    def test_judge_orders(self) -> None:
        for j in self.m["ai_panel"]["judges"]:
            orders = self.m["judge_arm_order"][j["id"]]
            self.assertEqual(len(orders), 50)
            for order in orders.values():
                self.assertEqual(sorted(order), sorted(self.m["arms"]))
                self.assertEqual(len(set(order)), 4)

    def test_hashes_and_status(self) -> None:
        self.assertEqual(self.m["status"], "FROZEN")
        self.assertTrue(self.m["frozen_before_ai_calls"])
        self.assertTrue(self.m["frozen_before_human_ratings"])
        self.assertEqual(self.m["test_163"], "SEALED")
        self.assertEqual(len(self.m["hashes"]), 50)
        self.assertTrue(all(len(v["source_sha256"]) == 64 for v in self.m["hashes"].values()))

    def test_decision_rule(self) -> None:
        d = self.m["decision_rule"]
        self.assertEqual(d["primary_contrast"], "2586 - pilot300")
        self.assertEqual(d["adequacy_lower_95_margin"], -0.25)
        self.assertEqual(d["critical_unsupported_upper_95_margin"], 0.05)
        self.assertEqual(d["ai_human_calibration"]["adequacy_icc21_min"], 0.70)
        self.assertEqual(d["contested"]["max_rate"], 0.10)


class TestAiInputs(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.rows = {}
        for j in cls.m["ai_panel"]["judges"]:
            path = INPUTS / f"judge_{j['id']}.jsonl"
            cls.rows[j["id"]] = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

    def test_input_counts(self) -> None:
        for jid, rows in self.rows.items():
            self.assertEqual(len(rows), 50, jid)
            self.assertEqual(len({r["doc_id"] for r in rows}), 50)

    def test_no_arm_names_or_metrics(self) -> None:
        forbidden = ["pilot300", "1293", "1940", "2586", "char_f1", "grounded", "checkpoint"]
        for rows in self.rows.values():
            for r in rows:
                for token in forbidden:
                    self.assertNotIn(token, r["prompt"])

    def test_prompt_has_four_summaries(self) -> None:
        for rows in self.rows.values():
            for r in rows:
                for label in ("SUMMARY A", "SUMMARY B", "SUMMARY C", "SUMMARY D"):
                    self.assertIn(label, r["prompt"])
                self.assertIn("Return ONLY valid JSON", r["prompt"])

    def test_model_config(self) -> None:
        self.assertEqual(
            {j["id"]: (j["model"], j["reasoning"]) for j in self.m["ai_panel"]["judges"]},
            {
                "glm": ("z-ai/glm-5.3-flash", "max"),
                "sonnet": ("claude-sonnet-5-5", "high"),
                "sol": ("gpt-6.1-sol", "xhigh"),
            },
        )


if __name__ == "__main__":
    unittest.main()
