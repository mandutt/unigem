# Wave 2B V2 — domain/length controls 3-AI 종합 (w2b_domain_length)

- 작성: 2026-11-05 22:46 KST
- 라운드: `w2b_domain_length`
- 검토 모델: **GLM 5.3 Flash(max) / Opus 5.5(medium) / GPT-6 Luna(xhigh)**
- 검토요청서: `docs/STT/reports/EXTERNAL_REVIEW_W2B_DOMAIN_LENGTH_2026-11-05.md` (740줄)
- 원문:
  - `docs/STT/hoplite/w2b_domain_length/2026-11-05_hoplite-review_w2b_domain_length_GLM.md` (244줄/18,398자)
  - `..._OPUS.md` (317줄/23,973자)
  - `..._LUNA.md` (129줄/22,522자)
- **종합 판정: 3/3 B — caveat-qualified, exploratory evidence.** C(전면 reject)는 없음.
- **새 학습·디코딩은 이 종합에서 실행하지 않았다.** 단, text-overlap은 로컬 read-only 감사로 종결했다(§4).

---

## 1. 한 줄 결론

> **Kspon long과 Zeroth long의 same-length 비교는 “Kspon-source/in-distribution 코퍼스 효과”를 강하게 지지한다. 그러나 “domain”이라는 좁은 인과 라벨은 과대하고, short-length 효과는 optimizer step confound 때문에 아직 미확정이다. 공통 최우선 조치는 step-matched B3-long이며, LoRA 구현·GPU smoke는 병행 가능하지만 confirmatory LoRA에는 fresh holdout과 matched no-LoRA가 필요하다.**

---

## 2. 모델별 종합 판정

| 항목 | GLM | Opus 5.5 | Luna |
|---|---|---|---|
| 전체 | **B** | **B** | **B** |
| 결론 성격 | recipe PASS 유지 + caveat | accept with caveats | caveat-qualified exploratory |
| domain | B — corpus-source effect | B — Kspon-source advantage | B — source/corpus association |
| length | A(판정 옳음) + run | B — undetermined | B — undetermined |
| Zeroth-long 대체 | B | B | B |
| V2 | B | B | B |
| test 재사용 | B | B | B |
| B0′ controls | B | A/B (B wording) | **C for broad “compute ruled out”; B for narrow** |
| sampler | B | B | B |
| text overlap | **C → short_v2 reproduced** | B (reproduced) | **C (not independently reproduced)** |
| Zeroth paradox | B | B | B |
| next priority | step-matched B3-long | step-matched B3-long | step-matched B3-long |
| public sentence | B (revised) | B (revised) | **C as written** |

**해석:** 전체 B는 “현재 evidence를 exploratory로 수용”한다는 뜻이지, “domain 인과 확정”이나 “length 확정”이 아니다. Luna의 C는 주로 **문장 과일반화**와 **text-overlap 미재현**에 대한 것이고, 실제 수치·설계 결함은 GLM/Opus와 같은 방향이다.

---

## 3. 공통 Must-fix

| ID | 지적 | 공통 조치 | 우선순위 | LoRA 차단 |
|---|---|---|---|---|
| **MF-1** | short vs long: B3-nat 11,196 vs B3-long 5,568 optimizer steps | **step-matched B3-long**을 실행. `batch=2, grad_accum=2`, 12 epoch, 928 steps/epoch = **11,136 steps**; final dev를 primary로 사전등록. exact pair를 원하면 B3-nat도 11,136으로 cap/재실행하고 cosine `T_max`를 step 단위로 고정 | **P0** | 아니오 (length claim만 차단) |
| **MF-2** | “domain” 라벨이 너무 넓음 | 문장을 **“Kspon-source (in-distribution) training-data advantage at matched 8–16s”**로 한정. 화자·녹음·문체·전사 규약·OOV·selection asymmetry를 bundle로 명시 | **P0 (public wording)** | 아니오 |
| **MF-3** | test 2,400은 1회 사용, 화자 독립 아님 | “Kspon eval_clean procedural holdout, not speaker-independent, used once”로 표기. 새 confirmatory claim에는 **fresh holdout**. spare 90 불충분 | **P0 (confirmatory)** | **예 — confirmatory LoRA만** |
| **MF-4** | text-level overlap | **short_v2 부분 종결**: test **136/2,400 = 5.67%**, 445/38,224 chars; dev 26/500 = 5.2%; 중복 제거 test Δ **+9.4762%p** (전체 +9.7373). Wave1·Kspon-long·Zeroth-long exact overlap은 로컬 감사에서 **0**; short_v1 manifest는 부재. near-duplicate는 미실시 | P1 | 아니오 (단, old test의 unqualified confirmatory wording 차단) |
| **MF-5** | non-Kspon short 4h 부재 | **현재 주장에는 필수 아님.** domain-at-short/full factorial claim에만 필요. 4h 새 코퍼스보다 **1.66h hour-matched** Zeroth-short vs Kspon-short control이 저렴 | P1 conditional | 아니오 |
| **MF-6** | V2 vocabulary selection dependence | 모든 absolute CER에 **“V2-vocabulary-conditioned”** 태그 + arm별 OOV(2.3753/7.33/4.47%) 병기. future arm도 V2 고정; vocab 변경 시 comparator 재실행 | P2 | 아니오 |
| **MF-7** | B0′ controls는 step과 exposure를 동시에 맞추지 않음 | “in these controls, increasing either alone did not close the gap”로 한정. **“compute/exposure ruled out” 금지** | P1 wording | 아니오 |
| **MF-8** | LoRA confirmatory confound | 구현·GPU smoke는 가능; confirmatory claim에는 **fresh holdout + matched no-LoRA comparator** (same data/steps/exposure/schedule/vocab/seed) | P1 | **confirmatory 차단** |
| **MF-9** | B3-zeroth-long의 해석 | “Zeroth (already in Wave1), long”으로 표기. **non-Kspon new-source control이 아님**; domain-at-short 미검증. same-corpus redundancy·long-only·OOV·optimization을 배제하지 말 것 | P2 | 아니오 |

---

## 4. Text-overlap — 종결 상태

### 4.1 검토자 재현

- **GLM**: project normalizer로 test↔short_v2를 재계산 → **136/2,400 = 5.67%**; dedup Δ **+9.4762%p**; dev 26/500.
- **Opus**: 동일 결과 **136/2,400**, 445/38,224 chars; dedup Δ **+9.476%p**; dev 26/500; 중복의 대부분이 3–6자 backchannel.
- **Luna**: “text overlap이 아직 재현되지 않았다”고 평가했지만, 이는 Luna가 코드를 실행하지 않은 데서 온 것이며, GLM과 Opus의 **독립 재현**으로 short_v2 범위는 종결됐다.

### 4.2 로컬 전수 감사 (이번 종합에서 read-only 실행)

`reports/provenance/W2B/overlap_text_audit.json`:

| 대상 | short_v2 | Wave1 | Kspon long | Zeroth long | short_v1 |
|---|---:|---:|---:|---:|---:|
| test 2,400 | **136행 / 445자 / 5.67%** | 0 | 0 | 0 | manifest 없음 |
| dev 500 | **26행 / 86자 / 5.2%** | 0 | 0 | 0 | manifest 없음 |

- dedup test: B0′ **0.356997**, B3 **0.262236**, Δ **+9.4762%p** (`overlap_text_audit_dedup.json`)
- **전체 exact overlap은 short_v2에만 존재**; Wave1/long/zeroth-long은 0.
- **미완**: near-duplicate/fuzzy match, short_v1 manifest, dedup CI. 그러나 exact short_v2 감사는 종결.

**판정:** MF-4의 “short_v2 136/2,400”은 **사실로 확정**. 전체 exact 감사도 로컬에서 0으로 확인. near-duplicate만 residual.

---

## 5. 합의된 해석

### 5.1 Domain — 강한 association, 좁은 인과 라벨 금지

- B3-long **0.283946** vs B3-zeroth-long **0.365571**; Δ **−8.1625%p**, CI **[−9.2063,−7.1645]**, 0 제외.
- 같은 8–16초, 같은 4h, 같은 10h, natural sampler, 거의 같은 step(5,568 vs 5,676).
- **“Kspon-source/in-distribution advantage at matched 8–16s”**로 말할 수 있다.
- **“domain alone” / “mechanism identified”**로 말할 수 없다. bundle: 발화 스타일, eval-corpus match, 전사 규약, 화자·채널, OOV/selection.
- **Zeroth는 Wave1에 이미 1,534개** 포함 — “new non-Kspon source”가 아니라 “same-corpus 추가”다.
- **domain-at-short**는 미검증.

### 5.2 Length — 미확정

- B3-nat **0.263314** vs B3-long **0.283946**; B3-nat +2.0632%p, CI 0 제외.
- 그러나 steps **11,196 vs 5,568**.
- Opus의 per-bin 분석: short refs에서 차이가 크고 long refs에서 거의 사라짐 — length-distribution match 가능성.
- Opus의 추가 신호: B3 balanced epoch6(약 5,598 steps, 0.2814)와 B3-long final(5,568 steps, 0.2839)이 비슷함 — step/annealing confound 시사.
- **어느 쪽도 확정 아님.** step-matched B3-long이 결정적.

### 5.3 B0′ controls — 좁은 결론

- B0′-20/38도 B3에 미치지 못함(9.72/10.01%p).
- 그러나 B0′-20은 exposure만, B0′-38은 step만 맞춤; 둘을 동시에 맞추지 않음.
- **“in these controls, increasing either alone did not close the gap”**가 정확.
- **“compute/exposure ruled out”**는 Luna가 C로 지적; 사용 금지.

### 5.4 Test·V2·LoRA

- test 2,400은 **used once**, in-domain, not speaker-independent. 새 control은 test 미사용.
- **V2-vocabulary-conditioned**; OOV by arm.
- LoRA **구현/GPU smoke**는 지금 가능; **confirmatory**는 fresh holdout + matched no-LoRA.

---

## 6. 이견·모델별 고유 지적

| 항목 | GLM | Opus | Luna |
|---|---|---|---|
| text overlap | short_v2 **재현·종결** | short_v2 **재현** | **미재현**; C |
| B0′ compute | B | B (A/B) | **C for broad claim**, B narrow |
| step-match | ga2, patience4, ≈3h | ga2, 12ep, patience99, final | **exact 11,136 cap; B3-nat cap; T_max step-based** |
| 추가 진단 | MF-I best/final 기준, MF-J Zeroth loss/holdout | per-bin 분석, epoch6 비교 | 공통 update budget, cosine T_max, effective batch |
| public sentence | B 수정안 | B 수정안 | **C as written** |

**Synthesis 결정:** 
- text overlap은 **GLM+Opus의 독립 재현 + 로컬 전수 감사**로 short_v2 종결. Luna의 C는 “감사 미실행”에 대한 방법론적 caveat로 기록.
- step-match는 **Luna의 exact budget**을 채택하는 것이 가장 안전: `batch2/ga2`, 11,136 steps, B3-nat cap/재실행, `T_max`를 actual update 수로 고정, final dev primary.
- B0′ 표현은 Luna의 좁은 문장을 채택.

---

## 7. 대외 주장 문장 (수정안)

> “EG2 reader-only 파일럿에서 Wave1 6h에 Kspon short 4h를 추가한 B3는 B0′ 대비 dev 500에서 +10.19%p, 봉인 test 2,400에서 +9.74%p(95% CI [+9.23,+10.26])의 CER 개선을 보였다. 이 개선은 optimizer step을 맞춘 B0′-38(+10.01%p 유지)과 exposure를 맞춘 B0′-20(+9.72%p)에서도 유지됐다. 다만 이 control들은 step과 exposure를 동시에 맞추지는 않았으므로 ‘compute/exposure가 배제됐다’고 말하지 않는다. 같은 8–16초·4h·거의 동일 step 조건에서 Kspon long 4h 추가 arm은 Zeroth long 4h 추가 arm보다 dev에서 8.16%p 우수했고, Zeroth arm은 B0′와 유의한 차이가 없었다. 이는 **Kspon-source/in-distribution 코퍼스 효과**를 지지하지만, ‘domain alone’의 인과 확정은 아니다. short-length 고유 효과는 step 수 약 2배 confound 때문에 **미확정**이며 step-matched control이 필요하다. test는 in-domain procedural holdout(화자 독립 아님)으로 1회 사용됐고, text overlap 136/2,400(5.7%)을 제거해도 Δ는 +9.48%p로 결론이 유지된다. 모든 신규 control은 single-seed·V2-conditioned·dev-only exploratory다.”

**금지 문장**:
- “short 4h 데이터 효과가 입증됐다.”
- “short-length 효과 = 2.06%p.”
- “화자 독립 일반화 +9.7%p.”
- “Kspon domain alone이 원인이다.”
- “compute/exposure가 배제됐다.”
- “B3-zeroth-long이 non-Kspon short control과 동등하다.”
- “LoRA가 필요/불필요하다.”

---

## 8. 다음 우선순위

1. **step-matched B3-long** (P0)
   - `batch=2, grad_accum=2`, 12 epochs, patience 99, final dev primary.
   - 928 steps/epoch × 12 = **11,136 steps**.
   - exact pair를 원하면 B3-nat도 11,136으로 cap/재실행, cosine `T_max=11,136`.
   - residual: effective batch 4 vs 8; report.
   - dev 500 only; test 금지; 사전등록.
2. **text-overlap residual** (P1)
   - exact short_v2/Wave1/long/zeroth 종결(§4); near-duplicate + short_v1 + dedup CI만 남음.
3. **LoRA 구현 + GPU smoke** (병행 가능)
   - confirmatory는 fresh holdout + matched no-LoRA 후.
4. **1.66h hour-matched short-domain** (conditional)
   - Zeroth-short 1.012클립/1.657h vs Kspon-short duration/step-matched.
   - non-Kspon 4h/FLEURS는 지금 불필요; 필요 시 별도 승인.
5. **seed 43 / 20-epoch / B0′-rep10** — 후순위.

---

## 9. 결정 필요

| ID | 결정 | 선택지 | 권고 |
|---|---|---|---|
| R-1 | step-matched B3-long 실행 | 지금 / 보류 | **지금** (≈1.5~2h CPU; ga2) |
| R-2 | B3-nat cap/재실행 | exact pair / historical reference만 | **exact pair 권장** (Luna) |
| R-3 | LoRA 구현·GPU smoke | 병행 / 대기 | **병행 가능** |
| R-4 | non-Kspon short 4h | 지금 / 연기 | **연기** (1.66h control이면 충분) |
| R-5 | fresh holdout | 지금 설계 / LoRA 후 | **LoRA confirmatory 전** |
| R-6 | 대외 문장 | §7 / 수정 | **§7 사용** |

---

## 10. 산출물

- 원문 3종: `docs/STT/hoplite/w2b_domain_length/2026-11-05_hoplite-review_w2b_domain_length_{GLM,OPUS,LUNA}.md`
- 검토요청서: `docs/STT/reports/EXTERNAL_REVIEW_W2B_DOMAIN_LENGTH_2026-11-05.md`
- text overlap: `reports/provenance/W2B/overlap_text_audit.json`, `overlap_text_audit_dedup.json`
- 기존 결과: `docs/STT/reports/W2B_domain_length_controls.md`, `docs/STT/reports/W2B_b0_matched_controls.md`
- thread 기록: `docs/STT/hoplite/w2b_domain_length/threads.json`
