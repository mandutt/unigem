# C5 Phase 6 v0.2.1-r3.3 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_3_2026-11-09/`
- 검토 기준 HEAD: `3500bc3` (r3.3 plan은 `148d5c1`; 이후 커밋은 metadata/review 파일만)
- 모델:
  - GLM 5.3 Flash **max**
  - DeepSeek V4.1 Flash **1017** **high** — Hoplite `deepseek-v4.1-flash-1017`
  - Terra 6.1 **high** — Hoplite `gpt-6.1-terra`
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_R3_3_2026-11-09.md`
- 원문:
  - `review_GLM.md` (20,206 chars, 187 lines)
  - `review_DS1017.md` (28,682 chars)
  - `review_TERRA.md` (23,065 chars)
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **1 CONTINUE(조건부) / 2 NARROW.** GLM은 spec-level에서 **CONTINUE(조건부)**이며 M1–M3를 동결 전제로 둔다. DeepSeek 1017과 Terra 6.1은 **NARROW**로, r3.3이 r3.2 blocker 대부분을 닫았지만 **§2.4 mixed L table 모순, F arm M builder 누락, `real_prefix_t` space, `n_signal` 15/20 불일치, `tail_driven` 입력 미정의, `adapter_lr` 충돌, T_proj real/control factor 누락**을 freeze blocker로 본다. **r3.4 text-only** 후 재검토한다.

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | r3.3 동결 | 구현+unit tests | D0 | D1 | 3-seed |
|---|---|---|---|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **CONTINUE(조건부)** | M1–M3 후 | 조건부 승인 | 조건부 승인 | 조건부(D0+M4) | 미승인 |
| DeepSeek 1017 | `deepseek-v4.1-flash-1017` high | **NARROW** | 아니오 | r3.4 후 | r3.4 후 | 미승인 | 미승인 |
| Terra 6.1 | `gpt-6.1-terra` high | **NARROW** | 아니오 | 아니오 | 아니오 | 미승인 | 미승인 |
| **종합** | — | **NARROW / 보류** | **미승인** | **미승인** | **미승인** | **미승인** | **미승인** |

- STOP 0/3.
- CONTINUE 1/3 conditional.
- NARROW 2/3.
- **만장일치 아님** → freeze하지 않는다.
- GLM의 CONTINUE는 **primary text를 다시 읽지 않은 spec-level** 판정이며, M1에서 primary-text closure audit을 요구한다. 따라서 실질적으로는 DS/Terra의 NARROW와 같은 방향이다.

---

## 2. 실제로 닫힌 것

세 검토자가 인정한 항목:

- **L consensus 단일화**: §2.3 authoritative, §9.2 ANDn alias 제거
- **§6.3 unreachable cell 삭제**
- fixture 16–18 primitive derivation
- `tail_driven` 수치 경계 복원
- `M_POS_MEAN` builder recipe + arm 표
- replay key/frame/canonical JSON/SHA256
- D1 phase 5 (initial fixed-prefix M CE)
- `NOT3`/`delta_memfree`/DoD 복원
- missing registered seed → `NA`
- new stats module `seed=20261109`
- PA caveat
- `endpoint_ok` 단일 정의
- `§1.1` content SHA-256
- cap 1,204 updates / 155 min / T_proj ≤96

DeepSeek는 r3.2 blocker 15개 중 **13개가 text로 닫혔다**고 평가했다. 남은 것은 주로 **scoring/analysis contract**다.

---

## 3. 남은 Must-fix

### MF-1. §2.4 mixed L table 모순 (blocker)

**문제**

- §2.3:
```text
l_signal = true   if l_copy=true and l_full=true
           false  if l_copy=false and l_full=false
           NA     otherwise
```
- §2.4 표:
```text
true,false  -> l_signal=false
false,true  -> l_signal=false
```
- §2.3과 정면 충돌한다. true/false와 false/true는 **NA**여야 한다.
- Terra: “table calls both false”로 Q1/Q2 disagree.
- GLM: `ANDn`/`NOT3` argument domain 미고정.

**r3.4 요구**

- §2.4의 두 mixed true/false 행을 **NA**로 수정.
- `copy_only`/`full_only`는 그대로 true가 되도록 유지:
  - true,false → copy_only=true, full_only=false
  - false,true → copy_only=false, full_only=true
- §5.3 dispatch에서 `copy_only`/`full_only`가 `l_signal`보다 먼저 평가됨을 명시.
- 9개 pair × validity VALID/INVALID/NA × n=14/15 test.

### MF-2. M builder F arm 누락 (blocker)

**문제**

- §8.4 `endpoint_ok`는 4 arms (F/L/P/PA)를 요구.
- §8.1/§8.2 builder는 L/P/PA만 다룬다; **F의 K_M/builder가 없다**.
- §8.2 `A(h_i)`는 P에 adapter가 없는데 적용된다.
- `h_i >= K_M`은 h가 tensor인지 length인지 type-ambiguous.

**r3.4 요구**

- arm × (K_M, memory, adapter, trainable) matrix:

| arm | K_M | A | adapter | M builder |
|---|---:|---|---|---|
| F | 753 | adapter | trained | `mean_i A(h_i)[:753]` |
| L | 753 | adapter | trained | `mean_i A(h_i)[:753]` |
| P | 512 | identity | none | `mean_i h_i[:512]` |
| PA | 512 | adapter | random-init | `mean_i A(h_i)[:512]` |

- `h_i_len >= K_M`로 type 명시.
- F M endpoint 포함.
- P `A=identity`.

### MF-3. `real_prefix_t` space 미정의 (blocker)

**문제**

- `M_NORM(t)`의 numerator `||real_prefix_t||_F`가 **raw EG2 embedding**인지 **adapter output**인지 불명확.
- `M_POS_MEAN`은 adapter output; mix하면 norm ratio가 잘못된다.

**r3.4 요구**

- `real_prefix_t := A(h_t)[:K_M]`, **same arm/adapter space**.
- M primary reference, M_NORM numerator, M CE real memory 모두 동일.
- P는 identity.
- target label leakage 없음.

### MF-4. `n_signal` 15/20 불일치 (blocker)

**문제**

- §5.1 “signal cohort val20”, `n_signal ∈ {NA,0..20}`.
- preflight L target eligible @753 = **15**.
- 따라서 L signal endpoint의 최대 n은 20이 아니라 **15**.
- DS: “val20/0..20 contradicts 15 eligible”; Terra same.

**r3.4 요구**

- L signal cohort = **15 eligible**; `n_signal ∈ {NA,0..15}`.
- n_signal=15 → `MARGINAL_SIGNAL_COHORT=true`.
- val20은 descriptive only; B0-B는 15.
- 만약 val20을 유지하려면 5개 short doc의 endpoint 정의를 별도로 명시; 현 데이터로는 15가 맞다.

### MF-5. `tail_driven` 입력 미정의 (blocker)

**문제**

- `tail_driven`이 hard gate인데 **어느 endpoint/arm/variant의 `leave_top3_mean`/`top3_share`인지** 없다.
- `top3_share`는 “descriptive only”라면서 gate로 사용.
- known-positive + null의 precedence가 겹친다.

**r3.4 요구**

- `tail_driven` input 고정:
```text
endpoint = L arm, val20, copy endpoint
variant = M_POS_MEAN
delta = control_copy_ce - real_copy_ce
```
- `top3_share`는 `|delta|` 기준으로 gate; signed share는 descriptive.
- precedence:
```text
if leave_top3_mean <= 0: true
elif top3_share is null or leave_top3_mean is null: NA
elif top3_share > .50: true
else: false
```
- raw sum/denominator/top3 IDs artifact 보존.

### MF-6. `adapter_lr` 충돌 (high)

**문제**

- §7.3: `adapter_lr: 1e-3 (PA only)`.
- §7.4: F/L도 adapter trained.
- runner도 F/L에 adapter_lr 사용.

**r3.4 요구**

```text
adapter_lr for all adapter-bearing arms (F/L/PA)
lora_lr for all LoRA-bearing arms (L/P/PA)
P: lora_lr only
```
- `(PA only)` 삭제.

### MF-7. T_proj real/control factor 누락 (high)

**문제**

- phase 5: 15 targets ×2 variants ×copy/full = 60, but real/control = **120**.
- phase 7: 15×5×2×copy/full = 300, but real/control = **600**.
- `T_proj` terms `15x2x2`/`15x5x2x2` omit `memory_kind` factor 2 → **2× undercount**.
- endpoint count 15×3×4×2 omits variants/copy/full; 360 vs 720/1,440 ambiguous.

**r3.4 요구**

- phase 5 `15×2×2×2 = 120`; phase 7 `15×5×2×2×2 = 600`.
- `T_proj` terms include `memory_kind` factor.
- endpoint record count explicit:
```text
15 targets ×3 seeds ×4 arms ×2 variants ×2 copy/full ×2 memory_kind = 1,440
```
- `endpoint_ok` uses 15×3×4×2×(variants 2) or named count.
- T_proj ≤96 min re-derived.

### MF-8. PA veto rationale (medium)

- `m_valid=ANDn(P,PA)`인데 PA는 random-init adapter/different geometry; PA가 L M-control을 veto한다.
- §7.2는 PA를 acquisition control로 규정.
- r3.4: rationale 명시하거나 `m_valid`에서 PA를 descriptive로 분리.

### MF-9. Golden vector self-generated (medium)

- 현재 golden vector는 구현이 만든 digest를 pin하는 구조.
- r3.4: independent worked frame example + hand-derivable digest + empty-set hash + endianness.
- replay golden record 3개.

### MF-10. Named-cell prerequisites (medium)

- “M pass L true + control PASS → EXPLORATORY”는 L flags/validity/n_signal 전제가 부족.
- “m_pass_l=false → M_CONTROL_FAIL”은 availability/calibration 전제가 부족.
- r3.4: fixture 16–18 참조로 대체; named cell은 primitive prerequisites 포함.

### MF-11. ANDn/NOT3 domain (medium)

- `ANDn(l_copy, NOT3(l_full))`의 operand domain (seeds/endpoints/arms) 미고정.
- r3.4: operator domain + worked example.

### MF-12. Zero-margin failure path (low)

- K=753 (754→14), cohort 15/15.
- r3.4: expected `M_NOT_EVALUABLE` path/reporting.

### MF-13. P0 caveat (low)

- P0 `source_max_length=256` vs registered 512.
- P0 untrained CE 12.7/13.2 > ln|V| 12.43.
- P0 never B0-B/gate evidence.

---

## 4. 검토자별 차이

### GLM — CONTINUE(조건부)

- r3.3 blocker 15개를 spec-level에서 closed로 판정.
- M1–M3:
  - primary-text closure audit
  - `ANDn`/`NOT3` domain
  - replay donor_id/golden digest
- M4–M7:
  - T_proj re-derive
  - M_NORM explicit
  - unit suite
  - P0 OOD logging
- **primary text를 다시 읽지 않은 spec-level**; M1 없이는 동결 불가.

### DeepSeek 1017 — NARROW

- 13/15 blockers closed.
- 6 blockers:
  1. F M builder
  2. real_prefix_t
  3. n_signal 15/20
  4. tail_driven input
  5. adapter_lr
  6. T_proj real/control factor
- 그 외 endpoint count, PA veto, golden vector, zero-margin.

### Terra 6.1 — NARROW

- **§2.4 mixed table 모순**을 최우선.
- M builder F/P identity/source length.
- replay/hash/D1 completeness.
- tail/statistics totality.
- **§2.4 true/false → false**를 명시적으로 지적.

**해석**: GLM은 spec-level CONTINUE, DS/Terra는 executable contract NARROW. **r3.4에서 §2.4 table, F builder, real_prefix_t, n_signal, tail input, adapter_lr, T_proj factor를 닫아야 한다.**

---

## 5. 결정

```text
r3.3 = 동결 보류 (1 CONTINUE conditional / 2 NARROW)
r3.4 = 필요 (text-only)
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

1. r3.4 text-only:
   - §2.4 mixed true/false → NA
   - F M builder + P identity + `h_i_len`
   - `real_prefix_t = A(h_t)[:K_M]`
   - `n_signal ∈ {NA,0..15}`
   - tail input/precedence
   - adapter_lr all adapter-bearing arms
   - T_proj real/control factor
   - endpoint record count
   - PA veto rationale
   - independent golden vector
   - named-cell prerequisites
   - ANDn/NOT3 domain
   - zero-margin path
   - P0 caveat
2. r3.4 3-AI 재검토
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
| `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_3_2026-11-09/review_GLM.md` | GLM full 187줄 |
| `.../review_DS1017.md` | DeepSeek full |
| `.../review_TERRA.md` | Terra full |
| `reports/C5_B0A_PM_PREREG_V0_2_1_R3_3_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_3.md` | r3.3 |
| `reports/provenance/C5_b0a/m_cohort_preflight.json` | M preflight |

## 8. 제한

- 이 종합은 승인이 아니다.
- 1 CONTINUE / 2 NARROW는 만장일치가 아니다.
- GLM의 CONTINUE는 primary-text 재검토를 M1으로 남긴 **spec-level** 판정이다.
- r3.4 없이 코드를 작성하지 않는다.
- “54 tests”는 historical evidence이며 PM tests는 아직 없다.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
