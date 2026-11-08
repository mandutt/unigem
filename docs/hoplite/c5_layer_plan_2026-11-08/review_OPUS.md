# External review — C5 EG2 → multilingual decoder layer plan (Opus 5.5, independent round)

- Reviewer: Opus 5.5 (anthropic/claude-opus-5-5), independent thread. No subagents or other LLMs were used. No other review answer was read.
- Request read in full: `reports/EXTERNAL_REVIEW_C5_LAYER_PLAN_2026-11-08.md` (618 lines, lines 1–618).
- Sync: `git fetch origin` succeeded; `git pull --ff-only origin main` → "Already up to date". Review basis HEAD = **`bb8bf702cbff4c73129098d4b660784be289fd75`** ("docs: add C5 layer-plan 3-AI review prompts and dispatch"). The request was authored at `949df7a`.
- Artifacts inspected: `runner/c5_mt5_layer_probe.py` (full), `runner/c5_eg2_all_layers_cache.py` (tokenization and extraction path), `reports/provenance/C5_b1d/mt5_layer_probe.json`, `reports/provenance/C5_b1d/umt5_layer_probe.json` (all 23 layers each), `docs/decisions.md` D-017, D-107…D-111.
- Not done: no training, no evaluation, test 163 not opened, no P1 data or external APIs, `eval/slot_verify.py` not touched. `data/wave2c/` and `data/models/` are **absent from this workspace**, so I could not measure the tokenizer mismatch rate directly (marked *unverified* below).
- Labels: **[measured]** = read from a repository artifact; **[code]** = read from source; **[inference]** = my reasoning, not verified.

---

## 0. Verdict: **NARROW**

Run **one revised Stage B0** with the controls that make its outcome interpretable. Put the layer-role probing on hold, apart from two cheap diagnostics: tokenizer mismatch and per-layer activation scale. B1, B2 and Stage C are **not approved by this review**. Each needs B0 to pass and a new decision record. Stage C also needs a metric audit first. T5Gemma2 stays closed (D-108). The A1 native pilot300 remains the frozen fallback/reference. Nothing in this plan is a product path, and none of its results should be reported next to A1 as if they were comparable product numbers.

Why NARROW rather than CONTINUE:
1. Stage A is **inconclusive, not negative**. The adapters did not fit even the training set (§1.1), so Stage A cannot support "frozen decoder is the bottleneck" or "no content selectivity".
2. As written, B0 changes **three things at once** compared with Stage A: decoder LoRA, 5→20 documents, and T5Gemma2→native tokenizer. It also has no frozen-decoder arm and no native-encoder positive control. It therefore cannot attribute any change to decoder adaptation, which breaks the plan's own rule in §11 ("do not change model/layer simultaneously").
3. Twenty training documents × 100 steps is very likely too small for a decoder to learn **generalising** cross-attention copying. A STOP triggered by such an underpowered run would be a false negative (§1.4).

Why not STOP: the cost of one well-controlled B0 is bounded (≤ 8 CPU-h, §6). It answers a question that remains genuinely open: does a LoRA-adapted mT5 decoder read *content* from EG2 hidden states? The T5Gemma2 closure does not answer it, because T5Gemma2 used a merged/shared K/V decoder, which mT5 does not.

---

## 1. Key findings from the artifacts

### 1.1 Stage A did not fit its own training data [measured]
- mT5, all 23 layers: `train_ce_last10_mean` = **5.16–5.95** after 100 steps on 5 docs (20 passes per doc). Val real CE = 6.62–7.47.
- UMT5, all 23 layers: `train_ce_last10_mean` ≈ **8.14–8.51**, and val real CE ≈ **8.19–8.72**. Train ≈ val: the UMT5 adapter learned almost nothing.
- Interpretation [inference]: in an underfit regime the adapter's best move is a document-independent "soft prompt" that shifts the frozen span-corruption decoder towards the target style. That alone gives real ≈ shuffled. Stage A therefore measures "an adapter cannot re-purpose a frozen, span-corruption-pretrained decoder in 100 steps". It does not measure whether EG2 content is usable. mT5 and UMT5 checkpoints are pretrained only on span corruption and are generally fine-tuned before generation, so a frozen-decoder probe was always going to be weak [literature-level background, not verified here].

### 1.2 Stage A's "zero" control is off-distribution [code]
`eval_ablation` feeds `torch.zeros_like(mem)` *after* the adapter. The adapter ends in `LayerNorm`, so a learned output is never near zero. Δzero (18.4–19.3 for mT5, 3.5–4.0 for UMT5) measures how badly an out-of-manifold memory disrupts the decoder. It is **not evidence that the decoder "uses memory existence/length"**. A mean-memory control (the dataset-mean adapter output, length-matched) is the appropriate null.

### 1.3 Layer is confounded with seed in Stage A, and layer19 is a winner's-curse pick [code + measured]
- `torch.manual_seed(20261108 + layer)`: every layer gets a different initialisation, so the layer ranking mixes layer effects with seed effects.
- Layer19 was chosen as the best of 23 noisy real-CE estimates on the same 5 val docs (6.623, then 6.908, 6.918). Its Δshuffled is only **0.030**. The highest Δshuffled was layer17 (0.189), followed by layer20 (0.122) and layer14 (0.114).
- B0's stated goal is *selectivity*, yet it picks its layer by *real CE*. The selection criterion does not match the question.

### 1.4 mT5 Δshuffled is not "≈0 everywhere" [measured, my count]
- mT5 Δshuffled is positive in **18 of 23** layers (negative only at L1, L8, L11, L12, L22). The mean is about **+0.037**, with a range of −0.051 to +0.189.
- UMT5: 16/23 positive, |Δ| ≤ 0.009, consistent with a null.
- Caveat: the layers share the same 5 docs and the same cyclic pairing (`ids[(i+1)%n]`), so they are **not independent**. A pairing artefact, such as the neighbour document's length or topic, could produce a consistent sign. This is a weak hint for mT5, not evidence. It still argues against describing Stage A as "no selectivity" without qualification.

### 1.5 The cache feeds T5Gemma2-tokenizer IDs into EG2 [code]
`c5_eg2_all_layers_cache.py` tokenises `"summarize: " + passage` with the **T5Gemma2-270m tokenizer** and passes those IDs to `model.language_model` of EG2. EG2 uses **PLE**, so token-ID-indexed embeddings are re-injected **at every layer**. A mismatched ID is therefore not a layer-0 error that later layers smooth over; it corrupts that position at every depth [inference from the architecture as described in §2.1 of the request]. The mismatch rate is unknown and I could not measure it (data absent).

### 1.6 Prior probing precedent predicts saturation for lexical probes [measured]
D-017 (B1 probing, an earlier encoder): layer 0 reached **99.57%** on token class and **100%** on numbers. Labels that are a deterministic function of token type are decodable from the embedding layer. With PLE re-injecting token identity everywhere, curves for "surface frequency" and "numeric" are likely to be **flat and near the ceiling at all layers**. That is uninformative about layer roles [inference].

---

## 2. Answers to §13 Q1–Q10

### Q1. Layer role probing design — **disagree (as designed); conditional with redesign**
Evidence:
- Surface-frequency and numeric/date labels are functions of token type. Per §1.6 they will saturate from layer 0, so the curve cannot distinguish layers.
- The "within-document label permutation" control yields roughly chance accuracy by construction. `acc_true − acc_perm` is just "above chance". It does not penalise token-identity memorisation, which is what Hewitt & Liang control tasks are designed to do.
- With class weights on imbalanced labels, plain accuracy is the wrong metric.
- Slot overlap uses labels derived from the summary, so it measures **salience/copy-worthiness**, not "slot information". It also has span-matching ambiguity when a string occurs more than once.
- Sentence position is confounded with absolute token position (RoPE) and with truncation at 1024.
- Missing probes:
  - **Token-identity and neighbour reconstruction** (can layer L recover token t, t±1, t±2?). This is what a decoder needs in order to copy names and numbers.
  - **Document discriminability** of the memory (retrieval accuracy among val docs, and inter-doc cosine of adapter outputs). This is the direct mechanistic counterpart of Δshuffled.
  - **Per-layer activation-scale and outlier-dimension statistics.** Gemma-family mid-layer hidden states can carry massive outlier dimensions. That affects both probes and adapters [inference].
- Causal ablation does not need to come first. The causal test belongs inside B0: knock out memory positions and measure the CE of the aligned target tokens.

Next steps:
1. Drop surface-frequency as a primary probe. Report every probe as **probe − token-type baseline** (majority label per token type from train) and against **layer 0**, using balanced accuracy or AUROC with a doc-level bootstrap.
2. Replace the permutation control with a **Hewitt–Liang type-level control task**. Add token-position-residualised sentence position, and an in-context numeric role label (date vs amount vs count for the same digit tokens).
3. Add two cheap probes that are more relevant to decoding: token(t±k) identity recoverability and doc-discriminability. Run all probes on the **native-tokenizer** cache.

### Q2. Stage A interpretation — **disagree** with "frozen decoder bottleneck" as an established conclusion
Evidence:
- §1.1: neither model fit its training data (mT5 train CE ≥ 5.16; UMT5 train ≈ val ≈ 8.3). Selectivity cannot be expected from a model that has not fit, so the result is inconclusive.
- With 5 val docs and 1 seed, the power is negligible. A Δshuffled of 0.10–0.19 is within noise for n = 5.
- §1.2: Δzero is off-distribution, so "uses memory existence/length" is not supported either.
- §1.4: mT5 shows 18/23 positive signs, a weak hint under non-independence.
- D-110/D-111 should therefore be read as **"STAGE_A_INCONCLUSIVE_UNDERFIT"** rather than "PARTIAL_MEMORY_USE_NO_CONTENT_SELECTIVITY". I am not asking for the decision records to be rewritten. This is the reviewer's reading.

Next steps:
1. In the B0 report, state explicitly that Stage A was underfit (train CE values) and inconclusive.
2. Re-run the frozen-decoder condition **inside B0** as its control arm, on the same native cache, docs and seeds, rather than re-running Stage A separately.
3. Retire Δzero (post-adapter zeros) as evidence of memory use and replace it with mean-memory.

### Q3. B0 single layer (layer19) — **conditional**
Evidence:
- §1.3: layer19 is a winner's-curse pick on 5 val docs, confounded with seed, and has a low Δshuffled (0.030).
- One layer is acceptable *if* B0's question is "can decoder adaptation produce selectivity at all?". In that case the right layer is the one with the **least ambiguous representational content**, not the noisiest CE winner.
- Adding layers 5 and 12 to B0 turns a diagnosis into a sweep before the metric has been validated. I would not do that.

Next steps:
1. Keep B0 to **one EG2 layer**, pre-registered before the run. Layer19 is acceptable for continuity, but record it as an arbitrary fixed choice rather than "best".
2. Make the *variable* in B0 the decoder condition, not the layer: **frozen adapter-only vs adapter + decoder LoRA vs native mT5 encoder + same LoRA (positive control) vs memory-free LoRA (negative control)**.
3. Use the same seed set for all arms. Never derive the seed from the layer.

### Q4. B0 DoD — **disagree; strengthen and re-anchor**
Evidence:
- 20 train docs × 100 steps = 5 epochs. Learning a *generalising* copy pathway that shows up on unseen val docs is unlikely at this budget [inference]. A STOP on this run would be a false negative, and the stop rule in §7.4 ("CI lower ≤ 0 → bridge 종료", i.e. end the bridge) would then close the track on underpowered evidence.
- An absolute 0.10-nat threshold over the whole sequence has no anchor. mT5 Stage A already reached 0.189 (layer17) frozen on 5 docs.
- "3 seeds all positive" passes 1 time in 8 under the null.
- A paired bootstrap over 20 docs ignores seed variance.
- Sequence-mean CE dilutes the signal: most summary tokens are predictable from the LM prior. Content selectivity should concentrate on target tokens that are **copyable from the source** (numbers, names, slots).

Next steps:
1. **Data/budget**:
   - train = first 300 of P0 train, which matches existing D-109 coverage, re-extracted with the native tokenizer;
   - val = P0 val docs **excluding** the 5 Stage A val docs, n = 100;
   - steps ≈ 900 (≈ 3 epochs), lr fixed in advance;
   - LoRA r = 8 on decoder self- and cross-attention q/k/v/o;
   - seeds 20261108/09/10 for every arm.
2. **Primary metric**: Δshuffled_copy = mean over val docs of (CE_shuffled − CE_real), restricted to target tokens whose surface string appears in that doc's source. Use **multiple derangements** (≥ 5 random, length-bucket-matched) and a **hierarchical bootstrap over docs × seeds**. Secondary metrics: full-sequence Δshuffled, CE_real vs CE_memfree, and Δmean-memory.
3. **Pre-registered gates**:
   - *Metric validity:* the native-encoder positive control must show Δshuffled_copy CI lower > 0. If it does not, the metric or budget is invalid → fix it; do not STOP the track.
   - *PASS:* the bridge LoRA arm has Δshuffled_copy CI lower > 0, **and** reaches ≥ 25% of the native control's Δshuffled_copy, **and** beats the frozen arm (paired CI lower > 0), **and** has CE_real < CE_memfree (CI lower > 0).
   - *STOP:* the positive control is valid **and** the bridge arm's Δshuffled_copy CI upper is below 10% of the native control's.
   - *In between:* a weak signal. Record it and do not auto-advance.
   - Generation (20 docs): non-empty ≥ 19/20, EOS ≥ 15/20, plus a repetition rate. These are sanity checks only, not gates for selectivity.

### Q5. B1 layer set — **defer**
Evidence:
- B1 is meaningless until B0 validates the metric.
- Layers 5/9/12 were chosen with **T5Gemma2-teacher** or **T5Gemma2-bridge** evidence (D-109 itself says "mT5 layer 선택 근거 아님", i.e. not a basis for choosing mT5 layers).
- Layer19 rests on a noisy CE pick.
- Twelve runs (4 layers × 3 seeds) at 20 docs is too little data per run and too many comparisons for 20 docs.

Next steps:
1. If B0 passes, choose B1 layers **a priori by depth spread** (e.g. 6, 12, 18 plus the B0 layer) and justify them with the corrected probes, not with T5Gemma2 cosine.
2. Use the B0 budget (300/100, ≈ 900 steps) and the primary metric Δshuffled_copy. Correct for multiple comparisons (Holm) against the B0 layer.
3. Do not add 6/8/10/11 in a dense sweep. Adjacent layers will be indistinguishable at this n [inference].

### Q6. B2 model comparison — **conditional**
Evidence:
- Holding the layer fixed does isolate the decoder, but **optimisation is a confound**: UMT5 learned nothing in Stage A (train ≈ val ≈ 8.3), so a single shared lr/scale is not a fair comparison.
- The scale of the native encoder output differs between models, and the adapter's LayerNorm output may suit one model and not the other [inference].
- Cross-model CE is not comparable because the tokenizers differ (request §0.1). Within-model *differences* (Δshuffled_copy relative to that model's own native control) are comparable.

Next steps:
1. Run a per-model mini lr sweep (3 values) on a **train-internal dev split** before the comparison. Match the adapter output scale to each model's native encoder-output RMS.
2. Compare models on the **normalised** selectivity (Δshuffled_copy_bridge / Δshuffled_copy_native) and on generation metrics computed by the same `eval/slot_verify.py` slot extraction and the same char-level F1, never on raw CE.
3. Keep "no difference → mT5" as the default tie-break. That is a reasonable simplicity prior.

### Q7. Stage C entry — **disagree** with including Stage C in this plan
Evidence:
- Stage C's DoD (F1 ≥ .45, grounded ≥ 50%, EOS ≥ 60%) sits far below A1 native matched val100 (.6552 / 100% / 100%). Passing it would not create a product candidate, and the request itself admits this (§10).
- `grounded` is no-new-only, with no preservation check (D-108 errata), so "50%" is a weak bar.
- No product benefit has been quantified. mT5-small's ~300M parameters are dominated by its ~250k-vocabulary embedding/LM head [inference from public model configs, not verified here]. A "lightweight decoder" may not save memory compared with A1 T5Gemma2-270m-270m.

Next steps:
1. Remove Stage C from this plan. If B0–B2 pass, write a new decision record that includes a **resource model** (total resident params/RAM/latency of EG2 + mT5 decoder vs A1) before any 300-doc run.
2. Any future Stage C must be a **paired non-inferiority test against A1** on matched val100, with paired bootstrap, after the metric audit (Q8).
3. Keep 20-doc generation in B0/B1 as sanity checks only.

### Q8. Metrics — **agree** that grounded must be fixed and entity audit must precede any Stage C
Evidence:
- D-108 errata: `grounded` = no-new-only, so preservation is unchecked.
- D-107 preservation values (.3618–.3656) show preservation is exactly where bridges fail.
- The production verifier must stay unmodified (SHA in request §2.4).

Next steps:
1. Implement a **separate, eval-only** preservation metric (source-slot recall in the summary, gold-slot recall) in a new evaluation module. Do not edit `eval/slot_verify.py`.
2. Run the entity audit on A1 val100 outputs first, so the reference is re-scored under the corrected metric.
3. For B0/B1 use CE-based gates, not grounded/F1, to keep metric fixes off the critical path.

### Q9. T5Gemma2 reopening — **agree: keep D-108 STOP**
Evidence:
- D-107: best bridge .4074 / 12% / 69% vs A1 .6552 / 100% / 100%.
- Slot-repair ceiling .3203.
- 3/3 STOP in D-108.
- External K/V separation is untried, but no evidence suggests it could close a 0.25 F1 / 88-point grounded gap.

Next steps:
1. Do not reopen. If an external K/V split is ever proposed, it requires a new decision record with its own pre-registered DoD and kill criterion.
2. Note in the B0 report that a B0 positive result does **not** transfer to T5Gemma2. The decoders differ in their cross-attention design.
3. Focus the remaining budget on the A1 metric audit (D-108 default) and the narrowed B0.

### Q10. Priority — **conditional**: B0 first, minimal diagnostics in parallel, role probing deferred
Evidence:
- B0 gates everything downstream. The plan already says role probing must not select B0's layer (§4).
- Role probing as designed is mostly saturated lexical curves (§1.6).
- The tokenizer question (Q5 core) blocks both, so it must come first.

Next steps:
1. **Day 0 (≤ 1 CPU-h):** tokenizer mismatch audit (rule in §3) plus per-layer activation RMS/outlier stats on the 400 P0 docs.
2. **Then the revised B0** (≤ 8 CPU-h including native re-extraction and the 4 arms × 3 seeds).
3. **Delete first:** Stage C (from this plan) and the surface-frequency probe. Defer B1/B2 and the redesigned role probing until B0 passes.

---

## 3. Core question 5 — tokenizer mismatch

**The existing cache is acceptable only as a historical screening artefact. B0 must use a native-tokenizer cache.** Stage A does not need a standalone re-run; its frozen condition is reproduced as B0's control arm on the native cache.

Pre-registered rule for the audit (no training, tokenizer-only plus one forward pass):
- Tokenise the same `"summarize: " + passage` for the 300 train + 100 val P0 docs with both tokenizers, and compute:
  - share of documents with identical ID sequences;
  - per-token mismatch rate after alignment;
  - mismatch rate restricted to digits and `extract_slots` spans.
- If the per-token mismatch is ≤ 0.5% **and** there are zero mismatches inside digit/slot spans, the old cache is *screening-acceptable*. Stage A numbers may still be cited, with that caveat. Otherwise, mark Stage A layer rankings as **unreliable**.
- In both cases, B0/B1 and the probes use the native cache. One forward pass per document already extracts every layer, so the cost is small.
- Also decide and record whether the `"summarize: "` prefix stays. EG2 has its own embedding-task prompt conventions. Keep the prefix identical across all arms.

---

## 4. Top methodological defects (ranked)

1. **B0 lacks the controls needed to attribute anything to decoder adaptation.** There is no frozen arm at the same data, no native-encoder positive control, and no memory-free LoRA. It changes LoRA, data size and tokenizer at once.
2. **Underpowered B0 with a hard STOP.** 20 docs / 100 steps can produce a false-negative termination.
3. **Stage A misread.** Underfit (train CE ≥ 5.16 for mT5, ≈ 8.3 for UMT5) and an off-distribution zero control mean that Stage A cannot support "frozen-decoder bottleneck" or "uses memory existence/length".
4. **Selectivity metric dilution and pairing artefacts.** Sequence-mean CE, a single cyclic derangement and no length matching all weaken the measurement.
5. **Layer–seed confound and winner's-curse layer pick** (`seed = 20261108 + layer`; layer19 chosen from 23 noisy estimates on 5 docs).
6. **Tokenizer/PLE contamination of the cache** at an unknown rate.
7. **Probe design saturates by construction** (type-determined labels, a permutation control, accuracy under class imbalance).
8. **Model-comparison optimisation confound in B2** (UMT5 did not train under shared hyperparameters).
9. **Stage C bar below the product reference** and no resource model justifying EG2 reuse.

## 5. Must-fix before any run
- MF1: Tokenizer mismatch audit plus a native re-extraction for B0 docs and layers.
- MF2: Add B0 arms: frozen adapter-only, adapter + LoRA, native-encoder + LoRA (positive control), memory-free/mean-memory LoRA (negative control). Use identical seeds and data, with seeds not derived from the layer.
- MF3: B0 data/budget 300/100 (val excluding the Stage A docs), ≈ 900 steps, pre-registered lr and LoRA rank.
- MF4: Primary metric Δshuffled_copy with ≥ 5 length-matched derangements and a docs × seeds hierarchical bootstrap. Replace post-adapter zeros with mean-memory.
- MF5: A pre-registered DoD anchored to the native control (§2 Q4), with a "metric invalid → fix, not STOP" branch.
- MF6: Remove Stage C from this plan. Any future Stage C needs a new decision record, a resource model, the metric audit, and a non-inferiority test against A1.

## 6. Maximum allowed cost
- Diagnostics: ≤ 1 CPU-h. B0: ≤ 8 CPU-h wall-clock, including re-extraction. Hard cap for this plan before a new decision record: **≤ 10 CPU-h**.
- If B0 passes, B1 + B2 together get ≤ 12 CPU-h under a new decision record.
- Any instability (non-finite loss, OOM) gets one retry with r = 4. A second failure → record the failure and STOP B0.

## 7. Relation to the A1 native product path
- A1 native pilot300 stays the frozen fallback/reference (D-108). This plan is **exploratory research**, and its numbers must not be tabulated as product alternatives to A1.
- The D-108 default (metric/A1 audit) should proceed **in parallel** and takes priority if resources conflict. It also benefits this plan (Q8).
- Test 163 remains sealed. Nothing here proposes using it or P1 data. No gate change is claimed as approved. All proposed gates above are reviewer recommendations awaiting a decision record.

## 8. Top additional experiments (all P0, no test, no P1)
1. **Tokenizer/PLE audit**: mismatch rates as in §3, plus per-layer RMS/outlier dims. Data: 300/100 P0. No seed. Stop condition: none (diagnostic).
2. **Revised B0 with 4 arms** (§2 Q4). Data: 300 train / 100 val (excluding Stage A val docs). Seeds 20261108/09/10. Targets: F5 summaries. Metric: Δshuffled_copy. Stop conditions as in Q4.
3. **Memory knock-out inside B0** (inference-only on the trained B0 arms): zero → mean-replace the memory positions whose source span matches a target slot, and measure the CE change on those target tokens vs on random positions. This provides the causal link that the probes cannot.
4. *(Only after B0 passes)* redesigned role probes: type-baseline-residualised slot salience, contextual numeric role, token(t±k) identity, doc discriminability. Native cache, doc-level bootstrap, Hewitt–Liang control.