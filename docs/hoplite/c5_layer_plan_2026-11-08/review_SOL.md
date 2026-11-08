# Independent C5 layer-plan review — Sol 6.1

Date: 2026-11-08

Reviewer: OpenAI Sol 6.1 (`openai/gpt-6.1-sol`), working independently without subagents or additional models.

Repository: `mandutt/unigem`; review basis: current `origin/main`.

## 1. Review provenance and scope

Executed, in order, `git fetch origin` and `git pull --ff-only origin main`. Both succeeded; pull reported **Already up to date**. Resulting workspace HEAD and `origin/main` were both:

```text
bb8bf702cbff4c73129098d4b660784be289fd75
```

The checkout retained its existing `hoplite/syrakousai-e66237db` branch, pointing at that same commit; no branch switch was necessary. The worktree was initially clean. The request's `949df7a` is its authoring reference, not this review's base.

I read the **entire 618-line** `reports/EXTERNAL_REVIEW_C5_LAYER_PLAN_2026-11-08.md`, in the requested line ranges, including the full text returned after output pagination. I inspected the Stage A and all-layer result JSONs, their reports, the cache/probe runners, generation/metric code, and relevant decision records. Other reviewers' report files and their answers were not used; D-107/D-108 are treated as established decision history, not as substitutes for this analysis.

No training, model inference, new model evaluation, external API experiment, or dataset inspection was performed. In particular, I did not open the master examples or sealed test examples/IDs. Model weights and EG2 feature-cache directories referenced by the request are not present in this checkout, so I could not measure native-versus-legacy tokenizer differences or reproduce inference. This is a document/artifact/code review. The only repository-file write is this report.

`eval/slot_verify.py` was unchanged; its inspected SHA256 is:

```text
a262cee0cd25307a74f3a87995624e2999b47daed9294000f036d27ea1869d03
```

**All experiment and gate revisions below are recommendations for prospective registration and approval, not changes already approved or implemented.** P1, external APIs and test 163 remain out of scope. T5Gemma2 bridge training remains closed.

## 2. Executive decision: NARROW

Recommend **one corrected B0 diagnostic package only**, including its necessary native-input audit and matched frozen-decoder control. Do not currently authorize the full role-probing/B1/B2/C ladder.

The valuable question is local: **at EG2 layer19, under the same input pipeline and training budget, does enabling decoder adaptation improve useful held-out memory selectivity compared with adapter-only training?** The proposed B0 measures selectivity after adaptation, but lacks the comparison needed to attribute any change to adaptation. Comparing its 20/20, three-seed run with the old 5/5 Stage A changes several variables simultaneously.

The biggest must-fix is therefore **a contemporaneous, matched adapter-only arm**, followed closely by a length-controlled wrong-memory ablation. Merely adding more layers or a role probe does not repair this causal comparison.

The existing numbers support a small diagnostic, not a product continuation:

| Established result | Interpretation retained in this review |
|---|---|
| mT5 Stage A: layer19 real CE 6.623; zero delta 18.4–19.3; maximum shuffled delta .189 | Frozen-adapter screening did not establish robust document-content selectivity. It did not identify the unique bottleneck. |
| UMT5 Stage A: layer12 real CE 8.185; zero delta 3.5–4.0; maximum shuffled delta .009 | Same limited screening conclusion; native-token CE is not directly comparable with mT5 CE. |
| EG2 teacher cosine: MLP1536 layer5 .7927, layer9 .7910, layer12 .7747, projection layer24 .7102 | Alignment to **base T5Gemma2 encoder hidden**, not a decoder-utility or semantic-role ranking. |
| A1 native matched val100: F1 .6552, grounded 100%, EOS 100%; val161 F1 .6576 | Keep the frozen native fallback/reference distinct from experimental bridges. These figures are not a fresh product approval. |
| Closed bridge: best F1 .4074, grounded 12%, EOS 69%; grounded-100 repair ceiling .3203 | D-107 failed its registered DoD; D-108 STOP remains in force. |

The first three rows were checked against the raw JSON artifacts. The A1 matched figures are accepted as verified in the request and decision record; I did not recompute them. The closed bridge's .4074/.12/.69 figures also appear in its raw val100 metrics JSON.

## 3. Evidence map

References below use repository-relative paths and line numbers at the reviewed commit.

- **[R]** `reports/EXTERNAL_REVIEW_C5_LAYER_PLAN_2026-11-08.md`: role probes lines 211–257; B0 274–329; B1 333–371; B2 375–408; C 412–432; risks 464–476; questions 480–538; runner not yet implemented at 594.
- **[A]** `runner/c5_mt5_layer_probe.py`: labels 79–82; memory/masks 85–107; aggregate-only output 108–118; initialization seed `20261108 + layer` at 133; optimization 135–155; first-N document selection 195–199; frozen parameters 202–209. Raw results: `reports/provenance/C5_b1d/mt5_layer_probe.json` and `umt5_layer_probe.json`, especially `/layers` entries for layers19 and12 respectively. Neither stores per-document CE/deltas.
- **[C]** `runner/c5_eg2_all_layers_cache.py`: native tokenizer loaded at 73, T5 tokenizer at 74, but actual source IDs come from **`t5_tok`** at 102–110; prefix is `summarize: ` at 30; source cap 1024 at 59; NPZ fields 122–129; metadata 139–147 does not identify the actual tokenizer/prompt/token IDs/offsets.
- **[S]** `reports/C5_EG2_ALL_LAYER_SWEEP_2026-11-08.md`, lines 9–15, 20–46, 61–72; raw `reports/provenance/C5_b1d/all_layers_pretest.json`, `/layers`: layer5 MLP1536 .7927 versus layer9 .7910, with a different teacher/objective from Stage A.
- **[G]** `runner/c5_b1d_generate.py`, lines 129–147: verifier report is available, but output `grounded` is **`not rep.new`**; lines 164–177 aggregate F1, grounded, EOS and repetition. `reports/provenance/C5_b1d/generation_val100_b2_layer12_300_ss_slot.metrics.json` records F1 .407355, grounded .12, EOS .69, repetition .405442.
- **[V]** `eval/slot_verify.py`, lines 95–117: NFKC normalization/canonicalization and normalized-text spans; 164–188: preservation, missing and new are computed, and `rejected=bool(missing or new)`. Thus the generator's grounded statistic is weaker than the production rejection rule. `eval/slot_verify_084a.py`, lines 230–247, likewise keeps missing separate from its no-new grounded field.
- **[F]** `runner/c5_a2null_eval.py`, lines 69–77: reported character F1 is **whitespace-stripped bag-of-characters F1**, not an order-sensitive factuality measure; repetition is separately defined at 80–85.
- **[L]** `runner/c5_b1d_b2.py`, lines 38–54: old T5Gemma2 LoRA attachment filters `model.decoder.` and `q_proj/k_proj/v_proj/o_proj`. This is not a ready-made mT5/UMT5 attachment implementation.
- **[D]** `docs/decisions.md`, D-107–D-111: closed bridge outcome, native fallback/reference status, scope corrections and exploratory Stage A results. D-108's earlier review conclusions are governance context only.

## 4. Q1–Q10 answers

### Q1. Layer role probing — **conditional**

**Verdict.** A useful accessibility survey, but insufficient as written to distinguish the four proposed information classes. A linear probe is an appropriate starting point; causal ablation need not precede it. Use EG2's native tokenizer. Do not call a successful label predictor a demonstrated functional layer role, or a failed probe proof that the information is absent.

**Evidence and reasoning.** [R] 227–235 defines correlated labels: document frequency is a token-type property; numeric/date labels are substantially readable from token spelling; summary-slot overlap is mostly a subset of recognizable source slots; sentence position correlates with absolute token position and the summary lead bias. PLE makes persistent lexical information unsurprising. Within-document label permutation alone does not control token-type memorization, positional shortcuts, or document-specific class proportions. “One probe, any layer has CI lower >0” also searches many hypotheses. Native offsets must align with [V]'s **NFKC-normalized** source, not summary offsets or unnormalized passage offsets.

**Next steps.**
1. Use the future probe protocol in section 7: layer0 baseline, spelling/type/frequency/position baselines, conditional numeric-versus-slot comparisons, document-clustered inference and multiplicity control. Keep source-only hidden extraction separate from reference-derived labels.
2. Audit source character spans, Unicode normalization, prompt offset, repeated slot occurrences, truncation, special tokens and class counts before fitting. Report slot overlap as **reference-slot accessibility**, not NER or full grounding; report negative probes as “not detected by this probe/budget.”
3. Defer this full survey until after B0. If later run, begin with logistic regression only; causal slot interventions are a follow-up for decoder use, not a prerequisite for an honest accessibility claim.

### Q2. Stage A interpretation — **disagree** with the bottleneck attribution

**Verdict.** Agree with “content selectivity was not established in this screening condition”; disagree with “the frozen decoder has been identified as the bottleneck.” Small sample/low power is one plausible explanation, not an established alternative explanation either.

**Evidence and reasoning.** [A] uses five validation documents, one cyclic donor assignment and aggregate CE only. The shuffled donor carries its own sequence length and all-ones mask, so content and length change together. Real-versus-zero keeps length fixed but compares learned nonzero memory with an extreme zero tensor: it establishes sensitivity to memory values/distribution, not specifically exploitation of length or useful semantic content. Teacher forcing may hide memory dependence by supplying most of the target prefix. In addition, each layer has a **different initialization seed**, so Stage A layer differences are not clean layer effects. Layer19's own shuffled delta is .03023, not the cross-layer maximum .18893.

**Next steps.**
1. Retain Stage A as legacy exploratory evidence; qualify both causal bottleneck and memory-length claims.
2. Replace the single cyclic ablation with the prospective, equal-shape, multiple-donor comparison in section 6 and retain per-document/per-token losses.
3. Compare frozen versus adapted decoder under the same native-input 20/20 protocol. Do not fabricate CIs from the stored aggregate JSON or infer that a small non-significant difference proves equivalence.

### Q3. B0's single layer — **conditional**

**Verdict.** Layer19 is a defensible **fixed anchor** for a minimum local diagnostic. Do not put layers5/12 into B0 by default. A positive controlled result at one layer is informative; a negative result cannot eliminate other layers, models, interfaces or adequate optimization budgets.

**Evidence and reasoning.** [R] fixes layer19 before role results, which prevents one source of adaptive selection. But it was selected by the smallest real CE in a 23-layer, seed-confounded screen, not by the strongest selectivity. The proposed 20/20 LoRA run and old 5/5 frozen run are not a treatment/control pair. Full decoder q/k/v/o adaptation can improve language modeling as well as cross-attention, so it supports a decoder-adaptation claim only with the matched comparison, not a uniquely cross-attention-bottleneck claim.

**Next steps.**
1. Fix layer19 without promoting it to “best layer,” and run the two-arm, three-seed B0 recipe in section 6.
2. Assert explicit decoder-only LoRA attachment and matched adapter initialization, example order, targets, optimizer settings and steps; do not reuse [L]'s T5Gemma2 naming filter unchanged.
3. Treat failure as an operational stop for this tested recipe/budget. Consider a different anchor only under a new, explicitly bounded decision, not an automatic rescue sweep.

### Q4. B0 DoD — **disagree** as a sufficient diagnostic

**Verdict.** Keep .10 native-token CE as a prospectively chosen screening effect size, not as a validated practical threshold. Positive directions in three seeds and a document-level CI are sensible safeguards, but the proposed DoD lacks the treatment contrast, useful-real-memory improvement and an honest inconclusive category. Twenty documents and 100 steps can detect a large local effect; they do not guarantee adequate power or convergence.

**Evidence and reasoning.** [R] 308–322 simultaneously treats CI lower ≤0 as bridge termination and .00–.10 as discretionary weak evidence. More importantly, an increased shuffled-minus-real gap could result from making wrong-memory outputs worse without improving correct-memory outputs. Three seeds on the same 20 documents are not 60 independent observations. Five generations and EOS 3/5 provide little protection against collapse. A finite gradient is not evidence of sufficiently optimized adaptation.

**Next steps.**
1. Register the effect, adaptation-interaction and correct-memory-gain endpoints defined in section 6, plus fixed dropout/evaluation/checkpoint policy, before any run.
2. Bootstrap paired document clusters after averaging within document over seeds/donors; show each seed separately. Save losses and generation for all 20 validation documents, not just five conveniently inspected examples.
3. Distinguish pass, weak, negative and inconclusive outcomes. No automatic B1 for the latter three, no post-hoc threshold relaxation, and no claim of universal bridge impossibility.

### Q5. B1 layer set — **conditional**

**Verdict.** The predeclared 5/9/12/19 set is a reasonable bounded sensitivity study **after** a corrected B0 pass. Four layers × three seeds is not excessive computationally, but 20 documents remain the limiting statistical resource. Do not add 6/8/10/11 now.

**Evidence and reasoning.** [S] makes layer5 a useful diverse proxy candidate, not a proven mT5 winner. Layer9 adds a nearby historical comparator; layer12 is also UMT5's exploratory anchor; layer19 is the fixed mT5 anchor. The .0017 teacher-cosine difference between5 and9 supplies no justification for a dense neighborhood sweep. [R] 361–365 allows selection on either CE or selectivity, increasing winner selection and potentially accepting a lower-CE, content-insensitive layer.

**Next steps.**
1. Keep the four candidates fixed, reuse layer19 runs only if the full B0 recipe is unchanged, and use paired seeds/initialization/order across layers rather than [A]'s seed-plus-layer rule.
2. Make corrected selectivity a prerequisite; use real CE/generation as prespecified secondary or non-degradation criteria, not an unrestricted “either metric wins” rule. Adjust the three candidate-versus-anchor comparisons for multiplicity.
3. Freeze a winner before a disjoint, within-round validation confirmation; disclose that historical validation reuse prevents calling it a pristine holdout. If gains do not replicate, retain19 and do not expand the layer set.

### Q6. B2 model comparison — **conditional**

**Verdict.** Fixing the same layer removes the obvious assigned-layer confound and permits a **conditional model-package comparison at that layer**. It is not a factorial estimate of model main effect, and it cannot estimate model×layer interaction. Generated-text quality is the appropriate primary cross-model comparison.

**Evidence and reasoning.** [R] correctly rejects comparing mT5-layer19 against UMT5-layer12 as a pure model effect. However, selecting L* on mT5 first can favor mT5's interaction with that layer. Furthermore, **CE differences/deltas per native target token are also tokenizer-scaled**, not just absolute CE. “UMT5's ΔCE is larger” is not a sufficient cross-model winner criterion. Same steps/seeds do not imply equal processed target tokens, effective LoRA capacity or equivalent token-based generation limits.

**Next steps.**
1. Keep B2 deferred. If later run at L*, describe its conclusion as conditional and compare the same documents' decoded-text F1, audited slot precision/recall, entity errors, EOS, repetition, length and latency, with paired uncertainty.
2. Keep CE/selectivity as within-model diagnostics; optionally report summed NLL differences divided by the same reference UTF-8 byte count as a tokenizer-length-normalized secondary diagnostic, not a fully calibrated replacement for generated quality.
3. If a general model-versus-layer claim is actually needed, use the prospective 2×2 design in section 7 (both models at layers12 and19). Otherwise narrow the claim instead of paying for a factorial. Any model choice still includes tokenizer/pretraining differences, not an isolated architecture effect.

### Q7. Stage C entry — **defer**

**Verdict.** A 300-document learning-curve step may eventually be justified; it is not justified now merely by passing B2's CE/EOS conditions. Twenty-document generation is a useful early futility screen, not proof that scaling cannot work. Compare A1 on matched allowed validation IDs **before** spending on C.

**Evidence and reasoning.** [R] 426–432 explicitly makes C non-product, appropriately. Its .45/50%/60% thresholds are nevertheless substantially below A1's .6552/100%/100%. The closed bridge history also shows that teacher-forced progress can fail to transfer to free-running behavior. Neither a proxy selectivity win nor a relative mT5/UMT5 win establishes a worthwhile product tradeoff.

**Next steps.**
1. Review matched A1, bridge, lead-sentence/source-copy baselines and audited generation from the existing permitted validation pool before proposing C; use the section 7 specification for any new comparison.
2. Require reproducible selectivity **and** useful generation, metric/entity audit, a stated quality/latency/memory tradeoff hypothesis, and a fresh decision/budget before C. Do not require UMT5 to win just to permit mT5 research scaling.
3. If C is later authorized, preregister its train300/val100, three seeds, gold target, fixed training/checkpoint budget and quality/futility criteria. Keep it exploratory; no product promotion or test access follows automatically.

### Q8. Metrics — **disagree** that current C criteria are sufficient

**Verdict.** Audit and separate metric meanings before C, and before using grounded results to select B1/B2 models. Do **not** silently patch the production verifier or reinterpret historical grounded percentages as preservation. Entity audit is required before any product-relevance claim.

**Evidence and reasoning.** [V] already computes preservation and rejects missing **or** new slots. [G] reports only absence of new slots as grounded. Thus the needed first fix is to the experimental measurement contract, not an assumption that production lacks missing-slot logic. A slot-free or heavily shortened output can score grounded while omitting required information. [F]'s bag-character F1 can also reward shared character inventory without correct ordering, relations or facts. The reported closed bridge repetition .4054 reinforces the need to inspect generation, not F1 alone.

**Next steps.**
1. Preserve production code/hash and legacy `grounded_no_new` reporting; add separately named source-slot preservation, reference-required-slot recall, new-slot precision/rate, slot-free/nonempty rates, and rejection counts in a future versioned evaluation artifact.
2. Audit names, organizations, numbers/dates and relation/attribution errors on a fixed, blinded P0 validation sample, with source/gold/output visible and system identity hidden. Treat regex slots as incomplete entity coverage; distinguish reference-required facts from every source fact.
3. Treat C's .45/50%/60% only as a proposed research milestone, not acceptable product quality. Any replacement gate or noninferiority margin needs prospective owner approval; no new gate is approved here.

### Q9. T5Gemma2 reopening — **agree** with maintaining STOP

**Verdict.** Keep D-107/D-108 closed. The untried external-K/V separation is a logically different hypothesis, not a reason to reopen this track within the current review. Focus the narrow diagnostic on mT5, with UMT5 conditional later.

**Evidence and reasoning.** [D] records the registered D-107 grounding failure and D-108 closure. [R] 175–178 openly distinguishes untried architectural changes from the unsuccessful shared-K/V bridge. Neither teacher-cosine layer5 nor different mT5 cross-attention establishes that a new T5Gemma2 bridge would meet the native reference. A1 native is a different, retained path, not permission to restart its bridge.

**Next steps.**
1. Preserve the stop record and frozen A1 pilot300 reference; do not relabel closed bridge experiments as active product candidates.
2. Do not schedule external-K/V training or layer5 T5Gemma2 B2 under this plan. Any future reconsideration requires a new decision record, explicit authorization, its own controls/budget and unchanged sealed-data boundary.

### Q10. Priority and deletion — **disagree** with default parallel execution

**Verdict.** B0 first; postpone the full role survey until a local decoder-use signal exists. The two are scientifically separable, but that does not make parallel work the best use of one CPU-only budget. **NARROW**, not blanket STOP and not approval of B0→B1→B2→C.

**Evidence and reasoning.** [R] 203–205 correctly prevents probe-driven B0 layer selection, but role probes cannot explain a negative B0 without a usable decoder endpoint. Both also depend on resolving native input provenance. The proposed full sequence incurs implementation/interpretation costs beyond raw fit times, while no B0/B1/B2 LoRA runner yet exists ([R] 594).

**Next steps.**
1. First perform E0 (native-input/wiring audit), then E1 (matched B0), as specified below. Share cache provenance work, not a broad new layer study.
2. Delete the **default parallel full role-probing/optional MLP sweep** from the immediate work package; defer B1/B2 and remove automatic C progression. Reconsider role probing only for a specific surviving question or separately budgeted representation study.
3. Enforce the section 8 cap. A positive E1 earns a new decision review for bounded B1, not automatic authorization; weak/negative/inconclusive E1 ends this execution block without more rescue sweeps.

## 5. Highest-priority methodological defects

Ordered by how directly they threaten the stated causal diagnosis:

1. **No matched intervention contrast.** A-versus-B0 changes document counts, initialization, seeds and possibly source tokenizer as well as decoder trainability. A B0 success alone does not establish decoder adaptation as the cause.
2. **Wrong-memory intervention is not content-only.** [A] changes donor length/mask and uses one fixed neighbor. Zero memory is an out-of-distribution reference; its large loss does not identify useful memory information or the role of length. Multiple donors and equal-shape comparisons are essential.
3. **Reliance is not necessarily usefulness.** Raising wrong-memory loss can pass a gap criterion without improving real memory; teacher forcing can hide generation failure. Correct-memory CE and unforced outputs need their own checks.
4. **Input and optimization are underspecified.** The actual cache uses T5 IDs, despite loading a native tokenizer. B0 omits LoRA rank/alpha/dropout, precise module scope, separate learning rates, schedule, checkpoint rule and training/evaluation mode. Gradient presence cannot rule out an undertrained or misattached adapter.
5. **Statistical units and adaptive selection are not fixed.** Tokens, donors and repeated seeds are not independent documents. Stage A confounds layer with seed; B1 offers multiple endpoints; B2 inherits mT5-selected L*. Validation has already been used repeatedly. None is repaired simply by “1,000 bootstraps.”
6. **Probe labels do not uniquely identify roles.** Type identity, numeric spelling, slot membership and position/lead bias overlap. Within-document random labels and one significant curve do not disentangle them. Span/normalization errors could dominate subtle layer differences.
7. **Research and product endpoints can be mistaken for each other.** No-new grounded, bag-character F1 and EOS are insufficient for preservation/entity correctness. A1 reference, exploratory EG2 bridge and any eventual product gate must remain separate.

## 6. First two experiments: exact narrow diagnostic proposal

These are proposed future experiments, **not executed in this consultation**. E0 and E1 together are the corrected B0 package. No exhaustive native Stage A rerun is required.

### E0 — Native-input provenance and external-memory wiring audit

- **Data:** only the fixed B0 train20/val20 drawn from the authorized P0 train/validation manifests; no master-dataset browsing or sealed examples. Use the existing first20 rule for comparability, publish selected allowed IDs/hashes, and flag near-duplicate train/validation sources. Do not choose examples by outcome. Use five of those validation examples for the forwarding equivalence checks.
- **Seeds:** deterministic tokenization; seed `20261108` for any randomized diagnostic. No fitting.
- **Target:** native EG2 token IDs/offsets for the same source text; for forwarding checks, the same mT5-native gold-summary labels used in E1.
- **Procedure:** compare legacy T5Gemma2 and EG2-native source tokenization on exactly the same text, prefix, special-token policy and 1024 cap. Record token/sequence mismatch rates, vocabulary/special-token identities, offsets, lengths, truncation and visible reference-slot coverage. A match in length alone is insufficient. Then extract native **layer19** only. Keep `summarize: ` fixed between E1 arms; record it as an explicit input choice, not an assumed optimal EG2 embedding prompt.
- **Wiring checks:** native mT5 encoder forwarding and externally supplied **identical native mT5 encoder memory** should yield matching logits/loss in evaluation mode within a preregistered FP32 numerical tolerance. Verify masks/labels/shifts/EOS IDs. At initialization, zero-output LoRA must reproduce the frozen-arm forward. Record exact attached modules and frozen/trainable parameter counts. A native-encoder ablation is a reference, not a requirement that an unfine-tuned summarizer already achieve good F5 quality.
- **Metrics:** mismatch/coverage tables, finite tensor/loss checks, external/native-path numerical agreement and module inventory. The legacy LoRA wrapper [L] must not silently attach zero modules or train an unused encoder.
- **Stop:** any unresolved input mapping, alignment or forwarding discrepancy blocks E1. Repair the harness prospectively; do not interpret a failed wiring check as a failed scientific hypothesis. If weights/tokenizers remain unavailable, stop here as blocked rather than guessing drift is harmless.

### E1 — Matched frozen-versus-adapted B0 at layer19

**Fixed data and fitting contract**

- **Data:** exactly E0's P0 train20/val20, fixed across all runs. Target is the gold summary, not A1 output and not T5Gemma2 hidden states. Native EG2 source tokenizer; mT5-native target tokenizer; source cap1024, target cap256 with EOS/truncation counts reported.
- **Seeds:** `20261108`, `20261109`, `20261110`; same adapter initialization and document order within each seed's paired arms. These vary optimization, not the validation sample size.
- **Model/layer:** mT5-small and EG2 layer19, fixed. EG2 and the base decoder are frozen except explicitly enabled decoder LoRA.
- **Arm F:** MLP512→512→512+LayerNorm adapter, decoder frozen. **Arm L:** identical adapter plus decoder self- and cross-attention q/k/v/o LoRA. This estimates the benefit of **decoder attention adaptation as a package**, not its unique self/cross mechanism.
- **Proposed fixed starting recipe:** LoRA r8/alpha16/dropout .05, adapter LR1e-3, LoRA LR1e-4, AdamW weight decay .01, gradient clipping1, batch size1, exactly100 updates/final checkpoint, no validation-based checkpoint selection. Those settings require registration; they are not validated optima. Assert decoder-only attachment, keep embeddings/LM head/encoder frozen, log dropout modes and schedules. Assert normal LoRA initialization behavior; not every LoRA factor must have a nonzero first-step gradient.
- Log first/last and intermediate train losses, gradient/update norms, trainable counts, time and memory. Persistent loss decline at step100 makes a null result budget-limited, not proof of adequate convergence; it does not authorize extra steps post hoc.

**Memory controls**

Use five prospectively seeded derangements per validation document, selected by a fixed source-length-bin rule, with no self or duplicate-source donor. Record donor IDs and source-slot overlap. Use the **same donor assignments** across arms/seeds and later layers/models.

For each recipient/donor pair, set `K=min(recipient_length, donor_length)` and crop **both** memories to K, using identical masks and the same target labels. This is an explicit equal-shape prefix intervention; measure and report evidence lost by cropping. Compare full real memory separately. Do not quietly compare cropped wrong memory against uncropped real memory, or claim the equal-prefix endpoint measures all full-document facts. Fix the policy before seeing results; if usable evidence coverage is inadequate, the diagnostic is not informative.

Zero memory at the same K remains a secondary pathology/reference control. Do not use token-order permutation as a substitute for wrong-document memory: without a memory-position mechanism, cross-attention to already contextualized vectors can be invariant to reordering memory rows.

For arm `a`, seed `s`, recipient `i`, average the paired wrong-minus-real loss across its donors:

```text
D[a,s,i] = mean_d( CE[a,s](wrong_d[:K], y_i)
                    - CE[a,s](real_i[:K], y_i) )
I[i]     = mean_s( D[L,s,i] - D[F,s,i] )
G[i]     = mean_(s,d)( CE[F,s](real_i[:K], y_i)
                       - CE[L,s](real_i[:K], y_i) )
```

CE here is nats per non-padding **mT5 target token**; all arms share that target sequence. `I` is the adaptation-associated selectivity gain; `G` guards against a gap created solely by worsening wrong-memory behavior. Also retain summed token NLL and slot-token versus non-slot-token losses where alignment is valid.

**Inference and generation**

Use 1,000 paired document-cluster bootstrap replicates, resampling the same 20 recipients across arms and averaging seeds/donors within each recipient first. Give seed-specific means/ranges and donor-assignment sensitivity separately; the bootstrap does not create more seeds/documents. State that intervals are conditional on this fixed donor protocol and cannot establish broad seed-population reliability.

Generate on all val20 for each arm/seed with fixed greedy decoding, native EOS, max_new_tokens256, no sampling or post-processing. Record nonempty, actual EOS, cap hits, repetition, character length/F1 and versioned slot diagnostics; inspect outputs rather than only their counts. On a fixed five-document subset, also generate with the prespecified wrong memory to check source dependence. The all20 generation endpoint, unlike teacher-forced CE, gets no gold prefix.

**Proposed decision table — approval still required**

| Result | Operational decision and permitted inference |
|---|---|
| Mean `D[L]` ≥.10; its paired 95% CI lower >0; each seed's mean positive; paired `I` and `G` lower bounds >0; generation safeguards pass | Local evidence that decoder adaptation helps this recipe. Eligible for a **new** bounded B1 decision, not product/whole-plan approval. |
| Both F and L show selectivity, but `I` does not support an adaptation gain | Frozen decoder is not established as the bottleneck under native 20/20 conditions. Prefer the simpler supported arm; do not credit LoRA merely for passing its standalone gate. |
| Positive gap below .10, or adaptation/real-memory gain not established | Weak/unsupported diagnostic. No automatic B1 or discretionary threshold relaxation. |
| Upper CI bound below .10 | Evidence excluding the chosen meaningful effect for this tested endpoint/recipe, subject to the stated interval limitations. Stop this branch. |
| CI spans zero and .10, seed directions conflict, optimization is clearly unfinished, or coverage is inadequate | Inconclusive/unstable/budget-limited. Stop this execution block without a universal no-bridge claim. |
| Wiring failure, nonfinite updates, OOM or collapsed generation | Technical failure or futility, not a clean bottleneck result; at most the one same-configuration technical retry allowed below. |

Proposed generation safeguards for diagnostic continuation: every seed has 20/20 nonempty outputs and at least 12/20 EOS; pooled-seed paired point estimates of bag-character F1, no-new rate and required-slot recall do not decline versus F, and mean repeated-4gram rate does not rise. Report the corresponding paired uncertainty; these point-estimate safeguards are not proof of noninferiority. Inspect both arms for collapse rather than accepting two equally broken generators. These replace the fragile 5-example checks **only if prospectively approved**. Meeting them is still far below product proof. Because .10 is an effect-size screen, a CI that crosses .10 is not automatically evidence against usefulness; an inconclusive run remains inconclusive even when operations stop.

### Tokenizer ruling

**Do not rerun all 23 layers × two models before B0.** The old cache is acceptable as an explicitly legacy, tokenizer-mismatched **screening** result. It is not acceptable as the matched causal baseline or a definitive layer ranking for native EG2 inputs.

Native-input layer19 Arm F is the necessary limited Stage A repeat, embedded in E1. It separates the adaptation treatment without paying for a broad screening repeat. Both E1 arms must use the same native cache; comparing legacy F against native L would be invalid. Archive/cache identifiers should include encoder/tokenizer revisions and hashes, prompt/special-token policy, token IDs/offsets, lengths/masks, layer index/kind, dtype, selected IDs and source-content hashes. Do not overwrite the historical caches. A measured near-identity of ordinary IDs does not excuse unmeasured special-token, normalization or truncation differences.

## 7. Additional experiments — conditional, not part of immediate authorization

All use only authorized P0 train/validation; none uses test, P1, external APIs or another model as annotator. These specifications accompany the recommendations so they cannot become unbounded follow-up sweeps.

| Experiment | Data, seeds and target | Metrics / stop condition |
|---|---|---|
| **Controlled role survey**, after B0 or as a separately budgeted representation question | Train300/val100; native EG2 layers0–23, exclude projection24; seeds20261108/09/10 for controls/resampling. Targets are train-derived DF bins, normalized source numeric/date spans, source occurrences of reference slots, and fixed sentence-position bins. Probe hyperparameters chosen within train documents only. | Logistic regression, macro-F1/balanced accuracy and per-class scores; true-minus-null plus layer0/spelling/type/position baselines; document-bootstrap simultaneous bands or prespecified multiple-testing correction. Stop for bad span coverage/too few positive documents or no reliable advantage over relevant baselines; do not add an MLP to rescue an uninformative label. |
| **Numeric/date content intervention**, only after useful E1 | Up to10 eligible examples from fixed val20; seed20261108; deterministic same-type, preferably equal-token-length value replacements, with reference changed only where the exact source-supported value occurs. No fitting. | Paired correct-versus-swapped value NLL, generated value accuracy, other-slot errors and unchanged-context behavior. Report all eligibility failures. Fewer than10 valid cases means insufficient evidence, not permission to mine more datasets; no universal causal conclusion. |
| **Bounded B1**, after a new decision | E1 train20/val20, same three seeds/targets; layers5/9/12/19; exact E1 training/ablation settings. Freeze a separate allowed validation subset for within-round confirmation before selection. | Require selectivity, compare paired candidate-minus19 effects with multiplicity control and real-memory/generation safeguards. Confirm the selected layer separately; no replicated improvement means keep19, no added layers. A new decision must specify the exact confirmatory subset before running. |
| **Minimal model×layer interaction check**, only if a general model claim is needed | Both mT5/UMT5 × layers12/19 × the same three seeds; same train20/val20, native EG2 source, each model's native gold target. Reuse exact matching B1 cells; otherwise fresh fits, not mismatched historical runs. | Common-text metrics and within-model selectivity; paired model difference at each layer and difference-of-differences. Underpowered interaction is inconclusive. Stop if neither model has useful selectivity/generation; do not expand to all layers. A one-L* B2 is cheaper but must carry a conditional claim. |
| **Matched A1/metric audit**, before any C proposal | Fixed20 validation examples, preferably E1 val20, with A1 predictions on the same IDs; seed20261108 for a frozen stratified audit order. Gold summary is the quality target, passage is factual evidence. Include deterministic lead-sentence/source-copy baselines. No fitting. | Bag-character F1 plus versioned slot metrics, repetition, lengths, human-blinded entity/attribution review and paired differences. Stop C promotion if metrics are unaudited or gains are only omissions/no-new artifacts. Historical use of these validation IDs must be disclosed. |

For the role survey specifically:

- DF quintiles need deterministic tie/OOV rules from **train only**. Report type lookup/character-pattern baselines and seen-versus-unseen types. A frequency predictor is lexical accessibility, not evidence of semantic abstraction.
- Numeric/date **membership** does not demonstrate recoverable value or preservation. Separate dates, money and ordinary numbers; compare spelling-only and layer0 predictors.
- Slot-overlap negatives should include source slots of the **same type** not selected by the reference, matched on frequency and position. Report all repeated occurrences/ambiguous occurrence labels instead of pretending the reference specifies one source mention. Predicting numeric membership alone must not pass as summary-slot selection.
- Sentence-position bins need a fixed sentence segmentation policy, relative/absolute position and passage-length baselines, and out-of-length/position-stratified checks within allowed validation. A token-index predictor is not evidence of discourse-role understanding.
- Keep the within-document permutation as one null, but add a token-type-consistent random-label control where applicable; the two test different shortcuts. Fit controls with the same capacity/regularization. Resample **documents**, not tokens. Do not claim significance from the best of roughly96 layer/task hypotheses without correction.
- Character labels must be projected onto the actual normalized, prefixed, truncated native-token sequence. Mask prompt/special/padding tokens. Extract reference slots, then find their canonical source occurrences; summary character offsets are never source offsets.

A future C decision would additionally need exact optimization/checkpoint/seed rules and cost limits; it is deliberately not scheduled here. Lower quality can only be justified against a measurable, prospectively accepted resource benefit, not the abstract desire to reuse EG2. F4/F6/F3 remain separate future tasks.

## 8. Budget, stop boundary and relationship to A1

**Proposed maximum for the immediate narrow block:** one working day (8 elapsed wall-clock hours), with **engineering time capped at 6 hours and compute time capped at 4 elapsed hours on at most six CPU threads** (up to 24 core-hours), including native extraction, controls, generation and reporting. Work and computation may overlap, but all three caps apply. The unit is explicit: elapsed six-thread time is not the same as one core-hour. If project capacity differs, reduce concurrent threads rather than silently increasing the budget. These are ceilings, not runtime forecasts.

The fit budget is six 100-update runs (two arms × three seeds), with at most **one same-configuration technical rerun** of an interrupted/invalid run: at most 700 fit updates total. No rank/module/learning-rate search, no additional layer, no UMT5 fits, no full role survey and no Stage C are included. Changing rank/modules after OOM changes the scientific condition; it requires a newly paired, preregistered design, not mixing configurations into the three-seed result. Exceeding any time cap stops work and yields a blocked/inconclusive report.

On an E1 pass, stop this package and present the artifacts for a new B1 decision. On weak/negative/inconclusive results, stop the local EG2→mT5 layer19 adaptation branch operationally; do not use an inconclusive CI as proof of global impossibility. On E0 failure, do not spend the remaining budget on unrelated probes. This prevents an endless sequence of small “one more layer/model/rank” exceptions.

**A1 native remains the frozen pilot300 fallback/reference.** Its matched .6552/100%/100% result is not superseded by a CE probe, a teacher-cosine maximum, a new model name or C's much lower research milestone. Native A1 metric/entity audit remains appropriate, without changing its weights or reopening its closed bridge. No automatic checkpoint promotion, product gate change, or sealed-test evaluation is authorized by this review.

## 9. Compact disposition

| Item | Verdict | Required disposition |
|---|---|---|
| Q1 — role probes | conditional | Accessibility only; native spans, shortcut baselines and corrected statistics first. |
| Q2 — Stage A | disagree | Screening is valid; unique frozen-decoder bottleneck attribution is not. |
| Q3 — B0 layer | conditional | Keep19 as fixed local anchor; add matched frozen control, not more layers. |
| Q4 — B0 DoD | disagree | Add adaptation interaction, useful-real gain, generation and inconclusive category. |
| Q5 — B1 layers | conditional | Bound at5/9/12/19, no neighborhood sweep; defer until controlled B0. |
| Q6 — B2 | conditional | Same layer gives a conditional comparison; generation primary, interaction unestimated. |
| Q7 — C | defer | Audit/compare A1 and justify scaling under a new decision. |
| Q8 — metrics | disagree | No-new ≠ preservation; audit entities and bag-character F1; preserve production code. |
| Q9 — closed bridge | agree | Maintain D-107/D-108; no T5Gemma2 reopening here. |
| Q10 — priority | disagree | Native/wiring audit → paired B0 only; defer parallel full role survey and B1/B2/C. |

**Bottom line:** NARROW to a falsifiable, matched native-input B0. Preserve Stage A as a screening artifact, not a causal verdict; keep A1 native separate and D-108 closed. This review recommends prospective changes and experiments, but approves no gate change and executes none of them.
