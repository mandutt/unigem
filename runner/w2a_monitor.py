"""Wave 2A-lite completion monitor (background; no interactive polling).

Checks local FA/FB logs and eg2-1 F-C logs every 5 minutes. Exits when all four
arm checkpoints exist, or after 4 hours. Writes logs/W2A_lite/monitor.log.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "runner"))
import instabox_api as api

MID = "m_agqvineqfebuv74ez7zv6v6n2y"
OUT = ROOT / "logs/W2A_lite/monitor.log"
MAX_SEC = 4 * 3600
INTERVAL = 300


def local_state() -> dict:
    out = {}
    for arm in ("fa_s42", "fb_s42"):
        ck = ROOT / f"data/wave2a_lite/ckpt/{arm}.pt"
        log = ROOT / f"logs/W2A_lite/train_{arm}.log"
        line = ""
        if log.exists():
            lines = [x for x in log.read_text(encoding="utf-8", errors="replace").splitlines() if x.strip()]
            line = lines[-1] if lines else ""
        out[arm] = {"done": ck.exists(), "last": line[:180]}
    return out


def vps_state() -> dict:
    cmd = ("cd /data/home/unigem; "
           "for a in fc_softmax_s42 fc_concat_s42; do "
           "echo ARM:$a; "
           "tail -2 logs/W2A_${a/fc_softmax/fc_softmax}.log 2>/dev/null || true; "
           "test -f data/wave2a_lite/ckpt/$a.pt && echo DONE:$a; done")
    # Use explicit log names to avoid shell substitution surprises.
    cmd = ("cd /data/home/unigem; "
           "echo SOFTMAX; tail -2 logs/W2A_fc_softmax.log 2>/dev/null; "
           "test -f data/wave2a_lite/ckpt/fc_softmax_s42.pt && echo DONE:fc_softmax_s42; "
           "echo CONCAT; tail -2 logs/W2A_fc_concat.log 2>/dev/null; "
           "test -f data/wave2a_lite/ckpt/fc_concat_s42.pt && echo DONE:fc_concat_s42; "
           "pgrep -af d5_reader | head -2")
    try:
        status, resp = api.exec_cmd(MID, cmd, timeout_s=25)
        return {"status": status, "out": (resp.get("stdout") or "")[-1800:]}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    while True:
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        state = {"ts": stamp, "local": local_state(), "vps": vps_state()}
        with open(OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps(state, ensure_ascii=False) + "\n")
        done_local = all(v["done"] for v in state["local"].values())
        vout = state["vps"].get("out", "")
        done_vps = "DONE:fc_softmax_s42" in vout and "DONE:fc_concat_s42" in vout
        if done_local and done_vps:
            print(f"{stamp} ALL DONE")
            return
        if time.time() - t0 > MAX_SEC:
            print(f"{stamp} MONITOR TIMEOUT")
            return
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
