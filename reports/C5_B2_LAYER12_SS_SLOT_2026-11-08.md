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

| 항목 | 값 |
|---|---:|
| train CE before → after | 1.4011 → **1.1141** |
| val CE before → after | 2.2985 → **2.2406** |
| elapsed | **1,869.1s (31.2분)** |

- SS(2.2356)와 거의 동일; layer12 대비 −0.0579
- slot-aware가 teacher-forced val CE를 악화시키지는 않았다.

## 4. Teacher-forced fidelity (target=teacher)

| system | CE | token acc |
|---|---:|---:|
| B2 layer12 r8 | 2.1190 | 56.11% |
| B2 layer12 ss | 2.0335 | 57.46% |
| **B2 layer12 ss slot-aware** | **2.0339** | **57.51%** |

- SS와 거의 동일; slot-aware가 fidelity를 희생하지 않았다.

## 5. Free-running val100

| metric | layer12 r8 | ss | **ss slot-aware** |
|---|---:|---:|---:|
| char F1 | 0.3464 | 0.3783 | **0.4074** |
| teacher F1 | 0.3392 | 0.3696 | **0.4020** |
| grounded | 21% | 10% | **12%** |
| EOS | 60% | 59% | **69%** |
| rep4 | 0.588 | 0.4625 | **0.4054** |
| gen_len | 309.6 | 312.9 | 286.4 |
| new slot micro | **0.535** | 0.612 | 0.559 |
| preservation | 0.2512 | 0.3618 | **0.3656** |

- **F1 +0.0610**, teacher F1 +0.0628, rep4 −0.183, EOS +9%p
- grounded는 21% → 12%로 여전히 미달
- val100 1,233.8s

### Slot repair

| 방법 | grounded | char F1 | preservation |
|---|---:|---:|---:|
| 원본 | 12% | **0.4074** | 0.3656 |
| drop-new-sentences | **100%** | 0.3159 | 0.1621 |
| oracle subset | **100%** | **0.3203** | 0.1621 |

- grounded 100% F1 상한 **0.320**
- 원본 F1 .4074는 높지만, **grounded 12%**로 제품 불가

## 6. 판정

**SLOT_AWARE_SS_DOD_FAIL_GROUNDED**

사전 등록 DoD:

| 지표 | 기준 | 결과 | 판정 |
|---|---:|---:|---|
| val100 F1 | ≥ 0.36 | **0.4074** | PASS |
| grounded | ≥ 20% | **12%** | **FAIL** |
| EOS | ≥ 58% | **69%** | PASS |

- F1/EOS는 통과했지만 **grounded 12%**로 핵심 조건 미달
- slot-aware는 grounded를 10% → 12%로만 회복
- **사전 등록대로 bridge 계열 종료**
- 제품 후보 없음; **A1 native 제품 경로로 전환**
- test 163 sealed

## 7. 결론

- **A1 native**: F1 **0.6576**, grounded **100%**, EOS **100%**
- bridge 최고 F1: **0.4074** (grounded 12%)
- bridge 최고 grounded: **21%** (F1 .3464)
- slot repair 상한 F1: **0.320**
- **bridge는 A1 native를 대체할 수 없다.**

## 8. 산출물

- `data/models/f5_t5gemma2_lora/b2_layer12_300_ss_slot/adapter_final.pt`
- `reports/provenance/C5_b1d/b2_layer12_300_ss_slot_metrics.json`
- `reports/provenance/C5_b1d/b2_layer12_300_ss_slot_fidelity_teacher.json`
- `reports/provenance/C5_b1d/generation_val100_b2_layer12_300_ss_slot.jsonl`
- `reports/provenance/C5_b1d/slot_repair_ss_slot_val100.json`
- training 1,869.1s, val100 1,233.8s
