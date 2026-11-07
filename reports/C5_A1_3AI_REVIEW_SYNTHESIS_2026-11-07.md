# C5 A1 full train — 3-AI 검토 종합 (2026-11-07)

## 0. 검토 개요

| 항목 | 값 |
|---|---|
| 요청서 | `reports/EXTERNAL_REVIEW_C5_A1_FULLTRAIN_2026-11-07.md` (350줄) |
| 검토 기준 HEAD | **`5694cc7`** (요청서 `ad327ce` + 프롬프트/dispatch `5694cc7`) |
| 데이터 | F5 P0 clean: train 1,293 / val 161 / test 163(A1 미사용) |
| full train | 2 epoch = 2,586 step, **4시간 20분 18초**, exit 0 |
| strict D-083 결과 | **`selected_step: null`**, fallback **pilot300** |
| test 163 | **A1 미사용·봉인** (A0는 D-080에서 사용) |

### 모델·스레드·비용

| 모델 | 추론 | thread | 비용 | input / output | 시간 |
|---|---|---|---:|---:|---:|
| GLM 5.3 Flash | max | `thr_e49bdfc7ce7a422d80a01e7275af4371` | **$0.1629** | 2.06M / 66.8K | 6분 50초 |
| Opus 5.5 | medium | `thr_59b77eb130354b97b2422a29de174391` | **$1.4412** | 0.86M / 31.4K | 5분 59초 |
| Sol 6.1 | xhigh | `thr_9d0309888efe4101a4208ea7640603fe` | **$0.6948** | 1.21M / 24.2K | 7분 37초 |
| **합계** | — | — | **$2.2989** | — | 약 20분 |

- 원문: `docs/hoplite/c5_fulltrain_2026-11-07/review_{GLM,OPUS,SOL}.md`
- 3/3 모두 요청서 전문을 읽고, test 163을 열지 않았고, P1 데이터를 쓰지 않았다고 명시했다.
- Sol은 full source passage가 shallow checkout에 없어 3개 normalization 후보의 **source-context 최종 판정은 보류**했다. 이 한계는 아래 판정에 반영한다.

---

## 1. 한 줄 결론

**3/3 모두 “D-083 strict 결과를 유지하고, verifier v2는 D-084로 사전등록한 뒤 전체 checkpoint를 재선택하며, human 50은 1,940을 primary로 하고, test 163은 계속 봉인한다”에 동의했다.**

- **D-083 strict 결과**: 3/3 “그대로 유지, 사후 gate 변경 금지”
- **pilot300**: 3/3 “strict fallback 유지, 제품 승격 아님”
- **1,940**: 3/3 “exploratory human-review primary”
- **2,586**: 3/3 “secondary compression contrast, terminal adapter라도 승격 금지”
- **test 163**: 3/3 “D-084 + human 50 + candidate freeze 전까지 봉인”
- **verifier v2**: 3/3 “방향은 conditional, blanket equivalence는 반대”

---

## 2. 판정 행렬

| 항목 | GLM 5.3 Flash | Opus 5.5 | Sol 6.1 | 공통 결론 |
|---|---|---|---|---|
| **D1** verifier v2 | 조건부 — bundle 분리 | 조건부 — versioned/audit | 조건부 — 보수적 audit | **3/3 조건부** |
| **D2** candidate | strict pilot + 1,940 exploratory | 조건부 — both | 조건부 — both | **3/3 strict 유지 + 1,940 후보** |
| **D3** human 50 | 동의 — test 전 | 동의 — test 전 | 동의 — test 전 | **3/3 동의** |
| **D4** test 163 | 동의 — 봉인 | 보류 — 봉인 | 보류 — 봉인 | **3/3 봉인** |
| **D5** next | A → B, C defer | A > B > E > C > D | A+E → B → C → D | **A first, B second** |
| **Q1** URL | 찬성 — 좁게 | 찬성 — 좁게 | 조건부 — 좁게 | **URL wrap repair** |
| **Q2** 오전/오후 | 조건부 — 별도 policy | 조건부 — qualifier_dropped | 조건부 — event/scope 확인 | **자동 동등시 금지** |
| **Q3** 18명/18 | 조건부 — uniqueness guard | 조건부 — bare number만 | 조건부 — entity/scope | **unit erasure 금지** |
| **Q4** D-084 | 찬성 — 필수 | 조건부 — 필수 | 찬성 — 필수 | **3/3 D-084 필수** |
| **Q5** fallback | pilot + 1,940 review | both | both | **3/3** |
| **Q6** human primary | **1,940** | **1,940** | **1,940** | **3/3 1,940** |
| **Q7** grounded/G-C5 | 별도 preservation | 별도 + CP | 별도 adequacy | **grounded 재정의 금지** |
| **Q8** 2 epoch | 동의 — 사전등록 | 조건부 — constant LR | 조건부 — 2ep reasonable | **소급 early-stop 금지** |
| **Q9** human 50 | stratified | same 50, 3 systems | 25 targeted + 25 random | **50 unique, blind** |
| **Q10** test | 봉인 | 봉인 | 봉인 | **3/3 봉인** |
| **Q11** priority | A → B, C defer | A > B > E > C > D | A+E → B → C → D | **A then B** |
| **Q12** request errors | 7/15 등 | 7/15 등 | 7/15 등 | **수정 필요** |

---

## 3. 3/3 공통 발견

### 3.1 Strict D-083은 절대 유지

- 3/3 모두 `selection_summary.json`의 `selected_step: null`과 pilot300 fallback을 확인했다.
- “verifier v2가 160/161을 만들 수 있다”는 것은 **가설**이며, D-083 결과를 덮어쓰지 않는다.
- v2 결과는 별도 `selection_v2.json`에 기록하고, v1 결과와 side-by-side로 보고해야 한다.

### 3.2 v2는 “URL 수정 + equivalence policy”를 분리해야 함

- **URL 줄바꿈**은 source-side extraction bug다. `http://coronamap.\n site`가 `http://coronamap`으로 잘려 모델의 정상 URL이 new가 됐다.
- **오전/오후 생략**은 invention이 아니라 **specificity loss**다. `qualifier_dropped`로 별도 기록해야 한다.
- **18명/18**은 `18 확진자`에서 추출된 bare number 문제다. `18명`은 prediction에 두 번 보존되어 있으며, **unit을 전면 무시하면 `18%` vs `18명` 같은 위험한 오탐**이 생긴다.
- 3/3 모두 trailing punctuation은 이미 `_canonical`이 처리한다고 지적했다. 새 normalization으로 등록하면 안 된다.

### 3.3 1,293도 재선택 대상

- 1,293의 grounded 실패는 `02742`(URL)와 `03801`(identifier) 2건이다.
- URL 수정만으로 `02742`가 해소되면 1,293은 **160/161**이 되고, repeated4 0.05866은 0.06을 통과한다.
- 따라서 “1,940과 2,586만 160/161”이라는 서술은 불완전하다. **D-084는 pilot300 + 647 + 1,293 + 1,940 + 2,586 전체를 재선택**해야 한다.
- 647은 URL+time 수정으로 157/161까지 가도 repeated4 0.0684가 남아 부적격이다.

### 3.4 647/1,293의 미분석 실패

- 647: `00114, 00818, 01767, 02742, 03086, 03978` 6건
- 1,293: `02742, 03801` 2건
- 1,940/2,586만 분석한 “진짜 실패는 04951 1건”은 **1,940/2,586 범위로 한정**해야 한다.
- 647/1,293의 나머지 실패는 D-084 audit에서 분류해야 한다.

### 3.5 G-C5와 D-083의 denominator가 다름

- G-C5는 **slot-level**이고, D-083 grounded는 **document-level**이다.
- 1,940: grounded 158/161, new-slot micro **4/860 = 0.465%**.
  - CP 95% upper **≈1.19%** → point는 ≤1%지만 “≤1% 증명”은 아님.
- 2,586: 3/762 = 0.394%, CP upper **≈1.15%**.
- pilot300: 0/837, CP upper **≈0.44%** — G-C5-consistent.
- 161문서에서 grounded 0.99는 “최대 1건 실패”이고, 161/161도 99% population guarantee가 아니다. **gate는 deterministic screen이지 certificate가 아니다.**

### 3.6 2,586의 over-compression

| 지표 | 1,940 | 2,586 | target/reference |
|---|---:|---:|---:|
| F1 | **0.6823** | 0.6690 | — |
| slots/doc | **5.342** | 4.733 | 5.6335 |
| slot preservation | **0.4761** | 0.4188 | **≈0.465** |
| slot-free | 4 | 11 | — |
| repeated4 | 0.0514 | **0.0445** | — |

- target의 implied preservation ≈ **0.465** (=5.6335/12.106).
- 1,940은 target 수준이고, 2,586은 target 아래다.
- 2,586의 slot-free 11건 중 9건은 target slot이 3~4개인데도 0개가 됐다.
- 3/3 모두 2,586을 **over-compression contrast**로 보고, 1,940을 primary로 선택했다.

### 3.7 Val 재사용·길이 confound

- Opus/Sol: val161은 prompt/LR/pilot 선택에 이미 재사용됐고, 16/161 val 문서가 train과 article prefix를 공유한다. F1 절대값은 selection bias를 포함한다.
- pilot300의 generation length는 **248.3**, 1,940은 **199.5**, 2,586은 **190.3**이다. char F1은 길이에 민감하므로 F1만으로 “1,940이 의미적으로 낫다”고 말할 수 없다.
- 1,940 vs 2,586의 paired CI는 nominal이며, checkpoint selection과 article clustering을 반영하지 않는다.

---

## 4. Verifier v2 제안 — D-084 초안 골자

> 아래는 **승인된 D-084가 아니다.** 검토자 3인의 공통 권고를 정리한 초안이며, 코드 수정은 승인 후에만 한다.

### 4.1 URL soft-wrap join — measurement fix

- source와 summary 모두, URL이 **newline 직전에 `.`/`/`/`-`/`_`로 끝나고** 다음 token이 URL continuation인 경우에만 join.
- continuation은 `[A-Za-z0-9][A-Za-z0-9.\-/_%?=&#]*`로 제한. 한글·문장부호는 join하지 않음.
- scheme/host만 lowercase 허용; **path/query case, comma, escape는 보존**.
- join한 원본 span과 repair 기록을 남긴다.
- **금지**: suffix 추측, `www.` 제거, prefix match, URL 전체 fuzzy match.

### 4.2 Time qualifier — equivalence policy

- summary time이 **qualifier 없이** `H시[M분]`이고 source가 같은 `H시[M분]`을 **어떤 qualifier로든** 가지면 grounded로 인정.
- 단, `qualifier_dropped`에 기록하고 **specificity loss**로 별도 보고.
- summary가 `오전/오후`를 **새로 붙이면** new로 실패.
- `오전 9시` vs `오후 9시`는 불일치; 12h↔24h 변환은 v2에서 금지.

### 4.3 Number/unit — equivalence policy

- summary number에 **unit이 없고**, source에 **동일 numeric value**의 number slot이 있으면 grounded로 인정.
- `unit_dropped`에 기록.
- summary number에 unit이 있으면 **value+unit exact match**.
- `18%` vs `18명`, `18건` vs `18일`, 반올림, `만/억` 확장, `%`↔`퍼센트`는 금지.
- `18 확진자` 같은 head noun은 **entity/scope가 명확할 때만** person-count alias로 인정; 불명확하면 manual adjudication.

### 4.4 버전·감사·재선택

1. `verify_summary_v2` + `verifier_version`을 별도로 두고 v1을 덮어쓰지 않는다.
2. **383개 excluded pair** 등 independent P0 audit set에서 v1→v2로 **flip된 모든 건을 사람이 확인**한다. acceptance는 “human-confirmed false accept 0”.
3. v2 rule을 code/tests/SHA로 **freeze한 뒤** val161을 재채점한다.
4. pilot300 + 647 + 1,293 + 1,940 + 2,586 전체를 재선택한다.
5. 결과는 `val-reused / exploratory`로 표기하고, D-083 strict 결과와 side-by-side로 둔다.

### 4.5 Gate 보강

- grounded **0.99는 유지**한다. 낮추지 않는다.
- `grounded_nonvacuous`, `slot_free`, `slot_preservation`을 항상 같이 보고.
- coverage/preservation은 **별도 adequacy criterion**으로 추가:
  - target implied preservation 대비 relative criterion
  - slot-free with target ≥3 slots
  - material omission / key-slot recall
- doc-level과 slot-level denominator를 분리하고 CP 95% + INCONCLUSIVE를 보고한다.

---

## 5. Human 50 / candidate / test

### 5.1 Candidate 상태

| system | strict D-083 | exploratory human | product |
|---|---|---|---|
| **pilot300** | **fallback PASS** | control arm | **아님** |
| **1,940** | ineligible (grounded 158/161) | **primary** | **아님** |
| 2,586 | ineligible (grounded 159/161) | secondary compression contrast | **아님** |

- 3/3 모두 **1,940 primary**.
- 1,940: F1 0.6823, slots/doc 5.34, preservation 0.476, slot-free 4.
- 2,586: repetition 0.0445, terminal adapter이나 slot-free 11, preservation 0.419, F1 0.6690.

### 5.2 Human 50 공통 골격

- **같은 50 unique val docs**에 pilot300/1,940/2,586을 blind, randomized order로 평가.
- 포함:
  - `04951` genuine negative control
  - `03978`, `04709`, `02742` normalization candidates
  - 2,586 slot-free 11건
  - top slot-loss docs
  - lowest-F1 decile
  - longest outputs
  - random remainder (seed 고정)
- Rubric: fabricated entity/number, wrong unit/qualifier, negation/attribution, material omission, fluency, memory utility.
- 두 명의 rater, 최소 random 20건은 agreement 보고.
- targeted/risk stratum과 random stratum을 **분리 보고**하고, naive 50-row bootstrap을 쓰지 않는다.

### 5.3 Test 163

**3/3 봉인.** 해제 조건:

```text
D-084 승인
→ verifier v2 audit + full re-selection
→ human 50 완료
→ single candidate adapter/hash/decoder/gate freeze
→ A1 test 163 1회
→ 이후 retuning 금지
```

A0가 이미 test 163을 사용했으므로 “project 전체 미사용”이 아니라 **A1 미사용**으로 표기한다.

---

## 6. 공통 Must-fix

1. **D-083 strict 기록 보존** — `selected_step: null`, pilot300 fallback. v2 결과로 덮어쓰지 않는다.
2. **D-084 없이 v2 재채점 금지** — URL fix / qualifier / unit을 별도 clause로 사전등록한다.
3. **versioned verifier + independent audit** — 383 excluded P0, flip 전건 human check, forbidden generalization tests.
4. **전체 checkpoint 재선택** — pilot300, 647, 1,293, 1,940, 2,586. **1,293도 160/161이 될 수 있다.**
5. **647/1,293 미분석 실패 분류** — `00114, 00818, 01767, 03086, 03801` 등.
6. **Human 50 blind, 1,940 primary, pilot300 control, 2,586 contrast** — test 전에 완료.
7. **Test 163 firewall** — D-084 + human + candidate freeze 전까지 봉인, A1 1회만.
8. **보고 정합성 수정** — 03978 missing 7(not 8), 04709 missing 15(not 18), `18명` preserved; 647 EOS 160/161은 pass; CP/denominator/nonvacuous 병기.

---

## 7. 이견·미합의

| 쟁점 | 차이 | 종합 판단 |
|---|---|---|
| D5 순서 | GLM A→B, Opus A>B>E>C>D, Sol A+E→B→C→D | **A와 E(D-084 설계)를 먼저, B human, C/D는 후속** |
| Q9 표본 | GLM/Opus는 50 unique 3-system, Sol은 25 targeted+25 random | **50 unique, targeted/risk + random 분리 보고**가 공통 상위호환 |
| Q2 qualifier | GLM/Opus는 guard부 매칭 허용, Sol은 event/scope 확인 강조 | **자동 동등시 금지, `qualifier_dropped` + human adjudication** |
| Q3 unit | 공통적으로 unit erasure 반대; Sol이 entity/scope 조건을 더 엄격히 | **bare number only + uniqueness/entity guard** |
| Q7 preservation | GLM relative target−0.05, Opus pilot non-inferiority, Sol adequacy | **절대 gate를 바로 만들지 말고 target/pilot baseline + human rubric** |
| C seed 43 | GLM/Opus는 후속, Sol은 replication 먼저 | **C는 D-084/human 이후, D보다 먼저** |

---

## 8. 요청서·오류 분석 정정

| 항목 | 기존 | 정정 |
|---|---|---|
| `03978` missing | 8개 | **7개** |
| `04709` missing | 18개, `18명` 포함 | **15개**, `18명`은 missing 아님 |
| `04709` prediction | `18` one mention | **`18명` 두 번 보존**, `18 확진자`의 bare `18`만 new |
| trailing punctuation | v2 신규 작업 | **_canonical이 이미 처리** |
| 1,293 | v2 side effect 미기재 | **URL fix로 160/161 가능**, full re-selection 필수 |
| 647 EOS | gate fail로 서술 | **160/161 = 0.9938, EOS 기준 통과**; grounded/rep4가 fail |
| “3 of 5” | 전체처럼 서술 | **1,940/2,586 범위**; 647/1,293 미분석 |
| `04951` | “hallucination” | **source-unsupported extrinsic content**; real-world-looking, human rubric에서 별도 분류 |

---

## 9. 다음 결정

### 즉시 가능 (승인 시)

- **A. verifier v2 audit + D-084 초안**: 1~2시간 CPU + 1~3시간 source adjudication. 코드 수정은 D-084 초안 승인 후.
- **B. human 50 protocol/freeze**: 12~20 person-hours. 아직 평가 실행 전.

### 승인 후

- **C. seed 43 full train**: 4시간 20분 + eval. D-084/human 이후.
- **D. over-compression arm**: 4~5시간/run. 1.5-epoch stop 또는 LR decay 중 하나만.
- **E. fresh P0 confirmatory set**: 299 independent zero-failure docs는 99% lower bound의 best-case minimum; test 163만으로 99% guarantee를 주장하지 않는다.

### 금지

- test 163 즉시 개방
- verifier v2를 사후에 적용해 D-083을 pass로 덮어쓰기
- 2,586을 terminal adapter라는 이유로 승격
- `grounded`를 omission gate로 재정의
- 1,940/2,586만 재선택하고 1,293을 누락

---

## 10. 산출물

- 원문: `docs/hoplite/c5_fulltrain_2026-11-07/review_GLM.md`
- 원문: `docs/hoplite/c5_fulltrain_2026-11-07/review_OPUS.md`
- 원문: `docs/hoplite/c5_fulltrain_2026-11-07/review_SOL.md`
- 요청서: `reports/EXTERNAL_REVIEW_C5_A1_FULLTRAIN_2026-11-07.md`
- full train: `reports/C5_A1_full_train_2ep_2026-11-07.md`
- 오류 분석: `reports/C5_A1_error_analysis_2026-11-07.md`
- strict selection: `reports/provenance/C5_a1/full_2ep/selection_summary.json`
- 비용: **$2.2989** (GLM $0.1629 / Opus $1.4412 / Sol $0.6948)

---

## 11. 후속 audit 정정 (2026-11-07)

D-084 초안 작성 중 `runner/c5_a1_verifier_v2_audit.py`로 저장된 val 예측을 재검증했다. 이 결과는 위 3-AI 검토의 “conditional 160/161”을 다음과 같이 구체화한다.

| system | V1 | V2 generic | V2 + counter alias |
|---|---:|---:|---:|
| pilot300 | 161/161 | 161/161 | 161/161 |
| 647 | 155/161 | 158/161 | 158/161 |
| **1,293** | 159/161 | **160/161** | 160/161 |
| **1,940** | 158/161 | **159/161** | **160/161** |
| **2,586** | 159/161 | **160/161** | 160/161 |

- **generic v2**(URL + qualifier + uniqueness-guarded number)만 적용하면 **1,940은 159/161**이며, 160/161이 되려면 `18 확진자` **counter alias**가 필요하다.
- generic v2에서 eligible 후보의 max F1은 **2,586(0.6690)**, alias를 추가하면 **1,940(0.6823)**이다. 즉 **selection 결과가 alias policy에 의존**한다.
- corpus collision: URL wrap **3/1,617**, qualifier collision **7/1,617**, numeric unit collision **902/1,617 (55.8%)**.
- **target audit**: excluded 383쌍 중 v2가 grounded로 뒤집은 5건(`00291`, `01844`, `03253`, `04791`, `05019`)이 있어 human adjudication 필요; clean 1,617쌍은 v1/v2 차이 0.
- 기존 v1 URL canonicalizer는 path/query case와 comma를 잃는 **false accept**가 있다 (`Case?key=A,B` vs `case?key=ab`가 grounded).
- raw: `reports/provenance/C5_a1/full_2ep/verifier_v2_audit.json`
- audit: `reports/C5_A1_verifier_v2_audit_2026-11-07.md`
- D-084 초안: `docs/D-084_verifier_v2_draft_2026-11-07.md`

**D-083 strict 결과는 여전히 `selected_step: null`, pilot300 fallback이다.**
