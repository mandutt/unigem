# C5 B2 + Usage-Contrast Diagnostic (2026-11-07)

## 0. 결론

**Usage-contrast는 이 실패의 병목이 아니다.**

- mean hidden control: gap이 너무 커서 penalty가 무의미
- 다른 문서 H_s control:
  - train usage gap **1.936**
  - val usage gap **0.744**
- margin 0.5 기준 **penalty = 0** (train/val 모두)
- 즉 decoder는 H_s의 **문서별 정보를 이미 사용**하고 있다.
- 따라서 “decoder가 H_s를 무시한다”는 가설은 이 control에서는 기각된다.

## 1. 왜 mean control을 버렸나

처음 LLINK식 zero/mean control을 넣었더니:

| control | CE | gap |
|---|---:|---:|
| real H_s | 1.36 | — |
| token-mean H_s | 3.78 | +2.42 |

penalty `relu(gap + margin)`가 항상 큰 값이라 **상수**가 되고 gradient가 없었다.  
그래서 control을 **다른 문서의 H_s**로 바꿨다. 이는 같은 분포·같은 norm이지만 문서 내용이 다른 control이다.

## 2. 다른 문서 control 결과

2문서 smoke:

| split | CE(real) | CE(other-doc) | gap | penalty (margin .5) |
|---|---:|---:|---:|---:|
| train before | 1.395 | 3.331 | **1.936** | **0.000** |
| val before | 3.245 | 3.989 | **0.744** | **0.000** |
| train after | 0.992 | 3.289 | 2.296 | 0.000 |
| val after | 3.374 | 4.140 | 0.766 | 0.000 |

- train gap 1.94 > margin 0.5
- val gap 0.74 > margin 0.5
- **usage penalty가 한 번도 활성화되지 않음**
- adapter H_s를 다른 문서 것으로 바꾸면 CE가 크게 나빠짐
- 즉 **decoder는 H_s를 문서별로 사용하고 있다.**

## 3. 해석

LLINK의 “decoder ignores the vector” 문제는 **우리 B2에는 해당하지 않는다.**

남은 문제는 usage가 아니라:

1. **adapter hidden의 내용 품질**
2. **20문서 overfit**
3. **grounding/복사 능력 부족**
4. **decoder LoRA의 일반화 부족**

이다.

따라서 usage-contrast를 full로 돌리는 것은 의미가 낮다. penalty가 0이면 B2 CE 학습과 동일하고, 20문서를 더 overfit시킬 뿐이다.

## 4. 다음 선택

### B2 full — 1,293 × 2 epoch (권장)

- 20문서 overfit을 full 데이터로 해소
- B2 pilot에서 EOS 0.40, repeated-4gram 0.649까지 개선된 방향을 유지
- grounding이 full에서 개선되는지 확인
- CPU 수 시간

### Teacher sequence-level KD

- T5Gemma2 native teacher가 생성한 요약을 target으로 사용
- gold summary CE보다 **teacher의 문장 습관**을 더 잘 distill
- adapter + frozen/LoRA decoder에 CE
- test 163 미사용

### Slot-constrained decoding

- 생성 후 `eval.slot_verify`로 new slot을 차단하거나 repair
- 제품 안전장치로는 유효
- 근본 생성 능력 개선은 아님

## 5. 상태

| 항목 | 값 |
|---|---|
| usage-contrast diagnostic | **inactive (penalty 0)** |
| decoder H_s usage | **문서별 사용 확인** |
| full usage run | **미실행 (중단)** |
| B2 full | 미실행 |
| test 163 | **sealed** |
| human/AI panel | 중단 유지 |

## 6. 산출물

- `runner/c5_b1d_b2_usage.py`
- `reports/provenance/C5_b1d/b2_usage_smoke_metrics.json`
- `reports/provenance/C5_b1d/b2_usage_smoke_stdout.txt`
- 이 문서
