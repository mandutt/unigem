# EXTERNAL REVIEW — C5 B0A P/M PREREG v1.0.6 — GLM 5.3 Flash (independent round)

- Reviewer model: GLM 5.3 Flash (OpenRouter), Hoplite thread run, no subagents, no other-LLM output used.
- Review basis: `mandutt/unigem` @ origin/main `e619885ce34c9f498008b00fd6d0a52e40c7316d`
  ("docs: add C5 P/M v1.0.6 review request", 2026-11-09T18:37:38+09:00).
- Date: 2026-11-09 (UTC). Round: NEW, separate v1.0.6 review round (not a reuse of any prior model's answer).
- Round outcome: **NARROW — round invalid as executed; verdict below is process-level, NOT a substantive v1.0.6 verdict.**

## 0. Review-integrity statement (read this first)

This round's instructions required the reviewer to stop using tools and stop reading files before any basis
document had been opened, and then write this report. As a result, **none of the twelve listed basis documents
were read in this round.** Under evidence rules, no verdict is issued on uninspected material. Consequently:

- Every question-specific verdict below is **NOT EVALUABLE (this round)**.
- Nothing in this file implies that the plan, runner, tests, golden vectors, provenance JSONs, or the v1.0.5
  synthesis were reviewed, and nothing here may be recorded as approval of v1.0.6, P1, Phase 6, B0-B, B1, B2, or Stage C.
- Facts are split into two classes throughout: **[VERIFIED]** = observed locally by the reviewer this round;
  **[DISPATCH-CLAIMED]** = stated in the review dispatch key facts and taken on trust, unverified.

## 1. Sync record [VERIFIED]

- `git fetch origin` → success (branch `main` → FETCH_HEAD).
- `git pull --ff-only origin main` → "Already up to date"; no merge, no rebase.
- Resulting HEAD: `e619885ce34c9f498008b00fd6d0a52e40c7316d`; `HEAD == origin/main` confirmed post-pull.
- Note: the local checkout branch is `hoplite/haliartos-071f817a` (workspace worktree naming), but its tip is
  content-identical to origin/main `e619885c…`, so the review basis commit is correct.
- Working tree was clean before the pull; the only write made in this round is this file
  (`docs/hoplite/c5_b0a_pm_prereg_v1_0_6_2026-11-09/review_GLM.md`), which did not exist before this round.

## 2. File inventory [VERIFIED — existence/size only, contents NOT read]

| Path | Lines present |
|---|---|
| `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_6_2026-11-09.md` | 269 |
| `docs/plan_c5_b0a_pm_prereg_v1_0_6.md` | 1730 |
| `docs/plan_c5_b0a_pm_prereg_v1_0_6_FREEZE.template.json` | 18 |
| `docs/hoplite/c5_b0a_pm_prereg_v1_0_6_2026-11-09/golden_vectors.json` | 158 |
| `reports/C5_B0A_PM_PREREG_V1_0_5_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 221 |
| `reports/provenance/C5_b0a/m_cohort_preflight.json` | 201 |
| `reports/provenance/C5_b0a/p0_native_sanity.json` | 457 |
| `reports/provenance/C5_b0a/p1_usage.json` | 7 |
| `reports/provenance/C5_b0a/p1_usage.postrun.json` | 5 |
| `reports/provenance/C5_b0a/phase6_artifact_registry.json` | 16 |
| `runner/c5_mt5_lora_b0.py` | 802 |
| `eval/tests/test_c5_b0_metric.py` | 128 |

Also present in the review directory: `dispatch.sh`, `prompt_glm.txt`, `prompt_ds1017.txt`, `prompt_sol.txt`,
`watch_reviews.py` [VERIFIED existence only].

## 3. Q1–Q13

The question texts themselves live in the unread review-request file; their numbering and exact wording could
not be confirmed. Each is therefore answered uniformly; §4 gives a *candidate* evidence map inferred from the
dispatch fix list (explicitly not confirmed against the request file).

| Q | Verdict | Evidence | Next step |
|---|---|---|---|
| Q1 | NOT EVALUABLE (this round) | Basis documents not read this round (instruction forbade reads before report) | Re-run round with read access; answer from the mapped files in §4 |
| Q2 | NOT EVALUABLE (this round) | Same | Same |
| Q3 | NOT EVALUABLE (this round) | Same | Same |
| Q4 | NOT EVALUABLE (this round) | Same | Same |
| Q5 | NOT EVALUABLE (this round) | Same | Same |
| Q6 | NOT EVALUABLE (this round) | Same | Same |
| Q7 | NOT EVALUABLE (this round) | Same | Same |
| Q8 | NOT EVALUABLE (this round) | Same | Same |
| Q9 | NOT EVALUABLE (this round) | Same | Same |
| Q10 | NOT EVALUABLE (this round) | Same | Same |
| Q11 | NOT EVALUABLE (this round) | Same | Same |
| Q12 | NOT EVALUABLE (this round) | Same | Same |
| Q13 | NOT EVALUABLE (this round) | Same | Same |

## 4. Candidate per-Q evidence map (INFERRED from dispatch fix list — numbering unconfirmed)

Dispatch states v1.0.6 fixes: §13.5 token, array digest, phase-7 equal-dim, control golden order,
bootstrap RNG, freeze handoff, postrun coverage, P0/schema. Likely minimum evidence per fix area:

| Fix area (dispatch wording) | Minimum files to answer |
|---|---|
| §13.5 token | `docs/plan_c5_b0a_pm_prereg_v1_0_6.md` §13.5 + `runner/c5_mt5_lora_b0.py` |
| Array digest | runner + `docs/hoplite/.../golden_vectors.json` + `reports/provenance/C5_b0a/p0_native_sanity.json` |
| Phase-7 equal-dim | runner |
| Control golden order | `golden_vectors.json` + `eval/tests/test_c5_b0_metric.py` |
| Bootstrap RNG | runner + `eval/tests/test_c5_b0_metric.py` |
| Freeze handoff | plan + `docs/plan_c5_b0a_pm_prereg_v1_0_6_FREEZE.template.json` |
| Postrun coverage | `reports/provenance/C5_b0a/p1_usage.json` + `p1_usage.postrun.json` |
| P0/schema | `p0_native_sanity.json` + `m_cohort_preflight.json` + plan |
| Sizing/splits (1,680/560/600; F=360, L=360, P=480, PA=480) | plan + `m_cohort_preflight.json` |
| v1.0.5 residual closure (1 CONTINUE / 2 NARROW, 8 residuals) | v1.0.5 synthesis + external review request |

## 5. Fact classification

**[VERIFIED] this round:** sync/fetch/ff-only-pull success; HEAD `e619885c…` == origin/main; clean tree pre-pull;
existence and line counts of all twelve basis files; absence of `review_GLM.md` before this round; presence of
dispatch/prompt/watch files; no training/evaluation run; no subagents spawned; no P1 usage; test 163 not opened.

**[DISPATCH-CLAIMED], unverified:** v1.0.5 posture (1 CONTINUE / 2 NARROW, 8 residuals); the eight v1.0.6 fixes
and their correctness; sizing 1,680/560/600 with F=360, L=360, P=480, PA=480; P0 results train +3.7617
[1.8917, 5.6050], val +5.2375 [2.5013, 8.0753]; absence of any trained P/PA/M result; T5Gemma2 D-108 STOP;
Phase 6 / B0-B / B1 / B2 / Stage C not approved.

## 6. Gate posture after this round

- **Unchanged and in force:** T5Gemma2 D-108 STOP; Phase 6 / B0-B / B1 / B2 / Stage C remain NOT approved;
  no trained P/PA/M result exists; v1.0.5 residual gates remain in force until a valid v1.0.6 verdict exists.
- **Not granted by this file:** P1 execution, test 163, any Phase 6/B0-B approval, any threshold change,
  any T5Gemma2 reopening.
- P0 numbers quoted anywhere downstream must cite the provenance JSON after a reviewer has actually read it;
  this round cannot certify them.

## 7. Must-fix (process) before re-dispatch

1. **Round execution order:** the reviewer must be able to read all basis documents before the report is
   written; "no reads" + "write report" + "answer Q1–Q13" is unsatisfiable as dispatched.
2. **Fail-fast guard:** add a dispatch check that the reviewer quotes (a) HEAD SHA and (b) at least one
   verbatim line from `docs/plan_c5_b0a_pm_prereg_v1_0_6.md` §13.5 and from `runner/c5_mt5_lora_b0.py`;
   reject reports lacking both as invalid rounds (this report deliberately lacks them).
3. **Record semantics:** this file must be logged as "round invalid — process failure", not as a
   CONTINUE/NARROW/STOP verdict on v1.0.6 content, and not as evidence that any fix was verified.
4. **Question numbering:** the re-dispatch must confirm Q1–Q13 wording against
   `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_6_2026-11-09.md` so the §4 map can be corrected.

## 8. Round verdict

**NARROW (process-level).** Not CONTINUE: this round yields zero verified content findings, so it cannot lift
any v1.0.5 residual or gate any phase forward. Not STOP of the program: no negative technical evidence was
found either — the correct action is to re-run this v1.0.6 review with working read access under the same
constraints (no training/eval, no test 163, no P1, no subagents, T5Gemma2 D-108 STOP stands, Phase 6 / B0-B /
B1 / B2 / Stage C remain unapproved, no post-result threshold changes).

## 9. Attestation

- Authored solely by GLM 5.3 Flash in this round; no other model's review was read or reused.
- No training or evaluation executed; no test 163 opened; no P1 used; no subagents; no T5Gemma2 reopening;
  no threshold changes proposed.
- Sole write this round: this file. All other repository content untouched.
- Unverified work is labeled as such; nothing in this report should be cited as verification of any v1.0.6 fix.