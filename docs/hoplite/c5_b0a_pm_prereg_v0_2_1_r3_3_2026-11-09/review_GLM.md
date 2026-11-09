# C5 Phase 6 v0.2.1-r3.3 — External Review (GLM)

- Reviewer: **GLM 5.3 Flash (reasoning: max)**, independent external reviewer for `mandutt/unigem`, Hoplite project `proj_2e8de5ed594f47c7b851f1d7c5b52c61`.
- Round: NEW, intentionally separate r3.3 review round. Not derived from, and not reusing, any r3.2 reviewer's output (r3.2 was 1 CONTINUE-conditional / 2 NARROW).
- Review date: 2026-11-09.
- Reviewed HEAD: **`3500bc38e2edd6c2f523838d4a55588cbaf5672b`** ("docs: record C5 P/M v0.2.1-r3.3 review thread ids"), on `main`.
- Status: **r3.3 review only. No execution approval.** Phase 6 / B0-B / B1 / B2 / Stage C are NOT approved by this round.

---

## 0. Provenance, sync record, and scope of this review

### 0.1 Sync and HEAD

1. `git fetch origin` then `git pull --ff-only origin main`: first pull reported "Already up to date" at `2ed41f0` (the review-request commit). A subsequent `git fetch --deepen=20` revealed that origin/main had advanced; a second `git pull --ff-only origin main` fast-forwarded to **`3500bc3`**, which adds only `docs/hoplite/c5_b0a_pm_prereg_v0_2_1_r3_3_2026-11-09/threads.json` (+20 lines). Working tree clean after sync.
2. Lineage verified: `148d5c1` (r3.3 contract unification) → `2ed41f0` (review request) → `3500bc3` (thread ids). The two commits after `148d5c1` touch only review metadata; the review artifacts are identical to the `148d5c1` basis the request pins. **Review basis = current origin/main HEAD `3500bc3`.**

### 0.2 Independent verifications performed this round

| Check | Result |
|---|---|
| SHA-256 of `reports/provenance/C5_b0a/m_cohort_preflight.json` | `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` — **exact match** to the request's pinned hash |
| `docs/plan_c5_b0a_pm_prereg_v0_2_1_r3_3.md` line count | 1,031 — matches the request's claim (1,031줄) |
| Artifact presence/sizes at HEAD | r3.3 plan 1,031; r3.2 plan 900; r3.2 synthesis 392; preflight JSON 201; P0 report 116; runner 802; metric tests 128 lines — all seven listed artifacts exist |
| Working tree | clean; no AGENTS.md / CLAUDE.md found |

### 0.3 Scope limitation (disclosed, material to every verdict)

This round read the review request (`reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V0_2_1_R3_3_2026-11-09.md`) **in full** and directly verified repository state, commit lineage, artifact presence/sizes, and the preflight content hash (0.2). Per the requester's explicit close-out directive ("produce the final review now; do not read more files"), the bodies of the r3.3 plan (1,031 lines), r3.2 plan, r3.2 synthesis, preflight JSON content, P0 report, runner (`runner/c5_mt5_lora_b0.py`), and test file (`eval/tests/test_c5_b0_metric.py`) were **not re-read** this round.

Consequences, applied consistently below:

- Every verdict is a **specification-level** judgment against the request's own §2 (r3.2 blockers), §3.1–3.8 (r3.3 fix summary), §4 (P0 baseline), and §5 (questions), plus the 0.2 verifications.
- **Enumeration ≠ verification**: that §3.1–3.8 lists a fix for each blocker does not verify the primary text implements it coherently. The primary-text closure audit is therefore Must-fix **M1** and is a precondition of freeze.
- No citation below refers to document content I did not see. Items I could not see are explicitly labeled *unverified*.

### 0.4 Constraints honored

No training or evaluation was run. Test 163 untouched (sealed). No P1 data, no external APIs. No subagents or additional LLM calls. Repository unmodified except this single report file, written at the requester's direction.

---

## 1. Q1–Q12

### Q1. Total factored contract

Q1.
- 판정: **conditional**
- 근거: Request §3.1 defines `l_signal` as the unique tri-state consensus (true+true→true; false+false→false; otherwise NA) with `copy_only = ANDn(l_copy, NOT3(l_full))`, `full_only = ANDn(l_full, NOT3(l_copy))`; §3.8 adds the `NOT3` definition and the DoD truth table; §3.2 forbids injecting derived `m_pass_l`/`m_valid`. Together these address r3.2 blockers #1 and #8 at specification level. Two executability risks remain visible **in the summary itself**: (a) the argument domains of `ANDn` and `NOT3` are not stated in §3.1 — `ANDn(·, NOT3(·))` mixes an n-ary AND with a "NOT-3" operator; if `ANDn` ranges over seeds while `NOT3` negates 3-seed unanimity, the expression is ill-typed or ambiguous, which is exactly the dual-definition failure class of blocker #1; (b) totality of F1–F11 and the small-N precedence rule cannot be confirmed from the request text (*unverified* against the 1,031-line plan).
- 다음 단계: (1) Pin the argument domain of `ANDn` and `NOT3` (axis: seeds/endpoints/arms) in §2.3, with one worked example per operator. (2) Desk-audit F1–F11 + small-N precedence for totality (every input combination maps to exactly one label). (3) Add a totality unit test enumerating all input cells.

### Q2. L consensus / fixtures

Q2.
- 판정: **conditional**
- 근거: The 3×3 consensus arithmetic is self-consistent as summarized: 2 determined cells ((T,T)→true; (F,F)→false) and 7 NA cells; `false+NA → NOT_ASSESSABLE`, explicitly not `MEAN_CONTRAST_ONLY` (§3.1). Fixtures 16–18 cover exactly the three label outcomes: all-m_pass + (T,T) → `EXPLORATORY_L_SIGNAL`; all-m_pass + (F,F) → `MEAN_CONTRAST_ONLY`; `m_pass_pos_l=false` + (F,F) → `NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE` (§3.2). Deleting the §6.3 "M pass L false + control PASS" cell rather than populating it is the correct repair — under consensus semantics that cell is genuinely unreachable, so closing r3.2 blocker #2 by deletion (not by fabrication) is right. Residual risk: §9.2's `L_SIGNAL=ANDn` alias removal and the absence of dangling references after the §6.3 deletion are asserted (§3.1–3.2) but *unverified* in the primary text; r3.2 blocker #12 (§1.4 dangling) shows dangling references are this document's recurring failure class.
- 다음 단계: (1) Text audit: zero remaining occurrences of the §9.2 ANDn alias; zero references to the deleted §6.3 cell. (2) Extend the unit suite from fixtures 16–18 (3 rows) to all 9 consensus cells. (3) Assert the fixture schema carries no precomputed `m_pass_l`/`m_valid` fields.

### Q3. M preflight / cohort

Q3.
- 판정: **conditional**
- 근거: Verified directly this round: the preflight artifact's SHA-256 equals the request's pinned `3ee3f1ca…9837af` (chain-of-custody intact). Request §5-Q3 numbers: K=753, 15/20 M cohort, val20 signal, endpoint 15/15, full-K 11/20 as secondary. Internal consistency: 15/20 contributors satisfies the builder's contributors≥10 threshold (§3.4); full-K at 11/20 < 15/20 justifies secondary-only status. The numeric derivations inside the preflight JSON were not read this round (*unverified*).
- 다음 단계: (1) During implementation approval, read the preflight JSON against the cohort table line by line. (2) Encode contributors≥10 as a builder unit test. (3) Keep full-K 11/20 labeled secondary in every downstream table.

### Q4. M builder / M_NORM / endpoint / replay

Q4.
- 판정: **conditional**
- 근거: §3.4 specifies `M_POS_MEAN = mean_i A(h_i)[:K_M]` with shape K_M×512, L `[:753]` / P·PA `[:512]`, adapter `eval()` + `no_grad()`, per-seed builder then seed-average, **M primary reference = target prefix at K_M**, donor-crop forbidden — this closes r3.2 blocker #4 at spec level and the recipe is executable as written. §3.6's replay design — self-delimiting frame `name_len|name|dtype|ndim|shape|nbytes|bytes`, key `(doc_id, arm, seed, variant, endpoint, memory_kind, donor_id)` with `memory_kind ∈ {real, control}`, donor-free primary M separated from donor-level replay, canonical JSON + SHA-256, golden vector with expected digest, permutation/duplicate/missing-key tests — addresses blocker #6. Three gaps: (a) **M_NORM(t)** is named in the review question but its formula does not appear in §3.4's summary — *unverified* whether the plan defines it; (b) the replay key includes `donor_id` while primary M is donor-free — the encoding for donor-free entries (omitted field vs reserved sentinel) is unstated, a wire-format ambiguity of exactly the class blocker #6 was meant to close; (c) the golden vector's expected digest must be committed in-repo, not merely promised.
- 다음 단계: (1) Confirm/pin `M_NORM(t)`'s formula and time base; if absent, add before freeze. (2) Define the `donor_id` encoding for donor-free primary M in the key schema. (3) Land the golden-vector test with the pinned digest before the replay implementation merges; tie the endpoint grid (15×3×4×2) to the single `endpoint_ok` definition.

### Q5. PA

Q5.
- 판정: **agree**
- 근거: §3.8: the acquisition name `PA_STEP100_NOT_VALID` makes the invalid acquisition non-reusable by construction; `PA_RETENTION` is explicitly non-gate, preventing an unpowered statistic from gating decisions; the PA scale/geometry caveat is needed and correctly motivated by the arm table (§3.5): P/PA run native mT5 at K=512 while L runs EG2 layer19 at K=753, so cross-geometry comparison of P/PA with L is invalid without the caveat. These close the PA half of blocker #11 without touching any threshold.
- 다음 단계: (1) Attach the scale/geometry caveat at every comparison site (arm table rows, any P/PA-vs-L table), not once globally. (2) Unit-test that `PA_RETENTION` cannot appear in any gate predicate.

### Q6. Cap / D0 / D1

Q6.
- 판정: **conditional**
- 근거: Update-count arithmetic checks out from §5-Q6: registered = 4 arms × 3 seeds × 100 steps = **1,200**; D0 = **0** updates; D1 = 4 arms × 1 = **4**. §3.7 adds phase 5 (initial fixed-prefix real/M CE scoring, 15×2×copy/full) to the 8-phase T_proj and restricts the donor factor to phases 2/3/7 only — internally consistent, since exactly those phases carry the ×5 donor factor (phase 2: step0 eval 20×5; phase 3: final eval 20×5; phase 7: replay 15×5), while phases 4 (builder 20+15 ×2), 5 (15×2×2), and 6 (generation 20×256) do not. This closes blocker #7, and including phase 5 in T_proj is the right accounting. *Unverified*: the ≤96 min total is asserted, not re-derived; adding phase 5 must be absorbed by the per-phase ledger.
- 다음 단계: (1) Desk-check the per-phase timing ledger sums to ≤96 min with phase 5 included. (2) Assert in code that the donor factor appears only in phases 2/3/7. (3) Keep D1 a mechanics/timing gate, not a signal gate.

### Q7. Statistics

Q7.
- 판정: **agree**
- 근거: §3.8: new stats module with bootstrap seed **20261109**, n_boot 1,000, percentile CI (§5-Q7) — a fixed seed makes every CI exactly reproducible, and percentile CI is the appropriate choice at n=20, as P0's own wide intervals demonstrate (train Δcopy +3.7617, CI [1.8917, 5.6050]; val +5.2375, CI [2.5013, 8.0753]). `documents_positive` with a stated denominator, 2/3-registered-seed partials labeled via the missing-seed→predicate-NA rule (§3.8, closing blocker #9), and partial endpoint/tail tri-states propagating NA rather than coercing booleans (consistent with §3.1/§3.3) make the statistics executable as specified.
- 다음 단계: (1) Unit-test stats determinism (same seed → identical CI bounds). (2) Unit-test NA propagation for missing seed, partial endpoint, and tail NA. (3) Require `documents_positive` to print its denominator and the present-seed set.

### Q8. 남은 Must-fix / r3.3이 새로 만든 문제

Q8.
- 판정: **conditional**
- 근거: All 12 r3.2 blockers (request §2) have an enumerated textual counterpart in §3.1–3.8 — none is visibly abandoned. What remains is verification-grade, not redesign-grade (M1–M7 below). Candidate **new** problems created by r3.3 itself: the ANDn/NOT3 domain ambiguity (new operator combination, §3.1); the `donor_id` sentinel gap for donor-free primary M in the replay key (new wire format, §3.6); fixture-format migration risk against the 54 historically passing tests (fixtures 16–18 postdate them); and the standing risk of dangling references after the §6.3 cell deletion (this document's recurring failure class — blocker #12).
- 다음 단계: execute the ranked Must-fix list in §3 below, in order.

### Q9. 동결·구현 승인

Q9.
- 판정: **conditional**
- 근거: At specification level the blockers are closed; what remains before freeze is verification, not redesign (M1–M3). Approving implementation + unit tests + D0 zero-update mechanics debug is the cheapest path to surface spec-vs-code mismatches, and D0's 0-update design cannot contaminate any gate statistic. Required pre-implementation tests/contracts: 9-cell consensus table test; `tail_driven` tri-state test incl. NA; replay framing golden-vector test with pinned digest; builder shape/contributors/eval-mode test; stats determinism test; fixture schema purity test (no injected `m_pass_l`/`m_valid`).
- 다음 단계: (1) Complete M1–M3, then freeze r3.3 with the freeze HEAD and the preflight hash `3ee3f1ca…9837af` recorded. (2) Land the six named tests before any runner change. (3) Run D0 only after the tests pass.

### Q10. D1 / 3-seed

Q10.
- 판정: **agree**
- 근거: Keeping the D1 timing gate (4×1 updates, ≤96 min T_proj, §3.7) separate from the 3-seed decision preserves the boundary: D1 answers mechanics and timing; 3-seed answers signal stability across seeds 2/3 under the missing-seed→NA rule (§3.8). Checklist additions needed: (i) D1 must record phase-5 initial CE values against the P0 OOD caveat — §4 lists untrained real CE 12.7/13.2 > ln|V| 12.43, i.e. the untrained baseline is worse-than-uniform on real-memory prefixes, so the interpretable quantity is the trained-vs-initial contrast, never trained-vs-P0; (ii) per-phase timing ledger vs the cap; (iii) replay golden-vector executed inside D1, not only in unit tests; (iv) `endpoint_ok` evaluated at D1 as well, not only at 3-seed.
- 다음 단계: (1) Add the four items to the D1 protocol. (2) Gate 3-seed on an explicit D1 pass, never on D1 partials.

### Q11. B0-B

Q11.
- 판정: **agree**
- 근거: The boundary holds: the request header and §8 forbid automatic progression, and B0-B now requires `tail_driven == false` under the restored exact criterion (§3.3: true iff leave_top3_mean ≤ 0 OR top3_share > .50; false iff leave_top3_mean > 0 AND top3_share ≤ .50; NA if either null/nonfinite). **Restated B0-B predicate in r3.3 labels**: B0-B is eligible only if (i) no affirmative L signal per §2.3 consensus — `l_signal = false`, and any NA ⇒ predicate not satisfied; (ii) `tail_driven == false` exactly as above, any NA ⇒ not satisfied; (iii) `endpoint_ok` per its single definition (§3.8, closing blocker #11); all evaluated on registered-config artifacts. Material caution: P0's val top-3 share is **.4862**, only 1.4 points under the .50 boundary, and P0 ran `source_max_length=256` while the registered M is 512 (§4 한계) — the tail predicate must be recomputed on registered 512-length artifacts, and P0's .4862 must never be used as B0-B evidence.
- 다음 단계: (1) Write the restated predicate verbatim into the B0-B prereg as a **new prereg** (not a threshold edit). (2) Compute the tail tri-state only from registered-config artifacts. (3) Require a separate approval round for B0-B regardless of r3.3 results.

### Q12. 최종 판정

Q12.
- 판정: **CONTINUE** (conditional scope — full block in §2)
- 근거: All 12 blockers have enumerated closures; the remaining items are verification-grade (M1–M7); P0 is descriptive-only with its limitations correctly listed (§4: val median 2.9739 vs mean 5.2375 — skewed; share .4862 borderline; untrained CE above uniform; 256-vs-512 length mismatch; no trained P/PA/L evidence); and the ladder implementation → D0 → D1 → 3-seed must stay sequential and gated.
- 다음 단계: execute only the approved scope in §2; nothing else.

---

## 2. 최종 판정

```text
최종 판정: CONTINUE (conditional)
r3.3 동결:   conditional — freeze after M1–M3 are confirmed in the primary text;
             record freeze HEAD + preflight hash 3ee3f1ca…9837af in the freeze record.
구현+unit tests: approved — CPU-only; the six named contract tests land first.
D0:          approved — 0 update steps; forward/eval mechanics debug only.
D1:          conditional — only after D0 pass + timing desk-check (M4);
             4 updates (4×1) + eval phases inside the document's own ≤96 min T_proj ledger.
3-seed:      NOT released by this round — gated on an explicit D1 pass;
             the 12×100 = 1,200-update budget is reserved, not approved.
금지 범위:    Phase 6 execution; B0-B / B1 / B2; Stage C; test 163 (sealed); P1 data;
             T5Gemma2 (D-108 STOP stands); threshold/seed/donor/step/LR changes after results;
             use of P0 numbers as gate evidence.
최대 compute: implementation + unit tests CPU-only; D0 = 0 updates;
             D1 ≤ 4 updates + eval within ≤96 min T_proj as documented. Nothing beyond.
Must-fix (ranked): M1–M7 (§3).
잘못된 전제:  (1) P0's positive Δcopy/Δfull are trained-memory-use evidence — they are
             untrained-model, descriptive-only, 256-length, with an OOD baseline caveat
             (untrained CE 12.7/13.2 > ln|V| 12.43, i.e. worse than uniform);
             (2) the request's §3 fix summary is verified plan text — it is a summary;
             the primary-text audit (M1) is outstanding and was not performed this round
             by instruction; (3) the 54 historical tests cover fixtures 16–18 and the
             tri-state table — they predate them; (4) enumerated blocker closures are
             verified closures — enumeration ≠ verification.
```

---

## 3. Must-fix (ranked)

| # | Item | Closure evidence required | Cost |
|---|---|---|---|
| **M1** | Primary-text closure audit (blockers #1, #2, #11, #12): verify in the r3.3 plan itself that §9.2 has no residual `L_SIGNAL=ANDn` alias; the §2.4 9-cell table matches §2.3 exactly (7 NA cells; false+NA → `NOT_ASSESSABLE` only); the deleted §6.3 cell leaves zero dangling references. r3.2's blockers were documentation defects, so a documentation errata's closure must itself be text-verified. | audit note with zero-count grep results | desk check |
| **M2** | Pin `ANDn` / `NOT3` argument domains in §2.3 with worked examples; otherwise `copy_only`/`full_only` is ill-typed or ambiguous — the same dual-definition failure class as blocker #1. | §2.3 text + 2 worked examples | desk check |
| **M3** | Replay wire-format completeness: define the `donor_id` encoding for donor-free primary M (omitted vs sentinel), and commit the golden-vector test with the **pinned expected digest in-repo**. Without a pinned digest, blocker #6 is not closed. | test file + digest constant | small code+test |
| **M4** | Re-derive the ≤96 min T_proj ledger with phase 5 included; assert in code that the donor factor appears only in phases 2/3/7. | timing table + assertion | desk check + assert |
| **M5** | Confirm `M_NORM(t)` is explicitly defined (formula + time base) in the plan; if absent, add before freeze. | §3.4/§4 text | desk check |
| **M6** | Extend the unit suite: all 9 consensus cells; `tail_driven` tri-state incl. NA; missing-seed→NA; stats determinism (seed 20261109); fixture schema purity (no injected `m_pass_l`/`m_valid`); builder contributors≥10 + eval-mode + shape K_M×512; endpoint grid tied to the single `endpoint_ok`. | green tests | small delta on the 128-line suite |
| **M7** | Interpretive guard: phase-5 initial CE must be read against the P0 OOD caveat (worse-than-uniform untrained baseline, CE 12.7/13.2 > ln|V| 12.43); P0's Δ values and .4862 share must never be cited as gate evidence; any B0-B tail computation must use registered 512-length artifacts. | D1/D0 protocol text | desk check |

---

## 4. Verification record

| Fact | Value |
|---|---|
| Sync | `git fetch origin`; `git pull --ff-only origin main` → fast-forward, clean tree |
| Review HEAD | `3500bc38e2edd6c2f523838d4a55588cbaf5672b` (= origin/main at review time) |
| Plan commit under review | `148d5c1` (r3.3 contract unification); later commits metadata-only |
| Preflight hash (verified locally) | `3ee3f1ca68a834e9bc2c63f6d92844ee37f2e23da1cdf640ace93c46769837af` — matches request pin |
| Reads performed | review request (full); repository state/lineage/hash/sizes |
| Reads not performed (by instruction) | plan bodies, synthesis, preflight JSON content, P0 report, runner, tests — reflected in M1 and each "unverified" label |
| Writes performed | this file only |

*End of report — GLM 5.3 Flash (reasoning: max), independent r3.3 review round.*