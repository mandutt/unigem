# 결정 로그 (append-only)

기준 문서: `docs/plan_v0_5.md` (v0.5, 2026-11-01). 문서의 `eg2-lab/`은 이 저장소 루트를 뜻한다.

| ID | 날짜 | 결정 | 근거·비고 |
|---|---|---|---|
| D-001 | 2026-11-02 | 프로젝트 루트 = `C:\code\unige`, git 저장소로 관리 | 사용자 지시. 문서 §14의 `eg2-lab/` 경로를 이 루트로 매핑 |
| D-002 | 2026-11-02 | 기존 운영 자산(`C:\code\eg2-langidentifier`, `%LOCALAPPDATA%\jev-mem`)은 **읽기 전용 참조**만. 프로젝트 venv는 `.venv`(Python 3.12)로 분리 | 문서 §0-3, §9 A0 |
| D-003 | 2026-11-02 | Phase A0·A1을 read-only로 선행 수행 (코드 산출 없음, 측정·기록만) | 문서 §9 A0·A1. A1 결과 G-A1 FAIL 확인 → A2 필요 |
| D-004 | 2026-11-02 | VPS는 **계정 B**를 사용한다 (`~/.instabox-b.env`, API `api.instabox.sh`) | 사용자 지시. 계정 B 현재 머신은 `eg2-1` 1대뿐 — 확장 방식은 CP0 안건 |
| D-005 | 2026-11-02 | A2 export의 1차 실행 호스트는 **로컬 PC** (bf16 체크포인트 사본이 이미 로컬에 존재, VPS 전송 비용 회피). RAM 부족/OOM 시에만 vps-1로 이관 | 문서 §9 A2는 vps-1 우선이나 "RAM 부족 시 로컬" 허용. 로컬에 원본 사본이 있어 역방향이 더 저렴 |

## 미결 안건 (사용자 승인 필요)

| ID | 안건 | 선택지 | 필요 시점 |
|---|---|---|---|
| OA-1 | VPS 규모·계정 | (a) 계정 B에 머신 4대 추가 생성 (비용·쿼터 확인 필요) (b) 계정 B 1대 + 계정 A 4대 혼용 (c) 계정 B 1대로 축소 운영 | CP0 (Phase V 착수 전) |
| OA-2 | git 원격 | (a) 로컬 전용 (b) GitHub 비공개 리포 생성 후 push | A2 착수 전 |
| OA-3 | G-A3S(Notesoop 특징 재현), G-C2a(호환성) 게이트 승인 | 승인 / 측정·보고만 | C2-A 착수 전 |
| OA-4 | A2 export 실행 승인 | 승인 / 보류 | 즉시 |

## 참고: 로컬 자산 실측 메모

- `run-20261024-embedgemma2ko/model-src/`에 HF 체크포인트 사본 존재: `model.safetensors` 1,488,915,288 B (bf16), `config.json`, `tokenizer.json`(32,170,510 B).
- 이 사본의 **HF revision/provenance는 아직 미확인** — A2에서 `google/embeddinggemma-2` config·tokenizer 해시와 대조해 고정한다.
- `config.json`의 `text_config.max_position_embeddings = 262144`는 문서 §5.1의 "컨텍스트 8192"와 불일치. 실제 유효 컨텍스트는 A2에서 확인·기록한다(문서 수치를 사실로 가정하지 않는다).
