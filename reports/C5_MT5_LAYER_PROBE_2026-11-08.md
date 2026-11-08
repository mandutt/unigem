# C5 mT5-small layer probe — Stage A (2026-11-08)

## 1. 목적

mT5-small decoder를 frozen으로 두고, EG2 layer1~23 각각이 **native cross-attention memory**로 실제 사용 가능한지 screening했다. teacher hidden cosine이 아니라 **decoder CE와 memory ablation**을 직접 측정했다.

## 2. 프로토콜

- model: `google/mt5-small` (300M, d_model 512, 8 decoder layers)
- train 5 / val 5, seed 20261108
- adapter: MLP 512→512→512 + LayerNorm, adapter-only
- decoder frozen; mT5 encoder bypassed via `encoder_outputs`
- 100 steps, lr 1e-3, target max 256
- val: real vs zero vs shuffled memory CE
- test 163: 미사용
- layer0(embedding), layer24(projection) 제외


## 3. 결과

| layer | train CE last | val real CE | zero CE | shuffled CE | Δ zero | Δ shuffled |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 5.660 | 7.286 | 25.877 | 7.238 | 18.591 | -0.048 |
| 2 | 5.465 | 7.071 | 25.877 | 7.077 | 18.806 | 0.006 |
| 3 | 5.057 | 7.236 | 25.877 | 7.247 | 18.641 | 0.011 |
| 4 | 5.872 | 7.301 | 25.877 | 7.320 | 18.576 | 0.018 |
| 5 | 5.595 | 7.460 | 25.877 | 7.521 | 18.417 | 0.061 |
| 6 | 5.412 | 7.075 | 25.877 | 7.109 | 18.802 | 0.034 |
| 7 | 5.496 | 7.094 | 25.877 | 7.113 | 18.783 | 0.018 |
| 8 | 5.802 | 7.372 | 25.877 | 7.320 | 18.506 | -0.051 |
| 9 | 5.201 | 6.997 | 25.877 | 7.011 | 18.880 | 0.014 |
| 10 | 5.742 | 7.240 | 25.877 | 7.279 | 18.638 | 0.039 |
| 11 | 5.301 | 6.950 | 25.877 | 6.911 | 18.927 | -0.039 |
| 12 | 5.388 | 7.088 | 25.877 | 7.082 | 18.789 | -0.005 |
| 13 | 5.046 | 6.918 | 25.877 | 6.935 | 18.959 | 0.017 |
| 14 | 5.334 | 7.017 | 25.877 | 7.130 | 18.861 | 0.114 |
| 15 | 5.422 | 7.283 | 25.877 | 7.335 | 18.594 | 0.052 |
| 16 | 5.130 | 6.908 | 25.877 | 6.980 | 18.969 | 0.072 |
| 17 | 5.579 | 7.104 | 25.877 | 7.293 | 18.773 | 0.189 |
| 18 | 5.757 | 7.416 | 25.877 | 7.500 | 18.461 | 0.084 |
| 19 **← best real** | 4.964 | 6.623 | 25.877 | 6.653 | 19.255 | 0.030 |
| 20 | 5.837 | 7.387 | 25.877 | 7.510 | 18.490 | 0.122 |
| 21 | 6.231 | 7.469 | 25.877 | 7.520 | 18.408 | 0.051 |
| 22 | 5.628 | 7.306 | 25.877 | 7.283 | 18.571 | -0.023 |
| 23 | 5.505 | 7.132 | 25.877 | 7.208 | 18.745 | 0.076 |


- **best real CE: layer19 6.623**

- best Δzero: layer19 19.255; best Δshuffled: layer17 0.189

## 4. 판정

**PARTIAL_MEMORY_USE_NO_CONTENT_SELECTIVITY**

- real CE는 zero CE보다 **18~19 CE 낮음** → decoder가 memory의 존재/길이를 사용한다.

- 그러나 real CE와 shuffled CE의 차이는 **최대 .189**, 대부분 0 근처 → **문서 내용 기반 선택성은 확인되지 않음**.

- layer별 real CE 차이는 있으나(최저 layer19 6.623, 최고 layer21 7.469), shuffled 이득이 없어 **layer 선택을 내용 사용성으로 해석할 수 없다**.

- frozen decoder + adapter-only 조건의 한계다. **Stage B(decoder LoRA)** 없이 layer를 버리면 안 된다.

- hidden T5Gemma2 sweep의 layer5 우위는 mT5 layer 선택에 전이되지 않았다: layer5 real CE 7.460, layer19 6.623.


## 5. 다음

- Stage B: real CE 상위권(layer19, 16, 13, 11, 9)과 비교군(layer5, 12)을 decoder LoRA로 재평가.
- UMT5-small Stage A를 동일 프로토콜로 실행해 mT5와 비교.
- Stage B에서도 shuffled 이득이 없으면 frozen/adapter-only 경로를 종료하고, decoder adaptation 또는 다른 memory interface를 검토.


## 6. 산출물

- `reports/provenance/C5_b1d/mt5_layer_probe.json`
- `reports/provenance/C5_b1d/mt5_layer_probe.log`
- `runner/c5_mt5_layer_probe.py`
- test 163 sealed
