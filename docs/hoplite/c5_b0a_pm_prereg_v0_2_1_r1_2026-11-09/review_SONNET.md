# External review — C5 Phase 6 v0.2.1-r1 (Sonnet 5.5, reasoning medium)

I am the **Sonnet 5.5 (medium reasoning)** independent reviewer for this round. I did not read or reuse any other model's answer for r1. I read the earlier v0.2.1 synthesis only as the Must-fix baseline the request names. Consultation only: no training or evaluation, no test 163, no P1, no repository edits other than this file.

- Sync: `git fetch origin` then `git pull --ff-only origin main` gave "Already up to date". **HEAD = 4920953bca28ab502372780e67e3f87f41082ec2**. The request itself was written at `0fce2e2`.
- Read: the review request, r1 (552 lines), v0.2.1 errata, the 3-AI synthesis, `m_cohort_preflight.json`, the P0 report, `runner/c5_mt5_lora_b0.py` (grep and targeted reads), and `eval/tests/test_c5_b0_metric.py`.
- Independent re-check of the preflight JSON, data-only:
  - Train lengths ≥753: 16, matching the stated contributors.
  - Val lengths ≥753: 15. K=754 gives 14, so 753 is the maximum K that keeps 15/20.
  - Full-K rule (a train count ≥10 at K_real = the target's own length) reproduces 11/20, with the same 9 excluded IDs.
  - The JSON does not store native source lengths, so "native 20/20 at 512" cannot be re-derived from the artifact.

## 0. Bottom line

**NARROW (r2, text-only plus tiny).** r1 closes most of the v0.2.1 Must-fix items in form. The factored output, the M preflight, the cap split and the statistics constants are real improvements.

r1 is not yet a total factored contract. Main problems:

- **M_VALID has no place in the status functions.** This is the biggest hole.
- Each status is still a first-match precedence chain, and the signal axis depends on the control axis.
- Several §2.8 test claims contradict §2.5.
- Some aggregation rules are undefined, such as seed pooling for P_VALID/PA_VALID.
- The "optional D1" conflicts with the "timing projection" launch gate.
- K_M_L=753 is a zero-slack boundary choice. It is defensible as a data-only choice, but it needs honest labeling.

None of this needs a threshold, seed, donor, step or LR change. It is all contract text.

## 1. Q1–Q12

### Q1. Factored decision — **conditional (disagree that it is yet total)**

**Evidence**
- **Missing input.** §2.4 `control_status` reads only `m_evaluable` and `m_pass_l`. `M_VALID` (§4.5: P and PA both pass M_POS and M_NORM) is in neither `validity_status`, `control_status`, nor the §2.8 input list.
- **Missing cell.** §4.5 says a P/PA M *missing* gives `M_NOT_EVALUABLE`, but P/PA M *failing* has no home. With m_evaluable=T, m_pass_l=T and P/PA M failed, r1 outputs `VALID / M_CONTROL_PASS / EXPLORATORY_L_SIGNAL`.
- **B0-B contradiction.** §9 requires "M valid + L M pass", so the contract contradicts its own B0-B prerequisite. r1 also deleted `M_CONTROL_NOT_VALID` (§2.4) without replacing the cell.
- **Not independent.** The axes are only partly factored:
  - Within each axis, `validity_status` is still a first-match chain (§2.3). P false hides PA NA/false, and PA NA hides `M_NOT_EVALUABLE`.
  - `signal_status` depends on `control_status`.
  - `M_NOT_EVALUABLE` appears in both validity and control.
  - Validity does not feed signal or control. The string `ASSAY_INVALID/M_CONTROL_PASS/EXPLORATORY_L_SIGNAL` can be emitted, and "EXPLORATORY" next to an invalid assay is misleading.
- **Weak Kleene use.** l_signal/copy_only/full_only use AND3/NOT3. But "any required signal flag NA → NOT_ASSESSABLE" ("required" undefined) fires first, so the Kleene short-circuit never changes an outcome. For example l_copy=F and l_full=NA gives l_signal=F by AND3, yet signal_status is NOT_ASSESSABLE.
- **Signal absent but control NOT_EVALUABLE.** When l_copy=F, l_full=F and control is `M_NOT_EVALUABLE`, the chain falls through to `NOT_ASSESSABLE`. The signal is assessable and negative, so this conflates "no signal" with "can't assess".
- **L lost in signal_status.** With l_signal=T and `control_status=NOT_ASSESSABLE`, nothing matches, so the label is `NOT_ASSESSABLE`. §2.8 says "L flag true → signal_status doesn't lose L", but §2.5's "n_signal<15 → INCONCLUSIVE_SMALL_N" does lose it. The flags retain L, so only the test sentence is wrong.
- **Ambiguous inputs.** "path/test flag" collapses several flags (assay_path_ok, p0_path_ok, p/pa step100 path, test_split_used) into one variable in §2.8.
- **Cheap test.** 3^7×4 = 8,748 combinations is cheap to enumerate. The domain needs consistency constraints, for example n_signal NA with defined flags.

**Next steps**
1. Add `m_valid` (tri-state, = AND3 of M_POS/M_NORM for P and PA) to the flag list.
   - Define `control_status` over it: `M_NOT_EVALUABLE` / `M_CONTROL_INVALID` (P/PA M false) / `M_CONTROL_PASS` / `M_CONTROL_FAIL` / `NOT_ASSESSABLE`.
   - `M_CONTROL_INVALID` is not on the deleted list and avoids the old `M_CONTROL_NOT_VALID` name.
2. Declare the "required signal flags" explicitly (l_copy, l_full). Add a signal label for "no L signal, control not evaluable", for example `NO_L_SIGNAL_CONTROL_NOT_ASSESSABLE`. Alternatively drop the Kleene-for-signal claim and say signal uses only l_copy/l_full.
3. Add a defined predicate `b0b_prerequisites_met = f(validity, control, signal, tail_driven, leakage)`. Fix §2.8 to say "L flags are preserved in `flags`; `signal_status` may be `INCONCLUSIVE_SMALL_N`". Replace the single `path` input with named flags.

### Q2. Signal labels — **conditional**

**Evidence**
- `INCONCLUSIVE_SMALL_N` is now reachable (n_signal<15). It is placed before the NA-flag check, which is fine.
- `MEAN_CONTRAST_ONLY` is defined as "control pass, no L signal". Whether it fires when copy_only/full_only is NA depends on the order of the NA-first rule, so the outcome is implementation-order dependent unless the pseudocode is fixed.
- **Boundary gap.** The cohort is exactly 15/20 and n_min is 15, so there is zero slack. P0 val copy coverage is ~.82. One doc with a missing copy mask drops n_signal to 14, giving `INCONCLUSIVE_SMALL_N` from a single doc. The same happens with a single NA for the common subset (§5).
- `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` is fine as a label.
- L flags are always preserved in `flags` (§2.7). They are not always preserved in `signal_status` (see Q1).

**Next steps**
1. Write the signal chain as ordered pseudocode that includes the required-flag set.
2. Add a boundary test for n_signal ∈ {14, 15, 16}.
3. State in the report template that n=15 is the minimum and one missing doc flips to `INCONCLUSIVE_SMALL_N`. This is a descriptive fact, not a threshold change.

### Q3. M preflight (K_M_L=753) — **conditional agree**

**Evidence**
- It is data-only: `no_model_forward`, `no_training` and `test_split_used:false` are all true. I reproduced 16 contributors, 15/20 and 11/20.
- Full-K as a gate is unreachable (11/20 < 15), so `M_NOT_EVALUABLE` would be near-certain otherwise. A prefix control is better than a permanently blank control, provided the labeling is honest.
- **Boundary choice.** 753 is the largest K at which val has 15 eligible docs. One included doc (`01331`, h=753) sits exactly on the boundary, and the cohort has zero margin. It was chosen using target-set lengths (val20), not outcomes. That is not outcome tuning, but it is a cohort choice made with knowledge of the target set and should be disclosed as such.
- **Length-selection bias.** The 5 excluded docs are the 5 shortest val docs. M-control inference is on the longer 15 docs, while L signal may be on up to 20.
- **Different reference.** M's real reference is the 753-prefix real CE (§4.3). L_SIGNAL uses full-K memory and donor-cropped wrong CE. So `M_CONTROL_PASS` is not a control on the same CE and cohort as the signal it gates.
  - It is a control on a related, truncated quantity.
  - The adapter was trained on full K and is evaluated on truncated memory.
- **Weak transfer of the validity half.** P/PA M validity runs at K=512 on native memory, on the common IDs from the 15 L docs. It validates the M assay on the native path, not on EG2 layer19.
- **Full-K principle.** r1 does not hide this: it says "secondary descriptive" and "not an M gate". The principle is bent but not silently broken.
- **Rule inconsistency.** The ≥10 contributor rule from v0.2.1 §3.2 is no longer stated in r1 (16 ≥ 10 here, so moot). The document should say whether it was dropped or kept.

**Next steps**
1. Label it `M_CONTROL_PREFIX753_COHORT15`. Require the report to state: control cohort = the 15 longest-of-20 val docs; the signal cohort may differ; M does not test full-K L memory.
2. Add a descriptive flag `l_signal_on_common15` (the L-signal computed on the same 15 docs). It does not enter `signal_status`.
3. Add native lengths per doc to the preflight JSON, and have the implementation re-run the preflight and assert `common_ids` equality by hash.

Accepting `M_NOT_EVALUABLE` outright would be the more conservative option. I judge the prefix design better, because it gives a negative control that can actually fail.

### Q4. M aggregation and replay — **conditional**

**Evidence**
- Leakage: M is built from train20 adapter outputs and evaluated on val targets, so there is no target leakage. M_NORM uses the target real norm, which is declared as a magnitude-matched control and not strictly target-independent (v0.2.1 §3.5, carried forward).
- Seed handling is unambiguous: per-seed builder, per-doc seed mean, then document bootstrap. A missing seed should give NA.
- **Replay tolerance is ambiguous.** The text gives `atol=1e-5` and `rtol=1e-4`. CE ≈ 13, so float32 eps alone gives ~1.3e-5 absolute. Does "within" mean the `np.allclose` sum rule or both conditions?
- **Replay failure is under-classified.** A replay failure maps to `M_NOT_EVALUABLE`, but a non-reproducible checkpoint reload is an assay problem, so it should also be `ASSAY_INVALID` for that arm. 9 replays (L, P, PA × 3 seeds) are not clearly inside or outside the 2h cap.
- **P/PA pooling undefined.** It is not stated whether P_VALID/PA_VALID are evaluated per seed (3/3, 2/3) or on the seed-averaged per-doc delta. Only L_SIGNAL has the 2/3 seed rule. This is a real gap.
- The runner's `bootstrap_paired` resamples values, not indices, so pairing is only safe if differences are bootstrapped. §5 says L>F is a paired difference, which is fine.

**Next steps**
1. State the replay criterion as `np.allclose(a, b, atol=1e-5, rtol=1e-4)`. Add replay-failure → `ASSAY_INVALID`. Count replay in the cap.
2. Define P_VALID/PA_VALID pooling (seed-averaged per-doc plus a seed-sign rule, or per seed). Do it as pre-result text.
3. Add a leakage test: M source IDs ∩ target IDs = ∅, and an explicit min-contributor rule.

### Q5. PA — **agree (conditional on caveat language)**

**Evidence**
- `PA_STEP100_NOT_VALID` replaces the causal name. The acquisition-control framing, the separate random-adapter step0 and the null-able `PA_RETENTION` (§3.2–3.3) are consistent with the earlier review.
- Retention is descriptive only and is not a gate, which is right.
- **Expected-failure risk.** PA_VALID uses the same `.05` gate on a randomly initialised Linear–GELU–Linear–LayerNorm adapter trained for 100 steps at lr 1e-3. P0 shows the native path has Δ≈+3.8, so P_VALID looks like a non-collapse screen. PA is a more demanding acquisition test, and PA failure may be common.
- A PA failure sets the validity axis, so it blocks B0-B and M_VALID.

**Next steps**
1. Add pre-result text: "PA_STEP100_NOT_VALID is not evidence for or against content use by L; it says only that the PA acquisition control did not reach the screen".
2. Record `adapter_delta_norm`, the step-0 random-adapter delta and the lora_b norm in the artifact (already listed in v0.2.1). Do not add a threshold on them.
3. Add the PA step0 and mT5-final-hidden vs EG2-layer19 caveat to the report template, not only the artifact.

### Q6. Cap — **conditional**

**Evidence**
- The arithmetic is now consistent: 12×100 = 1,200 registered. D0 has 0 updates and D1 has 4×1 update, accounted separately.
- The registered cap has zero slack: 1,200 updates with no retry.
- **D1 is "optional", but checklist item 6 requires a "timing projection ≤0.8×cap".** §6.5 says to extrapolate from D0/D1 timing. D0 has 0 updates, so it cannot measure backward and optimizer cost. Item 6 therefore effectively requires D1, contradicting §6.3's "D1 없이도 ... 통과 가능".
- **Seed for D1 not given.** v0.2.1 named an unregistered seed 20261111. r1 does not carry it forward, and D1 on a registered seed would be a contamination risk.
- **Wall-clock contents.** I cannot judge 2h feasibility from the repository. The costs of these are unknown:
  - each unit's evaluation (20 val × 5 donors × real/wrong forwards, ×2 at step0/step100),
  - M builds,
  - replays,
  - the 6-thread CPU runtime.

  D1 timing is needed. 0.8×2h = 96 minutes is a sound guard.
- There is no stated abort behavior at the cap: write a partial artifact marked `NOT_ASSESSABLE`, or discard?

**Next steps**
1. Make D1 a required gate item if the 0.8× projection is required. Alternatively define a D0-only projection method (forward-only timing × a fixed multiplier) as pre-result text.
2. Name the D1 seed (20261111 is already unregistered). State that D1 artifacts carry `not_a_result:true`.
3. Specify cap-abort behavior and whether eval, M and replay time count toward 2h.

### Q7. Statistics — **conditional**

**Evidence**
- The constants are fixed: n_boot 1000, percentile 2.5/97.5, seed 20261109, unit=document, seed-average first, top-3 share formula and leave-top-3-out.
- **Runner conflict.** The runner's `bootstrap_paired` default is **seed 20261108**. P0 used that default. r1 fixes **20261109**. This is a code-vs-contract mismatch that a test should catch.
- **Stale name.** `bootstrap_paired` still returns the key `seeds_positive`, but it counts documents (`(arr>0).sum()`). r1 §5 forbids this and the DoD has a test. The runner will fail that test until changed.
- With n=15–20 docs, the bootstrap CI is anti-conservative, which §5 acknowledges. I do not propose changing any threshold.
- **Unspecified bootstrap RNG scope.** It is not stated whether one RNG stream or a fresh generator per CI is used. Per-CI re-seeding with 20261109 gives correlated resamples across endpoints. That is deterministic and acceptable if stated.
- The `tail_driven` rule is a flag only. P0 val top-3 share (.486) is already near the .50 boundary. The flag is not tied to any status, so the B0-B "heavy-tail robustness" line is only informally connected.

**Next steps**
1. Change the runner default seed to 20261109 and rename the doc-count key in the implementation phase. Add tests for both.
2. State the RNG construction: one `default_rng(20261109)` per CI call, and which array is resampled for paired L−F (the difference array).
3. Add `tail_driven` to the `b0b_prerequisites_met` predicate (see Q1) instead of leaving it as an unconnected flag.

### Q8. Remaining Must-fix (ranked), and new problems from r1

Ranked, highest first:
1. **M_VALID missing from the decision function.** Add the tri-state `m_valid` and a control cell for "P/PA M failed". See Q1.
2. **P_VALID/PA_VALID/M seed pooling is undefined.** See Q4.
3. **§2.5/§2.8 contradictions and gaps.** Define required signal flags. Fix "L flag never lost". Cover the `l_signal=T` + control `NOT_ASSESSABLE` cell. Name the path flags. Add the combined predicate `b0b_prerequisites_met` (§9 vs statuses).
4. **D1 optional vs timing-projection gate.** Name the D1 seed and the cap-abort behavior. See Q6.
5. **Replay semantics.** Define `allclose`, classify replay failure as `ASSAY_INVALID`, and include replay in the cap. See Q4.
6. **753 labeling and cohort disclosure.** Add `M_CONTROL_PREFIX753_COHORT15` and the shortest-5 exclusion statement. Add native lengths to the preflight JSON. See Q3.
7. **Zero-slack cohort and n_min.** State that one missing doc flips to `INCONCLUSIVE_SMALL_N` or `M_NOT_EVALUABLE`. This is descriptive.
8. **Runner/contract constants.** The runner has bootstrap seed 20261108, the `seeds_positive` key, and no `pm-diagnostic` mode (`--mode` choices are smoke, metric-smoke, train, p0-sanity).

New problems r1 created:
- `M_NOT_EVALUABLE` is placed in both validity and control.
- The 753-prefix vs full-K mismatch between the M control and the L signal.
- A "required" flag set that is nowhere defined.

### Q9. Freeze and implementation approval — **conditional**

**Evidence**
- I do not think r1 should be frozen as written, because Q1 item 1 (M_VALID) changes the status functions and truth table.
- The fixes are text-only. I recommend r2, which changes only the Q8 items 1–6, then freeze, then implementation, unit tests and D0.
- The existing 54 tests are historical and cover the metric only. The PM tests do not exist yet.

**Required before or at implementation** (pure functions, no model)
- an exhaustive truth-table test (tri-state, 8,748 combinations with a domain constraint)
- Kleene operator tests
- a test that `m_valid` is a gate input
- label-reachability, flag-immutability and n_signal boundary (14/15/16) tests
- an M builder test (leakage-free, contributors=16, K=753, native 512)
- a test that the preflight is reproducible from the data (common_ids hash)
- seed aggregation, pooled-bootstrap and bootstrap-constant tests (seed 20261109; `documents_positive` naming)
- P step0 zero-LoRA and PA random-adapter step0 tests
- per-seed LoRA init reproducibility
- the absence tests (`ADAPTER_REGIME_LOSS`, `M_CONTROL_NOT_VALID`)
- an assertion that `test_split_used` is false

**Next steps**
1. Write r2 as a short text-only errata. Do not re-open anything else.
2. Freeze by commit hash after a quick re-read. A full 3-reviewer round should not be needed if the changes are limited to the Q8 items.
3. Implement the pure decision function first and gate the D0 run on its tests.

### Q10. D1 / 3-seed boundaries — **conditional**

**Evidence**
- D0 and D1 are separate from the registered cap and carry `not_a_result`/`labels_computed:false`, which is a good boundary.
- The checklist (§7) has 10 items.

**Missing from the 3-seed checklist**
- a clean git tree, with the r2 freeze hash equal to the doc hash used by the code
- the registered seed list 20261108/09/10 and a D1/D0 seed exclusion check
- a hash of the preflight JSON, and a re-run assertion of 15/20
- the cohort/donor ID hashes
- cap-abort behavior
- a replay plan inside the cap
- an artifact schema validator
- a statement of how a partial or missing seed is handled (NA, never a pooled headline)
- a D1 artifact review step: what D1 must show (shapes, finite, timing) without any result labels

**Next steps**
1. Add those items to the §7 checklist.
2. Resolve the D1 optional/required conflict (Q6).
3. Keep "explicit user approval" as item 8.

### Q11. B0-B boundary — **agree (conditional on the predicate)**

**Evidence**
- §9 says no label auto-approves B0-B/B1/B2/Stage C, and that `EXPLORATORY_L_SIGNAL` is exploratory. I agree with that boundary.
- The needed conditions, restated in r1 terms:
  - validity_status == `VALID`
  - control_status == `M_CONTROL_PASS` with m_valid true (Q1)
  - signal_status == `EXPLORATORY_L_SIGNAL`, computed on n_signal ≥ 15
  - `tail_driven` false
  - no leakage, mode or metric failures
  - complete artifacts, plus replay pass
  - a separate pre-registration, review and user approval for B0-B
- Even then, M is a prefix-753/15-doc control, so the control's scope must be quoted.

**Next steps**
1. Replace the prose list in §9 with the restated predicate.
2. Quote the M scope in any B0-B request.
3. B0-B pre-registration must come first, before any B0-B work.

### Q12. Final verdict — **NARROW**

- **r1 freeze:** not as written. Write r2 (text-only, Q8 items 1–6), then freeze by commit hash.
- **Implementation and unit tests:** conditionally approvable after the r2 freeze. This is pure-function and unit-test work, with no model runs needed for the decision logic.
- **D0:** approvable after implementation and tests are green: 0 updates, ≤4 configs, ≤15 min, no labels.
- **D1:** not approved here. It needs separate explicit approval, an unregistered seed, and ≤20 min.
- **3-seed:** not approved. It needs all checklist items and explicit approval.
- **Forbidden:**
  - B0-B, B1, B2, Stage C and Phase 6 auto-approval
  - test 163
  - P1
  - reopening T5Gemma2 (D-108 STOP)
  - threshold, seed, donor, step or LR changes after results
- **Max compute (existing prereg values, not new):**
  - registered: 12 units / 1,200 updates / 2h / 6 threads / no GPU / no retry
  - D0: ≤15 min and 0 updates
  - D1: ≤20 min, only if separately approved
- **Test 163:** sealed.

## 2. Wrong premises, or places to be careful

- "Factored" is not "independent". The signal axis reads the control axis, and each axis is still a precedence chain. "Total" should wait for the exhaustive test.
- "M validity" appears in §4.5 and §9 but not in the decision function. This is a premise error in §10, which marks "decision function total" as closed.
- "K_M_L=753 preserves a full-real-K control" would be an overclaim. It is a truncated-prefix control on the 15 longest-of-20 val docs, with a boundary doc at exactly 753. It stays valid as a data-only pre-result choice.
- The "54 tests pass" is historical. No PM test exists, and the runner lacks `pm-diagnostic`.
- P0 supports only native-path sensitivity (val median Δ 2.97, top-3 share .486, untrained CE > ln|V|). It does not support an EG2 or adapter expectation.

## 3. Compact summary

| Q | Verdict |
|---|---|
| 1 | conditional (not yet total: M_VALID missing, precedence residue) |
| 2 | conditional |
| 3 | conditional agree |
| 4 | conditional |
| 5 | agree |
| 6 | conditional |
| 7 | conditional |
| 8 | Must-fix list above |
| 9 | conditional (r2 then freeze) |
| 10 | conditional |
| 11 | agree (restate predicate) |
| 12 | **NARROW** |