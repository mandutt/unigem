# C5 F0 v1.8 — Independent Review (LUNA)

- **Reviewed HEAD:** ac1ee40da32427d452bd5d89bb339f034b2b7c9c
- **Synchronization:** git fetch origin and git pull --ff-only origin main both succeeded; main was already up to date at the reviewed HEAD.
- **Target:** docs/plan_c5_f0_v1_8_2026-11-09.md (DRAFT, unapproved, unexecuted).
- **Scope:** This is a new independent review. I did not inherit a v1.7 verdict. No training, evaluation, test-163/P1 data access, or subagent work was performed.

## Verbatim paired E01–E11 (v1.8 §§2, 6.3)

~~~text
| E01 (F0) | EG2 raw | none | 64 modules | 100 | adapter-free + LoRA |
| E11 (L) | EG2 raw | trained | 64 modules | 100 | adapter + LoRA |

- Primary: **E01 vs E11** (LoRA initialization matched).
~~~

~~~text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
~~~

## Q1. P/Q/R gates, schemas, and hashes

- **판정: disagree — blocking.** The intended audit coverage is substantially better than the earlier drafts, but the written schemas do not yet encode the populations their predicates claim to validate.
- **P cardinality is underspecified:** §13A.10 (lines 547–557) declares seeds:[20261108,20261109,20261110], but cells is only {E00,E10,E01,E11 -> {hash,lora_names,n_params}}; it does not specify a seed dimension or per-seed cell records. The predicate nevertheless requires 3 seeds × 4 cells. The hash payload and the exact fields compared by the single p_r_hash_equal boolean are also not typed. §0 (lines 24–29) and §13A.1 (lines 429–434) describe per-seed/per-cell evidence, but the literal schema cannot unambiguously represent it.
- **Q has a per-seed/global-count contradiction:** §13A.10 (lines 559–569) places units:12 and trained_updates:9 in each q_seed_audit/{seed}.json, while §13A.1 (lines 431–434) defines 12 units/9 trained updates across all three seeds. A per-seed artifact should validate 4 cells/units and 3 trained updates (E00 zero), or the artifact must instead be a single three-seed aggregate. As written, both readings are possible. The exact cells key set and per-cell update count also need to be literal, not {...}.
- **R pass is not a complete fail-closed mechanics schema:** §13A.10 (lines 571–577) lists totals and provenance_ok, but not per-seed/per-cell count bindings or the required generation_records:240 from §5 (lines 181–192). A total can match while its distribution across cells/seeds is wrong. Specify how unit manifests and record files are checked and make missing, duplicate, malformed, partial, or misassigned records fail the gate.
- **ID hashes do not bind order:** §3 (line 83) trains using train20[step%20]; §4 (lines 121–124) hashes sorted UTF-8 IDs and says preflight order is recorded separately. A sorted-membership hash is unchanged by reordering, although training assignments change. Bind the exact ordered train/val/common ID sequences into the canonical digest and assert them at P/Q/R; “recorded separately” is not a defined integrity check. This also makes seeded document-level resampling reproducible against the same input ordering.
- **Next steps:** Define versioned, typed seed→cell maps and exact per-seed Q counts; specify R’s per-unit and aggregate predicates; hash and compare ordered ID sequences, not only sorted membership. Preserve the canonical tensor/KAT contract in §13A.2 and test it in the committed F0 runner before any stage approval.

## Q2. D1 real CE, seal, and telemetry

- **판정: conditional — blocking until the counter and custody contract are made executable.** The strongest part of v1.8 is the separation from eval_arm_d1: §11 (lines 361–370) requires a new mechanics evaluator, while §§5 and 13A.4 forbid signal objects, restrict the D1 output, require checkpoint deletion, and add negative tests. Keep these protections. The existing Phase 6 eval_arm_d1 materializes per-document real/wrong CE and deltas (runner/c5_pm_phase6.py:429–476); run_d1 persists step/final results, partial reports, phase-7 data, and checkpoints (:804–882). Reusing it would defeat the stated seal.
- **The D1 CE-count predicate is ambiguous and can be self-attested:** §5 (lines 150–180) requires 20 step-0 and 20 final docs per cell; §13A.4 (lines 493–507) defines expected_real_memory_ce_calls using one step-0 call per cell, then only E10/E01/E11 final donor-crop calls for 15 docs × 5 donors, plus “M CE count from report.” §13A.8 (lines 533–537) says D1 must make zero wrong-donor CE calls and first exercises that numerical path at R. Define exactly which D1 real-memory calls are made, whether the 15-doc subset is distinct from the 20-doc mechanics counts, and what one “call” counts (per donor crop, per loss, or another unit). Compute the expected M/CE total independently from frozen per-cell expectations; deriving it from the same report being checked makes the comparison circular.
- **Crash custody needs a hard-kill case:** §13A.4 (lines 508–511) requires no checkpoint after a crash, but a handled exception/partial-writer test does not prove cleanup after SIGKILL or host interruption. Use an isolated temporary checkpoint area and test abrupt termination/restart cleanup; only a digest may survive, and the consumer must reject all D1-derived artifacts other than the exact allowed mechanics schema.
- **Telemetry is specified but not yet evidenced:** §13A.4 (lines 482–484) records nproc, threads_per_arm, parallel_wall_s, and contention_ratio; §11 (lines 361–370) requires committed provenance. Before relying on these values, the committed orchestrator must record the actual arm process start/end/exit times, effective CPU affinity/quota and thread settings, host identity, and measured parallel wall. nproc and a self-reported parallel_arms boolean alone do not prove four concurrent arms or two usable threads per arm. Keep D1 stdout/log CE-free (§13 lines 417–424), and retain the rule that no D1 value is read for R/STOP (§5 lines 176–192).
- **Next steps:** Freeze the call-count formula and independent expected constants; add abrupt-kill custody tests; require the committed orchestrator’s auditable CPU/process telemetry before D1 is accepted.

## Q3. STOP/MDE/near-threshold

- **판정: agree on the decision taxonomy; conditional on clarifying the diagnostic.** Given finite, ordered CI bounds and PROTOCOL_VALID, the four states in §7 (lines 273–324) are mutually exclusive and exhaustive. PASS_POSITIVE requires CI_D.lower > +.05, while EQUIVALENT requires CI_D.upper <= +.05, so they cannot overlap. ALL_FAIL includes FAIL(E01,copy), which prevents it from co-occurring with PASS_POSITIVE’s SIGNAL(E01,copy). ALL_FAIL plus a relative adapter benefit still stops only the route configured; §14 (lines 591–595) correctly forbids turning that into an EG2-wide conclusion or automatic H3 launch.
- **MDE disclosure is appropriately limited:** §12 (line 391) labels .037573/.019170 as an F−L planning proxy, not a validated E01−E11 SE; .0537 is the corresponding approximate 80%-power MDE. It says the realized CI governs the decision and is conditional on the fixed donor graph. The Phase 6 cause report also limits its P/PA result to the native path and does not establish EG2 generalization (reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md, §§1, 5). Keep those caveats; do not present these proxies as F0 power or population guarantees.
- **Near-threshold formula needs correction/precision:** §7 (line 315) sets h=(CI.upper-CI.lower)/2 and calls a cell near when |mean-b|<=h, for b∈{.05,0}. The CI is a percentile interval and need not be centered on the arithmetic mean; this formula is not the distance from the actual interval to the decision boundary. It also does not state which boundary applies to copy versus full, or diagnose the CI.lower>0 and 2/3-seed gates. Report signed margins separately (copy mean−.05, full mean−0, CI.lower−0, and number of positive seeds−2) and, if desired, actual interval-to-boundary distance. Keep all such diagnostics descriptive and forbid them from changing the frozen state.
- **Next steps:** Retain the four-state truth table and route-only consequence; repair the descriptive near-threshold definition and label it non-decision metadata.

## Q4. Cohort and cell CI

- **판정: agree, conditional on Q1/R artifact checks.** §§6.1–6.6 (lines 196–271) state the estimand honestly: the 15 frozen, length-eligible common documents with the fixed donor graph; 20-doc results are descriptive, and population generalization is forbidden. Requiring all 15 docs × 3 seeds, exactly five donors per doc, identical donor sets across E00/E10/E01/E11, no 15→14 substitution, and NOT_EVALUABLE on missingness is appropriate. The cell signal CI uses donor-averaged per-doc deltas after seed averaging, not 15×5 pseudo-independent observations (§§6.2–6.4); the primary E01−E11 contrast is paired at the document level (§6.3).
- The explicit n_boot=10000, seed 20261109, and prohibition on l_predicate (§6.3) address the frozen Phase 6 default of 1,000 (docs/plan_c5_b0a_pm_prereg_v1_0_11.md, §10.1). The referenced bootstrap_paired_v2 implementation uses document resampling with replacement, fresh PCG64, and linear percentile bounds (runner/c5_pm_stats.py:29–71); the F0 runner must pass the override and record/assert n=15, n_boot, seed, RNG, and CI method. Do not claim inference beyond this selected cohort and donor graph. The limitations are consistent with the earlier v1.0 review’s length-selection concern (reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md, §3 DS-2); this agreement is based on the current estimand, not that prior verdict.
- **Next steps:** Bind the ID/order and donor-map hashes to every seed/cell result; enforce the 15×5×4×3 completeness checks before labels are computed.

## Q5. Compute: 2 threads/arm, caps, and lower bound

- **판정: conditional — no R approval on current evidence.** Four arm processes × two threads/arm = **eight logical worker threads**, which is internally consistent with the v1.8 normative configuration and a 16-core host (§§0, 5, 12). The 900 R updates are also arithmetically correct: 3 trained cells × 100 updates × 3 seeds; E00 remains untrained (§5, lines 181–192).
- **The “4 worker threads” wording in §15 (line 617) conflicts with that configuration.** Clarify it as four arm processes / two threads per arm / eight logical threads, and separately say the host must expose at least 16 usable CPUs. nproc>=16 should be backed by affinity/cgroup-quota and process telemetry, not merely a nominal machine size.
- **Do not treat the Phase 6 wall values as measurements:** v1.8 §12 (lines 383–394) itself labels 1,180.6s and 4,939.884s as estimates. The cited Phase 6 prereg instead says six threads (§11.1), and its D1 runner sets six Torch threads (runner/c5_pm_phase6.py:778–804) while iterating arms; those sources do not validate a two-thread-per-arm parallel benchmark. Treat D-157 as a target configuration unless its measured artifact is attached and auditable.
- **The lower-bound correction is sound but must remain a one-way condition:** §13A.7 (lines 526–531) correctly says D1-derived T_proj omits R-only replay and is a lower bound, not a pre-abort guarantee. The binding R limit is measured wall ≤96 minutes (§12, lines 388–394; §13A.7, line 530). The committed orchestrator must enforce a real 96-minute wall deadline and fail closed/mark the run non-evaluable if it is exceeded; T_proj_R <=96 alone cannot prove that R will finish under the cap. D1’s 25-minute cap is expressly provisional, not yet evidenced by a measurement.
- **Next steps:** Resolve the worker-count wording; attach the D-157 measurement or stop using it as an anchor; require F0 code commit and measured qualifying-host D1 telemetry before R. Do not substitute the Phase 6 estimates for those measurements.

## Q6. Scope and negative reads

- **판정: conditional agree — scope boundaries are good; read-path proof is not yet sufficient.** §§10, 14, and 17 (lines 351–357, 539–550, 642–650) appropriately remove H3, prohibit automatic follow-on work, limit ROUTE_STOP to the configured route, state the association-only interpretation, and exclude test 163/P1. §13A.7–13A.9 (lines 526–543) improves on flags alone by requiring direct negative read tests, frozen ID allowlists, and a data-scope manifest. This is the right direction. The Phase 6 review synthesis correctly warns that access flags are attestations, not proof (reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md, §3 MF-6).
- **There is a concrete loader path that F0 must not inherit:** runner/c5_pm_phase6.py:70–77 reads and parses every line of DATA; load_frozen_inputs() calls it at line 94 and only constructs/checks the train20/val20 allowlist at lines 95–100. The Phase 6 prereg lists split sizes 1,293/161/163 (docs/plan_c5_b0a_pm_prereg_v1_0_11.md, §1.1). If this JSONL contains all splits, filtering after this load materializes sealed rows before the allowlist check. I did not inspect the dataset or assert that a test row was accessed; this is a reachable path that must be excluded from the F0 implementation. Use an approved train/val-only input or filter before parsing/materializing rows, and test the complete transitive loader path. Direct open probes and boolean flags alone do not prove non-access through Path.read_text, NumPy/PyTorch loaders, or subprocesses.
- **Next steps:** Keep the F0 runner independent; enforce access controls at the data-loader boundary and run negative tests over every supported read API/path before any P/Q/R stage. Record the committed code/input manifest used for that proof.

## Final verdict: **NARROW**

**Do not approve or execute F0 stages on this draft.** The estimand, primary pairing, route-only STOP consequence, and exclusion of H3 are acceptable. Approval is blocked by the P/Q/R schema/cardinality and ID-order gaps, the circular/ambiguous D1 CE-count contract, and the unproven no-read and compute-telemetry paths. These are fixable preregistration and implementation-contract defects, not a recommendation to expand the experiment. D0/D1/R remain separately gated and require their own explicit approvals (§11, lines 359–371).

### Must-fix before approval (ranked)

1. **Make P/Q/R gates represent and validate the actual run:** explicit seed×cell hashes, per-seed Q counts, per-cell/per-seed R record counts, complete provenance, and fail-closed schemas; hash the ordered ID arrays and bind them in init_hashes.json.
2. **Freeze an independent D1 CE-count formula and seal test:** reconcile 20-doc mechanics counts with the 15-doc donor-crop count, define the counted operation, derive expected counts independently of the output report, and test abrupt process/host termination for checkpoint cleanup.
3. **Prove scope at the loader boundary:** ensure no full-split source is parsed before the train20/val20 allowlist filter; test the transitive read path for test 163/P1, not just direct-open probes or flags.
4. **Make compute evidence enforceable:** correct “4 worker threads” to four arms × two threads (=8 logical threads), document usable CPU affinity/quota, commit the orchestrator before D0, measure D1 on the qualifying host, and enforce the actual 96-minute R wall deadline. Do not use the lower-bound projection as a completion guarantee.
5. **Define near-threshold reporting against the actual gates:** separate mean, CI-lower, and seed-sign margins; keep diagnostics non-decisional.

### Wrong premises to avoid

- 2 threads/arm is a proposed F0 execution configuration, not established by the Phase 6 six-thread/sequential runner or its estimated wall values.
- .037573 / .019170 are F−L planning proxies, not validated E01−E11 effect/SE or a population-power guarantee.
- M_PASS is not donor-specific content-use evidence (Phase 6 cause report, §1); ROUTE_STOP does not stop EG2 overall or authorize H3.
- A sorted set hash, test_split_used:false, or p1_used:false flag alone does not prove ordered-ID integrity or non-access.