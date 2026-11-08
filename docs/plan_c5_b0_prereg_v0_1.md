# C5 B0 — EG2 layer19 → mT5 decoder adaptation 사전등록서 v0.1

- 작성일: 2026-11-09
- 상태: **사전등록 초안**. 학습·평가 **미실행**. 사용자 승인 전에는 B0를 시작하지 않는다.
- 상위 결정: D-112 (3-AI NARROW), D-113 (E0 tokenizer/wiring), D-114 (2-arm runner smoke PASS)
- 대상: EG2 native layer19 hidden → adapter → mT5-small decoder
- test 163: **sealed**. P1 데이터: 사용하지 않음. T5Gemma2: D-108 STOP 유지.

---

## 0. 한 줄 목적

> **mT5 decoder에 LoRA를 붙였을 때, EG2 layer19 memory의 *내용*을 실제로 더 잘 사용하는가?**
> 즉 **decoder adaptation이 병목이었는지**를, 같은 data·cache·seed의 frozen arm과 비교해 판정한다.

이 문서는 “F5 제품 품질”을 판정하는 문서가 아니다. **B0는 원인 분리 진단**이며, B1/B2/Stage C는 별도 결정이다.

---

## 1. 배경과 범위

### 1.1 확정된 사실

| 항목 | 결과 | 출처 |
|---|---|---|
| EG2 native layer19 cache | 300 train / 100 val, 512d, 401MB | D-113 |
| EG2 ↔ T5Gemma2 tokenizer | content ID 400/400 일치, 차이는 native EOS 1개 | D-113 |
| legacy vs native layer19 hidden | cosine train .99135 / val .99150 | D-113 |
| mT5 encoder vs external `encoder_outputs` | loss/logits delta 0.0 | E0 |
| mT5 decoder LoRA | 64/64 modules, zero-LoRA delta 0.0 | D-114 |
| Stage A | underfit screening; frozen decoder 병목의 인과 증거 아님 | D-110/111 + 3-AI review |

### 1.2 포함

- mT5-small, decoder q/k/v/o LoRA, adapter-only vs adapter+LoRA.
- native EG2 layer19 cache.
- 20 train / 20 val screening.
- 3 seeds.
- source-copyable target token 기준 selectivity.
- length-matched multiple donor.
- 문서 단위 cluster bootstrap.
- val20 generation sanity check.

### 1.3 제외

- B1 layer sweep, B2 mT5 vs UMT5, Stage C 300문서.
- test 163.
- P1 데이터, 외부 LLM API.
- 제품 승격, A1 native 대체.
- T5Gemma2 bridge 재개.
- layer role probing 전체 survey.

---

## 2. 설계 개요

```text
Stage B0-A  (screening, 이 문서의 승인 범위)
  20 train / 20 val, 2 arms, 3 seeds, 100 updates
  F = adapter-only, decoder frozen
  L = adapter + decoder q/k/v/o LoRA
        ↓
  POSITIVE_SIGNAL / INCONCLUSIVE / NO_SIGNAL
        ↓
Stage B0-B  (confirmatory, 별도 승인)
  300 train / 95 val, 4 arms, 3 seeds, ~900 updates
  F, L, P(native positive), M(memory-free/mean)
```

**중요**: B0-A는 **screening**이다. B0-A의 NO_SIGNAL을 “bridge 영구 종료”로 일반화하지 않는다. B0-B는 별도 사전등록·승인 후에만 실행한다.

---

## 3. 데이터와 cache

### 3.1 데이터

- 파일: `data/external/f5_pairs_v3_clean.jsonl`
- split: `reports/provenance/C5_clean/splits.json` (seed 42)
- **train20**: `split["train"][0:20]`
  - Stage A train 5개를 포함한다. 이는 **training 재사용**이며, B0-A의 목적이 새 layer 탐색이 아니라 decoder adaptation 진단이므로 허용한다.
- **val20**: `split["val"][5:25]`
  - Stage A가 사용한 val 앞 5개를 제외해 **Stage A val 문서 재사용을 피한다.**
- test 163: **사용하지 않음**
- target: gold summary
- prefix: `summarize: `
- source cap: native EG2 cache에 이미 적용된 **1,024 tokens**
- target cap: **256 tokens**

### 3.2 cache

- 경로: `data/wave2c/eg2_native_layer19/layer19`
- tokenizer: native EG2 `GemmaTokenizer`
- layer: 19, transformer, 512d
- cache meta: `tokenizer_path = data/models/embeddinggemma-2-f9972ac2`, `test_split_used: false`
- **legacy cache `data/wave2c/eg2_layer19`는 사용하지 않는다.**

### 3.3 모델

- `data/models/mt5-small`
- base encoder/decoder: **frozen**
- adapter: MLP 512→512→512 + LayerNorm
- decoder LoRA: `decoder.block.*.{SelfAttention,EncDecAttention}.{q,k,v,o}`
- LoRA r **8**, alpha **16**, dropout **0.05**
- LoRA attach assert: **64 modules**
- zero-output LoRA가 frozen forward와 일치해야 한다 (D-114에서 확인)

---

## 4. Arms

| arm | decoder | trainable | 목적 |
|---|---|---|---|
| **F (frozen)** | frozen | adapter only | 같은 data/cache/seed의 통제 |
| **L (lora)** | frozen base + LoRA | adapter + LoRA | decoder adaptation treatment |

### 4.1 B0-A에서 제외하는 arm

| arm | 왜 지금 제외 |
|---|---|
| P (native mT5 encoder + LoRA) | metric validity positive control. B0-B에서 추가 |
| M (memory-free / mean-memory) | negative control. B0-B에서 추가 |

**명시적 한계**: B0-A는 P/M이 없으므로 “LoRA가 content selectivity를 만들었다”는 **강한 인과 주장을 하지 않는다.** B0-A는 **F vs L의 방향성**과 **다음 단계 진행 여부**만 판정한다.

---

## 5. 학습 계약

| 항목 | 값 |
|---|---|
| optimizer | AdamW |
| adapter LR | **1e-3** |
| LoRA LR | **1e-4** |
| weight decay | 0.01 |
| gradient clipping | 1.0 |
| batch size | 1 |
| updates | **100** |
| epochs | 고정하지 않음 (step 기준) |
| checkpoint selection | **없음**. 마지막 step 하나만 평가 |
| early stopping | 없음 |
| dropout/eval mode | 학습 시 LoRA dropout, 평가 시 eval |
| seeds | **20261108, 20261109, 20261110** |

### 5.1 seed 규칙

- seed는 **arm과 독립**이다.
- 같은 seed의 F/L은 **동일 adapter 초기화, 동일 문서 순서, 동일 donor 배정**을 사용한다.
- seed를 layer에서 파생하지 않는다 (`20261108 + layer` 금지).

### 5.2 고정 하이퍼파라미터

B0-A 결과를 본 뒤 adapter/LoRA LR, rank, dropout, step 수를 바꾸지 않는다. 변경이 필요하면 **새 사전등록**이다.

---

## 6. Metric

### 6.1 Primary: `Δshuffled_copy`

문서 `i`, seed `s`, donor `d`에 대해:

```text
D[arm,s,i] = mean_d( CE[arm,s](wrong_d[:K], y_i_copy)
                    - CE[arm,s](real_i[:K], y_i_copy) )
```

- `K = min(recipient_length, donor_length)`; real과 wrong 모두 **같은 prefix K**로 crop.
- `y_i_copy`: target summary token 중 **source passage에 surface string이 존재하는 token**만.
  - special/pad/prompt token 제외.
  - tokenizer piece의 leading space를 제거한 뒤 source에 substring으로 존재하는지 확인.
  - copyable target token이 20개 미만인 문서는 **full target CE**를 secondary로 사용하고, copy coverage를 기록.
- donors: **5개**, length bucket matching, self/duplicate source 제외.
- same donor assignment across arms/seeds.

**Primary estimate**: 문서별로 seed와 donor를 평균한 뒤, 문서 단위 평균.

### 6.2 Secondary

| metric | 정의 |
|---|---|
| `Δshuffled_full` | full target CE의 shuffled − real |
| `Δzero` | zero memory − real. **진단용, 증거로 사용하지 않음** |
| `Δmean_memory` | train mean memory − real (가능하면) |
| `Δ_L_minus_F` | L의 `Δshuffled_copy` − F의 `Δshuffled_copy` |
| `real_ce` | real memory CE |
| copy coverage | copyable target token 비율 |

### 6.3 통계

- **문서 단위 cluster bootstrap**, 1,000회.
- 각 문서에서 seed/donor를 먼저 평균한 뒤 문서를 resample한다. token을 resample하지 않는다.
- seed별 평균과 범위를 별도 표기한다.
- 95% CI는 **paired document-cluster bootstrap**.
- 다중 비교는 B0-A에서 primary 1개만 사용하므로 보정하지 않는다. secondary는 exploratory로 표기한다.

### 6.4 Copy coverage guard

- 문서별 copyable target token이 **20개 미만**이거나, val20 전체의 median copy coverage가 **10% 미만**이면:
  - primary `Δshuffled_copy`를 **INCONCLUSIVE**로 표기한다.
  - full target CE는 exploratory secondary로만 보고한다.
  - copy coverage가 낮은 상태에서 `Δshuffled_copy`를 해석하지 않는다.

---

## 7. Generation sanity check

- val20 전체, 각 arm/seed.
- greedy decoding, `max_new_tokens=256`, native EOS.
- 기록:
  - nonempty
  - actual EOS
  - cap hit
  - repeated-4gram
  - char F1
  - grounded no-new (기존 metric)
  - generated length
- **gate가 아니다.** generation이 붕괴하면 metric 해석을 보류하고 별도 보고한다.

---

## 8. B0-A 판정

### 8.1 Primary decision

| 판정 | 조건 |
|---|---|
| **POSITIVE_SIGNAL** | mean `Δshuffled_copy` ≥ **.05**, document-cluster 95% CI lower > 0, **L > F** paired CI lower > 0, 2/3 seeds 양수 |
| **NO_SIGNAL** | mean `Δshuffled_copy` ≤ 0 **and** CI upper < .05 |
| **INCONCLUSIVE** | 그 외 |

### 8.2 해석 규칙

- **POSITIVE_SIGNAL**: B0-B(confirmatory)를 **새 decision으로 제안**할 수 있다. B1 자동 승인 아님.
- **INCONCLUSIVE**: B0-B 또는 더 강한 positive control이 필요하다. B1 자동 승인 아님.
- **NO_SIGNAL**: B0-A 조건에서는 decoder adaptation 신호가 없다. **bridge 전체의 영구 STOP으로 일반화하지 않는다.** B0-B 여부는 별도 판단.
- **기술 실패**(nonfinite, OOM, attach failure): 동일 config 1회 재시도. 두 번째 실패는 B0-A 중단.
- **B0-A 결과를 본 뒤 threshold를 바꾸지 않는다.**

---

## 9. B0-B (confirmatory, 별도 승인)

B0-A가 POSITIVE_SIGNAL 또는 INCONCLUSIVE일 때만 검토한다.

| 항목 | 값 |
|---|---|
| train / val | **300 / 95** (val[5:100], Stage A 5개 제외) |
| arms | F, L, **P(native mT5 encoder + LoRA)**, **M(memory-free/mean-memory)** |
| seeds | 20261108/09/10 |
| updates | ~900 (3 epoch 상당) |
| primary | `Δshuffled_copy` |
| positive control | P의 `Δshuffled_copy` CI lower > 0 |
| PASS | P valid + L CI lower >0 + L ≥ 25% of P + L>F + real<memfree |
| STOP | P valid + L upper < 10% of P |
| 그 외 | INCONCLUSIVE. 자동 B1 없음 |

B0-B는 이 문서의 승인 범위가 아니다. **별도 사전등록서와 사용자 승인**이 필요하다.

---

## 10. 구현 전제

현재 `runner/c5_mt5_lora_b0.py`는 F/L 학습·real/zero/shuffled ablation 경로와 아래 B0-A metric 경로를 갖는다. 구현 상태는 다음과 같다.

- [x] copyable target token mask
- [x] 5 length-matched donors + prefix crop
- [x] `Δshuffled_copy` aggregation
- [x] 문서×seed cluster bootstrap
- [x] val20 generation
- [x] B0-A 결과 JSON/provenance 경로
- [x] metric smoke (2 docs / 2 donors, no training)

이 항목을 구현하고 **2/2 smoke**를 통과한 뒤에만 B0-A를 실행한다.

---

## 11. 실행 순서

1. 사용자: 이 사전등록서 승인
2. 구현: metric, donors, bootstrap, generation
3. smoke: 2 train / 2 val, 2 step, F/L attach 및 metric 경로 확인
4. 사용자: B0-A 실행 승인
5. B0-A: 20/20, F/L, 3 seeds, 100 updates
6. 보고: `reports/C5_B0A_2026-11-09.md` + provenance JSON
7. 결과가 POSITIVE_SIGNAL/INCONCLUSIVE이면 **B0-B 별도 승인**
8. B1/B2/C는 B0-B 이후 별도 결정

---

## 12. 비용

| 단계 | 예상 |
|---|---:|
| 구현(metric/donor/bootstrap/generation) | **3~5시간** |
| smoke | **10~20분** |
| B0-A 실행 (6 runs × 100 updates + val/generation) | **45~90분** |
| B0-A 보고 | **30~60분** |
| **B0-A 총** | **5~7시간** |
| B0-B (별도) | **6~10시간** |

CPU only, no test, no P1.

---

## 13. 산출물

- `runner/c5_mt5_lora_b0.py` 확장
- `reports/provenance/C5_b0a/b0a_metrics.json`
- `reports/provenance/C5_b0a/predictions_val20.jsonl`
- `reports/provenance/C5_b0a/bootstrap.json`
- `reports/C5_B0A_2026-11-09.md`
- `docs/plan_c5_b0_prereg_v0_1.md` (이 문서)

---

## 14. 명시적 금지

- test 163 사용
- P1 데이터 사용
- B1/B2/Stage C 자동 진행
- B0-A 결과로 제품 후보 승격
- A1 native fallback 대체
- T5Gemma2 bridge 재개
- 결과를 본 뒤 threshold·seed·donor·step 변경
- `Δzero`를 content selectivity의 증거로 사용

---

## 15. 승인 요청

이 문서에서 승인할 범위:

```text
B0-A: 20 train / 20 val, F vs L, 3 seeds, 100 updates
+ 필요한 metric/donor/bootstrap/generation 구현
+ smoke 후 B0-A 실행
```

**B0-B, B1, B2, Stage C는 이 승인에 포함되지 않는다.**
