# Wave 2B + 2C-short v2 외부 검토 보고서 — w2b_2c_short_v2

**검토 모델:** GLM (z-ai/glm-5.3-flash, OpenRouter) — Hoplite 독립 외부 검토

**검토 일자:** 2026-11-04

**검토 대상:** `reports/EXTERNAL_REVIEW_W2B_2C_SHORT_V2_2026-11-04.md` (522줄, 23,449바이트 — 전체를 청크로 나눠 원문 그대로 직접 판독, 요약·발췌·이전 대화에 의존하지 않음)

**동기화 결과:** `git fetch origin` + `git pull --ff-only origin main` 성공, fast-forward `2cbd85e` → `e1d62803ef869bcddddd57951f2e3621365239d2` ("docs: record w2b_2c_short_v2 thread ids"). 요청서 기준 커밋 `1db2d0e`는 HEAD의 조상이며 `1db2d0e..HEAD`의 유일한 변경은 `threads.json` 추가라서 요청서 내용은 현재 HEAD에서도 그대로 유효하다.

**교차 검증에 사용한 자료(모두 직접 읽음):** `docs/plan_wave2b_2c_short_v2.md`(205줄), `reports/W2B_2C_SHORT_3AI_SYNTHESIS.md`(184줄), `reports/W2B_preflight.md`(48줄), `reports/W2A_lite_results.md`(142줄), `docs/decisions.md` D-066, `reports/provenance/W2B/preflight.json`, `data/wave2b/preflight/split_candidate.json`(구조·sha256 실측), `runner/w2b_preflight.py`(존재 확인), `git log 6b1d720..1db2d0e`(12커밋 — 요청서 §2.1의 커밋 목록 모두 존재·내용 일치).

**검증 한계(중요):** 동결 체크포인트(.pt), `data/wave1/manifest.jsonl`, `kspon_eval_other.jsonl`, Kspon 원본 zip, 6h feature 캐시는 레포에 커밋되어 있지 않아 실데이터 재검증이 불가능하다. 이 보고서에서 "불확실"로 표기한 수치는 이 한계를 반영한 것이다. 문서·아티팩트 수준에서 교차 검증 가능한 것(산술, 교집합, 해시, 문서 간 정합성)은 모두 검증했다.

**제약 준수:** 본 보고서 파일 생성 외에 어떤 파일도 수정·삭제하지 않았다. 서브에이전트·다른 모델은 사용하지 않았다.

---

## 0. 권장 결론

**B — 명시된 Must-fix를 반영한 뒤 pilot을 시작한다.**

이유: v2의 골격은 v1 대비 실질적으로 좋아졌다. B0′ 재학습·전 arm 공통 reader warm-start, dev 500/test 2,400/spare 90 분할(산술·교집합 검증 통과), test의 "Kspon in-domain sealed holdout" 표기 제한, 채택 판정(`max(B2,B3)` vs B0′)과 귀속 진단의 분리는 직전 3-AI 공통 Must-fix의 핵심을 정확히 반영했고, preflight는 실제로 split/OOV/CTC/화자 부재를 확인한 유의미한 산출물이다. 그러나 pilot 착수 전에 반드시 문서 수준에서 고쳐야 할 결함이 3개 남아 있다. (1) B3-nat의 정의가 같은 문서 안에서조차 두 가지로 서로 모순되며, 그 결과 B3−B3-nat의 "sampler 효과"라는 귀속 라벨은 정의에 따라 참이 되거나 거짓이 된다. (2) plan §2.1의 "1,101자 vocab 기준 OOV 클립 제외" 규칙이 "2B vocab을 train 6h+short에서 재구축"이라는 정책과 정면으로 상충한다 — 그대로 실행하면 vocab 재구축이 사실상 무효가 되고 구어체 클립 선택 편향이 생긴다. (3) pilot이 프로젝트를 멈출 수 있는 조건(중단 기준)과 full 채택의 절대 pp 최소값이 없어서, 문서 스스로 인정한 "미해결" 상태로 학습에 들어가게 된다. 이 세 가지는 코드나 데이터가 아니라 정의·사전등록의 문제이므로 설계 전체를 다시 만들어야 한다는 C까지는 아니다. D(새 P0 holdout 없이 중단)는 과하다 — in-domain holdout 표기로 주장 범위를 정확히 제한했기 때문이다.

---

## 1. Q1 — dev/test split과 test 재사용

①판정: split 설계는 대체로 타당하며 산술·교집합 검증을 통과했다. 다만 화자 차원의 리스크가 두 겹으로 남고, 그중 하나(train과 eval의 화자 분리 여부)는 문서가 다루지 않는다. ②근거: dev 500 + test 2,400 + spare 90 = 2,990 = 3,000 − 16초 초과 10건으로 분모가 정확히 맞고, duration bin별 합계(전체 1,440+783+537+187+43 = 2,990, dev 246+126+90+32+6 = 500, test 1,151+633+431+149+36 = 2,400, spare 43+24+16+6+1 = 90)도 `preflight.json`과 일치한다. `split_candidate.json` 실측 구조(seed 42, dev 500/test 2,400/spare 90)와 `preflight.json`의 `overlap_dev_test: 0`, `overlap_test_used: 0`, `overlap_dev_used: 100`도 요청서와 일치한다. 기존 D-β 100의 dev 포함은 test 자체를 오염시키지 않지만(test∩100=0), 이 100건은 과거 분석·평가에 이미 쓰인 발화라 dev 절대치에 낙관 편향을 남긴다. 완화 요인으로 모든 arm이 같은 2A F-C-concat reader로 warm-start하므로 편향이 arm 간 공유되어 상대 비교에 미치는 영향은 제한적이다. 화자 ID 부재로 duration 층화만 가능하다는 점은 정직하게 문서화됐고 "새 화자 일반화" 주장 금지 표기도 올바르다. 그러나 두 가지가 덜 다뤄졌다. (a) 요청서가 말하는 "eval_clean의 60명 화자"는 화자 ID가 없다는 전제와 함께 놓고 보면 출처가 AI Hub 등 외부 메타데이터뿐이며 본 검토에서는 검증 불가다. (b) 더 중요하게, short 4h로 들어올 Kspon train 발화의 화자가 eval_clean 화자와 겹치는지 프로젝트는 확인할 수 없다. 겹친다면 B2/B3의 "데이터 효과" 일부가 화자별 음향 적응(암기)일 가능성을 배제할 수 없다. ③다음 단계: (1) dev 500 전체와 별도로 신규 400건만의 secondary CER을 사전등록해 재사용 편향의 크기를 측정 가능하게 한다. (2) AI Hub 데이터셋 메타데이터·원논문으로 eval 화자 수와 train/eval 화자 분리 여부를 확인하고 결과를 limitations에 기록한다. 확인 불가면 "데이터 효과에 화자 혼입 가능성 있음"을 명시한다. (3) "in-domain sealed holdout" 표기와 test 1회 원칙을 유지한다. 새 P0 holdout 확보는 이 라운드에서 강제할 가치가 없다(비용 대비, 2,400규모 봉인 holdout이 이미 확보됨).

## 2. Q2 — B0′·reader warm-start·feature parity

①판정: 방향은 옳고 모든 arm이 동일 reader 초기화를 공유하는 구조는 내부 비교의 공정성을 만든다. 그러나 검증 규칙이 세 곳에서 불완전하게 정의되어 있어 그대로 구현하면 "확인했다"의 의미가 약해진다. ②근거: 첫째, "B1 0-step == B0′"(요청서 §4.1, plan §3)은 문구 그대로면 학습된 B0′ checkpoint와의 일치처럼 읽힐 수 있으나 실제로 성립하는 비교는 **학습 시작 전 초기화 상태**(2A reader warm-start + LoRA B=0 동결 타워)끼리의 일치뿐이다. 비교 대상·지표(고정 배치에서 CTC logits 최대절대차, dev CER 동일 여부)와 허용오차가 미정이다. 둘째, feature parity 허용오차가 미정이며(요청서도 "허용오차 명시"를 계획으로만 적음), fp32 on-the-fly vs fp32 cached면 상대 ~1e-4 수준이 현실적이지만 캐시를 fp16으로 바꾸면 허용오차 체계가 달라진다 — 디스크 결정(Q6)과 묶어 정해야 한다. 셋째, B0′ 자체의 학습 입력 경로(cached feature vs on-the-fly)가 어디에도 명시되지 않아 B0′(cached 가정)와 B1(on-the-fly) 사이 경로 차이가 epoch-0 체크로 잡히는지 불명확하다. 넷째, B0′가 2A seed42 0.20913에서 크게 벗어나는 경우 plan §3.1은 "기록하고 B0′ 기준으로 비교"라고만 하는데, gate가 상대적이라 방침은 맞지만 몇 %p까지 정상인지 임계값(예: 편차 1%p 초과 시 seed·파이프라인 재현성 진단 우선)이 없으면 판정이 매번 임의가 된다. 참고로 2A vocab이 1,101자인데 2B vocab을 재구축하면 reader CTC head 크기가 달라지므로, "모든 arm 동일 warm-start" 주장이 성립하려면 신규 행 초기화 규칙이 필요하다(Q4 연계, Must-fix 2). ③다음 단계: (1) epoch-0 체크를 "초기화 상태 일치"로 재정의하고 고정 샘플 배치에 대한 정량 허용오차를 사전등록한다. (2) parity unit test에 dtype·허용오차·고정 샘플·측정 지표를 명시하고 B0′↔B1 경로도 대상에 포함한다. (3) B0′는 B3와 같은 cached 경로로 통일할 것을 권장한다. (4) B0′ 편차 판정 규칙에 정량 임계값을 둔다.

## 3. Q3 — B3-nat의 정의 (이번 설계의 가장 큰 결함)

①판정: B3-nat이 **서로 다른 두 정의로 동시에 쓰여 있고**, 어느 쪽을 택하느냐에 따라 B3−B3-nat의 귀속 라벨("sampler 효과")이 참이 되거나 거짓이 된다. pilot 전에 반드시 하나로 확정해야 한다. ②근거: 요청서 §4.1 표와 §4.2("B3-nat: 10h natural sampler"), plan §2.2(56행 "10h natural sampler")는 **해석 A — B3와 같은 10h(6h+short 4h)에 natural sampler**다. 반면 요청서 §5.2("B3-nat: 별도 4h natural 후보", 산출물 `b3nat_4h.jsonl`), 요청서 §9.4, plan §1(23행 "Kspon 4h natural 길이 분포"), plan §3(111행 "별도로 natural로 선별"), plan §6 DoD(175행 "B3와 길이 분포만 다름"), D-066("Kspon 4h natural")은 **해석 B — 별도 natural 4h**다. 해석 A에서는 B3−B3-nat이 같은 데이터·다른 sampler이므로 순수 sampler 대조가 맞고, B3−B0′ = (B3−B3-nat) + (B3-nat−B0′)라는 분해가 성립한다(B3-nat−B0′ = "short 4h를 자연 샘플링으로 추가"한 데이터 효과). 해석 B에서는 B3−B3-nat이 데이터 구성과 sampler가 동시에 바뀌는 confound가 되어 현재 문서의 "sampler 효과" 라벨은 틀린 주장이 된다. 추가로 plan §3(111행)의 "B3의 4h와 가능한 한 같은 화자/도메인 범위를 쓰되 길이 분포만 다르게"는 화자 ID 부재가 확인된 지금 **실행 불가능한 약속**이다(선별 단계에서 화자 매칭을 할 수 없음). ③다음 단계: (1) 권장안은 **해석 A**다 — 귀속 분해가 성립하고, 별도 4h 선별 작업·디스크(+7.3GB 캐시)·Phase 1 추정 부담이 사라지며, "자연 길이 Kspon 4h로도 개선되는가"라는 도메인 질문은 이번 라운드 목표(데이터 효과 vs adaptation 효과)의 필수 조건이 아니기 때문이다. (2) A를 택하면 plan §1·§3(111행)·§6, 요청서 §5.2·§9.4, D-066 후속 기록의 표기를 전부 A로 통일하고 포기하는 도메인 질문을 limitations에 명시한다. (3) B를 유지하겠다면 B3−B3-nat 라벨을 "길이 타깃+sampler 결합 효과"로 수정하고 sampler 단독 귀속 주장을 금지하며 111행의 화자 매칭 문구를 삭제한다. 어느 쪽이든 pilot 착수 전에 하나로 고정한다.

## 4. Q4 — OOV·vocab

①판정: "상한" 프레이밍과 평가 측 OOV 정책은 타당하지만 **학습 데이터 쪽 OOV 규칙이 vocab 재구축 정책과 상충**해서 그대로 실행하면 재구축의 목적이 사라진다. ②근거: 요청서·preflight의 OOV 수치는 산술적으로 정확하다(전체 226/2,990 = 7.56%, dev 38/500 = 7.60%, test 185/2,400 = 7.71%, spare 3/90, 문자 261 = 43+214+4, test 214자/test 참조 40,222자 = 0.53%). "2A vocab 기준 상한이며 2B vocab 재구축 후 최종 OOV를 재측정한다"는 프레이밍, test에서 vocab을 확장하는 것을 leakage로 금지하는 원칙, in-vocab subset 2,215(=2,400−185) 보조 + OOV 문자 오류 처리 정책은 모두 옳다. 그러나 plan §2.1(48행)은 "Kspon train에서 1,101자 vocab에 없는 문자가 있는 클립은 **제외를 기본**으로"라고 하고 같은 문서 §2.5(88행)는 "2B vocab은 Kspon train 6h+short에서 새로 build"라고 한다. 제외 규칙대로 선별하면 1,101에 없던 문자는 short 4h에서 영원히 유입되지 않으므로 2B vocab은 사실상 2A vocab에 수렴하고 test OOV는 약 7.7%에 머문다. 더 나쁘게 preflight의 top OOV(밌 26, 껄 7, 쫌 7, 걍 6 등)가 정확히 Kspon 구어체 토큰이라 이 규칙은 "구어체 발화를 표본에서 걸러내는 선택 편향"이 된다 — 2C-short가 노리는 바로 그 도메인을 깎는 셈이다. ③다음 단계: (1) 1,101 기반 클립 제외 규칙을 폐지하거나 "전사 품질 필터(빈 전사·1자 이하·0.5초 미만·CTC frame 부적격)만 적용"으로 재정의한다. (2) 2B vocab 구성식을 명시한다 — 권장: `vocab(2B) = chars(6h train + short 4h)`로 하되 2A vocab(1,101)의 상위집합이 되도록 보장하고, reader CTC head 신규 문자 행의 초기화 규칙(예: warm-start 행 복사 + 신규 행 소규모 random init)을 사전등록한다. (3) short 선별 완료 후 최종 OOV 재측정(기존 계획 유지)과 OOV율·제외율 보고(DoD 이미 포함)를 승인 문서에 넣는다. (4) 사용자 승인 대기 중인 "OOV 정책"에 위 정합화가 포함되도록 한다.

## 5. Q5 — Gate·표본·주지표

①판정: 채택 판정과 귀속 진단의 분리 구조는 옳다. 다만 (a) full 채택의 절대 pp 최소값 부재(문서도 인정), (b) pilot의 중단 규칙 부재, (c) plan에 남아 있는 "speaker-cluster bootstrap" 잔재, 세 가지를 pilot 전에 고쳐야 한다. ②근거: `max(B2,B3)` vs B0′ 채택 + B2−B1/B2−B3 귀속 분리는 "B2>B1 & B2>B3 강제"보다 명백히 낫고 3-AI 종합과도 일치한다. 통계 규모로 보면 test 2,400(참조 약 40,222자)에서 paired utterance bootstrap의 CER 차이 표준오차는 대략 0.4~0.7%p로 추정되고(불확실 — 실측 필요), 절대 1%p 효과는 test에서 충분히 검출 가능하다. dev 500(참조 약 8,400자)에서는 표준오차가 0.7~1.1%p 수준이라 pilot의 "절대 1.0%p" 기준은 상당수가 INCONCLUSIVE가 될 것을 미리 알 수 있고, INCONCLUSIVE 밴드를 둔 것은 합리적이다. 그러나 현재 pilot 결과 분기는 "Go → full, INCONCLUSIVE → full"뿐이라 **pilot이 무엇을 중단시키는지 정의가 없다**(3-AI 종합의 "데이터 효과 미확인 시 B2/B1 보류" 규칙이 v2에서 사라졌다). dev 500 재사용(early stop + best epoch + pilot gate) 편향은 존재하지만 test 1회 원칙이 이를 통제하므로 허용 범위다. seed 42 단독 판정은 CI 기반이면 허용 가능하나 2A 실측에서 seed 간 CER 차이가 0.1%p 내외였으므로(0.20913 vs 0.208116) 승패가 ±0.5%p 이내로 좁아지는 경계 결과에서는 seed 43 확장이 필요하다. FLEURS no-regression +1.0%p는 192클립/7,861자에서 1%p ≈ 79자로 guardrail로서 적절하나, FLEURS dev 192도 2A arm 선택에 쓰였다는 재사용 사실이 있으므로 "모든 arm 공유 편향 아래의 상대 guardrail"임을 유지해야 한다. 마지막으로 plan §5.2(156행)가 아직 "**speaker-cluster** paired bootstrap 95% CI 하한 > 0"이라고 적고 있는데, preflight는 화자 ID 부재를 확인했고 요청서·preflight는 utterance bootstrap으로 대체한다고 정정했다 — plan의 미갱신 문구다. ③다음 단계: (1) full 채택 절대 기준을 "paired bootstrap 95% CI 하한 > 0 **AND** 점추정 절대 개선 ≥ 0.5%p"로 사전등록할 것을 권장한다(0 근처 noise 채택 방지; 1.0%p 유지도 가능하나 검출력과의 균형 메모를 남길 것). (2) pilot 분기를 완성한다 — 파이프라인 실패(parity 불일치, sec/step 초과, 디스크 초과) → 중단/수정, 데이터 가설 사망(B3−B0′가 음의 방향이며 CI가 0의 음측 배제) → 중단 또는 축소, 그 외 → full. (3) seed 43은 경계 결과 시 winner arm + B0′만 확장. (4) plan §5.2 문구를 "utterance-level paired bootstrap"으로 수정한다.

## 6. Q6 — 데이터·디스크·VPS

①판정: 계획의 뼈대(zip streaming + 선택 파일만 저장, B3/B3-nat reader-only의 VPS 분산)는 현실적이지만 검증 없이 진행하면 세 곳에서 터질 수 있다 — AI Hub 다운로드, 로컬 디스크 산술, 화자 프록시. ②근거: 첫째, preflight는 eval zip의 metadata만 읽었을 뿐 **train shard streaming은 아무것도 검증하지 않았다.** AI Hub 대용량 파일의 인증·일일 쿼터·HTTP range 지원 여부는 15GB × 5 shard(50211~50215, 각 14~15GB) 규모에서 실패 비용이 크다. shard당 약 200h 추정(전체 약 1,000h 기준, 불확실)이면 0–8s 풀이 shard 하나로 충분할 가능성이 높지만 shard별 duration 히스토그램은 미확인이므로 0–2초 1.0h 목표가 한 shard에서 채워지지 않을 가능성도 배제할 수 없다. 둘째, 디스크 산술이 요청서의 "빠듯하다"(§9.7)보다 나쁘다. 6h fp32 F-C 캐시 11GB(미검증 수치지만 전제로 수용)에서 10h는 약 18.3GB이고, dev/test/spare 특징(2,990클립 × 평균 3.126초 ≈ 2.6h → 약 4.8GB)을 더하면 **약 23GB > 여유 18GB**다. 해석 B(B3-nat 별도 4h)이면 +7.3GB로 약 30GB가 되어 로컬은 원천적으로 불가능하다. fp16으로 신규 캐시만 저장하면 해석 A 기준 약 17GB로 간신히 성립한다. 결정적으로 `preflight.json`의 `disk_free_gb`가 **null**로 기록되어 있어 "C: 여유 약 18GB"라는 수치는 provenance에 근거가 없다. 셋째, VPS eg2-2 20GB는 15GB zip 전체 저장과 10h 캐시의 병행이 불가능하므로 streaming 성공이 하드 전제다. 넷째, "화자당 10% 상한"의 세션/파일 프록시는 유일한 대안이 맞지만 그 프록시가 실제 화자 다양성을 커버하는지는 선별 후 파일명 접두사 분포로 검증해야 한다. ③다음 단계: (1) Phase 1의 첫 30~60분을 **feasibility spike**로 쓴다 — shard central directory 파싱, 샘플 10파일 range 추출, throughput 측정, duration 히스토그램 부분 스캔. 실패 시 fallback(전체 다운로드→선별→삭제, 또는 로컬 streaming)을 미리 정한다. (2) 캐시 dtype(fp16 여부)·위치(로컬/VPS)·삭제 대상·단계별 peak disk를 표로 사전등록하고 parity 허용오차와 연동한다(Q2). (3) `disk_free_gb`를 재측정해 provenance에 기록한다. (4) 해석 A 채택 시 B3-nat 별도 4h 선별 자체가 사라져 Phase 1 추정이 내려간다(Q3 연계).

## 7. Q7 — 일정·중단 기준

①판정: "5~7일"은 낙관적이며 **두 문서의 일정 추정이 서로 모순**되고 LoRA arm의 학습 속도는 전무 실측이다. ②근거: 요청서 §5.7의 합산은 short 3~5시간 + 구현 1.5~2.5일 + pilot 0.5~1일 + full 1.5~2.5일 + test·보고 0.5~1일 = 4.25~7.25일인데, plan §7의 단계별 합산은 1+1+1+1+1+(3~5)+1.5 = **9.5~11.5일**로 2~4일 차이가 난다(특히 full — 요청서 1.5~2.5일 vs plan 3~5일. 로컬-only 가정이면 요청서도 +1~2일로 3.5~4.5일이 되어 plan과 합류한다). 더 근본적으로 이 프로젝트는 **CPU 학습**(plan §4 "AMP 없음 (CPU)", threads 6)이고 2A의 322~356초/epoch는 cached feature 기반 reader-only 실측이다. B1/B2는 타워 forward+backward를 on-the-fly로 돌려야 하는데 sec/step 실측이 전무하다. CPU에서 타워 forward(+10–11층 backward)가 클립당 1~3초라면 B2(10h, 약 7,500클립)의 pilot 3 epoch는 하루 안에 안 끝날 수 있고 full 12 epoch는 B2 단독으로 수십 시간에 이른다(불확실 — "epoch 322~356초/20 epoch"라는 표기 자체도 단위가 모호하다). 즉 "구현이 critical path이며 학습 시간이 아니다"(§5.7)라는 전제는 LoRA arm에 대해서는 아직 근거가 없다. 중단 기준도 없다 — 현재 문서는 INCONCLUSIVE → full 확장만 있고 무엇이 프로젝트를 멈추는지(3-AI 종합의 보류 규칙 포함) 사전등록돼 있지 않다. ③다음 단계: (1) pilot 첫 시간에 B1의 sec/step·RSS를 실측하고 그 값으로 full 일정을 재산출한 뒤 두 문서의 일정 표기를 하나로 통일한다. (2) 슬립 트리거를 사전등록한다 — 예: 구현 4일 초과 시 pilot에서 B1 생략(B1은 채택 gate에 불필요한 귀속 진단이므로 가장 먼저 잘라도 된다), short 수율 부족 시 두 번째 shard 이어받기 또는 목표 완화, VPS steal 재발 시 B3부터 로컬 fp16 캐시로 이동. (3) 중단 기준 3종을 Gate에 사전등록한다 — 파이프라인 실패, 데이터 가설 사망(Q5 정의), 자원 한도(디스크/시간) 초과. (4) 전체 일정 표기에 "+2일 버퍼"를 명시하고 "빠르면 4일" 표기는 근거 부족이므로 제거할 것을 권장한다.

## 8. Q8 — 종합 권고

①판정: **B — Must-fix 반영 후 pilot 시작.** ②근거: 설계 골격과 preflight는 승인할 수 있는 수준이지만 Q3(B3-nat 정의 이중성 — 귀속 라벨의 참/거짓을 가름), Q4(OOV 클립 제외 vs vocab 재구축 상충 — vocab 재구축 무효화 + 구어체 선택 편향), Q5(pilot 중단 기준·full 절대 pp 최소값 부재 — "미해결" 상태로 학습 진입)의 세 결함은 전부 pilot 실행의 해석 가능성을 훼손하므로 비용이 몇 시간 단위의 문서 작업인 만큼 먼저 고치는 것이 합리적이다. 코드 수정·데이터 다운로드 준비는 이 세 가지와 병렬로 시작할 수 있으나 **short 선별 기준과 B3-nat 선별은 정책 확정 전에 실행해서는 안 된다**(선별 규칙이 곧 데이터가 되므로 재선별 비용이 크다). ③다음 단계 및 **pilot 전에 하지 말아야 할 일**: (i) test 2,400의 audio 추출·평가 금지(기존 원칙 유지 — split 후보만으로는 sealed 여부가 완성되지 않았다). (ii) OOV 정책 확정 전에 1,101자 기반 클립 제외 실행 금지. (iii) B3-nat 정의 확정 전에 `b3nat_4h.jsonl` 선별 금지. (iv) pilot 실측(sec/step·parity·disk peak) 전에 full 5-arm 12-epoch 착수 금지(기존 원칙 유지). (v) FLEURS test 재사용 금지, eval에서 vocab 확장 금지(기존 원칙 유지). (vi) 사용자 승인 없이 Gate 수치(절대 pp 최소값 등)를 바꾸지 않는다 — 사전등록 후 승인받는다.

---

## 9. Must-fix (pilot 전 반드시 수정 — 3개)

1. **B3-nat 정의를 하나로 확정하고 전체 문서에 일관 적용.** 권장은 해석 A(= B3와 동일한 6h+short 4h 10h에 natural sampler)다. 이 경우 B3−B3-nat = 순수 sampler 효과, B3-nat−B0′ = "short 4h 추가(자연 샘플링)" 효과로 귀속 분해가 성립한다. 해석 B(별도 natural 4h)를 유지하려면 B3−B3-nat의 라벨을 "sampler 효과"에서 "데이터 구성+sampler 결합 효과"로 수정하고, plan §3(111행)의 실행 불가능한 화자 매칭 문구를 삭제하며 B3-nat−B0′를 "도메인/길이 대조"로만 해석한다. 요청서 §4.1/§4.2 vs §5.2/§9.4, plan §1/§2.2 vs §3/§6, D-066 간 모순을 모두 정리한다.
2. **OOV·vocab 정책 정합화.** plan §2.1(48행)의 "1,101자 vocab 기준 OOV 클립 제외(기본)"를 폐지하거나 재정의하고, 2B vocab 구성식(chars(6h+short), 2A vocab 상위집합 보장), reader CTC head 신규 행 초기화 규칙, 최종 OOV 재측정 시점(short 선별 후), in-vocab 2,215 보조 지표 + OOV 문자 오류 처리를 하나의 승인 문서로 사전등록한다. 이것이 없으면 "모든 arm 동일 reader warm-start" 주장도 head 크기 문제로 불완전해진다.
3. **Gate 완결 — pilot 중단/확장 기준과 full 채택 절대 pp 최소값의 사전등록.** pilot 분기(파이프라인 실패 → 중단/수정, 데이터 가설 사망 → 중단/축소, 기타 → full)와 full 기준(권장: CI 하한 > 0 AND 점추정 ≥ 0.5%p)을 문서에 박고, plan §5.2의 "speaker-cluster paired bootstrap"을 utterance bootstrap으로 정정한다. 사용자 승인 절차를 거쳐 D-066 계열로 기록한다.

## 10. Optional improvements (있으면 좋은 것)

- **feasibility spike(30~60분):** AI Hub shard streaming(인증·range·throughput)과 shard duration 히스토그램 부분 스캔을 Phase 1 최우선으로 실행. 실패 시 fallback 사전정의.
- **캐시 fp16 표준화 + 단계별 disk peak 표:** 10h fp32 캐시(약 18.3GB) + eval 특징(약 4.8GB)은 여유 18GB를 초과한다. fp16 캐시 시 해석 A 기준 약 17GB로 성립. parity 허용오차와 연동.
- **dev 신규 400건 전용 secondary CER 사전등록:** D-β 100 재사용 편향의 크기를 측정.
- **B1을 full에서도 조건부로 유지:** 채택 gate에 불필요한 귀속 진단이므로 일정 압박 시 가장 먼저 제거. 요청서의 pilot "B1(조건부)" 표기를 full에도 확장.
- **≤4초 샘플러 비중 재검토:** balanced sampler의 ≤4초 40%는 test 2,400의 ≤4초 74.3%(1,151+633/2,400)에 여전히 크게 못 미친다. 방향은 맞으나 "balanced"라는 명칭이 주는 인상과 실제 격차를 보고서에 명시하고, pilot의 ≤4초 bin 방향이 부정적이면 50~60% 상향을 후속 옵션으로 검토.
- **pilot LoRA arm 2 epoch 옵션:** sec/step 실측 전까지 pilot 3 epoch가 B2에서 하루를 초과할 수 있다. INCONCLUSIVE 기본값이라 2 epoch로 시작해도 결론 방향은 같다.
- **화자 메타데이터 확인:** AI Hub 메타데이터·원논문으로 eval 화자 수("60명" 검증)와 train/eval 화자 분리 여부 확인 → limitations 기록.
- **문서 소소 정리:** plan §2.2(54행) "short 4개" → "short 4h" 오기, 요청서 §3.1 F-A′ 0.222364는 1,748/7,861 = 0.222361(표기 미세 오차), 요청서 §5.7 "epoch 322~356초/20 epoch"의 단위 명확화, 3-AI 종합의 공통 필수 수정은 6개 불릿을 요청서가 7건으로 재분류한 것임을 표기.

## 11. 잘못된 전제 / 검증이 필요한 것

1. **split 후보 sha256 불일치(사실과 다름).** 요청서 §4.4(298행)는 `data/wave2b/preflight/split_candidate.json`의 sha256을 `25eb37f6...d680deb`라고 적었지만 실측은 `6805a8de071067502e421c0da96257eaea6ee7b5f2ec6607f51360b885b515f0`이며 `5170404`, `1bb8df0`, `1db2d0e`, HEAD **어떤 커밋 버전과도 일치하지 않는다**(전 커밋에서 동일 해시). 오기이거나 커밋되지 않은 다른 버전을 지칭한다. 파일 내용 자체(500/2,400/90, seed 42)는 요청서와 일치하므로 데이터 훼손으로 보기는 어렵다.
2. **plan §5.2(156행) "speaker-cluster paired bootstrap" — 사실과 다른 미갱신 문구.** preflight가 화자 ID 부재를 확인했고 요청서·preflight는 utterance bootstrap으로 정정했다.
3. **plan §2.1(48행) OOV 클립 제외 규칙 — vocab 재구축 정책(§2.5, 88행)과 상충.** 실행 시 2B vocab 재구축이 사실상 무효가 되고 구어체 선택 편향 발생(Q4).
4. **B3-nat 정의의 문서 내·문서 간 이중성.** 요청서 §4.1/§4.2(10h natural sampler) vs 요청서 §5.2/§9.4(별도 4h), plan §1/§2.2(10h natural) vs plan §3/§6(별도 natural 4h), D-066("Kspon 4h natural"). Q3 참조.
5. **"C: 여유 약 18GB" — provenance 미기록.** `preflight.json`의 `disk_free_gb: null`. 수치 자체는 수동 관측으로 보이며 재측정·기록이 필요하고, 디스크 산술(약 23GB 필요)로 볼 때 여유 판단도 낙관적(Q6).
6. **"eval_clean의 60명 화자" — 검증 불가.** 화자 ID가 .trn·파일명에 없다는 것이 확인된 이상 이 수치의 유일한 출처는 외부 메타데이터다. AI Hub 메타데이터로 확인 필요.
7. **"B1 0-step == B0′"의 비교 대상 모호.** 학습된 B0′와의 일치로 읽히면 거짓 명제가 된다. 초기화 상태 비교로 재정의 필요(Q2).
8. **일정 추정의 문서 간 모순.** 요청서 §5.7 합산 4.25~7.25일("5~7일") vs plan §7 합산 9.5~11.5일. "빠르면 4일"은 근거 부족. LoRA arm CPU sec/step 무실측(Q7).
9. **"구현이 critical path이며 학습 시간이 아니다"(§5.7) — 미검증 전제.** B1/B2의 on-the-fly CPU 타워 학습 비용에 대한 실측이 없다.
10. **요청서 §3.1 F-A′ 0.222364 — 소소한 계산 오차.** 1,748/7,861 = 0.222361(W2A 결과 문서는 0.22236로 표기). 결론에 영향 없음.
11. **"2A epoch 322~356초/20 epoch, feature extraction 2,963클립 467.7초"(§5.7) — 본 검토에서 원출처 미확인.** `W2A_lite_results.md`에는 이 수치가 없다. 다른 로그/문서 출처로 추정되며 단위 표기도 모호하다.
12. **Kspon train(short 4h)과 eval_clean의 화자 분리 여부 — 미확인.** 겹친다면 B2/B3 데이터 효과에 화자 혼입 가능성. 프로젝트가 데이터만으로 확인 불가능하므로 외부 메타데이터 확인 또는 limitations 명시 필요.
13. **6h feature 11GB, test 참조 40,222자 등 데이터 기반 수치 — 레포에 데이터가 없어 독립 재검증 불가.** 문서 간 정합성은 확인됨.

## 12. 산술·분모 검증 결과 (가능한 범위 전수 확인)

- **분할:** 3,000 − 10(16초 초과) = 2,990. 500+2,400+90 = 2,990 ✓. duration bin 합계: 전체 1,440+783+537+187+43 = 2,990 ✓, dev = 500 ✓, test = 2,400 ✓, spare = 90 ✓ (요청서 §4.4 = preflight.json 일치).
- **교집합:** `split_candidate.json` 실측 dev 500/test 2,400/spare 90, seed 42. `preflight.json` overlap_dev_test=0, overlap_test_used=0, overlap_dev_used=100 ✓. 단, 문서 기재 sha256은 불일치(위 11.1).
- **OOV:** 226/2,990 = 7.558% → 7.56% ✓. dev 38/500 = 7.60% ✓. test 185/2,400 = 7.708% → 7.71% ✓. spare 3/90 = 3.33% ✓. 38+185+3 = 226 ✓. 문자 43+214+4 = 261 ✓. 214/40,222 = 0.532% → 0.53% ✓(40,222자는 원데이터 미보관으로 문서 수치 수용).
- **in-vocab subset:** 2,400 − 185 = 2,215 ✓ (요청서 Q4/DoD).
- **CER 재계산:** F-C-concat 1,644/7,861 = 0.209134 ✓. F-A′ 1,748/7,861 = 0.222361(문서 0.222364, 오차 3e-6) ≈ ✓. F-B 1,724/7,861 = 0.219311 ✓. F-C-softmax 1,746/7,861 = 0.222109 ✓. 차이 1.323%p, 상대 5.95% ✓. seed43 (0.2233−0.208116)/0.2233 = 6.80% ✓. Kspon eval_other 23,508/66,893 = 0.351437 → 0.35143 ✓(평가 2,962/3,000과 특징 추출 2,963의 차이는 skip 1건으로 정합). FLEURS test 3,126/13,297 = 0.235094 ✓.
- **short 4h 목표:** 1.0+1.4+0.8+0.8 = 4.0h ✓ (25/35/20/20% × 4h).
- **CP-D2 분해:** train ≤4초 0.17%+3.9% = 4.07% → "4.1%" ✓. eval_other ≤4초 27.6%+29.6% = 57.2% ✓. Kspon 비중 합계 100.0% ✓. ≥12초 28.6−23.1 = 5.5%p ✓.
- **일정:** 요청서 §5.7 구간 합산 4.25~7.25일 — "5~7일" 표기는 구간을 벗어나지 않지만 plan §7 합산(9.5~11.5일)과 모순(위 11.8).

## 13. 신뢰도

**medium.** 근거: (1) 요청서 522줄 전수와 지원 문서 4종, decisions D-066, preflight provenance, split 후보 파일을 직접 읽고 산술·교집합·해시·문서 간 정합성을 검증했다 — 문서 수준 결함(B3-nat 이중 정의, OOV 규칙 상충, sha 불일치, speaker-cluster 잔재)은 직접 확인한 사실이다. (2) 반면 오디오·체크포인트·manifest·feature 캐시가 레포에 없어 실데이터 기반 수치(6h 11GB, 여유 18GB, test 참조 40,222자, 60명 화자, shard 구성)는 독립 검증이 불가능하고, LoRA arm의 CPU 학습 속도와 AI Hub streaming 가능성은 전무 실측이라 일정·디스크 판단에 불확실성이 크다. (3) 권장 결론 B 자체는 이 불확실성 아래에서도 안정적이다 — 세 Must-fix는 문서 작업이고 설계 골격에 대한 반대 근거는 발견되지 않았다.
