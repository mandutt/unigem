# C5 D-084 rev2 — 3-AI 검토 종합 (2026-11-07)

## 0. 검토 개요

| 항목 | 값 |
|---|---|
| 요청서 | `reports/EXTERNAL_REVIEW_C5_D084_REV2_2026-11-07.md` (346줄) |
| rev2 | `docs/D-084_verifier_v2_rev2_2026-11-07.md` (368줄) |
| 검토 기준 | **`e8b6367`** |
| strict D-083 | **`selected_step: null`, pilot300 fallback** |
| test 163 | **A1 미사용·봉인** |

### 모델·비용

| 모델 | 추론 | thread | 비용 | input/output | 시간 |
|---|---|---|---:|---:|---:|
| GLM 5.3 Flash | max | `thr_6e6e188d6bd7449682ff9252779e9374` | **$0.1297** | 2.13M / 47.8K | 4분 30초 |
| **Sonnet 5.5** | **high** | `thr_c46eb18b19ff49c89d186dcf23b81883` | **$0.8584** | 1.19M / 40.5K | 5분 43초 |
| Sol 6.1 | xhigh | `thr_538e48812df648698704f33c8d747018` | **$0.6440** | 1.18M / 20.9K | 6분 21초 |
| **합계** | — | — | **$1.6320** | — | 약 17분 |

원문: `docs/hoplite/c5_d084_rev2_2026-11-07/review_{GLM,SONNET,SOL}.md`

---

## 1. 한 줄 결론

**3/3 모두 rev2의 방향(URL-only 084a + 084b report-only)은 지지하지만, 현재 상태로는 구현 승인·candidate 승인·human 50 실행을 할 수 없다고 판정했다.**

- **D-083**: 3/3 유지, `selected_step: null`, pilot300 fallback
- **084a**: 3/3 URL-only baseline 지지, 단 URL boundary/attestation/회귀 측정 보강 필요
- **084b**: 3/3 report-only/default off 지지
- **2,586**: 3/3 **conditional review nominee**; 아직 approved candidate 아님
- **1,940**: 3/3 **gate-ineligible, human exploratory**
- **test 163**: 3/3 봉인
- **D-084 rev2**: 3/3 **Must-fix 전 구현 승인 불가**

---

## 2. 판정 행렬

| 항목 | GLM | Sonnet | Sol | 공통 |
|---|---|---|---|---|
| **R1** 084a URL-only | 동의(조건부) | 동의(조건부) | 조건부 | **방향 지지, 보강 필요** |
| **R2** unit report-only | 동의 | 동의 | 동의 | **3/3 동의** |
| **R3** alias off | 동의 | 동의 | 동의 | **3/3 동의** |
| **R4** 2,586 nominee | 조건부 | 조건부 | 조건부 | **conditional review nominee** |
| **R5** 1,940 exploratory | 동의 | 동의 | 동의 | **3/3 동의** |
| **R6** human 50 | 동의(조건부) | 조건부 | 조건부 | **4 arms, decision rule 필요** |
| **R7** audit DoD | 조건부 | 조건부 | 조건부 | **Must-fix 필요** |
| **R8** test seal | 동의 | 동의 | 동의 | **3/3 봉인** |
| **Q1** separation | 동의(조건부) | 동의(조건부) | 조건부 | **machine-enforce 필요** |
| **Q2** URL attestation | 조건부 | 조건부 | **반대(불충분)** | **실행 규칙 필요** |
| **Q3** 1,940 158 | 동의 | 동의 | 동의 | **3/3 동의** |
| **Q4** qualifier 084b | 동의 | 동의 | 동의 | **3/3 동의** |
| **Q5** 2,586 vs no candidate | 조건부 | 조건부 | 조건부 | **conditional + exit branch** |
| **Q6** 1,293 sensitivity | 동의 | 동의(조건부) | 동의 | **sensitivity arm** |
| **Q7** human design | 동의(조건부) | 조건부 | 조건부 | **primary contrast 필요** |
| **Q8** G-C5/CP | 조건부 | 조건부 | **반대(불충분)** | **truth table 필요** |
| **Q9** audit DoD | 조건부 | 조건부 | 조건부 | **7 Must-fix** |
| **Q10** 383/5 flips | 조건부 | 조건부 | 조건부 | **084a flips 0 예상, 5는 084b** |
| **Q11** test conditions | 동의 | 조건부 | 조건부 | **action rule/freeze** |
| **Q12** draft gaps | 조건부 | 조건부 | 조건부 | **구현 전 수정** |
| **Q13** prior critiques resolved | 조건부 | 조건부 | 조건부 | **방향은 해결, 실행 미해결** |
| **Q14** errors | 오류 없음/omissions | 11 issues | 9 issues | **overstatement/용어 수정** |

---

## 3. 3/3 공통 결론

### 3.1 URL-only 084a는 올바른 방향

- URL wrap join과 URL case/comma strictness는 **measurement**다.
- qualifier/unit/alias는 **equivalence policy**이며 selection에서 제외한다.
- **1,940의 URL-only 158/161이 맞다.** 이전 synthesis의 159는 generic matcher 값이었고, 03978은 time-type이라 URL-only로 해소되지 않는다.
- 1,293/2,586의 160/161은 02742 URL repair에서 나온다.
- 647의 156은 **derived/unverified**; 647은 repeated4로 어차피 부적격.

### 3.2 2,586은 conditional review nominee

- 084a expected eligible: pilot300, 1,293, 2,586.
- max F1: **2,586** (0.6690 vs 1,293 0.6659, 차이 0.003).
- 2,586 − pilot300 F1 CI는 0 포함; preservation .4188 < pilot .4558; slot-free 11 (9 target slot omissions).
- **2,586은 approved candidate가 아니라 human-review nominee**.
- **no-candidate branch를 사전등록해야 한다**: audit 또는 human 50이 실패하면 “no approved candidate, pilot300 fallback 유지”.

### 3.3 1,940은 human exploratory

- 084a 158/161; 03978(time), 04709(bare 18), 04951(2.3/2.2 genuine).
- F1 .6823, preservation .4761, slot-free 4로 quality evidence는 가장 좋다.
- 그러나 non-alias gate-ineligible; alias로 eligible하게 만들지 않는다.
- human 50에서 quality comparator로 평가하되, selection eligibility와 분리한다.

### 3.4 084b는 report-only/default off

- unit: 902/1,617 collision, 5 old generic flips. selection 사용 금지.
- qualifier: 7/1,617 collision; 오전 omission은 information loss; selection 사용 금지.
- alias: default off; audit alias는 uniqueness 우회, `명` 미강제, offset 문제; production rule 금지.
- **5 excluded flips는 084b evidence**이며 084a의 5 flips가 아니다. 084a에서는 **expected 0**; URL flip이 나오면 adjudication.

### 3.5 URL boundary와 회귀

3/3가 새로 지적한 중요한 문제:

1. **URL boundary**: v1 URL regex가 trailing Hangul particle을 URL에 포함한다.
   - `https://coronamap.site에서` → URL slot에 `에서` 포함.
   - 084a는 URL boundary 규칙을 명시해야 한다.
2. **Strictness regression**:
   - URL case/comma strictness는 **match-removing** 방향이다.
   - 기존 v1 pass가 084a에서 **new fail**이 될 수 있다.
   - 현재 expected table은 one-directional; val/clean target의 양방향 재채점이 필요하다.
3. **URL recall**:
   - wrap regex가 `?`, `=`, `&`, `#`, `%` terminator를 놓칠 수 있다.
   - 3/1,617은 regex가 찾은 수이지 전체 wrap 수가 아니다.
4. **04909 trailing slash**, **fine.fss. unresolved**, **percent-escape case** 정책 필요.

### 3.6 DoD/API separation

- `VerifierV2Policy` flag와 `verify_summary_v2()`가 selection-bearing `grounded`를 반환하면 084b가 섞일 수 있다.
- **machine-enforce**:
  - `selection_v2`는 084a-only policy/spec hash일 때만 write.
  - 084b fields는 read-only diagnostic pass.
  - diagnostic toggle이 `grounded`/counts/ranking을 바꾸지 않음을 test.
- DoD를 **084a DoD / 084b DoD**로 분리.
- `status` 하나로 PASS/FAIL/INCONCLUSIVE를 합치지 말고 **screen eligibility / evidence status / approval**을 분리.

### 3.7 Gate/CP

- D-083 point screens 유지: grounded ≥.99, new-slot micro ≤.01, EOS ≥.95, repeated4 ≤.06.
- **doc-level CP95**: 160/161 lower .9659; 161/161 lower .9773 — 모두 .99 미만.
- **slot-level CP**: pilot 0/837 upper .44%; 1,940 4/860 upper 1.19%; 2,586 3/762 upper 1.15%.
- `INCONCLUSIVE`가 eligibility를 제거하면 **모든 system이 INCONCLUSIVE**가 되어 selection이 vacuous해진다.
- 따라서:
  - point-screen eligibility와 statistical evidence status를 분리.
  - INCONCLUSIVE는 label/evidence status이며 eligibility를 자동 제거하지 않는다.
  - CP convention은 two-sided 95%로 사전 고정.
  - slot observations are clustered; doc/article-family uncertainty 별도.

### 3.8 Human 50

- same 50 unique val docs, 4 arms.
- **400 ratings** (50 × 4 × 2), not 50.
- primary contrast: **2,586 vs pilot300**.
- 1,293 = sensitivity; 1,940 = exploratory.
- rubric: unsupported/extrinsic content, critical omission, wrong unit/qualifier, entity/relation, fluency, memory utility.
- blind, randomized, 2 raters, third arbitration.
- **decision rule/action**을 사전등록:
  - 2,586이 unsupported content에서 non-inferior, omission에서 acceptable
  - 실패/INCONCLUSIVE → no approved candidate, pilot300 fallback, test 163 seal.
- 16/161 prefix-sharing docs는 random stratum에서 flag/exclude sensitivity.

### 3.9 Test 163

- 3/3 sealed.
- release chain:
  - rev2 Must-fix → spec-faithful 084a audit → all changed decisions adjudication → selection_v2 → human 50 → candidate/hash/policy freeze → **separate explicit authorization** → A1 one-shot.
- A0 D-080, corpus-wide audit exposure, A1 predictive 미사용을 분리 기록.
- human 50이 완료됐다는 이유만으로 test를 열지 않는다.

---

## 4. 공통 Must-fix

1. **URL spec executable**
   - source-side attestation, both-side wrap, Hangul boundary, delimiters, wrong-suffix, percent-escape, trailing slash, raw offsets, `fine.fss.` unresolved, 04909.
   - golden/negative tests.
2. **Bidirectional strictness audit**
   - v1 pass → 084a fail, v1 fail → 084a pass 모두.
   - val 161 + clean/train/val targets + 383 excluded; per-doc IDs.
   - expected table commit before run.
3. **DoD split / API enforcement**
   - 084a and 084b separate.
   - selection_v2 refuses non-084a policy/spec.
   - diagnostic invariance tests.
4. **No-candidate + status truth table**
   - audit fail/human fail/INCONCLUSIVE → no approved candidate.
   - point-screen eligibility vs statistical evidence vs approval.
   - CP convention, denominators, INCONCLUSIVE semantics.
5. **Residual failures / fragility**
   - characterize 03801, 647 residuals, 04709 exact cause, 04951 negative control.
   - 2,586 one-document margin; 1,293 sensitivity.
   - 1,940 not highest preservation overall (647 .4873 > .4761) but 647 ineligible.
6. **Corrected audit + all changed decisions**
   - all 383 + saved val outputs; policy-specific.
   - 5 historical generic flips = 084b evidence, not 084a.
   - blind two-rater + arbitration; any confirmed/ambiguous false accept → narrow/remove clause + rerun.
7. **Human 50 executable protocol**
   - primary 2,586 vs pilot300; 1,293 sensitivity; 1,940 exploratory.
   - 400 ratings; strata; rubric; stop/hold; action.
   - prefix overlap sensitivity.
8. **D-083 immutable / test firewall**
   - hash/tag v1 and D-083 artifacts.
   - `selection_v2.json` separate.
   - test use-log; one-shot; separate authorization.

---

## 5. 이견

| 쟁점 | GLM | Sonnet | Sol | 종합 |
|---|---|---|---|---|
| 084a direction | 동의(조건부) | 동의(조건부) | 조건부 | **direction yes, implementation conditional** |
| URL attestation sufficiency | 조건부 | 조건부 | **불충분(반대)** | **executable spec 필요** |
| 2,586 | 조건부 nominee | 조건부 nominee | 조건부 nominee | **conditional, not approved** |
| human primary | 2,586 decision | 2,586 vs pilot | 2,586 vs pilot | **2,586 vs pilot** |
| CP/G-C5 | 조건부 | 조건부 | **불충분** | **truth table 필요** |
| 084b 5 flips | 084b evidence | 084b evidence | 084b evidence | **084a 아님** |
| test | 봉인 | 봉인 | 봉인 | **3/3** |

---

## 6. 다음 순서

1. **rev2 Must-fix 반영 → rev3 작성**
   - URL executable spec, DoD split, API enforcement, no-candidate, status truth table, human decision rule.
2. **spec-faithful 084a 구현·audit**
   - tests, bidirectional flips, data allowlist, no test.
3. **모든 changed decision adjudication**
   - 383 + val; blind; arbitration.
4. **selection_v2**
   - 084a only; 2,586 conditional nominee; no-candidate branch.
5. **Human 50**
   - 4 arms, 2,586 vs pilot primary; 1,940 exploratory.
6. **Test 163**
   - separate authorization after freeze.

---

## 7. 현재 상태

| 항목 | 값 |
|---|---|
| D-083 | **selected_step null / pilot300 fallback** |
| D-084 rev2 | **direction supported; implementation conditional** |
| production verifier | **미수정** |
| audit matcher | **spec 미준수; provisional** |
| human 50 | 미실행 |
| test 163 | **봉인** |
| 비용 | **$1.6320** |
| 원문 | `docs/hoplite/c5_d084_rev2_2026-11-07/review_{GLM,SONNET,SOL}.md` |

**어떤 gate change, candidate 승인, human 실행, test 개방도 이 검토로 승인되지 않았다.**
