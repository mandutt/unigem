# C5 Phase 6 P/M v1.0.9 — Final Same-Thread Confirmation (DeepSeek V4.1 Flash 1017)

- Reviewer: Hoplite `deepseek-v4.1-flash-1017` (OpenRouter), reasoning high
- Round: v1.0.9 final confirmation, same consultation thread as my v1.0.7 and v1.0.8 reviews. No other model's answer reused; no subagents.
- Review date: 2026-11-09
- Reviewed HEAD SHA: **`e680c8f`**
- Repository: `mandutt/unigem`, branch `main` (project `proj_2e8de5ed594f47c7b851f1d7c5b52c61`)
- Mode: read-only consultation. No training, no evaluation, no test-163 access, no P1 use.
- Scope: the three items I left open in v1.0.8 only. Items closed in v1.0.7/v1.0.8 were not re-reviewed.

## Mandatory verification

Reviewed commit:

```text
e680c8f
```

Verbatim quote:

```text
c5_pm_stats.bootstrap_paired_v2
```

## 0. Sync and provenance

```text
git fetch origin          -> success
git pull --ff-only origin main
  Updating d4e9dfa..b9fd854
  head = b9fd85417377bc77cbe1ee146e34a89c78448869
```

- The first pull attempt aborted because upstream had committed my own v1.0.8 `review_DS1017.md` at the same path as my untracked copy. I backed it up to `/tmp`, removed the untracked file, and the pull completed. The committed copy is byte-identical to mine except a trailing newline, so the v1.0.8 report is preserved verbatim.
- `git diff --name-status e680c8f b9fd854` adds only review-harness files (`dispatch_fup.sh`, `fup_ds1017.txt`, `fup_glm.txt`, `fup_sol.txt`, `threads.json`, `watch_reviews.py`, the v1.0.9 request). No plan, template, golden, provenance, runner, or test file differs, and `git show e680c8f:docs/plan_c5_b0a_pm_prereg_v1_0_9.md` equals the working copy. Reviewing `e680c8f` therefore reviews the current artifact bytes.
- Working tree clean after the pull.

Artifact hashes:

```text
plan_c5_..._v1_0_9.md     3b662b27ee8078cc93031cb2acea04634205e96db487057c4e6514b01d5bb719
golden_vectors.json       9223cb9257962b090c6acd397c6aa68c89ba86d6271f7d6a39464a0c4e43339b
m_cohort_preflight.json   3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af  (matches §0.4)
```

Golden digests recomputed independently from the JSON and all match: `state 43ecb58e…d65712`, `empty e3b0c442…b855`, `replay_base c43ea35c…f7851667`, `key_coverage 8277a713…af7a20` (4 records), `control 6b50c226…c1938`; `phase7_diagnostic` remains 600/arm-seed, numeric-only.

**Delta check.** Diffing the v1.0.8 and v1.0.9 plans shows only: version strings, the §10.2 symbol, the §12.3 golden path, the §15 traceability labels, the §16.2/§16.3 version strings, the two new `freeze_manifest_sha256` / custody bullets, and the §17.3 "before the freeze commit" clause. No hidden semantic change, no new scientific choice.

---

## Q1. `bootstrap_paired_v2` symbol consistency

- **판정: agree**

Verified occurrences in the v1.0.9 plan:

```text
1183  - `c5_pm_stats.bootstrap_paired_v2(seed=20261109)`.
1755    -> c5_pm_stats.bootstrap_paired_v2
1761  - if `evaluate_arm` is reused, its bootstrap call is replaced by
        `c5_pm_stats.bootstrap_paired_v2` **before the freeze commit**.
```

Negative occurrences (all correctly referring to the *legacy* symbol):

```text
1188  - no legacy `bootstrap_paired`.
1585  - stats module does not import legacy `bootstrap_paired`.
1760  - it must not import or call `runner.c5_mt5_lora_b0.bootstrap_paired` legacy.
1762  - test: source/call-graph assertion that `bootstrap_paired(` does not appear in the Phase 6 path.
```

- The v1.0.8 contradiction is gone: §10.2 and §17.3 now name the same symbol, and the module is qualified as `c5_pm_stats.` in both.
- The §17.3 assertion is no longer self-defeating. It checks for the literal `bootstrap_paired(`, and `bootstrap_paired_v2(` does not contain that substring (the character after `bootstrap_paired` is `_`, not `(`). It therefore passes against the new API name while still catching the legacy call.
- The legacy function remains only in the frozen helper for P0 historical reproduction, which is correct: I confirmed P0 reaches it through `p0_eval_split`, not `evaluate_arm`.

Residual (non-blocking, low): §13.5 still states only the negative (does not import legacy) and never names `bootstrap_paired_v2`, so the DoD list does not positively require the new symbol. Also, a literal substring check does not catch aliasing (`from ... import bootstrap_paired as bp`); the plan's "source/call-graph assertion" wording covers this if the implementer actually asserts on the call graph or attribute access rather than raw text.

- 다음 단계:
  1. In the implementation, satisfy §17.3 with an import/attribute-access or call-graph assertion, not only a raw-text grep.
  2. Optionally add `bootstrap_paired_v2` by name to the §13.5 DoD line.
  3. Keep the legacy symbol untouched for P0.

## Q2. `freeze_manifest_sha256` definition and external txt custody

- **판정: agree**

§16.2 now states, in order:

```text
- `manifest_commit` is always `null` inside `_FREEZE.json`; ...
- after the manifest commit, write `reports/provenance/C5_b0a/freeze_manifest_commit.txt` with the actual SHA.
- `freeze_manifest_sha256` = SHA256 of the committed `_FREEZE.json` bytes.
- `freeze_manifest_commit.txt` is committed; D0 also records its SHA256.
- D0 report records both `freeze_manifest_sha256` and `manifest_commit` from that external file.
- freeze order: (1) final plan commit; (2) populate `_FREEZE.json` with `manifest_commit:null`;
  (3) manifest commit; (4) write external commit file; (5) D0 report.
```

- The hash is defined over a specific object (committed manifest bytes), not left implicit.
- The chain is acyclic: `_FREEZE.json` contains `manifest_commit: null`; the txt contains the manifest commit SHA; D0 records the manifest byte hash and the txt hash. No artifact contains its own commit SHA.
- Custody is now explicit in both directions: the txt is committed, and its content hash is recorded, so a later edit to the pointer is detectable.
- The manifest stays outside `plan_sha256`, so the plan hash is stable across steps 2–5.

Residual (non-blocking, low): the freeze order says step (4) "write external commit file" while the bullet says the txt "is committed"; the commit of the txt is not its own numbered step. Because D0 records the txt's SHA256, this is auditable either way, but one clause would remove the ambiguity.

- 다음 단계:
  1. State that step (4) both writes and commits `freeze_manifest_commit.txt` (or name the txt commit in D0).
  2. Keep `manifest_commit: null` in the manifest; do not reintroduce a self-reference.
  3. Recompute `plan_sha256` only after the final plan commit.

## Q3. `evaluate_arm` replacement before freeze

- **판정: agree**

- §17.3 now reads "if `evaluate_arm` is reused, its bootstrap call is replaced by `c5_pm_stats.bootstrap_paired_v2` **before the freeze commit**." The timing question I raised in v1.0.8 is answered explicitly.
- This composes correctly with §16.2's `freeze_commit = final plan commit (normative bytes + helper sources)`: because `runner/c5_mt5_lora_b0.py` is in `helper_commits`, the replacement must land no later than that commit, so the bound helper hash covers the replaced file. No post-freeze drift between the frozen helper and the Phase 6 path.
- The real hazard remains correctly targeted: `train_arm` calls `evaluate_arm` (`runner/c5_mt5_lora_b0.py:723`), and `evaluate_arm` calls the legacy `bootstrap_paired` at line 460; `metric_smoke` also reaches it (619/621, 653).
- "No monkeypatch-only workaround" plus the call-graph assertion is the right combination: it forbids pretending to fix the path at runtime while leaving the source dependency in place.

Residual (non-blocking, low): the plan does not state that P0 is unaffected (P0 uses `p0_eval_split`, not `evaluate_arm`), so a reader could fear the replacement perturbs the frozen P0 artifact. This is a clarity point, not a defect.

- 다음 단계:
  1. Land the `evaluate_arm` bootstrap replacement in the freeze commit's helper bytes.
  2. Add a runtime test that patches the legacy symbol to raise and exercises the Phase 6 eval path.
  3. Note that P0 is unaffected because P0 does not use `evaluate_arm`.

## Q4. Residuals introduced by v1.0.9

- **판정: agree (no new blocking problem)**

The v1.0.8→v1.0.9 diff is confined to the three fixes plus version strings. I checked for collateral damage and found none:

- No stale `v1_0_6` / `v1_0_7` / `v1_0_8` path or manifest reference remains in the v1.0.9 plan (`grep` returns nothing); `plan_path`, the freeze manifest name, and the golden path all point to `v1_0_9`.
- Previously closed clauses are intact: §0.4 preflight hash `3ee3f1ca…`; §1.1 splits `1,293 / 161 / 163` with test 163 sealed; §9.6.1 `K_d = min(K_M, len(real_prefix), len(donor_prefix))`; §4.6 `p_step NA + p_valid=NA → NOT_ASSESSABLE` plus the two reachable PA bullets; §10.4 P0 tail `.4862/.43355/.455` marked derived-not-stored; §11.6 registered 120 vs aggregate 155.
- Arithmetic unchanged and still correct: 1,680 endpoint records (15×96 + 5×48), 560 per seed, 600/arm-seed phase 7, 1,204 updates, 155 min envelope.
- Template matches the schema (`manifest_commit: null`, `plan_path` v1_0_9, `status: template`, `note` allowed by §16.2).

Non-blocking observations only (ranked):

1. §13.5 DoD does not positively name `bootstrap_paired_v2` (Q1 residual).
2. Freeze-order step (4) "write" vs "is committed" for the txt (Q2 residual).
3. P0-unaffected statement absent (Q3 residual).

None of these creates ambiguity about what to implement or changes any scientific parameter. None is a freeze blocker.

## Q5. Final verdict and approval scope

- **판정: CONTINUE**

All three v1.0.8 must-fixes are closed as text-only repairs: the symbol is unified as `c5_pm_stats.bootstrap_paired_v2` with the legacy name explicitly forbidden; `freeze_manifest_sha256` has a concrete definition and an acyclic custody chain through a committed external txt and the D0 report; and the `evaluate_arm` replacement is pinned before the freeze commit. No new problem, no post-result parameter change, and no previously closed clause regressed.

```text
최종 판정: CONTINUE
v1.0.9 freeze: APPROVED (protocol contract only; final plan commit = freeze_commit,
  _FREEZE.json with manifest_commit:null, external committed freeze_manifest_commit.txt)
구현+unit tests: APPROVED (contract/decision/M/stats/replay tests per §13;
  no training, no evaluation, no generation)
D0: APPROVED (≤4 configs, 0 optimizer updates, ≤15 min, seed 20261111,
  labels_computed:false for decision/signal labels, not_a_result:true)
D1: NOT APPROVED (separate approval after the D0 report)
3-seed: NOT APPROVED
금지 범위:
  - Phase 6 registered training/evaluation execution
  - test 163 access (sealed)
  - P1 use
  - T5Gemma2 reopening (D-108 STOP)
  - B0-B/B1/B2/Stage C auto-advance
  - post-result threshold/seed/donor/step/LR changes
  - single-checkpoint replay
  - direct debug-vs-final replay-hash comparison
  - any 753 training/generation requirement
  - runtime monkeypatch as a substitute for the §17.3 source fix
최대 compute: no grant beyond D0; prospective ceiling only ≤1,204 updates / 155 min
  (1,200 registered + 4 D1; D0 ≤15 min; D1 ≤20 min; registered 120-min hard abort; T_proj ≤96 min)
Must-fix (ranked): none blocking. Implementation-time follow-ups:
  1. satisfy §17.3 with an import/attribute-access or call-graph assertion, not raw text only;
  2. name `bootstrap_paired_v2` positively in the §13.5 DoD line;
  3. clarify that freeze-order step (4) also commits `freeze_manifest_commit.txt`;
  4. state that P0 is unaffected by the evaluate_arm replacement.
v1.0.9 self-contained: YES for the decision/validity/control/stats/replay/freeze/entrypoint
  contracts; helper internals remain external by design and are bound by helper_commits.
잘못된 전제:
  - `e680c8f` is not current origin/main HEAD; HEAD is `b9fd854`, one commit later.
    The only difference is the review harness; reviewed artifact bytes are identical.
  - v1.0.8's split was 2 CONTINUE / 1 NARROW, not a unanimous CONTINUE; this round
    closes the single NARROW's three items, so it does not retroactively validate
    the prior round's majority as unanimity.
  - P0 remains descriptive native-path sensitivity, not trained P/PA/L calibration.
  - test 163 is sealed, P1 is unused, and no Phase 6 result exists.
```

## 4. Limitations

- No training, evaluation, generation, test-163 read, or P1 read was performed.
- I did not run the repository's Python test suite (not requested for a text review; the default interpreter also lacks `numpy`/`torch`). Golden digests and structural checks were recomputed with the standard library and `git`/`grep` only.
- This report is consultation only. It modifies no plan, template, golden vector, provenance file, runner, or test.
- This CONTINUE approves the protocol contract, implementation + unit tests, and bounded D0 mechanics only. It does not approve Phase 6 registered training, D1, 3-seed, B0-B, B1/B2, or Stage C.
