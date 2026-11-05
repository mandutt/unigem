# 외부 AI 검토 보고서 — Wave 2B V2 reader-only 후속 (w2b_domain_length)

- **검토자:** GLM (OpenRouter `z-ai/glm-5.3-flash`, Hoplite 에이전트) — 독립 신규 라운드, 과거 w2b_v2_gate 스레드와 무관
- **검토일:** 2026-11-05 (KST)
- **요청 문서:** `reports/EXTERNAL_REVIEW_W2B_DOMAIN_LENGTH_2026-11-05.md` (740줄 전체 대조 완료)
- **워크스페이스 동기화:** `git fetch origin` → `git pull --ff-only origin main` → **"Already up to date"**. HEAD = **`857eed071ff9be82e41d705862c0b17659ec3bf4`** ("chore: prepare w2b_domain_length review dispatch", 2026-11-05 22:29:30 +0900). 요청서 기준 커밋은 `069879f`이며, HEAD는 여기에 디스패치 준비 커밋이 얹힌 상태. `git status` 깨끗함(본 보고서 파일 외 변경 없음).
- **검토 성격:** 상담 전용. 요청서 외 파일은 **수정하지 않았고**, 학습·디코딩 재실행도 하지 않았다. 아래 "검증 수행 내역"은 저장소 산출물(provenance JSON, 예측 파일, 매니페스트, 정규화기 코드)을 **읽기 전용으로 재계산**한 것이다.

---

## 검증 수행 내역 (본 라운드에서 실제로 확인한 것)

모두 `python3` 읽기 전용 계산이며, 프로젝트 정규화기 `eval/normalize.py`의 `normalize_nospace` + `_edit_distance`를 그대로 사용했다.

1. **dev CER 7개 arm 전수 재계산** — `reports/provenance/W2B/devpred_*.json`의 원본 `ref`/`pred`를 정규화기→edit distance 체인으로 재계산. 결과: B0′ 0.370084, B3 0.268214, B3-nat 0.263314, B3-long 0.283946, B3-zeroth-long 0.365571, B0′-20 0.365442, B0′-38 0.368279 — **보고값과 소수 6자리까지 일치**.
2. **bootstrap 12개 비교 재확인** — `domain_controls_bootstrap.json`, `matched_bootstrap.json`의 point/CI가 요청서 표기와 전부 일치 (−2.0632 [−2.9625,−1.1861], −8.1625 [−9.2063,−7.1645], +8.6138, +0.4513 [−0.2087,+1.1278], +9.7228, +10.0064 등).
3. **step·예산 회계 재확인** — `domain_controls_budget.json`: B3-long 12ep×464=5,568 steps(3,711클립, 1.494h), B3-zeroth-long 12ep×473=5,676(3,779클립, 1.517h), 참조 B3-nat/B3 933/ep=11,196, B0′ 298/ep=3,576. 노출은 B3-nat/B3/B3-long/B3-zeroth-long 모두 10h×12ep≈120h로 **이미 매칭** — length 비교의 confound는 정확히 "optimizer step 수" 하나다.
4. **text-level overlap 감사 재현 (MF-E의 short_v2 부분 종결)** — `testpred_b0p_v2_s42.json`의 test 2,400개 ref를 `normalize_nospace`로 정규화해 `data/wave2b/short_4h_v2.jsonl`(5,079개 학습 ref)과 정확 일치 비교:
   - 일치: **136/2,400 = 5.67%** — Sonnet 보고(136/2,400)와 **정확히 일치**.
   - 제외 민감도(test): B0′ 35.6997% vs B3 26.2236% → Δ **+9.4762%p** (전체 +9.7373%p, −0.261%p) — Sonnet의 "9.74→9.48" 주장 재현. 게이트 기준(Δ≥1.0%p, CI 하한>0)에는 영향 없음.
   - 추가 발견: **dev 500 중 26개(5.2%)**가 short_v2 학습 텍스트와 일치. 이 26개를 제외하면: B0′−B3 +10.187→+9.949%p, B3-nat−B3-long −2.063→−1.904%p, B3-long−B3-zeroth-long −8.163→−8.006%p — **모든 결론 방향 불변**. (B3-long/B3-zeroth-long은 short 데이터를 학습하지 않았으므로 domain 비교에는 이 중복이 원리적으로 무관.)
5. **vocab·test 구성 확인** — `vocab_v2.json` chars=1,329 ✓, `short_4h_v2_summary.json` 5,079클립/4.0016h/OOV 2.3753% ✓, `test_breakdown.json`에서 test 8–16s n=185, ≤4s 1,784/2,400=74.33% ✓, `test_freeze.json`에 "B3 selected on dev 500 before sealed test" 절차 기록 ✓.
6. **확인 불가(데이터 미수록)** — Wave1(2,384)·short_v1(5,119)·long_4h 매니페스트와 오디오/캐시는 repo에 없음(로컬 전용). 따라서 test↔**전체** 학습 refs 감사와 Zeroth-long arm의 품질 진단은 이 환경에서 불가.

---

## 0. 결론 (A/B/C/D)

**B — recipe-level PASS 유지 + caveats.** B3-long vs B3-zeroth-long이 주는 "Kspon 코퍼스 출처 효과(같은 long 길이·4h·거의 동일 step)" 근거는 강하고 수치는 전수 재검증됐다. "short-length 효과 미확정" 판정도 옳다. 단, (1) "domain" 표기를 corpus-source bundle로 명확화, (2) step-matched B3-long 1회(ga2, ≈3h CPU), (3) text-overlap 감사 종결 — short_v2 부분은 본 보고서에서 재현·종결(136/2,400, Δ 9.74→9.48%p, 결론 불변), Wave1 포함 전체 감사만 로컬 잔여 — 이 세 가지가 다음 단계의 조건이다.

---

## 1. Q1~Q11

### Q1. Domain 결론 — 판정: B

**(1) 판정:** "같은 long 8–16s, 같은 4h에서 Kspon이 Zeroth보다 8.16%p 우수하다"는 사실 진술은 **강하게 지지**된다. 다만 "Kspon domain 효과"라는 라벨은 넓다 — 정확히는 **"추가 4h의 코퍼스 출처(bundle) 효과"**다.

**(2) 근거:**
- 설계가 paired 비교로 깨끗하다: 길이(8–16s), 볼륨(4h), 10h 총량, natural sampler, V2 vocab, seed 42, 12ep/patience 4가 모두 동일하고 steps도 5,568 vs 5,676(1.9% 차)로 사실상 매칭. B0′-20/38에서 확인된 것처럼 이 스케일에서 step·exposure 차이는 dev를 거의 움직이지 않으므로, 남는 차이는 데이터 출처뿐이다.
- 재검증: dev 0.283946 vs 0.365571, Δ −8.1625%p CI [−9.2063,−7.1645] (JSON과 일치). 방향 일관성도 있다: B3-long은 B0′ 대비 +8.6138%p(CI 0 제외), B3-zeroth-long은 +0.4513%p(비유의) — 두 독립 비교가 같은 방향.
- 반대설명 점검: compute 부족 설명은 부정(B3-zeroth-long이 B0′보다 step·데이터 모두 많음), sampler 오염 없음(양쪽 natural), vocab 고정. 남는 교란은 corpus-source bundle(화자 구성, 녹음, 발화 스타일, 전사 규약, OOV 기반 클립 선택 차이 7.33% vs 4.47%)뿐이며, 이것이 곧 "domain"이 지칭하는 것이다. 참고로 Wave1 자체에 Kconf 2.1007h(3화자, D-061)가 있어 기반선도 코퍼스 혼합이라는 점은 bundle 해석에 붙어 다닌다.

**(3) 필수 수정:** 보고서·문장에서 "Kspon domain 효과"를 **"Kspon(코퍼스 출처) 효과 — 같은 long 길이·예산에서, bundle은 화자·녹음·문체·OOV를 포함"**으로 정의를 붙여 사용. 녹음/문체 등 하위 가설 분리는 지금 가능한 데이터로 불가능하므로 시도하지 않는다(우선순위 낮음).

**(4) 차단 여부:** 다음 단계 비차단, LoRA 비차단.

### Q2. Length 결론 — 판정: A(판정이 옳음) + 필수 실행

**(1) 판정:** "short-length 효과는 아직 확정할 수 없다"는 **옳다**. 2.06%p는 (length + step) 결합치다.

**(2) 근거:**
- B3-nat 11,196 steps vs B3-long 5,568 steps(2.01×). 노출은 양쪽 120h로 이미 매칭 — confound는 정확히 step 수다.
- B3-long은 ep9에서 best(0.2828) 후 patience 4로 종료 — 포화 흔적이 없어 step을 늘리면 개선될 여지가 실재한다.
- B3-balanced도 B3-long보다 −1.5732%p(CI 0 제외) — 같은 step confound를 공유하므로 length 근거로 인용 금지.
- 반대로 B0′ 계열(B0′-12→20→38)에서 step·exposure를 2~3배 늘려도 dev가 ≤0.5%p밖에 움직이지 않았다는 사실은 "step 효과가 작을" 가능성을 시사하지만, 이는 B0′(6h 반복) 관찰이지 B3 구성에 대한 직접 증거가 아니다.

**(3) 필수 수정 — step-matched B3-long 최소 설계:**
```
arm: b3long_ga2_v2_s42
python train/d5_reader.py \
  --features data/wave2b/feats_10h_kspon_long/fc.npz \
  --dev-features data/wave2b/feats_dev/fc.npz \
  --vocab-file data/wave2b/vocab_v2.json --retarget --arch base \
  --init-ckpt data/wave2b/ckpt_v2/w2a_fc_concat_s42_v2head.pt \
  --epochs 12 --patience 4 --batch 2 --grad-accum 2 \
  --seed 42 --threads 6 --device cpu --sampler natural \
  --ckpt-dir data/wave2b/ckpt_controls
예상: 928 steps/epoch × 12 = 11,136 steps (B3-nat 11,196과 −0.54%),
      노출 120.2h 동일, 12ep cosine 스케줄 형태 동일, 학습 ≈3.0h CPU.
```
- **왜 `grad_accum=2`인가:** batch=2(ga4)의 micro-batch 2를 유지하면서 효과적 배치만 8→4로 줄여 step을 맞춘다. `batch=1`(ga4, 3,711 micro/ep, 928 steps)도 같은 928 steps/ep이지만 micro-noise만 커진다. replay(동일 캐시 24 epoch)는 step을 맞추는 대신 노출·스케줄·데이터 반복 confound를 다시 만들므로 열등하다(노출은 이미 매칭돼 있으므로 어지럽힐 이유가 없다).
- **잔여 confound:** 효과적 배치 8→4. 이를 지우려면 2차로 B3-nat-ga2(효과 배치 4, 11,196 steps)를 하나 더 실행(≈3h). 1차 결과가 애매할 때만 실행.
- **사전등록 해석 규칙(실행 전 확정):** primary = final dev(ep12). B3-long-ga2 − B3-nat의 95% CI가 0을 제외하고 격차 ≥1%p → short-length 효과 "지지(배치 caveat 병기)". CI가 0 포함 또는 격차 ≤0.5%p → "step 효과로 설명 가능"으로 다운그레이드. best-dev도 민감도 병기. dev 500 전용, test 금지.

**(4) 차단 여부:** LoRA 구현·GPU 스모크 비차단. 길이가 확정되기 전 LoRA **confirmatory 주장**은 차단.

### Q3. Zeroth long 대체 — 판정: B

**(1) 판정:** 방법론적으로 **수용 가능**. 단 "non-Kspon short control의 대체"로 표기하면 안 되고, "domain at long" 비교의 확보로 표기해야 한다.

**(2) 근거:**
- 물리적 제약이 실재한다: Zeroth short 잔여 1,012클립/1.6574h(0–2s 0개, 2–4s 52, 4–6s 548, 6–8s 412). 4h를 채우려면 같은 데이터를 ~2.4회 반복해야 하고 그러면 반복 confound가 생긴다. (빈 테이블 수치는 repo에서 직접 검증 불가 — 매니페스트 미수록, 문서 기준.)
- 대체가 오히려 2×2 설계 중 더 결정적인 셀(domain at long)을 채웠고, 그 결과(−8.16%p)가 이번 라운드의 핵심 근거가 됐다.
- 결정적 결함이 아닌 이유: 현재 주장 범위(recipe PASS + domain-at-long + length 미확정)는 non-Kspon short 없이 성립한다. "domain at short"만 여전히 미검증이며 이 빈칸을 메우지 않는다는 사실만 정직하게 표기하면 된다.

**(3) 필수 수정:** 문서에 "Zeroth long은 non-Kspon short control이 아니다. domain-at-short는 미검증" 문구 고정. non-Kspon short 4h는 **지금 필수 아님(연기)**. 나중에 만들 경우 조건: 공개 코퍼스(FLEURS ko train 등), 0.5–8s 4h unique, eval 세트와 clip·텍스트 중복 0 확인, V2 고정(문자 OOV >5%면 append-only superset 검토), natural sampler, 12ep/seed 42 — short 데이터는 clip 수가 많아 B3-nat과 step이 자연 매칭된다(933/ep 근처).

**(4) 차단 여부:** 비차단.

### Q4. V2 vocabulary — 판정: B

**(1) 판정:** "모든 arm에 동일 V2 고정 → arm 간 비교는 공정"은 **타당**하다. absolute CER은 V2 조건부다.

**(2) 근거:** `vocab_v2.json` chars=1,329 확인, 모든 arm이 동일 vocab+동일 head remap(missing=0/unexpected=0)+동일 warm start. arm 간 차이(8.16%p, 2.06%p)는 vocab으로 오염되지 않는다. 반면 V2 문자 집합 자체가 short 선택+2-pass 루프의 산물이므로, 다른 vocab 절차였다면 절대값(0.26/0.28/0.37)은 달라질 수 있다. OOV 제외율의 arm 간 차이(2.3753%/7.33%/4.47%)도 corpus 구성의 일부로 남는다.

**(3) 필수 수정:** 게이트·컨트롤 보고서와 대외 문장에 **"V2-vocab-conditioned"** 태그 + 한 줄 정의("vocab은 short 선택에 의존하는 2-pass 절차로 구성, 모든 비교 arm에 동일 적용"). 미래 non-Kspon/FLEURS arm도 **V2 고정 원칙**(비교 가능성 유지). OOV가 과도할 때만 append-only superset(V1/V2 ID 보존)으로 확장하고, 그 경우 매칭 reference arm도 같은 superset으로 재실행.

**(4) 차단 여부:** 비차단.

### Q5. Test 재사용·confirmatory 지위 — 판정: B

**(1) 판정:** 현재 운용(test 2,400 1회 사용, 신규 컨트롤은 dev 전용)은 **올바르고**, "in-domain procedural holdout, used once" 표기도 **정확**하다.

**(2) 근거:** `test_freeze.json`에 "B3_v2_s42 selected on dev 500 before sealed test" 절차 기록. `domain_controls_budget.json` scope 필드 "sealed test 2,400 not used" 확인. testpred은 B0′/B3 2개 파일뿐(신규 arm 없음) — 내 재계산에서도 test CER 0.359643/0.262270, Δ +9.7373%p 일치.

**(3) 필수 수정:** 규칙 명문화 — (a) step-matched B3-long, non-Kspon short, LoRA를 **같은 test 2,400에 넣는 것은 전부 비-confirmatory**(multiplicity/forking paths)이므로 금지; (b) 새 confirmatory claim에는 **fresh holdout 필수**; (c) **spare 90은 불충분** — 표본이 너무 작고 동일 eval_clean 풀의 동일 절차 split이라 독립성이 없다(smoke 용도로만); (d) fresh holdout 후보로 Kspon eval_other가 있으나, 2A-lite에서 참고값(0.35143)으로 이미 접촉한 이력이 있으므로 사용 전 "선택·freeze 의사결정에 영향 없음" 감사를 하고, 기준(Δ≥1.0%p + CI 하한>0 등)을 **결과 확보 전에 사전등록**.

**(4) 차단 여부:** LoRA 구현 비차단; LoRA confirmatory 주장은 차단(fresh holdout + matched no-LoRA comparator 필요).

### Q6. B0′ matched-budget controls — 판정: B

**(1) 판정:** "compute/exposure만으로는 B3의 ~10%p 격차를 설명할 수 없다"는 결론은 **지지**된다. 다만 몇 가지 caveat과 표기 문제가 있다.

**(2) 근거:**
- 재검증: B0′-12 0.370084, B0′-20(e20 decode) 0.365442, B0′-38 0.368279. gap +9.7228%p [+8.6558,+10.8187], +10.0064%p [+8.9080,+11.1608] — JSON 일치. B0′-12→20→38에서 dev 이득 ≤0.5%p(CI 0 포함)로 포화 명확.
- caveat: (i) B0′-38은 6h를 38회 반복 — 과적합 방향으로 작용했음에도 격차가 줄지 않았으므로 결론은 보수적으로 안전; (ii) LR 스케줄 shape 차이(20/38ep cosine) — 포화 관찰이 이를 상쇄; (iii) sampler 차이(B3 balanced vs B0′ natural) — B3-nat 비교에서 ns라 작음; (iv) single seed; (v) 이 컨트롤에서는 FLEURS guardrail 미측정.

**(3) 필수 수정:**
- **표기 불일치 신규 지적(MF-I):** 요청서 §1.2/§5.3이 "final dev 0.3657/0.3687"과 "gap +9.723/+10.006"을 나란히 쓰는데, provenance의 gap은 **best-dev decode(0.365442/0.368279)**에서 계산된 값이다. 어느 decode 기준인지 표에 명시하고 통일(권고: best/final 병기 + CI의 기준 명시).
- B0′-rep10: **지금 불필요**(우선순위 낮음). B0′-20이 이미 exposure 매칭이고 포화가 확인됐다. 6h 반복·서브샘플로 10.02h를 흉내내는 것은 새 confound를 추가할 뿐이다. 다만 "데이터 볼륨 자체의 효과"를 나중에 문제 삼는 리뷰어가 나오면 실행.

**(4) 차단 여부:** 비차단.

### Q7. B3-nat·sampler — 판정: B

**(1) 판정:** "sampler 효과는 dev에서 탐지되지 않았다"는 표현으로 **충분**하다.

**(2) 근거:** B3-nat−B3 = −0.49%p, CI 0 포함(dev-only). B3-nat을 test에 넣지 않은 것은 옳다(test 보존 — 승패와 무관한 비교에 소비할 이유가 없다). 오염 질문: B3-long/B3-zeroth-long은 둘 다 natural이므로 domain 비교는 sampler에 대해 자체 매칭; length 비교(B3-nat vs B3-long)도 둘 다 natural. balanced-vs-natural이 섞이는 것은 B3(11,196 steps) vs B3-long(5,568) 비교뿐이고, 이 비교를 주 근거로 쓰지 않으므로 실질 오염 없음.

**(3) 필수 수정:** B3-balanced − B3-long −1.5732%p(CI 0 제외)를 **sampler 근거로 인용하는 것 금지**(step도 다름). sampler null 인용은 반드시 B3-nat vs B3(steps 동일)로만.

**(4) 차단 여부:** 비차단.

### Q8. Text overlap — 판정: C(미종결 상태 유지 불가) → 단, short_v2 부분은 본 보고서에서 종결

**(1) 판정:** "새 holdout 때 함께 처리" 계획은 **수정 필요**. 감사는 거의 공짜(순수 텍스트 비교, 학습 불필요)이고, 유일한 confirmatory 결과(test)의 신뢰성에 직결되므로 **즉시** 닫아야 한다. 실제로 본 검토에서 short_v2 범위는 닫았다(위 "검증 수행 내역" 4번).

**(2) 근거:**
- 프로젝트 정규화기(`normalize_nospace`)로 재현: test↔short_v2(5,079) 정확 텍스트 일치 **136/2,400=5.67%** — Sonnet 수치와 정확히 일치(그의 감사가 short_v2 범위였음을 시사).
- 민감도: 중복 136개 제외 시 test Δ +9.7373→**+9.4762%p** — 게이트(Δ≥1.0%p, CI 하한 +9.228)에 영향 없음. "gate 결과가 중복 때문에 생긴 것"이라는 대안은 배제.
- 부수 확인: dev 26/500 중복 제외 시에도 모든 비교 방향 불변(−0.1~0.2%p 수준 감소).

**(3) 필수 조치:** (a) 본 결과를 `reports/provenance/W2B/` 형식(overlap_final.json 확장)으로 저장 — 단, **Wave1(2,384, Kconf 포함)/short_v1/long 매니페스트가 로컬에만 있으므로 전체 감사는 로컬에서 실행**해야 종결; (b) 게이트 결과 보고서에 "test↔short-train 텍스트 중복 5.7%, 제외 시 Δ 9.74→9.48%p, 결론 불변" 병기; (c) fresh holdout 설계 시 동일 감사를 절차에 포함.

**(4) 차단 여부:** 전체 감사(wave1 포함) 완료 전, 새 대외 확장 주장과 LoRA confirmatory 주장은 차단 권장. 현재 탐색 작업·LoRA 구현은 비차단.

### Q9. B3-zeroth-long 역설 — 판정: B

**(1) 판정:** 가장 가능성 높은 설명은 **domain/corpus 불일치**다. 이 arm을 domain control으로 쓰는 것은 타당하다.

**(2) 근거:** (i) compute 부족 설명 부정 — B3-zeroth-long은 B0′보다 step(5,676 vs 3,576)과 데이터(10h vs 6h) 모두 많음; (ii) "long-only라서 안 됨" 설명 약화 — 같은 long 데이터가 Kspon에서는 +8.61%p; (iii) Zeroth long이 Wave1의 Zeroth(1,534클립)와 같은 코퍼스 계열이라는 점에서 "같은 코퍼스 추가의 한계효용 급감" 가능성도 있으나, 이 경우에도 Kspon 추가의 효과와의 대비로서 domain 결론과 일관. control이 null을 보이는 것은 결함이 아니라 결과다. "B0′+Zeroth long이 잘못된 control"이라는 주장에는 근거가 없다.

**(3) 필수 수정(학습 불필요한 저비용 진단 2개):** (a) arm별 train loss/grad norm 곡선을 보고서에 공개 — Zeroth long arm의 수렴이 정상인지 확인; (b) B3-zeroth-long 체크포인트를 Zeroth long 홀드아웃(예: 50클립, 사전에 학습에서 제외)에서 디코드 — Zeroth long을 전사하지도 못한다면 domain 불일치가 아니라 데이터·품질 문제. (체크포인트·오디오가 로컬에만 있어 본 검토에서는 실행 불가.)

**(4) 차단 여부:** 비차단.

### Q10. 다음 우선순위 — 판정: 지금 당장 1개 = **step-matched B3-long(ga2)**

**(1) 판정:** "domain은 충분하니 length를 중단하고 LoRA로 가라"는 판단은 **권장하지 않는다**. step-matched B3-long + 감사 종결을 먼저 하되, LoRA **구현·GPU 스모크는 병행 시작**해도 된다.

**(2) 근거:** (i) 2C-short(Kspon short 4h)는 gated recipe의 핵심 구성요소인데 그 기여 분리가 미확정 — LoRA confirmatory 설계(no-LoRA comparator 선택, 효과 크기 해석)에 직접 들어가는 정보다; (ii) 비용이 ≈3h CPU로 허용 범위 내; (iii) text-overlap 감사는 "실험"이 아니라 거의 공짜 감사로 병행 가능(short_v2 부분은 이미 종결, 잔여는 로컬 전체 감사); (iv) non-Kspon short는 현재 주장에 불필요해 연기해도 손실이 없다.

**(3) 필수 수정(우선순위 목록):** 아래 §3 참조.

**(4) 차단 여부:** step-matched 완료 전 LoRA **confirmatory 주장** 차단. 구현·스모크는 비차단.

### Q11. 대외 주장 문장 — 판정: B(수정안으로 수용)

**(1) 판정:** 원문 문장은 두 군데서 과일반화다. (a) "Kspon domain 효과가 강하다"가 근거 범위(같은 long 길이에서의 dev-only 비교)를 넘어 읽힌다; (b) test +9.74%p가 화자 독립 일반화처럼 읽힌다. control이 dev-only·단일 seed·V2 조건부라는 표기가 없다.

**(2) 근거:** 위 Q1/Q5/Q6/Q8. 또한 "short 4h 데이터 효과"라고 쓰면 안 되는 이유(한 문장): **2.06%p 차이가 step 수 2배 confound와 결합되어 있어 길이 고유 효과와 step 효과를 분리할 control(step-matched B3-long)이 아직 없기 때문이다.**

**(3) 필수 수정:** §4의 수정안 사용.

**(4) 차단 여부:** 수정안 채택 전 대외 배포 차단 권장.

---

## 2. Must-fix 표

| ID | 지적 | 필수 조치 | 우선순위 | LoRA 차단 |
|---|---|---|---|---|
| **MF-A2** (구 MF-A 잔여) | step-matched B3-long 미실시 → short-length 미확정 | 위 Q2 설계(ga2, 11,136 steps, ≈3h CPU) 1회 실행 + 해석 규칙 사전등록 | **P1** | confirmatory 주장 차단 / 구현 비차단 |
| **MF-E2** (구 MF-E) | test↔학습 text overlap 미종결 | **short_v2 부분 종결됨(본 보고서): 136/2,400, Δ 9.74→9.48%p, 결론 불변.** 잔여: Wave1/long 매니페스트 포함 전체 감사를 로컬에서 실행·provenance 저장 | **P1** | 전체 감사 완료 전 confirmatory 주장 차단 |
| **MF-B2** | test 재사용 규칙 부재 | "동일 test 재평가=비confirmatory" 명문화 + fresh holdout 사전등록(spare 90은 confirmatory 불가) | **P2** | LoRA confirmatory 차단 |
| **MF-C2** (구 MF-C) | V2 vocab selection dependence 표기 | "V2-vocab-conditioned" 태그+정의를 게이트·컨트롤 보고서에 추가 | P2 | 비차단 |
| **MF-G2** (구 MF-G) | 화자 독립 아님 | 모든 대외 문장에 유지(기존 운용 올바름) | P2 | 비차단 |
| **MF-H** (기존) | LoRA compute confound | fresh holdout + matched no-LoRA comparator + GPU smoke | P2 | LoRA confirmatory 차단 / 구현 비차단 |
| **MF-I** (신규) | matched-budget gap의 decode 기준 혼재(best 0.3654/0.3683 vs 문서의 final 0.3657/0.3687) | CI 산출 기준 decode 명시, 표 통일 | P3 | 비차단 |
| **MF-J** (신규) | B3-zeroth-long 역설의 최적화·품질 진단 부재 | train loss 곡선 공개 + Zeroth-long 홀드아웃 디코드 진단 | P3 | 비차단 |
| **MF-K** (신규) | dev 500 내 text overlap 26/500 | dev 민감도 병기(본 보고서: 격차 −0.1~0.2%p 감소, 결론 불변) | P3 | 비차단 |

---

## 3. 다음 실험 우선순위

1. **step-matched B3-long (ga2)** — 지금 당장 추가할 최소 실험 1개. ≈3h CPU, dev 500 전용. length vs step 분리의 결정적 셀.
2. **text-overlap 감사 전체 종결** — Wave1(2,384)·long 매니페스트 포함, 로컬에서 실행·저장. short_v2 부분은 본 리뷰에서 재현·종결. 실험이 아니라 감사(수 시간 미만)이므로 1과 병행.
3. **LoRA B1/B2 구현 + GPU smoke** — 엔지니어링 작업으로 즉시 병행 가능(주장이 아니라 코드).
4. **fresh holdout 설계·사전등록** — 후보 eval_other의 사용이력 감사 포함, 기준을 결과 전 확정. LoRA confirmatory 전 필수.
5. **seed 43 재현** — step-matched 결과가 length를 지지할 때만(robustness 보조).
6. **non-Kspon short 4h** — 연기. 필요 시 FLEURS ko train(조건은 Q3). 현재 주장에 불필요.
7. **20-epoch 3-arm, B0′-rep10** — 선택/연기(B0′ 포화로 낮은 기대값).

**결정 문답(요청서 §12 5개 항목):**
- 지금 당장 최소 실험 1개: **step-matched B3-long(ga2)**.
- 지금 해서는 안 되는 주장 1개: **"short-length(짧은 발화 4h) 효과가 2.06%p다"** — step confound 미제거 상태에서의 인과 귀속 금지.
- LoRA로 넘어가는 조건: 구현·스모크는 즉시 가능. **confirmatory 주장**은 (1) step-matched 결과로 length 스토리 확정, (2) fresh holdout 사전등록, (3) matched no-LoRA comparator(동일 데이터·steps·exposure·vocab·seed), (4) text-overlap 전체 감사 종결 — 충족 후.
- non-Kspon short 없이 domain 결론 유지: **가능**. 단 주장 범위는 "같은 long 길이·예산에서의 코퍼스 출처 효과, dev-only"로 한정. "domain at short" 주장은 불가.

---

## 4. 대외 주장 문장 (수정안)

**권장 문장(전문):**

> "EG2 reader-only 파일럿에서 Wave1 6h에 Kspon short 4h를 추가한 B3는 B0′ 대비 dev 500에서 +10.19%p, 봉인 test 2,400에서 +9.74%p(95% CI [+9.23, +10.26])의 CER 개선을 보였다. 이 개선은 optimizer step을 11,324로 맞춘 B0′-38(격차 +10.01%p 유지)과 누적 노출을 맞춘 B0′-20(+9.72%p)으로도 해소되지 않았다. 같은 8–16초 길이·4h·거의 동일 step 조건에서는 Kspon long 4h 추가 arm이 Zeroth long 4h 추가 arm보다 dev에서 8.16%p 우수했고, Zeroth long arm은 B0′와 유의한 차이가 없었다. 즉 추가 데이터의 코퍼스 출처(화자·녹음·발화 스타일·전사 규약·OOV 구성을 포함하는 'domain bundle')가 큰 차이를 만든다는 dev-only 증거가 있다. 반면 short-length(짧은 발화 중심 4h) 고유 효과는 step 수 2배 차이 confound 때문에 미확정이며 step-matched control이 필요하다. 학습 텍스트와 test 텍스트의 중복(136/2,400=5.7%)은 제외 시 Δ가 +9.74→+9.48%p로 결론에 영향이 없다. 모든 신규 컨트롤은 dev 500·seed 42·V2 vocab 고정 조건의 탐색적 결과이며, test 2,400은 B3 확정 후 1회 사용된 in-domain procedural holdout으로 화자 독립이 아니다."

**짧은 버전(요약용):**

> "V2 reader-only recipe는 in-domain dev/test에서 큰 CER 개선(+10.19/+9.74%p)을 보였고, 이는 compute/exposure만으로 설명되지 않는다. 같은 long 길이·예산에서 Kspon 4h 추가는 Zeroth 4h 추가보다 8.16%p 우수했다(dev-only, corpus-source bundle 효과). short-length 고유 효과는 step confound로 미확정이다."

**금지 문장 목록:** "Kspon short 4h의 순수 효과를 입증" / "short-length 효과=2.06%p" / "화자 독립 일반화 +9.7%p" / "test 재사용 confirmatory PASS" / "B3-zeroth-long이 non-Kspon short control과 동등" / "LoRA가 필요하다/불필요하다"(B1/B2 미실행).

---

## 5. 불확실한 점

1. **데이터 미수록:** Wave1/short_v1/long_4h 매니페스트와 오디오·캐시·체크포인트는 repo에 없다. 본 감사(136/2,400 재현)는 short_v2(5,079) 범위이며, 정확히 같은 수치가 나온 점에서 Sonnet의 감사도 같은 범위였을 것으로 추정되나 확정할 수 없다. 전체 종결은 로컬 실행 필요.
2. **학습 재실행 없음:** 모든 학습 의존 수치는 repo provenance·예측 파일 기반 재계산이다. 디코딩·학습은 실행하지 않았다.
3. **best vs final decode:** 요청서의 B0′-20/38 "final dev" 표기(0.3657/0.3687)와 provenance decode(0.365442/0.368279=best)의 관계를 문서만으로 확정할 수 없다(MF-I).
4. **Kconf의 코퍼스 계열:** D-061은 "3화자/2.1007h"만 기록 — Wave1 기반선 내 Kspon 계열 비중이 domain bundle 해석에 미세하게 붙는다.
5. **단일 seed:** bootstrap CI는 발화 리샘플링만 반영하며 seed 변동은 반영하지 않는다. seed 43은 후순위이지만 "강하다" 표현에는 이 한계가 있다.
6. **long 조건의 test 일반화:** test 8–16s가 185건뿐이라, 도메인 효과가 long *평가* 조건에서도 동일하게 나타날지는 현재 test로 좁게만 확인 가능하다.

---

### 부록 — 본 검토가 사용한 재현 경로 (읽기 전용)

- `python3` + `eval/normalize.py`(`normalize_nospace`, `_edit_distance`): `reports/provenance/W2B/devpred_*.json`(7 arm), `testpred_b0p_v2_s42.json`·`testpred_b3_v2_s42.json`의 원본 ref/pred 재계산.
- `data/wave2b/short_4h_v2.jsonl`(5,079) ↔ test/dev refs 정규화 정확 일치 비교 + 중복 제외 CER 민감도.
- `domain_controls_bootstrap.json`, `matched_bootstrap.json`, `domain_controls_budget.json`, `overlap_final.json`, `test_freeze.json`, `test_breakdown.json`, `training_budget.json`, `data/wave2b/V2_READY.json`, `short_4h_v2_summary.json`, `vocab_v2.json` 대조.
- 코드: `train/d5_reader.py`(정규화 체인), `runner/w2b_domain_controls_analyze.py`(bootstrap 방법론), `eval/normalize.py`.
