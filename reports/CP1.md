# CP1 — Phase A 종료 체크포인트

- 작성: 2026-11-02
- 상태: **사용자 결정 대기** (다음 Phase 자동 진행 금지, 문서 §0-10)
- 대상: Phase A (EG2 ONNX 다중 출력화)

## 1. Phase A 결과 요약

| 단계 | 게이트 | 판정 | 핵심 수치 | 보고서 |
|---|---|---|---|---|
| A0 환경 | — | 완료 | venv 분리(3.12), lock `001c498f…` | `A0_env.md` |
| A1 현재 ONNX | G-A1 | 기존 그래프 FAIL | 텍스트 단일층(768)·오디오 단일 출력 | `A1_onnx_io.md` |
| A2 텍스트 재수출 | G-A1 | **PASS** | 9개 출력(768 pooled + 6층/최종 512 + projected) | `A2_export_text.md` |
| A2 오디오 재수출 | G-A1 | **INCONCLUSIVE** | legacy 실패, dynamo 14분+ 무출력 → 재시도 중 | `A2_export_audio.md` |
| A3 텍스트 parity | G-A3 | **PASS** | 층별 cos 0.999999999998, NaN 0, 패딩 불변 | `A3_parity_text.md` |
| A3L 언어 판정 | G-A3L | **FAIL** | 43/44 = 97.7%, 불일치 1건 id↔ms margin<0.01, 확신 오판 0 | `A3L_langid.md` |
| A4 Q8 | G-A4 | **PASS** | 층별 cos 0.9977, LID 44/44, 512tok 540ms(t6), RSS 178MiB | `A4_q8_perf.md` |

## 2. 확보한 산출물 (로컬, git 미추적)

| 파일 | 크기 | SHA256 (기록 위치) |
|---|---|---|
| `onnx/eg2_text_research_fp32.onnx(+.data)` | 5.3MB + 1.084GB | `onnx/*.meta.json` |
| `onnx/eg2_text_prod_q8.onnx(+_data)` | 4.9MB + 679MB | `onnx/*.meta.json` |
| `data/models/embeddinggemma-2-f9972ac2/` | 1.49GB | HF blob과 일치 |
| `logs/A3_*`, `logs/A4_*` | 수 MB | 원시 측정 |

## 3. 판정 해석

- **텍스트 경로는 Phase A를 통과했다.** FP32는 PyTorch와 사실상 동일(cos≈1), Q8은 G-A4 기준을 여유 있게 충족.
- **G-A3L FAIL은 실질 회귀가 아니라 게이트 정의 문제다.** 유일한 불일치는 id↔ms 초근접 경합(margin 0.0094 vs 0.0068)이며,
  기존 판정기가 ms로 틀린 클립을 신규 FP32가 id로 맞혔다. Q8에서는 다시 ms로 돌아와 44/44 일치.
  즉 두 그래프의 차이는 양자화 잡음 수준이고, “확신 오판 증가 0”은 충족한다.
- **오디오 다층 hidden은 아직 없다.** 텍스트 헤드(B1, F4)는 바로 진행 가능하지만, C2(STT reader)는 오디오 층 hidden이 필요하다.

## 4. CP1 결정 요청

### D1. G-A3L 처리 (필수)

| 안 | 내용 | 영향 |
|---|---|---|
| **A (권장)** | FAIL을 그대로 기록하고, id↔ms 1건을 “언어적 모호 구간의 비확신 불일치”로 예외 승인 | Phase A 종료 가능. 임계값 불변 |
| B | 게이트를 그룹 기준(id/ms 묶음)으로 재정의 | 사전등록 변경 — 사유 기록 필요 |
| C | 44 → 220클립으로 확대 재측정 | 판정은 정확해지나 시간 소요 |

### D2. 오디오 다층 export 경로 (필수)

| 안 | 내용 |
|---|---|
| **A (권장, 사용자 제안 반영)** | VPS(`eg2-1`, 8GiB)에서 export → **Notion 별도 프로젝트 페이지 하위에 업로드** → 로컬로 회수·검증 |
| B | 로컬에서 재시도 (현재 백그라운드 진행 중, 최대 30분 관찰) |
| C | 기존 q8 오디오 그래프에 중간 텐서를 출력으로 추가 (재export 없음, FP32 불가) |
| D | C2 착수 시점으로 연기 (Phase A는 텍스트만으로 종료) |

> Notion 경로를 쓰면 1~2GB ONNX도 회수 가능하다. 프로젝트 페이지命名은 `unigem` 하위 `artifacts/onnx/`를 제안.

### D3. 상주 EG2 구성 확정 (CP1 본래 안건)

현재 측정으로 확정 가능한 범위:
- 타워: **텍스트 + 오디오** (비전은 C1 시점 추가)
- 출력 층: 텍스트 `{0,4,8,12,16,20,last}` 전부 노출(연구용), 운영은 B2 결과 후 축소
- dtype: **Q8 (q8-al4)** — G-A4 통과
- 스레드: **6** (12는 SMT 경합으로 역효과)

미확정: 상주 RAM 상한은 G-D에 따라 정하지 않고 측정만 한다.

### D4. G-A3S / G-C2a 승인 (C2 선행)

- G-A3S: Notesoop 특징 재현(ONNX FP32 ≥0.99, Q8 ≥0.98) — 측정·보고만 할지, 게이트로 승인할지.
- G-C2a: Q8 특징 사용 시 CER 상대 증가 ≤10% — 승인 여부.

## 5. 다음 단계(승인 후)

1. (D2-A) VPS 오디오 export → Notion 업로드 → 로컬 parity.
2. Phase V(G-V0): 5대 VPS 환경 구성·정합·캘리브레이션. (VPS는 이미 5대 생성 완료)
3. Phase B1: 텍스트 토큰 복원 프로빙 (VPS 병렬 가능).

## 6. 참고: 환경·비용 메모

- VPS 계정 B: `eg2-1`~`eg2-5`, 4 vCPU/8GiB/20GiB, free tier(실측 5대 생성 가능), `maxRunMinutes` 480 고정.
- 로컬 RAM 압박: 상시 여유 2~3GiB. 장시간·대용량 작업은 VPS 우선이 맞다.
