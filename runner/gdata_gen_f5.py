"""F5 v3 — LLM 추상 요약(3~5문장) 생성. 체크포인트·재개 지원."""
from __future__ import annotations

import json
import os
import re
import sys
import time

import requests

ROOT = r"C:\code\unigem"
SRC = os.path.join(ROOT, "data", "external", "f5_pairs_v2.jsonl")
OUT = os.path.join(ROOT, "data", "external", "f5_pairs_v3.jsonl")
DONE = os.path.join(ROOT, "logs", "f5_v3_done.json")
COST = os.path.join(ROOT, "data", "external", "f5_v3_cost.json")
URL = "http://127.0.0.1:20128/v1/chat/completions"
MODEL = "rva/deepseek-ai/DeepSeek-V4.1-Flash-1017"
BATCH = 3

SYS = ("너는 한국어 뉴스 편집자다. 주어진 글을 3~5문장으로 요약한다. "
       "규칙: (1) 글의 주제와 핵심 대상(인물·기관·사건)을 중심으로 쓴다. "
       "(2) 인물 이름을 성씨로 줄이지 말고 글에 나온 표기를 유지한다. "
       "(3) 숫자·날짜·금액·고유명사는 원문 그대로 보존한다. "
       "(4) 원문에 없는 내용을 추가하지 않는다. (5) '이 글은', '다음과 같다' 같은 군더더기 없이 바로 요약한다. "
       "출력은 JSON 배열만: [{\"id\":\"...\",\"summary\":\"...\"}]")


def load_done():
    if os.path.exists(DONE):
        return set(json.load(open(DONE, encoding="utf-8")))
    return set()


def save_done(s):
    json.dump(sorted(s), open(DONE, "w", encoding="utf-8"), ensure_ascii=False)


def call(items):
    body = "\n\n".join(f"[{r['id']}]\n{r['passage'][:1800]}" for r in items)
    payload = {"model": MODEL, "temperature": 0.3, "max_tokens": 2200,
               "messages": [{"role": "system", "content": SYS},
                            {"role": "user", "content": body}]}
    for attempt in range(4):
        try:
            r = requests.post(URL, json=payload, timeout=180)
            r.raise_for_status()
            obj, _ = json.JSONDecoder().raw_decode(r.content.decode("utf-8").lstrip())
            txt = obj["choices"][0]["message"]["content"]
            i = txt.find("[")
            arr, _ = json.JSONDecoder().raw_decode(txt[i:])
            out = {}
            for idx, x in enumerate(arr):
                s = str(x.get("summary", "")).strip()
                if not s:
                    continue
                key = str(x.get("id", ""))
                if key in {r["id"] for r in items}:
                    out[key] = s
                else:
                    hit = next((r["id"] for r in items if r["id"].endswith(key)), None)
                    out[hit or items[idx]["id"]] = s
            usage = obj.get("usage", {})
            return out, usage
        except Exception as e:
            print("retry", attempt, type(e).__name__, str(e)[:120], flush=True)
            time.sleep(2 + attempt * 3)
    return {}, {}


def main():
    src = [json.loads(l) for l in open(SRC, encoding="utf-8")]
    done = load_done()
    todo = [r for r in src if r["id"] not in done]
    print("src", len(src), "done", len(done), "todo", len(todo), flush=True)
    ptok = ctok = calls = 0
    with open(OUT, "a", encoding="utf-8") as f:
        for i in range(0, len(todo), BATCH):
            chunk = todo[i:i + BATCH]
            res, usage = call(chunk)
            calls += 1
            ptok += usage.get("prompt_tokens", 0)
            ctok += usage.get("completion_tokens", 0)
            for r in chunk:
                s = res.get(r["id"], "")
                if not s:
                    continue
                f.write(json.dumps({"id": r["id"], "passage": r["passage"], "summary": s,
                                    "target": "llm_summary3to5"}, ensure_ascii=False) + "\n")
                done.add(r["id"])
            f.flush()
            save_done(done)
            json.dump({"calls": calls, "prompt_tokens": ptok, "completion_tokens": ctok},
                      open(COST, "w", encoding="utf-8"))
            if i % 60 == 0:
                print(f"{i}/{len(todo)} calls={calls} done={len(done)}", flush=True)
    print("finished", len(done), "calls", calls, "ptok", ptok, "ctok", ctok, flush=True)


if __name__ == "__main__":
    main()
