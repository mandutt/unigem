# C5 D-084 verifier v2 — 3-AI 검토 종합 (2026-11-07)

## 0. 검토 개요

| 항목 | 값 |
|---|---|
| 요청서 | `reports/EXTERNAL_REVIEW_C5_D084_2026-11-07.md` (446줄) |
| D-084 초안 | `docs/D-084_verifier_v2_draft_2026-11-07.md` |
| audit | `reports/C5_A1_verifier_v2_audit_2026-11-07.md` |
| 검토 기준 | **`fc31b07`** (요청서 `7ffa251` + 프롬프트/dispatch `fc31b07`) |
| strict D-083 | **`selected_step: null`, pilot300 fallback** |
| test 163 | **A1 미사용·봉인** |

### 모델·비용

| 모델 | 추론 | thread | 비용 | input/output | 시간 |
|---|---|---|---:|---:|---:|
| GLM 5.3 Flash | max | `thr_427124d7b22843e8a11e2ec1cddb7827` | **$0.1349** | 1.32M / 66.2K | 5분 48초 |
| **Sonnet 5.5** | **high** | `thr_e55753f9fde7414581fd74ab640ea4a8` | **$0.8519** | 0.63M / 42.0K | 5분 42초 |
| Sol 6.1 | xhigh | `thr_ae02e0e25cdd4af1a7435437ab09a32a` | **$0.6873** | 1.00M / 24.4K | 7분 16초 |
| **합계** | — | — | **$1.6741** | — | 약 19분 |

원문: `docs/hoplite/c5_d084_2026-11-07/review_{GLM,SONNET,SOL}.md`

---

## 1. 한 줄 결론

**3/3 모두 D-083 strict 결과를 유지하고, D-084를 “outcome-informed exploratory”로만 다루며, 현재 D-084 초안을 그대로 승인하지 말고 URL-only baseline으로 축소한 뒤 spec-faithful audit을 다시 수행하라고 판정했다.**

- **D-083**: 3/3 유지, pilot300 fallback, 제품 승격 없음
- **D-084 초안**: 3/3 “그대로 승인 불가”
- **generic unit rule**: 3/3 “selection-bearing default로 부적절” (Sonnet/Sol은 disagree, GLM은 conditional)
- **counter alias**: 3/3 “자동 채택 금지; human adjudication 밖”
- **formal candidate**: 3/3 “non-alias 기준이면 2,586”
- **1,940**: 3/3 “human exploratory comparator/primary; alias 없이는 gate-ineligible”
- **test 163**: 3/3 봉인
- **human 50**: 3/3 blind 4-arm, 2,586 decision primary / 1,940 exploratory (GLM은 1,940 quality primary를 더 강조)

---

## 2. 판정 행렬

| 항목 | GLM 5.3 Flash | Sonnet 5.5 | Sol 6.1 | 공통 결론 |
|---|---|---|---|---|
| **D4-1** unit policy | 조건부 — generic exploratory, alias separate | **반대** — generic unit은 selection-bearing 부적절 | **반대** — URL-only baseline | **unit default off / report-only** |
| **D4-2** generic candidate | 조건부 — 2,586 | 조건부 — 2,586 | 조건부 — 2,586 | **2,586 (non-alias)** |
| **D4-3** alias candidate | 보류 / 조건부 | **반대** | 보류 | **alias 미승인, 1,940 candidate 아님** |
| **D4-4** gate additions | 동의 | 조건부 | 동의 | **nonvacuous/CP/INCONCLUSIVE 추가** |
| **D4-5** 5 flips | 보류 | 조건부 | 보류 | **전건 adjudication, false accept 0** |
| **D4-6** URL case/comma | 조건부 — v2 내 수정 | 동의 — 지금 수정 | 동의 — 지금 수정 | **v2에 포함, v1 불변** |
| **D5-1** human 50 | 조건부 — 4 arms, 1,940 primary | 조건부 — 4 arms, 2,586 decision | 조건부 — 4 arms, 2,586 decision | **4 arms, 2,586 decision / 1,940 exploratory** |
| **D5-2** test 163 | 동의 — 봉인 | 동의 — 봉인 | 동의 — 봉인 | **3/3 봉인** |
| **D5-3** next | 조건부 — D-084 → human → seed43 | 조건부 — v2 구현/ablation → human | 동의 — verifier first | **v2 audit first; training later** |
| **D5-4** D-084 status | 조건부 — exploratory | 조건부 — exploratory | 조건부 | **outcome-informed exploratory** |
| **Q1** generic vs URL-only | 조건부 | 조건부 | **반대 (generic)** | **URL-only baseline first** |
| **Q2** alias | 동의 — separate human | 조건부 — default off | 조건부 — human | **별도 clause, default off** |
| **Q3** 5 flips | 보류 / 조건부 | 조건부 | 보류 | **blind adjudication** |
| **Q4** exploratory | 조건부 | 조건부 | 조건부 | **가능, D-083 불변** |
| **Q5** 1,940 vs 2,586 | 조건부 — 역할 분리 | 조건부 — 2,586 | 동의 — 2,586 | **2,586 formal, 1,940 human** |
| **Q6** alias 근거 | 조건부 | 반대 | 보류 | **현재 근거 부족** |
| **Q7** human design | 동의 | 조건부 | 조건부 | **4 arms, blind, 2 raters** |
| **Q8** G-C5 | 동의 | 조건부 | 조건부 | **별도 denominator/CP** |
| **Q9** n=161 | 동의 — CP 병기 | 동의 — CP/INCONCLUSIVE | 동의 | **gate 유지, certificate 아님** |
| **Q10** test | 동의 | 동의 | 동의 | **봉인** |
| **Q11** URL fix | 조건부 — 포함 | 동의 | 동의 | **v2에 포함** |
| **Q12** draft gaps | 조건부 — Must-fix | 조건부 — 7 Must-fix | 조건부 — 7 Must-fix | **수정 필요** |
| **Q13** human vs eligible | 동의 | 동의 | 동의 | **분리** |
| **Q14** errors | 2 omissions | 11 issues | 11 issues | **spec/implementation gap** |

---

## 3. 3/3 공통 결론

### 3.1 D-083 strict는 불변

- `selected_step: null`, pilot300 fallback.
- D-084가 승인되어도 D-083 기록을 덮어쓰지 않는다.
- `selection_v2.json`은 별도 파일로 두고, strict와 v2를 항상 side-by-side로 표시한다.
- D-083 파일은 hash/tag로 보존한다.

### 3.2 현재 D-084 초안은 그대로 승인 불가

3/3 공통 이유:

1. **audit matcher가 D-084 spec을 완전히 구현하지 않았다.**
   - URL path/query case·comma strictness가 빠져 있다.
   - v1 `_canonical`을 재사용해 URL false accept를 그대로 상속한다.
   - uniqueness가 “distinct unit-type”이 아니라 “occurrence count”다.
   - alias 구현이 draft보다 훨씬 넓다.
2. **generic unit rule이 selection-bearing이다.**
   - 1,293·2,586은 URL만으로 160/161.
   - 1,940만 unit/alias에 의존.
   - 902/1,617 numeric collision.
3. **5 excluded flip은 truth label이 없다.**
   - 5/383은 false-accept rate가 아니라 **flip rate**.
   - human-confirmed false accept 0 기준이 필요하다.

**결론**: D-084를 “URL-only 084a”와 “equivalence 084b”로 분리하고, 084b는 default off/report-only로 시작해야 한다.

### 3.3 URL-only baseline

3/3 공통:

- **URL wrap join**: source와 summary 양쪽, source-attested, ambiguity guard.
- **URL canonicalization**: scheme/host만 lowercase; path/query case·comma·escape 보존.
- **time/unit은 default off**; 별도 policy로만 보고.
- `fine.fss.` wrap candidate는 문맥 확인 필요.
- URL wrap regex가 문장 단어를 잘못 join할 수 있으므로 negative test 필요.

### 3.4 2,586이 formal candidate, 1,940은 human exploratory

non-alias 기준:

| system | strict | URL-only/generic | 판정 |
|---|---:|---:|---|
| pilot300 | 161/161 | 161/161 | strict fallback |
| 647 | 155/161 | 158/161 | rep4 fail |
| 1,293 | 159/161 | 160/161 | eligible, F1 .6659 |
| 1,940 | 158/161 | **159/161** | **gate-ineligible**, human exploratory |
| **2,586** | 159/161 | **160/161** | **formal max-F1 candidate**, not promoted |

- 2,586 F1 .6690 > 1,293 .6659, but gap .003은 noise 수준.
- 2,586 − pilot300 F1 CI는 0 포함, preservation .4188 < pilot .4558, slot-free 11 > 6.
- **eligibility ≠ superiority**; 2,586은 “human-review candidate”일 뿐 제품 승격이 아니다.
- 1,940은 F1 .6823, preservation .4761, slot-free 4로 quality evidence가 가장 좋지만, generic gate에서는 부적격.
- **1,940을 alias로 eligible하게 만들지 않는다.**

### 3.5 Alias는 현재 승인 불가

3/3 공통:

- `18 확진자` ↔ `18명`은 regex normalization이 아니라 **entity/scope adjudication**이다.
- audit alias는 uniqueness를 모든 값에서 우회하고, source unit `명`을 강제하지 않으며, 24자 window/offset 문제가 있다.
- non-additive: alias=True가 generic unique match를 오히려 깨뜨릴 수 있다.
- source `18일`을 사람 수로 잘못 credit할 수 있다.
- **default off**, human-adjudicated closed table, unit-constrained, all firings adjudicated.

### 3.6 Human 50

공통:

- same 50 unique val docs, blind, randomized order.
- **4 arms**: pilot300, 1,293, 1,940, 2,586.
- two raters, targeted + random strata separately, no naive pooled bootstrap.
- **decision primary = policy-selected 2,586** (non-alias), **1,940 = exploratory comparator**.
- GLM은 1,940을 quality-primary로 더 강조하지만, Sonnet/Sol은 2,586을 decision-primary로 본다. **selection과 quality를 분리**하는 것이 공통 해법.
- Human 50은 confirmatory가 아니라 exploratory; val reuse 때문에 population claim 불가.

### 3.7 Gate/CP

- grounded 0.99 유지.
- **nonvacuous grounded** 별도 보고.
- **slot-level new-slot micro + CP95 + INCONCLUSIVE**.
- pilot300 0/837 → CP upper .44% (consistent).
- 1,940 4/860 → upper 1.19% (point pass, CI fail).
- 2,586 3/762 → upper 1.15% (point pass, CI fail).
- doc-level 160/161 CP lower .9659 < .99; gate는 screen이지 certificate가 아니다.
- 161/161도 99% population guarantee가 아니다; 0-error 95% lower bound에는 n≥368 (two-sided).

### 3.8 Test 163

- 3/3 봉인.
- 해제 조건:
  - D-084 approved
  - spec-faithful v2 + audit
  - 383 flip adjudication
  - full re-selection
  - human 50
  - single candidate/hash/policy freeze
  - A1 1회
- A0 D-080 사용 이력, corpus-wide source/target audit exposure, A1 predictive 미사용을 분리 기록.

---

## 4. Audit 구현 결함 — 반드시 고칠 것

3-AI가 독립적으로 확인한 audit matcher 문제:

| # | 문제 | 영향 |
|---|---|---|
| 1 | URL matching이 v1 `_canonical`을 사용해 path/query case·comma를 잃음 | 현재 v2 수치는 **spec 미준수**, false accept 가능 |
| 2 | uniqueness가 occurrence count | distinct value+unit 기준이 아님; `04709` 설명 불완전 가능 |
| 3 | alias가 uniqueness 우회, `명` 미강제, 24자 window, offset 불일치 | date/percent를 person count로 오인 |
| 4 | alias=True가 generic match를 깨뜨릴 수 있음 | “generic + alias”가 additive가 아님 |
| 5 | summary URL repair evidence를 discard | audit trace 불완전 |
| 6 | corpus audit이 clean 1,617 전체(train+val+test)를 로드 | test source/target exposure history 명시 필요 |
| 7 | `URL+qualifier only` 행은 직접 실행된 적 없음 | derived scenario; final result 아님 |
| 8 | `fine.fss.` wrap은 문맥 확인 필요 | 3개 URL wrap 중 false join 가능 |
| 9 | `clean 1,617 v1/v2 차이 0`은 vacuous | clean은 v1 grounded by construction; safety 증명 아님 |
| 10 | 5/383은 flip rate | false-accept rate 아님; truth label 없음 |

**따라서 현재 v2 숫자는 모두 “pre-spec audit matcher의 optimistic upper bound”로 표기해야 한다.**

---

## 5. 공통 Must-fix

1. **spec-faithful audit 재실행**
   - URL path/query case·comma·escape
   - distinct unit-type uniqueness
   - source-attested summary URL join
   - alias default off
   - all-clean access 제거; train/val + excluded-only manifests
2. **D-084를 084a/084b로 분리**
   - 084a = URL wrap + URL canonicalization (measurement)
   - 084b = qualifier / unit / alias (equivalence; default off/report-only)
   - policy/spec hash를 freeze한 뒤 final re-selection
3. **Clause ablation**
   - URL / +qualifier / +unit / +alias
   - val 5 systems + 383 pool
   - responsible clause per changed document
4. **383 flip adjudication**
   - blind two raters, third arbitration
   - full source/summary spans, rule reason
   - acceptance: **human-confirmed false accept 0 + unresolved auto-accept 0**
   - any confirmed/ambiguous false accept → remove/narrow clause
5. **Candidate/eligibility 분리**
   - non-alias formal candidate: 2,586
   - 1,940: human exploratory comparator
   - 2,586: not promoted; pilot300 fallback
   - alias로 1,940을 eligible하게 만들지 않음
6. **Gate reporting**
   - nonvacuous
   - slot-free with target≥3 breakdown
   - preservation vs target-implied ~0.465
   - CP95 + INCONCLUSIVE
   - doc/slot denominators
7. **Human 50 freeze**
   - 4 arms, same 50, blind, 2 raters
   - predefined primary contrast
   - targeted/random separate
   - exploratory only
8. **Test 163 / D-083 immutability**
   - D-083 hash/tag
   - `selection_v2.json` separate
   - test use-log
   - A1 one-shot only

---

## 6. 이견

| 쟁점 | GLM | Sonnet | Sol | 종합 |
|---|---|---|---|---|
| 1,940 human role | quality primary | co-primary/exploratory | exploratory; 2,586 decision | **1,940 exploratory primary; 2,586 decision primary** |
| generic unit | conditional exploratory | disagree | disagree | **default off / report-only** |
| D-084 split | one exploratory | 084a/084b | 084a/084b | **split 권고** |
| human 50 arms | 4 | 4 (1,293 optional) | 4 | **4 arms** |
| alias | separate human clause | default off, no alias now | human only | **default off** |
| candidate | 2,586 mechanical | 2,586 formal, not better | 2,586 formal | **2,586 formal, no promotion** |

---

## 7. 다음 순서

1. **D-084 초안 수정** — URL-only baseline, generic/alias default off, 084a/084b 분리, audit implementation caveat 명시.
2. **spec-faithful audit 구현·재실행** — URL strictness, distinct uniqueness, source-attested joins, tests.
3. **383 flip + 5 flips adjudication** — blind human, source spans.
4. **전체 checkpoint 재채점** — pilot300, 647, 1,293, 1,940, 2,586; strict/v2 side-by-side.
5. **Human 50** — 4 arms, 2,586 decision primary, 1,940 exploratory.
6. **Test 163** — 위 완료 + candidate freeze 후 1회.
7. **Seed 43 / compression arm** — 그 이후, 별도 승인.

---

## 8. 현재 상태

| 항목 | 값 |
|---|---|
| D-083 strict | **selected_step null / pilot300 fallback** |
| D-084 | **draft; 3-AI review 결과 수정 필요** |
| production verifier | **미수정** |
| audit matcher | **spec 미준수; provisional** |
| human 50 | 미실행 |
| test 163 | **봉인** |
| 비용 | **$1.6741** |
| 원문 | `docs/hoplite/c5_d084_2026-11-07/review_{GLM,SONNET,SOL}.md` |
