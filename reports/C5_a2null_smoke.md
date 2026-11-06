# C5 A2-null — smoke 기록

- 작성: 2026-11-06
- 상태: **1-epoch full adapter train 완료, val 생성 품질 미달**
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

## 7. Full extraction

- 완료: **1,293 train / 161 val / 163 test**
- layer12 PCA 200건, **94.10%** explained variance (152,846 tokens)
- feature: final 768 + null-injected PCA 256, float16, 1024 pad
- cache: `data/wave2c/a2null/` **2.4GB**
- meta: `reports/provenance/C5_a2null/features_meta.json`
- 검증: NaN 0, length train 629~910, val 622~865, test 665~875

## 8. 1-epoch full adapter train

- train **1,293**, val **161**
- steps **1,293**
- elapsed **2,646.1초 (44.1분)**
- train loss **3.2487**
- val loss **3.1196**
- step time **1.75~1.98초**
- final RSS **2,954.7MB**
- 산출물: `data/models/f5_a2null_full/{adapter.pt,last.pt,train_report.json}`

## 9. Val 생성 평가 (5건)

| 항목 | 값 |
|---|---:|
| char F1 평균 | **0.1603** |
| grounded rate | **0/5** |
| new slot rate 평균 | **0.9000** |

- 출력이 `10대 여성의 10대 여성의 ...`, `2019년 12월 15일, 1999년 ...`처럼 반복 붕괴했다.
- teacher-forced val loss 3.12는 생성 품질을 보장하지 않았다.
- **adapter-only 1 epoch로는 A2-null이 usable하지 않다.**
- EOS 수정 후 재학습 결과: char F1 **0.2297**, grounded **0/5**, new slot **0.96**, **5/5 eos 없음** → `reports/C5_a2null_eos_retrain.md`
- test 163은 사용하지 않았다.

## 10. 다음

1. A2-null-raw control (injection 없이 768→640)
2. adapter+decoder LoRA 또는 2 epoch 재학습 여부 결정
3. A1 standard LoRA와 val 비교
4. test 163은 마지막 1회

## 11. 해석 주의

- 이 문서의 full train 수치는 **label 결함 상태**다. target tokenizer의 `<bos>`를 label에 포함하고 `<eos>`를 넣지 않아 decoder가 정지 토큰을 배우지 못했다.
- 수정 label로 재학습하기 전까지 이 수치를 A2-null 성능 근거로 사용하지 않는다.
- 원인 조사와 Exa 근거: `reports/C5_a2null_search_2026-11-06.md`

- 이 smoke는 **A2-null이 학습 가능**하다는 것만 확인했다.
- A1보다 요약이 잘 된다는 증거가 아니다.
- 원 Reddit 방법은 pooled audio embedding이고, A2-null-seq는 token-level text 확장이다.
