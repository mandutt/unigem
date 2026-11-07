# C5 bridge diagnostics — H_s ablation + teacher bias (2026-11-07)

## 1. 목적

adapter-only teacher fidelity 결과를 다른 관점에서 반증한다.

1. **H_s zero/shuffle/other-doc**: adapter hidden이 실제로 decoder에서 사용되는가?
2. **teacher hidden control**: adapter가 teacher hidden에 얼마나 못 미치는가?
3. **teacher copy/leading bias**: teacher target 자체가 extractive/leading 편향인가?

모델 재학습 없음. val100 teacher-forced. test 163 미사용.

## 2. H_s ablation

adapter: `b1d_teacher100/adapter_final.pt`, teacher: A1 native pilot300.
조건:

- `real`: 해당 문서 adapter hidden
- `zero`: 같은 shape의 0
- `token_shuffle`: adapter hidden의 time position을 shuffle
- `other_doc`: 다음 val 문서의 adapter hidden을 현재 길이에 맞게 pad/truncate
- `teacher`: 실제 teacher hidden
- `teacher_shuffle`: teacher hidden의 time position을 shuffle

### 2.1 결과

| condition | CE mean | ΔCE vs real | token acc | 해석 |
|---|---:|---:|---:|---|
| **real** | **2.7705** | — | **43.58%** | 기준 |
| zero | 6.1708 | **+3.4003** | 17.70% | adapter content 사용됨 |
| token_shuffle | 2.7706 | +0.0001 | 43.52% | order 무영향 |
| other_doc | 3.4829 | **+0.7124** | 34.70% | document-specific content 사용됨 |
| **teacher** | **0.5837** | **−2.1868** | **87.51%** | upper reference |
| teacher_shuffle | 0.5835 | −2.1870 | 87.59% | teacher도 order 무영향 |

### 2.2 해석

#### (1) “decoder가 adapter를 무시한다”는 기각

- zero H_s: CE **+3.40**, token acc **43.6% → 17.7%**
- other document H_s: CE **+0.71**, token acc **34.7%**

adapter content가 실제로 CE를 크게 낮추고, 문서별 content도 사용된다.
따라서 **adapter를 완전히 무시하는 것은 아니다.**

#### (2) token_shuffle은 order 테스트가 아니다

teacher hidden을 shuffle해도 CE가 **0.5837 → 0.5835**로 동일하다.
표준 cross-attention은 encoder state를 permute하면 attention weight와 value가 같은 방식으로
permute되어 출력이 보존되는 permutation-equivariant 구조다. 이 모델에서도 teacher hidden이
같은 결과를 보였으므로, token_shuffle 결과를 “adapter가 순서를 무시한다”로 해석하면 안 된다.
**teacher조차 같은 결과**가 나오므로 이 조건은 bridge 결함 진단이 아니다.

#### (3) adapter는 teacher hidden에 크게 못 미친다

- CE 차이 **−2.1868** (teacher가 더 낮음)
- token accuracy 차이 **87.5% vs 43.6%**

adapter content는 사용되지만 **teacher hidden의 content/quality에는 크게 미달**한다.
이것이 adapter-only의 진짜 병목이다.

## 3. Teacher copy/leading bias

teacher train100/val100과 gold를 같은 문서 ID에서 비교.
copy는 whitespace 제거 후 **character 4-gram** 기준.

| 집합 | copy4 mean | leading40 sentence mean | char length |
|---|---:|---:|---:|
| teacher train100 | **84.40%** | **56.94%** | **230.3** |
| gold train100 | **66.17%** | **52.35%** | **267.7** |
| teacher val100 | **84.66%** | **57.52%** | **221.0** |
| gold val100 | **63.60%** | **51.67%** | **249.5** |

### 해석

- teacher summary는 gold보다 **4-gram copy rate가 +18~21%p 높다**.
- teacher summary는 **더 짧고**, source 앞부분에 더 편중된다.
- therefore teacher output KD는 student에게 **extractive / leading-biased target**을 학습시킬 수 있다.
- A1 teacher의 grounded 100%는 **사실성**을 뜻하지만, **abstractiveness**를 뜻하지 않는다.

이것은 Exa의 PLATE/DisCal 관찰과 같은 방향이다.

## 4. 종합 판정

### 기각된 대안

- **“decoder가 adapter를 무시한다”**: 기각. zero/other-doc에서 CE가 크게 악화.
- **“token order가 adapter 결함이다”**: 기각. teacher hidden도 order shuffle에 무영향.

### 지지된 대안

- **“adapter는 사용되지만 teacher hidden에 크게 못 미친다”**: 지지.
  - CE 2.77 vs teacher 0.58
  - token acc 43.6% vs 87.5%
- **“teacher target이 extractive/leading 편향”**: 지지.
  - copy4 84.4% vs gold 66.2%
  - teacher가 더 짧음
- **“token-level KD/exposure bias”**: 여전히 유효.
  - teacher-forced 43.6% vs free-running F1 .233
- **“adapter-only 구조적 한계”**: 지지.
  - teacher hidden control과의 큰 격차
  - projector-only frozen backbone 문헌과 일치

## 5. 다음 실험

### 1순위 — B2 teacher KD 100

- adapter + decoder LoRA
- teacher output target
- val teacher-forced + free-running
- **decoder LoRA가 teacher hidden 격차를 줄이는가**

### 2순위 — B2 gold 100 matched control

- 같은 100문서, 같은 조건
- teacher target vs gold target 분리
- teacher의 extractive bias가 student에 전이되는지

### 3순위 — adapter capacity

- adapter width/rank 확대
- teacher hidden과의 CE 격차가 capacity인지 확인

### 4순위 — on-policy KD

- student-generated prefix로 teacher scoring
- token-level KD의 exposure bias 직접 공략

## 6. 판정

**BRIDGE_CONTENT_USED_BUT_INSUFFICIENT**

- adapter content는 사용됨
- adapter는 teacher hidden에 크게 미달
- teacher target은 extractive/leading 편향
- token-level KD의 free-running gap은 별도 문제
- 제품 후보 없음; pilot300 fallback; test 163 sealed

## 7. 산출물

- `runner/c5_b1d_bridge_ablation.py`
- `runner/c5_teacher_bias_audit.py`
- `reports/provenance/C5_b1d/bridge_ablation_val100.json`
- `reports/provenance/C5_b1d/bridge_ablation_val100.log`
- `reports/provenance/C5_b1d/teacher_bias_audit.json`
- wall: ablation **526.1s**, bias audit 수 초
