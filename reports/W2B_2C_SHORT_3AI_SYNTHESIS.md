# Wave 2B + 2C-short — 3-AI 검토 종합

- 작성: 2026-11-04
- 검토 라운드: `w2b_2c_short`
- 검토 모델: GLM 5.3 Flash(max), Claude Sonnet 5.5(medium), GPT-6 Luna(xhigh)
- 원문:
  - `docs/hoplite/w2b_2c_short/2026-11-04_hoplite-review_w2b_2c_short_GLM.md`
  - `docs/hoplite/w2b_2c_short/2026-11-04_hoplite-review_w2b_2c_short_SONNET.md`
  - `docs/hoplite/w2b_2c_short/2026-11-04_hoplite-review_w2b_2c_short_LUNA.md`
- 검토 대상: `docs/plan_wave2b_2c_short.md`, `reports/EXTERNAL_REVIEW_W2B_2C_SHORT_2026-11-04.md`
- **상태: 설계 v1은 그대로 승인하지 않는다. v2 수정 후 pilot 승인.**

---

## 1. 한눈에 보는 결론

3개 모델 모두 **A안(4h short + 4-arm factorial)을 조건부 채택**했다. B3 삭제안(B)은 공통적으로 반대했다. 그러나 **현재 문서 그대로의 실행은 3/3 모두 반대**했고, 공통 Must-fix가 나왔다.

| 항목 | GLM | SONNET | LUNA | 종합 |
|---|---|---|---|---|
| 기본안 | A 조건부 | A 조건부 | A 조건부 | **A (수정 후)** |
| B3 유지 | 유지 | 유지(가장 싸다) | 유지 | **유지** |
| B0 기존 checkpoint | 반대 | 반대 | 반대 | **B0′ 재학습** |
| dev 100 | 부족 | 부족(≈500 확대) | 부족(≈500 확대) | **dev 확대** |
| eval_clean 2,900 | in-domain holdout | in-domain, 독립 아님 | in-domain, 독립 아님 | **in-domain으로 한정** |
| short 4h | 적절 | 적절 | 적절(단위 명시) | **4h, 단위 고정** |
| 7~10일 | 조건부 | 미실측 | 미실측 | **pilot 후 확정** |
| gate | max(B2,B3) vs B0 + 귀속 분리 | 절대 pp/CI + seed2 | 절대 pp/CI + cluster | **절대 pp 주지표** |

**핵심:** “2B(LoRA)만” 또는 “2C(데이터)만”이 아니라 **2×2 factorial은 유지**하되, **B0 재학습·reader 초기화·dev 확대·test 정책 기록·feature parity·compute 실측**을 먼저 고쳐야 한다.

---

## 2. 3-AI 공통 Must-fix

### MF-1. B0를 기존 2A checkpoint로 쓰지 말고 재학습

- 2A `w2a_fc_concat_s42.best.pt`는 **다른 학습 코드·sampler·epoch·reader 초기화**로 만들어졌다.
- B1/B2/B3와 B0를 비교하면 **reader 재학습·optimizer·step 수 효과**가 섞인다.
- **B0′**: B3와 동일한 코드·sampler·epoch·seed로 6h-only를 재학습한다. 기존 2A checkpoint는 historical reference로만 보고한다.
- **reader 초기화**: B1/B2/B3 모두 동일하게. GLM 권고는 **B0′의 학습된 reader warm-start** + LoRA B=0. Sonnet/Luna도 동일 초기화·step budget을 요구.
- **epoch-0 회귀 체크**: B1을 0-step(초기화만)으로 dev에 평가해 B0′와 일치하는지 확인.

### MF-2. dev 100은 너무 작다

- Sonnet/Luna: eval_clean 2,900 중 **약 500을 화자 층화로 dev로 이동**, test는 약 2,400으로 줄이는 안.
- GLM: dev 100의 검증력 부족을 인정하고, **INCONCLUSIVE 밴드 + FLEURS dev/seed43 확장**을 요구.
- 공통:
  - dev를 키우거나, 최소한 **화자 클러스터 bootstrap + seed 2개 + FLEURS dev 방향 일치**를 gate에 포함.
  - early stopping과 최종 gate를 같은 dev에서 반복하면 선택 편향이 커진다. **epoch 선택과 final gate 분리**.
  - 기존 dev 100의 **선출 규칙**을 provenance에 기록(무작위/선두/선별 불명).

### MF-3. eval_clean 2,900은 “독립 test”가 아니다

- eval_other와 **같은 Kspon 코퍼스·같은 60명 화자**를 공유한다.
- CP-D2-lite의 길이 분포 분석이 설계에 쓰였으므로 **분포 튜닝 편향**도 남는다.
- 따라서 표현을 **“Kspon in-domain sealed holdout”**으로 한정한다. “새 도메인/화자 일반화” 주장은 새 P0 holdout이 필요하다.
- **정책 기록 필수**: eval_clean 100은 D-β dev, 나머지 2,900은 2B test로 재지정한다는 **dated decision**을 `decisions.md`에 남긴다. eval_clean은 아직 최종 test로 사용된 적이 없다는 점을 근거로 기록.
- FLEURS test 재사용 금지는 3/3 동의. FLEURS dev는 2A에서 arm 선택에 쓰였으므로 **보조 진단**으로만.

### MF-4. short 4h는 “길이”와 “Kspon 도메인”이 결합된 개입

- 기존 6h는 **Zeroth 1,534 + Kconf 850**이며 Kspon이 전혀 없다(D-061). short 4h는 **Kspon 도메인 데이터의 최초 도입**이다.
- 따라서 B2−B1을 “길이 효과”라고 단독 해석하면 안 된다. **“Kspon short-domain 데이터 효과”**로 표기한다.
- Sonnet은 **B3-nat**(Kspon 4h, 길이 분포는 natural) control arm을 추가하라고 제안. Luna는 domain-control 필요성을 인정하되 필수는 아님. GLM은 대조 arm 추가를 강요하지 않음.
- 종합: **B3-nat은 optional high-value**; 예산이 허용되면 추가, 아니면 한계로 명시.

### MF-5. feature 경로·데이터 단위·OOV·화자 메타데이터를 사전 고정

- **feature parity**: B3는 offline `w1_extract` fc, B1/B2는 on-the-fly mel. 같은 샘플에서 수치 동등성(허용오차) unit test. GLM/Sonnet/Luna 공통.
- **4h 분배 단위**: 25/35/20/20이 **오디오 시간인지 발화 수인지** 명시. CP-D2의 4.1%/57.2%는 발화 기준이므로 시간 분배와 직접 비교 금지.
- **sampler**: effective ≤4초 40%는 natural 약 26.5%에서 1.5배 가중. 0–2초 세부 목표(예: effective 15%)와 클립당 노출 횟수(~19회/12 epoch)를 기록.
- **vocab/OOV**: Kspon train 라벨을 1,101자 vocab에 맞추는 규칙(제외/매핑)과 OOV율을 사전등록.
- **화자 메타데이터**: Kspon train에서 화자 ID/세션 프록시를 얻을 수 있는지 preflight. 불가하면 “화자당 상한·화자 중복 0” 규칙을 프록시 기준으로 변경.
- **CTC frame**: 0–2초에서 frame 수와 target 길이·반복 문자 blank 요구량을 검사; 불가능/경계 클립 제외율 보고.

### MF-6. compute·disk는 pilot 전 확정 금지

- 100-step pilot의 **sec/step, peak RSS, feature extraction time, epoch 처리량**을 실측.
- 7~10일/3~5일은 **UNVERIFIED**. pilot 결과를 full-run 일수로 환산해 사전 합의 임계(예: >5일) 초과 시 fallback(short 4h→2h 또는 epoch 12→8)을 **사전 선택**.
- **no_grad 최적화**: 0–9층은 `no_grad`, l06/l08 tap detach; gradient는 l10–11 LoRA와 reader에만. CPU 시간·activation 메모리 절감.
- **disk**: 19GB에서 14~15GB zip 전체 해제는 위험. `zipfile` stream으로 필요한 클립만 선택·삭제; peak를 실측. “25GB 필요”는 스트리밍 전제로 재산정.

---

## 3. 모델별 차이와 종합 판단

### 3.1 Arm 순서

- **Sonnet**: B0′ → B3 → B2 → B1(조건부). B3는 reader-only로 가장 싸고, 데이터 효과를 먼저 확인.
- **Luna**: preflight → 2h/4h 적격성 → matched 4-arm; B0′ 먼저.
- **GLM**: B0′/B3를 먼저, B1/B2는 pilot 후.
- **종합**: **B0′ → B3 → B2 → B1(조건부)**. B3 vs B0′에서 데이터 효과가 없으면 B2/B1을 보류.

### 3.2 Gate

- **Sonnet/Luna**: 절대 CER pp 차이를 주지표, 상대 개선은 보조. 화자 클러스터 bootstrap, seed 2개, FLEURS dev no-regression.
- **GLM**: `max(B2,B3)` vs B0′를 채택 판정으로, B2>B1/B2>B3는 **귀속 진단**으로 분리. pilot INCONCLUSIVE 밴드(상대 3~5%).
- **종합**:
  - **채택 판정**: `max(B2, B3)` vs B0′ (절대 pp + CI).
  - **귀속**: B2−B1(데이터), B2−B3(adaptation), B3−B0′(데이터-only)를 보고. B2가 B1/B3보다 반드시 좋아야 Go라는 조건은 폐기.
  - **pilot**: n=100/500의 한계를 인정해 INCONCLUSIVE 밴드 + FLEURS dev/seed43 확장.
  - **full/test**: 절대 pp + CI 하한; 상대 10%는 보조. test는 1회.

### 3.3 Test split

- **Sonnet**: 2,900 중 500을 dev, test 2,400.
- **Luna/GLM**: 2,900 test 유지 가능; dev 확대는 별도.
- **종합 권고**: **dev 500 / test 2,400**이 통계적으로 낫다. 단, 이는 2A/2B 사전등록 변경이므로 **사용자 승인 + decisions 기록** 후 확정. test 2,400도 in-domain holdout이다.
- 대안: 2,900 test 유지 + dev 500을 **별도 Kspon train speaker-disjoint**에서 확보; 데이터 확보 비용이 더 든다.

### 3.4 B3-nat

- **Sonnet**: 추가 권고(도메인 교란 분리).
- **Luna**: domain-control 필요성 인정, 필수 아님.
- **GLM**: 강요하지 않음.
- **종합**: optional high-value. 예산 허용 시 추가; 아니면 “short=Kspon domain” 한계를 명시하고 B2−B1을 길이 효과로 부르지 않는다.

---

## 4. 수정된 설계 v2 (권고안)

이 표는 승인 전 **설계 변경안**이며, 아직 구현·데이터 다운로드를 시작하지 않는다.

| 항목 | v1 | v2 권고 |
|---|---|---|
| B0 | 기존 2A checkpoint | **B0′ 재학습** (동일 코드·sampler·epoch·seed) |
| reader 초기화 | 미정의 | **B0′ reader warm-start** (또는 scratch; 사전등록) |
| Arms | B0/B1/B2/B3 | **B0′/B1/B2/B3** (+ optional B3-nat) |
| short 4h | 25/35/20/20 (단위 불명) | **시간·발화 수·문자 수 표를 모두 기록**, 0–2초 effective 목표 명시 |
| sampler | effective 40/30/30 | 유지 + 클립당 노출·replacement·epoch 정의 |
| dev | Kspon eval_clean 100 | **500 화자 층화** (test 2,400) |
| test | eval_clean 2,900 | **in-domain sealed holdout**; 2,400 또는 2,900, decision 기록 |
| test 주장 | “독립 test” | **“Kspon in-domain”**; 외부 일반화는 새 P0 |
| feature | B3 offline / B1,B2 online | **수치 parity unit test** |
| compute | 7~10일 가정 | **preflight/pilot 실측 후 확정** |
| gate | B2>B1 & B2>B3 | **max(B2,B3) vs B0′ + 귀속 보고** |
| 주지표 | 상대 개선 | **절대 CER pp + CI**, 상대는 보조 |
| seed | 42 | pilot 42, full **42+43** (가능 시) |
| FLEURS | dev 192 | dev 192 + **no-regression gate** |
| 0–9층 | forward | **no_grad + tap detach** |
| disk | 25GB 선확보 | **zip stream + 선택 삭제**, peak 실측 |

---

## 5. 남은 결정 (사용자 승인 필요)

1. **dev/test 분할**: eval_clean 2,900 중 500을 dev, test 2,400으로 줄이는 안을 승인하는가?
   - 대안: 2,900 test 유지 + dev 500을 별도 Kspon train에서 확보.
2. **B0′ 재학습 + reader warm-start**를 승인하는가?
3. **B3-nat** 도메인 control을 추가하는가? (예산 +0.5~1일)
4. **Gate v2**: 절대 pp 주지표, `max(B2,B3)` 채택, B2>B1/B3는 귀속 진단, pilot INCONCLUSIVE 밴드.
5. **테스트 표현**: “독립 test”가 아니라 “Kspon in-domain sealed holdout”으로 한정.
6. **일정**: pilot 전 7~10일 약속 금지; pilot 실측 후 full-run 승인.

---

## 6. 결론

- 3-AI 모두 **A안(4h + 4-arm)을 조건부 채택**했지만, **v1 그대로는 승인 불가**로 판정했다.
- 가장 중요한 공통 지적은 다음 4개다.
  1. **B0′ 재학습·reader 초기화·feature parity** 없이는 B1/B2/B3 비교가 성립하지 않는다.
  2. **dev 100은 너무 작고, early stop과 gate를 동시에 맡기면 편향된다.**
  3. **eval_clean 2,900은 독립 test가 아니라 Kspon in-domain holdout이다.**
  4. **short 4h는 길이 + Kspon 도메인 결합 개입이며, compute/disk는 미실측이다.**
- 따라서 다음 단계는 **설계 v2 수정 → 사용자 승인 → preflight/pilot** 순서다. full 2B 학습은 pilot 통과 전 시작하지 않는다.

---

## 7. 원문 링크

- GLM: `docs/hoplite/w2b_2c_short/2026-11-04_hoplite-review_w2b_2c_short_GLM.md`
- Sonnet: `docs/hoplite/w2b_2c_short/2026-11-04_hoplite-review_w2b_2c_short_SONNET.md`
- Luna: `docs/hoplite/w2b_2c_short/2026-11-04_hoplite-review_w2b_2c_short_LUNA.md`

## 8. Hoplite 사용량

| 모델 | 비용 | input tokens | output tokens | runtime |
|---|---:|---:|---:|---:|
| GLM max | $0.1378 | 1,072,368 | 85,002 | 14.6분 |
| Sonnet medium | $0.4135 | 415,225 | 19,190 | 3.9분 |
| Luna xhigh | $0.0734 | 1,038,976 | 45,097 | 10.1분 |
| **합계** | **$0.6248** | — | — | — |

