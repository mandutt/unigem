# C5 F0 v1.11 — Independent Review (New Block, Round 1/10)

- **Reviewed HEAD:** `5aa18b1c857a29b3190b683098e3f098f1ce4063`
- **Synchronization:** `git fetch origin` succeeded; `git pull --ff-only origin main` succeeded (`Already up to date`). The worktree was clean before this report.
- **Status:** v1.11 remains a draft; this review does not approve any stage or authorize execution.
- **Independence:** v1.10 and its synthesis were read as history, not adopted as conclusions. Findings below are from v1.11 and the source present at the reviewed HEAD.
- **Activity boundary:** consultation only; no training, evaluation, test 163/P1 access, or subagents.

## Verbatim paired E01−E11 primary

From `docs/plan_c5_f0_v1_11_2026-11-09.md` §6.3 (lines 219–225):

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
assert realized.n_boot == 10000 and realized.seed == 20261109
assert not used_l_predicate
```

## Q1. CPU / D1 custody

- **Judgment: conditional — not sufficient to approve D1.** The custody design is materially narrower than Phase 6 and its intent is sound, but the implementation contract does not yet prove the stated seal or compute capacity.
- **Evidence:** v1.11 §5 (lines 164–172) limits D1 to one mechanics file, bars signal/per-document persistence, and says checkpoints are digest-only/deleted. §13A.4 (lines 503–505) specifies writer/consumer allowlists and checkpoint/forbidden-payload tests. However, the v1.11 change summary claims logs/temp/crash paths were tested (§0 item 11, lines 40–41); the body does not enumerate those paths or define a before/after filesystem inventory. §13 lines 411–417 prohibit CE values in stdout/logs and name the D1 artifact, but do not establish crash-log/traceback redaction or temporary-file cleanup.
- The new `parallel` fields (`cpu_affinity`, `cgroup_cpu_quota`, `torch_threads`, `thread_pool_counts`) occur in the D1 schema only (§13A.4, line 478). R records only `nproc`, `threads_per_arm`, `parallel_wall_s`, and `contention_ratio` (§5, lines 182–185; §12, line 384), despite §0 item 1 claiming these fields were added to parallel/R provenance. No units/source contract or fail-closed effective-CPU calculation is specified. The `nproc < 16` abort (§12, line 385) is not tied to a quota/affinity rule.
- The current Phase 6 runner demonstrates why it cannot substitute for the planned F0 runner: `eval_arm_d1` returns `per_doc` CE values (`runner/c5_pm_phase6.py`, lines 429–489); `run_d1` invokes it for step0/final, writes checkpoints, and persists phase-7/control artifacts (lines 804–835), then writes `d1_partial.json` (lines 838–853). The F0 plan correctly calls for separate files and explicitly says not to reuse `eval_arm_d1` (§11, lines 354–365); that boundary must be enforced in code.
- **Next step:** before D1 approval, implement and test a complete success/crash filesystem allowlist (including logs, temp files, tracebacks and checkpoint deletion); specify sanitized crash output; add CPU fields and an effective-capacity gate to R’s actual schema and orchestrator. Do not reuse the Phase 6 runner.

## Q2. Wrong-donor execution / error enum

- **Judgment: disagree — the v1.11 Q contract is internally inconsistent.**
- **Evidence:** §0 item 3 says the Q schema adds `wrong_donor_ce_calls` (line 25), and §13A.8 says Q is the first wrong-donor execution and that its schema records this counter (line 530). But the literal per-seed Q schema in §13A.10 (lines 553–564) contains only `wrong_donor_finite` and `shape_ok`; it has no `wrong_donor_ce_calls`. Thus the claimed execution count cannot be checked against an expected count. Q’s prose says it runs donor-crop/wrong-donor CE checks without persistence (§13A.1, lines 427–429), but does not give a frozen, per-cell/per-doc/per-donor expected-call contract.
- D1’s `wrong_donor_ce_calls: 0` is explicit (§13A.4, line 490), and D1 is explicitly forbidden from calling wrong-donor CE (§13A.8, line 529); that separation is coherent. The crash enum is also explicit for D1 (`TIMEOUT`, `OOM`, `CE_NONFINITE`, `SHAPE_MISMATCH`, `CHECKPOINT_DIGEST_FAIL`, `OTHER_REDACTED`; §13A.4, line 496). It is not specified for Q, whose schema has no `partial`/`error` fields or crash-output rule. The prohibition on CE values in logs (§13, line 411) needs to cover Q exceptions and tracebacks as well as ordinary output.
- **Next step:** add the Q count and its independently frozen expected value(s) to the literal schema; define a redacted, fail-closed Q crash record and log policy. Preserve the no-persistence rule for Q numeric CE values and the D1 zero-wrong-donor-call rule.

## Q3. Donor count / overrun / provenance

- **Judgment: disagree — the claimed single overrun rule and provenance are not implemented consistently in the text.**
- **Evidence:** §0 item 6 states `>25 min: hard abort, partial, new code SHA + explicit stage re-approval` and says §0/§5/§12 are aligned (lines 30–31). But §5 D1 says only “cap ≤25 min parallel” and calls it provisional (line 163); §12 says an overrun requires “repair or re-review; no silent extension” (line 383). Neither states the hard-abort/partial/new-SHA/re-approval sequence. The D1 schema permits `TIMEOUT` and `partial` (§13A.4, lines 496, 502), but does not itself enforce the stated timer or re-approval gate.
- The D-157 anchor contradicts itself: §12 line 378 says `4,939.884s` was measured at 2 threads/arm and is not an F0 measurement; §12 line 382 calls the same Phase 6 registered value an estimate and “not a measurement.” The correct distinction must be explicit: it is a prior Phase 6 measurement, not an F0 measurement; it may be an F0 planning anchor only if labeled as such. D1’s `1,180.6s` is likewise a Phase 6 measurement at 3 threads/arm, not F0 (§12, line 378).
- The metadata/runtime distinction is conceptually correct (§0 item 5, line 29; D1 `donor_map_loads: 0`, §13A.4 line 491). However, D1’s schema has no frozen `donor_count` field or reference to a separately hashed frozen operation-table artifact; §13A.4 line 500 describes that table only in prose. §13A.5 says to require `evaluated_donors == expected_donors == 5` per doc/cell (lines 507–509), but does not identify the persisted, hash-bound record carrying those values. R’s expected counts are also described as an exact pre-frozen table without a path/hash or a literal per-phase expected-count schema (§13A.10, lines 566–580).
- **Next step:** unify the D1 timeout rule verbatim across §§0/5/12 and the executable gate; specify the D1 and R overrun artifact/reapproval state. Correct the D-157 wording. Persist and hash-bind the frozen CE/donor-count table, while keeping metadata donor count distinct from runtime donor-map loads.

## Q4. Near-threshold / EQUIVALENT

- **Judgment: conditional — the decision rule is mostly coherent, but two diagnostics are underspecified.**
- **Evidence:** the primary positive gate is strict (`CI_D.lower > +.05`) (§6.3, line 229); practical equivalence is inclusive at the limits (`CI_D.lower >= -.05` and `CI_D.upper <= +.05`) (§7, line 288). §6.5 correctly labels this nominal practical equivalence, not population equality (lines 254–259), and §7 says the realized CI governs (line 310). The 15-doc conditional cohort and no-substitution rule are explicit (§6.1, lines 194–203; §6.6, lines 261–266).
- §12 line 386 says EQUIVALENT reachability “requires realized `SE_D <= .0255`,” but does not define `SE_D`; `.0255` is `.05/1.96`, not a general identity for the width of the specified percentile bootstrap CI. Keep the realized percentile CI as the sole classification rule; define this as an approximate diagnostic (if retained), not a necessary gate.
- §7 line 310 varies `b` over `{+0.05, 0}` for signed margins but defines `m_sign=(#seeds>0)-2` for both values. That is a zero-threshold seed-sign diagnostic, not a margin relative to `b=+.05`. State that distinction or define the b-relative sign margin separately; diagnostics remain non-decisional.
- **Next step:** define `SE_D`, mark `.0255` as non-decisional approximation or remove it, and disambiguate `m_sign` without changing any frozen threshold or seed gate.

## Q5. R donor identity / hash

- **Judgment: disagree — the identity intent is good, but the hash contract is not implementation-grade.**
- **Evidence:** §6.1 defines `donors_for(val20, cache)`, says `donor_map_sha256` is recorded in `init_hashes.json`, and says R records that hash plus per-doc donor-ID hashes and asserts equality (line 197). It also requires exactly five donors and identical donor sets across cells (§6.1, line 200; §13A.5, line 509). However, no canonical serialization/preimage is defined for either donor hash (unlike the explicit ID/tensor serialization rules in §4, lines 115–119 and §13A.2, lines 431–442). The only literal R mechanics schema (§13A.10, lines 566–580) does not include `donor_map_sha256` or per-doc donor-ID hashes, nor does it define which artifacts/seed-cell records are compared. The prose assertion therefore cannot yet be audited or implemented unambiguously.
- **Next step:** add a literal R report schema containing the frozen donor-map digest and per-doc donor-ID digests, define canonical bytes/order and hash algorithm, bind them to the frozen inputs and runner/code SHA, and assert equality across all cells/seeds. Validate five unique, non-self donors per eligible doc before accepting R.

## Q6. Scope / route

- **Judgment: agree, subject to preserving the stated claim boundary.**
- **Evidence:** the contrast is limited to E01 vs E11 with LoRA initialization matched (§2, lines 61–68); §4 correctly states that the tested factor is `adapter-as-configured`—adapter parameters, LR, and adapter-conditioned graph—not an architecture-only adapter effect (line 123). §14 explicitly limits the claim to association in this fixed EG2/LoRA route, makes `ROUTE_STOP` route-only, disclaims population/causal generalization from descriptive contrasts, and keeps H3 out of scope (lines 591–595). H3 also requires a separate preregistration/approval (§10, lines 346–352); test 163/P1 and downstream B0/B1/B2/Stage C are excluded (§14, lines 584–590; §17, lines 642–650). Phase 6’s native-path cause report does not establish an EG2 result ( `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md` §5, lines 103–110).
- **Next step:** retain the fixed-route, association-only wording; do not infer an EG2-wide mechanism, rescue B0-B, or launch H3 from this result.

## Freshness check against historical material

`reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md` §3 (line 41) says the Phase 6 runner rejects `--mode registered`. At the reviewed HEAD, `runner/c5_pm_phase6.py` accepts `registered` in the choices (line 948) and dispatches it (lines 960–964). That historical statement is stale at this HEAD; it is not evidence that F0 code exists. The current v1.11 plan itself says no F0 code is implemented and requires separate F0 runner files and stage approval (§11, lines 354–366).

## Final decision

**NARROW — do not approve or execute D0, D1, Q, or R from this draft.** Continue only with spec correction, implementation, and review against the corrected contract. No stage approval is granted here. D0/D1/R each require separate explicit stage approval (§11, line 366); v1.11 is expressly unapproved/unexecuted (§0, lines 1–11).

- **Initialization:** design contract is reviewable (seed reset, matched LoRA initialization, and hash assertions; §4, lines 81–123), but F0 implementation is absent (§11, lines 354–365). “LoRA fixed” means initialization matched, not trained weights equal (§4, line 121).
- **D1 seal:** not approved until the exact success/crash filesystem boundary, log redaction, and enforced timeout/reapproval contract are complete.
- **STOP/MDE:** the state taxonomy and frozen realized-CI rule are understandable (§7, lines 268–319); correct the `.0255` reachability wording before using it as any gate.
- **Cohort/CI:** the fixed 15-doc estimand, same-doc pairing, 3-seed completeness, and no-substitution rule are explicit (§6.1–6.6). Claims remain conditional on this donor graph, not population inference.
- **Compute:** sandbox status at review time reports a box-limited 4 vCPU (`burstLimit` 4), while §13A.7 requires 16 cores; this workspace is not a qualifying host, so no F0 execution here. R must also record and enforce effective CPU quota/affinity rather than merely log `nproc`.
- **H3:** out of scope; no automatic trigger or rescue path.

### Must-fix, ranked

1. **D1 safety/overrun enforcement:** define and test the complete allowed filesystem delta (success and every crash path), sanitized logging, hard timeout/partial behavior, checkpoint cleanup, and new-code-SHA plus explicit stage re-approval. Align §§0/5/12 (§5, lines 163–174; §12, lines 378–389; §13A.4, lines 496–505).
2. **Q and R count/error schemas:** add Q `wrong_donor_ce_calls` and independently frozen expected counts; specify safe crash/error handling for Q. Persist/hash-bind the donor-count/CE operation table and make R expected counts literal, auditable fields (§0, lines 23–31; §13A.4, lines 487–501; §13A.8–10, lines 527–580).
3. **Correct provenance statements:** resolve the D-157 `4,939.884s` contradiction and distinguish Phase 6 measured time from any F0 estimate (§12, lines 378–383).
4. **R donor identity binding:** define canonical donor-map/per-doc donor-ID hash inputs and serialize them in the literal R report schema; assert the frozen mapping is identical across all cells/seeds (§6.1, line 197; §13A.10, lines 566–580).
5. **Compute contract:** define effective CPU/quota/affinity units and minimums, enforce them in the orchestrator, and record them in R provenance as well as D1 (§5, lines 182–185; §12, lines 384–385; §13A.4, line 478; §13A.7, lines 520–525).
6. **Decision diagnostics:** define `SE_D` and the non-decisional status of `.0255`; distinguish the zero-based seed sign from a `b`-relative signed margin (§7, line 310; §12, line 386).

### Incorrect or incomplete premises in v1.11

- §0 item 3 claims the Q schema includes `wrong_donor_ce_calls`; the literal Q schema in §13A.10 omits it.
- §0 item 6 claims the overrun wording is aligned; §§5 and 12 omit the stated hard-abort/partial/new-SHA/reapproval rule.
- §0 item 7 correctly calls D-157 “measured, not F0,” but §12 line 382 calls the same 4,939.884-second Phase 6 value “not a measurement.”
- §0 item 1 says CPU observability was added to R provenance; R’s listed fields in §§5/12 do not include the added affinity/quota/thread-pool fields.