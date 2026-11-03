"""D0-a — 정규화 라벨 정정 및 재계산.

Notesoop 382클립 예측(`logs/C2_A1/fleurs_pred.jsonl`)에 대해
구 정규화(Notesoop normalize_text)와 신 정규화(eval.normalize)의
공백 포함/무시 CER을 각각 계산한다.
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = r"C:\code\unigem"
sys.path.insert(0, ROOT)

from eval.normalize import _edit_distance, normalize  # noqa: E402

# Notesoop normalize_text와 동일한 규칙(공백 포함)
_PUNCT = re.compile(r"[?!.,\"~:;()\[\]{}<>@#$%^&*_+=\\/\\|`·…“”‘’]")
_SPACE = re.compile(r"\s+")


def old_norm(s: str) -> str:
    return _SPACE.sub(" ", _PUNCT.sub(" ", s)).strip()


def corpus(fn, rows, ignore_space: bool) -> float:
    edits = total = 0
    for r in rows:
        a, b = fn(r["ref"]), fn(r["hyp"])
        if ignore_space:
            a, b = _SPACE.sub("", a), _SPACE.sub("", b)
        edits += _edit_distance(a, b)
        total += len(a)
    return edits / total


def main():
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "logs", "C2_A1", "fleurs_pred.jsonl"), encoding="utf-8")]
    out = {"n": len(rows), "systems": {}}
    for name, fn in (("old", old_norm), ("new", normalize)):
        out["systems"][name] = {
            "cer_space": corpus(fn, rows, False),
            "cer_nospace": corpus(fn, rows, True),
        }
    # pair-wise difference distribution (new - old)
    diffs = []
    for r in rows:
        old_s = cer_prepared(old_norm(r["ref"]), old_norm(r["hyp"]), False)
        new_s = cer_prepared(normalize(r["ref"]), normalize(r["hyp"]), False)
        old_n = cer_prepared(old_norm(r["ref"]), old_norm(r["hyp"]), True)
        new_n = cer_prepared(normalize(r["ref"]), normalize(r["hyp"]), True)
        diffs.append({"id": r["id"], "space": new_s - old_s, "nospace": new_n - old_n})
    out["delta_space_mean"] = sum(d["space"] for d in diffs) / len(diffs)
    out["delta_nospace_mean"] = sum(d["nospace"] for d in diffs) / len(diffs)
    out["improved_space"] = sum(1 for d in diffs if d["space"] < 0)
    out["improved_nospace"] = sum(1 for d in diffs if d["nospace"] < 0)
    os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
    with open(os.path.join(ROOT, "logs", "D0a_normalization.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
