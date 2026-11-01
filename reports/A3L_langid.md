# G-A3L — 언어 판정 회귀 (텍스트 그래프 교체)

- 작성: 2026-11-02
- 대상 게이트: **G-A3L** (기존 대비 argmax 일치율 ≥ 99%, 확신 오판 증가 0)
- 판정 환경: `local`
- 스크립트: `eval/a3l_langid.py` (`--mode old` → `--mode new` → `--mode compare`)

## 1. 목적

A2에서 재수출한 텍스트 그래프가 기존 운영 판정 결과를 깨지 않는지 확인한다.
오디오 인코더는 **기존 운영 q8-al4를 그대로** 쓰고, 텍스트 그래프만 교체해 차이를 하나로 통제했다.

- 기존(old): 운영 `make_embedder` (오디오 q8-al4 + 텍스트 q8-al4)
- 신규(new): 운영 오디오 q8-al4 + **신규 텍스트 FP32** (`eg2_text_research_fp32.onnx`)
- 판정기: `eg2_langid.LanguageIdentifier` (29-way 프로브 + 그룹/id-ms 헤드 + unknown 게이트), 변경 없음

## 2. 입력

FLEURS **test** split, 22개 언어 × 2클립 = **44클립** (`C:\code\eg2-langidentifier\data\raw\fleurs_cache`, 읽기 전용).
언어: en ko ja zh es pt fr de it nl pl ru uk sv ar hi th tr vi fil id ms.
각 클립은 16 kHz mono로 디코드, 최대 30초.

## 3. 결과

| 항목 | 값 |
|---|---|
| n | 44 |
| argmax 일치 | **43/44 = 0.9773** |
| 벡터 cosine 평균 | 0.999887 |
| old margin 중앙값 / 최소 | 0.6322 / 0.0094 |
| new margin 중앙값 / 최소 | 0.6312 / 0.0068 |
| 확신 오판(margin ≥ 0.05) 불일치 | old 0 / new 0 |

불일치 1건:

| 클립 | old | new | old margin | new margin | cos |
|---|---|---|---|---|---|
| `id_id:1` | `ms_my` | `id_id` | 0.0094 | 0.0068 | 0.99988 |

## 4. 게이트 판정

**G-A3L: FAIL** — 사전등록 기준(argmax 일치 ≥ 99%)에 미달한다(43/44 = 97.7%).

근거·해석(임계값 변경 아님):

- 불일치는 **id↔ms 1건**으로, 두 파이프라인 모두 margin < 0.01의 초근접 경합이다.
- 이 쌍은 기존 29-way 판정기에서도 margin이 0.006~0.11로 가장 낮은 공인 혼동쌍이다(eg2-langidentifier Phase 4l).
- 새 그래프는 이 클립에서 **정답(id_id)** 을 냈고, 기존 그래프가 ms로 틀렸다.
- “확신 오판 증가 0” 조건은 충족한다(양쪽 모두 margin ≥ 0.05 오판 0).
- id/ms를 하나의 그룹으로 묶어 세면 **44/44 = 100%** 일치한다.

즉 실질 회귀는 없고, 게이트 정의(단일 argmax)가 언어적으로 모호한 쌍에서 1건 걸린 경우다.
**임계값은 바꾸지 않고 FAIL로 기록**하며, CP1에서 (a) 예외 승인, (b) 그룹 기준 재정의, (c) 추가 표본 확대 중 선택을 요청한다.

## 5. 이상 징후

- 없음. 벡터 cosine 0.9999로 텍스트 그래프 수치 자체는 사실상 동일하다.

## 6. 미해결

- 오디오 타워 다층 export가 완료되지 않아, 신규 오디오 그래프를 포함한 end-to-end 회귀는 아직 없다
  (`reports/A2_export_audio.md` 참조).

## 7. 다음 단계

A4 Q8 양자화 후 같은 44클립으로 재측정(신규 Q8 텍스트 그래프), CP1 보고.
