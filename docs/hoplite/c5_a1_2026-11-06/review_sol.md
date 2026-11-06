# Independent review: C5 A1 and EG2-to-T5 bridge

## 1. Verdict

**start A1 full train now** — authorize a preregistered, capped two-epoch research run, not product adoption or test unsealing; do not put B3 or another pilot in its critical path.

### Review basis and scope

- Reviewer: Sol 6.1 (`openai/gpt-6.1-sol`), independently, without subagents, additional models, or consulting other model review reports. The prior-opinion summaries inside the required request document were read as context, not adopted as authority.
- Synchronization: `git fetch origin` succeeded; `git pull --ff-only origin main` succeeded with **Already up to date**. `git rev-parse HEAD` confirmed **`834d598e2fb6c003419713156de183d377c4c335`**, containing the request. The workspace's existing branch is `hoplite/euhesperides-4bc68ec2`; its reviewed HEAD is the synchronized main revision. I did not switch branches or rely on historical SHAs.
- Read the entire 562-line `reports/EXTERNAL_REVIEW_C5_A1_2026-11-06.md`, including its bridge designs, decisions, questions, preregistration, limitations, and reproduction section. Checked the supplied A1 reports and code, A2 training code/results, plans, decisions, and pilot300 metrics. Historical supporting reports are treated as observations at their stated stage, not as current experiment status.
- The supplied recalculated metrics are accepted. I checked analytical parameter/cache arithmetic, not the raw evaluation again. No training, new inference, sealed-test access, production changes, or credentials were needed. This report is the only file changed.
- External checks: the [T5Gemma2 paper](https://arxiv.org/html/2512.14856), [Transformers documentation](https://huggingface.co/docs/transformers/en/model_doc/t5gemma2), and [version 5.22.1 implementation](https://raw.githubusercontent.com/huggingface/transformers/v5.22.1/src/transformers/models/t5gemma2/modeling_t5gemma2.py). The versioned implementation establishes the distinct embedding and encoder-output interfaces; neither the paper nor the API proves this project's proposed bridge works.

## 2. Decisions D1–D6

### D1 — Start a bounded A1 full-training study

**Recommendation:** Start with a maximum of **two epochs**, preserving pilot300 as a fallback candidate; do not automatically add epoch three. Use the same r8 attention LoRA and lr `2e-4`, with a recorded checkpoint-selection protocol.

**Rationale:** The +0.0465 paired val advantage, positive CI, 112/161 wins, normal EOS, zero detected new slots, and modest resource use justify spending roughly three training hours. Three hundred examples/steps are only about 23% of one pass through 1,293 pairs, so these results establish feasibility rather than the optimal training duration. Validation selection and absent human review limit adoption claims, not permission to conduct this inexpensive next experiment.

**Evidence that would change it:** Discovery of split leakage, target/label errors, unsafe factual substitutions in a small audit, or incompatible resource behavior would pause execution. A plateau or safety regression during the fixed run would select an earlier checkpoint, possibly pilot300; convincing continued improvement at the cap would justify a separately approved third epoch, not an automatic extension.

### D2 — Keep the prefix as the initial F5 protocol, not as a proven optimum

**Recommendation:** Use `summarize: ` consistently for the initial full run. Perform one paired **bare versus prefix val161 evaluation of the existing pilot300** before freezing the final inference policy; do not make a dropout-training arm mandatory.

**Rationale:** The initial recipe is supported and reproducible, but the prefix-trained adapter's bare val5 score is higher, 0.6522 versus 0.6272, with less repetition and substantially different length. That is sufficient uncertainty to warrant a cheap inference comparison, not sufficient evidence to retrain bare. F5 supervision itself specializes the adapter; deleting a textual cue does not make it general-purpose.

**Evidence that would change it:** A full-val paired bare advantage with no factuality, termination, or coverage loss would favor bare inference, confirmed on the selected checkpoint before test. Prefix dropout becomes worthwhile if robustness to callers omitting the cue is an explicit requirement, rather than a speculative generalization benefit.

### D3 — A1 first; corrected B1d first for a separate bridge investigation

**Recommendation:** Finish the short A1 run first on the shared CPU. For a separately scoped two-week **general bridge** investigation, start with corrected B1d encoder-output distillation using a linear student and oracle controls; B3 is optional, not a prerequisite.

**Rationale:** B3 retains the original passage and the native T5 encoder, so good summaries could be generated without using EG2 information at all. B1d directly tests the valuable proposition that EG2 token features can replace the native encoder's final memory, but the request currently describes its inference path incorrectly. Detailed, separately ranked F5-only and general-bridge priorities appear below.

**Evidence that would change it:** If the goal becomes augmentation of the native encoder rather than replacing it, a controlled B3 study moves up. If the linear student cannot preserve held-out decoder behavior despite a valid oracle, investigate a bounded contextual adapter; if the teacher itself lacks the required task behavior, alignment alone is not the remedy.

### D4 — Close A2 as a product candidate; preserve the negative result

**Recommendation:** Stop A2 product development without waiting for a trained raw-versus-null control. Do not automatically add decoder LoRA to A2.

**Rationale:** F1 around 0.12, grounding checks failing on almost every example, extreme repetition, and poor EOS are ample grounds to reject this implementation. Positive shuffled-memory ΔNLL shows document-conditioned information, not usable summaries or a benefit specifically caused by null injection. Frozen merged attention and bypass of the native encoder are material structural limitations, but A1 changes several things simultaneously and does not isolate their individual causal contributions.

**Evidence that would change it:** An explicit scientific objective to identify null injection's contribution would justify matched, separately trained raw controls. A new external-memory architecture with convincing held-out generation could reopen a new research candidate; neither outcome is required to stop the current product candidate.

### D5 — Keep one final-candidate test event

**Recommendation:** Leave test163 sealed for learned-candidate selection. Freeze the checkpoint, prefix, generation policy, metrics, and human rubric first; then run one selected candidate once under the approved protocol.

**Rationale:** Reusing val for model selection is expected, but the resulting CI is not a selection-corrected estimate of production gain. Giving each bridge proposal a separate opportunity to inspect the same test would turn it into another development set. The historical A0 test evaluation must be acknowledged: this is not a never-opened dataset, although no A1 test result is reported.

**Evidence that would change it:** A predeclared multi-system confirmatory study could freeze all candidates before a single evaluation event, but that changes the present one-candidate contract and needs authorization. Otherwise, bridges developed after the final event need a future untouched P0 holdout for confirmatory claims, not repeated adaptive use of these 163 examples.

### D6 — Human review after training and before test

**Recommendation:** Conduct a blinded, source-aware, paired A0/A1 review of 50 validation examples before test; a small pilot audit may run earlier but should not delay the capped research run.

**Rationale:** No-new-slot checks cannot detect wrong attribution, inverted relations, negation changes, unsupported non-slot claims, or omission of a critical condition. Include the six zero-detected-slot outputs in the audit, with the sampling scheme/stratum weights disclosed if estimating overall acceptance. Require zero observed critical factual errors as well as the existing critical-omission rule; 60% acceptance alone is not sufficient evidence of product safety.

**Evidence that would change it:** Critical factual errors or failure of the declared utility threshold would stop promotion and keep test sealed. High agreement, low error severity, and acceptable usefulness would support proceeding to the frozen final evaluation, not a claim that the true error rate has been proved below 1%.

## 3. Answers to Q1–Q12

### Q1. Is pilot300 enough to begin full training?

Yes: 0.6576 versus 0.6111, paired +0.0465 with CI [+0.0336, +0.0603], and 112/161 wins make a capped full run a sensible next research expense. The improvement is not only on the five development examples: the reported remaining 156 average 0.6586, though that is still not an untouched confirmatory split after inspecting the aggregate result. At 23% of one epoch, pilot300 provides neither a learning-curve endpoint nor assurance that two epochs will improve it. Human review and a final frozen evaluation are necessary for promotion, but no additional bridge control is necessary to authorize training.

### Q2. Two or three epochs, and what selection rule?

Start with two epochs, **2,586 optimizer steps at batch one**, from the same base initialization/seed, retaining pilot300 separately; do not describe an undocumented warm start as the same experiment. Predeclare full-val generation at steps 647, 1,293, 1,940, and 2,586, and select the highest char F1 among safety-eligible candidates, treating differences below 0.002 as ties favoring the earlier checkpoint. An explicit proposed eligibility policy is the existing ≥99% case-level slot check, ≤1% new-slot micro rate, EOS ≥95%, plus repeated4 ≤0.06 as a reviewer-proposed no-material-regression guardrail, not a previously validated product threshold. Use patience two scheduled evaluations with min-delta 0.002; count ineligible checkpoints as non-improvements and retain the pilot if nothing improves acceptably. Training alone extrapolates to about 3.01 hours from 4.20 seconds/step; checkpoint evaluations and implementation time are additional.

### Q3. Is training with `summarize: ` appropriate, and what about reuse?

It is appropriate for an explicitly F5-specific adapter, but the current evidence does not establish it as the best pilot300 inference condition. The strongest within-checkpoint prefix result is on pilot100; the pilot100-to-pilot300 comparison also changes learning rate and steps, so its improvement cannot be assigned to prefix training alone. The pilot300 bare/prefix difference on five examples deserves full-val confirmation, including its length shift from 167.4 to 264.0 tokens. Prefix dropout is a robustness intervention, not a demonstrated path to generic generation. Keep F5 LoRA distinct from future F4/F6 adapters; F3 currently has no decoder path to reuse it on.

### Q4. Which bridge should be first?

For the actual F5 milestone, A1 should precede all bridge work. For the architectural objective of removing the native T5 encoder at inference, corrected B1d is a more discriminating first experiment than B3 because it compares an EG2-derived memory directly with an oracle native memory. B3 is a valid augmentation/prefix-control experiment only with real/shuffled/EG2-independent controls; its raw-text path makes it a weak test of EG2 information preservation. A linear B1d student is the first capacity baseline, not an assertion that contextual T5 hidden states must be linearly recoverable. Also, a faithful bridge to the frozen base decoder does not create the F5 skill that the weak zero-shot baseline lacks.

### Q5. May A2 close without a raw control?

Yes for product triage, no for attributing the result specifically to null injection or proving a unique failure cause. Grounded counts of 0/161 and 1/161, F1 0.1277/0.1169, and repeated4 around 0.85–0.87 make the current implementation noncompetitive without further controls. The +0.058 shuffled-minus-real NLL difference is worth preserving as evidence of conditional signal, not treating as a rescue criterion. A trained raw control is required only if a later investigation makes causal claims about the representation change. Decoder LoRA would create another model to evaluate, not retrospectively validate A2-null.

### Q6. Is the evaluation sufficient?

It is sufficient to justify more training, not a product decision. The slot metric does not test all factual relations, and char F1/copy rate cannot establish faithfulness, usefulness, or genuinely abstractive synthesis; A1's 0.8364 source four-gram copy rate is still substantial despite improving on A0's 0.9923. Mandatory additions before promotion are source-aware human factuality/critical-omission review, treatment of slot-free outputs, and explicit reporting of sentence count, compression/length, and excessive repetition. ROUGE-L is a cheap useful continuity metric from the original plan; BERTScore is optional and would need Korean/model calibration rather than serving as a factuality gate. Record actual inference latency/RSS as well, because generation remains the product path even when training is affordable.

### Q7. How should the six slot-free summaries be counted?

Report **161/161 no-new-detected-slot passes**, broken into **155/155 outputs with detected slots** and **6/161 with zero detected summary slots**. Keep the established all-example denominator for the operational gate, rather than silently redefining it after seeing the results, and expose the conditional 155-example result beside it. Neither number means factual grounding was established for those six outputs; all six need source-aware inspection for deletion, genericity, and non-slot factual errors. Do not automatically fail a legitimate slot-free summary either. Even 161/161 passes yield only about a 98.16% one-sided exact 95% lower bound for the population pass rate under an IID model, not proof of ≥99% reliability.

### Q8. Keep q/k/v/o r8 or add FFN/r16?

Keep the existing target and rank for the first full run: `attach_lora` covers encoder-text and decoder projections, yielding the reported 144 modules and 1,474,560 trainable parameters. In merged decoder attention, q/k/v/o adaptation affects the joint self/cross computation, so a separate conventional T5 `EncDecAttention` target is neither missing nor required. This is an empirically sufficient starting target, not proof that FFN adaptation or higher rank cannot help. Expand capacity only after a controlled learning curve or error analysis shows an unresolved bottleneck. Before any such comparison, fix the runner's configuration wiring: parsed rank/alpha/dropout currently do not reach `build_model`/`attach_lora`, although their argument values are saved as checkpoint metadata.

### Q9. How should test be handled if bridges run too?

Use val or inner development splits to compare A1 and bridges, then nominate a single final candidate before the test event. Do not allocate slices of a small 163-example test adaptively across architectures or open it to decide whether a bridge deserves another training round. A later general bridge should demonstrate its representation properties and transfer on separate P0 development tasks without consuming this F5 test. If multiple frozen candidates must receive confirmatory comparison, preregister that change before unsealing rather than interpreting the current rule as permission. A failed final evaluation should be reported, not followed by tuning on its outcomes.

### Q10. Does A1 conflict with the EG2 reuse goal?

It satisfies the user-facing F5 summarization objective while serving as a quality/resource reference for the independent EG2-reuse objective. It does not demonstrate EG2-to-T5 transfer, encoder elimination, or savings from EG2 residency. Reframe these as two milestones: a safe useful F5 summarizer, and a bridge that later achieves acceptable quality at measured total latency/RSS with the T5 encoder absent. B3 does not satisfy the latter milestone because it keeps both EG2 processing and the T5 encoder. Specify a small versioned tensor/task interface now, but avoid speculative F3 decoder support or production integration changes.

### Q11. Are two to three epochs appropriate, and how to control overfitting?

Two epochs are a reasonable budget to test, not a quantity supported as optimal by the pilot's falling training loss. Preserve lr `2e-4`, attention r8/alpha16/dropout0.05, clip1.0, batch one without changing effective batch, and explicitly record AdamW weight decay **0.01** if preserving the current implicit default; use no new schedule for this baseline. Shuffle deterministically anew each epoch, record ordering/seed, and use the fixed evaluations/stopping rule from Q2 instead of searching durations after seeing val. The current runner creates one random order and cycles it unchanged, has no scheduled checkpoint selection, and does not resume a training adapter merely because `--adapter` is provided. Keep the cap at two epochs and treat any third epoch, scheduler change, or FFN/rank expansion as another approved experiment.

### Q12. What factual errors or important omissions need correction?

The central technical error is saying B1d both skips the native encoder and sends teacher-final states through encoder `inputs_embeds`: those are incompatible execution paths. The counts for decoder-only B2, standard-width B1b, and B3 K32 MLP need correction or architectural qualification. The document overstates causal isolation of frozen attention, the effect of prefix training, and elimination of scale as a cause, while understating the weak-base-teacher limitation of label-free B1d. Its all-1,617 teacher-cache example includes sealed test passages and must not become a training recipe. Finally, distinguish the previously evaluated A0 test baseline from an A1-unopened test and distinguish slot-novelty success from verified factual grounding; the detailed audit below supplies corrections.

## 4. Bridge addendum

### 4.1 Rankings: separate goals, not empirical results

These are research-priority judgments under the corrected interfaces, not measured quality rankings. B1a/B1b describe adapter architectures, B1d describes an objective and injection point, and B2 adds trainable decoder capacity; they are not fully disjoint alternatives. In particular, B1d can use a B1a-sized linear map or a B1b-style contextual network.

| Candidate | F5-only rank | General EG2-to-T5 rank | Reason and most likely failure |
|---|---:|---:|---|
| **B2** | **1** | **4** | Most plausible task-specific bridge because supervised decoder LoRA can learn the F5 behavior absent from the base. Failure: decoder/adapter overfit 1,293 pairs, language-prior shortcutting, or task-specific LoRA repairs one task without preserving a portable representation. |
| **B1b** | **2** | **2** | Contextual adapter has more chance than a pointwise map to reconstruct useful sequence interactions. Failure: too much capacity for the available supervision, altered positions/context, CPU activation cost, or the native encoder still being needed. Generality requires a broader objective than F5 CE. |
| **B1a** | **3** | **3** | Essential low-cost token-level baseline, without a pooled information bottleneck. Failure: per-token mapping cannot recover teacher-specific contextual transformations or the correct memory/input distribution; matching tokenizer boundaries alone does not solve this. |
| **B3** | **4** | **5** | Can act as a task-conditioning augmentation while the original text remains available. Failure: EG2-independent learned-prompt shortcut, ignored EG2 information, or loss of exact token-level facts through pooling; it never demonstrates encoder replacement. |
| **B1d** | **5** | **1** | Best targeted test of reusable encoder-output compatibility and a label-free alignment objective. Failure: good average cosine/MSE but incorrect decoder-sensitive directions, positions, or scale; also, faithfully reproducing the weak base teacher fails to yield useful F5 summaries. |

B1d ranks last for **immediate F5-only performance as written**, not because distillation is unsound: its frozen base teacher/decoder is not the successful A1 system. A later B1d plus an independently tested A1-compatible task readout is a meaningful additional variant, not an observed result or permission to reuse F5 LoRA for F4/F6. In the general ranking, B1a/B1b would need unlabeled reconstruction/distillation or multi-task P0 supervision before any generality claim; their F5-only recipes are not already general bridges.

### 4.2 The corrected B1d contract

**Two distinct interfaces must not be conflated:**

1. **B1a/B1b encoder-input route:** map EG2 features to appropriately scaled input-like vectors; run the native encoder, then its decoder. This retains the T5 encoder and learns an input interface.
2. **B1d encoder-output replacement:** predict the native encoder's final `last_hidden_state`; supply it as `encoder_outputs` directly to the decoder. This removes the T5 encoder at inference and learns an output interface.

For B1d, the conceptual inference call is:

```python
model.generate(
    encoder_outputs=BaseModelOutput(last_hidden_state=H_student.to(base_dtype)),
    attention_mask=source_mask,
    # unchanged native decoder-start, EOS, and generation configuration
)
```

The versioned Transformers implementation explicitly skips its encoder when `encoder_outputs` is present. Passing `H_student` as encoder `inputs_embeds` instead runs an extra encoder and applies a transformation different from the teacher target. The fact that both tensors have width 640 does not make them interchangeable.

**Minimum technical requirements:**

- **Features:** identify the exact EG2 extraction point. The request elsewhere describes a 512d text hidden state and a 768×512 projection; “768d token hidden” must mean a specified projected feature, not an unspecified raw hidden state. Do not silently reuse the null/PCA representation from A2 or substitute a pooled normalized retrieval vector for token features.
- **Alignment:** the 4,695-sentence segmentation observation is useful but does not prove identical BOS/EOS handling, prompt insertion, padding, truncation, special tokens, or position IDs. Align by actual token IDs/offsets on the proposed prompt-plus-passage sequences, retain the complete valid-token mask, and handle all special-token positions explicitly. If exact correspondence fails, define a span/resampling alignment rather than applying pointwise MSE to unrelated positions.
- **Teacher:** cache the actual eval-mode, final-normalized encoder output consumed by the chosen decoder, not an arbitrary intermediate layer. Freeze and identify the teacher/decoder revision and adapter state. An A1-adapted encoder is not the same teacher as the frozen base encoder.
- **Scale/objective:** use masked, explicitly reduced losses such as token cosine plus MSE normalized by a fixed training-set teacher RMS, with recorded weights. Compare per-token norms and per-channel statistics as diagnostics, but preserve the teacher's absolute output scale. A unit-normalized sequence or unconditional `sqrt(640)` multiplier would not reconstruct final encoder states.
- **Decoder readability:** measure held-out teacher-versus-student decoder NLL/logits and actual generation, with real/shuffled source controls. Average hidden similarity can conceal small errors in directions to which merged attention is sensitive. A successful output interface should reproduce the teacher's conditional behavior, not merely its marginal hidden-state distribution.
- **Data boundary:** train/cache for fitting on the 1,293 training passages only, with an inner held-out portion for this study. Summary labels are unnecessary for hidden regression, but using test passages for unsupervised alignment is still test use and is not allowed here.

The frozen native teacher can teach an interface without summary labels. It cannot by itself teach the new summarization behavior observed only after A1 LoRA: zero-shot F1 is 0.2333 with EOS 1.86%, and its prompt differs from the trained A1 protocol. Establish the relevant native teacher behavior under matched prompts before attributing an unsuccessful F5 readout to a failed bridge.

### 4.3 First two-week experiment and minimum falsification test

**First experiment:** after the A1 run, conduct an encoder-replacement feasibility study, not a broad bridge sweep. Week one: fix token/mask/scale conventions, establish oracle bypass equivalence, make train-only teacher/EG2 caches, and fit one linear B1d map. Week two: evaluate held-out functional fidelity and source dependence; try one bounded contextual student only if the linear model's fit/generalization diagnostics justify it. Budget approximately **6–20 CPU wall-hours across extraction, fitting, and decoder evaluations**, plus engineering time; this is an allowance to measure, not a throughput claim.

**Minimum empirical test that can falsify a useful linear B1d claim:**

1. Choose, for example, 256 training passages and 64 inner-held-out passages from the training split, with fixed prompts and no F5 test access. Verify native `input_ids` inference and cached teacher `encoder_outputs` inference agree in logits/loss to the expected dtype tolerance and give the same greedy behavior except justified near-ties. A failed oracle means a broken harness, not evidence against distillation.
2. Fit the 0.492M projected-768-to-640 linear student with the declared masked hidden loss; first show it can substantially fit a tiny training subset. Evaluate the frozen decoder on held-out teacher-forced continuations shared across oracle, real-student, and shuffled-student conditions; these may be teacher-generated continuations, so the fitting objective still needs no summary labels.
3. Predeclare a functional target, for example student-minus-oracle NLL **≤0.10 nats/token**, and recovery of **≥80%** of the oracle-versus-shuffled NLL advantage when that advantage is positive. These are proposed feasibility criteria, not established universal tolerances. A paired interval whose lower bound exceeds the NLL margin, or whose upper bound is below the recovery target, rejects that fidelity claim for the tested linear recipe; mere failure to prove non-inferiority is inconclusive.
4. Inspect a small fixed set of generations and source-sensitive facts. If hidden regression looks good but the functional criteria fail, the proposed loss is not sufficient for decoder readability; consider a contextual student or decoder-aware distillation before a larger run.

Failure of this bounded linear experiment does **not** falsify every possible teacher-distilled bridge. Conversely, reproducing the weak native teacher does not establish F5 usefulness or F4/F6 transfer.

### 4.4 Why B3 is not a prerequisite readability test

B3's `[soft_prefix ; Embed_T5(passage)]` route leaves a full-information native-text path. Compare **real EG2 prefix, shuffled EG2 prefix, and a trained EG2-independent prefix of the same length**, with the same base and task cue; also report native text without learned prefix. If real and shuffled prefixes perform alike, a good F1 result does not demonstrate document-specific EG2 use. A zero prefix alone is not an adequate control because it changes the input distribution.

This is worthwhile if native-text augmentation is itself wanted, but otherwise it is a detour from encoder removal. Because B3 still runs the native encoder, a frozen encoder/decoder must remain in the autograd graph during adapter training; freezing weights does not mean wrapping the entire forward in `no_grad`. Its speed and activation memory cannot be inferred from its adapter's parameter count alone.

### 4.5 Parameter, cache, memory, and cost audit

Counts below include linear biases and exclude optional LayerNorm unless stated:

| Component | Recalculated size | Assessment |
|---|---:|---|
| B3 linear, K8 / K16 / K32 | 3,937,280 / 7,874,560 / 15,749,120 | Request's 3.9/7.9/15.7M approximations are sound. |
| B3 768→1024→K·640 MLP, K8 / K16 / K32 | 6,035,456 / 11,283,456 / **21,779,456** | K32 is about **21.8M**, not 22.4M for the stated architecture. Per-token LN adds 1,280, not the discrepancy. |
| B1a linear 768→640 | **492,160** | Approximately 0.49M is correct; a true 512→640 hidden-state map would instead be 328,320. |
| B1b: standard two-layer width640 Transformer, FFN1280 / FFN2560, with input projection | about **7.06M / 10.34M** | “2–5M” needs an explicitly narrower/bottleneck architecture or other parameter reduction; it is not a generic two-layer width640 estimate. |
| A1 all encoder+decoder attention LoRA r8 | **1,474,560** | Supported by the code and supplied smoke result; not a decoder-only count. |
| B2 decoder-only q/k/v/o r8 | about **737,280** for the reported symmetric encoder/decoder projection geometry | Specify and enumerate the actual decoder target modules. Claiming 1.47M while also saying encoder frozen conflates the A1 target set with decoder-only LoRA. |
| Teacher cache, 1,617×900×640×2 bytes | **1.863 GB = 1.735 GiB** | 1.9GB is reasonable as raw storage, not total RAM. It includes val/test and is not an allowed fitting cache. |
| Teacher cache, train1,293 at the same length | **1.490 GB = 1.387 GiB** | Prefer variable-length sharded storage; prompts/masks/metadata add overhead. |

The B3 “4–16M” comparison row covers the linear options, not the proposed MLP alternatives. B1d “0.5–5M” likewise requires an actual student specification; distillation does not determine the parameter count. B2's total is the chosen adapter plus its actual LoRA targets, not a universal 2–7M.

For memory, 370,637,824 bf16 base weights alone are approximately **0.741GB**, before load peaks, buffers, activations, and generation cache. FP32 trainable weights, gradients, and two AdamW moments add roughly **16 bytes per adapter parameter**: approximately 63–252MB for the B3 linear range, or 349MB for its K32 MLP. Backpropagating through frozen encoder/decoder layers still needs activations; caching or co-residency of EG2, full source features, and teacher states can dominate these adapter allocations. The measured A1 peak of about 2.45GB is encouraging, but it is not a demonstrated B3/B1/B1d memory bound; stream caches and measure peak RSS per proposed path.

The A1 extrapolation of ~90 minutes/epoch is well supported by the measured 4.20 seconds/step. B3's 300-step 20–30-minute estimate assumes 4–6 seconds/step; 1,000 steps at that rate take about 67–100 minutes, broadly plausible but unmeasured. The **3–8-hour bridge totals** are useful optimistic planning envelopes for a minimal prototype, not verified CPU costs, and mix engineering time with training/evaluation time. Report these separately, include EG2/teacher extraction and controls, and benchmark 10–20 representative steps before promising a larger budget; B1d cached regression and B3 full-model input-gradient training have fundamentally different compute profiles.

### 4.6 Merged attention, B2, and reuse boundaries

Merged attention makes decoder q/k/v/o a sensible adaptation target because the parameters jointly govern self and source attention. It does **not** imply a frozen decoder cannot consume a correctly reconstructed native hidden sequence; that is exactly the hypothesis B1d should test. Nor does LLINK establish that B2 is necessary here: it motivates a controlled rescue arm in a different architecture/task setting.

If B1d is functionally faithful but F5 generation remains poor, first check whether the native teacher/decoder is equally poor; then task adaptation is needed, not necessarily bridge repair. If hidden similarity is high but decoder fidelity is poor, fix alignment, norm, position handling, and objective, or test a contextual student. Add a separately evaluated decoder-only LoRA arm only after those controls, and require it to retain real-versus-shuffled source dependence rather than masking a source-ignorant shortcut.

For now, specify only a small contract: feature extraction/version, token IDs and masks, injection point, tensor width/dtype/scale, special-token/position conventions, immutable base hash, and task-specific adapter identifiers. Before claiming F4/F6 reuse, run small offline P0 development checks for their own output/retention constraints with task adapters isolated; do not put F5 LoRA in their production paths. F3 retrieval/emoji tagging needs no decoder retention experiment now, and no production assets need modification for this review or the proposed feasibility study.

## 5. Must-fix items — priority order

These are recommendations for the next authorized work, not changes performed in this consultation. Items 1–2 precede a faithful full-training execution; human/final-policy items precede promotion/test; bridge items precede bridge claims, not A1 training.

1. **[Document fix] Freeze an executable A1 protocol.** Specify fresh versus resumed initialization, total steps/effective batch, explicit optimizer defaults, evaluation cadence, checkpoint eligibility, repetition guardrail, stopping/ties, pilot fallback, and the one-candidate test event. Define “grounded” as the observed slot-novelty check, with separate case/micro denominators and slot-free reporting.
2. **[Needs new experiment] Validate the eventual full-training harness and reload.** The current pilot runner does not implement the proposed scheduled selection/resume protocol and ignores rank/alpha/dropout arguments when constructing LoRA. An authorized implementation must prove actual module configuration and checkpoint reload, preserve optimizer/RNG/order state if resuming, and enforce the declared resource stops; no such code changes are authorized or made here.
3. **[Needs new experiment] Complete the 50-example source-aware human review before test.** Audit unsupported claims, attribution/negation errors, critical omissions, repetition, and utility against A0, including the six slot-free cases. Report sampling/strata, critical-error counts, and reviewer agreement rather than equating 60% acceptance with safety.
4. **[Document fix] Correct B1d's injection point and training boundary.** Final-hidden distillation must use decoder `encoder_outputs`, aligned valid tokens and final-state scale, and an identified teacher/decoder pair; do not fit on all1,617 passages or claim a frozen weak teacher creates A1-level F5 ability.
5. **[Needs new experiment] Resolve the cheap prefix inference uncertainty.** Run paired bare/prefix val161 on the existing pilot, then freeze/confirm the final checkpoint's inference policy on development data before the test event. This does not require delaying the initial prefix-consistent full run or training a dropout grid.
6. **[Document fix] Specify bridge architectures, counts, and valid controls.** Correct/qualify B3 K32 MLP, B1b width, and decoder-only B2 counts; separate CPU wall-time from engineering effort and memory storage from peak RSS. Require EG2-dependence controls for B3 rather than treating any good summary as a successful bridge.
7. **[Document fix] Narrow causal and reuse claims.** Retain A2's structural-failure interpretation without claiming isolated causality, separate inference-cue effects from training-prefix effects, acknowledge the historical A0 test evaluation, and remove F3 decoder reuse from the current scope.

## 6. Additional experiments worth doing — maximum five

All costs below are rough wall-clock estimates on the stated six-core CPU, not measurements from this review; implementation and human effort are separate. None uses P1 data, product-path external APIs, production asset edits, or early sealed-test access.

| Experiment | Rough CPU cost | Decision value |
|---|---|---|
| **Paired pilot300 bare/prefix val161**, including length, EOS, repetition, slot strata, and paired score difference | One additional generation condition, roughly **10–30 minutes**, allowing longer if throughput differs | Highest-value cheap check: resolves the direct contradiction between the chosen prefix policy and the five-example pilot300 comparison. |
| **One second-seed A1 replication**, only if promotion depends on a small improvement or the curve is unstable | About **3 training hours**, plus roughly **0.5–1 hour** of fixed evaluations | Tests run-to-run stability; more informative than broad FFN/rank/prompt searches on the same val set. Not a prerequisite to the first full run. |
| **Minimal oracle/linear B1d replacement test** from §4.3 | Approximately **1–4 hours** including small feature/teacher extraction and decoder readout; cached linear fitting is only a fraction | Can reject the cheap encoder-replacement recipe before a large representation-learning investment. Teacher competence and oracle fidelity are explicit controls. |
| **Optional B3 dependence/learned-prefix control** at a single K and budget | Roughly **1–3 hours** for matched small runs and evaluation, plus EG2 extraction if uncached | Distinguishes document-specific EG2 contribution from task conditioning/native-text shortcut; useful only if augmentation is a real objective. |
| **Tiny offline F4/F6 transfer/retention probe**, only after a bridge passes its own fidelity gate | Approximately **15–60 minutes** of inference on small P0 development suites; no new multi-task training implied | Tests whether “reusable bridge” means more than F5 compatibility, with task-specific readouts isolated. No F3 decoder experiment is justified now. |

## 7. Factual errors, overclaims, and omissions in the request

1. **B1d execution contradiction — §3.7.4.** “No T5 encoder at runtime” conflicts with supplying the distilled final states to encoder `inputs_embeds`. Use `encoder_outputs`; otherwise redefine the student target as an encoder-input interface and retain the encoder. The generic “all B-family preserves the encoder” table must explicitly exempt corrected B1d.
2. **Teacher fidelity is asserted, not established.** “The decoder receives the same distribution” is a target, not a result of matching width or optimizing a loss. Marginal distribution matching is weaker than per-document, per-position functional agreement, especially under merged source/self competition.
3. **The weak teacher ceiling is missing.** Hidden-only distillation can mimic the frozen native path without labels; it does not teach task behavior that path has not demonstrated. The reported zero-shot failure uses a different cue, so a matched-prompt oracle must separate teacher inadequacy from bridge inadequacy.
4. **“768d token hidden” is underspecified.** The supplied A2 plan defines final hidden512 and a projection to768. Identify projected final features, raw hidden features, or null-augmented features explicitly; their counts, information content, and relation to D-042 differ.
5. **Tokenizer agreement is overgeneralized.** Agreement on 4,695 sentence segmentations does not settle prompt-plus-document special tokens, offsets, truncation, or positions. These must be verified for the actual teacher/student tensors.
6. **Parameter estimates need qualification.** The stated K32 B3 MLP is 21.779M rather than22.4M; “B3 4–16M” excludes the MLP options. A conventional two-layer width640 B1b exceeds2–5M, and 1.47M is the A1 encoder-plus-decoder LoRA count, not the expected decoder-only B2 count for the reported symmetric geometry.
7. **Cache arithmetic is reasonable; cache membership is not.** Approximately1.9GB for1,617×900×640 fp16 states is correct as raw bytes, but fitting on that cache would include test passages. Train-only at this illustrative length is approximately1.49GB, and neither number is an end-to-end RAM estimate.
8. **The A2 causal claim is too categorical in §4.** Frozen merged q/k/v/o and external unaligned memory are a strong structural explanation, but A1 also changes encoder, representation, and task adaptation. A positive NLL ablation establishes conditional signal, not sufficiency of information or a unique cause; the document's later limitation is more accurate than its categorical headline.
9. **Prefix-training benefit is confounded.** Pilot100 bare-trained inference-cue changes are within-checkpoint evidence; pilot100 versus pilot300 also changes lr and duration. “Bare val5 still summarizes” demonstrates that the prefix is not indispensable on those five cases, not that prefix sensitivity or F5 specialization is absent generally.
10. **Scale is not exhaustively eliminated.** A failed LayerNorm×5 A2 arm does not exclude all conditional norm, direction, positional, or decoder-K/V mismatch. For encoder-input B3, the versioned implementation's token lookup already multiplies by sqrt(hidden_size), while supplied `inputs_embeds` bypasses the lookup; match the actual lookup output and do not double-scale it. B1d final hidden states require the final-state scale, not that embedding rule.
11. **Test history needs precise language.** D-080 and the request's own decision table already report A0 test163 F1 0.6072. “Test has never been used” and “no command has used test” are too broad; state which learned-candidate evaluations remain sealed and preserve that boundary. The present review did not open it.
12. **Metric semantics and uncertainty are underreported.** Zero novel detected slots is not comprehensive factual grounding, and the six slot-free outputs are unassessed by that detector. Even zero failures out of163 would only give an approximately98.18% one-sided exact95% lower bound under IID assumptions; at least299 zero-failure examples would be needed for a99% lower bound, even before distribution shift or selection. These calculations contextualize the gate rather than proposing early test use or changing the agreed denominator.
13. **Full-train preregistration exceeds the present runner.** `runner/c5_a1_lora.py:82–92,128–145,164–169,181–228` shows default LoRA construction despite parsed hyperparameters, a single repeated permutation, end-only saving, no optimizer/RNG resume, and no scheduled best-checkpoint/early-stop implementation. The declared >60-second step stop is not implemented in its shown training loop, although the RSS stop is. A fixed `--steps 2586` invocation alone is not the draft's full protocol.
14. **Product and reuse requirements remain incomplete.** Include relation/attribution factuality, critical unsupported claims as well as omissions, three-to-five-sentence compliance, useful compression, and runtime cost. F4/F6 transfer is hypothetical, F3 is currently retrieval/emoji tagging, and unchanged base weights plus isolated task adapters need only a modest interface contract now—not speculative cross-feature product modifications.

## 8. Short final recommendation

Proceed with **A1, capped at two epochs**, retaining pilot300 and the current small attention target. Treat the observed val advantage as permission to learn more, not evidence of product-grade factuality; freeze the protocol, complete human review, and preserve the final-candidate test boundary. Keep the prefix initially but test the existing pilot's bare inference once on full val. Run **corrected B1d with oracle and source-dependence controls** as the first separate general-bridge study; B3 neither replaces the encoder nor needs to delay the F5 milestone.
