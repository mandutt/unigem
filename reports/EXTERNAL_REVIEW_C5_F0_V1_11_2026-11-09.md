# C5 F0 v1.11 — Review Request (New Block Round 1/10)

- 대상: `docs/plan_c5_f0_v1_11_2026-11-09.md`
- 이전: v1.10 = GLM CONTINUE / DS NARROW / Luna NARROW
- v1.10 스레드 archive 완료
- 미승인·미실행

## 0. Instructions

- 새 스레드 독립 검토; v1.10 결론 상속 금지.
- 파일: `docs/plan_c5_f0_v1_11_2026-11-09.md`, `docs/plan_c5_f0_v1_10_2026-11-09.md`, `reports/C5_F0_BLOCK2_3AI_REVIEW_SYNTHESIS_2026-11-10.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`.
- 금지: 학습/평가, test 163/P1, subagent, repo 수정(지정 report만).
- Q1~Q6 + final STOP/NARROW/CONTINUE.
- `docs/hoplite/c5_f0_v1_11_review_2026-11-09/review_{MODEL}.md`
- reviewed HEAD + verbatim `paired E01−E11`.

## 1. v1.11 변경

- CPU affinity/quota/thread-pool fields in parallel schema.
- `r/f0_replay.json` removed.
- Q first wrong-donor execution (finiteness/shape only); R first persisted/aggregated; Q count field.
- crash error enum; no CE values in strings/logs.
- D1 donor_count metadata vs runtime donor_map_loads separated.
- overrun single hard rule; 4,939.884s D-157 2-thread measured, not F0.
- R donor_map_sha256 + per-doc donor hash.
- near-threshold b∈{+0.05,0}; EQUIVALENT nominal.
- D1 custody exact inventory.

## 2. 설계

E00 0; E10 adapter; E01 LoRA64; E11 adapter+LoRA64; primary E01−E11; 15 length-eligible; PASS lower>.05 + E01 signal + 2/3 D_s.

## 3. 질문

Q1 CPU/D1 custody — 충분한가?
Q2 wrong-donor/error enum — 충분한가?
Q3 donor-count/overrun/provenance — 정합하는가?
Q4 near-threshold/EQUIVALENT — 정합하는가?
Q5 R donor identity/hash — 충분한가?
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
