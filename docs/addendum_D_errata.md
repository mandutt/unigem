# Addendum D — Errata (채택 전 수정 사항)

- 작성: 2026-11-03
- 대상: `docs/addendum_D.md` (SHA256 `c9d7ed025a80260f9d8450b209b5bc20230d56949deaf290afe1c7afb8e87be2`)
- 근거: `reports/Addendum_D_review.md`의 P0/P1 검증
- 효력: Addendum D 본문을 수정하지 않고, 아래 항목만 보충한다. 충돌 시 **이 errata가 우선**한다.

---

## E-1. D0-a — 정규화 "불일치"는 라벨 오기다

Addendum D D0-a의 다음 문장을 정정한다.

> Notesoop 공백 무시 CER 17.41% → 18.96% (상승), 공백 포함 19.10% → 16.93% (하락)

**정정:**

| 조건 | 구 정규화 | 신 정규화 |
|---|---|---|
| 공백 포함 CER | **17.410%** | **16.933%** |
| 공백 무시 CER | **19.097%** | **18.959%** |

- 17.41은 **공백 포함**, 19.10은 **공백 무시**다. 신 정규화에서 두 지표 모두 소폭 개선됐다.
- D0-a의 "원인 규명" 조사(단계별 켜고 끄기·참조 필드 비교)는 **불필요**하다.
- D0-a는 ① 라벨 정정 ② `eval/normalize.py` 단일화 ③ 기존 표 재계산으로 종결한다.

---

## E-2. D-5.4 F-A — `audio_features`가 아니라 `aud_out_proj`를 쓴다

Addendum D D-5.4의 F-A 정의를 정정한다.

> F-A: 타워 최종 출력 `audio_features` (LM 이전) — LM·projection 병목 제거 효과

`audio_features`는 `embed_audio` 1536→512 투영 **후**다. LM은 bypass하지만 projection 병목은 bypass하지 못한다.

| Arm | 입력 | 차원 | 가설 |
|---|---|---|---|
| **F-A′** | `aud_out_proj` (embed_audio 이전) | 1536 | **LM·projection 병목 제거** |
| F-A512 | `audio_features` (embed_audio 이후) | 512 | 256d MRL 절단 제거 (Wave 2 ablation) |

- 1차 파일럿은 **F-A′** 로 수행한다. F-A512는 Wave 2에서 여유 호스트가 있을 때만.
- F-A′ 저장량은 1536d FP16 기준 **0.28GB/h**(6h 1.7GB)다.

---

## E-3. D0-e — Q8 hidden parity를 먼저 확인한다

Addendum D는 "Q8 특징 안전성은 G-C2a로 확인"이라고 했지만, G-C2a가 검증한 것은 **최종 256d 특징** 하나뿐이다.

- F-B(11층 1024d), F-C(6/8/10/11층 1024d)의 **중간 hidden Q8 오차**는 미측정이다.
- D0-e에서 `eg2_audio_research_fp32_t1600_l12.onnx`와 `eg2_audio_q8_layers.onnx`의 6/8/10/11층 hidden을 같은 입력 20~50개로 비교해 **cos 최소·p1·p5**를 보고한다.
- 기준 미달이면 F-B/F-C는 FP32 특징으로 먼저 파일럿하고, Q8은 별도 arm으로 둔다.

---

## E-4. 파일럿 데이터 크기 — H=6h로 고정

Addendum D D-1은 "10h급 파일럿", D-5.3은 "4h ≤ H ≤ 6h"로 서로 다르다.

- VPS 데이터 예산 약 5GB, F-C 6h = 4.4GB이므로 **H=6h가 상한**이다.
- 1차 파일럿은 **H=6h**로 고정한다. "10h급"은 Wave 2 스케일업 표현으로만 쓰고, 40h는 **학습이 아니라 학습곡선 외삽**임을 명시한다.

---

## E-5. R-D1 "20% 지지"는 G-C2 15% 통과가 아니다

- F-D 18.96%에서 상대 20% 개선은 **15.17%** 로, 여전히 G-C2(≤15%) 위다.
- R-D1은 "병목 가설 지지"일 뿐이다. G-C2 통과 여부는 R-D2 외삽과 스케일업 후 최종 test로 판단한다.
- R-D1 문구에 "G-C2 통과 아님"을 명시한다.

---

## E-6. D-7.1 라벨링 시트는 HTML

- Addendum D의 "CSV 또는 단일 HTML"을 **HTML 카드형 + localStorage + JSON 내보내기**로 확정한다.
- CSV는 내부 백업용으로만 만든다(사용자 기존 지시).

---

## E-7. F4 정상 identity는 기존 P1 데이터를 재사용

- `data/p1/p1_corpus.jsonl`: clean train **1,600**, clean test **700**.
- D-6.2의 정상 identity 2,000을 새로 수집하지 말고, clean train 1,600을 학습에, clean test 700을 과교정 평가(≥600)에 쓴다.
- F4-v2의 2,000문장 확대(D-049)와는 별개다. 중복 검사를 먼저 한다.

---

## E-8. G-A3S 보완

- `reports/G_C2a.md`의 최종 256d 특징은 평균 0.999642, 최소 0.989480이다.
- G-A3S 보고에는 **프레임별 최소·p1·p5**를 추가한다. p1/p5가 Q8 기준 0.98 미만이면 해당 arm은 FP32로 재측정한다.

---

## 적용 순서

1. `docs/addendum_D.md` 저장·SHA 기록
2. 이 errata 저장·SHA 기록
3. `decisions.md` D-057(Addendum D 수신·CP-C1 결정), D-058(errata)
4. `gates.md` AM-9/AM-10/R-D1/R-D2, G-C2/G-C2a/G-A3S 표 갱신
5. D0-a → D0-e → D0-c → D0-d → D0-b 순으로 Wave 0
