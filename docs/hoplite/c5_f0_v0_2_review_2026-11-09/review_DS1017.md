# C5 F0 v0.2 — Independent Re-Review (DS1017)

- Review date: 2026-11-09
- **Reviewed HEAD: `185d2ff7b2c29aaa10093838335cb15901981657`** (`docs: revise C5 F0 draft to v0.2`)
- Workspace sync: `git fetch origin` → `main -> FETCH_HEAD`; `git pull --ff-only origin main` → `Already up to date.` No error. `origin/main` = `185d2ff7b2c29aaa10093838335cb15901981657`, identical to HEAD.
- Target: `docs/plan_c5_f0_v0_2_2026-11-09.md`
- Superseded reference: `docs/plan_c5_f0_2026-11-09.md` (v0.1)
- This is a **new independent round**. v0.1 conclusions are not inherited; every number below was re-read from the cited artifact or source file at this HEAD.
- No training, no evaluation, no test 163, no P1, no subagents. Repository unmodified except this file.
- The reviewed v0.2 phrase under test, verbatim: **“D0/D1 mechanics-only + Stage R 3-seed”** (`docs/plan_c5_f0_v0_2_2026-11-09.md` §12 Q1, line 189; also §0 item 1, line 21).
- Scope boundary: this review judges whether v0.2 can support the registered reading **adapter-associated donor-specific signal loss**, not a structural bottleneck diagnosis.

---

## 0. Summary

| Q | Topic | Verdict |
|---|---|---|
| Q1 | Stage D/R selection-bias removal | **conditional** |
| Q2 | E01 vs E11 2×2 validity | **conditional** |
| Q3 | route STOP vs track STOP | **conditional** |
| Q4 | M / signal / E00 baseline | **conditional** |
| Q5 | Compute realism | **conditional** |
| Q6 | H3 separation | **agree** |

**Overall: NARROW.** v0.2 fixes the two v0.1 blockers in principle: the 1-seed signal gate is removed (`§0` items 1–2, lines 19–24; `§4` lines 70–94) and track-level STOP is replaced by route-scoped language (`§0` item 3; `§5` line 115). The question and the four-cell skeleton remain the right next experiment. But v0.2 cannot yet be approved, for five concrete reasons:

1. **“LoRA fixed” is false at initialization.** In `runner/c5_pm_phase6.py` `build_arm`, `torch.manual_seed(seed)` (line 147) is followed by adapter construction (line 150) before LoRA attachment (line 153). The adapter consumes RNG before LoRA on E11 but not on E01, so the primary cells get different LoRA `lora_A` initializations. The primary contrast is therefore adapter presence **plus** LoRA-initialization difference.
2. **“D0/D1 mechanics pass” is undefined.** There is no closed list of pass criteria and no rule forbidding the operator from reading D1 signal telemetry and stopping. A discretionary gate can reproduce the v0.1 selection bias without a written §8 rule.
3. **The decision rule is still per-cell significance, not the paired contrast.** `§5` line 114 requires “E01 positive AND E11 negative AND E01−E11 >0”, but the primary endpoint is the paired `E01 − E11` CI (`§5` lines 101–110). The per-cell predicate pattern is a difference-in-significance argument and is not equivalent.
4. **STOP is not gated on protocol validity.** A negative under broken mechanics or a failed M calibration would be read as route STOP, not as “not evaluable”.
5. **Compute only works with unstated 4-way parallelism.** Phase 6 D1 measured **1,180.577 s (19.68 min)** with `parallel_arms: true`; the same four arms run sequentially took **3,116.5 s (51.94 min)** in recorded per-arm elapsed. v0.2’s D1 cap of 25 min is achievable only if F0 D1 is run in parallel, which `§4` does not state.

---

## Q1. Stage D/R selection-bias removal

**판정: conditional**

### What v0.2 fixes

- `§0` items 1–2 (lines 19–24) replace v0.1’s “1-seed 100-update → Stage R/STOP” with D0 0-update + D1 1-update, and state **signal gate 없음**.
- `§4` Stage R (lines 86–94) says three seeds `20261108/09/10` unconditionally after mechanics pass, and explicitly **No 1-seed signal gate**.
- D1 uses seed `20261111`, disjoint from the registered seeds `20261108/09/10` (`§3` line 66; `runner/c5_pm_phase6.py` lines 52, 337). That removes direct seed reuse.
- The registered documents are still the same frozen 15 common docs (`reports/provenance/C5_b0a/m_cohort_preflight.json`: `common_ids` = 15, `val20_ids` = 20, `train20_ids` = 20). That is unavoidable, but it means any inspection of D1 on those 15 docs is a draw on the same documents that Stage R will use.

### Why it is not yet selection-bias-free

**(a) The pass criteria are not enumerated as a closed rule.** `§4` D0 lists shape/module assertions (lines 70–78), but D1 only says “no decision labels; telemetry only” (line 84) and `§4` Stage R says “only after D0/D1 mechanics pass” (line 93). There is no statement of what makes D1 pass, no prohibition on reading `delta_shuffled_copy` at D1, and no rule that a mechanical pass forces R. “Mechanics pass” therefore remains an operator judgment.

**(b) There is no ban on interim looks during Stage R.** With three seeds, stopping after seed 1 because the contrast looks good or bad is still selection. `§4` forbids a *pre-R* 1-seed gate but does not forbid a *within-R* early stop or seed replacement.

**(c) Failure/retry handling is missing and internally inconsistent.** `§9` line 153 says “No retry/extension”, but D1 exists precisely to catch implementation faults. Phase 6 D1 actually ran twice: `reports/provenance/C5_b0a/d1/d1_report.json` records `attempt_1.status = failed`, reason `"inference tensor used in training backward for P/PA"`, `attempt_2.status = complete`. A no-retry rule applied to D1 would kill F0 for a fixable code bug; a silent rerun would create an unaudited selection point.

**(d) D1 is necessary; D0 alone is not sufficient.** D0 is 0 updates and cannot exercise backward, optimizer groups, gradient flow, clipping, or checkpoint save/load. Phase 6’s `attempt_1` failure is direct evidence that the training path can fail in exactly the way D1 is meant to catch. D1 is therefore justified — but only as a mechanical assertion stage, not as a signal screen.

### 다음 단계

1. Freeze a closed mechanical pass list in `§4`: exact shapes (753×512 for all four cells), LoRA module counts (0/0/64/64), adapter presence (absent/absent/present/present), finite step0 and post-update loss, nonzero gradients on expected parameter sets, checkpoint save/load, exact M/phase7/generation record counts. State explicitly: **any mechanical pass ⇒ Stage R proceeds unconditionally**.
2. Add: D1 signal numbers are written to artifacts but not read for a go/no-go decision; no Stage R interim analysis or early stop; a failed unit is fail-closed and is not replaced by a new seed.
3. Split retry policy: D1 may be rerun after a code fix with the failed attempt retained and marked `discarded`; Stage R has no retry.

---

## Q2. E01 vs E11 2×2 validity

**판정: conditional**

### What is valid

- Both E01 and E11 attach the same 64 decoder LoRA modules at `r8 alpha16 dropout .05` (`docs/plan_c5_b0a_pm_prereg_v1_0_11.md` §2.2, lines 138–156; `runner/c5_pm_phase6.py` `EXPECTED_LORA_MODULES = 64`, line 57) and run 100 updates. At the **module-set and LR-schedule** level, the LoRA side is held constant.
- E10 vs E11 is the cleanest secondary: both construct the adapter first from the same seed, so adapter initialization is identical between E10 and E11; E11 adds LoRA. This is a legitimate “LoRA with adapter” sensitivity.
- `§2` lines 50–56 now register all four marginal contrasts (`E10−E11`, `E10−E00`, `E01−E00`, `E01−E10`) and label the last as not clean causal. That is an improvement over v0.1 and is arithmetically correct.
- All four cells are EG2 layer19, so `donors_for(val_ids, cache)` gives identical `h_len`-based donor lists and identical `K_d = min(len(real), len(donor))` for all cells. This should be asserted as an artifact invariant; it is a real strength over Phase 6 P/PA, whose donor lengths differed by arm (prereg §2.5.6, lines 276–300).

### What breaks the causal reading

**(a) LoRA initialization is not held fixed (new blocker).** `build_arm` does:

```text
torch.manual_seed(seed)          # line 147
if spec["adapter"]:
    adapter = Adapter(512, 512)  # line 150 — consumes RNG
if spec["lora"]:
    attach_decoder_lora_mt5(model)  # line 153
```

`Adapter` is `Linear(512,512) → GELU → Linear(512,512) → LayerNorm(512)` (`runner/c5_mt5_layer_probe.py` lines 52–63); its Linear layers use default Kaiming/uniform initialization and therefore advance the global RNG. `LoRALinear` initializes `lora_A` with `kaiming_uniform_` (`runner/c5_a1_lora.py` lines 56–58), and `lora_B` is zero. Consequently:

- E01 (no adapter) and E11 (adapter) draw **different `lora_A` matrices** from the same seed.
- At step 0 the LoRA function is identical because `lora_B = 0`, but the first `lora_B` gradient is computed from `lora_A`; different A therefore produces different updates from step 1 onward.
- Labeling E01 vs E11 as “LoRA fixed” (`§2` line 50) is therefore false at the initialization level.

This also retroactively weakens the Phase 6 P vs PA reading: P has no adapter and PA does, so their LoRA A initializations differ too. That does not overturn the large P/PA contrast (+3.065, 14/15; P copy Δ 3.076 vs PA 0.011 in `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md` §2), but it is exactly the kind of confound F0 must eliminate rather than reproduce.

**(b) The adapter bundle adds 526,336 parameters at 10× LR.** `reports/provenance/C5_b0a/d0/d0_report.json` records `trainable_adapter_parameters: 526336` for F. The adapter trains at `adapter_lr: 1e-3`; LoRA at `lora_lr: 1e-4` (prereg §2.2). E01 trains only LoRA; E11 trains 526,336 adapter parameters plus LoRA. The contrast is therefore “adapter module as configured (capacity + LR + optimization path)”, not “adapter mapping alone”. Since these values are frozen from Phase 6 and `§14` forbids changing them, the correct fix is to **narrow the claim**, not to retune.

**(c) E00 is a degenerate cell, not a factorial cell.** E00 has no adapter and no LoRA; with the base decoder in eval, it has **zero trainable parameters**, so 0 updates is forced. The design is three trained cells plus one untrained reference, not a complete 2×2. `§2` line 52 and `§6` lines 123–124 correctly call E00 eval-only and non-trained, but the document should stop calling the whole design a 2×2 without that qualification, and must explicitly exclude E00 from all signal predicates.

**(d) E01 is not a neutral adapter-free baseline.** E01 feeds unnormalized raw EG2 layer19 `h` directly into mT5 cross-attention. The cause report’s representation table shows raw EG2 has between-doc variance **4.883**, the highest measured (F adapter 0.085, L adapter 0.081, native raw 0.841, PA adapter 1.284), with raw mean cosine 0.998. A negative E01 is therefore consistent with “EG2 contains no donor-specific information usable here” **or** “the raw EG2 basis/scale is off the mT5 decoder manifold and 100 LoRA updates cannot align it”. v0.2 §5 line 115 correctly refuses the stronger claim; the design should carry that limit explicitly into the E01 label.

### 다음 단계

1. Replace the shared RNG stream with per-component generators, e.g. `adapter_gen = torch.Generator().manual_seed(seed)` and `lora_gen = torch.Generator().manual_seed(seed)`, or always construct an adapter object (and discard it for E01) so both cells consume the same RNG before LoRA. Then assert at D0 that E01 and E11 `lora_A` hashes match and that E10 and E11 adapter hashes match.
2. Add D0 initialization-parity hashes to the artifacts; a mismatch is a mechanical failure, not a signal result.
3. Register the interpretation as “adapter module as configured (526,336 params, lr 1e-3)”, with E10 vs E11 as the LoRA-only sensitivity; do not claim a pure mapping effect.

---

## Q3. route STOP vs track STOP interpretation

**판정: conditional**

### What v0.2 fixes

- `§0` item 3 and `§5` line 115 delete the v0.1 track STOP and limit the negative reading to “this configured EG2-raw→mT5-decoder route does not show donor-specific signal”, adding “**not** proof that EG2 features lack information. Track decision separate.” That is the correct direction and removes the v0.1 §8 ↔ §1 H2 contradiction.

### What is still insufficient

**(a) The primary decision uses per-cell significance instead of the paired contrast.** `§5` line 114 requires the pattern “E01 positive AND E11 negative AND E01−E11 >0”. The endpoint is the paired document contrast `delta_E01(doc) − delta_E11(doc)` with a bootstrap CI (`§5` lines 101–110). “E01 significant, E11 not significant” is not the same as “E01−E11 significantly positive”; with correlated cells the paired CI is the correct test. The decision rule should be driven by the paired CI, not by two separate cell predicates.

**(b) The branch table is incomplete.** `§5` lines 114–117 define `(+,-)`, `(-,-)`, `(+,+)`, and “≈”, but not `(-,+)` — E01 negative while E11 positive. That pattern (adapter rescues a signal absent without it) is theoretically possible and would contradict the working “adapter-associated loss” reading; leaving it undefined invites post-hoc narration.

**(c) “E01 ≈ E11” has no equivalence margin.** Line 117 says “adapter effect not supported” without defining ≈. Non-rejection of `E01−E11` is not evidence of equivalence. Either predefine an equivalence bound (e.g., the paired CI entirely inside ±δ) or delete the branch and report “inconclusive”.

**(d) STOP is not conditioned on protocol validity.** If mechanics fail, M_PASS is false, or the endpoint is not evaluable, a negative cannot support even route STOP. `§5` does not distinguish “route negative” from “experiment failed”. Given `§6` line 123 explicitly makes M non-gating, this gap is live.

**(e) The `(+,+)` branch is under-specified.** Line 116 says “adapter not necessary under this regime; no structural adapter claim.” That is too flat: Phase 6 P vs PA showed adapter presence collapsed native signal from **3.076 to 0.011** (14/15 positive for P−PA, +3.065). An `(+,+)` F0 result would be a genuine EG2-vs-native discrepancy and should trigger a replication/anomaly check, not a generic “not necessary” conclusion.

**(f) Route scope should be exact.** “Route” should name: EG2 layer19 raw, 753-token memory, no adapter, decoder LoRA 64 modules r8/alpha16, 100 updates, 20 train docs, adapter-free E01; and E11 adds the 512→512 adapter at lr 1e-3. Anything broader (“EG2 route”, “resident track”) exceeds what F0 measures.

### 다음 단계

1. Make the primary decision `E01 − E11` paired CI (lower bound > 0, with a pre-registered minimum meaningful effect); treat the per-cell copy/full predicates as descriptive.
2. Add the `(-,+)` branch and replace “≈” with an explicit equivalence margin or an “inconclusive” outcome.
3. Gate STOP on: mechanics valid, endpoints evaluable, M interpretable, both cells fail copy and full on 3/3 seeds, and paired CI not >0. Otherwise label the run “not evaluable”, not “route STOP”.

---

## Q4. M / signal and E00 baseline

**판정: conditional**

### What is arithmetically correct

- M 120/cell/seed = 15 common × 2 variants (`M_POS_MEAN`, `M_NORM`) × 2 endpoints (`copy`, `full`) × 2 memory kinds (`control`, `real`). This matches prereg §9.5 (1,440 common records over 3 seeds) and v0.2 `§4` line 91.
- Phase 7 600/cell/seed = 15 docs × 5 donors × 2 endpoints × 2 memory kinds × 2 memory roles (real/donor). Stage R total 7,200, generation 240. The totals in `§4` line 91 are correct.
- M should **not** be a progression gate. Phase 6’s M table shows why: F control−real 0.576 / wrong−real 0.001, L 0.365 / −0.017, P 6.118 / 2.531, PA 0.576 / 0.013 — all M_PASS true, while `L_COPY_SIGNAL=false` with mean **−0.1135**, CI **[−0.2341, −0.0012]**, 6/15 positive, 0/3 seed means positive. M measures “real vs global mean”, not donor specificity; M_PASS is not content-use evidence.

### Why it is not yet sufficient

**(a) M should be a per-cell interpretability condition, not merely a reported number.** `§6` line 123 says M is reported separately and not a gate. Agreed for progression. But if `M_PASS` is false for a trained cell, a negative signal from that cell is **not evaluable**, not evidence of route failure. The plan needs that distinction explicitly; otherwise a “negative” can come from an arm that never learned to use memory at all.

**(b) The 15-document signal cohort cannot certify the frozen .05 threshold.** The val split has only 20 docs and 15 common (`m_cohort_preflight.json`), and `n_min_signal=15` is frozen (prereg §10.1). Phase 6 L’s 95% CI spans **0.2329** (−0.2341 to −0.0012), implying a doc-level SE of roughly **0.059** at n=15. For a true effect of 0.05 with a two-sided 95% CI lower bound > 0, one would need roughly `(0.059/0.0255)^2 ≈ 5.4×` the documents (≈81), which the 20-doc val split cannot supply. This is a proxy from the L arm and the paired contrast may be tighter, but the conclusion stands: **15 docs can resolve large effects (the Phase 6 P/PA effect was ~3), not threshold-scale effects near .05.** Reporting “no signal” from a CI that includes .05 is an overclaim.

**(c) The 2/3-seed rule is weak.** Under a null with per-seed positive probability .5, `P(≥2 of 3 positive) = 0.5`. The seed-average CI carries most of the evidence; 2/3 should not be presented as strong replication.

**(d) Donor/doc identity must be asserted, not assumed.** All four F0 cells are EG2 and therefore share `h_len` donor ordering, but the plan should assert identical 15 common docs, identical 5 donor IDs per doc, and identical `K_d` across E00/E01/E10/E11. Phase 6 already had to distinguish EG2 vs native donor regimes (prereg §2.5.6); F0 removes that difference but does not document the invariant.

### 다음 단계

1. Add “not evaluable” as an outcome when M_PASS is false or endpoint coverage is incomplete; a negative requires a passing M for that cell.
2. Predefine an “inconclusive” band for the 15-doc CI (e.g., CI lower ≤ 0 < upper and upper > .05) and forbid “no signal” language when the CI spans the threshold.
3. Assert and hash the identical 15 docs, 5 donors/doc, and `K_d` across all EG2 cells; explicitly exclude E00 from signal predicates.

---

## Q5. Compute realism

**판정: conditional**

### Measured evidence at this HEAD

- **Phase 6 registered:** 12 units, 1,200 updates, `wall_estimate_s = 4,939.884` = **82.33 min**, `cap_seconds = 7,200` (120 min), `cap_ok = true`, `parallel_units_per_wave = 4`; wave maxima 1,661.1 / 1,751.4 / 1,527.4 s (`reports/provenance/C5_b0a/registered/registered_report.json`).
- **Phase 6 D1:** `wall_estimate_s = 1,180.577` = **19.68 min**, `parallel_arms: true`, cap 1,200 s; per-arm elapsed F 873.7 s, L 897.4 s, P 612.4 s, PA 733.0 s, sequential sum **3,116.5 s = 51.94 min** (`reports/provenance/C5_b0a/d1/d1_report.json`).
- **D0:** 4 configs, 0 updates, no elapsed field in `d0_report.json`; the ≤15 min cap is plausible for build + memory probe but is not measured at this HEAD.

### Assessment of the v0.2 numbers

- **Stage R 900 updates / ≤120 min is realistic** at roughly 75–82 min expected: Phase 6 did 1,200 updates and 1,680 M records in 82.3 min; F0 drops to 900 updates and 1,440 M records, while phase7 (7,200) and generation (240) are unchanged. The remaining work is dominated by evaluation, so the saving over Phase 6 is modest. 120 min gives ~32–46% headroom — **only if the 12 units run as three 4-cell waves**, as Phase 6 did.
- **Stage D1 25 min is realistic only with 4 parallel cells.** The recorded 19.68 min is a parallel wall time; sequential per-arm elapsed totals 51.94 min, which would exceed 25 min by 2×. `§4` line 84 does not state the execution mode.
- **D0 15 min** is fine if D0 is the same build + probe path; no measured elapsed is recorded, so this remains an assumption.
- **Replay is not in the cap.** `§10` requires `f0_replay.json`, but `§9`’s 120 min is a Stage R training/eval envelope. Phase 6’s registered wall likewise excludes the separate replay driver. F0 must either add a replay budget or state explicitly that replay is outside the 120 min.
- **No-retry conflicts with D1’s purpose.** `§9` line 153 says no retry, but the recorded Phase 6 D1 has `attempt_1` failed and `attempt_2` complete. F0 needs a differentiated policy (see Q1).
- **Code status:** `runner/c5_pm_phase6.py` still has `ARMS = ("F","L","P","PA")` (line 59) and `arm_spec` supports only F/L/P/PA (lines 125–139); there is no `runner/c5_pm_f0.py`. So `§8` lines 140–142 are accurate: F0 arms are not implemented. Note however that `main()` now accepts `--mode registered` and `run_registered_unit` exists (lines 890, 905–930), so the earlier “main rejects registered” provenance claim is stale at this HEAD; the F0 gap is specifically the arm set, not the registered driver.

### 다음 단계

1. State execution mode explicitly: D1 = 4 cell processes in parallel on 6 threads; Stage R = 3 waves of 4 cells. Measure D1 wall before R and abort R if D1 exceeds 25 min.
2. Budget replay separately (or add it to the cap) and state whether `f0_replay.json` is inside 120 min.
3. Adopt the differentiated retry rule from Q1; record failed attempts and never silently replace a Stage R unit.

---

## Q6. H3 separation

**판정: agree**

### Why separation is correct

- H3 (`E01-LN`, `E01-P`, `E01-R`) decomposes the adapter’s internals. Putting it in the primary would add at least three arms × 3 seeds, change the question from “adapter presence” to “which adapter component”, and multiply compute. `§7` lines 127–136 correctly keeps it out and requires its own prereg.
- The primary cells cannot separate LayerNorm, the learned linear map, and the residual path; a separate H3 is the right decomposition.

### What H3’s prereg must fix before it can run

1. **Trainable-parameter parity.** `E01-LN` and `E01-P` have no trainable parameters of their own; if they are evaluated with a frozen decoder they are not comparable to E01 (which trains 64 LoRA modules for 100 updates). H3 must attach the same LoRA modules and train them, or explicitly register an eval-only comparison against E00 rather than E01.
2. **Residual is not identity-preserving at init.** `x + Adapter(x)` with the current random-init adapter (`Linear → GELU → Linear → LayerNorm`) changes the function at step 0; it is not an identity residual. H3 must zero-init the second linear or start with `α = 0`, and assert `x + Adapter(x) == x` at initialization.
3. **Projection must be specified.** Define the fixed orthogonal projection distribution (e.g., QR of a Gaussian), its shape (512×512), whether it preserves norm, and whether it is shared across seeds. Otherwise the arm is not reproducible.
4. **Same endpoints and power caveat.** H3 needs 3 seeds and the same 15-doc caveat from Q4; a negative H3 cannot certify “normalization is not the cause” from a wide CI.

### 다음 단계

1. Approve H3 only as a separate prereg; no H3 execution under F0.
2. Require LoRA parity for LN/projection arms and a zero-init/α=0 residual identity assertion.
3. Predefine the projection distribution and seed schedule; reuse the 15-doc inconclusive rule.

---

## Final decision block

```text
최종 판정: NARROW

Stage D/R:
- v0.2 removes the explicit 1-seed gate and always runs 3 seeds; direction is correct.
- Not yet approval-ready: "mechanics pass" is undefined, D1 telemetry is not firewalled, Stage R has no interim-look ban, and retry policy conflicts with D1's purpose.
- D1 is necessary (Phase 6 attempt_1 failed at backward: "inference tensor used in training backward for P/PA"); D0 alone cannot catch training-path faults.

2×2:
- E01 vs E11 is the right primary at module-set level, but "LoRA fixed" is false at initialization: adapter construction consumes RNG before LoRA (build_arm lines 147-153), so E01/E11 lora_A differ.
- E01 vs E11 also bundles +526,336 adapter params and adapter lr 1e-3 vs lora 1e-4; claim must be "adapter module as configured", not pure mapping.
- E00 has zero trainable parameters; it is a degenerate untrained reference, not a fourth factorial cell. E10 vs E11 is the cleanest secondary.

Interpretation:
- Track STOP removal is correct; route-scoped STOP is the right ceiling.
- Still insufficient: primary decision must use the paired E01−E11 CI, not per-cell significance; add the (-,+) branch; define or delete "≈"; gate STOP on protocol validity; scope "route" exactly.

M/signal:
- M 120/cell and phase7 600/cell arithmetic is correct; M must not gate progression.
- M_PASS must be a per-cell interpretability condition: M fail ⇒ "not evaluable", not negative.
- 15 common docs cannot certify the .05 threshold (Phase 6 L CI width 0.2329 ⇒ SE ≈ .059; ~5.4× docs needed); add an inconclusive band. 2/3 seeds is weak.

Compute:
- Stage R 900 updates / 120 min is realistic at ~75-82 min expected (Phase 6: 1,200 updates, 82.33 min, 4-unit waves).
- D1 25 min is realistic only with 4 parallel cells: measured 19.68 min parallel, 51.94 min sequential.
- Replay and retry are unaccounted; D0 15 min is unmeasured but plausible.

H3:
- Separate prereg is correct. H3 must fix trainable-parameter parity, zero-init residual identity, projection specification, and reuse the 15-doc caveat.

Must-fix (ranked):
1. Fix LoRA initialization parity (per-component RNG or RNG reset) and add D0 init-hash assertions; otherwise "LoRA fixed" is false.
2. Freeze closed D0/D1 mechanical pass criteria; state pass ⇒ R unconditional; forbid reading D1 signal for go/no-go; ban Stage R interim looks.
3. Make the primary decision the paired E01−E11 CI; add (-,+) branch; define equivalence or an inconclusive outcome.
4. Gate route STOP on mechanics + endpoint evaluability + M interpretability; scope STOP to the exact configured route (EG2 layer19 raw, 753, no adapter, 64×r8 LoRA, 100 updates, 20 docs).
5. Specify 4-cell parallel D1 and 3×4 Stage R waves; budget replay separately; differentiate D1 retry from Stage R no-retry.
6. Add the 15-doc inconclusive band and ban "no signal" claims when the CI spans .05; treat 2/3 seeds as weak.
7. Make M_PASS a per-cell interpretability condition; exclude E00 from all signal predicates.
8. Assert identical 15 docs, 5 donors/doc, and K_d across E00/E01/E10/E11; hash them.
9. In the separate H3 prereg, require LoRA parity and zero-init/α=0 residual identity.

잘못된 전제:
- "LoRA fixed" is false at initialization: adapter construction advances the RNG before LoRA attachment.
- "Stage D mechanics-only removes selection bias" is true only if pass criteria are objective and D1 telemetry is firewalled; as written, a discretionary gate remains.
- "E00 is a 2×2 cell" is false: it has zero trainable parameters and is an untrained reference.
- "E01 is a neutral adapter-free baseline" is false: it feeds unnormalized raw EG2 into mT5 cross-attention and may be off-manifold.
- "900 updates / 120 min" holds only with 4-way parallelism; sequential D1 already measures 51.94 min.
- "F0 negative ⇒ route STOP" is invalid without protocol-validity and M conditions; otherwise the correct label is "not evaluable".
- "E01 vs E11 isolates the adapter mapping" is false: it bundles 526,336 parameters, the 10× adapter LR, and a LoRA-initialization difference.
- "D1 1-update proves training mechanics" overstates it: it catches backward/gradient/optimizer/checkpoint faults (Phase 6 attempt_1 did), not multi-step stability.
```

---

## Verification notes

- Reviewed file content at HEAD `185d2ff7b2c29aaa10093838335cb15901981657`; `origin/main` is the same commit.
- Numbers re-read from: `reports/provenance/C5_b0a/registered/registered_report.json`, `reports/provenance/C5_b0a/d1/d1_report.json`, `reports/provenance/C5_b0a/d0/d0_report.json`, `reports/provenance/C5_b0a/m_cohort_preflight.json`, `reports/C5_B0A_PM_PHASE6_CAUSE_2026-11-09.md`, `docs/plan_c5_b0a_pm_prereg_v1_0_11.md`.
- Code read at this HEAD: `runner/c5_pm_phase6.py` lines 57–59, 125–153, 778–930; `runner/c5_mt5_layer_probe.py` lines 52–63; `runner/c5_a1_lora.py` lines 45–64; `runner/c5_mt5_lora_b0.py` lines 52–75.
- No training/evaluation, no test 163, no P1, no subagents. Only this report was written.