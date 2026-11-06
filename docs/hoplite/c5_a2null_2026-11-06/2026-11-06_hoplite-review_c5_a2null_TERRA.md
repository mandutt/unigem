# Independent review: C5 A2-null — GPT-6.1 Terra

**Review basis.** `git fetch origin` and `git pull --ff-only origin main` both succeeded; resulting HEAD was `fb2908d0f0cc1418f8207853814a5d135c3a1b23`. The requested `c388699` is its direct ancestor; the complete request and all nine permitted verification files are unchanged between the two commits. I read the request end-to-end and inspected the permitted reports, plans, training, generation and slot-verification code. I did not inspect P1 data or use the sealed test, and made no repository code changes. The local T5 model, clean data, feature cache, PyTorch and Transformers are absent, so model-level assertions below are static review, not a reproduced training or generation run. A small standard-library-only check used synthetic strings with the actual slot verifier.

## 1. Verdict

**full val 161 first** — after evaluation safeguards and a pre-registered protocol; then prioritize an A1 smoke/pilot, rather than automatically spending another run on A2 decoder LoRA.

## 2. Answers to Q1–Q15

### Q1. Experimental design

The sequence bridge is a legitimate hypothesis, not a validation or direct reproduction of the pooled-audio retrieval result: a per-token, task-trained memory for generation is a different setting. Orthogonality and PCA variance establish algebra and variance retention, not summary relevance, preservation of decoder-useful information, or causal benefit from null injection. The unrun raw control is needed to isolate injection, and the unrun pooled reference is a separate architectural comparison, not a substitute for it.

### Q2. Labels and code

`runner/c5_a2null_full_train.py:65–101` reserves a position for EOS, disables automatic special tokens, appends EOS and masks later labels with `-100`; the reported T5Gemma2 label shift prepends the decoder BOS, so this is the right contract in principle. The [Transformers 5.22.1 model source](https://raw.githubusercontent.com/huggingface/transformers/v5.22.1/src/transformers/models/t5gemma2/modeling_t5gemma2.py) confirms that automatic shifting occurs when labels are supplied without decoder inputs, and uses the decoder configuration's BOS and PAD. On the actual pinned model, test ordinary, empty and truncated targets, inspect IDs and the shifted sequence, assert EOS/PAD/BOS and training/generation start IDs, and compare loss to a manually shifted forward pass; account for the fact that a maximally long label's terminal EOS is not itself in the shifted decoder input. These artifacts are absent here, so I cannot independently execute those model-specific checks.

### Q3. Result interpretation

Both corrected-label one-epoch configurations are visibly unsuitable on these five selected validation examples: both were slot-ungrounded on all five and stopped naturally on only zero or one, with reported repetitive text. That is evidence about those exact configurations and cases, not proof that all adapter-only training, the null representation, or even the entire validation population must fail; the first five shard records are not a random sample. In particular, 128 new tokens may itself censor legitimate longer targets, so length distributions and a suitable fixed generation cap must be checked before interpreting EOS rates as a stopping defect.

### Q4. Next investment

First run the existing corrected EOS and LN checkpoints over the same full val 161, after correcting the evaluation hazards and pre-registering decoding and comparison; include A0 on those exact validation IDs. If the patterns persist, prioritize the separately approved A1 native encoder-decoder smoke and pilot, which answers the practical alternative rather than presupposing a frozen-decoder bottleneck. Raw control remains essential before claiming a null-space contribution: an adapter-plus-LoRA run without it can establish only whether that whole system works, not whether null injection helped.

### Q5. Decoder LoRA design

Merged attention makes decoder q/k/v/o LoRA a plausible exploratory intervention, not demonstrably the best one: the same projections participate in both self and cross attention, so it cannot isolate cross-attention adaptation. If A1 and the full-val results justify a bounded A2 follow-up, start with decoder-only q/k/v/o rank 8, alpha 16, dropout 0.05, LoRA LR `5e-5`, adapter LR `1e-4`, one epoch and gradient clipping 1.0; pin the seed, initialization, generation settings and checkpoint selection before training. This is a proposed starting configuration rather than evidence of optimality; verify exact module matches and nonzero gradients, memory dependence, CPU RSS and step time, and enable checkpointing only if memory requires it because of its CPU time cost. Under the stated 18-layer dimensions, all four rank-8 projections add roughly 737,280 LoRA parameters, excluding adapter and optimizer state; measure rather than assume the full runtime.

### Q6. Gates

Pre-register val IDs, inference cap/decoding, checkpoint choice, and denominators; report both summary-level no-new-slot pass fraction and micro-aggregated unique-slot new rate, as well as per-example macro rate, because they are different quantities. As exploratory go/no-go targets, require the stated ≥99% summary-level no-new-slot rate and ≤1% micro new-slot rate, nonempty outputs, ≥90% genuine EOS at a cap justified by the target length distribution, and an explicitly defined repetition/length check; also report failure counts rather than just means. Include paired A0/A1 comparisons on identical val IDs, ROUGE-L, copy/compression and blinded human review of 50 cases for support, omissions, adequacy and repetition; the existing ≥60% human acceptance is a proposal in the A1 plan, not a sufficient standalone safety proof, and char F1 ≥ A0 is not a sensible universal hard gate. Freeze the final candidate and protocol before the separately authorized single test evaluation; 0/161 errors gives only about a 98.16% one-sided 95% exact lower bound on a population pass rate under independent representative sampling, so a nominal 99% sample pass cannot itself demonstrate 99% reliability with that confidence.

### Q7. Evaluation validity

`grounded = not rep.new` tests only whether the regex-extracted canonical slot strings are present somewhere in the source; it is not factual grounding, entailment, completeness or non-repetition (`eval/slot_verify.py:153–183`, `runner/c5_a2null_eval.py:114–126`). With synthetic examples, the verifier passed swapped city/count associations, invented slot-free content, an empty summary, and verbatim repetition; the last two examples are especially important because an empty summary can be labelled grounded despite strict rejection. Add explicit nonempty/3–5-sentence and repetition checks, local automatic overlap/coverage diagnostics, and blinded source-based human judgments of claims, associations, omissions and contradictions; verify the regex on representative Korean formats and distinguish false positives from negatives. Do not use an external LLM API in the product path or treat the slot gate as a complete safety guarantee.

### Q8. A0 comparison

The reported A0 `0.6072` is clean test 163 and A2's `0.2297` is val 5; their numerical difference does not establish a same-distribution quality gap. Run both with the same frozen definitions on identical val cases and compare paired differences and uncertainty alongside no-new-slot rates, EOS/truncation, repetition, length, compression, extractive copying, latency and blinded factual/coverage judgments. A0's extraction makes it a useful no-new-slot baseline but does not make it the abstractive target; bag-of-characters F1 alone rewards neither accurate relations nor informative paraphrasing.

### Q9. Stop rule

A pre-registered full-val continuation rule should consider the whole quality profile, not require the unusual condition of exactly 0/161 grounded, which could continue an obviously unusable system with 1/161 passing. For example, stop investing in the present adapter-only configurations if the fixed-protocol full-val results show widespread repetition or truncation and miss the slot/quality gates, and stop the A2 branch as a practical candidate if a separately justified, budget-limited follow-up cannot meet them or show a credible cost-adjusted advantage over A1. It is legitimate to stop a poorly performing configuration before A1 exists; claims that A2 is inferior to A1 or that null injection has no value require the corresponding comparisons.

### Q10. A1 transition

A1 should use its native encoder and native source mask rather than assuming the external-memory bridge is needed, but should retain the corrected content-plus-EOS label contract and independently verify BOS/PAD, target truncation and shifted decoder inputs. First smoke one forward/backward step and a short free-running decode, checking nonzero intended LoRA gradients, frozen base weights, masks, finite loss, target coverage, EOS, peak RSS and step time; use the A1 plan's >13 GB RSS or >60 seconds/step stop rule before full training. Then run its specified 50–100-step pilot and compare on the same P0 validation examples and fixed evaluation protocol; A1's plan says approval is still pending.

### Q11. Missing facts and confirmation bias

The proposed sequence from full val to LoRA presumes decoder freezing is the cause, but neither the LN arm nor a shape-compatible external forward isolates that cause; optimization, training duration, memory semantics and decoding length remain live alternatives. Model output should be tested for sensitivity to actual versus shuffled/zeroed memory, and masks, IDs and teacher-forced versus free-running paths should be checked before expensive retraining. Repeated selection on val is adaptive even without further gradient updates; A1, raw and pooled were not run, so no causal or cross-system superiority claim is established and investment should be decided prospectively, not by sunk cost.

### Q12. F4/F6 bridge interface

Keep this checkpoint F5-exploratory and record a minimal boundary now: memory shape/dtype, valid-token mask and ordering, tokenizer/encoder and model revisions, LoRA target modules, checkpoint identity, task routing and output contracts. Separate base weights, task-specific LoRA and bridge artifacts so later reuse does not force a shared F5-tuned decoder or silent overwriting. That documentation reduces later integration and compatibility work without building a generic multitask framework or claiming F4/F6 reuse has been validated.

### Q13. D-042 and reuse

D-042 continues to prohibit EG2 text hidden in F4/F5 product paths; D-081 authorizes this A2-null exploration, not product deployment or automatic reuse in another task. A separate, explicitly authorized exploration with P0 data, independent validation and sealed tests could investigate F4/F6 reuse without treating it as product approval; product use requires the applicable new decision and task-specific quality/privacy gates. F6 is not automatically covered by the precise F4/F5 prohibition, but that is not authorization to deploy the bridge there.

### Q14. F3 expansion

Current F3 retrieval/emoji tagging has no decoder and needs no change or F5 retention gate now. For a future vision-to-text requirement, a decoder *interface* or base model may be reusable, but a text-trained EG2 projection and F5 LoRA cannot be presumed compatible with vision features, masks, positional information or objectives. Evaluate a vision-specific bridge and task-specific adapter against the then-current F3 requirements under separate authorization.

### Q15. Multitask regression

Do not make F4/F6 retention a blocking gate for an isolated F5 exploratory adapter that is never loaded for those tasks and leaves the base weights unchanged. Before any shared or merged decoder/LoRA is proposed for F4/F6, establish task-specific held-out P0 baselines and pre-register regression tolerances: e.g., F4 clean-sentence identity preservation and edit precision/false-edit rate, F6 correction error and entity/number preservation, plus F5 factuality and latency. Compare the same inputs with base and candidate weights, include human adjudication for consequential differences, and require separate approval before shared-path deployment.

## 3. Must-fix items, in priority order

1. **Protect the sealed split and evaluation integrity.** `runner/c5_a2null_eval.py:83` defaults to `test` and `:87` to a common output file; require an explicit val split and separate output in the future workflow, and assert expected ID membership, uniqueness and count before scoring. Verify cache masks against lengths and fail on missing shards or inconsistent IDs; this is a recommendation, not an edit made in this review.
2. **Re-establish the end-to-end model contract.** On the actual pinned model, test content/EOS/shifted-label alignment, special IDs and truncation; compare forward and generation masks and test real versus zeroed/shuffled memory, including padding and cached versus uncached generation. Both `make_batch` and evaluation reconstruct masks from lengths rather than using the stored mask, so contiguity is an assumption, not yet verified here.
3. **Fix metric definitions and insufficiency.** Report sample-level no-new-slot, macro per-summary unique-slot rate and micro unique-slot rate separately, together with counts; add nonempty, repetition, length/censoring and source-based factuality review. A no-slot or empty output currently gets a no-new-slot pass and a new-slot rate of zero.
4. **Pre-register full-val and fair same-split comparisons.** Fix both checkpoint identities, decoding including a justified cap, all 161 IDs, A0 pairing and selection rules before running; report uncertainty and prevent repeated val-driven tuning from being labelled confirmatory. Maintain the test seal and compare A1 when authorized.
5. **Do not overstate mechanism or scope.** Correct the null-vector formula and frozen-decoder statement, retire the claim that one LN run ruled out scale as a cause, and record D-042/D-081 and F4/F6/F3 boundaries before considering reuse.

## 4. Additional experiments worth doing

1. **Fixed full-val evaluation:** score both existing corrected checkpoints and A0 on the same 161 validation IDs; record EOS and cap hits with target-length distributions, repetition, paired metrics and a blinded 50-case factual/adequacy sample. This is the immediate next action after the safeguards above, not a test-set run.
2. **A1 native smoke/pilot:** subject to its separate approval, use the existing P0 split and A1 plan's resource stop rules, then run the same frozen val protocol; compare quality and CPU cost to A2 without imputing causal mechanism.
3. **Only if A2 remains decision-relevant:** run a matched A2-null-raw versus injected sequence ablation with identical data, adapter/decoder training, seeds and decoding; optionally include pooled as a separately labelled reference if the pre-set budget allows. A decoder-LoRA arm is a bounded engineering follow-up, not a replacement for the raw control or proof of null-injection benefit.

## 5. Factual errors, overclaims and omissions in the request

- **Invalid/ambiguous formula:** §3.2 writes `z_t = [W h_t ; P x_t] # 768`. Both terms are 768-dimensional, so ordinary concatenation yields 1536 dimensions, not 768; if the intended operation is addition, write `z_t = W h_t + P x_t` and verify it against the actual feature implementation before claiming that is what was run. This review did not inspect the feature-construction implementation.
- **Training contradiction:** §3.2 says both adapter and decoder train, whereas the reported experiments and `runner/c5_a2null_full_train.py:129–135` freeze all model parameters and train only the adapter. Decoder LoRA is proposed, not run.
- **Unfair split comparison:** §0 and §2.5 emphasize that A2's 0.23 is substantially below A0's 0.61 despite the adjacent warning that the samples differ; this is not a paired comparison. §7's proposed LoRA trigger repeats the cross-split comparison.
- **Scale and compatibility overclaims:** one LN×5 arm on five cases cannot rule out scale mismatch as a principal contributor; LayerNorm changes more than scale and its learned behavior may not match the native encoder distribution. A valid shape and forward pass do not establish that the memory is semantically used, masks and caching are correct for all cases, or the decoder is the bottleneck.
- **Metric ambiguity:** `C5_summary.md` describes slot-level grounding, while the A2 evaluator computes a per-summary boolean and averages per-summary unique-slot rates; these denominators are not interchangeable. `verify_summary` deduplicates canonical strings, ignores associations and returns zero new-slot rate for zero extracted slots, so even a 100% pass does not establish factual correctness.
- **Decoding and statistics:** `gen_len` includes the decoder start token, so 129 corresponds to 128 generated tokens, and the 128-token cap can censor natural EOS; inspect target lengths before calling every cap hit a learned stopping failure. Full val reduces the five-case selection problem but cannot by itself certify a 99% population rate, and adaptive use of val can overfit even without additional training.
- **Mask/test operational omissions:** the evaluator reads stored `mask` but replaces it with all ones over `length`, while training similarly assumes a contiguous valid prefix; this is valid only if verified for the cache. Its default split is `test`, contrary to the operational need to protect the sealed test, and it does not assert the full expected ID set. Its `--limit` is applied only after all feature shards for the split have been loaded, so it does not limit cache-reading work; full-val runtime and memory estimates should be measured rather than assumed.
- **Evidence limitations:** raw control, pooled reference and A1 comparison have not been run; no conclusion about injection's causal benefit or A1 superiority is supported. The request's cited SQuAD and other literature are indirect evidence, not a demonstration that merged q/k/v/o LoRA is the optimal next move for this model, task or CPU budget.
