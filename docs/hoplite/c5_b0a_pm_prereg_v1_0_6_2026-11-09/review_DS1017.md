# C5 Phase 6 v1.0.6 — External Review (DeepSeek V4.1 Flash 1017, high)

- 검토일: 2026-11-09
- 검토 모델: Hoplite `deepseek-v4.1-flash-1017` (OpenRouter), reasoning high
- 검토 기준: `origin/main` HEAD `e619885` (`db68565`의 자손; `db68565` = v1.0.6 repair commit)
- 동기화: `git fetch origin` → `git pull --ff-only origin main` → `Already up to date`
- test 163: **미사용**, P1: **미사용**, 학습/평가: **미실행**
- T5Gemma2: **D-108 STOP 유지**, Phase 6/B0-B/B1/B2/Stage C: **미승인**

## 0. 독립 재현 결과

직접 계산한 값(구현 코드 미사용, 스펙의 frame/JSON 규칙만 사용):

| 대상 | 기대값 | 재계산 | 일치 |
|---|---|---|---|
| state_full | `43ecb58e…d65712` | 동일 | ✅ |
| state_empty | `e3b0c442…b855` | 동일 | ✅ |
| replay_base (array) | `c43ea35c…51667` | 동일 | ✅ |
| key_coverage (array) | `8277a713…f7a20` | 동일 | ✅ |
| control (sorted name) | `6b50c226…c1938` | 동일 | ✅ |
| preflight content | `3ee3f1ca…837af` | 동일 | ✅ |

- control digest는 canonical name 정렬(`M_NORM` < `M_POS_MEAN`)에서만 재현된다.
- replay/key-coverage digest는 **정렬된 record array의 canonical JSON 1개**에서만 재현된다(record별 연결 아님).
- P0: train +3.7617264 [1.8916853, 5.6049574], val +5.2374585 [2.5013211, 8.0752724] — 요청서 수치와 일치.

## 1. Q1~Q13

### Q1. 8 residual closure

- 판정: **conditional** (7 closed / 1 partial)
- 근거:
  1. §13.5 `seeds_positive` — **closed**. §13.3은 `registered_seeds_positive`를 요구하고, §13.5는 “no legacy `seeds_positive` in registered stats; no stale registered counts”로 P0 helper와 등록 필드를 분리한다. §10.2도 동일하게 구분한다.
  2. array digest — **closed**. §12.2 “SHA256 over the canonical JSON of the sorted record array (one array); record-by-record concatenation is forbidden”, §13.4 negative test. `c43ea…`/`8277a7…` 재현.
  3. phase-7 equal-dim — **closed**. §9.6.1에 4-way `shape[0] == K_d` assert, `baseline_ce`/`delta` phase-7 재계산, `diagnostic_replay_ok` 분리(§11.4 step 7).
  4. control golden order — **closed**. §12.3 “sorted ascending by canonical name (`M_NORM` before `M_POS_MEAN`)”, golden 파일도 정렬됨. `6b50…` 재현.
  5. bootstrap RNG/percentile — **closed**. §10.3 `default_rng(20261109)` PCG64, fresh generator, `percentile(..., method="linear")`, 1,000.
  6. freeze handoff — **partial**. 순서(§16.2)와 template은 고쳤으나, **§16.2의 manifest 경로/`plan_path`가 여전히 v1.0.5**다(아래 MF-1).
  7. postrun/P1 coverage — **closed**. §1.5 glob expansion, actual file listing, self-list, frozen/postrun 분리, contradiction rule, malformed→NA.
  8. P0/schema/misc — **closed**. §0.4 hash, §16.2 `schema_version:1`, §10.4 P0 256 한계, §6.1 MARGINAL informational, §13.4 array/control tests.
- 다음 단계: (1) MF-1 text 수정. (2) 수정 후 §16.2만 재확인. (3) 나머지 7개는 재론하지 말 것.

### Q2. Self-containedness

- 판정: **conditional**
- 근거: §0.1은 단일 구현 계약을 선언하고, §2.5/§9/§12가 측정·builder·hash를 닫는다. 남는 외부 의존은 (a) §17.1 helper 6종의 **동작 계약**(파일 경로만 고정, 시그니처 본문은 인용 파일에 위임), (b) 데이터 경로 4종(§2.6), (c) `reports/provenance/C5_clean/splits.json` 스키마. 이는 암묵 과학 지식이 아니라 고정 입력이므로 허용 가능하다. 다만 §16.2 경로 오류와 §11.5 T_proj 입력 모호성은 “문서만 읽고 구현”을 깨뜨린다.
- 다음 단계: (1) MF-1/MF-2 수정. (2) §17.1 helper의 최소 시그니처를 부록에 명시(선택).

### Q3. Hash

- 판정: **agree**
- 근거: array digest, flat 8-field `hash_record`(arm, ce, doc_id, donor_id, endpoint, memory_kind, seed, variant), `donor_sort` null=-1 내부 전용, base `c43ea…`, key coverage `8277a7…`, control `6b50…`가 모두 정합적이며 5종 전부 독립 재현됐다. 정렬 키 `(doc_id, arm, seed, variant, endpoint, memory_kind, donor_sort)`와 golden record 순서도 일치한다.
- 다음 단계: (1) per-record concatenation negative test를 §13.4에 유지. (2) golden은 절대 구현으로 재생성하지 말 것.

### Q4. Phase-7

- 판정: **agree**
- 근거: §9.6.1의 equal-dim assert, `K_d=min(...)`, `M_NORM(t)[:K_d]` 무재정규화, `baseline_ce` phase-7 재계산, `delta=baseline_ce-ce`, 600/arm-seed(15×5×2×2×2)가 실행 가능하다. §11.4가 primary `replay_ok`와 `diagnostic_replay_ok`를 분리해 phase-7 실패가 primary를 오염시키지 않는다.
- 다음 단계: (1) §11.4 step 5의 “verify key-coverage golden” 문구를 “4-record fixture 별도 검증 + phase-7은 numeric-only”로 명확화(MF-3). (2) F/L donor `h_len<753` 케이스 회귀 1개.

### Q5. Seeds/stats

- 판정: **agree**
- 근거: §13.5가 required `registered_seeds_positive`를 보존하고 legacy `seeds_positive`만 금지한다. §10.2가 P0 helper의 document count와 등록 필드를 명시적으로 구분한다. §10.3 RNG/percentile이 재현 가능하며, §3.5/§4.5의 2/3 registered seed 규칙과 missing-seed NA가 일관적이다.
- 다음 단계: (1) `runner/c5_pm_stats.py`가 legacy `runner.c5_mt5_lora_b0.bootstrap_paired`(seed 20261108, `seeds_positive`)를 import하지 않음을 assert하는 test 추가(MF-5).

### Q6. Control golden

- 판정: **agree**
- 근거: `M_NORM` before `M_POS_MEAN` 정렬, synthetic `[1,1]` fixture, real `[K_M,512]` postrun-only가 §12.1/§12.3에서 일관적이다. `6b50…`는 정렬 순서에서만 재현된다.
- 다음 단계: (1) golden 파일의 `ordering` 노트 유지. (2) real `control_digest`는 postrun artifact로만 기록.

### Q7. Freeze

- 판정: **disagree** (text-only 수정 필요)
- 근거: §16.2가 freeze manifest를 `docs/plan_c5_b0a_pm_prereg_v1_0_5_FREEZE.json`, `plan_path: docs/plan_c5_b0a_pm_prereg_v1_0_5.md`로 적는다. template은 v1.0.6이다. 이대로면 manifest가 **v1.0.5 plan에 결속**되어 “implementation references only freeze commit + manifest”가 깨진다. 또한 `freeze_commit`이 plan commit인지 manifest commit인지 정의가 없다.
- 다음 단계: (1) §16.2 경로/`plan_path`를 v1.0.6으로 수정(MF-1). (2) `freeze_commit` = final plan commit임을 1줄 명시(MF-4). (3) `plan_sha256`은 step 1 이후 계산, manifest는 plan hash에 미포함 유지.

### Q8. P1/postrun

- 판정: **agree**
- 근거: §1.5가 frozen `p1_usage.json`과 `p1_usage.postrun.json`을 분리하고, postrun이 registry glob을 실제 파일로 확장·self-list하며, contradiction rule(any `p1_used=true`/`test_split_read=true`/allowlist 밖 ID → false)과 malformed→NA가 fail-closed다. `p1_usage.json`은 현재 `p1_used:false`, `test_split_read:false`, `checked_artifacts:[]`로 유효하다.
- 다음 단계: (1) postrun 실행 시 registry v2 glob 전개 결과를 실제 파일 목록으로 기록. (2) `assay_path_ok`는 frozen hash만 사용.

### Q9. D0/D1/cap

- 판정: **conditional**
- 근거: D0 4 configs/≤15 min/seed 20261111/`labels_computed:false`/`not_a_result:true`, D1 4 arms×1 debug seed×1 update/≤20 min, 8 phases, 560(120+120+160+160), 600/arm-seed, T_proj ≤96, 120-min hard abort, cap 1,204 updates/155 min이 서로 정합적이다. 다만 §11.5의 `t_primary_replay_arm` 설명이 “arm-seed 120/160”과 “360/480 per arm across 3 seeds”를 함께 적어 **외부 ×3과 삼중 계산 위험**이 있다.
- 다음 단계: (1) `t_primary_replay_arm` 입력은 arm-seed 120/160이고 360/480은 ×3 이후 per-arm 총계임을 명시(MF-2). (2) D0는 D1/3-seed와 별도 승인 유지.

### Q10. 남은 Must-fix

- 판정: **disagree** (신규 문제 1건 + 모호성 3건)
- 근거: ranked list는 아래 “Must-fix” 참조. 특히 §16.2 freeze 경로(v1.0.5)는 v1.0.6이 새로 만든 실질 결함이다. array digest/golden 5종, phase-7 equal-dim, control order는 새 문제 없음.
- 다음 단계: (1) MF-1~MF-4 text-only 수정. (2) 수정 diff만 재검토.

### Q11. 동결·구현 승인

- 판정: **conditional**
- 근거: 과학적 선택(threshold/seed/donor/step/LR/cohort)은 동결 가능한 수준으로 닫혔다. 그러나 MF-1이 freeze authority chain을 깨므로 “as-is freeze”는 불가하다. MF-1~MF-4는 text-only이며 새 과학 선택이 아니다.
- 구현 전 필수 test: (a) golden 5종 + per-record concat negative, (b) phase-7 equal-dim/`baseline_ce` numeric replay, (c) `registered_seeds_positive` vs P0 `seeds_positive` 분리, (d) bootstrap RNG/percentile 재현, (e) 1,680 exact key set(96/48), (f) P1 contradiction/malformed NA, (g) legacy `bootstrap_paired` 미사용 assert.
- 다음 단계: (1) MF-1~MF-4 수정 후 freeze. (2) 구현+unit tests. (3) D0 zero-update mechanics debug.

### Q12. B0-B / D1 / 3-seed

- 판정: **agree** (경계 충분, 승인은 아님)
- 근거: §14 predicate는 `validity_status==VALID AND control_status==M_CONTROL_PASS AND signal_status==EXPLORATORY_L_SIGNAL AND m_valid==true AND n_signal>=15 AND tail_driven==false AND leakage/mode/metric pass AND artifact complete AND separate prereg/approval`이며, `n_signal>=15`는 실질 15, tail true/NA는 차단, `EXPLORATORY_L_SIGNAL` 단독은 승인 아님을 명시한다. D1/3-seed/B0-B/B1/B2/Stage C는 각각 별도 승인으로 분리되어 있다.
- 다음 단계: (1) B0-B는 별도 prereg/approval 없이 열지 말 것. (2) `full_k_secondary`/P0/`PA_RETENTION`을 evidence로 쓰지 말 것.

### Q13. 최종 판정

- 판정: **NARROW**
- 근거: 8 residual 중 7 closed, freeze handoff만 partial. MF-1은 text-only이지만 authority chain에 직결되므로 동결 전 필수다. 과학적 재량 변경은 요구하지 않는다.
- 다음 단계: (1) MF-1~MF-4 수정. (2) freeze manifest 생성. (3) 구현+unit tests+D0.

## 2. Must-fix (ranked)

1. **MF-1 (blocking, text-only)** — §16.2 freeze manifest 경로/`plan_path`가 v1.0.5. v1.0.6으로 수정. template과 일치시킬 것.
2. **MF-2 (high, text-only)** — §11.5 `t_primary_replay_arm` 입력 정의 모호(120/160 arm-seed vs 360/480 per-arm). 외부 ×3과 삼중 계산 방지.
3. **MF-3 (medium, text-only)** — §11.4 step 5 “verify key-coverage golden”이 600-record phase-7 domain으로 오독될 수 있음. 4-record fixture 별도 검증 + phase-7 numeric-only로 명확화.
4. **MF-4 (medium, text-only)** — `freeze_commit` 의미(plan commit vs manifest commit) 1줄 정의.
5. **MF-5 (low, test-only)** — frozen helper `runner/c5_mt5_lora_b0.py`에 legacy `bootstrap_paired`(seed 20261108, `seeds_positive`)가 남아 있음. `runner/c5_pm_stats.py`가 이를 import하지 않음을 assert.

## 3. 최종 블록

```text
최종 판정: NARROW
v1.0.6 freeze: MF-1~MF-4 text-only 수정 후 승인 (as-is 불가)
구현+unit tests: freeze 후 승인 (Q11 필수 test 포함)
D0: 구현+unit tests 통과 후 승인 (≤4 configs, ≤15 min, seed 20261111)
D1: 미승인 (별도 승인)
3-seed: 미승인 (D1 이후 별도)
금지 범위: test 163, P1, T5Gemma2(D-108 STOP), Phase 6/B0-B/B1/B2/Stage C, post-result threshold/seed/donor/step/LR 변경
최대 compute: D0 ≤15 min; D1 ≤20 min; registered prospective 1,204 updates / 155 min (grant 아님)
Must-fix (ranked): MF-1 §16.2 v1.0.5 경로; MF-2 T_proj 입력; MF-3 key-coverage 문구; MF-4 freeze_commit; MF-5 legacy bootstrap assert
v1.0.6 self-contained: conditional (MF-1/MF-2 해소 후)
잘못된 전제: “freeze handoff가 완전히 닫혔다”는 요청서 §2.6 진술은 §16.2 경로 때문에 과장이다.
```

## 4. 제한

- 이 보고서는 승인이 아니다.
- 학습/평가 미실행, test 163 미열람, P1 미사용.
- golden/preflight/P0는 재현된 상수이며 결과가 아니다.