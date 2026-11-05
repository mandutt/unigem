# Hoplite review — Wave 2B V2 reader-only gate

- Review request: docs/STT/reports/EXTERNAL_REVIEW_W2B_V2_GATE_2026-11-05.md (769 lines; read in full)
- Synchronized checkout: HEAD ac1fd82ee32212ce99517e3986a5b43f69a0addc; origin/main matched HEAD after fetch and fast-forward pull.
- The request identifies 9d1aba6 as its review-base commit. This checkout is shallow/grafted at ac1fd82, so that older commit is unavailable for a history diff. The review below evaluates the current self-contained request and its current referenced reports/provenance.
- Scope: consultation only. No training, inference, or bootstrap was run; no code or experiment files were changed.

## 0. Conclusion

**B — Caveat-qualified PASS.** The documented V2 reader-only B3 recipe met the stated numerical gate and FLEURS-dev guardrail after dev selection and a one-time post-freeze test. Retain that narrow recipe-level PASS, but not as an isolated Kspon-short/data/domain effect, not as speaker-independent generalization, and not as a confirmatory result for future evaluations on the same test.

## 1. Q1–Q8

### Q1. Status of the gate

① **Judgment:** Accept the result as a caveat-qualified, recipe-level PASS for the documented V2 setup; do not downgrade it to exploratory solely because the recipes differ in compute. It is not a clean test of a data-only hypothesis. Also distinguish the documented V2 amendment from the original D-067 V1-vocabulary protocol.

② **Evidence:** The candidate B3 was selected/frozen on dev before its sole test evaluation. Dev improvement was +10.187 percentage points (paired utterance-bootstrap 95% CI [+9.107, +11.328]); test improvement was +9.737 pp (95% CI [+9.228, +10.258]); both exceed the 1.0-pp minimum with lower CI bounds above zero. FLEURS dev changed by −0.216 pp, within the no-regression limit. D-069 records the V1-to-V2 change after severe V1 training OOV; the V2 B0′ and B3 comparison uses the same V2 vocabulary, and the review says evaluation/test text was not used to construct it. Thus the threshold result remains meaningful for the amended V2 recipe, but it is not literally the originally specified V1 recipe.

③ **Required action:** Preserve the result and the amendment history together. Label it “V2 reader-only recipe-level gate PASS,” specify seed 42, 12 epochs, the B0′ and B3 data/sampler recipes, and disclose that the vocabulary changed from D-067 before final training/test. Do not rewrite it as a causal data result.

④ **Blocks LoRA/next step?** No for recording this narrow pass or doing an exploratory next reader experiment. Yes for any broader causal or confirmatory claim that treats the gate as isolating the contribution of Kspon short data.

### Q2. Causal attribution and controls

① **Judgment:** The current B0′–B3 contrast cannot identify a “short 4h data effect,” “Kspon domain effect,” or length effect. It does estimate the outcome difference between these two complete recipes, which is the proper scope of the recipe-level gate.

② **Evidence:** B0′ had 3,576 optimizer steps and 72.0096 audio-exposure hours; B3 had 11,196 steps and 120.2652 hours: 3.13× the steps and 1.67× the exposure. B0′ has Wave 1 only (Zeroth/Kconf, no Kspon); B3 adds Kspon short data and changes the duration mix. The B3 epoch-4 diagnostic (3,732 steps) is not a clean control: it has only 40.0884 exposure hours, uses epoch 4 of the 12-epoch cosine schedule, and its checkpoint was not retained. Likewise, the proposed B0′-38 run would roughly match B3-12 in steps but not exposure (about 228h versus 120.3h); B3-4 is near B0′-12 in steps but not exposure or learning-rate schedule. D-070’s 20-epoch figures preserve essentially the same 3.13×/1.67× imbalance (5,960 vs 18,660 steps; 120.016 vs 200.442 exposure hours).

③ **Required action:** Before making a causal data claim, pre-register a fixed-budget comparison with the same initialization, V2 artifacts, optimizer/schedule, number of updates, and cumulative audio seconds. At minimum compare B3 with a Wave-1-only replay/resampling control that spends the same update/audio budget; match or report duration-bin and padded-frame/compute differences. This estimates whether the Kspon-short mixture beats spending that budget on replayed Wave 1, not a universal “short data” effect. To separate domain from duration, add a duration-matched Kspon-long arm and/or a non-Kspon-short arm if suitable training data are available. If simultaneous step and audio matching is infeasible, choose the primary budget estimand in advance and state the unmatched quantity rather than calling the run compute-matched.

④ **Blocks LoRA/next step?** It blocks a causal “data effect” claim and blocks a clean incremental LoRA efficacy claim if LoRA is compared against an unmatched B0′. It does not invalidate the current recipe pass or block exploratory implementation/smoke tests.

### Q3. V2 vocabulary and two-pass selection

① **Judgment:** The two-pass loop creates training-set selection dependence, but the available facts do not show evaluation/test leakage. The low test OOV rate does not quantify or rule out selection bias in the selected training subset.

② **Evidence:** Draft V2 (2,342 characters) was used to select 5,066 short clips; final V2 was then formed using those selected references and the short set was selected again, yielding 5,079 clips. The request says eval/test transcripts were not used for vocabulary construction. Test OOV is 1.875% of utterances and 0.1299% of characters; both arms share the same vocabulary. Those numbers limit OOV’s direct asymmetry between arms, but say little about the dependence of training selection on the final character set.

③ **Required action:** Freeze the existing V2 vocabulary, manifests, and checkpoints for this result and for any directly comparable exploratory run; do not retroactively rebuild the vocabulary and silently treat it as the same recipe. For a new confirmatory recipe, define the vocabulary from a pre-specified eligible training-transcript pool (or a fixed external character inventory) before short-clip selection, define OOV handling, and report coverage/exclusion on the full candidate pool. If changing the vocabulary, retrain all comparison arms under the new contract and treat it as a new recipe.

④ **Blocks LoRA/next step?** No for the current result or a same-V2 exploratory LoRA prototype. Yes for claims that results are independent of the vocabulary/selection procedure, and for a new-vocabulary comparison unless all arms are rerun consistently.

### Q4. B3-nat and sampler conclusions

① **Judgment:** The evidence supports only “no statistically detectable B3 vs B3-nat difference on dev under this setup,” not “sampler has no effect.” A B3-nat test run is not necessary unless the sampler choice itself will change.

② **Evidence:** B3-nat was evaluated on dev only. B3−B3-nat is +0.490 pp with 95% CI [−0.229, +1.205], which includes zero and still allows nontrivial differences. B3-nat’s best dev epoch was 11 (0.2633) versus B3’s epoch 12 (0.2682); B3-nat’s epoch-12 CER was 0.2634. That near-equality of its best and final dev scores does not substitute for a test comparison.

③ **Required action:** Keep B3 balanced as the frozen candidate for the reported gate. Do not make a sampler-superiority or sampler-equivalence claim. Only evaluate B3-nat on the old test if that result would materially affect a decision; if run, pre-specify the comparison and label it an additional exploratory use of an already-used test. Prefer a new untouched holdout for any confirmatory sampler claim.

④ **Blocks LoRA/next step?** No, unless sampler behavior is itself a research objective or the LoRA recipe depends on selecting between samplers. It blocks claims that the samplers are equivalent or that one is better.

### Q5. Test reuse and confirmatory status

① **Judgment:** The test was a valid one-time in-domain procedural holdout for the frozen B3-vs-B0′ comparison, but it is no longer sealed for future model selection. Treat seed-43, 20-epoch, LoRA, or B3-nat results on these same 2,400 utterances as exploratory/post-hoc in this project context.

② **Evidence:** B3 was frozen on dev before test, and the report says no thresholds changed after test. The test contains 2,400 Kspon eval_clean utterances, but 74.33% are ≤4 seconds, only 185 are 8–16 seconds, and speaker IDs are unavailable. Train/test speaker independence therefore cannot be established.

③ **Required action:** In future reports call it an “in-domain procedural holdout, evaluated once; speaker independence unknown,” not an untouched future test. Reserve a new, adequately sized, untouched holdout for confirmatory claims, preferably with speaker IDs and a speaker-disjoint split. The spare 90 is too small for the primary gate. FLEURS is a different domain and cannot replace a Kspon holdout; moreover, the project history reports prior Wave 2A-lite FLEURS-test use, so do not describe it as fresh without checking its use and eligibility.

④ **Blocks LoRA/next step?** It blocks confirmatory claims from reusing this test, not exploratory dev-based experiments or descriptive historical comparisons. It blocks speaker-independent claims until a suitable speaker-disjoint evaluation exists.

### Q6. Next-experiment priority

① **Judgment:** Prioritize a pre-registered, step-and-audio-exposure-matched reader control. A seed-43 replication is useful for robustness but does not address the main confound; a 20-epoch three-arm run at the same epoch count also does not match compute; LoRA is premature as an efficacy claim.

② **Evidence:** The current test supports a large recipe contrast, but the update/exposure/domain/length factors move together. D-070’s projected 20-epoch budgets retain the same step and exposure ratios. Seed 43 would estimate seed sensitivity, not isolate the contribution of the added data.

③ **Required action:** Recommended order:
1. Pre-register and run the matched-budget reader comparison described in Q2. Keep the current V2 vocab, initialization, normalization, data processing, and evaluation protocol fixed; use dev for selection. The existing test can be shown only as exploratory if reused.
2. If the scientific question requires distinguishing “Kspon domain” from “short duration,” add an appropriate matched-duration/domain control. Do not infer either component from the two-arm mixture comparison.
3. Run seed 43 as a secondary robustness check, preferably on the matched recipes; it may be parallelized if budget permits, but it does not replace the control.
4. Run the D-070 20-epoch study only if the remaining learning curve motivates a convergence question. Use all arms and a common schedule, and describe it as convergence/exploratory unless budgets are also matched.
5. Defer LoRA efficacy evaluation until a matched no-LoRA comparator, GPU validation, and an untouched confirmatory evaluation plan are in place. LoRA code/GPU smoke tests can be engineering work in parallel.

④ **Blocks LoRA/next step?** The matched control is the next step for causal attribution, not a prerequisite to the current PASS. It blocks a causal data claim and a fair incremental LoRA claim; it does not block exploratory engineering or a clearly labeled recipe follow-up.

### Q7. LoRA readiness

① **Judgment:** Do not start a conclusion-producing LoRA efficacy run on the strength of this reader-only contrast. It is reasonable to implement or smoke-test LoRA as exploratory engineering, with no expected-gain claim inferred from the +9.74 pp recipe contrast.

② **Evidence:** B1/B2 LoRA was not implemented or evaluated. The documented run was CPU-only; GPU packaging/parity, throughput, memory, OOM behavior, and interruption recovery were not measured. The 10-pp result compares different reader-only data recipes and is not an estimate of LoRA’s marginal value.

③ **Required action:** Before an efficacy run, freeze the exact V2 data/vocabulary/splits and test-reuse policy; establish a same-data, same-step/audio-budget no-LoRA reader control; validate the LoRA path and CPU/GPU prediction parity (or a documented tolerance), and measure runtime/memory/recovery. Pre-register the target layers, rank/alpha, optimizer, budget, primary endpoint, and stop/go rule. A defensible proposed rule is at least a 1.0-pp CER improvement over the matched no-LoRA control with paired 95% CI lower bound above zero on a fresh untouched holdout, plus no more than 1.0-pp regression on the pre-specified FLEURS-dev guardrail and successful stability/resource checks. That threshold would be a new prospective rule, not a result already established here.

④ **Blocks LoRA/next step?** These items block a confirmatory LoRA efficacy claim, not code implementation or an explicitly exploratory smoke run. The old test may be descriptive only for LoRA.

### Q8. Reporting language and claim scope

① **Judgment:** Replace “Kspon short-domain 4 hours produced a data effect” with “the V2 reader-only B3 recipe improved over B0′.” Avoid “sealed” without saying it has since been used once. Do not claim speaker independence, broad generalization, state of the art, or a LoRA effect.

② **Evidence:** The comparison jointly changes training set size, Kspon domain, short-length distribution, steps, and audio exposure. The evaluation is same-corpus Kspon eval_clean with no speaker IDs; B3-nat has no test score; LoRA was not run.

③ **Required action:** Use wording such as:

> In the V2 reader-only experiment, B3 (Wave 1 6 h plus the selected Kspon short training set, approximately 4 h, with balanced sampling) achieved CER 0.2682 on the 500-utterance dev set versus 0.3701 for B0′, and 0.262270 versus 0.359643 on a 2,400-utterance Kspon eval_clean procedural holdout (B0′−B3 = +9.737 percentage points; paired utterance-bootstrap 95% CI [+9.228, +10.258]). The documented V2 recipe-level gate was met. B3 also used 3.13× as many optimizer steps and 1.67× the audio exposure, and added Kspon data with a shorter duration distribution; this comparison does not isolate a short-data or domain effect. The holdout was evaluated once, is not known to be speaker-independent, and should be exploratory for subsequent runs on the same utterances. FLEURS dev did not regress; no LoRA result is implied.

④ **Blocks LoRA/next step?** It blocks the current causal/overclaiming sentence, not the narrow recipe-level result or next exploratory experiment.

## 2. Must-fix table

| ID | Issue | Required action | Priority | LoRA / next-step blocking status |
|---|---|---|---|---|
| MF-1 | Compute, audio exposure, domain, and duration are confounded | Run a pre-registered matched-budget reader control; add domain/length control if attributing those components | P0 for causal attribution | Blocks data-effect claims and fair LoRA-increment claims; not exploratory engineering |
| MF-2 | The 2,400-utterance test has already been used once | Retire it from confirmatory use; obtain a fresh untouched holdout for new confirmatory claims | P0 for future confirmation | Blocks confirmatory claims on the same test; not exploratory follow-up |
| MF-3 | V2 vocab depends on draft-selected short references | Freeze V2 for current comparisons; construct any new vocab before clip selection and rerun all arms if changed | P1 | Does not block same-V2 work; blocks independent-vocab claims/new-vocab comparisons |
| MF-4 | Speaker independence and train/test speaker overlap are unknown | Obtain speaker metadata or a genuinely speaker-disjoint holdout before making speaker/generalization claims | P1 for generalization | Blocks speaker-independent claims; not the recipe gate |
| MF-5 | LoRA path has no GPU parity/resource evidence or matched no-LoRA efficacy comparator | Validate hardware path and compare LoRA against an identical-budget reader baseline under a prospective stop/go rule | P1 before LoRA efficacy claims | Blocks confirmatory LoRA efficacy, not implementation/smoke testing |
| MF-6 | B3-nat has dev-only evidence | Keep the conclusion limited to dev; run a test comparison only if sampler choice matters, and label it exploratory | P2 / decision-dependent | Blocks sampler-effect claims only |
| MF-7 | Seed-42-only result and proposed 20-epoch extension | Use seed 43 for robustness after the control is specified; do not treat epoch count as compute matching | P2 / follow-up | Does not block the existing gate; required only for stronger robustness/convergence claims |

## 3. Next-experiment priority

1. **Matched-budget reader-only control (first).** Compare B3 against a Wave-1-only replay/resampling arm at the same pre-registered optimizer-step and cumulative audio-second budget, with identical initialization, V2 vocab, schedule, and preprocessing. Match/report duration mix and padded-frame compute. If both update and exposure budgets cannot be matched, choose and name the primary estimand beforehand. Use the current test only descriptively; a fresh holdout is needed for confirmatory publication.
2. **Domain/length control (if attribution is the goal).** Add Kspon-long and/or non-Kspon-short data with matched duration/compute. Without this, label the treatment the joint “Kspon-short mixture,” not a domain-only or short-only effect.
3. **Seed-43 robustness.** Run after or alongside the matched design if affordable. It tests seed sensitivity, not causality; same-test results remain exploratory.
4. **20 epochs only as a convergence question.** If pursued, include all relevant arms on the same schedule. The proposed 20-epoch plan is not step- or exposure-matched and is not a causal control.
5. **LoRA after baselines and evaluation are ready.** GPU smoke/parity can proceed as engineering; efficacy needs a matched no-LoRA control, prospective thresholds, and a new untouched evaluation set.

## 4. External claim sentence

> The V2 reader-only B3 recipe (Wave 1 plus approximately 4 h of selected Kspon short training data, balanced sampling) improved CER over the V2 B0′ recipe by 10.187 percentage points on dev and 9.737 percentage points on a one-time Kspon eval_clean procedural holdout. The documented recipe-level gate was met. Because B3 also received 3.13× the optimizer steps and 1.67× the audio exposure and differs in domain and duration mix, the result does not isolate a Kspon-short data effect. The holdout is not known to be speaker-independent; reuse for subsequent model comparisons is exploratory.

## 5. Uncertainties and verification limits

- This was a document/provenance review. I did not train, decode, run bootstrap resampling, or independently recompute CER from per-utterance predictions.
- The review and cited reports state that test text was excluded from vocabulary construction and the test was run once after freeze; I did not independently regenerate the manifests or audit raw audio content.
- Speaker IDs are absent, so speaker overlap and speaker-independent performance cannot be resolved from the available evidence.
- The request’s original review-base commit is unavailable in this shallow checkout; the synchronized HEAD recorded above is the version reviewed.
