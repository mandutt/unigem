# unigem — EG2 상주 인코더 다용도 활용 프로젝트

EmbeddingGemma 2(EG2)를 메모리 시스템 상주 인코더로 재사용하고, 그 위에 작업별 경량 헤드를 얹어
언어 판정·STT·비전 태깅·맞춤법 교정·메모리 요약을 **실측으로 검증**하는 프로젝트입니다.

- **기준 문서:** [`docs/plan_v0_5.md`](docs/plan_v0_5.md) — `EG2_ResidentEncoder_MeasurementPlan_v0_5.md` (SHA256 `746c3c01…8d4d430`, 640줄)
- **문서상 작업 디렉터리 `eg2-lab/` = 이 저장소 루트(`C:\code\unigem`)**
- **상태:** Phase A 완료 (텍스트·오디오 다층 확보, 오디오 FP32 연구용 그래프 export 성공) → **CP1 결정 대기** (`reports/CP1.md`)
- **목표 하드웨어:** 로컬 PC (Windows 11, Ryzen 5 7600 6C/12T, 15.6 GiB, GPU 없음, ONNX Runtime CPU EP, Q8)
- **VPS:** P0 데이터 전용, 성능 판정 불가. **계정 B 5대 구성 완료** (`eg2-1`~`eg2-5`, 4 vCPU/8 GiB/20 GiB) — `env/snapshots/instabox_account_b_2026-11-02.json`

## 지금까지의 실측 (요약)

| 단계 | 결과 | 보고서 |
|---|---|---|
| A0 환경 고정 | 프로젝트 venv(3.12) 구성, 운영 자산 버전 스냅샷 | [`reports/A0_env.md`](reports/A0_env.md) |
| A1 현재 ONNX 점검 | 텍스트: `last_hidden_state[B,S,768]` + `sentence_embedding[B,768]` / 오디오: `audio_features[T,512]` 단일 출력 | [`reports/A1_onnx_io.md`](reports/A1_onnx_io.md) |
| G-A1 | **PASS** — 텍스트 9출력 + 오디오 12층(q8 그래프 수술, cos 0.9995+) + 오디오 FP32 연구용(t500·t1600, cos 1.0) | [`reports/A2_export_text.md`](reports/A2_export_text.md) · [`reports/A2_export_audio.md`](reports/A2_export_audio.md) · [`reports/A2_export_audio_research.md`](reports/A2_export_audio_research.md) |
| A3 parity | **PASS** — 층별 cos `0.999999999998`, NaN 0, 패딩 불변 | [`reports/A3_parity_text.md`](reports/A3_parity_text.md) |
| G-A3L | **FAIL** — 43/44 (97.7%), 불일치 1건은 id↔ms margin<0.01, 확신 오판 0 | [`reports/A3L_langid.md`](reports/A3L_langid.md) |
| A4 Q8 | **PASS** — 층별 cos 0.9977, LID 44/44, 512tok 540ms(t6), RSS 178MiB | [`reports/A4_q8_perf.md`](reports/A4_q8_perf.md) |
| **CP1** | **결정 대기** — G-A3L 예외·오디오 export 경로·상주 구성 | [`reports/CP1.md`](reports/CP1.md) |

## 저장소 구조

```
unigem/
  docs/        plan_v0_5.md(불변 기준 문서) · decisions.md(결정 로그) · gates.md(게이트 표) · phase_a_plan.md
  env/         환경 정의·lock·호스트 스냅샷
  jobs/        job manifest (data_class 필수, 시크릿 금지)
  onnx/        export 스크립트·계약 JSON (가중치 파일은 git 미추적)
  data/        데이터 목록·해시·출처 (P1은 로컬 전용, git 미추적)
  cache/       은닉 표현 캐시 (호스트 로컬, git 미추적)
  train/ eval/ runner/   학습·평가·manifest 러너
  reports/     단계별 보고서 (A0…D4, CP)
  logs/        원시 측정 로그 (CSV/JSONL, 호스트 ID 포함)
```

## 불변 규칙 (문서 §0 요약)

1. 실측 우선 — 측정 로그 없는 "된다/안 된다" 결론 금지.
2. 게이트 임계값은 사전등록됨(`docs/gates.md`). 사후 변경 금지, 변경 시 사유 기록 + 사용자 승인.
3. **기존 운영 자산은 읽기 전용** — `C:\code\eg2-langidentifier`, jev-mem, Hermes 코어 수정 금지.
4. 성능 게이트 판정은 **로컬 PC만**. VPS 수치는 `참고(VPS)`.
5. hang/OOM/타임아웃은 1회 원인 기록 후 중단·보고. 우회는 승인 후.
6. 데이터: 공개(P0) 우선 → 격차 분석 → 격차분만 LLM API 합성(G-DATA 승인 후). 추론 경로에서 외부 LLM 호출 금지.
7. **P1(개인 데이터)은 로컬 PC 밖 반출 금지** — VPS·외부 API 전송 금지.
8. 원본 가중치 불변 — 헤드·어댑터·LoRA·pruning/양자화 사본·ONNX export만 허용.
9. 시크릿 하드코딩 금지 — 환경변수/자격증명 저장소만.
10. CP0~CP4에서 멈추고 사용자 결정을 기다린다. 자동 진행 금지.

## 실행 환경

```bash
# 프로젝트 venv (운영 venv와 분리)
C:\code\unigem\.venv\Scripts\python.exe

# 기존 운영 자산 (읽기 전용 참조)
%LOCALAPPDATA%\jev-mem\venv\Scripts\python.exe
C:\code\eg2-langidentifier\scripts\mmal4\            # 현재 운영 ONNX (q8-al4)
%LOCALAPPDATA%\jev-mem\bench\run-20261024-embedgemma2ko\model-src\   # HF 체크포인트 사본(bf16, 1.49GB)
```

## 다음 단계

`docs/phase_a_plan.md`의 A2(재수출) 승인 후 진행합니다. 승인 안건은 README가 아니라 결정 로그
[`docs/decisions.md`](docs/decisions.md)에 기록합니다.
