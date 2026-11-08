# C5 adapter capacity pretest — linear vs MLP768 vs MLP1536 (2026-11-08)

## 1. 목적

B2 gold300에서 adapter capacity 확장이 의미 있는지, **B2 3-arm 2시간 실험 전에**
hidden-matching objective로 싸게 판정한다.

- train 300 / val 100
- 2 epoch, lr 1e-3, batch 1
- objective: `1 - cosine(adapter(EG2), teacher_hidden)`
- **모두 scratch, 동일 seed**
- decoder 없음, test 163 미사용

## 2. 결과

| arm | params | before cosine | after cosine | Δ vs linear | norm ratio | normalized MSE |
|---|---:|---:|---:|---:|---:|---:|
| **linear** | 493,441 | −0.0094 | **0.6665** | — | 1.1065 | 0.001042 |
| **MLP768 (current)** | 1,084,033 | −0.0020 | **0.6998** | **+3.33%p** | 1.0815 | 0.000938 |
| **MLP1536 (wide)** | 2,166,145 | −0.0071 | **0.7102** | **+4.37%p** | 1.0771 | 0.000906 |

- linear → MLP768: **+3.33%p**
- MLP768 → MLP1536: **+1.05%p**
- wide는 linear보다 +4.37%p지만, **MLP768 대비 이득은 작다.**

### 참고: 기존 B1d full (1,293문서)

- val hidden cosine **0.7271**
- 이번 300문서 scratch MLP1536 **0.7102**
- 300문서에서는 데이터/초기화 차이로 기존보다 낮다.

## 3. 해석

### capacity는 의미가 있다

- linear보다 MLP가 **+3.33%p**로 명확히 좋다.
- 즉 EG2→teacher hidden 변환에 **비선형성**이 일부 필요하다.

### 그러나 wide 이득은 작다

- MLP768 → MLP1536 **+1.05%p**
- 파라미터는 2배(1.08M → 2.17M)인데 이득은 작다.
- **output 640d 정보 병목**과 **EG2 feature 정보량**이 제한적임을 시사한다.

### 2시간 B2 3-arm은 정당화되지 않는다

- hidden capacity 이득이 +1%p 수준이면, B2 free-running F1/grounded 개선도 작을 가능성이 높다.
- **linear vs MLP768** 차이는 크지만, 이미 current가 MLP768이다.
- wide 1536은 **추가 1시간**을 쓸 근거가 약하다.

## 4. 판정

**CAPACITY_PARTIAL_DIMINISHING**

- linear < MLP768 < MLP1536
- MLP768은 capacity가 필요하다는 증거
- MLP1536은 **diminishing return**
- 다음은 adapter width가 아니라 **입력 feature / decoder cross-attention / objective** 쪽이 맞다.

## 5. 다음

1. **EG2 layer12 512 vs final 768** — 정보 병목 직접 공략
2. **decoder LoRA rank r16/32 또는 attention-only** — cross-attention 적응
3. **B2 1536 one-arm** — 정말 필요할 때만 (약 43분)
4. **on-policy KD** — teacher-forced/exposure bias
5. **A1 native 제품 경로** — EG2 재사용이 필수 아닐 때

## 6. 산출물

- `runner/c5_adapter_capacity_pretest.py`
- `reports/provenance/C5_b1d/adapter_capacity_pretest.json`
- `reports/provenance/C5_b1d/adapter_capacity_pretest.log`
- wall: linear 6.0s, MLP768 9.8s, MLP1536 18.2s
