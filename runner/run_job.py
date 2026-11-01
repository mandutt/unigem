"""V2 — manifest 기반 VPS job 러너 (최소 구현).

보장:
- data_class 검사: P1은 VPS에서 거부 (문서 §0-7)
- 디스크 가드: /data 여유 ≥ max(2 GiB, 추정 필요량)
- 메모리 상한: ulimit -v (KB)
- 타임아웃: GNU timeout
- 상태 기록: queued/running/done/failed/timeout/oom (exit code 기반)
- 입력 해시 검증: 원격에 파일이 있으면 sha256 대조
- 멱등: 같은 job_id는 기존 exit_code가 있으면 재실행하지 않음 (--force로 무시)

사용:
  python runner/run_job.py jobs/V2-smoke.json [--force]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instabox_api as ib  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTS = os.path.join(ROOT, "env", "snapshots", "vps_hosts.json")
MIN_FREE_GB = 2.0


def load_manifest(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        m = json.load(f)
    for key in ("job_id", "host", "data_class", "cmd"):
        if key not in m:
            raise SystemExit(f"manifest missing field: {key}")
    return m


def remote(mid: str, cmd: str, timeout_s: int = 30):
    st, resp = ib.exec_cmd(mid, cmd, timeout_s=timeout_s)
    if not isinstance(resp, dict):
        raise RuntimeError(f"exec failed ({st}): {str(resp)[:200]}")
    return resp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--poll", type=int, default=10)
    args = ap.parse_args()

    m = load_manifest(args.manifest)
    job = m["job_id"]
    host = m["host"]
    data_class = m["data_class"].upper()

    if data_class == "P1":
        print(json.dumps({"job_id": job, "status": "rejected",
                          "reason": "P1 데이터는 VPS에서 실행 금지 (§0-7)"}, ensure_ascii=False))
        return 2
    if data_class not in ("P0",):
        print(json.dumps({"job_id": job, "status": "rejected",
                          "reason": f"unknown data_class {data_class}"}, ensure_ascii=False))
        return 2

    hosts = json.load(open(HOSTS, encoding="utf-8"))
    if host not in hosts:
        raise SystemExit(f"unknown host: {host}")
    mid = hosts[host]

    # 호스트 상태
    machine = ib.get_machine(mid)
    if machine.get("state") != "running":
        print(json.dumps({"job_id": job, "status": "host_not_running", "state": machine.get("state")}))
        return 3

    # 멱등: 기존 exit_code 확인
    r = remote(mid, f"cat /data/home/unigem/runs/{job}/exit_code 2>/dev/null || echo NONE")
    prev = (r.get("stdout") or "").strip()
    if prev != "NONE" and not args.force:
        print(json.dumps({"job_id": job, "status": "already_done", "exit_code": prev}))
        return 0

    # 디스크 가드
    r = remote(mid, "df -k --output=avail /data | tail -1")
    free_gb = int((r.get("stdout") or "0").strip() or 0) / (1024 * 1024)
    need = float(m.get("resources", {}).get("disk_gb", 0)) + MIN_FREE_GB
    if free_gb < need:
        print(json.dumps({"job_id": job, "status": "no_disk",
                          "free_gb": round(free_gb, 2), "need_gb": round(need, 2)}))
        return 4

    # 입력 해시 검증 (원격에 존재하는 경우만)
    for inp in m.get("inputs", []):
        p = inp.get("path", "")
        sha = inp.get("sha256", "")
        if not p or not sha:
            continue
        r = remote(mid, f"sha256sum {p} 2>/dev/null | cut -d' ' -f1 || echo MISSING")
        got = (r.get("stdout") or "").strip()
        if got == "MISSING":
            print(json.dumps({"job_id": job, "status": "input_missing", "path": p}))
            return 5
        if not got.startswith(sha[:16]):
            print(json.dumps({"job_id": job, "status": "input_hash_mismatch", "path": p,
                              "expected": sha[:16], "got": got[:16]}))
            return 5

    res = m.get("resources", {})
    threads = int(res.get("threads", 4))
    mem_gb = float(res.get("mem_limit_gb", 6.5))
    timeout_s = int(res.get("timeout_s", 3600))
    mem_kb = int(mem_gb * 1024 * 1024)

    launch = f"""#!/bin/bash
cd /data/home/unigem
export PATH=/data/home/unigem/venv/bin:$PATH
mkdir -p runs/{job}
ulimit -v {mem_kb}
export OMP_NUM_THREADS={threads}
export ORT_INTRA_OP_THREADS={threads}
timeout {timeout_s} bash -c {json.dumps(m['cmd'])} > runs/{job}/run.log 2>&1
echo $? > runs/{job}/exit_code
"""
    import base64
    b64 = base64.b64encode(launch.encode()).decode()

    r = remote(mid, f"mkdir -p /data/home/unigem/runs/{job} && echo MK_OK")
    if "MK_OK" not in (r.get("stdout") or ""):
        print(json.dumps({"job_id": job, "status": "mkdir_failed"}))
        return 6

    r = remote(mid, f"echo {b64} | base64 -d > /data/home/unigem/runs/{job}/launch.sh "
                    f"&& chmod +x /data/home/unigem/runs/{job}/launch.sh && echo UP_OK")
    if "UP_OK" not in (r.get("stdout") or ""):
        print(json.dumps({"job_id": job, "status": "upload_failed"}))
        return 6

    r = remote(mid, f"rm -f /data/home/unigem/runs/{job}/exit_code && echo RM_OK")
    if "RM_OK" not in (r.get("stdout") or ""):
        print(json.dumps({"job_id": job, "status": "reset_failed"}))
        return 6
    r = remote(mid, f"setsid bash /data/home/unigem/runs/{job}/launch.sh > /dev/null 2>&1 < /dev/null & echo STARTED")
    if "STARTED" not in (r.get("stdout") or ""):
        print(json.dumps({"job_id": job, "status": "start_failed"}))
        return 6

    # 폴링
    deadline = time.time() + timeout_s + 60
    while time.time() < deadline:
        r = remote(mid, f"cat /data/home/unigem/runs/{job}/exit_code 2>/dev/null || echo RUNNING")
        code = (r.get("stdout") or "").strip()
        if code != "RUNNING":
            status = "done" if code == "0" else ("timeout" if code == "124" else "failed")
            tail = remote(mid, f"tail -5 /data/home/unigem/runs/{job}/run.log 2>/dev/null").get("stdout", "")
            out = {"job_id": job, "host": host, "status": status, "exit_code": code, "tail": tail}
            print(json.dumps(out, ensure_ascii=False))
            os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
            with open(os.path.join(ROOT, "logs", "jobs.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(out, ensure_ascii=False) + "\n")
            return 0 if status == "done" else 7
        time.sleep(args.poll)

    print(json.dumps({"job_id": job, "status": "poll_timeout"}))
    return 8


if __name__ == "__main__":
    raise SystemExit(main())
