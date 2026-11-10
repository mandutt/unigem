# C5 F0 v1.5 — Review Request (New Block Round 5/10)

- 대상: `docs/plan_c5_f0_v1_5_2026-11-09.md`
- 이전: v1.4 = GLM CONTINUE / DS NARROW / Luna NARROW
- v1.4 스레드 archive 완료
- 미승인·미실행

## 0. Instructions

- 새 스레드 독립 검토; v1.4 결론 상속 금지.
- 파일: `docs/plan_c5_f0_v1_5_2026-11-09.md`, `docs/plan_c5_f0_v1_4_2026-11-09.md`, `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`.
- 금지: 학습/평가, test 163/P1, subagent, repo 수정(지정 report만).
- Q1~Q6 + final STOP/NARROW/CONTINUE.
- `docs/hoplite/c5_f0_v1_5_review_2026-11-09/review_{MODEL}.md`
- reviewed HEAD + verbatim `paired E01−E11`.

## 1. v1.5 변경

- Stage P init-only (assertions 1–4,6–8; no 5/9/13A.3); post-step0 only D1.
- Cell-level SIGNAL CI fully specified (15×5, seed mean, n_boot 10000, seed 20261109, percentile linear).
- D1 full schema flags/assertions; mechanics_pass predicate; success/partial values; allowlists/filesystem/negative tests.
- Wrong-donor CE not run in D1; R-first risk accepted; donors_for unit test.
- nproc≥16 or threads_per_arm≤1; cap from contention.
- d0/init_hashes.json + r/init_hashes.json; Phase6 protected-path I/O audit/negative read/clean-tree SHA.
- MDE labels: SE .019170, 50% .0376, 80% .0537, gate mean .104, 50% boundary .0876.
- step_seed parentheses; setup_s_effective total 3 waves×4 procs.

## 2. 설계

E00 0; E10 adapter; E01 LoRA64; E11 adapter+LoRA64; primary E01−E11; 15 length-eligible; PASS lower>.05 + E01 signal + 2/3 D_s.

## 3. 질문

Q1 Stage P/init/step_seed — 충분한가?
Q2 D1 full schema/signal path/seal — 충분한가?
Q3 STOP/MDE labels — 정합하는가?
Q4 Cohort/cell CI/donor conditional — 충분한가?
Q5 Compute nproc/setup/T_proj — 충분한가?
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
