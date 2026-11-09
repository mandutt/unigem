# C5 Phase 6 v1.0.2 External Review — GLM 5.3 Flash (max)

- 작성일: 2026-11-09
- 검토자: **GLM 5.3 Flash, reasoning max** (`z-ai/glm-5.3-flash`, Hoplite 런타임)
- 검토 라운드: v1.0.2 신규 독립 라운드 (v1.0.1 3-AI 라운드와 별개, 타 모델 답변 미참조)
- 검토 기준 HEAD: sync 시점 `origin/main` = **`445a9cc`** ("docs: add C5 P/M v1.0.2 review request").
  검토 중 `git fetch --deepen`으로 원격이 `ee99fd0`("docs: record C5 P/M v1.0.2 review thread ids")로 진행됨을 확인했고
  `git pull --ff-only`로 fast-forward했다. `445a9cc..ee99fd0` diff는 `threads.json` 1개 파일뿐이며
  **검토 대상 파일(plan/golden/provenance/runner/tests)은 두 커밋에서 동일**하다. 요청서 기재 기준 HEAD `1f6b816`은
  v1.0.2 repair 커밋으로, `445a9cc`와 plan 본문 사이 무변동이다.
- 대상: `docs/plan_c5_b0a_pm_prereg_v1_0_2.md` (1,564줄) 전문 직접 독해 완료
- 방법: text-only 정합 검토 + **독립 재계산**(해시, 산술, donor 정렬) — 학습/평가 실행 없음
- 제한 준수: test 163 미개봉(splits.json 존재만 확인, 내용 미독), P1 미사용, 서브에이전트/추가 LLM 없음,
  저장소 수정 없음(본 보고서 1개 파일만 작성), Phase 6/B0-B/B1/B2/Stage C 승인 아님, T5Gemma2 D-108 STOP 유지

---

## 0. 한 줄 결론

> **NARROW.** v1.0.2는 v1.0.1의 15개 blocker를 텍스트 수준에서 전부 폐쇄했다(13 closed, 2 closed-with-minor-residual).
> 핵심 구조적 결함이던 validity/calibration 분리(§4.5/§5.4)와 arm-specific donor(§2.5.6), control tensor 재생(§12.1/§11.4)은
> 실제로 닫혔고, 요청서의 모든 수치와 4개 golden digest, preflight hash를 독립 재현했다.
> 그러나 **v1.0.2가 새로 만든 결함 2건**(§11.5 per-arm 420 산술 오류, phase-7 `memory_kind` 스키마 3방향 불일치)과
> 경미한 3건이 남아 있어, **이 5건을 반영한 뒤 freeze**하는 것이 올바른 순서다. 구현·unit tests·D0는 freeze 후 승인 가능.

---

## 1. 독립 검증 수행 내역 (실행 없는 재계산)

| 검증 | 방법 | 결과 |
|---|---|---|
| preflight 무결성 | `sha256sum reports/provenance/C5_b0a/m_cohort_preflight.json` | `3ee3f1ca…837af` — §0.4 고정값과 **일치** |
| golden state digest | §12.1 frame spec 직접 구현(u32le/u8/u64le, name/dtype/shape/nbytes/LE bytes) | `43ecb58e…65712` **일치** |
| golden empty digest | SHA256 of empty bytes | `e3b0c442…855` **일치** |
| golden replay base | `sort_keys=true,separators=(',',':')` UTF-8 SHA256 | `c43ea35c…1667` **일치** |
| golden replay supplemental | 동일 (P/PA, M_NORM, donor_id=4 포함 4 records) | `38e5e2fb…f6695` **일치** (§2.9 표기와 일치) |
| preflight 산술 | val_h_lengths 기준 K별 카운트 | val≥753=**15**, val≥754=**14**, `common_ids`==val≥753 집합 **일치**, train≥753=**16**(≥10 충족), `l_excluded_at_k` 일치 |
| allowlist | train20 ∪ val20 | **40 IDs**, train∩val 교집합 **0** |
| P0 artifact | top-level 필드 확인 | `mode="p0_sanity_no_training"`, `test_split_used=false`, **`no_training` 키 없음**(legacy 호환 근거) |
| P0 수치 | JSON 직접 파싱 | train +3.7617264 [1.8916853, 5.6049574], full +3.50274, docs>0 **14/20**; val +5.2374585 [2.5013211, 8.0752724], full +5.29365, docs>0 **18/20**; real CE copy 12.7022/13.2352 > ln(250100)≈12.43 — 요청서 §3 전부 재현 |
| donor 재계산 | preflight 길이로 정렬 재현 | `04161-00002`(h_len 764)의 F/L donor = `04798(2),03991(3),05258(7),03271(9),01058(10)`; P/PA donor(전부 512, doc_id asc) = `00020,00430,01058,01127,01331` — **두 list가 다르고** v1.0.1 합성 보고서 예시와 정확히 일치 |
| per-arm replay 산술 | 15×2×2×2×3 / 20×2×2×2×3 | F/L **360**, P/PA **480**, total **1,680** — §11.5 표기 "420/420"과 **모순**(§2 신규 결함 NMF-1) |
| runner 대조 | `runner/c5_mt5_lora_b0.py` 전 수식 경로 | 경로 4종(§2.6) 동일, Adapter geometry(§2.5.4) 동일, LoRALinear(r8/α16/dropout .05/scale=α/r/kaiming a=√5/B=0) 동일, `make_labels`(add_special_tokens+truncation) 동일, `load_layer_cache(ids/lengths/h)` 동일, `set_training_mode`(base eval+adapter train+LoRA train/dropout) §2.7 일치, `native_donors_for` tie-break 동일 |
| 환경 관찰 | `data/*`는 `.gitignore` 설계상 미추적 | 본 체크아웃에 `data/external`, `data/models`, EG2 cache 부재 — **plan 결함 아님**(실행 환경 아티팩트). D0 승인 시 환경 존재 확인 필요 |

P1 manifest 확인: `p1_usage.json` = `{"p1_used": false, "test_split_read": false}` + note. §1.5 요구와 일치.

---

## 2. Q1 — 15 blocker closure

- 판정: **agree (13 closed + 2 closed-with-minor-text-residual; 실질 open 0)**

| # | blocker | v1.0.2 근거 | 독립 검증 | 판정 |
|---|---|---|---|---|
| 1 | P0 `no_training` | §4.0 `p0_path_ok` = 존재 + `mode=p0_sanity_no_training` + `test_split_used=false`; 494행 "no `no_training` key required" | artifact에 `mode` 필드 존재, `no_training` 키 부재 확인 → flag true | **closed** |
| 2 | donor basis | §2.5.6 arm별 길이 기준(F/L EG2 h_len / P/PA native 512), per-arm list, arm 내 seed 공유, tie-break doc_id asc, train20 donor 없음 | donor 재계산 일치(표 참조) | **closed** |
| 3 | replay control tensors | §12.1 npz 실 tensor + per-tensor SHA256 + `control_digest`(frame canonical), §11.4 8단계 절차, "hash-only reconstruction is forbidden" | 절차 자체 실행 가능. 무게 관찰(≈수백 MB)은 Q10 | **closed** |
| 4 | `test_split_used`/P1 | §1.5 allowlist(40 IDs) membership 판정, §4.0 NA/false 규칙, `p1_usage.json` 존재·내용 확인 | sealed test 163 스캔 없음 | **closed** |
| 5 | `h_len`/data paths | §2.6 4개 경로+필드+`h_len` 정의+`copyable_mask` raw passage | runner 상수/로더와 전부 일치 | **closed** |
| 6 | P/PA seed aggregation | §4.5 "3 registered seeds; seed mean first, then bootstrap; missing → NA; no 2-of-available" | §10.1/§10.3과 정합 | **closed** |
| 7 | P/PA alias / `M_CONTROL_INVALID` | §4.5 validity(무결성)↔calibration 분리 = 합성보고서 Option B 채택; §5.4 라우팅 | v1.0.1 481행 `P_VALID = ANDn(P_POS_PASS,P_NORM_PASS)` 대비 실질 재정의 확인; 도달성 회복(Q3 상세) | **closed** |
| 8 | copy-token `<5` | §2.5.5 signal/eval=제외 / primary M=`endpoint_ok=false`→`M_NOT_EVALUABLE` 2분리 | §9.5 `copy tokens >=5`·`no missing key`와 모순 해소 | **closed** |
| 9 | phase-7 recipe | §9.6.1 K_d=min, control crop(not rebuilt), 600/arm-seed, diagnostic-not-gate, baseline 저장 | 600 산술 ✓. 단 기록 도메인이 §12.2와 불일치(NMF-2) | **closed (minor residual)** |
| 10 | threshold asymmetry | §4.5 "threshold asymmetry is intentional … No post-result change" | `.05`(P/PA·L signal) vs `>0`(M_PASS) 구조 일관 | **closed** |
| 11 | F11 label | §7.2 F11=`INCONCLUSIVE_SMALL_N_WITH_L_SIGNAL`+triple, §7.3 small-N 우선·INVALID 보존·l_signal false 시 copy-only/full-only/plain 순서 | §6.2 enum 존재 | **closed** |
| 12 | training mode/RNG | §2.7 모드 표(4 arm)+`model.train()` 금지+fresh state+RNG 순서(seed→adapter→LoRA, reseed 없음)+parameter inventory | runner `make_adapter`/`train_arm`/`set_training_mode` 일치 | **closed** |
| 13 | T_proj primary replay | §11.5 `t_primary_replay_arm` 추가, D1 560/registered 1,680 분리 | 식 자체는 closed. 단 per-arm 상수 오류(NMF-1) | **closed (minor residual)** |
| 14 | D1 no-labels/`not_a_result` | §11.3 decision/signal 라벨 없음 + target-token CE용 라벨은 계산 + `not_a_result:true` | 명시적 | **closed** |
| 15 | golden coverage | `golden_vectors.json` spec="C5 Phase 6 P/M v1.0.2" + supplemental(P/PA·M_NORM·donor 0..4) 4 digest | 4종 digest 전부 독립 재현 ✓. §13.4 테스트 목록에 supplemental 누락(NMF-3) | **closed (minor residual)** |

- 다음 단계:
  1. NMF-1/NMF-2 텍스트 교정을 freeze 직전에 반영(아래 §11).
  2. §13.4에 supplemental golden 1줄 추가(NMF-3).
  3. Q1의 "closed" 판정은 구현·unit test로 재확인하는 것을 조건으로 기록한다.

---

## 3. Q2 — Self-containedness

- 판정: **conditional agree**
- 근거:
  - §2.5가 tokenizer/loss/mask/donor/decoding을 전부 normative로 고정("No implementation may substitute…")하고 §2.6이 4개 데이터 경로와 `h_len`을, §2.7이 RNG 순서를 고정한다. §3–§9는 모델·데이터에 의존하지 않는 순수 결정 함수로 기술되어 있다. 구현자가 이 문서만으로 코드를 쓸 수 있는 수준이다.
  - 기존 helper 모듈(`runner/c5_mt5_layer_probe.py`의 `Adapter`/`make_labels`/`load_layer_cache`, `runner/c5_a1_lora.py`의 `LoRALinear`)의 실제 구현이 §2.5.4/§2.5.1/§2.6 서술과 정확히 일치함을 확인했다. 즉 spec이 암묵 지식을 inline으로 흡수했다.
  - K_M=753 선택 규칙 본문은 preflight artifact(`k_selection_rule`)에만 있지만 §0.4 content-hash로 고정되어 있어 참조 안전성이 확보된다.
- 남은 외부 참조·암묵 지식:
  1. helper 모듈의 **경로/커밋 해시 미기재** — freeze manifest에 기록 권고(모듈이 미래에 변해도 §2.5 서술이 우선한다는 점은 이미 명문).
  2. §11.2 D0의 "≤4 configs"에서 **config의 정의 미비**(4 arm 구성인지, mechanics 체크 4종인지).
  3. 데이터/캐시/모델 파일은 git 추적 대상이 아니므로 D0 실행 환경에서의 존재 확인은 별도 절차다(본 검토에서 splits.json 존재만 확인).
- 다음 단계:
  1. freeze manifest에 helper 모듈 경로+commit hash 기록.
  2. §11.2에 config 정의 1줄 추가(should-fix).
  3. D0 실행 환경 점검 목록에 §2.6 4경로 존재 확인 추가.

---

## 4. Q3 — Validity/calibration 분리와 `M_CONTROL_INVALID` 도달성

- 판정: **agree**
- 근거:
  - v1.0.1(481행)은 `P_VALID = ANDn(P_POS_PASS, P_NORM_PASS)`로 validity=calibration이었고, §5.4가 `p_valid false → M_NOT_EVALUABLE`로 먼저 탈출하므로 `M_CONTROL_INVALID`는 논리적으로 불가도달이었다(합성보고서 MF-7 확인).
  - v1.0.2 §4.5는 `P_VALID` = (P step100 path valid) AND (seed별 20 native × 2 variants × 2 endpoints × 2 memory kinds = **160 records/seed**, ×3 seeds = **480 records/arm** 존재·유한) AND (no test/P1 ID)로 **무결성** 재정의하고, `P_POS_PASS`/`P_NORM_PASS`/`PA_*`를 **calibration**으로 분리했다. `m_valid = ANDn(m_pass_pos_p, m_pass_norm_p, m_pass_pos_pa, m_pass_norm_pa)` (§5.2).
  - §5.4 라우팅: `p_valid/pa_valid false → M_NOT_EVALUABLE`, `m_valid false → M_CONTROL_INVALID`. 따라서 **P/PA artifact가 완전·유한한데 보정이 실패하는 경우에만** `M_CONTROL_INVALID`가 도달한다 — unconditional이 아니다.
  - 무결성 실패는 `M_NOT_EVALUABLE`(validity tier에서는 `P_STEP100_NOT_VALID`)로 분리되므로, `P_VALID`를 약화시켰다는 Q10 우려는 기각된다: 무결성 바(480 records/arm)는 실재하는 게이트이고, `m_evaluable`(§5.1: cohort/endpoint/seed/replay/builder)이 선행 gate로 작동한다.
  - `p_valid := P_VALID`, `pa_valid := PA_VALID` 바인딩과 §4.6 tier precedence(F3/F4/F9/F10 순서)를 코드 순서와 대조해 모순 없음을 확인했다.
  - threshold 정합성: P/PA calibration copy `>= .05` + full `> 0` (§4.5), M_PASS_L copy `> 0` + full `> 0` (§9.6.1), L signal copy `>= .05` (§3.5) — 세 값의 역할 차이가 §4.5 note로 명시되어 있고 결과 후 변경 금지가 명문이다. 내적 모순 없음(의도 기록 완료).
- 다음 단계:
  1. unit test 3케이스 고정: (i) `p_valid=false`+`pa_path=false` → `P_STEP100_NOT_VALID`, (ii) `m_evaluable=true`+`p_valid=pa_valid=true`+`m_valid=false` → `M_CONTROL_INVALID`, (iii) `p_valid=NA`+`m_valid=false` → `NOT_ASSESSABLE`.
  2. `L_SIGNAL_M_CONTROL_INVALID`/`NO_L_SIGNAL_CONTROL_INVALID` 라벨 도달 테스트를 §13.1에 명시(이미 항목 존재 — 케이스 값 명시).
  3. dispatch 출력 triple `(validity, control, signal)` 보존을 F11과 함께 회귀 고정.

---

## 5. Q4 — Donor

- 판정: **agree**
- 근거:
  - §2.5.6이 길이 기준을 arm별로 분리했다(F/L=EG2 layer19 `h_len`, P/PA=native "summarize: " 512-truncated 길이). v1.0.1의 "same donor set for all arms/seeds"(v1.0.1 259행) 모순이 제거되었다.
  - 재계산 검증: `04161-00002`(EG2 764)의 F/L donor top-5는 `04798,03991,05258,03271,01058`, P/PA는 native 전부 512라 tie-break doc_id asc로 `00020,00430,01058,01127,01331` — 서로 다르며 각각 결정적이다. P/PA donor는 사실상 doc_id 오름차순 first-5(자기 제외)로 완전히 특정된다.
  - arm 내 seed 동일 list / `donor_id 0..4` / `K=min(len(real),len(donor))` / `shuffled`=wrong-donor(토큰 셔플 아님) / wrong CE와 real CE가 동일 5 donor crop 평균 / train20 donor pool 없음 — 전부 명문이고 runner의 `donors_for`(EG2)/`native_donors_for`(native)가 동일 정렬 규칙을 구현한다.
  - F/L 내부 paired 비교(F vs L)는 같은 EG2 donor list를 공유하고, P vs PA도 같은 native list를 공유하므로 **집단 내 비교는 오염되지 않는다**. 집단 간(F/L vs P/PA) donor가 달라지는 것은 §11.4가 이미 "not comparable as same population"으로 선언한 영역(phase 7)에만 영향을 주며, phase 7은 gate가 아니다.
- 다음 단계:
  1. donor list artifact에 `arm`, `length_basis` 필드를 명시해 저장(감사용).
  2. unit test: 두 basis의 donor list가 같은 rid에 대해 서로 다름을 assert(회귀 방지).
  3. 구현 시 F/L donor 길이는 cache `lengths[i]`(§2.6)를 사용하고 `h.shape[0]` 대체를 금지하는 inventory assert 추가.

---

## 6. Q5 — Control tensors / replay 실행 가능성

- 판정: **conditional agree**
- 근거:
  - §12.1: `control_manifest/arm/seed/M_POS_MEAN.npz`, `control_manifest/arm/seed/M_NORM/t.npz`, `control_manifest.json`(path/dtype/shape/SHA256 per tensor), `control_digest`=canonical tensor frame SHA256. replay는 tensor를 **load**해 digest를 검증한 뒤 CE를 재계산하고, hash-only reconstruction을 금지한다. v1.0.1 MF-3("hash cannot supply tensors")의 요구를 정확히 충족한다.
  - §11.4 절차는 8단계로 완전하다: (state+manifest 로드·digest 검증) → (모드 복원: base/adapter/LoRA eval) → phase-5 1,680 재계산 → `atol=1e-5, rtol=1e-4` 비교 → phase-7 600/arm-seed 별도 → `replay_ok`는 primary 1,680 기준 → phase-7 실패는 primary `replay_ok`에 영향 없음 → 재학습 금지.
  - 파일 규모: F/L은 arm-seed당 M_POS_MEAN 1개(753×512×4B≈1.5MB)+M_NORM 15개, P/PA는 1개(1MB)+20개 → 총 **222개 npz**, 대략 200~400MB. 12 units 규모에서 실행 가능하다.
  - debug/final 분리: `debug_replay_hash`(D1 synthetic)와 `final_replay_hash`(registered postrun) 분리 필드 + 직접 비교 금지(§11.4/§12.2) — 충분하다. 허용오차는 CE≈O(10)에서 절대+상대 혼합으로 스레드 순서 비결정성을 흡수하면서 텐서 대체(≈≫1e-3 시프트)는 잡는다. 대체 자체는 digest가 막는다.
- 잔여(실행 가능성에는 영향 없으나 freeze 전 명확화 필요):
  - **NMF-2**: §9.6.1은 phase-7 기록의 `memory_kind ∈ {real, donor}`, §12.2는 `memory_kind ∈ {control,real}`로 기술하며, golden supplemental은 실제로 `donor` 레코드를 포함한다(내 재현으로 확인). canonical 스키마는 최소 `{control, real, donor}`를 허용해야 하고, phase-7에서 variant 축이 real/donor 레코드에서 퇴화(duplicate)함을 명시해야 한다. 600 산술 자체는 어느 해석에서도 유지된다.
- 다음 단계:
  1. NMF-2 정합화를 ERRATA(또는 freeze 전 수정)로 반영.
  2. npz 내부 배열 이름/키 스키마 1줄 pin(예: `tensor`, `target_id`, `variant`, `arm`, `seed`).
  3. replay unit test가 supplemental digest 검증까지 포함하도록 §13.4 보강(NMF-3).

---

## 7. Q6 — Allowlist / P1

- 판정: **agree**
- 근거:
  - §1.5: allowlist = frozen `train20_ids ∪ val20_ids`(40 IDs, 교집합 0 — 재확인). `test_split_used`는 **artifact 내 ID의 allowlist 소속**으로만 판정하고 sealed test 163을 스캔하지 않는다. v1.0.1 MF-4의 순환("증명하려면 봉인 데이터를 훑어야 함")이 제거되었다.
  - `p1_usage.json` 실존 + `p1_used:false`, `test_split_read:false` 확인. `assay_path_ok`는 preflight content-hash 일치(재현 확인) + ID 일치 + `test_split_used=false` + `p1_used=false` manifest 존재를 요구한다.
  - 누락/위조 경로: preflight hash 불일치 → `assay_path_ok=false` → `ASSAY_INVALID`(§4.2); `p1_used:true` → false → `ASSAY_INVALID`; manifest missing → `assay_path_ok=NA`(§1.5) → `NOT_ASSESSABLE`(§4.3). "known failure (false) dominates unknown (NA)" 원칙이 §4.0에 명문이다. F1/F2/F5/F6 fixture가 이 축을 고정한다.
- 잔여: `p1_usage.json`이 존재하지만 **필드가 누락/변형**된 경우(malformed)의 처리가 §1.5에 명시되어 있지 않다(합성보고서 MF-4 요구 "malformed → NA or false per known-failure rule"의 반쪽). 1줄로 닫힌다.
- 다음 단계:
  1. §1.5에 "malformed/필드 누락 → NA" 1줄 추가(should-fix).
  2. malformed-manifest unit test 1개 추가.
  3. artifact ID 수집 대상(허용되는 artifact 목록)을 §1.5에 명시(동일 ID가 여러 artifact에 나올 때의 판정 규칙).

---

## 8. Q7 — Data paths / h_len

- 판정: **agree**
- 근거:
  - §2.6: F5 JSONL 경로+필드(id, passage, summary), splits 경로+필드(train/val/test), EG2 cache 경로+npz 필드(ids, lengths, h; `h_len=lengths[i]`), native 토크나이저 경로+`h_len` 정의. `runner/c5_mt5_lora_b0.py`의 `MODEL`/`DATA`/`SPLITS`/`CACHE` 상수와 정확히 동일하다.
  - `h_len`은 항상 source sequence length이며 tensor shape이 아님 — 두 arm군 모두에 일관 적용. `copyable_mask`는 raw passage(접두어 없음) 기준 — runner `copyable_mask(rows[rid]["passage"], …)`와 일치.
  - P/PA all-512 가정: preflight `train_native_lengths`/`val_native_lengths` **40개 전부 512**(truncation cap)로 확인 — §2.5.6의 괄호 주석("(all 20 val docs are 512)")은 사실이고 donor tie-break이 결정적 동작을 보장한다.
  - JSONL은 `id`로 읽고 행 순서 의존 금지, test split 미독 — 명문.
- 다음 단계: 없음(구현은 §2.6 그대로). 강제할 것은 없으나, 구현 PR에서 경로 상수가 §2.6과 일치하는지 inventory로 1회 확인 권고.

---

## 9. Q8 — M arithmetic

- 판정: **agree — 단 §11.5의 per-arm 상수 1건 예외(NMF-1)**
- 근거:
  - mixed 1,680 = common 15×**96** (=4 arms×3 seeds×2 variants×2 endpoints×2 memory) 1,440 + native-only 5×**48** 240 — 재계산 일치. exact key set, 중복/누락 금지, 96회 출현 검증(§9.5) 일관.
  - D1 phase 5 **560** = F/L 120×2 + P/PA 160×2 — 일치. phase 7 **600** = 15×5×2×2×2 — 일치. 15+5, 96/48 — 일치.
  - `M_POS_MEAN` shape `[K_M,512]` (F/L [753,512], P/PA [512,512]), `M_NORM(t)=M_POS_MEAN×(‖real_prefix_t‖/‖M_POS_MEAN‖)` 단일 방향+스칼라 크기 — §9.2/§9.3과 self-consistent. `K_M` 753/512 분리(M-only rule §2.3) 유지.
  - `endpoint_ok`(§9.5)와 `m_evaluable`(§5.1) 조건 세트가 서로를 반복 없이 참조하며 모순 없음. `builder_ok` contributors 요건(F/L 15 대상 16 contributors, P/PA 20 대상 20) preflight와 일치.
  - **예외**: §11.5 "registered primary replay = 1,680 total; per arm F/L 420, P/PA 420" — 420×4=1,680으로 총합만 맞고, cohort 분리(15 vs 20)와 모순. 올은 값은 **F/L 360, P/PA 480**. 같은 줄의 `t_primary_replay_arm` "(D1 120/160; registered 420)"도 동일 오류를 전파한다.
- 다음 단계:
  1. §11.5 숫자 교정 360/480(NMF-1, 등록 수치의 정정이지 threshold 변경이 아님).
  2. unit test: 1,680 exact mixed key set + common 96회/native-only 48회 + 총합 3방향 검산.
  3. §13.2에 per-arm-seed 120/160 assert 추가.

---

## 10. Q9 — D0/D1/cap

- 판정: **conditional**
- 근거:
  - 산술은 모두 맞다: D0 0 update / D1 4 units(4 arms × 1 debug seed 20261111, 1 update/arm) / 등록 12 units×100=**1,200 updates** / prospective max **1,204** = 1,200+4 / **155 min** = 120(registered)+20(D1)+15(D0) / 8 phases / phase 5 560 / phase 7 600. §11.5 T_proj는 이제 `t_primary_replay_arm`을 포함하고 phase별 실측 기반 projection(≤96 min)이며 120-min hard abort가 있다.
  - 조건 1: §11.2 "≤4 configs"의 config 정의가 없다(D0가 8 phases 중 무엇을 하는지 간접만 유추 가능).
  - 조건 2: D1 ≤20 min cap 안에 generation(20 docs×256 tokens×4 arms = 80 시퀀스 greedy decode, CPU 6 threads)이 들어가는지는 미검증 리스크다. T_proj gate와 120-min hard abort가 방어적이지만, D1 자체가 generation 단계에서 abort하면 "8 phases 모두 측정" 요건(결측 phase → projection 불가)이 실패한다. 숫자 변경 제안은 하지 않는다(결과 후 변경 금지 원칙 및 사전등록 존중) — 리스크 기록만 한다.
  - 조건 3: NMF-1(420 오류)이 `t_primary_replay_arm`의 registered 상수 정의를 오염시킨다(총합에는 영향 없음).
- 다음 단계:
  1. §11.2에 config 정의 1줄 추가.
  2. NMF-1 교정.
  3. D1 승인(별도) 시 generation 포함 소요를 D1 자체 실측으로 확인하도록 요구 — cap은 그대로 유지하고 미달 시 D1 재사전등록으로 분리(신규 숫자 제안 아님, 절차 지침).

---

## 11. Q10 — 남은 Must-fix (v1.0.2 신규 결함 포함, ranked)

- 판정: **conditional** (아래 5건 존재 — 1·2는 freeze 전 반영 권고, 3·4·5는 should-fix)

| 순위 | ID | 내용 | 근거 | 심각도 |
|---|---|---|---|---|
| 1 | **NMF-1** | §11.5 per-arm registered replay "F/L 420, P/PA 420" 오류. 올바른 값 **F/L 360, P/PA 480**(총 1,680 불변). `t_primary_replay_arm` "(registered 420)" 동일 오류 전파 | 15×2×2×2×3=360, 20×2×2×2×3=480 재계산; 420=1,680/4는 균등 분할 가정의 착오 | 중 — normative 수식의 수치 오류 |
| 2 | **NMF-2** | phase-7 기록 도메인 불일치: §9.6.1 `memory_kind ∈ {real,donor}` vs §12.2 `{control,real}` vs golden supplemental(실제 `donor` 레코드 포함 — 재현 확인). canonical 스키마가 `donor`를 허용한다는 것과 phase-5(primary: control/real, donor_sort=-1)와 phase-7(supplemental digest)의 도메인 구분, variant 축의 퇴화 여부를 명확히 해야 supplemental digest 검증 정의가 확정된다 | 세 문장 상호 모순; golden이 `donor`를 사용 | 중 — replay 검증 대상 정의 미확정 |
| 3 | **NMF-3** | §13.4 hash/replay tests에 supplemental golden `38e5e2f…` 누락(§12.3에는 정의됨) | §13.4 줄목록 대조 | 소 — 테스트 매트릭스 1줄 |
| 4 | **NMF-4** | `p1_usage.json` malformed/필드 누락 시 NA/false 처리 미명시 | §1.5 대조 | 소 — 1줄 |
| 5 | **NMF-5** | D0 "≤4 configs" 정의 미비 | §11.2 | 소 — 1줄 |

요청된 3개 특별 확인에 대한 답:

1. **`P_VALID` 약화 → `M_CONTROL_INVALID` unconditional화?** 아니오. `M_CONTROL_INVALID` 도달에는 (a) `m_evaluable=true`(cohort/endpoint/seed/replay/builder 전부 통과), (b) `p_valid=pa_valid=true`(480 records/arm 존재·유한+경로 양호), (c) `m_valid=false`(P/PA calibration 실패)가 모두 필요하다. 무결성 실패는 `M_NOT_EVALUABLE`로 갈라지므로 INVALID는 조건부 도달이다. 오히려 v1.0.1의 "validity가 사실상 pass였던" 상태가 의미 있게 분리되었다.
2. **`control_manifest` 과중?** 222 npz / 수백 MB 수준으로 12-unit 규모에서 허용 가능. `M_NORM(t)`를 스칼라 ratio+base로 저장하면 크기가 ~1/15로 줄지만 그것은 spec 변경이므로 freeze 전에만 결정 가능하며, **현재안(실 tensor 저장)이 replay 안전성에서 우월하다 — 유지 권장**. 변경 제안 아님.
3. **donor arm-specific이 F/L/P/PA 비교를 해치는가?** 아니오. 모든 M/신호 비교는 arm 내부(control vs real, P vs PA, F vs L paired)이고 각 집단은 자기 basis의 donor list를 공유한다. 집단 간 donor 차이는 diagnostic(phase 7)에만 나타나며 gate가 아니다. §11.4 "not comparable" 선언과 정합.

이 외에 v1.0.2가 만든 문제로 의심되는 것을 추가로 찾지 못했다. 잔여 리스크(결함 아님): D1 generation 실현성(§10 조건 2), 데이터 아티팩트의 실행 환경 존재 여부.

- 다음 단계:
  1. NMF-1/NMF-2를 freeze 전 텍스트 교정으로 반영(NARROW 범위 내).
  2. NMF-3/4/5를 같은 커밋에 포함(1줄씩).
  3. 교정 후 freeze commit hash + content SHA-256 기록(§16.2 절차 준수).

---

## 12. Q11 — 동결·구현 승인

- 판정: **conditional yes**
- 근거: 위 Must-fix 1–2(및 권고 3–5)는 모두 text-only이고 등록된 과학적 선택(threshold/seed/donor/step/LR/cohort)을 전혀 바꾸지 않는다. §16.1의 "If NARROW: must-fix only; no new scientific choices" 범위 안이다. 반영 후 v1.0.2는 단일 구현 권위로 freeze 가능하다(§0.1). freeze 전에는 코드 금지("No code before freeze") 유지.
- 구현 전 필수 test (§13 확장판, 우선순위 순):
  1. golden 4종 digest(state/empty/base/**supplemental**) 재현 — canonical JSON sort_keys/separators, donor_sort -1/0..4 포함.
  2. F1–F11 전 케이스 + §4.6 tier precedence 회귀.
  3. fixtures 16–18 + §3.4 9 L pairs + ANDn/ORn/NOT3 의미론.
  4. `M_CONTROL_INVALID` 도달 3케이스(Q3) + `M_CONTROL_NOT_VALID` 부재.
  5. M 산술: 1,680 exact mixed key set, 96/48, 560, 600, `[K_M,512]` shape, `endpoint_ok` 전 조건, zero-margin abort(753/754→14).
  6. donor: arm별 list 차이 + tie-break + `donor_id 0..4` + arm 내 seed 공유.
  7. allowlist: 외부 ID → `test_split_used=true` → `ASSAY_INVALID`; missing → NA; malformed manifest.
  8. stats: seed 20261109, seed-average-before-bootstrap, missing seed NA, `documents_positive`/`seeds_positive` 분리, legacy `bootstrap_paired`(seed 20261108·doc count 오라벨링) 미재사용.
  9. hash: state frame spec(§12.1), debug/final 분리, numeric-vs-exact 구분.
  10. §13.5 금지 목록 전수(예: `no 0..20`, `no PA only`, `no delta_memfree`, 753 학습 요구 금지).
- 다음 단계:
  1. Must-fix 반영 → freeze(§16.2).
  2. 위 10종 unit test를 구현 PR의 DoD로 고정.
  3. 구현은 freeze hash만 참조(§16.2).

---

## 13. Q12 — B0-B / D1 / 3-seed 경계

- 판정: **agree**
- 근거: §0.2/§0.3/§11.5("D1 없이 3-seed 금지")/§14("EXPLORATORY_L_SIGNAL alone not approval", "no B1/B2/Stage C auto")가 경계를 충분히 강제한다. 본 라운드는 B0-B/D1/3-seed를 승인하지 않는다.
- B0-B predicate의 v1.0.2 label 재진술:

```text
B0-B 검토 가능 조건 (재진술):
  validity_status == VALID
  AND control_status == M_CONTROL_PASS
  AND signal_status == EXPLORATORY_L_SIGNAL
  AND m_valid == true            # M_CONTROL_PASS의 필수 전제지만 명시 유지(무해)
  AND m_evaluable == true        # §5.1 (M_CONTROL_PASS 도달의 전제)
  AND n_signal == 15             # "max 15; >=15 means exactly 15" (§14)
  AND tail_driven == false       # signal tail 기준(§10.4); true/NA 불가
  AND test_split_used == false AND assay_path_ok == true (leakage/mode/metric pass)
  AND artifact complete (checkpoint/manifest/replay hash 포함)
  AND 별도 사전등록/승인 존재
```

  - 주: §6.3 dispatch상 `EXPLORATORY_L_SIGNAL` 도달은 이미 validity VALID + `M_CONTROL_PASS` + `n_signal=15`를 함축하므로, 재진술의 앞 3항이 사실상 지배 조건이고 `tail_driven==false`와 별도 승인이 실질 추가 조건이다. `full_k_secondary`/P0/`PA_RETENTION`은 증거가 아니다(§14).
- 다음 단계:
  1. 위 재진술을 B0-B 별도 사전등록 서두에 그대로 인용.
  2. `tail_driven` 산출 근거(signal tail, top3_abs_share) artifact 필드 고정.
  3. D1 승인 문서에 "D1 결과는 `not_a_result:true`로 라벨·게이트에 유입 불가"를 재확인.

---

## 14. Q13 — 최종 판정 및 freeze

```text
최종 판정: NARROW
v1.0.2 freeze:      승인 가능 — 단, Must-fix NMF-1/NMF-2(필수)와 NMF-3/4/5(권고, 각 1줄)를
                    freeze 직전 텍스트로 반영한 뒤 §16.2 절차(hash+content SHA-256)로 동결.
                    등록된 과학적 수치·선택 변경 없음.
구현+unit tests:    freeze 커밋 이후 승인. §13의 10종 필수 test(§12 Q11)를 DoD로.
D0:                 freeze 이후 승인 가능. 0 optimizer updates, ≤4 configs(정의 보강 후),
                    ≤15 min, seed 20261111, labels_computed:false, not_a_result:true,
                    등록 cap과 별도, timing claim 금지, h-length assert 포함.
D1:                 이번 라운드 승인 아님(별도 승인 대상). 4 units/1 update/≤20 min 유지.
3-seed:             미승인. D1 완료+별도 승인 후에만.
금지 범위:          Phase 6 registered 실행, B0-B/B1/B2/Stage C 자동 진행, test 163 개봉,
                    P1 사용·외부 API, T5Gemma2(D-108 STOP), 15→14·native→common 치환,
                    결과 후 threshold/seed/donor/step/LR 변경, 사전 승인 없는 D0/D1 합편.
최대 compute:       이번 승인으로 실행되는 것은 freeze 이후 D0뿐 — D0 ≤15 min(0 update).
                    등록 상한은 계획 그대로 유지: 12 units / 1,200 updates / 120 min wall /
                    6 threads / GPU 없음 / retry 없음, T_proj ≤96 min gate,
                    prospective max 1,204 updates / 155 min (grant 아님).
Must-fix (ranked):  1) §11.5 per-arm 420→360(F/L)/480(P/PA) 교정 [필수]
                    2) phase-7 memory_kind 도메인 정합화(§9.6.1 vs §12.2 vs golden) [필수]
                    3) §13.4 supplemental golden 추가 [권고]
                    4) p1_usage malformed 규칙 명시 [권고]
                    5) D0 "≤4 configs" 정의 [권고]
v1.0.2 self-contained: 예 — 조건 2건: (a) freeze manifest에 helper 모듈 경로+commit hash 기록,
                    (b) NMF-2 정합화 후 replay 검증 대상 확정. K-selection은 hash-frozen preflight로 안전.
잘못된 전제:        요청서 기재 "기준 HEAD 1f6b816"은 현재 origin/main(445a9cc→ee99fd0)과 다르지만
                    검토 대상 파일은 무변동이라 영향 없음. "15 blockers 모두 closed"는
                    13 closed + 2 minor-residual로 정밀화하는 것이 정확하다. 그 외 전제
                    (P0 수치, 1,680/560/600, golden digest)는 전부 독립 재현되어 유효.
```

---

## 15. 검증 로그 (재현성)

사용한 읽기 전용 명령: `git fetch origin`, `git pull --ff-only origin main`(sync 시점 "Already up to date", 이후 deepen으로 확인된 원격 진행분 ff), `sha256sum`, `python3 -c`(golden frame/canonical-JSON SHA256 재계산, preflight 산술 검증, donor 정렬 재현, per-arm 산술), `sed`/`grep`/`cat` 본문 독해. 학습·평가 실행, test 163 개봉, P1 접근, 서브에이전트 호출 없음. 작성한 파일은 본 보고서 1개뿐이다.

## 16. 제한

- 본 보고서는 승인이 아니라 독립 검토 의견이다. 최종 동결·승인 결정권은 계획 소유자에게 있다.
- 승인해도 실제 실행되는 것은 없다(이번 라운드에서 구현·D0조차 시작되지 않음; 본 보고서는 자격만 진술).
- P0는 여전히 untrained native-path sensitivity이며 trained P/PA/L의 증거가 아니다(학습된 P/PA/M 결과는 아직 어떤 것도 존재하지 않는다 — 요청서 전제와 일치).
- golden digest는 상수이지 결과가 아니다.