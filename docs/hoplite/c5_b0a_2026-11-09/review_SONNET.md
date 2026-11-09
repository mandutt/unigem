I am the Sonnet 5.5 (reasoning: high) independent external reviewer for the unigem C5 B0-A review round.

# Independent review: C5 B0-A (EG2 layer19 → mT5-small decoder adaptation)

- Review basis: origin/main HEAD `1d0e756998e209faf35b0e46b962a195650b7d6f` (`docs: add C5 B0-A review prompts and dispatch`). `git fetch origin` and `git pull --ff-only origin main` both succeeded, and the workspace was already up to date. The result commit the request describes is `c66f17c`.
- Read in full: `reports/EXTERNAL_REVIEW_C5_B0A_2026-11-09.md` (all 495 lines), `docs/plan_c5_b0_prereg_v0_1.md`, `reports/C5_B0A_2026-11-09.md`, `reports/C5_MT5_LAYER_PROBE_2026-11-08.md`, `reports/C5_B0_METRIC_IMPL_2026-11-09.md`, `runner/c5_mt5_lora_b0.py`, `runner/c5_b0a_aggregate.py`, and the relevant parts of `runner/c5_mt5_layer_probe.py` and `runner/c5_a1_lora.py`.
- Raw artifacts inspected: `reports/provenance/C5_b0a/{aggregate.json, s{seed}_{frozen,lora}.json}`.
- Constraints respected: no training or evaluation was run, test 163 was not opened, no P1 data or external API was used, no subagents or other LLMs were used, and no repository file was modified. The only write is this file.
- My own checks were limited to arithmetic on the existing per-document JSONs. That means recomputing CIs and cross-checking CE fields. The E0 tokenizer and wiring numbers are taken from the request document and were not re-derived by me.

---

## 0. Executive summary

1. **The INCONCLUSIVE label is formally correct and robust.** I recomputed the aggregate from the per-document values. It reproduces the reported means and CIs (t-interval and bootstrap agree), and a two-way (documents × seeds) bootstrap gives wider CIs with the same verdict. Both POSITIVE_SIGNAL and NO_SIGNAL fail on more than one condition.
2. **The "LoRA generation collapse" is mis-framed. Both arms are degenerate.** All 120 generations (F 60, L 60) hit the 257-token cap and none produced EOS. F outputs look like `남    고고   고고 …` or whitespace, and L outputs look like `고 고 고 …`, `을 을 을 …` or pure whitespace. `nonempty` is a `.strip()` test, so "F 60/60 vs L 22/60" is a metric artifact. The real finding is that neither arm left the unigram regime in 100 batch-1 updates. Train CE last-10 is 6.26–7.35, and val copy-CE is about 7.7–8.1.
3. **The primary metric has an unverified, probably real, implementation defect.** `token_losses` compares `logits[:, :-1]` with `labels[:, 1:]`. In HF T5 the decoder input is `shift_right(labels)`, so `logits[t]` already predicts `labels[t]`. That would make the per-token CE off by one. The artifacts are consistent with this: 14 of 120 per-document rows violate a necessary inequality, discussed under Q3/Q8. This is a suspicion that needs a one-line unit test, not a proven bug.
4. **F and L are not matched.** F trains with the decoder in eval mode, while L calls `model.train()`, so base T5 dropout is active. At identical weights, step-0 CE is 27.4 / 21.7 / 37.0 for F against 37.4 / 32.1 / 49.1 for L. That is +10.0 / +10.5 / +12.1 nats from dropout alone. L−F therefore measures LoRA plus dropout, not LoRA.
5. **The "copyable" mask is close to vacuous.** Coverage is 0.8246 (per document 0.76–0.88). Spaces are stripped and single syllables count, so Korean particles and endings match almost any source. The coverage guard only protects against low coverage.
6. **B0-A could not have answered its own question.** The power at the observed variance was about 50% (L) and about 30% (L−F) even for the preregistered effect of 0.05, and the regime was untrained. It was a cheap, useful shakedown that exposed the problems above. It is not evidence about the bridge.

**Recommended verdict: NARROW.** Do zero-training fixes first, then a new preregistration, then run the positive control P and the null control M before interpreting F/L. Details are in Q12.

---

## 1. Independent re-verification of B0-A numbers

All values were recomputed from the per-document `delta_shuffled_copy` in `aggregate.json` and `s*_*.json`.

| quantity | reported | my recompute |
|---|---:|---:|
| F mean | +0.007810 | +0.00781 (n=20, sd 0.1026, SE 0.0229) |
| L mean | +0.021751 | +0.02175 (sd 0.1134, SE 0.0254) |
| L−F mean | +0.013942 | +0.01394 (sd 0.1596, SE 0.0357) |
| F CI | [-0.0380, +0.0512] | t-CI [-0.0402, +0.0558] |
| L CI | [-0.0280, +0.0672] | t-CI [-0.0313, +0.0748] |
| L−F CI | [-0.0525, +0.0786] | t-CI [-0.0608, +0.0887] |
| seed means F | -0.0029 / +0.0334 / -0.0071 | same, seed SD 0.022 |
| seed means L | +0.0339 / +0.0513 / -0.0199 | same, seed SD 0.037 |
| seed diffs L−F | n/a | +0.0367 / +0.0179 / -0.0128 |
| two-way (docs×seeds) bootstrap CI, L | n/a | about [-0.066, +0.081] |
| two-way bootstrap CI, L−F | n/a | about [-0.089, +0.108] |

- The aggregation matches the prereg: seed and donor are averaged inside each document, then documents are resampled.
- `bootstrap()` uses the same RNG seed for F, L and the paired difference. This is harmless and keeps the resamples paired.
- The reported CIs are conditional on these three seeds. Seed SD (0.022–0.037) is comparable to the document-level SE, so the reported CIs understate total uncertainty. The two-way bootstrap above shows by how much, and the verdict does not change.
- The decision rule is applied correctly in code. L fails POSITIVE on mean ≥ .05, CI lower > 0 and paired L−F lower > 0. L fails NO_SIGNAL because its mean is > 0.

Other facts from the raw JSONs that matter below:

| item | F (seeds 08/09/10) | L (seeds 08/09/10) |
|---|---|---|
| train CE step 0 | 27.44 / 21.68 / 36.98 | 37.43 / 32.15 / 49.10 |
| train CE last-10 mean | 6.26 / 6.86 / 6.62 | 7.29 / 7.31 / 7.35 |
| val `real_ce_full` (aligned `out.loss`) | 6.50 / 7.21 / 6.89 | 6.92 / 6.88 / 7.20 |
| val `real_ce_copy` | 8.07 / 7.97 / 7.84 | 7.70 / 7.65 / 7.91 |
| `wrong_ce_copy − real_ce_copy` | -0.003 / +0.033 / -0.007 | +0.034 / +0.051 / -0.020 |
| generation length | all 257 (cap) | all 257 (cap) |
| EOS | 0/60 | 0/60 |

---

## 2. Answers to Q1–Q12

### Q1. E0 tokenizer conclusion
- **Verdict: agree** (conditional only on provenance bookkeeping).
- **Evidence:**
  - Content IDs are identical in 400/400 documents, with 0 character mismatches over 498,455 characters and 0 digit mismatches over 12,538. The only difference is one native EOS token.
  - That removes the "tokenizer IDs broadly corrupt the EG2 PLE" hypothesis for content tokens. It does not address mT5-side tokenization of the targets. That is a separate tokenizer, and B0 uses it only for labels.
  - The legacy-vs-native hidden cosine is 0.9914 / 0.9915 mean, with 2.4–2.5% of tokens below 0.95. This is a real, small, non-zero difference from the EOS token alone, so it is not nothing.
  - B0-A already used the native cache (`data/wave2c/eg2_native_layer19/layer19`), so this was applied correctly.
  - I took the E0 numbers from the request and did not re-derive them.
- **Native cache for B0-B:** keep it, as a matter of provenance rather than necessity. It costs nothing, it is the actual EG2 input, and it removes a confound. The mismatch is small but the cost of using it is zero.
- **Next steps:**
  1. Record the native tokenizer hash and cache metadata in the B0-B prereg, and assert `test_split_used: false` in the cache.
  2. State explicitly that E0 settles source-side content IDs only. The mT5-side label tokenization and the copy mask are separate (see Q8).

### Q2. Adequacy of the B0-A design
- **Verdict: conditional.** It is acceptable as a cheap shakedown. It is a design defect to treat it as a matched B0 or as evidence about the bridge.
- **Evidence:**
  - The prior review's MF3 asked for four matched arms (F/L/P/M). The prereg deliberately deferred P and M and said B0-A would make no strong causal claim, which is honest. The cost was about 32 CPU-minutes.
  - The omission that actually hurt is the lack of a positive control. Without P, a null result cannot distinguish "LoRA does not help" from "this metric and regime cannot detect memory use at all". At 100 updates and unigram-level CE, the regime almost certainly cannot.
  - Two design problems go beyond P/M:
    - **F and L were not run under the same train-mode.** The runner calls `adapter.train()` for F, but only calls `model.train()` for L. L therefore trains with T5's base dropout (0.1) active, F with none. The step-0 CE gap above (+10.0 / +10.5 / +12.1 nats at identical weights and identical zero-initialised LoRA) proves the arms differ by something other than LoRA. The request lists "dropout/train mode" as a confound (§7) but does not weigh how large it is.
    - **The metric was never validated.** The "metric smoke" only checked that the code ran on 2 documents, with untrained weights (Δ = -0.1496). No unit test checked that per-token CE matches `out.loss` (see Q3 and Q8).
- **Next steps:**
  1. Record B0-A as a shakedown whose main yield was finding the three defects above, not as a failed screening.
  2. In any successor, require arms to differ in exactly one factor, and validate the instrument with P and M before F/L are interpreted.

### Q3. INCONCLUSIVE verdict
- **Verdict: agree** on the label. **Conditional** on the interpretation: INCONCLUSIVE here means "the instrument is unvalidated and underpowered", not "close to significant".
- **Evidence:**
  - No aggregation errors found. See §1 for the recomputation.
  - L fails POSITIVE on three of four conditions, and F−L inference is nowhere near significant (t ≈ 0.39 for L−F).
  - **Power.** At the observed document SD (0.113 for L, 0.160 for L−F) and n = 20, SE is 0.025 and 0.036. For a true effect equal to the preregistered 0.05, the power to get CI lower > 0 is about 50% for L alone and about 30% for L−F. The 80%-power minimum detectable effect is about 0.07 (L) and about 0.10 (L−F). So B0-A could not detect the threshold it set. Caveat: the SD was measured in an untrained regime and could differ after real training.
  - **"Positive seeds 2/3" carries almost no information.** With three seeds it is a coin-flip count, and the seed-level L−F differences (+0.037, +0.018, −0.013) are of the same size as their spread.
  - **NO_SIGNAL is structurally almost unreachable.** It requires mean ≤ 0, so any small positive mean can only be INCONCLUSIVE however narrow the CI. This is a property of the preregistered rule, not a result. I am not proposing to change it for B0-A. The B0-B rule (STOP when P is valid and L's upper bound is below 10% of P) is better because it is relative to a calibrated positive control.
  - **Metric validity concern (new).** `token_losses` does `logits[:, :-1]` against `labels[:, 1:]`. `make_labels` returns plain `[y1…yn, </s>]` with no leading start token, and HF `MT5ForConditionalGeneration` builds decoder inputs with `shift_right(labels)`, so `logits[t]` already predicts `labels[t]`. The per-token CE used for `Δshuffled_copy` would then score position t's prediction against token t+1. Supporting evidence from the artifacts:
    - The aligned `real_ce_full` (6.5–7.2) is lower than the copy-token CE (7.7–8.1), even though copyable tokens are 82% of the target.
    - If the CE were aligned, full CE could not be lower than coverage × copy-CE (that would need the non-copy tokens to have negative CE). Across all 120 per-document rows (6 units × 20 documents), 14 violate that by more than 0.05 nats. The worst margin is −0.62. The coverage definition is slightly different from the shifted mask, so I treat this as strong evidence, not proof.
    - Secondary `Δshuffled_full` uses the aligned `out.loss` and is also near zero (F means 0.005 / 0.008 / −0.009, L 0.035 / 0.055 / −0.030), so the conclusion "no detectable memory selectivity in this regime" holds either way. But the primary metric has never been shown to measure what the prereg describes.
- **Next steps:**
  1. Add a unit test asserting that the mean of the per-token CE vector equals `out.loss` (atol 1e-5) on a few documents. This is forward-only and needs no training. Fix the shift if it fails. Both are maintainer actions, and I did not run anything.
  2. Report B0-A as "INCONCLUSIVE, as run, instrument unvalidated". Keep the as-run numbers in the record and do not overwrite them.
  3. Report seed-level inference with a two-way bootstrap or more seeds in any successor.

### Q4. Generation collapse
- **Verdict: disagree** with the framing of "LoRA collapse" as the headline. I rank the causes as: ① underfit is primary, ③ the generation/eval metric is an artifact, a train-mode dropout confound is secondary, and ④ is not supported.
- **Evidence:**
  - **Both arms are degenerate.** All 120 generations have `gen_len` 257 (cap hit) and EOS 0/120. Examples:
    - F, seed 09: `남    고고   고고   고고 …`, then trailing whitespace, with whitespace-only strings for other documents.
    - L, seed 09: `을 고를 도를 도를 …` and single-syllable loops (`로 로 로`, `은 은 은`, `을 을 을`).
    - L, seed 10: whitespace only. L, seed 08: 2/20 contain `고 고 고`.
  - F's "60/60 nonempty" is an artifact of `.strip()`. A single stray character such as `남` followed by whitespace passes. The `nonempty` metric cannot separate "the decoder produced a summary" from "the decoder produced anything". The prereg §7 listed cap-hit, repeated-4gram and char F1, but only text, `gen_len` and EOS were recorded.
  - **Underfit.** Train CE last-10 is 6.26–7.35 and val real CE is 6.5–7.2 (aligned). That is unigram-LM level. Stage A (`C5_MT5_LAYER_PROBE`) had the same level, with layer19 val CE 6.62. The decoder never learned to end sequences (EOS is the last label token in every training example), so 100 batch-1 updates over 20 documents (5 passes) is not learning generation.
  - **Dropout confound.** L's train CE last-10 is higher than F's in all three seeds (7.29 / 7.31 / 7.35 against 6.26 / 6.86 / 6.62), consistent with train-mode noise rather than a capacity benefit. LoRA's own contribution is tiny at LR 1e-4 for 100 steps with B initialised to zero, so most of the F/L difference is plausibly not LoRA at all. I cannot prove that from the artifacts, but nothing in them supports attributing it to LoRA.
  - ④ "decoder adaptation itself failed" is not supported: the arms were not trained long enough to produce a valid decoder in either condition.
- **Does it make the CE results uninterpretable?** Yes for the purpose of any LoRA claim. The generation failure shows the decoder is in a regime where memory is not used, which is what the near-zero real-vs-wrong gap shows. The L-vs-F difference is further confounded by train-mode dropout and possibly by the CE shift. The collapse is also a genuine, separate finding: under this exact training config (train-mode base, 100 steps, LR 1e-4), nothing generates. It is not specific to LoRA.
- **Next steps:**
  1. Recompute the generation summary offline from the saved texts (no model run needed) with non-whitespace-token count, longest-run repetition, and cap-hit rate, and replace `nonempty` in the report.
  2. Treat "no EOS in 120/120" as a training-length defect and require, in the next prereg, a pre-set minimum EOS emission rate for P as part of the instrument-validity gate.
  3. Do not attribute the F/L generation difference to LoRA until train-mode is matched.

### Q5. What B0-A permits us to conclude
- **Verdict: agree** with the request's §6, with one tightening.
- **Evidence and classification:**
  - **Allowed:** "underpowered, instrument-unvalidated inconclusive". Precisely: in a 20-document, 100-update, unigram-level regime, with unmatched train-mode and an unvalidated metric, neither arm shows detectable content selectivity.
  - **Not allowed: "no signal".** The CI upper bounds (+0.051 F, +0.067 L, +0.079 L−F) all include the preregistered effect size, and the instrument was never calibrated.
  - **Not allowed: "LoRA unstable".** The collapse is common to both arms, and the only arm-specific difference is confounded with dropout.
  - **Not allowed:** any statement about layer19, about the frozen decoder being the bottleneck, or about comparison to A1.
- **Next steps:**
  1. Keep the §6.2 "not established" list in the record verbatim.
  2. Add "F and L differ in train-mode" to the list of confounds and to the report.

### Q6. Next experiment
- **Verdict: conditional.** I recommend a refined version of **option D**: P and M first, preceded by zero-training fixes, with F/L deferred until the instrument is validated.
- **Evidence and reasoning:**
  - **A (repair B0-A, same scale):** disagree. Repeating 20/20/100 is underpowered by construction (MDE ≈ 0.07–0.10 against a 0.05 threshold), and the request correctly prohibits it. Tuning steps or LR after seeing the result also needs a new prereg.
  - **B (full 4-arm B0-B immediately):** the sizes are reasonable, but it spends about half the compute on F and L before knowing whether the metric can detect anything. It is acceptable only after the Must-fix items in Q8 are closed. Even then I would order the runs so P and M come first, with an explicit stop rule.
  - **C (stop now):** disagree. B0-A is not evidence against the bridge. It shows the instrument was not ready.
  - **D (P + M only):** this is the minimal informative step. The important refinement is that it must run at a scale where learning can occur (about 300 train documents and about 900 updates), not at 20/20/100. At 100 updates even a native encoder would likely look like B0-A, so D at B0-A scale would not discriminate.
- **Proposed stop conditions** (to be fixed in a new prereg before anything runs):
  1. If P is not valid under the corrected metric (document-cluster CI lower ≤ 0, or P's real CE not better than M's by a preregistered margin), stop the mT5 decoder-adaptation screening track as currently instrumented, without drawing a bridge-wide conclusion.
  2. If M (a null) shows a significant positive Δshuffled_copy, the metric has a leak (length, crop or mask artifact). Stop and audit.
  3. A technical failure is retried once, per the existing prereg rule.
  4. If seed 20261108 of P fails catastrophically (non-finite, or no EOS and no CE improvement over M), do not run the other seeds.
- **Next steps:**
  1. Do the zero-training fixes first (Q8 items 1–2), then write prereg v0.2.
  2. Run P and M (seed 20261108 first), then decide on F/L in a separate decision record.
  3. Keep exploratory bridge results separate from the A1 native fallback.

### Q7. B0-B design (300/95, F/L/P/M, 3 seeds, ~900 updates)
- **Verdict: conditional.** The sizes are about right. The arm definitions and the DoD need tightening.
- **Evidence:**
  - **Sample size.** With the observed document SD, 95 validation documents give SE ≈ 0.0116 (L) and ≈ 0.0164 (L−F). That is an MDE of about 0.033 and 0.046, so it can detect the 0.05 threshold with reasonable power. The SD was measured in an unlearned regime, so treat this as a rough guide.
  - **900 updates at batch 1** is about three passes over 300 documents. That may still leave the decoder near the unigram regime. This is why P must gate the interpretation.
  - **Proposed P definition:** native mT5-small encoder applied to the passage text with the mT5 tokenizer (same source cap, or a documented smaller cap), encoder frozen, no adapter, and the same decoder LoRA, optimiser, LR, steps, order, seeds and train-mode as L. The only difference from L is the memory source. Shuffled-donor memory must use the same donor assignment, with the crop `K` defined on mT5 source length, and length matching done on that length.
  - **Proposed M definition:** a null with the same architecture as L and a decoupled memory:
    - **M_null (primary):** the adapter and LoRA are trained with donor-permuted memory (each training step pairs a target with a different document's memory, fixed derangement). Evaluation is unchanged. This gives a real, trained null for `Δshuffled_copy`.
    - **M_mean (secondary, eval-only):** replace memory with the train-mean memory vector, broadcast to length `K`, and report `Δmean_memory`. This is exploratory, like `Δzero`, which stays diagnostic because it is out of distribution.
  - **DoD additions (all fixed before any run):**
    - All arms share an identical dropout/train-mode policy (either base dropout off in every arm, or on in every arm). Assert it.
    - The metric unit test passes (Q8 item 1).
    - An instrument-validity gate is evaluated on P and M before F/L are read: P's corrected `Δshuffled_copy` has CI lower > 0, M's CI includes 0, and P's real CE is below M's by a preregistered margin.
    - The generation report includes cap-hit rate, EOS rate, repeated-4gram, longest run and non-whitespace length, not `nonempty`.
    - The L−F inference uses a two-way (documents × seeds) interval or at least 5 seeds.
  - The existing PASS/STOP rules are reasonable because they are relative to P. "real<memfree" is ambiguous and should be restated as a paired CI against M_null.
- **Next steps:**
  1. Write these definitions into prereg v0.2 with a git commit before running.
  2. Specify the margins and CI conventions in that document, not after the run.

### Q8. Must-fix before any next experiment (ranked)
- **Verdict: agree** with the need for a ranked list. Mine:

1. **Verify and fix the per-token CE alignment.** Add an automated test that the mean of the per-token CE vector equals `out.loss` for several documents (forward only). If it fails, fix the shift, and recompute nothing retroactively. Treat the B0-A `real_ce_copy` and `Δshuffled_copy` values as as-run, possibly misaligned. Evidence: 14 of 120 rows violate an inequality that aligned CE must satisfy.
2. **Match train-mode across arms.** F and L must share dropout/train-mode. Evidence: step-0 CE gap of +10.0 / +10.5 / +12.1 nats at identical weights.
3. **Add P and M_null and an instrument-validity gate** that is decided before F/L are interpreted, and run at a scale where learning can occur (not 20/100).
4. **Re-specify the copyable mask a priori**, using only the source and target text and train-split statistics, never Δ outcomes. At 0.8246 coverage the current mask (spaces stripped, single syllables allowed) is almost "all tokens". Candidate rules: minimum piece length of 2 or more syllables, or digits and names only, or exclude the top-frequency particles by train-target frequency. Keep the as-run mask as a labelled secondary. Add an upper-coverage warning, since the guard only protects against low coverage. This is a metric redefinition and requires a new preregistration. It must not be framed as a threshold change after seeing B0-A.
5. **Complete the prereg's reporting and inference.** Record the generation fields §7 promised (cap-hit, repeated-4gram, EOS rate, length), replace `nonempty`, and add seed-level inference (two-way bootstrap or ≥ 5 seeds). Also reconcile small prereg-vs-code mismatches: the code requires 5 copy tokens where the prereg says 20, which is immaterial since the minimum observed was 121.

### Q9. The 100-step / 20-document problem
- **Verdict: agree** that the extension must be forbidden. A numeric minimum is conditional.
- **Evidence:**
  - B0-A was in an untrained regime for both arms (EOS never emitted, CE near unigram), had about 30–50% power at the preregistered effect, and had unmatched arms. A statement such as "decoder LoRA has no effect" is unsupported by it, whatever follows.
  - **Documents.** From the observed SD, detecting an L−F difference of 0.05 with 80% power needs roughly 80 validation documents (n ≈ (2.8 × 0.16 / 0.05)²). That is the floor, and 95 is consistent with it. For training, 300 documents is already available in the split.
  - **Updates.** I cannot give a trustworthy fixed number, because the right number depends on when P stops looking like M. A fixed step count chosen after B0-A would also be a post-hoc choice. Use ~900 updates as the planned length (as in the prereg) and let the P-vs-M validity gate decide whether the regime is informative. If P fails at that length, record that no longer run is approved without a new decision.
  - Seeds: 3 is the floor; 5 is preferable or use a two-way CI.
- **Next steps:**
  1. Record the prohibition in the B0-A report: "B0-A does not support any statement about decoder LoRA efficacy".
  2. Put the validity gate, not a step count, in the prereg as the criterion for whether an F/L comparison is read.

### Q10. Role probing
- **Verdict: agree** with keeping it deferred (conditional on P).
- **Evidence:** B0-A cannot change the priority of role probing. Probing which layer plays which role presupposes an instrument that can detect memory use. P and M are exactly what would show whether it can. Running a probe survey on an unvalidated metric would compound the problem. B0-A also fixed layer19 as an anchor, so it provides no layer-level information.
- **Next steps:**
  1. Keep role probing deferred until P is valid under the corrected metric.
  2. Revisit it only in a separate decision record after B0-B, as the earlier review required.

### Q11. Metric audit
- **Verdict: conditional.** Do the mechanical audit before B0-B, and defer the preservation and entity audit.
- **Evidence:**
  - **Before B0-B (required):** the alignment test, the mask audit (coverage distribution, and a text-only check of which pieces are copyable), and the train-mode assertion. These are the Must-fix items and need no model training.
  - **Before Stage C or B2 (not before B0-B):** the preservation and entity audit. These matter for a product claim, and B0-B is a diagnostic about whether memory content is used.
  - **Keeping `Δshuffled_copy` as primary:** acceptable, but only after Must-fix 1 and 4 and with a new prereg. Also report aligned `Δshuffled_full` as a co-primary sanity check, because it does not depend on the mask. The two should agree in sign. Add a digits-and-names subset as exploratory. Note that a copy-based metric tests selectivity for copyable content, not abstractive content use.
  - `Δzero` stays diagnostic only.
- **Next steps:**
  1. Run the mechanical audit as a no-training task and publish the result before the prereg is frozen.
  2. Keep the preservation and entity audit on the Stage C/B2 gate list.

### Q12. Final verdict
- **Verdict: NARROW.**
- **Evidence:** B0-A is a valid shakedown with a correct INCONCLUSIVE label. It is not evidence for or against the bridge, and the instrument has several fixable defects. Stopping would be premature, since nothing has been tested at a scale or with controls that could fail the bridge. Continuing as planned would spend compute on an unvalidated instrument.
- **Allowed experiments:**
  - Zero-training work: the CE alignment test, the train-mode match, the mask audit (text only), offline recomputation of generation statistics from saved texts, and prereg v0.2.
  - After prereg v0.2 is committed and approved: P and M_null at about 300/95 and about 900 updates, seed 20261108 first, then the remaining seeds if the early-stop rule allows.
  - F and L at the same scale only after the validity gate passes, under a separate decision record. If everything is approved together, the schedule must still run P and M first with the stop rule.
- **Forbidden experiments:** rerunning B0-A at 20/20/100 or with changed LR, steps, seeds or donors to chase the threshold; B1, B2 and Stage C; any role-probing survey; comparison with A1; any use of test 163 or P1 data; any reopening of T5Gemma2 without a new decision record.
- **Maximum compute:** CPU only, within the prereg's own B0-B budget (6–10 CPU-hours). P and M should be roughly half of that, so F/L would use the remainder. No additional compute without a new decision.
- **Next decision gate:** a decision record after P/M, deciding on F/L, with the validity gate pre-specified. Do not treat any gate change as already approved. This review proposes none. Any changed definition needs a new preregistration written before the run.
- **Test 163:** remains sealed.
- **Separation:** exploratory mT5 bridge results stay distinct from the A1 native fallback, and are not a basis for product or fallback decisions.

---

## 3. Top Must-fix items (ranked)

1. Verify and fix per-token CE alignment (`logits[:, :-1]` vs `labels[:, 1:]`) with an `out.loss`-equality unit test.
2. Match train-mode and dropout across all arms. Assert it.
3. Add P and M_null with a pre-set instrument-validity gate, at a scale where learning can happen.
4. Re-specify the copyable mask a priori (coverage 0.8246 is near-vacuous), in a new preregistration, without using Δ outcomes.
5. Complete the generation reporting (cap-hit, EOS rate, repetition, length), drop `nonempty`, and add seed-level inference.

## 4. Premises in the request that I would correct

1. "LoRA arm's generation collapsed" implies a LoRA-specific failure. Both arms are degenerate (120/120 generations hit the cap, 0 EOS).
2. "F and L are matched" is not true. They differ in dropout/train-mode, and the step-0 CE gap shows the effect is large.
3. "Copy guard passed, so the mask is valid" overstates what the guard checks. It only guards against low coverage, and 0.8246 coverage is suspiciously high.
4. "Positive seeds 2/3" is presented as evidence. With three seeds it is nearly uninformative.
5. NO_SIGNAL is listed as an outcome, but with a mean ≤ 0 requirement it was almost unreachable for any small positive mean.
6. The per-token CE implementation is treated as validated by a smoke test that only checked that the code ran.

## 5. Limits of this review

- I did not run training, evaluation or any model forward, so the CE-alignment concern is based on code reading and internal consistency of the saved JSONs, and must be confirmed by the maintainers' unit test.
- My statistics were computed from the saved per-document values with standard-library Python, in memory. Power figures use the observed SD from an untrained regime and are rough.
- The E0 audit numbers and the mT5 wiring and LoRA inventory results are taken from the request and not independently re-derived.
- I make no claim that any gate change is approved. The verdict applies only to the exploratory mT5 track, not to the A1 native fallback.