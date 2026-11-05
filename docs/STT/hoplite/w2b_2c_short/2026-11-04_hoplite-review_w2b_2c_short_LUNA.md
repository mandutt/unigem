# Wave 2B + 2C-short 독립 설계 검토 — LUNA

- 검토일: 2026-11-04
- 검토 요청: `docs/STT/reports/EXTERNAL_REVIEW_W2B_2C_SHORT_2026-11-04.md` (전체 368행)
- 동기화: `git fetch origin` 성공; `git pull --ff-only origin main` 성공(Already up to date)
- 동기화 후 HEAD: `81d58ed34f13b06d2f13edd49d89a37a80323d0f`
- 요청서 기준 커밋: `6b1d720` (검토 시 현재 HEAD와 다름)
- 근거 문서: `docs/STT/plans/plan_wave2b_2c_short.md`, `docs/STT/reports/W2A_lite_results.md`, `docs/STT/reports/W2A_lite_cp_d2_lite.md`
- 범위: 문서 검토만 수행. 코드 수정, 다운로드, 학습, 신규 test 평가를 하지 않음.

## 1. 권장 결론

**A — 4h short + 4-arm 설계를 조건부로 권고한다.** LoRA와 데이터 효과를 분리한다는 목적에는 2×2 factorial이 맞고, B3를 생략한 B는 데이터 단독 효과와 상호작용을 알 수 없으므로 더 저렴하더라도 핵심 질문에 답하지 못한다. 다만 현재 문서 그대로의 승인·실행은 권하지 않는다. B0를 재학습 없는 기존 checkpoint로 두는 비교 불일치, B3/B1/B2 간 feature 경로 차이, speaker-level 독립성과 test 사용 이력, 샘플러의 실제 반복 노출, 미실측 CPU·디스크 계획을 먼저 고쳐야 한다. 모델 학습에 앞서 작은 데이터/throughput pilot으로 적격 데이터량과 시간·메모리를 재고, 기준을 통과할 때만 4h 및 full run으로 진행한다. eval_clean 2,900은 미사용 utterance split으로는 쓸 수 있지만, eval_other와 동일 코퍼스·60명 화자를 공유하고 eval_other 분석이 설계에 쓰였으므로 “독립적인 외부 test”가 아니라 “새로 봉인한 Kspon in-domain holdout”으로만 보고한다. 외부 일반화 주장이 필요해지면 새 P0 holdout을 별도로 확보한다.

## 2. Q1–Q8

### Q1. Arm 설계
B0/B1/B2/B3는 tower adaptation(없음/LoRA) × 추가 short data(없음/있음)의 2×2 구조이므로 네 arm 모두 필요하다. 그러나 계획의 B0는 기존 F-C-concat checkpoint이고 B1/B2는 LoRA와 reader를 새로 학습하므로 B1−B0에는 reader 재학습·optimizer·step 수 효과가 섞인다. B3도 frozen-feature/reader-only 경로여서 B2와 실제 입력 경로가 다를 수 있다. 동일한 초기 reader, vocab, seed, optimizer, sampler 정의 및 업데이트/프레임 예산을 맞춘 네 cell을 만들어야 한다(기존 B0는 참고 baseline으로 함께 보고). feature cache와 online 추출은 고정 batch에서 수치 동등성을 확인한다. 주효과·상호작용 대비를 보고하고 B2>B1 및 B2>B3를 단일 “최고 arm” 조건으로 강제하지 말 것: 이는 상호작용/주효과를 대체하지 못하며 과도하게 엄격할 수 있다. B3를 빼면 “데이터 효과”는 LoRA가 있는 조건에서만 추정된다.

### Q2. Short 데이터 규모·분포
4h의 25/35/20/20 분배는 짧은 구간을 보강하는 탐색적 안으로는 가능하지만, 비율의 단위가 오디오 시간인지 utterance 수인지 명시해야 한다. CP-D2의 4.1%, 57.2%, 27.6%는 발화 분포로 제시된 값인데 4h 시간 분배와 직접 비교할 수 없고, 전체 sampler의 ≤4초 40%도 test의 ≤4초 57.2%보다 낮으며 0–2초의 최종 학습 비중은 정해져 있지 않다. bin별 utterance 수, 오디오 시간, transcript 문자 수, sampling 확률과 loss/frame 가중치를 함께 기록하고 목표는 같은 단위로 정한다. 먼저 2h로 수집·필터 이후 충분한 unique clip/speaker가 남는지와 throughput을 확인한 뒤, 연구 질문상 필요한 경우에만 4h로 확장한다(6h 증량은 현재 근거가 없음). 단순 파일 복제 여부와 별개로 가중 샘플링은 같은 clip의 재노출을 늘린다. replacement 여부, epoch 정의, clip별 예상 노출 횟수, optimizer update 수를 사전 정의해 반복 노출 과적합을 확인한다. ≤0.5초 및 1자 이하 제외로 생기는 선택 편향과 test에 대한 적격 coverage도 수치화한다.

### Q3. Test 타당성
eval_clean 2,900은 요청서상 dev 100 ID를 제외한 새 utterance split이므로, manifest·오디오 hash·정규화 transcript 기준 중복이 없고 checkpoint 선택 후 1회만 열면 동일 corpus 내 잠금 holdout으로는 타당하다. 그러나 eval_other 결과의 길이별 분석으로 실험 가설을 정했고 두 split이 같은 60명을 공유하므로 독립 speaker/domain test는 아니다. dev 100은 D-β에서 이미 사용됐고 다시 early stopping에 쓰면 추가 선택 편향이 생긴다. dev/test 간 speaker 겹침 및 기존 6h/short train 전체의 ID·speaker·near-duplicate 겹침 검증이 필요하다; 요청서의 ID 중복 0만으로는 충분하지 않다. test 결과는 “Kspon eval_clean in-domain holdout”으로 한정하고, 넓은 일반화 주장을 하려면 별도 P0 corpus 또는 미노출 speaker holdout을 추가한다. FLEURS test 재사용 금지는 옳고, FLEURS dev는 이미 2A에서 여러 arm 선택에 쓰였으므로 보조 진단으로만 취급한다. 별도 holdout은 현재 실험 진행의 필수 선결조건은 아니지만, 독립 일반화 주장을 위한 조건이다.

### Q4. 모델·LoRA
10–11층 rank 8/alpha 16은 제한된 예산에서 시험할 수 있는 가설이나, 제공된 근거만으로 최적이라고 검증되지는 않았다. 0-based/1-based layer 번호와 실제 모델 revision, 8개 target module 일치 여부, trainable parameter 수를 명시하고 LoRA B=0 초기화 시 고정 batch에서 baseline 출력이 동일한지·gradient가 허용 대상에만 흐르는지 확인한다. F-C-concat은 2A에서 선택된 입력이므로 이번 비교에서는 고정하는 것이 공정하며 F-A′, layer 수, attention/FFN 조합을 test 결과로 추가 탐색하지 않는다. 6/8층 tap은 LoRA 적용 전이고 10/11 tap은 적용 후이므로 각 tap의 정상 gradient/feature 경로도 확인해야 한다. B3의 precomputed feature와 B1/B2의 on-the-fly mel은 extractor revision, resampling, padding mask, normalization, dtype, truncation, eval/train mode가 완전히 같아야 한다. wordpiece head 제외는 범위 통제상 합리적이며 별도 가설로 남긴다.

### Q5. Gate
5/8% 및 10/10% 상대 개선은 근거가 제시되지 않은 임계치다. 35%대 CER에서 상대 10%는 약 3.5%p 수준이지만 새 eval_clean의 B0 기준 CER은 아직 UNVERIFIED이므로 이를 현실적/과도하다고 단정할 수 없다. corpus CER의 절대 %p 차이를 주지표, 상대 개선을 보조 지표로 사전 지정하고 실용적 최소 효과와 CI 산출법을 함께 고정한다. n=100 전체 CI는 참고로 쓸 수 있어도 ≤4초 bin의 표본 수와 speaker 군집을 고려하면 안정적인 확증 근거가 아닐 수 있다. 동일 utterance 쌍의 오류를 유지하는 paired bootstrap을 쓰되 speaker 단위 cluster resampling을 우선하고 bin별 n·speaker 수 및 CI를 함께 보고한다. 동일 dev에서 early stopping, gate, 반복적인 pilot 결정을 모두 하면 CI가 낙관적으로 변하므로 epoch 선택과 최종 dev gate를 분리하거나 pilot에서 epoch를 고정한다. 2,900 test의 10% gate는 사전에 고정할 수 있지만 test를 본 뒤 모델·전처리·threshold를 바꾸지 않고 B0와 사전 선택된 단일 B2 checkpoint의 paired 결과만 한 번 보고해야 한다.

### Q6. 누락된 confounder
우선 보완할 것은 기존 6h를 포함한 전체 train/dev/test 간 speaker 및 near-duplicate 누출, dev/test의 speaker 공유, short 선별로 인한 주제·대화자·녹음 조건·전사 품질 변화다. raw PCM의 byte truncation, sample rate/resample, silence/boundary 처리, duration bin 경계, 16초·0.5초 exclusion, transcript cleaning의 적용 전후와 수작업 QA를 고정·기록한다. 짧은 발화에서는 CTC 출력 frame 수(실제 subsampling 후)와 target 길이 및 반복 문자의 blank 요구량을 검사해 불가능/경계 사례와 제외율을 보고한다. variable-length padding과 attention/input mask, batch sorting, loss normalization이 길이별 gradient를 바꾸지 않는지 검증한다. B3 cached features와 B1/B2 online extraction의 동등성, tower eval/dropout, 모델·processor hash를 확인한다. 한 seed는 탐색 결과일 뿐이므로 seed 42만으로 재현성을 주장하지 말고, 계산이 허용될 때 최소 추가 seed를 둔다. worker/thread·결정성·resume state와 평가 coverage도 provenance에 남긴다.

### Q7. 비용·현실성
7–10일과 full B1/B2/B3 3–5일은 현재 자료로는 UNVERIFIED다. 100-step pilot은 full epoch의 throughput, feature extraction/I/O, checkpoint 저장, 12 epoch 및 조기종료 시간을 대표한다고 볼 증거가 없고 “step 5초”가 microbatch인지 optimizer update인지도 불명확하다. 예시 데이터 크기와 실제 step/epoch, 세 arm 별 처리량, peak RSS·swap, 추출·평가 시간을 측정해 재산정해야 하며 측정 전 full-run 약속을 해서는 안 된다. 현재 19GB는 계획상의 25GB보다 적다. 14–15GB archive뿐 아니라 압축 해제본, audio/feature cache, checkpoint, 임시 파일의 peak 공간이 필요할 수 있으므로 25GB가 충분한지도 UNVERIFIED다. 다운로드 전 비파괴적인 용량 산정과 여유 공간 확인을 하고 사용자 데이터를 삭제하지 말며, 2h pilot 종료 기준을 실제 elapsed-time·RSS로 정한다. CPU-only 실측 결과가 3–5일을 넘으면 축소 실험/early stop을 택하고 VPS로 우회하지 않는다.

### Q8. 종합 권고
선택지는 **A**다. 2B(LoRA)와 2C(short data)를 모두 판단하려면 B3가 있는 matched 4-arm factorial이 유일하게 목적에 부합한다. 다만 승인 대상은 “현재 문서 그대로의 4h/full run”이 아니라 위 Must-fix를 반영한 단계적 A여야 한다: 먼저 data/feature/throughput preflight와 제한된 pilot으로 2h 및 4h 후보의 고유 clip·speaker·반복노출·실제 비용을 확인하고, 네 arm의 비교 조건을 맞춘 뒤 4h full run 여부를 결정한다. 테스트는 같은 Kspon split의 내부 holdout이라고 한정하고, 결과를 보고 gate를 완화하거나 재시도하지 않는다. 독립 외부 일반화가 목적이라면 E의 새 P0 holdout을 그 주장에 한해 추가한다.

## 3. Must-fix

1. **비교 가능한 factorial로 재정의:** 재학습 없는 B0는 historical reference로 분리하고, 실험용 2×2의 reader 초기화·학습 조건·데이터 노출/step budget을 맞춘다. B3 cached-feature 대 B1/B2 online 경로의 수치 동등성 검증을 DoD에 추가하고, factorial contrasts/interaction을 사전 지정한다.
2. **Split·누출·주장 범위 고정:** 100 dev와 2,900 test, 기존 6h, short data에 대해 ID·speaker·오디오 hash/near-duplicate 검증을 한다. D-β 사용 dev는 재사용된 dev임을 표시하고 독립 test로 부르지 않는다. 2,900은 “동일 Kspon corpus의 sealed in-domain holdout”으로 제한하며, 외부 일반화가 목표라면 별도 미노출 P0/speaker holdout을 확보한다.
3. **실측 가능한 data/compute gate:** sampler 목표 단위를 utterance/loss contribution 기준으로 명시하고 replacement·노출 횟수·CTC 적격률을 기록한다. 2h preflight에서 실제 per-step 정의, epoch 처리량, peak disk/RSS, feature caching 시간을 재고 그 결과에 따라 4h/full 진행 여부를 결정한다. 현재 디스크와 일정은 검증 전 미확정이다.

## 4. Optional

- FLEURS ko dev는 결과표에 포함하되, 2A에서 이미 모델/입력 선택에 사용된 보조 진단으로만 해석한다.
- 동일 speaker를 cluster로 한 paired bootstrap과 utterance 단위 paired CER 차이를 함께 제시하고, 전체 CER·길이별 CER·coverage/제외 수·빈 출력·vocab coverage를 보고한다.
- 최소 2개 seed 결과를 확보할 수 없다면 단일 seed를 탐색적 결과로 명시한다; 여러 seed를 test에 걸쳐 탐색하지 않는다.
- 4h의 0–2s 및 2–4s 분할은 test의 **utterance 수 분포**와 별도 비교하고, 전사 문자 수/발화 수/총 오디오 시간 각각의 표를 제공한다.

## 5. 잘못된 전제 또는 검증이 필요한 주장

- **“eval_clean 2,900은 독립 test”**: utterance ID 기준으로 미사용일 수는 있지만 eval_other와 같은 Kspon 코퍼스·60명 화자를 공유하고, eval_other 오류 분석이 실험 설계에 사용됐다. 독립 외부 또는 speaker-independent benchmark라는 표현은 부정확하다.
- **“B2−B1은 데이터 효과, B2−B3는 LoRA 효과만 반영”**: 초기 reader, 학습/샘플러 budget 및 cached 대 online feature path가 일치하지 않으면 성립하지 않는다. 현재 계획의 동일성은 UNVERIFIED.
- **“4h 데이터 비율/≤4초 sampler가 test 분포를 대표”**: 4h 비중은 시간 기준일 수 있고 test 57.2%는 발화 기준이다. 단위와 최종 0–2초 기여도가 정해지기 전에는 비교할 수 없다.
- **“2A-lite 5.95% 개선이 이번 LoRA/short-data 효과를 뒷받침”**: 이는 FLEURS dev에서 두 입력 표현을 비교한 결과다. seed42/43 재현은 유용하지만 이번 Kspon 효과나 4-arm 효과 크기를 보장하지 않는다.
- **“100 dev의 CI와 100-step pilot이 gate·full-run feasibility를 검증”**: small-bin 표본/화자 군집, 반복적인 dev 선택, pilot의 step 정의·epoch coverage가 불명확하다.
- **“25GB와 7–10일이면 충분”**: 압축 해제·cache·checkpoint의 최대 사용량과 full-run throughput/RSS 실측이 제공되지 않아 UNVERIFIED.

## 6. 신뢰도

**Medium.** 핵심 판정은 요청서와 인용된 설계·2A-lite/CP-D2 결과 문서에 있는 설계 및 요약 수치에 근거한다. 데이터 manifest의 실제 교집합, speaker 분포, sampler 구현, feature 값 동등성, 학습 처리량·peak disk/RSS는 실행·원자료 검증을 하지 않았으므로 UNVERIFIED이며, 이 검토는 이들을 검증했다고 주장하지 않는다.
