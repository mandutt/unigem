# C5 B2 Slot Repair / Grounded Ceiling (2026-11-07)

## 0. 결론

오프라인 slot repair로 **grounded 100%**는 달성할 수 있다.  
그러나 **실제 요약 품질 상한은 낮다.**

| 방법 | grounded | char F1 | slot preservation | new slot | nonempty |
|---|---:|---:|---:|---:|---:|
| B2 원본 | 18.01% | **0.3349** | 0.2198 | 622 | 100% |
| drop-new-sentences | **100%** | **0.2624** | 0.1200 | **0** | 100% |
| oracle subset (target-aware) | **100%** | **0.2719** | 0.1191 | **0** | 100% |

- **grounded 상한은 100%** — new slot 문장을 모두 버리면 달성.
- 하지만 **F1 상한은 0.272**(target까지 사용하는 oracle)이고, deployable한 drop 방식은 **0.262**.
- **71/161 (44.1%)**은 모든 문장을 버려서 **source 첫 문장 fallback**으로 채워졌다.
- 즉 “grounded 100%”는 **요약을 거의 버린 결과**다.

## 1. 실제 소요 시간

- 구현: 약 10분
- 161건 적용·검증: **수십 초**
- 집계·표본 확인: 약 2분
- **총 15분 이내**

모델 재실행이나 GPU/CPU 추론은 없었다.

## 2. 방법

각 B2 출력에 대해:

1. 원본이 grounded면 그대로 유지
2. new slot이 있는 **문장만 삭제**
3. 삭제 후 빈 출력이면 **source 첫 문장**으로 fallback
4. `oracle_subset`은 new slot이 없는 문장 중 **target과 가장 F1이 높은 subset** 선택  
   - target을 사용하므로 **배포 불가능한 상한**이다.

## 3. 결과

### 원본

- grounded 29/161 = 18.01%
- new slot 622 / summary slot 981 = 63.4%
- missing source slot 1,590
- preservation 0.2198

### drop-new-sentences

- grounded 161/161 = 100%
- new slot 0
- missing 1,766
- preservation 0.1200
- F1 0.2624
- fallback 71/161
- 평균 문자 길이 176.2

### oracle subset

- grounded 161/161 = 100%
- F1 0.2719
- missing 1,767
- preservation 0.1191
- fallback 71/161
- 평균 문자 길이 137.6

### fallback 제외

| subset | n | F1 | preservation |
|---|---:|---:|---:|
| drop, non-fallback | 90 | 0.2731 | 0.1405 |
| drop, fallback | 71 | 0.2488 | 0.0940 |
| oracle, non-fallback | 90 | **0.2901** | 0.1389 |
| oracle, fallback | 71 | 0.2488 | 0.0940 |

fallback을 제외해도 F1은 0.27~0.29 수준이다.

## 4. 해석

### 확인된 것

- **slot post-processing으로 grounded 100%는 가능**하다.
- 그러나 **source slot 보존이 0.22 → 0.12로 악화**된다.
- 44%는 source 첫 문장으로 대체되어 **B2 생성 요약이 아니다.**
- target-aware oracle도 F1 0.272로, **A1 native pilot300 0.6576의 절반 이하**다.

### 결론

> **grounded 상한 100%는 의미 있는 상한이 아니다.**  
> 요약을 버리면 grounded는 100%가 되지만, 요약 품질은 오히려 낮아진다.

Slot-constrained post-processing은 **제품 안전 필터**로는 유용하지만, B2의 **품질 문제를 해결하지 못한다.**

## 5. 다음

- **Slot-constrained decoding** — 생성 중 제한; 구현 2~4시간
- **Slot auxiliary loss** — 학습 중 slot 보존; 재학습 필요
- **Teacher sequence-level KD** — A1 native pilot300의 grounded 요약을 target으로 사용; 가장 유망
- **A1 native pilot300 유지** — 현재 fallback

## 6. 상태

| 항목 | 값 |
|---|---|
| offline slot repair | **완료** |
| grounded ceiling | **100%** |
| F1 ceiling (oracle) | **0.2719** |
| deployable F1 (drop) | **0.2624** |
| fallback rate | **44.1%** |
| test 163 | **sealed** |
| product candidate | 없음 |
