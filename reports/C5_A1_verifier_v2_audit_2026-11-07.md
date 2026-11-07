# C5 A1 — verifier v2 candidate audit (2026-11-07)

## 0. 범위

- **읽기 전용 audit**. `eval/slot_verify.py`는 수정하지 않았다.
- 대상: P0 `f5_pairs_v3_clean.jsonl` 1,617쌍 + A1 val 161 예측
- test 163: **미사용**
- audit script: `runner/c5_a1_verifier_v2_audit.py`
- raw: `reports/provenance/C5_a1/full_2ep/verifier_v2_audit.json`
- **D-084 공식 결정 아님**; production verifier v2도 아직 구현하지 않았다.

## 1. Corpus-level rule exposure

| 항목 | 값 |
|---|---:|
| clean | **1,617** |
| excluded (2,000 − clean) | **383** |
| URL soft-wrap 문서 | **3 / 1,617** |
| URL soft-wrap 발생 | **3** |
| qualifier collision 문서 (`H시M분`에 오전/오후 또는 bare가 공존) | **7 / 1,617** |
| numeric unit collision 문서 (같은 숫자값이 서로 다른 unit로 등장) | **902 / 1,617 (55.8%)** |

URL wrap 문서:

- `REPORT-news_r-02742-00001` → `http://coronamap.site`
- `REPORT-news_r-03992-00001` → `http://fine.fss.` (문맥 확인 필요)
- `REPORT-news_r-04909-00001` → `https://coronamap.site/`

**해석**:
- URL wrap은 드물어 measurement fix로 좁게 적용할 수 있다.
- qualifier collision은 7건뿐이므로 uniqueness guard가 필수다.
- **numeric unit collision이 902건(55.8%)** 이므로 “unit을 무시한 number 매칭”은 광범위한 false accept 위험이 있다. `18명`/`18%`/`18일`을 자동 동일시하면 안 된다.

### 1.1 Target-side audit (false-accept 후보)

| subset | n | V1 grounded | V2 generic grounded | V1→V2 flip |
|---|---:|---:|---:|---:|
| **excluded pairs** (v1 clean filter에서 제외) | 383 | 0 | **5** | **5** |
| clean pairs | 1,617 | 1,617 | 1,617 | 0 |

excluded pair에서 v2가 grounded로 뒤집힌 5건:

```text
REPORT-news_r-00291-00002  v1_new=('2020',)
REPORT-news_r-01844-00001  v1_new=('2021',)
REPORT-news_r-03253-00001  v1_new=('404',)
REPORT-news_r-04791-00001  v1_new=('20',)
REPORT-news_r-05019-00001  v1_new=('5000', '200')
```

이 5건은 **v2 false accept 후보**다. 반드시 human adjudication 대상이며, “v2는 clean target을 바꾸지 않았다”는 것만으로 정당화하면 안 된다. clean 1,617에서는 v1/v2 차이가 0이므로, v2의 영향은 **rejected target 경계**와 val 예측에 집중된다.

## 2. V1 vs candidate v2 — val 161

> 아래 v2는 **audit matcher** 결과다. production v2가 아니다. `counter_alias`는 `18 확진자`처럼 summary에 bare number가 있고 바로 뒤에 `확진자`가 있는 경우만 별도 허용한 exploratory variant다.

| system | V1 grounded | V2 generic grounded | V2 generic 신규 실패 | V2 + counter alias grounded | V2 alias 신규 실패 |
|---|---:|---:|---|---:|---|
| pilot300 | **161/161** | **161/161** | 없음 | **161/161** | 없음 |
| 647 | 155/161 | **158/161** | `00114`, `01767`, `03086` | 158/161 | 동일 |
| 1,293 | 159/161 | **160/161** | `03801` | 160/161 | 동일 |
| **1,940** | 158/161 | **159/161** | **`04709`, `04951`** | **160/161** | `04951` |
| 2,586 | 159/161 | **160/161** | `04951` | 160/161 | 동일 |

### 핵심

- **URL repair만으로 1,293과 2,586이 160/161**이 된다.
- **1,940은 generic unit rule로는 159/161**이다. `03978`은 해소되지만 `04709`는 source에 `18일`과 `18명`이 함께 있어 **uniqueness guard에 걸린다**.
- `counter_alias`를 적용해야 1,940이 160/161이 된다. 이 alias는 자동 규칙이 아니라 **entity/scope adjudication**이 필요하다.
- `04951`의 `2.3%`, `2.2%`는 v2에서도 ** genuine negative control**로 남는다. 이것이 없어지면 audit가 잘못된 것이다.
- 647은 158/161까지 가도 repeated4 0.0684로 gate 미달이다.

## 3. D-084 selection sensitivity

D-083 gate를 그대로 적용하고 v2 결과만 사용하면:

| 정책 | grounded 통과 후보 | max F1 후보 | 비고 |
|---|---|---|---|
| **generic v2** | pilot300(161), 1,293(160), 2,586(160) | **2,586** (0.6690) | 1,940은 159로 부적격 |
| **generic + counter alias** | + 1,940(160) | **1,940** (0.6823) | alias의 human adjudication 필요 |
| **no unit rule** | pilot300, 1,293(160), 2,586(160) | **2,586** | 03978/URL만 수정 |

**이것이 D-084의 핵심 쟁점이다.** “v2가 1,940을 통과시킨다”는 결과는 **unit alias 정책에 의존**하며, 그 정책을 먼저 정하지 않고 160/161을 목표로 삼으면 post-hoc gate가 된다.

## 4. 기존 verifier false equivalence

현재 `slot_verify.py`의 `_canonical`은 URL 전체를 lowercase하고 comma를 제거한다.

```text
source: https://example.com/Case?key=A,B
summary: https://example.com/case?key=ab
→ new = (), missing = (), grounded = True
```

이것은 **URL path/query case와 comma를 잃는 false accept**다. v2 URL repair는 이 문제를 악화시키지 않도록:

- scheme/host만 lowercase
- path/query case 보존
- comma/escape 보존
- URL 내부 newline만 join
- trailing sentence punctuation은 별도 처리

를 명시해야 한다.

## 5. Rule audit 결론

1. **URL wrap join**은 measurement fix로 채택 가능하나, source와 summary **양쪽**에 적용해야 한다. 1,940 prediction도 `http://coronamap.\nsite`를 포함하므로 한쪽만 고치면 새로운 false new가 생긴다.
2. **qualifier drop**은 7개 collision 문서 때문에 uniqueness guard 없이는 위험하다. `qualifier_dropped` reporting이 필수다.
3. **unit rule**은 902개 numeric collision 문서 때문에 **기본 uniqueness guard**가 필요하다. 그 결과 1,940은 generic v2에서 159/161이다.
4. **counter alias**는 1,940을 160/161로 만들 수 있지만, `18일`/`18명`이 같이 있는 문서에서 “사람 수”를 문맥으로 확정해야 한다. human adjudication 없이는 자동 채택 금지.
5. **1,293과 2,586은 generic v2에서 160/161**이다. 3-AI가 지적한 “1,293 side effect”가 실측으로 확인됐다.
6. **test 163은 계속 봉인**한다.

## 6. 권고

- D-084에서는 **generic v2**를 baseline으로 두고, `counter_alias`를 **별도 clause**로 분리한다.
- D-084 승인 전에는 production `slot_verify.py`를 수정하지 않는다.
- audit set 383건 전체에서 v1→v2 flip을 사람이 확인하고, **human-confirmed false accept 0**을 acceptance로 둔다.
- selection v2는 **generic 결과와 alias 결과를 모두 별도 표로** 보고하고, 어느 쪽도 제품 승격으로 부르지 않는다.
