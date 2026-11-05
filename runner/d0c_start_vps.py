"""D0-c — VPS 5대 기동 및 상태 확인 (rate limit 3/분)."""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import instabox_api as api  # noqa: E402

ROOT = r"C:\code\unigem"
OUT = os.path.join(ROOT, "reports", "provenance", "D0c_vps_start.json")
IDS = list(api.machines().values())


def state(mid):
    return api.get_machine(mid).get("state")


def main():
    started = []
    for mid in IDS[:3]:
        st, body = api.start(mid, idem=f"d0c-start-{mid}-{int(time.time())}")
        started.append({"id": mid, "status": st, "body": body})
        print("start", mid, st, body, flush=True)
    print("wait 60s for rate limit", flush=True)
    time.sleep(60)
    for mid in IDS[3:]:
        st, body = api.start(mid, idem=f"d0c-start-{mid}-{int(time.time())}")
        started.append({"id": mid, "status": st, "body": body})
        print("start", mid, st, body, flush=True)
    deadline = time.time() + 300
    states = {}
    while time.time() < deadline:
        states = {mid: state(mid) for mid in IDS}
        print("states", states, flush=True)
        if all(v == "running" for v in states.values()):
            break
        time.sleep(10)
    out = {"started": started, "states": states, "ids": IDS}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
