"""Phase V0 — 5대 호스트 점검.

- free tier start rate limit(3/분) 대응: 3대 시작 → 60초 → 2대 시작
- 각 머신에서 OS/CPU/glibc/python/RAM/disk/cgroup/steal 수집
- 결과: env/snapshots/v0_hosts_<date>.json (추적) + logs/V0_hosts.json (원시)
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instabox_api as ib  # noqa: E402

PROBE = (
    'echo "HOST=$(hostname)"; '
    '. /etc/os-release; echo "OS=$PRETTY_NAME"; echo "VERSION=$VERSION_ID"; '
    'echo "KERNEL=$(uname -r)"; echo "ARCH=$(uname -m)"; '
    'echo "GLIBC=$(ldd --version 2>&1 | head -1)"; '
    'echo "PY=$(python3 -V 2>&1)"; '
    'echo "NPROC=$(nproc)"; '
    'echo "CPU=$(grep -m1 \'model name\' /proc/cpuinfo | cut -d: -f2 | xargs)"; '
    'echo "FLAGS=$(grep -m1 \'^flags\' /proc/cpuinfo | tr \' \' \'\\n\' | '
    'grep -xE \'avx2|avx512f|avx512_vnni|avx512bw|f16c|fma\' | sort -u | tr \'\\n\' \',\')"; '
    'free -m | awk \'/Mem:/{print "MEM_TOTAL="$2" MEM_AVAIL="$7}\'; '
    'df -h /data | awk \'NR==2{print "DATA_SIZE="$2" DATA_AVAIL="$4}\'; '
    'df -h / | awk \'NR==2{print "ROOT_AVAIL="$4}\'; '
    'echo "CGROUP2=$(cat /sys/fs/cgroup/cgroup.controllers 2>/dev/null)"; '
    'echo "SYSTEMD_RUN=$(command -v systemd-run || echo none)"; '
    "top -bn2 -d 2 | grep '^%Cpu' | tail -1 | awk '{print \"CPU_LINE=\"$0}'"
)


def parse_kv(stdout: str) -> dict:
    out = {}
    for line in stdout.splitlines():
        line = line.strip()
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def main():
    machines = ib.list_machines()
    print(f"machines: {len(machines)}")
    # 3 + 2 배치 기동 (rate limit 3/min)
    batches = [machines[:3], machines[3:]]
    for bi, batch in enumerate(batches):
        if bi:
            print("sleep 60 for start-rate limit")
            time.sleep(60)
        for m in batch:
            st, body = ib.start(m["id"], idem=f"v0-{m['name']}-{int(time.time())}")
            print(f"start {m['name']}: {st} {body if isinstance(body, dict) else body}")
            time.sleep(2)

    results = {}
    for m in machines:
        ok, state = ib.wait_state(m["id"], "running", timeout_s=300, poll_s=5)
        print(f"{m['name']} state={state} ok={ok}")
        if not ok:
            results[m["name"]] = {"id": m["id"], "state": state}
            continue
        st, resp = ib.exec_cmd(m["id"], PROBE, timeout_s=90)
        if not isinstance(resp, dict):
            results[m["name"]] = {"id": m["id"], "state": state, "exec_status": st, "error": str(resp)[:300]}
            continue
        results[m["name"]] = {
            "id": m["id"],
            "state": state,
            "exitCode": resp.get("exitCode"),
            **parse_kv(resp.get("stdout") or ""),
            "stderr": (resp.get("stderr") or "").strip()[:300],
        }

    out = {"date": str(date.today()), "machines": results}
    os.makedirs("logs", exist_ok=True)
    os.makedirs("env/snapshots", exist_ok=True)
    with open("logs/V0_hosts.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open(f"env/snapshots/v0_hosts_{date.today()}.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    for name, r in results.items():
        print(f"{name}: {r.get('OS','?')} | {r.get('CPU','?')} | {r.get('NPROC','?')}c "
              f"| {r.get('MEM_TOTAL','?')}MB | avx2={('avx2' in (r.get('FLAGS') or ''))} "
              f"| steal={r.get('CPU_LINE','?')}")


if __name__ == "__main__":
    main()
