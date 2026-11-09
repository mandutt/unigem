# C5 B0-A Phase 6 P/M 사전등록 — 독립 외부 검토보고서

- 검토자: **GLM 5.3 Flash (reasoning effort: max)** — 이번 라운드의 독립 외부 검토자
- 검토일: 2026-11-09
- 검토 기준 HEAD: `26e334a79148e8be73e3378b6c82846891f1e180` (`docs: add C5 P/M prereg external review request`)
  - 동기화: `git fetch origin` 성공, `git pull --ff-only origin main` → "Already up to date".
  - 요청서 기재 작성 기준은 `ef912b2`이며, `26e334a`는 그 위에 이 검토요청서를 추가한 커밋이다.
- 대상: `docs/plan_c5_b0a_pm_prereg_v0_1.md` (Phase 6 P/M bounded diagnostic v0.1, **실행 미승인**)
- 독립성: 이전 c5_b0a 라운드의 개별 리뷰 원문(`review_GLM/SOL/SONNET.md`)은 읽지 않았다. 3-AI 종합 보고서는 요청서가 지정한 artifact로서 사실 상태 확인(결함 목록, 전력 수치)을 위해 읽었으나, 아래 모든 판정은 내가 직접 읽은 사전등록·러너 코드·테스트·provenance JSON에서 도출했다.
- 제약 준수: 학습·평가 미실행. test 163 미개봉. P1 미사용. 외부 API 미사용. 저장소 수정 없음(이 보고서 파일 1개만 작성). subagent·추가 LLM 미호출. T5Gemma2 D-108 STOP 유지. B0-B/B1/B2/Stage C 미승인.

---

## 0. 검증 기반

### 0.1 직접 확인한 문서·코드

| 대상 | 방법 |
|---|---|
| `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_2026-11-09.md` | 전문(353줄) 직접 판독 |
| `docs/plan_c5_b0a_pm_prereg_v0_1.md` | 전문(314줄) 직접 판독 |
| `reports/C5_B0A_P0_NATIVE_SANITY_2026-11-09.md` | 전문 |
| `reports/C5_B0A_REPAIR_2026-11-09.md` | 전문 |
| `reports/C5_B0A_3AI_REVIEW_SYNTHESIS_2026-11-09.md` | 전문 (사실 확인 목적) |
| `runner/c5_mt5_lora_b0.py` | 전부(802줄) 판독 |
| `eval/tests/test_c5_b0_metric.py` | 전부(128줄) 판독 |
| `runner/c5_mt5_layer_probe.py` | `Adapter` / `make_labels` / `load_layer_cache` 부분 |

### 0.2 provenance 수치 재확인 (JSON 직접 파싱)

- `reports/provenance/C5_b0a/p0_native_sanity.json`: train mean Δcopy **3.7617264366** CI [**1.8917**, **5.6050**], val **5.2374585485** CI [**2.5013**, **8.0753**], copy coverage **.83512 / .82462**, decision **SENSITIVE_POSITIVE** ×2 — 보고서 기재와 일치.
- `reports/provenance/C5_b0a/metric_alignment_probe.json`: builtin `out.loss` **31.98719596862793** == aligned same-position CE, old shifted CE **33.9515380859375**, 차이 **+1.9643421173095703**, `historical_result_preserved: true` — 일치.

### 0.3 코드 상태 (`runner/c5_mt5_lora_b0.py`)

- `token_losses()`는 same-position(`logits` vs `labels`, 추가 shift 없음)이며 문서화 주석이 있다.
- `set_training_mode()`은 arm ∈ {frozen, lora}만 지원하고, base decoder eval + adapter/LoRA만 train, `trainable_base_parameters == 0` assert, LoRA **64 modules** assert를 수행한다.
- `copyable_mask()`는 NFKC + 공백제거 substring 매칭(as-run rule 유지). `shifted_copy_mask()`는 이름만 유지하고 shift 없음.
- `donors_for()`(cache h 길이 기준)와 `native_donors_for()`(tokenized source 길이 기준) 모두 length-nearest, self-exclusion, 결정론적.
- `bootstrap_paired()`은 문서 단위 paired 1,000회, bootstrap seed 기본값 20261108(하드코딩).
- `argparse` 모드: smoke / metric-smoke / train / p0-sanity. **`--mode pm-diagnostic`은 미구현** — G0 승인 전 단계와 일치하며, 아래 Must-fix가 구현 단계의 전제가 된다.

### 0.4 환경 제한 (정직 기록)

- 이 검증 샌드박스에는 `torch`가 설치되어 있지 않다. 따라서 **54 tests를 이 환경에서 재실행하지 못했다.** "focused 7 / full 54 OK"는 repair 보고서·요청서의 기재로 채택하며, 구현 단계에서 재확인해야 한다.
- 데이터 파일(`f5_pairs_v3_clean.jsonl` 등) 개봉, test 163 접근, 모델 추론·학습 실행은 하지 않았다.

---

## 1. 요약 판정 행렬

| 질문 | 판정 |
|---|---|
| Q1 P 양성 통제 타당성 | **agree** |
| Q2 M eval-only 타당성 | **agree** |
| Q3 mean-memory 정의 | **conditional** |
| Q4 F/L/P 비교 해석 | **agree** |
| Q5 20/20/100/3 seeds | **agree** |
| Q6 `.05` threshold | **agree** |
| Q7 M_CONTROL_PASS | **conditional** |
| Q8 P 실패 → ASSAY_INVALID | **agree** |
| Q9 M 실패 → NO_CONTENT_USE_EVIDENCE | **conditional** |
| Q10 Must-fix | MF-1~MF-5 (§2.Q10) |
| Q11 B0-B 경계 | **agree** |
| Q12 최종 판정 | **NARROW** |

핵심 요지: 사전등록은 P(양성 통제)·M(음성 통제)·F/L(처치)을 올바르게 분리한다. eval-only M은 Phase 6의 질문("L의 real memory가 target-independent mean보다 나은가")에 대한 직접·paired 검증으로 타당하다. 승인은 **NARROW** — 구현·1-seed debug는 Must-fix MF-1~MF-3(코드 assert + leakage 테스트)이 구현·통과된 이후에만 허용하고, 3-seed 실행은 별도 gate로 남긴다.

---

## 2. Q1~Q12 판정

형식: 판정 / 근거 / 다음 단계 (요청서 §6).

### Q1. P의 타당성

- 판정: **agree** — P는 정의된 역할(metric + decoder-LoRA 양성 통제)에 타당하다. adapter를 포함한 "matched capacity" 요구는 **받아들이지 않는다**.
- 근거:
  - P0가 no-training 상태에서 native memory 경로의 감지력을 이미 확립했다(val mean Δcopy +5.2375, CI [2.5013, 8.0753]). 사전등록 §4.2대로 P의 질문은 "학습된 상태에서도 그 감지력이 남는가"다.
  - P에 EG2 adapter를 추가하면 (a) P가 검증 대상인 bridge 자체와 혼재되어 P 실패 시 원인 귀속(metric? adapter? 경로?)이 불가능해지고, (b) "잘 인코딩된 native memory"라는 양성 통제의 정의가 무너진다. capacity 비교는 동일 memory·동일 adapter 초기화·동일 seed 하의 **L−F** 대비가 담당한다(§2.1~2.2).
  - P는 EG2 bridge 성능 주장이 아니라는 제한을 §11이 명시한다.
  - 유의: P_PASS는 사전 확률이 높은 약한 통제다(P0가 사실상 같은 경로를 이미 통과). P의 정보 가치는 주로 **실패 검출**(decoder-LoRA 학습이 경로 감지력을 파괴하는가)에 있다.
- 다음 단계:
  1. P 학습 경로를 명시적 코드로 분리: 동일 train20 문서의 native mT5 memory(`summarize: ` prefix, max_length 256, **평가와 동일한 전처리**)로 LoRA-only 학습.
  2. `set_training_mode`에 arm `"p"` 확장: adapter 부재, LoRA 64 modules, base eval, LoRA+dropout train, trainable_base=0 assert(현재 runner는 {frozen, lora} 외 ValueError).
  3. artifact에 P 전용 필드 기록: native memory shape 512, prefix, source_max_length, 학습/평가 전처리 동일성.

### Q2. M의 타당성

- 판정: **agree** — eval-only mean-memory 교체가 맞다. trained M은 불필요하며 질문을 바꾼다.
- 근거:
  - Phase 6의 질문은 "L의 real memory가 target-independent mean보다 나은가"(§3.1)다. 직접 검증은 **동일 checkpoint에서 memory만 교체**하는 paired 대비다. §4.1의 논거(trained M은 treatment가 달라진다)가 정확하다.
  - eval-only M은 "학습된 decoder가 평가 시점에 memory content를 사용하는가"를 포착한다: content-use를 학습했다면 mean 교체 시 CE가 나빠져 Δmemfree > 0.
  - trained M이 답하는 별개 질문("mean memory로 학습하면 어떻게 되는가")은 §2.4가 B0-B 이후 새 사전등록 대상으로 남겨둔 것이 적절하고, compute cap(9 units)과도 일관된다.
- 다음 단계:
  1. M probe가 반드시 L checkpoint(학습 완료 adapter 포함)에서 실행되도록 배선하고, checkpoint 식별자를 artifact에 기록(§3의 "L checkpoint의 adapter A" 구현 일치 확인).
  2. M 결과를 L_SIGNAL과 독립 열로 보고하고, M 실패가 L 학습 자체의 실패로 보고되지 않도록 라벨을 분리 유지.

### Q3. Mean-memory 정의

- 판정: **conditional** — 구조적으로 leakage-free이고 음성 통제로 과학적으로 충분하다. 조건은 (i) 구현-level assert/provenance, (ii) 두 가지 해석 주의의 명시적 기록이다.
- 근거:
  - 정의(§3): train20의 A(h_i)만 사용, target val/summary/donor 금지, target 길이 K에 position-wise mean, `len(h_i) >= K` eligible, <10이면 m_eligible=false로 제외. 구조상 val leakage 경로가 없다.
  - 주의 1(in-sample adapter): A는 train20으로 학습된 adapter이므로 A(h_i)는 in-sample 표현이다. 그러나 mean은 target-specific content를 가질 수 없어 음성 통제 성질은 유지된다. train 주제 통계가 val 주제와 겹치면 mean이 약간 유익해져 Δmemfree가 작아지는 방향, 즉 **M_FAIL 쪽으로 보수적**이다. 허용 가능.
  - 주의 2(off-manifold): position-wise mean은 decoder가 학습에서 본 적 없는 분포(분산 축소, norm 변화)를 만든다. real 우위가 content가 아니라 분포 차이에서 나올 수 있다. 설계가 이미 Δshuffled(단일 wrong-doc memory, on-manifold)를 병행하므로 삼각검증이 가능하다 — **두 대비를 항상 함께 보고**할 것.
  - `len(h_i)`는 adapter 통과 전 길이지만 adapter는 position-wise Linear+LayerNorm이라 길이 불변이므로 문제없다.
  - 경미한 내부 불일치: plan §3은 P/F의 M probe 규칙을 정의하는 반면 DoD D4는 "M probes for L (and optionally F/P)"이다. F/P M-probe의 지위(secondary/optional)를 실행 전에 정리해야 한다.
- 다음 단계:
  1. (G0 전 prereg 수정 가능) 탐색적 secondary probe 2종을 "비게이팅 보고"로 추가 검토: norm-matched mean(real memory 평균 norm에 맞춘 스케일), position-permuted mean. 채택 시 반드시 실행 전 prereg에 명시하고, gate 판정은 기존 정의 그대로.
  2. mean 구성의 중복 방지: 정규화 passage 기준 중복/근접중복 train 문서를 mean 소스에서 제외(1개 문서가 mean을 지배하는 것 방지).
  3. artifact에 per-doc 기록: mean에 사용된 train id 목록, eligible 수, K, m_eligible, real memory 대비 mean memory norm.

### Q4. F/L/P 비교

- 판정: **agree** — 해석 가능한 비교가 제한적이라는 전제가 맞고, 사전등록 §11이 그 제한을 이미 명시한다.
- 근거:
  - 세 arm은 memory source(EG2 layer19 cache vs native encoder), adapter 유무, trainable이 다르다. 절대 CE 직접 비교 금지(§11)가 정확하다.
  - 허용 비교: (i) 각 arm **내부** paired 대비(Δshuffled, Δmemfree — 같은 checkpoint에서 memory만 교체), (ii) **L−F** paired 차이(동일 memory·동일 adapter 초기화·seed이므로 decoder-LoRA 기여 분리), (iii) P는 pass/fail validity로만 사용.
  - 동시 해석 규칙: P_POSITIVE + L>F + L_SIGNAL → EXPLORATORY_L_SIGNAL(assay 유효, EG2 memory+LoRA가 adapter-only를 넘는 memory-selective 이득, 탐색적). P 실패 → L>F 포함한 모든 arm 간 비교 무의미. P 성공 + L≈F → 이 규모에서는 adapter-only로 충분.
- 다음 단계:
  1. 보고서 템플릿에서 P를 "비교 arm" 열이 아닌 "validity" 행으로 고정.
  2. L−F 계산이 per-doc paired(공통 doc 교집합)로만 이루어지는지 확인 — `metric_smoke`의 `l_minus_f` 방식을 pm-diagnostic에 승계.

### Q5. 20/20/100/3 seeds

- 판정: **agree** — bounded screening으로 충분하고, 사전등록이 과잉 해석을 자체 차단한다.
- 근거:
  - 전력: 3-AI 종합의 관측 SD(L−F 0.160) 기준 n=20에서 CI-lower>0 MDE ≈ 0.068, 80% 전력 MDE ≈ 0.098 — threshold .05보다 커서 L_SIGNAL은 **본질적으로 underpowered**(§6.2도 인정). 그러나 Phase 6의 목적은 확증이 아니라 assay validity(P)와 음성 통제(M)의 분리다.
  - 9 trained units + M eval-only, 100 updates, 2 CPU-h cap은 screening 규모로 자기일관적이다.
- 다음 단계(금지해야 할 결론):
  1. 금지: bridge 효능/품질 주장, "content use가 존재한다/없다"의 일반적 진단, B0-B 자동 승인, 95-doc/300-doc 일반화, seed 1개 단독 결론(3 seed 전부 보고).
  2. 허용: §6.3의 4개 label과 그 탐색적 해석뿐.

### Q6. `.05` threshold

- 판정: **agree** — L에 .05 유지가 맞고, P/M에 .05를 적용하지 않는 것이 맞다.
- 근거:
  - L의 .05는 B0-A 사전등록의 소급 변경 금지 원칙(요청서 §0.7, P0 보고서 §4 "기존 B0-A threshold를 소급 변경하지 않음")과 직결된다. 지금은 결과 전이지만 threshold 변경은 어느 경우에도 새 사전등록의 사안이다.
  - P/M은 **통제**다: 최소 효과 크기 개념이 없고 요구는 방향+신뢰성(mean>0, CI lower>0)뿐이다. 통제에 .05를 요구하면 통제가 처치보다 통과하기 어려운 비논리가 생긴다.
- 다음 단계:
  1. 해석 규칙을 보고서에 명시: 0 < Δshuffled_copy < .05 & CI lower>0인 경우 label은 여전히 INCONCLUSIVE_SMALL_N이며, 별도의 "weak signal" 라벨을 사후 생성하지 않는다.
  2. 효과 크기·CI·per-seed 부호를 L_SIGNAL 판정에 나란히 보고해 threshold의 전력 한계를 노출.

### Q7. M_CONTROL_PASS

- 판정: **conditional** — content-use의 **필요** 증거로는 적절하나 **충분** 증거가 아니며, §11의 각주 유지 + shortcut 진단의 탐색적 보고가 조건이다.
- 근거:
  - `mean Δmemfree_copy > 0 and CI lower > 0`은 real memory가 target-independent mean보다 나음을 뜻한다. 이는 "memory 의존 성분의 존재" 표지이지 "content 사용 입증"이 아니다(§11이 이미 인정).
  - 잔여 shortcut: (a) off-manifold mean 아티팩트(norm/분산), (b) position-구조 이점 — 다만 Δshuffled도 position 구조를 보존하므로 이 통제는 Δshuffled 쪽이 더 강하다, (c) train-val 주제/빈도 중첩.
- 다음 단계:
  1. Δmemfree와 Δshuffled를 **항상 동시 보고**(M 단독 해석 금지).
  2. 탐색적 secondary: norm-matched mean 대비, Δmemfree와 copy-coverage의 상관, 길이 계층 요약. gate에는 불영향.
  3. artifact에 per-doc Δmemfree와 mean 구성 provenance(Q3) 포함 — 상관/계층 재분석 가능성 확보.

### Q8. P 실패 시

- 판정: **agree** — ASSAY_INVALID 스코핑이 맞고, bridge STOP으로 일반화하지 않는 판단도 맞다.
- 근거:
  - P 실패는 "잘 인코딩된 native memory + corrected metric + decoder-LoRA 학습"으로도 양성 selectivity가 나오지 않는다는 뜻이며, 이 경우 F/L의 null은 무해성 확인조차 불가능하다(assay 무효).
  - 그러나 P는 bridge와 assay만 공유하고 memory source는 공유하지 않으므로, P 실패가 EG2 메모리의 무가치를 뜻하지 않는다 — §6.2의 스코핑이 정확하다.
- 다음 단계(cap 내 최소 진단, 새 학습 없음):
  1. P artifact의 assert 감사(64 modules, mode policy, metric_alignment, native memory shape).
  2. P 학습 손실 곡선(train_ce_first/last/last10) 확인 — 발산/비학습 여부.
  3. 학습 직후 P checkpoint를 LoRA 비활성 상태(또는 학습 전 스냅샷)와 비교해 "학습이 경로 감지력을 파괴했는가" 국소 진단. 하이퍼파라미터 재시도는 새 사전등록 없이 금지.

### Q9. M 실패 시

- 판정: **conditional** — 라벨 자체는 타당하다. 단, 라벨 이름의 함의를 보고서에서 명시적으로 통제해야 한다.
- 근거:
  - P 성공(assay 감지력 확인) + M 실패(real ≈ mean)이면 "이 규모·이 구성에서 real memory가 target-specific 이득을 준다는 증거가 없다"는 것이고, L의 content-use 주장은 금지된다(§6.2). 타당하다.
  - 함의 주의: NO_CONTENT_USE_EVIDENCE는 "content use 없음의 증거"가 아니라 **"content use의 증거 없음"**으로만 읽어야 한다. n=20/100-step underpowered에서 M_FAIL은 전력 실패일 수 있다.
  - "decoder가 mean memory를 쓰는데 content use가 아니라 할 수 있는가" — 그렇다. mean memory에는 target-specific content가 없으므로 mean에서 유사 CE가 나오면 성능이 content에 의존하지 않는다는 뜻이고, 이는 "실제 memory를 쓸 때조차 content 기여가 측정되지 않는다"는 동일 결론이다.
- 다음 단계:
  1. 보고서에 라벨 해석 각주 고정: "no evidence FOR content use at 20 docs / 100 updates; not proof of absence; not a bridge verdict."
  2. M_FAIL 시에도 P/M/L per-doc 수치를 전부 공개해 향후 새 사전등록의 설계 근거로 남긴다.
  3. M_FAIL이 L의 다른 품질 지표(train CE 수렴)와 함께 보고되는지 artifact 스키마에서 확인.

### Q10. Must-fix

구현(pm-diagnostic)·1-seed debug **이전에** 필요한 코드/설계 Must-fix, 효과 우선순위 순:

1. **MF-1 P-arm 경로 + mode assert**: `set_training_mode`에 `"p"` 확장(adapter 부재, LoRA 64, base eval, LoRA/dropout train, trainable_base=0), P 전용 학습 루프(동일 train20의 native memory, prefix/max_length의 학습-평가 동일성 assert), native memory 512d shape assert. 근거: 현재 runner는 {frozen, lora} 외 ValueError이고 pm-diagnostic 모드가 미구현 — G0 승인을 "구현 착수 허가"로만 해석하기 위한 전제.
2. **MF-2 M leakage assert + provenance**: mean 소스 ⊆ train20 assert, target/donor id 제외 assert, "val id 포함 시 raise" 단위 테스트(prereg D3 명시 — blocking으로 시행), per-doc mean 구성 기록(id 목록, eligible 수, K, m_eligible), 중복 train passage 제외, F/P M-probe 지위 정리(D4 "optionally"와 plan §3 정의 간 표기 일치).
3. **MF-3 metric_alignment 하드 assert**: 모든 arm/seed artifact에 same-position CE == built-in `out.loss`(atol 1e-5) 기록 + 불일치 시 중단(§10 stop 조건과 연결). 근거: 이번 결함의 실제 원인이었던 지점(31.9872 vs 33.9515).
4. **MF-4 donor/K 규칙·provenance 일관성**: Δshuffled의 k=min(real, wrong) crop과 M의 target-K crop이 다른 규칙임을 코드·artifact에 명시, donor id/K/길이 per-doc 기록, arm별 donor 길이 정의 차이(F/L: cache 길이, P: tokenized source 길이) 기록. 근거: `evaluate_arm`/`p0_eval_split`은 k=min crop, `donors_for`와 `native_donors_for`의 길이 정의가 다름.
5. **MF-5 통계 pooling + mask warning + cap 정의**: §6.1의 pooled(mean per-doc across seeds → doc bootstrap) 구현 및 per-seed 표·seeds_positive 기록, bootstrap seed 기록(기본값 20261108 하드코딩), median coverage >.90 시 exploratory flag(§5.2), "≤2 CPU-hours, 6 threads"의 실행 가능한 정의(wall 시계 상한 + thread 수 기록) 명확화 — **G0 이전 prereg v0.2에서 문구 수정**.

### Q11. B0-B와의 경계

- 판정: **agree** — Phase 6의 어떤 label도 B0-B를 자동 승인하지 않는다(§6.3, §9 단계 7).
- 근거: Phase 6은 20/20/100-step screening이고 L_SIGNAL은 underpowered(§6.2 명시)이며, content-use 관련 label들은 §11의 제한을 받는다. 이는 요청서·사전등록 양쪽의 전제와 일치한다.
- 다음 단계:
  1. **B0-B로 넘어갈 수 있는 최소 조건**(그래도 별도 승인 필요): EXPLORATORY_L_SIGNAL(P_POSITIVE + M_CONTROL_PASS + L_SIGNAL). 이 경우 B0-B 사전등록에 전력 분석(95 val MDE ≈ .031~.046), validation reuse 정책, stop rule, 확장된 P/M 통제를 포함.
  2. **넘어가면 안 되는 조건**: ASSAY_INVALID(assay 재설계 선행), NO_CONTENT_USE_EVIDENCE(memory/assay 재설계 또는 STOP 상향 논의), INCONCLUSIVE_SMALL_N(대규모가 불확실성을 해소한다는 정당화 없이는 B0-B 사전등록 작성도 보류).
  3. 어느 경우에도 test 163 봉인, P1 미사용, T5Gemma2 D-108 STOP은 그대로.

### Q12. 최종 판정

- 판정: **NARROW**
- 근거: 사전등록은 통제 분리(P/M/L/F)와 해석 제한을 올바르게 정의했고, P0(SENSITIVE_POSITIVE ×2)와 repair(same-position CE, mode parity, 54 tests 기재)로 전제가 확인됐다. 구현 전 코드 전제(MF-1~MF-3)와 통계/cap 정의(MF-4~MF-5)가 남아 무조건 CONTINUE는 아니며, assay 무효 증거는 없어 STOP일 이유도 없다.

---

## 3. 최종 블록

```text
최종 판정: NARROW
Phase 6 구현·1-seed debug: 조건부 승인 — MF-1~MF-3이 코드+테스트로 구현·통과된 직후 착수 가능(MF-4~MF-5 동시 구현 요구)
3-seed 실행: 별도 gate — 1-seed debug artifact(assert 통과, leakage 테스트, metric_alignment, m_eligible 기록) 검토 후
금지 범위: B0-B/B1/B2/Stage C 실행, test 163 개봉, P1 사용, T5Gemma2 재개(D-108 STOP),
  결과 관찰 후 threshold/seed/donor/step 변경, arm 간 절대 CE 비교, Phase 6 label의 bridge/품질 일반화
최대 compute: 사전등록 §8 그대로 — 9 trained units × 100 updates + M eval-only,
  ≤2 CPU-hours, threads 6, GPU 없음, 자동 retry 없음, 초과 시 즉시 중단·보고
Must-fix (ranked): MF-1 P-arm 경로/assert → MF-2 M leakage assert+provenance
  → MF-3 metric_alignment 하드 assert → MF-4 donor/K 규칙·provenance → MF-5 pooling/mask warning/cap 문구
잘못된 전제:
  - "P 통과 = EG2 bridge 검증" — P는 assay 양성 통제일 뿐이다(§11).
  - "M_CONTROL_PASS = content use 입증" — memory 의존 성분의 존재 표지일 뿐이다(§11).
  - "eval-only M과 trained M은 같은 질문" — 다른 질문이며 Phase 6은 전자만 묻는다.
  - "≤2 CPU-hours"가 wall인지 CPU-time인지 모호 — G0 전에 명확화 필요.
  - "54 tests OK"는 이 검토 환경(torch 없음)에서 재실행되지 않았다 — 문서 기재로 채택, 구현 단계 재확인 필요.
```

---

## 4. 산출물

| 경로 | 내용 |
|---|---|
| `docs/hoplite/c5_b0a_pm_prereg_2026-11-09/review_GLM.md` | 이 보고서 (GLM 5.3 Flash max 독립 검토) |