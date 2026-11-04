# 외부 검토 요청서 — Wave 2B + 2C-short 설계

- 작성일: 2026-11-04
- 검토 기준 커밋: `6b1d720`
- 프로젝트: `mandutt/unigem` (비공개)
- 문서 목적: **프로젝트 이력을 처음 보는 외부 AI가 추가 정보 없이 설계 타당성과 다음 단계를 판단**하도록 하는 자기완결형 검토 요청서
- 주의: 이 문서는 **검토 요청**이지 승인 문서가 아니다. 검토 의견은 사용자 승인 전 구현에 반영하지 않는다.

---

## 0. 검토자에게

당신은 이 프로젝트를 처음 보는 독립 검토자라고 가정한다. 아래 정보만으로 판단하라. 프로젝트 저장소를 읽을 수 있으면 `docs/plan_wave2b_2c_short.md`, `reports/W2A_lite_results.md`, `reports/W2A_lite_cp_d2_lite.md`를 참조해도 되지만, **이 문서만으로도 판단 가능해야 한다.**

특히 다음을 우선하라.

1. 설계가 **과학적으로 반증 가능한가**
2. test 재사용·데이터 누출·선택 편향이 없는가
3. 2B(LoRA)와 2C(short data)를 분리하는 arm 설계가 타당한가
4. CPU·디스크·일정이 현실적인가
5. 더 싸고 빠른 대안이 있는가

칭찬보다 **결함·누락·대안**을 우선해 달라. 불확실하면 “불확실”이라고 명시하라.

---

## 1. 프로젝트 한눈에 보기

### 1.1 목표

EmbeddingGemma 2(EG2)의 **오디오 타워를 재사용**해 다음 과제를 검증하는 연구 프로젝트다.

- F1: 언어 판정
- **F2: STT (이 문서의 대상)**
- F3: 비전 태깅
- F4: 맞춤법 교정
- F5: 메모리 요약
- F6: STT 후처리

F2의 **제품 경로는 기존 komixv2/whisper**로 확정되어 있고, EG2 기반 F2는 **연구 트랙**이다. 따라서 이 문서의 실패가 제품 경로를 바꾸지 않는다.

### 1.2 왜 EG2 오디오 타워인가

- EG2 오디오 타워: **12층 Conformer**, 25 tokens/s, hidden 1024, output_proj 1536.
- 타워는 원 모델 학습 중 frozen이었다.
- 우리는 타워를 고정하고 **작은 CTC reader**만 학습하는 방식으로 6시간 데이터에서 어디까지 가능한지 측정했다.
- 전체 모델·데이터 확장은 예산상 불가능하므로, **상위층 적응(LoRA)** 과 **데이터 분포 보정**의 효과를 분리하는 것이 현실적 next step이다.

### 1.3 하드웨어·데이터 제약

- 로컬 Windows 11, Ryzen 5 7600 6C/12T, RAM 15.6GiB, GPU 없음.
- 학습은 CPU. 장시간 학습은 로컬에서만 한다.
- 무료 VPS 5대가 있으나 **CPU steal이 시간이 지나면 급증**한다(1시간 clean → 2시간 후 17.5%, epoch 4배). 장기 학습에는 쓰지 않는다.
- 데이터 등급: **P0(공개·합성)만** 외부/VPS 허용. 개인 데이터는 로컬 전용.
- 외부 LLM API는 이 실험에 쓰지 않는다.
- 현재 C: 여유 약 **19GB**. Kspon train zip 14~15GB를 받으려면 **25GB 이상 확보**가 필요하다.

---

## 2. 지금까지의 실측 결과

### 2.1 Wave 2A-lite — 4-arm dev

- dev: FLEURS ko **192클립**(≤16초), 참조 **7,861자**.
- 정규화: `normalize_nospace`(공백·구두점 제거).
- 학습: 6.0008h / 2,384클립, seed 42, 동일 reader(4층 Transformer d384, CTC).

| Arm | 입력 | dev CER | errors/ref |
|---|---|---:|---:|
| F-A′ | `aud_out_proj` 1536 | 0.22236 | 1,748 / 7,861 |
| F-B | `aud_h_l11` 1024 | 0.21931 | 1,724 / 7,861 |
| F-C-softmax | 4층 softmax mix 1024 | 0.22211 | 1,746 / 7,861 |
| **F-C-concat** | 4층 concat 4096 | **0.20913** | **1,644 / 7,861** |
| fbank baseline | log-mel 80 + CTC | 0.9812 | 실패(blank plateau) |

- F-C-concat − F-A′ = **+1.323%p (상대 5.95%)**, 문장 paired bootstrap 95% CI **[+0.631, +2.028]%p**.
- seed43 F-C-concat = **0.208116** (seed43 F-A′ 0.2233 대비 **6.8%** 개선).
- seed42/43에서 5% 이상 개선이 재현됨.

### 2.2 Wave 2A-lite — 봉인 test

동결 checkpoint: seed42 F-C-concat.
SHA-256: `258f6ddf84b3f41afc0e88f832946229b3a1319d28cec11cd4a0da40951cb23d`

| 세트 | 평가 수 | CER | blank | errors/ref |
|---|---:|---:|---:|---:|
| **Kspon eval_other** | **2,962 / 3,000** | **0.35143** | 0 | 23,508 / 66,893 |
| **FLEURS ko test** | **318 / 382** | **0.23509** | 0 | 3,126 / 13,297 |

- 16초 초과 및 너무 짧은 발화는 특징 추출에서 제외됨(manifest 행 수와 평가 행 수가 다름).
- Kspon eval_other은 **이미 2A-lite gate에 1회 사용**됐다.
- FLEURS test도 **이미 2A-lite에서 1회 사용**됐다.

### 2.3 CP-D2-lite — Kspon 35.14% 분해

추가 test 평가 없이 기존 decode/manifest만 분석했다.

| 항목 | 결과 |
|---|---:|
| Kspon CER | 0.35143 |
| 상위 1% 발화의 오류 비중 | **4.2%** |
| 상위 5% 발화의 오류 비중 | **15.5%** |
| blank | 0 |
| noisy CER / clean CER | 34.7% / 35.4% |
| duration–CER Pearson | **−0.265** |

길이 구간별:

| duration | Kspon CER | train 비중 | Kspon 비중 |
|---|---:|---:|---:|
| 0–2초 | **46.4%** | 0.17% (4개) | 27.6% |
| 2–4초 | **37.8%** | 3.9% (93개) | 29.6% |
| 4–6초 | 35.2% | 8.9% | 17.3% |
| 6–8초 | 33.2% | 26.6% | 10.3% |
| 8–10초 | 33.0% | 24.9% | 6.7% |
| 10–12초 | 31.6% | 16.8% | 4.6% |
| 12–16초 | **28.6%** | 18.7% | 3.9% |

핵심:

- **train ≤4초 4.1% vs Kspon eval_other ≤4초 57.2%.**
- 오류는 소수 outlier가 아니라 **전반적 음향 혼동**이다.
- **잡음 마커가 주원인이 아니다** — noisy가 clean보다 오히려 낮다.
- Kspon ≥12초 28.6% vs FLEURS test ≥12초 23.1% → 길이를 맞춰도 **약 5.5%p 도메인 갭**이 남는다.

### 2.4 외부 기준

- KsponSpeech 원 논문: 960h급 Transformer에서 **eval-other CER 9.0%**를 보고. 우리는 6h·동결 타워·4층 reader라 직접 비교 불가. [KsponSpeech paper](https://www.mdpi.com/2076-3417/10/19/6936)
- ASR 문헌: 짧은 발화에서 substitution/insertion이 늘고 오류가 커진다. [Chan 2016](https://doi.org/10.1184/r1/6716237), [ESPnet issue #2893](https://github.com/espnet/espnet/issues/2893)
- Kspon 전사 `b/ l/ o/ n/ u/` 정의와 전처리 관행은 원 논문·KoSpeech와 일치. [KoSpeech preprocess](https://sooftware.github.io/kospeech/notes/Preparation.html)

---

## 3. 현재 판단

- 2A-lite dev 기준 **Go 조건은 충족**했다.
- 그러나 Kspon test **35.14%**는 “reader/window unit만 고치면 된다”는 결론을 지지하지 않는다.
- CP-D2-lite는 **짧은 발화 분포 불일치**가 큰 축임을 보여준다.
- 따라서 다음 단계는 **2B 상위층 LoRA 단독**이 아니라 **2B + 2C-short(짧은 발화 데이터)** 로 설계했다.
- 2B/2C의 효과를 분리하기 위해 **4-arm factorial**을 제안한다.

---

## 4. 제안 설계 — 2B + 2C-short

### 4.1 2C-short: Kspon train 4h

- 원천: AI Hub KsponSpeech **train** (datasetkey 123, filekey 50211~50215 중 선별).
- P0 공개 데이터. eval_other/eval_clean은 사용하지 않는다.
- 오디오: 16kHz mono PCM(headerless), 홀수 바이트 1바이트 절단 후 wav.
- 전사: eval_other와 동일한 정리 규칙(`[A-Za-z]{1,2}/` 제거, `(A)/(B)` 첫 대안, `+`·괄호 제거, `ref_raw` 보존).
- 목표 4.0h:

| duration | 비중 | 시간 |
|---|---:|---:|
| 0–2초 | 25% | 1.0h |
| 2–4초 | 35% | 1.4h |
| 4–6초 | 20% | 0.8h |
| 6–8초 | 20% | 0.8h |

- 선별: 빈 전사·1자 이하 제외, 0.5초 미만 제외, 화자당 상한(4h의 10%).
- 기존 6.0008h + short 4h = **10h train**.
- `LengthBalancedSampler`로 epoch당 effective 분포:

| effective | 목표 |
|---|---:|
| ≤4초 | 40% |
| 4–8초 | 30% |
| 8–16초 | 30% |

- 같은 short 클립을 단순 복제하지 않고 unique 4h 유지.

### 4.2 2B-pilot 4-arm

| Arm | 타워 | 데이터 | 목적 |
|---|---|---|---|
| **B0** | 동결 | 기존 6h | 기준선(F-C-concat seed42) |
| **B1** | 10–11층 LoRA | 기존 6h | adaptation 효과 |
| **B2** | 10–11층 LoRA | 6h + short 4h | adaptation + data |
| **B3** | 동결 | 6h + short 4h | data-only 대조군 |

- LoRA: rank 8, alpha 16, dropout 0.0
- 대상: 10–11층의 attention(q/k/v/post)과 FFN 8개 `.linear`
- 0–9층, embedding, `embed_audio`, output_proj는 동결
- reader: 기존 `CTCReader(4096)` + F-C-concat 입력 유지
- optimizer: LoRA LR 1e-4, reader LR 1e-3, AdamW, cosine, warmup 10%, grad clip 5
- batch 2 + grad accumulation 4, threads 6
- checkpoint에 model/LoRA/reader/optimizer/scheduler/epoch/RNG 포함(`--resume`)

### 4.3 평가 세트

| 세트 | 용도 | 크기 |
|---|---|---:|
| Kspon eval_clean 100 | primary dev, early stop | 100발화 |
| FLEURS ko dev | secondary generalization | 192클립 |
| **Kspon eval_clean 2,900** | **새 봉인 test** | 2,900발화 |

- 100 dev는 D-β에서 이미 사용된 dev다. **test가 아니므로 2B dev로 재사용**한다.
- 2,900 test는 `data/c2a1/manifest.json`의 eval_clean 100 ID를 제외한 나머지.
- 검증: 2,900 고유 ID, dev 100과 교집합 0, 2A-lite eval_other와 교집합 0, 학습/2C-short와 교집합 0.
- **FLEURS test는 2A-lite에서 이미 사용했으므로 2B에서 재사용하지 않는다.**
- test는 checkpoint freeze 후 **1회만** 평가.

### 4.4 판정 기준 초안

**Pilot Go**

- B2 Kspon dev 100 CER가 B0 대비 **상대 5% 이상** 개선
- B2 ≤4초 bin CER가 B0 대비 **상대 8% 이상** 개선
- paired bootstrap 95% CI 하한 > 0 (가능한 경우; n=100)
- 미충족 → full run 중단, CP-D2

**Full Go**

- B2 Kspon dev 100 CER가 B0 대비 **상대 10% 이상** 개선
- B2 ≤4초 bin CER가 B0 대비 **상대 10% 이상** 개선
- CI 하한 > 0
- B2 > B1 (short data 이득) AND B2 > B3 (adaptation 이득)
- 최종 test 2,900에서 **상대 10% 이상** 개선, CI 하한 > 0
- 미충족 → No-Go/CP-D2

### 4.5 예산

| 단계 | 예상 |
|---|---:|
| 데이터 선별·test 구축 | 1.5~2일 |
| LoRA/Dataset/Sampler 구현 | 1일 |
| pilot | 0.5일 |
| full B1/B2/B3 | 3~5일 |
| 평가·보고 | 1.5일 |
| **합계** | **7~10일** |

- 디스크: Kspon train zip 14~15GB + short 0.5GB + test 0.3GB → **25GB 이상 필요**.
- 현재 19GB. `cache/wave1.tar.gz` 등 정리 후 진행해야 한다.
- VPS는 사용하지 않는다(steal 지연 발현).

---

## 5. 검토 질문

### Q1. Arm 설계

B0/B1/B2/B3 factorial이 2B와 2C-short의 효과를 분리하는 데 충분한가?

- B3(data-only)를 빼고 B0/B1/B2만 하는 것이 비용 대비 나은가?
- B3를 reader-only로 두는 것이 “데이터 효과”를 제대로 대표하는가?
- B2 > B1, B2 > B3를 모두 요구하는 것이 지나치게 엄격한가?

### Q2. Short 데이터 규모·분포

4h short(0–2 25%, 2–4 35%, 4–6 20%, 6–8 20%)와 effective ≤4초 40%가 적절한가?

- 2h pilot으로 줄이는 것이 나은가, 6h로 늘리는 것이 나은가?
- Kspon train에서 **short 4h를 뽑는 것**이 Kspon eval_other 분포를 대표하는가?
- 0–2초를 25%로 제한한 것이 타당한가? test는 0–2초가 27.6%다.
- 같은 short 클립을 sampler로 40%까지 올리는 것이 과적합 위험을 키우지 않는가?

### Q3. Test 타당성

Kspon eval_clean **2,900**을 새 봉인 test로 쓰는 것이 타당한가?

- 100 dev는 D-β에서 이미 사용됐다. dev 재사용이 test 편향을 만드는가?
- 2A-lite에서 eval_other를 이미 사용했다. 같은 Kspon eval 코퍼스의 다른 split(eval_clean)을 2B test로 쓰는 것이 독립 test로 인정되는가?
- 더 깨끗한 **새 P0 holdout**을 확보해야 하는가? 그 비용 대비 가치가 있는가?
- FLEURS test 재사용 금지가 적절한가?

### Q4. 모델·LoRA

10–11층 LoRA(rank 8, alpha 16)가 적절한가?

- 8–11층 또는 11층만/전체 fine-tune과 비교해야 하는가?
- LoRA를 attention만/FFN만/둘 다 중 어디에 붙이는 것이 좋은가?
- F-C-concat(4096) 입력을 유지하는 것이 좋은가, F-A′(1536)로 단순화해야 하는가?
- wordpiece head를 2B에 포함하지 않은 판단이 타당한가?

### Q5. Gate

Pilot 5%/8%, Full 10%/10% 기준이 적절한가?

- dev 100발화에서 CI를 계산하는 것이 유의미한가? n이 너무 작지 않은가?
- “B2 > B1 AND B2 > B3”를 모두 요구하는 것이 현실적인가?
- 상대 개선과 절대 CER 중 무엇을 주지표로 해야 하는가?
- Kspon eval_clean 2,900 test의 threshold를 10%로 고정하는 것이 과도한가?

### Q6. 누락된 confounder

다음 중 설계에 빠진 것이 있는가?

- Kspon train과 eval_clean의 화자·주제·녹음 환경 차이
- short clip의 전사 길이와 CTC frame 수 제약
- 16초 상한/패딩, 발화 경계, silence trimming
- 전사 정리 규칙이 short clip에 다르게 작용하는 문제
- 데이터 선택 편향(짧은 발화만 선택)
- B3의 feature extraction과 B1/B2의 on-the-fly mel 간 불일치
- CPU thread/seed/수치 재현성

### Q7. 비용·현실성

- 10h·12 epoch를 CPU 6 threads로 3~5일에 끝낼 수 있다는 가정이 현실적인가?
- 25GB 디스크를 확보하기 위한 정리·외부 저장 전략이 충분한가?
- 7~10일 예산이 적절한가, 2h short로 3~5일 pilot만 하는 것이 나은가?

### Q8. 종합 권고

다음 중 어느 쪽이 가장 좋은가?

- **A. 설계대로 4h short + 4-arm pilot 진행**
- **B. 2h short + B0/B1/B2만 먼저 (B3 생략)**
- **C. short data 없이 2B LoRA만 먼저**
- **D. 2C(데이터 확장)만 먼저**
- **E. 새 P0 holdout 확보 전 보류**

권장안과 이유, 그리고 **반드시 고쳐야 할 1~3개**를 적어 달라.

---

## 6. 답변 형식

아래 형식으로 답해 달라.

1. **권장 결론:** A/B/C/D/E 중 하나
2. **Q1~Q8:** 각 1문단
3. **Must-fix:** 시작 전 반드시 고칠 것 1~3개
4. **Optional:** 있으면 좋은 것
5. **잘못된 전제:** 이 문서에서 사실과 다르거나 검증이 필요한 것
6. **신뢰도:** high/medium/low

---

## 7. 재현 정보

- 저장소: `mandutt/unigem` (비공개), branch `main`
- 검토 기준 커밋: `6b1d720`
- 실행 정본: `docs/plan_wave2b_2c_short.md`
- 2A-lite 결과: `reports/W2A_lite_results.md`
- CP-D2-lite: `reports/W2A_lite_cp_d2_lite.md`, `reports/W2A_lite_cp_d2_lite.json`
- 동결 checkpoint: `data/wave2a_lite/frozen/w2a_fc_concat_s42.best.pt` (sha256 `258f6ddf84b3f41afc0e88f832946229b3a1319d28cec11cd4a0da40951cb23d`)
- Test provenance: `reports/provenance/W2A_lite/test_run.json`
- 학습 데이터: `data/wave1/manifest.jsonl` (2,384클립/6.0008h)
- dev: `data/wave2a_lite/fleurs_dev.jsonl` (226행, ≤16초 192)
- 기존 test: `data/wave2a_lite/kspon_eval_other.jsonl` (3,000; 2A에서 사용 완료)
- 새 test 예정: `data/wave2b/test/kspon_eval_clean_2900.jsonl` (미생성)
- `w1_extract.py`: 16초 초과/0.5초 미만을 제외하므로 manifest 행 수와 평가 수가 다르다.
- 정규화: `eval/normalize.py::normalize_nospace` — 공백·구두점 제거 후 CER.

### 7.1 AM-6 이행 표

| 요구 | 이행 |
|---|---|
| 4-arm 동일 조건 | 이행 |
| dev/test 분리 | 이행 |
| seed 반복 | seed42/43 |
| positive control | PASS(1h overfit 0.1161) |
| per-domain/error/blank/vocab/fbank | 보고 |
| test 1회 | 2A-lite에서 이행 |
| WER/공백 포함 CER | 미산출(예측 공백 없음) |
| 13-state/wordpiece/40h/LoRA | 2B/2C에서 일부 착수 제안 |

---

## 8. 검토자가 특히 의심해야 할 지점

1. **Kspon eval_clean 2,900이 정말 독립 test인가** — eval_other와 같은 60명 화자, 같은 코퍼스다.
2. **100 dev의 선택 편향** — D-β에서 이미 사용된 100발화를 dev로 재사용한다.
3. **short data 선택 편향** — Kspon train에서 짧은 발화만 골라 train 분포를 인위적으로 바꾼다.
4. **B3의 data-only control이 정말 같은 조건인가** — frozen feature extraction과 on-the-fly mel의 차이.
5. **10% gate가 6h 데이터에서 현실적인가** — Kspon 960h baseline 9.0%와 우리 35%의 간극.
6. **CPU 7~10일 예산** — full 3-arm 학습이 실제로 가능한가.
