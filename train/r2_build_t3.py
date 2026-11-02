"""R2 T3′ — AI Hub 교정문 기반 최소쌍 5유형 (자연문장).

정답 문장은 AI Hub C4의 cor_sentence(사람 교정문)에서 채굴.
오답 문장은 대상 형태만 1글자 치환해 생성. 라벨: 정답 형태=1, 오답=0.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import zipfile

import ijson

ROOT = r"C:\code\unigem"
BASE = (r"C:\code\dataset\ai_hub\인터페이스(자판음성)별 고빈도 오류 교정 데이터"
        r"\143.인터페이스(자판-음성)별 고빈도 오류 교정 데이터\01-1.정식개방데이터\Training\02.라벨링데이터")
OUT = os.path.join(ROOT, "data", "r2")

RULES = {
    "doe": [("되었", "돼었"), ("되면", "돼면"), ("되고", "돼고"), ("돼요", "되요"), ("돼서", "되서")],
    "an": [("않", "안")],
    "ro": [("로서", "로써"), ("로써", "로서")],
    "deon": [("던", "든"), ("든", "던")],
    "nat": [("낫", "낳"), ("낳", "났"), ("났", "낫")],
}
WANT = 900  # 유형별 문장 수


def split_of(k):
    v = int(hashlib.sha256(k.encode()).hexdigest()[:8], 16) % 100
    return "train" if v < 70 else ("val" if v < 85 else "test")


def main():
    os.makedirs(OUT, exist_ok=True)
    got = {k: [] for k in RULES}
    files = sorted(f for f in os.listdir(BASE) if f.endswith(".zip"))
    for fn in files:
        if all(len(v) >= WANT for v in got.values()):
            break
        with zipfile.ZipFile(os.path.join(BASE, fn)) as zf:
            name = zf.namelist()[0]
            with zf.open(name) as f:
                for rec in ijson.items(f, "data.item"):
                    s = rec.get("annotation", {}).get("cor_sentence", "").strip()
                    if not s or len(s) < 12:
                        continue
                    for typ, pairs in RULES.items():
                        if len(got[typ]) >= WANT:
                            continue
                        for good, bad in pairs:
                            pos = s.find(good)
                            if pos >= 0 and bad not in s:
                                got[typ].append((s, s[:pos] + bad + s[pos + len(good):], pos, good, bad))
                                break
        print(fn, {k: len(v) for k, v in got.items()}, flush=True)

    rows = []
    for typ, items in got.items():
        for i, (good, bad, pos, a, b) in enumerate(items):
            g = f"{typ}-{i}"
            sp = split_of(g)
            rows.append({"id": f"{g}-ok", "kind": f"t3_{typ}", "lang": "ko_kr", "text": good,
                         "split": sp, "group": g, "label": 1, "target_char": pos, "source": "aihub-c4"})
            rows.append({"id": f"{g}-bad", "kind": f"t3_{typ}", "lang": "ko_kr", "text": bad,
                         "split": sp, "group": g, "label": 0, "target_char": pos, "source": "aihub-c4+rule"})
    with open(os.path.join(OUT, "t3_corpus.jsonl"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("rows", len(rows), "pairs", len(rows) // 2,
          "by_type", {t: len(v) for t, v in got.items()},
          "splits", {k: sum(1 for r in rows if r["split"] == k) for k in ("train", "val", "test")})


if __name__ == "__main__":
    main()
