# 결정 로그 (append-only)

기준 문서: `docs/plan_v0_5.md` (v0.5, 2026-11-01). 문서의 `eg2-lab/`은 이 저장소 루트를 뜻한다.

| ID | 날짜 | 결정 | 근거·비고 |
|---|---|---|---|
| D-001 | 2026-11-02 | 프로젝트 루트 = `C:\code\unigem`, git 저장소로 관리 | 사용자 지시(경로 정정: unige → unigem). 문서 §14의 `eg2-lab/` 경로를 이 루트로 매핑 |
| D-002 | 2026-11-02 | 기존 운영 자산(`C:\code\eg2-langidentifier`, `%LOCALAPPDATA%\jev-mem`)은 **읽기 전용 참조**만. 프로젝트 venv는 `.venv`(Python 3.12)로 분리 | 문서 §0-3, §9 A0 |
| D-003 | 2026-11-02 | Phase A0·A1을 read-only로 선행 수행 (코드 산출 없음, 측정·기록만) | 문서 §9 A0·A1. A1 결과 G-A1 FAIL 확인 → A2 필요 |
| D-004 | 2026-11-02 | VPS는 **계정 B**를 사용하며, **4대를 추가 생성해 5대 구성** (eq-2 ~ eq-5) | 사용자 승인(2026-11-02). 계정 B 기존 `eg2-1` + 신규 4대 = 5대, 전부 4 vCPU / 8 GiB / 20 GiB 목표 |
| D-005 | 2026-11-02 | A2 export의 1차 실행 호스트는 **로컬 PC** (VPS 전송 비용 회피, RAM 부족/OOM 시에만 vps-1로 이관) | 문서 §9 A2는 vps-1 우선이나 "RAM 부족 시 로컬" 허용. 로컬에 체크포인트 사본이 있어 역방향이 더 저렴 |
| D-006 | 2026-11-02 | A2의 원본 체크포인트는 **HF `google/embeddinggemma-2` revision `f9972ac2…5a1e`를 새로 다운로드**해 쓴다. 로컬 사본은 파생본(바이트 불일치)이므로 export 원본으로 쓰지 않는다 | provenance 실측: tokenizer 해시 일치, config는 `transformers_version`만 다름, `model.safetensors`는 같은 크기·다른 SHA256(재저장본 추정) |
| D-007 | 2026-11-02 | 다운로드한 체크포인트의 `model.safetensors` SHA256이 HF blob `197a3296…53d79`와 **일치**함을 확인. 이후 이 사본을 export 원본으로 고정 | `data/models/embeddinggemma-2-f9972ac2/` (git 미추적) |
| D-008 | 2026-11-02 | ~~오디오 타워 export는 dynamo exporter만 동작한다~~ → **D-010에서 정정**: dynamo도 dynamic_axes로는 실패하며, 정적 shape에서만 동작 | 오디오 forward가 커스텀 autograd 연산을 사용. 텍스트는 dynamo로 성공 |
| D-009 | 2026-11-02 | 오디오 다층 hidden은 **재수출 대신 기존 q8 그래프에 중간 텐서를 출력으로 추가**해 확보한다 (`eg2_audio_q8_layers.onnx`). 원본 불변, 파생 사본만 수정 | dynamo export가 로컬·VPS(8GiB) 모두 14~17분+ 무출력. 그래프 수술 결과 PyTorch 대비 cos 0.99945~0.999998, 패딩 불변 1.0. FP32 오디오 그래프는 미확보 |
| D-010 | 2026-11-02 | 오디오 **FP32 연구용 그래프**는 `dynamo + 정적 shape(--static) + optimize=False`로 export한다. legacy는 `unfold` 미지원으로 사용하지 않는다 | 원인 4중 규명: ① legacy `autograd_inlining=False` 필요 ② `F.pad(value=None)`이 None 상수로 굳음 ③ legacy `Tensor.unfold` input size 미추적 ④ dynamo+`dynamic_axes` symbolic 제약 정체. 해결 후 cos 1.0, NaN 0 (`reports/A2_export_audio_research.md`) |
| D-011 | 2026-11-02 | **CP1 D1=A 승인**: G-A3L FAIL은 그대로 기록하고, id↔ms 1건만 "비확신 모호 구간" 예외로 승인. 게이트 임계값 불변 | 사용자 승인. 불일치 margin 0.0094/0.0068, 확신 오판 0. Q8에서는 44/44 |
| D-012 | 2026-11-02 | **CP1 D3 승인**: 상주 EG2는 **텍스트+오디오 한 세션**, Q8(q8-al4), 스레드 6, 연구용 전체 층 노출(운영 층 축소는 B2 이후) | 사용자 승인. 비전 타워는 C1에서 추가, RAM 상한은 G-D에 따라 측정만 |
| D-013 | 2026-11-02 | **CP1 D5=A 승인**: 오디오 연구용 FP32 그래프는 500/1600/3000 mel 3종. 런타임은 가장 가까운 긴 그래프에 zero-pad + mask | 사용자 승인. 그래프당 1.22GB, 디스크 여유 109GB |
| D-014 | 2026-11-02 | **CP1 D6=A 승인**: t1600에 대해 **12층 전체** export (`--layers 0..11`) | 사용자 승인. C2-B 층 조합 스윕 즉시 수행 가능 |
| D-015 | 2026-11-02 | **CP1 D7 승인**: G-A3S(Notesoop 특징 재현), G-C2a(Q8 특징 CER 상대 증가 ≤10%)를 **게이트로 승인** | 사용자 승인. 사전등록 원칙 유지 — 결과 확인 전 임계값 고정 |
| D-016 | 2026-11-02 | **Phase V 실행 완료 (G-V0 PASS)**: 5대 네이티브 venv, lock 단일(`6cccf5e9…`), 정합 cos 1.0, 가드 4종(메모리·타임아웃·디스크·P1) 실측 | `reports/V0_hosts.md`, `V1_env.md`, `V2_runner.md`. 러너 `runner/run_job.py` |

## 미결 안건 (사용자 승인 필요)

| ID | 안건 | 선택지 | 필요 시점 |
|---|---|---|---|
| OA-1 | VPS 규모·계정 | **확정: 계정 B에 머신 4대 추가 생성 (5대 구성)** | 2026-11-02 승인 완료 |
| OA-2 | git 원격 | **확정: GitHub 비공개 `mandutt/unigem`** (2026-11-02) | 사용자 지시 |
| OA-3 | G-A3S(Notesoop 특징 재현), G-C2a(호환성) 게이트 승인 | **확정: 게이트로 승인 (2026-11-02, D-015)** | C2-A 착수 전 |
| OA-4 | A2 export 실행 승인 | **확정: 승인 (2026-11-02)** — 로컬 텍스트 export + 오디오 그래프 수술 | 완료 |

## 참고: 로컬 자산 실측 메모

- `run-20261024-embedgemma2ko/model-src/`에 HF 체크포인트 사본 존재: `model.safetensors` 1,488,915,288 B (bf16), `config.json`, `tokenizer.json`(32,170,510 B).
- 이 사본의 **HF revision/provenance는 아직 미확인** — A2에서 `google/embeddinggemma-2` config·tokenizer 해시와 대조해 고정한다.
- `config.json`의 `text_config.max_position_embeddings = 262144`는 문서 §5.1의 "컨텍스트 8192"와 불일치. 실제 유효 컨텍스트는 A2에서 확인·기록한다(문서 수치를 사실로 가정하지 않는다).
