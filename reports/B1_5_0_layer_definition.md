# B1.5-0 — 층 정의 확인

- 작성: 2026-11-02
- 대상: Addendum A §A-3.2 (F-1 대응)
- 호스트: `local`
- 산출물: `logs/B1_5_0/torch.npz`, `onnx.npz`, `train/b1_5_0_layer_def.py`

## 1. 질문

B1의 `tok_h_l00`은 순수 임베딩 출력인가, 첫 블록 출력인가?
순수 임베딩이라면 G-B1의 l00 통과는 "토크나이저가 결정적"이라는 것만 보여준다.

## 2. 방법

- 동일 문장 3개(ko/en, 식별자 포함)를 PyTorch(bf16)와 ONNX(FP32)로 각각 실행
- PyTorch: `embed_tokens` 출력 + 각 decoder layer 출력을 hook으로 캡처
- 비교: ONNX `tok_h_l00/l04` vs PyTorch `embed_tokens` 및 layer 0/4 출력의 cosine

## 3. 결과

| 비교 | 문장 1 | 문장 2 | 문장 3 |
|---|---|---|---|
| `tok_h_l00` vs **embed_tokens** | 0.3923 | 0.4197 | 0.3959 |
| `tok_h_l00` vs **layer 0 출력** | **0.99998** | **0.99998** | **0.99998** |
| `tok_h_l04` vs **layer 4 출력** | 0.99995 | 0.99995 | 0.99994 |

- ONNX `tok_h_l00`은 **임베딩이 아니라 decoder layer 0의 출력**이다(HF `hidden_states[1]`에 해당).
- `tok_h_last`는 final RMSNorm 출력으로, 어떤 raw layer와도 cosine이 낮다(0.07~0.10). RMSNorm의 학습된 가중치가 방향을 바꾸기 때문이다.

## 4. 모델 사실 확인 (HF 모델 카드)

| 항목 | 값 |
|---|---|
| 레이어 | **24** |
| Model dimension | 512 |
| Hidden dimension | 2048 |
| 어휘 | 262,144 |
| 컨텍스트 | 8,192 |
| 풀링 | mean |

- B1의 층 집합 `{0,4,8,12,16,20,last}`는 24층 중 얕은/중간/깊은 층을 고르게 포함한다.
- B1.5-0 검증 스크립트의 "best match" 탐색은 0~11층만 비교했으므로, 12층 이상 매핑은 `tok_h_last` 정의(모델 코드)로 확인했다.

## 5. 입력 형식

- tokenizer post-processor가 `<bos>` + 문장 + `<eos>`를 자동 추가한다.
- **B1은 태스크 접두사를 쓰지 않았다.** 모델 카드의 접두사 문자열은 다음과 같다(확인).
  - SearchQuery: `task: search result | query: {query}`
  - Document: `title: {title} | text: {content}` (`title: none` 허용)
  - QuestionAnswering: `task: question answering | query: {question}`
  - Classification: `task: classification | query: {content}`
- 접두사 유무·종류의 영향은 B1.5-6에서 측정한다.

## 6. 해석

- F-1은 **부분 해소**됐다. l00은 순수 임베딩이 아니라 1개 블록을 통과한 표현이므로, B1의 l00 99.57%는 "룩업의 역함수"가 아니라 실제 표면 정보 보존 결과다.
- 다만 24층 중 1층이므로 **얕은 층**이라는 한계는 그대로다. F4/F5에 쓸지는 B1.5-3(문맥 가치)의 몫이다.
- G-B1 표기는 "l00 형식 충족, 의도 미확인 → G-B1.5"에서 **"l00 = layer0 출력 확인, 의도는 B1.5에서 검증"**으로 갱신한다.
