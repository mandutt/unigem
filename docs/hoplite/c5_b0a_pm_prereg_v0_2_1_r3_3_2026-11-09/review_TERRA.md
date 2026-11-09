# Terra 6.1 high reviewer — independent external review of C5 P/M v0.2.1-r3.3

**Verdict: NARROW.** The proposed contract is substantially improved, but it is not yet internally total or sufficiently specified to freeze or implement as an experimental protocol. I recommend a narrowly scoped, text-only r3.4 addressing the ranked must-fixes below, followed by independent review. This is a recommendation, not authorization to execute Phase 6 or any subsequent stage.

## Review basis and limits

- Repository `mandutt/unigem`: `git fetch origin` and `git pull --ff-only origin main` both succeeded, with the checkout already up to date. Review HEAD and `origin/main`: `2ed41f096dc66180a09804b8555abbb3d62f7db5`.
- I personally read the full review request, r3.3, r3.2, the r3.2 synthesis, preflight JSON, P0 report, runner and metric tests, with targeted checks of inherited protocol clauses. The synthesis was background, not a substitute for this review; I did not read or reuse another reviewer's report.
- The preflight file's content SHA-256 independently matches `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`. This verifies file identity, not the correctness of its derivation.
- No training, model evaluation, or tests were run. Historical claims of 54 passing tests were not independently verified; existing tests are not evidence that the proposed P/M contracts are implemented. No trained P/PA/M results have been observed. Test 163 remained sealed; no P1 data or external APIs were used, and no subagent or additional model was used.
- References below use paths relative to the repository. `r3.3` means `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_3.md`; line numbers refer to the reviewed HEAD.

## Q1. Total factored contract

**Verdict: disagree.**

**Evidence.** The false-dominant `ANDn`/`ORn`/`NOT3`, ordered validity tiers and small-N precedence are individually understandable (r3.3:66–103, 138–207, 320–410). But the contract's stated expected outputs conflict with its executable branches. Section 2.3 makes both mixed true/false L inputs `NA`; the nine-pair table calls both `false` (r3.3:89–117). Further, the named cell “M pass L true + control PASS → EXPLORATORY_L_SIGNAL” is not sufficient: with both L endpoint signals false, fixture 17 correctly gives `MEAN_CONTRAST_ONLY` (r3.3:457–482, 527). Likewise `m_pass_l=false → M_CONTROL_FAIL` omits availability and calibration prerequisites in the ordered control dispatch (r3.3:249–265, 528). Therefore the requirement that every named cell have its exact output is not currently satisfiable as written. Section 9.4 also gives overlapping tail rules for a known-positive input paired with a null input (Q7).

**Next steps.**
1. Reconcile the table and all named-cell premises with the authoritative primitive functions, including valid/available/calibrated prerequisites; do not inject derived flags as independent primitives.
2. Specify total input domains and precedence, then add synthetic per-axis, boundary and named-cell tests, including F1–F11 and all reachable labels; preserve the validity/control/signal triple and raw reasons for small N.

## Q2. L consensus / fixtures

**Verdict: disagree.**

**Evidence.** For `(l_copy,l_full)=(true,false)` and `(false,true)`, the authoritative §2.3 “otherwise NA” gives `l_signal=NA`, whereas §2.4 displays `false` (r3.3:91–97, 107–117). The `copy_only`/`full_only` results do still route to the intended weak labels because those checks precede the `l_signal=NA` branch; the contradiction nevertheless breaks the mandated table test and permits different raw flags or consumers. Fixtures 16–18 derive the stated results if their other assumed validity and availability inputs are satisfied (r3.3:425–511); the previously impossible `m_pass_l=false` plus control PASS cell is removed, but the new insufficient named-cell premises in Q1 remain.

For `false+NA` or `NA+false`, the §2.3 result is NA and neither one-sided flag is true. With `n_signal>=15` and validity VALID, dispatch gives `NOT_ASSESSABLE`, not `MEAN_CONTRAST_ONLY` (r3.3:320–390). It is **not literally the only possible signal label**: if `n_signal<15`, the explicitly higher-priority result is `INCONCLUSIVE_SMALL_N`; an NA count also takes the first branch. This does not hide separately recorded validity.

**Next steps.**
1. Make the table's two mixed true/false consensus entries NA, consistent with the stated authoritative formula; retain one-sided flags and dispatch order.
2. Test all nine inputs under valid, invalid/NA validity, and n=14/15, explicitly documenting the small-N exception to the shorthand “false+NA only NOT_ASSESSABLE.”

## Q3. M preflight / cohort

**Verdict: conditional.**

**Evidence.** The preflight states a data-only length rule choosing the maximum eligible K: 753 gives 16 L train contributors and 15/20 common targets, while 754 yields only 14 eligible targets; all 20 native train/val lengths are reported as 512. Its exact common IDs and exclusions are recorded; full-K L is 11/20 and secondary (preflight:95–145, 191–200). This supports a *feasibility-selected prefix control* with zero margin, not a representative full-memory claim or a validated endpoint set. Fifteen of fifteen finite copy/full endpoints remain a prospective model-output requirement, not something established by the length-only preflight. `val20` signal and common-15 M are correctly different estimands (r3.3:276–288, 600–610, 645–661).

A new ambiguity affects feasibility: the arm table calls F/L “memory K 753” without limiting that to M (r3.3:580–587), although four of 20 train h lengths and five of 20 val h lengths are below 753 (preflight:51–93). The inherited shuffled signal contract uses donor-dependent `K=min` rather than requiring every signal memory to have 753 positions (`docs/plan_c5_b0a_pm_prereg_v0_2.md`:137–154; runner:423–429). A strict global interpretation conflicts with the registered 20-document workloads. The table does not establish which interpretation is intended.

**Next steps.**
1. Before freeze, distinguish train, shuffled signal and fixed-prefix M length/cropping rules for each arm, including short documents; reconcile them with inherited clauses without changing registered thresholds or cohort after outcomes.
2. Bind the exact common IDs and contributor selection to the verified preflight hash, reject replacement or incomplete M endpoints, and report prefix/selection scope and excluded documents.

## Q4. M builder / M_NORM / endpoint / replay

**Verdict: disagree that the specification is sufficient to freeze.**

**Evidence.** The proposal restores the positionwise `K_M×512` train-only mean, evaluation/no-grad, target-prefix primary real reference and whole-matrix Frobenius normalization (r3.3:612–643). The formula is target-dependent through the scalar; it is magnitude-matched, not strictly target-independent. Endpoint identity binds 15 IDs, three seeds, four arms and two variants, with finite CE and at least five copy tokens (r3.3:645–661). However, the builder table specifies L, P and PA but not F, even though endpoint_ok requires F and D1 times M for every arm. It also applies `A(h_i)` generically to P although P has no adapter (r3.3:580–587, 600–621). One can infer identity for P and an F adapter, but a freezeable algorithm should say so, including which seed checkpoint, encoder state, input prefix/attention mask and calculation order are used. Distinguish native source tokenization/encoding at the inherited training/signal length from constructing the native 512 M path; encoding a cropped token sequence need not equal slicing the output of a bidirectional encoder. `builder_ok` should be evaluated per required arm/seed/target and rolled up explicitly.

The replay key improves identity but does not complete the claimed wire contract (r3.3:851–893). Metadata integer endianness and allowed dtype spellings are not specified; mixed null/integer `donor_id` sorting has no defined total order; JSON float formatting, record fields/schema and key types/order across implementations are not fixed. The “golden vector” describes neither actual tensor/record values nor expected digest constants. Donor index 0..4 does not itself record which donor document it denotes. Most importantly, primary initial M is donor-free, while D1 replay is 15×5×2×copy/full (r3.3:803–816, 873–879); the exact mapping between the baseline primary records and separate-process replay records, including how toleranced CE comparison operates for every primary key, is unspecified. A hash of replay bytes alone is not a replacement for tolerance-based numeric comparison.

**Next steps.**
1. Specify F/L/P/PA builder and reference pipelines explicitly, including P identity, F scope, per-arm/seed checks, full source encoding versus prefix slicing, and endpoint/mask identity.
2. Freeze a precise byte and replay schema with explicit metadata endianness, canonical sort/null ordering, float serialization, actual fixed golden inputs and expected digests, and negative tests for duplicates, missing/extra keys and nonfinite values.
3. Define separate-process replay baseline-to-replay keys, donor mapping and numerical comparisons for every donor-free primary endpoint; reconcile the donor-level workload with D1 without silently changing the preregistered design.

## Q5. PA

**Verdict: conditional.**

**Evidence.** PA is named an acquisition control, not a direct retention comparator: native 512 memory and EG2 prefix 753 differ in geometry and scale; `PA_RETENTION` is nullable/descriptive, not a gate (r3.3:555–563). The ordered PA path/validity statuses distinguish `PA_STEP100_NOT_VALID` from P failure or assay NA (r3.3:158–183). The inherited errata explicitly define PA_VALID using P's same criteria (`docs/plan_c5_b0a_pm_prereg_v0_2_1_errata.md`:189–198), but r3.3 does not restate the linkage. More materially, the arm table trains F and L adapters while its hyperparameters say `adapter_lr: 1e-3 (PA only)` (r3.3:565–594). The current F/L runner uses `args.adapter_lr`, default 1e-3 (runner:665–696, 774), but code defaults are not sufficient to resolve a preregistration conflict.

**Next steps.**
1. State PA_VALID and its step-0/step-100 source and aggregation, and preserve its acquisition/geometry caveat.
2. Resolve the inherited F/L versus PA adapter optimizer groups and registered learning rates in the protocol before freeze, with explicit per-arm trainable inventory and initialization/mode tests; do not select a new rate based on results.

## Q6. Cap / D0 / D1

**Verdict: conditional.**

**Evidence.** The arithmetic is correct: 4 arms × 3 seeds × 100 = 1,200 registered updates; D0 adds zero, D1 adds four; 120 + 15 + 20 = 155 maximum prospective wall minutes, 1,204 updates (r3.3:771–850). D1 is separate approval, debug seed 20261111, no labels, no projection from D0; its new phase 5 explicitly includes initial fixed-prefix donor-free real/M scoring. T_proj multiplies the sum of the eight measured per-arm workloads by three and is gated at finite, nonnegative ≤96 minutes (r3.3:792–843). These are prospective caps, not permission.

The accounting is not yet fully operational: the donor-free primary versus 5-donor replay equality mapping is missing (Q4), and F M construction is not specified. For an honest projection, phase boundaries must cover real and control work and actual separate-process reload/serialization without omission or double counting. One update and debug generation need not predict trained-state generation lengths or later update cost, so ≤96 is an empirical gate with 24 minutes nominal headroom, not a proof that the registered 120-minute cap will be met. The existing runner is not a D0 runner: its train mode rejects zero steps and later indexes `losses[0]` (runner:742, 790–791).

**Next steps.**
1. Specify the per-phase operation/key ledger, measured wall-clock boundaries, process/reload costs, hardware/thread identity and primary replay mapping before D1; ensure all eight full workloads complete.
2. Keep D0 zero-update, ≤4 configs/15 min and no labels/results; require separate D1 approval, ≤4 updates/20 min, a complete timing artifact, and cap-abort/no retry.
3. Record generated token counts and projection limitations; a D1 pass does not waive the actual 120-minute hard stop or separately authorize 3-seed execution.

## Q7. Statistics

**Verdict: conditional.**

**Evidence.** r3.3 specifies document resampling, 1,000 percentile bootstrap draws, seed 20261109, seed averaging before document bootstrap, same retained F/L IDs and registered-seed 2/3 positivity (r3.3:700–749). The inherited formula makes `documents_positive` a count of positive per-document seed-averaged deltas, and `seeds_positive` a count of positive seed means (`docs/plan_c5_b0a_pm_prereg_v0_2_1_r3.md`:587–591). The existing helper uses seed 20261108 and labels positive document count `seeds_positive` (runner:384–397); it must not be reused for these P/M decisions. A missing registered seed makes the relevant L predicate NA rather than pooling available seeds (r3.3:727–730). Partial endpoint handling should also clarify how n is recorded when a whole seed is missing: n=0 under all-required-keys membership leads to a small-N signal label even while the primitive predicates are NA; the raw missing-seed reason and separate axes remain essential.

The tail rule as presented is not disjoint: e.g. `leave_top3_mean=-1`, `top3_share=null` meets both “true if leave≤0” and “NA if either null” (r3.3:750–760). An explicit NA-first policy would preserve the stated null/nonfinite rule; it must be written as ordered pseudocode rather than inferred. The document also calls signed `top3_share` descriptive while using it in the B0-B tail gate (r3.3:750–765, 970–983). Signed ratios outside [0,1] are permitted, so the gating calculation and interpretation should not be described as merely non-gating. Specify which per-document endpoint/delta is ranked, tie-breaking, and retained set; restore raw top-three sum and denominator as well as the values. CI percentile interpolation/RNG details and exact pairing/order should be frozen to reproduce boundary decisions.

**Next steps.**
1. Fix explicit missing/nonfinite-first tail precedence and identify the precise ranking input, ties, artifacts and gate role, without changing `.50` or zero boundaries.
2. Freeze deterministic document/seed aggregation, paired resampling/RNG and percentile details; implement the new stats module with synthetic equality-boundary, null/nonfinite, 2-of-3 and partial-endpoint tests.

## Q8. Remaining must-fix, ranked

**Verdict: disagree that all r3.2 blockers are closed; new r3.3 inconsistencies also block freeze.**

**Evidence.** The r3.2 synthesis identifies 12 blocker groups (synthesis:62–291); r3.3's closure table calls them all closed (r3.3:990–1008). The fixes are meaningful, but these claims are too strong:

1. **Decision truth-table / named-cell consistency (highest).** Correct the two mixed L consensus entries and specify all named-cell prerequisites, including signal value, availability, calibration and validity (Q1–Q2). Preserve small-N/false+NA precedence and test all nine input pairs.
2. **Arm, source-length, builder and optimizer contract.** Resolve global F/L K=753 versus short train/val documents and donor-cropped signal; specify per-arm F/L/P/PA M builders, especially F and P identity, native encoding/prefix order, and F/L adapter LR/optimizer groups (Q3–Q5). No post-result changes.
3. **Replay/hash and D1 completeness.** Fix actual golden input/digest and wire conventions, deterministic sorting/typing/donor identity, and donor-free primary-to-separate-process replay mapping; include all required work in the measured eight-phase ledger (Q4/Q6).
4. **Tail/statistics totality.** State null/nonfinite precedence, ranked endpoint, ties, ratio gate semantics and raw sum/denominator; freeze reproducible pairing and seed/missing-endpoint behavior (Q7).
5. **Before implementation, test/acceptance matrix.** Specify synthetic tests for the above plus all endpoint identities/negative cases, state hashes, 15/15, mode and parameter inventories, and D0/D1 stop conditions (Q9–Q10). Historical tests do not implement these requirements.

Already substantially addressed in text: the duplicate §9.2 L alias, the original impossible PASS/false cell, NOT3 and delta definitions, missing registered-seed rule, PA caveat, single endpoint definition, new-statistics module intent, and corrected preflight hash reference. These are not evidence of implemented or verified closure.

**Next steps.**
1. Make only the ranked pre-result contract corrections in a text-only r3.4, without changing thresholds, registered seeds, donor counts, steps or learning rates in response to results.
2. Obtain review of the corrected contract and its synthetic test matrix before any freeze or implementation.

## Q9. Freeze / implementation / D0

**Verdict: disagree with freezing r3.3 or approving implementation/D0 now.**

**Evidence.** The unresolved observable decision-table inconsistencies and missing builder/replay specifications above directly affect labels, executable work, and reproducibility. r3.3 itself says that on NARROW only must-fixes should be made in r3.4 and code follows freeze (r3.3:1012–1018). The existing file has old F/L and P0 paths, not the proposed PM protocol, and its model-dependent regression tests are skip-conditional (runner:753–798; `eval/tests/test_c5_b0_metric.py`:13–23). A prior 54-test historical result is not proof of new tests.

**Next steps.**
1. After corrected text is reviewed and explicitly frozen, implement and unit-test the decision function, nine L pairs, F1–F11, named-cell preconditions, all requested builder/endpoint/hash/replay/statistics/mode negative and boundary cases, and separate D0 path.
2. Only with appropriate explicit authorization, run D0 as zero-update mechanics, at most four configurations and 15 minutes, seed 20261111, `labels_computed:false` and `not_a_result:true`; do not use it to claim projected runtime.

## Q10. D1 / 3-seed boundary

**Verdict: conditional.**

**Evidence.** D1 and 3-seed are explicitly distinct gates (r3.3:792–843, 897–921). The checklist requires separate user approval, frozen protocol/code hashes, complete unit tests, D0 and D1 artifacts, registered/debug seed separation, preflight hash, T_proj≤96, manifest and post-run hash validation plan. This is a strong procedural boundary, but the mapping gaps in Q4/Q6 prevent declaring it complete, and a passing timing projection cannot itself authorize the 3-seed run. Debug and final hashes apply to different states and must not be compared as if equal (r3.3:883–886).

**Next steps.**
1. Add explicit checks that D1 phase 5 and separate-process primary replay cover the exact same keys, real/control endpoints, checkpoints and donor mapping; record workload counts and all phase wall times.
2. Before any separately approved 3-seed launch, verify the corrected frozen/code versions, executable cap-abort behavior, hardware and six-thread/no-GPU manifest, exact preflight/source/donor/mode/optimizer identities, complete test artifacts, and actual D0/D1 pass with T_proj≤96. Missing/failed items mean no launch.

## Q11. B0-B

**Verdict: agree with the separation, conditional on a total tail and complete artifacts.**

**Evidence.** r3.3:968–986 requires **all** of: `validity_status==VALID`; `control_status==M_CONTROL_PASS`; `signal_status==EXPLORATORY_L_SIGNAL`; `m_valid==true` as consistency check; `n_signal>=15`; `tail_driven==false`; leakage/mode/metric pass; complete artifacts; and a separate preregistration and approval. True or NA tail cannot pass. The M interpretation is `M_CONTROL_PREFIX753_COHORT15`, not a full-K or all-val control. P0, PA_RETENTION and the 11/20 full-K secondary cohort do not themselves justify progression.

**Next steps.**
1. Keep this conjunction and explicit separate preregistration/approval; do not let an exploratory L label or a good Phase 6 result auto-approve B0-B, B1, B2 or Stage C.
2. Resolve Q7's tail precedence and record all primitive values and validity/control/signal axes so the predicate is auditable.

## Q12. Final recommendation and authorization boundaries

**Verdict: conditional — final classification NARROW.**

**Evidence.** r3.3 fixes important r3.2 omissions but its L table and named cells conflict with their own formulas; arm/source/M and replay details remain incomplete, and tail conditions overlap. These are pre-result text-contract issues, not evidence that the scientific approach must be abandoned. P0 is descriptive native-path sensitivity only: val mean Δcopy +5.2375, CI [2.5013, 8.0753], median 2.9739 and top-three share .4862; untrained real CE is roughly 12.7/13.2 vs ln|V|≈12.43, and P0 used max source 256, not the M 512 path (P0 report:25–72; r3.3:925–930; request:175–187). It does not establish trained P/PA/M success or a bridge result.

**Next steps.**
1. Limit the next round to a reviewed text-only r3.4 addressing Q8, then consider freeze, implementation and D0 as distinct decisions with the necessary user authorization.
2. Retain separate D1, 3-seed and any downstream preregistration/approval gates. Do not modify thresholds, seeds, donor counts, steps or LR in response to outcomes; a substantive new design requires a new preregistration.

### Decision matrix and compute

| Item | Recommendation in this review |
|---|---|
| r3.3 freeze | **No**; resolve ranked must-fixes in r3.4 first. |
| Implementation + unit tests | **Not approved now**; after corrected freeze and authorization only. |
| D0 | **Not approved now**; after corrected freeze, successful tests and authorization only; 0 updates, ≤4 configs, ≤15 minutes, seed 20261111, no result labels. |
| D1 | **Not approved**; separate authorization, ≤4 updates and ≤20 minutes, all eight phases, debug-only, no labels; complete T_proj ≤96 minutes required for later gate. |
| 3-seed | **Not approved**; separate explicit user approval and complete checklist; registered maximum 12 units ×100 = 1,200 updates and 120 wall minutes. |
| Prospective maximum | If each separate gate is later authorized: D0+D1+registered run ≤1,204 updates and ≤155 wall minutes, CPU only, six threads, no retry/extension. These are ceilings, not a grant or a prediction. This consultation used **0 training updates and ran no evaluation**. |
| Forbidden / out of scope | Phase 6 execution is not approved by this review; no automatic B0-B, B1, B2 or Stage C; test 163 remains sealed; no P1 data. T5Gemma2 remains closed under D-108 STOP. |

**Incorrect premises to avoid:** the 15/20 length preflight is not a 15/15 model-endpoint pass; 54 historical tests are not current PM implementation tests; `false+NA` is not always the final signal label under small-N precedence; P0 is neither a trained control nor a confirmatory holdout; T_proj≤96 is not a guarantee or an approval; and r3.3's closure table is not itself evidence that every blocker has closed.