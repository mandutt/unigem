# C5 F0 v0.9 — Independent Review Request

- 작성일: 2026-11-09
- 대상: `docs/plan_c5_f0_v0_9_2026-11-09.md` (DRAFT v0.9)
- 이전: v0.8 = 3/3 NARROW
- 이전 v0.8 검토 스레드 3개는 **archive 완료**
- 상태: **미승인·미실행**
- test 163: sealed
- P1: unused
- T5Gemma2: D-108 STOP
- **새 독립 검토 라운드**.

---

## 0. Reviewer Instructions

1. 새 스레드에서 독립 검토하라. v0.8 결론을 상속하지 말라.
2. 아래 파일을 직접 읽어라.
   - `docs/plan_c5_f0_v0_9_2026-11-09.md`
   - `docs/plan_c5_f0_v0_8_2026-11-09.md` (superseded)
   - `reports/C5_F0_V0_8_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_F0_V0_7_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`
   - `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`
   - `runner/c5_pm_phase6.py`
3. 학습·평가 실행 금지. test 163/P1 사용 금지. 서브에이전트/추가 LLM 금지.
4. repository 수정 금지. 지정 report 파일만 작성.
5. Q1~Q6 판정 + 근거 + 다음 단계.
6. 최종 판정 STOP / NARROW / CONTINUE.
7. 보고서 경로:
   `docs/hoplite/c5_f0_v0_9_review_2026-11-09/review_{MODEL}.md`
8. reviewed HEAD와 verbatim quote `paired E01−E11` 포함.

---

## 1. v0.9 변경

1. **Cap 통일**
   - 모든 R cap **120 min**; D1 25 min. 150 잔재 제거.
2. **EQUIVALENT 문장 모순 제거**
   - “No equality claim from CI contains 0” 삭제.
   - Practical equivalence only.
3. **MDE power**
   - 50% ≈.166; 80% ≈.216; .05 lower-bound gate; underpowered 명시.
4. **D1 exact schema/path**
   - `d1_mechanics.json` only; no `d1_sealed/`, `d1_report.json`, `per_doc`, `final`, phase7.
   - gate negative/invariance test.
5. **H3 out of scope** 유지.
6. **Donor/step_seed** all-cell equality, golden test.

## 2. 설계

| cell | memory | adapter | LoRA | updates |
|---|---|---|---|---|
| E00 | EG2 raw | none | none | 0 |
| E10 | EG2 raw | trained | none | 100 |
| E01 | EG2 raw | none | 64 | 100 |
| E11 | EG2 raw | trained | 64 | 100 |

- Primary E01 vs E11 matched LoRA init.
- PASS: `mean_D>0`, `CI_D.lower>.05`, E01 signal, 2/3 D_s.
- MDE .166/.216; STOP taxonomy exact.

## 3. 검토 질문

### Q1. Initialization

Per-step reseed, step_seed golden test, hashes, F0≠Phase6 L — 충분한가?

### Q2. D1 no-signal

D1이 signal/per_doc/phase7/final을 전혀 생성하지 않는가? exact schema/path와 negative test가 충분한가?

### Q3. STOP/MDE

EQUIVALENT 문장, PASS lower>.05, MDE .166/.216, reason enum이 정합하는가?

### Q4. Cohort/CI

15 common, 3/3 seed, 5 donors all cells, n_boot=10000, donor dependence, seed gate가 충분한가?

### Q5. Compute

T_proj 공식, D1 25/R 120, nproc≥12, 900 updates가 정합하는가?

### Q6. Scope

H3 out-of-scope와 F0 approval 경계가 충분한가?

## 4. 답변 형식

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거
- 다음 단계: 1~3개

최종 판정: STOP / NARROW / CONTINUE
Initialization:
D1 no-signal:
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
- test 163/P1 사용 금지
- repository 수정 금지 (지정 report만)
- subagent/추가 LLM 금지
- threshold/seed/donor/step/LR 변경 금지
- B0-B/B1/B2/Stage C 자동 진행 금지
