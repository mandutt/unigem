# Phase A 실행 계획 (승인 요청)

- 작성: 2026-11-02
- 범위: Phase A (A0~A4) — EG2 ONNX 다중 출력화
- 선행 완료: A0 환경 고정, A1 현재 ONNX 점검 (read-only)
- 승인 후 착수: A2 재수출

## 1. Scope

| 포함 | 제외 |
|---|---|
| 원본 체크포인트에서 연구용(FP32)·운영용(Q8 대상) ONNX 재수출 | EG2 상위 층 파인튜닝, 원본 가중치 갱신 |
| 다층 hidden 노출(text: `[B,S,512]`, audio: `[T,512]`) + pooled `[B,768]` 동시 출력 | 비전 타워 export (C1 시점으로 연기) |
| 원본(PyTorch) ↔ ONNX 수치 일치, 패딩 불변성, batch 일치 | VPS 최종 판정 (성능 판정은 로컬만) |
| 언어 판정 회귀(G-A3L), Q8 양자화·성능 측정(A4) | F1~F6 기능 구현 (Phase B~D) |

## 2. DoD (게이트)

- **G-A1**: 한 세션에서 `sentence_embedding` + 선택 층 시퀀스 출력 확보 → PASS 조건.
- **G-A3**: 층별 cosine ≥ 0.99, NaN 0, 패딩 불변, batch 1/N 일치.
- **G-A3L**: 기존 판정기 argmax 일치율 ≥ 99%, 확신 오판 증가 0 (로컬).
- **G-A4**: Q8 vs FP32 층별 cosine ≥ 0.98, 언어 판정 일치율 ≥ 99% (로컬).
- 모든 수치는 `reports/A2_export.md`, `reports/A3_parity.md`, `reports/A4_q8_perf.md`에 원시 로그 경로와 함께 기록.
- 실패해도 FAIL로 기록하고 중단·보고 (임계값 사후 변경 금지).

## 3. Public API — ONNX 입출력 계약 (초안)

### 3.1 텍스트 백본 (연구용 FP32 / 운영용 Q8 동일 인터페이스)

입력
| 이름 | dtype | shape | 비고 |
|---|---|---|---|
| `input_ids` | int64 | `[B,S]` | 동적 B·S |
| `attention_mask` | int64 | `[B,S]` | **입력으로 받아 통과** (출력 아님) |
| `image_features` | float32 | `[N_i,512]` | 비전 미사용 시 `[0,512]` |
| `video_features` | float32 | `[N_v,512]` | 미사용 시 `[0,512]` |
| `audio_features` | float32 | `[N_a,512]` | 오디오 타워 soft token |

출력
| 이름 | dtype | shape | 노출 |
|---|---|---|---|
| `sentence_embedding` | float32 | `[B,768]` | 항상 (L2 정규화, 기존 소비자 호환) |
| `tok_h_l00` … `tok_h_l20` | float32 | `[B,S,512]` | 연구용: L={0,4,8,12,16,20}, **projection 이전** 백본 hidden |
| `tok_h_last` | float32 | `[B,S,512]` | 연구용: 마지막 층(projection 이전) |
| `tok_emb_768` | float32 | `[B,S,768]` | 연구용 선택: projection 이후(현행 `last_hidden_state`와 동일 지점) |

### 3.2 오디오 타워 (별도 그래프, 현재와 동일 분리 구조)

입력: `input_features` `[B,128,mel_frames]` float32, `input_features_mask` `[B,mel_frames]` int64
출력: `audio_features` `[T,512]` float32 (= `audio_soft_tokens`), 연구용으로 `aud_h_l00`…`aud_h_last` `[T,512]` 추가

> 현재 운영 그래프는 `audio_features`만 낸다(A1). 다층 오디오 hidden은 A2에서 추가한다.

### 3.3 규칙

- 동적 축: batch, sequence, time 모두 동적. 고정 shape 금지.
- 출력 이름은 위 표기를 고정하고, 층 집합은 export 시 설정값으로 바꾼다(이름은 유지).
- 계약은 `onnx/contracts/eg2_io_v1.json`에 기계 판독 형식으로 고정한다.

## 4. 구현 순서

| # | 작업 | 산출물 | 예상 |
|---|---|---|---|
| A2.1 | 체크포인트 provenance 고정 — 로컬 사본 config/tokenizer를 HF `google/embeddinggemma-2` revision과 해시 대조, revision 기록 | `env/snapshots/ckpt_*.json` | 20분 |
| A2.2 | 연구용 텍스트 그래프 export (FP32, L={0,4,8,12,16,20,last} + projected) | `onnx/eg2_text_research_fp32.onnx`, export 스크립트 | 2~3시간 |
| A2.3 | 연구용 오디오 타워 export (FP32, 다층 hidden + soft token) | `onnx/eg2_audio_research_fp32.onnx` | 1~2시간 |
| A2.4 | A3 수치 일치 — PyTorch(bf16/fp32) vs ONNX FP32, 층별 cosine·max abs·NaN·패딩 불변·batch 1/N | `reports/A3_parity.md` + JSONL | 1시간 |
| A2.5 | G-A3L 언어 판정 회귀 — 기존 평가 입력으로 pooled 출력 argmax 일치·margin 분포 비교 | `reports/A3_langid_regression.md` | 1시간 |
| A2.6 | 운영용 그래프 확정·Q8 동적 양자화 (초기 층 집합은 B2 전까지 L={0,4,8,12,16,20,last} 전체 노출) | `onnx/eg2_text_prod_q8.onnx` | 2시간 |
| A4 | Q8 성능: 파일 크기·로드·첫 추론·peak RAM·길이별 지연(텍스트 128/256/512, 오디오 5/15/30s)·스레드 6 vs 12 | `reports/A4_q8_perf.md` + CSV | 2시간 |

총 예상: **1~2 작업일** (로컬 실행, 실패 시 재수출 포함).

## 5. 리스크·완화

| 리스크 | 완화 |
|---|---|
| 로컬 RAM 15.6GB에서 bf16 1.49GB 모델 + export 그래프 메모리 | 텍스트/오디오 타워를 분리 export, 배치 1로 trace. OOM 시 vps-1 이관 |
| transformers 5.20.1이 EG2 export에 미검증 | export는 프로젝트 venv에 **버전 고정** 설치, 실패 시 5.19.x로 내림 (Notesoop 사례와 동일 계열) |
| 마스크 처리 오류(참고 사례의 eager attention 오디오 마스크 반전) | A3에서 원본 대비 수치 일치 필수, 기본 attention 사용 |
| `last_hidden_state` 768차원이 projection 이후임을 혼동 | 계약에 `tok_h_*`=512(projection 이전), `tok_emb_768`=768(이후)로 분리 |
| 기존 ONNX 소비자(`C:\code\eg2-langidentifier`) 회귀 | 신규 파일은 `C:\code\unigem\onnx\`에만 생성, 기존 경로 교체는 CP1 승인 후 |

## 6. 승인 안건

1. **A2 착수 승인** (OA-4) — 로컬에서 체크포인트 provenance 확인 + export.
2. **git 원격** (OA-2) — 로컬 전용 / GitHub 비공개.
3. **VPS 계정 B 확장 방식** (OA-1) — CP0에서 확정. Phase A는 로컬만으로 진행 가능하므로 지금 결정하지 않아도 됨.
