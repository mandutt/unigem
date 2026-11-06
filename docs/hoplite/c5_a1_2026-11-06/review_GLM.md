# Hoplite 독립 검토 — F5 A1 T5Gemma2 LoRA와 EG2→T5 bridge (모델: GLM 5.3 Flash, reasoning=max)

- 날짜: 2026-11-06
- 검토 대상: `reports/EXTERNAL_REVIEW_C5_A1_2026-11-06.md` **전문 561행**(청크 분할로 전부 대조, 요약·발췌에 의존하지 않음)
- 동기화: `git fetch origin` + `git pull --ff-only origin main` → **Already up to date**, HEAD `834d598e2fb6c003419713156de183d377c4c335` ("docs: add A1 3-AI review prompts and dispatch", 2026-11-06 20:57 +0900). 요구서의 "검토 HEAD = 본 문서가 포함된 커밋" 조건과 일치.
- 방법: 코드(`runner/c5_a1_lora.py`, `runner/c5_a1_eval_batch.py`, `runner/c5_a2null_full_train.py`, `runner/c5_a2null_eval.py`의 지표 정의, `eval/slot_verify.py`)와 산출물(`reports/provenance/C5_a1/pilot300_val161/*`의 저장 필드 재집계), 보고서 6종, 계획 2종, `docs/decisions.md`(D-079~D-082)를 교차 대조했다. 요구서가 "로컬 raw 재계산으로 검증됨"이라고 명시한 핵심 수치(A1/A0 paired 차이, CI 등)는 재소송하지 않았고, A1 측 저장 산출물 내부 정합성만 독립 확인했다.
- 이 검토 환경에는 `data/models/` 가중치가 없다. 따라서 텐서 수준(merged attention shape, EG2 컨텍스트 길이 등) 재검증은 불가하며, 코드·산출물·문서 대조로 대체하고 그 한계를 여기서 명시한다.
- 구속 준수: 상담 전용. **본 파일 1개만 추가**했고 다른 파일은 수정하지 않았다. subagent·추가 모델 미사용(직접 수행). P1 데이터·외부 LLM API·봉인 test 163 접촉 없음.

---

## 1. Verdict (한 줄)

**A1 full train을 지금 시작한다** — 2 epoch, 아래 Must-fix #1(프로토콜)·#2(slot 보존 보고)를 적용한 뒤 즉시. B-family bridge는 별도 트랙으로 분리하고 같은 CPU 창을 소비하게 하지 않는다. 근거: pilot300은 1 epoch의 23.2%에 불과하지만 paired +0.0465 CI [+0.0336,+0.0603](하한이 0에서 충분히 떨어져 있음), grounded(신규 슬롯) 100%, EOS 100%, repeated4 0.0554로 방향이 크고 일관되며, 남은 리스크(과적합, prefix 조건)는 3시간짜리 val-gate 실행 자체가 가장 싸게 답하는 질문이다. 다만 **이 verdict는 "제품 채택"이 아니라 "다음 실험 실행" 승인**이며, 제품 판정은 full train → 사람 50 → test 163 순서를 유지해야 한다(§5 Must-fix #2, §2 D6).

---

## 2. D1–D6 권고

### D1. A1 full train 승인 — **2 epoch 먼저, 조건부 승인**

- 권고: 2 epoch(사전등록 초안 §7 유지) + 아래 프로토콜 수정. 3 epoch는 지금 근거가 없다.
- 근거: 300 step 시점에 이미 A0 대비 우세가 CI로 확정됐고 loss가 아직 하강 중(first10 0.7193 → last10 0.6016)이다. 즉 추가 pilot은 같은 구성의 같은 분포를 다시 샘플링할 뿐 정보가 없다. 2 epoch(≈3h + 평가 오버헤드 ≈1h)가 1 epoch(90분)보다 val 곡선을 2배 길게 줘 과적합 관측점을 만들고, 3 epoch는 1,293쌍 과적합 리스크만 더한다.
- 변경 조건: epoch 1 종료 시점 val best가 pilot300의 0.6576을 넘지 못하면 과적합/스케줄 문제로 중단하고 contingency arm(D1-변형: r16 또는 +gate/up/down)을 새로 승인받아 검토한다. 반대로 val이 계속 상승 중이면 3 epoch 연장을 별도 승인으로 검토한다.

### D2. prefix 조건 — **`summarize: ` train+eval 고정(F5 전용) + bare val161 병행 보고, dropout arm은 하지 않는다**

- 권고: 학습·평가 모두 `summarize: ` 고정. 단, 배포 입력 형식을 먼저 결정하고, 그 형식으로 val161을 한 번 더 평가해 헤드라인 숫자와 배포 조건을 일치시킨다.
- 근거: prefix는 특수 토큰이 아닌 일반 텍스트이고, bare 학습 adapter에 prefix만으로 +0.1459(0.4659→0.6118), prefix 학습 adapter는 bare에서도 0.6522를 유지한다 — adapter는 task를 학습했지 prefix 문자열에 의존하지 않는다. 범용 재사용은 이미 사전등록에서 금지됐으므로("F4/F6 LoRA 재사용 금지") dropout arm의 실익이 없다. 주의: bare 0.6522 > prefix 0.6272(val5)는 n=5라서 노이즈와 구분 불가(n=5에서 per-doc char F1 표준편차 ~0.15 → SE ~0.07)이며, 요구서는 이 역전을 해석 없이 넘어갔다.
- 변경 조건: bare val161이 prefix val161보다 유의하게 낮으면(예: Δ>0.03) prefix가 load-bearing이므로 배포 계약에 prefix를 명시하고 문서로 고정한다. 반대로 bare가 같거나 높으면 prefix 없는 배포도 허용 가능 — 어느 쪽이든 결과를 문서로 남긴다.

### D3. bridge 우선순위 — **A1 full train이 먼저다. B-family의 첫 실험은 B3가 아니라 "인터페이스 수정 + readout이 추가된 B1d 최소 프로브"다**

- 권고: 요구서 §3.7.8의 순서(B3 → B1d)는 뒤집는다. B3-as-specified는 §4(bridge addendum)에서 논증하듯 redundant-channel 혼란 때문에 "decoder readability"를 측정하지 못한다. B1d는 인터페이스 모순(§7 오류 #1)을 고친 뒤 readout(NLL 갭)과 함께 가야 한다.
- 근거: 범용 bridge의 존재 이유는 "label 없이 P0 text로 확장"이고 그 조건을 유일하게 갖는 변형이 B1d다. 반면 B3는 label을 쓰면서도 정보 전달을 검증하지 못하는 최악의 조합이다. 단 B1d도 단독으로는 frozen decoder의 zero-shot 천장(char F1 0.2333, repeated4 0.8383, 동일 val161 실측)을 벗어나지 못하므로, 성공 기준을 생성 품질이 아니라 표현 정렬 + decoder 소비 가능성(NLL 갭)으로 미리 고정해야 한다.
- 변경 조건: B1d 최소 프로브(추가 실험 #4)에서 teacher-forced NLL 갭이 사전등록 역치를 넘으면 → B1d는 기각되고 B1a(감독 기반)로 폴백한다. 반대로 갭이 작으면 B2(decoder LoRA)가 다음 실험이 된다.

### D4. A2 종결 — **현재 근거로 제품 후보 종결. raw-vs-seq는 "재개 조건"이지 "종결 조건"이 아니다**

- 권고: 종결 유지. ablation 양성(+0.058, CI>0, 149~157/161 문서)은 exploratory 기록으로 보존.
- 근거: grounded 0/161·1/161, char F1 0.13, repeated4 0.85~0.87은 여유 없는 실패다. ΔNLL +0.058은 NLL 3.116 대비 상대 1.9%로, "문서 특정 신호가 존재"를 보여줄 뿐 제품 가능성과 거리가 크고, 길이·스타일 같은 얕은 단서로도 설명된다. raw control을 지금 돌려도 종결을 뒤집을 인과 경로는 없다.
- 변경 조건: B1d 계열이 "정렬된 memory 주입"으로 회귀할 때 — 즉 A2와 같은 injection 지점을 다루는 실험이 열릴 때 — raw-vs-seq control을 B1d readout 안에 참조 arm으로 흡수하는 것이 비용 최소 경로다(별도 A2 재개 아님).

### D5. test 163 — **현 계획 유지: full train 후, val best 1개, 1회. B-family에는 test를 쓰지 않는다**

- 권고: A1 full train의 val-best 체크포인트 1개에만 1회 사용. B-family는 test 접근 금지 유지.
- 근거: 현재 B-family 출력은 "제품 후보"가 아니라 "표현 readout" 수준이므로 test를 쓸 후보 자체가 없다. 다중 비교 위험은 변형마다 test를 쓰는 순간 발생한다.
- 변경 조건: B-family가 val161에서 A1 val-best를 넘는 후보를 만들었을 때만, **그 시점 이전에** B-family test 지출 규칙(후보 1개, 1회)을 사전등록하고 집행한다. 사후 규칙 변경은 금지.

### D6. 사람 50건 — **full train 후, test 163 전**

- 권고: 순서 고정: full train → 사람 50 → test 163(1회).
- 근거: 사람 검토만이 grounded가 잡지 못하는 오류류(사실 누락, 잘못된 바꿔쓰기, 비slot 사실 왜곡)를 볼 수 있고(§3 Q6, slot 보존 0.456 발견), test는 1회성이므로 사람 검토에서 구조적 결함이 발견됐을 때 test를 아끼는 것이 최적 순서다. 요구서의 "치명적 사실 누락 없음" 기준은 slot 보존 문제를 정면으로 다루는 유일한 gate다.
- 변경 조건: 사람 검토에서 val 지표로는 보이지 않는 체계적 결함류가 발견되면, test 전에 해당 결함류를 재는 자동 지표를 추가하고 gate를 갱신한다(갱신은 test 사용 전에만 허용).

---

## 3. Q1–Q12 답변

**Q1. pilot300 val161은 full train 시작 근거로 충분한가?**
실행 승인으로는 충분, 제품 근거로는 불충분 — 이 구분이 핵심이다. 찬성 근거: paired +0.0465 CI [+0.0336,+0.0603]으로 0 하한이 3 표준오차 이상 떨어져 있고 112/161(69.6%) 우세, grounded/EOS 100%, repeated4 0.0554는 target 데이터 평균 0.0270의 2배 수준으로 "붕괴 아님"을 확인시켜 준다. 또한 char F1은 원문 복사(copy 4-gram 0.99)에 유리한 지표인데 A0가 그 유리한 지표에서 졌다는 점이 결과를 오히려 강화한다. 반대 근거: 300/1,293 step(23.2%), 상수 lr 2e-4(스케줄·warmup 없음), 중간 체크포인트 없음(현 `c5_a1_lora.py`는 종료 시 1회 저장), 단일 seed, 첫 5건 튜닝 재사용(제외 156건 0.6586으로 편향은 작음), 사람 검토 0건. 그러나 이 반대 근거들은 "pilot 연장"이 아니라 "프로토콜을 붙인 full train"으로 해소되는 것들이고, full train은 test를 건드리지 않으므로 되돌릴 수 있다. 판정: 시작한다(단 Must-fix #1·#2 선행).

**Q2. 2 epoch vs 3 epoch, 체크포인트/early stop 고정 방법은?**
2 epoch 먼저다. 고정할 것: (a) 체크포인트 저장을 250~350 step 간격(약 epoch당 4~5회)으로, (b) 각 체크포인트마다 `c5_a1_eval_batch.py`로 val161 평가(회당 ~12-15분), (c) 선택 지표 우선순위 사전등록 — 신규 슬롯 0(하드) → EOS ≥95% → char F1 최대 → repeated4 최소 동점 처리, (d) early stop은 "평가 2회 연속 running-best 대비 char F1 −0.01 이상 하락"으로 정의(요구서의 "patience 1"은 단위가 모호하므로 평가 횟수 단위로 명시), (e) lr은 warmup 3~5% + 선형 decay(peak 2e-4 유지), (f) 데이터 순서는 현재 randperm(42) 1회 생성 후 순환인데 2 epoch이면 동일 순서 2회 — epoch별 재셔플(새 seed)을 사전등록. 주의: 3h/4.5h 견적은 평가 제외치이며, 실제 벽시계는 체크포인트 평가 포함 약 4~5h다.

**Q3. `summarize: ` prefix를 학습에 넣는 것이 F5 전용으로 타당한가?**
타당하다. 증거는 세 층: (1) T5 계열 summarization 관례와 model card 예시와 일치하고, (2) 한국어 instruction prefix는 오히려 최악(0.4027, grounded 3/5)이었으며, (3) prefix로 학습한 adapter가 bare 입력에서 0.6522를 유지해 prefix는 의존성이 아니라 task cue임이 확인됐다. F5 전용 adapter로 고정하는 설계는 이미 "task별 adapter 분리" 결정과 정합이다. 다만 두 가지를 문서에 남겨야 한다: 배포 계약(입력에 prefix를 항상 붙이는지)과 bare 조건 성능(현재 val5 뿐) — 추가 실험 #1이 이것을 해소한다. dropout arm은 위 D2 근거대로 지금은 하지 않는다.

**Q4. B3 / B1a-b / B1d / B2 중 어디부터인가? B1d가 범용 bridge의 최소 경로인가, B3 readability test가 먼저인가?**
방향으로는 B1d가 맞지만 **지금 형태 그대로는 실행 금지**다. B1d는 label-free 확장이 가능한 유일한 변형이고(범용 bridge의 요건), teacher가 만드는 것은 정확히 frozen decoder가 소비하는 encoder-output 분포라는 점에서 구조적으로 올바른 목표다. 그러나 (a) 요구서 §3.7.4가 `inputs_embeds` 주입과 "런타임에 T5 encoder 미사용"을 동시에 주장하는 내부 모순이 있고, (b) teacher/EG2 hidden의 스케일·기하 대조 없이 MSE+cosine을 섞으면 고분산 차원이 지배한다(A2 adapter가 이미 ×5 learned scale이 필요했다는 점이 전례), (c) 성공 판정을 생성 품질로 두면 frozen decoder의 zero-shot 천장에 막힌다. B3가 먼저라는 주장은 기각한다: passage가 네이티브 임베딩으로 그대로 있으므로 모델은 soft token을 무시하고 최적에 도달할 수 있고, 관찰되는 개선은 "학습된 task cue"(= `summarize: ` 효과의 재현)와 구분되지 않는다. 순서: 인터페이스 수정 → 1-2h 최소 프로브(추가 실험 #4) → 통과 시 B1d 본격화, 실패 시 B1a 폴백.

**Q5. A2를 raw-vs-seq control 없이 종결하는 것이 정당한가?**
정당하다. 종결의 근거는 생성 결과(grounded 0/161, char F1 −0.48 CI)이지 ablation이 아니고, raw control은 "원인 규명"에 필요한 것이지 "제품 기각"에 필요한 것이 아니다. +0.058 ΔNLL(CI [+0.0520,+0.0640], 149~157/161 양성)은 메모리에 문서 의존 신호가 있음을 보여주지만 상대 1.9%로 약하며 얕은 단서 가능성을 배제하지 못한다. decoder LoRA를 지금 붙이지 않는 판단도 옳다 — 붙이는 순간 A1과 비교 불가능한 별도 모델이 되고, 원인 분리 없이 1,293쌍에서 과적합 리스크만 진다. 다만 B1d가 A2와 같은 injection 지점(encoder_outputs)을 다시 다룰 것이므로, raw-vs-seq 질문은 폐기 말고 B1d readout의 참조 arm으로 이관해 기록한다.

**Q6. A1 val161 지표 구성이 충분한가? 무엇이 필수인가?**
불충분하며, 가장 큰 구멍은 **slot 보존(slot_preservation) 미보고**다. 배치 evaluator는 행 단위로 `slot_preservation`을 계산·저장하지만 metrics.json 집계에서 뺐고, 요구서 전체가 이 숫자를 보고하지 않았다. 필자가 저장값을 재집계한 결과 **평균 0.4558, 최소 0.0, 153/161 문서가 원문 slot을 1개 이상 누락**이다(A0 참고치: test163 coverage 0.7820, D-080). `grounded = not rep.new`는 신규 slot만 검사하므로(검증기의 `rejected`는 missing도 포함하지만 eval의 grounded는 포함하지 않음) "사실이 빠진" 요약이 전부 통과한다. 필수 추가: slot_preservation 평균/분포 집계(코드 1줄 수준), slot-free 6건 처리 규칙(Q7), 사람 50(test 전, "치명적 사실 누락 없음"을 유일한 누락 gate로). ROUGE-L/BERTScore는 gate 결정 가치가 낮고(char F1이 이미 문자 중복을 재고, BERTScore는 외부 모델 의존) 참고 수준으로 충분하다.

**Q7. 6/161 slot-free 문서의 grounded 보고 방법은?**
"grounded 155/155(정보 문서), 6/161 slot-free(vacuous, 별도 목록)"로 보고하고 gate 분모에서는 제외하되 목록과 해당 문서의 char F1을 함께 싣는다. 요구서 §0의 "grounded 161/161" 헤드라인은 6개 vacuous 문서를 포함한 수치라 그대로 쓰면 과장이다. 진짜 증거는 155개 정보 문서에서 총 837개 요약 slot, 신규 0이라는 사실이다. 사전등록에 "slot-free 문서는 gate 분모 제외 + 개별 표기 의무"를 문장으로 고정하고, 향후 grounded가 100% 미만일 때도 동일 규칙을 적용한다.

**Q8. LoRA target(q/k/v/o r8)은 충분한가? FFN/rank16은? B2는 B1d가 무시될 때 필요한가?**
구조적으로는 타당하다: 144 모듈 = (encoder 18 + decoder 18) × 4이고, merged attention 덕에 decoder q/k/v/o LoRA 하나가 self+cross를 동시에 적응시킨다(역방향 분리는 불가하다는 대가는 감수). pilot300이 A0를 넘었으므로 용량 부족의 증거는 없고, loss가 아직 하강 중인 것은 용량보다 학습량(lr 스케줄 부재) 문제에 가깝다. 권고: 1차 full train은 현 구성 유지, **contingency arm(r16 또는 +gate/up/down, DataCamp 레시피 방향)은 사전등록 트리거**(epoch 2 val-best가 pilot300을 못 넘거나 val loss 조기 정체)에서만 실행 — CPU 1대에서 무조건 2 arm 병행은 하지 않는다. B2 여부는 B1d readout이 결정한다: teacher-forced NLL에서 frozen decoder가 distilled memory를 실제로 소비하면 B2 불필요, 소비하지 않으면(간극 큼) B2가 필수가 된다. 단 B2 단독(정렬 없는 decoder LoRA)은 A2-with-LoRA와 같아서 금지됐던 방향이므로, B2는 항상 B1a/B1d 위에 얹는다.

**Q9. test 163 배분은?**
현 계획(A1 full train val-best 1개, 1회)이 맞다. B-family에는 test를 주지 않는다 — 현재 B-family 후보는 readout 단계라 test 후보가 아니고, 변형별 test 사용은 다중 비교를 만든다. B-family가 나중에 후보가 되면 그 전에 지출 규칙을 사전등록한다(D5). 사람 50은 test 전에 끝내 test의 의미를 보존한다(D6).

**Q10. A1은 EG2를 쓰지 않는다 — 프로젝트 목표를 어떻게 정의해야 하나?**
두 목표를 문서로 분리해야 한다. (1) F5 제품 목표 = "메모리용 추상 요약 품질"이며 그 성공 지표는 G-C5+사람 gate다 — A1은 이 목표의 정당한 경로이고 EG2 미사용은 결함이 아니다. (2) EG2 재사용은 플랫폼/전략 목표로, 별도 gate(readout, encoder-run 절감 비용, 멀티태스크 가능성)와 별도 트랙(B-family)으로 둔다. F5 설계를 EG2 사용을 강제하도록 비틀면(B-family를 제품 경로로 끌어올리기) 양쪽 다 나쁘다. 보고 규칙도 명시: A1 계열 성과에 "EG2 재사용" 크레딧을 붙이지 않는다.

**Q11. 2~3 epoch는 과적합 관점에서 적절한가? 고정할 것은?**
2 epoch는 적절, 3 epoch는 근거 부족이다. 고정: warmup 3~5% + 선형 decay(현 코드는 상수 lr), weight decay는 torch AdamW 기본 0.01이 이미 적용됨(문서에 명시), LoRA dropout 0.05 유지, epoch별 재셔픴 규칙 사전등록, 체크포인트별 val161 평가로 early stop(위 Q2). 추가로, val에서 과적합 징후는 "train loss는 내려가고 val char F1 하락"으로 판정하며, 이 판정에 train/val loss만 쓰지 말고 생성 지표(EOS, repeated4)를 함께 봐야 한다 — LoRA 과적합은 먼저 반복/붕괴로 나타나는 경우가 많다.

**Q12. 반드시 고쳐야 할 factual error나 누락은?**
있다. §7의 목록 전부이며, 가장 큰 3개는 (1) B1d 인터페이스 자기모순(문서 수정 필요), (2) **slot_preservation 0.456 미보고**(산출물에는 저장돼 있었음 — 요구서 개정 필요), (3) zero-shot 기준선이 자기 진단에서 최악이었던 한국어 prefix로 측정돼 0.2333이 base 모델을 과소표현할 가능성. 나머지는 §7 참조.

---

## 4. Bridge addendum

### 4.1 순위

**(a) F5-only (제품 경로로서 EG2→T5):**

| 순위 | 후보 | 이유 |
|---:|---|---|
| 1 | **B1a** | token 정렬(H4′ 100% 주장) 위에서 Linear(768→640) 0.49M으로 passage 임베딩을 **대체**하므로 정보 전달을 깨끗하게 검증하고, summary CE 감독이 있어 G-C5 통과가 이론적으로 가능한 최소 변형 |
| 2 | **B2** | B1a 단독이 부족할 때의 확장(단, B2 단독 금지 — A2-with-LoRA와 동일해짐). merged attention 특성상 decoder LoRA가 self+cross를 동시에 건드리는 대가 인지 |
| 3 | **B1b** | B1a가 underfit할 때의 capacity 폴백. 단 요구서의 2~5M 추정은 d=640 표준 FFN 기준 10M+일 가능성(§7 #7) |
| 4 | **B3** | 재설계 전에는 순위 불인정: passage가 네이티브 임베딩으로 이미 있어 soft prefix는 무시 가능한 redundant channel — 결과가 "학습된 task cue"와 혼동됨 |
| 5 | **B1d** | label-free라 요약 품질 감독이 없음 → 단독으로는 frozen decoder zero-shot 천장을 벗어나지 못해 G-C5 통과 불가. F5-only에는 진단용으로만 가치 |

**(b) 범용 EG2→T5 bridge:**

| 순위 | 후보 | 이유 |
|---:|---|---|
| 1 | **B1d** | P0 text만으로 학습 가능(유일한 확장 경로), teacher=정확히 decoder가 소비하는 encoder-output 분포, "런타임 encoder 미실행" 효율 목표와 일치. 단 인터페이스 수정 + readout 선행 조건 |
| 2 | **B2** | LLINK가 지적한 "decoder가 정렬된 표현을 무시한다" 리스크의 정석적 해법이자 B1d의 완성 단계. B1d readout 결과에 따라 트리거 |
| 3 | **B1a** | 감독 기반 폴백. task별 adapter가 되므로 "범용" 주장 불가(요구서 §3.7.9도 인정) |
| 4 | **B1b** | B1d/B1a의 capacity 폴백. 큰 파라미터가 "범용 최소" 정신과 상충 |
| 5 | **B3** | pooled 1-vector는 token-level 정보를 잃어 slot grounding에 구조적으로 불리하고, redundant channel 혼란은 여기서도 유효 |

### 4.2 첫 2주 실험

**A1 full train(즉시, 3~5h)을 먼저 끝내고, B-family의 첫 2주 실험은 "수정된 B1d 최소 프로브"다**: (i) 인터페이스 확정 — H_s를 `encoder_outputs`(cross-attention memory)로 주입하는 A2와 동일 지점으로 고정하고 "런타임 encoder 미실행"을 참으로 만든다(§7 #1), (ii) 1h 규모 프로브 — T5 encoder 최종 hidden과 EG2 token hidden의 norm/std 분포, random-init adapter의 per-position cosine 분포 측정(A2의 ×5 scale 전례 참조), (iii) distillation 학습(1,293쌍, decoder CE 불필요 → step당 A1보다 저렴), (iv) readout — val161에서 teacher-forced NLL(H_s) vs NLL(H_T) vs 비정렬 메모리 참조 arm + per-position cosine. 2주 내 P0 text 소량 확장으로 label-free 확장성도 1회 확인. **B3는 이 2주에 넣지 않는다.**

### 4.3 B1d 반증 최소 실험

**frozen decoder teacher-forced NLL 갭 측정** — val161(또는 20~30건 하위 표본)에서 동일 label·동일 mask로 `NLL(H_s)` − `NLL(H_T)`를 잰다. 선행 측정으로 `NLL(H_T)`(frozen decoder + 진짜 teacher states) 자체를 먼저 잰다. 이 숫자는 **지금까지 어디에서도 측정된 적 없는 참조치**이며, 완벽한 bridge가 도달 가능한 decoder-side 상한을 규정한다(A2 비정렬 메모리는 3.116이었고, 정상 A1 train loss는 0.66 대역). 사전등록 예시 역치: 중앙값 상대 갭 ≤ +3% 및 문서의 80% 이상이 +5% 이내 — 초과 시 이 capacity에서 B1d의 핵심 주장(EG2 token feature → linear/경량 adapter로 encoder-output 공간 재현)은 반증되고, capacity 상향(B1b) 또는 트랙 중단으로 간다. 학습 전 random-init 상태의 cosine 분포도 함께 찍어 "학습이 실제로 무엇을 옮겼는지"를 남긴다.

### 4.4 각 후보의 가장 가능성 높은 실패 모드

- **B3**: soft token 무시(redundant channel) — passage가 이미 있어 adapter가 기여할 여지가 적고, 관찰 개선이 learned task cue와 구분 불가. 2차: pooled 병목이 slot 수준 정보 상실.
- **B1a**: 선형 map이 T5 encoder의 문맥적 상태를 underfit → decoder에 off-distribution 입력. grounded는 유지되지만 char F1이 A0 하회.
- **B1b**: 1,293쌍 과적합 + 용량을 올려도 근본 정보 부족은 유지; 비용·파라미터 과소추정 리스크.
- **B1d**: (1) 문서 모순대로 잘못된 인터페이스(inputs_embeds)로 구현, (2) 스케일 불일치로 MSE가 고분산 차원에 지배당음, (3) 정렬에 성공해도 frozen decoder 생성은 zero-shot 수준 유지 → 제품 가치 0(B2 필요), (4) 토큰화 100% 일치 주장이 prompt 포함 조건에서 깨짐.
- **B2**: 1,293쌍에서 decoder LoRA 과적합; merged attention 특성상 self/cross 동시 적응으로 실패 원인 귀속 불가; 정렬 없이 standalone 실행 시 A2-with-LoRA 회귀.

---

## 5. Must-fix (최대 7, 우선순위 순)

1. **Full-train 실행 프로토콜 구현** — `c5_a1_lora.py`에 주기적 체크포인트 저장(250~350 step), 체크포인트별 val161 배치 평가, 사전등록 선택 지표(신규 슬롯 0 하드 → char F1 → repeated4), early stop(평가 2회 기준), warmup+선형 decay, epoch별 재셔플. 현재 코드는 종료 시 1회 저장이라 "val 161 best 선택"이 물리적으로 불가능하다. **[문서+코드 수정, 새 실험 아님]**
2. **slot_preservation 집계·보고 의무화** — 배치 evaluator가 행 단위로 이미 계산하는 값을 metrics.json에 추가(평균/최소/누락 문서 수). 요구서에는 A1 val161 = 0.456(153/161 문서 누락 있음, 최소 0.0)을 정정 기재. 향후 모든 평가(report·gate)에 필수 필드로. **[문서+코드 수정, 새 실험 아님]**
3. **B1d 인터페이스 모순 해소** — `inputs_embeds` 주입 문장 삭제 또는 "encoder_outputs 직접 주입(런타임 encoder 미실행)"으로 확정. 이것이 distillation target과 런타임 그래프를 결정하므로 B-family 코드 작성 전 필수. **[문서 수정]**
4. **배포 입력 형식 결정 + bare val161 평가** — prefix vs bare 중 배포 조건을 결정하고 pilot300 adapter로 그 반대 조건 val161을 1회 평가해 두 조건 수치를 문서에 병기(현재 val161은 prefix-only, bare는 val5뿐). **[새 평가 실행 필요, ~15분 CPU]**
5. **zero-shot `summarize: ` 재측정** — 현 zero-shot 0.2333은 자기 진단에서 최악이었던 한국어 prefix 조건. `summarize: ` zero-shot val161을 1회 측정해 "A1이 개선해야 할 출발점"과 "B1d가 상속할 frozen decoder 천장"을 재보정. **[새 평가 실행 필요, ~15분 CPU]**
6. **grounded 보고 규칙 + CI 방법 명시** — slot-free 6건의 분모 제외·별도 표기 규칙 사전등록(Q7), paired CI [+0.0336,+0.0603]의 방법(bootstrap/t, B, seed) 명시. **[문서 수정]**
7. **사람 50건 채점 기준(루브릭) 사전등록** — "치명적 사실 누락 없음"을 slot 보존 결과와 연결해 측정 가능한 기준으로(예: 원문 slot 중 제품-critical 종류 누락 시 fail), 수용 ≥60%와 함께 test 전 집행. grounded만으로는 누락을 못 잡는다는 것이 0.456 발견의 직접 귀결이다. **[문서 수정]**

---

## 6. 추가 실험 (최대 5)

1. **bare vs prefix val161 이중 평가** — pilot300 adapter, 배치 evaluator 2회. 비용 ~15분/조건. 결정 가치: 높음(D2 확정, 배포 계약 고정, n=5 역전 해소).
2. **zero-shot + `summarize: ` val161** — 네이티브 모델, adapter 없음. 비용 ~15분. 결정 가치: 높음(B1d 상한과 "A1 개선 폭"의 기준선 재보정; 현재 기준선은 최악 프롬프트로 측정됨).
3. **디코딩 진단** — pilot300으로 repetition_penalty=1.2 / no_repeat_ngram_size=4 변형 1회(val5 또는 val161 하위). 비용 ~15분. 결정 가치: 중간(잔여 반복이 decoding 유인인지 학습 문제인지 분리; 최종 gate 대체 금지 — Exa 보고서 자체의 원칙).
4. **B1d 최소 프로브**(§4.2·§4.3) — teacher hidden norm/std 프로브 + NLL(H_T) 참조 측정 + 소형 distillation + readout. 비용 ~2-4h(캐싱 1~2h 포함). 결정 가치: 최고(bridge 트랙 전체의 go/no-go를 구현 전에 결정).
5. **contingency LoRA arm**(r16 또는 +gate/up/down) — 사전등록 트리거(epoch 2 val-best ≤ 0.6576 또는 val 정체)에서만. 비용 ~3h. 결정 가치: 조건부 높음(용량이 병목인지 아닌지를 한 번에 답함).

---

## 7. 사실 오류·과장·누락

1. **[내부 모순] B1d 인터페이스**(§3.7.4): "H_s를 encoder inputs_embeds로 넣고"와 "런타임에는 T5 encoder를 쓰지 않는다"는 동시에 참일 수 없다. inputs_embeds로 넣으면 encoder가 런타임에 실행되고 distillation target(teacher의 encoder **출력** states)과 주입 위치(입력 임베딩 공간)가 어긋난다. encoder 미실행이 참이 되려면 주입은 `encoder_outputs`(A2와 동일 지점)이어야 한다.
2. **[과장] B1d의 "범용 bridge 최소 경로/가장 유망" 헤드라인**(§0.4, §3.7.7, §3.7.8): label-free adapter는 frozen decoder의 zero-shot 행동(동일 val161에서 char F1 0.2333, EOS 1.86%, repeated4 0.8383)을 상속한다. §3.7.9는 이를 인정하지만 표·결론의 헤드라인은 이를 반영하지 않는다 — B1d는 "정렬 가능성"의 실험이지 제품 후보가 아니다.
3. **[누락-중대] slot_preservation 미보고**: 저장 산출물에는 행 단위로 존재(평균 0.4558, 153/161 문서 ≥1 slot 누락, 최소 0.0)하나 metrics.json·요구서 어디에도 없음. A0의 coverage 0.782(D-080)와 비교 보고가 원칙이었는데 A1에서만 빠졌다. "grounded 100%" 헤드라인과 나란히 놓으면 사실 안전성 인상을 왜곡한다.
4. **[기준선 편향] zero-shot 프롬프트**: 0.2333은 한국어 instruction prefix(`다음 글을…`) 조건이며, 자기 진단이 이 프롬프트를 최악으로 분류했다(0.4027 vs 0.6118). `summarize: ` zero-shot arm이 없어 base 모델 실력이 과소표현됐을 가능성.
5. **[표기] grounded 정의 혼재**(§3.1): 한 표에 개수(0/161), macro(0.6584), micro가 정의 없이 섞여 있고, "grounded 161/161"에는 slot-free 6건의 vacuous 판정이 포함돼 있다(유효 분모 155).
6. **[누락] 통계 방법**: paired CI의 방법(bootstrap/t), 반복 횟수, seed 미명시. 112/161 우세에 부호검정 병기도 없다(69.6% — 유의하겠지만 명시 필요).
7. **[추정 오류 가능성] B1b 파라미터 2~5M**: d=640 표준 2-layer transformer(Gemma식 FFN)는 층당 ~5-6.5M으로 2층 ≈ 10-13M. d_ff를 고정하기 전엔 비용 주장 금지.
8. **[추정 과대] B1d 비용 4~7h**: distillation 학습 자체는 decoder CE가 없어 step당 A1보다 저렴(추정 ≤2초/step → 2 epoch ≈ 1.5h 이하). 4~7h는 추출·캐싱·평가 포함 총량 기준으로도 상단 과대.
9. **[모호] B-family의 EG2 입력 차원**: A2는 final projection 후 512 + null PCA 256 = 768을 썼고, B-family 표는 "EG2 token feature 768"을 가정한다. pre-projection 768인지 512+256 조합인지, 각각의 D-042 상태(exploratory 표현인지)가 명시돼 있지 않다.
10. **[절차] 답변 형식 불일치**: 요구서 §10은 must-fix ≤5·실험 ≤3인데 상위 검토 요청은 ≤7·≤5 — 합성 단계에서 혼란 소지(본 검토는 상위 요청 형식을 따름).
11. **[소] 추정치 미포함 항목**: plan §2가 평가 항목으로 요구한 지연(latency)이 A1 결과에 없음. 제품(메모리 요약) 판단에는 1건 생성 시간이 필요.

검증으로 **오류 없음을 확인한 것**: 파라미터 수치(B3 Linear/MLP, B1a 0.49M, LoRA 1,474,560 = 144×10,240 = 0.398%), teacher cache 1.9GB(1,617×900×640×2B), 1 epoch 90분(1,293×4.2s), 300 step = 23.2% epoch, pilot300 시간·RSS·loss·adapter 크기(1,474,560×4B ≈ 5.9MB), metrics.json ↔ predictions.jsonl 전 수치 일치, 449 cap 도달 0건, 6/161 slot-free, D-079~D-082 내용, A2 코드가 실제로 encoder_outputs 주입으로 encoder를 우회함.

---

## 8. 최종 권고 (짧게)

지금 A1 full train(2 epoch)을 사전등록 프로토콜(Must-fix #1)과 slot 보존 보고(#2)를 붙여 시작한다. 같은 주에 bare-vs-prefix val161과 zero-shot `summarize: ` 재측정(각 ~15분)으로 기준선 두 개를 고정한다. B-family는 B3를 건너뛰고, 인터페이스 모순을 고친 B1d 최소 프로브(teacher-forced NLL readout 포함, ~2-4h)를 bridge 트랙의 첫 실험으로 하되, 성공 기준을 생성 품질이 아니라 NLL 갭·cosine으로 사전등록한다. A2는 제품 후보에서 종결 유지, test 163은 A1 val-best 1회만, 사람 50은 test 전에 실행한다. F4/F6 재사용은 지금 인터페이스 계약 문서화만 하고 구현·retention 검증은 보류한다(단, F6의 상류인 STT는 D-079로 동결 중이므로 범용 bridge의 수요자는 사실상 F4 하나뿐임을 계획에 명시).

---

## 부록. 독립 재집계 로그 (검증 근거)

`reports/provenance/C5_a1/pilot300_val161/predictions.jsonl`(161행) 저장 필드 재집계:

| 필드 | 재집계값 | metrics.json/요구서 | 일치 |
|---|---:|---:|---|
| char_f1_mean | 0.657580 | 0.6576 | ✓ |
| repeated4_mean | 0.055350 | 0.0554 | ✓ |
| distinct2_mean | 0.823057 | 0.8231 | ✓ |
| gen_len_mean(token) | 248.34 | 248.3 | ✓ |
| eos_rate | 1.000 | 161/161 | ✓ |
| grounded(not new) | 1.000 | 161/161 | ✓ (정의상) |
| new_slot_count 합 | 0 | 0 | ✓ |
| summary_slot_count 합 | 837 | 837 | ✓ |
| slot-free 문서 | 6 | 6/161 | ✓ |
| gen_len ≥ 449(cap) | 0건 | (미보고) | — |
| **slot_preservation_mean** | **0.455827** | **(미보고)** | **신규 발견** |
| slot_preservation 최소 | 0.000 | (미보고) | — |
| 누락 slot 있는 문서 | 153/161 | (미보고) | — |

비고: (a) `char_f1`은 공백 제거 문자 bag-of-characters F1이다(`runner/c5_a2null_eval.py:69-77`) — 순서·구조를 반영하지 않는 참고 지표임을 문서에 명시 권장. (b) `grounded`는 `not rep.new`이며 `slot_verify.rejected`(missing 포함)와 다르다 — 이 구별이 요구서 어디에도 없다. (c) 본 검토는 A0 val161·paired CI를 재계산하지 않았다(상위 요청이 로컬 raw 재계산으로 검증 완료 명시).