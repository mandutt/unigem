# C5 F0 v0.5 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_f0_v0_5_review_2026-11-09/`
- 모델: GLM 5.3 Flash high, DeepSeek 1017 high, Luna 6 xhigh
- 대상: `docs/plan_c5_f0_v0_5_2026-11-09.md`
- 추가 학습/평가: 없음

## 1. 판정

| 검토자 | 판정 | 핵심 |
|---|---|---|
| GLM | **NARROW** | EQUIVALENT/harm/benefit overlap, INDETERMINATE 귀착 |
| DeepSeek | **NARROW** | D1 schema 모순, seed variance, ALL_FAIL+benefit, T_proj, H3 rank |
| Luna | **NARROW** | equivalence boundary, reason priority, D1 gate |
| **종합** | **3/3 NARROW** | **F0 미승인** |

## 2. 닫힌 것

- ROUTE_STOP 부호 (harm=`CI_D.lower>0`).
- ALL_FAIL E01/E11×copy/full.
- D1 seal allowlist/negative test.
- cohort 5 donors.
- post-step0 RNG hash.
- R cap 150min.
- H3 QR/identity/trigger.

## 3. Must-fix

### MF-1. EQUIVALENT overlap (GLM/Luna, blocker)

- `CI_D=[+0.01,+0.04]` is both harm and EQUIVALENT.
- `CI_D=[-0.04,-0.01]` is both benefit and EQUIVALENT.
- v0.5 table sends both to ROUTE_STOP via EQUIVALENT; bullet says benefit→INDETERMINATE.
- v0.6: reason precedence `EQUIVALENT > harm > benefit`; harm/benefit defined as NOT EQUIVALENT.

### MF-2. ALL_FAIL+benefit (DS)

- Keeping a failing route alive as INDETERMINATE is not justified.
- v0.6: ALL_FAIL → ROUTE_STOP regardless of direction; reason `benefit` if applicable.
- `INDETERMINATE` only when not ALL_FAIL.

### MF-3. D1 schema contradiction (DS, blocker)

- Assertions `step0/final n_docs` conflict with denylist banning `final`/`step0`.
- v0.6: scalar `n_docs_step0`/`n_docs_final`; exact-key allowlist; sanitized partial.
- injection/invariance tests.

### MF-4. Seed variance (DS, blocker)

- Doc-level CI excludes seed variance.
- v0.6: `PASS_POSITIVE` additionally requires 2/3 seeds `D_s>0`; n_boot 10000.

### MF-5. R cap (DS)

- 1.316 multiplier underived; mixes 8-thread and 12-thread configs.
- v0.6: R cap 150 provisional; T_proj primary; nproc≥12; orchestrator commit.

### MF-6. Init audit (DS)

- Add base/cache/label hashes, per-step reseed, digest canonicalization/capture point.
- v0.6 반영.

### MF-7. H3 (DS/Luna)

- E01-P rank 512 is identity; use `r<512`.
- zero-init mandatory; permuted null + donor-discrimination; trigger unified.
- v0.6 반영.

## 4. 결정

```text
F0 v0.5 = 3/3 NARROW
F0 = 미승인, 미실행
v0.6 = equivalence priority, ALL_FAIL stop, D1 schema, seed gate, T_proj, H3
```

## 5. 다음

- v0.6 3-AI 재검토 (새 스레드, v0.5 스레드 archive).
- 3/3 CONTINUE까지 또는 최대 10라운드.
