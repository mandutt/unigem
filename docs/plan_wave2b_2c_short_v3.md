# Wave 2B + 2C-short 설계 v3 — 검토 결정 통합

- 작성: 2026-11-04
- 상태: **v3 정본. v2(`docs/plan_wave2b_2c_short_v2.md`)의 해당 절을 대체한다.**
- 근거:
  - 3-AI v2 검토: `reports/W2B_2C_SHORT_V2_3AI_SYNTHESIS.md` — **3/3 B**
  - 사용자 결정(2026-11-04): 아래 §0
  - Preflight addendum: `reports/W2B_preflight_addendum.md`
- 아직 실행하지 않음: short 4h 다운로드·선별, 코드 구현, 학습, test 평가.

---

## 0. 사용자 확정 결정

| # | 항목 | 결정 |
|---:|---|---|
| 1 | vocab | **V1 — 2A 1,101자 vocab 유지** |
| 2 | B3-nat | **A — B3와 같은 10h clip set, natural sampler** |
| 3 | Full gate | **Δ ≥ 1.0%p + paired utterance bootstrap 95% CI 하한 > 0** |
| 4 | test split | **ID 블록 감사 후 결정** — 화자/세션 대응이 확인되면 블록 split, 아니면 현 split 유지 |
| 5 | 0.5초 미만 test 28건 | **평가 추출 하한 0.28초**, 실제 CTC 실패는 오류 처리 |
| 6 | pilot 범위 | **reader-only B0′/B3/B3-nat 먼저**, LoRA B1/B2는 조건부 |

추가 원칙:

- **B2/B3 primary는 dev 500에서 선택해 freeze**한다. test에서 `max(B2,B3)`를 고르지 않는다.
- test 2,400은 checkpoint freeze 후 **1회만** 평가한다.
- FLEURS test는 재사용하지 않는다.
- F2 제품 경로는 **komixv2/whisper** 그대로다. 이 실험은 연구 트랙이다.

---

## 1. 데이터

### 1.1 기존 6h

- `data/wave1/manifest.jsonl`: **2,384클립 / 6.0008h**
- 구성: **Zeroth 1,534 + Kconf 850**
- **Kspon은 0** — short 4h가 최초의 Kspon 도메인 데이터다.
- 기존 특징: `data/wave1/feats` 11GB(그중 `fc.npz` 3.9GB)

### 1.2 2C-short 4h

| duration | 시간 비중 | 목표 시간 |
|---|---:|---:|
| 0–2초 | 25% | 1.0h |
| 2–4초 | 35% | 1.4h |
| 4–6초 | 20% | 0.8h |
| 6–8초 | 20% | 0.8h |

- 원천: Kspon train(AI Hub datasetkey 123, filekey 50211~50215)
- 전사 정리: eval_other와 동일 규칙, `ref_raw` 보존
- 제외: 빈 전사, 1자 이하, 0.5초 미만, CTC frame 부적격
- 선별 후 **오디오 시간·발화 수·문자 수·OOV율·CTC 적격률**을 `summary.json`에 기록
- `data/wave2b/short_4h.jsonl`로 고정

### 1.3 B3-nat-A

**B3와 동일한 10h clip ID 집합**을 쓴다.

- B3: 같은 10h에 **LengthBalancedSampler**
- B3-nat: 같은 10h에 **natural sampler**
- 둘 다 frozen tower, reader-only, 동일 epoch/optimizer step/노출량
- 이름: **“fixed short-enriched pool, natural sampler”**
- 해석:
  - `B3 − B3-nat` = **순수 sampler 효과**
  - `B3-nat − B0′` = short 4h를 natural sampling으로 추가한 **데이터 효과**
  - Kspon **natural length distribution**을 대표하는 실험은 아니다. 그 질문은 후속 B3-natB로 둔다.

별도 `b3nat_4h.jsonl`은 **만들지 않는다.**

### 1.4 dev/test

| 세트 | 크기 | 상태 |
|---|---:|---|
| dev | **500** | 기존 D-β 100 + 신규 400, duration 층화 |
| test | **2,400** | 후보, 봉인 전 |
| spare | **90** | 평가 미사용 |

- eval_clean 3,000 − 16초 초과 10 = **2,990**
- 500 + 2,400 + 90 = 2,990
- dev∩test = 0, test∩기존 D-β 100 = 0
- **test는 “Kspon in-domain sealed holdout”** — 절차적 holdout이며 화자 독립 test가 아니다.

### 1.5 split 결정

현재 후보는 duration 층화다. v3는 다음 순서로 확정한다.

1. eval_clean ID의 **연속 블록**이 화자/세션과 대응하는지 감사
   - AI Hub 메타데이터, 원논문, ID 범위·파일명 패턴 확인
2. 대응이 확인되면 **블록 단위 500/2,400/90** 재생성
   - 블록 내 발화는 통째로 dev 또는 test에만 배정
   - 길이 분포는 블록 층화로 맞춘다
3. 대응이 확인되지 않으면 **현재 duration 층화 유지**
   - “화자 독립” 주장 금지
   - 한계를 보고서에 명시

**audio 추출·test 평가 전에 결정한다.**

### 1.6 test 0.5초 미만 28건

- dev 500 중 2건, **test 2,400 중 28건**, spare 0건
- `w1_extract.py`의 0.5초 하한을 그대로 쓰면 test는 **2,372**가 된다.
- v3 정책:
  - **평가 추출만 최소 0.28초**로 낮춘다.
  - 학습 데이터는 0.5초 하한을 유지한다.
  - feature 생성 후 `target_len + repeats <= output_frames`를 **실제 frame**으로 재검사한다.
  - CTC 불가 클립은 **오류로 계산**하고 별도 보고한다.
  - 최종 보고서에 **full 2,400 기준 CER**과 evaluable 수를 병기한다.

---

## 2. Vocab·OOV

### 2.1 V1 — 2A 1,101자 유지

- 2A F-C-concat reader의 출력층을 그대로 warm-start한다.
- short 4h에서 1,101자 vocab 밖 문자가 있는 클립은 **제외**한다.
- 제외율·OOV 문자 종류·영향을 기록한다.
- test 평가:
  - **full 2,400 주평가**
  - **in-vocab subset 2,215 보조**
  - OOV 문자는 오류로 계산
- test 문자로 vocab을 확장하지 않는다(leakage).

### 2.2 V2 전환 조건

short 4h의 **클립 OOV 제외율이 5%를 초과**하면 V1은 2C-short의 목적을 훼손한다.

이 경우:

- **즉시 학습을 시작하지 않는다.**
- 2B vocab을 `chars(6h + short 4h)`로 재구축하는 **V2 안을 별도 승인**받는다.
- V2에서는 2A 행 복사 + 신규 행 초기화, blank index, 모든 arm 동일 head를 사전등록한다.

---

## 3. Arms

| Arm | 타워 | 데이터 | sampler | 목적 |
|---|---|---|---|---|
| **B0′** | 동결 | 6h | natural | 새 기준선 |
| **B1** | 10–11층 LoRA | 6h | natural | adaptation(조건부) |
| **B2** | 10–11층 LoRA | 6h + short 4h | balanced | adaptation + short(조건부) |
| **B3** | 동결 | 6h + short 4h | balanced | data-only |
| **B3-nat** | 동결 | **same 10h clip set** | natural | sampler control |

- B0′: 2A F-C-concat **reader warm-start**, tower frozen.
- 모든 arm: 동일 vocab, 동일 reader 초기화, 동일 blank index.
- B1/B2 LoRA: 10–11층, rank 8, alpha 16, attention(q/k/v/post) + FFN 8모듈.
- B=0 초기화.
- **B1 0-step == B0′**는 “학습된 B0′”가 아니라 **공통 초기화 상태의 고정 배치 logits/CER 일치**로 정의한다.
- B0′도 B3와 같은 **cached feature 경로**를 쓴다.

---

## 4. 학습·parity

| 항목 | 값 |
|---|---:|
| batch size | 2 (16s), short-only 4 |
| grad accumulation | 4 |
| epochs | pilot 3 / full 12 |
| early stop | patience 4 on dev 500 |
| LoRA LR | 1e-4 |
| reader LR | 1e-3 |
| scheduler | cosine, warmup 10% |
| grad clip | 5.0 |
| seed | 42, 경계 시 43 |
| threads | 6 |
| AMP | 없음(CPU) |

- 0–9층 `no_grad`; l06/l08 tap detach; gradient는 10–11층 LoRA와 reader만.
- `--resume`: model/LoRA/reader/optimizer/scheduler/epoch/best/RNG.
- **parity**:
  - 동일 frozen tower·동일 샘플·동일 전처리에서 online vs cached feature/logit 비교
  - dtype별 허용오차 사전등록
  - B0′↔B1 경로도 대상
  - LoRA B=0 별도 회귀
- **중단 규칙**: B0′가 2A 0.20913 대비 seed 잡음(약 0.1%p) 이상 벗어나면 pilot 중단·원인 조사.

---

## 5. Gate

### 5.1 Pilot — reader-only 먼저

순서: **B0′ → B3 → B3-nat**

- 3 epoch, dev 500
- `Δ = CER(B0′) − CER(candidate)`
- **Pilot Go**: Δ ≥ **1.0%p** + CI 방향 일치
- 미달/불확실: **INCONCLUSIVE**
- INCONCLUSIVE는 자동 full이 아니다. 아래를 모두 통과할 때만 full 고려:
  - test/dev 누출 없음
  - vocab·head 계약 일치
  - online/cached parity 통과
  - 실제 CTC 적격률 통과
  - 디스크·시간 상한 이내
- **B3−B0′가 음의 방향이고 CI가 0의 음측을 배제하면** LoRA 투자 전에 중단·축소한다.

### 5.2 LoRA 조건부

reader-only pilot에서 데이터 신호가 있을 때만 B1/B2를 구현한다.

- 일정 압박 시 B1은 **귀속 진단용**이므로 먼저 생략 가능
- B2는 채택 후보이므로 유지

### 5.3 Full

- **primary 선택**: dev 500에서 B2/B3 중 하나를 선택해 freeze
  - 차이가 0.3%p 이내면 **B3(reader-only, 단순)** 우선
  - test에서 `max(B2,B3)` 선택 금지
- **채택**: `Δ ≥ 1.0%p` **AND** paired utterance bootstrap 95% CI 하한 > 0
- **보조**: 상대 10%, bin별 CER, FLEURS dev no-regression(+1.0%p 이내)
- **귀속**: B2−B1(데이터+sampler), B2−B3(adaptation), B3−B0′(data-only), B3−B3-nat(sampler), B3-nat−B0′(short data, natural sampler)
- test 2,400 1회; 사후 threshold 변경 금지
- seed 43은 경계 결과에서 winner+B0′만 확장

---

## 6. Preflight·다음 단계

| 단계 | 작업 | 상태 |
|---:|---|---|
| 0 | v2 3-AI 검토 | 완료(3/3 B) |
| 1 | Preflight addendum: 0.5초/overlap/disk/sha | **이 문서와 함께 기록** |
| 2 | ID 블록 감사 → split 확정 | 대기 |
| 3 | short 4h 선별 + OOV율 측정 | 대기 |
| 4 | V1/V2 최종 확인 | 대기 |
| 5 | vocab·dev/test feature | 대기 |
| 6 | 코드(LoRA/sampler/warm-start/resume/parity) | 대기 |
| 7 | reader-only pilot B0′/B3/B3-nat | 대기 |
| 8 | LoRA B1/B2 조건부 | 대기 |
| 9 | full 12 epoch | 대기 |
| 10 | test 2,400 1회·보고 | 대기 |

---

## 7. 일정(잠정)

| 구간 | 예상 |
|---|---:|
| short 4h 확보 | 3~5시간 |
| 구현 | 1.5~2.5일 |
| reader-only pilot | 0.5~1일 |
| LoRA/full | 2~4일 |
| test·보고 | 0.5~1일 |
| **합계** | **7~10일 + 2일 버퍼** |

- 이전 5~7일은 **LoRA sec/step 미실측** 상태의 낙관적 추정이었다.
- pilot 첫 시간에 B1 sec/step·RSS를 실측한 뒤 full 일정을 재산정한다.
- full은 별도 승인 후 시작한다.

---

## 8. DoD

- [ ] ID 블록 감사 결과 기록, split 확정
- [ ] test 2,400의 0.5초 미만 28건 처리, 실제 CTC 재검사
- [ ] short 4h OOV율·제외율·문자 수·CTC 적격률 기록
- [ ] V1 유지 또는 V2 전환 승인
- [ ] B3/B3-nat same clip set, 같은 step/노출량
- [ ] B0′/B1 초기화·parity 정의
- [ ] reader-only pilot B0′/B3/B3-nat
- [ ] dev primary 선택 freeze
- [ ] test 2,400 1회, in-domain holdout 표기
- [ ] FLEURS test 미사용
- [ ] full gate Δ≥1.0%p + CI 하한>0

---

## 9. 남은 승인·확인

- ID 블록 감사 결과에 따른 split 변경
- short OOV 제외율 5% 초과 시 V2 전환
- pilot 결과 후 LoRA/full 착수
- full 일정·자원 상한

---

## 10. 재현·참조

- v2 설계: `docs/plan_wave2b_2c_short_v2.md`
- v1 설계: `docs/plan_wave2b_2c_short.md`
- 3-AI 종합: `reports/W2B_2C_SHORT_V2_3AI_SYNTHESIS.md`
- Preflight: `reports/W2B_preflight.md`
- Preflight addendum: `reports/W2B_preflight_addendum.md`
- Split: `data/wave2b/preflight/split_candidate.json`
- Git blob sha256: `6805a8de071067502e421c0da96257eaea6ee7b5f2ec6607f51360b885b515f0`
- 2A frozen: `data/wave2a_lite/frozen/w2a_fc_concat_s42.best.pt`
  - sha256 `258f6ddf84b3f41afc0e88f832946229b3a1319d28cec11cd4a0da40951cb23d`
- 정규화: `eval/normalize.py::normalize_nospace`
