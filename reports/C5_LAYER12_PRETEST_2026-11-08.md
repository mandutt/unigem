# C5 EG2 layer12 512 pretest — final 768 대비 (2026-11-08)

## 1. 목적

EG2 final hidden 768이 retrieval/embedding objective에 최적화되어
token-level 정보가 약할 수 있다는 가설을 검증한다.

- final 768 (기존 B1d/B2 입력)
- layer12 512 (중간 layer)
- 동일 teacher hidden cosine objective, decoder 없음

## 2. 설정

- train 300 / val 100
- `summarize: ` prefix + T5 tokenizer ID (B1d cache와 동일)
- 2 epoch, lr 1e-3, scratch, same seed
- loss: `1 - cosine(adapter(feature), teacher_hidden)`
- test 163 미사용

## 3. 결과

| input | adapter | params | val cosine | final 768 MLP768 대비 |
|---|---|---:|---:|---:|
| final 768 | MLP768 | 1,084,033 | 0.6998 | 기준 |
| **layer12 512** | linear | 329,601 | **0.7424** | **+4.26%p** |
| **layer12 512** | MLP768 | 887,425 | **0.7629** | **+6.31%p** |
| **layer12 512** | MLP1536 | 1,772,929 | **0.7747** | **+7.49%p** |

- layer12 linear만으로 final 768 MLP768보다 **+4.26%p** 높다.
- layer12 MLP1536은 **0.7747**로 가장 높다.
- final 768의 정보 병목 가설을 지지한다.

## 4. 해석

- final layer는 embedding/retrieval 목적에 맞춰져 있어 token-level 정보가 일부 손실될 수 있다.
- layer12는 teacher hidden과의 alignment에 더 유리하다.
- layer12 MLP1536은 capacity 이득도 일부 있지만, **입력 feature 선택의 효과가 더 크다.**
- 이 결과는 “adapter width 확장”보다 **feature layer 선택**이 더 중요하다는 것을 보여준다.

## 5. 다음

- **B2 layer12 512 + MLP1536** (300문서, gold target, decoder LoRA)
- teacher-forced CE/token accuracy
- val20/val100 free-running F1/grounded
- final 768 B2 gold300과 비교

## 6. 산출물

- `data/wave2c/eg2_layer12/` (train 300 / val 100, 512d)
- `runner/c5_eg2_layer12_cache.py`
- `runner/c5_layer12_pretest.py`
- `reports/provenance/C5_b1d/layer12_pretest.json`
- `data/models/f5_t5gemma2_lora/layer12_hidden/mlp{768,1536}_adapter_final.pt`
- cache 추출 **379.7s**, pretest **약 30s**
