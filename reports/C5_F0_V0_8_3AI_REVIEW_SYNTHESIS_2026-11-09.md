# C5 F0 v0.8 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_f0_v0_8_review_2026-11-09/`
- 모델: GLM 5.3 Flash high, DeepSeek 1017 high, Luna 6 xhigh
- 대상: `docs/plan_c5_f0_v0_8_2026-11-09.md`
- 추가 학습/평가: 없음

## 1. 판정

| 검토자 | 판정 | 핵심 |
|---|---|---|
| GLM | **NARROW** | D1 negative test 전수, F0≠Phase6 L 수치 고정 |
| DeepSeek | **NARROW** | EQUIVALENT 문장 모순, MDE power, cap |
| Luna | **NARROW** | D1 schema/path, R cap/T_proj, step_seed |
| **종합** | **3/3 NARROW** | **F0 미승인** |

## 2. 닫힌 것

- D1 no-signal persistence.
- H3 out of scope.
- PASS/EQUIVALENT disjoint.
- reason enum/fallback.
- donor all-cell.
- T_proj formula.
- MDE stated.

## 3. Must-fix

### MF-1. EQUIVALENT 문장 모순 (DS, blocker)

- “No equality claim from a CI that contains 0” conflicts with `[-.04,+.04]` being EQUIVALENT.
- v0.9: sentence removed; practical equivalence only.

### MF-2. MDE power (DS)

- .166 is 50% power; 80% ≈.216; .05 gate underpowered.
- v0.9: both stated; results bounded/exploratory.

### MF-3. Cap 불일치 (DS/Luna)

- v0.8 had 150/120 mixed; Q5 150.
- v0.9: all R cap 120; D1 25.

### MF-4. D1 schema/path (Luna/GLM)

- exact schema/path still incomplete; negative test paths.
- v0.9: exact key inventory, no d1_sealed/d1_report/final/per_doc/phase7.

### MF-5. Init/step_seed (GLM/Luna)

- step_seed semantics/tests.
- v0.9: golden test and canonical hash.

## 4. 결정

```text
F0 v0.8 = 3/3 NARROW
F0 = 미승인, 미실행
v0.9 = EQUIVALENT 문장, MDE power, cap 통일, D1 schema
```

## 5. 다음

- v0.9 3-AI 재검토 (v0.8 스레드 archive).
- 3/3 CONTINUE까지 또는 최대 10라운드.
