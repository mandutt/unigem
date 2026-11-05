# 외부 AI 검토 요청서 — Wave 2B V2 reader-only 후속: matched-budget 및 domain/length controls

- 작성일: **2026-11-05 (KST)**
- 프로젝트: `mandutt/unigem` (비공개, branch `main`)
- 현재 기준 커밋: **`069879f`** (`origin/main`과 0/0)
- 직전 검토 기준점: `reports/EXTERNAL_REVIEW_W2B_V2_GATE_2026-11-05.md` (768줄, 기준 커밋 `9d1aba6`)
- 직전 검토 결과: **3/3 B — recipe-level PASS with caveats**, C(exploratory/reject) 0/3
- 이 문서의 목적: **프로젝트 이력을 처음 보는 외부 AI가 저장소의 과거 문서를 읽지 않고도, 직전 검토 이후 추가된 matched-budget control과 domain/length control의 타당성 및 다음 결정을 판단**할 수 있게 하는 자기완결형 검토 요청서
- 문서 상태: **검토 요청**이며 승인 문서가 아니다. 검토 의견은 사용자 승인 전 구현·주장에 반영하지 않는다.

---

## 0. 검토자에게 — 이번 라운드의 핵심

직전 라운드(2026-11-05 전반)에서 3개 AI는 V2 reader-only 결과를 **3/3 B (recipe-level PASS)**로 평가했다. 그때 공통 Must-fix는 다음 8건이었다.

1. **step·audio exposure·domain·length가 결합**된 confound
2. **V2 vocabulary의 2-pass selection dependence**
3. **test 2,400을 이미 1회 사용**
4. **B3-nat는 dev-only**
5. **matched step/audio control 필요**
6. **test와 short-train의 text-level overlap 감사**
7. **10.0221h(frames) vs 10.0024h(manifest) 시간 회계 불일치**
8. **LoRA confirmatory claim에는 fresh holdout + matched no-LoRA comparator 필요**

그 후 우리는 다음을 실제로 실행했다.

- **B0′ matched-budget controls**: exposure-matched(B0′-20)와 step-matched(B0′-38) — D-073
- **Domain/length controls**: Kspon long 8–16s 4h arm(B3-long)와 non-Kspon long 8–16s 4h arm(B3-zeroth-long) — D-074/D-074a/D-075
- 모든 control은 **dev 500 전용**, sealed test 2,400 미사용
- **Kspon long 4h**, **Zeroth long 4h**, 10h caches, checkpoints, 예측·bootstrap을 보존(D-074b)

이번 라운드에서 검토받고 싶은 핵심 질문은 다음 네 가지다.

> **Q-A. “Kspon domain 효과가 강하다”는 현재 결론은 타당한가?**
>
> **Q-B. “short-length 효과는 아직 확정할 수 없다”는 판단이 옳은가? 아니라면 어떤 step-matched control이 필요한가?**
>
> **Q-C. 원래 계획한 non-Kspon short 4h control을 데이터 부족으로 Zeroth long 4h로 대체한 것이 방법론적으로 허용되는가?**
>
> **Q-D. 지금의 증거로 어떤 문장까지 대외적으로 말할 수 있고, 다음 우선순위는 무엇인가?**

칭찬보다 **결함·누락·대안·중단 기준**을 우선해 달라. 확실하지 않으면 “불확실”이라고 명시해 달라.

---

## 1. 한눈에 보는 현재 상태

### 1.1 직전 gate 결과 (변경 없음)

| 항목 | 값 |
|---|---:|
| Dev 500, B0′ 6h | **0.370084** |
| Dev 500, B3 10h balanced | **0.268214** |
| Dev 500, B3-nat 10h natural | **0.263314** |
| Sealed test 2,400, B0′ | **0.359643** |
| Sealed test 2,400, B3 | **0.262270** |
| Test Δ (B0′−B3) | **+9.737%p**, 95% CI **[+9.228,+10.258]** |
| FLEURS dev, B0′ → B3 | 0.209770 → **0.207607** (no regression) |
| Gate 판정 | **PASS** (사전등록 Δ≥1.0%p + CI 하한>0) |

### 1.2 직전 검토 이후 추가 결과

| 실험 | 핵심 결과 | 지위 |
|---|---|---|
| B0′-20 (exposure-matched) | final dev **0.3657**; B3와 **+9.723%p** 차이 | dev-only exploratory |
| B0′-38 (step-matched) | final dev **0.3687**; B3와 **+10.006%p** 차이 | dev-only exploratory |
| B3-long (Kspon long 8–16s 4h) | final dev **0.283946**; B0′ 대비 **+8.614%p** | dev-only exploratory |
| B3-zeroth-long (Zeroth long 8–16s 4h) | final dev **0.365571**; B0′ 대비 **+0.451%p (비유의)** | dev-only exploratory |
| B3-nat − B3-long | **−2.0632%p**, CI **[−2.9625,−1.1861]** | length 후보, **step confound** |
| B3-long − B3-zeroth-long | **−8.1625%p**, CI **[−9.2063,−7.1645]** | **domain 효과, 같은 long 길이** |

### 1.3 현재 우리의 해석

- **compute/exposure만으로는 B3의 +10%p를 설명하지 못한다.** B0′를 20/38 epoch로 늘려도 B3 격차는 약 9.7~10.0%p로 유지됐다.
- **B3-long vs B3-zeroth-long**는 같은 8–16s, 같은 4h, 거의 같은 optimizer step(5,568 vs 5,676)이므로 **domain 효과가 강하다**는 증거다.
- **B3-nat vs B3-long**은 B3-nat이 2.06%p 좋지만, B3-nat은 **11,196 steps**, B3-long은 **5,568 steps**로 **step 수가 약 2배**다. 따라서 **short-length 효과는 아직 확정할 수 없다.**
- 원래 계획한 **non-Kspon short 4h** direct control은 데이터 부족으로 **미실시**다. Zeroth short 잔여가 1.66h뿐이었다.

---

## 2. 자기완결 배경

### 2.1 프로젝트

EmbeddingGemma 2(EG2)의 **오디오 타워를 재사용**해 다음 과제를 검증하는 연구 프로젝트다.

- F1 언어판정
- **F2 STT**
- F3 비전 태깅
- F4 맞춤법 교정
- F5 메모리 요약
- F6 STT 후처리

F2의 **제품 경로는 이미 komixv2/whisper로 확정**(D-057)되어 있고, EG2 기반 F2는 **연구 트랙**이다. 이 연구가 실패해도 제품 경로는 바뀌지 않는다.

### 2.2 이번 실험의 위치

- EG2 오디오 타워는 **frozen**이다.
- 그 위에 작은 **CTC character reader**(4층 Transformer, d=384, 6 head, FF=1536, **9,183,922 params**)를 붙인다.
- Wave 2A-lite에서 6시간 데이터·동결 타워로 FLEURS ko dev CER **0.20913**을 냈고, Kspon eval_other에서는 **0.35143**으로 도메인/길이 갭이 남았다.
- Wave 2B+2C-short의 목표는 다음 두 개입을 분리하는 것이다.
  - **2B**: EG2 오디오 타워 상위층 LoRA
  - **2C-short**: Kspon train에서 **짧은 발화 4시간**을 추가
- 이번 라운드는 그중 **reader-only** 파일럿이다. **LoRA B1/B2는 아직 구현·실행하지 않았다.**

### 2.3 용어

| 용어 | 뜻 |
|---|---|
| **B0′** | Wave 1 6시간만 사용한 reader. V2 baseline |
| **B3** | Wave 1 6시간 + Kspon short 4시간 = 10시간, **balanced sampler** |
| **B3-nat** | B3와 **같은 10시간 clip ID 집합**, **natural sampler** |
| **B3-long** | Wave 1 6시간 + **Kspon long 8–16초 4시간**, natural sampler |
| **B3-zeroth-long** | Wave 1 6시간 + **Zeroth long 8–16초 4시간**, natural sampler |
| **CER** | character error rate. 공백 무시·구두점 제거의 통일 정규화 |
| **dev 500** | Kspon eval_clean에서 duration 층화로 뽑은 500발화. arm 선택·freeze에 사용 |
| **test 2,400** | 같은 eval_clean의 나머지 2,400발화. **sealed holdout, 1회 사용 완료** |
| **spare 90** | eval_clean의 나머지 90발화. 평가 미사용 |
| **V1** | 2A의 1,101자 vocabulary |
| **V2** | V1 순서·ID를 보존하고 신규 228자를 추가한 **1,329자**(head 1,330행) |
| **gate** | 사전등록 판정: `Δ = CER(B0′) − CER(candidate)`, **Δ ≥ 1.0%p AND paired utterance bootstrap 95% CI 하한 > 0** |
| **in-domain holdout** | 같은 Kspon 코퍼스 계열의 절차적 holdout. **화자 독립 test가 아님** |
| **steps** | optimizer step 수. `batch=2`, `grad_accum=4`, 즉 micro-batch 8 기준 |

---

## 3. 데이터·평가 프로토콜

### 3.1 Wave 1 6시간

| 항목 | 값 |
|---|---:|
| 총 클립 | 2,384 |
| Zeroth | 1,534 |
| Kconf | 850 |
| 오디오 | 6.0008h |
| feature | frozen EG2 F-C-concat 4,096d, memmap cache |

### 3.2 Kspon short 4시간 (V2)

| 항목 | 값 |
|---|---:|
| 클립 | **5,079** |
| 오디오 | **4.0016h** |
| 길이 | 0.5–8초 |
| V2 OOV 제외율 | **2.3753%** (2,319/97,628) |
| 10h cache | **7,463클립 / 901,985 frames / 10.0221h** |

### 3.3 V2 vocabulary — 2-pass 구성

- V1 short 후보의 OOV 제외율이 **90.727%**여서 V2로 전환했다.
- V2는 **V1 1,101자의 순서·ID를 보존**하고 신규 228자를 추가한 **1,329자**(head 1,330행)다.
- 구성은 **2-pass**다.
  1. draft vocab으로 short 후보를 1차 선택
  2. 선택된 short refs로 final V2 vocab을 구성
  3. final V2로 short를 다시 선택
- **선택 의존성**이 남아 있다. test/dev 누출은 없지만, short subset의 문자 coverage는 selection-dependent다.
- 이번 control에서도 **V2 vocab을 고정**하고 동일 head remap(`missing=0, unexpected=0`)을 사용했다.

### 3.4 OOV·test 대표성

| 항목 | 값 |
|---|---:|
| dev 500 OOV | 5클립 / 1.0000%, 문자 5/8,247 = 0.0606% |
| test 2,400 OOV | 45클립 / 1.8750%, 문자 53/40,788 = 0.1299% |
| test ≤4초 | **1,784 / 2,400 = 74.33%** |
| test 8–16초 | 185건 (bin 검정력 낮음) |
| 0.5초 미만 | 28건, 최소 0.286초 |
| test feature | `--min-dur 0.28`로 2,400/2,400 유지 |

### 3.5 split·overlap

- split은 원논문의 filename 변경·shuffle 때문에 **화자 독립 split이 아니다**.
- duration 층화로 dev 500 / test 2,400 / spare 90을 구성했다.
- **clip ID 기준** 교집합은 모두 0이다.

| 비교 | 교집합 |
|---|---:|
| test ∩ short V2 (5,079) | **0** |
| test ∩ short V1 (5,119) | **0** |
| test ∩ Wave 1 train (2,384) | **0** |
| dev ∩ short V2 | **0** |
| spare ∩ short V2 | **0** |

- **주의**: 직전 3-AI 중 Sonnet은 **text-level overlap 136/2,400(5.7%)**를 보고했고, 중복 제거 시 Δ가 9.74→9.48%p로 변한다고 했다. 이번 라운드에서 이 text-level 감사를 **정규화기로 재현·종결하지 않았다.** (ID overlap 0과는 별개다.)

### 3.6 test 사용 이력

- test 2,400은 **B3를 dev에서 freeze한 뒤 1회만** 사용했다.
- 이후 B0′-20/38, B3-long, B3-zeroth-long은 **모두 dev 500 전용**이며 test를 사용하지 않았다.
- 따라서 **새 control 결과는 confirmatory가 아니다.**

---

## 4. 직전 3-AI 검토 결과와 Must-fix

### 4.1 판정

| 항목 | GLM | Sonnet | Luna |
|---|---|---|---|
| 판정 | **B** (caveat부 PASS) | **B** (recipe-level PASS with caveats) | **B** (caveat-qualified PASS) |
| 분량 | 15,189자 | 20,641자 | 19,123자 |
| C(exploratory/reject) | 없음 | 없음 | 없음 |

3/3 **B**. gate 숫자 자체는 유효하다는 데 합의했지만, **데이터 효과로의 귀속은 금지**했다.

### 4.2 공통 Must-fix 8건과 현재 상태

| ID | 지적 | 현재 상태 |
|---|---|---|
| **MF-A** | B0′ 6h vs B3 10h: step 3.13×, exposure 1.67×, domain, length 결합 | **부분 이행**: B0′-20/38 완료. B3-long/zeroth-long 완료. **step-matched B3-long은 미실시** |
| **MF-B** | test 2,400 1회 사용, 화자 독립 아님 | **유지**: 새 control도 test 미사용. “in-domain procedural holdout, used once”로만 표기 |
| **MF-C** | V2 vocab 2-pass selection-dependent | **부분 이행**: V2 고정, control에도 동일 V2. selection loop 자체는 미해결 |
| **MF-D** | B3-nat dev-only, CI 0 포함 | **유지**: “dev에서 탐지 가능한 sampler 차이 없음”으로만 표기. test 재평가 없음 |
| **MF-E** | test refs와 short-train refs의 text-level overlap | **미종결**: Sonnet 136/2,400(5.7%) 발견; 이번 라운드에서 정규화기 재현·민감도 분석 미실시 |
| **MF-F** | 10.0221h(frames) vs 10.0024h(manifest) | **문서화**: 두 값을 병기. 0.2% 차이 |
| **MF-G** | speaker/session overlap 확인 불가 | **유지**: 모든 대외 문장에 “not speaker-independent” 명시 |
| **MF-H** | LoRA compute confound | **미착수**: LoRA B1/B2 미구현. fresh holdout + matched no-LoRA 필요 |

### 4.3 모델별 고유 지적

- **GLM**: 사전등록·test freeze·커밋 순서의 절차 무결성 강조; **B0′-rep10**(Wave1 6h 반복·서브샘플링 10.02h) 제안; 시간 회계 10.0221h vs 10.0024h 지적.
- **Sonnet**: **text-level overlap 136/2,400(5.7%)** 발견; 중복 제거 시 Δ 9.74→9.48%p; Kspon long 4h control이 “short” claim 검증의 유일한 control이라고 봄; LoRA confirmatory에는 fresh holdout 필요.
- **Luna**: step과 cumulative audio seconds를 **동시에** 맞춘 사전등록 비교 필요; Wave1 replay/resampling control 제안; Kspon long vs short, non-Kspon short control로 domain/duration 분리; seed 43은 robustness 보조.

---

## 5. 직전 검토 이후 실행 1 — B0′ matched-budget controls (D-073)

### 5.1 목적

B0′ 6h vs B3 10h의 +10%p가 **추가 optimizer step** 또는 **추가 audio exposure**로 설명되는지 확인.

### 5.2 설계

| Arm | epochs | total steps | audio exposure | 목적 |
|---|---:|---:|---:|---|
| B0′-12 | 12 | 3,576 | 72.0h | 기존 baseline |
| B0′-20 | 20 | 5,960 | **120.0h** | exposure-matched (B3 120.3h) |
| B0′-38 | 38 | **11,324** | 228.0h | step-matched (B3 11,196) |
| B3-12 | 12 | 11,196 | 120.3h | reference |

- 모두 Wave 1 6h, V2, same remapped init, seed 42, natural sampler, **patience 99**(full budget).
- **dev 500 전용**, test 2,400 금지, gate 아님.

### 5.3 결과

| Arm | best dev CER | final dev CER |
|---|---:|---:|
| B0′-12 | 0.3701 | 0.3701 |
| B0′-20 | 0.3654 (ep19) | **0.3657** |
| B0′-38 | 0.3683 (ep35) | **0.3687** |
| B3-12 | 0.2682 | 0.2682 |

Bootstrap, 20,000 resamples, seed 42:

| 비교 | Δ CER | 95% CI |
|---|---:|---:|
| B0′-12 − B0′-20 | +0.464%p | [−0.107,+1.028] |
| B0′-12 − B0′-38 | +0.181%p | [−0.486,+0.846] |
| B0′-20 − B3 | **+9.723%p** | [+8.656,+10.819] |
| B0′-38 − B3 | **+10.006%p** | [+8.908,+11.161] |
| B0′-20 − B0′-38 | −0.284%p | [−0.923,+0.347] |

### 5.4 해석

- B0′는 **12 epoch에서 포화**됐다. 20/38 epoch 추가 이득은 0.5%p 이내, 38은 오히려 약간 나쁘다.
- **compute/exposure를 맞춰도 B3 격차는 9.7~10.0%p로 유지**된다.
- 따라서 B3 이점은 “더 많은 step/audio”로 설명되지 않는다.
- 남는 것은 **Kspon short 데이터 구성(domain + short-length)**이지만, 이 실험만으로 둘을 분리할 수 없다.

### 5.5 한계

- dev 500, single seed.
- B0′-20/38은 B3와 **LR schedule shape**이 다르다(20/38 epoch cosine vs 12 epoch cosine).
- B0′-38은 같은 6h를 38 epoch 반복하므로 **데이터 반복/과적합**이 섞인다.
- B3는 balanced, B0′는 natural sampler다. sampler 차이는 dev에서 유의하지 않았지만 완전히 배제되지 않는다.
- FLEURS guardrail은 이 control에서 측정하지 않았다.

---

## 6. 직전 검토 이후 실행 2 — domain/length controls (D-074/D-074a/D-075)

### 6.1 설계

| Arm | Wave1 6h | 추가 4h | sampler | 역할 |
|---|---|---|---|---|
| B3-nat (기존) | Zeroth/Kconf | Kspon short 0.5–8s | natural | Kspon + short reference |
| **B3-long** (신규) | Zeroth/Kconf | **Kspon long 8–16s** | natural | **length control** |
| **B3-zeroth-long** (신규) | Zeroth/Kconf | **Zeroth long 8–16s** | natural | **domain control (길이 matched)** |

- 모두 10h, 12 epoch, seed 42, V2, same remapped init, patience 4, CPU 6 threads.
- **dev 500 전용**, test 2,400 미사용, gate 아님.

### 6.2 데이터 선택

#### Kspon long 4h

- 원본: `D:/unigem/kspon_train/10.한국어음성/KsponSpeech_05.zip` (재다운로드 없음)
- transcript: `D:/unigem/w2b/train.trn` (620,000줄)
- 8.0–16.0초, target 4.0h
- **1,327클립 / 4.0025h**, 124 folders
- V2 OOV 제외 **1,574/21,477 = 7.33%**
- 출력: `data/wave2b/long_4h.jsonl`, `data/wave2b/audio/long_4h/`

#### Zeroth long 4h — D-074a

- 원본: `data/raw/zeroth/data/train-*.parquet`
- **Wave1에서 이미 쓴 Zeroth 1,534개를 제외**한 뒤 추가 선택
- 8.0–16.0초, target 4.0h
- **1,395클립 / 4.0014h**
- V2 OOV 제외 **436/9,758 = 4.47%**
- 출력: `data/wave2b/long_4h_zeroth.jsonl`, `data/wave2b/audio/long_4h_zeroth/`

#### 원안 non-Kspon short 4h가 불가능했던 이유

Zeroth short 0.5–8s의 Wave1 제외 잔여는 **1,012클립 / 1.6574h**뿐이었다.

| bin | 클립 | 시간 |
|---|---:|---:|
| 0–2s | 0 | 0h |
| 2–4s | 52 | 0.055h |
| 4–6s | 548 | 0.801h |
| 6–8s | 412 | 0.801h |
| **합계** | **1,012** | **1.657h** |

4h short-domain arm을 만들 수 없어 **D-074a로 Zeroth long 8–16s 4h**로 대체했다.

### 6.3 학습 결과

| Arm | 추가 데이터 | final dev CER | best dev CER | steps/epoch | total steps | 학습 시간 |
|---|---|---:|---:|---:|---:|---:|
| B0′-12 | 없음 | 0.370084 | 0.3701 | 298 | 3,576 | — |
| B3-12 balanced | Kspon short | 0.268214 | 0.2682 | 933 | 11,196 | — |
| B3-nat | Kspon short | **0.263314** | 0.2633 | 933 | 11,196 | — |
| **B3-long** | Kspon long | **0.283946** | 0.2828 (ep9) | **464** | **5,568** | 5,377.3초 (1.494h) |
| **B3-zeroth-long** | Zeroth long | **0.365571** | 0.3654 (ep9) | **473** | **5,676** | 5,461.3초 (1.517h) |

10h cache:

- Kspon long: **10.0130h / 3,711클립**
- Zeroth long: **10.0125h / 3,779클립**

### 6.4 Bootstrap

20,000 resamples, seed 42, utterance-level. 부호는 `CER(A) − CER(B)`; 음수면 A가 더 좋다.

| 비교 | Δ CER | 95% CI |
|---|---:|---:|
| B3-nat − B3-long | **−2.0632%p** | **[−2.9625, −1.1861]** |
| **B3-long − B3-zeroth-long** | **−8.1625%p** | **[−9.2063, −7.1645]** |
| B3-nat − B3-zeroth-long | −10.2257%p | [−11.3818, −9.1389] |
| B0′ − B3-long | **+8.6138%p** | **[+7.6628, +9.5939]** |
| B0′ − B3-zeroth-long | +0.4513%p | [−0.2087, +1.1278] |
| B3-balanced − B3-long | −1.5732%p | [−2.4710, −0.6910] |

### 6.5 해석

#### Domain — 강함

`B3-long`과 `B3-zeroth-long`은 **같은 8–16초, 같은 4h, 같은 10h, 같은 natural sampler**이고 total step도 5,568 vs 5,676으로 거의 같다.

- Kspon long **0.2839** vs Zeroth long **0.3656**
- **Kspon이 8.16%p 더 좋음**, CI **[−9.21,−7.16]**, 0 제외.

→ **Kspon domain(또는 Kspon long 데이터 구성) 효과가 크다.** domain을 바꾸면 같은 길이에서도 큰 손실이 난다.

#### Length — 아직 확정 불가

B3-nat(short) **0.2633** vs B3-long(long) **0.2839**는 B3-nat이 **2.06%p** 좋고 CI도 0을 제외한다. 그러나:

- B3-nat: **933 steps/epoch, 총 11,196 steps**
- B3-long: **464 steps/epoch, 총 5,568 steps**
- B3-balanced도 B3-long보다 1.57%p 좋다(CI 0 제외).

long clip은 같은 4h에서 clip 수가 적어 optimizer step이 절반이다. 따라서 **2.06%p를 순수 길이 효과로 귀속할 수 없다.** short-length가 기여할 가능성은 있지만, **step-matched B3-long** 없이는 인과 주장 금지.

#### B0′ 대비

- B0′ **0.3701** → B3-long **0.2839**: Kspon long만으로 **8.61%p** 개선(CI 0 제외).
- B0′ **0.3701** → B3-zeroth-long **0.3656**: **+0.45%p**, CI **[−0.21,+1.13]**로 유의하지 않음.

→ Kspon long 4h는 B0′보다 명확히 낫지만, Zeroth long 4h는 B0′와 사실상 차이 없음. **domain 가설과 일치.**

---

## 7. 현재 증거의 지위 — 말할 수 있는 것/없는 것

### 7.1 말할 수 있다

- V2 reader-only **recipe-level gate PASS**: dev +10.187%p, test +9.737%p, FLEURS dev 악화 없음.
- B3의 이점은 **추가 step/audio exposure만으로 설명되지 않는다** (B0′-20/38 controls).
- **Kspon long과 Zeroth long의 same-length 비교에서 Kspon이 8.16%p 우수**하다.
- **B3-long은 B0′보다 8.61%p 우수**하다.
- **B3-zeroth-long은 B0′와 유의하게 다르지 않다.**
- 이 모든 control은 **dev 500 전용 exploratory**이며 sealed test를 사용하지 않았다.

### 7.2 말할 수 없다

- “Kspon short 4시간의 순수 데이터 효과를 입증했다.”
- “short-length 분포 효과가 2.06%p다.” — **step confound** 때문에 금지.
- “화자 독립 일반화에서 +9.7%p다.”
- “B3-zeroth-long이 non-Kspon short control과 동등하다.”
- “20 epoch/seed 43/LoRA도 같은 test에서 confirmatory PASS.”
- “LoRA가 필요 없다/있다.” (B1/B2 미실행)

### 7.3 현재 가장 정확한 한 문장

> **V2 reader-only recipe는 in-domain dev/test에서 큰 폭의 CER 개선을 보였고, 그 개선은 단순한 compute/exposure가 아니다. 같은 long 길이에서 Kspon이 Zeroth보다 8.16%p 우수해 domain 효과는 강하게 지지된다. 그러나 short-length 효과는 optimizer step confound 때문에 아직 확정할 수 없고, non-Kspon short direct control도 데이터 부족으로 미실시다.**

---

## 8. 위협·한계

### 8.1 Step/exposure confound

- B3-nat 11,196 steps vs B3-long 5,568 steps.
- B3-balanced 11,196 vs B3-long 5,568.
- B3-long vs B3-zeroth-long는 **5,568 vs 5,676**으로 거의 같다 → domain 비교는 clean.
- 따라서 **length 주장만** step confound에 취약하다.

### 8.2 Domain/length 완전 분리 실패

- 원안은 2×2 factorial(domain × length)이었다.
- 실제로는 **Kspon short**, **Kspon long**, **Zeroth long**만 있고 **Zeroth short 4h가 없다**.
- 따라서 “domain at short”를 직접 검증하지 못했다.

### 8.3 V2 vocabulary selection loop

- V2 vocab이 short selection과 얽혀 있다.
- control에서도 V2를 고정했기 때문에 arm 간 비교는 공정하지만, **absolute CER의 일반화**에는 selection dependence가 남는다.

### 8.4 Test 재사용

- test 2,400은 B3 vs B0′에 1회 사용됐다.
- 새 control은 test를 쓰지 않았지만, **앞으로 test를 다시 쓰는 confirmatory claim은 불가**하다.

### 8.5 Text overlap

- Sonnet의 **136/2,400(5.7%)** text-level overlap 지적은 아직 **정규화기 재현·민감도 분석으로 종결되지 않았다.**
- ID overlap 0과 별개다.

### 8.6 Split·화자

- Kspon eval_clean은 화자 ID가 없고 filename이 shuffle돼 **화자 독립이 아니다.**
- dev/test/spare는 duration 층화 split이다.

### 8.7 길이 대표성

- test는 ≤4초가 **74.33%**로 short 중심이다.
- 8–16초 bin은 185건뿐이라 long 조건의 test 결론은 약하다.

### 8.8 데이터 선택·OOV

- Kspon long OOV **7.33%**는 short V2(2.3753%)보다 높다.
- Zeroth long OOV 4.47%.
- OOV clip을 제외한 selection이 arm별로 다른 문자 분포를 만들 수 있다.

### 8.9 단일 seed·exploratory

- 모든 control은 seed 42, dev 500.
- B3-long/zeroth-long은 12 epoch, patience 4.
- B3-zeroth-long은 B0′보다 약간 나쁜데, “domain 데이터를 추가하면 왜 나빠지는가”에 대한 최적화·과적합 설명이 아직 없다.

### 8.10 B3-nat

- dev-only, B3보다 0.49%p 좋지만 CI 0 포함.
- “sampler 효과는 탐지되지 않음”까지만 말할 수 있다.

### 8.11 LoRA

- B1/B2 LoRA 미구현.
- GPU 패키징·Volume·T4/L4/L40S smoke 미완료.
- LoRA confirmatory에는 **fresh holdout + matched no-LoRA comparator**가 필요하다.

---

## 9. 검토 요청 질문

각 질문에 **A/B/C/D** 중 하나를 붙이고, 이유와 필수 수정을 적어 달라.

- **A** = 현재 해석·계획을 그대로 수용
- **B** = caveat를 붙이면 수용
- **C** = 수정·재실험 없이는 수용 불가
- **D** = 정보 부족

### Q1. Domain 결론

> “같은 long 8–16s, 같은 4h에서 Kspon이 Zeroth보다 8.16%p 우수하므로 Kspon domain 효과가 강하다.”

이 문장을 **A/B/C/D**로 평가해 달라. 
- B3-long vs B3-zeroth-long의 유일한 차이는 데이터 source(도메인)다. 
- 그러나 Kspon long과 Zeroth long은 **화자·recording·text style·OOV**도 다르다. “domain”이라는 라벨이 너무 넓은가?
- domain 효과를 더 좁은 하위 가설(recording, vocabulary, speaking style)로 나눌 필요가 있는가?

### Q2. Length 결론

> “B3-nat short가 B3-long보다 2.06%p 좋지만, step 수가 2배이므로 short-length 효과는 아직 확정할 수 없다.”

이 판단이 옳은가? 
- **step-matched B3-long**을 하려면 `grad_accum=2`(928 steps/epoch, 총 11,136)와 `batch=1`(3,711 micro/epoch, 928 steps) 중 어느 쪽이 더 타당한가?
- 아니면 **Wave1 6h + Kspon long 4h를 2회 반복**해 step을 맞추는 **replay control**이 더 나은가?
- length effect와 step effect를 분리할 **최소 실험**은 무엇인가?

### Q3. Zeroth long 대체

> “Zeroth short 4h가 1.66h밖에 없어 Zeroth long 4h로 대체했다.”

이 대체가 **A/B/C/D**인가?
- 원래의 “non-Kspon short” 가설을 직접 검증하지 못한 것을 **결정적 결함**으로 봐야 하는가?
- FLEURS train 등 공개 데이터를 추가로 받아 **non-Kspon short 4h**를 구성하는 것이 필요한가? 필요하다면 어떤 데이터·길이·화자 조건을 요구하는가?
- 아니면 현재의 “domain at long” 증거로 충분하다고 보는가?

### Q4. V2 vocabulary

> “V2 1,329자는 short selection과 2-pass로 얽혀 있지만, 모든 arm에 동일 V2를 고정했으므로 arm 비교는 공정하다.”

이 주장이 타당한가?
- absolute CER를 대외에 말할 때 V2 selection dependence를 어떻게 표기해야 하는가?
- “V2 vocab-conditioned”라는 표현으로 충분한가?
- 향후 non-Kspon short/FLEURS arm에도 V2를 고정해야 하는가, 아니면 새 vocab을 만들어야 하는가?

### Q5. Test 재사용·confirmatory 지위

- test 2,400은 B3 vs B0′에 1회 사용됐다.
- 새 control은 test를 쓰지 않았다.
- 앞으로 **step-matched B3-long**, **non-Kspon short**, **LoRA** 결과를 test로 평가할 때 각각 어떤 지위인가?
- **새 confirmatory claim**을 하려면 fresh holdout이 필수인가? spare 90으로 충분한가?
- “in-domain procedural holdout, used once”라는 표기가 정확한가?

### Q6. B0′ controls

> “B0′-20/38로 compute/exposure를 맞춰도 B3 격차는 9.7~10.0%p로 유지된다.”

이 결론이 타당한가?
- B0′-38은 6h를 38 epoch 반복하므로 **데이터 반복**이 섞인다. 이 결함이 결론을 얼마나 약화하는가?
- B0′-20과 B0′-38의 LR schedule shape 차이(20/38 epoch cosine vs 12 epoch cosine)를 어떻게 처리해야 하는가?
- **B0′-rep10**(Wave1 6h 반복·서브샘플 10.02h)을 추가로 해야 하는가?

### Q7. B3-nat·sampler

> “B3-nat는 dev에서 B3보다 0.49%p 좋지만 CI가 0을 포함하므로 sampler 효과는 탐지되지 않았다.”

이 표현이 충분한가?
- B3-nat를 test로 평가하지 않은 것을 결함으로 봐야 하는가?
- B3-long/zeroth-long도 natural sampler이므로, balanced vs natural 차이가 length/domain 결론을 오염시키는가?

### Q8. Text overlap

- Sonnet이 **136/2,400(5.7%)** text-level overlap을 보고했고, 중복 제거 시 Δ 9.74→9.48%p라고 했다.
- 이번 라운드에서 우리는 이 감사를 **정규화기로 재현하지 않았다.**
- 이 미종결 항목이 **현재 gate/주장**에 얼마나 치명적인가?
- 지금 즉시 재현해야 하는가, 아니면 새 holdout을 만들 때 함께 처리하면 되는가?

### Q9. B3-zeroth-long의 역설

- Zeroth long 4h를 추가한 B3-zeroth-long은 **0.3656**으로 B0′ **0.3701**보다 약간 좋지만 유의하지 않다.
- “데이터를 추가했는데 왜 거의 개선이 없는가?”에 대해 **domain mismatch**, **long-only data**, **과적합**, **sampler/step** 중 어느 설명이 가장 가능성이 높은가?
- 이 arm을 domain control로 쓰는 것이 타당한가, 아니면 **B0′+Zeroth long** 자체가 잘못된 control인가?

### Q10. 다음 우선순위

현재 후보는 다음과 같다.

1. **step-matched B3-long** (length vs step 분리; 약 1.5~2h CPU)
2. **non-Kspon short 4h** (FLEURS train 등 공개 데이터; 다운로드·선별 필요)
3. **seed 43 재현**
4. **20-epoch 3-arm**
5. **LoRA B1/B2 구현 + GPU smoke**
6. **text-overlap 감사 종결**

**지금 당장 하나만** 고른다면 무엇이며, 그 이유는 무엇인가? 
- “domain은 충분히 강하니 short/length는 중단하고 LoRA로 가라”는 판단이 가능한가?
- 아니면 **step-matched B3-long + non-Kspon short**를 먼저 끝내야 하는가?

### Q11. 대외 주장 문장

다음 문장의 **A/B/C/D**와 수정안을 달라.

> “EG2 reader-only에서 Kspon short 4h를 추가한 B3가 B0′보다 dev +10.19%p, test +9.74%p 좋았다. 이 이점은 compute/exposure로 설명되지 않으며, Kspon domain 효과가 강하다. short-length 효과는 아직 확정되지 않았다.”

- “Kspon domain 효과가 강하다”를 대외 문장에 넣어도 되는가?
- “short 4h 데이터 효과”라고 쓰면 안 되는 이유를 한 문장으로 명시해 달라.

---

## 10. 재현 정보

### 10.1 주요 파일

- 결과 보고서
  - `reports/W2B_v2_gate_results.md`
  - `reports/W2B_v2_dev_results.md`
  - `reports/W2B_V2_GATE_3AI_SYNTHESIS.md`
  - `reports/W2B_b0_matched_controls.md`
  - `reports/W2B_domain_length_controls.md`
- 계획·결정
  - `docs/decisions.md` (D-001~D-075)
  - `reports/W2B_domain_length_controls_plan.md`
  - `reports/W2B_b0_matched_controls_plan.md`
- Provenance
  - `reports/provenance/W2B/v2_dev_bootstrap.json`
  - `reports/provenance/W2B/v2_test_bootstrap.json`
  - `reports/provenance/W2B/matched_bootstrap.json`
  - `reports/provenance/W2B/domain_controls_bootstrap.json`
  - `reports/provenance/W2B/domain_controls_budget.json`
  - `reports/provenance/W2B/test_freeze.json`
  - `reports/provenance/W2B/overlap_final.json`
  - `reports/provenance/W2B/training_budget.json`
- Dev predictions
  - `reports/provenance/W2B/devpred_b0p_v2_s42.json`
  - `reports/provenance/W2B/devpred_b3_v2_s42.json`
  - `reports/provenance/W2B/devpred_b3nat_v2_s42.json`
  - `reports/provenance/W2B/devpred_b3long_v2_s42.json`
  - `reports/provenance/W2B/devpred_b3zerothlong_v2_s42.json`

### 10.2 Checkpoint sha256

| Arm | sha256 |
|---|---|
| B3 V2 best | `8349159e9b449ed4cd2f60e27fac4f955513423593ff34854772e90356e84328` |
| B0′ V2 best | `c869e66bf205bdf55596f2428aad3452ac813a68f9817bc4eeea77e6b4c27ddd` |
| B3-long final | `94da8b5aa6c8da19ad79ff929aa7ce6c4da84f7b026eb34a6dd4112e7bbf45ca` |
| B3-zeroth-long final | `ab1a2b3716222e16cdfacc09461bb93a507bc331845bd92611835f62b0c01c54` |

### 10.3 주요 재현 명령

```text
# Kspon long selection (V2)
python runner/w2b_select_kspon_long.py --vocab data/wave2b/vocab_v2.json

# Zeroth long selection (V2, Wave1 1,534 skip)
python runner/w2b_select_zeroth_long.py --vocab data/wave2b/vocab_v2.json

# 4h feature
python train/w1_extract.py --manifest data/wave2b/long_4h.jsonl \
  --out-dir data/wave2b/feats_kspon_long \
  --vocab-in data/wave2b/vocab_v2.json \
  --arms fc --fc-memmap --threads 6 --min-dur 0.5

# 10h cache
python runner/w2b_combine_feats.py \
  --base data/wave1/feats/fc.npz \
  --extra data/wave2b/feats_kspon_long/fc.npz \
  --out data/wave2b/feats_10h_kspon_long

# B3-long training
python train/d5_reader.py \
  --features data/wave2b/feats_10h_kspon_long/fc.npz \
  --dev-features data/wave2b/feats_dev/fc.npz \
  --vocab-file data/wave2b/vocab_v2.json --retarget \
  --arch base --arm b3long_v2_s42 \
  --init-ckpt data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt \
  --epochs 12 --patience 4 --batch 2 --grad-accum 4 \
  --seed 42 --threads 6 --device cpu --sampler natural \
  --ckpt-dir data/wave2b/ckpt_controls

# Dev decode
python train/d5_reader.py --decode \
  --features data/wave2b/feats_dev/fc.npz \
  --vocab-file data/wave2b/vocab_v2.json \
  --ckpt data/wave2b/ckpt_controls/b3long_v2_s42.pt \
  --out reports/provenance/W2B/devpred_b3long_v2_s42.json

# Bootstrap
python runner/w2b_domain_controls_analyze.py \
  --out reports/provenance/W2B/domain_controls_bootstrap.json
```

### 10.4 환경

- Windows 11, Ryzen 5 7600 6C/12T, 15.6GiB RAM, **GPU 없음(CPU only)**
- Python 3.12 `.venv`, ORT 1.31.1 CPU EP
- 비용 **$0**, VPS/GPU 미사용
- control caches 약 **20.5GB**는 D-074b에 따라 보존; 자동 삭제 금지

### 10.5 시간 회계

- B3 10h frames 기준 **10.0221h**, manifest 합 **10.0024h** (0.2% 차이)
- B3-long 10h **10.0130h**, B3-zeroth-long 10h **10.0125h**
- B3-long 학습 **5,377.3초 (1.494h)**, B3-zeroth-long **5,461.3초 (1.517h)**

---

## 11. 타임라인·커밋

| 시점 | 사건 | 커밋/파일 |
|---|---|---|
| 2026-11-05 전반 | V2 gate PASS, dev/test/FLEURS | D-071, `9fe5bd0` |
| 2026-11-05 | V2 gate 외부 검토 요청서(768줄) | `9f1ed7d`, `ac1fd82` |
| 2026-11-05 | 3-AI 검토 3/3 B | `28fb54d` |
| 2026-11-05 | 종합보고서 | `W2B_V2_GATE_3AI_SYNTHESIS.md` |
| 2026-11-05 | B0′ matched controls D-072/D-073 | `cd83c1a` |
| 2026-11-05 | domain/length plan D-074, D-074a, D-074b | `5c7fc0b`, `afee409`, `6342a9a` |
| 2026-11-05 | domain/length 결과 D-075 | `069879f` |
| 현재 | 최신 `origin/main` | **`069879f`, 0/0** |

---

## 12. 답변 형식

다음 형식으로 답해 달라.

```text
## 0. 결론 (A/B/C/D)
## 1. Q1~Q11
### Q1
- 판정: A/B/C/D
- 이유:
- 필수 수정:
### Q2
...
## 2. Must-fix 표
| ID | 지적 | 필수 조치 | 우선순위 | LoRA 차단 |
## 3. 다음 실험 우선순위
1.
2.
3.
## 4. 대외 주장 문장 (수정안)
## 5. 불확실한 점
```

특히 다음을 명시해 달라.

1. **지금 당장 추가해야 하는 최소 실험 1개**
2. **지금 당장 해서는 안 되는 주장 1개**
3. **LoRA로 넘어가도 되는 조건**
4. **non-Kspon short 4h가 없는데도 domain 결론을 유지할 수 있는지**
5. **step-matched B3-long의 정확한 설계**

---

## 13. 검토자에게 마지막으로

이 프로젝트는 “성공적인 결과를 포장하는 것”이 목적이 아니다. **어떤 주장이 아직 이르고, 어떤 control이 결정적인지**를 알고 싶다.

- 좋은 결과처럼 보이는 숫자(특히 B3-long 0.2839, B3-zeroth-long 0.3656)를 **과대해석하지 않도록** 비판해 달라.
- 데이터 선택·OOV·step·test 재사용·text overlap 중 **어느 것이 결론을 가장 취약하게 만드는지** 순위를 매겨 달라.
- “지금 멈추고 LoRA로 가라” 또는 “step-matched/non-Kspon short를 먼저 하라” 중 하나를 권고해 달라.
