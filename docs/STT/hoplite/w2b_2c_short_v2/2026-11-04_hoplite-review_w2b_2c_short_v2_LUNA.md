# 외부 검토 보고서 — Wave 2B + 2C-short v2

**모델:** GPT-6 Luna (openai/gpt-6-luna)
**검토 기준 커밋:** e1d62803ef869bcddddd57951f2e3621365239d2
**권장 결론:** **B — 아래 Must-fix를 반영한 뒤 pilot 시작**

## 검토 범위와 판단 전제

요청서 docs/STT/reports/EXTERNAL_REVIEW_W2B_2C_SHORT_V2_2026-11-04.md 522행을 첫 행부터 끝까지 직접 읽었다. 추가로 docs/STT/plans/plan_wave2b_2c_short_v2.md, docs/STT/reports/W2B_preflight.md, docs/STT/reports/W2A_lite_results.md를 대조했다. 검토에 앞서 git fetch origin과 git pull --ff-only origin main은 모두 성공했고, 결과 HEAD는 위 커밋이다. 보고서의 평가 대상은 설계·문서·preflight 근거이며, short 오디오·실제 학습·feature parity 코드 검증은 아직 실행되지 않은 상태다.

현재 안은 in-domain 발화 수준의 탐색 실험으로는 진행 가능하지만, **그대로 pilot에 들어가면 안 된다.** 가장 중요한 이유는 (1) vocab/OOV 정책이 요청서와 설계 문서에서 충돌하고, 실제 입력 feature 기준 CTC 적격 여부가 확인되지 않았으며, (2) B0′/B1의 “0-step 동일”과 cache parity의 비교 대상이 모호하고, (3) B3-nat의 현재 데이터 정의로는 sampler 효과를 분리할 수 없고, (4) CER에서 max(B2,B3)와 최종 판정의 후보 선택·최소 효과 크기가 사전 고정되지 않았기 때문이다. 이 문제들은 새 P0 holdout을 요구하기보다 사전등록과 비교 조건을 고정해 해결할 수 있다.

## Q1. dev/test 분리와 재사용

**판정:** 수량과 표기는 utterance-level “in-domain sealed holdout”에 적합하지만, 독립 test나 화자 일반화의 증거는 아니다. **근거:** preflight의 수량은 3,000−10=2,990이고 500+2,400+90=2,990으로 맞으며, duration bin별 dev/test/spare 합도 각각 500/2,400/90이다. test는 기존 D-β 100과 겹치지 않고 dev/test 교집합도 0으로 보고됐다. 따라서 D-β 100을 dev에 재사용한 사실은 새 test의 직접 누출은 아니지만, 이전에 본 100개는 early stopping과 모델 선택에서 더 적합해질 수 있는 dev 편향을 만든다. 더 중요하게, 실제 preflight 보고는 eval_other·Wave 1 train·short·B3-nat와의 ID 중복이 0이라고 보여주지 않는다(설계서의 해당 항목은 향후 검증 목록이다). eval_clean의 speaker ID가 없으므로 speaker overlap 및 cluster bootstrap도 검증할 수 없다. test transcript는 preflight의 OOV/CTC 계산에 사용됐으므로 “sealed”는 라벨을 접근 불가능하게 한 blind test가 아니라, 결과를 모델 선택에 쓰지 않는 절차적 봉인으로 이해해야 한다. **다음 단계:** audio 추출 전 ID/manifest hash로 train·eval_other·short·B3-nat·dev·test의 중복을 검사하고, 시험 점수와 개별 test 라벨은 checkpoint·후보 선택 전 열람하지 않는 접근 절차를 둔다. 기존 100과 신규 400의 dev 결과를 별도로도 보고하고, 신규 400을 모델 선택의 주 dev로 쓰는 방안을 사전등록한다. 결론은 in-domain utterance에 한정하고 P0나 새 화자 일반화로 확대하지 않는다.

## Q2. B0′, reader warm-start와 feature parity

**판정:** 공통 reader 초기화는 좋은 통제지만, 지금 적힌 회귀/parity 계획만으로 비교가 공정하다고 확정할 수 없다. **근거:** 설계서는 B0′를 2A reader로 warm-start해 6h 재학습한다고 하면서 B1의 “0-step == B0′”도 요구한다. B0′가 이미 6h 학습을 마친 checkpoint를 뜻하면, 같은 2A 초기화에서 시작한 무학습 B1이 그 최종 reader와 같을 이유가 없다. 반대로 “0-step”이 공통 초기 상태와의 출력 동일성만 뜻한다면 그 기준 checkpoint를 명시해야 한다. 또 2B vocab을 확대하면 2A reader의 출력 차원·문자 ID와 달라질 수 있으므로 기존 출력층 행의 remap, blank index, 신규 문자 행 초기화가 정의되지 않은 채 “같은 reader weight”를 보장할 수 없다. LoRA B=0은 동일 tower weight에서 adapter를 켠 초기 forward가 같다는 검증이지, 학습 후 B1과 B0′가 같다는 뜻이 아니다. 마찬가지로 LoRA가 학습된 B1/B2 feature와 frozen tower에서 캐시한 B3/B3-nat feature는 정상적으로 다를 수 있어, 그 둘을 직접 비교하는 것은 일반적인 cache parity 검사가 아니다. **다음 단계:** B0′의 시작·학습 완료 checkpoint와 B1 초기 checkpoint의 관계를 문서화하고, vocab이 정해진 뒤 동일한 문자→ID 매핑과 새 output row의 초기화를 모든 arm에 고정한다. 동일한 frozen tower/checkpoint·동일 샘플·동일 전처리에서 online과 cached feature/logit을 비교하고, dtype·장치에 맞춘 수치 허용오차를 사전 설정한다. LoRA B=0의 별도 출력 회귀, feature 생성의 checkpoint hash·frontend 설정, B0′가 과거 2A dev 결과에서 크게 벗어났을 때 재현성 조사/중단 규칙도 둔다.

## Q3. B3-nat의 인과 해석

**판정:** 현 문구대로는 B3−B3-nat을 sampler 효과로 해석할 수 없다. **근거:** 설계서의 B3는 short-biased 4h를 추가하고, B3-nat은 길이 목표가 없는 별도 natural 4h를 추가한다. 그러면 두 arm은 sampler뿐 아니라 선택된 클립과 길이·전사 구성도 다르다. 반대로 같은 short 4h를 두 arm에서 쓰면 sampler contrast는 깨끗해지지만, 그 집합에 natural sampler를 적용한 것이 자연적인 Kspon 길이 분포를 재현하는 것은 아니다. 현재 요청서의 Q3도 이 양자택일을 인지하지만, 계획과 gate는 B3−B3-nat을 “sampler 효과”로 부른다. 아울러 B3−B0′는 추가 데이터와 sampler가 함께 바뀌므로 순수 data-only 효과가 아니며, ≤4초/4–8초/8–16초의 40/30/30이 clip draw 비율인지 오디오 시간·frame 비율인지도 고정해야 한다. **다음 단계:** 가장 저렴하고 해석 가능한 선택은 B3와 B3-nat에 **정확히 같은 10h clip ID 집합**을 쓰고 sampler만 다르게 하되, B3-nat을 “고정된 short-enriched pool에서의 unbalanced/natural sampling”으로 부르는 것이다. optimizer step 수와 총 노출량(clip 수 또는 audio frames 중 정의된 기준)을 맞추고 replacement·seed·epoch를 고정한다. 원래 Kspon natural 분포를 대표하는 별도 4h를 유지하려면 B3−B3-nat은 “구성+sampler 차이”라고 제한해 보고하고, sampler 단독 효과라는 표현을 삭제한다. 순수한 도메인·길이·sampler 분해를 추가로 원하면 요인 설계가 필요하지만, pilot 목적상 그 비용을 먼저 지출할 근거는 부족하다.

## Q4. OOV, vocab와 CTC

**판정:** 2A vocab 기준 통계는 유용한 상한이지 최종 2B coverage나 CTC 적격성 증명은 아니다. **근거:** preflight에서 test OOV는 185/2,400 utterances(7.71%)이며 OOV 문자는 참조 40,222자 중 214자, 즉 214/40,222=0.532%로 계산과 표기가 맞는다. “in-vocab 2,215”는 2,400−185로 맞지만, 이는 OOV utterance를 제외한 선택된 보조 subset일 뿐 전체 test를 대체하지 않는다. 요청서는 2B vocab을 train 6h+short에서 새로 만들겠다고 하지만 설계서 §2.1은 1,101자 2A vocab 밖 문자가 있는 Kspon train clip을 기본 제외한다고 해 새 vocab 계획과 충돌한다. 이 선택은 short 표본의 lexical composition을 바꿀 수 있다. 또한 preflight는 오디오 추출 없이 metadata/TRN만 읽었다고 명시하면서 CTC chars+repeats > frames 0을 보고하므로, 해당 frame 수가 실제 전처리·encoder 출력 frame인지 시간 기반 추정인지 확인되지 않았다. **다음 단계:** train-only vocab 정책을 하나로 확정한다. 새 vocab이면 eval 텍스트를 넣지 않고, short 선별·정규화 이후 모든 arm에 동일하게 freeze하며 reader 출력층 remap을 정의한다. 2A vocab을 고수한다면 제외 규칙·제외율·선택 편향을 기록한다. test 전체 2,400을 주평가에 남기고 OOV 문자를 오류로 처리하며, in-vocab subset은 보조로만 보고한다. 실제 파형/동일 frontend/정규화에 대한 CTC target_len + repeats <= output_frames 검사를 train·dev·test feature 생성 시 다시 실행하고, test 라벨은 모델 선택에 사용하지 않는다. eval_clean에 speaker ID가 없어 utterance bootstrap만 가능하다는 제한도 고정한다.

## Q5. Gate, 표본과 주지표

**판정:** 현재 gate는 사전등록 가능한 상태가 아니다. **근거:** CER는 낮을수록 좋은 지표이므로 “max(B2,B3)”가 CER 값의 최대인지, 개선량의 최대인지, dev에서 선택한 최선 arm인지 명확하지 않다. test 결과를 보고 둘 중 더 나은 arm을 고르는 것이라면 그 선택까지 포함하지 않은 단순 paired CI는 선택 편향을 반영하지 않는다. pilot의 “1.0%p 개선 또는 상대 5%+CI 방향”은 OR 조건이며, dev 500은 early stop에도 쓰여 pilot Go의 독립적인 확증 표본이 아니다. full gate에는 최소 실용 개선폭이 없고, 개선량 차이의 부호도 정의되지 않았다. speaker-cluster bootstrap은 사용 불가이며 plan §5.2는 여전히 이를 요구해 요청서와 상충한다. **다음 단계:** 개선량을 Δ = CER(B0′) − CER(candidate)로 정의해 양수가 개선임을 명시하고, full 채택은 최소 점추정 개선 1.0%p와 paired utterance-bootstrap 95% CI 하한 >0을 함께 요구하는 안을 사전 확정한다(다른 실용 임계값을 택해도 되지만 test 전에 고정). B2/B3 후보는 dev에서만 선택·freeze한 뒤 그 한 arm을 primary test comparison으로 지정하고, 나머지 frozen arms의 test 결과는 탐색적 진단으로만 표시하거나 max-selection을 CI에 반영하는 방법을 미리 정한다. bootstrap은 같은 utterance를 두 모델에서 짝지어 재표집하고, 각 replicate에서 오류 수/참조 문자 수로 micro-CER를 다시 계산한다. pilot은 실행 가능성·학습 안정성 점검과 사전등록된 진행 조건에 한정하고, seed 43의 요구 여부도 “가능하면”이 아니라 필수 robustness 조건 또는 명시적 미실시 한계로 고정한다. FLEURS dev no-regression은 보조 안전장치이지 새 도메인 일반화 gate가 아니다.

## Q6. 데이터, 디스크와 VPS

**판정:** 현재 자료만으로 streaming·저장 용량의 현실성을 확인할 수 없다. **근거:** preflight는 C: 여유 약 18GB, VPS eg2-2 디스크 20GB, shard 하나 14–15GB로 보고하지만, shard 다운로드 throughput, 실제 선별 audio 크기, feature cache/임시파일/모델 저장 공간의 동시 peak는 측정하지 않았다. zip 전체를 staging하는 경우 20GB 중 약 5–6GB만 남으며, feature 저장은 그 전에 고려되지 않았다. 요청서의 6h F-C feature 약 11GB도 4h short, 별도 4h natural, dev/test feature를 함께 보관할 때의 peak를 증명하지 않는다. 단순 선형 환산으로 4h feature 하나만 약 7.3GB가 될 수 있지만, 길이 분포·dtype·저장 형식이 같다는 보장이 없어 이는 capacity 측정값이 아니다. 로컬은 B0′/B1/B2, VPS는 B3/B3-nat이라는 배치는 host별 재현성·steal·파일 복제 비용도 남긴다. **다음 단계:** 대표 shard 일부를 실제로 받아 압축/선별 audio/feature 생성까지 한 번 재고, peak free disk, 임시 공간, throughput, 체크포인트 보존을 기록한 뒤 상한과 안전 여유를 정한다. 동일한 6h frozen feature를 재사용하고 arm별 추가 cache는 순차 처리·삭제하거나 VPS에 보관하는 방안을 검증한다. 같은 short pool로 B3/B3-nat을 비교하면 별도 natural 4h 확보·저장 비용도 줄어든다. “streaming”이라는 이름만으로 15GB shard가 20GB VPS에서 문제없이 처리된다고 가정하지 않는다.

## Q7. 일정과 중단 기준

**판정:** 5–7일은 목표치로는 가능할 수 있지만, 검증된 일정 예측은 아니다. **근거:** 요청서의 phase 범위를 그대로 더하면 약 4.125–7.208일(데이터 3–5시간을 일 단위로 환산하고 구현·pilot·full·보고 범위를 합산)로, 5–7일은 둥글린 추정이며 빠른 4일은 최소치보다도 빠듯하다. 산출 근거인 2A 20-epoch 시간과 feature extraction은 이번 5-arm/12-epoch 실행, 특히 B1/B2의 LoRA gradient 비용이나 VPS steal을 실측한 값이 아니다. pilot에서 “INCONCLUSIVE면 full 확장”은 그 자체로 진행 승인 기준이 아니며, full의 추가 비용과 seed 43까지 포함한 최대 예산도 고정되어 있지 않다. **다음 단계:** pilot 전에 hard stop을 사전등록한다: ID 누출, vocab/reader mapping 오류, 실제 CTC 실패, frozen-path parity 실패, 데이터·feature peak disk 초과, blank/NaN/비수렴, 또는 B0′ 재현의 설명되지 않는 큰 이탈이면 중단·수정한다. pilot의 inconclusive는 자동 full이 아니라, 안정성/누출 조건을 모두 통과하고 사전 정의한 실용 효과 범위를 배제하지 않으며 승인된 시간·자원 상한 안에 있을 때만 full을 고려하는 것으로 제한한다. run별 sec/step·RSS·peak disk를 재고, steal 발생 시 arm을 임의로 옮기지 말고 동일 설정으로 가장 안정적인 host를 선택한다. 5–7일은 이 측정 전까지 범위 추정으로만 보고하고, full 실행은 별도 승인 조건을 유지한다.

## Q8. 종합 권고

**판정:** **B**를 권고한다. 현재 v2는 pilot 그대로 시작할 상태는 아니지만, 새 P0 holdout 없이는 중단할 사유도 없다. **근거:** 새 eval_clean split의 수량·ID 교집합과 in-domain 한정 표기는 합리적이며, 제품 STT 경로가 별도라는 점에서도 이 연구의 효용은 내부 실험 질문에 한정된다. 다만 vocab/CTC·초기화·B3-nat estimand·gate 선택 규칙은 실제 pilot이 시작되기 전에 결정되어야 하고, disk 가능성은 대표 추출로 확인해야 한다. **다음 단계:** 아래 Must-fix 세 항목을 반영해 protocol/version을 freeze하고, test를 추가로 보지 않은 상태에서 data/feature/회귀 smoke check를 통과한 뒤 pilot을 시작한다. pilot 전에는 test 점수로 arm·vocab·threshold를 고르거나, 별도 natural 4h를 sampler-only control이라고 부르거나, 미측정 5–7일/용량을 확정 일정으로 약속하지 않는다.

## Must-fix — pilot 전 필수 3항목

1. **데이터·vocab·적격성 계약을 하나로 고정:** 2B vocab 확장과 1,101자 외 train clip 제외 중 무엇을 쓸지 결정하고, train-only build, OOV 처리, test OOV 오류 처리, reader output remap/blank index를 함께 freeze한다. 실제 feature frame으로 CTC 반복문자 조건을 재검사하고, eval_other/train/short/B3-nat와 test ID overlap을 audio 추출 전에 확인한다. 대표 shard와 feature의 peak disk/throughput을 재어 안전 여유까지 충족하지 않으면 다운로드·pilot을 중단한다.
2. **arm 간 비교 기준을 명세하고 parity를 통과:** B0′의 초기/최종 reader checkpoint 및 B1 “0-step equality”의 기준을 명시한다. 모든 arm의 동일한 vocab·문자 ID·초기 reader를 확정하고, LoRA B=0 회귀와 동일 frozen tower의 online/cached feature parity를 같은 샘플에서 검증한다. B3와 B3-nat은 같은 clip ID 집합에서 sampler만 바꾸거나, 별도 natural set을 유지할 경우 구성+sampler confound라고 재명명한다. optimizer step/노출량 기준과 sampler의 40/30/30 단위를 고정한다.
3. **확증 gate와 pilot stop rule을 사전등록:** 개선 부호, full 최소 실용 개선폭, bootstrap 단위·micro-CER 계산, B2/B3 winner의 dev 선택 및 test primary 지정, seed 43의 역할, pilot inconclusive 처리, 자원/시간 상한을 freeze한다. CER에서 “max”를 쓰지 말고 “dev에서 선택한 primary arm” 또는 “max improvement”를 구체적으로 쓴다. Full 최소 점추정 개선 1.0%p와 paired CI 하한 >0은 권고안이며, threshold를 바꿀 경우 test 전에 승인·고정한다.

## Optional improvements

- Dev의 기존 D-β 100과 신규 400을 따로 표기해 이전 노출이 결과에 얼마나 영향을 주는지 보인다.
- test 전체 CER 및 in-vocab subset CER를 모두 보고하되, subset은 보조로만 취급한다. 참조 문자 수, edit 수, micro/macro 정의와 OOV 오류 기여를 arm마다 같은 규칙으로 제공한다.
- 가능한 경우 두 seed를 후보 선택과 독립적으로 보고한다. seed 42만 test에 쓰면 결론을 그 학습 seed에 조건부인 결과로 한정한다.
- ≤4초 결과와 duration bin별 결과는 탐색적 분석으로 두고, 작은 bin별 수치에 별도 유의성 주장을 하지 않는다.
- FLEURS dev no-regression은 2A에서 이미 사용된 dev의 보조 지표라고 분명히 표시하고, 독립적인 외부 일반화 증거로 제시하지 않는다.

## 잘못된 전제 또는 추가 검증이 필요한 주장

- **vocab 정책 충돌:** 요청서와 plan §2.5는 train 6h+short로 새 vocab을 만든다고 하지만, plan §2.1은 2A의 1,101자 바깥 문자가 있는 Kspon train clip을 기본 제외한다고 한다. 구현 전 어느 정책이 기준인지 정리해야 한다.
- **B3-nat 해석:** 별도 natural 4h를 뽑는 설계는 B3와 데이터 조성이 다르므로 sampler-only 비교가 아니다. 같은 clip set을 쓰면 sampler contrast는 되지만 Kspon의 native length distribution control이라는 뜻은 아니다.
- **Bootstrap 표기:** 요청서·preflight는 speaker ID 부재로 utterance bootstrap을 말하지만 plan §5.2는 speaker-cluster paired bootstrap을 요구한다. 후자는 현재 입력에서 실행할 수 있다고 볼 근거가 없다. eval_clean의 “60명 화자” 주장도 이 preflight 자료로 검증되지 않는다.
- **CTC 완료 주장:** preflight는 오디오 추출·feature 계산을 하지 않았다고 적혀 있다. 따라서 chars+repeats > frames = 0은 실제 model output frame 검사인지 시간 추정인지 확인하기 전까지 실제 오디오의 CTC 적격률 100%로 해석하면 안 된다.
- **“sealed”의 범위:** eval_clean transcript와 split 후보를 preflight가 사용했으므로 test는 blind/접근 불가 test가 아니라 결과를 모델 선택에 쓰지 않는 절차적 holdout이다. 이 제한을 기록하고 접근·결과 확인을 통제해야 한다.
- **아직 입증되지 않은 overlap:** preflight 결과에는 dev/test 및 test/기존 D-β 100 중복 0이 있지만 eval_other/train/short/B3-nat와의 test ID 중복 검증 결과는 없다. 계획에 “확인 예정”이라는 문구를 결과 완료로 취급하면 안 된다.
- **수치 검산:** 3,000−10=2,990, 500+2,400+90=2,990, 1.0+1.4+0.8+0.8=4.0h, train ≤4초 0.17%+3.9%=4.07%≈4.1%, eval_other 27.6%+29.6%=57.2%, OOV 214/40,222=0.532%, 2,400−185=2,215는 서로 일치한다. 단, 시간·디스크·실제 CTC는 계산 일치만으로 실행 가능성이 검증되는 것은 아니다.
- **CER의 “max”:** CER 원값의 max는 더 나쁜 쪽이다. “최고 성능”을 뜻한다면 dev에서 선택하는 규칙과 test 후 선택 편향 통제를 문서화해야 한다.
- **일정:** phase 추정 범위의 합은 약 4.1–7.2일로 5–7일은 둥글린 전망이다. 이를 실측 일정이나 LoRA run의 검증된 runtime으로 표현하면 안 된다.

## 신뢰도

**Medium.** 문서 내부의 수량·정의·gate·설계 모순과 산술은 높은 확신으로 검토했으나, 실제 shard의 speaker 메타데이터·audio/feature frame·중복 ID·디스크 peak·LoRA 학습 속도는 아직 관측되지 않았다. 이 항목들이 확인되기 전에는 데이터 적격성, 인과 귀속, 일정에 대한 확신을 더 높일 수 없다.
