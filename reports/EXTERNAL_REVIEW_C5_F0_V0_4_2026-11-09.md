# C5 F0 v0.4 — Independent Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `v0.4 local commit`
- 대상: `docs/plan_c5_f0_v0_4_2026-11-09.md` (DRAFT v0.4)
- 이전: v0.3 = GLM CONTINUE / DeepSeek NARROW / Luna NARROW
- 이전 v0.3 검토 스레드 3개는 **archive 완료**
- 상태: **미승인·미실행**
- test 163: sealed
- P1: unused
- T5Gemma2: D-108 STOP
- **새 독립 검토 라운드**. archive된 스레드의 후속이 아니며 중복 요청이 아님.

---

## 0. Reviewer Instructions

1. 새 스레드에서 독립 검토하라. 이전 v0.3 결론을 상속하지 말라.
2. 아래 파일을 직접 읽어라.
   - `docs/plan_c5_f0_v0_4_2026-11-09.md`
   - `docs/plan_c5_f0_v0_3_2026-11-09.md` (superseded)
   - `reports/C5_F0_V0_3_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_F0_V0_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`
   - `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`
   - `runner/c5_pm_phase6.py`
3. 학습·평가 실행 금지. test 163/P1 사용 금지. 서브에이전트/추가 LLM 금지.
4. repository 수정 금지. 지정 report 파일만 작성.
5. Q1~Q6에 판정 + 근거 + 다음 단계 1~3개.
6. 최종 판정은 STOP / NARROW / CONTINUE.
7. 보고서 경로:
   `docs/hoplite/c5_f0_v0_4_review_2026-11-09/review_{MODEL}.md`
8. reviewed HEAD와 verbatim quote `paired E01−E11`를 포함하라.

---

## 1. v0.4 변경

v0.3 must-fix 반영:

1. **Compute 회계**
   - F0 D1/R = 4 arms × 3 threads/arm = **12 logical threads**.
   - Phase 6 D1 실측 1,180.6s parallel / 3,116.5s sequential.
   - F0 전용 `c5_pm_f0_parallel.py`가 `wall_estimate_s`/`parallel_arms`/`cap_ok` 생성.
   - 기존 sequential `run_d1`은 F0 gate에 사용하지 않음.
2. **D1 seal**
   - D1 `mechanics_only`; signal은 `d1_sealed/` + sha256.
   - decision input allowlist는 `d1_mechanics.json`만.
3. **STOP taxonomy**
   - `NOT_EVALUABLE` / `PASS_POSITIVE` / `ROUTE_STOP` / `INDETERMINATE`.
   - `FAIL(c,e)=NOT SIGNAL(c,e)`; 3/3 seeds 문구 제거.
   - `E01≈E11` + both fail → ROUTE_STOP; CI upper<0 → harm.
4. **Cohort binding**
   - 15 common = frozen `common_ids`; all present in `unit.final.per_doc` every cell×seed.
   - missing → NOT_EVALUABLE.
5. **Init audit**
   - E01/E11 LoRA hash, E10/E11 adapter hash, lora_names 64, lora_A/B zero-init, post-init RNG hash.
   - F0 E11 ≠ Phase 6 L at init.
6. **RNG scope**
   - LoRA fixed = init only; dropout training stream diverges.
7. **H3**
   - frozen LN/projection, train20 only, residual identity metric, trigger.
8. **D0 timing**
   - `elapsed_s`/`phase_timings`.

## 2. 설계

| cell | memory | adapter | decoder LoRA | updates |
|---|---|---|---|---|
| E00 | EG2 raw 753×512 | none | none | 0 |
| E10 | EG2 raw | trained | none | 100 |
| E01 (F0) | EG2 raw | none | 64 modules | 100 |
| E11 (L) | EG2 raw | trained | 64 modules | 100 |

- Primary: E01 vs E11 with matched LoRA initialization.
- Primary source: final-checkpoint donor-crop, 15 frozen common docs.
- Primary: paired `CI_D.lower >0` AND `SIGNAL(E01,copy)`.
- `E01≈E11`: CI contains 0 AND |mean_D|<.05.
- STOP taxonomy exact; no 15→14.
- Stage R 3 seeds after D0/D1 mechanics only.

## 3. 검토 질문

### Q1. Initialization audit

F0-only seed reset, lora_names equality, LoRA/A/B hash, adapter hash, post-init RNG hash, F0≠Phase6 L — 충분한가? `LoRA fixed`를 init-only로 한정한 것이 정확한가?

### Q2. D1 seal

D1 `mechanics_only` + sealed signal + decision input allowlist가 재량 게이트를 기계적으로 막는가? 우회 경로는 무엇인가?

### Q3. STOP taxonomy

4-state priority table이 상호배타·전체 포괄인가? `PASS_POSITIVE`에 E01 cell signal을 요구한 것이 타당한가?

### Q4. Cohort/CI

15 common frozen binding, doc-level CI + seed-level descriptor, missing→NOT_EVALUABLE이 충분한가?

### Q5. Compute

12 logical threads, D1 25min, R 120min, 900 updates가 Phase 6 실측과 정합하는가? F0 전용 병렬 오케스트레이터가 필요한가?

### Q6. H3

H3 발동 조건, frozen LN/projection, residual identity 판정식이 충분한가?

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
