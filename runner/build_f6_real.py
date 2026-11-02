"""F6 재구축 — AI Hub 71560 실제 오류-교정 gold 쌍 (6개 오류 유형 stratified)."""
from __future__ import annotations

import glob
import json
import os
import random
import zipfile

ROOT = r"C:\code\unigem"
BASE = (r"C:\code\dataset\ai_hub\인터페이스(자판음성)별 고빈도 오류 교정 데이터"
        r"\143.인터페이스(자판-음성)별 고빈도 오류 교정 데이터\01-1.정식개방데이터\Training\02.라벨링데이터")
OUT = os.path.join(ROOT, "data", "external", "f6_pairs_v2.jsonl")
PER = 220  # 유형당 최대


def main():
    rng = random.Random(0)
    pool = {}
    for z in sorted(glob.glob(BASE + r"\TL_*.zip")):
        name = os.path.basename(z)[3:-4]
        items = []
        with zipfile.ZipFile(z) as zf:
            for n in zf.namelist():
                if not n.endswith(".json"):
                    continue
                try:
                    d = json.loads(zf.read(n).decode("utf-8"))
                except Exception:
                    continue
                for it in d.get("data", []):
                    a = it.get("annotation", {})
                    e = (a.get("err_sentence") or "").strip()
                    c = (a.get("cor_sentence") or "").strip()
                    if not e or not c or e == c:
                        continue
                    if not (10 <= len(e) <= 200):
                        continue
                    items.append({"id": it.get("metadata_info", {}).get("id", ""),
                                  "correct": c, "error": e, "type": name,
                                  "source": it.get("metadata_info", {}).get("source", "")})
        rng.shuffle(items)
        pool[name] = items[:PER]
        print(name, len(items), "->", len(pool[name]), flush=True)

    rows = [r for v in pool.values() for r in v]
    rng.shuffle(rows)
    seen = set(); out = []
    for r in rows:
        k = r["error"][:80]
        if k in seen:
            continue
        seen.add(k); out.append(r)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("total", len(out), "->", OUT)


if __name__ == "__main__":
    main()
