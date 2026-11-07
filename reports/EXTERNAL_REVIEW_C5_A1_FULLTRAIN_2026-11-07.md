# 외부 검토 요청 — C5 A1 full train과 grounded gate 재판정

- 날짜: 2026-11-07
- 저장소: `mandutt/unigem` (비공개), branch `main`
- 검토 기준: **본 문서가 포함된 `origin/main` HEAD** (`git rev-parse HEAD`로 확인)
- 검토 범위: F5 메모리용 추상 요약, A1 T5Gemma2 LoRA full train
- 데이터 등급: **P0(공개·합성 가공)**. P1 개인 데이터는 사용하지 않았다.
- test 163: **A0가 과거 사용(D-080, 0.6072); A1에는 미사용·봉인**
- 이 문서는 자기완결형이다. 이전 Hoplite 스레드나 대화를 읽지 않아도 판단할 수 있다.

---

## 0. 한눈에 보는 결론

1. **A1 full train 2 epoch은 정상 완료**됐다.
   - clean train 1,293, val 161
   - 2,586 step, 4시간 20분 18초, exit 0
   - final adapter: `data/models/f5_t5gemma2_lora/full_2ep/adapter.pt`
2. **D-083 strict selection gate를 통과한 checkpoint는 없다.**
   - gate: grounded ≥0.99, new-slot micro ≤0.01, EOS ≥0.95, repeated4 ≤0.06
   - 1,940: F1 **0.6823**, grounded 158/161 = 0.9814 → fail
   - 2,586: F1 **0.6690**, grounded 159/161 = 0.9876 → fail
   - 647: grounded 155/161, repeated4 0.0684 → fail
   - 1,293: grounded 159/161 → fail
3. **D-083 fallback에 따라 pilot300을 유지**했다.
   - pilot300: F1 0.6576, grounded 161/161, new slot 0, EOS 161/161, repeated4 0.0554
   - pilot300은 gate를 통과하지만 full train은 아니다.
4. **grounded 실패 5건(체크포인트 단위) 중 3건은 verifier 정규화 후보**다.
   - URL 내부 줄바꿈으로 source URL이 잘린 건
   - `오전` qualifier가 생략된 시각
   - `18명`을 `18`로 추출한 unit 생략
   - 실제 신규 slot hallucination은 `2.3%`, `2.2%` 1건으로 보인다.
5. **2,586은 1,940보다 더 짧고 더 압축된 요약**을 만든다.
   - slots/doc 5.34 → 4.73
   - total slots 860 → 762
   - slot-free 4 → 11
   - F1 −0.0133, length −9.2 tokens, slot preservation −0.0573
   - slot 감소 문서 73/161
6. **검토가 필요한 핵심**:
   - verifier 정규화를 어디까지 허용할 것인가
   - 그것을 새 gate로 사전등록할 것인가, 아니면 post-hoc로 보아 금지할 것인가
   - pilot300 fallback vs 1,940/2,586 candidate
   - human 50건과 test 163을 언제 열 것인가

---

## 1. 데이터·실험 설정

### 1.1 데이터

| 항목 | 값 |
|---|---|
| 파일 | `data/external/f5_pairs_v3_clean.jsonl` |
| 전체 clean | **1,617쌍** |
| train | **1,293** |
| val | **161** |
| test | **163** (A1 미사용) |
| split | `reports/provenance/C5_clean/splits.json`, seed 42 |
| 등급 | P0 |

계보:

```text
원본 v3       2,000
grounded      1,953
clean         1,617  ← full train은 이것만 사용
```

clean은 grounding 100%, 신규 slot 0인 데이터다. 원본 2,000 중 383쌍이 제외됐다.

### 1.2 모델·실행

| 항목 | 값 |
|---|---|
| base | `t5gemma-2-270m-270m`, vision tower 제거 |
| params | text-only **370,637,824** |
| LoRA | q/k/v/o, rank 8, alpha 16, dropout 0.05 |
| trainable | **1,474,560 (0.40%)** |
| input | `summarize: ` + passage, max 1,024 |
| label | summary content + `<eos>`, max 512, padding `-100` |
| train | 2 epoch = **2,586 step**, batch 1, lr 2e-4, AdamW wd 0.01, clip 1.0 |
| checkpoint | 647 / 1,293 / 1,940 / 2,586 |
| eval | 각 checkpoint에서 val 161, greedy, max_new 448 |
| wall | **15,617.9초 = 4시간 20분 18초** |
| peak RSS | 약 **3.88GB** |
| test | **미사용** |

### 1.3 지표 정의

- **char F1**: 공백 제거 문자 bag-of-characters F1. 순서·의미·사실성을 반영하지 않는다.
- **grounded**: `verify_summary`가 `new slot`을 하나도 만들지 않았는가. `missing slot`은 이 gate에서 실패로 치지 않는다.
- **new slot**: 원문 passage에 없는 숫자·날짜·시간·URL·경로·영문 식별자.
- **slot preservation**: 원문 slot 중 요약에 남은 비율. `verify_summary`의 `slot_preservation`.
- **slot-free**: 요약에 slot이 하나도 없는 문서. grounded는 이를 vacuous하게 통과시킨다.
- **EOS**: 생성이 EOS로 끝난 비율.
- **repeated4**: 반복 4-gram 비율.

---

## 2. Full train 결과

| checkpoint | char F1 | grounded | new slot (micro) | EOS | repeated4 | slots/doc | slot preservation | slot-free | gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **pilot300 fallback** | 0.657580 | **161/161 (1.0000)** | **0** | **161/161** | 0.05535 | 5.199 | 0.45583 | 6/161 | **PASS** |
| 647 | 0.669853 | 155/161 (0.9627) | 6 (0.00684) | 160/161 | 0.06840 | 5.447 | 0.48729 | 2/161 | FAIL |
| 1,293 | 0.665946 | 159/161 (0.9876) | 2 (0.00234) | **161/161** | 0.05866 | 5.304 | 0.45705 | 8/161 | FAIL grounded |
| **1,940** | **0.682278** | 158/161 (0.9814) | 4 (0.00465) | **161/161** | 0.05138 | 5.342 | 0.47610 | 4/161 | FAIL grounded |
| 2,586 | 0.668982 | 159/161 (0.9876) | 3 (0.00394) | **161/161** | **0.04450** | 4.733 | 0.41882 | **11/161** | FAIL grounded |

### Paired F1

| 비교 | mean diff | 95% bootstrap CI | 승/패 |
|---|---:|---:|---:|
| 1,940 − pilot300 | **+0.024698** | **[+0.012027, +0.037295]** | 99 / 61 |
| 2,586 − pilot300 | +0.011402 | [−0.000398, +0.023058] | 92 / 69 |
| 1,940 − 2,586 | **+0.013297** | **[+0.001197, +0.024928]** | 86 / 75 |

`bootstrap`는 2,000회, seed 42, paired document resampling.

### Selection 결과

- D-083 gate를 모두 적용한 결과: **`selected_step = null`**
- 이유: **no checkpoint met grounded ≥0.99**
- fallback: **pilot300**
- `selection.json` / `selection_summary.json` 참조

---

## 3. Grounded 실패 유형 분석

### 3.1 1,940 — 3건

| id | new slot | missing | char F1 | 판정 |
|---|---|---|---:|---|
| `REPORT-news_r-03978-00001` | `9시30분` | `오전9시30분` 포함 8개 | 0.5828 | **verifier format 후보** — 모델이 `오전`을 생략한 같은 시각 |
| `REPORT-news_r-04709-00001` | `18` | `18명` 포함 18개 | 0.5826 | **verifier unit 후보** — 모델의 `18 확진자`를 `18`로 추출, 원문은 `18명` |
| `REPORT-news_r-04951-00002` | `2.3%`, `2.2%` | 23개 | 0.6360 | **실제 신규 slot** — 원문에 없는 수치 |

### 3.2 2,586 — 2건

| id | new slot | missing | char F1 | 판정 |
|---|---|---|---:|---|
| `REPORT-news_r-02742-00001` | `http://coronamap.site` | `http://coronamap` 포함 6개 | 0.6322 | **verifier URL 후보** — 원문이 `http://coronamap.\n site`로 줄바꿈돼 source가 `http://coronamap`으로 잘림 |
| `REPORT-news_r-04951-00002` | `2.3%`, `2.2%` | 19개 | 0.7000 | **실제 신규 slot** — 동일 hallucination |

### 3.3 해석

- **두 checkpoint 모두 진짜 신규 slot 실패는 `04951` 1건**으로 보인다.
- 1,940의 `03978`(오전 생략), `04709`(18명/18), 2,586의 `02742`(URL 줄바꿈)는 **추출기 정규화 문제**일 가능성이 높다.
- 이 3건을 교정하면 1,940과 2,586은 각각 **160/161**이 되어 grounded gate를 통과할 수 있다.
- 그러나 이것은 **gate/verifier 변경**이다. D-083 strict 기준 결과를 사후에 바꾸면 안 된다.

### 3.4 Slot-free 11건 (2,586)

| target slot 수 | 문서 수 | 의미 |
|---|---:|---|
| 0 | 2 | 정상 vacuous |
| 1 | 3 | 경미한 누락 |
| 3~4 | 6 | **실질 누락** |
| **합계** | **11** | **9/11이 target slot 누락** |

예:

- `00159`: target 1 → 0
- `00426`: target 4 → 0
- `00706`: target 4 → 0
- `02741`: target 4 → 0
- `03220`: target 3 → 0
- `03348`: target 4 → 0
- `03915`: target 4 → 0

`grounded`는 이 11건을 vacuous하게 통과시킨다. **grounded 159/161은 사실 보존 99%가 아니다.**

---

## 4. 1,940 → 2,586 압축 drift

| 지표 | 1,940 | 2,586 | 변화 |
|---|---:|---:|---:|
| char F1 | **0.6823** | 0.6690 | −0.0133 |
| gen length | 199.5 | 190.3 | −9.2 |
| summary slots/doc | 5.342 | 4.733 | −0.609 |
| total slots | 860 | 762 | **−98** |
| slot preservation | 0.4761 | 0.4188 | −0.0573 |
| slot-free | 4 | 11 | +7 |
| new slots | 4 | 3 | −1 |
| repeated4 | 0.0514 | **0.0445** | −0.0069 |

### 문서 단위

- slot 감소: **73/161**
- slot 증가: 51/161
- 동일: 37/161
- 2,586에서 새로 slot-free: **8건**
- 2,586에서 slot이 생긴 문서: 1건

### 상관

- `slots_delta` ↔ `F1_delta`: **+0.324**
- `length_delta` ↔ `F1_delta`: **+0.351**
- `slots_delta` ↔ `length_delta`: **+0.519**

### 큰 손실 예

| id | slots Δ | F1 Δ | length Δ | preservation Δ |
|---|---:|---:|---:|---:|
| `01082` | −9 | −0.068 | −68 | −0.500 |
| `04855` | −8 | −0.207 | −87 | −0.571 |
| `03991` | −8 | +0.046 | −52 | −0.471 |
| `00476` | −7 | −0.066 | −52 | −0.538 |
| `05207` | −7 | +0.019 | −59 | −0.538 |
| `05292` | −7 | +0.037 | −79 | −0.700 |

### 해석

2,586은 1,940보다 더 짧고 압축된 요약을 만든다.

- 반복과 EOS는 개선됐다.
- 그러나 **slot과 길이를 함께 잃는 문서가 늘었고**, F1도 하락했다.
- target의 평균 summary slot은 **5.63/doc**인데, 1,940은 5.34, 2,586은 4.73이다. 2,586은 target보다 **0.9 slot/doc 적다**.
- 2,586의 “압축 개선”은 **정보 손실을 동반한 over-compression**으로 보는 것이 타당하다.

---

## 5. 결정·질문

### 5.1 결정 후보

| ID | 결정 | 선택지 | 현재 상태 |
|---|---|---|---|
| **D1** | verifier v2 정규화 | URL 줄바꿈만 / URL+AM·PM+unit / 정규화 안 함 | **미결** |
| **D2** | candidate | pilot300 fallback / 1,940 / 2,586 / 없음 | **strict 기준 no eligible** |
| **D3** | human 50 | test 전 / test 후 / 생략 | **미실행** |
| **D4** | test 163 |A1 최종 후보 1회 / 보류 / B-family에도 사용 | **A1 미사용** |
| **D5** | 다음 실험 | verifier audit / seed 43 / over-compression 대응 / 새 gate | **미결** |

### 5.2 검토 질문

**Q1.** verifier v2에서 URL 내부 줄바꿈·trailing punctuation을 정규화하는 것은 정당한가? `http://coronamap.\n site`와 `http://coronamap.site`를 같은 URL로 보는 것이 맞는가?

**Q2.** `오전 9시 30분`과 `9시 30분`을 같은 slot으로 볼 수 있는가? qualifier 생략을 “new slot”으로 볼 것인가, “missing qualifier”로 별도 처리할 것인가?

**Q3.** `18명`과 `18 확진자`를 같은 slot으로 볼 수 있는가? number canonicalization에서 unit을 어디까지 무시해야 하는가?

**Q4.** 위 정규화를 적용하면 1,940과 2,586이 각각 160/161이 된다. 이것을 **새 D-084 gate로 사전등록**하는 것이 정당한가, 아니면 post-hoc gate 변경으로 보아 금지해야 하는가?

**Q5.** strict D-083 기준에서 **pilot300 fallback**을 유지하는 것이 맞는가? 아니면 full train 1,940을 “near-miss exploratory candidate”로 human review에 올릴 수 있는가?

**Q6.** 1,940(F1 0.6823, slots/doc 5.34, slot-free 4)과 2,586(F1 0.6690, repeated4 0.0445, slot-free 11) 중 어느 쪽을 human 50의 primary로 삼아야 하는가?

**Q7.** 2,586의 slot-free 11건 중 9건이 target slot 누락이다. 이것을 grounded gate 실패로 간주하지 않는 현재 정의가 타당한가? G-C5를 “grounded + slot preservation”으로 확장해야 하는가?

**Q8.** 2 epoch의 후반 over-compression을 고려할 때, full train을 2 epoch로 한 결정은 적절했는가? 1 epoch(1,293 step) 또는 1,940 step early stop이 더 나았을 가능성이 있는가?

**Q9.** human 50건은 어떤 표본으로 구성해야 하는가? `04951` hallucination, slot-free 11건, 최저 F1 decile, 최장 출력, 나머지 random을 어떻게 배분할 것인가?

**Q10.** test 163을 지금 열어도 되는가? 아니면 verifier v2 + human 50 + candidate freeze 전까지 봉인해야 하는가?

**Q11.** 다음 실험의 우선순위는 무엇인가?
- A. verifier v2 audit + re-adjudication
- B. human 50 on 1,940/2,586
- C. seed 43 full train
- D. over-compression 대응(length/slot auxiliary)
- E. gate 재설계

**Q12.** 이 요청서의 사실 오류·과장·누락은 무엇인가?

---

## 6. 요청 형식

각 사안에 대해:

1. **판정** — 찬성/반대/조건부/보류
2. **근거** — 이 문서의 수치·정의·코드·artefact에 기반
3. **다음 단계** — 실행 가능한 1~3개

추가로:

- Must-fix 최대 7개, 우선순위 순
- 추가 실험 최대 5개, 예상 비용
- 사실 오류·과장·누락
- 최종 권고 1~2문단

**금지**: test 163을 지금 열지 말 것, P1 데이터 사용 금지, 운영 자산 수정 금지, gate를 사후에 낮추는 제안 금지.

---

## 7. 재현·산출물

### 결과·분석

- `reports/C5_A1_full_train_2ep_2026-11-07.md`
- `reports/C5_A1_error_analysis_2026-11-07.md`
- `reports/C5_A1_3AI_REVIEW_SYNTHESIS_2026-11-06.md`
- `reports/C5_A1_bare_val161_2026-11-06.md`
- `reports/provenance/C5_a1/full_2ep/eval_step_{0647,1293,1940,2586}/`
- `reports/provenance/C5_a1/full_2ep/selection_summary.json`
- `reports/provenance/C5_a1/full_2ep/error_analysis_1940_vs_2586.json`

### 코드

- `runner/c5_a1_lora.py`
- `runner/c5_a1_eval_batch.py`
- `runner/c5_a1_select.py`
- `runner/c5_a1_error_analysis.py`
- `runner/c5_a1_full_watch.py`
- `eval/slot_verify.py`
- `eval/tests/test_a1_runner.py`

### 모델

- full train adapter: `data/models/f5_t5gemma2_lora/full_2ep/adapter.pt`
- checkpoints: `data/models/f5_t5gemma2_lora/full_2ep/checkpoints/step_{0647,1293,1940,2586}.pt`
- pilot300 fallback: `data/models/f5_t5gemma2_lora/pilot300_lr2e4_prefix.pt`

### 재현 명령

```bash
# full train
.venv/Scripts/python.exe -u runner/c5_a1_lora.py \
  --mode full \
  --steps 2586 \
  --lr 2e-4 \
  --prefix "summarize: " \
  --rank 8 --alpha 16 --dropout 0.05 --weight-decay 0.01 \
  --checkpoint-steps 647,1293,1940,2586 \
  --checkpoint-dir data/models/f5_t5gemma2_lora/full_2ep/checkpoints \
  --eval-checkpoints --eval-limit 0 \
  --adapter data/models/f5_t5gemma2_lora/full_2ep/adapter.pt \
  --out reports/provenance/C5_a1/full_2ep

# selection
.venv/Scripts/python.exe runner/c5_a1_select.py \
  --root reports/provenance/C5_a1/full_2ep

# error analysis
.venv/Scripts/python.exe runner/c5_a1_error_analysis.py
```

## 8. 한계

- test 163은 A1에 사용하지 않았다. A0가 과거 사용했다.
- human 50은 아직 없다.
- `char F1`은 lexical metric이다. 의미·사실성·유용성을 보장하지 않는다.
- `grounded`는 신규 slot만 본다. 누락은 보지 않는다.
- 2,586의 slot-free 11건은 vacuous 통과이며, 9건은 target slot 누락이다.
- verifier 정규화 후보 3건은 **아직 공식 재판정 전**이다. 이 문서의 표는 strict 기준 결과와 후보 분석을 분리해 표기했다.
- full train은 2 epoch, 단일 seed다. seed 43 재현은 미실행.
- B1d EG2→T5 bridge는 이번 범위가 아니다.
