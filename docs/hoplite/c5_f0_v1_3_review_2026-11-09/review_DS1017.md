# C5 F0 v1.3 — Independent Review (DS1017, new block round 3/10)

- Reviewed HEAD: `f5cc44b1bbe733523a3c66913eb5a719ebaa5872`
- `git fetch origin` / `git pull --ff-only origin main`: already up to date; tree clean.
- Target: `docs/plan_c5_f0_v1_3_2026-11-09.md` (536 lines, DRAFT v1.3, unapproved/unrun)
- Also read: `docs/plan_c5_f0_v1_2_2026-11-09.md`, `reports/C5_F0_V1_0_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_F0_V0_9_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `reports/C5_PM_PHASE6_RESULTS_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`, `runner/c5_pm_phase6.py`, `runner/c5_mt5_lora_b0.py`, `runner/c5_pm_stats.py`, `reports/provenance/C5_b0a/{m_cohort_preflight,labels/labels,cause_analysis}.json`, `reports/provenance/C5_b0a/registered/registered_report.json`.
- No training/eval, no test163/P1, no subagents, no repository modification except this file.
- This is an independent review; v1.2 conclusions are not inherited.

## 0. Verdict

| area | verdict |
|---|---|
| Init / serialization / pre-R audit (Q1) | **conditional** — one direct contradiction; hash-inequality control is tautological |
| D1 literal schema / seal (Q2) | **disagree** — schema and assertions are mutually unsatisfiable; artifact tree re-opens D1 |
| STOP / MDE proxy / P−PA (Q3) | **conditional** — taxonomy sound, MDE arithmetic correct, expected-branch sentence is wrong-signed |
| Cohort / donor count / LOO (Q4) | **agree with caveat** — declared and reproducible; power cost of 15 vs 20 |
| Compute 9-term / host (Q5) | **conditional** — 900 updates and 12 threads consistent; T_proj prose and setup accounting inconsistent |
| Scope / route-only (Q6) | **agree** |

**Final: NARROW.** The core E01−E11 design is sound and most v1.2 must-fixes are genuinely closed, but the prereg is not yet internally consistent at three points that would make an implementation either violate its own allowlist or rely on a non-informative control. These are text/contract fixes, not a scientific STOP.

## 1. Verified facts (recomputed at HEAD)

- `step_seed` golden table matches the stated formula exactly:
  - 20261108: `0x9f02514d / 0x3d5bdb86 / 0xdb9345df`
  - 20261109: `0x9f02514c / 0x3d5bdb87 / 0xdb9345de`
  - 20261110: `0x9f02514f / 0x3d5bdb84 / 0xdb9345dd`
  - 20261111: `0x9f02514e / 0x3d5bdb85 / 0xdb9345dc`
- MDE arithmetic: `.019170 × 1.96 = .0375732`; 80% gate mean `.05 + 2.8016 × .019170 = .10371 ≈ .104`; 50% boundary `.05 + 1.96 × .019170 = .08757 ≈ .0876`.
- `labels.json L_COPY_SIGNAL.paired`: mean `-0.002639`, CI `[-0.040845, +0.034302]`, n=15, n_boot=1000 → half-width `.037573`, SE `.019170`. The F−L provenance claim is accurate.
- `cause_analysis.json P_minus_PA`: mean `3.065202`, positive `14/15`; recomputed per-doc SD `2.40476`, SE `0.62091`. All four v1.3 numbers are exact.
- `m_cohort_preflight.json`: `common_ids` = 15, `train20` = 20, `k_m_l` = 753.
- Phase 6 registered wall: `wall_estimate_s = 4939.884` (82.3 min) for 12 units / 1,200 updates, cap 7,200 s. This is a better cap anchor than the D1 figure v1.3 cites.

## 2. Verbatim paired E01−E11 (mandatory)

All quotes are verbatim from `docs/plan_c5_f0_v1_3_2026-11-09.md` at the reviewed HEAD.

Primary statement (§2, line 65):

> - Primary: **E01 vs E11** (LoRA initialization matched).

Cell delta and paired contrast (§6.2–6.3, lines 208–219):

> delta_c(s,d) = mean_donor( CE_wrong_donor - CE_real )

> D(d) = delta_E01(d) - delta_E11(d)     # paired, same 15 docs
> mean_D = mean_d D(d)
> CI_D = bootstrap_paired_v2(D, n_boot=10000, seed=20261109)  # explicit override of frozen N_BOOT=1000

Positive predicate (§6.3, line 222):

> - Primary positive: `mean_D > 0 AND CI_D.lower > +.05 AND SIGNAL(E01,copy) AND 2/3 seeds D_s>0`.

ALL_FAIL definition (§7, lines 277–278):

> ALL_FAIL = FAIL(E01,copy) AND FAIL(E01,full)
>            AND FAIL(E11,copy) AND FAIL(E11,full)

Init equality assertions (§4, lines 103–107):

> 1. `lora_names` E01 == E11, length 64.
> 2. `sha256(lora_A/lora_B)` E01 == E11 at init.
> 3. `sha256(adapter)` E10 == E11 at init.
> 4. `post_init_rng_state_sha256` E01 == E11.
> 5. `post_step0_rng_state_sha256` E01 == E11.

## 3. Q1 — Initialization / serialization / pre-R audit

**Verdict: conditional.**

What is now adequate:

- F0-only `build_arm_f0` with `LORA_SEED_XOR` reset after adapter construction is the right structure; it makes E01/E11 LoRA init order-independent of adapter presence (lines 86–101).
- Per-step reseed is structural rather than assumed; dropout RNG equality follows because the adapter (Linear/GELU/Linear/LayerNorm) draws no RNG, so E01/E11 consume the same draw sequence before and after the reseed.
- The `step_seed` goldens are correct (Section 1), and the parenthesis fix in line 114 removes the precedence ambiguity.
- Group-specific weight change (13A.3) closes the v1.2 weakness that assertion 9 only required “at least one” parameter to move.
- Stage P (13A.1) is the right place to audit all three registered seeds before R.

Blocking defect — the two controls contradict each other:

- §4 line 118: “**Phase 6 I/O assert**: F0 must not open any Phase 6 checkpoint; `open`/`torch.load` path audit records zero Phase 6 paths. This replaces the untestable “F0 E11 ≠ Phase 6 L”.”
- §0 line 31: “F0 E11 init/final hash != frozen Phase 6 L hash; I/O path audit secondary.”
- §13A.6: “F0 E11 init and final hashes must differ from frozen Phase 6 L hash; I/O path audit is secondary.” / “Phase 6 checkpoint open count must be 0.”

These cannot both govern. Worse, the reinstated hash inequality is **tautological** under `build_arm_f0`: E11 reseeds with `seed ^ 0x5EED10A5` before attaching LoRA, whereas Phase 6 L attaches under `seed`; therefore E11 init (and consequently final) differs from Phase 6 L even if F0 read a Phase 6 checkpoint. The only non-tautological evidence of non-reuse is the I/O path audit. The primary/secondary ordering in §0 and §13A.6 is therefore backwards.

Secondary defect: 13A.2 says the serialization “expected SHA-256” is “included in `init_hashes.json`”. `init_hashes.json` is a run output; it cannot serve as a pre-run golden vector. Expected digests must live in a committed fixture (e.g. `docs/hoplite/.../golden_vectors.json` or a repo test fixture). The digest concatenation in §4 line 117 (“sorted key + `\0` + UTF-8 value”) also needs an explicit entry separator; otherwise distinct key/value splits can collide.

Next steps: make the I/O path audit primary and delete or re-justify the hash-inequality claim; commit serialization golden vectors outside the run output; add the entry delimiter.

## 4. Q2 — D1 literal schema / seal

**Verdict: disagree (approval blocker for D1).**

The schema at 13A.4 is literal and the crash/partial contract is good, but it is **not satisfiable together with §5 D1 assertions**:

| §5 D1 assertion | Required field | In 13A.4 allowlist? |
|---|---|---|
| #2 `updates_total == 3` (line 151) | `updates_total` | no (derivable, but named) |
| #4 `n_docs_step0 == 20`, `n_docs_final == 20` (line 153) | `n_docs_step0`, `n_docs_final` | **no** |
| #5 M records `120/cell`, total 480 (line 154) | per-cell `m_records` | no (only total) |
| #10 `labels_computed:false`, `not_a_result:true` (line 159) | `labels_computed`, `not_a_result` | **no** |

Because 13A.4 says “Only these keys”, an implementation that writes the fields needed to satisfy assertions #4 and #10 violates the allowlist; one that obeys the allowlist cannot run those assertions. `cells` only carries `{updates, lora_params, adapter_params}`, so neither the per-cell M count nor the doc counts fit.

Second, the §13 artifact tree lists `units/{cell}_{seed}.json`, `m_records_{cell}_{seed}.json`, and `checkpoints/{cell}/{seed}.pt` under the same root with no stage scoping. `units/...` is the per-doc `final` object, which §5 explicitly forbids D1 from writing (“D1 does **not** compute or write signal deltas, `per_doc`, phase7, or `final` objects”, line 163). The tree therefore re-opens the D1 seal unless it is annotated R-only.

Third, D1 sets `wrong_donor_ce_calls` to 0 (13A.4) while the primary `delta_c` requires wrong-donor CE. As a result the primary computation path is never exercised until the 96-minute R run. That is a deliberate sealing tradeoff, but it is a readiness risk worth stating explicitly; a mechanics-only dry run that counts wrong-donor calls without persisting values would close it.

Next steps: add the missing scalar keys (or delete the assertions that need them); add per-cell `m_records`; annotate every non-`f0_d1_mechanics.json` artifact as Stage R only; state the wrong-donor dry-run policy.

## 5. Q3 — STOP taxonomy / MDE proxy / P−PA

**Verdict: conditional. Taxonomy is sound; the expected-branch sentence is wrong-signed.**

Taxonomy check (§7, lines 276–308):

- States are exhaustive by priority: `NOT_EVALUABLE` → `PASS_POSITIVE` → `ROUTE_STOP` → `INDETERMINATE`, with `INDETERMINATE = not ALL_FAIL and not PASS_POSITIVE`.
- `PASS_POSITIVE` requires `CI_D.lower > +.05`; `EQUIVALENT` requires `CI_D.upper <= +.05`. They are disjoint, and `PASS` implies `SIGNAL(E01,copy)`, hence `ALL_FAIL` false. No overlap.
- `harm`/`benefit` are disjoint and both require `NOT EQUIVALENT`; the stated precedence `EQUIVALENT > harm > benefit` is well defined.
- `ALL_FAIL` is exactly E01/E11 × copy/full, excluding E00/E10; `ROUTE_STOP` correctly uses cell-level `FAIL`, not a 3/3 seed rule.

So Q3’s taxonomy question is answered yes. The problem is the rationale text.

Wrong-signed P−PA claim (§0, line 26):

> - P−PA(+3.065, 14/15)는 ROUTE_STOP 쪽; “undetermined; PASS와 ROUTE_STOP both live.”

`delta` is `CE_wrong − CE_real`, so positive means real memory beats the wrong donor. P (no adapter) = 3.076; PA (adapter) = 0.011; therefore adapter presence **removes** donor-specific signal. In the primary contrast that is `E01 (no adapter) − E11 (adapter) > 0`, i.e. the **PASS** direction, not `ROUTE_STOP`. `ROUTE_STOP` requires `ALL_FAIL`, which requires **both** E01 and E11 to fail; P−PA at most predicts that the adapter arm (E11) collapses. It says nothing that makes E01 fail. §6.5 (line 250) correctly says the branch is undetermined; §0 line 26 contradicts it.

MDE: the arithmetic is now correct and the transfer is honestly labeled a planning proxy. Two caveats remain:

- `.037573`/`.019170` come from the F−L **null-like** paired contrast (mean ≈ −0.0026, SD ≈ 0.074). P−PA per-doc SD is 2.405 (32× larger). The planning range is therefore `.0376` to `1.217` half-width; under the large-dispersion branch, `EQUIVALENT` (±.05) is unreachable and `PASS` needs `mean_D ≳ 1.27`. “Realized CI governs” is the right fallback, but the plan should say plainly that the experiment is effectively all-or-nothing across that range.
- Calling P−PA an “adapter-dispersion **upper bound**” is not justified; no confidence bound on the SD is computed. It is a reference dispersion, not an upper bound.

Next steps: correct §0 line 26 to the PASS direction (or delete the directional claim); rename “upper bound” to “reference dispersion”; state the large-dispersion branch explicitly.

## 6. Q4 — Cohort / donor count / LOO

**Verdict: agree with caveat.**

- 15 `common_ids` is real and frozen (`m_cohort_preflight.json`), and the plan declares it is length-selected at K=753 and forbids generalization to the 20-doc val population (lines 191–193). That closes prior DS-2.
- `donors_for(val20, cache)` is deterministic and length-nearest (runner line 318); with 19 candidates it always yields 5, and the same map is used for E00/E10/E01/E11, so the all-cell donor-set equality assertion is achievable.
- `evaluated_donors == 5 and expected_donors == 5` (13A.5) plus abort is the right replacement for the old silent drop. `eval_arm_d1` can still produce fewer than 5 when `copy_ce` returns `None` (<5 copy tokens), but Phase 6 endpoint coverage was 1,680/1,680, so this is a guard rather than a likely abort.
- LOO recomputation and declared donor reuse are adequate for a descriptive sensitivity range.

Caveat: the primary endpoint is donor-crop, where K is `min(len(real), len(donor))`; the 15-doc restriction is inherited from M’s K=753 requirement, which is unrelated to the primary endpoint. This discards 5 evaluable docs (25% of the cohort) and lowers power for no endpoint-driven reason. It is declared and therefore not a blocker, but the plan should state that the 15-doc choice is for comparability with the F−L/P−PA 15-doc artifacts, not because the donor-crop endpoint requires it.

## 7. Q5 — Compute 9-term / execution host

**Verdict: conditional.**

Consistent: R = 3 seeds × 3 trained cells × 100 = **900** updates; D1 = 3; D0 = 0. M 1,440, phase7 7,200, generation 240 are internally consistent with 4 cells × 3 seeds. 4 arms × 3 threads = 12 logical; `nproc >= 12` and the explicit disqualification of the 4-vCPU workspace (13A.7) are correct.

Inconsistent / under-specified:

- §12 line 366 says the nine terms “map 1:1 to Phase 6 §11.5: setup, step0 eval, 100 steps, M build, M CE, phase7 replay, primary replay, generation, overhead”. Phase 6 §11.5’s nine terms are: `100*t_train`, `t_step0_eval_20x5`, `t_step100_eval_20x5`, `t_M_build`, `t_initial_M_ce`, `t_generate_20x256`, `t_primary_replay`, `t_replay_15x5x2x2x2`, `t_overhead`. There is no `setup` term in Phase 6 §11.5. The prose substitutes `setup` for `t_step100_eval` and then adds the step-100 eval back as “separate”. The formula on line 367 is the correct nine; the prose enumeration is not 1:1 and should be corrected.
- Setup accounting is contradictory: line 367 puts `setup_s` **outside** the `3 × (...)`, but line 368 says “per-process/wave; if per-worktree, 4× per wave”. If each of 4 processes per wave loads the base, setup is `3 × 4 × per_process_setup`, not one `setup_s`. The plan defers this to “amortization must be proven in orchestrator commit”, but the cap cannot be evaluated until that is defined. Define `setup_s_effective` explicitly in the formula.
- The cap is anchored to the Phase 6 **D1** measurement (1,180.6 s, line 364), not the committed registered wall `4,939.884 s` (82.3 min for 1,200 updates). F0’s 96 min for 900 updates is plausible against 82.3 min, but the cited basis is the weaker one. Cite the registered wall as the anchor.

The 96-minute cap is not itself a blocker: with 900/1,200 updates and one registered wall of 82.3 min, 96 min is defensible; the `T_proj_R > 96 min` hard abort remains the protection.

## 8. Q6 — Scope / route-only

**Verdict: agree.**

- H3 is fully removed (lines 335–341); no arm, trigger, rank, identity, null, or donor-discrimination endpoint is registered.
- `ROUTE_STOP` is explicitly route-only and does not stop the EG2 track, rescue B0-B, or launch H3 (lines 469–472).
- Association-only, descriptive contrasts, and the lost MF-4 null / 1-seed gate are declared and cannot be claimed as replaced (lines 467–472).
- Phase 6 P/PA native-path evidence is not promoted to an EG2 mechanism claim; M_PASS is not donor-specific content-use evidence.

One addition: because F0 drops the zero/permuted null and the 1-seed D-level gate, the PASS claim should be phrased as “adapter-as-configured changes the donor-crop contrast in this fixed route”, not as a causal architecture claim. The plan already says this in §14; keep it in the result template too.

## 9. Regressions from v1.2

- v1.2 §0 item 8 required “`f0_r_labels.json` canonical; `f0_labels.json` alias forbidden; n_boot=10000 assert.” v1.3 keeps `n_boot=10000` in §6.1/§6.3 but **drops the assert and the alias ban** (`grep` finds no `f0_labels`/`alias` in v1.3). Restore it; otherwise the default `N_BOOT=1000` in `runner/c5_pm_stats.py` can silently re-enter through `l_predicate`.
- v1.2 §12 had eight terms inside the projection; v1.3 adds the step-100 eval (correct) but mislabels the resulting nine in prose (Section 7).
- v1.2 §6.5’s `±.0124` is correctly deleted; v1.3’s replacement sentence is correct, but §0 line 26 reintroduces a directional error.

## 10. Ranked must-fix

1. **MF-1 (blocker, D1):** Make 13A.4 and §5 D1 assertions mutually satisfiable. Add `n_docs_step0`, `n_docs_final`, `updates_total`, `labels_computed`, `not_a_result`, and per-cell `m_records` (or delete the assertions that require them). Annotate `units/`, `m_records_{cell}_{seed}.json`, `phase7_records/`, and `checkpoints/` as Stage R only; D1 writes only `f0_d1_mechanics.json`.
2. **MF-2 (blocker, init):** Resolve the §4 line 118 vs §0 line 31 / §13A.6 contradiction. Make the Phase 6 I/O path audit the primary non-reuse evidence; delete or explicitly justify the hash-inequality assertion, which is tautological given the added `LORA_XOR` reseed.
3. **MF-3 (blocker, expected branch):** Correct §0 line 26. P−PA (+3.065, 14/15) points to `D = E01 − E11 > 0` (adapter-free better), i.e. the PASS direction; it does not support `ROUTE_STOP`, which requires both E01 and E11 to fail. §6.5 is correct and should govern.
4. **MF-4 (high, statistics):** Restore the v1.2 `n_boot=10000` assertion and the `f0_labels.json` alias ban; explicitly forbid `l_predicate` for F0; assert the realized `n_boot` and seed in `f0_r_labels.json`.
5. **MF-5 (high, compute):** Fix the §12 nine-term enumeration to match Phase 6 §11.5 exactly (include `t_step100_eval`, exclude `setup` from the nine), and define `setup_s_effective` for the per-process/wave case. Cite the registered wall `4,939.884 s` as the cap anchor.
6. **MF-6 (medium, D1 readiness):** Add a mechanics-only wrong-donor call-count dry run (no persisted values) or explicitly accept that the primary wrong-donor CE path is first exercised in Stage R.
7. **MF-7 (medium, stage P):** 13A.1 says stage P “records all §4 assertions”, but assertion 9 (`post_step0_weight_change`) requires an optimizer step and stage P has none. Scope stage P to assertions 1–8 plus 13A.3, or state assertion 9 is N/A in P.
8. **MF-8 (low, serialization):** Move expected SHA-256 vectors out of `init_hashes.json` into a committed fixture; add an explicit entry delimiter to the canonical digest.
9. **MF-9 (low, terminology):** Rename “P−PA adapter-dispersion upper bound” to “reference dispersion”; no upper confidence bound is computed.

## 11. 잘못된 전제 (wrong premises)

- “P−PA는 ROUTE_STOP 쪽” — wrong sign; it is the PASS direction under the primary contrast.
- “F0 E11 init/final hash != Phase 6 L” as non-reuse evidence — tautological under `build_arm_f0`; only the I/O audit is informative.
- “T_proj 9항이 Phase 6 §11.5와 1:1” — the prose list swaps `setup` for `t_step100_eval`; the formula is correct, the enumeration is not.
- “D1의 유일한 출력은 `f0_d1_mechanics.json`” — true only if the §13 artifact tree is stage-scoped; as written it includes D1-forbidden `units/` and `checkpoints/`.
- “15 common은 primary endpoint가 요구” — it is inherited from M’s K=753, not from donor-crop; it is a declared comparability choice with a power cost.

## 12. Final

```text
최종 판정: NARROW
Init:      conditional — I/O audit vs hash-inequality contradiction; hash control tautological
D1:        disagree — literal allowlist cannot satisfy §5 assertions; §13 tree re-opens seal
STOP/MDE:  conditional — taxonomy sound, MDE arithmetic correct; P−PA sentence wrong-signed
Cohort:    agree with caveat — 15 frozen and declared; 25% power cost not endpoint-driven
Compute:   conditional — 900/12-thread consistent; T_proj enumeration and setup accounting inconsistent
Scope:     agree — H3 removed, route-only, association-only, lost controls declared
```

No execution approval is implied by this review. F0 remains unapproved and unrun; B0-B/B1/B2/Stage C remain unapproved; test 163 sealed; P1 unused; T5Gemma2 D-108 STOP.