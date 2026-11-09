# C5 Phase 6 P/M Prereg v1.0.1 — External Review

- 작성일: 2026-11-09
- **Reviewer: GLM 5.3 Flash (OpenRouter `z-ai/glm-5.3-flash`, reasoning max) — independent external reviewer for this round.** This report is written from my own reading of the repository artifacts at the review HEAD. No other model's review text was reused; no subagents or additional LLMs were called.
- 검토 기준 HEAD: `30b62191afe88d0a36389871e3a69fc524b4bbaa` (origin/main)
- 동기화: `git fetch origin` → `git pull --ff-only origin main` → "Already up to date"; working tree clean. 요청서 표기 기준 `7ecf973` 대비 현재 HEAD는 리뷰 요청서 추가 커밋(`30b6219 docs: add C5 P/M v1.0.1 review request`)이 선행하는 수준이며, 검토 대상 문서 내용 SHA-256은 `d11a234580e89b0a351f08f0d518da7dc63094437ffeddd6b02cf5016e64e1b5`이다.
- 제약 준수: 학습·평가 미실행 / test 163 미개봉 / P1 미사용 / 저장소 수정 없음(이 파일만) / 서브에이전트·추가 LLM 없음 / T5Gemma2 D-108 STOP 유지 / Phase 6·B0-B·B1·B2·Stage C 승인 없음.

---

## 0. Independent verifications performed (read-only)

이 리뷰에서 직접 재계산·재현한 결과. 학습/평가가 아니라 순수 해시·통계 재계산이다.

| # | 검사 | 방법 | 결과 |
|---|---|---|---|
| V1 | preflight content hash (§0.4) | `sha256sum reports/provenance/C5_b0a/m_cohort_preflight.json` | `3ee3f1ca…37af` — **일치** |
| V2 | golden state digest (§12.3) | frame spec을 직접 재구현하여 SHA256 | `43ecb58e…d65712` — **일치** |
| V3 | golden empty digest | SHA256 of empty byte string | `e3b0c442…b855` — **일치** |
| V4 | golden replay digest (§12.3) | canonical JSON(`sort_keys`, `(',',':')`) 재직렬화 후 SHA256 | `c43ea35c…f7851667` — **일치** |
| V5 | P0 통계 재계산 | `p0_native_sanity.json` per-doc deltas | train mean Δcopy **3.7617**·positive 14/20, val **5.2375**·18/20, val median **2.9739**, signed top3 **.4862**, absolute **.43355**, mean Δfull 3.5027/5.2936 — **모두 일치** |
| V6 | endpoint 산술 | 15×96 + 5×48 = 1,440+240 = **1,680**; phase 5 = 120+120+160+160 = **560**; phase 7 = 15×5×2×2×2 = **600**/arm-seed | 일치 |
| V7 | cap 산술 | 1,200+4 = **1,204** updates; 120+20+15 = **155** min; T_proj ≤ **96** < 120 hard abort | 일치 |
| V8 | cohort 산술 (preflight) | train contributors(h≥753) = **16**; val eligible = **15**; excluded 5 IDs = `l_excluded_at_k`와 일치; K=754 → **14** | 일치 |
| V9 | 테스트 인벤토리 | `eval/tests` 내 test 함수 수 = 2+1+7+11+10+11+12 = **54** | "54 tests historical"과 일치 (P/M prereg 테스트는 아직 없음) |
| V10 | 코드↔문서 대조 | `runner/c5_mt5_lora_b0.py`, `runner/c5_mt5_layer_probe.py`, `runner/c5_a1_lora.py`, `eval/tests/test_c5_b0_metric.py` vs §2.5 | same-position CE(무 shift), copyable mask 규칙, donor 규칙(self 제외·길이정렬·doc_id tie-break), 64 LoRA 모듈, `kaiming_uniform_(a=√5)` A / zeros B, Adapter 512→512→GELU→512→LayerNorm, labels=native special token 포함 — **일치** |
| V11 | ln\|V\| 하한 | mT5 vocab 250,100 → ln ≈ **12.4296** | "12.43" 일치; untrained real CE 12.70/13.24 > 하한 ✓ |
| V12 | stale-ref / 금지 용어 스캔 | v1.0.1 전문 grep | `r3.x`/`v0.2`는 §0 헤더(대체 선언)와 §15 traceability에만 존재; `delta_memfree`, `M_CONTROL_NOT_VALID`, `PA only`, `0..20`은 금지 선언문에만 존재 |

미검증 항목(명시): P0 bootstrap CI 끝점([1.8917, 5.6050], [2.5013, 8.0753])은 재샘플 RNG 재현에 numpy가 필요한데 리뷰 샌드박스에 numpy가 없어 재계산하지 못했다. seed-독립 통계(평균·중앙값·top3·positive 수)는 모두 독립 재현되었으므로 CI 값 자체의 추가 검증은 낮은 리스크로 남긴다.

---

## 1. Q1–Q13 판정

### Q1. Self-containedness

- 판정: **conditional**
- 근거: §0.1의 단일 구현 계약 주장이 구조적으로 성립한다. 규범 구역(§1–§14)에는 r3.x 의존 문장이 없다(V12: r3/v0.2 문자열은 대체 선언과 §15 traceability에만 존재). §2.5가 측정 경로(모델/토크나이저/접두사/길이/손실/mask/donor/디코딩/초기화)를 코드-참조 없이 규범적으로 고정(MF-5 closed), §4.0이 4개 path flag를 tri-state로 정의(MF-4), §11.4가 8단계 replay 절차와 numeric tolerance·debug/final 분리(MF-6), §12가 해시 프레임과 `control_digest`(MF-7)를 정의한다. 그러나 여전히 non-total 지점이 3개 있다: (i) phase-7 donor-level 레코드의 **내용**(control 텐서가 무엇인지) 미정의 — 개수 600/arm-seed만 존재(R2); (ii) §2.5.6 donor 규칙을 문자 그대로 적용하면 train20 문서의 donor가 val20에서 뽑히는데 이를 명시하지 않음(R4); (iii) §2.5.5 "copy tokens <5 → copy endpoint 제외"와 §9.5 exact-key-set("copy tokens ≥5", "no missing key")이 서로 다른 방향을 가리킴(R1).
- 다음 단계: ① R1–R4를 번호 붙은 ERRATA로 반영(텍스트 전용); ② ERRATA 후 stale-ref 재스캔; ③ freeze commit + content SHA-256 발행.

### Q2. Decision contract

- 판정: **agree**
- 근거: §4.2–§4.4 체인이 total이다 — 5개 tri-state path flag × `p_valid`/`pa_valid`의 모든 조합이 5개 값 중 하나로 종결된다. F1–F11을 §4 논리와 대조해 전수 확인했다(예: F5 = assay NA + p_step false → §4.2 known-failure-first에 의해 `ASSAY_INVALID`; F3/F4는 §4.6 순서 규칙과 정확히 일치). §3.4는 9개 (l_copy, l_full) 쌍을 모두 정의하고 false+NA → `NOT_ASSESSABLE`을 고정한다. §6.3 dispatch는 n_signal {NA,0..15} × validity × copy_only/full_only × control(5값) 조합을 fallback `NOT_ASSESSABLE`까지 포함해 덮으며, fixtures 16–18의 derived 값(16→`EXPLORATORY_L_SIGNAL`, 17→`MEAN_CONTRAST_ONLY`, 18→`M_CONTROL_FAIL`/`NO_AFFIRMATIVE_CONTENT_USE_EVIDENCE`)이 §5.2/§5.4와 일치한다. small-N이 validity를 숨기지 않는다는 §6.4도 dispatch와 정합이다.
- 다음 단계: ① decision 로직을 모델/데이터 비의존 순수 함수로 먼저 구현; ② 어떤 데이터 접촉도 전에 F1–F11 + 9 pairs + fixtures 16–18 유닛 테스트 통과(§13.1); ③ F11의 triple 보존(validity INVALID가 small-N 라벨과 병기) 테스트 추가.

### Q3. Mixed M domain

- 판정: **agree**
- 근거: mixed domain이 문서 전체에서 한 번만 정의되고 일관되게 사용된다. §9.1(F/L 15 common @753, P/PA 20 native @512), §9.5(15 common ×96 + 5 native-only ×48 = **1,680** exact key set), §4.5(`m_valid` = 20 native, bindings `m_pass_*_p/pa := P/PA_*_PASS`), §9.6(`m_pass_l` = 15 common), §11.3 phase 5 = **560**, §11.4 replay 1,680 — 모두 상호 정합(V6). V8에서 preflight(`common_ids`=15, native eligible 20/20, 배제 5개 = L 비적합 문서)와의 정합도 확인했다. 96/48 다중성 산술(4 arms × 3 seeds × 2 variants × 2 endpoints × 2 memory kinds = 24/target/arm; common은 4 arm에, native-only는 P/PA 2 arm에만 출현)도 성립한다.
- 다음 단계: ① exact mixed key set 유닛 테스트(96/48 다중성 포함, "missing native doc → M_NOT_EVALUABLE" 단언); ② 15→14 / native→common 치환 금지를 코드 전역에서 단언.

### Q4. M builder / M_NORM / endpoint / replay

- 판정: **conditional**
- 근거: 개별 정의는 충분하다 — builder(§9.2: contributors ≥10, V8에서 16/20 확인; `A=identity` P; eval/no_grad; seed-average), M_NORM(§9.3: 동일 adapter 공간에서 스칼라 rescale, `real_prefix_t` 공유), endpoint identity(§9.5: exact 1,680), replay(§11.4: 8단계 절차, numeric tolerance vs exact hash 분리), `control_digest`(§12.1: `M_POS_MEAN` + 모든 `M_NORM/t` 포함 — MF-7 closed). 남는 것은 **phase-7 donor diagnostic의 내용**이다: 600/arm-seed = 15×5×2×2×2라는 개수는 variant 축을 강제하므로 control = `M_POS_MEAN[:K_d]`/`M_NORM(t)[:K_d]` vs real = `A(h_t)[:K_d]`(K_d = min(len(real), len(donor)), donor는 crop 크기만 결정)라는 읽기만이 개수와 golden record 3(donor_id=0, memory_kind=real, variant=M_POS_MEAN)과 정합한다. 그러나 이 읽기를 문서가 명시하지 않는다(R2) — 서로 다른 두 구현이 같은 600개 레코드 수로 다른 내용을 만들 수 있다.
- 다음 단계: ① ERRATA로 phase-7 control 텐서 정의(R2); ② 유닛 테스트: ‖M_NORM(t)‖=‖real_prefix_t‖, zero/nonfinite norm abort, donor-crop K 선택; ③ replay tolerance(atol 1e-5/rtol 1e-4) 테스트를 exact-hash 테스트와 분리.

### Q5. F/L memory length scope

- 판정: **agree**
- 근거: §2.3이 `K_M=753`을 M-only로 고정하고 training/eval/generation의 753 요구를 금지한다. training forward는 real memory 전체 길이(§2.5.3, donor 없음), eval signal은 20 train/val 전체에 donor-crop K=min, generation은 20 val ×256(§2.5.7). 짧은 5개 val 문서는 F/L M target에서만 배제되고 P/PA native-20·20-doc signal eval·generation에는 모두 남는다 — short docs가 구조적으로 처리된다. zero-margin(K=754→14, §9.8)이 F/L cohort를 보호한다(V8에서 14 확인).
- 다음 단계: ① training/generation 코드 경로에 753 단언이 없음을 테스트; ② synthetic short-doc 세트로 donor-crop eval 테스트.

### Q6. P/PA

- 판정: **conditional**
- 근거: P/PA 술어는 20-native cohort 위에 완전 정의되어 있다(§4.5: `delta_pos_copy ≥ .05`, CI lower > 0, `delta_pos_full > 0`, CI lower > 0 × pos/norm). PA veto 의미론도 명시적이다(§5.3: PA 실패는 joint calibration을 거부할 뿐 native regime 자체의 반증이 아님; `PA_RETENTION`은 descriptive/nullable이고 gate 아님; §8.2 geometry caveat 512 vs 753, 직접 retention 비교 금지). 잔여: `m_valid` 피연산자(P/PA, copy **≥ .05**, v1.0 §4.5에서 그대로 계승)와 `m_pass_l` 피연산자(copy **> 0**, §9.6)의 임계값 비대칭이 어디에도 의도로 선언되지 않았다(R3). 결과가 아직 없으므로 지금의 ERRATA는 사후 조정이 아닌 사전등록 수선이다.
- 다음 단계: ① ERRATA R3(의도 명시; 값 변경은 새 사전등록으로만); ② PA veto 라우팅(F7/F8)과 `PA_RETENTION` nullable 처리 유닛 테스트; ③ manifest에 geometry caveat 유지.

### Q7. Statistics / tail

- 판정: **agree**
- 근거: §10.1 상수가 완전하다(n_boot 1000, seed 20261109, unit=document, seed-average-before-bootstrap, n_min 15). §10.2는 새 `runner/c5_pm_stats.py`를 요구하고 P0 helper 재사용을 금지하는데, 그 금지가 정당함을 코드에서 확인했다 — 기존 `bootstrap_paired`는 `seed=20261108` 기본값이고 `seeds_positive` 필드가 실제로는 문서 수를 세는 mislabel이다(runner L384–398). §10.4 signal tail은 absolute top3 + 결정론적 tie rule(|delta| desc, doc_id asc) + NA 전파를 정의한다. missing registered seed → 술어 NA, 2-of-available 금지(§3.5)도 total하다. V5에서 요청서·보고서의 모든 P0 수치를 원본 artifact에서 재현했다.
- 다음 단계: ① tie rule, missing-seed NA, `documents_positive` vs `seeds_positive` 네이밍 유닛 테스트; ② 새 stats 모듈이 legacy helper를 import하지 않음을 단언.

### Q8. D0/D1/cap

- 판정: **agree**
- 근거: §11.1 registered 12 units/1,200 updates/120 min/threads 6/GPU none/retry none; §11.2 D0 ≤4 configs·≤15 min·seed 20261111·`labels_computed:false`·`not_a_result:true`·h-length assert; §11.3 D1 4 arms × 1 update·≤20 min·8 phases(Phase 5 = 560, Phase 7 = 600/arm-seed — V6); §11.5 T_proj 공식 ≤96 min + 120-min hard abort; §11.6 prospective ceiling 1,204 updates/155 min(V7). 경계 설정(D0 mechanics-only, D1 no-labels/no-registered-seed, 별도 승인)이 §0.2/§16.3과 정합이다.
- 다음 단계: ① phase별 타이머 + "missing phase → no projection" 강제; ② 120-min hard abort 테스트; ③ D0/D1 산출물에 `not_a_result` 플래그 유지.

### Q9. Hash/golden

- 판정: **agree**
- 근거: V2–V4 — §12.1 frame spec과 §12.2 canonical JSON을 golden_vectors.json 상수만으로 재구현하여 세 golden digest를 **정확히** 재현했다(state `43ecb58e…`, empty `e3b0c442…`, replay `c43ea35c…`; donor-level 레코드의 donor_sort=0·variant 포함). `control_digest`(§12.1)가 MF-7을 닫았다. §11.4가 numeric tolerance와 exact hash를 분리하고 debug/final hash 직접 비교를 금지한다. `donor_sort −1/0..4`, seed enum, arm/variant/endpoint/memory_kind enum은 정의역 전체를 덮는다.
- 다음 단계: ① MF-9 잔여 보강 golden(M_NORM variant 및/또는 P/PA arm 레코드, donor tie-break 사례) 추가; ② permutation/duplicate/missing-key 테스트(§12.3); ③ 모든 manifest에 `control_digest` 존재 단언 + digest 없이 replay 불가 확인.

### Q10. 남은 Must-fix

- 판정: **conditional** (종합적으로는 닫혔고, 텍스트 수준 잔여 4+1)
- 근거: synthesis MF 목록과 v1.0.1 대응: MF-1→§9.1/§9.5/§11.3(mixed 1,680, exact key set, no silent subset, missing native → `M_NOT_EVALUABLE`) **closed**; MF-2→§2.5.6 **closed**; MF-3→§2.5.6("shuffled"=wrong-donor, 5-donor 평균, real도 동일 crop 평균) **closed**; MF-4→§4.0 **closed**; MF-5→§2.5 **closed**; MF-6→§11.4 **closed**; MF-7→§12.1 **closed**; MF-8→§2.3 **closed**; MF-9→§4.5 bindings + §7.1 3^6 + golden donor 레코드 **closed**(보강 golden은 부분 — R5a). v1.0.1이 새로 만들거나 노출한 문제는 아래 ranked list. 구조적·산술적 모순은 더 이상 없다(V6–V8).
- 다음 단계: ① R1–R4를 ERRATA로 pre-freeze 반영; ② 편집 후 §9 개수 재검증; ③ 이외 범위 확장 금지.

### Q11. 동결·구현 승인

- 판정: **conditional**
- 근거: R1–R4 적용 **후라면** 동결이 적절하다. 잔여 항목이 모두 텍스트 전용이고 새로운 과학적 선택이 아니기 때문이다(§16.1 NARROW 정의와 정확히 일치). 동결 후 구현 + unit tests + D0는 §16.3 배제 목록(D1/3-seed/B0-B/test 163/P1/T5Gemma2)을 지키며 승인 가능하다. 구현 전 필수 테스트(§13 외): golden 3-digest, F1–F11, 9 L pairs, fixtures 16–18, exact mixed 1,680 key-set(96/48, missing-native → `M_NOT_EVALUABLE`), `M_PASS_POS/NORM` 독립성 + `delta_memfree` 부재, missing-seed NA, tail tie rule, training/generation 무-753, donor 규칙(R4 반영 포함 train-doc donor pool), phase-7 의미론(R2 반영), `control_digest` 존재/재현, D0 `not_a_result` + h-length assert.
- 다음 단계: ① ERRATA R1–R4 발행 → freeze commit + content SHA-256; ② decision/stats/hash 모듈을 위 테스트와 함께 구현; ③ D0 실행(≤4 configs, ≤15 min, seed 20261111).

### Q12. B0-B / D1 / 3-seed

- 판정: **agree** (경계 충분; predicate 재진술은 아래)
- 근거: 모든 단계가 별도 승인으로 분리되어 자동 승인 경로가 없다(§0.2, §16.3). B0-B 입력(§14)은 v1.0.1 라벨 체계에서 모두 정의되고, tail gate는 signal tail만 사용하며 absolute share가 게이트 지표다(§10.4). M scope 라벨 `M_CONTROL_PREFIX753_COHORT15` 유지. 유일한 약한 의존은 `tail_driven` 입력 artifact의 명칭 미고정이다(R5b).
- 재진술된 B0-B predicate (v1.0.1 라벨 기준):

```text
B0-B eligible iff 모두 참:
  validity_status == VALID                  # §4: path flags clean, P/PA step100 valid
  control_status == M_CONTROL_PASS          # §5.4: m_evaluable ∧ P/PA valid ∧ m_valid=true ∧ m_pass_l=true
  signal_status == EXPLORATORY_L_SIGNAL     # §6.3: l_signal true, copy_only/full_only 아님
  m_valid == true                           # 명시적 재단언(M_CONTROL_PASS에 함축되지만 독립 기재)
  n_signal == 15                            # §6.1: ">=15"는 exactly 15
  tail_driven == false                      # §10.4 signal tail: leave_top3_mean > 0 ∧ top3_abs_share ≤ .50; true/NA는 block
  test_split_used == false ∧ P1 미사용 ∧ 등록 mode/semantics 준수
  artifact complete                          # manifest + final_checkpoint_hash + control_digest + final_replay_hash(1,680 primary pass; phase-7 별도 보고)
  B0-B 자체의 별도 사전등록 + 승인 존재       # 3-seed/EXPLORATORY_L_SIGNAL만으로 자동 승격 없음
```

- 다음 단계: ① B0-B를 별도 사전등록 문서로 유지; ② predicate을 순수 함수 + truth-table 테스트로 구현; ③ 코드 어디에도 자동 승격 없음 단언(§13.5).

### Q13. 최종 판정 및 freeze

- 판정: **NARROW** (최종)
- 근거: v1.0.1은 v1.0의 9개 Must-fix를 텍스트 수준에서 실제로 닫았고, mixed 1,680/560/600 산술과 세 golden digest를 내 독립 재현이 확인했다. 남은 것은 정의-명확성 ERRATA 4건(R1–R4) + 저위험 보강(R5)뿐이며, 이는 §16.1의 "must-fix only; no new scientific choices" 범위 안이다. STOP 사유(구조적 모순·산술 붕괴·측정 불가능성)는 없다. CONTINUE(지금 즉시 동결)는 R1–R2가 게이트 정의에 직접 균열을 넣을 수 있어(유닛 테스트가 잘못 고정될 위험) 선택하지 않았다.

---

## 2. Must-fix (ranked)

- **R1 (high, gate-relevant)** — §2.5.5 vs §9.5 정합: §2.5.5는 "copy tokens <5 → `copy_ce=None`; 문서를 copy endpoint에서 제외"(관용적 읽기), §9.5는 exact 1,680 key set에 "copy tokens ≥5", "no missing key"(엄격 — 단 하나의 <5-copy 목표가 있어도 `endpoint_ok=false` → `M_NOT_EVALUABLE`). ERRATA 권고 문안: "M primary endpoint에서 copyable 토큰 <5 목표는 key set 불완전으로 `endpoint_ok=false` → `M_NOT_EVALUABLE`이다. §2.5.5의 '제외' 문장은 signal/eval 경로(`n_signal`, §6.1)에만 적용된다." 값 변경 없음, 중의성 제거만.
- **R2 (high)** — phase-7 donor-level 레코드 의미론: `K_d = min(len(real), len(donor))`; control = 해당 레코드 variant를 `K_d`로 crop(`M_POS_MEAN[:K_d]` / `M_NORM(t)[:K_d]`); real = `A(h_t)[:K_d]`; donor는 crop 크기만 결정; 600/arm-seed = 15×5×2 variants×2 endpoints×2 memory kinds. (이 읽기만이 600 개수와 golden record 3과 정합한다 — 명시가 없을 뿐.)
- **R3 (medium)** — 임계값 비대칭 의도 명시: `m_valid` 피연산자 copy `≥ .05`(§4.5, v1.0 계승) vs `m_pass_l` 피연산자 copy `> 0`(§9.6). "의도적"(validity=습득 강도, calibration=방향 일치)임을 ERRATA로 선언. 결과 후 값 변경 금지 원칙 유지 — 지금은 사전등록 수선이므로 허용, 이후에는 새 사전등록.
- **R4 (medium)** — train-doc donor pool 명시: §2.5.6 "candidates = val20 IDs except rid"는 train20 문서에 val20 donor를 준다(cross-split; P0의 within-split 관례와 다름). ERRATA 문안: "train20 문서의 eval-signal donor는 val20에서 길이정렬로 선택한다(자기 제외는 val 문서에만 적용). donor 길이 원은 arm별로 F/L=EG2 cache h_len, P/PA=native token 길이(전부 512로 동일 → tie-break doc_id asc)."
- **R5 (low)** — 보강: (a) MF-9 잔여 golden(M_NORM/P·PA arm/donor tie-break 사례) 추가; (b) §10.2–10.4가 소비하는 per-doc signal-eval delta의 artifact 명칭 지정(§12.2 스키마는 variant=NA 표현이 없어 signal eval을 담지 못함); (c) §5.1 `cohort_ok` "≥15/20" → "정확히 15개 common ID 존재"(§9.8과 정렬); (d) §2.1 role 셀 "B0-A 재검증"은 역사 라벨 — 임의로 순화 가능; (e) §2.5.1 `source_max_length=512`가 native 경로에 적용되며 F/L 메모리 길이는 cache h_len임을 한 문장으로 명시; (f) compute dtype(float32/CPU)과 `threads=6`을 명시 — numeric replay(atol 1e-5)가 동일 환경을 가정함을 고정.

---

## 3. 최종 판정

```text
최종 판정: NARROW
v1.0.1 freeze: R1–R4 ERRATA 반영 후 동결 가능 (R5는 동결과 동시/직후 가능)
구현+unit tests: 동결 후 승인 — 위 Q11 필수 테스트 목록을 게이트로
D0: 동결 후 승인 — ≤4 configs, ≤15 min, seed 20261111, not_a_result, h-length assert
D1: 미승인 (별도 승인 필요; 4 arms × 1 update, ≤20 min)
3-seed: 미승인 (D1 완료 + 별도 승인 필요)
금지 범위: test 163(sealed), P1, T5Gemma2(D-108 STOP), B0-B/B1/B2/Stage C 자동 승격,
  결과 후 threshold/seed/donor/step/LR 변경, r3.x 이전 문서를 구현 근거로 사용
최대 compute: D0 ≤15 min(0 update); D1 ≤20 min(4 updates, 별도 승인 시);
  registered 12 units / 1,200 updates / wall ≤120 min / T_proj ≤96 min;
  prospective ceiling 1,204 updates / 155 min; retry/extension 없음
Must-fix (ranked): R1 copy-token 정합, R2 phase-7 의미론, R3 임계값 비대칭 의도,
  R4 train-doc donor pool, R5 보강(a–f)
v1.0.1 self-contained: ERRATA 후 예 — §0.1 단일 구현 권위 성립.
  기존 runner/tests는 참조 구현이며 텍스트에 종속; 계승 코드 재사용 시 runner commit 고정을
  manifest provenance로 권장(과학적 선택 아님).
잘못된 전제: (1) "untrained CE 12.7/13.2 > ln|V| 12.43"은 untrained 경로의 uniform-하한
  sanity일 뿐 trained arm 증거가 아님 — v1.0.1도 이 구분을 유지하고 있어 전제 오류 없음.
  (2) "54 tests"는 기존 eval/tests 함수 수와 일치하지만 P/M prereg 테스트는 0개 — 구현 시 모두 신규.
  (3) "phase 7 = 600/arm-seed"는 개수만으로는 내용을 고정하지 못한다(R2) — 개수를 근거로
  의미론을 단정하는 사용은 피해야 함.
```

Phase 6 실행, B0-B, D1, 3-seed는 이 리뷰로 승인되지 않는다. test 163은 봉인 상태로 유지된다.