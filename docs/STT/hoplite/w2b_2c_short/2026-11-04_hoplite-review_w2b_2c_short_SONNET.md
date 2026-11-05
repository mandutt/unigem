# W2B + 2C-short 독립 검토 — SONNET (w2b_2c_short)

- 검토일: 2026-11-04 / 검토자: SONNET (단독 수행, 서브에이전트·외부 LLM 미사용)
- 동기화: `git fetch origin` OK, `git pull --ff-only origin main` → "Already up to date". HEAD = `81d58ed34f13b06d2f13edd49d89a37a80323d0f` (요청서의 기준 커밋 `6b1d720`보다 앞섬)
- 읽은 자료: `docs/STT/reports/EXTERNAL_REVIEW_W2B_2C_SHORT_2026-11-04.md` 전체 368줄(1–368). `docs/STT/plans/plan_wave2b_2c_short.md`와 `docs/STT/reports/W2A_lite_results.md`는 일부 grep만 했다. `docs/STT/reports/W2A_lite_cp_d2_lite.md`는 읽지 않았고 요청서에 인용된 수치만 사용했다.
- 코드·체크포인트·데이터는 열어보지 않았다. 표본 구성, 처리 속도 같은 실측 사실은 아래 UNVERIFIED로 표시했다.

## 1. 권장 결론

**A (4h short, 4-arm)를 채택하되, 아래 세 가지를 고치고 단계 게이팅으로 실행하라.**

- B는 채택하지 않는다. B3를 생략하라는 안인데, B3는 캐시된 feature 위에서 reader만 학습하는 가장 싼 arm이다. 이 arm을 빼면 "데이터 효과"를 귀속할 수 없다.
- 순서는 B0′(재학습) → B3 → B2 → B1(조건부)로 한다.
- 이유는 아래 Q1에 쓴다.
- E는 pilot에는 불필요하다. 다만 최종 주장은 "Kspon in-domain, 화자 중복 가능"으로 한정해야 한다(Q3).

## 2. Q1–Q8

**Q1 (arm 설계).**
- 2×2 factorial 구조(LoRA × short data)는 타당하다. B2−B3는 데이터가 있을 때의 LoRA 효과이고, B2−B1은 LoRA가 있을 때의 데이터 효과다.
- 단, B2 > B1 AND B2 > B3를 동시에 요구하면 짧은 발화 분포 보정만 효과가 있고 LoRA는 효과가 없는 경우(B3≈B2)에 No-Go가 된다. 그 결과는 "LoRA 불필요, 데이터가 답"이라는 유효한 발견인데도 실패로 처리된다. gate를 "B2 > B0"(결합 효과)와 "분해 기여도 보고"로 나눠라.
- B3는 비용이 거의 없다(reader-only 학습). 반면 B1은 LoRA arm 중 가장 비싸고, 중요한 질문(short 데이터가 효과가 있는가)에는 가장 덜 답한다. 그러니 B3를 생략하지 말고 B1을 조건부(B2가 B3를 이길 때만)로 돌려라.
- 더 큰 confounder가 있다. short 4h는 **짧음**과 **Kspon 도메인 in-domain 데이터**를 함께 바꾼다. 기존 6h의 구성(FLEURS 비중 등)은 UNVERIFIED다. CP-D2의 train 0–2초 4클립은 6h가 Kspon 중심이 아닐 수 있음을 시사한다.
- 그러면 B3의 이득이 "짧은 발화 효과"인지 "Kspon 도메인 노출"인지 구분되지 않는다. 길이 분포를 자연 분포로 둔 Kspon 4h control(B3-nat)을 하나 추가하는 것이 가장 깨끗하다. 비용은 reader-only 한 run이다.

**Q2 (short 데이터 규모·분포).**
- 4h로 시작하는 것은 타당하다. 비용 대부분은 zip 확보와 선별이라 2h로 줄여도 절감이 작다.
- sampler 우려는 과장됐다. 산술상 ≤4초는 6h에서 약 0.25h, short에서 약 2.4h(60%)이므로 합쳐서 약 2.65h/10h ≈ 26.5%다. 40%로 올리는 것은 짧은 클립을 약 1.5–1.6배 가중하는 수준이다. 이 정도는 심한 과적합이 아니고, epoch마다 노출이 약 1.5배라는 뜻이다.
- 오히려 부족한 쪽은 test 분포 일치다. 0–2초는 natural 약 10%, effective 약 15%인데 test는 27.6%다. 8–16초는 30%인데 test는 약 15%다.
- 0–2초가 test에서 CER 46.4%로 가장 나쁘고 비중도 크다. 0–2초를 25%로 두고 ≥0.5초만 허용하면 선택 편향이 생긴다. 이는 반대 방향 편향이다(test의 0.5초 미만은 feature 추출에서 이미 제외되어 평가 대상이 아님. 요청서 2.2).
- 이 편향을 막으려면 0.5초 컷오프와 CTC frame 하한(프레임 수 ≥ 전사 글자 수 + 반복 글자 수)을 pre-register하고, 각 컷오프에 걸려 탈락한 클립 비율을 test와 train에서 같이 보고하라.
- 같은 화자가 짧은 발화를 많이 갖는 경우를 위한 화자당 10% 상한은 좋다.
- 한국어 Kspon의 감탄사·필러가 짧은 발화에 몰려 있을 가능성이 있다(UNVERIFIED). 전사 정리가 짧은 클립에서 더 많은 비중을 지우는지 확인하라.

**Q3 (test 타당성).**
- eval_clean 2,900은 train과 ID·화자가 분리된다면 유효한 held-out test다. 하지만 "독립 test"는 아니다.
- eval_other와 같은 코퍼스·같은 60명 화자라면 화자·녹음 환경이 공유된다. 설계 결정(길이 분포 조정 목표)을 eval_other 분포 분석에서 끌어냈으므로, 이 test는 사실상 "그 분포로 튜닝한 in-distribution test"다.
- 따라서 주장은 "Kspon 평가 화자군에서의 개선"으로 제한하고 일반화 주장은 FLEURS dev(no-regression guard)로만 한다.
- 더 큰 문제는 dev 100이다. 같은 100발화가 D-β와 early stopping(patience 3), pilot/full gate에 모두 쓰이고, 거기서 ≤4초 bin은 약 50개 안팎(UNVERIFIED: eval_other 비율로 추정)이다. 선택 편향이 크다.
- 새 P0 holdout은 pilot에는 필수가 아니다. 단 full 단계 최종 선언 전에 가능하면 확보하라(UNVERIFIED: 비용). FLEURS test 재사용 금지는 맞다.
- 2,900은 test로 쓰면 되지만, **dev를 키워야 한다**. 2,900 중 약 500을 화자 층화로 dev로 옮기고, test는 약 2,400으로 줄여라(Must-fix 1).

**Q4 (모델·LoRA).**
- 10–11층 LoRA r8은 합리적인 첫 시도지만 근거는 plan의 주장("가장 비용 효율적", plan 92행)뿐이다. 비교 실험은 없으므로 UNVERIFIED다. 최소 범위로 시작하는 것은 옳지만 층·모듈 ablation은 이번 라운드에서 하지 마라.
- 중요한 효율 이점이 있다. LoRA가 10–11층에만 있다면 0–9층 출력은 고정이다. 그 은닉상태를 한 번 캐시하면 B1/B2는 2개 층만 forward/backward 하면 된다.
- 규모는 대략 1024 dim × 25 tok/s × fp16 ≈ 51 KB/s이므로 10h에 약 1.8GB다(추정). F-C-concat이 쓰는 4개 층이 10–11층 이전을 포함하면 해당 층 출력도 따로 캐시한다. 이 캐시 여부를 plan은 명시하지 않는다(UNVERIFIED).
- 캐시하면 SpecAugment 계열 on-the-fly 증강은 못 쓴다. 증강을 쓰고 있었다면 B0/B3와 파리티를 맞춰야 한다.
- 입력은 F-C-concat(4096)을 유지하라. 2A에서 가장 좋았고 seed 재현됐다. 단 concat 입력에 LoRA 층 출력이 들어가므로 층 간 스케일 정합을 확인하라.
- wordpiece head 제외는 타당하다. 변수를 늘리지 않는다.

**Q5 (gate).**
- dev 100에서 CI는 의미가 약하다. 100발화 CER의 bootstrap CI는 넓고, ≤4초 bin은 n이 더 작다. "가능한 경우"는 사후 해석 여지를 준다.
- 2A에서 FLEURS dev 192의 CI는 [+0.631, +2.028]pp, 효과 1.32pp였다. 효과가 상대 6%인데 CI가 이 정도로 넓었다.
- 필수 조치는 세 가지다.
  - dev를 약 500으로 키운다(Q3).
  - 문장 단위가 아니라 화자 클러스터 bootstrap을 쓴다.
  - 최소 seed 2개를 쓴다. 2A에서 seed 간 차이는 0.1pp 안팎이었지만(0.20913 vs 0.208116), LoRA arm에서는 분산이 더 클 수 있다(UNVERIFIED).
- 10% 상대 개선은 현실성이 있다. 35% CER에서 10%는 약 3.5pp이고, 짧은 발화에 train이 거의 없었던(≤4초 4.1%) 상황에서 데이터 보정만으로 가능한 크기다. 다만 "달성하지 못하면 No-Go"가 아니라 상대 개선과 절대 CER, CI를 함께 pre-register하고 하한 기준을 쓰는 게 낫다.
- 960h 9.0%와의 비교는 무의미하다(요청서도 직접 비교 불가라고 인정).
- pilot 5%/8% 기준은 pilot이 3 epoch인 점(plan 222행)을 고려하면 수렴 전 비교다. B0는 2A에서 epoch 16–20에 best였다. 12 epoch full에서도 같은 수렴 속도 차이로 불공정할 수 있다.
- 주지표는 상대 개선이 아니라 CER의 절대 pp 차이와 CI로 하고, 상대 개선은 보조로 보고하라.
- FLEURS dev에 대한 no-regression gate(예: 절대 +1.0pp 이상 악화 없음)를 추가하라. short Kspon 데이터가 FLEURS를 해칠 수 있다.

**Q6 (누락된 confounder).** 다음이 빠져 있다.
1. **B0 기준선 정의.** 2A의 frozen seed42 체크포인트(`w2a_fc_concat_s42.best.pt`)를 B0로 쓰면 sampler, epoch 수, 데이터 순서가 다른 arm과 일치하지 않는다. B0는 B3와 동일한 학습 코드·sampler·epoch로 재학습해야 한다. 6h-only arm(B0, B1)에 LengthBalancedSampler를 켜면 ≤4초 97클립을 약 10배 복제하게 되어 B1이 불리해진다. 6h-only arm의 sampler 정책(natural 또는 같은 가중)을 먼저 정하고 문서화하라.
2. **feature 파리티.** B3/B0은 캐시된 feature, B1/B2는 on-the-fly 경로다. LoRA B=0 초기값에서 on-the-fly 출력이 캐시와 수치적으로 일치하는지(허용오차 이내) 테스트를 pre-registered 항목으로 넣어라.
3. **short의 도메인 교란**(Q1 참조).
4. **CTC frame 제약.** 0–2초는 25 tok/s에서 12–50 프레임이다. 한국어 음절 전사의 글자 수가 반복 글자 때문에 프레임 수에 근접하면 CTC가 불안정하다. 클립 선택 시 필터와 탈락률을 보고하라.
5. **test 커버리지.** eval_other는 2,962/3,000만 평가됐고(16초 초과, 짧은 발화 제외), 새 test도 같은 필터가 걸린다. 탈락 목록을 manifest에 남겨 비교 가능성을 확보하라.
6. **재현성.** CPU 6스레드 비결정성, seed 분리(LoRA init, 데이터 순서, dropout)와 resume 시 RNG 복원 확인.

**Q7 (비용·현실성).**
- 10h × 12 epoch를 6스레드에서 3–5일에 끝낸다는 가정은 plan 95행이 스스로 "가정, pilot에서 실측"이라고 인정한다. 근거가 없으므로 UNVERIFIED다.
- arm이 3개(B1, B2, B3)이고 한 머신 6코어에서 동시에 못 돌리니 순차 실행이다. 실측 sec/step 없이 일정(7–10일)을 승인하지 마라.
- 대응책은 둘이다. 하위 0–9층 출력을 캐시해 forward 비용을 없앤다(Q4). B3는 reader-only라 매우 싸다. 둘을 합치면 가장 비싼 run도 2개 층 + reader 비용으로 줄어든다. 이 경우 일정이 실제로 크게 줄 수 있다(추정, UNVERIFIED).
- 디스크는 zip 전체를 풀지 않는 쪽이 낫다. `zipfile`로 필요한 클립만 스트리밍 추출하고 zip은 선별 직후 삭제하면 25GB 확보가 필수는 아닐 수 있다. 단 zip 자체(14–15GB)가 19GB 여유에 들어가는지는 확인이 필요하다(zip 한 개씩 받으면 해결).
- 2h pilot만 따로 하는 것은 권하지 않는다. 데이터 선별은 4h로 한 번에 하고, 학습만 단계화(B3 → B2 → B1)하는 편이 더 싸다.

**Q8 (종합).**
- A를 수정해서 채택한다(위 1절).
- 대안별 판단은 다음과 같다.
  - B: B3 생략이 문제다.
  - C: 데이터 분포 불일치가 주원인이라는 CP-D2 결과를 무시한다. LoRA만으로 짧은 발화 부족을 메우기 어렵다.
  - D: 데이터만 먼저 하는 것은 유일하게 싼 경로이므로 실제로는 B3에서 B2 순으로 하는 단계화가 D를 포함한다.
  - E: pilot에는 과하다.
- 필수 수정은 Must-fix 1–3에 있다.

## 3. Must-fix (시작 전)

1. **평가 프로토콜 재설계.**
   - 2,900 중 약 500을 화자 층화로 dev에 옮긴다(early stop과 gate는 이 dev로, 기존 100은 폐기 또는 보조).
   - test는 약 2,400으로 줄이고 manifest SHA를 사전에 고정한다. gate(절대 pp, 상대 %, CI 종류)를 실행 전에 확정한다.
   - 화자 클러스터 bootstrap과 seed 2개 이상을 요구하고, FLEURS dev no-regression gate를 추가한다.
2. **arm 파리티와 B0 재학습.**
   - B0를 B3와 동일 코드·sampler·epoch·seed로 재학습한다. 2A 체크포인트는 참고로만 쓴다.
   - 6h-only arm의 sampler 정책을 명시한다.
   - on-the-fly(LoRA B=0)와 캐시 feature 사이 수치 파리티 테스트를 추가한다.
   - Kspon 도메인 control(B3-nat)을 한 arm 추가한다.
   - gate는 "B2 > B0(결합)"으로 두고 B2>B1, B2>B3는 분해 보고로 바꾼다.
3. **계산 실측과 캐시 우선.**
   - 일정 승인 전에 sec/step과 RSS를 실측한다. 0–9층 은닉상태 캐시 설계(및 증강 유무)를 확정한다.
   - 단계 실행은 B0′ → B3 → B2 → B1(조건부) 순서로 한다. B3 vs B0′에서 데이터 효과가 없으면 B2/B1은 보류한다.
   - CTC frame 필터와 탈락률을 사전 보고한다.

## 4. Optional

- 층 8–11 또는 attention-only LoRA ablation(다음 라운드).
- 공백 포함 CER과 WER 보고(요청서 7.1에서 미산출 인정).
- 새 P0 holdout 확보는 full 최종 선언 직전 단계에서 고려한다.
- 0–2초 비중을 test(27.6%)에 맞추는 변형(예: 0–2초 30%)은 하나의 추가 arm 대신 sampler 가중 sensitivity로 보고한다.
- 16초 상한과 padding/silence trimming이 arm 간 동일한지 로그에 남긴다.

## 5. 잘못된 전제 / 검증 필요

- "dev 100은 test가 아니므로 재사용 가능" — 틀리지 않지만 early stop과 gate를 동시에 맡기면 편향이 생긴다. 실제 비율은 UNVERIFIED다.
- "eval_clean은 독립 test" — 같은 코퍼스·60명 화자이므로 제한적이다(요청서도 인정). 화자 중복 여부는 UNVERIFIED다.
- "2,900 test로 test 재사용 편향을 피한다" — 설계 분포가 eval_other 분석에서 나왔으므로 분포 튜닝 편향은 남는다.
- "B3가 data-only control" — 데이터 효과가 아니라 Kspon 도메인 + short 효과다(Q1).
- "6h 기준선 B0 = 2A frozen" — 학습 조건이 달라 불공정할 수 있다.
- "sampler 40%가 과적합 위험" — 산술상 natural 약 26.5%에서 1.5배 정도의 가중이다(수치 직접 계산).
- 10h·12 epoch·3–5일 — plan이 가정이라고 명시. 실측 없음.
- 6h의 구성(source)과 Kspon 비율: UNVERIFIED.
- 요청서의 "기준 커밋 6b1d720"과 현재 HEAD(81d58ed)가 다르다. 그 사이 변경은 확인하지 않았다.

## 6. 신뢰도

**medium.** 구조와 평가 설계 비판은 요청서 내용만으로 높은 확신이 있다. 반면 계산량, 6h 구성, 화자 중복 같은 실측 사실은 확인하지 못해서 일정과 효과 크기에 대한 판단은 중간 수준이다.

## 7. Q1–Q8 요약 판정

| Q | 판정 |
|---|---|
| Q1 | factorial 유효. B3 유지(가장 싸다). B1은 조건부. B2>B1&B3 동시 요구는 완화. 도메인 control(B3-nat) 추가 |
| Q2 | 4h 적절. sampler는 약 1.5배 가중이라 과적합 우려는 작음. 0–2초와 8–16초 비중은 test와 여전히 불일치. 필터와 탈락률 보고 |
| Q3 | 2,900은 유효하나 독립 test 아님. dev 100은 부족, dev를 약 500으로 확대. 새 holdout은 full 직전에 고려. FLEURS test 금지 유지 |
| Q4 | 10–11층 r8 OK(근거는 plan의 주장뿐). 0–9층 캐시로 비용 절감. F-C-concat 유지. wordpiece 제외 OK |
| Q5 | dev 100 CI는 약함. 화자 클러스터 bootstrap, seed 2개, 절대 pp 주지표, FLEURS no-regression 추가. 10%는 현실성 있으나 사전 등록 필요 |
| Q6 | B0 재학습·파리티·short=in-domain 교란·CTC frame·커버리지·재현성이 누락 |
| Q7 | 3–5일은 근거 없음(plan도 가정). 실측 후 일정 승인. 캐시와 B3 우선, 디스크는 스트리밍 추출 |
| Q8 | A 수정 채택(B0′→B3→B2→B1 조건부). 신뢰도 medium |
