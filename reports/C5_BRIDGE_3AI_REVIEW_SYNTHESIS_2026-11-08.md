# C5 bridge 3-AI external review — 종합

- 작성일: 2026-11-08 (KST)
- 검토 대상: `reports/EXTERNAL_REVIEW_C5_BRIDGE_2026-11-08.md` (624줄)
- 검토 기준 HEAD: **`f8c33a69c3dced040a401faf552a74437a696d02`**
  (실험 결과 기준 `ee084af` + review 문서/prompts 커밋)
- reviewers:
  - **GLM 5.3 Flash**, reasoning `max`
  - **Opus 5.5**, reasoning `medium`
  - **Sol 6.1**, reasoning `xhigh`
- test 163: **sealed, 미사용**
- P1 데이터·외부 API: 미사용
- `eval/slot_verify.py`: 미수정 (SHA256 일치 확인)

---

## 0. 최종 판정

### **3/3 STOP**

| reviewer | verdict | 핵심 |
|---|---|---|
| GLM 5.3 Flash | **STOP — 동의** | 격차가 구조적·통계적으로 압도적; 단일 반증 실험 없음 |
| Opus 5.5 | **STOP** | A1 0.6552/100/100 vs bridge 0.4074/12/69; product 결론을 뒤집을 실험 없음 |
| Sol 6.1 | **STOP** | D-107 DoD 실패; A1 fallback이 품질 우위; bridge 재개는 별도 승인 필요 |

**공통 결론**

- bridge는 **제품/대체 트랙으로 종료**한다.
- A1 native pilot300은 **fallback/reference candidate**로 유지하되,
  검증 전에는 **승인된 제품**이라고 부르지 않는다.
- bridge 재개는 **비용 동기 정량화 + 새 decision record + 명시적 NARROW 승인** 없이는 없다.

---

## 1. 3-AI 판정 행렬

| 질문 | GLM | Opus | Sol | 공통 해석 |
|---|---|---|---|---|
| Q1 bridge 전제 / STOP | agree | agree | agree | **STOP 3/3** |
| Q2 종료는 사후 합리화인가 | agree | agree | agree | 사전 등록 유효; DoD 설계는 보완 |
| Q3 SS grounding 붕괴 | conditional | conditional | conditional | 실제 행동 변화; slot-aware 회복은 비유의 |
| Q4 layer9 역설 | conditional | **disagree** | conditional | “역설”은 대부분 proxy/표본 노이즈 |
| Q5 300문서 결론 | agree | agree | conditional | STOP에는 충분, 일반화에는 한계 |
| Q6 slot repair 상한 | conditional | agree | conditional | 생성 grounding이 근본 병목 |
| Q7 slot aux vs copy vs constrained | conditional | conditional | conditional | **constrained decoding 1순위** |
| Q8 평가 지표 | conditional | conditional | conditional | 지표 정의·entity coverage 수정 필요 |
| Q9 A1 제품 경로 | conditional | agree | conditional | pilot300 동결; full은 별도 검증 |
| Q10 비교 공정성 | conditional | conditional | conditional | ID matching은 공정; subset/seed 편향 |
| Q11 중단 기준 | agree | agree | agree | 재개는 예외 승인 + 예산 상한 |
| Q12 Must-fix | agree | agree | agree | 지표·인과·provenance |

---

## 2. 공통 Must-fix

### M1. `grounded` 정의와 코드가 다르다 — **High**

- 요청서 §2.3은 `grounded = source slot 보존 + 신규 slot 없음`으로 서술했다.
- 실제 `runner/c5_b1d_generate.py`는 **`grounded = not rep.new`**만 사용한다.
  **보존(preservation)은 검사하지 않는다.**
- 따라서:
  - A1 native의 **grounded 100%**는 “신규 slot 0”이지 “모든 source slot 보존”이 아니다.
    A1 preservation은 matched val100에서 **0.4446**이다.
  - slot repair의 **grounded 100%**도 missing slot을 방치한 **no-new-only** 결과다.
    (repair missing 1,063; vacuous/slot-free 문서도 존재)
- **조치**:
  - `grounded_no_new`와 `grounded_strict(preservation 포함)`를 분리 표기.
  - preservation, missing, vacuous, new-slot micro를 함께 보고.
  - production `eval/slot_verify.py`는 **수정하지 않는다**.

### M2. 한국어 고유명사 coverage — **High**

- `slot_verify`는 숫자·날짜·URL·경로 등 typed slot 중심이며,
  **한국어 인명·기관명 같은 고유명사는 검사하지 않는다.**
- bridge가 인명/기관명을 발명해도 `grounded`가 통과할 수 있다.
- A1 native도 같은 한계가 있으므로, 제품화 전 **entity-level audit**이 필요하다.
- **조치**: A1 pilot300에 대해 P0 표본 human audit(또는 P0 NER 기반 check)를 수행한다.

### M3. SS의 인과 귀속과 통계 — **High**

- **no-SS continuation control이 없다.** SS arm은 `init=b2_layer12_300`에서
  1 epoch, lr 1e-4로 추가 학습했지만, 같은 조건의 `ss_prob=0` 1 epoch arm이 없다.
- 따라서 “SS가 F1을 올렸다”는 **인과 주장은 미확립**이다.
- **slot-aware 회복(10%→12%)은 비유의**:
  - Opus: McNemar **p=0.77**
  - GLM: p=0.77
  - Sol: 같은 2-point 회복을 “특히 약하다”고 평가
- **layer9 vs layer12**:
  - ΔF1 −0.0124, CI 0 포함 (GLM/Opus)
  - grounded 21→22, McNemar p=1.0
  - “layer9 free-running 악화”는 **노이즈**로 보는 것이 맞다.
- **조치**:
  - headline 비교에 **paired bootstrap CI + McNemar**를 붙인다.
  - D-106/D-107의 SS 문구를 “SS arm vs continuation”으로 한정한다.
  - “layer9 악화”를 “layer9≈layer12”로 정정한다.

### M4. Teacher hidden과 teacher output의 혼동 — **High**

- `runner/c5_b1d_cache.py`의 “teacher” hidden은
  **A1 LoRA가 없는 base T5Gemma2 encoder**다.
- “teacher output”은 **A1 native pilot300**의 출력이다.
- 요청서 §3.5는 둘을 “A1 native teacher”로 뭉뚱그려 서술했다.
- 따라서 D-095의 teacher hidden **0.5837/87.51%**는
  “A1 native encoder hidden”이 아니라 **base encoder hidden**과의 비교다.
- **조치**:
  - “hidden teacher = base T5Gemma2 encoder”로 명시.
  - “output teacher = A1 pilot300”으로 분리.
  - cache/checkpoint hash와 manifest를 기록.

### M5. Fidelity 표의 n 라벨 오류 — **Medium**

- 요청서 §5.2의 `train n`은 실제로 **val100 teacher-forced 평가**다.
- `b2_*_fidelity_teacher.json`은 n=100, target=teacher다.
- **조치**: 표 라벨을 `val n`으로 정정하고, train/val을 분리한다.

### M6. Provenance / config null — **Medium**

- `b2_layer12_300_ss_metrics.json`의 `ss_prob`가 **null**.
- `b2_layer12_300_metrics.json`의 `feature_dir`가 **null**.
- checkpoint에 optimizer/RNG state가 없어 exact resume이 어렵다.
- **조치**:
  - immutable run-config manifest에 seed, ss_prob, feature_dir, model hash, tokenizer hash 기록.
  - 기존 artifact는 **addendum**으로 보완하고 결과 수치는 재작성하지 않는다.

### M7. 비교 subset / val 재사용 — **Medium**

- teacher train100은 **길이 정렬 상위 100건**으로 val100과 분포가 다르다.
- A1 `.6506`은 **예측 파일의 id 정렬 앞 100행**, bridge matched `.6552`는
  **bridge val100과 동일 ID**다. 둘을 혼동하면 안 된다.
- val20 결정(D-096, D-102)은 표본이 작다.
- **조치**:
  - subset 정의를 artifact로 남긴다.
  - headline은 val100/val161만 사용하고, val20은 screening으로만 표기.
  - 가능하면 multi-seed 또는 CI를 병기한다.

### M8. EOS/slot-aware 구현 caveat — **Low~Medium**

- `--ss-slot-aware`의 EOS 보호는 **no-op**이다.
  (decoder input의 마지막 위치는 EOS target이 아니라 그 앞 token이므로)
- student argmax는 gold-context pass에서 얻은 값이며,
  진짜 free-running prefix rollout이 아니다.
- **조치**: 문구를 “one-pass noisy-prefix CE”로 정정하거나,
  향후 진짜 on-policy KD/rolling SS로 교체한다.

---

## 3. 요청서 자체의 수치·비교 정정

| 항목 | 기존 | 정정 |
|---|---|---|
| A1 native val100 | `.6506` (first 100) | **`.6552`** (bridge val100과 동일 ID) |
| bridge 최고 grounded | `21%` | **`22%`** (layer9, F1 .3340); layer12 21% |
| grounded 정의 | “보존 + no new” | **no-new only** (preservation 별도) |
| teacher hidden | “A1 native” | **base T5Gemma2 encoder** (A1 LoRA 없음) |
| §5.2 `train n` | train | **val100** |
| SS EOS 보호 | “EOS corruption 금지” | **no-op** (실질 보호 없음) |
| `ss_prob` | 문서 .2 | metrics JSON **null**; addendum 필요 |
| `feature_dir` | layer12 | metrics JSON **null**; addendum 필요 |

---

## 4. Reviewer별 고유 지적

### GLM 5.3 Flash

- **paired 통계**: A1 vs bridge ΔF1 **−0.2478**, 95% CI
  **[−0.2773, −0.2192]**; grounded 88/100 문서가 같은 방향, McNemar p≈1e-14.
- **E1**: teacher-hidden free-running attribution control (무훈련, ≤1h/25min).
  - teacher hidden을 넣고 free-running이 성공하면 → EG2/adapter 병목 확정.
  - 실패하면 → decoder free-running 병목; on-policy KD만 남음.
  - **어떤 결과도 bridge 재개를 승인하지 않는다.**
- **E2**: A1 1,940/2,586 checkpoint에 drop-new repair를 적용해
  pilot300과 paired 비교 (무훈련, ≤30분). repair 후 grounded 1.0,
  F1 > .6576, EOS 1.0, fallback ≤5/161이면 승격 **제안서**.
- EG2 재사용 **비용 이득이 요청서에 정량화되지 않았다**는 점을 재개 결측 변수로 지적.

### Opus 5.5

- **F1**: slot-aware 회복은 통계적 노이즈 (p=.77); layer9도 유의하지 않음.
- **F2**: grounding 붕괴는 **slot volume** 때문.
  slots/doc 6.0→9.7, per-slot new rate는 0.54→0.61로 상대적으로 작음.
- **F3**: no-SS continuation control 부재.
- **F4**: grounded 정의 불일치.
- **F5**: fidelity가 val100 vs teacher인데 train으로 표기됨.
- **F6**: provenance gap (`ss_prob`, `feature_dir`, seed, subset).
- **E0**: A1 pilot300 freeze + validation (reload determinism, CI, entity audit).
- **E1**: inference-only **source-constrained decoding**, 2 CPU-hours max;
  DoD grounded ≥95%, per-slot new ≤.02, F1 ≥.40, EOS ≥60.
  통과해도 product는 F1 ≥.55 + grounded ≥99% 전에는 아님.
- **Do not run** slot auxiliary/copy/B2 full under current evidence.

### Sol 6.1

- **STOP**; A1은 **fallback이지 approved product 아님**.
- **Experiment 1 (default)**: source-aware metric + A1 adequacy audit.
  - frozen matched val100, P0 source, blind 50 docs × 4 systems = 200 ratings.
  - supported/unsupported values, wrong relationships, critical omissions,
    coverage, repetition, adequacy.
  - **0.1~0.25 CPU-hours + 3~6 human-hours**.
- **Experiment 2 (optional)**: constrained frozen bridge, only with explicit
  NARROW + material EG2-reuse efficiency objective.
  - prospective research DoD: gold F1 ≥.60, no-new ≥99%, new-slot micro ≤1%,
    EOS ≥95%, rep4 ≤.06, coverage 100%, preservation ≥.40,
    ≥20% latency or RSS advantage.
  - 2~4 engineering hours + 1~3 CPU-hours; not approved.
- Additional high-severity:
  - teacher identity ambiguity (hidden base encoder vs output A1);
  - vacuity changes ranking;
  - LoRA dropout eval-mode hazard;
  - repair “ceiling”/rank/teacher-KD statements overgeneralized.

---

## 5. 결론

### 5.1 Bridge

**STOP.** 3/3 reviewer가 동의했다.

- bridge 최고 F1 **.4074 / grounded 12%**
- A1 native matched **.6552 / 100% / 100%**
- slot repair grounded-100 F1 ceiling **.3203**
- F1 gap **.25**, per-slot hallucination gap **~.55 vs ~0**
- 어떤 단일 실험도 제품 결론을 뒤집지 못한다.

### 5.2 A1 native

- **pilot300을 fallback/reference로 동결**한다.
  - val161 **.6576 / 161/161 / EOS 161/161**
  - matched val100 **.6552 / 100% / 100%**
  - preservation **.4446** (추상화로 source slot 일부 생략)
- **승인된 제품이라고 부르지 않는다.**
  - reload determinism 확인
  - val161 CI
  - Korean entity audit / human-50
  - test 163은 별도 승인 전 사용 금지
- **1,940/2,586**: 자동 승격하지 않는다.
  - 1,940: F1 .6823, grounded 158/161 (98.14%), new slot 4
  - 2,586: F1 .6690, grounded 159/161 (98.76%), new slot 3
  - repair 재평가는 **no-training diagnostic**으로만 가능; 제품 승격은 별도 승인.
  - GLM은 1,940 repair 재평가를 권고, Opus는 defer, Sol은 오류 진단 우선.

### 5.3 다음 실험 우선순위

| 순위 | 실험 | 훈련 | 비용 | DoD | 비고 |
|---|---|---|---:|---|---|
| 1 | **Metric/A1 audit** | 없음 | 0.1~0.25 CPU-h + 3~6 human-h | no-new/strict/preservation/vacuity/entity 재집계; A1 adequacy | **default** |
| 2 | **Source-constrained decoding** (frozen D-107) | 없음 | ≤2 CPU-h | grounded ≥95%, new micro ≤.02, F1 ≥.40, EOS ≥60 | 명시적 NARROW + 비용 동기 필요 |
| 3 | **A1 1,940/2,586 repair re-eval** | 없음 | ≤30분 | repair 후 grounded 1.0, F1 > .6576, EOS 1.0, fallback ≤5/161 | 진단용; 승격 별도 |
| 4 | **Teacher-hidden attribution** (GLM E1) | 없음 | ≤1h | free-running 100문서 완주 + paired 표 | post-mortem |
| 5 | slot auxiliary / copy / B2 full | 훈련 | 수시간~수일 | 별도 decision record | **현재 금지** |

**금지**

- slot auxiliary, copy/pointer, B2 full 1,293, layer9 full을
  현 상태에서 자동 실행하지 않는다.
- repair를 “제품 품질”로 부르지 않는다.
- test 163을 사용하지 않는다.
- gate를 사후 변경하지 않는다.

---

## 6. 비용

Hoplite thread usage:

| reviewer | totalCost | llm | vm | runtime |
|---|---:|---:|---:|---:|
| GLM 5.3 Flash | **$0.1926** | $0.1219 | $0.0707 | 338s |
| Opus 5.5 | **$1.4125** | $1.3364 | $0.0761 | 356s |
| Sol 6.1 | **$0.8330** | $0.7508 | $0.0822 | 422s |
| **합계** | **$2.4381** | $2.2091 | $0.2290 | — |

---

## 7. 원문·artifact

- `docs/hoplite/c5_bridge_2026-11-08/review_GLM.md` (20,675자)
- `docs/hoplite/c5_bridge_2026-11-08/review_OPUS.md` (28,816자)
- `docs/hoplite/c5_bridge_2026-11-08/review_SOL.md` (44,200자)
- `docs/hoplite/c5_bridge_2026-11-08/threads.json`
- `docs/hoplite/c5_bridge_2026-11-08/watch.log`
- 요청서: `reports/EXTERNAL_REVIEW_C5_BRIDGE_2026-11-08.md`
- 결정 원장: `docs/decisions.md` D-087~D-107
- 상태: `reports/C5_STATUS_2026-11-06.md` §37~§50

---

## 8. 한 줄 결론

**bridge는 STOP. A1 native pilot300은 fallback으로 동결하되 제품 승인 전
metric 정의·entity audit·determinism 검증을 먼저 수행한다.**
