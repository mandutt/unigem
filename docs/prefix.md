# EG2 태스크 접두사 (공식 문자열)

- 작성: 2026-11-02
- 출처: 모델 카드 `google/embeddinggemma-2` (Hugging Face), "Best Practices → 1. Task Instruction Prefixes"
- 체크포인트: 로컬 `data/models/embeddinggemma-2-f9972ac2` (rev `f9972ac2e696a105c482202646979e33e4b5a1e`)
- 주의: HF API에서 해당 rev 조회는 404(삭제·이동 추정)였으나 로컬 파일은 보존되어 있다. 접두사 문자열은 모델 카드에서 확인했다.

## 접두사 표 (원문 그대로)

| 용도 | 유형 | Prompt Name | 질의 접두사 | 문서 접두사 |
|---|---|---|---|---|
| 웹/문서 검색 | 비대칭 | SearchQuery | `task: search result \| query: {query}` | `title: {title} \| text: {content}` |
| 질의응답 | 비대칭 | QuestionAnswering | `task: question answering \| query: {question}` | `title: {title} \| text: {passage}` |
| 사실 확인 | 비대칭 | FactChecking | `task: fact checking \| query: {claim}` | `title: {title} \| text: {evidence}` |
| 코드 검색 | 비대칭 | CodeRetrieval | `task: code retrieval \| query: {query}` | `title: {title or filename} \| text: {code}` |
| 텍스트 분류 | 대칭 | Classification | `task: classification \| query: {content}` | — |
| 클러스터링 | 대칭 | Clustering | `task: clustering \| query: {content}` | — |
| 유사도 | 대칭 | SentenceSimilarity | `task: sentence similarity \| query: {content}` | — |

- 제목이 없으면 문서는 `title: none`으로 시작한다(공식 표기: `title: none`).
- 접두사는 **텍스트에만** 적용한다. 이미지·비디오·오디오에는 붙이지 않는다.

## 이 프로젝트에서의 사용 원칙 (Addendum B §B-5)

| 용도 | 접두사 | 근거 |
|---|---|---|
| F4 맞춤법 전용 EG2 패스 | **없음(기본)** | 교정 대상은 문서 검색이 아님. 접두사가 AUPRC +2%p 이상 개선할 때만 채택 |
| F5 요약(원문 입력) | 없음 | 검색용 접두사는 생성 과제와 무관 |
| 저장 임베딩 재사용 | 저장 임베딩과 **동일 접두사**여야 함 | 불일치 시 hidden 분포가 달라짐 |

## 주의 (모델 카드)

- **float16 사용 금지**: activation 범위가 float16을 초과해 NaN/무음 열화가 발생한다. bf16 또는 fp32 사용. 우리 ONNX는 FP32/Q8이므로 해당 없음.
- 풀링: **mean pooling**, 출력 768d(512→768 projection), 컨텍스트 8,192, 슬라이딩 윈도 1,024.
