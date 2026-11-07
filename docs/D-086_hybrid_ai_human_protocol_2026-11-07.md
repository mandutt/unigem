# D-086 — Hybrid AI panel + human calibration protocol (v1.0.0)

**상태:** `FROZEN` — AI 호출·human rating 시작 전 사전등록  
**날짜:** 2026-11-07  
**대상:** C5 F5 abstractive summary, A1 full-train checkpoints  
**목적:** D-085 human-only 240 ratings를 **AI 3-judge panel 600 ratings + human calibration 100 ratings**로 대체

> D-085는 human rating을 시작하지 않은 상태에서 **D-086으로 대체**한다. D-085 파일과 hash는 이력으로 보존하며, D-085로 human rating을 수집하지 않는다.  
> 이 문서는 AI 출력과 human rating을 보기 전에 고정한다. 시작 후 primary contrast, 표본, model, rubric, gate를 변경하지 않는다. 변경은 별도 amendment로만 가능하다.

---

## 0. 한 줄 요약

- **AI panel**: 3 models × 50 docs × 4 summaries = **600 ratings**
- **Human calibration**: 20 docs × 4 summaries = **80 ratings**
- **Human repeat**: 5 docs × 4 summaries = **20 ratings** (7일 이상 간격)
- **Human total**: **100 ratings**
- AI panel과 human calibration의 일치도가 gate를 통과할 때만 AI panel을 primary evidence로 사용한다.
- 실패/INCONCLUSIVE → **pilot300 fallback, no approved candidate, test 163 sealed**

---

## 1. 왜 hybrid인가

D-085의 human-only 설계는 인간 기준의 타당도는 직접적이지만, 1인 평가의 불안정성과 240 ratings 부담이 있다.  
AI-only는 빠르고 일관적이지만, AI consensus가 인간 기준과 일치한다는 보장이 없다.

D-086은 두 가지를 분리한다.

| 역할 | 담당 |
|---|---|
| **대규모 평가** | AI 3-judge panel, 600 ratings |
| **타당도 calibration** | human 20 docs, 80 ratings |
| **human 안정성** | human repeat 5 docs, 20 ratings |
| **최종 primary** | calibration gate를 통과한 AI panel |

**AI panel은 human population이 아니다.** 3개 모델의 consensus는 “독립적인 인간 3명”과 같지 않으며, model family가 공유하는 오류가 있을 수 있다. 그래서 `ai_independence_claim = NOT_INDEPENDENT`로 기록한다.

---

## 2. 표본

D-085의 frozen 50-doc sample을 그대로 사용한다. 새 표본을 만들지 않는다.

- 50 docs = targeted 20 + random 30
- test 163: **사용하지 않음**
- AI panel: **50 docs 전체**
- human calibration: **20 docs** = targeted 10 + random 10
- human repeat: **5 docs** = targeted 3 + random 2

### 2.1 Human calibration 20

- targeted 10: known residual 6 + 2,586 slot-free 4
- random 10: D-085 random30의 첫 10개
- 4 sessions × 5 docs
- 각 doc 4 summaries = **80 ratings**

### 2.2 Human repeat 5

- targeted 3: known residual 3
- random 2: calibration random의 첫 2개
- **7일 이상 간격**
- 1 session × 5 docs = **20 ratings**

### 2.3 train-prefix

D-085와 동일하게 train-prefix 16건을 flag로 유지한다.  
AI panel·human calibration 결과 모두 **train-prefix 제외 sensitivity**를 보고한다.

---

## 3. AI panel

### 3.1 Models

| judge | model | reasoning |
|---|---|---|
| `glm` | `z-ai/glm-5.3-flash` | `max` |
| `sonnet` | `claude-sonnet-5-5` | `high` |
| `sol` | `gpt-6.1-sol` | `xhigh` |

- 3 models × 50 docs = **150 calls**
- 각 call은 4 summaries를 평가하므로 **600 ratings**
- 모델별로 독립적인 A–D 순서를 사용한다. 순서는 `manifest.judge_arm_order[judge][doc]`에 고정한다.

### 3.2 AI가 보는 것

- SOURCE 원문
- A–D summaries (4개)
- rubric
- response schema

### 3.3 AI가 보지 않는 것

- target summary
- arm 이름, checkpoint step, model 이름
- char F1, grounded, EOS, repeated4
- human rating
- 다른 judge의 출력
- 다른 doc의 출력

### 3.4 출력 schema

각 doc에 대해 **valid JSON only**:

```json
{
  "doc_id": "...",
  "summaries": {
    "A": {
      "adequacy": 0,
      "critical_unsupported": 0,
      "critical_omission": 0,
      "wrong_unit_qualifier": 0,
      "entity_relation": 0,
      "fluency": 1,
      "utility": 1,
      "evidence": ["short source quote"],
      "reason": "one or two sentences"
    },
    "B": {},
    "C": {},
    "D": {}
  }
}
```

- `adequacy` 0–4
- flags 0/1
- `fluency`, `utility` 1–5
- `evidence`: SOURCE에서 짧은 quote
- `reason`: 1–2문장
- JSON parse 실패 시 **1회 retry**; 그래도 실패하면 해당 judge/doc는 missing으로 기록하고 `INCONCLUSIVE`.

### 3.5 AI panel 집계

- **adequacy**: 3 judge의 **median**
- **flags**: 3 judge의 **majority**
  - 1/2 split 또는 0/2 split은 `contested`
- **fluency/utility**: median
- **contested**:
  - adequacy range ≥ **2**, 또는
  - critical flag vote split
- `contested` doc-arm은 primary에서 별도 표시하고 sensitivity에서 제외한다.

### 3.6 AI inter-judge reliability

- 50 docs × 4 arms = **200 targets**, 3 judges
- adequacy **ICC(2,1) ≥ 0.60**
- 미달 시 AI panel은 primary evidence가 될 수 없다 → `INCONCLUSIVE`

---

## 4. Human calibration

### 4.1 Blind

- human은 AI panel 출력을 보지 않는다.
- human은 arm 이름·model·step·metrics를 보지 않는다.
- A–D 순서는 human sheet에서 별도 무작위화한다. (AI panel 순서와 무관)
- human calibration은 AI panel 결과가 lock되기 전/후 어느 쪽이어도 가능하지만, **서로의 결과를 보지 않는다.**

### 4.2 Rating

- 20 docs × 4 summaries = **80 ratings**
- 4 sessions × 5 docs
- rubric은 D-085와 동일
- `adequacy`, 4 flags, `fluency`, `utility`, `notes`

### 4.3 Human repeat

- 5 docs × 4 summaries = **20 ratings**
- **7일 이상 간격**
- 첫 pass 점수를 보지 않는다.
- human intra-rater reliability:
  - adequacy **ICC(2,1) ≥ 0.70**
  - quadratic weighted kappa **≥ 0.60**
- 미달 시 `INCONCLUSIVE`; AI panel을 승인하지 않는다.

### 4.4 Human limitation

- human inter-rater reliability는 **NOT_AVAILABLE** (1명)
- human repeat는 independence를 대체하지 않는다.
- 결과는 **single human + AI panel** evidence이며, human population 일반화가 아니다.

---

## 5. AI–human calibration gate

AI panel median과 human rating을 **20 docs × 4 arms = 80 pairs**로 비교한다.

| 항목 | 기준 |
|---|---:|
| Adequacy ICC(2,1) | **≥ 0.70** |
| Adequacy quadratic weighted kappa | **≥ 0.60** |
| Critical unsupported Cohen's kappa | **≥ 0.60** |
| Critical omission Cohen's kappa | **≥ 0.60** |
| Human repeat ICC(2,1) | **≥ 0.70** |
| Human repeat QWK | **≥ 0.60** |
| AI inter-judge ICC(2,1) | **≥ 0.60** |
| Contested rate | **≤ 0.10** |

하나라도 실패하면:

- `INCONCLUSIVE`
- AI panel은 primary evidence가 아니다.
- human rating을 50 docs로 확대하는 것은 **자동이 아니다**; 별도 amendment 필요.
- candidate approval 없음.

---

## 6. Primary decision

Calibration gate를 통과한 경우에만 AI panel median으로 primary analysis를 한다.

### 6.1 Contrast

- primary: **2,586 − pilot300**, paired by doc
- secondary: 2,586 − 1,293
- exploratory: 1,940 − pilot300 / 1,940 − 2,586

### 6.2 Margins

- adequacy paired mean의 **95% bootstrap lower bound ≥ −0.25**
- critical unsupported 차이의 **95% upper bound < +0.05**
- critical omission 차이의 **95% upper bound < +0.05**
- bootstrap **10,000**, seed `20261107`
- train-prefix 16건 제외 sensitivity도 같은 margin 통과

### 6.3 Contested sensitivity

- `contested` doc-arm을 제외한 뒤:
  - adequacy lower ≥ −0.25
  - critical upper < +0.05
- 실패하면 `INCONCLUSIVE`

### 6.4 판정

| 조건 | 결과 |
|---|---|
| calibration gate + primary + sensitivity 모두 통과 | **HYBRID_SUPPORTED** |
| primary margin 실패 | **FAIL** |
| calibration/reliability/contested gate 실패 | **INCONCLUSIVE** |
| 데이터 누락 | **INCONCLUSIVE** |

`HYBRID_SUPPORTED`이어도:

- `candidate_status = PROVISIONAL_NOMINEE`
- `approval_status = NOT_APPROVED`
- `evidence_level = HYBRID_AI_HUMAN`
- human inter-rater reliability **없음**
- **AI independence claim 없음**
- test 163 **sealed**

### 6.5 no-candidate branch

`FAIL` 또는 `INCONCLUSIVE`:

- `NO_APPROVED_CANDIDATE`
- **pilot300 fallback**
- test 163 **sealed**
- 1,293으로 자동 변경하지 않음
- 1,940을 exploratory 이유로 승격하지 않음

---

## 7. 실행 순서

1. D-086 manifest·prompt·protocol freeze/hash
2. AI panel 150 calls (3 models × 50 docs)
3. AI outputs JSON validation + hash lock
4. Human calibration sheet 생성 (20 docs, 80 ratings)
5. Human calibration + repeat 수집
6. AI–human calibration gate 계산
7. AI inter-judge / contested gate 계산
8. Gate 통과 시 AI panel primary analysis
9. `HYBRID_SUPPORTED` / `FAIL` / `INCONCLUSIVE`
10. 별도 승인 전 test 163 금지

**중요:** AI panel outputs와 human ratings는 서로를 보지 않는다.  
AI panel outputs는 human calibration 전에 hash로 lock한다.

---

## 8. Artifacts

- 이 protocol
- `reports/provenance/C5_hybrid/manifest.json`
- `reports/provenance/C5_hybrid/ai_inputs/judge_{glm,sonnet,sol}.jsonl`
- `runner/c5_hybrid_build_manifest.py`
- `runner/c5_hybrid_build_ai_inputs.py`
- future: `reports/C5_hybrid_human_calibration_sheet.html`
- future: `reports/provenance/C5_hybrid/ai_outputs/`
- future: `reports/provenance/C5_hybrid/human_ratings.jsonl`
- future: `reports/provenance/C5_hybrid/hybrid_result.json`
- freeze: `reports/provenance/C5_hybrid/freeze.sha256`

---

## 9. 한계

1. **AI panel은 human population이 아니다.** 3 model consensus는 독립 인간 3명이 아니다.
2. **model family correlation** — 같은 pretraining/alignment 편향을 공유할 수 있다.
3. **AI reasons는 post-hoc일 수 있다.** evidence quote로 검증하지만 완전하지 않다.
4. **human calibration도 1명** — human inter-rater reliability는 없다.
5. **20 docs calibration은 작다.** gate를 통과해도 AI-human agreement의 불확실성이 남는다.
6. **AI panel이 human calibration에서 통과해도**, 다른 human population에 일반화된다는 보장은 없다.
7. **test 163은 이 protocol로 열지 않는다.**

---

## 10. D-085와의 관계

- D-085는 **human rating 시작 전** D-086으로 대체한다.
- D-085 file/hash/manifest는 이력으로 보존한다.
- D-085로 human rating을 수집하지 않는다.
- D-085의 50-doc sample·hash·train-prefix flag는 D-086에서 그대로 사용한다.
- D-085의 primary rating sheet는 사용하지 않는다. D-086 human calibration은 20 docs용 별도 sheet를 쓴다.
