"""F5 재구축 — AI Hub 022 gold summary3(3문장) 우선, 없으면 summary2/1."""
from __future__ import annotations

import glob
import json
import os
import zipfile

ROOT = r"C:\code\unigem"
BASE = r"C:\code\dataset\ai_hub\요약, 기계독해를 위한 말뭉치 데이터\022.요약문 및 레포트 생성 데이터\01.데이터"
OUT = os.path.join(ROOT, "data", "external", "f5_pairs_v2.jsonl")
N = 2000


def main():
    seen = set(); n = 0
    with open(OUT, "w", encoding="utf-8") as f:
        for z in sorted(glob.glob(BASE + r"\**\TL*.zip", recursive=True)):
            with zipfile.ZipFile(z) as zf:
                for name in zf.namelist():
                    if not name.endswith(".json"):
                        continue
                    try:
                        d = json.loads(zf.read(name).decode("utf-8"))
                        passage = d["Meta(Refine)"]["passage"].strip()
                        ann = d["Annotation"]
                        summ = (ann.get("summary3") or ann.get("summary2") or ann.get("summary1") or "").strip()
                        kind = "summary3" if ann.get("summary3") else ("summary2" if ann.get("summary2") else "summary1")
                        if len(passage) < 100 or len(summ) < 30:
                            continue
                        key = passage[:200]
                        if key in seen:
                            continue
                        seen.add(key)
                        f.write(json.dumps({"id": d["Meta(Refine)"]["passage_id"], "passage": passage,
                                            "summary": summ, "target": kind}, ensure_ascii=False) + "\n")
                        n += 1
                        if n >= N:
                            break
                    except Exception:
                        continue
            print(z.split("\\")[-1], n, flush=True)
            if n >= N:
                break
    print("pairs", n, "->", OUT)


if __name__ == "__main__":
    main()
