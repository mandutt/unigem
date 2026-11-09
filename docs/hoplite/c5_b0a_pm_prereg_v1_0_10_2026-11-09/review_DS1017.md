# C5 Phase 6 P/M v1.0.10 — Option A Final Confirmation (DeepSeek V4.1 Flash 1017)

- Reviewer: Hoplite `deepseek-v4.1-flash-1017` (OpenRouter), reasoning high
- Round: v1.0.10 Option A, same consultation thread as v1.0.7 / v1.0.8 / v1.0.9. No other model's answer reused; no subagents.
- Review date: 2026-11-09
- Reviewed HEAD SHA: **`a88c714`**
- Repository: `mandutt/unigem`, branch `main` (project `proj_2e8de5ed594f47c7b851f1d7c5b52c61`)
- Mode: read-only consultation. No training, no evaluation, no test-163 access, no P1 use.
- Scope: Option A lifecycle, `evaluate_arm` exclusion, `train_arm` reuse only. Items closed in v1.0.9 (symbol unification, `freeze_manifest_sha256`, custody) were not re-reviewed.

## Mandatory verification

Reviewed commit:

```text
a88c714
```

Verbatim quote, from §17.3 at line 1758 (23 spaces before `#`):

```text
own eval loop                       # no evaluate_arm
```

## 0. Sync and provenance

```text
git fetch origin          -> success
git pull --ff-only origin main
  Updating b9fd854..206117b
  head = 206117bd31e29d2b5fd391e2bd0fc7a831c3d6d7
```

- The first pull aborted because upstream committed my own v1.0.9 `review_DS1017.md` at the same path as my untracked copy. I backed it up to `/tmp`, removed the untracked file, and the pull completed. The committed copy matches mine except a trailing newline, so the v1.0.9 report is preserved verbatim.
- `git diff --name-status a88c714 206117b` adds only review-harness files (`dispatch_fup.sh`, three `fup_*.txt`, `threads.json`, `watch_reviews.py`, the v1.0.10 request). No plan, template, golden, provenance, runner, or test file differs. Reviewing `a88c714` reviews the current artifact bytes.
- Working tree clean after the pull.

Artifact hashes:

```text
plan_c5_..._v1_0_10.md     d9d6599451714ac0cde024d9e25ac17454b56b1c024371c5570480457bd12d9b
golden_vectors.json        795bd0852f51d8e428024386f2a88a1409e25221500d3460c34094d8a1617b1c
m_cohort_preflight.json    3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af  (matches §0.4)
```

All five golden digests recomputed independently and match; `phase7_diagnostic` remains 600/arm-seed numeric-only; `key_coverage_golden` remains 4 records. Template matches the §16.2 schema with `manifest_commit: null` and `plan_path` v1_0_10.

**Delta check.** The v1.0.9→v1.0.10 plan diff is exactly the Option A repair plus version strings: §13.5 gains "Phase 6 path does not import `evaluate_arm`"; §17.3 replaces the call-graph block and the `evaluate_arm` reuse clause; everything else is a version label. No hidden semantic change.

---

## Q1. Option A lifecycle consistency with no-code-before-freeze

- **판정: conditional**

What is now consistent:

- §16.1 still says "No code before freeze."
- §17.3 now says "no pre-freeze helper edit is required for this path." That is the correct resolution of the Sol/GLM lifecycle conflict: Option A avoids having to modify `runner/c5_mt5_lora_b0.py` before the freeze commit, so §16.1 and §17.3 no longer contradict.
- Evaluation ownership moves into `runner/c5_pm_phase6.py`, which is unambiguously Phase 6 code written **after** the freeze. The design is sound.

Where it still breaks:

- §17.3 also says "`train_arm` may be reused for training; evaluation is owned by `c5_pm_phase6.py`." That clause cannot be satisfied against the frozen helper. In `runner/c5_mt5_lora_b0.py`, `train_arm` (line 665) unconditionally calls `evaluate_arm(...)` at line 723 and `generate_arm(...)` at line 724, and merges the evaluation result into its return via `**evaluation`. Reusing `train_arm` therefore *is* reusing `evaluate_arm`.
- To make `train_arm` training-only you would have to edit the helper **before** the freeze — precisely the pre-freeze edit Option A exists to avoid. The lifecycle is consistent only if the reuse clause is removed.

- 다음 단계:
  1. Delete "`train_arm` may be reused for training" and state that `c5_pm_phase6.py` owns the training loop as well as the eval loop.
  2. If reuse is desired, name a genuinely training-only helper and add it to §17.1 **and** to the freeze commit's helper bytes; do not amend the frozen `train_arm`.
  3. Keep "no pre-freeze helper edit is required" as the invariant.

## Q2. `evaluate_arm` exclusion

- **판정: conditional**

What is closed:

- §17.3: "it must not import or call `runner.c5_mt5_lora_b0.evaluate_arm`."
- §13.5 DoD: "Phase 6 path does not import `evaluate_arm`."
- §17.3 test: "source/call-graph assertion that neither `evaluate_arm` nor legacy `bootstrap_paired(` appears in the Phase 6 path."
- "No monkeypatch-only workaround" remains, which correctly forbids a runtime patch in place of a structural fix.

What is not closed:

- The scope of "Phase 6 path" is undefined. If it means only the text of `c5_pm_phase6.py`, the assertion is satisfiable while the call graph still reaches `evaluate_arm` through `train_arm` (line 723). If it means the transitive call graph, the assertion correctly fails under the current `train_arm` reuse clause. The spec does not say which, and Q3 shows the two readings disagree.
- This is the same failure mode I flagged in v1.0.8: a literal-source check does not prove unreachability. "Call-graph" is the right word, but the plan must define the root and the closure it covers.

- 다음 단계:
  1. Define "Phase 6 path" as the transitive call graph rooted at `runner/c5_pm_phase6.py`.
  2. Assert on attribute access/imports reached from that root, not only on literal source text.
  3. Add a runtime test that patches `runner.c5_mt5_lora_b0.evaluate_arm` to raise and exercises the Phase 6 eval path.

## Q3. `train_arm` training-only reuse

- **판정: disagree**

The frozen `train_arm` is not training-only and cannot support the Phase 6 arms:

| observation | evidence |
|---|---|
| calls `evaluate_arm` unconditionally | `runner/c5_mt5_lora_b0.py:723` |
| calls `generate_arm` unconditionally | line 724 |
| returns evaluation merged into result | `**evaluation` in the returned dict |
| only arms `frozen`/`lora`, else `ValueError` | lines 685–693 |
| EG2 layer19 cache only | `load_layer_cache("train"...)`, `adapter(h)` |
| not in the authoritative helper table | §17.1 lists Adapter, make_labels, load_layer_cache, LoRALinear, attach_decoder_lora_mt5, native_memory, repeated_4gram_rate — no `train_arm` |

Consequences:

- Reusing `train_arm` re-introduces `evaluate_arm` and therefore legacy `bootstrap_paired` (line 460), defeating Option A's entire purpose.
- Even ignoring that, `train_arm` cannot train P or PA: it accepts only `frozen`/`lora` and builds EG2 memory via the adapter, whereas P/PA require the native mT5 encoder at 512 (§2.5.3, §8).
- §17.1 does not authorize `train_arm` as an authoritative symbol, so its behavior is not frozen by a contract entry, which contradicts §17.3's "may be reused."

- 다음 단계:
  1. Remove `train_arm` from the §17.3 call graph.
  2. Have `c5_pm_phase6.py` own the per-arm training loop (F/L adapter+LoRA; P identity; PA random-init adapter+LoRA) and call `c5_pm_stats.bootstrap_paired_v2` itself.
  3. If a shared training helper is wanted, define it in §17.1 with a training-only contract and land it at the freeze commit.

## Q4. Residuals introduced by v1.0.10

- **판정: disagree (one material residual)**

Ranked:

1. **MF-1 (material):** `train_arm` reuse contradicts the `evaluate_arm` exclusion and cannot train P/PA. §17.3 is internally inconsistent: "may be reused for training" versus "must not import or call `evaluate_arm`." Text-only fix.
2. **MF-2 (medium):** "Phase 6 path" is undefined; the assertion's coverage is ambiguous and, on the lenient reading, does not prove unreachability.
3. **MF-3 (low):** `train_arm` is absent from §17.1, so the reuse clause references an unfrozen symbol while §17.1 says "signatures and behavior are frozen by the cited files."
4. **MF-4 (low, carryover):** the plan still does not state that P0 is unaffected by the Option A split, because P0 uses `p0_eval_split`, not `evaluate_arm`.

No new scientific choice is introduced. No previously closed clause regressed: the v1.0.9 symbol unification (`c5_pm_stats.bootstrap_paired_v2` at §10.2/§17.3), `manifest_commit: null`, `freeze_manifest_sha256` and txt custody, paired L>F, §4.6 precedence, P0 tail provenance, and the 1,680/560/600/1,204/155 arithmetic are all intact.

## Q5. Final verdict and approval scope

- **판정: NARROW**

Option A is the right architectural choice and it does resolve the Sol/GLM lifecycle contradiction *provided* Phase 6 owns both loops. As written, §17.3 simultaneously forbids `evaluate_arm` and permits reusing `train_arm`, which calls it. An implementer following the reuse clause would silently re-enable legacy `bootstrap_paired`; an implementer following the exclusion would violate the reuse clause. That ambiguity blocks freeze as a single unambiguous implementation authority.

```text
최종 판정: NARROW
v1.0.10 freeze: NO as-is; YES after MF-1..MF-3 (text-only), plan re-hashed, new freeze commit
구현+unit tests: CONDITIONAL (after freeze; contract/decision/M/stats/replay tests only)
D0: CONDITIONAL (after freeze + unit tests; ≤4 configs, 0 updates, ≤15 min, seed 20261111)
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
  - runtime monkeypatch as a substitute for the exclusion
최대 compute: no grant beyond D0; prospective ceiling only ≤1,204 updates / 155 min
  (1,200 registered + 4 D1; D0 ≤15 min; D1 ≤20 min; registered 120-min hard abort; T_proj ≤96 min)
Must-fix (ranked):
  1. MF-1: drop `train_arm` reuse; Phase 6 owns the training loop too
     (frozen train_arm calls evaluate_arm at :723 and supports only frozen/lora).
  2. MF-2: define "Phase 6 path" as the transitive call graph rooted at
     runner/c5_pm_phase6.py, and assert on attribute access, not literal text.
  3. MF-3: add any reused training helper to §17.1, or reference no unfrozen helper.
  4. MF-4 (low): state that P0 is unaffected because P0 uses p0_eval_split.
v1.0.10 self-contained: YES for decision/validity/control/stats/replay/freeze contracts;
  NO for the training-path contract, because §17.3 permits a helper that cannot
  satisfy its own restriction and cannot train P/PA.
잘못된 전제:
  - `a88c714` is not current origin/main HEAD; HEAD is `206117b`, one commit later.
    The only difference is the review harness; reviewed artifact bytes are identical.
  - v1.0.9's split was 2 CONTINUE / 1 NARROW, not unanimous; this round closes the
    lifecycle conflict only if the train_arm clause is removed.
  - `train_arm` in the frozen helper is not training-only: it bundles
    evaluate_arm and generate_arm.
  - P0 remains descriptive native-path sensitivity, not trained P/PA/L calibration.
  - test 163 is sealed, P1 is unused, and no Phase 6 result exists.
```

## 4. Limitations

- No training, evaluation, generation, test-163 read, or P1 read was performed.
- The repository's Python test suite was not executed (not requested for a text review; the default interpreter also lacks `numpy`/`torch`). Golden digests and call-site claims were verified with the standard library, `git`, `grep`, and `sed` only.
- This report is consultation only. It modifies no plan, template, golden vector, provenance file, runner, or test, and does not approve Phase 6 registered training, D1, 3-seed, B0-B, B1/B2, or Stage C.
