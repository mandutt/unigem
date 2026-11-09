# C5 F0 v0.3 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_f0_v0_3_review_2026-11-09/`
- 검토 HEAD: `4534f86b0e9d31a2a1f370dded5a29f7bf869583`
- 대상: `docs/plan_c5_f0_v0_3_2026-11-09.md`
- 모델: GLM 5.3 Flash high, DeepSeek 1017 high, Luna 6 xhigh
- 이전 F0 스레드 6개: archive 완료
- 추가 학습/평가: 없음

## 1. 판정

| 검토자 | 최종 판정 | 핵심 |
|---|---|---|
| GLM | **CONTINUE** | 구조적 결함 3개 closed; definitional must-fix 6개 |
| DeepSeek | **NARROW** | compute 재현성, D1 seal, STOP taxonomy, cohort binding |
| Luna | **NARROW** | STOP truth table, D1 비결정 강제, init audit, cap |
| **종합** | **1 CONTINUE / 2 NARROW** | **F0 미승인** |

## 2. 닫힌 것

- Stage D selection gate / track STOP 제거.
- E01/E11 LoRA init mismatch 수정.
- D1 E00 optimizer 모순 수정 (3 updates).
- Primary = paired E01−E11.
- final-checkpoint primary source.
- protocol-valid STOP gate.
- H3 분리.

## 3. Must-fix

### MF-1. Compute 회계 재현성 (DS blocker)

- v0.3 §12 “3 threads/arm” vs Phase 6 prereg `threads 6`.
- Phase 6 D1 parallel measured 1,180.6s / 19.68min; sequential 3,116.5s.
- Committed `run_d1` is sequential 6 threads and does not emit `wall_estimate_s`/`parallel_arms`/`cap_ok`.
- Need F0-specific parallel orchestrator committed; exact threads/arm + total logical threads.

### MF-2. D1 signal-read 기계적 강제 (DS blocker, Luna must-fix)

- `not_a_result` metadata만으로는 signal read를 막지 못한다.
- Need D1 signal sealed + sha256; decision driver input allowlist excludes sealed signal.
- D1 mechanics-only.

### MF-3. STOP/판정 taxonomy (DS/Luna/GLM)

- 4-state mutually exclusive/exhaustive: NOT_EVALUABLE / PASS_POSITIVE / ROUTE_STOP / INDETERMINATE.
- `FAIL(c,e)=NOT SIGNAL(c,e)` per §6.4; remove ambiguous “3/3 seeds”.
- `E01≈E11` vs ROUTE_STOP priority.
- `CI_D not >0` split into `upper<0` (harm) vs uncertain.
- `PASS_POSITIVE` should require E01 cell signal.

### MF-4. Primary cohort binding (GLM)

- 15 common = frozen preflight common_ids.
- All 15 present in `unit.final.per_doc` for every cell×seed; `eval_arm_d1` silently drops docs.
- Missing → NOT_EVALUABLE, no 15→14.

### MF-5. Init hash 감사 (DS/Luna)

- Canonical hash inputs; `lora_names` 64 equality; lora_A/B zero-init distinction.
- `post_init_rng_state_sha256` E01==E11.
- F0 E11 ≠ Phase 6 L at init.
- “LoRA fixed” = init only; dropout training stream diverges.

### MF-6. H3 (GLM/Luna)

- LN/projection frozen; train20 only.
- residual identity metric; zero-init branch if identity claim.
- H3 trigger only after F0 PASS/INDETERMINATE with adapter direction.

### MF-7. D0 timing (DS minor)

- `elapsed_s`/`phase_timings` for 15min cap.

## 4. 결정

```text
F0 v0.3 = 1 CONTINUE / 2 NARROW
F0 = 미승인, 미실행
v0.4 = compute/ seal/taxonomy/cohort/init/H3/D0 timing 반영
```

## 5. 다음

- v0.4 3-AI 재검토 (새 스레드, 이전 v0.3 스레드 archive).
- 3/3 CONTINUE까지 또는 최대 10라운드.
