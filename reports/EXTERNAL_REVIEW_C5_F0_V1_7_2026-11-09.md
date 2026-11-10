# C5 F0 v1.7 — Review Request (New Block Round 7/10)

- 대상: `docs/plan_c5_f0_v1_7_2026-11-09.md`
- 이전: v1.6 = GLM CONTINUE / DS NARROW / Luna NARROW
- v1.6 스레드 archive 완료
- 미승인·미실행

## 0. Instructions

- 새 스레드 독립 검토; v1.6 결론 상속 금지.
- 파일: `docs/plan_c5_f0_v1_7_2026-11-09.md`, `docs/plan_c5_f0_v1_6_2026-11-09.md`, `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`.
- 금지: 학습/평가, test 163/P1, subagent, repo 수정(지정 report만).
- Q1~Q6 + final STOP/NARROW/CONTINUE.
- `docs/hoplite/c5_f0_v1_7_review_2026-11-09/review_{MODEL}.md`
- reviewed HEAD + verbatim `paired E01−E11`.

## 1. v1.7 변경

- Q failure → NOT_EVALUABLE, all-3-seed requirement; no 2-seed continuation.
- Thread contract: 16 cores, 1 thread/arm, 4 workers; nproc>=16 only.
- 1,180.6s and 4,939.884s are estimates; final cap measured `parallel_wall_s`; anchor 3/arm.
- Q donor-crop/wrong-donor finiteness/shape; no per-doc/delta; D1 wrong_donor 0.
- Near-threshold b∈{.05,0}, h=(upper-lower)/2; near if |mean-b|≤h.
- cells_ok/updates_total_ok/e00_steps_zero predicates.
- common_ids_sha256; data-scope/manifest single-writer.
- harm/benefit non-exclusive with PASS.

## 2. 설계

E00 0; E10 adapter; E01 LoRA64; E11 adapter+LoRA64; primary E01−E11; 15 length-eligible; PASS lower>.05 + E01 signal + 2/3 D_s.

## 3. 질문

Q1 Q gate/3 seeds/init manifest — 충분한가?
Q2 D1 predicates/seal/telemetry — 충분한가?
Q3 STOP/MDE/near-threshold/harm-benefit — 정합하는가?
Q4 Cohort/cell CI/donor conditional — 충분한가?
Q5 Compute 16-core/1-thread/estimate provenance — 충분한가?
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
