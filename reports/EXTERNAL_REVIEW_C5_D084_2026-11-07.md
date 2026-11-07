# 외부 검토 요청 — C5 A1, verifier v2, D-084 재선택 (2026-11-07)

- 저장소: `mandutt/unigem` (비공개), branch `main`
- 검토 기준: **본 문서가 포함된 `origin/main` HEAD**
- 데이터 등급: **P0(공개·합성 가공)**. P1 데이터는 사용하지 않았다.
- test 163: **A0가 과거 사용(D-080, 0.6072); A1에는 미사용·봉인**
- 이 문서는 자기완결형이다. 이전 Hoplite 스레드나 대화를 읽지 않아도 판단할 수 있다.
- **상태: D-084는 draft이며 승인된 결정이 아니다.** `eval/slot_verify.py`와 production selection은 수정하지 않았다.

---

## 0. 한눈에 보는 현재 상태

1. **D-083 strict 결과는 그대로 유효**하다.
   - full train 4 checkpoint 모두 grounded gate 미달
   - `selected_step = null`
   - fallback = **pilot300** (제품 승격 아님)
2. **A1 full train은 정상 완료**됐다.
   - 2 epoch, 2,586 step, 4시간 20분 18초, exit 0
   - test 163 미사용
3. **직전 3-AI 검토(2026-11-07)** 는 다음에 합의했다.
   - strict D-083 유지
   - pilot300 fallback
   - **1,940을 exploratory human-review primary**
   - 2,586은 over-compression contrast
   - **D-084 없이 verifier v2를 적용하지 말 것**
   - test 163 봉인
4. **후속 verifier v2 audit**에서 중요한 반전이 확인됐다.
   - generic v2: 1,293·2,586은 **160/161**, 1,940은 **159/161**
   - counter alias를 추가해야 1,940이 **160/161**
   - 즉 **selection 결과가 unit alias 정책에 의존**한다.
5. **D-084 초안**은 이 차이를 명시적으로 다룬다.
   - generic v2를 baseline
   - counter alias를 별도 opt-in clause
   - 전체 checkpoint 재선택
   - test 163과 human 50은 별도
6. **판단이 필요한 핵심**:
   - generic v2만 쓸 것인가, counter alias를 허용할 것인가
   - 그 결과 candidate를 2,586으로 둘 것인가, 1,940으로 둘 것인가
   - human 50의 primary를 무엇으로 할 것인가
   - D-084를 “outcome-informed exploratory”로 승인할 수 있는가
   - test 163을 언제 열 것인가

---

## 1. 프로젝트·데이터·모델

### 1.1 목표

F5는 EG2/T5Gemma2 계열 모델로 **메모리용 추상 요약**을 만드는 트랙이다. 추출형이 아니라 추상 요약을 목표로 한다. 현재 중심 실험은 A1: native **T5Gemma2-270m-270m** encoder-decoder에 q/k/v/o LoRA를 붙여 요약을 학습하는 것이다.

### 1.2 데이터

| 항목 | 값 |
|---|---|
| 원본 v3 | 2,000쌍 |
| grounded filter | 1,953 |
| **clean (primary)** | **1,617** |
| train | **1,293** |
| val | **161** |
| test | **163** (A1 미사용) |
| split | seed 42, `reports/provenance/C5_clean/splits.json` |
| 등급 | P0 |

clean은 v1 slot verifier 기준 grounding 100%, new slot 0으로 필터링한 데이터다. 이 필터 자체가 v1에 의존한다는 점이 D-084의 문제의식이다.

### 1.3 모델·실행

| 항목 | 값 |
|---|---|
| base | `t5gemma-2-270m-270m`, vision tower 제거 |
| text-only params | 370,637,824 |
| LoRA | q/k/v/o, rank 8, alpha 16, dropout 0.05 |
| trainable | 1,474,560 (0.40%) |
| input | `summarize: ` + passage, max 1,024 |
| label | summary content + `<eos>`, max 512, pad `-100` |
| train | 2 epoch = **2,586 step**, batch 1, lr 2e-4, AdamW wd 0.01, clip 1.0 |
| checkpoint | 647 / 1,293 / 1,940 / 2,586 |
| val eval | 각 checkpoint, greedy, max_new 448 |
| wall | **15,617.9초 = 4시간 20분 18초** |
| peak RSS | 약 3.88GB |
| test | **미사용** |

---

## 2. D-083 strict 결과

### 2.1 Gate

D-083 사전등록:

```text
grounded_rate >= 0.99
new-slot micro <= 0.01
EOS >= 0.95
repeated4 <= 0.06
→ 통과 후 max char F1
→ tie는 이른 checkpoint
→ pilot300 fallback 보존
→ test 163은 A1 최종 후보 1개에만 1회
→ 사람 50건은 test 전
```

161문서에서 grounded ≥0.99는 **최대 1건 실패**를 뜻한다. 160/161 = 0.9938은 통과, 159/161 = 0.9876은 실패다.

### 2.2 결과

| checkpoint | char F1 | grounded | new slot (micro) | EOS | repeated4 | slots/doc | slot preservation | slot-free | gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **pilot300 fallback** | 0.657580 | **161/161** | **0** | **161/161** | 0.05535 | 5.199 | 0.45583 | 6/161 | **PASS** |
| 647 | 0.669853 | 155/161 | 6 | 160/161 | 0.06840 | 5.447 | 0.48729 | 2/161 | FAIL |
| 1,293 | 0.665946 | 159/161 | 2 | **161/161** | 0.05866 | 5.304 | 0.45705 | 8/161 | FAIL grounded |
| **1,940** | **0.682278** | 158/161 | 4 | **161/161** | 0.05138 | 5.342 | 0.47610 | 4/161 | FAIL grounded |
| 2,586 | 0.668982 | 159/161 | 3 | **161/161** | **0.04450** | 4.733 | 0.41882 | **11/161** | FAIL grounded |

### 2.3 Paired F1

| 비교 | mean diff | 95% bootstrap CI |
|---|---:|---:|
| 1,940 − pilot300 | **+0.024698** | **[+0.012027, +0.037295]** |
| 2,586 − pilot300 | +0.011402 | [−0.000398, +0.023058] |
| 1,940 − 2,586 | **+0.013297** | **[+0.001197, +0.024928]** |

bootstrap 2,000회, seed 42, paired document resampling.

### 2.4 strict selection

```text
selected_step: null
reason: no checkpoint met grounded >= 0.99
fallback: pilot300
test_163: sealed / unused for A1
```

**D-083 strict 결과는 변경되지 않았다.**

---

## 3. 직전 3-AI 검토 (2026-11-07)

모델: **GLM 5.3 Flash max / Opus 5.5 medium / Sol 6.1 xhigh**. 비용 약 **$2.2989**. 원문은 `docs/hoplite/c5_fulltrain_2026-11-07/review_{GLM,OPUS,SOL}.md`.

| 항목 | 3/3 결론 |
|---|---|
| D-083 strict | **유지** |
| pilot300 | **strict fallback 유지** |
| 1,940 | **exploratory human-review primary** |
| 2,586 | **secondary compression contrast, 승격 반대** |
| test 163 | **봉인** |
| verifier v2 | **조건부; D-084 필수** |
| 1,293 side effect | **v2에서 160/161 가능, 전체 재선택 필요** |
| G-C5 | slot-level과 D-083 doc-level 분리; CP·nonvacuous 병기 |
| 2,586 | target implied preservation ≈0.465보다 낮은 0.4188; over-compression |

3-AI가 지적한 요청서 오류:

- `03978` missing **7개**(not 8)
- `04709` missing **15개**(not 18), `18명`은 missing 아님
- 647 EOS 160/161은 **기준 통과** (EOS 실패 아님)
- trailing punctuation은 v1 canonicalizer가 이미 처리
- “grounded 실패 5건 중 3건”은 **1,940/2,586 범위**로 한정해야 함

---

## 4. verifier v2 audit (2026-11-07, 신규)

### 4.1 Audit 방식

- **읽기 전용**. `eval/slot_verify.py`는 수정하지 않았다.
- local P0 `f5_pairs_v3_clean.jsonl` 1,617쌍 + val 161 예측
- audit script: `runner/c5_a1_verifier_v2_audit.py`
- raw: `reports/provenance/C5_a1/full_2ep/verifier_v2_audit.json`
- audit matcher는 production v2가 아니다.

### 4.2 V1 vs candidate v2

| system | V1 grounded | V2 generic | V2 + counter alias | V2 generic 신규 실패 |
|---|---:|---:|---:|---|
| pilot300 | 161/161 | 161/161 | 161/161 | — |
| 647 | 155/161 | 158/161 | 158/161 | `00114, 01767, 03086` |
| **1,293** | 159/161 | **160/161** | 160/161 | `03801` |
| **1,940** | 158/161 | **159/161** | **160/161** | `04709, 04951` |
| **2,586** | 159/161 | **160/161** | 160/161 | `04951` |

### 4.3 왜 1,940은 generic v2에서 159인가

- `03978`은 qualifier rule로 해소된다.
- `04709`는 source에 `18일`과 `18명`이 **함께** 있어, bare `18`을 `18명`에 자동 매칭하는 uniqueness guard가 실패한다.
- `18 확진자`를 사람 수로 확정하려면 **counter alias**가 필요하다. 이것은 단순 normalization이 아니라 **entity/scope adjudication**이다.
- `04951`의 `2.3%`, `2.2%`는 v2에서도 **genuine negative control**로 남는다.

### 4.4 Selection sensitivity

| 정책 | grounded 통과 후보 | max F1 | 결과 |
|---|---|---|---|
| **generic v2** | pilot300, 1,293, 2,586 | **2,586** (0.6690) | 1,940은 159로 부적격 |
| **generic + counter alias** | + 1,940 | **1,940** (0.6823) | alias adjudication 필요 |
| **URL+qualifier only** | pilot300, 1,293, 2,586 | **2,586** | unit rule 없음 |

**이것이 이번 검토의 중심 쟁점이다.** 1,940을 살리기 위해 alias를 채택하는 순서는 post-hoc gate가 된다. alias는 독립적으로 정당화되어야 한다.

### 4.5 Corpus exposure

| 항목 | 값 |
|---|---:|
| URL soft-wrap 문서 | **3 / 1,617** |
| qualifier collision 문서 | **7 / 1,617** |
| numeric unit collision 문서 | **902 / 1,617 (55.8%)** |
| clean target v1→v2 변화 | **0 / 1,617** |
| excluded 383쌍 중 v2 grounded flip | **5 / 383** |

Excluded target flip 5건:

```text
REPORT-news_r-00291-00002  v1_new=2020
REPORT-news_r-01844-00001  v1_new=2021
REPORT-news_r-03253-00001  v1_new=404
REPORT-news_r-04791-00001  v1_new=20
REPORT-news_r-05019-00001  v1_new=5000, 200
```

이 5건은 **v2 false-accept 후보**다. human adjudication 없이 “v2는 clean target을 바꾸지 않았다”고 정당화하면 안 된다.

### 4.6 기존 URL false equivalence

현재 v1 `_canonical`은 URL 전체를 lowercase하고 comma를 제거한다.

```text
source: https://example.com/Case?key=A,B
summary: https://example.com/case?key=ab
→ new=(), missing=(), grounded=True
```

v2에서는 scheme/host만 lowercase하고 path/query case·comma·escape를 보존해야 한다. 이 수정은 false accept를 줄이는 방향이어야 하며, URL wrap join은 source와 summary **양쪽**에 적용해야 한다. 1,940 prediction도 `http://coronamap.\nsite`를 포함하기 때문이다.

---

## 5. D-084 초안

전문: `docs/D-084_verifier_v2_draft_2026-11-07.md` (DRAFT / 미승인)

### 5.1 Scope

포함:

- verifier v2 rule 명세·audit
- 383 excluded P0 pair의 flip 조사
- val 161 v1/v2 side-by-side
- pilot300 + 647 + 1,293 + 1,940 + 2,586 전체 재선택
- `selection_v2.json`

제외:

- 추가 학습·seed 43
- test 163
- human 50 실제 rating
- B-family / EG2 bridge
- P1
- 제품 승격

### 5.2 Rules

**URL soft-wrap**

- source와 summary 양쪽
- URL이 newline 직전 `.`/`/`/`-`/`_`로 끝나고 다음 token이 URL continuation일 때만 join
- source-attested; suffix 추측 금지
- scheme/host만 lowercase; path/query case·comma·escape 보존

**Time qualifier**

- summary가 qualifier 없이 `H시[M분]`이고 source가 같은 시간을 qualifier와 함께 가지면 `qualifier_dropped`로 기록하고 grounded 인정
- summary가 qualifier를 새로 붙이면 new
- source에 같은 시간의 오전/오후가 둘 다 있으면 자동 match 금지
- 12h↔24h 변환 금지

**Bare number / unit**

- summary number에 unit이 없고 source에 동일 numeric value가 **unit 포함 유일**할 때만 match
- `unit_dropped` 기록
- `18%`↔`18명`, `18건`↔`18일`, 반올림, `만/억` 확장 금지

**Counter alias (별도 opt-in)**

- summary bare `18` 뒤에 `확진자`가 있고 source `18명`과 같은 사건·집단·범위임이 명확할 때만
- **human adjudication** 후 인정
- default 아님

### 5.3 Gate / selection

- grounded 0.99 유지
- `grounded_nonvacuous`, `slot_free`, `slot_preservation` 별도 보고
- coverage/adequacy는 별도 criterion; grounded를 omission gate로 재정의하지 않음
- doc-level/slot-level denominator 분리
- CP 95% + INCONCLUSIVE
- D-083 strict 기록은 덮어쓰지 않음

### 5.4 Public API / 구현 순서

```python
@dataclass(frozen=True)
class VerifierV2Policy:
    url_wrap_join: bool = True
    time_qualifier_drop: bool = True
    bare_number_unique: bool = True
    counter_alias: bool = False  # opt-in, human adjudication only

def verify_summary_v2(source, summary, policy=VerifierV2Policy()) -> SlotReportV2:
    ...
```

순서:

1. D-084 spec 승인
2. `eval/slot_verify_v2.py` 별도 구현 + tests (v1 불변)
3. 383 audit + human flip check
4. 전체 재채점
5. selection v2 report
6. human 50
7. test 163 (별도)

---

## 6. 판단이 필요한 내역 일체

| ID | 결정 | 선택지 | 현재 |
|---|---|---|---|
| **D4-1** | unit policy | generic uniqueness / + counter alias / no unit | 미결 |
| **D4-2** | generic candidate | 2,586 (F1 .6690) / 1,293 (.6659) | 미결 |
| **D4-3** | alias candidate | 1,940 (.6823) | 미결 |
| **D4-4** | gate additions | nonvacuous / coverage / CP / INCONCLUSIVE | 미결 |
| **D4-5** | 5 excluded flip | false accept / legitimate fix / defer | 미결 |
| **D4-6** | URL case/comma | v2에서 즉시 수정 / 별도 audit | 미결 |
| **D5-1** | human 50 | 1,940 primary / 2,586 primary / include 1,293 | 미결 |
| **D5-2** | test 163 | seal until D-084 + human + freeze / other | **seal** |
| **D5-3** | next experiment | v2 implementation / seed 43 / compression arm | 미결 |
| **D5-4** | D-084 status | exploratory outcome-informed / reject post-hoc | 미결 |

---

## 7. 검토 질문

**Q1.** generic v2(URL + qualifier + uniqueness-guarded number)를 baseline으로 승인하는 것이 정당한가? 아니면 URL만 measurement fix로 제한해야 하는가?

**Q2.** `18 확진자` counter alias를 별도 clause로 두는 것이 정당한가? 자동 규칙이 아니라 human adjudication이어야 하는가?

**Q3.** excluded 383쌍 중 v2가 grounded로 뒤집은 5건을 false accept로 볼 것인가? 이 5건을 포함한 human flip audit의 acceptance 기준은 무엇인가?

**Q4.** D-084는 “outcome-informed exploratory”로 승인 가능한가? 아니면 verifier v2 자체를 폐기해야 하는가? D-083 strict 결과를 어떻게 보존해야 하는가?

**Q5.** generic v2에서 1,940은 159/161로 부적격이고, max F1 후보는 2,586이다. 3-AI가 1,940을 human primary로 권고한 것과 충돌한다. 어느 쪽을 candidate로 삼아야 하는가?

**Q6.** counter alias를 승인하면 1,940이 160/161이 되어 max F1 후보가 된다. alias를 승인할 근거는 무엇이며, `18일`/`18명` collision을 어떻게 adjudicate해야 하는가?

**Q7.** human 50은 누구를 primary로 해야 하는가? 1,940, 2,586, 1,293, pilot300을 같은 50문서에 blind로 평가해야 하는가?

**Q8.** G-C5에 nonvacuous grounded, coverage/adequacy, CP, INCONCLUSIVE를 추가해야 하는가? 구체적인 threshold와 denominator는 무엇인가?

**Q9.** 161문서에서 grounded ≥0.99는 통계적 보장이 아니다. gate를 유지하되 CP/INCONCLUSIVE를 병기하는 것이 맞는가? 아니면 표본을 늘려야 하는가?

**Q10.** test 163을 지금 열어서는 안 되는가? 해제 조건과 A0/A1 사용 이력을 어떻게 표기해야 하는가?

**Q11.** URL canonicalizer의 path/query case·comma false accept를 v2에서 즉시 수정해야 하는가? 별도 audit로 분리해야 하는가?

**Q12.** D-084 draft의 Scope/DoD/Public API/구현 순서에 빠진 것이 있는가? 구현 전에 반드시 고쳐야 할 Must-fix는 무엇인가?

**Q13.** 1,940이 generic v2에서 부적격이라면, human 50에서 1,940을 여전히 exploratory primary로 볼 수 있는가? “human review”와 “selection eligibility”를 분리하는 것이 맞는가?

**Q14.** 이 요청서의 사실 오류·과장·누락은 무엇인가?

---

## 8. 산출물·재현

### 결과·분석

- `reports/C5_A1_full_train_2ep_2026-11-07.md`
- `reports/C5_A1_error_analysis_2026-11-07.md`
- `reports/C5_A1_3AI_REVIEW_SYNTHESIS_2026-11-07.md`
- `reports/C5_A1_verifier_v2_audit_2026-11-07.md`
- `reports/EXTERNAL_REVIEW_C5_A1_FULLTRAIN_ERRATA_2026-11-07.md`
- `reports/provenance/C5_a1/full_2ep/eval_step_{0647,1293,1940,2586}/`
- `reports/provenance/C5_a1/full_2ep/selection_summary.json`
- `reports/provenance/C5_a1/full_2ep/verifier_v2_audit.json`

### 코드

- `runner/c5_a1_lora.py`
- `runner/c5_a1_eval_batch.py`
- `runner/c5_a1_select.py`
- `runner/c5_a1_error_analysis.py`
- `runner/c5_a1_verifier_v2_audit.py`
- `eval/slot_verify.py` (v1, 수정 금지)
- `eval/tests/`

### 모델

- `data/models/f5_t5gemma2_lora/full_2ep/adapter.pt`
- `data/models/f5_t5gemma2_lora/full_2ep/checkpoints/step_{0647,1293,1940,2586}.pt`
- `data/models/f5_t5gemma2_lora/pilot300_lr2e4_prefix.pt`

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
- val 161은 prompt/LR/pilot 선택에 재사용됐다. selection bias가 있다.
- 16/161 val 문서가 train과 article prefix를 공유한다.
- pilot300의 generation length 248.3 vs 1,940 199.5 / 2,586 190.3; F1 길이 confound.
- audit matcher는 production v2가 아니다.
- URL repair 3건, qualifier collision 7건, numeric unit collision 902건; human 확인 없이 자동 적용 금지.
- 1,940의 160/161은 counter alias에 의존한다. generic v2는 159/161이다.
- **D-084는 아직 승인된 결정이 아니다.**

## 10. 요청 형식

각 D4-1~D5-4와 Q1~Q14에 대해:

1. **판정** — 찬성/반대/조건부/보류
2. **근거** — 이 문서의 수치·정의·artefact에 기반
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
- 1,940을 살리기 위해 alias를 먼저 채택하는 순서 금지
- 2,586을 terminal adapter라는 이유로 승격하는 제안 금지
