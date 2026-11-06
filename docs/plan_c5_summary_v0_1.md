# F5 메모리용 요약 — 재개 계획 v0.1

- 작성: 2026-11-06
- 상태: **A0+슬롯 검증기 1차 완료, 사람 검토 대기; C3 A1 미착수**
- 범위: F5 메모리용 중요정보 요약 + 슬롯 보존 검증기
- 관련: `docs/plan_v0_5.md` §C5, `docs/gates.md` G-C5, D-052/D-053, D-079(STT 동결)
- 데이터: `data/external/f5_pairs_v3.jsonl` (2,000쌍)

> STT(F2)는 D-079로 동결됐다. F5는 STT와 독립이며, 이 문서는 **F5만** 재개한다. JEV/메모리 코어는 수정하지 않는다.

## 1. 배경

- F5 데이터 2,000쌍은 이미 사람 검토를 통과했다(F5 2.94/3, 수용 100%, D-053).
- 그러나 **요약기·슬롯 검증기·G-C5 평가는 아직 구현되지 않았다.**
- F5 target 자체에 **슬롯 환각 1.22%**가 보고됐다(D-052). G-C5 기준은 **신규 슬롯 ≤1%**이므로, 학습 전에 target 품질을 먼저 감사해야 한다.
- C3 디코더(A1 T5Gemma 2 / A2 EG2 adapter)는 미착수다. F5는 A0(추출형)으로 먼저 기준선을 만들고, 디코더는 후속으로 비교한다.

## 2. Scope

### 포함

1. **슬롯 추출·검증기**
   - 숫자·금액, 날짜·시간, 버전, 파일명·경로, 영문 식별자·모델명, URL.
   - 원문 슬롯이 요약에 모두 있는지, 요약에 없는 새 슬롯이 생겼는지 검사.
   - 위반 시 **요약 거부 → 원문 폴백**.
2. **F5 target 감사**
   - 2,000쌍의 target 요약에 대해 슬롯 보존율·신규 슬롯률 측정.
   - 1.22% 환각이 어떤 슬롯 유형인지 분류.
   - 필요 시 target repair/filter 정책을 별도 승인.
3. **A0 추출형·템플릿 baseline**
   - 디코더 없이 문장 선택/압축.
   - 슬롯 보존, 압축률, 중복률, 핵심 사실 보존(사람 표본) 측정.
4. **평가 하네스**
   - deterministic split: train/val/test (예: 1,600/200/200).
   - JSONL 예측·메트릭 원장.
   - 사람 표본 50건 검토 시트.
5. **C3 A1 후속 비교(별도 승인)**
   - T5Gemma 2 네이티브 LoRA.
   - A0 대비 품질·슬롯·지연·RAM 비교.
   - A2(EG2 adapter)는 A1 결과 후.

### 제외

- F2 STT 재개
- JEV/메모리 코어 수정
- P1 메모리 원문 사용·외부 API 전송
- G-DATA 2단계 확장
- C3 전체 arm 동시 학습
- 제품 경로 즉시 교체

## 3. DoD

| # | 항목 | 통과 기준 |
|---|---|---|
| 1 | 슬롯 추출기 단위 테스트 | 합성 케이스 ≥50, 유형별 추출·오탐 확인 |
| 2 | F5 target 감사 | 2,000쌍 전수, 슬롯 보존율·신규 슬롯률 보고 |
| 3 | A0 baseline | 2,000쌍 추론, test 200 메트릭 |
| 4 | 슬롯 검증기 | 위반 요약 100% reject, 원문 폴백 |
| 5 | 사람 표본 | 50건, 핵심 사실 보존·과압축 점검 |
| 6 | G-C5 판정 | 슬롯 보존 ≥99%, 신규 슬롯 ≤1% (통과분 기준 0) |
| 7 | 보고서 | `reports/C5_summary.md` |
| 8 | CP3 | A0 채택/보류/폐기 사용자 결정 |

**주의:** G-C5는 요약 품질 전체를 보장하지 않는다. ROUGE 단독 판정 금지. 슬롯·사실 보존·압축률·사람 검토를 함께 본다.

> **2026-11-06 실측 주의:** target 감사에서 `원문 대비 슬롯 보존율`과 `요약 슬롯의 grounding rate`가 크게 다르게 나왔다. 전자는 요약이 원문 숫자를 의도적으로 생략해 낮아지고, 후자는 환각 여부를 본다. G-C5의 "보존" 정의는 CP3-1에서 확정한다. 임계값을 임의로 바꾸지 않는다.

## 4. Public API (초안)

```python
# eval/slot_verify.py
def extract_slots(text: str) -> list[Slot]: ...
def verify_summary(source: str, summary: str) -> SlotReport: ...
# report: preserved, missing, new, rejected, details

# runner/c5_summary_eval.py
def summarize_a0(passage: str) -> str: ...
def evaluate_split(records: list[dict]) -> dict: ...
```

- 입력/출력은 JSONL.
- `SlotReport.rejected=True`이면 상위 호출자는 **원문을 그대로 저장**한다.
- API는 JEV에 직접 연결하지 않고, 어댑터 경계만 정의한다.

## 5. 구현 순서

1. **F5 target 슬롯 감사** — 모델 없이 2,000쌍 분석
2. **슬롯 추출·검증기 + 단위 테스트** — G-C5의 핵심
3. **split 고정** — deterministic, test 200
4. **A0 추출형 baseline** — 로컬 CPU
5. **A0 평가·사람 표본 50** — `reports/C5_summary.md`
6. **CP3-1** — A0 채택/보류 결정
7. **C3 A1 T5Gemma 2 LoRA** — 별도 승인 후
8. **C3 A2 EG2 adapter** — A1 대비 이득 있을 때만
9. **CP3-2** — 최종 채택

## 6. 예상 비용·시간

| 단계 | 호스트 | 예상 |
|---|---|---|
| target 감사 | 로컬 CPU | 10~20분 |
| 슬롯 검증기·테스트 | 로컬 CPU | 0.5~1일 |
| A0 baseline | 로컬 CPU | 0.5일 |
| 사람 표본 50 | 사용자 | 1~2시간 |
| C3 A1 probe | VPS/로컬 CPU | 0.5~1일 |
| C3 A1 LoRA | VPS/GPU 필요 시 | 별도 승인 |

**1차(A0+검증기)는 GPU·외부 API 없이 진행 가능**하다.

## 7. 데이터·윤리

- F5 데이터는 P0(공개·합성)만 사용한다.
- 기존 메모리 저장소의 (원문, 저장문) 쌍은 P1이므로 **사용하지 않는다**.
- target 감사 결과는 통계·ID·슬롯 유형만 보고하고 원문 전체를 외부에 보내지 않는다.
- AI Hub 라이선스는 D-049 확인 범위 내에서 사용한다.

## 8. 승인 요청

**권장: 1~3단계(A0+슬롯 검증기) 먼저 승인.**  
C3 A1(T5Gemma 2 LoRA)은 A0 결과와 자원을 본 뒤 별도 승인한다.

승인 시 다음을 진행한다.
- F5 target 슬롯 감사
- `eval/slot_verify.py` + 단위 테스트
- deterministic split
- A0 baseline + `reports/C5_summary.md`

승인 전에는 **코드·학습을 시작하지 않는다.**
