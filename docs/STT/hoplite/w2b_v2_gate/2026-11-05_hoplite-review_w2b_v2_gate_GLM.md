# Hoplite 독립 검토 — Wave 2B V2 reader-only gate (라운드 `w2b_v2_gate`)

- **검토자:** Hoplite (GLM, `z-ai/glm-5.3-flash`) — 신규 독립 라운드. 보관된 `w2b_2c_short_v2` 스레드와 무관.
- **검토일:** 2026-11-05 (KST 기준 작성)
- **검토 대상:** `docs/STT/reports/EXTERNAL_REVIEW_W2B_V2_GATE_2026-11-05.md` 전문(768행) 대독 + 참조 산출물 대조
- **동기화:** `git fetch origin` → `git pull --ff-only origin main`. 검토 시작 시 HEAD **`ac1fd82`**(요청 기준 커밋 `9d1aba6`의 직후 문서 커밋, 검토 요청서 내용 동일). 검토 중 원격에 `e05d524`(dispatch 로그·watcher 스크립트 추가, 결과 문서 무변경)가 push되어 ff-only로 재동기화했다. 본 검토의 근거는 `ac1fd82` 시점의 문서와 산출물이다.
- **방법:** 문서 전문 대독, 참조 JSON/Markdown/코드 대조(부록 A), 산술 검산. **실험은 실행하지 않았다.** 모든 수치 확인은 기존 커밋된 산출물 대상이며, 정성 추정은 별도 표기했다.

---

## 0. 결론

한 줄: **B — caveat부 PASS.** "V2 reader-only recipe-level PASS"로 인정한다. 단, PASS 기록에 5개 caveat(귀속·화자 독립·길이 분포·단일 seed·V2 vocab 조건)을 **조건으로** 부착하고, "Kspon short 4h 데이터 효과" 귀속 주장은 compute/domain control 전까지 금지한다. exploratory로 강등할(C) 결정적 결함은 발견되지 않았다.

요약 근거: (1) 사전등록 절차가 커밋 이력으로 확인되고(v3 설계 `ac253bc`가 모든 결과 커밋에 선행), 모든 gate 조건을 문턱의 ~10배 여유로 통과했다. (2) 양 arm이 동일 vocab·feature·init·test를 공유하므로 step/exposure/domain/length confound는 **비교의 내부 타당성**이 아니라 **해석(귀속)**의 문제다. (3) test 누출·vocab 편향·군집 부트스트랩 한계를 포함한 뒤집기 후보를 점검했으나 gate를 뒤집을 규모의 결함은 없었다.

---

## 1. Q1~Q8

### Q1. Gate PASS의 지위

**① 판정:** recipe-level PASS를 **인정한다(B)**. exploratory/INCONCLUSIVE로 강등할 이유가 없고, 판정을 뒤집을 결정적 결함은 찾지 못했다.

**② 근거:**
- 사전등록 조건 전부 충족 + 큰 여유: dev Δ **+10.187%p** (CI [+9.107, +11.328]), test Δ **+9.737%p** (CI [+9.228, +10.258]), FLEURS dev **−0.216%p**. 문턱(Δ≥1.0%p, CI 하한>0) 대비 효과가 약 10배라서, 선택 편향·다중성 규모의 왜곡으로는 만들어낼 수 없는 크기다.
- 절차 무결성(산출물 대조): `test_freeze.json`의 3개 sha256이 문서 §10.2와 **정확히 일치**하고, candidate 선택 문구("B3 selected on dev 500 before sealed test; B3-nat is sampler control, not a candidate")가 기록돼 있다. 커밋 이력 확인: v3 설계/D-067(`ac253bc`) → B0′ baseline(`342c569`) → B3 결과(`5fb03be`) → D-071 PASS(`9fe5bd0`) 순서로, **사전등록이 결과보다 선행**한다.
- 내부 타당성: B0′/B3가 동일 V2 vocab(1,329자 — `vocab_v2.json` 직접 확인), 동일 cached feature, 동일 remapped init, 동일 test를 쓴다. 따라서 3.13× step / 1.67× exposure / Kspon domain / 길이 분포 차이는 **두 레시피 비교의 유효성을 깨지 않고**, "무엇 때문인가"라는 귀속 해석만 제한한다.
- 화자 군집 견고성(정성 검산, 실행한 실험 아님): `W2B_split_audit.md`에 따르면 eval_clean은 화자당 100발화 규모로 구성됐다(≈30 화자 → test 2,400은 약 24개 화자군). utterance-level 부트스트랩이 화자 상관을 반영하지 못해도, **ICC=1 극단 가정**에서도 SE가 최대 ~√100=10배 팽창해 95% CI 하한이 대략 +4~5%p 수준으로 추정된다. 즉 군집 효과만으로 gate를 뒤집는 것은 비현실적이다(정성 추정치이며 대체 분석으로 대체 가능).
- 점검했으나 기각한 뒤집기 후보: ① vocab을 통한 test 누출 — vocab 구축에 eval/test 텍스트 미사용(코드 docstring·§3.3 일치), test는 coverage audit에만 사용. ② vocab이 B3에만 유리 — 양 arm 동일 vocab, test OOV도 동일 적용. ③ 화자 중복 — 확인 불가하나 위 군집 검산상 gate 뒤집기 규모 아님. ④ dev 재사용(D-β 100 포함) — dev∩test=0, test∩D-β100=0(`W2B_split_audit.md`)이고 이번 라운드 선택은 사전등록 절차를 따름. 누적 선택 압력은 있으나 결정적이지 않음.

**③ 필수 조치:** D-071과 gate 보고서에 estimand 문구를 명시한다: "레시피 효과 — Wave 1 6h 레시피(B0′)를 'Kspon short 4h 추가 + balanced sampler + 동일 12 epoch'의 10h 레시피(B3)로 바꾼 효과". MF-A의 caveat 5종을 PASS 기록에 부착한다. "data effect" 표현은 기록에서 제외한다.

**④ 다음 단계 차단 여부:** **아니오.** LoRA 착수·다음 실험 모두 가능. 차단되는 것은 *귀속 주장*뿐이다.

### Q2. 인과 귀속 — 무엇을 control해야 하는가

**① 판정:** estimand를 "이 recipe로 10h를 학습했을 때의 효과"로 제한하면 **정당**하다(문서 §5.3의 자체 제한이 올바르다). "short 4h 데이터 효과"를 주장하려면 **최소 1개의 compute 정합 control + 도메인/길이 분해 control**이 필요하다.

**② 근거:** `training_budget.json` — B0′ 3,576 step/72.0096h vs B3 11,196 step/120.2652h(3.13×/1.67×, 문서와 일치). B3 epoch-4 진단(+7.98%p)은 12-epoch cosine의 epoch-4라서 LR이 다르고, checkpoint 미보존, exposure 40.1h로 부족 — clean control 아님(JSON note에도 동일 명시). **문서가 명시하지 않은 핵심 구조:** 데이터 **스왑** control(Kspon short 4h ↔ Kspon long 4h, 또는 non-Kspon short 4h)은 총 10.02h·12 epoch·sampler를 유지하므로 **steps/exposure/schedule이 정의상 B3와 정확히 일치**한다. 별도의 schedule 트릭 없이 compute를 고정하는 유일한 control 계열이다. 반면 B0′-38은 step만 근사 일치(11,324 vs 11,196)하고 exposure가 228h로 1.9× **과잉**, 38-epoch cosine은 12-epoch와 다르다. B0′-rep10(6h 반복으로 10.02h 구성 후 12 epoch)은 steps·exposure·schedule을 모두 일치시켜 "새 데이터 vs 반복 학습"을 분리한다.

**③ 필수 조치(우선순위와 해석 한계):**
1. **B3-long(Kspon long 4h 스왑)** — 도메인 고정, 길이만 변경. B3와 compute 동일 → "short 4h 특유 효과 vs Kspon 도메인 효과"의 직접 분해. 한계: long 구간은 OOV율이 더 높음(6–8초 bin 이미 4.376%, `short_4h_v2_summary.json` by_bin) → 4h 확보 가능성·sampler bin(8–16초) 정의를 사전 감사 필요. 결과는 dev+FLEURS만.
2. **B0′-rep10** — Wave 1 6h를 반복·서브샘플링해 10.02h로 구성, 12 epoch. B3와 compute 완전 일치 → "새 4h 데이터"와 "알던 6h 반복"의 차이 분리. 한계: 동일 클립 재등장 처리(1-epoch 내 중복)와 sampler bin 재계산을 사전 정의해야 하고, 반복 데이터의 다양성 손실이 "신규성"을 과대평가하게 만들 수 있음. (이 설계는 내 제안이며 문서에 없음.)
3. **B0′-38(폴백)** — step 근사 일치. 한계: exposure 1.9× 과잉 + schedule 불일치 → "step 수만으로 설명되는가"의 상한 추정용.
4. **B3-4 재학습(checkpoint 보존)** — 기존 진단의 보강. 한계: exposure 부족 + LR 불일치는 여전. 별도 우선순위 항목으로 두지 말고 B3 계열 재학습 시 checkpoint 보존을 절차화.

**④ 다음 단계 차단 여부:** "데이터 효과" 주장은 차단. LoRA 실행 자체는 불차단. 단, LoRA의 추가 효과 주장에도 동일한 step-matching 원칙을 적용해야 한다(Q7).

### Q3. V2 vocabulary 2-pass selection

**① 판정:** 2-pass loop는 short subset의 문자 coverage를 **선택에 조건화**하지만, (a) eval/test 누출은 없고, (b) 양 arm이 동일 vocab을 공유해 비교의 내부 타당성은 유지되며, (c) 영향의 상한이 관측값으로 묶여 있다(test OOV 1.875% clip / 0.1299% 문자). **final V2를 다시 만들 필요 없다.** "V2 vocab에 조건화된 결과"로 표기하는 것으로 충분하다.

**② 근거:** `vocab_v2.json` 1,329자 / `vocab_v2_alltrain.json` 2,342자 직접 확인. `runner/w2b_build_vocab_v2.py`의 `--short` 플래그("short manifest whose refs define V2")가 2차 경로를 코드로 확인 — draft(all train.trn) → 1차 선별 → `--short`로 final V2 → 재선별의 순서가 문서 §3.3과 일치. draft vocab은 학습에 미사용. V1 회귀안(1,101자)은 OOV 제외 90.727%로 비현실적(D-069) — 재고려 대상 아님.

**③ 필수 조치:** (a) gate 보고서에 "results are conditional on the V2 vocabulary (1,329 chars) and the 2-pass short-selection procedure"를 명시. (b) 향후 데이터 재선별이 있는 라운드에서는 **사전(pre-selection) 시점에 vocab을 고정하는 1-pass 원칙**을 사전등록 — 후보군: pre-selection eligible refs 기반 고정 또는 all-train draft 고정. (c) 현재 결과의 비교 가능성을 유지하기 위해 final V2 재구성은 금지.

**④ 다음 단계 차단 여부:** **아니오.**

### Q4. B3-nat / sampler

**① 판정:** "dev에서 sampler 효과는 유의하지 않다"는 **dev-only 서술로 허용**된다. **B3-nat test 평가는 불필요**하다 — 실행하면 exploratory가 되고 이미 소진된 test의 신뢰도를 추가로 소모한다. best epoch 11(0.2633) vs epoch 12(0.2634)의 차이(0.0001)는 결론에 무영향이다.

**② 근거:** `v2_dev_bootstrap.json` — B3−B3-nat +0.490, CI [−0.229, +1.205](0 포함). `W2B_v2_dev_results.md` — B3-nat best epoch 11, B3 best=final epoch 12. B0′/B3 모두 best=final이라 checkpoint 선택 비대칭도 사실상 없음.

**③ 필수 조치:** 현 상태 유지(문서 §4.7의 서술이 적절). sampler 질문이 미래에 의사결정에 중요해지면 **새 holdout + 사전등록**으로 별도 질문화한다. "B3-nat의 test 숫자가 나중에 더 좋아 보이면 candidate를 바꾼다"는 유혹을 원천 차단하는 원칙을 MF-B에 포함한다.

**④ 다음 단계 차단 여부:** **아니오.**

### Q5. Test 재사용과 confirmatory 지위

**① 판정:** test 2,400의 **confirmatory 예산은 소진**됐다. 이후 동일 test를 쓰는 20-epoch·seed 43·LoRA·B3-nat 평가는 전부 **exploratory/post-hoc**이다. 새 confirmatory 주장의 최소 요건은 **사전등록된 새 holdout**이다. 후보별 성격: (a) **eval_other 기반 holdout** — 모델이 본 적 없는 발화로서 유효한 in-family holdout. 단, ≤4초 57.2%로 길이 분포가 다르고, `W2B_split_audit.md`상 eval_clean/eval_other이 **같은 화자의 발화를 ~50/50으로 나눈 것**이라는 점(모델에는 무관하나 표기 필요)과 도메인 스타일 차이를 명시해야 한다. (b) **FLEURS test** — 교차 도메인 회귀 확인용 **보조**로만 가능; Kspon 결론의 대체 불가(문서 판단이 타당). (c) **spare 90** — 규모상 게이트 판정용 부적합.

**② 근거:** §4.8/§7.5, `test_freeze.json`(freeze 후 1회, sha256 고정), D-071, `W2B_split_audit.md`.

**③ 필수 조치:** 서면 policy(MF-B): ① test 2,400 = "소진(spent)" 선언, ② 향후 사용 시 보고서에 "exploratory (test reused)" 라벨 의무, ③ 다음 confirmatory 판정(예: LoRA go/no-go) **전에** 새 holdout을 선출·사전등록, ④ 탐색적 test 결과로 frozen candidate 교체 금지.

**④ 다음 단계 차단 여부:** 미래 **confirmatory 주장**은 차단. 실험 실행 자체는 불차단.

### Q6. 다음 우선순위

**① 판정:** 아래 순서. 1위는 "가장 싸고 가장 큰 리스크를 제거", 2위는 "결과의 의미를 바꾸는 분해".

**② 근거:** 단일 seed(42)는 기록된 PASS의 가장 큰 미해결 위협이며 제거 비용이 최소(~3h CPU, 문서 추정). 반면 confound 분해는 gate 합격 여부가 아니라 **주장의 범위**를 바꾼다. 스왑 control이 정의상 compute-matched인 점(Q2)이 선택 이유다.

**③ 필수 조치(순서):**
1. **seed 43 재현** — B0′/B3 12-epoch, **dev+FLEURS만** 보고, test 금지. 설계 변경 0, 즉시 실행 가능.
2. **B3-long(Kspon long 4h 스왑)** — 사전 OOV/coverage 감사 후 학습. 도메인 vs 길이 분해.
3. **B0′-rep10**(폴백 B0′-38) — 신규성 vs 반복 분리.
4. **LoRA 구현·GPU smoke** — 위와 **병행 가능**(GPU 작업과 CPU 작업은 자원이 분리). 단 평가는 사전등록 후.
5. **20-epoch 3-arm** — D-070 대로 보류. compute-matched가 아니고 시간당 가치가 가장 낮다.

**④ 다음 단계 차단 여부:** LoRA **실행** 전 필수 항목: seed 43, MF-B(test policy), MF-E(LoRA 프로토콜 사전등록), GPU parity smoke. 병행 가능: B3-long 데이터 준비, vocab 조건부 문서화. "20-epoch vs step-matched" 질문에는 **step-matched(및 스왑 control)가 우위** — 20-epoch는 수렴 확인일 뿐 step/exposure 비율(3.13×/1.67×)을 그대로 유지한다(D-070의 판단이 정확하다).

### Q7. LoRA 착수 가능성

**① 판정:** **조건부 Go.** 구현·인프라(GPU 패키징, smoke, sec/step·메모리 측정)는 즉시 착수 가능. 첫 **평가**는 사전등록된 step-matched 설계와 새 holdout policy 하에서만 수행한다.

**② 근거:** 저장소에 LoRA 구현 코드 없음(grep 확인 — w2a 문서 문구만 존재). `train/d5_reader.py`는 `--device cuda`(CUDA 부재 시 CPU fallback)·resume을 지원하지만 Modal 패키징·볼륨·T4/L4/L40S smoke은 미완료(MF-6 부분 이행과 일치). **구조적 유의점(문서에 명시 없음):** 현 파이프라인은 frozen-tower의 **캐시된** feature로 학습하지만, 타워 상위층 LoRA는 캐시를 무효화한다 → 학습 루프가 타워 forward를 배치마다 포함하도록 재설계되고 메모리·속도 프로파일이 완전히 달라진다. 기대 이득은 측정된 바가 없으며, 현재 +10%p는 recipe 효과라 LoRA 기대치와 직접 비교할 근거가 아직 없다(문서에 없음).

**③ 필수 조치(Must-fix):** (a) LoRA 프로토콜 사전등록 — arm 정의(B1/B2), **step-matched 비교**(동일 데이터·sampler·epoch에서 B3 vs B3+LoRA, 동일 형태의 schedule), seed 2개 이상, stop/go: dev Δ≥1.0%p & CI 하한>0, FLEURS guardrail 유지, 비용 상한과 중단 기준. (b) MF-B test policy 준수(test 2,400 재사용은 exploratory 라벨). (c) GPU parity 체크리스트 — init 등가성, feature 경로, seed/결정론, CER 정규화(`normalize_nospace`) 동일성. (d) 첫 평가는 dev 500 우선, confirmatory는 새 holdout에서만.

**④ 다음 단계 차단 여부:** 확인적 주장 차단, 구현 착수 불차단.

### Q8. 보고·주장의 범위

**① 판정:** 현 문장은 **수정 필요**. "Kspon short-domain 4시간을 추가"는 도메인+길이+compute를 한 원인처럼 읽히게 한다. 정확한 라벨은 **recipe effect** 하나뿐이다. "data effect"·"domain effect"·"short-length effect"는 모두 미분리 상태다.

**② 근거:** §4.2 confound 표, §7.1–7.4, `training_budget.json`. 또한 test의 성격(in-domain procedural holdout, ≤4초 74.33%, 화자 ID 부재)은 문장에 전혀 노출되지 않았다.

**③ 필수 조치:** §4의 수정안 사용. "화자 독립", "일반화", "state-of-the-art" 배제에 동의한다. 추가 caveat: 단일 seed, holdout 1회 사용, balanced sampler가 recipe의 일부라는 점, FLEURS는 보조 guardrail이라는 점.

**④ 다음 단계 차단 여부:** 외부 공개 문구 확정 전에는 MF-A/MF-G 이행이 필요하나, 실험 진행 자체는 불차단.

---

## 2. Must-fix 표

| ID | 지적 | 조치 | 우선순위 | LoRA 차단 여부 |
|---|---|---|---|---|
| **MF-A** | PASS 기록에 estimand·caveat 미부착 — "PASS"만으로 "데이터 효과"로 오독될 위험 | D-071/gate 보고서에 "recipe-level" 문구 + caveat 5종(귀속 불가·화자 비독립·길이 편향 test·단일 seed·V2 vocab 조건) 명시 | **P0** | 아니오(주장만 차단) |
| **MF-B** | test 2,400 소진 후 재사용 policy 부재 | 서면 policy: 소진 선언, 향후 사용 시 "exploratory (test reused)" 라벨 의무, 다음 confirmatory 전 새 holdout 사전등록, 탐색적 결과로 candidate 교체 금지 | **P0** | **예 — LoRA의 confirmatory 평가 차단(실행은 가능)** |
| **MF-C** | 단일 seed(42) | seed 43 재현(B0′+B3, dev+FLEURS만, test 금지) | P1 | 아니오(외부 robustness 주장 전 권장) |
| **MF-D** | compute·domain·length confound 미분해 | B3-long 스왑 → B0′-rep10(폴백 B0′-38) 순 실행; 결과는 dev+FLEURS만 | P1 | 아니오("데이터 효과" 주장 차단) |
| **MF-E** | LoRA 프로토콜·GPU parity 미확정 | 사전등록(step-matched 비교, stop/go, 비용 상한) + GPU smoke(sec/step·메모리) 측정 | P1 | **예 — 평가 착수 전 필수** |
| **MF-F** | V2 2-pass 조건이 결과 기록에 미표기 | "V2 vocab(1,329자)·2-pass 절차에 조건화된 결과" 표기 + 향후 1-pass vocab 원칙 사전등록 | P2 | 아니오 |
| **MF-G** | 화자 중복 확인 불가가 대외 문구에 누락될 위험 | 모든 대외 문장에 "not speaker-independent" 명시 | P2 | 아니오 |
| **MF-H** | 수치 회계 기준 불일치 — cache 10.0221h(frames 기준 추정) vs manifest 합 10.0024h; OOV audit 40,788자 vs CER 분모 38,224자 | 시간·문자 회계 기준(frames/25 vs manifest, 정규화 전/후)을 문서화해 하나로 고정 | P3 | 아니오 |

---

## 3. 다음 실험 우선순위

1. **seed 43 재현** (B0′/B3, dev+FLEURS만, test 금지) — 최저 비용, 단일 seed 리스크 제거.
2. **B3-long: Kspon long 4h 스왑** — 정의상 compute-matched; 도메인 vs 길이 분해; 사전 OOV/coverage 감사 필수.
3. **B0′-rep10** (폴백: B0′-38) — 신규 데이터 vs 반복 학습 분리.
4. **LoRA 구현·GPU smoke** — 1–3과 병행 가능(GPU/CPU 자원 분리); 평가는 사전등록 후.
5. **20-epoch 3-arm** — D-070 대로 보류; compute-matched 아님, 시간당 가치 최하.

---

## 4. 대외 주장 문장 (수정안)

> "V2 reader-only 12-epoch 비교에서, Wave 1 6시간 레시피(B0′)에 Kspon train short 4시간(5,079클립)을 추가하고 balanced sampler로 학습한 10시간 레시피(B3)가 dev 500에서 +10.19%p, dev에서 사전동결한 뒤 1회 평가한 in-domain procedural holdout(test 2,400)에서 +9.74%p의 CER 개선을 보였다(paired utterance bootstrap 95% CI [+9.23, +10.26]). 이 개선은 **recipe-level 비교 결과**이며, 추가 optimizer step(3.13배), audio exposure(1.67배), Kspon 도메인, 짧은 발화 분포의 효과를 분리한 것이 아니다. holdout은 **화자 독립이 아니며** ≤4초 발화가 74.3%다. 결과는 **단일 seed(42)**와 **V2 vocabulary(1,329자, 2-pass 선별 절차)**에 조건화된다. FLEURS dev에서 유의미한 악화는 없었다(−0.216%p)."

라벨 판정: **recipe effect**만 사용 가능. data/domain/short-length effect는 control 전 금지.

---

## 5. 불확실한 점

- **시간 회계:** `v2_data_ready.json`의 `ten_hours_est` 10.0221은 frames(901,985)/25 기준 추정으로 보이고, manifest 합은 6.0008+4.0016=**10.0024**h다(차이 0.0197h≈71초, 0.2%). `training_budget.json`은 10.0221을 쓴다. 3.13×/1.67× 비율 결론은 불변이나 어느 정의가 공식인지 고정이 필요하다(MF-H).
- **문자 회계:** OOV audit의 test 40,788자 vs CER 분모 38,224자 — 정규화(공백 제거·구두점 제거) 전/후 차이로 추정되나 문서에 명시가 없다.
- **군집 견고성 검산**은 내 정성 추정(Q1 ②)이며 실행한 실험이 아니다. speaker-cluster bootstrap이 불가능한 상황에서의 대체 민감도 분석으로 formalize할 가치가 있다.
- **소요 시간 추정**(~3h CPU)은 문서/결정 로그 값을 인용한 것으로 독립 검증하지 않았다.
- **dev 500의 D-β 100 포함:** 라운드 간 누적 선택 압력의 크기는 미평가. 완화 요인: dev∩test=0, test∩D-β100=0, 이번 라운드 선택이 사전등록 절차를 따름.
- **B0′-rep10 설계는 내 제안**으로 문서에 없다. 반복 구성 시 balanced sampler bin 재계산과 1-epoch 내 중복 처리 정의가 사전 조건이다.
- **FLEURS dev 규모(n=192, 7,861자)**는 `fleursdev_*.json`에서 확인 — 문서 본문에는 미기재. 게이트 문서에 규모 기재 추가 권고.
- B0′-38/B0′-rep10이 만드는 "완전한" compute 매칭은 존재하지 않는다(스왑 control만 정의상 완전). 어느 control이든 해석 한계를 결과와 함께 기록해야 한다.

---

## 12(§12에 대한 답). 문서 충분성 판단

이 요청서는 경계 설정에 **충분했다**. §5.3(판정이 말하지 않는 것)과 §7의 자기 한계 기술이 정확하고, 필자의 독립 검산에서 산술 불일치가 발견되지 않았다(MF-H의 회계 기준 차이는 표기 문제). 개선 여지: ① FLEURS dev 규모(n=192) 기재, ② 시간/문자 회계 기준 정의, ③ 데이터 스왑 control이 compute-matched라는 구조적 장점의 명시, ④ LoRA 시 캐시 파이프라인 무효화라는 구현 제약의 명시.

---

## 부록 A. 검증 대상과 확인 결과

실험은 실행하지 않았다. 아래는 커밋된 산출물과 문서 수치의 대조 결과다.

| 항목 | 문서 값 | 산출물/코드 확인 | 결과 |
|---|---|---|---|
| test CER B0′ | 0.359643 (13,747/38,224) | `v2_test_bootstrap.json` | 일치 |
| test CER B3 | 0.262270 (10,025/38,224) | `v2_test_bootstrap.json` | 일치 |
| test Δ/CI | +9.737 [9.228, 10.258], B=20,000, seed 42 | `v2_test_bootstrap.json` | 일치 |
| dev CER 3 arm | 0.3701 / 0.2682 / 0.2633 (7,755자) | `v2_dev_bootstrap.json` | 일치 |
| dev Δ/CI | +10.187 [9.107, 11.328]; B3−B3-nat +0.490 [−0.229, +1.205] | `v2_dev_bootstrap.json` | 일치 |
| FLEURS dev | 0.209770 (1,649/7,861) vs 0.207607 (1,632/7,861), Δ −0.216 | `fleursdev_{b0p,b3}_v2_s42.json` | 일치 |
| 학습 예산 | 3,576/72.0h vs 11,196/120.3h; epoch-4 진단 주의 문구 | `training_budget.json` | 일치 |
| checkpoint sha256 3건 | §10.2 표 | `test_freeze.json` | 일치 |
| clip overlap 9쌍 전부 0 | §3.7 | `overlap_final.json` | 일치 |
| vocab | 1,329자(head 1,330) / draft 2,342 | `vocab_v2.json`, `vocab_v2_alltrain.json` | 일치 |
| short set | 5,079클립/4.0016h, OOV 2,319/97,628=2.3753%, bin별 0.99/1.97/3.06/4.38% | `short_4h_v2_summary.json`(재계산 포함) | 일치 |
| test 길이 bins | 1,151/633/431/185, ≤4초 1,784(74.33%) | `test_breakdown.json` | 일치 |
| 오류 분해 | sub 8,691/6,372, del 4,159/2,685, ins 897/968, blank 7/2, len_ratio 0.9147/0.9551 | `test_breakdown.json` | 일치 |
| 결정 로그 | D-069/070/071 내용 | `docs/decisions.md` | 일치 |
| 사전등록 순서 | v3 설계가 결과에 선행 | `git log`: `ac253bc` < `342c569` < `5fb03be` < `9fe5bd0` | 확인 |
| 2-pass vocab 구현 | §3.3 절차 | `runner/w2b_build_vocab_v2.py` `--short` 경로 | 확인 |
| LoRA 코드 부재 / CUDA 지원 | §7.7 | grep + `d5_reader.py` `--device cuda` fallback | 확인 |

**발견한 유일한 수치 불일치:** §3.2 "10.0221h" vs 구성 합 10.0024h(위 불확실성·MF-H 참조). 이 외에는 불일치가 없었다.

---

*이 검토는 읽기 전용이다. 저장소의 다른 파일은 수정하지 않았고, 이 보고서 파일 생성 외의 쓰기는 없다. 실험은 실행하지 않았으며, 모든 판정은 문서와 커밋된 산출물의 대조에 근거한다.*
