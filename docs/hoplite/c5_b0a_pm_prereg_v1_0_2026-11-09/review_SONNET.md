# v1.0 External Review: Claude Sonnet 5.5 (reasoning medium)

I am the **Claude Sonnet 5.5 (medium reasoning) independent reviewer**. This is a read-only consultation and I did not use another model's answer.

- Reviewed HEAD: `78fa7b4`. `git pull --ff-only origin main` reported "Already up to date".
- The request names `631e180` as its basis, but that commit is not present in this shallow checkout. I could not diff against it. The freeze record must pin the plan file's own SHA-256.
- I ran no training or evaluation. I did not open test 163, use P1 or call external APIs. T5Gemma2 stays closed by D-108.
- The only file I wrote is this report.
- Checks I ran:
  - The preflight SHA-256 is `3ee3f1ca…837af`, which matches §0.4.
  - Both golden digests reproduce independently with `printf`, `jq` and `sha256sum`, not through the repo code. State `43ecb58e…d65712` matches. Replay `c43ea35c…851667` matches the canonical JSON of the three records in the golden file.
  - The preflight lengths agree with the spec: 15 val docs have h ≥ 753, doc `01331` sits at exactly 753, K=754 gives 14, there are 16 train contributors, and all native lengths are 512.

## Verdict: **NARROW**

v1.0 does close most of the r3.4 Must-fix list at the text level. It is not yet a single implementation authority, because of two things:

1. It contradicts itself on the P/PA M cohort and the record counts (MF-1).
2. It leaves the replay procedure, several validity flags and the measurement semantics undefined. It also hands the training and eval objective to code that lives outside the document.

None of the fixes needs a new scientific choice, threshold or seed. Each is a drafting fix or a pre-result choice between options already on the table. That is why this is NARROW and not STOP.

---

## Q1–Q13

**Q1. Self-containedness — conditional (leans disagree).**
- Evidence:
  - §0.1 says an implementer can write code from this document alone.
  - v1.0 never defines the following, and the only definitions are in `runner/c5_mt5_lora_b0.py` or older docs:
    - the training loss and label format;
    - the `copyable_mask` and `copy_ce` token definition, and how "copy tokens ≥5" is counted;
    - how donors are chosen (5 length-matched donors excluding self, and what ordering gives donor ordinals 0–4);
    - whether `shuffled_*_ce` is the mean over the 5 donors;
    - F/L adapter initialization (only PA is stated as "random-init");
    - the source prefix and tokenization (`summarize: `, 512 for native);
    - generation decoding settings.
  - `assay_path_ok`, `p0_path_ok`, `p_step100_path_ok`, `pa_step100_path_ok` and `test_split_used` are used in §4.2–4.4 and never defined.
  - The replay procedure is never defined (see Q4).
  - §0.1 says "do not reference earlier r3.x docs", but v1.0 relies on the runner for the items above.
- Next steps:
  1. Add a §2.5 "Measurement semantics" that is normative and not code-by-reference. It should cover the copy mask, `copy_ce`, the donor rule and ordering, per-document donor averaging, the training loss, F/L adapter init and decoding.
  2. Add a definitions table for each path flag: its computing function, the artifact it reads, and its true / false / NA conditions.
  3. If some items are deliberately inherited from the runner, say so. Freeze the runner commit and the relevant function hashes. Otherwise drop the "self-contained" claim.

**Q2. Decision contract — agree, with small fixes.**
- Evidence:
  - I hand-checked the §3.4 table against the `ANDn`/`NOT3` definitions for all 9 rows. They are consistent.
  - The §6.3 dispatch is total, and every branch has an `else`. Fixtures 16–18 follow from the primitives.
  - F1–F11 are consistent with the §4.2–4.4 ordering.
  - Small points:
    - MF-5 asked for "n_signal ≥ 15 only, otherwise NA". The §6.3 dispatch instead keeps `l_signal` live under small-N labels. The dispatch looks like the intended behavior, so the prose should be reconciled.
    - §3.5 does not name the cohort for `L_COPY_SIGNAL` and `L_FULL_SIGNAL`. I assume the retained 15 L-eligible docs.
    - Neither the "paired L>F" nor the "CI" statistic says whether it is computed on seed-averaged per-document deltas. §10.3 implies it.
    - §13.5 says "no stale `seeds_positive`", but §10.2 defines `seeds_positive`. Reword it to "no legacy mislabeled key", because the legacy helper's `seeds_positive` actually counts documents.
- Next steps:
  1. State the cohort and aggregation in §3.5.
  2. Reconcile the MF-5 prose with the §6.3 dispatch.
  3. Add an exhaustive 9×{validity}×{n small/ok} dispatch test.

**Q3. Variant × memory_kind — agree.**
- Evidence:
  - §9.4 gives each variant its own control tensor and a shared `real_prefix_t`.
  - `M_PASS_POS` uses `delta_pos` and `M_PASS_NORM` uses `delta_norm`. They are distinct tests, since the control tensors differ.
  - 15×3×4×2×2×2 = 1,440 and 96 per target are correct for a 15-target-for-all-arms design.
  - One note: `M_PASS_*` uses `>0` and `CI lower>0`, while `L_COPY_SIGNAL` uses `.05`. This is internally consistent and pre-registered. Do not tune it afterwards.
- Next steps:
  1. The Q4 cohort contradiction below changes the 1,440 and 96 figures if P/PA move to 20 docs.
  2. Pin the exact key set as a literal enumeration in a test.
  3. Add a degeneracy test that fails if `M_NORM` equals `M_POS_MEAN` for a document with equal norm.

**Q4. M builder / M_NORM / endpoint / replay — disagree (blocking).**
- Evidence:
  - **Cohort contradiction.** §4.5, §5.2 and §8.3 say P/PA `m_pass_*` use the **20 native docs**. §9.1 gives P/PA M targets as "15 common" and "contributors 20". §9.5 counts 1,440 records for all four arms at 15 targets. §11.3 phase 5 gives 120 per arm-seed for every arm. §5.1 `builder_ok` requires 15 norms.
  - These cannot all hold. The 20-doc reading gives 15×8×2 + 20×8×2 = 560 records per seed, so 1,680 total, with 96 appearances for the 15 common targets and 48 for the other 5. Phase 5 for P/PA would be 160 per arm-seed. T_proj would change.
  - **Replay is only partly specified.** §5.1 has `replay_ok`, §11.4 has the domains, and §12.2 has the hash. Nowhere does it say what is replayed (reload the final checkpoint and recompute all phase-5 CE?), what is compared (per-record CE, `atol=1e-5`, `rtol=1e-4`), or what the exact hash covers. A recomputed CE will not hash identically. So "hash exact" can only mean the stored artifact record set, and that needs to be said.
  - **Record schema.** The sort key uses `donor_sort` (−1 or 0..4). The golden records carry `donor_id` (null or int) and no `donor_sort`. The mapping is implied, not stated.
  - **Float serialization.** The hash depends on how float64 is serialized (Python `repr` or shortest round-trip). That should be stated, because a golden digest in another language could differ.
  - The `real_prefix_t` / `M_NORM` definitions are fine. Both use the same adapter space. P is the identity and F/L use `[:753]`. No P/PA padding or 15→14 substitution is allowed.
- Next steps:
  1. Pick one P/PA M cohort before freeze. I lean to 20 native for P/PA, because it matches MF-3 and §8.3, and reflect that in §9.1, §9.5, §11.3, T_proj and the key-set test. The alternative is to keep M at 15 common for all arms and use the 20 docs only for `P_VALID` and `PA_VALID`. Either is acceptable if stated once and propagated. This is a pre-result drafting choice, not a result-driven change.
  2. Write a normative replay algorithm: input checkpoint hash, records recomputed, comparison rule, and what "hash exact" covers.
  3. Add a `donor_id`↔`donor_sort` mapping line and a float serialization rule. Add a golden vector that mixes null and integer donors.

**Q5. F/L K scope — agree.**
- Evidence:
  - §2.3 limits K=753 to M only. Training and eval signal use donor-crop `K=min(len_real,len_donor)`, and generation uses 20×256 with no padding, dropping or reordering.
  - This addresses the 4 train and 5 val short documents. The preflight shows 5 val docs below 753 (718, 751, 750, 708, 728) and 16 train contributors at 753.
  - Risk to note: a donor-cropped signal on a short document trains and evaluates on a shorter memory than M tests. That is a design property, not a defect. It does mean `l_signal` and M are measured at different K, and the spec should say so in one sentence.
- Next steps:
  1. Add a sentence stating the K difference between signal (donor-crop) and M (753).
  2. Add a unit test where the real length is 718 and the donor is 760 (K=718), and one at exactly 753.
  3. In D0, assert the 20-doc train order and the 4 short train docs unchanged.

**Q6. P/PA — conditional.**
- Evidence:
  - §4.5 defines `P_VALID` and `PA_VALID` directly on 20 native docs, which closes MF-3 and MF-7. §5.3 now words the PA veto as a joint calibration failure and not proof that the native regime is invalid.
  - `PA_RETENTION` is non-gate and the 512-vs-753 geometry caveat is stated.
  - The seed handling of `P_VALID` and `PA_VALID` is undefined. It does not say whether they use seed-averaged deltas, per-seed deltas, or all three seeds, and there is no missing-seed rule. §3.5 has one for L but §4.5 does not.
  - Note for honest expectation, not a change: a random-init adapter at lr 1e-3 for 100 steps may fail `PA_VALID`. The veto then yields `PA_STEP100_NOT_VALID` and an uninformative M. The document should state that this outcome is acceptable and does not trigger any retune.
  - The P0 val20 docs are the same documents `P_VALID` uses. P0 is descriptive and untrained, so there is no gate leakage, but it should be disclosed that val20 is not fresh.
- Next steps:
  1. Define the seed aggregation and the missing-seed rule (NA, consistent with §3.5) for `P_VALID` and `PA_VALID`.
  2. State in the document that an uninformative P/PA outcome is a permitted terminal result.
  3. Disclose the P0 reuse of val20.

**Q7. Statistics / tail — conditional.**
- Evidence:
  - Constants are fixed: `n_boot=1000`, percentile 2.5/97.5, seed 20261109, document-level unit, seed-average first.
  - `documents_positive` is defined (count of delta>0) and tested, but no gate or label uses it. State that it is descriptive only.
  - The signal-tail rule is clear: L, copy, shuffled donor, variant NA, 15 docs. M tails are descriptive. The ties rule is deterministic and the rule is total over NA, with n<4 → `leave_top3_mean`=NA.
  - The gate is `top3_abs_share > .50`. P0 gives .43355 on val20 and .455 on the 15 common docs, so the tail block is a live possibility. The threshold stays unchanged.
  - The tail delta does not say whether it is per-seed or seed-averaged per document. Use seed-averaged, to match §10.3.
  - Minor: the bootstrap seed 20261109 equals the second registered training seed. This is harmless but confusing.
  - The tail gate covers the copy endpoint only. The full endpoint has no tail check. That is a design choice to note, not change.
- Next steps:
  1. Say that the tail delta is the seed-averaged per-document delta.
  2. Mark `documents_positive` descriptive-only.
  3. Add tests for ties at the top-3 boundary and for a negative-sum denominator.

**Q8. D0 / D1 / cap — conditional.**
- Evidence:
  - The arithmetic works: phase 5 is 15×2×2×2 = 120 and phase 7 is 15×5×2×2×2 = 600 per arm-seed. Total cap 1,200 updates plus 4 debug updates is 1,204. 120 + 15 + 20 = 155 min.
  - T_proj multiplies 100× a single measured update. The first update includes warmup and allocation cost, so the projection is biased high. That is conservative and acceptable.
  - T_proj assumes serial execution (`3 * sum arms`). The spec lists 6 threads and never says whether the 12 units run serially or in parallel. D1 must use the same thread and parallelism configuration as the registered run.
  - If the Q4 fix moves P/PA to 20 docs, phase 5 and T_proj change for P/PA.
  - D0 is described as `labels_computed:false`, but it still has to run the encoder and adapter forward for the M builder and h-length assert. Say which D0 steps need a forward pass.
- Next steps:
  1. Specify serial vs parallel execution and require D1 to match it.
  2. Recompute phase 5 and T_proj after the Q4 cohort decision.
  3. List the D0 checks explicitly (h-length assert, state hash golden, replay golden, enum assertions) and mark that D0 produces no timing or CE claims.

**Q9. Hash / golden — mostly agree.**
- Evidence:
  - Both golden digests reproduce from an independent construction. The state frame spec is unambiguous for `<f4`.
  - The state vector covers only `<f4`. The real state includes LoRA A/B and adapter parameters. If any are bf16 or fp16, the `dtype_str` must be fixed for them. State the dtype that the real checkpoint uses.
  - The replay vector has three records and no mixed null and integer donors, so it does not test `donor_sort` ordering.
  - Hash coverage is stated: checkpoint hash is postrun, `debug_replay_hash` is D1-only, and they are never compared.
- Next steps:
  1. Add one more replay golden with permuted input, null and integer donors and a duplicate key (expected: rejection).
  2. Fix the dtype string for each tensor type in the real state.
  3. Fix the float serialization rule (Q4).

**Q10. Remaining Must-fix — see ranked list below.** I agree v1.0 closes the r3.4 items at the text level: the variant table, signal-tail variant=NA, P/PA 20-native validity, L binding, K scope, `PA_VALID`, top3 absolute/signed, `documents_positive` and the golden digests. It introduces or leaves open the items listed under "Must-fix".

**Q11. Freeze and implementation approval — conditional.**
- Evidence: freeze after the Must-fix edits below. Implementation, unit tests and the D0 zero-update mechanics debug are acceptable after that, because D0 produces no result and has no label computation.
- Also, a document cannot contain its own hash. §16.2 should say the freeze is recorded in a separate record (commit hash plus plan SHA-256) that is not part of the plan.
- Tests required before D0: the §13 matrix, plus:
  - the P/PA cohort and key-set tests after the Q4 decision;
  - a replay-algorithm test;
  - a path-flag derivation test.
- Next steps:
  1. Apply Must-fix 1 to 5.
  2. Freeze with an external record.
  3. Implement `runner/c5_pm_stats.py` and the pure decision function first, with the golden vectors read from the JSON file and never from implementation output.

**Q12. B0-B / D1 / 3-seed — agree, with a restatement.**
- Evidence: §14 requires VALID, `M_CONTROL_PASS`, `EXPLORATORY_L_SIGNAL`, `m_valid`, `n_signal ≥ 15`, `tail_driven == false`, leakage/mode/metric pass, a complete artifact and a separate prereg and approval. §0 and §16.3 exclude D1, 3-seed and B0-B/B1/B2/Stage C from this approval.
- Restated B0-B predicate in v1.0 labels:
  `validity_status==VALID ∧ control_status==M_CONTROL_PASS ∧ m_valid==true ∧ signal_status==EXPLORATORY_L_SIGNAL ∧ n_signal==15 ∧ tail_driven==false (top3_abs_share ≤ .50 on the L/copy/shuffled-donor signal tail, with leave_top3_mean > 0) ∧ M scope M_CONTROL_PREFIX753_COHORT15 ∧ artifact complete`, and only as eligibility to write a separate prereg. It approves nothing.
- Next steps:
  1. Add the restated predicate to §14.
  2. Keep D1 and 3-seed under separate approvals, each citing the freeze record.
  3. State that a terminal `M_NOT_EVALUABLE` or `PA_STEP100_NOT_VALID` ends the line without a retune.

**Q13. Final verdict: NARROW.**
- Freeze v1.0 once the Must-fix edits are applied.
- Self-contained as a single authority: not yet.
- Approval scope after the edits: implementation, unit tests and D0.
- D0 only if a fresh reviewer or the owner checks the edited document against the Must-fix list.
- D1 and 3-seed are not approved. The cap in §11 stays as written: 1,200 updates and 120 min for the registered run, plus separate D0 and D1 allowances.
- Phase 6, B0-B, B1, B2 and Stage C are not approved.
- Test 163 stays sealed, P1 stays unused and T5Gemma2 stays closed.

---

## Must-fix (ranked)

1. **P/PA M cohort contradiction** (§4.5/§5.2/§8.3 say 20 native, §9.1/§9.5/§11.3 say 15 with 1,440 and 120). Choose one before freeze. Propagate to record counts, per-target appearances, `builder_ok`, phase 5 and T_proj.
2. **Replay algorithm undefined**: what is replayed, what is compared, and what the exact hash covers. Also state the `donor_id`↔`donor_sort` mapping and the float serialization rule.
3. **Measurement semantics not in the document**: copy mask and `copy_ce`, donor selection and ordering, shuffled-CE averaging, training loss, F/L adapter init and decoding settings. Add them, or declare and freeze the runner functions as an explicit dependency.
4. **Undefined validity flags**: `assay_path_ok`, `p0_path_ok`, `p_step100_path_ok`, `pa_step100_path_ok`, `test_split_used`. Define each with its inputs and NA conditions.
5. **Aggregation gaps**: seed handling for `P_VALID`/`PA_VALID` (including the missing-seed rule), the cohort and aggregation for `L_*_SIGNAL`, and the tail delta (seed-averaged). Reconcile the MF-5 n_signal prose with the §6.3 dispatch.
6. **D1/T_proj execution mode**: serial or parallel, with D1 required to match it.
7. **Freeze record**: external, because the plan cannot contain its own hash.
8. **Minor**: mark `documents_positive` descriptive-only, fix the `seeds_positive` wording in §13.5, fix the real checkpoint dtype string, add the extra golden vector, and state that an uninformative P/PA or M result is terminal.

## Wrong premises or caveats

- "Self-contained and total" overstates the state of the document (Q1, Must-fix 3 and 4).
- "1,440 records / 96 per target" only holds under the 15-target reading for P/PA.
- r3.4's "3/3 NARROW" is not evidence that v1.0 is complete. It only shows the earlier Must-fix list was addressed.
- The P0 deltas (+5.2 nats on untrained memory, untrained CE above ln|V|) show path sensitivity only. They say nothing about trained P, PA or L and should not be used to set expectations for any gate.
- No trained result has been seen. Nothing in this review proposes changing a threshold, seed, donor, step count or LR.