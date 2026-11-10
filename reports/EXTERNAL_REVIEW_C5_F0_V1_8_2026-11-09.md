# C5 F0 v1.8 — Review Request (New Block Round 8/10)

- 대상: `docs/plan_c5_f0_v1_8_2026-11-09.md`
- 이전: v1.7 = **3/3 NARROW**
- v1.7 스레드 archive 완료
- 미승인·미실행

## 0. Instructions

- 새 스레드 독립 검토; v1.7 결론 상속 금지.
- 파일: `docs/plan_c5_f0_v1_8_2026-11-09.md`, `docs/plan_c5_f0_v1_7_2026-11-09.md`, `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`.
- 금지: 학습/평가, test 163/P1, subagent, repo 수정(지정 report만).
- Q1~Q6 + final STOP/NARROW/CONTINUE.
- `docs/hoplite/c5_f0_v1_8_review_2026-11-09/review_{MODEL}.md`
- reviewed HEAD + verbatim `paired E01−E11`.

## 1. v1.8 변경

- Registered anchor 2 threads/arm (D-157); normative 16 cores, 2/arm; D1 cap provisional; R binding measured wall; D1 T_proj lower bound.
- P/Q/R gate schemas; P 3×4, Q 12 units/9 trained updates, R 900/1440/7200; fail-closed.
- real_memory_ce_calls expected count + flag; provenance_ok in predicates.
- Near-threshold cell-level; paired diagnostic relabeled.
- train20/val20/common ordered hashes; device=cpu.
- .104/.0876 removed; .037573/.019170 retained.
- Wrong-donor residual risk explicit.
- Q artifact/stdout ban; test163/P1 negative read tests.

## 2. 설계

E00 0; E10 adapter; E01 LoRA64; E11 adapter+LoRA64; primary E01−E11; 15 length-eligible; PASS lower>.05 + E01 signal + 2/3 D_s.

## 3. 질문

Q1 P/Q/R gates/schema/hash — 충분한가?
Q2 D1 real CE/seal/telemetry — 충분한가?
Q3 STOP/MDE/near-threshold — 정합하는가?
Q4 Cohort/cell CI/donor conditional — 충분한가?
Q5 Compute 2/arm/caps/lower-bound — 충분한가?
Q6 Scope/negative reads — 충분한가?

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
