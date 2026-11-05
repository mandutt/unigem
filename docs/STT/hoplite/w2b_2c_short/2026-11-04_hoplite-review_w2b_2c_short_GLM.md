# Hoplite 독립 검토 보고서 — Wave 2B + 2C-short (w2b_2c_short)

- 라운드: `w2b_2c_short` (2026-11-04 신규 독립 라운드. 아카이브된 v4 라운드와 별개)
- 검토자: GLM (단독 수행. 서브에이전트 생성 및 외부 모델/LLM 호출 없음)
- 검토일: 2026-11-04
- 성격: **자문(consultation)**. 프로젝트 코드·데이터·테스트·설정은 일절 변경하지 않았으며, 본 보고서 파일 1개만 신규 작성했다.

## 0. 동기화·검토 방법

- `git fetch origin` → `git pull --ff-only origin main`: "Already up to date". 당시 HEAD = `81d58ed34f13b06d2f13edd49d89a37a80323d0f` ("docs: add w2b_2c_short Hoplite dispatch").
- 검토 세션 중 origin/main이 `f4fc8a33c392cc61afefa1e748bc2666f5f7a9c6` ("docs: add w2b_2c_short Hoplite watcher", 워처 스크립트 1개 추가)로 진행되어 추가 fast-forward pull을 했다. 검토 대상 문서에는 영향 없음.
- 요청서 명시 기준 커밋 `6b1d720`은 HEAD의 조상임을 확인했다(`git merge-base --is-ancestor` PASS. 초기 shallow 상태에서 미해상이었으나 `git fetch --deepen=5` 후 확인).
- 전문 열람(요약·발췌 아님, 첫 줄부터 끝 줄까지): `docs/STT/reports/EXTERNAL_REVIEW_W2B_2C_SHORT_2026-11-04.md`(368행 전체), `docs/STT/plans/plan_wave2b_2c_short.md`(507행 전체), `docs/STT/reports/W2A_lite_results.md`(142행 전체), `docs/STT/reports/W2A_lite_cp_d2_lite.md`(165행 전체).
- 정책 교차검증: `docs/gates.md`(147행), `docs/decisions.md`(D-030~D-065 관련 행). 저장소 외부 검증: KsponSpeech 공개 데이터 카드(HuggingFace 2종)로 eval 분할 규모 확인. KsponSpeech 원논문(MDPI) 페이지는 기술적 이유로 본문 추출에 실패해 원문 직접 재확인은 하지 못했다(문서 내 3곳 일관 인용으로만 확인).
- 검토 우선순위는 요청서 §0(반증 가능성, 누출/재사용/선택 편향, factorial 타당성, 자원 현실성, 저비용 대안)을 따른다. 칭찬은 구조 판단에 필요한 최소한으로만 쓴다.

---

## 1. 답변 형식 (요청서 §6)

### 1) 권장 결론

**A — 설계대로 4h short + 4-arm pilot 진행(조건부).** 단, 아래 Must-fix 3개(MF1~MF3)가 시작 전에 반영되어야 하며, 100-step pilot이 예산 초과를 예고하면 사전등록된 fallback으로만 전환한다(사후 조정 금지 원칙 유지).

### 2) Q1~Q8

**Q1. Arm 설계 —** 2×2 factorial(LoRA 유무 × short 데이터 유무)은 두 요인의 주효과와 상호작용을 식별하는 표준적이고 충분한 구성이며, B3 제거안(옵션 B)은 약 0.5~1일 절감에 불과한 반면 CP-D2-lite의 진단("길이 분포 불일치가 주축")이 맞다면 B3≈B2라는 결과야말로 "2B 불필요, 저렴한 2C-only 채택"이라는 가장 실익이 큰 결론을 주므로 B3 유지가 옳다. 그러나 두 가지를 고쳐야 factorial이 성립한다. (1) 현재안은 B3만 offline 특징 추출(`w1_extract.py --arms fc`) + 별도 스크립트(`d5_reader.py`)를 쓰는데, 이는 AM-10("arm 간 코드·하이퍼파라미터·시드 동일, 달라도 되는 것은 입력 특징의 종류·차원뿐")과 긴장하며 요청서 §8.4가 스스로 지적한 confounder다 — 특징 수치 동등성 증명 없이는 B2−B3 차이를 LoRA 효과로 귀속할 수 없다(MF1). (2) "B2 > B1 AND B2 > B3" 동시 요구를 Full Go 차단 조건으로 쓰는 것은 귀속(attribution) 질문과 채택(go/no-go) 질문을 섞은 것이다: B3만 B0 대비 10% 이상이고 B2≈B3이면 "데이터만으로 충분, LoRA 불채택"이 합리적 승리인데, plan §8 해석 규칙("B3가 B0보다 좋으면 데이터만으로 개선; 2B 불필요")과 달리 gate 문구에서는 No-Go가 된다. Full Go 1차 판정은 `max(B2, B3)` vs `B0`(+CI)로 하고, B2>B1·B2>B3는 어느 구성을 채택할지 결정하는 귀속 진단으로 분리할 것. 또한 B1−B0 비교에는 reader 재초기화 효과가 섞인다(MF1 참조) — 이는 factorial 오염이 아니라 "LoRA 단독 효과" 해상도의 한계로, 셀 평균 기반 주효과 판단으로 보완 가능하다.

**Q2. Short 데이터 규모·분포 —** 4h는 적절한 기본값이다: 2h는 ≤4s bin gate(상대 8~10%)를 검증하기에 unique 자료가 부족하고, 6h는 CPU·디스크 부담 대비 한계효과가 작다. 분포(0–2s 25%/2–4s 35%/4–6s 20%/6–8s 20%)와 effective 40/30/30은 eval_other(≤4s 57.2%)보다 보수적인데, 이는 8–16s 성능(현재 28.6%) 보호와의 절충으로 방어 가능하다. 다만 네 가지 단서가 있다. (1) "short 4h"는 Kspon train 데이터의 **최초 도입**이기도 하다(wave1 6h는 Zeroth+Kconf, decisions D-061) — 즉 이 요인은 길이 보정과 도메인 적응이 묶여 있고, Kspon-long 대조 arm이 없으면 B2−B1을 "길이 효과"로 단독 귀속할 수 없다. 결론 문구를 "Kspon short-domain 데이터 효과"로 명확히 하라(CP-D2-lite 자체가 도메인 잔여 갭 ~5.5%p를 인정하고 있다). (2) effective 40% 내부의 0–2s 세부 목표가 미정이다. 0–2s는 최악 bin(CER 46.4%)이자 test 비중 27.6%인데, 자연 mix 기준 effective 0–2s는 약 15% 수준으로 추정된다 — 세부 목표를 명시하라(옵션 3 참조). (3) 과적합: unique ≤4s 자료는 약 2.5h(6h 중 ~0.1h + short 2.4h)이고 effective 40%는 epoch당 ~1.6배 과다 노출, 12 epoch에서 클립당 실질 ~19회 노출이다. unique 4h 유지 원칙 덕에 견딜 만하지만 short-bin train loss 대비 dev 격차 모니터링을 pilot부터 기록하라. (4) 대표성: train의 짧은 발화는 감탄사·단답 위주로 편중될 수 있어 "길이만 맞추면 eval_other short를 대표한다"는 보장은 없다 — 이는 인정된 한계로 기록하고, 화자당 상한 외의 다양화 장치는 이번 라운드에서 강요하지 않는다.

**Q3. Test 타당성 —** 발화 ID 기준 독립성은 설계대로면 충분하다: 2A-lite는 eval_other만 사용했고, D-β는 eval_clean 100만 dev로 사용했으며, FLEURS test 재사용 금지는 정확하다. 다만 세 가지 단서가 있다. (1) eval_clean 2,900은 eval_other와 **같은 코퍼스·같은 녹음 조건·(아마도) 같은 화자 풀**을 공유하는 코퍼스 내부 test다 — "새로운 도메인 일반화" 주장에는 쓸 수 없고 "Kspon 내부 일반화"로 표현을 한정해야 한다. 연구 질문(Kspon short 발화 적응)에는 이것으로 충분하며, 제품 인접 주장이 생길 때 새 P0 holdout을 별도 선언하면 된다. (2) 정책 연속성: `docs/gates.md` AM-9는 Kspon eval_clean을 "최종 판정 1회용 test" 자원으로 지정해 왔고, 2A-lite 사전등록은 "Kspon eval_clean 100은 D 평가에서 영구 제외"라고 기록했다. 2B의 재지정(100=dev, 2,900=test)은 누출은 아니지만 기존 지정 정책의 변경이므로, 봉인 전에 decisions에 명시적·dated decision으로 기록해야 한다(MF2). 참고로 공개 데이터 카드 기준 eval_clean은 3,000발화(2.6h, 60명)로 "3,000−100=2,900" 구성 자체는 사실로 확인됐다. (3) dev 100의 **선출 규칙이 어디에도 문서화되어 있지 않다**(무작위/선두/선별 여부 불명) — 편향 여부를 판단할 수 없으므로 선출 규칙을 provenance로 남기고, n=100의 검증력 한계를 gate 설계에 반영하라(Q5). 또한 dev 100과 test 2,900은 같은 60명 화자 풀에서 나오므로 dev 기반 early stop이 화자 특이성에 부분 최적화될 수 있다 — test 성능 자체에는 덜 해롭지만 "새 화자 일반화" 주장을 함께 하지 말아야 한다.

**Q4. 모델·LoRA —** rank 8/alpha 16, 10–11층 8모듈(q/k/v/post + FFN 1/2)은 근거가 아직 없는 상태에서의 비용 합리적 1차 가설이고, LoRA B=0 초기화로 학습 시작점이 정확히 B0의 함수와 동일해진다는 점은 좋은 설계다. 그러나 (1) **reader 초기화가 미정의**다. 2A-lite에서 scratch reader의 best epoch는 15–20이었는데, scratch 초기화 + pilot 3 epoch(또는 full 12 epoch)를 완전 수렴한 B0와 비교하면 구조적으로 불리하며, 이는 "LoRA·데이터 무효"라는 false No-Go로 직결된다. B1/B2/B3의 reader를 동일하게 초기화할 것을 사전등록하라(권고: B0의 학습된 reader에서 warm-start — B=0 초기화와 결합하면 세 arm 모두 B0 해에서 출발하는 깨끗한 비교가 된다. warm-start 시 reader LR 1e-3이 warm 해를 파괴하지 않도록 pilot에서 확인). (2) 8–11층 확장이나 conv(`lconv1d`) 적용은 B1이 약한 방향일 때의 1차 진단 후보로만; 전체 fine-tune은 CPU 예산상 부적격하다. (3) F-C-concat(4096) 유지는 2A-lite와의 직접 비교 가능성을 지키므로 옳다(1536 단순화는 별도 wave에서). (4) wordpiece head 미포함은 단일변수 원칙상 옳다.

**Q5. Gate —** 상대 개선 + paired bootstrap CI + 결과 후 threshold 변경 금지라는 골격은 프로젝트 관례(gates.md AM-5/AM-6)와 일관되고 좋다. 문제는 검증력이다. (1) dev n=100에서 B0 예상 CER ~0.35–0.39(D-β에서 F-A′ 0.3939였던 같은 100발화 기준)에 대한 상대 5%는 절대 ~1.8–2.0%p로, 2A dev(n=192)의 paired CI 폭(~1.4%p)을 n으로 스케일하면 n=100 CI 폭은 ~±1%p 수준으로 추정된다 — 실제 효과가 있어도 pilot이 빈번히 FAIL/무의미한 판정에 도달한다. gates.md의 자체 관례(PASS/FAIL/INCONCLUSIVE, R-D1의 "INCONCLUSIVE 시 1회 확장")를 2B pilot에 이식하고, 확장 수단으로 FLEURS dev 192 방향 일치 또는 B2 seed43 반복을 사전에 지정하라(MF3). (2) ≤4s bin gate(상대 8%)는 dev 100 내 bin 표본(예상 ~50–70개, UNVERIFIED — 봉인 시 측정)에서 판별력이 사실상 없으므로 pilot에서는 "방향 일치"로 완화하고 bin 수치 판정은 full + test 2,900으로 승격하라. (3) 상대 개선을 주지표로 하는 것은 적절하되 절대 CER·errors/ref 병기는 기존 관례대로 유지. (4) test 10% 고정 + 1회 평가는 all-or-nothing이므로, 점추정 5–10% 구간을 INCONCLUSIVE(CP-D2 진단)로 처리하는 완충을 권고한다(기각선 자체를 결과 후에 바꾸는 것이 아니라 사전에 밴드를 넣는 것이므로 AM-5 위반이 아니다).

**Q6. 누락된 confounder —** 요청서에 나열된 항목 외에 실제로 빠져 있거나 미정의인 것은 다음이다. (1) B3 offline 특징 vs B1/B2 on-the-fly mel의 수치 동등성(§8.4 — MF1에서 unit test로 강제). (2) **vocab/OOV**: Kspon train short 클립을 1,101자 vocab(wave1 기반)에 맞추는 규칙이 미정의다. eval_other에서도 vocab coverage 99.43%(378자 miss)였음을 감안하면 train 라벨의 OOV 처리(클립 제외 또는 매핑)와 OOV율 보고를 사전등록해야 B3(데이터-only)까지 동일 규칙이 적용된다(MF2). (3) **화자 메타데이터 가용성**: D-061은 "화자 ID 부재 등으로 speaker-disjoint 평가 불가"였다. 2C-short 선별 규칙("화자당 상한", "eval과 화자 중복 0")은 Kspon train에서 화자 ID(또는 세션 프록시)를 실제로 얻을 수 있어야 실행 가능하다 — preflight에서 확인하고, 불가하면 대체 규칙을 사전에 확정하라(MF2). (4) eval_clean 2,900의 duration 분포 미측정 — bin gate의 분모이므로 봉인 시점에 메타데이터만으로 측정·고정. (5) early stop(patience 3) on n=100 dev — 진동에 의한 조기 중단 위험이 있으니 patience 4–5 또는 완화 규칙을 pilot에서 확인. (6) CPU 6-thread 학습은 bitwise 재현이 보장되지 않는다 — 기존 관례(env snapshot, RNG in checkpoint)로 대응하고 보고서에 한계 표기. (7) "short-only batch 4"의 정확한 의미(batch 구성 규칙)를 명시할 것 — sampler와 상호작용한다. (8) Kconf와 eval_clean 간 화자 중복 가능성은 UNVERIFIED(데이터 비공개로 저장소에서 검증 불가) — 가능하면 확인.

**Q7. 비용·현실성 —** 7–10일은 조건부로 현실적이다. 근거: Wave 0에서 reader(8.65M params) 20 epoch가 66–82분이었으므로 B3(reader-only + short 특징 추출)은 0.5–1일 내 가능하다. 불확실한 것은 B1/B2의 end-to-end 비용(12층 Conformer forward 10h × 12 epoch × 2 arm)이며, 이는 100-step pilot의 sec/step을 즉시 "full-run 예상 일수"로 환산해 판정해야 한다(사전 합의된 임계 초과 시 사전등록 fallback — MF3). 계산 절감 여지도 있다: gradient는 l10–11 LoRA와 reader에만 필요하므로 0–9층은 `no_grad`로 돌리고 l06/l08 tap을 detach하면 backward 비용과 activation 메모리가 크게 줄어든다(옵션 1). 디스크는 현재 19GB로 "25GB 이상" 선제 확보가 어려운데, shard 단위 stream+선택+삭제(피크 ~6–7GB)로 충분히 가능하다 — "25GB" 전제는 스트리밍을 전제로 재산정하거나 preflight에서 실측 피크로 갈음하라. VPS 배제는 steal 실측(1시간 후 17.5%, epoch 4배)이라는 근거가 있어 타당하다. 전체적으로 일정이 빠듯하므로, pilot 이후 설계 변경이 필요해지는 순간이 예산 붕괴의 최대 리스크다.

**Q8. 종합 권고 —** **A**를 권한다. (1) CP-D2-lite의 길이-불일치 진단은 수치로 견고하다(46.4%→28.6% 단조 감소, train ≤4s 4.1% vs eval_other ≤4s 57.2%, 잡음 마커 부정, outlier 아님) — 이 진단에 대한 유일한 저비용 개입이 short 데이터 보강이고, 그 효과를 검증하지 않고 다음으로 갈 근거가 없다. (2) factorial 4-arm은 효과 분리의 최소 구성이고 B3는 Wave 0 실측상 저렴하다 — B(3-arm)는 0.5–1일 절감 대비 attribution 상실이 커서 비추천. (3) C(LoRA만)는 CP-D2-lite가 스스로 "부족할 가능성 높다"고 예고한 경로를 비용을 들여 재확인하는 낭비다. (4) D(데이터만)는 adaptation 효과를 계속 미측정으로 남기고, E(새 holdout까지 보류)는 연구 트랙의 질문에는 과잉 안전장치다. 단, A는 MF1~MF3 반영을 조건으로 하며, pilot이 실현성 한계를 보이면 사전등록된 fallback(short 2h 또는 epoch 축소 — B안의 "B3 제거"보다 이쪽을 우선)으로 전환한다.

### 3) Must-fix (시작 전 반드시 수정)

**MF1 — arm 공정성 계약(가장 중요).** (a) B1/B2/B3의 reader 초기화를 동일하게 사전등록하라. 권고는 B0의 학습된 reader에서 warm-start하는 것(LoRA B=0과 결합 시 세 trained arm 모두 정확히 B0 해에서 출발). 미지정 상태의 scratch + 3/12 epoch는 2A-lite의 best epoch 15–20 실측과 충돌하며 false No-Go를 만든다. (b) B3의 offline 특징(`w1_extract --arms fc`)과 B1/B2의 on-the-fly mel이 동일 샘플에서 수치 일치함(허용오차 명시)을 unit test로 강제하라(AM-10 충족). (c) pilot 직전에 B1을 0-step(초기화만) 상태로 dev 100에 평가해 B0와 일치함을 확인하는 회귀 체크를 넣어라. 이 셋 없이는 pilot 결과와 B2−B3 귀속 모두 신뢰할 수 없다.

**MF2 — 봉인 전 test·데이터 계약 고정.** (a) eval_clean 재지정(100=dev, 2,900=test)을 decisions에 명시·dated 기록하라(AM-9의 "eval_clean = 최종 1회용 test" 지정, "eval_clean 100 영구 제외" 문구와의 정합성 포함). (b) 봉인 시점에 2,900의 duration bin 분포·bin 정의·화자 구성을 측정·기록하라(라벨 미열람, 메타데이터만) — bin gate의 분모를 사전에 확정한다. (c) Kspon train 화자 메타데이터 가용성을 preflight에서 확인하라(D-061 선례: 화자 ID 부재로 speaker-disjoint 불가). 불가하면 "화자당 상한·화자 중복 0"을 세션/파일 단위 프록시 규칙으로 사전 변경. (d) 1,101 vocab에 대한 Kspon train OOV 처리 규칙(제외/매핑 + OOV율 보고)을 사전등록하라.

**MF3 — pilot의 통계적·계산적 현실화.** (a) pilot gate에 INCONCLUSIVE 밴드(상대 3–5%)를 도입하고, 확장 수단(FLEURS dev 192 방향 일치 또는 B2 seed43 반복 중 택1)을 사전 지정하라 — R-D1 선례의 재사용이다. (b) 100-step pilot 결과를 full-run(B1+B2, 12 epoch) 예상 일수로 즉시 환산해 보고하고, 사전 합의된 임계(예: 합계 > 5일) 초과 시 사전등록 fallback(short 4h→2h 또는 epoch 12→8, 어느 쪽인지 사전 선택)을 적용하라. (c) pilot의 ≤4s bin gate는 "방향 일치"로 완화하고 bin 수치 판정은 full + test 2,900으로 승격하라(dev 100 내 bin n≈50–70에서는 상대 8% 판별이 불가능하다).

### 4) Optional (있으면 좋은 것)

1. **0–9층 `no_grad` + l06/l08 tap detach**: gradient는 l10–11 LoRA와 reader에만 필요하다. CPU 학습 시간과 메모리를 크게 줄이는 구현 최적화로, MF3의 실현성 판정을 유리하게 만든다.
2. **B2(+가능하면 B3) seed43 반복**: Full 판정의 seed 민감도를 낮춘다. B3는 Wave 0 근거상 저렴하다.
3. **sampler 0–2s 세부 목표 명시**(예: effective 15% 내외)와 8–16s bin 회귀 모니터링 — 최악 bin(0–2s 46.4%) 공략과 long 회귀 방어를 동시에.
4. **B1이 약한 방향일 때의 진단 계획**: `lconv1d`/8–11층 확장은 "결과를 본 뒤 arm·threshold 변경"이 아니라 새 사전선언 진단으로만.
5. **참고 맥락 기록**: D-043의 Notesoop Kspon eval_clean 27.81%(gate 아님, 참고치)을 2B 보고서 배경에 병기하면 상대 위치 해석에 도움이 된다.
6. **test 1회 평가 이후의 탐색 분석 허용**: bin별·화자별 세부 분석은 "탐색적" 라벨로 허용 — gate 오염 없이 정보량을 얻는다.

### 5) 잘못된 전제 / 검증이 필요한 것

1. **(요청서 누락 — 확인됨)** 요청서는 wave1 6h의 구성을 명시하지 않는다. `docs/decisions.md` D-061에 따르면 6.0008h = **Zeroth 1,534 + Kconf 850**으로 Kspon이 전혀 없다. 따라서 "short 4h 추가"는 길이 보정인 동시에 **Kspon 도메인 데이터의 최초 도입**이며, 2C의 효과 서술과 B2−B1 해석 규칙("short data 효과 없음")은 이 결합을 명시해야 한다.
2. **(정책 긴장 — 확인됨)** AM-9가 Kspon eval_clean을 "최종 판정 1회용 test"로 지정하고 2A-lite 사전등록이 "eval_clean 100은 D 평가에서 영구 제외"라고 기록한 것과, 2B의 "100=dev 재사용 + 2,900=test"는 충돌하지 않도록 명시적 재지정 decision이 필요하다(누적 사용 이력: eval_clean 100 = D-β dev 1회뿐, test로는 미사용).
3. **(UNVERIFIED)** "eval_other와 같은 60명 화자" — 공개 데이터 카드는 각 split이 60명(30남/30여)임까지만 확인한다. 두 split이 **동일한** 60명인지는 메타데이터로 검증 필요.
4. **(UNVERIFIED)** "Kspon train 1 shard에서 4h short 선별" — Kspon train(자발적 대화)의 ≤8s 밀도가 높아 가능성은 높으나, shard별 분포와 화자 메타데이터 가용성에 의존한다. preflight 필수 확인.
5. **(UNVERIFIED)** "10h·12 epoch CPU 3–5일" — pilot 측정 전까지 미확인. Wave 0의 66–82분/20epoch는 reader-only 하한일 뿐이다.
6. **(설계 미완결 — 확인됨)** pilot 3 epoch의 B2를 완전 수렴한 B0와 비교하는 "Pilot Go"는 reader 초기화가 정의되지 않으면 성립하지 않는다(MF1).
7. **(검증 완료 — 잠재 의심 해소)** "eval_clean 3,000 − 100 = 2,900" 구성은 공개 데이터 카드 2종과 일치한다(eval_clean 3,000발화/2.6h/60명, eval_other 3,000발화/3.8h/60명).
8. **(사소)** 검토 기준 커밋 `6b1d720`은 HEAD 조상으로 확인됐다. 요청서 작성 후 docs성 커밋 4개(디자인 문서·프롬프트·dispatch·watcher)가 추가되었으나 검토 대상 내용은 변하지 않았다.

### 6) 신뢰도

- **high**: 설계 구조 판단(factorial, gate 구조, 누출/재사용 판정), 수치 앵커 검증(부록 A 전 항목 원문 재계산 일치), 정책 연속성 판단(gates.md/decisions.md 원문 대조).
- **medium**: 비용·일정 추정(CPU end-to-end 실측 부재), 데이터 메타데이터 의존 항목(화자 ID, shard 밀도, eval_clean duration 분포 — 저장소에 데이터가 없어 검증 불가), Kspon 원논문 9.0% 수치의 원문 직접 재확인(페치 실패).

---

## 2. 부록 A — 수치 대조표 (요청서 앵커 ↔ 원문)

| 앵커 | 원문 근거 | 판정 |
|---|---|---|
| F-C-concat seed42 dev CER 0.20913 (1,644/7,861) | `W2A_lite_results.md` L14, 요청서 L73 | 일치 |
| F-A′ 0.22236 (1,748/7,861) | `W2A_lite_results.md` L11, 요청서 L70 | 일치 |
| +1.323%p, 상대 5.95%, CI [+0.631, +2.028]%p | `W2A_lite_results.md` L24 (재계산: (0.22236−0.20913)/0.22236 = 5.95%) | 일치 |
| seed43 F-C-concat 0.208116, F-A′ 0.2233, 6.8% | `W2A_lite_results.md` L59-66 (재계산: 6.80%) | 일치 |
| Kspon eval_other 2,962평가, CER 0.35143, blank 0, 23,508/66,893 | `W2A_lite_results.md` L86-91 (재계산: 0.35143) | 일치 |
| FLEURS test 318평가, CER 0.23509 | `W2A_lite_results.md` L101-106 (재계산: 0.23510) | 일치 |
| train ≤4s 4.1% (97/2,384) vs eval_other ≤4s 57.2% (1,693/2,962) | `W2A_lite_cp_d2_lite.md` L50-58, L136 (재계산: 4.07%, 57.16%) | 일치 |
| 0–2s CER 46.4% vs 12–16s 28.6%, Pearson −0.265 | `W2A_lite_cp_d2_lite.md` L25, L31, L18 (재계산: 0.4644, 0.2862) | 일치 |
| noisy 34.7% vs clean 35.4% | `W2A_lite_cp_d2_lite.md` L76-77, L141 | 일치 |
| 상위 1% 오류 4.2%, 상위 5% 15.5% | `W2A_lite_cp_d2_lite.md` L85-87, L130 | 일치 |
| 학습 6.0008h / 2,384클립 | plan L133, decisions D-061 | 일치 (구성: Zeroth+Kconf — 요청서 미기재) |
| eval_clean 100 dev / 2,900 test / FLEURS test 재사용 금지 | plan L147-168, 요청서 L190-202 | 일치 |
| 타워 12층 Conformer, 25 tokens/s, hidden 1024, output_proj 1536 | 요청서 L44, plan §4 | 일치 (문서 간) |
| Kspon 원논문 960h eval-other CER 9.0% | 요청서 L128 등 3곳 인용 | 문서 내 일관 인용, 원문 직접 재확인 실패(UNVERIFIED) |

## 3. 부록 B — 판정 근거 상세

### B1. factorial 식별과 채택 판정의 분리

2×2 셀(B0=frozen+6h, B1=LoRA+6h, B2=LoRA+10h, B3=frozen+10h)에서 주효과는 셀 평균으로 식별된다: 데이터 주효과 = [(B2+B3)−(B1+B0)]/2, LoRA 주효과 = [(B1+B2)−(B0+B3)]/2, 상호작용 = (B2−B1)−(B3−B0). 현행 gate가 요구하는 "B2>B1 AND B2>B3"는 상호작용 하의 조건부 효과만 검사한다. 채택 판정과 귀속 판정을 분리하면, B3-only 성공(=2C-only 채택, tower 수정 없는 가장 저렴한 배포 형태)도 정상적 성공 경로로 기록된다. 이는 plan §8 해석 규칙(L415-417)의 정신과 일치하며 gate 문구만 고치면 된다.

### B2. reader 초기화와 pilot 공정성

2A-lite에서 scratch reader의 best epoch는 15–20(F-A′ 16, F-B 15, F-C-softmax 20, F-C-concat 18)이었다. pilot 3 epoch의 B2(아마도 scratch)를 완전 수렴 B0와 비교하면 "B2가 나쁨"이 구조적으로 예약되어 있다. warm-start(B0 reader) + LoRA B=0이면 세 trained arm 모두 B0 해에서 출발하므로, (i) 3 epoch pilot이 방향 판별이 가능해지고, (ii) B2−B3가 "동일 데이터에서 tower adaptation의 순수 효과"에 가까워지며, (iii) epoch-0 회귀 체크(B1 0-step ≡ B0)로 파이프라인 등가성까지 검증된다. warm-start의 반대편 리스크(reader가 6h 분포의 해에 갇혀 새 데이터 효과를 과소계상)는 pilot에서 warm vs scratch 중 하나를 고르라는 요구 자체를 정당화한다 — 어느 쪽이든 **사전등록**이 핵심이다.

### B3. sampler 산수와 과적합 한계

10h mix의 자연 ≤4s 비중은 약 2.5h(=25%; plan L136의 "24% 정도"와 일치)다. effective 40%는 epoch당 4h 분량을 ≤4s에 배정 → 클립당 ~1.6배 노출, 12 epoch 누적 ~19회. uniform(12회) 대비 +58% 노출로, unique 2.5h 규모에서는 과적합이 배제되지 않으나 허용 범위다. 대조적으로 CP-D2-lite가 경고한 "4개 클립 반복" 시나리오와는 질적으로 다르다. 0–2s 세부는 effective ~15% 추정(1.0h/2.5h×40%)으로 test 27.6% 대비 부족 — 옵션 3.

### B4. pilot 검증력 추정

B0의 dev 100 CER은 미측정이지만 같은 100발화에서 D-β F-A′ 0.3939였으므로 0.35–0.40 구간이 합리적 추정이다. 상대 5% ≈ 절대 1.8–2.0%p. 2A dev(n=192) paired CI 폭 1.4%p를 sqrt(192/100) 스케일하면 n=100 폭 ~1.9%p(반폭 ~1%p) — 5% 효과 탐지는 성공/실패 이분법에서 불안정하다. 이 수치는 추정이며(라벨: estimate), 결론은 "INCONCLUSIVE 밴드 + 확장 수단 사전지정"이 필요하다는 방향론이다.

### B5. CPU 실현성

확정 근거: Wave 0 reader 8.65M/20epoch = 66–82분(B3 비용의 상한 근거), 2A-lite reader best epoch 15–20. 미확정: tower forward 포함 1 epoch 시간. 10h epoch ≈ 2,000 batch(batch 2×평균 ~9s) — sec/step이 1s이면 ~33분/epoch/arm, 5s이면 ~2.8h/epoch/arm. 즉 pilot 측정값에 따라 full B1+B2가 하루 미만일 수도, 1주일 이상일 수도 있다 — MF3(b)의 사전 환산 규칙이 필수인 이유다. `no_grad` 절감(옵션 1)은 최악의 쪽을 상당히 완화한다.

### B6. 정책 타임라인 (eval_clean)

D-043 시절 eval_clean은 최종 평가 후보로 지정 → D-β에서 100발화를 dev로 사용(정책 일탈, 기록됨) → 2A-lite 사전등록 "eval_clean 100은 D 평가에서 영구 제외" + AM-9 "test 1회 원칙" → 2B 제안 "100=dev, 2,900=test". 누출 없음. 필요한 것은 재지정의 공식 기록뿐이다. eval_clean이 최종 test로 **한 번도 사용된 적이 없다**는 점이 이 재지정의 정당성 근거다.

## 4. 부록 C — 리스크·완화 요약

| 리스크 | 등급 | 완화 (근거) |
|---|---|---|
| pilot false No-Go (reader 미정의/3 epoch) | 상 | MF1 warm-start + epoch-0 회귀 체크 |
| B2−B3 귀속 오염 (특징 경로 불일치) | 상 | MF1 unit test, AM-10 준수 |
| pilot gate 저검증력 (n=100) | 상 | MF3 INCONCLUSIVE 밴드 + FLEURS dev/seed43 |
| 정책 불연속 (eval_clean 재지정 미기록) | 중 | MF2 dated decision |
| 화자 메타데이터 부재 (D-061 선례) | 중 | MF2 preflight + 프록시 규칙 사전확정 |
| vocab OOV (Kspon train 최초 학습) | 중 | MF2 사전등록 규칙 |
| CPU 일정 초과 | 중 | MF3 사전 환산 + fallback, no_grad 절감 |
| 디스크 19GB < 25GB | 중 | shard stream+삭제로 피크 재산정 (plan 리스크표와 동일 방향) |
| 길이 효과와 도메인 효과 결합 | 중 | 해석 문구 수정 (Q2) — 대조 arm 추가는 강요하지 않음 |
| short-bin 과적합 (클립당 ~19회 노출) | 하 | 모니터링 + unique 4h 유지 원칙 |

## 5. 검토 범위의 한계

- 저장소에 학습·평가 데이터가 없어(`data/`에는 README만 커밋됨) 다음은 문서 진술로만 확인된다: eval_clean 100의 선출 규칙, 2,900 ID 실재성, eval_other/eval_clean 화자 구성, manifest 통계. 해당 항목은 본문에서 UNVERIFIED로 표기했다.
- 코드(`train/d5_reader.py`, `w1_extract.py` 등)는 이번 라운드 범위에서 구현 세부까지 열람하지 않았다. MF1의 unit test 요구는 문서 수준 계약으로 제시한다.
- KsponSpeech 원논문 본문 페치가 실패해 외부 기준 수치(9.0%)는 프로젝트 문서의 일관 인용으로만 확인했다.
