# C5 F0 v1.0 — Round 10 Final Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_f0_v1_0_review_2026-11-09/`
- 모델: GLM 5.3 Flash high, DeepSeek 1017 high, Luna 6 xhigh
- 대상: `docs/plan_c5_f0_v1_0_2026-11-09.md`
- **10번째(최종) 라운드**
- 추가 학습/평가: 없음

## 1. 판정

| 검토자 | 판정 | 핵심 |
|---|---|---|
| GLM | **CONTINUE** | 구현 commit + D0 stage approval; must-fix는 D0 gate에서 확인 |
| DeepSeek | **NARROW** | D1 seal 모순, cohort length-selected, MDE 산술, provenance |
| Luna | **NARROW** | D1 artifact/oracle, init, MDE provenance, compute |
| **종합** | **1 CONTINUE / 2 NARROW** | **F0 미승인** |

## 2. 10라운드 요약

| round | version | verdict |
|---:|---|---|
| 1 | v0.1 | 3/3 NARROW |
| 2 | v0.2 | 3/3 NARROW |
| 3 | v0.3 | 1 CONTINUE / 2 NARROW |
| 4 | v0.4 | 1 CONTINUE / 2 NARROW |
| 5 | v0.5 | 3/3 NARROW |
| 6 | v0.6 | 3/3 NARROW |
| 7 | v0.7 | 3/3 NARROW |
| 8 | v0.8 | 3/3 NARROW |
| 9 | v0.9 | 3/3 NARROW |
| 10 | v1.0 | **1 CONTINUE / 2 NARROW** |

## 3. Round 10 must-fix

### DS-1. D1 seal 모순 (blocker)

- “3 trained checkpoints exist” vs “digest-only, discarded, load forbidden”.
- “only D1 output” vs M 480/generation 80.
- `eval_arm_d1` materializes `delta_shuffled_*`.
- Fix: separate mechanics evaluator, literal allowlist, writer assert, digest-delete-assert-absent, phase7/checkpoint filesystem asserts.

### DS-2. Cohort length-selected/donor-dependent (blocker)

- 15 common is length-selected: F 15-doc −0.11087 vs 20-doc +0.000195; L −0.11351 vs −0.02218.
- donors reuse val docs.
- Fix: define estimand conditional on 15 length-eligible docs + fixed donor graph; report 20-doc descriptive; donor-cluster sensitivity.

### DS-3. MDE arithmetic (blocker)

- .166/.216 are single-arm SE 0.0594, not paired D.
- Phase 6 paired half-width .037573 (SE .019170), 80% MDE ≈.054, PASS mean ≈.0876.
- If CI_D half-width .117, EQUIVALENT unreachable.
- Fix: derive from paired SE; relabel/drop numbers; rewrite §6.5.

### DS-4. Provenance (blocker)

- No committed F0 driver / code_commit / command / input SHA.
- Fix: commit `runner/c5_pm_f0*.py`, record SHA/command/freeze hashes; no uncommitted driver.

### DS-5. Init audit missing (high)

- step_seed golden, tensor/RNG serialization, post-step0 weight non-equality, all 3 seeds.
- F0 E11 ≠ Phase 6 L via I/O provenance assert.

### DS-6. n_boot silent revert (high)

- `l_predicate` hardcodes 1000; `N_BOOT=1000`.
- Fix: direct bootstrap n_boot=10000, assert, forbid l_predicate.

### DS-7. T_proj (medium)

- Phase 6 t_proj uses F/L/P/PA all arms; F0 slowest-arm aggregation not compatible.
- `contention_ratio`, nproc, setup once.

### DS-8. Scope (medium)

- ROUTE_STOP consequence; descriptive no-inference; dropped 1-seed/null; explicit R approval.

### Luna

- D1 oracle/artifact control.
- Canonical tensor serialization/step_seed golden.
- MDE provenance.
- Compute projection provenance.

## 4. GLM CONTINUE 조건

- F0 구현 commit + D0 stage approval.
- must-fix는 구현/D0 gate에서 확인.
- threshold/seed/donor/step/LR 변경 금지.
- 신규 review round 불요, D0 승인 시점 확인.

## 5. 최종 결정

```text
10/10 라운드 완료
3/3 CONTINUE 미달 (1 CONTINUE / 2 NARROW)
F0 v1.0 = 미승인·미실행
추가 라운드 없음 (사용자 최대 10라운드 지시)
B0-B = 미승인
Phase 6 = negative 종료 불변
test 163 sealed; P1 unused; T5Gemma2 D-108 STOP
```

## 6. 다음 세션 후보

- v1.1: D1 mechanics evaluator 분리, cohort estimand 고정, paired-SE MDE 재계산, F0 driver commit/provenance.
- 그 후 새 3-AI 라운드(별도 승인).
- 실행은 D0/D1/R 각각 별도 승인.
