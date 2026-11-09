# C5 Phase 6 P/M v1.0.4 — External Review (GLM 5.3 Flash)

- Date: 2026-11-09
- Reviewer: `z-ai/glm-5.3-flash` (reasoning max). Independent round; no reuse of any other model's answer; no subagents.
- Review basis: origin/main HEAD `0bfee85d20dd0017fe6f07f2e8939ff4c7ccf203` ("docs: add C5 P/M v1.0.4 review request"). `git fetch origin` + `git pull --ff-only origin main` → "Already up to date".
- Inputs read: `docs/plan_c5_b0a_pm_prereg_v1_0_4.md` (1,691 lines, full), `golden_vectors.json`, v1.0.3 3-AI synthesis, `m_cohort_preflight.json`, `p0_native_sanity.json`, `p1_usage.json`, `p1_usage.postrun.json`, `phase6_artifact_registry.json`, `runner/c5_mt5_lora_b0.py` (full), `eval/tests/test_c5_b0_metric.py` (full), plus the cited helper modules for contract verification only.
- Constraints honored: no training/evaluation executed; test 163 not opened; P1 data not used (manifest files read only); no subagents/other LLMs; sole write = this file; no post-result threshold/seed/donor/step/LR proposal.
- Status: **v1.0.4 review — CONTINUE (conditional). Registered execution not approved.**

---

## 0. Independent verification performed (pure computation only)

No model, data pipeline, or test was run. I recomputed hashes and arithmetic directly from the repository files:

| check | result |
|---|---|
| state_full `43ecb58e…d65712` | **MATCH** (frame spec recomputed byte-for-byte from golden tensors a/b) |
| state_empty `e3b0c442…7852b855` | **MATCH** |
| replay_base `c43ea35c…7851667` | **MATCH** — flat 8-field records, `sort_keys=true`, compact separators, donor_sort null-first; listed order already canonical |
| replay_supplemental `8277a713…7a20` | **MATCH** |
| control digest, name-asc `6b50c226…01938` | **MATCH** |
| control digest, listed order | `531ba0ad…03bd68` — reproduces exactly the documented insertion-order artifact; non-normative, as the synthesis stated |
| preflight content SHA-256 | `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` = §0.4 **MATCH** |
| 1,680 arithmetic | 15×96=1,440 + 5×48=240; per-unit 120 (F/L) / 160 (P/PA); per-arm F=360, L=360, P=480, PA=480; per-seed total 560 — all consistent |
| phase-7 count | 15 docs × 5 donors × 2 variants × 2 endpoints × 2 memory kinds = 600/arm-seed |
| caps | 1,200 + 4 = 1,204 updates; 15 + 120 + 20 = 155 min; T_proj ≤ 96; hard abort 120 — consistent |
| control footprint | (1+15)·753·512·4·6 + (1+20)·512·512·4·6 = 280,166,400 B ≈ 0.28 GB ≈ "~0.3 GB" ✓ |
| P0 artifact vs request §3 | train 3.7617264 [1.8916853, 5.6049574], 14/20 positive; val 5.2374585 [2.5013211, 8.0752724], 18/20; full 3.5027/5.2936; mean real CE 12.702/13.235; `source_max_length: 256` in artifact — **all match** |
| P0 val tail recomputed from per-doc deltas | median 2.9739; signed top3 .4862; absolute top3 .43355 (val20), .45478 (15 common) — **match** |
| helper contracts in code | `Adapter` = Linear→GELU→Linear→LayerNorm (512→512) ✓; `LoRALinear`: base frozen, `lora_A` kaiming_uniform_(a=√5), `lora_B` zeros, scale=α/r, dropout ✓; `load_layer_cache` → id→{h length-sliced, length} ✓; `make_labels` → [1,L] ✓; `attach_decoder_lora_mt5` = 64 modules, r8/α16/dropout .05 ✓; `native_memory`, `repeated_4gram_rate` present ✓ |

Environment notes (not spec defects): `data/models/mt5-small`, `data/external/f5_pairs_v3_clean.jsonl`, and `data/wave2c/eg2_native_layer19/layer19` are absent from this checkout, so model-dependent unit tests would skip here (the `skipUnless` guard exists); nothing was executed. `runner/c5_pm_stats.py` does not exist yet — correct per §16.1 ("no code before freeze"). The current runner implements smoke / metric-smoke / p0-sanity / train_arm (F,L on EG2 cache) only; P/PA arms, M builder, phase-5/7 record writers, control-manifest builder, checkpoint hashing, stats module, and the decision function are post-freeze implementation work.

---

## Q1. Ten residual closures — verdict: **agree**

| # | v1.0.3 residual | status | evidence |
|---|---|---|---|
| 1 | phase-7 `K_d`/`baseline_ce` | **closed** | §9.6.1: `K_d=min(len(real_prefix),len(donor_prefix))`, `assert 1<=K_d<=min(...)`; `control_pos=M_POS_MEAN[:K_d]`, `control_norm=M_NORM(t)[:K_d]`; `baseline_ce = CE(control_variant[:K_d], target, endpoint)` **recomputed in phase 7**; "phase-5 stored CE at K_M must not be reused"; donor content not mixed; `control` is a baseline, not a record memory kind; 600/arm-seed verified |
| 2 | null total order | **closed** | §12.2: internal `donor_sort=-1` (null) vs 0..4, "not serialized and not hashed", ascending sort, serialized `donor_id=null`; both replay goldens recompute MATCH under this order |
| 3 | flat 8-field hash | **closed (verified)** | §12.2 flat record + golden vectors; my independent SHA-256 recomputation matches `c43ea…`/`8277a7…` only for the flat projection — a nested `{key,ce}` hash cannot reproduce them, so the golden tests seal it |
| 4 | 12-key checkpoint | **closed** | §12.1 JSON object with exactly 12 `arm/seed`→`sha256:…` keys; §11.4 step 1 loads it, paths `checkpoints/{arm}/{seed}.pt`, "no single-checkpoint replay"; arithmetic verified |
| 5 | P1 frozen/postrun | **closed** | §1.5 + §4.0: frozen at freeze with empty inventory, hash into freeze manifest as `p1_manifest_sha256`; separate `p1_usage.postrun.json`; registry file present; `assay_path_ok` uses frozen hash, postrun audit-only; unknown `note` key allowed; malformed→NA, contradictory→false (fail-closed); files on disk match the declared state |
| 6 | control fixture shape | **closed** | golden declares "synthetic framing fixture; not a trained tensor" + scope note "real [K_M,512] control_digest is postrun-only"; NPZ key `tensor`; canonical names `control/{arm}/{seed}/M_POS_MEAN`, `control/{arm}/{seed}/M_NORM/{target_id}` match golden tensor names; `6b50c226` = name-asc (verified), `531ba0ad` = listed-order artifact (verified) |
| 7 | external module contracts | **closed** | §17.1 table with paths/contracts; I verified each cited symbol exists with the stated behavior; missing helper → NOT_ASSESSABLE, no guessing; helper commit hashes to be recorded in the freeze manifest (freeze-time step) |
| 8 | D0 labels/timing | **closed** | §11.2: `labels_computed:false`, `not_a_result:true`, "no timing claim", h-length asserts, control-manifest path/size; §11.3: "`labels_computed:false` refers to decision/signal labels, not target-token labels"; control manifest built after step0, before any decision label |
| 9 | per-arm notation | **closed** | F=360, L=360, P=480, PA=480, total 1,680 restated in §11.5; 155-min envelope in §11.6; `M_CONTROL_PREFIX753_COHORT15` in preflight/§14 |
| 10 | dtype/fixture order/note | **closed** | golden uses `dtype_str "<f4"` (§12.1 bans torch strings); fixture order now normative as "sorted by canonical name" — verified numerically (6b50 asc vs 531ba listed); `p1_usage` note key allowed |

Next steps: none required for closure; fold the two low notes (MF-3/MF-4 below) into the freeze text.

## Q2. Self-containedness — verdict: **conditional (agree with declared imports)**

Evidence: an implementer can build from v1.0.4 alone given (a) §17.1 helper modules frozen by citation at the freeze commit, (b) §2.6 data paths, (c) preflight artifact + frozen hash, (d) golden vectors. `c5_pm_stats.py`'s contract is defined in §10.2 (new module, seed 20261109, no P0 helper reuse — correctly diagnosing the legacy `bootstrap_paired(seed=20261108)`/`seeds_positive` doc-count mislabel).

Remaining external references (declared, not implicit): the five §17.1 helpers; the data/cache paths; splits.json schema (fields declared; test list must not be read); freeze manifest itself.

Next steps: (1) at freeze, record the five helper commit hashes in the freeze manifest; (2) resolve the checkpoint base-directory ambiguity (MF-2 below).

## Q3. Phase-7 measurement — verdict: **agree**

Evidence: the recipe is now executable as written. `K_d` bounds are asserted; slices are explicit; `baseline_ce` is recomputed per record in phase-7 conditions (it varies with donor because `K_d` varies — e.g., F/L donors with h_len<753 give `K_d<753`, and P/PA always give `K_d=512`); 15×5×2×2×2=600 confirmed; phase-5 CE reuse is explicitly banned; phase-7 stays diagnostic and outside `replay_ok` (§11.4 step 6–7). "Raw `ce` may duplicate across variants, but `delta` differs" is consistent with the record schema.

Next steps: (1) implementation must assert `K_d>=1` and recompute `baseline_ce` per record; (2) add a test that phase-5 stored CE values never appear as phase-7 `baseline_ce`.

## Q4. Canonical hash — verdict: **agree (independently verified)**

Evidence: flat 8-field records; `sort_keys=true,separators=(',',':')`; `donor_sort` internal-only; `baseline_ce`/`delta` excluded from the hash domain. I recomputed `c43ea35c…` and `8277a713…` from the golden records and both MATCH; the listed orders are already canonical. A nested `{key,ce}` projection yields a different digest, so the golden vectors make the nested form fail-closed. One residual: no golden vector exercises a case where `donor_sort` (-1 vs 0) is the *deciding* sort field (in both vectors, `doc_id`/`memory_kind` already determine order), so the null-before-0 rule is pinned by §12.2 text but not by digest.

Next steps: (1) permutation/duplicate/missing-key tests (§12.3/§13.4); (2) optional unit-test fixture pair where donor_sort is the deciding field (MF-4).

## Q5. Checkpoint map — verdict: **agree**

Evidence: 12-key `final_checkpoint_hash.json` shape matches §12.1 exactly (`F/20261108`…`PA/20261110`); `checkpoints/{arm}/{seed}.pt` with per-unit restore; per-unit phase-5 records F/L 15×2×2×2=120, P/PA 20×2×2×2=160; aggregates F=3×120=360, L=360, P=3×160=480, PA=480, total 1,680 = 1,440+240 ✓; replay procedure (§11.4) restores each unit, no single checkpoint; numeric tolerance (`atol=1e-5, rtol=1e-4`) separated from exact SHA-256 integrity.

Next steps: (1) unit test asserting the map's exact key set and per-key file existence; (2) state-hash frame test against `43ecb58e…`/`e3b0c442…`.

## Q6. P1 — verdict: **agree**

Evidence: frozen `p1_usage.json` on disk has `manifest_version 1`, `p1_used:false`, `test_split_read:false`, empty `checked_artifacts` — valid pre-run per §1.5; `p1_usage.postrun.json` is separate with `status:"not_run"` and an explicit "frozen file must not be modified" note; registry lists the five expected artifacts; `test_split_used` is evaluated by allowlist membership (frozen train20∪val20), never by scanning sealed test 163; missing/malformed → `assay_path_ok=NA` (→ NOT_ASSESSABLE), contradictory known-use → false (→ ASSAY_INVALID): fail-closed in the right direction.

Next steps: (1) at freeze, compute and record `p1_manifest_sha256`; (2) postrun inventory must be compared against the registry audit-only.

## Q7. Control tensors — verdict: **agree (independently verified)**

Evidence: synthetic `[1,1]` framing fixture is explicitly declared in both golden JSON and §12.3; real `[K_M,512]` digest is postrun-only; NPZ array key `tensor`; canonical names match the golden tensor names; `6b50c226…` reproduces only under name-asc frame ordering (verified), and the listed order reproduces `531ba0ad…`, confirming the synthesis's "insertion-order artifact, not normative" note; `control_manifest.json` fields (name/path/array_key/target_id/dtype/shape/sha256) and frame-over-tensor (not ZIP) hashing are specified; footprint ≈0.28 GB matches the "~0.3 GB" budget.

Next steps: implement `control_digest` strictly as name-asc frame concatenation; assert per-arm-seed tensor presence (15 F/L + 20 P/PA targets).

## Q8. External modules — verdict: **agree**

Evidence: all seven contracts verified against the cited files (see §0 table). `attach_decoder_lora_mt5` and `native_memory` already live in `runner/c5_mt5_lora_b0.py` as §17.1 assigns. Missing helper → NOT_ASSESSABLE is safe (fail-closed, no reimplementation with divergent semantics). The §17.1 one-line `Adapter` contract is coarse (Linear→GELU→Linear→LayerNorm is in §2.5.4), so table + §2.5.4 together are sufficient.

Next steps: (1) freeze manifest records helper commit hashes; (2) unit tests import helpers rather than reimplementing them (the existing test file already does this).

## Q9. D0/D1/cap — verdict: **agree**

Evidence: D0 = 0 updates, ≤4 configs (one per arm, no variant/seed duplication), ≤15 min, seed 20261111, `labels_computed:false`, `not_a_result:true`, h-length asserts, no timing claim, control-manifest path+size. D1 = 4 arms × 1 debug seed (20261111) × 1 update, ≤20 min, separate approval, 8 phases with phase-5 560 (120+120+160+160) and phase-7 600/arm-seed; step0 before update or restored state. T_proj = 3×Σ_arm(9 terms) ≤ 96 min; 120-min hard abort; prospective (not granted) 1,204 updates/155 min = 1,200+4 and 15+120+20 ✓; "D1 없이 3-seed 금지", "D0 projection 금지", no timing-probe substitute.

Next steps: (1) D0 harness must emit no wall-clock-derived claims; (2) keep D1 gating separate.

## Q10. Remaining / new must-fix — verdict: **conditional (no new blocker; low-ranked list)**

Explicit checks requested: (a) `baseline_ce`/`delta` are outside the phase-7 hash domain — confirmed by §12.2 and by digest reproduction with exactly 8 fields; (b) 12-key map vs runner — the current runner contains no checkpoint/M/phase-5/7 code at all; the map is internally consistent and is post-freeze implementation scope, not a mismatch; (c) P1 frozen/postrun separation is auditable via `p1_manifest_sha256` + registry + postrun inventory.

Ranked must-fix (all text/test-level; none blocks freeze):

1. **MF-1 (low-medium): supplemental (phase-7) replay digest population undefined.** §11.4 step 5 says "verify supplemental replay digest" (singular) but does not state whether it pools all 12 arm-seeds (12×600=7,200 records) or is per arm-seed (12 digests), and no artifact field name is defined for it (contrast `debug_replay_hash`/`final_replay_hash`/`control_digest`). One clarifying line + field name needed.
2. **MF-2 (low): checkpoint base directory ambiguity.** §17.2 says "no artifact path outside `reports/provenance/C5_b0a/` for provenance" while the registry/§12.1 use relative `checkpoints/{arm}/{seed}.pt`. State the base explicitly (recommend `reports/provenance/C5_b0a/checkpoints/{arm}/{seed}.pt`).
3. **MF-3 (low): `M_NORM(t)[:K_d]` truncation semantics.** Add a half-line that `M_NORM(t)` is the §9.3 K_M-scaled vector truncated at `K_d` (no re-normalization at `K_d`) to prevent implementer divergence; note that for P/PA `K_d=K_M=512` always, so this only bites F/L donors with h_len<753.
4. **MF-4 (low, test-side): null-vs-0 donor_sort tie not digest-pinned.** No golden vector has `donor_sort` as the deciding field; §12.2 text is authoritative. Add a unit-test fixture pair (e.g., same doc_id/arm/seed/variant/endpoint/memory_kind with null and 0) rather than changing vectors.
5. **MF-5 (cosmetic): golden `ordering` note wording.** `golden_vectors.json` supplemental says "sorted ascending by canonical key (…, donor_id)"; the normative sort field is internal `donor_sort` (§12.2). Harmonize wording or annotate §12.2 authority.

Observations (not must-fix): legacy runner gap is expected under §16.1; `bootstrap_paired(seed=20261108)`/`seeds_positive` mislabel stays legacy and is already neutralized by §10.2's new stats module; P0 artifacts remain descriptive.

## Q11. Freeze / implementation / unit tests / D0 — verdict: **conditional-approve**

Evidence: all ten v1.0.3 residuals are closed in text; the five golden digests and the preflight hash reproduce independently; the arithmetic (1,680/560/600, 360/480, 1,204/155) is consistent; helper contracts exist in code. The only findings are MF-1..MF-5, all text/test-level with no scientific content — compatible with "must-fix only; no new scientific choices" (§16.1).

Essential tests before implementation proceeds (order matters — cheap and pure first):
1. Golden digest tests: all five vectors, plus permutation invariance and duplicate/missing-key rejection.
2. Decision tests: ANDn 2/4/5; F1–F11; §3.4 nine L pairs; fixtures 16–18; full dispatch ladder; INVALID vs NOT_ASSESSABLE preservation.
3. M tests: builder (16/20 contributors, ≥10 gate), endpoint exact mixed key set (1,680; 96/48 appearances), zero-margin abort (754→14), no-`delta_memfree`.
4. Stats tests: n_boot 1000, seed 20261109, `documents_positive`/`seeds_positive` semantics, tail rule and ties.
5. Checkpoint-map test (exact 12 keys, per-unit 120/160) and P1 strict both-flags/malformed→NA test.

Then D0 zero-update mechanics. Unit tests that load mT5-small run only where the data exists (skip-guard already present); no training steps anywhere in this scope.

## Q12. B0-B / D1 / 3-seed boundaries — verdict: **agree**

Evidence: §16.3 approval explicitly excludes D1, 3-seed, B0-B/B1/B2/Stage C, test 163/P1, T5Gemma2 (D-108 STOP). §14 B0-B predicate restated in v1.0.4 labels:

```text
B0-B (separate prereg/approval required):
  validity_status == VALID
  AND control_status == M_CONTROL_PASS
  AND signal_status == EXPLORATORY_L_SIGNAL
  AND m_valid == true
  AND n_signal >= 15   # max is 15, so exactly 15
  AND tail_driven == false   # true/NA both block; signal tail only
  AND leakage/mode/metric pass
  AND artifact complete
  AND separate prereg/approval
```

`EXPLORATORY_L_SIGNAL` alone is not approval; `full_k_secondary`, P0, and `PA_RETENTION` are not B0-B evidence; no B1/B2/Stage C auto-progression; M scope is `M_CONTROL_PREFIX753_COHORT15`.

Next steps: none — boundaries are sufficient as written.

## Q13. Final verdict and freeze — **CONTINUE (conditional)**

```text
Final verdict: CONTINUE
v1.0.4 freeze: YES — after absorbing MF-1..MF-5 (text-only) into the freeze commit
               (post-freeze corrections only via numbered ERRATA)
Implementation+unit tests: APPROVED — §13 matrix only; no training; no test 163/P1;
               helper-import discipline per §17.1
D0: APPROVED — ≤4 configs (one per arm), 0 optimizer updates, ≤15 min, seed 20261111,
    threads 6, no GPU, no timing claims, not_a_result:true
D1: NOT APPROVED (separate approval)
3-seed: NOT APPROVED
Forbidden: test 163 (sealed), P1 data use, T5Gemma2 (D-108 STOP stands),
    B0-B/B1/B2/Stage C, any post-result threshold/seed/donor/step/LR change,
    registered Phase 6 run before D1 + separate approvals
Max compute (approved scope): CPU-only implementation + unit tests (mT5-small loads,
    zero training steps) + D0 ≤4 configs ≤15 min. Nothing beyond.
test 163 status: sealed; allowlist-membership checks only
v1.0.4 single implementation authority: YES (v1.0.4 + numbered ERRATA only)
Must-fix (ranked): MF-1 supplemental digest population; MF-2 checkpoint base dir;
    MF-3 M_NORM truncation note; MF-4 donor_sort tie test; MF-5 ordering-note wording
Wrong premises: none material found (P0 §3 figures and all digests verified)
```

Rationale: v1.0.3's blocker set (2 NARROW / 1 CONTINUE) is closed in v1.0.4 text, and the closure is now *independently verifiable*: the flat-hash, null-ordering, state-frame, and control digests reproduce from the golden vectors alone, and the preflight hash, cohort arithmetic, P0 figures, and helper contracts all check out against the artifacts. What remains are five documentation/test-level clarifications that do not touch any scientific choice. Freezing v1.0.4 (with MF-1..MF-5 absorbed) and proceeding to implementation + unit tests + D0 is justified; nothing in this review approves Phase 6 execution, D1, 3-seed, B0-B, or any downstream stage.