# Independent external review — Terra 6.1 medium reviewer

Date: 2026-11-09. Review basis: `origin/main` and workspace HEAD `fc0d9737e95e3b9952a0176da6e52fd4b40afa13`; `git fetch origin` and `git pull --ff-only origin main` both succeeded and the heads matched. This is an independent r3 review, not a repetition of the r2 review. I read the complete request and the seven requested artifacts, plus the relevant inherited v0.2/v0.2.1 errata needed to interpret r3. I did not use prior models' individual answers. Line references below refer to the reviewed HEAD.

**Overall: NARROW.** The r2 repairs are materially improved, but r3 is not yet a self-consistent, executable freeze contract. Authorize only text-only correction and subsequent independent review; do not freeze r3 or authorize implementation, unit tests, D0, D1, or the registered run on the basis of this review. No Phase 6, B0-B, B1, B2, or Stage C approval is conveyed. This is a recommendation, not an execution authorization.

## Q1 — Total factored contract

**Verdict: disagree** that it is fully executable as written; the central routing is much improved.

**Evidence.** r3 §3.2–3.5 (lines 137–191) tests known assay/P path failures before NA, and makes test-split and PA path NA fail closed. §4 (lines 204–255) removes M availability from validity, separates P/PA prerequisites and maps `m_valid=false` to `M_CONTROL_INVALID`. With otherwise valid paths/P/PA, `cohort_ok=false`, `n_signal=20`, and both L flags true, the triple is `(VALID, M_NOT_EVALUABLE, L_SIGNAL_M_CONTROL_NOT_EVALUABLE)`: the formerly dead cell is reachable. With all availability and P/PA prerequisites true and one calibration flag false, control INVALID is reachable. Control status is an independent axis, so a control PASS by itself is **not** assay validity or launch approval.

However, §6.3 lines 427–428 states unconditionally that `test_split_used=NA` and `pa_step100_path_ok=NA` produce `NOT_ASSESSABLE`. These are incompatible with the dispatch: e.g. `test_split_used=NA, p_step100_path_ok=false` yields `ASSAY_INVALID`; with all earlier paths good, `p_valid=false, pa_step100_path_ok=NA` yields `P_STEP100_NOT_VALID`. The safe invariant is that those NA values cannot yield VALID, subject to explicit earlier precedence. In addition, `m_evaluable` has only cohort, endpoint, seed and replay flags (§4.1), while inherited v0.2.1 errata §3.2/3.6 requires zero/nonfinite M norms or insufficient contributors to be `M_NOT_EVALUABLE`. If the four r3 flags are true but an M norm is zero, r3's formula divides by zero and routing through NA M-pass flags can produce control `NOT_ASSESSABLE`, not the inherited `M_NOT_EVALUABLE`. This is an unresolved mapping, not evidence of a fail-open exploratory label.

**Next steps:** (1) Make §6.3 precedence-aware and provide those two counterexample fixtures. (2) Define builder availability, zero/nonfinite norms, insufficient contributors and invalid inputs in the factored control contract and synthetic fixtures, retaining fail-closed routing. (3) Specify accepted input domains and test each axis, all label reachability, and cross-axis invariants, including impossible-combination handling.

## Q2 — L preservation and signal labels

**Verdict: conditional.**

**Evidence.** r3 §5.3 dispatches `n_signal=NA` first, then small N, then all non-VALID validity states, before copy/full-only and L/control labels. This closes the original asymmetric validity guard: COPY_ONLY_WEAK, FULL_ONLY_WEAK, MEAN_CONTRAST_ONLY and NO_AFFIRMATIVE require VALID. With `n=14`, L true and invalid validity, the small-N L-qualified label wins while the validity axis still records the failure. With `n=20`, both flags true, VALID, and `M_NOT_EVALUABLE`, the L-qualified M-unavailable label is reachable. With copy T and full NA, consensus is NA and, for n≥15 and VALID, the output is NOT_ASSESSABLE, while raw flags remain recorded (§5.5). `copy_only` and `full_only` use false-dominant AND3, so one can be false rather than NA for other partial-NA combinations; do not claim both are always NA.

For `validity_status=NOT_ASSESSABLE`, the branch labels observed L/copy/full evidence `*_VALIDITY_INVALID`, although unknown is not proven invalid. This is conservative but the wording can mislead unless the validity axis and reason are inseparable from the label. An `n_signal=NA` label cannot itself preserve the L qualifier, so the required raw flags/reason must always accompany it. Reachability here is reasoned from text, not an executed exhaustive test.

**Next steps:** (1) Require the full triple, raw flags and reason together in every report, distinguishing known invalid from unknown validity. (2) Add synthetic truth-table cases for all nine copy/full combinations, small N, NA n, all validity/control statuses and every claimed reachable label. (3) Define consistent common document/seed eligibility before deriving the L flags (Q7).

## Q3 — M preflight, cohort and endpoints

**Verdict: conditional.**

**Evidence.** I independently counted the length values in `reports/provenance/C5_b0a/m_cohort_preflight.json`: at K=753, 16/20 train and 15/20 val are eligible; at 754, 16 train and 14 val. The calculated common-ID set and five exclusions exactly match the artifact; native recorded lengths are 512 for all 20. The file's actual SHA-256 is `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`, matching r3 §11. This establishes the arithmetic of the preregistered length-only maximum, not external generalization or validation of actual model outputs. The 15 longest are length-conditioned and zero-margin. Full-K 11/20 is secondary only (preflight lines 130–145). r3 §§5.1, 8.2 use val20 for signal and the fixed common 15 for M, with all 15 L and P/PA copy/full endpoints required; loss of one M endpoint makes M unavailable, not necessarily signal small-N, since up to 19 val20 signal documents may remain.

The 15/15 rule is appropriately fail-closed but operationally needs the exact fixed IDs and endpoint meaning across **all three seeds, each arm, each primary variant, and both real and control CEs**, including finite results and mask threshold. The existing runner's `copy_ce` returns None for fewer than five aligned copy tokens (lines 302–315); simply counting 15 masks without checking the CEs or seed/variant identity is insufficient. Cohort replacement or lowering to 14 after observing results would be inappropriate.

**Next steps:** (1) Bind endpoint checks to the hash-identified 15 IDs, arms, variants and seeds; define finite/missing/duplicate checks and exact flags. (2) Preserve signal/M separate counts, common IDs and exclusions; predefine handling without replacement. (3) Report only `M_CONTROL_PREFIX753_COHORT15` scope and the 753-versus-512 difference; do not treat full-K 11/20 as a gate.

## Q4 — M builder, aggregation and replay

**Verdict: conditional.**

**Evidence.** r3 §§8.3–8.6 specifies train-only contributors, adapter/model eval and no-grad, per-seed reconstruction, target-wise seed average before document bootstrap, false-dominant AND3, checkpoint hashes, and separate-process replay with `atol=1e-5`, `rtol=1e-4`. These are appropriate principles and avoid treating 45 seed-document observations as independent. False + NA gives false in the M calibration conjunction *when the M-availability and P/PA prerequisite branches have passed*; a failed prerequisite takes precedence. The previously conflicting r2 missingness-first rule is overridden by r3.

They do not prove leakage-free execution. `M_NORM` uses each target's real-prefix Frobenius norm: inherited v0.2.1 errata §3.5 explicitly calls this a target-dependent, magnitude-matched control, not a strictly target-independent mean; it need not use target labels, but that must be enforced. Fix the builder/norm failure routing in Q1. Specify exact checkpoint, tensor/state hashes, model/adapter/mode, fixed contributor IDs, which per-target/per-variant/per-seed CEs are compared, finite checks and both tolerance terms; a single aggregate match would not guarantee per-cell replay. Numeric tolerances support reproducibility, not a proof of no leakage.

**Next steps:** (1) Predefine builder provenance, target-norm-only permitted dependence and no validation target labels in training/mean construction. (2) Define finite/zero failures and comparison granularity and test them synthetically. (3) Verify separate-process replay of all required primary cells and identities after execution, not only aggregate CE.

## Q5 — PA acquisition control

**Verdict: conditional.**

**Evidence.** r3 §7 says PA uses native memory plus a random adapter and decoder LoRA, with its own step0 random re-baseline, `PA_STEP100_NOT_VALID`, and `PA_RETENTION` potentially null/non-gating. Inherited errata §2.2–2.4 specifies zero-LoRA step0 and the same step100 sensitivity criterion as P. The PA setup is an acquisition/path control, not evidence of learned EG2 selectivity; native mT5 final hidden versus EG2 layer19 scale/geometry limits comparisons. P0 is untrained native-path sensitivity, not a trained P/PA/L result: val mean Δcopy +5.2375, median 2.9739, top-three share .4862 and real CE 13.2352. P0's 256 source limit does not validate the registered 512 M path (r3 §12). None of this establishes PA training success.

**Next steps:** (1) Specify PA random adapter identity, step0 separate execution, initialization/RNG reset and distinct checkpoints. (2) Require synthetic zero-LoRA and train/eval-mode tests and report scale caveat and null retention. (3) Keep the preregistered PA validity criteria and any invalid/NA result separate from conclusions about content use.

## Q6 — Cap, D0 and D1

**Verdict: conditional** on arithmetic and approval separation; **disagree** that the timing projection is adequate as specified.

**Evidence.** r3 §10: registered 4 arms × 3 seeds × 100 updates = 12 trained units/1,200 updates, ≤120 minutes, 6 threads, no GPU or retries; D0 separately ≤4 configurations, 0 updates, ≤15 minutes; D1 separately 4 arm-seeds ×1 = 4 updates, ≤20 minutes. D1 requires explicit approval and cannot be replaced by D0. If all future stages were separately approved and used to their maxima, combined accounting is **1,204 updates and 155 minutes wall** (15 + 20 + 120), not 1,200 updates or 2 hours total. These are caps, not permissions.

The multipliers 100 and 3 in §10.4 are arithmetically correct only if each `t_*` is the *entire corresponding per-arm, per-seed registered workload*. Yet §10.3 times step0/final on “one doc subset” and inserts those times once, without defining subset, per-document/variant/donor scaling, or coverage of all required 20 documents. It times an M builder “15 docs” although the builder uses **16 train contributors for L and 20 for P/PA**, while 15 are target docs; these are different workloads (§8.3). F has no specified M builder yet the formula sums one for every arm. Required setup, loading, checkpoint/artifact I/O, primary/secondary evaluation, generation telemetry and separate-process replay workload are not clearly accounted for. A projection below 96 min could therefore be a severe underestimate; a 20% buffer is not a substitute for a workload inventory.

**Next steps:** (1) Define exact timed phases, train-contributor versus target counts, per-arm applicable phases and all required document/donor/variant counts. (2) Measure representative per-unit timings and fixed overhead, specify extrapolation with no omitted work and finite/nonnegative validation. (3) Keep the 96-minute gate, separate approvals and hard abort/no retry; do not authorize D1 now.

## Q7 — Statistics

**Verdict: conditional.**

**Evidence.** r3 §9 specifies 1,000 percentile document bootstrap resamples, seed 20261109, per-document seed averaging, positive document versus seed counts, paired L−F and marginal signal n=15. The inherited errata §4.3 defines the actual copy/full L gates, including paired L−F and 2/3 seed means. Runner `bootstrap_paired` lines 384–398 instead defaults to seed 20261108 and calls a count of positive *documents* `seeds_positive`; existing tests do not establish r3 compliance. A future implementation must not silently reuse those defaults or field names. Historical 54 tests are not tests run in this review, and the requested test file contains no Phase 6 truth table.

`n_signal` is “val20 docs with valid copy and full endpoints” (r3 §5.1), but does not state precisely how common IDs intersect F/L, real/wrong donor pairs, and all three seeds, or how missing donor/seed observations affect per-document averages and 2/3 seed means. Thus different implementations can obtain different paired contrasts. r3 §9 sets top-three share to null for zero/nonfinite denominator but `tail_driven = leave_top3_mean <= 0 or top3_share > .50` has no null-aware comparison rule. Signed sums can be negative or nearly zero, making a share misleading; “top 3” tie-breaking and which contrast/cohort is used are also unspecified. r3 §14's `tail_driven == false (or explicitly reported)` must not silently interpret unknown as false. Small samples and reusing val20 are exploratory, not confirmatory.

**Next steps:** (1) Specify common paired F/L document/seed/donor/endpoint inclusion, missingness and n/seed mean calculations before results. (2) Define deterministic ordering, denominator and null propagation for top-three diagnostics, with explicit B0-B handling of unknown, without changing thresholds. (3) Freeze RNG/percentile convention and test synthetic paired data, 14/15/20 boundaries, ties, zero/nonfinite totals and mixed missingness.

## Q8 — Ranked remaining Must-fix / r2 closure

**Verdict: disagree** with r3 §15's blanket “closed”; several r2 holes are genuinely addressed in text, but closure is not complete.

**Evidence — ranked unresolved items:**
1. **Timing workload and launch safety:** r2's undefined D1 phases now have names, a shared seed and formula, but §10.3–10.4 does not scale subset measurements or reconcile 15 targets with 16/20 builder contributors; define full workload projection and enforce the existing caps (Q6).
2. **Contract consistency and M builder failure:** correct unconditional NA assertions versus precedence, and map zero/nonfinite/insufficient M builder prerequisites into the factored availability axis (Q1/Q4). These are real text-level contradictions even though the two originally reported NA paths no longer reach VALID.
3. **Prelaunch versus post-run artifacts:** §11 item 14 requires “replay hash complete,” while §8.6 records final checkpoint/replay state hashes, unavailable before the registered run. Define a D0/D1 *debug* replay hash or replay-contract/code hash as the prelaunch artifact and final trained hashes as post-run gates; do not silently require future results at launch (Q10).
4. **Endpoint/paired statistics and nulls:** identify all required 15 endpoint cells and the common val20 F/L/seed/donor intersection; define top-three null handling and B0-B unknown handling (Q3/Q7/Q11).

Already addressed in the normative routing: M_NOT_EVALUABLE control-only and the formerly dead L label; `m_pass_l` derivation and false-dominant conjunction; signal validity guard; signal/M cohort distinction; fixed preflight hash; noncircular M_VALID *computation contract*; and P0 256/512 limitation. These still need the specified tests and operational details; textual closure is not empirical proof.

**Next steps:** (1) Resolve the four ranked items in a text-only r4 without changing registered thresholds. (2) Re-review the corrected contract and verify the formerly closed items with synthetic tests only after approval.

## Q9 — Freeze, implementation, unit tests and D0

**Verdict: disagree** with approving them on r3 as-is.

**Evidence.** r3 §16 explicitly requires NARROW → text-only r4, and code only after freeze. The contradictory truth-table requirements and undefined timing/availability cases above prevent one unambiguous implementation; runner `main` lines 753–789 offers smoke, metric-smoke, train and p0-sanity, not `pm-diagnostic`. Current test file covers existing alignment, mode, donor and descriptive P0 paths, not r3's PM contract; its model-dependent class may be skipped if the local model is absent. Prior 54 passes are historical only.

**Next steps:** (1) Produce a minimal text-only r4 resolving ranked blockers without post-result threshold, seed, donor, step or LR changes; obtain review and freeze its commit before implementation. (2) Thereafter require synthetic exhaustive routing, fail-closed, M norm/endpoint/seed/replay, paired-statistics, F/L mode, P zero-LoRA and PA random-step0 tests, plus manifest/hash coverage. (3) Only after separate approval consider D0, with 0 updates, ≤4 configurations, ≤15 minutes and no outcome labels; this review does not authorize it.

## Q10 — D1 and 3-seed boundary/checklist

**Verdict: conditional.**

**Evidence.** r3 §11 requires distinct freeze/code commits, green tests, D0, D1, verified preflight hash, debug seed disjoint from registered seeds, unchanged frozen parameters, projection ≤96 min, manifest and explicit user approval. Item 9 correctly requires the M_VALID *computation contract* rather than its unknowable post-training truth. D1 and 3-seed are separate, and D1 alone cannot authorize 3-seed. But item 14's “replay hash complete” has no specified phase: final checkpoint and replay state hashes in §8.6 cannot exist for an unrun 3-seed experiment. It may have intended a debug replay hash, but the document does not say so. Nor can the current D1 projection establish the actual required work (Q6).

**Next steps:** (1) Split prelaunch debug replay evidence and replay procedure from post-run final checkpoint/replay hashes and output validation. (2) Add workload-complete D1 timing, environment/thread identity, finite projection and exact endpoint/cohort contract to the checklist. (3) Require explicit, separate D1 and 3-seed approvals; on failed/missing gate or cap abort, stop without retry or extension.

## Q11 — B0-B boundary

**Verdict: conditional.**

**Evidence.** r3 §14 explicitly denies automatic progression. Its stated predicate is `validity_status=VALID` AND `control_status=M_CONTROL_PASS` AND `signal_status=EXPLORATORY_L_SIGNAL` AND `tail_driven=false (or explicitly reported)` AND leakage/mode/metric pass AND complete artifacts AND separate preregistration/approval. M_CONTROL_PASS already entails true M calibration and L M pass under §4, and EXPLORATORY also requires VALID/control PASS. The written “or explicitly reported” is a reporting alternative, **not** proof of robustness or automatic approval; its interpretation, especially for `tail_driven=NA`, is under-specified. P0, PA retention and full-K 11/20 are explicitly not B0-B evidence (§14).

**Next steps:** (1) Require explicit tail status and missingness; if not demonstrably false, report the limitation for a separate decision, never equate NA with false. (2) Require the exact 753/15 scope, complete reproducibility and leak/mode/metric evidence, plus a new preregistration and explicit approval. (3) Do not authorize B0-B/B1/B2/Stage C based on this review or any Phase 6 label.

## Q12 — Final verdict and authorization scope

**Verdict: conditional** on a corrected, independently reviewed preregistration; final classification **NARROW**.

**Evidence.** The fixed preflight arithmetic, r3 dispatch and P0 sensitivity support a narrowly scoped design exercise, not a freeze-ready or approved experiment. The known contradictions, timing and artifact dependencies in Q1/Q6/Q10 are sufficient to withhold freeze and mechanics execution. There is no trained P/PA/M evidence in the review basis.

**Next steps:** (1) Text-only r4 addressing the ranked Must-fix, followed by separate review and freeze decision. (2) If eventually approved, implementation/tests and D0 are bounded separately from D1 and the 3-seed launch. (3) Preserve all sealed/closed boundaries and report outcomes without retroactive protocol tuning.

## Final scope, compute and incorrect premises

- **Final: NARROW.** Permitted recommendation now: text-only protocol repair and independent review. This review itself authorizes no experimental compute.
- **r3 freeze:** no. **Implementation + unit tests:** no. **D0:** no. **D1:** no, separately authorized if ever considered. **3-seed:** no, separate launch gate and explicit approval.
- **Prospective caps, not approval:** D0 0 updates, ≤4 configs, ≤15 min; D1 4 × 1 = 4 updates, ≤20 min; registered Phase 6 12 × 100 = 1,200 updates, ≤120 min, 6 CPU threads, no GPU, no retry or extension. Combined separately approved maximum = 1,204 updates and 155 minutes wall; never count debug as registered outcome evidence. Actual elapsed execution and abort behavior must be accounted for.
- **Prohibited/unapproved:** training or evaluation in this review; Phase 6/B0-B/B1/B2/Stage C; P1; opening test 163; extra models/subagents. Test 163 remains sealed. T5Gemma2 remains closed under D-108 STOP. No changes to threshold, seed, donor, steps or LR after results; materially new choices require a new preregistration.
- **Incorrect premises to avoid:** r3's “all Must-fix closed” and unconditional NA assertions; P0 as proof of trained selectivity or the 512-token M path; length-only preflight as proof of actual endpoint availability; a D1 subset timing as a complete 3-seed cost; a numerical replay as proof of no leakage; 15/15 M failure as necessarily val20 small-N; a prior 54-test historical result as verification of unimplemented PM code; any label as automatic B0-B approval.

Verification in this review was static reading, SHA-256 hashing, and independent length/count/set arithmetic from the allowed preflight artifact. No training, evaluation, test execution, P1, sealed test access, external API, or subagent/model call was used.