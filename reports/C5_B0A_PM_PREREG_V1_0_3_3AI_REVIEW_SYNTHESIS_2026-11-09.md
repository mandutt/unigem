# C5 Phase 6 v1.0.3 — 3-AI Review Synthesis

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_pm_prereg_v1_0_3_2026-11-09/`
- 검토 기준 HEAD: `c53ed76`
- 모델:
  - GLM 5.3 Flash **max** — 19,752 chars
  - DeepSeek V4.1 Flash **1017** **high** — 24,060 chars
  - Sol 6.1 **medium** — 33,928 chars
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_3_2026-11-09.md`
- test 163: **미사용**
- P1: **미사용**
- Phase 6 실행: **없음**

---

## 0. 한 줄 결론

> **1 CONTINUE(조건부) / 2 NARROW.** v1.0.3은 v1.0.2의 10개 blocker를 구조적으로 닫았고, golden 5종·preflight hash·360/480/1,680/560/600 산술은 재현됐다. 그러나 **phase-7 `K_d`/`baseline_ce`의 실제 계산 조건, `donor_id=null`의 total order, replay hash의 flat wire projection, 12-key checkpoint map의 직렬화 형식, P1 frozen hash vs postrun inventory**가 남아 동결할 수 없다. **v1.0.4/ERRATA text/schema only.**

---

## 1. 판정 행렬

| 검토자 | 모델 | 판정 | v1.0.3 freeze | 구현+unit tests | D0 | D1 | 3-seed |
|---|---|---|---|---|---|---|---|
| GLM | `z-ai/glm-5.3-flash` max | **CONTINUE(조건부)** | MF-A/B 흡수 후 | 승인 | 승인 | 미승인 | 미승인 |
| DeepSeek 1017 | `deepseek-v4.1-flash-1017` high | **NARROW** | ERRATA MF-1..10 후 | 보류 | 보류 | 미승인 | 미승인 |
| Sol | `gpt-6.1-sol` medium | **NARROW** | MF-1..4 후 | 보류 | 보류 | 미승인 | 미승인 |
| **종합** | — | **NARROW (2/3)** | **보류** | **보류** | **보류** | **미승인** | **미승인** |

- CONTINUE 1/3.
- NARROW 2/3.
- STOP 0/3.
- NARROW 우세 → **동결하지 않는다**.

---

## 2. 실제로 닫힌 것

- `donor_id` canonical key — **closed** (DS, Sol, GLM)
- base `c43ea…` 보존 — **verified**
- supplemental `8277a7…` — **verified**
- control `6b50c226…` — **verified** (name-asc)
- 12-checkpoint identity — **partial** (내용은 맞지만 serialization 미정)
- 360/480/1,680/560/600 — **verified**
- phase-7 enum `{control,real,donor}` — **closed**
- phase-7 raw `ce`/`baseline_ce`/`delta` — **partial** (K_d 조건 미정)
- P1 both flags — **closed** (inventory/hash unresolved)
- P_VALID tri-state/F9 — **closed**
- control tensor schema — **closed** (fixture shape/order note)
- P/PA asymmetry — **closed**
- D0 4-config — **closed**
- native-512 assert — **closed**

DS: 10개 중 **9 closed, 1 partial**.
Sol: 10개 중 **7 closed, 3 partial**.
GLM: **10/10 closed**, 7개 1-line clarification.

---

## 3. 남은 Must-fix

### MF-1. Phase-7 `K_d`/`baseline_ce` (blocker/high)

- `K_d = min(len(real_prefix), len(donor_prefix))`만으로는 부족.
- `baseline_ce`가 **K_d-crop control variant를 phase-7 조건에서 재계산한 값**인지, phase-5 K_M CE인지 불명.
- preflight lengths에서 `M_POS_MEAN[:K_d]`/`M_NORM[:K_d]`가 실제로 유효한지.
- donor-conditioned baseline의 target/endpoint 조건.

**v1.0.4 요구**:
- `baseline_ce = CE(control_variant[:K_d], target, endpoint)`를 phase-7에서 재계산.
- phase-5 stored CE(K_M) 재사용 금지.
- `K_d` bounds: `1 <= K_d <= min(len(real), len(donor))`.
- `donor_prefix` length = donor document의 arm-space length.
- control variant slice만 사용; donor content 혼합 없음.

### MF-2. `donor_id=null` total order (medium)

- canonical key sort에서 null의 위치가 불명.
- GLM: internal `donor_sort=-1`로 null 먼저; DS: total order 정의.
- 기존 fixture digest에는 영향 없음.

**v1.0.4 요구**:
- null은 **-1로 내부 정렬**, serialized `donor_id=null`.
- ascending key: `doc_id, arm, seed, variant, endpoint, memory_kind, donor_sort`.
- positive donors 0..4.
- permutation invariance test.

### MF-3. Replay hash wire projection (high)

Sol:
- §9.6.1은 canonical projection `{key, ce}`.
- §12.3/golden은 key fields를 top-level로 flat.
- nested-key literal hash:
  - base `33c945a2…e0ca62c`
  - supplemental `e5936867…f1f253c`
  - registered는 `c43ea…`/`8277a7…`.

**v1.0.4 요구**:
- canonical hash record는 **flat 8-field object**:
  `{doc_id, arm, seed, variant, endpoint, memory_kind, donor_id, ce}`.
- `key`는 sort용 tuple이며 nested object로 hash하지 않는다.
- phase-7 `baseline_ce`/`delta`는 hash domain에서 제외.
- 예시 JSON + SHA256 재계산.

### MF-4. 12-key checkpoint map serialization (medium)

- `final_checkpoint_hash` 12 keys는 선언됐지만 JSON shape/file binding 없음.
- GLM MF-C, DS MF-5, Sol MF-3.

**v1.0.4 요구**:
- `final_checkpoint_hash.json`:
  ```json
  {
    "F/20261108": "sha256:...",
    "L/20261108": "sha256:...",
    ...
  }
  ```
- 12 keys exactly `arm/seed`.
- checkpoint file path `checkpoints/{arm}/{seed}.pt`.
- replay loads each unit; no single checkpoint.
- `control_digest` field in `control_manifest.json`.

### MF-5. P1 frozen hash vs postrun inventory (medium)

- `checked_artifacts: []` is valid pre-run.
- after artifacts, completeness undefined.
- freeze manifest hash vs later inventory updates.

**v1.0.4 요구**:
- `p1_usage.json` is frozen at freeze time with empty inventory.
- postrun adds `p1_usage.postrun.json` listing actual artifacts; does not modify frozen file.
- `assay_path_ok` uses frozen hash; postrun inventory used for audit.
- expected artifact registry path.
- `note` unknown-key allowed.

### MF-6. Control fixture shape (low/medium)

- control golden `[1,1]`, spec `[K_M,512]`.
- synthetic framing fixture vs real digest conflation.

**v1.0.4 요구**:
- declare synthetic fixture explicitly.
- add realistic-shape fixture or declare real `control_digest` postrun-only.
- name-asc order note; `531ba0ad…` is insertion-order artifact, not normative.

### MF-7. External module contracts (low)

- `Adapter`, `make_labels`, `load_layer_cache`, `LoRALinear`, `repeated_4gram_rate` are external.
- self-containedness conditional.

**v1.0.4 요구**: append helper module paths + commit hashes; no behavior change.

### MF-8. D0 labels/manifest timing (low)

- `labels_computed:false` semantics and control manifest build timing.
- D0 4 configs.

**v1.0.4 요구**: one-line clarification.

### MF-9. Per-arm notation (low)

- restate `F=360, L=360, P=480, PA=480, total 1,680`.
- 155 min envelope label.

### MF-10. dtype_str/fixture order/P1 note (cosmetic)

- `dtype_str` `<f4` style.
- control fixture listing order vs digest order.
- `p1_usage` note unknown key.

---

## 4. 검토자별 핵심

### GLM — CONTINUE(조건부)

- 10/10 closed.
- MF-A baseline_ce source; MF-B null sort; MF-C map format; MF-D dtype; MF-E inventory; MF-F fixture order; MF-G note.
- freeze + 구현 + D0 승인; D1/3-seed 미승인.

### DS 1017 — NARROW

- 9 closed / 1 partial.
- MF-1 phase-7 K_d/control slicing; MF-2 baseline_ce; MF-3 null order; MF-4 supplemental vs diagnostic digest; MF-5 map/control_digest; MF-6 P1 registry; MF-7 fixture shape; MF-8 module contracts; MF-9 D0 labels; MF-10 notation.
- freeze after ERRATA.

### Sol — NARROW

- 7 closed / 3 partial.
- MF-1 phase-7 prefix/baseline; MF-2 flat hash projection; MF-3 12-checkpoint serialization; MF-4 P1 frozen vs postrun.
- freeze no.

---

## 5. 결정

```text
v1.0.3 = 동결 보류 (1 CONTINUE / 2 NARROW)
v1.0.4/ERRATA = 필요 (text/schema only)
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

1. v1.0.4 text/schema:
   - phase-7 `K_d`/`baseline_ce`
   - null total order
   - flat 8-field hash projection
   - 12-key map JSON
   - P1 frozen vs postrun
   - control fixture shape
   - external module contracts
   - D0 labels/timing
   - per-arm notation
2. v1.0.4 review
3. freeze commit + content SHA256 + `p1_manifest_sha256`
4. 구현 + unit tests
5. D0
6. D1 separate
7. 3-seed separate

---

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_3_2026-11-09/review_GLM.md` | GLM |
| `.../review_DS1017.md` | DeepSeek |
| `.../review_SOL.md` | Sol |
| `reports/C5_B0A_PM_PREREG_V1_0_3_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |
| `docs/plan_c5_b0a_pm_prereg_v1_0_3.md` | v1.0.3 |
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_3_2026-11-09/golden_vectors.json` | golden |

## 8. 제한

- 이 종합은 승인이 아니다.
- NARROW 2/3가 우세하다.
- v1.0.4 없이 코드를 작성하지 않는다.
- P0는 historical native-path sensitivity이며 trained P/PA/L 증거가 아니다.
- golden digests are verified constants, not results.
