# STT 연구 트랙 — 진행 상황 및 동결 기록

- 작성: 2026-11-06 (KST)
- 상태: **FROZEN / HOLD** (D-079)
- 범위: EG2 기반 F2 STT 연구 트랙. F1 언어 판정, F3 이미지 태깅, F4/F5/F6 등 다른 트랙은 이 동결에 포함되지 않는다.
- 제품 STT 경로: **komixv2/whisper 유지** (D-057)

---

## 1. 한 줄 요약

EG2 오디오 타워를 재사용하는 STT 연구는 **10시간 reader-only + V2 gate + domain/length controls + step-matched B3-long**까지 완료했지만, **제품 기준(≤15%)과 Sténo급(3,205h·상위층 FT·wordpiece·LM)**에는 도달하지 못했다. 현 자원(CPU-only, RAM 15.6GB, C 약 76GB/D 약 332GB, GPU 없음)으로 대규모 학습을 진행하는 것은 비용·저장·데이터 측면에서 정당화되지 않아 **동결**한다.

---

## 2. 최종 실험 결과

### 2.1 V2 reader-only (D-071)

| Arm | Dev CER | Test CER |
|---|---:|---:|
| B0′ V2 | 0.3701 | 0.359643 |
| **B3 V2 (balanced)** | **0.2682** | **0.262270** |
| B3-nat V2 | **0.2633** | — |

- Dev Δ(B0−B3) **+10.187%p**, CI **[+9.107,+11.328]**
- Sealed test Δ **+9.737%p**, CI **[+9.228,+10.258]**
- FLEURS dev B3 0.207607 vs B0′ 0.209770
- B3−B3-nat dev +0.490%p, CI [−0.229,+1.205] (비유의)
- **test 2,400은 이때 1회 사용 완료 → confirmatory 재사용 불가**

### 2.2 Matched-budget controls (D-073)

| Arm | epochs | steps | final dev CER |
|---|---:|---:|---:|
| B0′-12 | 12 | 3,576 | 0.3701 |
| B0′-20 | 20 | 5,960 | 0.3657 |
| B0′-38 | 38 | 11,324 | 0.3687 |
| B3-12 | 12 | 11,196 | **0.2682** |

→ B0′는 12 epoch에서 포화. compute/exposure만으로 B3 이점을 설명하지 못함.

### 2.3 Domain/length controls (D-075)

| Arm | 추가 4h | steps | final dev CER |
|---|---|---:|---:|
| B3-nat | Kspon short 0.5–8s | 11,196 | **0.263314** |
| B3-long | Kspon long 8–16s | 5,568 | 0.283946 |
| B3-zeroth-long | Zeroth long 8–16s | — | 0.365571 |

- B3-nat−B3-long **−2.0632%p**, CI [−2.9625,−1.1861]
- B3-long−B3-zeroth-long **−8.1625%p**, CI [−9.2063,−7.1645]
- Domain 효과는 강함. Length 효과는 **step confound**로 미확정.

### 2.4 Step-matched B3-long (D-078)

| 항목 | 값 |
|---|---|
| Arm | `b3long_sm_v2_s42` |
| steps | **11,136** (B3-nat 11,196 대비 0.54%) |
| final dev CER | **0.279433** |
| best dev CER | 0.2790 (epoch 11) |
| 학습 시간 | 5,814.4초 = 96.9분 |
| test 2,400 | **미사용** |

Bootstrap:
- `b3long_sm − B3-nat` **+1.6119%p**, CI **[+0.7606,+2.4933]**
- `b3long_sm − B3-long(ga4)` −0.4513%p, CI [−1.1119,+0.2055] (비유의)
- `b3long_sm − B0′` −9.0651%p, CI [−10.0532,−8.0875]

D-077 규칙상 **“step을 맞춰도 short-length 이점이 남는다”** (exploratory, dev 500, single seed). 단, **Kspon long OOV 7.33% vs short 2.3753%**, effective batch 4 vs 8의 교란이 있어 **길이의 인과 효과로 단정하지 않는다.**

---

## 3. 시도한 것 / 하지 않은 것

### 완료

- B0′/B3/B3-nat V2 reader-only
- B3-long, B3-zeroth-long domain/length controls
- B0′-20, B0′-38 matched-budget controls
- step-matched B3-long (batch2/ga2, 11,136 steps)
- Kspon long/Zeroth long 선별, V2 vocab, remap init
- 3-AI Hoplite review 4회(설계·V2 gate·domain/length·2C short)
- text overlap 감사(D-076)

### 미완료 / 보류

- **LoRA B1/B2 구현·학습** — GPU 이전 최대 작업이었으나 동결
- 13-state learned softmax mix
- wordpiece head + Gemma embedding 초기화
- 4-gram LM top-N rescoring
- non-Kspon short 1.66h hour-matched control
- seed 43 재현, 20-epoch exploratory
- fresh holdout 기반 confirmatory
- 3,000시간 Sténo급 학습

---

## 4. 동결 사유

### 4.1 제품 경로 대비 이득

- 제품 STT: **komixv2 5.49% / whisper-turbo 5.09%** (FLEURS 382, D-056)
- EG2 연구 트랙 best: **26.3% CER** (Kspon eval_clean dev)
- LoRA 10시간 기대: **23~26% CER**
- 제품 기준 **≤15%**에 미달하며, 별도 런타임·모델을 대체할 근거가 부족하다.

### 4.2 자원

| 항목 | 현재 | Sténo급 필요 |
|---|---|---|
| GPU | 없음(CPU only) | 40~100 GPUh |
| RAM | 15.6GB | 학습은 GPU, 데이터 로더는 RAM |
| 저장 | C 약 76GB / D 약 332GB | 1TB+ |
| 예산 | Modal $30 크레딧 | $120~200+ |
| 데이터 | 10시간 | 3,000시간+ |
| 구현 | LoRA 미구현 | top-layer FT/LoRA·13-state·wordpiece·LM |

### 4.3 저장

| 형태 | 3,000h 기준 |
|---|---:|
| WAV PCM16 | 345GB |
| FLAC | **170~220GB** |
| feature cache 4-layer fp16 | **약 2.1TB** |
| feature cache 13-state | **약 6.8TB** |
| feature cache int8 | 약 1.05TB |

FLAC은 raw audio만 줄이며, feature cache 병목은 해결하지 못한다.

### 4.4 RAM

- EG2 오디오 타워 Q8: **로드 431MB / peak 620MB**
- Sténo-like int8 단일 타워: **0.75~0.9GB**
- fp32 reader: **1.1~1.4GB**
- dual tower: **1.2~1.8GB**
- +4-gram LM: **1.5~2.5GB**
- whisper-turbo q4_k: **peak 969MB**
- komixv2: 파일 739MB, RAM 0.9~1.2GB 추정

Sténo급은 RAM 이점도 크지 않다.

---

## 5. 현재 보존 상태

- **삭제된 STT 산출물 없음**
- `data/wave2b/ckpt_controls/` — B3-long, B3-zeroth-long, b3long_sm 체크포인트
- `data/wave2b/feats_*` — control feature cache 약 20.5GB(D-074b 보존)
- `reports/provenance/W2A_lite/`, `reports/provenance/W2B/` — dev/test prediction·bootstrap 원장
- `logs/W2B/` — 학습·decode·watchdog 로그
- `docs/STT/reports/`, `docs/STT/plans/`, `docs/STT/hoplite/` — 문서
- 활성 백그라운드 프로세스 **없음**

---

## 6. 재개 조건

1. 사용자 명시 승인.
2. 새 사전등록(데이터·목표·평가셋·gate·중단 규칙).
3. GPU·저장·예산 계획.
4. 데이터 라이선스 확인.
5. **D-079 해제** 및 후속 결정.
6. confirmatory는 **fresh holdout** 사용. 기존 test 2,400 재사용 금지.

---

## 7. 관련 결정

| 결정 | 내용 |
|---|---|
| D-057 | 제품 F2 = komixv2/whisper, EG2 D = 연구 트랙 |
| D-067 | Wave 2B/2C-short v3 정본 |
| D-069 | V2 vocabulary 전환 |
| D-071 | V2 reader-only gate PASS |
| D-073 | matched-budget controls |
| D-075 | domain/length controls |
| D-076 | 3-AI review (3/3 B) |
| D-077 | step-matched B3-long 사전등록 |
| D-078 | step-matched B3-long 결과 |
| **D-079** | **STT 연구 트랙 동결·보류** |

상세는 [`../decisions.md`](../decisions.md) 참조.
