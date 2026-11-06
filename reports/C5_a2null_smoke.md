# C5 A2-null — smoke 기록

- 작성: 2026-11-06
- 상태: **feasibility + 2-step adapter smoke 완료, pilot extraction 진행 중**
- 원본: `reports/provenance/C5_a2null/nullspace_probe.json`

## 1. Null-space

| 항목 | 값 |
|---|---:|
| W shape | 768×512 |
| rank | 512 |
| nullity | 256 |
| `max|WᵀP|` | 4.29e-06 |
| final projection error | **0.0** |
| layer12 PCA256 | 95.1% (10건) |

- `P`는 W의 left null basis.
- `last_hidden_state = W @ norm(h_last)`를 forward hook으로 확인.
- null injection과 final의 dot max 0.00475.

## 2. T5 external memory

- T5Gemma2 decoder hidden 640.
- `BaseModelOutput(last_hidden_state=memory)` + `attention_mask`로 forward/backward 성공.
- 512d/768d memory는 거부, 640d만 허용.

## 3. Adapter 2-step smoke

- feature: 3 train records, layer12 PCA, null injection
- adapter: 768→768 GELU→640
- T5Gemma2 frozen (bf16), external memory 512 tokens, target 256
- 결과:

| step | loss | sec | RSS |
|---:|---:|---:|---:|
| 1 | 13.7150 | 0.96 | 2,628MB |
| 2 | 8.8715 | 0.95 | 2,585MB |

- NaN 없음; backward가 adapter까지 전달됨.
- **2 step은 품질 판정이 아니다.** loss 하락은 배치 암기 가능성만 보여준다.

## 4. Pilot extraction

- clean train 100 / val 100 / test 100 (debug limit)
- layer12 PCA 256: **94.29%** explained variance (50 records, 38,468 tokens)
- 파일: `data/wave2c/a2null_pilot/`
- 소요: **331.9초** (PCA 48초 포함)
- 전체 1,617 추출은 `data/wave2c/a2null/`에서 진행 중

## 5. 20-step adapter pilot

- train 100 features, max memory 1,024, target 512
- loss: **15.754 → 3.741** (20 step)
- step time: **1.87~2.24초** (평균 약 1.95초)
- RSS peak: **3,083MB**
- adapter: `data/models/f5_a2null_pilot/adapter_smoke.pt`

**해석:** 20 step·20 샘플 loss 하락은 배치 암기 가능성이 높다. 요약 품질·일반화 판정이 아니다. 다만 **A2-null adapter + T5 decoder의 forward/backward가 CPU에서 동작**하고, full train이 시간상 가능하다는 것은 확인했다.

## 6. Pilot generation

- pilot test 2건, `max_new_tokens=64`
- 결과: char F1 **0.0125**, grounded **0/2**, new slot rate **1.0**
- 출력이 `20일대양양양...`, `1 1 1...`처럼 붕괴했다.
- 원인: 20 step·20 샘플 adapter로는 생성 능력을 학습할 수 없다. **A2-null 자체의 실패로 해석하지 않는다.**
- 이 결과는 평가 하네스가 실제로 생성·슬롯 검증까지 연결된다는 것만 확인한다.

## 7. 다음

1. pilot feature로 20~50 step adapter 학습
2. full extraction (1,293/161/163)
3. A2-null-raw control (injection 없이 512→640)
4. A1 standard LoRA와 val 비교
5. test 163은 마지막 1회

## 6. 해석 주의

- 이 smoke는 **A2-null이 학습 가능**하다는 것만 확인했다.
- A1보다 요약이 잘 된다는 증거가 아니다.
- 원 Reddit 방법은 pooled audio embedding이고, A2-null-seq는 token-level text 확장이다.
