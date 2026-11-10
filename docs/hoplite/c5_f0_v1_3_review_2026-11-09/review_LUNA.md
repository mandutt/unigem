# Independent review — C5 F0 v1.3 (new block, round 3/10)

**Reviewed HEAD:** `f5cc44b1bbe733523a3c66913eb5a719ebaa5872`

**Synchronization:** `git fetch origin` and `git pull --ff-only origin main` both succeeded; pull reported “Already up to date.”

**Review status:** v1.3 is still a draft and is marked unapproved/unrun. This is a design review only; no training, evaluation, test-163/P1 access, or experiment was performed.

## Verbatim paired E01−E11 definition

The v1.3 plan’s paired contrast is quoted exactly from §6.3:

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
```

There are **no realized E01/E11 pairs or observed `mean_D`/`CI_D` values**: the review request and plan both say F0 is unapproved and unrun. Do not substitute the historical P−PA or F−L contrasts for E01−E11.

## Q1. Initialization, serialization, and pre-R audit

- **Verdict: disagree — approval blocker.** The intended controls are materially stronger, but the new pre-R stage cannot satisfy its own stated audit and is not explicitly wired as a Stage R prerequisite.
- **Evidence:** §4 items 4–5 and 9 require `post_step0_rng_state_sha256` and a changed trainable-group hash; §13A.3 likewise requires first-update changes in E10/E01/E11. Yet §13A.1 defines stage P as **no updates** and says it records **all §4 assertions**. A zero-update audit cannot establish post-update RNG/weight-change assertions. Separately, §5 Stage R says to start after D0/D1 mechanics pass (§5, Stage R bullets), but does not require `pre_r_init_audit_pass:true` from §13A.1.
- **Conflicting non-reuse rules:** §4 says the Phase 6 path audit (zero Phase 6 checkpoint opens) replaces the untestable `F0 E11 ≠ Phase 6 L` assertion (§4, item 118). §13A.1 reintroduces the E11-vs-L hash inequality, and §13A.6 requires both init and final hashes to differ while calling the I/O audit secondary (§13A.6, items 451–452). These compare unspecified hash objects and contradict §4’s stated authority. An inequality between differently defined digests is not evidence that a Phase 6 checkpoint was not read.
- **Serialization is not yet a frozen oracle:** §13A.2 gives useful framing (`u32le` name length, `u8` dtype length, `u8` ndim, `u32le` dimensions, `u64le` byte length), but says expected vector hashes are included in `init_hashes.json` (§13A.2, 411–416). That makes the run artifact, rather than a pre-committed fixture, the apparent authority for the expected digest. Canonical dtype spellings and payload normalization also need to be fixed for the supported tensors.
- **Next steps:** Split stage P’s init-only assertions from post-update assertions; make a passing P artifact a hard Stage R gate; choose one authoritative Phase 6 non-access check and specify its complete read-path coverage; commit independent serialization fixtures and expected digests before D0. Keep first-update checks in an update-capable mechanics stage, not in a zero-update audit.

## Q2. D1 literal schema and seal

- **Verdict: conditional — not yet an approval gate.** The direction is good: v1.3 rejects the Phase 6 `eval_arm_d1` path, prohibits wrong-donor CE and donor-map loads, requires digest-then-delete checkpoints, and forbids persisted signal-shaped fields (§5 D1, §11, §13A.4). Those are the right separation goals.
- **Evidence of what must not be reused:** the current Phase 6 runner’s `eval_arm_d1` computes both real- and wrong-donor losses (`runner/c5_pm_phase6.py:429–470`); `run_d1` calls it before and after the update and writes phase-7/checkpoint and other artifacts (`runner/c5_pm_phase6.py:778–882`). The dedicated F0 mechanics evaluator required by §11 is therefore necessary. At this reviewed HEAD, the Phase 6 CLI does include `registered` in its mode choices (`runner/c5_pm_phase6.py:946–964`); that current source, not an older synthesis statement about the CLI, is the relevant evidence. It is still not an F0 implementation: §11 says the new F0 code is not implemented (§11, 343–355).
- **Schema gap:** §13A.4 lists only field types for several critical values. `cells` does not state exact per-cell expected `updates`/parameter counts; `checkpoint_digests` does not enumerate its exact keys or SHA-256 format; and `mechanics_pass` is not defined as a conjunction of the listed assertions. The normal and crash/partial forms are not distinguished even though §13A.4 requires `partial:true` plus `error` on a crash while the rest of the schema uses concrete types. The D1 stage does state expected counts—120 M records/cell (480 total), 0 phase-7 records, and 20 generations/cell (80 total)—but these must be executable schema predicates, not merely prose (§5 D1, items 4–9). The explicit zero wrong-donor CE / zero donor-map loads are good and must remain hard assertions.
- **Next steps:** Freeze two exact schemas (complete success and partial failure), with `additionalProperties:false`, literal cell/digest keys, exact counts and parameter counts, strict JSON types, and a precise `mechanics_pass` predicate. Require the writer, consumer, and filesystem inventory to reject extra keys/files, `d1_report.json`, `d1_sealed/`, persisted `per_doc`/`delta_*`/`signal`/phase-7 payloads, or any surviving/loadable D1 checkpoint. Preserve the planned negative tests.

## Q3. STOP taxonomy, MDE proxy, and P−PA

- **Verdict: agree on the state logic; conditional on the proxy wording.** The primary is a positive paired E01−E11 contrast plus E01 absolute copy signal and a 2/3 seed-sign gate (§6.3). `EQUIVALENT` is a CI wholly inside `[-.05,+.05]`; `harm` and `benefit` are defined from the paired CI; then the ordered states are NOT_EVALUABLE, PASS_POSITIVE, ROUTE_STOP, INDETERMINATE (§6.5–§7). Given a finite ordered CI, PASS and EQUIVALENT do not overlap, and the four states are exhaustive. `ALL_FAIL` is correctly limited to E01/E11 × copy/full; ROUTE_STOP is route-only (§7, 277–307; §14, 468–472).
- **MDE correction is mostly sound:** `.019170 = .037573/1.96` is explicitly identified as an F−L paired-SE planning proxy and not an E01−E11 SE; `.104` is gate-only 80% power, `.0876` an analytic 50% boundary, and neither is presented as an observed F0 mean (§12, 372). Let realized `CI_D` govern the labels. Retain the assumptions/calculation alongside those planning-only numbers so they cannot be mistaken for F0 power or a forecast.
- **P−PA is not an E01−E11 variance bound:** v1.3 cites mean `+3.0652`, SE `0.6209`, 14/15 positive, per-doc SD `2.405` (§0, 20–23; §12, 372). The cause report describes the historical native-path P−PA contrast as `+3.065`, 14/15 positive, with P copy Δ `3.076` versus PA `0.011` (§2, 53–60). The Phase 6 review synthesis also notes P/PA differ in capacity (+526,336 parameters) and adapter LR (10×), so they are not a clean adapter-only isolation (§3, MF-4, 70–80). This is useful historical dispersion/context, but calling it an **“upper bound”** for F0/E01−E11 is unsupported; call it a comparator unless an actual bound is justified. It does not resolve the F0 branch.
- **Next steps:** Keep the four-state ordering and exact thresholds frozen. Rename P−PA “upper bound” to “historical comparator” (or prove the bound pre-run), and state that all proxy power values are assumption-dependent planning quantities only.

## Q4. Cohort and donor count

- **Verdict: conditional.** The cohort is adequately fixed for a narrowly scoped 15-document, fixed-donor-graph diagnostic: the 15 `common_ids` are frozen and length-selected, 20-doc results are descriptive only, each document must have exactly five donors, donor sets must match across all four cells, and all 15 documents/three seeds are required (§6.1, 190–200; §6.6, 252–257; §7, 261–272). The plan correctly forbids generalization to the 20-document validation population (§6.1, 191–195). `n_boot=10000` is an explicit override, which matters because the frozen Phase 6 stats default is `N_BOOT=1000` (`runner/c5_pm_stats.py:15,29–71`; F0 plan §6.3, 219).
- **Remaining inferential issue:** `bootstrap_paired_v2` resamples document-level values with replacement (`runner/c5_pm_stats.py:34–39,55–61`). Donors are reused from `val20` and that reuse is declared (§6.1, 194–195), so target-document deltas can share donor units. The planned leave-one-donor-out **range** is useful sensitivity analysis, but is not itself a donor-cluster-adjusted CI. Since `CI_D` drives PASS/EQUIVALENT/harm/benefit, specify whether that interval is conditional on the fixed donor graph and strictly an assay decision statistic, or preregister an inference procedure that accounts for the shared donor clusters. Do not call it population-level uncertainty under the current dependence structure.
- **Next steps:** Preserve the 15-doc/3-seed/5-donor completeness assertions and no-substitution rule. Before R, freeze the donor-dependence interpretation of `CI_D` and the role of leave-one-donor-out results; do not decide this after seeing outcomes.

## Q5. Compute projection and execution host

- **Verdict: disagree — the caps are not yet supported by the specified F0 D1 measurements.** The v1.3 formula has nine addends inside the 3-wave sum—step-0 eval, 100 training steps, 20×5 step-100 eval, M build, M CE, phase-7 replay, primary replay, generation, and overhead—plus `setup_s` outside the sum (§12, 365–374). It also correctly keeps D1/R parallel, requires `nproc>=12`, sets D1 ≤25 min and R ≤96 min, and declines the current four-vCPU host (§12, 369–374; §13A.7, 454–457).
- **Projection hole:** F0 D1 is expressly mechanics-only: `wrong_donor_ce_calls == 0`, `phase7_records == 0`, and no signal is materialized (§5 D1, 155–170; §13A.4, 431–442). Therefore the prescribed F0 D1 cannot directly time the 20×5 donor evaluation, phase-7 replay, or primary replay terms needed for R. “T_proj analog from D1 per-phase timing” (§12, 374) does not supply measurements for work that D1 forbids. Phase 6’s historical parallel D1 time of 1,180.6 s and sequential scratch time of 3,116.5 s (§12, 365) are not, without a stated mapping, measurements of this F0 workload on the qualifying host.
- **Accounting ambiguity:** the formula counts `setup_s` once, while §12 says setup is per-process/per-wave and may be 4× per wave if per-worktree; it does not define the measured arm aggregation (max/parallel wall versus sum of per-arm times). Stage P time is said to count in D0/compute but has no explicit cap or inclusion rule (§13A.1, 403–406). These can materially change a 96-minute cap.
- **Next steps:** Before the D1 gate, specify a non-signal timing method or a justified prior timing source for every R-only evaluation term; define per-arm parallel aggregation, contention, setup count across 4 processes × 3 waves, and the P-stage budget. Put that accounting in the committed orchestrator and compute `T_proj_R` from its recorded timings. Until then, neither 25 nor 96 minutes is demonstrated by the proposed mechanics-only D1.

## Q6. Scope and route-only consequence

- **Verdict: agree.** H3 arms/triggers/endpoints are removed, require a separate prereg and approval, and cannot be auto-launched by F0 (§10, 335–341). The causal description is properly limited to `adapter-as-configured` (parameters, LR, and adapter-conditioned graph) rather than an architecture-only bottleneck (§4, 121; §14, 468). ROUTE_STOP applies only to this configured EG2/LoRA route, not the whole EG2 track or B0-B; the dropped zero/permuted null and one-seed controls are explicitly not claimed as replaced (§14, 461–472). M_PASS is not donor-specific evidence (§9, 328–330). Keep test 163/P1 and all other tracks outside this review and experiment.
- **Next steps:** Preserve these boundaries verbatim in the gate output and final report; no result should automatically start H3 or broaden the claim.

## Final verdict and ranked must-fix

**NARROW — F0 v1.3 is not approved for D0, D1, or R as written.** This is a repairable prereg/specification decision, not a STOP of the EG2 track. The design has a coherent narrow estimand and improved decision taxonomy, but the pre-R audit is internally impossible, its gate is not connected to R, the D1 schema is not fully literal, donor dependence is unresolved for a CI-based gate, and the proposed D1 cannot produce several R projection timings. No experiment is authorized by this review.

1. **Blocker — reconcile Q1:** make P init-only or change its scope; separate post-update checks; require `pre_r_init_audit_pass:true` before R; resolve the conflicting Phase 6 hash-inequality vs no-open rule.
2. **Blocker — freeze hash proof:** commit canonical tensor/dtype/payload rules and independent known-answer vectors before D0; make zero Phase 6 checkpoint reads the authoritative non-reuse gate.
3. **Blocker — make D1 schema executable:** exact success/partial schemas, per-cell expected values/counts, strict writer and consumer allowlists, crash cleanup, and filesystem/negative tests.
4. **Blocker — define CI dependence:** either make `CI_D` explicitly conditional on the fixed donor graph and limit its interpretation, or preregister donor-cluster-aware uncertainty before R.
5. **Blocker — repair compute evidence:** safely measure or justify all R-only timings; define setup and concurrent-arm aggregation across waves; cap/budget stage P; retain `nproc>=12` and no-run-on-4-vCPU rule.
6. **Clarification — correct proxy label:** do not call P−PA an F0 upper bound; retain `.019170`, `.104`, `.0876`, and P−PA values only as explicitly non-transferable planning/context statistics.

**Not run:** tests, training, evaluation, test 163/P1 access, or any stage of F0, as required for this consultation-only review.