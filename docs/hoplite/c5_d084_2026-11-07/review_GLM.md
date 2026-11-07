# External Review — C5 verifier v2 audit, D-084 re-selection draft (GLM 5.3 Flash)

- Reviewer: GLM 5.3 Flash (independent external review thread, multi-model round)
- Date: 2026-11-07
- Repository: `mandutt/unigem`, branch `main`
- Review basis: `reports/EXTERNAL_REVIEW_C5_D084_2026-11-07.md` — **read in full, all 446 lines**
  (read across chunks; no summary or excerpt was relied on)
- Workspace sync: `git fetch origin` + `git pull --ff-only origin main` → "Already up to date";
  HEAD = **`fc31b0719f3cd0ad1a9c18b326baf7426c12103e`** (2026-11-07 10:47:30 +0900,
  "docs: add D-084 review prompts with Sonnet 5.5 high"); verified `HEAD == origin/main`.
- Mode: consultation only. Read-only except this single report file. No training run, no
  generation, no subagents, no additional LLM calls. test 163 **not opened**; P1 data **not used**.

---

## 0. Method and scope

I read the full request, the complete D-084 draft (`docs/D-084_verifier_v2_draft_2026-11-07.md`,
260 lines), the v2 audit JSON + audit matcher code, the v1 verifier, the selection/eval code, and
the supporting reports, then **independently recomputed** the load-bearing numbers from the
committed artifacts:

- `reports/provenance/C5_a1/full_2ep/selection_summary.json`, `selection.json`
- `reports/provenance/C5_a1/full_2ep/verifier_v2_audit.json` (full) and
  `runner/c5_a1_verifier_v2_audit.py` (full `match_v2` logic)
- `eval/slot_verify.py` (v1, unmodified — confirmed untouched)
- `reports/provenance/C5_a1/full_2ep/eval_step_{0647,1293,1940,2586}/eval.metrics.json` **and**
  `eval.jsonl` (per-document rows recomputed)
- `reports/provenance/C5_a1/pilot300_val161/metrics.json` + `predictions.jsonl` (recomputed)
- `reports/provenance/C5_a1/full_2ep/error_analysis_1940_vs_2586.json`
- `reports/C5_A1_full_train_2ep_2026-11-07.md`, `reports/C5_A1_error_analysis_2026-11-07.md`,
  `reports/C5_A1_verifier_v2_audit_2026-11-07.md`, `reports/C5_A1_3AI_REVIEW_SYNTHESIS_2026-11-07.md`
  (full), `reports/EXTERNAL_REVIEW_C5_A1_FULLTRAIN_ERRATA_2026-11-07.md`
- `docs/decisions.md` (D-022, D-080, D-083), `docs/gates.md` (G-C5, AM-3/5/8),
  `reports/provenance/C5_clean/splits.json` (1293/161/163, seed 42)
- `runner/c5_a1_select.py`, `runner/c5_a1_eval_batch.py` (gate arithmetic)

**Not verifiable in this sandbox** (P0 passages are not present — `data/external/` is empty here,
consistent with D-084 §11): the source-context adjudication of the 5 excluded flips, the
`REPORT-news_r-03992-00001` "fine.fss." wrap context, and the "16/161 val docs share article
prefix with train" claim. Those remain local-side tasks; I mark them as pending, not as verified.

### Independent verification results

**Per-step strict metrics — recomputed from `eval.jsonl`, all match the request exactly:**

| step | F1 | grounded | new slots | slot-free | summary slots | EOS | rep4 | preservation | gen_len |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pilot300 | 0.657580 | 161/161 | 0 | 6 | 837 | 161/161 | 0.05535 | 0.45583 | 248.3 |
| 647 | 0.669853 | 155/161 | 6 | 2 | 877 | 160/161 | 0.06840 | 0.48729 | 193.2 |
| 1,293 | 0.665946 | 159/161 | 2 | 8 | 854 | 161/161 | 0.05866 | 0.45705 | 191.4 |
| 1,940 | 0.682278 | 158/161 | 4 | 4 | 860 | 161/161 | 0.05138 | 0.47610 | 199.5 |
| 2,586 | 0.668982 | 159/161 | 3 | 11 | 762 | 161/161 | 0.04450 | 0.41882 | 190.3 |

**Paired F1 bootstrap — independently reproduced** (2,000 resamples, seed 42, paired document
resampling; endpoints differ from the report only by RNG stream, conclusions identical):

| comparison | my mean diff | my 95% CI | report CI | conclusion |
|---|---:|---|---|---|
| 1,940 − pilot300 | +0.024698 | [+0.012021, +0.037114] | [+0.012027, +0.037295] | significant |
| 2,586 − pilot300 | +0.011402 | [−0.000399, +0.022848] | [−0.000398, +0.023058] | **includes 0** |
| 1,940 − 2,586 | +0.013297 | [+0.001197, +0.024757] | [+0.001197, +0.024928] | significant |

**Clopper–Pearson bounds (exact binomial bisection, one-sided 95%; synthesis quotes two-sided):**

| rate | point | CP95 upper (1-sided) | CP95 upper (2-sided) | G-C5 (≤1% new slots) |
|---|---:|---:|---:|---|
| pilot300 0/837 | 0.000% | 0.357% | ≈0.44% | **consistent** |
| 1,940 4/860 | 0.465% | **1.061%** | ≈1.19% | point-pass, CI-fail → **INCONCLUSIVE** |
| 2,586 3/762 | 0.394% | **1.014%** | ≈1.15% | point-pass, CI-fail → **INCONCLUSIVE** |
| doc-level 1 fail/161 | — | 2.91% | — | 0.99 doc gate is a screen, not a certificate |

**Prediction-level evidence (val docs only; verified directly in `eval.jsonl`):**

- 1,940 / `REPORT-news_r-02742-00001` prediction literally contains `coronamap.\nsite)` (wrapped);
  2,586's contains `coronamap.site)` (joined). This **proves the both-side repair requirement is
  load-bearing**: under v1 (no repair) 1,940 passes 02742 precisely because source and prediction
  are wrapped identically; repairing the source only would flip 1,940 into a *new* failure on this
  doc (a 160→159 regression risk), while repairing both sides keeps the match.
- 1,940 / `04709` prediction: contains `18명` twice, contains `18 확진자`, contains no `18일` —
  the single new slot is the bare `18` from `18 확진자`, exactly as the request/errata state.
- 1,940 / `04951` prediction: contains both `2.3%` and `2.2%` — genuine negative control confirmed.
- 2,586 slot-free 11 = target-slots 0:2 docs, 1:3 docs, 3–4:6 docs → **9/11 omit target slots** ✓;
  delta vs 1,940: 8 newly slot-free, 1 recovered.

### Two code-level findings on the audit matcher (material for this review)

1. **The audit matcher does NOT implement draft §5.5.** `match_v2` matches URLs through v1's
   `_canonical` (full lowercase + comma stripping). So **every v2 number in this review cycle is
   computed WITHOUT the URL case/comma fix**, although §5.5 is part of the drafted v2 spec.
   §5.5 only *tightens* (removes false accepts), so the final numbers can only be equal or lower —
   e.g., a currently-accepted 160/161 can drop. The request lists "audit matcher is not production
   v2" as a generic limitation but does not state this specific gap; the selection-sensitivity
   tables must be re-derived after §5.5 lands.
2. **The audit's `counter_alias=True` variant is looser than draft §5.4.** In the audit it skips
   the uniqueness guard *for all values* and accepts any bare number followed by `확진자` within
   24 characters, with no entity/scope check. It is a sensitivity probe, not the drafted clause.
   On val 161 it only changed 1,940 (159→160), but it must never become the production rule.

Also noted: the wrap-join regex accepts any `[a-z0-9]`-initial continuation token, so a sentence
word after a URL-terminated line can be wrongly joined (which can *create* new-slot failures, the
reverse of the intended fix). The corpus stats (3/7/902) are computed over clean 1,617 only; the
383 excluded pairs are flip-audited but not counted in the collision stats.

### State separation (kept explicit throughout)

| track | status |
|---|---|
| **Strict D-083 (v1, registered)** | unchanged: `selected_step: null`, fallback pilot300, test 163 sealed. **No gate change has been approved.** |
| **Verifier v2 (audit only, unregistered)** | exploratory re-scoring with a *candidate* matcher, **without §5.5**, alias variant = loose probe. All v2 numbers below are hypothetical-under-policy, not results. |
| **D-084** | DRAFT / unapproved. My verdicts are recommendations to the human decision-maker. |

---

## 1. Answers to the six headline questions (short form)

1. **Generic v2 baseline?** Conditional yes as the *exploratory* baseline, with URL-only and
   URL+qualifier arms reported alongside; §5.5 must be implemented and re-audited first. URL wrap
   join is the only pure measurement fix; qualifier-drop and bare-number-uniqueness are equivalence
   *policy* and must be labeled as such.
2. **18-counter alias?** Legitimate only as a separate, human-adjudicated clause (draft §5.4 is
   right; the audit's loose variant is not). It is entity/scope adjudication, not normalization.
3. **5 excluded flips?** Genuinely open — they cannot be adjudicated in this sandbox. Pre-register
   a rubric, adjudicate locally, acceptance = human-confirmed false accept 0 (ambiguous = false
   accept); corpus stays frozen inside D-084 either way.
4. **Outcome-informed exploratory approval?** Yes, conditional — with policy arms + spec hash
   frozen before final re-selection, §5.5 implemented, flips adjudicated, D-083 record untouched,
   and no product promotion. Rejecting v2 entirely is not warranted (the URL artifact is real and
   prediction-verified).
5. **Which candidate for human review?** Human review and selection eligibility are separate
   tracks: 1,940 stays the *human-50 exploratory primary* on quality grounds; 2,586 is the
   *mechanical selection candidate* under generic v2. Both go to human 50. Do not alias-in 1,940
   to make it eligible; do not make 2,586 the quality primary merely because it is eligible.
6. **Human 50 / G-C5 / test 163 / next experiment?** Human 50: same 50 docs, blind, 4 arms
   (pilot300 control, 1,293, 1,940 primary, 2,586 contrast), 2 raters, strata separated. G-C5:
   keep slot-level/doc-level split, report CP95 + INCONCLUSIVE (pilot300 consistent; 1,940 and
   2,586 point-pass/CI-fail). test 163: stay sealed until D-084 + audit + human 50 + freeze. Next:
   finish D-084 → human 50 → fresh P0 confirmatory set; seed 43 and the compression arm stay
   deferred.

---

## 2. Verdicts — D4-1 through D5-4

### D4-1 — Unit policy (generic uniqueness / +counter alias / no unit)

**Verdict: conditional** — generic uniqueness-guarded bare-number matching as the default, alias
only as a separate human-adjudicated clause; "no unit rule" acceptable as a conservative floor arm.

**Evidence:** numeric-unit collisions in 902/1,617 (55.8%) docs make unguarded unit-drop matching
dangerous (`18%`↔`18명`); the uniqueness guard keeps `04709` failing under generic v2 and keeps
`04951` (2.3%, 2.2%) as a genuine negative control (audit JSON). Under current numbers the unit
rule is *selection-neutral* (the URL+qualifier-only arm yields the same eligible set {pilot300,
1,293, 2,586}, max 2,586), so its main value is verifier correctness (e.g., resolving 647's `00818`),
not flipping selection — which lowers the temptation to tune it post hoc.

**Next steps:** (1) implement §5.3 with the forbidden-pair unit tests (`18%`↔`18명`, `18건`↔`18일`,
rounding, 만/억, `%`↔`퍼센트`); (2) report per-rule attribution (which doc resolved by which rule)
in `selection_v2.json`; (3) keep the alias arm reported separately, never merged into "generic".

### D4-2 — Generic candidate: 2,586 vs 1,293

**Verdict: conditional** — under the current (pre-§5.5) audit numbers the pre-registered rule picks
2,586; neither may be treated as a product candidate, and both belong in human 50.

**Evidence:** 2,586 F1 0.6690 > 1,293 0.6659 (no significance test reported for this 0.0030 gap);
both 160/161 under the audit matcher. But 2,586 shows over-compression: slot-free 11 (9 omit target
slots), preservation 0.4188 < target-implied ≈0.465, slots/doc 4.733, while 1,293 is at 0.4571 /
8 / 5.304. 2,586 − pilot300 F1 CI includes 0. The 3-AI round already rejected 2,586 promotion and
the request forbids promoting it as "terminal adapter" — that constraint still binds.

**Next steps:** (1) re-derive both candidates' numbers after §5.5 lands; (2) pre-register (now,
before re-selection) that the mechanical generic candidate is 2,586 with over-compression flags
attached; (3) include 1,293 as a human-50 arm so the choice is evidence-based, not policy-based.

### D4-3 — Alias candidate: 1,940

**Verdict: defer** (alias ratification) / **conditional** (1,940's candidacy).

**Evidence:** 1,940 is 159/161 under generic v2 and 160/161 only with the alias — the selection
outcome depends on the policy (audit JSON; sensitivity table). The request itself forbids adopting
the alias in order to rescue 1,940; the only clean path is: ratify the alias clause on independent
semantic grounds first, adjudicate each instance, then re-select. Note 1,940's quality case is
policy-independent: F1 0.682278 (best), preservation 0.47610 ≥ target-implied 0.465, slot-free 4,
rep4 0.05138, EOS 1.0, and significant paired F1 wins over both pilot300 and 2,586.

**Next steps:** (1) label a small alias ratification set (val alias candidates + a sample of the
902 collision docs, **not only 04709**); (2) if ratified, re-score all five systems under
generic+alias and re-run the eligibility logic; (3) until then, record 1,940 as "gate-ineligible
under generic v2; human-review primary candidate" — both labels at once, without contradiction.

### D4-4 — Gate additions (nonvacuous / coverage / CP / INCONCLUSIVE)

**Verdict: agree** — with concrete thresholds and denominators.

**Evidence:** `grounded` is vacuous on slot-free docs (2,586: 11 slot-free; 9 omit ≥1 target slot);
G-C5's own min-sample rule (`docs/gates.md`, AM-3/D-022: slots ≥300, Clopper-Pearson,
PASS/FAIL/INCONCLUSIVE mandatory) is currently violated *in spirit* by reporting point estimates
only: 1,940 4/860 CP95 upper 1.061% (2-sided ≈1.19%) and 2,586 3/762 upper 1.014% (≈1.15%) both
exceed the 1% criterion → INCONCLUSIVE; only pilot300 (0/837, upper 0.36%/0.44%) is consistent.
Doc-level 160/161 has 1 failure → CP95 upper 2.91%, so the 0.99 doc gate is a deterministic screen.

**Next steps:** (1) always report `grounded_nonvacuous` (denominator: docs with ≥1 summary slot;
2,586 = 148/150 = 0.9867), `slot_free` with target-slot breakdown (target ≥3 → "material omission"
count), and `slot_preservation` against the target-implied ≈0.465 reference; (2) report slot-level
new-slot micro with CP95 and an explicit INCONCLUSIVE label where the upper bound exceeds 1%;
(3) keep grounded ≥0.99 as an unchanged screen; add preservation as a *screening flag* (e.g.,
< 0.40 or non-inferiority vs pilot300 0.4558) rather than a hard gate, pending human 50.

### D4-5 — The 5 excluded flips (false accept / legitimate fix / defer)

**Verdict: defer** the substantive ruling (impossible here — no source passages in this sandbox);
**conditional** on the procedure and acceptance criterion below.

**Evidence:** the audit JSON shows exactly 5 v1→v2 grounded flips among the 383 excluded pairs
(`00291` v1_new=2020, `01844` 2021, `03253` 404, `04791` 20, `05019` 5000+200) — all consistent
with unit-dropped bare numbers newly matched by the §5.3 rule (e.g., bare `2020` ↔ `2020년`,
bare `5000` ↔ `5,000원`). Clean 1,617: v1/v2 difference 0. Whether each is a legitimate
`unit_dropped` equivalence or a false accept depends on source context that is not present here.

**Next steps:** (1) pre-register the rubric *before* adjudication: same numeric value + same
referent (entity/event/scope) + dropped unit semantically vacuous in context → legitimate;
ambiguous → false accept; (2) acceptance criterion: **human-confirmed false accept = 0 among ALL
v1→v2 flips in the 383** (not just these 5; ambiguous counts as false accept), per-pair evidence
spans recorded; (3) even legitimate flips do **not** re-enter clean/train within D-084 — corpus
re-freezing is a separate decision; the flips only inform it.

### D4-6 — URL case/comma false accept: fix in v2 now vs separate audit

**Verdict: conditional** — fix it *inside* D-084's v2 (not shipped without it), measured in the
same audit cycle; do not postpone it behind a separate audit, and do not finalize `selection_v2`
before it is measured.

**Evidence:** v1 `_canonical` lowercases the whole URL and strips commas, so
`.../Case?key=A,B` ≡ `.../case?key=ab` (verified in code). The audit matcher inherits this, so the
current v2 tables do not measure §5.5's effect. Since §5.5 only removes false accepts, it can only
lower grounded counts — meaning today's 160/161 figures are optimistic upper bounds under the
drafted spec. Exposure is small (3 wrap docs in clean) but the canonicalizer change touches every
URL match.

**Next steps:** (1) implement scheme/host-only lowercase with path/query case/comma/escape
preserved, with unit tests; (2) re-run the 383 target audit and the 5-system val re-scoring with
§5.5 included; (3) publish before/after counts so the "false accept 감소 확인" required by draft
§5.5 is actually demonstrated.

### D5-1 — Human 50 composition

**Verdict: conditional** — same 50 unique val docs, blind, randomized order, **4 arms**: pilot300
(strict fallback / control), 1,293 (generic runner-up, not over-compressed), 1,940 (exploratory
primary), 2,586 (compression contrast).

**Evidence:** 3-AI synthesis agreed on 50 unique blind docs with pilot300/1,940/2,586; adding
1,293 costs one extra rating per doc and directly informs D4-2, because 1,293 and 2,586 are the
two generic-v2 eligible candidates with materially different compression profiles (slot-free 8 vs
11, preservation 0.4571 vs 0.4188). Strata: 04951 (negative control), 03978/04709/02742
(normalization docs), 2,586's 11 slot-free docs, top slot-loss docs, lowest-F1 decile, longest
outputs, seeded random remainder; two raters, ≥20-doc overlap for agreement; targeted and random
strata reported separately; no naive bootstrap over the stratified 50.

**Next steps:** (1) freeze the 50-doc list + rubric (fabricated entity/number, wrong unit/qualifier,
negation/attribution, material omission, fluency, memory utility) before ratings; (2) run blind
with randomized arm order per doc; (3) report per-arm, per-stratum, with agreement stats.

### D5-2 — test 163

**Verdict: agree** — stay sealed now; open only after the full chain, once, for one A1 candidate.

**Evidence:** A0 already used test 163 in D-080 (char F1 0.6072; A0 clean-test grounding 0/163
PASS per `docs/gates.md` G-C5 status), so the project-level budget is "once-used by A0, one A1
use reserved" per D-083. `selection_summary.json` confirms `test_163: sealed / unused for A1`.
Nothing in the v2 audit touches test data (audit JSON scope field confirms val-only).

**Next steps:** (1) unseal checklist, in order: D-084 approved → v2 final (incl. §5.5) implemented
and tested → 383 flip audit clean → full re-selection (`selection_v2.json`) → human 50 done →
single candidate frozen (adapter hash, decoder config, verifier version+policy, gate) → one A1
run → no retuning afterwards; (2) label usage history on any future report: "A0: D-080; A1: this
run, 1st and only use"; (3) never use test 163 for model or policy selection.

### D5-3 — Next experiment

**Verdict: conditional** — order: (1) finish D-084 (spec freeze incl. §5.5 + alias decision path +
383 adjudication + re-selection), (2) human 50, (3) fresh P0 confirmatory set, (4) seed 43 only
after D-084+human, (5) compression arm only if human 50 confirms compression is the binding issue.

**Evidence:** the audit is done but its numbers are pre-§5.5 and the flips are unadjudicated, so
re-selection cannot be finalized today; G-C5 is INCONCLUSIVE for both full-train candidates at
CP95, which only a larger independent P0 set can resolve (299 zero-failure independent docs is the
best-case minimum for a 99% lower bound; at the observed ~0.4% slot-level rate, resolving CP95
upper ≤1% realistically needs ≥1,000–1,500 docs); seed 43 replicates a result whose evaluation is
still being defined — running it first risks another re-selection round.

**Next steps:** (1) execute D-084 steps 2–5 as drafted but with §5.5 inside step 2; (2) prepare the
human-50 protocol in parallel (no ratings yet); (3) scope the fresh P0 confirmatory set (no P1) for
after human 50.

### D5-4 — D-084 status: outcome-informed exploratory vs reject

**Verdict: conditional** — approve as **outcome-informed exploratory**, with binding conditions;
do not reject v2 outright.

**Evidence:** the sequence is unavoidably outcome-informed (D-083 failed all checkpoints before v2
was proposed), and the draft already contains the correct hygiene: D-083 record untouched (§6.1),
policy arms reported side-by-side (§6.2), explicit ban on alias-to-rescue-1,940, no product
promotion, test 163 sealed. The URL-wrap artifact is real and prediction-verified (see §0), so
discarding v2 would keep a known measurement defect in the gate. What prevents a clean "agree" is
that the audit omitted §5.5, the alias variant is looser than drafted, and the 5 flips are
unadjudicated — so approval must be conditional, and the result must remain labeled exploratory
and val-reused (AM-5: no threshold relaxation or post-result criterion change; AM-8: any future
product-path resumption needs a new pre-declared experiment).

**Next steps:** (1) freeze policy arms + spec hash before final re-selection; (2) complete Must-fix
items 1–4 below; (3) register D-084 (if approved) as a separate exploratory decision that
explicitly does not modify the D-083 entry.

---

## 3. Verdicts — Q1 through Q14

**Q1 (generic v2 baseline vs URL-only). Verdict: conditional.** Generic v2 (URL + qualifier-drop +
uniqueness-guarded bare number) is acceptable as the *exploratory* baseline: each rule has an
independent semantic rationale, the collision stats bound the risk (7/1,617 qualifier; 902/1,617
numeric, mitigated by the uniqueness guard), and the sensitivity table shows the unit rule is
selection-neutral today. But URL wrap join is the only pure *measurement* fix; the other two are
*equivalence policy* and must stay labeled as policy; §5.5 must be included and re-audited before
any numbers are final; and the URL-only arm should remain reported as the conservative floor.
*Next:* implement §5.5; report all three arms; per-rule attribution table.

**Q2 (18-counter alias as separate clause / human adjudication). Verdict: agree.** It is
entity/scope adjudication, not normalization: `04709` contains both `18일` and `18명` (so the
uniqueness guard correctly refuses), and resolving `18 확진자` → `18명` requires confirming the
same event/group/scope — a judgment no regex can make. The audit's alias variant (uniqueness skip
for all values + 24-char `확진자` window) is a probe and must not become the rule. *Next:* narrow
machine pre-filter (counter noun ∈ person-count class; source has the unit-bearing number; no
unresolved same-value conflict) + per-instance human sign-off recorded in the report
(`alias_adjudicated` with provenance); ratify on an independent labeled sample.

**Q3 (5 excluded flips + acceptance criterion). Verdict: defer (ruling) / conditional (criterion).**
They are false-accept *candidates*; adjudication requires the P0 passages, which are not in this
sandbox. Acceptance criterion: human-confirmed false accept = 0 across **all** flips in the 383
(ambiguous → false accept), rubric pre-registered, evidence spans recorded, corpus frozen inside
D-084 regardless of outcome. *Next:* see D4-5.

**Q4 (D-084 outcome-informed exploratory approval; D-083 preservation). Verdict: conditional.**
Approvable with the D5-4 conditions; rejecting v2 entirely is unnecessary and would preserve a
verified measurement defect. D-083 strict must remain byte-identical in `docs/decisions.md` and
`selection_summary.json`; v2 results live only in `selection_v2.json` with `verifier_version` +
policy + spec hash, side-by-side with v1. *Next:* see D5-4.

**Q5 (1,940 ineligible under generic v2; 2,586 is max-F1; conflict with 3-AI's human primary).
Verdict: conditional — separate the roles.** The 3-AI recommendation concerned *human review
quality*, which never required gate eligibility; the audit changes *selection eligibility*, not the
quality evidence (1,940: best F1 0.6823, preservation 0.4761 ≥ 0.465 target-implied, slot-free 4,
significant paired wins). Keep 1,940 as human-50 exploratory primary; record 2,586 as the
mechanical generic-v2 selection candidate; put both in front of raters. Do not alias-in 1,940 to
pass, and do not crown 2,586 quality-primary merely because it is eligible (its own
over-compression profile argues against that on quality grounds). *Next:* dual-label table in
`selection_v2.json` (eligibility per policy × human-review role); human 50 with both arms.

**Q6 (alias approval grounds; 18일/18명 collision adjudication). Verdict: conditional.** Grounds
must be semantic and outcome-blind: a bare number followed by a person-counter noun (`확진자`)
supplies the unit lexically, and `명`-class units are the only ones this alias may target; approve
it only if it survives ratification on instances **other than** 04709 as well. For the collision:
(a) enumerate same-value source slots (`18일`, `18명`); (b) the summary counter noun must select
exactly one unit class; (c) confirm referential identity (same event/group/time scope as the
`18명` sentence); (d) record evidence spans + adjudicator; (e) unresolvable → stays `new` (fail).
*Next:* see Q2; add the collision case as a unit test in both directions.

**Q7 (human 50 composition). Verdict: agree** — all four systems (1,940, 2,586, 1,293, pilot300)
on the same 50 docs, blind, randomized. See D5-1 for strata/raters/reporting. *Next:* freeze list
and rubric first.

**Q8 (G-C5 additions; thresholds; denominators). Verdict: agree.** Concretely: `grounded_nonvacuous`
(≥1 summary-slot docs; 2,586 = 148/150 = 0.9867), `slot_free` with target-slot breakdown (target
≥3 slots → material omission; 2,586 has 6 such docs), `slot_preservation` vs target-implied ≈0.465,
slot-level new-slot micro with CP95 + INCONCLUSIVE where upper >1% (pilot300 0/837 → 0.36%/
0.44% consistent; 1,940 4/860 → 1.06%/1.19% INCONCLUSIVE; 2,586 3/762 → 1.01%/1.15% INCONCLUSIVE),
doc-level and slot-level denominators reported separately, doc-level 0.99 kept as a screen (1
failure/161 → CP95 upper 2.91%). Coverage/adequacy stays a separate criterion; grounded must not
be redefined into an omission gate. *Next:* put these fields in `SlotReportV2`/`selection_v2.json`.

**Q9 (keep doc/slot split with CP+INCONCLUSIVE, or enlarge the sample?). Verdict: agree (keep now,
enlarge later).** The split plus CP95/INCONCLUSIVE is exactly what the current data supports;
enlargement belongs to the fresh P0 confirmatory set (E) after D-084 + human 50. test 163 alone
cannot certify 99%. *Next:* scope set E (no P1), size it so the CP95 upper at the observed rate
can fall below 1% (realistically ≥1,000–1,500 docs; 299 zero-failure is the best-case minimum).

**Q10 (when may test 163 open; how to label A0/A1 history). Verdict: agree (seal now).** Unseal
only after the full chain in D5-2; label every future use with both A0 (D-080, 0.6072, grounding
0/163) and A1 history; one A1 use only; never for selection. *Next:* publish the checklist in the
D-084 decision text when approved.

**Q11 (URL case/comma fix in v2 now vs separate audit). Verdict: conditional (fix now, inside
D-084, with re-audit).** A known false accept must not survive into a "v2"; but its measurement is
currently missing, and since the fix only tightens, today's numbers are optimistic. A postponed
"separate audit" is acceptable only if it blocks finalization of `selection_v2` until done —
simpler to keep it inside D-084. *Next:* see D4-6.

**Q12 (draft Scope/DoD/API/order gaps; Must-fix). Verdict: conditional.** The draft is close to
right; Must-fix list in §4 below. Specific gaps: §5.5 is not an explicit DoD item nor was it
measured; §10's decision table omits D4-5, D4-6, D5-3, D5-4 (the request's §6 has all ten); the
alias production rule is not distinguished from the audit's loose variant; "URL continuation" lacks
an operational definition; 647/1,293 residual failures (00114, 00818, 01767, 03086, 03801) are not
in scope; `SlotReportV2` should also carry `alias_adjudicated` provenance and the policy echo.
*Next:* apply §4 items 1–7 before user approval is requested.

**Q13 (1,940 still human primary despite generic-v2 ineligibility? separate review from
eligibility?). Verdict: agree — keep them separate.** Human review grades summary quality
(fabrication, unit/qualifier errors, omission, utility); selection eligibility is a gate under a
frozen verifier policy. 1,940 remains human-50 exploratory primary; generic v2 only makes it
gate-ineligible. Symmetrically, 2,586's eligibility does not make it the quality primary. Never
label 1,940 "eligible" under generic v2; never call 2,586 quality-primary on eligibility grounds.
*Next:* dual-label reporting per Q5.

**Q14 (request factual errors / exaggerations / omissions). Verdict: agree with two material
omissions and no factual errors found.** All strict-state numbers, the paired CIs (reproduced),
the gate arithmetic (160/161 = 0.9938 passes; 159/161 = 0.9876 fails), the corpus stats, the flip
list, the 3-AI summary and errata, and the v1 URL false-accept example were verified against
artifacts — see §0. Omissions: (1) all v2 numbers exclude §5.5 and are therefore optimistic
upper bounds; (2) the "V2 + counter alias" variant is looser than drafted §5.4. Minor: collision
stats cover clean 1,617 only, not the 383; the sensitivity tables should carry a "pre-§5.5 audit
matcher" footnote. Unverifiable here (sandbox lacks P0 passages; not errors): 16/161 prefix
sharing, 03992 wrap context, the 5 flips' ground truth. *Next:* add the footnotes to the
request/sensitivity tables; track the unverifiable items into the local adjudication task.

---

## 4. Must-fix (max 7, priority order)

1. **Implement §5.5 and re-audit before anything is final.** Scheme/host-only lowercase, path/query
   case/comma/escape preserved; re-run the 383 target audit and the 5-system val re-scoring with it.
   Every current 160/161 table must be labeled "pre-§5.5 audit matcher" until re-derived.
2. **Freeze policy arms + spec hash before final re-selection.** `selection_v2.json` records
   `verifier_version`, policy, spec hash, and the per-doc v1↔v2 flip list; all arms labeled
   outcome-informed exploratory / val-reused. No product promotion language anywhere.
3. **Adjudicate all 383 flips with a pre-registered rubric.** Acceptance = human-confirmed false
   accept 0 (ambiguous = false accept); evidence spans recorded; corpus stays frozen inside D-084.
4. **Pin the alias production rule.** Narrow pre-filter + per-instance human adjudication with
   provenance; explicitly retire the audit's uniqueness-skipping variant from any production path;
   ratify on an independent labeled sample (not only 04709).
5. **Define "URL continuation" operationally for the wrap join** (both-side repair; guard against
   over-join, e.g., joined form attested on the summary side or a domain-sanity check), and add the
   verified 1,940/2,586 `02742` wrapped-vs-joined pair as a golden test; include §5.5 case/comma
   and alias-uniqueness-skip regression tests, and "summary adds qualifier → new".
6. **Extend scope/DoD:** classify the residual 647/1,293 failures (00114, 00818, 01767, 03086,
   03801); add per-rule attribution reporting; add the four missing decisions (D4-5, D4-6, D5-3,
   D5-4) to draft §10.
7. **Adopt the D4-4 reporting bundle** (nonvacuous, slot_free with target-slot breakdown,
   preservation vs ≈0.465, slot-level micro with CP95 + INCONCLUSIVE, doc/slot denominators) as
   mandatory fields in `selection_v2.json`.

## 5. Additional experiments (max 5, with cost)

1. **v2 final implementation + full re-audit** (incl. §5.5, both-side wrap, alias probe as separate
   arm, per-rule attribution): ~1–2 h CPU + 1–3 h human adjudication.
2. **Human 50** (4 arms, blind, 2 raters, ≥20 overlap): ~12–20 person-hours (protocol freeze first).
3. **Fresh P0 confirmatory set** (no P1; sized so CP95 upper at the observed ~0.4% slot-level rate
   can fall ≤1%, realistically ≥1,000–1,500 docs; 299 zero-failure docs is the best-case minimum):
   eval-only, ~2–4 h CPU + labeling.
4. **Seed-43 full-train replication** — ~4.5 h + eval; only after D-084 + human 50.
5. **Over-compression arm** (1.5-epoch stop OR LR decay, one variable only) — ~4–5 h/run; only if
   human 50 confirms compression is the binding quality issue.

## 6. Factual errors / exaggerations / omissions in the request

- **No factual errors found.** All numbers I could recompute matched exactly (strict table, corpus
  stats, flip list, sensitivity tables, 3-AI and errata claims). The 160/161-pass / 159-fail
  arithmetic is correct.
- **Material omission 1:** v2 numbers exclude §5.5 (URL case/comma) — optimistic upper bounds.
- **Material omission 2:** the counter-alias audit variant is looser than drafted §5.4.
- **Minor:** collision stats cover clean 1,617 only; sensitivity tables need a "pre-§5.5 audit
  matcher" footnote; the wrap-join regex's continuation check is weaker than the drafted
  "URL continuation" wording (over-join can create new-slot failures, the reverse risk).
- **Not errors, unverifiable in this sandbox:** 16/161 prefix sharing; 03992 wrap context; the 5
  flips' ground truth (P0 passages absent locally-by-design of this checkout).

## 7. Final recommendation

Keep the two tracks strictly separate and finish D-084 before any selection claim is made. The
strict D-083 record (`selected_step: null`, pilot300 fallback, test 163 sealed) is verified correct
and must remain untouched; the v2 audit is a genuine improvement in measurement honesty — the URL
wrap defect it targets is real and I verified it in the raw predictions — but the audit as run
excludes §5.5 and uses a looser alias probe than the draft specifies, so today's 160/161 figures
are optimistic upper bounds, not final policy results. My concrete path: implement §5.5 with tests,
freeze the policy arms and spec hash, adjudicate the 383 flips (acceptance: human-confirmed false
accept 0, ambiguous counts as false accept), then re-score all five systems and publish
`selection_v2.json` with generic / URL-only / +alias arms side by side, CP95 + INCONCLUSIVE labels,
and per-rule attribution.

On the candidates: under generic v2 the mechanical selection candidate is 2,586, but its
over-compression profile (slot-free 11 with 9 target-slot omissions, preservation 0.4188 below the
≈0.465 target-implied level) means it must not be promoted on eligibility grounds alone; 1,940
remains the human-50 exploratory primary on quality grounds and must not be alias-ed into
eligibility. Run human 50 with all four systems blind on the same 50 docs, keep G-C5
slot/doc-denominator reporting with CP95 + INCONCLUSIVE (only pilot300 is currently
G-C5-consistent), keep test 163 sealed until D-084 + audit + human 50 + a single frozen candidate,
and defer seed 43 and the compression arm until after that. Nothing here approves a gate change;
it sequences the evidence so the eventual decision is not an artifact of policy timing.