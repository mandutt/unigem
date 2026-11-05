# Independent review — Wave 2B domain/length controls

- **Review date:** 2026-11-05
- **Reviewer:** Hoplite / GPT-6 Luna
- **Scope:** Independent review round `w2b_domain_length`, Q1–Q11; no prior-round opinions used as authority.
- **Synchronization:** `git fetch origin` and `git pull --ff-only origin main` succeeded. The first resulting HEAD was `857eed071ff9be82e41d705862c0b17659ec3bf4`. A later fetch exposed a newer remote tip; a second fast-forward pull succeeded. **Final HEAD:** `e8c462e74e395a43876c0a19d0b9d01269a3aee0`. The 740-line request was unchanged between those heads. Its reported experiment baseline is `069879f`.
- **Review method:** Read the complete request and checked the cited result reports, bootstrap/budget/overlap provenance, `train/d5_reader.py`, and `eval/normalize.py`. **No training or evaluation experiment was rerun.**

## 0. Conclusion (B)

**B — Accept the findings only as caveat-qualified, exploratory evidence; this is not approval of a causal “domain effect,” a resolved length effect, or a new confirmatory gate.** The same-long Kspon-versus-Zeroth contrast is a large, well-separated *corpus/source-configuration association* on this dev set. It does not identify “domain alone.” The short-versus-long comparison remains confounded by roughly 2× optimizer updates. Before repeating the prior test result as clean evidence, reproduce the text-overlap audit with the project normalizer.

## 1. Q1–Q11

### Q1 — Domain conclusion

- **Judgment: B.** The result supports a strong contrast between these two long-data corpus configurations, but not an isolated causal effect of “domain.”
- **Evidence:** B3-long and B3-zeroth-long use the same Wave1 base, nominal 4h additions in the 8–16s range, 10h caches, natural sampler, V2 vocabulary, initialization, seed, and 12 epochs. They have 5,568 versus 5,676 updates. On 500 dev utterances, CER is 0.283946 versus 0.365571; the paired difference is −8.1625 percentage points (Kspon lower; 95% utterance-bootstrap CI [−9.2063, −7.1645]). This is a large measured separation. However, “source” also changes speakers, recordings, text style, within-bin length distribution, OOV filtering, and other corpus properties. OOV clip exclusions are 7.33% for Kspon long and 4.47% for Zeroth long. The CI is conditional on these trained checkpoints and utterances; it does not cover seed/training variability or establish generalization.
- **Required action:** Describe this as “Kspon-long versus Zeroth-long source/corpus-configuration effect on the 500-utterance dev set,” not “domain alone.” Retain OOV and selection details. A short-domain claim would require a direct short-domain arm; the existing comparison only supports the long-length contrast.
- **Blocks:** **Next step:** No, for the planned step-matched length diagnostic. **LoRA:** No for exploratory implementation; broad causal/public domain claims remain blocked by the wording and evidence limits, not by the missing Zeroth-short arm.

### Q2 — Length conclusion and step-matched design

- **Judgment: B.** It is correct to leave the short-length effect unresolved. The proposed accumulation change is preferable to replaying long clips, with explicit residual caveats.
- **Evidence:** B3-nat is 0.263314 with 11,196 updates; B3-long is 0.283946 with 5,568 updates. The 2.0632-point advantage for B3-nat has a dev utterance-bootstrap CI excluding zero, but that bootstrap does not repair the approximately 2× update-count confound. Long and short selection also have different clip counts and OOV exclusion rates.
- **Required action — minimum useful step-matched comparison:**
  1. Keep the same Wave1 + 4h Kspon data definitions, V2/remapped initialization, seed 42, natural sampler, optimizer, peak LR, and full training horizon. Do not replay the long data twice: that changes long-data exposure and repetition/overfitting.
  2. For B3-long, use **batch=2, grad_accum=2** (batch=1, grad_accum=4 is a comparable alternative). With 3,711 clips this is 928 updates/epoch, or **11,136 over 12 epochs**, versus B3-nat’s 11,196. For an exact pairwise budget, rerun/cap B3-nat at the same 11,136 optimizer updates from the same initialization; set the cosine schedule explicitly in optimizer-step units and use a hard optimizer-step cap rather than relying on epoch patience. This is a 0.54% difference from the historical B3-nat budget and preserves nearly the same total audio exposure (about 119.6h versus 120.2h).
  3. Record valid audio frames/seconds per update and the effective utterance batch. The proposed long run has about four examples/update versus eight in the historical short run; average audio seconds/update are close because each arm has about 10h per epoch, but this is not identical optimizer noise. A frame-budgeted accumulation policy would be preferable if practical. Report this as a minimum diagnostic, not a pure causal estimate.
  4. The current `train/d5_reader.py` derives cosine `T_max` using floor division, while the final partial accumulation can produce a ceiling number of actual updates. Set `T_max` to the actual declared update budget so the schedule is not accidentally short by a few steps. Use dev 500 only; one seed remains exploratory.
- **Blocks:** **Next step:** Yes, for a length-effect conclusion or a Wave2C-short decision based on causality; no, for running this diagnostic. **LoRA:** No for exploratory LoRA engineering; it does block using the current short-versus-long result as causal support for LoRA/data claims.

### Q3 — Zeroth-long substitution for unavailable Zeroth-short

- **Judgment: B.** The substitution was methodologically acceptable as a different, long-length source control, but it is not a substitute for the originally planned non-Kspon-short comparison.
- **Evidence:** After excluding the 1,534 Wave1 Zeroth clips, only 1,012 short clips / 1.6574h remained, not the planned 4h. The Zeroth-long arm therefore answers “Kspon long versus Zeroth long,” not “Kspon short versus non-Kspon short.” It leaves the domain-by-length 2×2 incomplete.
- **Required action:** Keep the unrun short-domain contrast explicit. A new 4h short corpus is needed only if the desired claim is domain-at-short or a full domain×length comparison. If using FLEURS train or another corpus, precheck that it actually supplies sufficient 0.5–8s labeled clips, freeze source/selection and license/provenance, report length/OOV composition, and keep evaluation data out of training. Prefer speaker/session identifiers and disjoint groups where available. Do not present FLEURS as matched merely because it is Korean speech.
- **Blocks:** **Next step:** No, for the long-source comparison or step-matched length run; yes, for non-Kspon-short or full-factorial claims. **LoRA:** No; it is not a prerequisite for an exploratory LoRA study.

### Q4 — V2 vocabulary dependence

- **Judgment: B.** Freezing V2 makes the existing arm comparisons more comparable, but does not remove selection dependence from the absolute CERs or establish broad vocabulary generality.
- **Evidence:** V2 preserves V1’s 1,101 IDs and adds 228 characters after a two-pass loop: draft vocabulary → first short selection → final V2 → short reselection. No dev/test leakage is reported, but selection and short-data character coverage are linked. All controls use fixed V2 and the same remapped head, which is a strength for those within-V2 comparisons.
- **Required action:** Label absolute results “V2-vocabulary-conditioned”; report OOV rates by arm. Keep V2 fixed for a direct source/length comparison. If coverage requires a new vocabulary for a future corpus, define one train-only union vocabulary before training and rerun all compared arms with it; do not give each arm a separately selected head/vocabulary and compare the resulting CER as if only data changed.
- **Blocks:** **Next step:** No, if V2 and its selection rule are frozen. **LoRA:** No, but the LoRA/no-LoRA pair must use the same vocabulary and report coverage.

### Q5 — Test reuse and confirmatory status

- **Judgment: B.** “In-domain procedural holdout, used once” is accurate; calling it a fresh or speaker-independent sealed test is not.
- **Evidence:** The 2,400 Kspon eval_clean utterances were used once for B0′ versus B3. New matched-budget and domain/length controls stayed on dev 500. The split is duration-stratified, not speaker-independent, and 90 spare utterances are not a meaningful confirmatory replacement.
- **Required action:** Do not use the same 2,400 to select or claim confirmatory results for step-matched B3-long, non-Kspon-short, or LoRA. Keep those comparisons dev-only/exploratory. A confirmatory LoRA claim needs a **fresh, predeclared holdout** (preferably speaker/session-disjoint or from an independent source) and a no-LoRA comparator matched on data, initialization, optimizer steps, exposure, schedule, and evaluation. Use that new holdout once. The spare 90 are not sufficient.
- **Blocks:** **Next step:** No for dev-only work; yes for any new confirmatory claim using the old test. **LoRA:** Blocks confirmatory LoRA claims, not implementation or dev-only exploration.

### Q6 — B0′ matched-budget controls

- **Judgment: C** for the claim that compute/exposure have been ruled out; **B** for the narrower observation that either increase alone failed to close the dev gap in these exploratory runs.
- **Evidence:** B0′-20 is exposure-matched (120.0h vs B3’s 120.3h) but has 5,960 versus 11,196 updates. B0′-38 is approximately step-matched (11,324 versus 11,196) but sees 228.0h, nearly twice B3’s exposure, by repeating the same 6h. Its 0.3687 and B0′-20’s 0.3657 remain far from B3’s 0.2682. These are useful negative controls, but they do not jointly match exposure and steps. The 20/38-epoch cosine schedules differ from B3’s 12-epoch schedule; B0′ is natural-sampled while B3 is balanced-sampled. They are single-seed, dev-only, and lack FLEURS guardrail results.
- **Required action:** Say “in these controls, increasing exposure alone or optimizer steps alone did not close the gap,” not “compute/exposure is ruled out.” Treat repeated-data saturation/overfit and schedule/sampler differences as live limitations. B0′-rep10 could be a secondary data-repetition control if the unique-hours question becomes decision-critical, but it is not the highest-value next training run.
- **Blocks:** **Next step:** No; blocks only the broad compute-exclusion claim. **LoRA:** No.

### Q7 — B3-nat and sampler

- **Judgment: B.** “No sampler effect was detected on dev” is suitably cautious; “the samplers are equivalent” is not supported.
- **Evidence:** B3-nat is 0.49 points better than balanced B3 on dev, with the stated CI including zero. B3-nat and B3-long both use natural sampling, so their direct contrast is not confounded by balanced-versus-natural sampling. B3-long and B3-zeroth-long also share the natural sampler. The balanced B3 versus long comparison does change sampler and should not be used alone to infer length.
- **Required action:** Keep sampler fixed within each contrast and report “not detected,” not “no effect.” Do not reopen the used test to re-evaluate B3-nat. If sampler itself matters to the decision, preregister a small, matched sampler comparison on dev or a future holdout.
- **Blocks:** **Next step:** No. **LoRA:** No; fix sampler for the LoRA/no-LoRA comparison.

### Q8 — Text-level overlap

- **Judgment: C** as a closed item; this remains an unresolved audit that materially qualifies the old test result.
- **Evidence:** The prior 136/2,400 (5.7%) text-overlap report has not been reproduced with the project normalizer. `overlap_final.json` records clip-ID intersections only and therefore does not close text-level overlap. The evaluation implementation uses `eval.normalize.normalize_nospace`, which applies NFC, lowercasing, punctuation/non-word removal, whitespace normalization, then removes spaces. Identical normalized transcripts do not prove audio-clip leakage, but they can make the test less independent and may advantage a model trained on those target strings. The reported deduplicated Δ (9.74→9.48pp) suggests the large direction may survive, but that calculation is not yet verified.
- **Required action:** Reproduce the reference intersection between test and each training source using `normalize_nospace`; document exact counts, IDs, and normalization. Recompute the old paired CER/bootstrap with overlapping test utterances excluded as a sensitivity analysis (no retuning or retraining). Keep both full and non-overlap results and continue to describe the test as used once. This is analysis, not a reason to spend the next training run.
- **Blocks:** **Next step:** Does not block dev-only step matching, but blocks treating the prior test as an unqualified clean confirmation. **LoRA:** Blocks confirmatory use of that test; fresh holdout is required regardless.

### Q9 — B3-zeroth-long result

- **Judgment: B.** It is a useful same-length source comparator, but its near-baseline score does not identify why Zeroth-long adds little on this dev set.
- **Evidence:** B3-zeroth-long is 0.365571 versus B0′ 0.370084; B0′−B3-zeroth-long is +0.4513pp with CI [−0.2087, +1.1278], so improvement is not detected. B0′-20 is 0.3657 at similar exposure and a broadly similar step budget, making a “new long data automatically helps” story unwarranted. Best-versus-final dev CER for Zeroth-long is 0.3654 versus 0.3656, which does not show a large late-epoch collapse; it cannot rule out overfit or optimization effects. The dev set is short-heavy (74.33% ≤4s), while the new data is 8–16s.
- **Required action:** Treat domain/source mismatch, long-only distribution against a short-heavy dev set, OOV/sample selection, and optimization budget as plausible explanations, not a ranked causal diagnosis. The same-long paired contrast remains informative as a source-configuration comparison; do not use B0′ non-significance to claim Zeroth data has zero effect.
- **Blocks:** **Next step:** No. **LoRA:** No.

### Q10 — Next priority and LoRA sequencing

- **Judgment: B.** Run the step-matched long/short diagnostic before making a Wave2C-short causal decision. A non-Kspon-short arm is conditional, not a prerequisite to LoRA.
- **Evidence:** The step-matched run is the cheapest direct check of the largest remaining length confound (roughly 1.5–2 CPU hours per the project estimate). The domain-at-long contrast is already large enough to retain as a narrow exploratory finding. The unavailable Zeroth-short arm is only necessary to answer domain-at-short. LoRA is a distinct intervention and has not been implemented/run.
- **Required action:** First close the text-overlap audit as a non-training prerequisite for repeating the test claim. The **one additional training experiment** to prioritize is the exact-step-budget B3-nat/B3-long comparison described under Q2. Then freeze a fresh holdout and matched no-LoRA design before any confirmatory LoRA evaluation. Run non-Kspon-short only if the decision requires a short-domain/full-factorial result. LoRA can be implemented or explored on dev without waiting for that short-domain arm, but do not stop the length inquiry and then describe short-length benefit as established.
- **Blocks:** **Next step:** Yes for resolving the length claim; no need to run non-Kspon-short first. **LoRA:** No for implementation/dev exploration; fresh holdout plus matched no-LoRA comparator blocks confirmatory LoRA claims.

### Q11 — Proposed public statement

- **Judgment: C** for the sentence as written; its broad domain and compute wording overstates the controls, and its test result needs the overlap caveat.
- **Evidence:** The descriptive B3/B0′ numbers are documented (dev 0.370084→0.268214, 10.187pp; previously used test 0.359643→0.262270, 9.737pp). But B3 versus B0′ changes data amount, source, length, optimizer updates, and sampler; the B0′ controls vary exposure and updates separately with limitations. “Kspon domain effect is strong” generalizes beyond the long-only source comparison. “Short-length effect unresolved” is correct because B3-nat has 11,196 updates versus B3-long’s 5,568.
- **Required action:** Use the narrower wording below and keep the used-once/test-overlap status adjacent to the test number. Do not claim a pure “4h short data effect”: the B0′→B3 contrast is a recipe comparison with multiple simultaneous changes, not an isolated intervention on shortness.
- **Blocks:** **Next step:** Blocks the exact sentence, not dev-only work. **LoRA:** Blocks confirmatory wording based on the used test; not exploratory LoRA work.

## 2. Must-fix table

| ID | Must-fix | Required action | Priority | Blocking status |
|---|---|---|---|---|
| MF-1 | Unreproduced 136/2,400 text-overlap finding | Recompute intersections with `eval.normalize.normalize_nospace`; report full and non-overlap paired test sensitivity without tuning. | **P0 before public use of test result** | Does not block dev-only next run; blocks unqualified test-confirmatory wording. Fresh holdout still required for confirmatory LoRA. |
| MF-2 | B3-nat vs B3-long step confound | Run the fixed-step paired comparison (target 11,136 updates; batch 2/accumulation 2 for long; exact step scheduler/cap; disclose effective-batch difference). | **P1 before any length/Wave2C causal claim** | Blocks length conclusion, not LoRA implementation or a separate exploratory LoRA track. |
| MF-3 | No fresh independent holdout for new confirmatory claims | Freeze a new holdout before LoRA/next gate; prefer speaker/session-disjoint or independent source; pair with matched no-LoRA. | **P0 before confirmatory LoRA/gate** | Blocks confirmatory LoRA claims; not engineering or dev-only exploration. |
| MF-4 | “Domain” over-attributes a corpus-source comparison | Use “Kspon-long vs Zeroth-long source/corpus-configuration association”; retain speaker/recording/style/OOV/length limitations. | **P0 for broad external causal claim** | Does not block narrow long-source reporting or LoRA. |
| MF-5 | B0′ controls do not jointly match steps and exposure | Limit wording to each axis tested separately; note schedule, sampler, and 6h repetition. | **P1 before saying compute/exposure are ruled out** | Blocks that causal phrasing only; not next run or LoRA. |
| MF-6 | V2 two-pass vocabulary dependence | Label CER V2-conditioned; preserve one frozen train-only vocabulary across future direct comparisons and show OOV. | **P1 before broad absolute-CER claims** | No block if fixed for existing comparisons; future vocabulary change requires rerunning comparators. |
| MF-7 | No Zeroth-short 4h / incomplete factorial | Keep the missing arm explicit; collect a qualified 4h short source only if short-domain is a required claim. | **P2, conditional on domain-at-short question** | Does not block long-domain reporting, step-match, or LoRA. |

## 3. Next experiment priority

1. **Analysis prerequisite:** close the text-overlap audit using the project normalizer before presenting the old test result as clean evidence. The old test has already been used once; this audit does not make it fresh again.
2. **One additional training experiment:** run a step-matched B3-nat/B3-long pair on dev only, with an explicit common optimizer-update budget and step-based cosine schedule (Q2). This is the direct, low-cost test of whether the observed short advantage persists after update count is controlled. It is still exploratory at one seed.
3. **Before confirmatory LoRA:** predeclare a matched no-LoRA control and a fresh, once-used holdout. Non-Kspon-short is not required first unless the project wants a domain-at-short or complete factorial claim.

**Exact minimum long design:** same Wave1 + Kspon-long 4h, V2, remapped init, seed 42, natural sampler, and 12-epoch data exposure; B3-long `batch=2, grad_accum=2` gives 928×12=11,136 steps. Rerun/cap B3-nat at 11,136 updates for exact update matching, set cosine `T_max=11,136`, and do not stop early. The short arm’s approximately 0.5% lower exposure from the cap and the 4-versus-8 example/update difference must be disclosed. Do not replay the long corpus twice as the primary control; that would increase its exposure and repetition. If resources permit, use a frame-budgeted batch policy and/or repeat the comparison across seeds before making a stronger causal claim.

## 4. Public-claim wording

> In a single-seed, V2-vocabulary-conditioned reader-only pilot, B3 (Wave1 plus 4h of Kspon short data) had CER 0.2682 versus 0.3701 for B0′ on the 500-utterance Kspon eval_clean dev subset, a 10.19-point difference. The previously used 2,400-utterance in-domain procedural holdout showed 0.2623 versus 0.3596 (9.74 points); it was used once, is not speaker-independent, and a reported text-overlap finding remains to be reproduced with the project normalizer. Separate dev-only long-data controls showed 0.2839 for Kspon-long versus 0.3656 for Zeroth-long (8.16 points; paired utterance-bootstrap 95% CI for the Kspon advantage 7.16–9.21), consistent with a large source/corpus-configuration difference at long lengths, not an isolated domain-only effect. The short-versus-long comparison does not establish a length effect because the short arm used about twice the optimizer updates. B0′ controls did not close the gap when exposure or steps were increased separately, but do not fully rule out compute/schedule effects.

**Do not say:** “The 4h short-data effect is proven,” “the effect generalizes across speakers,” “Kspon domain alone caused the full B3 gain,” “compute/exposure is ruled out,” or “the 2,400 set remains a fresh sealed test.”

## 5. Remaining uncertainty

- Training-seed variability is not represented by the paired utterance bootstrap; all new controls are seed 42 and dev-only.
- The long arms share a broad 8–16s bin, not necessarily identical within-bin duration distributions. Speaker/session, recording, style, and transcript-selection differences are not isolated.
- OOV filtering differs across sources, and V2 was selected through a two-pass short-data loop. Fixed vocabulary aids arm comparison but conditions the reported CER.
- The text-level overlap count and its effect have not been independently reproduced; clip-ID disjointness is not a substitute.
- The 2,400 test is an in-domain, duration-stratified, used-once set and not speaker-independent; spare 90 cannot replace it.
- No LoRA results, GPU smoke test, or fresh-holdout result were examined or run in this review.

