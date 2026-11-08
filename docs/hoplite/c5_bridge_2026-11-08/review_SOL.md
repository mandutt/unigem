# Independent external review — C5 EG2 → T5Gemma2 bridge

**Reviewer:** Sol 6.1 (`openai/gpt-6.1-sol`), independent review round
**Date:** 2026-11-08 UTC
**Repository:** `mandutt/unigem`; Hoplite project `proj_2e8de5ed594f47c7b851f1d7c5b52c61`
**Review basis:** `origin/main` / HEAD **`f8c33a69c3dced040a401faf552a74437a696d02`**

## 0. Scope, synchronization, and independence

I ran, in order, `git fetch origin` and `git pull --ff-only origin main`.
Both succeeded; pull reported **Already up to date**. HEAD and `origin/main`
were identical at the commit above. The existing workspace branch was
`hoplite/pharsalos-c00b40f7`; I did not switch branches. The request document's
`ee084af` header is an older reference, not this review's checkout.

I personally read **all 624 lines** of
`reports/EXTERNAL_REVIEW_C5_BRIDGE_2026-11-08.md`, in the ranges 1–210,
211–420, and 421–624, including retrieval of truncated tool output. I then
inspected the referenced reports, train/val result artifacts, and relevant
implementation. I did not consult another external review, delegate work, or
call another model. Aggregate historical protocol decisions were read as
provenance, not as independent judgments to adopt.

**Restrictions observed:** no training; no opening or evaluation of sealed
test 163; no P1 data, external APIs, model downloads, or external research;
no source-code changes. I did not open the mixed clean corpus or split file,
which could expose sealed records/IDs. Numerical checks used already-produced
train/val artifacts only. The sole intentional repository-file write in this
review is this report. Synchronization necessarily updated Git metadata.

The production verifier SHA256 independently matches the request:
`a262cee0cd25307a74f3a87995624e2999b47daed9294000f036d27ea1869d03`.
Model weights and feature-cache metadata were not present at their documented
paths in this checkout. Thus this is **artifact arithmetic and static code
review**, not a rerun of inference or an authentication of checkpoint bytes.

## 1. Executive verdict

### **STOP the current bridge track. Keep A1 native as a product-development fallback, not an approved product.**

D-107 failed its pre-registered conjunction. Its F1 and EOS improvements do
not cancel grounded 12% against a required 20%. The matched A1 fallback
substantially dominates the bridge, and no demonstrated deployment saving
compensates for the quality gap. More importantly, even passing 20% would
remain far short of the existing product safety gate.

This is an **engineering stopping decision under the current evidence and
budget**, not proof that EG2 irreversibly lost every fact or that all possible
copy-equipped bridges are impossible. The experiments do not support that
universal conclusion.

A single valid, conditional falsification opportunity exists: **source-slot
constrained decoding of the frozen best-F1 bridge**, with no training and
with quality, non-vacuity, coverage, and deployment-cost controls. I would
consider **NARROW only after explicit owner authorization of that one bounded
experiment**, and only if EG2 reuse has a concrete deployment value. I do not
recommend an open-ended auxiliary/copy/full-data sequence. No new gate,
experiment, or product promotion is approved by this review.

### Confirmed headline results

All of the following preserve the published meaning of `grounded`:
**no newly detected canonical slot**, not full verifier acceptance.

| System / matched 100 IDs | Gold char F1 | Grounded | EOS | Interpretation |
|---|---:|---:|---:|---|
| A1 native pilot300 | 0.6552 | 100/100 | 100/100 | Strong fallback; not complete factuality proof |
| B2 full 1,293 | 0.3128 | 15/100 | 55/100 | Old feature/init/LR configuration |
| B2 layer12 300 | 0.3464 | 21/100 | 60/100 | Better grounding than either SS arm |
| B2 layer9 300 | 0.3340 | 22/100 | 55/100 | Best headline grounding, substantially vacuous |
| B2 layer12 SS | 0.3783 | 10/100 | 59/100 | Better overlap/repetition, worse no-new-slot rate |
| B2 layer12 slot-aware SS | 0.4074 | 12/100 | 69/100 | Best bridge F1; D-107 fails grounding |

The A1–best-bridge F1 gap is **0.2478 absolute**, with an **88 percentage-point**
no-new-slot gap. A1 val161 remains 0.6576; it must not replace its matched
val100 number in this comparison.

## 2. Evidence that materially changes interpretation

### 2.1 `grounded` is weaker than the request's metric definition

The request's §2.3 says grounding includes source-slot preservation and no
new slots. In contrast:

- `eval/slot_verify.py:164–188` sets `rejected = bool(missing or new)`.
- `runner/c5_b1d_generate.py:129–147` sets `grounded = not rep.new`.
- `runner/c5_a1_eval_batch.py:64–79` uses the same weaker predicate.
- `runner/c5_b2_slot_repair.py:89–119` also uses no-new-only grounding.

Thus the published 100%, 12%, and repair 100% are internally reproducible,
but they are **not percentages passing the complete production verifier**.
From the existing A1 `verifier_084a_audit.json` per-document v1 records,
matched A1 has **4/100** documents with neither missing nor new slots; 96/100
have missing source slots. From existing repair JSONL original records,
layer12 has **1/100**, ordinary SS **0/100**, and slot-aware SS **0/100**
with both counts zero. Slot-aware repair has **1/100**, not 100/100, under
that stricter predicate. These are separate diagnostics, not replacements
for the supplied headline numbers and not a proposal to change any gate.

For abstractive summarization, preserving every incidental source number may
itself be the wrong *future* adequacy requirement. That is a specification
question requiring prospective agreement. The immediate fix is to expose
both existing predicates and measure important-fact adequacy separately,
without changing production code or relabeling a failed run.

### 2.2 The slot-aware grounding “recovery” is especially weak

I aggregated the existing val100 JSONL rows, with identical IDs/order across
the four feature/SS arms:

| System | No-new documents | Zero detected summary slots | No-new, nonzero-slot documents | No-new rate among nonzero-slot documents | Mean source-slot preservation |
|---|---:|---:|---:|---:|---:|
| Layer12 | 21 | 4 | 17 | 17/96 = 17.7% | 0.2512 |
| Layer9 | 22 | 11 | 11 | 11/89 = 12.4% | 0.1418 |
| SS | 10 | 1 | 9 | 9/99 = 9.1% | 0.3618 |
| Slot-aware SS | 12 | 3 | 9 | 9/97 = 9.3% | 0.3656 |
| A1 native matched | 100 | 5 | 95 | 95/95 = 100% | 0.4446 |

The extra two no-new documents in slot-aware SS are matched by an extra two
slot-free outputs; **the aggregate non-vacuous success count stays nine**.
This does not mean all individual improvements were vacuous: seven documents
gained no-new status and five lost it relative to ordinary SS. It does mean
that “10% → 12% grounding recovery” is not robust evidence of a restored
copy mechanism. Layer9's 22% also should not be called a meaningful grounding
win over layer12's 21% without this qualification.

The ordinary SS deterioration is not *only* a vacuity artifact. Detected
new/summary-slot totals change from **322/602** to **594/971**; slot-aware
reduces them to **480/858**. Relative to layer12, SS gains six no-new documents
but loses seventeen. The change exists in raw outputs under a fixed metric;
its causal attribution and semantic severity remain separate questions.

### 2.3 Fairness checks and known overlap

I independently joined A1 to the bridge IDs. Gold targets match, and the
bridge's stored teacher strings equal A1's predictions for those IDs.
A1 matched F1 is **0.6551818585**. Its own artifact's first 100 rows give
**0.6506219019**, confirming the request's warning about order/subset choice.
B2 full joined to those IDs gives **0.3127746150**, 15 grounded, 55 EOS.

The existing human50 manifest flags **16/161** validation IDs as sharing an
article-prefix group with train, using the first three hyphen-separated ID
components. **Nine** occur in bridge val100. This is a known overlap flag,
not proof of exact duplicate text or proof that all 16 overlap pilot300's
actual training subset. Removing those nine from existing matched results:

| System | n | F1 | Grounded | EOS |
|---|---:|---:|---:|---:|
| A1 | 91 | 0.653549 | 91/91 | 91/91 |
| Layer12 | 91 | 0.344490 | 20/91 | 53/91 |
| Slot-aware SS | 91 | 0.410389 | 12/91 | 65/91 |

The STOP comparison survives this limited sensitivity check. It does not
establish that all possible article-level leakage has been removed.

## 3. Q1–Q12

### Q1. Bridge premise — **verdict: agree**

**Answer:** STOP is justified for this track. No present result justifies
CONTINUE, and A1's dominance is much larger than the small within-bridge
feature differences. “Stop this investment” is supported; “no bridge could
possibly work” is not.

**Evidence:** Request §§1.2–1.3, 5.3; the matched arithmetic above; D-107
metric artifact; repair oracle F1 0.3203. No end-to-end EG2-reuse saving is
reported alongside the quality deficit.

**Next steps:**
1. Preserve D-107 as failed and freeze bridge checkpoints/results as exploratory.
2. Spend the next default effort on A1's factuality/adequacy validation, not bridge training.
3. Only if deployment value is established, seek authorization for Experiment 2 below; its fixed frozen-checkpoint design is the single proposed STOP falsifier.

### Q2. Termination decision — **verdict: agree**

**Answer:** Given the stated pre-registration, stopping is not post-hoc
rationalization: F1 ≥0.36 passes, grounded ≥20% fails at 12%, EOS ≥58% passes.
A conjunction fails when one requirement fails. I accept the user's stated
pre-registration; this snapshot alone does not independently timestamp it.

The DoD was reasonable as a **cheap research screening gate**, though far
too weak as a product gate. It was not an obligation to exhaust every future
architecture. Its failure cannot prove a universal architectural limit.

**Evidence:** Request lines 62–71 and 447–452; D-107 and
`reports/C5_B2_LAYER12_SS_SLOT_2026-11-08.md` §2/§6.

**Next steps:**
1. Retain the exact old thresholds, metric definitions, and failed outcome.
2. Attach an immutable pre-run protocol reference/time and code/config hashes to future runs.
3. Treat any exceptional new probe as a separately authorized research contract, not a revised D-107 or an approved gate change.

### Q3. Scheduled sampling interpretation — **verdict: conditional**

**Answer:** The measured output shift is real; the proposed mechanism is
plausible but not causally identified. The two-point slot-aware recovery is
partly a measurement/design effect, not established mechanistic recovery.

`ce_scheduled` (`runner/c5_b1d_b2.py:125–174`) first obtains argmax predictions
under the **gold prefix**, substitutes selected shifted decoder inputs in
one parallel pass, then keeps gold labels. It is noisy-prefix CE, not a
recursive student rollout and not teacher-distribution KD on student prefixes.
Inconsistent prefixes can teach recovery toward the gold continuation while
weakening exact source-dependent continuations. Adjacent context remains
unprotected, so (a) and (b) are plausible. Nothing establishes (c), an inherent
F1/grounding trade-off. Both improve together in A1. For (d), vacuity affects
the small recovery, but fixed-metric raw counts show that it cannot explain
away the broader ordinary-SS decline.

There is a key missing control: both SS arms receive **another epoch at
1e-4 from layer12**, but no same-init, same-order, same-step/LR **p=0
continuation** is reported. Extra training, LR change, and corruption are
confounded. SS-versus-slot-aware is more closely matched, but has only one
seed and small/noisy grounding differences.

Mask caveats are concrete. Lines 78–87 create a length-L mask for content
IDs and mark its last content token as `# EOS`; actual EOS is appended to the
mask at line 139. The shifted prefix excludes gold EOS anyway. Predicted EOS
can still be inserted at unprotected positions. This does **not** demonstrate
an off-by-one error in protection of all slot spans; it demonstrates an
inaccurate EOS-protection description and extra last-content protection.
Also, extractor offsets refer to NFKC text while tokenizer offsets are used
on raw text: a normalization-dependent alignment risk, not a proven cause
on this corpus. Protected gold inputs do not constrain future generated
numbers, and the extractor has no general Korean person/organization NER.

**Next steps:**
1. Use the source-aware audit in Experiment 1 to distinguish genuine new facts, extractor errors, omission, and slot-free passes.
2. Correct the mechanism description and audit shifted-mask/EOS/normalization invariants before making any further causal claim; no code changes are made here.
3. If training is ever separately reopened, require the missing p=0 continuation as a causal control inside that approved design; it is not an additional training recommendation for this review.

### Q4. Layer9 paradox — **verdict: conditional**

**Answer:** Primarily a limit of the proxy, with overfit as a plausible
contributor. Neither feature noise nor overfit is established as the cause.
I would not fund layer9 full 1,293 next.

**Evidence:** Teacher-target CE/token accuracy improve from 2.1190/56.11% to
1.8904/59.58%, but free-running gold F1 decreases by only 0.0124. Token
accuracy and bag-character F1 are different metrics under different prefix
and target conditions; their disagreement is not a mathematical paradox.
Layer9 has a wider final train/val CE gap (about 0.979 versus 0.897), but also
better validation CE. That is suggestive, not a diagnosis. Its F1 wins/losses
against layer12 are 51/49; no seed uncertainty or paired interval accompanies
the claimed layer ordering. Its 22% headline grounding masks eleven
slot-free outputs and preservation 0.1418.

**Next steps:**
1. Describe layer9 as best on the measured alignment/fidelity proxy, not best summary features generally.
2. Publish paired output uncertainty and non-vacuous/slot-type diagnostics from existing artifacts; do not select on hidden cosine alone.
3. Keep layer9 full-data work deferred unless a separately approved direct grounding intervention first merits reopening.

### Q5. Data scale — **verdict: conditional**

**Answer:** Three hundred documents are sufficient to reject these observed
candidates and stop spending; insufficient to prove that scaling the best
architecture cannot work. Full layer12/SS has some scientific information
value, but low decision value before solving grounding.

**Evidence:** Old B2 full uses a different initialization/feature configuration
and LR 2e-4, while layer12 300 uses hidden-pretrained 512→1536 features and
LR 3e-4. Their similar outcomes are not a controlled learning curve. The
older gold300/full comparison in D-097 also mixes val100 and val161; on
matched IDs full is 0.3128/15%, not 0.3349/18.01%. Equal epochs additionally
mean unequal optimizer updates. Request §2.4 correctly warns against mixing
subsets, but older conclusions still do so.

**Next steps:**
1. Restrict the conclusion to current checkpoints/configurations and the present business decision.
2. Label 300-versus-1,293 comparisons as confounded, not evidence of established scaling saturation.
3. Defer full layer12/SS rather than spend several more CPU hours on an undirected scale-up.

### Q6. Slot repair — **verdict: conditional**

**Answer:** The result demonstrates the limits of **sentence deletion from
these outputs**, with substantial useful content discarded. It supports a
generation grounding bottleneck; it does not prove repair in general is bad,
nor that 0.3203 bounds replacement, rewriting, constrained generation, or
another model.

**Evidence:** `slot_repair_ss_slot_val100.json` reports F1 0.4074→0.3159
(drop) /0.3203 (oracle), preservation 0.3656→0.1621, and missing-slot total
829→1,063. The algorithm selects new-slot-free generated sentences, falls
back to the source's first sentence if empty, uses the gold target to choose
an oracle subset, and uses a greedy search above twelve eligible sentences
(`runner/c5_b2_slot_repair.py:37–105`). Thus “oracle ceiling” is restricted to
that candidate/search/fallback family and is not always an exact global
subset optimum. The oracle is not deployable. Repair's reported 100% is
no-new-only, not all-facts-preserved.

Source-supported replacement/rewrite could exceed 0.3203, but nearest-looking
numbers can attach the wrong value to the wrong event. Source membership
alone does not establish relations, units, polarity, or attribution.

**Next steps:**
1. Rename the claim to “best observed target-aware sentence-subset repair result.”
2. Report fallback fraction, missing facts, non-vacuity, and semantic relation errors with repair F1.
3. Do not authorize a separate rewrite branch now; the one optional constrained-decoding probe tests a more direct intervention without gold-guided selection.

### Q7. Slot auxiliary versus copy — **verdict: conditional**

**Answer:** Conditional on reopening, rank **constrained decoding →
copy/pointer → slot auxiliary → B2 full 1,293**. This is an information-per-cost
ranking for the present stopping decision, not a claim that constrained
output has the highest ultimate architectural ceiling.

| Rank | Option | Why | DoD / stop condition before it could justify further investment |
|---|---|---|---|
| 1 | Source-slot constrained decoding | Only direct source restriction that can probe existing weights without training; also an optimistic check of whether usable language remains after grounding restrictions | Experiment 2's joint quality/safety/coverage/efficiency contract; stop on any miss or budget exhaustion |
| 2 | Copy/pointer | Most direct learned route for exact source tokens; must learn the correct fact/relationship, not merely emit an allowed number | Deferred, not an approved second bridge experiment. Reopening would need source-aligned copy behavior and the same joint quality/safety standard, not only pointer accuracy; stop if copying increases wrong attribution or just source verbosity |
| 3 | Slot auxiliary | Low implementation cost but can train an unused head or source detection rather than decoder faithfulness | Deferred. Require measured improvements in generated, non-vacuous grounding versus a matched CE control plus no adequacy loss; an auxiliary-head score alone never passes |
| 4 | B2 full 1,293 | More data does not directly address the observed slot-generation failure; old full result is not the relevant controlled scaling arm | Deferred. Require prospective matched feature/init/step accounting and joint generation improvement; stop if only CE/cosine improves or any safety/quality requirement fails |

The last three rows are **eligibility criteria, not three additional proposed
experiments or an authorized sequence**. Under STOP their present budget is
zero. Slot-only copy is compatible with abstractive surrounding prose; copying
the entire source is not a successful solution.

**Subjective prior:** approximately **10%** that one modest copy/pointer
intervention, using the existing P0 training resources, would reach a
product-near result of F1 ≥0.60 and no-new grounding ≥99% without damaging
adequacy. This is an elicited judgment, not an empirical probability; my
uncertainty is broad (roughly 2–25%). The chance of merely exceeding the
old research threshold of 20% is appreciably higher, but that is the wrong
success event for replacing A1. There is no repository evidence supporting
a calibrated success probability.

**Next steps:**
1. Establish an explicit resource-saving objective for retaining EG2 reuse.
2. If authorized, run only the first-ranked falsifier with frozen weights and a single predeclared decoding rule.
3. Keep the other options deferred rather than treating this ranking as a new roadmap approval.

### Q8. Evaluation metrics — **verdict: conditional**

**Answer:** A1's 100% is a real result under the no-new-detected-slot
criterion, not evidence that it copied its own teacher labels at evaluation.
The matched gold strings are the evaluation target, and teacher-relative F1
is separate. However, a source-extractive output can earn that safety score
while missing key facts or making unsupported relational claims. The
teacher-bias audit reports matched val copy4 about 84.66% versus gold 63.60%,
consistent with extractive bias, not proof of data leakage or full adequacy.

Bridge 12% is not “too harsh” merely because the extractor is conservative:
A1 passes the same predicate and slot-aware SS has 480 new canonical slots
across 100 outputs. Specific detector false positives require source-aware
audit, not a discounted denominator or a gate adjustment. The broader
verifier is conservative about omission, while the reported grounding field
ignores omission entirely.

**Evidence:** Evaluation code cited in §2.1; `teacher_bias_audit.json`;
`runner/c5_a2null_eval.py:69–77` computes whitespace-stripped **bag-of-character
multiset F1**, which ignores word order, roles, and factual relationships.
The extractor covers URLs, paths, dates, times, versions, identifiers, and
numbers; not arbitrary names or natural-language factual claims.

**Next steps:**
1. Present no-new-slot rate, full-verifier rejection, important-fact coverage, non-vacuity, and human adequacy as distinct measures.
2. Apply hard safety requirements first, then maximize quality among eligible candidates; never average F1 and grounded to let one compensate for the other.
3. Audit false passes as well as false rejections, including source-present values with wrong entity/date/event associations.

### Q9. A1 native product path — **verdict: conditional**

**Answer:** Freeze pilot300 as the **fallback/reference candidate**, not a
released or approved product. The full 1,940 and 2,586 checkpoints have already
been evaluated. Repeating identical metrics has little information value;
reviewing their specific errors can inform diagnosis, not retroactive selection.

**Evidence:** `reports/C5_A1_full_train_2ep_2026-11-07.md` and
`reports/provenance/C5_a1/full_2ep/selection.json` retain no eligible full
checkpoint / `selected_step: null`. Step 1,940 has F1 0.6823 but grounded
158/161 (98.14%); 2,586 has 0.6690 and 159/161 (98.76%). Neither reaches 99%.
D-086's aggregate decision is INCONCLUSIVE; human calibration was not run.
A1's mean preservation is only 0.4446 on matched val100 despite no new slots.

**Next steps:**
1. Pin pilot300's actual bytes, tokenizer, prefix, generation limits, and verifier hash before treating it as a reproducible fallback.
2. Prioritize the human/source adequacy audit in Experiment 1; preserve NO_APPROVED_CANDIDATE until the applicable approval requirements are met.
3. Use existing 1,940/2,586 failures as diagnostic cases only; do not reselect them on F1 or reinterpret 98.76% as a 99% pass.

### Q10. Fair comparison — **verdict: conditional**

**Answer:** Matching IDs fixes the main denominator error, and the resulting
A1 advantage is robust. It does not erase adaptive validation selection,
training-subset differences, resource-budget differences, article overlap,
or different checkpoint-selection procedures.

**Evidence:** Exact joins and the 91-document sensitivity check in §2.3.
The teacher train100 are length-selected, whereas bridge training is selected
by split order; teacher/gold arms were additionally filtered to 99 examples
with no new teacher slots (`runner/c5_b1d_b2.py:229–245`). Layer/width/rank,
checkpoints, SS settings, and small val20/val100 views were repeatedly
examined on the same validation resource. That makes small “best” differences
exploratory. The matched ID-list SHA256, defined over UTF-8 IDs joined by
newline with no trailing newline, is
`57adb315e23beb95cdf82a0fe333c4d510d114d830fb895f9a4e538b025f02eb`.

**Next steps:**
1. Publish explicit ID lists/hashes and always join by ID; accompany headline results with the flagged article-prefix exclusion sensitivity.
2. For any authorized causal comparison, match init, examples, targets, optimizer updates/LR, generation settings, and selection rule; separate scaling from feature/objective changes.
3. Label reused-validation estimates exploratory, report paired uncertainty, and do not use sealed test 163 to settle the selection problem.

### Q11. Research stopping and A1 validation — **verdict: agree**

**Answer:** Stop now by default. If a one-off NARROW exception is explicitly
authorized, stop on any Experiment 2 DoD miss, semantic-grounding failure,
missing efficiency case, irreproducible provenance, or budget overrun. No
serial “one more arm” extensions.

A1 needs a provenance-complete replay contract and human verification of
important content, omissions, attribution, numerical relationships, and
summary usefulness. Retain the existing D-083 automatic gates and the
unresolved human-approval status. A diagnostic human audit is not itself
permission to replace the failed/inconclusive approval protocol.

**Evidence:** D-083/D-107; the historical human decision in D-086; A1's
no-new/full-verifier distinction and prefix-sharing flags. Even 100/100
passes imply an exact two-sided 95% binomial lower bound of only **96.38%**;
161/161 implies **97.73%**, under an independent-draw assumption. Reused,
possibly clustered validation is weaker evidence still. A 99% empirical gate
pass is not proof that population reliability exceeds 99%.

**Next steps:**
1. Keep bridge spending at zero unless the exception is explicitly approved; cap that exception at four CPU-hours and four engineering-hours.
2. Complete A1 source-based human validation and article-group sensitivity, plus end-to-end CPU latency/RSS and clean checkpoint-load verification when artifacts are available.
3. Report empirical gate status, statistical uncertainty, and approval status separately; test 163 remains sealed throughout these recommendations.

### Q12. Must-fix priorities — **verdict: agree**

Only these **three priorities** should precede a new scientific or product claim:

1. **Fix the evaluation contract and evidence presentation.** Distinguish
   no-new-slot grounding from `not rejected`; show non-vacuous rates,
   important-fact adequacy, and semantic false passes/rejections. A1's 100%
   and repair's 100% must never be described as all-source-slot preservation.
2. **Fix causal controls and generalization accounting.** SS lacks a matched
   extra-epoch p=0 control; scaling mixes configuration/subsets/updates;
   repeated val reuse and article-prefix overlap are not adequately represented
   in the executive conclusions. Freeze IDs, control selection, and report
   uncertainty/sensitivity before interpreting small deltas.
3. **Fix run provenance and implementation invariants.** Record commit,
   checkpoint/cache/tokenizer hashes, actual IDs, seed/state, effective
   configuration, and resume history; resolve the hidden-teacher identity and
   mask/EOS/dropout issues below. Otherwise “reproduction” can silently be a
   different experiment.

**Evidence:** §2; trainer/code citations in Q3/Q10; missing metadata fields
and the concrete implementation findings in §4 below.

**Next steps:**
1. Publish a corrected results dictionary and joined per-document appendix without editing old gates or result values.
2. Make future pre-run contracts auditable and prospective, preserving all failed historical verdicts.
3. Do not launch further bridge work until the three categories have an accountable resolution plan.

## 4. Issue register: severity, evidence, and remedy

These are recommendations only; none of these code/document fixes was
performed during this consultation.

| Severity | Defect and evidence | Recommended remedy |
|---|---|---|
| **High** | Metric-definition mismatch: request §2.3 says preservation + no-new; both generation runners report only no-new. Full verifier rejects missing slots. | Document both predicates; keep old numbers/gates intact; validate important-fact adequacy separately. |
| **High** | Vacuity changes the apparent ranking: layer9 11 slot-free outputs; SS→slot-aware non-vacuous no-new count remains 9. | Report counts and conditional rates, not only aggregate grounded; include omission and important-slot coverage. |
| **High** | Missing p=0 continuation and confounded scaling/selection; one seed, reused validation and article-prefix overlap. | Prospectively match comparisons, document all selection exposures, and preserve article-group sensitivity. Do not claim a causal SS mechanism from these runs. |
| **High** | “Teacher” identity is ambiguous. `runner/c5_b1d_cache.py:50–55` loads the **base** T5 encoder without A1 LoRA; summary targets are A1 pilot300 outputs. The request describes A1 as teacher without clearly separating these objects. Cache binaries/metadata are unavailable here. | Name hidden-space teacher, output teacher, and initialization separately; attach actual cache/checkpoint hashes. Do not assume the hidden target is the adapted A1 encoder or that its control has A1's quality. |
| **Medium** | Trainer validation can retain LoRA dropout. Base model is set `.eval()` before newly constructed LoRA modules are attached; those new Dropout modules default to training mode. `eval_ce` at lines 315–324 never toggles them. `LoRALinear` has dropout 0.05. | Explicitly manage training/evaluation modes and restore them. Distinguish stochastic training-run gold CE from standalone fidelity evaluation (which attaches dropout 0.0). This does not invalidate deterministic generation scores. |
| **Medium** | EOS mask description and normalized-offset risk: content mask marks final content as EOS; gold EOS is not a candidate shifted-prefix input; inserted predicted EOS is unrestricted. Extractor offsets are NFKC-relative, token offsets applied to raw text. | Assert label/shift/mask alignment, special-token policy, and normalization mapping. Audit actual corpus incidence before attributing results to this hazard. |
| **Medium** | Reproduction/resume hazards. Checkpoints save weights/step metadata but no optimizer or RNG state; generation appends/resumes using ID only and does not verify existing output provenance (`c5_b1d_generate.py:99–109`). | Hash run manifests and reject mismatched output reuse; save optimizer/RNG state for exact continuation. This is a reproducibility risk, not evidence that the reviewed runs actually resumed incorrectly. |
| **Medium** | Missing run fields: ordinary SS metrics omit `ss_prob`/`ss_slot_aware`; layer12 metrics omit feature/dimension fields; current reports lack commit/ID/checkpoint/tokenizer hashes. | Preserve immutable run-config manifests rather than infer historical settings from today's default flags. |
| **Medium** | Repair “ceiling,” layer9 information/noise, rank-not-bottleneck, and teacher-KD-no-gain statements overgeneralize limited proxy/val20 evidence. | Scope each claim to its tested objective, configuration, checkpoint, and sample. Keep universal causal claims unresolved. |
| **Low** | Historical maxima/units/version labels conflict: D-107 and slot-aware report still say best grounded 21%; header uses old commit; generation versus repair `gen_len` uses different units. | Correct narrative maxima to layer9 22% with vacuity caveat, state review commit, and label tokens versus characters. No result/gate rewriting. |

A particular caution about hypotheses H1–H6: the information-processing
inequality does not prove this encoder discarded the needed facts; failed
finite-budget probes cannot establish that. A concatenated representation
contains the component representation, so worse finite-MLP alignment is not
proof that concatenation has intrinsically less information. Decoder rank
r16 doing worse in one setup does not exclude optimization/data limitations.
D-096 itself calls teacher-versus-gold **inconclusive and early-stop-dependent**;
“No demonstrated benefit here” is defensible, “KD cannot help” is not.

## 5. At most two additional experiments

**No experiment below was run. No training or additional model calls are
part of either proposed experiment.** Experiment 1 is the default next step;
Experiment 2 is an optional exception to STOP, not an approved continuation.
All time estimates are planning estimates for the request's CPU-only Ryzen
machine, not timings measured in this workspace.

### Experiment 1 — Source-aware metric and A1 adequacy audit

**Question:** Do no-new-slot pass/fail decisions correspond to useful,
factually faithful abstractive summaries, and is A1 a credible next product
candidate rather than merely the best automatic-score fallback?

**Design:** Freeze the existing matched val100 outputs and provenance. Audit
all computed no-new/non-vacuous/missing counts. Before rating, freeze a seeded
random sample of 50 of these validation documents and blind A1/layer12/SS/
slot-aware identities (200 summary ratings). Use unsealed P0 validation source
text only. Label supported/unsupported values, wrong relationships or
attribution, critical omission, useful coverage, repetition, and adequacy;
adjudicate detector disagreements using explicit source spans. Report the
nine-prefix-sharing exclusion sensitivity. This is a diagnostic audit, not
an unapproved replacement for D-086 or product-selection gates.

**DoD:** Complete auditable labels for every sampled output, deterministic
reconciliation of artifact metric counts, separate false-positive/false-pass
and vacuity accounting, and an A1 adequacy/error report with uncertainty.
All serious unsupported/omitted facts must be enumerated; do not define
success as simply finding A1 better. A1 cannot be promoted by this audit
alone while the applicable approval requirements remain unresolved.

**Expected cost:** approximately **0.1–0.25 CPU-hours** for artifact
reconciliation and **3–6 human-hours**, assuming locally available P0 source
exports. Rater scheduling/reliability requirements can add calendar time;
those are not hidden within this estimate.

**Stop conditions:** Missing/unverifiable source provenance, inconsistent
sample ownership, or reliability inadequate for the claimed conclusion →
INCONCLUSIVE. Critical A1 errors block promotion. Do not compensate by
loosening metrics, substituting another model's judgment, or accessing test.

### Experiment 2 — Optional single STOP falsifier: constrained frozen bridge

**Admission condition:** The owner explicitly authorizes a NARROW exception
and states a material EG2-reuse latency/memory objective. If not, do not run.
Weights, tokenizer, and source-only slot extraction must be available and
hash-verifiable; the current checkout alone is insufficient.

**Design:** Use only the frozen D-107 best-F1 adapter/LoRA and its exact
matched val100 IDs. Predeclare one source-slot-aware, multi-token constraint
rule that restricts completed numeric/date/identifier/etc. spans to supported
source canonical values while allowing abstractive non-slot prose. Evaluate
with the unchanged production verifier, reporting both no-new and missing/
rejected fields. Validate token-boundary, multi-token, special-token, and
normalization handling on synthetic P0 examples before the fixed run.
Keep max_new=448 and generation/search settings fixed except the declared
constraint. Do not tune rules on validation outputs, use gold for constraints,
or substitute A1/extractive source fallback into the bridge arm. Empty,
unfinishable, or abstained outputs remain in the denominator, with failed
coverage and zero quality where appropriate.

Compare with the frozen unconstrained D-107 and A1 outputs. Measure actual
end-to-end CPU latency/RSS, not just cached-decoder generation. Declare the
resident-EG2 assumption and include the relevant feature extraction, adapter,
decoder, and constraint costs. Report warm-cache and uncached conditions
separately so a cached bridge is not compared with an uncached A1.

**Proposed prospective research DoD — not approved and not a revised product
gate:** All of the following must hold on the fixed matched sample:

- Gold char F1 **≥0.60** (within approximately 0.055 of A1, rather than merely
  exceeding 0.36); no-new-slot grounding **≥99%**, new-slot micro **≤1%**,
  EOS **≥95%**, and rep4 **≤0.06**. The latter safety/behavior requirements
  retain the existing A1 automatic-gate values.
- **100% scored, nonempty coverage** (no omitted/abstained documents), mean source-slot preservation
  **≥0.40**, and zero-slot output count no greater than A1's matched **5/100**.
  Report non-vacuous grounding and full-verifier rejection separately.
- Apply Experiment 1's blinded sample and source-checking rubric to the
  constrained outputs as well: no new critical unsupported-relationship
  failure attributable to the constraint. Exact-match slots alone are insufficient.
- At least **20% lower** end-to-end latency *or* peak RSS under the declared
  deployment assumption, with the other resource no more than **10% worse**
  than A1. The owner must accept this proposed efficiency target beforehand.
- Report paired quality differences and sampling uncertainty. Passing these
  point-estimate research screens supports only reopening discussion, not
  a claim of population 99% reliability or product approval.

The extra F1/preservation/efficiency values are my explicit **decision-value
proposal**, not historical thresholds. They deliberately demand evidence
strong enough to challenge STOP against an already-available A1, rather than
rerunning the much weaker historical research screen.

**Expected cost:** **2–4 engineering-hours** to implement/audit a bounded
constraint if existing tokenizer integration permits it; **1–3 CPU-hours**
for fixed inference and cost comparison. Existing unconstrained val100
inference took about 20–23 minutes; constraints may multiply this cost.
Allow an additional **1–2 human-hours** to rate the constrained outputs on
the same frozen sample. That extrapolation is uncertain and excludes absent
model/cache provisioning.

**Hard maximum:** **four engineering-hours and four CPU-hours total for this
bridge exception**, including synthetic checks, failures, reruns, and cost
measurement, plus at most **two incremental human-hours** for source rating. If faithful constraints cannot be implemented within that cap,
that is a no-go under the present economics, not evidence for another budget.

**Stop conditions:** Any joint DoD miss, rule tuning after seeing val results,
wrong source-value association, quality achieved through vacuity/verbosity/
source fallback, absent deployment savings, unavailable provenance, or cap
exhaustion → retain STOP. No automatic transition to pointer training,
auxiliary training, layer9 full, or layer12 full. Passing would justify a
new decision discussion only; it does not amend D-107 or authorize launch.

## 6. Numerical/documentation corrections and unresolved limits

1. **Keep all verified headlines:** bridge 0.4074/12%/69%; layer9 best headline
   grounded 22% at F1 0.3340; A1 matched 0.6552 and full-val 0.6576; observed
   repair 0.3203; D-107 PASS/FAIL/PASS. No contrary raw evidence was found.
2. **Stale 21% maximum:** D-107's narrative and the slot-aware result report
   §7 say bridge best grounded is 21%. It is 22% for layer9, with the vacuity
   qualification in §2.2. The review request itself corrects this maximum.
3. **Grounding semantics:** no-new-only and all-source-slot retention are not
   interchangeable. Clean “100% grounding” likewise should not be paraphrased
   as retention of every source fact without checking which predicate was used.
4. **Subset comparisons:** old layer12/gold300 narratives compare their val100
   to full's val161; the matched full comparator is 0.3128/15%/55%. Current
   request matched table is correct. A1 artifact row order is not the bridge
   subset order; join by IDs rather than taking an arbitrary first 100.
5. **Repair ceiling:** 0.3203 is the observed target-aware result of this
   sentence-subset/fallback routine, not an upper bound for all grounded
   summaries. Its oracle and deployable repair must remain separate.
6. **Units:** generation `gen_len` counts generated tensor tokens, while repair
   `gen_len` uses Python character length. The very same original slot-aware
   outputs have means **286.41 tokens** and **396.73 characters**. Neither is
   a contradiction, but unlabeled length comparisons are invalid. Batched A1
   tensor lengths can additionally include padding.
7. **Metric/proxy labels:** “token acc” in standalone fidelity is a mean of
   per-document token accuracies, not necessarily corpus-token-micro accuracy.
   Gold training-run CE and teacher-target fidelity CE are different targets;
   the layer12 report's fidelity table should not silently mix full gold CE
   2.6341 with teacher-target CE. Hidden cosine, CE, bag-char F1, and human
   factuality are not commensurable scores.
8. **Teacher provenance:** adapted A1 summary teacher and base-T5 hidden-cache
   teacher are not demonstrated to be the same system. Actual cache metadata
   is absent here. Likewise, better alignment does not establish lost versus
   recoverable source information.
9. **Prior claims remain limited:** one r16/concat/teacher-target comparison
   rules out those tested configurations as immediate priorities, not the
   architectural concepts. Single-seed, reused-val results do not identify a
   structural impossibility or a calibrated copy-success probability.
10. **A1 status:** fallback is not product approval; full selection remains
    null. Human evidence remains unresolved. No threshold rounding, gate
    relaxation, or test unsealing is recommended.

## 7. Evidence index and verification performed

Primary request: `reports/EXTERNAL_REVIEW_C5_BRIDGE_2026-11-08.md` (all lines).

Result reports inspected: `reports/C5_B2_LAYER12_2026-11-08.md`,
`reports/C5_B2_LAYER9_2026-11-08.md`,
`reports/C5_B2_LAYER12_SS_2026-11-08.md`,
`reports/C5_B2_LAYER12_SS_SLOT_2026-11-08.md`,
`reports/C5_EG2_LAYER_SWEEP_2026-11-08.md`,
`reports/C5_CONCAT_PRETEST_2026-11-08.md`,
`reports/C5_A1_full_train_2ep_2026-11-07.md`, and
`reports/C5_A1_bare_val161_2026-11-06.md`. Additional interface/protocol context:
`reports/C5_B1D_PROBE_2026-11-07.md`, relevant C5 entries in
`docs/decisions.md`, the SS status sections in
`reports/C5_STATUS_2026-11-06.md`, and train-prefix rules in
`docs/D-085_human50_single_rater_protocol_2026-11-07.md`.

Raw evidence, all existing unsealed artifacts:

- Under `reports/provenance/C5_b1d/`: the layer12/layer9/SS/slot-aware
  `*_metrics.json`, `*_fidelity_teacher.json`, `generation_val100_*.jsonl`
  and corresponding generation metrics; `b2_full_metrics.json` and
  `generation_val161_b2.jsonl`/metrics; the three relevant
  `slot_repair_*val100.jsonl` plus slot-aware repair metrics;
  `teacher_bias_audit.json`, hidden-pretest JSON, and
  `token_alignment_all.json`.
- `reports/provenance/C5_a1/pilot300_val161/predictions.jsonl`;
  `reports/provenance/C5_a1/full_2ep/selection.json`,
  `selection_summary.json`, and existing verifier audit metadata/per-document
  pilot300 v1 results. No alternative verifier was adopted or executed.
- `reports/provenance/C5_human50/manifest.json` for known article-prefix flags.

Static code inspected: `runner/c5_b1d_b2.py`, `c5_b1d_generate.py`,
`c5_b2_fidelity_eval.py`, `c5_b2_slot_repair.py`, relevant cache/pretest/bias
and A1 LoRA/evaluation code, `runner/c5_a2null_eval.py`, and the unchanged
`eval/slot_verify.py`.

Read-only calculations independently checked matched F1/grounded/EOS,
unique IDs/order and target/teacher equality, slot totals, vacuity,
per-document pass transitions, known-prefix exclusion sensitivity, existing
full-verifier acceptance fields, and the verifier checksum. These checks did
not run a model, training, a new production evaluation, or sealed-test access.

**Bottom line:** retain **STOP** for the reviewed bridge family; retain
**pilot300 fallback / NO_APPROVED_CANDIDATE** for the separate native product
path. Audit the evaluation contract first. At most, authorize one explicit,
strictly capped inference-only bridge falsifier—never an implicit reopening
or a retroactive gate change.
