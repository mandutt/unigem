# STT 연구 트랙 — 동결·보류 (2026-11-06)

> **상태: FROZEN / HOLD**
>
> unigem의 EG2 기반 STT 연구 트랙은 2026-11-06부터 **동결·보류**한다.
> 새 학습, GPU 대여, 데이터 다운로드·전처리, 모델·코드 변경, 새 test 평가를 시작하지 않는다.
> 기존 문서·체크포인트·feature cache·provenance는 **삭제하지 않고 보존**한다.

## 왜 동결했나

1. **별도 모델 대비 이득이 제한적이다.**
   - 제품 STT 경로는 이미 **komixv2/whisper**(D-057)다.
   - EG2 STT는 연구 트랙이며, 현재 10시간 조건의 best는 **26.3% CER**로 제품 기준(≤15%)에 미달한다.
2. **Sténo급 대규모 학습은 현 자원으로 무리다.**
   - Sténo: 3,205시간, 상위층 fine-tune, 13-state mix, 30k wordpiece, 4-gram LM.
   - 한국어 재현: 3,000시간급 데이터, **40~100 GPUh**, **$120~200+**, **1TB+ 저장**.
   - 현재: CPU-only, RAM 15.6GB, C 약 76GB / D 약 332GB 여유, GPU 없음, Modal $30 크레딧.
3. **저장·전처리 병목이 크다.**
   - 3,000시간 feature cache는 4-layer 기준 **약 2.1TB**, 13-state 기준 **약 6.8TB**.
   - FLAC raw audio로 줄여도 **170~220GB**이며, feature cache 문제는 해결되지 않는다.
4. **현재 남은 개선 여지가 제품 전환을 정당화하지 못한다.**
   - LoRA 10시간 기대: **23~26% CER** (1~3%p 개선).
   - frozen/LoRA 구조 실험은 가능하지만, 제품 경로를 바꿀 수준은 아니다.

## 동결 범위

**중단**
- 새 STT 학습(B0′/B3/B3-nat/LoRA/대규모)
- GPU 대여(Modal/L40S/A100 등)
- 새 음성 데이터 다운로드·전처리·feature 추출
- 새 test 평가 및 test 2,400 재사용
- STT 관련 코드·모델·런타임 변경

**허용**
- 기존 문서·결과·checkpoint·feature cache의 **읽기 전용 검토**
- 동결 상태 문서화, 오류·경로 정리
- 제품 경로(komixv2/whisper) 운영
- 사용자 명시 승인 후 별도 프로젝트로 재개

## 문서 지도

| 위치 | 내용 |
|---|---|
| [`STATUS.md`](STATUS.md) | 현재까지의 진행 상황·최종 결과·동결 사유·재개 조건 |
| [`INDEX.md`](INDEX.md) | STT 관련 문서 전체 색인 |
| [`plans/`](plans/) | Wave 2A/2B/2C 설계 문서 |
| [`reports/`](reports/) | STT 실험 보고서·검토 요청서·분석 |
| [`hoplite/`](hoplite/) | Hoplite 3-AI 검토 원문·threads·dispatch 로그 |
| [`../decisions.md`](../decisions.md) | 전역 결정(D-057, D-067~D-079 등) |

## 재개 조건

다음이 모두 충족되고 **사용자 명시 승인**이 있을 때만 재개한다.

1. **새 사전등록**: 데이터·목표 CER·평가셋·gate·중단 규칙.
2. **자원 계획**: GPU 종류·예상 GPUh·예산·저장 위치(1TB+).
3. **데이터 계획**: 3,000시간급 확보·라이선스(연구/상업)·전처리 일정.
4. **제품 정당성**: komixv2/whisper 대비 명확한 이득 또는 별도 제품 요구.
5. **새 결정 등록**: D-079 해제 및 후속 결정.

재개하더라도 **기존 test 2,400은 confirmatory에 재사용하지 않는다.** 새 holdout이 필요하다.

## 현재 상태

- 활성 STT 학습·watchdog: **없음**
- 마지막 STT 실험: `b3long_sm_v2_s42` 완료(2026-11-06 00:42:50)
- 최종 dev CER: **0.279433** (best 0.2790)
- 최신 관련 결정: **D-078**(step-matched 결과), **D-079**(동결)
- 제품 STT 경로: **komixv2/whisper 유지(D-057)**
