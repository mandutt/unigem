# Independent Review — C5 Phase 6 P/M Prereg v0.2.1 Errata

**Reviewer: Sonnet 5.5 (reasoning: high). Independent round; no other reviewer's answer was read or reused. No subagents or additional LLMs were called.**

- Review basis: `git fetch origin` + `git pull --ff-only origin main` succeeded ("Already up to date"). `HEAD == origin/main == 075621596fbe4e169c02f0c4c75ad65b3d42853f` (`docs: add C5 P/M v0.2.1 review request`).
- Read in full: the review request, `docs/plan_c5_b0a_pm_prereg_v0_2_1_errata.md`, `docs/plan_c5_b0a_pm_prereg_v0_2.md`, the v0.2 3-AI synthesis, the P0 report, `runner/c5_mt5_lora_b0.py`, `eval/tests/test_c5_b0_metric.py`. I also read the P0 raw artifact (`reports/provenance/C5_b0a/p0_native_sanity.json`) and two lines of `c5_mt5_layer_probe.py` / `c5_a1_lora.py` (Adapter and LoRALinear definitions).
- Not done: no training, no evaluation, no unit-test execution, no test 163, no P1, no external APIs, no repository edits other than this file. T5Gemma2 stays closed (D-108). Nothing here approves Phase 6, B0-B, B1, B2 or Stage C. I propose no threshold, seed, donor, step or LR change after any result; every amendment below is a **pre-result** change to the unfrozen v0.2.1 text.

---

## 0. Bottom line

**NARROW.** v0.2.1 is a real improvement. It adds the independent flag vector, removes the causal label name, adds the P/PA interaction table, the PA step0 run, M AND-pass, the common cohort, a statistics contract, an unregistered debug seed and a manifest list. However, the "total decision function" is **not total**, the cap is **arithmetically infeasible as written**, and the M cohort rule is **likely unreachable by construction**. All three can be settled before any code exists, and none needs a threshold change.

The five findings that most affect the verdict:

1. **`not_assessable` is a flag with no decision cell, and `INCONCLUSIVE_SMALL_N` (#13) is dead code.** After rules 1–12, every non-`l_signal` case ends at #9–#12 (copy_only, full_only, neither with M pass, neither without M pass). "Otherwise" is therefore unreachable. A missing CI makes `l_signal` false, so the function silently falls into `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`, which turns "cannot assess" into a negative-sounding label (§1.1 vs §1.2 vs §1.5).
2. **A hole exists: P valid and PA path-failed.** Rule 4 requires `pa_step100_path_ok`. Rule 2 and rule 3 do not fire when `p_valid` is true. Whether the headline lands on #6, #7, #8 or #12 then depends on how `m_valid_pa` is initialised for a PA that never produced a valid step100. That is undefined.
3. **Cap arithmetic.** 12 units × 100 updates = 1,200, which already equals the cap. §5.1 adds 4 arms × ≤5 updates of debug, and §6.1 says debug counts against both the unit and the update cap. Debug plus the registered run therefore needs ≥16 units and ≥1,220 updates. The cap cannot be satisfied.
4. **M cohort structure.** The rule "eligible train contributor ≥10 of 20, with `len(h_i) >= K_real`" makes a target doc eligible only if `K_real` ≤ roughly the 10th-longest train length, about the train median. If val lengths resemble train lengths, about half of the val docs qualify. The common L∩P∩PA cohort needs ≥15/20. This is a data-only fact that can be measured before the freeze. If it holds, `M_NOT_EVALUABLE` becomes the structural headline and the M arm tests nothing.
5. **PA is mislabelled.** The PA adapter is a random-init `Linear–GELU–Linear–LayerNorm` stack applied to native mT5 memory. At step0 that is a random re-basing of a space the frozen decoder was never trained on. PA step0 will probably be near zero or noise (`PA_RETENTION` null by the errata's own guard), so PA is an **acquisition** control, not a "retention" control. The name `ADAPTER_REGIME_LOSS` implies something was lost that never was present.

These are fixable in one short amendment (call it v0.2.1-r1) before the freeze. Decision in §Q12.

---

## 1. Q1–Q12

### Q1. Total decision function / L_SIGNAL suppression

- **Verdict: conditional (not total yet; flags do preserve L_SIGNAL).**
- **Evidence.**
  - The good part: §1.3 stores `l_copy_signal` / `l_full_signal` / `l_signal` independently and requires an explicit statement when the headline is a validity failure. The `REGIME_ERASES_SELECTIVITY` rename is correct.
  - **Dead cell.** Case analysis of §1.2 #7–#13: `l_signal` → #7 or #8. Not `l_signal` → exactly one of {copy_only, full_only, neither}. `copy_only` → #9 (the `and not full_only` guard is redundant because copy_only and full_only are mutually exclusive). `full_only` → #10. Neither plus `m_control_pass_l` → #11. Neither without it → #12. `INCONCLUSIVE_SMALL_N` (#13) has no remaining input. §1.5 says "document count too small → INCONCLUSIVE_SMALL_N", but no small-N rule is defined (no n-min), so the label has neither a trigger nor a threshold.
  - **`not_assessable` has no cell.** It is in the flag vector (§1.1), but §1.2 never tests it. §1.5 says "CI not computable → NOT_ASSESSABLE; one seed missing → NOT_ASSESSABLE; common subset <15/20 → NOT_ASSESSABLE", and no precedence entry carries that label. The flags `l_*`, `m_pass_*` and `p_valid` are written as booleans. They need a third value (true / false / not_assessable), or "not assessable" collapses to false.
  - **Path-fail inconsistency.** §1.2 #2 labels a P step100 *path* failure `P_STEP100_NOT_VALID`, whereas §1.5 and the stop conditions (v0.2 §11) treat path failure as `ASSAY_INVALID` or an immediate stop. v0.2 §6.1 said ASSAY_INVALID. The runner raises `RuntimeError` on non-finite loss (line ~707–708), so rule #2 is effectively unreachable and contradicts #1/§1.5.
  - **PA path-fail hole**: see finding 2 above (`p_valid` true, `pa_step100_path_ok` false).
  - **`MEAN_CONTRAST_ONLY` (#11) appears nowhere else**: not in v0.2 §6.4, not in the §3.6 M labels, not in the request's "13-label" description of semantics. It needs a one-line meaning ("L's real memory beats the mean memory but beats the wrong-doc memory by less than the floor").
  - **Headline still hides L_SIGNAL in six of thirteen cells (#1–#6).** The flags survive, but anyone reading only the headline loses the L information. A reader cannot tell "M_NOT_EVALUABLE with L_SIGNAL true" from "M_NOT_EVALUABLE with L flat". Given finding 4, `M_NOT_EVALUABLE` could be the commonest headline.
  - **Asymmetry in rule #6.** M_VALID (P and PA both pass M) is needed to interpret an L M-*fail* (v0.2 §6.3 says exactly that). Rule #6 precedes #7/#8, so an L M-*pass* with `l_signal` is also demoted to `M_CONTROL_NOT_VALID` when P/PA fail M. That may be a deliberately conservative choice, but it is not stated, and it hides the one cell that most resembles a positive result.
  - `tail_driven` never reaches the headline. v0.2 §12 required heavy-tail robustness for a B0-B review; v0.2.1 stores a flag only.
- **Next steps.**
  1. Replace the single headline with a **factored output** `(validity_status, signal_status)`. `validity_status` ∈ {ASSAY_INVALID, P_STEP100_NOT_VALID, PA_STEP100_NOT_VALID/ADAPTER_REGIME_LOSS, M_NOT_EVALUABLE, M_CONTROL_NOT_VALID, VALID}. `signal_status` ∈ {EXPLORATORY_L_SIGNAL, L_SIGNAL_M_CONTROL_FAIL, COPY_ONLY_WEAK, FULL_ONLY_WEAK, MEAN_CONTRAST_ONLY, NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE, NOT_ASSESSABLE, INCONCLUSIVE_SMALL_N}. Both are always emitted, so L is never hidden. The scalar headline can stay as a convenience string (`validity/signal`). This removes the precedence problem rather than patching it.
  2. Make every gated flag tri-state; define `NOT_ASSESSABLE` propagation (any required conjunct unassessable and none false → NOT_ASSESSABLE; any false → false); define one n-min and one trigger for `INCONCLUSIVE_SMALL_N`, or delete the label. Fix the P path-fail rule (fold into #1) and add the PA path-fail cell. Define `MEAN_CONTRAST_ONLY`. State explicitly whether an L M-pass with M_VALID false is a distinct reachable cell.
  3. Commit an **exhaustive truth-table test**: enumerate all tri-state combinations of the flags, assert that every combination yields exactly one output, that no flag is mutated, that every label is reachable by at least one combination, and that the labels the spec calls reachable are hit.

### Q2. P/PA contract and `ADAPTER_REGIME_LOSS`

- **Verdict: conditional.**
- **Evidence.**
  - Good: PA step0 is a separate run (§2.2); the P0 file is not reused as PA step0; movement fields are listed; retention is descriptive with a null guard; the (P,PA) cells are enumerated.
  - **What PA step0 is.** `Adapter` is `Linear(512,512) → GELU → Linear(512,512) → LayerNorm(512)` (`c5_mt5_layer_probe.py` 52–63), random-initialised by `make_adapter(seed)`. Feeding native mT5 encoder output through it re-expresses the memory in an arbitrary basis with every row normalised, which the frozen decoder's cross-attention was never trained on. Expect PA step0 Δ ≈ 0 (or noisy). Hence `PA_RETENTION = Δ100/Δ0` is probably a ratio over a near-zero denominator → `null`. PA_VALID at step100 is really "can adapter + LoRA **learn**, in 100 updates, to use a source that is known to be content-informative". That is the correct positive control for L (and arguably the main value of PA), but the document calls it "retention".
  - **Naming.** `ADAPTER_REGIME_LOSS` says "loss". Nothing was shown to exist at step0 in the PA regime. Use a neutral name such as `PA_STEP100_NOT_VALID`. §1.4's disclaimer is a mitigation, not a fix.
  - **Scale mismatch not recorded.** PA's adapter input is mT5 `last_hidden_state` (final-layer-normed); L's input is the cached EG2 layer-19 hidden states. Scale and geometry differ. PA_VALID shows the regime can learn from native memory; it does not show L's input can. The labels already say "NO_AFFIRMATIVE", which is the right strength. Say this in the artifact's interpretation block.
  - **F/T cell** (P invalid, PA valid) is informative (decoder-LoRA-only lost sensitivity while adapter + LoRA kept it) but maps to the same label as F/F. The PA flag is stored, so this is only a reporting matter.
  - **P step0 vs P0.** P step0 (native, zero LoRA, same docs/donors/K) should reproduce `p0_native_sanity.json` to numeric tolerance. The errata does not require that check; it is the cheapest end-to-end validation of the new P path.
  - **LoRA init pairing.** `train_arm` today calls `make_adapter(seed)` then `attach_decoder_lora_mt5` with no re-seed (lines 678–681). `LoRALinear.lora_A` uses `kaiming_uniform_` on the global RNG. The "reseed immediately before LoRA init" rule therefore *changes* L's LoRA init relative to the old B0-A L runs (fine, F/L are rerun), and makes `lora_A` identical across P / PA / L for a given seed. That pairing is worth asserting in a test. LoRA dropout also draws from the global RNG; with the same seed and no RNG use by the adapter, the dropout streams match across P / PA / L. Say so.
  - **Runner support.** `set_training_mode` accepts only `"frozen"`/`"lora"` and asserts `adapter.training` (lines 335–368). P has no adapter. A new mode (`p`, `pa`) is needed, and its inventory checks (64 modules, 0 trainable base params, base eval) have to be re-derived. `--mode` has no `pm-diagnostic`.
- **Next steps.**
  1. Rename `ADAPTER_REGIME_LOSS` → `PA_STEP100_NOT_VALID`; reword §2.2/§2.3 so PA is an "acquisition control (adapter + LoRA from random init on native memory)" and `PA_RETENTION` is expected to be null/uninformative. Add the scale/geometry caveat to the interpretation block.
  2. Require P step0 to reproduce P0 per-doc deltas (atol stated, e.g. 1e-4) and record the P0 artifact hash in the manifest; this is also the definition of `p0_path_ok`.
  3. Add tests: `lora_A` equality across P/PA/L at the same seed; adapter state equality PA/L; two same-seed runs give equal step-5 loss within a stated tolerance (6-thread CPU math is not guaranteed bitwise).

### Q3. P gate (`.05` + full/copy CI)

- **Verdict: conditional (still a weak gate; acceptable only as a sanity screen).**
- **Evidence.**
  - P0 val mean Δcopy 5.2375 and Δfull 5.2936; P0 train 3.7617 / 3.5027. A floor of .05 is 1.0–1.3 % of the val mean, so it detects near-total erasure only. §2.4 says so ("post-training native-path sensitivity screen") and forbids reading it as selectivity learning.
  - P0's absolute scale is dominated by wrong-memory CE. In the raw artifact, val's first doc has real full CE 14.02 against wrong full CE 31.77. Untrained real CE (12.7 / 13.2) is already above ln|V| = 12.43. The Δ is largely a mismatch penalty of an untrained decoder. 100 LoRA steps will lower real CE but need not lower the wrong-memory penalty, so Δ may stay large and `P_VALID` will very likely pass trivially. In that case `P_VALID` mainly certifies that the training path did not break; it is not evidence that "native content use" survived.
  - No per-seed requirement exists for P/PA validity. One collapsed seed can be masked by the seed average (§4.1), whereas L_SIGNAL requires 2/3 seeds.
  - The D-gate wording "P_VALID = post-training sensitivity retention" in the review request is slightly stronger than what §2.4 defines; keep §2.4's wording.
- **Next steps.**
  1. Keep `.05` unchanged. Add a **descriptive** (non-gating) field set: per-seed Δcopy/Δfull at step100, `real_full_ce_step100 < ln|V|`, and a retention tier. Retention ratios become informative only if the denominator is P0's, so for P this is meaningful and for PA it is not.
  2. State in the report template that `P_VALID` = "path/sensitivity sanity", and forbid language that treats it as support for L's content use. Pre-register that a passing P/PA does *not* make a null L result informative about EG2 memory beyond "this regime can use native memory".
  3. If a per-seed condition for P/PA is wanted (e.g. no seed with Δ ≤ 0), register it **now**, before any result; otherwise record per-seed values only.

### Q4. M contract (M_POS_MEAN AND M_NORM, M_VALID, common cohort, checkpoint)

- **Verdict: conditional.**
- **Evidence.**
  - Strengths: M_POS_MEAN alone can no longer pass (§3.4); M_GLOBAL cannot rescue a fail; the Frobenius scale is fixed (§3.5); M_NORM is honestly described as magnitude-matched rather than target-independent; mean sources are train-only; zero/non-finite norms map to `M_NOT_EVALUABLE`.
  - **Cohort reachability (finding 4).** §3.2 says a train doc contributes if `len(h_i) >= K_real` and that ≥10 contributors are needed. The condition for a val doc to be eligible is "at least 10 train docs are as long as its `K_real`", i.e. `K_real` ≲ the 10th-longest of 20 train lengths. With similar length distributions that is about half of the val docs, and the required intersection across L, P and PA is ≥15/20. Under binomial(20, .5) the chance of ≥15 is ~2 %. Length ties at a truncation cap (256 for P/PA) could raise it; the L cache's own length cap is unknown to me (the cache files are not in the checkout). This is a deterministic function of document lengths, not a result, so it can be computed **before** the freeze (from `lengths` in the cache and the tokenizer; no model forward).
  - **Cohort definition gaps.** (a) The cohort is "eligible in L/P/PA" but does not say whether copy/full-eligibility is intersected into it. (b) It does not say that `M_PASS_*` for L, P and PA are computed on the *identical* cohort; if each uses its own, the "common" cohort is only a count gate. (c) K_real differs by arm: L uses the EG2 cache length; P/PA use tokenised source length ≤256.
  - **M aggregation.** §3.4 does not say how seeds are combined for M (per seed, or seed-averaged per-doc deltas as in §4.1). The v0.2 synthesis (MF-3) asked for a pooled quantifier; v0.2.1 leaves "P(…) AND PA(…)" without a seed rule.
  - **Conjunction size.** `M_VALID` = POS and NORM for P and for PA, each requiring Δfull>0, full CI lower>0, Δcopy>0, copy CI lower>0 on ~15–20 docs: 16 CI conditions. Combined with `M_CONTROL_PASS_L` (4 more), a pass is hard by design. Fine for a conservative diagnostic, but `M_CONTROL_NOT_VALID` / `NO_AFFIRMATIVE` are then the likely outcomes, and the document should say so before results.
  - **What M_PASS shows.** The decoder is trained on rows whose per-row structure is high-variance (adapter ends in LayerNorm), and the mean memory is smooth. A real-vs-mean gap can arise from distribution shift alone. The AND with M_NORM removes the magnitude route but not the shape route. Under this design `M` is best read as "real memory is better than a smooth generic memory", a necessary condition, not evidence of content use. Say so in the labels' glosses.
  - **Leakage.** I see no target, val or donor information in the mean builder; the only target-derived inputs are `K_real` (length) and, for M_NORM, `||real_memory||_F`, both documented. Train docs in the mean are in-sample for the adapter, which is permitted. The synthetic invariance tests listed in §5.2 are the right ones.
  - **Replay.** "Final checkpoint hash (M replay)" implies M may run in a separate process. A replay-equals-in-process check is not required anywhere.
- **Next steps.**
  1. **Before the freeze**: run a data-only preflight that reports, for L (cache lengths) and for P/PA (tokenised source lengths at max 256), the K_real values, train contributor counts, and the number of eligible val docs, and the L∩P∩PA intersection. No model, no losses. If the intersection is <15 the M design is dead on arrival, and the amendment must choose an eligibility rule that is *length-feasible by design* (for example, crop all contributors and the target to a common prefix K). That is a pre-result design fix, not a threshold change.
  2. Specify in the amendment: the cohort includes copy/full eligibility; all M arms are scored on the single common cohort; M is scored on seed-averaged per-doc Δ with the same document bootstrap as §4; per-seed values are recorded.
  3. Add tests: replay-equals-in-process within a tolerance; builder invariance to val/target/donor and to non-eligible train docs; M_NORM Frobenius equals the real norm; per-row diagnostic recorded but never used in a decision.

### Q5. Statistics contract

- **Verdict: conditional (mostly executable; several parameters unspecified).**
- **Evidence.**
  - Good: the unit is the document; seed-average first, then bootstrap; L>F uses the paired per-document difference; `documents_positive` and `seeds_positive` are separate; copy/full use a common subset; heavy-tail statistics are required.
  - **Runner mismatch.** `bootstrap_paired` still returns a key called `seeds_positive` that counts positive *documents* (line 395); the errata's rename needs code and a test.
  - **Not specified.** (i) CI level and type: the code uses a 2.5/97.5 percentile CI with 1,000 resamples and a fixed RNG seed `20261108` per call; the errata only says "1,000 resamples". Pin level, method, RNG seed policy and the resample count. (ii) `L>F`: "mean > 0" with no floor and no CI. A paired difference of 1e-4 qualifies. That is a weak third conjunct next to the CI-lower>0 for Δ itself. (iii) The "2/3 seeds" rule uses the L seed means only, not L−F per seed. (iv) No P/PA seed rule (Q3). (v) M seed aggregation (Q4).
  - **Eligibility is vacuous in the current runner.** `evaluate_arm` skips any doc whose copy CE is None (line 437–438), so the full-CE set equals the copy-eligible set. The errata's "common subset / full-only / copy-only counts" can therefore never differ unless the runner changes. Either change the runner (full CE for all docs, separate copy eligibility) or state that full is computed on copy-eligible docs only and drop the copy_only/full_only distinction. For `copy_ce`, docs with <5 copy tokens drop out.
  - **Heavy-tail rule.** `tail_driven` = leave-top-3-out mean ≤0 or top-3 share >.50. The share definition is unspecified. From the P0 artifact I get, using Σtop3 / Σall: val copy .486, val full .509, train copy .422, train full .429; leave-top-3-out means: val copy 3.17, val full 3.06, train copy 2.56, train full 2.36. By this rule P0 val-full would already be `tail_driven` and P0 val-copy would not. So the flag is endpoint-dependent and sits within .02 of the cutoff on the only data seen. Define: top-3 by value, share of the positive-part sum or of the signed sum; the behaviour when the sum ≤0; whether the flag is the OR of both endpoints.
  - **Multiplicity.** `L_SIGNAL` is a conjunction over two endpoints, which is conservative against false positives. Not a defect.
  - **Per-doc eligibility with a missing seed.** A missing seed → NOT_ASSESSABLE; consistent with §1.5 once that has a cell (Q1).
- **Next steps.**
  1. Add a "statistical constants" block: CI = percentile 2.5/97.5; n_boot = 1,000; bootstrap RNG seed fixed and recorded; define top-3 share formula and endpoint combination for `tail_driven`; define n-min for `INCONCLUSIVE_SMALL_N`.
  2. Resolve the copy/full eligibility vacuity in either direction, and rename `seeds_positive` → `documents_positive` inside `bootstrap_paired` with a regression test.
  3. If L>F is to carry weight, register now that it also needs CI lower > 0 on the paired difference; if not, label it explicitly "direction check only".

### Q6. Debug protocol

- **Verdict: conditional.**
- **Evidence.**
  - The registered seeds are excluded (§5.3) and the debug seed 20261111 is not among them, which prevents the specific leak in the v0.2 MF-5. Mechanics-only checks in §5.2 are the right list.
  - **Residual exposure.** Debug evaluates real checkpoints on the registered val docs `val[5:25]`. P step0 is seed-independent and P0 is already known. Five-update F/L/P/PA deltas are near-step0 values, so a debug run would reveal registered-doc behaviour for the registered docs and donors even with a different seed. "No labels" does not stop anyone reading numeric deltas.
  - **Printing.** `main()` prints the full JSON payload for p0-sanity and train mode (lines ~279, 797). A debug mode must not print per-doc outcomes.
  - **"1 mechanics probe" of M on real data** computes real Δmemfree on registered docs. Same exposure.
  - **Seed burn.** Nothing states that 20261111 can never be used as a replacement seed after a bad registered result.
  - **Coverage.** Five updates never wrap the 20-doc cyclic order, never make `train_ce_last10` meaningful, and do not test checkpoint replay unless that is added.
- **Next steps.**
  1. Run debug on **different documents** (for example train docs 20–29 and val docs beyond 25, after checking provenance that they are neither test nor P1), or have debug write outcome fields to a sealed file that is not printed or read. Mechanics checks need none of the registered-doc numbers.
  2. Add a runner flag `--mechanics-only` that (a) refuses to compute headline/flags, (b) suppresses outcome printing, (c) writes `"debug": true, "gating": false, "registered_seed": false` into every artifact, and (d) is rejected by the aggregation script. Declare seed 20261111 permanently burned.
  3. Cover the gaps with synthetic unit tests (cyclic order wrap with a toy dataset, last-10 mean semantics, replay).

### Q7. Cap and artifacts

- **Verdict: disagree as written; agree after the arithmetic is fixed.**
- **Evidence.**
  - §6.1 lists "12 arm-seed units, ≤1,200 updates", and "debug included in wall-clock/units/updates". 12 × 100 = 1,200 exactly. Debug adds 4 arms × ≤5 updates = 20 updates and 4 more trained units. The cap is violated before the registered run starts.
  - v0.2 §9 said "≤2 CPU-hours"; v0.2.1 says "wall-clock ≤2 h from process start, 6 threads". That is a loosening of up to ~12 CPU-hours. It may be the right reading, but it is not labelled a change.
  - "From process start": registered units, debug and M replay can be different processes. No cumulative ledger exists.
  - Cost realism is unverifiable without timing. Training is 1,200 batch-1 updates on mT5-small, which looks cheap. Per unit the evaluation is 200 forward passes per arm (20 docs × 5 donors × real/wrong), PA and P also need step0 (another 200 each, three PA seeds), M is a few hundred forwards per arm, and generation is greedy up to 256 new tokens on 20 docs. `load_base` sets `config.use_cache = False`, so `model.generate` has no KV cache, which makes decoding roughly quadratic in length. I expect generation to be the largest single cost line. The errata does not say whether P/PA generate, though §6.3 requires "generation telemetry".
  - Artifacts: the manifest list (prereg hash, code hash, data/split hash, tokenizer/model hash, seeds, LRs, max lengths, checkpoint hash) is good. Missing: P0 artifact hash (needed for `p0_path_ok`), the debug acceptance record, and the cumulative ledger file.
  - Retry is "no automatic extension", which is clear.
- **Next steps.**
  1. Rewrite the cap as **two budgets**, both stated before any run: registered run ≤12 units, ≤1,200 updates, ≤2 h wall; debug ≤4 units, ≤20 updates, ≤30 min wall, in a separate ledger. Alternatively, make the single cap ≤1,220 updates and 16 units. State that CPU time is recorded but is not the cap, and disclose the change from v0.2's "2 CPU-hours".
  2. Add a cumulative ledger (`wall_start`, per-phase seconds, per-process) that is checked before each unit starts, and a **projection rule**: after debug, projected registered cost = debug phase timings × scale ≤ 0.8 × cap, otherwise do not launch the 3-seed run without a new approval. This is an execution go/no-go, not a threshold.
  3. Decide and record whether P/PA/M generate, and the generation length used for cost estimation.

### Q8. Remaining Must-fix (ranked) and new problems created by v0.2.1

| Rank | Must-fix | Why |
|---:|---|---|
| 1 | Decision function: tri-state flags, a `NOT_ASSESSABLE` output, a trigger or deletion for `INCONCLUSIVE_SMALL_N`, the PA path-fail cell, the P path-fail vs `ASSAY_INVALID` contradiction, a definition for `MEAN_CONTRAST_ONLY`, an explicit position on L M-pass with M_VALID false, and a factored `(validity, signal)` output | Q1; the headline is the artifact readers will actually use |
| 2 | Cap arithmetic and ledger (two budgets, cumulative wall-clock, CPU-hour change disclosed, generation costed, projection go/no-go) | Q7; cap cannot be met as written |
| 3 | M cohort reachability: data-only preflight before the freeze; common-cohort definition including copy/full eligibility; one common cohort for L/P/PA; M seed aggregation | Q4; risk that M is structurally `M_NOT_EVALUABLE` |
| 4 | PA semantics: acquisition control, neutral name, P step0 must reproduce P0, scale caveat | Q2; avoids reading PA failure as "adapter destroyed something" |
| 5 | Debug exposure: disjoint docs or sealed outcomes, `--mechanics-only`, burned seed, artifact flags | Q6 |
| 6 | Statistical constants and the heavy-tail definition (share formula, endpoint rule), copy/full eligibility vacuity, `seeds_positive` rename | Q5 |
| 7 | B0-B boundary restated over the new labels (v0.2 §12 still lists the deleted `REGIME_ERASES_SELECTIVITY` and omits `P_STEP100_NOT_VALID`, `ADAPTER_REGIME_LOSS`, `M_NOT_EVALUABLE`, `tail_driven`), and a **single consolidated frozen document** instead of v0.2 + errata with a "v0.2.1 wins on conflict" rule | Q11; two interleaved documents are an audit risk |
| 8 | Descriptive P/PA fields: per-seed deltas and `real_full_ce < ln|V|` flag | Q3 |

**New problems introduced by v0.2.1 (versus v0.2):** the dead/undefined headline cells; the cap infeasibility; the new `.50` top-3 cutoff, placed between the two P0 endpoints already observed (.486 / .509), so it was set with the P0 numbers in view (non-gating, so tolerable, but disclose it); a naming problem in `ADAPTER_REGIME_LOSS`; and a silent move from CPU-hours to wall-clock.

**Already closed well (credit):** `REGIME_ERASES_SELECTIVITY` removed; L flags independent of headline; PA step0 is a separate run; M_POS_MEAN AND M_NORM; whole-matrix Frobenius scale; documents vs seeds naming; seed-avg-then-bootstrap; unregistered debug seed; manifests and checkpoint hash.

### Q9. Approve implementation + unit tests?

- **Verdict: conditional.** Approve once the amendment in §3 closes ranks 1–4 (and 5–7 where they are text-only). Implementation of code that does not depend on the amended items could start earlier, but I would not split approval; writing the decision function against the current text would build the dead cells into the code.
- **Evidence.** The current test file has eight tests and none for P/PA training, M, statistics, the label function, caps or artifacts; the P0 decision test is descriptive only. The runner has no `pm-diagnostic` mode, no P/PA training mode, no M builder, no flag/label function, no checkpoint saving.
- **Required contracts/tests before implementation is called done:**
  1. Exhaustive tri-state truth-table and reachability tests for the decision function; flags are never mutated by labelling.
  2. P/PA: 64 modules, 0 trainable base params, base eval, adapter present only in PA; `lora_A` equal across P/PA/L; same-seed reproducibility within a stated tolerance; P step0 equals the P0 artifact within tolerance; cyclic order `train_ids[step % 20]`; grad clip 1.0; LR groups.
  3. M: leakage/invariance tests, eligible count, cohort intersection with copy/full eligibility, Frobenius scale, zero-norm → `M_NOT_EVALUABLE`, replay equals in-process.
  4. Statistics: seed-average-then-bootstrap, paired L−F, `documents_positive` vs `seeds_positive`, tail statistics including negatives, deterministic bootstrap, missing seed → NOT_ASSESSABLE.
  5. Artifact schema, manifest hashes, `test_split_used: false`, debug flags, ledger and cap enforcement.
- **Next steps.** (1) Issue the amendment (§3). (2) Freeze the consolidated document with its commit hash. (3) Implement against it; run the unit tests only (no training or evaluation).

### Q10. Unregistered-seed mechanics debug

- **Verdict: conditional.** Approve **after** implementation and unit tests pass at a recorded commit, and only with the Q6 changes.
- **Evidence.** §5 is the right shape; residual issues are the exposure on registered docs, stdout printing, the M probe and the missing artifacts (Q6, Q7).
- **Artifacts needed so debug is not mistaken for a 3-seed gate:**
  - separate output directory (for example `reports/provenance/C5_b0a/pm_debug/`) and a `debug_acceptance.json` listing each mechanics check as pass/fail with **no** CE or Δ values;
  - every debug artifact carries `debug: true`, `gating: false`, `registered_seed: false`, code and prereg commit hashes, the debug seed, and no headline, flags or label fields; the runner refuses to write them;
  - an aggregation step that rejects artifacts with those flags;
  - per-phase timings feeding the projection rule (Q7).
- **Next steps.** (1) Implement `--mechanics-only` and the debug acceptance file. (2) Run debug only after step 1, on non-registered docs. (3) Record the acceptance file hash in the approval note; the 3-seed run requires a separate explicit approval.

### Q11. 3-seed run and B0-B boundary

- **Verdict: agree that the separation is intended; conditional that it holds in the text.**
- **Conditions for a 3-seed run (all required, none sufficient):** (a) consolidated prereg frozen with its hash; (b) unit tests pass at that code commit; (c) mechanics debug acceptance file all-pass; (d) data-only M preflight shows an evaluable cohort, or the amended eligibility rule does; (e) timing projection ≤ 0.8 × cap; (f) manifest complete; (g) explicit user approval; (h) no test 163 or P1 access.
- **Conditions even to *propose* B0-B:** `validity_status = VALID` and `signal_status = EXPLORATORY_L_SIGNAL`, `tail_driven` false on both endpoints, no leakage/mode/metric failures, complete artifacts. These are necessary only. A B0-B proposal would be a new prereg with its own design and review, because 20 val docs are not confirmatory. Neither this round nor a clean Phase 6 result authorises B0-B, B1, B2 or Stage C. Test 163 stays sealed and any change to that status needs a separate decision. Nothing in my reading suggests using P1 or test 163 for Phase 6.
- **Evidence.** v0.2 §12 still names the removed `REGIME_ERASES_SELECTIVITY` and does not name the new labels, so the "forbidden" list is stale relative to v0.2.1. v0.2.1 §8 says the 3-seed run is a separate gate, which is correct.
- **Next steps.** (1) Restate the B0-B boundary over the new label set in the consolidated document. (2) Add "good Phase 6 result ≠ approval" as a literal sentence in the report template. (3) Add the 3-seed launch checklist (a)–(h) as an artifact.

### Q12. Final verdict

- **Verdict: NARROW.** Scope below.
- **v0.2.1 freeze:** **not yet.** Freeze a *consolidated v0.2.1-r1* after the amendment in §3 closes ranks 1–7. It is a text-only change; no threshold, seed, donor, step or LR changes, and no new experiment.
- **Implementation + unit tests:** approve **conditionally**, after the freeze commit. A second full review round is not needed if the diff is limited to the listed items; an optional quick confirmation by one reviewer would suffice.
- **Mechanics debug:** approve conditionally after unit tests pass, on non-registered documents, mechanics-only, with the acceptance artifact (Q6, Q10). Debug budget: ≤4 units, ≤20 updates, ≤30 minutes wall, stated separately from the registered cap.
- **3-seed run:** **not approved.** Separate gate (Q11).
- **Forbidden:** training or evaluating on registered seeds 20261108/09/10 before the 3-seed gate; using seed 20261111 after debug; reading debug deltas as results; test 163; P1; T5Gemma2; Phase 6 launch, B0-B, B1, B2, Stage C; any post-result change to thresholds, seeds, donors, steps or LRs; automatic extension or retry of the cap.
- **Maximum compute:** unchanged in substance for the registered run (12 units, ≤1,200 updates, ≤2 h wall, 6 threads, no GPU). Debug is budgeted separately as above, or the single cap is restated as 16 units / ≤1,220 updates. No other compute is approved by this review.
- **Test 163:** sealed. This review neither requests nor needs it.

---

## 2. Wrong or fragile premises in the document

1. "Total decision function" — only on paper (Q1).
2. "≤1,200 updates including debug" with 12×100 updates (Q7).
3. "PA step0 random-adapter baseline gives retention" — it more likely gives a near-zero denominator; PA is an acquisition control (Q2).
4. "Eligible contributors ≥10 → cohort ≥15/20 is reachable" — not shown, and likely false for length reasons (Q4).
5. "Debug on a different seed hides registered-seed results" — it hides the seed, not the documents (Q6).
6. "copy/full common subset" — the runner currently makes the two sets identical (Q5).
7. "P_VALID retains sensitivity" — with a .05 floor against a 4–5 scale and an untrained decoder above uniform CE, it is close to a path check (Q3).

## 3. Proposed amendment list (v0.2.1-r1, text-only)

1. Factored `(validity_status, signal_status)` output; tri-state flags; `NOT_ASSESSABLE` cell; `INCONCLUSIVE_SMALL_N` n-min or deletion; PA path-fail cell; fold P path failure into `ASSAY_INVALID`; define `MEAN_CONTRAST_ONLY`; explicit rule for L M-pass with M_VALID false.
2. Two-budget cap with cumulative ledger; disclose the CPU-hour → wall-clock reading; cost generation; projection go/no-go rule.
3. Data-only M preflight before the freeze; common-cohort definition (copy/full eligibility included, single cohort for L/P/PA, M seed aggregation); an eligibility rule that is length-feasible if the preflight fails.
4. PA wording (acquisition control; neutral name); P step0 must reproduce P0 within tolerance; P0 hash in the manifest; scale caveat.
5. Debug: non-registered docs or sealed outcomes; `--mechanics-only`; burned seed; artifact flags; acceptance file.
6. Statistical constants block (CI, resamples, RNG), top-3 share formula and endpoint rule, copy/full eligibility handling, `seeds_positive` → `documents_positive`.
7. Restate the B0-B boundary over the new labels; consolidate v0.2 + v0.2.1 into one document.
8. Descriptive-only additions: per-seed P/PA deltas and `real_full_ce < ln|V|` flag.

## 4. Compact table

| Q | Verdict | Key point |
|---|---|---|
| Q1 | conditional | Flags keep L_SIGNAL, but #13 is dead, `not_assessable` has no cell, PA path-fail hole |
| Q2 | conditional | PA is an acquisition control; rename; P step0 must match P0 |
| Q3 | conditional | `.05` ≈ 1 % of P0; sanity screen only |
| Q4 | conditional | Cohort ≥15/20 probably unreachable by length; preflight; one common cohort |
| Q5 | conditional | Constants missing; copy/full eligibility vacuous in runner; `seeds_positive` rename |
| Q6 | conditional | Registered docs still exposed; use other docs / sealed outcomes |
| Q7 | disagree as written | 12×100 + debug > 1,200; two budgets and ledger |
| Q8 | — | Ranked list in §Q8 |
| Q9 | conditional | After amendment; tests listed |
| Q10 | conditional | After unit tests; non-registered docs; acceptance artifact |
| Q11 | conditional | Boundary holds only if restated over new labels |
| Q12 | **NARROW** | Freeze v0.2.1-r1 first; no 3-seed, no B0-B |

**Final: NARROW.**