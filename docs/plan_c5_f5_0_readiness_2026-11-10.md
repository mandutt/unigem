# C5 F5.0 — Readiness Audit + Pilot Design (2026-11-10)

- 상태: **READINESS_AUDIT_COMPLETE / PILOT_DESIGN_DRAFT**
- 범위: F5 abstract summary, native baseline 우선
- 학습: **없음**
- test 163: **sealed**
- P1: 사용하지 않음

## 1. 결론

F5 추상 요약은 **Korean pilot으로 진행 가능**하다.

- F5 clean 1,617건, split 1,293/161/163이 존재한다.
- target은 LLM 생성 3~5문장 추상 요약이며, 사람 50건 검토에서 **2.94/3, 수용 100%**였다.
- `A1-native T5Gemma2 + decoder LoRA`의 **pilot300 fallback**이 val161에서
  **char F1 0.6576, grounded 161/161, EOS 161/161, repeated4 0.0554**로
  F5 pilot 기준을 통과했다.
- F5.0 smoke에서 pilot300 adapter를 실제로 로드해 val5를 재현했고,
  **char F1 0.62724, grounded 1.0, EOS 1.0, new slot 0**을 확인했다.
- 그러나 **full train 2 epoch는 grounded gate를 통과하지 못했다.**
  pilot300은 제품 후보가 아니라 **fallback baseline**이다.
- **다국어 준비는 미완료**다. 현재 F5 데이터는 한국어 단일 언어이며,
  다국어 요약 target이 없다. 다국어 성능은 아직 주장할 수 없다.
- EG2 bridge(B2)는 F1 0.3349, grounded 18%로 F5-native보다 크게 낮다.
  F5.1은 **bridge 없이 native baseline만** 사용한다.

## 2. 데이터 audit

### 2.1 F5 clean

| 항목 | 값 |
|---|---|
| 파일 | `data/external/f5_pairs_v3_clean.jsonl` |
| rows | **1,617** |
| split | **train 1,293 / val 161 / test 163** |
| target | `llm_summary3to5` |
| target 문장 수 | 평균 **3.68** |
| passage chars | mean 1,235.9 / median 1,229 |
| summary chars | mean 332.4 / median 325 |
| compression | **0.269** |
| summary 8-gram copy overlap | mean **0.49** / median 0.479 / max 0.976 |
| Korean char ratio (passage) | median **0.666**, min 0.498 |
| rows with Korean ratio < 0.2 | **0** |
| rows with Latin ratio > 0.5 | **0** |

### 2.2 언어 판정

- 현재 F5는 **한국어 단일 언어**다.
- 영어 고유명사·숫자는 섞여 있지만, 영어/중국어/일본어 요약 target은 없다.
- T5Gemma2의 `summarize: ` prefix는 영어지만, 출력 target은 한국어다.
- 따라서 **“다국어 abstract summary가 된다”는 현재 증거 없음**.
  모델 tokenizer가 다국어를 지원한다는 사실과, 다국어 요약 성능은 별개다.

### 2.3 target 품질

- 사람 50건 v3 검토: **F5 2.94/3, 수용 100%** (`C10_gdata_pilot`).
- 단, target은 LLM(DeepSeek-V4.1-Flash-1017) 생성 요약이며,
  독립 human gold가 아니다.
- 8-gram copy 0.49는 완전 추상 요약이 아니라 **부분 추출성**이 남아 있음을 뜻한다.
  추상성 평가는 char F1만으로 부족하다.

## 3. 모델·checkpoint audit

### 3.1 Base

| 항목 | 값 |
|---|---|
| model | `data/models/t5gemma-2-270m-270m` |
| 규모 | 270M, 1.5GB |
| encoder/decoder | 18/18 layers, hidden 640 |
| vocab | 262,144 |
| runtime | CPU, torch |
| vision tower | F5에서 제거 (`--keep-vision` 없음) |

### 3.2 A1 native baseline

| 항목 | 값 |
|---|---|
| 방식 | T5Gemma2 native encoder-decoder + decoder attention LoRA |
| LoRA | q/k/v/o, r8 alpha16 dropout0.05 |
| prefix | `summarize: ` |
| fallback adapter | `data/models/f5_t5gemma2_lora/pilot300_lr2e4_prefix.pt` (5,998,227 bytes) |
| full adapter | `data/models/f5_t5gemma2_lora/full_2ep/adapter.pt` (5,994,111 bytes) |
| checkpoint | pilot300 + full train 647/1,293/1,940/2,586 |

### 3.3 val161 실적

| checkpoint | char F1 | grounded | new slot | EOS | repeated4 | slot preservation | gate |
|---|---:|---:|---:|---:|---:|---:|---|
| **pilot300 (fallback)** | **0.657580** | **161/161** | **0** | **161/161** | **0.05535** | 0.45583 | **PASS** |
| full 647 | 0.669853 | 155/161 | 6 | 160/161 | 0.06840 | 0.48729 | FAIL |
| full 1,293 | 0.665946 | 159/161 | 2 | 161/161 | 0.05866 | 0.45705 | FAIL grounded |
| full 1,940 | **0.682278** | 158/161 | 4 | 161/161 | 0.05138 | 0.47610 | FAIL grounded |
| full 2,586 | 0.668982 | 159/161 | 3 | 161/161 | 0.04450 | 0.41882 | FAIL grounded |

- full train에서 D-083 gate를 통과한 checkpoint는 **없음**.
- `pilot300`은 fallback이며 제품 승격이 아니다.
- `slot_preservation`은 0.42~0.49로 낮다. **사실 보존은 미해결**이다.
- `grounded`는 신규 slot 없음만 검사한다. 완전한 사실성 지표가 아니다.

### 3.4 다른 시스템

| system | char F1 | grounded | EOS | repeated4 | 판정 |
|---|---:|---:|---:|---:|---|
| A0 extractive | 0.6111 | — | — | — | 비교 기준, 추상 요약 아님 |
| A2-null EOS | 0.1277 | 0/161 | 9.94% | 0.8695 | FAIL |
| zero-shot T5Gemma2 | 0.2333 | — | 1.86% | 0.8383 | 심한 반복, reference only |
| B2 bridge full | 0.3349 | 18.01% | 60.25% | — | FAIL |
| B2 layer12 | 0.3464 | 21% | 60% | — | FAIL |

**해석**: F5-native A1은 작동하지만, EG2 bridge(B2)는 현재 F5 제품 경로가 아니다.
F0 adapter/LoRA와 A1 decoder LoRA는 **다른 실험**이다.

## 4. F5.0 smoke 재현

실행:

```text
runner/c5_a1_lora.py --mode eval --eval-limit 5 \
  --adapter data/models/f5_t5gemma2_lora/pilot300_lr2e4_prefix.pt \
  --prefix "summarize: " --eval-max-new 448
```

결과:

| metric | val5 |
|---|---:|
| char F1 | **0.62724** |
| grounded | **1.0** |
| new slot micro | 0.0 |
| EOS | 1.0 |
| repeated4 | 0.10042 |
| slot preservation mean | 0.32381 |
| gen len mean | 167.4 |

- 기존 pilot300 val5 **0.6272**와 일치한다.
- adapter load, prefix, generation path가 재현됨을 확인했다.
- val5는 full val161의 대체가 아니다. **readiness smoke**일 뿐이다.

## 5. F5.1 pilot design

### 5.1 목적

F5 abstract summary의 **Korean native baseline**을 val161에서 재현하고,
자동 지표 + 사람 rubric으로 추상성/사실성을 평가한다.
F0 adapter/LoRA와 EG2 bridge는 **이 단계에 넣지 않는다.**

### 5.2 systems

| id | system | 역할 |
|---|---|---|
| S0 | A0 extractive | 추출형 참조 |
| S1 | zero-shot T5Gemma2 | 학습 없는 참조, 반복/불안정 확인 |
| S2 | **A1 pilot300** | **주 baseline** |
| S3 | A1 full 1,940 | 진단용; grounded 실패로 후보 아님 |
| — | B2 / EG2 bridge | **F5.1 제외** |

### 5.3 split / generation

- val **161**만 사용한다.
- test **163은 계속 sealed**.
- prefix `summarize: `, `max_new=448`, 기존 A1 eval 설정과 동일.
- greedy/기존 decoding 설정을 변경하지 않는다.
- checkpoint: 모델·adapter SHA256 기록. 학습 없음.

### 5.4 metrics

자동:

- char F1
- grounded / new slot (micro, macro)
- EOS
- repeated 4-gram
- distinct-2
- generation length
- slot preservation
- 8-gram copy overlap
- novel 4-gram ratio (원문에 없는 4-gram 비율)
- compression ratio

사람:

- 40~50건 stratified sample
- 3점 rubric: **abstractness / factual preservation / readability**
- “추출 copy”와 “사실 오류”를 분리 기록

### 5.5 pilot gate (제안, 동결 전)

F5.1은 confirmatory가 아니라 **pilot**이므로 다음은 제품 gate가 아니다.

```text
artifact consistency (재생성 없음):
  existing pilot300 val161 metrics:
    char_F1 == 0.6575798
    grounded >= 0.99
    EOS >= 0.95
    repeated4 <= 0.06

human:
  mean rubric >= 2.5 / 3
  factual-error rate reported separately
```

- gate를 통과해도 **제품 승격 아님**.
- val161을 다시 생성하지 않는다. 기존 `pilot300_val161/predictions.jsonl`과 `metrics.json`을 사용한다.
- gate 실패 시 bridge로 가지 않고, 원인을 native data/decoding/target 품질로 분리한다.
- gate 값은 F5.1 freeze 전에 사용자 승인을 받는다.

### 5.6 다국어 확장

현재 데이터로 다국어를 평가할 수 없다. F5.1과 별도로 **F5-ML**이 필요하다.

권장 순서:

1. **Korean + English** 50~100 docs each, P0 public data
2. 동일 rubric으로 native baseline 평가
3. 필요 시 Japanese/Chinese 추가
4. 언어별 gate를 분리하고, 한국어 gate를 다국어 gate로 재사용하지 않음

후보 데이터는 XLSum/WikiLingua 등 P0 공개 요약 데이터를 검토하되,
라이선스·언어·target 품질을 먼저 audit한다. AI Hub 022는 한국어 only다.

## 6. DoD

F5.0 완료 조건:

- [x] F5 data/split audit
- [x] target 품질·copy/compression audit
- [x] model/adapter/checkpoint inventory
- [x] val5 smoke 재현
- [x] F5.1 pilot design
- [x] multilingual gap 명시
- [ ] F5.1 existing pilot300 val161 predictions analysis (재생성 없음)
- [ ] F5-ML data audit (별도 작업)

## 7. 권고

**F5.1a: existing pilot300 val161 predictions analysis**를 먼저 한다.

- **재생성 없음**: `reports/provenance/C5_a1/pilot300_val161/predictions.jsonl` 161건 사용
- **재학습 없음**
- test 163 미사용
- 기존 예측에서 abstractness/copy/novel 4-gram/slot preservation 오류 유형 분석
- 이후 사람 40~50건 rubric
- 그 다음에만 **F5-ML**과 **bridge incremental** 검토

재실행이 필요한 경우는 code/adapter/split이 바뀌어 provenance가 달라졌을 때뿐이다. 현재는 해당 없음.

F0 adapter/LoRA는 F5.1에 넣지 않는다. F5-native가 먼저다.

## 8. Artifacts

- audit: 이 문서
- smoke eval: `reports/provenance/C5_f5_0/val5_smoke/eval.jsonl`
  - SHA256 `9a4c2735e85ebf34c6aa6faca1a745c08d59eb431374f2e87ca082e7135cad01`
- pilot300 adapter: `data/models/f5_t5gemma2_lora/pilot300_lr2e4_prefix.pt`
- full adapter: `data/models/f5_t5gemma2_lora/full_2ep/adapter.pt`
- target review: `reports/C10_gdata_pilot.md`
- A1 result: `reports/C5_A1_full_train_2ep_2026-11-07.md`
- A2-null / zero-shot: `reports/C5_A2NULL_VAL161_2026-11-06.md`
- B2: `reports/C5_B2_FULL_2026-11-07.md`
