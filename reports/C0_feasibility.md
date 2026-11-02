# C0 — 토크나이저·디코더 타당성 점검

- 작성: 2026-11-02
- 대상: Addendum A §A-8.1 (C0), plan v0.5 §9 C0
- 호스트: `local`
- 산출물: `logs/C0_tokenizer.json`

## 1. T5Gemma 2 접근 상태

- 대상: `google/t5gemma-2-270m-270m`
- HF API: `gated=manual`, `private=false`
- 현재 계정(`Roastedmandu`)은 **접근 승인 목록에 없음** → `tokenizer.json` 다운로드 403.
- **H4(토크나이저 동일 여부)의 최종 확인은 접근 승인 후에만 가능하다.** 사용자 HF 계정에서 해당 repo의 access request가 필요하다.

## 2. 대리 비교 (Gemma 3 토크나이저)

T5Gemma 2는 Gemma 3 기반이므로, 공개 미러 `unsloth/gemma-3-270m`의 토크나이저를 대리로 비교했다(명시적 proxy).

| 항목 | EG2 | Gemma 3 (proxy) |
|---|---|---|
| vocab | 262,144 | 262,145 |
| tokenizer.json SHA256 | `4d777ef5…` | `4667f208…` |
| 교집합 | 262,125 | |
| Jaccard | **0.9999** | |
| 토큰 문자열 분할 | 거의 동일 | |

- **ID 정렬은 불가능**: 같은 문자열인데 id가 다른 토큰이 **6,187개**(unused 슬롯 이동).
- Gemma 3에는 `<end_of_turn>`이 추가로 있고, EG2는 인코딩 시 `<eos>`를 자동 부착한다.
- 토큰 "문자열" 수준에서는 99.99% 일치하므로, 정렬이 필요하면 **문자열/임베딩 매핑**으로 해야 한다.

## 3. 결론 (잠정)

- **H4 기각(잠정)**: 토큰 id 1:1 정렬은 성립하지 않는다. A4(어댑터 사전학습 with id 정렬)는 전제가 무너진다.
- 문자열 기반 매핑은 가능하지만, EG2 hidden을 T5Gemma 디코더에 넣으려면 **임베딩 공간 정렬**이 별도 과제다.
- T5Gemma 2 실제 토크나이저 확인 전까지 이 결론은 "proxy 기준"으로 표기한다.

## 4. 디코더 분리 점검 (미완)

- T5Gemma 2 config를 받지 못해 decoder d_model/층수/LM head 크기는 **미확인**.
- 접근 승인 후 `config.json`으로 텐서 단위 파라미터 수·파일 크기를 계산한다.

## 5. 다음

1. 사용자: HF `google/t5gemma-2-270m-270m` access request.
2. 승인 후: tokenizer/config 재확인 → H4 최종 판정, C0 보고서 갱신.
