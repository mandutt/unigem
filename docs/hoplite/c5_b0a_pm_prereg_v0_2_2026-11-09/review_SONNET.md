# External Review — C5 B0-A Phase 6 P/M Prereg v0.2

**Reviewer identity:** Claude Sonnet 5.5, reasoning **high** (independent round; no other reviewer's answer was read or reused; no subagents or additional LLMs were called).
**Review basis:** `origin/main` HEAD `918cfa5` (`docs: add C5 P/M prereg v0.2 review request`). `git fetch origin` and `git pull --ff-only origin main` both succeeded ("Already up to date"). The workspace is a depth-1 clone, so file history is not available. The request cites 8c4f197 as the authoring HEAD. I read the v0.2 plan as it exists at 918cfa5 and did not diff it against 8c4f197.
**Read in full:** the review request (352 lines), `docs/plan_c5_b0a_pm_prereg_v0_2.md` (405), v0.1 (314), the 3-AI synthesis (211), the P0 report (116), `runner/c5_mt5_lora_b0.py` (802), `eval/tests/test_c5_b0_metric.py` (128). For grounding I also read `reports/C5_B0A_REPAIR_2026-11-09.md`, `reports/provenance/C5_b0a/p0_native_sanity.json` (per-doc values), and the head of `aggregate.json`. I also read `LoRALinear` in `runner/c5_a1_lora.py` and `Adapter` in `runner/c5_mt5_layer_probe.py`.
**Not done:** no training or evaluation, no test 163, no P1, no external APIs, no repository edits. This file is the only write. I created its parent directory to hold it.
**Status of this report:** consultation only. It approves nothing for Phase 6, B0-B, B1, B2 or Stage C. T5Gemma2 stays closed under D-108.

---

## 0. Bottom line

**Verdict: NARROW.** v0.2 is a real improvement over v0.1 and closes most of the 12 Must-fix items on paper. It is not yet safe to freeze, because several gaps would be encoded into code by the implementer:

1. The label table is not a total function. `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE` is defined in §6.3 but missing from the §6.4 table. PA appears in no label. Single-label precedence can hide a positive L signal.
2. The P gate floor of `.05` is about 1% of P0's observed effect. PA has no step-0 reference and starts in a different regime from P0.
3. `M_POS_MEAN` is a norm-shrunk, out-of-distribution input, so "real beats mean" does not isolate content use.
4. Pooling, "L > F" and "2/3 seeds" are still under-specified at the level needed to code them.
5. The debug protocol would reveal a registered seed's results before the 3-seed gate.

These are mostly small text-level fixes made **before any result exists**, so threshold changes at this stage are pre-registration, not post-hoc tuning. I recommend a **v0.2.1 errata commit** closing Must-fix MF-1 to MF-6 (§7). After that: approve implementation plus non-gating mechanics debug only. Do not approve the 3-seed run.

---

## 1. Short answers to the five core-focus questions

1. **Does v0.2 fix the near-vacuous P gate and the adapter-regime confound?** Partly.
   - The gate is no longer literally vacuous. It adds a full-CE condition and a `.05` floor, and it measures after training.
   - In practice it detects only near-total erasure. The floor is about 1% of P0 (val +5.24, train +3.76), and `P_RETENTION` is descriptive only.
   - PA is the right control idea, but as written it has no step-0 reference and no label consequence.
2. **Is eval-only M with full-real-K and P/PA validation adequate?** Eval-only M and the full-real-K reference are correct. The validation and decision rule are not yet adequate. The validation checks that M is detectable, not that it is fair (norm/OOD confound, survivorship, no checkpoint persistence).
3. **Are the new labels and full-CE co-primary free of overclaim?** Mostly, but there are contradictions: a missing cell, precedence masking, and a causal name (`REGIME_ERASES_SELECTIVITY`). "Copy" still appears in `L_COPY_SIGNAL` and `COPY_ONLY_WEAK` even though the as-run mask is not copy-specific.
4. **What Must-fix remains?** See §7 (MF-1 to MF-6).
5. **STOP / NARROW / CONTINUE?** **NARROW**, with the approvals in Q12.

---

## 2. Q1–Q12

### Q1. P gate

- **Verdict: conditional.** Better than v0.1, still weak as a regime test.
- **Evidence**
  - v0.1's `P_POSITIVE` was `mean Δcopy > 0 and CI lower > 0`. v0.2 adds `mean Δcopy ≥ .05`, `Δfull > 0` and the full CI lower bound. It also moves the measurement to step 100 and adds a step-0 reference.
  - P0 val is +5.2375 CI [2.50, 8.08], train +3.7617 CI [1.89, 5.61]. A floor of `.05` is about 1% of those means. `P_VALID` therefore fails only if training erases about 99% of the effect, or if the 20-doc bootstrap CI becomes too wide to exclude 0. Even then, `REGIME_ERASES_SELECTIVITY` would be a mislabel (see Q5).
  - `P_RETENTION = Δ_step100/Δ_step0` is "descriptive; not a hidden gate" (§6.1).
  - P has no adapter and is trained with LoRA only. In the runner, `lora_lr` defaults to 1e-4, 100 updates, batch 1, 20 docs cycled (`train_arm`). `LoRALinear.lora_B` starts at zero. Adam moves each B entry by at most about 1e-2 over 100 steps. v0.2 does not state P's learning rate or require a log of how far P moved. P step 100 may therefore sit close to P0, which would make `P_VALID` a re-run of P0 rather than a test of the trained regime.
  - The Δ scales differ by about two orders of magnitude. P0 Δ is 3–5 nats. The old-metric B0-A frozen per-doc values lie roughly within ±0.3, mostly below 0.15 (`aggregate.json`; compromised metric; I eyeballed this, not recomputed). The shared `.05` floor means different things in the P regime and the F/L regime.
  - Both P0 val and train carry most of the mean in a few documents. Val top-3 share is .4862 (I verified: 19.13 + 17.55 + 14.24 = 50.9 of about 104.75). Val has 2 non-positive docs and train has 6. Untrained real CE is 12.70 and 13.24, above ln|V| = 12.43. So Δ measures catastrophic wrong-memory penalty, not graded content use (P0 report §3).
- **Next steps**
  1. Pre-register, before any debug, how P/PA movement is reported: step-0 vs step-100 real val CE, train CE first/last/last-10, LoRA B and adapter parameter delta norms, and the learning rates actually used (state P/PA LoRA lr 1e-4 and adapter lr 1e-3 explicitly).
  2. Decide now between two options, and freeze the choice.
     - (a) Add a retention floor to `P_VALID`. A value around .25 is a reasonable order of magnitude, but the authors must choose it before the debug run.
     - (b) Keep `P_RETENTION` descriptive, but forbid any wording such as "P preserved selectivity" unless retention and movement are shown.
     - I prefer (a). If (b) is kept, add a label `P_VALID_UNINFORMATIVE` when P barely moves.
  3. State that P_VALID supports only "the metric/decoder-LoRA path is not broken". It does not support "graded content use" or "regime-equivalent to F/L".

### Q2. PA arm

- **Verdict: conditional.** The right control, incompletely specified.
- **Evidence**
  - PA = native memory + `make_adapter(seed)` + LoRA 64, with the same adapter and LoRA settings as L. That does isolate "adapter-as-soft-prompt plus LoRA" from "EG2 memory" (L vs PA differ only in the memory source).
  - Gaps
    1. **No step-0 reference.** P0 is native memory with no adapter. PA at step 0 passes native memory through a randomly initialised MLP with LayerNorm. The repair debug shows that F/L at step 1 have CE 27.44, far above ln|V| = 12.43 and above P0's 12.7/13.2. PA likely starts in that catastrophic random-adapter regime (not measured). `REGIME_ERASES_SELECTIVITY` is defined only for "P0 positive but P step100 invalid". PA has no equivalent.
    2. **No label consequence.** §6.1 says "PA가 P보다 selectivity를 크게 잃으면 adapter soft-prompt risk로 기록" with no quantity and no effect on §6.4. If P is valid and PA is not, L's non-signal is uninterpretable, yet the table still allows `INCONCLUSIVE_SMALL_N` or `EXPLORATORY_L_SIGNAL` unchanged.
    3. **Donor mismatch.** P/PA donors use native tokenised length; F/L donors use cache hidden length (§4). Cross-arm L vs P/PA paired contrasts are not paired on donors. Use P/PA only as validity gates, never as magnitude comparators to L.
    4. The adapter ends in `LayerNorm(512)`, so each memory row has near-fixed norm. This matters for M (Q4).
    5. PA/L/P share seeds. L and PA share RNG order (`make_adapter(seed)` then LoRA init), but P's LoRA A init is drawn from a different RNG state. Do not claim P-vs-PA is initialisation-matched.
- **Next steps**
  1. Add an explicit interaction table with cells for (P_VALID, PA_VALID) = (T,T), (T,F), (F,T), (F,F). The (T,F) cell needs a name along the lines of `ADAPTER_REGIME_ERASES_SELECTIVITY` (descriptive), and any L non-signal in that cell must be reported as uninterpretable (not "no evidence").
  2. Define PA's step-0 reference as the PA untrained forward on the same docs and donors, in addition to P0. Record it, but do not let it gate.
  3. In the artifact, record both `PA_VALID` and the full per-doc Δ for PA, and state that L-vs-PA is not donor-paired.

### Q3. M real reference

- **Verdict: agree, with two conditions.**
- **Evidence**
  - The mean is built at length `K_real`. The like-for-like comparison is real memory at `K_real` vs mean memory at `K_real`, same labels, same checkpoint. Donor-cropped real memory (length `k = min(len_real, len_donor)` in `evaluate_arm`, `p0_eval_split`) answers a different question: wrong vs prefix-cropped real. Mixing the two would confound crop with intervention. v0.2 §2.5, §4 and §5.2 fix this correctly.
  - The two references differ in more than length. In `evaluate_arm` the real memory is `adapter(h_real[:k])`, a crop of the full-doc EG2 cache. In `p0_eval_split` real memory is re-encoded from `real_ids[:k]`, a different object from a crop of full-doc hidden states. The P/PA native path therefore changes the encoder context as well as the length. In P0, the shorter doc of a pair keeps its EOS under cropping and the longer one does not.
  - Δshuffled uses the cropped real CE and Δmemfree uses the full-K real CE. Subtracting or comparing them directly is invalid.
- **Next steps**
  1. Store per doc: `real_full_ce@K_real`, per-donor `real_full_ce@k`, and the crop effect (difference). For every donor with `len ≥ K_real`, the cropped and full values must be identical. Make that an executable reconciliation test, because it checks the two code paths against each other.
  2. State in the report that Δshuffled (donor-cropped reference) and Δmemfree (full-K reference) are different estimands and are never combined or differenced.

### Q4. Mean-memory definition

- **Verdict: conditional.** Leakage-free in the label sense, not sufficient as a negative control.
- **Evidence**
  - **Norm/OOD confound.** L's adapter ends in LayerNorm, so every row has a near-constant norm of about √512 × γ. The position-wise mean of such rows across 10–20 docs shrinks substantially in norm. `M_POS_MEAN` is then an out-of-distribution input, and "real beats mean" can hold for a content-blind decoder that is merely sensitive to memory statistics. v0.2 adds `M_NORM` as secondary, but `M_CONTROL_PASS` is defined on `M_POS_MEAN` alone (§6.3). That is the weakest variant.
  - **M_VALID tests detectability, not fairness.** P0's wrong memory already drives CE above uniform (16.5–18.5 vs 12.43). A mean memory in the P/PA setting is likely also catastrophic. A P/PA M check passing therefore says "the intervention is detectable", not "the intervention removes content only".
  - **Ambiguity.** `M_VALID` reads "P/PA의 M_POS_MEAN ... real_full < mean_full". It does not say whether P and PA are both required, whether per-seed or pooled, or whether the CI is the same document bootstrap.
  - **Survivorship.** The `len(h_i) ≥ K_real` eligibility filter excludes long targets and thins the mean at far positions. `m_eligible=false` removes docs. The report must show that real-vs-mean is computed on the same eligible docs, and say how many docs were excluded. v0.2 does not set a minimum for the M gate to be evaluable.
  - **Target-derived scalars.** `K_real` and the `M_NORM` scale come from the target's own input. That is acceptable for an input intervention but should be stated, since the doc says "target 사용 금지".
  - **Missing checkpoint persistence.** `train_arm` returns a result dict and does not save adapter or LoRA state. Eval-only M needs the final L state. Either evaluate M in-process immediately after training, or save state dicts and hash them. v0.2 lists "checkpoint hash" in artifacts without saying how the checkpoint is held.
  - **Position-wise mean semantics.** T5 cross-attention has no relative position bias. `M_POS_MEAN` and `M_GLOBAL` therefore differ only through position-specific content in the rows. Claims about "positional" structure should be avoided.
- **Next steps**
  1. Define `M_CONTROL_PASS` to require pass on **both** `M_POS_MEAN` and `M_NORM`. If only `M_POS_MEAN` passes, report the qualified outcome `M_PASS_NORM_CONFOUNDED` and do not treat it as pass. Specify the `M_NORM` scale (a whole-matrix Frobenius norm or per-row; pick one).
  2. Specify the `M_VALID` quantifier (both P and PA, pooled across seeds, same CI rule). Set a minimum number of m-eligible val docs below which the M gate is `M_NOT_EVALUABLE`.
  3. Add the invariants listed in Q9, and require final-state evaluation in-process or from a hashed checkpoint.

### Q5. Decision labels

- **Verdict: disagree as written; fixable.**
- **Evidence**
  - **Missing cell.** `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE` is defined in §6.3 but absent from the §6.4 final table (it appears only at lines 27 and 243 of the v0.2 plan). The table says "otherwise → INCONCLUSIVE_SMALL_N". Two sections give different outputs for the same condition (M fail, no L signal).
  - **PA is absent.** No row mentions `PA_VALID`. `EXPLORATORY_L_SIGNAL` can be emitted with PA invalid.
  - **Precedence hides results.** If `M_VALID` is false, the label is `M_CONTROL_NOT_VALID` even when `L_SIGNAL` is true. If P step 100 is invalid, the label is `REGIME_ERASES_SELECTIVITY` regardless of L. A single precedence label discards a positive L signal from the headline.
  - **Copy-xor-full vs M.** `COPY_ONLY_WEAK` or `FULL_ONLY_WEAK` is reached without checking `M_CONTROL_PASS`.
  - **Causal name.** `REGIME_ERASES_SELECTIVITY` asserts a mechanism. A P step-100 failure can come from small n, a wide CI, tail-driven variance, or insufficient training. The name should describe the observation.
  - **"Copy" in labels.** `L_COPY_SIGNAL` and `COPY_ONLY_WEAK` carry the word "copy". §5.3 says the word is for the as-run mask only, but P0 Δcopy ≈ Δfull (3.76 vs 3.50, 5.24 vs 5.29) and as-run coverage is .82–.84.
  - **Full has no floor.** `L_FULL_SIGNAL` requires only Δfull > 0 and CI lower > 0. Only the copy half has the `.05` floor, so `L_SIGNAL` is effectively `Δcopy ≥ .05` plus a sign check on Δfull.
- **Next steps**
  1. Make the output a **vector of independent flags** (`ASSAY_OK`, `P_VALID`, `PA_VALID`, `M_VALID`, `M_PASS_POS`, `M_PASS_NORM`, `L_COPY`, `L_FULL`, `TAIL_DRIVEN`) plus a **total, deterministic headline function** over those flags. Unit-test every combination. The headline may never suppress a true `L_SIGNAL`: it must be reported as a flag even when the headline is a validity failure.
  2. Add the missing rows (`NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`, PA cells, copy-xor-full with M status). Rename `REGIME_ERASES_SELECTIVITY` to an observational name such as `P_STEP100_NOT_VALID` (keep the old text as a hypothesis in the narrative).
  3. Footnote "copy" everywhere as "as-run-mask CE (coverage .82/.84; not copy-specific)". Add a floor or explicit "no floor" statement for the full CE.

### Q6. Copy vs full

- **Verdict: agree with co-primary, and requiring both is not excessive.**
- **Evidence**
  - With as-run coverage .8246/.8351, the as-run copy mask covers most label tokens. Δcopy and Δfull are nearly collinear. Requiring both costs little, but it also adds little independent evidence. The two together are not evidence of copy-specificity.
  - The only copy-specific measurement is the strict mask (`piece_len ≥ 2`, coverage .2427/.2161), which v0.2 demotes to exploratory secondary. That is right, but "exploratory" should not become "ignored" if someone wants to say anything about copying.
  - Δfull equals the built-in `out.loss` difference and is unaffected by the original alignment bug (REPAIR report). It is the safest quantity.
- **Next steps**
  1. Keep both co-primary. State plainly that agreement of the two is expected and does not establish copy-specificity.
  2. Add `Δnoncopy` (full minus as-run-copy tokens) and the strict-mask delta as descriptive columns. Any "copy" language needs a strict-mask or noncopy contrast.
  3. Do not drop the `.05` floor on copy. Either add a stated floor to full or say explicitly that the full condition is a sign test only.

### Q7. Heavy tail and power

- **Verdict: conditional.** The diagnostics are the right ones; their interpretive limits need to be written down.
- **Evidence**
  - P0: val median 2.9739 vs mean 5.2375; top-3 share .4862 (train .4222, median 4.068). Val per-doc range −5.78 to +19.13, with only 2/20 non-positive docs; train has 6/20 non-positive docs.
  - Three seeds on the same 20 documents do not add document-sampling power. They add training/initialisation variability only. The effective sample for content claims stays n = 20.
  - 1,000-resample percentile bootstrap on 20 heavy-tailed values is anti-conservative (v0.2 §7 acknowledges this). Documents also share donors within val (the length-nearest among the same 20 docs), so docs are not independent.
  - Old-metric F/L per-doc Δ is roughly ±0.1–0.3. A mean of `.05` against an SE of about 0.02–0.03 means roughly marginal power at the floor. I did not recompute this.
  - Whether the P0 tail pattern persists after training is not yet known.
- **Next steps**
  1. Write the "detectable" and "forbidden" lists into the prereg.
     - **Detectable:** catastrophic path failure; whether L's mean Δcopy clears the floor with a document-bootstrap CI above 0 in this sample; sign consistency across 3 seeds (seed-level means).
     - **Forbidden conclusions:** graded content use; absence of content use; copy-specificity; generalisation beyond these 20 val docs; magnitude comparison between L and P/PA; treating 3 seeds × 20 docs as 60 independent units; any inference from CI lower > 0 alone when `leave-top-3-out` flips sign.
  2. Add a `TAIL_DRIVEN` descriptive flag: `leave-top-3-out` mean ≤ 0 or median ≤ 0 while the mean passes. It does not gate, but it must be printed next to any positive label and must be reproduced in the B0-B condition list (it already is in §12).
  3. State that pooled CIs are computed over documents after averaging each document's Δ across seeds. Per-seed CIs are informational only.

### Q8. Compute and implementation

- **Verdict: conditional.** The compute is plausible; the code gap is larger than the plan implies.
- **Evidence**
  - **Compute.** The work is mT5-small, one document per step, 100 steps, 12 trained units, an eval of 20 docs × 5 donors × 2 forwards, and M evals (about 3 means × 20 docs, plus P/PA). All of it is small on CPU. The largest cost is generation: `load_base()` sets `config.use_cache = False`, so greedy generation up to 256 tokens re-runs the full decoder each step. That is about 20 docs × ≤256 steps × 12 units. I have not measured it. I expect it to fit in 2 hours but do not know.
  - **Cap wording.** "≤2 CPU-hours, 6 threads" is ambiguous (CPU time vs wall time).
  - **Code state (pm-diagnostic does not exist).**
    - `set_training_mode` accepts only `frozen`/`lora` and requires an adapter, so P needs a no-adapter policy and PA needs a third policy.
    - `train_arm` is hard-wired to the EG2 cache, `make_adapter` and `donors_for` (cache lengths).
    - `bootstrap_paired` returns a key named `seeds_positive` that counts documents (as flagged in the synthesis).
    - `evaluate_arm` has only the donor-cropped real reference.
    - No checkpoint is written.
    - The test file has 7 tests; the "54 tests" is a suite-level historical figure that I did not re-run.
- **Next steps (ranked Must-fix for implementation)**
  1. Add the P/PA arm paths: native memory source, no-adapter policy, `torch.manual_seed(seed)` before LoRA init, explicit lr per arm, and the same `set_training_mode` asserts (64 modules, base eval, `trainable_base_parameters == 0`).
  2. Add the M builder and evaluator: train-only mean, eligibility, full-K real reference, `M_NORM`/`M_GLOBAL`, leakage assertions, and an in-process or hashed-checkpoint final state.
  3. Add the stats module: per-doc seed averaging, document bootstrap, per-seed means, "L > F" as defined in the errata, tail diagnostics, and the total label function. Rename the document-count key.
  4. Define the cap as **wall-clock** hours on 6 threads. Log per-phase timings. Stop at the cap with no retry.

### Q9. Tests required before implementation

- **Verdict: agree with the list in D3; several are underspecified, and some are missing.**
- **Must exist before the first debug run**
  1. P and PA each attach exactly 64 LoRA modules, base in eval, `trainable_base_parameters == 0`, adapter present only for PA, LoRA dropout in train mode, and `torch.manual_seed(seed)` called before LoRA init. Assert reproducibility by checking that two inits with the same seed give identical `lora_A`, and different seeds give different ones.
  2. **P step-0 equivalence.** Zero-LoRA P in the new runner reproduces the stored `p0_native_sanity.json` per-doc deltas (donors, K, cropping) within a tolerance. This ties `P0` to the new code path.
  3. **M leakage.** Mean construction is invariant to (a) permuting train-document order, (b) replacing the target document's text or label with anything else (only `K_real` and the `M_NORM` scalar may change), and (c) donor identity. The mean source IDs are a subset of the 20 train IDs and disjoint from val.
  4. **M reconciliation.** For donors with `len ≥ K_real`, cropped real CE equals full-K real CE (Q3).
  5. **Real-vs-real null.** Replacing the "mean" with the real memory itself gives Δmemfree exactly 0.
  6. **Labeler totality.** Run the label function over all combinations of the flag vector. Every combination gives exactly one headline. `L_SIGNAL` true is never lost from the flag output.
  7. **Aggregation.** `documents_positive` and `seeds_positive` are separate keys. `seeds_positive` is computed from seed-level means. Add a test with a synthetic case where documents are mostly positive but seeds are not.
  8. Full CE equals built-in `out.loss` for all new paths (atol 1e-5), including full-K M.
- **Next steps**
  1. Write these as fixtures that need no model weights where possible (labeler, aggregation, leakage on synthetic tensors).
  2. Keep any test that needs mT5 weights behind the existing `skipUnless(MODEL.exists())`.

### Q10. 1-seed debug

- **Verdict: conditional.**
- **Evidence**
  - v0.2 §10 allows a non-gating 1-seed debug but does not say which seed or how many steps. Seed 20261108 is one of the three registered seeds. A full 100-step run on it would reveal P/PA/M outcomes before the 3-seed gate and would tempt design changes, even if declared non-gating.
  - Registered artifacts (`reports/provenance/C5_b0a/pm/{arm}_{seed}.json`) are listed but there is no pass/fail checklist for debug.
- **What debug may do (mechanics only)**
  - Use either a short run (for example ≤10 steps) on the registered seed, or a full run on a seed outside {20261108, 20261109, 20261110}. State which in the errata, before running.
  - Check: path/shape/finite, 64 modules, mode policy, seed behaviour, metric alignment (atol 1e-5), artifact completeness, per-phase timing, M leakage/invariance tests passing on real tensors, and that the label function runs on synthetic fixtures.
  - Check that LoRA and adapter parameters actually moved (train CE first/last, parameter delta norm). This is a mechanics check, not a selectivity check.
- **What debug may not do**
  - Compute or cite a Phase 6 label from debug values. Change thresholds, donors, seeds, steps, learning rates, floors or label rules based on them. Treat the run as a replacement for any of the 12 trained units.
  - Any code change after debug must be a bug fix that does not alter a registered definition, listed in a commit message.
- **3-seed gate conditions**
  1. A frozen commit hash of the prereg (v0.2.1) and runner.
  2. All Q9 tests green, with output recorded.
  3. A debug artifact set with complete provenance fields, timings and `test_split_used:false`.
  4. A written extrapolation of wall time against the 2-hour cap.
  5. Explicit user approval.

### Q11. B0-B boundary

- **Verdict: agree.** Not auto-approving B0-B is correct.
- **Evidence**
  - The plan's own list (§12) calls its conditions necessary and not sufficient. The 20 val docs (`val[5:25]`) have been used in B0-A, P0 and Phase 6, so they cannot serve as a confirmatory set. P0's val is reused with the same docs and is explicitly "not confirmatory" (§4).
  - Δ is teacher-forced CE. It says nothing yet about generation quality, and generation telemetry is non-gating here.
  - M pass does not establish semantic content use. A pass is also consistent with document-specific length, format or lexical cues.
  - The "300/95" B0-B size is not justified by anything in Phase 6.
- **Next steps (necessary conditions for a B0-B proposal; none sufficient)**
  1. A new preregistration with its own approval, thresholds fixed before any run, and a stated power analysis built from the per-document variance observed in Phase 6.
  2. A held-out set not used by B0-A, P0 or Phase 6. Test 163 and P1 stay out of scope unless separately authorised by the project.
  3. Phase 6 flags: P and PA valid and informative (movement shown), `M_PASS_POS` and `M_PASS_NORM` both true on enough eligible docs, `L_SIGNAL` with `TAIL_DRIVEN` false, no assay/leakage/mode failures, complete artifacts.
  4. At least one non-teacher-forced readout (generation telemetry with a pre-registered interpretation) and a strict-mask or noncopy decomposition, so "copy" claims are supportable.
  5. A compute plan with stop conditions.

### Q12. Final verdict

- **Verdict: NARROW.**
- **Approvals (this reviewer's recommendation, not an approval of Phase 6)**
  - **v0.2 as written:** not frozen. Freeze v0.2.1 after the errata in §7 (MF-1 to MF-6), committed with a hash before any code that depends on it.
  - **Implementation (code and unit tests, no training):** approve after v0.2.1.
  - **Non-gating mechanics debug:** approve after v0.2.1, under the Q10 rules (short run or an unregistered seed).
  - **3-seed run (12 trained units):** not approved. It needs the Q10 gate and separate user approval.
  - **Maximum compute:** keep the plan's cap of 12 arm-seeds, ≤1,200 updates, ≤2 hours **wall-clock** on 6 threads, no GPU, no automatic retry, and debug runs counted inside the cap.
  - **Forbidden:** test 163, P1, T5Gemma2 (D-108 STOP), B0-B, B1, B2, Stage C, any post-result change of thresholds, seeds, donors, steps or learning rates, and any "no content use" or "copy-specific" claim.
  - **Next decision gate:** the 3-seed gate (Q10), then a separate B0-B decision under Q11.
  - **Test 163:** sealed.

---

## 3. What v0.2 gets right

- The F/L/P/PA/M separation, with M eval-only and no trained M arm, is the correct choice for the question asked.
- The full-real-K reference for M, train-only mean, and the leakage-oriented artifact list.
- Co-primary full CE (a quantity unaffected by the old alignment bug), as-run mask renamed and limited, strict mask demoted to exploratory.
- `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE` wording, `L_SIGNAL_M_CONTROL_FAIL`, documents-vs-seeds separation, seed fixed before LoRA init, and an explicit compute cap.
- Honest framing: P0 is "coarse sensitivity", and 20/20/100/3 seeds is a screening envelope.

## 4. Limits of this review

- I did not run any code or tests. The "54 tests" figure is historical; the test file I read has 7 tests.
- All numbers cited come from the repository artifacts. Where I give an estimate (old-metric per-doc spread, power at the floor, P's movement under lr 1e-4) it is labelled as unmeasured.
- I did not diff v0.2 at 918cfa5 against 8c4f197; the clone is shallow.

---

## 5. Must-fix (ranked)

Items MF-1 to MF-4 block implementation, because they define what the code must compute. MF-5 and MF-6 block the 3-seed gate.

| # | Must-fix | Done when |
|---|---|---|
| MF-1 | **Total label function.** Add the missing `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE` row, PA cells, a (P_VALID, PA_VALID) interaction table, copy-xor-full × M rows. Output an independent flag vector plus a headline. Rename `REGIME_ERASES_SELECTIVITY` to an observational name. | Every flag combination maps to one headline. A true `L_SIGNAL` is never suppressed. This is a unit test. |
| MF-2 | **P/PA gate meaning.** Freeze the learning rates. Require reporting of step-0 vs step-100 real CE, train CE trajectory and parameter movement. Choose the retention-floor-or-wording option (Q1). Define PA's step-0 reference. | The errata states which option is chosen. The artifact schema has the movement fields. |
| MF-3 | **M adequacy.** `M_CONTROL_PASS` requires both `M_POS_MEAN` and `M_NORM`. Define the `M_NORM` scale, the `M_VALID` quantifier (P and PA, pooled), a minimum eligible-doc count (`M_NOT_EVALUABLE`), same-doc comparison, and final-state persistence. | The errata text is explicit. The M tests in Q9 exist. |
| MF-4 | **Statistics contract.** Document-level bootstrap on seed-averaged per-doc Δ. "L > F" as a paired per-doc difference with a stated rule. "2/3 seeds" on seed-level means for both copy and full. State that full has no magnitude floor, or add one. Rename the document-count key. | The errata defines each rule in a form a test can check. |
| MF-5 | **Debug protocol.** Short run or an unregistered seed, a mechanics-only checklist, no label computed from debug values, and a frozen commit hash. | Stated in the errata before debug. |
| MF-6 | **Cap and artifact contract.** Wall-clock definition of the cap, per-phase timing, extrapolation before the 3-seed gate, checkpoint hash and persistence, per-doc donor/K/crop-effect fields. | The artifact schema lists them. The timings exist in the debug output. |

Should-fix (not blocking): `Δnoncopy` column, `TAIL_DRIVEN` flag, rename "copy" wording, per-doc scatter table.

---

## 6. Premises I believe are wrong or overstated

1. **"The P gate is now strengthened."** The `.05` floor is about 1% of P0 (3.76 / 5.24). The strengthening is mostly the added full CI and the post-training measurement. As written, the gate detects near-total erasure only.
2. **"PA closes the adapter-regime confound."** It closes it only if PA's regime and step-0 behaviour are characterised. F/L start near CE 27 (repair debug), P0 near 12.7/13.2, and PA's start is unmeasured and likely closer to the F/L case. There is also no label consequence for PA invalid.
3. **"M validation in P/PA makes M a valid negative control."** It shows that the intervention is detectable, not that it is fair. The norm/OOD confound remains unless `M_NORM` is part of the pass condition.
4. **"Δfull as co-primary resolves copy overclaim."** Only partly. Co-primary full is collinear with as-run copy (coverage .82/.84). Copy-specificity needs the strict mask or a noncopy contrast.
5. **"3 seeds" as replication.** Seeds vary training, not documents. n = 20 either way.
6. **"54 tests pass."** Historical. The inspected test file has 7 tests, and no P/PA/M tests exist yet.

---

## 7. Final line

```text
최종 판정: NARROW
v0.2: not frozen as written. Freeze v0.2.1 (errata MF-1..MF-6) with a commit hash before code depends on it.
구현·1-seed debug: approve after v0.2.1 (code + unit tests; mechanics-only debug, short run or unregistered seed, no labels from debug values).
3-seed: not approved. Needs the Q10 gate and separate user approval.
금지 범위: test 163 (sealed), P1, T5Gemma2 (D-108 STOP), B0-B/B1/B2/Stage C, post-result changes to thresholds/seeds/donors/steps/lr, "no content use" and "copy-specific" claims.
최대 compute: 12 arm-seeds, ≤1,200 updates, ≤2 wall-clock hours on 6 threads, no GPU, no automatic retry; debug counts inside the cap.
Must-fix (ranked): MF-1 total label function; MF-2 P/PA gate meaning + PA step-0; MF-3 M adequacy (M_NORM in pass, quantifier, eligibility, persistence); MF-4 statistics contract; MF-5 debug protocol; MF-6 cap/artifact contract.
잘못된 전제: see §6 (P gate "strengthened", PA closes confound, M validation = fair control, co-primary full resolves copy, 3 seeds = replication, 54 tests).
```