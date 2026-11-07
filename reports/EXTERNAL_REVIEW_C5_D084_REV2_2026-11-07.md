# 외부 검토 요청 — D-084 rev2 (URL-only baseline) (2026-11-07)

- 저장소: `mandutt/unigem` (비공개), branch `main`
- 검토 기준: **본 문서가 포함된 `origin/main` HEAD**
- 데이터 등급: **P0(공개·합성 가공)**. P1 데이터는 사용하지 않았다.
- test 163: **A0가 과거 사용(D-080, 0.6072); A1에는 미사용·봉인**
- 이 문서는 자기완결형이다. 이전 Hoplite 스레드나 대화를 읽지 않아도 판단할 수 있다.
- **D-084 rev2는 draft이며 승인된 결정이 아니다.** production `eval/slot_verify.py`·selection은 수정하지 않았다.

---

## 0. 한눈에 보는 현재 상태

1. **D-083 strict 결과는 유효**하다.
   - full train 4 checkpoint 모두 grounded gate 미달
   - `selected_step = null`
   - fallback = **pilot300** (제품 승격 아님)
2. **A1 full train**은 정상 완료됐다.
   - 2 epoch = 2,586 step, 4시간 20분 18초, exit 0
   - test 163 미사용
3. **직전 D-084 3-AI 검토**는 다음에 합의했다.
   - D-083 strict 유지
   - 현재 D-084 초안 그대로 승인 불가
   - URL-only baseline을 먼저
   - generic unit/alias는 default off
   - **non-alias formal candidate = 2,586**
   - **1,940 = human exploratory, gate-ineligible**
   - test 163 봉인
4. **rev2**는 그 합의를 반영해 작성됐다.
   - 084a = URL-only measurement baseline
   - 084b = qualifier/unit/alias report-only, default off
   - 2,586 provisional formal candidate
   - 1,940 human exploratory comparator
   - human 50 4 arms, 2,586 decision primary
   - test 163 봉인
5. **판단이 필요한 핵심**:
   - 084a URL-only baseline을 승인할 수 있는가
   - 084b를 정말 selection에서 배제하는가
   - 2,586을 formal candidate로 두는 것이 맞는가
   - 1,940을 human exploratory로만 두는 것이 맞는가
   - spec-faithful audit의 DoD가 충분한가
   - human 50/test 163 조건이 충분한가

---

## 1. D-083 strict 결과

### 1.1 데이터·모델

| 항목 | 값 |
|---|---|
| clean | **1,617** |
| train / val / test | 1,293 / 161 / 163 |
| base | T5Gemma2-270m-270m, vision tower 제거 |
| params | 370,637,824 |
| LoRA | q/k/v/o r8 alpha16 dropout0.05 |
| trainable | 1,474,560 (0.40%) |
| input / label | `summarize: ` + passage / summary + `<eos>` |
| max input / target | 1,024 / 512 |
| run | 2 epoch, 2,586 step, 4시간 20분 18초, exit 0 |
| peak RSS | 약 3.88GB |

### 1.2 strict table

| checkpoint | char F1 | grounded | new slot | EOS | repeated4 | slot preservation | slot-free | gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **pilot300 fallback** | 0.657580 | **161/161** | 0 | **161/161** | 0.05535 | 0.45583 | 6/161 | PASS |
| 647 | 0.669853 | 155/161 | 6 | 160/161 | 0.06840 | 0.48729 | 2/161 | FAIL |
| 1,293 | 0.665946 | 159/161 | 2 | 161/161 | 0.05866 | 0.45705 | 8/161 | FAIL grounded |
| **1,940** | **0.682278** | 158/161 | 4 | 161/161 | 0.05138 | 0.47610 | 4/161 | FAIL grounded |
| 2,586 | 0.668982 | 159/161 | 3 | 161/161 | 0.04450 | 0.41882 | 11/161 | FAIL grounded |

- 161문서에서 grounded ≥0.99는 **최대 1건 실패**.
- 160/161 = 0.9938 통과; 159/161 = 0.9876 실패.
- 647은 repeated4 0.0684로 부적격.
- `selected_step = null`; pilot300 fallback.

### 1.3 paired F1

| 비교 | mean diff | 95% bootstrap CI |
|---|---:|---:|
| 1,940 − pilot300 | **+0.024698** | **[+0.012027, +0.037295]** |
| 2,586 − pilot300 | +0.011402 | [−0.000398, +0.023058] |
| 1,940 − 2,586 | **+0.013297** | **[+0.001197, +0.024928]** |

---

## 2. 직전 D-084 3-AI 검토 결과

모델: **GLM 5.3 Flash max / Sonnet 5.5 high / Sol 6.1 xhigh**. 비용 약 **$1.6741**. 원문 `docs/hoplite/c5_d084_2026-11-07/review_{GLM,SONNET,SOL}.md`.

### 2.1 공통 결론

- D-083 strict 유지.
- D-084는 **outcome-informed exploratory**로만 가능.
- 현재 D-084 초안 그대로 승인 불가.
- **URL-only baseline**을 먼저.
- generic unit / alias는 default off.
- **non-alias formal candidate = 2,586**.
- **1,940 = human exploratory**, alias 없이는 gate-ineligible.
- test 163 봉인.

### 2.2 지적된 audit 구현 결함

- URL matcher가 v1 canonicalizer를 상속해 **path/query case·comma**를 잃음.
- uniqueness가 **distinct unit-type**이 아니라 occurrence count.
- alias가 uniqueness를 우회하고 `명`을 강제하지 않음.
- alias=True가 generic match를 깨뜨릴 수 있음.
- summary URL repair evidence 일부 유실.
- all-clean audit이 train+val+test source/target을 로드.
- `URL+qualifier only` 행은 직접 실행된 적 없음.
- `fine.fss.` wrap은 문맥 확인 필요.
- clean 1,617 v1/v2 차이 0은 **vacuous**; clean은 v1 grounded by construction.
- 5/383은 **flip rate**, false-accept rate 아님.

### 2.3 이견

- GLM: generic unit을 exploratory baseline으로 허용, 1,940을 quality-primary로 더 강조.
- Sonnet: generic unit default 반대, 2,586 decision primary.
- Sol: URL-only baseline, generic unit default 반대, 2,586 decision primary.

이번 rev2는 **Sonnet/Sol의 URL-only 방향**을 채택하고, GLM의 1,940 quality evidence는 human exploratory로 보존한다.

---

## 3. D-084 rev2 — 084a

### 3.1 URL soft-wrap

- source와 summary **양쪽**.
- URL token이 newline 직전 `.`/`/`/`-`/`_`로 끝나고 다음 token이 source-attested URL continuation일 때만 join.
- suffix 추측 금지.
- `02742`의 wrapped/joined pair를 golden test.
- `http://fine.fss.`는 unresolved.
- over-join negative test 포함.

### 3.2 URL canonicalization

- scheme/host만 lowercase.
- **path/query/fragment case, comma, escape 보존**.
- trailing sentence punctuation만 별도 제거.
- `Case?key=A,B`와 `case?key=ab`는 같지 않음.

### 3.3 084a expected — provisional

| system | v1 | 084a expected | 비고 |
|---|---:|---:|---|
| pilot300 | 161/161 | 161/161 | 변화 없음 |
| 647 | 155/161 | 156/161 | 02742만 해소; 03978 등 잔여 |
| **1,293** | 159/161 | **160/161** | 02742 해소; 03801 잔여 |
| **1,940** | 158/161 | **158/161** | 02742는 v1에서 이미 grounded |
| **2,586** | 159/161 | **160/161** | 02742 해소; 04951 잔여 |

- 084a eligible set 예상: pilot300, 1,293, 2,586.
- max F1 예상: **2,586** (0.6690).
- **1,940은 158/161로 gate-ineligible**.
- 이 표는 spec-faithful audit 전 provisional.

---

## 4. D-084 rev2 — 084b

084b는 **report-only / default off**이며 084a selection에 사용하지 않는다.

### 4.1 time qualifier

- `qualifier_dropped` 기록.
- summary가 새 qualifier를 붙이면 new.
- 오전/오후 collision은 unresolved.
- selection 사용 금지.

### 4.2 numeric unit

- `unit_dropped` 후보만 기록.
- 자동 grounded 인정 금지.
- 902/1,617 numeric unit collision.
- 5 excluded flip.
- selection 사용 금지.

### 4.3 counter alias

- default off.
- `18 확진자` ↔ `18명`은 entity/scope adjudication.
- closed head-noun table, `명` unit, same event/group/scope, all firings human adjudication 필요.
- 04709 한 건으로 승인 금지.
- audit의 loose alias 구현은 production rule 금지.
- selection 사용 금지.

---

## 5. Candidate / human / test

### 5.1 Candidate

| system | 084a | 역할 |
|---|---|---|
| **2,586** | 160/161 expected | **provisional formal candidate**, not promoted |
| 1,293 | 160/161 expected | sensitivity comparator |
| 1,940 | 158/161 expected | **human exploratory comparator** |
| pilot300 | 161/161 | strict fallback / control |

- 2,586은 F1 .6690 > 1,293 .6659이나 차이는 .003.
- 2,586 − pilot300 F1 CI는 0 포함.
- 2,586 preservation .4188 < pilot .4558; slot-free 11 > 6.
- **eligibility ≠ superiority**; 2,586도 제품 승격 아님.
- 1,940은 F1/preservation quality가 가장 좋지만 non-alias gate-ineligible.

### 5.2 Human 50

- same 50 unique val docs.
- 4 arms: pilot300 / 1,293 / 1,940 / 2,586.
- blind, randomized order, 2 raters.
- **2,586 decision primary**.
- **1,940 exploratory comparator**.
- targeted + random strata separately.
- human 50은 exploratory; confirmatory 아님.

### 5.3 Test 163

```text
D-084 rev2 승인
→ spec-faithful 084a audit
→ 383 flip adjudication
→ selection_v2
→ human 50
→ candidate/hash/policy freeze
→ A1 test 163 1회
→ retuning 금지
```

A0 D-080 사용, corpus-wide audit exposure, A1 predictive 미사용을 분리 기록한다.

---

## 6. 판단이 필요한 내역

| ID | 결정 | 선택지 | 현재 |
|---|---|---|---|
| **R1** | 084a baseline | URL-only / URL+qualifier / generic | **rev2: URL-only** |
| **R2** | 084b unit | report-only / off / future policy | **rev2: report-only** |
| **R3** | 084b alias | off / human adjudicated closed table | **rev2: off** |
| **R4** | candidate | 2,586 / 1,293 / defer | **rev2: 2,586 provisional** |
| **R5** | 1,940 role | human exploratory / eligible via alias / drop | **rev2: exploratory** |
| **R6** | human 50 | 4 arms / 2,586 decision primary / 1,940 exploratory | **rev2: 4 arms** |
| **R7** | spec audit DoD | current / stronger | **rev2: stronger** |
| **R8** | test 163 | seal / later one-shot | **seal** |

---

## 7. 검토 질문

**Q1.** rev2의 **URL-only 084a**가 3-AI가 요구한 “measurement fix vs equivalence policy” 분리를 충분히 달성하는가?

**Q2.** URL wrap join의 source-attested 조건과 `fine.fss.` unresolved 처리가 충분한가? over-join을 막는 negative test가 충분한가?

**Q3.** 084a에서 1,940이 158/161로 남는 것을 받아들이는가? 1,940을 human exploratory로 두는 것이 맞는가, 아니면 alias policy를 별도로 먼저 확정해야 하는가?

**Q4.** 084b를 **report-only / default off**로 두는 것이 맞는가? qualifier를 084a에 포함해야 하는가?

**Q5.** 2,586을 non-alias formal candidate로 두는 것이 맞는가? 2,586의 over-compression(preservation .4188, slot-free 11) 때문에 “no candidate”가 더 정직한가?

**Q6.** 1,293을 human 50의 sensitivity arm으로 포함하는 것이 충분한가? 아니면 1,293을 formal candidate로 재검토해야 하는가?

**Q7.** human 50을 4 arms, 2,586 decision primary, 1,940 exploratory로 구성하는 것이 타당한가? 1,940을 quality-primary로 두는 GLM 의견을 어떻게 반영해야 하는가?

**Q8.** G-C5에 nonvacuous, coverage/adequacy, CP95, INCONCLUSIVE를 추가하는 방식이 충분한가? 구체적 threshold가 필요한가?

**Q9.** spec-faithful audit의 DoD—URL strictness, distinct typed-slot uniqueness, source-attested summary join, train/val+excluded-only inputs—가 충분한가? 빠진 Must-fix는 무엇인가?

**Q10.** 383 excluded flip adjudication과 5 flip의 blind two-rater 기준이 충분한가? “human-confirmed false accept 0 + unresolved auto-accept 0”이 현실적인가?

**Q11.** test 163의 해제 조건이 충분한가? D-084 rev2 → audit → human 50 → candidate freeze 순서를 바꿔야 하는 이유가 있는가?

**Q12.** D-084 rev2의 Scope/DoD/API/구현 순서에서 빠진 것이 있는가? 구현 전에 반드시 고칠 Must-fix는 무엇인가?

**Q13.** 이 rev2가 직전 3-AI 지적을 실제로 해소했는가? 남은 overstatement·omission은 무엇인가?

**Q14.** 이 요청서의 사실 오류·과장·누락은 무엇인가?

---

## 8. 산출물·재현

### 문서

- `docs/D-084_verifier_v2_rev2_2026-11-07.md`
- `docs/D-084_verifier_v2_draft_2026-11-07.md` (검토 이력)
- `reports/C5_D084_3AI_REVIEW_SYNTHESIS_2026-11-07.md`
- `reports/C5_A1_verifier_v2_audit_2026-11-07.md`
- `reports/C5_A1_3AI_REVIEW_SYNTHESIS_2026-11-07.md`
- `reports/C5_A1_full_train_2ep_2026-11-07.md`

### 데이터·코드

- `runner/c5_a1_verifier_v2_audit.py` (audit; production 아님)
- `eval/slot_verify.py` (v1, 수정 금지)
- `reports/provenance/C5_a1/full_2ep/verifier_v2_audit.json`
- `reports/provenance/C5_a1/full_2ep/eval_step_{0647,1293,1940,2586}/`
- `reports/provenance/C5_a1/full_2ep/selection_summary.json`

### 재현

```bash
.venv/Scripts/python.exe runner/c5_a1_verifier_v2_audit.py
.venv/Scripts/python.exe -m unittest discover -s eval/tests
```

## 9. 한계

- test 163은 A1에 사용하지 않았다. A0는 D-080에서 사용했다.
- human 50은 아직 없다.
- char F1은 lexical metric이며 의미·사실성을 보장하지 않는다.
- grounded는 신규 slot만 본다. 누락은 보지 않는다.
- 2,586의 slot-free 11건 중 9건은 target slot 누락이다.
- val 161은 prompt/LR/pilot 선택에 재사용됐다.
- 16/161 val 문서가 train article prefix를 공유한다.
- 084a expected table은 spec-faithful audit 전 provisional.
- 2,586은 pilot300보다 우수하다고 입증되지 않았다.
- 1,940은 non-alias gate-ineligible; alias는 default off.
- 현재 audit matcher는 spec 미준수이며 모든 v2 숫자는 optimistic upper bound.
- D-084 rev2는 아직 승인되지 않았다.

## 10. 요청 형식

각 R1~R8과 Q1~Q14에 대해:

1. **판정** — 찬성/반대/조건부/보류
2. **근거** — 이 문서·rev2·artefact에 기반
3. **다음 단계** — 실행 가능한 1~3개

추가:

- Must-fix 최대 7개, 우선순위 순
- 추가 실험 최대 5개, 예상 비용
- 사실 오류·과장·누락
- 최종 권고 1~2문단

**금지**:

- test 163을 지금 열지 말 것
- P1 데이터 사용 금지
- production `eval/slot_verify.py` 수정 금지
- D-083 strict 결과를 사후에 덮어쓰는 제안 금지
- 1,940을 alias로 eligible하게 만드는 제안 금지
- 2,586을 terminal adapter라는 이유로 승격하는 제안 금지
- unit/alias를 selection baseline에 넣는 제안 금지
