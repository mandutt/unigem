# C5 F0 v1.4 — Review Request (New Block Round 4/10)

- 대상: `docs/plan_c5_f0_v1_4_2026-11-09.md`
- 이전: v1.3 = **3/3 NARROW**
- v1.3 스레드 archive 완료
- 미승인·미실행

## 0. Instructions

- 새 스레드 독립 검토; v1.3 결론 상속 금지.
- 파일: `docs/plan_c5_f0_v1_4_2026-11-09.md`, `docs/plan_c5_f0_v1_3_2026-11-09.md`, `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`.
- 금지: 학습/평가, test 163/P1, subagent, repo 수정(지정 report만).
- Q1~Q6 + final STOP/NARROW/CONTINUE.
- `docs/hoplite/c5_f0_v1_4_review_2026-11-09/review_{MODEL}.md`
- reviewed HEAD + verbatim `paired E01−E11`.

## 1. v1.4 변경

- D1 schema: per-cell n_docs_step0/final, m_records, generation_records, ce_finite, assertions; stage-scoped §13 tree (D1 only d1 JSON; r/ R-only).
- Init: Phase 6 I/O audit authoritative; hash-inequality removed; stage P assertions 1–8; assertion 9 N/A; pre_r_init_audit_pass required before R.
- Expected branch: P−PA(+3.065,14/15) is PASS-direction context, not ROUTE_STOP.
- T_proj: 9 Phase 6 §11.5 terms per arm, setup_s_effective, wall anchor 4,939.884s.
- n_boot=10000 assertion, f0_labels alias ban, l_predicate forbidden, realized n_boot/seed.
- Serialization KAT fixture/delimiter/dtype whitelist.
- P−PA reference dispersion terminology; CI conditional on fixed donor graph.
- R-only timings measured/justified; nproc≥12; 4-vCPU no-run.

## 2. 설계

E00 0; E10 adapter; E01 LoRA64; E11 adapter+LoRA64; primary E01−E11; 15 length-eligible; PASS lower>.05 + E01 signal + 2/3 D_s.

## 3. 질문

Q1 Init/stage P/non-reuse — 충분한가?
Q2 D1 schema/§13 stage scope/seal — 충분한가?
Q3 STOP/MDE/reference dispersion — 정합하는가?
Q4 Cohort/donor CI conditional/LOO — 충분한가?
Q5 Compute 9-term/setup/execution host — 충분한가?
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
