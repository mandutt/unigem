# Wave 2B V2 — domain/length control 결과 (D-075)

- 작성: 2026-11-05 22:15 KST
- 범위: **dev 500 전용**. sealed test 2,400은 사용하지 않았다.
- 성격: exploratory control. **gate 아님.**
- 사전등록: `reports/W2B_domain_length_controls_plan.md`, D-074 / D-074a
- 보존: D-074b, `data/wave2b/PRESERVE_CONTROL_CACHES.txt`

## 1. 데이터

| 항목 | 값 |
|---|---|
| Kspon long | **1,327클립 / 4.0025h**, 8–16s, OOV **1,574/21,477 = 7.33%** |
| Zeroth long | **1,395클립 / 4.0014h**, 8–16s, OOV **436/9,758 = 4.47%** |
| Wave1 base | 2,384클립 / 6h |
| 10h cache | Kspon long **10.0130h / 3,711클립**, Zeroth long **10.0125h / 3,779클립** |

### D-074a — 원안 short-domain control 불가

Zeroth short 0.5–8s의 Wave1 제외 잔여는 **1,012클립 / 1.6574h**뿐이었다. 4h short-domain arm을 만들 수 없어 **Zeroth long 8–16s 4h**로 대체했다.

## 2. 학습

모두 V2 vocab, same remapped init(`w2a_fc_concat_s42_v2head.pt`), seed 42, natural sampler, 12 epoch, patience 4, CPU 6 threads.

| Arm | 추가 데이터 | final dev CER | best dev CER | steps/epoch | total steps |
|---|---|---:|---:|---:|---:|
| B0′-12 | 없음 | 0.370084 | 0.3701 | 298 | 3,576 |
| B3-12 balanced | Kspon short 0.5–8s | 0.268214 | 0.2682 | 933 | 11,196 |
| B3-nat | Kspon short 0.5–8s | **0.263314** | 0.2633 | 933 | 11,196 |
| **B3-long** | Kspon long 8–16s | **0.283946** | 0.2828 (ep9) | **464** | **5,568** |
| **B3-zeroth-long** | Zeroth long 8–16s | **0.365571** | 0.3654 (ep9) | **473** | **5,676** |

- B3-long: 5,377.3초 (1.494h), final epoch12 **0.2839**
- B3-zeroth-long: 5,461.3초 (1.517h), final epoch12 **0.3656**

## 3. Paired utterance bootstrap (20,000 resamples, seed 42)

부호는 `CER(A) − CER(B)`; 음수면 A가 더 좋다.

| 비교 | Δ CER (%p) | 95% CI |
|---|---:|---:|
| B3-nat − B3-long | **−2.0632** | **[−2.9625, −1.1861]** |
| **B3-long − B3-zeroth-long** | **−8.1625** | **[−9.2063, −7.1645]** |
| B3-nat − B3-zeroth-long | −10.2257 | [−11.3818, −9.1389] |
| B0′ − B3-long | +8.6138 | [+7.6628, +9.5939] |
| B0′ − B3-zeroth-long | +0.4513 | [−0.2087, +1.1278] |
| B3-balanced − B3-long | −1.5732 | [−2.4710, −0.6910] |

## 4. 해석

### 4.1 Domain 효과 — 강함

`B3-long`과 `B3-zeroth-long`은 **같은 8–16s, 같은 4h, 같은 10h, 같은 natural sampler**이며 total step도 5,568 vs 5,676으로 거의 같다.

- Kspon long **0.2839** vs Zeroth long **0.3656**
- **Kspon이 8.16%p 더 좋음**, CI **[−9.21, −7.16]**, 0 제외.

→ **Kspon domain(또는 Kspon long 데이터 구성) 효과가 크다.** domain을 바꾸면 같은 길이에서도 큰 손실이 난다.

### 4.2 Length 효과 — 아직 확정 불가

B3-nat(short) **0.2633** vs B3-long(long) **0.2839**는 B3-nat이 **2.06%p** 좋고 CI도 0을 제외한다. 그러나:

- B3-nat: **933 steps/epoch, 총 11,196 steps**
- B3-long: **464 steps/epoch, 총 5,568 steps**
- B3-balanced도 B3-long보다 1.57%p 좋다(CI 0 제외).

long clip은 같은 4h에서 clip 수가 적어 optimizer step이 절반이다. 따라서 **2.06%p를 순수 길이 효과로 귀속할 수 없다.** short-length가 기여할 가능성은 있지만, **step-matched B3-long** 없이는 인과 주장 금지.

### 4.3 B0′ 대비

- B0′ **0.3701** → B3-long **0.2839**: Kspon long만으로 **8.61%p** 개선(CI 0 제외).
- B0′ **0.3701** → B3-zeroth-long **0.3656**: **+0.45%p**, CI **[−0.21, +1.13]**로 유의하지 않음.

→ Kspon long 4h는 B0′보다 명확히 낫지만, Zeroth long 4h는 B0′와 사실상 차이 없음. **domain 가설과 일치.**

## 5. 한계

1. **원래 계획한 non-Kspon short 4h 직접 대조는 미실시** — Zeroth short 잔여 1.66h. domain 효과는 long에서 확인했지만 short에서 직접 확인하지 못했다.
2. **B3-nat vs B3-long은 step 수가 다르다** — length 효과는 inconclusive. step-matched B3-long(grad accumulation 2 또는 batch 1)이 필요하다.
3. **단일 seed, dev 500** — exploratory. test 2,400 재사용 금지.
4. B3-zeroth-long은 **Zeroth long**이므로 원래의 “non-Kspon short”와 동일하지 않다.

## 6. 결론

- **Domain 효과는 강하고 재현 가능한 방향**으로 관측됐다: 같은 long 길이에서 Kspon이 Zeroth보다 **8.16%p** 우수.
- **Short-length 효과는 시사되지만 미확정**: B3-nat이 B3-long보다 2.06%p 좋으나 step 수가 2배다.
- B3의 +10%p 이점은 **Kspon domain + short 데이터 구성**이 함께 만든 것으로 보이며, **compute/exposure만으로는 설명되지 않는다**는 D-073과 일치한다.
- 다음 우선순위:
  1. **step-matched B3-long** — length vs step 분리 (약 1.5~2h CPU)
  2. **non-Kspon short 4h** — FLEURS train 등 공개 데이터로 별도 승인 후 구성
  3. 위 결과 전에는 length 인과 주장 금지

## 7. 산출물

- `reports/provenance/W2B/devpred_b3long_v2_s42.json`
- `reports/provenance/W2B/devpred_b3zerothlong_v2_s42.json`
- `reports/provenance/W2B/domain_controls_bootstrap.json`
- `data/wave2b/DOMAIN_CONTROLS_DONE.json`
- `logs/W2B/domain_controls.log`
- `logs/W2B/domain_controls_watch_state.json`
- `data/wave2b/ckpt_controls/b3long_v2_s42.pt`
- `data/wave2b/ckpt_controls/b3zerothlong_v2_s42.pt`
