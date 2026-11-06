# C5/F5 A2-null 3-AI 검토 종합 — 2026-11-06

## 0. 검토 구성

| 항목 | 내용 |
|---|---|
| 요청서 | `reports/EXTERNAL_REVIEW_C5_A2NULL_2026-11-06.md` (568줄) |
| 검토 HEAD | `fb2908d` (요청서 `c388699`의 자식, docs 변경만) |
| 프로젝트 | `proj_2e8de5ed594f47c7b851f1d7c5b52c61` (mandutt/unigem) |
| GLM | `z-ai/glm-5.3-flash`, reasoning **max** — `thr_f7ac0e5904e9410e8c50eb23689efdc6` |
| Opus | `claude-opus-5-5`, reasoning **medium** — `thr_59105b494cbf4298991a7e868c07e862` |
| Terra | `gpt-6.1-terra`, reasoning **high** — `thr_4d6bd6e3a4974be89ca48eea86f15e1e` |

원문:
- `docs/hoplite/c5_a2null_2026-11-06/2026-11-06_hoplite-review_c5_a2null_GLM.md`
- `docs/hoplite/c5_a2null_2026-11-06/2026-11-06_hoplite-review_c5_a2null_OPUS.md`
- `docs/hoplite/c5_a2null_2026-11-06/2026-11-06_hoplite-review_c5_a2null_TERRA.md`

## 1. 판정 요약

| 모델 | 총평 |
|---|---|
| GLM 5.3 Flash | **full val 161 first** — val 5는 방향은 일관되지만 확증 아님, 현재는 **INCONCLUSIVE(부정 방향)** |
| Opus 5.5 | **Pivot to A1** — 전환 전 약 1시간의 **memory-ablation ΔNLL + raw-vs-seq control**로 A2-null을 닫아라. decoder LoRA는 A1 코드 이후 1회만 |
| Terra 6.1 | **full val 161 first** — eval 안전장치·사전등록 후, 그다음 **A1 smoke/pilot** 우선. A2 decoder LoRA를 자동으로 이어가지 말 것 |

**공통 결론: 지금 decoder q/k/v/o LoRA를 바로 시작하지 않는다.** full val 161과 memory-conditioning/control 실험으로 판단 근거를 만든 뒤, A2-null 추가 투자 또는 A1 전환을 결정한다.

## 2. 3/3 공통 지적

### 2.1 val 5는 결정 근거가 아니다

- val 5는 **val shard의 결정론적 첫 5건**이며 무작위 표본이 아니다.
- grounded **0/5**의 95% Clopper-Pearson 상한은 약 **52%**로, G-C5 99%와 거리가 멀다. “이 구성은 G-C5를 통과할 수 없다”는 좁은 주장은 가능하지만, “adapter-only A2-null은 원리적으로 불충분하다”는 일반화는 아직 안 된다.
- 세 arm(EOS, EOS+LN) 모두 **1 epoch·adapter-only·frozen decoder**를 공유해 underfitting과 decoder bottleneck이 분리되지 않았다.
- **full val 161**이 필요하다. test 163은 계속 봉인한다.

### 2.2 가장 큰 결함은 repetition이 아니라 input independence

Opus/Terra:
- 5개 출력이 모두 원문과 무관한 주제로 환각했다(호주 산불 → 이탈리아 촛불집회, 법조 기사 → 대학 100주년, Bill Barr → 캘리포니아 촛불집회).
- 모든 출력의 slot preservation이 0.00~0.09.
- **matched target char F1 0.230/0.227 vs mismatched target char F1 0.206/0.190** — 입력을 바꿔도 출력이 거의 변하지 않는다.
- 따라서 “반복 붕괴”보다 **“memory가 decoder를 조건화하지 못함”**이 정확한 실패 서술이다.

### 2.3 최대 결함: eval 기본값이 봉인 test

`runner/c5_a2null_eval.py`의 기본값:
- `--split test`
- `--out predictions.jsonl`
- `--max-new 256` (보고된 실행은 128)

인자 없이 실행하면 **봉인 test 163을 평가**한다. D-081 위반 경로이므로:
- 기본 split을 `val`로 변경
- `test`는 명시적 `--allow-test` + 경고/결정 ID 없이는 거부
- `--max-new`는 target length p95에 맞춰 고정
- `--out`도 split별로 분리

### 2.4 max_new=128은 EOS/recall을 인위적으로 절단했다

실측 target length(clean 1,617, content+EOS):
- mean **208.9**
- p50 **204**
- p90 **268**
- p95 **289**
- p99 **333**
- max **439**

128 token 상한은 **p50보다도 작다**. 따라서:
- EOS 0/5는 “EOS를 못 배웠다”와 “상한에 걸렸다”가 섞여 있다.
- char F1 recall도 target 길이 때문에 손해를 본다.
- full val에서는 **512 token 상한**(또는 최소 1.5×p95=434)으로 고정하고, `ended_eos`/cap hit를 별도 보고해야 한다.

### 2.5 grounded 지표는 불충분하다

`grounded = not rep.new`는:
- slot이 없는 빈 요약도 통과한다(`summary_count=0`이면 `new_slot_rate=0`).
- slot-free 엔티티 환각(이재명, 롯데백화점, 캘리포니아주립대)을 잡지 못한다.
- `new_slot_rate_mean`은 **per-sample macro**이며, G-C5 audit의 **micro**(980/14,454)와 다르다.
- char F1은 공백 제거 문자 bag으로 순서·반복·사실 관계를 무시한다.

필수 보강:
- nonempty / 3~5문장 / truncation flag
- **micro new-slot rate**(Σnew/Σsummary_slots)와 macro 병기
- repetition: repeated-4-gram rate, distinct-2, longest repeated span
- ROUGE-L/chrF + mismatched-target floor
- 사람 50건은 최종 확증으로 유지

### 2.6 A0 비교는 같은 split에서만

A0 **clean test 163** char F1 0.6072 vs A2-null **val 5** 0.2297은 직접 비교가 아니다. 요청서에 split 주의가 있지만, 여전히 “A0보다 크게 낮다”는 서술은 오해를 부른다.

필수:
- A0를 **val 161 동일 ID**로 재평가
- A2-null도 val 161
- paired difference, 동일 slot 검증기, 동일 char/ROUGE 정의
- **mismatched target floor**를 함께 보고

### 2.7 memory conditioning을 아직 검증하지 않았다

Opus/Terra/GLM 공통:
- adapter가 실제 memory를 사용하는지 **teacher-forced ΔNLL**로 확인해야 한다.
- real memory vs shuffled memory(다른 문서 z) vs zero memory.
- `ΔNLL = NLL(shuffled/zero) − NLL(real)`; CI가 0을 제외해야 memory 사용을 주장할 수 있다.
- **raw-vs-seq control**: `z_raw = z − (zP)Pᵀ`로 기존 cache에서 유도 가능. 별도 재추출 불필요.
- **zero-shot T5Gemma2**: native encoder + frozen decoder, 동일 val 5/161. “bridge 문제”와 “decoder/task 정합 문제”를 분리하는 가장 싼 참조점이다.

### 2.8 EOS-only arm 재현성

`f06df58`에서 `Adapter` 클래스를 in-place로 LayerNorm+scale로 바꿨기 때문에, 현재 HEAD의 trainer로 EOS-only arm을 재현할 수 없다. 다음이 필요하다.

- `--adapter-norm none|ln` 플래그
- 또는 adapter class를 분리하고 trainer가 선택
- label contract unit test 추가(`<bos>` 없음, `<eos>` 정확히 1개, decoder input 첫 token bos)
- trainer default `--out`이 폐기된 `f5_a2null_full/`을 가리키지 않게 변경

### 2.9 요청서 자체의 factual error

- §3.2 `z_t = [W h_t ; P x_t] # 768`은 **concat으로 읽히지만 실제 코드는 sum**이다. `z_t = W h_t + P x_t`로 고쳐야 한다.
- §3.2 “adapter와 decoder만 학습”은 틀렸다. **adapter만 학습; T5 decoder는 완전 frozen**이다.
- §7 raw control “feature 재추출 + 별도 cache”는 틀렸다. `z_raw = z − (zP)Pᵀ`로 기존 cache에서 유도 가능하다.
- §6.1 “attention mask 정상”은 batch 1/all-ones에서만 확인된 것이며, padding path는 미검증이다.
- `max_new=128`의 censoring과 target p95=289를 명시해야 한다.
- EOS-only arm이 HEAD에서 재현 불가하다는 사실을 명시해야 한다.

## 3. 모델별 고유 의견

### GLM

- full val 161 + A0-on-val + zero-shot T5Gemma2를 먼저.
- decoder LoRA 전에 **adapter-only 2~3 epoch**가 underfitting/EOS imbalance를 더 싸게 검증한다고 제안.
- decoder LoRA는 q/k/v/o 전체보다 k/v-only 또는 o_proj+final norm이 귀속에 유리.
- gate: grounded ≥0.99, eos ≥0.90, repetition 지표, val 161; test 1회.

### Opus

- **A1 전환**이 최종 방향. 전환 전 약 1시간짜리 closure diagnostic:
  - memory ablation ΔNLL
  - raw vs seq projection control
- decoder LoRA는 A1 코드 위에서 **encoder만 바꾼 1회 비교**로 제한.
- T5Gemma2 merged attention은 `k_proj`/`v_proj`가 encoder states에 대해 별도 호출되므로 **memory-side-only k/v LoRA**가 가능하다. self-attention/LM prior를 건드리지 않는다.
- cross key는 `k_norm`을 거치므로 LN×5의 “key saturation” 설명은 약하다.
- `max_new=128`이 target mean 209보다 작아 EOS 0/5는 평가 artifact가 섞였다.
- overfit-8 test(8쌍을 외워 재현하는지)가 end-to-end pipeline 검증으로 필요하다.

### Terra

- full val 161 + eval 안전장치 + 사전등록 후 **A1 smoke/pilot** 우선.
- decoder q/k/v/o LoRA는 “plausible exploratory”일 뿐 최선의 다음 수가 아니다.
- `grounded`의 빈 요약 통과, macro/micro 혼동, cap censoring, mask/test 기본값을 강하게 지적.
- 0/161 오류도 99% 인구 신뢰를 보장하지 않는다(one-sided 95% lower ≈98.16%) — gate 해석에 주의.

## 4. 합의된 다음 순서

1. **문서·코드 안전장치 수정** (compute 없음)
   - eval 기본 split val, `--allow-test` guard
   - `max_new=512` (p95 289의 1.5배 이상)
   - micro/macro, nonempty, eos, repetition, truncation 지표
   - 요청서 수식·decoder 서술·raw control 유도 수정
   - EOS-only adapter 재현 플래그 + label unit test
2. **full val 161** — EOS adapter, LN adapter, A0, zero-shot T5Gemma2
3. **memory conditioning** — real vs shuffled vs zero ΔNLL, raw vs seq control
4. **결정**
   - memory ΔNLL ≈ 0 또는 grounded가 계속 0이면: **A2-null 중단, A1 전환**
   - memory가 유의하게 사용되고 A2-null에 최소 진전이 있으면: A1 코드 위에서 **bounded A2-null+LoRA 1회**
   - test 163은 최종 후보 1회만

## 5. 권고

**지금 decoder LoRA를 바로 시작하지 않는다.**

- 3/3 모두 “full val/closure diagnostic 없이 decoder LoRA”에 반대.
- Opus는 A1 전환, GLM/Terra는 full val 후 A1 우선. 실질적으로 **A1이 기본 후보**이고, A2-null은 cheap closure diagnostic 후에만 한 번 더 볼 가치가 있다.
- A2-null의 매몰비용(feature 2.4GB, 3회 학습)은 판단에서 제외한다.

## 6. 산출물

- 원문 3종: `docs/hoplite/c5_a2null_2026-11-06/*_GLM.md`, `*_OPUS.md`, `*_TERRA.md`
- threads: `docs/hoplite/c5_a2null_2026-11-06/threads.json`
- 요청서: `reports/EXTERNAL_REVIEW_C5_A2NULL_2026-11-06.md`
- 이 종합: `reports/C5_A2NULL_3AI_REVIEW_SYNTHESIS_2026-11-06.md`
