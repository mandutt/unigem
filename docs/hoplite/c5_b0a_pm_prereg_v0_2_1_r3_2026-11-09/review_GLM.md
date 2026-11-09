# C5 Phase 6 P/M Prereg v0.2.1-r3 — External Review (GLM 5.3 Flash)

- Reviewer: **GLM 5.3 Flash (max reasoning), via OpenRouter** — independent r3 round. This is not a reuse of the r2 GLM review or of any other model's answer; all verdicts below were derived in this session from the repository artifacts.
- Date: 2026-11-09
- Repository: `mandutt/unigem`, branch `main`, project `proj_2e8de5ed594f47c7b851f1d7c5b52c61`
- Review basis: **origin/main HEAD `fc0d9737e95e3b9952a0176da6e52fd4b40afa13`** (`docs: add C5 P/M v0.2.1-r3 review request`). Sync performed as instructed: `git fetch origin` then `git pull --ff-only origin main` → `Already up to date`. The request cites basis `e779e93`; `git diff e779e93 HEAD -- docs/plan_c5_b0a_pm_prereg_v0_2_1_r3.md` is empty, so the r3 text reviewed here is byte-identical to the request's basis commit.
- Constraints honored: no training or evaluation was run; test 163 was not opened; P1 data was not used; T5Gemma2 D-108 STOP untouched; repository read-only except this single report file; no subagents or additional LLMs were called.

---

## 0. Independent verifications performed (not taken on trust)

1. **Preflight hash recomputed.** SHA256 of `reports/provenance/C5_b0a/m_cohort_preflight.json` = `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`, matching r3 §11 item 6 and the committed sidecar `m_cohort_preflight.sha256`. The stale `07c3…` hash from r2 §12 item 6 appears nowhere in r3.
2. **K rule recomputed from the 40 embedded lengths.** Train h≥753 = 16/20 (`l_contributors_at_k=16`); val h≥753 = 15/20; at K=754 val eligible drops to 14 (`REPORT-news_r-01331-00001` sits at exactly 753). Zero-margin confirmed. The excluded 5 IDs (`00430`, `01127`, `02180`, `02804`, `03445`) match `l_excluded_at_k`. Full-K secondary = 11/20 with 9 excluded listed. `common_ok=true` at 15.
3. **r2 fail-open cells confirmed, then confirmed closed.** In r2 §2.4 `test_split_used=NA` and `pa_step100_path_ok=NA` (with `pa_valid=true`) both fall through to `VALID`; the PA-NA branch does not exist. r3 §3.3/§3.5 add both branches ahead of `VALID`. r3 §3.2 also moves `p_step100_path_ok=false` into the known-failure-first block, so `assay_path_ok=NA` + `p_step100_path_ok=false` → `ASSAY_INVALID` as §3.6 requires.
4. **Signal label reachability walked by hand (r3 §5.3/§5.4).** All labels are reachable; none is dead. In particular `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` is now reachable (validity VALID + p/pa valid + `m_evaluable=false` via cohort/endpoint/seed/replay failure — e.g., a replay mismatch), because validity no longer emits `M_NOT_EVALUABLE`.
5. **Runner state inspected.** `runner/c5_mt5_lora_b0.py` exposes modes {`smoke`, `metric-smoke`, `train`, `p0-sanity`} only — there is no `pm-diagnostic` mode, no P/PA arms, no M builder, and no decision function. This is consistent with r3 §0 ("code is written only after r3 approval"). Two live debts found in existing code that r3's DoD already anticipates: (a) `bootstrap_paired` defaults to seed **20261108** while r3 §9 registers **20261109**; (b) `bootstrap_paired` labels document-level counts as `seeds_positive` (`int((arr > 0).sum())` over per-document deltas) — a live instance of the exact "stale `seeds_positive`" usage the DoD bans. PM statistics must be new code, not a reuse of this helper's labeling.
6. **Replay convention already in code.** The runner's zero-LoRA equivalence check uses `torch.allclose(..., atol=1e-5, rtol=1e-4)`, matching r3 §8.6's replay tolerance — the convention is implementable as written.
7. **P0 cross-checked** against `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md`: train Δcopy +3.7617 CI [1.8917, 5.6050], val +5.2375 CI [2.5013, 8.0753], positive docs 14/20 and 18/20, `SENSITIVE_POSITIVE` (descriptive rule, not a threshold). Median 2.9739 and top-3 share .4862 are request-stated (raw JSON fields, not in the report table).
8. **ln|V| arithmetic coherent.** mT5-small |V| = 250,100 → ln|V| ≈ 12.43; the request's untrained real CE 12.7/13.2 > 12.43 is arithmetically consistent.
9. **"54 tests" is historical evidence only** (r2 synthesis §8). The PM decision function and its tests do not exist yet; nothing in this review is outcome-informed — no trained P/PA/M result has been seen.

---

## 1. Q1 — Total factored contract

**판정: agree (with two minor labeling/notation conditions, see Q8).**

**근거:**

- Validity is total over the 5 path flags × `p_valid` × `pa_valid`. Known failures fire first (§3.2: `assay_path_ok=false`, `p0_path_ok=false`, `test_split_used=true`, `p_step100_path_ok=false` → `ASSAY_INVALID`), then NA fail-closed (§3.3), then P (§3.4), then PA (§3.5), else `VALID`. `VALID` is reachable only when every path flag is explicitly T/F (not NA), `p_valid=true`, `pa_valid=true`, and no path is false — so neither `test_split_used=NA` nor `pa_step100_path_ok=NA` can produce `VALID` (§3.6 requirement met). P-failure-wins over PA states is explicit (§3.5 bullets).
- Control is total and correctly factored. `m_evaluable = AND3(cohort_ok, endpoint_ok, seed_ok, replay_ok)` is availability; P/PA validity is checked separately (§4.2 second branch); `m_valid=false` → `M_CONTROL_INVALID`, `m_valid=NA` → `NOT_ASSESSABLE`, `m_pass_l` T/F/NA → `M_CONTROL_PASS`/`M_CONTROL_FAIL`/`NOT_ASSESSABLE`. Every control cell dispatches; NA anywhere fails closed. `M_CONTROL_NOT_VALID` is absent by design (§4.3).
- `M_NOT_EVALUABLE` is control-only (§3.1, §3.6 last bullet, §4.3) — the r2 dead-label mechanism (validity emitting `M_NOT_EVALUABLE` and swallowing `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` in the `validity != VALID` guard) is structurally removed.
- Signal dispatch (§5.3) covers: n NA → NA; n<15 → four small-N variants; validity ≠ VALID → L/copy-only/full-only validity-invalid labels, else NA; copy-only/full-only WEAK (validity VALID only); `l_signal=NA` → NA; `l_signal=true` → five control-qualified labels; no-L → control-qualified NO_* labels, else NA. No unhandled cell found in a hand walk.

**다음 단계:**

1. Fix the `AND3` arity ambiguity before implementation (MF-R3-1 below) — it is the one item that can produce a silent implementation bug in this otherwise-total contract.
2. Add the §3.6/§4/§5/§6.3 requirement cells as named fixtures in the pure-function test suite (no full Cartesian product; see MF-R3-6).

---

## 2. Q2 — L preservation / signal labels

**판정: agree (one labeling-fidelity condition, MF-R3-2).**

**근거:**

- Raw L flags are always stored (§5.5: `l_copy_signal`, `l_full_signal`, `l_signal` in `flags`; `NOT_ASSESSABLE` also stores `signal_reason`), and every L-bearing state gets an L-qualified label: small-N (`INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL/_WITH_COPY_ONLY/_WITH_FULL_ONLY`), validity-invalid (`L_SIGNAL_VALIDITY_INVALID`, `COPY_ONLY_VALIDITY_INVALID`, `FULL_ONLY_VALIDITY_INVALID`), and control-qualified (`EXPLORATORY_L_SIGNAL`, `L_SIGNAL_M_CONTROL_FAIL/_INVALID/_NOT_EVALUABLE`, `L_SIGNAL_CONTROL_NOT_ASSESSABLE`).
- Dead-label check: `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` requires validity VALID + control `M_NOT_EVALUABLE` + l true. Since validity VALID implies p/pa valid, control `M_NOT_EVALUABLE` in that state can only come from `m_evaluable=false` (cohort/endpoint/seed/replay) — which is reachable (e.g., replay tolerance breach per §8.6). Reachable; not dead. `MEAN_CONTRAST_ONLY` and `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE` now sit strictly behind the validity-VALID guard (§5.3 branch order) — the r2 asymmetry (MF-3) is closed symmetrically for copy-only/full-only/mean/no.
- `EXPLORATORY_L_SIGNAL` requires validity VALID **and** control `M_CONTROL_PASS` (§5.4) — no path leaks an exploratory label from an unassessed or invalid assay.
- Residual: the validity-invalid branch is entered on `validity_status is not VALID`, which includes `validity_status=NOT_ASSESSABLE`. A NA validity (e.g., `test_split_used=NA`) with `l_signal=true` therefore yields `L_SIGNAL_VALIDITY_INVALID` — a label that asserts *invalid* when the truth is *unassessable*. Fail-closed direction is preserved (nothing reaches VALID/EXPLORATORY), but the label overstates what is known. Control distinguishes INVALID vs NA (`M_CONTROL_INVALID` vs `NOT_ASSESSABLE`); signal should too.

**다음 단계:**

1. Split the validity-NA case in §5.3 (add `*_VALIDITY_NOT_ASSESSABLE` variants, or route validity-NA to `NOT_ASSESSABLE` with `signal_reason`) — one text errata line, no threshold change.
2. Add reachability fixtures for each new label if introduced.

---

## 3. Q3 — M preflight / cohort

**판정: agree.**

**근거:**

- K=753 is outcome-blind and length-only: I recomputed 16 train contributors and 15/20 val-eligible from the preflight's own embedded lengths; K=754 → 14 (doc `01331` at exactly 753), so the max-K rule (train≥10 AND val≥15) selects exactly 753 with zero margin (`zero_margin: true`). This is the documented basis for `M_CONTROL_PREFIX753_COHORT15`.
- Cohort separation is now explicit: signal cohort = val20 (§5.1), M cohort = 15 longest-of-20 (§8.1/§8.2), `M_COHORT_MARGIN=0` applies to the M cohort only, and `n_signal` vs M n are recorded as separate fields. This closes the r2 MF-4 confusion.
- Endpoint rule is executable and fail-closed: `endpoint_ok = 15/15 L copy/full AND 15/15 P/PA copy/full`; any missing endpoint → `m_evaluable=false` → `M_NOT_EVALUABLE` (§8.2). The r2 zero-margin drift risk ("one doc missing → n=14") is closed by refusing to lower to 14. The P/PA side is consistent with the preflight (`native_target_eligible_at_512=20`, evaluated on the same 15 common IDs, §8.5).
- full-K 11/20 stays secondary-only and is named as not the M gate (§8.1, preflight `full_k_secondary.note`), so the narrow scope cannot be silently widened.

**다음 단계:**

1. In the implementation, assert `excluded 5` IDs and `n=15` from the frozen preflight at M-build time (fail loudly on any drift rather than re-deriving).
2. Record per-arm endpoint coverage (15/15 L, 15/15 P/PA, copy and full separately) in the artifact.

---

## 4. Q4 — M builder / aggregation / replay

**판정: agree.**

**근거:**

- Builder determinism: `adapter.eval()`, `model.eval()`, `torch.no_grad()`, seed-wise rebuild, 16 train contributors at 753 (L) and 20 at 512 (P/PA), positionwise mean, `M_NORM` rescale (§8.3). Contributors come from train20 only; targets are val — no train/val mixing in M itself.
- `M_NORM` uses the target's own real-prefix Frobenius norm. This touches val data, but only as a per-target scale factor for the memory-free control variant; it cannot leak outcomes into `M_POS_MEAN`, and `M_PASS_NORM_CONFOUNDED` is descriptive-only, not a pass (§8.4).
- Aggregation: seed-average-before-bootstrap (§8.6, §9), 3 seeds × 15 docs not treated as 45 units, false-dominant AND3 for mixed false+NA (§6.2, §8.5) with missingness-first explicitly banned. This closes r2 MF-6's aggregation conflict.
- Replay: separate process, one pass, `atol=1e-5 / rtol=1e-4` on CE, state hash recorded, breach → `m_evaluable=false` / `M_NOT_EVALUABLE` (§8.6). The tolerance matches the convention already exercised in the runner's zero-LoRA equivalence check, so it is realistically implementable.
- `m_pass_l = AND3(m_pass_pos_l, m_pass_norm_l)` is now derived in the inventory (§2.2) and closure map — r2 MF-6's missing derivation is closed.

**다음 단계:**

1. Implement the M builder as a pure function over cached memories where possible so the seed-aggregation test can run without model forwards.
2. Record the final adapter/LoRA checkpoint hash per seed before replay, and the replay process hash, as §8.6 requires.

---

## 5. Q5 — PA

**판정: agree.**

**근거:**

- PA is explicitly an *acquisition control* with random adapter re-basing at step0, its own separate step0 run, and `PA_RETENTION` allowed to be null/uninformative — i.e., a null PA result is interpretable rather than a gate failure (r3 §7.2).
- `PA_STEP100_NOT_VALID` is the only PA-invalid label; `ADAPTER_REGIME_LOSS` is banned by name; the mT5-final-hidden vs EG2-layer19 scale/geometry caveat must be recorded in the artifact. The DoD adds `ADAPTER_REGIME_LOSS` absence and PA step0 random-adapter tests (§13).
- Hyperparameters unchanged from r2 (adapter_lr 1e-3 PA-only, lora_lr 1e-4, 100 updates, batch 1, `train_ids[step % 20]`, clip 1.0, LoRA 64 modules r8 α16 dropout .05, base decoder eval) with the ordering guarantee `make_adapter(seed)` → `torch.manual_seed(seed)` immediately before LoRA init (§7.3).
- P0's 256-source vs registered 512-prefix mismatch is quarantined in §12 (historical native-path sensitivity only; no P0 re-run; P0 numbers are not trained P/PA/L evidence) — the correct epistemic status.

**다음 단계:**

1. In the PA artifact, store the step0 random-adapter hash and the step100 adapter hash so "acquisition happened" is auditable without rerunning.

---

## 6. Q6 — Cap / D0 / D1

**판정: conditional.**

**근거:**

- Arithmetic checks out: registered = 12 units × 100 = 1,200 updates, 2 h wall, 6 threads, no GPU, no retry (§10.1); 4 arms × 3 seeds = 12 units is internally consistent. D0 = 0 updates, ≤4 configs, ≤15 min, seed 20261111, `labels_computed:false`, `not_a_result:true`, explicitly not a timing basis (§10.2). D1 = 4 arm-seeds × 1 update, ≤20 min, separate approval, five timed phases enumerated, no outcome labels (§10.3). D0-only projection banned; no 3-seed without D1 (§10.4) — this closes the r2 "separately approved timing probe" loophole by deleting the option (§10.4 last bullet).
- Projection formula `T_proj = 3 · Σ_arm(100·t_train + t_step0_eval + t_step100_eval + t_M_build + t_replay)`: the ×100 and ×3 scales are correct, and the gate `≤0.8×2h = 96 min` is arithmetically right. M-build timing is consistent (D1 times 15 docs; registered M is 15 docs).
- **Residual gap (MF-R3-3):** the eval phases have no count scale. D1 times "step0 eval on one doc subset" and "final eval on one doc subset" (§10.3), but r3 never states the registered run's eval cohort size, so the projection implicitly assumes D1's subset equals the registered eval set. If D1 times a 1-doc subset and the registered eval runs on 20 docs, `t_step0_eval`/`t_step100_eval` are understated up to ~20× and T_proj can pass the 96-min gate while the real run hits the 2-h cap. The cap-abort (§10.5, no retry) bounds the damage to wasted compute, not to validity — which is why this is conditional, not a structural defect.

**다음 단계:**

1. State the registered eval doc counts (step0, step100, per arm) in §10.4, or normalize eval timing per document and multiply by the registered count in T_proj.
2. Add checklist items asserting D0/D1 artifacts carry `labels_computed:false` and `not_a_result:true` (defined in §10.2/§10.3 but not enforced by §11's list).

---

## 7. Q7 — Statistics

**판정: agree (one implementation-debt condition, MF-R3-5).**

**근거:**

- Constants are complete and executable: n_boot=1,000, percentile 2.5/97.5, bootstrap seed 20261109, unit=document, seed-average-before-bootstrap, `per_doc_delta[doc] = mean over seeds`, `documents_positive = count(per_doc_delta > 0)`, `seeds_positive = count(seed_mean > 0)` with the explicit ban on using seed counts as document counts (§9). `L>F` is a paired per-document difference; top-3 share with null denominator guard; leave-top3-out mean; `tail_driven` as a non-label-changing flag; 20-doc CI anti-conservatism flagged; `MARGINAL_SIGNAL_COHORT` as a non-label-changing flag.
- **Debt:** the existing runner's `bootstrap_paired` defaults to seed 20261108 and mislabels per-document positive counts as `seeds_positive`. The DoD's "stale `seeds_positive` 사용 금지 test" covers this, but the PM statistics module must be written fresh with the registered seed 20261109 and `documents_positive`, not adapted from the P0 helper. (20261109 is also registered-seed #2 for training; different use, no conflict — but the statistics manifest should record the bootstrap seed explicitly.)

**다음 단계:**

1. New statistics module with the registered constants hardcoded as named constants; unit tests for `documents_positive` vs `seeds_positive` on synthetic per-doc/per-seed arrays.
2. Assert `bootstrap_seed=20261109` appears in the run manifest (checklist addition).

---

## 8. Q8 — Remaining Must-fix (ranked) / new r3 issues

All six r2 Must-fix items are closed in text (verified against r2 §2.4/§4/§6.2/§12 and r3 §3/§4/§5/§8/§10/§11/§12/§15). Remaining items, ranked by implementation risk:

1. **MF-R3-1 — `AND3` arity (notation, can cause silent bugs).** r2 §3 defines AND3 as a 3-input operator, but r3 applies it to 2 inputs (`m_pass_l`, `copy_only`), 4 inputs (`m_evaluable`, `m_valid`), and r2 used 5. Semantics are unambiguous (false-dominant n-ary), but a literal 3-input implementation truncates. Fix: one line — "AND3(…) denotes the n-ary false-dominant AND; any false → false, else any NA → NA, else true" — plus an n-ary unit test. Carried from r2, still unfixed in r3 text.
2. **MF-R3-2 — validity-NA conflated with validity-invalid in signal labels** (new in r3): `validity_status=NOT_ASSESSABLE` routes to `*_VALIDITY_INVALID` labels. See Q2. Fix: split or relabel; add fixtures.
3. **MF-R3-3 — projection eval-phase scaling undefined** (new in r3): D1 "one doc subset" vs registered eval cohort size unstated. See Q6. Fix: state counts or per-doc normalization.
4. **MF-R3-4 — `n_signal` fixture domain incomplete:** §6.1 enumerates {NA, 0, 14, 15, 20}, but 16–19 are reachable (a val20 subset with missing copy/full endpoints). Fix: extend the fixture domain to 0–20 (contract logic unaffected; n≥15 vs n<15 is the only branch).
5. **MF-R3-5 — statistics implementation debt:** runner `bootstrap_paired` (seed 20261108 default; `seeds_positive` mislabeling of document counts) must not be reused for PM; DoD test should assert the new module's constants explicitly.
6. **MF-R3-6 — "exhaustive truth table" is unexecutable as a literal Cartesian product:** the §6 input space is 3¹⁷-scale; the DoD item needs a defined strategy — per-axis exhaustive (all T/F/NA values per flag) + all named requirement cells from §3.6, §4, §5, §6.3 + randomized cross-product sampling — written into the test plan before code.

New r3 issues beyond the above: none structural found. The r2→r3 changes introduced no fail-open path; the two new labels' reachability holds; cohort/endpoint tightening is fail-closed.

---

## 9. Q9 — Freeze + implementation approval

**판정: conditional (approve freeze + implementation + unit tests + D0, with MF-R3-1…6 resolved as text errata or as binding acceptance fixtures before code review).**

**근거:** r3 closes all six r2 Must-fix items as text (closure map §1/§15 verified line-by-line against r2); the contract is total and fail-closed (Q1); preflight, cohort, statistics, D0/D1 accounting are executable and independently re-verified. The residual items are notation/labeling/projection-precision issues, none touching threshold, seed, cohort, donor, step, or LR. None requires post-result changes.

**구현 전 필수 test/contract (pre-code requirements):**

1. Pure decision function, no model/data imports; synthetic fixtures only (§6.3).
2. Per-axis exhaustive tri-state tests + named requirement cells (MF-R3-6 strategy) covering: NA fail-closed for all five path flags; `M_NOT_EVALUABLE` control-only; `M_CONTROL_INVALID` reachable (p/pa valid + m_valid false); `m_pass_l` derivation; `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` reachable; signal validity guard symmetry (WEAK/MEAN/NO_AFFIRMATIVE never with validity ≠ VALID); L preservation in `flags` for every signal label; small-N precedence; val20 vs M-15 separation; endpoint 15/15 → M_NOT; cohort 15/20; false-dominant mixed false+NA; `M_CONTROL_NOT_VALID` and `ADAPTER_REGIME_LOSS` absence; `test_split_used:false` assertion.
3. Statistics module tests (bootstrap seed 20261109, `documents_positive`/`seeds_positive` separation, top-3 share null guard).
4. n-ary AND semantics test (MF-R3-1).

---

## 10. Q10 — D1 / 3-seed boundary

**판定: conditional → 판정: conditional.**

**근거:** the boundary is now well-defined and adequate: D1 is required for the 3-seed timing projection and banned as a substitute for it (`D0-only projection 금지; D1 없이 3-seed 금지`, §10.4); D1 remains separately approved (§10.3); the "separately approved timing probe" loophole from r2 §11.3 is deleted; D1/D0 results are explicitly not 3-seed results (§10.5). Checklist item 5 (D1 artifact) + item 12 (projection ≤96 min) enforce the dependency at launch.

Checklist gaps (small): (a) no item asserts D0/D1 artifacts carry `labels_computed:false` / `not_a_result:true`; (b) no item asserts the statistics manifest records `bootstrap_seed=20261109`; (c) no item records the D1-vs-registered eval doc counts used in the projection (ties to MF-R3-3); (d) item 6 could additionally require re-verifying the preflight hash at launch time (not just referencing it).

**다음 단계:** add (a)–(d) to §11 as items 18–21 (they are audit lines, not new gates).

---

## 11. Q11 — B0-B boundary

**판정: agree.**

**근거:** §14 keeps the hard boundary — no Phase 6 label auto-approves B0-B/B1/B2/Stage C; full-K 11/20, P0, and `PA_RETENTION` are excluded as B0-B evidence; separate prereg/approval is a predicate conjunct. Dropping r2's explicit `m_valid == true` conjunct is safe because `M_CONTROL_PASS` entails it (control PASS requires m_evaluable true, p/pa valid, m_valid not false and not NA, m_pass_l true).

**B0-B predicate restated in r3 labels:**

```text
B0-B candidate (requires separate prereg + explicit user approval):
  validity_status  == VALID
  AND control_status == M_CONTROL_PASS          # entails m_valid == true
  AND signal_status == EXPLORATORY_L_SIGNAL     # the only exploratory label
  AND cohort scope stated: M_CONTROL_PREFIX753_COHORT15 (15 longest-of-20, K=753; NOT full-real-K)
  AND MARGINAL_SIGNAL_COHORT flag recorded (n_signal margin reported)
  AND tail_driven == false (or explicitly reported as tail-driven)
  AND leakage/mode/metric pass (test_split_used:false; base decoder eval; LoRA/adapter-only trainables)
  AND artifacts complete (manifest, checkpoint hash, replay hash, D1 timing, T_proj ≤ 96 min)
  AND separate prereg document + explicit user approval
```

Nothing in r3 short-circuits this predicate; `EXPLORATORY_L_SIGNAL` alone is insufficient by construction (§14 first bullet).

**다음 단계:** carry this restated predicate verbatim into the future B0-B prereg; do not weaken the scope statement.

---

## 12. Q12 — Final verdict

**최종 판정: CONTINUE (conditional).** r3 genuinely closes the r2 holes; the remaining items are precision fixes that should land before code, not another full review round.

```text
최종 판정: CONTINUE (conditional)
r3 동결:      APPROVED, conditional on folding MF-R3-1…4 into a short r3.1 errata
              (or binding acceptance fixtures) BEFORE code is written.
              No threshold/seed/donor/step/LR/cohort change is involved.
구현+unit tests: APPROVED under the §13 DoD plus the Q9 pre-code test list,
              after the r3.1 errata lands. Pure decision function + synthetic
              fixtures; CPU only; no training.
D0:           APPROVED as specified: 0 updates, ≤4 configs, ≤15 min wall,
              seed 20261111, labels_computed:false, not_a_result:true,
              outside the registered cap.
D1:           NOT APPROVED this round — separate approval after D0 passes and
              unit tests are green, with MF-R3-3 resolved (eval doc counts).
3-seed:       NOT APPROVED this round — separate gate after D1; requires
              checklist §11 (items 1–17 + proposed 18–21) and T_proj ≤ 96 min.
금지 범위:     test 163 (sealed); P1 data; T5Gemma2 (D-108 STOP); B0-B/B1/B2/
              Stage C auto-approval; post-result threshold/seed/donor/step/LR
              changes; missingness-first aggregation; `ADAPTER_REGIME_LOSS`;
              reusing P0's bootstrap helper (seed 20261108 / seeds_positive
              mislabel) for PM statistics.
최대 compute:  implementation+tests: CPU-only, no model training (existing local
              mT5-small test suite style). D0: ≤15 min × ≤4 configs, 6 threads,
              CPU. D1 (if later approved): ≤20 min, 4 arm-seeds × 1 update.
              Registered 3-seed (if later approved): 1,200 updates, ≤2 h wall,
              6 threads, no GPU, no retry, gated by T_proj ≤ 96 min from D1.
              Nothing beyond these without new approval.
Must-fix (ranked): MF-R3-1 AND3 n-ary semantics; MF-R3-2 validity-NA signal
              labels; MF-R3-3 projection eval-phase scaling; MF-R3-4 n_signal
              fixture domain 0–20; MF-R3-5 fresh statistics module (seed
              20261109, documents_positive); MF-R3-6 truth-table fixture strategy.
잘못된 전제:   (1) The request's basis `e779e93` vs actual synced HEAD `fc0d9737`
              — r3 text is identical between them, so no review drift, but the
              request should cite the current HEAD next round.
              (2) "exhaustive truth table" cannot mean the full Cartesian
              product — it needs the MF-R3-6 strategy to be executable.
              (3) D1's "one doc subset" cannot be projected onto the registered
              run without stated eval doc counts (MF-R3-3).
```

test 163 status: **sealed, untouched, unused** — unchanged by this review. No trained P/PA/M result exists; nothing here is outcome-informed.

---

## 13. Answer-format compliance (§6 of the request)

Each Q above carries 판정 (agree / disagree / conditional / defer), 근거 tied to specific r3 sections, preflight values, runner code, or request numbers, and 1–3 next steps. Final verdict block per §6 is in §12 of this report.