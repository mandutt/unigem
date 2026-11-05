# Wave 2B V2 — B0′ matched-budget controls 결과

- 완료: 2026-11-05 18:22 KST
- 사전등록: D-072, `reports/W2B_b0_matched_controls_plan.md`
- 범위: **dev 500 전용**. sealed test 2,400은 사용하지 않았다.
- 목적: B0′ 6h vs B3 10h의 차이가 **추가 step / audio exposure**로 설명되는지 확인
- 결과: **compute controls는 B3의 약 +10%p를 설명하지 못함**

## 1. 최종 결과

| Arm | epochs | total steps | audio exposure | best dev CER | final dev CER |
|---|---:|---:|---:|---:|---:|
| B0′-12 (기존) | 12 | 3,576 | 72.0h | 0.3701 | 0.3701 |
| **B0′-20** | 20 | **5,960** | **120.0h** | **0.3654** (ep19) | **0.3657** (ep20) |
| **B0′-38** | 38 | **11,324** | 228.0h | **0.3683** (ep33–35) | **0.3687** (ep38) |
| **B3-12 (reference)** | 12 | **11,196** | **120.3h** | **0.2682** | **0.2682** |

- B0′-20은 **exposure-matched** (B3-12: 120.3h).
- B0′-38은 **step-matched** (B3-12: 11,196 steps).

## 2. Paired dev bootstrap

20,000 resamples, seed 42, utterance-level.

| Comparison | Δ CER | 95% CI | 해석 |
|---|---:|---:|---|
| B0′-12 − B0′-20 | **+0.464%p** | [−0.107, +1.028] | B0′-20이 약간 좋지만 **유의하지 않음** |
| B0′-12 − B0′-38 | **+0.181%p** | [−0.486, +0.846] | **유의하지 않음** |
| B0′-20 − B3 | **+9.723%p** | [+8.656, +10.819] | B3가 훨씬 좋음 |
| B0′-38 − B3 | **+10.006%p** | [+8.908, +11.161] | B3가 훨씬 좋음 |
| B0′-20 − B0′-38 | −0.284%p | [−0.923, +0.347] | 차이 없음 |

Δ = CER(왼쪽) − CER(오른쪽). 양수 = 오른쪽이 더 좋음.

## 3. 해석

### 3.1 Exposure는 설명하지 못한다

B0′-20은 B3-12와 audio exposure가 거의 같다(120.0h vs 120.3h). 그런데도:

- B0′-20 best **0.3654**
- B3 **0.2682**
- 차이 **9.72%p**, CI가 0과 멀리 떨어짐

20 epoch로 exposure를 맞춰도 B3에 접근하지 못했다.

### 3.2 Step도 설명하지 못한다

B0′-38은 B3-12와 optimizer step이 거의 같다(11,324 vs 11,196). 그런데도:

- B0′-38 best **0.3683**
- B3 **0.2682**
- 차이 **10.01%p**

step을 맞춰도 B3에 접근하지 못했다. 오히려 B0′-38의 best는 B0′-20보다 나쁘다(0.3683 vs 0.3654; 차이는 유의하지 않음). 6h 데이터를 38 epoch 반복하면 **추가 이득 없이 포화/과적합**되는 것으로 보인다.

### 3.3 따라서 남는 것은 데이터 구성

B0′ control 두 개는 모두 **Wave 1 6h만** 사용한다. B3는 **Wave 1 6h + Kspon short 4h**다.

- step을 맞춰도(B0′-38) B3 격차가 유지됨
- exposure를 맞춰도(B0′-20) B3 격차가 유지됨
- B3의 우위는 **추가 Kspon short 데이터의 구성 효과** 쪽으로 남는다

단, 이 실험으로 **Kspon domain**과 **short-length 분포**를 분리할 수는 없다. B3에는 둘이 함께 들어 있다.

### 3.4 B0′는 포화됐다

- B0′-12: 0.3701
- B0′-20: 0.3657 (best 0.3654)
- B0′-38: 0.3687 (best 0.3683)

6h 데이터에서 epoch를 12→20→38로 늘려도 **0.5%p 이내**의 변화만 있었고, 38 epoch는 오히려 조금 나빠졌다. **B0′의 병목은 최적화 예산이 아니라 데이터**다.

## 4. B3와의 비교

| 비교 | B3 이점 | 95% CI |
|---|---:|---:|
| B3 − B0′-12 | **+10.187%p** | [+9.107, +11.328] |
| B3 − B0′-20 (exposure-matched) | **+9.723%p** | [+8.656, +10.819] |
| B3 − B0′-38 (step-matched) | **+10.006%p** | [+8.908, +11.161] |

세 비교 모두 **약 9.7~10.2%p**로 거의 같다. compute를 맞춰도 B3의 이점은 줄지 않는다.

## 5. 무엇을 말할 수 있고 없는가

### 말할 수 있다

- “B3의 이점은 단순한 **추가 optimizer step**이나 **추가 audio exposure**로 설명되지 않는다.”
- “B0′는 12 epoch에서 이미 포화됐고, 20/38 epoch로 늘려도 0.5%p 이내다.”
- “B3의 남는 이점은 **Kspon short 데이터 구성**과 관련된다.”
- “이 실험은 dev 500 전용 exploratory control이며, sealed test를 사용하지 않았다.”

### 말할 수 없다

- “Kspon short 4시간의 순수 데이터 효과다.”
- “Kspon domain 효과다.”
- “short-length 효과다.”
- “화자 독립 일반화에서 +10%p다.”
- “새 gate PASS다.”

**domain과 short-length는 아직 결합돼 있다.** 분리하려면 Kspon long-clip 4h control 또는 non-Kspon short control이 필요하다.

## 6. 한계

- dev 500, single seed 42.
- B0′-20/B0′-38은 B3와 **LR schedule shape**이 다르다 (20/38 epoch cosine vs 12 epoch cosine). Step 수는 맞췄지만 LR trajectory는 완전히 같지 않다.
- B0′-38은 동일 6h를 38 epoch 반복하므로 **데이터 반복/과적합**이 섞인다.
- test 2,400은 사용하지 않았고, 이 결과는 confirmatory가 아니다.
- B0′-20/B0′-38의 FLEURS guardrail은 측정하지 않았다 (dev-only control).
- B3는 balanced sampler, B0′는 natural sampler다. sampler 차이는 dev에서 유의하지 않았지만(B3−B3-nat CI 0 포함), 완전히 배제되지는 않는다.

## 7. 결론

> **B3의 +10%p는 “더 많은 step”도 “더 많은 audio exposure”도 아니다. B0′를 38 epoch까지 늘려도 B3 격차는 10.0%p로 유지됐다. 남는 설명은 Kspon short 데이터 구성(domain + short-length)이며, 둘을 분리하려면 별도 control이 필요하다.**

- D-071은 **recipe-level PASS**로 유지한다.
- D-072 control은 **완료**.
- 다음: **Kspon long-clip 4h / non-Kspon short 4h control**로 domain vs short-length 분리.
- **LoRA confirmatory claim은 여전히 새 holdout + matched no-LoRA comparator가 필요하다.**

## 8. 산출물

- Log: `logs/W2B/b0_matched.log`
- Sentinel: `data/wave2b/B0_MATCHED_DONE.json`
- Checkpoints: `data/wave2b/ckpt_matched/`
- Dev predictions:
  - `reports/provenance/W2B/devpred_b0p_v2_s42_e20.json`
  - `reports/provenance/W2B/devpred_b0p_v2_s42_e38.json`
- Bootstrap: `reports/provenance/W2B/matched_bootstrap.json`
- Plan: `reports/W2B_b0_matched_controls_plan.md`
- D-072 (사전등록), D-073 (결과)
