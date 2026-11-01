# jobs/ — job manifest

문서 §8.5 규격. 시크릿은 절대 넣지 않는다. 러너는 `runner/`에 둔다.

```json
{
  "job_id": "C3-armA2-s1",
  "stage": "C3",
  "host": "vps-2",
  "data_class": "P0",
  "env_lock": "env/lock_linux_2026-11-01.txt",
  "inputs": [{"path": "data/c3/train.jsonl", "sha256": "..."}],
  "cmd": "python train/adapter_t5g2.py --config cfg/a2.yaml --seed 1",
  "resources": {"threads": 4, "mem_limit_gb": 6.5, "timeout_s": 28800},
  "outputs": [{"path": "runs/C3-armA2-s1/"}],
  "resume": true,
  "seed": 1
}
```

러너 보장 사항: `data_class` 검사(P1이면 VPS 거부), 디스크 여유 확인(2GB 이상), 메모리 상한,
타임아웃, 상태 기록(`queued/running/done/failed/oom/timeout`), 로그·결과 회수, 입력 해시 검증,
재개·멱등.
