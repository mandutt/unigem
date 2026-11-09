# C5 F0 v0.5 — Independent Review Request

- 작성일: 2026-11-09
- 대상: `docs/plan_c5_f0_v0_5_2026-11-09.md` (DRAFT v0.5)
- 이전: v0.4 = GLM CONTINUE / DeepSeek NARROW / Luna NARROW
- 이전 v0.4 검토 스레드 3개는 **archive 완료**
- 상태: **미승인·미실행**
- test 163: sealed
- P1: unused
- T5Gemma2: D-108 STOP
- **새 독립 검토 라운드**. archive된 스레드의 후속이 아니며 중복 요청이 아님.

---

## 0. Reviewer Instructions

1. 새 스레드에서 독립 검토하라. 이전 v0.4 결론을 상속하지 말라.
2. 아래 파일을 직접 읽어라.
   - `docs/plan_c5_f0_v0_5_2026-11-09.md`
   - `docs/plan_c5_f0_v0_4_2026-11-09.md` (superseded)
   - `reports/C5_F0_V0_4_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_F0_V0_3_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`
   - `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`
   - `runner/c5_pm_phase6.py`
3. 학습·평가 실행 금지. test 163/P1 사용 금지. 서브에이전트/추가 LLM 금지.
4. repository 수정 금지. 지정 report 파일만 작성.
5. Q1~Q6에 판정 + 근거 + 다음 단계 1~3개.
6. 최종 판정은 STOP / NARROW / CONTINUE.
7. 보고서 경로:
   `docs/hoplite/c5_f0_v0_5_review_2026-11-09/review_{MODEL}.md`
8. reviewed HEAD와 verbatim quote `paired E01−E11`를 포함하라.

---

## 1. v0.5 변경

v0.4 must-fix 반영:

1. **ROUTE_STOP 부호·granularity**
   - `ALL_FAIL = FAIL(E01,copy) ∧ FAIL(E01,full) ∧ FAIL(E11,copy) ∧ FAIL(E11,full)`.
   - E00/E10 제외.
   - `harm = CI_D.lower>0` (E01 우세; adapter hurts).
   - `benefit = CI_D.upper<0` (E11 우세).
   - STOP = ALL_FAIL AND (harm OR EQUIVALENT).
2. **Equivalence**
   - `EQUIVALENT = 95% CI_D within [-.05,+.05]`.
   - `E01≈E11` descriptive only.
3. **PASS_POSITIVE**
   - `CI_D.lower>0 AND SIGNAL(E01,copy)`.
4. **D1 seal**
   - denylist for `delta_*`/`per_doc`/`final`/`step0` in mechanics/logs/partial.
   - negative test; state_dict-only checkpoints.
5. **Cohort**
   - 15 docs ×3 seeds; n_donors=5; E01/E11 donor set identical.
6. **RNG**
   - post-step0 RNG hash E01==E11; LoRA fixed=init only.
7. **Compute**
   - R cap 150 min; basis 4,939.88s ×1.316≈6,500s; nproc/threads/contention.
8. **H3**
   - QR seed/rank/hash, identity thresholds, CI-excluding-0 trigger.

## 2. 설계

| cell | memory | adapter | decoder LoRA | updates |
|---|---|---|---|---|
| E00 | EG2 raw 753×512 | none | none | 0 |
| E10 | EG2 raw | trained | none | 100 |
| E01 (F0) | EG2 raw | none | 64 modules | 100 |
| E11 (L) | EG2 raw | trained | 64 modules | 100 |

- Primary: E01 vs E11 matched LoRA init.
- Primary source: final-checkpoint donor-crop, 15 frozen common docs.
- Primary: paired `CI_D.lower>0` AND `SIGNAL(E01,copy)`.
- `EQUIVALENT`: 95% CI within ±.05.
- STOP taxonomy exact; no 15→14.

## 3. 검토 질문

### Q1. Initialization audit

F0-only seed reset, lora_names equality, LoRA/A/B hash, adapter hash, post-init and post-step0 RNG hash, F0≠Phase6 L — 충분한가?

### Q2. D1 seal

D1 `mechanics_only` + sealed signal + decision input allowlist + denylist + negative test가 재량 게이트를 충분히 막는가? 남는 우회 경로는 무엇인가?

### Q3. STOP taxonomy

4-state priority table이 상호배타·전체 포괄인가? harm/benefit 부호, EQUIVALENT 95% CI, PASS_POSITIVE E01 signal guard가 타당한가?

### Q4. Cohort/CI

15 common frozen binding, doc 3/3 seed, n_donors=5, donor set equality, missing→NOT_EVALUABLE이 충분한가?

### Q5. Compute

12 logical threads, D1 25min, R 150min, 900 updates가 Phase 6 실측과 정합하는가?

### Q6. H3

H3 trigger, QR projection spec, identity threshold가 충분한가?

## 4. 답변 형식

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거
- 다음 단계: 1~3개

최종 판정: STOP / NARROW / CONTINUE
Initialization:
D1 seal:
STOP taxonomy:
Cohort/CI:
Compute:
H3:
Must-fix (ranked):
잘못된 전제:
```

## 5. 금지

- 승인 전 F0 실행 금지
- 학습·평가 실행 금지 (review 단계)
- test 163/P1 사용 금지
- repository 수정 금지 (지정 report만)
- subagent/추가 LLM 금지
- threshold/seed/donor/step/LR 변경 금지
- B0-B/B1/B2/Stage C 자동 진행 금지
- Phase 6 결과 재해석으로 B0-B 구제 금지
