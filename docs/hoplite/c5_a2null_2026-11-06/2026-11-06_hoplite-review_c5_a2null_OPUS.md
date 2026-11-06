# Independent review — C5/F5 A2-null (Opus 5.5, reasoning=medium)

- Date: 2026-11-06
- Reviewed document: `reports/EXTERNAL_REVIEW_C5_A2NULL_2026-11-06.md` (read in full, 568 lines)
- Requested review HEAD: `c388699`. After `git fetch origin && git pull --ff-only origin main`, the workspace HEAD is **`fb2908d`** ("docs: prepare A2-null Hoplite review prompts"). `c388699` is its parent. `git diff c388699 fb2908d` touches only the 4 files in `docs/hoplite/c5_a2null_2026-11-06/` (prompts and dispatch.sh), so every reviewed file is identical at both commits.
- Also inspected: `reports/C5_a2null_{eos_retrain,ln_retrain,search_2026-11-06}.md`, `reports/C5_summary.md`, `eval/slot_verify.py`, `runner/c5_a2null_{eval,full_train,extract}.py`, `docs/plan_c5_{a2null,abstractive}_v0_1.md`, `reports/provenance/C5_a2null/*.json(l)`, `git show f06df58`, and the `transformers==5.22.1` source for `T5Gemma2MergedAttention`, `T5Gemma2DecoderLayer` and `prepare_decoder_input_ids_from_labels`.
- Not available in this workspace: `data/` (models, feature cache, clean jsonl) and `logs/`. Nothing was run against the model. The numbers I computed come only from the committed val-5 prediction files and are labeled as such.
- Scope: consultation only. This file is the only file I created, and I modified no code.

---

## 1. Verdict

**Pivot to A1.** Before pivoting, spend about 1 hour on a closure diagnostic for A2-null using the existing adapters and cache: a memory-ablation ΔNLL on val 161, plus the raw-vs-seq projection control. That run needs no new training. Park decoder LoRA for A2-null until A1's LoRA code exists, then run it at most once as an "A1 recipe with the encoder swapped" comparison.

---

## 2. Answers Q1–Q15

### Q1. Is A2-null-seq a legitimate extension?
It is a large extrapolation, and the request should frame it as a new hypothesis rather than an extension. The original method is training-free and makes pooled retrieval embeddings richer while keeping the text component bit-identical (`pooled_text_cosine_mean 0.99999`). A2-null-seq instead feeds a token sequence to a frozen generator that was never trained on EG2 geometry. So the null-space property ("W-space is untouched") has no particular value here: the adapter's first `Linear(768→768)` mixes both subspaces anyway. The one question A2-null can answer scientifically is "does adding layer-12 PCA in the null space help a decoder relative to the projected final hidden alone?" Only **seq vs raw under an identical recipe** tests that. No run so far has done that comparison.

### Q2. Is the EOS/label fix sufficient?
Yes for the label contract. `make_batch` builds `content(add_special_tokens=False) + <eos>`, with -100 after that. In 5.22.1, `prepare_decoder_input_ids_from_labels` prepends `config.decoder.bos_token_id` and turns -100 into pad, so the decoder sees `[<bos>, content…, <eos>, <pad>…]`, which matches generation starting from bos. Remaining code issues are about hygiene and reproducibility, not label correctness:
- (a) `runner/c5_a2null_full_train.py` at HEAD hardcodes `LayerNorm + scale` (commit `f06df58` changed the class in place). The **EOS-only arm cannot be reproduced from HEAD**, yet both reports cite the same command line.
- (b) `runner/c5_a2null_eval.py` defaults to `--split test`, and its `--max-new` default (256) differs from the reported value (128).
- (c) The trainer's default `--out` is the deprecated `f5_a2null_full/` directory, and it auto-resumes from `last.pt` there.
- (d) No committed unit test asserts the label/decoder-input contract.

Fix: add a 10-line test that tokenizes 3 targets and asserts no `<bos>` in labels, exactly one `<eos>` at index n, and `decoder_input[0]==bos`.

### Q3. Is "adapter-only failed" justified from val 5?
For the narrow claim "this configuration cannot meet G-C5", yes: 0/5 grounded gives a 95% Clopper–Pearson upper bound of about **52%** on the grounded rate, far below 99%, so full val 161 cannot reverse the gate verdict. The broader claim "adapter-only A2-null is insufficient in principle" is **not** supported. The evidence is consistent with an untrained bridge (1,293 pairs × 1 epoch, lr 1e-4, batch 1; projector-alignment work typically uses far more pairs or an alignment pretraining stage). It is also consistent with a frozen T5Gemma2 decoder that cannot summarize at all, and with the null injection doing harm. None of these has been separated from the others. The strongest val-5 signal is not repetition but **content that does not depend on the input**. All 5 outputs are off-topic: koala/bushfire → candlelight rally in "르네바, Italy"; lawyers' association → university centenary; Bill Barr → candlelight / California. `slot_preservation` is 0.00–0.09. On the committed predictions, char F1 against the *matched* target (0.230 / 0.227) is barely above char F1 against *mismatched* targets (0.206 / 0.190). The memory is carrying almost no source information.

### Q4. What is the next single move, and is LoRA-before-raw-control a causal problem?
Next move: a **teacher-forced memory-ablation ΔNLL** on val 161 with the two existing adapters. Compare NLL with the real memory against shuffled memory (another document's z) and against zero memory. It is cheap (forward passes only, the same code path as the trainer's val loss) and decisive: if ΔNLL ≈ 0, the adapter learned a decoder prior and nothing else, and no amount of val-161 generation adds information. Doing decoder LoRA before the raw control **does** confound the causal reading: any gain would be attributable to decoder adaptation, not null injection. The raw control is cheap. Because `col(P) ⟂ col(W)`, `z_raw = z − (z P) Pᵀ` can be computed from the existing cache and `null_basis.pt`, with no re-extraction (contrary to option F in the request). After that, pivot to A1.

### Q5. Is decoder q/k/v/o LoRA the right design given merged attention?
Not as the first A2-null step. From the 5.22.1 source, `T5Gemma2MergedAttention` calls `self.k_proj(encoder_hidden_states)` and `self.v_proj(encoder_hidden_states)` separately from the self-attention call, then concatenates. So a **memory-side-only LoRA** is straightforward: wrap `k_proj`/`v_proj` so the LoRA delta applies only on the encoder-states call. That is the true XA-only analog, and it leaves self-attention, and therefore the LM prior that F4/F6 might share, untouched. Note also that cross keys go through `k_norm` (per-head RMSNorm) and get no RoPE. Key scale is normalized away, which helps explain why LN×5 did little; only value scale reaches the output. If you do it: rank 8–16, alpha = 2·rank, LoRA lr 1e-4–2e-4, adapter lr ~1e-3, grad-accumulation 8–16, 2–3 epochs, early stop on val generation metrics. Gradient checkpointing is unnecessary at RSS ~2 GB; CPU time is the constraint. Build it inside the **A1 LoRA code path** so the only difference between A1 and A2-null+LoRA is the memory source.

### Q6. Which gates to preregister?
Required (val 161, before any test use):
- (1) Grounded ≥ 99% **and** micro new-slot rate ≤ 1% (pooled `Σnew/Σsummary_slots`, not the current per-sample mean).
- (2) EOS rate ≥ 95%, with `max_new_tokens` ≥ 1.5 × p95 target length.
- (3) Repetition: repeated-4-gram rate and distinct-2 within a fixed margin of the gold targets.
- (4) Memory-ablation ΔNLL > 0 with a CI excluding 0.
- (5) A content metric (ROUGE-L or chrF) above a **mismatched-target floor** and non-inferior to A1 by a preregistered margin.
- (6) Human 50 acceptance ≥ 60% (already in the plan's DoD).

Reference only: compression, copy rate / novel n-gram rate, slot preservation, latency. Test 163 is used once, for the single final candidate, after all of the above. "char F1 ≥ A0" should not be a gate (see Q8).

### Q7. Is `grounded = not new_slot` sufficient?
No. It is a necessary safety filter but a poor quality or faithfulness metric. An output with no digits counts as grounded (`new_slot_rate = 0` when `summary_count == 0`), so a model that learns to avoid numbers will pass while hallucinating entities. The val-5 outputs already hallucinate non-slot entities such as 이재명, 롯데백화점, 캘리포니아주립대 and 르네바, none of which the verifier catches. Add these checks without an external LLM:
- **novel-entity/eojeol rate**: summary eojeol or char-4-grams containing proper-noun-like tokens absent from the source;
- **repetition** (repeated n-gram rate, longest repeated span);
- **truncation flag** (no EOS);
- **the macro→micro new-slot fix**.

Human review remains the only factual-consistency check for now, so keep the 50-item review mandatory.

### Q8. Is the A0 comparison fair? What besides char F1?
Not as a quality comparison. Char-bag F1 rewards copying and is weakly discriminative for Korean news. On the committed val-5 file, an **unrelated document's gold summary** scores char F1 ≈ 0.40 against each target, above A2-null's 0.23 (n=5, rough estimate). A2-null is below a wrong-document floor, and A0's 0.607 (test 163) should be read against a floor of that size, not against 0. Compare on: micro new-slot and novel-entity rate, compression ratio, novel n-gram (abstraction) rate, ROUGE-L/chrF over a mismatched floor, EOS/length, and human acceptance, all on the **same split** (val 161 for A0 can be computed at no cost).

### Q9. Stopping rule?
"Decoder LoRA once, stop if grounded = 0" is a weak rule, because a LoRA model can reach grounded = 1.0 by emitting slot-free fluff. Better:
- **Stop A2-null as the primary line now.**
- Reopen only if the ablation ΔNLL is clearly positive *and* seq > raw.
- Then allow exactly one A2-null+LoRA run using the finished A1 recipe and budget, judged by non-inferiority to A1 on val 161 under the Q6 gates.
- If that fails, close A2-null with a written negative result.

Waiting for A1 is consistent with D-081 itself ("product adoption needs A1 val comparison"), so A2-null cannot reach a decision without A1 anyway.

### Q10. Lessons to carry into A1, and A1 smoke items
Smoke items:
- (1) Label/decoder-input unit test (Q2).
- (2) **Overfit-8 test**: train on 8 pairs until the loss is near 0 and confirm greedy output reproduces the targets. This end-to-end pipeline check was never run for A2-null.
- (3) Measure the target token-length distribution and set `max_new_tokens` from it.
- (4) Encoder-shuffle ΔNLL as a conditioning check.
- (5) Seal guard: eval refuses `split=test` without an explicit `--unseal-final` flag plus a recorded decision ID.
- (6) Pick checkpoints by val generation metrics (20 fixed random val ids), not by loss.
- (7) Text-only load with RSS/step-time logging.
- (8) Every arm reproducible from a commit plus a flag, with no in-place class edits.

### Q11. Missing facts and bias
Yes, there is visible confirmation and sunk-cost drift:
- The ladder (EOS → LN → LoRA) adds one knob per run while the basic "does the memory condition anything?" check never ran.
- The failure is framed as "repetition collapse" when it is mainly input-independent generation.
- The LN rationale (attention-logit saturation) is undercut by `k_norm` on cross keys.
- The request omits that `plan_c5_abstractive_v0_1.md` names A1 as the approved-first path and that A1 is required for any A2-null decision under D-081.

Also missing from the request:
- `max_new_tokens = 128` is below the stated ~175-token mean target, so EOS 0/5 is partly an evaluation artifact.
- No norm statistics for `‖W h‖` versus `‖P x‖`. Unscaled layer-12 PCA could dominate z, which is consistent with the adapter-output max norm of ~2,000.
- EG2 features were extracted without EG2's task prompt prefix. This is acceptable but should be recorded.

### Q12. F5-only or a shared bridge interface?
Keep the implementation F5-only, but write down the **contract** now as a one-page ADR. Its contents:
- the memory tensor `[B,T,640]` bf16 plus a bool mask;
- the label contract (no bos, trailing eos, -100);
- the base checkpoint hash and tokenizer;
- per-task LoRA naming and loading;
- the rule that the base weights stay frozen and each task gets its own LoRA.

With separate swappable LoRAs on a frozen base, the rework cost of not designing a shared bridge now is small: a merge or multitask decision can come later (D-6 A1-all). Building a shared framework now, for a bridge with no working instance, would be premature.

### Q13. D-042 and reuse boundary
No. Product reuse in F4/F6 needs a new decision. D-042 is about EG2 text hidden in product paths, and nothing in A2-null so far is evidence against it; if anything, val-5 is weak evidence in favor. Exploratory reuse in F4/F6 would need its own preregistered plan under the D-081 pattern: exploratory label, F4/F6 test sets sealed, a separate gate, and no shared weights with any product LoRA. Note that the current A2-null has nothing worth reusing; only the A1 LoRA tooling is.

### Q14. F3 vision→text extension
F3 should not reuse the EG2→T5Gemma2 text bridge. T5Gemma 2 is natively multimodal: it has its own vision encoder, which the A1 plan proposes dropping for a text-only load. A future vision→text F3 should therefore use T5Gemma2's native image path, plus a task LoRA if needed. EG2's image embedding stays the retrieval path. Today, the only thing worth recording is "do not hard-delete the vision tower from shared artifacts; load text-only at runtime". No design work is warranted yet.

### Q15. Multitask retention gate now?
Not now, provided each task gets its own LoRA on a frozen base: retention is then guaranteed by construction, because the base weights never change. Add a retention gate only when a merged or shared LoRA (A1-all) is proposed. At that point, use:
- an F4 identity set (correct sentences must come back unchanged; target ≥ 99% exact identity);
- the F6 correction pairs (CER/WER delta versus the per-task LoRA);
- F5 val 161 under the Q6 gates.

---

## 3. Must-fix (priority order)

1. **Run a memory-conditioning check before any more A2-null training.** Measure teacher-forced NLL on val 161 with real, shuffled and zero memory, for both existing adapters, and report ΔNLL with a bootstrap CI. Without it, no A2-null result (including any future LoRA result) can be attributed to the memory.
2. **Fix the evaluation contract.** Set `max_new_tokens` from the measured target-length p95 (128 < ~175 mean). Report new-slot as micro. Add repetition, novel-entity and truncation metrics. Add a mismatched-target floor to every content metric, and stop using char-bag F1 as a headline.
3. **Add a seal guard to `runner/c5_a2null_eval.py`.** The default `--split test` should become val or required, with an explicit unseal flag. Do the same in any A1 eval script.
4. **Make arms reproducible.** Restore the EOS-only arm behind an adapter flag (`--adapter-norm none|ln`) instead of editing the class in place. Change the trainer's default `--out` away from the deprecated `f5_a2null_full/` resume directory. Commit the label-contract unit test.
5. **Correct the request document** per §5, especially the z formula, the "raw control needs re-extraction" claim, the EOS interpretation under the 128-token cap, and the framing of the failure as repetition rather than input-independent output.

## 4. Additional experiments (max 3)

1. **Raw vs seq vs native, adapter-only, overfit-8 plus ΔNLL.** From the existing cache, build z_seq, z_raw = z − PPᵀz, and optionally T5Gemma2-native encoder outputs (640d, identity-initialized adapter) for 8 train pairs. Test whether each can be overfit to reproduce targets, and compare val ΔNLL. This separates "frozen decoder can't be steered", "EG2 memory lacks content" and "null injection hurts" in under about 1 CPU-hour.
2. **A1 with a memory-side-only LoRA variant.** In the A1 code, compare standard q/k/v/o LoRA with the k/v-on-encoder-states-only LoRA. The result is useful for F4/F6 sharing (the self-attention LM prior stays untouched), and the same harness later evaluates A2-null+LoRA cleanly.
3. **A0 and A1 on val 161 under the new metric set.** Include the mismatched floor, micro new-slot, novel-entity rate, repetition and compression, so CP3-2 has a same-split extractive vs abstractive comparison before test 163 is unsealed once.

(Not recommended: more adapter-only epochs before item 1; decoding hacks such as `no_repeat_ngram_size` except as a labeled diagnostic; any use of P1 data, external LLM APIs or test 163.)

## 5. Factual errors, overclaims and omissions in the request document

1. **§3.2 formula:** `z_t = [W h_t ; P x_t] # 768` reads as concatenation (which would be 1536-d). The code (`runner/c5_a2null_extract.py`) computes a **sum**, `z = final + x @ P.T`, where `final = last_hidden_state` is already the projected 768-d `W h`. Write `z_t = W h_t + P x_t`.
2. **§7 option F:** "feature 재추출 + 별도 cache 필요" (needs re-extraction and a separate cache) is wrong. `z_raw = z − (zP)Pᵀ` and `x = zP` can be computed from the existing cache with `null_basis.pt` (fp16 rounding is the only caveat). A pooled reference can also be approximated from the cache.
3. **EOS interpretation:** eval used `max_new_tokens = 128` while §6.2 states the targets average ~175 tokens, and the gold targets are 252–357 chars against ~150–190-char predictions. EOS 0/5 and the char-F1 recall are partly caused by the cap, and the document never mentions this.
4. **Failure framing:** "반복 붕괴" (repetition collapse) understates it. All 5 outputs are topically unrelated to the source, slot preservation is ≈0, and matched-vs-mismatched char F1 differ by only ~0.02–0.04 (computed from committed predictions). The main failure is that the output does not depend on the input.
5. **§5.4 / §1.2 LN rationale:** the "attention-logit saturation" hypothesis ignores that T5Gemma2 applies `k_norm` (per-head RMSNorm) to cross keys, so key scale is normalized. "Scale was not the main cause" is the right conclusion, but the stated mechanism was weak from the start.
6. **§6.1 "attention mask 정상" (mask is fine):** with batch 1 and an all-ones mask, the padding path was never exercised. It is untested rather than verified, which matters once batch > 1.
7. **§5.6 metric definition:** `new_slot_rate_mean` is a per-sample macro mean in which slot-free outputs count as 0. The G-C5 audit numbers (980/14,454) are micro. The two are not comparable.
8. **§2.5 framing:** "A2-null 0.23 vs A0 0.61 is important" has the right split caveat but omits the floor: an unrelated gold summary scores about 0.40 char F1 on the val-5 targets (rough, n=5), so char F1 is a weak discriminator.
9. **Reproducibility (§5.2 / §10):** the EOS-only arm cannot be reproduced from HEAD, because `f06df58` replaced the Adapter class in place. The `train_report.json`, logs and model files are not in the repo, so the losses in §5.2 cannot be checked from git alone.
10. **§10.3:** "작성 시점 작업 트리 clean, origin/main 0/0" (clean tree, in sync at writing time) is now stale. HEAD is `fb2908d`, docs only.
11. **Omissions:**
    - No unconditional/ablated NLL baseline for the val loss of 3.12.
    - No `‖Wh‖` vs `‖Px‖` norm statistics.
    - No overfit-small-set sanity check.
    - EG2 features extracted without a task prompt.
    - The A1 plan (`plan_c5_abstractive_v0_1.md`) is the approved-first abstractive path, and D-081 makes A1 a prerequisite for any A2-null decision.
    - T5Gemma2 has a native vision path, which matters for Q14.
    - Whether the 270m-270m checkpoint is pretrained-only or instruction-tuned is not stated, and this matters for interpreting a frozen decoder.
12. **Overclaim risk in §6.1:** "이미 배제한 가설" (hypotheses already ruled out) lists the label and scale as ruled out after single val-5 runs. They are better described as "fixed; not shown to be sufficient".
