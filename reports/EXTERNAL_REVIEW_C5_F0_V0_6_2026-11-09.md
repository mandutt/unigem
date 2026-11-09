# C5 F0 v0.6 — Independent Review Request

- 작성일: 2026-11-09
- 대상: `docs/plan_c5_f0_v0_6_2026-11-09.md` (DRAFT v0.6)
- 이전: v0.5 = 3/3 NARROW
- 이전 v0.5 검토 스레드 3개는 **archive 완료**
- 상태: **미승인·미실행**
- test 163: sealed
- P1: unused
- T5Gemma2: D-108 STOP
- **새 독립 검토 라운드**. archive된 스레드의 후속이 아니며 중복 요청이 아님.

---

## 0. Reviewer Instructions

1. 새 스레드에서 독립 검토하라. 이전 v0.5 결론을 상속하지 말라.
2. 아래 파일을 직접 읽어라.
   - `docs/plan_c5_f0_v0_6_2026-11-09.md`
   - `docs/plan_c5_f0_v0_5_2026-11-09.md` (superseded)
   - `reports/C5_F0_V0_5_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_F0_V0_4_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`
   - `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`
   - `runner/c5_pm_phase6.py`
3. 학습·평가 실행 금지. test 163/P1 사용 금지. 서브에이전트/추가 LLM 금지.
4. repository 수정 금지. 지정 report 파일만 작성.
5. Q1~Q6에 판정 + 근거 + 다음 단계 1~3개.
6. 최종 판정은 STOP / NARROW / CONTINUE.
7. 보고서 경로:
   `docs/hoplite/c5_f0_v0_6_review_2026-11-09/review_{MODEL}.md`
8. reviewed HEAD와 verbatim quote `paired E01−E11`를 포함하라.

---

## 1. v0.6 변경

v0.5 must-fix 반영:

1. **EQUIVALENT priority**
   - `EQUIVALENT` = 95% CI within [-.05,+.05].
   - `harm = lower>0 AND NOT EQUIVALENT`; `benefit = upper<0 AND NOT EQUIVALENT`.
   - reason precedence `EQUIVALENT > harm > benefit`.
2. **ALL_FAIL+benefit**
   - ALL_FAIL이면 방향과 무관하게 ROUTE_STOP; reason benefit 가능.
   - INDETERMINATE는 ALL_FAIL이 아닌 경우만.
3. **Seed variance gate**
   - PASS_POSITIVE = CI_D.lower>0 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0.
   - n_boot 10000.
4. **D1 schema**
   - scalar `n_docs_step0`/`n_docs_final`; exact-key allowlist.
   - denylist raw final/step0/per_doc/delta; sanitized partial; negative/invariance test.
5. **Init audit**
   - per-step RNG reseed; base/cache/label hashes; canonical digest/capture point.
6. **Compute**
   - R cap 150 provisional; T_proj primary; nproc≥12; no 1.316.
7. **H3**
   - rank r<512, H3_PROJ_SEED, zero-init mandatory, permuted null + donor discrimination.
8. **Cohort**
   - 15×3, n_donors=5, all-cell donor set equality.

## 2. 설계

| cell | memory | adapter | decoder LoRA | updates |
|---|---|---|---|---|
| E00 | EG2 raw | none | none | 0 |
| E10 | EG2 raw | trained | none | 100 |
| E01 (F0) | EG2 raw | none | 64 modules | 100 |
| E11 (L) | EG2 raw | trained | 64 modules | 100 |

- Primary E01 vs E11, matched LoRA init.
- Primary source final-checkpoint donor-crop, 15 frozen common.
- Primary paired CI + E01 signal + 2/3 seed sign.
- STOP taxonomy exact; no 15→14.

## 3. 검토 질문

### Q1. Initialization audit

Per-step reseed, lora_names/hash, adapter hash, post-init/post-step0 RNG, base/cache/label hashes, F0≠Phase6 L — 충분한가?

### Q2. D1 seal

Exact-key allowlist + denylist + sanitized partial + negative/invariance test가 재량 게이트를 충분히 막는가? 남는 우회 경로는?

### Q3. STOP taxonomy

4-state table이 상호배타·전체 포괄인가? ALL_FAIL이면 benefit도 ROUTE_STOP으로 보내는 것이 타당한가? EQUIVALENT precedence와 2/3 seed gate가 정합하는가?

### Q4. Cohort/CI

15 common, doc 3/3 seed, n_donors=5, all-cell donor equality, n_boot=10000, doc CI + seed gate가 충분한가?

### Q5. Compute

12 logical threads, D1 25min, R 150 provisional, T_proj/nproc≥12, 900 updates가 정합하는가? Orchestrator commit이 선행 조건인가?

### Q6. H3

Trigger, rank r<512, zero-init, identity threshold, permuted null/donor discrimination이 충분한가?

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
