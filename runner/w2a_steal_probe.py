"""Sample CPU steal deltas on all Wave 2A-lite VPS hosts.

Writes one JSON line per minute to logs/W2A_lite/steal_probe.jsonl.
This distinguishes:
  - host-specific noisy neighbor (only one machine rises)
  - provider-wide sustained-load throttling (clean machines rise after N minutes)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "runner"))
import instabox_api as api

HOSTS = api.machines()
OUT = ROOT / "logs/W2A_lite/steal_probe.jsonl"
DURATION = 3600
INTERVAL = 60


def sample(mid: str) -> dict:
    cmd = "grep '^cpu ' /proc/stat; nproc; uptime | sed 's/.*load average: //'"
    status, r = api.exec_cmd(mid, cmd, timeout_s=20)
    if not isinstance(r, dict):
        return {"error": f"{status}: {str(r)[:200]}"}
    lines = (r.get("stdout") or "").strip().splitlines()
    if not lines:
        return {"error": status}
    vals = [int(x) for x in lines[0].split()[1:]]
    # user nice system idle iowait irq softirq steal guest guest_nice
    steal = vals[7] if len(vals) > 7 else 0
    total = sum(vals[:8])
    return {"steal": steal, "total": total, "load": lines[2] if len(lines) > 2 else ""}


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prev = {}
    end = time.time() + DURATION
    while time.time() < end:
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        row = {"ts": ts, "hosts": {}}
        for name, mid in HOSTS.items():
            cur = sample(mid)
            p = prev.get(name)
            if p and "error" not in cur:
                ds = cur["steal"] - p["steal"]
                dt = cur["total"] - p["total"]
                cur["steal_pct"] = round(100.0 * ds / dt, 3) if dt > 0 else None
            prev[name] = cur
            row["hosts"][name] = cur
        with open(OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
