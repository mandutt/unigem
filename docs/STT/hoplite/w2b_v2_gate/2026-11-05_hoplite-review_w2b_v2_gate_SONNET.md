# Hoplite review — w2b_v2_gate (reviewer: Claude Sonnet 5.5)

- Workspace sync: `git fetch origin` OK; `git pull --ff-only origin main` → "Already up to date". HEAD = `ac1fd82ee32212ce99517e3986a5b43f69a0addc`. The request cites base commit `9d1aba6`, which does **not exist** in this clone (shallow). I could not check anything against that hash.
- Read: all 769 lines of `docs/STT/reports/EXTERNAL_REVIEW_W2B_V2_GATE_2026-11-05.md` (the file has 769 lines, not 768). I read it in chunks of at most about 90 lines.
- I ran **no experiments** and modified no repo files. The only code I ran was two read-only Python checks on committed files (`vocab_v2.json`, `short_4h_v2.jsonl`, `testpred_*_v2_s42.json`). They are reported below as **reviewer ad-hoc checks, not project results**. The Wave 1 manifest is not in the clone, so I could not check the Wave 1 side.

## 0. Verdict

**B — recipe-level PASS with caveats.** The gate is met as pre-registered (CER improves ~10 pp, CI far from 0). The estimand is "this recipe, 6h Wave-1 → 10h incl. Kspon-short, 12 epochs". Do not call it a data, short-length or domain effect. Do not promote it to a claim about speaker-independent generalization.

I do not recommend C (downgrade to exploratory). Nothing in the document reverses the sign or the gate. The gap is ~10 pp against a 1.0 pp threshold, with CI [9.2, 10.3]. The confounds change the *attribution* of the gain, not its existence at the recipe level.

Arithmetic check: I recomputed every table figure I could (errors/chars → CER, steps, exposure, bin counts, Δs, FLEURS). All are internally consistent. One discrepancy is listed under Q8: OOV-table denominators versus CER denominators.

## 1. Q1–Q8

### Q1 — Gate PASS status
1. **Judgment: B** (recipe-level PASS, caveats attached). Do not use the bare label "gate PASS".
2. **Evidence:**
   - Dev Δ = +10.187 pp, CI [9.107, 11.328]. Test Δ = +9.737 pp, CI [9.228, 10.258]. FLEURS dev −0.216 pp. All were frozen/selected before test and test was used once.
   - The comparator B0′ has *zero* Kspon audio, and the test set is Kspon eval_clean. The gate therefore mostly measures "adding in-domain training data and compute helps in-domain eval". That is a weak, nearly expected result. The 1.0 pp threshold was cheap to clear. The gate is valid but low-information about the *short-clip* hypothesis that motivated 2C-short.
   - FLEURS gain (−0.216 pp CER, i.e. 1,649 → 1,632 errors) has no CI reported and is not distinguishable from zero on the evidence given. It supports "no regression", not "transfer".
   - Both arms are probably under-trained. B0′ and B3 both peak at epoch 12 with no early stop (B3 dev still falling: 0.2696 → 0.2682). The comparison is at a fixed, truncated budget, not at convergence.
   - Test refs overlap train short refs at text level (see Q5/Q8). It is small in effect, but clip-ID overlap = 0 does not cover it.
3. **Required action:**
   - Record D-071 as "recipe-level PASS (pre-registered gate), estimand = 12-epoch, 10h-incl-Kspon-short recipe vs 6h Wave-1 recipe".
   - Add the caveat set (domain, compute, length, in-domain holdout, text overlap) to the gate report itself.
   - No re-running is needed.
4. **Blocks LoRA/next step: No.**

### Q2 — Causal attribution / controls
1. **Judgment: B.** Restricting the estimand to "this recipe" is justified. Anything finer needs controls that do not exist yet.
2. **Evidence (including one point the document does not make):**
   - Steps and audio exposure are **not interchangeable here**. B3 has 3.13× steps and 1.67× audio-hours because its clips are short: 11,196 / 120.3 h ≈ 93 steps per exposure-hour versus 3,576 / 72 h ≈ 50. A "step-matched" control and an "exposure-matched" control are therefore *different* experiments, and the document treats them as one confound.
   - **B0′-20 epochs gives 5,960 steps / 120.0 h, i.e. exposure-matched to B3-12 (120.3 h).** The document only frames 20-epoch as a convergence check. It *is* the exposure control, just not the step control. It is also, by construction, step-mismatched by 1.9×.
   - B3 epoch 4 (3,732 steps, 0.2903 dev CER) versus B0′-12 (3,576 steps, 0.3701) is the best existing hint. It is a diagnostic only. The checkpoint was not kept, the LR differs under the 12-epoch cosine schedule, and exposure is 40 h versus 72 h. Gap: +7.98 pp.
   - That same data point cuts against "compute explains it all", but it cannot separate Kspon domain from short length.
3. **Required action (priority, with interpretation limits):**
   - (a) **B0′-38 epochs** (step-matched, ~3 h CPU). It answers "is the gain just more updates?". Limit: B0′ then sees 228 h of the same 2,384 clips, so overfitting may make it a weak control. Report the full epoch curve, not only `best.pt`.
   - (b) **B0′-20 epochs** (exposure-matched). Cheap, and also supplies the 20-epoch cell of D-070.
   - (c) **Domain/length decomposition:** a Kspon *natural-length* (or long-clip) 4h arm, with the same V2 vocab. This is the only control that tests the "short" claim. A non-Kspon short control is lower priority, since Wave 1 is already mostly short Zeroth/Kconf and no suitable data is named.
   - (d) B3 epoch-4 re-run with the real schedule (cheap but only supporting).
   - Until (a)–(c) exist, do not use "data effect", "short-clip effect" or "domain effect". "Recipe effect" is the only supported label.
4. **Blocks LoRA: Partly.** (a) and (b) should finish before LoRA is interpreted. They do not block LoRA *implementation*, GPU packaging or smoke tests.

### Q3 — V2 vocabulary two-pass loop
1. **Judgment: B** (keep V2, label results as conditioned on it; no rebuild).
2. **Evidence:**
   - No eval/test text was used. The draft vocab (2,342) came from train transcripts and was not used for training. The loop is not a leakage path.
   - The loop can bias *which short clips are eligible* (clips whose chars are in a vocab derived from earlier-selected clips). Re-selection moved the set only slightly: 5,066 → 5,079 clips, 4.0035 → 4.0016 h. This favours "small effect".
   - Both arms share one vocab. OOV is arm-neutral. The **asymmetry** that matters is the 228 new characters: B0′'s head rows for them are freshly initialised and B0′ has seen (presumably) none of them. I checked this on the test predictions. **Reviewer ad-hoc check:** 114 of 2,400 test refs contain a char at vocab index ≥1101, covering ~122 chars out of 38,224 (~0.3%). On those utterances B0′ CER = 0.397 versus B3 0.284 (Δ ≈ 11 pp, close to the overall Δ). So the new-char asymmetry cannot explain the headline. Caveat: I assumed the new 228 chars are `chars[1101:]`. The list shows `.`, `?`, `,`, `/` at indices 1101–1104, so the boundary may be off by a few indices. The conclusion (≤~0.3% of chars) is robust to that.
   - In the short subset, 143 of those 228 chars occur at all and the median occurrence count is 1. The new characters are essentially unlearnable. They add vocab size but contribute almost nothing to the effect.
3. **Required action:**
   - Keep `vocab_v2.json` frozen (hash it in `test_freeze.json` or a new provenance entry). Never rebuild it after seeing any further results.
   - Label results "conditioned on V2 vocab (selection-dependent)".
   - For *new* arms (long-clip control), select with the **already fixed V2** and do not iterate. If the long-clip arm needs chars outside V2, drop those clips rather than extending the vocab.
   - Optional: report a char-occurrence histogram for the 228 new chars.
4. **Blocks LoRA: No.**

### Q4 — B3-nat / sampler
1. **Judgment: B.** "No *detectable* sampler effect at dev-500" is supportable. "No sampler effect" or "sampler-invariant" is not.
2. **Evidence:**
   - B3 − B3-nat = +0.490 pp, CI [−0.229, +1.205] (note sign convention: positive means B3-nat is better). The CI extends to ~1.2 pp, which is about the same size as the pre-registered effect threshold. The test is under-powered to rule out a gate-sized sampler difference. Absence of significance ≠ equivalence.
   - Single seed (42), dev 500 (7,755 chars).
   - B3-nat best epoch 11 (0.2633) versus final epoch 12 (0.2634): a 0.0001 difference, immaterial. B3 best = final = 12. Both used `.best.pt` selected on the same dev set that reports the number. This is mild dev-selection optimism that is *symmetric* across arms, and negligible given checkpoint closeness.
   - The point estimate favours the *natural* sampler. Frozen B3 was balanced. The pre-registered choice of the candidate was not wrong, but B3-nat is an unevaluated alternative that is nominally better.
3. **Required action:** Do **not** evaluate B3-nat on the used test. Doing so adds no confirmatory value and consumes the holdout further. Report the dev-only result as "not distinguishable at dev-500, single seed". Use seed 43 on dev (the cheap path) if sampler choice matters for later arms. Decide the sampler for LoRA by pre-registered rule, not by the test.
4. **Blocks LoRA: No** (but fix the LoRA sampler a priori).

### Q5 — Test reuse / confirmatory status
1. **Judgment: B.** The first test use is confirmatory for exactly one frozen comparison (B0′ vs B3-12, seed 42). Every later evaluation on this 2,400 is exploratory.
2. **Evidence:**
   - The document states the test is an in-domain procedural holdout, not speaker-independent. Speaker IDs are unavailable and filenames were shuffled by the corpus authors. Speaker, session and script overlap with Kspon train is **unverifiable**. For Kspon, where utterances from the same speaker and session are numerous, this is a substantive risk to "holdout". Clip-ID overlap = 0 is the weakest overlap criterion.
   - **Reviewer ad-hoc check (text-level overlap, short-train refs only):** 136 of 2,400 test refs (5.7%) match a short-train ref exactly after stripping whitespace and punctuation (my own normalisation, not `normalize_nospace`). On those 136 (445 chars), B0′ CER = 0.584 versus B3 0.265. Excluding them gives non-duplicate CERs of B0′ 0.357 and B3 0.262, Δ ≈ **9.48 pp** (against 9.74 pp overall). So duplicates contribute ~0.26–0.37 pp, which is not material. But this overlap was not reported or audited. Overlap against the *full* Kspon train transcripts (620,000) was not checked and could be larger, but only the short subset reaches B3.
   - The only claim this test can still support is the existing one, plus descriptive statistics.
3. **Required action:**
   - Declare in D-071 and all text that test is "in-domain procedural holdout, used once; later results exploratory".
   - Add a text-overlap audit (exact match plus near-duplicate) to `overlap_final.json`, and report the Δ with duplicates removed as a sensitivity analysis (my number above should be reproduced by the owners with the project's normaliser).
   - For any *new* confirmatory claim (LoRA, new recipe), the minimum is a **fresh holdout** not previously evaluated. FLEURS test is an acceptable cross-domain confirmatory set but does not substitute for Kspon in-domain evidence. spare-90 (≈0.077 h, ≤~1,500 chars) is far too small for a gate (paired CI would be wide, ~±3 pp). Use it only as a smoke/consistency check. A new Kspon holdout carved from eval_other, with a speaker/session split if any metadata exists, is the best option.
4. **Blocks LoRA: Yes for any LoRA *confirmatory* claim** (a fresh holdout is needed before the LoRA gate). It does not block building LoRA.

### Q6 — Next priority
1. **Judgment: B.** Do step/exposure controls first, then seed, then LoRA. The 3-arm 20-epoch plan is not a priority as designed.
2. **Evidence:**
   - A 20-epoch 3-arm run preserves the 3.13× step / 1.67× exposure ratios (document §4.2). It answers "does more training help each arm", not attribution. It costs ~7–8 h CPU.
   - B0′-38 (~3 h) answers the step question directly, and B0′-20 answers the exposure question. B0′-20 is one arm of the 3-arm plan, so a trimmed plan (B0′-20 plus B0′-38 only) gets the attribution answer for less than the full 3-arm plan.
   - Single seed throughout. Seed variance is unmeasured. The 10 pp gap is probably well above seed noise, but the 0.49 pp sampler gap is not.
3. **Required action (ordered):**
   1. **B0′-38** (step-matched), report the full epoch curve. About 3 h.
   2. **B0′-20** (exposure-matched; doubles as D-070 arm).
   3. **Seed 43 for B0′ and B3 (12 epochs), dev only.** Gives a noise floor for Q4 and the control comparisons.
   4. **Kspon natural-length 4h control** (needs data prep with fixed V2).
   5. LoRA B1/B2.
   - Drop B3-20 and B3-nat-20 unless 1–3 show B0′ closing the gap. They are only informative if so.
   - Pre-register the interpretation before running: if B0′-38 reaches ≥ B3-12 − 1 pp on dev, "recipe gain is mostly compute"; if it stays ≥ 5 pp behind, "data/domain matters beyond compute". Give a stop rule so the outcome does not get re-read after the fact.
4. **Blocks LoRA: items 1–2 should precede LoRA *interpretation*; seed 43 can run in parallel with LoRA engineering.**

### Q7 — LoRA readiness
1. **Judgment: B** (may start implementation and GPU smoke now; do not start the pre-registered LoRA gate runs until the prerequisites below are done).
2. **Evidence:**
   - LoRA is unimplemented, with no sec/step, memory or preemption data and no GPU packaging. MF-6 is only partly met.
   - The reader-only baseline has not been attributed (Q2), so a LoRA delta cannot be compared properly: B1/B2 should be compared against a compute-matched reader-only B3, otherwise LoRA's extra compute and capacity are confounded just as B3's were.
   - A ~10 pp reader-only gain on Kspon sets a high bar for visible LoRA gains. The *expected* LoRA gain is not estimated anywhere in the document ("not in document").
3. **Required action before LoRA gate runs:**
   - Finish Q6 items 1–2, and have a fresh holdout (Q5).
   - Freeze V2 vocab and sampler (Q3/Q4).
   - GPU parity check: same features/seed/schedule for a reader-only arm run on GPU versus CPU (otherwise LoRA-vs-reader differences include hardware nondeterminism).
   - Pre-register stop/go: LoRA arm vs *B3 trained at matched steps/exposure*, Δ ≥ a stated pp (suggest ≥ 1.0 pp point estimate with paired CI lower bound > 0, on a fresh holdout), plus FLEURS no-regression ≤ 1.0 pp. Stop if smoke shows cost per gate run above a stated budget, e.g. > 2× B3 wall-clock or OOM on the chosen GPU.
4. **Blocks LoRA gate runs: Yes. Blocks implementation/smoke: No.**

### Q8 — Claim scope
1. **Judgment: B.** The proposed sentence over-attributes. Correct it as below.
2. **Evidence (problems in the proposed sentence):**
   - "Kspon short-domain 4 hours" bundles domain and length. Neither is isolated.
   - "dev +10.19 pp, test +9.74 pp" omits that dev and test are both Kspon eval_clean, from the same corpus as the training addition, and that B3 got 1.67× audio exposure and 3.13× steps.
   - "sealed test" is inaccurate if read as independent. It is an in-domain holdout, used once, with unverifiable speaker/session overlap and some text overlap.
   - Document inconsistency: OOV table denominators (dev 8,247, test 40,788, spare 1,473 chars) differ from the CER denominators (7,755, 38,224). The likely cause is raw versus normalised refs (the dev/test OOV tables seem to use unnormalised text including whitespace/punctuation). The document does not say so. **CER numbers (7,755 / 38,224) are the ones the gate uses; 0.1299% is a raw-text rate and should be described as such.** Also the request says 768 lines; the file has 769.
   - Label: use **"recipe effect"**. "Data effect", "domain effect" and "short-length effect" are all unsupported.
   - I agree "speaker-independent", "generalization" and "state-of-the-art" must be avoided. The FLEURS result supports "no regression on FLEURS dev" only.
3. **Required action:** adopt the revised sentence in §4; add the caveat list to any publication; reconcile the OOV/CER denominators in the report.
4. **Blocks LoRA: No.**

## 2. Must-fix table

| ID | Finding | Action | Priority | Blocks LoRA? |
|---|---|---|---|---|
| MF-A | Compute/exposure confound: step-matched and exposure-matched controls are different and neither exists | Run B0′-38 (step) and B0′-20 (exposure), with full epoch curves and a pre-registered interpretation rule | P0 | Blocks LoRA *interpretation*, not implementation |
| MF-B | Domain/length confound: no Kspon natural-length or non-Kspon short control | Build a Kspon natural-length 4h arm using fixed V2 (no vocab rebuild). Until then, forbid "short-clip/domain/data effect" wording | P1 | No (blocks wording only) |
| MF-C | Test is used once, speaker/session overlap unverifiable, and text-level overlap was never audited. My ad-hoc check found 136/2,400 exact short-train text matches (Δ ~9.48 pp without them) | Add text overlap audit with the project's normaliser and report Δ without duplicates. Obtain a fresh holdout (new Kspon split or FLEURS test) for any later confirmatory claim | P0 | Yes for confirmatory LoRA claims |
| MF-D | B3-nat is dev-only, single seed, CI up to +1.2 pp; "no sampler effect" is unsupported | Reword to "not distinguishable at dev-500, one seed". Do not run B3-nat on used test. Seed 43 on dev if the sampler matters | P2 | No |
| MF-E | V2 vocab 2-pass loop; the 228 new chars are mostly unlearnable (median 1 occurrence in short refs) | Keep V2 and freeze with a hash. Label results "conditioned on V2". No rebuild | P2 | No |
| MF-F | Seed variance unmeasured (single seed 42) | Seed 43 for B0′ and B3 on dev, 12 epochs | P1 | No, but run before LoRA gates |
| MF-G | D-070 3-arm 20-epoch preserves the 3.13× / 1.67× ratios and is not an attribution experiment | Reduce to B0′-20 (exposure control). Run B3-20 only if the controls show B0′ closing the gap | P2 | No |
| MF-H | LoRA gate has no pre-registered stop/go, no GPU parity, no compute-matched comparator | Pre-register LoRA vs matched-compute B3 on a fresh holdout; GPU/CPU parity check; cost stop rule | P1 | **Yes** for gate runs |
| MF-I | Report inconsistencies: OOV-table vs CER denominators; 768 vs 769 lines; cited commit `9d1aba6` absent in clone; FLEURS Δ has no CI | Fix the report, add FLEURS paired CI, state the commit hash in an accessible ref | P3 | No |

## 3. Experiment priority

1. **B0′-38 epochs** (step-matched control, full curve, ~3 h CPU) and **B0′-20 epochs** (exposure-matched). Together they settle the largest attribution gap cheaply.
2. **Seed 43 (B0′, B3), dev only.** Establishes a noise floor. Can run in parallel with LoRA engineering.
3. **Kspon natural-length 4h control** (fixed V2), then **LoRA B1/B2** (GPU smoke and cost measurement can start earlier). Skip B3-20/B3-nat-20 unless controls make them informative.

## 4. Proposed external claim (revised)

> "In a reader-only pilot (frozen EG2 audio tower, 4-layer CTC reader), a recipe that adds ~4 h of short Kspon clips (6 h → 10 h total, 12 epochs, with 3.13× more optimizer steps and 1.67× more audio exposure than the 6 h baseline) reduced character error rate on a Kspon in-domain, non-speaker-verified holdout by 9.7 pp (95% CI 9.2–10.3; 26.2% vs 36.0%) and on dev-500 by 10.2 pp, and did not degrade FLEURS-dev CER (−0.2 pp). This meets our pre-registered gate for this recipe. The effect cannot yet be attributed to data volume, Kspon domain, short-clip length, or training compute individually; results are single-seed, the holdout was used once and shares corpus, and possibly speakers/sessions and some text, with training data."

## 5. Uncertainties

- I could not check anything against commit `9d1aba6` (absent in this clone); reviewed HEAD `ac1fd82`.
- Wave 1 manifest, full Kspon train transcripts, and any speaker/session metadata were not available to me, so Wave-1-side overlap and full-train text overlap are unchecked.
- My ad-hoc numbers (136 duplicates, 114 utterances with new chars) use my own normalisation and an assumed new-char boundary (`chars[1101:]`). They are indicative, not authoritative, and should be rechecked with project tooling.
- I do not know whether the Kspon corpus's own splits make speaker leakage likely. I flagged it as an unverifiable risk, not a finding.
- The document offers no estimate of LoRA's expected gain or cost, so my LoRA stop/go suggestions are placeholders for the owners to calibrate.
- Seed variance is unknown; I judged the 10 pp gap to exceed it, but that is a judgment, not a measured fact.
- Because the tool output was condensed on some reads, I re-read the file in small chunks. I believe I read every line, but some chunk content was rendered in condensed form by the tooling; the line numbers and section headers matched the file's `grep -n '^#'` index.
