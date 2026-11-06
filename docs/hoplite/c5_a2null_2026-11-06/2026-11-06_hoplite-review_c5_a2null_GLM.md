# Hoplite 독립 검토 — C5/F5 A2-null (모델: GLM 5.3 Flash, reasoning=max)

- 날짜: 2026-11-06
- 검토 대상: `reports/EXTERNAL_REVIEW_C5_A2NULL_2026-11-06.md` 전문(568행) + 검증 파일 9종
- 동기화: `git fetch origin` + `git pull --ff-only origin main` → **Already up to date**, HEAD `fb2908d0f0cc1418f8207853814a5d135c3a1b23` ("docs: prepare A2-null Hoplite review prompts"). 검토 HEAD `c388699`는 이 커밋의 부모이며, 두 커밋 차이는 리뷰 프롬프트/디스패치 docs 4개 파일뿐이라 검토 내용에 영향 없음.
- 방법: 코드(`eval/slot_verify.py`, `runner/c5_a2null_eval.py`, `runner/c5_a2null_full_train.py`, `runner/c5_a2null_extract.py`, `runner/c5_a2null_probe.py`, `runner/c5_summary_eval.py`), 산출물(`reports/provenance/C5_a2null/*`, `reports/provenance/C5_clean/*`), 보고서·계획 문서를 대조. 이 검토 환경에는 `data/models/`가 없어 T5Gemma2/EG2 가중치 구조(merged attention shape, transformers 5.22.1 캐시 수정)는 저장소 기록을 신뢰해 수용하고 독립 재검증 불가를 명시한다.
- 구속: 상담 전용. 저장소 코드 수정 없음. 본 파일만 추가함.

---

## 1. 총평 (한 줄)

**full val 161 first** — val 5(첫 5건, 결정론적 순서)는 방향은 일관되지만 확증 증거가 아니므로, 먼저 val 161 전수 + A0-val-161 + zero-shot T5Gemma2 통제로 기반을 만들고, 그 결과에 따라 decoder LoRA(A2-null 연속) 또는 A1 전환을 사전등록된 게이트로 판정한다.

---

## 2. Q1–Q15 답변

### Q1. 실험 설계 — A2-null-seq는 정당한 확장인가

null-space 수학 자체는 아티팩트 수준에서 검증됐다(`nullspace_probe.json`: rank 512, `WᵀP` 4.29e-06, `PᵀP` 오차 4.77e-07, projection 재현 오차 0.0, `extract.py`의 `z = final + P x_t`는 W의 열공간과 직교합으로 계획 수식과 동치). 그러나 원 방법은 "pooled retrieval 벡터의 코사인 기하 개선"이고 A2-null-seq는 "frozen decoder cross-attention이 소비하는 token-level encoder memory"로, 목적 함수·소비자·요구 분포가 모두 달라지는 큰 외삽이며 성공 근거의 이전 논거는 없다. 계획 문서 스스로 "A2-null이 A1보다 나쁠 가능성이 높다"(`plan_c5_a2null_v0_1.md` §7)고 규정한 점은 정확하다. 결론: 과학적 ablation("EG2 표현이 generation을 구동할 수 있는가")으로는 의미 있고, 문서의 exploratory 자기 규정은 적절하다 — 다만 성공 선험확률은 낮게 보는 것이 맞다.

### Q2. 코드·label — EOS 계약에 남은 버그가 있는가

`runner/c5_a2null_full_train.py` 74–94행의 수정은 정확하다: `add_special_tokens=False`로 bos 제거, content 뒤 `<eos>` 1개, 유효 구간 밖 `-100`, decoder input은 HF shift-right가 bos로 구성(decoder_start None → bos fallback은 소스 확인 기록 존재). 코드 검토에서 계약 자체의 추가 버그는 발견하지 못했고, 남은 리스크는 계약이 아니라 통계적 것이다 — eos 1/≈175 token × 1,293 step × 1 epoch로는 eos 확률이 크게 오르기 어려워 eos 0/5~1/5 관측과 정합한다. 권장 추가 체크: (a) label을 decode해 원문 summary와 round-trip 일치 assert, (b) label당 eos 개수 == 1 assert, (c) eval 기록에 "eos 미생성"과 "상한 도달"을 구분해 이미 `gen_len`/`ended_eos`로 남기고 있으니 이를 gate 지표로 승격. eval 쪽 `skip_special_tokens` 디코딩·`ended_eos` 판정도 점검했으나 문제 없다.

### Q3. 결과 해석 — "adapter-only 실패"로 결론 내릴 수 있는가

지지되는 결론은 "이 구성(adapter-only·1 epoch·frozen decoder)이 val 5에서 실패했다"이고, "adapter-only A2-null은 불충분하다"는 일반 결론은 아직이다. val 5는 shard 첫 5건으로 임의 표본이 아닌 것이 코드로 확인된다(`splits.json`의 `val[:5]`와 예측 id가 정확히 일치), n=5에는 분산 추정이 없고, 3개 arm이 모두 동일 구성을 공유해 1 epoch underfitting 혼재가 배제되지 않았다(train 3.25 vs val 3.12는 과적합이 아니라 미학습 쪽 정합). 다만 15/15 전 생성이 동일 붕괴 시그니처(129토큰 상한, eos 없음, grounded 0/5, new_slot ≈1.0)를 보인 것은 정성적으로 일관된 부정 증거다. 판정: **INCONCLUSIVE(부정 방향)** — full val 161 없이 "실패" 확정은 조기다.

### Q4. 다음 투자 — 다음 한 수

다음 한 수는 **full val 161**이며, 같은 평가 배치에 A0-on-val-161과 zero-shot T5Gemma2를 함께 돌리는 것이 정보당 비용이 가장 낮다. raw control 없이 decoder LoRA를 먼저 하면 성공·실패 어느 쪽도 "null injection의 기여"를 확정할 수 없고, `plan_c5_a2null_v0_1.md` DoD #8이 이미 요구하는 A0·raw·seq 비교도 미완으로 남는다 — 다만 목표를 "인과 규명"이 아니라 "생성 가능성 확인"으로 명시하면 decoder LoRA 선행도 방어 가능하다. 권장 순서: val 161(+참조 통제) → 사전등록 게이트 판정 → decoder LoRA 또는 A1 전환.

### Q5. Decoder LoRA 설계

merged self/cross attention에서 q/k/v/o LoRA는 현실적 1-shot이지만 두 경로를 동시에 적응시켜 효과의 귀속이 불가능하다(실패해도 cross 문제인지 self 교란 문제인지 모른다). 더 좁은 대안으로 k/v-only LoRA(memory를 직접 소비하는 projection), 또는 o_proj + decoder final norm(XA-only 레시피의 최근접 변형)을 들 수 있다. 수치 권고: r=8~16, alpha=2r, dropout 0.05, lr 1e-4 + warmup 5%, 1~2 epoch, gradient checkpointing, adapter는 학습 상태 유지, per-step eos/반복 지표 로깅. 단 그 전에 **adapter-only 2~3 epoch**(옵션 D, 회당 ~45분)가 가설 3·4(underfitting, EOS imbalance)를 더 싸게 검증하므로 순서상 먼저다.

### Q6. Gate

필수(사전등록, val 161): grounded ≥ 0.99(G-C5), eos 종결률 ≥ 0.90, 반복 지표(예: repeated-3-gram 비율 ≤ 0.20 또는 distinct-2 ≥ 0.6 — 값은 실행 전 고정). 참고(비게이트, 보고 의무): char F1, ROUGE-L, compression, slot 보존/coverage, copy rate. 사람 50은 계획대로 최종 확증 단계로 유지하고 gate에서 제외. test 163은 최종 후보 확정 후 1회만. A0-val-161은 게이트가 아니라 필수 보고 비교 기준으로 둔다.

### Q7. 평가 타당성 — grounded 지표로 충분한가

충분하지 않다. `grounded = not new`는 slot 위조만 잡고, slot이 없는 유창한 비사실·반복 텍스트는 통과시킨다(관측된 record 1은 반복 덩어리가 숫자/날짜로 추출돼 걸렸지만, 일반 문장 반복은 grounded=True가 될 수 있다). char F1은 문자 bag이라 순서를 무시하고 반복을 정밀도 희석으로만 반영하며 반복과 환각을 구분하지 못한다 — 검증기 docstring 자체가 "safety gate, not a summary-quality metric"이라고 밝힌다. 최소 추가: eos rate, distinct-2/3(또는 반복 n-gram 비율), ROUGE-L, 길이 분포. 비slot 사실 오류는 외부 LLM API가 금지된 상태에서 사람 50이 유일한 확증 수단이므로 현 계획을 유지한다.

### Q8. A0 비교

공정한 품질 서열 비교가 아니다: split이 다르고(test 163 vs val 5), A0는 추출형이라 grounding·coverage가 구조적으로 유리하며 char F1도 원문 복사에 유리하다. char F1 외에 봐야 할 것: 동일 split 재계산(A0-on-val-161), grounding, eos/길이 거동, 반복, compression, 사람 수용도 — 모두 같은 slot 검증기로. 문서의 split 주의 표기는 정확하며 유지해야 한다.

### Q9. 중단 규칙

"decoder LoRA 1회 후에도 grounded 0이면 중단"은 (i) 사전등록된 단일 시도, (ii) 최소 진전 기준 명시라는 전제에서 유효하다. A1과의 val 비교를 중단 조건으로 넣는 것은 반대한다 — A1은 미착수인 독립 결정이며, A2-null의 계속 여부를 A1에 직렬화하면 둘 다 지연된다. 권고: val 161이 기존 adapter의 붕괴를 확인하고, 후속 단일 개입(decoder LoRA 또는 3-epoch adapter)이 사전등록 최소 진전(예: grounded > 0, eos ≥ 0.5 on val 161)에 못 미치면 중단·A1 전환. 추가로 A2-null 총 추가 예산 상한(예: 학습 2회)을 두고, 2.4GB feature cache 등 매몰비용은 판단에서 명시적으로 제외한다.

### Q10. A1 전환 시

이전할 것: EOS label 계약 + assert 기반 검증, val 161 전수 평가(반복 지표·ROUGE-L 포함), A0-val-161 기준선, 사전등록 게이트, test 1회 규칙. A1 신규 smoke: (1) label round-trip·`decoder_start_token_id` 확인, (2) **frozen zero-shot T5Gemma2 val 5 생성 sanity** — 디코더가 자체 encoder로 뭘 하는지의 참조점이자 생성 경로 smoke, (3) RSS ≤ 13GB·step time ≤ 60초 중단 규칙(`plan_c5_abstractive_v0_1.md` §3), (4) LoRA q/k/v/o(+필요시 FFN) 2~3 epoch, val best 선택. zero-shot이 이미 붕괴한다면 문제의 중심은 bridge가 아니라 decoder·task 정합이고, A1은 그것을 직접 고치는 경로라는 점이 초기에 확정된다.

### Q11. 누락·확증 편향·매몰비용

누락: (a) `c5_a2null_eval.py` 기본 `--split=test`라는 봉인 접촉 위험, (b) zero-shot T5Gemma2 통제의 부재("아직 하지 않은 것" 목록에도 없음), (c) char F1의 순서 무시성, (d) plan DoD #8이 raw 비교를 이미 요구한다는 사실(문서는 단순 "미실행"으로만 표기), (e) n=5의 분산/CI 부재. 확증 편향: 3개 arm이 모두 1 epoch·adapter-only·frozen decoder를 공유하므로 "adapter-only 실패"는 구성 외삽이고, "수학·feature·메모리는 검증됐다"는 프레임은 사실이지만 "표현 이전 가설 자체는 미검증"을 가릴 수 있다. 매몰비용: feature cache·학습 시간은 이미 지출됐고, 계속 여부는 A1 대비 기대 정보 가치로만 판단해야 한다 — 요청서는 이 균형을 대체로 잘 유지하고 있다.

### Q12. F5 전용 vs 공유 decoder bridge

지금은 F5 전용이 맞다. 자산(P, PCA, adapter)은 이미 F5 네임스페이스로 분리돼 있고, 인터페이스(`encoder_outputs` [T,640] bf16 + `attention_mask`)는 충분히 얇아 나중에 공유화해도 재작업이 작다. 나중에 실제 재설계 대상은 LoRA 소유권(F5 전용 vs 멀티태스크 공유)인데, 이는 F4/F6 decoder 경로가 실제로 승인됐을 때만 의미가 있어 지금 결정하면 존재하지 않는 요구에 대한 조기 경직이다. 요구되는 것은 공유 코드가 아니라 결정 로그 한 단락(인터페이스 계약·재사용 조건·D-042 경계)이다.

### Q13. D-042와 재사용 경계

새 결정 없이는 불가하다. D-042는 EG2 text hidden의 F4/F5 **제품 경로** 사용을 금지하며, A2-null 산출물의 F4/F5 재사용은 그 경계 안에 있다(F6 텍스트 교정 경로도 같은 질문을 새로 겪는다). 탐색 실험 간 재사용(제품 경로 제외, split 독립, test 163 접근 금지)은 D-081형 스코핑으로 가능하지만, 기능별 gate와 별도 결정은 각각 필요하다. 요청서의 경계 서술(D-042 유지, D-081 하의 exploratory, 재사용 미승인)은 정확하며 그대로 유지해야 한다.

### Q14. F3 확장과의 관계

지금 F3 관련 설계·테스트는 불요하다. 현재 F3는 retrieval/emoji tagging으로 decoder를 쓰지 않아 회귀 점검 대상이 없다. 향후 vision→text tagging 확장이 실제로 제기되면 필요한 것은 vision hidden 기하에 맞는 별도 adapter 경로이고, F5 bridge에서 이전되는 것은 가중치나 null basis가 아니라 평가 하네스와 "encoder 대체 memory + frozen decoder" 패턴이다. 결정 로그에 한 줄(텍스트 모달리티 전용, F3 확장 시 별도 결정)이면 충분하다.

### Q15. 멀티태스크 회귀(retention)

지금 gate에 넣지 않는다. F4/F6의 decoder 제품 경로가 없어 회귀 점검 대상이 없고, 탐색 트랙에 절차 비용만 추가된다. 공유 decoder 자산이 제품 결정 지점에 올 때 신설한다 — 표본: F4 정상 문장 보존 쌍, F6 교정쌍; 지표: 편집 정확성, 신규 slot 0, 지연; 기준: 각 기능의 frozen baseline. 그 전에는 로그 한 줄로 족하다.

---

## 3. Must-fix (우선순위 순, 최대 5)

1. **봉인 test 163 실행 가드**: `runner/c5_a2null_eval.py`의 기본값이 `--split test`·`--out predictions.jsonl`이다. 인자 없이 실행하면 봉인 분할을 평가한다. 기본 split을 `val`로 바꾸고, test는 `--allow-test` 명시 플래그 + 경고 로그를 요구하라. 이것은 D-081 봉인 규칙의 실행 수준 위반 경로다.
2. **평가 지표 보강 후에 val 161을 해석**: eos rate, distinct-2/3(또는 반복 n-gram 비율), ROUGE-L, 길이 분포를 eval에 추가한다. 현 세트(grounded + char-bag F1)는 관측된 실패 양상(반복 붕괴)을 특징화할 수 없어 게이트 판정의 근거가 된다.
3. **동일 split 기준선 확보**: A0-on-val-161과 frozen zero-shot T5Gemma2(val 5 → val 161)를 실행한다. 둘 다 학습 불요·분 단위~시간 단위 비용이고, A0 정의도 동일하게 재계산해 split 문제와 정의 문제를 동시에 제거한다.
4. **val 5 → val 161 확증을 continue/stop 결정의 전제로 고정**: 첫 5건(결정론적, 무작위 아님)의 n=5 결과로 "adapter-only A2-null 실패"를 일반화하지 않는다. val 161 결과가 있기 전까지 decoder LoRA 착수를 보류한다.
5. **사전등록 문서화**: 다음 학습 실행 전에 gate(grounded/eos/반복), 중단 규칙, 최대 추가 예산(예: 학습 2회), test 163 1회 사용 규칙, raw control 포함 여부(목표가 인과 규명이면 필수)를 문서로 고정한다. 이것은 plan DoD #8의 미이행 분을 닫는 작업이기도 하다.

## 4. 추가 실험 (최대 3)

1. **Zero-shot T5Gemma2 통제** — native encoder + frozen decoder, val 5(필요시 val 161), greedy/max_new 동일 조건. 디코더 자체 참조점을 만들어 "bridge 문제 vs decoder·task 정합 문제"를 분리한다. 가장 진단적이고 가장 싸다(분 단위).
2. **A2-null-raw control** — null injection 없이 `W h_t`(768) → adapter → decoder. plan DoD #8 이행이며, decoder LoRA 이후에도 인과 해석이 가능해진다. feature 부분 재추출 + 학습 ~45분.
3. **Adapter-only 2~3 epoch** — EOS imbalance·underfitting 가설을 decoder LoRA보다 싸게 직접 검증(회당 ~45분). eos rate와 반복 지표가 개선되는지가 decoder 적응 투자 판단의 분기점이 된다.

## 5. 사실 오류·과장·누락

1. **(위험 누락)** eval 기본 `--split=test`: 요청서 §10.2는 eval의 arm 자동 감지를 정확히 서술했지만, 기본 split이 봉인 test라는 사실과 위험을 언급하지 않는다.
2. **(지표 한계 미기술)** char F1이 "공백 제거 후 문자 bag"이라는 정의는 있으나, 순서를 무시하고 반복을 특징화하지 못한다는 함의가 어디에도 없다. 또한 A0의 `char_f1`(`c5_summary_eval.py`: `re.sub(r"\s+","",s)` 전체 공백 제거)와 A2-null의 `char_f1`(`c5_a2null_eval.py`: ASCII 공백만 `replace(" ","")`)은 동일 구현이 아니다 — 미세하지만 비교 시 동일 정의로 재계산해야 한다.
3. **(누락)** zero-shot T5Gemma2 통제가 "아직 하지 않은 것"(§5.8) 목록에 없다. 가장 진단적인 미실행 실험이다.
4. **(DoD 정합)** `plan_c5_a2null_v0_1.md` DoD #8은 "비교 | A0·A2-null-raw·A2-null-seq"를 통과 기준으로 요구하는데, 요청서는 raw control을 단순 "미실행 항목"으로만 표기하고 계획 DoD와의 불일치를 지적하지 않는다. 현재 상태는 자체 DoD 미충족 상태다.
5. **(소소한 과장)** "가장 좋은 A2-null 결과도 char F1 0.2297" — n=5에서 0.2297 vs 0.2269(LN arm)는 잡음 내 차이인데 "best"라는 서열 표현은 해석을 유도한다. "동등(노이즈 내)"이 정확하다.
6. **(문서 정합)** `reports/C5_a2null_search_2026-11-06.md` 헤더의 "full retrain 미실행"은 이후 작성된 eos/LN retrain 보고서와 모순되는 작성 시점 스냅샷인데, 요청서가 이를 "원인 조사" 근거로 인용한다. 상태 문구 갱신을 권장한다.
7. **(독립 검증 불가 명시)** T5Gemma2 merged attention shape(q 640→1024, k/v 640→256), 18층/4 heads, transformers 5.22.1 캐시 버그 미해당 주장은 이 검토 환경에 모델 파일이 없어 재검증하지 못했다. 저장소 소스 확인 기록을 신뢰해 수용하되, decoder LoRA 설계 전에 모델 config로 1회 확인할 것.

## 부록 — 이 검토에서 실제 검증한 것 / 하지 못한 것

| 항목 | 결과 |
|---|---|
| git 동기화 | up-to-date, HEAD `fb2908d`; 검토 HEAD `c388699` = 부모, diff는 리뷰 프롬프트 docs뿐 |
| val5 선정 | `splits.json` `val[:5]` == 예측 id 5건, 결정론적 첫 5건 확인 |
| val5 수치 재계산 | char F1 평균 0.2296(EOS)/0.2269(LN), new_slot 0.8667 — 보고서와 일치 |
| A0 지표 | `a0_eval.json`: char F1 0.6072, grounding 위반 0/163, compression 0.2524 일치 |
| slot 검증기 | 11개 테스트 존재, 패턴 우선순위·canonicalization·`rejected=bool(missing or new)` 코드 확인 |
| EOS label 계약 | `full_train.py` 74–94행, `-100` 마스킹·shift-right 구조 확인 — 계약상 결함 없음 |
| attention mask | train(`m_pad`)·eval(`ones(t)`) 모두 memory 길이와 일치 — 결함 없음 |
| external memory 경로 | 640d bf16 `BaseModelOutput(last_hidden_state=...)` + mask, train/eval 일관 |
| feature 추출 | `z = final + P x_t`(직교합), PCA train-only 상위 200건 학습(누수 없음), float16·resume 지원 |
| null-space 수학 | probe 아티팩트 수치가 요청서 §4.1과 일치 |
| adapter 파라미터 | EOS 1,082,752 / LN 1,084,033 ≈ "약 1.08M" 일치 |
| 미검증 | T5Gemma2 구조 상수·5.22.1 캐시 수정·watchdog 프로세스 상태(모델/환경 부재) |

끝. 이 검토는 상담 전용이며 저장소 코드를 수정하지 않았다(본 보고서 파일 추가는 요청된 산출물).
