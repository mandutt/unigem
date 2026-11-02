"""G-DATA 1단계 품질 검증 — 슬롯 보존·환각·중복·길이 + 사람 검토 시트."""
from __future__ import annotations

import csv
import json
import os
import re
from collections import Counter

ROOT = r"C:\code\unigem"
D = os.path.join(ROOT, "data", "external")
SLOT = re.compile(r"[A-Za-z][A-Za-z0-9._/-]{2,}|\d[\d,.]*%?|https?://\S+")


def slots(s):
    return set(m.group(0).strip(".,)(") for m in SLOT.finditer(s))


def stats_f6(rows):
    keep = 0; n_slot = 0; slot_tot = 0; slot_ok = 0; halluc = 0; ratios = []
    for r in rows:
        a, b = r["correct"], r["error"]
        if a == b:
            continue
        keep += 1
        sa, sb = slots(a), slots(b)
        if sa:
            n_slot += 1; slot_tot += len(sa); slot_ok += len(sa & sb)
        halluc += len(sb - sa)
        ratios.append(len(b) / max(1, len(a)))
    return {"n": keep, "n_with_slots": n_slot, "slot_total": slot_tot,
            "slot_preserved": slot_ok, "slot_rate": slot_ok / max(1, slot_tot) if slot_tot else None,
            "hallucinated_slots": halluc,
            "len_ratio_mean": sum(ratios) / max(1, len(ratios))}


def stats_f5(rows):
    numer = 0; halluc = 0; total = 0; ratios = []
    for r in rows:
        a, b = r["passage"], r["summary"]
        sa, sb = slots(a), slots(b)
        total += len(sb); numer += len(sb & sa); halluc += len(sb - sa)
        ratios.append(len(b) / max(1, len(a)))
    return {"n": len(rows), "summary_slots": total,
            "summary_slots_in_passage": numer,
            "hallucinated_slots": halluc,
            "halluc_rate": halluc / max(1, total),
            "len_ratio_mean": sum(ratios) / max(1, len(ratios))}


def dup_rate(rows, key):
    seen = Counter(r[key][:120] for r in rows)
    return sum(1 for v in seen.values() if v > 1) / max(1, len(rows))


def main():
    f6 = [json.loads(l) for l in open(os.path.join(D, "f6_pairs.jsonl"), encoding="utf-8")]
    f5 = [json.loads(l) for l in open(os.path.join(D, "f5_pairs.jsonl"), encoding="utf-8")]
    res = {"f6": stats_f6(f6), "f5": stats_f5(f5),
           "f6_dup": dup_rate(f6, "error"), "f5_dup": dup_rate(f5, "summary")}
    json.dump(res, open(os.path.join(ROOT, "logs", "GDATA_validate.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(res, ensure_ascii=False, indent=1), flush=True)

    # 사람 검토 시트 (F6 50 + F5 50)
    import random
    rng = random.Random(0)
    path = os.path.join(D, "gdata_review_sample.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kind", "id", "input", "output", "acceptable_1to3", "note"])
        for r in rng.sample(f6, 50):
            w.writerow(["F6", r["id"], r["correct"], r["error"], "", ""])
        for r in rng.sample(f5, 50):
            w.writerow(["F5", r["id"], r["passage"][:1500], r["summary"], "", ""])
    print("sheet", path, flush=True)


if __name__ == "__main__":
    main()
