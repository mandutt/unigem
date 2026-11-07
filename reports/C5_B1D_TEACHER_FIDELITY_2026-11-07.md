# C5 B1d adapter-only teacher-fidelity pilot — 결과 (2026-11-07)

## 1. 요약

A1 native T5Gemma2 teacher의 출력을 target으로 **adapter only**(decoder frozen)를
학습한 결과, **teacher-forced fidelity는 부분적으로 상승**했다.

- train token accuracy **39.02% → 52.71%** (+13.69%p)
- val token accuracy **40.29% → 43.58%** (+3.29%p)
- train CE **3.0069 → 2.2161**
- val CE **2.9384 → 2.7705**
- free-running val20: teacher F1 **0.2333**, gold F1 **0.2592**,
  EOS **40%**, grounded **15%**, gen_len **327.6**

즉 **adapter가 teacher behavior를 학습하는 것은 가능하지만, 99문서에서는 일반화가 약하고
frozen decoder의 free-running 격차가 크다.** 제품 후보로 승격하지 않는다.

## 2. 설정

| 항목 | 값 |
|---|---|
| teacher | A1 native T5Gemma2 pilot300 |
| teacher train100 | F1 **0.6697**, grounded **99/100**, EOS **100/100** |
| teacher val161 | F1 **0.6576**, grounded **161/161**, EOS **161/161** |
| student | EG2 → adapter(768→640) → **frozen** T5Gemma2 decoder |
| trainable | **adapter only**, 1,084,033 params |
| init | B1d-CE adapter |
| train | **99**문서 (teacher new-slot 1건 제외) |
| val | **100**문서 |
| loss | teacher-forced CE + **0.05 × (1 − hidden cosine)** |
| optimizer | AdamW, lr 3e-4, 2 epoch, batch 1 |
| test 163 | **로드하지 않음** |

teacher train100은 `verify_summary`에서 new slot이 1건 있어 1건을 제외했다.
val teacher 100건은 모두 grounded다.

## 3. Teacher-forced fidelity

### 3.1 정정 전 계측 오류

최초 실행에서 token accuracy를 `logits[:, :-1]` vs `labels[:, 1:]`로 계산해
**off-by-one** 오류가 있었다. T5Gemma2는 내부에서 labels를 shift하므로
`logits`와 `labels`를 **그대로** 비교해야 한다.

- 잘못된 값: train 1.74%, val 1.91%
- 정정 값: train **52.71%**, val **43.58%**
- 원본 오류값은 `b1d_teacher100_metrics_offbyone.json`에 보존
- 정정값은 `b1d_teacher100_metrics.json` 및 `b1d_teacher100_after_corrected.json`

### 3.2 정정 후 표

| 단계 | train CE | train token acc | val CE | val token acc | train hidden cos | val hidden cos |
|---|---:|---:|---:|---:|---:|---:|
| before (B1d-CE init) | 3.0069 | 39.02% | 2.9384 | 40.29% | 0.6967 | 0.6924 |
| after (teacher KD) | **2.2161** | **52.71%** | **2.7705** | **43.58%** | 0.6634 | 0.6582 |

training CE epoch 평균:

| epoch | CE mean | first20 | last20 |
|---|---:|---:|---:|
| 1 | 2.9118 | 3.0614 | 2.8357 |
| 2 | 2.5494 | 2.4461 | 2.5634 |

- train CE는 내려갔고 teacher token accuracy도 올라갔다.
- **val 개선폭은 train의 1/4 수준**으로, 99문서 overfit이 확인된다.
- **hidden cosine은 오히려 하락**했다(.6967→.6634). hidden auxiliary 0.05보다
  CE gradient가 커서 adapter가 behavior 쪽으로 이동한 결과다.
  “hidden을 유지하면서 behavior를 맞춘다”는 목표는 이 가중치로는 달성되지 않았다.

## 4. Free-running val20

| metric | 값 |
|---|---:|
| teacher char F1 | **0.2333** |
| gold char F1 | **0.2592** |
| EOS rate | **40%** |
| grounded rate | **15%** |
| gen_len mean | **327.6** |

teacher-forced token accuracy 43.58%에 비해 free-running F1이 낮다.
**teacher-forced에서는 맞히지만, 자기가 생성한 prefix에서는 무너지는 exposure bias**가
그대로 남아 있다.

## 5. 기존 결과와 비교

| system | 학습 대상 | free-running char F1 | grounded | EOS |
|---|---|---:|---:|---:|
| B1d full | adapter, teacher hidden | 0.0477 | 10% | 0% |
| B1d-CE | adapter, gold CE | 0.2061 | 5% | 10% |
| **teacher100** | **adapter, teacher output CE** | **0.2333** | **15%** | **40%** |
| B2 full | adapter + decoder LoRA, gold CE | **0.3349** | **18.01%** | **60.25%** |
| A1 native pilot300 | encoder + LoRA | **0.6576** | **100%** | **100%** |

- teacher output KD는 B1d hidden-only와 B1d-CE gold보다 **free-running이 개선**됐다.
- 그러나 B2 full(decoder LoRA)에는 미달한다.
- A1 native와는 여전히 큰 격차가 있다.

## 6. 해석

### 확인된 것

1. **adapter-only teacher output KD는 학습된다.**
   - teacher-forced token accuracy +13.7%p(train), +3.3%p(val)
   - teacher CE -0.79(train), -0.17(val)
2. **99문서는 부족하다.**
   - train/val CE gap 0.554, token accuracy gap 9.13%p
   - Exa의 “projector는 10~20% 데이터로 coarse alignment” 주장은
     **coarse alignment에는 맞지만, teacher behavior 일반화에는 99문서가 부족**하다.
3. **hidden auxiliary 0.05는 hidden을 보존하지 못했다.**
   - CE가 behavior를 맞추는 동안 hidden cosine이 하락
   - hidden과 behavior를 동시에 요구하려면 가중치/layer 선택 재검토 필요
4. **frozen decoder의 free-running 병목이 남아 있다.**
   - teacher-forced 43.6% vs free-running F1 0.233
   - stop token/EOS는 40%로 개선됐지만 60%는 EOS 없이 끝난다.

### 아직 모르는 것

- 300~1,293문서로 늘리면 val token accuracy가 계속 오르는가
- adapter capacity를 키우면 teacher fidelity가 오르는가
- **B2(decoder LoRA) + teacher output KD**가 free-running 격차를 줄이는가
- teacher output KD가 gold CE보다 **같은 데이터에서** 우수한가 (matched control 미실행)

## 7. 판정

**ADAPTER_ONLY_TEACHER_FIDELITY_PARTIAL**

- teacher-forced fidelity: **부분 상승**
- free-running: **B1d-CE보다 개선, B2 full 미달**
- 제품 후보: **없음**
- pilot300 fallback 유지
- test 163 sealed
- human/AI panel 재개 없음

## 8. 다음 후보

1. **B2 teacher KD 100문서** — adapter + decoder LoRA, teacher output target.
   free-running 격차를 decoder LoRA가 줄이는지 확인.
2. **B2 gold 100문서 matched control** — teacher target의 효과를 gold와 분리.
3. **B1d teacher 300문서** — 99문서 overfit이 데이터 부족인지 확인.
   Exa의 projector data-efficiency와 충돌하므로 exploratory.

우선순위는 **1 → 2**다. adapter-only 결과만으로 full 1,293을 재학습하는 것은
비용 대비 근거가 약하다.

## 9. 한계

- **teacher train100은 A1 eval batch의 길이 정렬 상위 100건**(짧은 문서)이다.
  val100은 split 순서의 첫 100건이라 train/val 분포가 완전히 같지 않다.
  이 pilot의 목적은 “adapter가 teacher behavior를 학습하는가”의 방향 확인이며,
  절대 성능 비교로 쓰지 않는다.
- teacher train100 F1 0.6697은 **train 문서** 기준이므로 val161 F1 0.6576과 직접 비교하지 않는다.
- free-running은 val 20건뿐이다.
- B2 full과 동일 데이터/동일 조건의 matched comparison이 아니다.

## 10. 산출물

- `runner/c5_b1d_teacher_fidelity.py`
- `docs/plan_c5_b1d_teacher_pilot_v0_1.md`
- `data/models/f5_t5gemma2_lora/b1d_teacher100/adapter_final.pt`
- `data/models/f5_t5gemma2_lora/b1d_teacher100/adapter_ep1.pt`, `adapter_ep2.pt`
- `reports/provenance/C5_b1d/teacher_train100.jsonl`
- `reports/provenance/C5_b1d/teacher_train100.metrics.json`
- `reports/provenance/C5_b1d/b1d_teacher100_metrics.json`
- `reports/provenance/C5_b1d/b1d_teacher100_metrics_offbyone.json`
- `reports/provenance/C5_b1d/b1d_teacher100_after_corrected.json`
- `reports/provenance/C5_b1d/b1d_teacher100_train.log`
- wall **989.4s** (원 실행), metric recompute **158.7s**
