# C5 EG2 → mT5/UMT5 layer plan — 3-AI review synthesis

- 작성일: 2026-11-08
- 라운드: `docs/hoplite/c5_layer_plan_2026-11-08/`
- 검토요청서: `reports/EXTERNAL_REVIEW_C5_LAYER_PLAN_2026-11-08.md` (618줄)
- 검토 기준 HEAD: `bb8bf702cbff4c73129098d4b660784be289fd75`
- 검토 모델: **GLM 5.3 Flash max / Opus 5.5 medium / Sol 6.1 xhigh**
- **최종 종합 판정: NARROW**
  - 전체 role probing + Stage B1/B2/Stage C 승인 아님
  - **native-tokenizer audit + 통제된 단일 B0 진단**만 다음 결정 대상으로 제안
  - **STOP 아님**: T5Gemma2 bridge는 D-108에서 계속 닫혀 있고, mT5 decoder 경로는 아직 국소적으로 검증할 가치가 있다.
- **실행 없음**: 이 문서는 검토 결과 기록이며, E0/B0/B1/B2/C 어떤 학습도 실행하지 않았다.
- test 163 봉인 유지, P1 데이터 미사용, `eval/slot_verify.py` 미수정, A1 native는 frozen fallback/reference.

---

## 0. 한 줄 결론

3-AI는 **만장일치로 “현재 계획 전체를 그대로 실행”하지 말 것**에 동의했다. 다만 **GLM은 조건부 CONTINUE**, **Opus와 Sol은 NARROW**였고, 실질 공통점은 다음이다.

> **먼저 tokenizer/wiring을 바로잡고, decoder adaptation의 효과를 matched control로 분리하는 단일 B0만 수행한다. B1/B2/Stage C와 대규모 role probing은 B0 통과 후 새 결정으로 미룬다.**

즉 **“계획 전체 승인”도 아니고 “bridge 영구 종료”도 아니다.** 가장 좁은 falsifiable B0만 남긴다.

---

## 1. 모델별 최종 판정

| 검토자 | 최종 판정 | 승인 범위 | 핵심 조건 |
|---|---|---|---|
| **GLM 5.3 Flash max** | **CONTINUE — 조건부** | layer role probing + Stage B0 | M1 LoRA attach, M2 tokenizer audit/re-cache가 B0 선행 조건. B1은 B0 후, B2는 B1 후, Stage C 제외 |
| **Opus 5.5 medium** | **NARROW** | 수정된 단일 B0만 | role probing은 보류. frozen adapter-only / adapter+LoRA / native encoder positive / memory-free 4-arm, 300/100, 3 seeds |
| **Sol 6.1 xhigh** | **NARROW** | E0 audit + E1 matched B0만 | native tokenizer/wiring audit, 20/20 2-arm × 3 seeds, 동일 donor/seed, B1/B2/C는 새 결정 |

### 종합

- **2/3 NARROW**이므로 종합 판정은 **NARROW**다.
- GLM의 CONTINUE도 “B0를 수정 없이 승인”이 아니라 **M1/M2를 선행 조건으로 요구**했고 Stage C를 제외했다. 따라서 실질적으로는 **B0만 조건부 진행**이라는 점에서 3-AI가 수렴한다.
- **STOP이 아닌 이유**: T5Gemma2 bridge와 달리 mT5의 표준 cross-attention decoder 경로는 아직 한 번도 제대로 된 matched-control B0로 검증되지 않았다. 비용도 1일 이내로 제한 가능하다.
- **전체 계획을 승인하지 않는 이유**: Stage A가 underfit이고, B0가 decoder LoRA·데이터 수·tokenizer를 동시에 바꾸며, 층 선택과 통계 단위가 고정되지 않았다. 이 상태의 B0는 성공해도 원인을 귀속할 수 없고, 실패해도 false negative가 된다.

---

## 2. 요청서·기존 실험에서 확인된 확정 결함

### 2.1 Stage A는 content selectivity의 clean negative가 아니다

원시 JSON에서 확인:

| 모델 | train CE(last10) 범위 | val real CE | 해석 |
|---|---:|---:|---|
| mT5-small | **5.158~5.950** | 6.623~7.469 | 5문서·100 step에서 train조차 충분히 fit하지 못함 |
| UMT5-small | **8.142~8.506** | 8.185~8.720 | train ≈ val, adapter가 거의 학습되지 않음 |

- Stage A의 `PARTIAL_MEMORY_USE_NO_CONTENT_SELECTIVITY`는 **screening 결과**로는 유효하지만, “frozen decoder가 병목”이라는 **인과 결론은 아니다**.
- mT5 layer19의 `delta_shuffled`는 **.0302**이고, cross-layer 최대는 **layer17 .1889**다. layer19는 **real CE 최소**였을 뿐 content selectivity 최고가 아니다.
- `torch.manual_seed(20261108 + layer)` 때문에 **layer와 initialization seed가 confounded**되어 있다. 23개 layer 순위를 layer effect로 읽을 수 없다.
- Stage A aggregate JSON에는 per-document delta가 없어 CI를 만들 수 없다. 단일 seed·5 val 문서의 .10~.19 차이는 noise와 구분되지 않는다.

**처리**: D-110/D-111의 판정 문구를 소급해 rewrite하지 않는다. 대신 이후 보고서에서 **Stage A = underfit screening, causal bottleneck 미확립**으로 명시한다.

### 2.2 `Δzero`는 memory 존재/길이의 증거가 아니다

- `eval_ablation`은 adapter의 **LayerNorm 이후**에 `zeros_like(mem)`을 넣는다.
- adapter가 학습한 출력은 결코 0 근처가 아니므로, zero memory는 **out-of-distribution**이다.
- real < zero의 큰 차이는 “memory를 쓴다”기보다 “out-of-manifold 입력이 decoder를 망가뜨린다”에 가깝다.
- **대체 통제**: train memory 평균(mean-memory), 길이 매칭 wrong-document, 동일 shape prefix crop.

### 2.3 EG2 cache가 T5Gemma2 tokenizer를 사용한다 — 실제 코드 결함

`runner/c5_eg2_all_layers_cache.py`:

```python
tok = AutoTokenizer.from_pretrained(str(args.model), ...)   # EG2 native: 로드만 됨
t5_tok = AutoTokenizer.from_pretrained(str(T5_PATH), ...)   # 실제 사용
...
ids_t = t5_tok(text, add_special_tokens=True, truncation=True, ...)
```

- native EG2 tokenizer를 로드하고도 **T5Gemma2 tokenizer ID를 EG2 language_model에 전달**한다.
- EG2는 **PLE**로 token-ID-indexed embedding을 매 layer에 재주입하므로, ID 불일치는 layer0에서 희석되는 오류가 아니라 **전 depth에 반복되는 오류**다.
- 불일치율은 아직 실측되지 않았다. 따라서 Stage A의 layer 순위와 B0의 baseline은 **native cache로 다시 세워야 한다**.

**판정**: 기존 cache는 **historical screening artifact**로만 보존하고, B0/B1/probing은 **native EG2 tokenizer cache**를 사용한다. 두 cache를 한 분석에서 혼용하지 않는다.

### 2.4 mT5/UMT5 LoRA attach가 조용히 0개가 될 수 있다 — Blocker

`runner/c5_b1d_b2.py`:

```python
TARGETS = ("q_proj", "k_proj", "v_proj", "o_proj")
...
if not name.startswith("model.decoder."):
    continue
if not name.endswith(TARGETS):
    continue
```

- 이 코드는 **T5Gemma2**의 decoder module naming을 따른다.
- mT5/UMT5의 T5 계열 attention은 일반적으로 `q`, `k`, `v`, `o` naming을 쓰며, `q_proj` 계열이 아니다.
- 현재 저장소에는 **mT5/UMT5 decoder LoRA runner가 없다**. `runner/c5_mt5_layer_probe.py`는 adapter-only/frozen decoder다.
- 이 상태로 B0를 구현하면 **LoRA가 0개 module에 attach되어 adapter-only 재현**이 될 수 있고, 그 결과를 “decoder LoRA도 효과 없음”으로 오독하게 된다.

**필수**: attach module 수를 assert하고, decoder-only q/k/v/o LoRA 목록을 provenance에 기록한다. zero-output LoRA가 frozen forward와 일치하는지도 확인한다.

### 2.5 B0 as written은 decoder adaptation을 귀속할 수 없다

계획의 B0는 Stage A와 비교해 한 번에 세 가지를 바꾼다.

| 변수 | Stage A | 계획의 B0 |
|---|---|---|
| decoder | frozen | decoder LoRA |
| train/val | 5 / 5 | 20 / 20 |
| tokenizer | T5Gemma2 (legacy) | native EG2 (명시는 없음) |

- **frozen adapter-only arm이 같은 data/tokenizer로 없다.**
- **native encoder positive control이 없다.** metric이 실제로 copy를 측정하는지 확인할 수 없다.
- **memory-free / mean-memory negative control이 없다.**
- 따라서 B0가 좋아져도 “decoder adaptation 덕분”인지, “문서 수 증가”, “tokenizer 교체”, “adapter 초기화” 때문인지 분리할 수 없다.

### 2.6 B0 DoD의 통계·전력 문제

- 20문서 × 100 step = 5 epoch 수준으로, **unseen 문서로 일반화되는 copy path**를 학습하기에 매우 작다.
- 3 seeds × 20 docs를 60개의 독립 관측처럼 다루면 안 된다. **문서 단위 cluster**가 필요하고, seed variance도 별도로 보여야 한다.
- `mean Δshuffled ≥ .10`은 Stage A의 단일 seed 변동(.189)보다 작은 절대 임계다. 근거가 약하다.
- “3 seeds 모두 양수”는 null에서도 **1/8**로 통과한다.
- sequence-mean CE는 대부분 LM prior로 예측되는 token이 신호를 희석한다. **source에서 copy 가능한 target token**에 집중해야 한다.
- single cyclic derangement는 donor length와 content를 동시에 바꾼다. **길이 매칭 donor + 복수 derangement**가 필요하다.
- “CI lower ≤ 0 → bridge 종료”는 **underpowered B0의 false negative로 전체 트랙을 닫는** 위험이 있다.

### 2.7 Role probing은 “역할”을 직접 식별하지 못한다

- surface frequency, numeric/date, slot overlap, sentence position은 **token type / spelling / position shortcut**과 강하게 상관된다.
- summary-derived slot label은 “source에 존재하는 slot”과 “요약이 선택한 slot”을 혼용한다.
- within-document label permutation은 “chance보다 높음”만 측정하며, token identity memorization을 통제하지 못한다.
- 23 layer × 4 probe = 92개 검정에서 “하나라도 유의”는 우연으로도 쉽게 충족된다.
- bootstrap은 token이 아니라 **문서 단위**여야 하고, primary probe 사전등록 + BH-FDR이 필요하다.
- role probing은 **B0의 선행조건이 아니다**. B0 통과 후 별도 예산의 representation study로 두는 것이 맞다.

### 2.8 Metric: `grounded`는 no-new-only다

- 코드의 `grounded`는 **신규 slot이 없는지**만 본다. preservation(원문 slot 보존)은 별도다.
- `grounded 100%`가 정보 보존을 뜻하지 않는다. A1 matched val100의 preservation은 **.4446**이었다.
- Stage C 전에 **preservation, required-slot recall, new-slot rate, entity audit, repetition/length**를 별도 보고해야 한다.
- production `eval/slot_verify.py`는 수정하지 않고, **eval-only reporting layer**에서 이중 표기한다.

### 2.9 Stage C와 B2

- Stage C DoD(F1 ≥ .45 / grounded ≥ 50% / EOS ≥ 60%)는 A1 native **.6552 / 100% / 100%**보다 낮다. 통과해도 제품 후보가 아니다.
- mT5-small의 ~250k vocabulary embedding/LM head 때문에 “경량 decoder”의 RAM 이점도 아직 정량화되지 않았다.
- B2의 cross-model CE는 tokenizer가 달라 직접 비교할 수 없다. B2는 **같은 layer에서의 conditional model-package 비교**로 한정하고, generation 중심으로 봐야 한다.
- B2의 UMT5는 Stage A에서 train ≈ val ≈ 8.3으로 거의 학습되지 않아 **optimization confound**가 있다.

---

## 3. Q1~Q10 판정 행렬

기호: **C** conditional, **A** agree, **D** disagree, **DF** defer.

| 질문 | GLM | Opus | Sol | 종합 |
|---|---|---|---|---|
| Q1 role probing 설계 | C | D → redesign | C | **재설계 전 사용 보류** |
| Q2 Stage A 해석 | C | D | D | **underfit screening; bottleneck 결론 아님** |
| Q3 B0 layer19 | C (+layer5 confirmatory) | C (fixed anchor, add arms) | C (fixed19, matched control) | **layer19 fixed anchor; “best” 아님; 추가 layer sweep 없음** |
| Q4 B0 DoD | C | D | D | **DoD v2 재작성 필수** |
| Q5 B1 layer set | A | DF | C | **B0 통과 전 defer** |
| Q6 B2 model comparison | C | C | C | **defer; same-layer conditional, generation primary** |
| Q7 Stage C | C → 사실상 DF | D (계획에서 제외) | DF | **제외; 별도 decision** |
| Q8 metric | A + 수정 | A | D (현 C 기준 불충분) | **metric audit 선행; production 미수정** |
| Q9 T5Gemma2 재개 | A | A | A | **D-108 STOP 유지** |
| Q10 우선순위 | C (병렬 가능) | C (B0 first) | D (병렬 full role survey 반대) | **E0 → B0 first; full role survey defer** |

### Q별 핵심

- **Q1**: probing은 “accessibility survey”로만 유효하다. native offset, token-type baseline, doc-discriminability, token(t±k) identity, BH-FDR, doc-cluster bootstrap이 필요하다.
- **Q2**: `PARTIAL_MEMORY_USE_NO_CONTENT_SELECTIVITY`를 “frozen decoder 병목”으로 확장하지 말 것. Stage A는 fit하지 못했다.
- **Q3**: layer19는 **고정 anchor**로 유지하되 “best layer”로 부르지 않는다. 첫 B0에서 layer5/12를 추가하지 않는다.
- **Q4**: matched control, `Δshuffled_copy`, real-memory gain, 다중 donor, docs×seeds hierarchical bootstrap, inconclusive category가 필요하다.
- **Q5**: B1은 B0 통과 후 5/9/12/19의 bounded study로만.
- **Q6**: 같은 layer에서 mT5 vs UMT5를 비교하되, tokenizer/optimizer 차이 때문에 generation 중심의 conditional 비교.
- **Q7**: Stage C는 이 계획에서 제거. A1 matched comparison + metric audit + resource model + 새 decision 필요.
- **Q8**: `grounded` no-new-only를 preservation과 혼동하지 말 것. entity audit 필수.
- **Q9**: T5Gemma2 D-108 STOP 유지. external K/V 분리도 새 decision 없이는 재개 금지.
- **Q10**: tokenizer/wiring E0 → B0. full role survey와 B1/B2/C는 뒤로.

---

## 4. 통합 Must-fix

| # | Must-fix | 등급 | 조치 |
|---|---|---|---|
| **MF1** | Native tokenizer provenance | **Blocker** | 300/100 문서를 legacy T5Gemma2 vs EG2 native로 tokenize해 ID/offset/length/special/truncation 불일치율 측정. B0/B1은 native cache만 사용. Stage A cache는 legacy screening으로 표기 |
| **MF2** | mT5/UMT5 LoRA attach | **Blocker** | `q/k/v/o` decoder-only attach, 예상 module 수 assert, zero-output LoRA = frozen forward, module 목록·trainable count 기록 |
| **MF3** | B0 matched arms | **High** | frozen adapter-only / adapter+decoder LoRA / native encoder positive / memory-free or mean-memory negative. 동일 data·seed·donor·tokenizer |
| **MF4** | B0 DoD v2 | **High** | primary `Δshuffled_copy`; source-copyable target tokens; ≥5 length-matched derangements; docs×seeds hierarchical bootstrap; real-memory gain; generation all val20; **inconclusive branch**, hard STOP 금지 |
| **MF5** | Role probing redesign | **Medium** | native offsets, source-derived slot primary, token-type/position baselines, token identity + doc discriminability, BH-FDR, doc-cluster bootstrap, 2 seeds. B0 이후 |
| **MF6** | Metric audit | **High** | no-new vs preservation 분리, required-slot recall, entity audit, bag-character F1, repetition/length. production verifier 미수정 |
| **MF7** | Scope discipline | **High** | Stage C 제외, B1/B2는 새 decision, A1 native와 bridge 수치 분리, T5Gemma2 D-108 유지, test 163 sealed |

### 실행 순서

```text
E0  native tokenizer / wiring / LoRA attach audit     (무훈련, ≤1 CPU-h)
  ↓
B0  matched frozen-vs-adapted diagnostic              (사전등록 후 승인)
  ↓
새 decision → B1 bounded layer study
  ↓
새 decision → B2 conditional model comparison
  ↓
별도 decision + metric audit → Stage C
```

- **B0와 role probing을 병렬로 크게 돌리지 않는다.** E0와 cache provenance만 공유한다.
- **B0 실패를 bridge 전체의 영구 종료로 자동 일반화하지 않는다.** 반대로 B0 성공도 B1/B2/C 자동 승인이 아니다.

---

## 5. 이견과 미합의

| 쟁점 | GLM | Opus | Sol | 종합 처리 |
|---|---|---|---|---|
| 최종 판정 | CONTINUE 조건부 | NARROW | NARROW | **NARROW** (2/3), 단 B0 1개는 허용 |
| B0 layer | layer19 + layer5 confirmatory | layer19 하나, arms를 늘림 | layer19 하나, matched control | **첫 B0는 layer19 하나. layer5는 B0 이후 선택** |
| B0 규모 | 20/20, 100 step, 3 seeds | 300/100, ~900 step, 4 arms | 20/20, 2 arms, 3 seeds, 100 update | **미합의. E0 후 별도 사전등록에서 결정** |
| Role probing 시점 | B0와 병렬 가능 | B0 전면 보류, cheap diagnostics만 | B0 후로 연기 | **B0 first; full survey defer** |
| Stage C | 제외 | 계획에서 제거 | defer | **제외/별도 decision** |
| Tokenizer | audit 후 native re-cache | B0는 native 필수 | E0 native/wiring audit | **일치: native cache 필수** |

**가장 중요한 미합의**는 B0의 데이터 규모다. 20/20은 빠르지만 underpowered하고, 300/100은 전력이 낫지만 CPU 비용이 크다. 이 값은 **E0 결과와 사용자 예산 승인 후** 고정해야 하며, 결과를 본 뒤 바꾸면 안 된다.

---

## 6. 권고 다음 단계

### 즉시 가능 — 승인만 필요, 학습 없음

1. **E0 native-input audit**
   - 300 train + 100 val을 legacy T5Gemma2 tokenizer와 EG2 native tokenizer로 각각 tokenize
   - 문서별 ID 일치율, 위치별 mismatch, digit/slot span mismatch, length/truncation 차이
   - `summarize: ` prefix 유지 여부를 명시적 입력 선택으로 기록
   - EG2 layer19 native cache 1회 추출
   - native mT5 encoder forwarding과 external memory forwarding의 logits/loss 일치 확인
   - mT5 LoRA attach module 수 assert
   - per-layer RMS/outlier 통계(선택)

2. **B0 사전등록서 작성**
   - E0 결과를 반영해 native cache, layer19, arm 수, data size, seed, donor, DoD를 고정
   - **B0 실행 전 사용자 승인**
   - 결과를 본 뒤 threshold를 바꾸지 않는다

### B0 설계 권고

- **최소안(Sol)**: 20/20, 2 arms(frozen adapter-only vs adapter+LoRA), 3 seeds, 100 update. 빠른 causal contrast.
- **강화안(Opus)**: 300/100, 4 arms(native positive, memory-free negative 포함), ~900 step, 3 seeds. 전력은 높지만 비용 큼.
- **절충 권고**: E0 후 **최소안으로 wiring과 방향성만 확인**하고, B0 결과가 inconclusive/weak이면 **300/100 강화안을 새 decision으로** 수행한다. 어느 쪽이든 **B0 하나로 B1/B2/C를 자동 승인하지 않는다.**

### 하지 말 것

- Stage A legacy cache와 native cache를 한 분석에서 혼합
- layer19를 “best layer”로 표기
- `Δzero`를 memory 사용 증거로 사용
- 20문서 B0 실패를 bridge 전체 STOP으로 일반화
- role probing 결과로 B0 layer를 사후 선택
- Stage C를 이 계획의 자동 다음 단계로 실행
- T5Gemma2 bridge 재개

---

## 7. 검토 비용·산출물

### API 사용량

| 모델 | LLM 비용 | VM 비용 | 합계 | input tokens | output tokens | runtime |
|---|---:|---:|---:|---:|---:|---:|
| GLM 5.3 Flash max | $0.089651 | $0.026272 | **$0.115923** | 1,066,274 | 58,583 | 266.6s |
| Opus 5.5 medium | $0.939901 | $0.025608 | **$0.965509** | 393,415 | 21,898 | 250.2s |
| Sol 6.1 xhigh | $0.610614 | $0.024698 | **$0.635312** | 857,067 | 23,872 | 418.8s |
| **합계** |  |  | **$1.716744** |  |  |  |

### 원문

- `docs/hoplite/c5_layer_plan_2026-11-08/review_GLM.md` (28,021 B)
- `docs/hoplite/c5_layer_plan_2026-11-08/review_OPUS.md` (24,451 B)
- `docs/hoplite/c5_layer_plan_2026-11-08/review_SOL.md` (43,794 B)
- `docs/hoplite/c5_layer_plan_2026-11-08/threads.json`
- `docs/hoplite/c5_layer_plan_2026-11-08/prompt_{glm,opus,sol}.txt`
- `docs/hoplite/c5_layer_plan_2026-11-08/dispatch.sh`
- `docs/hoplite/c5_layer_plan_2026-11-08/watch_reviews.py`

### 재현·검증

- 모든 검토자는 **618줄 전문**을 직접 읽었다고 명시했다.
- 세 검토 모두 **test 163 미사용, P1 미사용, subagent/추가 LLM 미사용, production verifier 미수정**을 선언했다.
- 검토 기준 HEAD는 `bb8bf70`으로 동일하다.
- 원시 Stage A 수치와 `c5_eg2_all_layers_cache.py`의 tokenizer 사용은 이 종합에서 다시 대조했다.
- **이 리뷰는 계획 검토이며 gate 변경 승인이 아니다.**

---

## 8. 최종 요약

```text
Stage A        = underfit screening, causal bottleneck 아님
Layer 19       = fixed anchor, "best" 아님
Tokenizer      = T5Gemma2 IDs → EG2, native re-cache 필수
B0 as written  = confounded + underpowered + LoRA attach 위험
Role probing   = native offset + shortcut 통제 + FDR 전에는 보류
B1/B2/C        = B0 통과 후 새 decision
T5Gemma2       = D-108 STOP 유지
A1 native      = frozen fallback/reference, 제품 승인 아님
Final          = NARROW — E0 + 통제된 단일 B0만
```

---

## 9. E0 addendum — tokenizer 우려의 정정 (2026-11-09)

E0 audit 300 train + 100 val 결과:

- EG2 native와 T5Gemma2 tokenizer의 **content token ID는 400/400 일치**했다.
- 차이는 **native EOS 1 token**뿐이었다. character/digit mismatch는 **0**.
- 다만 native EOS 추가로 layer19 hidden cosine은 train mean **.99135**(p01 .9275), val **.99150**(p01 .9292)였고, 약 **2.4% token**이 cosine < .95였다.
- 따라서 **“T5Gemma2 tokenizer ID가 EG2 PLE를 광범위하게 오염시켰다”는 우려는 content 기준으로 재현되지 않았다.** native cache는 **EOS/sequence semantics 보존**을 위해 계속 사용하되, Stage A legacy cache를 “wrong IDs”라고 부르지 않는다.
- E0의 mT5 wiring은 native encoder vs external `encoder_outputs`에서 loss/logits delta **0.0**으로 PASS했고, decoder는 `q/k/v/o` **64 modules**를 노출했지만 legacy `q_proj` target은 **0**이었다. B0 LoRA runner는 아직 구현되지 않았다.
- **Post-E0 (D-114):** `runner/c5_mt5_lora_b0.py` smoke에서 **64/64 modules attach**, zero-output LoRA가 frozen forward를 **loss/logits delta 0.0**으로 재현했다. **B0 학습은 아직 미실행**이며 native positive/memory-free/mean controls는 추가 구현이 필요하다.
- 상세: `reports/C5_E0_NATIVE_AUDIT_2026-11-09.md`, `reports/C5_B0_LORA_RUNNER_SMOKE_2026-11-09.md`, `reports/provenance/C5_e0/`.
