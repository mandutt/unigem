# C5 F0 v1.0 — Independent Review (Round 10, final)

- Reviewer: DS1017 (`deepseek-v4.1-flash-1017`)
- Date: 2026-11-09
- Target: `docs/plan_c5_f0_v1_0_2026-11-09.md` (DRAFT v1.0, unapproved, unexecuted)
- This is a fresh thread. No v0.9 conclusion is inherited; only the listed sources and committed artifacts were read.
- No training, no evaluation, no test-163/P1 access, no subagents. One file written: this report.

## 0. Review basis

`git fetch origin` succeeded. `git pull --ff-only origin main` reported `Already up to date`.

Reviewed HEAD:

```
80a723f83b2e559ebc1f64bc7bff12d7ed582d48
docs: add C5 F0 v1.0 final review request
```

The working tree was clean before the write; all cited plan/runner/prereg lines are at this HEAD.

Sources read in full or in the cited ranges: the external review, v1.0 plan, v0.9 plan, v0.9/v0.8 syntheses, B0A cause report, Phase 6 results synthesis, prereg v1.0.11 (§11, §12, §13), `runner/c5_pm_phase6.py`, `runner/c5_pm_stats.py`, `runner/c5_pm_labels.py`, `runner/c5_pm_gate.py`, plus `reports/provenance/C5_b0a/{m_cohort_preflight.json,labels/labels.json,labels/cause_analysis.json,registered/registered_report.json}`.

## 1. Verdict summary

| Q | Topic | Verdict |
|---|---|---|
| Q1 | Initialization | **conditional** — structural reseed is sound; audit contract is not delivered |
| Q2 | D1 seal | **disagree** — seal is internally contradictory and has materialized outputs |
| Q3 | STOP / MDE | **disagree** — taxonomy is coherent; MDE numbers are derived from the wrong SE |
| Q4 | Cohort / CI | **disagree** — length-selected cohort and donor dependence are unacknowledged |
| Q5 | Compute | **conditional** — 900/96/25 are coherent; T_proj implementation and commit precondition are missing |
| Q6 | Scope | **conditional agree** — H3 removal is right; ROUTE_STOP consequence and lost-control tradeoff are undefined |

**Final: NARROW. v1.0 is not approved. No D0/D1/R.**

## 2. Verbatim paired E01−E11

From `docs/plan_c5_f0_v1_0_2026-11-09.md` §6.3, exactly as written:

```
- `D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.
```

The registered contrast and its computation, verbatim (§2 and §6.3):

```
- Primary: **E01 vs E11** (LoRA initialization matched).
D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
```

## 3. Q1. Initialization

**Judgment: conditional.** The RNG design is structurally correct; the audit that §0 says exists does not exist in §4, and the "per registered seed" claim is not executed by any stage.

What is sound:

- §4 makes LoRA init adapter-independent: `torch.manual_seed(seed)`, optional `Adapter`, then `torch.manual_seed(seed ^ 0x5EED10A5)` before `attach_decoder_lora_mt5`. E01 and E11 therefore get identical LoRA A/B init even though E11 also builds an adapter.
- Per-step `step_seed = seed ^ (0x9E3779B9*(step+1)) & 0xffffffff` before each forward makes LoRA dropout masks structural. `set_arm_training` in `runner/c5_pm_phase6.py:340-358` keeps the base decoder in eval and trains only the adapter/LoRA branch; `Adapter` (`runner/c5_mt5_layer_probe.py:52-63`) has no dropout, so E01 vs E11 have the same RNG consumers. Assertions 4/5 (post-init and post-step0 RNG hash) are meaningful.
- Assertion 6 correctly refuses to treat all-zero `lora_B` as equality evidence.

What is not delivered:

1. **No step_seed golden table.** §0 item 5 and the review request claim one; §4 gives only the formula. There are no pinned expected values for 20261108/09/10 or the debug seed 20261111, so a refactor can change the seed schedule without a failing test.
2. **No serialization frame.** §0 item 5 says dtype/shape are pinned; §4 does not specify the tensor hash frame. Prereg §12.1 already defines one (`name_len:u32 LE | name | dtype_len | dtype_str | ndim | shape:u32×ndim LE | nbytes:u64 LE | LE bytes`). F0 must cite and reuse it, including for `post_init_rng_state_sha256` / `post_step0_rng_state_sha256`.
3. **No post-step0 weight non-equality assert.** §0 item 5 promises it; §5 D1 only asserts `updates == 1` and checkpoint existence. Nothing proves the optimizer actually moved E10/E01/E11 weights.
4. **No init audit on the registered seeds.** §4 says "assertions per registered seed", but D0 uses only 20261111 (§5 D0) and D1 uses only 20261111 (§5 D1). The three registered seeds 20261108/09/10 reach Stage R with no prior init-hash equality check. Add a cheap init-only audit over all three seeds before R, or restate the contract as debug-seed-only.
5. **"F0 E11 ≠ Phase 6 L at init" is asserted, not verified.** §4 line 111 rests on "separate builder"; Phase 6 never persisted an init state, so no numeric comparison is possible. Replace with a provenance/I-O assertion (builder loads only `load_base()`; no Phase 6 checkpoint is opened) and record the base-state hash. A weight-inequality claim that cannot be tested is not an audit.

Next step: implement (1)-(5) in `runner/c5_pm_f0.py`; D0 must fail if any init hash is missing or if the golden step_seed vector differs.

## 4. Q2. D1 seal

**Judgment: disagree.** The seal is not self-consistent, and several D1 outputs are model-behavioral artifacts that the "counts only" claim does not cover.

Direct contradictions:

- §5 D1 assertion 9 says "3 trained checkpoints exist; E00 checkpoint optional" (line 151).
- §5 D1 lines 160-162 say checkpoints are **digest-only**, the file is **discarded**, and loading is forbidden.
- Both cannot be true. If the file is discarded, assertion 9 must be "3 checkpoint digests recorded and 0 checkpoint files remain"; if files remain, the oracle is open.
- §5 line 157 says `d1_mechanics.json` is "the only D1 output", but assertion 5 requires **480 M records** (120/cell) and assertion 7 requires **80 generation records**. Those are outputs. The plan never says where they are written or that they are non-signal.

Materialization bypass:

- `eval_arm_d1` (`runner/c5_pm_phase6.py:429-490`) computes and returns `per_doc[rid]["delta_shuffled_copy"]` and `delta_shuffled_full`. If F0 reuses it to satisfy "all CE finite" / "n_docs == 20", the signal values are materialized in process memory even if not written. That falsifies §5 line 163 ("the values are never materialized in D1").
- Phase 6 `run_d1` (`runner/c5_pm_phase6.py:800-880`) writes `step0`, `final` (with `per_doc`), `phase7_records`, `generation`, `checkpoint`, `d1_partial.json` and `d1_report.json`. The F0 seal must be a different code path, not a flag on this one.

Missing controls that §0 claims:

- §0 line 29 promises a **literal allowlist**, writer-side key/dir asserts, and a **phase7 filesystem assert**. §5 only says "exact-key allowlist" and "phase7 records == 0". No key list, no writer assert, no `Path(phase7_dir).exists()` check.
- `d1_partial.json` is not on the denylist; neither are `m_records_*`, `generation_*`, `checkpoints/**`, or `phase7_records/**`.

Remaining bypass paths after the current text:

1. Reusing `eval_arm_d1` (in-memory deltas).
2. Retained checkpoints (direct reload/recompute).
3. Generation text (copy behavior is observable and can proxy signal).
4. M CE records (model-dependent, even if donor-free).
5. Any extra writer key not covered by an allowlist.

Next step: define `eval_arm_d1_mechanics` returning only `{n_docs, n_donors_counts, ce_finite, endpoint_ok}`; forbid importing/calling `eval_arm_d1`; enumerate the literal allowed key set and assert `set(payload) == ALLOWED` at write time; assert the phase7/checkpoint directories are empty after D1 and that the digest-only files are absent; extend the negative/invariance test to every forbidden path, not only `d1_report.json`.

## 5. Q3. STOP taxonomy / MDE

**Judgment: disagree (on MDE); taxonomy itself is sound.**

Taxonomy:

- §7 states are mutually exclusive by ordered evaluation and exhaustive: any protocol-valid case is PASS, ALL_FAIL, or neither (INDETERMINATE). PASS and ALL_FAIL cannot co-occur because PASS requires `SIGNAL(E01,copy)` while ALL_FAIL requires `FAIL(E01,copy)`.
- PASS (`CI_D.lower > +.05`) and EQUIVALENT (`CI_D.upper <= +.05`) are disjoint. Boundary `.05` is not PASS, which is consistent.
- `ALL_FAIL` is exactly E01/E11 × copy/full (§7 line 289), and the reason precedence `EQUIVALENT > harm > benefit` is coherent. `benefit` means E11 (adapter) is better; recording `adapter_benefit` while still stopping the route is defensible.

MDE and CI arithmetic are not:

- `labels.json` L copy: mean −0.113506, CI [−0.234090, −0.001167], half-width **0.116462**, so SE ≈ 0.059419.
- `.166 ≈ 2.802 × 0.059419`; `.216 ≈ 3.605 × 0.059419`. These are **≈80% and ≈95% power at the single-arm SE**, not at the paired contrast's SE. v0.9 §0 labeled them "50%/80%"; v1.0 removed the labels but kept the numbers, so the error is hidden rather than fixed.
- The only committed paired contrast is Phase 6 F−L: `labels.json` paired CI [−0.040845, +0.034302], half-width **0.037573**, SE **0.019170**. At that SE, 80% MDE ≈ **0.0537**, and PASS `lower > .05` requires mean ≳ **0.0876** (80% power near 0.104). Power at a true 0.05 effect is ≈2%, not 80%.
- §6.5 says "With n=15 doc-level bootstrap (Phase 6 L half-width ≈0.117), EQUIVALENT and ROUTE_STOP may be rare." If CI_D's half-width really were 0.117, EQUIVALENT (±.05, §7) would be **arithmetically unreachable** (need mean in (+.067, −.067)); it has top priority in §7. Either CI_D is much tighter than the single-arm figure (as the paired proxy suggests), or EQUIVALENT is decorative. The plan cannot have it both ways.
- The expected-outcome sentence is also wrong on base rates: on the 15-common cohort Phase 6 F is −0.111 (see Q4), so ALL_FAIL → ROUTE_STOP is the more likely branch, not "plain INDETERMINATE dominant".

Next step: derive MDE from D's own paired SE (doc-level, seed-averaged), state power at δ=.05 and at the PASS threshold, drop or relabel .166/.216, and rewrite §6.5 so EQUIVALENT's reachability matches the stated half-width.

## 6. Q4. Cohort / CI

**Judgment: disagree.** Three issues are material: the 15-doc cohort is length-selected and not representative of the 20 val docs; donors are reused documents and are not independent of targets; and the 10,000-bootstrap override can silently revert to 1,000.

Cohort:

- `m_cohort_preflight.json`: `common_cohort_at_k = 15`, `l_target_eligible_at_k = 15`, `l_excluded_at_k = 5`, `val20 = 20`. The excluded docs are short (`REPORT-news_r-00430`, `-01127`, `-02180`, `-02804`, `-03445`). Selection is by target length at K=753, not random, though outcome-independent.
- Recomputing from `registered/registered_report.json` (seed-pooled doc means, `delta_shuffled_copy`):
  - F: 15-common **−0.11087** vs 20-doc **+0.000195**.
  - L: 15-common **−0.11351** vs 20-doc **−0.02218**.
  The 15-doc estimand is therefore not a neutral subset; Phase 6 F flips sign between cohorts. §6.1 freezes the 15 IDs but never states this conditioning or the divergence. A 15-doc result cannot be generalized to the 20-doc val set.
- §6.6 "no 15→14 substitution" and the presence check are good; keep them.

Donor dependence:

- `donors_for` (`runner/c5_mt5_lora_b0.py:318-326`) assigns the 5 nearest-length **other val docs**. Donors are themselves targets (doc A's donor can be doc B, whose own target uses A), and the same donor can serve several targets. The doc-level bootstrap (`bootstrap_paired_v2`, PCG64, percentile) resamples docs only, so it treats the 5-donor average as fixed and ignores shared-donor dependence. `donors_for`'s docstring says "same for all arms/seeds", which guarantees identity, not independence.
- §6.1/§7 only require "exactly 5 donors" and identical donor sets; they do not define the estimand as conditional on this fixed donor graph, nor report donor-level dispersion.

Bootstrap override:

- §6.3 correctly passes `n_boot=10000`, but `runner/c5_pm_labels.py:62` hard-codes `bootstrap_paired_v2(per_doc_delta, 1000, 20261109)`, and `runner/c5_pm_stats.py` freezes `N_BOOT = 1000`. If the F0 gate reuses `l_predicate`, the override silently disappears. §0/§6.3 do not forbid that reuse.

Next step: state the estimand as "15 length-eligible docs, fixed 5-donor graph"; report the 20-doc descriptive separately; add a donor-cluster sensitivity (or at least donor-level spread and a statement that CIs are conditional); implement the F0 gate as a direct `bootstrap_paired_v2(..., n_boot=10000)` call with `assert out["n_boot"] == 10000` and forbid `l_predicate`.

## 7. Q5. Compute

**Judgment: conditional.** The arithmetic is consistent; the implementation path is not.

Consistent:

- §12: R is 4 cells × 3 seeds; E10/E01/E11 at 100 updates = **900 updates**. M = 120 × 4 × 3 = **1,440**; phase7 = 600 × 4 × 3 = **7,200**; generation = 20 × 4 × 3 = **240**. All correct.
- D1 25 min vs D-156 measured 1,180.6 s / 1,200 s (**19.7 min**), and R 96 min vs D-157 measured 4,939.9 s / 7,200 s (**82.3 / 120 min**), are coherent. F0 removes 300 updates (E00 is eval-only), so 96 min has margin.
- `nproc < 12` is the right floor for 4 arms × 3 threads.

Not consistent / missing:

1. **The frozen T_proj function cannot accept F0.** `t_proj_seconds` (`runner/c5_pm_stats.py`) requires exactly `F, L, P, PA`, sums all four arms, then multiplies by 3. §12 says "slowest arm" for cells E00/E10/E01/E11. §11's claim that the term set "mirrors Phase 6 §11.5" is true only for the terms, not the aggregation. Using the frozen function would raise `ValueError` or overcount ~4×. A new `t_proj_f0` with cell keys and slowest-arm-per-wave semantics is required; §11 does not list it.
2. **Contention is recorded but not applied.** §12 line 357 defines `contention_ratio = parallel_wall_s / sum(per_arm_phase_s)`, but `T_proj_R` (line 353) has no contention factor and the abort is on projected time only (line 358). A run can pass `T_proj_R ≤ 96` and still exceed 96 wall. Either apply `T_proj_R × max(1, contention_ratio)` or abort on measured `parallel_wall_s > 96`.
3. **`setup_s` is multiplied by 3** in `T_proj_R = 3 × (...)` even though setup is per-run, not per-seed.
4. **Baseline thread count is inconsistent in the governing docs.** Prereg §11.1 says 6 threads; D-157 says 3 waves of 4 arms at 2 threads each (8). F0 assumes 3/arm ×4 (12). The T_proj comparison must record the actual baseline, not just cite 82.3 min.
5. **No orchestration-commit precondition.** §11 names `runner/c5_pm_f0.py`, `c5_pm_f0_parallel.py`, `c5_pm_f0_gate.py` but does not require them committed at a recorded SHA before D0/D1. This is the Phase 6 MF-1 provenance gap repeated for F0. §13 also has no `code_commit`, `command`, or input-SHA fields.

Next step: implement `t_proj_f0` (cells E00/E10/E01/E11, setup once, slowest arm × 3 waves, contention applied); require a committed driver SHA before D0 and record it in every artifact; restate the thread baseline.

## 8. Q6. Scope

**Judgment: conditional agree.**

- Removing H3 (§10) is correct: no H3 arm/trigger/rank/null is registered, F0 cannot auto-launch H3, and a separate prereg is required. This is the right boundary.
- Title "Single-Contrast Diagnostic" and the association-only limitation (§14) are honest. Four cells with one registered contrast (E01 vs E11) and descriptive E00/E10 contrasts is defensible, provided descriptive contrasts carry a no-inference rule; §2 labels them confounded/not clean causal but never says they cannot enter a decision.
- The lost-controls sentence (§14) is explicit, but it understates what was dropped. Phase 6 MF-4 asked for a zero/permuted null and a 1-seed D-level gate. v1.0 replaces the 1-seed gate with a **sealed** D1 that cannot read signal, and omits the null. That is a deliberate no-peek trade, not a control. F0 must record that a positive result cannot separate an adapter effect from a pipeline artifact without a future null/projection prereg.
- `ROUTE_STOP` has no defined consequence. §7 stops the route but §14 says the EG2 overall STOP/keep decision is out of scope. State explicitly: ROUTE_STOP stops only the route as configured (EG2 layer19 raw + this LoRA/adapter configuration), does not stop the EG2 track, does not rescue B0-B, and does not launch H3.
- §0 item 9 says D0/D1/R each require explicit stage approval, but §11 only says implementation + D0/D1 requires approval and "D1 before R". Add an explicit R approval line.

## 9. Must-fix (ranked)

**MF-1 (blocker) — D1 seal is contradictory and not count-only.**
§5 assertion 9 ("3 trained checkpoints exist") vs lines 160-162 (digest-only, discarded, load forbidden); line 157 ("only D1 output") vs assertions 5/7 (480 M records, 80 generation records); `eval_arm_d1` materializes `delta_shuffled_*` in memory. Fix: separate mechanics evaluator, literal allowlist, writer assert, phase7/checkpoint filesystem asserts, digest-then-delete-then-assert-absent, full denylist including `d1_partial.json`.

**MF-2 (blocker) — cohort is length-selected and donor-dependent.**
Preflight 15/15/5/20; F 15-doc −0.11087 vs 20-doc +0.000195; L 15-doc −0.11351 vs 20-doc −0.02218; `donors_for` reuses val docs as donors. Fix: declare the estimand conditional on the 15 length-eligible docs and fixed donor graph, report 20-doc descriptive, add donor-cluster sensitivity, and forbid generalization to the 20-doc val population.

**MF-3 (blocker) — MDE/EQUIVALENT arithmetic.**
.166/.216 are 80%/95% power at single-arm SE 0.0594, not D; Phase 6 paired half-width is 0.037573 (SE 0.019170), implying 80% MDE ≈ 0.054 and PASS threshold mean ≈ 0.0876. If CI_D half-width were 0.117, EQUIVALENT is unreachable despite top priority. Fix: derive from D's own paired SE, relabel or drop the numbers, rewrite §6.5, and state power at 0.05.

**MF-4 (blocker) — provenance and commit precondition.**
No committed F0 driver requirement; §13 lacks `code_commit`/`command`/input SHA. Fix: commit `runner/c5_pm_f0*.py` at a recorded SHA before D0; record code SHA, command, freeze/input hashes in D0/D1/R artifacts; no uncommitted driver.

**MF-5 (high) — initialization audit is claimed but missing.**
step_seed golden table; tensor/RNG-state serialization (cite prereg §12.1); post-step0 weight non-equality; init assertions for all three registered seeds (D0/D1 only run 20261111); replace "F0 E11 ≠ Phase 6 L at init" with an I-O/provenance assert.

**MF-6 (high) — n_boot 10000 can silently revert.**
`l_predicate` hard-codes 1000 (`runner/c5_pm_labels.py:62`); `N_BOOT=1000` (`runner/c5_pm_stats.py`). Fix: direct `bootstrap_paired_v2(..., n_boot=10000)`, assert `n_boot == 10000` in `f0_labels.json`, forbid `l_predicate`, and state Phase 6 artifacts remain at 1000 and are not recomputed.

**MF-7 (medium) — T_proj implementation, contention, baseline.**
New `t_proj_f0` for E00/E10/E01/E11; setup once; apply `max(1, contention_ratio)` or abort on measured wall; record `os.cpu_count`; reconcile prereg §11.1's 6 threads with D-157's 2/arm.

**MF-8 (medium) — scope boundaries.**
Define ROUTE_STOP consequences; add no-inference rule for descriptive contrasts; record the dropped 1-seed gate/null and its effect on mechanism claims; add explicit R approval.

## 10. 잘못된 전제 (wrong premises)

1. **"T_proj는 Phase 6 §11.5 term set을 그대로 쓴다"** — the terms match, the aggregation does not. Phase 6 `t_proj_seconds` requires `F,L,P,PA` and sums all arms ×3; F0 has E00/E10/E01/E11 and uses slowest-arm ×3. The frozen function cannot run F0 unchanged.
2. **".166/.216은 D의 MDE"** — they are 80%/95% power at the single-arm SE; v0.9 labeled them 50%/80%, which is wrong. The paired contrast SE is ~3× smaller in the only committed proxy.
3. **"D1 checkpoint는 digest-only이고 3개가 존재한다"** — mutually exclusive. One of the two must change.
4. **"literal allowlist / step_seed golden table / phase7 filesystem assert / post-step0 non-equality / tensor serialization pinned"** — these appear in §0's summary but not in §4/§5. A summary claim is not a contract.
5. **"15 common은 중립적인 frozen cohort"** — it is length-selected (5 of 20 val docs excluded at K=753), and F flips from −0.111 on 15 docs to +0.0002 on 20.
6. **"EQUIVALENT and ROUTE_STOP are rare; INDETERMINATE is dominant"** — at the stated single-arm half-width EQUIVALENT is unreachable; at the 15-doc base rate ALL_FAIL/ROUTE_STOP is the more likely branch.
7. **"F0 E11 ≠ Phase 6 L at init"** — asserted structurally; no Phase 6 init artifact exists, so the inequality is untestable as written.
8. **"n_boot=10000 override is effective"** — only if the F0 gate does not reuse `l_predicate`, which hard-codes 1000.
9. **"donor sets identical ⇒ independent"** — identity across cells is not independence across docs; donors are reused val documents.

## 11. Final

```text
최종 판정: NARROW

Initialization: conditional
  RNG ordering and per-step reseed are structurally correct. Missing: step_seed golden
  table, serialization frame, post-step0 non-equality, registered-seed init audit,
  and a testable F0≠Phase6-L assertion.

D1: disagree
  "3 checkpoints exist" vs digest-only/discarded; 480 M + 80 generation outputs vs
  "only D1 output"; eval_arm_d1 materializes per_doc deltas in memory. Seal must be
  a separate mechanics path with a literal allowlist and filesystem asserts.

STOP/MDE: disagree
  Four-state taxonomy is exclusive/exhaustive and PASS/EQUIVALENT are disjoint.
  .166/.216 are 80%/95% power at single-arm SE 0.0594, not D's paired SE; with the
  Phase 6 paired half-width 0.037573, 80% MDE ≈ 0.054 and PASS needs mean ≈ 0.0876.
  If CI_D half-width were 0.117, EQUIVALENT would be unreachable.

Cohort/CI: disagree
  15-common is length-selected (15/15/5 of val20); F 15-doc −0.11087 vs 20-doc
  +0.000195; L −0.11351 vs −0.02218. Donors are reused val docs; doc bootstrap
  ignores that dependence. l_predicate silently uses n_boot=1000.

Compute: conditional
  900 updates, M 1,440, phase7 7,200, generation 240, D1 25 min vs D-156 19.7,
  R 96 min vs D-157 82.3 are coherent. Missing: F0-specific T_proj function,
  contention application, setup counted once, committed-driver precondition,
  consistent thread baseline.

Scope: conditional agree
  H3 removal and association-only language are right. ROUTE_STOP consequence is
  undefined; the dropped 1-seed gate/null is a no-peek trade, not a control; add
  explicit R approval and a no-inference rule for descriptive contrasts.

Must-fix (ranked):
  1. D1 seal contradiction + materialized M/generation outputs + literal allowlist.
  2. 15-doc length-selection, 15-vs-20 divergence, donor reuse/dependence.
  3. MDE/EQUIVALENT arithmetic (single-arm vs paired SE).
  4. Committed F0 drivers + code/command/input-SHA provenance.
  5. step_seed golden, serialization, post-step0 non-equality, 3-seed init audit.
  6. n_boot 10000 enforcement; forbid l_predicate.
  7. t_proj_f0, contention, setup-once, thread baseline.
  8. ROUTE_STOP boundary, descriptive no-inference, explicit R approval.

Approval: withheld. No D0/D1/R. Re-review only after MF-1…MF-4 are closed in a
new revision; if those close, this reviewer would move to CONTINUE for a
single-delta confirmation, not unconditional approval.
```

## 12. Boundaries observed

- No training/evaluation; no test-163/P1; no subagents; no threshold/seed/donor/step/LR change.
- No repository change other than this file.