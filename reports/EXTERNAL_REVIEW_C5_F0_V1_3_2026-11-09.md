# C5 F0 v1.3 — Review Request (New Block Round 3/10)

- 대상: `docs/plan_c5_f0_v1_3_2026-11-09.md`
- 이전: v1.2 = GLM CONTINUE / DS NARROW / Luna NARROW
- v1.2 스레드 archive 완료
- 미승인·미실행

## 0. Instructions

- 새 스레드 독립 검토; v1.2 결론 상속 금지.
- 파일: `docs/plan_c5_f0_v1_3_2026-11-09.md`, `docs/plan_c5_f0_v1_2_2026-11-09.md`, `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`.
- 금지: 학습/평가, test 163/P1, subagent, repo 수정(지정 report만).
- Q1~Q6 + final STOP/NARROW/CONTINUE.
- `docs/hoplite/c5_f0_v1_3_review_2026-11-09/review_{MODEL}.md`
- reviewed HEAD + verbatim `paired E01−E11`.

## 1. v1.3 변경

- MDE: `.019170`은 F−L LoRA planning proxy; P−PA mean +3.0652/SE .6209/14 of 15/SD 2.405; realized CI governs; ±.0124 removed; .104 gate-only, .0876 analytic 50%.
- Expected branch: undetermined; PASS/ROUTE_STOP both live.
- T_proj 9 terms incl 20×5 step-100 eval; setup per-process/wave.
- Init: F0 E11 hash != Phase 6 L; I/O audit secondary; E00 assertion N/A.
- D1: literal schema, partial/crash, zero wrong-donor/donor-map loads, real-memory CE.
- Pre-R all-seed audit stage P, `pre_r_init_audit.json`.
- Byte grammar, test vectors, post-step0 capture.
- Group-specific weight change.
- Donor evaluated/expected count 5.
- nproc≥12; 4-vCPU host not qualifying.

## 2. 설계

E00 0 updates; E10 adapter; E01 LoRA64; E11 adapter+LoRA64; primary E01−E11; 15 length-eligible; PASS lower>.05 + E01 signal + 2/3 D_s.

## 3. 질문

Q1 Init/serialization/pre-R audit — 충분한가?
Q2 D1 literal schema/seal — 충분한가?
Q3 STOP/MDE proxy/P−PA — 정합하는가?
Q4 Cohort/donor count/LOO — 충분한가?
Q5 Compute 9-term/execution host — 충분한가?
Q6 Scope/route-only — 충분한가?

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
