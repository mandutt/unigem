# C5 F0 v0.7 — Independent Review Request

- 작성일: 2026-11-09
- 대상: `docs/plan_c5_f0_v0_7_2026-11-09.md` (DRAFT v0.7)
- 이전: v0.6 = 3/3 NARROW
- 이전 v0.6 검토 스레드 3개는 **archive 완료**
- 상태: **미승인·미실행**
- test 163: sealed
- P1: unused
- T5Gemma2: D-108 STOP
- **새 독립 검토 라운드**. archive된 스레드의 후속이 아니며 중복 요청이 아님.

---

## 0. Reviewer Instructions

1. 새 스레드에서 독립 검토하라. 이전 v0.6 결론을 상속하지 말라.
2. 아래 파일을 직접 읽어라.
   - `docs/plan_c5_f0_v0_7_2026-11-09.md`
   - `docs/plan_c5_f0_v0_6_2026-11-09.md` (superseded)
   - `reports/C5_F0_V0_6_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_F0_V0_5_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`
   - `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`
   - `runner/c5_pm_phase6.py`
3. 학습·평가 실행 금지. test 163/P1 사용 금지. 서브에이전트/추가 LLM 금지.
4. repository 수정 금지. 지정 report 파일만 작성.
5. Q1~Q6에 판정 + 근거 + 다음 단계 1~3개.
6. 최종 판정은 STOP / NARROW / CONTINUE.
7. 보고서 경로:
   `docs/hoplite/c5_f0_v0_7_review_2026-11-09/review_{MODEL}.md`
8. reviewed HEAD와 verbatim quote `paired E01−E11`를 포함하라.

---

## 1. v0.7 변경

1. **PASS/EQUIVALENT 중복 제거**
   - `PASS_POSITIVE = mean_D>0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0`.
   - `.05` lower bound는 equivalence band 밖 practical effect.
   - `CI_D=[+.01,+.04]`는 EQUIVALENT이며 PASS 아님.
2. **ALL_FAIL fallback reason**
   - `ALL_FAIL` 항상 ROUTE_STOP.
   - reason priority `EQUIVALENT > harm > benefit > no_signal_direction_uncertain`.
   - CI straddle `[-.20,+.10]` → `no_signal_direction_uncertain`.
3. **Predicate 통일**
   - §0/§6.3/§7 동일 predicate.
4. **Seed gate**
   - 2/3 `D_s>0`는 PASS guard only; harm/benefit CI descriptor.
5. **H3 trigger**
   - PASS 또는 ROUTE_STOP harm/benefit; EQUIVALENT/uncertain STOP 이후 금지.

## 2. 설계

| cell | memory | adapter | LoRA | updates |
|---|---|---|---|---|
| E00 | EG2 raw | none | none | 0 |
| E10 | EG2 raw | trained | none | 100 |
| E01 | EG2 raw | none | 64 | 100 |
| E11 | EG2 raw | trained | 64 | 100 |

- Primary E01 vs E11, matched LoRA init.
- Primary final-checkpoint donor-crop, 15 common.
- `CI_D.lower > .05` + E01 signal + 2/3 D_s.
- STOP taxonomy exact.

## 3. 검토 질문

### Q1. Initialization audit

Per-step reseed, hashes, F0≠Phase6 L — 충분한가?

### Q2. D1 seal

Exact-key allowlist + denylist + sanitized partial + negative/invariance test가 충분한가?

### Q3. STOP taxonomy

PASS `lower>.05`가 EQUIVALENT와 겹치지 않는가? ALL_FAIL fallback reason과 H3 trigger가 정합하는가?

### Q4. Cohort/CI

15 common, doc 3/3 seed, n_donors=5, all-cell donor equality, n_boot=10000, seed gate가 충분한가?

### Q5. Compute

12 logical threads, D1 25min, R 150 provisional, T_proj/nproc≥12, 900 updates가 정합하는가?

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
