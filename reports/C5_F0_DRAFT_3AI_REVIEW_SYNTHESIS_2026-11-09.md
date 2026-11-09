# C5 F0 Draft — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_f0_draft_review_2026-11-09/`
- 검토 HEAD: `68957bdc711acb8462cb9959e2c85b5299e65fd8`
- 대상: `docs/plan_c5_f0_2026-11-09.md` (DRAFT)
- 새 독립 스레드 3개
- test 163: sealed
- P1: unused
- 추가 학습/평가: 없음

## 0. 한 줄 결론

> **3/3 NARROW.** F0의 질문과 2×2 골격은 옳지만, **Stage D 1-seed 결과로 Stage R과 EG2 track을 STOP하는 규칙**이 자기모순이며 selection bias를 만든다. F0는 승인 불가; prereg 수정 후 재검토해야 한다.

## 1. 판정

| 검토자 | 모델 | 최종 판정 | 핵심 |
|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **NARROW** | §8 track STOP ↔ §1 H2 모순 |
| DeepSeek | `deepseek-v4.1-flash-1017` high | **NARROW** | 4 structural reasons; 1-seed STOP |
| Sol | `gpt-6.1-sol` medium | **NARROW** | Stage D selection gate; not approval |
| **종합** | — | **NARROW 3/3** | **F0 미승인** |

## 2. 합의된 것

- F0 질문은 옳다: **LoRA 고정 하 adapter 유무가 EG2 donor-specific signal을 바꾸는가**.
- **E01 vs E11**은 primary contrast로 적절하다 (LoRA 고정, adapter만 차이).
- E00/E10은 보조 비교이며 clean causal contrast가 아니다.
- M_PASS는 donor-specific content-use 증거가 아니다.
- F0 negative가 “EG2 feature 부족”을 의미하지 않는다.
- F0 positive가 adapter 구조적 인과를 확정하지 않는다.
- H3 LN/projection/residual은 primary와 분리해야 한다.
- **F0는 승인 불가, 실행 금지**.

## 3. Must-fix (consensus)

### MF-1. Stage D STOP 규칙 자기모순 (blocker)

- §1 H2: “F0 negative는 트랙 STOP의 충분조건이 아니다.”
- §8: “E01 negative and E11 negative → stop EG2 resident track.”
- GLM/DS/Sol 모두 같은 모순 지적.
- 1 debug seed, 15 docs로 track STOP은 과도하다.
- 수정: §8에서 track STOP 삭제; 최대 **“stop the EG2-raw→mT5-decoder route as configured”**로 한정.

### MF-2. Stage D selection bias

- Stage D는 “descriptive/no gate”라면서 Stage R 진입을 1-seed 결과로 결정한다.
- Sol: 실질적으로 prospective selection gate.
- DS: cheap error(3-seed ~87min)는 막고, expensive error(track kill)는 허용하는 비대칭.
- 수정:
  - Stage D는 **mechanics/D0-D1 only**, no decision; 또는
  - Stage R을 항상 3-seed로 실행; 또는
  - Stage D decision rule을 제거하고 3 seeds를 기본으로.

### MF-3. 2×2 cell 정의

- E01 vs E11은 적절.
- E00은 0-update eval baseline, trained control 아님.
- E01 vs E10은 LoRA+training path 동시 차이로 causal contrast 아님.
- E10 vs E00도 adapter+training 차이.
- 수정: 2×2 표에 “trained/eval-only”와 interpretability를 명시; E00은 baseline으로만.

### MF-4. F0 코드 미구현

- `runner/c5_pm_phase6.py`의 `arm_spec`은 F/L/P/PA만 지원.
- F0 E00/E01/E10/E11은 코드에 없다.
- “F0 draft”는 설계이며 구현이 아니다.
- 수정: F0 전용 `c5_pm_f0.py`/arm mode를 별도 구현하고, D0-D1 후 Stage D.

### MF-5. H3 분리

- LN/projection/residual을 primary 2×2에 섞지 말 것.
- 별도 prereg 또는 별도 stage.
- residual `x + Adapter(x)`가 identity를 보존하는지 별도 검증.

### MF-6. Compute/해석

- DS measured 82 min (Stage R?) vs draft 150min; compute estimate 재검토.
- Stage D 45min, 300 updates; Stage R 900 updates.
- F0 negative/positive의 해석 상한을 명시.

## 4. 검토자별

### GLM

- F0 질문/2×2는 옳다.
- §8 track STOP이 §1 H2와 모순 (blocker).
- H3는 별도.
- Stage D rule의 positive/negative 해석 상한 보강.
- NARROW.

### DeepSeek

- 4 structural reasons:
  1. §8 STOP/H2 모순.
  2. 1-seed/15-doc STOP.
  3. E01 vs E10 not clean.
  4. F0 code/arm_spec hardcoded F/L/P/PA.
- Stage D selection bias.
- Code provenance improved vs prior review, but F0 not implemented.
- NARROW.

### Sol

- Stage D is prospective selection gate.
- F0 negative ≠ feature insufficiency; positive ≠ unique adapter architecture.
- H3/LN/residual separate.
- Do not approve D0/D1/D/R/H3.
- NARROW.

## 5. 결정

```text
F0 draft = 3/3 NARROW
F0 = 미승인, 미실행
Stage D STOP rule = 수정 필요
Stage R selection = 재설계 필요
H3 = 별도 prereg
B0-B = 미승인 (Phase 6 negative)
```

## 6. 다음 단계

1. F0 draft 수정:
   - Stage D를 mechanics-only로.
   - Stage R은 3 seeds 기본; 1-seed 선택 gate 제거.
   - track STOP 문구 삭제/한정.
   - E00/E10 interpretability 명시.
   - H3 분리.
2. F0 코드/D0-D1 구현은 별도 승인 후.
3. F0 revised draft 3-AI 재검토.
4. 승인 후에만 실행.

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_f0_draft_review_2026-11-09/review_GLM.md` | GLM NARROW |
| `.../review_DS1017.md` | DeepSeek NARROW |
| `.../review_SOL.md` | Sol NARROW |
| `reports/C5_F0_DRAFT_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |

## 8. 제한

- 이 종합은 F0 승인이 아니다.
- 3/3 NARROW: prereg 수정 후 재검토.
- test 163 sealed; P1 unused; T5Gemma2 D-108 STOP.
