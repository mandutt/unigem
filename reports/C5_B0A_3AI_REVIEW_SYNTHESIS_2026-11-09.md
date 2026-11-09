# C5 B0-A 3-AI 검토 종합 — NARROW

- 작성일: 2026-11-09
- 검토 라운드: `docs/hoplite/c5_b0a_2026-11-09/`
- 검토 기준 HEAD: `1d0e756` (prompts/dispatch), 결과 기준 `c66f17c`
- 검토 모델:
  - GLM 5.3 Flash **max**
  - Sonnet 5.5 **high**
  - Sol 6.1 **high**
- 검토요청서: `reports/EXTERNAL_REVIEW_C5_B0A_2026-11-09.md` (495줄)
- 원문:
  - `docs/hoplite/c5_b0a_2026-11-09/review_GLM.md` (17,741 chars)
  - `docs/hoplite/c5_b0a_2026-11-09/review_SONNET.md` (30,143 chars)
  - `docs/hoplite/c5_b0a_2026-11-09/review_SOL.md` (36,067 chars)
- test 163: **미사용**. P1 데이터: **미사용**. T5Gemma2: **D-108 STOP 유지**.

---

## 0. 한 줄 결론

> **3/3 NARROW.** B0-A의 INCONCLUSIVE 산술은 맞지만, **primary `Δshuffled_copy`의 CE 정렬 결함이 실제로 확인됐고**, F/L 학습 모드·dropout 비대칭과 copyable mask 과잉 관대, generation degeneration이 겹쳐 B0-A를 decoder adaptation의 증거로 사용할 수 없다. B0-B 즉시 실행·B1/B2/C는 금지하고, **정합성 수리 + 새 사전등록 + 소규모 P/M 진단**이 다음 단계다.

---

## 1. 판정 행렬

| 검토자 | 판정 | 핵심 승인 범위 |
|---|---|---|
| GLM 5.3 Flash max | **NARROW** | 무훈련 P0 metric sanity → collapse 진단 → P/M 20/20; B0-B는 그 후 |
| Sonnet 5.5 high | **NARROW** | zero-training correctness 수리 → P/M → B0-B |
| Sol 6.1 high | **NARROW (conditional)** | correctness-first repair, bounded diagnostic; B0-B 별도 |
| **종합** | **NARROW 3/3** | **B0-B/B1/B2/C 미승인** |

STOP 0/3, CONTINUE 0/3. 세 모델 모두 **bridge 전체 STOP은 근거 부족**이라고 봤다.

---

## 2. 확인된 핵심 결함

### 2.1 Primary metric CE 정렬 결함 — **확인됨**

`runner/c5_mt5_lora_b0.py`의 `token_losses()`는 다음을 비교한다.

```text
logits[:, :-1]  vs  labels[:, 1:]
```

그러나 mT5는 seq2seq 모델이며, `logits[t]`가 이미 `labels[t]`를 예측한다. 따라서 이 비교는 **한 칸 더 shift**되어 있다.

#### Forward-only 진단

- 대상: val index 5, `REPORT-news_r-04161-00002`
- label/logits length: 181
- built-in `out.loss`: **31.98719596862793**
- aligned same-position CE: **31.98719596862793**
- current shifted CE: **33.9515380859375**
- 차이: **+1.9643421173095703**

**결론**: aligned CE는 built-in loss와 정확히 일치하고, 현재 구현은 그렇지 않다. `Δshuffled_copy`는 **의도한 copy-token CE가 아니다.**

- 영향: B0-A primary `Δshuffled_copy` (그리고 copy CE/guard).
- 비영향: 학습 자체는 `out.loss`를 사용한다. `Δshuffled_full`도 `out.loss`를 사용한다. generation 관찰도 별개다.
- **역사적 수치는 수정하지 않는다.** B0-A는 “as-run, primary-metric-compromised”로 보존한다.
- 산출물: `reports/provenance/C5_b0a/metric_alignment_probe.json`

### 2.2 F/L 학습 모드·dropout 비대칭 — **확인됨**

- F: `load_base()`의 eval 상태 유지 → decoder dropout off
- L: `model.train()` 호출 → mT5 base dropout 0.1 + LoRA dropout 0.05
- 평가는 양쪽 `model.eval()`이라 metric 평가 자체는 같지만, **학습 경로가 다르다.**
- step-0 CE: F **27.44 / 21.68 / 36.98**, L **37.43 / 32.15 / 49.10**
- 동일 adapter 초기화·동일 첫 문서에서 **+10.0 / +10.5 / +12.1 nats** 차이

따라서 L−F는 **LoRA + dropout bundle**이지 순수 decoder capacity 효과가 아니다.

### 2.3 Generation degeneration — **양 arm 공통**

- 6 unit × 20문서 = **120/120 모두 gen_len 257**, EOS **0/120**
- F 60/60 nonempty, L 22/60 nonempty는 `.strip()` 기반 표면형 차이
- 실제로는 양 arm 모두 unigram/loop regime
- L의 2/3 seed는 공백 계열 loop token으로 이동
- “LoRA만 붕괴”가 아니라 **공통 underfit + LoRA arm의 2/3 seed 표면형 이동**으로 표기해야 한다.

### 2.4 Copyable mask 과잉 관대 — **3/3 지적**

- `copyable_mask()`는 NFKC 후 공백 제거 substring 매칭
- 한국어 1~2음절 piece가 source 어디에나 존재
- coverage **0.8246**, per-doc 0.76~0.88
- guard는 낮은 coverage만 막고, **과도한 coverage는 막지 않는다**
- 따라서 copy coverage 통과는 metric 건강의 증거가 아니다.

### 2.5 전력 부족

- 관측 document SD: L 0.113, L−F 0.160
- n=20에서 L−F CI lower>0에 필요한 효과 ≈ **0.068** (80% power ≈ 0.098)
- 관측 L−F **0.014**
- B0-A는 **자기 threshold 0.05를 검출할 전력이 없었다.**
- 95 val이면 paired MDE ≈ 0.031~0.046으로 B0-B 규모는 타당하다. 단 **threshold 변경이 아니라 새 사전등록**이다.

---

## 3. 검토자별 고유 강조점

### GLM 5.3 Flash max

- **D 우선**: 무훈련 native P0 sanity → collapse 진단(≤1 CPU-h) → P/M 20/20.
- `copyable mask` 과잉 관대, generation 기록 필드 미구현(F7), 계층적 통계(F6) 지적.
- B0-B 6~10h는 선행 진단 후; 최대 선행 compute **~3 CPU-h**.
- “frozen vs lora train CE 비교 불가”를 잘못된 전제로 명시.

### Sonnet 5.5 high

- **Primary metric off-by-one**을 가장 먼저 지적. 14/120 row가 aligned CE의 필요 부등식을 위반한다고 재계산.
- **F/L unmatched dropout**을 step-0 CE로 확증.
- `copyable mask` near-vacuous, coverage guard only low-side.
- **B0-A power ~30-50%**; zero-training fixes 후 P/M.
- **Aligned full CE를 co-primary sanity**로 두라고 제안.

### Sol 6.1 high

- **Correctness-first repair**; B0-A historical result 보존.
- `token_losses`의 extra shift를 코드 라인 단위로 지적.
- **donor duplicate-source exclusion**, validation reuse, P/M counterfactual provenance까지 요구.
- 다음 compute cap: **12 arm-seed units, ≤1,200 updates, ≤2 CPU wall-hours**.
- P/M 정의와 joint-bootstrap contrast 제안.

---

## 4. 공통 Must-fix (ranked)

| 순위 | Must-fix | 완료 증거 |
|---:|---|---|
| 1 | **CE 정렬 수정 + 회귀 테스트** | same-position CE mean == `out.loss` (atol 1e-5), first/EOS/ignored/copy mask cases |
| 2 | **F/L train-mode·dropout 대칭** | base dropout parity assert, trainable params, zero-LoRA eval equality |
| 3 | **Generation 진단 완성** | raw IDs, special/pad/EOS counts, cap hit, rep-4gram, char F1, grounded/no-new |
| 4 | **Copyable mask 재정의·감사** | train-only rule, coverage distribution, sample precision; 새 사전등록 |
| 5 | **P/M control 정의·배선** | native encoder P, mean-memory M, donor IDs/K, duplicate-source exclusion |
| 6 | **무훈련 P0 native sanity** | frozen decoder + native memory Δ copy/full; 학습 0 |
| 7 | **새 사전등록·전력·validation reuse** | 문서×seed variance, MDE, no post-hoc threshold/seed/donor/step |

Must-fix 1~2는 **B0-A 수리**가 아니라 **다음 실험의 전제**다. B0-A 수치를 소급 수정하지 않는다.

---

## 5. 다음 단계

### 즉시 금지

- B0-B 4-arm 300/95 즉시 실행
- B1 layer sweep / B2 decoder 비교 / Stage C
- 동일 B0-A config 재실행
- B0-A 결과를 bridge STOP 또는 제품 품질의 근거로 사용
- test 163 / P1 / T5Gemma2 재개

### 허용 후보 (별도 승인 필요)

1. **무훈련 P0 native metric sanity**
   - native mT5 encoder memory + frozen decoder
   - Δshuffled_copy/full + generation 0 step
   - 실패 시 metric/cross-attention 재설계 또는 STOP 상향

2. **Correctness repair**
   - CE alignment unit test
   - train-mode/dropout parity
   - generation diagnostics
   - mask audit

3. **Bounded diagnostic** (새 사전등록)
   - 20/20 F/L/P/M, original seeds, final checkpoint only
   - Sol cap: ≤12 arm-seed, ≤1,200 updates, ≤2 CPU-h
   - GLM cap: 선행 합산 ~3 CPU-h

4. **B0-B 사전등록서 작성**
   - 실행은 별도 승인
   - 300/95, P/M, power, validation reuse, stop rule

---

## 6. 최종 판정

```text
최종 판정: NARROW (3/3)

B0-A: INCONCLUSIVE, but primary metric compromised
B0-B: 미승인
B1/B2/Stage C: 미승인
T5Gemma2: D-108 STOP 유지
test 163: sealed
P1: 미사용

다음 decision gate:
  correctness repair + no-training P0 + bounded P/M diagnostic
  → 새 사전등록서 → 사용자 승인
```

---

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_2026-11-09/review_GLM.md` | GLM 원문 |
| `docs/hoplite/c5_b0a_2026-11-09/review_SONNET.md` | Sonnet 원문 |
| `docs/hoplite/c5_b0a_2026-11-09/review_SOL.md` | Sol 원문 |
| `reports/provenance/C5_b0a/metric_alignment_probe.json` | CE 정렬 확인 |
| `reports/C5_B0A_2026-11-09.md` | B0-A as-run 결과 |
| `reports/C5_B0A_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 이 종합 |

## 8. 재현

```bash
cd C:/code/unigem
python -c "import json; d=json.load(open('reports/provenance/C5_b0a/metric_alignment_probe.json')); print(d)"
```
