# C5 Phase 6 P/M v1.0.8 — Same-Thread Continuation Review (DeepSeek V4.1 Flash 1017)

- Reviewer: Hoplite `deepseek-v4.1-flash-1017` (OpenRouter), reasoning high
- Round: v1.0.8, same consultation thread as my v1.0.7 review. No other model's answer reused; no subagents.
- Review date: 2026-11-09
- Reviewed HEAD SHA: **`38a2a81`**
- Repository: `mandutt/unigem`, branch `main` (project `proj_2e8de5ed594f47c7b851f1d7c5b52c61`)
- Mode: read-only consultation. No training, no evaluation, no test-163 access, no P1 use.
- Scope: closure of the seven v1.0.7 residuals only. Items already closed in v1.0.7 (§16.2 path, T_proj per-seed, `K_d <= K_M`, key-coverage 4-record vs 600, golden/preflight hashes) were not re-reviewed.

## Mandatory verification

Reviewed commit:

```text
38a2a81
```

Verbatim quote:

```text
manifest_commit is always null inside _FREEZE.json
```

Source line it is taken from, with its markup (§16.2):

```text
- `manifest_commit` is always `null` inside `_FREEZE.json`; a file cannot contain the SHA of the commit that adds it.
```

## 0. Sync and provenance

```text
git fetch origin          -> success
git pull --ff-only origin main
  Updating a826308..d4e9dfa
  head = d4e9dfaefa0e25696864bd2623a57283d7f7d3aa
```

- The first pull attempt aborted: upstream had committed `docs/hoplite/c5_b0a_pm_prereg_v1_0_7_2026-11-09/review_DS1017.md`, colliding with my untracked v1.0.7 report. I backed mine up to `/tmp`, removed the untracked copy, and the pull then succeeded. The committed copy is byte-identical to mine except a trailing newline, so the v1.0.7 report was preserved verbatim.
- `git diff --name-status 38a2a81 d4e9dfa` adds only review-harness files (`dispatch_fup.sh`, `fup_ds1017.txt`, `fup_glm.txt`, `fup_sol.txt`, `threads.json`, `watch_reviews.py`, the v1.0.8 request). No plan, template, golden, provenance, runner, or test file differs between `38a2a81` and current HEAD, so reviewing `38a2a81` reviews the current artifact bytes.
- `working tree` is clean after the pull.

Artifact hashes:

```text
plan_c5_..._v1_0_8.md     50d4bf218ec93b590c3866ce987a570b9ed3844601f07dfe249a6afde38345ca
golden_vectors.json       0aa8284cbe1b4b4c4524fb682c10bb5f37bd73016800130209df959b73517e32
m_cohort_preflight.json   3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af  (matches §0.4)
p1_usage.json             69af129a4f58f7400189c361ba2447f12e17d35f012d7a36c26efdf485a3a2dc
```

All five golden digests recomputed independently from the JSON and match: `state 43ecb58e…d65712`, `empty e3b0c442…b855`, `replay_base c43ea35c…f7851667`, `key_coverage 8277a713…af7a20`, `control 6b50c226…c1938`; control order is still `M_NORM` before `M_POS_MEAN`. `phase7_diagnostic` remains `600/arm-seed`, numeric-only.

The v1.0.8 golden file is functionally the v1.0.7 fixture with `spec`/`created` updated. That is expected for a text-only repair round and does not by itself invalidate the vectors.

---

## Q1. Seven residual closures

- **판정: conditional (6 closed, 1 partial)**

| # | residual | status | evidence |
|---|---|---|---|
| 1 | `manifest_commit` self-reference | **closed** | §16.2 schema now has `"manifest_commit": null`; the actual SHA moves to `reports/provenance/C5_b0a/freeze_manifest_commit.txt`; D0 records both values. No file contains its own commit SHA. |
| 2 | legacy `bootstrap_paired` reachability | **partial** | §17.3 defines `runner/c5_pm_phase6.py` as the only entrypoint, forbids the legacy import, requires the `evaluate_arm` bootstrap call to be replaced, and requires a source/call-graph assertion. But §10.2 still names the new function `bootstrap_paired(...)`, while §17.3 names it `bootstrap_paired_v2` (MF-1). |
| 3 | paired `L>F` | **closed** | §3.5 now fixes cohort 15 common, same variant/endpoint/memory_kind/seed, per-doc `delta_L(doc) - delta_F(doc)`, seed-average before bootstrap, missing pair `NA`, no 15→14. |
| 4 | template `note` vs frozen schema | **closed** | §16.2 explicitly allows an optional `note` in the frozen manifest; the template's `note` is therefore legal. `status: template → frozen` is shown by the schema. |
| 5 | cap 120 vs 155 | **closed** | §11.6 now states registered wall = 120 min (Phase 6 only), 155 min = D0 15 + D1 20 + registered 120, explicitly "not a single-run cap". |
| 6 | P0 tail provenance | **closed** | §10.4 now states `.4862/.43355/.455` are derived from `p0_native_sanity.json`, not stored, descriptive only. I recomputed: val20 abs `0.43355` / signed `0.4862`; common-15 abs `0.45478 → .455`. Accurate. |
| 7 | §4.6 `p_valid=NA` | **closed** | §4.6 now reads `p_step NA + p_valid=NA → NOT_ASSESSABLE`, matching F9; `pa_path NA + p_valid=false → P_STEP100_NOT_VALID` matches §4.4 ordering and F3. No unreachable tier bullet remains in §4.6. |

- 다음 단계:
  1. Rename the new stats symbol consistently to `bootstrap_paired_v2` in §10.2/§13.5 (MF-1).
  2. State that the `evaluate_arm` bootstrap replacement lands before the freeze commit (MF-2).
  3. Re-hash the plan after the text patch; the current `50d4bf21…` hash will change.

## Q2. Freeze chain

- **판정: agree (chain is sound); one low residual**

- Order is now: (1) final plan commit; (2) populate `_FREEZE.json` with `manifest_commit:null`; (3) manifest commit; (4) write `freeze_manifest_commit.txt`; (5) D0 report. No step requires a file to contain its own commit SHA.
- `freeze_commit` = final plan commit (normative bytes + helper sources), stated explicitly and distinct from the manifest commit.
- `plan_sha256` is computed after step 1 and the manifest is excluded from the plan hash, so the plan hash is stable across steps 2–5.
- D0 records `manifest_commit` from the external file, so the pointer is auditable without self-reference.

Residual (MF-2, low): `freeze_manifest_sha256` is used at §16.2 step (5) but never defined. Define it as `SHA256` over the committed `_FREEZE.json` bytes, and state whether `freeze_manifest_commit.txt` is itself committed (and, if so, that D0 also records its hash) so the external pointer has a custody chain.

- 다음 단계:
  1. Add the one-sentence definition of `freeze_manifest_sha256`.
  2. State the commit/custody status of `freeze_manifest_commit.txt`.
  3. Keep the manifest out of `plan_sha256`.

## Q3. Legacy bootstrap

- **판정: conditional (mechanism is right; symbol contract is contradictory)**

What is now closed:

- `runner/c5_pm_phase6.py` is declared the only Phase 6 entrypoint; its call graph is listed as `-> c5_pm_stats.bootstrap_paired_v2` and `-> c5_mt5_lora_b0.train_arm/evaluate_arm`.
- It must not import or call `runner.c5_mt5_lora_b0.bootstrap_paired`; if `evaluate_arm` is reused its bootstrap must be replaced; a source/call-graph assertion and "no monkeypatch-only workaround" are required.
- I confirmed the real hazard is on that path: `train_arm` calls `evaluate_arm` (`runner/c5_mt5_lora_b0.py:723`), and `evaluate_arm` calls the legacy `bootstrap_paired` at line 460. `metric_smoke` also reaches it (lines 619/621, 653). P0 does **not** (`p0_sanity` → `p0_eval_split`), so the replacement does not change the P0 artifact — a useful fact the plan should state.

What is not closed (MF-1, material):

- §10.2 defines the new module's API as `` `bootstrap_paired(seed=20261109)` ``, while §17.3 requires `c5_pm_stats.bootstrap_paired_v2`. An implementer cannot satisfy both.
- The mandated test "source/call-graph assertion that `bootstrap_paired(` does not appear in the Phase 6 path" would **fail against the plan's own §10.2 name**. It is also defeatable by aliasing (`from c5_pm_stats import bootstrap_paired as bp`) because it is a literal-source check.
- The spec does not say when the `evaluate_arm` replacement happens. §17.1 freezes helper behavior "by the cited files at the freeze commit," so the replacement must land **before** the freeze commit; otherwise `helper_commits["runner/c5_mt5_lora_b0.py"]` binds a file that contradicts the Phase 6 path.

- 다음 단계:
  1. Rename §10.2's symbol to `bootstrap_paired_v2` and make §13.5 refer to it; keep "no legacy import" as a separate clause.
  2. Replace the bare substring assertion with an import-graph/attribute-access assertion on `runner.c5_mt5_lora_b0.bootstrap_paired`, plus a runtime test that patches the legacy symbol to raise and exercises the Phase 6 eval path. ("No monkeypatch-only workaround" should be read as banning a runtime monkeypatch *fix*, not a detection test; say so.)
  3. State that the `evaluate_arm` replacement is pre-freeze, and that P0 is unaffected because P0 does not use `evaluate_arm`.

## Q4. Paired L>F

- **판정: agree**

- Cohort = 15 common IDs; same variant/endpoint/memory_kind/seed; per-doc `delta_L - delta_F`; seed-average before bootstrap; missing pair `NA`; no 15→14 substitution.
- F and L both have 15 common M targets (`m_cohort_preflight.json: l_target_eligible_at_k=15`), so the pairing domain is populated and non-degenerate.
- It composes with §10.3 ("same retained IDs copy/full/L−F") and §3.5's `delta_copy = shuffled_copy_ce - real_copy_ce`, so both arms use the same definition.
- Minor wording only: "same variant" is vacuous for the signal endpoint, where `variant` is `NA` (§10.4). Harmless, but the clause could say "same variant (or `NA` for the signal endpoint)".

- 다음 단계:
  1. Clarify the signal-endpoint `variant=NA` case in the pairing list.
  2. Add a unit test with one document missing from F → predicate `NA`, not a 14-doc pass.
  3. Add a test that pairing is by `doc_id`, not by position.

## Q5. Cap and labels

- **판정: agree**

- §11.6: registered run wall = 120 min (Phase 6 only); 155 min = 15 (D0) + 20 (D1) + 120 (registered), "not a single-run cap"; prospective max 1,204 updates / 155 min, explicitly not a grant; no retry/extension.
- Arithmetic verified: `1,200 + 4 = 1,204`; `120 + 15 + 20 = 155`; registered units 12 (4 arms × 3 seeds); D1 4 units.
- This removes the ambiguity I flagged in Q9/MF-5 of the v1.0.7 round.

- 다음 단계:
  1. Keep §11.1 registered-only table and §11.6 envelope label as they now read.
  2. Keep the 120-min hard abort tied to the registered run, not the envelope.

## Q6. P0 tail provenance

- **판정: agree**

- §10.4 adds: "P0 tail values `.4862/.43355/.455` are derived from `p0_native_sanity.json`; they are not stored fields and are descriptive only."
- I recomputed from the artifact: val20 `top3_abs_share = 0.43355`, `top3_signed = 0.4862`; common-15 `top3_abs_share = 0.45478` (the `.455` in the plan is correct at the stated precision); common-15 signed `0.50708`.
- This closes the GLM finding that the values were absent from `p0_native_sanity.json`: they are derivable, and the plan now says so.
- The stronger surrounding warnings are intact: P0 used `source_max_length=256`, Phase 6 M uses 512, and P0 is not trained P/PA/L calibration.

- 다음 단계:
  1. Keep the derived-not-stored sentence; do not add a new P0 artifact or regenerate P0.
  2. Optionally record the derivation formula next to the values so a reader does not have to re-derive the top-3 tie rule.

## Q7. §4.6 tier precedence

- **판정: agree**

- `p_step NA + p_valid=NA → NOT_ASSESSABLE` matches F9 exactly and resolves the unreachable notation.
- The other three bullets remain reachable and consistent with §4.2–§4.4: `pa_path NA + p_valid=false → P_STEP100_NOT_VALID` (P check precedes PA path), `pa_path NA + pa_valid=false → NOT_ASSESSABLE` (PA path NA precedes PA validity).
- I found no remaining unreachable tier bullet in §4.6, and §4.7's invariants still agree.

- 다음 단계:
  1. Add a one-line test binding each §4.6 bullet to its F-fixture.
  2. Keep F9/F10 as the NA-precedence regressions.

## Q8. Self-containedness

- **판정: conditional**

- v1.0.8 is implementable without reading v0.2.x/r3.x for the decision, validity, control, statistics, replay, freeze, and entrypoint contracts.
- Remaining external references are explicit and bound: §17.1 helper implementations (frozen by the helper commits recorded in the manifest) and the preflight/P1/golden artifacts (hash-bound).
- Two self-containedness defects remain: the `bootstrap_paired` vs `bootstrap_paired_v2` contradiction (Q3/MF-1), and the undefined `freeze_manifest_sha256` plus unstated custody of `freeze_manifest_commit.txt` (Q2/MF-2). Both are text-only and small, but an implementer currently must guess.

- 다음 단계:
  1. Fix MF-1 and MF-2 as numbered text repairs.
  2. Add an explicit statement that a helper signature not matching the bound commit is `NOT_ASSESSABLE`.
  3. Do not add new scientific choices.

## Q9. Final verdict

- **판정: NARROW**

Six of the seven items are genuinely closed, and the freeze chain itself no longer self-references. The one material gap is that the mechanism that closes the legacy-bootstrap item names two different symbols, and the plan's own required assertion would fail against §10.2. That is a text-only fix, but until it is made v1.0.8 cannot be the single unambiguous implementation authority.

```text
최종 판정: NARROW
v1.0.8 freeze: NO as-is; YES after MF-1 and MF-2 (text-only), plan re-hashed, new freeze commit
구현+unit tests: CONDITIONAL (after freeze; contract/decision/stats tests only, no training)
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
  - runtime monkeypatch as a substitute for the entrypoint fix
최대 compute: no grant; prospective ceiling only ≤1,204 updates / 155 min
  (1,200 registered + 4 D1; D0 ≤15 min; D1 ≤20 min; registered 120-min hard abort; T_proj ≤96 min)
Must-fix (ranked):
  1. MF-1 (material): new stats symbol is `bootstrap_paired` in §10.2 but `bootstrap_paired_v2`
     in §17.3; the required source assertion would fail against §10.2. Rename consistently and
     replace the substring check with an import/attribute-access assertion.
  2. MF-2 (low): `freeze_manifest_sha256` used in §16.2 but never defined; state the definition
     and the commit/custody status of `freeze_manifest_commit.txt`.
  3. MF-3 (clarity): state that the `evaluate_arm` bootstrap replacement lands before the freeze
     commit, and that P0 is unaffected because P0 does not use `evaluate_arm`.
v1.0.8 self-contained: YES for decision/validity/control/stats/replay/freeze contracts,
  except the MF-1 symbol contradiction and MF-2 hash definition; helper internals are
  external by design and bound by helper commits.
잘못된 전제:
  - `38a2a81` is not current origin/main HEAD; HEAD is `d4e9dfa`, one commit later.
    The only difference is the review harness; reviewed artifact bytes are identical.
  - v1.0.7's substantive split was 1 CONTINUE / 2 NARROW, not 2/2 NARROW; the current
    round's basis is the 2/3 NARROW synthesis.
  - Replacing the legacy bootstrap call does not alter the P0 artifact, because P0 uses
    `p0_eval_split`, not `evaluate_arm`.
  - P0 is descriptive native-path sensitivity, not trained P/PA/L calibration.
  - test 163 is sealed, P1 is unused, and no Phase 6 result exists.
```

## 4. Limitations

- No training, evaluation, generation, test-163 read, or P1 read was performed.
- I did not run the repository's Python test suite (not requested for a text review; the environment also lacks `numpy`/`torch` in the default interpreter). Golden digests and P0 tail values were recomputed with the standard library only.
- This report is consultation only. It modifies no plan, template, golden vector, provenance file, runner, or test, and it does not approve Phase 6/B0-B/B1/B2/Stage C.