# C5 Phase 6 P/M Prereg v0.2.1-r3.4 — Independent Review

- Reviewer: **DeepSeek V4.1 Flash 1017** (Hoplite model `deepseek-v4.1-flash-1017`, OpenRouter), **reasoning: high**
- Round: r3.4, independent (not a duplicate of the r3.3 round; no other model's answer was read or reused)
- Date: 2026-11-09
- Request: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_R3_4_2026-11-09.md`
- Review basis: current `origin/main` HEAD after sync

## 0. Sync record and scope

```text
git fetch origin        -> branch main -> FETCH_HEAD (no new objects reported)
git pull --ff-only origin main -> Already up to date.
HEAD                    -> 05de3ae1b0a4b3bc3df5170efdfe037b45038b9b
commit subject          -> docs: add C5 P/M v0.2.1-r3.4 review request
worktree branch         -> hoplite/kos-d1155e5f (clean; no repository edits by me)
```

- The request cites `30b966d` as the r3.4 document commit; the current HEAD adds only the
  review-request file on top. Review basis is the HEAD above.
- Honored constraints: no training/eval executed; test 163 not opened; no P1 data; no external
  APIs; no subagents or additional LLMs; T5Gemma2 remains closed by D-108 STOP; Phase 6 /
  B0-B / B1 / B2 / Stage C not approved by this round; the only file written is this report.
- r3.4 is text-only. No code was written for it and none should be read as pre-existing.

## 1. Independent verification actually performed

| Check | Method | Result |
|---|---|---|
| Preflight integrity | `sha256sum reports/provenance/C5_b0a/m_cohort_preflight.json` | `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` — **matches** §1.1 |
| K_M = 753 maximality | recomputed from `train_h_lengths` / `val_h_lengths` | val 6th-smallest = 753 ⇒ `#val≥K ≥ 15` forces `K ≤ 753`; train 11th-smallest = 770; 754 ⇒ 14 eligible — §8.7 statement **correct** |
| Contributor / cohort counts | recomputed | 16 train contributors ≥ 10; 15 val eligible; `common_ids` = 15; native @512 = 20/20 — **consistent** |
| Endpoint / phase arithmetic | recomputed | `15·3·4·2·2·2 = 1,440`; phase 5 `15·2·2·2 = 120`; phase 7 `15·5·2·2·2 = 600`; 12×100 = 1,200; 1,200+4 = 1,204; 120+20+15 = 155 min — **all correct** |
| P0 headline numbers | `jq` on `reports/provenance/C5_b0a/p0_native_sanity.json` | train +3.76173 CI [1.89169, 5.60496], 14/20; val +5.23746 CI [2.50132, 8.07527], 18/20 — **matches** §4 |
| P0 tail descriptor | recomputed from `per_doc` | val20 median **2.9739** ✓; top-3 **signed** share **0.48620**; top-3 **absolute** share **0.43355** (≈0.455 on the 15 `common_ids`) — see MF-10 |
| §2.3/§2.4/§2.2 coherence | hand-evaluated all 9 cells under `ANDn`/`NOT3` | every `l_signal`/`copy_only`/`full_only` cell reproduces exactly — **closed** |
| r3.4 self-containment | `grep` for normative cross-references to r3.3 | only the history line and the precedence line; **no definition defers to r3.3** |

## 2. Answers to Q1–Q13

### Q1. Total factored contract (validity / control / signal, ANDn, F1–F11, L tri-state, small-N)

- Verdict: **agree** (with two wording fixes, MF-7/MF-8)
- Evidence: §5.3 ends in a total `else`; I traced all 5 validity values (§3.1), all 9 L pairs
  (§2.4), and all 5 control values (§4.3). Every label in §5.2 is reachable: `COPY_ONLY_WEAK`
  (VALID, n=15, `copy_only=true`), `FULL_ONLY_WEAK`, `MEAN_CONTRAST_ONLY` (fixture 17),
  `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE` (fixture 18), `EXPLORATORY_L_SIGNAL` (fixture 16),
  `*_VALIDITY_INVALID`/`*_VALIDITY_NOT_ASSESSABLE`, `L_SIGNAL_CONTROL_NOT_ASSESSABLE`, and all
  `INCONCLUSIVE_SMALL_N*` via `n_signal<15`. F1–F11 are consistent with the §3.2→§3.4 ordering
  (e.g. F3 `pa_path NA + P invalid → P_STEP100_NOT_VALID`, F9 `p_step NA + p_valid false →
  NOT_ASSESSABLE` via §3.3 tier precedence). §5.5 small-N precedence does not hide validity.
- Residual: §4.3 `if m_evaluable is not true: M_NOT_EVALUABLE` collapses availability **NA** into a
  definite label, which is asymmetric with the adjacent "do not collapse p/pa NA" rule and with
  false-dominant `ANDn` (MF-8). §4.3's bullet "`M_CONTROL_INVALID` = P/PA calibration fail" is
  ambiguous against the code path `p_valid=false → M_NOT_EVALUABLE` (MF-7).
- Next steps: (1) add one sentence that `M_CONTROL_INVALID` means M-pass calibration of the P/PA
  arms, not `P_VALID`/`PA_VALID`; (2) state whether availability NA collapsing to
  `M_NOT_EVALUABLE` is intentional; (3) pin it in the truth-table test.

### Q2. L consensus / fixtures agreement

- Verdict: **agree**
- Evidence: §2.4 rows now read `true,false → l_signal=NA, copy_only=true, full_only=false` and
  `false,true → l_signal=NA, copy_only=false, full_only=true`. Deriving each cell from §2.2
  (`copy_only = ANDn(l_copy, NOT3(l_full))`) reproduces the full 9-row table including the
  `true/NA`, `NA/true`, `false/NA`, `NA/false` rows. §2.3 is the single author, §9.2's `ANDn`
  alias is explicitly retired, and §6.3's prohibition (no "control PASS + `m_pass_l=false`" cell)
  is consistent. Fixtures 16/17/18 derive by primitive and match §5.3.
- Residual: only the fixture-default convention (MF-11): the F1–F11 `flags` column does not state
  the remaining flags, so the expected value depends on unstated defaults.
- Next steps: (1) add "unspecified path flags are `true`, P/PA valid/calibrated, `test_split_used
  = false`" to §3.7; (2) keep the 9-pair × {VALID, INVALID, NA} × n={14,15} test matrix.

### Q3. M preflight / cohort legitimacy

- Verdict: **conditional**
- Evidence: the arithmetic is sound and I re-derived it independently (table above): K=753 is the
  maximum K with ≥10 train contributors and ≥15 eligible val targets, 754 drops to 14, native
  @512 is 20/20, and the preflight hash is frozen and verified. What is *not* yet stated is that
  the 15-doc cohort is **length-selected**: the 5 excluded val docs are the five shortest
  (751, 718, 708, 750, 728), so every signal claim is conditioned on longer documents and on a
  zero-margin K (any h-length recomputation drift aborts). §8.7 records the abort path but §12
  does not record the selection-bias limitation. `full-K 11/20` is undefined (MF-6): the preflight
  gives a count and an excluded set but no K, and that excluded set is the **nine longest** val
  docs (h = 771…830), which does not follow from a naive `h_len ≥ K` rule.
- Next steps: (1) define `K_full` and its eligibility predicate in §8.1, or mark the full-K cohort
  descriptive with no stated count; (2) add the length-selection limitation to §12; (3) require the
  5 excluded IDs plus their descriptive deltas in the artifact (checklist item 11 covers only the
  15-vs-val20 separation).

### Q4. M builder / M_NORM / endpoint / replay / golden vector

- Verdict: **conditional** (two blockers)
- Evidence: the builder is now executable — `h_len_i` is a scalar (§8.2), the arm matrix fixes
  F/L=753+adapter, P=512+identity, PA=512+random-init adapter, `real_prefix_t := A(h_t)[:K_M]`
  fixes the adapter space (§8.3), and `builder_ok` covers contributors/finite/`||M_POS_MEAN||>0`/
  15 positive target norms. Endpoint arithmetic is 1,440 exactly.
  But the **semantics** of the `variant × memory_kind` grid are not defined (MF-1): §8.3 fixes the
  real memory to `real_prefix_t`, which is variant-independent, while §8.4/§8.5 treat `M_POS_MEAN`
  and `M_NORM` as two primary variants that must both pass. Under that reading the `real` row is
  duplicated across variants, so the 2×2 grid is degenerate and the record count is not 1,440
  distinct cells. `delta_memfree` (§8.5) also implies a memory-free control, but no tensor is
  named as `control` anywhere (grep: only the label `memory_kind ∈ {real, control}`, §10.6).
  Replay: phase 7 is 600/arm-seed donor-level, yet §10.6 requires donor-free records to encode
  `donor_id: null`, which are phase-5 records (120/arm-seed) — the replay set is therefore either
  600 or 720 per arm-seed (7,200 vs 8,640) and `replay_ok` feeds `m_evaluable` (MF-4).
  The golden-vector method is adequate (byte-level frame, endianness, empty-state hash, replay
  golden, permutation/duplicate/missing-key tests) but the digests do not yet exist.
- Next steps: (1) publish the 4-cell tensor table (variant × memory_kind → exact tensor) and either
  prove the 4 cells distinct or reduce the axis/count; (2) state the replay set domain and record
  count explicitly and drop `donor_id:null` if phase 5 is outside it; (3) commit
  `golden_vectors.json` from the independent script before the endpoint test is called green.

### Q5. PA

- Verdict: **conditional**
- Evidence: naming is coherent (`PA = native memory + random adapter + decoder LoRA`, acquisition
  control), `PA_STEP100_NOT_VALID` is a distinct validity value, `PA_RETENTION` is explicitly
  nullable and non-gating, and the scale/geometry caveat is stated (§7.2) — PA memory is native
  512 while L memory is EG2-753, so PA is not an L retention comparison. The veto rationale is now
  written and pre-registered (§4.2): PA failure ⇒ native-regime calibration invalid ⇒
  `m_valid=false` ⇒ `M_CONTROL_INVALID` ⇒ no affirmative.
- Residual: the rationale is a design assertion, not evidence; no trained P/PA result exists. So the
  branch "P passes, PA fails ⇒ the whole L M-control is uninterpretable" is a live, high-probability
  outcome that should be named in §12 as an accepted risk. Also `P_VALID`/`PA_VALID` have no pinned
  cohort (MF-3).
- Next steps: (1) pin the P/PA validity cohort (recommend the 15 `common_ids` for comparability);
  (2) state the P-pass/PA-fail outcome in §12 as expected-and-accepted; (3) test it in
  `control_status` fixtures.

### Q6. Cap / D0 / D1 / T_proj

- Verdict: **agree** (two wording fixes)
- Evidence: re-derived — 4 arms × 3 seeds = 12 units × 100 = 1,200 registered updates; D1 = 4
  updates at one debug seed; combined 1,204 and 155 min (120 + 20 + 15); 8 timed phases; phase 5 =
  120/arm-seed; phase 7 = 600/arm-seed; `T_proj` formula multiplies by 3 seeds and 100 updates and
  includes the memory-kind factor; `T_proj ≤ 96 min` sits below the 120-min wall as a guard; D0 is
  0 updates/≤15 min/seed 20261111/not-a-result and outside the registered cap.
- Residual: "4 arm-seeds ×1 update" should read "4 arms × 1 seed" (MF-12), and the plan should say
  that `100 · t_train_arm` is a linear extrapolation from a single measured update.
- Next steps: (1) reword D1; (2) state the extrapolation; (3) record the per-phase overhead term
  explicitly in the D1 artifact.

### Q7. Statistics

- Verdict: **conditional**
- Evidence: constants are complete and executable (n_boot 1,000, percentile 2.5/97.5, bootstrap seed
  20261109, unit = document, seed-average before bootstrap, n_min_signal 15); the L predicates
  restore the thresholds correctly (copy `.05`, full `>0`); missing registered seed ⇒ predicate
  `NA` with no 2-of-available substitution; tail tri-state is ordered and total with null handling
  for denominator 0 and n<4.
- Residual: (a) `documents_positive` is only a module output line, never defined or classified as
  descriptive vs gate (MF-9); (b) the primitives `l_copy_signal`/`l_full_signal` are never bound to
  `L_COPY_SIGNAL`/`L_FULL_SIGNAL` (MF-5), and the minimum n for computing them when `n_signal<15`
  is unstated even though §5.3 branches on `INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL`; (c) no statement
  that no multiplicity correction is applied beyond the conjunctive both-variant requirement;
  (d) the bootstrap seed 20261109 numerically equals a registered training seed (harmless, but
  worth flagging to avoid artifact confusion).
- Next steps: (1) define `documents_positive` (count of docs with delta > 0) and mark it
  descriptive; (2) add `l_copy_signal := L_COPY_SIGNAL` / `l_full_signal := L_FULL_SIGNAL` plus the
  retained-ID set and minimum n; (3) add the no-additional-correction statement.

### Q8. Remaining Must-fix (ranked) and new problems introduced by r3.4

- Verdict: **disagree** that the r3.3 blocker list is fully closed; the ranked list is §3 below.
- Evidence: tracks 15 of the 18 r3.3 blockers as textually closed, and I agree with that for §2.4,
  the F/L/P/PA builder, `real_prefix_t` space, `n_signal {NA,0..15}`, `adapter_lr`, T_proj 120/600,
  endpoint arithmetic, PA veto, named-cell prerequisites, ANDn/NOT3 domain, zero-margin path and
  the P0 caveat. Not closed: the tail input is still variant-ambiguous (MF-2), and three holes that
  were never on the r3.3 list are exposed by r3.4's own explicit enumeration: the variant ×
  memory_kind tensor semantics (MF-1), the P/PA validity cohort (MF-3), and the replay set domain
  (MF-4).
- New problems introduced by r3.4 itself: (a) writing the 1,440 record count made the degenerate
  variant × memory_kind grid explicit but not resolvable; (b) writing `top3_abs_share` as the gate
  input means P0's reported `.4862` (a signed-denominator share) is not the gate statistic — the
  comparable absolute value is `.4335` (§1 table), so §12 should carry the tail caveat with the
  right number.
- Next steps: (1) close MF-1…MF-5 in a text-only r3.5; (2) re-issue the endpoint and tail sections
  as normative tables, not prose; (3) re-verify §15 against the artifact rather than by assertion.

### Q9. Freeze and implementation approval

- Verdict: **conditional / disagree as-is**
- Evidence: r3.4 cannot be frozen as-is because MF-1…MF-4 each change an executable decision
  (primary endpoint tensors, the tail gate value, the P/PA-driven `control_status`, and
  `replay_ok → m_evaluable`). Every one of them can flip `EXPLORATORY_L_SIGNAL`. None requires new
  data, new thresholds, or new compute: all are text-only definitions. So the correct action is a
  short r3.5, not a redesign.
- Next steps: (1) r3.5 closes MF-1…MF-5 (and MF-6/MF-7 if cheap); (2) freeze the r3.5 commit hash;
  (3) then implementation + unit tests + D0 may start, with the pre-freeze contracts below.
- Implementation prerequisites (must exist before code is accepted): pure decision function with
  F1–F11, the 9 L pairs × {VALID, INVALID, NA} × n={14,15}, fixtures 16–18; builder tests
  (contributor threshold, P identity, scalar `h_len_i`, 15 positive target norms, `[:753]`/`[:512]`);
  the 4-cell endpoint distinctness + record-count test; canonical hash golden vector produced by the
  independent script; replay domain test including `variant`/`memory_kind`/`donor_id`; stats module
  tests (seed 20261109, `documents_positive`, 2-of-3, missing-seed `NA`); zero-margin abort test;
  and a single-source test proving the runner imports the decision module rather than re-implementing
  it.

### Q10. D1 / 3-seed boundaries

- Verdict: **conditional**
- Evidence: the boundary structure is adequate — D0 (0 updates, ≤15 min, no timing claim), D1
  (4 updates, ≤20 min, no labels, separate approval), 3-seed (separate gate, requires D1 timing,
  `T_proj ≤ 96 min`), and the debug seed 20261111 is outside the registered 20261108/09/10. The
  27-item checklist covers freeze hash, code hash, tests green, D0/D1 artifacts, preflight hash,
  no-threshold-diff, replay hashes, and the B0-B boundary.
- Residual: the checklist has no item for the 4-cell memory tensor distinctness, the P/PA validity
  cohort, the tail variant, the decision-function single-source import, or an artifact/manifest
  schema version; and item 8 ("no threshold/seed/donor/step/LR diff") has no stated verification
  mechanism.
- Next steps: (1) add checklist items 28–33 (memory-cell distinctness, P/PA cohort pin, tail
  variant pin, single-source import, manifest schema version, config-hash diff check);
  (2) make item 8 a machine check over a committed config hash; (3) keep D1 and 3-seed separate.

### Q11. B0-B boundary

- Verdict: **agree**
- Evidence: §14 keeps every automatic-progression guard: `EXPLORATORY_L_SIGNAL` alone is not
  approval, `tail_driven` must be `false` (NA/true fail), full-K 11/20, P0 and `PA_RETENTION` are
  not B0-B evidence, and a separate prereg/approval is required. This round does not approve
  B0-B/B1/B2/Stage C.
- Restated predicate in r3.4 labels:

```text
validity_status == VALID
AND control_status == M_CONTROL_PASS        # ⇒ m_evaluable true, p_valid/pa_valid true,
                                            #   m_valid true, m_pass_l true, both M variants pass
AND signal_status == EXPLORATORY_L_SIGNAL   # ⇒ validity VALID, n_signal=15, l_signal true,
                                            #   control PASS
AND l_signal == true AND n_signal == 15
AND tail_driven == false
AND leakage/mode/metric pass
AND artifact complete
AND separate prereg/approval
scope: M_CONTROL_PREFIX753_COHORT15 only
```

- Next steps: (1) note in §14 that several conjuncts are implied by the labels and are kept only as
  consistency assertions; (2) state whether `M_NORM`-only pass (`M_PASS_NORM_CONFOUNDED`) can ever
  satisfy `M_CONTROL_PASS` (today it cannot, because `m_pass_l = ANDn(pos, norm)`).

### Q12. Final verdict

- Verdict: **NARROW**
- Evidence: 15 of 18 r3.3 blockers are genuinely closed and the document is close to executable, but
  four definition-level holes remain in the primary scoring path (MF-1…MF-4). None is a scientific
  disagreement; all are missing sentences in a text-only errata.
- Next steps: see §5 block below.

### Q13. Consolidation (v1.0)

- Verdict: **agree** that a single consolidated normative document should precede implementation
- Evidence: r3.4 is already ~self-contained — I found no normative reference that defers a
  definition to r3.3 (only the precedence line and history). So consolidation is cheap: it is the
  fixed r3.5 republished as v1.0, not a re-derivation. The errata chain is the higher risk: an
  implementer must apply `r3.4 > r3.3 > r3.2 > …` across nine documents to resolve any sentence
  r3.4 does not restate, and the four residual holes above are exactly the kind that survive such
  a chain.
- Minimum TOC: (1) scope/definitions/preflight hash; (2) primitives + tri-state + operator domains;
  (3) validity; (4) control availability + `control_status`; (5) signal labels + dispatch +
  precedence; (6) statistics (constants, L predicates, bootstrap, tail, partial endpoints);
  (7) M: builder, memory taxonomy (the 4-cell tensor table), `M_NORM`, endpoint identity, pass/delta,
  replay/canonical hash, zero-margin; (8) P/PA arms, hyperparameters, validity cohort; (9) D0/D1/
  cap/`T_proj`; (10) truth table + fixtures; (11) implementation DoD; (12) B0-B boundary;
  (13) limitations (P0 OOD, length-selected cohort, PA veto risk); (14) traceability appendix.
- Traceability method: a table mapping each v1.0 section to (a) its r3.1–r3.4 origin, (b) each
  reviewer Must-fix ID it closes, (c) the unit test that pins it. Keep the preflight hash and the
  supersedes-all line; drop the errata framing.
- r3.4 as implementation authority: **no** — use the fixed v1.0. Keep the v1.0 review as one
  separate, single round on the consolidated diff.
- Next steps: (1) produce v1.0 = r3.5; (2) one review round on it; (3) freeze, then implement.

## 3. Ranked Must-fix before freeze and implementation

| Rank | Severity | Item | Where | Why it blocks |
|---|---|---|---|---|
| MF-1 | **blocker** | The `variant × memory_kind` 4-cell grid has no tensor definition; `real_prefix_t` is variant-independent while `M_POS_MEAN`/`M_NORM` are two variants that both must pass; `control` is never named; `delta_memfree` implies a memory-free control | §8.3 L646–656, §8.4 L662–680, §8.5 L682–691 | Determines the primary endpoint; the 2×2 grid may be degenerate, so 1,440 records may not be 1,440 distinct cells; `M_PASS_POS` vs `M_PASS_NORM` may be the same test twice |
| MF-2 | **blocker** | `tail_driven` input omits `variant`, although two primary variants exist and `tail_driven` is a hard B0-B gate | §9.4 L776–786 vs §8.4 L665, §14 L1051–1058 | A hard gate with two possible values; the review request's own §3.5 omits the same field |
| MF-3 | **blocker** | `P_VALID`/`PA_VALID` (and `m_pass_pos_p/norm_p`) have no pinned cohort — 15 `common_ids` or 20 native docs | §7.1 L546–557, §8.4 L662, §10.3 L854–855 | Feeds validity §3.4 and `control_status` §4.3, so the primary label depends on an unpinned n |
| MF-4 | **blocker** | Replay set domain/count undefined (phase 5 donor-free 120/arm-seed vs phase 7 donor-level 600/arm-seed ⇒ 600 or 720 per arm-seed, 7,200 or 8,640 total); `debug_replay_hash` is a D1 hash (seed 20261111, 1 update) yet is compared to the registered post-run hash | §10.3 L856–860, §10.6 L925–945 | `replay_ok` feeds `m_evaluable`; a hash-domain mismatch can flip `control_status` |
| MF-5 | high | `l_copy_signal`/`l_full_signal` are never bound to `L_COPY_SIGNAL`/`L_FULL_SIGNAL`; minimum n when `n_signal<15` unstated | §2.3 vs §9.2 L742–757, §5.3 | The primitives that drive `l_signal` and the small-N labels have no binding statement |
| MF-6 | medium | "full-K 11/20 secondary" has no K or predicate; preflight's excluded set is the nine longest val docs, inconsistent with `h_len ≥ K` | §8.1 L615, §14 L1061, preflight `full_k_secondary` | Not a gate, but an executable contract cannot cite an undefined cohort |
| MF-7 | low | "`M_CONTROL_INVALID` = P/PA calibration fail" vs `p_valid=false → M_NOT_EVALUABLE` | §4.3 L258–262 | Ambiguous label semantics in the truth table |
| MF-8 | low | Availability `NA` collapses to `M_NOT_EVALUABLE`, contradicting the adjacent no-collapse rule | §4.3 L248–250 | Undocumented asymmetry in a normative decision function |
| MF-9 | low | `documents_positive` undefined and unclassified | §9.3 L764 | Stats module output with no contract |
| MF-10 | low | §12 omits the tail-loading caveat; the request's `.4862` is the **signed** share, not the gate's absolute share (`.4335`) | §12 L1020–1026 | A known pre-result tail risk sits ~4–7 points below the `.50` gate and should be stated without relaxing it |
| MF-11 | low | F1–F11 omit residual flag defaults | §3.7 L193–208 | Makes "exact output" ambiguous per fixture |
| MF-12 | low | D1 "4 arm-seeds" wording; `100·t_train` extrapolation unstated | §10.3 L788–790 | Cap accounting clarity |
| MF-13 | low | `golden_vectors.json` digests absent | §10.6 L948–952 | Endpoint test cannot be called green before they exist |

## 4. What r3.4 genuinely closed (for the record)

§2.4 mixed rows → `NA` with `copy_only`/`full_only` true (verified cell by cell); F M builder and the
full F/L/P/PA arm matrix with K_M, adapter and `h_len_i` scalar; P `A=identity`; `real_prefix_t :=
A(h_t)[:K_M]` in the same adapter space; `n_signal ∈ {NA,0..15}` with val20 descriptive only;
`adapter_lr` for all adapter-bearing arms; T_proj memory-kind factor with 120/600; the 1,440 record
identity; PA veto rationale; independent golden-vector construction; named-cell prerequisites
(fixtures 16–18 only); scalar `ANDn`/`NOT3` domains; zero-margin abort and `ZERO_MARGIN_COHORT_FAIL`;
P0 OOD caveat. I also independently confirmed the preflight hash, the K=753 maximality argument, the
cohort counts, the whole cap arithmetic, and every P0 headline number.

## 5. Final verdict

```text
최종 판정: NARROW
r3.4 동결: 아니오 — MF-1~MF-5를 닫는 text-only r3.5(=v1.0) 후 동결
구현+unit tests: r3.5 동결 후 조건부 승인 (아래 구현 전 계약 충족 시)
D0: r3.5 동결 후 조건부 승인 (0 updates, ≤15 min, seed 20261111, not_a_result)
D1: 미승인 (별도 승인)
3-seed: 미승인 (D1 + T_proj ≤96 min + 별도 gate)
금지 범위: test 163 열람, P1 사용, 학습·평가 실행(r3.5 전), B0-B/B1/B2/Stage C 자동 진행,
           T5Gemma2 (D-108 STOP), threshold/seed/donor/step/LR 변경, r3.5 전 코드 작성
최대 compute: 현재 0. r3.5 동결 후에도 registered 1,200 updates / 120 min wall / 6 threads /
           no GPU / no retry; D0 0 updates ≤15 min; D1 4 updates ≤20 min;
           combined 1,204 updates / 155 min (grant 아님, §10.5 그대로)
Must-fix (ranked): MF-1 (variant×memory_kind tensor table), MF-2 (tail_driven variant),
           MF-3 (P/PA validity cohort), MF-4 (replay domain/count + debug-vs-final hash),
           MF-5 (l_copy/l_full binding), MF-6 (full-K), MF-7/8 (control_status wording),
           MF-9…MF-13 (low)
v1.0 consolidation: 필요 — r3.5를 self-contained v1.0으로 발행, traceability 부록 포함,
           1회 단독 리뷰 후 freeze. errata chain으로 구현하지 않는다.
잘못된 전제:
  (1) "tail_driven input이 닫혔다" — arm/endpoint/cohort만 닫혔고 variant가 없다.
  (2) "§15에서 18개 모두 closed" — 자기 선언이며, r3.4 자신의 1,440 enumeration이
      variant×memory_kind·P/PA cohort·replay domain 세 구멍을 새로 드러냈다.
  (3) "P0 top-3 share .4862"는 signed-denominator share다; r3.4 gate 입력인 absolute share는
      val20에서 .4335(15 common_ids에서 ≈.455)다.
  (4) "54 tests pass historically"는 이 checkout에서 PM 결정함수 테스트로 확인되지 않는다
      (eval/tests에는 B0 metric 7-test class만 존재). historical claim으로만 취급한다.
  (5) 확인된 전제: preflight SHA-256 일치, K=753 maximality, P0 mean/CI/positive count 일치,
      원격 동기화는 이미 최신(05de3ae).
```

## 6. Constraints restated

This review does **not** approve Phase 6 execution, B0-B, B1, B2 or Stage C, and does not authorize
test 163, P1 data, external APIs, T5Gemma2 work, or any threshold/seed/donor/step/LR change. It
proposes no change that depends on results, because no trained P/PA/L result has been seen.