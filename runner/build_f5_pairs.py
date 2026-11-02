"""F5 학습 쌍 — AI Hub 022 gold 요약(passage → summary1/summary3), 2,000쌍."""
from __future__ import annotations

import glob
import json
import os
import zipfile

ROOT = r"C:\code\unigem"
BASE = r"C:\code\dataset\ai_hub\요약, 기계독해를 위한 말뭉치 데이터\022.요약문 및 레포트 생성 데이터\01.데이터"
OUT = os.path.join(ROOT, "data", "external")
N = 2000


def main():
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, "f5_pairs.jsonl")
    seen = set()
    n = 0
    with open(out, "w", encoding="utf-8") as f:
        for z in sorted(glob.glob(BASE + r"\**\TL*.zip", recursive=True)):
            with zipfile.ZipFile(z) as zf:
                for name in zf.namelist():
                    if not name.endswith(".json"):
                        continue
                    try:
                        d = json.loads(zf.read(name).decode("utf-8"))
                        passage = d["Meta(Refine)"]["passage"].strip()
                        ann = d["Annotation"]
                        summ = (ann.get("summary1") or ann.get("summary3") or "").strip()
                        if len(passage) < 100 or len(summ) < 30:
                            continue
                        key = passage[:200]
                        if key in seen:
                            continue
                        seen.add(key)
                        f.write(json.dumps({"id": d["Meta(Refine)"]["passage_id"], "passage": passage,
                                            "summary": summ}, ensure_ascii=False) + "\n")
                        n += 1
                        if n >= N:
                            break
                    except Exception:
                        continue
            print(z.split("\\")[-1], n, flush=True)
            if n >= N:
                break
    print("pairs", n, "->", out)


if __name__ == "__main__":
    main()
