# F5 A2-null — exploratory 계획 v0.1

- 작성: 2026-11-06
- 상태: **exploratory 승인 (D-081), 코드·학습 미착수**
- 범위: EG2 text intermediate layer를 final projection의 null space에 주입하는 A2 변형
- 데이터: `data/external/f5_pairs_v3_clean.jsonl` (1,617; train 1,293 / val 161 / test 163)
- 관련: D-042, D-080, D-081, `docs/plan_c5_abstractive_v0_1.md`

## 1. 배경과 정확한 범위

참고한 Reddit/EmbeddingGemma-2 방식은 **audio retrieval용 pooled embedding**을 보강한다.

```text
text/audio hidden → W(768×512) → 768d embedding
                         └ left null space 256d ← intermediate audio layer PCA 256
```

우리의 A2-null은 이를 **text token sequence**에 적응한 exploratory 변형이다. 원 방법을 그대로 재현했다고 주장하지 않는다.

### 두 변형

| 변형 | 입력 | 목적 |
|---|---|---|
| **A2-null-seq (primary)** | EG2 token hidden 512 + null-injected PCA 256 = 768/token | T5 decoder cross-attention용 sequence |
| A2-null-pooled (reference) | pooled 768 embedding 1개 | 원 방법에 가장 가까운 축소 실험 |

A2-null-seq의 수식:

```text
h_t       = EG2 text final hidden (512)
x_t       = PCA_256(EG2 intermediate hidden at t)   # 512 → 256
P         = left null basis of W (768×256), WᵀP = 0
z_t       = W h_t + P x_t                         # 768
memory_t  = Adapter(z_t)                            # 768 → 640
```

- `W h_t`는 원래 EG2 final projection과 같은 768d 공간
- `P x_t`는 W의 column space와 직교하는 256d
- adapter만 학습; T5Gemma2 decoder와 EG2 원본은 동결

## 2. D-042와의 관계

- D-042는 **raw EG2 text hidden을 F4/F5 제품 경로에 사용하지 않는다**는 결정이다.
- A2-null은 raw hidden을 그대로 쓰지 않고 **intermediate layer + null-space projection**이라는 새 표현을 쓴다.
- 따라서 **exploratory 실험은 허용**하되, 제품 채택은 D-042를 대체하는 **새 결정**이 필요하다.
- A2-null이 A1보다 낫다는 증거가 나오기 전에는 제품 경로·JEV 코어에 연결하지 않는다.

## 3. Scope

### 포함

1. Null-space 수학 검증:
   - `W = language_model.embedding_projection.weight` (768×512)
   - SVD로 left null basis `P` (768×256) 추출
   - `max |WᵀP|`, `PᵀP=I` 확인
2. EG2 text intermediate layer 선택:
   - 후보 layer 2/6/12/18/23
   - train 1,293에서 token hidden 추출
   - PCA 256 explained variance 기록
3. A2-null-seq feature cache:
   - token-level 512 + PCA 256 → 768
   - float16 저장, split별 manifest
4. T5Gemma 2 external memory 호환성 확인:
   - `encoder_outputs`로 640d memory 주입
   - dummy memory로 decoder forward smoke
5. Adapter smoke:
   - 768→640 2-layer MLP
   - 1~10 step, loss/NaN/RSS/step time
6. 소규모 pilot → full train(별도 승인)
7. A1과 동일 split·seed·test로 비교
8. G-C5 grounding, char F1, copy rate, 사람 50
9. 보고서 `reports/C5_a2null.md`

### 제외

- A2-null 제품 채택
- D-042 폐기
- F5 test 163의 조기 사용
- JEV/메모리 코어 수정
- EG2 원본 fine-tuning
- A1 없는 단독 결론
- STT(F2) 재개

## 4. DoD

| # | 항목 | 통과 기준 |
|---|---|---|
| 1 | null basis | rank 512, nullity 256, `max|WᵀP| < 1e-4` |
| 2 | PCA | 256d explained variance 기록; layer별 비교 |
| 3 | external memory | T5 decoder가 640d memory로 forward |
| 4 | adapter smoke | 10 step, NaN 없음, peak RSS ≤13GB |
| 5 | extraction | train/val/test 전량, manifest sha256 |
| 6 | A2-null 학습 | train 1,293, val 161; test 미사용 |
| 7 | G-C5 | grounding ≥99%, 신규 슬롯 ≤1% |
| 8 | 비교 | A0·A2-null-raw·A2-null-seq; A1은 A1 완료 후 |
| 9 | 사람 검토 | 50건, 수용 ≥60% |
| 10 | 보고서 | `reports/C5_a2null.md` |

**중단 규칙:** nullity가 256이 아니거나, `WᵀP`가 1e-4를 넘거나, T5 external memory가 동작하지 않으면 학습을 시작하지 않는다.

## 5. Public API (초안)

```python
@dataclass
class A2NullFeatures:
    final_hidden: Tensor   # [T, 512]
    null_features: Tensor  # [T, 256]
    layer: int

class A2NullEncoder:
    def encode(self, text: str) -> A2NullFeatures: ...
    def memory(self, text: str) -> Tensor: ...  # [T, 640]

class C5A2NullSummarizer:
    def summarize(self, text: str) -> SummaryResult: ...
```

- `P`, PCA mean/components, adapter path는 `data/models/f5_a2null/`에 저장.
- 원본 EG2/T5Gemma 2 가중치는 불변.

## 6. 구현 순서

1. **null-space probe**: W, SVD, P, text pooled component invariance
2. **layer/PCA probe**: 100~200 train 샘플로 layer별 explained variance
3. **T5 external memory smoke**: dummy 640d memory
4. **feature extraction**: 1,617 전량, float16, checkpoint/resume
5. **adapter smoke**: 10 step
6. **pilot**: 50~100 step
7. **full train**: 별도 승인
8. **자동 평가 + 사람 50**
9. **A1과 비교 / CP3-3**

## 7. 예상 비용·위험

| 항목 | 예상 |
|---|---|
| null-space SVD | 초 단위 |
| EG2 feature extraction 1,617 | CPU 수십 분~2시간 |
| A2-null adapter smoke | 수 분 |
| full train | **미정 — smoke 후 산정** |
| 저장 | feature cache 수 GB 이하 |

위험:

- 원 Reddit 방법은 **pooled embedding**이고, 우리 A2-null-seq는 **token-level 확장**이다. 성능이 보장되지 않는다.
- EG2 intermediate layer가 요약에 유용하다는 근거는 아직 없다.
- T5 decoder external memory 주입이 아키텍처상 제한될 수 있다.
- A2-null이 A1보다 나쁠 가능성이 높다. exploratory로만 판단한다.

## 8. 승인 경계

- 이 계획은 **탐색 실험**이다. 제품 채택·D-042 폐기·test 사용은 별도 승인이다.
- full train 전에 smoke 결과(RSS, step time, loss)를 보고한다.

## 9. Cross-feature 경계 (2026-11-06 추가)

- 이 실험은 F5만의 요약기가 아니라 **EG2→T5Gemma2 decoder bridge**를 만든다. 이 bridge는 향후 F4(맞춤법 교정), F6(STT 후처리 교정)의 decoder 경로와 공유될 수 있다.
- **현재 F3(비전 태깅)는 retrieval/emoji tagging이며 decoder를 쓰지 않는다.** 향후 vision→text tagging으로 확장할 때만 decoder bridge가 관련된다.
- 따라서 decoder LoRA를 F5 전용으로 확정하기 전에 **F4/F6 멀티태스크 재사용·retention**을 검토해야 한다.
- 이 계획은 F4/F6/F3 코드를 구현·승인하지 않는다. 재사용은 D-042 경계와 별도 gate/결정이 필요하다.
- 외부 검토 질문 Q12~Q15가 이 경계를 다룬다: `reports/EXTERNAL_REVIEW_C5_A2NULL_2026-11-06.md`.
