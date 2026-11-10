# C5 F0 — Integrated Synthesis Report

- 작성일: 2026-11-10
- 범위: F0, F0 post-mortem, F0.1a, F0.2, F0.3
- 성격: **internal synthesis, not a 3-AI reviewed report**
- 데이터 등급: P0 only; test 163/P1 미사용

# 1. Verified Facts

## 1.1 Experiment inventory

| 단계 | 목적 | units | updates | wall | artifact status |
|---|---|---:|---:|---:|---|
| F0 R | 원래 2×2 causal test | 12 | 900 | 3,898.5s | ROUTE_STOP |
| F0 post-mortem | E01 underfit 진단 | 0 (기존 artifact) | — | — | 완료 |
| F0.1a | E01 optimization rescue | 9 | 2,700 | 2,177.4s | RESCUED 400 |
| F0.2 | matched E01/E11 signal | 6 | 2,400 | 2,091.3s | INDETERMINATE |
| F0.3 | E00/E10 reference | 6 | 1,200 | 1,515.2s | REFERENCE_DECOMPOSITION |

## 1.2 F0 original

- contract label: **ROUTE_STOP**
- reason: **no_signal_uncertain**
- primary `E01_copy − E11_copy`: mean **−0.02196**, 95% CI **[-0.37411, +0.33494]**, positive seeds **0/3**
- E01 copy: `0.0029`; E11 copy: `0.0249`; both non-signal
- E10 full: `0.0324`; descriptive only

## 1.3 F0 post-mortem

- E01 final train loss ≈ **19.7**; E10/E11 ≈ **6.2–7.3**
- E01 loss reduction ratio ≈ **0.736**; E11 ≈ **0.236**
- E01 copy doc-mean SD **0.7228**; E11 **0.0555**
- copy coverage E01 = E11 = **0.8267**
- finding: **E01 underfit / optimization confound**

## 1.4 F0.1a

| condition | updates | LoRA LR | median fit_ratio | seed passes | condition_fit |
|---|---:|---:|---:|---:|---|
| C1 | 100 | 1e-4 | 0.7355 | 0/3 | false |
| C2 | 400 | 1e-4 | 0.3814 | 0/3 | false |
| C4 | 400 | 3e-4 | 0.2524 | 3/3 | true |

- C4 final loss: 6.74–6.85
- diagnosis: **E01_UNDERFIT_RESCUED_400_RANGE**

## 1.5 F0.2

Fit: **6/6 pass**. E01 ratios 0.2524/0.2510/0.2553; E11 ratios 0.1341/0.1704/0.1169.

| cell | endpoint | mean | 95% CI | pos seeds | signal |
|---|---|---:|---|---:|---|
| E01 | copy | −0.0146 | [−0.0605, +0.0241] | 0/3 | false |
| E01 | full | −0.0155 | [−0.0486, +0.0190] | 0/3 | false |
| E11 | copy | +0.1152 | [+0.0598, +0.1718] | 3/3 | true |
| E11 | full | +0.0893 | [+0.0425, +0.1374] | 3/3 | true |

- `D = E01_copy − E11_copy`: **−0.12980**, CI **[-0.21860, -0.05718]**, positive seeds **0/3**
- benefit direction: **true**
- `ALL_FAIL`: **false**
- frozen label: **INDETERMINATE**

## 1.6 F0.3

E10 fit: **3/3 pass**.

| cell | endpoint | mean | 95% CI | pos seeds | signal |
|---|---|---:|---|---:|---|
| E00 | copy | +0.1130 | [−0.8010, +1.0588] | 3 | false |
| E00 | full | +0.1380 | [−0.8217, +1.1276] | 3 | false |
| E10 | copy | +0.1382 | [+0.0716, +0.2084] | 3 | true |
| E10 | full | +0.1163 | [+0.0626, +0.1752] | 3 | true |

- `E10 − E00` copy: **+0.0252**, CI **[-0.9315, +0.9448]**
- `E11 − E10` copy: **−0.0230**, CI **[-0.0839, +0.0309]**
- E00 is a 0-update baseline with very wide variance; E10−E00 is not a clean causal contrast.

# 2. Inferred Analysis

## 2.1 What is established

1. The original F0 `ROUTE_STOP` is **mechanically valid under its frozen rules**, but it is **not a clean test of adapter effect**: E01 was underfit.
2. E01 can be made to fit with 400 updates + LoRA LR 3e-4; this is an optimization rescue, not a signal result.
3. Under matched optimization, **E11 (adapter+LoRA) shows positive copy/full donor-specific signal**, while **E01 (LoRA-only) does not**.
4. **E10 (adapter-only) also shows positive copy/full signal** in the reference run.
5. **E11−E10 is small and CI includes zero**: no clear incremental LoRA benefit over adapter-only.
6. **E10−E00 is uninformative** because E00 is a 0-update noisy baseline; it cannot isolate adapter-only effect against a matched no-adapter control.

## 2.2 What is not established

- Confirmatory `PASS_POSITIVE` for adapter effect. F0.2 primary direction was E01−E11 and the observed direction was opposite; the frozen label is INDETERMINATE.
- Population generalization beyond the 15 length-eligible docs and fixed donor graph.
- A clean causal estimate of adapter-alone effect vs a matched no-adapter control.
- That LoRA adds incremental content-use signal over adapter-only.
- That E00 is a meaningful zero-signal baseline; its CI is very wide.
- Any H3, B0-B, or EG2 track-level STOP/keep decision.
- Independent replication: F0.2/F0.3 reuse the same cohort and overlapping seeds; they are not external validation.

## 2.3 Best current interpretation

The evidence is most consistent with:

> **Adapter-containing cells (E10/E11) produce a donor-specific copy/full signal; LoRA-only E01 does not under matched optimization. The original F0 negative was an optimization artifact. However, the adapter-only effect is not cleanly isolated because E00 is a noisy 0-update baseline, and no confirmatory directional test has been run.**

This is **directional evidence**, not a PASS.

# 3. Recommendations

## Blocker

- Do **not** cite F0 `ROUTE_STOP` as evidence that “adapter is useless” or “EG2 has no content use.”
- Do **not** relabel F0/F0.2 post hoc.
- Do **not** open H3 or B0-B from these results.

## Major

1. If a confirmatory adapter claim is required: new prereg with **fresh seeds** and a **directional E11−E01** endpoint; same data alone is not independent confirmation.
2. If product progress is the priority: close F0 as **directional/inconclusive** and move to **F5 abstract summary**.
3. If E10 adapter-only is to be isolated: design a matched no-adapter control that is not a 0-update noisy baseline; E00 alone cannot do this.

## Minor / Future

- Keep F0.2/F0.3 labels descriptive; do not merge them into F0.
- Record that F0.2/F0.3 omitted M/phase7/generation; they are signal-only.
- If external publication: 3-AI review and independent replication are required.

# 4. Final Judgement

- **Release status: internal research only**
- **Release ready: NO**
- **Confirmed negative/positive claim: none**
- **Scientific status: F0 original = INCONCLUSIVE_UNDERFIT; F0.2 = directional E11 signal, label INDETERMINATE; F0.3 = reference decomposition only**
- **Confidence: moderate for the optimization diagnosis; low for any adapter causal claim**

## Forced choice

**B. Close F0 as directional/inconclusive and move to F5** — recommended.

- A. Run F0.4 fresh-seed directional confirmation first.
- **B. Close F0, preserve directional evidence, proceed to F5.**
- C. Expand E00/E10 reference further.

# 5. Artifact Index

- F0 result: `reports/C5_F0_RESULT_2026-11-10.md`
- F0 post-mortem: `reports/C5_F0_POSTMORTEM_2026-11-10.md`
- F0.1a: `reports/C5_F0_1A_RESULT_2026-11-10.md`
- F0.2: `reports/C5_F0_2_RESULT_2026-11-10.md`
- F0.3: `reports/C5_F0_3_RESULT_2026-11-10.md`
- provenance: `reports/provenance/C5_f0*/`
- commits: `75fe476`, `0617adb`, `03afe9f`, `e0e5652`, `c749eee`

# Addendum — F0.4 (2026-11-10)

F0.4 fresh-seed directional confirmation was completed after this synthesis.

- fresh seeds: 20261112/13/14
- fit gate: **6/6 pass**
- status: **NO_BENEFIT**
- E11 copy: **+0.0766**, CI **[-0.0027, +0.1633]**, 3/3 seeds positive but CI includes 0 → signal **false**
- E01 copy: −0.0150, non-signal
- `E11 − E01` copy: **+0.09166**, CI **[-0.01668, +0.21448]**, 3/3 seed D_s > 0
- `benefit_positive`: **false**; `equivalent`: false

Interpretation: direction remains positive (E11 > E01) but **F0.2's E11 signal/directional benefit was not confirmed** under fresh seeds. This is not proof of no effect; it is a failure to confirm under the current 15-doc/low-power cohort. F0 line should be closed as **directional but unconfirmed**. F0.2/F0.3 labels remain unchanged.
