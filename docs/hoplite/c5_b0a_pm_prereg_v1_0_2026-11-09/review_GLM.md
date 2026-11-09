# C5 Phase 6 P/M Prereg v1.0 — External Review (GLM 5.3 Flash, max)

- Reviewer: **GLM 5.3 Flash (reasoning: max)**, independent external reviewer for `mandutt/unigem`, Hoplite project `proj_2e8de5ed594f47c7b851f1d7c5b52c61`.
- Round: NEW, intentionally separate v1.0 review round. This is the first review of the consolidated v1.0 spec and is not a duplicate of the r3.4 round; no other model's (and no earlier round's) answer was reused as input to the verdicts below. All judgments derive from this round's own full reading of the v1.0 text and the listed artifacts, and from this round's own recomputations. Where conclusions coincide with earlier rounds (e.g., the NARROW chain), that is convergence, not inheritance.
- Review date: 2026-11-09.
- Reviewed HEAD (after sync): **`78fa7b455c8963e246eb6a3d9206491843e5e3d1`** ("docs: add C5 P/M v1.0 review request"), on `main`.
- Status: **consultation only.** No execution approval. Phase 6 / B0-B / B1 / B2 / Stage C are NOT approved by this round. test 163 sealed and untouched. P1 unused. T5Gemma2 remains D-108 STOP. This round's only repository write is this report file.

---

## 0. Provenance, sync record, and independent verifications

### 0.1 Sync and HEAD

1. `git fetch origin` then `git pull --ff-only origin main`: succeeded ("Already up to date"). Resulting HEAD after sync: **`78fa7b455c8963e246eb6a3d9206491843e5e3d1`**.
2. The request pins base `631e180`. The workspace clone was shallow (depth 1), so `631e180` was initially unavailable; after `git fetch --deepen=10` the lineage resolved: `c6011ad` (r3.4 split) → `63876ce` (v1.0 spec added) → `631e180` (consolidation record) → `78fa7b4` (this review request). `git merge-base --is-ancestor 631e180 HEAD` → **yes**.
3. `git diff --stat 631e180..78fa7b4` touches only the v1.0 review-request directory (dispatch.sh, three prompt files, watch_reviews.py, the request md; 6 files, +627). `git diff --quiet 63876ce HEAD -- docs/plan_c5_b0a_pm_prereg_v1_0.md` → byte-identical; same for `golden_vectors.json`. Review basis = current origin/main HEAD `78fa7b4`.
4. Mid-review, `git fetch --deepen=10` revealed origin/main had advanced to `ec97f8a`. Noted, not merged; per the diff above no reviewed artifact changes. Review basis remains `78fa7b4`.
5. Working tree clean after sync; no AGENTS.md / CLAUDE.md found in the inspected tree.

### 0.2 Independent verifications performed this round

All primary sources read in full: v1.0 plan (1,220 lines — matches the request's claim), `golden_vectors.json`, the r3.4 synthesis, `m_cohort_preflight.json`, the P0 report, `runner/c5_mt5_lora_b0.py` (802 lines), `eval/tests/test_c5_b0_metric.py` (128 lines).

| Check | Result |
|---|---|
| SHA-256 of `reports/provenance/C5_b0a/m_cohort_preflight.json` (recomputed) | `3ee3f1ca…9837af` — **exact match** to v1.0 §0.4 and the request (content hash, not blob OID, as specified) |
| **Golden `state_full` recomputed from the §12.1 frame spec** (two independent methods: Python `struct`/`json` re-derivation, and raw-byte `printf` → `sha256sum`) | `43ecb58e…d65712` — **exact match**, both methods |
| **Golden `state_empty`** | `e3b0c442…b855` — exact match (SHA-256 of the empty byte string) |
| **Golden `replay_three` recomputed** (canonical JSON `sort_keys=true,separators=(',',':')`; donor_sort −1 for null; file order verified equal to the §12.2 key-sort order, so both orderings hash identically) | `c43ea35c…f7851667` — **exact match**, both methods. The three digests are now reviewer-verified constants, not merely author assertions |
| Endpoint arithmetic | 15 × 3 × 4 × 2 × 2 × 2 = **1,440** ✓; 96 per target ✓; D1 phase 5 = 15×2×2×2 = **120**/arm-seed = 1,440/12 exactly ✓; phase 7 = 15×5×2×2×2 = **600**/arm-seed ✓ |
| Cap arithmetic | registered 12 units × 100 = **1,200** ✓; prospective 1,200 + 4 (D1) = **1,204** ✓; 120 + 15 + 20 = **155 min** ✓; T_proj finite/nonnegative/≤96 min (§11.5) ✓ |
| Preflight cohort cross-check vs §1.2 | contributors 16 (≥10 builder floor) ✓; 15 L-eligible; the 5 excluded val docs all have h_len < 753 (751, 750, 718, 708, 728) ✓; boundary docs `01331`=753 (inclusive, eligible) and `01058`=754 both in `common_ids` ✓; native 20/20 at 512 ✓; zero-margin K=754 → 14 ✓; `common_ok`=true |
| P0 numbers | match the P0 report exactly: train +3.7617 [1.8917, 5.6050], Δfull +3.5027, 14/20; val +5.2375 [2.5013, 8.0753], Δfull +5.2936, 18/20; median 2.9739. v1.0 §10.4 labels signed `.4862` vs absolute `.43355` (val20) / `.455` (15 common) correctly — r3.4 MF-9 closed |
| OOD caveat grounding | ln(250,100) ≈ **12.4296** < real copy CE 12.7022 (train) / 13.2352 (val) ✓ |
| Runner cross-check (`runner/c5_mt5_lora_b0.py`) | legacy `bootstrap_paired` (default `seed=20261108`, `seeds_positive = int((arr>0).sum())` — a document count mislabeled as seeds) is present, so v1.0 §10.2's reuse prohibition targets a real defect ✓; LoRA 64 modules r8 α16 dropout .05 ✓; Adapter 512×512 ✓; AdamW wd .01, clip 1.0, order `train_ids[step % len]` ✓; adapter_lr 1e-3 / lora_lr 1e-4 ✓; base decoder eval via `set_training_mode` ✓; `test_split_used: False` throughout ✓ |
| `runner/c5_pm_stats.py` | **absent** ✓ — consistent with no-code-before-freeze (§16.1) |
| `eval/tests/test_c5_b0_metric.py` | 7 B0 metric tests (same-position CE alignment, unshifted copy mask, copy_ce ≥5-token floor, generation telemetry, symmetric training mode, length-matched donors, descriptive P0 decision); no P/M decision-function tests exist yet — consistent with code-after-freeze |
| Stale-reference scan (grep) | `r3.x` / `v0.2.x` / ERRATA appear **only** in the supersession header (§ preamble), the historical-only §15 traceability appendix, and freeze/ERRATA statements — no normative section depends on an earlier P/M document |
| Banned-term scan | `delta_memfree`, `ADAPTER_REGIME_LOSS`, `n_signal 0..20`, `M_CONTROL_NOT_VALID` appear only inside prohibition lists ("no …", "금지") ✓ |

### 0.3 Constraints honored

No training or evaluation was run. Test 163 untouched (sealed). No P1 data, no external APIs. No subagents, no additional LLM calls. Repository unmodified except this single report file, written at the requester's direction.

---

## 1. Q1–Q13

### Q1. Self-containedness

- **판정: conditional.**
- 근거: Structurally, v1.0 is the first spec in this chain whose normative sections (§0–§14) reference no earlier P/M document — the grep scan in §0.2 shows `r3.x` only in the supersession header, the historical-only §15 traceability appendix, and prohibition lists. Every r3.4 Must-fix area now has a direct in-document definition: variant×memory_kind (§9.4), signal-tail variant=NA (§10.4), P/PA 20-native cohort (§4.5), replay phase-5/7 domains + debug/final hash separation (§11.4, §12.2), L binding (§3.3), F/L K=753 M-only (§2.3), PA_VALID (§4.5), top3 absolute/signed (§10.4), documents_positive (§10.2), golden digests (§12.3 — all three independently verified this round). That is a real, verifiable closure of the r3.4 blocker set.
  However, four items keep v1.0 from being *totally* self-contained: (i) the four path flags `assay_path_ok`, `p0_path_ok`, `p_step100_path_ok`, `pa_step100_path_ok` route `ASSAY_INVALID`/`NOT_ASSESSABLE` (§4.2–§4.4, lines 275–301) but are defined **nowhere** in the document — the last chain-inherited definitions; (ii) the donor selection rule (count 5, length-matched nearest, exclude self, deterministic tie-break, donor_id ordinal mapping) exists only implicitly in phase arithmetic ("20 docs ×5 donors", "donor_id 0..4") and in runner code (`native_donors_for`), not as contract text; (iii) the signal-axis control memory "shuffled donor" (§3.5, §10.4) is never defined — it is a legacy name, and the document does not say it means *wrong-donor-document memory* (cropped `K=min(len(real), len(donor))`, 5 donors averaged) rather than token shuffling; (iv) the P/PA M-cohort contradiction (Q6/MF-V1-1).
- 다음 단계: (1) define the four path flags normatively in §4; (2) add the donor-selection rule and the signal-control-memory definition to §2/§3; (3) resolve MF-V1-1.

### Q2. Decision contract

- **판정: agree.**
- 근거: §3.1–§3.2 define the tri-state, ANDn (false → NA → true), ORn, NOT3; §3.3 binds `l_copy_signal := L_COPY_SIGNAL` and `l_full_signal := L_FULL_SIGNAL` **directly** and explicitly states `l_signal` is not `ANDn` — closing r3.4 MF-5. The §3.4 9-pair table is complete and re-derived consistently (true/false → l_signal NA with copy_only=true, full_only=false; true/NA → copy_only=NA, full_only=false; false+NA → NOT_ASSESSABLE, not MEAN_CONTRAST_ONLY). The §4 validity chain is total with known-failure-first (§4.2), assay-tier NA (§4.3), and P/PA ordering (§4.4); I checked F3/F7/F8/F9/F10 routings against the branch order and all agree with §4.6. §6.3 dispatch is total with a fallback and every §6.2 label is reachable (verified: L_SIGNAL_M_CONTROL_*, NO_L_SIGNAL_*, COPY_ONLY_WEAK / FULL_ONLY_WEAK, small-N triple, MEAN_CONTRAST_ONLY, NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE); copy_only/full_only correctly precede the l_signal NA case. Fixtures 16–18 use primitive flags, not derived values.
  Two cosmetic gaps: `p_valid := P_VALID`, `pa_valid := PA_VALID`, `m_pass_* := M_PASS_*` bindings are implicit by naming convention (the l_* binding got the explicit §3.3 treatment; p/pa did not), and §7.1's "calibration 3^4" counts only m_valid's four operands while omitting m_pass_l's two.
- 다음 단계: (1) add explicit p_valid/pa_valid/m_pass_* bindings mirroring §3.3; (2) correct §7.1 to calibration 3^6; (3) none blocking.

### Q3. M variant × memory_kind

- **판정: agree.**
- 근거: §9.4 states the full grid: `M_POS_MEAN` control = `M_POS_MEAN` tensor, real = `real_prefix_t`, delta_pos; `M_NORM` control = `M_NORM(t)` (one global mean direction × per-target magnitude scalar, same adapter space, no raw EG2 embedding, no per-target matrix), real = `real_prefix_t`, delta_norm; `memory_kind ∈ {control, real}`; the two variants are distinct controls and `M_PASS_POS`/`M_PASS_NORM` are independent tests using delta_pos/delta_norm respectively (§9.6) — "not the same test twice" is explicit. This closes r3.4 MF-1 exactly as that review specified. Endpoint arithmetic verified: 1,440 records, 96 per target, exact key set required (§9.5). Degenerate-norm guardrails exist: builder_ok requires `‖M_POS_MEAN‖_F > 0` and all 15 `‖real_prefix_t‖_F > 0` (§5.1), with zero/nonfinite-norm tests mandated (§13.2).
  One non-blocking note: `M_NORM(t)` is target-dependent, and the per-target ratio `‖real_prefix_t‖_F / ‖M_POS_MEAN‖_F` is not required as a retained artifact (§10.4 mandates raw top3 artifacts but §9.3 does not mandate ratio retention) — without it, replay records alone cannot re-derive the M_NORM controls.
- 다음 단계: (1) none blocking; (2) require norm-ratio retention per target in §9.3.

### Q4. M builder / M_NORM / endpoint / replay

- **판정: conditional.**
- 근거: Builders are well-specified (§9.2): eval/no_grad, no dropout, per-seed builder with seed-average before bootstrap, `A=identity` for P (P identity explicit), F/L `[:753]`, P/PA `[:512]`, donor-crop prohibited for primary M, `M_GLOBAL` demoted to descriptive-only. `real_prefix_t := A(h_t)[:K_M]` in the same adapter space (§9.3); `M_NORM(t)` defined with the exact scalar formula. Replay closes r3.4 MF-4: phase 5 = primary donor-free 120/arm-seed (`donor_id=null`), phase 7 = donor diagnostic 600/arm-seed (`donor_id 0..4`), declared non-comparable populations; `debug_replay_hash` is D1-synthetic-only and is **never compared to** `final_replay_hash` (§11.4); numeric tolerance values are present (`atol=1e-5`, `rtol=1e-4`, line 955); the record schema (§12.2) fixes the key, `doc_id` (not `id`), float64 finite-reject, ascending sort, canonical JSON, SHA-256 of UTF-8 bytes, and donor_sort −1/0..4.
  Three gaps: (i) the donor selection rule is not contract text (Q1); (ii) the P/PA 20-native M-calibration records have no phase, no count, and no replay domain (Q6/MF-V1-1); (iii) §12.1's state-hash domain covers "adapter parameters + LoRA A/B" and excludes frozen base — it does not include the M tensors (`M_POS_MEAN`, `M_NORM`) nor require them in the manifest, so the hashed checkpoint + replay records do not bind the exact control tensors used.
- 다음 단계: (1) pin the donor rule; (2) add M tensors (or their digests) to the §12.1 hash domain or the manifest; (3) resolve MF-V1-1's replay home.

### Q5. F/L memory length scope

- **판정: agree.**
- 근거: §2.3 states the rule verbatim: "`K_M=753` is **M-only**; training/eval/generation must not require 753", with M memory F/L `[:753]` / P/PA `[:512]` (donor-crop prohibited), training/eval signal donor-crop `K=min(len(real), len(donor))` per document over all 20 docs, and generation on 20 val docs with `max_new_tokens=256`. This closes r3.4 MF-6. Preflight cross-check: exactly 4 train docs (707, 746, 740, 730) and 5 val docs (751, 750, 718, 708, 728) fall below 753 — precisely the population the rule protects; native lengths are 512/512 for all 40, so P/PA are eligible on all 20 val docs. Zero-margin handling is explicit (§1.2, §9.8: K=754 → 14, abort, no 15→14 substitution, report `ZERO_MARGIN_COHORT_FAIL` + missing ID). `full_k_secondary` (11/20) is demoted to historical/descriptive-only and appears in no gate (§9.1, §14, §15) — closing r3.4 MF-8.
  Minor wording issue: §2.3's "training/eval signal … all 20 train/val docs" reads as if the *training* forward used donor-crop, but a training step has no donor; this ambiguity is folded into MF-V1-6.
- 다음 단계: (1) clarify in §2.3 that the training forward consumes real memory and donor-crop applies to eval endpoints; (2) none else.

### Q6. P/PA

- **판정: conditional.**
- 근거: Closed items — `PA_VALID` is defined directly in §4.5 with the full four-conjunct predicate (`delta_copy ≥ .05 AND copy CI lower > 0 AND delta_full > 0 AND full CI lower > 0`) on the 20-native cohort with the same 100-step protocol, with "PA_VALID is defined here, not inherited" stated; this closes r3.4 MF-3's definition half and MF-7. The PA veto rationale is corrected ("PA failure vetoes joint P/PA calibration; it does not prove native memory regime is intrinsically invalid", §5.3/§8.2); `PA_RETENTION` is nullable/descriptive and never a gate (§5.3, §8.2, §14); the geometry caveat (512 vs 753, no direct retention comparison) is present (§8.2); P/PA validity excludes test 163 (§4.5).
  **Blocker (MF-V1-1): cohort contradiction.** §4.5 ("P/PA `m_pass_pos/norm` use 20 native docs"), §5.2 ("P/PA pass uses 20 native docs. M L pass uses 15 common targets"), and §8.3 (`m_pass_pos_p/norm_p`, `m_pass_pos_pa/norm_pa` = 20 native docs) implement r3.4 MF-3's 20-native requirement. But §9.1's cohort table lists P/PA M targets = "15 common", §9.5's endpoint_ok counts all four arms at 15 targets (→ 1,440), and §11.3 phase 4 builds "15 target" / phase 5 computes "15×2×2×2 = 120/arm-seed" with no 20-native phase. `m_valid = ANDn(m_pass_pos_p, m_pass_norm_p, m_pass_pos_pa, m_pass_norm_pa)` is a gate input (it routes `M_CONTROL_INVALID` in §5.4), so its input cohort must be a single pinned value; today the document states two. Additionally, §8.1's "20 native docs" conflates the P/PA **training** cohort (train20 natively tokenized at 512) with the **validity** cohort (val20, per §1.2) — both are "20 native docs" but they are different ID sets.
- 다음 단계: (1) pick one design and reconcile every dependent number — recommended: keep the uniform 15-common grid for cross-arm records *and* add an explicit P/PA 20-native M-calibration computation (20×2×2×2 = 160/arm-seed) with its own phase, count, and replay domain; the alternative (per-arm grid 15/15/20/20) requires restating 1,440 → 1,680, 120 → 560/arm-seed, and endpoint_ok per-arm; (2) split "20 native docs" in §8 into training cohort (train20@512) vs validity cohort (val20@512); (3) recompute phase 4/5/T_proj terms after the choice.

### Q7. Statistics / tail

- **판정: agree.**
- 근거: §10.1 fixes all constants (n_boot 1000, percentile 2.5/97.5, bootstrap_seed 20261109, unit=document, seed_average_before_bootstrap=true, n_min_signal=15). §10.2 mandates a new `runner/c5_pm_stats.py` and prohibits reuse of the legacy helper — cross-checked against the runner: the legacy `bootstrap_paired` really does default to `seed=20261108` and reports `seeds_positive = int((arr>0).sum())` (a document count mislabeled as seeds), so the prohibition targets a live defect, and the P0 report's own "positive documents 14/20, 18/20" language shows why `documents_positive` needed a proper definition (now given, §10.2) — closing r3.4 MF-10's definition half. Missing registered seed → predicate NA, "2-of-available 금지", and "existing 2 seeds only → NA, not 2/2" (§3.5) close r3.4 MF-5's n-condition half. Tail: the hard gate is the **signal tail** with arm=L, endpoint=copy, control=shuffled donor, **variant=NA**, cohort=15, delta = shuffled−real copy (§10.4) — closing r3.4 MF-2; `M_POS_MEAN`/`M_NORM` tails are demoted to descriptive (`tail_driven_M_POS_MEAN/_NORM`); the gate metric is `top3_abs_share` with the signed share descriptive (closing MF-9 — P0's .4862 is correctly labeled signed and .43355 absolute); the tie rule is deterministic (|delta| desc, doc_id asc, exactly 3); n<4 → `leave_top3_mean=NA`; denominator 0 → share NA; the precedence rule (leave_top3 ≤ 0 → true; NA → NA; share > .50 → true; else false) is executable and the `.50` threshold is unchanged; raw top3 IDs/sum/denominator/signed share must be retained; B0-B requires `tail_driven=false` with true/NA blocking (§14).
  Note: the first precedence branch makes `top3_abs_share` irrelevant whenever `leave_top3_mean ≤ 0` — intentional and executable, but it deserves a dedicated fixture.
- 다음 단계: (1) add a fixture for the leave_top3-first branch; (2) none blocking.

### Q8. D0 / D1 / cap

- **판정: agree.**
- 근거: D0 is genuinely mechanics-only: 0 optimizer updates, ≤4 configs, ≤15 min, seed 20261111, `labels_computed:false`, `not_a_result:true`, h-length assert, no timing claim, separate from the registered cap (§11.2). D1 is bounded: 4 arms × 1 debug seed = 4 units, seed 20261111, 1 update/arm, ≤20 min, 8 phases with "all 8 measured; missing phase → no projection" and "step0 before update or restored state" (§11.3). Arithmetic verified: phase 5 = 120/arm-seed (= 1,440/12 exactly), phase 7 = 600/arm-seed; `T_proj = 3 × Σ_arm(100·t_train + 7 phase terms)`, finite/nonnegative/≤96 min, with "D1 없이 3-seed 금지", "D0 projection 금지", "no timing probe substitute", and a 120-min hard abort (§11.5); cap §11.6 gives "prospective max 1,204 updates / 155 min (**not grant**)" with no retry/extension — all consistent (1,200+4=1,204; 120+15+20=155). Approval boundaries are respected: D0/D1/3-seed are separate approvals and B0-B is not automatic (§14, §16.3).
  Caveat: phase 4/5 and the T_proj terms inherit the 15-target uniform grid, so they must be restated after MF-V1-1 is resolved.
- 다음 단계: (1) recompute phase 4/5/T_proj after MF-V1-1; (2) none else.

### Q9. Hash / golden

- **판정: agree.**
- 근거: §12.1 specifies the state frame completely (sorted state_dict keys; adapter + LoRA A/B only; frozen base excluded; exact byte layout `u32le name_len | name | u8 dtype_len | dtype | u8 ndim | u32le shape | u64le nbytes | LE contiguous bytes`; no padding; empty state → SHA-256 of empty bytes; frozen base/config/mode in manifest; `final_checkpoint_hash` postrun). §12.2 makes replay canonicalization total (key with donor_sort, `doc_id` not `id`, enum domains, float64 finite-reject, ascending sort, canonical JSON `sort_keys=true,separators=(',',':')`, SHA-256 of UTF-8 bytes; debug vs final hash separation; numeric tolerance `atol=1e-5, rtol=1e-4` in §11.4 vs exact hash for artifact integrity). §12.3's three digests were **independently recomputed by this reviewer via two independent methods** (Python struct/json re-derivation and raw-byte printf→sha256sum): state_full `43ecb58e…d65712` ✓, state_empty `e3b0c442…b855` ✓, replay_three `c43ea35c…f7851667` ✓ — with file order verified equal to the canonical key order, so both orderings hash identically. The digests are therefore usable as implementation gates exactly as §13.4 intends, and the "do not regenerate from the implementation under test" note in `golden_vectors.json` is honored by this procedure. The preflight content hash also re-verified exactly (§0.2).
  Two hardening notes (non-blocking): the replay vector exercises only donor_id=null / arm L / M_POS_MEAN — a supplemental vector with donor_id 0..4, a P/PA arm, and an M_NORM record would exercise the sort/enum paths; and M tensors remain outside the §12.1 hash domain (Q4).
- 다음 단계: (1) optional supplemental replay golden vector; (2) add M-tensor manifest digests; (3) none blocking.

### Q10. Remaining Must-fix

- **판정: conditional** — r3.4's MF-1…MF-10 are genuinely closed at text level (each closure verified above against specific sections, with the golden digests and preflight hash now reviewer-verified), but consolidation introduced one new contradiction and left a small set of definitional holes.

Ranked list:

1. **MF-V1-1 (blocker).** P/PA M-cohort contradiction: §4.5/§5.2/§8.3 say the P/PA M pass uses **20 native docs**; §9.1/§9.5/§11.3 (phase 4/5, 1,440) put P/PA at **15 common**. `m_valid` is a gate input; its cohort must be unique, and the chosen record set needs a count, a D1 phase, and a replay domain.
2. **MF-V1-2 (high).** The donor selection rule (5 donors, length-matched nearest, exclude self, deterministic tie-break, donor_id ordinal → `donor_sort 0..4` mapping) is only implied by phase arithmetic and runner code; pin it as contract text.
3. **MF-V1-3 (high).** Define the signal-axis control memory: "shuffled donor" = memory computed from a different (length-matched) donor document, cropped `K=min(len(real), len(donor))`, averaged over the 5 donors; state that "shuffled" is a legacy name for wrong-donor memory, not token shuffling.
4. **MF-V1-4 (medium).** Define the four path flags `assay_path_ok` / `p0_path_ok` / `p_step100_path_ok` / `pa_step100_path_ok` in-document (they gate `ASSAY_INVALID`); this is the last chain-inherited definition.
5. **MF-V1-5 (medium).** Bind the M tensors: add `M_POS_MEAN`/`M_NORM` (and per-target norm ratios) to the §12.1 hash domain or the manifest so checkpoint+replay can re-derive the exact controls used.
6. **MF-V1-6 (low).** §2.3 wording: state that the training forward consumes real memory (no donor) and donor-crop applies to eval endpoints; split §8's "20 native docs" into training cohort (train20@512) vs validity cohort (val20@512).
7. **MF-V1-7 (low).** Add explicit bindings `p_valid := P_VALID`, `pa_valid := PA_VALID`, `m_pass_* := M_PASS_*` (mirror §3.3).
8. **MF-V1-8 (low).** §7.1 axis bookkeeping (calibration is 3^6 including m_pass_l's two operands); optionally add the supplemental replay golden vector (donor 0..4 / P or PA / M_NORM).

New-problem check: no r3.4 blocker regressed; the superseded statements (n_signal 0..20, `PA only`, `delta_memfree`, 753 training requirement, debug/final direct comparison) all remain prohibited (§13.5, §15). The one genuinely new problem is MF-V1-1.

### Q11. Freeze / implementation approval

- **판정: conditional.**
- 근거: Freeze now is not possible because MF-V1-1 changes gate arithmetic (1,440 vs 1,680; phase 4/5 counts; endpoint_ok key sets) — exactly the class of decision §16.1 reserves for pre-freeze must-fix. MF-V1-2/3/4 are pure definitional closures with no new scientific choices, so they fit the NARROW rule ("must-fix only"). After they are folded in (v1.0 + numbered ERRATA or a v1.0.1), frozen with commit hash + content SHA-256 (§16.2), implementation + unit tests + D0 zero-update mechanics debug are approvable. Mandatory pre-implementation tests (from §13, plus this round's findings): golden-vector tests asserting the three verified digests (`43ecb58e…`, `e3b0c442…`, `c43ea35c…`) with permutation/duplicate/missing-key cases; exact-key-set test at the post-fix record count with 96-per-target; §3.4 9-pair table; F1–F11; fixtures 16–18; ANDn 2/4/5; tail tie-rule and the leave_top3-first precedence branch; missing-seed → NA (2 seeds → NA, not 2/2); `documents_positive`; zero-margin abort; state-frame golden; canonical JSON; a stats-module test proving no legacy `bootstrap_paired` reuse (bootstrap seed 20261109; `seeds_positive` counting seed means, not documents); builder_ok norm guards; P identity (`A=identity`); `M_NORM` same-adapter-space; donor-crop prohibition for primary M.
- 다음 단계: (1) fold MF-V1-1…4 → freeze (hash + SHA-256); (2) implement against the freeze hash with the §13 matrix as DoD; (3) then D0.

### Q12. B0-B / D1 / 3-seed boundaries

- **판정: agree** (boundaries are adequate; restated below with v1.0 labels).

B0-B predicate, restated in v1.0 terms (§14):

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS
AND signal_status == EXPLORATORY_L_SIGNAL
AND m_valid == true
AND n_signal >= 15            # max is 15 → exactly 15; MARGINAL_SIGNAL_COHORT=true
AND tail_driven == false      # signal tail only (variant NA); true or NA blocks
AND leakage/mode/metric pass  # test_split_used false; no P1; no test 163; mode-policy asserts pass
AND artifact complete         # manifest + final_checkpoint_hash + final_replay_hash + preflight hash intact
AND separate B0-B prereg/approval
```

- 근거: `EXPLORATORY_L_SIGNAL` alone is not approval; `full_k_secondary`, P0, and `PA_RETENTION` are explicitly not evidence (§14); there is no B1/B2/Stage C auto-advance; D1 and 3-seed remain separately approved runs (D1 after D0; 3-seed only after D1 with T_proj ≤96 and no timing-probe substitute, §11.5). No predicate needs weakening or strengthening; `n_signal ≥ 15` with max 15 correctly means exactly 15, and the val20 count is descriptive-only (§6.1).
- 다음 단계: (1) keep B0-B as a separate prereg; (2) none else.

### Q13. Final verdict and v1.0 freeze

See the final block below. Summary: **NARROW**. Not STOP — the spec is structurally sound, every r3.4 blocker has a real in-document closure, the golden digests and preflight hash verify exactly, and the remaining items are definitional/textual. Not CONTINUE — MF-V1-1 is a gate-arithmetic contradiction that cannot stand in a frozen implementation contract, and MF-V1-2/3/4 are the residual chain dependencies that §0.1's own "구현자는 이 문서만 읽고" promise requires closing.

---

## 2. Final verdict block

```text
최종 판정: NARROW

v1.0 freeze:        보류 — MF-V1-1…4를 반영(v1.0 + 번호 ERRATA 또는 v1.0.1)한 뒤
                    freeze commit hash + content SHA-256으로 동결.
구현+unit tests:    동결 후 승인 가능. §13 matrix + 금문 digests 3종(43ecb58e…/e3b0c442…/c43ea35c…,
                    본 라운드 독립 재계산 일치) 게이트 + exact-key-set/96회 + 9-pair + F1–F11 +
                    fixtures 16–18 + tail tie/precedence + missing-seed NA + legacy-bootstrap 금지 테스트.
D0:                 동결 + unit tests 통과 후 승인 가능 (0 updates, ≤4 configs, ≤15 min,
                    seed 20261111, labels_computed:false, not_a_result:true, h-length assert).
D1:                 본 라운드 미승인 (별도 승인; D0 후, 8 phases 전부 측정, T_proj 전제).
3-seed:             미승인 (D1 완료 + T_proj ≤96 min + 120-min hard abort 후 별도 승인).
금지 범위:          Phase 6 학습/평가 실행, B0-B/B1/B2/Stage C 자동 진행, test 163 (sealed),
                    P1 사용, T5Gemma2 (D-108 STOP), 결과 후 threshold/seed/donor/step/LR 변경.
최대 compute:       D0 ≤15 min; D1 ≤20 min (4 units, 1 update/arm);
                    registered(별도 승인 후) 12 units / 1,200 updates / 120-min hard abort /
                    threads 6 / GPU none / retry none; prospective 1,204 updates / 155 min (not grant);
                    T_proj ≤96 min.
Must-fix (ranked):  MF-V1-1 (blocker) P/PA M cohort 이중 진술(20 native vs 15 common/1,440) 단일화;
                    MF-V1-2 (high) donor 선택 규칙의 계약문화;
                    MF-V1-3 (high) signal control memory("shuffled donor") 정의;
                    MF-V1-4 (med) 4개 path_ok 플래그 정의;
                    MF-V1-5 (med) M tensor의 hash/manifest 바인딩;
                    MF-V1-6 (low) training-forward/학습·검증 코호트 문구;
                    MF-V1-7 (low) p_valid/pa_valid/m_pass_* 명시 바인딩;
                    MF-V1-8 (low) §7.1 축 정리 + 보조 replay golden vector.
v1.0 self-contained: 조건부 충족 — r3.x 의존은 traceability/prohibition으로 격리 완료;
                    path flags·donor rule·control memory 정의가 문서 내에 들어오는 순간 완전.
잘못된 전제:        "P/PA M cohort"가 §4.5/§5.2/§8.3(20 native)과 §9.1/§9.5/§11.3(15 common,
                    1,440)으로 이중 진술되어 있다 — m_valid의 입력 코호트는 단일 값이어야 하며,
                    이것이 freeze 불가의 유일한 blocker다.
```

---

## 3. Scope discipline of this round

- No training/evaluation executed; no test 163 access; no P1 data; no external APIs; no subagents or additional LLM calls; no repository modification other than this file.
- No threshold/seed/donor/step/LR changes are proposed anywhere above; all MF items are definitional or arithmetic reconciliations of statements already in v1.0.
- Phase 6 / B0-B / B1 / B2 / Stage C remain unapproved by this round; T5Gemma2 remains D-108 STOP; test 163 remains sealed.