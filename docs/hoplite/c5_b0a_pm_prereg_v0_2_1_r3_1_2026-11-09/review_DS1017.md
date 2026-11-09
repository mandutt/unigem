# C5 Phase 6 P/M Prereg v0.2.1-r3.1 — Independent Review (DeepSeek V4.1 Flash 1017)

- Reviewer identity: **DeepSeek V4.1 Flash 1017**, Hoplite model ID **`deepseek-v4.1-flash-1017`** (OpenRouter), reasoning **high**.
- Review round: independent, separate from the r3 split review. This is not a reuse of any other model's answer.
- Review date: 2026-11-09.
- Sync result: `git fetch origin` + `git pull --ff-only origin main` → already up to date.
- **HEAD reviewed: `c4ed30a1f120b01905291602e3aec53f87c765fc`** (`docs: add C5 P/M v0.2.1-r3.1 review request`).
  - The request header cites `7264c55`; HEAD is two documentation commits later and includes the request file itself. The r3.1 plan blob I reviewed is at this HEAD.
- Preflight hash verified: `sha256(reports/provenance/C5_b0a/m_cohort_preflight.json) = 3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` — **matches** the request.
- Constraints honored: no training, no evaluation, test 163 not opened, P1 unused, no subagents/additional LLMs, no repository edits other than this file. T5Gemma2 remains D-108 STOP. Phase 6 / B0-B / B1 / B2 / Stage C are **not** approved by this round.

---

## 0. One-line conclusion

> **NARROW.** r3.1 genuinely closes all nine declared r3 residuals at the text level, and the factored decision function is close to total and executable. But it is not yet a safe freeze: (1) §9.2 silently changes `L_FULL_SIGNAL` from `mean delta_full > 0` (v0.2 §218, v0.2.1-errata §314) to `>= .05` while §0 claims "no threshold change"; (2) §8.2 replaces r3's fixed `M_NORM` formula with an unpinned "target-dependent" statement; (3) the D1 projection omits generation and the 20-train M build, so `T_proj <= 96 min` can pass while the 2 h cap is exceeded; (4) the checkpoint/replay hash is named but never canonically defined; (5) the B0-B predicate still admits `tail_driven=true` via "(or explicitly reported)". These are text/contract defects that must be repaired in r3.2 before freeze. Implementation, D0, D1, and 3-seed are not approved.

---

## 1. Baseline facts I was able to verify myself

| Item | Evidence |
|---|---|
| r3.1 plan length | 771 lines (`docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_1.md`) |
| r3 plan length | 795 lines |
| Preflight hash | `3ee3f1ca…69837af` — recomputed, matches |
| Preflight essentials | `k_m_l=753`, `l_contributors_at_k=16`, `l_target_eligible_at_k=15`, `common_cohort_at_k=15`, `native_contributors_at_512=20`, `full_k_secondary.l_target_eligible=11`, `k_selection.zero_margin=true`, `next_k=754 → 14` |
| Existing runner stats | `bootstrap_paired(..., seed=20261108)` and `"seeds_positive": int((arr > 0).sum())` (document count) — exactly the defect r3.1 §9.2 is meant to close; confirms the residual was real in code |
| Existing tests | `eval/tests/test_c5_b0_metric.py` has 7 test methods, all P0/metric/donor/mode; **no PM decision-contract tests exist yet** |
| P0 | train Δcopy +3.7617, CI [1.8917, 5.6050], 14/20 positive; val +5.2375, CI [2.5013, 8.0753], 18/20 positive; val median 2.9739, top-3 share .4862; untrained real CE 12.7022/13.2352 > ln\|V\| 12.43 |
| P0 length | `p0_sanity` passes `args.target_max_length` (default 256) as `source_max_length`; registered M path is 512 — the 256/512 caveat is factually correct |
| P0 bootstrap seed | P0 used the runner default `20261108`, not the registered `20261109` — another reason P0 helpers must not be reused for the registered statistic |

I could not run the training/eval path by instruction, and I did not. All statements below are derived from the documents, the committed preflight, and the committed runner/tests.

---

## 2. Q1–Q12

### Q1. Total factored contract

- **Verdict: conditional.**
- **Evidence.**
  - The core fix is real: `ANDn`/`ORn`/`NOT3` are total (§2.2); `m_pass_l`(2), `m_valid`(4), `m_evaluable`(5) now have explicit distinct arities, and §2.2 forbids silent 3-arity truncation. r3's `m_valid = AND3(P/PA POS/NORM)` (r3 §8.5, 4 arguments through a 3-ary name) is genuinely corrected.
  - `validity_status` is total: the chain in §3.4 terminates in `else: VALID`, and every NA/false case is enumerated.
  - `control_status` is total: §4.3 terminates in `else: NOT_ASSESSABLE`.
  - `signal_status` is total: §5.3 terminates in a final `else: NOT_ASSESSABLE`.
  - **Residual totality defect (new/inherited):** §4.3 writes `elif p_valid is not true or pa_valid is not true: M_NOT_EVALUABLE`. This collapses `not_assessable` into the definite `M_NOT_EVALUABLE` instead of `NOT_ASSESSABLE`, which contradicts the tri-state total contract the section claims to implement. It is masked in the signal path because §5.3 consults `validity_status` first, but `control_status` as a standalone function is not tri-state-total.
  - **Residual precedence tier is implicit:** §3.3 (assay-level path NA) runs before §3.4 (P/PA validity), while `pa_step100_path_ok` NA is deliberately *not* in §3.3 and is evaluated *after* `p_valid`. The result is an asymmetry: `pa_path=NA + p_valid=false → P_STEP100_NOT_VALID` (F3), but `p_step100_path_ok=NA + p_valid=false → NOT_ASSESSABLE` (§3.3 wins). That may be intended (assay tier poisons everything), but it is neither stated as a tier nor covered by F1–F8, so a second implementation can legitimately read it the other way.
  - **Not executable as written:** §8.2's "M_NORM is magnitude-matched with target real-prefix norm; target-dependent" has no formula (see Q4/Q8).
- **Next steps.**
  1. Add a fixture for `p_step100_path_ok=NA + p_valid=false`, or state the two-tier precedence rule explicitly ("assay-tier NA precedes P/PA validity; P/PA path NA follows p_valid").
  2. Make `control_status` preserve NA for `p_valid`/`pa_valid` (NA → `NOT_ASSESSABLE`), or document why `M_NOT_EVALUABLE` is intended.

### Q2. L preservation

- **Verdict: agree (preservation is adequate), with one semantic caveat.**
- **Evidence.**
  - §5.2 splits labels into `*_VALIDITY_INVALID` vs `*_VALIDITY_NOT_ASSESSABLE` for all three of `L_SIGNAL`, `COPY_ONLY`, `FULL_ONLY`; the small-N family is retained unchanged (§5.2).
  - §5.4 requires raw L flags in every record and `(validity, control, signal, flags, reason)` together, with `signal_reason` on `NOT_ASSESSABLE`. This preserves the information even when a label is lossy.
  - `copy_only`/`full_only` remain `ANDn` with `NOT3`, so a missing full endpoint yields NA (not "copy only") — correct.
  - Caveat: `MEAN_CONTRAST_ONLY` is still emitted in the `l_signal == false` branch under `control_status == M_CONTROL_PASS` (§5.3). At that point *no* L mean contrast has been demonstrated; the label describes an M-control mean contrast. The name overstates. This is inherited from r3 §5.4 ("control PASS, no L signal"), not new, so it is not a preservation failure — but it should be renamed or gated on an explicit L mean-delta check.
- **Next steps.**
  1. Rename `MEAN_CONTRAST_ONLY` (e.g. `M_MEAN_CONTRAST_ONLY`) or require `mean delta_copy > 0 or mean delta_full > 0` before emitting it.
  2. Keep the `(validity, control, signal, flags, reason)` tuple as a hard output schema and test it.

### Q3. M preflight / cohort

- **Verdict: conditional (numbers legitimate; binding must be to the committed artifact).**
- **Evidence.**
  - Preflight is internally consistent: `k_m_l=753`, `l_contributors_at_k=16`, `l_target_eligible_at_k=15`, `common_cohort_at_k=15`, `common_ok=true`; `k_selection.zero_margin=true` with `next_k=754 → 14 target-eligible`.
  - M cohort is selected by **length only**, never by outcome — no selection leakage.
  - `full_k_secondary.l_target_eligible=11` is explicitly labeled "secondary only, not M gate" in the preflight and in r3.1 §8.1 — correct.
  - `zero_margin=true` means a single-document shift in the EG2 cache or tokenizer would move the cohort to 14 and make M not evaluable. The only adequate mitigation is to **load the exact 15 `common_ids` from the committed preflight blob**; r3.1 §8.3 says "exact 15 IDs from preflight hash", which is right, but the implementation contract should forbid recomputing lengths from the cache at run time.
  - The request's "K=753, 15/20 M" is accurate. P/PA has `native_contributors_at_512=20`; the gate is still the common 15 (r3 §8.5 stated "P/PA each variant evaluated on common 15 target IDs; full 20 P/PA M descriptive secondary"). **r3.1 drops that sentence**, leaving it ambiguous whether P/PA's 20-doc M is in scope.
- **Next steps.**
  1. Add: "implementation MUST read the 15 IDs from `m_cohort_preflight.json`; recomputation from `h_len` is non-conforming."
  2. Restore the r3 §8.5 statement that the full-20 P/PA M is descriptive secondary only.

### Q4. M builder / endpoint / replay

- **Verdict: conditional.**
- **Evidence — closed:**
  - `builder_ok` (§4.1, §8.2) now routes contributor shortage, non-finite M tensors, zero `||M_POS_MEAN||`, and zero `||real_prefix||` to `M_NOT_EVALUABLE`. Combined with `m_evaluable = ANDn(cohort, endpoint, seed, replay, builder)` this closes r3 residual 4 structurally.
  - `endpoint_ok` (§8.3) enumerates exact 15 IDs × 3 seeds × 4 arms × primary variants, finite real/control CE, `copy_ce != None`, copy tokens ≥5, no duplicate/missing ID, no 15→14 substitution, no target replacement. This is a real executable contract, materially stronger than r3.
  - Prelaunch vs post-run replay hash is now separated (§8.6, §10.5), and checklist item 14 requires only the prelaunch debug hash while item 18 is post-run only — correct.
- **Evidence — not closed:**
  - **Hash canonicalization is undefined.** `debug_replay_hash`, `final_checkpoint_hash`, `final_replay_hash` are named but no canonicalization is specified (key ordering, dtype, byte order, contiguous vs view, fp32 vs bf16, inclusion of LoRA A/B, adapter state order). Two conforming implementations can produce different hashes. For an "exact endpoint identity" contract this is a Must-fix.
  - **`M_NORM` regressed.** r3 §8.3 = `M_NORM = M_POS_MEAN * (||real_prefix_753||_F / ||M_POS_MEAN||_F)` (identical in errata §229, r1 §313, r2 §515) — one fixed matrix with a single scalar rescale. r3.1 §8.2 removes the formula and calls it "target-dependent". If taken literally (per-target norm matching), the control statistic changes; if not (single scalar from the target set), the wording is wrong. Also `builder_ok`'s `||real_prefix||_F > 0` then refers to an unspecified aggregate. This is a genuine new ambiguity introduced by a doc that claims to be text-neutral.
  - Contributor clause `>= 10` is vacuous given preflight 16/20; harmless but should not be presented as a live guard.
- **Next steps.**
  1. Define a canonical hash function (sorted state keys, dtype, byte order, tensor bytes) and add a golden-vector unit test.
  2. Restore the exact `M_NORM` formula, state whether it is one matrix or per-target, and define which `real_prefix` norm `builder_ok` checks.

### Q5. PA

- **Verdict: conditional.**
- **Evidence.**
  - Naming is correct: PA is an **acquisition control** (native memory + random adapter + decoder LoRA), `PA_STEP100_NOT_VALID` is the failure label, `ADAPTER_REGIME_LOSS` is banned, `PA_RETENTION` may be null and is not a gate (§7.2). This is materially better than treating PA as a selectivity arm.
  - Gaps: §7.3 fixes `make_adapter(seed)` and `torch.manual_seed(seed)` before LoRA init, but **PA's "random adapter" initialization distribution/seed derivation is not stated**; and "scale/geometry caveat 기록" (§7.2) is a placeholder with no content.
- **Next steps.**
  1. State the PA adapter init (same `make_adapter(seed)` as the frozen arm? a distinct derived seed? distribution).
  2. Write the scale/geometry caveat text (parameter count, prompt length, adapter vs memory geometry) instead of "record".

### Q6. Cap / D0 / D1

- **Verdict: conditional.**
- **Evidence.**
  - Arithmetic is consistent: 12 units × 100 = 1,200 updates; D0 0 updates ≤15 min; D1 4 arm-seeds ×1 ≤20 min; combined "1,204 updates / 155 min" = 1,200+4 and 120+15+20. ✓
  - D1 seed `20261111` shared, debug seed ∉ {20261108/09/10} (checklist item 7) — consistent.
  - `T_proj = 3 * sum_arm(100·t_train + t_step0_eval_20 + t_step100_eval_20 + t_M_build_15 + t_replay_15)` with `≤96 min` is the right shape and correctly multiplies by 3 seeds.
  - **Gap 1 (generation omitted):** the committed runner's `train_arm` calls `generate_arm` over all 20 val docs at `max_new_tokens` default 256 (`runner/c5_mt5_lora_b0.py`). D1's five timed phases (§10.3) contain no generation phase, and `T_proj` has no `t_generate_*` term. Because v0.2 lists "generation telemetry" as an expected output, generation is in scope; `T_proj ≤ 96` can therefore pass while the real 2 h wall cap is exceeded.
  - **Gap 2 (train build omitted):** §10.3 phase 4 is "M builder **20 train / 15 target**", but the projection term is `t_M_build_15` only. The 20-document train-side builder pass is not counted.
- **Next steps.**
  1. Add `t_generate_20_arm` (with the exact `max_new_tokens`) to the timed phases and to `T_proj`.
  2. Replace `t_M_build_15` with `t_M_build_20_15` (train 20 + target 15) and re-derive the 96-min gate.

### Q7. Statistics

- **Verdict: disagree (as written).**
- **Evidence.**
  - Executable parts are good: `n_boot=1000`, percentile 2.5/97.5, `bootstrap_seed=20261109`, unit = document, seed-average-before-bootstrap, `documents_positive`, `seeds_positive` restricted to seed means, top-3 share with null on zero/non-finite denominator, leave-top-3-out, `tail_driven = leave_top3_mean <= 0 or top3_share > .50`, `MARGINAL_SIGNAL_COHORT` non-gating (§9.1–9.2). This closes r3 residual 8.
  - **But §9.2 changes a threshold.** It writes `L_COPY_SIGNAL = mean delta_copy >= .05 …` and then `L_FULL_SIGNAL = same for full`, i.e. `mean delta_full >= .05`. The last explicit registered values are `L_COPY_SIGNAL: mean delta_copy >= .05` and `L_FULL_SIGNAL: **mean delta_full > 0**` (v0.2 §213–218; v0.2.1-errata §304–314). r3.1 §0 claims "threshold/seed/donor/step/LR 변경 없음". It also contradicts itself internally: §7.1 keeps `P_VALID = … delta_full_step100 > 0`. This is an undisclosed threshold change smuggled in as errata.
  - **Dropped caveat:** r3 §9 has "20-doc bootstrap CI는 anti-conservative일 수 있음". r3.1 §9.2 omits it. r3.1 is the operative doc, so the caveat must be restated.
  - Note: P0's CIs were produced with `bootstrap_paired` default `seed=20261108`; the registered statistic uses `20261109`. This is another concrete reason the P0 helper must not be reused (r3.1 already forbids reuse — correct).
- **Next steps.**
  1. Restore `L_FULL_SIGNAL = mean delta_full > 0 AND full CI lower > 0 AND paired L>F > 0 AND 2/3 seed means > 0`, **or** declare the `.05` full-side change explicitly as a new preregistration (not as errata) before any trained result.
  2. Restore the anti-conservative 20-doc caveat in §9.2.

### Q8. Remaining Must-fix (ranked) and new problems

- **Verdict: disagree that the residual set is closed.**
- **Declared residuals that ARE genuinely closed (my independent check):** ANDn arity (r3 residual 1), validity-NA labels (2), precedence-aware F1–F8 (3, with the p_step gap noted in Q1), builder_ok (4), endpoint identity/finite (5), D1 workload counts (6, partially), `n_signal ∈ {NA,0..20}` (7), stats module/2-of-3 (8, except the threshold change), per-axis truth-table strategy (9). That is 9/9 at the level of "the named residual got a concrete mechanism".
- **Remaining / new, ranked:**
  1. **Undeclared `L_FULL_SIGNAL` threshold change** `>0 → >= .05` (§9.2 vs §0, §7.1, v0.2 §218, errata §314). Highest severity: it changes a gate and violates the errata contract.
  2. **D1 projection understates the workload** — generation (20 docs × 256 tokens) and the 20-train M build are missing (§10.3–10.4). This can defeat the 2 h cap.
  3. **`M_NORM` formula removed and replaced by "target-dependent"** (§8.2), conflicting with the fixed formula in errata §229 / r1 §313 / r2 §515 / r3 §527; `builder_ok`'s `real_prefix` norm becomes ambiguous.
  4. **No canonical hash definition** for `debug_replay_hash` / `final_checkpoint_hash` / `final_replay_hash` (§8.6, §10.5).
  5. **B0-B tail gate weakened**: §14 "`tail_driven == false` **(or explicitly reported)**" lets a tail-driven result pass B0-B by merely reporting it.
  6. `control_status` collapses `p_valid`/`pa_valid` NA into `M_NOT_EVALUABLE` (§4.3) — tri-state loss (Q1).
  7. No fixture/tier statement for `p_step100_path_ok=NA + p_valid=false` (Q1).
  8. r3.1 dropped r3's P/PA full-20 "descriptive secondary" sentence and the anti-conservative caveat (Q3, Q7).
  9. PA adapter init seed and the scale/geometry caveat remain placeholders (Q5).
- **New problems r3.1 itself created:** #1, #3, #4 (new/regressed), #8 (regression). #5 and #6 are inherited but are exactly the kind of boundary a freeze review should catch.
- **Next steps.** Fix 1–5 in r3.2 text; 6–9 can be either r3.2 text or explicit implementation-contract clauses, but must be listed in the DoD.

### Q9. Freeze and implementation approval

- **Verdict: disagree with approving freeze + implementation + D0 now; conditional after r3.2.**
- **Evidence.** Freezing r3.1 as-is would freeze (a) an undeclared threshold change, (b) an under-specified control matrix, and (c) an undefined hash. Those are contract defects, not implementation details, so they cannot be deferred to "code after freeze". The rest of the contract (ANDn, F1–F8, labels, builder_ok, endpoint identity, n_signal, per-axis truth table) is strong enough that r3.2 should be small.
- **Required pre-implementation test/contract list (in addition to §13):**
  1. `ANDn` 2/4/5 arity tests; `m_evaluable` must be 5-ary and `m_valid` 4-ary.
  2. F1–F8 exact outputs, plus a `p_step100_path_ok=NA + p_valid=false` cell.
  3. All 17 named cells (§6.2) plus a "every label reachable" test over `{NA, 0..20}` × validity × control.
  4. `n_signal = NA, 0, 14, 15, 16, 19, 20` fixtures; `MARGINAL_SIGNAL_COHORT` at 15.
  5. `m_valid`/`M_CONTROL_INVALID` reachability; `m_pass_l` derivation.
  6. `builder_ok` zero / non-finite / contributor-short cases.
  7. `endpoint_ok` 15×3×4×2 with one missing ID, one duplicate, one non-finite CE, one `copy_tokens<5`.
  8. Stats module: `seed=20261109`, `documents_positive`, `seeds_positive` on seed means only, 2-of-3, top-3 share null guard; a static check that `runner/c5_mt5_lora_b0.py::bootstrap_paired` is not imported.
  9. Canonical hash golden vector.
  10. `M_NORM` formula + "no target label leakage" test.
- **Next steps.**
  1. Write r3.2 text-only with Must-fix 1–5.
  2. Re-review r3.2; on CONTINUE, freeze the commit hash.
  3. Then implement + unit tests; D0 remains a separate approval.

### Q10. D1 / 3-seed boundary

- **Verdict: conditional.**
- **Evidence.** The separation is structurally right: D1 is 4 arm-seeds ×1 update, separate approval, no labels, `not_a_result:true`; 3-seed is a separate gate and D1-less 3-seed is forbidden (§10.4, §11). Item 14 is prelaunch-only and item 18 is post-run-only, which is the correct split. But the 18-item checklist omits:
  - generation workload/time (Q6);
  - the canonical hash function (Q4);
  - "load the 15 IDs from the preflight artifact" (Q3);
  - PA adapter init seed (Q5);
  - the stats-module tests and the no-P0-helper static check (Q9);
  - an `M_NORM` formula/leakage test (Q4).
- **Next steps.** Add those as checklist items 19–24 and require them to be green before the 3-seed gate.

### Q11. B0-B

- **Verdict: conditional.**
- **Evidence.** §14 keeps the right boundary: `EXPLORATORY_L_SIGNAL` alone does not approve B0-B; `M_CONTROL_PREFIX753_COHORT15` must be quoted; full-K 11/20, P0, and `PA_RETENTION` are not B0-B evidence; B0-B/B1/B2/Stage C remain separate. The weakness is the parenthetical "`tail_driven == false` (or explicitly reported)", which converts a hard gate into a reporting requirement.
- **Restated B0-B predicate against r3.1 labels (as it should read):**
  ```text
  validity_status == VALID
  AND control_status == M_CONTROL_PASS
  AND signal_status == EXPLORATORY_L_SIGNAL
  AND m_pass_pos_l == true AND m_pass_norm_l == true      # m_valid true
  AND n_signal >= 15
  AND l_copy_signal == true AND l_full_signal == true     # restored thresholds
  AND tail_driven == false                                # hard, no parenthetical
  AND M_PASS_NORM_CONFOUNDED reported and not used as a pass claim
  AND leakage/mode/metric checks pass
  AND artifact complete
  AND separate prereg + explicit user approval
  ```
- **Next steps.**
  1. Delete "(or explicitly reported)" and make `tail_driven == false` hard.
  2. Add the explicit `n_signal >= 15` and `m_pass_*_l` conjuncts so the predicate does not rely on "implied".

### Q12. Final verdict

- **Verdict: NARROW.**
- **Evidence.** All nine declared r3 residuals have a concrete mechanism in r3.1 and most are genuinely closed. But four freeze-contract defects remain (undeclared full-side threshold change, D1 projection omission, `M_NORM` regression, undefined hash) plus a weakened B0-B predicate. A freeze now would lock an errata document that silently changes a gate, which is worse than a small r3.2.
- **Scope of this verdict:** r3.1 **not frozen**; implementation + unit tests **not approved**; D0 **not approved**; D1 **not approved**; 3-seed **not approved**; B0-B/B1/B2/Stage C **not approved**; maximum compute **0**; test 163 **sealed**; P1 **unused**; T5Gemma2 **D-108 STOP**.

---

## 3. Wrong premises in the request / artifacts (잘못된 전제)

1. **"r3.1 adds stats module/2-of-3" implies pure restatement.** It does not: §9.2 changes `L_FULL_SIGNAL` from `> 0` to `>= .05`. §0's "no threshold change" is false for the full endpoint.
2. **"r3.1 adds builder_ok/M norm routing" implies M_NORM is unchanged.** It is not: the fixed formula from errata/r1/r2/r3 is removed and replaced by a "target-dependent" description.
3. **"D1 workload ... closed"** is only partially true: eval counts are now explicit, but generation and the 20-train builder pass are absent from the projection, so the 96-min gate is not a ceiling on the real workload.
4. **"54 tests pass historically"** is not evidence for this contract. The committed `eval/tests/test_c5_b0_metric.py` has 7 tests and none exercise the PM decision function; the PM tests do not exist yet (r3.1 §13 correctly says code comes after freeze).
5. **P0 is being over-read if treated as a threshold baseline.** Val is positive (+5.2375, 18/20) but median 2.9739 and top-3 share .4862, and untrained real CE 12.7/13.2 exceeds `ln|V|=12.43`. P0 is path/metric sensitivity only; it cannot set or justify the L thresholds, and its CIs used seed `20261108`.

---

## 4. Must-fix (ranked, for r3.2)

| Rank | Must-fix | Location | Why it blocks freeze |
|---:|---|---|---|
| 1 | Restore `L_FULL_SIGNAL = mean delta_full > 0` (or declare the `.05` full-side change as a **new** preregistration) | §9.2 vs §0, §7.1, v0.2 §218, errata §314 | Undeclared gate change; violates the errata contract |
| 2 | Add generation (20 docs, exact `max_new_tokens`) and the 20-train M build to D1 phases and `T_proj`; re-derive `≤96 min` | §10.3–10.4 | Projection can pass while the 2 h cap is exceeded |
| 3 | Restore the exact `M_NORM` formula; state one-matrix vs per-target; define which `real_prefix` norm `builder_ok` checks | §8.2, §8.4 | Control is not executable / drift from r3 |
| 4 | Define a canonical checkpoint/state/replay hash and add a golden-vector test | §8.6, §10.5, §11 item 14/18 | "Exact" endpoint/replay contract is not reproducible |
| 5 | Make `tail_driven == false` a hard B0-B conjunct; drop "(or explicitly reported)" | §14 | Weakens the downstream gate |
| 6 | Preserve NA in `control_status` for `p_valid`/`pa_valid`, or document the intended collapse | §4.3 | Tri-state total contract (Q1) |
| 7 | Add `p_step100_path_ok=NA + p_valid=false` fixture or state the precedence tier | §3.3–3.6, §6.2 | Precedence asymmetry uncovered by F1–F8 |
| 8 | Restore r3's P/PA full-20 "descriptive secondary" sentence and the anti-conservative bootstrap caveat | §8.1, §9.2 | Regressions in the operative doc |
| 9 | Fix PA adapter init seed and write the scale/geometry caveat text | §7.2–7.3 | PA is not fully specified |

---

## 5. Final verdict block

```text
최종 판정: NARROW
r3.1 동결: 아니오 (r3.2 text-only repair 후 재검토)
구현+unit tests: 미승인 (r3.2 freeze 후)
D0: 미승인
D1: 미승인
3-seed: 미승인
금지 범위: Phase 6 실행, B0-B/B1/B2/Stage C, test 163 열람, P1 사용, T5Gemma2 재개, 결과 후 threshold/seed/donor/step/LR 변경
최대 compute: 0 (이번 라운드는 검토만)
Must-fix (ranked): 위 §4의 1–9
잘못된 전제: 위 §3의 1–5
```

**Stop conditions I am asserting for the next round.** r3.2 must be text-only, must not alter thresholds other than by explicitly re-declaring the full-side value, and must not be frozen on the strength of this review. If Must-fix 1–5 are closed in r3.2, a subsequent round may move to CONTINUE(conditional) for freeze + implementation + D0. B0-B / B1 / B2 / Stage C remain out of scope for this and the next round.

---

## 6. What I did not verify

- I did not execute training, evaluation, D0, D1, or the runner. Runtime values (timings, actual CE) are not verified by me.
- I did not open test 163 and did not use P1.
- I did not modify any repository file other than this report.