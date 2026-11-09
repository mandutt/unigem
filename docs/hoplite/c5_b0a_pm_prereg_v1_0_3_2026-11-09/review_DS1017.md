# C5 Phase 6 P/M Prereg v1.0.3 — Independent External Review

- Reviewer: **DeepSeek V4.1 Flash 1017 high** (Hoplite `deepseek-v4.1-flash-1017`, OpenRouter)
- Review round: **v1.0.3**, new independent round
- Review basis: `origin/main` HEAD `82648462b087e013fc9d85568d16faefe993ef63`
  (`8264846 docs: add C5 P/M v1.0.3 review request`)
- Request: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_3_2026-11-09.md`
- Target: `docs/plan_c5_b0a_pm_prereg_v1_0_3.md` (1,618 lines)
- Mode: **read-only consultation**. No training, no evaluation, no test 163, no P1 data, no external APIs, no subagents.
- Only permitted write: this report file.

## 0. Synchronization and method

```
git remote -v          -> origin https://github.com/mandutt/unigem.git
git fetch origin       -> (no error)
git pull --ff-only origin main -> "Already up to date."
git rev-parse HEAD     -> 82648462b087e013fc9d85568d16faefe993ef63
```

Note: the review request cites basis HEAD `97e9d12`; the current `origin/main` head is
`8264846` (the commit that adds the review request itself). All statements below are
against `8264846`.

Independence note: the repository's own prior synthesis (`D-133`, `D-136`) lists
"DeepSeek V4.1 Flash 1017 high" as a v1.0.1/v1.0.2 reviewer label. The run metadata for
this round names a distinct route (`deepseek-v4.1-flash-1017`, distinct from
`deepseek/deepseek-v4.1-flash`). The repository cannot itself prove model distinctness,
so this report does not rely on the prior answer. Every digest and count below was
recomputed independently in this run from the frozen fixtures; no prior review text,
verdict, or number was reused.

Independent recomputation performed with Python `json`/`hashlib`/`struct` only
(no model, no data forward):

| item | computed | expected | result |
|---|---|---|---|
| preflight content SHA-256 | `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` | same | **match** |
| state frame | `43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712` | same | **match** |
| empty state | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | same | **match** |
| replay base (canonical JSON) | `c43ea35c46c51a0e82cebe5764a989d1b67012b2690246a0f89a94dff7851667` | same | **match** |
| replay supplemental (ascending key) | `8277a713fd52b2ba8c5c3c859c83fd78593aa5a381f8640448e2128a97af7a20` | same | **match** |
| control manifest (frames sorted by canonical name) | `6b50c226ecc402323787bd25b20e57fe57376caeb925c040b57985ccc0ec1938` | same | **match** |

The control digest matched only after frames were sorted by canonical name, exactly as
§12.1 requires (`control_digest` = SHA-256 over all control frames sorted by canonical
name). Hashing in fixture insertion order gives `531ba0ad…`, which is *not* the normative
rule. This is a useful warning for implementers: the fixture's array order is
`M_POS_MEAN` then `M_NORM/doc_a`, but canonical name order is `M_NORM/doc_a` before
`M_POS_MEAN`.

---

## 1. Q1–Q13

### Q1. Are the 10 v1.0.2 blockers actually closed?

- **Verdict: conditional — 9 closed, 1 partial.**

| # | blocker | status | evidence |
|---|---|---|---|
| 1 | `donor_sort` vs `donor_id` | **closed** | §12.2 key = `(doc_id, arm, seed, variant, endpoint, memory_kind, donor_id)`; `donor_sort` internal only, not serialized/hashed. Base golden recomputes to `c43ea…` with `donor_id`. |
| 2 | 12-checkpoint replay | **closed** | §12.1 `final_checkpoint_hash` = 12-key `(arm,seed)` map; §11.4 step 1 loads the map; per-unit 120/160; aggregate 1,680. Residual: map serialization form not specified (see MF-5). |
| 3 | per-arm 420 → 360/480 | **closed** | §11.5 and §13.4: F/L 360, P/PA 480, total 1,680; D1 120/160, total 560. Arithmetic verified (Q4). |
| 4 | phase-7 enum / CE | **partial** | Enum closed (`{control,real,donor}` general; phase 5 `{control,real}`; phase 7 `{real,donor}`); `ce`/`baseline_ce`/`delta` defined. But `K_d` / `M_POS_MEAN[:K_d]` can exceed `K_M` for F/L, and `baseline_ce` is not bound to `K_d` (Q5, MF-1/MF-2). |
| 5 | supplemental golden `8277a7…` | **closed** | Independently recomputed `8277a713…` for both the file order and ascending-key order. |
| 6 | P1 strict both flags | **closed** | §4.0 `assay_path_ok` requires `p1_used=false` **and** `test_split_read=false`, manifest SHA-256, allowlist; malformed→NA, contradictory→false. Residual: `checked_artifacts` completeness rule undefined (MF-6). |
| 7 | `P_VALID` tri-state / F9 | **closed** | §4.5 tri-state (false/NA/true); F9 `p_step NA + p_valid NA → NOT_ASSESSABLE`; F10 likewise; `M_CONTROL_INVALID` reachable when P/PA valid but calibration fails. |
| 8 | control tensor schema | **closed** | §12.1 NPZ key `tensor`, canonical names, `<f4`, frame hash over tensor frame (not ZIP), `control_digest`; `6b50…` verified under canonical-name sort. Residual: fixture shape `[1,1]` vs normative `[K_M,512]` (MF-7). |
| 9 | P/PA calibration asymmetry | **closed** | §4.5 documents omitted `2/3 seeds_positive` and paired `L>F` for P/PA; no threshold change. Defensible: no paired P/PA counterpart exists. |
| 10 | D0 / artifact / native assert | **closed** | §11.2 D0 ≤4 configs = one 0-update config per arm; control manifest path `reports/provenance/C5_b0a/control_manifest/`, ~0.3 GB; h-length and native-512 assert. Residual: D0 `labels_computed` clarification (MF-9). |

- **Next steps:** (1) close #4 via MF-1/MF-2 text ERRATA; (2) close residuals MF-5–MF-9 without changing any scientific choice; (3) re-freeze only after ERRATA are numbered.

### Q2. Is v1.0.3 self-contained enough to implement?

- **Verdict: conditional.**
- **Evidence:** the measurement contract is now strong: §2.5.1 model/tokenizer/prefix/512/256; §2.5.2 same-position CE; §2.5.3 memory construction; §2.5.4 `Adapter(512,512): Linear→GELU→Linear→LayerNorm`, LoRA 64 decoder q/k/v/o, `r8 alpha16 dropout .05`; §2.5.5 copyable mask; §2.5.6 donor rule; §2.5.7 generation. However, the document asserts "구현자는 이 문서만 읽고 코드를 작성할 수 있어야 한다" while still depending on repository modules whose contracts are not restated: `runner/c5_mt5_layer_probe.py` (`Adapter`, `make_labels`, `load_layer_cache`), `runner/c5_a1_lora.py` (`LoRALinear`), `runner/c5_a2null_eval.py` (`repeated_4gram_rate`), plus EG2 cache NPZ fields and `splits.json` semantics. §2.6 states the cache fields (`ids`, `lengths`, `h`), which helps, but `make_labels`/`load_layer_cache` behavior is not normative in v1.0.3.
- **Next steps:** (1) add a short "external contract" appendix naming each imported symbol and its required behavior; (2) either inline `make_labels` semantics or declare the existing module normative-by-reference; (3) keep the doc's single-authority claim honest by listing data/model paths as frozen inputs.

### Q3. Do canonical key and golden digests agree?

- **Verdict: agree, with one definitional gap.**
- **Evidence:** all four fixtures reproduce exactly (see §0 table). Base `c43ea…` uses `donor_id` (null/0) and is preserved; changing the key from `donor_sort` to `donor_id` did **not** break the base digest. Supplemental `8277a7…` is the ascending-key hash; the supplied record order already equals ascending key order, so both orderings coincide. Control `6b50…` is correct under canonical-name sort. `sort_keys=true,separators=(',',':')` is specified.
- **Gap:** "sort ascending by key" is not a total order when `donor_id` mixes `null` and `0..4` in one array — and the base golden does exactly that (`doc_a` rows have `null`, the `doc_b` row has `0`). Python cannot compare `None` with `int`; another language may define a different order. The document must define the null ordering (e.g., `null` sorts before `0`, or sort internally by `donor_sort=-1/0..4` while serializing `donor_id`).
- **Next steps:** (1) define the total order explicitly (MF-3); (2) add a permutation-invariance test that shuffles the base and supplemental arrays; (3) keep the verified constants unchanged.

### Q4. Is the replay arithmetic correct?

- **Verdict: agree.**
- **Evidence:**

| quantity | computation | value |
|---|---|---:|
| phase-5 F/L per arm-seed | 15 × 2 variants × 2 endpoints × 2 memory kinds | 120 |
| phase-5 P/PA per arm-seed | 20 × 2 × 2 × 2 | 160 |
| D1 phase 5 total | 120+120+160+160 | 560 |
| registered F (3 seeds) | 3 × 120 | 360 |
| registered L (3 seeds) | 3 × 120 | 360 |
| registered P (3 seeds) | 3 × 160 | 480 |
| registered PA (3 seeds) | 3 × 160 | 480 |
| registered total | 360+360+480+480 | **1,680** |
| phase 7 per arm-seed | 15 × 5 donors × 2 × 2 × 2 | 600 |
| common target appearances | 4 arms × 3 seeds × 2 × 2 × 2 | 96 → 15×96=1,440 |
| native-only appearances | 2 arms × 3 × 2 × 2 × 2 | 48 → 5×48=240 |

- `T_proj` is a `3 × Σ_arm(…)` with `t_primary_replay_arm` at the arm-seed 120/160, which scales to 360/480 across seeds — consistent. Phase-7 diagnostic is explicitly excluded from primary `replay_ok` (§11.4 step 7). No arithmetic error found.
- Minor notation risk: "F/L 360, P/PA 480" can be misread as F+L=360 and P+PA=480. It means **F=360, L=360, P=480, PA=480**. Make that explicit (MF-10).
- **Next steps:** (1) restate the per-arm table explicitly; (2) keep `T_proj` per-arm-seed semantics; (3) add a unit test asserting the 12-unit → 1,680 aggregation.

### Q5. Is phase-7 measurement executable and does 600 hold?

- **Verdict: conditional — the count holds, but the recipe is not executable as written for F/L.**
- **Evidence:** 600 = 15×5×2×2×2 holds. `ce` = raw CE of the record tensor, `baseline_ce` = control variant CE, `delta = baseline_ce - ce`; variant selects the baseline; raw `ce` may duplicate across variants while `delta` differs; phase-7 records store `{key, ce, baseline_ce, delta}` and the canonical replay hash uses `{key, ce}` only. That part is coherent.
- **Defect (F/L domain):** `K_d = min(len(real_prefix), len(donor_prefix))` is defined on memory prefixes whose F/L lengths are EG2 `h_len` (preflight range 708–830), while `K_M = 753`. If `real_prefix`/`donor_prefix` are not truncated to `K_M`, then `K_d` can exceed 753 (e.g., 830 and 806 → 806), and `control_pos = M_POS_MEAN[:K_d]` / `control_norm = M_NORM(t)[:K_d]` become **out of range** because those tensors have only `K_M=753` rows. For P/PA this cannot happen (native length 512 = `K_M`).
- **Defect (binding):** `baseline_ce` is "control variant CE for the same doc/endpoint" but the document does not say it is computed at `K_d` (it must be, to pair with `real`/`donor` at `K_d`), nor that it uses `control_pos` vs `control_norm` according to `variant`.
- **Defect (hash conflation):** §11.4 step 5 says "recompute phase-7 diagnostic 600/arm-seed separately; verify supplemental replay digest". The supplemental golden `8277a7…` is a **four-record synthetic fixture**, not the 600/arm-seed postrun digest. The real phase-7 digest is not golden-pinned and cannot be "verified" against `8277a7…`.
- **Next steps:** (1) define `K_d = min(K_M, len(real_prefix), len(donor_prefix))` and state truncation of both prefixes to `K_M` (or cap `K_d ≤ K_M`) so control slicing is always valid; (2) define `baseline_ce` at `K_d` with variant-selected control; (3) separate the supplemental golden fixture from the postrun phase-7 digest (MF-4).

### Q6. Is P1 / allowlist fail-closed and does it avoid test 163?

- **Verdict: agree (with a completeness residual).**
- **Evidence:** §4.0 requires both strict booleans, manifest SHA-256 match, preflight hash/ID match, `test_split_used=false`, allowlist membership; missing/malformed manifest → `assay_path_ok=NA`; contradictory known use → `false`; false declaration is explicitly an attestation, not proof. `test_split_used` is evaluated by allowlist membership, never by scanning sealed test 163. Current `p1_usage.json` has `p1_used=false`, `test_split_read=false`, `checked_artifacts=[]`; this is valid pre-artifact. Test 163 is not opened.
- **Residual:** §1.5 says "after artifacts exist, incomplete list → NA" but does not define the expected artifact registry that determines completeness. Also the shipped manifest contains an extra `note` field not shown in §1.5; a strict schema validator would reject it.
- **Next steps:** (1) define the expected artifact registry or downgrade inventory to advisory; (2) state that extra manifest fields are allowed; (3) hash the manifest at freeze.

### Q7. Does `P_VALID` tri-state keep `M_CONTROL_INVALID` reachable, and is asymmetry justified?

- **Verdict: agree.**
- **Evidence:** §4.5 `P_VALID` is tri-state: path false or nonfinite → false; path NA or missing/unreadable → NA; path true + 20 native ×2×2×2 per seed finite → true. §5.4: `m_evaluable true` + `p_valid/pa_valid true` + `m_valid false → M_CONTROL_INVALID`; `p_valid=false` routes to `M_NOT_EVALUABLE`, not `M_CONTROL_INVALID`. F9/F10 are reachable. Asymmetry is documented: P/PA copy `>= .05` vs L `>0`, and P/PA omit `2/3 seeds_positive` and paired `L>F`; the paired conjunct has no P/PA counterpart, so omission is defensible. This is a pre-result choice; it must not be changed post-result.
- **Next steps:** (1) add an explicit unit test for the F9/F10 tier precedence; (2) test `p_valid=false → M_NOT_EVALUABLE` and `m_valid=false + valid P/PA → M_CONTROL_INVALID`; (3) record the asymmetry in the freeze manifest as a fixed choice.

### Q8. Are control tensors reproducible and within footprint?

- **Verdict: agree (with fixture-coverage note).**
- **Evidence:** §12.1 defines the path layout, NPZ array key `tensor`, canonical names `control/{arm}/{seed}/M_POS_MEAN` and `.../M_NORM/{target_id}`, dtype `<f4`, shape `[K_M,512]`, `target_id="__shared__"` for the shared mean, version-1 manifest fields, frame hash over tensor frames, and `control_digest` sorted by canonical name. The `6b50…` digest reproduces under that rule. Footprint estimate is consistent: F/L `M_POS_MEAN` ≈ 753×512×4 ≈ 1.54 MB ×6, P/PA ≈ 1.05 MB ×6, plus per-target `M_NORM` (15 or 20 per arm-seed) → ≈ 0.28 GB, i.e. ~0.3 GB.
- **Residual:** the golden fixture uses shape `[1,1]`, not the normative `[K_M,512]`, and has only 2 tensors; it tests framing/name-sort but not the real 15/20-target `control_digest`. Also `control_digest` is not listed among the `control_manifest.json` version-1 fields, although §11.4 requires verifying it.
- **Next steps:** (1) add `control_digest` to the manifest schema; (2) add a realistic-shape fixture or state that the real `control_digest` is postrun-only and not golden-pinned; (3) test canonical-name sort explicitly (the insertion-order hash differs).

### Q9. Are D0/D1/cap correct?

- **Verdict: agree (with labeling clarifications).**
- **Evidence:** D0: 0 updates, ≤4 configs = one 0-update config per arm, ≤15 min, seed 20261111, `labels_computed:false`, `not_a_result:true`, separate cap, h-length and native-512 assert, control manifest path/footprint/retention. D1: 4 arms × 1 debug seed = 4 units, 1 update/arm, ≤20 min, 8 phases, phase-5 560, phase-7 600/arm-seed, `debug_replay_hash` only, no debug-vs-final comparison, target-token labels computed but no decision/signal labels. Registered: 12 units, 1,200 updates, 120 min, 6 threads, no GPU, no retry; `T_proj ≤ 96` min; 120-min hard abort. `1,204 = 1,200 + 4` D1 updates; `155 = 15 + 20 + 120` min, so the "155 min prospective max" is consistent if it is the D0+D1+registered envelope.
- **Residuals:** §11.2 D0 does not repeat the D1 clarification that `labels_computed:false` means decision/signal labels rather than target-token labels; the document does not say whether D0 or the registered run builds `control_manifest/`.
- **Next steps:** (1) apply the D1 label clarification to D0; (2) state the control-manifest build point; (3) label 155 min as the D0+D1+registered envelope and keep 120 min as the registered hard abort.

### Q10. What Must-fix remains, and did v1.0.3 create new problems?

- **Verdict: conditional — 10 ranked Must-fix items, all text/schema/test only; no scientific-choice change.**
- **Ranked list:**

| rank | id | severity | Must-fix |
|---|---|---|---|
| 1 | MF-1 | high | Phase-7 `K_d`/control slicing: `K_d` can exceed `K_M=753` for F/L (preflight h_len up to 830), making `M_POS_MEAN[:K_d]` invalid. Define `K_d = min(K_M, len(real), len(donor))` and truncate both prefixes to `K_M`. |
| 2 | MF-2 | high | Phase-7 `baseline_ce` binding: define it as the variant-selected control CE at `K_d`, not the phase-5 `K_M` baseline. |
| 3 | MF-3 | medium-high | Canonical sort total order for `donor_id` `null` vs `0..4` (base golden mixes them). Define `null` order or sort by internal `donor_sort`. |
| 4 | MF-4 | medium | Separate the four-record supplemental golden from the real 600/arm-seed phase-7 replay digest (§11.4 step 5 conflates them). |
| 5 | MF-5 | medium | Define the 12-key `final_checkpoint_hash` JSON shape and add `control_digest` to `control_manifest.json`. |
| 6 | MF-6 | medium | Define P1 `checked_artifacts` completeness (expected artifact registry) and allow the `note` field. |
| 7 | MF-7 | low-medium | Control golden fixture uses `[1,1]`, not `[K_M,512]`; add a realistic-shape fixture or declare real `control_digest` postrun-only. |
| 8 | MF-8 | low | Self-containedness: enumerate external module contracts (`Adapter`, `make_labels`, `load_layer_cache`, `LoRALinear`, `repeated_4gram_rate`). |
| 9 | MF-9 | low | D0 `labels_computed` clarification and control-manifest build timing. |
| 10 | MF-10 | low | Restate `F=360, L=360, P=480, PA=480, total 1,680`; label 155 min as the D0+D1+registered envelope. |

- **New problems introduced by v1.0.3:** yes, but all are specification-level: MF-1/MF-2 (phase-7 executability), MF-3 (null ordering), MF-4 (fixture/digest conflation), MF-5 (map/manifest schema). The key v1.0.2 concerns are genuinely fixed: canonical key is `donor_id`, base `c43ea…` is preserved, 12 checkpoints and 360/480 are stated, supplemental order is `8277a7…`, P1 gates both flags, `P_VALID` is tri-state, control schema exists, asymmetry is documented, and D0/native-assert are defined.
- **Specific checks requested in Q10:** canonical-key change does **not** break the base digest (verified); the 12-checkpoint map is stated in §12.1/§11.4 but its serialized form is not yet specified (MF-5); phase-7 `baseline_ce` does **not** collide with the replay hash because the hash uses `{key, ce}` only — but its `K_d` binding is undefined (MF-2).
- **Next steps:** (1) produce a numbered ERRATA for MF-1..MF-10; (2) add the associated unit tests; (3) do not change any threshold, seed, donor, step, or LR.

### Q11. Can v1.0.3 be frozen and implementation + unit tests + D0 approved?

- **Verdict: conditional — freeze after ERRATA; implementation and unit tests after freeze; D0 after implementation and unit tests.**
- **Evidence:** the 10 blockers are 9 closed / 1 partial; all golden digests and the preflight hash reproduce; arithmetic is correct; P1/test-163 boundaries are intact. Remaining issues are normative-text/schema ambiguities, not empirical choices. §16.1 already reserves must-fix for exactly this case ("If NARROW: must-fix only; no new scientific choices").
- **Required tests before implementation:** state/empty/base/supplemental/control golden reproduction; permutation invariance; canonical-name control sort; 12-unit → 1,680 aggregation; phase-5 `{control,real}` / phase-7 `{real,donor}` key domains; `K_d ≤ K_M` guard; F1–F11; 9 L pairs; fixtures 16–18; `P_VALID` tri-state and F9/F10; `M_CONTROL_INVALID` reachability; `p0_path_ok` mode-only compatibility; P1 malformed→NA/contradictory→false.
- **Next steps:** (1) issue ERRATA and re-freeze; (2) implement pure decision function + hash/replay utilities; (3) run unit tests and D0 zero-update mechanics only, within ≤15 min and 0 optimizer updates.

### Q12. Are the B0-B / D1 / 3-seed boundaries sufficient?

- **Verdict: agree.**
- **Evidence:** D1 is a debug-seed (`20261111`) mechanics run, 1 update/arm, `not_a_result`, `debug_replay_hash`, never compared to final; 3-seed is a separate registered run; B0-B is a separate downstream gate. §14 requires `validity_status == VALID AND control_status == M_CONTROL_PASS AND signal_status == EXPLORATORY_L_SIGNAL AND m_valid == true AND n_signal >= 15 AND tail_driven == false AND leakage/mode/metric pass AND artifact complete AND separate prereg/approval`. `n_signal ≥ 15` means exactly 15 (max), and tail true/NA blocks.
- **B0-B restated in v1.0.3 labels:** `validity_status=VALID`; `control_status=M_CONTROL_PASS`; `signal_status=EXPLORATORY_L_SIGNAL`; `m_valid=true`; `n_signal=15`; `tail_driven=false`; leakage/mode/metric pass; artifact complete; separate prereg and approval. `EXPLORATORY_L_SIGNAL` alone is not approval; `full_k_secondary`, P0, and `PA_RETENTION` are not evidence.
- **Next steps:** (1) keep D1/3-seed/B0-B on separate approvals; (2) assert `n_signal` exactly 15 (not `>=` with hidden 15→14 substitution); (3) record the B0-B predicate verbatim in the freeze manifest.

### Q13. Final verdict and freeze scope

- **Verdict: NARROW.**
- **Reason:** v1.0.3 genuinely closes the v1.0.2 blockers at the text/golden/schema level, and every digest and count I recomputed matches. It is very close to a single implementation authority. But it is not yet fully self-contained and not yet executable without ambiguity in phase-7 `K_d`/`baseline_ce`, canonical `null` ordering, the 12-key map shape, and the supplemental-vs-postrun digest distinction. These are must-fix text/schema items, not scientific changes, so STOP is too strong and unconditional CONTINUE is too generous.
- **Scope:**
  - v1.0.3 freeze: **after numbered ERRATA for MF-1..MF-10**.
  - Implementation + unit tests: **after freeze**; pure decision/hash/stats code only.
  - D0: **after implementation + unit tests**, 0 optimizer updates, ≤15 min.
  - D1: **not approved** this round.
  - 3-seed: **not approved**.
  - Prohibited: Phase 6 training, D1, 3-seed, B0-B/B1/B2/Stage C, test 163, P1, external APIs on P1, T5Gemma2 (D-108 STOP), post-result threshold/seed/donor/step/LR changes.
  - Max compute: **0 registered updates this round**; if later approved, registered cap 1,200 updates / 120 min hard abort, D0 ≤15 min, D1 ≤20 min (155 min envelope), no retry/extension.
  - test 163: **sealed**.
  - Is v1.0.3 a sufficient single implementation authority? **Not yet** — after MF-1..MF-10 ERRATA, yes.
- **Next steps:** (1) publish ERRATA; (2) re-run a focused review of the ERRATA only (no new science); (3) freeze by content SHA-256 and begin implementation/unit tests.

---

## 2. Final block

```text
최종 판정: NARROW
v1.0.3 freeze: numbered ERRATA(MF-1..MF-10) 후
구현+unit tests: freeze 후 (decision/hash/stats only)
D0: 구현+unit tests 후, 0 updates, <=15 min
D1: 미승인
3-seed: 미승인
금지 범위: Phase 6 training, D1, 3-seed, B0-B/B1/B2/Stage C, test 163, P1,
           external API on P1, T5Gemma2, post-result threshold/seed/donor/step/LR change
최대 compute: this round 0 registered updates; later 1,200 updates / 120 min hard abort
              + D0 <=15 min + D1 <=20 min (155 min envelope), no retry/extension
Must-fix (ranked): MF-1 phase-7 K_d/control slicing; MF-2 baseline_ce at K_d;
                   MF-3 donor_id null total order; MF-4 supplemental vs phase-7 digest;
                   MF-5 12-key map/control_digest schema; MF-6 P1 artifact registry;
                   MF-7 control fixture shape; MF-8 external module contracts;
                   MF-9 D0 labels/manifest timing; MF-10 per-arm 360/480 notation
v1.0.3 self-contained: 조건부 — measurement semantics 충분, external module contract 미기재
잘못된 전제: v1.0.3가 이미 fully self-contained/무수정 freeze 가능하다는 전제는 아님;
             단, 10 blocker가 실질적으로 닫힌 것은 맞음
```

## 3. Limits of this review

- No training or evaluation was run; no trained P/PA/L/M result was seen.
- Test 163 was not opened; P1 was not used.
- P0 values quoted (`train +3.7617 [1.8917,5.6050]`, `val +5.2375 [2.5013,8.0753]`) are descriptive P0 artifacts, not trained-arm evidence.
- Phase 6/B0-B/B1/B2/Stage C are **not** approved by this round.
- This report recommends no post-result threshold, seed, donor, step, or LR change.