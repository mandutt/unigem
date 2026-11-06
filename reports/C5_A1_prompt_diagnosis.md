# A1 prompt 일관성 진단 — 2026-11-06

- adapter: `data/models/f5_t5gemma2_lora/pilot100.pt` (100 step, lr 1e-3, bare passage 학습)
- val 5건 고정, greedy, max_new 448
- test 163 미사용

## 결과

| prefix | char F1 | grounded | EOS | repeated4 | distinct2 | mean len |
|---|---:|---:|---:|---:|---:|---:|
| **bare** | 0.4659 | 5/5 | 3/5 | 0.4860 | 0.4485 | 315.2 |
| **`summarize: `** | **0.6118** | 5/5 | **5/5** | **0.2166** | **0.6841** | 214.8 |
| **한국어 instruction** | 0.4027 | 3/5 | 5/5 | 0.3200 | 0.6209 | 181.6 |
| **`summarize: ` + 300 step lr2e-4 학습** | **0.6272** | **5/5** | **5/5** | **0.1004** | **0.7762** | 167.4 |

- `summarize: ` inference prefix만으로 **+0.1459** char F1 (bare → prefix)
- prefix 학습 300 step은 prompt-only 0.6118에서 **+0.0154**, repeated4 **0.2166→0.1004**, EOS 5/5 유지
- 한국어 prefix는 bare보다 낮고 grounded 3/5 → 이 모델에는 `summarize: `가 맞다

### prefix-trained pilot300의 bare 입력 확인

pilot300 adapter(prefix 학습)를 **prefix 없이** 같은 val 5건에 적용:

| 입력 | char F1 | grounded | EOS | repeated4 | len |
|---|---:|---:|---:|---:|---:|
| bare | **0.6522** | 5/5 | **5/5** | 0.0407 | 264.0 |
| `summarize: ` | 0.6272 | 5/5 | 5/5 | 0.1004 | 167.4 |

→ prefix를 학습에 넣어도 **bare 입력에서 요약이 유지**된다. prefix가 필수 조건은 아니며, target 분포 자체가 요약 task를 학습시킨다. 단, 다른 task에 이 F5 adapter를 재사용하면 요약 쪽으로 편향될 수 있으므로 **task별 adapter 분리**가 필요하다.

## 해석

1. **prompt mismatch가 A1 pilot 반복의 큰 부분이다.** adapter는 bare passage로 학습됐지만, T5Gemma2의 공식 summarization prompt는 `summarize: `다. inference에서 prefix만 바꿔도 EOS와 반복이 크게 개선됐다.
2. **prefix를 학습 input에도 넣으면 추가 개선된다.** pilot300 lr2e-4 prefix는 pilot100 prefix보다 char F1 +0.0154, repeated4 -0.116, 길이 167.4로 더 안정적이다.
3. **한국어 instruction prefix는 이 모델에 맞지 않는다.** 270M pretrained T5Gemma2는 한국어 instruction-tuned가 아니며, 영어 `summarize:`가 더 안정적이다.
4. **full val 161 비교는 아직 없다.** 이 표의 n=5는 sanity이며, A1이 A0(.5981)보다 우수하다고 확정할 수 없다.

## 다음

- full train(2~3 epoch) 전에 **val 161 batch evaluator**가 필요하다
- full train 승인 시 `summarize: ` prefix, lr 2e-4, r8 attention LoRA를 기본 조건으로 둔다
- test 163은 최종 후보 1회만

## Artifacts

- `reports/provenance/C5_a1/prompt_bare/eval.jsonl`
- `reports/provenance/C5_a1/prompt_summarize/eval.jsonl`
- `reports/provenance/C5_a1/prompt_korean/eval.jsonl`
