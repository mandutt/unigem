# C5 F0 v0.7 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_f0_v0_7_review_2026-11-09/`
- 모델: GLM 5.3 Flash high, DeepSeek 1017 high, Luna 6 xhigh
- 대상: `docs/plan_c5_f0_v0_7_2026-11-09.md`
- 추가 학습/평가: 없음

## 1. 판정

| 검토자 | 판정 | 핵심 |
|---|---|---|
| GLM | **NARROW** | D1 phase7 plaintext, T_proj, H3 reason table |
| DeepSeek | **NARROW** | D1 raw delta, reason enum, H3 trigger, MDE, caps |
| Luna | **NARROW** | D1 custody, H3 details, T_proj, donor protocol |
| **종합** | **3/3 NARROW** | **F0 미승인** |

## 2. 닫힌 것

- PASS/EQUIVALENT overlap.
- ALL_FAIL fallback reason.
- predicate 통일.
- donor all-cell equality.
- step_seed/init audit.

## 3. Must-fix

### MF-1. D1 signal persistence (GLM/DS/Luna, blocker)

- D1 still materializes `d1_sealed`/phase7/final; readable.
- v0.8: D1 does not compute/persist signal, per_doc, phase7, final; mechanics only.
- `d1_report.json` exact-path ban; no `d1_sealed/`.

### MF-2. H3 out of scope (GLM/DS/Luna)

- H3 trigger/details keep generating blockers and is unreachable in likely INDETERMINATE.
- v0.8: H3 completely removed from F0; separate prereg after F0.

### MF-3. T_proj/caps (GLM/DS/Luna)

- T_proj undefined; 150 min cap unjustified; 1.316 underived.
- v0.8: T_proj formula 3×(setup+100×step+eval+gen); D1 25, R 120; no cap increase.
- MDE ≈.166; .05 lower bound only.

### MF-4. Reason enum (DS)

- condition names vs reason strings inconsistent.
- v0.8: enum `no_signal_equivalent`, `adapter_harm`, `adapter_benefit`, `no_signal_uncertain`.

### MF-5. D1 phase7 leak (GLM)

- D1 phase7 per-donor deltas plaintext.
- v0.8: D1 phase7 = 0; R only.

### MF-6. H3 reason table (GLM)

- moot via H3 removal.

## 4. 결정

```text
F0 v0.7 = 3/3 NARROW
F0 = 미승인, 미실행
v0.8 = D1 no-signal, H3 out, T_proj/caps, reason enum, phase7 R-only
```

## 5. 다음

- v0.8 3-AI 재검토 (v0.7 스레드 archive).
- 3/3 CONTINUE까지 또는 최대 10라운드.
