# C5 Phase 6 P/M Prereg v1.0.2 — Independent External Review

- Reviewer: **DeepSeek V4.1 Flash 1017 (high)** — `deepseek-v4.1-flash-1017` via OpenRouter
- Round: v1.0.2 (separate, independent round; prior v1.0.1 3/3 NARROW is historical input only)
- Review date: 2026-11-09
- Mode: **consultation only, read-only**

## 0. Sync and review basis

```text
git fetch origin          -> ok (no new refs reported)
git pull --ff-only origin main -> "Already up to date."
HEAD                      -> 445a9cc2b1ff758edd807da659a3e50c9c703d1d
subject                   -> "docs: add C5 P/M v1.0.2 review request"
```

- The workspace is a depth-1 clone; the review request's stated basis `1f6b816`
  is **not present as a local object** (`fatal: Not a valid object name`).
- Therefore this review's basis is the current `origin/main` HEAD `445a9cc`,
  which is the commit that adds this review request and contains every artifact
  listed in it. I did not deepen the clone; no spec content differs between the
  request's file list and HEAD.
- Artifact hashes observed at `445a9cc`:

| artifact | SHA-256 |
|---|---|
| `docs/plan_c5_b0a_pm_prereg_v1_0_2.md` | `834fe640609fedb30ab356d3e450b237a9b3d4351ae33dc498ac89566ab86e59` |
| `.../golden_vectors.json` | `36af0b2d3d31e88979c9305569540d34c4b664e40aa97dbe5debd7c2f4a1e959` |
| `reports/provenance/C5_b0a/m_cohort_preflight.json` | `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` (matches §0.4) |

Constraints observed: no training/evaluation run, test 163 not opened, P1 not
used, no subagents/other LLMs, T5Gemma2 remains D-108 STOP, Phase 6/B0-B/B1/B2/
Stage C not approved. Only this report file was written.

Independent checks I actually executed (read-only):

- recomputed all four golden digests from the stated frame/canonicalization;
- recomputed cohort/zero-margin counts from preflight;
- recomputed the P0 descriptive numbers from `p0_native_sanity.json`;
- recomputed the M record arithmetic (1,680 / 560 / 600 / 96 / 48);
- read the runner and metric tests to test whether v1.0.2 is executable as
  written against existing code.

---

## 1. Summary judgment

> **NARROW.** v1.0.2 genuinely closes the structural half of the v1.0.1
> blockers: 12 of 15 are closed outright, 3 are partial, 0 are open. P0
> compatibility, arm-specific donors, control-tensor storage, the ID allowlist,
> `h_len`, P/PA seed aggregation, validity/calibration separation, copy-token
> scope, threshold intent, F11, training mode/RNG, and D1 semantics are fixed
> and checkable. Two new contract-binding defects remain, both in the
> replay/golden layer, plus a per-arm arithmetic error in `T_proj`: the replay
> canonical record field is `donor_sort` in §12.2 but `donor_id` in the frozen
> golden vectors (verified: the two canonicalizations hash to different
> values), the replay procedure asks one checkpoint to reproduce all 1,680
> records, and the registered per-arm primary-replay counts are stated as
> 420/420 instead of 360/480. Until those are fixed by numbered ERRATA the spec
> is **not** a single, self-contained implementation authority, because its own
> mandatory golden test cannot be satisfied by an implementation that follows
> §12.2 literally.

---

## 2. Q1 — Are the 15 v1.0.1 blockers closed?

Verdict: **conditional (12 closed / 3 partial / 0 open)**.

| # | Blocker | Status | Evidence |
|---:|---|---|---|
| 1 | P0 `no_training` | **closed** | §4.0 now defines `p0_path_ok` by `mode=p0_sanity_no_training` + `test_split_used=false` only. Actual artifact keys are exactly `experiment, mode, model, source_prefix, source_max_length, donor_count, splits, interpretation, test_split_used`—there is **no** `no_training` key, and `mode` is `p0_sanity_no_training`, `test_split_used` false. P0 numbers unchanged (train +3.7617 [1.8917,5.6050], val +5.2375 [2.5013,8.0753]). |
| 2 | donor basis | **closed** | §2.5.6 gives two length maps (F/L EG2 layer19 `h_len`; P/PA native length after `summarize: ` truncation 512), per-arm donor lists, same list within an arm across seeds, no train20 donor pool, `donor_id=0..4`, `shuffled`=wrong-donor. Correctly resolves the v1.0.1 contradiction. |
| 3 | replay control tensors | **closed** | §12.1 specifies `control_manifest/arm/seed/M_POS_MEAN.npz` and `M_NORM/{t}.npz` with dtype/shape/id fields, JSON per-tensor SHA-256, and `control_digest` as integrity only ("hash-only reconstruction is forbidden"). Storage footprint is acceptable (~0.3 GB). |
| 4 | `test_split_used`/P1 | **closed** | §1.5/§4.0 allowlist membership (`train20 ∪ val20`), no scan of sealed test 163, `p1_usage.json` exists with `p1_used:false` and `test_split_read:false`; missing manifest → NA. Residual hardening in MF-6. |
| 5 | `h_len`/data paths | **closed** | §2.6 pins F5 JSONL, splits, EG2 cache, native model, and defines `h_len` as source length for both arms; `copyable_mask` on raw passage. Preflight independently confirms what v1.0.1 lacked: `train_native_lengths`/`val_native_lengths` are **all 512** (20/20 each), `native_contributors_at_512=20`, `native_target_eligible_at_512=20`. |
| 6 | P/PA seed aggregation | **closed** | §4.5: 3 registered seeds, seed mean then bootstrap, missing registered seed → NA, no 2-of-available. Consistent with §10.3. |
| 7 | P/PA alias / `M_CONTROL_INVALID` | **closed** | `p_valid := P_VALID` (artifact validity) is distinct from `P_POS_PASS` (calibration); `m_valid` is four calibration operands; §5.4 routes calibration failure to `M_CONTROL_INVALID`. Aliasing removed. |
| 8 | copy-token `<5` | **closed** | §2.5.5 splits scopes: signal/eval excludes the doc, primary M sets `endpoint_ok=false` → `M_NOT_EVALUABLE`; no silent key omission. Compatible with the exact 1,680 key set. |
| 9 | phase-7 recipe | **partial** | §9.6.1 pins `K_d`, crops control/real/donor, and the 600 count, but declares `memory_kind ∈ {real, donor}` while the recipe's CE tensors are `control_pos`/`control_norm`/`real` (and `wrong` only sets `K_d`). The enum and the tensor set do not match. See MF-4. |
| 10 | threshold asymmetry | **closed** | §4.5 and §9.6.1 state P/PA copy `>= .05`, L M copy `>0`; documented as intentional, no post-result change. Values unchanged. |
| 11 | F11 label | **closed** | §6.2/§7.2 give `INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL` plus an explicit `validity=INVALID` triple; §7.3 fixes dispatch order and the false-l_signal fallback. |
| 12 | training mode/RNG | **closed** | §2.7 per-arm mode table, base decoder eval, adapter/LoRA train, fresh state per arm, `manual_seed → adapter → LoRA` with no reseed, parameter-inventory assert. |
| 13 | T_proj primary replay | **partial** | §11.5 adds `t_primary_replay_arm`, but the registered per-arm counts are wrong (420/420 vs 360/480) and conflict with the `3 × Σ_arm` per-seed structure. See MF-3. |
| 14 | D1 no-labels/`not_a_result` | **closed** | §11.3 distinguishes decision/signal labels from target-token CE labels, sets `not_a_result:true`, debug seed 20261111, 1 update/arm. |
| 15 | golden coverage | **partial** | Supplemental vector added (P/PA native-20, `M_NORM`, `donor_id=4`), spec label updated to v1.0.2, and **all four digests reproduce exactly**. But the frozen records use `donor_id` while §12.2's canonical key uses `donor_sort`; the two hashes differ. See MF-1. |

Next steps:

1. Accept 12 closures as written; do not reopen them.
2. Fix items 9/13/15 via numbered ERRATA (MF-1..MF-4) before freeze.
3. Re-run only the golden/replay/`T_proj` arithmetic tests after ERRATA.

---

## 3. Q2 — Is v1.0.2 self-contained?

Verdict: **conditional**.

Evidence:

- §0.1 makes v1.0.2 the sole implementation contract and forbids reading r3.x;
  §15 marks history traceability-only.
- Measurement, tokenizer, loss, memory construction, adapter/LoRA init, donor
  rule, generation, aggregation, tail, hashes, and test matrix are all present.
  An implementer can build the pure decision function, stats, hash, donor and
  control-manifest code from this document alone.
- Residual external/ambiguous references:
  - §12.2 key field `donor_sort` vs golden `donor_id` (MF-1) — irreconcilable
    without a decision;
  - phase-7 `memory_kind` enum (MF-4);
  - §11.4 "load final_checkpoint_hash" (singular) then "1,680 keys" (MF-2);
  - "every checked artifact" in §4.0 is not enumerated (MF-6);
  - `Adapter`/`LoRALinear` module internals and `make_labels` live in
    `runner/c5_mt5_layer_probe.py` / `runner/c5_a1_lora.py`; the spec gives
    their required behavior but not their exact code. That is acceptable for a
    contract but means "spec only" implies reimplementation, not reuse.
- The existing runner is **not** the authority and must not be reused blindly:
  `set_training_mode` accepts only `"frozen"`/`"lora"` (no P/PA and no
  adapter-less P path), `bootstrap_paired` defaults to seed `20261108` and
  labels the document count `seeds_positive`, and `donors_for`'s docstring still
  says "same for all arms/seeds". §10.2 correctly forbids reuse.

Next steps:

1. Add a one-page "implementation appendix" that names the data schemas and
   states that the legacy runner is non-normative.
2. Resolve MF-1/MF-4 so no implementer decision is left open.
3. Keep §10.2's ban on the legacy bootstrap helper as a test assertion.

---

## 4. Q3 — Validity/calibration separation and `M_CONTROL_INVALID`

Verdict: **agree, with one tri-state clarification**.

Evidence:

- Reachability is restored and is **not** unconditional. Under v1.0.1,
  `p_valid = ANDn(P_POS_PASS,P_NORM_PASS)` made `p_valid=true ⇒ m_valid=true`,
  so §5.4's early exit made `M_CONTROL_INVALID` dead. In v1.0.2, `P_VALID` is
  artifact completeness/finiteness (20 native docs × 2 variants × 2 endpoints ×
  2 memory kinds × 3 seeds) with no numeric threshold, while `m_valid` is the
  four calibration predicates. Therefore `M_CONTROL_INVALID` is reached iff:
  `m_evaluable=true` **and** `p_valid=true` **and** `pa_valid=true` **and**
  some `*_POS_PASS`/`*_NORM_PASS` is false. It is gated by `m_evaluable`
  (cohort, endpoint, seed, replay, builder) and by all 6 arm-seed artifact sets
  being present and finite, so it is conditional, not unconditional.
- `p_valid`/`pa_valid` are used consistently in §4.4 and §5.4: §4.4 reports
  validity (`P_STEP100_NOT_VALID`/`PA_STEP100_NOT_VALID`), §5.4 reports control
  (`M_NOT_EVALUABLE`). The invariants in §4.7 match this split.
- Thresholds are internally coherent: P/PA copy `>=.05` matches
  `L_COPY_SIGNAL`'s copy threshold and is intentionally stricter than
  `M_PASS_*`'s `>0`; full is `>0` in both. No post-result change is implied.
- Clarification needed: `P_VALID` includes "P step100 path valid". Under strict
  ANDn, `p_step100_path_ok=NA` forces `p_valid=NA`, so §4.6's stated cell
  "`p_step NA + p_valid=false` → `NOT_ASSESSABLE`" (and F9) describes an
  unreachable input combination. The output is the same, but the fixture's
  premise is ill-defined. Also unstated: whether a *nonfinite* CE yields
  `p_valid=false` (known failure) or `NA`. See MF-5.
- Secondary observation (not a frozen-threshold change): P/PA calibration lacks
  the `2/3 seeds_positive` and paired `L>F` conditions that the L predicates
  carry. This is a deliberate arm asymmetry unless documented otherwise; it
  makes `m_valid` slightly weaker as an aggregation while stronger on copy
  effect size. Document, do not retune.

Next steps:

1. ERRATA: state the per-condition tri-state map for `P_VALID`/`PA_VALID`
   (missing → NA, nonfinite → false) and make `P_VALID` path-agnostic or fix F9.
2. Keep `.05`/`>0` exactly as frozen.
3. Document the P/PA-vs-L aggregation asymmetry in §4.5.

---

## 5. Q4 — Donor arm-specificity and executability

Verdict: **agree**.

Evidence:

- §2.5.6's two length maps are correct and mutually exclusive: F/L use EG2
  layer19 `h_len` (preflight val range 708–830, so nearest neighbours differ per
  doc); P/PA use native length after truncation, which preflight shows is
  **512 for all 20 val docs**, so the P/PA donor order is the deterministic
  `doc_id`-ascending tie-break over the other 19 val IDs.
- This reproduces the v1.0.1 counterexample: for
  `REPORT-news_r-04161-00002` the EG2-nearest and native-nearest sets differ, so
  arm-specific lists are required and are now specified.
- Same donor list for all seeds within an arm; `donor_id=0..4` in sorted order;
  train20 has no donor pool; `shuffled` means wrong-donor memory; real CE is the
  mean over the same 5 donor crops; donor lists/lengths are artifacts.
- The existing `native_donors_for` sorts by `(abs(len[c]-len[rid]), c)`, matching
  the spec's tie rule, so the rule is executable.

Next steps:

1. Emit the per-arm donor lists as a frozen artifact and pin its SHA-256 in the
   manifest.
2. Assert in unit tests that F/L and P/PA lists differ for at least one doc.
3. Keep donors out of training and out of primary M (§2.3/§9.2 already do).

---

## 6. Q5 — Control tensors and replay executability

Verdict: **conditional / disagree as written**.

Evidence:

- Storage and integrity are now real: `.npz` tensors plus per-tensor SHA-256 and
  a `control_digest` that is explicitly not a substitute. `atol=1e-5`,
  `rtol=1e-4` for numeric replay, exact SHA-256 for artifacts, and debug/final
  hashes are separate fields. §11.4 forbids comparing debug to final directly.
  This closes the v1.0.1 "hash cannot reconstruct memory" blocker.
- Two executability defects:
  1. **Record key name.** §12.2 defines the canonical key with `donor_sort`
     (`-1` for null, `0..4` otherwise). The frozen golden records use
     `donor_id` (`null`/`0`/`4`). I computed both: the frozen records reproduce
     `c43ea35…` and `38e5e2f…` exactly, while renaming to `donor_sort` yields
     `32db40bf5bfcdc6df8b64b083227df0812eb67de1efa3dcf19688c22bb9d7ffe`
     (base) and `1ccdee0319172149b21a1dbc688902c7803495cbcec4a736db53ced1c108d922`
     (supplemental). An implementation that follows §12.2 literally fails the
     mandatory golden test.
  2. **Replay scope.** §11.4 step 1 loads one `final_checkpoint_hash` state,
     then step 3 says "recompute phase-5 primary M CE for exact 1,680 keys".
     One arm-seed checkpoint can produce only 120 (F/L) or 160 (P/PA) primary
     records; 1,680 is the 12-checkpoint total. `replay_ok` must be defined per
     checkpoint (120/160), aggregated across the 12 units, and §11.4 must say so.
- The supplemental digest is a 4-record canonicalization vector, not the
  phase-7 600-record replay hash; §11.4 step 5's "verify supplemental replay
  digest" conflates the two. Name them separately.

Next steps:

1. ERRATA: adopt the golden field name (`donor_id`) in §12.2, or regenerate
   nothing and rename the key in the plan. Do not change frozen digests.
2. ERRATA: define replay per checkpoint (120/160) and the 12-unit aggregation to
   1,680; keep phase-7 replay separate.
3. Split `golden_supplemental_digest` from `phase7_replay_hash` in §11.4/§12.3.

---

## 7. Q6 — Allowlist / P1 without opening test 163

Verdict: **conditional**.

Evidence:

- §1.5/§4.0 decide `test_split_used` by membership in frozen
  `train20_ids ∪ val20_ids`, never by scanning the sealed file. That is the
  correct way to prove non-use without access.
- `p1_usage.json` exists at HEAD with `p1_used:false`, `test_split_read:false`,
  and a note; §1.5 requires the manifest for `assay_path_ok`, and missing →
  NA. Known-failure dominance is stated (false beats NA).
- Gaps: `assay_path_ok` only requires "`p1_used=false` manifest exists"; it does
  not check `test_split_read=false`, does not pin the manifest's SHA-256, and
  does not enumerate which artifacts are "checked". An ID-free artifact set
  would pass vacuously. Allowlist rejection is correct but untested at the
  artifact-walk level.

Next steps:

1. Require both `p1_used=false` and `test_split_read=false`, and pin the P1
   manifest hash in §4.0.
2. Enumerate the checked artifacts (checkpoint manifests, replay records,
   preflight, M/control manifests).
3. Add a unit test that an out-of-allowlist ID yields `test_split_used=true`
   without touching the test file.

---

## 8. Q7 — Data paths, `h_len`, copyable mask, P/PA 512

Verdict: **agree**.

Evidence:

- §2.6 pins every path used by the runner (`data/external/f5_pairs_v3_clean.jsonl`,
  `reports/provenance/C5_clean/splits.json`,
  `data/wave2c/eg2_native_layer19/layer19`, `data/models/mt5-small`), the JSONL
  fields, and the split fields.
- `h_len` is defined as source sequence length, not tensor shape, separately for
  F/L (EG2 cache `lengths[i]`) and P/PA (native ids after `summarize: `
  truncation at 512). §9.2's builder and §9.8's zero-margin use the same
  definition.
- `copyable_mask` is computed on the raw passage (no prefix), which is the
  correct denotation for "copied from the passage".
- The all-512 claim is **verified in preflight**, not merely asserted:
  `val_native_lengths` and `train_native_lengths` are all 512 (20/20),
  `native_contributors_at_512=20`, `native_target_eligible_at_512=20`. The
  plan should cite these fields, and D0's h-length assert should check them, so
  a future data change cannot silently break the uniform-shape assumption.

Next steps:

1. Cite `val_native_lengths` / `native_target_eligible_at_512` in §2.6 and §9.8.
2. Make D0 assert all 20 native val lengths are 512 and abort otherwise.
3. Keep the zero-margin rule (753; 754→14; no substitution).

---

## 9. Q8 — M arithmetic and tensor shapes

Verdict: **agree**.

Evidence (recomputed):

- per arm-seed primary M: F/L `15 × 2 variants × 2 endpoints × 2 memory = 120`;
  P/PA `20 × 2 × 2 × 2 = 160`.
- per seed: `120+120+160+160 = 560`; D1 (4 arms × 1 debug seed) = **560**.
- registered: `560 × 3 = 1,680`; common target appears
  `3 seeds × 2 × 2 × 2 × 4 arms = 96` times; native-only
  `5 × 2 × 2 × 2 × 2 arms = 48`; `15×96 + 5×48 = 1,440+240 = 1,680`. Correct.
- phase 7: `15 × 5 donors × 2 variants × 2 endpoints × 2 memory = 600` per
  arm-seed. Correct as a count (but see MF-4 for the enum).
- cohort: preflight gives val ≥753 = **15**, val ≥754 = **14** (zero margin
  real), train ≥753 = **16** contributors (≥10 builder floor).
- shapes: `M_POS_MEAN` and `M_NORM(t)` are `[K_M,512]` with `K_M=753` (F/L) or
  `512` (P/PA); `real_prefix_t` matches; P/PA native docs are all 512, so no
  ragged shape.

Next steps:

1. Keep `endpoint_ok` as an exact key-set check, not a count check.
2. Unit-test `96`/`48` per-target multiplicities and the duplicate/missing-key
   rejection.

---

## 10. Q9 — D0/D1/cap arithmetic

Verdict: **disagree on the registered per-arm replay counts**.

Evidence:

- D0: 0 updates, ≤4 configs, ≤15 min, seed 20261111, `labels_computed:false`
  (decision/signal labels), `not_a_result:true`, h-length assert, no timing
  claim, separate cap. Consistent.
- D1: 4 arms × 1 debug seed = 4 units, 1 update/arm, ≤20 min, 8 phases, phase 5
  = 560 total (120/120/160/160), phase 7 = 600/arm-seed, `not_a_result:true`.
  Consistent.
- **Error:** §11.5 states "registered primary replay = 1,680 total; per arm F/L
  420, P/PA 420". The correct registered per-arm totals are **F/L 360** and
  **P/PA 480** (`120×3`, `160×3`); 420 is only `1680/4` and ignores the 15-vs-20
  cohort mix. It also contradicts the `3 × Σ_arm(...)` structure, inside which
  `t_primary_replay_arm` must be per arm-seed (120/160), not per registered arm.
- `T_proj` still cannot be numerically confirmed (no authoritative per-step
  durations), but the ≤96 min cap, 120-min abort, `1,204 updates / 155 min`
  prospective ceiling, and "D1 without D0 forbidden" are coherent.

Next steps:

1. ERRATA: replace 420/420 with 360/480 and state the per-arm-seed vs registered
   unit explicitly in §11.5.
2. Add an arithmetic unit test for `T_proj` (D1 560; registered 1,680).
3. Do not raise the cap.

---

## 11. Q10 — Remaining Must-fix (ranked)

| rank | severity | item |
|---:|---|---|
| 1 | **blocker** | Replay record key field: §12.2 `donor_sort` vs golden `donor_id`. Verified divergent hashes (`32db40…`/`1ccdee…` vs `c43ea…`/`38e5e2f…`). Freeze would create an unsatisfiable mandatory test. |
| 2 | **blocker** | §11.4 replay scope: one `final_checkpoint_hash` cannot reproduce 1,680 records. Define per-checkpoint 120/160 and 12-unit aggregation. |
| 3 | high | §11.5 registered per-arm replay counts 420/420 are wrong (360/480) and conflict with the per-seed formula. |
| 4 | medium | Phase-7 `memory_kind` enum `{real,donor}` contradicts the recipe's `control_pos`/`control_norm` tensors and the supplemental `control` record; §12.2 uses `{control,real}`. Fix the enum/tensor mapping (600 count unchanged). |
| 5 | medium | `P_VALID` tri-state undefined for missing vs nonfinite; §4.6's F9 premise (`p_step NA + p_valid false`) is unreachable because `P_VALID` includes path validity. |
| 6 | medium | P1 manifest integrity: `assay_path_ok` ignores `test_split_read:false`, does not pin the manifest hash, and "checked artifacts" is unenumerated. |
| 7 | low | P/PA calibration omits the `2/3 seeds_positive` and paired `L>F` conjuncts used by L; document as intentional arm asymmetry (no threshold change). |
| 8 | low | Cite preflight `val_native_lengths`/`native_target_eligible_at_512` and add the D0 512 assert to §2.6/§9.8. |
| 9 | low | `control_manifest` footprint (~0.3 GB) and storage path are not in the cap/artifact list; specify path and retention. |

Assessment of the three risks the request names specifically:

- **Is `P_VALID` now too weak, making `M_CONTROL_INVALID` unconditional?** No.
  It is artefact-completeness only, but `M_CONTROL_INVALID` still requires
  `m_evaluable=true` (5 operands incl. replay/builder) and `p_valid=pa_valid=true`
  across 6 arm-seed sets. Under a clean run these hold almost always, so
  `M_CONTROL_INVALID` becomes the **default calibration-failure route**—which is
  the intended semantics—not an unconditional label.
- **Is `control_manifest` too heavy?** No. F/L `753×512×4B ≈ 1.54 MB` × 15
  targets × 3 seeds × 2 arms ≈ 139 MB; P/PA `512×512×4B ≈ 1.05 MB` × 20 × 3 × 2
  ≈ 126 MB; plus means. ~0.3 GB total is acceptable and necessary for replay.
- **Does arm-specific donor hurt F/L vs P/PA comparability?** It removes a false
  equality rather than creating one. Length-matched donors per memory space are
  the correct control; cross-arm comparisons are already disclaimed by the
  geometry caveat (§8.2) and by "not comparable as same population" (§11.4).

---

## 12. Q11 — Freeze / implementation / D0

Verdict: **conditional**.

- **Freeze now: no.** MF-1 and MF-2 make the frozen contract internally
  unsatisfiable at the golden/replay layer; MF-3 misstates a cap input. These
  are text-level ERRATA, not new science.
- **Freeze after ERRATA 1–4: yes.** No further scientific choice is needed.
- **Implementation + unit tests: conditional.** Pure decision function, stats,
  hash, donor, allowlist, and control-manifest code can be implemented and
  tested immediately after ERRATA. Model-coupled replay/training code should
  wait for the same ERRATA.
- **D0 zero-update mechanics: conditional yes** after ERRATA; it is data-only,
  ≤15 min, ≤4 configs, 0 updates, `not_a_result:true`, and it is exactly the
  place to discharge the native-512 and h-length asserts.
- Minimum required tests before implementation is considered done:
  1. golden state `43ecb…`, empty `e3b0…`, replay base `c43ea…`, supplemental
     `38e5e2f…`, with the reconciled field name;
  2. F1–F11, the 9 L pairs, fixtures 16–18, NA propagation, every label
     reachable, no `M_CONTROL_NOT_VALID`;
  3. `M_CONTROL_INVALID` positive test (validity true + calibration false) and
     negative tests (path/validity false → not invalid);
  4. exact 1,680 key set with 96/48 multiplicities, duplicate/missing reject;
  5. per-checkpoint replay 120/160 plus 12-unit aggregation to 1,680;
  6. donor arm-specificity, `donor_id 0..4`, `shuffled`=wrong-donor;
  7. allowlist rejection without reading test 163;
  8. tail top3 tie rule, `n<4` → NA, denominator 0 → NA;
  9. `T_proj` arithmetic including primary replay.

---

## 13. Q12 — Boundaries and restated B0-B predicate

Verdict: **conditional (boundaries are sufficient; predicate needs restatement)**.

Evidence:

- D1 is 4 units × 1 debug seed × 1 update, `not_a_result:true`, separate
  approval. 3-seed is 12 units, separate. B0-B is a separate downstream gate
  with its own prereg/approval. No auto-continuation is specified. This is the
  right boundary.
- Restated B0-B predicate against v1.0.2 labels:

```text
validity_status              == VALID
AND control_status           == M_CONTROL_PASS        # implies m_evaluable, p/pa valid+calibrated, m_pass_l
AND signal_status            == EXPLORATORY_L_SIGNAL
AND m_valid                  == true
AND n_signal                 == 15                    # §6.1 max is 15, so ">=15" is exactly 15
AND tail_driven              == false                 # signal tail only; true/NA block
AND leakage/path/mode/metric checks pass
AND artifact set complete (12 checkpoints, manifests, hashes)
AND a separate prereg and approval exist
```

- `M_CONTROL_PASS` already entails `m_pass_l=true` and P/PA calibration, so the
  listed `m_valid`/`M_CONTROL_PASS` conjunction is redundant but harmless.
  `full_k_secondary`, P0, and `PA_RETENTION` remain non-evidence. Scope label
  `M_CONTROL_PREFIX753_COHORT15` is appropriate.

Next steps:

1. Write `n_signal == 15` (not `>=15`) and define tail `NA` as blocking.
2. Keep B0-B/B1/B2/Stage C explicitly unapproved by this round.

---

## 14. Q13 — Final verdict and freeze

Verdict: **NARROW**.

The 15 v1.0.1 blockers are substantively answered (12 closed, 3 partial), and
the scientific protocol is now largely implementable. It is not yet a single
authority because its own golden/replay contract is self-contradictory and its
registered replay arithmetic is wrong. These are narrow, numbered-ERRATA fixes;
none requires a new experiment or a post-result threshold change.

```text
최종 판정: NARROW

v1.0.2 freeze:            NO now; YES after numbered ERRATA 1-4
구현+unit tests:          CONDITIONAL YES (decision/stats/hash/donor/allowlist/manifest
                          after ERRATA; model-coupled replay after ERRATA)
D0:                       CONDITIONAL YES (0 updates, <=4 configs, <=15 min, seed 20261111,
                          not_a_result, native-512 + h-length assert)
D1:                       NO (separate approval, 4 units x 1 debug seed x 1 update, <=20 min)
3-seed:                   NO (separate registered run, 12 units, 120 min hard abort)

금지 범위:
  - Phase 6 F/L/P/PA registered run
  - 3-seed, B0-B, B1, B2, Stage C
  - test 163 access; P1 use; external API on P1
  - T5Gemma2 (D-108 STOP)
  - any threshold/seed/donor/step/LR change after seeing results
  - reusing the legacy runner/bootstrap as authority

최대 compute (this round):
  - D0: 0 optimizer updates, <=4 configs, <=15 min, CPU (no GPU)
  - unit tests: CPU only, no model forward required beyond fixtures
  - prospective (NOT granted): 1,204 updates / 155 min; registered 1,200 updates / 120 min

Must-fix (ranked):
  1. golden/replay key field donor_sort vs donor_id (blocker)
  2. §11.4 per-checkpoint vs 1,680 replay scope (blocker)
  3. §11.5 registered per-arm replay 420/420 -> 360/480 (high)
  4. phase-7 memory_kind enum vs control tensors (medium)
  5. P_VALID tri-state map and F9 premise (medium)
  6. P1 manifest content/hash and checked-artifact enumeration (medium)
  7. P/PA vs L aggregation asymmetry documented (low)
  8. cite native-length preflight fields; D0 512 assert (low)
  9. control_manifest path/footprint in artifact list (low)

v1.0.2 self-contained:   CONDITIONAL — yes for the protocol, no while MF-1/MF-4
                          leave the implementer a forced choice
잘못된 전제:              (a) that one checkpoint can replay 1,680 records;
                          (b) that "per arm 420" is a meaningful split;
                          (c) that §12.2's key name matches the frozen golden vectors;
                          (d) that phase 7 has only two memory kinds while also
                              defining control cropped tensors.
```

This is a consultation, not an approval of Phase 6/B0-B/B1/B2/Stage C. Test
163 remains sealed, P1 remains unused, and T5Gemma2 remains under D-108 STOP.