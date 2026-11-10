# C5 F0 v1.6 — Independent Review (Luna)

- **Reviewed HEAD:** `b483e69f95340b12a51717749ebda6ea97c96bf9`
- **Synchronization:** `git fetch origin` succeeded; `git pull --ff-only origin main` fast-forwarded `1b6e4c5..b483e69`.
- **Review status:** consultation only. v1.6 is still a draft; no F0 result exists at this HEAD. No training or evaluation was run, and this review does not approve a stage for execution.

## Required verbatim paired E01−E11 definition

From `docs/plan_c5_f0_v1_6_2026-11-09.md` §6.3:

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

Also verbatim §6.3: “`D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.” This is the registered contrast, **not an observed estimate**.

## Q1. Wrong-donor path, P/Q gates, and initialization hashes

- **Verdict: conditional.** The initialization contract in §§4, 13A.1–13A.2 is materially specified: E01/E11 reset the LoRA seed identically; E10/E11 use the same adapter seed; per-step seeds have golden vectors; LoRA/adapter/base/cache/label/RNG hashes and a serialization KAT are required. P checks all three registered seeds at init; Q checks one update per registered seed and expected parameter-group changes. The donor-map SHA is required in §6.1. The checked-in `donors_for` implementation is deterministic, excludes the target, and selects nearest-length donors with an ID tie-break (`runner/c5_mt5_lora_b0.py:318-326`).
- **Blocker:** §5 lines 181-182 permits R to continue with at least two seeds after a Q failure, but §§6.1, 6.6 and 7 require complete 3/3-seed data for `PROTOCOL_VALID`/primary evaluation. A two-seed R can consume compute but cannot yield the preregistered primary decision. Make any Q failure block primary R, or preregister a distinct two-seed estimand and decision rule before any data; do not silently treat two as three.
- **Blocker:** the plan accepts `wrong_donor_ce_calls:0` for D1 and first exercises the primary wrong-donor CE path at R (§§0.1, 13A.8). A `donors_for`/crop unit test does not verify CE computation, endpoint masking, or evaluator wiring. Keep D1’s no-signal seal, but add a non-result, pre-R test of the actual wrong-donor CE path and its expected finite/count behavior. Otherwise the primary measurement can fail only after a registered seed has started.
- **Implementation condition:** P’s 12 loads are parallel in the compute table, while `d0/init_hashes.json` must be append-only (§§12, 13A.1). Specify a single-writer/atomic merge (including duplicate `{stage,seed,cell}` rejection) so concurrent processes cannot lose or replace records. The Phase 6 I/O denylist in §13A.6 also needs to be enforced by the committed F0 reader path, not only asserted in a report.

## Q2. D1 `mechanics_pass`, flags, telemetry, and seal

- **Verdict: disagree as specified; the seal shape is strong, but not yet sufficient to gate.** §13A.4 gives a literal allowlist, makes `mechanics_pass` an AND over assertions and seal flags, and constrains success/partial shapes; §13A.4 and §13A.6 require checkpoint deletion and negative filesystem/input tests. Those are the right controls. The separate F0 mechanics evaluator is essential: the checked-in `runner/c5_pm_phase6.py` still defines only Phase 6 arms F/L/P/PA (`:52-59`), and its Phase 6 `eval_arm_d1` is not the F0 mechanics evaluator (`:429ff`). The plan itself says the new F0 code is not implemented yet (§11, lines 351-360); no existing Phase 6 D1 artifact is proof that this F0 seal works.
- **Specific gap:** the schema reports `real_memory_ce_calls:int`, but `mechanics_pass` does not require an exact expected call count or include a `real_memory_ce_calls_ok` assertion (§13A.4, lines 458-489). With `wrong_donor_ce_calls==0`, `ce_finite_ok:true` could be vacuously true if the real-memory CE loop did not execute. Define the expected real-CE count from the D1 call plan and AND that check into the pass predicate.
- **Telemetry blocker:** the literal D1 schema has `timings.setup_s`, `step0_s`, `step100_s`, `m_build_s`, `m_ce_s`, `generation_s`, and `total_s` (§13A.4, lines 468-470). It does not define `setup_wall_s` versus `sum_process_setup_s`, nor expose the per-arm nine timing terms used by §12 lines 373-383 to compute `T_proj_R` (including training and replay/overhead). Therefore the claim that D1 telemetry supports the R projection is not yet auditable. Add exact fields/semantics and map them to the projection formula; do not infer them from `total_s`.

## Q3. STOP/MDE/near-threshold rules

- **Verdict: conditional.** The four-state ordering in §7 is mutually exclusive and exhaustive if the reported CI is valid: `PASS_POSITIVE` cannot overlap `EQUIVALENT` because it requires `CI_D.lower > +.05`, while equivalence requires the full interval within `[-.05,+.05]`. `ROUTE_STOP` is separately restricted to `ALL_FAIL` for E01/E11 × copy/full; `INDETERMINATE` is the residual valid-protocol state. The route-only consequence in §14 is appropriately limited.
- **MDE treatment is acceptable only as labeled context:** §12 line 381 explicitly calls `.019170` an F−L planning proxy, not a validated E01−E11 SE, and says realized `CI_D` governs; `.0376`, `.0537`, `.104`, and `.0876` are not observed F0 estimates. Keep them out of claims of achieved power or expected F0 effect.
- **Blocker:** §7 line 306 says a near-threshold `ROUTE_STOP` is one where `|mean_D|` is “within one half-width of the boundary,” but it does not identify the boundary (0, ±.05, or the PASS lower-bound threshold), define half-width for an asymmetric percentile CI, or give the exact reporting trigger. Define the boundary set and formula before execution; report observed mean, both CI endpoints, and the defined width whenever the rule fires. The current prose leaves reporting discretionary.

## Q4. Cohort and cell CI

- **Verdict: conditional agree for the fixed estimand only.** §§6.1-6.4 freeze the 15 length-eligible `common_ids` (5 of 20 excluded at K=753), prohibit substitution/generalization to the 20-doc cohort, require all 3 seeds and exactly 5 identical donors per doc across cells, and define the seed-averaged, document-level bootstrap with `n_boot=10000`, seed `20261109`, and finite/realized-parameter assertions. The checked-in `bootstrap_paired_v2` resamples the supplied per-document vector after seed averaging with linear percentile bounds (`runner/c5_pm_stats.py:29-71`), matching that declared estimand.
- The interval is conditional on the 15 documents, the fixed length-nearest donor graph, and the three registered seeds; it is not a donor-population or 20-document population CI. The leave-one-donor-out range in §6.1 is a sensitivity check, not a donor-cluster CI. Preserve those limits in reporting. M is correctly not a primary donor-specific endpoint (§9).
- **Gate inconsistency:** the Q-failure/two-seed allowance noted under Q1 is incompatible with the exact 3-seed cohort and `NOT_EVALUABLE` rule (§6.6). This must be resolved before R; a 2-seed dataset must not enter the registered cell CIs or seed-sign gate as if complete.

## Q5. Compute, 16-core gate, and setup accounting

- **Verdict: disagree; approval blocker.** The v1.6 summary says “16 cores, 1 thread/arm” (§0, lines 35-38), while §12 lines 367-371 budgets 3 threads/arm × 4 arms = 12 logical threads for P/Q/D1/R; §12 line 380 and §13A.7 allow that configuration only when `nproc>=16` (or instead allow one thread/arm). These alternatives may describe different modes, but the document does not say which is normative. Reconcile the host, per-arm thread count, and measured parallelism in one contract. The stated 4-vCPU workspace must remain excluded unless it actually satisfies that contract.
- There is also a measurement-source conflict: two of the nine projection terms are primary/replay timings (§12, line 374), while D1 is expressly forbidden to compute or persist signal/replay values (§5, lines 160-170; §13A.8 keeps wrong-donor CE calls at zero). Identify a separate non-result timing method or a frozen, justified proxy for those terms; do not claim that the sealed D1 run measured them. Require a committed F0 orchestrator, exact wall/setup/per-arm measurements, `nproc` and thread counts, and a passing projection under the frozen cap before approving R. P/Q have their own separate 10/15-minute caps; do not fold them into D0 or R.

## Q6. Scope and route-only consequence

- **Verdict: conditional agree.** §§8, 10 and 14 appropriately limit F0 to the configured EG2 layer-19 route and the adapter-as-configured contrast; they disavow an architecture-only bottleneck, keep H3 out of scope, forbid automatic H3/B0-B progression, and acknowledge the missing null/one-seed controls. A `ROUTE_STOP` must remain route-only; M_PASS is not donor-specific evidence (§9; also `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, §§1, 5).
- **Scope audit still needs an implementation gate:** §13A.4 records `test_split_used:false` and `p1_used:false`, but a Boolean declaration is not proof of non-access. The Phase 6 prereg explicitly says test-split use is determined by frozen-ID allowlist membership and that a false declaration is only an attestation (`docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, §1.5, lines 96-119). Make the F0 runner validate every consumed/produced ID against the frozen train20/val20/common-ID allowlist and record the inventory without opening test 163 or using P1. Keep the plan’s explicit test/P1 prohibitions.

## Final verdict: **NARROW**

The experiment remains a coherent, route-limited diagnostic, but v1.6 is **not ready for approval as written**. Resolve the ranked gates below in the prereg/implementation before any D0 approval; this review authorizes no D0, D1, Q, or R execution.

### Must-fix (ranked)

1. **Resolve the Q-failure versus 3/3-seed contradiction.** If any seed fails Q, block primary R; do not continue with two seeds under the current primary/CI rules.
2. **Unify the execution contract and make the R projection computable.** Choose the normative 16-core/thread-per-arm mode and emit `setup_wall_s`, `sum_process_setup_s`, and all per-arm projection terms in the literal D1 schema.
3. **Validate the actual wrong-donor CE path before R, without creating a signal result.** Keep D1 `wrong_donor_ce_calls:0`; add a separate pre-R non-result path test, plus an exact D1 real-memory CE count assertion.
4. **Define the near-threshold trigger mathematically.** Name the decision boundary/boundaries and the asymmetric-CI width rule; make reporting deterministic.
5. **Enforce the data-scope and initialization-manifest contracts in code.** Apply frozen ID allowlists and use a single-writer/atomic append-and-validate path for parallel P/Q/init records; keep test 163 and P1 untouched.

**Incorrect premise to avoid:** initialization-matched LoRA does not mean trained E01/E11 weights remain equal; the preregistered treatment is the configured adapter path (parameters, LR, and conditioned forward graph), not architecture alone (§§4, 14).