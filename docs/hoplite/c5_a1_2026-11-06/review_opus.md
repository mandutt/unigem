# Independent review: F5 A1 T5Gemma2 LoRA and EG2→T5 bridge (Opus 5.5, reasoning=medium)

- Reviewed document: `reports/EXTERNAL_REVIEW_C5_A1_2026-11-06.md` (read in full, 562 lines)
- Workspace sync: `git fetch origin` OK; `git pull --ff-only origin main` reported "Already up to date."
- Review HEAD: `834d598e2fb6c003419713156de183d377c4c335` ("docs: add A1 3-AI review prompts and dispatch")
- Files checked: `runner/c5_a1_lora.py`, `reports/C5_A1_smoke_pilot.md`, `reports/C5_A1_prompt_diagnosis.md`, `reports/C5_A1_val161_2026-11-06.md`, `reports/C5_A1_exa_diagnosis_2026-11-06.md`, `reports/C5_T5Gemma2_paper_notes_2026-11-06.md`, `reports/C5_EG2_T5_bridge_literature_2026-11-06.md`, `docs/plan_c5_abstractive_v0_1.md`, `docs/decisions.md` (D-027, D-042, D-080–D-082), `docs/gates.md` (H4′), `reports/provenance/C5_a1/pilot300_val161/{metrics.json,predictions.jsonl}`, `reports/provenance/C5_clean/{a0_val161.predictions.jsonl,target_slot_audit.json}`.
- My own recomputations from committed artifacts are marked **[recomputed]**. I ran no training, no generation and nothing on test 163.

---

## 1. Verdict

**Start A1 full train now.** Treat it as a pre-registered experiment, not a product decision. Two cheap document fixes come first (Must-fix 1–3). Run the B family only after the full train, beginning with a B1d feasibility probe and not with B3.

---

## 2. Decisions D1–D6

### D1. Approve A1 full train
- **Recommendation:** Approve 2 epochs (2,586 steps at batch 1, about 3 h). Save checkpoints and evaluate them at fixed steps (650 / 1,293 / 1,940 / 2,586). Pre-register the selection rule. Make no 3rd epoch unless the val curve is still rising at step 2,586.
- **Rationale:** The pilot is cheap to extend and the downside is small: about 3 h of CPU, with a 13 GB limit against 2.45 GB RSS. The val161 signal is not marginal. The paired CI lower bound is +0.034, A1 wins 112/161, and the minimum per-document A1 char F1 is 0.432 **[recomputed]**, so no case collapsed. The result holds on the 156 documents that were not used for tuning (0.6586). Extending the pilot would cost the same CPU as a full train and give less information. The real open questions (convergence, overfitting, human acceptability) can only be answered by the full train plus human review.
- **What would change it:** A bare-prefix val161 run that beats the prefix run by more than the CI half-width (about 0.013) would mean the input format should change first. A step-time or RSS regression would also change it.

### D2. Prefix condition for full train
- **Recommendation:** Keep the `summarize: ` prefix fixed for the primary run. Before training, run inference only on bare val161 with the existing pilot300 adapter (about 9 min). Do not add a prefix-dropout arm to this full train.
- **Rationale:** The prefix is a constant string under our control at inference time, so for an F5-only adapter "bias" is not a real risk. It is part of the adapter's input contract. The bare-vs-prefix val5 gap (0.6522 vs 0.6272) is n=5, and the outputs differ in length (264 vs 167 tokens). On val5, char F1 tracks length, so this is not evidence. Prefix dropout only matters if the adapter is meant to be reused across tasks, and the request already says adapters are per task.
- **What would change it:** Bare val161 ≥ prefix val161 + about 0.015 with equal grounding and EOS. Then train bare, which keeps the input contract simpler.

### D3. EG2→T5 bridge priority
- **Recommendation:** Do the A1 full train first. Then run a **B1d feasibility probe** (feature substitution plus teacher-forced NLL, §4), not B3. Defer B3 or redesign it with a shuffled-EG2 control.
- **Rationale:** B3 as specified prepends soft tokens to the **full passage embeddings**. The frozen encoder therefore already has all the text, and B3 measures input-conditioned prompt tuning of a frozen 270M model. Small-model prompt tuning is known to be weak, and frozen zero-shot is 0.233 with 1.86% EOS. B3 does not measure whether the decoder can read EG2. Either way the result is uninterpretable without a "same adapter, shuffled/constant EG2" arm.
- **What would change it:** If the product requirement is "summarize from stored EG2 states when the passage text is absent", only bridges with no passage text count, and B3 drops out entirely. If the bridge is only meant to add features alongside the text, B3 with a shuffled control becomes acceptable.

### D4. Close A2 without raw-vs-seq control
- **Recommendation:** Yes, close A2 as a product candidate now. Record the raw-vs-seq control as an open exploratory item. Do not spend CPU on it.
- **Rationale:** A2 is 0.48 char F1 below A0 with grounded 0–1/161. No plausible control result could bring it near A1. The control would only explain *why* A2 failed, and B1d (§4) answers a sharper version of that question: can a frozen decoder consume an EG2-derived memory whose distribution matches the native encoder?
- **What would change it:** A B1d probe showing that the frozen decoder *can* read a distribution-matched EG2 memory. A2's failure would then be clearly about the objective or distribution rather than the frozen q/k/v/o, and the paper-based explanation would need revising.

### D5. Test 163
- **Recommendation:** Run A1 once on test, using the single checkpoint chosen by the pre-registered val rule, **after** human review on val (D6). Do not allocate test to B-family candidates until one of them beats A1 on val161 under the same contract. If that happens, the test run is a separate, single, pre-registered comparison. Never pick a winner on test.
- **Rationale:** Test is the only unbiased estimate. Val161 has already been used for prompt and lr selection (5 documents) and will be used for checkpoint selection.
- **What would change it:** Nothing short of a governance change.

### D6. Human 50
- **Recommendation:** Review after the full train, **on val, before test**. Use a stratified sample rather than a random one: the 6 slot-free documents, the lowest-char-F1 decile, the longest outputs, and the rest random. Use a written rubric that covers fabricated entities, wrong numbers or units, negation and attribution errors, critical omissions, and sentence count (3–5).
- **Rationale:** Grounding checks only numeric, date, time, identifier and URL slots (about 91% of source slots are `number` per `target_slot_audit.json` **[recomputed]**). It cannot see people or organization names, polarity, or attribution. Human review is the only fidelity check in the plan.
- **What would change it:** Nothing. Human review should come before the test run because it can veto the candidate.

---

## 3. Q1–Q12

**Q1. Is pilot300 val161 enough to start full train?**
It is enough to start the full-train experiment, but it does not support any product claim. The effect is consistent: CI [+0.034, +0.060], 112/161 wins, worst A1 document 0.432 **[recomputed]**, and the 156 untuned documents give 0.6586. Its limits are 23% of one epoch, a single seed, val also used for tuning, metrics that are mostly lexical, and no human review. One extra control I would add is free: A1 emits fewer slots than A0. There are 5.2 slots per document (837/161) and slot preservation is 0.456, against A0's 8.75 per document and 0.801 **[recomputed]**. Part of A1's grounding cleanliness may come from saying fewer numbers. Clean targets preserve 0.510 of source slots (micro, `target_slot_audit.json`), so A1 is near the target distribution and not abnormal, but report this next to grounding.

**Q2. 2 or 3 epochs; selection and early stopping?**
Start with 2 epochs. "Patience 1" with 2 epoch-level evaluations means almost nothing. Evaluate at 4 fixed step checkpoints instead, at about 9 min each for val161 generation. Pre-register this rule: among checkpoints that pass the gates (grounded ≥99%, new-slot ≤1%, EOS ≥95%), choose the one with the highest val161 char F1, breaking ties toward the earlier checkpoint. Also log teacher-forced val NLL at each checkpoint (cheap), so overfitting is visible even when char F1 is flat. Run a 3rd epoch only if the last checkpoint is the best and is still improving by more than about 0.005.

**Q3. Is the `summarize: ` prefix valid for F5; compare bare or dropout; is it separable from other tasks?**
For F5 it is valid. It is a T5 convention, the base model responds to it (pilot100 inference-only: 0.4659 → 0.6118), and it is deterministic at inference. The only comparison worth paying for is bare val161 on the existing adapter (9 min, no training). Dropout is a reuse feature, and the adapters are per task. The separation design is adequate on one condition: the adapter file must record its input contract (prefix string, max_input, special-token handling). Right now the adapter checkpoint dict stores rank, alpha and so on, **but not the prefix** (`runner/c5_a1_lora.py` `adapter = {...}`), so the contract lives only in command lines.

**Q4. B3, B1a/b, B1d or B2 first?**
B1d, run as a feasibility probe and not as a full system (see §4 for the exact test). It answers the question that matters for a general bridge, "can a frozen T5Gemma2 decoder consume an EG2-derived memory?", with little compute: train the adapter on cached features, then evaluate teacher-forced NLL. B3 is a detour because the full passage is still in the encoder input. B2 should come only after the B1d probe shows partial readability.

**Q5. Is closing A2 without raw-vs-seq justified?**
Yes, for product purposes. The −0.48 paired char F1 gap and 0–1/161 grounding are decisive, and the +0.058 shuffled ΔNLL shows only weak document-specific use of the memory. For scale, that is about 2% of the 3.12 NLL. Keep the memory-ablation result on record as "the signal exists but is weak". Do not attribute the failure *solely* to frozen merged q/k/v/o. The adapter objective (CE through a frozen decoder from an off-distribution memory) is an equally plausible cause, and the B1d probe separates the two.

**Q6. Are the metrics sufficient?**
They are not sufficient for a product decision, but they are fine for model selection. Must-have additions are cheap and local: (a) slot preservation and slots per document next to grounding (A1 0.456 vs A0 0.801), (b) sentence-count compliance with the 3–5 target, where a rough splitter puts 28/161 A1 outputs outside 3–5 against 7/161 targets **[recomputed, heuristic regex; verify]**, (c) ROUGE-L, which the plan's DoD already lists (`plan_c5_abstractive_v0_1.md` §2.7), and (d) the stratified human 50. BERTScore with a Korean encoder is optional. Latency is in the plan DoD and unmeasured, and it matters on CPU.

**Q7. How to report 6/161 slot-free documents?**
Report both numbers and never fold them together: "grounded 155/155 non-vacuous (100%); 6/161 slot-free (vacuous)". Keep the G-C5 gate denominator as all documents, as D-080 defines it, so no gate change is implied. State the non-vacuous rate as the primary evidence. Include all 6 slot-free documents in the human sample, because they are where hallucinated *non-slot* content is invisible to the verifier.

**Q8. LoRA target: keep q/k/v/o r8, or add FFN or r16?**
Keep q/k/v/o r8 for this full train so it stays comparable with the pilot. Merged attention means each LoRA on decoder k/v adapts self-attention and cross-attention keys together, and that is unavoidable. q/k/v/o on encoder plus decoder (144 modules) already covers every attention path, so the merged structure is no reason to add FFN. Add FFN (gate/up/down) or r16 only if the full train underfits, meaning train loss plateaus above about 0.5 while val NLL is still falling with training. Do that as a separate arm after the test decision, not inside it. 1.47M trainable parameters on 1,293 examples is not capacity-limited, so the binding constraint is steps.

**Q9. Test allocation with B-family running in parallel?**
Test goes to one A1 checkpoint, once. B-family results stay on val161 under the same contract. If a B candidate later beats A1 on val, pre-register a single head-to-head on test using an already-chosen checkpoint for each system. Do not let the existence of a test run for A1 relax the rule for B.

**Q10. A1 fits F5 but not "EG2 reuse". How should the goal be defined?**
Split the goal into two:
- **F5 product goal:** Grounded abstractive summaries on CPU. A1 meets this.
- **Research goal:** An EG2→decoder bridge. It needs a *stated reason to exist*.

With 100% token-string alignment on H4′ text, running the T5 encoder (100M non-embedding parameters, one pass over ≤908 tokens) is cheap next to roughly 250 greedy decoder steps. So the latency gain from skipping the T5 encoder is small. The strong motivation is storage: memories that keep only EG2 states and not text, or a shared resident encoder for several decoder features. Unless one of these is a real requirement, the general bridge should stay exploratory with a small budget. Also note that D-042 ("EG2 text hidden for F4/F5: abandoned") still governs the product path. Any B-family product adoption needs a new decision that explicitly supersedes D-042.

**Q11. Overfitting at 2–3 epochs on 1,293 pairs?**
The risk is moderate and observable. The LoRA is small and there is dropout 0.05, but training is batch 1 with constant lr 2e-4 and no warmup or decay. Fix the following now. (1) **Reshuffle every epoch.** The code cycles a single fixed `randperm` through `order[(step-1) % len(order)]`, so epoch 2 repeats epoch 1 in identical order. (2) Keep AdamW at the torch default weight_decay 0.01 and state it, since it is currently implicit. (3) Keep lr constant to stay comparable with the pilot. A short linear decay over the last 20% is defensible, but it is a change, so pre-register it if used. (4) The plan says "batch 1 + gradient accumulation", but the runner has no accumulation. Either implement it or correct the plan. My preference is to stay at batch 1 for comparability and fix the plan text.

**Q12. Factual errors or omissions?**
Yes. See §7. The most material are: H4′ alignment is overstated (it was measured on corpus v2 sentences, not F5 passages, and D-027 records 6,186 id mismatches and an `<eos>` difference). B1d's injection point is internally inconsistent. Pilot300 exceeded D-082's 50–100-step approval without a recorded decision. The A1 LoRA is applied to the encoder too, so A1's encoder is not "native" in the frozen sense, which matters for B1d's teacher choice.

---

## 4. Bridge addendum

### 4.1 Technical check of B1d

1. **The injection point is inconsistent.** The teacher `H_T = T5Encoder(prompt+passage)` is an *encoder output*: contextual and after the final norm. §3.7.4 says to inject `H_s` "as encoder inputs_embeds", which would push an output-space tensor through the encoder a second time. That is off-distribution by construction. The same section says "the T5 encoder is not used at runtime". Only one reading is consistent: **`H_s` replaces `encoder_outputs`**. That is exactly A2's injection site, now with a distribution-matching objective. The document should say so plainly, because it reframes B1d as "A2 done correctly" and not as a member of the soft-token-at-encoder-input B family. The alternative, matching T5 *input* embeddings, is degenerate under perfect token alignment: the adapter only has to recover token ids, and EG2 adds nothing.
2. **Teacher choice.** If the F5 decoder is A1's LoRA'd decoder, the teacher must be **A1's LoRA'd encoder**, because A1 puts LoRA on 72 encoder modules. A bridge distilled from the base encoder feeds that decoder slightly off-distribution states. For a general bridge, use the base encoder with the base decoder. Choose explicitly.
3. **Token alignment.** H4′ is a *token-string* sequence match on 4,695 corpus-v2 sentences with zero mismatched-id tokens *in that corpus*. D-027 records 6,186 id mismatches and a different `<eos>`. F5 news passages, special tokens (BOS/EOS), and any EG2 task prompt (EmbeddingGemma-style `task: … | query:` prefixes, if used) must be re-verified and position-mapped. This is cheap and must happen before any per-token loss.
4. **Hidden-state scale.** Gemma-family hidden states usually have a few very-large-magnitude dimensions. Plain MSE on raw 640d is then dominated by those dimensions, and cosine ignores the norm, which the frozen decoder's k/v projections do see. Measure per-dimension teacher statistics first. Use per-dimension standardized MSE plus cosine, and verify the student's per-token norm distribution against the teacher's.
5. **Objective.** Representation loss alone does not guarantee the decoder can consume the result: small, correlated errors can compound in a frozen 18-layer decoder. Add an optional **output-level KD term**, the KL between teacher-forced decoder next-token distributions given `H_T` and given `H_s`. It still needs no summary labels (decode the teacher's own greedy output or the passage itself as continuation), and it is the real criterion. It costs one frozen-decoder forward/backward per step, about A1 step cost.
6. **EG2 token-state quality.** EG2's last layer is trained for mean-pooled embeddings, and D-042 already found EG2 text hidden inferior for F4. Intermediate layers (as in A2-null's PCA) may carry more token-level content. Treat "which EG2 layer" as a probe variable.
7. **Cost.** The estimates are plausible and probably pessimistic for compute. Teacher cache is 1,617 × about 900 × 640 × 2 B ≈ 1.9 GB, which checks out (about 1.6 GB at the 762 mean). An EG2 cache at 768d is about 2.2 GB on top. B1a/B1b training on cached features without KD takes minutes on CPU. The time goes into implementation and into generation evaluation at about 9 min per val161.

### 4.2 Rankings

**(a) F5-only** (best F5 quality per unit cost, A1 as baseline):

1. **B2**: adapter plus q/k/v/o LoRA. This is effectively A1 plus EG2 side input. It is the only B variant likely to *match* A1, because a frozen decoder cannot learn EOS and length behaviour from soft tokens alone (zero-shot EOS 1.86%). It needs an A1-vs-B2(real)-vs-B2(shuffled EG2) comparison or it proves nothing.
2. **B1d**: if it reaches near-teacher NLL, it reuses A1's decoder unchanged.
3. **B1b**
4. **B1a**
5. **B3**: frozen-model prompt tuning at 270M, confounded by the passage already being in the input.

None of these is likely to beat A1 on F5. For F5 alone, the B family has low expected value.

**(b) General EG2→T5 bridge:**

1. **B1d**: the only variant trained without task labels.
2. **B1b**: a context-correcting adapter. It is the natural B1d student architecture if B1a's linear map is insufficient.
3. **B1a**
4. **B2**: task-specific LoRA ties the bridge to one task.
5. **B3**: a pooled single vector loses token-level content, and it is task-supervised.

### 4.3 First two-week experiment
After A1's full train, test, and human review finish: **the B1d feasibility probe (B1a, then B1b student), with substitution-NLL evaluation and a small generation check.** Steps:
- Days 1–2: alignment audit, caches, teacher stats.
- Days 3–6: B1a/B1b training with standardized-MSE + cosine.
- Days 7–10: optional KD term.
- Final days: write-up.

Do not start B3 or B2 in this window.

### 4.4 Minimum test that falsifies B1d
On val161, with the frozen base decoder (or A1's decoder with A1's encoder as teacher, consistently), compute teacher-forced NLL of the reference summaries under four memories: `H_T` (teacher), `H_s` (student), `H_T` shuffled across documents, and `H_s` shuffled. Define the recovered fraction **R = (NLL_shuf − NLL_student) / (NLL_shuf − NLL_teacher)**.

**B1d is falsified if** either of these holds:
- R < 0.5 for the best of B1a/B1b, after the alignment and scale fixes above, and with KD tried once.
- Greedy generation on 20 fixed val documents with `H_s` as `encoder_outputs` gives EOS < 90% or grounded < 95%, while `H_T` passes.

Cost: about 1–2 h of CPU after the caches exist. As a sanity anchor, A2's real-vs-shuffled gap was only 0.058. The teacher-vs-shuffled gap must be large for the test to have resolving power, so measure it first and abort if it is under about 0.3 nats.

### 4.5 Most likely failure mode of each

| Variant | Most likely failure mode |
|---|---|
| **B3** | The adapter learns a document-independent task prompt. Real and shuffled EG2 score the same, and quality stays near frozen zero-shot. |
| **B1a** | A per-token linear map from mean-pool-tuned EG2 last-layer states cannot reproduce contextual T5 encoder states. Cosine looks fine, but NLL recovery is low because the errors are structured. |
| **B1b** | It fits the train passages (1,293, too few for a general mapping) and generalizes poorly to val. It needs more P0 text than F5 provides. |
| **B1d** | The objective mismatch: low representation loss but poor decoder consumption (outlier-dimension and norm errors), or the base-vs-A1 teacher mismatch. |
| **B2** | The LoRA learns to summarize from the passage tokens or the soft tokens and ignores EG2. In effect it is A1 again, and the real-vs-shuffled EG2 delta is about 0. |

### 4.6 Parameter, memory and time checks **[recomputed]**
- Linear 768→K·640 (with bias): K=8 3.94M, K=16 7.87M, K=32 15.75M. Correct.
- MLP 768→1024→K·640: K=8 6.04M and K=16 11.28M are correct. **K=32 is 21.78M, not 22.4M.**
- §3.7.7 lists B3 trainable as "4~16M", which leaves out the MLP variants (up to about 22M).
- B1a 768→640 = 0.49M. Correct.
- A1 LoRA 1,474,560. Correct: r8 × (640+1024 + 640+256 + 640+256 + 1024+640) = 40,960 per layer × 36 layers.
- B3 time is given as "3~4h" (§3.7.7) and "2~4h" (§3.7.8). That is inconsistent. B3 backpropagates through the full frozen encoder and decoder, so its step cost ≈ A1 (about 4.2 s), and prompt-style tuning usually needs more steps than LoRA. 1,000 steps is probably too few, and the 70–90 min figure covers training only.
- The B1d teacher-cache estimate of 1.9 GB is correct (padded). The EG2 student cache (about 2.2 GB) is missing from the estimate. Both fit in 15.6 GB.

### 4.7 F3/F4/F6 interface
Spend no more than a one-page interface note now. It should cover: EG2 layer index, the shape and dtype of token states, special-token and prompt convention, tokenizer/model hashes, and whether the bridge replaces `encoder_outputs` or prepends `inputs_embeds`. Retention testing is not warranted yet. The base weights are frozen and adapters are per task, so there is nothing to retain until a general bridge exists. F3 uses retrieval/emoji tagging and has no decoder path, so it should not shape the bridge design at all.

---

## 5. Must-fix (priority order)

1. **Record the full-train selection protocol in the pre-registration** *(document fix)*: fixed checkpoint steps, gate-then-max-char-F1 rule, tie-break, teacher-forced val NLL logging, "no 3rd epoch unless…", human review on val before test. Replace the meaningless "early stop patience 1" with this rule.
2. **Per-epoch reshuffle, plus explicit optimizer settings** *(code-level change before full train, no new experiment)*: the current loop repeats one fixed permutation every epoch. State weight_decay. Remove "gradient accumulation" from the plan or implement it.
3. **Governance gaps** *(document fix)*:
   - Record the decision that authorized pilot300 (D-082 approved only 50–100 steps).
   - State that D-042 still governs product use of EG2 text hidden, so B-family adoption needs a superseding decision.
   - State that test 163 was used once for A0 (D-080: 0.6072), so "unused" means "unused for A1".
4. **Fix the B1d specification** *(document fix)*: injection via `encoder_outputs`, not `inputs_embeds`. Choose base or A1 encoder as teacher. Add a scale/normalization plan and an optional KD term. Correct the H4′ alignment claim (see §7) and require a re-audit on F5 passages.
5. **Report slot preservation, slots per document, and sentence-count compliance next to grounding; split vacuous from non-vacuous grounding** *(document fix; recompute from existing predictions)*.
6. **Bare-prefix val161 on the pilot300 adapter** *(needs new experiment; about 9 min CPU, inference only)*: this is what decides D2.
7. **Store the input contract (prefix, max_input, max_target, tokenizer hash) inside the adapter checkpoint and in the eval metrics** *(small code change)*.

---

## 6. Additional experiments (≤5)

| # | Experiment | Rough CPU cost | Decision value |
|---|---|---|---|
| 1 | Bare val161 with the pilot300 adapter | about 9 min | Decides D2 for the full train. Highest value per minute. |
| 2 | A1 full train, 2 ep, 4 checkpoints × val161 generation + val NLL | about 3 h + 4 × 9 min ≈ 3.6 h | The main decision. Supplies the test candidate. |
| 3 | Stratified human 50 on the chosen checkpoint (val) | 0 CPU, about 2–3 h human | The only fidelity check outside slots. Can veto test. |
| 4 | B1d feasibility probe (alignment audit, caches, B1a/B1b, substitution NLL R, 20-document generation) | about 1 h caches + under 1 h train + 1–2 h eval | Go/no-go for the whole general-bridge line, at a fraction of the cost of B3/B2. |
| 5 | Seed replicate of the chosen A1 config (second seed, same steps) | about 3 h | Shows whether the +0.047 margin is stable or seed luck. Run it only if the full-train margin over A0 falls below about +0.03. |

---

## 7. Factual errors, overclaims, omissions

1. **H4′ overclaim.** "Segmentation matched 100% on 4,695 sentences, so token-level alignment can be assumed" is an overstatement. H4′ (`docs/gates.md`) is a token-string match on corpus v2 sentences, with zero mismatched-id tokens *in that corpus*. D-027 records 6,186 vocabulary id mismatches and an `<eos>` difference. The claim has not been validated on F5 passages or with special and prompt tokens.
2. **B1d is self-contradictory** about whether `H_s` goes into `inputs_embeds` (encoder runs again) or stands in for encoder output ("the T5 encoder is not used at runtime"). It is also presented as a soft-prefix-at-encoder-input method, but it is really an `encoder_outputs` replacement, which is A2's injection site.
3. **"A1 = native encoder" is imprecise.** A1 puts LoRA on 72 encoder q/k/v/o modules as well as 72 decoder modules (144 total, `attach_lora` targets `model.encoder.text_model.*` and `model.decoder.*`). That is acceptable for A1, but it matters for the teacher choice in B1d and for any statement that "the encoder distribution is preserved".
4. **Approval scope.** Pilot300 exceeds D-082 ("smoke 1 step + pilot 50~100 step only"). There is no recorded decision.
5. **D-042 omitted.** The plan (`plan_c5_abstractive_v0_1.md` §1) and D-042 abandon EG2 text hidden for F4/F5. D-081 kept D-042 in force for the product path. The request never mentions this when it proposes B1/B1d with raw EG2 token states.
6. **"Test 163 unused"** should read "unused for A1". A0 was evaluated on it (D-080, 0.6072).
7. **Prefix interpretation overclaim.** "The prefix-trained adapter keeps summarizing on bare input, so it does not depend on the prefix" rests on n=5, with output length differing 264 vs 167. "Official summarization prompt is `summarize:`" (prompt diagnosis report) is sourced from an HF discussion thread, not official documentation.
8. **Arithmetic and consistency.**
   - MLP K=32 should be 21.8M, not 22.4M.
   - B3 time is "3~4h" vs "2~4h".
   - B3 trainable range "4~16M" excludes the MLP variants.
   - The B1d memory estimate leaves out the EG2 student cache.
9. **Omissions in the metrics.**
   - A1 slot preservation is 0.456 against A0's 0.801. A1 has 5.2 slots per document against A0's 8.75. Targets are at 0.510.
   - Sentence-count compliance with the 3–5 target is not reported (heuristic: 28/161 A1 outputs outside the range).
   - ROUGE-L and latency are listed in the plan DoD but not measured.
   - About 91% of the slots the grounding checks are numbers. Entity and polarity errors are invisible to the verifier.
10. **Code vs plan.** The plan says "batch 1 + gradient accumulation" and mentions gradient checkpointing as default. The runner has no accumulation, and checkpointing is opt-in. A single fixed permutation repeats across epochs.
11. **A2 attribution.** "A2 failure = absence of decoder adaptation" is listed under "supported interpretations" in §4. It is a hypothesis consistent with the paper, and the request itself admits (§8) that it is not isolated. Move it to "remaining hypotheses".

---

## 8. Final recommendation

Approve a 2-epoch A1 full train with the protocol fixes above. Run bare val161 first (about 9 min) to settle the prefix. Select the checkpoint on val by a pre-registered rule, review 50 stratified val outputs by hand, then use test 163 once. Report grounding together with slot preservation, and keep vacuous and non-vacuous cases separate. Freeze the B family until A1 is decided. Then run one cheap B1d feasibility probe, specified as an `encoder_outputs` replacement with a matched teacher and judged by recovered substitution NLL, before investing in B3 or B2. Before any of that, write down why an EG2→T5 bridge is needed (storage or no retained text), since the latency gain is small.
