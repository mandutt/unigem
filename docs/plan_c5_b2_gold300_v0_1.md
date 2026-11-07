# C5 B2 gold 300 — data scaling pilot (v0.1)

## 1. 목적

B2 gold100에서 **99문서 overfit**이 확인됐다.

- teacher arm: train CE 2.2161→1.3024, val 2.7705→3.0095
- gold arm: train CE 2.6729→1.6723, val 2.9375→2.9969

100문서 B2는 target 효과보다 epoch/early-stop 효과가 컸다.
이 실험은 **train 300문서**로 data scaling이 overfit과 free-running 품질을 개선하는지 본다.

## 2. 설정

| 항목 | 값 |
|---|---|
| init | `b1d_teacher100/adapter_final.pt` |
| train | **300** (clean split 앞 300) |
| val | **100** (split 앞 100) |
| target | gold summary |
| trainable | adapter + decoder q/k/v/o LoRA |
| LoRA | r8 α16 dropout .05, 72 modules |
| loss | CE + 0.01 hidden |
| epochs | 2 |
| lr | 3e-4 |
| checkpoint | every 50 |
| test 163 | 미사용 |

## 3. 주의: data subset 차이

- B2 gold100 matched control은 **teacher-filtered 99건**(A1 eval batch의 길이 정렬 상위 100)을 사용했다.
- B2 gold300은 **split 순서 앞 300건**을 사용한다.
- 따라서 두 실행은 **완전한 superset 비교가 아니다.**
- 이 실험은 “100 → 300으로 늘렸을 때 overfit이 줄어드는가”의 **방향성 확인**이며, target 효과의 최종 비교는 아니다.

## 4. 평가

- val CE before/after
- teacher-forced fidelity (target=teacher, val100)
- val20 free-running
- final vs ep1
- grounded/EOS/rep4

## 5. 해석 규칙

- 300에서 val CE가 before보다 낮아지고 free-running F1/EOS가 개선
  → data scaling 유효; B2 full early-stop 또는 300 확장
- 300에서도 val CE가 악화
  → LoRA capacity/regularization 문제; rank/epochs 축소 또는 full 1,293
- 300이 100보다 개선되지만 A1에 미달
  → bridge decoder adaptation은 유효하나 capacity/teacher target 한계

## 6. 비용

- 600 step + before/after eval 400건 ×2
- 예상 **40~45분** (CPU)
- val20 generation **+5~6분**
- teacher generation 없음

## 7. 산출물

- `data/models/f5_t5gemma2_lora/b2_gold300/adapter_final.pt`
- `reports/provenance/C5_b1d/b2_gold300_metrics.json`
- `reports/provenance/C5_b1d/b2_gold300_fidelity_teacher.json`
- `reports/provenance/C5_b1d/generation_val20_b2_gold300.jsonl`
- `reports/C5_B2_GOLD300_2026-11-07.md`
