# Sol 6.1 medium reviewer — independent r3.2 external review

**Reviewer:** Sol 6.1 medium (`openai/gpt-6.1-sol`), independent review of unigem v0.2.1-r3.2.  
**Date:** 2026-11-09.  
**Final recommendation: NARROW — repair the remaining contract contradictions before freeze, implementation, or D0.** This is not a scientific STOP and is not approval of Phase 6 or B0-B.

## Review basis and limits

- Repository: `mandutt/unigem`, Hoplite project `proj_2e8de5ed594f47c7b851f1d7c5b52c61`.
- Ran `git fetch origin`, then `git pull --ff-only origin main`, in that order. Both succeeded; pull reported `Already up to date.`
- Resulting HEAD and fetched `origin/main`: **`6aac52f0c486f4137a47cf4e173be77e81975a80`**. The existing workspace branch is `hoplite/leukas-ed68aa97`; its HEAD equals `origin/main`. I did not switch branches. This is the review revision, rather than the older `44bbef6` mentioned in the request document.
- Read the full external review request and all seven subsequently requested artifacts: r3.2, r3.1, the r3.1 synthesis, M preflight JSON, P0 report, runner, and metric tests. Also inspected relevant inherited r3/r2/r1/v0.2 passages to resolve formula, statistics, and D0/D1 inheritance. The synthesis was treated as a list of claims to check, not as another model's answer to adopt. I did not read the prior individual review reports or call another model/subagent.
- Read-only verification used Git, text inspection, SHA-256, and Python standard-library arithmetic over the supplied preflight JSON. No project runner was imported or invoked. **No training, evaluation, model forward, generation, D0, D1, or test suite was run.** “54 tests pass” remains historical evidence, not a result of this review.
- Did not open test 163, raw corpus/split files, P1 data, or model/cache tensors. No external data/model APIs were used. The only repository-content write is this report.
- Citations below use **R32** = `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_2.md`, **R31** = the corresponding r3.1 document, **PF** = `reports/provenance/C5_b0a/m_cohort_preflight.json`, **Runner** = `runner/c5_mt5_lora_b0.py`, **Tests** = `eval/tests/test_c5_b0_metric.py`.

## Executive findings

The repair is substantial: the numeric full threshold is restored, fixtures 16–18 are now internally coherent, M_NORM has an explicit formula, preflight identity is genuine, small-N and validity tiers are stated, generation and overhead appear in the timing formula, and the B0-B tail bypass is removed. These are real improvements.

However, **the document is not yet a single executable contract**:

1. R32 §2.3 defines an L consensus operator, while §9.2 defines the same signal with false-dominant ANDn. They disagree on partially unknown inputs and can change the final signal label.
2. R32 §6.3 still repeats the impossible old “M pass L false + control PASS” fixture, notwithstanding the correct replacement in §6.2. The exact-output requirement cannot satisfy both.
3. Replay canonicalization does not yet specify an identity for all required CE values. The record has one CE but lacks a real/control discriminator, uses `doc_id` for sorting and `id` for storage, and leaves donor-level versus aggregate records unresolved. The checkpoint byte stream also needs exact framing, not just a list of ingredients.
4. D1's newly expanded ledger still needs an explicit mapping for the **initial fixed-prefix real/M CE scoring**, as distinct from constructing tensors and replaying scores, and an explanation of where its five-donor replay factor applies. This can be a small textual clarification, but should not be left to timing implementation after freeze.

The first two are direct contradictions, not preferences about implementation style. The latter two are bounded operational specifications, not requests for more experiments or different thresholds.

## Q1. Total factored contract

**Verdict: disagree** with “fully total/executable as written.”

**Evidence.** R32 §§3–5 do supply deterministic dispatches for separate validity, control, and signal axes. ANDn is false-dominant (§2.2); F9/F10 fix the tier-specific NA cases (§3.7); §5.5 explicitly gives small-N priority while retaining validity/control. These parts are usable.

But §2.3, lines 81–83, defines `l_signal=false` only when **both** endpoint signals are false. §9.2, line 632, instead says `L_SIGNAL = ANDn(...)`. Consider:

| L copy | L full | §2.3 consensus | §9.2 ANDn |
|---|---|---|---|
| true | false | NA | false |
| false | NA | NA | false |
| NA | false | NA | false |

For `validity=VALID`, `n_signal=20`, `control=M_CONTROL_PASS`, copy=false/full=NA, both `copy_only` and `full_only` are not true. The §2.3 route reaches `NOT_ASSESSABLE`; the §9.2 route reaches `MEAN_CONTRAST_ONLY` (§5.3). Thus this is observable, not merely a naming inconsistency. Also, §6.3's impossible named cell conflicts with §6.4's requirement that every named cell have its exact output.

**Next steps.**
1. Give the dispatch input one authoritative definition: preserve the inherited §2.3 consensus semantics and either remove the §9.2 alias or give the raw ANDn conjunction a distinct name that is not substituted into dispatch. This does not alter the numerical endpoint thresholds.
2. Specify the expected outputs for all nine copy/full tri-state pairs, including false+NA, and retain the existing per-axis/named-cell strategy.
3. Keep the validity/control/signal triple and reasons mandatory, including small-N and NA cases.

## Q2. L predicates and fixtures

**Verdict: conditional.** The numeric threshold regression and §6.2 fixtures are repaired; closure throughout the document is incomplete.

**Evidence.** R32 §9.2 explicitly sets copy mean `>= .05`, full mean `> 0`, both CI lower bounds `> 0`, paired per-document L−F means `> 0`, and at least two of three arm-L shuffled-minus-real seed means `> 0`. This matches the inherited v0.2 §6.2 thresholds; `.05` must not be applied to full. The clarification that seed means are not L−F is valuable.

R32 §6.2 now derives fixture 16 from both L signals true and `m_pass_l=true`; fixture 17 from both L signals false and `m_pass_l=true`; fixture 18 from both false and `m_pass_l=false`. With the supplied validity/control prerequisites, their labels are correct.

Nevertheless, §6.3 lines 467–468 still says “M pass L true + control PASS → EXPLORATORY” and “M pass L false + control PASS → MEAN_CONTRAST_ONLY.” In the latter, §4.3 requires `m_pass_l=true` to return PASS, so the premise is impossible. In the former, the L signal/validity/N prerequisites are again absent, and `EXPLORATORY` is not the exact enum `EXPLORATORY_L_SIGNAL`.

**Next steps.**
1. Replace the last two §6.3 bullets with explicit references to fixtures 16–18, using their complete prerequisites and exact enums.
2. Retain the restored thresholds and require synthetic boundary tests: copy exactly .05, full exactly zero, full positive below .05, CI lower exactly zero, and two versus one positive seeds.
3. Resolve the signal-combiner conflict in Q1; do not claim all L contract regressions are closed solely because §9.2's numbers are correct.

## Q3. M preflight and cohort

**Verdict: agree**, as a length-based eligibility registration, not proof of model endpoint validity.

**Evidence.** Independently recomputed the PF content SHA-256:

`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`

It matches R32 §1.1. From PF's stored 20 train and 20 val hidden lengths, K=753 has **16** eligible train contributors and **15** eligible val targets; K=754 has **14** eligible val targets. Enumerating the stored lengths confirms 753 is the maximum K satisfying train contributors ≥10 and val targets ≥15. The 15 stored common IDs exactly equal the val IDs whose hidden lengths are ≥753. Native stored lengths are all 512. The secondary full-K list contains 11 eligible targets by its stored exclusions; I did not recompute that result from raw caches.

The separation of val20 signal and M15 control is appropriate (R32 §§5.1, 8.1). Zero margin is material: losing any required M endpoint cannot be repaired by dropping to 14 or replacing the target. PF is data-only and contains no CE, so “endpoint 15/15” is a future requirement, not an achieved result.

**Next steps.**
1. Bind the exact PF bytes, IDs, contributor rule, and prefix lengths into the frozen manifest.
2. Enforce 15/15 endpoint completeness independently of signal `n_signal`; fail M availability without cohort replacement if it is not met.
3. Restrict interpretation to `M_CONTROL_PREFIX753_COHORT15`; keep full-K 11/20 secondary and non-rescuing.

## Q4. M builder, M_NORM, endpoint identity, replay

**Verdict: conditional.** The mathematical builder is substantially executable; the endpoint serialization contract is not complete.

**Evidence.** R32 §8.3 now specifies

`M_NORM(t) = M_POS_MEAN * (||real_prefix_t||_F / ||M_POS_MEAN||_F)`.

Read literally, this is one train-only mean direction per arm/seed, with a different magnitude scalar for each target. Its finite, nonzero result has the target prefix's Frobenius norm. R32 §§4.1/8.2 check the mean and all 15 target norms, contributor count, and tensor finiteness. Seed-specific construction and seed-average-before-document-bootstrap are explicit (§8.6). The inherited R31 §8.4 and r3 §8.3 retain eval/no-grad construction and positionwise averaging. No target labels enter the mean.

There is a wording distinction worth recording: the required r3.1 synthesis requested a single target-set/global scalar, while R32 explicitly chooses per-target `t`. The older formula used `real_prefix` without a clear set aggregation. I do **not** treat the synthesis's interpretation as binding mathematics or claim that these alternatives are equivalent. R32 makes a defensible explicit choice before results. “No per-target matrix” should mean no independently estimated per-target **mean direction**, not that the resulting scaled tensor cannot vary by target. This remains a magnitude-dependent control, not a completely target-independent one.

R32 §8.4 requires 15×3×4×2 = **360 paired document/seed/arm/variant cells**, with both real/control and copy/full CE values. That is 1,440 CE scalars if real CE is repeated within each variant cell; deduplicating identical real references is fine only if explicit. §4.1's abbreviated endpoint definition mentions L/P/PA, while §8.4 includes F; the latter should be the authoritative schema.

R32 §10.6's single-CE replay record does not say how real versus control CE is identified. It sorts by `doc_id` but lists `id` as the stored field. If replay is donor-level, the five donors from §10.3 are not represented in its key; if donor-averaged, the aggregation and contributor identities are unspecified. These omissions prevent an unambiguous no-duplicate/no-missing check. The checkpoint stream lists name/dtype/shape/bytes but does not define field framing or encoding, so two otherwise conforming serializers can hash differently.

**Next steps.**
1. Freeze one record schema distinguishing real/control, copy/full, variant, arm, seed, document, and checkpoint/stage, with donor identity or an explicit aggregate definition as applicable. Reconcile F coverage across §§4.1 and 8.4 and state expected row counts.
2. Define exact checkpoint framing/encoding and replay JSON numeric/encoding rules, reject nonfinite CE, and require fixed expected hash vectors plus permutation/duplicate/missing-key tests before D0.
3. Keep separate-process CE replay at `atol=1e-5`, `rtol=1e-4`. Use CE hashes for integrity and state hashes for state identity; do not silently replace tolerant CE comparison with exact CE-hash equality. Bind the frozen base/config/mode identity in the manifest even though frozen weights are excluded from the trainable-state hash.

## Q5. PA

**Verdict: agree**, with the inherited interpretation caveat carried forward explicitly.

**Evidence.** R32 §7.2 calls PA native memory + random adapter + decoder LoRA an **acquisition control**, uses `PA_STEP100_NOT_VALID`, forbids `ADAPTER_REGIME_LOSS`, makes PA retention nullable/non-gating, and requires a separate PA step0. R31 §7.2 explicitly retains the scale/geometry caveat; omission of that sentence from R32 does not revoke it under the inheritance rule.

P0 is not PA step0: it has no random adapter. Nor do P0's large contrasts show successful learned P/PA/L selectivity. P0's source truncation is 256 rather than registered native M's 512 (R32 §12). The supplied P0 values—train +3.7617 with CI [1.8917, 5.6050], val +5.2375 with CI [2.5013, 8.0753]—are descriptive path sensitivity only. Val median 2.9739 and top-three share .4862 caution against a mean-only argument. Real CE 12.7022/13.2352 exceeding ln|V|≈12.43 also prevents interpreting positive contrasts as good absolute predictive quality.

**Next steps.**
1. Carry the scale/geometry caveat and acquisition language into implementation/report templates.
2. Test PA-specific step0, trainable parameter groups, initialization, encoder freezing, and mode policy; do not route PA through an F/L-only helper unchanged.
3. Keep retention descriptive and never use P0 or retention as a substitute for the registered P/PA validity and M calibration checks.

## Q6. Cap, D0, D1

**Verdict: conditional.** Arithmetic and authorization separation agree; timing completeness needs a final explicit mapping.

**Evidence.** R32 §10 correctly registers 4 arms×3 seeds×100 = **1,200 updates**, 120 minutes, six CPU threads, no GPU, no retries. D0 is zero updates, ≤4 configurations, ≤15 minutes. D1 is four arm-seeds×one update = four updates, shared debug seed 20261111, ≤20 minutes, separately approved. Thus the prospective, separately approved aggregate is **1,204 updates / 155 minutes**, not a present grant.

The new projection correctly multiplies only training by 100, and the complete per-arm sum by three seeds. Generation 20×256, the 20-train mean build, donors, variants, and overhead now appear. Missing phases prohibit projection; the launch screen is ≤96 minutes, not a new 96-minute or 155-minute execution allowance.

Residual ambiguity: §10.3 phase 4 says “M builder 20 train + 15 target×2 variants,” not explicitly fixed-prefix **real and M CE scoring**. Constructing a target-scaled tensor is not scoring it. Phase 6 says replay 15×5 donors×2 variants, although M primary real/mean contrasts use fixed prefixes rather than donor cropping. It is possible these terms intend to include everything; they need an explicit operation-to-phase mapping before a builder-only timing can be ruled out. This is not evidence that actual runtime exceeds the cap—no timing was run.

**Next steps.**
1. State which phase contains initial fixed-prefix real/M_POS/M_NORM CE scoring, including full/copy outputs, and which endpoints are replayed. Distinguish shuffled donor work from donor-free primary M work; preserve the inherited fixed-prefix M real reference.
2. Keep the seven-phase ledger but require its logged counts to reconcile to the frozen endpoint schema and all registered work, including secondary work if retained; do not omit work merely because it is non-gating.
3. After separate approval only, measure D1, require finite nonnegative components and `T_proj≤96`, and retain the 120-minute registered hard abort, no retry/extension. No D0-derived projection.

## Q7. Statistics

**Verdict: conditional.** Most statistical rules are executable, but not all consumers have an authoritative definition.

**Evidence.** R32 §9 fixes 1,000 document bootstrap samples, percentile 2.5/97.5 CI, bootstrap seed 20261109, and seed averaging before bootstrap. It distinguishes `documents_positive` from `seeds_positive`, defines the seed means, and pairs L−F by document. F/L×three seeds×copy/full intersection membership prevents partial-seed pooling. N ranges 0–20 or NA; N=15 is marginal without silently changing the threshold.

The inherited R31 §9.2 criterion is `leave_top3_mean<=0 OR top3_share>.50`. R32 §9.4 adds tri-state handling: any known positive criterion → true; both known false → false; otherwise NA. Zero denominator and N<4 produce null statistics; signed shares are not clipped to [0,1]. These are useful repairs. Numerical undefinedness must propagate as unknown, not Python false. The raw L consensus conflict in Q1 still prevents an end-to-end executable result.

The existing Runner helper at lines 384–397 uses seed **20261108** and labels a count of positive documents `seeds_positive`. R32 correctly prohibits reusing that helper unchanged. Existing Tests cover same-position loss, copy mask, modes, donor matching, and descriptive P0 decisions—not the new PM decision/statistics contract. The whole test class is also skipped when the local model is absent (Tests line 13), so future pure tests must not inherit that model dependency.

**Next steps.**
1. Resolve Q1 and implement the new PM statistics module with synthetic, model-independent tests for seed averaging, shared IDs, pairing, and 2-of-3 counts.
2. Freeze the exact input contrast/cohort/endpoint consumed by the singular launch `tail_driven` flag; show any endpoint-specific diagnostics separately rather than allowing an implementation to choose a favorable endpoint. Preserve the inherited .50 and zero boundaries.
3. Test zero sums, small N, known-false plus unknown, known-true plus unknown, missing seeds, and nonfinite CE; retain excluded-ID reasons and never convert NA to false.

## Q8. Remaining Must-fix

**Verdict: agree** that a narrow residual repair is necessary; disagree with the unconditional “closed” entries in R32 §15.

**Evidence.** R32 §15 declares closure, but §§2.3/9.2, §6.3, §10.6, and §10.3 retain the specific conflicts or under-specifications demonstrated in Q1, Q2, Q4, and Q6.

**Ranked list before freeze/implementation:**

1. **MF-1 — authoritative L signal semantics.** Resolve §2.3 versus §9.2 without changing the restored endpoint thresholds. Evidence/counterexample: Q1. This is the most important newly explicit contradiction in r3.2.
2. **MF-2 — remove contradictory named fixtures.** §6.2 is repaired, but §6.3 still requires an impossible control-PASS/m_pass_l=false cell and an inexact label. Evidence: Q2. This is an r3.1 blocker incompletely removed, not a request for more outcomes.
3. **MF-3 — complete endpoint/replay and canonical byte contracts.** Resolve `id`/`doc_id`, real/control identity, donor versus aggregate granularity, exact framing, and row coverage. Evidence: Q4. Include an explicit tail input mapping because it now controls launch eligibility (Q7). Canonicalization has a mechanism but is not yet a uniquely specified wire format.
4. **MF-4 — close the timing ledger mapping.** Explicitly include initial primary M CE scoring and reconcile donor multiplicity/replay with the endpoint schema. Evidence: Q6. The generation and 20-train-build omissions themselves are repaired.

**Not additional freeze blockers:** numeric L thresholds, the corrected §6.2 fixtures considered alone, PF content hash/K selection, PA naming, small-N precedence, F9/F10, and the B0-B `tail_driven=false` requirement. M_NORM's explicit per-target scalar is acceptable if described accurately; it must not be represented as the synthesis's different global-scalar interpretation. R32 §15's reference to “§1.4” for the content hash is a minor stale reference; the actual definition is §1.1.

**Next steps.**
1. Prepare a text-only r3.3 limited to MF-1–MF-4, consistent with R32 §16; keep all thresholds/seeds/donors/steps/LRs frozen in meaning before results.
2. Replace blanket closure claims with the actual contract references and exact expected cases.
3. Recheck the revised contract before granting implementation/D0; no new experiment is needed to resolve these issues.

## Q9. Freeze and implementation approval

**Verdict: disagree** with freezing r3.2 as-is or approving implementation plus D0 now.

**Evidence.** Two contradictory normative L definitions and an unreachable required fixture cannot both pass a correct implementation. R32 §§0/16 explicitly require contract freeze before code; bypassing that sequence would transfer scientific interpretation choices to the implementer. The existing code only exposes F/L plus P0 and does not implement the PM protocol (Runner CLI lines 753–798). Historical metric tests do not satisfy the new DoD.

**Next steps.**
1. Close MF-1–MF-4 in text and freeze the accepted protocol revision/commit, with the inherited documents identified.
2. Then separately authorize implementation and synthetic unit tests. Mandatory contract tests: all nine L pairs; false-dominant ANDn 2/4/5; validity F1–F11; fully expanded fixtures 16–18; no unreachable required enums; M formula/norm/contributor/leakage checks; exact endpoint membership; hash vectors; replay tolerance; statistics and tail NA cases; P/PA initialization/modes; approval/cap accounting.
3. Only after those pass, consider D0: four configs maximum, zero optimizer updates, ≤15 minutes, seed 20261111, `labels_computed:false`, `not_a_result:true`. Here “labels” means outcome/decision labels; D0 may exercise the inherited mechanics, not produce scientific results. This review did not execute or presently authorize D0.

## Q10. D1 versus three-seed launch

**Verdict: conditional.** The approval boundary is sound, but checklist evidence must be made unambiguous.

**Evidence.** R32 §§10–11 require a separately approved D1, debug seed outside registered 20261108/09/10, complete timing, ≤96-minute projection, freeze/code hashes, unit tests, D0 evidence, preflight hash, debug replay hash, post-run final hash validation plan, and explicit user approval. Final trained hashes are correctly not demanded before training. No trained P/PA/M evidence is an appropriate prelaunch requirement.

What remains missing in executable form is a versioned authoritative signal decision, exact replay/endpoint row counts, and a timed-work-to-endpoint reconciliation. These are MF-1–MF-4, not grounds to demand favorable scientific outcomes during debug. A debug hash proves bytes existed, not replay correctness by itself.

**Next steps.**
1. Add checklist references to the accepted operator/schema versions, MF-1–MF-4 tests, actual replay comparison report, and the complete operation-count ledger.
2. Require same approved configuration, six-thread CPU policy, and a hard cap watchdog/abort policy in the eventual implementation; no extension or retry after a miss. Record actual D1 elapsed time separately from projected registered time.
3. Keep D1 approval and three-seed approval separate. D1 failure, missing phase, or projection above 96 minutes means no three-seed launch under this registration—not a license to alter steps/LR/donors after results.

## Q11. B0-B boundary

**Verdict: agree** with the hard boundary, subject to implementing the earlier definitions correctly.

**Evidence.** R32 §14 removes “or explicitly reported,” excludes both true and NA tail flags, and requires separate preregistration/approval. Restated eligibility is:

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid == true
AND n_signal >= 15
AND tail_driven == false
AND leakage/mode/metric checks pass
AND required artifacts are complete
AND separate B0-B preregistration and explicit approval exist
```

This is a conjunction of requirements, **not an authorization to launch**. M scope remains `M_CONTROL_PREFIX753_COHORT15`; full-K 11/20, P0 positivity, and PA retention cannot substitute. A positive r3.2 result does not authorize B0-B/B1/B2/Stage C. The undefined-tail bypass is closed at the text level.

**Next steps.**
1. Preserve this exact fail-closed boundary and test true/NA/false tails plus missing-artifact and missing-approval cases.
2. Resolve the input/schema issues above so “false” cannot come from silently missing data or a favorable endpoint selection.
3. Require separate review and user authorization for any future stage; do not infer permission from `EXPLORATORY_L_SIGNAL`.

## Q12. Final verdict and scope

**Verdict: conditional — NARROW.** Continue only with the bounded text repair/review process, not experimental execution.

**Evidence.** The preflight is consistent and the design is scientifically worth preserving; no evidence justifies reopening model families or stopping the entire line of inquiry. But the concrete conflicts in Q1/Q2 preclude calling this version freeze-ready, and Q4/Q6 leave operational choices open. R32 §16 itself prescribes a Must-fix-only r3.3 if review again yields NARROW.

**Next steps.**
1. Repair and independently check MF-1–MF-4 before freeze; do not change numerical thresholds, registered seeds, donors, steps, or LR in response to outcomes.
2. Seek staged approval for implementation/unit tests, then D0, then D1, then the registered run; do not collapse these gates.
3. Maintain all sealed-data/model/stage prohibitions and report incomplete evidence as incomplete.

### Approval matrix and compute

| Item | This review's recommendation |
|---|---|
| r3.2 freeze as-is | **No** |
| Text-only Must-fix repair/review | **Yes, recommended next; not performed here** |
| Implementation + unit tests | **Not approved now; after corrected freeze and authorization** |
| D0 | **Not approved now**; prospective ≤4 configs, 0 updates, ≤15 min, seed 20261111 |
| D1 | **Not approved**; future separate approval, four total updates, ≤20 min, seed 20261111, no outcome labels |
| Registered three-seed run / Phase 6 | **Not approved**; future separate gate and explicit approval |
| B0-B/B1/B2/Stage C | **Not approved; no automatic progression** |
| T5Gemma2 | **D-108 STOP unchanged** |
| test 163 | **Sealed; neither opened nor authorized** |
| P1 / external data or model APIs | **Not used or proposed** |

**Maximum compute authorized by this consultation: zero training/evaluation/debug runs.** Prospective limits, only if separately authorized later: registered 12×100 = 1,200 updates / 120 minutes, six CPU threads, no GPU/retry; D0 0 updates / 15 minutes; D1 four updates / 20 minutes. Combined prospective maximum **1,204 updates / 155 minutes is not a grant**. A valid D1 projection ≤96 minutes is a necessary launch screen, not evidence that timing has passed.

### Incorrect premises to avoid

- Restored numbers do not resolve the two different L logical operators.
- Correct §6.2 fixtures do not erase contradictory normative §6.3 bullets.
- PF length eligibility is not observed 15/15 finite copy/full CE completeness.
- A common mean direction with per-target scaling is not one numerically identical control tensor for every target, nor a target-independent control.
- A canonical key list is not yet a uniquely framed serializer; exact CE hashes are not equivalent to tolerant CE replay.
- Expanded phase names do not prove a measured, fully reconciled D1 workload or a passed cap screen.
- Positive P0 contrasts and historical 54 tests do not establish trained PM validity, successful new unit tests, or authorization of later phases.

**Final: NARROW. No Phase 6 or B0-B approval.**