# C5 F0 v1.9 — Independent Review (LUNA)

- **Reviewed HEAD:** `d88d8de1f7641fd44761dadedc8b5d0ffc53498b`
- **Synchronization:** `git fetch origin` and `git pull --ff-only origin main` succeeded; pull reported up to date.
- **Review scope:** v1.9 draft and the requested v1.8/Phase 6 context only. No training/evaluation, no test 163/P1 access, and no subagents. The F0 implementation does not exist yet (`plan v1.9 §11`, lines 351–363).

## Required paired E01–E11 contrast — verbatim from v1.9

> Primary: **E01 vs E11** (LoRA initialization matched).

```text
delta_c(s,d) = mean_donor( CE_wrong_donor - CE_real )
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
```

These are preregistered quantities, not observed F0 results; no E01–E11 outcome exists to report.

## Verdict

**NARROW — do not approve D0, D1, or R from this draft.** The single contrast and its association-only interpretation are appropriately bounded, but the D1 CE counter, P↔R initialization proof, R mechanics predicate, and data-scope test still need auditable definitions. This is an independent v1.9 decision; the archived v1.8 verdict is not carried forward. No threshold, seed, donor, step, or learning-rate change is recommended.

## Q1. D1 CE formula / dry-run

- **Verdict: conditional (not sufficient as written).** The freeze-before-D1 and mismatch→`NOT_EVALUABLE` rule are good (§13A.4, lines 485–503), but the counted operation is not operationally unique: it is defined as `real_memory_ce` per doc×donor×cell×phase, while D1 requires `wrong_donor_ce_calls == 0` and `donor_map_loads == 0` (§13A.4, lines 485–499; §13A.8, lines 525–529). The plan does not say whether D1 evaluates real memory once per doc or repeats it once per each of five donors/crops, nor whether E00 contributes one phase or both: §5 says 20 step-0 and 20 final docs, while §9 says E00 step0=final and one eval (§5, lines 142–171; §9).
- The ambiguity changes the expected count materially. Under one real CE forward per doc-phase and E00 once, the 20-doc mechanics count would be `20 × (1 + 3×2) = 140`; repeating the real call across five donors makes it 700. Counting E00 twice instead gives 160 or 800. These are examples of the unresolved definition, not proposed observed counts. The 15-doc primary donor-crop count must be an independently specified R count, not silently folded into D1.
- Freeze a per-cell/per-phase table with the precise counted function/forward, donor multiplicity, and separate 20-doc vs 15-doc path before D0; bind it to the clean code SHA and command. The instrumented dry-run must independently compare that frozen numeric table to observed call counts and fail closed. It must not compute or retain endpoint deltas.

## Q2. P/Q per-seed schema

- **Verdict: conditional.** v1.9 correctly changes P to `per_seed` and Q to `units:4`, `trained_updates:3`, `e00_updates:0`; 12 units/9 trained updates are aggregates (§13A.1 and §13A.10, lines 419–427, 538–562). This fixes the v1.8 schema's per-file 12/9 aggregate ambiguity.
- The P↔R equality is still only a boolean: `pre_r_init_audit_pass` requires each `p_r_hash_equal:true` (§13A.10, lines 549–559), but Q stores no pre-update parameter/init hash per cell (§13A.10, lines 561–571). Specify which independently built R-equivalent initialization is compared with P and when. Add canonical pre-update init hashes per seed/cell to Q (and compare them at the actual R builder before its first update); a bare `true` cannot establish equality. Make the audit pass false until all 3 seeds × 4 cells have source hashes and verified comparisons.

## Q3. D1 materialization / wall fallback

- **Verdict: conditional.** Exact-key output, no `per_doc`/`delta_*`/`final`/phase-7 objects, digest-only checkpoint handling, post-crash cleanup, and a 25-minute overrun path are materially stronger (§5, lines 160–171; §13A.4, lines 448–503). Keep the dedicated mechanics evaluator: the existing Phase 6 `eval_arm_d1` emits per-doc real/wrong CE and `delta_shuffled_*` fields (`runner/c5_pm_phase6.py:429–489`), so reusing it would violate this seal; v1.9 §11 correctly says not to reuse it.
- The count-only statement should cover returned and logged values, not just persisted JSON. Existing Phase 6 `generate_d1` returns per-ID generation records (`runner/c5_pm_phase6.py:736–762`). F0 must discard generation/M payloads at the producing boundary and expose only counts; test stdout/stderr, temporary/partial files, and crash paths as well as the final writer. The `>25 min` path should be an unconditional hard abort; any repair/re-run or cap change requires a new committed code SHA and explicit D1 re-approval, not an in-place extension.

## Q4. R mechanics / scope boundary

- **Verdict: disagree as a gate; conditional on scope proof.** `r_mechanics_pass.json` currently types `real_memory_ce_calls`, `wrong_donor_ce_calls`, and `donor_map_loads` as integers but defines neither expected values nor a pass predicate for them (§13A.10, lines 564–576). Since `PROTOCOL_VALID` depends on “R mechanics pass” (§7, lines 267–278), an arbitrary count could otherwise accompany a true flag. Freeze per-seed/cell/phase expected counts and define exactly what each counter counts, including the distinct 20-doc mechanics and 15-doc primary path, five donors, and donor-map creation/load semantics. Define `r_mechanics_pass` as equality to those counts plus the 900-update / 1,440-M / 7,200-phase7 checks and provenance.
- The scope rule is correct in principle: filter the frozen train20/val20 allowlist before parsing and test the transitive test-163/P1 read path (§13A.9, lines 531–536; §13A.7, lines 518–523). But this must be demonstrated in F0 code, not inferred from flags. The only current loader, `runner/c5_pm_phase6.py`, reads and JSON-parses every row with `read_jsonl_by_id(DATA)` before constructing/checking `allowed` (`runner/c5_pm_phase6.py:73–98`). The new F0 loader must not reuse that path; its negative test must prove disallowed/test/P1 sources are blocked before row parsing, including transitive imports and crash paths. Keep test 163 sealed and P1 unused.

## Q5. Compute: 8 threads / affinity

- **Verdict: conditional.** Four arms × two worker threads = eight logical worker threads is internally consistent, and the gates are appropriately conservative: D1 ≤25 min provisional, R ≤96 min binding, `nproc <16` or `T_proj_R >96 min` abort, no retry/extension (§12, lines 367–386; §13A.7, lines 518–523). The Phase 6 wall anchors, 1,180.6s and 4,939.884s, are explicitly estimates, not measurements (§12, lines 375–380).
- `nproc` alone does not prove usable CPU quota or worker affinity. The literal D1 schema records `nproc` and `threads_per_arm`, but not effective cgroup quota, allowed CPU set, or the other thread pools (§13A.4, lines 473–476). Record/enforce the actual per-worker affinity and effective quota, plus PyTorch/BLAS intra/inter-op limits, before launching; fail if the four×two plan cannot run as declared. Keep measured D1 timings and the binding 96-minute R wall check. Do not use the current 4-vCPU workspace for a qualifying run (§13A.7).

## Q6. Near-threshold / scope

- **Verdict: conditional.** The scope boundary is appropriate: the primary estimand is the fixed, length-selected 15-doc cohort with five fixed donors; generalization to all 20 is prohibited, and donor reuse is disclosed (§6.1, lines 188–201). The claim is association with the adapter-as-configured, not an architecture-only bottleneck (§4 and §14); E00/E10 comparisons are descriptive (§2). `ROUTE_STOP` is route-only and H3 does not launch automatically (§7, lines 305–316; §10; §14). The Phase 6 reports do not supply F0 results: the cause report confines the native P/PA observation and says M_PASS is not donor-specific evidence (§§1–5 of `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`); its numbers must not be transferred to E01/E11.
- Define the diagnostic margins before R so they are reproducible but remain non-decisional (§7, line 307). For cell signal, state `mean_margin = mean(delta)-.05` for copy and `mean(delta)-0` for full, `ci_margin = CI.lower-0`, and `seed_margin = n_positive_seeds-2` (three seeds; the gate is 2/3 positive). For the primary, separately define `mean_D-0`, `CI_D.lower-.05`, and `count(D_s>0)-2`; define `D_s` as the mean paired contrast over the same 15 docs. Preserve the existing strict/inclusive predicates in §§6.3–6.4; diagnostics must never change them. The `.019170` / `.0376` / `.0537` figures are explicitly planning proxies, not validated E01–E11 precision (§12, line 383).

## Ranked must-fix before any stage approval

1. **D1 CE count contract:** freeze the exact count table, operation semantics, and phase/donor multiplicity; independently instrument and compare before D1. No post-hoc expected count.
2. **P/Q/R initialization proof:** store and compare canonical P and Q/R pre-update hashes per seed/cell; define the comparison timing and make the gate fail closed.
3. **R mechanics predicate:** specify expected per-seed/cell/phase CE and donor-map counts and the complete `r_mechanics_pass` formula; do not accept unvalidated integer telemetry.
4. **Data-scope enforcement:** implement an F0-specific allowlist-first loader and transitive negative tests proving test 163/P1 paths and out-of-allowlist rows are not parsed or consumed.
5. **D1 seal and overrun:** count/discard M/generation payloads at source; test logs and crash/temporary paths; make >25 min a hard abort requiring new code SHA and explicit stage re-approval.
6. **Compute observability:** enforce and record actual CPU set/quota and all thread pools; `nproc` alone is not a capacity proof.
7. **Near-threshold reproducibility:** freeze the signed-margin formulas and `D_s` definition; keep diagnostics non-decisional.

## Incorrect premise / limits

- No F0 implementation or F0 result was available; D1/R counts remain specifications, not verified measurements. No prior v1.8 verdict or Phase 6 outcome establishes an E01–E11 effect.
- This review does not authorize D0, D1, R, test 163, P1, B0-B, or H3.