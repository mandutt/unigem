# C5 EG2 → T5Gemma2 bridge — 외부 독립 검토 보고서 (GLM 5.3 Flash)

- 작성: 2026-11-08 (UTC), 독립 외부 reviewer (GLM 5.3 Flash)
- 검토 대상 문서: `reports/EXTERNAL_REVIEW_C5_BRIDGE_2026-11-08.md` (624줄 전문 직접 열람, 요약/발췌에 의존하지 않음)
- 기준 commit: `origin/main` HEAD **`f8c33a69c3dced040a401faf552a74437a696d02`**
  - 동기화: `git fetch origin` + `git pull --ff-only origin main` → "Already up to date"
  - 문서 기재 기준 `ee084af`는 HEAD의 직계 조상임을 확인. HEAD는 리뷰 요청 문서 3건(`8eeb0d3`, `88ccf77`, `f8c33a6`)만 추가된 상태이므로 실험 결과는 `ee084af`와 동일.
- 제약 준수: 학습 없음, test 163 미개봉, subagent·타 LLM 미사용, P1·외부 API 미사용,
  `eval/slot_verify.py` 미변경(SHA256 `a262cee0…869d03` 재확인 일치).
  저장소에 대한 유일한 쓰기는 본 보고서 파일 1개.
- 성격: **consultation only.** 본 보고서의 모든 제안은 기존 승인 절차가 별도로 필요하며,
  어떤 gate 변경도 승인된 것으로 읽어서는 안 된다. bridge 계열 결과는 탐색 트랙이고,
  A1 native pilot300은 별개의 제품 fallback 후보다(둘을 혼용하지 않음).

---

## 0. 최종 판정

### Bridge viability verdict: **STOP — 동의**

핵심 요지:

1. **격차가 통계적으로 압도적이고 구조적이다.** 동일 val100 ID에서 A1 native 0.6552/100%/100% vs
   bridge 최고(ss-slot) 0.4074/12%/69%. 내 paired 분석(§1.3)에서 ΔF1 = **−0.2478,
   95% CI [−0.2773, −0.2192]**, grounded는 100→12로 88/100 문서가 전부 같은 방향으로 역전(McNemar p ≈ 1e-14).
   제품 gate(grounded ≥ 0.99, new-slot micro ≤ 0.01)와 bridge 실측(0.12, 480/858 slots 발명) 사이 격차는
   데이터 규모·feature·디코딩 트릭 수준의 문제가 아니라 **표현 공간 병목**으로 설명되며(D-095),
   어떤 단일 반증 실험이 이 격차를 뒤집을 물리적 여지가 없다.
2. **사전 등록 DoD 종료는 사후 합리화가 아니다.** git으로 확인: `adc08f2`(feature 커밋) 시점의
   `reports/C5_B2_LAYER12_SS_SLOT_2026-11-08.md`에는 DoD 표(F1 ≥ 0.36 / grounded ≥ 20% / EOS ≥ 58%)가
   있고 결과 섹션은 전부 "진행 중/pending"이었다. 결과는 이후 커밋 `ee084af`에서 확정됐다.
3. 단, 종료 결론의 **일반화 범위는 수정이 필요하다**(Q3, Q4, Q12). "layer9 역설"과 "slot-aware의 grounded
   부분 회복"은 내 검증에서 **통계적 유의성이 없다**(p = 1.0 / p = 0.77). 즉 bridge 종료 결론 자체는 강건하지만,
   종결 사유로 쓰인 일부 세부 해석(회복 실패, feature 축 소진의 근거)은 노이즈를 근거로 과잉 서술되어 있다.

NARROW를 정당화할 "단일 반증 실험"이 존재하는가? — **존재하지 않는다.**
유일하게 decision-relevant한 무훈련 attribution control(§4 실험 E1: teacher-hidden free-running)은
어느 결과가 나와도 EG2 기반 bridge를 A1 대비 우위로 만들지 못한다:

- teacher hidden을 넣고 free-running이 **성공**하면 → 병목이 adapter/EG2 표현임이 확정 → EG2 재사용 전제 자체가 사망(STOP 확정, 메커니즘 입증).
- teacher hidden임에도 **실패**하면 → 병목이 디코더 free-running 쪽 → on-policy KD가 마지막 가설이 되지만,
  그 성공 상한도 A1 native(같은 디코더가 native 입력에서 이미 0.6552/100%/100%)를 넘을 이유가 없다.

따라서 E1은 **bridge 부활 실험이 아니라 종료 사유의 메커니즘 귀속(attribution) 실험**으로만 권고한다.

---

## 1. 독립 검증 결과

### 1.1 Raw artifact 재계산 (요청서 핵심 수치 전수 확인)

| 항목 | 문서 값 | 내 재계산/확인 | 출처 |
|---|---:|---:|---|
| ss-slot val100 F1 / grounded / EOS / rep4 / new-slot | .4074 / 12% / 69% / .4054 / .559 | **0.40736 / 0.12 / 0.69 / 0.40544 / 0.5594** | `generation_val100_b2_layer12_300_ss_slot.metrics.json` |
| ss-slot slot repair drop-new / oracle | .3159 / .3203 (grounded 100%) | **0.31594 / 0.32031, grounded 1.0** | `slot_repair_ss_slot_val100.json` |
| layer12 val100 | .3464 / 21% / 60% / .588 | **0.34639 / 0.21 / 0.60 / 0.58824** | `generation_val100_b2_layer12_300.metrics.json` |
| layer9 val100 | .3340 / 22% / 55% / .5755 | **0.33399 / 0.22 / 0.55 / 0.57550** | `generation_val100_b2_layer9_300.metrics.json` |
| ss val100 | .3783 / 10% / 59% / .4625 | **0.37830 / 0.10 / 0.59 / 0.46253** | `generation_val100_b2_layer12_300_ss.metrics.json` |
| B2 full val161 / val100 subset | .3349 / 18.01% / 60.25% 및 .3128 / 15% / 55% | **0.33492 / 0.1801 / 0.6025**, subset 재계산 **0.3128 / 15/100 / 55/100** | `generation_val161_b2.metrics.json` + jsonl |
| **A1 native matched val100** | .6552 / 100% / 100% | **0.6552 / 100/100 / 100/100**, preservation **0.4446** | `pilot300_val161/predictions.jsonl` × `splits.json` 앞 100 ID 독립 재계산 |
| A1 val161 | .6576 | **0.65758** | 동일 |
| ".6506 (같은 val 앞 100건)" | .6506 | **0.6506 재현** — 정체 확인: **예측 파일(id 정렬) 순서의 앞 100행**(`splits.val` 순서 앞 100과 **다른 부분집합**) | 동일 파일, 파일 순서로 재계산 |
| bridge val100 = splits.val 앞 100 | (암묵) | **jsonl ID 순서 == splits.val 앞 100 일치 확인** | 양측 jsonl |
| teacher train100 | F1 .6697 / grounded 99/100 / EOS 100 | **0.66968 / 0.99 / 1.0** | `teacher_train100.metrics.json` |
| ss-slot 학습 val CE / 설정 | 2.2985→2.2406, ss_prob .2, slot-aware | **2.29847→2.24062, 0.2, True** | `b2_layer12_300_ss_slot_metrics.json` |
| layer sweep cosine (layer9 최고 .7910) | .7604/.7798/.7910 등 전체 표 | **5개 pretest json 전부 일치** (layer9 .79102 최고, concat .74496 최저) | `layer{6,9,12}_pretest.json`, `concat_pretest.json` |
| D-083 1,940 ckpt | F1 .6823 / grounded 158/161 / EOS 161 | **0.68228 / 0.9814 / 1.0, new slot 4개/161 문서** | `full_2ep/eval_step_1940/eval.metrics.json` |
| D-093 drop-new fallback | 71/161 | **71 재현** (jsonl strategy 카운트) | `slot_repair_val161.jsonl` |

문서의 헤드라인 수치는 **하나도 틀리지 않았다.** 재현성·provenance는 우수하다.

### 1.2 코드 검토에서 확인한 사실 (문서 서술과 다른 부분 포함)

1. **`grounded`의 실제 정의는 "신규 slot 없음"뿐이다.** 모든 runner에서
   `grounded = not rep.new` (`c5_b1d_generate.py:147`, `c5_a2null_eval.py:158`, `c5_a1_eval_batch.py:79`,
   `c5_a1_lora.py:375`, `c5_b2_slot_repair.py` 동일). `slot_verify.rejected = bool(missing or new)`는
   **어디에서도 사용되지 않는다.** 요청서 §2.3의 정의("source slot 보존 + 신규 slot 없음")와 불일치.
   증거: drop-new repair가 `missing_count` 1,063(증가)인데도 `grounded 1.0`.
2. **SS 구현의 세부:** (a) corruption에 쓰는 student argmax는 **gold prefix 전체를 본 teacher-forced pass**에서
   얻은 것(`ce_scheduled`의 첫 forward)으로, 스스로 굴리는 rolling trajectory가 아님 → 복합 오류를 과소모사.
   (b) `labels_and_slot_mask`의 `protect[-1] = True` 주석 "# EOS"는 실제로는 **마지막 content token** 보호이고,
   EOS는 decoder input에 등장하지 않으므로 "EOS corruption 금지"는 **구현상 무의미(no-op)**다
   (`ce_scheduled`에서 `protect`에 append한 True는 적용 슬라이스 `[:n-1]` 밖).
   (c) slot 보호는 slot/숫자 token 자체만 보호하고 **주변 문맥은 보호하지 않음** — 문서 해석 (b)와 일치.
3. **디코딩 공정성:** A1과 bridge 모두 greedy(`num_beams=1, do_sample=False`), `max_new=448`로 동일. 공정.
4. **D-095가 사실상 병목의 위치를 이미 밝혔다:** teacher hidden 투입 시 teacher-forced CE **0.5837/87.51%** vs
   adapter real **2.7705/43.58%**. 디코더는 좋은 입력에서 잘 동작하고, adapter 출력(최고 cosine .79)은
   토큰 정확도 59.58%(layer9)까지밖에 못 올린다. CE 격차 3~5배는 MLP adapter로 메울 수 있는 크기가 아니다.

### 1.3 통계 검증 (내 계산 — 단일 seed/single run 쌍, paired bootstrap 20,000회 + McNemar exact)

| 비교 (val100 paired) | ΔF1 | 95% CI | 유의? | grounded 변화 | McNemar p |
|---|---:|---|---|---|---:|
| layer12 → ss-slot | **+0.0610** | [+0.0292, +0.0929] | 예 | 21→12 (+7/−16) | 0.093 |
| layer12 → ss | +0.0319 | [−0.0033, +0.0670] | 아니오 | 21→10 (+6/−17) | **0.0347** |
| ss → ss-slot | +0.0291 | [−0.0026, +0.0608] | 아니오 | 10→12 (+7/−5) | 0.774 |
| layer12 → layer9 | −0.0124 | [−0.0497, +0.0245] | 아니오 | 21→22 (+15/−14) | 1.000 |
| **A1 native → ss-slot** | **−0.2478** | [−0.2773, −0.2192] | **예** | 100→12 (88/100 동방향) | ≈0 |

문서별 발명 slot 수(내 계산): layer12 평균 **3.22개/문서**(79/100 문서), ss **5.94**(90/100),
ss-slot **4.80**(88/100). ΔF1과 Δnew-slot의 상관은 r ≈ −0.02~−0.03로 사실상 없다.

---

## 2. Q1~Q12 판정

형식: **verdict / evidence / next steps**.

### Q1. Bridge 전제 — STOP이 타당한가, NARROW로 갈 단일 반증 실험이 있는가

**verdict: agree (STOP).** 단일 반증 실험 존재 여부: **없음** (§0 참조).

**evidence:** §1.1·§1.3 전부. 특히 (i) 동일 ID·동일 디코딩 파라미터 비교에서 ΔF1 CI가 0을 크게 벗어나고,
grounded는 88/100 문서가 전부 A1 우위 방향; (ii) grounded-100 강제 시 F1 상한 0.3203 = A1의 49%;
(iii) D-095 표현 격차(teacher-hidden CE 0.5837 vs adapter 2.7705)가 adapter 측에서 메울 수 없는 상한을 만든다;
(iv) 제품 gate grounded ≥ 0.99 vs bridge 0.12 — 이 격차는 SS/feature/data 어느 축으로도 메운 전례가 이 문서에 없다.

**next steps:**
1. bridge를 "탐색 종료(품질 격차)"로 공식 기록하되, 종료 사유에 §0의 attribution 귀속 문장을 추가.
2. 무훈련 attribution control(§4 E1)을 post-mortem으로 1회 실행(선택, ≤30분).
3. bridge 재개 논의가 필요해지면 먼저 **EG2 재사용의 serving-cost 이득을 수치화**하는 문서를 요구
   (현재 요청서 어디에도 비용 동기가 정량화되어 있지 않다 — NARROW/CONTINUE 판단의 결측 변수).

### Q2. 종료 판정은 사후 합리화가 아닌가 / DoD가 부적절했는가

**verdict: agree (사전 등록 유효).** DoD 자체는 "합리적이지만 근거 미문서화 + 잡음 미고려".

**evidence:** git 검증 — `adc08f2`에서 DoD 표 존재, 결과 섹션 전부 "진행 중/pending"; 결과는 `ee084af`.
grounded ≥ 20%는 "SS가 grounded를 잃지 않을 것"(직전 layer12 21%)이라는 무회귀 조건으로 타당했고,
실제 12%로 실패했다. 반면 (i) 임계값 산출 근거(왜 0.36/20/58인지)가 어디에도 없고,
(ii) DoD가 **단일 seed n=100 단일 실행** 값으로 평가됐다. 내 분석에서 ss→ss-slot의 grounded 차이(10→12)는
p=0.77로 노이즈지만, DoD 평가 자체(12 < 20)는 등록된 대로 유효하다. 종료 판정에 영향 없음.

**next steps:**
1. 향후 DoD에는 (a) 산출 근거, (b) 단일 실행 vs 다중 seed, (c) CI 포함 평가 방법을 명시.
2. 이번 판정은 그대로 유지(사후 변경 금지 준수). DoD를 소급 수정하지 말 것.
3. 종료 보고에 "grounded = 신규 slot 없음(보존 아님)"임을 명기(§ Q8).

### Q3. SS의 grounding 붕괴 — 실제 메커니즘인가, 측정/설계 artifact인가

**verdict: conditional.** **붕괴(21→10)는 실제**로 보인다(내 McNemar p=0.0347, 유일하게 유의한 grounded 변화).
그러나 **"slot-aware의 부분 회복(10→12)"은 유의하지 않다**(p=0.77) — mask 불충분 여부를 판단할 근거가 없다.

**evidence:**
- 메커니즘(실제): SS는 문서당 발명 slot 평균 3.22 → **5.94**로 늘리고(발명 문서 79→90), slot 보존율도
  0.251→0.362로 함께 올랐다. 즉 "더 길고 유창하게 쓰되 출처 대신 언어모델 사전 지식으로 slot을 채우는" 방향 전환이며,
  corruption으로부터의 회복(denoising) 학습이 LM prior 의존을 강화했다는 해석과 일치. 문서 해석 (a)+(b) 지지.
- ΔF1과 Δnew-slot의 상관 r≈0 → F1 이득은 slot과 무관한 내용 유창성 개선에서 나옴. F1 상승이 grounding 붕괴를
  "보상"하지 않음. metric gaming이라기보다 실제 행동 변화다(teacher F1도 0.339→0.370으로 상승).
- 설계 artifact 2건: (i) student argmax가 gold-context pass에서 나옴(복합 오류 과소모사),
  (ii) EOS 보호 no-op(§1.2). 둘 다 방향성을 바꿀 만큼 크지는 않다.

**next steps:**
1. 보고서에서 "slot-aware가 grounded를 10%→12%로 회복" 문구를 "유의 차이 없음(n=100)"으로 수정.
2. SS 재시도 시 rolling/true on-policy 방식(생성 prefix에 teacher 분포)으로 교체하고, EOS 보호 문구를 사실대로 정정.
3. 붕괴 메커니즘 확증이 필요하면 기존 jsonl로 발명 slot의 유형 분포(숫자/날짜/고유명사)를 오프라인 집계(무훈련).

### Q4. layer9 역설 — 300 overfit인가, feature-noise인가, teacher-forced 한계인가 / full 1,293 가치

**verdict: conditional — "역설"의 상당 부분은 표본 노이즈다.**

**evidence:** layer9 vs layer12 free-running ΔF1 = −0.0124, CI [−0.0497, +0.0245] — **유의 없음**, grounded p=1.0.
즉 layer9가 free-running에서 "더 나쁘다"는 주장 자체가 n=100 노이즈 범위다. teacher-forced 우위(1.8904/59.58% vs
2.1190/56.11%)와 free-running 동률의 조합은 "teacher-forced/cosine 지표가 free-running을 예측하지 못한다"는
문서 자신의 결론(그리고 자신이 인용한 Cosine Misleads r=−0.94)과 정합적이다. 300 overfit 설명은
train/val CE gap이 layer9에서 더 크다는 관측과 양립하지만, 이것만으로 인과 단정은 불가.

**next steps:**
1. 보고서에서 "layer9 free-running 악화"를 "동률(유의 차이 없음)"로 정정. feature 축은 layer9≈layer12로 결론.
2. layer9 full 1,293 단독 실행은 정보 가치가 낮다(§ Q5). 실행한다면 반증 번들(§4) 안에서만.
3. feature 선택 기준을 hidden cosine에서 "소형 probe의 free-running F1"으로 교체하는 프로토콜을 다음 트랙부터 적용.

### Q5. 데이터 규모 — 300문서로 결론 내려도 되는가 / full 재실행의 정보 가치

**verdict: agree (300으로 STOP 결론은 유효), 단 완전한 일반화는 아님.**

**evidence:** 같은 feature(final 768)에서 300 → 1,293 확장이 free-running을 거의 바꾸지 않았다
(.3341/18% → val161 .3349/18.01%; matched val100 .3128/15%). 데이터 4.3배가 F1/grounded를 움직이지 못했다는
것이 "bridge의 병목은 데이터가 아니다"의 직접 증거다. layer12/SS@1,293 미실측은 gap이지만,
그 상한 추정(300 결과 + 메커니즘)으로는 0.25 F1 + 8배 grounded 격차를 닫을 수 없다.

**next steps:**
1. layer12-SS@1,293은 NARROW 번들에서만(예상 ~3.5h CPU) — DoD: val161 F1 ≥ 0.40 AND grounded ≥ 20%,
   미달 시 즉시 종료.
2. 그 외의 목적(예: A1)으로 1,293 재실행은 불필요.
3. 실험 보고서에 "train subset = splits.train 순서 앞 300" 정의를 명기(재현성).

### Q6. slot repair 상한 .3203 — repair가 나쁜가, 생성 grounding이 병목인가 / replacement 가치

**verdict: conditional.** 상한 .3203은 **생성 단계 grounding이 근본 병목**이라는 증거이자,
동시에 repair가 **품질을 파괴하는 안전 필터**라는 증거다(원본 .4074 → drop-new .3159, F1의 23%가
발명 문장에서 나옴; 평균 3.27문서 중 2.12문서가 발명 포함). drop-new는 "신규 slot 없음"만 강제하고
missing은 방치(missing 1,063)임에 유의 — "grounded 100%"의 의미가 §2.3 정의보다 훨씬 약하다.

**next steps:**
1. slot **replacement**(발명 slot을 source의 대응 slot으로 치환) 1회 프로토타입 — DoD: grounded 100%에서
   F1 ≥ 0.38이면 "틀린 값, 맞는 자리" 가설 지지. 비용 ~1h(무훈련). 단, bridge 구제 여지는 .4074가 천장이라 작다.
2. repair의 실전 용도는 bridge가 아니라 **A1 full-train checkpoint**(1,940: 발명 slot이 161 문서에서 총 4개)다(§ Q9).
3. repair 결과를 "모델 출력"과 구분해 공개 규정(수정 사실 표기 + fallback 사용률 공개)을 문서화.

### Q7. slot auxiliary vs copy/pointer vs constrained decoding vs B2 full 1,293 — 우선순위·DoD

**verdict: conditional (bridge가 사실상 종결된 상태에서의 순위). 전제: EG2 재사용의 비용 동기가 먼저 정량화되어야 함.**

순위(가치/비용 순, 사전 확률은 내 주관 추정):

| 순위 | 수단 | 비용 | 사전 확률(DoD 통과) | DoD (val100, 동일 프로토콜) | 중단 조건 |
|---|---|---|---|---|---|
| 1 | **constrained decoding / verifier-guided re-ranking** (기존 ss-slot ckpt, 무훈련) | 구현 2–4h + 평가 0.5h | ~20% | grounded ≥ 99% **그리고** F1 ≥ 0.45 → 트랙 재개 심의; grounded ≥ 99% & F1 < 0.40 → decode-time 한정, bridge 종결 | 첫 평가에서 grounded < 99%면 즉시 중단 |
| 2 | **slot auxiliary head** (decoder 상태에서 target token의 source-slot 여부/유형 예측 다중과제) | ~35–60분 | ~15–20% | new-slot micro ≤ 0.20 **그리고** grounded ≥ 50% **그리고** F1 ≥ 0.38 | grounded < 25% 또는 F1 < 0.35 |
| 3 | **B2 layer12(+SS) full 1,293** | ~3.5h | ~10% | val161 F1 ≥ 0.40 AND grounded ≥ 20% | 미달 시 종료 |
| 4 | **copy/pointer mechanism** | 수일(구조 수술 + 재학습) | ~10% | 300 프로토타입 grounded ≥ 60% AND F1 ≥ 0.40 | 프로토타입 미달 시 폐기 |

copy/pointer 사전 확률이 낮은 이유: T5Gemma2는 merged attention으로 별도 cross-attn 파라미터가 없어
pointer 추가가 "frozen decoder" 전제를 깨고, 요청서가 인용한 T5 XA-only 문헌(13.7% params로 full 대비 −0.003)과
달리 이 문제는 **입력 표현 부족**(D-095)이어서 copy 경로만으로 해결되기 어렵다. 발명 slot micro 0.56–0.69는
모델이 source 접근 인센티브가 없다는 신호이기도 하지만, 근본 입력 품질 문제를 decode-time/side-path로
메우는 것의 상한이 낮다.

**evidence:** 위 표의 근거는 §1.2(merged attention, D-095), §1.3(유의성), D-097(데이터 확장 중립), Q6(repair 상한).

**next steps:** 위 표 그대로. 단 1–4 모두 "bridge 재개 승인"이 먼저다(자동 승인 아님).

### Q8. 평가 지표 — grounded의 의미, A1 100%의 의미, 결합 방법

**verdict: conditional — 지표는 혁신보다 문서 서술이 틀렸다.**

**evidence:**
- 실제 구현의 `grounded` = **신규 slot 없는 문서 비율**(anti-invention). `slot_verify.rejected`(missing 포함) 미사용.
  요청서 §2.3 정의("source slot 보존 + 신규 slot 없음")와 **불일치** — 문서 쪽을 고쳐야 한다(코드는 production 미수정 원칙 유지).
- 따라서 **A1의 grounded 100%는 "발명 0건"이라는 실질 품질이지만, source slot을 다 보존한다는 뜻이 아니다**
  (A1 preservation 0.4446 — 요약이 source slot을 ~56% 버리는 정상적 추상화). "teacher-copy artifact"는 아니다:
  copy rate 0.836(A0 0.992 대비)로 추상화 방향이며, 발명 slot 0/837은 검증된 사실.
- bridge grounded 12%는 "가혹한" 것이 아니다: 발명 slot 480/858(micro 0.559), 발명 문서 88/100.
  제품 gate(new-slot micro ≤ 0.01) 대비 56배.
- 결합 규칙 제안: 1차 gate = grounded(no-new) 문서율 ≥ 0.99 **그리고** new-slot micro ≤ 0.01;
  품질 판정 = 같은 ID에서 incumbent 대비 paired ΔF1 + CI; 진단 지표 = slot preservation, nonvacuous grounded
  (slot-free 문서 제외, A1은 6/161) 별도 보고.

**next steps:**
1. 모든 보고서의 "grounded"를 "grounded(no-new)"로 표기 통일 + §2.3 정의 수정.
2. bridge/A1 메트릭에 nonvacuous grounded와 slot-free 문서 수 추가.
3. gold 요약 자체의 preservation(내 환경에서 미측정 — clean jsonl 부재)을 1회 측정해 "보존 요구가 현실적인지" 확인.

### Q9. A1 native 제품 경로 — pilot300 고정이 타당한가 / 1,940·2,586 재평가 가치

**verdict: conditional — pilot300 고정은 안전하지만, 1,940 재평가는 명확한 가치가 있다.**

**evidence:** pilot300은 **300 step(≈300 문서 1 pass, train의 23%)** 학습한 경량 fallback으로 gate는 통과하지만
과소학습 상태다. 1,940 checkpoint는 paired ΔF1 **+0.0247, CI [+0.0120, +0.0373]** 로 유의하게 우수하고
EOS 161/161이며 발명 slot이 **총 4개(3문서)** 로 grounded 0.9814 — gate 0.99 미달은 불과 3문서 차이다.
여기에 drop-new repair(또는 수동 검토)를 적용하면 grounded 100% 복원이 거의 확실하고 F1 손실 상한도
극히 작다(영향 문서 ≤3). 2,586은 pilot300 대비 유의하지 않음(CI 0 포함).

**next steps:**
1. **무훈련 재평가**: 기존 `eval_step_1940/2586` val161 출력에 repair 필터 적용 → grounded/F1/EOS 재집계,
   paired CI로 pilot300과 비교. DoD: repair 후 grounded 1.0, F1 > 0.6576, EOS 1.0 → 제품 후보 승격 **제안서** 작성
   (승격 자체는 기존 승인 절차 필요 — 이 검토만으로 gate 변경 아님).
2. fallback(source 첫 문장) 사용률 감사 — A1에서는 3문서 이하 예상(B2는 71/161이었음).
3. 제품화 최소 검증은 §6 목록 준수(사람 50건 → test 163은 최종 후보 1회만).

### Q10. 비교 공정성 — selection bias와 필요한 matched control

**verdict: conditional — 헤드라인 비교(A1 vs bridge)는 공정하다. 위험은 부분집합 정의와 단일 seed다.**

**evidence:**
- A1 val100 재계산은 bridge와 **동일 ID(splits.val 앞 100), 동일 디코딩 파라미터** — 공정. 내 재계산도 일치(0.6552).
- ".6506"의 정체를 밝혔다: **예측 파일의 id-정렬 순서 앞 100행**(다른 부분집합) — 내 재현 0.6506.
  문서는 둘을 구분해 놓았지만 부분집합 정의를 artifact로 남기지 않아 혼란이 생겼다(§ Q12-3).
- teacher train100 = "길이 정렬 상위 100건"은 val100과 분포가 다른 비대표 훈련 집합 → teacher arm의
  모든 결론은 이 subset 정의에 의존(D-094/096/097). 코드/아티팩트 기준이 요청서에 문서화되지 않음.
- A1이 val 첫 5건으로 튜닝된 사실은 공개됐고 156건 subset에서도 0.6586으로 안정 — 허용 가능한 수준의 공개된 편향.
- bridge 측 가장 큰 취약점은 subset이 아니라 **단일 seed n=100 무-CI**(§1.3)다.

**next steps:**
1. 모든 "앞 N건" 수치에 부분집합 정의(split 순서 vs id 정렬)를 명기하고, 재계산 스크립트/아티팩트를 남길 것.
2. teacher train100 선택 기준의 코드 참조를 요청서 §9.1에 추가.
3. 향후 결정적 비교에는 seed 3회 또는 paired CI를 의무화.

### Q11. 연구 중단 기준 — bridge 중단 조건 / A1 제품화 검증

**verdict: agree + 보완.**

**evidence:** 사전 등록 DoD 실패로의 종료는 이미 올바르게 실행됐다(Q2). 재개 조건은 §0/§ Q1대로
(i) 비용 동기 정량화 + (ii) E1 attribution 결과에서만 열려야 한다.

**next steps:**
1. bridge 재개 시 한도: **실험 2개 이하, 총 ≤ 8 CPU-hours, val100 1회 평가씩**, 각 실험 DoD·중단 조건 사전 등록,
   2개 모두 미달 시 **최종 종료**(재심의 없음).
2. A1 제품화 최소 검증(§6 참조): repair 재평가 → 사람 50건 → test 163 최종 1회(별도 승인) — 이 순서.
3. 운영 모니터링: 발명 slot률/보존율/EOS율 샘플링 대시보드 + repair 개입률(점점 커지면 모델 교체 신호).

### Q12. Must-fix (우선순위 3)

1. **[High] `grounded` 지표 정의·문서 불일치.** 구현은 no-new-only인데 §2.3은 "보존+no-new"로 서술.
   repair "grounded 100%"는 missing 1,063을 방치한 결과다. → 모든 문서 표기 통일, preservation/nonvacuous 병기,
   repair의 의미 명시. (영향: A1 포함 모든 grounded 수치의 해석)
2. **[High] 단일 seed n=100 무-불확실성 보고.** layer9 "역설"과 slot-aware "회복"은 내 CI에서 유의하지 않은데
   결정 근거로 서술됐다. → paired bootstrap CI + McNemar를 결과 표 표준으로, 핵심 주장은 seed 반복.
3. **[Medium] 부분집합 정의의 provenance 부재 + SS 구현/문서 불일치.** ".6506 vs .6552"의 정체(id-정렬 파일 순서)
   기록 없음. SS의 EOS 보호는 no-op이고 argmax는 gold-context pass 기반인데 문서는 "EOS corruption 금지"로 서술.
   → subset 정의 문서화 + SS 문구 정정(또는 코드 주석·동작 정정, 단 production slot_verify는 건드리지 말 것).

---

## 3. 이슈 표

| # | severity | issue | evidence | fix |
|---|---|---|---|---|
| 1 | High | `grounded` = no-new-only로 구현됐으나 문서는 "보존+no-new"로 서술 | §1.2-1, `c5_b1d_generate.py:147` 등 전 runner, repair missing 1,063 | 문서 정의 수정 + 지표명 통일 + preservation 병기 |
| 2 | High | 단일 seed n=100, CI/McNemar 없음 — 노이즈를 결론으로 서술 | §1.3: layer9 ΔF1 CI 0 포함, ss→ss-slot p=0.77 | paired bootstrap+McNemar 표준화, 핵심 주장 seed 3회 |
| 3 | Medium | SS EOS 보호 no-op / argmax가 gold-context pass 기반 | §1.2-2 코드 분석 | 문구 정정, rolling SS 또는 on-policy KD로 교체 검토 |
| 4 | Medium | 부분집합 정의 provenance 부재(.6506 vs .6552) | §1.1 재현, § Q10 | subset 정의를 artifact·문서에 기록 |
| 5 | Medium | hidden-cosine을 feature 선택 기준으로 사용 — 자기 반증 보유 | layer9 free-running 동률 + 자기 인용(Cosine Misleads) | probe free-running F1 기준으로 교체 |
| 6 | Medium | bridge 재개/종결 판단의 결측 변수: EG2 재사용 비용 이득 미정량 | 요청서 전체에 비용 근거 없음 | 비용 모델 문서화 후 재개 여부 판단 |
| 7 | Low | gen_len 단위 불일치(토큰 vs 문자) | ss-slot 286.41(토큰) vs repair json 396.73(문자) | 단위 표기 통일 |
| 8 | Low | vacuous grounded(slot-free 문서) 미보고 | A1 6/161만 공개, bridge 미보고(내 계산: layer12 4, ss 1, ss-slot 3) | nonvacuous grounded 병기 |

---

## 4. 다음 실험 (최대 2개)

### E1. Teacher-hidden free-running attribution control (무훈련, bridge post-mortem)

- **내용:** B2 ss-slot checkpoint(decoder LoRA 포함)에 A1 native encoder의 hidden states를
  `encoder_outputs`로 넣고 val100 greedy 생성(기존 `c5_b1d_generate.py` 경로 재사용, teacher cache 존재).
  D-095의 teacher-forced(0.5837/87.51%)가 free-running에서 무엇이 되는지 측정.
- **DoD:** 100문서 완주 + A1/layer12/ss-slot과의 paired 비교표(CI 포함) 작성.
- **판정 규칙(사전 등록 권고):** F1 ≥ 0.60 & grounded ≥ 90% → 병목 = EG2/adapter 표현 (STOP 메커니즘 확정).
  F1 < 0.40 (CE 0.5837에도) → 병목 = decoder free-running → on-policy KD만이 유일한 잔여 가설(NARROW 심의 조건).
  그 외 → 혼합, STOP 유지.
- **예상 시간:** 구현 포함 ≤ 1h, 실행 ~25분 (CPU).
- **중단 조건:** 없음(훈련 없음). 단, 어떤 결과도 이것만으로 bridge 재개를 승인하지 않는다.

### E2. A1 1,940/2,586 checkpoint repair-filter 재평가 (무훈련, 제품 경로 — bridge와 별개)

- **내용:** 기존 `full_2ep/eval_step_{1940,2586}` val161 출력에 `c5_b2_slot_repair`의 drop-new 필터를 적용해
  grounded/F1/EOS/fallback률 재집계, pilot300과 paired 비교.
- **DoD:** repair 후 grounded 1.0 **그리고** F1 > 0.6576(pilot300) **그리고** EOS 1.0 **그리고**
  fallback ≤ 5/161 → 제품 후보 승격 제안서 작성(승인 절차는 별도; 이 검토는 gate 변경이 아님).
- **예상 시간:** ≤ 30분(생성 재실행 불요, 출력 이미 존재).
- **중단 조건:** F1 손실 > 0.01 또는 fallback > 5/161 → pilot300 유지.

*(참고: bridge를 별도로 재개할 경우의 첫 실험은 § Q7 순위 1(constrained decoding)이며, DoD·중단 조건은 해당 표를 따른다.
이는 E1 결과가 decoder-side 병목을 시사하고 비용 동기가 정량화된 경우에만 열린다.)*

---

## 5. 문서 수치·비교의 오류/누락

1. **§2.3 `grounded` 정의 vs 구현 불일치**(가장 중요) — §3 이슈 #1.
2. **§2.4 ".6506"의 부분집합 정의 누락** — id-정렬 예측 파일 순서 앞 100(재현 확인). split 순서 앞 100(=.6552, bridge ID)과 다름.
3. **§5.3/§5.4 gen_len 단위 혼용** — generation metrics는 토큰(286.41), slot_repair json은 문자(396.73). 같은 필드명.
4. **§5.4 preservation 열의 의미** — .1621은 drop-new **후** 값이고 원본은 .3656(§5.3)임에도 열 이름이 동일해 혼동 소지.
5. **"slot-aware가 grounded 10→12% 회복" 해석** — 유의하지 않음(p=0.77). "회복" 표현 과잉.
6. **"layer9 free-running 악화(F1 −0.0124)" 해석** — 유의하지 않음(CI 0 포함). "악화" 표현 과잉.
7. D-096/D-097/D-098 등 val20 스크린 수치는 내가 미검증(artifact 존재 확인만). 헤드라인 결론과 무관.
8. 그 외 헤드라인 수치(§1.1 표)는 **전수 일치** — 오류 없음.

---

## 6. bridge 계속 시 최대 허용 비용 / A1 제품화 최소 검증

- **bridge 최대 허용 비용(재개 승인 시):** 실험 2개 이하, 총 8 CPU-hours, 신규 데이터 없음, val100 평가 각 1회.
  사전 등록 DoD 미달 2회 누적 시 최종 종료.
- **A1 제품화 최소 검증:** (1) E2 repair 재평가 통과, (2) 사람 50건 검토(아직 미실행 — 기존 rating sheet 활용),
  (3) robustness 점검(slot-free 문서, 극단 길이, 프롬프트 민감도), (4) test 163은 **최종 후보 확정 후 1회만**(기존 규칙),
  (5) 배포 시 repair/안전 필터의 개입률 모니터링.

## 7. 본 검토의 한계

- 모델 체크포인트/캐시는 로컬에 없어 **훈련·추론 재실행은 일절 없었고**, 모든 수치는 커밋된 artifact와
  예측 jsonl의 재계산으로 검증했다. clean 데이터셋 본체(`data/external/f5_pairs_v3_clean.jsonl`)가 워크스페이스에
  없어 gold 요약의 slot preservation은 직접 측정하지 못했다.
- 통계 검증은 단일 seed 단일 실행 쌍에 대한 재표본 기반 CI로, 실행 간 변동(seed variance)은 포함하지 않는다.
- P1 데이터, test 163, 다른 모델의 리뷰는 일절 참조하지 않았다.

---

*이 보고서는 P0 데이터와 비밀값 없이, 요청된 파일 1개만 작성되었다. test 163은 봉인 상태로 유지된다.*