# C5 B2 teacher KD 100 + B2 gold 100 matched control (v0.1)

## 1. 목적

adapter-only teacher fidelity의 후속.

- adapter-only에서는 teacher-forced token accuracy가 43.6%에 그쳤고,
  teacher hidden control은 87.5%였다.
- T5Gemma2 decoder가 adapter content를 사용하지만 teacher hidden에는 크게 미달한다.
- teacher target은 gold보다 extractive/leading 편향이 있다
  (copy4 84.4% vs 66.2%, leading 56.9% vs 52.4%).

이 실험은 두 가지를 분리한다.

1. **decoder LoRA**가 adapter content를 더 잘 사용하게 만드는가?
2. **teacher target**이 gold target보다 나은가, 아니면 teacher bias를 전이하는가?

## 2. 설계

| 항목 | teacher arm | gold arm |
|---|---|---|
| init | `b1d_teacher100/adapter_final.pt` | 동일 |
| train | 99 (teacher new-slot 1건 제외) | 동일 99 |
| val | 100 | 동일 100 |
| trainable | adapter + decoder q/k/v/o LoRA | 동일 |
| LoRA | r8 α16 dropout .05, 72 modules | 동일 |
| target | **teacher output** | **gold summary** |
| loss | CE + 0.01 hidden | 동일 |
| epoch | 2 | 2 |
| lr | 3e-4 | 3e-4 |
| test 163 | 미사용 | 미사용 |

matched control이므로 **target만 다르다.**

## 3. 평가

Teacher-forced:
- train/val CE
- (후속) token accuracy

Free-running:
- val20 screen
- char F1 vs gold
- teacher char F1
- grounded
- EOS
- rep4 / distinct-2 / gen_len

## 4. 해석 규칙

- teacher arm이 gold arm보다 free-running 좋음 → teacher KD 유효
- teacher arm이 teacher-forced CE는 좋지만 free-running 나쁨 → decoder/exposure bias
- teacher arm이 extractive/leading bias를 더 보임 → teacher target bias 전이
- 두 arm 모두 낮음 → capacity/data 문제

## 5. 비용

- 각 arm 198 step, 약 15~25분
- val20 generation 각 5~10분
- 총 40~60분 (CPU)

## 6. 산출물

- `data/models/f5_t5gemma2_lora/b2_teacher100/adapter_final.pt`
- `data/models/f5_t5gemma2_lora/b2_gold100/adapter_final.pt`
- `reports/provenance/C5_b1d/b2_teacher100_metrics.json`
- `reports/provenance/C5_b1d/b2_gold100_metrics.json`
- `reports/provenance/C5_b1d/generation_val20_b2_teacher100.jsonl`
- `reports/provenance/C5_b1d/generation_val20_b2_gold100.jsonl`
- `reports/C5_B2_TEACHER100_2026-11-07.md`
