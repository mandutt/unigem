# STT 대규모 학습 타당성 검토 — Sténo급 한국어 STT

- 작성: 2026-11-05 (KST, 2026-11-06 00:01 기준 상태 포함)
- 상태: **검토·의사결정 보조 문서 (결정 등록 아님)**
- 범위: 현재 10시간 reader 실험 이후, **Sténo급 3,000시간 한국어 STT**를 현 자원으로 진행할 수 있는가
- 관련 결정: D-057(제품 경로 komixv2/whisper), D-071(V2 gate PASS), D-073(matched-budget), D-075(domain/length controls), D-077(step-matched B3-long)
- 관련 보고서: `W2B_b3long_stepmatched_plan.md`, `W2B_domain_length_controls.md`, `W2B_DOMAIN_LENGTH_3AI_SYNTHESIS.md`, `EXTERNAL_REVIEW_W2B_DOMAIN_LENGTH_2026-11-05.md`

> 이 문서는 **대규모 학습을 승인하거나 시작하는 문서가 아니다.** 현재 자원·비용·데이터·RAM을 정리하고, 지금 할 일과 별도 프로젝트로 분리할 일을 구분하기 위한 검토서다.

---

## 0. 결론 요약

1. **현 시점 자원으로 Sténo급 3,000시간 학습은 무리다.**
   - 현재 환경: CPU-only(Ryzen 5 7600 6C/12T), RAM 15.6GB, C: 약 71GB 여유, D: 약 332GB 여유, GPU 없음.
   - Sténo급은 3,000시간급 데이터, 상위층 fine-tune/LoRA, 13-state mix, 대형 wordpiece reader, 4-gram LM, 40~100 GPU-hour, 1TB급 저장이 필요한 **별도 프로젝트**다.
   - FLAC을 쓰면 raw audio는 345GB → 170~220GB로 줄지만, **feature cache 2.1TB(4-layer)/6.8TB(13-state)** 문제는 해결되지 않는다.

2. **Sténo는 “frozen EG2”가 아니다.**
   - Sténo: 3,205시간, **상위 10~12층 fine-tune**, 13-state learned softmax mix, 30k wordpiece, 4-gram LM.
   - FLEURS fr: **WER 12.8% greedy / 9.7% + LM**.
   - 따라서 “frozen만으로 Sténo급”은 Sténo보다 더 어려운 조건이다. frozen도 데이터·readout·LM이 받쳐주면 경쟁력이 있지만, **10시간·9M 문자 reader·LM 없음**으로는 불가능하다.

3. **현재 10시간 실험의 연장으로 Sténo급을 기대하면 안 된다.**
   - 현재 best: B3-nat **26.33%** dev / B3 **26.23%** test (Kspon eval_clean).
   - LoRA 10시간의 현실적 기대: **23~26% CER**, 즉 1~3%p 개선.
   - 제품 기준(≤15%)과 Sténo급(프랑스어 9.7% WER)에는 모두 미달.

4. **당장의 순서는 유지한다.**
   - step-matched B3-long 완료 → LoRA B1/B2 구현·smoke → 10시간 LoRA 결과 확인.
   - 대규모는 **100시간 → 960시간 → 3,000시간**의 단계적 gate로 분리하고, 각 단계의 데이터·저장·GPU 예산을 별도 승인한다.

5. **제품 STT 경로는 계속 komixv2/whisper다(D-057).**
   - EG2 기반 STT는 연구 트랙이며, 대규모 학습을 시작해도 제품 채택은 별도 결정이다.

---

## 1. 현재 위치 (작성 시점)

### 1.1 진행 중인 실험

`b3long_sm_v2_s42` — step-matched B3-long (D-077)

- `batch=2`, `grad_accum=2` → **928 steps/epoch × 12 = 11,136 steps**
- B3-nat 11,196 steps 대비 0.54%
- 작성 시점: **epoch 6/12**, dev CER **0.2913**
- epoch별: 0.3231 → 0.3121 → 0.3014 → 0.3019 → 0.2928 → **0.2913**
- 최종 결과 아님. B3-nat 0.2633 대비 아직 미달.

### 1.2 현재 확정 비교

| Arm | 추가 데이터 | 총 steps | final dev CER |
|---|---|---:|---:|
| B0′-12 | 없음 | 3,576 | 0.370084 |
| B3-12 balanced | Kspon short 0.5–8s | 11,196 | 0.268214 |
| B3-nat | Kspon short 0.5–8s | 11,196 | **0.263314** |
| B3-long | Kspon long 8–16s | 5,568 | 0.283946 |
| B3-zeroth-long | Zeroth long 8–16s | — | 0.365571 |
| **b3long_sm** | Kspon long, step-matched | **11,136** | 진행 중 |

Bootstrap 기준:
- `B3-nat − B3-long`: **−2.0632%p** CI [−2.9625, −1.1861]
- `B3-long − B3-zeroth-long`: **−8.1625%p** CI [−9.2063, −7.1645]
- `B0′ − B3-long`: **+8.6138%p** CI [+7.6628, +9.5939]
- `B0′ − B3-zeroth-long`: +0.4513%p CI [−0.2087, +1.1278] (비유의)

→ domain 효과는 강하고, length 효과는 step confound로 미확정. step-matched 결과가 그 분리를 시도하는 중이다.

---

## 2. Sténo 사양과 한국어 재현 조건

| 항목 | Sténo (프랑스어) | 한국어 Sténo급 재현에 필요한 것 |
|---|---|---|
| 데이터 | **3,205시간** | 3,000시간+ 한국어 음성·전사, 도메인 다양성 |
| 오디오 타워 | EG2 audio tower, **1~9층 frozen, 10~12층 fine-tune** | 상위 2~3층 fine-tune 또는 3~10M LoRA |
| 특징 결합 | **13-state learned softmax mix** | 13-state mix 구현 |
| Reader | 6 blocks(110M) / 10 blocks(163M), width 768 | 20~163M급 reader |
| 출력 | **Gemma wordpiece 30,002** + 텍스트 임베딩 초기화 | 한국어 wordpiece + Gemma embedding 초기화 |
| LM | 4-gram LM | 한국어 4-gram, top-N rescoring |
| FLEURS fr | **WER 12.8% greedy / 9.7% + LM** | 직접 비교 불가. 한국어 목표는 별도 측정 |
| 학습 | L40S **38 GPUh + 17 GPUh** | 40~100 GPUh (튜닝·재실행 포함) |

**핵심:** Sténo의 성능은 단일 요소가 아니라 **데이터 3,205h + 상위층 적응 + 13-state mix + wordpiece + LM**의 조합이다. 하나만 바꿔서 재현할 수 없다.

---

## 3. 데이터 확보 가능성

### 3.1 후보

| 소스 | 규모 | 접근·주의 |
|---|---:|---|
| **KsponSpeech** | **960시간** | AI Hub 신청·라이선스. 현재 `KsponSpeech_05.zip` 일부(15.6GB)만 보유 |
| **AI Hub 한국어 음성/회의/전화/소음** | 수백~수천 시간 | 데이터별 신청·라이선스, 상업 이용 조건 확인 |
| **Zeroth-Korean** | 51.6시간 | OpenSLR 공개 |
| **Common Voice Korean** | 수십~100시간급 | 공개, 품질 편차 |
| **FLEURS ko train** | 약 10시간 | 공개, 낭독체 |
| **KSS / LibriVox Korean** | 10시간 내외~ | 라이선스·정렬 확인 |

### 3.2 판단

- **용량 기준으로는 3,000시간 조달 가능성이 있다.** Kspon 960h + AI Hub 대화/회의/전화 + Zeroth/Common Voice 조합.
- 그러나 **“바로 다운로드”는 아니다.**
  - AI Hub 데이터별 신청·라이선스, 상업 이용 가능 여부 확인
  - Kspon 전사 규약·잡음 마커 정규화
  - 화자·도메인 다양성 확보
  - 수백 GB 저장과 수일~2주 전처리
- **3,000시간은 “데이터가 존재한다”와 “지금 학습 가능하다”가 다르다.** 현재는 후자가 아니다.

---

## 4. 저장 공간 — FLAC과 feature cache는 별개

### 4.1 3,000시간 기준

| 형태 | 예상 용량 | 비고 |
|---|---:|---|
| WAV PCM16 16kHz mono | **345GB** | 32KB/s |
| **FLAC** | **170~220GB** | 음성 50~65% 압축, 무손실 |
| Opus 24kbps | 약 32GB | 손실, 학습 품질 위험 |
| mel 128×100fps fp16 | 약 276GB | tower 입력 전 |
| **feature cache 4-layer fp16** | **약 2.1TB** | 현재 4h≈2.8GB 기준 |
| **13-state 전부 cache** | **약 6.8TB** | Sténo식 13-state mix |
| feature cache int8 | 약 1.05TB | 정확도 검증 필요 |
| feature cache PCA 512 | 약 1.05TB | 정보 손실 위험 |
| feature cache PCA 256 | 약 0.53TB | 손실 큼 |

### 4.2 해석

- **FLAC은 raw audio만 줄인다.** 345GB → 170~220GB.
- **2TB는 feature cache**이므로 FLAC과 무관하다.
- Sténo식 13-state를 전부 캐시하면 **6.8TB**로 더 커진다.
- 따라서 Sténo 방법을 하려면 **FLAC raw audio + on-the-fly tower forward**가 맞다.
  - 저장: 170~220GB
  - 대신 매 step tower forward 비용 발생
  - 13-state도 forward에서 바로 얻음
- frozen reader-only라면 feature cache가 유리하지만, 3,000시간은 너무 크다.
  - 1,000시간: 4-layer fp16 약 0.7TB
  - int8/PCA 512: 약 0.35TB
  - mel cache: 100fps 기준 약 92GB/1,000h

### 4.3 현재 디스크

- C: 약 **71GB** 여유
- D: 약 **332GB** 여유
- 3,000시간 FLAC은 D:에 들어가지만, Kspon 원본·체크포인트·다른 데이터를 포함하면 빠듯하다.
- 학습 시에는 **NVMe 또는 Modal Volume 1TiB**가 안전하다.
- D: 외장 HDD에서 2TB feature cache를 random access하는 것은 I/O 병목이 크다.

---

## 5. GPU·학습 시간·비용

### 5.1 Sténo 기준

- Sténo: L40S **38 GPUh + 17 GPUh = 55 GPUh**
- 한국어 재현: **40~60 GPUh** 기본, 튜닝·재실행 포함 **60~100 GPUh**
- L40S $1.95/h: **$120~200**
- A100-40GB $2.10/h: **$125~210**
- wall time, L40S 1장: **2~4일**
- wall time, 2~4 GPU: **1~2일**
- 데이터 전처리·feature: **수일~2주** (CPU/IO 병목)
- 저장: **1TB+** 권장

### 5.2 현 자원과의 비교

| 항목 | 현 자원 | Sténo급 필요 |
|---|---|---|
| GPU | 없음(CPU only) | L40S/A100 40~100 GPUh |
| RAM | 15.6GB | 학습은 GPU 메모리, 데이터 로더는 RAM |
| 저장 | C 71GB / D 332GB | 1TB+ 권장 |
| 예산 | Modal $30 크레딧 | $120~200+ |
| 데이터 | 10시간 | 3,000시간+ |
| 구현 | LoRA 미구현 | top-layer FT/LoRA, 13-state, wordpiece, LM |

**결론:** 10시간 LoRA는 가능하지만, Sténo급 3,000시간은 **현 자원·예산·데이터·구현 모두 별도 프로젝트**다.

---

## 6. RAM — 가중치 파일과 실제 점유는 다르다

### 6.1 실측

| 구성 | 값 | 근거 |
|---|---:|---|
| EG2 오디오 타워 Q8 단독 | 로드 **+431MB**, peak **483/551/620MB** (5/16/30s) | `logs/A7_audio_q8_latency.json` |
| whisper-turbo q4_k | peak **969MB** (90s) | `eg2-transcribe-bench/long_ko_news_turbo.json` |
| komixv2 CT2 int8 | 파일 **739MB**, RAM **0.9~1.2GB 추정** | 파일 확인, 동일 조건 RAM 미실측 |

### 6.2 Sténo급 구성

| 구성 | 예상 peak RAM |
|---|---:|
| 단일 타워 + 110M reader(int8) + wordpiece | **0.75~0.9GB** |
| 같은 구성, reader fp32 | **1.1~1.4GB** |
| base 타워 + adapted 타워 | **1.2~1.8GB** |
| 위 + 4-gram LM | **1.5~2.5GB** |
| 현재 9.18M 문자 reader + 타워 | **0.5~0.65GB** |

**중요:** komix 739MB·whisper 453MB는 **파일 크기**다. 실제로는 런타임·토크나이저·피처·디코더·스레드 오버헤드가 붙는다. whisper는 453MB 파일이 **969MB peak**까지 간다.

---

## 7. 4-gram LM을 SSD에 두는 방법

- **가능하다.** 단, “SSD에서 직접 연산”이 아니라 **mmap + demand paging**이다.
- KenLM은 **`.bin`**을 mmap하면 private heap 복사 없이 file-backed page cache로 동작한다.
- **ARPA는 피한다.** 파싱·heap 로드가 발생한다.
- RAM이 여유 있으면 OS가 페이지를 캐시하고, 압박 시 회수한다. “SSD 전용 강제”는 안정적으로 불가능하다.
- **콜드 스타트·랜덤 I/O·p95 jitter**가 단점이다. 4-gram은 빔 서치에서 랜덤 접근이 많다.
- 실용안:
  - `build_binary -q 8` 양자화
  - 도메인 pruning
  - **top-N rescoring** (모든 빔을 LM에 넣지 않음)
  - lazy load + idle unload
  - 작은 3-gram fallback
- 우리 D-046에서는 KenLM이 **17.445% vs greedy 17.410%**로 이득이 없고 RTF +39%였다. 한국어 4-gram은 **CER 개선과 콜드/웜 p95를 함께 실측**한 뒤 채택해야 한다.

---

## 8. Frozen으로 Sténo급이 가능한가 — Exa 조사 결과

### 8.1 확인된 사례

| 사례 | 구성 | 결과·의미 |
|---|---|---|
| **EmbeddingGemma 2 Transcribe Reader** | frozen EG2 + 19.6M reader, LibriSpeech 960h, no LM | test-clean **4.21% WER**, test-other **10.42%** |
| **stt-gemma_embedding-2** | frozen EG2 + 13.3M causal head, 960h, 6-gram LM | LibriSpeech 계열에서 경쟁력 있는 WER |
| **Embed2ASR** | frozen EG2 + 9.66M GRU-CTC | LibriSpeech 9.0%, **FLEURS en 24.5%** → frozen ceiling 명시 |
| **Arabic frozen vs adapted** | frozen: 22.6M reader + 4-layer mix + 4-gram LM / adapted: **3.1M LoRA** + 41.5M hybrid reader | frozen은 WER에서 뒤지지만 **CER는 6개 조건 중 5개에서 유의차 없음**; adapted가 더 좋음 |
| **norsk-asr** | 1~11층 frozen, **12층만 fine-tune**, 13-state mix, 83M reader | 부분 fine-tune으로 노르웨이어 CTC |
| **Sténo** | 3,205h, **10~12층 fine-tune**, 13-state mix, 30k wordpiece, 4-gram LM | FLEURS fr **12.8% greedy / 9.7% + LM** |

### 8.2 해석

- **완전 frozen이 불가능한 것은 아니다.** 960시간 LibriSpeech read speech에서 frozen EG2 + 19.6M reader가 **4.21/10.42% WER**를 냈다.
- 그러나 **한국어 Kspon은 전화 구어**이고 현재 데이터는 10시간이다. read speech 960시간과 직접 비교할 수 없다.
- **Sténo 자체는 frozen이 아니다.** 상위층 fine-tune을 한다. 순수 frozen은 더 어려운 조건이다.
- **frozen에서 효과가 있었던 레버:**
  1. 13-state learned softmax mix (마지막 층만 쓰지 않음)
  2. wordpiece head + Gemma 텍스트 임베딩 초기화
  3. 20~80M reader (conv/transformer)
  4. 4-gram/6-gram LM + top-N rescoring
  5. 3~10M LoRA/adapters (base weights는 freeze)
  6. distillation from komix/whisper
- **한국어 기대치(외삽, 실측 아님):**
  - 10시간: 23~26% CER
  - 100시간: 18~23% CER 가능성
  - 960시간 Kspon: 12~18% CER 가능성
  - 3,000시간 + wordpiece + LM + 상위층 FT/LoRA: Sténo급 접근 가능, pure frozen은 WER에서 뒤질 가능성

---

## 9. 선택지

### A. 현재 계획 유지 (권장)

- step-matched B3-long 완료
- LoRA B1/B2 구현 + T4/L4 smoke
- L40S에서 10시간 LoRA **4~8 GPUh**, $10~20
- 목표: 10시간 조건에서 LoRA 효과와 RAM/지연 확인
- **대규모 학습은 시작하지 않음**

### B. 10시간 architecture 실험

- 13-state mix 구현
- wordpiece + Gemma embedding 초기화
- 20M급 reader
- 4-gram LM top-N rescoring
- 예상: 1~3 GPUh, $2~6
- 목적: “데이터가 아니라 구조” 문제를 분리

### C. 100시간 파일럿

- 100시간 선별·전처리
- frozen vs LoRA 비교
- 예상: 5~15 GPUh, $10~30
- 저장: feature cache 0.07TB(4-layer), raw FLAC ~6~7GB
- 목적: 데이터 scaling 기울기 확인

### D. 960시간 Kspon

- Kspon 전체 960시간
- FLAC + on-the-fly 또는 int8/PCA cache
- 예상: 20~50 GPUh, $40~100
- 저장: FLAC ~55~70GB, feature cache 0.7TB
- 목적: 한국어 frozen/부분 FT의 현실적 상한 확인

### E. 3,000시간 Sténo급

- Kspon 960h + AI Hub + 공개 코퍼스
- top-layer FT/LoRA + 13-state + wordpiece + LM
- 예상: 60~100 GPUh, $120~200+
- 저장: FLAC 170~220GB + feature/on-the-fly
- **현 자원·예산으로는 별도 프로젝트, 지금 시작하지 않음**

---

## 10. 권고

1. **지금은 A.**
   - 현재 10시간 실험을 끝내고 LoRA smoke까지 간다.
   - 대규모 학습을 지금 시작하지 않는다.

2. **대규모는 단계적 gate로 분리한다.**
   - 10시간 → 100시간 → 960시간 → 3,000시간
   - 각 단계에서 **CER 개선, GPU 시간, 저장, 데이터 라이선스**를 확인한 뒤 다음 단계 승인.

3. **Sténo급을 목표로 하면 frozen을 고집하지 않는다.**
   - 상위 2~3층 fine-tune 또는 3~10M LoRA.
   - 13-state mix, wordpiece, LM을 함께 구현.
   - Sténo도 frozen이 아니라 부분 fine-tune이다.

4. **저장은 FLAC + on-the-fly를 기본으로 한다.**
   - 3,000시간 feature cache(2.1TB/6.8TB)를 만들지 않는다.
   - frozen readout 실험만 int8/PCA cache를 소규모로 사용.

5. **제품 경로는 komixv2/whisper 유지(D-057).**
   - EG2 대규모 학습은 연구 트랙이며, 제품 채택은 별도 gate다.

---

## 11. 미해결 질문

1. 한국어 wordpiece 30k와 Gemma embedding 초기화가 실제로 char reader보다 얼마나 좋은가?
2. 13-state mix가 현재 F-C concat보다 Kspon에서 유의하게 좋은가?
3. 4-gram LM이 한국어 Kspon에서 CER/RTF를 정당화하는가? (D-046은 부정적)
4. frozen 960시간 Kspon의 CER은? (현재 직접 측정 없음)
5. Kspon 960h + AI Hub 데이터의 **상업 이용 라이선스**가 확보되는가?
6. 3,000시간 FLAC/feature 파이프라인의 실제 I/O 병목은?
7. komixv2의 동일 조건 peak RSS는? (현재 파일 크기만 확인)

---

## 12. 참고 자료

### 내부
- `reports/W2B_b3long_stepmatched_plan.md` — D-077 사전등록
- `reports/W2B_domain_length_controls.md` — B3-long/B3-zeroth-long 결과
- `reports/W2B_DOMAIN_LENGTH_3AI_SYNTHESIS.md` — 3-AI 종합
- `reports/EXTERNAL_REVIEW_W2B_DOMAIN_LENGTH_2026-11-05.md` — 자기완결형 검토요청서
- `reports/C8_c2a1_cer.md` — Notesoop/komix/whisper 비교
- `reports/D5_beta_pilot.md` — Sténo 비교
- `reports/EXTERNAL_REVIEW_2026-11-04.md` — Sténo·EG2 논문 정리
- `logs/A7_audio_q8_latency.json` — 오디오 타워 RAM/RTF
- `C:/Users/mandu/hermes-made/eg2-transcribe-bench/REPORT.md` — whisper/Notesoop 메모리
- `docs/decisions.md` — D-057, D-071, D-073, D-075, D-077

### 외부 (Exa 검색)
- EmbeddingGemma 2 Transcribe Reader — https://huggingface.co/mlboydaisuke/EmbeddingGemma-2-Transcribe-Reader
- stt-gemma_embedding-2 — https://huggingface.co/harshit2312/stt-gemma_embedding-2
- Embed2ASR — https://github.com/tc3oliver/embed2asr
- Frozen vs adapter Arabic study — https://arxiv.org/html/2610.28673
- norsk-asr — https://huggingface.co/ahdrage/norsk-asr
- EmbeddingGemma 2 소개 — https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/

---

## 13. 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-11-05 | 최초 작성. Sténo급 데이터·GPU·저장·RAM·LM·frozen 방법론 검토 |
