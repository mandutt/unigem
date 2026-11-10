# C5 F5.0 — A1 Checkpoint Comparison (2026-11-10)

- 상태: **ANALYSIS_ONLY / NO_REGENERATION**
- 대상: pilot300 + full2ep 647/1,293/1,940/2,586
- split: val **161**; test 163 미사용
- 학습/생성: **없음**

## 0. 결론

A1을 더 학습하면 abstractness가 **어느 정도 개선되지만, 충분하지 않고 단조롭지도 않다.**

- **pilot300**: copy8 **0.7300**, novel4 **0.1109**
- **full 1,940**: copy8 **0.6434**, novel4 **0.1630** ← 가장 추상적
- **full 2,586**: copy8 **0.7354**, novel4 **0.1154** ← final epoch에서 다시 추출 쪽으로 퇴행

target은 copy8 **0.4980**, novel4 **0.2687**이다.
가장 좋은 1,940도 target보다 copy8이 **+0.1455**, novel4가 **−0.1058**로
여전히 **extract-biased**다.

즉 **“더 오래 학습 = 더 추상적”이 아니다.**  
F5.1은 checkpoint selection에 abstractness를 넣어야 하며, final checkpoint를 자동 선택하면 안 된다.

## 1. 비교표

| checkpoint | n | char F1 | copy8 | novel4 | slot pres. | rep4 | grounded | EOS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| pilot300 | 161 | 0.6576 | 0.7300 | 0.1109 | 0.4558 | 0.0554 | **1.0000** | **1.0000** |
| full 647 | 161 | 0.6699 | 0.6710 | 0.1498 | 0.4873 | 0.0684 | 0.9627 | 0.9938 |
| full 1,293 | 161 | 0.6659 | 0.6979 | 0.1348 | 0.4571 | 0.0587 | 0.9876 | 1.0000 |
| **full 1,940** | 161 | **0.6823** | **0.6434** | **0.1630** | 0.4761 | 0.0514 | 0.9814 | 1.0000 |
| full 2,586 | 161 | 0.6690 | 0.7354 | 0.1154 | 0.4188 | 0.0445 | 0.9876 | 1.0000 |
| **target** | 161 | — | **0.4980** | **0.2687** | — | — | — | — |

## 2. Abstractness gap

| checkpoint | copy8 − target | novel4 − target |
|---|---:|---:|
| pilot300 | **+0.2321** | **−0.1579** |
| full 647 | +0.1731 | −0.1190 |
| full 1,293 | +0.1999 | −0.1340 |
| **full 1,940** | **+0.1455** | **−0.1058** |
| full 2,586 | +0.2375 | −0.1533 |

- 1,940이 target에 가장 가깝다.
- 그러나 target copy8 0.498과 비교하면 여전히 **29% 더 추출적**이다.
- 2,586은 pilot300보다도 copy8이 높다. **final epoch는 abstraction 관점에서 최악**이다.

## 3. 오류 flags

| checkpoint | high copy8 | low slot | high rep | low F1 |
|---|---:|---:|---:|---:|
| pilot300 | 45 | 21 | 19 | 12 |
| full 647 | 21 | 13 | 32 | 5 |
| full 1,293 | 30 | 17 | 26 | 10 |
| **full 1,940** | **12** | 14 | 23 | 4 |
| full 2,586 | 51 | 25 | 14 | 12 |

- 1,940은 high-copy 문서가 12건으로 가장 적고, low-F1도 4건으로 가장 적다.
- 2,586은 high-copy 51건, low-slot 25건으로 다시 악화된다.
- 647은 repetition 32건으로 가장 나쁘다.

## 4. 해석

1. **abstractness는 학습 중 개선될 수 있다.**
   - 1,940에서 copy8 0.6434, novel4 0.1630.
   - pilot300 대비 copy8 −0.0866, novel4 +0.0521.

2. **그러나 final epoch는 퇴행한다.**
   - 2,586 copy8 0.7354, novel4 0.1154.
   - “마지막 checkpoint = 최선”이라는 가정이 틀렸다.

3. **grounded와 abstractness가 trade-off다.**
   - pilot300: grounded 1.0, copy8 0.7300
   - 1,940: grounded 0.9814, copy8 0.6434
   - 2,586: grounded 0.9876, copy8 0.7354
   - grounded만 최적화하면 late checkpoint가 선택되고, abstractness는 나빠진다.

4. **target 수준에는 아직 도달하지 못했다.**
   - best copy8 0.6434 vs target 0.4980.
   - best novel4 0.1630 vs target 0.2687.
   - 따라서 “A1이 abstract summary를 한다”고 아직 말할 수 없다.

5. **F5.1은 multi-objective selection이 필요하다.**
   - grounded/EOS만 gate로 쓰지 않는다.
   - copy8/novel4를 checkpoint selection에 포함한다.
   - human rubric로 “어느 정도 copy까지 허용할지”를 정한다.

## 5. 권고

### 즉시

- **full 1,940을 abstractness diagnostic candidate로 사용**한다.
  - 제품 후보 아님: grounded 158/161.
- **full 2,586을 abstractness 후보로 사용하지 않는다.**
- pilot300은 safety baseline으로만 유지한다.

### F5.1

1. 1,940 예측에 대해 사람 40~50건 rubric
   - high-copy / low-slot / high-rep / low-F1 strata 포함
2. copy8/novel4를 checkpoint selection metric에 추가
3. “final epoch 자동 선택” 금지
4. abstractness 개선 실험은 **copy penalty / target style / decoding / early stop** 중 하나씩
5. bridge(EG2 adapter/LoRA)는 native abstractness가 target에 가까워진 뒤에만

### 판정

```text
best_abstractness_checkpoint = full_1940
still_extract_biased = true
target_gap_copy8 = +0.1455
target_gap_novel4 = -0.1058
product_candidate = none
```

## 6. Artifacts

- comparison JSON: `reports/provenance/C5_f5_0/checkpoint_compare.json`
  - SHA256 `f0a32183f5c7efd9264315c8c5c8fd45893d39456c79382a65e0f87c5a4b2c36`
- script: `runner/c5_f5_0_checkpoint_compare.py`
- inputs:
  - `reports/provenance/C5_a1/pilot300_val161/predictions.jsonl`
  - `reports/provenance/C5_a1/full_2ep/eval_step_{0647,1293,1940,2586}/eval.jsonl`
