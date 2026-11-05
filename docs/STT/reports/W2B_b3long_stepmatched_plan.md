# Wave 2B V2 — step-matched B3-long 계획 (D-077 사전등록)

- 작성: 2026-11-05
- 목적: **short-length vs optimizer-step confound**를 분리한다.
- 선행: `docs/STT/reports/W2B_DOMAIN_LENGTH_3AI_SYNTHESIS.md` (3/3 B), D-075, D-076
- 범위: **dev 500 전용**. sealed test 2,400은 사용하지 않는다. 새 gate가 아니다.

## 1. 배경

현재 비교:

| Arm | 추가 4h | steps/epoch | total steps | final dev CER |
|---|---|---:|---:|---:|
| B3-nat | Kspon short 0.5–8s | 933 | 11,196 | 0.263314 |
| B3-long | Kspon long 8–16s | 464 | 5,568 | 0.283946 |

B3-nat이 **2.0632%p** 좋지만 CI가 0을 제외해도, long arm은 optimizer step이 **절반**이다. 따라서 “short-length 효과”와 “추가 update 효과”가 결합돼 있다.

## 2. 실행 arm

**`b3long_sm_v2_s42`**

- 동일: Wave1 6h + **Kspon long 8–16s 4h**, V2 vocab, same remapped init, seed 42, natural sampler, CPU 6 threads, 12 epoch, **patience 99** (early stop 없음), same LR/schedule.
- 변경: `batch=2`, **`grad_accum=2`**.
- 예상: **928 steps/epoch × 12 = 11,136 steps** (B3-nat 11,196과 60 steps 차이, 0.54%).
- Exposure: 10.013h × 12 ≈ **120.2h** (B3-nat 120.3h와 거의 동일).
- Final checkpoint: `data/wave2b/ckpt_controls/b3long_sm_v2_s42.pt`.
- **primary metric: final epoch dev CER**; best dev도 secondary로 보고.
- **test 2,400 사용 금지**.

## 3. 해석 규칙 (사전등록)

`D = CER(b3long_sm) − CER(b3nat)`로 정의한다. 양수면 short arm이 더 좋다.

1. **D ≥ +1.0%p AND paired utterance bootstrap 95% CI lower bound > 0**
   - “step을 맞춰도 short-length 쪽 이점이 남는다” — **exploratory, dev-only, one seed**.
2. **CI가 0을 포함하거나 D < 0.5%p**
   - “step을 맞추면 length 효과는 탐지되지 않는다.”
3. **0.5 ≤ D < 1.0%p 또는 CI가 경계**
   - **B3-nat ga2 bracket**(batch2/ga2, 11,136)을 추가 실행해 effective batch 4 vs 8까지 맞춘다.
4. B3-long(ga4) 대비 결과도 참고로 보고하되, 주 비교는 B3-nat vs b3long_sm.

**금지:** 이 실험 전에는 “short 4h 데이터 효과가 2.06%p”라고 말하지 않는다. 이 실험도 single seed·dev-only이므로 confirmatory가 아니다.

## 4. 잔여 confound

- b3long_sm은 effective batch **4**, B3-nat historical은 **8**. step 수는 맞지만 gradient noise가 다르다.
- B3-nat historical 11,196 vs 11,136: 0.54% 차이.
- Kspon long OOV 7.33% vs short V2 2.3753%; selection asymmetry.
- dev 500, seed 42 only.

## 5. DoD

- [x] D-077 사전등록
- [x] `b3long_sm_v2_s42` 12 epoch / 11,136 steps 완료
- [x] `devpred_b3long_sm_v2_s42.json` 생성
- [x] B3-nat vs b3long_sm paired bootstrap 20,000
- [x] `docs/STT/reports/W2B_b3long_stepmatched.md`
- [x] D-078 결과 기록
- [x] test 2,400 미사용 확인

## 6. 예상 소요

- 학습: **1.5~2시간 CPU**
- decode·bootstrap·보고: 15~20분
- GPU 미사용, 비용 $0

## 7. 산출물

- `runner/w2b_run_b3long_sm.py`
- `runner/w2b_watch_b3long_sm.py`
- `logs/W2B/b3long_sm.log`
- `data/wave2b/B3LONG_SM_DONE.json`
- `data/wave2b/ckpt_controls/b3long_sm_v2_s42.pt`
- `reports/provenance/W2B/devpred_b3long_sm_v2_s42.json`
- `reports/provenance/W2B/b3long_sm_bootstrap.json`
- `docs/STT/reports/W2B_b3long_stepmatched.md`
