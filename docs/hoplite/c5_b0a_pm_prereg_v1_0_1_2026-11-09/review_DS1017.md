# C5 Phase 6 P/M Prereg v1.0.1 — Independent External Review

**Reviewer identity:** DeepSeek V4.1 Flash 1017 (Hoplite model `deepseek-v4.1-flash-1017`), reasoning **high**.
**Review date:** 2026-11-09
**Review basis:** `origin/main` at **`30b62191afe88d0a36389871e3a69fc524b4bbaa`** (`30b6219 docs: add C5 P/M v1.0.1 review request`).
**Mode:** Consultation only. Read-only. No training, no evaluation, no test 163, no P1, no subagents/extra LLMs, no threshold changes after results.

---

## 0. Sync and evidence base

Commands run:

```text
git fetch origin            -> branch main -> FETCH_HEAD (no new objects reported)
git pull --ff-only origin main -> "Already up to date."
git rev-parse HEAD          -> 30b62191afe88d0a36389871e3a69fc524b4bbaa
```

- The review request header names `7ecf973` as its writing basis. The current `origin/main` HEAD is `30b6219` (the review-request commit). The workspace is shallow (depth 1), so I cannot independently prove `7ecf973` is an ancestor; I reviewed the artifacts as they exist at `30b6219`.
- The normative spec is 1,431 lines and is the only implementation authority candidate. I read it in full, plus `golden_vectors.json`, the v1.0 synthesis, the preflight, the P0 report and artifact, `runner/c5_mt5_lora_b0.py`, and `eval/tests/test_c5_b0_metric.py`.
- I did **not** reuse any other model's review. I did **not** open test 163 or P1 data.

### 0.1 Independently reproduced hashes and arithmetic

| Item | Expected | Recomputed | Result |
|---|---|---|---|
| preflight content SHA-256 | `3ee3f1ca…69837af` | `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` | **match** |
| state golden | `43ecb58e…d65712` | `43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712` | **match** |
| empty golden | `e3b0c442…b7852b855` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | **match** |
| replay golden | `c43ea35c…f7851667` | `c43ea35c46c51a0e82cebe5764a989d1b67012b2690246a0f89a94dff7851667` | **match** |
| endpoint records | 1,680 | `(2·15 + 2·20)·3·2·2·2 = 1,680` | **match** |
| D1 phase 5 | 560 | `(2·15 + 2·20)·2·2·2 = 560` | **match** |
| phase 7 / arm-seed | 600 | `15·5·2·2·2 = 600` | **match** |
| common target appearances | 96 | `4·3·2·2·2 = 96` | **match** |
| native-only appearances | 48 | `2·3·2·2·2 = 48` | **match** |
| F/L contributors at K=753 | 16 | 16 train docs `h_len ≥ 753` | **match** |
| L target cohort | 15 | 15 val docs `h_len ≥ 753`; 754 → 14 | **match** |
| P0 val mean/median/positive | 5.2375 / 2.9739 / 18 | recomputed from `per_doc` | **match** |
| P0 val top3 absolute / signed | .43355 / .4862 | recomputed; common-15 absolute `.45478` | **match** |

The arithmetic and the three golden digests are internally correct. The defects below are **definition/binding** defects, not arithmetic errors.

---

## 1. Overall judgment

> **v1.0.1 genuinely closes the v1.0 *textual* Must-fix set (MF-1…MF-9) at the level of intent, and its 1,680 / 560 / 600 arithmetic is correct. It is nevertheless not yet freezeable/implementable as a single total authority.** Concrete binding defects remain: the P0 artifact does not satisfy the spec's own `p0_path_ok`; donor ordering is internally contradictory across arms; replay hashes do not carry reconstructable control tensors; `test_split_used`/P1 verification is operationally undefined; `h_len` and data paths are not normative; and P/PA seed aggregation is unspecified. These are text-only repairs plus one small artifact change, so the correct disposition is **NARROW**, not STOP.

---

## 2. Q1–Q13

### Q1. Self-containedness

- **Verdict: conditional**
- **Evidence:** The document now contains normative measurement semantics (§2.5), donor rule (§2.5.6), path flags (§4.0), replay procedure (§11.4), control digest (§12.1), bindings (§4.5), and 3^6 calibration axis (§7.1). That is a large improvement over v1.0 and is sufficient for a reader to understand the intended experiment. However, it is not total: `h_len` is used for cohort selection, zero-margin, donor ordering, and `builder_ok` (§1.2, §2.5.6, §9.2, §9.8) but is never normatively defined; the EG2 layer-19 cache path/format, split file, JSONL schema, and record fields are not pinned in the plan (the runner constants are `data/wave2c/eg2_native_layer19/layer19` and `reports/provenance/C5_clean/splits.json`); and the source string used by `copyable_mask` is ambiguous between the passage and the `summarize: `-prefixed source (§2.5.1 vs §2.5.5).
- **Next steps:**
  1. Add an implementation appendix defining `h_len` per arm (F/L: EG2 layer-19 cache sequence length; P/PA: native source token length after `summarize: ` truncation at 512), with the exact cache path/format and split-file schema.
  2. State whether `copyable_mask` uses the passage or the prefixed source; pin the JSONL fields consumed.
  3. Either pin a runner commit + function hashes or declare the named functions (e.g., `read_jsonl`, `attach_decoder_lora_mt5`) as normative aliases.

### Q2. Decision contract

- **Verdict: agree with one caveat (conditional)**
- **Evidence:** The validity dispatch (§4.2–§4.4), `m_evaluable`/`m_pass_l`/`m_valid` (§5.1–§5.2), control dispatch (§5.4), and signal dispatch (§6.3) are total over the tri-state values; F1–F10 match the dispatch order; fixtures 16–18 derive correctly from the stated primitives; `ANDn` 2/4/5 and the 9 L pairs are enumerated. The caveat is **F11**: its expected output is written as `small-N + validity INVALID`, which is not one of the labels in §6.2. §6.3 returns `INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL` / `..._WITH_COPY_ONLY` / `..._WITH_FULL_ONLY` / `INCONCLUSIVE_SMALL_N`, and §6.4 says validity is preserved in the tuple. A test cannot assert an undefined label.
- **Next steps:**
  1. Define F11's expected label as one of the four §6.2 labels plus an explicit `(validity_status=INVALID, ...)` tuple assertion.
  2. Add a reachability test that every §6.2 label is returned by the dispatch, including the `l_signal=NA` / `control` fall-through paths.
  3. Add a test that `m_evaluable` false/NA collapses to `M_NOT_EVALUABLE` without hiding P/PA validity.

### Q3. Mixed M domain

- **Verdict: agree**
- **Evidence:** The mixed domain is arithmetically and structurally consistent: F/L 15 common, P/PA 20 native (15 common + 5 native-only), primary 1,680, common target ×96, native-only ×48, D1 phase 5 560, phase 7 600/arm-seed, `m_valid` on P/PA-20, `m_pass_l` on L-15. Preflight confirms `common_ids=15`, `native_target_eligible_at_512=20`, and the 5 excluded short val docs. No silent 15→14 or native→common substitution is present. **Caveat:** this verdict concerns arithmetic/cohort consistency, not donor identity (see Q4/MF-2).
- **Next steps:**
  1. Keep Option A (mixed) as the frozen choice; do not reopen common-only.
  2. Add a manifest assertion that the exact mixed key set equals 1,680 (not only the count).
  3. State that `m_valid` is a gate input and cannot be computed on a different cohort than 20 native.

### Q4. M builder / M_NORM / endpoint / replay

- **Verdict: conditional**
- **Evidence:** The builder (§9.2), P identity, `real_prefix_t`, `M_NORM` (§9.3), variant×memory table (§9.4), endpoint identity (§9.5), and delta/pass rules (§9.6) are coherent and reproduce 1,680. However, three concrete problems remain:
  1. **Donor identity is contradictory.** §2.5.6 says the donor set is "same … for all arms/seeds," but also says "donor lengths from the same cache as the real document." Preflight shows all native lengths are exactly 512 while F/L `h_len` ranges 708–830. Therefore P/PA donor ordering (all-equal lengths → `doc_id` order) cannot be the same list as F/L ordering (length-nearest), unless one basis is imposed for all arms.
  2. **Replay cannot reconstruct the controls.** §12.1 defines `control_digest` as a SHA-256 over `M_POS_MEAN` and `M_NORM/t`, and §11.4 step 1 says "load `final_checkpoint_hash` state + `control_digest` manifest," then step 3 recomputes 1,680 CE. A digest is not the tensors. Without stored control tensors (or a deterministic rebuild from train20 + seed + checkpoint), replay is not executable.
  3. **Replay counts are mixed.** §11.4 says "primary M replay … total 560," but the registered postrun replay is 3 seeds × 560 = 1,680; step 3 then says "exact 1,680 keys," while §11.3 D1 phase 5 is 560. The text must distinguish D1 debug replay (560) from registered replay (1,680).
- **Next steps:**
  1. Define donor ordering per arm as `(abs(h_len_arm[c] − h_len_arm[rid]), c)` and state donor sets are per-document; or impose a single EG2-based donor order for all arms and use native memory only for P/PA donors.
  2. Store `M_POS_MEAN` and `M_NORM/t` in a manifest/artifact with the state frame (or define deterministic rebuild), and make `control_digest` verify that artifact.
  3. Restate replay as: D1 debug = 560 primary; registered final = 1,680; never compare hashes across the two.

### Q5. F/L memory length scope

- **Verdict: conditional**
- **Evidence:** §2.3 correctly separates training real memory from eval donor-crop and generation 20×256, and §9.8 enforces K=753 only for M. But the phrase "all 20 train/val docs" under "Training/eval signal" remains ambiguous: training forward consumes train20, while the signal endpoint is val20; there is no train-split signal endpoint. The training-memory length policy is also unspecified (full real sequence up to the EG2 length, or a cap). The v1.0 synthesis MF-8 specifically asked for this split, so it is not fully closed.
- **Next steps:**
  1. Replace "all 20 train/val docs" with "training forward: train20 real memory; eval signal: val20 donor-crop; no train signal endpoint."
  2. State the training memory length (full real `h` length; no 753 requirement; no donor crop) and the eval crop `K=min(len(real), len(donor))` explicitly.
  3. Add a D0 h-length assertion covering the 4 train / 5 val short docs.

### Q6. P/PA

- **Verdict: conditional**
- **Evidence:** P/PA-20 native, `P_POS_PASS`/`P_NORM_PASS`/`PA_POS_PASS`/`PA_NORM_PASS`, PA veto, `PA_RETENTION` non-gate, and the 512-vs-753 geometry caveat are present and internally consistent (§4.5, §5.3, §8). The missing piece is **seed aggregation**: §4.5 says "20 native val20 docs, 100-step" but never states whether the passes use 3 registered seeds, seed-average-before-bootstrap, or per-seed. §10.3's "same retained IDs copy/full/L−F" is L-centric and does not cover P/PA. Without this, `m_valid` is not executable identically across implementations.
- **Next steps:**
  1. Add: P/PA passes use 3 registered seeds, seed-average per document before bootstrap, missing registered seed → NA, no pooling.
  2. State the bootstrap unit (document) and the CI rule for P/PA explicitly, mirroring §10.3.
  3. Clarify that P/PA validity is 100-step-only and does not use test 163 or P1.

### Q7. Statistics / tail

- **Verdict: agree**
- **Evidence:** `n_boot=1000`, `bootstrap_seed=20261109`, `documents_positive`, `seeds_positive` (registered seed means >0), 2/3 registered, missing-seed NA, signal-tail `arm=L`, `endpoint=copy`, `control=shuffled donor`, `variant=NA`, 15 common, absolute-top3 gate, tie rule (`|delta|` desc then `doc_id` asc), and `n<4 → leave_top3_mean=NA` are all defined and executable (§10). I independently reproduced P0's val mean 5.2375, median 2.9739, 18/20 positive, signed .4862, absolute .43355 (val20) and .45478 (common-15). The plan's `.455` common-15 value is consistent within rounding. The runner's legacy `bootstrap_paired(seed=20261108)` and mislabeled `seeds_positive` are correctly flagged as non-reusable; the new `runner/c5_pm_stats.py` does not yet exist, which is consistent with "no code before freeze."
- **Next steps:**
  1. Add a test that `documents_positive` and `seeds_positive` are distinct quantities and that missing seeds are NA, not 2-of-available.
  2. Add a test that the tail gate uses `top3_abs_share`, while signed share is descriptive only.
  3. Add an explicit P0-to-Phase-6 non-comparability note (P0 `source_max_length=256` vs M 512).

### Q8. D0 / D1 / cap

- **Verdict: conditional**
- **Evidence:** The arithmetic is correct: 12 units × 100 updates = 1,200; prospective max 1,204 updates / 155 min (120 registered + 15 D0 + 20 D1); D0 0 updates / ≤4 configs / ≤15 min / seed 20261111; D1 4 arms × 1 debug seed / 1 update per arm / ≤20 min; D1 phase 5 = 560; phase 7 = 600/arm-seed; `T_proj ≤96 min`. Two wording/spec problems remain:
  1. §11.3 says D1 has "no labels," but phase 5 computes copy/full CE, which requires target labels. If "labels" means decision labels, say so and add `not_a_result:true` to the D1 manifest (as D0 does).
  2. `T_proj` includes `t_initial_M_ce_arm` and `t_replay_15x5x2x2x2_arm` (phase 7) but not the primary phase-5 replay recomputation (560/seed, 1,680 registered). The projection can therefore under-estimate the registered replay cost.
- **Next steps:**
  1. Replace "no labels" with "no decision/result labels; CE target labels are data, not result labels" and add `not_a_result:true` to D1.
  2. Add `t_replay_phase5_arm` (or a second `t_initial_M_ce_arm`) to `T_proj`, or state explicitly that phase-5 replay is inside `t_overhead_arm`.
  3. Keep D1 and 3-seed as separate approvals; no auto-start.

### Q9. Hash / golden

- **Verdict: agree on digests; conditional on completeness**
- **Evidence:** The state frame, replay key, canonical JSON (`sort_keys=true`, `separators=(',',':')`), `donor_sort=-1/0..4`, float64 finite rejection, exact artifact hash vs numeric tolerance (`atol=1e-5`, `rtol=1e-4`), and debug/final separation are defined. All three golden digests and the preflight hash reproduce exactly. Remaining gaps: `control_digest` is a hash, not a tensor store (Q4); §12.3 has only one replay vector (`L`/`M_POS_MEAN`/`donor 0`), so P/PA, `M_NORM`, and donor `0..4` canonicalization are untested; the golden file header still says `spec: C5 Phase 6 P/M v1.0` rather than v1.0.1.
- **Next steps:**
  1. Add supplemental replay vectors for P/PA, `M_NORM`, and `donor_id` 0..4, with independent expected digests.
  2. Update the golden file `spec` label to v1.0.1 (or explicitly mark it as a v1.0-era directory).
  3. Specify whether `control_digest` covers all 15/20 target tensors and the exact key order; add a golden for the control digest.

### Q10. Remaining Must-fix

- **Verdict: disagree that v1.0.1 is freeze-ready; NARROW**
- **Evidence:** v1.0's MF-1…MF-9 are substantially addressed in intent: mixed 1,680, donor rule, wrong-donor definition, path flags, measurement semantics, replay procedure, control digest, training-vs-eval wording, bindings/axis/golden. But the following concrete defects remain, ranked:

| Rank | ID | Severity | Defect |
|---:|---|---|---|
| 1 | MF-1017-1 | **blocker** | **P0 artifact fails the spec's own `p0_path_ok`.** `p0_path_ok` requires `no_training=true` (§4.0), but `reports/provenance/C5_b0a/p0_native_sanity.json` top-level keys are `experiment, mode, model, source_prefix, source_max_length, donor_count, splits, interpretation, test_split_used` — there is no `no_training`. As written, `p0_path_ok=false` → `ASSAY_INVALID` for every Phase 6 run. |
| 2 | MF-1017-2 | **blocker** | **Donor identity contradiction.** §2.5.6 says "same donor set for all arms/seeds" but also "donor lengths from the same cache as the real document"; native lengths are all 512 (preflight), EG2 lengths vary 708–830. P/PA and F/L therefore cannot share one donor list under both rules. |
| 3 | MF-1017-3 | **blocker** | **Replay is not reconstructable.** `control_digest` is a SHA-256; §11.4 loads "control_digest manifest" and recomputes 1,680 CE. A hash cannot supply `M_POS_MEAN`/`M_NORM/t`. Store the tensors or define deterministic rebuild. |
| 4 | MF-1017-4 | high | **`test_split_used` / P1 verification is circular.** §4.0 defines it by testing whether artifacts contain a test ID, while test 163 is sealed and not read; no test-ID manifest or P1-usage artifact is defined. |
| 5 | MF-1017-5 | high | **Self-containedness gaps.** `h_len` is undefined; EG2 cache path/format, split file, and JSONL schema are not normative; `copyable_mask` source (passage vs prefixed source) is ambiguous. |
| 6 | MF-1017-6 | high | **P/PA seed aggregation undefined.** §4.5 does not say whether `P_POS_PASS`/`PA_POS_PASS` use 3 seeds, seed-average-before-bootstrap, or per-seed. |
| 7 | MF-1017-7 | medium | **Endpoint vs copy-exclusion contradiction.** §2.5.5 excludes docs with `<5` copy tokens from the copy endpoint; §9.5 requires exact 1,680, `copy_ce != None`, and `copy tokens >=5`. These cannot both hold if any doc drops below 5. |
| 8 | MF-1017-8 | medium | **Training/eval cohort wording.** §2.3 "all 20 train/val docs" still blurs train20 real forward and val20 donor-crop; training memory length is unspecified. |
| 9 | MF-1017-9 | medium | **D1 "no labels" / no `not_a_result`.** §11.3 says "no labels" but phase 5 computes CE; D1 is not explicitly marked `not_a_result`. |
| 10 | MF-1017-10 | medium | **F11 expected label undefined.** §7.2 `small-N + validity INVALID` is not a §6.2 label. |
| 11 | MF-1017-11 | medium | **`T_proj` omits primary phase-5 replay.** Formula includes phase-7 replay but not the 1,680-key phase-5 replay cost. |
| 12 | MF-1017-12 | low | **L>F pairing undefined.** §3.5 "paired L>F copy mean" lacks formal seed/doc pairing and aggregation. |
| 13 | MF-1017-13 | low | **Golden coverage/header.** Only one replay vector; no P/PA, `M_NORM`, donor 0..4; file says `spec: … v1.0`. |

- **Next steps:**
  1. Issue a text-only v1.0.2/ERRATA closing MF-1017-1…6; do not change thresholds, seeds, donor policy, step, or LR.
  2. Re-freeze with a content hash; then re-review the delta only.
  3. Keep MF-1017-7…13 as pre-implementation test/spec items; they can be closed during implementation if the freeze text is unambiguous.

### Q11. Freeze / implementation approval

- **Verdict: conditional (not approved as-is)**
- **Evidence:** §16.1 correctly says "No code before freeze." At HEAD `30b6219`, `runner/c5_pm_stats.py` does not exist and `eval/tests/test_c5_b0_metric.py` contains 7 P0-era metric tests, not a v1.0.1 decision/M/stats/replay suite. Approving "implementation + unit tests + D0" now would authorize coding against a spec whose P0 path flag is self-inconsistent and whose replay/control binding is incomplete. The correct sequence is: close MF-1017-1…6 as text-only repairs, freeze, then approve implementation + unit tests + D0.
- **Next steps:**
  1. After MF-1017-1…6, freeze v1.0.2 and approve implementation + the §13.1–§13.4 unit-test matrix + D0 (0 updates, ≤4 configs, ≤15 min, seed 20261111, `labels_computed:false`, `not_a_result:true`, h-length assert).
  2. Do not approve D1/3-seed in the same approval; keep them separate.
  3. Require the implementation to be tested against the three independent golden digests, not regenerated from the implementation.

### Q12. B0-B / D1 / 3-seed boundaries

- **Verdict: conditional (boundaries adequate; predicate must be restated)**
- **Evidence:** D1 is 4 arms × 1 debug seed, 1 update/arm, ≤20 min, separate approval; 3-seed is a separate registered run; B0-B is a separate downstream gate with no automatic B1/B2/Stage C. The §14 predicate includes validity, control, signal, `m_valid`, `n_signal`, `tail_driven`, leakage/mode/metric, artifact completeness, and separate approval. It is directionally adequate, but `leakage/mode/metric pass` is vague and `replay_ok`/`control_digest` are not explicit. Restated for v1.0.1 labels:

```text
B0-B_candidate =
  validity_status == VALID
  AND control_status == M_CONTROL_PASS
  AND signal_status == EXPLORATORY_L_SIGNAL
  AND m_evaluable == true
  AND m_valid == true
  AND m_pass_l == true
  AND n_signal == 15
  AND tail_driven == false
  AND test_split_used == false
  AND assay_path_ok == true
  AND p0_path_ok == true
  AND p_step100_path_ok == true
  AND pa_step100_path_ok == true
  AND endpoint_ok == true          # exact 1,680 mixed key set
  AND replay_ok == true            # final_replay_hash, 1,680
  AND control_digest_matches == true
  AND separate_prereg_and_approval == true
```

- **Next steps:**
  1. Replace `leakage/mode/metric pass` with named flags (`test_split_used=false`, `assay_path_ok=true`, `p0_path_ok=true`, mode assertions).
  2. Add `replay_ok` and `control_digest_matches` explicitly (they are implied by `m_evaluable`, but the gate should be auditable).
  3. Keep D1/3-seed/B0-B/B1/B2/Stage C as separate approvals; no auto-advance.

### Q13. Final verdict and freeze

- **Verdict: NARROW**
- **Evidence:** v1.0.1 is a substantial, mostly successful text-level repair. The 1,680 / 560 / 600 arithmetic, the golden digests, the preflight hash, the P0 statistics, the mixed cohort, the measurement semantics, the donor rule, the path flags, and the bindings are all present and mostly coherent. But it is not yet a total authority because of MF-1017-1…6 (P0 path-flag mismatch, donor contradiction, non-reconstructable replay, circular test-split verification, missing `h_len`/data paths, undefined P/PA seed aggregation). These are repairable without new scientific choices, so STOP is too strong and CONTINUE is premature.
- **Approval scope:** **No Phase 6 execution, no D1, no 3-seed, no B0-B/B1/B2/Stage C, no test 163, no P1, no T5Gemma2 re-open, no threshold/seed/donor/step/LR changes.** This round is consultation only; my only write is this report.
- **Next steps:**
  1. Produce a text-only v1.0.2/ERRATA closing MF-1017-1…6; add `no_training:true` to the P0 artifact or amend `p0_path_ok` to accept `mode=p0_sanity_no_training`.
  2. Re-freeze v1.0.2 with a content hash and re-review only the delta.
  3. After freeze, approve implementation + unit tests + D0 only; keep D1/3-seed/B0-B separate.

---

## 3. Final form

```text
최종 판정: NARROW

v1.0.1 freeze: 아니오 (MF-1017-1…6 text-only repair 후 v1.0.2/ERRATA로 재동결)
구현+unit tests: 아니오 (현재 기준). freeze 후 conditional yes.
D0: 아니오 (현재 기준). freeze 후 conditional yes (0 updates, ≤4 configs, ≤15 min, seed 20261111, labels_computed:false, not_a_result:true, h-length assert).
D1: 미승인 (별도 승인; 4 arms ×1 debug seed, 1 update/arm, ≤20 min, not_a_result).
3-seed: 미승인 (D1 이후 별도 registered run).
금지 범위: Phase 6 execution, D1, 3-seed, B0-B, B1, B2, Stage C, test 163, P1, T5Gemma2 (D-108 STOP), post-result threshold/seed/donor/step/LR changes.
최대 compute: 이번 라운드 0 updates / 0 min. Prospective cap 1,204 updates / 155 min is NOT granted.
Must-fix (ranked): MF-1017-1 P0 no_training/p0_path_ok; MF-1017-2 donor-set basis contradiction; MF-1017-3 replay control tensors; MF-1017-4 test_split_used/P1 verification; MF-1017-5 h_len/data paths/self-containedness; MF-1017-6 P/PA seed aggregation; then MF-1017-7…13.
v1.0.1 self-contained: 아니오 (conditional; h_len/data paths/replay tensors missing).
잘못된 전제: (a) P0 artifact satisfies p0_path_ok; (b) one donor set can serve F/L and P/PA under both stated rules; (c) control_digest alone is sufficient for replay; (d) test_split_used can be computed while test 163 is sealed without a test-ID manifest; (e) v1.0.1 is already a total single implementation authority.
```

---

## 4. Verified positives (for the record)

- Mixed domain arithmetic: 1,680 primary, 560 D1 phase 5, 600/arm-seed phase 7.
- Common target ×96, native-only ×48; exact mixed key set is well-formed.
- Preflight content SHA-256 `3ee3f1ca…69837af` matches the spec.
- State/empty/replay golden digests match independently computed values.
- P0 train/val means, CIs, medians, positive counts, and top3 shares reproduce.
- `test_split_used=false`, `no_training` absent (defect), `mode=p0_sanity_no_training` present.
- No v1.0.1 implementation exists at HEAD; `runner/c5_pm_stats.py` absent, consistent with "no code before freeze."

---

## 5. Non-approvals restated

I do **not** approve Phase 6, B0-B, B1, B2, or Stage C. I do **not** propose P1 or test 163 use. I do **not** reopen T5Gemma2 (D-108 STOP). I do **not** propose any threshold, seed, donor, step, or LR change after seeing results. This review is independent and was completed without subagents or additional LLM calls.
