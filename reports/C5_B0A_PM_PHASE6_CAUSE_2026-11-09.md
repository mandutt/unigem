# C5 Phase 6 P/M — Signal Collapse Cause Analysis

- 분석일: 2026-11-09
- 입력: registered 3-seed final checkpoints + per-doc eval + M records
- 추가 학습: **없음**
- test 163: **sealed**
- P1: **unused**
- 결론: **native 경로에서 adapter 부착과 연관된 donor-specific signal 소실**. EG2 전체 일반화와 구조적 bottleneck 인과는 미확립.

## 1. 관찰

### L signal

| 항목 | 값 |
|---|---:|
| `L_COPY_SIGNAL` | **false** |
| mean Δ copy | **-0.1135** |
| 95% CI | [-0.2341, -0.0012] |
| positive docs | **6/15** |
| seed means >0 | **0/3** |
| `L_FULL_SIGNAL` | **false** |
| mean Δ full | **-0.1085** |
| positive docs | 6/15 |

- L의 real memory는 wrong-donor memory보다 낫지 않습니다.
- 3 seeds 모두 평균이 음수입니다.
- tail top3는 모두 음수이고, top3 제거 후에도 mean **-0.0279**로 음수입니다. 즉 **일부 outlier만의 문제가 아니라 broad negative**입니다.

### M은 통과

| arm | M control-real Δ | wrong-real Δ | ratio |
|---|---:|---:|---:|
| F | 0.576 | 0.001 | 0.001 |
| L | 0.365 | -0.017 | -0.046 |
| P | **6.118** | **2.531** | **0.414** |
| PA | 0.576 | 0.013 | 0.022 |

- M gate는 `real vs global mean`을 봅니다.
- L/F/PA는 real과 wrong donor 모두 global mean보다 좋지만, **wrong donor가 real과 거의 동일**합니다.
- P만 real이 wrong donor보다 명확히 좋습니다.
- 따라서 **M_PASS와 L_SIGNAL false는 모순이 아닙니다.** M은 donor specificity를 요구하지 않습니다.

## 2. 분리 실험

### LoRA 효과 — 거의 없음

- F(adapter only) vs L(adapter+LoRA):
  - 15-doc seed-average paired contrast **-0.0026**
  - 8/15 positive
  - 60 seed-doc pairs mean -0.0224, 30/60 positive
- L−F contrast ~0 → **decoder LoRA가 signal을 만들거나 없애지 않음**.

### Adapter 효과 — 결정적

- P(native, no adapter) vs PA(native + adapter + LoRA):
  - 15-doc seed-average paired contrast **+3.065**
  - **14/15 positive**
  - P copy Δ mean **3.076** vs PA **0.011**
- P와 PA는 **adapter 유무만 다릅니다**. 둘 다 native mT5, decoder LoRA, 100 updates, 3 seeds.
- **adapter를 넣으면 signal이 3.08 → 0.01로 사라집니다.**

### EG2 adapter 특성

15 val common docs의 mean-token vector 기준:

| representation | between-doc variance | mean pair distance | centered cosine |
|---|---:|---:|---:|
| raw EG2 layer19 | **4.883** | **3.142** | -0.068 |
| F adapter on EG2 | **0.085** | 0.418 | -0.068 |
| L adapter on EG2 | **0.081** | 0.405 | -0.067 |
| native raw | 0.841 | 1.324 | -0.069 |
| PA adapter on native | 1.284 | 1.623 | -0.067 |

- F/L adapter는 EG2 feature의 between-doc variance를 **98% 이상 감소**시킵니다 (4.883→0.085).
- PA adapter는 variance를 오히려 키우지만, decoder-usable donor specificity는 사라집니다.
- 따라서 “단순 global collapse” 하나로 설명되지 않습니다. 공통 원인은 **adapter가 decoder에 유용한 content-specific 성분을 보존/정렬하지 못하는 것**입니다.

## 3. 배제된 대안

| 가설 | 판정 | 근거 |
|---|---|---|
| decoder LoRA가 원인 | **기각** | P는 LoRA가 있어도 signal 3.08; L−F ~0 |
| EG2 layer19 단독 원인 | **기각/부분** | PA는 native에서도 adapter 추가 시 signal 0.01 |
| donor crop length | **기각** | P/PA는 K=512 고정, PA도 0.01 |
| copy mask / copy token 부족 | **기각** | coverage 0.8 수준, endpoint_ok 1,680 모두 true |
| bootstrap/seed noise | **기각** | 3/3 seed mean negative, CI upper <0 |
| M endpoint 실패 | **기각** | M_PASS all arms true |
| tail-only outlier | **기각** | top3 제거 후에도 mean -0.0279 |

## 4. 메커니즘 — 가설적 설명 (인과 확정 아님)

가장 일관된 **가설**:

1. **Adapter training on 20 train docs**가 decoder에 대해 “global mean보다 나은” generic shift를 학습합니다.
2. 이 shift는 **real vs global mean**에서는 충분히 커서 M_PASS를 만듭니다.
3. 그러나 **real vs wrong donor**에서는 두 memory가 같은 generic shift를 공유하므로 차이가 사라집니다.
4. F/L에서는 adapter가 EG2 feature variance를 강하게 압축해 이 효과가 두드러집니다.
5. PA에서는 variance는 유지되지만 decoder가 adapter 출력의 donor-specific 성분을 사용하지 않습니다.
6. P는 adapter 없이 native encoder feature를 decoder가 직접 사용하므로 donor-specific signal이 살아 있습니다.

## 5. 결론

- **P/PA native 경로에서는 adapter 부착 시 donor-specific signal이 소실된다.**
- LoRA는 이 실험의 주원인이 아닙니다.
- EG2/F-L로의 일반화는 **미확립**입니다. F/L vs P/PA는 memory source도 다릅니다.
- “bottleneck”은 구조적 진단명이 아니라 **관찰된 adapter-associated signal loss**로 한정합니다.
- Adapter는 512→512이며 width bottleneck이 아닙니다. LayerNorm/input-insensitive mapping, optimization interference, decoder off-manifold 중 어느 것인지 미분리.
- variance contraction은 원인 증거가 아닐 수 있습니다. centered cosine/CV/eff_rank는 거의 동일하고 raw EG2도 이미 mean cosine 0.998입니다.
- M gate는 donor specificity를 측정하지 않으므로 **M_PASS ≠ content-use signal**입니다.
- B0-B candidate gate false는 **측정 오류가 아니라 signal 부재**로 해석됩니다.

## 6. 다음 실험 제안 — 새 prereg 필요

현재 결과에 맞춰 threshold/seed/donor/step/LR을 바꾸는 것은 금지입니다. 별도 prereg로만:

### H1. Adapter-free EG2 arm (F0)

```text
F0 = EG2 layer19 raw 512 -> mT5 decoder LoRA only (no adapter)
```

- P와 동일한 decoder LoRA, native 대신 EG2 raw memory.
- 목적: EG2 raw feature가 donor-specific signal을 보존하는지.
- 예상 분기:
  - F0 signal positive → adapter가 원인 확정.
  - F0 signal ~0 → EG2 layer19 feature 자체가 부족.

### H2. Native no-adapter 대조

- P는 이미 positive control로 존재.
- PA는 adapter 추가 시 signal 소멸.
- H1과 P를 결합하면 memory source와 adapter를 2×2로 분리할 수 있습니다.

### H3. Adapter 구조/학습 변경 (별도 prereg)

- residual adapter (`x + α·Adapter(x)`)로 identity 보존
- adapter capacity/LR/step 고정 비교
- auxiliary reconstruction/contrastive loss
- 단, **현재 결과를 보고 threshold를 맞추는 것은 금지**

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `reports/provenance/C5_b0a/labels/cause_analysis.json` | per-doc, P/PA contrast, collapse metrics |
| `reports/provenance/C5_b0a/labels/cause_centered.json` | centered cosine/variance metrics |
| `reports/C5_B0A_PM_PHASE6_LABELS_2026-11-09.md` | label/replay 원본 |

## 8. 경계

```text
B0-B = 미승인 (candidate false)
B1/B2/Stage C = 미승인
test 163 = sealed
P1 = unused
T5Gemma2 = D-108 STOP
```

- 이 분석은 **원인 진단**이며 새 실험 승인이 아닙니다.
- H1/H2/H3는 **새 prereg + 별도 승인**이 필요합니다.

## 9. MF-3 correction (post-review)

- 3-AI review (GLM/DS1017/Sol) 판정: “adapter bottleneck”은 **P/PA native 경로의 관찰**로는 지지되지만, EG2/F-L 전체 일반화·구조적 bottleneck·variance 인과는 미확립.
- DS 지적: Adapter는 512→512로 width bottleneck이 아니며, LayerNorm/input-insensitive mapping/optimization interference/decoder off-manifold가 분리되지 않았다.
- Sol 지적: mean-vector variance contraction은 information destruction의 증거가 아니다.
- 따라서 이 보고서의 결론을 **adapter-associated donor-specific signal loss (native path)**로 한정한다.
- 수치(L signal, tail, P/PA contrast, M table)는 변경하지 않는다.
- 후속 F0 prereg에서 adapter × LoRA 2×2, projection/residual/null control로 원인을 분리한다.
