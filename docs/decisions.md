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

## 미결 안건 (사용자 승인 필요)

| ID | 안건 | 선택지 | 필요 시점 |
|---|---|---|---|
| OA-1 | VPS 규모·계정 | **확정: 계정 B에 머신 4대 추가 생성 (5대 구성)** | 2026-11-02 승인 완료 |
| OA-2 | git 원격 | (a) 로컬 전용 (b) GitHub 비공개 리포 생성 후 push | A2 착수 전 |
| OA-3 | G-A3S(Notesoop 특징 재현), G-C2a(호환성) 게이트 승인 | 승인 / 측정·보고만 | C2-A 착수 전 |
| OA-4 | A2 export 실행 승인 | 승인 / 보류 | 즉시 |

## 참고: 로컬 자산 실측 메모

- `run-20261024-embedgemma2ko/model-src/`에 HF 체크포인트 사본 존재: `model.safetensors` 1,488,915,288 B (bf16), `config.json`, `tokenizer.json`(32,170,510 B).
- 이 사본의 **HF revision/provenance는 아직 미확인** — A2에서 `google/embeddinggemma-2` config·tokenizer 해시와 대조해 고정한다.
- `config.json`의 `text_config.max_position_embeddings = 262144`는 문서 §5.1의 "컨텍스트 8192"와 불일치. 실제 유효 컨텍스트는 A2에서 확인·기록한다(문서 수치를 사실로 가정하지 않는다).
