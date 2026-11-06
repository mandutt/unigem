# C5 A2-null — feasibility probe

- 작성: 2026-11-06
- 상태: **probe 완료, feature extraction/training 미착수**
- 모델: `data/models/embeddinggemma-2-f9972ac2`
- 데이터: clean F5 10건 (probe), 전체 1,617은 후속
- 원본: `reports/provenance/C5_a2null/nullspace_probe.json`

## 1. Null-space 검증

| 항목 | 값 |
|---|---:|
| projection W | **768 × 512** |
| rank | **512** |
| nullity | **256** |
| singular min / max | 10.52 / 122.43 |
| `max|WᵀP|` | **4.29e-06** |
| `max|PᵀP−I|` | 4.77e-07 |
| `W h` vs final projection max error | **0.0** |

`P`는 W의 left null space(768×256)로 정상 추출됐다. W는 full rank 512이고, 출력 768d 중 256d가 비어 있다.

## 2. Text intermediate layer

`language_model`은 24층, hidden 512, final projection 768이다.

- 최종 projection 입력은 **post-norm 512d hidden**
- forward hook으로 확인: `last_hidden_state = W @ norm(h_last)`, 오차 **0.0**
- `hidden_states`에는 embedding + 24층 출력이 포함됨

### PCA 256 explained variance (probe 10건, 7,644 tokens)

| layer | explained variance | top-1 |
|---|---:|---:|
| 2 | 0.9028 | 0.0745 |
| 6 | 0.9456 | 0.0554 |
| **12** | **0.9510** | 0.0737 |
| 18 | 0.9278 | 0.1661 |
| 23 | 0.8937 | 0.2158 |

- layer 12가 256d에서 가장 높은 분산 보존(95.1%)
- layer 2도 90.3%로 usable
- **primary 후보: layer 12**, 비교 후보: layer 6/2

## 3. Injection orthogonality

무작위 null vector `x`를 `P x`로 주입했을 때:

| 항목 | 값 |
|---|---:|
| `final · (P x)` max | **0.00475** |
| pooled text cosine (random injection) | 0.999995 |

- `final`은 W의 column space에 있으므로 `P x`와 직교한다.
- **원래 768d 성분은 변하지 않는다.**
- 단, **text pooled vector 전체는 injection만큼 변한다.** Reddit 원문의 “text bit-for-bit unchanged”는 **audio에만 주입하는 경우**에 성립한다. A2-null은 text에도 주입하므로 total embedding은 변한다.

## 4. T5Gemma 2 external memory

- `encoder_outputs=BaseModelOutput(last_hidden_state=memory)`로 640d memory 주입 확인
- dummy memory 640d에서 decoder forward 성공 (`logits [1,4,262144]`, bf16)
- 512d/768d는 거부됨 → adapter 출력은 **640d**로 맞춰야 함

## 5. 판정

| 항목 | 결과 |
|---|---|
| nullity 256 | PASS |
| WᵀP orthogonality | PASS |
| final projection 일치 | PASS |
| PCA 256 | PASS (layer 12 95.1%) |
| T5 external memory 640d | PASS |
| **A2-null-seq 진행** | **가능** |

## 6. 다음

1. layer 12 기준 PCA를 train 1,293에서 fit
2. final 768 + PCA 256 injection → 768 feature cache
3. adapter 768→640 smoke
4. 10 step loss/RSS/step time
5. full train은 별도 승인

**주의:** 이 probe는 A2-null이 **작동 가능**하다는 것만 확인했다. A1보다 요약 품질이 좋다는 의미는 아니다.
