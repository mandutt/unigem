#!/usr/bin/env python3
"""Build D-086 AI-panel input prompts.

No AI call is made here. Each judge gets 50 independent doc prompts with its
own A-D order. The prompt contains no arm names, checkpoint steps, metrics,
target summaries, human ratings, or other-judge outputs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reports/provenance/C5_hybrid/manifest.json"
CLEAN = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
PILOT = ROOT / "reports/provenance/C5_a1/pilot300_val161/predictions.jsonl"
RUN = ROOT / "reports/provenance/C5_a1/full_2ep"
OUTDIR = ROOT / "reports/provenance/C5_hybrid/ai_inputs"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    # Use the base 50, not only calibration 20.
    d085 = json.loads((ROOT / "reports/provenance/C5_human50/manifest.json").read_text(encoding="utf-8"))
    sample = [x["id"] for x in d085["targeted"] + d085["random"]]
    data = {str(r["id"]): r for r in load_jsonl(CLEAN) if str(r["id"]) in set(sample)}
    preds = {
        "pilot300": {str(r["id"]): str(r.get("pred") or "") for r in load_jsonl(PILOT)},
        "1293": {str(r["id"]): str(r.get("pred") or "") for r in load_jsonl(RUN / "eval_step_1293/eval.jsonl")},
        "1940": {str(r["id"]): str(r.get("pred") or "") for r in load_jsonl(RUN / "eval_step_1940/eval.jsonl")},
        "2586": {str(r["id"]): str(r.get("pred") or "") for r in load_jsonl(RUN / "eval_step_2586/eval.jsonl")},
    }
    for rid in sample:
        if rid not in data:
            raise SystemExit(f"missing source: {rid}")
        for arm in preds:
            if rid not in preds[arm] or not preds[arm][rid].strip():
                raise SystemExit(f"missing/empty {arm}: {rid}")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    summary = {}
    for judge in manifest["ai_panel"]["judges"]:
        jid = judge["id"]
        lines = []
        for rid in sample:
            order = manifest["judge_arm_order"][jid][rid]
            labels = ["A", "B", "C", "D"]
            summaries = {labels[i]: preds[arm][rid] for i, arm in enumerate(order)}
            prompt = PROMPT_TEMPLATE.format(
                doc_id=rid,
                source=str(data[rid]["passage"]).strip(),
                a=summaries["A"].strip(),
                b=summaries["B"].strip(),
                c=summaries["C"].strip(),
                d=summaries["D"].strip(),
            )
            lines.append({"judge": jid, "model": judge["model"], "reasoning": judge["reasoning"], "doc_id": rid, "prompt": prompt})
        path = OUTDIR / f"judge_{jid}.jsonl"
        path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in lines) + "\n", encoding="utf-8")
        summary[jid] = {"path": str(path), "docs": len(lines), "bytes": path.stat().st_size}

    print(json.dumps({"outdir": str(OUTDIR), "judges": summary, "total_prompts": 150}, ensure_ascii=False, indent=2))
    return 0


PROMPT_TEMPLATE = """You are an independent evaluator for Korean news summaries.
Read the SOURCE and four summaries A-D. Rate each summary independently against the SOURCE.
Use only the SOURCE. Do not use outside knowledge. Do not try to infer which system produced a summary.
Do not compare a summary to another summary; rate each on its own.

SOURCE:
<<<SOURCE
{doc_id}
{source}
SOURCE>>>

SUMMARY A:
<<<A
{a}
A>>>

SUMMARY B:
<<<B
{b}
B>>>

SUMMARY C:
<<<C
{c}
C>>>

SUMMARY D:
<<<D
{d}
D>>>

RUBRIC:
- adequacy (0-4): 4 = almost all key facts/relations/qualifiers preserved and sufficient; 3 = key meaning preserved with minor loss; 2 = only part preserved or one important omission/distortion; 1 = most key meaning lost or misleading; 0 = not a functioning summary (empty/repetition/severe hallucination).
- critical_unsupported (0/1): 1 if the summary adds important facts, numbers, entities, causes, dates, or conclusions not supported by SOURCE. Do not flag ordinary paraphrase or harmless connective wording.
- critical_omission (0/1): 1 if omitting a fact changes a reader's understanding or decision; do not flag every minor detail.
- wrong_unit_qualifier (0/1): 1 if a number/unit, time, date, condition, or scope is wrong or materially missing (e.g. 18명 -> 18, 오전 -> 오후, 2020 -> 2021).
- entity_relation (0/1): 1 if a person/institution/place or a relation (who did what to whom, cause/effect) is wrong.
- fluency (1-5): 5 = natural Korean; 3 = understandable but awkward/repetitive; 1 = barely readable.
- utility (1-5): 5 = directly useful for a reader's decision; 3 = needs work; 1 = not useful.
Multiple flags may be 1 at the same time. Be conservative: flag critical issues only when clear from SOURCE.

Return ONLY valid JSON, with no markdown fences, in exactly this schema:
{{
  "doc_id": "{doc_id}",
  "summaries": {{
    "A": {{"adequacy": 0, "critical_unsupported": 0, "critical_omission": 0, "wrong_unit_qualifier": 0, "entity_relation": 0, "fluency": 1, "utility": 1, "evidence": ["short source quote"], "reason": "one or two sentences"}},
    "B": {{"adequacy": 0, "critical_unsupported": 0, "critical_omission": 0, "wrong_unit_qualifier": 0, "entity_relation": 0, "fluency": 1, "utility": 1, "evidence": ["short source quote"], "reason": "one or two sentences"}},
    "C": {{"adequacy": 0, "critical_unsupported": 0, "critical_omission": 0, "wrong_unit_qualifier": 0, "entity_relation": 0, "fluency": 1, "utility": 1, "evidence": ["short source quote"], "reason": "one or two sentences"}},
    "D": {{"adequacy": 0, "critical_unsupported": 0, "critical_omission": 0, "wrong_unit_qualifier": 0, "entity_relation": 0, "fluency": 1, "utility": 1, "evidence": ["short source quote"], "reason": "one or two sentences"}}
  }}
}}"""


if __name__ == "__main__":
    raise SystemExit(main())
