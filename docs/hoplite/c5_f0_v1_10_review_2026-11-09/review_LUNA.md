# C5 F0 v1.10 — Independent Review (Round 10/10, final)

**Reviewed HEAD:** `de90ebdb16a584a7d406c9b0b325ee8a096daf20`
**Synchronization:** `git fetch origin` succeeded; `git pull --ff-only origin main` reported “Already up to date.”
**Scope:** v1.10 reviewed independently. I did not carry forward v1.9’s verdict. No training, evaluation, test163/P1 access, or tests were run. This review authorizes no stage.

## Verbatim paired E01–E11 from v1.10 §2

> | E01 (F0) | EG2 raw | none | 64 modules | 100 | adapter-free + LoRA |
> | E11 (L) | EG2 raw | trained | 64 modules | 100 | adapter + LoRA |
>
> - Primary: **E01 vs E11** (LoRA initialization matched).

## Q1. CE count/schema/hash

- **Verdict: conditional — not sufficient as currently specified.**
- **Evidence:** §13A.4 freezes a CE operation table before D1 and calls for an independently instrumented expected count (20-doc mechanics and 15-doc donor-crop separated; mismatch → NOT_EVALUABLE). That is the right control in principle. However, the table is not identified as a versioned artifact or digest-bound input in the D1 schema (§13A.4, lines 452–503); the schema exposes aggregate `real_memory_ce_calls`, `expected_real_memory_ce_calls`, and a boolean. For R, the prose requires expected CE counts “per seed/cell/phase,” but `r_mechanics_pass.json` carries only aggregate real/wrong-donor CE and donor-map counts (§13A.10, lines 568–582). A missing operation in one cell/phase could therefore be masked by an extra call elsewhere while the aggregate matches. “Independent instrumented run” also needs a specified, retained source/result and its code/table SHA; it must not simply repeat the same unverified counter path.
- **Next:** Commit/freeze a literal operation-table artifact and hash before D1; record keyed expected and observed counts by cell × phase × operation × endpoint for D1 and R; bind each count artifact to code and input SHAs. Make any missing, extra, or misallocated call fail closed. Keep the canonical tensor serialization/KAT and per-seed/cell initialization comparisons in §4 and §13A.2; those are useful controls, not substitutes for CE accounting.

## Q2. D1 materialization/seal/overrun

- **Verdict: disagree — approval blocker.**
- **Evidence:** The design correctly prohibits signal deltas and per-doc/final objects, allows only a count-oriented D1 output, and requires checkpoint deletion and crash-path checks (§5 D1, lines 165–175; §13A.4, lines 500–507). But a `checkpoint_absent` postcondition does not establish that the checkpoint was never read before deletion; `d1_signal_read:false` is a writer-supplied boolean, not an access audit. The body enumerates post-success/post-crash checkpoint absence and negative tests for selected names, but does not define a complete write/read boundary for temporary, log, stdout/stderr, or crash paths. The v1.10 change summary calls for a “>25 min hard abort,” while §12 only says an over-25-minute wall time requires repair/re-review and no silent extension; the D1 schema has no enforced timeout/abort status or `cap_ok` field (§12, lines 384–390; §13A.4, lines 477–498), despite the orchestrator plan mentioning `cap_ok` (§11, line 361).
- **Implementation boundary:** The existing `runner/c5_pm_phase6.py` is not a compliant F0 D1 implementation: its evaluator materializes per-doc real/wrong CE and deltas (lines 429–475), and its D1 writer emits partial/report, M, phase-7, and checkpoint artifacts (lines 813–882). The v1.10 plan correctly requires a separate mechanics evaluator and says not to reuse `eval_arm_d1` (§11, lines 357–367); that requirement is not yet evidenced by code.
- **Next:** Before any D1 approval, enforce a watchdog that terminates at 25 minutes and can never emit a pass/usable artifact on timeout; bind the timeout result to the reviewed code SHA and require new approval after an overrun. Audit or deny reads of D1 checkpoint paths, and assert the complete allowed filesystem/output set after success, exception, crash, and timeout. Explicitly define which count-only D1 fields R may read: §5 line 175 says D1 “values” must not be read for R/STOP, but §5 line 188 and §7 require reading D1 mechanics/pass information. Clarify that signal-bearing values are prohibited while whitelisted mechanics fields are permitted, or the gates contradict each other.

## Q3. R mechanics/gates

- **Verdict: disagree — approval blocker.**
- **Evidence:** P/Q are useful fail-closed concepts: P compares initialization across all registered seeds/cells; Q requires per-seed one-update, RNG/group-change, and wrong-donor finite/shape checks before R (§13A.1–13A.3, lines 423–450; §13A.10, lines 542–566). But R’s expected keyed counts are not represented in its aggregate output schema, as noted in Q1. In addition, P/Q are separate gates, yet the provenance requirement in §11 names D0/D1/R artifacts only; the P/Q schemas shown in §13A.10 do not require their own code commit, clean-tree state, command, and frozen input SHA. A stale or differently built Q record must not satisfy the per-seed R gate. The broad D1-read prohibition also conflicts with the R gate’s stated D1 mechanics dependency.
- **Next:** Add P/Q provenance and freshness fields, validate them against the approved runner/input manifest, and require exact per-seed/cell R mechanics evidence. Keep any missing, duplicate, malformed, stale, partial, or provenance-mismatched record as NOT_EVALUABLE/no R.

## Q4. Cohort/CI/STOP/near-threshold

- **Verdict: conditional — the primary estimand and STOP taxonomy are mostly coherent, with interpretation details to lock.**
- **Evidence:** The primary is explicitly conditional on the frozen 15 length-eligible common docs and fixed donor graph; 20-doc generalization is prohibited, each doc must have five donors with equal cell donor sets, and donor reuse plus leave-one-donor-out sensitivity are disclosed (§6.1, lines 192–205). The paired doc-level bootstrap uses 10,000 draws and fixed seed; the cell-level CI and seed-sign roles are separated (§6.3–6.4, lines 218–250). The four decision states are exhaustive after PROTOCOL_VALID, and ROUTE_STOP is correctly limited to E01/E11 copy/full failures (§7, lines 269–320). The `SE_D <= .0255` condition is labeled a reachability condition, while realized `CI_D` governs EQUIVALENT/harm/benefit (§12, line 387); it is not a guarantee that equivalence will be observed. The .019170 Phase 6 number is also correctly called an F−L planning proxy, not a validated E01−E11 SE.
- **Caveat:** `m_mean=mean-b` and `m_lower=CI.lower-b` do not identify which frozen boundary `b` means. This design has multiple relevant boundaries (e.g. primary `mean_D>0`, primary `CI_D.lower>.05`, and E01 SIGNAL’s `.05` mean / `0` lower-bound thresholds). Because these diagnostics are non-decisional (§7, line 311), this is not by itself a gate change, but reporting them without named boundaries would be ambiguous. The doc-level bootstrap remains conditional on this 15-doc/fixed-donor setup; it must not be presented as population-level inference.
- **Next:** Name each margin by endpoint and exact threshold; report the realized interval and margins without letting diagnostics change labels. Preserve the fixed-cohort and donor-graph limitations in every interpretation.

## Q5. Compute/scope

- **Verdict: disagree — execution-host and scope checks are not yet demonstrably enforceable.**
- **Evidence:** The workload is explicit (four arms, two threads per arm; D1 ≤25 min provisional; R ≤96 min; (T_{proj,R}) includes nine per-arm terms and setup) and the plan recognizes that cited Phase 6 timings are not F0 timings (§5, lines 151–164 and 177–188; §12, lines 371–390). It also correctly rejects the present 4-vCPU workspace as a run host (§13A.7, lines 522–527). But the change summary asks for CPU set/quota/all thread pools, whereas the D1 `parallel` schema records only `nproc`, `threads_per_arm`, wall time, and contention ratio (§13A.4, lines 479–480); `nproc>=16` alone does not prove usable quota/affinity or that nested thread pools obey the budget (§12, line 386; §13A.7, lines 522–526). Likewise, the F0 allowlist-first loader and transitive access tests are mandatory in prose (§13A.9, lines 535–540), not yet demonstrated by an F0 implementation. The existing Phase 6 loader reads/parses the full JSONL before applying the frozen ID allowlist (`runner/c5_pm_phase6.py`, lines 70–100), so it must not be reused for F0.
- **Next:** Put CPU affinity, effective quota, and actual per-library/thread-pool counts in the gate schema and abort unless the required effective capacity and per-arm limits hold. Implement the separate F0 loader and test the transitive read path before any stage approval; do not treat manifest flags as access proof.

## Q6. Route/limitations

- **Verdict: agree, within the stated scope.**
- **Evidence:** The primary comparison matches E01/E11 LoRA initialization and the plan explicitly defines the causal factor as the configured adapter package (parameters, LR, and adapter-conditioned graph), not an architecture-only effect (§4, lines 99–124). ROUTE_STOP applies only to the named EG2 layer19/LoRA/adapter route; it does not stop the EG2 track, rescue B0-B, or launch H3 (§14, lines 584–597). M_PASS is not treated as donor-specific content-use evidence, H3 is excluded pending a separate prereg, and the residual risk that the wrong-donor numerical path is exercised first at R is declared (§10, lines 347–353; §13A.8, lines 529–533). This is appropriately narrow.
- **Next:** Retain those claim limits. Do not reinterpret F0 as a general EG2 or structural bottleneck test, or as a B0-B/H3 authorization.

## Final decision: **NARROW**

**No D0, D1, P, Q, or R execution is approved by this review.** The hypothesis, contrast, fixed-cohort interpretation, and route limitations are bounded well enough to retain; the preregistration is not ready for stage approval until the blockers below are incorporated and the required F0 implementation is committed and reviewed.

- **Initialization:** Strong intended contract (matched E01/E11 LoRA init, canonical serialization, KAT, group-change checks); P/Q/R provenance and hash binding still need complete stage-level enforcement.
- **D1 seal:** Not adequate yet. Count-only intent is sound, but checkpoint non-access, complete output custody, and an enforceable hard timeout are not proven by the current schema.
- **STOP/MDE:** STOP states are coherent and route-only. The Phase 6 SE/MDE numbers are correctly proxies; realized F0 intervals must decide. Define named near-threshold boundaries.
- **Cohort/CI:** Coherent only for the frozen 15-doc cohort and fixed donor graph; no population generalization.
- **Compute:** Do not use this 4-vCPU workspace. Require effective affinity/quota and bounded thread pools, not `nproc` alone; verify the R wall cap with the actual committed orchestrator.
- **H3:** Correctly excluded; no automatic follow-on.

### Must-fix before any stage approval (ranked)

1. **D1 custody and overrun enforcement:** Add auditable read/write controls for D1 checkpoint, logs, temporary/crash paths and output inventory; enforce the 25-minute hard timeout; make timeout/partial artifacts unambiguously fail closed; reconcile the D1 mechanics read needed by gates with the blanket no-read sentence.
2. **CE accounting contract:** Freeze and hash the actual D1 operation table and its independent expected-count evidence; record expected/observed counts at cell × phase × operation × endpoint granularity for D1 and R, not just totals.
3. **Gate provenance:** Bind P/Q as well as D0/D1/R records to committed clean-tree code, command, input/source hashes, and the serialization KAT; reject stale or mixed-run artifacts.
4. **Effective compute and data scope:** Enforce CPU set/quota and all worker/thread-pool limits in the schema; implement and transitive-test the F0 allowlist-first loader, with test163/P1 paths unopened.
5. **Margin reporting:** Replace the unqualified `b` with named thresholds for each non-decisional margin; keep the fixed-donor/15-doc bootstrap interpretation explicit.

### Incorrect or unsupported assumptions to avoid

- A matching aggregate CE count does not prove each cell/phase executed the correct operations.
- `nproc >= 16` alone is not evidence of 16 usable CPUs or controlled nested thread pools.
- `checkpoint_absent` and a self-reported `d1_signal_read:false` do not prove the checkpoint was never read.
- The present Phase 6 runner is not the required F0 runner; its D1 writer persists artifacts that v1.10 forbids for F0.
- This experiment cannot establish a population-level 20-doc/general EG2 conclusion, an architecture-only bottleneck, a B0-B rescue, or an H3 trigger.