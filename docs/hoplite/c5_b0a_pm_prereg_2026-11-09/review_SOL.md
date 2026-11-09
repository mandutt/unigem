# Sol 6.1 high reviewer — independent C5 B0-A Phase 6 P/M preregistration review

Reviewer: **Sol 6.1 high**. Date: **2026-11-09 UTC**. This is a new, independent consultation round, not a continuation or reuse of the earlier B0-A review.

## Review basis and boundaries

- Ran `git fetch origin`, then `git pull --ff-only origin main`; both succeeded. Pull reported `Already up to date.`
- Reviewed local HEAD and `origin/main`, both **`26e334a79148e8be73e3378b6c82846891f1e180`**. The existing workspace branch was retained; its contents matched the requested review basis.
- Personally read the entire 356-line external review request, entire 314-line preregistration, both requested result/repair reports, all 802 lines of the runner, and all 128 lines of the metric tests. Also inspected the referenced alignment/P0/debug provenance and relevant Adapter/LoRA helpers.
- Read the historical three-review synthesis only as requested project history. Its recommendations and other reviewers' original reports were not used as substitutes for this review; I did not open those original reviews or any peer report for this round.
- **No training, evaluation, model forward, generation, or tests were executed.** The reported 54 passing tests are historical repository evidence, not a fresh verification by me. JSON inspection was read-only artifact inspection, not a new evaluation.
- No subagents, additional models, external APIs, P1 data, or sealed test 163 were accessed. I did not open the dataset or split file. T5Gemma2 remains closed under **D-108 STOP**.
- The only authored repository file is this report. This document recommends gates; it does **not** approve or launch Phase 6, B0-B, B1, B2, or Stage C.

### Source shorthand

| Reference | File |
|---|---|
| Request | `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_2026-11-09.md` |
| Plan | `docs/plan_c5_b0a_pm_prereg_v0_1.md` |
| P0 | `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md` |
| Repair | `reports/C5_B0A_REPAIR_2026-11-09.md` |
| Runner | `runner/c5_mt5_lora_b0.py` |
| Tests | `eval/tests/test_c5_b0_metric.py` |
| Provenance | `reports/provenance/C5_b0a/{metric_alignment_probe,p0_native_sanity,repair_debug}.json` |

Line references below refer to the synchronized revision above.

## Executive conclusion

**Final recommendation: NARROW, conditional and correctness-first. Execution approval remains outstanding.**

The underlying decomposition is useful: native P checks the native-memory/decoder-LoRA assay, F/L checks the repaired EG2 treatment package, and eval-only M probes the *same L checkpoint* under an input intervention. Neither inserting an adapter into P nor separately training M is necessary for these narrow questions.

However, v0.1 is not implementation-ready without a frozen clarification/addendum. Its largest practical hazard is comparing a full-length mean-memory evaluation against `real_ce_copy` that the existing runner averaged over **donor-specific cropped lengths**. Its largest inferential hazard is interpreting an off-manifold mean replacement as proof of semantic content use, or a nonsignificant control as proof of no content use. Eligibility, pooled decision semantics, mode handling for P, provenance, and resource accounting also need explicit contracts.

P0 is meaningful supporting evidence: train delta-copy **+3.7617**, CI **[1.8917, 5.6050]**; val **+5.2375**, CI **[2.5013, 8.0753]**. It establishes native-path sensitivity on these reused documents, not that trained P will pass, that LoRA creates that sensitivity, or that the EG2 bridge works. The historical extra CE shift remains a confirmed defect; the current correction is supported by source and provenance, not a reason to reinterpret old B0-A copy results.

## Compact Q1–Q12 verdicts

| Question | Verdict | Bottom line |
|---|---|---|
| Q1 P validity | agree | Adapter bypass is appropriate for a native-path assay control, not a capacity-matched bridge control. |
| Q2 Eval-only M | agree | Valid same-checkpoint ablation; trained M answers a different question and is not required here. |
| Q3 Mean definition | conditional | Potentially leakage-free conditional on length; construction, cohort, and missingness rules must be frozen. |
| Q4 F/L/P comparison | conditional | Paired L-minus-F selectivity; P only validates its own native path. No cross-arm ranking. |
| Q5 Small diagnostic | conditional | Suitable screening envelope, not adequate confirmatory or generalization evidence. |
| Q6 Thresholds | agree | Retain L's .05; P/M zero-boundary sensitivity tests serve different roles. |
| Q7 M sufficiency | disagree | A positive mean-replacement contrast alone does not establish semantic content use. |
| Q8 P failure | conditional | Operational assay-not-validated gate, not proof the metric or bridge is invalid. |
| Q9 M failure | conditional | No affirmative evidence from this control; not evidence of no content use or equivalence. |
| Q10 Must-fix | conditional | Five ranked blocking contracts below; prior fixes must be preserved, not reinvented. |
| Q11 B0-B boundary | agree | Even favorable results require a new preregistration and explicit decision. |
| Q12 Final scope | conditional | NARROW recommendation only; no execution approval from this consultation. |

## Q1. Is P, with adapter bypass, a valid positive control?

- **Verdict: agree.**
- **Evidence:** Plan lines 58–67 define native mT5 encoder memory, no adapter, frozen base, and decoder-only LoRA. This is an appropriate control for whether the native path remains sensitive after that LoRA training procedure. P0 lines 27–35 and its JSON show substantial positive real-minus-wrong discrimination in both splits, including **18/20 positive val documents**. `native_source_ids` and `native_memory` implement the prefixed native path (Runner lines 129–141).
- Adding a randomly initialized/trained adapter would introduce another potentially broken interface and undermine the purpose of the native positive control. Matching trainable parameter counts is unnecessary for assay validation. Conversely, adapter bypass means P does **not** test the EG2 adapter and cannot explain whether an L failure is due to adapter alignment, EG2 representations, or optimization.
- P0 was already positive without LoRA. Thus a positive final P demonstrates **preserved/available sensitivity after training**, not that LoRA produced or improved sensitivity. P's final pass does not establish the correctness of every F/L implementation path.
- **Next steps:**
  1. Keep the bypass; explicitly freeze/eval the native encoder and shared/base parameters, attach only the same 64 decoder self/cross q/k/v/o LoRA modules, and optimize LoRA only.
  2. Verify zero-output-LoRA P against the unmodified native path on identical prefix, labels, lengths, and donors; this is P's equivalence check, not equality to F/L.
  3. Record initial/final native-path checks without selecting checkpoints by val performance; describe final positivity as a validity check, not a LoRA improvement claim.

## Q2. Is eval-only M valid, and is trained M mandatory?

- **Verdict: agree**, for the stated same-checkpoint intervention.
- **Evidence:** Plan lines 69–83 and Request lines 212–216 ask whether a fixed L checkpoint scores real memory better than a train-derived mean. Holding the model and adapter checkpoint fixed isolates that input replacement more directly than comparing two separately optimized models. A trained M would instead ask whether a model *optimized on a constant/mean input* can learn the target distribution.
- This is a **mean-memory replacement baseline**, not literally a memory-free or guaranteed in-distribution null. A trained M is not required for this bounded diagnostic. It would be relevant to a different claim about the incremental benefit of content-conditioned training over a separately optimized target-prior baseline. Compute convenience is not the scientific justification for distinguishing these estimands.
- **Next steps:**
  1. Keep M eval-only and use the exact final L adapter/LoRA checkpoint, with no optimizer updates or recalibration during mean construction/probing.
  2. Name the estimand precisely: held-out target CE change under replacement of this checkpoint's real representation by its train-derived, length-conditioned mean.
  3. If a separately trained no-source baseline becomes necessary, require a new preregistration and compute decision; do not add it automatically to this round or presume B0-B approval.

## Q3. Is the mean definition leakage-free and adequate?

- **Verdict: conditional.** It can be leakage-free, but it is not target-independent without qualification and is underspecified operationally.
- **Evidence:** Plan lines 89–105 restrict inputs to train20 and define the mean over documents with `len(h_i) >= K`, excluding a target when fewer than ten training documents qualify. This avoids direct val/source/label inclusion **if enforced**. But Plan line 76 says “repeated/cropped,” whereas lines 91–96 specify a position-wise prefix mean with no repetition. These are different interventions. No implementation of `mean_mem` or `m_eligible` exists in the reviewed runner.
- For final L adapter `A_s`, training lengths `l_i`, and full target memory length `K_j`, the intended definition should be frozen as:

  ```text
  E(K_j) = {i in the fixed train20 : l_i >= K_j}
  mu_s,K_j[t] = (1 / |E(K_j)|) * sum_{i in E(K_j)} A_s(h_i)[t]
  for 0 <= t < K_j, eligible iff |E(K_j)| >= 10.
  ```

- Use deterministic eval-mode, detached, **post-adapter** representations, one document vote each, excluding padding. `A(mean(h))` is not equivalent to `mean(A(h))`: the adapter contains GELU and LayerNorm (`runner/c5_mt5_layer_probe.py`, lines 52–63). Do not repeat a pooled vector, include padded zeros, or mix full-real memory into the mean.
- Using target source **length** is a permitted nuisance match, not target-label leakage. Nevertheless both the eligible training subset and mean depend on K, so this is content-independent **conditional on length**, not a completely target-independent input. A train-fitted adapter may contain training-label information; that is ordinary training, not direct val leakage. Train/val source duplicates or val-driven checkpoint selection would compromise the intended held-out interpretation and require explicit checks.
- The ten-document condition concerns the number of contributors **per mean**, not the number of evaluable val documents. Long targets may be disproportionately excluded. The plan provides no minimum evaluable-val cohort or low-coverage status; a tiny selected subset cannot stand in for val20. I have not inspected the underlying lengths, so I cannot assert that adequate coverage is feasible.
- **Next steps:**
  1. Make the formula above authoritative in a pre-debug addendum, remove the repetition ambiguity, freeze the checkpoint, and enforce a builder API that accepts only allowlisted train IDs/memories and K, never val representations or labels.
  2. Before outcome inspection, freeze the length-derived eligible val cohort, minimum evaluable-document requirement, and explicit `M_NOT_EVALUABLE` handling; report all exclusions, contributor IDs/counts, and length distribution. Never add donors/docs or alter K to rescue a failed result.
  3. Test with synthetic inputs that changing val content/labels at fixed K cannot change the mean, changing an ineligible training item cannot change it, and fewer than ten contributors yields no numeric M score. A different mean definition requires a new preregistration, not a post-result substitution.

## Q4. What F/L/P comparisons are interpretable?

- **Verdict: conditional.**
- **Evidence:** Plan lines 39–67 intentionally vary memory source and trainable components. Repair lines 72–79 and `repair_debug.json` support equal initial F/L CE **27.43998146057129** under the repaired mode policy. Runner lines 665–724 use the same EG2 adapter architecture and select deterministic donors. L additionally trains **458,752** LoRA parameters in the debug provenance; F has **526,336** adapter parameters only. P is not matched to that adapter treatment.
- Interpret L-minus-F as the incremental **adapter-plus-LoRA training package** relative to adapter-only training, with paired initialization, data order, optimization settings, and EG2 donor interventions. It is not a pure “capacity” experiment: the adapter can co-adapt differently, and active LoRA dropout is part of the L treatment. P independently checks native-path sensitivity. P passing while L fails does not localize the failure to one bridge component.
- `L > F` needs an explicit scalar. The appropriate reading here is greater mean **delta-shuffled-copy**, not lower absolute real CE, greater training loss reduction, or a larger value than P. All arms use mT5 target labels; a different target tokenizer is not needed to explain why their interventions are not directly comparable. Native and EG2 lengths/donor identities can differ.
- **Next steps:**
  1. Freeze `L > F` as the positive paired mean of `delta_L(s,j) - delta_F(s,j)` over identical EG2 documents/donors/K and the registered seeds; report its paired CI without silently adding a new CI-based gate.
  2. Report per-arm selectivity and P validity separately. Do not rank bridge quality from P-versus-L/F absolute CE or delta magnitude.
  3. Preserve paired F/L initial adapter states, document order, and optimizer settings; explicitly seed P's LoRA initialization independently of whether an adapter was instantiated.

## Q5. Is 20/20, 100 updates, three seeds sufficient?

- **Verdict: conditional**, sufficient for bounded screening, not confirmatory inference.
- **Evidence:** Plan lines 113–122, 150–157, and 251–260 bound the proposed experiment at nine trained units and 900 updates plus M evaluation. P0's large positive native contrast makes an assay sensitivity check reasonable. It does not establish power for a repaired L effect near **.05** or for L-minus-F. These val documents have already been used for earlier diagnostics, including P0; three seeds do not create new held-out documents.
- The sample is twenty document identities, not 60 independent seed-document observations and not 100 independent donor pairs. Seed-averaged document bootstrap intervals are conditional on these seeds and the fixed donor construction; they do not quantify all training-seed uncertainty or remove dependence caused by reused donors. The plan appropriately calls the experiment exploratory (lines 299–306).
- **Next steps:**
  1. Retain the fixed splits, original seeds, 100 updates, and final-checkpoint-only policy; report seed means/ranges and all per-document paired data alongside the specified bootstrap.
  2. Freeze an integrity-only one-seed gate, with no extra seeds, seed replacement, early checkpoint selection, or step extension after seeing results. Count any reusable debug units inside the nine-unit ceiling.
  3. Prohibit claims of generalization, production summarization quality, equivalence, bridge-wide failure, or sufficient power at .05. A future confirmatory design needs its own preregistration and explicit treatment of validation reuse.

## Q6. Keep L's .05, but not apply it to P/M?

- **Verdict: agree.**
- **Evidence:** Plan lines 161–193 retain L's original **.05** and give P/M the distinct criterion of positive mean with CI lower bound above zero. L's threshold is a historical effect-size convention for bridge screening; P/M test whether their specific contrasts have a resolved positive direction. There is no demonstrated common calibration across native shuffled memory, EG2 shuffled memory, and EG2 mean replacement.
- Correcting CE alignment does not establish that .05 has the same practical meaning as before. Retaining it prevents retrospective threshold relaxation; it does not validate its scientific utility. A tiny significant M effect remains tiny, and a large unresolved effect remains unresolved.
- **Next steps:**
  1. Keep .05 and the existing zero-boundary P/M criteria unchanged; report effect sizes in nats/token and intervals, not only boolean labels.
  2. Freeze pooled-versus-seed-level decision semantics before debug: seed-average each document first, then bootstrap documents; interpret the “2/3 seeds > 0” clause explicitly rather than leaving the quantity ambiguous.
  3. Require a new preregistration for any later threshold, seed, donor, mask, or step change. Do not use this diagnostic to retroactively repair B0-A's compromised primary results.

## Q7. Is M_CONTROL_PASS sufficient evidence of content use?

- **Verdict: disagree.**
- **Evidence:** Plan line 302 already states that M pass alone is insufficient. Plan lines 191–195 support only the claim that real memory beats the specified mean. Averaging post-LayerNorm representations can change norms, covariance, attention-key/value structure, and diversity; a decoder trained on real memories may simply dislike this off-distribution replacement. Matching K controls token count within a pair, but does not make the distribution or position-conditioned priors identical.
- Position-wise means deliberately retain shared positional/task/corpus structure and length-conditioned frequency information. The primary copy mask is broad: P0 coverage is **.8351/.8246**, and Repair lines 118–127 report the strict candidate at **.2161/.2427**, with manual precision adjudication still pending. A favorable contrast can reflect lexical/topic compatibility, not faithful semantic summarization or evidence-grounded generation.
- **Next steps:**
  1. Interpret a pass as **specific mean-replacement sensitivity**, corroborated rather than established by the existing length-matched real-versus-wrong-source contrast. Keep the conservative exploratory joint label only after all integrity checks.
  2. In the preregistered diagnostics, report K/contributor-count strata, real/mean representation norm summaries, full-target CE, copy coverage/upper warning, and the already proposed strict-mask secondary. These are descriptive checks, not new post-hoc pass thresholds.
  3. For a stronger content-use claim, require a new preregistration for content counterfactuals that preserve nuisance properties and separate generic source compatibility from target-specific information. Do not add trained arms or extra data to this consultation.

## Q8. If P fails, should it be ASSAY_INVALID rather than bridge STOP?

- **Verdict: conditional.** The operational gate is right; the scientific wording is too categorical.
- **Evidence:** Plan lines 168–172 explicitly forbid generalizing P failure to bridge STOP. That is correct. But `P_POSITIVE = false` can mean low power, degradation during P's LoRA training, implementation failure, or a resolved negative result. P0's positive native results mean a failed *trained* P does not automatically invalidate the corrected CE metric. Missing/non-finite data are not statistical negatives.
- **Next steps:**
  1. Keep progression blocked and interpret `ASSAY_INVALID` as **“assay validity not established for this trained protocol”**; distinguish unresolved, negative, missing, and technical-failure reasons in the artifact.
  2. Inspect, without tuning, the recorded native prefix/shape/masks/donors, initial-versus-final checks, same-position CE equality, frozen encoder/base state, LoRA gradients, and finite-loss trace. Restore training mode after any evaluation helper.
  3. Report the failure; any additional model run, altered learning rate/steps, or changed P criterion requires a new decision/preregistration. Do not infer EG2 bridge-wide failure or reopen T5Gemma2.

## Q9. If P succeeds and M fails, is NO_CONTENT_USE_EVIDENCE valid?

- **Verdict: conditional**, only as “not established by this control.”
- **Evidence:** Plan lines 195–197 equate failure with being indistinguishable from mean. That is not generally correct. Failure includes a positive estimate with a wide interval, a near-zero estimate, or a resolved **negative** estimate where mean is better. Ineligible/missing M is a different state altogether. No equivalence margin or powered equivalence test is registered.
- The decoder can use aggregate training-derived content and structural priors in mean memory. That is not target-specific passage use, but neither does real≈mean prove the decoder ignores real content. A single intervention can fail to detect relevant dependence. Conversely, real>mean would still not, by itself, establish semantic content use.
- **Next steps:**
  1. Retain the cautious label only with the qualifier “no affirmative target-specific content-use evidence from this mean-replacement probe”; never translate it as “L does not use content.”
  2. Report estimate/CI/eligible n and separate unresolved, negative, and `M_NOT_EVALUABLE` outcomes; do not call missing eligibility a control failure or equality result.
  3. Block automatic scale-up and require a fresh decision for any further diagnostic; do not respond by training M or relaxing thresholds within this round.

## Q10. Ranked Must-fix items before implementation/debug

- **Verdict: conditional.** The repaired CE and F/L mode policy have real supporting evidence. The blockers are freezing their PM contracts and closing the following design/implementation gaps, not repeating an unrestricted repair experiment.

### 1. Freeze the mean builder, leakage boundary, and eligible cohort

Resolve Plan line 76 versus lines 89–105 in favor of one exact post-adapter position-wise formula. Allow only fixed train20 IDs and source memories, final checkpoint, and K; no target/donor content, labels, val-driven adapter fitting, padding, or repetition. Check train/val ID and normalized-source disjointness without accessing test. Freeze length-only eligibility, its minimum evaluable-val requirement, and a non-evaluable status **before outcomes**. Keep the existing contributor threshold of ten. Save contributor identities/counts and mean/checkpoint hashes. Do not silently pool only whichever seed/doc rows survived.

**Acceptance evidence:** synthetic provenance/invariance tests, deterministic reconstruction, and an outcome-blind cohort manifest. The builder's data interface should make target-label leakage impossible rather than merely asserting `test_split_used: false`.

### 2. Preserve same-position CE and extend mode/parameter invariants correctly to P

The alignment provenance gives built-in/aligned **31.98719596862793**, versus old shifted **33.9515380859375**. Runner lines 107–126 now implement same-position CE; Tests lines 25–46 check equality and unshifted copy selection. Preserve this for every PM path, including ignored labels, first/EOS positions, and actual partial copy masks. Use a valid-label mean with absolute tolerance **1e-5**.

`set_training_mode` accepts only F/L and requires an adapter (Runner lines 329–381); P needs an explicit no-adapter path, encoder/base eval and frozen, LoRA train only, and deterministic eval for all probes. F must have **zero** LoRA modules, not 64: Plan line 218's blanket F/L/P inventory wording conflicts with its F definition. L/P each require 64. Log trainable counts and verify nonzero LoRA learning without demanding every zero-initialized branch parameter have a first-step gradient.

`token_losses` calls `model.eval()` (Runner line 114), while training mode is set once before the loop (line 697). An alignment probe inserted into training could silently disable LoRA dropout for subsequent updates. Run equality checks in explicit evaluation phases or save/restore the complete mode policy. P must be explicitly seeded: the current seed reset resides in `make_adapter`, which P bypasses. Synthetic PM tests should not all inherit the existing model-availability class skip (Tests line 13).

**Acceptance evidence:** P/F/L inventory, freeze/mode, zero-LoRA equivalence, same-position, and post-probe mode-restoration tests; no skipped required model-backed proof presented as a pass.

### 3. Freeze donor/K semantics and do not reuse the wrong real-CE baseline for M

Runner lines 423–445 average real CE across donor-specific `K = min(real_length, donor_length)`. Plan lines 91–95 instead define M at the target's **full real length**. That averaged `real_ce_copy` cannot be subtracted from a full-K M CE: two treatments would differ in real length as well as memory content. Recompute real and mean CE at the **same full K_j**, same checkpoint, labels, copy mask, and cross-attention mask for each eligible M document. Name/store that real baseline separately. Do not substitute the shuffled-evaluation baseline.

For shuffled probes, freeze five unique nonself, nonduplicate-source donors, length metric, tie-break, crop rule, and insufficient-donor behavior before outcomes. F/L must share donors/K. P may use its native-token length matching, but must preserve the chosen contextualization rule: current P0 **crops source IDs then encodes** (Runner lines 186–193), not full-encoding then slicing contextual states. Save the prefix/EOS/truncation policy. Record whether the frozen full-source primary copy mask includes pieces not visible after crop; do not quietly redefine it.

**Acceptance evidence:** deterministic donor manifest with IDs/source hashes/full lengths/K, tests of equal-length real/wrong and real/mean pairs, and explicit missing/short-donor statuses. The current donor helpers exclude only identical IDs, not duplicate source texts (Runner lines 144–150, 318–325).

### 4. Make pooling, decision clauses, and missingness executable without interpretation

Implement Plan lines 152–157 literally: first average the same document across all three registered seeds, then perform 1,000 paired document bootstrap resamples with frozen RNG/95% interval rule. Average donors within documents first. Use joint document resampling for L-minus-F. Freeze `L > F` as paired mean selectivity difference >0; report its CI without adding significance to the gate. Define the two-of-three clause explicitly; my natural reading is that at least two **per-seed L mean delta-shuffled-copy** values exceed zero. If another quantity was intended, resolve it before debug rather than choosing after results.

P/M primary booleans should use the same clearly identified pooled estimator; report per-seed results separately. Maintain .05/zero boundaries. Specify no-data, insufficient eligibility, non-finite, and missing-unit handling before computing labels. A partial run is not a pooled three-seed result. Document intervals as conditional on these seeds/fixed donor design and labels as exploratory on reused val.

**Acceptance evidence:** deterministic hand-constructed fixture tests for seed/document aggregation, donor averaging, L-minus-F pairing, sign boundaries, and all incomplete-data statuses. No model evaluation is needed to test the aggregation code.

### 5. Bind artifacts, checkpoints, approval stages, and the compute cap

The current runner has no PM mode or PM mean path (CLI, Runner lines 753–789); the PM tests in Plan lines 234–239 are requirements, not completed coverage. `train_arm` returns metrics without saving a reusable adapter/LoRA checkpoint (lines 715–750). Same-checkpoint M therefore needs either immediate in-process probing or an explicitly saved, hash-bound final checkpoint. Defer no binding until after a process exits.

Each expected arm/seed artifact needs revision/config hashes; exact split allowlists; initialization/optimizer/order/steps; checkpoint identity; module inventory/modes; CE alignment result; donor-level K and real/wrong scores; separately named full-K real/mean scores; contributor IDs/counts and eligibility; mask coverage/warnings; registered generation telemetry; elapsed/CPU accounting; and an explicit completion/error status. Optional F/P mean probes conflict in scope between Plan line 98 and line 244 and are absent from the M compute table; designate **L-only M** for this bounded proposal unless a revised preregistration explicitly budgets more. Do not create a separately trained “mean” unit through an ambiguous arm selector.

Plan line 257 calls the limit “wall time <=2 CPU-hours,” with six threads. Two wall-hours at six busy cores can consume about twelve core-hours. Resolve that ambiguity before debug; my conservative recommendation is **both <=7,200 aggregate process-CPU seconds and <=7,200 elapsed seconds**, at most six threads, no GPU. Account for child processes, model preprocessing, debug, training, evaluation, generation, and M; stop and report partial artifacts at the first cap. No automatic retry/extension. A one-seed debug must not become nine production units plus three unbudgeted debug units. Stage-specific manifests must not treat six intentionally unlaunched units as a run failure.

**Acceptance evidence:** an outcome-blind dry contract/manifest review, explicit owner-approved resource definition and debug scope, fail-fast budget enforcement, and complete first-stage artifacts. Audit correctness/provenance at the next gate, not whether seed one is conveniently favorable.

**Next steps for Q10:**
1. Owner freezes a versioned pre-debug addendum/new preregistration addressing these five contracts; do not edit scientific definitions after debug outcomes.
2. After explicit implementation permission, implement and prove the contracts with synthetic/static tests plus separately authorized model-backed correctness checks.
3. Submit the code diff, test evidence, exact debug scope/budget, and cohort/donor manifests for explicit implementation/debug gate sign-off. This consultation itself grants no run permission.

## Q11. Does a favorable Phase 6 authorize B0-B?

- **Verdict: agree** that it does not.
- **Evidence:** Plan lines 185–208, 270–279, and 301–306 explicitly separate B0-B and later stages. Native P and same-checkpoint M validate limited aspects of a small, reused-val screening protocol; neither establishes bridge generalization, summarization quality, causal semantic use, or power for 300/95 conclusions.
- A complete favorable P/M/L pattern, coherent full-CE/secondary diagnostics, no leakage/mode/metric failures, and reproducible artifacts can justify **considering a new B0-B proposal**, not launching it. A missing/ineligible control, unresolved P, negative/unstable findings, incomplete seeds, or cap/contract failure is a reason not to advance automatically. No L signal at this n is not bridge-wide STOP.
- **Next steps:**
  1. Require a new B0-B preregistration specifying estimands/controls, prospective power or MDE under the corrected metric, validation reuse limits, exact data/compute, and stop rules.
  2. Obtain a separate explicit decision after reviewing complete Phase 6 evidence and outstanding alternative explanations; no result label can substitute for that decision.
  3. Keep B1/B2/Stage C unapproved, P1 unused, test 163 sealed, and T5Gemma2 under D-108 STOP. Reopening that model would require a new decision record.

## Q12. Final verdict, scope, cap, and next gate

- **Verdict: conditional. Final recommendation: NARROW.**
- **Evidence:** The native positive signal and corrected source support continuing design work rather than stopping the entire bridge. The unresolved Must-fix contracts and explicitly unapproved status in Plan lines 4, 270–277, and 310–314 prevent an unconditional implementation/debug or three-seed execution endorsement.
- **Next steps:**
  1. Resolve/freeze the five Must-fix items and obtain explicit owner approval for implementation and its bounded correctness/debug procedure.
  2. If separately authorized, use only seed **20261108** for the initial F/L/P debug stage, at most **100 updates per arm**, final checkpoint only, with L-only eval M and no scientific tuning. Treat those three units as the first three of the nine-unit maximum if accepted, not an additional run allowance; no automatic rerun or seed replacement.
  3. Return to an integrity/provenance gate with completed stage artifacts and budget usage. The remaining two seeds and any B0-B proposal require their own explicit decisions; favorable debug metrics alone are insufficient.

### Decision ledger

| Item | Recommendation / present status |
|---|---|
| Overall | **NARROW, conditional**; not bridge-wide STOP, not CONTINUE to scale. |
| Implementation | Recommend only after frozen Must-fix addendum and explicit permission; **not approved by this report**. |
| One-seed debug | Conditional recommendation after contract/test gate and owner authorization; **not authorized or executed here**. |
| Three-seed execution | **Withheld** pending separate integrity/result gate and explicit authorization. |
| Maximum diagnostic envelope, if later authorized | F/L/P only; 9 arm-seed units, <=100 updates each, <=900 total updates; M eval-only for L; debug counted inside this envelope. |
| Resource recommendation | No GPU; <=6 threads; <=2 aggregate process-CPU hours **and** <=2 elapsed hours including debug/eval/generation; no automatic extensions/retries. Resolve units before execution. |
| Next gate | Frozen design, PM implementation/test evidence, outcome-blind cohort/donor manifests, exact compute meter; then authorized seed-one artifacts and completeness review before any remaining seeds. |
| B0-B / B1 / B2 / Stage C | **Not approved**. Favorable Phase 6 results do not change this automatically. |
| test 163 | **Sealed, unopened, unused**; no Phase 6 debugging or gate use. |
| P1 / external APIs | Unused and prohibited for this review/proposal. |
| T5Gemma2 | **D-108 STOP maintained**; no reopening without a new decision record. |

### Incorrect premises to avoid

1. “A valid P must match the adapter's capacity.” No: that would change the assay question.
2. “Positive trained P means LoRA created selectivity.” No: P0 is already positive.
3. “Eval-only mean is a trained memory-free baseline.” No: it is an input replacement at a fixed checkpoint and retains train/length/position priors.
4. “Train-only construction is completely target-independent.” Only conditional on K, with disjointness and no val-driven checkpoint selection enforced.
5. “M can reuse shuffled evaluation's real CE.” Not when shuffled real CE averages donor-specific cropped lengths but M uses full K.
6. “M pass proves semantic use; M fail proves no use or equivalence.” Neither implication follows.
7. “Three seeds produce sixty independent held-out documents.” They do not.
8. “54 historical tests mean PM paths are verified.” PM paths/tests do not yet exist in the reviewed runner; I did not rerun any tests.
9. “Two wall-hours with six threads equals two CPU-hours.” Not under aggregate CPU accounting.
10. “NARROW review or favorable Phase 6 approves Phase 6 execution/B0-B.” This consultation does not confer execution approval, and B0-B remains a separate decision.