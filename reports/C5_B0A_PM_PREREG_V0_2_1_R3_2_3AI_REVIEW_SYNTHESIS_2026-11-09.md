# C5 Phase 6 v0.2.1-r3.2 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_2_2026-11-09/`
- 검토 기준 HEAD: `6aac52f` (요청서 커밋; r3.2 plan은 부모 `44bbef6`)
- 모델:
  - GLM 5.3 Flash **max**
  - DeepSeek V4.1 Flash **1017** **high** — Hoplite `deepseek-v4.1-flash-1017`
  - Sol 6.1 **medium**
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_R3_2_2026-11-09.md`
- 원문:
  - `review_GLM.md` (23,769 chars, full)
  - `review_DS1017.md` (3,874 chars, final-message summary; DS reported 295-line report on its own branch)
  - `review_SOL.md` (27,168 chars, full)
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **1 CONTINUE(조건부) / 2 NARROW.** GLM은 MF-1~MF-8 text-only micro-errata 후 동결·구현·D0를 조건부 승인한다. DeepSeek 1017과 Sol은 **r3.2를 그대로 동결하면 안 된다**고 본다. 핵심은 **§2.3 L consensus와 §9.2 `L_SIGNAL=ANDn`의 이중 정의**, **§6.3에 남은 unreachable fixture**, **`tail_driven` 기준 삭제**, **`M_POS_MEAN` builder recipe/M primary reference 누락**, **arm 표 부재**다. **r3.3 text-only repair** 후 재검토한다.

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | r3.2 동결 | 구현+unit tests | D0 | D1 | 3-seed |
|---|---|---|---|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **CONTINUE(조건부)** | MF-1~MF-8 후 | 조건부 | 조건부 | 미승인 | 미승인 |
| DeepSeek 1017 | `deepseek-v4.1-flash-1017` high | **NARROW** | 아니오 | 미승인 | 미승인 | 미승인 | 미승인 |
| Sol | `gpt-6.1-sol` medium | **NARROW** | 아니오 | 미승인 | 미승인 | 미승인 | 미승인 |
| **종합** | — | **NARROW / 보류** | **미승인** | **미승인** | **미승인** | **미승인** | **미승인** |

- STOP 0/3.
- CONTINUE 1/3 conditional.
- NARROW 2/3.
- **만장일치 아님** → freeze하지 않는다.

---

## 2. 실제로 닫힌 것

세 검토자가 인정한 항목:

- **full threshold `>0` 복원** — v0.2 §6.2와 일치, `.05` 잔존 없음
- fixture 16–18의 §6.2 primitive derivation
- `M_NORM(t)` fixed formula
- D1에 generation 20×256, 20-train M build, 5 donors, 2 variants, overhead 포함
- canonical checkpoint/replay hash 메커니즘
- B0-B `tail_driven == false` hard gate
- F9/F10/F11, small-N precedence
- preflight content SHA-256 `3ee3f1ca…`
- cap 산술 1,204 updates / 155 min / T_proj ≤96
- `M_NOT_EVALUABLE`/`M_CONTROL_INVALID` 분리

DeepSeek/Sol도 **r3.1의 9 blocker 중 상당수가 실제로 닫혔다**고 평가했다. 남은 것은 주로 **r3.2가 새로 만든 또는 완전히 제거하지 못한 contract 모순**이다.

---

## 3. 남은 Must-fix

### MF-1. L signal 이중 정의 (blocker)

**문제**

- §2.3:
```text
l_signal = true   if both l_copy and l_full true
           false  if both false
           not_assessable otherwise
```
- §9.2:
```text
L_SIGNAL = ANDn(L_COPY_SIGNAL, L_FULL_SIGNAL)
```
- `copy=false, full=NA`에서 §2.3은 NA, §9.2/ANDn은 false.
- 이 경우 `copy_only=false`, `full_only=NA`이므로 §5.3은 §2.3에서 `NOT_ASSESSABLE`, §9.2에서 `MEAN_CONTRAST_ONLY`로 갈린다.
- **관측 가능한 label 차이**다.

**r3.3 요구**

- §5.3 dispatch가 소비하는 **단일 authoritative `l_signal`**을 §2.3 consensus로 고정.
- §9.2의 `L_SIGNAL = ANDn(...)`을 삭제하거나 `L_RAW_ANDN`으로 이름을 바꾸고 dispatch에 사용하지 않는다.
- 3×3 copy/full tri-state 표에 모든 expected label을 명시.
- `false+NA` 조합은 `NOT_ASSESSABLE`로 고정.

### MF-2. §6.3 unreachable fixture (blocker)

**문제**

- §6.3:
```text
- M pass L true + control PASS → EXPLORATORY.
- M pass L false + control PASS → MEAN_CONTRAST_ONLY.
```
- §4.3에서 `m_pass_l=false`이면 `control_status=M_CONTROL_FAIL`이므로 “control PASS”가 불가능.
- `EXPLORATORY`는 enum `EXPLORATORY_L_SIGNAL`이 아니다.
- §6.4 “every named cell exact output”을 원리적으로 불만족.

**r3.3 요구**

- §6.3의 마지막 두 bullet 삭제.
- fixture 16–18을 명시적으로 참조:
  - 16 = EXPLORATORY
  - 17 = MEAN_CONTRAST_ONLY
  - 18 = NO_AFFIRMATIVE
- `m_pass_l=false` cell은 control FAIL로만.
- 모든 fixture는 primitive에서 derive; derived `m_pass_l`/`m_valid` 직접 주입 금지.

### MF-3. `tail_driven` 기준 소실 (blocker)

**문제**

- r3/r3.1 기준:
```text
tail_driven = true if leave_top3_mean <= 0
              or top3_share > .50
```
- r3.2 §9.4는 “known positive criterion”만 남기고 **정확한 수치 경계를 삭제**.
- B0-B가 **정의되지 않은 predicate**에 hard gate를 건다.
- P0 val `top3_share=.4862`는 `.50`까지 0.0138 — 경계가 outcome-relevant.

**r3.3 요구**

- 정확한 기준 복원:
```text
tail_driven = true   if leave_top3_mean <= 0 OR top3_share > .50
              false  if leave_top3_mean > 0 AND top3_share <= .50
              NA     if either input null/nonfinite
```
- `top3_share`/`leave_top3_mean`/raw top3 sum/denominator를 artifact에 보존.
- B0-B `tail_driven == false` 유지.
- threshold 변경 없음.

### MF-4. M builder recipe / M primary reference 누락 (blocker)

**문제**

- r3의 builder recipe:
```text
M_POS_MEAN[j] = mean_i A(h_i)[:K_M][j]
shape = K_M × 512
```
- r3.2 §8.3은 공식만 있고 **M_POS_MEAN 구성식, shape, adapter eval/no_grad, contributor 판정**이 없다.
- “M primary reference = target prefix at K_M; donor-crop 금지” 규칙도 없다.
- 현행 runner는 donor-crop을 사용하므로, 문서 없이 구현하면 상속 위반.

**r3.3 요구**

- §8에 builder recipe 복원:
  - adapter/model `eval()`
  - `no_grad()`
  - contributors >=10
  - `M_POS_MEAN[j] = mean_i A(h_i)[:K_M][j]`
  - shape `K_M × 512`
  - L `[:753]`, P/PA `[:512]`
  - seed별 builder 후 seed-average
- M primary reference = **target prefix at K_M**, donor-crop 금지.
- `M_GLOBAL` secondary 위치 명시.

### MF-5. Arm 표 부재 (blocker, 구현)

**문제**

- 12 units / 1,200 updates의 전제인 **F/L/P/PA arm 정의 표**가 r3.2에 없다.
- P/PA memory/trainable 구분, adapter 유무, decoder LoRA 유무가 문장에 흩어져 있다.

**r3.3 요구**

- 다음 표 복원:

| arm | memory | trainable | 역할 |
|---|---|---|---|
| F | EG2 layer19 | adapter | reference |
| L | EG2 layer19 | adapter + decoder LoRA | B0-A 재검증 |
| P | native mT5 encoder | decoder LoRA only | positive control |
| PA | native mT5 encoder | adapter + decoder LoRA | P/F regime 정합 |

- 12 units = 4 arms × 3 seeds.
- 100 updates/unit.

### MF-6. Replay/hash wire format (blocker/high)

**문제**

- replay record:
```text
(doc_id, arm, seed, variant, endpoint, CE float64)
```
- `id`와 `doc_id` 혼용.
- real/control discriminator 없음.
- donor-level vs donor-averaged 불명확.
- checkpoint byte stream의 exact framing/encoding 없음.
- golden-vector expected digest 상수 없음.
- variant 집합 불명확.

**r3.3 요구**

- replay record key:
```text
(doc_id, arm, seed, variant, endpoint, memory_kind)
```
- `memory_kind ∈ {real, control}`.
- donor-level replay이면 donor ID를 key에 포함; donor-averaged이면 aggregation rule 명시.
- checkpoint frame:
  - `name_len:u32|name|dtype_len:u8|dtype|ndim:u8|shape:u32×ndim|nbytes:u64|bytes`
  - little-endian
  - sorted keys
- replay JSON:
  - sorted keys, separators `(',',':')`
  - float64 finite only; nonfinite reject
- golden-vector expected SHA256 상수를 test에 동결.
- permutation/duplicate/missing-key tests.

### MF-7. D1 initial fixed-prefix M CE scoring (high)

**문제**

- D1 phase 4는 “M builder 20 train + 15 target ×2 variants”만 있다.
- **initial fixed-prefix real/M CE scoring**이 builder와 별도 phase인지 불명확.
- donor multiplicity 5가 replay phase에만 있고, initial M scoring에는 없는지 불명확.
- generation/replay/donor factor가 endpoint schema와 어떻게 대응하는지 불명확.

**r3.3 요구**

- D1 phase를 분리:
  1. train 1 update
  2. step0 eval 20×5 donors
  3. final eval 20×5 donors
  4. M builder 20 train + 15 target ×2 variants
  5. **initial fixed-prefix real/M CE scoring 15×2×copy/full**
  6. generation 20×256
  7. replay 15×5×2×copy/full
  8. overhead
- `T_proj`에 phase 5를 명시적으로 추가.
- donor factor는 phase 2/3/7에만; phase 4/5는 donor-free primary M work.
- `T_proj` ≤96 min.

### MF-8. `§1.4` dangling (mod)

- §15 closure table: “blob 표현 → §1.4 content SHA-256”
- 실제 절은 **§1.1**.
- r3.3에서 `§1.1`로 수정.

### MF-9. `NOT3`/`delta_memfree`/DoD 항목 소실 (high)

- `NOT3` 정의가 r3.2에 없지만 §2.3에서 사용.
- `delta_memfree_full = mean_full_ce − real_full_ce` 정의 소실.
- DoD에서 “truth-table per-axis + named cells”와 “PA acquisition labels” 삭제.

**r3.3 요구**

- `NOT3` 정의 복원: true↔false, NA→NA.
- `delta_memfree_copy/full` 정의 복원.
- DoD 두 항목 복원.

### MF-10. 결측 seed / 2-of-3 (mod)

- “2/3 seed means >0”이 **등록 3 seeds** 기준인지, 가용 seed 기준인지 불명확.
- 등록 seed 결측 시 predicate을 `not_assessable`로 해야 한다; 2-of-available 대체 금지.

**r3.3 요구**

- `2/3 registered seeds` 고정.
- missing registered seed → `l_copy_signal`/`l_full_signal` = `not_assessable`.
- §9.4와 정합.

### MF-11. Statistics legacy (mod)

- `bootstrap_paired(seed=20261108)`와 `seeds_positive` 문서 수 오기 생존.
- r3.2 §9.3은 new module/seed 20261109를 요구하지만 runner legacy는 그대로.

**r3.3 요구**

- 새 `runner/c5_pm_stats.py`만 사용.
- `bootstrap_seed=20261109`.
- `documents_positive`.
- `seeds_positive` = seed mean only.
- P0 helper 재사용 금지.

### MF-12. PA caveat / endpoint_ok 이중 정의 (mod/low)

- §7.2 PA scale/geometry caveat 삭제.
- `endpoint_ok`가 §4.1과 §8.4에 중복 정의.

**r3.3 요구**

- PA caveat 복원: native 512 vs L 753, geometry/scale 다름, PA는 acquisition control이며 retention gate 아님.
- `endpoint_ok`를 §8.4 단일 정의로 통합.

---

## 4. 검토자별 차이

### GLM — CONTINUE(조건부)

- 9 r3.1 blocker 모두 **closed**로 판정.
- Must-fix 8개:
  - PA scale/geometry caveat 복원
  - builder recipe/M_POS_MEAN
  - delta_memfree
  - NOT3
  - DoD truth-table/PA labels
  - missing-seed rule
  - replay variant set
  - §1.4→§1.1, golden digest, enum assertion
- MF 반영 후 freeze+구현+D0 조건부 승인.

### DeepSeek 1017 — NARROW

- `.05`/`>0` 회귀는 완전히 닫힘.
- blocker:
  - §6.3 unreachable cell
  - tail_driven criterion 삭제
  - M_POS_MEAN builder/reference 탈락
  - F/L/P/PA arm 표 부재
- 그 외 hash wire format, fixture derived-value 주입, `§1.4`, seed 집합, legacy stats, PA caveat, endpoint_ok.

### Sol — NARROW

- **가장 중요한 신규 모순은 §2.3 L consensus vs §9.2 ANDn**.
- §6.3 unreachable fixture.
- replay identity/framing/golden vectors.
- D1 initial fixed-prefix M CE scoring/donor mapping.
- r3.3 text-only MF-1~MF-4.

**해석**: GLM은 micro-errata로 충분하다고 보지만, DS/Sol은 **L consensus·fixture·tail·M builder**를 freeze blocker로 본다. r3.3에서 모두 닫아야 한다.

---

## 5. 결정

```text
r3.2 = 동결 보류 (1 CONTINUE conditional / 2 NARROW)
r3.3 = 필요 (text-only)
Phase 6 구현 = 미승인
unit tests = 미승인
D0 = 미승인
D1 = 미승인
3-seed = 미승인
B0-B/B1/B2/Stage C = 미승인
test 163 = sealed
T5Gemma2 = D-108 STOP
```

---

## 6. 다음 단계

1. r3.3 text-only errata:
   - L consensus 단일화
   - §6.3 unreachable cell 제거
   - tail_driven exact criterion
   - M builder recipe + primary reference
   - arm 표
   - replay/hash wire format
   - D1 initial M CE scoring
   - NOT3/delta_memfree/DoD 복원
   - missing-seed 2/3
   - stats legacy 제거
   - PA caveat/endpoint_ok
   - §1.1
2. r3.3 3-AI 재검토
3. freeze commit
4. 구현 + unit tests
5. D0
6. D1 separate
7. 3-seed separate
8. B0-B separate

---

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_2_2026-11-09/review_GLM.md` | GLM full |
| `.../review_DS1017.md` | DeepSeek final-message summary |
| `.../review_SOL.md` | Sol full |
| `reports/C5_B0A_PM_PREREG_V0_2_1_R3_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_2.md` | r3.2 |
| `reports/provenance/C5_b0a/m_cohort_preflight.json` | M preflight |

## 8. 제한

- 이 종합은 승인이 아니다.
- 1 CONTINUE / 2 NARROW는 만장일치가 아니다.
- r3.3 없이 코드를 작성하지 않는다.
- “54 tests”는 historical evidence이며 PM tests는 아직 없다.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
