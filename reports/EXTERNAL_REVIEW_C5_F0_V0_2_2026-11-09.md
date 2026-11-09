# C5 F0 v0.2 — Independent Re-Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `244b25c` + local v0.2 commit
- 대상: `docs/plan_c5_f0_v0_2_2026-11-09.md` (DRAFT v0.2)
- 이전: F0 v0.1 3/3 NARROW (`reports/C5_F0_DRAFT_3AI_REVIEW_SYNTHESIS_2026-11-09.md`)
- 상태: **미승인·미실행**
- test 163: sealed
- P1: unused
- T5Gemma2: D-108 STOP
- **새 독립 검토 라운드**. v0.1 스레드의 후속이 아니며 중복 요청이 아님.

---

## 0. Reviewer Instructions

1. 새 스레드에서 독립 검토하라. v0.1 결론을 상속하지 말라.
2. 아래 파일을 직접 읽어라.
   - `docs/plan_c5_f0_v0_2_2026-11-09.md`
   - `docs/plan_c5_f0_2026-11-09.md` (v0.1, superseded)
   - `reports/C5_F0_DRAFT_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`
   - `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`
   - `runner/c5_pm_phase6.py`
3. 학습·평가 실행 금지. test 163/P1 사용 금지. 서브에이전트/추가 LLM 금지.
4. repository 수정 금지. 지정 report 파일만 작성.
5. Q1~Q6에 판정 + 근거 + 다음 단계 1~3개.
6. 최종 판정은 STOP / NARROW / CONTINUE.
7. 보고서 경로:
   `docs/hoplite/c5_f0_v0_2_review_2026-11-09/review_{MODEL}.md`
8. reviewed HEAD와 verbatim quote `mechanics-only`를 포함하라.

---

## 1. v0.2 변경

v0.1 review must-fix 반영:

1. **Stage D = D0/D1 mechanics-only**
   - v0.1: 1-seed 100-update 결과로 Stage R/track STOP 결정.
   - v0.2: D0 0-update + D1 1-update; signal gate 없음.
2. **Stage R = 3 seeds 기본**
   - 1-seed selection gate 제거.
   - D0/D1 mechanics pass 후 항상 3 seeds.
3. **track STOP 삭제/한정**
   - F0 negative는 EG2 전체 track STOP의 충분조건이 아니다.
   - 최대 “EG2-raw→mT5-decoder route as configured”만 STOP.
4. **E00/E10 해석 한정**
   - E00 eval-only baseline; trained control 아님.
   - E01 vs E11만 primary causal contrast.
5. **H3 분리**
   - LN/projection/residual은 별도 prereg.
6. **F0 코드 미구현 명시**
   - `arm_spec` F/L/P/PA만 지원; F0 arms 별도.

## 2. 설계

| cell | memory | adapter | decoder LoRA | updates | 해석 |
|---|---|---|---|---|---|
| E00 | EG2 raw 753×512 | none | none | 0 | eval-only baseline |
| E10 | EG2 raw | trained | none | 100 | adapter-only |
| E01 (F0) | EG2 raw | none | 64 modules | 100 | adapter-free + LoRA |
| E11 (L) | EG2 raw | trained | 64 modules | 100 | adapter + LoRA |

- Primary: E01 vs E11 (LoRA fixed).
- E11 vs E10: LoRA with adapter.
- E01 vs E10: adapter + training path 동시; not clean.
- E00 not trained.

### Stages

| stage | units | updates | cap |
|---|---:|---:|---:|
| D0 | 4 | 0 | ≤15 min |
| D1 | 4 | 4 | ≤25 min |
| R | 4×3 | 900 | ≤120 min |

- Stage R only after D0/D1 mechanics pass, not signal-based.
- No 1-seed signal gate.
- M 1,440; phase7 7,200; generation 240.

## 3. 검토 질문

### Q1. Selection bias 제거

D0/D1 mechanics-only + Stage R 3-seed 기본이 v0.1의 selection bias를 제거하는가? D1 1-update가 필요한가, D0만으로 충분한가?

### Q2. 2×2

E01 vs E11 primary가 LoRA 고정 adapter contrast로 충분한가? E10/E00 보조 해석 한계가 명확한가?

### Q3. Interpretation

“E01/E11 negative → route STOP, not track STOP” 문구가 충분한가? E01 positive/E11 positive 분기 처리?

### Q4. M/signal

M 120/cell, signal 15 common, M not gate가 적절한가?

### Q5. Compute

D0 15 + D1 25 + R 120 min, 900 updates가 CPU 6 threads에서 현실적인가?

### Q6. H3

H3를 별도 prereg로 분리하는 것이 맞는가? primary에 LN/projection을 넣어야 하는가?

## 4. 답변 형식

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거
- 다음 단계: 1~3개

최종 판정: STOP / NARROW / CONTINUE
Stage D/R:
2×2:
Interpretation:
M/signal:
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
