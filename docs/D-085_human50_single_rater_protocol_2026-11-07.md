# D-085 — Human 50 single-rater protocol (v1.0.0)

**상태:** `FROZEN` — human rating 시작 전 사전등록  
**날짜:** 2026-11-07  
**대상:** C5 F5 abstractive summary, A1 full-train checkpoints  
**목적:** 2,586 vs pilot300의 human adequacy를 single-rater 조건에서 비교하고, 2,586을 provisional nominee로 유지할지 판정

> 이 문서는 human rating 결과를 보기 전에 고정한다. 평가 시작 후에는 primary contrast, 표본, rubric, decision rule을 변경하지 않는다. 변경이 필요하면 별도 `amendment`를 만들고 원래 primary analysis와 분리한다.

---

## 0. 한 줄 요약

**val 161에서 고유 문서 50개**를 뽑아 **4개 arm**(pilot300, 1,293, 1,940, 2,586)을 **1명**이 평가한다.  
primary **200 ratings** + repeat **40 ratings** = **240 ratings**.  
반복 평가는 **7일 이상 간격**으로 하고, **intra-rater ICC ≥ 0.70**을 통과해야 한다.  
실패 또는 INCONCLUSIVE이면 **pilot300 fallback, no approved candidate, test 163 sealed**다.

---

## 1. 왜 single-rater인가

현재 이 프로젝트에서 human rating에 참여할 수 있는 사람은 **1명**이다. 따라서 원래 설계한 “2인 독립 평가”는 실행할 수 없다.

2인 평가를 1인으로 바꾸면 다음이 달라진다.

| 항목 | 2인 설계 | 1인 설계 |
|---|---|---|
| 평가자 | 2명 | **1명** |
| primary ratings | 400 | **200** |
| repeat ratings | — | **40** |
| inter-rater reliability | ICC/κ 가능 | **불가능** |
| intra-rater reliability | — | **가능** |
| 결과의 일반화 | 평가자 모집단에 어느 정도 일반화 | **이 평가자 1인에게 한정** |
| 판정 단위 | 문서 50개 paired | **문서 50개 paired** |

**중요:** 2인 평가가 n=100이 되는 것은 아니다. 판정 단위는 문서 50개다. 1인 평가에서도 50개 paired comparison은 유지되지만, 평가자 1명의 측정 오차와 편향은 별도로 다룬다.

---

## 2. 표본

### 2.1 전체

- 모집단: **val 161**
- 표본: **고유 문서 50개**
- **targeted 20 + random 30**
- test 163: **사용하지 않음**

### 2.2 targeted 20 — 결정론적 규칙

targeted는 “hard case 진단”을 위해 의도적으로 뽑는다. 선택 규칙은 다음과 같고, 결과는 manifest에 고정한다.

1. **known residual 6건**
   - `02742` — URL wrap new pass
   - `03978` — time-type residual
   - `04709` — bare `18` unit
   - `04951-00002` — genuine negative control
   - `01518` — source URL truncated
   - `03801` — 1,293 identifier residual

2. **2,586 slot-free 6건**
   - 2,586에서 summary slot이 0인 문서 중 아직 선택되지 않은 것
   - ID 오름차순으로 6건

3. **2,586 low-preservation 4건**
   - slot-free가 아닌 문서 중 `a_preservation`이 낮은 순서
   - 값이 같으면 ID 오름차순
   - 4건

4. **647 residual 2건**
   - 647에서 `a_grounded=false`인 문서 중 아직 선택되지 않은 것
   - ID 오름차순 2건

5. **seeded fill**
   - 위 단계에서 20건이 안 되면 seed `20261107`로 남은 val에서 채움

실제 20개 ID는 `reports/provenance/C5_human50/manifest.json`의 `targeted` 배열에 고정되어 있다.

### 2.3 random 30

- targeted 20을 제외한 val 141개에서
- seed **20261107**로 30개를 무작위 추출
- 순서도 manifest에 고정

### 2.4 repeat 10

- targeted에서 **6건**: known residual 4건 + 2,586 slot-free 2건
- random 30에서 **4건**: random30의 첫 4건
- 총 **10개 문서 × 4 arm = 40 ratings**
- primary 200에는 포함하지 않고, **오직 reliability 추정에만 사용**

### 2.5 train-prefix-sharing

val 161 중 **16건**은 train prefix와 겹치는 문서다. 이 16건은 삭제하지 않는다.

- manifest에서 해당 ID를 flag로 표시한다.
- primary 결과와 **16건 제외 sensitivity**를 모두 보고한다.
- sensitivity gate: 16건을 제외한 뒤에도
  - adequacy lower 95% bound **≥ −0.25**
  - critical unsupported upper 95% bound **< +0.05**
  - critical omission upper 95% bound **< +0.05**
  를 만족해야 한다.
- 하나라도 실패하면 **INCONCLUSIVE**로 처리한다.

---

## 3. Arm과 블라인드

### 3.1 Arm

| arm | 설명 |
|---|---|
| `pilot300` | D-083 fallback; 비교 기준 |
| `1293` | full-train checkpoint; sensitivity |
| `1940` | full-train checkpoint; exploratory (084a gate-ineligible) |
| `2586` | full-train checkpoint; provisional nominee |

### 3.2 블라인드

평가자는 다음을 보지 않는다.

- 모델 이름, checkpoint step, arm 이름
- char F1, grounded, EOS, repeated4
- 다른 평가자의 점수
- 이전 pass의 점수

각 문서마다 4개 요약의 **순서를 무작위화**한다. 순서는 manifest의 `arm_order`에 고정한다.

완전한 맹검은 불가능하다. 평가자는 프로젝트 맥락을 알고 있다. 따라서 “**arm identity와 성능 지표를 모르는 blinded single-rater**”로 한정한다.

---

## 4. Rating 절차

### 4.1 Primary pass — 200 ratings

- 50개 문서 × 4 arm = 200
- 5 sessions × 10 documents = **40 ratings/session**
- 한 세션은 40 ratings를 넘지 않는다.
- 세션 내에서도 arm 순서는 manifest를 따른다.
- 각 rating 후 `adequacy`와 flags를 입력한다.
- 4개 요약을 모두 평가한 뒤 다음 문서로 넘어간다.
- 세션 사이에는 최소 30분 휴식; 가능하면 하루 2세션 이하.

### 4.2 Repeat pass — 40 ratings

- primary 10개 문서 × 4 arm = 40
- **7일 이상 간격**
- 첫 pass의 점수를 보지 않는다.
- arm 순서는 다시 무작위화한다. 단, manifest의 repeat order를 따른다.
- 2 sessions × 5 documents = **20 ratings/session**
- 목적: **intra-rater ICC / weighted kappa** 추정
- repeat 점수는 primary 분석에 섞지 않는다.

### 4.3 입력 schema

```json
{
  "doc_id": "REPORT-news_r-...",
  "arm": "pilot300|1293|1940|2586",
  "pass": 1,
  "adequacy": 0,
  "critical_unsupported": 0,
  "critical_omission": 0,
  "wrong_unit_qualifier": 0,
  "entity_relation": 0,
  "fluency": 1,
  "utility": 1,
  "notes": ""
}
```

- `adequacy`: 0~4
- `critical_unsupported`, `critical_omission`, `wrong_unit_qualifier`, `entity_relation`: 0/1
- `fluency`, `utility`: 1~5
- `notes`: 선택
- 모든 field는 필수다. 빈 값은 허용하지 않는다.

---

## 5. Rubric

| 항목 | 정의 | 척도 |
|---|---|---|
| **adequacy** | 원문의 핵심 의미를 얼마나 보존했는가 | 0~4 |
| **critical_unsupported** | 원문에 없는 중요한 주장·수치·관계를 추가했는가 | 0/1 |
| **critical_omission** | 의사결정에 중요한 사실을 빠뜨렸는가 | 0/1 |
| **wrong_unit_qualifier** | 단위·시간·조건 qualifier를 틀리게 썼는가 | 0/1 |
| **entity_relation** | 사람·기관·사건의 관계를 틀리게 썼는가 | 0/1 |
| **fluency** | 한국어 문장으로 자연스러운가 | 1~5 |
| **utility** | 실제 읽고 판단하는 데 유용한가 | 1~5 |

### adequacy anchor

| 점수 | 기준 |
|---:|---|
| 4 | 핵심 사실·관계·qualifier를 거의 모두 보존; 요약으로 충분 |
| 3 | 핵심은 보존; 경미한 생략/표현 손실 |
| 2 | 핵심 일부 보존; 중요한 생략 또는 약한 왜곡 |
| 1 | 핵심 대부분 손실; 원문과 다른 인상 |
| 0 | 요약으로 기능하지 않음; 빈 출력/반복/심한 hallucination |

### critical 기준

- **critical_unsupported**: 원문에 없는 핵심 수치, 인과, 정책, 신원, 날짜·시간을 추가한 경우
- **critical_omission**: 원문의 핵심 결정·이유·대상·기한·수치를 빠뜨려 요약의 결론이 달라지는 경우
- **wrong_unit_qualifier**: `18명`을 `18`로, `오전`을 `오후`로, `2020`을 `2021`로 바꾼 경우
- **entity_relation**: 누가 무엇을 했는지, 어느 기관·지역·대상인지 틀린 경우

---

## 6. Decision rule — 사전등록

Primary contrast: **2,586 − pilot300**, paired by document, primary pass only.

### 6.1 통과 조건

다음을 **모두** 만족해야 한다.

1. **Adequacy non-inferiority**
   - 50개 문서의 paired adequacy difference 평균의 **95% bootstrap lower bound ≥ −0.25**
2. **Critical unsupported non-inferiority**
   - `critical_unsupported` 비율 차이(2,586 − pilot300)의 **95% bootstrap upper bound < +0.05**
3. **Critical omission non-inferiority**
   - `critical_omission` 비율 차이의 **95% bootstrap upper bound < +0.05**
4. **Intra-rater reliability**
   - repeat 10문서 × 4 arm의 adequacy **ICC(2,1) ≥ 0.70**
   - adequacy **quadratic weighted kappa ≥ 0.60**

### 6.2 판정

| 조건 | 결과 |
|---|---|
| 1~4 모두 통과 | **SINGLE_RATER_SUPPORTED** |
| 1~3 중 하나 실패 | **FAIL** |
| 1~3 통과, 4 실패 | **INCONCLUSIVE** |
| 데이터 누락/평가 미완료 | **INCONCLUSIVE** |
| 16 train-prefix 제외 sensitivity가 반대 방향 | **INCONCLUSIVE** |

### 6.3 no-candidate branch

`FAIL` 또는 `INCONCLUSIVE`이면:

- `NO_APPROVED_CANDIDATE`
- **pilot300 fallback**
- test 163 **sealed**
- 1,293으로 자동 변경하지 않음
- 1,940을 exploratory quality 이유로 승격하지 않음

`SINGLE_RATER_SUPPORTED`이면:

- candidate status는 **PROVISIONAL_NOMINEE**
- `approval_status`는 사용자 별도 승인 전까지 **NOT_APPROVED**
- **2인 독립 평가를 통과했다고 표기하지 않음**
- `evidence_level = SINGLE_RATER`

---

## 7. 통계 분석

### 7.1 Primary

- 분석 단위: 문서 50개
- 각 문서에서 `2586`과 `pilot300`의 adequacy 차이를 계산
- paired mean difference
- **10,000 bootstrap resamples**, seed `20261107`, percentile 95% CI
- `critical_unsupported`, `critical_omission`은 문서별 0/1 차이의 비율 차이로 계산
- 동일한 doc-level bootstrap을 사용

### 7.2 Reliability

- repeat 10문서 × 4 arm = 40 paired ratings (pass 1 vs pass 2)
- **ICC(2,1)** — two-way random effects, single measurement
- **quadratic weighted kappa** — adequacy 0~4
- `critical_unsupported`/`critical_omission`은 simple agreement와 Cohen's kappa를 보조로 보고

### 7.3 Secondary / exploratory

- `2586 − 1293` = secondary sensitivity
- `1940 − pilot300` / `1940 − 2586` = exploratory
- `fluency`, `utility`, `wrong_unit_qualifier`, `entity_relation` = descriptive
- **secondary/exploratory가 primary를 대체하지 않는다.**

### 7.4 Missing data

- primary 200 ratings가 모두 있어야 한다.
- repeat 40 ratings가 모두 있어야 한다.
- 누락 시 imputation하지 않고 **INCONCLUSIVE**.
- 평가 중단/재개는 세션 단위로 기록한다.

### 7.5 No peeking

- ratings가 모두 lock되기 전에는 primary contrast를 계산하지 않는다.
- 중간 점수로 arm을 바꾸거나 표본을 바꾸지 않는다.
- 분석가가 중간 결과를 보더라도 평가자에게 피드백하지 않는다.

---

## 8. 표본 동결과 hash

- manifest: `reports/provenance/C5_human50/manifest.json`
- protocol: 이 문서
- analysis: `runner/c5_human50_single_rater_analysis.py`
- freeze hash: `reports/provenance/C5_human50/freeze.sha256`

manifest에는 다음이 고정되어 있다.

- 50개 ID와 targeted/random 구분
- 10개 repeat ID
- 5 primary sessions / 2 repeat sessions
- 각 문서의 arm order
- 각 문서의 source/target SHA256
- seed와 selection rule
- decision rule

평가 시작 전에 위 파일들의 SHA256을 기록한다. 평가 시작 후 변경은 **amendment**로만 가능하다.

---

## 9. 한계

1. **inter-rater reliability 없음** — “다른 사람도 같은 판단을 하는가”는 이 실험으로 알 수 없다.
2. **single-rater generalization 없음** — 결과는 이 평가자 1인의 판단이다.
3. **repeat는 independence를 대체하지 않음** — 7일 간격이 기억을 완전히 제거하지 못한다.
4. **50문서는 val 전체의 prevalence-representative sample이 아님** — targeted 20이 포함되어 있다.
5. **adequacy −0.25 margin은 non-inferiority margin** — “품질이 같다”는 뜻이 아니라 “실질적으로 열등하지 않다”는 뜻이다.
6. **critical margin +0.05는 50문서에서 2.5문서 수준** — 매우 작은 추가 위험도 민감하게 잡는다.
7. **test 163은 이 protocol로 열지 않는다.**

---

## 10. 산출물과 다음 단계

### 이번에 고정하는 것

- 이 protocol
- `reports/provenance/C5_human50/manifest.json`
- `runner/c5_human50_single_rater_analysis.py`
- `reports/provenance/C5_human50/freeze.sha256`

### 아직 하지 않는 것

- human rating 수집
- test 163 평가
- 084b diagnostics 결과를 protocol에 반영
- candidate approval

### 다음

1. rating sheet 생성 및 평가 세션 시작
2. primary 200 + repeat 40 수집
3. ratings lock + hash
4. `c5_human50_single_rater_analysis.py` 실행
5. 결과에 따라 `SINGLE_RATER_SUPPORTED` / `FAIL` / `INCONCLUSIVE`
6. 별도 승인 전까지 candidate approval·test 163 금지
