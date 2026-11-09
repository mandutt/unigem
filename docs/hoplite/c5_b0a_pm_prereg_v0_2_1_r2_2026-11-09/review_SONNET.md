# External Review — C5 P/M Prereg v0.2.1-r2 — Sonnet 5.5 (medium)

**Reviewer identity:** Claude Sonnet 5.5, reasoning medium. This is an independent round. I did not reuse the earlier r1 Sonnet answer or any other model's answer.
**Review basis:** `origin/main` HEAD `fc5680ef051bb6d00dbe74e7a0c08da193725b38`. `git fetch` and `git pull --ff-only` reported "Already up to date". The request document names `308648e` as its basis. HEAD is one docs commit later (the review request itself).
**Scope kept:** read-only. No training or eval was run, test 163 was not opened, P1 was not used, no subagents were called. The only write is this file.

Method: I read the request, r2 (770 lines), r1, the r1 synthesis, `m_cohort_preflight.json`, the P0 report, the runner and the metric tests. I recomputed the preflight arithmetic by hand from the JSON lengths. The workspace policy blocked inline Python, so this was not scripted.
- Val h >= 753 gives 15. Val h >= 754 gives 14.
- Train h >= 753 gives 16.
- The excluded 5 and the common_ids list match the JSON.
- `sha256sum` of the committed file equals `3ee3f1ca…837af` and equals the `.sha256` file.

---

## Headline

r2 is a real improvement. The r1 holes are closed in structure:
- `m_valid` now has a slot, and `M_CONTROL_INVALID` is reachable.
- Path flags are enumerated.
- The K rule is written down.
- A builder, aggregation and replay are specified.

But r2 is **not yet a total, executable contract**. I found two silent-VALID holes in the path precedence, one dead label caused by a double-counted axis, an asymmetric validity guard in the signal function, an undefined M-endpoint (copy-mask) rule at zero margin, and two stale or circular text items in the 3-seed checklist. All are text-only and small. Verdict: **NARROW**, with a short r2.1 errata that should be mechanical.

---

## Q1–Q12

### Q1. Total factored contract
- **Verdict: disagree (not yet total).**
- **Evidence (r2 §2.4, §4, §6.2, §7):**
  1. *Silent VALID on NA.*
     - §2.4 NA handling (line 164) lists only `assay_path_ok`, `p0_path_ok` and `p_step100_path_ok`.
     - `test_split_used = NA` is never routed. The first branch tests only `is true`, so NA falls through.
     - `pa_step100_path_ok = NA` is also never tested. The chain checks only `is false`, then `pa_valid`.
     - With `pa_valid = true` and `pa_step100_path_ok = NA`, or `test_split_used = NA`, and the other flags fine, the result is `VALID`.
     - That is a fail-open on the two flags that matter most. The §7.1 domain includes NA for both, so a strict truth-table test would expose it.
  2. *Dead label.*
     - `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` is unreachable. `M_NOT_EVALUABLE` is a *validity* value (§4) and also a *control* value (§5.2).
     - In §6.2 the `l_signal = true` branch tests `validity != VALID` first. Whenever control is `M_NOT_EVALUABLE`, validity is already `M_NOT_EVALUABLE`, which routes to `L_SIGNAL_VALIDITY_INVALID`.
     - Under `VALID`, `m_evaluable` is true, so control cannot be `M_NOT_EVALUABLE`.
     - This violates §7.2 "every label reached at least once".
     - It also mislabels a replay tolerance miss, a cohort miss or a missing seed as `L_SIGNAL_VALIDITY_INVALID`, which reads as an assay failure.
  3. *Asymmetric validity guard.*
     - In §6.2 only the `l_signal = true` branch checks validity.
     - `COPY_ONLY_WEAK`, `FULL_ONLY_WEAK`, `MEAN_CONTRAST_ONLY` and `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE` ignore it. `ASSAY_INVALID` plus `M_CONTROL_PASS` plus `l_signal = false` yields `MEAN_CONTRAST_ONLY`.
     - The B0-B predicate catches this, but a report reader of `headline` does not.
  4. *Smaller gaps.*
     - `m_pass_pos_l` and `m_pass_norm_l` are absent from the §2.1 inventory and the §7.1 domain. `m_pass_l` is an input there, so the AND3 derivation of `m_pass_l`, and of `m_valid` from four flags, is not covered by the truth table.
     - The control branch "p_valid or pa_valid not true" is dead because `m_evaluable` already contains both.
     - `m_evaluable = NA` maps to `M_NOT_EVALUABLE`, while every other NA maps to `NOT_ASSESSABLE`. This is tolerable but should be stated.
- **Next steps:**
  1. Add NA handling for `test_split_used` and `pa_step100_path_ok`, preferably fail-closed. For example, NA `test_split_used` gives `NOT_ASSESSABLE`, and NA `pa_step100_path_ok` gives `NOT_ASSESSABLE`.
  2. Remove `M_NOT_EVALUABLE` from `validity_status`. Keep it only in `control_status`, so validity answers "are the assay and P/PA valid". This also revives the dead label.
  3. Either apply `validity != VALID` as a prefix to all non-small-N signal labels, or state that signal and control are intentionally validity-agnostic. Add the derived-flag tests and the unreachable-label assertion.

### Q2. L preservation and small N
- **Verdict: conditional.**
- **Evidence:**
  - Raw flags plus L-qualified labels is the right invariant (§6.4).
  - r2 *changed* `l_signal` from r1's AND3 to a consensus rule. (F, NA) now gives NA, where r1 and the r1 MF-3 suggestion gave false. This is explicit and defensible, because one-sided false is not "no signal". The consequence is `NOT_ASSESSABLE` for (F, NA) even when control is `M_CONTROL_FAIL`. Accept it, but record it as a deliberate delta.
  - `INCONCLUSIVE_SMALL_N_WITH_*` preserves L flags correctly. The small-N branch precedes the validity qualifier, so an invalid assay with n < 15 shows no validity qualifier. This is acceptable because `validity_status` is a separate axis.
  - **Zero-margin n=15 is executable only if the cohort is defined.** §1.3 says one dropped copy mask makes signal n = 14. That implicitly equates the *signal* cohort with the M cohort.
  - But §6.1 defines `n_signal` as "common target docs with valid copy and full endpoints", with no statement of whether that is the val20 set or the 15-doc M cohort. If the signal is on val20, n_signal has margin of 5 and the §1.3 sentence is wrong. If it is on 15, the primary L signal itself is restricted to the 15 longest docs.
  - r2 also has **no rule for M endpoint validity**. `cohort_ok` is length-only. `delta_memfree_copy` needs the copy mask. If one of the 15 docs has no valid copy mask, the M copy endpoint has n = 14. §9.8 says only "common cohort < 15 → `M_NOT_EVALUABLE`".
  - Nothing says whether this means `m_evaluable = false`, `m_pass = false`, or a CI on 14. §1.3 resolves the analogous case only for the *signal* axis.
- **Next steps:**
  1. State exactly which doc set feeds `n_signal`, `l_copy_signal` and `l_full_signal` (val20, or the 15-doc M cohort). State whether L signal numbers restricted to the M cohort are reported as secondary.
  2. Add an M-endpoint rule. Suggested: if copy-valid docs in the 15-doc cohort < 15, `cohort_ok = false` and the result is `M_NOT_EVALUABLE`. No re-selection, no threshold change.
  3. The copy mask depends only on tokenizer, source text and target, so it is data-only. Compute copy-mask validity for the 15 IDs *before freeze* (pre-result, no forward) and add it to a v2 preflight JSON. That removes the unknown instead of defining a contingency.

### Q3. M preflight (K_M_L = 753)
- **Verdict: agree, conditional on label discipline.**
- **Evidence:**
  - I verified every number by hand: 15 val, 14 at K=754, 16 train contributors, 5 excluded IDs, `common_ids` of 15.
  - The train >= 10 condition is **non-binding**. Val >= 15 alone determines K, because train h at 753 is 16. The rule is therefore effectively "the 15th-longest val doc". That is length-only and outcome-blind.
  - The rule is deterministic, pre-result, and hash-pinned. The hash matches the committed blob, the `.sha256` file and the request.
  - Native lengths are 512 for all 40 docs, so P/PA "prefix 512" is the full native memory (truncation at tokenizer max_length). Only L is prefixed.
  - Prefix 753 versus per-target full K: the cost is that L evaluates a truncated memory. Targets with h of 830 lose about 9%, while the median is about 766, so about 2%. M and real are both cut at 753 in the same comparison (§9.3). The control is internally symmetric, so the principle is *bent but not broken*.
  - Residual problems:
    - The cohort is the 15 longest-of-20 val docs and is length-conditioned. Say so wherever `M_CONTROL_PASS` is quoted.
    - The L adapter is trained on full-length memory and evaluated on a 753 prefix. This is a small distribution shift for M only.
    - The 15-doc cohort is the only place the M gate is computed, so M can pass or fail on 15 docs while the signal is computed elsewhere (see Q2).
  - The preflight `consequence` field says "full-K 11/20 would make M_NOT_EVALUABLE". That is correct and documents why 753 was chosen.
- **Next steps:**
  1. Keep 753 and the label `M_CONTROL_PREFIX753_COHORT15`. Do not retune.
  2. Add the length-conditioned and prefix caveats to the report template.
  3. If the Q2 copy-mask check changes the preflight JSON, re-hash it *before* freeze and update every citation.

### Q4. M builder / aggregation / replay
- **Verdict: conditional.**
- **Evidence:**
  - eval/no_grad, same-IDs for P/PA/L, and seed-average-before-bootstrap (§9.6, §10) are correct. 3 seeds × 15 docs is not 45 units.
  - `delta_memfree = mean_ce − real_ce` is stated (§9.4).
  - Leakage: the M builder uses train20 only, and val is disjoint from train. That is clean. P/PA contributors at 512 use all 20 train docs, which are also the trained docs. This is expected for a training-only mean.
  - Missing pieces:
    - M_NORM for L is scaled to `||real_prefix_753||_F`. That is per target doc, so it uses the target's own memory norm. This is a norm-only leak, and it is exactly why `M_PASS_NORM_CONFOUNDED` exists. State that it is a norm match and not a content leak.
    - Replay `atol=1e-5, rtol=1e-4` is for a separate process on CPU. State thread count and dtype. A tolerance miss makes M permanently `M_NOT_EVALUABLE` with no retry, which is harsh for numerical noise.
    - §9.7 says "replay M builder/eval", so the builder is included. The CE comparison then needs the stored per-doc CE list to compare against.
    - The runner has no `pm-diagnostic` mode yet. It has `smoke`, `metric-smoke`, `train` and `p0-sanity`. That is expected before freeze.
    - `bootstrap_paired` in the runner defaults to seed **20261108**, and r2 fixes **20261109**. Add an explicit-seed test. The function also still emits `seeds_positive` as a document count (runner line 395). The DoD covers renaming it.
- **Next steps:**
  1. Fix replay conditions (threads, dtype, process isolation) in the manifest, and state the exact quantity compared.
  2. Test that the bootstrap seed is 20261109 and that the `documents_positive` key is used.
  3. Tag M_NORM results as "norm-matched, not norm-independent" in the artifact.

### Q5. PA
- **Verdict: agree.**
- **Evidence:**
  - "PA = acquisition control", `PA_STEP100_NOT_VALID` and `PA_RETENTION` as non-gate are consistent (§8.2).
  - The PA path-fail versus P path-fail asymmetry is now explicit (§2.4), and the "simultaneous failure, P first" rule is stated.
  - The mT5 final hidden versus EG2 layer19 scale/geometry caveat is recorded.
  - P0 context supports caution on P_VALID. Untrained real CE is 12.7/13.2, **above ln|V| = 12.43**, and wrong-source CE is 16.5/18.5. The decoder is confidently wrong and wrong-source is more so, so P0 Δ partly reflects calibration. P_VALID (Δcopy >= .05 with CI lower > 0) is a permissive screen. That is by design and must not be tightened after results.
  - The PA path-NA hole is the same as in Q1.
- **Next steps:**
  1. Fix the `pa_step100_path_ok = NA` hole (Q1).
  2. Say in the report that P_VALID and PA_VALID are screens, not evidence of content use.
  3. Keep `ADAPTER_REGIME_LOSS` and `M_CONTROL_NOT_VALID` absence tests.

### Q6. Cap / D0 / D1
- **Verdict: conditional.**
- **Evidence:**
  - 4 arms (F/L/P/PA) × 3 seeds = 12 units × 100 updates = 1,200 (§11.1). The arithmetic is correct. M is eval-only.
  - D0 is 0-update, 4 configs and ≤15 min, and it is separate from the cap. D1 is 4 × 1 update, ≤20 min, needs separate approval, and is also separate from the cap. Seed 20261111 is not in {20261108, 20261109, 20261110}.
  - Timing weakness: a 1-update projection to 100 updates × 12 units is optimistic. It excludes step-0 evals, wrong-donor evals (5 donors), final evals, M builder runs, M evals, replay, and generation if any. It also includes first-step warmup and allocation costs.
  - §11.4 says "per-phase timing" but D1 is defined as 1 update with no labels. It does not say that D1 must time the eval, M and replay phases.
  - The 96-minute rule (0.8 × 2 h) gives margin, but it is only meaningful if the non-training phases are measured.
  - "Separately approved timing probe" is undefined, so it is a possible loophole.
  - The cap text says to stop and report on overrun, with no retry. It is unclear whether partial results count as a result. Specify that an aborted run yields no labels, or that labels are computed only on a complete 12-unit set.
- **Next steps:**
  1. Define D1's required timed phases: one train update, a step-0 eval, a final eval for one doc subset, an M builder pass, and replay, each extrapolated by documented counts.
  2. Define the minimal content of an acceptable "timing probe". Otherwise delete the option.
  3. State the outcome of a partially complete run (no labels, report only).

### Q7. Statistics
- **Verdict: conditional.**
- **Evidence:**
  - n_boot = 1000, percentile 2.5/97.5, seed 20261109, document unit, seed-average-before-bootstrap and `documents_positive` are all executable. The runner already implements the paired bootstrap, and P0 used 1000 resamples.
  - The M pass needs 4 CI-lower > 0 conditions (full and copy, POS and NORM) per variant. P, PA and L give 12 CI gates at n = 15. This is intentionally strict, and a power-limited M gate will often yield `M_CONTROL_FAIL`. The interpretation "NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE" must not be read as evidence of absence at n = 15.
  - **Tail risk is not in the M gate.** P0 val has mean +5.24 against median +2.97 and top-3 share .486, and 18/20 docs positive. `tail_driven` (top-3 share > .50 or leave-top-3-out <= 0) is only a flag. M_PASS and P_VALID can be satisfied by three documents.
  - `MARGINAL_SIGNAL_COHORT` is a flag only. That is coherent.
  - The percentile bootstrap at 15–20 docs is anti-conservative. r2 admits this (§10).
  - The tail threshold .50 sits almost exactly at the P0 observed .4862. A tail_driven flip is likely, so report it, not gate on it.
- **Next steps:**
  1. Report `tail_driven` and top-3 share for the M deltas and P deltas as well as L, as flags only.
  2. Add a mandatory report line: "n = 15 CI gate; failure is not evidence of absence".
  3. Test that the bootstrap rng is re-seeded per call, so that paired endpoints use identical resample indices. Document that this is intended.

### Q8. Remaining Must-fix (ranked)
- **Verdict: conditional (r1 items mostly closed, new defects found).**
- **r1 closure table (§15):** the claims "closed" for MF-1 through MF-6 are structurally true. Exceptions are the two silent-VALID NA cells, the dead label, and the checklist errors below.
- **Ranked list:**
  1. **Silent-VALID on NA** for `test_split_used` and `pa_step100_path_ok` (§2.4, Q1).
  2. **Stale M preflight hash in the 3-seed checklist.** §12 item 6 cites `07c3fe4c…`, but the frozen hash is `3ee3f1ca…` (§1.4, the `.sha256` file and the request). A checker built from §12 would reject the right artifact.
  3. **Circular checklist item.** §12 item 9, "P/PA M_VALID true", is a *precondition for launching* the 3-seed run, but `m_valid` is an *output* of that run. It must become "M_VALID defined and computed in the manifest".
  4. **Double-counted `M_NOT_EVALUABLE`** in validity and control, which makes `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` dead and mislabels M failures as `L_SIGNAL_VALIDITY_INVALID` (Q1).
  5. **Undefined doc set for signal versus M cohort**, and no M copy-mask endpoint rule (Q2). Pre-compute copy-mask validity for the 15 IDs.
  6. **Asymmetric validity guard** in §6.2 (Q1).
  7. **Minor:**
     - `m_pass_pos_l` and `m_pass_norm_l` are missing from the inventory.
     - Replay conditions are underspecified.
     - D1 timed phases and the "timing probe" are undefined.
     - The bootstrap seed default is 20261108 in the code against 20261109 in the plan.
- **New problems r2 introduced:** the consensus `l_signal` (a deliberate change), the validity/control overlap, and the two checklist errors.
- **Next steps:**
  1. Issue a short errata (r2.1 or r3) covering items 1–7 as text only.
  2. Re-hash if the preflight changes, and re-grep for `07c3fe4c`.
  3. Ask the implementer to generate the exhaustive truth table with an unreachable-label report.

### Q9. Freeze and implementation approval
- **Verdict: conditional.**
- **Evidence:** the r2 protocol is close. The remaining defects are textual and do not change any threshold, seed, donor, step or LR. The truth-table domain is about 3^12 × 5 ≈ 2.6M cells. That is cheap for a pure function, so no sampling is needed.
- **Required before freeze:** the errata in Q8 items 1–6.
- **Required tests before implementation is accepted:**
  - exhaustive truth table (exactly one triple per cell, inputs not mutated, every label reachable, unreachable labels listed);
  - NA handling for every path flag, including `test_split_used` and `pa_step100_path_ok`;
  - AND3 derivation of `m_valid` (81 cells) and `m_pass_l`;
  - `bootstrap_paired` seed 20261109 and `documents_positive`;
  - a preflight hash test against the committed blob;
  - the seed-average and replay tests in the DoD (§13).
- **Next steps:**
  1. Approve implementation, unit tests and D0 *only after the errata is committed and re-frozen*.
  2. Freeze by commit hash and record the hash in the manifest.
  3. Do not start code before that commit.

### Q10. D1 / 3-seed
- **Verdict: conditional.**
- **Evidence:**
  - Keeping D1 (timing) and the 3-seed run as separate gates is right. D1 as a 3-seed precondition and not an implementation gate is a coherent design (§11.3).
  - Missing from the §12 checklist:
    - the corrected preflight hash (Q8 item 2);
    - removal of the circular `M_VALID true` item (Q8 item 3);
    - replay conditions;
    - an explicit statement that an aborted or partial run yields no labels;
    - a disk and memory check for 12 units;
    - the copy-mask preflight result (Q2);
    - a manifest field recording that `bootstrap_seed = 20261109`;
    - D0 and D1 outputs carrying `labels_computed: false` and `not_a_result: true`, with a test that no label function is called in those modes.
- **Next steps:**
  1. Repair §12 as in Q8.
  2. Add the missing checklist items above.
  3. Keep explicit user approval as the final item.

### Q11. B0-B boundary
- **Verdict: agree, with a restatement.**
- **Evidence:** §14 keeps "no label auto-approves B0-B/B1/B2/Stage C", and requires separate prereg and approval. `m_valid == true` in the predicate is redundant with `M_CONTROL_PASS`, but harmless.
- **Restated predicate for r2 labels (necessary, never sufficient):**
  ```text
  validity_status == VALID
  AND control_status == M_CONTROL_PASS     # implies m_valid, m_evaluable
  AND signal_status == EXPLORATORY_L_SIGNAL
  AND n_signal >= 15
  AND tail_driven reported (not auto-gating)
  AND leakage/mode/metric checks pass
  AND artifact and manifest complete, hash-pinned
  AND cohort scope stated: M_CONTROL_PREFIX753_COHORT15, length-conditioned
  AND separate new prereg AND explicit user approval
  ```
  Full-K 11/20, P0 and PA_RETENTION are not evidence. This round approves none of Phase 6, B0-B, B1, B2 or Stage C.
- **Next steps:**
  1. Replace §14 with the restated predicate and drop the redundant `m_valid` line, or mark it as a consistency check.
  2. Add "the L signal and M control cohorts must be stated" (Q2).
  3. Keep T5Gemma2 closed (D-108 STOP).

### Q12. Final verdict
- **Verdict: NARROW.**
- **Evidence:** the defects above are mechanical text fixes and none touches a threshold, seed, donor, step or LR. r1's structural Must-fix items are closed. Not CONTINUE, because the contract still fails strict totality (silent-VALID on NA) and the 3-seed checklist is wrong on two items. Not STOP, because nothing in the design is unsound.
- **Next steps:** see the summary below.

---

## Final summary

| Item | Position |
|---|---|
| **Final verdict** | **NARROW** (text-only r2.1/r3 errata; no result-dependent change) |
| r2 freeze | Not as written. Freeze after the errata, by commit hash. |
| Implementation + unit tests | Conditional: approved only after the errata is committed |
| D0 (0-update mechanics) | Conditional: same condition. ≤4 configs, ≤15 min, seed 20261111, `labels_computed:false`, `not_a_result:true`, separate from the 1,200-update cap |
| D1 | Not approved here (separate approval; ≤20 min, 4 × 1 update, seed 20261111) |
| 3-seed | Not approved here (separate gate, 12 units × 100 = 1,200 updates, 2 h cap, projection <= 96 min from D1) |
| Forbidden | Phase 6, B0-B, B1, B2 and Stage C approval; P1; test 163 (sealed); T5Gemma2 (D-108 STOP); any threshold, seed, donor, step or LR change after results |
| Max compute implied | D0 ≤15 min, D1 ≤20 min, registered 2 h, all CPU, 6 threads, no retry |

**Must-fix (ranked):**
1. NA fall-through to VALID for `test_split_used` and `pa_step100_path_ok`.
2. §12 item 6: stale hash `07c3fe4c…`; it should be `3ee3f1ca…`.
3. §12 item 9: circular precondition "P/PA M_VALID true".
4. Remove `M_NOT_EVALUABLE` from `validity_status` (or fix routing). This revives the dead `L_SIGNAL_M_CONTROL_NOT_EVALUABLE`.
5. Define the signal doc set versus the M cohort, and add an M copy-mask endpoint rule. Pre-compute the copy-mask validity for the 15 IDs before freeze, and re-hash if the preflight JSON changes.
6. Make the validity guard in §6.2 symmetric, or state that it is intentionally absent.
7. Minor items: inventory `m_pass_{pos,norm}_l`, replay conditions, D1 timed phases or deletion of the "timing probe" option, and the bootstrap seed default.

**Wrong or weak premises noted:**
- "The train >= 10 condition constrains K". In fact only val >= 15 binds.
- "Zero-margin means one copy-mask loss gives n = 14". That is true only if the signal cohort is the M cohort, which r2 never states.
- "m_valid is a launch precondition". It is a run output.
- P0 SENSITIVE_POSITIVE is metric/path sensitivity only. Untrained CE above ln|V| means part of Δ is calibration.

Not claimed: no approval of Phase 6, B0-B, B1, B2 or Stage C; no P1 or test 163 use; no reopening of T5Gemma2; no threshold changes proposed.