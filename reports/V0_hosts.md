# V0 — VPS 5대 호스트 점검

- 작성: 2026-11-02
- 대상 게이트: G-V0 (§8.6 (a)~(d) 중 V0 부분)
- 호스트: `eg2-1` ~ `eg2-5` (InstaBox 계정 B, free tier)
- 원시 로그: `logs/V0_hosts.json`, 스냅샷 `env/snapshots/local/v0_hosts_2026-11-02.json`(미추적)

## 1. 목적

VPS 5대의 OS·커널·glibc·Python·CPU 명령어 세트·RAM·디스크·cgroup·steal time을 기록하고,
Phase V1(환경 구성·정합·캘리브레이션)의 전제 조건을 확인한다.

## 2. 결과

| 항목 | eg2-1 | eg2-2 | eg2-3 | eg2-4 | eg2-5 |
|---|---|---|---|---|---|
| 상태 | running | running | running | running | running |
| OS | Debian 13 (trixie) | 동일 | 동일 | 동일 | 동일 |
| 커널 | 6.18.54-instabox | 6.18.60 | 6.18.60 | 6.18.60 | 6.18.60 |
| glibc | 2.41 | 2.41 | 2.41 | 2.41 | 2.41 |
| Python | 3.13.5 | 3.13.5 | 3.13.5 | 3.13.5 | 3.13.5 |
| CPU | AMD EPYC, 4 vCPU | 동일 | 동일 | 동일 | 동일 |
| ISA | avx2, avx512f, avx512bw, **avx512_vnni**, f16c, fma | 동일 | 동일 | 동일 | 동일 |
| RAM | 7,964 MB (가용 7,234) | 7,964 (7,611) | 7,964 (7,610) | 7,964 (7,610) | 7,964 (7,607) |
| /data | 20G, 여유 17G | 16G | 16G | 16G | 16G |
| / (root) 여유 | 11G | 11G | 11G | 11G | 11G |
| cgroup v2 | memory 컨트롤러 포함 | 동일 | 동일 | 동일 | 동일 |
| systemd-run | 있음 | 있음 | 있음 | 있음 | 있음 |
| steal (idle) | 0.1% | 0.0% | 0.0% | 0.0% | 0.0% |

- 전 머신이 **동일 클래스**(같은 OS·CPU·RAM·디스크)로 확인됐다. 커널만 eg2-1이 6.18.54로 한 단계 낮다.
- **AVX-512 VNNI 지원** — Q8(MatMulNBits)에서 VNNI 커널을 쓸 수 있는 조건이다. 단, 실제 이득은 V1 캘리브레이션에서 측정한다.
- cgroup v2 memory 컨트롤러와 `systemd-run`이 있어 **메모리 상한(`MemoryMax`)·타임아웃을 커널 수준에서 강제**할 수 있다.
- 유휴 steal은 0%대지만, 공유 vCPU이므로 **부하 시 steal을 다시 측정**해야 한다(V1 캘리브레이션).

## 3. 문서 가정과의 차이

| 항목 | 문서(§3.2) | 실측 | 영향 |
|---|---|---|---|
| RAM | 8GB | 7,964MB (가용 7.6GB) | mem_limit 상한을 6.5GB 이하로 잡아야 안전 |
| 디스크 | 20GB | /data 20GB(여유 16~17GB), root 11GB | 모델·캐시 배치 시 여유 2GB 규칙 유지 필요 |
| OS | Linux(미확정) | Debian 13 trixie, glibc 2.41 | wheel 호환성 문제 없음(py3.13 지원 확인 필요) |

## 4. 미확인

- 제공사 약관의 **장시간 CPU 사용·트래픽 한도** 조항은 문서로 확인하지 못했다. 플랫폼 제약(`maxRunMinutes=480`, idle 30분 suspend)은 API로 실측했다.
- 네트워크 대역(HF 다운로드·로컬 rsync 속도)은 V1에서 측정한다.

## 5. 판정

**G-V0: 부분 통과 (V0 완료, V1·V2 대기)**
- (a) venv·정합 검증 — V1에서 판정
- (b) 자원 상한·디스크 가드 — V2에서 판정 (cgroup v2·systemd-run 가용 확인됨)
- (c) 캘리브레이션 — V1에서 판정
- (d) P1 반입 차단 — V2에서 판정

## 6. 다음 단계

1. V1: 5대 공통 venv + lock, 정합(동일 모델 출력 cosine), 캘리브레이션(스레드별 p50, steal).
2. V2: manifest 러너, 디스크 가드, 메모리 상한, P1 거부 테스트.
