# C5 B0-A Phase 6 — P/M Bounded Diagnostic Preregistration v0.1

- 작성일: 2026-11-09
- 상태: **사전등록 초안. 실행 미승인.**
- 상위 계획: `docs/plan_c5_b0a_repair_v0_1.md`
- 선행 결과:
  - B0-A 3-AI review: NARROW 3/3 (D-117)
  - CE alignment defect confirmed (D-117)
  - repair phases 1~4 (D-118)
  - P0 native sanity: SENSITIVE_POSITIVE train/val (D-119)
- test 163: **sealed**
- P1 데이터: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- B0-B / B1 / B2 / Stage C: **미승인**

---

## 1. 목적

Phase 6는 **B0-B 300/95가 아니다.** 20 train / 20 val에서 다음을 분리하는 bounded diagnostic이다.

1. **P (native positive control)**
   - native mT5 encoder memory + decoder LoRA가 corrected metric에서 양성 selectivity를 만드는가?
2. **M (mean-memory negative control)**
   - L arm의 real memory가 **target-independent mean memory**보다 실제로 더 좋은가?
3. **F/L**
   - repaired metric·mode에서 EG2 layer19 memory + decoder LoRA의 signal이 남아 있는가?

핵심 질문:

> **“metric은 작동하고, native positive control은 양성이며, L의 real memory가 mean memory보다 나은가?”**

이 질문에 답하지 못하면 B0-B로 확대하지 않는다.

---

## 2. Arm 정의

### 2.1 F — frozen adapter-only

- memory: EG2 native layer19 cache 512d
- adapter: 2-layer MLP + LayerNorm, 526,336 params
- decoder: frozen, **eval mode**
- trainable: adapter only
- LoRA: 없음
- training: 20 docs, 100 updates, seed별

### 2.2 L — adapter + decoder LoRA

- memory: EG2 native layer19 cache
- adapter: F와 동일 초기화·동일 seed
- decoder: frozen base, **eval mode**
- LoRA: decoder self/cross q/k/v/o, **64 modules**, r8 α16 dropout .05
- trainable: adapter + LoRA
- training: 20 docs, 100 updates, seed별
- mode: base eval, adapter+LoRA train

### 2.3 P — native mT5 encoder + decoder LoRA

- memory: **native mT5 encoder** on `summarize: ` + source passage
- adapter: **사용하지 않음**
- decoder: frozen base, **eval mode**
- LoRA: decoder q/k/v/o, **64 modules**, r8 α16 dropout .05
- trainable: LoRA only
- training: 20 docs, 100 updates, seed별
- evaluation: native val source memory vs **length-matched native donor source**
- P의 역할: **metric/decoder-LoRA 양성 통제** (EG2 bridge 성능 주장 아님)

### 2.4 M — mean-memory negative control

M은 별도 학습 arm이 아니다.

- 각 L checkpoint에서 val20을 평가할 때 memory를 **training-only mean memory**로 교체한다.
- mean memory는 **train 20 문서의 memory만** 사용해 만든다.
- target 문서의 내용·summary·label은 mean 계산에 사용하지 않는다.
- mean memory는 target length K에 맞춰 repeated/cropped된다.
- 비교:
  - `real_ce_copy`: L의 real memory
  - `mean_ce_copy`: mean memory
  - `Δmemfree_copy = mean_ce_copy − real_ce_copy`
  - positive = real memory가 mean보다 낮은 CE

M은 **L의 content-use negative control**이다. M을 별도로 100-step 학습하지 않는 이유는 compute cap과 “mean 자체가 target-specific content를 갖지 않게” 하기 위해서다. 별도 trained M arm은 B0-B 이후 새 사전등록 대상이다.

---

## 3. Mean-memory 정의

L checkpoint의 adapter를 `A`라 하자.

1. train 20 문서의 EG2 memory `h_i`를 `A(h_i)`로 변환한다.
2. target val 문서의 real memory length를 `K`라 한다.
3. `len(h_i) >= K`인 train 문서만 사용한다.
4. `mean_mem[0:K] = mean_i A(h_i)[0:K]`.
5. `mean_mem`을 decoder cross-attention memory로 사용한다.
6. 사용한 train 문서 수가 **10 미만**이면 해당 doc은 M 평가에서 제외하고 `m_eligible=false`로 기록한다.

P의 M probe는 native encoder train memory에 같은 규칙을 적용한다. F의 M probe는 F adapter 출력에 적용한다.

### 금지

- val 문서를 mean 계산에 사용하지 않는다.
- target summary/label을 mean 계산에 사용하지 않는다.
- donor를 mean 계산에 사용하지 않는다.
- mean을 real memory와 섞지 않는다.

---

## 4. 데이터·split

| 항목 | 값 |
|---|---|
| train | `split["train"][0:20]` |
| val | `split["val"][5:25]` |
| seeds | **20261108 / 20261109 / 20261110** |
| donors | 5, length-nearest, prefix crop `K=min` |
| target max length | 256 |
| source max length (P) | 256 |
| test 163 | **미사용** |
| P1 | **미사용** |

F/L/P는 같은 20 train 문서와 같은 20 val 문서를 사용한다. M은 train 20에서만 mean을 만든다.

---

## 5. Corrected metric

### 5.1 CE

- `token_losses`는 **same-position** `logits[t]` vs `labels[t]`를 사용한다.
- `Δshuffled_copy = mean(wrong_copy_ce − real_copy_ce)`
- `Δshuffled_full = mean(wrong_full_ce − real_full_ce)`
- positive = real memory가 더 좋음

### 5.2 Copy mask

- as-run mask를 primary로 사용하되, **coverage와 upper bound를 함께 보고**한다.
- `piece_len >= 2` strict mask는 **exploratory secondary**로만 보고한다.
- Phase 6에서 mask rule을 바꾸지 않는다.
- mask upper-coverage warning: median > .90이면 exploratory로 표시.

### 5.3 M

- `Δmemfree_copy = mean_ce_copy − real_ce_copy`
- `Δmemfree_full = mean_full_ce − real_full_ce`
- positive = real memory가 mean memory보다 좋음

---

## 6. 통계·판정

### 6.1 Bootstrap

- 문서 단위 paired bootstrap 1,000회
- seed별 결과를 별도 표로 보고
- pooled mean은 seed 평균을 먼저 만든 뒤 문서 단위로 계산
- seed variability를 별도로 표기

### 6.2 사전등록 판정

#### P validity

```text
P_POSITIVE = mean Δshuffled_copy > 0
             AND bootstrap CI lower > 0
```

P가 `P_POSITIVE`가 아니면:

- assay/decoder-LoRA validity 실패로 기록
- B0-B/B1/B2/C 금지
- P 실패를 bridge STOP으로 일반화하지 않음

#### L signal

B0-A와 같은 `.05` threshold를 유지한다.

```text
L_SIGNAL = mean Δshuffled_copy >= .05
           AND CI lower > 0
           AND L > F
           AND 2/3 seeds > 0
```

- 20문서/100step은 still underpowered; `L_SIGNAL` absent는 bridge STOP이 아니다.
- `L_SIGNAL` present도 B0-B 자동 승인이 아니다.

#### M control

```text
M_CONTROL_PASS = mean Δmemfree_copy > 0
                 AND CI lower > 0
```

- M_CONTROL_PASS = real L memory가 mean memory보다 우수
- M_CONTROL_FAIL = real memory가 mean과 구별되지 않음
- M_CONTROL_FAIL이면 L의 content-use 주장 금지

### 6.3 최종 diagnostic label

| 조건 | label |
|---|---|
| P_POSITIVE false | **ASSAY_INVALID** |
| P_POSITIVE true + M_CONTROL_FAIL | **NO_CONTENT_USE_EVIDENCE** |
| P_POSITIVE true + M_CONTROL_PASS + L_SIGNAL | **EXPLORATORY_L_SIGNAL** |
| P_POSITIVE true + M_CONTROL_PASS + no L_SIGNAL | **INCONCLUSIVE_SMALL_N** |

어떤 label도 B0-B/B1/B2/C를 자동 승인하지 않는다.

---

## 7. DoD

### D1. Code path

- `--mode pm-diagnostic` 구현
- `--pm-arm {frozen,lora,p,mean}` 또는 동등한 명시적 arm 선택
- F/L/P는 64-module inventory, mode policy, same-position CE assert
- P는 adapter 없이 64 LoRA modules, native memory path
- M은 training-only mean, `m_eligible` 기록

### D2. Artifacts

각 arm/seed:

- `reports/provenance/C5_b0a/pm/{arm}_{seed}.json`
- per-doc `delta_shuffled_copy`, `delta_shuffled_full`
- M: `delta_memfree_copy`, `delta_memfree_full`
- generation telemetry (cap_hit, EOS, rep4, surface_empty)
- `test_split_used: false`
- `train_mode_policy`
- `metric_alignment` check

### D3. Tests

- 기존 54 tests + new PM tests
- P path: native memory shape 512, 64 LoRA modules
- M: no val leakage, no target label usage, `m_eligible` handling
- mode: base eval, adapter/LoRA train

### D4. Run integrity

- 3 seeds × F/L/P = 9 trained units
- M probes for L (and optionally F/P) recorded separately
- no test split
- no threshold/seed/donor/step change after results
- no B0-B launch

---

## 8. Compute cap

| 항목 | 상한 |
|---|---:|
| F/L/P training | 9 arm-seed × 100 updates |
| M evaluation | 3 seeds × 20 docs, no training |
| wall time | **≤ 2 CPU-hours** |
| threads | 6 |
| GPU | 없음 |
| retry/extension | 자동 없음 |

cap 초과 시 중단·보고한다.

---

## 9. Implementation order

| 단계 | 작업 | 승인 |
|---:|---|---|
| G0 | 이 사전등록 승인 | **필요** |
| 1 | `pm-diagnostic` runner 구현 + tests | G0 후 |
| 2 | native P memory 경로 smoke | G0 후 |
| 3 | mean-memory leakage test | G0 후 |
| 4 | 1 seed debug | G0 후 |
| 5 | 3 seed F/L/P run | **별도 결과 gate** |
| 6 | M probe + report | 5 후 |
| 7 | 새 decision (B0-B 여부) | **별도 승인** |

Phase 6 실행은 B0-B가 아니다. 300/95, B1/B2/C는 이 문서로 승인되지 않는다.

---

## 10. Stop conditions

즉시 중단:

- P path shape/64 module/mode assert 실패
- M mean에 val/target label leakage 발견
- same-position CE != built-in loss (atol 1e-5)
- non-finite loss
- test 163/P1 접근
- 2 CPU-hour cap 초과
- 9 unit artifact 누락

중단 시 자동으로 OTHER arm이나 B0-B를 실행하지 않는다.

---

## 11. 해석 제한

- P는 native encoder positive control이며 EG2 bridge의 성능 증거가 아니다.
- M은 training-only mean-memory negative control이며, M_CONTROL_PASS가 “L이 content를 쓴다”는 단독 증거는 아니다.
- 20문서/100 update는 screening이며 confirmatory 아님.
- F/L/P의 절대 CE를 서로 직접 비교하지 않는다. tokenizer/memory source/arm이 다르다.
- test 163은 계속 sealed.
- B0-B/B1/B2/C는 별도 decision이다.

---

## 12. 승인 요청

> **이 P/M bounded diagnostic 사전등록(v0.1)으로 구현·1-seed debug까지 진행해도 되는가?**

승인 후에도 3-seed 실행과 M probe는 결과 gate에서 별도로 확인한다.
