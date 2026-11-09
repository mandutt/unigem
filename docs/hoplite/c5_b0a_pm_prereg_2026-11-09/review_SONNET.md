I am the Sonnet 5.5 (reasoning: high) independent external reviewer for the unigem C5 B0-A Phase 6 P/M preregistration review round.

# Independent review: C5 B0-A Phase 6 P/M bounded diagnostic (prereg v0.1)

- Review basis: origin/main HEAD `26e334a79148e8be73e3378b6c82846891f1e180` (`docs: add C5 P/M prereg external review request`). `git fetch origin` and `git pull --ff-only origin main` both succeeded ("Already up to date").
- Read in full: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v0_1.md`, `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md`, `reports/C5_B0A_REPAIR_2026-11-09.md`, `runner/c5_mt5_lora_b0.py` (all 802 lines), `eval/tests/test_c5_b0_metric.py`.
- Also read, as supporting evidence only: `reports/provenance/C5_b0a/{p0_native_sanity.json, aggregate.json, s20261108_{frozen,lora}.json}`, plus `Adapter`/`make_labels`/`load_layer_cache` in `runner/c5_mt5_layer_probe.py` and `LoRALinear` in `runner/c5_a1_lora.py`. I did not read `reports/C5_B0A_3AI_REVIEW_SYNTHESIS_2026-11-09.md` and did not consult the other models' reviews for this round.
- Constraints respected:
  - No training or evaluation was run.
  - Test 163 was not opened. I grepped the runner: it never reads `split["test"]`.
  - No P1 data or external API was used.
  - No subagents or other LLMs were used.
  - No repository file was modified. This file is my only write.
- My own checks were limited to `jq` reads of the existing P0/B0-A JSONs and arithmetic. A heredoc python call was blocked by the workspace policy, so I used `jq` and by-hand arithmetic.
- Not verified by me, and flagged where it matters: the wall-clock cost of a trained unit (no timing is logged in the P0 artifacts), and the T5 cross-attention permutation invariance. I rely on my knowledge of the HF T5 architecture there and recommend a unit test.

---

## 0. Executive summary

**Verdict: NARROW.** Implementation and a non-gating mechanics debug may proceed only after the prereg is amended to v0.2 with the Must-fix items below. The 3-seed run is not approved by this review. Neither Phase 6 nor B0-B is approved here.

The design instinct is right. Separating a positive control (P), a content-free negative control (M) and the F/L arms is the correct structure. The repair work is solid. I confirmed in the runner that `token_losses` is now same-position and that `set_training_mode` gives F/L parity. But the prereg as written has five problems that would make its labels hard to interpret.

1. **P_POSITIVE is close to a vacuous gate, and P sits in a different training regime from F/L.**
   - P0 (no training) already gives val Δcopy +5.24 and train +3.76. The gate only asks for Δ > 0 with CI lower > 0, so almost any P that does not destroy the encoder→decoder path passes.
   - P0's untrained CE is 12.7 (train) and 13.2 (val). `ln|V|` is `ln 250112 = 12.43`, so the untrained model is not even better than a uniform guess on those tokens. The P0 Δ therefore measures "wrong memory is catastrophically wrong", not graded content use.
   - The trained F/L arms live at CE ≈ 6.5–7.7. B0-A: F train last-10 CE 6.26 and val real_ce_full 6.5–7.2; L val real_ce_copy 7.7. B0-A also shows that at that CE real ≈ wrong (L +0.034, F −0.003).
   - P has no adapter and trains only LoRA at lr 1e-4 (B initialised at zero, 100 updates). I predict, without having measured it, that P stays far above CE 7 and keeps most of the P0 Δ.
   - A pass in that regime does not show the assay can detect an effect at F/L's operating point. In F/L the adapter output can act as a soft prompt and absorb the marginal LM.
2. **The adapter bypass in P removes the component under test.** P cannot separate "EG2 layer19 memory carries no usable content" from "20 docs / 100 updates / adapter-as-soft-prompt washes out selectivity regardless of memory source". An adapter + LoRA arm on native memory (PA, below) can.
3. **M is a valuable control, but the definition has avoidable defects.**
   - The "real" reference for M is not pinned.
   - The mean memory is likely out of distribution in norm.
   - The `len ≥ K` / eligible ≥ 10 rule creates survivorship and document-exclusion bias.
   - "Position-wise" is probably meaningless for a T5 decoder, because cross-attention has no position bias.
   - M is never validated on a memory where content use is known to exist (P).
4. **The label table over-claims and is incomplete.**
   - `NO_CONTENT_USE_EVIDENCE` reads as absence of evidence turned into evidence of absence, at n = 20.
   - The cell "L_SIGNAL true + M fail" is not covered by any rule.
   - "`L > F`" and "2/3 seeds > 0" are under-specified, and the code has a mislabeled field (`seeds_positive` counts documents).
5. **"Copy" language is not supported.** The as-run copy mask covers 82–84% of target tokens, and P0 Δcopy ≈ Δfull (3.76 vs 3.50, 5.24 vs 5.29). This is effectively a full-target-CE selectivity metric. The strict mask (`piece_len ≥ 2`, coverage 0.22–0.24) is the only mask with copy-specific content, and it is reported only as secondary.

None of these needs a threshold change after results. All are fixable in a v0.2 prereg amendment committed before any Phase 6 run. The P0 results are known, but no trained P, PA or M number has been seen, so pre-run amendments are legitimate. Freeze v0.2 with its commit hash before the debug run.

---

## 1. Facts I verified (read-only)

| item | evidence |
|---|---|
| CE alignment fixed | `token_losses` (runner L107–126) uses `logits` vs `labels` at the same positions. `shifted_copy_mask` is unshifted (L302–308). Unit test `test_same_position_ce_matches_builtin_loss` exists. |
| F/L mode parity | `set_training_mode` (L329–381) puts base in eval, trains adapter and LoRA branches, and asserts `trainable_base_parameters == 0` and 64 modules. |
| `set_training_mode` cannot take P | It raises `ValueError` for any arm outside `{"frozen","lora"}` (L335–336). `train_arm` also raises for any other arm (L689–690) and `--arm` choices are `frozen/lora/both` (L756). The P/PA/M code path does not exist yet. That is expected for a draft, but it is not a "DoD D1 done" item. |
| No adapter seeding in P | `train_arm` seeds torch only through `make_adapter(seed)` (L82–84, L678). P has no adapter. LoRA A init (`kaiming_uniform_`) draws from the torch RNG, so P needs an explicit `torch.manual_seed(seed)` before `attach_decoder_lora_mt5`, or the 3 seeds will not be reproducible or will be identical. |
| Seeds only vary init | Training data order is fixed: `train_ids[step % len(train_ids)]` (L700). 100 updates over 20 docs is 5 deterministic epochs, batch size 1. The 3 "seeds" vary adapter and LoRA init only. They are not independent replicates over documents, so the pooled CI is a document-level CI conditional on a fixed order. |
| `bootstrap_paired` mislabel | The key `seeds_positive` is `int((arr > 0).sum())`, a count of positive documents (L395). It is not a per-seed count. `L_SIGNAL`'s "2/3 seeds > 0" needs separate per-seed means. Nothing in the runner computes that today. |
| Adapter is position-wise | `Adapter` = Linear → GELU → Linear → LayerNorm per token (`c5_mt5_layer_probe.py` L52–63). Applying it to `h[:k]` equals cropping `A(h)`. |
| Eval "real" in F/L | `evaluate_arm` uses `h_real[:k]`, with `k = min(len_real, len_donor)`, averaged over 5 donors (L423–436). The real memory is truncated to the donor length whenever the donor is shorter. M's real reference is not defined as this or as full length (see Q3). |
| P0 numbers | train Δcopy +3.7617, CI [1.8917, 5.6050]; val +5.2375, CI [2.5013, 8.0753]. Val real_ce_copy 13.2352, wrong_ce_copy 18.4727. `jq` on the val per-doc values: Δcopy ranges −5.8 … +19.1. The three largest (19.1, 17.6, 14.2) sum to about 50.9 of the total of about 104.8, so about 49% of the mean comes from 3 of 20 documents. Per-doc real_ce_copy ranges 5.5 … 20.9. The effect is heavy-tailed, driven by catastrophic wrong-memory cases. |
| Vocabulary | `ln(250112) = 12.43`. P0 real CE (12.7 / 13.2) is above uniform. |
| B0-A trained regime | `s20261108_frozen.json`: train CE step 0 = 27.44 → last-10 mean 6.26. `s20261108_lora.json`: 37.43 → 7.29. Val Δ for L +0.034 with CI [−0.009, +0.080]. Real ≈ wrong at CE ≈ 7–8, which indicates the memory channel is mostly being used as a marginal / soft prompt. |
| Copy mask | `copyable_mask` strips spaces and accepts any single piece (alphanumeric/Hangul) that is a substring of the NFKC-normalised passage. Coverage 0.8351 / 0.8246. Strict `piece_len ≥ 2` coverage 0.2161 / 0.2427. |
| Test 163 | No code path loads `split["test"]`, and every result payload carries `test_split_used: false`. |
| Tests | I did not re-run the 54 tests (no execution). The test file contains 7 test methods for metric alignment, mode parity and P0 donors/decision. There are no tests for any P or M path. |

---

## 2. Answers Q1–Q12

### Q1. Validity of P (native mT5 encoder + decoder LoRA, adapter bypass)

- **Verdict: conditional.**
- **Evidence.**
  - P is a legitimate positive control for the metric and for the decoder-LoRA training pipeline. The corrected metric separates native real from shuffled memory strongly in P0 (+3.76 / +5.24).
  - It is a weak control as specified, for three reasons.
    1. Starting from Δ ≈ +5, `P_POSITIVE = Δ > 0 ∧ CI_lo > 0` is nearly guaranteed. LoRA B is zero-initialised, lr is 1e-4, and there are only 100 updates, so P ≈ P0 unless training actively destroys selectivity. The gate cannot fail for reasons related to the assay.
    2. P0's Δ is a miscalibration artefact. Real CE is 12.7–13.2 (above `ln|V|` = 12.43), wrong CE is 16.5–18.5, and about 49% of the val mean comes from 3 documents. That is sensitivity to catastrophic wrong-source memory, not graded content use.
    3. Regime mismatch. P (LoRA only, lr 1e-4) will probably stay at CE ≫ 7 after 100 updates. F/L reach CE ≈ 6.5–7.7 mostly through the adapter (lr 1e-3), and there real ≈ wrong. This is my prediction, to be checked from the training logs, not a measured fact. A P pass at CE ≈ 10 says nothing about whether the assay would detect content selectivity at CE ≈ 7.
  - Adapter inclusion matters. The adapter is the component under test in F/L and the main path by which CE falls to ≈ 7. Without it, P cannot attribute an L null to EG2 memory. Matched capacity requires an adapter.
- **Next steps.**
  1. Keep P (cheap), but amend `P_POSITIVE` to `mean Δshuffled_copy ≥ .05 ∧ CI_lo > 0`, i.e. the same magnitude floor that L must clear. A positive control that is not required to detect an effect of the size required of the treatment cannot validate the assay. This is a pre-run amendment of a draft, not a post-hoc threshold change.
  2. Add arm **PA** = native mT5 encoder memory + the same 526,336-parameter adapter (same init and lr as F/L) + the same 64 decoder LoRA modules. It is "L with the memory source swapped". Report train CE trajectory and Δ for every arm. 3 more trained units (12 total).
  3. Evaluate every arm at step 0 as well as step 100 (same docs and donors) and report Δ(step 100) − Δ(step 0). This shows whether training creates, preserves or erases selectivity. Without it, P ≈ P0 cannot be told apart from "LoRA learned something".

### Q2. Validity of M as eval-only mean-memory replacement on the L checkpoint

- **Verdict: conditional (valid for the stated question; trained M is not required in Phase 6).**
- **Evidence.**
  - The question is "does the trained L decoder depend on doc-specific memory?". A swap test on the same checkpoint holds weights fixed and changes only memory. That is the cleanest answer, and it avoids a different-treatment confound (§4.1 of the request).
  - Eval-only M also corrects a real limitation of Δshuffled. Δshuffled conflates "real helps" with "wrong hurts". P0 shows wrong memory raising CE by 3–5 nats. A content-free mean memory separates the two, and in expectation Δmemfree ≤ Δshuffled. M is therefore the stricter test, and a useful one.
  - Two limits of eval-only M.
    1. It measures dependence, not benefit. A decoder can depend on memory without being better off than a decoder trained with no memory. That question needs a trained LoRA + constant-memory baseline arm. It is not needed for Phase 6, but it should be listed as a precondition for any B0-B-style claim of "benefit from memory".
    2. M has no positive validation. If M on L returns "real ≈ mean", this cannot be read as "L ignores content" unless the same probe returns Δmemfree > 0 on a memory where content use is certain.
- **Next steps.**
  1. Make the M probe mandatory for P and PA (and F), not "optional". M on P is the positive control for the M assay. If the M probe on P (or PA) fails `M_CONTROL_PASS`, M on L is uninterpretable. Add the label `M_UNVALIDATED`.
  2. Keep trained M out of Phase 6. Record "trained LoRA+constant-memory arm" as a precondition in the B0-B gate (Q11).
  3. Pin the L-side comparator: M's real reference is L with full-length real memory, evaluated in the same pass (see Q3).

### Q3. Mean-memory definition: leakage, validity, better definitions

- **Verdict: conditional.**
- **Evidence.**
  - Leakage: the definition is leakage-free as written. The mean uses only train-20 memories passed through the trained adapter. It never touches val documents, val summaries, donors or labels. The copy mask depends on the target summary, but it is applied identically to real and mean. I found no leakage path. It still needs executable tests (Q10 MF2).
  - Defects that affect interpretation:
    1. **Real reference undefined.** Δshuffled's real memory is `h[:k]` with `k = min(K_real, K_donor)`, averaged over donors. `Δmemfree = mean_ce − real_ce` is a different, full-length real condition (K = K_real). The prereg must say that M's `real_ce_copy` is the full-length real memory, computed in the same eval pass, and not reuse the Δshuffled real value. Otherwise the two Δs are not comparable.
    2. **Norm shrinkage / OOD.** Each adapter output is a LayerNorm vector (norm ≈ √512·γ). Averaging 10–20 weakly correlated vectors shrinks the norm, so the mean memory is out of distribution in scale and low-variance. Because T5 cross-attention takes the memory directly into K/V, this changes both attention sharpness and value magnitude. Part of any "real beats mean" effect can then be an OOD-scale effect rather than a content effect. The Phase 6 prereg records no norms.
    3. **Position-wise is probably moot.** In HF T5, only the first self-attention layer carries a relative position bias. Cross-attention has none. So the decoder treats memory as an unordered set (permuting memory rows leaves logits unchanged, up to numerical noise). Averaging "position j across documents" then gives K nearly identical vectors (each ≈ global mean + noise/√20), apart from sink-like first-token structure if layer19 has it. Consequences: (a) the length-K tiling adds almost nothing, (b) the `len ≥ K` requirement is an artefact of the position-wise construction with no decoder-side justification, (c) a single global mean token tiled K times behaves almost the same. I rely on architecture knowledge here and recommend a unit test.
    4. **Survivorship and exclusion.** `len(h_i) ≥ K` means that at large K the mean uses only long documents, so the composition changes with position. "Eligible < 10 → doc excluded" drops exactly the longest val documents from M, so the M document set differs from the Δshuffled set. Without a same-document-set report, M and Δshuffled are not comparable. EG2 length distribution is not in the request; I could not check how many val docs this would exclude.
    5. **Mean of memorised documents.** The adapter has seen the train-20 five times. The mean over them is not leakage, but it is a mean of adapter outputs on documents the adapter was fit to, which is a further difference from val memory.
- **Better definition (pre-registered, eval-only, cheap).**
  - **Primary M (keep as written, with fixes):** position-wise mean as preregistered. Pin the real reference. Record the per-position eligible count and the mean memory norm against the mean real norm.
  - **M-norm (secondary):** the same mean, rescaled per position to the average real per-token norm of train memory. This removes the OOD-scale explanation.
  - **M-global (secondary):** one global mean token (mean of all train adapter tokens), tiled K times. No `len ≥ K` rule, no exclusion, no document dropped. If it agrees with the primary M, the position-wise machinery is confirmed redundant.
  - The gate is computed on the primary M only. Secondaries are descriptive, and must be declared as such before the run.
- **Next steps.**
  1. Pin in v0.2: M's real reference = full-length real memory, same pass; mean computed with adapter in eval mode, `no_grad`; the P-arm mean uses the same crop convention as P's real/wrong memory (see Q10 MF1). Report n_eligible per doc and the document set for M and for Δshuffled; require the Δshuffled and M results to also be reported on the intersection set.
  2. Add M-norm and M-global as descriptive variants. Report mean-memory norm vs real-memory norm.
  3. Add a unit test: permuting memory rows leaves T5 decoder logits unchanged (|Δ| < 1e-4). If the test passes, document that "position-wise" is a stylistic choice and allow M-global as the fallback when eligibility fails. If it fails, the position-wise definition needs a separate justification.

### Q4. How to interpret F/L/P together (L > F and P)

- **Verdict: conditional.**
- **Evidence.**
  - Memory source and trainable parameters differ across arms. Per-arm absolute CE is not comparable (the prereg §11 already says so).
  - The only valid within-arm quantities are the selectivity deltas (Δshuffled, Δmemfree, each with its own step-0 reference). The only valid cross-arm quantity is the paired per-document difference of such deltas between arms that share a memory source: L − F (both EG2) and PA − P (both native).
  - P and L answer different questions: P (native, no adapter) is a pipeline/assay check, and L is the bridge arm. P positive does not transfer to L. Without PA, "P pass + L null" admits two readings: (a) the EG2 layer19 memory lacks adapter-accessible content, and (b) the 20-doc / 100-update / adapter regime erases selectivity for any memory.
  - `L > F` is not defined in v0.1. It could mean "mean(Δ_L) > mean(Δ_F)" or "paired difference CI lower > 0". At B0-A scale (L−F SD ≈ 0.16, SE ≈ 0.036), the mean-only reading is nearly uninformative.
- **Next steps.**
  1. Define `L > F` as the document-level paired difference `Δ_L(doc) − Δ_F(doc)` (seed-averaged first), with bootstrap CI lower > 0. State it before the run.
  2. Interpret the arms only through this table: within-arm Δ and Δ-change from step 0; L − F paired (EG2 memory + LoRA effect over adapter only); PA − L (memory-source effect, same machinery). P and PA are never compared with F/L by absolute CE.
  3. Forbid any statement of the form "bridge works/does not work" from a single arm. State that P passing never implies L can pass, and that P failing never implies L fails.

### Q5. Is 20/20/100/3 sufficient for a Phase 6 diagnostic?

- **Verdict: conditional (sufficient for a screening diagnostic with restricted conclusions; not sufficient for any null or generalisation claim).**
- **Evidence.**
  - The B0-A sample gives per-doc Δ SD ≈ 0.10–0.11 for F and L. A doc-level bootstrap CI at n = 20 therefore has half-width ≈ 0.045–0.05. The detectable effect is roughly ≥ 0.05 with about 50% power, not an adequate power level. Per-doc Δ from P0 is heavy-tailed (top 3 of 20 documents ≈ 49% of the sum). A 20-document percentile bootstrap on heavy tails is anti-conservative, and a single outlier flips the CI.
  - The three seeds only vary init (fixed data order), and B0-A seed SD (0.022–0.037) is comparable to the document-level SE. A document-only bootstrap therefore understates total uncertainty.
  - The compute cap (2 CPU-hours, 9 units) is plausibly generous for mT5-small, but I could not verify per-unit time. The P0 log has no timing.
- **Forbidden conclusions** (put these in v0.2 §11):
  - Any "no effect" or "bridge fails/works" statement from a non-significant L.
  - Any copy-specific claim (see Q7 and §5 "Wrong premises").
  - Any claim about generalisation beyond these 20 val documents.
  - Any claim that the 3 seeds estimate optimiser variance.
  - Any cross-arm absolute-CE comparison.
  - Any use of Δshuffled alone as "content use".
- **Next steps.**
  1. Keep 20/20/100/3. Do not change them after results. Add descriptive (non-gating) reporting: per-seed means, median Δ, number of docs with Δ > 0, top-3 contribution share, and a two-way (documents × seeds) bootstrap CI.
  2. Add a leave-top-3-out descriptive Δ for P and PA, so that outlier-driven positives are visible.
  3. Debug-run timing is mandatory. Extrapolate the 12 units from it, and stop before the 3-seed gate if the projection exceeds 2 CPU-hours.

### Q6. The `.05` threshold

- **Verdict: conditional.**
- **Evidence.**
  - Keeping `.05` for L is correct. It is the B0-A preregistered threshold. Changing it would be a post-hoc change.
  - Applying a lower bar to P (Δ > 0) than to L (Δ ≥ .05) is inverted. A positive control must be able to detect at least the effect size that the treatment is required to show.
  - M uses Δ > 0 as a pure separation test. That is coherent as a control, because M gates L's interpretation, not an effect-size claim. The size of Δmemfree depends on the shrinkage choice (Q3), and a .05 floor would be arbitrary.
- **Next steps.**
  1. Amend P/PA to `mean Δ ≥ .05 ∧ CI_lo > 0` before any run. Keep L at `.05`. Leave M at `> 0 ∧ CI_lo > 0`, and state in the prereg why: M is a separation test, and its size depends on the construction.
  2. Interpret without changing thresholds: report every Δ in units of the preregistered `.05`. State explicitly that Δ ∈ (0, .05) is "present but below the preregistered effect size", and that it never triggers L_SIGNAL.
  3. Any change in thresholds after the first Phase 6 result needs a new preregistration.

### Q7. Is `M_CONTROL_PASS` sufficient evidence of content use? Position / length / frequency shortcuts

- **Verdict: disagree that it is sufficient; agree that it is necessary.**
- **Evidence.**
  - Real memory beats the mean for any doc-specific signal: topic, domain, length, register, named-entity inventory. These can lower CE without the decoder using "content" in the copy or alignment sense. The mean memory also carries population-level information about the news domain, so "doc-specific" has to be the stated claim (prereg §11 already hedges).
  - Length is matched by construction for M (K = K_real). That removes the length shortcut for M, but not for Δshuffled, where `k = min(K_real, K_donor)` crops real memory and where length-nearest donors only partially match length.
  - Position is moot for T5 cross-attention (Q3), which removes the position shortcut. It should be verified by a test and not assumed.
  - Token frequency: with an as-run copy mask covering ≈ 83% of tokens, a decoder that uses a doc-level frequency prior would show Δcopy ≈ Δfull, which is exactly the P0 pattern. The metric cannot tell copy from topical prior.
- **Additional controls (descriptive, pre-registered, eval-only, cheap).**
  1. **Strict-mask Δ** (`piece_len ≥ 2`, coverage ≈ 0.22–0.24) for Δshuffled and Δmemfree, with the same CI. Already planned as secondary. Add the complement ("non-copy") Δ so that a copy-specific effect would show as Δ_strict > Δ_non-strict.
  2. **Within-document row permutation** of real memory: a unit-test identity check (Q3), and a runtime sanity probe on a few docs.
  3. **Donor-length stratification**: report Δshuffled separately for donors with `|K_real − K_donor|` in the lowest and highest tercile, to expose a length-mismatch component.
- **Next steps.**
  1. Define the claim `M_CONTROL_PASS` supports: "real L memory is distinguishable from a content-free mean on this doc set". Do not call it "content use".
  2. Report strict-mask and non-copy Δ for every arm and for M. Use them for interpretation, not for gating.
  3. Add the P/PA M-probe validity requirement (Q2).

### Q8. P failure → ASSAY_INVALID; minimal diagnostics after a P failure

- **Verdict: conditional (agree not to generalise to bridge STOP; the label name is misleading).**
- **Evidence.**
  - P0 already passed untrained. So a P failure after training says "the training regime erased selectivity that the untrained path had", and the label ASSAY_INVALID is wrong in that case. The metric did work in P0. It would be more accurate as `REGIME_ERASES_SELECTIVITY`.
  - Conversely, a P *pass* is weak (Q1). Both outcomes need step-0 reference values to be interpretable.
  - If P (or PA) fails, then B0-A's null for L was plausibly produced by the same regime, so it carries no information about EG2 layer19. That supports "regime redesign", not "bridge STOP".
- **Next steps.**
  1. Rename: P fail → `P_NOT_SENSITIVE_AFTER_TRAINING`, with the explicit text "regime (20 docs / 100 updates) erased or never had selectivity; no statement about EG2 or the bridge".
  2. Minimal diagnostics after a P failure, all from artifacts already produced (no extra run): per-step train CE trajectory; Δ at step 0 vs step 100 (is it decayed or never present); real vs wrong absolute CE (is the model at marginal-LM level); strict-mask Δ; generation telemetry (cap_hit, EOS, rep4).
  3. Any follow-up (different lr, more steps, more docs) is a new preregistration. No automatic retry.

### Q9. P pass + M fail → `NO_CONTENT_USE_EVIDENCE`

- **Verdict: conditional (the logic is valid; the label is too strong and the cell structure is incomplete).**
- **Evidence.**
  - A decoder that uses the mean memory about as well as real memory shows no doc-specific dependence on this doc set. It can still use population-level content (domain, style, vocabulary) carried by the mean. So "L's decoder uses mean memory" does not mean "no content use". It means "no *doc-specific* content use detected".
  - With n = 20, `M_CONTROL_FAIL` is "not separated", which is not evidence of absence. B0-A suggests the true effect at this regime may be near zero, but the CI half-width is ≈ 0.05.
  - The table has an uncovered cell: P pass + M fail + L_SIGNAL true. That is the "wrong memory hurts but real ≈ mean" pattern. It is likely under this regime and needs its own label (e.g. `DONOR_PENALTY_ONLY`), not a collapse into NO_CONTENT_USE_EVIDENCE.
  - The label should also be conditioned on M validity (Q2): if the P/PA M-probe also fails, M cannot discriminate and the correct label is `M_UNVALIDATED`.
- **Next steps.**
  1. Rename to `NO_DOC_SPECIFIC_USE_DETECTED`, and state in the label definition that it is absence of detection at n = 20.
  2. Provide a full label table: {P, PA} × {M-probe on P/PA valid?} × {M on L} × {L_SIGNAL}. The mapping is computed by a unit-tested function, like `p0_sanity_decision`, not by hand.
  3. Keep the sentence "M_CONTROL_FAIL ⇒ no content-use claim for L" and add "M_CONTROL_FAIL is not evidence that L has no content use".

### Q10. Must-fix items (ranked)

- **Verdict: agree there are blockers; five ranked items below.**
- **Evidence.** See §1 and Q1–Q9.

**MF1 (blocks implementation): arm interface, mode parity, seeding and a single shared evaluation path.**
- `set_training_mode` and `train_arm` reject non-F/L arms. P and PA need explicit branches that assert: native encoder frozen; no adapter for P (0 adapter params); 526,336 adapter params for PA; 64 LoRA modules; `trainable_base_parameters == 0`; base in eval; LoRA dropout in train mode.
- Seed explicitly with `torch.manual_seed(seed)` before LoRA attach in P, and keep the same RNG order as L so L/PA/P LoRA inits are comparable.
- Do not fork the evaluation code. Use one eval function parameterised by a memory provider (EG2 adapter / native encoder / mean), so CE, donor selection, `k = min(...)`, copy mask and bootstrap are identical for every arm.
- Pin one crop convention for native memory: either "full encode then crop" or "re-encode the prefix". P0 re-encodes prefixes (`native_memory(model, real_ids[:k])`), which drops the final EOS. Use the same convention for P real, P wrong and the P mean memory, and write it down. Also make the P source length flag independent of `--target-max-length` (P0 reuses it for source max length).
- Assert at runtime, on every forward used for evaluation, that `out.loss` equals the masked per-token mean within 1e-5 (the stop condition in §10 exists only as a unit test today).

**MF2 (blocks implementation): M definition and leakage tests.**
- Pin: M's real reference (full-length, same pass); eval-mode adapter under `no_grad`; per-position eligible counts; mean vs real norm; same-document-set reporting; M-norm and M-global as descriptive variants.
- Tests: (a) a mean builder that takes only the train ids/cache and raises if it sees any val id; (b) the mean is bitwise unchanged when val labels, val cache and the donor table are perturbed; (c) no summary/label tensor is an input to the mean function; (d) `m_eligible=false` handling and the exclusion count; (e) memory row-permutation invariance of T5 decoder logits.
- M probe on P and PA is mandatory, and its outcome gates the interpretation of M on L (Q2).

**MF3 (blocks the 3-seed run; amend the prereg before the debug run): positive-control definition.**
- `P_POSITIVE` and `PA_POSITIVE` need `Δ ≥ .05 ∧ CI_lo > 0`, and step-0 and step-100 evaluation for every arm, so training-induced change is measurable.
- Add PA (native + adapter + LoRA). Add a train-CE trajectory (every 10 updates) and final train/val real CE to every artifact, so regime mismatch is visible.
- Rename the failure labels (Q8, Q9).

**MF4 (blocks the 3-seed run): statistics and label logic as tested code.**
- Define `L > F` as the paired per-document difference with a bootstrap CI lower > 0.
- Compute per-seed means for the "2/3 seeds" rule. Fix or stop reusing the `seeds_positive` field of `bootstrap_paired`, which counts documents.
- Implement `pm_decision(...)` with the full table, including the uncovered cell, and unit-test every branch, as `p0_sanity_decision` is tested.
- Add descriptive reports: median, positive-doc count, top-3 share, leave-top-3-out mean, and a two-way (docs × seeds) bootstrap CI.

**MF5 (blocks the 3-seed run): artifact completeness and provenance.**
- Per arm/seed JSON (`reports/provenance/C5_b0a/pm/{arm}_{seed}.json`): code commit hash, prereg v0.2 hash, args, per-doc K, n_donors, copy tokens and coverage, strict-mask and non-copy Δ, norms, step-0 evaluation, train-CE trajectory, `m_eligible` and counts, `train_mode_policy`, `metric_alignment` check value, generation telemetry for every arm, CPU-seconds per unit and total.
- A final aggregator that verifies the 12-unit artifact set is complete before computing any label (stop condition "9 unit artifact missing" must become 12 with PA).
- Debug isolation: the 1-seed debug must not use any of the three gating seeds with outcome inspection. Use a distinct debug seed and `--steps` small enough for a mechanics check, labelled `gating: false` in the artifact. A mechanics debug on the gating seed 20261108 would let the first Δ values inform later choices.

### Q11. Boundary with B0-B

- **Verdict: agree.**
- **Evidence.**
  - Phase 6 evaluates 20 docs with heavy-tailed Δ; no label from it is a confirmatory result, and `EXPLORATORY_L_SIGNAL` would not carry its own power analysis for 300/95.
  - The prereg already states no label auto-approves B0-B.
- **Conditions to even consider B0-B (all required; a new preregistration and a separate approval remain necessary):**
  1. `P_POSITIVE` and `PA_POSITIVE` (amended, ≥ .05) both pass, and the M-probe on P/PA is positive (M validated).
  2. `M_CONTROL_PASS` for L, with the strict-mask Δ having the same sign.
  3. `L_SIGNAL` with paired `L − F` CI lower > 0, and consistent sign in all 3 per-seed means (not just 2/3).
  4. The effect is not outlier-driven (leave-top-3-out Δ still > 0).
  5. Generation telemetry is not fully degenerate (B0-A: all 120 generations hit the 257-token cap, 0 EOS). Telemetry is not a gate in Phase 6, but it must be reviewed before any scale-up.
  6. A trained LoRA + constant-memory baseline arm (Q2) is pre-registered for B0-B.
  7. The new prereg includes a power analysis from Phase 6's observed SD (planning only), fresh documents distinct from `train[0:20]` and `val[5:25]`, and a compute estimate. Test 163 stays sealed, and Phase 6 documents are not reused as confirmatory data.
- **Do not proceed to B0-B if:** any of P/PA is not sensitive; M is unvalidated or fails; the only signal is L_SIGNAL without M pass; the signal depends on a few documents; the label is `INCONCLUSIVE_SMALL_N`. In particular, "inconclusive" is not by itself a reason to scale. Scaling after an inconclusive result is a power decision to be argued in a new prereg, not a signal-based escalation. If P/PA fail, the follow-up is a regime-redesign prereg, and any STOP escalation of the C5 bridge line needs its own decision record.
- **Next steps.** Add this list to v0.2 §6.3 as "B0-B consideration conditions (necessary, not sufficient)". Keep "no label auto-approves B0-B/B1/B2/C". Make no change to the T5Gemma2 status: D-108 STOP remains in force.

### Q12. Final verdict

- **Verdict: NARROW.**
- **Phase 6 implementation and 1-seed debug:** conditionally approvable. First amend the prereg to v0.2 with MF1–MF3 and the label/threshold edits in Q6, Q8 and Q9, commit it, and record its hash. Implementation of MF1–MF5 is part of the debug deliverable. The debug is mechanics-only and non-gating, uses a debug seed distinct from 20261108/09/10, and its Δ values are not used for any decision.
- **3-seed run:** not approved by this review. It needs a separate gate after the debug report shows: all new tests pass (existing 54 plus P/PA/M tests), runtime asserts hold, M and PA paths work, artifacts are complete, a measured per-unit time and a projected total within the cap.
- **Forbidden:**
  - Test 163 (sealed), P1 data, and external APIs.
  - T5Gemma2 (D-108 STOP stays, no reopening without a new decision record).
  - B0-B, B1, B2, Stage C.
  - Changing thresholds, seeds, donors, steps or documents after seeing any Phase 6 result.
  - Retries or "extensions" of any kind.
  - Any claim in the Q5 forbidden-conclusions list.
- **Maximum compute:** keep the preregistered ≤ 2 CPU-hours (6 threads, no GPU) for the whole Phase 6, **including** the debug run, with a projected-total check from measured debug timing before the 3-seed gate. With PA there are 12 trained units. If the projection exceeds the cap, drop PA's third seed only by a pre-registered v0.2 rule written before the debug, and never as an in-flight decision.
- **Next decision gate:** G1 = v0.2 prereg committed and reviewed (self-check against this list is sufficient if the user prefers). G2 = debug report → 3-seed approval. G3 = results → label → separate B0-B decision.
- **Test 163:** remains sealed. This review neither recommends nor requires opening it.

---

## 3. Final answer table

| Q | Verdict | One-line reason |
|---|---|---|
| Q1 | conditional | P is a valid metric/LoRA pipeline check but near-vacuous (P0 already +3.8/+5.2) and in a different regime from F/L; require ≥ .05, add step-0 reference and a PA arm. |
| Q2 | conditional | Eval-only M is the right swap test and trained M is not needed in Phase 6, but M must be validated on P/PA, where content use is known. |
| Q3 | conditional | No leakage, but real reference, norm shrinkage, survivorship/exclusion and the moot "position-wise" notion need fixes; add M-norm and M-global as descriptive variants. |
| Q4 | conditional | Interpret only through within-arm Δ with step-0 reference plus paired L − F and PA − L; P ⇏ L; define `L > F` as a paired document-level CI. |
| Q5 | conditional | Enough for screening only; forbid null/generalisation/copy claims; add outlier and two-way-bootstrap reporting; measure timing in debug. |
| Q6 | conditional | Keep .05 for L; the lower bar for P is inverted, so amend P/PA to ≥ .05 pre-run; M stays a separation test. |
| Q7 | disagree (as sufficient) | Necessary, not sufficient; doc-level topical/frequency priors are not excluded; add strict/non-copy Δ and row-permutation test. |
| Q8 | conditional | Right not to generalise to bridge STOP, but P0 already passed, so the failure label should say "erased by regime"; diagnostics are step-0 vs step-100 and CE trajectory. |
| Q9 | conditional | Logic is right, label over-claims at n = 20; rename, fill the L_SIGNAL + M fail cell, add M_UNVALIDATED. |
| Q10 | agree (5 blockers) | See MF1–MF5. |
| Q11 | agree | No auto-approval; explicit necessary conditions listed, none sufficient. |
| Q12 | NARROW | v0.2 amendment → implement + non-gating debug; 3-seed needs a separate gate. |

## 4. Must-fix summary (ranked)

1. **MF1** Arm interface and parity for P/PA: new branches in `set_training_mode`/`train_arm`, explicit LoRA seeding for P, one shared eval path via a memory provider, pinned native crop convention, runtime CE-alignment assert.
2. **MF2** M definition and leakage tests: pinned real reference, norm and eligibility reporting, M-norm and M-global variants, a no-val-access test, a perturbation-invariance test, a row-permutation test, and a mandatory M probe on P/PA that gates M-on-L.
3. **MF3** Positive control: P/PA need Δ ≥ .05 ∧ CI_lo > 0 (pre-run amendment), step-0 evaluation for all arms, a PA arm, train-CE trajectory.
4. **MF4** Statistics and labels as tested code: paired `L > F`, per-seed means, fixed `seeds_positive`, full label table with the uncovered cell, renamed labels, outlier and two-way-bootstrap reports.
5. **MF5** Artifact completeness and provenance: commit and prereg hashes, per-doc fields, timing, 12-unit completeness check, and a non-gating debug on a seed that is not one of the three gating seeds.

## 5. Wrong or weak premises in the request

1. "P_POSITIVE = Δ > 0 ∧ CI_lo > 0" validates the assay: it cannot fail given P0 (+3.76/+5.24) unless training destroys the path, and it does not test the F/L regime.
2. P0 `SENSITIVE_POSITIVE` shows graded content sensitivity: untrained CE 12.7/13.2 exceeds `ln|V|` = 12.43, wrong-memory CE 16.5–18.5, and about 49% of the val mean comes from 3 of 20 documents.
3. The copy metric measures copy: the as-run mask covers 82–84% of tokens and Δcopy ≈ Δfull. Only the strict mask is copy-specific.
4. Position-wise mean and the `len ≥ K` rule matter to the decoder: T5 cross-attention has no position bias, so memory is an unordered set. Needs a unit test.
5. M fail ⇒ "no content-use evidence": it is non-detection at n = 20, and M's own sensitivity has not been shown.
6. Three seeds estimate variability: the data order is fixed, so seeds vary init only, and "2/3 seeds > 0" is not computed by any current code.
7. The 1-seed debug on a gating seed is harmless: looking at its Δ values before the 3-seed gate is outcome peeking.