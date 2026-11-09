# C5 B0-A Phase 6 P/M Bounded Diagnostic — 외부 검토요청서

- 작성일: 2026-11-09
- 작성 기준 HEAD: `ef912b2` (`docs: add C5 B0-A P/M diagnostic preregistration`)
- 직전 검토 기준: `1d0e756` (B0-A review prompts/dispatch)
- **검토 기준: Hoplite 스레드 생성 시점의 origin/main HEAD**
- 대상: `docs/plan_c5_b0a_pm_prereg_v0_1.md` (Phase 6 P/M bounded diagnostic)
- 상태: **사전등록 검토용. 실행 미승인.**
- test 163: **sealed**
- P1 데이터: **미사용**
- T5Gemma2: **D-108 STOP 유지**
- B0-B / B1 / B2 / Stage C: **미승인**

---

## 0. Reviewer instructions

1. 이 문서를 **처음부터 끝까지 직접 읽어라**. 요약·발췌·다른 모델의 답을 근거로 삼지 말라.
2. 저장소 접근이 가능하면 다음 원문을 확인하라.
   - `docs/plan_c5_b0a_pm_prereg_v0_1.md`
   - `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md`
   - `reports/C5_B0A_REPAIR_2026-11-09.md`
   - `reports/C5_B0A_3AI_REVIEW_SYNTHESIS_2026-11-09.md`
   - `runner/c5_mt5_lora_b0.py`
   - `eval/tests/test_c5_b0_metric.py`
3. **학습·평가를 실행하지 말라.** test 163을 열지 말라. P1 데이터를 사용하지 말라.
4. **서브에이전트/추가 LLM을 호출하지 말고 직접 검토하라.**
5. 각 Q1~Q12에 대해 **판정(agree / disagree / conditional / defer) + 근거 + 권장 다음 단계 1~3개**를 적어라.
6. 최종 판정은 **STOP / NARROW / CONTINUE** 중 하나로 하고, 승인 범위·금지 범위·compute cap을 명시하라.
7. 결과를 본 뒤 threshold·seed·donor·step을 바꾸자는 제안은 하지 말라. 필요하면 **새 사전등록**으로 분리하라.
8. 보고서 파일을 작성하라:
   `docs/hoplite/c5_b0a_pm_prereg_2026-11-09/review_{MODEL}.md`
   최종 메시지에는 Q1~Q12 판정 표와 Must-fix 요약을 포함하라.

---

## 1. TL;DR

> **B0-A는 metric 정렬 결함 때문에 primary 결과를 폐기하지 않되, historical as-run으로 보존했다. Repair phases 1~4와 P0 native sanity(SENSITIVE_POSITIVE)를 완료했고, 이제 Phase 6 P/M bounded diagnostic을 20/20/3 seeds로 실행하려 한다. 검토 대상은 “이 사전등록이 P/M 통제를 올바르게 정의하는가”이며, B0-B 300/95 승인 요청이 아니다.**

핵심 상태:

| 항목 | 상태 |
|---|---|
| B0-A 3-AI review | **NARROW 3/3** |
| B0-A primary | **compromised / historical only** |
| CE alignment | fixed + 54 tests OK |
| F/L mode | base eval, adapter/LoRA only |
| P0 native sanity | **SENSITIVE_POSITIVE** train/val |
| Phase 6 | **prereg draft, not approved** |
| test 163 | sealed |

---

## 2. 직전 검토 이후 진행

### 2.1 B0-A review 결론

- GLM 5.3 Flash max: NARROW
- Sonnet 5.5 high: NARROW
- Sol 6.1 high: NARROW
- 공통: B0-A INCONCLUSIVE 산술은 맞지만 primary metric 결함, F/L dropout 비대칭, generation degeneration, mask 과잉 관대, low power.

### 2.2 확인된 metric 결함

같은 val 문서에서:

| 항목 | 값 |
|---|---:|
| built-in `out.loss` | **31.98719596862793** |
| aligned same-position CE | **31.98719596862793** |
| old shifted CE | **33.9515380859375** |

`token_losses`가 `logits[:, :-1]`와 `labels[:, 1:]`를 비교해 한 칸 더 shift하고 있었다. 수정 후 focused 7 tests / full 54 tests OK.

### 2.3 Repair phases 1~4

- same-position CE
- F/L base decoder eval + adapter/LoRA-only train
- generation telemetry
- mask audit

1-step debug에서 F/L first CE가 모두 **27.43998146057129**였고, LoRA 64 modules, base trainable params 0을 확인했다.

### 2.4 P0 native sanity

native mT5 encoder + frozen decoder, no training, 20/20, 5 donors.

| split | mean Δcopy | 95% CI | mean Δfull | positive docs |
|---|---:|---|---:|---:|
| train | **+3.7617** | [1.8917, 5.6050] | +3.5027 | 14/20 |
| val | **+5.2375** | [2.5013, 8.0753] | +5.2936 | 18/20 |

copy coverage .8351/.8246, guard false. 판정 **SENSITIVE_POSITIVE**는 descriptive이며 threshold 변경이 아니다.

---

## 3. Phase 6 제안

### 3.1 목적

20 train / 20 val에서:

1. **P (native positive control)**가 corrected metric에서 양성 selectivity를 만드는가?
2. **M (mean-memory negative control)**에서 L의 real memory가 target-independent mean memory보다 나은가?
3. repaired F/L에서 signal이 남아 있는가?

이것은 **B0-B 300/95가 아니다.** B0-B/B1/B2/C는 별도 결정이다.

### 3.2 Arms

| arm | memory | trainable | 역할 |
|---|---|---|---|
| F | EG2 native layer19 512d | adapter | adapter-only reference |
| L | EG2 native layer19 | adapter + decoder LoRA | EG2 bridge arm |
| P | native mT5 encoder on `summarize: passage` | decoder LoRA only | native positive control |
| M | training-only mean memory | 없음 (eval-only) | mean-memory negative control |

### 3.3 F

- 20 train, 100 updates, seed 20261108/09/10
- adapter 526,336 params
- base decoder eval
- no LoRA

### 3.4 L

- same as F + decoder self/cross q/k/v/o LoRA 64 modules
- r8 α16 dropout .05
- adapter+LoRA train, base eval
- same corrected metric

### 3.5 P

- native mT5 encoder memory
- **adapter 없음**
- decoder LoRA 64 modules
- 20 train, 100 updates, 3 seeds
- eval: native val memory vs length-matched native donor source

P의 목적은 “metric/decoder-LoRA가 잘 인코딩된 native memory에서 양성 신호를 만들 수 있는가”를 확인하는 것이다. EG2 bridge 성능 주장이 아니다.

### 3.6 M — eval-only

M은 별도 학습 arm이 아니다.

- L checkpoint에서 val20을 평가할 때만 memory를 mean으로 교체
- mean은 **train 20 문서의 adapter memory만** 사용
- target val/summary/donor는 mean에 사용 금지
- target length K에 맞춰 position-wise mean
- `len(h_i) >= K`인 train 문서만 사용
- eligible train 문서 < 10이면 해당 doc 제외

비교:

```text
Δmemfree_copy = mean_ce_copy − real_ce_copy
```

positive = real memory가 mean보다 낮은 CE.

### 3.7 Data

| 항목 | 값 |
|---|---|
| train | `train[0:20]` |
| val | `val[5:25]` |
| seeds | 20261108 / 20261109 / 20261110 |
| donors | 5, length-nearest, prefix crop K=min |
| target max length | 256 |
| source max length (P) | 256 |
| test 163 | 미사용 |
| P1 | 미사용 |

### 3.8 판정

```text
P_POSITIVE = mean Δshuffled_copy > 0
             AND bootstrap CI lower > 0

L_SIGNAL   = mean Δshuffled_copy >= .05
             AND CI lower > 0
             AND L > F
             AND 2/3 seeds > 0

M_CONTROL_PASS = mean Δmemfree_copy > 0
                 AND CI lower > 0
```

최종 label:

| 조건 | label |
|---|---|
| P 실패 | **ASSAY_INVALID** |
| P 성공 + M 실패 | **NO_CONTENT_USE_EVIDENCE** |
| P/M 성공 + L signal | **EXPLORATORY_L_SIGNAL** |
| P/M 성공 + L no signal | **INCONCLUSIVE_SMALL_N** |

어떤 label도 B0-B/B1/B2/C를 자동 승인하지 않는다.

### 3.9 Compute

- F/L/P = **9 trained units** (3 arms × 3 seeds), 100 updates
- M = evaluation-only
- wall time **≤2 CPU-hours**, 6 threads, no GPU
- cap 초과 시 중단·보고

---

## 4. 설계 근거와 알려진 위험

### 4.1 왜 M을 eval-only로 두는가

- trained M은 “mean memory로 학습한 arm”이 되어 treatment가 달라진다.
- Phase 6의 질문은 “L의 real memory가 target-independent mean보다 나은가”이므로, **같은 L checkpoint에서 memory만 교체**하는 것이 직접적이다.
- 별도 trained M arm은 B0-B 이후 새 사전등록 대상으로 남긴다.

### 4.2 왜 P가 필요한가

- P0는 no-training native memory의 sensitivity만 보였다.
- P는 **decoder LoRA가 학습된 상태**에서도 native memory를 사용할 수 있는지 확인한다.
- P 실패는 bridge STOP이 아니라 **assay/decoder-LoRA validity 실패**다.

### 4.3 알려진 위험

- 20문서/100 update는 screening이며 confirmatory가 아니다.
- P와 F/L은 memory source·adapter 유무가 달라 직접 CE 비교가 아니다.
- M의 position-wise mean은 “mean” 정의에 따라 결과가 달라질 수 있다.
- copy mask는 여전히 과잉 관대할 수 있다.
- generation은 telemetry이며 quality gate가 아니다.
- 3 seeds는 optimization variability를 완전히 추정하지 못한다.

---

## 5. 검토 질문

### Q1. P의 타당성

P는 native mT5 encoder + decoder LoRA, adapter bypass다. 이 정의가 **metric/decoder-LoRA positive control**로 타당한가? adapter를 포함해야 matched capacity가 되는가?

### Q2. M의 타당성

M을 별도 학습 arm이 아니라 **L checkpoint의 eval-only mean-memory 교체**로 정의한 것이 타당한가? trained M이 반드시 필요한가?

### Q3. Mean-memory 정의

train 20 문서의 adapter 출력, target K에 맞춘 position-wise mean, `len>=K` 문서만 사용, eligible <10 제외가 leakage 없이 valid한 negative control인가? 더 나은 정의가 있는가?

### Q4. F/L/P 비교

F/L/P의 memory source와 trainable parameter가 다르다. 이 3-arm 결과를 **어떤 비교로만** 해석해야 하는가? `L > F`와 `P` 결과를 동시에 어떻게 해석해야 하는가?

### Q5. 20/20/100/3 seeds

9 trained units + M eval, 20 train/20 val, 100 updates, 3 seeds가 Phase 6 diagnostic으로 충분한가? 어떤 결론은 금지해야 하는가?

### Q6. `.05` threshold

L에 B0-A와 같은 `.05`를 유지하는 것이 맞는가? P와 M에는 왜 `.05`를 적용하지 않는가? threshold 변경 없이 해석하는 방법을 제시하라.

### Q7. M_CONTROL_PASS

`mean Δmemfree_copy > 0 and CI lower > 0`가 content-use의 충분한 증거인가? position/길이/빈도 shortcut을 어떻게 추가 통제해야 하는가?

### Q8. P 실패 시

P_POSITIVE가 실패했을 때 **ASSAY_INVALID**로 두고 bridge STOP으로 일반화하지 않는 판단이 맞는가? P 실패 후 어떤 최소 진단이 남는가?

### Q9. M 실패 시

P 성공 + M 실패를 **NO_CONTENT_USE_EVIDENCE**로 label하는 것이 타당한가? L의 decoder가 mean memory를 사용해도 “content use”가 아니라고 말할 수 있는가?

### Q10. Must-fix

Phase 6 구현 전에 반드시 고칠 **code/design Must-fix 1~5개**를 ranked list로 제시하라. 특히 mean leakage, CE alignment, mode parity, donor/K, artifact completeness를 다루라.

### Q11. B0-B와의 경계

Phase 6 결과가 좋아도 B0-B 300/95를 자동 승인하지 않는 것이 맞는가? B0-B로 넘어갈 조건과 넘어가지 말아야 할 조건을 명시하라.

### Q12. 최종 판정

**STOP / NARROW / CONTINUE** 중 하나와 승인 범위를 제시하라.

- Phase 6 구현·1-seed debug 승인 여부
- 3-seed 실행 승인 여부
- 금지 범위
- 최대 compute
- 다음 decision gate
- test 163의 지위

---

## 6. 답변 형식

각 Q1~Q12:

```text
Qn.
- 판정: agree / disagree / conditional / defer
- 근거: 이 문서·artifact의 구체 수치
- 다음 단계: 1~3개
```

마지막에:

```text
최종 판정: STOP / NARROW / CONTINUE
Phase 6 구현·1-seed debug:
3-seed 실행:
금지 범위:
최대 compute:
Must-fix (ranked):
잘못된 전제:
```

---

## 7. Artifacts

| 경로 | 내용 |
|---|---|
| `docs/plan_c5_b0a_pm_prereg_v0_1.md` | Phase 6 사전등록 |
| `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md` | P0 결과 |
| `reports/provenance/C5_b0a/p0_native_sanity.json` | P0 원시 결과 |
| `reports/C5_B0A_REPAIR_2026-11-09.md` | phases 1~4 |
| `reports/C5_B0A_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | B0-A 3-AI 종합 |
| `reports/provenance/C5_b0a/metric_alignment_probe.json` | CE 정렬 증거 |
| `runner/c5_mt5_lora_b0.py` | corrected runner |
| `eval/tests/test_c5_b0_metric.py` | alignment/mode/P0 tests |

현재 54 tests OK.

---

## 8. 금지

- 학습·평가 실행 금지
- test 163 열람 금지
- P1 데이터 사용 금지
- repository 수정 금지 (지정 report 파일만)
- subagent/추가 LLM 호출 금지
- 결과를 본 뒤 threshold/seed/donor/step 변경 금지
- B0-B/B1/B2/Stage C 자동 진행 금지

---

## 9. 요청하는 최종 판단

> **이 Phase 6 P/M 사전등록이 metric/positive/negative control을 올바르게 분리하는가, 그리고 구현·1-seed debug를 승인할 수 있는가?**

특히 다음을 명시해 달라.

1. M eval-only 정의가 타당한가, trained M이 필요한가?
2. P의 adapter bypass가 positive control을 confound하는가?
3. Phase 6 결과로 B0-B를 자동 승인하면 안 되는 이유와, 넘어갈 수 있는 최소 조건은 무엇인가?
