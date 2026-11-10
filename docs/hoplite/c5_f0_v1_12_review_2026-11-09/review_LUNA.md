# C5 F0 v1.12 — Independent Review (Luna)

**Reviewed HEAD:** `f994c1033729f2ebe2705bcad335a5f19d7018d6`  
**Workspace sync:** `git fetch origin` succeeded; `git pull --ff-only origin main` succeeded (`Already up to date`).  
**Status:** F0 remains unapproved and unimplemented. This review did not run training, evaluation, tests, test 163/P1 reads, or any experiment. Only this review report is added.

The v1.10 plan and review syntheses were read as design history and evidence, not as inherited verdicts. The findings below are based on v1.12’s actual normative text and the available Phase 6 source.

## Verbatim paired E01–E11

From v1.12 §2 and §6.3:

```text
- Primary: **E01 vs E11** (LoRA initialization matched).
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
```

This is the contrast I reviewed; it is not a comparison to E00, E10, or Phase 6 L.

## Q1. Donor count / D1 custody

- **판정: disagree — the design boundary is sensible, but the seal is not yet proven.** v1.12 correctly makes the five-donor assertion R-only and keeps D1 `donor_map_loads` and `wrong_donor_ce_calls` at zero (§0, items 1 and 4; §13A.4–.5; §13A.8). It also prohibits signal/per-doc/final output and requires digest-only D1 checkpoints (§5, lines 158–168; §13A.4, lines 486–499).
- The crash guarantee is still a process-level assertion: the D1 worker is said to write `partial:true`, record an error, and delete checkpoints (§13A.4, lines 496–499), but no external watchdog/finalizer behavior, atomic failure-record write, or post-kill inventory procedure is specified. A hard kill, host loss, or OOM kill can prevent the worker from writing the failure record and cleaning its checkpoint. The change summary promises an allowed filesystem delta, success/crash inventory, and sanitized logs (§0, lines 30–31), but the normative artifact contract does not define that inventory or a log path/redaction test; it only says logs must not print CE values (§13, lines 405–412).
- Reuse of Phase 6 `eval_arm_d1` is unsafe: the existing `run_d1` passes donor maps to step-0/final evaluations, writes phase7 records, captures `final`, checkpoints, and incremental partial output (`runner/c5_pm_phase6.py:801–823, 824–852`). v1.12 correctly requires a new F0 mechanics runner and says no F0 code is implemented (§11, lines 348–360); this remains a precondition, not completed evidence.
- **Next:** implement and review the F0 runner plus an external watchdog that enforces the deadline, kills/joins all workers, removes checkpoints and scratch outputs, and atomically emits one allowlisted fail-closed record after success or failure. Demonstrate success, timeout, worker crash, and forced-kill inventories before approving D1.

## Q2. Overrun / provenance

- **판정: disagree.** The 4,939.884s value is now correctly identified as D-157 at two threads per arm and explicitly not an F0 measurement (§0, item 3; §12, lines 372–377). That correction is adequate; it is not an F0 runtime estimate.
- The claimed single overrun rule is inconsistent with the stage table: §0 says `>25 min` is the shared hard-abort rule including D0 (line 23), while D0 is capped at 15 minutes and says to repair first if it exceeds 15 (§5, lines 135–137; §12, line 368); D1 has a 25-minute cap (§12, line 377). State the actual D0 and D1 watchdog deadlines and the exact partial/cleanup/re-approval behavior for each. A recorded `parallel_wall_s` is not hard-abort enforcement.
- D1’s provenance fields (`code_commit`, `command`, `input_sha256`, `clean_tree`) are appropriate starting points (§13A.4, line 471), but there is no F0 implementation to inspect and the R schema does not define the same provenance contract. `§11` requires F0 code to be committed before D0; hold all stage approvals until the runner/orchestrator and its clean-tree/input binding are reviewed.
- **Next:** reconcile the stage-specific caps in §0/§5/§12 and make the watchdog/finalizer part of the committed, hash-bound implementation before any D0 approval.

## Q3. Wrong-donor / error enum / expected counts

- **판정: disagree — the gate schemas do not yet bind the operations they claim to gate.** Q is the first numerical wrong-donor execution and should persist no signal values (§13A.1, lines 419–423; §13A.8, lines 522–526). But `q_seed_audit` records `wrong_donor_ce_calls:int` while `pre_r_seed_audit_pass` is defined only by unit presence/pass and finite/shape booleans (§13A.10, lines 548–560); it does not compare that call count to a frozen expected number. A zero, duplicate, or omitted call could therefore be invisible to the stated gate if the booleans are wrong or stale.
- For R, the schema lists only aggregate `updates_total`, `m_records`, `phase7_records`, and observed CE/donor-load counts; the required per-seed/cell/phase expected-count table is deferred to “frozen before R” and is not actually specified (§13A.10, lines 562–576). `r_mechanics_pass` is said to compare all expected counts, but the exact expected real/wrong CE calls, donor-map loads, and endpoint/phase breakdown are absent. D1’s operation table is likewise described but not included as literal rows (§13A.4, line 494). Counts must be independent expectations, not values generated by the run being checked.
- The D1 error enum is usefully closed (`TIMEOUT`, `OOM`, `CE_NONFINITE`, `SHAPE_MISMATCH`, `CHECKPOINT_DIGEST_FAIL`, `OTHER_REDACTED`; §13A.4, line 490), but Q has no parallel failure schema, and the spec does not say how raw exception text/tracebacks are prevented from entering logs. The token `OTHER_REDACTED` alone does not enforce redaction.
- **Next:** freeze the operation tables before their respective stages; include exact Q wrong-donor call expectations and R real/wrong CE and donor-load expectations by seed/cell/phase/doc/donor/copy/full; make every count an explicit fail-closed predicate. Define closed Q/R failure codes and prohibit raw exception/value logging.

## Q4. Near-threshold / EQUIVALENT

- **판정: conditional.** The normative decision logic is coherent: paired doc-level `CI_D`; `EQUIVALENT` iff the realized 95% interval is inside `[-.05,+.05]`; `.0255` is only a nominal planning threshold (§6.3–6.5, lines 211–253; §7, lines 282–305; §12, line 380). The fixed 15-document/fixed-donor estimand is explicitly conditional, not population inference.
- The review question contradicts that rule: §15 Q4 describes EQUIVALENT as `SE_D<=.0255` (line 609), which is expressly not the decision criterion. The near-threshold line also sets `m_mean=mean-b` and `m_b=m_mean` while requiring both b values `{+.05,0}` (§7, line 304); specify a per-b output table and avoid duplicative names. These are report/spec consistency fixes, not a reason to replace the realized-CI rule.
- **Next:** correct §15 Q4 and define the two non-decisional margin rows. Keep `.0255` out of all outcome gates.

## Q5. Compute / CPU custody

- **판정: disagree.** The plan correctly says the current four-vCPU workspace is not a qualifying host and requests four arms × two threads with a 16-core host (§13A.7, lines 515–520). However, `cpu_affinity`, `cgroup_cpu_quota`, `torch_threads`, and `thread_pool_counts` appear in the D1 `parallel` object only (§13A.4, line 472). The R stage specifies just `nproc`, `threads_per_arm`, wall time, and contention (§5, line 178); the R mechanics schema has no CPU fields (§13A.10, lines 562–576), and `r_mechanics_pass` does not gate on effective CPU allocation. The `nproc < 16` check (§12, line 379) does not prove that the four workers have the required effective affinity/quota or that hidden BLAS/OpenMP pools are bounded.
- **Next:** record and validate effective cpuset/affinity, cgroup quota, and actual Torch/BLAS/OpenMP thread pools for each worker and R wave. Make minimum capacity and no-oversubscription assertions part of the R gate, not telemetry. Do not run on the documented four-vCPU workspace.

## Q6. Scope / route

- **판정: conditional (scope accepted; donor identity is a blocker).** The scientific claim is appropriately narrow: adapter-as-configured in this fixed EG2/LoRA route, association-only, with route-only `ROUTE_STOP`, H3 excluded, and no generalization from the 15 length-eligible documents (§1–2, §6.1, §8, §10, §14). Phase 6 evidence also cautions that M is not donor-specific evidence and does not establish an EG2-wide mechanism (C5 Phase 6 cause report, §§1–2, §8). Keep those limits in the final report; do not promote the result to an architecture/bottleneck claim.
- R donor provenance is underspecified. §6.1 names `donor_map_sha256` and a per-document donor-ID hash but gives no canonical map encoding, row schema, or independently inspectable mapping; §13A.5 asserts only `evaluated_donors==5` (§§6.1, 13A.5, lines 187–196 and 501–504). Five donors proves cardinality, not correct identities, self-exclusion, or the frozen length-nearest ordering. The prior normative donor rule is candidates = other val20 IDs, sorted by `(abs(length difference), doc_id)`, first five (Phase 6 prereg §2.5.6, lines 276–299). The existing Phase 6 phase7 artifact uses the ordinal `donor_id` index rather than the actual donor ID (`runner/c5_pm_phase6.py:693–725`), so do not assume that legacy artifact proves identity.
- **Next:** define a canonical, auditable per-doc donor map (or an artifact containing the map plus its hash), independently validate the five expected IDs/order and self-exclusion, and assert equality across cells/seeds before labels are computed.

## Final verdict

**NARROW — not approved for execution.** The endpoint and route scope are reviewable, but the custody/timeout enforcement, count gates, effective CPU gate, R donor identity, and absent F0 implementation are approval blockers. Do not start D0, D1, Q, or R until the ranked must-fixes below are resolved in a committed version and the applicable stage receives explicit approval. This is not a STOP of the broader EG2 track and does not authorize H3.

### Ranked must-fix

1. **D1 custody and executable overrun control:** implement the separate F0 runner and external watchdog/finalizer; reconcile the D0 15-minute versus shared `>25 min` wording; prove atomic fail-closed output, checkpoint/scratch cleanup, and success/crash/forced-kill inventories. No stage approval without this.
2. **Frozen CE/count gates:** publish the literal D1/Q/R operation tables before use; make Q `wrong_donor_ce_calls` and every R CE/donor-load count equality mandatory gates; specify failure codes and log redaction. Current aggregate R totals are not a substitute for the table.
3. **R donor identity/provenance:** define the canonical donor-map serialization and schema, record an auditable map plus digest, and independently verify intended IDs/order/self-exclusion across cells and seeds. `evaluated_donors==5` is insufficient.
4. **Effective CPU gate:** put affinity/quota/thread-pool measurements in R artifacts and gate against effective capacity/oversubscription, not `nproc` alone.
5. **Normative text consistency:** change §15 Q4 so it no longer calls `SE_D<=.0255` EQUIVALENT; define the `m_mean`/`m_b` rows for each b. The realized-CI equivalence rule itself is accepted.

### Initialization / cohort / compute / H3

- **Initialization:** matched LoRA initialization is a defensible control for E01−E11; this identifies adapter-as-configured, not adapter architecture alone (§4, lines 75–117).
- **D1 seal:** the intended no-signal contract is good; the crash and read-prevention proof is not yet implemented. `d1_signal_read:false` is an assertion, not an access audit by itself.
- **STOP/MDE:** use realized `CI_D`; `.0255` and the historical F−L proxy are planning context only (§12, line 380).
- **Cohort:** exactly 15 common length-eligible documents, three seeds, fixed donor graph; no 20-document population or broader EG2 claim (§6.1, §6.6, §14).
- **Compute:** no qualifying F0 implementation/host proof in this checkout; the plan itself excludes the current four-vCPU workspace (§13A.7).
- **H3:** out of scope and requires a separate prereg/approval (§10).

### Incorrect premises to correct

- `nproc>=16` is not evidence of 16 effective CPU cores or bounded thread pools.
- `evaluated_donors==5` is not evidence that the intended donor identities were evaluated.
- `.0255` is not the EQUIVALENT decision threshold; the realized 95% `CI_D` is.
- A successful child-process flag or a `partial` field does not, by itself, prove cleanup after a forced kill.
- Phase 6 association results and M_PASS do not establish donor-specific EG2 mechanism or broader track conclusions.