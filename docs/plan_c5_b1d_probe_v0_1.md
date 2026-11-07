# C5 B1d Bridge Feasibility Probe v0.1

## 0. 목적

EG2(EmbeddingGemma 2) 상주 인코더를 T5Gemma2 decoder에 연결하는 **B1d teacher-hidden distillation** 경로가 실제로 성립하는지, 소규모로 검증한다.

이 probe는 요약 품질 실험이 아니다. **인터페이스·토큰 정렬·hidden scale·`encoder_outputs` 경로**만 확인한다.

## 1. 범위

- train 5문서, val 2문서 (test 163 **사용 금지**)
- EG2 text encoder frozen, T5Gemma2 encoder는 teacher로만 사용
- adapter: token-level 768→640 (LayerNorm 포함)
- teacher hidden: T5Gemma2 encoder `last_hidden_state`
- student hidden: EG2 text `last_hidden_state`
- 학습: adapter만, 200 step 이내
- 생성: val 1문서, `encoder_outputs=BaseModelOutput(last_hidden_state=H_s)`로 16 token 이내

## 2. DoD

| 항목 | 기준 |
|---|---|
| token alignment | train/val 7/7에서 token sequence 동일 |
| teacher shape | `[T, 640]` |
| student shape | `[T, 768]` |
| adapter train loss | 초기 대비 감소 |
| val cosine | 초기 대비 증가 |
| `encoder_outputs` generate | 예외 없이 non-empty 출력 |
| test split | **미사용** |
| full train | **하지 않음** |

## 3. Public interface

```python
# student
eg2_out = eg2.language_model(**enc)
H_eg2 = eg2_out.last_hidden_state  # [B,T,768]

# adapter
H_s = adapter(H_eg2)               # [B,T,640]

# decoder-side injection: encoder_outputs, NOT inputs_embeds
gen = t5.generate(
    encoder_outputs=BaseModelOutput(last_hidden_state=H_s),
    attention_mask=mask,
)
```

`inputs_embeds`는 T5 encoder를 다시 실행하므로 B1d 목적과 모순된다.

## 4. 구현 순서

1. token alignment audit
2. EG2 student feature 추출
3. T5 teacher feature 추출
4. adapter cosine distillation (train 5)
5. val cosine
6. `encoder_outputs` generate smoke
7. JSON 보고서

## 5. 해석 제한

- 5+2문서 결과는 **품질 근거가 아니다.**
- adapter cosine이 높아도 요약이 좋다는 뜻이 아니다.
- probe 통과 후에도 full distillation 전에 다음을 별도 결정한다:
  - teacher hidden cache 1,293 train 전체
  - adapter 용량(linear vs 2-layer)
  - decoder LoRA 필요 여부(B2)
  - prompt(`summarize: `) 포함 방식
- test 163은 계속 sealed.

## 6. 중단 조건

- token sequence mismatch → **STOP**, alignment 설계부터 재검토
- EG2/T5 hidden shape 불일치 → **STOP**
- `encoder_outputs` generate 예외 → **STOP**, 인터페이스 재검토
- OOM/시간 초과 → 문서화 후 중단
