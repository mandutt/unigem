# External Review — C5 A1 Full Train 2-epoch and grounded gate re-adjudication

- Reviewer: GLM 5.3 Flash (independent external review thread, multi-model round)
- Date: 2026-11-07
- Repository: `mandutt/unigem`, branch `main`
- Review basis: `reports/EXTERNAL_REVIEW_C5_A1_FULLTRAIN_2026-11-07.md` (read in full, 350 lines)
- Workspace sync: `git fetch origin` + `git pull --ff-only origin main` → **already up to date**;
  HEAD = **`5694cc7fbe0d371f0b4800830037fa36269e44c3`** (2026-11-07 09:36:58 +0900,
  "docs: add full-train 3-AI review prompts and dispatch")
- Mode: consultation only. Read-only except this file. No training run, no subagents,
  no additional LLM calls. test 163 not opened; P1 data not used.

---

## 0. Method and scope

I read the full request file, then verified claims against committed artifacts:

- `reports/provenance/C5_a1/full_2ep/selection.json`, `selection_summary.json`
- `reports/provenance/C5_a1/full_2ep/eval_step_{0647,1293,1940,2586}/eval.metrics.json` and `eval.jsonl`
- `reports/provenance/C5_a1/full_2ep/error_analysis_1940_vs_2586.json` and `error_analysis_stdout.txt`
- `reports/provenance/C5_a1/pilot300_val161/metrics.json`
- `reports/C5_A1_full_train_2ep_2026-11-07.md`, `reports/C5_A1_error_analysis_2026-11-07.md`,
  `reports/C5_A1_3AI_REVIEW_SYNTHESIS_2026-11-06.md`, `reports/C5_A1_bare_val161_2026-11-06.md`,
  `reports/C5_STATUS_2026-11-06.md`
- `docs/decisions.md` (D-080, D-083), `docs/gates.md` (G-C5, AM-5, AM-8, sample-size table)
- `eval/slot_verify.py`, `runner/c5_a1_select.py`, `runner/c5_a1_error_analysis.py`,
  `runner/c5_a1_lora.py` (checkpoint/eval wiring), `runner/c5_a1_eval_batch.py`,
  `eval/tests/test_a1_runner.py`, `logs/C5/a1_full_train_2ep.log` (tail)
- `reports/provenance/C5_clean/splits.json` (1293/161/163, seed 42, sha256 recorded)

Limitations: `data/external/f5_pairs_v3_clean.jsonl` and model weights are gitignored and absent
in this workspace, so source passages could not be re-parsed directly. Source-side claims were
verified through the committed `error_analysis_1940_vs_2586.json` / `error_analysis_stdout.txt`
(which record extracted source slots and values) and the `eval.jsonl` predictions/targets.
Clopper-Pearson intervals below were computed by me (exact binomial summation / bisection).

## 1. Executive summary

1. All headline numbers in the request reproduce from artifacts (see §2). One execution fact is
   confirmed from the training log: step 2586, `elapsed_s 15617.9`, `rss_gb 3.88`, exit path normal.
2. Under **strict pre-registered D-083**, no full-train checkpoint is eligible
   (`selected_step: null`, fallback pilot300). This record must stand.
3. The three "verifier normalization candidates" are real and verified in the artifacts, but they
   are **not one homogeneous class**: the 02742 URL case is a source-side measurement artifact
   (line-broken URL truncated by extraction), while the 03978 (오전 qualifier) and 04709 (`18명` vs
   bare `18`) cases are **equivalence-policy decisions**, not extractor bugs. They should not be
   bundled into a single normalization switch.
4. Applying all three would make 1,940 and 2,586 160/161 — but it would **also make 1,293 eligible**
   (02742 is its only URL-class failure; repeated4 0.05866 just passes). Re-adjudication must
   therefore be a full re-selection over all checkpoints under a pre-registered D-084, not a
   hand-edit of two rows.
5. The genuine hallucination at 1,940/2,586 is 04951 (`2.3%`, `2.2%` — an invented JP-Morgan growth
   narrative absent from source and target). The claim "the only genuine new-slot failure is 04951"
   is scoped to 1,940/2,586 and does **not** extend to 647/1,293, which have unanalyzed failures
   (00114, 00818, 01767, 03086, 03801).
6. The 04709 case is mischaracterized in the request: the prediction **preserves `18명` twice**; the
   flagged `18` comes from the phrase `18 확진자`, which the extractor's fixed unit list does not
   parse. The source `18명` is **not missing** (request table says it is; artifact shows 15 missing
   slots, none of them `18명`).
7. 2,586's "compression gain" is real but paired with over-compression: preservation 0.4188 is
   **below the target's own implied preservation (~0.465)**, slot-free docs rise 4→11 (9/11 with
   target slots ≥1), and 73/161 docs lose slots. 1,940 dominates 2,586 on F1, slots/doc,
   preservation, and slot-free; 2,586 leads only on repeated4 (0.0445 vs 0.0514, both passing) and
   the single grounded doc count.
8. Recommendation: keep strict D-083 results; run a verifier audit and pre-register D-084
   (URL line-break join as measurement fix; narrowly scoped qualifier/unit rules with separate
   defect reporting); run human-50 on val with 1,940 as primary candidate; keep test 163 sealed
   until candidate freeze; make slot preservation a separately registered reporting criterion.

## 2. Verification of key numbers

| Claim | My check | Result |
|---|---|---|
| 2,586 steps, 2 epochs, wall 15,617.9 s, exit 0 | `logs/C5/a1_full_train_2ep.log` final step event; `eval_step_2586` present; runner has checkpoint-steps + eval-checkpoints + per-epoch `build_order` (unit-tested) | **confirmed** |
| pilot300: F1 0.657580, grounded 161/161, new 0, EOS 161/161, rep4 0.05535 | `pilot300_val161/metrics.json` (837 slots, 5.199/doc, preservation 0.45583, gen_len 248.3) | **confirmed** |
| 647: F1 0.669853, grounded 155/161, micro 0.00684, rep4 0.06840 | `eval_step_0647/eval.metrics.json` | **confirmed** |
| 1,293: F1 0.665946, grounded 159/161, micro 0.00234, rep4 0.05866 | `eval_step_1293/eval.metrics.json` | **confirmed** |
| 1,940: F1 0.682278, grounded 158/161, micro 0.00465 (4 new), rep4 0.05138 | `eval_step_1940/eval.metrics.json` | **confirmed** |
| 2,586: F1 0.668982, grounded 159/161, micro 0.00394 (3 new), rep4 0.04450, slot-free 11 | `eval_step_2586/eval.metrics.json` | **confirmed** |
| selection: `selected_step = null`, "no checkpoint met grounded >= 0.99", fallback pilot300 | `selection.json`, `selection_summary.json` | **confirmed** |
| Paired F1 CIs (1,940−pilot +0.0247 [+0.0120,+0.0373]; 1,940−2,586 +0.0133 [+0.0012,+0.0249]) | both reports, same numbers | **confirmed** (document-resampling bootstrap, single training seed) |
| 1,940 failures = 03978 / 04709 / 04951 | `error_analysis_1940_vs_2586.json` `grounded_failures` | **confirmed** (counts differ, see §8) |
| 2,586 failures = 02742 / 04951 | same file; source URL value `http://coronamap.` truncation recorded in `error_analysis_stdout.txt` | **confirmed** |
| 2,586 slot-free 11; 2 target-0, 3 target-1, 6 target-3~4; 9/11 real omission | `slotfree` entries incl. per-doc `target_slots` | **confirmed** |
| Drift: slots −98, F1 −0.0133, len −9.2, preservation −0.0573, slot-loss docs 73, corr +0.324/+0.351/+0.519 | `delta_1940_to_2586` | **confirmed** |
| test 163: A0 used (D-080, 0.6072), A1 unused | `docs/decisions.md` D-080; no A1 test artifacts | **confirmed** |
| Splits 1,293/161/163 seed 42 | `splits.json` | **confirmed** |

## 3. Strict D-083 vs verifier-normalization candidates (kept explicit)

| Item | Strict D-083 (authoritative record) | v2-candidate analysis (contingent, not adjudicated) |
|---|---|---|
| 1,940 | grounded 158/161 → **fail**; ineligible | 160/161 *if* qualifier+unit rules adopted; micro 2/860 = 0.00233; would pass all legs and win max-F1 |
| 2,586 | grounded 159/161 → **fail**; ineligible | 160/161 *if* URL rule adopted; micro 2/762 = 0.00262; eligible |
| 1,293 | grounded 159/161 → **fail** | **also becomes eligible** (02742 fixed; 03801 unanalyzed, likely remains); repeated4 0.05866 passes with 0.00134 margin |
| 647 | grounded 155/161, rep4 0.0684 → **fail** | 157/161 at best; rep4 still fails → ineligible regardless |
| fallback | pilot300 stays | unchanged under v2 (0 new slots either way) |

Nothing above changes today's decision. Any v2 outcome requires D-084 first.

## 4. Decisions D1–D5

### D1 — verifier v2 normalization. **Verdict: conditional (split the bundle)**

Evidence:

- `eval/slot_verify.py`: URL regex `https?://[^\s<>"')\]]+` cannot span the newline in
  `http://coronamap.\n site`; `_canonical` already strips trailing `.,;:!?()[]{}<>"'` from all
  kinds, so *trailing punctuation is already handled* — the residual URL defect is only the
  internal line-break truncation (source measured as `http://coronamap`).
- Time canonical keeps the qualifier: `오전9시30분` ≠ `9시30분`. Dropping 오전 is **omission**, not
  invention — but a verifier cannot silently equate them without collision handling, because a
  pred that asserted the *wrong* half-day (오후 where source had 오전) must still fail.
- Number canonical keeps the unit: `18명` ≠ `18`. The pred in 04709 contains `18명` twice
  (preserved) and the new `18` comes from `18 확진자` — the extractor's unit list
  (`원|달러|…|명|개|건|…`) does not include noun heads like 확진자, so this is an extractor
  coverage/equivalence gap, not a model-invented number.

Classification and allowed normalizations:

1. **URL line-break join — legitimate measurement fix, recommend adopting (under D-084).**
   Join a line break inside a URL span only when the pre-break text ends in `.` and the post-break
   fragment is a lowercase-alphanumeric URL continuation; ship with unit tests and corpus counts.
   This repairs source-side measurement and has near-zero falsification risk.
2. **AM/PM qualifier — equivalence policy, allow only narrowly and separately reported.** Rule
   shape: time slots match on hour/minute when the *summary side has no qualifier*; a mismatched
   qualifier still fails; when the source contains both 오전X시 and 오후X시, bare X시 stays new
   (uniqueness guard). Report every affected doc in a `qualifier_dropped` list.
3. **Number/unit — equivalence policy, allow only with a uniqueness guard.** Bare numeral N in the
   summary may match a source `N+unit` slot only if N is unique among source numerals in that
   document; report affected docs in a `unit_dropped` list. Extending the unit list (확진자 etc.)
   instead would re-extract everything and must be part of the audit, not a quick patch.
4. **Trailing punctuation: already implemented; do not re-register as new.**

Next steps: (i) audit script counting all three classes across the 1,617 passages (train/val/test
separately) plus collision/uniqueness checks; (ii) unit tests in `eval/tests/` for each rule;
(iii) draft D-084 text with exact rules, pseudo-code, and expected counts, for user approval.

### D2 — candidate. **Verdict: agree (strict), with 1,940 as exploratory human-review candidate**

Evidence: `selection.json` (`selected_step: null`, fallback pilot300) is the correct strict outcome;
the request's own pairing table shows 1,940 > pilot300 on F1 with CI excluding 0, and 1,940 > 2,586
on F1 [+0.0012, +0.0249]. D-083 forbids product promotion of a failing checkpoint, and nothing here
should promote 1,940 to product. Human review of a near-miss on **val** is compatible with D-083
and is the cheapest way to learn whether the remaining failures are real defects.

Next steps: (i) keep pilot300 as the only fallback/production-track candidate; (ii) register 1,940
as "near-miss exploratory candidate for human review only" in the D-084 text; (iii) forbid any test
163 use until a candidate is frozen post-D-084 + human-50.

### D3 — human 50. **Verdict: agree (before test; on val; blinded; stratified)**

Evidence: D-083 fixes "사람 50건은 test 전"; the 3-AI synthesis (M2/M7) already established the
reporting rubric and that slot-free/vacuous docs must be included. Human review also doubles as
adjudication of the three v2 candidates (are `9시30분`-for-`오전9시30분`, `18 확진자`-for-`18명`,
and the joined URL fact-preserving in context?).

Next steps: (i) build the 50-doc sample per Q9 below; (ii) rubric: fabricated entity/number, wrong
number/unit, qualifier error, negation/attribution error, critical omission, 3–5 sentence
compliance, overall utility; blinded to checkpoint identity; (iii) score pilot300 on the same 50 as
a control arm.

### D4 — test 163. **Verdict: agree (keep sealed; single use, later)**

Evidence: D-080 (A0 already consumed test 163 once, 0.6072), D-083 ("test 163은 A1 최종 후보 1개에만
1회"), AM-9 analog (test = final judgment, once). Opening it now would burn the single A1
measurement before the verifier/gate questions are settled.

Next steps: (i) record the unsealing precondition chain explicitly: D-084 registered → v2
re-adjudication done → human 50 done → single candidate frozen → one test run; (ii) keep
`selection_summary.json`'s "sealed / unused for A1" marker; (iii) no B-family use.

### D5 — next experiment. **Verdict: conditional — A first, then B; C deferred**

Priority: **A (verifier v2 audit + D-084 draft, ~1–2 h) → B (human 50, 2–3 h human) → gate/E folded
into D-084 → D (over-compression arm, only if the A1 track continues) → C (seed 43, defer)**.

Evidence: A and B are prerequisites for any re-adjudication and for the single test use; C
(~4.5 h CPU) does not change any current decision because selection is gate-blocked, not
variance-blocked; D is only meaningful once the candidate step (1,940-class) is confirmed.

Next steps: (i) run A this week; (ii) schedule B immediately after; (iii) hold C and D until the
D-084 adjudication, then decide based on whether margins (e.g., 1,293's repeated4 0.05866 vs 0.06)
are decision-relevant.

## 5. Questions Q1–Q12

### Q1 — URL normalization legitimacy. **Verdict: agree, narrowly**

Evidence: source truncation `http://coronamap.` → canonical `http://coronamap` is recorded in
`error_analysis_stdout.txt`; the model's `http://coronamap.site` is the *correct* full URL of the
source's own link. `http://coronamap.\n site` and `http://coronamap.site` should count as the same
URL **when the join is provable from form** (dot before break, lowercase URL-grammar continuation).
This failure recurs at 647, 1,293, and 2,586 — it is systematic, not checkpoint-specific. Risk
case: a sentence-final URL followed by a new sentence starting with a lowercase word could be
over-joined; the conservative pattern and a corpus diff (count joined URLs; eyeball all of them)
keep this safe. Trailing punctuation is already stripped in `_canonical`.

Next steps: exact regex + tests; corpus-wide count of affected URLs; re-extract and diff source
slot sets for all 1,617 passages.

### Q2 — 오전/오후 qualifier. **Verdict: conditional — separate category, not silent equality**

Evidence: `오전 9시 30분` vs `9시 30분` — the time value exists in the source; only the qualifier
is dropped (03978; the pred also contains the source's 오전10시/오전10시20분, consistent with an
오전 context). Treating omission as "new slot" conflates omission with invention; treating it as
automatically equal would let a wrong half-day pass. The defensible middle: match on hour/minute
only when the summary side carries no qualifier, keep qualifier-mismatch as new, guard the
both-qualifiers collision, and report `qualifier_dropped` per doc.

Next steps: count docs where source has both 오전X시 and 오후X시; add `qualifier_dropped` to the
eval schema; put 03978 into the human-50 sample to confirm a human reads the pred as fact-preserving.

### Q3 — `18명` vs `18 확진자`. **Verdict: conditional — uniqueness-guarded unit equivalence**

Evidence: the request's framing ("모델의 `18 확진자`를 `18`로 추출, 원문은 `18명`") is right in
spirit but the artifact shows the pred *also* preserves `18명` twice; only the bare `18` from the
`18 확진자` phrase is new, because the unit list has no head-noun coverage. Equivalence "number
regardless of unit" is too permissive (`18명` vs `18억원` confusion would pass); the
uniqueness-guarded rule (bare N matches N+unit iff N unique in source) fixes this case without
opening that hole.

Next steps: count documents with duplicate numerals across units (collision rate); add
`unit_dropped` reporting; decide unit-list extension vs match rule inside the same D-084.

### Q4 — pre-register as D-084 vs post-hoc. **Verdict: agree — D-084 mandatory, post-hoc forbidden**

Evidence: `docs/gates.md` header: "결과를 본 뒤 임계값을 바꾸지 않는다. 변경 시 사유 기록 + 사용자
승인"; AM-5(iii) "임계값 완화·결과 후 기준 변경 불허"; AM-8 "재개는 새 사전 선언 실험으로만 하며 이전
실험의 사후 재해석 금지". The request itself states this (§3.3). Two additional points the request
does not make: (a) a *measurement* fix and an *equivalence policy* change should be registered as
two explicitly separated clauses of D-084, because they carry different risk; (b) the side effect
that 1,293 becomes eligible means v2 must trigger a **full re-selection** (`selection_v2.json`),
not a retroactive edit of two rows. D-083's strict record stays in force until D-084 is approved.

Next steps: draft D-084 (rules, counts, guard conditions, re-selection protocol, explicit
"D-083 results unchanged" clause); user approval before any code change; version the verifier
(`slot_verify.py` v2) alongside v1.

### Q5 — grounded ≥ 0.99 at n=161; add slot preservation to G-C5? **Verdict: conditional**

Evidence (my exact Clopper-Pearson computations, 95% two-sided):

| doc-level grounded | rate | CP95 |
|---|---:|---|
| 155/161 | 0.9627 | [0.9207, 0.9862] |
| 158/161 (1,940) | 0.9814 | [0.9465, 0.9961] |
| 159/161 (1,293, 2,586) | 0.9876 | [0.9558, 0.9985] |
| 160/161 (v2 pass) | 0.9938 | [0.9659, 0.9998] |
| 161/161 (pilot300) | 1.0000 | [0.9773, 1.0000] |

Even a perfect 161/161 cannot statistically certify 99% at doc level (lower bound 0.977; rule of
three: 0 failures in 161 → upper bound 1.86%). The gate is therefore a deterministic screen, not a
certificate — acceptable as a pre-registered conservative bar, but it must not be sold as "≥99%
proven". At slot level (the actual G-C5 metric per D-080/CP3-1), n = 762–877 per eval exceeds
gates.md's ≥600 bar for resolving 0.5%: pilot300 0/837 → CP upper 0.44% (G-C5-consistent);
1,940 4/860 → CP upper ≈1.19% (point 0.465% passes ≤1%, CI does not); 2,586 3/762 → upper ≈1.15%.
Report both levels with CIs.

On slot preservation: D-080/CP3-1 deliberately set coverage/preservation as reference-only, and an
absolute preservation gate is ill-posed — the **targets themselves preserve only ~0.465** of source
slots (target 5.6335 slots/doc vs val mean 12.106 source slots/doc from the A0 val161 file), while
1,940 reaches 0.476 and 2,586 falls to 0.419. A defensible extension is a *relative* criterion
(e.g., preservation ≥ target − 0.05, and "slot-free docs with target slots ≥ 3" = 0) registered in
D-084 — not folded into `grounded`, and not retroactive.

Next steps: (i) add CP CIs for grounded (doc) and new-slot micro (slot) to all eval reports;
(ii) draft the relative preservation criterion with its val-distribution baseline; (iii) keep
`grounded` semantics unchanged in v1.

### Q6 — primary for human 50: 1,940 or 2,586? **Verdict: 1,940**

Evidence: 1,940 leads on F1 (0.6823 vs 0.6690, paired CI excluding 0), slots/doc (5.342 vs 4.733,
target 5.633), preservation (0.4761 vs 0.4188; only 1,940 is at/above the target-implied 0.465),
and slot-free (4 vs 11, of which 9/11 at 2,586 are real omissions). 2,586 leads only on repeated4
(0.0445 vs 0.0514 — both pass ≤0.06) and by one grounded doc, which v2 would equalize anyway. The
over-compression analysis (73/161 docs losing slots, new slot-free 8) makes 2,586 the worse
candidate despite its cleaner repetition. Both share the 04951 hallucination.

Next steps: designate 1,940 primary, 2,586 secondary (useful as the over-compression exemplar);
pilot300 as control arm; freeze this ordering in the human-50 protocol document.

### Q7 — does the grounded definition's vacuous pass invalidate it; extend G-C5? **Verdict: conditional**

Evidence: `grounded` = "no new slot" by definition; empty summaries pass vacuously (2,586: 11 docs;
`nonvacuous_grounded` 148/150 = 0.9867 is already computed and must be surfaced in every table).
The request's §3.4 correctly shows 159/161 is not "99% preservation". But G-C5's purpose
(환각 통제) argues against folding omissions into the hallucination gate; the right fix is a
separate, pre-registered preservation criterion (Q5) plus mandatory non-vacuous reporting.

Next steps: (i) always report `grounded`, `grounded_nonvacuous`, `slot_free`, `slot_preservation`
side by side; (ii) put the 11 slot-free docs and the 6 "target 3–4 → 0" docs into human 50;
(iii) register the relative preservation criterion in D-084 for future runs.

### Q8 — was 2 epochs the right call? **Verdict: agree (as pre-registered); do not relitigate**

Evidence: D-083 pre-registered 2 epochs with a 4-point checkpoint grid; the grid is exactly what
makes the 1,940-vs-2,586 trade-off observable. 1 epoch (1,293) does *not* pass the gate either
(159/161) and has lower F1 (0.6659); the val optimum sits between the epoch marks (1,940 ≈ 1.5
epochs). Over-compression at 2,586 is a schedule/capacity symptom (constant lr 2e-4, batch 1), not
proof that "2 epochs" was wrong. Re-running full train now would cost ~4.5 h CPU to move a decision
that is currently blocked by the verifier, not by the schedule.

Next steps: (i) keep the checkpoint grid in any future run; (ii) if a new arm is approved later,
test lr decay or 1.5-epoch stop, one change at a time, pre-registered; (iii) do not re-run seed 43
before D-084 adjudication.

### Q9 — human-50 composition. **Verdict: agree — stratified, deduped, blinded**

Proposed allocation (val 161, dedup by id, total 50):

1. Failure probes (5): 04951 (both steps), 03978, 04709, 02742, 03801.
2. Slot-free union (11): 00138, 00159, 00426, 00450, 00706, 00942, 02741, 03220, 03348, 03915,
   04769 (2 vacuous controls: target 0).
3. Top slot-loss Δ ≤ −6 (8): 01082, 04855, 03991, 00476, 05207, 05292, 05517, 00644.
4. Lowest-F1 decile, minus overlap (~10 new docs, incl. 04769 if not already covered).
5. Longest outputs (~2): e.g., 00942/00138 (352 tokens) if not already in.
6. High-quality controls (3): e.g., 05220 (F1 0.8013), 05392 (0.7977), 04798 (0.7698).
7. Random stratified remainder to 50 (~11), seed-fixed.

Each doc judged for: fabricated entity/number, wrong number/unit, qualifier error, negation and
attribution errors, critical omission, 3–5 sentence compliance, utility. Blinded to checkpoint;
score pilot300 on the same 50.

Next steps: (i) generate the sample list programmatically from the eval JSONLs with a fixed seed;
(ii) publish the rubric before scoring; (iii) record per-doc verdicts in provenance JSON.

### Q10 — open test 163 now? **Verdict: disagree (keep sealed)**

Evidence: as D4. The request's own §6 forbids it, D-080 shows the A0 precedent, and any v2
re-adjudication could change which checkpoint is the candidate — opening test before that would
waste the single shot. "A1 has not used it" is the correct framing (A0's earlier use stands).

Next steps: keep the seal; write the unsealing precondition chain into the D-084 draft; after the
single use, mark test 163 consumed for A1 in `selection_summary.json`.

### Q11 — next experiment priority. **Verdict: A → B, then D-084 registration; C last**

Evidence: A (verifier audit, ~1–2 h CPU) unblocks the entire gate question and is a prerequisite
for B's interpretation; B (human 50, ~2–3 h human) is required before any test use and adjudicates
both candidates and v2; D (over-compression arm, ~4.5 h CPU) is only worth running if the A1 track
continues past human review; C (seed 43, ~4.5 h CPU) is a robustness check whose value rises only
once a checkpoint actually passes a registered gate; E (gate redesign) is not a standalone
experiment — it is the D-084 registration itself.

Next steps: run A immediately; draft D-084 in parallel; schedule B on completion; queue C/D behind
the D-084 adjudication.

### Q12 — factual errors, exaggerations, omissions in the request. **Verdict: minor errors found; core claims sound**

Errors:

1. §3.1, 03978: "missing `오전9시30분` 포함 **8개**" — artifact: **7** missing slots
   (1일, 45, 15일, 1, 오전9시30분, 10, 20).
2. §3.1, 04709: "missing `18명` 포함 **18개**" — artifact: **15** missing slots, and **`18명` is
   not among them** (the pred preserves `18명` twice; `18명` is a *preserved* slot). The character
   of the failure (bare `18` from `18 확진자`) is as described; the missing-list claim is not.
3. §3.3 "진짜 신규 slot 실패는 `04951` 1건" — true **only for 1,940/2,586**. At 647 the unanalyzed
   failures 00114, 00818, 01767, 03086 exist; at 1,293, 03801 (`www.shucle.com` identifier) is
   unanalyzed. The taxonomy claim should be scoped explicitly.

Omissions:

4. The v2 side effect that **1,293 becomes eligible** (and 647 improves to 157/161) is unstated;
   re-adjudication scope is therefore larger than "1,940 and 2,586 pass".
5. The target's own implied preservation (~0.465 = 5.6335/12.106) is unstated; without it, Q7's
   "add slot preservation" invites an ill-posed absolute threshold.
6. Doc-level statistical power (CP intervals above; rule of three 1.86% at n=161) is unstated;
   "grounded ≥ 0.99" reads stronger than n=161 can certify.
7. pilot300's longer generations (gen_len 248.3 vs 199.5/190.3) and its 6/161 slot-free docs are
   not carried into the comparison tables; relevant when interpreting F1 differences (length
   sensitivity) and the fallback's own quality.
8. The request does not state that the clean filter itself was adjudicated with the v1 extractor;
   adopting v2 requires re-running the clean check to confirm the 1,617 set remains clean (a
   target containing the truncated URL form would become "new" under v2 source extraction).

No exaggeration found in the headline claims; the strict-vs-candidate separation in the request is
explicit and correct.

## 6. Must-fix (priority order, max 7)

1. **Do not apply any verifier normalization retroactively.** D-083 strict results
   (`selected_step: null`, pilot300 fallback) remain the record until D-084 is registered and
   approved. Any v2 numbers go to a new `selection_v2.json` with a D-084 reference.
2. **Split the normalization bundle.** URL line-break join = measurement fix; AM/PM and number/unit
   = equivalence policies with uniqueness guards and separate `qualifier_dropped` / `unit_dropped`
   reporting. Register them as distinct D-084 clauses.
3. **Re-adjudicate all checkpoints under v2, not just 1,940/2,586.** 1,293 becomes eligible under
   v2; the selection procedure (gate → max F1 → tie earlier) must re-run over {647, 1,293, 1,940,
   2,586} plus the pilot300 fallback.
4. **Extend the error analysis to 647 and 1,293** before any taxonomy claim: 00114, 00818, 01767,
   03086, 03801 are unanalyzed new-slot failures that bound how much the "only 04951 is real"
   narrative can be generalized.
5. **Publish CP confidence intervals** for doc-level grounded and slot-level new-slot micro in
   every eval report, with the non-vacuous grounded rate alongside; stop presenting 161-doc gates
   as statistical certificates.
6. **Correct the request's counts** (03978: 7 not 8; 04709: 15 not 18; `18명` preserved, not
   missing) in a short errata note, so downstream readers do not inherit the wrong missing-list.
7. **Write the test-163 unsealing precondition chain** (D-084 → v2 re-adjudication → human 50 →
   candidate freeze → single run) into the D-084 draft and keep the seal until then.

## 7. Additional experiments (max 5, with expected cost)

1. **Verifier v2 corpus audit** — count line-broken URLs, qualifier collisions, numeral/unit
   collisions across all 1,617 passages (train/val/test separately); re-extract source slot sets
   and diff v1→v2; re-run the clean-filter check. Cost: ~1–2 h CPU + 1 h review.
2. **Human 50 (blinded, stratified, rubric per Q9), 1,940 primary + pilot300 control.**
   Cost: ~2–3 h human time.
3. **Over-compression arm** (only if A1 track continues): one pre-registered change (lr linear
   decay or 1.5-epoch stop), same grid. Cost: ~4.5 h CPU + ~1 h eval.
4. **Seed 43 full-train replication** (deferred until a checkpoint passes a registered gate).
   Cost: ~4.5 h CPU + ~1 h eval.
5. **Slot-preservation auxiliary probe** (exploratory, pilot-scale only: length/slot-count
   auxiliary loss at 300 steps) to see whether slot-free/over-compression responds before
   committing to a full arm. Cost: ~30–60 min CPU.

## 8. Statistical appendix (computed for this review)

Exact binomial Clopper-Pearson 95% intervals (my computation):

| quantity | point | CP95 |
|---|---:|---|
| grounded 155/161 | 0.9627 | [0.9207, 0.9862] |
| grounded 158/161 | 0.9814 | [0.9465, 0.9961] |
| grounded 159/161 | 0.9876 | [0.9558, 0.9985] |
| grounded 160/161 | 0.9938 | [0.9659, 0.9998] |
| grounded 161/161 | 1.0000 | [0.9773, 1.0000] |
| new-slot micro 0/837 (pilot300) | 0.0000 | upper 0.00440 |
| new-slot micro 2/854 (1,293) | 0.00234 | [0.00028, 0.00843] |
| new-slot micro 4/860 (1,940) | 0.00465 | [0.00127, 0.01187] |
| new-slot micro 3/762 (2,586) | 0.00394 | [0.00081, 0.01146] |
| new-slot micro 6/877 (647) | 0.00684 | [0.00251, 0.01483] |

Reading: pilot300's zero-new-slot record is G-C5-consistent (upper 0.44% < 1%). 1,940/2,586 point
estimates pass the ≤1% micro gate but their CI uppers cross it — one more reason the doc-level
grounded screen, slot-level micro, and human review must be read together rather than any single
number standing alone.

## 9. Final recommendation

The full-train run itself is sound and honestly reported: the pre-registered D-083 gate was applied
as written, no checkpoint passed, and the pilot300 fallback was retained without product promotion.
The most valuable next move is not a new training run but a measurement audit: the five
checkpoint-level grounded failures decompose into one clear source-measurement artifact (the
line-broken URL, which also fails 647 and 1,293), two genuine equivalence-policy questions
(오전 omission; `18명`/`18 확진자` where the prediction actually preserves the source form), and one
real hallucination (04951's invented 2.3%→2.2% growth narrative). Register D-084 with the URL fix
and narrowly guarded qualifier/unit rules, re-select over all checkpoints, and let human-50 — with
1,940 as primary, pilot300 as control — adjudicate what the verifier cannot. Keep test 163 sealed
until a single candidate is frozen, and keep the strict D-083 record untouched regardless of what
v2 shows; a gate that can be lowered after looking at the results is not a gate.

Independently of the gate question, 2,586 should not be promoted on its repetition advantage: it
is the only full-train checkpoint whose slot preservation (0.419) falls below the targets' own
implied preservation (~0.465), it more than doubles slot-free docs (4→11, 9 with real target-slot
losses), and its F1 deficit to 1,940 is statistically confirmed. If the A1 track proceeds after
human review, the highest-value training-side experiment is a pre-registered over-compression
control (1.5-epoch stop or lr decay), with seed 43 deferred until a checkpoint actually passes a
registered gate.