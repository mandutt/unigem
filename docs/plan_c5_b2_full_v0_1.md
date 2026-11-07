# C5 B2 Full v0.1

## 목적

B2 pilot(20문서)에서 확인한 decoder LoRA + CE의 구조적 개선이 **full 1,293**에서도 유지되는지, 그리고 20문서 overfit이 해소되는지 확인한다.

## 범위

- init: `b1d_ce_pilot/adapter_final.pt`
- train **1,293**, val **161**
- 2 epoch = 2,586 step
- decoder base frozen
- decoder `q/k/v/o` LoRA r8 α16
- loss: CE + 0.01 hidden auxiliary
- optimizer: AdamW, lr 2e-4, wd 0.01
- **checkpoint every 100 step**
- **resume from latest step checkpoint**
- test 163 **미사용**
- human/AI panel 없음

## DoD

| 항목 | 기준 |
|---|---|
| train coverage | 1,293 × 2 epoch |
| checkpoint | 100 step 단위, resume 가능 |
| val CE | before/after 전체 161 |
| generation | val 161, EOS/반복/F1/grounded |
| test | 미사용 |

## 해석

- B2 full이 pilot보다 val CE를 낮추고 grounded를 개선하면 B2 계열 유지.
- 20문서 overfit이 full에서도 지속되면 데이터/objective 문제로 판단.
- test 163은 계속 sealed.

## 산출물

- `data/models/f5_t5gemma2_lora/b2_full/adapter_final.pt`
- `data/models/f5_t5gemma2_lora/b2_full/adapter_step_*.pt`
- `reports/provenance/C5_b1d/b2_full_metrics.json`
- `reports/provenance/C5_b1d/generation_val161_b2.jsonl`
- `reports/C5_B2_FULL_2026-11-07.md`
