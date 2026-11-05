# 외부 검토 요청서 v2 — Wave 2B + 2C-short 진행 내역과 구현계획

- 작성일: 2026-11-04
- 검토 기준 커밋: `1db2d0e` (요청서 작성 직전 `origin/main`)
- 직전 검토 기준 커밋: `6b1d720`
- 프로젝트: `mandutt/unigem` (비공개, branch `main`)
- 문서 목적: **프로젝트 이력을 처음 보는 외부 AI가 추가 정보 없이 v2 설계·preflight·구현계획을 판단**하도록 하는 자기완결형 재검토 요청서
- 주의: 이 문서는 **검토 요청**이지 승인 문서가 아니다. 검토 의견은 사용자 승인 전 구현에 반영하지 않는다.

---

## 0. 검토자에게 — 이번 라운드의 질문

직전 라운드에서 3개 모델이 **설계 v1을 그대로 승인하지 않았고**, 공통 Must-fix 7건을 제시했다. 그 후 사용자가 세 가지를 승인했고, 우리는 **preflight를 실제로 완료**했다. 이번 라운드의 핵심 질문은 다음 하나다.

> **수정된 v2와 preflight 결과가 “pilot을 시작해도 되는 상태”인가?**
> 아니라면, pilot 전에 반드시 고쳐야 할 것은 무엇인가?

특히 다음을 우선하라.

1. test/dev split과 test 재사용·선택 편향
2. B0′·reader warm-start·feature parity가 arm 비교를 성립시키는가
3. B3-nat의 정의가 실제로 “도메인/샘플러 효과”를 분리하는가
4. OOV·화자 메타데이터 부재·CTC 적격률이 결론을 오염시키는가
5. 5~7일·VPS/로컬 분업·디스크 계획이 현실적인가
6. 더 싸고 빠른 대안, 또는 중단 기준

칭찬보다 **결함·누락·대안**을 우선해 달라. 불확실하면 “불확실”이라고 명시하라.

---

## 1. 한눈에 보는 현재 상태

### 1.1 프로젝트 목표

EmbeddingGemma 2(EG2)의 **오디오 타워를 재사용**해 F1 언어판정, **F2 STT**, F3 비전 태깅, F4 맞춤법 교정, F5 메모리 요약, F6 STT 후처리를 검증하는 연구 프로젝트다.

F2 제품 경로는 이미 **komixv2/whisper**로 확정됐고(D-057), EG2 기반 F2는 **연구 트랙**이다. 이 연구가 실패해도 제품 경로는 바뀌지 않는다.

### 1.2 이번 대상

Wave 2A-lite에서 **6시간 데이터·동결 타워·작은 CTC reader**로 어디까지 가능한지 측정했고, dev에서는 F-C-concat이 개선됐지만 Kspon eval_other **CER 35.14%**로 도메인/길이 갭이 남았다. 이번 Wave 2B+2C-short는 다음 두 개입을 분리한다.

- **2B**: EG2 오디오 타워 10–11층 **LoRA**
- **2C-short**: Kspon train에서 **짧은 발화 4시간** 추가
- 목표: Kspon in-domain sealed holdout에서 B0′ 대비 개선이 있는지, 그 개선이 **데이터 효과**인지 **adaptation 효과**인지 진단

### 1.3 현재 상태 요약

| 항목 | 상태 |
|---|---|
| Wave 2A-lite | 완료(D-065) |
| CP-D2-lite | 완료 — 길이 분포 불일치가 주축 |
| v1 3-AI 검토 | 완료 — A안 조건부 채택, v1 그대로 승인 반대, Must-fix 7건 |
| 설계 v2 | 작성 완료 — `docs/STT/plans/plan_wave2b_2c_short_v2.md` |
| 사용자 승인 | dev 500/test 2,400, B0′ 재학습, B3-nat 추가, Gate v2 |
| Preflight | **완료** — split·OOV·CTC·디스크·데이터 가용성 |
| short 4h 다운로드·선별 | **미착수** |
| 코드 구현·학습·test 평가 | **미착수** |

---

## 2. 직전 검토 이후 진행 내역

### 2.1 커밋 범위

`6b1d720..1db2d0e`의 주요 커밋:

| 커밋 | 내용 |
|---|---|
| `7d89cb8` | Hoplite 3-AI 검토 원문·종합 기록 |
| `c0d475f` | w2b_2c_short watcher 로그 |
| `5846450` | Hoplite usage를 종합에 추가 |
| `d4cdf8d` | v1 설계·자기완결형 검토요청서 |
| `88eb58f` | v2 채택(B0′, dev 500, B3-nat) |
| `5611910` | v2 split 확정(dev 500/test 2,400) |
| `5170404` | preflight 스크립트·split 후보·리포트 |
| `1bb8df0` | v2 test 크기 표기 정정 |
| `1db2d0e` | preflight OOV를 2A vocab 기준 상한으로 명시 |

### 2.2 직전 3-AI 검토 결과

원문:

- GLM: `docs/STT/hoplite/w2b_2c_short/2026-11-04_hoplite-review_w2b_2c_short_GLM.md`
- Sonnet: `..._SONNET.md`
- Luna: `..._LUNA.md`
- 종합: `docs/STT/reports/W2B_2C_SHORT_3AI_SYNTHESIS.md`

공통 판정:

- **A안(4h short + 4-arm) 조건부 채택**
- **v1 그대로 승인 반대 3/3**
- **B3 삭제 반대 3/3**
- 공통 Must-fix 7건

| # | Must-fix | v2 반영 |
|---:|---|---|
| 1 | 기존 2A checkpoint를 B0로 쓰지 말고 **B0′ 재학습** | 반영 |
| 2 | reader 초기화·feature parity | **2A F-C-concat reader warm-start**, parity unit test 계획 |
| 3 | dev 100이 너무 작음 → **dev 500** | 반영(사용자 승인) |
| 4 | eval_clean 2,900은 독립 test가 아님 → **in-domain sealed holdout** | 표현·정책 반영 |
| 5 | short 4h는 길이+도메인 결합 → **B3-nat** | 사용자 승인, 정의는 Q3에서 재검토 |
| 6 | 4h 단위·OOV·화자·CTC 적격률 사전등록 | preflight로 OOV/CTC/화자 부재 확인 |
| 7 | 7~10일·25GB 미실측 → pilot 실측 | 5~7일 추정, preflight로 디스크 확인 |

모델별 차이:

- **Sonnet**: dev 500/test 2,400, B3 유지, B3-nat 추가 제안
- **Luna**: dev 500/test 2,400, 절대 CER pp 주지표, 화자 cluster bootstrap, seed 2개
- **GLM**: B3 유지, B0′ 재학습, reader warm-start, `max(B2,B3)` vs B0′, pilot INCONCLUSIVE 밴드
- 공통: **채택 판정과 귀속 진단을 분리**하라. B2>B1·B2>B3를 Go의 단일 조건으로 강제하면 “데이터만으로 충분” 같은 유효 결과를 실패 처리한다.

### 2.3 사용자 결정(2026-11-04)

사용자는 다음을 명시적으로 승인했다.

1. **Kspon eval_clean에서 dev 500 + test 2,400**
   - 기존 D-β dev 100을 dev에 포함
   - test 2,400은 기존 100을 포함하지 않음
2. **B0′ 재학습**
3. **B3-nat 추가**
4. **Gate v2**: 절대 CER pp/CI 주지표, `max(B2,B3)` vs B0′ 채택, B2−B1/B2−B3는 귀속 진단

이 결정은 `docs/decisions.md` D-066에 기록됐다.

---

## 3. Wave 2A-lite·CP-D2-lite 실측(변경 없음)

### 3.1 2A-lite dev — 4-arm

- dev: FLEURS ko **192클립**(≤16초), 참조 **7,861자**
- train: **6.0008h / 2,384클립**
- 정규화: `normalize_nospace`(공백·구두점 제거)

| Arm | 입력 | dev CER | errors/ref |
|---|---|---:|---:|
| F-A′ | `aud_out_proj` 1536 | 0.222364 | 1,748 / 7,861 |
| F-B | `aud_h_l11` 1024 | 0.219311 | 1,724 / 7,861 |
| F-C-softmax | 4층 softmax mix 1024 | 0.222109 | 1,746 / 7,861 |
| **F-C-concat** | 4층 concat 4096 | **0.209134** | **1,644 / 7,861** |
| fbank baseline | log-mel 80 + CTC | 0.9812 | 실패(blank plateau) |

- F-C-concat − F-A′ = **+1.323%p(상대 5.95%)**, 문장 paired bootstrap 95% CI **[+0.631, +2.028]%p**
- seed43 F-C-concat = **0.208116**(seed43 F-A′ 0.2233 대비 **6.8%**)
- seed42를 사전등록 주 seed로 동결, seed43은 재현 증거 전용

### 3.2 2A-lite 봉인 test

동결 checkpoint: `data/wave2a_lite/frozen/w2a_fc_concat_s42.best.pt`
SHA-256: `258f6ddf84b3f41afc0e88f832946229b3a1319d28cec11cd4a0da40951cb23d`

| 세트 | 평가 수 | CER | blank | errors/ref |
|---|---:|---:|---:|---:|
| **Kspon eval_other** | **2,962 / 3,000** | **0.35143** | 0 | 23,508 / 66,893 |
| **FLEURS ko test** | **318 / 382** | **0.23509** | 0 | 3,126 / 13,297 |

- 16초 초과 등으로 manifest 행 수와 평가 수가 다르다.
- **Kspon eval_other와 FLEURS test는 이미 2A-lite gate에 1회 사용됐다.**
- 따라서 2B에서는 **FLEURS test를 재사용하지 않는다.**

### 3.3 CP-D2-lite — 35.14%의 분해

추가 test 평가 없이 기존 decode/manifest만 분석했다.

| 항목 | 결과 |
|---|---:|
| Kspon CER | 0.35143 |
| 상위 1% 발화의 오류 비중 | **4.2%** |
| 상위 5% 발화의 오류 비중 | **15.5%** |
| blank | 0 |
| noisy CER / clean CER | 34.7% / 35.4% |
| duration–CER Pearson | **−0.265** |

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

- **train ≤4초 4.1% vs Kspon eval_other ≤4초 57.2%**
- 오류는 소수 outlier가 아니라 전반적 음향 혼동이다.
- 잡음 마커가 주원인이 아니다(noisy 34.7% < clean 35.4%).
- Kspon ≥12초 28.6% vs FLEURS ≥12초 23.1% → 길이를 맞춰도 **약 5.5%p 도메인 갭**이 남는다.

---

## 4. v2 설계

### 4.1 Arms

| Arm | 타워 | 데이터 | sampler | 목적 |
|---|---|---|---|---|
| **B0′** | 동결 | 6h | natural | 새 기준선(재학습) |
| **B1** | 10–11층 LoRA | 6h | natural | adaptation |
| **B2** | 10–11층 LoRA | 6h + short 4h | balanced | adaptation + short |
| **B3** | 동결 | 6h + short 4h | balanced | data-only (balanced) |
| **B3-nat** | 동결 | 6h + short 4h | natural | data-only domain control |

- **B0′**: 2A F-C-concat의 **reader weight warm-start**, tower frozen. B1/B2/B3/B3-nat도 같은 reader 초기화를 쓴다.
- LoRA: 10–11층, rank 8, alpha 16, attention(q/k/v/post) + FFN 8모듈.
- B=0 초기화; **epoch-0 회귀 체크**: B1 0-step == B0′.
- B3/B3-nat: short feature를 `w1_extract --arms fc`로 추출하고 reader-only 학습.
- Feature parity: B1/B2 on-the-fly mel vs B3/B3-nat cached feature를 같은 샘플에서 수치 비교.

### 4.2 데이터

- 기존 6.0008h + short 4h = **10h train**
- short 4h 목표:

| duration | 시간 비중 | 목표 시간 |
|---|---:|---:|
| 0–2초 | 25% | 1.0h |
| 2–4초 | 35% | 1.4h |
| 4–6초 | 20% | 0.8h |
| 6–8초 | 20% | 0.8h |

- **B0′/B1**: natural sampler
- **B2/B3**: LengthBalancedSampler, effective ≤4초 40%, 4–8초 30%, 8–16초 30%
- **B3-nat**: 10h natural sampler
- B2−B1은 “short data + sampler” 효과로 표기
- 클립당 예상 노출 횟수·replacement 여부·epoch 정의를 기록

### 4.3 dev/test

| 세트 | 크기 | 상태 |
|---|---:|---|
| dev | **500** | 기존 D-β 100 + 신규 400 |
| test | **2,400** | 봉인, 기존 100 제외 |
| spare | **90** | 평가 미사용 |
| FLEURS dev 192 | 보조 | 2A에서 arm 선택에 사용됨 |

- eval_clean 3,000 중 16초 초과 **10건 제외** → 적격 **2,990**
- dev 500 + test 2,400 + spare 90 = 2,990
- **dev∩test = 0**, **test∩기존 D-β 100 = 0**
- test 표현: **“Kspon in-domain sealed holdout”**
- “독립 test” 또는 “새 화자 일반화”라고 부르지 않는다.
- test는 checkpoint freeze 후 **1회만** 평가한다.

### 4.4 Preflight 실측(완료)

입력: `data/raw/kspon_eval/10.한국어음성/KsponSpeech_eval.zip`의 metadata + `extracted/eval_clean.trn`. **오디오 추출·다운로드·학습 없음.**

| 항목 | 결과 |
|---|---:|
| eval_clean PCM / TRN | 3,000 / 3,000 |
| 16초 초과 제외 | 10 |
| 평가 적격 | **2,990** |
| dev / test / spare | **500 / 2,400 / 90** |
| dev∩test | **0** |
| test∩기존 100 | **0** |
| duration min / mean / max | 0.286 / 3.126 / 15.738초 |
| CTC `chars > frames` | **0** |
| CTC `chars+repeats > frames` | **0** |

duration 분포:

| duration | all | dev 500 | test 2,400 | spare 90 |
|---|---:|---:|---:|---:|
| 0–2초 | 1,440 | 246 | 1,151 | 43 |
| 2–4초 | 783 | 126 | 633 | 24 |
| 4–8초 | 537 | 90 | 431 | 16 |
| 8–12초 | 187 | 32 | 149 | 6 |
| 12–16초 | 43 | 6 | 36 | 1 |

OOV(2A FLEURS vocab 1,101자 기준 **상한**):

| 세트 | OOV 행 | 비율 | OOV 문자 |
|---|---:|---:|---:|
| 전체 | 226/2,990 | 7.56% | 261 |
| dev | 38/500 | 7.60% | 43 |
| test | 185/2,400 | 7.71% | 214 |
| spare | 3/90 | 3.33% | 4 |

- test OOV 문자 214자는 test 참조 40,222자의 **0.53%**다.
- **2B vocab은 Kspon train 6h+short에서 새로 build**하고, short 선별 후 최종 OOV를 다시 측정한다.
- OOV 정책은 아직 사용자 승인 전이다.

화자·디스크:

- eval_clean.trn과 zip 파일명에 **화자 ID가 없다.**
- dev/test는 **duration 층화**로만 나눴다.
- speaker-cluster bootstrap은 불가능하며, **utterance bootstrap**으로 대체한다.
- Kspon train shard는 로컬에 없다: filekey **50211~50215**, 각 **14~15GB**.
- 현재 C: 여유 약 **18GB**.
- 따라서 **zip streaming + 선택 파일만 저장** 또는 **VPS eg2-2에서 선별**이 필요하다.

split 후보:

- `data/wave2b/preflight/split_candidate.json`
- sha256 `25eb37f6314072aa9a113b8d6f822ebedb8d6b3a638c42b52de8b7954d680deb`
- seed 42, dev/test/spare ID 목록 포함
- 아직 audio를 추출하지 않았고, test는 평가 전이다.

### 4.5 Gate v2

**Pilot**

- `max(B2,B3)` vs B0′에서 **절대 CER 1.0%p 이상 개선**, 또는 상대 5% 이상 + CI 방향 일치
- n=500에서도 불확실하면 **INCONCLUSIVE**로 두고 full 확장
- ≤4초 bin은 pilot에서 방향 일치만 보고

**Full/채택**

- **`max(B2, B3)` vs B0′**: 절대 CER pp 차이, paired bootstrap 95% CI 하한 > 0
- **귀속**: B2−B1(데이터+sampler), B2−B3(adaptation), B3−B0′(data-only), B3−B3-nat, B3-nat−B0′를 모두 보고
- **상대 10%는 보조**; 절대 pp와 CI를 주지표
- **FLEURS dev no-regression**: B0′ 대비 +1.0%p 이상 악화되지 않을 것
- seed 42(+가능하면 43); test는 primary seed42만
- test 2,400 1회, 사후 threshold 변경 금지
- No-Go 시 CP-D2 원인 진단. B2>B1/B3를 Go의 단일 조건으로 쓰지 않는다.

**미해결**: Full 채택의 **절대 pp 최소값**이 아직 명시되지 않았다. 현재 문서는 “CI 하한 > 0”만 있고, pilot은 1.0%p다. Q5에서 이 값을 정해야 한다.

---

## 5. 구현 계획(아직 실행 전)

### 5.1 Phase 0 — Preflight(완료)

- eval_clean split, OOV, CTC frame, 디스크, shard 가용성 확인
- 산출물: `docs/STT/reports/W2B_preflight.md`, `reports/provenance/W2B/preflight.json`, `data/wave2b/preflight/split_candidate.json`

### 5.2 Phase 1 — short 4h + B3-nat 4h

- Kspon train shard(50215 우선)을 **VPS eg2-2에서 streaming**
- short 4h: 0–2/2–4/4–6/6–8초 목표
- B3-nat: 별도 4h natural 후보
- 전사 정리: 기존 eval_other와 동일 규칙, `ref_raw` 보존
- 제외: 빈 전사, 1자 이하, 0.5초 미만, CTC frame 부적격
- 산출물: `data/wave2b/short_4h.jsonl`, `b3nat_4h.jsonl`, `summary.json`
- 예상: **3~5시간**(다운로드 0.5~3h + 선별/QC 1~2h)

### 5.3 Phase 2 — vocab·dev/test 특징·코드

- 2B vocab: Kspon train 6h+short에서 build, eval 누출 금지
- dev 500/test 2,400 특징 추출
- `train/d5_reader.py` 수정:
  - LoRA(10–11층, rank 8, alpha 16)
  - LengthBalancedSampler
  - reader warm-start
  - `--resume`(model/LoRA/reader/optimizer/scheduler/epoch/RNG)
  - feature parity unit test
  - OOV 정책
- 예상: **1.5~2.5일**(critical path)

### 5.4 Phase 3 — Pilot

- B0′ → B3 → B3-nat → B2 → B1(조건부)
- 3 epoch, dev 500 early stop
- sec/step, peak RSS, feature extraction, disk peak 기록
- 예상: **0.5~1일**

### 5.5 Phase 4 — Full

- 5-arm, 12 epoch
- B0′/B1/B2는 **로컬**(CPU steal 위험)
- B3/B3-nat reader-only는 VPS eg2-3/4에 분산 가능
- pilot 실측 후 full-run 별도 승인
- 예상: **1.5~2.5일**(VPS 병렬), 로컬-only면 **+1~2일**

### 5.6 Phase 5 — Test·보고

- checkpoint freeze → test 2,400 1회
- B0′ paired 비교, OOV full/in-vocab secondary
- 예상: **0.5~1일**

### 5.7 전체 예상

| 구간 | 예상 |
|---|---:|
| short 4h 확보 | 3~5시간 |
| 구현 | 1.5~2.5일 |
| pilot | 0.5~1일 |
| full | 1.5~2.5일 |
| test·보고 | 0.5~1일 |
| **합계** | **5~7일** |

- 빠르면 4일, VPS steal·구현 지연 시 8일.
- **구현이 critical path**이며 학습 시간이 아니다.
- Pilot INCONCLUSIVE 시 +1~2일.
- 이 추정은 아직 실측이 아니라 2A epoch 322~356초/20 epoch, feature extraction 2,963클립 467.7초를 근거로 한 추정이다.

---

## 6. 검토 질문

### Q1. dev/test split과 test 재사용

- eval_clean 3,000에서 **dev 500(기존 D-β 100 포함) / test 2,400 / spare 90**이 타당한가?
- 기존 dev 100을 dev에 포함하는 것이 test 편향을 만드는가?
- eval_clean의 60명 화자·eval_other와 같은 코퍼스라는 점을 “in-domain sealed holdout”으로 한정한 것이 충분한가?
- 화자 ID가 없어 duration 층화만 한 것이 결론을 얼마나 약화시키는가?
- 더 깨끗한 P0 holdout을 확보해야 하는가? 비용 대비 가치가 있는가?

### Q2. B0′·reader warm-start·feature parity

- B0′를 2A F-C-concat reader warm-start로 재학습하는 것이 B1/B2/B3 비교를 공정하게 만드는가?
- B1 0-step == B0′ 회귀 체크만으로 충분한가, 아니면 별도 seed/optimizer parity가 필요한가?
- B1/B2 on-the-fly mel vs B3/B3-nat cached fc의 **수치 parity 허용오차**를 어떻게 정해야 하는가?
- B0′가 2A 0.20913과 크게 달라질 경우 어떤 판정을 해야 하는가?

### Q3. B3-nat의 정의 — 가장 불확실한 지점

현재 v2는 B3-nat을 “Kspon 4h natural, frozen tower, reader-only”로 정의한다. 그러나 두 해석이 가능하다.

- **A. 같은 short 4h 클립 + natural sampler**: sampler 효과를 분리하지만 “natural 길이 분포”는 아니다.
- **B. 별도 4h natural 클립 + natural sampler**: 도메인/길이 분포 control이지만 **클립 구성과 sampler가 동시에 바뀐다.**

현재 v2는 B3−B3-nat을 “sampler 효과”로 적고 있지만, B를 택하면 **data composition + sampler confound**가 된다. 어떤 정의를 택해야 하며, 그에 맞춰 B3−B3-nat의 해석을 어떻게 제한해야 하는가?

### Q4. OOV·vocab

- 2A vocab 기준 OOV 7.56%(test 7.71%, 문자 0.53%)를 **상한**으로 보고, 2B vocab을 Kspon train 6h+short에서 새로 build하는 것이 타당한가?
- full test 2,400 주평가 + in-vocab subset 2,215 보조, OOV 문자는 오류 처리하는 정책이 타당한가?
- OOV 클립을 short 4h에서 제외하는 것이 데이터 선택 편향을 만들지 않는가?
- test OOV를 줄이기 위해 vocab을 test에서 확장하는 것은 leakage로 금지해야 하는가?

### Q5. Gate·표본·주지표

- Pilot 절대 1.0%p, full “CI 하한 > 0”만으로 충분한가?
- Full 채택의 **절대 pp 최소값**을 얼마로 정해야 하는가? (예: 1.0%p)
- `max(B2,B3)` vs B0′ 채택과 B2−B1/B2−B3 귀속 분리가 타당한가?
- dev 500으로 early stop과 final gate를 같은 세트에서 반복하는 편향을 어떻게 줄여야 하는가?
- seed 42 하나로 full을 판정하는 것이 충분한가? seed 43을 어디까지 요구해야 하는가?
- FLEURS dev no-regression +1.0%p 기준이 적절한가?

### Q6. 데이터·디스크·VPS

- 15GB shard를 **VPS eg2-2에서 streaming**하고 short 4h만 회수하는 계획이 현실적인가?
- 로컬 C: 18GB에서 10h feature(특히 F-C 4096d)를 저장·학습할 수 있는가? 어떤 파일을 지워야 하는가?
- B0′/B1/B2는 로컬, B3/B3-nat는 VPS로 나누는 것이 steal 위험과 재현성 측면에서 최선인가?
- VPS eg2-2의 20GB 디스크·네트워크로 15GB 다운로드가 가능한가? 더 나은 대안은?
- Kspon train 화자 메타데이터가 없다면 “화자당 10% 상한”을 세션/파일 프록시로 대체하는 것이 타당한가?

### Q7. 일정·중단 기준

- 5~7일 추정이 현실적인가? 가장 먼저 터질 병목은 무엇인가?
- 구현 1.5~2.5일, full 1.5~2.5일의 가정이 타당한가?
- pilot이 INCONCLUSIVE일 때 full로 갈 기준과 중단 기준을 어떻게 사전등록해야 하는가?
- VPS steal이 재발하면 어떤 arm을 먼저 local로 옮겨야 하는가?

### Q8. 종합 권고

다음 중 어느 쪽인가?

- **A. v2 그대로 pilot 시작**
- **B. 아래 Must-fix를 반영한 뒤 pilot 시작**
- **C. pilot 전에 설계를 더 바꿔야 함**
- **D. 새 P0 holdout 없이는 중단**
- **E. 다른 대안**

권장안과 이유, **반드시 고쳐야 할 1~3개**, 그리고 **pilot 전에 하지 말아야 할 것**을 적어 달라.

---

## 7. 답변 형식

아래 형식으로 답해 달라.

1. **권장 결론:** A/B/C/D/E 중 하나
2. **Q1~Q8:** 각 1문단 — ①판정 ②근거 ③권장 다음 단계
3. **Must-fix:** pilot 전 반드시 고칠 것 1~3개
4. **Optional:** 있으면 좋은 것
5. **잘못된 전제:** 이 문서에서 사실과 다르거나 검증이 필요한 것
6. **신뢰도:** high/medium/low

---

## 8. 재현 정보

- 저장소: `mandutt/unigem` (비공개), branch `main`
- 검토 기준 커밋: `1db2d0e`
- 직전 검토 기준: `6b1d720`
- v2 설계: `docs/STT/plans/plan_wave2b_2c_short_v2.md`
- v1 설계(이력): `docs/STT/plans/plan_wave2b_2c_short.md`
- 직전 3-AI 종합: `docs/STT/reports/W2B_2C_SHORT_3AI_SYNTHESIS.md`
- 직전 3-AI 원문: `docs/STT/hoplite/w2b_2c_short/2026-11-04_hoplite-review_w2b_2c_short_{GLM,SONNET,LUNA}.md`
- 2A-lite 결과: `docs/STT/reports/W2A_lite_results.md`
- CP-D2-lite: `docs/STT/reports/W2A_lite_cp_d2_lite.md`, `docs/STT/reports/W2A_lite_cp_d2_lite.json`
- Preflight: `docs/STT/reports/W2B_preflight.md`, `reports/provenance/W2B/preflight.json`, `runner/w2b_preflight.py`
- split 후보: `data/wave2b/preflight/split_candidate.json`
- 동결 checkpoint: `data/wave2a_lite/frozen/w2a_fc_concat_s42.best.pt`
  - sha256 `258f6ddf84b3f41afc0e88f832946229b3a1319d28cec11cd4a0da40951cb23d`
- 학습 데이터: `data/wave1/manifest.jsonl`(2,384클립/6.0008h)
- 기존 test: `data/wave2a_lite/kspon_eval_other.jsonl`(3,000; 2A에서 사용 완료)
- 새 test 예정: `data/wave2b/test/kspon_eval_clean_2400.jsonl` (미생성)
- 정규화: `eval/normalize.py::normalize_nospace`
- `w1_extract.py`는 16초 초과/0.5초 미만을 제외하므로 manifest 행 수와 평가 수가 다르다.

### 8.1 AM-6 이행 표

| 요구 | 이행 |
|---|---|
| arm 간 동일 조건 | v2에서 reader init·vocab·seed 통일 계획 |
| dev/test 분리 | preflight에서 ID 교집합 0 확인 |
| seed 반복 | 2A seed42/43, 2B seed42 + 43(가능 시) |
| positive control | 2A `pc_fa20n` PASS(1h overfit 0.1161) |
| per-domain/error/blank/vocab/fbank | 2A 보고 완료, 2B gate에 포함 |
| test 1회 | 2B는 freeze 후 1회 |
| WER/공백 포함 CER | 2A 예측 공백 없음, 2B 필요 시 보고 |
| 13-state/wordpiece/40h/LoRA | LoRA·short는 2B/2C, wordpiece/40h는 후속 |

---

## 9. 검토자가 특히 의심해야 할 지점

1. **test 2,400이 정말 “sealed”인가** — split 후보는 만들었지만 audio를 아직 추출하지 않았다. test 평가 전에 누출이 없는지 확인해야 한다.
2. **dev 500의 100개 재사용** — D-β에서 이미 본 발화다. dev 선택 편향이 남는다.
3. **화자 ID 부재** — “화자 층화”가 아니라 “duration 층화”다. speaker-cluster bootstrap을 주장하면 안 된다.
4. **B3-nat confound** — 별도 natural 4h를 쓰면 domain control이지 순수 sampler control이 아니다.
5. **OOV 7.56%는 2A vocab 기준 상한** — 2B vocab을 train에서 새로 build하기 전에는 최종 OOV가 아니다.
6. **Full gate에 절대 pp 최소값이 없다** — pilot 1.0%p만 있고 full은 CI 하한 > 0뿐이다.
7. **10h F-C 4096d feature의 디스크** — C: 18GB에서 6h feature 11GB + 4h short/nat feature가 겹치면 빠듯하다.
8. **5~7일은 추정** — 구현·VPS steal·pilot INCONCLUSIVE에 따라 늘어난다.
