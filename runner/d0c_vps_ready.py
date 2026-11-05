"""D0-c — VPS 상태·디스크·venv·네트워크 점검."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import instabox_api as api  # noqa: E402

ROOT = r"C:\code\unigem"
OUT = os.path.join(ROOT, "reports", "provenance", "D0c_vps_ready.json")
IDS = api.machines()
CMD = (
    "hostname; nproc; free -m | head -2; df -h /data | tail -1; "
    "/data/home/unigem/venv/bin/python -V 2>&1; "
    "sha256sum /data/home/unigem/lock_linux.txt 2>/dev/null; "
    "du -sh /data/home/unigem 2>/dev/null; "
    "find /data/home/unigem -maxdepth 3 -name '*.onnx' -printf '%s %p\\n' 2>/dev/null | head -10; "
    "curl -s -o /dev/null -w 'HF %{http_code} %{time_total}s\\n' https://huggingface.co 2>&1"
)


def main():
    out = {}
    for name, mid in IDS.items():
        st = api.get_machine(mid).get("state")
        code, resp = api.exec_cmd(mid, CMD, timeout_s=90)
        out[name] = {"id": mid, "state": st, "http": code, "resp": resp}
        print(name, st, code, flush=True)
        print(json.dumps(resp, ensure_ascii=False)[:2000], flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("saved", OUT)


if __name__ == "__main__":
    main()
