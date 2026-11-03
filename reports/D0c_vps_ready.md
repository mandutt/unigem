# D0-c — VPS 재기동·점검 (부분 완료)

- 작성: 2026-11-03
- 대상: Addendum D §D0-c
- 상태: **부분 완료 — 5대 running/venv/디스크 확인. 오디오 Q8 그래프 배포 진행 중**
- 호스트: eg2-1~eg2-5 (InstaBox 계정 B)

## 1. 기동

| 항목 | 결과 |
|---|---|
| 요청 | 5대 전부 `POST /start` 202 queued |
| rate limit | 3대 → 60초 대기 → 2대, 정상 |
| 최종 상태 | **5대 모두 running** |
| 시작 시각 | 2026-11-03 11:53 KST |
| `maxRunMinutes` | 480분 (8시간) — 19:53 KST 강제 정지 예정 |
| auto-suspend | 1800초 (30분 유휴) |

## 2. 호스트 상태

| 호스트 | vCPU | RAM free | `/data` | Python | lock SHA256 | 비고 |
|---|---|---|---|---|---|---|
| eg2-1 | 4 | 7,499MB | 20G, 4.8G 사용, **15G free** | 3.13.5 | `6cccf5e9…0470` | checkpoint 보유, 오디오 export 수행 |
| eg2-2 | 4 | 7,613MB | 20G, 5.6G 사용, **14G free** | 3.13.5 | 동일 | text ONNX만 |
| eg2-3 | 4 | 7,513MB | 20G, 5.6G 사용, **14G free** | 3.13.5 | 동일 | text ONNX만 |
| eg2-4 | 4 | 7,608MB | 20G, 5.6G 사용, **14G free** | 3.13.5 | 동일 | text ONNX만 |
| eg2-5 | 4 | 7,611MB | 20G, 5.6G 사용, **14G free** | 3.13.5 | 동일 | text ONNX만 |

- lock 단일 `6cccf5e9dde43d06ddbd020f46a6696be5bb6e592dd7abb1ab130ebfcf310470` (5대 동일).
- HF 접속 HTTP 200, 0.07~0.08s (latency only; throughput 미측정).
- eg2-1에만 `models/embeddinggemma-2-f9972ac2/model.safetensors` (1,488,915,288B)가 있다. eg2-2~5에는 모델이 없다.

## 3. 발견: 오디오 Q8 그래프가 없다

D-β는 `eg2_audio_q8_layers.onnx`(또는 동등한 다층 오디오 그래프)가 각 호스트에 필요하다. 현재 VPS에는 **text ONNX만** 있다.

- eg2-1에 `export_audio_new.py`로 FP32 t1600_l12를 export했다(9.3MB + 1.2GB data, 11:57).
- `quantize_q8_new.py`로 Q8을 만들었지만 **1.2GB**로 줄지 않았다(MatMul만 양자화; Conv/기타 가중치 FP32 잔존).
- 따라서 연구용 Q8 1.2GB는 5대 배포에 부적합하다.
- **로컬 운영 Q8 그래프**(`onnx/eg2_audio_q8_layers.onnx` 246KB + `_data` 325MB)를 eg2-1에 전송 중이다(SCP, `-C`).
- 전송 후 eg2-1에서 ORT 로드·카나리를 확인하고, 나머지 4대는 eg2-1의 공개 HTTP(또는 허용된 전송 경로)로 325MB를 받는 방식이 필요하다.

## 4. D0-c 잔여 항목

| 항목 | 상태 |
|---|---|
| 5대 기동 | **완료** |
| venv lock 일치 | **완료** |
| 디스크/RAM/네트워크 | **완료(기본)** |
| 오디오 Q8 그래프 배포 | **진행 중** (로컬→eg2-1 SCP) |
| 오디오 Q8 카나리 parity | **대기** (그래프 도착 후) |
| 나머지 4대 그래프 배포 | **대기** (전송 경로 확정 후) |
| D0-d cost probe | **대기** (eg2-1 그래프 도착 후) |

## 5. 판정

**D0-c는 아직 완료가 아니다.** 5대는 정상 기동했고 venv/디스크/네트워크 기본 점검은 통과했지만, **D-β 학습에 필요한 오디오 Q8 그래프가 각 호스트에 없어** Wave 1을 시작할 수 없다.

다음 순서:
1. 로컬→eg2-1 Q8 그래프 전송 완료 확인
2. eg2-1에서 ORT 로드 + 로컬 대비 카나리 cosine
3. eg2-1 → eg2-2~5 배포 경로 확정·실행
4. D0-d 비용 probe (eg2-1 또는 각 호스트)
5. 그래프가 준비된 뒤에만 D-β Wave 1

## 6. AM-6 이행 표

| 요구 (D0-c) | 이행 |
|---|---|
| 5대 기동 | 이행 |
| 호스트별 df/RAM/시계/네트워크 | 부분 — df/RAM/HF latency; 대역폭 미측정 |
| venv lock 일치 | 이행 |
| 모델 SHA256 | **미이행** — checkpoint는 eg2-1만, 오디오 그래프는 배포 중 |
| 오디오 Q8 카나리 | **대기** |
| 데이터 예산 확정 | 부분 — free 13~15G 확인 |

## 7. 산출물

- `runner/d0c_start_vps.py`
- `runner/d0c_vps_ready.py`
- `reports/provenance/D0c_vps_start.json`
- `reports/provenance/D0c_vps_ready.json`
- `logs/D0c_start_vps.log`
- eg2-1: `onnx/eg2_audio_research_fp32_t1600_l12.onnx` + `.data` (연구용, 1.2GB Q8 포함)
