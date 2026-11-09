# Independent review — Sol 6.1 medium reviewer

Reviewer: **Sol 6.1 medium**, independent external reviewer for unigem.
Date: 2026-11-09 (UTC).
Round: **v0.2.1-r3.1**, a new independent review, not a duplicate of r3.

## Review basis and safeguards

- Repository: `mandutt/unigem`; requested basis: current `origin/main`.
- Ran `git fetch origin`, then `git pull --ff-only origin main`. Both succeeded; pull reported `Already up to date.`
- Resulting HEAD and `origin/main`: **`c4ed30a1f120b01905291602e3aec53f87c765fc`**.
- The request's historical authoring HEAD `7264c55` is not substituted for this synchronized review basis.
- Read the complete review request, r3.1, r3, the requested r3 synthesis, preflight JSON, P0 report, runner, and metric test file. Consulted inherited contract passages in v0.2, v0.2.1 errata, r1, and r2 to resolve reference lengths and unchanged signal thresholds. The mandated synthesis is historical context, not this review's verdict. No individual reviewer answer was reused.
- No subagents, additional models, external APIs, model loading, training, evaluation, or test execution. No P1 data used; sealed test 163 was not opened. No P0 rerun.
- Verification was static reading, Git inspection, SHA-256, and standard-library arithmetic over the supplied preflight metadata. Historical “54 tests pass” is not a fresh result and does not establish PM implementation coverage.
- The only repository file written by this review is this report. No commit, PR, or execution approval is issued.

## Executive verdict

**Final verdict: NARROW — text-only residual repair before freeze, implementation, or D0.**

The factored decision pseudocode is substantially better and, on its declared tri-state/status domains, has a terminating branch for every input. ANDn, validity-NA labels, known-failure precedence, M availability routing, exact M endpoint identity, and replay-stage separation are meaningful improvements. There is no basis for abandoning the diagnostic entirely.

Nevertheless, the **whole normative contract is not yet self-consistent or fully executable**:

1. §9.2's `L_FULL_SIGNAL = same for full` imports `.05` from copy under a literal reading, whereas the inherited explicit full threshold is **mean delta_full > 0**. This conflicts with the stated no-threshold-change scope.
2. §6.2 fixtures 16–17 confuse **L shuffled-memory signal** with **L M pass**. Fixture 17 requires control PASS together with M pass L false, an impossible derived state under §4.3. Fixture 16 does not supply enough conditions to entail its signal label.
3. D1 fixes document counts but still needs an unambiguous end-to-end workload ledger: M construction versus target scoring, donor multiplicity, variants, replay coverage, retained generation telemetry, and non-forward overhead.
4. Statistics need explicit partial-endpoint and undefined-tail behavior across the newly complete n_signal domain; otherwise different implementations can silently use different documents/seeds or treat unknown concentration as false.

These are pre-result specification repairs, not requests to tune thresholds, seeds, donors, steps, or learning rates after outcomes. r3.1 §16 already provides a **Must-fix-only r3.2** route for a NARROW review.

## Compact Q1–Q12 verdicts

| Question | Verdict | Main finding |
|---|---|---|
| Q1 Total factored contract | conditional | Dispatch is total on declared domains; required fixtures are not consistent with it. |
| Q2 L preservation | agree | Raw flags plus factored statuses preserve L without upgrading validity NA to invalid. |
| Q3 M preflight/cohort | agree | Hash and counts verified; only a selected prefix753/common15 diagnostic. |
| Q4 Builder/endpoint/replay | conditional | Good fail-closed contract; implement per-arm/seed/target checks and exact replay coverage. |
| Q5 PA | agree | Acquisition terminology and non-gating retention are appropriately limited. |
| Q6 Cap/D0/D1 | conditional | Arithmetic and approval separation are sound; workload accounting is incomplete. |
| Q7 Statistics | conditional | Core pooling/constants are sound; full-threshold shorthand and undefined inputs remain. |
| Q8 Remaining Must-fix | disagree | The claim that every residual is closed is too strong; ranked repairs below. |
| Q9 Freeze/implementation | disagree | Do not freeze unchanged r3.1 or authorize implementation/D0 on it. |
| Q10 D1/3-seed | conditional | Separate gates are right; require complete timing/replay/schema proof before launch. |
| Q11 B0-B boundary | agree | Separate preregistration and explicit approval remain indispensable. |
| Q12 Final disposition | conditional | NARROW to text repair; reconsider implementation and D0 only after corrected freeze. |

## Ranked Must-fix

### MF-1 — Expand the full signal predicate without changing its threshold

**Evidence:** r3.1 §0 lines 21–25 says thresholds are unchanged. §9.2 lines 567–572 gives copy mean `>= .05` followed by `L_FULL_SIGNAL = same for full`. In contrast, v0.2 §6.2 lines 218–221 and v0.2.1 errata §4.3 lines 311–318 explicitly require **full mean > 0**, positive full CI lower bound, positive paired L−F full mean, and positive full seed means in at least two of three seeds. Neither r3 nor r2 explicitly replaces that full magnitude threshold.

**Impact:** for full mean `0.02`, positive CI lower bound, positive L−F, and two positive seed means, the inherited predicate passes but a literal r3.1 “same” predicate fails. This can change full-only and overall L labels before any model code is written.

**Required repair:** write both predicates in full. Preserve copy `>= .05` and full `> 0`; explicitly identify `seed_mean` as the arm-L shuffled-minus-real contrast for the corresponding endpoint, not the L−F contrast. L−F remains its separately paired positive-mean condition. This restores the existing contract rather than selecting a new threshold.

**Acceptance:** synthetic boundary cases for full `(0, .05)`, full zero, copy just below/exactly `.05`, and one versus two positive seed means. No real outputs or registered seed runs are needed.

### MF-2 — Correct the cross-axis oracle and cover the actual L M-pass axis

**Evidence:** r3.1 §4.3 lines 222–225 makes `M_CONTROL_PASS` require `m_pass_l=true`. Yet §6.2 line 395 says “M pass L false + control PASS → MEAN_CONTRAST_ONLY.” This state cannot arise from the derived flags. Line 394's “M pass L true + control PASS → EXPLORATORY_L_SIGNAL” is insufficient: that label also needs validity VALID, n_signal at least 15, and both L signal flags true. M contrast and L shuffled-donor contrast are different quantities.

**Required repair:** fixture 16 should explicitly set **l_signal=true**, validity VALID, n_signal>=15, and a derived control PASS. Fixture 17 should set **l_copy_signal=false and l_full_signal=false**, with the same validity/n/control prerequisites. Both fixtures must have `m_pass_l=true` to derive control PASS. A genuine `m_pass_l=false` fixture must derive control FAIL when availability/calibration/P/PA are good.

§6.1's nine-cell `(l_copy,l_full)` axis does not enumerate `(m_pass_pos_l,m_pass_norm_l)`. Add that nine-cell derived M-pass axis, with false+NA tests, and enumerate the combined 5-input availability primitive (`3^5 = 243` cells) or give equivalent explicit cross-axis cases. Full global Cartesian enumeration is unnecessary.

**Acceptance:** expected triples are derived from primitive inputs, not by injecting an inconsistent control status; all labels are reachable in the corrected function. Fixture defaults must be explicit, especially validity and n_signal, because small-N and validity branches precede L/control branches.

### MF-3 — Bind D1 phase names to all retained registered work

**Evidence:** r3.1 §10.3–10.4 fixes 20-doc step0/final evaluation and 20-train/15-target M work, but the formula names only `t_M_build_15`. Construction alone is not the real/POS/NORM target CE scoring required by §8.3. The inherited v0.2 §4 fixes five donors; §5.2 and §8 require secondary/telemetry artifacts, including generation. The current runner's `train_arm` separately calls `evaluate_arm` and `generate_arm` (lines 723–724), demonstrating that CE evaluation does not automatically include generation. Replay is a separate process, also with startup cost.

**Required repair:** define a phase ledger identifying which timer includes each retained computation: all donor pairs for step0/final, M train-memory construction and 15-target real/POS/NORM scoring for all four arms, replay of the required endpoints, retained secondary/generation work, and load/checkpoint/process/report overhead. Avoid double counting cached real CE. Explicitly map every term to a measurement or a stated conservative bound inside the existing cap. Do not silently drop work to satisfy the projection.

If subset normalization remains permitted (§10.4 line 634), specify the fixed subset and scaling rule before D1; total phase time cannot simply be multiplied per document when a phase also contains fixed train-builder/startup cost. The one-update train timing must identify whether it includes AdamW's first-step allocation and which registered training workload it represents.

**Acceptance:** no omitted phase yields a valid projection; an end-to-end ledger must still satisfy the unchanged **96-minute launch screen**, **120-minute hard registered cap**, and no retry/extension. This review does not require executing D1 or changing its budget.

### MF-4 — Make partial signal endpoints and undefined tail summaries explicit

**Evidence:** r3.1 §5.1 defines n_signal as documents with valid copy/full endpoints, without spelling out the arm/seed intersection. §9 requires seed averaging before bootstrap and paired L−F; inherited v0.2.1 errata §1.5 prohibits pooling a missing seed, and §4.4 requires a common-document subset. These requirements should be bound to one canonical endpoint key set, rather than silently averaging whichever seeds/arms survive.

The same §9.2 lines 576–578 permits top3_share=null for a zero/nonfinite denominator but then compares it with `.50`. Leave-top-three-out mean is also undefined at n<=3, within §5.1's explicit domain 0..20. A language-level null comparison is not an executable statistical rule.

**Required repair:** define valid finite signal endpoint membership across the required F/L arms and all three registered seeds; use the same retained IDs for copy/full and paired L−F. Record excluded IDs/reasons; do not average fewer seeds to create a complete document. Define NA routing for unavailable CIs/seed means and for empty leave-top-three-out statistics. Specify tail_driven's tri-state behavior when one summary is unknown: a known positive tail criterion can set true; both known false can set false; otherwise unknown, not silently false. No new magnitude cutoff is requested.

**Acceptance:** synthetic ragged/missing/nonfinite endpoint cases, n=0..3, zero-sum deltas, and null top-three share must produce an explicit status/reason without an exception or an affirmative eligibility upgrade.

## Detailed answers to section 5

### Q1. Total factored contract

**Verdict: conditional.**

**Evidence:** r3.1 §§2–5 separates validity, availability/calibration, and signal. ANDn is false-dominant; ORn is true-dominant; NOT3 preserves unknown. The 2/4/5 operand requirements address arity truncation. Validity §§3.2–3.4 has explicit precedence and a final VALID branch; control §4.3 and signal §5.3 each end with NOT_ASSESSABLE. F1–F8 correctly distinguish earlier known failures from later unavailable flags. For example, test_split NA with P path false gives ASSAY_INVALID, while PA-path NA with p_valid=false gives P_STEP100_NOT_VALID.

This is total **as pseudocode on its declared domains**, not proof of an implemented total pipeline. MF-2's mandatory fixture contradicts the derived control function; MF-1/MF-4 leave upstream statistics non-unique or undefined. The global phrase “known failure first” should be understood as the displayed ordered stages, not as every known downstream failure overriding every upstream NA.

**Next steps:**
1. Repair MF-1/MF-2 before freeze; retain the displayed validity precedence.
2. Define a primitive-only decision input schema, derived flags internally, and deterministic reasons for NA/invalid inputs.
3. Require corrected per-axis coverage, F1–F8, every-label reachability, and input immutability in synthetic tests after approval.

### Q2. L preservation

**Verdict: agree.**

**Evidence:** §5.3 preserves small-N L/copy-only/full-only labels before validity dispatch; n_signal NA falls back with raw flags. At adequate n, validity NA has separate `*_VALIDITY_NOT_ASSESSABLE` labels rather than calling unknown invalid. Copy-only/full-only are handled before the consensus-NA fallback; `(true,false)` is therefore not lost merely because l_signal consensus is NA. §5.4 requires `(validity, control, signal, flags, reason)` together, preventing a small-N headline from hiding an invalid assay. Mixed true/NA retains the raw evidence but does not assert copy-only or full-only.

The agreement is about preservation and label semantics, not about whether upstream signal statistics are already uniquely specified.

**Next steps:**
1. Test all nine copy/full tri-state pairs against validity VALID/invalid/NA and n below/at/above 15.
2. Preserve raw endpoint flags and reason fields even for n_signal NA and small-N labels.
3. Render all factored statuses together; never present a preserved invalid/NA L flag as affirmative evidence.

### Q3. M preflight / cohort

**Verdict: agree.**

**Evidence:** the committed preflight SHA-256 is exactly **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`**. Static recomputation from its length maps gives K=753: **16 train contributors, 15 eligible val documents**; K=754: **16 train, 14 val**. The common_ids set is exactly the 15 length-eligible/native512 targets, with 15 unique entries. Native train/val have 20/20 at 512. This supports the maximum-K rule without looking at outcomes. Full-K 11/20 is recorded as secondary, not a rescue cohort.

The 15 longest-of-20 cohort is selected by memory length and has **zero exclusion margin**, not an unbiased stand-in for all val20. Signal val20 and M15 are properly separate. Exact endpoint 15/15 must still be demonstrated later; metadata eligibility is not finite CE evidence.

**Next steps:**
1. Bind the exact common_ids and preflight hash in manifests and endpoint validation.
2. Report all five excluded IDs and retain `M_CONTROL_PREFIX753_COHORT15` in every interpretation.
3. Fail M availability on any missing primary target; never lower n to 14 or promote full-K secondary results.

### Q4. M builder / endpoint / replay

**Verdict: conditional.**

**Evidence:** §§4.1/8.2 adds builder_ok, contributor minimum 10, finite tensors and positive norms; known zero/nonfinite/contributor failure routes to M_NOT_EVALUABLE, not M calibration failure. §8.3 binds exact 15 IDs × three seeds × four arms × two primary variants, real/control finite CE, copy_ce present, minimum five copy tokens, and no duplicate/substitution. This implies 360 arm/seed/target/variant keys, each needing its declared real/control endpoints; it does not imply independent duplicated real forwards are required.

The inherited r2 §9.3 fixes matched **prefix real reference**, not donor-cropped or full-K reference. M_NORM uses the target real-prefix norm, so it is not strictly target-independent: only the mean's directional source is train-only. A magnitude-matched control with disclosed norm dependence is acceptable here, not a causal semantic-content isolation claim. The post-run final checkpoint/replay hashes and separate-process CE tolerance `atol=1e-5, rtol=1e-4` are correctly distinct from prelaunch debug hashes.

**Next steps:**
1. Quantify builder_ok over every required arm/seed/target; check scalar norms themselves are finite before division, with train-only contributor provenance and eval/no_grad mode.
2. Materialize the exact endpoint key schema, including F's own checkpoint/builder under the new four-arm requirement; aggregate failures with explicit reasons.
3. Require debug replay equality evidence, not merely a hash's presence, and final replay coverage for every required endpoint before report interpretation; incorporate that workload in MF-3.

### Q5. PA

**Verdict: agree.**

**Evidence:** §7.2 explicitly identifies native memory + random adapter + decoder LoRA as an **acquisition control**, uses PA_STEP100_NOT_VALID, forbids ADAPTER_REGIME_LOSS, and makes PA_RETENTION non-gating/null-capable. Inherited r3 §7.2 and v0.2.1 §2.2 require an actual PA step0 random-adapter reference rather than substituting P0. §7's scale/geometry caveat prevents a PA/P/L comparison being misread as clean causal identification of EG2 adaptation.

P0's train delta_copy +3.7617 and val +5.2375, positive CIs, demonstrate historical native-path sensitivity only. Val median 2.9739/top-three share .4862 and real CE around 12.7/13.2 above ln|V|≈12.43 limit stronger claims. P0 source length 256 does not validate registered M's native512 path, and no trained P/PA/M result has been seen.

**Next steps:**
1. Assert P no-adapter/zero-LoRA and PA random-adapter/zero-LoRA initialization and mode policies in the new tests.
2. Record actual step0/step100 movement and finite/null retention reasons without gating on retention.
3. Keep scale/geometry and historical256/native512 caveats adjacent to conclusions; do not rerun P0 for this review.

### Q6. Cap / D0 / D1

**Verdict: conditional.**

**Evidence:** §10 arithmetic is correct: four arms × three seeds ×100 updates = **1,200** registered updates. D0 is zero updates, <=4 configs, <=15 minutes. D1 is four one-update arm-seeds, shared debug seed 20261111, <=20 minutes, separately approved. If all stages were separately approved, prospective totals are **1,204 updates / 155 wall-clock minutes**. Six CPU threads do not turn this into 155 aggregate CPU-minutes; r3.1 explicitly controls wall time. GPU and retry are disallowed.

The projection factor three and factor100 are correct, and a 96-minute launch screen leaves 24 minutes below the 120-minute registered wall cap. MF-3 remains: matching document counts is not by itself complete runtime accounting. The numbered D1 phase list must not be executed in literal training-before-step0 order; step0 is measured before the update or from an identical restored unupdated state.

**Next steps:**
1. Freeze the workload ledger and pre-update step0 ordering before implementation/D1.
2. Enforce separate D0/D1/registered timers and update counters, cap abort, no retry, and no extension.
3. Do not run D1 or the registered experiment under this consultation; require explicit separate approvals.

### Q7. Statistics

**Verdict: conditional.**

**Evidence:** §9 correctly freezes n_boot=1,000, percentile 2.5/97.5, bootstrap seed20261109, document units, and seed averaging first. Three seeds ×15 M documents are not 45 independent observations. Inherited r3 §9 defines documents_positive and seeds_positive separately. Runner lines 384–397 still use seed20261108 and label a document-positive count `seeds_positive`; §9.2's new module is therefore a justified implementation requirement, not existing functionality.

A two-of-three positive-seed-mean condition is executable once tied to the correct L endpoint contrast. It is not a two-of-three significant-CI rule or a new seed-selection rule. MF-1 addresses the full threshold regression; MF-4 addresses consistent paired IDs and NA statistics. Signed `sum(top3)/sum(all)` is descriptive and may fall outside [0,1]; it is not a probability or ordinary positive-mass fraction.

**Next steps:**
1. Apply MF-1/MF-4, keeping all existing constants and thresholds unchanged.
2. Test seed averaging before document bootstrap, paired L−F alignment, deterministic RNG/results, and separate document/seed counts with synthetic arrays.
3. Report per-seed and per-document distributions, signed top-three share, leave-top-three-out mean, and anti-conservative small-cohort uncertainty; no seed×document pseudoreplication.

### Q8. Remaining Must-fix

**Verdict: disagree** with the blanket “all residuals closed” assertion in §15.

**Evidence:** MF-1 is a newly introduced ambiguous threshold restatement; MF-2 is a new impossible mandatory truth-table cell. MF-3 leaves the earlier workload residual only partially closed, and MF-4 concerns newly explicit n_signal values and null statistics. ANDn, the NA label split, precedence-aware F1–F8, builder routing, hash-bound endpoint identity, and replay-stage distinction are materially closed at text-design level. The statistics and truth-table changes are not yet complete simply because they appear in the closure map.

**Next steps:**
1. Make the four ranked text repairs above in a Must-fix-only r3.2, with no outcome-informed protocol tuning.
2. Cross-check every normative fixture against the displayed dispatch and inherited explicit formulas.
3. Request review of that correction before recording a freeze or starting implementation.

### Q9. Freeze and implementation approval

**Verdict: disagree** with freezing unchanged r3.1 and beginning implementation/unit tests/D0 now.

**Evidence:** §16 prohibits code before freeze and specifies r3.2 for a NARROW review. A literal full-signal implementation and a literal fixture17 implementation cannot both respect the intended no-threshold-change, derived-control contract. Historical metric tests do not resolve this: `eval/tests/test_c5_b0_metric.py` covers alignment, masking, telemetry, F/L mode, native donors and descriptive P0 decisions, not the PM decision contract. The current CLI (runner line755) has smoke/metric-smoke/train/p0-sanity, not pm-diagnostic.

**Next steps:**
1. Resolve MF-1–MF-4 textually and identify the corrected freeze hash before implementation.
2. Require synthetic decision/ANDn/availability/calibration/L-pass, stats/missingness, endpoint-identity and replay contracts in the implementation DoD; keep those pure tests independent of local model availability.
3. After explicit approval, implement and test, then consider only D0 within its own zero-update cap; D1 and three-seed remain separate decisions.

### Q10. D1 / three-seed boundary

**Verdict: conditional.**

**Evidence:** §10 forbids D0-only timing projection and D1 substitution; §11 requires freeze/code hashes, tests, D0, D1, preflight, debug-seed separation, 96-minute projection, manifests, replay and explicit approval. Item14 is now the prelaunch debug hash, and item18 is the plan for post-run final-hash validation, eliminating circular demand for a not-yet-trained checkpoint. M_VALID remains a computation contract, not a prelaunch observed true value. These are correct boundaries.

Missing explicit launch evidence should be completed by MF-2–MF-4: a consistent primitive/endpoint schema, successful replay equality rather than hash presence alone, and complete end-to-end timing. Builder/calibration/seed/endpoints at registered final states are post-run gates, not requirements to peek at trained outcomes before launching.

**Next steps:**
1. Bind the corrected protocol, implementation, model/tokenizer/cache identity, donor manifest and timing workload to launch artifacts.
2. Require D1 completion/equality evidence and a finite nonnegative <=96-minute projection for the retained workload, with no omitted phase.
3. Obtain separate explicit three-seed approval only after the checklist; enforce final endpoint/replay validation before interpreting outputs.

### Q11. B0-B

**Verdict: agree** that the no-automatic-approval boundary is preserved.

**Evidence:** §14 and §17 explicitly keep B0-B/B1/B2/Stage C separate. The r3.1 predicate is, as a necessary candidate-screening contract:

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid == true                 # consistency check, implied by control PASS
AND (tail_driven == false OR tail status explicitly disclosed for separate review)
AND leakage/mode/metric checks pass
AND required artifacts complete
AND a separate preregistration and explicit approval exist
```

Also quote `M_CONTROL_PREFIX753_COHORT15`. Full-K11, P0 and PA_RETENTION do not qualify as B0-B evidence. “Or explicitly reported” means disclosure, not an evidentiary waiver or a machine-true tail gate. An unknown or adverse tail flag requires explicit consideration in the separate decision. Even a fully favorable diagnostic is not Phase6/B0-B/B1/B2/StageC approval from this review.

**Next steps:**
1. Keep all downstream execution disabled absent separate preregistration/approval.
2. Report both tail diagnostics and any unknowns alongside the exact prefix/cohort limitation.
3. Check predicate/flag consistency rather than accepting a favorable signal string alone.

### Q12. Final verdict and scope

**Verdict: conditional. Final disposition: NARROW.**

**Evidence:** the diagnostic design remains worth considering, but MF-1 and MF-2 alone prevent an unambiguous unchanged freeze; MF-3/MF-4 complete the operational/statistical contract. No trained P/PA/M outcome justifies stopping the research question or declaring success. r3.1 §16 allows a small text-only repair instead of another expansive redesign.

**Next steps:**
1. Prepare Must-fix-only r3.2 without threshold/seed/donor/step/LR changes.
2. Re-review and explicitly freeze the corrected contract before code.
3. Advance only by separately approved implementation/tests, D0, D1, and registered-run gates; never infer downstream approval.

## Final scope ledger

| Item | Recommendation in this consultation |
|---|---|
| Unchanged r3.1 freeze | **No** |
| Immediate permitted next work | Text-only Must-fix repair for later review; this task writes only this report |
| Implementation + unit tests | **Not yet**; reconsider after corrected freeze and explicit approval |
| D0 | **Not yet**; prospective cap 0 updates, <=4 configs, <=15 minutes, debug20261111 |
| D1 | **Not approved**; prospective separate cap 4 updates, <=20 minutes, debug20261111 |
| Registered three-seed diagnostic | **Not approved**; prospective 12 units, <=1,200 updates, <=120 wall minutes, six CPU threads, no GPU/retry/extension |
| Combined prospective maximum | 1,204 updates /155 wall minutes **only if all stages separately approved**, not a grant |
| Actual training/evaluation compute used in this review | **None** |
| Phase6/B0-B/B1/B2/StageC | **No execution approval** |
| Test163 | **Sealed and unopened** |
| P1 / external APIs | **Unused and not proposed** |
| T5Gemma2 | **D-108 STOP remains closed** |

### Incorrect premises to avoid

- “Text mentions a residual” does not mean the residual has an executable, consistent oracle.
- M pass L is not L_SIGNAL; control PASS does not imply shuffled-memory L signal.
- “Same for full” is not harmless shorthand when the existing magnitude thresholds differ.
- A length-only preflight does not establish finite copy/full endpoints, and M15 is not val20.
- A hash's presence does not prove replay equality, and D0 does not establish registered runtime.
- Historical 54-test success is not fresh PM coverage; no tests were run here.
- Positive P0 contrasts at poor absolute CE do not establish trained P/PA/L, semantic content use, or permission for a later phase.

**Bottom line: NARROW to the four pre-result text repairs. Do not freeze unchanged r3.1, implement it, or run D0/D1/three-seed on the strength of this review.**