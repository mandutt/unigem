# F5 추상 요약 — C3 A1 T5Gemma 2 LoRA 계획 v0.1

- 작성: 2026-11-06
- 상태: **승인 대기 (코드·학습 미착수)**
- 범위: F5 메모리용 추상 요약. A0 추출형은 기준선으로만 유지.
- 데이터: `data/external/f5_pairs_v3_clean.jsonl` (1,617쌍, grounding 100%)
- 관련: `docs/plan_v0_5.md` §C3·§C5, D-042(EG2 text hidden 폐기), D-055(C-11.3), D-080

## 1. 결정

- **A0 추출형은 최종 구현이 아니다.** F5는 **추상 요약**이 목표다.
- C3 후보 중 **A1 = T5Gemma 2 네이티브 encoder-decoder + LoRA**를 먼저 구현한다.
- A2(EG2 adapter)는 D-042에서 F5 text hidden 사용이 폐기됐으므로 이번 경로에서 제외한다.
- A3(mT5-small)는 A1이 자원/품질에서 실패할 때만 fallback으로 검토한다.
- 원본 T5Gemma 2 가중치는 불변; LoRA adapter만 저장한다.

## 2. Scope

### 포함

1. T5Gemma 2 **텍스트 전용** 로드(비전 타워 제거 가능 여부 확인) 및 토크나이저 고정.
2. clean 1,617쌍의 train 1,293 / val 161 / test 163 split 재사용.
3. LoRA 학습:
   - attention q/k/v/o 우선, 필요 시 FFN 확장.
   - base frozen, adapter만 학습.
   - gradient checkpointing, batch 1 + gradient accumulation.
4. **CPU smoke**: 1 step forward/backward, step time, peak RSS, OOM 여부.
5. **소규모 LoRA pilot**: 50~100 step으로 loss/생성 붕괴 여부 확인.
6. **본 학습**: smoke/pilot 통과 후 2~3 epoch, val 161로 best 선택.
7. 평가: char F1, ROUGE-L, slot grounding/new, source coverage, copy rate, 길이, 지연.
8. 사람 표본 50건 검토.
9. 보고서 `reports/C5_abstractive.md` + CP3-2.

### 제외

- A0를 최종으로 채택하지 않음.
- A2 EG2 adapter, A3 mT5-small은 이번 승인 범위 밖.
- 외부 LLM API 호출.
- P1 메모리 원문 사용.
- JEV/메모리 코어 수정.
- 원본 T5Gemma 2 full fine-tuning.
- STT(F2) 재개.

## 3. DoD

| # | 항목 | 통과 기준 |
|---|---|---|
| 1 | 모델 로드 | 텍스트 전용 로드 성공, 파라미터·RSS 기록 |
| 2 | CPU smoke | 1 step 완료, peak RSS ≤13GB, step time 기록 |
| 3 | LoRA pilot | 50~100 step loss 하락, NaN/붕괴 없음 |
| 4 | 본 학습 | train 1,293, val 161, test 163; best val checkpoint |
| 5 | G-C5 | test에서 grounding ≥99%, 신규 슬롯 ≤1%, 위반 0 목표 |
| 6 | 품질 | A0 대비 char F1 또는 사람 수용도 개선 |
| 7 | 추상성 | copy rate가 A0보다 낮음(원문 장문 복사 감소) |
| 8 | 사람 검토 | 50건, 수용 ≥60%; 치명적 사실 누락 없음 |
| 9 | 보고서 | `reports/C5_abstractive.md`, CP3-2 |

**중단 규칙:** smoke에서 peak RSS >13GB 또는 step time이 60초를 넘으면 full train을 시작하지 않고 보고한다. VPS/GPU 사용은 별도 승인이다.

## 4. Public API (초안)

```python
@dataclass
class SummaryResult:
    summary: str
    grounded: bool
    new_slots: list[str]
    missing_slots: list[str]
    latency_ms: float

class F5AbstractiveSummarizer:
    def load(self) -> None: ...
    def summarize(self, text: str, max_new_tokens: int = 256) -> SummaryResult: ...
```

- `grounded=False`이면 상위 호출자는 **원문 폴백**을 사용한다.
- 학습·평가 CLI는 `runner/`에 두고, JEV에는 직접 연결하지 않는다.
- adapter 경로는 `data/models/f5_t5gemma2_lora/`에 저장하고 원본과 분리한다.

## 5. 구현 순서

1. **모델·토크나이저 고정**: text-only 로드, vision tower 제거 가능성 확인, token length 재확인.
2. **환경**: PEFT 필요 여부 확인. 필요하면 `peft` 설치(로컬 venv).
3. **smoke**: 1 batch forward/backward, RSS·step time.
4. **pilot**: 50~100 step, loss·생성 sanity.
5. **본 학습**: 2~3 epoch, val 선택, early stop.
6. **자동 평가**: test 163, A0와 동일 슬롯 검증기.
7. **사람 검토**: 50건 HTML.
8. **CP3-2**: 채택/보류/폐기.

## 6. 예상 비용

| 단계 | 호스트 | 예상 |
|---|---|---|
| 모델 로드·토크나이즈 | 로컬 CPU | 10~20분 |
| smoke 1 step | 로컬 CPU | 5~20분 |
| pilot 100 step | 로컬 CPU | 30분~2시간 |
| 본 학습 | 로컬 CPU | **미정 — smoke 후 산정** |
| 평가 | 로컬 CPU | 1~2시간 |
| 사람 검토 50 | 사용자 | 1~2시간 |

- T5Gemma 2 전체 786M, 텍스트 전용 369M, FP32 1.5GB, 추론 RSS 3.7GB(C-11.3).
- 학습은 LoRA + gradient checkpointing으로 메모리를 낮춘다.
- **GPU 없이 진행**하되, smoke 결과가 중단 규칙을 넘으면 VPS/GPU를 별도 승인받는다.

## 7. 데이터·평가 원칙

- clean 1,617쌍만 사용; 원본 target 문장을 변형하지 않는다.
- test 163은 최종 1회만 사용하고, val로 hyperparameter를 고정한다.
- G-C5의 `보존`은 D-080의 **grounding rate** 정의를 따른다.
- char F1·ROUGE-L은 참고 지표이며, 사람 검토와 slot gate를 대체하지 않는다.
- A0 결과(clean: grounding 0/163 위반, char F1 0.6072)를 비교 기준으로 둔다.

## 8. 승인 요청

**권장: 1~4단계(모델 로드 + CPU smoke + pilot)만 먼저 승인.**  
smoke/pilot 결과를 보고 full train 여부를 다시 승인받는다.

승인 시 다음을 진행한다.
- T5Gemma 2 text-only 로드
- LoRA smoke/pilot
- step time·peak RSS·loss 보고

승인 전에는 코드·학습을 시작하지 않는다.
