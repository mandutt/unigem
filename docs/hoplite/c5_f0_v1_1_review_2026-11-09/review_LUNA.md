# C5 F0 v1.1 — Independent Review (Round 1/10)

- Reviewed HEAD: `af0fa3ec374ab5cb20c9823485c78f2bd47c45d2`
- Synchronization: `git fetch origin` succeeded; `git pull --ff-only origin main` succeeded (“Already up to date.”).
- Target: `docs/plan_c5_f0_v1_1_2026-11-09.md`, DRAFT, unapproved and unexecuted.
- Verdict: **NARROW — do not approve D0, D1, or R as written.** The design has materially bounded its claim and resolved much of v1.0’s ambiguity, but the items below remain preregistration/implementation blockers. No F0 training/evaluation or test 163/P1 access was performed; the F0 runner was not executed.

## Verbatim paired E01−E11

The registered contrast is, verbatim from v1.1 §2 and §6.3:

> Primary: **E01 vs E11** (LoRA initialization matched).

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
```

And §6.3 states: “`D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.” These are preregistered definitions, not observed results: F0 remains unrun.

## Q1. Initialization

- **判定: conditional — not sufficient as written.**
- **Evidence:** v1.1 §4 specifies separate F0 construction, adapter-independent LoRA reseeding, per-step seed reset, E01/E11 LoRA-name and init-hash equality, E10/E11 adapter-hash equality, RNG-state hashes, and common base/cache/label hashes (lines 84–117). The v1.1 change summary additionally claims “post-step0 weight non-equality” (line 36), but §4 has no post-update parameter hash or non-equality assertion; its “post_step0” assertion is only RNG-state equality (line 109). D1 checks one optimizer update and finite CE (lines 143–155), which does not establish that the intended trainable weights changed.
- **Serialization gap:** `sha256(lora_A/lora_B)`, `sha256(adapter)`, and RNG-state hashes are named but their tensor/RNG byte encodings are not defined. The canonical digest at §4 line 113 specifies how hash *strings* are combined, not how tensor or RNG state bytes are serialized. Phase 6 prereg §12.1 (lines 1366–1400) demonstrates the missing state-hash contract: sorted keys plus dtype, shape, byte order, and contiguous tensor bytes.
- **Next steps:** (1) Pin deterministic tensor and CPU/CUDA RNG serialization and independent golden vectors; reuse the Phase 6 tensor framing where appropriate. (2) Capture pre-update and post-first-update hashes and assert the expected trainable parameter groups changed for E10/E01/E11, including the D1 debug seed and all three registered seeds. (3) Keep the initialization-equality checks separate from post-training non-equality checks.

## Q2. D1 artifact seal

- **판정: conditional — the direction is right, but the artifact boundary is not yet fully specified.**
- **Evidence:** v1.1 §§0, 5, and 11 require a separate mechanics evaluator, prohibit reuse of `eval_arm_d1`, make the mechanics JSON the sole durable D1 result, and require checkpoint digest-then-delete (lines 19–23, 139–168, 338–350). This directly addresses the v1.0 synthesis blocker (§3, lines 36–41). It is necessary: the current Phase 6 `eval_arm_d1` materializes `per_doc` and `delta_shuffled_*` (runner lines 429–489); `run_d1` writes step0/final records, M records, phase-7 records, generations, checkpoints, and a partial report (lines 804–858).
- **Remaining bypass/ambiguity:** v1.1 says “exact-key allowlist” but does not enumerate the allowed keys or the complete allowed D1 filesystem paths. It asserts `phase7 records == 0` (§5 line 151), which is a logical count, not the phase-7 filesystem-absence assertion claimed in §0 line 22. Checkpoint absence is specified (§5 line 154), but a corresponding explicit path/tree absence assertion for phase-7 output and other temporary/partial artifacts is not. The negative test names `d1_report.json`, `per_doc`, and `delta_*` (§5 line 162), not every unallowlisted writer output. There is also a path-name mismatch: §5 line 180 reads `d1_mechanics.json`, while §13 line 378 lists `d1/f0_d1_mechanics.json`.
- **Next steps:** (1) Enumerate the exact allowed D1 JSON keys and durable/transient paths (including timing/provenance fields); assert exact-key equality and reject every other file/key. (2) After digesting the temporary checkpoint, assert its absence and assert the D1 phase-7 directory/files are absent; include partials, symlinks, and writer-created files in the audit. (3) Add negative tests for unexpected outputs and confirm the F0 implementation never calls Phase 6 `eval_arm_d1` or writes signal/generation content to files or logs before D1 approval.

## Q3. STOP/MDE

- **판정: conditional — the state machine is mostly coherent; the MDE/power statement is not.**
- **Taxonomy:** v1.1 §7 defines four exhaustive, ordered outcomes after `PROTOCOL_VALID` (lines 254–303). `PASS_POSITIVE` requires the copy-primary lower bound (>+.05), E01 copy signal, and 2/3 positive seed contrasts; `EQUIVALENT` is a CI wholly within ±.05. Those conditions do not overlap. `ALL_FAIL` is explicitly E01/E11 × copy/full, and `ROUTE_STOP` is route-only. The reason precedence is understandable. Clarify in the output that `adapter_benefit` under `ALL_FAIL` means a relative contrast favoring E11 while neither primary cell passed its absolute signal criteria; it is not a positive route recommendation.
- **Blocking arithmetic:** With the stated SE .019170, a normal 95% half-width is (1.96 	imes .019170 = .03757). Thus .0876 is approximately the *observed sample mean* at which the lower bound is .05; because the gate is strict, the observed mean must be just above it. It is not an 80%-power target. For 80% probability of crossing a 95% lower-bound gate at .05, the normal approximation is (.05 + (1.96 + .842)	imes .019170 approx .1037), before the additional E01-signal and 2/3-seed gates. A true effect of .0876 would yield only about 50% probability of clearing the lower-bound gate under that approximation. The stated .054 is approximately ( (1.96+.842)	imes SE), i.e. a detectable increment above zero, not above the registered +.05 lower-bound threshold.
- **Provenance:** v1.1 §12 gives .019170/.037573/.054/.0876 (lines 360–370), but the reviewed supporting sources do not reproduce a derivation tying that SE to the planned EG2 E01−E11 estimand. Phase 6 cause report §3 (lines 45–60) describes F−L as a LoRA contrast with adapter present, and P−PA as an adapter contrast on the native path; neither is the planned EG2 adapter contrast. Do not present a surrogate SE as an established F0 variance without labeling and justifying that transfer.
- **Next steps:** (1) Recompute or relabel the power/MDE statements for the actual `CI_D.lower > .05` decision, explicitly accounting for the joint signal/seed gates; state the approximation and SE source. (2) If .019170 is only a planning surrogate, say so and do not call .054 the 80% MDE for PASS. (3) Retain the four-state precedence, with the route-only reason wording made explicit.

## Q4. Cohort

- **判定: conditional — the restricted estimand is defensible, but the dependency sensitivity is underspecified.**
- **Evidence:** v1.1 §6.1–6.3 fixes the primary to 15 length-eligible common IDs, requires all 15 across cells/seeds, forbids substitution, requires exactly five identical donor sets per document, averages seeds before a doc-level paired bootstrap, and makes 20-doc values descriptive only (lines 184–220, 247–252). It explicitly disclaims generalization to the 20-doc population (§6.1 lines 187–190). This is a meaningful improvement over the selection concern recorded in v1.0 synthesis §3 (lines 43–47).
- **Remaining gap:** donor reuse is acknowledged, but “donor-cluster sensitivity” is only promised (§0 line 27; §6.1 line 190). No resampling/leave-cluster-out method, cluster unit, or precommitted rule for what happens if the sensitivity conflicts with the document bootstrap is stated. Because donor nodes are reused across documents, the method must not leave that decision to post-result judgment. Bind the exact frozen IDs/graph in F0 artifacts: Phase 6 prereg §0.4 names `reports/provenance/C5_b0a/m_cohort_preflight.json` with content SHA-256 `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`; §2.5.6 (lines 276–299) gives the deterministic nearest-length donor rule. v1.1’s generic input-SHA field (§11 line 347) should identify these inputs explicitly.
- **Next steps:** (1) Bind the preflight content hash, 15 IDs, donor map/rule, and source/cache hashes in the prereg and each applicable artifact. (2) Define donor-cluster sensitivity and its interpretation before results; state whether it is a robustness gate or diagnostic and constrain any label/claim accordingly. (3) Preserve the stated finite-cohort scope—no population generalization.

## Q5. Compute

- **判定: conditional — the cap plan is acceptable in outline, but remains a hard pre-run gate.**
- **Evidence:** v1.1 §§11–12 separates `t_proj_f0`, requires four-arm parallel execution with 3 threads/arm (12 logical threads), sets D1 ≤25 min and R ≤96 min, includes R-only phase-7/primary replay terms, records `nproc` and `contention_ratio`, and hard-aborts below 12 processes or above the R cap (lines 338–370). It also requires an F0-specific implementation commit with clean tree and SHA before D0 and separate D0/D1/R approvals (§11 lines 341–350); these are required gates, not optional follow-ups.
- **Remaining detail:** No F0 implementation or timing exists, so these are projected caps, not demonstrated runtime. §0 line 40 says setup once, while §12’s (3 	imes (setup + ldots)) formula counts setup once per seed wave; spell out whether setup is per arm process or shared per wave and ensure the measured parallel timing matches that accounting. Resolve the label-path mismatch noted in Q2 and the second label mismatch: §5 line 180 reads `f0_r_labels.json`, but §13 line 384 lists `f0_labels.json`.
- **Next steps:** (1) Commit the F0 builder/orchestrator at a recorded clean SHA before D0. (2) Use D1’s measured per-phase parallel timings to calculate R projection with the stated slowest-arm and three-wave convention; record actual thread/process and contention measurements. (3) Do not start R unless the 12-thread and 96-minute checks pass and its separate approval is granted.

## Q6. Scope

- **判定: agree.**
- **Evidence:** v1.1 §10 removes H3 and explicitly forbids automatic launch (lines 330–336). §14 limits `ROUTE_STOP` to the configured EG2 layer19/LoRA/adapter route, disclaims an architecture-only bottleneck, makes the auxiliary contrasts descriptive/no-inference, records the dropped zero/permuted null and 1-seed gate as lost controls, and says F0 cannot claim they were replaced (lines 394–407). This is consistent with the Phase 6 cause report’s bounded native-path conclusion (§1 lines 8, 53–60; §5 lines 101–109): M_PASS is not donor-specific evidence, and native P/PA findings do not establish EG2 mechanism.
- **Next steps:** Preserve these boundaries in any result report. No EG2-track STOP, B0-B rescue, H3 launch, or replacement-control claim follows automatically from F0.

## Final verdict: NARROW

**No D0/D1/R approval and no execution on this draft.** The design’s scope and decision table are substantially clearer, but the MDE/power claim is quantitatively misaligned with the actual PASS threshold; initialization assertions omit the promised post-update weight change and canonical state/RNG encoding; D1’s exact allowlist and filesystem seal are not fully specified; and donor-cluster sensitivity lacks a precommitted method and decision role. These are fixable, but must be resolved in the prereg and checked against the committed F0 implementation before any stage approval.

## Must-fix, ranked

1. **STOP/MDE calibration (blocker):** Correct the 80%-power/MDE for the strict `CI_D.lower > .05` gate; source the SE and account for the additional E01-signal and seed-sign gates. .0876 is the observed CI-boundary estimate, not an 80%-power mean.
2. **Initialization audit (blocker):** Define canonical tensor/RNG serialization with golden vectors and assert intended trainable weights actually change after the first update for the debug and all registered seeds.
3. **D1 artifact seal (blocker):** Enumerate the literal allowed keys/files, add phase-7 and complete-tree absence assertions, and test the writer/negative cases; no reuse of `eval_arm_d1`.
4. **Cohort dependency binding (blocker):** Bind the exact preflight/donor graph by content hash and define the donor-cluster sensitivity method and pre-result interpretation.
5. **Implementation interface/compute (before D0):** Resolve `d1_mechanics.json` vs `f0_d1_mechanics.json` and `f0_r_labels.json` vs `f0_labels.json`; pin setup accounting in `T_proj_f0`; commit the clean F0 implementation before D0 and require each stated stage approval.

## Incorrect or unsupported premises to correct

- `.054` is not the 80%-power target for a PASS rule whose lower 95% CI must exceed +.05; the normal approximation for that lower-bound gate is about .104 using the stated SE, before joint gates.
- `.0876` is the approximate observed estimate whose lower 95% bound reaches .05, not an 80%-power expected mean.
- The reviewed evidence contains no observed F0 E01−E11 outcomes and does not establish that Phase 6’s paired SE transfers to the planned EG2 contrast.
- The 15-document conditional estimand and descriptive 20-document values do not support population generalization; v1.1 correctly disclaims it.
- Phase 6 M_PASS and native P/PA results are not evidence of EG2 donor-specific content use or a structural adapter bottleneck.