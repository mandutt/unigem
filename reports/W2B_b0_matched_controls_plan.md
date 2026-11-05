# Wave 2B V2 — matched-budget reader controls

- 작성: 2026-11-05 (KST)
- 목적: 3-AI 검토 공통 권고에 따라, B0′ vs B3의 **compute/domain/length confound**를 분리하기 위한 reader-only control 두 개를 사전등록한다.
- 범위: **dev 500 전용**. **sealed test 2,400은 사용하지 않는다.** 새 gate가 아니다.
- 기준 결과: `reports/W2B_v2_gate_results.md`, D-071.
- 검토: `docs/hoplite/w2b_v2_gate/2026-11-05_hoplite-review_w2b_v2_gate_{GLM,SONNET,LUNA}.md` (3/3 B).

## 1. 왜 필요한가

현재 B0′ vs B3:

| Arm | unique audio | epochs | steps/epoch | total steps | audio exposure | dev CER |
|---|---:|---:|---:|---:|---:|---:|
| B0′ | 6.0008h | 12 | 298 | 3,576 | 72.0h | 0.3701 |
| B3 | 10.0221h | 12 | 933 | 11,196 | 120.3h | 0.2682 |

B3는 B0′보다 **step 3.13×, audio exposure 1.67×**이고, Kspon domain과 short-length 분포도 추가된다. 따라서 B0′−B3의 +10.19%p를 “short 4h 데이터 효과”로 귀속할 수 없다.

## 2. Control arms

모두 **B0′와 같은 Wave 1 6h feature, 같은 V2 vocab, 같은 remapped init, seed 42, natural sampler**를 쓴다. Early stopping으로 budget이 줄지 않도록 **patience 99**로 고정한다.

| Arm | epochs | total steps | audio exposure | 맞추는 축 | B3와의 관계 |
|---|---:|---:|---:|---|---|
| **B0′-20** | 20 | **5,960** | **120.0h** | **audio exposure** | B3-12: 120.3h / 11,196 steps |
| **B0′-38** | 38 | **11,324** | 228.0h | **optimizer steps** | B3-12: 11,196 steps / 120.3h |

- B0′-20은 **exposure-matched**지만 step은 B3의 약 절반이다.
- B0′-38은 **step-matched**지만 exposure는 B3의 약 1.9배다.
- 하나의 run으로 step과 exposure를 동시에 맞출 수는 없다. 두 control은 **서로 다른 estimand**다.

## 3. 학습 설정

- Feature: `data/wave1/feats/fc.npz`, dev `data/wave2b/feats_dev/fc.npz`
- Vocab: `data/wave2b/vocab_v2.json` (1,329), `--retarget`
- Init: `data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt`
- Reader: `arch=base`, 9,183,922 params
- Batch 2, grad accumulation 4, threads 6, CPU
- Seed 42, cosine schedule (T_max = epochs × steps/epoch)
- `--patience 99` (full budget; no early stop)
- Checkpoints: `data/wave2b/ckpt_matched/`
- Log: `logs/W2B/b0_matched.log`
- Sentinel: `data/wave2b/B0_MATCHED_DONE.json`

## 4. 판정 규칙 (사전등록)

이 실험은 **exploratory control**이며 gate가 아니다. 다음을 그대로 보고한다.

1. **Primary:** 각 control의 **final epoch dev CER** (budget-matched).
2. **Secondary:** best dev CER과 epoch, full dev curve.
3. **비교:** B0′-20 vs B3-12 (exposure), B0′-38 vs B3-12 (steps), B0′-12 vs B3-12 (original).
4. Paired utterance bootstrap 95% CI를 가능한 비교에 붙인다.
5. **해석 규칙:**
   - B0′-38이 B3에 근접하면 → **추가 step이 큰 부분을 설명**.
   - B0′-20이 B3에 근접하면 → **추가 audio exposure가 큰 부분을 설명**.
   - 둘 다 B3에 크게 못 미치면 → **Kspon domain/short-length/데이터 구성**이 남는 효과.
   - 두 control 모두로도 **domain과 short-length를 분리할 수 없다**; 그 분리는 별도 Kspon long/non-Kspon short control이 필요하다.
6. **금지:** test 2,400 사용, “data effect” 확정, gate PASS 재판정, LoRA confirmatory claim.
7. B0′-20/B0′-38 중 어느 하나가 B0′-12보다 좋지 않으면 그 사실도 그대로 기록한다.

## 5. 예상 소요

- B0′-20: 약 20 × 270초 ≈ **1.5시간**
- B0′-38: 약 38 × 270초 ≈ **2.9시간**
- 순차 실행 총 **4.5~5시간** (CPU 6 threads, 다른 학습 없음)
- GPU 미사용, VPS 미사용, 비용 $0

## 6. 실행 순서

1. B0′-20 (빠른 exposure control)
2. B0′-38 (step control)
3. dev 500 prediction·bootstrap
4. `reports/W2B_b0_matched_controls.md` 작성
5. D-072 결과 기록

## 7. 재현

```text
python train/d5_reader.py \
  --features data/wave1/feats/fc.npz \
  --dev-features data/wave2b/feats_dev/fc.npz \
  --vocab-file data/wave2b/vocab_v2.json --retarget \
  --arch base --arm b0p_v2_s42_e20 \
  --init-ckpt data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt \
  --epochs 20 --patience 99 --batch 2 --grad-accum 4 \
  --seed 42 --threads 6 --device cpu \
  --ckpt-dir data/wave2b/ckpt_matched

python train/d5_reader.py \
  --features data/wave1/feats/fc.npz \
  --dev-features data/wave2b/feats_dev/fc.npz \
  --vocab-file data/wave2b/vocab_v2.json --retarget \
  --arch base --arm b0p_v2_s42_e38 \
  --init-ckpt data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt \
  --epochs 38 --patience 99 --batch 2 --grad-accum 4 \
  --seed 42 --threads 6 --device cpu \
  --ckpt-dir data/wave2b/ckpt_matched
```
