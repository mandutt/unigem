# C5 F0 v1.10 — Review Request (New Block Round 10/10, final)

- 대상: `docs/plan_c5_f0_v1_10_2026-11-09.md`
- 이전: v1.9 = **3/3 NARROW**
- v1.9 스레드 archive 완료
- 미승인·미실행
- **새 10라운드 블록의 마지막 라운드**

## 0. Instructions

- 새 스레드 독립 검토; v1.9 결론 상속 금지.
- 파일: `docs/plan_c5_f0_v1_10_2026-11-09.md`, `docs/plan_c5_f0_v1_9_2026-11-09.md`, `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`.
- 금지: 학습/평가, test 163/P1, subagent, repo 수정(지정 report만).
- Q1~Q6 + final STOP/NARROW/CONTINUE.
- `docs/hoplite/c5_f0_v1_10_review_2026-11-09/review_{MODEL}.md`
- reviewed HEAD + verbatim `paired E01−E11`.

## 1. v1.10 변경

- D1 CE operation table frozen before D1; independent instrumented expected count, no post-hoc.
- P/Q/R pre-update hash proof per seed/cell; fail closed.
- R mechanics full expected counts/formula.
- F0 allowlist-first loader; transitive test163/P1/out-of-allowlist tests.
- D1 M/generation count-only at source, logs/crash/temp tests, >25 min hard abort + new code SHA/re-approval.
- CPU set/quota/all thread pools recorded.
- near-threshold signed margins m_mean/m_lower/m_sign, D_s frozen, non-decisional.
- Materialization wording corrected.
- D1 3 threads/arm measured, registered 2 threads/arm measured; neither F0.
- EQUIVALENT `SE_D <= .0255`.
- Plan §15 Q1-Q6 rewritten.

## 2. 설계

E00 0; E10 adapter; E01 LoRA64; E11 adapter+LoRA64; primary E01−E11; 15 length-eligible; PASS lower>.05 + E01 signal + 2/3 D_s.

## 3. 질문

Q1 CE count/schema/hash — 충분한가?
Q2 D1 materialization/seal/overrun — 충분한가?
Q3 R mechanics/gates — 충분한가?
Q4 Cohort/CI/STOP/near-threshold — 정합하는가?
Q5 Compute/scope — 충분한가?
Q6 Route/limitations — 충분한가?

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
