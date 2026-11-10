# C5 F0 v1.5 — Independent Review (LUNA)

- Review date: 2026-11-10
- Reviewed HEAD after synchronization: `79b5dc772817d68026b7548507d0d6e87927b30e`
- Synchronization: `git fetch origin` succeeded; `git pull --ff-only origin main` reported “Already up to date.”
- Scope: independent review of v1.5 and the specified source material. No training/evaluation, test 163/P1 access, or changes outside this report.
- Status of plan: draft, unapproved, unexecuted (v1.5 §0, lines 1–11).

## Verbatim paired E01–E11 definition

No observed E01/E11 result exists in the reviewed material. The following is the preregistered primary contrast, reproduced verbatim from v1.5 §§2, 6.3 (lines 68, 219–224, 230):

> Primary: **E01 vs E11** (LoRA initialization matched).

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

> `D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.

## Q1. Stage P / initialization / `step_seed`

- **판정: conditional.** The design is materially stronger: E01/E11 reseed LoRA initialization independently of adapter construction; it records LoRA/adapter and base/cache/label hashes; and the parenthesized `step_seed` formula is unambiguous. I checked the listed golden vectors against that formula; they match (v1.5 §4, lines 85–124).
- The unresolved gap is coverage: §4 says the initialization assertions are “per registered seed” (lines 105–114), but Stage P records only assertions 1–4 and 6–8 for registered seeds 20261108/09/10; post-step0 RNG equality, weight change, and group-specific weight-change checks run only at D1 seed 20261111 (v1.5 §0, lines 19–22; §13A.1–13A.3, lines 416–440). That sentinel is not one of the R seeds.
- **Next:** make the post-step0 RNG and expected-group weight-change checks fail closed for each registered seed before accepting its 100-update unit, or explicitly narrow the §4 “per registered seed” contract and specify the per-seed R validity rule. Keep Stage P init-only; do not make it read signal values.

## Q2. D1 schema / signal path / seal

- **판정: disagree.** The D1 boundary is thoughtfully scoped, but the written contract is internally unsatisfiable and the pre-R signal-path choice is contradictory.
- **Schema/provenance collision:** D1 §5 requires `elapsed_s` and `phase_timings` (v1.5 lines 163); §11 requires each D1 artifact to record `code_commit`, command, and input SHA, while §12 requires the parallel-run telemetry (`nproc`, `threads_per_arm`, `parallel_wall_s`, `contention_ratio`; lines 358, 361). Yet §13A.4 lists the literal keys and then says “Only these keys” (lines 445–488); none of those timing, provenance, or parallel telemetry fields is allowed, and §5 says the mechanics JSON is the only D1 output (lines 165–173). Resolve this before approval by extending the literal schema or explicitly allowing a separately sealed telemetry/provenance artifact and naming its exact path and writer/reader rules.
- **Signal-path contradiction:** the change summary says “D1 wrong-donor CE finiteness dry run … choose dry run” (v1.5 §0, lines 32–33). The literal schema instead requires `wrong_donor_ce_calls: 0` ( §13A.4, lines 474–484), and §13A.8 says D1 must not call wrong-donor CE and that this path is first exercised at R (lines 508–512). Choose one contract. If retaining the no-signal D1 seal, correct the summary to R-first and state that the pre-R donor/crop unit test is not a CE smoke test; otherwise define a separate pre-R finite-only smoke artifact, with no persisted per-document CE/deltas and a matching call-count/schema rule.
- The plan correctly requires a new mechanics evaluator and forbids reuse of Phase 6 `eval_arm_d1` (v1.5 §11, lines 354–364). That separation is essential: the existing runner computes wrong-donor CE and writes `per_doc`/`delta_shuffled_*` in `eval_arm_d1` (`runner/c5_pm_phase6.py:429–489`), and calls it for step0/final in D1 (`:804–806`). Require the committed F0 implementation and a negative test proving it neither imports/calls that path nor leaves a readable D1 checkpoint after a hard process termination; catchable-exception cleanup alone is not sufficient evidence for the stated post-crash seal.
- **Next:** settle the signal-path contract, make the allowlist compatible with required metadata, and verify both success and killed-process failure paths before any D1 approval.

## Q3. STOP / MDE labels

- **판정: agree.** Given a valid ordered CI, `PASS_POSITIVE` (`CI_D.lower > +.05`) cannot overlap `EQUIVALENT` (the full CI lies in `[-.05,+.05]`). `ALL_FAIL` requires `FAIL(E01,copy)`, while PASS requires `SIGNAL(E01,copy)`, so the two branches do not overlap. With `NOT_EVALUABLE` first, then PASS, ALL_FAIL/ROUTE_STOP, and the residual INDETERMINATE state, the four-state ordering is exhaustive (v1.5 §§6.5, 7, lines 251–317). The fallback reason is explicit.
- The numeric labels are coherent as planning quantities: `.019170 = .037573/1.96`; `.0376` is the 50% MDE, `.0537` the 80% MDE, `.0876` the 50% gate boundary, and `.104` approximately the 80% gate mean. Crucially, §12 states that `.019170` is an F−L proxy, not a validated E01−E11 SE, and that none of these is an observed F0 mean (lines 380–382). Keep that qualification attached to any report of them.
- `ROUTE_STOP` is correctly route-only, not an EG2-track or B0-B decision (v1.5 §14, lines 514–527).

## Q4. Cohort / cell CI / donor conditional

- **판정: conditional.** The estimand is acceptably narrow if interpreted literally: 15 frozen, length-eligible common docs; 3/3 seed completeness; exactly five identical donors across cells; per-cell signals average seeds before the 15-doc bootstrap; 10,000 resamples, seed 20261109, linear percentile; and donor leave-one-out sensitivity (v1.5 §§6.1–6.4, lines 191–249). The plan explicitly bars extrapolation to the 20-doc validation population and says `CI_D` is conditional on the fixed donor graph (§6.1, §6.5; lines 193–204, 257–259).
- This is **not** a donor-population CI: donor identities are reused across documents, and leave-one-donor-out is a reported sensitivity range, not a donor-cluster confidence interval. Keep conclusions conditional to this 15-doc cohort and fixed graph. That limitation matters empirically: the prior v1.0 synthesis reports F at −0.11087 on 15 docs versus +0.000195 on 20, and L at −0.11351 versus −0.02218, respectively (v1.0 synthesis §3, DS-2). The current no-20-doc-generalization rule is therefore appropriate, not optional.
- **Next:** preserve the exact preflight `common_ids` and donor-map content hashes in the committed input/provenance record; do not relabel the bootstrap interval as population or donor-generalization evidence.

## Q5. Compute / `nproc` / setup

- **판정: disagree.** The workloads and caps are enumerated (D1: 3 updates/25 min; R: 900 updates/96 min; 4 arms × 3 threads), and the nine timing terms track Phase 6 §11.5 (v1.5 §12, lines 366–385; Phase 6 prereg §11.5, lines 1330–1354). But the admissible-host rule and the projection are not executable as written.
- **Host contradiction:** §13A.7 says `nproc>=16` **or** `threads_per_arm<=1`, while also declaring the current 4-vCPU host non-qualifying (v1.5 lines 503–506). The hard abort is only `nproc < 16 AND threads_per_arm > 1` (§12, line 381), which permits a 4-vCPU host when the arm thread count is 1. State explicitly whether that mode qualifies; give the same rule in the table, addendum, and abort check.
- **Projection ambiguity:** `setup_s_effective` is described as total setup for 3 waves × 4 processes and then added to a wall-time `T_proj_R` (v1.5 lines 376–378). Define whether that is accumulated process-seconds or measured wall setup per wave; they are not interchangeable. Also, `contention_ratio = parallel_wall_s / sum(per_arm_phase_s)` (line 380) is recorded but has no threshold or specified use in the cap, despite §0 saying the cap is from measured contention ratio (line 35). Define the reference/baseline and exact cap rule, or rename/remove it as descriptive telemetry. The runner is not implemented yet; §11’s clean committed SHA, command, input-SHA gate before D0 is necessary but does not resolve these ambiguities (lines 352–364).
- **Next:** publish one deterministic host eligibility predicate and wall-time projection with measured setup semantics, then require the committed orchestrator to emit and enforce those exact values. The current 4-vCPU workspace is not an approved execution target under the plan’s own exclusion.

## Q6. Scope / route-only

- **판정: agree.** H3 has no arm, trigger, or automatic launch; it requires a separate preregistration and approval (v1.5 §10, lines 344–350). The scope also states no EG2-wide STOP/keep claim, no B0-B rescue, and no architecture-only bottleneck inference (§14, lines 514–527). This is a defensible boundary for the single contrast.

## Final verdict

**NARROW — do not approve P/D0, D1, or R yet.** This is a preregistration/specification hold, not a recommendation to stop the EG2 track. The initialization design, conditional cohort, STOP taxonomy, and route-only scope are largely well bounded; the blockers below prevent an auditable gate and a reliable compute decision.

### Must-fix before any stage approval (ranked)

1. **D1 literal schema cannot carry required evidence.** Reconcile the exact-key allowlist with timings, provenance, and parallel telemetry; otherwise neither D1 sealing nor `T_proj_R` can be audited.
2. **Resolve the pre-R wrong-donor CE contradiction.** Pick D1 finite-only dry run versus R-first; align §0, `wrong_donor_ce_calls`, §13A.8, and the artifact/negative tests. Keep `per_doc`/delta/signal labels out of D1, and prove the seal against a killed process.
3. **Make compute eligibility and projection deterministic.** Reconcile 16-core versus 1-thread/arm (including the 4-vCPU exclusion), distinguish wall setup from summed process setup, and define how `contention_ratio` affects or does not affect the 96-minute cap.
4. **Align per-registered-seed init/update assertions.** Either check post-step0 RNG parity and expected parameter-group changes for each R seed before accepting that seed’s run, or narrow the §4 contract and explicitly define how an R seed can fail mechanics.

### Incorrect or unsupported assumptions

- The v1.5 change summary’s claim that the D1 wrong-donor CE dry run was chosen is not true of §13A.8 as written.
- The post-step0/weight-change audit is not currently performed on the three registered R seeds; the D1 sentinel seed is 20261111.
- “Total setup for 3 waves × 4 processes” is not yet defined as wall seconds, although it is added to a wall-time projection.