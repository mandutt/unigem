# 외부 검토 요청서 — Wave 2B V2 reader-only 결과와 다음 단계

- 작성일: 2026-11-05 (KST)
- 프로젝트: `mandutt/unigem` (비공개, branch `main`)
- 검토 기준 커밋: **`9d1aba6`** (요청서 작성 직전 `origin/main`; `origin/main`과 0/0)
- 직전 검토 라운드: **`w2b_2c_short_v2`** (2026-11-04, 3/3 **B — Must-fix 반영 후 pilot**)
  - 직전 요청서 기준: `1db2d0e`
  - 직전 검토 기록: `e1d6280`
  - 직전 종합: `reports/W2B_2C_SHORT_V2_3AI_SYNTHESIS.md`
- 이번 문서의 목적: **프로젝트 이력을 처음 보는 외부 AI가 저장소의 과거 문서를 읽지 않고도, V2 reader-only 결과의 타당성과 다음 단계를 판단**할 수 있게 하는 자기완결형 검토 요청서
- 문서 상태: **검토 요청**이며 승인 문서가 아니다. 검토 의견은 사용자 승인 전 구현·주장에 반영하지 않는다.

---

## 0. 검토자에게 — 이번 라운드의 핵심

직전 라운드(2026-11-04)는 **설계 v2 검토**였고, 3개 모델 모두 “Must-fix를 반영하면 pilot은 가능하지만 v2 그대로 시작은 반대”라는 **B 판정**을 냈다. 그 뒤 사용자가 v3 설계와 6개 조건을 승인했고, 우리는 실제로 데이터 준비·학습·dev 선택·sealed test까지 완료했다.

이번 라운드의 질문은 하나로 요약된다.

> **현재의 V2 reader-only 결과를 “사전등록된 gate PASS”로 인정할 수 있는가?**
> 인정할 수 있다면 **어떤 주장까지** 허용되고, 다음 단계는 무엇인가?
> 인정할 수 없다면 **무엇이 결정적인 결함**이며, 최소한 어떤 추가 실험이 필요한가?

특히 다음을 우선해 달라.

1. **B0′ 6h vs B3 10h** 비교에서 **추가 optimizer step(3.13×)·추가 audio exposure(1.67×)·Kspon domain·짧은 길이 분포**가 뒤섞여 있는데, 현재 gate를 “데이터 효과”라고 불러도 되는가?
2. **V2 vocabulary의 2-pass 구성**(draft vocab으로 short를 고르고, 그 short refs로 final vocab을 만든 뒤 다시 short를 고르는 방식)이 선택 편향을 만드는가?
3. **sealed test 2,400을 이미 1회 사용**했으므로, 앞으로의 20-epoch·seed 43·LoRA 결과를 어떤 지위로 보고해야 하는가?
4. **B3-nat는 dev에서만 평가**했는데, sampler 효과가 없다고 말할 수 있는가?
5. 다음 우선순위를 **seed 43 재현 / step-matched control / 20-epoch 3-arm / LoRA** 중에서 어떻게 정할 것인가?

칭찬보다 **결함·누락·대안·중단 기준**을 우선해 달라. 확실하지 않으면 “불확실”이라고 명시해 달라.

---

## 1. 자기완결 맥락

### 1.1 프로젝트

EmbeddingGemma 2(EG2)의 **오디오 타워를 재사용**해 다음 과제를 검증하는 연구 프로젝트다.

- F1 언어판정
- **F2 STT**
- F3 비전 태깅
- F4 맞춤법 교정
- F5 메모리 요약
- F6 STT 후처리

F2의 **제품 경로는 이미 komixv2/whisper로 확정**돼 있고(D-057), EG2 기반 F2는 **연구 트랙**이다. 이 연구가 실패해도 제품 경로는 바뀌지 않는다.

### 1.2 이번 실험의 위치

- EG2 오디오 타워는 **frozen**이다.
- 그 위에 작은 **CTC character reader**(4층 Transformer, d=384, 6 head, FF=1536, **9,183,922 params**)를 붙인다.
- Wave 2A-lite에서 6시간 데이터·동결 타워로 FLEURS ko dev CER **0.20913**을 냈고, Kspon eval_other에서는 **0.35143**으로 도메인/길이 갭이 남았다.
- Wave 2B+2C-short의 목표는 다음 두 개입을 분리하는 것이다.
  - **2B**: EG2 오디오 타워 상위층 LoRA
  - **2C-short**: Kspon train에서 **짧은 발화 4시간**을 추가
- 이번 라운드는 그중 **reader-only** 파일럿이다. **LoRA B1/B2는 아직 구현·실행하지 않았다.**

### 1.3 용어

| 용어 | 뜻 |
|---|---|
| **B0′** | Wave 1 6시간만 사용한 reader. 이번 V2의 baseline |
| **B3** | Wave 1 6시간 + Kspon short 4시간 = 10시간, **balanced sampler** |
| **B3-nat** | B3와 **같은 10시간 clip ID 집합**, **natural sampler**. sampler-only control |
| **CER** | character error rate. 공백 무시·구두점 제거의 통일 정규화 |
| **dev 500** | Kspon eval_clean에서 duration 층화로 뽑은 500발화. arm 선택·freeze에 사용 |
| **test 2,400** | 같은 eval_clean의 나머지 2,400발화. **sealed holdout** |
| **spare 90** | eval_clean의 나머지 90발화. 평가 미사용 |
| **V1** | 2A의 1,101자 vocabulary |
| **V2** | V1 순서·ID를 보존하고 신규 228자를 추가한 **1,329자**(head 1,330행) |
| **gate** | 사전등록 판정: `Δ = CER(B0′) − CER(candidate)`, **Δ ≥ 1.0%p AND paired utterance bootstrap 95% CI 하한 > 0** |
| **in-domain holdout** | 같은 Kspon 코퍼스 계열의 절차적 holdout. **화자 독립 test가 아님** |

### 1.4 이번 라운드에서 **하지 않은** 것

- LoRA B1/B2 구현·학습
- GPU 대여·Modal 패키징
- 20-epoch 연장(D-070)
- seed 43 재현
- FLEURS test 재사용
- 화자 독립 holdout 확보
- Kspon long-clip control / non-Kspon short control
- B3-nat의 test 평가

---

## 2. 직전 검토 이후 진행 내역

### 2.1 커밋 범위

직전 요청서 기준 `1db2d0e`부터 현재 `9d1aba6`까지 **26개 커밋**이다. 주요 커밋만 묶으면 다음과 같다.

| 커밋 | 내용 |
|---|---|
| `ac253bc` | v3 설계 확정, D-067, preflight addendum |
| `51d9e3f` | eval split 감사, eval manifests, short-selection 도구 |
| `e5ac36a` | B0′ init, balanced sampler, grad accumulation, 10h feature merge |
| `238f81f` | V1 B0′ 6h 결과 기록 |
| `b30ef32` | short OOV 비율 보고, B0′ baseline |
| `3e91684` | `d5_reader.py` CUDA 선택·resumable checkpoint |
| `84915f8` | W2B data-finish watcher |
| `c614258` | V1 10h cache·V1 OOV caveat |
| `6c003df` | V2 vocabulary·OOV audit·V2 10h cache |
| `168c05a` | V2 vocab 확정, remapped B0′ 학습 |
| `3f39302` | B3/B3-nat chain queue |
| `3f75b12` | final B0′ checkpoint 대기 버그 수정 |
| `ed4d05d` | W2B watchdog(B0′ 자동 resume, B3/B3-nat 경고) |
| `342c569` | B0′ V2 baseline 기록 |
| `5fb03be` | B3 V2 결과 기록 |
| `6900d0a` | **D-070**: 20-epoch 연장 보류·exploratory |
| `628de33` | dev gate 후 B3 candidate freeze |
| `9fe5bd0` | **D-071**: V2 reader-only gate PASS |
| `9d1aba6` | V2 dev prediction·B3 chain provenance |

### 2.2 직전 검토의 공통 Must-fix

직전 3-AI는 **3/3 B**였고, A(그대로 pilot)는 0/3이었다. 공통 Must-fix는 6건이었다.

1. vocab·OOV·reader head 계약을 하나로 고정
2. B3-nat 정의를 A(같은 10h clip set + natural sampler)로 확정
3. gate의 후보 선택 편향 제거, 최소 효과 크기 명시
4. B0′/B1 초기화·feature parity 범위 명확화
5. test 적격률·0.5초 미만·ID 중복·길이 대표성
6. 디스크·streaming·LoRA 학습 속도

이번 문서 §6에서 각 항목의 **실제 조치·상태**를 대응표로 제시한다.

### 2.3 이후 추가 결정

| 결정 | 내용 |
|---|---|
| **D-067** | v3: vocab V1, B3-nat-A, full gate `Δ≥1.0%p + CI 하한>0`, dev primary, 0.28초 test 하한, reader-only 먼저 |
| **D-068** | eval_clean filename shuffle 확인 → **block split 미적용**, duration 층화 유지 |
| **D-069** | **V1 short OOV 90.727%** → V2 채택. V1 1,101 + 신규 228 = 1,329자, head remap |
| **D-070** | 20-epoch 연장은 **보류·exploratory**. B3만 늘리지 않는다. 필요 시 3-arm 동일 20-epoch 또는 seed 43 먼저 |
| **D-071** | **V2 reader-only gate PASS**. dev·test·FLEURS guardrail 결과 기록 |

---

## 3. 데이터·프로토콜

### 3.1 Wave 1 6시간

- `data/wave1/manifest.jsonl`: **2,384클립 / 6.0008시간**
- 구성: **Zeroth 1,534 + Kconf 850**
- **Kspon은 0** — short 4시간이 최초의 Kspon 도메인 데이터다.
- 따라서 B0′는 “Kspon을 전혀 보지 않은 6시간 모델”이고, B3는 “Kspon short 4시간을 추가한 10시간 모델”이다. 이 차이는 단순한 길이 추가가 아니라 **도메인 추가**이기도 하다.

### 3.2 Kspon short 4시간

- 원본: KsponSpeech_05 train (AI Hub 50215, `KsponSpeech_05.zip` 15,641,266,705 bytes)
- **V2 최종 short**: **5,079클립 / 4.0016시간**, 124 folders
- duration bin:

| bin | 시간 | 클립 |
|---|---:|---:|
| 0–2초 | 1.0002h | 2,368 |
| 2–4초 | 1.4004h | 1,713 |
| 4–6초 | 0.8005h | 585 |
| 6–8초 | 0.8006h | 413 |

- 후보 OOV 제외: **2,319 / 97,628 = 2.3753%** (D-067 5% 기준 통과)
- V1 short는 5,119클립/4.0023h였지만 **OOV 제외율 90.727%**로 폐기했다. V1 4시간으로 B3를 학습하지 않았다.
- 10시간 cache는 **2,384 + 5,079 = 7,463클립 / 10.0221시간**이다.

### 3.3 V2 vocabulary — 2-pass 구성과 잠재적 순환

V2는 다음 순서로 만들어졌다.

1. **draft V2**: V1 1,101자 + Wave 1 6h manifest + **Kspon train 전체 620,000 transcript** → **2,342자** (`vocab_v2_alltrain.json`, 감사용 보존)
2. draft V2로 short candidate를 1차 선별 → **5,066클립 / 4.0035시간**
3. **final V2**: V1 1,101자 순서·ID 보존 + Wave 1 6h + **1차 선별된 short refs**의 신규 문자 228자 → **1,329자**
4. final V2로 short를 **재선별** → **5,079클립 / 4.0016시간**, 후보 OOV **2.3753%**

중요한 사실:

- **eval/test 텍스트는 vocabulary 구축에 사용하지 않았다.** test는 coverage audit에만 사용했다.
- draft 2,342자는 학습에 사용하지 않았다. 최종 학습은 **1,329자 V2**만 사용했다.
- 2A head 1,102행을 문자 정체성으로 V2 1,330행에 remap했고, **shared 1,101자 복사**, 신규 228자 초기화, `missing=0 unexpected=0`을 확인했다.
- **그러나 final V2의 문자 집합은 “draft로 1차 선택된 short refs”에 의존**한다. 즉 short 선택 → vocab → short 재선택의 **2-pass loop**가 있다. eval/test 누출은 아니지만, short subset의 문자 coverage가 selection에 의해 조건화된다. 이 점이 Q3의 쟁점이다.

### 3.4 OOV audit

| Set | Clips | OOV clips | OOV rate | OOV chars / total | Char rate |
|---|---:|---:|---:|---:|---:|
| dev 500 | 500 | 5 | 1.0000% | 5 / 8,247 | 0.0606% |
| test 2,400 | 2,400 | 45 | 1.8750% | 53 / 40,788 | 0.1299% |
| spare 90 | 90 | 1 | 1.1111% | 1 / 1,473 | 0.0679% |

- test OOV는 주로 희귀 한글·숫자·기호다.
- 두 arm(B0′/B3)은 **같은 V2 vocab**을 쓰므로 OOV clip은 양쪽에 동일하게 존재한다. 절대 CER의 하한을 만들지만, arm 차이를 직접 왜곡하지는 않는다.
- **V1 기준 test OOV는 7.7% 행/0.53% 문자**였고, V2에서 크게 줄었다.

### 3.5 dev / test / spare

- eval_clean 3,000발화 중 16초 초과 10건 제외 → 적격 **2,990**
- **dev 500**: duration 층화, 기존 D-β 100 포함, 0.4263시간, 참조 7,755자
- **test 2,400**: duration 층화, 2.0929시간, 참조 38,224자
- **spare 90**: 0.0769시간, 평가 미사용
- **dev∩test = 0**
- **화자 ID 없음**: Kspon 원논문은 개인정보 보호를 위해 filename을 변경·shuffle했다. 따라서 **화자 독립 test가 아니며**, bootstrap은 **utterance-level paired bootstrap**만 사용한다.

### 3.6 test의 길이 대표성

| 구간 | test 2,400 | 비율 |
|---|---:|---:|
| 0–2초 | 1,151 | 47.96% |
| 2–4초 | 633 | 26.38% |
| 4–8초 | 431 | 17.96% |
| 8–16초 | 185 | 7.71% |
| **≤4초** | **1,784** | **74.33%** |

- test는 eval_other(≤4초 57.2%)보다 **훨씬 짧은 발화 중심**이다.
- 8–16초 bin은 185건으로, bin별 결론의 검정력이 낮다.
- 0.5초 미만은 **28건**, 최소 0.286초. test feature 추출은 `--min-dur 0.28`로 수행해 **2,400/2,400을 유지**했다. CTC에서 실제로 실패한 clip은 오류로 계산한다.

### 3.7 test overlap — 최종 재확인

직전 검토에서 “short/B3-nat 선별 후 test overlap을 다시 확인하라”는 Must-fix가 있었다. 최종 manifest로 재확인한 결과는 다음과 같다.

| 비교 | 교집합 |
|---|---:|
| test ∩ short V2 (5,079) | **0** |
| test ∩ short V1 (5,119) | **0** |
| test ∩ Wave 1 train (2,384) | **0** |
| dev ∩ short V2 | **0** |
| spare ∩ short V2 | **0** |
| test ∩ eval_other | **0** (기존 preflight) |

- **B3-nat는 B3와 같은 short V2 clip ID 집합**이므로 test ∩ B3-nat도 **0**이다.
- **화자 중복은 확인할 수 없다.** eval_clean에 speaker ID가 없고, Kspon train과 eval_clean의 화자 대응도 공개 메타데이터로 확인 불가하다. “화자 독립”이라고 주장하지 않는다.

---

## 4. 학습·평가

### 4.1 공통 조건

- Reader: 4층 Transformer, d=384, 6 head, FF=1536, CTC character head
- Params: **9,183,922**
- Init: `data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt` (2A reader를 V2 head로 문자 remap)
- Batch 2, grad accumulation 4 → micro-batch 8
- Seed 42, 12 epochs, patience 4, cosine schedule
- CPU, 6 threads, **GPU 미사용**
- Feature: frozen EG2 audio tower의 F-C-concat 4,096d cached features

학습 명령의 핵심은 다음과 같다.

```text
B0′:
d5_reader.py --features data/wave1/feats/fc.npz
  --dev-features data/wave2b/feats_dev/fc.npz
  --vocab-file data/wave2b/vocab_v2.json --retarget
  --arch base --arm b0p_v2_s42
  --init-ckpt data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt
  --epochs 12 --patience 4 --batch 2 --grad-accum 4
  --seed 42 --threads 6 --device cpu
  --ckpt-dir data/wave2b/ckpt_v2

B3:
d5_reader.py --features data/wave2b/feats_10h_v2/fc.npz
  --dev-features data/wave2b/feats_dev/fc.npz
  --vocab-file data/wave2b/vocab_v2.json --retarget
  --arch base --arm b3_v2_s42
  --init-ckpt data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt
  --epochs 12 --patience 4 --batch 2 --grad-accum 4
  --seed 42 --threads 6 --device cpu
  --sampler balanced --ckpt-dir data/wave2b/ckpt_v2

B3-nat:
  같은 명령에서 --arm b3nat_v2_s42 --sampler natural
```

- balanced sampler: `secs = lens/25.0`, `b4 = secs<=4`, `b8 = 4<secs<=8`, `b16 = secs>8`, 확률 `[0.40, 0.30, 0.30]`
- B3-nat는 **B3와 같은 10시간 clip ID 집합**에 natural sampler만 적용했다.

### 4.2 학습 예산 — **중요한 confound**

| Arm | unique audio | epochs | steps/epoch | total optimizer steps | audio exposure | dev CER |
|---|---:|---:|---:|---:|---:|---:|
| B0′ 6h | 6.0008h | 12 | 298 | **3,576** | **72.0h** | 0.3701 |
| B3 10h balanced | 10.0221h | 12 | 933 | **11,196** | **120.3h** | 0.2682 |
| B3-nat 10h natural | 10.0221h | 12 | 933 | **11,196** | **120.3h** | 0.2633 |
| B3 epoch 4 diagnostic | 10.0221h | 4 | 933 | **3,732** | 40.1h | 0.2903 |

- B3는 B0′보다 **optimizer step이 3.13×**, **audio exposure가 1.67×** 많다.
- 따라서 **B0′ − B3 = +10.187%p**는 “데이터만의 효과”가 아니라 **추가 학습량 + Kspon domain + 길이 분포**의 결합이다.
- **B3 epoch 4**는 B0 epoch 12와 step 수가 비슷하지만(3,732 vs 3,576), 12-epoch cosine schedule의 epoch 4라서 LR이 같지 않고, checkpoint도 보존하지 않았다. **exploratory diagnostic**일 뿐 gate가 아니다. 그럼에도 이 지점에서 B3가 **0.2903 vs B0′ 0.3701 (+7.98%p)**로 앞서는 것은 “step 수만으로 전부 설명되지는 않는다”는 신호다.
- **D-070의 20-epoch 3-arm도 이 confound를 해결하지 않는다.** B0-20은 5,960 step/120.0h, B3-20은 18,660 step/200.4h로 여전히 **3.13× step, 1.67× audio** 차이다. 20-epoch는 “수렴 확인”이지 “compute-matched causal test”가 아니다.

### 4.3 Dev 500 결과

| Arm | Best epoch | Dev CER | Errors / chars |
|---|---:|---:|---:|
| B0′ 6h | 12 | **0.3701** | 2,870 / 7,755 |
| B3 10h balanced | 12 | **0.2682** | 2,080 / 7,755 |
| B3-nat 10h natural | 11 | **0.2633** | 2,042 / 7,755 |

B3-nat final epoch 12은 0.2634였다. early stopping은 어느 arm에서도 발동하지 않았다.

B3 epoch 곡선:

| Epoch | B3 dev CER |
|---:|---:|
| 1 | 0.3226 |
| 2 | 0.3090 |
| 3 | 0.3024 |
| 4 | 0.2903 |
| 5 | 0.2941 |
| 6 | 0.2814 |
| 7 | 0.2807 |
| 8 | 0.2735 |
| 9 | 0.2754 |
| 10 | 0.2709 |
| 11 | 0.2696 |
| 12 | **0.2682** |

### 4.4 Dev bootstrap

Paired utterance bootstrap, 20,000 resamples, seed 42, percentile 95% CI:

| 비교 | Δ CER | 95% CI |
|---|---:|---:|
| B0′ − B3 | **+10.187%p** | **[+9.107, +11.328]%p** |
| B0′ − B3-nat | +10.677%p | [+9.624, +11.804]%p |
| B3 − B3-nat | +0.490%p | **[-0.229, +1.205]%p** |

- B3−B3-nat의 CI는 0을 포함한다 → **sampler 효과는 유의하지 않다.**
- B3-nat가 점추정에서 0.49%p 더 좋지만, 이 차이는 잡음과 구분되지 않는다.

### 4.5 Sealed test 2,400 — 1회

test는 **B3를 dev에서 선택·freeze한 뒤** 한 번만 평가했다. B3/B0′의 checkpoint sha256은 `test_freeze.json`에 기록했다.

| Arm | Test CER | Errors / chars | n |
|---|---:|---:|---:|
| B0′ 6h | 0.359643 | 13,747 / 38,224 | 2,400 |
| B3 10h balanced | **0.262270** | 10,025 / 38,224 | 2,400 |

- **Δ = +9.737%p**
- paired utterance bootstrap 95% CI **[+9.228, +10.258]%p**
- **gate 기준(Δ≥1.0%p, CI 하한>0)을 충족**한다.

오류 분해:

| 항목 | B0′ | B3 |
|---|---:|---:|
| substitution | 8,691 | 6,372 |
| deletion | 4,159 | 2,685 |
| insertion | 897 | 968 |
| blank (empty hyp) | 7 | 2 |
| length ratio (hyp/ref) | 0.9147 | 0.9551 |

- B3는 **deletion을 크게 줄였고**(4,159→2,685), length ratio가 1에 가까워졌다.
- insertion은 897→968으로 소폭 증가했다.

길이 구간별 test CER:

| 구간 | n | B0′ CER | B3 CER |
|---|---:|---:|---:|
| 0–2초 | 1,151 | 0.4788 | 0.3357 |
| 2–4초 | 633 | 0.3751 | 0.2726 |
| 4–8초 | 431 | 0.3229 | 0.2368 |
| 8–16초 | 185 | 0.2912 | 0.2228 |
| 전체 | 2,400 | 0.3596 | 0.2623 |

- B3는 **모든 길이 구간에서** B0′보다 좋다. 특히 0–2초에서 +14.3%p, 2–4초에서 +10.2%p 개선됐다.
- 이는 “짧은 발화 보완”과 방향이 일치하지만, **Kspon domain 추가**와 **추가 step**도 함께 작용했으므로 인과 귀속은 별도 문제다.

### 4.6 FLEURS dev guardrail

| Arm | FLEURS dev CER | Errors / chars |
|---|---:|---:|
| B0′ | 0.209770 | 1,649 / 7,861 |
| B3 | **0.207607** | 1,632 / 7,861 |

- B3는 **−0.216%p**로 악화되지 않았다(guardrail: ≤ +1.0%p).
- FLEURS dev는 2A에서도 사용한 dev다. **FLEURS test는 사용하지 않았다.**

### 4.7 B3-nat / sampler

- B3-nat는 **test를 평가하지 않았다.**
- dev에서 B3-nat 0.2633 vs B3 0.2682, Δ 0.49%p, CI [-0.229, +1.205] → **sampler 효과는 유의하지 않다.**
- B3-nat는 candidate가 아니며, test 후보로 선택하지 않았다.
- 따라서 “balanced sampler가 natural sampler보다 낫다/나쁘다”는 주장은 하지 않는다. 현재 결론은 **“이 데이터 규모에서 sampler 차이는 작고, 데이터 추가 효과가 두 sampler 모두에서 관찰된다”**까지다.

### 4.8 Test freeze / 재사용

- B3는 dev 500에서 선택해 **test 전에 freeze**했다.
- test는 **1회**만 평가했다.
- `max(B2,B3)` 같은 test-time 선택은 하지 않았다.
- **그러나 test 2,400은 이제 사용됐다.** 앞으로 20-epoch·seed 43·LoRA를 같은 test로 평가하면 그것은 **confirmatory test가 아니라 exploratory/post-hoc**이다.
- FLEURS test는 아직 미사용이다. spare 90은 작지만 남아 있다.

---

## 5. Gate 판정

### 5.1 사전등록 기준

- `Δ = CER(B0′) − CER(candidate)`
- **점추정 Δ ≥ 1.0%p**
- **paired utterance bootstrap 95% CI 하한 > 0**
- primary는 **dev 500에서 선택·freeze**
- test는 freeze 후 1회
- FLEURS dev no-regression: +1.0%p 이내 악화 금지

### 5.2 판정표

| 항목 | 요구 | 결과 |
|---|---|---|
| Dev Δ | ≥1.0%p, CI 하한>0 | **PASS** (+10.187%p, CI +9.107) |
| Test Δ | ≥1.0%p, CI 하한>0 | **PASS** (+9.737%p, CI +9.228) |
| FLEURS dev | ≤ +1.0%p 악화 | **PASS** (−0.216%p) |
| Test 선택 | frozen candidate, no max | **PASS** (B3 freeze 후 1회) |
| B3-nat | 별도 control | **sampler 효과 유의하지 않음** |

**V2 reader-only gate: PASS (사전등록된 recipe-level 비교).**

### 5.3 이 판정이 **말하지 않는** 것

- “Kspon short 4시간만의 순수 데이터 효과”라고 말하지 않는다.
- “화자 독립 일반화”라고 말하지 않는다.
- “B3-nat보다 B3가 우수하다”고 말하지 않는다.
- “20 epoch면 더 좋아진다”고 말하지 않는다(D-070은 가설).
- “LoRA가 필요 없다/있다”고 말하지 않는다(B1/B2 미실행).

---

## 6. 직전 Must-fix 대응표

| Must-fix | 조치 | 상태 | 남은 쟁점 |
|---|---|---|---|
| **MF-1** vocab/OOV/head 계약 | V1 short OOV 90.727% → **V2 1,329자**, 1,101 shared remap, head 1,330, `missing=0/unexpected=0` | **이행** | V2 2-pass selection loop (Q3) |
| **MF-2** B3-nat 정의 | **A안**: B3와 같은 10h clip ID, natural sampler | **이행** | test 미실시 (Q4) |
| **MF-3** gate 선택 편향/최소효과 | dev 500에서 B3 freeze, test 1회, Δ≥1.0%p + CI | **이행** | test 재사용 불가 (Q5) |
| **MF-4** B0′/B1 parity | B0′/B3 같은 init·cached feature 경로; B1/B2 미실행 | **부분 이행** | step/audio exposure confound (Q2) |
| **MF-5** test 적격률·0.5초·split | `--min-dur 0.28`, 2,400/2,400 유지; split 감사; overlap 0 | **이행** | 화자 독립 불가 |
| **MF-6** 디스크·streaming·LoRA 속도 | V2 10h cache 7.39GB, memmap, CPU 학습 완료 | **부분 이행** | LoRA sec/step·GPU 미측정 |

### 6.1 이번 라운드에서 새로 드러난 쟁점

| ID | 쟁점 | 상태 |
|---|---|---|
| **N1** | B0′ vs B3의 **step 3.13× / audio 1.67×** 차이 | 미해결, Q2 |
| **N2** | B3의 추가 데이터는 **Kspon domain + short length**가 결합 | 미해결, Q2 |
| **N3** | V2 vocab의 **2-pass selection loop** | 미해결, Q3 |
| **N4** | test 2,400 **1회 사용 완료** | 향후 confirmatory 불가, Q5 |
| **N5** | B3-nat **test 미실시** | dev-only 결론, Q4 |
| **N6** | D-070 20-epoch는 **compute-matched가 아님** | Q6 |

---

## 7. 열린 confound와 한계

### 7.1 Compute / exposure confound

B3는 10시간 데이터를 12 epoch 학습해 **11,196 step / 120.3시간 exposure**를 봤고, B0′는 6시간을 12 epoch 학습해 **3,576 step / 72.0시간**을 봤다. 두 모델의 차이는 “데이터”만이 아니라 **더 많은 step과 더 많은 audio exposure**를 포함한다.

B3 epoch 4 diagnostic은 step 수가 B0 epoch 12와 비슷한 지점에서도 B3가 +7.98%p 앞선다는 신호를 주지만, 다음 이유로 **clean control이 아니다.**

- 12-epoch cosine schedule의 epoch 4라서 LR이 B0 epoch 12와 다르다.
- epoch 4 checkpoint를 보존하지 않았다.
- B3 epoch 4는 40.1시간 exposure로 B0의 72.0시간보다 적다.

### 7.2 Domain / length confound

- B0′의 6시간은 **Zeroth + Kconf**이고 Kspon은 0이다.
- B3는 여기에 **Kspon train short 4시간**을 추가한다.
- 따라서 B3의 gain은 ① Kspon domain/recording/style, ② short-length distribution, ③ 추가 step/audio가 결합되어 있다.
- **Kspon long-clip control**도, **non-Kspon short control**도 없다.
- B3-nat는 sampler만 바꾸므로 domain/length confound를 풀지 않는다.

### 7.3 V2 vocabulary selection loop

- final V2는 **draft V2로 1차 선택된 short refs**에서 만들어졌고, 그 final V2로 short를 다시 선택했다.
- eval/test 누출은 없지만, short subset의 문자 coverage가 **selection-dependent**가 된다.
- test OOV 1.875% clip/0.1299% 문자는 absolute CER에 영향을 주지만, B0/B3가 같은 vocab을 쓰므로 arm 차이의 주원인은 아니다.
- **V2 vocab을 pre-selection candidate refs에서 고정**하는 편이 더 깨끗한지 검토가 필요하다.

### 7.4 Test의 성격

- test는 **Kspon eval_clean**의 in-domain holdout이다.
- 화자 ID가 없고 filename이 shuffle돼 **화자 독립 test가 아니다.**
- test는 ≤4초가 74.33%로 **짧은 발화 중심**이다.
- 8–16초 bin은 185건뿐이다.
- Kspon train short와 eval_clean의 **화자 중복 여부는 확인 불가**하다.

### 7.5 Test 재사용

- test 2,400은 12-epoch B3 vs B0′에 **한 번 사용**됐다.
- 20 epoch, seed 43, LoRA를 같은 test로 평가하면 **새 confirmatory test가 아니다.**
- FLEURS test는 미사용이나, Kspon 결론을 FLEURS로 대체할 수는 없다.
- spare 90은 너무 작아 주 gate로 쓰기 어렵다.

### 7.6 B3-nat

- dev-only control이다.
- B3-nat가 B3보다 0.49%p 좋지만 CI가 0을 포함한다.
- B3-nat의 test를 새로 돌리면 exploratory가 되고, test 재사용 문제가 커진다.

### 7.7 LoRA / GPU

- B1/B2 LoRA는 **미구현**이다.
- `d5_reader.py`는 `--device cuda`와 `--resume`을 지원하지만, Modal 패키징·Volume 업로드·T4/L4/L40S smoke는 **미완료**다.
- GPU는 대여하지 않았다. 비용 $0.
- LoRA의 sec/step, 메모리, OOM, preemption 대응은 아직 실측하지 않았다.

### 7.8 D-070

- D-070은 “20 epoch가 더 좋을 수 있다”는 **가설**을 기록한 것이지 실행 계획이 아니다.
- 20 epoch를 하려면 B0′-20/B3-20/B3-nat-20을 **같은 20-epoch cosine schedule**로 다시 해야 한다.
- 그러나 20 epoch도 step/audio 비율(3.13×/1.67×)을 없애지 않는다. **compute-matched causal test가 아니다.**
- 20 epoch 결과를 test로 평가하면 **exploratory**다.

---

## 8. 검토 질문

각 질문에 대해 **① 판정 ② 근거 ③ 필수 조치 ④ 다음 단계 차단 여부**를 적어 달라. 가능하면 A/B/C 중 하나로 명시해 달라.

### Q1. Gate PASS의 지위

현재 결과는 사전등록 기준(dev/test Δ≥1.0%p + CI 하한>0, FLEURS no-regression, B3 freeze 후 test 1회)을 충족한다.

질문:

- 이 gate를 **“V2 reader-only recipe-level PASS”**로 인정할 수 있는가?
- 아니면 compute/domain confound 때문에 **“exploratory/INCONCLUSIVE”로 강등**해야 하는가?
- 이 판정을 뒤집을 수 있는 **결정적 결함**이 있는가?

### Q2. 인과 귀속 — 무엇을 control해야 하는가

B3는 B0′보다 **step 3.13×, audio 1.67×, Kspon domain, short length**가 모두 다르다.

질문:

- 현재 gate의 estimand를 **“이 recipe로 10시간을 학습했을 때의 효과”**로 제한하면 정당한가?
- “short 4시간 데이터 효과”라고 주장하려면 **최소 어떤 control**이 필요한가? 예:
  - B0′를 **38 epoch**로 학습해 step 수를 B3-12와 맞춤
  - B3를 **4 epoch**로 학습해 B0′-12와 step 수를 맞춤
  - B0′ 6시간을 **10시간으로 repeat**해 audio exposure를 맞춤
  - **Kspon long-clip 4시간** 또는 **non-Kspon short 4시간** control
- 위 선택지의 우선순위와 각각의 해석 한계를 달라.

### Q3. V2 vocabulary 2-pass selection

V2는 draft 2,342자로 short를 1차 선택하고, 그 refs로 final 1,329자를 만든 뒤 short를 재선택했다.

질문:

- 이 **selection-vocabulary loop**가 short subset을 편향시키는가? 그 크기는 test OOV 1.875%·문자 0.1299%로 제한적으로 볼 수 있는가?
- 더 깨끗한 대안은 무엇인가?
  - pre-selection eligible short refs로 vocab 고정
  - V1 + Wave1 + all Kspon train transcript(2,342) 사용
  - V1 유지(1,101) + OOV clip 제외
- final V2를 다시 만들어야 하는가, 아니면 현재 결과를 **“V2 vocab에 조건화된 결과”**로 표기하면 충분한가?

### Q4. B3-nat / sampler

B3-nat는 dev에서 0.2633, B3는 0.2682, Δ 0.49%p, CI [-0.229, +1.205]였다. B3-nat test는 없다.

질문:

- **dev-only**로 “sampler 효과는 유의하지 않다”고 말할 수 있는가?
- B3-nat test를 추가로 돌려야 하는가? 돌린다면 test 재사용 문제를 어떻게 표기해야 하는가?
- B3-nat best epoch 11 vs B3 final epoch 12가 결론에 영향을 주는가?

### Q5. Test 재사용과 confirmatory 지위

test 2,400은 이미 1회 사용됐다.

질문:

- 앞으로 **seed 43, 20-epoch, LoRA**를 같은 test로 평가할 때, 어떤 결과까지 **confirmatory**라고 부를 수 있는가?
- 새 confirmatory 주장을 하려면 **spare 90 / FLEURS test / 새 Kspon holdout** 중 무엇이 최소 요건인가?
- 현재 결과를 논문·블로그에 쓸 때 test를 **“in-domain procedural holdout, 1회 사용”**으로 표기하면 충분한가?

### Q6. 다음 우선순위

후보:

1. **seed 43 12-epoch 재현** (B0′/B3, dev 중심; 약 3시간 CPU)
2. **B0′-38 step-matched** (B3-12와 step 수 맞춤; 약 3시간)
3. **B3-4 step-matched diagnostic** (B0′-12와 step 수 맞춤; checkpoint 재학습 필요)
4. **B0′-20/B3-20/B3-nat-20** (D-070; 약 7~8시간, compute-matched 아님)
5. **B1/B2 LoRA** (GPU·구현 선행)
6. **Kspon long-clip / non-Kspon short control** (데이터 추가)

질문:

- **가장 먼저** 무엇을 해야 하는가? 이유는?
- LoRA 전에 반드시 끝내야 하는 항목과, LoRA와 병행 가능한 항목을 분리해 달라.
- 20 epoch는 지금 가치가 있는가, 아니면 step-matched control이 더 가치 있는가?

### Q7. LoRA 착수 가능성

B1/B2 LoRA는 아직 구현하지 않았다. 현재 데이터·V2 vocab·test 결과는 reader-only다.

질문:

- 지금 LoRA를 시작해도 되는가?
- 시작 전 **Must-fix**는 무엇인가? (예: V2 vocab 고정, step-matched baseline, test 재사용 정책, GPU parity)
- LoRA의 기대 이득이 **현재 10%p 데이터 효과**와 비교해 충분한가? 어떤 stop/go 기준을 사전등록해야 하는가?

### Q8. 보고·주장의 범위

현재 우리가 말하려는 문장은 다음과 같다.

> “Kspon short-domain 4시간을 추가한 V2 reader-only 실험에서 dev +10.19%p, sealed test +9.74%p의 CER 개선이 있었고, 사전등록 gate를 통과했다.”

질문:

- 이 문장에서 **빼거나 고쳐야 할 표현**은 무엇인가?
- “data effect”, “domain effect”, “short-length effect”, “recipe effect” 중 어느 라벨이 정확한가?
- “화자 독립”, “일반화”, “state-of-the-art” 같은 표현을 피해야 한다는 점에 동의하는가?
- 외부 공개(논문/블로그)에 필요한 **추가 caveat**은 무엇인가?

---

## 9. 사용자/검토자 결정 필요 표

| ID | 결정 | 선택지 | 이번 검토에서 필요한 답 |
|---|---|---|---|
| **R-1** | Gate 지위 | A: recipe-level PASS 인정 / B: caveat부 PASS / C: exploratory로 강등 | Q1 |
| **R-2** | 인과 귀속 | recipe effect만 / step-matched control 추가 / domain control 추가 | Q2 |
| **R-3** | V2 vocab | 현 V2 유지 / pre-selection vocab 재구성 / V1 회귀 | Q3 |
| **R-4** | B3-nat test | 생략 / exploratory test 추가 | Q4 |
| **R-5** | 다음 실험 | seed43 / step-matched / 20-epoch / LoRA / control | Q6 |
| **R-6** | LoRA 착수 | 지금 / Must-fix 후 / 보류 | Q7 |
| **R-7** | 대외 표현 | 현 문장 / 수정 문장 | Q8 |

---

## 10. 재현 정보

### 10.1 주요 파일

- Gate 보고서: `reports/W2B_v2_gate_results.md`
- Dev 결과: `reports/W2B_v2_dev_results.md`
- V2 데이터: `reports/W2B_v2_data_ready.md`
- B3 결과: `reports/W2B_b3_v2.md`
- 결정 로그: `docs/decisions.md` **D-069, D-070, D-071**
- Test freeze: `reports/provenance/W2B/test_freeze.json`
- Dev bootstrap: `reports/provenance/W2B/v2_dev_bootstrap.json`
- Test bootstrap: `reports/provenance/W2B/v2_test_bootstrap.json`
- Test predictions: `reports/provenance/W2B/testpred_b0p_v2_s42.json`, `..._b3_v2_s42.json`
- Dev predictions: `reports/provenance/W2B/devpred_{b0p,b3,b3nat}_v2_s42.json`
- Test breakdown: `reports/provenance/W2B/test_breakdown.json`
- Training budget: `reports/provenance/W2B/training_budget.json`
- Final overlap: `reports/provenance/W2B/overlap_final.json`
- V2 short summary: `data/wave2b/short_4h_v2_summary.json`
- V2 vocab: `data/wave2b/vocab_v2.json` (1,329)
- Draft audit vocab: `data/wave2b/vocab_v2_alltrain.json` (2,342, 학습 미사용)
- V2 10h cache: `data/wave2b/feats_10h_v2/`
- test features: `data/wave2b/feats_test_v2/` (2,400 rows)

### 10.2 Checkpoint sha256

| Arm | Path | sha256 |
|---|---|---|
| B3 candidate | `data/wave2b/ckpt_v2/b3_v2_s42.best.pt` | `8349159e9b449ed4cd2f60e27fac4f955513423593ff34854772e90356e84328` |
| B0′ baseline | `data/wave2b/ckpt_v2/b0p_v2_s42.best.pt` | `c869e66bf205bdf55596f2428aad3452ac813a68f9817bc4eeea77e6b4c27ddd` |
| B3-nat control | `data/wave2b/ckpt_v2/b3nat_v2_s42.best.pt` | `784c3889aa1c92da26080f4d5a00fcafc4e8d065e9075a569ddadd399c10d783` |

### 10.3 Test 재현

```text
# test features (2,400/2,400; min 0.28s)
python train/w1_extract.py \
  --manifest data/wave2b/test_2400.jsonl \
  --out-dir data/wave2b/feats_test_v2 \
  --vocab-in data/wave2b/vocab_v2.json \
  --arms fc --fc-memmap --threads 6 --min-dur 0.28

# decode B0′
python train/d5_reader.py --decode \
  --features data/wave2b/feats_test_v2/fc.npz \
  --vocab-file data/wave2b/vocab_v2.json \
  --ckpt data/wave2b/ckpt_v2/b0p_v2_s42.best.pt \
  --batch 8 --threads 6 \
  --out reports/provenance/W2B/testpred_b0p_v2_s42.json

# decode B3
python train/d5_reader.py --decode \
  --features data/wave2b/feats_test_v2/fc.npz \
  --vocab-file data/wave2b/vocab_v2.json \
  --ckpt data/wave2b/ckpt_v2/b3_v2_s42.best.pt \
  --batch 8 --threads 6 \
  --out reports/provenance/W2B/testpred_b3_v2_s42.json
```

### 10.4 Bootstrap 방법

- unit: **utterance**
- pair: B0′와 candidate의 같은 utterance
- resamples: **20,000**
- seed: **42**
- statistic: `sum(err_B0 - err_candidate) / sum(ref_chars)` over resampled utterances
- interval: percentile 2.5–97.5
- **speaker-cluster bootstrap 아님** (speaker ID 부재)

### 10.5 비용·환경

- CPU only: Ryzen 5 7600, 6 cores/12 threads, 15.6GiB RAM
- GPU: **미사용**
- VPS: **미사용**
- 비용: **$0**
- test feature extraction: 273.2초 (2,400/2,400)

### 10.6 재현 시 주의

- `d5_reader.py --decode`는 `normalize_nospace`를 적용한다. 학습 라벨과 decode 정규화가 같아야 한다.
- `w1_extract.py`의 0.5초 하한을 그대로 쓰면 test 2,400 중 28건이 빠진다. 반드시 `--min-dur 0.28`을 쓴다.
- `feats_test_v2`는 대용량이라 git에 포함되지 않는다. 위 명령으로 재생성한다.
- B3/B0′은 **`.best.pt`**를 사용했다. B3는 best=final epoch 12, B0′도 best=final epoch 12다.
- B3-nat는 candidate가 아니다. test 후보로 쓰지 않는다.

---

## 11. 답변 형식

다음 형식을 지켜 달라.

```text
## 0. 결론
한 줄: A(recipe-level PASS 인정) / B(caveat부 PASS) / C(exploratory로 강등 또는 reject)

## 1. Q1~Q8
### Q1
① 판정:
② 근거:
③ 필수 조치:
④ 다음 단계 차단 여부:

...

## 2. Must-fix 표
| ID | 지적 | 조치 | 우선순위 | LoRA 차단 여부 |

## 3. 다음 실험 우선순위
1.
2.
3.

## 4. 대외 주장 문장 (수정안)
"..."

## 5. 불확실한 점
- ...
```

- **칭찬·요약보다 결함·대안·중단 기준을 우선**해 달라.
- 수치가 문서와 다르면 **어느 수치가 맞는지** 명시해 달라.
- 문서에 없는 내용을 추정하지 말고, 필요한 경우 “문서에 없음”이라고 적어 달라.
- 이 검토는 **읽기 전용**이다. 파일을 수정하거나 코드를 실행해 저장소를 바꾸지 말라.
- 추가 모델·서브에이전트 호출 없이 **직접** 검토를 완료해 달라.

---

## 12. 검토자에게 마지막으로

이 프로젝트는 “좋은 숫자”를 만드는 것이 목적이 아니다. **어떤 조건에서 어떤 주장이 가능한지**를 정확히 남기는 것이 목적이다. 현재 결과는 **recipe-level gate**를 통과했지만, “short 4시간 데이터만의 효과”라고 말하기에는 confound가 남아 있다. 이 문서가 그 경계를 명확히 하는 데 충분한 정보를 제공했는지도 판단해 달라.

특히 **Q1·Q2·Q5·Q6**의 답이 다음 사용자 결정(LoRA 착수 여부, 20-epoch 여부, 대외 발표 문장)을 좌우한다.
