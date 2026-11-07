# C5 B2 Decoder LoRA + CE Pilot v0.1

## 목적

B1d-CE pilot에서 남은 **반복·EOS 지연·환각**이 frozen decoder 때문인지 확인한다. B1d adapter는 유지하고, T5Gemma2 decoder attention에 LoRA를 추가해 adapter hidden을 decoder가 실제로 사용하도록 학습한다.

## 범위

- init adapter: `b1d_ce_pilot/adapter_final.pt`
- train 20 / val 20, 2 epoch
- decoder base **frozen**, LoRA만 trainable
- LoRA target: decoder `q_proj`, `k_proj`, `v_proj`, `o_proj`
- LoRA r8, alpha16, dropout 0.05
- loss: teacher-forced CE + hidden auxiliary 0.01
- test 163 **미사용**
- human/AI panel 없음

## DoD

| 항목 | 기준 |
|---|---|
| LoRA attach | decoder q/k/v/o에만 attach, encoder LoRA 없음 |
| trainable | adapter + decoder LoRA |
| val CE | before/after 기록 |
| generation | val20, EOS/반복/F1/grounded 기록 |
| 비교 | B1d-CE pilot과 동일 20문서 |
| test | 미사용 |

## 해석

- CE와 LoRA를 함께 학습했을 때 EOS율·repeated-4gram·char F1이 개선되는지 본다.
- 20문서 pilot은 품질 gate가 아니다.
- 개선되면 full 1,293 B2로 확장 여부를 별도 결정한다.
- test 163은 계속 sealed.

## 산출물

- `runner/c5_b1d_b2.py`
- `runner/c5_b1d_generate.py` (LoRA load 지원)
- `reports/provenance/C5_b1d/b2_pilot_metrics.json`
- `reports/provenance/C5_b1d/generation_val20_b2.jsonl`
- `reports/C5_B2_PILOT_2026-11-07.md`
