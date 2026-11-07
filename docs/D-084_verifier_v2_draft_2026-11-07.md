# D-084 초안 — verifier v2 audit과 A1 재선택

> **상태: DRAFT / 미승인.**  
> 이 문서는 사용자 승인을 받은 초안이며, 공식 결정이 아니다. `docs/decisions.md`에 D-084로 등록하지 않는다.  
> `eval/slot_verify.py`와 production selection은 아직 수정하지 않았다. D-083 strict 결과는 그대로다.

- 작성일: 2026-11-07
- 대상: C5/F5 A1 full train의 grounded gate 재판정
- 데이터: P0 clean 1,617쌍, val 161, test 163 미사용
- 근거: `reports/C5_A1_verifier_v2_audit_2026-11-07.md`, 3-AI 종합 `reports/C5_A1_3AI_REVIEW_SYNTHESIS_2026-11-07.md`

---

## 1. 문제

D-083 strict gate는 full train 4 checkpoint 모두 eligible하지 않다고 판정했다.

- 1,940: grounded 158/161, F1 0.6823
- 2,586: grounded 159/161, F1 0.6690
- fallback: pilot300 161/161, F1 0.6576

3-AI 검토에서 grounded 실패의 일부가 verifier surface matching artifact일 가능성이 확인됐다.

- URL internal newline
- `오전/오후` 생략
- `18명`/`18 확진자` unit
- 실제 negative control: `04951`의 `2.3%`, `2.2%`

그러나 이를 사후에 적용해 D-083을 통과시키면 gate 변경이다. D-084는 **measurement fix와 equivalence policy를 분리해 사전등록**하고, 전체 checkpoint를 재선택하는 절차를 정의한다.

---

## 2. Audit 결과 (초안 작성 시점)

### 2.1 V1 vs candidate v2

| system | V1 grounded | V2 generic | V2 + counter alias | V2 generic 실패 |
|---|---:|---:|---:|---|
| pilot300 | 161/161 | 161/161 | 161/161 | — |
| 647 | 155/161 | 158/161 | 158/161 | 00114, 01767, 03086 |
| 1,293 | 159/161 | **160/161** | 160/161 | 03801 |
| **1,940** | 158/161 | **159/161** | **160/161** | 04709, 04951 |
| 2,586 | 159/161 | **160/161** | 160/161 | 04951 |

### 2.2 Rule exposure

- URL soft-wrap: **3/1,617**
- qualifier collision: **7/1,617**
- numeric unit collision: **902/1,617 (55.8%)**
- excluded audit pool: **383**
- excluded target v1→v2 grounded flip: **5/383** (`00291`, `01844`, `03253`, `04791`, `05019`) — **false-accept 후보, human adjudication 필수**
- clean target v1→v2 change: **0/1,617**

### 2.3 핵심

1. **1,293과 2,586은 generic v2에서 160/161**이 된다.
2. **1,940은 generic v2에서 159/161**이며, `04709` 때문에 160이 되지 않는다.
3. 1,940을 160으로 만들려면 `18 확진자` counter alias가 필요하다. 이것은 **semantic adjudication**이지 단순 normalization이 아니다.
4. generic v2에서 eligible 후보의 max F1은 **2,586**(0.6690), alias를 추가하면 **1,940**(0.6823)이다. 즉 **selection 결과가 D-084 policy에 의존**한다.
5. `04951`은 v2에서도 남는 genuine negative control이다.
6. 647은 158/161이어도 repeated4 0.0684로 여전히 부적격이다.

---

## 3. Scope

### 포함

- verifier v2 rule 명세와 audit
- 383 excluded P0 pair의 rule collision·flip 조사
- val 161의 v1/v2 side-by-side 재채점
- pilot300 + 647 + 1,293 + 1,940 + 2,586 전체 재선택
- 결과 문서와 `selection_v2.json`

### 제외

- 추가 학습·full train·seed 43
- test 163 평가
- human 50 실제 rating (별도 protocol)
- B-family / EG2 bridge
- P1 데이터
- production 제품 승격

---

## 4. Definitions

- **v1**: 현재 `eval/slot_verify.py`의 `verify_summary`. 수정 금지.
- **v2**: 별도 versioned matcher. `verifier_version`을 결과에 기록.
- **grounded**: `new slot`이 하나도 없는 문서. v2에서도 이 정의를 유지한다.
- **grounded_nonvacuous**: summary slot이 1개 이상인 문서 중 grounded.
- **slot_free**: summary slot 0.
- **slot_preservation**: source slot 중 summary에 남은 비율. **grounded와 별도**.
- **coverage/adequacy**: target/reference 대비 중요한 slot 보존. 별도 보고.

---

## 5. Verifier v2 rules

### 5.1 URL soft-wrap join — measurement fix

source와 summary **양쪽**에 적용한다.

```text
pattern: https?://<non-space> [./_-] \n [space] [a-z0-9][A-Za-z0-9.\-/_%?=&#]*
```

- URL이 newline 직전에 `.`/`/`/`-`/`_`로 끝나고, 다음 token이 URL continuation일 때만 join.
- source-attested여야 하며, 추측으로 suffix를 만들지 않는다.
- scheme/host만 lowercase; **path/query case, comma, escape 보존**.
- URL wrap repair는 audit record에 남긴다.
- `http://coronamap.\n site`와 `http://coronamap.site`는 audit에서 같은 URL로 인정.
- **금지**: `www.` 제거, prefix match, arbitrary whitespace join, sentence punctuation join.

### 5.2 Time qualifier drop — equivalence policy

- summary time이 `오전/오후` 없이 `H시[M분]`이고, source의 같은 `H시[M분]`에 qualifier가 있으면 **qualifier_dropped**로 기록하고 grounded로 인정.
- summary가 qualifier를 **새로 붙이면** new.
- source에 같은 `H시[M분]`의 오전/오후가 **둘 다** 있거나 bare time이 함께 있으면 **자동 match 금지**, human adjudication.
- `오전 9시` vs `오후 9시`는 불일치. 12h↔24h 변환 금지.

### 5.3 Bare-number / unit — equivalence policy

- 기본은 **uniqueness guard**:
  - summary number에 unit이 없고
  - source에 동일 numeric value의 number slot이 있으며
  - 그 value가 source 전체에서 **unit까지 포함해 유일**할 때만 match.
- `unit_dropped`로 기록.
- number에 unit이 있으면 value+unit exact match.
- **금지**: `18%`↔`18명`, `18건`↔`18일`, 반올림, `만/억` 확장, `%`↔`퍼센트`.

### 5.4 Counter alias — 별도 clause (옵션)

`04709`처럼 `18 확진자`가 source의 `18명`과 같은 사람 수임이 문맥으로 명확한 경우:

- summary bare `18` 뒤에 `확진자`가 있고
- source에 `18명`이 있으며
- 같은 사건·집단·범위임이 확인될 때만
- **manual/human adjudication** 후 `counter_alias`로 인정.

이 clause는 자동 default가 아니다. `18일`·`18%`와 충돌할 수 있으므로 **entity/scope evidence**가 필요하다.

### 5.5 기존 URL false equivalence 수정

현재 `_canonical`은 URL 전체를 lowercase하고 comma를 제거해 다음을 같게 본다.

```text
https://example.com/Case?key=A,B
https://example.com/case?key=ab
```

v2는 URL path/query case와 comma를 보존해야 한다. 이 수정은 v2 audit에서 **false accept 감소**를 확인해야 한다.

---

## 6. Gate / selection

### 6.1 D-083 strict 결과 불변

```text
D-083 selected_step = null
fallback = pilot300
```

v2 결과로 이 기록을 덮어쓰지 않는다.

### 6.2 D-084 selection v2 — 정책별 시나리오

| 정책 | grounded 통과 후보 | max F1 | 결과 |
|---|---|---|---|
| generic v2 | pilot300, 1,293, 2,586 | **2,586** | 1,940은 159로 부적격 |
| generic + counter alias | + 1,940 | **1,940** | alias adjudication 필요 |
| URL+qualifier only | pilot300, 1,293, 2,586 | **2,586** | unit rule 없음 |

**결정 전에는 어느 것도 제품 후보로 부르지 않는다.**  
특히 “1,940을 살리기 위해 alias를 채택”하는 순서는 금지한다. alias는 독립적인 semantic rule로 먼저 정당화되어야 한다.

### 6.3 Gate 보강

- grounded 0.99 유지 (낮추지 않음)
- `grounded_nonvacuous` 항상 병기
- `slot_free` / `slot_preservation` 별도 보고
- coverage/adequacy는 **별도 criterion**; `grounded`를 omission gate로 재정의하지 않음
- doc-level/slot-level denominator 분리
- CP 95% + INCONCLUSIVE
- 161문서의 0.99는 statistical certificate가 아님

---

## 7. Public API (제안)

production 구현은 승인 후.

```python
@dataclass(frozen=True)
class VerifierV2Policy:
    url_wrap_join: bool = True
    time_qualifier_drop: bool = True
    bare_number_unique: bool = True
    counter_alias: bool = False  # opt-in, human adjudication only

def verify_summary_v2(
    source: str,
    summary: str,
    policy: VerifierV2Policy = VerifierV2Policy(),
) -> SlotReportV2:
    ...
```

`SlotReportV2`는 v1 `SlotReport`와 별도이며 `verifier_version`, `qualifier_dropped`, `unit_dropped`, `url_repairs`를 포함한다. v1 `verify_summary()`는 절대 수정하지 않는다.

---

## 8. DoD

- [ ] D-084 spec 사용자 승인
- [ ] `eval/slot_verify_v2.py` 별도 구현, v1 import/behavior 불변
- [ ] unit tests: URL wrap, trailing punctuation, URL case/comma, qualifier collision, `18%`/`18명`, duplicate numeric, no test data
- [ ] 383 excluded P0 pairs audit; all v1→v2 flips human-checked; **human-confirmed false accept 0**
- [ ] val 161 v1/v2 side-by-side for pilot300 + 4 checkpoints
- [ ] `selection_v2.json` with `policy` and `verifier_version`
- [ ] report: strict vs generic vs alias, all candidates, CP, nonvacuous, slot-free
- [ ] human 50 separate protocol (not started)
- [ ] test 163 seal 유지

---

## 9. 구현 순서

1. **이 초안 승인** — rule/option/DoD 확정.
2. **v2 module + tests** — production verifier와 분리.
3. **383 audit + human flip check** — false accept 0 확인.
4. **전체 재채점** — pilot300, 647, 1,293, 1,940, 2,586.
5. **selection v2 report** — generic/alias 별도.
6. **human 50** — 별도 승인.
7. **test 163** — candidate/hash freeze 후 1회.

---

## 10. 미결 결정

| ID | 결정 | 선택지 |
|---|---|---|
| D4-1 | unit policy | generic uniqueness / + counter alias / no unit |
| D4-2 | candidate if generic | 2,586 (F1 .6690) vs 1,293 (.6659) |
| D4-3 | candidate if alias | 1,940 (.6823) |
| D4-4 | gate additions | nonvacuous / coverage / CP / INCONCLUSIVE |
| D5-1 | human 50 | 1,940 primary? 2,586? include 1,293? |
| D5-2 | test 163 | seal until all above |

---

## 11. 한계·위험

- audit matcher는 production v2가 아니다.
- source raw data는 local에만 있고 Hoplite 샌드박스에는 없었다. audit는 local P0에서 수행했다.
- 902/1,617 numeric collision은 unit equivalence의 위험을 보여준다.
- val 161은 prompt/LR/pilot 선택에 재사용됐다. v2 재채점도 exploratory다.
- 1,940의 160/161은 counter alias에 의존한다. generic v2는 159/161이다.
- test 163은 계속 봉인.
