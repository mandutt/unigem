# C5 EG2 layer sweep — layer9가 최적 (2026-11-08)

## 1. 목적

EG2 hidden layer를 바꾸면 teacher hidden alignment가 개선되는지 확인한다.

- final 768
- layer12 512
- layer6 512
- layer9 512
- concat(layer12+final) 1280

모두 동일한 hidden cosine objective, train 300 / val 100, scratch, same seed.

## 2. 결과

| feature | linear | MLP768 | MLP1536 | 최고 |
|---|---:|---:|---:|---:|
| final 768 | 0.6665 | 0.6998 | 0.7102 | 0.7102 |
| layer12 512 | 0.7424 | 0.7629 | 0.7747 | 0.7747 |
| layer6 512 | 0.7582 | 0.7766 | **0.7883** | 0.7883 |
| **layer9 512** | **0.7604** | **0.7798** | **0.7910** | **0.7910** |
| concat 1280 | 0.7157 | 0.7345 | 0.7450 | 0.7450 |

- **layer9 MLP1536 0.7910**가 최고
- layer6 0.7883, layer12 0.7747
- final 768 0.7102
- concat 0.7450

## 3. 해석

- 중간 layer(layer6~9)가 final보다 token-level 정보가 풍부하다.
- layer9가 layer6/12보다 약간 우세하다.
- final 768은 retrieval objective에 최적화되어 token-level 정보가 약하다.
- concat은 final의 noise를 더해 오히려 악화된다.
- **feature layer 선택이 adapter width보다 훨씬 중요**하다.

## 4. 다음

- **B2 layer9 512 + MLP1536, 300문서, gold target, decoder LoRA r8**
- layer12 B2(val CE 2.2983, F1 .3464/21%)와 직접 비교
- 이후 slot auxiliary/copy 또는 on-policy KD

## 5. 산출물

- `data/wave2c/eg2_layer6/`(train 300/val 100)
- `data/wave2c/eg2_layer9/`(train 300/val 100)
- `data/models/f5_t5gemma2_lora/layer6_hidden/`
- `data/models/f5_t5gemma2_lora/layer9_hidden/`
- `reports/provenance/C5_b1d/layer6_pretest.json`
- `reports/provenance/C5_b1d/layer9_pretest.json`
- test 163 미사용
