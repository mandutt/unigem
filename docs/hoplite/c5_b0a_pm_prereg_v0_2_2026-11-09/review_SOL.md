# Sol 6.1 high reviewer — independent C5 B0-A P/M preregistration v0.2 review

## Review identity, basis, and restrictions

- Reviewer: **Sol 6.1 high** (`gpt-6.1-sol`), independent external reviewer for this new v0.2 round.
- Date: 2026-11-09 UTC.
- Repository: `mandutt/unigem`; review basis: current `origin/main`.
- Synchronization: `git fetch origin` succeeded; `git pull --ff-only origin main` succeeded with `Already up to date.` Both resulting `HEAD` and `origin/main` were **`918cfa5bc9129016b91d506bb412a1938f119bcf`** (`docs: add C5 P/M prereg v0.2 review request`). The existing workspace branch was `hoplite/lampsakos-e6ced772`; I did not switch branches. Its commit matched remote main.
- I personally read the complete v0.2 review request, both preregistrations, the requested synthesis, P0 report, repair report, runner, and metric tests. I additionally inspected the relevant Adapter/LoRA definitions and existing P0 JSON. The synthesis was historical context, not a substitute for this review; I did not open the individual prior reviewers' reports or consult another model.
- **No training, evaluation, model loading, generation, test execution, external API use, subagents, or additional LLM calls.** The only computation on an experimental artifact was read-only arithmetic over already-recorded P0 per-document deltas. I did not open the sealed test set or use P1 data.
- Following the expressly authorized initial Git synchronization, the only repository file written by this consultation is this report. No implementation, commit, PR, or execution approval is delivered here.
- The historical test count is not fresh verification. The repair report §6 records 52 tests at that stage; the later synthesis records 54 historically. Neither establishes P/PA/M coverage.

## Executive judgment

**Final verdict: NARROW.** v0.2 materially improves v0.1, especially by introducing PA, separating M's full-memory reference from shuffled-memory crops, and requiring aligned full CE alongside the broad copy-mask endpoint. The small diagnostic is scientifically worth implementing **after the outstanding protocol contracts below are frozen**. It is not ready as written for an unconditional debug run, and it is not a validation of learned semantic content use.

The principal remaining problems are:

1. P remains a **post-training sensitivity/retention screen**, not evidence that LoRA learned useful selectivity. The `.05` addition does not solve that distinction. PA is specified but its failure is not consistently wired into the decision table.
2. M is a useful **fixed-checkpoint input intervention**, not a trained content-free competitor. P/PA validation helps but does not establish distributional validity for EG2-derived L memory. Eligibility, missingness, validation conjunction, and norm dependence still need an executable contract.
3. A failed P confidence-bound condition is not proof that training **erased** selectivity. The final label table also omits an explicitly defined cell and overlaps another.
4. Pooling, full-versus-copy missingness, the meaning of `L > F`, and debug-inclusive compute accounting remain underspecified.

I recommend conditional progression to implementation and, only following explicit owner authorization and successful acceptance checks, one non-gating mechanics debug. **This consultation does not approve Phase 6 execution, the three-seed run, B0-B, B1, B2, or Stage C.** Test 163 remains sealed; P1 remains unused; T5Gemma2 remains closed under D-108 STOP.

## Compact Q1–Q12 verdicts

| Question | Verdict | Bottom line |
|---|---|---|
| Q1 P gate | conditional | Stronger sensitivity gate; still not a learned-selectivity or useful-operating-point control. |
| Q2 PA | conditional | Necessary regime-matched improvement; PA validity and its own step-zero baseline must be operational. |
| Q3 M reference | agree | Full-real-K is the right M reference; never subtract donor-cropped real CE from full-K mean CE. |
| Q4 M definition | conditional | Leakage-free primary construction is possible; cohort, norm, OOD, and validation limitations remain. |
| Q5 Labels | disagree | Statistical non-pass is not erasure; PA, missingness, and no-affirmative-evidence cells are incomplete. |
| Q6 Full/copy | conditional | Conjunctive co-primary endpoints are defensible; metric hierarchy and copy-specific wording need correction. |
| Q7 Tail/power | agree | Exploratory screening only; heavy-tail sensitivity is not proof of an outliers-only effect. |
| Q8 Compute | defer | Completion within cap is unverified; accounting units and debug inclusion must be fixed first. |
| Q9 Tests | agree | All named invariant categories are necessary, with correctly specified permutation/perturbation expectations. |
| Q10 Debug | conditional | Mechanics only after contract/test closure and owner approval; no tuning or automatic three-seed launch. |
| Q11 B0-B | agree | Even a positive diagnostic only supports a separately reviewed proposal. |
| Q12 Overall | conditional | **NARROW**, not approval as written and not authorization to execute Phase 6. |

## Q1. Does the strengthened P gate fix the near-vacuous gate?

**Verdict: conditional.** It fixes part of the operational weakness, but not the scientific limitation if P is presented as evidence of *learning* selectivity.

**Evidence.** v0.1 §6.2 required positive copy delta and a positive CI lower bound. v0.2 §6.1 additionally requires mean copy delta at least `.05` and positive full delta/full CI lower bound. These are more restrictive numerical conditions, but none compares step 100 with step 0 or requires improved target prediction. P0 already has validation mean copy delta **5.2375**, CI **[2.5013, 8.0753]**, and full delta **5.2936**. A copy delta of `.05` is only about **0.95%** of that historical mean. This is a scale illustration, not a prediction that the trained P CI will pass. The existing P0 JSON does not contain a full-delta CI; I do not infer that condition from its full mean.

The new wording in v0.2 §1—whether native selectivity is *maintained*—is more appropriate than a claim that adaptation creates it. A pass can coexist with a large reduction in selectivity and poor absolute CE. Reported P0 real **copy-masked** CE of 12.7022/13.2352 exceeds the uniform-token reference `ln(250112) ≈ 12.43` on that mask; it does not by itself establish overall full-target CE or explain the mechanism of the delta. Large wrong-minus-real differences could reflect wrong-memory damage as well as useful real-memory conditioning.

**Next steps.**

1. Freeze P_VALID as a **post-training native-path sensitivity screen**, retaining the registered numerical cutoffs; explicitly prohibit interpreting its pass as LoRA-created selectivity, EG2 validity, or good generation quality.
2. Record matched step-zero/step-100 real and wrong copy/full CE, deltas, and descriptive retention, with a defined undefined-ratio policy when the step-zero denominator is zero or unsuitable. No hidden retention gate.
3. Separate a statistical P non-pass from path/mode/finite failures, and remove the implication that any non-pass proves erasure. A stronger learning claim would require a separately preregistered question, not retrospective threshold adjustment.

## Q2. Is PA sufficient to separate the adapter-regime confound?

**Verdict: conditional.** PA is the right bounded addition, but is not a complete causal isolation of “adapter as soft prompt.”

**Evidence.** v0.2 §§2.3–2.4 compare native memory without an adapter against native memory with the same adapter architecture/init scheme used in F/L. The actual Adapter is a non-identity tokenwise two-layer MLP plus LayerNorm (`runner/c5_mt5_layer_probe.py:52–63`). Thus PA exposes whether the adapter-plus-LoRA recipe can preserve recoverable native-source distinctions. It does not make native and EG2 representations distributionally identical, isolate every optimization difference, or prove why a PA failure occurred.

Two gaps matter. First, v0.2 §6.1 defines PA_VALID, but §6.4 has no branch for a statistically invalid PA when its path is technically sound. §12 requires P/PA valid for a B0-B proposal, so the controls must remain explicit. Second, “step0 reference: P0 native / zero-LoRA path” is a valid P reference, but **not PA's matched step-zero reference**: PA already contains a randomly initialized nonlinear adapter. A PA-versus-P difference after training alone cannot establish a training-induced adapter collapse.

**Next steps.**

1. Make positive-control eligibility explicitly require **P_VALID AND PA_VALID**, with each status and its per-seed results retained. A technically valid but statistically non-passing PA must not disappear into `EXPLORATORY_L_SIGNAL`.
2. Record PA's actual initialized-adapter, zero-output-LoRA step-zero baseline, separately from P0. Keep the same source/crop policy, documents, and deterministic donor assignment within each comparison.
3. Freeze initialization/RNG, optimizer, example order, and mode contracts. Seed explicitly immediately before LoRA initialization for both P and PA; do not rely on incidental RNG consumption by `make_adapter(seed)`. Describe any failure as an adapter-regime limitation, not proof of soft-prompt causation.

## Q3. Is full-real-K the right reference for M?

**Verdict: agree.** This is a substantive repair.

**Evidence.** v0.2 §§2.5–3 use full real memory length `K_real` for both real and mean views. In contrast, `evaluate_arm` (`runner/c5_mt5_lora_b0.py:423–446`) computes a potentially different `k = min(real_length, donor_length)` for each donor and averages those cropped real losses. Those quantities answer different questions.

The native P0 path adds an important detail: it crops **token IDs before native encoding** (`:186–193`), whereas F/L crop already-contextualized cached hidden states. Encoding a prefix is not equivalent to slicing a fully contextualized encoder output. Truncation can also change EOS inclusion. “Length matched” does not establish that these details are interchangeable.

**Next steps.**

1. Compute and name a distinct `real_fullK_ce_{full,copy}` at the same checkpoint, labels, modes, and attention-mask policy as each mean view. Define M deltas exclusively from that matched full-K pair.
2. Keep donor-cropped real CE under a separate name and retain donor IDs/K. Present shuffled and M contrasts side by side; do not subtract, equate, or merge their absolute CE baselines. A crop-only comparison, if reported, stays secondary.
3. Freeze whether native prefixes are encoded before or after cropping, and the prefix/EOS/padding conventions. Retain the chosen P0-compatible behavior rather than silently changing it after observing trained results.

## Q4. Are the mean definition and P/PA validation adequate?

**Verdict: conditional.** Adequate for a narrowly interpreted input-replacement diagnostic after remaining invariants are fixed; not adequate for an unconditional semantic-content test.

**Evidence.** v0.2 §3 fixes averaging **adapter outputs**, not applying the nonlinear adapter to a mean input. Restricting contributors to train documents with length at least K, with at least ten contributors, can avoid validation-summary leakage. Length conditioning is legitimate if disclosed: the mean is **source-length-conditioned**, not independent of every target-source attribute.

The residual issues are specific:

- `eligible >= 10` counts **training contributors for one target**, not analyzed validation targets. It can leave very few or no target documents. No minimum analyzable target cohort or missing-CI behavior is specified. Arm-specific native/EG2 lengths can also yield different P/PA/L cohorts.
- `M_VALID = P/PA ...` (§6.3) does not specify AND versus OR, pooling, or treatment of one missing control. Validate P and PA separately and require both; do not pick whichever passes.
- P/PA mean controls operate on native-memory distributions. Passing them cannot prove that mean replacement is in-distribution for EG2-derived L memory. Averaging contextual vectors can change dispersion, direction, and effective attention behavior. Global rescaling does not remove those changes.
- **M_NORM is not strictly target-independent:** it uses the real target-source memory's norm. This is not summary-label leakage, but is intentional input dependence. It is a secondary magnitude-matched intervention, not a fully content-free primary mean.
- `M_POS_MEAN` averages token-index positions that need not be semantically aligned across documents. It is a reproducible baseline, not a meaningful “average source sequence.”
- P/PA M_VALID is defined only on **full CE**; L's M_CONTROL_PASS also requires copy CE. Full-only validation must not be described as independent validation of every copy-endpoint failure.

**Next steps.**

1. Freeze deterministic contributor IDs, arm/checkpoint identity, full K, EOS/padding exclusions, token-weighted M_GLOBAL construction, and M_NORM's Frobenius-norm/zero-norm policy. Assert train/val separation and the declared duplicate policy; no target summaries, validation contributors, or shuffled donors in primary mean construction. Save source/contributor hashes and counts.
2. Predefine the target cohort, common-target comparison policy across P/PA/L, minimum usable target coverage, and `NOT_ASSESSABLE` behavior before CE is observed. Report all 20 selected targets, every exclusion, and arm-wise/common-cohort counts. An eligible-subset result must not become a whole-panel claim. Zero observations or a missing CI is not a failed content-use test.
3. Require separately reported P and PA mean-validation results under the frozen full-CE rule and an explicit conjunction. Report their copy contrasts too. Keep M_GLOBAL/M_NORM secondary: they may expose distribution sensitivity, but may not rescue a failed primary or replace its definition after results.

## Q5. Are the decision labels consistent and free of overclaim?

**Verdict: disagree.** Several improvements are real, but the table is not yet complete or semantically safe.

**Evidence.** v0.2 §6.3 correctly adds `L_SIGNAL_M_CONTROL_FAIL` and the qualified `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`. Nevertheless:

1. **Non-pass is not erasure.** §6.1/§6.4 assign `REGIME_ERASES_SELECTIVITY` whenever P0 is positive and step-100 P is not P_VALID. A positive estimate with a CI touching zero, a copy mean just below `.05`, or a failed full condition can produce that outcome without demonstrating that selectivity was erased. Separate pre/post significance classifications are not a paired test of change.
2. **PA statistical failure has no cell.** A path-correct PA can be invalid while §6.4 still selects an exploratory L label.
3. **A defined label is absent from the final table.** §6.3 assigns `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE` to no L signal plus failed M, but §6.4 sends the neither-endpoint-positive case to `INCONCLUSIVE_SMALL_N`.
4. **Partial-signal overlap.** “No L_SIGNAL” includes copy-only and full-only cases. §6.3 and §6.4 can therefore assign different labels to the same result when M fails.
5. Ineligible M, incomplete arms/cap exhaustion, missing CIs, and failed positive-control sensitivity are not equivalent to valid negative measurements. They need explicit states and precedence.

**Next steps.**

1. Replace the automatic erasure conclusion with a factual label such as `P_SELECTIVITY_NOT_ESTABLISHED`, preserving P0 and step-100 estimates. Retain a separate technical `ASSAY_INVALID` status. Describe actual paired change without introducing a hidden new gate.
2. Freeze a total, ordered decision function: technical failure; incomplete/not-assessable; P/PA sensitivity eligibility; M validation; then joint/partial/no L signal with L-M status. One consistent final-stage ordering is joint signal → exploratory or L-signal/M-fail; xor → endpoint-specific weak label plus M status; neither + failed M → no affirmative evidence; neither + passed M → inconclusive. Keep every constituent status in the artifact even when an earlier condition determines the headline.
3. Enumerate and test all truth-table cells, including PA-only failure and unknown values. No statistical label authorizes B0-B or generalizes to absence of content use.

## Q6. Are full CE and copy CE handled appropriately?

**Verdict: conditional.** Requiring both endpoints is defensible for a conservative exploratory screen, but the hierarchy and claims need to be made consistent.

**Evidence.** v0.2 §5.1 calls full and as-run copy CE **co-primary**, and §6.2 requires both for L_SIGNAL. However, the change table at line 29 says “as-run copy secondary,” and Q6 in the review request repeats that wording. Both hierarchies cannot govern the run. The fullCE/copyCE conjunction also means a full-only result intentionally remains weak; this is a design choice, not evidence that full CE failed to work.

The broad as-run mask covers about **82–84%** of target tokens. P0 validation deltas are copy **5.2375** and full **5.2936**; these are not independent replications or a copy-specific effect. `piece_len >= 2` is a useful exploratory restriction, but substring overlap alone does not establish copying precision; the repair report §5 explicitly leaves manual precision adjudication outstanding. Agreement between full and copy CE is not proof of copying either.

There is also a code-level issue: `evaluate_arm` skips a whole document when no valid copy CE exists (`:437–438`), thereby dropping its otherwise available full CE. P0 does similarly (`:201–202`). A genuinely full-target endpoint should not silently depend on passing the copy-token-count filter.

**Next steps.**

1. Make the hierarchy unambiguous before implementation: retain the explicit §5.1/§6.2 **co-primary AND** rule, with strict-mask analyses exploratory. This review does not recommend loosening the rule after results.
2. Compute full CE on all predeclared valid target documents, excluding padding/ignored labels but not applying the copy mask. Keep copy eligibility and any common-cohort sensitivity report separate; do not silently discard full results because `copy_ce` requires at least five selected tokens.
3. Restrict conclusions to source-conditioned target prediction under memory interventions. Neither full/copy agreement nor a strict-mask signal alone licenses a claim of semantic copying or generation quality. Preserve full-only/copy-only results rather than tuning the mask to make them agree.

## Q7. What can the diagnostic detect, given heavy tails and low power?

**Verdict: agree** with exploratory-only interpretation and robustness reporting; disagree with any stronger conclusion implied merely by “three seeds” or by the heavy-tail warning.

**Evidence.** P0 has only 20 validation documents, validation median **2.9739**, mean **5.2375**, and signed top-three contribution **0.4862**. I independently checked arithmetic from the existing P0 JSON: removing the three largest recorded deltas leaves a validation mean of **3.16586** over 17 documents, and train mean **2.55687** over 17. Thus the reported P0 mean is influenced by large observations but is **not an outliers-only positive mean**. I ran no new model evaluation or bootstrap to obtain these arithmetic summaries.

The same 20 validation documents are reused (§4); three training seeds do not create 60 independent documents. Five donors per target are repeated interventions, not five independent target samples. The design can detect technical breakage, large within-panel sensitivity, severe regime differences, and a reproducible exploratory L-vs-F contrast. It cannot establish population-level generalization, absence/equivalence from a non-pass, a semantic mechanism, task-quality improvement, or that scaling will solve a weak result. Document bootstrap uncertainty is conditional on the chosen panel, donors, and seeds; it does not capture all training or data-selection uncertainty.

**Next steps.**

1. Specify the estimand: average donors within document, retain each seed's document vector and mean, then average seeds within each document for the pooled document bootstrap. Resample document IDs jointly across arms/endpoints/seeds, not 60 seed-document cells as independent observations.
2. Define `L > F` as the paired mean difference in the **registered delta endpoint** on the frozen matched cohort, not an arbitrary comparison of absolute CE. Report its paired contrast and uncertainty without silently adding a new CI gate. Apply the stated two-of-three sign rule per endpoint and show the joint seed sign matrix; the same two seeds need not pass both endpoints under the formula as written.
3. Report the registered median, quantiles, signed top-three share with a defined denominator policy, leave-top-three-out means, and all per-document results. Keep these descriptive, except the already stated prospective B0-B robustness requirement. No donor/seed/step/threshold changes, tail exclusions from the primary, equivalence claims, or “scale will fix it” inference.

## Q8. Are the compute cap and implementation plan realistic?

**Verdict: defer** on feasibility; the implementation gaps are directly observable.

**Evidence.** The runner CLI (`:753–789`) has smoke, metric-smoke, train, and P0 modes, but no `pm-diagnostic` or PA/M path. `set_training_mode` only accepts frozen/lora and assumes an adapter (`:329–381`). `train_arm` handles F/L, returns JSON, and does not persist the final trained state needed for independently replayable M probes (`:665–750`). The training defaults include AdamW, weight decay `.01`, adapter LR `1e-3`, LoRA LR `1e-4`, cyclic example order, and clipping `1.0`; v0.2 should explicitly freeze whether P/PA inherit these, rather than leave them to implementation choice.

Twelve units and 1,200 updates are ceilings, not evidence of completion in two hours. A straightforward shuffled evaluation already entails **12 × 20 × 5 × 2 = 2,400 decoder forwards** before reuse of identical views, in addition to backpropagation, native encoding, M variants, and generation. The P0 log listed in the report is not present at the advertised path in this checkout; the inspected repair metadata provides no end-to-end PM timing proof. No local timing benchmark was performed in this consultation.

The cap table calls its row “wall time” but gives “CPU-hours.” Two elapsed hours with six busy threads can approach twelve core-CPU-hours; two aggregate CPU-hours can be much less elapsed time. Also, a separate four-arm one-seed debug plus a freshly rerun three-seed study is **16 units / 1,600 updates**, not 12 / 1,200.

**Next steps.**

1. Close the ranked Must-fix contracts below before implementation/debug. Explicitly inherit or specify all optimizer, data-order, initialization, source-limit, and final-checkpoint choices without changing registered numerical decision thresholds.
2. Freeze wall versus aggregate process-tree CPU accounting, debug/smoke inclusion, generation workload, and stop behavior. Until clarified, the conservative interpretation is to enforce **both** at most 7,200 elapsed seconds and at most 7,200 aggregate CPU seconds, six threads, no GPU, no automatic extension, and at most 12 trained units / 1,200 updates overall. This is a proposed clarification requiring owner acceptance, not evidence that the workload fits.
3. In a separately authorized debug, measure end-to-end phase costs and projected remaining cost, including encoding/evaluation/M/generation. Use deterministic caching only where semantics are identical, keyed by checkpoint/source/crop policy. If the cap cannot accommodate the registered workload, stop incomplete and seek a new prospective decision, not an unregistered reduction or extra budget.

## Q9. Which P/PA/M tests are mandatory?

**Verdict: agree** that all listed categories are mandatory, with their expected invariants stated precisely.

**Evidence.** `eval/tests/test_c5_b0_metric.py` tests alignment, mask placement, F/L modes, basic native donor assignment, telemetry, and descriptive P0 labels. It does not implement the new P/PA/M contracts. Every test in that file is inside a class skipped when the local model directory is absent (`:13–14`); pure builder/decision tests must not all disappear behind that model dependency. Existing donor helpers exclude self IDs but do not check duplicate **source contents** (`runner/...b0.py:144–150,318–325`). The bootstrap output currently calls a count of positive input values `seeds_positive` (`:384–397`), although those inputs are document deltas.

Minimum acceptance specification:

| Area | Required evidence before any actual-model debug |
|---|---|
| Path/inventory | P has no adapter; PA has the specified adapter; F has no LoRA; L/P/PA have exactly 64 decoder self/cross q/k/v/o LoRA modules; native encoder and all base parameters remain frozen. |
| Seed/isolation | Same seed/config reproduces initialized LoRA and adapter tensors independent of run order; separate arms/seeds start from a clean base; zero-output LoRA matches the corresponding no-LoRA path in eval mode. |
| Modes/gradients | Base and native encoder stay eval; only intended adapter/LoRA parameters are trainable; LoRA dropout is train only during training; evaluation is deterministic. Reapply/assert training modes after step-zero evaluations, since `token_losses` calls `model.eval()`. Check expected trainable gradients and no base gradients without assuming zero-initialized LoRA A must already have a nonzero first-step gradient. |
| CE/endpoints | Built-in full loss matches aligned per-token CE within `1e-5`; ignored labels and EOS policy are correct; copy mask is unshifted; full CE survives a document with insufficient copy tokens; train and evaluation objectives use the same alignment. |
| Donors/crops | Exactly five unique non-self, nonduplicate-source donors or a predeclared failure state; deterministic tie-breaking and source-only selection; per-view K/IDs; native crop-before-encoding policy versus hidden-state cropping is explicit. |
| M construction/leakage | Mean is of post-adapter outputs at the frozen checkpoint; train-only contributors; correct length filtering; exact boundary tests at 9 versus 10 contributors; no padding in means; full-K matched real view; source-ID provenance; zero eligible targets yields not-assessable rather than an empty-bootstrap pass/fail. |
| Perturbations | With K held fixed, changing validation summaries, donor identities, or validation source content cannot change primary POS/GLOBAL mean tensors or contributors. Altering eligible training memory should change the constructed mean in a controlled toy example. M_NORM is an explicit exception for dependence on the real-memory norm. |
| Permutations | Reordering the **list of train documents** leaves means unchanged within floating tolerance. Permuting completed memory rows together with their attention-mask entries should preserve decoder CE where the cross-attention path has no additional row-position signal. M_GLOBAL is invariant to input-position permutation; **M_POS_MEAN is not generally invariant to independent row permutations before averaging**. Do not encode a scientifically false blanket invariance test. |
| Pooling/labels | Synthetic fixtures distinguish document positives from seed positives, verify paired document bootstrap and `L > F`, enforce the two-of-three endpoint rules, and cover every validity/signal/M/missingness label cell. |
| Checkpoints/budget | Saved final state reloads to the same eval outputs; M cannot update parameters; code/config/input hashes identify each artifact; cap and incomplete-run handling cannot silently launch another arm or retry. |

**Next steps.**

1. Freeze these acceptance cases before writing the PM implementation; put pure toy builder/statistics/label tests outside model-dependent skips.
2. Require fresh, non-skipped results for all new applicable checks plus the existing regression suite under separately authorized implementation/testing. Keep actual-model checks local-only and bounded; no sealed-data or external-model downloads.
3. Make acceptance a prerequisite for debug, not something inferred from a plausible loss curve. Test the norm-dependent and position-permutation exceptions explicitly rather than weakening failing tests to make a false invariant pass.

## Q10. How far may a non-gating one-seed debug go?

**Verdict: conditional.** Only after preregistration clarifications, implementation tests, and explicit owner approval; none is executed or authorized by this consultation.

**Evidence.** v0.2 §10 explicitly separates a one-seed non-gating debug from the three-seed gate. The missing details are its seed/arm coverage, budget relationship, reusable-checkpoint policy, and what counts as success. “One seed” cannot establish a two-of-three seed rule, and viewing a debug loss must not become permission to choose thresholds, donors, masks, or a favorable checkpoint.

**Next steps.**

1. Prospectively choose the already registered first seed **20261108**, exercise F/L/P/PA and L/P/PA M paths, and inspect only mechanics: shapes, finite values, mode/gradient assertions, aligned CE, contributor/donor provenance, serialization, and timing. At most four arm-seed units and 100 updates per unit; any shorter mechanical prefix is not a substitute final checkpoint or a gate result. Do not search seeds or steps.
2. Charge all actual-model debug work to the frozen overall cap. One viable accounting policy is to preserve the first-seed final checkpoints as immutable, non-gating artifacts that may be included in a later explicitly authorized three-seed panel **only if that reuse was declared beforehand and code/config are unchanged**. No rerun of that seed to get a better result. If a correctness repair invalidates it, stop and obtain a new prospective accounting/preregistration decision rather than silently refill the 12-unit allocation.
3. The separate three-seed authorization package must include the frozen protocol/code hash, complete passing test results, exact manifest of IDs/donors/K, step-zero/final state hashes, all per-document and M eligibility/validation records, mode/alignment records, clock/budget accounting, failures, and a fit-within-cap projection. Mechanical success—not a favorable P/L delta—is the criterion for requesting that gate. No automatic launch or parameter adjustment based on debug effects.

## Q11. Does L_SIGNAL plus M pass leave B0-B unapproved?

**Verdict: agree.** This boundary is correct and essential.

**Evidence.** v0.2 §§1,10,12 explicitly separate this 20/20/100-update screen from B0-B 300/95 and make P/PA validity, M validity/pass, joint L signal, tail robustness, integrity, and complete artifacts necessary but insufficient for considering a B0-B proposal. Even the best label remains **EXPLORATORY**. The panel was already used for P0 and is not an untouched confirmatory holdout.

**Next steps.**

1. Require every stated §12 prerequisite under the corrected executable decision/cohort contract. A positive M result cannot rescue a failed positive control, missing data, invalid assay, or absent joint L signal.
2. If those prerequisites are met, submit a separate B0-B proposal with its own prospectively frozen hypothesis, sample/split usage, endpoints, thresholds, seed/checkpoint/donor policies, uncertainty treatment, compute cap, and explicit owner approval. Do not treat this review as that proposal or approval.
3. Preserve the exclusions unchanged: no B1/B2/Stage C progression; test 163 stays sealed; no P1 use; no reopening T5Gemma2 under D-108 STOP. An inconclusive screen does not justify scaling by assertion.

## Q12. Final verdict, permissions, cap, and next decision gate

**Verdict: conditional — NARROW.**

**Evidence.** v0.2 is a meaningful conceptual repair over v0.1, not a duplicate review target. It closes the biggest design omissions but leaves material executable ambiguities before its requested implementation/debug step (§13). No trained P/PA/M evidence exists in the reviewed basis, and none was generated here. The scientific question remains worth a bounded exploratory diagnostic; neither project-level STOP nor unconditional CONTINUE is justified.

**Next steps.**

1. Resolve and freeze the ranked Must-fix list below before implementation choices or debug observations can determine the contract.
2. Obtain explicit owner approval for implementation and subsequent bounded mechanics debug, then satisfy the acceptance tests. This report itself changes no approval state.
3. Return with the complete debug/integrity/budget package for a separate three-seed decision. The resulting diagnostic, if later authorized, still cannot approve B0-B automatically.

### Ranked Must-fix and closure conditions

| Rank | Must-fix | Closure evidence / timing |
|---|---|---|
| **MF-1** | **Validity and total decision table** | Before implementation: state P AND PA eligibility; P AND PA mean-validation logic; distinguish non-pass from erasure; resolve omitted/overlapping no-affirmative/partial-signal cells; define unknown/incomplete states and precedence. Before debug: exhaustive synthetic truth-table tests pass. |
| **MF-2** | **Estimand, pooling, and target cohorts** | Before implementation: define donor→document→seed aggregation, paired document resampling, `L > F`, per-endpoint seed signs, full-CE independence from copy eligibility, M target cohort/minimum coverage and missing-CI policy. Before debug: toy cases verify each. |
| **MF-3** | **Mean-builder and reference contract** | Before implementation: freeze full-K real reference, post-adapter train-only means, contributor IDs, EOS/pad/crop semantics, norm definition/zero handling, and secondary-only M_GLOBAL/M_NORM status. Before debug: leakage, eligibility-boundary, correct permutation/perturbation, and full-K tests pass. |
| **MF-4** | **P/PA training-path and metric acceptance** | Before implementation: freeze optimizer/order/RNG and matched PA step-zero behavior; preserve existing F/L repairs and numeric gates. Before debug: clean model isolation, exact 64-module inventories, frozen base/encoder, intended modes/gradients, zero-LoRA equivalence, independent source length flag, and same-position loss equality are freshly verified. |
| **MF-5** | **Metric hierarchy and interpretation** | Before implementation: reconcile “copy secondary” with the explicit co-primary AND formula; restrict P/M/copy claims to their measured estimands; no secondary-result rescue. Before debug: output schema retains all endpoint/validity statuses rather than just a favorable headline. |
| **MF-6** | **Budget, debug provenance, and replay artifacts** | Before any actual-model work: resolve wall versus CPU-hours, include debug in unit/update/time caps, freeze reuse/no-retry policy and generation workload. Before three-seed consideration: final checkpoints/hashes, code/config/input manifests, complete per-view/per-doc/eligibility records, clocks, and budget projection exist. |

MF-1–MF-3 and MF-5 are protocol choices to settle **before implementation**; MF-4/MF-6 also require a frozen contract then. Their implementation/test evidence is required **before debug**. None may be repaired by choosing a favorable interpretation after trained outcomes are seen. A later substantive design change belongs in a new preregistration.

### Approval recommendation and hard boundaries

| Item | Recommendation / status |
|---|---|
| v0.2 as written | **Not unconditionally approved. NARROW with the above Must-fix.** |
| Implementation | Recommend conditional approval after the protocol contracts are explicitly resolved/frozen and the owner authorizes work; no implementation done here. |
| One-seed debug | Conditional future mechanics-only step after applicable tests and explicit owner authorization; **not execution-approved by this review**. |
| Three-seed run | **Not approved**; separate gate after the complete debug package. |
| Phase 6 execution | **Not approved by this consultation**; recommendations do not substitute for owner authorization. |
| B0-B / B1 / B2 / Stage C | **Not approved**; no automatic progression under any diagnostic label. |
| Maximum proposed diagnostic compute | Overall **12 trained arm-seed units, at most 1,200 updates, six CPU threads, no GPU, no automatic retry/extension**; M evaluation-only. All new debug/encoding/evaluation/generation work must be charged. Resolve the two-hour unit before work; conservatively enforce both 7,200 elapsed seconds and 7,200 aggregate CPU seconds until a prospectively approved unambiguous contract exists. Historical P0/repair work remains excluded as specified. |
| Debug share of that cap | At most four units / 400 updates at seed 20261108, **inside**, not additional to, the overall cap; upfront immutable first-seed reuse or a separate prospective reauthorization is necessary to avoid a 16-unit/1,600-update debug-plus-rerun design. |
| Next decision gate | Protocol closure and owner implementation/debug authorization first; then tests + complete mechanics/provenance/timing package for separate three-seed consideration. |
| Test 163 | **Sealed; not opened here and must remain sealed.** |
| P1 | **Unused; not proposed.** |
| T5Gemma2 | **D-108 STOP remains closed.** |

### Incorrect premises to avoid

- A P pass establishes adaptation-created selectivity, or any P statistical non-pass establishes erasure.
- Adding PA to the arm list automatically makes PA_VALID a decision prerequisite, or completely isolates the adapter's mechanism.
- P/PA mean-control success establishes that EG2-derived mean memory is in-distribution, or M_NORM is strictly target-independent.
- Ten eligible training contributors imply ten eligible validation observations.
- Full-K real CE and donor-cropped real CE are interchangeable.
- Full/copy agreement, or a stricter substring mask, proves semantic copying; two correlated endpoints are independent replications.
- A 49% top-three share proves the positive P0 mean disappears without those documents; the recorded leave-top-three-out mean is still positive.
- Three seeds or five donors multiply the independent document sample size.
- Historical “54 tests pass” covers newly proposed P/PA/M behavior, or the current runner already implements PM.
- “Two CPU-hours” is an unambiguous wall-time cap, or a separate debug can be added outside 12 units/1,200 updates.
- Any positive diagnostic label approves Phase 6 execution or downstream stages, or a weak result justifies scaling without a new decision.

**Bottom line: NARROW. Preserve the bounded design and existing numerical gates; finish the protocol and acceptance contracts before authorized implementation/debug. No trained-result claim, downstream approval, or sealed-data access follows from this review.**
