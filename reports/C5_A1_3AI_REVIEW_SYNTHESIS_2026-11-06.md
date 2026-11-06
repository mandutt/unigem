# C5 A1 + EG2→T5 bridge — 3-AI review synthesis (2026-11-06)

## 0. 메타

- 검토 대상: `reports/EXTERNAL_REVIEW_C5_A1_2026-11-06.md` (562줄)
- 검토 기준 HEAD: **`834d598`** (`docs: add A1 3-AI review prompts and dispatch`)
- 검토 모델
  - **GLM 5.3 Flash**, reasoning **max**, thread `thr_7ee6040e49024744b2aad2ac0b8ed6e0`
  - **Opus 5.5**, reasoning **medium**, thread `thr_3c27af4d1d0d4e21b5e53524c085b2a8`
  - **Sol 6.1**, reasoning **xhigh**, thread `thr_4bc68ec25581424ba76a9b6d60eaaed8`
- 모든 모델이 요청서 전문을 읽었고, **test 163은 열지 않았다**. P1 데이터·외부 LLM API·운영 자산 변경 없음.
- 원문
  - `docs/hoplite/c5_a1_2026-11-06/review_GLM.md` (205줄)
  - `docs/hoplite/c5_a1_2026-11-06/review_OPUS.md` (221줄)
  - `docs/hoplite/c5_a1_2026-11-06/review_SOL.md` (251줄)

---

## 1. 한눈에 보는 결론

**3/3 모두 “A1 full train을 지금 시작하되, 2 epoch의 사전등록 연구로 제한”**을 권고했다. 제품 채택·test 개봉 승인은 아니다.

| 사안 | 3-AI 합의 | 핵심 조건 |
|---|---|---|
| A1 full train | **전원 승인** | 2 epoch, 2,586 step, val-best 선택, pilot300 fallback |
| A2-null | **전원 제품 후보 종결** | raw control은 원인 규명용 exploratory로 보존 |
| B1d bridge | **전원 “범용 bridge의 첫 후보”** | 단, 현재 문서의 주입 인터페이스는 **오류** → `encoder_outputs`로 수정 |
| B3 bridge | **전원 “첫 실험이 아님”** | passage가 이미 encoder에 있어 EG2 사용을 입증하지 못함 |
| prefix | **전원 “초기 F5 프로토콜로 유지”** | bare val161을 추가 측정해 배포 계약 확정 |
| test 163 | **전원 “A1 최종 후보 1회만”** | B-family에는 test를 주지 않음 |
| 사람 50건 | **전원 “full train 후, test 전”** | stratified, blinded, 사실 오류·누락 rubric |

한 줄 요약:

> **A1은 “다음 실험”으로 승인됐고, “제품”으로 승인되지 않았다. 범용 EG2→T5 bridge는 B1d가 가장 유망하지만, 지금 문서의 B1d는 실행 경로가 자기모순이므로 코드 작성 전에 반드시 고쳐야 한다.**

---

## 2. D1–D6 판정 행렬

| 결정 | GLM 5.3 Flash | Opus 5.5 | Sol 6.1 | 합의 |
|---|---|---|---|---|
| **D1** A1 full train | 2 epoch, 조건부 승인 | 2 epoch 승인 | 2 epoch, bounded research | **2 epoch** |
| **D2** prefix | train+eval `summarize: ` 고정, bare val161 병행 | prefix 고정, bare val161 먼저 | prefix 초기 유지, bare/prefix paired val161 | **고정 + bare val161** |
| **D3** bridge | A1 먼저; B3가 아니라 **수정된 B1d 프로브** | A1 먼저; **B1d feasibility probe** | A1 먼저; **corrected B1d encoder-output distillation** | **B1d first, B3 아님** |
| **D4** A2 종결 | 제품 후보 종결 | 제품 후보 종결 | 제품 후보 종결 | **종결** |
| **D5** test 163 | A1 val-best 1개, 1회 | A1 1개, 1회 | A1 1개, 1회 | **A1 only, once** |
| **D6** 사람 50 | full train 후, test 전 | full train 후, val에서, test 전 | full train 후, blinded A0/A1, test 전 | **test 전** |

### 판정의 성격

- **GLM**: “제품 채택”이 아니라 “다음 실험 실행” 승인. Must-fix #1·#2를 적용한 뒤 시작.
- **Opus**: pre-registered experiment로 시작. 2 epoch, 4 checkpoints, val gate.
- **Sol**: capped two-epoch research run. test unsealing·제품 채택은 별도.

---

## 3. 3/3 공통 Must-fix

우선순위 순. “문서 수정”과 “새 실험”을 분리한다.

### M1. B1d 주입 인터페이스가 자기모순 — **문서 수정 필수**

현재 요청서 §3.7.4는 동시에 이렇게 말한다.

1. `H_s`를 **encoder `inputs_embeds`**로 넣는다.
2. 런타임에는 **T5 encoder를 쓰지 않는다.**

이 둘은 같이 참일 수 없다. `inputs_embeds`를 넣으면 encoder가 다시 실행된다. teacher target은 encoder의 **최종 출력** `last_hidden_state`인데, 이를 encoder 입력 공간에 다시 넣는 것은 분포도 위치도 다르다.

**수정안 — B1d는 `encoder_outputs` replacement로 고정한다.**

```python
model.generate(
    encoder_outputs=BaseModelOutput(last_hidden_state=H_student.to(base_dtype)),
    attention_mask=source_mask,
    # decoder start/eos/generation 설정은 그대로
)
```

이렇게 해야 “런타임 T5 encoder 미실행”이 참이 된다.

**별도 경로와 혼동 금지**

| 경로 | 주입 | 런타임 encoder | 대상 |
|---|---|---|---|
| **B1/B3 encoder-input** | `inputs_embeds` 앞 soft token | **실행됨** | encoder input interface |
| **B1d encoder-output** | `encoder_outputs.last_hidden_state` | **실행 안 됨** | encoder output replacement |

B1d는 이름은 “B1 계열”이지만 실제로는 **A2와 같은 주입 지점을 올바른 목적함수로 다시 푸는 실험**이다. 이 점을 문서에 명시해야 한다.

### M2. A1의 `slot_preservation`이 보고되지 않았다 — **가장 큰 평가 구멍**

원문 리포트가 저장 필드에서 재집계한 값:

| 항목 | A1 pilot300 val161 | A0 extractive val161 |
|---|---:|---:|
| `slot_preservation_mean` | **0.455827** | **0.801190** |
| slot 누락 문서 (<1.0) | **153/161** | — |
| `slot_preservation == 0` | **6/161** | — |
| `slot_preservation < 0.5` | **91/161** | — |
| summary slots/doc | **5.199** (837/161) | **8.752** |
| char F1 | 0.6576 | 0.6111 |

의미:

- A1은 **신규 slot은 0개**지만, 원문 slot을 평균 **54.4% 누락**한다.
- A1은 A0보다 **문서당 slot을 3.55개 적게** 만든다.
- `grounded 161/161`은 “새 slot이 없다”는 뜻이지 “사실이 보존됐다”는 뜻이 아니다.
- 6/161은 summary slot 자체가 0개인 **vacuous** 문서다. 이 6건은 `grounded`가 자동 통과한다.

**보고 규칙 (합의)**

- `grounded 155/155 (non-vacuous)`와 `6/161 slot-free (vacuous)`를 **분리**한다.
- G-C5의 기존 분모 161은 유지하되, non-vacuous 155를 별도로 표기한다.
- slot-free 6건은 사람 50건 표본에 **반드시 포함**한다.
- A0의 coverage 0.782와 A1의 slot_preservation 0.456을 같은 표에 둔다.
- “grounded 100%”를 “사실 안전 100%”로 쓰지 않는다.

### M3. Full train 프로토콜이 현재 코드에 없다 — **코드 수정 필수**

리뷰어들이 `runner/c5_a1_lora.py`를 직접 확인해 지적한 사항:

- 체크포인트 저장이 **종료 시 1회**뿐 → “val 161 best 선택”이 물리적으로 불가능.
- `--rank/--alpha/--dropout`는 argparse에 있으나 `build_model()`/`attach_lora()`에 전달되지 않는다. 현재는 항상 기본값 8/16/0.05.
- `order = torch.randperm(...)`가 한 번만 생성되고 epoch마다 같은 순서를 순환한다.
- `--steps 2586`만으로는 사전등록의 checkpoint selection/early stop이 구현되지 않는다.
- `model.gradient_checkpointing_enable`는 opt-in이고, 계획의 “batch 1 + gradient accumulation”은 runner에 없다.
- `--step-time` 중단 규칙은 문서에 있으나 학습 loop에 구현되어 있지 않다.

**따라서 full train 전에 필요한 것**

1. 647 / 1,293 / 1,940 / 2,586 step에 checkpoint 저장.
2. 각 checkpoint에서 val161 batch eval + teacher-forced val NLL 기록.
3. 선택 규칙 사전등록: safety gate → max char F1 → tie는 이른 checkpoint.
4. epoch별 재셔플, seed/ordering 기록.
5. rank/alpha/dropout을 실제 LoRA 구성에 전달.
6. adapter checkpoint에 prefix/max_input/max_target/tokenizer hash 저장.
7. step-time 60초 초과 중단 규칙 실제 구현.
8. pilot300을 fallback 후보로 보존.

### M4. H4′ 정렬 주장이 과장됐다 — **문서 수정 + token audit**

- H4′는 **코퍼스 v2 4,695문장의 token-string 분절 일치 100%**다.
- D-027은 **vocab id 불일치 6,186개 + `<eos>` 차이**를 기록했다.
- F5 passage, prompt, BOS/EOS, padding, truncation, position id에서 **재검증되지 않았다.**

B1d/B1a의 per-token loss 전에 실제 F5 입력에서 token id/offset/mask를 감사해야 한다. 실패하면 span-level resampling 또는 다른 정렬을 설계해야 한다.

### M5. Governance 누락 — **문서 수정**

- **D-082는 smoke 1 step + pilot 50~100 step만 승인**했다. pilot300은 그 범위를 넘었고, 이를 승인한 결정 기록이 없다.
- **D-042는 EG2 text hidden의 F4/F5 제품 사용을 폐기**했다. B-family 제품 채택은 D-042를 명시적으로 대체하는 새 결정이 필요하다.
- **test 163은 A0가 이미 사용**했다(D-080, 0.6072). “unused”는 “A1에 unused”로 써야 한다.
- A1은 encoder와 decoder 양쪽에 LoRA를 걸었다. “native encoder”는 “architecture는 native, weights는 LoRA로 adapted”로 정확히 써야 한다.

### M6. Prefix 근거는 n=5다 — **cheap experiment**

- pilot300의 bare 0.6522 vs prefix 0.6272는 **val 5건**이다.
- 두 출력의 길이가 264 vs 167 token으로 달라 char F1이 길이에 민감하다.
- pilot300 val161은 **prefix 조건만** 측정됐다.

**전원 권고**: full train 전이나 직후에 pilot300 adapter로 **bare val161**을 1회 평가한다. 비용 ~9~15분. 결과가 prefix 우위를 뒤집으면 배포 계약을 bare로 바꾼다.

추가로 GLM은 **zero-shot `summarize: ` val161**도 측정하라고 했다. 현재 zero-shot 0.2333은 한국어 instruction prefix 조건이라 base model을 과소평가했을 수 있다.

### M7. 평가 지표가 제품 판단에 부족하다 — **문서 + 코드**

필수 추가:

- `slot_preservation` 평균/분포/누락 문서 수.
- `summary_slot_count`와 `slots/doc`.
- 3~5문장 준수율. Opus의 휴리스틱 재집계로 A1 28/161이 범위 밖.
- ROUGE-L (계획 DoD에 있으나 미측정).
- 실제 CPU latency/RSS (계획 DoD에 있으나 미측정).
- 사람 50건의 **blinded, source-aware rubric**: fabricated entity, wrong number/unit, negation, attribution, critical omission, 3~5문장, utility.
- `grounded`와 `slot_verify.rejected`의 정의 차이를 문서화.

---

## 4. 모델별 이견

| 항목 | GLM | Opus | Sol | 해석 |
|---|---|---|---|---|
| F5-only bridge 1위 | **B1a** | **B2** | **B2** | A1을 이길 가능성은 B2가 가장 높지만, B2는 task-specific |
| General bridge 1위 | **B1d** | **B1d** | **B1d** | 3/3 일치 |
| B3 | 4위, “재설계 전 순위 불인정” | 5위, “detour” | 4위, “optional” | **첫 실험 금지** |
| B1d 판정 | teacher-forced NLL gap 중앙값 ≤3%, 80% ≤5% | recovery **R ≥ 0.5**, teacher-shuffled gap >0.3 nats | student-oracle NLL ≤0.10 nats, recovery ≥80% | 기준은 다르지만 모두 **NLL 기반 반증 가능** |
| LoRA schedule | warmup 3~5% + linear decay 권고 | constant 유지, 마지막 20% decay는 선택 | **no new schedule** for baseline | 첫 run은 constant가 비교 가능 |
| Full train 시간 | 2 epoch ≈3h + 평가 1h | 2 epoch ≈3h + 4×9분 | 2,586 step ≈3.01h + 평가 | **3.6~4.5h** 현실적 |
| 사람 검토 | full train 후, test 전 | stratified, val, test 전 | blinded A0/A1, test 전 | 동일 |

### GLM의 고유 지적

- B3는 **passage가 이미 encoder에 있으므로** soft token이 무시되어도 요약이 잘 나온다. 따라서 “decoder readability” 실험이 아니라 “learned task cue” 실험이 된다.
- B1d는 teacher hidden의 **스케일·기하**를 먼저 재야 한다. A2 adapter가 learned scale ×5가 필요했던 전례가 있다.
- B1d의 4~7h 견적은 **decoder CE가 없어** 상단 과대. distillation 자체는 더 싸다.
- zero-shot 0.2333은 **한국어 prefix** 조건이라 base model을 과소평가했을 수 있다.

### Opus의 고유 지적

- **A1 LoRA는 encoder 72개 + decoder 72개**다. 따라서 B1d teacher를 고를 때 **base encoder**와 **A1 LoRA encoder**를 혼동하면 안 된다. F5 decoder에 맞는 bridge를 원하면 A1 encoder를 teacher로 써야 하고, 범용 bridge를 원하면 base encoder+base decoder로 일관해야 한다.
- B1d의 falsification은 **recovery R**로 정의하라.

```text
R = (NLL_shuffled − NLL_student) / (NLL_shuffled − NLL_teacher)
```

- `H_T` oracle 자체의 NLL을 먼저 재라. teacher-vs-shuffled gap이 0.3 nats 미만이면 실험 resolving power가 없다.
- A1은 A0보다 slot을 적게 만든다. **A1의 grounding cleanliness가 “숫자를 덜 말해서”일 수 있다.** target micro 0.510, A1 0.456, A0 0.801.
- B2 decoder-only LoRA는 **737,280** params이지 A1의 1,474,560이 아니다. encoder까지 걸면 A1과 같아진다.

### Sol의 고유 지적

- **B1d train cache에 test passage를 넣으면 안 된다.** 1,617 전체 cache 1.9GB는 raw bytes로 맞지만, fitting은 train 1,293만 사용해야 한다. train-only는 약 **1.49GB**.
- B1d는 **summary label 없이** teacher hidden regression이 가능하지만, **약한 base teacher가 F5 요약 능력을 가르치는 것은 아니다.** zero-shot 0.2333, EOS 1.86%가 그 증거다.
- **oracle equivalence**를 먼저 확인하라: native `input_ids` inference와 cached `encoder_outputs` inference가 같은 logits/생성을 내야 한다. 이게 실패하면 harness 버그이지 distillation 실패가 아니다.
- 0/161 pass의 one-sided exact 95% lower bound는 약 98.16%. 99% lower bound에는 최소 299건이 필요하다. “161/161이므로 99% 안전”은 과장이다.
- B3 time이 문서에서 3~4h와 2~4h로 다르다. B3는 frozen encoder/decoder를 통과하므로 step cost가 A1과 비슷하고, parameter 수로 시간을 추정하면 안 된다.

---

## 5. EG2→T5 bridge — 수정된 설계

### 5.1 B1d corrected contract

**목표**: 런타임에 T5 encoder를 실행하지 않고, EG2 token features에서 T5 encoder의 최종 hidden sequence를 재구성한다.

**Offline**

```text
EG2 token features (정확한 layer/projection 명시)
→ student adapter (B1a linear 768→640, 또는 B1b contextual)
→ H_s ∈ R^{T×640}
Teacher H_T = T5Gemma2 encoder final last_hidden_state ∈ R^{T×640}
Loss = masked standardized MSE + cosine (+ optional decoder KL)
```

- teacher는 **base encoder** 또는 **A1 LoRA encoder** 중 하나로 고정한다. decoder와 일관된 pair를 써야 한다.
- train은 **1,293 passage만**. val은 inner held-out. **test passage는 cache/fitting에서 제외**한다.
- summary label은 필수가 아니다. 단, teacher prompt와 student prompt를 일치시켜야 한다.
- scale: per-dimension teacher RMS로 normalize하고, absolute norm도 보존한다. raw MSE만 쓰면 outlier dimension이 지배한다.

**Inference**

```python
model.generate(
    encoder_outputs=BaseModelOutput(last_hidden_state=H_s.to(base_dtype)),
    attention_mask=source_mask,
    max_new_tokens=448,
    # native decoder start/eos 설정
)
```

**금지**: B1d를 `inputs_embeds`로 구현하는 것. 그 경우 encoder가 실행되고, teacher output과 input space가 어긋난다.

### 5.2 후보 순위 (3-AI 종합)

| 후보 | F5-only | General bridge | 판단 |
|---|---:|---:|---|
| **B2** adapter + decoder LoRA | **1~2** | 4 | F5에서 A1을 이길 가장 현실적인 후보. 그러나 task-specific이고, real-vs-shuffled EG2 control이 필요 |
| **B1d** encoder-output distillation | 2~5 | **1** | 유일한 label-free 확장 경로. 약한 teacher 한계, interface 수정, oracle/NLL 검증 필수 |
| **B1b** contextual adapter | 2~3 | **2** | B1a가 underfit할 때. 7~10M params로 2~5M 추정은 과소 |
| **B1a** linear token adapter | 1~3 | 3 | 가장 싼 baseline. 문맥 변환 재현에는 한계 |
| **B3** pooled soft-prefix | 4~5 | 5 | passage가 남아 있어 EG2 사용을 입증하지 못함. augmentation 목적이 아니면 첫 실험 금지 |

**공통**: F5 제품 경로는 A1이 기준선이다. B-family는 A1을 대체하는 제품 후보가 아니라 **별도 연구 트랙**이다.

### 5.3 B1d 최소 반증 실험

1. **Oracle equivalence**: native encoder `input_ids` vs cached `encoder_outputs`가 같은 logits/생성을 내는지 확인.
2. **Teacher reference**: `NLL(H_T)`를 val161 또는 고정 64건에서 측정. teacher-vs-shuffled gap이 충분히 큰지 확인.
3. **Student fit**: train 1,293에서 B1a linear부터 학습. train subset을 먼저 과적합해 harness를 검증.
4. **Readout**: 같은 label/mask로 `NLL(H_s)`, `NLL(H_T)`, `NLL(H_s shuffled)`, `NLL(H_T shuffled)`를 측정.
5. **Generation**: 고정 20건에서 EOS/grounded/char F1을 확인.

사전등록 예시(모델별로 다름, 하나를 선택해 고정):

- **Opus**: `R ≥ 0.5` (alignment/scale 수정 후, KD 1회 시도 후). `R < 0.5`면 B1d 기각.
- **Sol**: `NLL_student − NLL_oracle ≤ 0.10 nats/token` **그리고** oracle-vs-shuffled advantage의 **≥80% 회복**. 256 train / 64 inner-held-out.
- **GLM**: median relative gap ≤3%, 문서의 80%가 ≤5%. 초과 시 capacity 상향 또는 중단.

이 기준들은 **검증된 제품 임계값이 아니라 feasibility 기준**이다. 하나를 실험 전에 고정해야 한다.

### 5.4 B3를 먼저 하지 않는 이유

B3의 입력은 `[soft_prefix ; Embed_T5(passage)]`다. passage가 그대로 있으므로:

- 좋은 요약이 나와도 **EG2 정보를 썼는지** 알 수 없다.
- “개선”은 learned task cue와 구분되지 않는다.
- decoder가 soft token을 무시해도 native text로 요약할 수 있다.

B3를 하려면 **real EG2 prefix / shuffled EG2 prefix / EG2-independent learned prefix** 3-arm이 필요하고, 이는 “encoder replacement” 실험이 아니다. augmentation이 목적일 때만 가치가 있다.

---

## 6. A1 full train 실행안

### 6.1 사전 조건

1. **M1 문서 수정**: B1d interface를 `encoder_outputs`로.
2. **M2 slot 보고**: `slot_preservation`/slots per doc/slot-free 분리.
3. **M3 코드 수정**: checkpoint/eval/selection/reshuffle/rank wiring/step-time stop.
4. **M6 cheap eval**: pilot300 bare val161, zero-shot `summarize: ` val161 (GLM 권고).
5. **M5 governance**: pilot300 승인 기록, D-042 관계, test 163 A0 사용 이력.

### 6.2 학습 설정

| 항목 | 값 |
|---|---|
| base | `t5gemma-2-270m-270m`, vision tower 제거 |
| LoRA | q/k/v/o, rank 8, alpha 16, dropout 0.05 |
| trainable | 1,474,560 (0.40%) |
| steps | **2,586** (2 epoch × 1,293) |
| batch | 1 |
| lr | 2e-4 |
| schedule | **constant 유지** (Opus/Sol); GLM의 warmup+decay는 별도 arm |
| clip | 1.0 |
| weight decay | AdamW default 0.01 (명시) |
| eval | 647 / 1,293 / 1,940 / 2,586 step에서 val161 |
| selection | safety gate → max char F1 → tie earlier; pilot300 fallback |
| human | full train 후, val 50건, test 전 |
| test | A1 val-best 1개, 1회 |

### 6.3 예상 비용

- 학습: 약 **3.0~3.6시간** (4.20초/step × 2,586)
- val161 평가 4회: 약 **40~60분**
- 총 **3.6~4.5시간** CPU, peak RSS 약 **2.45GB**
- test 163은 별도, 최종 후보만 1회

### 6.4 Full train 후 판정

- **A1이 pilot300을 유의하게 넘지 못하면** pilot300을 fallback으로 유지하고 full train 결과를 제품 후보로 승격하지 않는다.
- **A1이 넘으면** 사람 50건 → test 163 1회.
- **B-family는 A1 full train과 동시에 CPU에서 돌리지 않는다.** A1 종료 후 B1d probe를 별도 트랙으로 시작한다.

---

## 7. Q1–Q12 핵심 답

| 질문 | 3-AI 종합 |
|---|---|
| Q1 pilot300으로 full train? | **실험 승인은 충분, 제품 근거는 불충분**. 23% epoch, 단일 seed, val 재사용, 사람 0건 |
| Q2 2 vs 3 epoch? | **2 epoch 먼저**. 4 checkpoint, safety gate → max char F1, pilot300 fallback |
| Q3 prefix? | **F5 전용으로 유지**. bare val161을 추가 측정. dropout은 범용성 요구가 있을 때만 |
| Q4 bridge 첫 실험? | **B1d corrected probe**. B3는 첫 실험이 아님 |
| Q5 A2 raw control? | **제품 종결은 정당**, 원인 규명은 exploratory. decoder LoRA 추가 금지 |
| Q6 지표 충분? | **불충분**. slot preservation, sentence count, ROUGE-L, latency, human 50 필수 |
| Q7 slot-free 6건? | **155/155 non-vacuous + 6/161 vacuous 분리**. gate 분모는 161 유지 |
| Q8 LoRA target? | **q/k/v/o r8 유지**. FFN/r16은 underfit 증거가 있을 때 별도 arm |
| Q9 test? | **A1 1회만**. B-family는 val에서만; test를 bridge에 쓰지 않음 |
| Q10 A1 vs EG2 reuse? | **두 목표 분리**. A1은 F5 제품, B-family는 별도 bridge 연구 |
| Q11 과적합? | **2 epoch 적절**. epoch reshuffle, weight decay 명시, checkpoint val, repetition/EOS 감시 |
| Q12 오류? | **M1~M7** 참조. B1d interface, slot preservation, H4′, governance가 핵심 |

---

## 8. 결정 필요

| # | 결정 | 권고 | 상태 |
|---|---|---|---|
| 1 | A1 full train 2 epoch 승인 | 3/3 승인, 단 M1~M3 수정 후 | **대기** |
| 2 | full train 전 bare val161 + zero-shot `summarize: ` 측정 | 비용 ~15~30분, D2 확정 | **대기** |
| 3 | B1d bridge를 A1 후 첫 별도 트랙으로 | 3/3 B1d first, interface 수정 전 코드 금지 | **대기** |
| 4 | test 163 | A1 최종 후보 1회, B-family 금지 | **유지** |
| 5 | 사람 50건 | full train 후, test 전, stratified blinded | **대기** |

**지금 하지 말아야 할 것**

- B3를 먼저 구현하는 것.
- B1d를 `inputs_embeds`로 구현하는 것.
- A2에 decoder LoRA를 붙이는 것.
- B-family에 test 163을 쓰는 것.
- pilot300 결과를 제품 채택으로 해석하는 것.

---

## 9. 검토 비용·산출물

### 사용량

| 모델 | runtime | cost | input tokens | output tokens |
|---|---:|---:|---:|---:|
| GLM 5.3 Flash max | 10분 26초 | $0.1490 | 912,090 | 53,352 |
| Opus 5.5 medium | 4분 33초 | $1.3175 | 858,059 | 24,569 |
| Sol 6.1 xhigh | 9분 05초 | $0.6691 | 1,084,054 | 25,433 |
| **합계** | **약 24분** | **약 $2.14** | 2,854,203 | 103,354 |

- Hoplite 잔여 included credits: **53.93** (2026-11-06 조회)
- 원문·thread IDs·dispatch·watch 로그는 `docs/hoplite/c5_a1_2026-11-06/`에 보존

### 산출물

- 요청서: `reports/EXTERNAL_REVIEW_C5_A1_2026-11-06.md`
- 원문 3종: `review_GLM.md`, `review_OPUS.md`, `review_SOL.md`
- 스레드 매핑: `threads.json`
- 워처 로그: `watch.log`
- 이 종합: `reports/C5_A1_3AI_REVIEW_SYNTHESIS_2026-11-06.md`

### 검증 한계

- 세 모델 모두 **test 163을 열지 않았다.**
- GLM은 sandbox에 `data/models/` 가중치가 없어 텐서 수준 재검증을 하지 못했다. 코드·산출물·문서 대조로 대체했다.
- Slot preservation 0.4558/0.8012, A1 slots 837/5.199, A0 8.752는 이 세션에서 `predictions.jsonl`로 재확인했다.
- H4′ 6,186 id mismatch, D-027, D-042, D-082는 `docs/decisions.md`와 `docs/gates.md`로 대조했다.
- B1d/B3/B2는 **아직 구현·실행되지 않았다.** 이 문서의 순위는 문헌·구조·비용 분석에 기반한 연구 우선순위이지 실측 결과가 아니다.
