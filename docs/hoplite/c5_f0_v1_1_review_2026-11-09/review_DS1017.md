# C5 F0 v1.1 — Independent Review (New Block, Round 1/10)

- Reviewer: DS1017 (`deepseek-v4.1-flash-1017`)
- Date: 2026-11-10 (UTC)
- Target: `docs/plan_c5_f0_v1_1_2026-11-09.md` (DRAFT v1.1, unapproved, unexecuted)
- This is a fresh thread. No v1.0/v0.9 conclusion is inherited; only the listed sources and committed artifacts were read.
- No training, no evaluation, no test-163/P1 access, no subagents. One file written: this report.

## 0. Review basis

- `git fetch origin` succeeded (`main` -> `FETCH_HEAD`).
- `git pull --ff-only origin main` reported `Already up to date`.
- Working tree clean before the write (`git status --porcelain` empty).

Reviewed HEAD:

```text
af0fa3ec374ab5cb20c9823485c78f2bd47c45d2
2026-11-10 09:47:55 +0900  docs: add C5 F0 v1.1 review request
```

All plan/runner/prereg citations below are at this HEAD.

Sources read: `reports/EXTERNAL_REVIEW_C5_F0_V1_1_2026-11-09.md`, v1.1 plan (all 471 lines), v1.0 plan, v1.0/v0.9 syntheses, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, Phase 6 results synthesis, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md` (§12.1), `runner/c5_pm_phase6.py`, `runner/c5_pm_stats.py`, `runner/c5_pm_labels.py`, `runner/c5_mt5_lora_b0.py`, and `reports/provenance/C5_b0a/{m_cohort_preflight.json,labels/labels.json,labels/cause_analysis.json}`.

## 1. Verdict summary

| Q | Topic | Verdict |
|---|---|---|
| Q1 | Init | **disagree** — §0 promises four controls that do not exist in §4/§5 |
| Q2 | D1 | **conditional** — round-10 contradiction is fixed; the seal's computation scope and "literal" allowlist are still undefined |
| Q3 | STOP / MDE | **agree on taxonomy / disagree on the MDE rationale** — arithmetic is now correct; §6.5 still uses the wrong (single-arm) width |
| Q4 | Cohort | **conditional** — estimand restriction is now honest; donor-cluster sensitivity is a placeholder, not a method |
| Q5 | Compute | **conditional** — 900/25/96 are coherent; `t_proj_f0` is undefined and setup is triple-counted |
| Q6 | Scope | **agree** — H3 removal and ROUTE_STOP consequence are adequate |

**Final: NARROW. v1.1 is not approved for D0/D1/R.** The cohort and MDE blockers from round 10 are genuinely closed; the init, D1-scope, compute, and provenance blockers are not.

## 2. Verbatim paired E01−E11

From `docs/plan_c5_f0_v1_1_2026-11-09.md` §2 (line 67) and §6.3 (lines 212, 218), exactly as written:

```text
- Primary: **E01 vs E11** (LoRA initialization matched).

D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs

- `D_s` = paired E01−E11 contrast per seed; seed-sign gate tests replication, not a second primary.
```

The doc-average and seed-mean definitions that make the pairing literal are §6.2 (line 207):

```text
- per-doc seed average: `delta_c(d) = mean_s delta_c(s,d)`.
```

## 3. Q1. Initialization

**Judgment: disagree.** The RNG construction is sound and is a real improvement over Phase 6. The audit contract that §0 says exists does not exist.

What is sound in §4:

- The unconditional `torch.manual_seed(seed ^ 0x5EED10A5)` before `attach_decoder_lora_mt5` (line 92) is necessary, and I verified it is absent from the current Phase 6 builder: `runner/c5_pm_phase6.py:142-160` does `torch.manual_seed(int(seed))`, then `Adapter(512,512)` if the arm has one, then `attach_decoder_lora_mt5(model)` with **no** reseed. In Phase 6, L's LoRA init therefore depends on adapter construction order. The F0 builder genuinely fixes that confound.
- Per-step `step_seed` before every forward (lines 95-96) makes dropout masks structural. `Adapter` has no dropout, and the base decoder is eval-only, so E01/E11 have identical RNG consumers. Assertions 4 and 5 (post-init and post-step0 RNG hash) are meaningful.
- Assertion 6 (line 110) correctly refuses to treat all-zero `lora_B` as equality evidence.

What is claimed but absent — this is the round-10 DS-5 must-fix, still unclosed:

1. **No `step_seed` golden table.** §0 line 36 promises one. §4 gives only the formula (line 95). There is no pinned expected vector for 20261108/09/10 or 20261111, so a refactor of the seed schedule cannot fail a test.
2. **No tensor/RNG serialization frame.** §0 line 36 promises it; §4 line 113 defines only the digest of `init_hashes.json` (sorted key + `\0` + value). That is not the frame used to hash a tensor. Prereg §12.1 already fixes one at `docs/plan_c5_b0a_pm_prereg_v1_0_11.md:1375-1380` (`name_len:u32 LE | name | dtype_len:u8 | dtype_str | ndim | shape:u32×ndim LE | nbytes:u64 LE | LE bytes`). F0 must cite and reuse it, including for `post_init_rng_state_sha256` and `post_step0_rng_state_sha256`. The string `dtype` does not occur anywhere in the v1.1 plan.
3. **No post-step0 weight non-equality assert.** §0 line 36 promises it; no assertion in §4 or §5 checks that E10/E01/E11 weights actually moved after the update. D1 assertion 2 only checks `updates_total == 3`. A misconfigured optimizer (lr 0, adapter params omitted, frozen branch) would pass D0/D1 and only surface as D≈0 in Stage R.
4. **No init audit on the registered seeds.** §4 line 104 says "Assertions per registered seed", but D0 uses only 20261111 (§5 line 122) and D1 only 20261111 (§5 line 140). Stage R uses 20261108/09/10 (line 172) with no init assertions in its block (lines 172-180). The three seeds that feed the primary estimand never get a hash-equality check. Add a cheap init-only audit over all three seeds before R.
5. **"F0 E11 ≠ Phase 6 L at init" is still untestable.** §4 line 114 rests on "separate builder"; D0 assertion 8 checks only E01/E11 LoRA equality and E10/E11 adapter equality. Nothing asserts that no Phase 6 checkpoint is opened. The provenance requirement added at §11 line 347 (`code_commit`, command, input SHA) does not replace an I/O assertion.

## 4. Q2. D1 seal

**Judgment: conditional.** The round-10 self-contradiction is resolved: §5 D1 assertion 9 now says "digest recorded then checkpoint deleted; `checkpoint_absent == true`; no loading" (line 155), and `eval_arm_d1` is explicitly forbidden at §11 line 343. That is the right direction. Three gaps remain.

1. **The seal's computation scope is undefined.** §5 line 158 says D1 "does not compute or write signal deltas, `per_doc`, phase7, or `final` objects" and line 163 says "the values are never materialized in D1". But assertion 4 (line 149) requires `n_docs_step0 == 20` and `n_docs_final == 20`, assertion 5 requires 480 M records, and assertion 7 requires 80 generations. To eval 20 docs at step0 and final you must compute CE. If the mechanics evaluator reuses Phase 6's per-doc loop shape, `delta_shuffled_copy`/`delta_shuffled_full` are materialized in memory (`runner/c5_pm_phase6.py:470,473`). The plan must state what `c5_pm_f0_mechanics.py` computes: real-copy CE and M-only, and **never** wrong-donor CE. Without that sentence, "never materialized" is a claim about the writer, not the evaluator.
2. **The allowlist is not literal.** §5 line 160 and §13 line 392 say "exact-key allowlist", but no key list is enumerated anywhere. `d1_mechanics.json` has no schema. A "literal allowlist" is a named set of keys that a writer assert can compare against; the plan has the adjective, not the set.
3. **Q2's own premises are not in the plan.** The review request (Q2) and plan §15 Q2 (line 417) ask about "exact-key allowlist + denylist + sanitized partial + negative/invariance test". `denylist`, `sanitized`, and `invariance` occur **only** in that question line — not in §5, §11, or §13. The negative test exists (line 162: non-zero exit on `d1_report.json`/`per_doc`/`delta_*`), but the denylist and invariance test do not. I cannot approve a control that is only named in the question.

Additional ambiguity worth fixing: assertion 10 `labels_computed:false` (line 156) sits next to assertions that require CE and 20-doc eval. `labels` here must mean decision labels, not token labels; say so, or an implementer will read it as "no token labels".

The residual oracle is not a design defect: a checkpoint exists between write and delete, and anyone with shell access can copy it. The plan correctly frames this as an access-control limit (line 162: "process non-computation is not artifact non-access"). It should not be described as "stronger than a seal" (line 163) unless the deletion assert and the file-mode/no-copy path are specified.

## 5. Q3. STOP / MDE

**Judgment: taxonomy agree; MDE arithmetic agree; MDE rationale disagree.**

Taxonomy: §7's four states are mutually exclusive and exhaustive in the stated priority order (lines 287-292).

- `PASS_POSITIVE` requires `CI_D.lower > +.05`; `EQUIVALENT` requires `CI_D.upper <= +.05`. These cannot both hold (`lower > .05` implies `upper > .05`), so the two are disjoint. Confirmed.
- `PASS_POSITIVE` requires `SIGNAL(E01,copy)`, i.e. `NOT FAIL(E01,copy)`; `ROUTE_STOP` requires `ALL_FAIL`, which includes `FAIL(E01,copy)`. They cannot both hold. Confirmed.
- `ALL_FAIL` is exactly E01/E11 × copy/full (lines 272-273, 294); E00/E10 are excluded. Reason precedence (`no_signal_equivalent > adapter_harm > adapter_benefit > no_signal_uncertain`) is deterministic. Confirmed.
- `mean_D > 0` in the PASS predicate (line 290) is redundant given `CI_D.lower > .05`, but harmless.

MDE arithmetic: correct, and I traced it to committed numbers.

- `reports/provenance/C5_b0a/labels/labels.json` → `L_COPY_SIGNAL.paired`: `mean = -0.002639`, `ci = [-0.040845, +0.034302]`, `n = 15`, `n_boot = 1000`, `seed = 20261109`, `ci_method = linear`. Half-width = `(0.034302 - (-0.040845))/2 = 0.0375735`; SE = `0.019170`. These match §0 lines 29-30 exactly.
- 95% half-width `1.96 × 0.019170 = 0.037573` ✓.
- 80% MDE `(1.96 + 0.8416) × 0.019170 = 0.05371 ≈ 0.054` ✓.
- PASS mean `0.05 + 0.037573 = 0.087573 ≈ 0.0876` ✓.

Rationale: §6.5 line 245 argues "With n=15 doc-level bootstrap (Phase 6 L half-width ≈0.117), EQUIVALENT and ROUTE_STOP may be rare". That `0.117` is the **single-arm** L delta half-width: `labels.json` → `L_COPY_SIGNAL.delta` `ci = [-0.234090, -0.001167]`, half-width `0.11646`. It is not the width of the paired `CI_D`. At the paired half-width of `0.037573`, `EQUIVALENT` holds whenever `|mean_D| <= 0.0124`, which is not rare — it is a plausible null outcome. The conclusion ("INDETERMINATE dominant") may still be right, but this paragraph uses the wrong scale and should be rewritten with `0.0376`.

Related wrong premise: §6.4 defines `SIGNAL(c,copy)` as `mean(delta_c) >= .05 AND CI.lower > 0 AND 2/3 seeds > 0` (lines 233-236). With a single-arm SE of about `0.0594`, `CI.lower > 0` requires `mean >= ~0.117`, so the `.05` mean threshold is inert — the binding floor is `0.117`, not `.05`. That is a defensible (if demanding) gate, but calling `.05` the signal threshold misstates it. Say "`CI.lower > 0` dominates; effective mean floor ≈0.117".

## 6. Q4. Cohort / CI

**Judgment: conditional.** The v1.1 estimand fix is real and is the main reason this round differs from round 10.

- §6.1 lines 187-191 now state: primary estimand = 15 length-eligible docs + fixed donor graph; 20-doc values descriptive only; generalization forbidden; donor reuse declared; donor-cluster sensitivity reported. This is exactly the restriction the round-10 blocker demanded.
- The preflight artifact supports it: `m_cohort_preflight.json` has `common_ok: true`, `common_cohort_required: 15`, `common_cohort_at_k: 15`, `k_selection_rule: "K_M_L = max K such that #train h>=K >= 10 and #val h>=K >= 15; K=753 is the maximum; K=754 gives 14 target-eligible"`, and five excluded IDs (`l_excluded_at_k`). `no_model_forward: true`, `test_split_used: false`. So the cohort is frozen, length-selected, and declared.
- §7 line 264 requires exactly 5 donors per doc and identical donor sets across E00/E10/E01/E11; §6.1 line 198 requires all 15 present in `unit.final.per_doc`; §6.1 line 199 forbids shrinking the cohort (`eval_arm_d1` silently drops non-copyable docs — `runner/c5_pm_phase6.py:466-469`, `if not real_copy: continue`). Good.
- `n_boot=10000` is explicit at §6.3 line 214, and `bootstrap_paired_v2` accepts it (`runner/c5_pm_stats.py:29-67`). `l_predicate` really does hardcode 1000 (`runner/c5_pm_labels.py:54-60`: `bootstrap_paired_v2(per_doc_delta, 1000, 20261109)`), so §0 line 38's "forbid `l_predicate`" is well founded.

What is still missing:

1. **"Donor-cluster sensitivity" is a placeholder.** It appears twice (line 27, line 190) with no method. Donors are length-nearest neighbours drawn from the same 20 val docs, self-excluded (`runner/c5_mt5_lora_b0.py:318-330`, `donors_for`, `x != rid`). For the 15-doc cohort the donor sets overlap heavily, so the doc-level bootstrap at §6.3 treats correlated `D(d)` as independent and understates variance. Define the sensitivity: a donor-clustered bootstrap (resample donor clusters) or a leave-one-donor-out re-estimate of `mean_D` and `CI_D`; record the frozen donor map hash.
2. **The donor graph is not named or hashed.** §6.1 says "fixed donor graph" but never says it is `donors_for(val_ids, cache)` from `c5_mt5_lora_b0.py`, nor that the map is hashed into `init_hashes.json`/provenance. Without that, "fixed" is not auditable.
3. **The 5 excluded docs are not reported as a descriptive block.** §6.1 says "report 20-doc F/L descriptively", which includes them, but given the round-10 number (F 15-doc −0.11087 vs 20-doc +0.000195), the 5-doc excluded subset should be reported explicitly so the direction change is visible.

The seed-sign gate (`2/3 seeds D_s > 0`, line 218) is weak: under a true null with independent signs it fires with probability 0.5. It is frozen from Phase 6 and is labelled a replication gate, not a second primary, which is acceptable; it should not be described as evidence of replication strength.

## 7. Q5. Compute

**Judgment: conditional.** The workload counts are coherent; the projection function and setup accounting are not.

Coherent:

- §5 Stage R: 4 cells, E00 0 updates, E10/E01/E11 100 each = 900 updates (line 175). M 1,440 = 120 × 4 × 3; phase7 7,200; generation 240. Arithmetic checks.
- D1 cap 25 min vs Phase 6 measured parallel 1,180.6s = 19.68 min (§12 line 360) → 27% headroom for a lighter D1 (3 trained updates vs Phase 6's 4 arms). Plausible.
- R cap 96 min vs Phase 6 82.3 min → 16.7% headroom, and F0 has 900 updates vs Phase 6's 1,200. Plausible.
- `nproc < 12` hard abort and `contention_ratio = parallel_wall_s / sum(per_arm_phase_s)` (line 365) are the right telemetry.

Not coherent / not defined:

1. **`t_proj_f0` has no definition.** §11 line 345 and §0 line 40 say "separate `t_proj_f0`", but no signature, term set, or arm set is given. The existing function cannot be reused: `t_proj_seconds` (`runner/c5_pm_stats.py:139-178`) hard-requires the arms `("F","L","P","PA")` and the nine named terms, and multiplies by 3 outside. F0 needs its own term set for E00/E10/E01/E11 (E00 has no training, so `t_train_arm` is 0 for E00) and an explicit slowest-arm aggregation.
2. **Setup is counted three times.** §0 line 40 and the v1.1 change note say "setup once", but §12 line 361 computes `T_proj_R = 3 × (setup_s + ...)`, which charges `setup_s` to each of the three seed waves. That is a real (if small) over-count and contradicts the text. Use `setup_s + 3 × (step0 + 100×step + ...)`.
3. **"Slowest arm" is stated but not in the formula.** Line 363 says "Slowest arm; seed waves sequential", while line 361 sums one arm's terms. Say `max over arms` explicitly.
4. **Provenance is a precondition, not a note.** §11 line 347 requires `runner/c5_pm_f0*.py` committed at a recorded SHA with a clean tree before D0. Those files do not exist (`ls runner/` has no `c5_pm_f0*`). Therefore D0 cannot be approved or started from v1.1 as written; the plan is not yet executable.

## 8. Q6. Scope

**Judgment: agree.** (The plan's own §15 Q6 asks about H3; the review request's Q6 asks about scope. I answer scope and confirm H3.)

- §10 lines 330-336 remove H3 completely and state that F0 results do not launch it. This is correct and should not be reopened.
- §14 line 404 defines `ROUTE_STOP` as stopping only the route as configured (EG2 layer19 raw + this LoRA/adapter configuration), not the EG2 track, not B0-B, and not H3. That is the right boundary.
- §14 line 405 forbids causal inference from E00/E10/E01-vs-E00 descriptive contrasts.
- §14 line 406 records the dropped MF-4 zero/permuted null and 1-seed gate as intentionally out of scope and says F0 cannot claim they were replaced. Honest.
- §11 line 350 requires explicit D0/D1/R stage approvals. Present.

One residual: §7's `ROUTE_STOP` is a state name that includes a benefit branch (`adapter_benefit`, line 291/298). "STOP" for a benefit result is semantically odd. It is deterministic and documented, so not a blocker, but rename to `ROUTE_NULL`/`ROUTE_CLOSED` or explain in one line that ROUTE_STOP means "route closed to further work", not "adverse".

## 9. Wrong premises in the review request / plan

1. **Q2 asserts controls that do not exist.** "denylist", "sanitized partial", and "negative/invariance test" appear only in the question (line 417). The plan has a negative test and an "exact-key allowlist" phrase, but no denylist, no sanitizer, and no invariance test. The question cannot be answered "agree".
2. **§6.5's "Phase 6 L half-width ≈0.117" is the single-arm width**, not `CI_D`'s width. Using it to argue `EQUIVALENT` is rare is the wrong scale; the paired width is `0.037573`.
3. **§6.4's `.05` "signal threshold" is inert** because `CI.lower > 0` at SE ≈0.0594 requires mean ≈0.117.
4. **§0 item 5's four init controls exist only in §0**, not in §4 or §5. A reviewer who reads §0 as a manifest would approve controls that are not specified.
5. **"This is stronger than a seal: the values are never materialized in D1" (line 163)** is not established while the evaluator is undefined and 20-doc step0/final eval plus 480 M records are required.

## 10. Final

```text
최종 판정: NARROW

Init: disagree
  RNG order/reseed is structurally sound and fixes a real Phase 6 confound
  (c5_pm_phase6.py:142-160 has no LoRA reseed). But §0 item 5 promises a
  step_seed golden table, a tensor/RNG serialization frame, post-step0 weight
  non-equality, and an all-3-seed audit; none are in §4/§5. "F0 E11 != Phase 6 L"
  is still an assertion, not an I/O check.

D1: conditional
  Digest-delete-absent now resolves the round-10 contradiction. Still missing:
  the mechanics evaluator's computation scope (must never compute wrong-donor
  CE), a literal key list, a denylist, and an invariance test. Q2's premises
  are not in the plan.

STOP/MDE: taxonomy agree, arithmetic agree, rationale disagree
  Four states are exclusive/exhaustive; PASS and EQUIVALENT are disjoint;
  PASS and ROUTE_STOP are disjoint. SE 0.019170 / half-width 0.037573 trace to
  labels.json L_COPY_SIGNAL.paired (n=15, n_boot=1000). 0.054 and 0.0876 check.
  But §6.5 uses the single-arm 0.117, not the paired 0.0376, and §6.4's .05
  threshold is inert against CI.lower>0.

Cohort: conditional
  15 length-eligible + fixed donor graph, 20-doc descriptive only, is now
  correct and matches preflight (15/20, K=753, 5 excluded). Donor-cluster
  sensitivity has no method; the donor map is neither named nor hashed.

Compute: conditional
  900 updates, D1 25 min, R 96 min are coherent against 1,180.6s and 82.3 min.
  t_proj_f0 is undefined; t_proj_seconds cannot be reused (hard-coded
  F/L/P/PA + nine terms); setup_s is charged three times in §12 line 361;
  runner/c5_pm_f0*.py does not exist, so the provenance precondition blocks D0.

Scope: agree
  H3 fully removed, ROUTE_STOP limited to route-only, descriptive contrasts
  no-inference, dropped null/1-seed controls recorded, D0/D1/R approvals
  explicit.

Must-fix (ranked):
  1. Write the init audit that §0 claims: step_seed golden vector for
     20261108/09/10/20261111; cite prereg §12.1 frame
     (name_len|dtype|ndim|shape|nbytes|LE bytes); add post-step0 weight-change
     assert; add an init-only audit over the three Stage R seeds before R.
  2. Define c5_pm_f0_mechanics.py's computation: real-copy CE + M only, never
     wrong-donor CE; enumerate the exact d1_mechanics.json keys; add denylist
     and invariance test; clarify labels_computed:false = decision labels.
  3. Define t_proj_f0 (arms, terms, slowest-arm max) and fix setup accounting
     to setup_s + 3 x (per-wave terms).
  4. Commit runner/c5_pm_f0*.py at a recorded SHA, record code_commit/command/
     input SHA in D0/D1/R, and add an I/O assert that no Phase 6 checkpoint is
     opened (replaces the untestable "F0 E11 != Phase 6 L").
  5. Operationalize donor-cluster sensitivity (donor-clustered bootstrap or
     leave-one-donor-out) and hash the frozen donor map.
  6. Rewrite §6.5 with the paired width 0.0376 and state that §6.4's .05
     mean threshold is dominated by CI.lower>0 (effective floor ~0.117).
  7. Assert n_boot==10000 is recorded and forbid importing l_predicate in the
     F0 gate (c5_pm_labels.py:54-60 hardcodes 1000).

Approval: withheld. No D0/D1/R. Move to CONTINUE only after MF-1..MF-4 are
closed in a v1.2 and the F0 drivers are committed; MF-5..MF-7 can close at the
D1/R gate if they are stated as gate assertions.
```

## 11. Boundaries observed

- No training/evaluation; no test-163/P1; no subagents; no threshold/seed/donor/step/LR change.
- No repository change other than this file.