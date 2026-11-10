# C5 F5.0 — Human-only Evaluation Protocol v0.1 (2026-11-10)

- 상태: **DRAFT / HUMAN_ONLY / NO_EXTERNAL_API**
- 목적: A1 checkpoint 3개의 abstract summary 품질을 사람 1인이 비교
- test 163: **sealed**
- 외부 LLM/API: **사용하지 않음**

## 1. 왜 human-only인가

- 현재 다른 API 사용이 곤란하다.
- LLM judge는 일관성이 높지만, abstractness와 “중요 정보”의 가치는 인간 기준과 다를 수 있다.
- 이번 평가는 제품 승인이 아니라 **checkpoint ranking + rubric calibration**이다.
- 단일 평가자이므로 inter-rater reliability는 없고, **SINGLE_RATER_EXPLORATORY**로 표기한다.

## 2. 비교 시스템

| code | system | 역할 |
|---|---|---|
| P | `A1 pilot300` | safety baseline (grounded/EOS 100%) |
| H | `A1 full 1,940` | best abstractness (copy8 .6434, novel4 .1630) |
| F | `A1 full 2,586` | final-epoch regression control (copy8 .7354, novel4 .1154) |

- HTML 시트에서는 시스템 이름을 숨기고 문서별로 **A/B/C**로 무작위 배치한다.
- 평가가 끝난 뒤 `human_review_key.json`으로 decode한다.
- target summary는 화면에 표시하지 않는다. target을 보여주면 평가가 anchor된다.

## 3. 표본

- **20 documents × 3 systems = 60 summaries**
- pilot300 val161의 실패 유형을 기준으로 stratified:
  - high copy8 5
  - low slot preservation 4
  - high repetition 4
  - low char F1 3
  - middle/random 4
- 같은 문서에 대해 세 시스템을 모두 평가한다.
- test 163은 사용하지 않는다.

## 4. 평가 rubric

각 summary에 대해 세 축을 1~3점으로 평가한다.

### Overall

| 점수 | 기준 |
|---:|---|
| 3 | 추상 요약으로 사용 가능. 핵심을 자기 말로 재구성하고 읽기 좋다. |
| 2 | 부분적으로 사용 가능. copy/누락/반복이 있지만 핵심은 남아 있다. |
| 1 | 사용하기 어렵다. 거의 복사, 핵심 누락, 반복, 또는 사실 오류가 크다. |

### Abstractness

| 점수 | 기준 |
|---:|---|
| 3 | 원문 표현을 재구성한 추상 요약 |
| 2 | 추출과 추상이 섞여 있음 |
| 1 | 원문 문장을 거의 그대로 복사 |

### Factual preservation

| 점수 | 기준 |
|---:|---|
| 3 | 원문의 핵심 사실을 정확히 보존 |
| 2 | 일부 누락/약화가 있으나 치명적이지 않음 |
| 1 | 핵심 사실 누락, 왜곡, 또는 원문에 없는 내용 |

### Flags

- `copy_heavy`
- `key_omission`
- `unsupported_fact`
- `repetition`

## 5. 블라인드와 순서

- 문서별로 A/B/C 시스템 순서를 무작위화한다.
- 시스템 이름, checkpoint 번호, 점수, 다른 시스템의 결과를 표시하지 않는다.
- 한 문서의 세 요약을 모두 본 뒤 평가한다.
- 평가 중 이전 문서로 돌아갈 수 있으나, 다른 시스템 결과를 참고하지 않는다.

## 6. 분석 계획

- per-system mean: overall / abstractness / factual preservation
- per-document paired difference:
  - H − P
  - H − F
  - P − F
- bootstrap 95% CI: 10,000 resamples, seed **20261110**
- flag rate: copy_heavy / key_omission / unsupported_fact / repetition
- qualitative notes: 문서별 이유
- single rater이므로 ICC/κ는 계산하지 않는다.

## 7. 판정 규칙 (사전 고정)

```text
SUPPORTS_1940:
  mean_overall(H) - mean_overall(P) >= +0.5
  AND mean_overall(H) - mean_overall(F) >= +0.5
  AND mean_factual(H) >= mean_factual(P) - 0.3
  AND H wins/ties P on >= 12/20 docs

SUPPORTS_PILOT300:
  mean_overall(P) - mean_overall(H) >= +0.5
  AND mean_overall(P) - mean_overall(F) >= +0.5

otherwise:
  INCONCLUSIVE
```

- `SUPPORTS_1940`도 **제품 승인이 아니다**. 다음 실험의 방향 결정일 뿐이다.
- factual preservation이 크게 낮으면 overall이 높아도 1940을 선택하지 않는다.

## 8. 산출물

- review sheet: `reports/C5_F5_0_human_review.html`
- sample: `reports/provenance/C5_f5_0/human_review_sample.json`
- blinding key: `reports/provenance/C5_f5_0/human_review_key.json`
- ratings export: 사용자가 `f5_human_ratings.json`으로 다운로드
- analysis: 추후 `runner/c5_f5_0_human_analysis.py`

## 9. DoD

- [ ] 20 documents × 3 systems = 60 ratings
- [ ] export JSON 수령
- [ ] per-system/paired analysis
- [ ] 판정 `SUPPORTS_1940` / `SUPPORTS_PILOT300` / `INCONCLUSIVE`
- [ ] test 163 미사용 확인
