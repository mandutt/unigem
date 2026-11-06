# C5/F5 A2-null 외부 검토 요청서 — 2026-11-06

## 0. 한눈에 보는 결론

- F5(메모리용 추상 요약)의 **A0 추출형 baseline**은 완료됐다. clean test 163에서 grounding 위반 **0/163**, char F1 **0.6072**.
- **A2-null exploratory**는 EG2 text의 null space를 T5Gemma2 decoder에 주입하는 실험이다. 수학·feature 추출·adapter 학습까지 완료했지만, **adapter-only 1 epoch로는 생성이 반복 붕괴**한다.
- 가장 좋은 A2-null 결과도 val 5건에서 char F1 **0.2297**, grounded **0/5**, new slot **0.96**이다. A0보다 훨씬 낮고, 환각·반복이 남아 있다.
- 2026-11-06 현재 **test 163은 봉인**되어 있고, A1(T5Gemma2 LoRA)은 아직 시작하지 않았다.
- 이 문서의 핵심 질문은 **“A2-null에 decoder LoRA를 한 번 더 투자할 것인가, 아니면 A1로 전환할 것인가”**다.

이 문서는 다른 AI가 저장소를 읽지 않아도 판단할 수 있도록 작성했다. 모든 수치는 이 문서 작성 시점의 `reports/`·`logs/` 원장과 대조했다.

---

## 1. 검토 목적

다음을 검토받고 싶다.

1. A2-null의 **실험 설계·학습·평가**에 논리적 결함이나 코드 버그가 남아 있는가.
2. 현재 결과를 **“adapter-only A2-null은 실패”**로 해석하는 것이 정당한가.
3. 다음 투자 순서가 **full val 161 → decoder LoRA → A1** 중 무엇이 합리적인가.
4. A2-null을 계속할 경우 **사전등록할 gate와 중단 규칙**은 무엇인가.
5. A2-null을 중단하고 A1로 갈 경우, A2-null에서 얻은 교훈을 A1에 어떻게 반영해야 하는가.
6. **F5에서 만드는 EG2→T5Gemma2 decoder bridge가 F4(맞춤법 교정)와 향후 F3(비전 태깅 확장)에 미치는 영향**을 지금 어디까지 설계·기록해야 하는가.

제품 채택을 승인해 달라는 요청이 아니다. **탐색 실험의 계속/중단 판단**을 위한 검토다.

---

## 2. 프로젝트와 F5 정의

### 2.1 프로젝트

- 저장소: `C:\code\unigem` (비공개)
- 목표: EG2(EmbeddingGemma 2) 상주 인코더를 재사용해 F1~F6 기능을 검증.
- 현재 활성 라인: **F5 — 메모리용 중요정보 요약**.
- STT(F2)는 **D-079로 동결**되어 이 검토 범위가 아니다.
- 실행 환경: Windows 11, Ryzen 5 7600 6C/12T, RAM 15.6GB, **GPU 없음(CPU only)**, Python 3.12, torch CPU, transformers 5.22.1.

### 2.2 F5 과제

- 입력: 한국어 뉴스/기사 passage.
- 출력: **3~5문장 추상 요약**.
- 목적: 메모리에 저장할 중요 정보를 요약하되, 원문에 없는 **slot(날짜·숫자·금액·버전·URL·경로·식별자)** 을 만들지 않는다.
- A0 추출형은 기준선이며 최종 구현이 아니다. 최종 목표는 추상 요약이다.

### 2.3 데이터

- 원본: `data/external/f5_pairs_v3.jsonl` — **2,000쌍**.
  - AI Hub 022 원문 passage를 LLM이 3~5문장 추상 요약한 쌍.
  - P0 등급 데이터만 사용. P1 개인 원문은 사용하지 않는다.
- 감사 결과 원본 target에는 신규 slot이 **6.7801%** 있어 G-C5를 위반했다.
- **clean 1,617쌍**을 primary로 확정:
  - 신규 slot이 있는 383건을 제외.
  - target 문장을 수정하지 않아 보존적.
- clean split(seed 42): **train 1,293 / val 161 / test 163**.
- repaired 1,953쌍은 secondary 민감도 분석용이며 이번 학습에는 쓰지 않았다.

### 2.4 G-C5

- **grounding rate ≥ 99%**
- **신규 slot ≤ 1%** (검증기 통과분의 신규 slot 0)
- 원문 대비 coverage는 **참고 지표**이며 gate가 아니다(뉴스 요약은 숫자를 생략하는 것이 정상).
- slot 검증기: `eval/slot_verify.py`; 11개 단위 테스트 통과.

### 2.5 A0 기준선

A0는 decoder 없이 원문 문장을 선택하는 추출형 baseline이다(`max_sentences=4`, `max_chars=500`).

| 데이터 | test n | strict reject | grounding reject | 원문 대비 coverage | 신규 slot | 압축률 | char F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 원본 v3 | 200 | 149 (74.50%) | 0 | 0.7770 | 0.0000 | 0.2557 | 0.6095 |
| **clean** | **163** | 118 (72.39%) | **0 (0.00%)** | 0.7820 | 0.0000 | 0.2524 | **0.6072** |
| repaired | 196 | 158 (80.61%) | 0 | 0.7597 | 0.0000 | 0.2653 | 0.6027 |

A0는 추출형이라 신규 slot이 0이지만, 추상 요약기가 아니고 원문 장문을 그대로 복사한다. **A2-null과 A0의 char F1을 동일 조건의 품질 비교로 과대해석하면 안 된다.** 그래도 A2-null의 현재 결과(0.23)가 A0(0.61)보다 크게 낮다는 사실은 중요하다.

> **split 주의:** A0 수치는 clean **test 163**, A2-null 수치는 **val 5**다. 같은 표본이 아니므로 두 char F1을 직접 비교하지 않는다. A2-null의 test 163은 아직 봉인되어 있다.

### 2.6 F5 밖의 영향 — F4·F6·F3와의 접점

이 실험은 F5 하나의 요약기만 만드는 작업이 아니다. **EG2 768d/512d 표현을 T5Gemma2 640d decoder에 연결하는 bridge**를 만드는 작업이며, 이 bridge는 향후 텍스트 생성형 기능과 공유될 수 있다.

| 기능 | 현재 계획 | T5Gemma2 decoder 의존 | 이번 A2-null과의 관계 |
|---|---|---|---|
| **F5 메모리 요약** | 추상 요약, A1(T5Gemma2 LoRA) 목표 | **직접 사용** | 현재 실험의 본체 |
| **F4 맞춤법 검사·교정** | 규칙 + 디코더 후보 재순위 또는 edit 태깅. F4-v2는 규칙+LM 점수 | **조건부** — 생성형/재순위 경로에서 decoder 사용 가능 | A2-null adapter/LoRA가 재사용될 수 있음. 단 D-042가 EG2 text hidden의 F4 제품 경로 사용을 금지 |
| **F6 STT 후처리 교정** | CTC 출력 → decoder 교정·정규화 | **직접 사용 가능** | D-6 A1-all은 F5+F6+F4 identity를 한 LoRA로 학습하는 계획이었음. F2(STT)는 D-079로 동결 |
| **F3 비전 태깅** | 현재는 **이미지 검색·이모지 태깅**이며 decoder를 쓰지 않음 | **현재 없음** | 현재 F3는 영향 없음. **향후 F3를 비전→텍스트 생성/태깅으로 확장할 때만** decoder bridge가 관련 |

핵심 구분:

- **F3 현재 구현은 decoder를 사용하지 않는다.** “F3 확장”은 vision tower → text decoder로 가는 새 요구가 생길 때의 이야기이며, 이번 F5 실험 결과로 F3가 직접 바뀌지는 않는다.
- **F4는 이미 decoder 경로 후보가 있다.** F4-v2는 규칙+LM 점수 중심이지만, 생성형 교정/재순위 경로를 택하면 F5의 decoder bridge와 LoRA 자산이 재사용될 수 있다.
- **F6는 F4와 같은 decoder 계열**이며, D-6 A1-all(F5+F6+F4 identity)은 공유 LoRA를 전제로 했다. F2는 동결이지만 F6 데이터·설계 자체는 남아 있다.
- 따라서 F5에서 **decoder LoRA를 F5 전용으로 급히 확정하면**, 나중에 F4/F6 멀티태스크와 충돌할 수 있다. 반대로 지금 공유 인터페이스를 과도하게 설계하면 F5 탐색 속도가 떨어진다.
- 이 검토요청서는 **F4/F6/F3 코드를 승인하거나 실행하지 않는다.** 영향 가능성과 인터페이스 경계를 기록하는 것이 목적이다.

> **D-042 경계:** D-042는 EG2 text hidden을 F4/F5 **제품 경로**에서 쓰지 않는다는 결정이다. A2-null은 exploratory이며, F4/F6에 이 bridge를 제품으로 재사용하려면 **별도 결정**이 필요하다. 이 문서는 그 재사용을 승인하지 않는다.

---

## 3. A2-null이 무엇인가

### 3.1 배경

참고한 공개 실험은 `google/embeddinggemma-2`의 **audio retrieval pooled embedding**을 개선한 것이다.

```text
text/audio hidden → W(768×512) → 768d embedding
                         └ left null space 256d ← intermediate audio layer PCA 256
```

원 방법은 **학습 없이** audio null space에 intermediate Conformer layer 특징을 채워 MAEB audio benchmark를 개선했다. text embedding은 bit-for-bit 변하지 않는다.

우리의 A2-null은 이를 **text token sequence + T5Gemma2 decoder**에 적응한 **exploratory 변형**이다. 원 방법을 그대로 재현했다고 주장하지 않는다.

### 3.2 수식

```text
h_t       = EG2 text final hidden (512)
x_t       = PCA_256(EG2 intermediate hidden at t)   # 512 → 256
W         = EG2 final projection (768×512)
P         = left null basis of W (768×256), WᵀP = 0
z_t       = W h_t + P x_t                         # 768
memory_t  = Adapter(z_t)                            # 768 → 640
```

- `W h_t`는 원래 EG2 final projection과 같은 768d 공간.
- `P x_t`는 W의 column space와 직교하는 256d.
- adapter만 학습; T5Gemma2 decoder와 EG2 원본은 동결.
- **A2-null-seq**(token-level)가 primary, pooled 변형은 reference.

### 3.3 D-042와 D-081

- **D-042**: EG2 text hidden을 F4/F5 **제품 경로**에 쓰지 않는다. P1 F4에서 EG2 hidden이 baseline 대비 +2.83%p로 기준 +3.0%p에 미달했기 때문이다.
- **D-081**: A2-null은 raw hidden과 다른 **새 표현**이므로 **exploratory만** 허용한다. 제품 채택은 A1과의 val 비교 + 새 결정 전 금지. test 163은 봉인.
- **A1은 별도 계획의 우선 후보**다(`docs/plan_c5_abstractive_v0_1.md`). A2-null은 A1을 대체하지 않으며, A1 결과 없이 제품 방향을 확정하지 않는다.

즉, 이 실험은 “D-042를 폐기”하는 것이 아니라 **D-042를 유지한 채 별도 표현을 탐색**하는 것이다.

---

## 4. 실측 1 — 수학·구조·feature

### 4.1 Null-space 검증

| 항목 | 값 |
|---|---:|
| W shape | **768 × 512** |
| rank | **512** |
| nullity | **256** |
| singular min / max | 10.5177 / 122.43 |
| `max\|WᵀP\|` | **4.2915e-06** |
| `max\|PᵀP − I\|` | 4.77e-07 |
| final projection 재현 오차 | **0.0** |
| projection 입력 | **post-norm 512d** |
| null injection vs final dot max | 0.00475 |

→ 수학적으로 A2-null의 전제는 성립한다.

### 4.2 PCA layer 선택

train 일부에서 layer별 PCA 256 explained variance:

| layer | probe 10건 | full 200건 |
|---|---:|---:|
| 2 | 0.9028 | — |
| 6 | 0.9456 | — |
| **12** | **0.9510** | **0.9409789** |
| 18 | 0.9278 | — |
| 23 | 0.8937 | — |

layer 12를 사용했다. top1 0.0689, tokens 152,846.

### 4.3 Feature cache

- 경로: `data/wave2c/a2null/`
- 크기: **2.4GB**, float16, max 1024 tokens.
- train **1,293** (length 629~910), val **161** (622~865), test **163** (665~875).
- NaN **0**.
- `z` [n, maxT, 768], `mask`, `lengths`, `ids`.
- PCA: layer 12, 200 records, explained variance **0.9409789**, `pca_sec 205.4`, `elapsed_sec 1792.4`.

### 4.4 T5Gemma2 external memory

- `encoder_outputs=BaseModelOutput(last_hidden_state=memory)` + `attention_mask`.
- memory는 **640d bf16만** 허용. 512/768d는 shape 오류.
- decoder는 **18층, hidden 640, 4 heads, bf16, 완전 frozen**.
- T5Gemma2는 **self/cross merged attention**을 쓴다:
  - `q_proj: 640→1024`
  - `k_proj: 640→256`
  - `v_proj: 640→256`
  - `o_proj: 1024→640`
- 따라서 T5의 별도 `EncDecAttention`처럼 “cross-attention만” 떼어내는 XA-only 실험은 **직접 이식할 수 없다**.

---

## 5. 실측 2 — 학습과 생성 결과

### 5.1 공통 학습 설정

| 항목 | 값 |
|---|---:|
| adapter | `Linear(768→768) → GELU → Linear(768→640)` (+ 후속 LN arm) |
| train / val | 1,293 / 161 |
| batch | 1 |
| lr | 1e-4 |
| optimizer | AdamW |
| clip | 1.0 |
| epoch | 1 |
| max_memory | 1024 |
| max_target | 512 |
| T5 | frozen, bf16 |
| threads | 6 |
| eval | val 5건, greedy, **max_new 128 (평가 상한; target p95 289보다 작음)** |

**★max_new=128의 한계:** clean target(content+EOS)의 token 길이는 mean **208.9**, p50 **204**, p90 **268**, p95 **289**, p99 **333**, max **439**다. 128 상한은 p50보다 작아 EOS 0/5와 char F1 recall이 **상한 절단(censoring)** 영향을 받는다. 이 결과를 “EOS를 전혀 배우지 못했다”로 단정하지 않는다. full val에서는 512 상한(또는 1.5×p95=434 이상)으로 재평가해야 한다.

### 5.2 학습 이력

| arm | label | train loss | val loss | elapsed | val5 char F1 | grounded | new slot | eos |
|---|---|---:|---:|---:|---:|---|---:|---:|
| 1차 full | **결함** `<bos>` 포함, `<eos>` 없음 | 3.2487 | 3.1196 | 44.1분 | 0.1603 | 0/5 | 0.90 | 0/5 |
| 2차 full | `content + <eos>` | 3.2525 | 3.1160 | 42.3분 | **0.2297** | 0/5 | 0.96 | 0/5 |
| 3차 full | EOS + `LayerNorm × 5` | 3.2513 | 3.1288 | 42.7분 | 0.2269 | 0/5 | 0.8667 | **1/5** |

**1차 full은 label 결함 때문에 A2-null 성능 근거로 사용할 수 없다.** `data/models/f5_a2null_full`의 adapter는 폐기 대상이다.

### 5.3 확정된 label 결함

T5Gemma2 tokenizer는 summary 앞에 `<bos>`를 자동으로 붙이지만 `<eos>`는 붙이지 않는다.

```text
tokenizer(summary) = [<bos>, ...content..., .]
```

기존 label은 이 출력을 그대로 사용했다.

```text
labels        = [<bos>, ...content..., .]   # eos 없음
decoder_input = [<bos>, <bos>, ...content...]  # shift 후
```

→ decoder가 첫 token으로 `<bos>`를 배우고, `<eos>`를 배우지 못한다. 수정 후:

```text
labels        = [...content..., <eos>, -100, -100, ...]
decoder_input = [<bos>, ...content..., <eos>, <pad>, ...]
```

수정 후 2-step smoke는 exit 0, 20-step pilot은 여전히 미학습 붕괴(20 step 한계)였다.

### 5.4 LayerNorm×5 arm

adapter 출력 scale을 T5 encoder hidden에 맞추기 위해 추가:

```text
Linear(768→768) → GELU → Linear(768→640) → LayerNorm(640) → ×5
```

근거(실측):

| 대상 | std | norm mean | norm max |
|---|---:|---:|---:|
| 기존 adapter 출력 | 10.4~12.9 | 162~211 | 1,912~2,100 |
| T5Gemma2 encoder hidden | 5.08 | 126.3 | 404.7 |

LayerNorm은 EOS 1건과 신규 slot을 약간 개선했지만, **char F1은 EOS 수정보다 낮고 grounded는 여전히 0/5**였다. **스케일 불일치가 주원인은 아니었다.**

### 5.5 Val 5건 상세

EOS 수정 arm:

| id | gen_len | eos | char F1 | grounded | new slot |
|---|---:|---|---:|---|---:|
| REPORT-news_r-00365-00001 | 129 | False | 0.0628 | False | 1.00 |
| REPORT-news_r-00420-00001 | 129 | False | 0.2462 | False | 1.00 |
| REPORT-news_r-02318-00002 | 129 | False | 0.2727 | False | 1.00 |
| REPORT-news_r-04679-00001 | 129 | False | 0.3388 | False | 0.80 |
| REPORT-news_r-03915-00001 | 129 | False | 0.2277 | False | 1.00 |

EOS + LN arm:

| id | gen_len | eos | char F1 | grounded | new slot |
|---|---:|---|---:|---|---:|
| REPORT-news_r-00365-00001 | 129 | False | 0.1893 | False | 0.6667 |
| REPORT-news_r-00420-00001 | 129 | False | 0.1606 | False | 1.00 |
| REPORT-news_r-02318-00002 | **123** | **True** | 0.3227 | False | 1.00 |
| REPORT-news_r-04679-00001 | 129 | False | 0.3135 | False | 0.6667 |
| REPORT-news_r-03915-00001 | 129 | False | 0.1486 | False | 1.00 |

출력 예:

```text
"10일 서울 강남구 신촌동에 위치한 롯데백화점 롯데백화점 롯데시네마 롯데백화점 롯데시네마 ..."
"이재명(32)은 2018년 10월 15일 서울 강남구 신촌동에 100여명의 학생을 둔 100여명의 학교에서 ..."
```

대부분이 **128 token 상한까지 반복**했고, EOS+LN에서 1건만 `<eos>`에서 멈췄다.

### 5.6 평가 지표 정의

- `char_f1`: 공백 제거 후 문자 bag의 F1. ROUGE가 아니다.
- `grounded = not rep.new`: 요약에 **새 slot이 하나도 없어야** True.
- `new_slot_rate = len(new) / summary_count`: 요약 slot 중 새 slot 비율.
- `slot_preservation = preserved / source_count`.
- val 5건은 **val shard의 첫 5건**이며 무작위 표본이 아니다.
- test 163은 사용하지 않았다.

### 5.7 현재 상태

- 활성 학습·watchdog 프로세스 **없음**.
- A2-null test 163 **봉인**.
- A1(T5Gemma2 LoRA) **미착수**.
- A2-null adapter-only 결론: **usable하지 않음**.

---

### 5.8 아직 하지 않은 것

- full val 161 생성 평가 — **val 5건만**
- ROUGE-L / BERTScore
- 사람 50건 검토
- **zero-shot T5Gemma2**(native encoder + frozen decoder) 통제
- **A2-null-raw control**(null injection 없이 final 768→adapter→decoder)
- **A2-null-pooled reference**
- A1과의 직접 비교
- test 163 — **봉인**

이 중 full val 161, raw control, A1 비교가 없으면 A2-null의 **인과적 기여**를 확정할 수 없다.

## 6. 왜 실패했는가 — 가설과 이미 배제한 것

### 6.1 이미 배제한 가설

| 가설 | 검증 | 결과 |
|---|---|---|
| null-space 수학 오류 | SVD, `WᵀP`, `PᵀP` | 성립 |
| T5 external memory 호환 오류 | 640d forward | 성립 |
| target label `<bos>`/`<eos>` | tokenizer 검사, 재학습 | **수정함**, 그래도 실패 |
| adapter 출력 scale | LayerNorm×5 | 약간 개선, 실패 |
| T5Gemma2 cross-attn cache 버그 | 5.22.1 소스 확인 | 현재 해당 없음 |
| `decoder_start_token_id` | config `None` → bos fallback | 학습·생성 bos 일치 |
| attention mask | T5 forward/generate 경로 확인 | 정상 |

### 6.2 남은 가설

1. **decoder가 완전 frozen** — adapter가 memory를 바꿔도 decoder의 cross-attention/self-attention이 새 분포에 적응하지 못한다.
2. **adapter 용량 부족** — 768→768→640 약 1.08M params만으로 1,293개 요약을 학습하기 어렵다.
3. **teacher forcing과 free-running 불일치** — val loss 3.12가 생성 품질을 보장하지 않는다.
4. **EOS class imbalance** — 평균 약 209 token 중 1개라 1 epoch로는 EOS 확률이 충분히 올라가지 않는다. (128 상한 절단과 혼재)
5. **A2-null-seq의 구조적 부적합** — 원 방법은 pooled retrieval embedding이고, token-level decoder memory는 검증된 적이 없다. T5 cross-attention에는 external memory의 명시적 위치 정보가 없다.
6. **데이터/목표 불일치** — F5 target은 추상 요약인데, EG2 text hidden은 검색·임베딩 목적 표현이다.

### 6.3 Exa 검색에서 확인한 외부 근거

| 출처 | 요지 | 우리 경우 |
|---|---|---|
| Encoder-decoder adapters (posttrainllm) | seq2seq에는 encoder self, decoder self, decoder cross-attn 세 적응 지점이 있고 cross-attn이 중요 | adapter만으로는 부족할 수 있음 |
| T5-large XA-only model card | decoder cross-attn + final norm만 13.7% 학습으로 SQuAD F1 0.8128; LoRA r8 0.8152; full 0.8162 | decoder 적응이 유효하다는 참고. 단 SQuAD 모델 카드이며 요약·T5Gemma2가 아님 |
| To Adapt or to Fine-tune (arXiv 2208.14559) | 일반적으로 full FT > adapter; 극저자원에서는 adapter가 대등 | 1,293쌍은 경계 구간 |
| LoRA multilingual summarization (arXiv 2311.08572) | LoRA는 저자원에서 안정적 | decoder LoRA 근거 |
| T5Gemma2 #45521/#45540 | encoder 길이 ≥ sliding_window에서 cross-attn cache 버그 | 5.22.1에서 수정, memory 629~910이라 해당 없음 |
| Neural text degeneration (1904.09751) | likelihood/beam search가 반복을 선호 | 반복 붕괴 해석 |
| Unlikelihood training (1908.04319) | 반복 token 확률을 낮추는 objective | 아직 적용하지 않음 |
| DITTO (2206.02369) | 문장 반복의 self-reinforcement | 반복 붕괴 해석 |
| Exposure bias (2109.08705) | teacher-forced loss와 free-running 불일치 | val loss 3.12와 생성 품질 괴리 |

**외부 사례는 preprint/모델 카드이며 우리 하드웨어·한국어 재현이 아니다.**

---

## 7. 다음 선택지

| 선택지 | 내용 | 예상 비용 | 장점 | 위험 |
|---|---|---|---|---|
| **A. full val 161 먼저** | EOS·LN adapter를 val 161 전체로 평가, 학습 없음 | 10~30분 | 5건 표본 한계 제거, 다음 투자 전 확증 | val 과적합 위험은 없지만 추가 학습 없음 |
| **B. decoder LoRA** | adapter + T5 decoder q/k/v/o LoRA(rank 8~16), 1 epoch | 구현 30~60분 + 학습 50~60분 | frozen decoder 병목 직접 공략 | merged attention이라 self/cross 동시 적응, overfit 가능 |
| **C. A1 T5Gemma2 LoRA** | native T5Gemma2 encoder+decoder LoRA, 2~3 epoch | 구현·smoke·학습 수시간 | T5Gemma2의 원래 encoder-decoder 정합성 | A2-null과 다른 경로, CPU 비용 큼 |
| **D. adapter-only 2 epoch** | 현재 구조에서 epoch만 증가 | 45분 | 싼 확인 | decoder 병목이면 반복 지속 가능 |
| **E. A2-null 중단** | 폐기, A1로 전환 | 0 | 시간 절약 | A2-null exploratory를 충분히 검증하지 못함 |
| **F. A2-null-raw control** | null injection 없이 final 768→adapter→decoder. `z_raw = z − (zP)Pᵀ`로 기존 cache에서 유도 가능 | 학습 ~45분 (feature 재추출 불필요) | injection 효과를 분리 | fp16 반올림·별도 cache 선택 |
| **G. A2-null-pooled reference** | pooled 768 1개 → adapter → decoder | 구현·학습 수십 분 | 원 Reddit 방법에 가장 가까운 축소 실험 | sequence 정보 손실 |

### 현재 권고(검토 전 잠정)

1. **full val 161**로 EOS·LN arm의 5건 우연성을 확인한다.
2. 여전히 grounded 0/161이고 char F1이 A0에 크게 못 미치면 **decoder LoRA를 1회** 시도한다.
3. decoder LoRA도 실패하면 **A2-null을 중단하고 A1로 전환**한다.
4. test 163은 어느 경우에도 최종 후보 1회만 사용한다.

---

## 8. 검토 질문

### Q1. 실험 설계

A2-null-seq가 **원 Reddit null-space 방법의 정당한 확장**인가? pooled retrieval embedding을 token-level decoder memory로 바꾸는 것이 과학적으로 의미 있는 실험인가, 아니면 너무 큰 외삽인가?

### Q2. 코드·label

EOS 수정은 충분한가? `content + <eos>`, `add_special_tokens=False`, `prepare_decoder_input_ids_from_labels()`의 bos prepend 조합에 남은 버그가 있는가? tokenizer·label·decoder input을 검증할 추가 체크가 필요한가?

### Q3. 결과 해석

val 5건에서 char F1 0.23, grounded 0/5, eos 0~1/5를 **“adapter-only A2-null 실패”**로 해석하는 것이 정당한가? 아니면 5건 표본이 너무 작아 INCONCLUSIVE인가?

### Q4. 다음 투자

full val 161, **A2-null-raw control**, decoder LoRA, A1, adapter 2 epoch 중 **다음 한 수**는 무엇인가? 그 이유는? raw control 없이 decoder LoRA를 먼저 하는 것이 인과 해석에 문제를 만들지 않는가?

### Q5. Decoder LoRA 설계

T5Gemma2가 merged self/cross attention이라 XA-only가 불가능할 때, decoder q/k/v/o LoRA가 최선인가? target module·rank·alpha·lr·epoch·gradient checkpointing에 대한 권고는?

### Q6. Gate

A2-null을 계속할 경우 **사전등록할 gate**는 무엇인가? 예를 들어:
- val 161에서 grounded ≥99%, new slot ≤1%
- char F1 ≥ A0?
- eos rate ≥90%
- copy rate / compression
- 사람 검토 50건
- test 163 1회

어떤 지표가 필수이고 어떤 지표가 참고인가?

### Q7. 평가 타당성

`grounded = not new_slot` 정의는 충분한가? 이 지표는 **새 slot이 없으면 True**이므로, slot이 없는 일반 문장의 사실 오류나 반복을 잡지 못한다. F5에 더 적합한 factual consistency / repetition / coverage 지표가 필요한가?

### Q8. A0 비교

A0는 추출형이라 char F1 0.6072, A2-null은 추상형이라 0.23이다. 이 비교가 공정한가? A0와 A2-null을 비교할 때 **char F1 외에** 무엇을 봐야 하는가?

### Q9. 중단 규칙

어느 시점에 A2-null을 중단해야 하는가? “decoder LoRA 1회 후에도 grounded 0이면 중단” 같은 규칙이 타당한가? 아니면 A1과의 val 비교 전에는 중단 판단을 보류해야 하는가?

### Q10. A1 전환 시

A1(T5Gemma2 native encoder-decoder + LoRA)로 갈 경우, A2-null에서 얻은 교훈(EOS label, external memory, decoder adaptation, evaluation)을 어떻게 반영해야 하는가? A1에서 먼저 확인할 **smoke 항목**은 무엇인가?

### Q11. 누락·반대 의견

이 검토요청서에서 빠진 결정적 사실이나, 우리가 범하고 있는 **확증 편향**이 있는가? A2-null을 계속하는 것이 매몰비용 추구인가?

### Q12. F4·F6 공유 decoder bridge

F5의 EG2→T5Gemma2 adapter/decoder LoRA를 **F5 전용**으로 두는 것이 맞는가, 아니면 처음부터 F4/F6가 재사용할 수 있는 **공유 decoder bridge 인터페이스**로 설계해야 하는가? 지금 공유 인터페이스를 설계하지 않으면 나중에 어떤 재작업이 생기는가?

### Q13. D-042와 재사용 경계

D-042가 EG2 text hidden의 F4/F5 제품 경로 사용을 금지하는 상황에서, A2-null exploratory의 adapter/LoRA를 F4/F6에 재사용하는 것은 **새 결정 없이 가능한가?** 가능하다면 어떤 조건(탐색 전용, test 봉인, 별도 gate)이 필요한가?

### Q14. F3 확장과의 관계

현재 F3는 decoder를 쓰지 않는 retrieval/emoji tagging이다. 향후 F3를 **vision→text tagging**으로 확장할 때, F5의 decoder bridge를 재사용하는 것이 합리적인가? 아니면 F3는 별도 vision decoder 경로로 분리해야 하는가?

### Q15. 멀티태스크 회귀

F5 decoder LoRA가 F4/F6의 기존 능력을 손상시키지 않는지 **retention/regression**을 지금 gate에 넣어야 하는가? 넣는다면 어떤 표본(정상 문장 보존, F6 교정쌍)과 지표를 써야 하는가?

---

## 9. 답변 형식

가능하면 아래 형식으로 답해 달라.

```text
1. 총평(한 줄): A2-null 계속 / full val 먼저 / A1 전환 / 중단
2. Q1~Q15 답변 (각 2~5문장, 근거 포함)
3. Must-fix (최대 5개, 우선순위)
4. 추가로 확인해야 할 실험 (최대 3개)
5. 이 문서의 사실 오류·과장·누락
```

관점:
- **실험 설계 관점**과 **ML 엔지니어링 관점**을 모두 포함해 달라.
- “A2-null이 재미있다”는 이유만으로 계속하지 말고, **A1 대비 기대 이득과 비용**을 기준으로 판단해 달라.
- 확실하지 않은 부분은 추정과 사실을 구분해 달라.

---

## 10. 재현 정보

### 10.1 주요 파일

| 역할 | 경로 |
|---|---|
| F5 데이터/A0 허브 | `reports/C5_summary.md` |
| A0 clean test | `reports/provenance/C5_clean/a0_eval.json` |
| A2-null 계획 | `docs/plan_c5_a2null_v0_1.md` |
| A2-null feasibility | `reports/C5_a2null_probe.md` |
| A2-null smoke/pilot | `reports/C5_a2null_smoke.md` |
| EOS retrain | `reports/C5_a2null_eos_retrain.md` |
| LayerNorm retrain | `reports/C5_a2null_ln_retrain.md` |
| 원인 조사/Exa | `reports/C5_a2null_search_2026-11-06.md` |
| slot 검증기 | `eval/slot_verify.py` |
| A2-null eval | `runner/c5_a2null_eval.py` |
| full train | `runner/c5_a2null_full_train.py` |

### 10.2 데이터·feature

- `data/external/f5_pairs_v3_clean.jsonl` — 1,617
- `data/wave2c/a2null/` — 2.4GB; `train_0000~0012`, `val_0000~0001`, `test_0000~0001`
- `data/models/f5_a2null_full_eos/adapter.pt` — EOS arm
- `data/models/f5_a2null_full_ln/adapter.pt` — LN arm
- `data/models/f5_a2null_full/` — **label 결함, 사용 금지**
- `reports/provenance/C5_a2null/a2null_eos_val5_predictions.jsonl`
- `reports/provenance/C5_a2null/a2null_ln_val5_predictions.jsonl`

`runner/c5_a2null_eval.py`는 adapter state에 `scale` key가 있는지로 LN/EOS arm을 자동 감지해 둘 다 로드한다(LN arm의 학습된 scale은 4.922).

### 10.3 커밋

| 커밋 | 내용 |
|---|---|
| `a43b765` | F5 A0/filter, CP3-1 |
| `b245995` | A2-null generation eval + pilot collapse |
| `dfd8247` | full feature extraction 기록 |
| `b1302e0` | full adapter training |
| `36ba46d` | **EOS label 수정** |
| `5277964` | EOS retrain watchdog |
| `1208c0a` | watchdog 15분 보고 |
| `5266fb1` | EOS retrain 결과 |
| `f06df58` | LayerNorm×5 arm |
| `33396f3` | LayerNorm 결과 |

**작성 시점 작업 트리 clean, origin/main 0/0.**

### 10.4 환경

```text
Windows 11
Ryzen 5 7600 6C/12T
RAM 15.6GB
GPU 없음
Python 3.12
torch CPU
transformers 5.22.1
```

---

## 11. 용어

| 용어 | 정의 |
|---|---|
| F5 | 메모리용 중요정보 요약 |
| A0 | 추출형 sentence selection baseline |
| A1 | T5Gemma2 native encoder-decoder + LoRA 계획 |
| A2-null | EG2 text null-space + adapter + frozen T5Gemma2 decoder |
| D-042 | EG2 text hidden을 F4/F5 제품 경로에 사용하지 않는 결정 |
| D-079 | STT(F2) 동결 |
| D-080 | F5 G-C5 grounding 기준, clean 1,617 |
| D-081 | A2-null exploratory 승인 |
| G-C5 | grounding ≥99%, 신규 slot ≤1% |
| CP3-2 | F5 A0 채택/보류 결정 지점 |
| grounded | 요약의 새 slot이 하나도 없음 |
| new_slot_rate | 요약 slot 중 원문에 없는 slot 비율 |

---

## 12. 마지막 요약

- **A2-null의 수학·feature·T5 external memory는 검증됐다.**
- **label 결함과 출력 스케일은 수정했지만, adapter-only 1 epoch는 반복 붕괴를 벗어나지 못했다.**
- 현재 val 5건 결과는 **exploratory**이며, full val 161·ROUGE·사람 검토는 아직 없다.
- **F5의 EG2→T5Gemma2 bridge는 F4/F6의 decoder 경로와 잠재적으로 공유된다.** F3는 현재 decoder를 쓰지 않지만, 향후 vision→text 확장 시 별도 판단이 필요하다. 이 검토요청서는 F4/F6/F3 코드를 승인하지 않는다.
- 가장 큰 미해결 질문은 **“decoder를 적응시키는 한 번의 추가 투자가 A1 전환보다 가치 있는가”**다.
