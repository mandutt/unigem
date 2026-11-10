# C5 F0 v0.9 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_f0_v0_9_review_2026-11-09/`
- 모델: GLM 5.3 Flash high, DeepSeek 1017 high, Luna 6 xhigh
- 대상: `docs/plan_c5_f0_v0_9_2026-11-09.md`

## 1. 판정

| 검토자 | 판정 | 핵심 |
|---|---|---|
| GLM | **NARROW** | T_proj phase7/M 누락, D1 checkpoint custody, n_donors |
| DeepSeek | **NARROW** | T_proj/96, D1 allowlist/checkpoint oracle, n_boot override, MDE |
| Luna | **NARROW** | D1 schema, init, T_proj, cohort |
| **종합** | **3/3 NARROW** | **F0 미승인** |

## 2. Must-fix

1. T_proj full Phase 6 §11.5 terms; 96 min cap; nproc<12 abort; contention ratio.
2. D1 literal allowlist/checkpoint digest-only/loading forbidden/phase7 filesystem assert.
3. n_boot 10000 explicit override + record.
4. MDE .166/.216 approximate; realized CI half-width.
5. step_seed golden table; hash serialization; base/cache/label freeze.
6. donor all cells/per-doc n_donors=5.
7. title/association-only/lost controls.

## 3. v1.0 반영

- Title `Single-Contrast Diagnostic`.
- T_proj term set + 96 min.
- D1 checkpoint digest-only/load forbidden.
- n_boot override explicit.
- hash/step_seed/donor/MDE.
- association-only/lost controls.
- D0/D1/R stage approvals.

## 4. 결정

```text
F0 v0.9 = 3/3 NARROW
F0 = 미승인, 미실행
v1.0 = 마지막 10번째 라운드
```
