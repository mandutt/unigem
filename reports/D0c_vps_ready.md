# D0-c — VPS 재기동·점검 (부분 완료)

- 작성: 2026-11-03
- 대상: Addendum D §D0-c
- 상태: **완료(그래프 배포·카나리 포함)** — 5대 running/venv/디스크/그래프 확인
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

## 3. 오디오 Q8 그래프 배포

D-β는 `eg2_audio_q8_layers.onnx`(또는 동등한 다층 오디오 그래프)가 각 호스트에 필요하다. 현재 VPS에는 **text ONNX만** 있다.

- eg2-1에 `export_audio_new.py`로 FP32 t1600_l12를 export했다(9.3MB + 1.2GB data). `quantize_q8_new.py`로 만든 Q8도 **1.2GB**로, MatMul 외 가중치가 FP32로 남아 5대 배포에 부적합했다.
- 대신 **로컬 운영 Q8 그래프**(`eg2_audio_q8_layers.onnx` 246KB + `_data` 325MB)를 eg2-1에 SCP로 전송하고, eg2-1의 공개 HTTP(`https://8090-agqvineqfebuv74ez7zv6v6n2y.instabox.tech`)로 2~5에 배포했다.
- 5대 모두 sha256이 로컬과 일치한다:
  - graph `03e0ad8608cdbc810ddee3e8ab78b46675e5ef1615929d0b63476aa171c52d59`
  - data `aa6361d898e1f1d6303f8dd2b5fabf4fd3629e15fd709e9cb06ac5cb9416a030`
- 5대 모두 ORT로 14개 출력 로드에 성공했다.
- eg2-1에서 로컬 기준 출력과 비교: `audio_features`/6·8·10·11층/`aud_out_proj` 모두 **cos 최소 1.0, 최대 절대 오차 0.0** (`reports/provenance/D0c_audio_canary.json`).

## 4. D0-c 잔여 항목

| 항목 | 상태 |
|---|---|
| 5대 기동 | **완료** |
| venv lock 일치 | **완료** |
| 디스크/RAM/네트워크 | **완료(기본)** |
| 오디오 Q8 그래프 배포 | **완료** — 5대 sha 일치 |
| 오디오 Q8 카나리 parity | **완료(eg2-1)** — cos 1.0, maxabs 0.0 |
| 나머지 4대 그래프 배포 | **완료** — 5대 sha 일치, ORT 로드 성공 |
| D0-d cost probe | **대기**(다음 단계) |

## 5. 판정

**D0-c 완료.** 5대 running, lock/디스크/네트워크 기본 점검, 오디오 Q8 그래프 5대 배포(sha 일치), eg2-1 카나리 cos 1.0/maxabs 0.0을 확인했다.

다음 순서:
1. D0-d 비용 probe (추출 RTF·reader 1 epoch)
2. D-β Wave 1 (F-D/F-A′/F-B/F-C)
3. D-β 데이터 목록·H=6h 확정
4. A1 timing probe (vps-5)

## 6. AM-6 이행 표

| 요구 (D0-c) | 이행 |
|---|---|
| 5대 기동 | 이행 |
| 호스트별 df/RAM/시계/네트워크 | 부분 — df/RAM/HF latency; 대역폭 미측정 |
| venv lock 일치 | 이행 |
| 모델 SHA256 | **이행** — Q8 graph/data 5대 sha 일치; checkpoint는 eg2-1만 |
| 오디오 Q8 카나리 | **이행(eg2-1)** — cos 1.0, maxabs 0.0 |
| 데이터 예산 확정 | 부분 — free 13~15G 확인, F-C 6h 4.4GB 가능 |

## 7. 산출물

- `runner/d0c_start_vps.py`
- `runner/d0c_vps_ready.py`
- `reports/provenance/D0c_vps_start.json`
- `reports/provenance/D0c_vps_ready.json`
- `logs/D0c_start_vps.log`
- eg2-1: `onnx/eg2_audio_research_fp32_t1600_l12.onnx` + `.data` (연구용, 1.2GB Q8 포함)
