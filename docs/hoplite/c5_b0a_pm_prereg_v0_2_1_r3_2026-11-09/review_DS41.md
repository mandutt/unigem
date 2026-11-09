# C5 Phase 6 v0.2.1-r3 — Independent External Review

**Reviewer: DeepSeek 4.1 Flash 1017 (OpenRouter), reasoning max.** This is a new,
independent r3 review round. It is not a duplicate of the r2 NARROW round and does
not reuse any other reviewer's answer.

- 작성일: 2026-11-09
- Repository: `mandutt/unigem`, branch `main`
- Review basis (after sync): HEAD **`fc0d9737e95e3b9952a0176da6e52fd4b40afa13`**
  (`docs: add C5 P/M v0.2.1-r3 review request`)
  - `git fetch origin` → rc=0; `git pull --ff-only origin main` → rc=0
    (`Already up to date.`)
- Preflight hash verified in both places:
  - worktree file: `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af`
  - committed blob (`git show HEAD:...`): same
  - matches `reports/provenance/C5_b0a/m_cohort_preflight.sha256` and r3 §11 item 6
- test 163: **sealed** (not opened). P1: **unused**. External APIs: **unused**.
  Training/evaluation: **not run**. Subagents/other LLMs: **not called**.
  T5Gemma2: **D-108 STOP** treated as closed. Repository writes: only this file.

Read in full for this review: the r3 review request; `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3.md`
(795 lines) and r2 (770 lines); `reports/C5_B0A_PM_PREREG_V0_2_1_R2_3AI_REVIEW_SYNTHESIS_2026-11-09.md`;
`reports/provenance/C5_b0a/m_cohort_preflight.json` (+ `.sha256`);
`reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md` and the raw `p0_native_sanity.json`;
`runner/c5_mt5_lora_b0.py`; `eval/tests/test_c5_b0_metric.py`. Because r3's precedence
chain is documented as `r3 > r2 > r1 > v0.2.1 > v0.2`, I also read the v0.2.1 errata
(`plan_c5_b0a_pm_prereg_v0_2_1_errata.md`) and r1 sections that carry definitions r3
inherits (L-signal criteria, M_NORM rules, statistics).

Independence note: the r2 synthesis is mandated reading in the review request and was
read. No r2 reviewer file and no r3 peer output was read. A few earlier-round review
lines surfaced incidentally in broad `grep` output; they were not used as evidence.

---

## 0. Bottom line

> **The six r2 3-AI Must-fix items are structurally closed by r3** (verified cell-by-cell
> below), and the factored contract is total. A small set of text/test-contract residuals
> remains (ranked in §13); none of them changes a threshold, seed, donor, step, or LR, and
> none re-opens an r2 hole. **Verdict: CONTINUE** — approve r3 freeze, implementation +
> unit tests, and D0 zero-update mechanics debug, with the ranked items attached as
> pre-implementation test/contract items. D1, 3-seed, the registered Phase 6 run, and
> B0-B/B1/B2/Stage C remain **not approved**.

---

## 1. Direct verification performed (evidence)

| # | Check | Result |
|---|---|---|
| V1 | Validity dispatch totality (§3.2–3.5) for `{assay_path_ok, p0_path_ok, p_step100_path_ok, pa_step100_path_ok, test_split_used, p_valid, pa_valid} ∈ {T,F,NA}⁷` | Every assignment yields exactly one of `ASSAY_INVALID / P_STEP100_NOT_VALID / PA_STEP100_NOT_VALID / NOT_ASSESSABLE / VALID`; known failures precede NA; `test_split_used=NA` and `pa_step100_path_ok=NA` can no longer yield `VALID`; `validity_status` never returns `M_NOT_EVALUABLE` (§3.1, §3.6). r2 MF-1 closed. |
| V2 | Control dispatch totality (§4.1–4.2) | `m_evaluable not true → M_NOT_EVALUABLE` (covers false and NA); `p_valid/pa_valid not true → M_NOT_EVALUABLE`; then `m_valid false → M_CONTROL_INVALID`, `NA → NOT_ASSESSABLE`, `m_pass_l ± → PASS/FAIL`, else NA. `M_CONTROL_INVALID` and `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` are reachable (r3 §6.3 stated; confirmed by case walk). r2 MF-2 closed. |
| V3 | Signal dispatch totality (§5.1–5.3) | Order: `n_signal NA → NA`; `<15 → 4 small-N labels`; `validity_status ≠ VALID → L/COPY/FULL validity-invalid labels else NA`; `copy_only/full_only`; `l_signal NA → NA`; `l_signal true/false × control`. No cell is undefined; `EXPLORATORY_L_SIGNAL` requires validity `VALID` + control `M_CONTROL_PASS`; partial NA (copy T, full NA) gives `l_signal=NA → NOT_ASSESSABLE` with raw flags stored. r2 MF-3 closed. |
| V4 | Dead-label / reachability walk over all §5.3 labels | No dead label found; the r2-dead `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` is now reachable (validity `VALID` + control `M_NOT_EVALUABLE` + `l_signal=true`). |
| V5 | K_M_L recomputation from `m_cohort_preflight.json` length tables | `#train(h≥753)=16`; `#val(h≥753)=15`; `#val(h≥754)=14`; medians 768.5 / 766.5; `common_ids` lists exactly 15 IDs; excluded 5 are the five shortest val docs. K=753 is the maximum K satisfying `train≥10 ∧ val≥15` (counts are non-increasing in K). `k_selection.next_k_target_eligible=14` confirmed. |
| V6 | Hash / checklist | `3ee3f1ca…` equals worktree, committed blob, and `.sha256` file. Item 6 no longer stale; item 9 is a computation contract, not a prelaunch truth value (§11, notes). r2 MF-5 closed. |
| V7 | "54 tests pass historically" | Counted `def test_`: 2+1+7+11+10+11+12 = **54** across `eval/tests/` (7 in `test_c5_b0_metric.py`). No PM decision-function tests exist yet. |
| V8 | P0 raw statistics recomputed from `p0_native_sanity.json` per-doc deltas | val20: mean Δcopy +5.2375, median **2.9739**, top-3 share **0.4862**, n=20 — matches the request's figures exactly; train20: median 4.0680, top-3 share 0.4222. Real copy CE 13.2352 (val) / 12.7022 (train) vs ln|V|≈12.43 for mT5's 250,112-token vocabulary (model files not present in this checkout, so the vocab value is cited from mT5's standard config, not re-read locally). |
| V9 | Runner hazards relevant to implementation | `copy_ce` returns `None` when `<5` copy tokens (`runner/c5_mt5_lora_b0.py:311-315`); `bootstrap_paired` default seed is **20261108** (`:384`) and its `seeds_positive` field counts *documents* (`:395`); P0 default source length 256 (`:766`). These are code-time constraints for the future PM implementation, not r3 text errors. |

---

## 2. Q1. Total factored contract

- **판정: conditional.**
- **근거:**
  - Totality: verified by exhaustive case walk (V1–V4). The three functions compose
    pairwise-consistently: signal consults validity and control; control consults
    `m_evaluable`, `p_valid/pa_valid`, `m_valid`, `m_pass_l`; validity consults only
    assay/P/PA flags. `validity_status` cannot emit `M_NOT_EVALUABLE` (§3.1/§3.6), and
    `M_CONTROL_INVALID` covers all `(m_evaluable=true, p/pa valid, m_valid=false)` cells
    (§4.2/§6.3).
  - NA fail-closed: `test_split_used=NA`, `assay_path_ok=NA`, `p0_path_ok=NA`,
    `p_step100_path_ok=NA` → `NOT_ASSESSABLE`; `assay_path_ok=NA` + `p_step100_path_ok=false`
    → `ASSAY_INVALID` (§3.2 before §3.3); `pa_step100_path_ok=NA` → `NOT_ASSESSABLE`
    (§3.5). Correct precedence.
  - Executability residuals (both cheap, both pre-results decisions):
    (i) §6.1 enumerates `n_signal ∈ {NA,0,14,15,20}`, but the dispatch predicate is
    `n_signal < 15` vs `≥15`, so any count 0–20 is semantically well-defined while the
    "exhaustive truth table" test spec covers only an arbitrary subset. Extend the
    enumerated domain to `NA ∪ {0..20}` (or declare `n_signal ∈ ℕ∪{NA}`).
    (ii) "endpoint valid" is used as a gate (§4.1, §8.2) but never defined. Fix the
    criterion to the code contract: copy endpoint valid ⇔ copy CE computable (≥5 copy
    tokens, finite) per `copy_ce`; full endpoint valid ⇔ finite full CE; otherwise
    "missing" → `endpoint_ok=false → m_evaluable=false → M_NOT_EVALUABLE`.
- **다음 단계:** (1) extend the §6.1 input domain; (2) add the endpoint-valid
  definition to §4.1/§8.2; (3) implement the pure decision function with an exhaustive
  truth-table test over the extended domain (per §13 DoD).

## 3. Q2. L preservation / signal labels

- **판정: agree.**
- **근거:**
  - Every `l_signal=true` path emits an L-qualified label (`EXPLORATORY_L_SIGNAL`,
    `L_SIGNAL_M_CONTROL_FAIL/_INVALID/_NOT_EVALUABLE`, `L_SIGNAL_CONTROL_NOT_ASSESSABLE`,
    `INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL`); the r2 hole where an invalid validity silently
    produced `EXPLORATORY` is closed by placing the `validity_status ≠ VALID` branch
    before the control branches (§5.3), with new `L_SIGNAL_VALIDITY_INVALID`,
    `COPY_ONLY_VALIDITY_INVALID`, `FULL_ONLY_VALIDITY_INVALID` labels (§5.4).
  - `copy_only`/`full_only` can only be true when the opposite flag is explicit false
    (`AND3(l_copy, NOT3(l_full))`), so partial NA collapses to `l_signal=NA` and lands in
    `NOT_ASSESSABLE` (`n≥15`) or a small-N label — never a false "no L" claim. Raw flags
    are always stored (§5.5), and even `NOT_ASSESSABLE` keeps `signal_reason` + raw flags.
  - `MEAN_CONTRAST_ONLY` / `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE` are now gated to
    validity `VALID` (§5.3/§5.4), matching the r2 MF-3 request.
  - Dead-label check (V4): zero dead labels. `L_SIGNAL_M_CONTROL_NOT_EVALUABLE` is
    reachable in the intended cell (validity `VALID`, control `M_NOT_EVALUABLE`,
    `l_signal=true`).
  - One accepted nuance: small-N + partial NA collapses to generic
    `INCONCLUSIVE_SMALL_N`; this is fail-closed and the raw flags still preserve L, so it
    is not a distortion.
- **다음 단계:** (1) implement L-preservation tests including partial-NA
  (copy T / full NA) and non-enumerated `n_signal` (e.g., 13, 17); (2) assert all labels
  reachable at least once on synthetic fixtures; (3) assert raw flags are never mutated.

## 4. Q3. M preflight / cohort

- **판정: agree (with the endpoint-criterion nit from Q1).**
- **근거:**
  - Independently recomputed from the preflight length tables (V5): K_M_L=753 is the
    maximum K with train contributors ≥10 (16 at 753) and val eligible ≥15 (15 at 753;
    K=754 → 14). The rule is outcome-blind (length-only, no model forward —
    `data_only:true, no_model_forward:true` in the JSON).
  - Common cohort = 15/20 with the exact ID list; excluded 5 = the five shortest val h
    (751, 728, 708, 750, 718); zero-margin is explicit (`cohort_ok = 15/20`,
    `zero_margin:true`). Endpoint rule is fail-closed: any missing endpoint →
    `m_evaluable=false → M_NOT_EVALUABLE`, and "M copy endpoint n을 14로 낮추지 않는다"
    (§8.2) — this closes the r2 MF-4 zero-margin concern.
  - Signal cohort (val20) and M cohort (15 longest-of-20) are separate and separately
    recorded (§5.1, §8.1–8.2, §11 item 11). Full-K L 11/20 is secondary only and not a
    gate (§8.1, §14); P/PA targets are 20/20 only because native source is truncated at
    512 for every doc (preflight `val_native_lengths` all 512) — the P/PA "512" is a
    truncation cap, not a length-selected cohort, which is consistent and acknowledged
    (§12). The binding constraint is L's 15.
  - Residual: define "endpoint valid" (Q1.ii) so the builder and an auditor compute
    `endpoint_ok`/`n_signal` identically.
- **다음 단계:** (1) add the endpoint-valid criterion; (2) test: one synthetic missing
  endpoint → `m_evaluable=false`; 14 valid endpoints → `M_NOT_EVALUABLE`, never a pass;
  (3) keep `M_CONTROL_PREFIX753_COHORT15` scope in every report.

## 5. Q4. M builder / aggregation / replay

- **판정: conditional.**
- **근거:**
  - Builder: `adapter.eval()`, `model.eval()`, `torch.no_grad()` (§8.3 step 1);
    train-only contributors (L: 16 docs with `h_len ≥ 753`; P/PA: 20 docs) — no val,
    donor, or cross-arm memory enters the mean; `M_POS_MEAN` positionwise mean;
    `M_GLOBAL` secondary; `M_NORM` scale-matched (§8.3; errata §3.2/§3.5).
  - Aggregation: `m_pass_l = AND3(m_pass_pos_l, m_pass_norm_l)`, `m_valid = AND3(P/PA
    POS/NORM)`, mixed false+NA = false-dominant, no missingness-first (§8.5); per-target
    deltas averaged over seeds *before* document bootstrap; 3×15 is never treated as 45
    independent units (§8.6; statistics §9).
  - Replay: separate process, checkpoint/state hashes recorded, CE `atol=1e-5`,
    `rtol=1e-4`, overflow → `m_evaluable=false / M_NOT_EVALUABLE` (§8.6).
  - Residual (text carry-over): r3 §8.3 step 6 restates the M_NORM formula but drops the
    errata's two binding qualifiers — errata §3.5 "whole `K×512` Frobenius norm;
    per-row norm secondary only" and errata §3.2.7 "zero/non-finite norm →
    `M_NOT_EVALUABLE`". Because r3 is the top-precedence document for M, a reader of r3
    alone could implement per-row scaling or omit the guard. Restate these in §8 or
    incorporate them by explicit reference. Also keep the honest label that M_NORM uses
    the real target norm (magnitude-matched control, not strictly target-independent).
- **다음 단계:** (1) restate/cross-reference the Frobenius + zero-norm guard; (2) unit
  test whole-matrix scaling and zero/non-finite → `M_NOT_EVALUABLE`; (3) leakage assert
  that val/donor IDs are absent from the builder inputs.

## 6. Q5. PA

- **판정: agree (one minor wording restoration).**
- **근거:**
  - PA is fixed as an **acquisition control** (native memory + random adapter + decoder
    LoRA), step0 random re-basing run separately, `PA_RETENTION` explicitly
    null/uninformative and **not a gate** (§7.2; errata §2.3); `PA_STEP100_NOT_VALID`
    used for both path and validity failure; `ADAPTER_REGIME_LOSS` is not used
    (§7.2, §3.5); P=LoRA-only and P step0 = native memory + zero-LoRA are separated from
    PA (§7.1–7.3; errata §2.2).
  - Scale/geometry caveat is present ("mT5 final hidden vs EG2 layer19 scale/geometry
    caveat", §7.2) — but r2 §8.2 required this to be **recorded in the artifact**
    ("caveat를 artifact에 기록"), and r3 dropped that clause. Since r3 supersedes r2 on
    conflict, restore the recording requirement to keep it binding.
- **다음 단계:** (1) restore "record in artifact"; (2) PA step0 random-adapter and
  zero-LoRA tests; (3) keep `PA_RETENTION` descriptive-only in DoD.

## 7. Q6. Cap / D0 / D1

- **판정: conditional (arithmetic and boundaries correct; one D1 definition gap).**
- **근거:**
  - Registered: 4 arms × 3 seeds = 12 trained units; 12×100 = 1,200 updates; 2h cap
    (§10.1). Projection: `T_proj = 3·Σ_arm(100·t_train + t_step0 + t_step100 + t_M_build
    + t_replay) ≤ 96min` = 0.8×2h (§10.4) — arithmetic consistent; `3` = seeds,
    `100` = registered updates, per-arm terms measured in D1.
  - D0: 0 optimizer updates, ≤4 configs, ≤15min, seed 20261111, `labels_computed:false`,
    `not_a_result:true`, not timing evidence (§10.2). D1: 4 arm-seeds ×1 update, shared
    seed 20261111, ≤20min, no outcome labels, separate approval, and the former
    "separately approved timing probe" loophole is removed — D1 only (§10.3–10.4).
  - Checklist arithmetic matches: item 5 = D1 timing artifact (no substitute), item 7 =
    debug seed ∉ {20261108, 20261109, 20261110}, item 12 ≤96min (§11).
  - Residual: §10.3 lists the five timed phases once while §10.4 sums them **per arm**.
    State explicitly that each of the four D1 runs measures all five phases, and define
    `t_M_build`/`t_replay` for an arm that runs no M builder (or measure it anyway), so
    the projection is well-defined. Minor: errata §6.1 said debug is *included* in the
    2h/units/updates; r2/r3 account D0/D1 *separately* — add one line reconciling the
    accounting (bounded either way: ≤35 extra minutes, 4 extra updates).
- **다음 단계:** (1) add the per-arm phase sentence; (2) reconcile the cap-accounting
  line; (3) freeze the D0/D1 seed exclusion in the checklist (already item 7).

## 8. Q7. Statistics

- **판정: conditional (constants correct; two implementation musts).**
- **근거:**
  - `n_boot=1000`, percentile CI 2.5/97.5, `bootstrap_seed=20261109`, unit=document,
    seed-average-before-bootstrap, `documents_positive`, `seeds_positive =
    count(seed_mean>0)`, top-3 share = `sum(top3)/sum(all)` with null on zero/non-finite
    denominator, leave-top-3-out mean, `tail_driven = leave_top3_mean ≤0 or share >.50`
    as a non-gating flag, `MARGINAL_SIGNAL_COHORT` as a non-label-changing flag (§9;
    errata §4.2/§4.5). `L>F` is the paired per-document difference, and the L-signal
    criteria live in errata §4.3 (`≥.05` / CI lower >0 / paired L−F mean >0 / 2-of-3
    seeds >0) — r3 §9 references `seeds_positive` and the paired difference but does not
    restate the 2-of-3-seed clause; precedence keeps it binding, but a freeze-time
    reference would remove ambiguity.
  - Implementation musts (V9): the runner's `bootstrap_paired` defaults to seed
    **20261108** and its `seeds_positive` field actually counts *positive documents*
    (`runner/c5_mt5_lora_b0.py:384-397`). PM statistics code must pass
    `bootstrap_seed=20261109` and compute `seeds_positive` as the number of positive
    *seed means* (never reuse that field). The DoD already demands a stale
    `seeds_positive` test; add an explicit seed assertion.
  - P0 heavy-tail context (V8): val top-3 share 0.4862 sits just below the `tail_driven`
    threshold .50, median 2.9739 < mean 5.2375 — report the tail flag per §9, don't
    change any threshold (P0 is descriptive, not a result).
- **다음 단계:** (1) add DOF tests: `bootstrap_seed==20261109`; `seeds_positive` from
  seed means only; (2) reference errata §4.3 in §9 or restate the 2-of-3-seed rule;
  (3) keep `documents_positive` and `seeds_positive` in separate fields.

## 9. Q8. Remaining Must-fix / what r3 newly created

- **판정: r2 Must-fix = fully closed (6/6); 6 residual items, none structural.**
- **근거 (r2 closure, verified):**
  - MF-1 NA fail-open → closed (§3.2/§3.3/§3.6; V1).
  - MF-2 `M_NOT_EVALUABLE` dead label → closed (§3.1 removal; §4 control-only; V2/V4).
  - MF-3 signal validity-guard asymmetry → closed (§5.3/§5.4; V3).
  - MF-4 signal/M cohort + endpoint → closed (§5.1, §8.1–8.2; V5).
  - MF-5 stale hash + circular M_VALID → closed (§11 items 6/9; V6).
  - MF-6 D1 timing/seed/projection, P0 256/512, `m_pass_l` derivation, mixed false+NA →
    closed (§10.3–10.5, §12, §2.2/§8.5, §6.2/§8.5).
- **New problems created by r3:** none of r2 severity. The reordering
  (validity-before-copy-only) and label additions are upward-compatible; the §14
  removal of the redundant `m_valid==true` conjunct is safe because
  `control_status=M_CONTROL_PASS` implies `m_valid=true` by the §4.2 dispatch.
- **Ranked residual list:**
  1. **Endpoint-valid criterion undefined** (§4.1, §8.2) — gate-relevant (zero-margin
    15/15). Fix by tying it to the `copy_ce`/finite-CE contract.
  2. **Statistics wiring** — `bootstrap_seed=20261109` and `seeds_positive` semantics
     must be enforced in code (V9); errata §4.2 already prohibits misuse.
  3. **D1 per-arm phase definition** (§10.3 vs §10.4) — needed for the ≤96min gate.
  4. **`n_signal` truth-table domain** (§6.1) — extend to `NA ∪ {0..20}` for a truly
     exhaustive test.
  5. **M_NORM Frobenius + zero/non-finite guard** — errata §3.5/§3.2.7 binding but
     silent in r3 §8; restate or cross-reference (top-precedence doc).
  6. **Minor wording** — restore the PA scale/geometry "record in artifact" clause
     (r2 §8.2 → r3 §7.2 dropped); add a one-line D0/D1-vs-errata cap-accounting note.

## 10. Q9. Freeze / implementation approval

- **판정: conditional yes.**
- **근거:** All r2 Must-fix items are closed (V1–V6); the contract is total and its M
  statistics/preflight are pinned by data-only preflight + hash; the D0 gate is
  mechanics-only (0 updates, no labels) so the residual items above cannot leak into
  any result-bearing computation before the implementation review. No trained P/PA/M
  result exists (and none is requested by this round).
- **Required pre-implementation test/contract items:** (1) exhaustive pure-function
  truth table over the extended domain incl. `n_signal ∈ NA∪{0..20}`; (2) endpoint-valid
  criterion + missing-endpoint → `M_NOT_EVALUABLE` tests; (3) L-preservation incl.
  partial NA; (4) `m_pass_l`/`m_valid`/`M_CONTROL_INVALID` tests; (5) M_NORM Frobenius
  and zero/non-finite guard test; (6) replay equality and seed-aggregation tests;
  (7) statistics tests: bootstrap seed 20261109, `seeds_positive` from seed means,
  `documents_positive` separate; (8) D0 asserts `labels_computed:false`,
  `not_a_result:true`, 0 updates, seed 20261111, ≤4 configs.
- **다음 단계:** (1) freeze r3 (hash at this HEAD) with items 1–6 in §9 attached
  either as text-only errata (no constant change) or as implementation-review
  conditions; (2) implement the decision function + tests first; (3) run D0 and
  record the artifact before any D1 request.

## 11. Q10. D1 / 3-seed boundary

- **판정: conditional (separation adequate; checklist additions recommended).**
- **근거:** D1 is separately approved, seeded 20261111, ≤20min, no labels, and is the
  only accepted basis for the 3-seed timing projection (§10.3–10.4). The 3-seed launch
  checklist keeps: r3 freeze hash, code hash, all-green unit tests, D0 artifact, D1
  artifact, preflight hash + 15/20 cohort, seed exclusion, no post-freeze
  threshold/seed/donor/step/LR diff, M_VALID as computation contract, cohort-scope
  note, signal/M separation, ≤96min projection, manifest, replay hash, explicit user
  approval, test-163/P1 exclusion, and no auto-approval of B0-B/B1/B2/Stage C (§11).
- **Missing items to add:** (1) bootstrap seed 20261109 pinned in code/manifest;
  (2) L_COPY/L_FULL signal criteria restated or referenced (errata §4.3, incl. 2-of-3
  seeds); (3) M_NORM guard/scale test recorded; (4) endpoint-valid criterion test;
  (5) D1 per-arm phase measurement recorded. `tail_driven` stays a report field, not a
  checklist gate.
- **다음 단계:** add items 1–5 to §11/§13; keep D1 as a separate explicit approval;
  keep 3-seed behind the full checklist.

## 12. Q11. B0-B

- **판정: agree (boundary intact).**
- **근거:** r3 §14 states no Phase 6 label auto-approves B0-B/B1/B2/Stage C, and
  restates the predicate: `validity_status == VALID AND control_status ==
  M_CONTROL_PASS AND signal_status == EXPLORATORY_L_SIGNAL AND tail_driven == false (or
  explicitly reported) AND leakage/mode/metric pass AND artifact complete AND separate
  prereg/approval`. In r3 labels this is equivalent to r2's predicate plus the
  redundancy removal: `M_CONTROL_PASS` already implies `m_valid == true` (§4.2), and
  `EXPLORATORY_L_SIGNAL` already implies validity `VALID` and control `PASS` (§5.3), so
  the compound predicate is not weakened. Scope note `M_CONTROL_PREFIX753_COHORT15`
  must appear in every report; full-K 11/20 and P0/PA_RETENTION are explicitly not
  B0-B evidence.
- **다음 단계:** (1) keep the predicate verbatim in implementation docs; (2) require a
  separate B0-B prereg/approval before any B0-B step; (3) report `tail_driven` and the
  M-cohort scope with any exploratory signal.

## 13. Final decision

```text
최종 판정: CONTINUE
r3 동결: 승인 (fc0d973 / r3 plan as committed; MUST items 1–6 above attached —
         text-only errata with no threshold/seed/donor/step/LR change, or
         implementation-review conditions)
구현+unit tests: 승인 (with the §10 required test/contract items)
D0: 승인 — 0 updates, ≤4 configs, ≤15 min, seed 20261111,
    labels_computed:false, not_a_result:true, mechanics only
D1: 미승인 (별도 명시 승인; ≤20 min, 4 runs ×1 update, seed 20261111, no labels)
3-seed: 미승인 (별도 gate + §11 checklist + explicit user approval)
Phase 6 registered run (12 units / 1,200 updates / 2 h): 미승인
금지 범위: any 100-step training; D1/3-seed without separate approval; test 163
           (sealed); P1; T5Gemma2 (D-108 STOP); B0-B/B1/B2/Stage C; post-result
           threshold/seed/donor/step/LR changes; opening the test split
최대 compute: implementation + unit tests (CPU, no optimizer steps) and D0
              (≤15 min wall, 0 updates, ≤4 configs, seed 20261111)
Must-fix (ranked): 1 endpoint-valid criterion; 2 statistics wiring (bootstrap
              seed / seeds_positive); 3 D1 per-arm phases; 4 n_signal domain;
              5 M_NORM Frobenius + zero-norm guard; 6 wording restorations
잘못된 전제: none material found. Two clarifications to carry: r2's `m_valid==true`
           conjunct is redundant (not weakened) in §14; errata §6.1's "debug
           included in cap" is superseded by r3's separate D0/D1 accounting —
           reconcile in text.
```

test 163 지위: **sealed** (unchanged). P1: unused. T5Gemma2: **D-108 STOP** (unchanged).

---

## 14. Limitations

- This review is documentation- and artifact-level; I did not execute the runner,
  the unit tests, or any model forward pass (per instructions), so "executable" is
  judged by contract totality and code-level consistency, not by running code.
- The plan document at HEAD was reviewed; the request's quoted basis commit `e779e93`
  (plan commit) was not separately fetched (shallow clone, depth 1), but the plan text
  and the preflight hash at HEAD were verified directly.
- ln|V|≈12.43 relies on mT5's standard 250,112-token vocabulary; model files are not
  present in this checkout, so it was not re-read locally. All other numbers in §1 were
  recomputed from repository artifacts.