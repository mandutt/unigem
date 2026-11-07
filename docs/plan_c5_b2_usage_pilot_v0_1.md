# C5 B2 + Usage-Contrast Pilot v0.1

## 목적

B2 pilot에서 남은 **grounding 실패**가 “decoder가 adapter hidden을 충분히 사용하지 않기 때문”인지 검증한다.

LLINK의 usage-enforcing objective를 T5Gemma2 encoder-decoder에 맞게 변형한다.

## Usage-contrast

```text
L_with   = CE(H_s)
L_ctrl   = CE(mean_t(H_s) broadcast)   # 토큰별 문서 정보 제거
L_usage  = relu(L_ctrl - L_with + margin)
L_total  = L_with + λ_usage * L_usage + λ_hidden * L_hidden
```

- `H_s`가 실제로 문서별 정보를 전달하면 `L_ctrl > L_with + margin`이어야 한다.
- 그렇지 않으면 penalty.
- control은 `detach()`하여 gradient는 `L_with` 쪽으로만 흐른다.

## 범위

- init: `b2_pilot/adapter_final.pt` (adapter + decoder LoRA)
- train 20 / val 20, 2 epoch
- decoder base frozen; adapter + q/k/v/o LoRA trainable
- λ_usage = 0.5, margin = 0.5, λ_hidden = 0.01
- test 163 미사용

## DoD

| 항목 | 기준 |
|---|---|
| usage penalty | 기록 |
| val CE | before/after |
| generation val20 | EOS/반복/F1/grounded |
| 비교 | B2 pilot과 동일 20문서 |
| test | 미사용 |

## 해석

- usage-contrast가 grounded를 개선하면 B2 full로 확장.
- 개선이 없으면 B2 full 또는 B1d-CE full로 이동.
- 20문서 pilot은 품질 gate가 아니다.
