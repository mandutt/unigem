# C5 F0 v0.8 — Independent Review Request

- 작성일: 2026-11-09
- 대상: `docs/plan_c5_f0_v0_8_2026-11-09.md` (DRAFT v0.8)
- 이전: v0.7 = 3/3 NARROW
- 이전 v0.7 검토 스레드 3개는 **archive 완료**
- 상태: **미승인·미실행**
- test 163: sealed
- P1: unused
- T5Gemma2: D-108 STOP
- **새 독립 검토 라운드**.

---

## 0. Reviewer Instructions

1. 새 스레드에서 독립 검토하라. v0.7 결론을 상속하지 말라.
2. 아래 파일을 직접 읽어라.
   - `docs/plan_c5_f0_v0_8_2026-11-09.md`
   - `docs/plan_c5_f0_v0_7_2026-11-09.md` (superseded)
   - `reports/C5_F0_V0_7_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_F0_V0_6_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`
   - `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`
   - `runner/c5_pm_phase6.py`
3. 학습·평가 실행 금지. test 163/P1 사용 금지. 서브에이전트/추가 LLM 금지.
4. repository 수정 금지. 지정 report 파일만 작성.
5. Q1~Q6에 판정 + 근거 + 다음 단계.
6. 최종 판정 STOP / NARROW / CONTINUE.
7. 보고서 경로:
   `docs/hoplite/c5_f0_v0_8_review_2026-11-09/review_{MODEL}.md`
8. reviewed HEAD와 verbatim quote `paired E01−E11` 포함.

---

## 1. v0.8 변경

1. **D1 no signal persistence**
   - D1은 signal/per_doc/phase7/final을 생성하지 않음.
   - `d1_mechanics.json` only; `d1_report.json` exact-path 금지; no `d1_sealed/`.
2. **H3 F0에서 완전 제거**
   - H3 arm/trigger/rank/null은 F0 문서에 없음.
   - 별도 prereg/승인; F0가 H3 자동 개시하지 않음.
3. **T_proj/caps**
   - `T_proj_R = 3 × (setup_s + 100×step_s + eval_final_s + gen_s)`.
   - D1 25 min, R 120 min; cap 상향 없음.
   - MDE ≈ .166 명시; .05 lower bound.
4. **Reason enum**
   - `no_signal_equivalent`, `adapter_harm`, `adapter_benefit`, `no_signal_uncertain`.
5. **Donor protocol**
   - E00/E10/E01/E11 all-cell 5-donor equality.
6. **Init**
   - per-step reseed, step_seed golden test, base/cache/label hashes.
7. **Phase7**
   - D1 0; Stage R 7,200 only.

## 2. 설계

| cell | memory | adapter | LoRA | updates |
|---|---|---|---|---|
| E00 | EG2 raw | none | none | 0 |
| E10 | EG2 raw | trained | none | 100 |
| E01 | EG2 raw | none | 64 | 100 |
| E11 | EG2 raw | trained | 64 | 100 |

- Primary E01 vs E11 matched LoRA init.
- Primary final-checkpoint donor-crop, 15 common.
- PASS: `mean_D>0`, `CI_D.lower>.05`, E01 signal, 2/3 D_s.
- STOP taxonomy exact; MDE .166.

## 3. 검토 질문

### Q1. Initialization audit

Per-step reseed, step_seed test, hashes, F0≠Phase6 L — 충분한가?

### Q2. D1 no-signal

D1이 signal/per_doc/phase7/final을 전혀 생성하지 않는 설계가 seal 우회를 제거하는가? gate negative test가 충분한가?

### Q3. STOP taxonomy

PASS lower>.05, reason enum, ALL_FAIL fallback, MDE .166이 정합하는가?

### Q4. Cohort/CI

15 common, 3/3 seed, 5 donors all cells, n_boot=10000, donor dependence, seed gate가 충분한가?

### Q5. Compute

T_proj 공식, D1 25/R 120, nproc≥12, 900 updates가 정합하는가?

### Q6. Scope

H3를 F0에서 완전히 제거한 것이 타당한가? F0 approval과 H3 분리가 충분한가?

## 4. 답변 형식

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거
- 다음 단계: 1~3개

최종 판정: STOP / NARROW / CONTINUE
Initialization:
D1 no-signal:
STOP taxonomy:
Cohort/CI:
Compute:
Scope:
Must-fix (ranked):
잘못된 전제:
```

## 5. 금지

- 승인 전 F0 실행 금지
- 학습·평가 실행 금지
- test 163/P1 사용 금지
- repository 수정 금지 (지정 report만)
- subagent/추가 LLM 금지
- threshold/seed/donor/step/LR 변경 금지
- B0-B/B1/B2/Stage C 자동 진행 금지
