# C5 Phase 6 v0.2.1-r3.4 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_4_2026-11-09/`
- 검토 기준 HEAD: `05de3ae` (r3.4 plan은 `30b966d`; 이후 `c158c7f`는 threads only)
- 모델:
  - GLM 5.3 Flash **max** — 30,109 chars
  - DeepSeek V4.1 Flash **1017** **high** — 25,025 chars
  - Terra 6.1 **high** — 20,824 chars
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_R3_4_2026-11-09.md`
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **3/3 NARROW.** r3.4는 §2.4 mixed L table과 F/P builder, `n_signal 15`, T_proj 120/600, endpoint 1,440을 실제로 닫았다. 그러나 **variant×memory_kind tensor grid, `tail_driven`의 variant, P/PA validity cohort, replay domain/debug-vs-final hash, L binding, F/L memory length scope, PA_VALID, exact endpoint key set, golden digest**가 남아 freeze할 수 없다. 세 검토자 모두 **구현 전 v1.0 consolidated spec**이 필요하다고 판정했다.

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | r3.4 동결 | 구현+unit tests | D0 | D1 | 3-seed |
|---|---|---|---|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **NARROW** | 아니오 | 아니오 | 아니오 | 미승인 | 미승인 |
| DeepSeek 1017 | `deepseek-v4.1-flash-1017` high | **NARROW** | 아니오 | 아니오 | 아니오 | 미승인 | 미승인 |
| Terra 6.1 | `gpt-6.1-terra` high | **NARROW** | 아니오 | 아니오 | 아니오 | 미승인 | 미승인 |
| **종합** | — | **NARROW 3/3** | **미승인** | **미승인** | **미승인** | **미승인** | **미승인** |

- STOP 0/3.
- CONTINUE 0/3.
- NARROW 3/3.
- **만장일치 NARROW** → freeze하지 않는다.

---

## 2. 실제로 닫힌 것

세 검토자가 인정한 항목:

- **§2.4 mixed L table**: true/false·false/true → `NA`; copy_only/full_only는 각각 true
- **F/L/P/PA M builder**: F/L 753 adapter, P 512 identity, PA 512 adapter
- **`h_len_i`** scalar
- **`real_prefix_t := A(h_t)[:K_M]`** same adapter space
- **`n_signal ∈ {NA,0..15}`**
- **T_proj phase 5 = 120**, phase 7 = 600
- **endpoint 1,440** arithmetic
- **`adapter_lr`** F/L/PA
- PA caveat/veto rationale
- independent golden-vector procedure(단, digest 미기재)
- zero-margin path
- P0 OOD caveat
- 27-item checklist

GLM: **17/18 r3.3 blockers text-level closed**. DeepSeek: **MF-1~MF-5만 남음**. Terra: 개선 인정, 그러나 data-to-decision totality는 미완.

---

## 3. 남은 Must-fix

### MF-1. Variant × memory_kind tensor grid 미정의 (blocker)

**문제**

- `real_prefix_t`는 variant-independent.
- `M_POS_MEAN`/`M_NORM` 두 variant가 둘 다 pass해야 한다.
- `control`이 무엇인지 명시되지 않는다.
- `delta_memfree`는 “memory-free” control을 함축하지만, M_POS_MEAN/M_NORM와의 관계가 불명확.
- 2×2 grid가 degenerate일 수 있어 1,440 records가 1,440 distinct cells가 아닐 수 있다.
- `M_PASS_POS`와 `M_PASS_NORM`이 같은 test를 두 번 하는 것일 수 있다.

**v1.0 요구**

- 명시적 tensor table:

| variant | control memory | real memory | endpoint |
|---|---|---|---|
| M_POS_MEAN | global train mean | `A(h_t)[:K_M]` | copy/full |
| M_NORM | `M_POS_MEAN * norm_ratio` | `A(h_t)[:K_M]` | copy/full |

- `memory_kind` axis가 **variant-dependent**임을 명시.
- `delta_memfree`는 M_POS_MEAN/M_NORM 각각에 대해 정의.
- `M_PASS_POS`/`M_PASS_NORM`이 독립 test임을 명시.
- exact key set.

### MF-2. `tail_driven` variant 미고정 (blocker)

**문제**

- r3.4 §9.4는 `arm=L`, `endpoint=copy`, `cohort=15`, `delta=control−real`까지 고정.
- 그러나 **variant (M_POS_MEAN vs M_NORM)**가 없다.
- 두 primary variants가 있으므로 hard B0-B gate가 두 값을 가질 수 있다.
- GLM MF-A, DS MF-2, Terra Q7 모두 지적.

**v1.0 요구**

- `tail_driven` variant = **M_POS_MEAN**으로 고정.
- `M_NORM` tail은 descriptive only.
- `top3_abs_share`/`leave_top3_mean` raw values artifact 보존.
- 15 eligible docs; n<15 → NA.

### MF-3. P/PA validity cohort 미정의 (blocker)

**문제**

- `P_VALID`/`PA_VALID`가 15 `common_ids`인지 20 native docs인지 불명.
- P/PA native는 20/20 at 512.
- `m_pass_pos_p/norm_p` cohort도 불명.
- `m_valid`/`control_status`가 이 cohort에 의존.

**v1.0 요구**

- P/PA validity cohort = **20 native docs** (native 512 eligible).
- L/F cohort = 15 common IDs.
- `m_pass_pos_p/norm_p`/`m_pass_pos_pa/norm_pa` = 20 native.
- `m_valid` = P/PA 20-doc calibration.
- `PA_VALID`를 v1.0에 직접 정의; old errata 참조 금지.
- `PA_VALID = delta_copy_step100 >= .05 AND copy CI lower>0 AND delta_full_step100 >0 AND full CI lower>0`, 20 native docs, same 100-step protocol.

### MF-4. Replay domain/count/debug vs final hash (blocker)

**문제**

- phase 5 donor-free 120/arm-seed; phase 7 donor-level 600/arm-seed.
- total 7,200 vs 8,640 ambiguous.
- `debug_replay_hash`는 D1 seed 20261111, 1 update인데 registered postrun hash와 비교되는지 불명.
- tolerance `atol/rtol`와 exact SHA256 equality가 혼합.
- donor-free `donor_id:null` vs donor ordinal 0–4 sorting ambiguity.
- CE field name, JSON encoding, null/integer ordering 미정의.

**v1.0 요구**

- phase 5 = **primary M replay**, donor-free, 120/arm-seed, `donor_id:null`.
- phase 7 = **donor diagnostic replay**, donor-level, 600/arm-seed, `donor_id:0..4`.
- `debug_replay_hash` = D1 synthetic only; **registered postrun hash와 직접 비교하지 않는다**.
- numeric replay: tolerance `atol=1e-5`, `rtol=1e-4`.
- artifact integrity: SHA256 exact, separate field.
- canonical sort key: `(doc_id, arm, seed, variant, endpoint, memory_kind, donor_sort)` where `donor_sort = -1` for null, `0..4` for donor.
- record field `ce` float64; nonfinite reject.
- exact total = 15×3×4×2×2×2 = 1,440 primary M; phase 7 = 15×3? No, D1 only 4 arm-seeds; define per D1 vs registered.
- state hash frame independent of replay hash.

### MF-5. L primitive binding (blocker/high)

**문제**

- `l_copy_signal`/`l_full_signal`가 `L_COPY_SIGNAL`/`L_FULL_SIGNAL`에 bind되지 않는다.
- `n_signal<15`일 때 최소 n/계산 가능 조건 미정의.

**v1.0 요구**

```text
l_copy_signal := L_COPY_SIGNAL
l_full_signal := L_FULL_SIGNAL
```

- `n_signal>=15` only; otherwise `NA` and small-N label.
- `L_COPY_SIGNAL`/`L_FULL_SIGNAL` full 4-conjunct predicates.
- missing registered seed → `NA`.

### MF-6. F/L memory length scope (blocker/high)

**문제**

- arm table F/L memory K=753이 M뿐 아니라 training/eval/generation에도 적용되는 것으로 읽힌다.
- training order 20 docs 중 4개가 753 미만; generation 20 val docs 중 5개가 753 미만.
- padding/drop/order change 없이 모두 753을 요구할 수 없다.

**v1.0 요구**

- **M memory** F/L `[:753]`; P/PA `[:512]`.
- **training/eval signal** donor-crop `K=min(len_real,len_donor)` 유지.
- **generation** registered 20 val docs, no 753 requirement; max_new_tokens=256.
- **M** donor-free target prefix `[:K_M]`.
- F/L arm table K=753은 **M-only**로 명시.
- no padding/drop/order change.

### MF-7. `PA_VALID`/PA veto (high)

- `PA_VALID`가 r3.4에 없다; v0.2.1 errata §2.4에서 복원해야.
- PA veto rationale가 “native regime invalid”로 과장; 실제는 joint P/PA calibration policy.
- v1.0: `PA_VALID` 직접 정의 + veto rationale “PA random-init adapter failure vetoes joint calibration; not proof native regime invalid.”

### MF-8. `full-K 11/20` 정의 (medium)

- r3.4 §8.1/§14가 “full-K 11/20 secondary”를 인용하지만 K/predicate 없음.
- preflight excluded set은 h<753 9개; full-K 11은 K=768? Define.
- v1.0: `full_k_secondary`의 K, IDs, predicate, descriptive-only 명시; gate 아님.

### MF-9. Top3 signed vs absolute (medium)

- P0 `.4862`는 **signed** top3 share; gate는 **absolute** share `.43355` (val20) / `.455` (15 common).
- r3.4 §12 caveat가 signed를 인용.
- v1.0: both values, clear label; gate uses absolute; `.50` threshold unchanged.
- raw top3 sum/denominator/top3 IDs.

### MF-10. `documents_positive` / flags / labels (low)

- `documents_positive` undefined; classify.
- F1–F11 flags residual defaults.
- `M_CONTROL_INVALID` vs `M_NOT_EVALUABLE` p_valid=false wording.
- availability NA collapse asymmetry.
- `golden_vectors.json` digest absent.
- 3-seed checklist item 24 omits L.
- D1 “4 arm-seeds” wording; `100*t_train` extrapolation.

---

## 4. 검토자별 차이

### GLM — NARROW

- 17/18 closed; MF-A tail variant, MF-B donor replay, MF-C delta naming, MF-D chain-inherited definitions, MF-E checklist typo.
- Q13: v1.0 needed.
- freeze no; implementation no; D0 no.

### DeepSeek 1017 — NARROW

- Q1/Q2 agree; contract total at predicate level.
- MF-1 variant×memory_kind, MF-2 tail variant, MF-3 P/PA cohort, MF-4 replay domain/hash, MF-5 L binding.
- Q13: v1.0 needed; consolidate.
- no freeze/no code/no D0.

### Terra 6.1 — NARROW

- Q1 disagree: data-to-decision not total; F/L memory length and replay semantics.
- Q2 agree at derived-predicate level.
- Q4 conditional: exact key set not just count; 96 appearances per target.
- Q7 disagree: tail variant/ties.
- Q13: v1.0 needed with 9 sections.
- independent golden hash example:
  - state vector `43ecb58e…d65712`
  - empty `e3b0c442…b855`
  (review calculation, not committed artifact)

**해석**: 3/3 NARROW. GLM is closest to freeze, DS/Terra require more. v1.0 is the common next step.

---

## 5. Q13 Consolidation — 3/3 agree

세 검토자 모두 **v1.0 self-contained normative spec**이 구현 전에 필요하다고 답했다.

이유:

- r3.4는 여전히 errata chain의 일부.
- `PA_VALID` 같은 정의가 과거 errata에 의존.
- r3.3의 stale `n_signal 0..20`/mixed table 같은 inheritance risk.
- precedence만으로는 executable implementation contract가 되지 않는다.
- past docs are audit trail, not implementation authority.

### v1.0 minimum sections

1. scope / approval / sealed boundaries
2. data/model/cohort identities, donor and leakage rules
3. four-arm initialization, training/eval modes, workload-specific memory/length/crop
4. M builder, variants, endpoints, exact record schema
5. statistical estimands, aggregation, CI, tail
6. primitive three-axis decision tables, failure precedence
7. canonical checkpoint/replay formats, independent vectors
8. D0/D1 workload, timing, caps, gates
9. artifacts, tests, B0-B boundary, aborts

### Traceability

- clause-by-clause map from r3.4 + inherited normative rules
- explicitly mark superseded clauses
- resolve conflicts
- immutable preflight/spec/code hashes
- no silent new scientific choices under “consolidation”

---

## 6. 결정

```text
r3.4 = 동결 보류 (3/3 NARROW)
r3.5 = 만들지 않는다
v1.0 = r3.4 + Must-fix를 반영한 self-contained normative spec
v1.0 review = 별도 1회
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

## 7. 다음 단계

1. r3.4를 base로 **v1.0 consolidated spec** 작성
   - MF-1~MF-10 반영
   - F/L memory length scope
   - PA_VALID
   - variant×memory_kind table
   - tail variant
   - P/PA cohort
   - replay domain/hash separation
   - L binding
   - top3 signed/absolute
   - full-K definition
2. v1.0 3-AI review
3. freeze `v1.0` commit hash + SHA256
4. 구현 + unit tests
5. D0
6. D1 separate
7. 3-seed separate
8. B0-B separate

---

## 8. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_4_2026-11-09/review_GLM.md` | GLM 30,109 chars |
| `.../review_DS1017.md` | DeepSeek 25,025 chars |
| `.../review_TERRA.md` | Terra 20,824 chars |
| `reports/C5_B0A_PM_PREREG_V0_2_1_R3_4_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_4.md` | r3.4 |
| `reports/provenance/C5_b0a/m_cohort_preflight.json` | M preflight |

## 9. 제한

- 이 종합은 승인이 아니다.
- 3/3 NARROW는 만장일치다.
- v1.0 없이 코드를 작성하지 않는다.
- “54 tests”는 historical evidence이며 PM tests는 아직 없다.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
- Terra의 golden hash는 review calculation이며 committed artifact가 아니다.
