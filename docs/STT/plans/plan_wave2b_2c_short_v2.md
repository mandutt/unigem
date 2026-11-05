# Wave 2B + 2C-short 설계 v2 — 3-AI 검토 반영

- 작성: 2026-11-04
- 상태: **v3가 현행 정본이다(`docs/STT/plans/plan_wave2b_2c_short_v3.md`). 이 문서는 v2 검토·preflight 이력으로 보존한다. Preflight 완료(2026-11-04), short 다운로드·학습·test는 미착수.**
- 근거: `docs/STT/reports/W2B_2C_SHORT_3AI_SYNTHESIS.md`
- 사용자 승인(2026-11-04):
  1. **eval_clean에서 dev 500 + test 2,400** (2026-11-04 사용자 최종 결정)
  2. **B0′ 재학습** 승인
  3. **B3-nat** 추가 승인
- 아직 실행하지 않음: 데이터 다운로드·코드·학습·test 평가.

---

## 1. v1에서 바뀐 핵심

| 항목 | v1 | v2 |
|---|---|---|
| B0 | 기존 2A checkpoint | **B0′를 동일 코드·sampler·epoch·seed로 재학습** |
| reader 초기화 | 미정의 | **2A F-C-concat reader warm-start** (모든 학습 arm 동일) |
| dev | Kspon eval_clean 100 | **Kspon eval_clean에서 500** (기존 100 dev + 400 신규) |
| test | eval_clean 2,900 | **eval_clean에서 2,400** |
| arms | B0/B1/B2/B3 | **B0′/B1/B2/B3/B3-nat** |
| B3-nat | 없음 | **Kspon 4h natural 길이 분포, frozen tower, reader-only** |
| 주지표 | 상대 개선 | **절대 CER pp + CI**, 상대는 보조 |
| 채택 gate | B2>B1 & B2>B3 | **max(B2,B3) vs B0′ + 귀속 진단 분리** |
| early stop | dev 100 | **dev 500**, patience 4 |
| compute | 7~10일 가정 | **preflight/pilot 실측 후 full 승인** |
| test 표현 | “독립 test” | **“Kspon in-domain sealed holdout”** |

---

## 2. 데이터 v2

### 2.1 2C-short 4h

v1과 동일한 목표를 쓰되 **단위를 명시**한다.

| duration | 시간 비중 | 목표 시간 | 목표 발화 수(추정) | 전사 문자 수 |
|---|---:|---:|---:|---:|
| 0–2초 | 25% | 1.0h | TBD | TBD |
| 2–4초 | 35% | 1.4h | TBD | TBD |
| 4–6초 | 20% | 0.8h | TBD | TBD |
| 6–8초 | 20% | 0.8h | TBD | TBD |

- 선별 후 실제 **오디오 시간·발화 수·문자 수**를 모두 `summary.json`에 기록한다.
- 0.5초 미만, 빈 전사, 1자 이하 제외.
- CTC frame 하한: `output_frames >= target_len + required_blanks`를 preflight에서 검사하고 탈락률을 기록.
- Kspon train OOV: 1,101자 vocab에 없는 문자는 **클립 제외**를 기본으로 하고 OOV율을 보고. (대안: 매핑, 별도 승인)
- 화자 메타데이터가 없으면 “화자당 10% 상한”을 **세션/파일 프록시**로 대체하고 그 사실을 기록.

### 2.2 train mix

- 기존 6.0008h + short 4h = 10h.
- **B0′/B1**: natural sampler (6h만; short 4개를 인위적으로 40%까지 올리지 않음).
- **B2/B3**: LengthBalancedSampler, effective ≤4초 40%, 4–8초 30%, 8–16초 30%.
- **B3-nat**: 10h natural sampler (Kspon 4h도 natural).
- `B2−B1`은 “short data + sampler” 효과, `B3−B3-nat`은 sampler 효과, `B2−B3`는 balanced 조건의 adaptation 효과로 **명시적으로 분해 보고**한다.
- 클립당 예상 노출 횟수·replacement 여부·epoch 정의를 기록.

### 2.3 dev 500

- 원천: **Kspon eval_clean 3,000**.
- **기존 D-β dev 100을 dev에 포함**하고, 나머지에서 **400발화**를 길이 bin 층화로 추가한다.
- 총 **dev 500**.
- 기존 eval_clean 100은 test에 넣지 않는다.
- 가능한 경우 화자 층화. Kspon eval_clean 화자 ID가 없으면 세션/파일 프록시를 쓰고 한계를 기록.
- FLEURS dev 192는 보조 일반화 세트로 병기.

### 2.4 test 2,400

- eval_clean 3,000에서 **16초 초과 10건을 제외**해 평가 적격 **2,990**을 만든다.
- **dev 500**(기존 D-β 100 포함)을 먼저 고정하고, 남은 2,490 중 **test 2,400**을 봉인한다. **나머지 90발화는 미사용(spare)**으로 남긴다.
- `data/wave2b/test/kspon_eval_clean_2400.jsonl`로 봉인.
- 검증:
  - dev 500과 ID 교집합 0
  - eval_other와 ID 교집합 0
  - train·short·B3-nat와 ID 교집합 0
  - 기존 D-β 100이 test에 없음
  - 가능하면 화자 교집합도 확인
- **표현:** “Kspon in-domain sealed holdout”. “독립 test” 또는 “새 화자 일반화”라고 부르지 않는다.
- FLEURS test는 2A-lite에서 사용했으므로 **재사용 금지**.
- test는 checkpoint freeze 후 1회만.

### 2.5 Preflight 결과 (2026-11-04)

- eval_clean PCM/TRN 교집합 **3,000**; 16초 초과 **10건 제외** → 적격 **2,990**.
- dev **500** (기존 D-β 100 + 신규 400), test **2,400**, spare **90**; **dev∩test=0**, test∩기존100=0.
- OOV: 전체 **226/2,990 (7.56%)**, dev **38/500 (7.60%)**, test **185/2,400 (7.71%)**, OOV types 106. **이는 2A FLEURS vocab(1,101자) 기준 상한이며, 2B vocab은 Kspon train 6h+short에서 새로 build한다. 최종 OOV는 short 선별 후 재측정한다.**
- CTC frame 초과 **0**; OOV 정책은 별도 승인 대상.
- eval_clean에 **화자 ID 없음** → duration 층화만 적용. speaker-cluster bootstrap 불가, utterance bootstrap으로 대체.
- Kspon train shard는 로컬에 없음: filekey 50211~50215(각 14~15GB). C: 여유 약 18GB → **zip streaming + 선택 파일만 저장** 필요.
- 상세: `docs/STT/reports/W2B_preflight.md`, `reports/provenance/W2B/preflight.json`

---

## 3. Arms v2

| Arm | 타워 | 데이터 | sampler | 목적 |
|---|---|---|---|---|
| **B0′** | 동결 | 6h | natural | 새 기준선(재학습) |
| **B1** | 10–11층 LoRA | 6h | natural | adaptation |
| **B2** | 10–11층 LoRA | 6h + short 4h | balanced | adaptation + short |
| **B3** | 동결 | 6h + short 4h | balanced | data-only (balanced) |
| **B3-nat** | 동결 | 6h + short 4h | natural | data-only domain control |

- **B0′**: 2A F-C-concat의 **reader weight warm-start**, tower frozen. B1/B2/B3/B3-nat도 같은 reader 초기화.
- LoRA: 10–11층, rank 8, alpha 16, attention(q/k/v/post) + FFN 8모듈.
- B=0 초기화; **epoch-0 회귀 체크**: B1 0-step == B0′.
- B3/B3-nat: short feature를 `w1_extract --arms fc`로 추출하고 reader-only 학습.
- Feature parity: B1/B2 on-the-fly mel vs B3/B3-nat cached feature를 같은 샘플에서 수치 비교(허용오차 명시).
- B3-nat의 4h는 **길이 목표 없이** Kspon train에서 natural로 선별. B3의 4h와 가능한 한 같은 화자/도메인 범위를 쓰되 길이 분포만 다르게 한다.

### 3.1 B0′ 정의

- 6h natural, reader warm-start, tower frozen, same CTC/optimizer/scheduler/epoch/seed.
- 2A checkpoint는 **참고용 historical baseline**으로만 표기.
- B0′가 2A seed42 0.20913과 크게 다르면 그 차이를 기록하고, 비교는 B0′ 기준으로 한다.

---

## 4. 학습 v2

| 항목 | 값 |
|---|---:|
| batch size | 2 (16s), short-only batch 4 |
| grad accumulation | 4 |
| epochs | pilot 3 / full 12 |
| early stop | patience 4 on dev 500 |
| LoRA LR | 1e-4 |
| reader LR | 1e-3 |
| scheduler | cosine, warmup 10% |
| grad clip | 5.0 |
| seed | 42 (full에서 43 추가 가능) |
| threads | 6 |
| AMP | 없음 (CPU) |

- 0–9층은 `no_grad`, l06/l08 tap detach; gradient는 10–11층 LoRA와 reader에만.
- `--resume`: model/LoRA/reader/optimizer/scheduler/epoch/best/RNG.
- CPU peak RSS, sec/step, feature extraction, checkpoint 저장 시간을 기록.

---

## 5. Gate v2

### 5.1 Pilot (B0′/B3/B3-nat/B2 순서)

- B3-nat vs B0′: Kspon 4h natural의 데이터 효과.
- B3 vs B3-nat: balanced sampler 효과.
- B2 vs B3: balanced 조건에서 LoRA 효과.
- B2 vs B1: short+sampler 효과.
- **Pilot Go:** B2 또는 B3가 B0′ 대비 **절대 CER 1.0%p 이상 개선**, 또는 상대 5% 이상 + CI 방향 일치. n=500 dev에서도 불확실하면 **INCONCLUSIVE**로 두고 full 확장.
- ≤4초 bin은 pilot에서 **방향 일치**만 보고; 수치 gate는 full/test로.

### 5.2 Full

- **채택 판정:** `max(B2, B3)` vs B0′ — 절대 CER pp 차이, speaker-cluster paired bootstrap 95% CI 하한 > 0.
- **귀속:** B2−B1, B2−B3, B3−B0′, B3−B3-nat, B3-nat−B0′를 모두 보고.
- **상대 10%는 보조**; 절대 pp와 CI를 주지표.
- **FLEURS dev no-regression:** FLEURS dev CER가 B0′ 대비 **+1.0%p 이상 악화되지 않을 것**.
- **seed:** full에서 seed 42 + 43 (가능한 경우); test는 primary seed42만.
- **test:** Kspon eval_clean **2,400** 1회, B0′와 동일 조건 paired 비교. 사후 threshold 변경 금지. OOV 정책은 §2.5/별도 승인에 따른다.
- **No-Go:** CP-D2 원인 진단. B2>B1/B3를 Go의 단일 조건으로 쓰지 않는다.

---

## 6. DoD v2

- [ ] dev 500: eval_clean 3,000에서 기존 100 + 신규 400, test와 ID 교집합 0
- [ ] test 2,400: 16초 초과 10건 제외 후 dev 500·spare 90과 분리해 봉인
- [ ] OOV 사전등록: full 2,400 주평가 + in-vocab subset 2,215 보조, OOV 문자는 오류 처리
- [ ] B0′ 재학습, reader warm-start, epoch-0 B1==B0′
- [ ] B1/B2/B3/B3-nat 동일 vocab/reader init/seed/eval
- [ ] B3/B3-nat cached feature vs B1/B2 on-the-fly parity
- [ ] 4h short: 시간·발화·문자·CTC 적격률·OOV율
- [ ] B3-nat natural 4h: B3와 길이 분포만 다름
- [ ] pilot sec/step/RSS/peak disk
- [ ] test 2,400 1회, in-domain holdout 표기
- [ ] FLEURS test 미사용

---

## 7. 구현 순서 v2

| 단계 | 작업 | 예상 |
|---:|---|---:|
| 0 | Preflight: eval_clean split, Kspon shard, OOV, disk, CTC frame | 0.5~1일 |
| 1 | short 4h + B3-nat natural 4h 선별 | 1일 |
| 2 | test 2,400 봉인, dev 500 구축 | 1일 |
| 3 | B0′/reader warm-start/parity unit tests | 1일 |
| 4 | B3/B3-nat reader-only | 1일 |
| 5 | pilot B0′→B3→B3-nat→B2→B1(조건부) | 1일 |
| 6 | full runs (pilot 승인 후) | 3~5일 |
| 7 | dev/test 평가·보고 | 1.5일 |

- full run은 pilot 실측 후 별도 승인. 7~10일을 사전 약속하지 않는다.
- B3-nat 추가로 +0.5~1일 예상.

---

## 8. 남은 승인

- Gate v2 승인 완료
- dev 500/test 2,400/preflight 승인 완료
- **OOV 정책 승인 대기**
- **short 4h 다운로드·선별 승인 대기**
