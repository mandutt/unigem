# C5 F0 v1.4 — Independent Review (Round 4/10)

- Reviewed HEAD: `60c806f95a97e284972a00ba1a0f5b43217e673e`
- Synchronization: `git fetch origin` succeeded; `git pull --ff-only origin main` succeeded (`Already up to date`).
- Scope: consultation only. No training/evaluation, test 163/P1 access, or implementation work.
- Verdict is based on the v1.4 text and the cited Phase 6 source/reference, not inherited from v1.3 conclusions.

## Required verbatim paired E01−E11 definition

From v1.4 §6.2–6.3:

```text
For cell c, seed s, doc d:

delta_c(s,d) = mean_donor( CE_wrong_donor - CE_real )
```

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

The plan also states verbatim: “`D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.” E01/E11 outcomes are unobserved; P−PA is not an observed substitute for this contrast.

## Q1. Init / Stage P / non-reuse

- **Decision: conditional.** The initialization construction is directionally sound: v1.4 §4 (lines 85–122) resets the LoRA seed independently of adapter presence, specifies shared E01/E11 LoRA and E10/E11 adapter initialization, records tensor/base/cache/label hashes, fixes step-seed vectors and canonical serialization, and prohibits modifying Phase 6 `build_arm`. The non-reuse objective is also explicit (§4, line 119; §13A.6, lines 478–482).
- **Blocker — Stage P is internally impossible as written.** §13A.1 (lines 411–416) says Stage P has no updates, but requires assertions 1–8 plus §13A.3. Assertion 5 in §4 (lines 103–112) is `post_step0_rng_state_sha256`; §13A.2 (line 429) defines it as the CPU RNG state after the first optimizer step. §13A.3 (lines 431–435) requires that first optimizer update change E10 adapter, E01 LoRA, and both E11 groups. None can be observed in a no-update Stage P. Move the post-update RNG/weight-change checks to the first R update gate; make P an initialization-only audit with only values defined before any forward/update. Explicitly state whether Stage P’s ≤10 min is inside or additive to the provisional D0 ≤15 min budget (§5, lines 126–142; §13A.1).
- **Non-reuse evidence is not yet independently auditable.** “Phase 6 checkpoint I/O open count = 0” is declared authoritative, but the protocol does not define the exact protected checkpoint paths, what read mechanisms/processes the audit covers, or a positive-control proving a forbidden open is detected. Define the path/API coverage and fail-closed audit, count attempted as well as successful reads, and add a test that a deliberate attempted Phase 6 checkpoint read fails the gate. The audit must be tied to the committed clean-tree code required by §11 (lines 348–360), not just a caller-written zero.
- **Next steps:** resolve the Stage P event/measurement contradiction; specify and test the I/O audit before approving P or D0.

## Q2. D1 schema / stage scope / seal

- **Decision: conditional.** The mechanics-only boundary is substantially improved: §5 (lines 144–173) forbids signal persistence and `d1_report.json`; §11 (lines 351–357) requires a new mechanics evaluator that does not reuse `eval_arm_d1`; §13 (lines 384–407) makes `d1/f0_d1_mechanics.json` the only D1 output and keeps `r/` paths R-only; §13A.4 (lines 437–472) enumerates exact top-level keys and scalar/nested types. The gate’s negative input test is a useful check (§5, line 167).
- **Blocker — schema fields are not fully bound to the pass predicate or storage seal.** §13A.4 gives `mechanics_pass`, `partial`, `checkpoint_digests`, `wrong_donor_ce_calls`, and `donor_map_loads`, but does not define the exact success predicate tying these fields together. The `assertions` object lists five booleans, while the required checks in §5 also include per-cell update counts, E00 optimizer steps, phase7=0, checkpoint deletion, and no wrong-donor/donor-map access. State exact successful values and aggregation rules for every field (including `lora_params`/`adapter_params` and digest-or-null cases), and define crash output (`partial:true`, `mechanics_pass:false`, error, checkpoint cleanup).
- **Blocker — the text declares a one-file boundary but does not specify the filesystem/writer proof.** Add a writer path allowlist and post-success/post-crash filesystem assertion that no units, checkpoints, phase7, sealed/report, or other files were created; add consumer allowlisting and negative tests for forbidden files/keys. This matters because the current Phase 6 implementation does materialize `per_doc`/`delta_shuffled_*` in `eval_arm_d1` (`runner/c5_pm_phase6.py:429–480`) and writes M/phase7/checkpoint artifacts in `run_d1` (`:778–882`). The v1.4 prohibition on reusing it is correct, but the new F0 implementation and seal tests are still required before D0.
- **Next steps:** make `mechanics_pass` a specified conjunction over the complete D1 contract; implement and test the writer, reader, and filesystem allowlists before D1 approval.

## Q3. STOP / MDE / reference dispersion

- **Decision: conditional.** The primary contrast’s sign and the decision taxonomy are coherent: positive `D = E01−E11` favors adapter-free E01; PASS requires `CI_D.lower > +.05`, E01 copy signal, and 2/3 positive seed contrasts (§6.3, lines 215–231); EQUIVALENT is bounded by ±.05 (§6.5, lines 247–255); the ordered `NOT_EVALUABLE` / `PASS_POSITIVE` / `ROUTE_STOP` / `INDETERMINATE` states are exhaustive by construction (§7, lines 264–313). PASS and EQUIVALENT do not overlap. `ALL_FAIL` is correctly limited to E01/E11 × copy/full; E00/E10 are not stop arms (§7, lines 282–312).
- The expected-branch correction is appropriate. v1.4 §12 (line 378) labels `.019170 = .037573/1.96` as the Phase 6 F−L LoRA-contrast planning proxy, not an E01−E11 SE; labels P−PA `+3.0652`, SE `.6209`, `14/15`, SD `2.405` as reference dispersion, not a bound or F0 effect; and identifies `.104`/`.0876` as gate-only power / analytic 50% boundary, not observed F0 means. That matches the primary source’s P−PA result (cause report §2, lines 53–60). Do not use P−PA to classify an F0 branch.
- **Blocker — cell-level CIs that control `SIGNAL` and `ALL_FAIL` are underspecified.** §6.4 (lines 233–245) uses `CI.lower` for each cell’s copy/full `SIGNAL`; §7 uses those signals to determine `ALL_FAIL` and `ROUTE_STOP`. §6.1 says `n_boot=10000` for primary/descriptive bootstrap and §6.2 defines the seed-averaged per-doc cell values, but only §6.3 binds `CI_D` to the explicit `bootstrap_paired_v2(..., seed=20261109)` call and realized-value assertions. §6.4 does not explicitly bind each cell-level `CI.lower` to that helper, seed, percentile/RNG semantics, or equivalent realized-value assertions. The old Phase 6 default is 1,000 (v1.0.11 §10.1–10.3; `runner/c5_pm_stats.py:15–70`), while v1.4 bans `l_predicate` (§6.3, lines 220–225). Specify the per-cell CI call/record contract explicitly; otherwise the `ALL_FAIL`/STOP branch can vary by implementation.
- **Next steps:** freeze the cell-level bootstrap procedure without changing thresholds; keep P−PA descriptive and keep the route-only stop consequence.

## Q4. Cohort / donor / CI

- **Decision: conditional.** The finite estimand is well bounded: 15 frozen `common_ids`, explicitly length-selected from 20 at K=753; 20-doc results are descriptive only; all cells/seeds require all 15 docs and exactly five donors with identical donor sets; missingness is `NOT_EVALUABLE`, never 15→14 (§6.1, lines 189–202; §6.6–7, lines 257–277). The donor map is frozen/hash-recorded; donor reuse from val docs is disclosed, and leave-one-donor-out is descriptive (§6.1, lines 192–200). The paired doc-level bootstrap of seed-averaged `D(d)` is appropriate for the stated estimand, **conditional on this fixed donor graph** (§6.2–3; §12, line 378).
- This supports no population claim for the 20-doc validation cohort and no donor-population CI: the graph has five reused donors, with donor-cluster sensitivity reported only as a range. Keep that limitation in every result label. The v1.4 text already says so; do not weaken it in implementation or reporting. The per-cell CI omission noted in Q3 must be fixed because `SIGNAL` gates the same cohort’s STOP classification.
- **Next steps:** retain the exact frozen IDs/donor map and missingness rules; add the Q3 bootstrap specification; report donor-LOO as descriptive sensitivity only.

## Q5. Compute / 9-term projection

- **Decision: conditional.** The nine terms in §12 (lines 370–380) are a faithful F0 adaptation of Phase 6 v1.0.11 §11.5 (lines 1330–1350): `100*t_train`, step-0 eval 20×5, step-100 eval 20×5, M build, initial M CE, generation 20×256, primary replay, 15×5×2×2×2 replay, and overhead. Using the slowest arm for each of three parallel seed waves is consistent with the stated 4-arm/3-thread, 12-logical-thread R layout; 900 trained updates and the 96-minute hard cap are arithmetically consistent (§5, lines 175–185; §12, lines 364–379).
- **Blocker — setup aggregation is ambiguous in the formula.** `T_proj_R = setup_s_effective + 3 × sum(9 terms for slowest arm)` (§12, lines 371–374), while `setup_s_effective` is described as per-process/per-wave and “4× per wave” for four worktrees. Define whether this scalar already includes setup for all four processes in all three waves. If not, the formula undercounts setup. Freeze the aggregation formula and source timings in the committed orchestrator; include setup exactly once, neither omitted nor double-counted.
- The 4,939.884s wall anchor and Phase 6 D-156 1,180.6s D1 measurement are reference data, not F0 timing validation (§12, lines 370–375). The plan correctly requires committed F0 orchestration before D0 and `nproc>=12`, and says the current 4-vCPU workspace is not a run host (§11, lines 351–360; §13A.7, lines 484–487). No D0/D1/R execution is authorized by this review; R remains contingent on actual parallel F0 timing and `T_proj_R ≤96 min`.
- **Next steps:** define total setup across 3 waves/4 processes; commit the F0 orchestrator; use measured parallel D1 phase timings and enforce the stated 12-CPU/96-minute aborts.

## Q6. Scope / route-only

- **Decision: agree.** Scope is appropriately narrow: one primary E01−E11 contrast (§2, lines 65–71). E11 vs E10 is labeled the LoRA effect with adapter; E10/E01 vs E00 are explicitly confounded, and E01 vs E10 is explicitly not a clean causal contrast (§2, lines 66–71). The causal factor is “adapter-as-configured,” not an architecture-only claim (§4, line 122; §14, lines 498–502). `ROUTE_STOP` stops only EG2 layer19 raw plus this adapter/LoRA configuration; it does not stop EG2 overall, rescue B0-B, or launch H3 (§14, lines 498–502). H3 has no arm/trigger and requires a separate prereg and approval (§10, lines 340–346). M is not donor-specific evidence and is not an F0 primary gate (§9, lines 331–338). Keep test 163/P1 unused and do not auto-advance any downstream phase.
- **Next steps:** preserve these boundaries verbatim in the runner and labels; require separate stage approvals and a separate H3 prereg.

## Final verdict: NARROW

**Do not approve P/D0/D1/R on the current text.** The design is salvageable, but the Stage P no-update contradiction, undefined cell-level CI that controls STOP, and incomplete D1 writer/consumer seal are approval blockers. Resolve the ranked items below in the prereg/code before requesting any stage-specific execution approval. No threshold, seed, donor, step, or LR changes are recommended.

### Must-fix (ranked)

1. **Stage P observability contradiction:** reconcile §13A.1’s no-update P with §4 assertion 5 / §13A.2 post-step0 timing and §13A.3 first-update weight-change checks. Move post-update checks to R; define P as init-only. Also settle whether P’s ≤10 min is inside D0’s budget.
2. **Freeze cell-level `SIGNAL` CIs:** specify per-cell copy/full input construction, seed averaging, n_boot=10000, seed, RNG, percentile method, and realized-stat assertions. `ALL_FAIL`/`ROUTE_STOP` depends on them.
3. **Make D1 seal executable and testable:** exact `mechanics_pass` predicate and successful/partial field values; writer/consumer allowlists; post-success/crash filesystem assertion; negative tests for forbidden signal artifacts and checkpoint access.
4. **Make Phase 6 non-reuse audit falsifiable:** enumerate protected checkpoint paths and complete I/O coverage; test a forbidden read attempt fails; record audit with the committed clean-tree SHA.
5. **Close compute accounting:** define `setup_s_effective` as total setup for the three waves/four processes (or show the equivalent explicit sum), then derive T_proj from committed orchestrator D1 measurements. Keep `nproc>=12`, 25-minute D1 and 96-minute R aborts.

### Wrong premise to avoid

P−PA’s `+3.0652` (14/15) is context/reference dispersion from a different native route, not F0 E01−E11 evidence or a ROUTE_STOP argument. The only registered primary is the paired 15-document E01−E11 contrast quoted above; its CI is conditional on the fixed donor graph, and any conclusion is route-only.