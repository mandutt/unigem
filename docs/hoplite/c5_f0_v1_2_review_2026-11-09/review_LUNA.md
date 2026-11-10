# C5 F0 v1.2 Independent Review — LUNA

## Review identity and boundary

- **Reviewed HEAD:** `f2525253efeb7de49d35a355b25c22b481594178`
- **Workspace synchronization:** `git fetch origin` succeeded; `git pull --ff-only origin main` succeeded (`Already up to date`).
- Reviewed the v1.2 request and prereg, v1.1 prereg, v1.0/v0.9 review syntheses, Phase 6 cause/results materials, Phase 6 prereg, and `runner/c5_pm_phase6.py` as requested. This is an independent v1.2 review; prior verdicts are cited only as source evidence, not inherited.
- No training, evaluation, test-163/P1 access, or subagents. The F0 draft itself states it is unapproved/unexecuted and has no implemented F0 code (§0, lines 4–11; §11, lines 349–359).

## Final verdict: **NARROW**

**Do not approve D0, D1, or R yet.** The estimand and route-only scope are mostly bounded, and the STOP table is coherent, but D1's claimed exact contract is not actually specified as a schema, initialization checks are not staged for all registered seeds before R, and the present workspace cannot meet the hard `nproc >= 12` gate. The forecast/power narrative also treats Phase 6 arm results as more predictive of a different F0 contrast than the evidence warrants. These are fixable prereg/implementation gates, not grounds to stop the EG2 track.

## Verbatim paired E01–E11 definition (v1.2 §6.3, lines 218–229)

```text
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
mean_D = mean_d D(d)
CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000
```

> `D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.

This is a **planned estimand**, not an observed F0 result: v1.2 is unexecuted (§0, lines 4–11). Do not label the Phase 6 F/L cell values as paired E01−E11 data.

## Q1. Initialization — **conditional**

The structure is substantially improved: the adapter-independent LoRA seed reset, per-step reseeding, paired E01/E11 LoRA-name and tensor hashes, adapter hash, base/cache/label hashes, and a separate Phase 6 checkpoint prohibition are appropriate (§4, lines 88–125). I independently checked the listed `step_seed` vectors against the formula in §4, lines 116–120; the listed values match.

Approval blockers:

1. **The all-registered-seed check has no defined pre-R stage.** §4, line 106 says assertions are per registered seed, and the change summary says all three registered seeds are checked before R (§0, lines 27–30). But D0 and D1 each specify only seed `20261111` (§5, lines 129–145 and 147–175); R uses `20261108/09/10` (§5, lines 178–188). Specify a no-update initialization audit for all three R seeds before R, its artifact and gate, and include its time in the D0/compute accounting.
2. **The canonical tensor byte grammar is not yet canonical enough to implement independently.** `name_len|dtype|ndim|shape|nbytes|LE bytes` (§4, line 120) omits the byte encoding and fixed-width/endian rules for lengths, dimensions and shape, canonical dtype/name encoding, and concatenation boundaries. Give a byte-level serialization grammar and hash test vectors. Define exactly when `post_step0_rng_state_sha256` is captured and what “step0” means (§4, lines 110–121).
3. **The weight-change assertion is too weak.** “At least one LoRA/adapter parameter changes” (§4, line 115) can pass if one expected trainable group is frozen or disconnected while another changes. Require the expected group(s) to change in each trained cell (E10 adapter; E01 LoRA; E11 both), with the check tied to the first optimizer update.
4. Canonicalize Phase 6 paths and ensure the I/O audit covers every checkpoint-loading path, not only an uncanonicalized `open`/`torch.load` string match (§4, line 122). Keep the separate F0 builder and clean committed driver requirement (§11, lines 349–358).

**Next:** define the pre-R three-seed audit; freeze byte serialization/capture points; require per-cell trainable-group changes and canonical-path non-access evidence.

## Q2. D1 seal — **disagree as written; conditional after contract completion**

The central decision to create a separate mechanics evaluator and prohibit `eval_arm_d1` is right. The cited Phase 6 implementation demonstrates why: `eval_arm_d1` computes wrong-donor CE, deltas and `per_doc` (§`runner/c5_pm_phase6.py`, lines 429–489); `run_d1` invokes it for step0/final, writes Phase 7 records and checkpoints, and emits partial/complete reports and M records (lines 778–883). F0 must not reuse that path.

However, v1.2 does **not** publish the promised literal allowlist/schema. It says `f0_d1_mechanics.json` is the only output and requires an exact-key allowlist (§5, lines 166–174), but lists no actual permitted keys, types, or nested-field rules. There are also three unresolved semantics:

- §5, line 176 says D1 values must not be read for Stage R or STOP, while line 188 says the Stage R driver reads `f0_d1_mechanics.json`. Restrict this explicitly to **mechanics pass/fail fields only**; state that no D1 signal/endpoint values can affect R or STOP.
- The summary prohibits wrong-donor CE (§0, line 33), while D1 requires “all CE finite” (§5, line 161). Define which CE is allowed (e.g. training/real mechanics loss only) and explicitly exclude donor-signal CE computation, not merely its persistence.
- `labels_computed:false` is defined as “decision labels only” (§0, line 33), although mechanics/training necessarily form token labels. Rename it to an unambiguous field such as `decision_labels_computed:false`, or define the literal field semantics and test them.

The checkpoint digest/delete/absent and phase7 filesystem checks are useful (§5, lines 158–175), but the contract also needs a complete output-path allowlist and a recursive no-extra-artifact assertion for success and crash paths. The negative input test alone does not establish output non-access/non-persistence.

**Next:** publish exact JSON keys/types and allowed values; reconcile the three contradictions above; test filesystem state and sanitized failure behavior for both successful and crashing D1 runs.

## Q3. STOP/MDE — **conditional**

The **taxonomy is coherent** as specified (§7, lines 265–312): `PASS_POSITIVE` requires `CI_D.lower > +.05`, whereas `EQUIVALENT` requires the whole interval within `[-.05,+.05]`, so they cannot overlap for a valid ordered CI. `ALL_FAIL` is exactly the four E01/E11 copy/full cell signals; it cannot coincide with PASS because PASS requires `SIGNAL(E01,copy)`. `INDETERMINATE` is the remaining valid-protocol state. Route-stop reason precedence is also explicit. Keep this route-only consequence, not an EG2-track conclusion (§14, lines 411–415).

The **arithmetic** in §0, lines 19–26 and §12, line 375 is consistent if `SE=.019170` and half-width `.037573` are used as the planning inputs:

- observed-CI crossing boundary: `.05 + .037573 = .087573` (≈`.0876`);
- approximate 80%-power mean for the strict lower-bound gate: `.05 + .037573 + 0.8416×.019170 = .1037` (≈`.104`);
- symmetric-interval EQUIVALENT mean range: `±(.05 − .037573) = ±.012427` (≈`±.0124`).

But these are **not validated F0 power estimates**. The cited Phase 6 paired contrast is F(adapter, no LoRA) vs L(adapter + LoRA) (Phase 6 prereg §2.1, lines 127–130); F0's primary is E01(no adapter + LoRA) vs E11(adapter + LoRA) (F0 §2, lines 62–74). The Phase 6 cause report gives F-vs-L paired contrast `−0.0026` (§2, lines 45–51), while v1.2's `−.111/−.1135` are historical arm-level signal means (§0, line 25), not the new E01−E11 contrast. Thus the historical SE is at most an explicitly labeled planning proxy, and “ALL_FAIL→ROUTE_STOP more likely” is not established for the new pair. Also rename “observed boundary” to make clear `.0876` is a calculated CI-crossing boundary, not an observed F0 mean.

**Next:** retain the thresholds and coherent state table, but label the SE/MDE as a Phase 6 proxy with sensitivity bounds; remove or qualify the ALL_FAIL forecast and “observed” wording. Do not tune thresholds from this review.

## Q4. Cohort/CI — **conditional**

The fixed estimand is appropriately narrow: 15 frozen, length-eligible `common_ids` out of 20; no generalization to the 20-doc population; exactly five donors, same donor sets across cells, three-seed completeness, and no silent substitution (§6.1, lines 192–205; §6.6, lines 256–261; §7, lines 265–276). The donor map hash and leave-one-donor-out range are positive controls against donor-map drift (§0, lines 41–44; §6.1, lines 198–202). The Phase 6 prereg supplies the donor selection rule and frozen preflight content SHA (§0.4, lines 45–50; §2.5.6, lines 276–299).

Before R, record/assert the exact preflight content SHA and ordered `common_ids` identity in F0 artifacts, in addition to the donor-map SHA; “input SHA” alone (§11, lines 355–357) does not identify which input binds cohort membership. Donors are reused from val20 (§6.1, line 199), so define the CI as conditional on this fixed donor graph and make the leave-one-donor-out sensitivity decision-relevant; otherwise use a resampling scheme that preserves repeated-donor dependence. Do not imply population inference from this selected cohort.

The 10,000-resample override is correctly explicit in the primary definition (§6.3, line 223). Preserve a runtime assertion that the recorded resample count is 10,000 and do not route F0 labels through Phase 6 `l_predicate`, which hard-codes 1,000 (`runner/c5_pm_labels.py`, lines 54–64; v1.1 §0, lines 39–40).

**Next:** bind preflight/cohort hashes; specify the fixed-graph CI target and donor-sensitivity interpretation; assert the actual 10,000 bootstrap path.

## Q5. Compute — **disagree for this workspace; conditional for a different execution environment**

The workload arithmetic is plausible in outline: three trained cells × 100 updates × three seed waves = 900 updates; E00 is eval-only (§5, lines 178–186; §12, lines 361–379). Using the slowest parallel arm per wave and multiplying the wave term by three is consistent **if** the four arms truly run concurrently and `setup_s` is a one-time shared cost. Define whether setup includes per-arm model/cache loading, and derive the estimate from the F0 launcher’s measured per-phase timings; Phase 6 D1’s 1,180.6 s is not an F0 orchestration measurement (§12, lines 369–377), and v1.2 requires a new committed F0 runner before D0 (§11, lines 347–359).

There is a concrete current-environment blocker: the sandbox reports a **4-vCPU burst ceiling** (`burstLimit.cpu=4`), while D1/R require 12 logical threads and hard-abort at `nproc < 12` (§12, lines 363–376). This workspace cannot satisfy that gate as configured; 12 software threads on four CPUs do not make `nproc` 12. No resize or workload was attempted. Run only in a verified environment meeting the declared CPU gate, or revise and re-review the prereg/cap; do not silently drop the abort.

**Next:** do not run D0 here; define `setup_s`/parallel-wave accounting and commit the F0 orchestrator; verify the target host exposes at least 12 CPUs and the D1-derived R projection is ≤96 minutes before any approval.

## Q6. Scope — **agree, with claim language kept narrow**

The route-only boundary is appropriate: F0 tests “adapter-as-configured,” not an architecture-only bottleneck (§4, line 125; §14, lines 411–415). `ROUTE_STOP` stops only this EG2 layer19/LoRA/adapter route, not the EG2 track, B0-B, or H3 (§7 and §14); descriptive control contrasts are not causal, and the dropped zero/permuted null and 1-seed gate are expressly acknowledged (§14, lines 413–415). H3 remaining out of scope and requiring separate prereg/approval is correct (§10, lines 339–345).

Keep the wording precise: “descriptive/no inference” applies to the E00/E10/E01-vs-E00 contrasts; the registered E01−E11 primary still has a fixed-cohort bootstrap decision rule. Neither supports broad population generalization or an architecture-only causal claim.

## Must-fix before any stage approval (ranked)

1. **D1 exact contract:** enumerate the literal output schema (keys/types/nested values); resolve the mechanics-read vs “D1 values” contradiction, CE/label semantics, and success/crash filesystem allowlists. Keep `eval_arm_d1` and wrong-donor CE out of D1.
2. **Compute feasibility and provenance:** current 4-vCPU workspace cannot satisfy `nproc>=12`; do not execute here. Commit the F0-specific runner/orchestrator and derive `T_proj_f0` from its measured parallel timings on a qualifying host.
3. **Pre-R initialization audit:** define how E01/E11 initialization and all expected trainable groups are asserted for all three registered seeds before R; freeze complete tensor serialization and exact RNG capture points.
4. **Bound the MDE narrative:** `.104`, `.0876`, and `±.0124` are arithmetically consistent under the stated Phase 6 SE, but that SE and the historical F/L signal means do not establish F0 E01/E11 power or make ALL_FAIL the likely result. Label as proxy/sensitivity only.
5. **Cohort/CI binding:** persist/assert frozen preflight and ordered `common_ids` hashes; state the fixed-donor-graph CI target and donor-reuse sensitivity; assert 10,000 resamples and exclude the Phase 6 1,000-resample helper.

**Incorrect premises to reject:** Phase 6 F/L arm means `−.111/−.1135` are not paired E01−E11 results; the historical F/L treatment contrast is not the F0 primary; `.0876` is a calculated CI boundary, not an observed F0 effect; and 12 configured threads do not satisfy a 12-CPU `nproc` gate on this 4-vCPU sandbox.