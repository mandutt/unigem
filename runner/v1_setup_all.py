"""Phase V1a — 5대 VPS 공통 venv 구성 (base64 주입 + setsid 실행 + 완료 마커 폴링).

전제: 머신이 running 상태. 스크립트는 runner/vps_setup.sh.
결과: logs/V1_setup.json, 각 머신 /data/home/unigem/lock_linux.txt
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instabox_api as ib  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SETUP = os.path.join(HERE, "vps_setup.sh")


def main():
    with open(SETUP, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    machines = [m for m in ib.list_machines() if m.get("state") == "running"]
    print(f"running machines: {[m['name'] for m in machines]}")

    launched = []
    for m in machines:
        mid, name = m["id"], m["name"]
        st, resp = ib.exec_cmd(mid, "mkdir -p /data/home/unigem && echo MK_OK", timeout_s=30)
        ok = isinstance(resp, dict) and "MK_OK" in (resp.get("stdout") or "")
        print(f"{name} mkdir: {st} ok={ok}")
        if not ok:
            launched.append({"name": name, "launched": False, "resp": str(resp)[:200]})
            continue
        cmd = (
            f"echo {b64} | base64 -d > /data/home/unigem/setup.sh && "
            "chmod +x /data/home/unigem/setup.sh && "
            "rm -f /data/home/unigem/setup.done && "
            "FORCE_REBUILD=1 setsid bash /data/home/unigem/setup.sh > /data/home/unigem/setup.log 2>&1 < /dev/null & "
            "echo LAUNCHED"
        )
        st, resp = ib.exec_cmd(mid, cmd, timeout_s=30)
        out = (resp.get("stdout") or "") if isinstance(resp, dict) else ""
        print(f"{name} launch: {st} {out.strip()[:40]} exit={resp.get('exitCode') if isinstance(resp, dict) else '?'}")
        launched.append({"name": name, "launched": "LAUNCHED" in out})

    # 완료 폴링 (최대 30분)
    deadline = time.time() + 1800
    pending = {x["name"]: x for x in launched if x.get("launched")}
    done = {}
    while pending and time.time() < deadline:
        for name in list(pending):
            m = next(x for x in machines if x["name"] == name)
            st, resp = ib.exec_cmd(m["id"], "ls /data/home/unigem/setup.done 2>/dev/null || echo PENDING", timeout_s=20)
            out = (resp.get("stdout") or "") if isinstance(resp, dict) else ""
            if "setup.done" in out:
                done[name] = True
                pending.pop(name)
        if pending:
            print(f"pending: {list(pending)} ({int(deadline - time.time())}s left)")
            time.sleep(30)

    result = {"launched": launched, "done": sorted(done), "pending": sorted(pending)}
    os.makedirs("logs", exist_ok=True)
    with open("logs/V1_setup.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
