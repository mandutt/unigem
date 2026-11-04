"""G-DATA 1단계 — F6 교정 쌍 생성 (P0, DeepSeek-V4.1-Flash-1017, 9router).

입력: AI Hub C4 교정문(P0) 1,000문장.
출력: (error, corrected) 쌍. 5문장/호출, 체크포인트·비용 기록.
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import time
import zipfile

import ijson
import requests

ROOT = r"C:\code\unigem"
OUT = os.path.join(ROOT, "data", "external")
BASE = (r"C:\code\dataset\ai_hub\인터페이스(자판음성)별 고빈도 오류 교정 데이터"
        r"\143.인터페이스(자판-음성)별 고빈도 오류 교정 데이터\01-1.정식개방데이터\Training\02.라벨링데이터")
MODEL = "rva/deepseek-ai/DeepSeek-V4.1-Flash-1017"
URL = "http://127.0.0.1:20128/v1/chat/completions"
N = 1200
BATCH = 5
PII = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|01\d{1}-\d{3,4}-\d{4}|\d{6}-\d{7}")

SYS = ("한국어 맞춤법 데이터 생성기. 올바른 문장을 의미 변화 없이 자연스러운 오류 1~2개가 있는 문장으로 바꾼다. "
       "오류 유형: 띄어쓰기, 자모 오타, 되/돼·안/않 혼동. 고유명사·숫자는 바꾸지 않는다. "
       "출력은 JSON 배열만: [{\"id\":\"...\",\"error\":\"...\"}]")


def sentences(n):
    out = []
    for fn in sorted(glob.glob(os.path.join(BASE, "*.zip"))):
        if len(out) >= n:
            break
        with zipfile.ZipFile(fn) as z:
            with z.open(z.namelist()[0]) as f:
                for rec in ijson.items(f, "data.item"):
                    s = rec.get("annotation", {}).get("cor_sentence", "").strip()
                    if 20 <= len(s) <= 150 and not PII.search(s) and s not in out:
                        out.append(s)
                        if len(out) >= n:
                            break
        print("collected", len(out), flush=True)
    return out[:n]


def call(batch):
    payload = [{"id": x["id"], "correct": x["correct"]} for x in batch]
    body = {"model": MODEL, "temperature": 0.7, "max_tokens": 900, "stream": False,
            "messages": [{"role": "system", "content": SYS},
                         {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}
    for attempt in (1, 2, 3):
        try:
            r = requests.post(URL, json=body, timeout=300)
            r.raise_for_status()
            d, _ = json.JSONDecoder().raw_decode(r.text.lstrip())
            txt = d["choices"][0]["message"]["content"].strip()
            txt = re.sub(r"^```(?:json)?|```$", "", txt, flags=re.M).strip()
            i = txt.find("[")
            if i < 0:
                i = txt.find("{")
            arr, _ = json.JSONDecoder().raw_decode(txt[i:])
            if isinstance(arr, dict):
                arr = [arr]
            return arr, d.get("usage", {})
        except Exception as e:
            print("retry", attempt, type(e).__name__, str(e)[:120], flush=True)
            time.sleep(3 * attempt)
    return None, {}


def main():
    os.makedirs(OUT, exist_ok=True)
    src = os.path.join(OUT, "f6_source.jsonl")
    if not os.path.exists(src):
        ss = sentences(N)
        with open(src, "w", encoding="utf-8") as f:
            for i, s in enumerate(ss):
                f.write(json.dumps({"id": f"s{i:04d}", "correct": s}, ensure_ascii=False) + "\n")
    items = [json.loads(l) for l in open(src, encoding="utf-8")]
    out = os.path.join(OUT, "f6_pairs.jsonl")
    done = {json.loads(l)["id"] for l in open(out, encoding="utf-8")} if os.path.exists(out) else set()
    todo = [x for x in items if x["id"] not in done]
    print("items", len(items), "todo", len(todo), flush=True)
    cost = {"calls": 0, "prompt": 0, "completion": 0}
    cp = os.path.join(OUT, "f6_cost.json")
    if os.path.exists(cp):
        cost = json.load(open(cp, encoding="utf-8"))
    for b in range(0, len(todo), BATCH):
        batch = todo[b:b + BATCH]
        arr, usage = call(batch)
        if not arr:
            print("FAILED batch", batch[0]["id"], flush=True); continue
        by = {x["id"]: x.get("error", "") for x in arr if isinstance(x, dict) and "id" in x}
        with open(out, "a", encoding="utf-8") as f:
            for x in batch:
                err = by.get(x["id"], "").strip()
                if not err or err == x["correct"]:
                    continue
                ratio = len(err) / max(1, len(x["correct"]))
                if not (0.7 <= ratio <= 1.4) or PII.search(err):
                    continue
                f.write(json.dumps({"id": x["id"], "correct": x["correct"], "error": err,
                                    "model": MODEL}, ensure_ascii=False) + "\n")
        cost["calls"] += 1
        cost["prompt"] += usage.get("prompt_tokens", 0)
        cost["completion"] += usage.get("completion_tokens", 0)
        json.dump(cost, open(cp, "w", encoding="utf-8"))
        if cost["calls"] % 10 == 0:
            print("calls", cost["calls"], "pairs", sum(1 for _ in open(out, encoding="utf-8")),
                  "tokens", cost["prompt"], cost["completion"], flush=True)
    print("DONE", cost, flush=True)


if __name__ == "__main__":
    main()
