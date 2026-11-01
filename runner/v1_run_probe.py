"""V1b — 각 VPS에서 v1_probe.py 실행 + 로컬 대비 cosine 비교.

전제: /data/home/unigem/venv 구성 완료(setup.done), 머신 running.
결과: logs/V1_probe.json
"""
from __future__ import annotations

import base64
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instabox_api as ib  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PROBE = os.path.join(HERE, "v1_probe.py")
LOCAL = os.path.join(os.path.dirname(HERE), "logs", "v1_local.json")


def cos(a, b):
    num = sum(x * y for x, y in zip(a, b))
    da = math.sqrt(sum(x * x for x in a))
    db = math.sqrt(sum(y * y for y in b))
    return num / (da * db + 1e-12)


def parse_json(stdout: str):
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except Exception:
                continue
    return None


def main():
    with open(PROBE, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    with open(LOCAL, encoding="utf-8") as f:
        local = json.load(f)

    results = {}
    for m in ib.list_machines():
        if m.get("state") != "running":
            print(f"skip {m['name']} state={m.get('state')}")
            continue
        name, mid = m["name"], m["id"]
        st, resp = ib.exec_cmd(
            mid,
            f"echo {b64} | base64 -d > /data/home/unigem/v1_probe.py && "
            "wc -c < /data/home/unigem/v1_probe.py",
            timeout_s=30,
        )
        size = (resp.get("stdout") or "").strip() if isinstance(resp, dict) else ""
        print(f"{name} upload: {size} bytes")
        st, resp = ib.exec_cmd(
            mid,
            "/data/home/unigem/venv/bin/python /data/home/unigem/v1_probe.py",
            timeout_s=180,
        )
        out = (resp.get("stdout") or "") if isinstance(resp, dict) else ""
        data = parse_json(out)
        if not data:
            results[name] = {"error": out[-300:], "stderr": (resp.get("stderr") or "")[-300:]}
            print(f"{name} probe FAILED: {out[-200:]}")
            continue
        coss = []
        for a, b in zip(data["runs"], local["runs"]):
            coss.append(round(cos(a["y"], b["y"]), 9))
        for r in data["runs"]:
            r.pop("y", None)
        data["cos_vs_local"] = coss
        results[name] = data
        print(f"{name}: p50={[r['p50_ms'] for r in data['runs']]} cos={coss}")

    os.makedirs("logs", exist_ok=True)
    with open("logs/V1_probe.json", "w", encoding="utf-8") as f:
        json.dump({"local": local, "vps": results}, f, ensure_ascii=False, indent=2)
    print("saved logs/V1_probe.json")


if __name__ == "__main__":
    main()
