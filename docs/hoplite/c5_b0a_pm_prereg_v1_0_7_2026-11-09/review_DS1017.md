# C5 Phase 6 P/M v1.0.7 — Independent External Review (DeepSeek V4.1 Flash 1017)

- Reviewer: Hoplite `deepseek-v4.1-flash-1017` (OpenRouter), reasoning high
- Distinct from `deepseek/deepseek-v4.1-flash`; this is a new, independent round. No other model's answer was reused.
- Review date: 2026-11-09
- Reviewed HEAD SHA: **`9613ef6`**
- Repository: `mandutt/unigem`, branch `main` (project `proj_2e8de5ed594f47c7b851f1d7c5b52c61`)
- Mode: read-only consultation. No training, no evaluation, no test-163 access, no P1 use, no subagents.

## Mandatory verification block

Reviewed commit:

```text
9613ef6
```

Verbatim §9.6.1 quote:

```text
K_d = min(K_M, len(real_prefix), len(donor_prefix))
```

## 0. Sync and provenance check

Commands run (read-only):

```text
git fetch origin          -> exit 0
git pull --ff-only origin main
  From https://github.com/mandutt/unigem
   * branch main -> FETCH_HEAD
  Already up to date.
```

Findings:

- After fetch/pull, `origin/main` HEAD is **`a826308f64301179cb54c7a87a208bf3f1bc6af4`** (`docs: add C5 P/M v1.0.7 review request`), not `9613ef6`.
- The initial workspace clone was depth-1 and did not contain `9613ef6`. `git fetch --deepen=100` succeeded; `9613ef6` then resolved as `docs: add Phase 6 v1.0.7 repair`, and is the **parent** of `a826308`.
- `git diff --name-status 9613ef6 HEAD` adds only review-harness files:
  - `docs/hoplite/c5_b0a_pm_prereg_v1_0_7_2026-11-09/dispatch.sh`
  - `.../prompt_ds1017.txt`, `.../prompt_glm.txt`, `.../prompt_sol.txt`, `.../watch_reviews.py`
  - `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_7_2026-11-09.md`
- No reviewed artifact (plan, template, golden, provenance, runner, tests) differs between `9613ef6` and current HEAD. Reviewing `9613ef6` therefore reviews the current artifact bytes.

Artifact hashes computed locally:

```text
m_cohort_preflight.json  3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af  (matches §0.4)
p1_usage.json            69af129a4f58f7400189c361ba2447f12e17d35f012d7a36c26efdf485a3a2dc
golden_vectors.json      7f5584f689bc2a9234596dee87c55c89d59b3f607b6040d1dc0b5c50fe2ede6f
plan_c5_..._v1_0_7.md    afa360989e15d0e8a32c086ed1939791e30b52217e0820d89f8950d0c300df4f
```

The preflight hash in the plan, the freeze template, and the actual file all agree.

## 1. Independently recomputed facts

Golden digests were recomputed from the JSON, not trusted:

| vector | computed | expected | result |
|---|---|---|---|
| `state` | `43ecb58e…d65712` | `43ecb58e…d65712` | match |
| `state.empty` | `e3b0c442…b855` | `e3b0c442…b855` | match |
| `replay_base` | `c43ea35c…f7851667` | `c43ea35c…f7851667` | match |
| `key_coverage_golden` | `8277a713…af7a20` | `8277a713…af7a20` | match |
| `control_manifest_golden` | `6b50c226…c1938` | `6b50c226…c1938` | match |

Control ordering recomputed: `control/F/20261108/M_NORM/doc_a` then `control/F/20261108/M_POS_MEAN` (ascending canonical name), matching the fixture note.

Arithmetic recomputed:

- Per-document per-arm-seed: `2 variants × 2 endpoints × 2 memory kinds = 8`.
- F/L: `15 × 8 = 120`; P/PA: `20 × 8 = 160`; per seed `120+120+160+160 = 560`.
- Registered: `560 × 3 = 1,680`; per arm across seeds `F=360, L=360, P=480, PA=480`.
- Common targets: `15 × (4 arms × 3 seeds × 8) = 15 × 96 = 1,440`.
- Native-only targets: `5 × (2 arms × 3 seeds × 8) = 5 × 48 = 240`.
- Phase 7: `15 × 5 × 2 × 2 × 2 = 600` per arm-seed.
- Preflight: `k_m_l=753`, `l_contributors_at_k=16`, `l_target_eligible_at_k=15`, `native_contributors_at_512=20`, `native_target_eligible_at_512=20`, `K=754 → 14`, `zero_margin=true`. All match the preflight file.

P0 recomputed from `p0_native_sanity.json`:

| split | mean Δcopy | CI | mean Δfull | positive docs | real copy CE |
|---|---:|---|---:|---:|---:|
| train | +3.7617 | [1.8917, 5.6050] | +3.5027 | 14/20 | 12.7022 |
| val | +5.2375 | [2.5013, 8.0753] | +5.2936 | 18/20 | 13.2352 |

- `source_max_length=256`; `mode=p0_sanity_no_training`; `test_split_used=false`.
- The `seeds_positive` field equals the document count (14/18), exactly the mislabel v1.0.7 retires.
- `ln(250100) ≈ 12.4296 < 12.7022 / 13.2352`: untrained real CE is above uniform, so P0 is a sensitivity check, not evidence of trained P/PA/L calibration.
- All 20 val per-doc records have non-null `real_ce_copy`; minimum copy coverage `0.7574`, so the `>=5` copy-token guard is satisfied on data already measured (the mask depends on passage/summary, not on P0's 256 source length).

Code facts:

- `runner/c5_pm_stats.py` does **not** exist (correct for "no code before freeze").
- `eval/tests/test_c5_b0_metric.py` contains 7 P0-era metric tests; no decision/M/stats/replay contract tests exist yet.
- `runner/c5_mt5_lora_b0.py:384` defines legacy `bootstrap_paired(..., seed=20261108)` and returns `"seeds_positive": int((arr > 0).sum())` (a document count). It is called at lines 220, 460, and 653.

---

## Q1. Six residual closures

- **판정: conditional**

| # | residual | status | evidence |
|---|---|---|---|
| 1 | §16.2 freeze paths | **closed** | §16.2 manifest is `..._v1_0_7_FREEZE.json`; `plan_path` is `docs/plan_c5_b0a_pm_prereg_v1_0_7.md`; template matches. |
| 2 | `T_proj` per-seed vs aggregate | **closed** | §11.5 defines the term as per-seed 120/160, adds `3 *` outside, and says "do not pass 360/480 into the term"; §13.5 adds `3 * sum(per-seed 120/160)`. |
| 3 | phase-7 `K_d <= K_M` | **closed** | §9.6.1 bounds `K_d` by `K_M` and asserts `1 <= K_d <= K_M` plus two length bounds; all four tensors are sliced to `K_d`. |
| 4 | `freeze_commit` / `manifest_commit` | **partial** | Both are defined and distinct, but the manifest schema contains `manifest_commit`, which cannot be known when the manifest is committed (see Q3). |
| 5 | key-coverage wording | **closed** | §12.3 says the 4-record fixture "is not the 600-record phase-7 domain"; phase 7 is numeric-only in §9.6.1 and the golden file. |
| 6 | legacy bootstrap assert | **partial** | Requirement is stated (§10.2, §13.5), but the assertion mechanism is unspecified and the legacy helper remains reachable through `evaluate_arm` (see Q7). |

- 다음 단계:
  1. Resolve the `manifest_commit` self-reference (MF-1).
  2. Specify the exact legacy-bootstrap assertion and the Phase 6 entrypoint call graph (MF-2).
  3. Recompute `plan_sha256` after any text patch; do not reuse `afa36098…`.

## Q2. Self-containedness

- **판정: conditional**

The decision, validity, control, statistics, replay, and freeze contracts are defined well enough to implement without reading v0.2.x/r3.x. Remaining external dependencies are explicit, not hidden:

- §17.1 makes `Adapter`, `make_labels`, `load_layer_cache`, `LoRALinear`, `attach_decoder_lora_mt5`, `native_memory`, and `repeated_4gram_rate` authoritative helpers. Their internals are external by design, but signatures are not fully restated; an implementer must read those files at the freeze commit. That is acceptable only because helper commit hashes are bound in the freeze manifest.
- §3.5 `L_COPY_SIGNAL` / `L_FULL_SIGNAL` use "paired L>F copy mean > 0" without stating the pairing cohort, endpoint alignment, or whether the paired difference is seed-averaged before the mean. §10.3 says "same retained IDs copy/full/L−F" but does not close §3.5.
- §9.2's builder pseudocode is sufficient for `M_POS_MEAN`, but it does not restate invalid/nonfinite behavior per contributor; §5.1 covers the aggregate (`||M_POS_MEAN||_F > 0`, per-target norms > 0).
- Everything else needed (cohorts, IDs, paths, tokenizer, masks, donors, hashes, seeds, caps) is in the document or in a bound artifact.

- 다음 단계:
  1. Add one sentence to §3.5 defining the paired L>F cohort and computation.
  2. Add a §17.1 sentence that helper signatures are read from the bound helper commits and that an incompatible signature is `NOT_ASSESSABLE`.
  3. Do not add new scientific choices; these are text-only clarifications.

## Q3. Freeze

- **판정: disagree (as written); conditional after text fix**

What is correct:

- `plan_path` in §16.2, the template, and the actual file all point to `v1_0_7`.
- `freeze_commit` = final plan commit; `manifest_commit` = `_FREEZE.json` commit; they are explicitly distinct.
- Freeze order (1) plan commit, (2) populate manifest, (3) manifest commit, (4) D0 records `freeze_manifest_sha256` is a sound sequence.
- `preflight_sha256` matches the file; `p1_manifest_sha256` and `golden_sha256` bind the right artifacts.

What blocks it:

- The §16.2 schema includes `"manifest_commit": "..."` **inside** `_FREEZE.json`. Under the stated order, the commit that adds the manifest is created after the file content is fixed, so the content cannot contain that commit's own SHA. If the file is committed with a placeholder and then updated with the real SHA in a second commit, the file at `manifest_commit` no longer matches the file that contains the value. The chain is self-referential and not executable as specified.
- The template and schema are close but not identical: the template carries `"status": "template"` and an extra `"note"` key, while §16.2 shows `"status": "frozen"` and no `note`. The template also omits `freeze_manifest_sha256` (correctly, since that is a D0 field, but the relationship should be stated).

Minimal repair (text/schema only):

```text
_FREEZE.json committed with manifest_commit = null
manifest_commit := the commit that adds that file
actual commit SHA and manifest byte-hash are recorded in D0
freeze_manifest_sha256 := SHA256 of the committed _FREEZE.json bytes
```

Alternatively define `manifest_commit` as the commit of the plan+manifest tree and record the manifest's byte hash separately, but do not put a commit's own SHA inside its content.

- 다음 단계:
  1. Change the schema so `manifest_commit` is null in the committed manifest, or remove it from the manifest and record it in D0.
  2. Delete the template-only `note`, or explicitly allow it in the schema.
  3. Recompute `plan_sha256` and `golden_sha256` after the text patch.

## Q4. T_proj

- **판정: agree**

- Per-seed term is 120/160; outer `3 *` yields 360/480 per arm; total `3 × 560 = 1,680`.
- `15×96 + 5×48 = 1,680`, and per-arm `F=360, L=360, P=480, PA=480` sum to 1,680.
- The v1.0.6 triple-count hazard is removed: §11.5 explicitly forbids passing 360/480 into the term, and §13.5 requires the arithmetic test.
- D1 uses the same per-seed 120/160, total 560, which is consistent.

- 다음 단계:
  1. Keep the §13.5 test as a hard precondition to D1/T_proj calculation.
  2. Add an assertion that the per-arm aggregate equals `3 × per-seed` before projection.

## Q5. Phase-7

- **판정: agree**

- `K_d = min(K_M, len(real_prefix), len(donor_prefix))` is present verbatim, with `1 <= K_d <= K_M` and two explicit length asserts.
- Slicing is defined for `M_POS_MEAN[:K_d]`, `M_NORM(t)[:K_d]`, `real_prefix[:K_d]`, `donor_prefix[:K_d]`; no renormalization; `M_NORM` remains the §9.3 K_M-scaled vector truncated at `K_d`.
- `baseline_ce` is recomputed in phase 7; phase-5 CE is explicitly forbidden as a substitute; `delta = baseline_ce - ce`.
- `600 = 15 × 5 × 2 × 2 × 2` per arm-seed, with `memory_kind ∈ {real, donor}` and `donor_id=0..4`.
- `K_M=753` (F/L) and `K_M=512` (P/PA) are consistent with preflight: F/L real prefix 753, P/PA native prefixes always 512, so `K_d=512` for P/PA and `K_d=min(753, donor h_len)` for F/L.
- The `1 <= K_d` assert is safe because `K_M ∈ {753,512}` and val20 prefixes are non-empty; no zero-length donor occurs in the preflight.

- 다음 단계:
  1. Add a unit test for `K_d` with a donor shorter than `K_M` and with `len(real) > len(donor)`.
  2. Add a test that `M_NORM(t)[:K_d]` is not renormalized.
  3. Keep phase-7 out of `m_valid` and every gate.

## Q6. Key coverage

- **판정: agree**

- `key_coverage_golden` is a 4-record fixture with `P/control`, `P/real`, `PA/donor`, `PA/real`, sorted by the canonical key with `donor_sort=-1` for null.
- §12.3 explicitly says it is not the 600-record phase-7 domain; §9.6.1 and `golden_vectors.json` both mark phase 7 as numeric-only.
- The 600-record phase-7 subset uses `{real, donor}` and `donor_id=0..4`; phase 5 uses `{control, real}` and `donor_id=null`; no conflation remains.
- The independently recomputed key-coverage digest matches `8277a713…af7a20`.

- 다음 단계:
  1. Add one test that a duplicate/missing key is rejected in the 4-record fixture.
  2. Add one test that the 600-record phase-7 domain produces no canonical hash.

## Q7. Legacy bootstrap

- **판정: disagree (insufficient as written)**

The requirement is correct but the test is not sufficient:

- The legacy function is real: `runner/c5_mt5_lora_b0.py:384` uses `seed=20261108` and returns `seeds_positive` as a document count.
- A test that only asserts `runner/c5_pm_stats.py` does not `import bootstrap_paired` does not prevent Phase 6 from calling `evaluate_arm()` (line 401), which calls the legacy `bootstrap_paired` at line 460. The same is true of `p0_eval_split()` (line 220) and `metric_smoke()` (line 653).
- The spec does not say whether the Phase 6 measurement path must avoid `evaluate_arm`. If implementers reuse it, the new stats module can be clean while the reported CIs still come from the legacy seed/mislabel.

Minimal repair (text + test plan only):

```text
- Phase 6 primary M/signal CIs must call runner/c5_pm_stats.py only.
- runner/c5_mt5_lora_b0.evaluate_arm must not be on the Phase 6 path,
  or its bootstrap dependency must be removed/parameterized.
- unit test: the Phase 6 entrypoint's import/call graph does not reach
  runner.c5_mt5_lora_b0.bootstrap_paired.
- behavioral test: seed=20261109; documents_positive is a document count;
  registered_seeds_positive is a seed-mean count; no "seeds_positive" key.
```

- 다음 단계:
  1. Add the call-graph/source assertion, not only an import check.
  2. State explicitly that `evaluate_arm` is not the Phase 6 statistics entrypoint.
  3. Keep the legacy function untouched for P0 historical reproduction.

## Q8. Hash / golden

- **판정: agree**

- Canonical JSON `sort_keys=true,separators=(',',':')` and SHA256 over the sorted record **array** are stated; per-record concatenation is explicitly forbidden.
- `hash_record` is the flat 8-field object; `baseline_ce` and `delta` are excluded.
- `donor_id` is canonical (`null` / `0..4`); `donor_sort` is internal (`-1` / `0..4`) and is not serialized or hashed.
- Sort order `(doc_id, arm, seed, variant, endpoint, memory_kind, donor_sort)` is consistent with the golden record order.
- All five golden digests were independently recomputed and match; control order is `M_NORM` before `M_POS_MEAN`.
- The control manifest golden is correctly labeled as a synthetic `[1,1]` framing fixture; the real `[K_M,512]` `control_digest` is postrun-only.

- 다음 단계:
  1. Add the permutation-invariance test over the flat 8-field records.
  2. Add a negative test that record-by-record concatenation does not equal the array digest.

## Q9. D0 / D1 / cap

- **판정: agree**

- D0: ≤4 configs, one 0-update config per arm, seed 20261111, `labels_computed:false`, `not_a_result:true`, ≤15 min, separate from the registered cap. Correct.
- D1: 4 arms × 1 debug seed × 1 update = 4 units, ≤20 min, `labels_computed:false` for decision/signal labels only (target-token labels for CE are computed), 8 phases, phase 5 total 560, phase 7 600/arm-seed, `not_a_result:true`, no registered seed. Correct.
- `T_proj ≤96 min`, `T_proj` finite/nonnegative, 120-min hard abort, no retry/extension. Correct.
- The prospective 1,204 updates = 1,200 registered + 4 D1; 155 min = 120 + 15 + 20. Correct.

One clarity issue: §11.1's table says "units 12, updates 1,200, wall 120 min" (registered only), while §11.6 says "1,204 updates / 155 min" (aggregate including D0/D1). Both are right, but the aggregate label should be explicit so a reader does not treat 155 as the registered wall cap.

- 다음 단계:
  1. Label §11.6 as the aggregate prospective ceiling and §11.1 as the registered-only cap.
  2. Keep D1 as a separate approval gate after the D0 report.
  3. Keep D0 projection forbidden.

## Q10. Remaining / new Must-fix

- **판정: agree (problems remain)**

Ranked:

1. **MF-1 (blocker):** §16.2 `manifest_commit` self-reference. The committed `_FREEZE.json` cannot contain the SHA of the commit that adds it. Text/schema repair required before freeze.
2. **MF-2 (high):** The legacy-bootstrap prohibition stops at `c5_pm_stats`; the Phase 6 path can still reach `runner.c5_mt5_lora_b0.bootstrap_paired` through `evaluate_arm`. Specify the entrypoint and add a call-graph/source assertion.
3. **MF-3 (medium):** §3.5 does not define the paired `L>F` cohort, endpoint alignment, or seed-averaging. §10.3 is not enough to make the predicate executable.
4. **MF-4 (low):** Template/schema mismatch: template `status: "template"` plus `note`; schema `status: "frozen"` without `note`. Remove the template-only key or allow it explicitly.
5. **MF-5 (low):** §11.1 vs §11.6 cap labels (registered 120 vs aggregate 155) should be disambiguated.

No new scientific choice is proposed. All five are text/schema/test-plan repairs; none changes seed, donor, threshold, step, LR, cohort, or K.

## Q11. Freeze / implementation approval

- **판정: conditional**

- Freeze v1.0.7 **as-is**: no. MF-1 is a genuine blocker, and MF-2/MF-3 must be closed as text/test-plan.
- Freeze after MF-1…MF-3 (and preferably MF-4/MF-5) are applied as numbered text/schema-only repairs, the plan is re-hashed, and a new freeze commit is created: yes.
- Implementation + unit tests: only **after** that freeze. Required tests before any D0:
  1. decision truth table (F1–F11, 9 L pairs, fixtures 16–18, tri-state ANDn/ORn);
  2. endpoint key set 1,680 (96/48 multiplicities) and duplicate/missing-key rejection;
  3. `3 * sum(per-seed 120/160)` and no 360/480 input;
  4. all five golden digests, array-vs-concatenation failure, permutation invariance, `donor_sort` non-serialization;
  5. phase-7 `K_d` with `len(donor) < K_M`, no M_NORM renormalization, 600 numeric-only;
  6. stats: seed 20261109, `documents_positive`, `registered_seeds_positive`, 2/3 registered, missing-seed NA, no legacy path;
  7. P1 strict flags and malformed → NA.
- D0 mechanics: only after freeze and unit tests, ≤4 configs, 0 updates, ≤15 min, seed 20261111.

This is an approval of protocol implementation mechanics only. It is not an approval of Phase 6 training, D1, 3-seed, or any downstream gate.

## Q12. B0-B / D1 / 3-seed boundary

- **판정: agree**

The v1.0.7 boundary is sufficient if restated in its own labels:

```text
B0-B requires all of:
  validity_status == VALID
  AND control_status == M_CONTROL_PASS
  AND signal_status == EXPLORATORY_L_SIGNAL
  AND m_valid == true
  AND n_signal >= 15                  # exactly 15, since max is 15
  AND tail_driven == false            # signal tail, top3_abs_share <= .50 and leave_top3_mean > 0
  AND leakage / decode-mode / metric checks pass
  AND artifact set complete
  AND a separate B0-B prereg + approval exists
```

- `tail_driven` is the signal tail only (`arm=L`, `endpoint=copy`, `control=shuffled donor`, `variant=NA`, 15 L-eligible docs); `tail_driven_M_POS_MEAN`/`tail_driven_M_NORM` are descriptive.
- `EXPLORATORY_L_SIGNAL` alone is not B0-B approval; `full_k_secondary`, P0, and `PA_RETENTION` are not evidence.
- D1 is a 1-update/arm debug run with no decision labels; 3-seed is a separate registered run; B0-B/B1/B2/Stage C are separate.

- 다음 단계:
  1. Keep the separate B0-B prereg/approval clause.
  2. Keep the 3-seed run blocked until D1 is reported.
  3. Do not let `M_CONTROL_PASS` or `m_valid=true` substitute for the B0-B gate.

## Q13. Final verdict

- **판정: NARROW**

```text
최종 판정: NARROW
v1.0.7 freeze: NO as-is; YES after MF-1..MF-3 text/schema/test-plan repairs and re-hash
구현+unit tests: CONDITIONAL (after freeze; contract tests only, no training)
D0: CONDITIONAL (after freeze + unit tests; ≤4 configs, 0 updates, ≤15 min, seed 20261111)
D1: NO (separate approval after D0 report)
3-seed: NO
금지 범위:
  - Phase 6 training/evaluation execution
  - test 163 access (sealed)
  - P1 use
  - T5Gemma2 reopening (D-108 STOP)
  - B0-B/B1/B2/Stage C auto-advance
  - post-result threshold/seed/donor/step/LR changes
  - single-checkpoint replay
  - direct debug-vs-final replay-hash comparison
  - any 753 training/generation requirement
최대 compute: no grant; prospective ceiling only ≤1,204 updates / 155 min
  (1,200 registered + 4 D1; D0 ≤15 min; D1 ≤20 min; registered hard abort 120 min; T_proj ≤96 min)
Must-fix (ranked): MF-1 manifest_commit self-reference; MF-2 legacy bootstrap reachable via evaluate_arm;
  MF-3 paired L>F definition; MF-4 template/schema note; MF-5 cap labels
v1.0.7 self-contained: YES for decision/validity/control/stats/replay/freeze contracts;
  PARTIAL for helper internals (bound by helper commits) and §3.5 paired L>F
잘못된 전제:
  - `9613ef6` is not current origin/main HEAD; HEAD is `a826308`, one commit later.
    The only difference is the review harness; reviewed artifact bytes are identical.
  - P0 is descriptive native-path sensitivity, not trained P/PA/L calibration.
  - test 163 is sealed and P1 is unused; no Phase 6 result exists.
```

## 2. Wrong premises / limitations

- The review request says the basis is `9613ef6`; `origin/main` has advanced to `a826308`. I verified the artifact bytes are unchanged across that step and reviewed `9613ef6` as required. No reviewed artifact drift was found.
- I could not run the repo's Python tests because the environment has no `numpy`/`torch` in the default interpreter; this is irrelevant to a text review and no test execution was requested. Golden digests were recomputed with the standard library only.
- No training, evaluation, generation, test-163 read, or P1 read was performed.
- This report is consultation only. It does not modify the plan, template, golden vectors, provenance files, runner, or tests, and it does not approve Phase 6/B0-B/B1/B2/Stage C.
