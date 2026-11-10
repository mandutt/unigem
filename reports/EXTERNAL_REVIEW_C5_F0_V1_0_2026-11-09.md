# C5 F0 v1.0 — Final Review Request (Round 10)

- 작성일: 2026-11-09
- 대상: `docs/plan_c5_f0_v1_0_2026-11-09.md` (DRAFT v1.0)
- 이전: v0.9 = 3/3 NARROW
- 이전 v0.9 스레드 3개는 **archive 완료**
- 상태: **미승인·미실행**
- **10번째 최종 검토 라운드**; 이후 새 라운드 없이 결과 보고/중지.

---

## 0. Reviewer Instructions

1. 새 스레드에서 독립 검토. v0.9 결론 상속 금지.
2. 파일:
   - `docs/plan_c5_f0_v1_0_2026-11-09.md`
   - `docs/plan_c5_f0_v0_9_2026-11-09.md` (superseded)
   - `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_F0_V0_8_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`
   - `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`
   - `runner/c5_pm_phase6.py`
3. 학습·평가 실행 금지. test 163/P1 금지. subagent/추가 LLM 금지.
4. repository 수정 금지; 지정 report만.
5. Q1~Q6 판정 + 근거 + 다음 단계.
6. 최종 STOP / NARROW / CONTINUE.
7. `docs/hoplite/c5_f0_v1_0_review_2026-11-09/review_{MODEL}.md`
8. reviewed HEAD + verbatim `paired E01−E11`.

## 1. v1.0 변경

- Title `Single-Contrast Diagnostic`; association-only.
- T_proj Phase6 §11.5 term set; R **96 min**; nproc<12 abort; contention_ratio.
- D1 checkpoint digest-only/load 금지; literal allowlist.
- n_boot 10000 explicit override.
- step_seed golden/hash; base/cache/label freeze hashes.
- donor all cells; per-doc n_donors=5.
- MDE .166/.216 approximation; realized CI-D half-width.
- lost MF-4 null/1-seed gate 명시.
- D0/D1/R stage approval.

## 2. 설계

| cell | memory | adapter | LoRA | updates |
|---|---|---|---|---|
| E00 | EG2 raw | none | none | 0 |
| E10 | EG2 raw | trained | none | 100 |
| E01 | EG2 raw | none | 64 | 100 |
| E11 | EG2 raw | trained | 64 | 100 |

- Primary E01 vs E11 matched LoRA init.
- PASS: mean_D>0, CI_D.lower>.05, E01 signal, 2/3 D_s.
- 15 common, 5 donors, 3 seeds, n_boot 10000.
- STOP taxonomy exact; H3 out.

## 3. 질문

### Q1. Initialization
step_seed golden, hashes, F0≠Phase6 L — 충분한가?

### Q2. D1
literal allowlist, digest-only checkpoint, load 금지, phase7 0 — 충분한가?

### Q3. STOP/MDE
PASS .05, reason enum, MDE .166/.216, realized CI — 정합하는가?

### Q4. Cohort/CI
15 common, 3/3, 5 donors all cells, n_boot 10000, donor dependence — 충분한가?

### Q5. Compute
T_proj full term set, R 96, nproc≥12, 900 updates — 정합하는가?

### Q6. Scope
Single-contrast title, association-only, H3 out, lost controls — 충분한가?

## 4. 답변

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거
- 다음 단계: 1~3개

최종 판정: STOP / NARROW / CONTINUE
Initialization:
D1:
STOP/MDE:
Cohort/CI:
Compute:
Scope:
Must-fix (ranked):
잘못된 전제:
```

## 5. 금지

- 승인 전 F0 실행 금지
- 학습·평가 실행 금지
- test 163/P1 금지
- repository 수정 금지
- subagent/추가 LLM 금지
- threshold/seed/donor/step/LR 변경 금지
- B0-B/B1/B2/Stage C 자동 진행 금지
