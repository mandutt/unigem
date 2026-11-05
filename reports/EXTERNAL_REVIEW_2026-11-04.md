# EG2 상주 인코더 — 4차 외부 검토 요청서

- 작성일: 2026-11-04
- 직전 검토: `reports/EXTERNAL_REVIEW_2026-11-03.md` (3차, 2026-11-03, 기준 커밋 `7d842e7`)
- 분석 기준 커밋: `cba80c0` (D-β reader 수정), `940271e` (W1 원시 로그·decode provenance)
- 정정 커밋: `174893b` (D-063, D-β 평가 정규화 정정), `1a80e12` (decode/eval 코드 수정, 표기 정정)
- 저장소: `github.com/mandutt/unigem` (private), branch `main`
- 용도: Hoplite를 통해 **3개 모델에 동일하게 전달하는 독립 검토 요청서**
- 문서 성격: **자가완결적 검토 요청서.** Hoplite 검토자는 GitHub 저장소에 접근할 수 있지만, 프로젝트 이력을 처음부터 읽지 않아도 이 문서만으로 판단할 수 있어야 한다. 저장소는 아래에 적은 파일의 실제 내용을 확인하는 용도로만 쓰면 된다.
- **이 문서는 승인 문서가 아니다.** 문서를 전달하거나 검토자가 답했다는 사실은 어떤 실험·설계·지출의 승인으로도 해석하지 않는다. 승인은 사용자만 한다.

---

## 0. 한눈에 보는 현재 상태

1. **CP-C1은 확정됐다(D-057).** F2(STT)의 **제품 경로는 기존 komixv2/whisper**이고, EG2 오디오 타워 위에 reader를 학습하는 **D는 연구 트랙**이다. D가 15%를 통과해도 제품 채택은 별도 결정이다. 따라서 이 문서의 질문은 “제품 STT를 무엇으로 할까”가 아니라 **“연구 트랙 D를 다음에 어떻게 진행할까”**다.
2. **Addendum D의 Wave 0은 완료됐다.** 정규화 정정, Q8 다층 hidden parity, VPS 5대 준비·카나리, 추출 RTF·reader 비용 probe가 끝났다.
3. **D-β Wave 1(6시간, 4개 arm)도 완료됐다.** 정정 후 dev CER은 F-D **0.5909**, F-A′ **0.3939**, F-B **0.3914**, F-C **0.3882**다. F-A′/F-B/F-C는 0.57%p 이내로 동률이고, 모든 pairwise 95% CI가 0을 포함한다.
4. **검토 준비 중 평가 하네스 오류를 하나 발견해 정정했다(D-063).** 최초 D-β 평가는 공백만 제거하고 구두점을 제거하지 않아, 학습 라벨에 없는 구두점을 오류로 계산했다. 정정 후 F-C 기준 절대 CER은 46.6%→38.8%, 어휘 포함율은 85.6%→**98.35%**로 바뀌었다. 이 정정은 **임계값 완화가 아니라 사전등록된 정규화의 적용**이다. 상세는 §3.3.
5. **Wave 2A 설계안은 승인 대기 중이다.** FLEURS ko dev 확보, vocab 재구성, F-C softmax mix, 3-arm 재학습을 1~2일에 수행하는 안이다. 그러나 설계안은 정정 전 수치를 전제로 작성됐고, 정정 후 5% Go 기준은 더 어려워졌다(목표 CER ≤0.3742).
6. **아직 해결되지 않은 핵심 문제는 “깨끗한 최종 test”다.** D-β는 Kspon eval_clean 100을 dev로 썼고, 이는 AM-9가 “최종 1회”로 지정한 test다. FLEURS test도 G-C2/C-8에서 이미 사용됐다. Wave 2A는 FLEURS dev를 쓰지만, D의 최종 test를 무엇으로 할지는 아직 사전등록되지 않았다.
7. **현재 실행 중인 작업은 없다.** VPS 5대는 모두 stopped이고, 로컬 백그라운드 학습도 없다.

### 이번 검토에서 가장 중요한 두 가지 질문

- **Q1:** D-β의 “256d readout 병목” 결론과 R-D1 형식 지지는 정규화 정정 후에도 유지되는가. 아니면 “탐색적”으로 더 낮춰야 하는가.
- **Q2:** 다음 단계는 **Wave 2A(측정 타당성+softmax mix)**, **Wave 2B(상위층 LoRA)**, **Wave 2C(데이터 확장)** 중 무엇인가. Wave 2A를 한다면 §4의 설계와 5% 기준을 그대로 승인할 수 있는가.

---

## 1. 프로젝트 개요 (자가완결)

### 1.1 목표

메모리 시스템에 항상 상주하는 **EmbeddingGemma 2(EG2)** 하나를 인코더로 재사용하고, 그 위에 작업별 경량 헤드를 얹어 다음 6개 기능을 **대형 모델 상주 없이** 수행할 수 있는지 실측한다.

| ID | 기능 | EG2 사용 방식 | 현재 상태 |
|---|---|---|---|
| F1 | 오디오 언어 판정 | 오디오 임베딩 + 프로토타입/margin | 운영 LID 그래프 유지. Q8 교체는 G-A3L-R FAIL로 보류 |
| F2 | 한국어 STT | 오디오 타워 + CTC reader | **제품 경로는 komixv2/whisper(D-057)**, D는 연구 트랙 |
| F3 | 비전 태깅 | 이미지 → 유사 이모지 검색 → 명칭 태그 | C-9 파일럿 미착수(사용자 라벨링 대기) |
| F4 | 맞춤법 검사·교정 | 규칙 + 디코더 재순위/편집 태깅 | P1 파일럿 FAIL, 텍스트 hidden 제품 경로 비채택 |
| F5 | 메모리용 요약 | 디코더 생성 + 슬롯 검증 | G-DATA 1단계 3,320쌍 PASS, 파일럿 미착수 |
| F6 | STT 후처리 | CTC 출력 → 디코더 교정 | G-DATA F6 1,320쌍 PASS, 파일럿 미착수 |

### 1.2 불변 조건

| 항목 | 내용 |
|---|---|
| 하드웨어 | Windows 11, Ryzen 5 7600 6C/12T, RAM 15.6GB, **GPU 없음**, ONNX Runtime CPU EP, Q8 중심 |
| 성능 판정 | **로컬 PC만 인정.** VPS 수치는 “참고(VPS)”로 표기하고 판정에 쓰지 않음 |
| 원본 가중치 | **불변.** 허용: 헤드·어댑터·LoRA 사본·pruning 사본·양자화 사본·ONNX export. 금지: 풀 파인튜닝, EG2 상위 층 파인튜닝 |
| 데이터 등급 | **P0(공개·합성)**만 VPS·외부 API 허용, **P1(개인)**은 로컬 전용. 이 문서의 모든 실험은 P0만 사용 |
| 기존 자산 | `C:\code\eg2-langidentifier`, `%LOCALAPPDATA%\jev-mem`, Hermes 코어는 **읽기 전용** |
| 게이트 | 2026-11-01 사전등록. 결과를 본 뒤 임계값 변경 금지. 변경 필요 시 사유 기록 + 사용자 승인 |
| 승인 | CP0/CP1/CP2/CP2′/CP-C1/CP-C2/CP-C3/CP-C4에서 사용자 승인 없이 자동 진행 금지 |
| 시크릿 | 코드·문서·로그·manifest에 기록 금지. 값은 모두 [REDACTED] |

### 1.3 EG2 구조 (실측 확인)

| 구성 | 값 |
|---|---|
| 전체 | 744M = 텍스트 백본 271M + 비전 167M + 오디오 305M |
| 텍스트 백본 | 24층 양방향 Transformer, model dim 512, 출력 임베딩 768, mean pooling |
| 오디오 타워 | 2층 CNN downsample + 12층 Conformer, hidden 1024, output_proj 1536 → 512 soft token |
| 오디오 프레임 | 40ms 청크, **25 tokens/sec** (16초 = 400 프레임) |
| 오디오 학습 상태 | Gemma 4 E2B/E4B 오디오 인코더와 **bit-identical**, EG2 학습 중 **frozen** |
| 운영 ONNX | `eg2_audio_q8_layers.onnx` (Q8, 14출력) |

`eg2_audio_q8_layers.onnx`의 14개 출력:

| 출력 | shape (16초) | 의미 |
|---|---|---|
| `audio_features` | `[N, 512]` 유효 프레임만 | `embed_audio` 1536→512 투영 **후** |
| `aud_h_l00`~`aud_h_l11` | `[1, 400, 1024]` 각각 | 12층 hidden (패딩 포함) |
| `aud_out_proj` | `[1, 400, 1536]` | output_proj 후, `embed_audio` **이전** |

**중요:** EG2는 인코더 전용 모델이므로 생성 능력이 없다. STT를 하려면 별도 reader/디코더가 필수다. D-β는 오디오 타워를 동결한 채 **CTC reader만 학습**했다.

### 1.4 D 트랙의 위치

- 제품 F2는 이미 komixv2(5.49%)/whisper-turbo(5.09%)로 닫혀 있다(D-057). D는 “EG2 하나로 어디까지 가능한가”를 측정하는 **연구 트랙**이다.
- 따라서 D가 G-C2(≤15%)를 통과하지 못해도 제품 계획은 바뀌지 않는다. D의 가치는 ①단일 상주 구조의 가능성 ②오디오 타워의 재사용 범위 ③F1/F3와의 공유 비용을 아는 데 있다.
- D-γ(운영 그래프에 LoRA merge)는 **불허**, D-γ′(LoRA 사본)와 D-δ(증류)는 **보류**다. D-γ′ 재개는 D-5 결과와 비용 견적 후 CP-D1 재승인이 필요하다.

---

## 2. 직전(3차) 검토 이후 진행

3차 검토요청서(2026-11-03)는 CP-C1(F2 방향)을 묻는 문서였다. 그 이후 다음이 진행됐다.

| 항목 | 내용 | 근거 |
|---|---|---|
| D-057 | CP-C1 확정: F2 제품=komixv2/whisper, D=연구 트랙. G-C2a 승인. D-γ 불허, D-γ′·D-δ 보류. AM-9/AM-10·R-D1/R-D2 사전등록 | `docs/decisions.md` |
| D-058 | Addendum D errata 8건 채택: D0-a 정규화 라벨 정정, F-A′=`aud_out_proj` 1536, Q8 hidden parity 선행, H=6h, R-D1≠G-C2, 라벨시트 HTML, P1 clean 재사용, G-A3S p1/p5 | `docs/addendum_D_errata.md` |
| D-059 | Wave 0: D0-a 16.933%/18.959%, D0-e Q8 hidden parity(6/8/10 p1≥0.9997, 11층 0.9973, 256d p1 0.9959), D0-c VPS 5대·카나리 cos 1.0, D0-d 추출 RTF | `reports/D0a_normalization.md`, `D0e_graph_taps.md`, `D0c_vps_ready.md`, `D0d_cost_probe.md` |
| D-060 | D0-d 완료: reader 8.65M params, 로컬 1.452s/step·4.09분/epoch·1,452MB, eg2-1 1.180s/step·3.32분·1,655MB | `reports/D0d_cost_probe.md` |
| D-061 | D-β 데이터 확정: 6.0008h/2,384클립(Zeroth 3.9001h/1,534 + Kconf 2.1007h/850), dev=Kspon eval_clean 100 | `docs/STT/reports/D5_beta_setup.md` |
| D-062 | D-β Wave 1 완료(탐색적): 최초 보고 CER F-D 0.6433/F-A′ 0.4707/F-B 0.4679/F-C 0.4663 | `docs/STT/reports/D5_beta_pilot.md` |
| D-063 | **D-β 평가 정규화 정정**: 정정 후 CER 0.5909/0.3939/0.3914/0.3882, coverage 98.35%, R-D1 +34.30% CI [+29.77,+39.26] | `docs/STT/reports/D5_beta_pilot.md` §9, `reports/provenance/W1/normalized_cer.json` |
| 외부 자료 | EG2 논문(arXiv:2610.37364) 검토, Sténo(프랑스어 EG2 CTC) 공개 사례 검토 | `references` 요약은 §3.7 |

### 2.1 현재 게이트 스냅샷

| 게이트 | 판정 | 핵심 |
|---|---|---|
| G-A1 | PASS | 텍스트 9출력 + 오디오 12층(q8 그래프 수술) |
| G-A3 | PASS | 텍스트 cos 0.999999999998, 오디오 q8 0.99945+ |
| G-A3L-R | FAIL | Q8 LID 216/220=98.18%, CP [95.41, 99.50], 확신 오판 21→23 |
| G-A4 | PASS | Q8 층별 cos 0.9977, LID 44/44 |
| G-B1.5-a | FAIL(l04) | l04 0.8504; l00 PASS는 임베딩 조회로 판정 대상 아님 |
| G-B1.5-b | FAIL(1/3) | T1-exp +5.60%p PASS, T2 +1.87%p FAIL, T3′ +0.89%p FAIL |
| G-B1.5-c | PASS | l00 0.043%p, l04 −0.059%p |
| P1(F4) | FAIL | ΔAUPRC +2.83%p(CI +2.13~+3.67), 기준 +3%p 미달 |
| G-C2 | FAIL | Notesoop FLEURS ko 382클립 18.96%(CI [17.55,20.38]) > 15% |
| G-C2a | PASS(측정·승인) | Q8 특징 CER 상대 −0.12%, cos 0.999642 |
| G-DATA | 1단계 PASS | F5 2,000 + F6 1,320 = 3,320쌍, 사람 수용 100% |
| G-C1/C3/C4/C5 | 미측정 | C-9/C-11.1/C-6 대기 |

이 표에서 중요한 것은 **F2 제품 경로가 이미 닫혔다는 점**이다. G-C2 FAIL은 D를 중단할 이유가 아니라, D를 연구 트랙으로 분리한 이유다.

---

## 3. D-β Wave 1 — 설계·결과·정정

### 3.1 데이터

| 소스 | 용도 | 시간 | 클립 | 화자 |
|---|---|---:|---:|---|
| Zeroth train (Bingsu/zeroth-korean, P0) | 낭독체 | 3.9001h | 1,534 | 화자 ID 없음 |
| KconfSpeech sample (P0) | 회의·대화체 | 2.1007h | 850 | 3명(S000012/13/17) |
| **합계** | 학습 | **6.0008h** | **2,384** | — |
| Kspon eval_clean 100 (P0) | dev(중간 판단) | 0.079h | 100 | 학습과 분리 |

- 목표 구성(낭독 65% + 대화 35%)을 **65.0/35.0**으로 충족했다.
- 모든 클립은 **0.5~16초**로 제한했다. 16초 초과 클립은 학습에서 제외하고 목표 시간을 다시 채웠다.
- 참조 텍스트는 Kconf 주석·문장부호·슬래시를 제거하고 공백을 정리했다. 학습 목표는 **공백 제거 문자 단위**다.
- **화자 분리 한계:** Zeroth에는 화자 ID가 없어 낭독 구간의 speaker-disjoint holdout을 보장할 수 없다. Kconf는 화자 ID가 있으나 3명뿐이다.
- **dev 문제:** FLEURS dev가 없어 Kspon eval_clean 100을 dev로 썼다. 이는 AM-9가 “최종 판정 1회”로 지정한 test를 dev로 쓴 것이다. D-β 결과를 **탐색적**으로 표기하는 이유 중 하나다.

### 3.2 Arm 정의

| Arm | 입력 | 차원 | 전처리 | 특징 크기 |
|---|---|---:|---|---:|
| F-D | `audio_features[:256]` | 256 | 프레임별 L2 | 245MB |
| F-A′ | `aud_out_proj` | 1,536 | 프레임별 LayerNorm | 1.5GB |
| F-B | `aud_h_l11` | 1,024 | 프레임별 LayerNorm | 1.0GB |
| F-C | `aud_h_l06/08/10/11` concat | 4,096 | 층별 LayerNorm 후 concat | 3.9GB |

- F-D는 Notesoop 방식의 256d readout으로, **병목 상태의 대조군**이다.
- F-A′는 `audio_features`(512, LM 이후)가 아니라 `aud_out_proj`(1536, LM 이전)를 쓴다. errata E-2에 따른 정본이다.
- F-C는 Addendum D-5.4가 요구한 **softmax 학습 혼합이 아니라 concat + 선형 투영**이다. 선형 투영이 학습 가능한 혼합을 대신하지만, 정본과 동일하지 않다. 이 차이는 결과 해석에 명시한다.

### 3.3 결과 (정정 후, 주지표)

**정정 전후 비교:**

| Arm | 정정 전 CER(구두점 포함) | 정정 후 CER(통일 정규화) | 오류/참조 | best epoch | 학습 시간 | 파라미터 |
|---|---:|---:|---:|---:|---:|---:|
| F-D | 0.6433 (1,163/1,808) | **0.5909** | 930/1,574 | 17 (20까지) | 5.67h | 7.61M |
| F-A′ | 0.4707 (851/1,808) | **0.3939** | 620/1,574 | 11 (early@16) | 4.37h | 8.10M |
| F-B | 0.4679 (846/1,808) | **0.3914** | 616/1,574 | 7 (early@12) | 3.14h | 7.90M |
| F-C | 0.4663 (843/1,808) | **0.3882** | 611/1,574 | 8 (early@13) | 3.61h | 9.08M |

- **best arm = F-C (0.3882).**
- F-A′/F-B/F-C는 **0.3882~0.3939**, 즉 **0.57%p 이내**다.
- 정정 전 값은 `reports/provenance/W1/*.json`의 raw `cer` 필드에 남아 있다. 판정·비교에는 정정 후 값을 쓴다.

**정정의 원인과 정당성:**

- `train/d5_reader.py:decode_npz`가 비교 직전에 `p.replace(" ", "")`와 `t.replace(" ", "")`만 적용하고, `eval/normalize.py:normalize_nospace`를 적용하지 않았다.
- 학습 라벨(Kconf)은 문장부호·슬래시를 제거한 상태이고, 학습 vocab 1,069자에도 구두점이 없다. 따라서 모델은 구두점을 출력할 수 없는데, dev 참조에는 `/ . ( ) ? +` 등이 남아 있었다.
- 정정 전 “어휘 포함율 85.6%(260/1,808)”의 260개 중 **234개가 비영숫자 기호**였다(`/ . ( ) ?` 226개 + `+`·`,` 8개). 통일 정규화 후 dev 참조는 1,574자이고, vocab에 없는 문자는 **26개(1.65%)**다(숫자 16개 + 희귀 한글 10개).
- 정규화는 Addendum D-5.6의 “CER(공백 무시)”와 D0-a에서 확정한 `normalize_nospace`를 적용한 것이다. **임계값을 바꾼 것이 아니라 평가 하네스 불일치를 수정한 것**이다.
- 상세 재계산: `reports/provenance/W1/normalized_cer.json`. 이 파일에는 arm별 CER·오류/참조, R-D1, pairwise CI, coverage, missing top 20이 들어 있다.

### 3.4 R-D1과 arm 간 비교

**R-D1 (병목 가설):**

- 정의: `(CER_FD − CER_best) / CER_FD`, 문장 단위 대응 부트스트랩 95%.
- 정정 후: `(0.590851 − 0.388183) / 0.590851` = **+34.30%**.
- 10,000회, seed 42, percentile 2.5/97.5: **95% CI [+29.77%, +39.26%]**.
- 점추정 ≥20%, 구간 하한 >0 → **R-D1은 형식상 “지지”**.

**Arm 간 pairwise 차이(정규화 CER, 10,000회 대응 부트스트랩):**

| 비교 | 점추정 차이 | 95% CI | 해석 |
|---|---:|---:|---|
| F-A′ − F-B | +0.254%p | [−1.57, +2.18]%p | 0 포함 |
| F-A′ − F-C | +0.572%p | [−1.45, +2.56]%p | 0 포함 |
| F-B − F-C | +0.318%p | [−1.63, +2.07]%p | 0 포함 |

- 따라서 “F-C가 최고”라고 말할 수는 있지만, **F-A′/F-B/F-C 중 어느 것이 실제로 우수한지는 이 표본으로 판별할 수 없다.**
- R-D1은 **F-D(256d)와 나머지 세 arm의 차이**만 지지한다. “LM/projection 병목”인지 “중간층 정보가 필요”인지 구분하지 못한다.

**R-D1을 G-C2와 혼동하지 말 것:**

- R-D1의 기준은 **F-D arm의 dev CER 0.5909**이지, G-C2의 Notesoop 18.96%가 아니다.
- F-D 0.5909에서 20% 개선하면 0.4727로, 여전히 15%의 3배가 넘는다. **R-D1 지지는 G-C2 통과와 무관하다.**
- 정정 전 `docs/gates.md`에 “F-D 18.96%의 20% 개선은 15.17%”라는 오기가 있었다. D-063에서 “R-D1 기준은 F-D arm 0.5909”로 정정했다.

### 3.5 프로토콜 이행과 편차

| 요구 (D-5) | 이행 | 비고 |
|---|---|---|
| 4~6h, 낭독 65% + 대화 35% | **이행** 6.0008h (65.0/35.0) | Zeroth + Kconf |
| 모든 arm 같은 오디오·코드·시드 | **이행** | seed 42, batch 8, threads 4 |
| F-A′ = `aud_out_proj` 1536 | **이행** | errata E-2 |
| F-C = 6/8/10/11 softmax 학습 혼합 | **부분 이행** | concat + 선형 투영. softmax mix 아님 |
| reader 4층 d384, ≤10M | **이행** | 7.61~9.08M |
| dev = FLEURS ko dev | **미이행** | FLEURS dev 미확보 → Kspon eval 100 |
| FLEURS test 최종 1회만 | **이행(미사용)** | D-β에서는 사용 안 함 |
| speaker-disjoint holdout | **부분** | Kconf는 화자 ID, Zeroth는 화자 ID 없음 |
| 어휘 포함율 보고 | **이행(정정)** | 98.35% (26/1,574). 정정 전 85.6%는 구두점 포함 |
| CER 공백 포함/WER | **미이행** | 예측이 공백을 출력하지 않아 WER 산출 불가 |
| R-D2 H/3·2H/3·H | **미이행** | Wave 2 |

**AM-9 위반 명시:** D-β는 Kspon eval_clean 100을 dev로 사용했다. AM-9는 이 세트를 “최종 판정에 1회만” 쓰도록 사전등록했다. 따라서 D-β의 R-D1은 **탐색적**이며, 게이트 판정이나 최종 test로 취급하지 않는다. Wave 2A는 FLEURS ko dev를 사용해 이 문제를 고치려 한다.

### 3.6 결과의 의미 / 의미하지 않는 것

**의미하는 것:**

- 6시간 데이터·동결 타워·4층 reader 조건에서, 256d readout(F-D)은 1536/1024/4096 특징보다 **명확히 나쁘다**.
- richer feature를 쓰면 dev CER이 0.59 → 0.39로 내려간다. 이는 “LM/projection 이전 특징을 쓰는 것이 낫다”는 방향과 일치한다.
- 6시간 조건에서 문자 단위 CTC reader는 **학습은 된다**. F-D도 17 epoch에서 0.5909까지 내려갔고(20 epoch까지 학습), 초기 blank plateau는 정상이다.

**의미하지 않는 것:**

- “F-C가 최적이다” — pairwise CI가 모두 0을 포함한다.
- “중간층이 필요하다” — F-A′/F-B/F-C가 동률이라 층 선택을 판별할 수 없다.
- “EG2 STT의 구조적 한계가 39%다” — 데이터 6시간, 문자 단위, 동결 타워, dev 도메인 불일치가 모두 섞여 있다.
- “R-D1 지지 = G-C2 통과 가능” — R-D1 기준은 F-D 0.5909이고, 20% 개선은 0.4727로 15%에 한참 못 미친다.
- “어휘가 14% 부족하다” — 정정 후 1.65%다. 구두점을 어휘 결손으로 오계산한 값이었다.

### 3.7 외부 비교 — Sténo와 EG2 논문

#### Sténo (프랑스어 EG2 CTC, 공개 프로젝트)

Sténo는 같은 EG2 오디오 타워 위에 CTC reader를 얹어 프랑스어 STT를 만든 공개 사례다. 수치는 원문 보고값이며, 우리 한국어·CPU·6시간 조건의 재현값이 아니다.

| 항목 | Sténo | 우리 D-β |
|---|---|---|
| 타워 | 1~9층 동결, **10~12층 fine-tune** | 전체 동결 |
| 특징 결합 | **13-state learned softmax mix** | F-C concat+linear (4층) |
| 출력 | **Gemma wordpiece 30,002**, Gemma 임베딩으로 head 초기화 | 한글 문자 1,069, 랜덤 head |
| 데이터 | **3,205h** (MLS/CommonVoice/YODAS 등) | **6h** |
| 학습 | 단일 L40S 48GB, base 약 38 GPUh | CPU 4 vCPU, 3~6시간/arm |
| FLEURS fr | WER 12.8% greedy / 9.7% + LM | CER 38.8% (다른 언어·지표) |

**해석 규칙:**

- Sténo의 WER와 우리 CER은 언어·정규화·테스트셋이 달라 직접 비교하지 않는다.
- Sténo는 **상위층 fine-tune·wordpiece head·데이터 규모**가 핵심 레버임을 보여준다. 우리 결과만으로 “EG2 STT는 원래 안 된다”고 결론내리면 안 된다.
- Sténo의 13-state mix는 Addendum D-5.4의 “학습 가중 혼합”의 실제 구현이다. 우리 F-C(4층 concat+linear)와 같은 이름으로 부르지 않는다.
- Sténo가 부분 fine-tune했다고 해서 D-β의 동결 조건을 중간에 바꾸지 않는다. Wave 2의 새 사전 선언 실험으로만 바꾼다.

#### EG2 논문 (arXiv:2610.37364)

| 사실 | 내용 | 우리에게 중요한 이유 |
|---|---|---|
| 오디오 타워 | Gemma 4 E2B/E4B와 **bit-identical**, EG2 학습 중 **frozen** | D-β는 “동결 타워의 readout”만 비교한다. 타워 자체의 상한을 말하지 않는다 |
| 비전 ablation | trainable 52.27 vs frozen 48.18 (MMEB-v2) | 오디오도 추가 학습 시 이득 가능성이 있다는 정황. D-γ′/Wave 2B의 근거 |
| Native audio vs ASR text | MSEB 69.54 vs 57.59 | **검색·분류** 결과. STT CER의 근거가 아니다 |
| MRL 768/512/256/128 | 최종 임베딩 기준. 256d 66.76 | 우리 F-D의 `audio_features[:256]`은 **임의 절단**이지 MRL이 아니다. Notesoop 256d projection도 논문 MRL과 동일하지 않다 |
| 양자화 | activation 8-bit + weight 2/4/8-bit by layer cluster | Q8 hidden parity(D0-e)와 일치하는 민감도 신호 |
| Future work | unpooled token representations를 STT/router/reranker에 적응 | 우리의 frozen tower + CTC reader 방향이 범위 안에 있다 |

**주의:** 논문에는 CTC STT·토큰 표면정보·맞춤법 평가가 없다. 우리 B1.5/P1 결과와 충돌하지 않는다.

---

## 4. Wave 2A 설계안 (승인 대기)

### 4.1 목적

D-β의 결론을 해석 가능하게 만드는 **측정 타당성 보강**과, Addendum D-5.4가 원래 요구한 **F-C softmax 혼합**을 구현하는 단계다.

### 4.2 Scope

**포함:**

1. FLEURS ko **dev** 확보·manifest·특징 추출
2. dev 어휘 포함율을 유지/개선하는 **고정 출력 vocab** 재구성
3. F-C를 **4개 층(6/8/10/11) softmax 학습 혼합**으로 구현
4. F-A′/F-B/F-C-softmax를 **같은 6시간 오디오·같은 seed**로 재학습
5. dev CER, 어휘 포함율, arm별 파라미터·시간, 대응 부트스트랩 보고

**제외:**

- FLEURS **test** 사용 — G-C2에서 이미 사용, 재사용 금지
- 40시간 확장·R-D2 — Wave 2C
- 오디오 타워 LoRA/fine-tune — Wave 2B
- wordpiece head — 10M 파라미터 상한과 충돌하므로 Wave 2B 이후 별도 검토
- Q4/QAT, Jev head, MaxSim — 별도 승인 사항

### 4.3 변경 사항

| 항목 | D-β | Wave 2A |
|---|---|---|
| dev | Kspon eval_clean 100 (AM-9 위반) | **FLEURS ko dev** |
| vocab | 1,069자, 3회 이상 | 상위 한글 2,350 + 숫자 + 라틴 + 공백 + unk, 약 2,388 |
| F-C | 4층 concat + linear | 4층 **softmax 학습 혼합** |
| arms | F-D/F-A′/F-B/F-C | F-A′/F-B/F-C-softmax (3개) |
| 조건 | 6.0008h, seed 42, batch 8 | 동일 |
| 보고 | CER·시간·파라미터 | + 어휘 포함율·pairwise CI·AM-6 표 |

### 4.4 모델·학습 조건

| 항목 | 값 |
|---|---|
| F-A′ | `CTCReader(in_dim=1536)` |
| F-B | `CTCReader(in_dim=1024)` |
| F-C-softmax | 4개 층 각 1,024d → LayerNorm → 학습 `w[4]` → softmax → 가중 합 1,024d → 기존 reader |
| reader | 4층 Transformer d384, 6 head, FF1536, pre-norm, CTC |
| 파라미터 | F-A′ 8.61M, F-B 8.41M, F-C-softmax 8.42M (모두 ≤10M) |
| 학습 | AdamW, lr 1e-3, cosine, grad clip 5.0, batch 8, seed 42, threads 4 |
| epochs | 최대 20, patience 5, dev CER 최저 checkpoint |
| 호스트 | 로컬 우선(F-C 3.9GB 특징, 15.6GB RAM) |

### 4.5 사전 선언 Go/No-Go

- **Go (Wave 2B로):** 3-arm 중 best가 **정정 후 F-A′ 0.3939 대비 상대 5% 이상 개선**(CER ≤ **0.3742**)이고, 대응 부트스트랩 95% CI 하한 >0.
- **No-Go (reader/output unit 아님):** 상대 개선 <5% 또는 CI 하한 ≤0 → Wave 2B(상위층 LoRA)로 바로 이동하되, Wave 2A 결과를 “reader/output unit 한계”로 기록.
- 정정 전 0.4707 기준의 5% 목표(0.4472)를 그대로 쓰지 않는다.
- 이 기준은 **탐색적 의사결정**이며, G-C2/R-D1 같은 게이트 임계값을 변경하지 않는다.

### 4.6 비용·DoD

- 구현 0.5~1일 + 학습 3~6시간 + 평가 1~2시간 = **1~2일**.
- DoD: FLEURS dev test 미포함, vocab coverage 보고, F-C softmax 파라미터 ≤10M, 3-arm 완료, 문장별 decode 저장, 10,000회 부트스트랩, AM-6 표, `reports/W2A_results.md`.

### 4.7 설계안에 대한 내부 우려 (검토자에게 미리 밝힘)

1. **5% 기준이 정정 후 더 어려워졌다.** 정정 전에는 F-A′ 0.4707 대비 5%면 0.4472였지만, 정정 후에는 0.3939 대비 5%면 0.3742다. 현재 F-C 0.3882에서 3.6% 상대 개선이 필요하다.
2. **vocab 확장의 여지가 줄었다.** 정정 후 coverage는 이미 98.35%다. 2,350자 확장은 숫자·희귀 한글 1.65%를 겨냥하며, 6시간 데이터에서 희귀 음절을 늘리면 head 과적합 위험이 있다.
3. **F-C softmax가 concat+linear보다 나을 보장이 없다.** concat+linear는 차원별 가중치를 학습하는 더 표현력이 큰 구조이고, softmax mix는 층별 스칼라 가중치라 더 제한적이다. 이 비교는 “정본 구현” 충실성과 “정규화” 효과를 함께 바꾼다.
4. **4-state mix는 Sténo의 13-state mix와 다르다.** 6/8/10/11만 쓰는 것이 12층 전체를 쓰는 것보다 나은지 근거가 없다.
5. **FLEURS dev와 test의 분리만으로는 clean test 문제가 해결되지 않는다.** FLEURS test는 G-C2/C-8에서 이미 사용됐고, D의 최종 test는 아직 새로 선언되지 않았다.
6. **한 seed뿐이다.** 0.57%p 차이를 arm 선택에 쓰려면 seed 반복이 필요하다. Wave 2A는 seed 42 하나만 계획하고 있다.

---

## 5. 검토 질문

각 질문에 **① 판정(승인/수정/반대/증거 부족) ② 근거 ③ 권장 다음 단계 ④ 반대 가능성**을 적어 주십시오. 가능하면 선택지 중 하나를 골라 주십시오.

### Q1. D-β의 “256d readout 병목” 결론과 R-D1 지지를 어떻게 평가하는가?

- 정정 후 CER: F-D 0.5909, F-A′ 0.3939, F-B 0.3914, F-C 0.3882. R-D1 +34.30% CI [+29.77,+39.26].
- F-A′/F-B/F-C pairwise CI는 모두 0 포함.
- D-β는 Kspon test를 dev로 사용했고(AM-9 위반), F-C는 softmax mix가 아니다.

선택지:
- **A. 현 결론 유지**: “256d readout 병목”은 지지되고, 층 선택은 미판별. R-D1은 형식상 지지.
- **B. 탐색적으로만 유지**: 방향은 맞지만 AM-9 위반·F-C 편차 때문에 “형식상 지지”라는 표현을 삭제.
- **C. 결론 철회**: dev 오염·F-C 미구현 때문에 D-β로는 아무 결론도 낼 수 없다.

추가로, 정규화 정정(D-063)을 사후 합리화(post-hoc)로 볼지, 사전등록된 지표의 버그 수정으로 볼지 판단해 주십시오.

### Q2. 다음 단계의 우선순위는 무엇인가?

현재 선택지:
- **A. Wave 2A 먼저** (측정 타당성 + softmax mix, 1~2일)
- **B. Wave 2B 먼저** (상위 2~3개 Conformer 층 LoRA/fine-tune, D-γ′ 재승인 필요)
- **C. Wave 2C 먼저** (40시간+ 데이터 확장, R-D2 학습곡선 포함)
- **D. D 연구 트랙 중단** (제품 F2는 이미 komix/whisper로 닫힘)

판단 기준: ① 6시간·1 seed로 얻을 정보의 가치 ② 15% 목표까지의 거리 ③ CPU·RAM·디스크 비용 ④ D-γ′ 승인 리스크 ⑤ “단일 상주” 연구 목표의 중요도.

### Q3. Wave 2A의 5% Go/No-Go 기준이 타당한가?

- 현재: best가 F-A′ 0.3939 대비 상대 5% 이상 & CI 하한 >0 → Go; 아니면 Wave 2B.
- 정정 후 목표 CER은 0.3742. 현재 F-C 0.3882에서 3.6% 상대 개선이 필요하다.
- 1 seed, dev 100문장(1,574자)이라 CI가 넓다.

질문:
- 5%가 적절한가, 아니면 3%·10%로 바꿔야 하는가?
- “CI 하한 >0”만으로 Go를 판정하는 것이 타당한가, 아니면 최소 절대 개선(예: 1%p)도 요구해야 하는가?
- No-Go일 때 “reader/output unit 병목 아님 → Wave 2B”로 바로 가는 논리가 타당한가? Wave 2A의 음성 결과가 구현·vocab 때문일 가능성을 어떻게 배제할 것인가?

### Q4. F-C softmax mix는 4-state로 충분한가?

- Wave 2A는 6/8/10/11 4개 층만 쓴다. Sténo 정본은 13-state(12층 + output) mix다.
- concat+linear는 softmax mix보다 표현력이 크다. 그런데 “정본 구현”을 위해 더 제한적인 softmax로 바꾸는 것이 개선을 기대할 수 있는가?
- 4-state와 13-state 중 무엇을 먼저 측정해야 하는가? 4-state 결과가 좋지 않으면 13-state로 확장하는 순서가 맞는가?

선택지:
- **A. 4-state만** (빠름, D0-e parity가 확인된 층)
- **B. 4-state + 13-state 둘 다** (비용 1.5~2배, 정본 비교)
- **C. 13-state만** (Sténo 정본, 특징 추출·디스크 증가)
- **D. softmax mix를 폐기하고 concat+linear를 유지** (표현력 우선)

### Q5. 출력 단위는 문자 CTC로 충분한가?

- 현재: 한글 음절 + 숫자 + 라틴 + 공백 + unk, 1,069자(확장 시 2,388자), 랜덤 head.
- Sténo: Gemma wordpiece 30,002, Gemma 입력 임베딩으로 head 초기화.
- 우리 예측은 공백을 출력하지 않아 WER·공백 포함 CER을 산출할 수 없다.
- 30k wordpiece head는 30,000×384 ≈ 11.5M로, reader 전체 10M 상한을 넘는다. factorized head(384→128→30k)는 약 3.9M이지만 기존 reader 8.4M과 합치면 약 11.4M로 여전히 10M을 넘는다. 상한을 지키려면 reader 축소·저랭크 결합이 필요하고, 그렇지 않으면 상한 lift 승인이 필요하다.

질문:
- 문자 CTC를 유지해야 하는가, wordpiece head로 가야 하는가?
- 간다면 10M 상한을 Lift할 것인가, reader 축소·저랭크 head를 결합해 상한을 지킬 것인가?
- 한국어 띄어쓰기는 별도 spacing 모듈로 분리하는 것이 맞는가, CTC가 공백을 직접 출력하도록 학습하는 것이 맞는가?
- 제품 F2가 komix/whisper인 상황에서, D의 출력 단위를 제품 요구(WER·띄어쓰기)에 맞출 필요가 있는가?

### Q6. D의 “깨끗한 최종 test”를 무엇으로 할 것인가?

- D-β dev = Kspon eval_clean 100. AM-9는 이 세트를 최종 1회 test로 지정했다. 위반이다.
- FLEURS test 382는 G-C2/C-8/G-C2a에서 이미 사용됐다.
- Zeroth test 457은 C2-A1 기준선 평가에 사용됐다.
- Wave 2A는 FLEURS dev를 쓰지만, 최종 test는 아직 새로 선언되지 않았다.

선택지:
- **A. FLEURS test를 D의 최종 test로 재사용**하되, “이미 다른 시스템 평가에 사용된 benchmark”로 명시하고 D 학습·arm 선택에는 쓰지 않는다.
- **B. Kspon eval_other(3.8h)를 새 최종 test로 선언**한다. 같은 코퍼스·다른 split.
- **C. Zeroth test 457을 D 최종 test로 선언**한다. 학습은 Zeroth train만 사용.
- **D. AI Hub의 새 한국어 음성 holdout을 확보**해 최종 test로 쓴다.
- **E. clean test가 확보될 때까지 Wave 2A를 보류**한다.

질문: 어느 쪽이 AM-9와 비교 가능성(FLEURS 18.96/5.49/5.09)을 모두 만족하는가? 최종 test를 지금 사전등록해야 한다면 어떤 세트인가?

### Q7. 데이터 규모·구성·R-D2

- 현재 6.0008h: Zeroth 3.9001h(낭독) + Kconf 2.1007h(대화), 65/35.
- Sténo는 3,205h. 우리는 40h 확장을 Wave 2C로 미뤘다.
- R-D2(H/3, 2H/3, H 학습곡선 → 40h 외삽)는 아직 실행하지 않았다.
- Zeroth는 화자 ID가 없어 speaker-disjoint holdout이 불가능하다.

질문:
- Wave 2A 전에 R-D2 학습곡선을 먼저 돌려야 하는가? 아니면 2A 후 best arm으로 돌려야 하는가?
- 40h가 의미 있는 최소 규모인가? 100h+가 필요한가?
- 낭독 65/대화 35 비율은 유지해야 하는가? Kspon train(대화체)을 학습에 넣어야 하는가?
- speaker-disjoint를 위해 Zeroth를 포기하고 Kconf/AI Hub만 쓰는 것이 맞는가?

### Q8. Wave 2A에 반드시 넣어야 할 진단·positive control은 무엇인가?

- 현재 계획은 CER·coverage·파라미터·시간·부트스트랩만 본다.
- Wave 2A가 No-Go일 때 “reader/output unit 병목이 아니다”라고 결론내리려면, 구현 실패·vocab·seed·최적화와 구분할 증거가 필요하다.

질문:
- 다음 중 무엇을 mandatory로 넣어야 하는가: ① 1시간 subset overfit test(positive control) ② 2~3 seed 반복 ③ per-domain CER(낭독/대화) ④ error taxonomy(deletion/insertion/substitution) ⑤ blank/alignment 진단 ⑥ vocab oracle(참조 문자를 모두 허용한 상한) ⑦ 13-state mix 비교 ⑧ wordpiece head 비교.
- Wave 2A의 “No-Go → Wave 2B” 결정 전에 최소한 무엇을 확인해야 하는가?

### Q9. D 트랙의 중단·예산 규칙

- D는 제품 경로가 아니므로 무한정 투자할 이유가 없다.
- 현재 D-γ′는 보류, D-δ도 보류다. Wave 2B는 LoRA 사본(+약 325MB, 세션 1개)과 Q8 parity 재검증을 요구한다.

질문:
- D 트랙에 허용할 최대 기간·비용(예: 2주, 40h 데이터, VPS 5대)을 지금 정해야 하는가?
- 어떤 결과가 나오면 D를 중단하고 F1/F3/F5로 자원을 돌려야 하는가?
- “15% 미달이어도 단일 상주 구조의 정보 가치가 있으면 계속”이 타당한가?

---

## 6. 검토 방법·출력 형식

### 6.1 검토자가 지켜야 할 것

- **저장소 전체를 처음부터 읽지 않아도 된다.** 이 문서가 자체완결적이다. GitHub는 아래 파일의 실제 내용을 확인할 때만 쓰면 된다.
- **코드를 수정하지 말 것.** 샌드박스 파일 작성은 허용되지만, 원본 저장소 변경·커밋·push는 하지 않는다.
- **서브에이전트/추가 모델 호출 금지.** 검토는 직접 완료한다.
- **수치를 인용할 때 분모와 정규화를 함께 적는다.** CER은 `normalize_nospace` 기준이고, WER은 산출되지 않았다.
- **문서에 없는 사실을 추정하지 않는다.** 특히 “F-D 18.96%” 같은 혼동을 피한다. R-D1 기준은 F-D 0.5909다.

### 6.2 권장 출력 형식

```
Q1: [A/B/C] — 판정 1~2문장
  근거: ...
  반대 가능성: ...
  다음 단계: ...
Q2: ...
...
가장 큰 위험 3개: ...
지금 결정을 보류해야 할 항목: ...
추가로 필요한 증거: ...
```

### 6.3 특히 답을 주었으면 하는 것

1. **Q1과 Q2** — D-β 결론의 과학적 지위와 다음 단계.
2. **Q6** — clean test를 무엇으로 할지. 이 답이 없으면 Wave 2A를 실행해도 최종 판정을 할 수 없다.
3. **Q5** — 문자 CTC vs wordpiece head. 이 결정이 Wave 2A/2B/2C의 범위를 바꾼다.
4. **Q3/Q8** — 5% 기준과 positive control. No-Go 결론의 타당성을 좌우한다.

---

## 7. 재현 정보

### 7.1 핵심 파일

| 경로 | 내용 |
|---|---|
| `docs/STT/reports/D5_beta_pilot.md` | D-β 결과·정정 이력·AM-6 표 |
| `reports/provenance/W1/normalized_cer.json` | 정정 후 CER·coverage·R-D1·pairwise CI |
| `reports/provenance/W1/{fd,fa,fb,fc}.log` | 학습 로그(epoch·loss·dev CER·early stop) |
| `reports/provenance/W1/{fd,fa,fb,fc}.json` | 문장별 예측·오류·참조 문자 |
| `train/d5_reader.py` | CTC reader·학습·decode·dev 평가 |
| `train/w1_extract.py` | 4-arm 특징 추출(F-D/F-A′/F-B/F-C) |
| `runner/w1_build_manifest.py` | 6시간 manifest 생성 |
| `docs/STT/plans/plan_wave2a.md` | Wave 2A 설계안(승인 대기) |
| `docs/decisions.md` | D-057~D-063 |
| `docs/gates.md` | 게이트·R-D1/R-D2/AM-9/AM-10 |
| `reports/D0e_graph_taps.md` | Q8 다층 hidden parity |
| `reports/EXTERNAL_REVIEW_2026-11-03.md` | 3차 검토요청서(배경) |

### 7.2 재현 명령(요약)

```bash
# 6시간 manifest (Zeroth 3.9h + Kconf 2.1h)
.venv/Scripts/python.exe runner/w1_build_manifest.py --read-hours 3.9 --conv-hours 2.1

# 4-arm 특징 추출 (로컬, 6 threads)
.venv/Scripts/python.exe train/w1_extract.py --threads 6 --out-dir data/wave1/feats

# 단일 arm 학습 예시 (실제 실행은 VPS 4대에 분산)
.venv/Scripts/python.exe train/d5_reader.py \
  --features data/wave1/feats/fa.npz \
  --dev-features data/wave1/feats_dev/fa.npz \
  --vocab-file data/wave1/vocab.json --arm fa --in-dim 1536 \
  --epochs 20 --batch 8 --threads 4 --ckpt-dir train/ckpt

# 문장별 decode
.venv/Scripts/python.exe train/d5_reader.py \
  --features data/wave1/feats_dev/fa.npz \
  --vocab-file data/wave1/vocab.json --arm fa --in-dim 1536 \
  --ckpt train/ckpt/fa.best.pt --decode --out logs/W1_decode/fa.json
```

- 실제 D-β 학습은 VPS eg2-1~4에서 실행됐고, 산출물은 `reports/provenance/W1/`에 커밋됐다. VPS는 현재 stopped이며 체크포인트는 `/data/home/unigem/train/ckpt`에만 남아 있다(백업·전송하지 않음).
- 정정 CER 재계산은 `reports/provenance/W1/normalized_cer.json`에 기록했고, `1a80e12`에서 `evaluate_cer`·`decode_npz`가 `normalize_nospace`를 쓰도록 수정했다. `eval/normalize.py`의 `normalize_nospace`와 `_edit_distance`로 재현할 수 있다.

### 7.3 환경

| 항목 | 값 |
|---|---|
| OS | Windows 11 |
| CPU | Ryzen 5 7600 6C/12T |
| RAM | 15.6GB |
| GPU | 없음 |
| ORT | 1.31.1 CPU EP |
| Python | 3.12 |
| venv | `.venv` (ONNX/일반), `.venv-c2a1` (torch 2.9.1, transformers 5.22.1) |
| 디스크 여유 | 약 48GB |
| VPS | eg2-1~eg2-5 전부 stopped |
| 실행 중 작업 | 없음 |

### 7.4 데이터 등급·보안

- 이 문서의 모든 학습·평가 데이터는 **P0(공개·합성)**다. P1 데이터는 사용하지 않았다.
- 원시 오디오는 저장소에 포함하지 않았다. 집계·manifest·문장별 decode만 커밋했다.
- API 키·토큰·SSH 키·VPS ID는 이 문서에 기록하지 않았다. 값이 필요한 재현은 사용자 환경변수로만 한다.

---

## 8. 부록 — 용어·약어

| 용어 | 정의 |
|---|---|
| EG2 | EmbeddingGemma 2. 744M 멀티모달 임베딩 모델. 여기서는 오디오 타워와 텍스트 백본을 인코더로 재사용 |
| F-D | Notesoop 방식 256d readout 대조군. `audio_features[:256]` + L2 |
| F-A′ | `aud_out_proj` 1536d. LM/projection 이전 특징 |
| F-B | `aud_h_l11` 1024d. 단일 상위층 |
| F-C | 6/8/10/11층 concat 4096d. D-β에서는 concat+linear, Wave 2A에서는 softmax mix 예정 |
| CTC | Connectionist Temporal Classification. 프레임별 문자 확률 + blank + 반복 병합 |
| CER | Character Error Rate. 여기서는 `normalize_nospace` 기준(공백·구두점 제거) |
| WER | Word Error Rate. 현재 예측이 공백을 출력하지 않아 산출하지 않음 |
| AM-9 | 중간 의사결정에는 dev만, test는 최종 1회만 사용하는 사전등록 규칙 |
| AM-10 | arm 간 코드·하이퍼파라미터·시드·데이터 목록을 동일하게 하는 규칙 |
| R-D1 | F-D 대비 best arm의 상대 CER 개선 ≥20% & CI 하한 >0을 “병목 가설 지지”로 보는 사전등록 |
| R-D2 | H/3·2H/3·H 학습곡선을 로그-시간에 적합해 40h CER을 외삽하는 사전등록 |
| D-γ′ | LoRA merge 사본을 별도 ONNX 세션으로 두는 안. 원본·F1 보존, +약 325MB. 현재 보류 |
| Sténo | 공개 프랑스어 EG2 CTC 프로젝트. 3,205h, 13-state mix, 30k wordpiece head |

---

## 9. 마지막 요약

- D-β는 **“256d readout은 병목”**까지만 보였다. 층 선택은 못 했다.
- 정정 후에도 **R-D1은 형식상 지지**지만, 이는 G-C2와 무관하고, D-β는 AM-9 위반으로 탐색적이다.
- Wave 2A는 이 결론을 해석 가능하게 만들려는 1~2일짜리 보강안이지만, **정정 후 5% 기준이 더 어려워졌고, vocab 확장의 여지도 줄었다.**
- 가장 큰 미해결 문제는 **clean final test**와 **출력 단위(문자 vs wordpiece)**다.
- 검토자에게 바라는 것은 “예/아니오”가 아니라, **Q1·Q2·Q6·Q5에 대한 판정과 그 근거**다.
