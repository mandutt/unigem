# A2 — ONNX 재수출 (오디오 타워) — 진행 기록

- 작성: 2026-11-02
- 대상 게이트: G-A1 (오디오 측 다층 hidden 노출)
- 호스트: `local`
- 스크립트: `onnx/export_audio.py`

## 1. 목적

오디오 타워에서 ① 기존 소비자용 `audio_features`(512, 투영 후 soft token)와
② C2(STT reader)용 층별 hidden(`aud_h_l*`)을 한 그래프에서 출력한다.

## 2. 입출력 계약

| 구분 | 이름 | dtype | shape |
|---|---|---|---|
| 입력 | `input_features` | float32 | `[B, T_mel, 128]` |
| 입력 | `input_features_mask` | bool | `[B, T_mel]` |
| 출력 | `audio_features` | float32 | `[N, 512]` (유효 토큰 평탄화) |
| 출력 | `audio_mask` | bool | `[B, T_audio]` |
| 출력 | `aud_h_l00/04/08/11` | float32 | `[B, T_audio, 1024]` (pre output_proj) |
| 출력 | `aud_out_proj` | float32 | `[B, T_audio, 1536]` |

## 3. 시행 기록

| 시도 | 설정 | 결과 |
|---|---|---|
| 1 | dynamo, `--mel 3000` | 420초 타임아웃 (도구 제한). 프로세스 잔존 → 종료 |
| 2 | dynamo, `--mel 750` | 7분+ 진행, 출력 없음 → 중단 |
| 3 | legacy (`dynamo=False`), `--mel 500` | **실패**: `IndexError: invalid unordered_map<K, T> key` (functorch/autograd custom op 경로) |
| 4 | dynamo, `--mel 500` | 진행 중 |

> D-008: 오디오 타워는 legacy exporter가 모델의 커스텀 autograd 연산에서 실패한다. dynamo만 사용 가능.

## 4. 결과

(진행 중 — 완료 후 갱신)

## 5. 게이트 판정

(진행 중)

## 6. 이상 징후

- 오디오 타워는 블록-슬라이딩 attention(5D mask)과 conv subsampling을 포함해 export 그래프가 크고,
  dynamo 변환 시간이 텍스트(2분)보다 훨씬 길다.
- 로컬 RAM 여유가 2~3 GiB 수준이라 export와 다른 작업을 동시에 돌리지 않는다.

## 7. 미해결

- export가 20분 내 완료되지 않으면: (a) mel 길이를 더 줄여 trace, (b) soft token만 우선 export하고
  다층 hidden은 C2 착수 시 재시도, (c) VPS(8 GiB 여유)에서 export 후 회수 — 셋 중 선택해 CP1에서 보고.

## 8. 다음 단계

export 완료 시 `eval/parity_audio.py`로 PyTorch 대비 cosine 검증.
