# C5 B2 layer12 slot-aware scheduled sampling (2026-11-08)

## 1. 목적

SS가 F1/rep4를 개선했지만 grounded가 21% → 10%로 하락했다.
**slot/number/EOS token을 corruption에서 제외**해
F1 이득을 유지하면서 grounding을 회복할 수 있는지 확인한다.

## 2. 사전 등록

- base: **B2 layer12 512 + MLP1536, decoder LoRA r8**
- init: `b2_layer12_300/adapter_final.pt`
- train 300 / val 100, 1 epoch, lr 1e-4
- `ss_prob=0.2`
- **slot-aware**: 다음 target token은 corruption 금지
  - `extract_slots`의 모든 slot span
  - 숫자를 포함한 token
  - EOS
- labels는 gold 유지

DoD:

| 지표 | 기준 |
|---|---:|
| val100 F1 | **≥ 0.36** |
| grounded | **≥ 20%** |
| EOS | **≥ 58%** |

- test 163 미사용

## 3. 학습 결과

**진행 중**.

## 4. Teacher-forced fidelity

**진행 중**.

## 5. Free-running val100

**진행 중**.

## 6. 판정

**pending**.

## 7. 산출물

- `data/models/f5_t5gemma2_lora/b2_layer12_300_ss_slot/`
- `reports/provenance/C5_b1d/b2_layer12_300_ss_slot_metrics.json`
