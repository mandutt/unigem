# G-C2a — Q8 ONNX 오디오 특징 호환성 (FLEURS ko 382)

- 작성: 2026-11-02
- 대상: Addendum B §B-11, 게이트 G-C2a
- 판정: **PASS** (CER 상대 변화 −0.12%, 기준 ≤ +10%)
- 산출물: `logs/C2_A1/gc2a_pred.jsonl`, `logs/C2_A1/gc2a_cer.json`, `runner/gc2a_patch.py`, `runner/gc2a_run.py`

## 1. 방법

Notesoop 추론 경로에서 **오디오 타워만** EG2 Q8 ONNX로 교체하고, 이후 단계(LM 24층 → final norm → `embedding_projection[:256]` → L2 → Conformer reader → greedy CTC)는 원본을 그대로 사용했다.

- ONNX 입력: Mel `[1,T,128]` + mask
- ONNX 출력: `audio_features [T,512]` (= audio tower + `output_proj` + `embed_audio` 결과)
- 패치: `extract_from_preprocessed`를 ONNX 버전으로 교체(`runner/gc2a_patch.py`)
- 데이터: FLEURS ko test **382클립**, chunk 16s/overlap 1s, greedy(KenLM 없음)
- 비교 기준: 동일 스크립트·동일 데이터의 원본 추출기 결과(`fleurs_cer.json`)

## 2. 특징 충실도 (처음 30클립)

| 지표 | 값 |
|---|---|
| 코사인 평균 | **0.999642** |
| 코사인 최소 | 0.989480 |

- 256d MRL 특징이 사실상 동일하다. Q8 양자화 오차가 최종 특징까지 전파되지 않는다.

## 3. CER 비교

| 조건 | CER | CER(공백 제거) | WER | RTF |
|---|---|---|---|---|
| 원본(FP32/bf16 오디오 타워) | 17.410% | 19.097% | 38.374% | 0.0838 |
| **Q8 ONNX 오디오 타워** | **17.388%** | 19.181% | 38.287% | 0.0927 |
| 상대 변화 | **−0.12%** | +0.44% | −0.23% | +10.6% |

- **G-C2a 판정: PASS** (상대 증가 −0.12% ≤ +10%).
- RTF는 10.6% 증가했으나 절대값 0.093으로 실시간 대비 약 10.8배다.

## 4. 해석

- Q8 ONNX 특징은 Notesoop 리더와 **호환된다**. C2-A3(특징 교체)로 인한 품질 리스크는 없다.
- 단, **G-C2(절대 CER ≤15%)는 여전히 FAIL**(17.41%)이다. G-C2a PASS는 "교체가 안전하다"는 상대 비교일 뿐, 제품 게이트를 통과시키지 않는다.
- G-C2 FAIL의 원인은 특징이 아니라 **디코더/언어모델**(KenLM 미적용 greedy)과 도메인 갭으로 보인다. 후속은 KenLM 또는 beam search 대체 디코더가 우선이다.

## 5. AM-6 이행 표

| 요구 (B-11 C2-A1/G-C2a) | 이행 |
|---|---|
| 동일 평가셋·동일 디코더 | 이행(382클립, greedy) |
| Q8 ONNX 특징 사용 | 이행 |
| CER 상대 증가 ≤10% | 이행(−0.12%) |
| 특징 충실도 보고 | 이행(cos 0.999642) |
| 반복 시드/CI | **미이행**(결정적 추론이라 시드 없음, CI 미산출) |
