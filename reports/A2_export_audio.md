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

| 시도 | 설정 | 소요 | 결과 |
|---|---|---|---|
| 4 | dynamo, `--mel 500` | **831초+ (중단)** | 출력 파일 없음, RSS 1.6GB→216MB. 그래프 변환 단계에서 비정상적으로 장시간 → 중단 |

**결론: 오디오 타워 다층 export는 현 로컬 환경에서 완료하지 못했다.** legacy는 실패, dynamo는 14분 이상
출력을 내지 않았다(무한 대기인지 극단적 지연인지 미확정). 원인 후보: 블록-슬라이딩 attention의 5D mask
변환 + conv subsampling이 dynamo 변환에서 과도한 그래프를 만든다.

## 5. 게이트 판정

**G-A1(오디오 부분): 보류(INCONCLUSIVE)** — 텍스트 다층 출력은 PASS이나, 오디오 다층 hidden은 확보하지 못했다.
문서 §0-5에 따라 우회·재시도는 사용자 지시 후 진행한다.

## 6. 이상 징후

- 오디오 타워는 텍스트(2분)와 달리 dynamo 변환 비용이 비정상적으로 크다.
- 로컬 RAM 여유 2~3 GiB로, export 중 다른 작업 병행이 어렵다.

## 7. 미해결 — CP1 선택지

1. **오디오는 기존 운영 인코더 유지** — G-A3L/C2-A3는 기존 q8 오디오 인코더로 진행. 다층 hidden이 필요하면
2. **VPS(8 GiB)에서 export** — 메모리 여유가 크고, 완료 후 ONNX(1~2GB) 회수 경로 필요(base64 분할 또는 HF 비공개 업로드).
3. **기존 q8 오디오 그래프에 중간 텐서를 출력으로 추가** — 재export 없이 층 hidden 확보(양자화 그래프 기준).
4. **C2 착수 시점으로 연기** — Phase A는 텍스트 그래프만으로 종료.

## 8. 다음 단계

CP1에서 위 1~4 중 선택. 그 전까지 A4는 텍스트 그래프만 양자화·측정한다.
