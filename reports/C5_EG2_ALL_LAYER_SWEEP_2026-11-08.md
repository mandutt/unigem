# C5 EG2 all-layer hidden sweep — 2026-11-08

## 1. 목적과 정정

이전 답변에서 “layer2/3은 semantic abstraction이 부족할 가능성이 크다”고 한 것은 **실측이 아니라 추측**이었다. 이번에 EG2 `hidden_states[0..24]`를 **문서당 한 번의 forward**로 모두 추출해 train 300 / val 100에서 hidden cosine을 측정했다. layer0은 embedding, layer1~23은 transformer hidden(512), layer24는 projected retrieval output(768)이다.

## 2. 프로토콜

- 데이터: `f5_pairs_v3_clean.jsonl`, split seed42, train 300 / val 100
- source: `summarize: ` + passage, T5Gemma2 tokenizer, max_length 1024
- teacher: base T5Gemma2 encoder hidden 640 (A1 LoRA 없음)
- adapter: linear / MLP768 / MLP1536, scratch, 2 epoch, lr 1e-3, seed 20261108
- objective: `1 - cosine(adapter(h_layer), teacher_hidden)` on min token length
- test 163: **미사용**
- cache: `runner/c5_eg2_all_layers_cache.py`, **417.7s** (all 25 layers, one forward per document)


## 3. 전체 결과

| layer | kind | dim | linear | MLP768 | MLP1536 |
|---:|---|---:|---:|---:|---:|
| 0 | embedding | 512 | 0.7267 | 0.7521 | 0.7597 |
| 1 | transformer | 512 | 0.7296 | 0.7550 | 0.7689 |
| 2 | transformer | 512 | 0.7370 | 0.7539 | 0.7621 |
| 3 | transformer | 512 | 0.7382 | 0.7598 | 0.7704 |
| 4 | transformer | 512 | 0.7489 | 0.7723 | 0.7853 |
| 5 | transformer **← MLP1536 best** | 512 | 0.7580 | 0.7789 | 0.7927 |
| 6 | transformer | 512 | 0.7582 | 0.7766 | 0.7883 |
| 7 | transformer | 512 | 0.7611 | 0.7773 | 0.7878 |
| 8 | transformer | 512 | 0.7607 | 0.7793 | 0.7907 |
| 9 | transformer | 512 | 0.7604 | 0.7798 | 0.7910 |
| 10 | transformer | 512 | 0.7558 | 0.7773 | 0.7886 |
| 11 | transformer | 512 | 0.7535 | 0.7731 | 0.7850 |
| 12 | transformer | 512 | 0.7424 | 0.7629 | 0.7747 |
| 13 | transformer | 512 | 0.7370 | 0.7591 | 0.7709 |
| 14 | transformer | 512 | 0.7304 | 0.7535 | 0.7671 |
| 15 | transformer | 512 | 0.7217 | 0.7482 | 0.7610 |
| 16 | transformer | 512 | 0.7125 | 0.7391 | 0.7506 |
| 17 | transformer | 512 | 0.7076 | 0.7305 | 0.7398 |
| 18 | transformer | 512 | 0.7000 | 0.7261 | 0.7357 |
| 19 | transformer | 512 | 0.6942 | 0.7208 | 0.7297 |
| 20 | transformer | 512 | 0.6894 | 0.7168 | 0.7259 |
| 21 | transformer | 512 | 0.6864 | 0.7151 | 0.7242 |
| 22 | transformer | 512 | 0.6834 | 0.7130 | 0.7223 |
| 23 | transformer | 512 | 0.6806 | 0.7105 | 0.7197 |
| 24 | projected_output (final projection) | 768 | 0.6665 | 0.6998 | 0.7102 |


## 4. 판정

- **MLP1536 최고: layer5 .7927** (layer9 .7910, layer8 .7907, layer10 .7886, layer6 .7883).

- **linear 최고: layer7 .7611**; MLP768 최고: layer9 .7798.

- **layer5가 새 최고**이며, D-104의 “layer9 best”는 layer6/9/12만 본 부분 스캔의 결론이었다. layer5는 그 스캔에 없었다.

- **layer2/3 실측**: layer2 .7621, layer3 .7704. layer5~11보다 낮아 “early layer가 중간층보다 약하다”는 방향은 **부분 지지**된다. 그러나 layer0 .7597, layer1 .7689 > layer2이고, layer3 < layer12 .7747이므로 **단조 증가도, 깔끔한 semantic abstraction 곡선도 아니다.** 따라서 “layer2/3 semantic abstraction 부족”은 여전히 **직접 증명되지 않은 해석**이며, hidden alignment가 낮다는 사실만 확인됐다.

- final projection(layer24) .7102로 전체 transformer layer보다 낮다. final 768을 hidden 대용으로 쓰면 안 된다는 기존 결론을 재확인했다.

- **주의**: 이 실험은 hidden cosine만 측정했다. D-105에서 layer9의 hidden 개선이 free-running으로 전이되지 않았으므로, layer5의 hidden 우위를 생성 성능 우위로 해석할 수 없다. **B2 layer5는 미실행**이다.


## 5. mT5 smoke에의 시사점

> **범위 정정 (2026-11-08):** 이 sweep의 teacher는 **base T5Gemma2 encoder hidden 640**이다. 따라서 이 결과는 **mT5-small에 적합한 layer를 식별한 것이 아니다.** layer5/12/9는 **후보**일 뿐이며, mT5 decoder의 CE/memory ablation으로 별도 검증해야 한다. mT5의 d_model은 512이고 cross-attention 분포도 T5Gemma2와 다르므로 hidden cosine 순위를 전이할 수 없다.

- EG2 feature는 **layer5(최고 hidden)**와 **layer12(B2 free-running 최고)**를 비교하는 것이 합리적이다. layer9는 hidden 상위권 비교군으로 유지한다.

- layer24(768 projection)와 layer0(embedding)은 bridge 입력으로 쓰지 않는다.

- mT5 cross-attention에서도 hidden cosine 순위가 유지된다는 보장은 없다. **interface smoke에서 layer5 vs layer12를 직접 비교**해야 한다.


## 6. 산출물

- `reports/provenance/C5_b1d/all_layers_pretest.json`
- `reports/provenance/C5_b1d/layer{0..24}_pretest.json`
- `runner/c5_eg2_all_layers_cache.py`
- `data/wave2c/eg2_layer{0..24}/`
- test 163 sealed
