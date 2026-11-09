# C5 Phase 6 v1.0.7 — External Review (GLM 5.3 Flash, reasoning max)

- 작성일: 2026-11-09
- 모델: `z-ai/glm-5.3-flash` (reasoning max), 독립 라운드, 타 모델 답변 미사용
- **검토 기준 HEAD SHA: `9613ef6`** (full: `9613ef60094b253df13213cfa3d911306b5d9f78`, "docs: add Phase 6 v1.0.7 repair")
- 동기화 HEAD: `git fetch origin` + `git pull --ff-only origin main` → `a826308f64301179cb54c7a87a208bf3f1bc6af4` ("docs: add C5 P/M v1.0.7 review request"). `9613ef6..a826308` diff는 리뷰 인프라 6개 파일(dispatch/prompts/watch/요청서)뿐이므로 검토 대상 12개 파일의 바이트는 `9613ef6`와 동일.
- **§9.6.1 verbatim 인용 (plan line 1089):**
  `K_d = min(K_M, len(real_prefix), len(donor_prefix))`
- 제약 준수: 학습/평가 실행 없음, test 163 미개봉, P1 미사용, 서브에이전트 없음. 유일한 실행은 커밋된 fixture 바이트에 대한 SHA-256 재계산(모델 로드·forward 없음)과 grep/read.
- 상태: v1.0.7 review. **Phase 6/B0-B/B1/B2/Stage C 실행 미승인. test 163 sealed. T5Gemma2 D-108 STOP 유지.**

---

## 0. 독립 검증 결과 (hash-only)

구현 결과물이 아닌 커밋된 fixture/preflight 바이트를 직접 재해시한 결과:

| 항목 | 재계산 | 기대값 | 일치 |
|---|---|---|---|
| state golden (`43ecb58e…d65712`) | frame 재구성 후 SHA256 | 동일 | ✅ |
| empty state (`e3b0c442…`) | SHA256(b"") | 동일 | ✅ |
| replay_base (`c43ea35c…f7851667`) | canonical JSON(sort_keys, `(',',':')`) 정렬 배열 1개 해시 | 동일 | ✅ |
| key_coverage 4-record (`8277a713…af7a20`) | 동일 규칙, `donor_sort=-1(null)` 정렬, 직렬화는 `donor_id:null` 유지 | 동일 | ✅ |
| control fixture (`6b50c226…c1938`) | canonical-name 오름차순(`M_NORM/doc_a` < `M_POS_MEAN`) 프레임 연결 해시 | 동일 | ✅ |
| preflight content SHA (`3ee3f1ca…69837af`) | file bytes SHA256 | §0.4 값과 동일 | ✅ |

수치 재확인: 15×96+5×48=1,680; arm-seed 120+120+160+160=560; 3×560=1,680; phase-7 15×5×2×2×2=600; per-arm F=360, L=360, P=480, PA=480; cap 1,200+4=1,204 updates / 120+20+15=155 min. P0 artifact 실측치와 §3 표 전부 일치(train +3.7617264 [1.8916853, 5.6049574], val +5.2374585 [2.5013211, 8.0752724], positive 14/20·18/20=`seeds_positive`(문서 수), real CE 12.702/13.235 > ln(250112)≈12.43, `source_max_length:256`, `mode=p0_sanity_no_training`, `test_split_used:false`).

---

## 1. Q1–Q13

### Q1. v1.0.6 잔여 6개 closure

- 판정: **agree (5 closed, 1 partial)**
- 근거:
  1. §16.2 freeze 경로 — **closed**. manifest `docs/plan_c5_b0a_pm_prereg_v1_0_7_FREEZE.json`, `plan_path` `docs/plan_c5_b0a_pm_prereg_v1_0_7.md`. template도 동일 경로.
  2. `T_proj` per-seed — **closed**. §11.5 "`t_primary_replay_arm` uses per-seed 120/160 … The outer `3 *` produces 360/480 … do not pass 360/480 into the term" + §13.5 산술 unit test.
  3. phase-7 `K_d<=K_M` — **closed**. §9.6.1 `K_d = min(K_M, len(real_prefix), len(donor_prefix))` + 4개 assert + 4 텐서 전부 `[:K_d]` 슬라이스 + "no renormalization" + §11.4 step 5의 600 numeric replay.
  4. `freeze_commit`/`manifest_commit` — **partial**. 정의는 분리됨(freeze_commit=최종 plan commit, manifest_commit=_FREEZE.json commit, freeze 순서 4단계, D0이 `freeze_manifest_sha256` 기록). 그러나 `manifest_commit`이 **_FREEZE.json 자신의 스키마 필드**(line 1664)로 남아 있어, 그 파일을 포함하는 커밋의 SHA는 파일 내용에 의존하므로 커밋 전에 채울 수 없음(자기참조). → MF-A.
  5. key-coverage wording — **closed**. §11.4 step 5 "verify the 4-record `key_coverage_golden` fixture; separately recompute phase-7 diagnostic 600/arm-seed", §12.3 "4-record … not the 600-record phase-7 domain; numeric-only".
  6. legacy bootstrap assert — **closed**. §10.2 "no legacy `bootstrap_paired`", §13.5 "stats module does not import legacy `bootstrap_paired`". `runner/c5_mt5_lora_b0.py:341`의 legacy `bootstrap_paired(seed=20261108, seeds_positive=문서 수)`는 helper로 잔존하며 신규 모듈 import만 금지 — 의도대로.
- 다음 단계: (1) MF-A 문구 보완 후 동결, (2) Q7 참고.

### Q2. Self-containedness

- 판정: **agree**
- 근거: 데이터 경로(§2.6), 측정 경로(§2.5.1–2.5.7), RNG 순서(§2.7), 판정 함수(§3–7), M 빌더/엔드포인트(§9), 통계(§10), 해시(§12), 테스트 매트릭스(§13), 파일 산출물(§17.2)이 전부 문서 내 정의. 외부 참조는 §17.1 helper 6종(파일+계약 명시, `helper_commits`로 freeze commit 고정)과 §0.4/§1.5 artifact들이며 전부 열거됨. `runner/c5_pm_stats.py`는 미존재(코드 선동결 원칙 §16.1 준수)이고 §10이 계약 정의. 암묵 지식 요구 없음. `Adapter`/`make_labels`/`load_layer_cache`(c5_mt5_layer_probe.py:52/79/66), `LoRALinear`(c5_a1_lora.py:45, kaiming a=sqrt(5), B zeros, r8/α16/dropout .05), `attach_decoder_lora_mt5` 64모듈 검증, `native_memory` — §2.2/§2.5.4/§17.1 계약과 실제 구현 일치 확인.
- 남는 것: 없음. helper 동작은 "freeze commit 시점 파일이 권위"라는 방식으로 해소됨.

### Q3. Freeze chain

- 판정: **conditional**
- 근거: §16.2 경로·스키마·template 일치(`plan_path` v1_0_7, `preflight_sha256` 선기입값 실측 일치, `status:"template"`→복사 시 `frozen` 주석 명시). `freeze_commit`=최종 plan commit(단계 1 이후 해시 산출, manifest 미포함) — 자기참조 없음. `freeze_manifest_sha256`(_FREEZE.json 파일 SHA)는 D0 보고서 기록 — 가능. **유일한 결함: `manifest_commit` 필드가 _FREEZE.json 내부에 있으면서 그 파일의 commit을 값으로 요구 → 커밋 SHA가 내용에 의존해 채울 수 없음.** §16.2는 대안(파일 내 null + D0/postrun 기록, 또는 후속 커밋 정의)을 규정하지 않음.
- 다음 단계: (1) MF-A 대로 한 문장 규정 추가, (2) 동결 단계 2에서 `manifest_commit:null`로 기입, (3) D0 보고서에 `freeze_manifest_sha256`과 함께 실제 manifest commit SHA 기록.

### Q4. T_proj

- 판정: **agree**
- 근거: phase-5 per-seed F/L 120, P/PA 160(15×8, 20×8); D1 합계 560; 등록 실행 per-seed 동일, outer `3*` → per-arm F=360, L=360, P=480, PA=480, 총 1,680 — §11.3/§11.5/§13.4 상호 일관. §11.5가 "do not pass 360/480 into the term"으로 이중 산입 명시적 차단, §13.5 단위 테스트 존재. phase-7 600/arm-seed는 별도 항 `t_replay_15x5x2x2x2_arm`으로 1회만 산입 — triple-count 위험 제거 확인.
- 다음 단계: 구현 시 §13.5 테스트를 최초 실행 묶음에 포함.

### Q5. Phase-7 실행 가능성

- 판정: **agree**
- 근거: `K_d = min(K_M, len(real_prefix), len(donor_prefix))` + `assert 1 <= K_d <= K_M` + `K_d<=len(real)·len(donor)` + 4 텐서 shape 일치 assert. P/PA는 preflight `val_native_lengths` 전부 512이므로 항상 `K_d=K_M=512`; F/L은 common 15개가 전부 `h_len>=753`(최소 753=REPORT-news_r-01331)이고 donor pool에 708/718/728/750/751이 있어 `h_d<753`만 절단 사례 — §9.6.1 주석과 정확히 일치. `baseline_ce`는 phase-7에서 재계산(phase-5 K_M 저장 CE 재사용 금지), `delta=baseline_ce-ce`, `M_NORM(t)[:K_d]` 재정규화 금지 — 전부 명시. 600/arm-seed는 §11.4 step 5–7에서 numeric-only(`atol=1e-5, rtol=1e-4`), `diagnostic_replay_ok` 분리 보고, primary `replay_ok` 불영향. `K_M` 753/512와 정합.
- 다음 단계: (1) 구현 시 assert 4종을 phase-7 진입부에 배치, (2) `donor_sort` 내부 전용 확인.

### Q6. Key coverage 분리

- 판정: **agree**
- 근거: 4-record fixture(P native val_native_01 M_NORM control/real full, PA donor_id=4 M_POS_MEAN donor/real copy)는 §12.2 키 도메인 검증용이고, phase-7 600은 numeric-only로 분리(§11.4 step 5, §12.3). fixture는 `donor_id=4` 커버리지를 직접 exercise. 재계산 digest 일치(§0 표). 혼동 여지 없음.

### Q7. Legacy bootstrap 테스트 충분성

- 판정: **conditional (agree with addition)**
- 근거: import 금지 단언은 필요조건이고 §10.1/§10.3(seed 20261109, PCG64 fresh generator, percentile method="linear")·§10.2(`documents_positive` vs `registered_seeds_positive`, P0 helper `seeds_positive` 재사용 금지)·§13.3·§13.5가 행동 차이를 함께 고정하므로 의미 재구현 위험은 대부분 봉쇄됨. 다만 import 금지 단언만으로는 동일 계산의 로컬 재작성을 잡지 못함.
- 다음 단계: (1) 신규 stats 모듈 테스트에 `bootstrap 시드 상수==20261109` 및 등록 경로 출력에 `seeds_positive` 키 부재 단언 추가, (2) legacy `bootstrap_paired` 심볼 미참조를 AST/grep 기반으로도 검사.

### Q8. Hash/golden 정합

- 판정: **agree**
- 근거: §0 표 — state/empty/replay_base/key_coverage/control 5종 + preflight 전부 독립 재계산 일치. flat 8-field(`arm,ce,doc_id,donor_id,endpoint,memory_kind,seed,variant`), `baseline_ce`/`delta` 해시 도메인 제외, 정렬 배열 1개 canonical JSON, per-record 연결 금지(§12.2/§13.4) — 재계산이 그 규격으로 성공했으므로 규격 자체도 검증됨. `donor_sort` 미직렬화·미해시 내부 전용 확인. control 오름차순 `M_NORM` < `M_POS_MEAN` 확인. control fixture는 synthetic `[1,1]` framing 전용이고 실 `control_digest`는 postrun-only라는 스코프 문구도 명확.

### Q9. D0/D1/cap

- 판정: **agree**
- 근거: D0 = arm당 0-update 1 config(≤4), seed 20261111, ≤15 min, `labels_computed:false`, `not_a_result:true`, h-length assert(F/L cache, P/PA 512 — preflight와 일치). D1 = 4 arms × 1 debug seed(20261111) × 1 update, ≤20 min, 8 phases 전부 나열, phase-5 560 / phase-7 600, `labels_computed:false`가 decision/signal 라벨만 지칭한다는 §11.3 명시. 등록 cap 12 units/1,200 updates/120 min/6 threads/no GPU/no retry(§11.1), T_proj ≤96 min + 120-min hard abort(§11.5), prospective 1,204/155 min not-a-grant(§11.6). 전부 상호 일관.

### Q10. v1.0.7이 새로 만든 문제

- 판정: **conditional (경미 3건, 과학적 결함 없음)**
- 근거: 과학적 내용(코호트·임계값·엔드포인트·통계)은 전부 기존 등록값 유지, 신규 수치 결함 없음. 발견한 것:
  - **MF-A (medium)** `manifest_commit` 자기참조 — Q3 참조. freeze 시 구현자가 즉흥적으로 채우게 되면 prereg 이탈.
  - **MF-B (low)** §10.4와 요청서가 인용하는 P0 tail 수치(val signed top3 .4862, absolute .43355, 15-common .455)가 `p0_native_sanity.json`에 존재하지 않음(top3/tail/share 필드 부재, `0.4862`는 C5_b1d/W2B 타 실험 파일에만 존재). descriptive·비게이트라 동결 차단은 아니나 출처 보관 갭.
  - **MF-C (cosmetic)** §4.6 bullet 2 "`p_step NA + p_valid=false` → NOT_ASSESSABLE"는 도달 불가능한 상태(§4.5상 p_step NA면 P_VALID는 NA). F9("p_step NA + p_valid NA")로 표현이 정확. §4.4/§4.7/F3와의 정합성 자체는 문제없음(`pa_path NA + p_valid=false`는 `P_STEP100_NOT_VALID`로 일치) — 본문 오독 없도록 표기만 정리.
  - (cosmetic) freeze template의 `note` 키·`status:"template"`은 복사 시 제거/치환 필요 — §1.5의 unknown-keys 허용은 p1 manifest 한정이므로 freeze manifest 스키마에 한 문장 여부 결정.
- 다음 단계: MF-A를 동결 커밋에 포함, MF-B는 provenance 보강 또는 문구 조정, MF-C는 표기 정리.

### Q11. 동결·구현 승인

- 판정: **conditional — 동결+구현+unit tests+D0 승인 가능 (MF-A 반영을 동결 커밋에 포함하는 조건)**
- 근거: 잔여 6개 중 5 closed·1 partial(MF-A)이고, 그 수정은 text/schema-only로 §16.1의 "no new scientific choices" 범위 내. 과학적 선택 재개 없음.
- 구현 전 필수 test(최초 실행 묶음): golden 5종 digest, flat-8-field + 정렬 배열 해시 + per-record 연결 실패, permutation/duplicate/missing, `donor_sort` 비직렬화, control canonical-name 순서, key-coverage 4-record, `3 * sum(per-seed 120/160)` 산술, legacy bootstrap 미import + seed 20261109 상수, F1–F11 + fixture 16–18 + §3.4 9 pairs + ANDn, copy CE same-position(기존 test_c5_b0_metric.py 계승), donor 규칙(길이 인접·본인 제외·arm별).
- D0 범위: 4 config 0-update mechanics, h-length assert, control manifest 빌드, `labels_computed:false`.

### Q12. B0-B / D1 / 3-seed 경계

- 판정: **agree**
- 근거: §16.3 승인 배제 목록(D1/3-seed/B0-B/B1/B2/Stage C/test 163·P1/T5Gemma2) 명시, §14 `separate prereg/approval`, §11.3 "D1 없이 3-seed 금지". 경계 충분.
- **v1.0.7 라벨로 재진술한 B0-B predicate:**
  ```text
  B0-B := (validity_status == VALID)
      AND (control_status == M_CONTROL_PASS)
      AND (signal_status == EXPLORATORY_L_SIGNAL)
      AND (m_valid == true)                    # P/PA 4-conjunct calibration
      AND (n_signal == 15)                     # >=15 ⇔ ==15 (max 15)
      AND (tail_driven == false)               # signal tail only, top3_abs_share rule; true/NA 불통과
      AND (assay_path_ok ∧ p0_path_ok ∧ p_step100_path_ok ∧ pa_step100_path_ok == true)
      AND (replay_ok == true ∧ artifact complete per phase6_artifact_registry v2)
      AND separate prereg + approval           # M_CONTROL_PREFIX753_COHORT15 scope
  ```
  `EXPLORATORY_L_SIGNAL` 단독, `full_k_secondary`/P0/`PA_RETENTION`은 증거 불가(§14) — 유지.

### Q13. 최종 판정

- 판정: **CONTINUE (조건부)**
- 근거: v1.0.6 잔여 6개 중 5개 완전 폐쇄, 1개(MF-A)는 문장 보완만 남음. 독립 재계산으로 golden/preflight/산수 전부 확인. 신규 과학적 결함 없음. STOP 사유 없음; NARROW로 동결을 다시 보류할 만한 실질 갭은 MF-A뿐이며 그 수정은 동결 커밋 자체에 포함 가능.

---

## 2. Must-fix (ranked)

1. **MF-A** §16.2: `manifest_commit` 채움 규칙 명시 — 권장 문구: "`manifest_commit` is not stored inside `_FREEZE.json`; the file records `manifest_commit: null` and the actual manifest commit SHA is recorded in the D0 report next to `freeze_manifest_sha256`." (또는 동등한 후속-커밋 규정). 동결 커밋에 포함.
2. **MF-B** §10.4 P0 tail 수치(.4862/.43355/.455) provenance 보강 — P0 artifact에 tail 요약 저장 또는 "derived, not stored in `p0_native_sanity.json`" 문구. descriptive라 동결 차단 아님.
3. **MF-C** §4.6 bullet 2 표기 정리(`p_valid=false`→도달 불가; F9의 `p_valid=NA`가 정확).
4. (cosmetic) freeze manifest 복사 시 `status:"frozen"` 치환·`note` 제거를 §16.2 절차에 한 문장 명시.

과학적 must-fix 없음. threshold/seed/donor/step/LR 변경 제안 없음(§0.7 준수).

## 3. 최종 판정 블록

```text
최종 판정: CONTINUE (조건부 — MF-A를 동결 커밋에 포함)
v1.0.7 freeze: 승인 (MF-A 문구 포함 시; 동결 경로 v1_0_7 확인됨)
구현+unit tests: 승인 (§13 매트릭스 + Q11 필수 묶음; 코드는 freeze 이후)
D0: 승인 (0 update, ≤4 config, ≤15 min, seed 20261111, labels_computed:false)
D1: 미승인 (별도 승인 필요)
3-seed: 미승인 (D1 이후 별도 등록 실행)
금지 범위: D1/3-seed/B0-B/B1/B2/Stage C 자동 진행, test 163 개봉, P1 사용, T5Gemma2(D-108 STOP), 결과 후 threshold/seed/donor/step/LR 변경, freeze 승인의 Phase 6 실행 착취
최대 compute: 지금 승인분 = 구현+unit tests(CPU, 학습 없음) + D0(0 update, ≤15 min). 등록 Phase 6는 12 units/1,200 updates/120 min/6 threads/no GPU/no retry, T_proj ≤96 min, 120-min hard abort, prospective 1,204 updates/155 min은 grant 아님 — 별도 승인 전까지 미실행
Must-fix (ranked): MF-A manifest_commit 자기참조 규정 / MF-B P0 tail provenance / MF-C §4.6 표기 / template 복사 절차 문구
v1.0.7 self-contained: 예 — 외부 참조는 §16.2 helper_commits로 고정된 §17.1 계약과 artifact들뿐, 암묵 지식 요구 없음
잘못된 전제: 없음. 단, P0 tail 수치는 저장 artifact에 없음(MF-B), "manifest_commit in-file"은 실행 불가(MF-A) — 두 전제는 v1.0.7 본문에서 수정 필요
```