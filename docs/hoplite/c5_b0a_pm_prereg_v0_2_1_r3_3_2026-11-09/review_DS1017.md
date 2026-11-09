# C5 Phase 6 v0.2.1-r3.3 — Independent External Review

- Reviewer: **DeepSeek V4.1 Flash 1017** (Hoplite model ID `deepseek-v4.1-flash-1017`, OpenRouter), reasoning **high**.
- Date: 2026-11-09
- Review basis: `origin/main` HEAD **`2ed41f096dc66180a09804b8555abbb3d62f7db5`** (`docs: add C5 P/M v0.2.1-r3.3 review request`), obtained by `git fetch origin` + `git pull --ff-only origin main` ("Already up to date").
- Target: `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_3.md` (1,031 lines), content SHA-256 **`5e67f21f…39f6a62`**.
- Preflight: `reports/provenance/C5_b0a/m_cohort_preflight.json`, content SHA-256 **`3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`** — **recomputed and matched**.
- test 163: **sealed, not opened**. P1: **not used**. T5Gemma2: **D-108 STOP 유지**.
- No training, no evaluation, no model forward, no repository modification. This file is the only write.

---

## 0. Method, scope, limits

1. Read the review request and every listed artifact in full: r3.3, r3.2, the r3.2 3-AI synthesis, the preflight JSON, the P0 report, `runner/c5_mt5_lora_b0.py` (lines 1–802 inspected, incl. `token_losses`, `copy_ce`, `donors_for`, `bootstrap_paired`, `evaluate_arm`, `set_training_mode`, `train_arm`), and `eval/tests/test_c5_b0_metric.py`.
2. Mechanically re-derived the whole decision contract: 9 L pairs (§2.4) against §2.3/`ANDn`/`NOT3`; the validity tier (§3.2–3.5) against F1–F11; dispatch (§5.3) against fixtures 16–18 and every label in §5.2.
3. Re-derived the arithmetic: 12 units × 100 = 1,200; +4 D1 = 1,204; 120 + 15 + 20 = 155 min; `T_proj` ≤ 96 min.
4. Recomputed artifact hashes with `sha256sum`; counted the suite (`54` `def test_` across 7 files, of which `7` are C5-B0/P0 metric tests and **0** are P/M decision tests).
5. Limits: the workspace is a depth-1 clone (`git rev-list --count HEAD` = 1), so the request's stated basis commit `148d5c1` is **not resolvable locally**. I reviewed the file content at `2ed41f0`, which is the only version present and is the commit that also adds this round's request and preflight. I did not use another model's answer; the r3.2 synthesis was read only as baseline evidence.

---

## 1. One-line conclusion

> **NARROW.** r3.3 really does close the 15 listed r3.2 blockers, and the **decision function (§2–§5) is total and executable** as written — I verified every conjunction, the 9 L pairs, F1–F11 and fixtures 16–18 by hand. What is *not* yet executable is the **scoring/analysis contract that feeds the decision function**: the M arm × builder matrix omits arm **F** while §8.4 requires 4 arms; the adapter space of `real_prefix_t` in `M_NORM` is undefined; the `n_signal` cohort contradicts the preflight (val20/0..20 vs 15 eligible); `tail_driven` never names its input endpoint yet hard-gates B0-B; `adapter_lr: 1e-3 (PA only)` contradicts the new §7.4 arm table; and the `T_proj` ledger drops the real/control factor in phases 5 and 7. All are text-only, so r3.3 is close — but freeze now would freeze ambiguous numbers.

---

## 2. Evidence checked (all confirmed unless marked)

| Check | Result |
|---|---|
| preflight content SHA-256 vs request | `3ee3f1ca…37af` — **match** |
| `common_cohort_at_k` / required | 15 / 15, `common_ok: true`, 15 `common_ids` |
| `l_contributors_at_k` | **16** (r3.3 §8.2 never states it; r3.2 said 16) |
| `native_contributors_at_512` | 20 (P/PA) |
| `full_k_secondary.l_target_eligible` | 11/20 — matches §8.1 "full-K L 11/20 secondary" |
| K selection margin | `k=753`, **`next_k=754 → 14 target-eligible`, `zero_margin: true`** |
| L pairs §2.4 → §2.3/`ANDn`/`NOT3` | **all 9 rows re-derived, consistent** |
| F1–F11 → §3.2–3.5 | **all 11 consistent** |
| Fixtures 16/17/18 | **derive correctly** (PASS/EXPLORATORY; PASS/MEAN_CONTRAST_ONLY; FAIL/NO_AFFIRMATIVE) |
| `false+NA` → `NOT_ASSESSABLE` only | **confirmed** (`copy_only=false`, `full_only=NA`, `l_signal=NA`) |
| Cap arithmetic | 1,200 / 1,204 / 155 min / 96 min — **correct** |
| 54 historical tests | **confirmed**: 7 files, 54 `def test_` |
| P0 values in request | match `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md` (train +3.7617 [1.8917,5.6050]; val +5.2375 [2.5013,8.0753]) |
| legacy runner pitfalls | `bootstrap_paired(..., seed=20261108)`, `seeds_positive = (arr>0).sum()`, donor-crop `k=min(len(real),len(wrong))`, `adapter_lr` default 1e-3 used for **both** F and L — all confirmed in code |

---

## 3. Answers

### Q1. Total factored contract

- **판정: agree**
- **근거**: §2.2 `ANDn/ORn/NOT3` are total on `{true,false,NA}`; §2.4's 9 pairs are exactly the closure of §2.3 under `copy_only = ANDn(l_copy, NOT3(l_full))` / `full_only = ANDn(l_full, NOT3(l_copy))` — I re-derived all 9 rows and each `l_signal`/`copy_only`/`full_only` cell matches. §3.2→§3.4 is a total priority chain and §3.5's three tier examples all follow it (`pa_path=NA,p_valid=false → P_STEP100_NOT_VALID` is correct because §3.4 tests `p_valid` before `pa_step100_path_ok`). §4.3's `control_status` chain covers all 5 enumerated values. §5.3 is total: `n_signal` NA is handled first, then `n_signal<15`, then validity NA, then validity≠VALID, then `copy_only`, then `full_only`, then `l_signal=NA`, then `l_signal=true` (all 5 control values incl. `else → L_SIGNAL_CONTROL_NOT_ASSESSABLE`), then the `l_signal=false` control ladder, then `else → NOT_ASSESSABLE`. No input combination falls through. Small-N precedence (§5.5) is deliberate and F11 matches it.
- **다음 단계**:
  1. Encode §5.3 as a pure function over an explicit input dataclass and property-test totality over the tri-state cross-product of (n_signal ∈ {NA,0..20}) × validity(5) × control(5) × L(9).
  2. Add one assertion that the *input* dict is unmutated (§6.4) and that raw flags survive a `NOT_ASSESSABLE` result.
  3. Fix the one naming drift: §2.3 consumes `l_copy_signal`/`l_full_signal`, §9.2 defines `L_COPY_SIGNAL`/`L_FULL_SIGNAL` — declare them the same objects or rename to one spelling; the DoD depends on the dispatch reading §9.2's predicate outputs.

### Q2. L consensus / fixtures

- **판정: agree**
- **근거**: With §2.3 single-authoritative and §9.2's `L_SIGNAL = ANDn(...)` deleted (confirmed by diff: the line is removed, not redefined), the only `l_signal` is the consensus. The observable divergence the r3.2 synthesis identified disappears: `copy=false, full=NA` now yields `l_signal=NA`, `copy_only=false`, `full_only=NA`, and §5.3 reaches `NOT_ASSESSABLE` via `elif l_signal is not_assessable` — **not** `MEAN_CONTRAST_ONLY` (`MEAN_CONTRAST_ONLY` requires `control_status==M_CONTROL_PASS` *after* the `l_signal` NA check). Fixture 17 is the only `MEAN_CONTRAST_ONLY` path and it has `l_signal=false` (both false), which is correct. Fixtures are primitive-derived and inject no `m_pass_l`/`m_valid`. §6.3's unreachable "control PASS + m_pass_l=false" cell is gone and replaced by an explicit prohibition.
- **다음 단계**:
  1. Add the 9-pair table to the DoD test matrix as *exact-label* assertions (currently §13 says "§2.4 9 L pairs", which is good, but must assert label, not just tri-state).
  2. Test that `copy_only`/`full_only` are evaluated before `l_signal` in dispatch (a refactor could reorder silently).
  3. Note that `l_signal=false + control=NOT_ASSESSABLE` collapses to the generic `NOT_ASSESSABLE` with no `NO_L_SIGNAL_*` prefix; that is acceptable but should be stated in §5.4 so reports do not look like a missing label.

### Q3. M preflight / cohort

- **판정: conditional**
- **근거**: The artifact is real and verifiable: hash matches, 20 train / 20 val, 5 val exclusions at 753, `common_cohort_at_k=15`, `common_ok=true`, full-K L 11/20 secondary. K is chosen by a pre-registered rule (`max K s.t. #train h>=K ≥10 and #val h>=K ≥15`), which is legitimate and not a post-hoc threshold. **But**: (a) the rule is at **zero margin** — `next_k=754 → 14`, so a one-token length change in one val document flips the cohort and forces `M_NOT_EVALUABLE`; and the target side is exactly 15 of 15 with `no 15→14 substitution` (§8.4), i.e. a single endpoint failure collapses the entire M control. (b) `l_contributors_at_k = 16` while §8.2's contributor rule is only ">=10" and r3.3 deleted r3.2's explicit "L contributors 16"; the frozen contract should state the expected 16/20 so implementation can assert it. (c) The bigger conflict is Q7/MF-3: §5.1 says signal cohort **val20**, `n_signal ∈ {NA,0..20}`, but L endpoints at K=753 exist for **15** val docs only, so `n_signal` cannot exceed 15 as written.
- **다음 단계**:
  1. State the expected contributor counts per arm (L 16, F 16 if F uses 753, P/PA 20) as assertable constants, not just ">=10".
  2. Pre-register the zero-margin failure path explicitly: one missing endpoint → `M_NOT_EVALUABLE` → labels NA; the plan already forbids 15→14, but the report should name this as an expected, non-rescuable outcome.
  3. Reconcile val20 vs 15 (see Q7).

### Q4. M builder / M_NORM / endpoint / replay

- **판정: conditional (disagree as written)**
- **근거**: The recipe (§8.2) and `M_NORM` (§8.3) are restored and are better than r3.2, and the replay key/framing (§10.6) is now a real wire format. But four material defects remain:
  1. **Arm F is missing from the M contract.** §8.1's `K_M` table lists only L=753 and P/PA=512; §8.2 says only "L uses `[:753]`; P/PA use `[:512]`". Yet §7.4 gives F memory K=753 and §8.4's `endpoint_ok` requires "**4 arms (F/L/P/PA)**" × "primary variants (M_POS_MEAN, M_NORM)". So F's `K_M`, builder and M existence are undefined while F is mandatory for `m_evaluable`. Either define F `K_M=753` + builder, or remove F from the M endpoint identity (F is the signal reference, not an M control — mixing the two sets in an M-evaluability gate is a scope conflation).
  2. **`real_prefix_t` space is undefined.** `M_POS_MEAN` lives in adapter-output space (mean of `A(h_i)`), but §8.3 defines `real_prefix_t` only as "target `t`'s real prefix at K_M". If the Frobenius norm is taken on raw `h_t` (EG2 embedding) while the numerator is `A(h_t)`, the magnitude match mixes two scales and `M_NORM` stops being a magnitude-matched control. Must state `real_prefix_t = A(h_t)[:K_M]` (and the same for the M primary reference and the M CE "real" memory).
  3. **Arm P has no adapter, but §8.2 applies `A` to every arm.** §7.4 says P is "decoder LoRA only", §7.2 says PA is the one with the random adapter. So §8.2 must state `A = identity` for P (and for PA, `A` is the random-init untrained adapter).
  4. **§8.2's condition is not type-correct**: "`for each contributor i in train20 with h_i >= K_M`" compares a tensor to an integer; it must be `h_i.shape[0] >= K_M`.
- Positives to keep: `M_GLOBAL` secondary, donor-crop prohibited for primary M, seed-level builder then seed-average before document bootstrap, `atol=1e-5, rtol=1e-4`, prelaunch vs final replay hash separation. The replay key `(doc_id, arm, seed, variant, endpoint, memory_kind, donor_id)` is well formed, but note the checkpoint frame never states the endianness of its integer fields (only of tensor bytes) and does not define the hash of an empty tensor set (F has no LoRA; P has no adapter).
- **다음 단계**:
  1. Replace §8.1/§8.2's prose with one **arm × (K_M, memory source, adapter?) matrix** covering F/L/P/PA, and state `A=identity` for P.
  2. Define `real_prefix_t := A(h_t)[:K_M]` explicitly in §8.3 and in the §8.5 M CE definition.
  3. Fix the `h_i >= K_M` typo and add the missing frame/endianness/empty-set clauses to §10.6.

### Q5. PA

- **판정: conditional**
- **근거**: The restored §7.2 caveat is correct and matters (PA memory = native mT5 512 vs L = EG2 layer19 753; PA is an *acquisition* control, not a retention comparison), `PA_STEP100_NOT_VALID` and `PA_RETENTION` non-gate are coherent, and `ADAPTER_REGIME_LOSS` is banned. Two problems:
  1. **New contradiction created by r3.3's arm table.** §7.3 says `adapter_lr: 1e-3 (PA only)`, but §7.4 says "`F` adapter trained; `L` adapter+LoRA trained" and PA has an adapter too. The runner confirms the truth: `train_arm` uses `args.adapter_lr` for the adapter in **both** the `frozen` (F) and `lora` (L) arms (`runner/c5_mt5_lora_b0.py:683,688`), default 1e-3. So "(PA only)" is wrong; it is "all adapter-bearing arms (F/L/PA)", with `lora_lr` on LoRA-bearing arms (L/P/PA).
  2. **PA vetoes the L M-control.** §4.2 sets `m_valid = ANDn(m_pass_pos_p, m_pass_norm_p, m_pass_pos_pa, m_pass_norm_pa)`, so a PA calibration failure forces `M_CONTROL_INVALID` for the L arm — even though §7.2 says PA is not directly comparable to L and PA's `M_POS_MEAN` is built from a **random-init, untrained** adapter. Gating the L control on a random-projection control is a design decision that needs an explicit sentence (and a stated fallback label) or a narrower `m_valid`.
- **다음 단계**:
  1. Correct §7.3 to "adapter_lr = 1e-3 for all adapter-bearing arms; lora_lr = 1e-4 for LoRA-bearing arms" and add a per-arm LR/parameter test.
  2. State whether PA failure invalidates the L M-control by design; if yes, say why the random-adapter PA is a meaningful veto.
  3. Add the PA label test (`PA_STEP100_NOT_VALID`, `PA_RETENTION` nullable) to the DoD test list.

### Q6. Cap / D0 / D1

- **판정: conditional**
- **근거**: Arithmetic is correct: 4 arms × 3 seeds × 100 = 1,200 (§10.1, §7.4); D1 = 4 units × 1 update; 1,200+4 = **1,204**; 120+20+15 = **155 min** (§10.5); `T_proj` includes generation 20×256, M build 20 train, initial M CE, donors 5, variants 2, copy/full 2, ≤96 min; D0 is 0 updates / ≤4 configs / ≤15 min / seed 20261111 and explicitly not a timing claim; D1 is `not_a_result`. The 8-phase list is coherent and phase 5 (initial fixed-prefix donor-free M CE) is the right repair for the r3.2 gap; "phase 2/3/7 only carry the donor factor" is stated. **But the ledger terms are dimensioned inconsistently with §10.6**: `t_initial_M_ce_15x2x2` and `t_replay_15x5x2x2` contain no factor for `memory_kind ∈ {real, control}`, while the replay key includes it. Phase 5 says "**real/M**" and phase 7's records are per `memory_kind`, so each of those terms is understated by **2×** (replay: 300 records/arm-seed as written → **600** per §10.6; phase 5: 60 → **120**). Since `T_proj ≤ 96 min` is the D1 gate, an undercount is not cosmetic.
- **다음 단계**:
  1. Add the real/control factor to phases 5 and 7 in both §10.3 and the `T_proj` formula (or explicitly state that replay scores one memory kind and the other is reused, which contradicts §10.6 then).
  2. State the legacy-loop basis of the 1-update → 100-update extrapolation (optimizer/step overhead included in `t_overhead_arm`), so the projection is auditable.
  3. Keep D1 as "no labels / `not_a_result`" and do not let its phases 2/3 generate any M or L label.

### Q7. Statistics

- **판정: conditional**
- **근거**: The stats module contract is good and correctly retires the legacy runner: `runner/c5_pm_stats.py` (new), `bootstrap_seed=20261109`, `documents_positive`, `seeds_positive` = seed mean only, no P0-helper reuse — and the runner indeed still carries `seed=20261108` and the mislabeled `seeds_positive = (arr>0).sum()` (`runner/c5_mt5_lora_b0.py:384–395`), so the prohibition is necessary and correct. `2/3 registered seeds` with "missing registered seed → predicate NA, no 2-of-available" is exact and matches §9.2. `n_boot=1000`, percentile 2.5/97.5, seed-average-before-document-bootstrap is executable. Three problems:
  1. **`tail_driven`'s input endpoint is never defined.** §9.4 gives exact numeric bounds but never says whether `leave_top3_mean`/`top3_share` are computed on `delta_memfree_copy`, `delta_memfree_full`, `delta_copy` (arm-L vs shuffled), or the paired `L−F`, nor which arm/variant. No earlier revision defines it either (r1/r3.1/r3.2 all define the formula only). Since §14 hard-gates B0-B on `tail_driven == false`, the gate is currently a predicate over an undefined quantity.
  2. **`top3_share` is declared "descriptive only" and simultaneously used as a hard gate.** §9.4 says "signed sum may fall outside [0,1]; descriptive only", then `tail_driven = true if … OR top3_share > .50`, and `tail_driven` is a B0-B hard gate. With signed deltas, a single dominant positive document surrounded by negatives can yield a *negative* share and mark the tail as non-driven. Pick one: either define the share on absolute values for gating, or make it non-gating.
  3. `n_signal ∈ {NA,0..20}` (§5.1) is unreachable above 15 for the L arm (Q3), so the "val20 signal cohort" and "MARGINAL at n_signal=15" statements do not compose: at the registered K, `MARGINAL_SIGNAL_COHORT` is true whenever anything is assessable.
- **다음 단계**:
  1. Write the exact statistic: `tail_driven` on `<endpoint>`, `<arm>`, `<variant>`, over the retained IDs, with `top3_share` defined on `|delta|` if it gates.
  2. Reconcile §5.1 with §8.1/§8.4 (15 vs 20) and restate the `n_signal` range accordingly.
  3. Add boundary tests at `leave_top3_mean ∈ {negative, 0, positive}`, `top3_share ∈ {.49,.50,.51}`, null and nonfinite inputs.

### Q8. Remaining Must-fix

- **판정: conditional**
- **근거**: 13 of the 15 r3.2 blockers are genuinely closed by text (L consensus, §6.3 cell, `NOT3`, `delta_memfree`, arm table, replay framing, phase 5, missing-seed 2/3, legacy stats ban, PA caveat, `endpoint_ok` single definition, §1.1, DoD); the two partial ones are **M builder/primary reference** (closed for L and P/PA, open for F) and **`tail_driven`** (formula restored, input quantity never defined). The residual list is in §4. **r3.3 also introduced new problems**, which is the important part of this answer: F is now required by §8.4 but absent from §8.1/§8.2's builder; §7.4's "F adapter trained" contradicts §7.3's "(PA only)" LR; and the `T_proj` ledger is dimensioned against a replay schema that includes a factor the ledger omits. None is a threshold change; all are text-only.
- **다음 단계**:
  1. Apply MF-1…MF-6 in a minimal **r3.4** (no threshold/seed/donor/step/LR change; these are definitional, not outcome-driven).
  2. Re-run only the contract re-derivation (no new review round needed if MF-1…MF-6 are text-only, per §16's own rule).
  3. Freeze the r3.4 commit hash and record it in the 3-seed checklist item 1.

### Q9. Freeze / implementation approval

- **판정: conditional (not on r3.3 as written)**
- **근거**: The pure decision function can be implemented and unit-tested now with high confidence — I found no defect in §2–§5. The *scoring* pipeline (M build, M_NORM, endpoint identity, replay, D1 phases) must not be written against the current text: MF-1 (F `K_M`/builder), MF-2 (`real_prefix_t` space), MF-3 (`n_signal` cohort), MF-5 (`adapter_lr`) would each be frozen into code and then into a checkpoint/replay hash. Existing coverage is 0 P/M decision tests (54 total, 7 C5-B0/P0), so the tests must be written from the frozen text, not from the runner.
- **다음 단계**:
  1. r3.4 (MF-1…MF-6 only) → freeze commit → protocol hash recorded.
  2. Implement **only** the pure decision function + stats decision layer + golden vectors; unit tests must include the 9 L pairs as exact labels, F1–F11, fixtures 16–18, `ANDn` arity 2/4/5, missing-seed → NA, tail tri-state, endpoint identity 15×3×4×2×(variants 2).
  3. D0 (0 updates, ≤4 configs, ≤15 min, seed 20261111, `labels_computed:false`) only after tests are green; D0 must not touch M or replay.

### Q10. D1 / 3-seed

- **판정: agree (with additions)**
- **근거**: Keeping D1 (4 units × 1 update, ≤20 min, no labels, `not_a_result`) as a separate approval and 3-seed as a later gate is the right boundary, and the checklist (§11, 23 items) is materially stronger than r3.2's. `debug seed 20261111 ∉ {20261108,09,10}` is correct and matches D0/D1. Missing items:
  - F-arm `K_M`/builder existence (MF-1) is not tested.
  - `real_prefix_t` adapted-space equality (MF-2) is not tested.
  - The `n_signal` cohort reconciliation (MF-3) is absent.
  - `T_proj` must be recomputed with the real/control factor (MF-6); the current "T_proj ≤96 min (8 phases)" could pass on an undercount.
  - The replay test must assert `memory_kind ∈ {real,control}` **and** `donor_id=null` for the donor-free primary M record (item 22 says variant/memory_kind/donor_id coverage — good, but the donor-free `null` case must be explicit).
  - Zero-margin failure reporting (one missing endpoint → `M_NOT_EVALUABLE`) should be a checklist item.
- **다음 단계**:
  1. Add checklist items for MF-1, MF-2, MF-3, MF-6 and the donor-free `null` donor case.
  2. Require the T_proj ledger to be printed per phase per arm so the 96-min gate is auditable.
  3. Keep "D1 없이 3-seed 금지" and "D0-only projection 금지" unchanged.

### Q11. B0-B

- **판정: agree**
- **근거**: §14 is a hard gate requiring validity VALID, control PASS, signal `EXPLORATORY_L_SIGNAL`, `m_valid==true`, `n_signal≥15`, `tail_driven==false`, leakage/mode/metric pass, complete artifact, and a separate prereg/approval; it explicitly says `EXPLORATORY_L_SIGNAL` alone is not approval, `tail_driven=NA` is not pass, and full-K 11/20 / P0 / `PA_RETENTION` are not B0-B evidence. Nothing in r3.3 auto-advances B0-B/B1/B2/Stage C. Restated to the r3.3 labels, the predicate remains:

```text
B0-B candidate ⇔ validity_status == VALID
              ∧ control_status == M_CONTROL_PASS
              ∧ signal_status  == EXPLORATORY_L_SIGNAL
              ∧ m_valid == true            # redundant consistency check
              ∧ n_signal >= 15             # implied by EXPLORATORY
              ∧ tail_driven == false       # input endpoint still undefined → MF-4
              ∧ leakage/mode/metric pass
              ∧ artifact complete
              ∧ separate prereg + approval
```

- Three of the conjuncts (`m_valid`, `n_signal`, control PASS) are implied by `signal_status == EXPLORATORY_L_SIGNAL`; that redundancy is fine as an assertion but should be labelled as such, and **`tail_driven` must not be a gate until MF-4 names its input**.
- **다음 단계**:
  1. Label the implied conjuncts as assertions to avoid two sources of truth.
  2. Resolve MF-4 before §14 can be executed.
  3. Keep the explicit non-evidence list (full-K 11/20, P0, `PA_RETENTION`) — it is correct and should not be weakened.

### Q12. Final verdict

- **판정: NARROW**
- **근거**: r3.3 is a real improvement: the decision function is total, the L double definition is gone, fixtures derive from primitives, `tail_driven` has numeric bounds, the arm table exists, replay has a wire format, phase 5 exists, and the cap arithmetic is right. It is **not** freeze-ready because six definitional defects (MF-1…MF-6) would be frozen into code and into hashes, and three of them (F `K_M`, `real_prefix_t` space, real/control ledger factor) affect the M control itself. This is a **NARROW**, not a STOP: no threshold, seed, donor, step or LR value is in dispute, and no result has been seen; the repair is text-only and can be done in one r3.4 pass.

```text
최종 판정: NARROW
r3.3 동결: 보류 — MF-1~MF-6 text-only r3.4 후 동결
구현+unit tests: r3.4 freeze 후 승인 가능 (pure decision function + stats layer + golden vectors 한정; M/replay/D1 코드는 MF-1/MF-2/MF-6 반영 후)
D0: r3.4 freeze + tests green 후 승인 가능 (0 update, ≤4 configs, ≤15 min, seed 20261111, labels_computed:false)
D1: 별도 승인 — 이 라운드 승인 아님 (4 units × 1 update, ≤20 min, no labels)
3-seed: 별도 gate — 이 라운드 승인 아님 (12 units, 1,200 updates)
금지 범위: 학습/평가 실행, test 163, P1, Phase 6/B0-B/B1/B2/Stage C, T5Gemma2(D-108 STOP), 결과 확인 후 threshold/seed/donor/step/LR 변경, donor-crop primary M
최대 compute: 이 라운드 0 (실행 없음). 승인 시 상한은 기존 등록값 그대로 — D0 0 update/≤15 min, D1 4 update/≤20 min, 3-seed 1,200 update/≤120 min wall, T_proj ≤96 min, threads 6, GPU 없음, retry 없음
```

---

## 4. Must-fix (ranked)

| # | Severity | Item | Where | Fix (text-only) |
|---|---|---|---|---|
| MF-1 | **blocker** | Arm **F** is mandatory in the M endpoint identity but has no `K_M`, no builder, no M existence; §8.2 also applies `A` to P, which §7.4 says has no adapter | §8.1, §8.2, §8.4, §7.4 | One arm × (K_M, memory, adapter?) matrix for F/L/P/PA; `A=identity` for P; define or exclude F's M explicitly |
| MF-2 | **blocker** | `real_prefix_t` space undefined; `M_NORM` numerator/denominator may mix raw EG2 embeddings with adapter-output mean | §8.3, §8.5 | `real_prefix_t := A(h_t)[:K_M]`; same for M primary reference and M CE "real" memory |
| MF-3 | **blocker** | `n_signal ∈ {NA,0..20}` / "signal cohort val20" contradicts L eligibility = 15 at K=753 (`l_target_eligible_at_k=15`) | §5.1, §8.1, §9.4 | Decide 15 vs 20 for signal endpoints; if 15, `n_signal ∈ {NA,0..15}` and say `MARGINAL_SIGNAL_COHORT` is automatic at pass |
| MF-4 | **blocker** | `tail_driven` input endpoint/arm/variant never defined, yet it hard-gates B0-B; `top3_share` is "descriptive only" but used as a gate | §9.4, §14 | Name the exact statistic and arm/variant; define the share on `|delta|` if it gates |
| MF-5 | **high** | `adapter_lr: 1e-3 (PA only)` contradicts "F adapter trained / L adapter+LoRA trained" and the runner, which uses `adapter_lr` for F and L | §7.3, §7.4 | "adapter_lr for all adapter-bearing arms (F/L/PA); lora_lr for LoRA-bearing arms (L/P/PA)" |
| MF-6 | **high** | `T_proj` terms for phases 5 and 7 omit the real/control factor that §10.6's replay key requires (2× undercount) | §10.3, §10.4, §10.6 | Add the `memory_kind` factor (rec 300→600 per arm-seed) and re-state the ≤96 min gate |
| MF-7 | medium | §7.4 contains unresolved drafting questions ("adapter only for F/P?", "F adapter trained? yes.") — not a frozen contract | §7.4 | Replace with declarative sentences |
| MF-8 | medium | Endpoint identity "15×3×4×2" omits variants (×2) and endpoints (already counted) — record count ambiguous (360 vs 720/1,440) | §8.4, §13 | Write the full product or a named `endpoint_record_count` |
| MF-9 | medium | PA (random-init adapter, different geometry) vetoes the L M-control via `m_valid = ANDn(P, PA)` while §7.2 says PA is not comparable | §4.2, §7.2 | State the rationale for the veto, or narrow `m_valid` |
| MF-10 | medium | Golden vector is produced by the implementation itself → pins behaviour, not the canonicalization spec; frame integer endianness and empty-tensor-set hash undefined | §10.6, §13 | Add an independent worked frame example with a hand-derivable digest; define endianness and empty-set hash |
| MF-11 | low | Zero-margin K (753; 754→14) and zero-margin cohort (15/15) mean one failure kills the M control | §4.1, §8.1, §8.4 | Pre-register the expected `M_NOT_EVALUABLE` path and its reporting |
| MF-12 | low | §0's global "copy threshold .05" vs §8.5's M copy `>0`; `l_copy_signal` vs `L_COPY_SIGNAL` naming; `builder_ok` partially restated in §8.3 | §0, §8.5, §9.2, §8.3 | Scope the §0 sentence to the L signal; unify names; dedupe `builder_ok` |

---

## 5. What r3.3 newly introduced (vs r3.2)

1. **F is now required by §8.4 but absent from the new M builder table** — the arm table (§7.4) and the M tables (§8.1/§8.2) were written independently and disagree.
2. **`adapter_lr: 1e-3 (PA only)`** becomes a contradiction only once §7.4 states that F/L adapters are trained; r3.2 had no arm table, so this is newly visible/created.
3. **`T_proj` phase 5/7 terms** were added in r3.3 and are dimensioned against a replay schema (also added in r3.3) that they do not match.
4. **§7.4 contains literal drafting questions**, which is new text in a freeze candidate.

Everything else in §1's closure table checks out against the diff.

---

## 6. Wrong premises in the review request (잘못된 전제)

1. "r3.3 fixes … M builder/arm table" — the M builder is fixed **for L and P/PA only**; F is outside it while §8.4 still requires F.
2. The r3.2 blocker list is treated as the complete defect set. It is not: MF-1/MF-5/MF-6 are r3.3-internal, not r3.2 leftovers, so "all r3.2 blockers closed" does not imply "freeze-ready".
3. "endpoint 15×3×4×2" (Q4 / DoD) understates the record count: with 2 variants and copy/full it is 15×3×4×2×2×2 = 1,440 CE numbers (720 per variant across endpoints), not 360.
4. The stated basis commit `148d5c1` is not resolvable in this depth-1 workspace; the reviewed content is HEAD `2ed41f0`. The content hash is recorded above so the review is reproducible against any clone.
5. "54 tests pass historically" is true (I counted 54), but **none** of them cover the P/M decision function — historical green is not evidence for this contract.

---

## 7. Non-approvals (explicit)

This review does **not** approve Phase 6 execution, B0-B, B1, B2, or Stage C. It does not reopen T5Gemma2 (D-108 STOP stands). It does not use or propose P1 or test 163. It proposes no threshold/seed/donor/step/LR change; every Must-fix above is a definitional clarification, and any item that would change a value must go to a new prereg instead.