# C5 F0 v1.1 — Independent Review Request (New Block Round 1/10)

- 작성일: 2026-11-09
- 대상: `docs/plan_c5_f0_v1_1_2026-11-09.md` (DRAFT v1.1)
- 이전: v1.0 = GLM CONTINUE / DS NARROW / Luna NARROW
- 이전 v1.0 스레드 3개 **archive 완료**
- 상태: **미승인·미실행**
- 새 10라운드 블록의 1번째.

## 0. Reviewer Instructions

1. 새 스레드 독립 검토. v1.0 결론 상속 금지.
2. 파일:
   - `docs/plan_c5_f0_v1_1_2026-11-09.md`
   - `docs/plan_c5_f0_v1_0_2026-11-09.md` (superseded)
   - `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`
   - `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`
   - `runner/c5_pm_phase6.py`
3. 금지: 학습/평가, test 163/P1, subagent, repository 수정(지정 report만).
4. Q1~Q6 + 최종 STOP/NARROW/CONTINUE.
5. `docs/hoplite/c5_f0_v1_1_review_2026-11-09/review_{MODEL}.md`
6. reviewed HEAD + verbatim `paired E01−E11`.

## 1. v1.1 변경

1. **D1 artifact contract**
   - separate `eval_mechanics_only`; no `eval_arm_d1`.
   - checkpoint digest then delete; no "3 exist".
   - literal allowlist + writer assert + phase7/checkpoint filesystem assert.
   - D1 output counts only; no signal/delta/per_doc.
2. **Cohort estimand**
   - primary = 15 length-eligible docs + fixed donor graph.
   - 20-doc F/L descriptive only; no population generalization.
   - donor-cluster sensitivity.
3. **MDE**
   - paired half-width .037573, SE .019170; 80% MDE .054; PASS mean .0876.
4. **Provenance**
   - F0 driver commit SHA/clean tree before D0; code_commit/command/input SHA in artifacts.
5. **Init**
   - step_seed golden; tensor/RNG serialization; post-step0 weight non-equality; all seeds.
6. **n_boot**
   - direct n_boot=10000; assert; forbid l_predicate.
7. **T_proj**
   - separate `t_proj_f0`; setup once; contention ratio.
8. **Scope**
   - ROUTE_STOP route-only; descriptive no-inference; dropped 1-seed/null recorded; explicit D0/D1/R approvals.

## 2. 설계

| cell | adapter | LoRA | updates |
|---|---|---|---|
| E00 | none | none | 0 |
| E10 | trained | none | 100 |
| E01 | none | 64 | 100 |
| E11 | trained | 64 | 100 |

- Primary E01 vs E11; 15 common; PASS `CI_D.lower>.05` + E01 signal + 2/3 D_s.
- STOP taxonomy exact; H3 out.

## 3. 질문

### Q1. Init
step_seed golden/serialization/all-seed assertions — 충분한가?

### Q2. D1
separate mechanics evaluator, digest-delete, literal allowlist, phase7/checkpoint asserts — 충분한가?

### Q3. STOP/MDE
paired-SE MDE .054/.0876, PASS .05, reason enum — 정합하는가?

### Q4. Cohort
15 length-eligible estimand, 20-doc descriptive, donor-cluster sensitivity — 충분한가?

### Q5. Compute
t_proj_f0, 96 min, nproc≥12, contention — 충분한가?

### Q6. Scope
ROUTE_STOP route-only, descriptive no-inference, lost controls — 충분한가?

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

## 5. 금지

- 승인 전 실행, test 163/P1, repo 수정, subagent, threshold/seed/donor/step/LR 변경, B0-B/B1/B2/Stage C.
