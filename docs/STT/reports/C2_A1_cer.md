# C2-A1 — Notesoop-STT-Ko-v1 기준선 CER

- 작성: 2026-11-02
- 대상: Addendum B §B-11 C2-A1
- 실행: 로컬, `.venv-c2a1`(torch 2.9.1 CPU), Notesoop `030e4720`, **greedy CTC(KenLM 비활성)**
- 산출물: `logs/C2_A1/pred.jsonl`(557), `logs/C2_A1/cer.json`, `runner/c2a1_prepare.py`, `runner/c2a1_run.py`

## 1. 데이터

| 소스 | 클립 | 시간 | 비고 |
|---|---|---|---|
| Zeroth test | 457 | 1.19h | 낭독체, 16kHz FLAC→WAV |
| KsponSpeech eval_clean | 100 (균등 표본) | 0.08h | 자유발화, PCM(EUC-KR 전사는 UTF-8) |
| **합계** | **557** | **1.27h** | |

- Kspon PCM은 **후행 1바이트 패딩**(모든 파일 홀수 바이트)이라 1바이트 절단 후 16-bit 해석.
- 전사 정규화: Notesoop `normalize_text`.

## 2. 결과

| 소스 | n | **CER** | CER(공백 제거) | WER | RTF |
|---|---|---|---|---|---|
| Zeroth | 457 | **17.32%** | 17.92% | 47.16% | 0.102 |
| Kspon eval_clean | 100 | **27.81%** | 27.70% | 47.03% | 0.527 |
| **전체** | **557** | **18.15%** | **18.66%** | **47.15%** | **0.178** |

- RTF 0.178 = 실시간 대비 약 5.6배(CPU). Kspon은 클립이 짧아 16초 청크 패딩 비용으로 RTF가 높다.
- KenLM 비활성 상태의 **greedy CTC** 결과다. 모델 카드의 KenLM 빔서치는 Windows에서 `kenlm` 빌드가 필요해 이번 측정에서 제외했다.

## 3. 오류 유형(표본)

- 수사·단위: `삼 월`→`3월`/`회 3월`, `전 장관`→`김 장관`
- 고유명사: `홍익대`→`홍대`, `자문단장`→`자문문단`
- 어미·철자: `위촉`→`미치`, `공모와`→`공모모와`, `즐길`→`즐길길`
- 띄어쓰기 오류가 CER(공백 포함)과 WER에 크게 기여

## 4. 해석과 한계

1. **G-C2 기준(FLEURS ko greedy CER ≤15%)과 직접 비교 불가** — 이번 데이터는 Zeroth/Kspon이다. FLEURS ko 평가는 별도 실행이 필요하다.
2. KenLM 미적용으로 **상한(보수적) 추정**이다. 모델 카드의 빔서치 대비 1~3%p 개선 여지가 있다.
3. Kspon 표본 100클립(0.08h)은 작다. 300클립 이상으로 확대하려면 추가 실행이 필요하다.
4. C2-A1의 목적은 **절대 CER 최적화가 아니라 이후 비교의 기준선**이다. G-C2a(Q8 ONNX 특징으로 교체 시 상대 증가 ≤10%)의 분모가 된다.

## 5. G-C2 — FLEURS ko test

- 데이터: `fleurs_cache/ko_kr_test.tar.gz` 382클립(전사 382), 16kHz
- 실행: 동일 Notesoop greedy(KenLM 없음), chunk 16s/overlap 1s
- 결과:

| n | **CER** | CER(공백 제거) | WER | RTF |
|---|---|---|---|---|
| 382 | **17.41%** | 19.10% | 38.37% | 0.084 |

- **G-C2 판정: FAIL** (기준 greedy CER ≤15%, 실측 17.41%).
- RTF 0.084(실시간 대비 약 12배).

### 5.1 KenLM 빔서치 비교 (Windows 빌드 성공)

| 디코더 | CER | WER | RTF |
|---|---|---|---|
| greedy | **17.410%** | 38.374% | 0.084 |
| KenLM 기본(α0.12/β0.40) | 17.618% | 39.654% | 0.107 |
| KenLM 튜닝(α0.5/β1.0) | 17.445% | 38.201% | 0.117 |

- 80클립 부분집합에서는 튜닝이 greedy보다 0.43%p 좋았으나(18.24 vs 18.67), **전체 382클립에서는 17.445 vs 17.410로 +0.035%p** — 잡음 수준.
- 결론: **KenLM 미채택.** 지연 +39%에 비해 CER 이득이 없다. G-C2는 여전히 FAIL이며, 원인은 디코더가 아니라 모델/도메인 갭으로 본다.

## 6. 다음

- G-C2a: 동일 FLEURS 382클립에서 EG2 Q8 ONNX 특징으로 교체 후 CER 상대 증가 측정
  - 선행 조건: ONNX 파이프라인이 Notesoop의 256d MRL 특징(`LM norm → embedding_projection[:256] → L2`)을 재현해야 함. 현재 `eg2_audio_q8_layers.onnx`는 512d soft token까지만 노출하므로 **추가 export 또는 어댑터**가 필요하다.
- KenLM: Windows 빌드 가능 여부 확인(불가 시 beam search 대체 디코더 검토)

## 7. AM-6 이행 표

| 요구 (B-11 C2-A1) | 이행 |
|---|---|
| Zeroth test 457발화 | 이행 |
| Kspon eval 표본 ≥20 | 이행(100) |
| CER·RTF 보고 | 이행 |
| 문장 단위 부트스트랩 CI | **미이행** |
| FLEURS ko ≥300발화 | **미이행** |
| KenLM 포함 | **미이행**(빌드 제약) |
