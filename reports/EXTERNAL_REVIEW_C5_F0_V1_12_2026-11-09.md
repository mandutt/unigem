# C5 F0 v1.12 — Review Request (Block 3 Round 2/10)

- 대상: `docs/plan_c5_f0_v1_12_2026-11-09.md`
- 이전: v1.11 = **3/3 NARROW**
- v1.11 스레드 archive 완료
- 미승인·미실행

## 0. Instructions

- 새 스레드 독립 검토; v1.11 결론 상속 금지.
- 파일: `docs/plan_c5_f0_v1_12_2026-11-09.md`, `docs/plan_c5_f0_v1_11_2026-11-09.md`, `reports/C5_F0_BLOCK2_3AI_REVIEW_SYNTHESIS_2026-11-10.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`.
- 금지: 학습/평가, test 163/P1, subagent, repo 수정(지정 report만).
- Q1~Q6 + final STOP/NARROW/CONTINUE.
- `docs/hoplite/c5_f0_v1_12_review_2026-11-09/review_{MODEL}.md`
- reviewed HEAD + verbatim `paired E01−E11`.

## 1. v1.12 변경

- 13A.5 donor-count assertion R-only; D1 no donor-map load.
- overrun single rule: >25 min hard abort, partial, new code SHA/re-approval.
- 4,939.884s = D-157 2-thread measured, not F0.
- Q schema `wrong_donor_ce_calls`.
- R CPU fields, donor hash, expected counts.
- D1 custody allowed-delta/inventory/logs.
- m_b and m_sign separated; b∈{+0.05,0}.
- .0255 nominal only; realized CI governs.

## 2. 설계

E00 0; E10 adapter; E01 LoRA64; E11 adapter+LoRA64; primary E01−E11; 15 length-eligible; PASS lower>.05 + E01 signal + 2/3 D_s.

## 3. 질문

Q1 donor-count/D1 custody — 충분한가?
Q2 overrun/provenance — 정합하는가?
Q3 Q/R schema/counts — 충분한가?
Q4 near-threshold/.0255 — 정합하는가?
Q5 R donor hash/CPU — 충분한가?
Q6 scope/route — 충분한가?

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
