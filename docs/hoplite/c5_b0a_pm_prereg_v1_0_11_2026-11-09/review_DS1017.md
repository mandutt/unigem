# C5 Phase 6 P/M v1.0.11 — Own-Loop Final Confirmation (DeepSeek V4.1 Flash 1017)

- Reviewer: Hoplite `deepseek-v4.1-flash-1017` (OpenRouter), reasoning high
- Round: v1.0.11 own-loop, same consultation thread as v1.0.7 … v1.0.10. No other model's answer reused; no subagents.
- Review date: 2026-11-09
- Reviewed HEAD SHA: **`6fad89e`**
- Repository: `mandutt/unigem`, branch `main` (project `proj_2e8de5ed594f47c7b851f1d7c5b52c61`)
- Mode: read-only consultation. No training, no evaluation, no test-163 access, no P1 use.
- Scope: own training/eval loop lifecycle, `train_arm`/`evaluate_arm` exclusion and transitive path, training correctness under §2.7/§2.5. Nothing closed in v1.0.10 was re-reviewed.

## Mandatory verification

Reviewed commit:

```text
6fad89e
```

Verbatim quote, from the §17.3 call graph at line 1756:

```text
  -> own training loop
```

The required substring appears exactly: `-> own training loop`.

## 0. Sync and provenance

```text
git fetch origin          -> success
git pull --ff-only origin main
  Updating 206117b..9954c98
  head = 9954c986a7f48ffba422908dfb84b1ddab13035e
```

- The first pull aborted because upstream committed my own v1.0.10 `review_DS1017.md` at the same path as my untracked copy. I backed it up to `/tmp`, removed the untracked file, and the pull completed. The committed copy matches mine except a trailing newline, so the v1.0.10 report is preserved verbatim.
- `git diff --name-status 6fad89e 9954c98` adds only review-harness files (`dispatch_fup.sh`, three `fup_*.txt`, `threads.json`, `watch_reviews.py`, the v1.0.11 request). No plan, template, golden, provenance, runner, or test file differs, so reviewing `6fad89e` reviews the current artifact bytes.
- Working tree clean after the pull.

Artifact hashes:

```text
plan_c5_..._v1_0_11.md     327a3e34f5bb2721b8b2400718dfd7bc56a0946641d1e83e2c8b454bf656d007
golden_vectors.json        30cbd1c1281235d0750c2bf9271b82cbe55eb64f099d8226216e14b2020ed3f6
m_cohort_preflight.json    3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af  (matches §0.4)
```

All five golden digests recomputed independently and match; `phase7_diagnostic` remains 600/arm-seed numeric-only; `key_coverage_golden` remains 4 records. The template matches the §16.2 schema with `manifest_commit: null` and `plan_path` v1_0_11.

**Delta check.** The v1.0.10→v1.0.11 diff is exactly the own-loop repair plus version strings: the §17.3 block, the two added exclusion bullets, the transitive-path definition, the P0 line, the `train_arm` composite explanation, and the §13.5 DoD line. No hidden semantic or scientific change.

---

## Q1. Own training/eval loop lifecycle

- **판정: agree**

- §16.1 keeps "No code before freeze."
- §17.3 keeps "no pre-freeze helper edit is required."
- Phase 6 now owns both loops: the call graph is `runner/c5_pm_phase6.py -> own training loop -> own eval loop -> c5_pm_stats.bootstrap_paired_v2`.
- Because nothing in the frozen helper has to change, the Sol/GLM lifecycle contradiction I accepted as resolved in v1.0.10 is now resolved *without* the counterexample: the v1.0.10 clause that broke it (`train_arm may be reused for training`) is gone.
- The ownership boundary is coherent: `c5_pm_phase6.py` is "the only Phase 6 entrypoint," and training, evaluation, and statistics all live inside it or in the new stats module.

- 다음 단계:
  1. Keep the "no pre-freeze helper edit" invariant as a freeze-checklist assertion.
  2. Confirm in the freeze manifest that `runner/c5_mt5_lora_b0.py`'s helper hash is unchanged from the pre-repair bytes.
  3. Do not reintroduce any helper-reuse clause without a matching §17.1 row.

## Q2. `train_arm` / `evaluate_arm` exclusion and transitive path

- **판정: agree**

The three prohibitions are explicit and now consistent:

```text
1762  - it must not import or call `runner.c5_mt5_lora_b0.train_arm`.
1763  - it must not import or call `runner.c5_mt5_lora_b0.evaluate_arm`.
1764  - it must not import or call `runner.c5_mt5_lora_b0.bootstrap_paired` legacy.
1766  - `train_arm` is a composite helper that calls `evaluate_arm`; it is not training-only and must not be reused.
1768  - "Phase 6 path" = transitive call graph rooted at `runner/c5_pm_phase6.py`.
1769  - test: no `train_arm`, `evaluate_arm`, or legacy `bootstrap_paired(` in that transitive path.
```

- This closes the defect I raised in v1.0.10: the frozen `train_arm` calls `evaluate_arm` at `runner/c5_mt5_lora_b0.py:723` and `generate_arm` at `:724`, so banning `train_arm` removes the last route to legacy `bootstrap_paired` (line 460).
- The "Phase 6 path" definition is now scoped: the transitive call graph rooted at the entrypoint. That is the correct reading, and it makes the literal-name test meaningful rather than sufficient-by-itself.
- §13.5 DoD repeats the exclusion ("Phase 6 path does not import `train_arm` or `evaluate_arm`"), so it is a definition-of-done item, not only a §17.3 note.
- P0's independence is stated: P0 uses `p0_eval_split`, not `train_arm`/`evaluate_arm`, so the exclusion cannot perturb the frozen P0 artifact.

- 다음 단계:
  1. Satisfy the assertion by reachability (import graph / attribute access), not only by literal substring grep, since `from x import train_arm as t` would evade a text check.
  2. Add a runtime test that patches `runner.c5_mt5_lora_b0.evaluate_arm` to raise and exercises the full Phase 6 eval path.
  3. Keep "no monkeypatch-only workaround" as the detection rule, not the fix.

## Q3. Training correctness under §2.7 / §2.5

- **판정: conditional**

The normative content needed by an own loop is present and mutually consistent:

| requirement | clause | state |
|---|---|---|
| optimizer AdamW, wd `.01`, lr split `1e-3` adapter / `1e-4` LoRA | §2.2 | complete |
| 100 updates, batch 1, `order = train20_ids[step % 20]`, clip 1.0 | §2.2 | complete |
| built-in mT5 CE via `encoder_outputs`, `attention_mask=ones(len(memory))`, `labels` | §2.5.2 | complete |
| F/L memory `A(h_i)[:753]`, P/PA `A(h_i)[:512]`, no donor in training | §2.5.3 | complete |
| adapter geometry `Linear→GELU→Linear→LayerNorm`, LoRA r8 alpha16 dropout .05, A kaiming / B zeros | §2.5.4 | complete |
| per-arm mode table (F/L/P/PA), base decoder eval, LoRA dropout train-only | §2.7 | complete |
| RNG order `manual_seed(seed)` → adapter → LoRA, no reseed between | §2.7 | complete |
| parameter inventory asserts expected trainable sets | §2.7 | complete |
| P identity memory, PA random-init adapter | §2.4, §2.5.3 | complete |

So the own loop is constructible from §2.2/§2.5/§2.7 plus the §17.1 primitives (`Adapter`, `make_labels`, `load_layer_cache`, `LoRALinear`, `attach_decoder_lora_mt5`, `native_memory`). There is no contradiction with the frozen helper: those primitives are unchanged, and the parts Option A moved inward were composite, not primitive.

Two completeness gaps remain (non-blocking, but they force implementer decisions the spec should fix):

1. **Helper coverage for the inward-moved work.** The own loop now needs functions that `evaluate_arm` used to supply: `copyable_mask`, `copy_ce`, `shifted_copy_mask`, `donors_for`, `native_source_ids`, `set_training_mode`, `lora_parameters`, `load_base`, `generate_arm` — all present in `runner/c5_mt5_lora_b0.py` but absent from the §17.1 table. Their semantics are specified in §2.5.5/§2.5.6/§2.5.7/§2.7 prose, and §17.1's "reproduce their contract exactly" covers the case, but §17.1 also says signatures and behavior "are frozen by the cited files," which currently cites no file for them. An implementer may import them (fine) or reimplement (allowed only if semantics match, and the signatures are not frozen anywhere), so exactness is not guaranteed.
2. **Checkpoint production is unassigned.** §17.2 requires `checkpoints/{arm}/{seed}.pt` and `final_checkpoint_hash.json`; §12.1 defines the 12-key hash map; §11.4 step 1 loads them. But no clause says the entrypoint writes them at step 100, and the frozen runner contains no `torch.save`. With Option A, this is now unambiguously Phase 6's job, and the plan should say so.

- 다음 단계:
  1. Add the inward-moved primitives to §17.1 with a one-line contract each (at minimum `copyable_mask`, `donors_for`, `native_source_ids`, `set_training_mode`).
  2. State that `c5_pm_phase6.py` writes `checkpoints/{arm}/{seed}.pt` after update 100 and emits `final_checkpoint_hash.json` per §12.1.
  3. Add a test that the parameter inventory after construction equals the §2.7 expected trainable set for each arm.

## Q4. Residuals introduced by v1.0.11

- **판정: agree (no new contradiction)**

Ranked:

1. **§17.3/§13.5 do not positively name `c5_pm_stats.bootstrap_paired_v2` in the DoD.** §10.2 and §17.3 name it; §13.5 states only the negative (no legacy import). Low.
2. **§17.1 omits the inward-moved primitives** (Q3 gap 1). Low–medium; it caps self-containedness without changing semantics.
3. **Checkpoint production unassigned** (Q3 gap 2). Low; paths and hash schema exist in §17.2/§12.1.
4. **`t_train_arm` naming in §11.5.** The T_proj term still reads `100 * t_train_arm`, while the loop is now Phase 6's own; it is a per-arm training-time symbol, but the name now echoes a banned function. Cosmetic.
5. **Literal-substring assertion.** `bootstrap_paired(` and `train_arm` checks are satisfiable by aliasing; the plan's "transitive call graph" wording is the right fix but the test text still describes a name scan. Low.

No previously closed clause regressed: the v1.0.9/v1.0.10 symbol unification, `manifest_commit: null`, `freeze_manifest_sha256` and txt custody, paired L>F, §4.6 precedence, P0 tail provenance, and the 1,680 / 560 / 600 / 1,204 / 155 arithmetic all verify unchanged.

## Q5. Final verdict and approval scope

- **판정: CONTINUE**

The v1.0.10 blocker is genuinely closed: Phase 6 owns both loops, `train_arm` and `evaluate_arm` are both banned, the path is defined transitively, and no pre-freeze helper edit is needed. §2.2/§2.5/§2.7 give an implementable training contract with no internal contradiction. What remains are completeness items — a few helper rows and one artifact-producer sentence — none of which changes a cohort, seed, threshold, donor, step, or LR, and none of which makes the specification ambiguous about *what* to implement.

```text
최종 판정: CONTINUE
v1.0.11 freeze: APPROVED (protocol contract only; final plan commit = freeze_commit,
  _FREEZE.json with manifest_commit:null, external committed freeze_manifest_commit.txt)
구현+unit tests: APPROVED (§13 contract/decision/M/stats/replay tests; no training,
  no evaluation, no generation)
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
  - pre-freeze edits to runner/c5_mt5_lora_b0.py
  - reuse of train_arm or evaluate_arm on the Phase 6 path
  - runtime monkeypatch as a substitute for the exclusion
최대 compute: no grant beyond D0; prospective ceiling only ≤1,204 updates / 155 min
  (1,200 registered + 4 D1; D0 ≤15 min; D1 ≤20 min; registered 120-min hard abort; T_proj ≤96 min)
Must-fix (ranked): none blocking. Implementation-time follow-ups:
  1. add copyable_mask / donors_for / native_source_ids / set_training_mode to §17.1;
  2. state that c5_pm_phase6.py writes checkpoints and final_checkpoint_hash.json;
  3. assert reachability, not literal substrings, for the train_arm/evaluate_arm ban;
  4. name bootstrap_paired_v2 positively in §13.5.
v1.0.11 self-contained: YES for lifecycle, exclusion, decision/validity/control/stats/
  replay/freeze and the §2.2/§2.5/§2.7 training contract; PARTIAL for the inward-moved
  primitive signatures and the checkpoint-producer assignment.
잘못된 전제:
  - `6fad89e` is not current origin/main HEAD; HEAD is `9954c98`, one commit later.
    The only difference is the review harness; reviewed artifact bytes are identical.
  - v1.0.10's split was 3/3 NARROW, not a majority; this round addresses that one
    blocker and does not retroactively validate earlier rounds.
  - `train_arm` is a composite: it calls evaluate_arm (:723) and generate_arm (:724),
    and supports only the `frozen`/`lora` arms.
  - P0 remains descriptive native-path sensitivity, not trained P/PA/L calibration.
  - test 163 is sealed, P1 is unused, and no Phase 6 result exists.
```

## 4. Limitations

- No training, evaluation, generation, test-163 read, or P1 read was performed.
- The repository's Python test suite was not executed (not requested for a text review; the default interpreter also lacks `numpy`/`torch`). Golden digests, helper presence, call sites, and hash values were verified with the standard library, `git`, `grep`, and `sed` only.
- This report is consultation only. It modifies no plan, template, golden vector, provenance file, runner, or test, and does not approve Phase 6 registered training, D1, 3-seed, B0-B, B1/B2, or Stage C.