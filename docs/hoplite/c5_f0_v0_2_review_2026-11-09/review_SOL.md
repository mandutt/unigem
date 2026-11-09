# C5 F0 v0.2 — independent re-review (SOL)

- Date: 2026-11-09.
- Reviewed HEAD: `185d2ff7b2c29aaa10093838335cb15901981657`.
- Synchronization: ran `git fetch origin`, then `git pull --ff-only origin main`; both succeeded, pull reported `Already up to date.` Resulting HEAD is the reviewed HEAD above. Initial working tree was clean.
- Scope: new, independent v0.2 consultation. The v0.1 plan and syntheses were read as historical evidence, not inherited verdicts or implementation authority.
- Stage D must remain **mechanics-only**.
- Only this report was written. No training, evaluation, tests, model imports/execution, test 163/P1 access, subagents, or additional LLM calls were performed. No execution approval is granted.

## Sources and citation key

All eight requested files were read:

1. **Request**: `reports/EXTERNAL_REVIEW_C5_F0_V0_2_2026-11-09.md`.
2. **V2**: `docs/plan_c5_f0_v0_2_2026-11-09.md` — the review target.
3. **V1**: `docs/plan_c5_f0_2026-11-09.md` — superseded historical design.
4. **Draft synthesis**: `reports/C5_F0_DRAFT_3AI_REVIEW_SYNTHESIS_2026-11-09.md`.
5. **Cause**: `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`.
6. **Results synthesis**: `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`.
7. **P6**: `docs/plan_c5_b0a_pm_prereg_v1_0_11.md` — frozen definitions to which V2 refers.
8. **Runner**: `runner/c5_pm_phase6.py` — inspected statically at reviewed HEAD.

Historical experiment numbers below are source-reported, not recomputed in this consultation. Arithmetic workload counts are derived from the specified loops, not timing measurements.

## Q1. Stage D/R selection bias removal

- **Verdict: conditional — the signal-selection defect is removed in the revised design; the mechanics contract needs two explicit corrections.**
- **Evidence:** V1 §8 required debug-seed `E01 copy mean > 0 AND E01−E11 paired mean > 0` to enter Stage R despite calling Stage D descriptive. V2 §§0, 4 replaces this with D0 at **0 updates**, D1 at **1 update**, debug seed **20261111**, and an unconditional scientific plan for registered seeds **20261108/20261109/20261110** after mechanics pass. V2 §4 lines 90–94 fixes Stage R at **900 updates** and explicitly says **No 1-seed signal gate**. Thus the old outcome-dependent selection is genuinely removed; I do not carry the old objection forward as if unchanged.
- **D1 is useful, not redundant with D0.** Shape/finite-memory checks cannot establish that backward propagation reaches the intended adapter/LoRA parameters, that AdamW groups are correct, that frozen weights remain frozen after a step, or that saving/restoring the evaluation path works. This matters because Runner `optimizer_for()` rejects empty trainable groups, and `train_one_update()` unconditionally constructs an optimizer and calls backward. D0 cannot expose that E00 failure mode. D1 should test finite loss/gradients, intended parameter changes, frozen-state invariance, modes, artifact completeness, and timing—not require loss improvement or positive donor deltas.
- **Remaining contradiction:** V2 §2 defines E00 as **0-update, no trainables**, but §4 says **4 cells, 1 update** and §9 totals **4** D1 updates. E00 cannot receive an optimizer update without ceasing to be E00. D1 should be **4 evaluated cells, 3 optimizer updates**: E00=0; E10/E01/E11=1 each. Correct prospective total is then **903**, not 904, optimizer updates across D/R. Also replace D0's three-entry `adapter absent/present/present` assertion with the explicit four-cell vector **absent/present/absent/present** in E00/E10/E01/E11 order; LoRA counts **0/0/64/64** are already correct.
- **Next steps:**
  1. Specify objective mechanics pass/fail criteria, including the corrected E00 update count and complete parameter/mode assertions; no condition on CE improvement, signal direction, M_PASS, generation quality, or contrast size.
  2. Explicitly discard debug states and start all registered units fresh. D1's seed, checkpoint, or telemetry must not select cells, donors, seeds, or training settings for R.
  3. Define technical failure/cap exhaustion as incomplete or not assessable, not scientific negative. A prospective timing-feasibility check may block an infeasible run, but cannot select on signal or authorize retries/extensions.

## Q2. E01 vs E11 and 2×2 validity

- **Verdict: conditional — valid primary comparison of configured training regimes; not a balanced trained factorial or a uniquely isolated architecture mechanism.**
- **Evidence:** V2 §2 now correctly compares **E01** (raw EG2, no adapter, decoder LoRA) against **E11** (same source, trained adapter, decoder LoRA). Both train **100 updates**. V2 §3 holds LoRA configuration at **64 q/k/v/o modules, r=8, alpha=16, dropout=.05**, LoRA LR **1e-4**, batch **1**, AdamW weight decay **.01**, clip **1.0**, train20 order `step%20`, and base decoder eval. E11 additionally has the **512→512 Linear/GELU/Linear/LayerNorm** adapter at LR **1e-3**. This addresses the simultaneous adapter-and-LoRA presence change in an E01-vs-E10 comparison.
- **Interpretation limit:** “LoRA fixed” means configuration/training rule, not identical final LoRA weights. Adding an adapter changes the optimizer trajectory, trainable capacity, normalization, and learning-rate groups. P6 §§2.5.4/2.7 and Runner `build_arm()` seed once, construct the adapter first when present, then attach LoRA without reseeding. E01's absent adapter therefore also changes the RNG position at LoRA initialization; same seed does not ensure identical initial LoRA A tensors. This does not invalidate a comparison of the preregistered regimes, but prevents describing it as an exact matched-weight architecture-only intervention. Three fixed seeds do not uniquely disentangle that mechanism.
- **Auxiliary cells:** V2 §§2/6 correctly restrict E00 to a descriptive eval-only baseline. E10−E00 includes adapter acquisition plus training; E01−E00 includes LoRA plus training; E01−E10 changes both adapter and LoRA/training path. Do not estimate a clean trained-factorial interaction from `(E11−E10)−(E01−E00)`. E11−E10 is interpretable as adding LoRA to the adapter training regime, including its optimization consequences—not a universally isolated decoder mechanism.
- **Endpoint contract is not yet executable without interpretation.** V2 §5 calls its predicates frozen Phase 6 definitions, but lists only **three** conjuncts: copy mean **≥.05**, CI lower **>0**, **2/3** positive seed means (full mean **>0** with the other two conditions). P6 §3.5 has a **fourth conjunct**, paired **L>F mean >0**. Its E11/E10 counterpart differs from V2's primary **E01−E11**. V2 does not state whether it intentionally separates that legacy relative-arm condition from within-cell donor evidence or how it binds each new cell. Blindly copying `L_COPY_SIGNAL` is not a solution.
- **Next steps:**
  1. Supply a binding table for every F0 cell-level copy/full predicate, consensus label, and primary between-cell predicate. Resolve the fourth-conjunct issue prospectively, explicitly preserving frozen numeric thresholds; do not silently omit or remap it after seeing data.
  2. State the estimand as the effect of adding the configured adapter/training regime with LoRA configuration held constant. Record initialization hashes and the inherited RNG order; do not silently change frozen seeds or constructor semantics to claim stronger matching.
  3. Confirm identical target IDs, five-donor lists, donor crops, tokenizer/loss/mask, and seed/document pairing across E01/E11. Implement the new arm routing only after separate approval.

## Q3. Route STOP vs track STOP; complete interpretation

- **Verdict: conditional — route/track separation is substantially fixed; the decision branches and uncertainty rules are incomplete.**
- **Evidence:** V2 §§0/5/11 removes V1 §8's resident-track STOP and explicitly says a double-negative result is **not** proof that EG2 features lack information. The defensible ceiling is **“EG2-raw→mT5-decoder route as configured”**, meaning layer19, these cells, these LRs, **100 updates**, and this donor assay/cohort. V2 §11 excludes the entire-track keep/stop decision. This revision is sufficient to reject the old track-level inference; neither H3 nor the EG2 track is automatically killed.
- **A failed positive predicate is not proof of absence.** A cell can miss mean **.05**, CI lower **>0**, or **2/3** seed consistency while retaining an uncertain positive effect. Define negative as “did not meet the preregistered signal criterion,” not “contains no information.” Missing seed, fewer than **15** paired eligible documents, invalid endpoint, and cap exhaustion must be distinct from valid negative.
- **The primary inference needs its own uncertainty rule.** V2 §5 specifies the paired document contrast and **1,000 PCG64 resamples, seed 20261109**, but its adapter-loss branch only says `E01−E11 >0`. A positive point estimate plus one passing and one failing cell is not sufficient evidence that the cells differ. Report the paired contrast's mean and **95% CI**, with the directional evidence rule specified before execution (e.g. lower bound **>0** for affirmative positive contrast). This clarifies the new contrast rather than retuning the inherited within-cell thresholds.

| Valid registered result | Permissible interpretation/action ceiling |
|---|---|
| E01 positive, E11 negative, paired positive contrast supported | Adapter-associated loss under the configured regime is supported; architecture/LayerNorm causation is not uniquely identified. H3 is a possible separately approved next diagnostic. |
| E01 positive, E11 negative, contrast uncertain | Asymmetric threshold crossing, not established between-cell loss. Report uncertainty; no automatic H3 execution. |
| Both negative | No affirmative registered donor-signal evidence in these configurations. A bounded route STOP may be an operational decision, not proof of equivalence, feature insufficiency, or track failure. |
| Both positive | Adapter-free acquisition is possible; adapter is not necessary for meeting this criterion. Still report the primary effect: both-positive does not imply equal signal or zero adapter-associated attenuation. |
| E01 negative, E11 positive | Adapter-bearing regime succeeds where adapter-free does not meet the criterion; check/report the opposite-direction contrast. No raw-route negative may stop the adapter-bearing route. This branch is absent from V2 §5. |
| No supported contrast / overlapping uncertainty | Adapter effect not demonstrated. `E01≈E11` is not established equivalence without a prospectively defined equivalence design. |
| Copy-only, full-only, invalid, missing, or interrupted | Preserve the endpoint/validity distinction; not a binary route-negative result. |

- **Next steps:**
  1. Make the §5 interpretation table exhaustive and explicitly define positive/negative, including copy/full disagreement and not-assessable cases (P6 §§3.3–3.4/6 distinguish these).
  2. Bind adapter-loss support to the paired contrast's preregistered uncertainty rule, not merely unequal cell significance labels or a positive point estimate.
  3. Describe route STOP as a bounded operational option after a valid complete R result. Keep track decisions, H3 approval, and B0-B/B1/B2/Stage C separate.

## Q4. M/signal separation and E00 baseline

- **Verdict: agree on separation and record arithmetic; conditional on preserving domains and reporting validity.**
- **Evidence:** V2 §§3/4/6 correctly separates M from donor signal and makes M **not a signal gate**. For each cell/seed, **15 targets ×2 variants ×2 endpoints ×2 memory kinds =120 M records**; **4×3×120=1,440** in R and **480** in D1. M is fixed-prefix **K=753**, donor-free, and uses real versus `M_POS_MEAN`/`M_NORM`. All four cells now have EG2 memory, so Phase 6's mixed native-20 **1,680**-record domain must not be reused.
- **Signal has a different population/path:** evaluate **20 val documents ×5 donors**, but primary inference is on the exact **15 common documents**, seed-averaged before paired document bootstrap. **3×15=45** seed-document values are not 45 independent document units. M's **120** records are likewise not 120 independent observations. Signal uses `K=min(len(real),len(donor))`, not a universal 753 truncation. Training uses real memory with no donor; short training/val documents are not dropped (P6 §2.3).
- **Phase 7 is not the signal endpoint:** **15×5×2×2×2=600** records/cell/seed, **2,400** D1 and **7,200** R, at `K_d=min(753,len(real),len(donor))`. Results synthesis §4 reports L **−0.0407** from the phase-7 diagnostic versus **−0.1135** from unit-final donor-crop signal; L's descriptive val20 mean is **−0.0222**, also not the primary 15-doc estimate. V2 needs to retain those distinctions in its artifact/label binding.
- **Why M is not a gate:** Cause §1 reports L M control-real delta **0.365** while wrong-real is **−0.017** in that diagnostic table; its donor-signal result is copy **−0.1135**, CI **[−0.2341, −0.0012]**, **6/15** positive documents, **0/3** positive seed means. These measurements can coexist because M measures advantage over a mean representation, not donor specificity. They are not interchangeable endpoints or a reason to rescue the frozen Phase 6 negative.
- **E00:** retain its raw-memory M/signal measurements descriptively. Repeating the same deterministic frozen baseline across three seed-labeled records does not create three independent trained replicates or establish training reproducibility. Do not call E00 a trained control or use it to subtract a clean training effect.
- **Next steps:**
  1. Specify exact F0 M and phase-7 key domains and bind the primary contrast only to unit-final donor-crop deltas on the unchanged 15 common IDs.
  2. Preserve seed completeness, copy-token eligibility (**at least 5**), finite CE, exact pairs, and no **15→14** substitution. Separate artifact validity from scientific M_PASS; M failure/NA must not silently select which signal results are reported.
  3. Report M, raw donor signal, primary contrast, E00 baseline, and E01/E11 signal tails separately. No extra native P/PA rerun is required by this review.

## Q5. Compute realism on CPU, six threads

- **Verdict: defer on demonstrated feasibility; conditional plausibility, not a supported 120-minute guarantee.**
- **Evidence:** V2 §§4/9 sets D0 **15 min**, D1 **25 min**, R **120 min**: an aggregate ceiling of **160 min**, not a 120-minute all-stage budget. R's **900** optimizer updates is correct: **3 cells×3 seeds×100**; E00 still contributes evaluation/generation overhead in **12 evaluated units**. P6 §11 originally budgeted **1,200 updates/120 min/6 threads**, but a prior budget is not a measured F0 throughput bound. Draft synthesis §3 MF-6 mentions historical **82 min** and §3 MF-2 mentions **~87 min**; neither is a per-phase F0 six-thread measurement supplied by this revised plan.
- **Evaluation is substantial despite fewer updates.** With Runner `eval_arm_d1()`'s real/wrong forward loop, one step0 or final evaluation is **20×5×2=200 teacher-forced forwards** per unit. Two checkpoints yield **400/unit**, **1,600** in D1 and **4,800** in R before M, phase-7 diagnostics, replay, or generation. Phase-7's **600 records/unit** are not 600 independent forwards: copy/full share logits and raw CE repeats across variants, while variant-specific baseline CEs add work. Runner caches those baselines by crop; account for actual calls rather than using record count as runtime.
- **Generation remains large:** **80 sequences** in D1, **240** in R; at the inherited **max_new_tokens=256** (P6 §2.5.7), the respective upper output-token counts are **20,480** and **61,440**. Early EOS may reduce work, but cannot be assumed from a favorable cell. Checkpoint/model load, controls, primary replay, diagnostic replay, and reporting also need explicit accounting. V2 §10 names `f0_replay.json` without specifying whether replay work is included in the cap.
- **D1 cannot certify R by update scaling alone.** If D1 measures the same per-unit nontraining work as R, let B be the four-cell total of that work and S the sum of one training-update time for E10/E01/E11. Then approximately `D1=B+S`, `R=3B+300S=3*D1+297S`, before any R-only overhead. At a full **25-minute** D1, only **45 minutes** remain under R's **120-minute** cap for the incremental training term and extra overhead. This is a workload identity under stated assumptions, not a benchmark or prediction.
- **Current code is not F0:** V2 §8 correctly says new arms are needed. Runner's current registered path does exist: `main()` dispatches `--mode registered --arm ... --seed ...` to `run_registered_unit()`, so Results synthesis §3 MF-1's historical assertion that it rejects registered mode is stale at this HEAD. Nevertheless `ARMS/arm_spec()` still accepts only **F/L/P/PA**, `optimizer_for()` cannot train E00, and both D1/registered functions unconditionally build a native cache. Reusing that path unchanged would misroute raw EG2 arms or waste native-encoder work; its existence is not proof of F0 implementation or timing.
- **Next steps:**
  1. Before execution approval, document a per-phase F0 projection and cap boundary, including initial/final eval, all generation, load/save, controls, primary replay and phase-7 work. Use the inherited P6 §11.5 projection structure; if adopting its **≤96 min** headroom rule, explicitly bind it to F0 rather than silently assuming inheritance.
  2. After separate approval only, obtain all required timings from the registered D1 mechanics path on the actual six-thread execution environment. No timing probe, training/evaluation, retry, or extension is authorized by this consultation.
  3. Predefine complete-unit scheduling and hard-abort reporting. If the fixed design cannot fit, return for preregistration/approval; do not drop seeds, donors, endpoints, steps, or slow cells to manufacture a complete positive/negative result.

## Q6. H3 separation

- **Verdict: agree — keep LN/projection/residual outside the primary experiment.**
- **Evidence:** V2 §7 lists **E01-LN**, **E01-P**, and **E01-R**, expressly requiring a separate preregistration/approval and prohibiting H3 execution here. They answer different mechanistic questions from the primary adapter-regime contrast and add compute, comparisons, and implementation degrees of freedom. None is necessary to answer whether the configured E01/E11 regimes differ. A positive contrast motivates H3; it does not identify its answer. A negative contrast does not automatically make H3 scientifically pointless or authorize it.
- **Mechanistic limits remain material:** Cause §2 reports P copy delta **3.076** versus PA **0.011**, paired **+3.065**, **14/15** positive documents. These are native-path observations, not raw-EG2 evidence. Cause reports EG2 variance **4.883→0.085/0.081**, yet PA variance **0.841→1.284** with signal loss; mean-vector contraction is therefore not a unique explanation. The adapter is **512→512**, not a width bottleneck. Cause §6's legacy claims “F0 positive → cause confirmed” and “F0 ~0 → feature itself insufficient” remain stronger than its correction §9 and V2 §5; do not import those claims into F0.
- **Separate H3 needs exact interventions:** fixed LayerNorm must define affine parameters/epsilon/statistics; a fixed orthogonal projection preserves information geometrically but can disrupt decoder-coordinate alignment; `x+Adapter(x)` retains an identity path but is not identity at random initialization. These are reasons to preregister H3 precisely, not add arms opportunistically to F0.
- **Next steps:**
  1. Keep all three H3 arms out of primary D0/D1/R and its **900-update** budget.
  2. In a separate proposal only, specify initialization, frozen/trainable components, LoRA settings, residual scaling/identity condition, endpoints, comparison rules, and cap.
  3. Keep H3 approval and any track decision independent of the F0 label; no automatic next-stage execution.

## Final STOP / NARROW / CONTINUE block

```text
Final verdict: NARROW

Stage D/R:
  The original signal-selection gate is removed. Retain mechanics-only D0/D1
  and the fixed three-seed R; clarify technical pass criteria, fresh starts,
  and E00=0 D1 updates (3 actual D1 optimizer updates, not 4).

2×2:
  Accept E01−E11 as the primary configured-regime contrast. E00 is eval-only;
  no clean full trained-factorial interaction or architecture-only claim.
  Resolve inherited predicate bindings and document RNG/initialization limits.

Interpretation:
  Route as configured only, never EG2-track STOP from these results.
  Add the E01-negative/E11-positive, uncertain-contrast, partial-endpoint,
  invalid/missing and interrupted branches. Non-significance is not equality.

M/signal:
  Accept 120 M records/cell/seed, 1,440 R M records and separate donor signal.
  Infer on exactly 15 paired documents after seed averaging; M is not a gate.
  Keep donor-crop signal, phase-7 diagnostics and E00 baseline distinct.

Compute:
  900 R updates is correct; total time ceiling is 160 minutes across stages.
  F0 completion within R's 120 minutes is unverified. Require prospective
  per-phase accounting and, only after approval, D1-based timing evidence.

H3:
  Separate preregistration/approval. Do not add LN/projection/residual to F0.

Must-fix (ranked):
  1. Bind cell-level copy/full/consensus predicates and the primary contrast;
     resolve the missing legacy L>F conjunct explicitly, retaining numeric
     thresholds, and specify uncertainty/NA and all interpretation branches.
  2. Correct the mechanics contract: E00 no optimizer, three D1 updates,
     four-cell adapter vector, objective mechanics checks and fresh R states.
  3. Define F0 runtime/projection/replay/cap accounting and incomplete-run
     semantics; no outcome-dependent cell/seed/workload selection.
  4. Bound causal language to configured training regimes and make inherited
     RNG, donor/crop/cohort and exact record-domain bindings explicit before
     separately approved F0 implementation.

Incorrect premises:
  - Same LoRA configuration/seed means identical initial or trained weights.
  - Four evaluated cells require four D1 optimizer updates.
  - Unequal significance labels prove a between-cell difference.
  - Both cells failing a positive criterion proves no usable EG2 information.
  - Both cells passing means equal signal; an uncertain contrast proves equality.
  - M_PASS or phase-7 delta is the primary donor-signal endpoint.
  - 900 updates alone establishes a six-thread 120-minute completion guarantee.
  - Historical lack of registered-mode support still describes this HEAD.
  - A residual skip path is automatically exact identity at initialization.

Disposition:
  Revise the preregistration contract, then seek separate approval. This review
  authorizes no implementation, D0/D1/R/H3 execution, B0-B/B1/B2/Stage C,
  threshold/seed/donor/step/LR change, test 163/P1 use, or T5Gemma2 restart.
  Phase 6 remains negative; B0-B remains unapproved; D-108 STOP is unchanged.
```