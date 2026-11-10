# C5 F0 v1.9 — Review Request (New Block Round 9/10)

- 대상: `docs/plan_c5_f0_v1_9_2026-11-09.md`
- 이전: v1.8 = **3/3 NARROW**
- v1.8 스레드 archive 완료
- 미승인·미실행

## 0. Instructions

- 새 스레드 독립 검토; v1.8 결론 상속 금지.
- 파일: `docs/plan_c5_f0_v1_9_2026-11-09.md`, `docs/plan_c5_f0_v1_8_2026-11-09.md`, `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`.
- 금지: 학습/평가, test 163/P1, subagent, repo 수정(지정 report만).
- Q1~Q6 + final STOP/NARROW/CONTINUE.
- `docs/hoplite/c5_f0_v1_9_review_2026-11-09/review_{MODEL}.md`
- reviewed HEAD + verbatim `paired E01−E11`.

## 1. v1.9 변경

- D1 CE count from committed evaluator call graph; 20-doc vs 15-doc separated; freeze at code commit; dry-run; mismatch NOT_EVALUABLE.
- P per_seed schema; Q per-seed 4 units/3 trained updates.
- D1 signal delta never materialized; M/generation counts in memory not persisted.
- D1 wall >25 min repair/re-review; R 96 binding.
- R mechanics counts added.
- Loader allowlist before full-split parse; transitive test163/P1 read test.
- 8 logical threads (4×2), affinity/quota, orchestrator commit.
- Near-threshold mean/CI-lower/seed-sign margins, non-decisional.

## 2. 설계

E00 0; E10 adapter; E01 LoRA64; E11 adapter+LoRA64; primary E01−E11; 15 length-eligible; PASS lower>.05 + E01 signal + 2/3 D_s.

## 3. 질문

Q1 D1 CE formula/dry-run — 충분한가?
Q2 P/Q per-seed schema — 충분한가?
Q3 D1 materialization/wall fallback — 충분한가?
Q4 R mechanics/scope boundary — 충분한가?
Q5 Compute 8 threads/affinity — 충분한가?
Q6 Near-threshold/scope — 충분한가?

## 4. 답변

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거
- 다음 단계

최종 판정: STOP / NARROW / CONTINUE
Init:
D1:
STOP/MDE:
Cohort:
Compute:
Scope:
Must-fix (ranked):
잘못된 전제:
```
