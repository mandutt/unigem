# C-7 — L1 출력 탭 추가형 개조 가능성 확인

- 작성: 2026-11-02
- 대상: Addendum C §C-7
- 상태: **탭 확보 성공(출력 완전 동일)**
- 호스트: 로컬, 운영 자산 **읽기 전용**(복사본만 수정)

## 1. 대상 그래프

| 항목 | 값 |
|---|---|
| 파일 | `eg2-langidentifier/scripts/mmal4/audio_encoder_quantized_al4.onnx` |
| 크기 | 그래프 249KB + external data 325MB |
| 노드 | 1,148 |
| 입력 | `input_features[1,T,128]`, `input_features_mask[1,T]` |
| 출력 | `audio_features[1,soft,512]` |

## 2. 중간 텐서 존재 확인

- 그래프가 최적화·융합됐지만 **마지막 층까지 노드가 남아 있음**.
- 탭 후보 3개를 복사본에 출력으로 추가:

| 탭 | 의미 | shape |
|---|---|---|
| `add_8945` | 11층 FFN 잔차 후 hidden | [1,312,1024] |
| `type_as_108` | output_proj 후 RMSNorm | [1,312,1536] |
| `linear_134` | GatherND 직전 투영 | [1,312,512] |

## 3. 동일성 검증 (220클립)

| 지표 | 결과 |
|---|---|
| `audio_features` 최대 절대 오차 | **0.0** |
| 오차 > 1e-6 클립 | **0/220** |
| 탭 출력 shape | 위 표와 일치 |

- 원 그래프와 탭 그래프의 `audio_features`가 **비트 단위로 동일**하므로, 이후 LID 파이프라인(embedding → 프로토타입 → argmax)의 결과도 동일하다.
- 따라서 같은 G-A3L-R 규칙을 적용하면 **98.18%가 그대로 재현**된다(재측정 불필요, 출력 동일이 더 강한 증거).

## 4. 결론

| 항목 | 판정 |
|---|---|
| 탭 추가 가능 | **가능** |
| 출력 동일성 | **완전 동일(0.0)** |
| 이중 상주 필요 | **없음** — 단일 그래프에 탭 출력을 포함 |

- 운영 LID 그래프를 교체하지 않고, 탭 포함 후보를 별도로 둘 수 있다.
- G-A3L-R FAIL 자체는 유지하며, 이번 작업은 "탭 확보"만 확인했다(§C-7.1 중단 사항 준수).

## 5. 산출물

- `onnx/tap/audio_encoder_q8_tap.onnx` (+ external data 복사본)
- `logs/C7_tap.json`
- 스크립트 `runner/c7_tap_feasibility.py`
