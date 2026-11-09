# C5 Phase 6 v0.2.1-r3.4 — External Review (GLM)

- Reviewer: **GLM 5.3 Flash (reasoning: max)**, independent external reviewer for `mandutt/unigem`, Hoplite project `proj_2e8de5ed594f47c7b851f1d7c5b52c61`.
- Round: NEW, intentionally separate r3.4 review round using a different model from the r3.3 round. No other model's answer was reused; all judgments below are from this round's own reading and verification.
- Review date: 2026-11-09.
- Reviewed HEAD: **`05de3ae1b0a4b3bc3df5170efdfe037b45038b9b`** ("docs: add C5 P/M v0.2.1-r3.4 review request"), on `main`.
- Status: **r3.4 review only. No execution approval.** Phase 6 / B0-B / B1 / B2 / Stage C are NOT approved by this round.

---

## 0. Provenance, sync record, and scope of this review

### 0.1 Sync and HEAD

1. `git fetch origin` then `git pull --ff-only origin main`: succeeded ("Already up to date") on branch `hoplite/thasos-a840aaff`, which was already at **`05de3ae1`**. Resulting HEAD after pull: `05de3ae1b0a4b3bc3df5170efdfe037b45038b9b`.
2. Lineage verified after `git fetch --deepen=30`: `148d5c1` (r3.3) → `2ed41f0` (r3.3 request) → `3500bc3` (r3.3 threads) → `362c52c` (r3.3 split) → **`30b966d`** (r3.4 executable contract closure — the basis the request pins) → `05de3ae1` (r3.4 review request). `git diff --stat 30b966d..05de3ae1` touches only the r3.4 review-request directory (dispatch.sh, three prompt files, watch_reviews.py, the request md; +717 lines); **the r3.4 plan file is byte-identical to its `30b966d` basis** (verified with `git diff --quiet`). Review basis = current origin/main HEAD `05de3ae1`.
3. During the review, origin/main advanced to `c158c7f` ("docs: record C5 P/M v0.2.1-r3.4 review thread ids", +20 lines, `threads.json` only). This was noted and **not** merged mid-review; no reviewed artifact changes. Review basis remains `05de3ae1`.
4. Working tree clean after sync; no AGENTS.md / CLAUDE.md found in the inspected tree.

### 0.2 Independent verifications performed this round

Unlike the r3.3 GLM round (which was explicitly spec-level and did not re-read the primary text), **this round read the full primary text** of r3.4 (all §0–§17), r3.3 (all §0–§17), the r3.3 synthesis, the preflight JSON, the P0 report, the runner, and the metric tests. Verifications:

| Check | Result |
|---|---|
| SHA-256 of `reports/provenance/C5_b0a/m_cohort_preflight.json` (recomputed) | `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` — **exact match** to the hash pinned in r3.4 §1.1 and the request |
| r3.4 plan line count | 1,109 — matches the request's claim |
| **§2.4 9-pair table re-derived by hand from §2.2 ANDn/NOT3 + §2.3** | all 9 rows consistent, including `copy_only`/`full_only` (e.g., true/false → copy_only=ANDn(true, NOT3(false))=true; true/NA → copy_only=NA, full_only=ANDn(NA, NOT3(true))=false; false/NA → copy_only=false (false-dominant), full_only=NA). **No contradiction remains.** |
| Endpoint identity arithmetic | 15 × 3 × 4 × 2 × 2 × 2 = **1,440** ✓; D1 phase 5 = 15×2×2×2 = **120**/arm-seed (= 1,440/12 exactly) ✓; phase 7 = 15×5×2×2×2 = **600**/arm-seed ✓ |
| Cap arithmetic | 12 units × 100 = **1,200** ✓; 1,200 + 4 (D1) = **1,204** ✓; 120 + 15 + 20 = **155 min** ✓; T_proj ≤ **96 min** retained |
| Preflight cohort numbers | `l_contributors_at_k`=16 (≥10 builder floor) ✓; `l_target_eligible_at_k`=15; 5 excluded val docs all have h_len < 753 (751, 750, 718, 708, 728) ✓; boundary docs `01331`=753 (inclusive) and `01058`=754 sit exactly at the margin; `common_ids` length 15; `full_k_secondary` 11/20 ✓; native 20/20 at 512 ✓; `common_ok`=true |
| P0 numbers vs `p0_native_sanity.json` (recomputed from per-doc deltas) | train mean +3.7617 (CI [1.8917, 5.6050]), Δfull +3.5027, 14/20 ✓; val mean +5.2375 (CI [2.5013, 8.0753]), Δfull +5.2936, 18/20 ✓; val median 2.9739 ✓; real copy CE 12.7022/13.2352 ✓ |
| **Val top-3 share discrepancy (new finding)** | Request §4 states "val … top-3 share **.4862**". Recomputation from the P0 artifact gives **absolute share = 0.4335** (sum of top-3 \|Δ\| / sum of all \|Δ\|) and **signed share = 0.4862** (sum of top-3 signed Δ / sum of all signed Δ). The quoted .4862 is the **signed** share, i.e., exactly the descriptive-only quantity that r3.4 §9.4 excludes from the gate. Descriptive-only for P0, so no gate impact — but the request's own caveat mislabels the quantity. |
| OOD caveat grounding | ln(250,100) = **12.4296** < real copy CE 12.7022 (train) / 13.2352 (val) ✓ — r3.4 §12's phase-5 OOD caveat is numerically grounded |
| Runner cross-check (`runner/c5_mt5_lora_b0.py`, 802 lines) | legacy `bootstrap_paired(seed=20261108)` with `seeds_positive = int((arr > 0).sum())` (a document count mislabeled as seeds) is present — r3.4 §9.3's prohibition targets a real defect ✓; train order `train_ids[step % len(train_ids)]` matches §7.3 ✓; adapter_lr 1e-3 / lora_lr 1e-4 / AdamW / wd .01 / clip 1.0 / base-decoder eval / LoRA 64 modules r8 α16 dropout .05 all match §7.3 ✓; donor-crop (`k = min(len_real, len_donor)`) evaluation is B0-style and is what the Phase 6 signal-axis phases 2/3/7 reuse |
| `runner/c5_pm_stats.py` | **absent** ✓ — correct; code may only be written after freeze |
| `eval/tests/test_c5_b0_metric.py` (128 lines) | 7 B0 metric tests (same-position CE alignment, unshifted copy mask, copy_ce ≥5-token floor, generation telemetry, symmetric training mode, length-matched donors, descriptive P0 decision). No PM decision-function tests exist yet — consistent with code-after-freeze |
| Golden vector frame example (r3.4 §10.6) | hand-verified: `<f4` is 3 chars; 1.0f32 LE bytes = `0000803f` ✓; −2.0f32 LE bytes = `000000c0` ✓ — the worked example is genuinely hand-derivable |
| Chain-inherited definitions | `PA_VALID` ("PA_VALID same.", errata §2.4; "P_VALID와 같은 threshold", r1), `M_GLOBAL` ("모든 eligible position의 global mean vector repeat", errata §3.2), `assay_path_ok`/`p0_path_ok`/`p_step100_path_ok` (errata §2.1), step0/step100 movement fields (errata §2.3), aggregation and L predicates (errata §4.2–4.3) — **defined only in earlier chain documents**, not restated in r3.4 |

### 0.3 Constraints honored

No training or evaluation was run. Test 163 untouched (sealed). No P1 data, no external APIs. No subagents or additional LLM calls. Repository unmodified except this single report file, written at the requester's direction.

---

## 1. R3.3 blocker closure audit (primary-text level)

r3.3 froze on 18 blockers (request §2; synthesis MF-1…MF-13). This round checked each against the r3.4 primary text:

| # | r3.3 blocker | r3.4 closure | This round's check | Status |
|---|---|---|---|---|
| 1 | §2.4 mixed true/false → false | §2.4 both mixed rows → NA | 9 rows re-derived from §2.2/§2.3 — consistent | **closed** |
| 2 | F M builder missing | §7.4 + §8.2 arm matrix with F (753, adapter, trained) | F recipe present; §8.4 includes F | **closed** |
| 3 | P `A(h_i)` with no adapter | §8.2 `A = identity` for P | explicit | **closed** |
| 4 | `h_i >= K_M` type | `h_len_i` scalar | explicit | **closed** |
| 5 | `real_prefix_t` space | §8.3 `A(h_t)[:K_M]`, same-arm; mixing forbidden | explicit; §8.3 extends it to M primary reference and real CE | **closed** |
| 6 | `n_signal` 15/20 mismatch | §5.1 `{NA, 0..15}`, cohort = 15 L-eligible | fixtures 16–18 use n_signal=15; §6.1 updated | **closed** |
| 7 | `tail_driven` input undefined | §9.4 arm=L, endpoint=copy, cohort=15, delta=control−real | **partially closed — control `variant` (M_POS_MEAN vs M_NORM) still not pinned** (MF-5's own requirement listed it) | **gap (MF-A)** |
| 8 | `top3_share` gate on signed quantity | §9.4 gate on `\|delta\|`; signed descriptive | explicit | **closed** |
| 9 | tail NA precedence | §9.4 ordered branches | ordered and total | **closed** |
| 10 | `adapter_lr (PA only)` | §7.3 all adapter-bearing arms | explicit + DoD | **closed** |
| 11 | T_proj real/control factor | §10.4 120/600 with memory-kind factor | arithmetic verified | **closed** |
| 12 | endpoint count variants/copy-full missing | §8.4 1,440 explicit | arithmetic verified | **closed** |
| 13 | PA veto rationale absent | §4.2 rationale | stated as intended arm-level calibration veto; PA_RETENTION stays non-gate | **closed** |
| 14 | golden vector self-generated | §10.6 independent one-off script + hand-derivable frame + empty-state hash + replay golden | example bytes verified | **closed** |
| 15 | named-cell prerequisites | §6.3 fixtures 16–18 only; forbidden cell stated | consistent with §4.3 ordering | **closed** |
| 16 | ANDn/NOT3 domain | §2.2 scalar predicates only; no axis mixing | explicit | **closed** |
| 17 | zero-margin failure path | §8.7 abort path | explicit (754→14; <15 targets or <10 contributors → M_NOT_EVALUABLE) | **closed** |
| 18 | P0 OOD caveat | §12 | explicit + numerically grounded | **closed** |

**Result: 17 of 18 fully closed in primary text; item 7 is partially closed (the variant sub-item of MF-5 remains).** Two additional residual gaps not on the r3.3 blocker list were found this round (MF-B donor-level replay semantics; MF-C delta-family naming), plus a restatement gap inherited from the errata chain (MF-D).

---

## 2. Answers to Q1–Q13

### Q1. Total factored contract

```text
Q1.
- 판정: conditional
- 근거: The §2–§6 decision machinery is total and internally consistent as far as I could
  re-derive it: tri-state primitives (§2.1), scalar-only ANDn/ORn/NOT3 with 2/4/5 arity
  tests and no axis mixing (§2.2), single authoritative L consensus (§2.3), the 9-pair
  table (§2.4 — all rows hand-verified), validity tiering with F1–F11 (§3), control
  availability + m_pass_l/m_valid/m_evaluable with false-dominant semantics (§4), signal
  dispatch covering every branch with small-N precedence and raw-flag preservation (§5),
  and per-axis truth-table requirements (§6). Three inputs remain underdefined in r3.4's
  own text: (a) pa_valid's numeric form exists only by chain inheritance (errata §2.4
  "PA_VALID same."); (b) tail_driven's control variant is unpinned (§9.4); (c) donor-level
  record semantics for phases 2/3/7 are undefined in §8 (see Q4). A contract that claims
  totality should not require the reader to resolve precedence across nine documents for
  a B0-B gate input.
- 다음 단계:
  1. Pin the tail_driven variant in §9.4 (variant = M_POS_MEAN, as MF-5 itself specified).
  2. Restate PA_VALID (P_VALID form applied to the PA arm) in §7.2.
  3. Define donor-level record semantics (MF-B) in §8, or mark phases 2/3/7 donor records
     as timing/descriptive-only with a defined construction.
```

### Q2. L consensus / fixtures

```text
Q2.
- 판정: agree
- 근거: §2.3 and §2.4 now agree — all 9 rows re-derived: (T,T)→true; (T,F)→NA with
  copy_only=true; (T,NA)→NA, copy_only=NA, full_only=false; (F,T)→NA with full_only=true;
  (F,F)→false; (F,NA)→NA, copy_only=false (false-dominant), full_only=NA; (NA,T)→NA,
  copy_only=false; (NA,F)→NA, full_only=false; (NA,NA)→NA. Mixed true/false reaches only
  NA; copy_only/full_only are evaluated before l_signal in §5.3 (COPY_ONLY_WEAK /
  FULL_ONLY_WEAK), matching the §2.4 note. Fixtures 16–18 are primitive-derived (no
  injected control_status), now use n_signal=15 (r3.3 used 20 — fixed), and fixture 18
  correctly shows m_pass_pos_l=false → m_pass_l=false → M_CONTROL_FAIL under the §6.3
  preconditions. The forbidden "control PASS + m_pass_l=false" cell is stated absent.
- 다음 단계:
  1. Add the 9-pair × validity(VALID/INVALID/NA) × n=14/15 grid as an explicit DoD item
     (§6.4 requires per-axis; make the grid named).
```

### Q3. M preflight / cohort

```text
Q3.
- 판정: agree
- 근거: Preflight verified end-to-end: content SHA-256 matches the frozen hash exactly;
  K_M_L=753 yields 16 train contributors (≥10 floor), 15/20 common targets, 5 excluded
  val docs all below 753; common_ids has exactly 15 IDs and endpoint_ok binds to them
  ("no 15→14 substitution"); full-K L is 11/20 and correctly demoted to secondary; native
  512 gives 20/20 for P/PA. The zero-margin risk is real (boundary docs at exactly 753
  and 754) and is handled by §8.7's assert-and-abort design rather than by silent cohort
  adjustment — the right choice for a prereg.
- 다음 단계:
  1. No blocking step. Optionally record in the D0 artifact that h-length recomputation
     matched the preflight for the two boundary docs (01331=753, 01058=754) explicitly.
```

### Q4. M builder / M_NORM / endpoint / replay / golden vector

```text
Q4.
- 판정: conditional
- 근거: The builder matrix is now complete and consistent (F/L: 753, adapter, trained;
  P: 512, identity; PA: 512, random-init-trained adapter; h_len_i scalar; adapter eval +
  no_grad; per-seed M_POS_MEAN with seed-average before doc bootstrap). real_prefix_t :=
  A(h_t)[:K_M] closes the space bug and is consistently reused for the M primary
  reference, the M_NORM numerator, and real CE. M_NORM is a fixed per-target scalar ×
  one global mean direction — no label leakage. Endpoint identity 1,440 is arithmetically
  exact and donor-free. The golden vector is now independent (computed by a one-off
  script from the spec, committed as golden_vectors.json), with a hand-derivable frame
  example whose bytes I verified (<f4, [1.0, −2.0] → 0000803f 000000c0) and an
  empty-state hash rule. Remaining gaps: (a) phase 7 replay (600/arm-seed, donor-level) —
  §8 defines no donor-level memory construction for Phase 6 (the M controls are
  donor-free), §10.6's replay key nonetheless carries donor_id ∈ {0..4} and a variant
  field whose meaning for donor-level records is undefined, and the donor pool for
  Phase 6 replay is unstated; it is not pinned which records (donor-free 1,440 only, or
  plus donor-level) enter final_replay_hash; (b) §8.3's "one global train-only mean
  matrix" reads as cross-seed, while §8.2 is per-seed; (c) §10.6 pins dtype_str only for
  the synthetic <f4 case; canonicalize the real-tensor dtype string (e.g., always
  str(torch.dtype)) so the hash is implementation-stable.
- 다음 단계:
  1. Pin the phase 7 replay record population: either define donor-level memory
     construction (pool, crop rule, variant meaning, hash membership) or reduce phase 7
     to a donor-free 120/arm-seed replay and re-derive T_proj ≤96 min.
  2. Fix the §8.3 per-seed wording ("per seed, train-only").
  3. Pin the canonical real-tensor dtype_str mapping in §10.6.
```

### Q5. PA

```text
Q5.
- 판정: agree
- 근거: Naming is consistent across §3.1/§4.2/§7.2/§7.4 (PA = acquisition control;
  PA_STEP100_NOT_VALID; ADAPTER_REGIME_LOSS forbidden; PA_RETENTION nullable and
  explicitly non-gating; PA step0 run separately). The scale/geometry caveat is explicit
  (native mT5 512 vs EG2 layer19 753 — different hidden geometry, so PA is not a direct
  retention comparison for L). The new §4.2 PA veto rationale is the right shape: PA
  failure invalidates native-memory-regime calibration, so m_valid = ANDn(P, PA) is an
  intended arm-level calibration veto, it does not alter the L threshold, and
  PA_RETENTION remains descriptive. This is a stated design decision with rationale,
  which is what MF-8 asked for.
- 다음 단계:
  1. Restate PA_VALID (same form/threshold as P_VALID, errata §2.4) inside §7.2 so the
     veto's input predicate is visible without leaving the document.
  2. Add a pa_valid predicate unit test to the DoD.
```

### Q6. Cap / D0 / D1

```text
Q6.
- 판정: agree
- 근거: Arithmetic verified: 4 arms × 3 seeds = 12 units × 100 updates = 1,200
  registered; D0 = 0 updates, ≤4 configs, ≤15 min, seed 20261111, labels_computed:false,
  not_a_result:true; D1 = 4 arm-seeds × 1 update, shared seed 20261111, ≤20 min, separate
  approval, no labels; combined prospective max 1,204 updates / 155 min labeled "not a
  grant"; T_proj = 3 × Σ_arm (100·t_train + 7 timing terms) with phase 5 = 120 and
  phase 7 = 600, ≤96 min, and the explicit prohibitions (no D1-less 3-seed, no D0-only
  projection, no "timing probe" substitute). Phase 5's 120/arm-seed equals 1,440/12
  exactly, so the phase list and the endpoint identity are mutually consistent. The
  phase 7 population's semantics remain open (Q4/MF-B) but its count is fixed.
- 다음 단계:
  1. Resolve MF-B before D1 approval; no cap numbers change.
  2. Keep D0's h-length recompute assert and test_split_used:false in the D0 artifact
     (already in §10.2/§11).
```

### Q7. Statistics

```text
Q7.
- 판정: conditional
- 근거: n_boot 1,000, percentile 2.5/97.5, bootstrap seed 20261109, document unit,
  seed-average-before-bootstrap are all pinned and executable; documents_positive is
  correctly named; missing registered seed → predicate NA with 2-of-available
  substitution forbidden; the new runner/c5_pm_stats.py prohibition of the legacy helper
  is justified — I verified the legacy defect (seed 20261108; seeds_positive counting
  documents) still exists in the current runner. The L predicates (copy ≥ .05 / full > 0
  / CI lower > 0 / paired L>F > 0 / 2-of-3 registered seed means > 0) are executable
  from the defined endpoint records. Two residuals: (a) the tail_driven variant pin
  (MF-A); (b) §9.2's seed_mean note still says "arm-L shuffled-minus-real endpoint mean"
  while §8.5 defines only delta_memfree (control − real) — r3.4 §9 actually contains two
  delta families (the signal-axis step-100 shuffled/donor deltas inherited from errata
  §4.3, and the control-axis delta_memfree used by M_PASS and the tail gate) and never
  names them apart. An implementer can resolve this, but only by chain archaeology.
- 다음 단계:
  1. Pin the tail variant (MF-A).
  2. Rename the two delta families explicitly (e.g., delta_shuffled_* for the signal
     axis vs delta_memfree_* for the control axis) and cross-reference in §9.2.
```

### Q8. Remaining Must-fix (ranked)

```text
Q8.
- 판정: conditional (a short, text-only list remains; nothing requires touching
  thresholds/seeds/donors/steps/LR)
- 근거 / ranked list:
  1. MF-A (high, blocker-for-totality): pin tail_driven's control variant. §9.4 fixes
     arm/endpoint/cohort/delta-sign but not the variant; MF-5's own requirement said
     variant = M_POS_MEAN. Since tail_driven is a B0-B gate input and the two variants
     can disagree, this is a genuine totality gap. One line.
  2. MF-B (high, blocker-for-implementation): define donor-level record semantics.
     Phases 2/3/7 (20×5 donor evals; 15×5 donor replay = 600/arm-seed) and §10.6's
     donor_id ∈ {0..4} replay key presuppose donor-level records, but §8 defines only
     donor-free M controls; the donor pool, the memory construction for donor-level
     records, the meaning of variant for them, and final_replay_hash coverage are all
     unstated. Either define them (donor-crop B0-style secondary) or descope phase 7 to
     donor-free 120/arm-seed and re-derive T_proj.
  3. MF-C (medium): disambiguate the two delta families in §9 and fix the stale
     "shuffled-minus-real" wording in §9.2 (cross-reference §8.5's delta_memfree).
  4. MF-D (medium): restate chain-inherited definitions — PA_VALID (errata §2.4),
     M_GLOBAL (errata §3.2), assay_path_ok/p0_path_ok/p_step100_path_ok/
     pa_step100_path_ok (errata §2.1), the step0/step100 movement fields (errata §2.3),
     and the n_signal per-doc validity criterion (12 endpoint records per doc: F/L × 3
     seeds × copy/full, copy tokens ≥5, finite CE). Or close this via v1.0 (Q13).
  5. MF-E (low, cosmetic): 3-seed checklist item 24 says "F/P/PA M builder existence" —
     add L (§13 correctly says F/L/P/PA); §8.3 "one global train-only mean matrix" →
     "per seed"; pin real-tensor dtype_str; clarify §10.3 phase 5's word "initial" (it
     is the primary M endpoint scoring that produces the 1,440 records); correct the
     request's own P0 val top-3 share mislabel (.4862 signed vs .4335 absolute —
     descriptive only).
- r3.4 created no new contradictions: §2.4 now derives from §2.2/§2.3,
  adapter_lr/T_proj/endpoint are mutually coherent, and fixtures 16–18 align with
  n_signal=15. The only quasi-new issue is the request document's own .4862 mislabel,
  which is outside the contract and descriptive-only.
- 다음 단계:
  1. Write the text-only fixes as r3.5 (MUST-FIX only, per §16) or fold them into v1.0.
  2. Re-verify the §2.4/§9.4/§10.3 deltas after the edit (small diff, cheap check).
```

### Q9. Freeze + implementation approval

```text
Q9.
- 판정: conditional
- 근거: The contract is one short text-only revision away from freezable: MF-A and MF-B
  are genuine totality/implementation gaps; MF-C/MF-D are clarity gaps that predict
  implementation error. With those closed, the §13 DoD is concrete and test-shaped, and
  matches what I verified in the runner (training order, LR groups, mode policy, donor
  conventions already exist in B0 form). The 54 historical tests are B0-era and cover
  none of the PM decision function — the PM unit suite is genuinely new work and must
  precede any run.
- 다음 단계:
  1. Close MF-A…MF-D in text (r3.5 or v1.0), then freeze at commit hash.
  2. Implementation + unit tests: §13 DoD in full, plus pa_valid predicate test,
     tail-variant test, donor-level replay coverage test (post-MF-B), independent golden
     digests (golden_vectors.json), stats-module tests, endpoint-1,440 identity test,
     zero-margin abort test, validity enum assertion, test_split_used:false assertion.
     Pure functions only; no model/data.
  3. D0 zero-update mechanics debug after unit tests green: 0 updates, ≤4 configs,
     ≤15 min, seed 20261111, h-length recompute assert vs preflight,
     labels_computed:false, not_a_result:true, separate from the registered cap.
```

### Q10. D1 / 3-seed boundary

```text
Q10.
- 판정: agree
- 근거: The boundary is maintained and enforced in text: D1 requires separate approval
  and measures all 8 phases with "missing phase → no projection"; T_proj ≤96 min;
  "D1 없이 3-seed 금지", "D0-only projection 금지", "timing probe 대체 금지"; the 3-seed
  gate is a separate 27-item checklist including explicit user approval (item 15) and
  post-run hash validation planning (item 18). Missing checklist items are minor: item
  24 omits L from the builder-existence test; once MF-A/MF-B/MF-D are fixed, add the
  tail-variant test, donor-level replay coverage test, and pa_valid predicate test as
  checklist items.
- 다음 단계:
  1. Keep D1 and 3-seed unapproved in this round.
  2. Amend checklist item 24 to F/L/P/PA and add the three tests after the text fixes.
```

### Q11. B0-B boundary

```text
Q11.
- 판정: agree
- 근거: §14 keeps B0-B behind a separate prereg/approval and explicitly refuses
  tail_driven ∈ {NA, true} and bare EXPLORATORY_L_SIGNAL; full-K 11/20, P0, and
  PA_RETENTION are named as non-evidence. Restated B0-B predicate in r3.4 labels (all
  scalar tri-state; booleans joined by false-dominant ANDn):

  B0-B_gate =
    (validity_status == VALID)                    # §3; no ASSAY_INVALID / *_NOT_VALID tier hit
    AND (control_status == M_CONTROL_PASS)        # §4.3; implies m_evaluable=true ∧ m_pass_l=true
    AND (signal_status == EXPLORATORY_L_SIGNAL)   # §5.3; implies l_signal=true ∧ VALID
    AND (m_valid == true)                         # consistency check (P ∧ PA calibration)
    AND (n_signal == 15)                          # ">= 15" achievable only as == 15 (max)
    AND (tail_driven == false)                    # §9.4; NA/true disqualify
    AND leakage/mode/metric pass
    AND artifact complete
    AND separate prereg/approval

  M_CONTROL_PASS already entails m_evaluable=true and m_pass_l=true;
  EXPLORATORY_L_SIGNAL already entails l_signal=true and validity=VALID; the binding
  extra conditions are n_signal=15, tail_driven=false, and the separate approval.
  B0-B remains NOT approved by this round regardless of r3.4's outcome.
- 다음 단계:
  1. Keep the boundary verbatim in v1.0; no relaxation.
```

### Q12. Final verdict

```text
Q12.
- 판정: NARROW — see the final verdict block (§4).
```

### Q13. Consolidation

```text
Q13.
- 판정: agree (v1.0 consolidated spec is needed before implementation)
- 근거: The contract now spans at least nine documents (v0.2.1-errata, r1–r3.4) with a
  precedence rule, and the definitions an implementer needs live upstream: PA_VALID and
  M_GLOBAL in the errata, the path flags in errata §2.1, the step-field family in §2.3,
  the aggregation/L predicates in §4.2–4.3. Every residual finding this round
  (MF-A…MF-D) is either an inheritance artifact or wording drift of the kind errata
  chains systematically produce — and the r3.3 round's own GLM review predicted exactly
  this failure mode by demanding a primary-text closure audit. A single self-contained
  normative spec with traceability has strictly lower implementation-error risk than
  precedence-chasing; the chain should remain frozen as provenance, not as
  implementation authority. r3.4 cannot be the sole implementation authority because it
  is by construction an errata that defers to the chain ("적용 대상: r3.3";
  "충돌 시: r3.4 > r3.3 > …").
- Minimum v1.0 TOC (normative only, self-contained):
  1. Scope, freeze status, precedence (v1.0 sole authority)
  2. Primitives: tri-state; ANDn/ORn/NOT3; scalar domain; arity rules
  3. L consensus + authoritative 9-pair table
  4. Validity: inputs (path flags defined here), tier ordering, F1–F11
  5. Control: availability, builder_ok, m_pass_l/m_valid, PA veto rationale, control_status
  6. Signal: 15-doc cohort, n_signal criterion (per-doc 12-record validity), labels,
     dispatch, small-N precedence
  7. Arms and training: arm matrix, P_VALID/PA_VALID (restated), hyperparameters,
     movement fields
  8. M: builders (all arms), M_NORM, endpoint identity 1,440, zero-margin, donor-level
     record semantics (post-MF-B), M_GLOBAL
  9. Statistics: constants, named delta families (delta_shuffled vs delta_memfree),
     L predicates, tail gate with pinned variant
  10. D0/D1/cap/T_proj
  11. Hashes, replay records, golden vectors (incl. dtype_str canonicalization)
  12. Artifacts/manifest requirements
  13. B0-B boundary (verbatim from §14)
  14. P0 limitations
  15. Traceability appendix: clause → source version+§, with "changed in v1.0" markers
- 다음 단계:
  1. Write v1.0 from the frozen chain (no new numbers; MF-A…MF-D incorporated).
  2. One separate review round for v1.0 (it is a new normative artifact, not an errata).
  3. Freeze v1.0 at commit hash; implementation proceeds against v1.0 only.
```

---

## 3. Constraints restated (requester's prohibitions, honored in this verdict)

- No approval of Phase 6 execution, B0-B, B1, B2, or Stage C is granted or implied.
- Test 163 stays sealed; P1 stays unused; T5Gemma2 stays under D-108 STOP.
- No threshold/seed/donor/step/LR changes are proposed after results; every fix above is text-only definitional closure.

---

## 4. Final verdict block

```text
최종 판정: NARROW
r3.4 동결:            No — not in current text. Close MF-A…MF-D (text-only r3.5, or fold
                      into v1.0), then freeze at commit hash.
구현+unit tests:      Conditional approval AFTER the text closure; scope = §13 DoD +
                      pa_valid test + tail-variant test + donor-level replay coverage
                      test + independent golden digests + stats tests. Pure functions;
                      no model/data.
D0:                   Conditional approval AFTER the text closure (0 updates, ≤4
                      configs, ≤15 min, seed 20261111, h-length assert,
                      not_a_result:true).
D1:                   Not approved (separate approval; requires MF-B resolved first).
3-seed:               Not approved (separate gate; 27-item checklist + additions).
금지 범위:            Registered Phase 6 execution; B0-B/B1/B2/Stage C; test 163
                      (sealed); P1; T5Gemma2 (D-108 STOP); post-result
                      threshold/seed/donor/step/LR changes; 15→14 substitution; donor
                      substitution; registered-seed substitution.
최대 compute:         Unit tests (CPU-only) + D0 (≤4 configs, ≤15 min, 0 optimizer
                      updates). Registered 1,200 updates remain ungranted until the
                      3-seed gate.
Must-fix (ranked):    1. Pin tail_driven variant (M_POS_MEAN) — §9.4.
                      2. Define donor-level replay record semantics (phases 2/3/7,
                         §10.6 key, final_replay_hash coverage) or descope phase 7 to
                         120/arm-seed and re-derive T_proj.
                      3. Disambiguate delta families in §9; fix stale
                         "shuffled-minus-real" wording.
                      4. Restate chain-inherited definitions (PA_VALID, M_GLOBAL, path
                         flags, step fields, n_signal per-doc criterion) — or close via
                         v1.0.
                      5. Cosmetic: checklist item 24 add L; §8.3 per-seed wording;
                         dtype_str; phase 5 "initial" wording; request's P0 top-3
                         share mislabel.
v1.0 consolidation:   Yes — required before implementation; self-contained,
                      normative-only, traceability appendix; one separate review round;
                      then v1.0 is the sole implementation authority and the errata
                      chain is frozen provenance.
잘못된 전제:          Request §4's "val top-3 share .4862" is the SIGNED share; the
                      r3.4-gate-form absolute share is .4335 (recomputed from
                      p0_native_sanity.json). Descriptive only; no gate impact, but the
                      caveat as written names the wrong quantity.
```

---

## 5. Limitations of this review

- Read-only consultation; no training/evaluation was executed, so all executability claims are text-and-artifact-level, verified against the preflight/P0 artifacts, the runner, and arithmetic — not against a running Phase 6 pipeline.
- The B0-style donor-level evaluation semantics were reconstructed partly from the errata chain and the B0 runner; MF-B flags precisely the place where that reconstruction is not pinned by r3.4 itself.
- Test 163, P1 data, and T5Gemma2 were not opened, per the requester's constraints; judgments touching them are boundary statements only.