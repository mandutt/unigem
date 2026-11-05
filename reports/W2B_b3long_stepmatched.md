# Wave 2B V2 — step-matched B3-long 결과 (D-078)

- 작성: 2026-11-06 (KST)
- 상태: **완료 — dev 500 전용, exploratory, gate 아님**
- 사전등록: `reports/W2B_b3long_stepmatched_plan.md` (D-077)
- 범위: **dev 500만 사용. sealed test 2,400 미사용.**
- 학습: CPU 6 threads, GPU 미사용, 비용 $0

## 1. 실행

| 항목 | 값 |
|---|---|
| Arm | `b3long_sm_v2_s42` |
| 데이터 | Wave1 6h + Kspon long 8–16s 4h, same `feats_10h_kspon_long` |
| V2 vocab | 1,329자 |
| Init | same remapped 2A checkpoint (`missing=0 unexpected=0`) |
| 변경 | `batch=2`, `grad_accum=2` |
| Steps | **928/epoch × 12 = 11,136** |
| B3-nat steps | 11,196 (0.54% 차) |
| Exposure | 10.013h × 12 ≈ **120.2h** |
| Seed / sampler | 42 / natural |
| Patience | 99 (early stop 없음) |
| 소요 | **5,814.4초 = 96.9분** |
| Final ckpt | `b3long_sm_v2_s42.pt` |
| Final sha256 | `e2a4efedab44c75c529389dfd4e54622583f1bf6a46da46a0291fccb36248547` |
| Best sha256 | `367a5ab9a75449b70c8b8a9ef1ab1f7e387cb8ce0c7db24c1979299ef8da4dc0` |

## 2. 학습 곡선

| Epoch | dev CER | errors/ref |
|---:|---:|---:|
| 1 | 0.3231 | 2,506/7,755 |
| 2 | 0.3121 | 2,420/7,755 |
| 3 | 0.3014 | 2,337/7,755 |
| 4 | 0.3019 | 2,341/7,755 |
| 5 | 0.2928 | 2,271/7,755 |
| 6 | 0.2913 | 2,259/7,755 |
| 7 | 0.2834 | 2,198/7,755 |
| 8 | 0.2814 | 2,182/7,755 |
| 9 | 0.2839 | 2,202/7,755 |
| 10 | 0.2805 | 2,175/7,755 |
| **11 (best)** | **0.2790** | **2,164/7,755** |
| **12 (final, primary)** | **0.2794** | **2,167/7,755** |

- **primary = final epoch dev CER 0.2794326**
- best = epoch 11 **0.2790**
- final과 best 차이 0.04%p로 사실상 동일.

## 3. 비교

| Arm | 추가 4h | steps | final dev CER | errors/7,755 |
|---|---|---:|---:|---:|
| B0′-12 | 없음 | 3,576 | 0.370084 | 2,870 |
| B3-12 balanced | Kspon short 0.5–8s | 11,196 | 0.268214 | 2,080 |
| **B3-nat** | Kspon short 0.5–8s | 11,196 | **0.263314** | **2,042** |
| B3-long (ga4) | Kspon long 8–16s | 5,568 | 0.283946 | 2,202 |
| **b3long_sm (ga2)** | Kspon long 8–16s | **11,136** | **0.279433** | **2,167** |

### Paired utterance bootstrap (20,000, seed 42)

| 비교 | point | 95% CI | 해석 |
|---|---:|---:|---|
| **b3long_sm − B3-nat** | **+1.6119%p** | **[+0.7606, +2.4933]** | short arm이 더 좋음 |
| b3long_sm − B3-long(ga4) | −0.4513%p | [−1.1119, +0.2055] | step 증가로 개선됐지만 유의하지 않음 |
| b3long_sm − B3(balanced) | +1.1219%p | [+0.2461, +1.9997] | B3 balanced가 더 좋음 |
| b3long_sm − B0′ | **−9.0651%p** | **[−10.0532, −8.0875]** | baseline보다 크게 좋음 |

부호 규칙: `D = CER(b3long_sm) − CER(비교 arm)`. 양수면 비교 arm(short/B3-nat)이 더 좋다.

## 4. 사전등록 판정

D-077 규칙:
1. `D ≥ +1.0%p AND CI lower > 0` → short-length 이점이 남는다 (exploratory)
2. CI가 0 포함 또는 `D < 0.5%p` → length 효과 미탐지
3. `0.5 ≤ D < 1.0%p` 또는 경계 → B3-nat ga2 bracket

결과:
- `D = +1.6119%p`, CI **[+0.7606, +2.4933]**
- **D ≥ +1.0%p 충족, CI lower > 0 충족**

→ **“step을 맞춰도 short-length 쪽 이점이 남는다”** (exploratory, dev 500, single seed, one training run).

## 5. 해석과 한계

### 5.1 step confound는 일부만 설명

- 기존 B3-nat − B3-long(ga4) 차이: **2.0632%p**
- step-matched 후 B3-nat − b3long_sm 차이: **1.6119%p**
- step 증가로 줄어든 차이: **0.4513%p** (유의하지 않음)
- 남은 차이: **1.61%p**

즉 **추가 optimizer step이 long arm의 열세를 일부 설명하지만, 전부 설명하지는 못한다.**

### 5.2 그러나 “길이만의 효과”라고 단정할 수 없다

- **OOV 차이**: Kspon long OOV **7.33%** vs short V2 **2.3753%**
- selection asymmetry: 같은 4h라도 long은 8–16s, short는 0.5–8s
- **effective batch 4(sm) vs 8(B3-nat)**: step 수는 맞췄지만 gradient noise는 다름
- **single seed 42, dev 500 only**
- **sealed test 2,400 미사용**

따라서 이 결과는 **“short 데이터 조건이 step을 맞춰도 더 낮은 CER을 보였다”**는 증거이지, **“길이 자체가 인과적으로 1.61%p를 만든다”**는 확정은 아니다.

### 5.3 B3-long 내부 비교

- ga4 0.283946 → ga2 0.279433: **−0.4513%p**
- CI가 0을 포함하므로 “step 증가가 유의하게 개선했다”고 말할 수 없다.
- 그래도 long arm이 11,136 steps에서 0.2794까지 내려온 것은 step budget이 일부 기여했음을 보여준다.

## 6. 결론

1. **step-matched 조건에서도 short arm(B3-nat)이 long arm(b3long_sm)보다 1.61%p 좋다.**
2. **step 증가는 long arm을 0.45%p 개선했지만 유의하지 않다.**
3. **D-077 규칙상 “short-length 이점이 남는다”로 기록하되, exploratory·single-seed·dev-only로 한정한다.**
4. **OOV 7.33% vs 2.3753%의 교란**이 남아 있으므로 “길이 효과”라고 인과적으로 부르지 않는다.
5. **sealed test 2,400은 사용하지 않았다.** confirmatory 주장에는 새 holdout이 필요하다.

## 7. 산출물

- `logs/W2B/b3long_sm.log`
- `logs/W2B/b3long_sm_watch_state.json`
- `data/wave2b/B3LONG_SM_DONE.json`
- `data/wave2b/ckpt_controls/b3long_sm_v2_s42.pt`
- `data/wave2b/ckpt_controls/b3long_sm_v2_s42.best.pt`
- `reports/provenance/W2B/devpred_b3long_sm_v2_s42.json`
- `reports/provenance/W2B/b3long_sm_bootstrap.json`
- `logs/W2B/decode_b3long_sm.out`

## 8. DoD

- [x] D-077 사전등록
- [x] `b3long_sm_v2_s42` 12 epoch / 11,136 steps 완료
- [x] `devpred_b3long_sm_v2_s42.json` 생성
- [x] B3-nat vs b3long_sm paired bootstrap 20,000
- [x] `reports/W2B_b3long_stepmatched.md`
- [x] D-078 결과 기록
- [x] test 2,400 미사용 확인
