# C5 Phase 6 P/M Prereg v1.0.4 — Independent External Review

- Reviewer: **Hoplite `deepseek-v4.1-flash-1017`** (OpenRouter route), reasoning **high**.
  This route is distinct from `deepseek/deepseek-v4.1-flash`; the repository cannot prove
  model distinctness, so this report relies on **nothing** from the v1.0.3 DeepSeek answer.
  Every digest, count and statistic below was recomputed in this run from the frozen files.
- Review round: **v1.0.4**, new independent round (consultation only).
- Review basis: `origin/main` HEAD **`0bfee85d20dd0017fe6f07f2e8939ff4c7ccf203`**
  (`0bfee85 docs: add C5 P/M v1.0.4 review request`).
- Request: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_4_2026-11-09.md`
- Target: `docs/plan_c5_b0a_pm_prereg_v1_0_4.md` (1,691 lines, 1,364 non-empty)
- Golden: `docs/hoplite/c5_b0a_pm_prereg_v1_0_4_2026-11-09/golden_vectors.json`
- Mode: **read-only consultation**. No training, no evaluation, test 163 not opened, P1 not
  used, no external API on P1, no subagents/other LLMs. Only write: this file.

## 0. Synchronization

```text
git fetch origin                       -> ok (no error)
git pull --ff-only origin main         -> "Already up to date."
git rev-parse HEAD                     -> 0bfee85d20dd0017fe6f07f2e8939ff4c7ccf203
git log -1                             -> 0bfee85 2026-11-09 17:53:24 +0900 docs: add C5 P/M v1.0.4 review request
```

- The request cites basis HEAD `f82b47d`; that is the **parent** commit
  (`f82b47d docs: add Phase 6 v1.0.4 repair`). `git fetch --deepen=10` confirms the chain
  `0bfee85 -> f82b47d -> e1a995d -> ...`. `0bfee85` only adds the review-request document, so
  every reviewed file is byte-identical between `f82b47d` and `0bfee85`.
- Working tree clean before review; no repository mutation was performed other than this file.

## 1. Independent recomputation

Performed with Python `json` / `hashlib` / `struct` only (no model, no data forward, no P1):

| item | my computed value | artifact | result |
|---|---|---|---|
| preflight content SHA-256 | `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` | §0.4 | **match** |
| state frame `43ecb…` | `43ecb58e197d5789df0a9dbbc67beba11538b8063c3da8ac46f96e1e95d65712` | §12.3 | **match** |
| empty state | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | §12.3 | **match** |
| replay base (flat 8-field, canonical JSON) | `c43ea35c46c51a0e82cebe5764a989d1b67012b2690246a0f89a94dff7851667` | §12.3 | **match** |
| replay supplemental (ascending key) | `8277a713fd52b2ba8c5c3c859c83fd78593aa5a381f8640448e2128a97af7a20` | §12.3 | **match** |
| control digest, frames **sorted by canonical name** | `6b50c226ecc402323787bd25b20e57fe57376caeb925c040b57985ccc0ec1938` | §12.3 | **match** |
| control digest, fixture **listing** order | `531ba0ad3ae6455af60411c678c5ab3686a856e00ed35460f1ee6de33a03bd68` | — | *not normative* |
| nested `{key, ce}` projection (the v1.0.3 defect) | `33c945a2f858dddd9cd466b578bc4c81fde94b32c1b3b2bf83ff2edf6e0ca62c` | D-137 | confirms the flat projection is **material** |

Notes on the ordering question, because the v1.0.3 synthesis mislabels it:
canonical name order is `control/F/20261108/M_NORM/doc_a` **before**
`control/F/20261108/M_POS_MEAN` (`N` < `P`). Sorting frames by that name gives `6b50c226…`,
i.e. the golden **is** the name-ascending digest; `531ba0ad…` is the listing-order artifact.
There is **no defect here**, and §12.1/§12.3/the golden agree.

Arithmetic recomputed:

| quantity | derivation | result |
|---|---|---|
| per arm-seed phase 5 (F/L) | 15 × 2 variants × 2 endpoints × 2 memory kinds | **120** |
| per arm-seed phase 5 (P/PA) | 20 × 2 × 2 × 2 | **160** |
| phase-5 across 4 arms (D1) | 2×120 + 2×160 | **560** |
| per arm across 3 seeds | F 360, L 360, P 480, PA 480 | **1,680** |
| common target appearances | 4 arms × 3 seeds × 8 cells | **96** |
| native-only appearances | 2 arms × 3 seeds × 8 cells | **48** |
| exact endpoint set | 15×96 + 5×48 | **1,680** |
| phase-7 diagnostic per arm-seed | 15 × 5 donors × 2 × 2 × 2 | **600** |
| control manifest footprint | (16×753 + 16×753 + 21×512 + 21×512)×512×4 B ×3 seeds | ≈ **267 MiB ≈ 0.3 GB** |

Preflight / split consistency (all verified against `m_cohort_preflight.json` and
`reports/provenance/C5_clean/splits.json`):

- `common_ids` = 15; `l_target_eligible_at_k` = 15; `l_contributors_at_k` = 16;
  `native_contributors_at_512` = 20; `k_m_l` 753; `k_m_native` 512; `common_ok` true.
- val `h_len ≥ 753` = 15/20; `k_selection.next_k_target_eligible` = 14 at K=754;
  `full_k_secondary` = 11/20 (correctly marked secondary); `cohort_label` =
  `M_CONTROL_PREFIX753_COHORT15`.
- `train20_ids == splits.train[:20]` **true**; `val20_ids == splits.val[5:25]` **true**;
  split sizes 1,293 / 161 / 163; **no test ID inside the allowlist**; `test_split_used`
  false; `no_model_forward` true; `data_only` true.

P0 recomputed from `p0_native_sanity.json` (descriptive only, **never** trained-arm evidence):

| split | mean Δcopy | 95% CI | mean Δfull | docs Δ>0 | median | top3 signed (by abs) | top3 abs |
|---|---:|---|---:|---:|---:|---:|---:|
| train | +3.76173 | [1.89169, 5.60496] | +3.50274 | 14/20 | 4.068 | .4222 | .34096 |
| val | +5.23746 | [2.50132, 8.07527] | +5.29365 | 18/20 | 2.9739 | **.4862** | **.43355** |

val common-15 subset: absolute top3 share **.45478** (doc says .455). Real copy CE
train 12.7022 / val 13.2352, both above `ln|V|` = 12.4297 for the 250,112-token mT5 vocab.
Copy coverage .835/.825; `copy_guard_failed` false. All numbers in §3 of the request reproduce.

External module contracts (§17.1) checked against the cited source files:

| symbol | file | observed | verdict |
|---|---|---|---|
| `Adapter` | `c5_mt5_layer_probe.py:52` | Linear/GELU/Linear/LayerNorm, `forward(x)`, default 512->512 | **match** |
| `make_labels` | `c5_mt5_layer_probe.py:79` | tokenizer labels, `truncation`, `max_length`, returns `[1,L]` | **match** |
| `load_layer_cache` | `c5_mt5_layer_probe.py:66` | `(split, dir)`, `{id: {h, length}}`, h trimmed to `length` | **match** |
| `LoRALinear` | `c5_a1_lora.py:45` | A kaiming_uniform(a=sqrt(5)), B zeros, `scale=alpha/r`, dropout | **match** |
| `attach_decoder_lora_mt5` | `c5_mt5_lora_b0.py:52` | r=8, alpha=16, 64 modules, raises on !=64 | **match** |
| `native_memory` | `c5_mt5_lora_b0.py:135` | native encoder hidden state, no_grad | **match** |
| `repeated_4gram_rate` | `c5_a2null_eval.py:80` | whitespace-stripped 4-gram repetition | **match** |

Could not be verified (stated as a limit, not a defect):

- `eval/tests/test_c5_b0_metric.py` is guarded by
  `@unittest.skipUnless(MODEL.exists(), ...)` and `data/models/mt5-small`,
  `data/external/f5_pairs_v3_clean.jsonl`, `data/wave2c/eg2_native_layer19/layer19` are all
  absent from this checkout, so **no test was executed**. This run inspected the file
  statically and checked its imports against the runner symbols (all present:
  `token_losses`, `shifted_copy_mask`, `copy_ce`, `generation_record`,
  `attach_decoder_lora_mt5`, `make_adapter`, `set_training_mode`, `native_donors_for`,
  `p0_sanity_decision`, `EXPECTED_LORA_MODULES`).

---

## 2. Q1–Q13

### Q1. Are the 10 v1.0.3 residuals closed?

- **Verdict: agree — all 10 asks are closed at the text/schema level**, but 3 follow-on gaps
  remain (MF-1..MF-3 below) that keep v1.0.4 from being a self-contained implementation authority.

| # | residual | status | evidence |
|---|---|---|---|
| 1 | phase-7 `K_d` / `baseline_ce` | **closed** | §9.6.1 L1080-1115: explicit bounds, `control_variant[:K_d]`, `baseline_ce` recomputed in phase 7, phase-5 K_M CE reuse forbidden. Residual audit gap = MF-2 |
| 2 | null total order | **closed** | §12.2 L1430-1432: internal `donor_sort=-1`, serialized `donor_id=null`, ascending `(doc_id, arm, seed, variant, endpoint, memory_kind, donor_sort)` |
| 3 | flat 8-field hash | **closed** | §12.2 L1434-1443 + §12.3 L1463-1475; I reproduced `c43ea…`; nested projection gives `33c945a2…`, so the rule is material. Naming residue = MF-5 |
| 4 | 12-key checkpoint map | **closed** | §12.1 L1363-1384, §11.4 L1303-1306, §17.2; 4 arms × 3 registered seeds, per-unit paths, no single-checkpoint replay |
| 5 | P1 frozen / postrun | **closed (ask met)** | §1.5 L111-117 + `p1_usage.json` (sha256 `69af129a…`) + `p1_usage.postrun.json` (`status: not_run`) + registry. Follow-on gap = MF-1/MF-6 |
| 6 | control fixture shape | **closed** | golden `control_manifest_golden.scope` declares synthetic `[1,1]`; real `[K_M,512]` digest is postrun-only (§12.3 L1489-1490); digest = name-ascending, verified |
| 7 | external module contracts | **closed** | §17.1 table verified against 4 source modules (see §1 above); commit hashes deferred to the freeze manifest (=MF-1) |
| 8 | D0 labels / timing | **closed** | §11.2 L1247-1259 (4 configs, seed 20261111, `labels_computed:false`, `not_a_result:true`); §11.3 L1267-1269 scopes the flag to decision labels and fixes manifest timing |
| 9 | per-arm notation | **closed** | §11.5 L1329-1331: 120/160 per unit, 360/360/480/480 per arm, 1,680 total; 560/600 verified |
| 10 | dtype / fixture order / note | **closed** | `dtype_str=<f4` (§12.1 L1380); `note` unknown key allowed (§1.5 L116); fixture order actually correct (name-asc). Wording nit = MF-7 |

**Next steps:** (1) register MF-1..MF-3 as numbered ERRATA; (2) do not reopen any closed item.

### Q2. Is v1.0.4 self-contained?

- **Verdict: conditional.** The measurement semantics, predicates, statistic definitions and
  hash/golden rules are sufficient on their own. What is missing is operational, not scientific.
- **Evidence.** Normative dependencies outside the document:
  1. **Freeze manifest schema** — `p1_manifest_sha256` (§4.0 L476, §1.5 L111), "freeze commit
     hash / freeze content SHA-256" (§16.2 L1638-1639) and "helper commit hashes are recorded
     in the freeze manifest" (§17.1 L1675) are all referenced, but no path, JSON shape or
     required field list exists. `assay_path_ok` is **unevaluable** without it (MF-1).
  2. Preflight **field names** are not specified; implementers must read
     `m_cohort_preflight.json` (acceptable — §2.6 makes it the authority — but it is an
     external artifact, not a schema in the text).
  3. §15 traceability cites v1.0.1 §9.1/§9.5/§9.6/§10.2/§11.4/§2.3. It is marked
     "historical only; not implementation authority", so this is a discipline risk rather than
     a contract gap.
  4. D1 artifact names (`debug_replay_hash`, `debug_checkpoint_hash`) are named but their file
     names are not; §17.2 lists only postrun artifacts.
  5. The hash **container** (a JSON array of records, not NDJSON) is only implied by the golden.
- **Next steps:** (1) add a freeze-manifest section with a field list; (2) state the hash
  container explicitly; (3) name the D1 artifacts.

### Q3. Is phase-7 measurement executable, and is phase-5 CE reuse eliminated?

- **Verdict: agree.**
- **Evidence.** `K_d = min(len(real_prefix), len(donor_prefix))` with `1 <= K_d <= min(...)` is
  executable for every arm: F/L prefixes are `A(h)[:753]` (so `K_d <= 753`, and it can be
  `< 753` when the nearest donor has `h_len < 753` — allowed, since `M_POS_MEAN[:K_d]` and
  `M_NORM(t)[:K_d]` are row slices of a `[K_M,512]` tensor); P/PA prefixes are `[:512]` and
  `K_d = 512` for all 20 val docs (preflight `val_native_lengths` = 512 ×20).
  `ce = raw CE(record tensor)`, `baseline_ce = CE(control_variant[:K_d], target, endpoint)`
  recomputed in phase 7, `delta = baseline_ce - ce`, 600 records/arm-seed = 15×5×2×2×2.
  Reuse is explicitly forbidden (L1109) and the baseline is variant-selected (L1110), so the
  same raw `ce` cannot silently inherit a phase-5 K_M baseline.
- **Residual:** see MF-2 — `baseline_ce`/`delta` are outside the hash and no numeric replay
  comparison is specified for them.
- **Next steps:** (1) add a phase-7 numeric replay clause for `baseline_ce`/`delta` at the
  existing `atol=1e-5, rtol=1e-4`; (2) state that `K_d < K_M` is legal for F/L donors.

### Q4. Is the canonical hash consistent with the base/supplemental goldens?

- **Verdict: agree.**
- **Evidence.** Flat 8-field records `{arm, ce, doc_id, donor_id, endpoint, memory_kind, seed,
  variant}`, `sort_keys=true`, `separators=(',',':')`, SHA-256 of UTF-8 bytes reproduce
  `c43ea35c…`. The nested `{key, ce}` form (the v1.0.3 error) yields `33c945a2…`, matching
  D-137's cited wrong digest, so the flat projection genuinely changes the wire bytes.
  The supplemental four records are already in ascending canonical-key order and reproduce
  `8277a713…`; `baseline_ce`/`delta` exclusion is stated twice (§9.6.1 L1114, §12.2 L1438).
  With `donor_sort = -1` for null, the total order is well defined and matches the goldens.
- **Residual:** the golden's own `ordering` string says `donor_id`, not `donor_sort` (MF-7) —
  an implementer copying it would compare `None` against `int` and fail.
- **Next steps:** (1) align the golden ordering note; (2) keep the goldens as independent
  constants (already stated, §12.3 L1477).

### Q5. 12-key map, per-unit 120/160, 360/480, 1,680?

- **Verdict: agree.**
- **Evidence.** 12 keys = 4 arms × {20261108, 20261109, 20261110}; value `"sha256:..."`;
  paths `checkpoints/{arm}/{seed}.pt`; replay loads each unit and has no single-checkpoint
  path (§11.4 L1303-1306, §12.1 L1384). Arithmetic: 120 (F/L) / 160 (P/PA) per unit;
  360/360/480/480 per arm; 1,680 total = 15×96 + 5×48; common target 96, native-only 48.
  The existing runner has **no checkpoint writer**, which is expected for a prereg — it is
  cited only as the LoRA/native-memory contract source.
- **Residual:** the D1 debug run produces a 4-key map (4 arms × seed 20261111) whose file name
  is undefined; `final_checkpoint_hash.json` is postrun-only by §12.1.
- **Next steps:** (1) name the D1 map; (2) add a unit test asserting exactly 12 keys and the
  96/48 appearance counts.

### Q6. Is P1 frozen/postrun fail-closed and auditable?

- **Verdict: conditional.**
- **Evidence.** The split is sound: frozen `p1_usage.json` (currently sha256 `69af129a…`,
  `p1_used:false`, `test_split_read:false`, `checked_artifacts:[]`, one allowed `note` key),
  separate `p1_usage.postrun.json` (`status:"not_run"`), registry
  `phase6_artifact_registry.json` (sha256 `90a7822d…`), `assay_path_ok` on the frozen hash,
  postrun audit-only. Missing/malformed goes to `NA`, known-use to `false`, so the fail-closed
  direction is right. Test 163 stays sealed and the allowlist rule avoids scanning it.
- **Gaps.** (a) "contradictory known-use goes to `false`" has **no operational definition** —
  e.g. `p1_used:false` together with a `checked_artifacts` entry outside the allowlist, or a
  postrun inventory listing P1 artifacts, is not classified. (b) Nothing requires the postrun
  inventory to be complete or names its writer. (c) The registry enumerates only 5 patterns and
  omits the per-unit control tensors and phase-7 records that `checked_artifacts` must cover.
- **Next steps:** (1) define contradiction explicitly; (2) require postrun
  `checked_artifacts` to cover `registry.expected`; (3) extend the registry to per-unit artifacts.

### Q7. Control tensors?

- **Verdict: agree.**
- **Evidence.** Synthetic `[1,1]` framing fixture declared as such; real tensors `[K_M,512]`,
  `dtype=<f4`; NPZ key `tensor`; canonical names
  `control/{arm}/{seed}/M_POS_MEAN` and `control/{arm}/{seed}/M_NORM/{target_id}`;
  `target_id="__shared__"` for the shared mean; `sha256` over the tensor frame rather than ZIP
  bytes; `control_digest` over name-sorted frames = `6b50c226…` (reproduced); footprint
  ≈267 MiB, consistent with "~0.3 GB"; real digest is postrun-only, so there is deliberately
  no pre-registered constant for it.
- **Nit.** The fixture exercises only 2 tiny frames; a framing bug that appears only at
  `[753,512]` (u32 shape word, u64 nbytes) would surface only postrun. A second synthetic
  large-shape fixture (e.g. zeros `[753,512]`) is cheap and would pin shape encoding.
- **Next steps:** (1) optional large-shape fixture; (2) state that `control_digest` includes
  the shared `M_POS_MEAN` frame.

### Q8. External module contracts?

- **Verdict: agree.**
- **Evidence.** All seven symbols exist and their observed behavior matches §17.1 (table in
  §1 above). §2.5.4 supplies the adapter architecture and RNG order that §17.1 abbreviates, so
  the contract is sufficient when read with §2.5.
- **Residual.** "missing helper goes to `NOT_ASSESSABLE`" is a decision value, not an import
  policy; implementers need an explicit "import/AttributeError maps to NA, do not guess" rule,
  and §17.1's freeze-commit hashes depend on the undefined freeze manifest (MF-1).
- **Next steps:** (1) state the NA-on-missing-import convention; (2) record helper hashes in
  the freeze manifest.

### Q9. D0 / D1 / cap?

- **Verdict: agree.**
- **Evidence.** D0: 0 optimizer updates, <=4 configs (one per arm), seed 20261111, <=15 min,
  `labels_computed:false`, `not_a_result:true`, separate from the registered cap; h-length
  assert for F/L cache length and P/PA native = 512. D1: 4 arms × 1 debug seed × 1 update,
  <=20 min, 8 phases, phase-5 560 and phase-7 600/arm-seed. T_proj over 3 seeds <=96 min with a
  120-min hard abort, no retry/extension; prospective envelope 1,204 updates / 155 min
  = 1,200 registered + 4 D1. All arithmetic checks.
- **Nit.** D0 is said to materialize the retained control manifest (§11.2 L1258) while §11.3
  L1269 says it is built after step0 in D1; both are the pre-update state, so clarify which
  run owns the retained copy.
- **Next steps:** (1) state the owning run for the retained manifest; (2) keep D0
  projection-free.

### Q10. What must still be fixed?

- **Verdict: conditional — no new scientific blocker, but 3 material gaps and 5 minor ones.**
- The three items the request highlights:
  - **`baseline_ce` separated from the phase-7 hash:** yes (§9.6.1 L1114, §12.2 L1438), **but**
    nothing then verifies `baseline_ce`/`delta` at replay (MF-2).
  - **12-key map vs the real runner:** the map matches the spec; the runner has no checkpoint
    writer yet, which is correct for a prereg (not a defect).
  - **P1 frozen/postrun auditability:** structurally good; blocked by the undefined freeze
    manifest (MF-1) and the undefined contradiction rule (MF-6).
- **Next steps:** see the ranked list in §3.

### Q11. Freeze + implementation + unit tests + D0?

- **Verdict: conditional — after numbered ERRATA for MF-1..MF-3 (text/schema only).**
- **Evidence.** Nothing in the remaining gaps requires a new scientific choice: no threshold,
  seed, donor, step, LR, cohort or predicate changes. They are schema/naming/definition items.
  Freeze cannot precede MF-1 because `assay_path_ok` is part of the D0 report and cannot be
  evaluated without a freeze manifest.
- **Required tests before implementation is considered done** (all in §13, none present yet in
  `eval/tests/test_c5_b0_metric.py`): (1) pure decision function — F1-F11, the 9 L pairs,
  fixtures 16-18, every label reachable; (2) hash goldens ×5 plus permutation/duplicate/
  missing-key and null-total-order tests; (3) 12-key map plus 120/160, 360/480 and the exact
  1,680 key set with 96/48 appearances; (4) phase-7 `K_d` slicing, `baseline_ce` recomputation
  and `delta`; (5) P1 malformed goes to NA and contradictory goes to false; (6) stats — seed
  20261109, `n_boot=1000`, seed-average-before-bootstrap, tail tie rule and `.50` threshold,
  `n<4` goes to NA.
- **Next steps:** (1) ERRATA; (2) focused ERRATA review; (3) freeze by content SHA-256;
  (4) implementation + unit tests; (5) D0.

### Q12. B0-B / D1 / 3-seed boundaries

- **Verdict: agree.**
- **Restated B0-B predicate on v1.0.4 labels:** `validity_status == VALID` AND
  `control_status == M_CONTROL_PASS` AND `signal_status == EXPLORATORY_L_SIGNAL` AND
  `m_valid == true` AND `n_signal == 15` AND `tail_driven == false` (signal tail: L / copy /
  shuffled-donor / 15 L-eligible, `top3_abs_share <= .50` and `leave_top3_mean > 0`) AND
  leakage/mode/metric pass AND artifact complete AND a separate prereg/approval. Note that with
  `n_signal = 15` the ">=15" clause is exactly 15, `EXPLORATORY_L_SIGNAL` already implies
  `m_pass_l = true`, and `tail_driven` true or NA blocks.
- **Boundary.** D1 (4 units, 1 update, debug seed) does not produce decision labels, does not
  pool with the 3-seed run, and `debug_replay_hash` must never be compared with
  `final_replay_hash`; 3-seed requires D1; B0-B/B1/B2/Stage C remain separate and unapproved.
- **Next steps:** (1) restate the predicate verbatim in the freeze manifest; (2) keep the
  debug/final hash separation in the test matrix (already §13.4).

### Q13. Final verdict and freeze scope

- **NARROW** (see §4). Not STOP: no scientific choice must change and all 10 v1.0.3 asks are
  closed. Not CONTINUE: three material gaps would let a conforming implementation produce an
  unauditable D0 report or mislabeled statistics.

---

## 3. Must-fix (ranked)

| rank | id | severity | item | required change |
|---|---|---|---|---|
| 1 | MF-1 | medium (blocks D0) | Freeze manifest is referenced (`p1_manifest_sha256` §4.0 L476, §1.5 L111; freeze commit/content SHA §16.2; helper commit hashes §17.1) but never defined | Add path + JSON schema (plan path/sha256, `p1_manifest_sha256`, golden sha256, preflight sha256, helper module commit hashes, registered seeds) |
| 2 | MF-2 | medium | Phase-7 `baseline_ce`/`delta` are hash-excluded and unreplayed; §11.4 step 5 only checks the `ce`-only supplemental digest, so a corrupted baseline/delta passes | Add numeric replay of `baseline_ce` and `delta` at `atol=1e-5, rtol=1e-4`; keep them out of the hash |
| 3 | MF-3 | medium-low | `seeds_positive` is both required (§10.2 L1173, §13.3 L1531) and forbidden (§13.5 L1564 "no stale seeds_positive"); the P0 helper returns the same name meaning **document** count | Rename the new module field (e.g. `registered_seeds_positive`) and state the P0 field is a doc count |
| 4 | MF-4 | low | "supplemental replay digest" (§11.4 L1308) conflates a 4-record key-coverage golden (mixes phase-5 `control` records with a phase-7 `donor` record) with the 600-record phase-7 domain; no phase-7 digest is defined | Rename to `key_coverage_golden`; if a phase-7 digest is wanted, define its domain/projection, else verify numerically |
| 5 | MF-5 | low | Two "record" schemas: §9.6.1 L1113 keeps nested `{key, ce, baseline_ce, delta}`, §12.2 L1434 mandates flat | Label `stored_record` vs `hash_record`, or make the stored record flat |
| 6 | MF-6 | low | P1 contradiction undefined; postrun completeness unstated; registry omits per-unit tensors/phase-7 artifacts | Define contradiction; require postrun to cover the registry; extend the registry |
| 7 | MF-7 | low | golden `replay_supplemental.ordering` says `donor_id`; §12.2 says internal `donor_sort` | Align wording to `donor_sort` (null to -1) |
| 8 | MF-8 | cosmetic | `MARGINAL_SIGNAL_COHORT` defined at L725 but never used in dispatch (and names the maximum cohort "marginal"); `C5_STATUS` says 1,690 lines vs 1,691; canonical name prefix `control/` vs path prefix `control_manifest/` | Drop or use the flag; fix the line count; note the prefix difference |

Not must-fix, recommended: a synthetic `[753,512]` control fixture to pin large-shape framing
before the postrun-only real digest exists.

---

## 4. Final block

```text
최종 판정: NARROW
v1.0.4 freeze: numbered ERRATA(MF-1..MF-3 필수, MF-4..MF-8 권고) 후
구현+unit tests: freeze 후, decision/hash/stats/M-builder 계약만
D0: 구현+unit tests 후, 4 configs, 0 updates, seed 20261111, <=15 min
D1: 미승인
3-seed: 미승인
금지 범위: Phase 6 training, D1, 3-seed, B0-B/B1/B2/Stage C, test 163, P1,
           external API on P1, T5Gemma2 (D-108 STOP),
           post-result threshold/seed/donor/step/LR 변경
최대 compute: 이번 라운드 0 updates / 0 GPU. 승인 후에도 D0 <=15 min,
              registered cap 1,200 updates / 120 min hard abort,
              D1 <=20 min (155 min envelope), no retry/extension
Must-fix (ranked): MF-1 freeze manifest schema; MF-2 phase-7 baseline_ce/delta replay;
                   MF-3 seeds_positive 명명 충돌; MF-4 supplemental vs phase-7 digest;
                   MF-5 stored vs hash record; MF-6 P1 contradiction/registry;
                   MF-7 donor_sort ordering note; MF-8 표기 정리
v1.0.4 self-contained: 조건부 — measurement/hash/stats는 충분, freeze manifest·P1 schema만 미정
잘못된 전제: (a) v1.0.4가 완전한 단일 구현 권위라는 전제는 아직 아님;
             (b) control digest 순서는 결함이 아님 — 6b50c226…이 name-asc로 맞고
                 531ba0ad…가 listing-order artifact (v1.0.3 synthesis의 표기가 반대);
             (c) P0는 descriptive이며 trained P/PA/L 증거가 아님
```

Approval note: this round does **not** approve Phase 6 execution, B0-B, B1, B2 or Stage C, and
does not change any threshold, seed, donor, step or LR.

## 5. Limits of this review

- No training or evaluation was run; no trained P/PA/M/L result exists and none is claimed.
- Test 163 was not opened; P1 was not used; no external API was called on any corpus.
- P0 values quoted are descriptive native-path artifacts (`source_max_length=256`, M path 512),
  not trained-arm evidence.
- Unit tests could not be executed because the model/data assets are absent from this checkout;
  the test file was reviewed statically only.
- Digests and counts were recomputed from the frozen files with Python `json`/`hashlib`/`struct`;
  no golden constant was regenerated into any artifact.
- This report is a consultation, not an approval, and recommends no post-result change.