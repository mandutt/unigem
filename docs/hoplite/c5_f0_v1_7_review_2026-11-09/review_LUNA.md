# C5 F0 v1.7 — Independent Review (Round 7/10)

- **Reviewed HEAD:** `e5d69ab3123b8ccc2426a87e672628da99cea080`
- **Synchronization:** `git fetch origin` succeeded; `git pull --ff-only origin main` succeeded (`Already up to date`). Working tree was clean before this review.
- **Scope:** Desk review only. No training, evaluation, test 163/P1 access, or experiment execution. No prior v1.6 verdict is inherited.
- **Verdict:** **NARROW — not approved for D0, D1, Q, or R yet.** The experiment is salvageable without changing frozen seeds, thresholds, donors, steps, or LR, but the ranked protocol gaps below must be closed before any stage is authorized.

## Required verbatim paired E01−E11

From v1.7 §2 and §6.3 (lines 69, 222–228, 233):

```text
- Primary: **E01 vs E11** (LoRA initialization matched).
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
- `D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.
```

## Q1. Q gate / three seeds / initialization manifest

- **Decision: conditional.** The initialization design is directionally adequate: §4 (86–125) separates adapter and LoRA RNG resets, requires matched E01/E11 LoRA and E10/E11 adapter hashes, records canonical tensor/RNG/base/cache/label hashes, supplies `step_seed` golden vectors, and explicitly treats matched initialization—not equal trained weights—as the claim. Stage P covers 3 registered seeds × 4 cells; Q audits one update for each seed/cell (§13A.1, 423–430). Requiring every registered seed to pass Q, with no two-seed continuation, is the correct fail-closed direction (§5, 188–190; §6.6, 264–269).
- **Blocker:** The gate is still expressed as `pre_r_seed_audit_pass[seed]:true`, but the P/Q record schema and the predicate that computes that value are not specified. “Append-only,” “atomic append+validate,” and “partial files rejected” (§13A.1, 425–431; §13A.9, 529–533) do not define the required record set, required keys/types, duplicate/stale-record handling, or how the gate proves all four cells passed for that seed. A missing, malformed, duplicated, or mismatched P/Q record must not be able to coexist with a true aggregate flag.
- **Next:** Before D0, define exact P/Q schemas and a deterministic gate: exactly one valid record for each required `(stage, seed, cell)`, bound to the clean `code_commit`, command, input hashes and frozen common-ID/donor-map hashes; any missing/extra/duplicate/partial/mismatched record fails closed and blocks R. Compute the aggregate pass from those records rather than trusting a caller-supplied boolean.

## Q2. D1 predicates / seal / telemetry

- **Decision: disagree pending correction.** The literal D1 schema, exact output path, checkpoint deletion, no-signal rules and negative tests are substantially stronger than a normal “sealed” flag (§5, 163–177; §13A.4, 452–503). In particular, `wrong_donor_ce_calls:0`, `donor_map_loads:0`, `checkpoint_absent:true`, and the mechanics-only writer/consumer boundary are appropriate.
- **Blocker — predicate omission:** `real_memory_ce_calls` is recorded (§13A.4, 488), but the assertion list (§13A.4, 467–475) has only `ce_finite_ok`; there is no expected real-memory CE count or `real_memory_ce_calls_ok`, and §13A.4’s `mechanics_pass` formula (“all assertions==true,” lines 497–500) therefore does not enforce the exact call-count assertion claimed in the v1.7 change summary (§0, line 33). Define the expected per-cell and total count from the permitted D1 calls, add an explicit equality assertion, and include it in `mechanics_pass`. Finiteness is not a substitute for call-count integrity.
- **Seal condition:** Keep the new F0 mechanics evaluator independent. The current `runner/c5_pm_phase6.py` is not a compliant substitute: `eval_arm_d1` materializes `per_doc`/`delta_shuffled_*` (lines 429–489); `run_d1` sets six Torch threads and performs the old eval/M/phase-7/checkpoint path (778–882). This conflicts with v1.7’s explicit “does not reuse `eval_arm_d1`” code plan (§11, 357–369), so D0 must remain blocked until a separate committed F0 implementation and its negative artifact tests exist.
- **Next:** Add the count predicate and test both success and crash paths against the exact output inventory, prohibited signal artifacts and checkpoint absence. Treat all absent/malformed telemetry as failure, not as a default success value.

## Q3. STOP / MDE / near-threshold / harm-benefit

- **Decision: agree with a wording condition.** The state ordering is coherent: protocol failure → `NOT_EVALUABLE`; the `PASS_POSITIVE` lower-bound condition (`CI_D.lower > +.05`) cannot overlap `EQUIVALENT` (`CI_D` wholly inside `[-.05,+.05]`); then `ALL_FAIL` yields route-only STOP; otherwise `INDETERMINATE` (§7, 271–322). `ALL_FAIL` is expressly limited to E01/E11 × copy/full, not E00/E10 (§7, 289–312). The fallback reasons are exhaustive, and harm/benefit are explicitly descriptive and non-exclusive with PASS (§7, 296–318).
- **MDE:** The values are appropriately qualified, not represented as F0 observations: `.019170` SE and `.0376` 50% MDE derive from the Phase 6 F−L paired proxy, not a validated E01−E11 SE; `.0537` is the 80% proxy, `.0876` the 50% gate-boundary mean, and `.104` the approximate 80%-power gate mean (§12, 389; v1.0 synthesis §3, 49–54). They must remain planning context only; the realized frozen `CI_D` drives decisions. Do not claim prospective F0 power from this proxy.
- **Near-threshold condition:** The deterministic rule in §7, line 313—`h=(CI_D.upper-CI_D.lower)/2`, near when `|mean_D-b|<=h` for `b∈{.05,0}`—is acceptable as a descriptive width heuristic, not an inference that the boundary lies inside the percentile CI. A percentile CI need not be centered on `mean_D`; therefore report mean, both CI endpoints, `h`, and each boundary, and label the flag descriptive. This is a clarification, not a reason to alter thresholds or decision states.

## Q4. Cohort / cell CI / donor-conditional interpretation

- **Decision: agree, conditional on the narrow estimand.** The plan fixes the 15 frozen length-eligible `common_ids`, says explicitly that they are length-selected and forbids generalization to the 20-doc validation population (§6.1, 194–207). It pairs E01/E11 on the same documents, averages the three registered seeds at document level, and bootstraps the 15 document contrasts (`n_boot=10000`, fixed seed; §6.2–6.4, 209–252). It also requires all 5 donors per doc, identical donor sets across cells, complete 3/3 seed data, and makes missing endpoints `NOT_EVALUABLE` rather than silently shrinking the cohort (§6.1, 201–206; §6.6, 264–269).
- **Interpretation limit:** Because the donor graph reuses validation documents, this is a fixed-cohort/fixed-donor-graph contrast, not independent sampling of 75 donor-document observations and not population-level donor inference. The plan states that condition and calls leave-one-donor-out a sensitivity range (§6.1, 197–201; §6.5, 260–262; §12, 389). Keep the claim at that conditional level; do not treat the sensitivity range as a donor-population CI. The 3-seed sign check is a replication gate, not a substitute for the doc-level interval (§6.3, 232–235).

## Q5. Compute / 16-core, 1-thread contract / estimate provenance

- **Decision: disagree pending a projection and host-check fix.** The one-thread-per-arm, four-process contract and `nproc>=16` gate are internally consistent as stated; the 4-vCPU workspace is explicitly disqualified (§0, 22–25; §12, 373–390; §13A.7, 518–521). The plan correctly labels `1,180.6s` and `4,939.884s` as Phase 6 estimates at 3 threads/arm—not measurements—and requires committed F0 provenance plus measured parallel timing (§0, 26–29; §11, 363–369; §12, 381–388). The F0 slowest-arm aggregation is appropriately distinguished from the historical four-arm Phase 6 sum (§12, 382–385).
- **Blocker — unmeasured projection terms:** `T_proj_R` includes `t_primary_replay` and `t_replay_15x5x2x2x2` (§12, 382–384), but D1’s literal `timings` object contains only setup, step0, step100, M build/CE, generation and total (§13A.4, 477). It also exposes scalar timing fields, while the projection requires the slowest arm’s phase terms and the contention formula uses `sum(per_arm_phase_s)` (§12, 383–387); no per-cell/per-arm timing schema or denominator field is specified. D1 is prohibited from computing/writing signal and from calling wrong-donor CE (§5, 167–177; §13A.8, 523–527), while Q’s wrong-donor finiteness check has no specified timing record (§13A.1, 427–431). As written, the specified D1/Q telemetry cannot substantiate the replay terms, slowest-arm aggregation, or contention denominator in the 96-minute R projection. Add a bounded, non-result timing method for those exact workloads and define the per-arm timing record (without persisting endpoint values and without weakening D1’s zero-wrong-donor rule), or give a fully specified conservative estimator and its validation; then use the committed orchestrator’s measured inputs to decide the cap.
- **Host enforcement:** `nproc>=16` alone does not prove the effective CPU quota or prevent nested Torch/BLAS worker threads. Before D0, specify and assert the effective affinity/quota and one-thread settings for each arm process (including intra/inter-op and relevant BLAS/OpenMP pools); record those alongside `nproc`, `threads_per_arm`, `parallel_wall_s`, and contention. Do not infer a qualifying 16-core execution from a host’s nominal CPU count alone.

## Q6. Scope / route-only boundary

- **Decision: agree, with implementation evidence required.** The causal target is correctly narrowed to `adapter-as-configured`—adapter parameters, LR and adapter-conditioned graph—not an architecture-only effect (§4, 121–126). The plan labels the contrast association-only, bounds `ROUTE_STOP` to this EG2 layer-19 route, explicitly disclaims EG2-track/B0-B conclusions, and keeps H3 outside F0 with no automatic trigger (§8, 324–338; §10, 349–355; §14, 535–548). It also admits that the earlier zero/permuted null and one-seed gate were dropped and cannot be claimed as replaced (§14, 547).
- **Condition:** The “test 163/P1 paths are not opened” claim is stronger than the two false flags in `data_scope.json`. §13A.9 (529–533) requires frozen ID allowlists and records `test_split_used:false`/`p1_used:false`, but does not specify a forbidden-path read audit or negative test for those inputs. Define the allowed input inventory and enforce/test denial of test/P1 reads in the committed F0 code. Keep the manifest as an audit record, not proof by assertion.

## Ranked must-fix before any stage approval

1. **P/Q gate integrity:** Specify exact P/Q record schemas, completeness and hash binding; compute each seed’s pass from all four cells and fail closed on missing, duplicate, malformed, stale or partial records.
2. **D1 count/seal correctness:** Add an explicit expected `real_memory_ce_calls` assertion to `mechanics_pass`; commit the separate F0 mechanics writer/gate and test prohibited artifact/checkpoint paths on success and crash. Do not reuse the current Phase 6 D1 evaluator.
3. **R compute projection:** Supply timing evidence or a validated conservative estimator for the primary and 15×5 replay terms while retaining D1’s no-signal/zero-wrong-donor contract; enforce effective CPU quota/affinity and one-thread-per-arm settings.
4. **Scope enforcement:** Define the allowed input inventory and negative read-path tests for test 163/P1; false manifest flags alone are not access evidence.
5. **Descriptive near flag:** State explicitly that the half-width rule is a reporting heuristic for percentile intervals, and print mean, CI endpoints, half-width and boundary. Do not change the preregistered thresholds.

## Incorrect premises / historical evidence

- Do not read the v1.6 vote (or the v0.9/v1.0 syntheses) as approval for v1.7; the v1.7 request says this is a fresh review and the plan remains draft/unapproved (§0, 1–14; §18, 605–612).
- The supplied Phase 6 synthesis says `runner/c5_pm_phase6.py` rejects `--mode registered` (reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md §3, 38–44). At the reviewed HEAD, its `main()` accepts that mode and calls `run_registered_unit` (`runner/c5_pm_phase6.py`, 946–965). Treat that statement as historical/stale; it does not establish that an F0 driver exists or can be reused.
- The Phase 6 `1,180.6s` and `4,939.884s` values are not F0 measurements, and the `.019170`/`.0376` figures are not validated E01−E11 uncertainty estimates (§12, 381–389). The plan correctly caveats these values; preserve that caveat.
- Phase 6 native-path adapter-associated signal loss is not evidence for an EG2 mechanism or an architecture-wide bottleneck (reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md §5–6, 101–139; v1.7 §14, 544–548).

**Final: NARROW.** Keep F0 unapproved and unexecuted until must-fixes 1–3 are satisfied in a committed implementation and the scope guard in item 4 is testable. No threshold, seed, donor, step, or LR change is requested.