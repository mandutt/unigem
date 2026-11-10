# C5 F0 — Second 10-Round 3-AI Review Block Synthesis

- 작성일: 2026-11-10
- 대상 블록: v1.1 ~ v1.10
- 이전 블록: v0.1 ~ v1.0 = **1 CONTINUE / 2 NARROW**
- 이번 블록 결과: **3/3 CONTINUE 미달**
- F0 상태: **미승인·미실행**
- 모델: GLM `z-ai/glm-5.3-flash` high, DeepSeek `deepseek-v4.1-flash-1017` high, Luna `gpt-6-luna` xhigh
- 각 라운드 전 기존 스레드 archive 완료

## 1. 라운드 판정

| round | version | GLM | DeepSeek | Luna |
|---:|---|---|---|---|
| 11 | v1.1 | CONTINUE | NARROW | NARROW |
| 12 | v1.2 | CONTINUE | NARROW | NARROW |
| 13 | v1.3 | NARROW | NARROW | NARROW |
| 14 | v1.4 | CONTINUE | NARROW | NARROW |
| 15 | v1.5 | CONTINUE | NARROW | NARROW |
| 16 | v1.6 | CONTINUE | NARROW | NARROW |
| 17 | v1.7 | NARROW | NARROW | NARROW |
| 18 | v1.8 | NARROW | NARROW | NARROW |
| 19 | v1.9 | NARROW | NARROW | NARROW |
| 20 | v1.10 | **CONTINUE** | **NARROW** | **NARROW** |

- **3/3 CONTINUE: 0회**
- **2 CONTINUE: 0회**
- **1 CONTINUE / 2 NARROW: 6회** (v1.1, v1.2, v1.4, v1.5, v1.6, v1.10)
- **3/3 NARROW: 4회** (v1.3, v1.7, v1.8, v1.9)
- DeepSeek: 10/10 전부 NARROW
- Luna: 10/10 전부 NARROW

## 2. v1.10 최종 draft

`docs/plan_c5_f0_v1_10_2026-11-09.md`

반영:
- D1 CE operation table를 D1 이전에 freeze, 독립 instrumented expected count, post-hoc 금지
- P/Q/R pre-update hash per seed/cell, fail-closed
- R mechanics full expected counts/formula
- F0 allowlist-first loader + transitive test163/P1 negative tests
- D1 payload count/discard at source, logs/crash/temp tests, >25 min hard abort + new code SHA/re-approval
- CPU set/quota/thread-pool 기록
- near-threshold signed margins, non-decisional
- D1 3 threads/arm measured, registered 2 threads/arm measured; neither F0
- EQUIVALENT `SE_D <= .0255`
- plan §15 Q1-Q6 rewritten

## 3. 마지막 라운드 판정 내용

### GLM — CONTINUE (조건부)

동의: init contract, D1 seal 구조, STOP/MDE proxy, 15-doc cohort, scope/route-only.

Must-fix:
1. CPU affinity/quota/thread-pool fields in `parallel`/R provenance schema.
2. Define or remove `r/f0_replay.json`.
3. Resolve 13A.1 vs 13A.8 wrong-donor wording; Q first execution, R first persisted use.
4. Restrict crash-path `error` enum so CE values cannot leak via error/log.

### Luna — NARROW

Must-fix:
1. D1 custody/overrun enforcement: checkpoint/log/temp/crash controls, 25-min hard timeout, fail-closed partial.
2. P/Q/R provenance/hash binding complete.
3. D1 seal proof and no-read reconciliation.
4. Compute affinity/quota, not `nproc` alone.
5. near-threshold named boundaries.
6. F0 implementation committed and reviewed before stage approval.

### DeepSeek — NARROW

- v1.10 thread `thr_0bea249f9378417d90ca7c1e0881d3dd`는 stop→fup 재개 후 보고서를 생성했다.
- 판정: **NARROW**. D1 frozen table의 donor_count와 `donor_map_loads:0`/`wrong_donor_ce_calls:0` 모순, overrun 3중 정의, CPU affinity/quota 미반영, 4,939.884s measured/not-measured 모순.
- v1.8 DS도 stop→fup으로 복구 성공(3/3 NARROW), v1.9 DS는 정상 완료(NARROW).

## 4. 결론

- 새 10라운드 블록에서도 **F0는 승인되지 않았다**.
- GLM은 v1.10을 조건부 CONTINUE로 보았으나, DS와 Luna는 NARROW다.
- 따라서 **3/3 CONTINUE 조건 미충족**, **F0 미승인·미실행**.
- 다음 단계는 v1.11이 아니라 **별도 결정**이다:
  1. GLM must-fix 4건 + Luna must-fix를 반영한 v1.11을 만들고 새 블록을 열 것인가.
  2. F0 구현(`runner/c5_pm_f0*.py`)을 먼저 commit하고 D0 stage approval을 받을 것인가.
  3. F0를 접고 Phase 6 negative 종료/B0-B 미승인 상태를 유지할 것인가.
- **D0/D1/P/Q/R 실행 없음**, test 163 sealed, P1 unused, T5Gemma2 D-108 STOP 유지.

## 5. 원문 경로

- `docs/hoplite/c5_f0_v1_{1..10}_review_2026-11-09/review_GLM.md`
- `docs/hoplite/c5_f0_v1_{1..10}_review_2026-11-09/review_DS1017.md`
- `docs/hoplite/c5_f0_v1_{1..10}_review_2026-11-09/review_LUNA.md`
- `docs/hoplite/c5_f0_v1_{1..10}_review_2026-11-09/threads.json`

## 6. 커밋

- v1.1~v1.10 요청서·draft·스레드 기록: `5f362b1`, `fbbc547`, `eab9109`, `de90ebd`, `a1288c8` 및 이후 보고서 커밋
