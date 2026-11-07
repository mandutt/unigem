# C5 A1 full train — grounded 실패·압축 drift 분석 (2026-11-07)

## 범위

- checkpoint **1,940** vs **2,586**
- val 161, test 163 미사용
- 분석 스크립트: `runner/c5_a1_error_analysis.py`
- 원시 분석: `reports/provenance/C5_a1/full_2ep/error_analysis_1940_vs_2586.json`

---

## 1. Grounded 실패 유형

### 1,940 — 3건

| id | new | missing | char F1 | 판정 |
|---|---|---|---:|---|
| `REPORT-news_r-03978-00001` | `9시30분` | `오전9시30분` 포함 **7개** | 0.5828 | **verifier format 후보** — 모델이 `오전`을 생략한 같은 시각 |
| `REPORT-news_r-04709-00001` | `18` | **15개** (`18명`은 missing 아님) | 0.5826 | **verifier unit 후보** — 모델은 `18명`을 두 번 보존했고, `18 확진자`에서 추출된 bare `18`만 new |
| `REPORT-news_r-04951-00002` | `2.3%`, `2.2%` | 23개 | 0.6360 | **실제 신규 slot** — 원문에 없는 수치 |

> 2026-11-07 3-AI 검토 후 정정: 초기 표의 `8개`/`18개`는 JSON의 `len(missing)`와 불일치했다. 실제 값은 **7개/15개**이며, `04709`의 `18명`은 missing이 아니라 prediction에 두 번 보존되어 있다. strict `grounded`/`new` 판정은 변경되지 않는다.


### 2,586 — 2건

| id | new | missing | char F1 | 판정 |
|---|---|---|---:|---|
| `REPORT-news_r-02742-00001` | `http://coronamap.site` | `http://coronamap` 포함 6개 | 0.6322 | **verifier URL 후보** — 원문 URL이 `http://coronamap.\n site`로 줄바꿈돼 source가 `http://coronamap`으로 잘림 |
| `REPORT-news_r-04951-00002` | `2.3%`, `2.2%` | 19개 | 0.7000 | **실제 신규 slot** — 1,940과 동일한 hallucination |

### 핵심

- **두 checkpoint 모두 진짜 신규 slot 실패는 `04951` 1건**으로 보인다.
- 1,940의 `03978`(오전 생략), `04709`(18 확진자/bare 18), 2,586의 `02742`(URL 줄바꿈)는 **추출기 정규화 문제**일 가능성이 높다.
- 다만 이것은 **verifier 재검증 없이 gate를 통과시키자는 뜻이 아니다.** D-083의 strict gate 결과는 여전히 `eligible 0`이다.

---

## 2. 2,586의 slot-free 11건

`slot-free` = 모델 요약에 slot이 하나도 없는 문서. `grounded`는 이런 문서를 vacuous하게 통과시킨다.

| 구분 | 문서 수 | 의미 |
|---|---:|---|
| target도 slot-free | 2 | 정상적인 vacuous |
| target slot 1개 | 3 | 경미한 누락 |
| target slot 3~4개 | 6 | **실질 누락** |
| **합계** | **11** | 9/11이 target slot을 누락 |

예:

- `00159` target 1 → 2,586 summary 0
- `00426` target 4 → 0
- `00706` target 4 → 0
- `02741` target 4 → 0
- `03220` target 3 → 0
- `03348` target 4 → 0
- `03915` target 4 → 0

즉 2,586의 slot-free 11건은 대부분 **빈 요약이 아니라 “숫자·날짜를 모두 뺀 요약”**이다. `grounded`가 이를 통과시키는 것은 평가 정의의 한계다.

---

## 3. 1,940 → 2,586 압축 drift

| 지표 | 1,940 | 2,586 | 변화 |
|---|---:|---:|---:|
| char F1 | **0.6823** | 0.6690 | **−0.0133** |
| gen length | 199.5 | 190.3 | −9.2 |
| summary slots/doc | 5.342 | 4.733 | **−0.609** |
| total summary slots | 860 | 762 | **−98** |
| slot preservation | 0.4761 | 0.4188 | **−0.0573** |
| slot-free | 4 | **11** | +7 |
| new slots | 4 | 3 | −1 |
| repeated4 | 0.0514 | **0.0445** | −0.0069 |

### 문서 단위 변화

- slot 감소 문서: **73/161**
- slot 증가 문서: **51/161**
- 동일: **37/161**
- 1,940에는 slot이 있었지만 2,586에서 slot-free가 된 문서: **8건**
- 반대로 2,586에서 slot이 생긴 문서: **1건**

Pearson correlation (161문서):

- `slots_delta` ↔ `F1_delta`: **+0.324**
- `len_delta` ↔ `F1_delta`: **+0.351**
- `slots_delta` ↔ `len_delta`: **+0.519**

즉 **2,586에서 slot과 길이가 줄어든 문서가 F1도 같이 잃는 경향**이 있다.

### 큰 손실 예

| id | slots Δ | F1 Δ | length Δ | preservation Δ |
|---|---:|---:|---:|---:|
| `01082` | **−9** | −0.068 | −68 | −0.500 |
| `04855` | **−8** | −0.207 | −87 | −0.571 |
| `03991` | **−8** | +0.046 | −52 | −0.471 |
| `00476` | −7 | −0.066 | −52 | −0.538 |
| `05207` | −7 | +0.019 | −59 | −0.538 |
| `05292` | −7 | +0.037 | −79 | −0.700 |
| `05517` | −6 | −0.096 | −109 | −0.429 |
| `00644` | −6 | −0.077 | −54 | −0.261 |

### 해석

2,586은 1,940보다 **더 짧고 더 압축된 요약**을 만든다.

- 반복(repeated4)은 개선됐지만 EOS는 두 checkpoint 모두 161/161로 동일하다.
- 그러나 **slot과 길이를 함께 잃는 문서가 늘었고**, F1도 하락했다.
- target의 평균 summary slot은 **5.63/doc**인데, 1,940은 5.34, 2,586은 4.73이다. 2,586은 target보다 **0.9 slot/doc 적다**.
- 따라서 2,586의 “압축 개선”은 **정보 손실을 동반한 over-compression**으로 보는 것이 타당하다.

---

## 4. 결론

1. **Strict D-083 gate 기준으로는 여전히 eligible checkpoint가 없다.** 이 분석은 gate를 사후 변경하지 않는다.
2. **grounded 실패 5건 중 최소 3건은 verifier 정규화 후보**다.
   - URL 내부 줄바꿈
   - `오전` qualifier 생략
   - `18 확진자`에서 추출된 bare `18` (`18명`은 prediction에 보존됨)
3. 2026-11-07 audit 기준: URL+qualifier+generic unit을 적용하면 **1,293 160/161, 2,586 160/161, 1,940 159/161**이다. 1,940의 `04709`는 source에 `18일`과 `18명`이 함께 있어 uniqueness guard에 걸리며, **counter alias**를 별도로 인정해야 160/161이 된다. 어느 경우든 재판정은 **전체 checkpoint 재선택**이어야 한다. 단, **verifier 수정·재판정은 D-084로 사전등록해야 하며, 지금 자동으로 gate를 바꾸지 않는다.**
4. 그래도 **2,586의 slot-free 11건(9건 실질 누락)** 은 별도 품질 문제다. Grounded gate가 이를 잡지 못한다.
5. 1,940이 F1 **0.6823**, slots/doc 5.34, slot-free 4로 2,586보다 낫다. 2,586은 repetition만 더 좋다.
6. test 163과 사람 50건은 여전히 미실행이다.

## 다음 권고

1. **verifier canonicalization audit** — URL 줄바꿈, AM/PM, number+unit 정규화. 기존 gate를 소급 변경하지 말고 새 버전으로 재판정.
2. **사람 50건 rubric** — 1,940/2,586의 slot-free 11건과 `04951` hallucination을 포함해 사실성·누락을 평가.
3. **압축 제어** — 2,586의 over-compression을 줄이는 조건(e.g. length/slot auxiliary)을 별도 실험으로 검토.
4. **D-084 후보** — verifier v2 + human audit + candidate selection을 한 번에 사전등록.

## 산출물

- `reports/provenance/C5_a1/full_2ep/error_analysis_1940_vs_2586.json`
- `reports/provenance/C5_a1/full_2ep/error_analysis_stdout.txt`
- `runner/c5_a1_error_analysis.py`
