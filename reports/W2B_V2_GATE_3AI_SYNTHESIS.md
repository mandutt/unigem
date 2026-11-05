# Wave 2B V2 reader-only gate — 3-AI 검토 종합

- 작성일: 2026-11-05 (KST)
- 라운드: `w2b_v2_gate`
- 검토 모델: **GLM 5.3 Flash(max)**, **Claude Sonnet 5.5(medium)**, **GPT-6 Luna(xhigh)**
- 검토 요청서: `reports/EXTERNAL_REVIEW_W2B_V2_GATE_2026-11-05.md`
- 요청서 기준 코드: `9d1aba6`; 검토 시점 HEAD: `ac1fd82` (shallow clone에서 `9d1aba6`은 해석 불가)
- 원문:
  - GLM: `docs/hoplite/w2b_v2_gate/2026-11-05_hoplite-review_w2b_v2_gate_GLM.md` (15,189자)
  - Sonnet: `..._SONNET.md` (20,641자)
  - Luna: `..._LUNA.md` (19,123자)
- **판정: 3/3 B — recipe-level PASS with caveats.** C(exploratory/reject)는 없음.
- GLM은 보고서 작성 후 서버 오류로 thread status가 failed가 됐지만, diff에서 보고서를 정상 회수했다.

---

## 1. 한눈에 보는 결론

세 모델 모두 **V2 reader-only gate의 숫자·절차는 유효**하다고 봤다. 따라서 D-071은 **“V2 reader-only recipe-level PASS”**로 유지한다.

그러나 세 모델 모두 다음에는 동의하지 않는다.

- “Kspon short 4시간 데이터 효과”라고 부르는 것
- “Kspon domain 효과” 또는 “short-length 효과”라고 부르는 것
- “화자 독립 일반화”를 주장하는 것
- 같은 test 2,400을 다시 사용해 20-epoch·seed43·LoRA를 **confirmatory**로 부르는 것

즉 **gate는 유효하지만 estimand는 “이 recipe(6h→10h, 12 epoch, V2)”**이다. “데이터만의 인과 효과”가 아니다.

---

## 2. 모델×질문 판정 행렬

| 질문 | GLM | Sonnet | Luna | 종합 |
|---|---|---|---|---|
| Q1 Gate PASS 지위 | B: recipe-level PASS | B: recipe-level PASS with caveats | B: caveat-qualified PASS | **B / recipe-level PASS** |
| Q2 Compute·domain·length 귀속 | B: control 필요 | B: control 필요 | B: matched-budget 필요 | **B / 귀속 불가** |
| Q3 V2 vocab 2-pass | B: 유지·동결 | B: 유지·label | B: 유지·동결 | **B / V2-conditioned** |
| Q4 B3-nat | B: dev-only 서술만 | B: no detectable difference only | B: no equivalence claim | **B / 탐지 불가만** |
| Q5 Test 재사용 | B: 1회 confirmatory, 이후 exploratory | B: 1회 confirmatory, 이후 exploratory | B: 1회 confirmatory, 이후 exploratory | **B / 재사용 금지** |
| Q6 다음 우선순위 | matched reader control → domain/length → seed43 → 20ep → LoRA | B0′-38, B0′-20, Kspon long; seed43 | matched step+audio → domain/duration → seed43 → 20ep → LoRA | **matched control first** |
| Q7 LoRA | 구현·smoke 가능, confirmatory 차단 | 구현 가능, fresh holdout 필요 | 구현 가능, matched no-LoRA 필요 | **구현 가능 / claim 차단** |
| Q8 보고·주장 | caveat 5개 부착 | “sealed” 표현 수정 | “recipe-level” 유지 | **caveat 필수** |

---

## 3. 공통 Must-fix

| ID | 지적 | 필수 조치 | 우선순위 | LoRA 차단 |
|---|---|---|---|---|
| **MF-A** | B0′ 6h vs B3 10h: step 3.13×, exposure 1.67×, Kspon domain, short length가 결합 | **step-matched(B0′-38)**와 **exposure-matched(B0′-20)**를 별도 실험으로 실행; “data/short/domain effect” 금지 | **P0** | causal claim 차단 |
| **MF-B** | test 2,400은 1회 사용; 화자 독립 아님 | “in-domain procedural holdout, used once”로 표기; 이후 결과는 exploratory; 새 confirmatory claim에는 fresh holdout | **P0** | confirmatory LoRA 차단 |
| **MF-C** | V2 vocab은 2-pass selection-dependent | V2 vocab·manifest·checkpoint 동결; 결과를 “V2 vocab-conditioned”로 표기; 새 arm은 고정 V2로 선택 | **P1** | 아니오 |
| **MF-D** | B3-nat는 dev-only, CI가 0 포함 | “dev에서 탐지 가능한 sampler 차이 없음”으로만 표기; test 재평가 금지 | **P1** | 아니오 |
| **MF-E** | test refs와 short-train refs의 **text-level overlap** | Sonnet의 136/2,400(5.7%)을 프로젝트 normalizer로 재현; duplicate 제거 sensitivity Δ 보고 | **P0** | confirmatory claim 차단 |
| **MF-F** | 10.0221h(frames) vs 10.0024h(manifest 합) | 공식 시간 정의 고정; 보고서에 둘 다 표기 | **P2** | 아니오 |
| **MF-G** | speaker/session overlap 확인 불가 | 모든 대외 문장에 “not speaker-independent” 명시 | **P1** | speaker claim 차단 |
| **MF-H** | LoRA 비교의 compute confound | LoRA는 **matched no-LoRA comparator**와 fresh holdout으로만 confirmatory | **P1** | confirmatory 차단 |

---

## 4. 모델별 고유 지적

### GLM

- 사전등록·test freeze·커밋 순서를 직접 대조해 **절차 무결성**을 강조.
- 화자 군집을 ICC=1 극단으로 정성 검산해도 CI 하한이 +4~5%p 수준 → gate를 뒤집기 어렵다고 봄.
- 추가 control으로 **B0′-rep10**(Wave1 6h를 반복·서브샘플링해 10.02h로 구성, 12 epoch)을 제안. B3와 compute를 완전히 맞추는 대안.
- **시간 회계 불일치**: `ten_hours_est` 10.0221h(frames 기준) vs manifest 합 10.0024h. 0.2% 차이로 결론 불변.

### Sonnet

- **Text-level overlap 136/2,400(5.7%)**을 자체 정규화로 발견. 중복 136개(445자)에서 B0′ 0.584 vs B3 0.265; 중복 제거 시 Δ **9.74→9.48%p**. 치명적이지 않지만 **감사 누락**.
- **B0′-38(step-matched)**과 **B0′-20(exposure-matched)**을 별도 실험으로 명확히 구분.
- Kspon natural/long-clip 4h control이 “short” claim을 검증하는 유일한 control이라고 봄.
- B3-nat test는 불필요; test 재사용은 confirmatory 가치 없음.
- LoRA confirmatory에는 **fresh holdout**이 필요하다고 명시.

### Luna

- “데이터 효과”를 말하려면 **step과 cumulative audio seconds를 동시에 맞춘 사전등록 비교**가 필요하다고 봄. 하나만 맞추면 unmatched quantity를 명시해야 함.
- **Wave-1-only replay/resampling control**을 제안: 같은 update/audio budget을 Wave1 반복에 쓰는 control.
- Kspon long vs short, non-Kspon short control로 domain/duration 분리.
- Seed 43은 robustness 보조; 20-epoch는 convergence 실험이며 compute-matched가 아님.
- LoRA는 구현·GPU smoke 가능, efficacy claim은 matched no-LoRA + fresh holdout 후.

---

## 5. Gate의 최종 지위

### 유지

D-071은 다음 문장으로 유지한다.

> **V2 reader-only recipe-level gate PASS.**  
> B3(10h incl. Kspon short, balanced, 12 epoch) vs B0′(6h Wave1, 12 epoch), seed 42, V2 vocab.  
> Dev Δ +10.187%p (CI +9.107~+11.328), test Δ +9.737%p (CI +9.228~+10.258), FLEURS dev −0.216%p.  
> Test는 B3 freeze 후 1회 사용.

### 금지 문장

- “Kspon short 4시간 데이터 효과를 입증했다.”
- “Kspon domain 효과다.”
- “short-length 분포 효과다.”
- “화자 독립 일반화에서 +9.7%p.”
- “20 epoch/seed43/LoRA도 같은 test에서 confirmatory PASS.”

### 허용 문장

- “이 recipe(6h→10h, 12 epoch, V2)에서 dev/test CER가 크게 개선됐다.”
- “개선은 data·domain·length·compute가 결합된 **recipe effect**이며, 인과 귀속은 아직 분리되지 않았다.”
- “test는 in-domain procedural holdout으로 1회 사용됐고, 화자 독립은 확인할 수 없다.”

---

## 6. 다음 실험 우선순위

3-AI 공통 권고를 반영한 순서:

1. **Matched-budget reader controls**
   - **B0′-20**: exposure-matched (5,960 steps, 120.0h; B3-12 120.3h)
   - **B0′-38**: step-matched (11,324 steps, 228.0h; B3-12 11,196 steps)
   - 둘 다 Wave1 6h, V2 vocab, same init, seed 42, natural sampler, full budget(patience 99)
   - dev 500 전용; test 사용 금지
2. **Kspon long-clip 4h control** — domain vs short-length 분리
3. **Wave1 replay/rep10 control** (GLM 제안, 선택) — “새 4h” vs “알던 6h 반복” 분리
4. **Seed 43** — robustness; matched recipe에서 보조
5. **20-epoch 3-arm** — convergence 질문이 남을 때만; compute-matched 아님
6. **LoRA** — 구현·GPU smoke는 병행 가능; confirmatory는 matched no-LoRA + fresh holdout 후

현재 **1번(B0′-20/B0′-38)을 D-072로 사전등록하고 실행**한다.

---

## 7. Test overlap 감사 — 즉시 조치

Sonnet의 ad-hoc 결과를 프로젝트 도구로 재현한다.

- 대상: test 2,400 refs vs short V2 train refs 5,079
- 정규화: `eval/normalize.py::normalize_nospace` 고정
- 보고:
  - exact duplicate 수/비율
  - duplicate utterance의 B0′/B3 CER
  - duplicate 제거 후 전체 CER와 Δ
  - near-duplicate(문자 편집 거리 기준) 별도 표
- 결과를 `reports/provenance/W2B/overlap_final.json`에 추가하고, `W2B_v2_gate_results.md`에 sensitivity로 기록
- **주의:** Sonnet의 136/2,400·9.48%p는 자체 정규화 기반 추정이며, 프로젝트 정본 수치가 아니다.

---

## 8. 원문·재현

- 요청서: `reports/EXTERNAL_REVIEW_W2B_V2_GATE_2026-11-05.md`
- 원문 3종:
  - `docs/hoplite/w2b_v2_gate/2026-11-05_hoplite-review_w2b_v2_gate_GLM.md`
  - `docs/hoplite/w2b_v2_gate/2026-11-05_hoplite-review_w2b_v2_gate_SONNET.md`
  - `docs/hoplite/w2b_v2_gate/2026-11-05_hoplite-review_w2b_v2_gate_LUNA.md`
- Thread 기록: `docs/hoplite/w2b_v2_gate/threads.json`
- Gate 결과: `reports/W2B_v2_gate_results.md`
- Dev 결과: `reports/W2B_v2_dev_results.md`
- 검토 요청서 커밋: `9f1ed7d`
- 3-AI 원문 커밋: `59f05c8`
- 최신 커밋(작성 시점): `28fb54d`

---

## 9. 한 줄 요약

> **Gate는 “이 recipe”에 대해 유효하고 3/3 B로 인정된다. 그러나 “short 4h 데이터 효과”는 아직 증명되지 않았다. B0′-20(exposure)과 B0′-38(step) control로 compute를 분리하고, Kspon long-clip control로 domain/length를 분리하기 전까지는 “recipe effect”로만 말해야 한다.**
