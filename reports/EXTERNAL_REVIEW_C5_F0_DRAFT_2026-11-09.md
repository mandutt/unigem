# C5 F0 Draft — Independent Review Request

- 작성일: 2026-11-09
- 작성 기준 HEAD: `244b25c`
- 대상: `docs/plan_c5_f0_2026-11-09.md` (DRAFT)
- 선행: Phase 6 v1.0.11 negative 종료, B0-B candidate false
- 상태: **F0 미승인·미실행**
- test 163: sealed
- P1: unused
- T5Gemma2: D-108 STOP
- **새 독립 검토 라운드**. 기존 Phase 6/Results 스레드의 후속이 아니며 중복 요청이 아님.

---

## 0. Reviewer Instructions

1. 새 스레드에서 독립 검토하라. 기존 스레드 결론을 상속하지 말라.
2. 아래 파일을 직접 읽어라.
   - `docs/plan_c5_f0_2026-11-09.md`
   - `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`
   - `reports/C5_B0A_PM_PHASE6_LABELS_2026-11-09.md`
   - `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`
   - `runner/c5_pm_phase6.py`
3. 학습·평가 실행 금지. test 163/P1 사용 금지. 서브에이전트/추가 LLM 금지.
4. repository 수정 금지. 지정 report 파일만 작성.
5. Q1~Q6에 **판정 + 근거 + 다음 단계 1~3개**.
6. 최종 판정은 **STOP / NARROW / CONTINUE**.
7. 보고서 경로:
   `docs/hoplite/c5_f0_draft_review_2026-11-09/review_{MODEL}.md`
8. `reviewed HEAD`와 verbatim quote `adapter-associated signal loss`를 보고서에 포함하라.

---

## 1. 배경

Phase 6 결과:

- M_PASS all arms true; `m_pass_l:true`, `m_valid:true`.
- L signal false: copy mean -0.1135, CI [-0.2341,-0.0012], 0/3 seeds positive.
- tail_driven true; signal_status `MEAN_CONTRAST_ONLY`.
- B0-B candidate gate false.
- P(native no adapter) signal 3.076 vs PA(native adapter) 0.011; paired +3.065 (14/15).
- LoRA effect F vs L ≈ -0.0026 (8/15).
- “adapter bottleneck”는 native 경로 관찰로 축소됨; EG2 전체 일반화는 미확립.

F0의 질문:

> **LoRA를 고정한 상태에서 adapter 유무가 EG2 donor-specific signal을 바꾸는가?**

## 2. F0 설계

| cell | memory | adapter | decoder LoRA | updates |
|---|---|---|---|---|
| E00 | EG2 raw 753×512 | none | none | 0 |
| E10 | EG2 raw | trained 512→512 | none | 100 |
| E01 (F0) | EG2 raw | none | 64 modules | 100 |
| E11 (L) | EG2 raw | trained | 64 modules | 100 |

- Primary contrast: **E01 vs E11** (LoRA fixed; adapter differs).
- E00 is eval-only baseline, not a trained control.
- E10/E00 secondary; E01 vs E10 is not a clean causal contrast.
- M K=753, 15 common; M_POS_MEAN/M_NORM; 120 records/cell/seed.
- signal: donor-crop K=min(len(real),len(donor)), 20 val docs, 5 donors.
- no threshold/seed/donor/step/LR changes.

### Stage

| stage | scale | cap |
|---|---|---:|
| Stage D | 1 seed 20261111, 4 cells, 300 updates | ≤45 min |
| Stage R | 3 seeds, 900 updates | ≤150 min |

Stage D proceed rule:

```text
E01 copy mean delta > 0
AND E01 - E11 paired copy mean > 0
AND both E01/E11 endpoints finite on 15 common docs
```

- Stage D is descriptive; no statistical gate.
- If false → STOP F0; no 3-seed.
- Stage R only after Stage D pass.

### H3

- `E01-LN`: raw EG2 + fixed LayerNorm (no learned adapter).
- `E01-P`: raw EG2 + fixed orthogonal projection.
- `E01-R`: residual adapter `x + Adapter(x)`.

H3 is separate from primary 2×2.

## 3. 검토 질문

### Q1. 2×2 정합성

E01 vs E11이 LoRA 고정 하에서 adapter 효과를 분리하는가? E00/E10 보조 비교의 한계와, 추가로 필요한 cell/control은 무엇인가?

### Q2. Stage D decision

1-seed Stage D의 `E01>0 AND E01−E11>0` 규칙이 3-seed 진입 조건으로 타당한가? 
- 너무 관대/엄격한가?
- 1-seed 결과로 3-seed를 선택하는 selection bias가 있는가?
- Stage D를 완전 descriptive로 두고 Stage R을 항상 3-seed로 해야 하는가?

### Q3. H3

LN/projection/residual 중 primary에 포함할 것과 별도 prereg로 분리할 것을 구분하라. 
- Adapter의 LayerNorm이 원인일 가능성을 실제로 분리하는가?
- residual `x + Adapter(x)`가 identity를 보존하는가?

### Q4. M/signal

M 120/cell/seed, signal 15 common, E00 eval-only가 적절한가? 
- M_PASS를 gate로 쓰지 않는가?
- E00 0-update baseline과 E10/E01/E11 100-update 비교가 공정한가?

### Q5. Compute

Stage D 45분, Stage R 150분, 900 updates가 CPU 6 threads에서 현실적인가? 
- 12 units가 아니라 9 trained units + E00 eval-only라는 계산이 맞는가?
- generation/phase7 포함 cap인가?

### Q6. 해석 경계

F0 negative가 “EG2 feature 부족”을 의미하지 않는다는 조건이 충분한가? 
- F0 positive가 adapter 인과를 확정하는가?
- adapter-associated signal loss를 넘어 구조적 원인을 주장하려면 무엇이 필요한가?

## 4. 답변 형식

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거
- 다음 단계: 1~3개
```

마지막:

```text
최종 판정: STOP / NARROW / CONTINUE
F0 2×2:
Stage D:
H3:
M/signal:
Compute:
금지 범위:
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
- 기존 Phase 6 결과 재해석으로 B0-B 구제 금지
