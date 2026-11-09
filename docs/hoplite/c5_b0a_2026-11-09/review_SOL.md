Sol 6.1 high reviewer — independent external review of C5 B0-A.

# C5 B0-A review: NARROW, correctness before scale

## Review basis and boundaries

- Repository: `mandutt/unigem`; requested review basis: current `origin/main`.
- Executed `git fetch origin`, then `git pull --ff-only origin main`. Both succeeded; pull reported `Already up to date.`
- Resulting local HEAD and `origin/main`: **`1d0e756998e209faf35b0e46b962a195650b7d6f`**, `docs: add C5 B0-A review prompts and dispatch`.
- The checkout remained on its existing platform branch, `hoplite/kolophon-a5346747`; its HEAD equals the requested remote main HEAD. No branch change was necessary.
- I personally read **all 495 lines** of `reports/EXTERNAL_REVIEW_C5_B0A_2026-11-09.md`, including every Q1–Q12 item. I did not read other reviewers' answers or reuse their conclusions. Statements about earlier reviews below come from the request itself, not independent adoption of their answers.
- This was a static code/artifact consultation. No training, model evaluation, generation, metric-smoke runner, or aggregation entry point was executed. Read-only Python inspected existing JSON and checked arithmetic; it did not load data, weights, or models.
- No test 163 contents, P1 data, external APIs, subagents, or additional models were used. The only repository file written is this report. No production verifier changes, commit, PR, or experiment authorization are implied.
- Runtime verification was deliberately not attempted. The shell Python lacks Transformers, and the local mT5 model and native EG2 cache directories are absent. The repository lock lists `transformers==5.22.1`; framework-level regression checks below are requirements for a future authorized repair, not checks claimed to have run here.

## Executive judgment

**Final recommendation: NARROW.** Choose **A, a correctness-first repair of B0-A**, with small P/M controls as part of the repaired diagnostic. Do not interpret A as merely increasing steps or searching learning rates. Do not immediately launch the 300/95 B0-B, run only P/M while leaving the F/L path defective, or declare the entire mT5 track impossible.

There are three distinct findings:

1. **The published arithmetic yields INCONCLUSIVE.** The stored means, confidence intervals, paired difference, and seed counts support neither preregistered POSITIVE_SIGNAL nor NO_SIGNAL.
2. **The implemented primary metric has an independent target-alignment defect.** The mT5 labeled forward is seq2seq, but `token_losses` applies a causal-LM-style extra shift. Consequently, the reported `Δshuffled_copy` cannot yet be accepted as the preregistered copy-token CE estimand. This is a more specific limitation than low statistical power. Preserve the historical result; do not silently replace its numbers or call it a clean, correctly implemented negative experiment.
3. **Generation has a separate, real failure phenotype.** L is nonempty in only 22/60 cases, versus 60/60 for F. All 120 stored generations have length 257, including decoder start, and none end in EOS. The empty strings are not evidence of immediate-EOS termination. Undertraining, treatment-specific instability, and decoding/token behavior remain unresolved; decoder adaptation in general has not been falsified.

No gate change is approved by this review. Any corrected experiment, mode-policy change, LR/step change, added control, or inferential-policy change requires a new preregistration and explicit approval. Preserve historical thresholds, seeds, donors, and results; do not tune them to make B0-A pass.

## Evidence inspected

The following are repository-relative references at the review HEAD:

| Ref | Source and use |
|---|---|
| R | `reports/EXTERNAL_REVIEW_C5_B0A_2026-11-09.md`, complete request, scope, questions, reported limitations |
| PR | `docs/plan_c5_b0_prereg_v0_1.md`, especially §§3–9 and §14: data, matching, metric, guard, decision rules, separate B0-B approval |
| BA | `reports/C5_B0A_2026-11-09.md`, result and generation warning |
| AG | `reports/provenance/C5_b0a/aggregate.json`, all aggregate statistics; `runner/c5_b0a_aggregate.py:40–131`, aggregation and decision logic |
| U | All six `reports/provenance/C5_b0a/s{20261108,20261109,20261110}_{frozen,lora}.json`, headers, per-document metrics, and generation records |
| E0 | `reports/C5_E0_NATIVE_AUDIT_2026-11-09.md`; raw `reports/provenance/C5_e0/{native_tokenizer_audit,legacy_native_hidden_diff,wiring_audit}.json` |
| SM | `reports/C5_B0_METRIC_IMPL_2026-11-09.md`; `reports/provenance/C5_b0/mt5_lora_smoke.json` |
| RUN | `runner/c5_mt5_lora_b0.py`, particularly lines 96–159, 187–274, 427–513 |
| DEP | `runner/c5_mt5_layer_probe.py:52–82`, adapter/cache/label definitions; `runner/c5_a1_lora.py:45–64`, LoRA wrapper; `env/lock_local_2026-11-02.txt` |
| SV | `eval/slot_verify.py`, schema, extraction patterns, and `verify_summary` at lines 164–188; read only |

I independently checked that all six U files contain the same 20 document IDs, every retained document has five donor comparisons, the minimum reported copy-token count is 121, and all six stored copy guards are false. Recomputing document means from stored scalars reproduced F, L, and L−F to floating-point precision. I did not rerun a bootstrap; the quoted intervals are the stored intervals, with their implementation inspected statically.

## Two material code findings

### Finding 1 — primary copy CE is shifted one position too far

`make_labels` returns the tokenizer's target IDs directly (DEP, lines 79–82). RUN passes these as `labels` to `MT5ForConditionalGeneration`. Under the mT5 seq2seq labels contract, the model shifts decoder **inputs** internally: logit position `t` predicts label position `t`. The intended external CE must therefore compare `out.logits` with the same-position `labels`.

Instead, RUN lines 111–118 compare:

```text
out.logits[:, :-1, :]  against  labels[:, 1:]
```

RUN lines 140–148 also slice the copy mask to `[:, 1:]`. This aligns the mask to the shifted target array, but does not repair the wrong logit/label pairing. For labels `[a, b, EOS]`, the intended pairs are `(logit0,a)`, `(logit1,b)`, `(logit2,EOS)`; the current copy path uses `(logit0,b)`, `(logit1,EOS)` before masking.

**Consequences:**

- `Δshuffled_copy` is a real numerical statistic, but not the specified copy-token negative log likelihood. Equal treatment of F and L does not make the wrong estimand correct; its bias need not cancel between arms.
- Training uses the model's `out.loss` (RUN 470–471), not this manually shifted loss. `Δshuffled_full` also uses `out.loss` (RUN 119, 205–223). This finding does **not** by itself invalidate training, every CE number, or the generation observations.
- Zero-LoRA equality only checks equivalence of two paths; both can share the same metric error. The smoke is insufficient to validate label alignment.
- Before any further experiment, require a regression check that the mean of unmasked, same-position per-token CE over valid labels equals the model's `out.loss`, plus explicit first-token, EOS, ignored-label, and copy-mask alignment cases. This review did not run those checks.
- Existing JSON stores scalar losses, not the necessary logits. The train runner does not save adapter/LoRA checkpoints in its result-writing path. The historical primary cannot be corrected from those scalars alone. If an independently saved checkpoint exists, a later, specifically authorized corrected evaluation could be considered; its existence is not established here.

### Finding 2 — frozen base weights do not imply matched base dropout

`load_base()` returns an eval-mode model (RUN 85–93). F leaves it there. L calls `model.train()` (RUN 459–462), enabling the base decoder's training-mode dropout as well as LoRA dropout. Frozen parameters still participate in stochastic forward computation.

Thus F/L compare **LoRA plus a different training stochasticity policy**, not just LoRA. Both are eval-mode at final evaluation, but their optimization histories differ. The raw first-step train CEs already differ, e.g. seed 08 F 27.4400 versus L 37.4268, despite zero-output LoRA; this is consistent with the mode confound, not proof of its exclusive causal role.

The repair should explicitly match base-model mode in both arms while allowing the preregistered LoRA-branch dropout only in L. For example, keep the base in eval mode and separately enable the LoRA dropout modules during training; this does not disable gradients to trainable tensors. Log/assert module modes and trainable parameter identities. Do not claim the higher reported L training CE proves worse optimization: the reported train losses were measured under different dropout conditions.

## Q1. E0 tokenizer conclusion

**Verdict: agree**, within the audited corpus and settings; native cache remains required for this line of work.

**Evidence:** E0's raw overall summary confirms content-ID identity in 400/400 documents, zero character-ID mismatches over 498,455 characters, zero digit mismatches over 12,538, and native-only EOS in all 400. This substantially resolves the proposed widespread content-ID corruption mechanism for these inputs. It does not prove tokenizer equivalence for all text or sequence behavior. Hidden cosine is 0.991352 train / 0.991501 validation, with about 2.4–2.5% below 0.95. EOS/sequence semantics matter. U already records the native cache, so native-cache migration is not an explanation for a within-B0-A F/L difference.

**Next steps:**
1. Keep the existing native EG2 layer19 cache for all future F/L/M comparisons; verify tokenizer/model/cache provenance, masks, and EOS metadata before an authorized run.
2. Correct descriptions of legacy Stage A: it is not demonstrated to have widespread wrong content IDs. Keep its legacy sequence convention distinct from the native experiment.
3. Do not reopen T5Gemma2: a tokenizer comparison is not authorization to resume that bridge.

## Q2. Was the B0-A design acceptable screening?

**Verdict: conditional.** A disclosed two-arm screen is defensible; calling it the complete matched-control experiment is not.

**Evidence:** PR §§2 and 4 explicitly narrow B0-A to 20/20, three seeds, 100 updates, and defer P/M. Their absence does not retroactively make every exploratory observation worthless. It does mean a failed F/L contrast cannot distinguish bridge failure from an insensitive metric, inadequate native summarization adaptation, or language-model/length shortcuts. Moreover, actual matching is incomplete because of Finding 2, and the primary is defective because of Finding 1. Those are concrete implementation/design limitations, not just missing power.

**Next steps:**
1. Preserve B0-A as a disclosed, incomplete screen, with a metric-validity caveat; do not relabel it a completed four-arm B0.
2. Fix primary alignment and base-mode matching before another F/L experiment.
3. Include small, explicitly defined P/M controls in the repaired diagnostic before considering scale.

## Q3. Was INCONCLUSIVE statistically and methodologically correct?

**Verdict: conditional.** Correct rule application and aggregation of stored numbers; not yet a validated primary-metric experiment.

**Evidence:**

| Statistic | Mean | Stored document-bootstrap 95% CI |
|---|---:|---:|
| F | +0.007810 | [−0.037997, +0.051194] |
| L | +0.021751 | [−0.028004, +0.067209] |
| L−F | +0.013942 | [−0.052508, +0.078599] |

L fails mean ≥ .05, positive lower CI, and positive paired lower CI, despite 2/3 positive seeds. NO_SIGNAL also fails because L's mean is positive and its upper CI exceeds .05. Hence INCONCLUSIVE is correct on the recorded statistic. AG implements PR §8's stronger paired-CI condition, not merely the shortened request's `L > F` wording.

Donors are averaged within documents, seeds are averaged within documents, and the bootstrap resamples the resulting 20 document clusters. The paired contrast uses the same document IDs. I found no mean/sign/paired-aggregation error in these artifacts. This is **document uncertainty conditional on the three fitted seeds and donor design**, not a CI over arbitrary future training seeds. It is not 60 independent documents, nor does the three-seed sign count establish a robust seed-population result. Shared donor reuse further limits simple independent-document interpretations.

There are prospective fail-closed issues: the aggregator silently intersects document sets, reads copy guards from only the first seed, and does not incorporate guard failure into its decision. RUN enforces a five-token cutoff rather than PR's 20-token document guard and only exposes a median-coverage failure. None changes this run's label: all six document sets match, all stored guards are false, and minimum reported copy count is 121. The inner per-run field `seeds_positive` counts positive document deltas, not seeds; AG's separate seed counts are the appropriate 1/3 and 2/3 values.

The material methodological error is Finding 1, not arithmetic. Keep the historical INCONCLUSIVE label, but append **primary implementation not validated / copy-CE alignment defective**. This does not justify substituting NO_SIGNAL, POSITIVE_SIGNAL, or bridge-wide STOP.

**Next steps:**
1. Preserve the existing numerical report and label; add the distinction between arithmetic validity and estimand validity in a later authorized correction record.
2. Repair alignment and enforce the existing coverage/count guard across every unit, with exact document-set assertions and no silent exclusions.
3. Preregister the next analysis's fixed-seed versus new-seed estimand. If crossed document/seed resampling is added, resample matched seed blocks across arms, not 60 rows as independent observations, and do not silently replace B0-A's historical CI procedure.

## Q4. How should generation collapse be interpreted?

**Verdict: conditional.** It is a separate, serious observed failure; its cause is deferred, not identified as adaptation impossibility.

**Evidence:** U confirms L nonempty counts 2/20, 20/20, 0/20; F is 20/20 in every seed. All 120 generations have `gen_len=257` and EOS false. With a 256-new-token cap and one decoder-start token, this is cap exhaustion, including empty decoded outputs, not demonstrated early-EOS collapse. RUN decodes with `skip_special_tokens=True` but does not retain generation token IDs in train results. Empty text could conceal special/pad-token repetition or whitespace; that mechanism cannot be diagnosed from the saved strings.

- **① Underfit:** plausible, especially the shared absence of EOS, but not proven to explain L's seed dependence.
- **② LoRA/LR/dropout instability:** plausible and supported as a concern by the seed variability and known mode confound; no isolated LR or dropout causal test exists.
- **③ Generation/eval path:** must be checked, particularly raw tokens and native positive control. E0 checked forward wiring, not trained free-running generation. Current generation code enters eval mode for both arms, so accidentally leaving L in train mode during final decoding is not supported by this source.
- **④ Decoder adaptation itself fails:** not established beyond this configuration and budget.

Generation collapse alone does not make teacher-forced CE mathematically uninterpretable. It limits the claim to a teacher-forced conditional diagnostic and blocks a generation-success inference. PR §7 explicitly says to hold interpretation when generation collapses. Separately, Finding 1 prevents accepting the current copy CE as its intended primary. These must not be conflated.

**Next steps:**
1. In an approved repair, save raw token IDs and start/pad/EOS/special-token counts, true new-token length, cap hits, repetition, and checkpoint/config provenance for every arm/seed.
2. Check native P generation and matched-mode F/L generation with the same decoding contract; do not assume that more updates or an LR change is the cure.
3. Keep collapse unresolved and block scaling if it persists; do not reinterpret blank, no-EOS outputs as successful termination.

## Q5. What does B0-A establish about decoder adaptation?

**Verdict: agree** with narrowly limiting conclusions, with the additional metric caveat.

**Evidence:** The estimates are imprecise and span adverse and favorable effects. L−F includes zero. P/M are absent, base dropout differs, and the primary is misaligned. Therefore:

- **“NO_SIGNAL” as a preregistered category:** not reached.
- **“No demonstrated improvement”:** correct; no positive claim is supported.
- **“Underpowered inconclusive”:** a reasonable description of precision, but incomplete without the metric-validity and matching caveats. There was no prospective power proof that this budget should detect the target effect.
- **“LoRA unstable”:** acceptable as shorthand for seed-sensitive, degenerate generation in this L recipe; not proof of a general property of LoRA or a particular optimizer failure mechanism.
- **“Frozen decoder is the bottleneck,” “layer19 is best,” or “mT5 cannot bridge EG2”:** unsupported.

**Next steps:**
1. Report selectivity uncertainty, generation degeneration, and primary-implementation validity as separate findings.
2. Do not use the positive point estimate, 2/3 seed count, or attachment smoke to claim improvement.
3. Keep all findings separate from A1 native fallback and product readiness.

## Q6. What is the minimal next experiment?

**Verdict: conditional — choose A, correctness-first repair with miniature P/M controls.** B is premature; D alone leaves the defective F/L path unresolved; C is not compelled by this evidence.

**Evidence:** Repeating only the historical two arms cannot repair metric validity by itself. A large four-arm run would spend more compute on known defects. Native P is necessary to demonstrate a working positive path; M is necessary to separate content-bearing memory from generic decoder adaptation. Neither can retroactively validate the original F/L metric.

**Next steps:**
1. Seek a new preregistration for an implementation repair and bounded 20/20 diagnostic: correct label alignment, match base modes, define P/M, preserve the original three seeds and five-donor policy, instrument generation, and fix fail-closed accounting. No step/LR sweep is part of this recommendation.
2. After correctness checks, permit at most one final-checkpoint F/L/P/M run per original seed at 100 updates, only if explicitly approved, within the cap in Q12. This is a new diagnostic, not a replacement B0-A result or the 300/95 B0-B. Freeze control-validity and generation-usability conditions before execution; do not invent a retrospective pass rate here.
3. Stop the diagnostic at its cap, a repeated technical failure, a failed correctness invariant, invalid P/M, or unresolved catastrophic generation. Valid controls plus usable generation and still-inconclusive selectivity can motivate a **separate** B0-B decision; they do not automatically authorize it. Persistent L-specific degeneration can justify stopping this configuration on engineering grounds without proving all mT5 bridges impossible.

## Q7. Is the proposed B0-B appropriate, and what exactly are P/M?

**Verdict: conditional.** A 300/95, four-arm, three-seed design is a reasonable later candidate, not ready or guaranteed adequate, and not a clean untouched-validation confirmation.

**Evidence:** PR §9 leaves important control and inference details open. Its `val[5:100]` includes the 20 B0-A documents at `val[5:25]`; only 75 lie outside B0-A, and those are not established as untouched by all earlier work. Furthermore, the current cyclic trainer means 100/20 = **five document passes**, whereas 900/300 = **three passes**. “900 updates” is not automatically more training per document or a solution to collapse.

### Exact proposed control definitions, subject to new preregistration

| Arm | Definition and role |
|---|---|
| F | Native EG2 layer19 → trainable 512→512→512+LayerNorm adapter → frozen-base mT5 decoder; no decoder LoRA. |
| L | Same EG2 memory, adapter initialization, examples, order, budget, and base-mode policy as F; decoder self/cross q/k/v/o LoRA r8/alpha16/dropout .05, 64 modules. |
| P | Same mT5 checkpoint with its **frozen native encoder**, native mT5 tokenizer, and the same decoder LoRA inventory as L; no EG2 adapter and no encoder LoRA. Train decoder LoRA only, using the same documents, targets, fixed schedule, and decoding policy. Keep the encoder in eval mode. This is a positive headroom/control path, not an equal-parameter causal comparison with L. |
| M | Capacity-matched content-free L control: same trainable adapter and decoder LoRA as L, but replace EG2 hidden tokens in both training and evaluation with a fixed training-only mean vector. Define `mu = mean_i(mean_t(h_train_i,t))`, using the registered training set only, and repeat `mu` to the registered recipient length. No recipient text, target, document ID, validation mean, or recipient hidden values enter M's content. |

M retains length/mask structure and therefore is **content-free, not literally information-free**. That limitation must be explicit. Compare L real CE with independently trained M on matched target positions and length policy. At evaluation, donor swapping with a fixed common K must leave M's repeated-mean input unchanged, providing a strong wiring/metric invariance check. Zero-memory may remain an OOD diagnostic; it is not the primary negative control or proof of content use. The trained M arm and an inference-only memory ablation of trained L answer different questions and must not be mixed.

For P, compute real/donor selectivity with native encoder representations, true masks, the same target mask, and the same registered donor identities. Define pairwise common-length cropping in P's own representation; do not equate EG2 token counts with mT5 token counts. Freeze a source-span/truncation policy so P is not quietly given different semantic content. Differences in native-memory geometry limit interpretation of a numerical L/P ratio.

### Definition of done

- Correct unshifted CE and masks; built-in-loss agreement; frozen/external and zero-LoRA equivalence; exact module/parameter/mode assertions; native cache provenance; all expected arm/seed/doc results present.
- P demonstrates positive selectivity with lower CI > 0 under the registered analysis, plus independently usable native generation. If P fails, the assay/training budget is not validated; that is not a bridge STOP finding.
- M passes the equal-K input-invariance check, and L-vs-M real copy CE is reported as a paired, prespecified contrast. Retain primary `Δshuffled_copy`, seed tables, and paired L−F uncertainty.
- Treat PR §9's **25% PASS and 10% STOP relative-to-P rules as unapproved candidate B0-B rules**, not current decisions. A new preregistration must define how P uncertainty enters them. A suitable explicit formulation is paired joint-bootstrap contrasts `L−0.25P` and `L−0.10P`, alongside P validity, rather than comparing an L CI endpoint with a noisy P point estimate. This is a proposed operationalization, not an approved gate change. Do not lower the fractions or the B0-A .05 criterion in response to these results.
- Native P validity, stable decoding, artifact completeness, and the scope boundary are prerequisites. Otherwise return technical failure/INCONCLUSIVE, not automatic STOP or B1 approval.

**Next steps:**
1. Resolve the repair gate first, then preregister P/M training, lengths, donors, all decision contrasts, checkpoint choice, generation conditions, and compute before seeking B0-B approval.
2. Freeze a validation-exposure ledger and report reused B0-A versus other validation documents separately as preregistered descriptive strata. Do not describe the 95 as a pristine confirmatory holdout or use test 163 to create one.
3. Justify 300/95 and 900 updates through a prospective precision/training argument, not by assuming larger counts guarantee convergence or causal identification.

## Q8. Ranked Must-fix items before the next experiment

**Verdict: agree** that the following five items block another model experiment; implementation-only repair and design work must precede it. Successful control results are additionally required before any scale-up.

**Evidence:** RUN 105–148 contains the extra shift and five-token cutoff; RUN 459–462 differs in base training mode; U records 38 empty L outputs and no raw generation IDs; PR §§4, 6, and 9 defer P/M and specify the stronger count guard; AG 61–64 and 125–128 use document intersection and first-seed-only guard reporting. These concrete gaps, rather than the positive or negative direction of any estimate, determine the ranking.

| Rank | Must-fix | Completion evidence required |
|---:|---|---|
| **1** | **Fix seq2seq primary-metric alignment and mask/guard correctness.** | Same-position CE matches built-in loss over valid labels; first/EOS/ignored/copy positions checked; PR's 20-token and median-coverage guard enforced; historical results preserved separately. |
| **2** | **Match frozen-base training modes and expose the actual treatment.** | Assert F/L base dropout parity, trainable parameter identities, same adapter initialization/order, and eval-mode pre-update zero-LoRA equality. Log comparable eval-mode CE; do not confuse raw train-mode CE across arms. |
| **3** | **Make degeneration diagnosable and gate scaling on generation validity.** | Raw generation IDs, special/pad/EOS counts, cap/repetition/length metrics, fixed decoding config, checkpoint/adapter/LoRA provenance, and preregistered usability/technical-stop conditions. |
| **4** | **Define and wire P/M plus counterfactual provenance.** | Native frozen-encoder+decoder-LoRA P; training-only repeated-mean capacity-matched M; true/common-K masks; recorded five donor IDs and K values; self/duplicate-source exclusion checked. Current donor code excludes only identical IDs, not duplicate source text. This is a missing safeguard, not evidence that duplicates actually occurred. |
| **5** | **Register a bounded, fail-closed analysis and scope contract.** | New repair preregistration/approval; all six/twelve units and exact document sets asserted; every unit's guard enforced; fixed original seeds/donor policy; document-vs-seed uncertainty and validation reuse disclosed; fixed compute/checkpoints; explicit decision gate with no automatic B1/B2/C. |

**Next steps:**
1. Complete items 1–5 as code/design requirements without changing the historical experiment or product verifier.
2. Demonstrate correctness invariants before the authorized small diagnostic; establish P/M and generation validity before a B0-B proposal.
3. Treat any necessary correction to donor eligibility, seed policy, hyperparameters, or inference as a newly registered design change, never favorable post-result selection. No alternative seed/donor search is recommended.

## Q9. How many documents/updates are enough to conclude LoRA is ineffective?

**Verdict: disagree** with the premise that a universal count permits that conclusion.

**Evidence:** Twenty validation documents give wide paired uncertainty, three training seeds provide weak evidence about optimization variability, and the primary/mode defects are not repaired by adding samples. Updates and document passes differ: B0-A's five passes did not yield EOS, while the proposed 900-update B0-B has only three passes. Neither “100 is too little” nor “900 is sufficient” is established. A null result in one layer, adapter, LoRA placement, optimizer, and budget cannot establish general decoder-adaptation ineffectiveness.

**Next steps:**
1. For a later B0-B, preregister a smallest effect/precision target and a paired power/sensitivity calculation using document and seed variability; retain the existing candidate thresholds rather than picking a favorable effect after this result.
2. Define fixed training/checkpoint and adequacy criteria before execution; do not keep extending steps until validation looks positive. Any new LR or step schedule requires a separate preregistration.
3. Limit even a valid negative result to the registered mT5 configuration and budget. A resource-based decision to stop the track is permissible, but must not be presented as a general statistical proof that LoRA has no effect.

## Q10. Should layer role probing resume now?

**Verdict: agree** with continued deferral, at least through a valid B0 control/selectivity decision; B0-A does not increase its priority.

**Evidence:** Current failure modes are the outcome metric, mode matching, missing controls, and generation degeneration. A role probe cannot repair these, and layer19 remains a fixed anchor rather than an optimum. R §2 already requires native offsets, shortcut baselines, and FDR for any later probe. A new layer sweep now would add selection opportunities without resolving whether the decoder uses content at all.

**Next steps:**
1. Spend the next bounded diagnostic budget on validity and generation, not role probing or layer selection.
2. Require a separate later decision and preregistration for native-offset probing, shortcut baselines, multiplicity/FDR handling, and any layer-based selection.

## Q11. What metric audit is needed; can copy selectivity remain primary?

**Verdict: conditional.** Corrected `Δshuffled_copy` can remain the primary mechanistic selectivity metric; it is not a summarization-quality or factual-preservation gate.

**Evidence:** Coverage 0.8246 passes the current guard but does not prove source grounding or entity fidelity. RUN uses NFKC-normalized single-token surface substring matches after removing spaces; common Korean fragments, numeral fragments, and changed entity bindings can satisfy this mask. Copyability is not entailment, and donor cropping can remove evidence for tokens marked from the full source.

SV extracts typed regex slots and compares unique canonical strings. Its `new_slot_rate` is 0 when a summary has no extracted slots; an empty/generic output can therefore look perfect on **no-new alone**. The production verifier separately rejects missing source slots, so this is not a claim that its full reject gate accepts all empty outputs. Regex numeric/identifier containment also does not establish person/organization identity, correct number-to-entity relationships, or preservation of summary-relevant facts. Preserve that distinction.

**Next steps:**
1. Before another experiment, repair alignment, audit copy-mask positions/normalization against permitted train/validation examples, and verify the 20-token/coverage guard. Keep full CE, copy coverage, and generation failures visible; do not promote full CE to a replacement primary after seeing results.
2. Before B2 or Stage C, complete a preregistered, arm-blinded manual source/gold/output audit on allowed train/validation cases covering missing versus new slots, entity identity and bindings, numbers/units/dates, Korean spacing/subwords, blank/generic outputs, and repetitions. Report extractor precision/recall or false-positive/false-negative counts, denominators, and disagreements separately from model failures. No external LLM or P1 data is needed.
3. Publish no-new, source-slot preservation, gold-relevant fact/entity preservation, and generation usability separately. Keep `eval/slot_verify.py` unchanged; any product-gate proposal requires its own decision record and preregistration, not a threshold relaxation justified by B0-A.

## Q12. Final decision and permitted scope

**Verdict: conditional — NARROW.** This is an external recommendation, not experiment or gate approval.

**Evidence:** Arithmetic INCONCLUSIVE is defensible; broad STOP is unsupported. But the primary alignment defect, non-matched base dropout, missing controls, and seed-level generation degeneration block immediate expansion. Correctness-first repair has greater information value than scaling a compromised assay.

**Next steps:**
1. Obtain an explicit new decision for the bounded repair diagnostic described below. This consultation itself authorizes no execution or code changes beyond this report.
2. Return with correctness evidence, all arm/seed artifacts, control validity, generation traces, corrected fixed-rule statistics, validation-exposure disclosure, and compute accounting at the next gate.
3. Decide then whether to propose a separately registered B0-B, suspend the assay for invalid controls, or stop this mT5 configuration for reproducible degeneration/budget reasons. Do not automatically proceed to B1/B2/C.

### Scope and compute contract recommended for a future decision

| Item | Recommendation, only if separately approved |
|---|---|
| Allowed now | This consultation/report only; **zero training or evaluation**. |
| Allowed next | Implementation correctness repair, then one small **20 train / 20 val F/L/P/M diagnostic**, original seeds 20261108/09/10, fixed five-donor policy, final checkpoint only, max 100 optimizer updates per arm/seed. |
| Maximum next compute | **12 arm-seed units, at most 1,200 optimizer updates total, and at most 2 CPU wall-hours with at most six Torch threads** (whichever limit is reached first). Include runtime smokes/control checks in that wall-time cap. No GPU, external API, LR/rank/seed/donor search, best-checkpoint search, or automatic extension/retry beyond the cap. Stop if controls cannot be established in it; this cap is not a guarantee of power or convergence. |
| Repair gate | Correct CE/masks/guards, matched base modes, complete provenance, valid P, invariant content-free M, and preregistered generation-usability/technical checks. Stop/suspend on failure rather than reclassifying it as a bridge negative. |
| Statistical gate | Preserve original B0-A categories and thresholds. Any corrected-run inference is registered prospectively and reported separately. An inconclusive repaired screen can support a B0-B proposal only if assay/generation validity is established; it does not approve that run. |
| Later B0-B | 300/95 four-arm design is a separate decision with exact control, inference, validation-reuse, compute, and stopping specifications; its advertised 6–10 hours are **not authorized here**. |
| Forbidden | Immediate B0-B scaling, B1 layer sweep, B2 decoder comparison, Stage C, role-probing survey, P1, external LLM/API use, test access, product promotion, or retrospective threshold/seed/donor selection. |
| Test 163 | **Sealed throughout.** Do not inspect, evaluate, tune on, or use it as a new holdout. |
| A1 native | Frozen fallback/reference, not a product-approved comparator or replaced by exploratory bridge metrics. |
| T5Gemma2 | **D-108 STOP remains closed.** Only a new decision record could reopen it; nothing in this review does so. |

### Incorrect premises to avoid

- Content-ID parity implies identical sequence semantics or makes native provenance unnecessary.
- Attaching 64 LoRA modules and passing zero-init equivalence validates optimization, generation, or target alignment.
- Correct bootstrap arithmetic validates the underlying metric implementation.
- Empty decoded output proves immediate EOS; the stored outputs instead reach the cap without EOS.
- A positive point estimate/2-of-3 seeds proves improvement, or a nonpositive result under this small recipe proves bridge impossibility.
- More documents or updates automatically resolve undertraining, controls, and validation reuse.
- A no-new score alone establishes preservation or entity correctness.
- A review recommendation approves B0-B, changes product gates, replaces A1, unseals test 163, or reopens T5Gemma2.

**Bottom line:** retain B0-A as a historically faithful but incomplete and primary-metric-compromised **INCONCLUSIVE** screen. Treat generation degeneration as a separate unresolved training/decoding finding. Repair correctness and matching under a new bounded preregistration, validate P/M and generation, then make a new decision. **NARROW, not immediate CONTINUE and not bridge-wide STOP.**
