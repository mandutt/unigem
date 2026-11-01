# A3 — 수치 일치 검증 (텍스트, ONNX FP32 ↔ PyTorch FP32)

- 작성: 2026-11-02
- 대상 게이트: **G-A3** (층별 cosine ≥ 0.99, NaN 0, 패딩 불변)
- 호스트: `local`
- 스크립트: `eval/parity_text.py` (`--mode dump` → `--mode compare`, 메모리 절약 2단계)

## 1. 목적

재수출한 연구용 그래프가 PyTorch 원본과 수치적으로 같은지 확인한다. 여기서 어긋나면
이후 모든 헤드 실험(B1, C2, C3)의 입력이 오염된다.

## 2. 환경·입력

`reports/A0_env.md`와 동일. 비교 대상:

- ONNX: `onnx/eg2_text_research_fp32.onnx` (FP32, opset 21)
- PyTorch: `EmbeddingGemma2TextModel` FP32 + `TextGraph` 래퍼 (export에 쓴 것과 동일 코드)
- 토크나이저: HF `f9972ac2` `tokenizer.json`
- 입력 prefix: `task: search result | query: ` (문서 §5.1 접두사 규칙)

| 케이스 | 토큰 수 | 내용 |
|---|---|---|
| `short` | 11 | hello world |
| `mid` | 135 | 반복 문장 14회 |
| `long` | 549 | 반복 문장 60회 |
| `numeric` | 52 | 버전·날짜·경로·식별자 포함 |
| `korean` | 27 | 한국어 문장 |
| `padinv:*` | 11/135/27 | 3문장을 한 배치에 패딩해 넣고 단독 실행과 비교 |

## 3. 결과

`logs/A3_parity_text.jsonl`, `logs/A3_parity_text_summary.json`

| 항목 | 값 | 기준 | 판정 |
|---|---|---|---|
| 층별 cosine 최소 (6개 층 × 5케이스) | **0.999999999998** | ≥ 0.99 | PASS |
| `sentence_embedding` cosine 최소 | **0.999999999998** | ≥ 0.99 | PASS |
| 패딩 불변 cosine 최소 (batch vs 단독) | **0.999999999999** | ≥ 0.99 | PASS |
| 층별 max abs diff 최대 | 4.56e-4 | — | (FP32 누적 오차) |
| NaN | 0 | 0 | PASS |

## 4. 게이트 판정

**G-A3 (텍스트): PASS** — 층별 cosine ≥ 0.99, NaN 0, 패딩 불변 모두 충족.

## 5. 이상 징후

- max abs diff 4.6e-4는 hidden norm이 수백~수천 규모임을 감안하면 상대오차 ~1e-7 수준으로,
  FP32 누적 순서 차이로 설명된다. cosine은 1.0에 수렴.
- `long`(549토큰)도 단일 실행으로 통과 — 동적 시퀀스 축이 정상 동작.

## 6. 미해결

- 오디오 타워 parity (별도 보고서 `reports/A2_export_audio.md` / `reports/A3_parity_audio.md`).
- 언어 판정 회귀(G-A3L): 현재 운영 ONNX(q8-al4)와 신규 FP32/Q8의 pooled 출력을 기존 평가 입력으로 비교해야 한다.

## 7. 다음 단계

A4 Q8 양자화 + 성능 측정, G-A3L 회귀.
