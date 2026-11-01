# V2 — manifest 러너 · 자원 가드 · P1 차단

- 작성: 2026-11-02
- 대상 게이트: G-V0 (b) 자원 상한·디스크 가드, (d) P1 반입 차단
- 구현: `runner/run_job.py`, `runner/instabox_api.py`, 매니페스트 `jobs/*.json`
- 원시 로그: `logs/jobs.jsonl`

## 1. 러너 동작

1. 매니페스트 로드 → `job_id`, `host`, `data_class`, `cmd` 필수 검사
2. **data_class 검사:** `P1`은 즉시 거부(비실행), `P0`만 허용
3. 호스트 상태 확인 (running 아니면 중단)
4. 멱등: 원격 `runs/<job>/exit_code`가 있으면 재실행하지 않음 (`--force`로 무시)
5. **디스크 가드:** `/data` 여유 ≥ `disk_gb + 2GiB`
6. 입력 해시 검증(원격에 파일이 있을 때)
7. 원격 런치 스크립트 생성: `ulimit -v`(메모리), `OMP_NUM_THREADS`, `timeout`
8. setsid 실행 → `exit_code` 파일 폴링 → `done / failed / timeout` 판정
9. 결과를 `logs/jobs.jsonl`에 append

## 2. 가드 검증 (실측)

| 테스트 | 매니페스트 | 기대 | 결과 |
|---|---|---|---|
| 정상 실행 | `V2-smoke-1` (eg2-2) | done, 출력 파일 | **done** — `out.txt = instabox-eg2-2` |
| P1 차단 | `V2-p1-reject` | 거부 | **rejected** — "P1 데이터는 VPS에서 실행 금지" |
| 메모리 상한 | `V2-mem-guard` (0.3GB 상한, 800MB 할당) | 실패 | **failed(exit 1)** — `MemoryError` |
| 타임아웃 | `V2-timeout` (3초 상한, sleep 20) | timeout | **timeout(exit 124)** |
| 디스크 가드 | `V2-disk-guard` (100GB 요구) | 중단 | **no_disk** — free 13.94GB < need 102GB |

- 메모리 상한은 `ulimit -v`로 강제된다. ORT처럼 가상 메모리를 크게 잡는 런타임은
  상한을 실제 RSS보다 여유 있게(예: 6.5GB) 두어야 한다.
- 디스크 가드는 작업 시작 전에만 검사한다. 장시간 작업은 실행 중 증가분을 별도로 봐야 한다(후속).

## 3. 판정

**G-V0 (b) 통과** — 메모리 상한·타임아웃·디스크 가드가 실제로 동작.
**G-V0 (d) 통과** — P1 매니페스트가 실행 전에 거부됨.

## 4. 한계

- 러너는 로컬 오케스트레이터다. VPS 재부팅·회수 시 `exit_code`가 사라지므로,
  실제 학습 job은 자체 체크포인트(문서 §8.2-6)를 가져야 한다.
- 원격 로그 회수는 tail 5줄만 한다. 대용량 산출물은 Notion 경로를 쓴다.
- `maxRunMinutes=480`(8시간) 하드 스톱은 러너가 아니라 플랫폼 제약이다. 장시간 job은
  시작 시각을 기록하고 8시간 전에 stop→start로 클록을 리셋해야 한다.
