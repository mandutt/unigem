# C5 F0 v1.2 — Review Request (New Block Round 2/10)

- 작성일: 2026-11-09
- 대상: `docs/plan_c5_f0_v1_2_2026-11-09.md`
- 이전: v1.1 = GLM CONTINUE / DS NARROW / Luna NARROW
- v1.1 스레드 archive 완료
- 미승인·미실행

## 0. Instructions

- 새 스레드 독립 검토; v1.1 결론 상속 금지.
- 파일: `docs/plan_c5_f0_v1_2_2026-11-09.md`, `docs/plan_c5_f0_v1_1_2026-11-09.md`, `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`.
- 금지: 학습/평가, test 163/P1, subagent, repo 수정(지정 report만).
- Q1~Q6 + final STOP/NARROW/CONTINUE.
- `docs/hoplite/c5_f0_v1_2_review_2026-11-09/review_{MODEL}.md`
- reviewed HEAD + verbatim `paired E01−E11`.

## 1. v1.2 변경

- MDE: paired SE .019170/half-width .037573; strict lower>.05 80% power mean ≈.104; observed boundary .0876; `.166/.216` removed.
- §6.5: EQUIVALENT mean ±.0124; ALL_FAIL→ROUTE_STOP more likely; 0.117 removed.
- Init: step_seed golden table with actual hex; tensor serialization; post-step0 weight change; all seeds.
- D1: canonical `f0_d1_mechanics.json`; no eval_arm_d1; no wrong-donor CE; labels_computed decision-only; filesystem asserts.
- t_proj_f0: setup once + 3× per-wave terms; slowest arm.
- Provenance: F0 driver commit/clean tree; code_commit/command/input SHA; Phase6 checkpoint I/O assert.
- Donor: donors_for(val20,cache), sha256, leave-one-donor-out.
- Labels: `f0_r_labels.json`; alias forbidden; n_boot=10000 assert.

## 2. 설계

| cell | adapter | LoRA | updates |
|---|---|---|---|
| E00 | none | none | 0 |
| E10 | trained | none | 100 |
| E01 | none | 64 | 100 |
| E11 | trained | 64 | 100 |

Primary E01 vs E11, 15 length-eligible docs, PASS lower>.05 + E01 signal + 2/3 D_s.

## 3. 질문

### Q1. Init
golden/serialization/post-step0/all-seed — 충분한가?

### Q2. D1
f0_d1 mechanics, literal allowlist, no wrong-donor CE, filesystem seal — 충분한가?

### Q3. STOP/MDE
.104/.0876, EQUIVALENT ±.0124, ALL_FAIL likely — 정합하는가?

### Q4. Cohort
15 length-eligible, 20 descriptive, donor map sha256/LOO — 충분한가?

### Q5. Compute
t_proj_f0 setup once + 3× terms, 96 min, nproc≥12 — 충분한가?

### Q6. Scope
route-only, descriptive no-inference, lost controls — 충분한가?

## 4. 답변

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거
- 다음 단계: 1~3개

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
