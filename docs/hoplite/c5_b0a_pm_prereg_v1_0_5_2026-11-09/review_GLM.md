# C5 Phase 6 v1.0.5 — External Review Report (GLM 5.3 Flash, reasoning max)

- 작성일: 2026-11-09
- 모델: `z-ai/glm-5.3-flash` — **신규 독립 라운드.** v1.0.4 답변 및 타 모델 답변 미재사용 (`prompt_ds1017.txt`/`prompt_sol.txt` 미독; `prompt_glm.txt`는 본 요청서와 동일 텍스트임을 확인)
- 검토 기준 HEAD: `d38264fcb713bb43e718fb7b89a46ed2c403d6b6` (2026-11-09 18:16:18 +0900, "docs: add C5 P/M v1.0.5 review request")
  - 동기화: `git fetch origin` → `git pull --ff-only origin main` → **"Already up to date"**. 워크스페이스 브랜치 라벨 `hoplite/lipara-8b3d4682`가 동일 커밋. 요청서 표기 HEAD `50653b5` 이후 커밋이나 shallow clone(depth 1)이라 커밋별 diff 대조 불가 — 검토 대상은 현재 origin/main HEAD 내용 기준.
  - `docs/plan_c5_b0a_pm_prereg_v1_0_5.md` 1,721 lines, `plan_..._FREEZE.json` 미존재(템플릿만), `runner/c5_pm_stats.py` 미존재 → **§16.1 "No code before freeze" 준수 확인.**
- 제약 준수: 학습/평가 실행 없음, test 163 미개봉, P1 미사용, subagent/추가 LLM 없음, 수정 파일은 본 파일뿐, 결과 후 threshold/seed/donor/step/LR 변경 제안 없음.
- T5Gemma2: **D-108 STOP 유지.** Phase 6/B0-B/B1/B2/Stage C: **미승인 유지.**

---

## 0. 독립 재현 (본 라운드에서 직접 계산)

모델/데이터 실행 없이 파일 바이트와 직렬화 규칙만으로 해시를 재계산했다.

| 항목 | 재현값 | 기대값(§0.4/§12.3) | 결과 |
|---|---|---|---|
| preflight content SHA-256 | `3ee3f1ca68a8…69837af` | 동일 | ✓ |
| state golden | `43ecb58e197d…95d65712` | 동일 | ✓ (frame 규칙 그대로) |
| empty golden | `e3b0c44298fc…7852b855` | 동일 | ✓ |
| replay_base | `c43ea35c46c5…851667` | 동일 | ✓ **정렬 레코드 배열 전체의 canonical JSON 1개를 해시** |
| key_coverage_golden | `8277a713fd52…af7a20` | 동일 | ✓ 동일 배열 규칙 |
| control_manifest_golden | `6b50c226ecc4…ec1938` | 동일 | ✓ canonical name 정렬 후 frame concat |
| P0 train | mean +3.7617, CI [1.8917, 5.6050], positive 14/20, full +3.5027 | 요청서 §3 동일 | ✓ |
| P0 val | mean +5.2375, CI [2.5013, 8.0753], positive 18/20, full +5.2936 | 요청서 §3 동일 | ✓ |

- P0 `mode=p0_sanity_no_training`, `source_max_length=256`(기록된 한계), decision SENSITIVE_POSITIVE ×2 — descriptive 확인에 그친다.
- **replay 레코드 다이제스트 바이트 규칙**: 정렬된 레코드들을 **JSON 배열 하나로** canonical 직렬화(`sort_keys=true, separators=(',',':')`)한 바이트의 SHA-256만 golden과 일치. 레코드별 canonical JSON 연결은 불일치(base `d5afe0bc…`, coverage `43c8c635…`), newline join도 불일치(`fa7d1cdd…`/`33cedf4c…`). control frame은 파일 순서면 `531ba0ad…`로 불일치 → "canonical name 정렬" 규칙까지 확인. **§12.2 L1445-1446에 배열 규칙이 명시돼 있지 않다(→ MF-B).**
- 참고용: `golden_vectors.json` 파일 SHA-256 = `b6251a0768ab…294c64f`, `p1_usage.json` = `69af129a4f58…a3a2dc` (freeze 시 각 해시 재계산·기입 대상).
- §17.1 헬퍼 7심볼 존재 확인: `Adapter`(c5_mt5_layer_probe.py:52), `load_layer_cache`(:66), `make_labels`(:79, Tensor 반환), `LoRALinear`(c5_a1_lora.py:45), `repeated_4gram_rate`(c5_a2null_eval.py:80), `attach_decoder_lora_mt5`(c5_mt5_lora_b0.py:52), `native_memory`(:135). runner는 smoke/p0 전용이며 `train_arm`은 smoke 경로에서 호출되지 않음.

---

## Q1. 10 residual closure

- 판정: **conditional agree** — 9 closed / 1 partial.

| # | residual | 판정 | 근거 |
|---|---|---|---|
| 1 | freeze manifest | closed | §16.2 path+schema(L1640-1666), template 존재(status "template", preflight 해시 선기입 — 재현 ✓) |
| 2 | phase-7 baseline/delta numeric replay | closed | §9.6.1 `baseline_ce` phase-7 재계산 + "phase-5 stored CE 재사용 금지"; §11.4 L1313 numeric `atol=1e-5, rtol=1e-4`; L1315 `diagnostic_replay_ok` 분리; §12.2 hash 제외 |
| 3 | `registered_seeds_positive` | **partial** | §10.2 L1177-1178 정의 + P0 `seeds_positive`=문서 카운트 구분 ✓, §13.3 L1537 요구 ✓ — 그러나 §13.5 L1570 "no stale `registered_seeds_positive`"는 **신규 필드명을 금지하는 토큰 오류**(legacy `seeds_positive`를 금지해야 함) → MF-A |
| 4 | key-coverage golden | closed | golden `key_coverage_golden` 4-record + scope note; §12.3 L1493 "not the 600-record phase-7 domain"; 다이제스트 재현 ✓ |
| 5 | stored/hash record | closed | §9.6.1 `stored_record`={key, ce, baseline_ce, delta} nested / §12.2 `hash_record` flat 8-field |
| 6 | P1 contradiction/registry | closed | §1.5 contradiction rule(fail-closed) + missing/malformed→NA + unknown key(`note`) 허용; registry v2가 checkpoints/control/phase7 포함; postrun 커버 의무 |
| 7 | ordering `donor_sort` | closed | §12.2 internal-only(not serialized/hashed), null→-1; golden ordering note 정합; 재현으로 정렬 규칙 확인 |
| 8 | M_NORM truncation | closed | §9.6.1 "K_M-scaled vector truncated at K_d; no renormalization" + P/PA `K_d=K_M=512` 명시 |
| 9 | checkpoint base dir | closed | §12.1/§11.4 `reports/provenance/C5_b0a/checkpoints/{arm}/{seed}.pt` 절대 base 명시 |
| 10 | MARGINAL_SIGNAL_COHORT/line count/prefix | closed | §6.1 informational 명시(not dispatch input); `control/` 논리명 vs `control_manifest/` 파일시스템 §12.1 명시. C5_STATUS 1,690/1,691 행 수는 이번 라운드 파일셋 밖 — 검증 불가, 중요도 낮음 |

- 다음 단계: (1) MF-A 토큰 수정, (2) C5_STATUS 행 수 항목은 다음 라운드에서 파일 확인(본 라운드 범위 밖).

## Q2. Self-containedness

- 판정: **conditional agree** (MF-B 반영 시 self-contained).
- 근거: 단일 normative 선언(§0.1)·충돌 시 v1.0.5 우선·역사 문서 traceability only. 외부 참조는 §17.1 헬퍼 4파일(freeze commit+manifest로 바인딩, 심볼 존재 확인)과 해시로 바인딩된 데이터 아티팩트(preflight/golden/p1)뿐. 잔여 암묵 지식 3가지: (1) multi-record replay digest 바이트 규칙(배열) — golden이 pin하지만 plan 미명시(MF-B), (2) freeze_commit/manifest 커밋 순서 규칙(MF-D), (3) registry `{arm}/{seed}/{target_id}` 패턴의 postrun 전개 규칙(minor).
- 다음 단계: (1) MF-B 한 줄 추가, (2) MF-D 규칙 명시, (3) registry 전개 규칙 1문장.

## Q3. Freeze manifest

- 판정: **conditional agree**.
- 근거: path(`docs/plan_c5_b0a_pm_prereg_v1_0_5_FREEZE.json`)·schema가 §16.2와 template으로 확정 — D0 `assay_path_ok`(§4.0: preflight 해시+ID 일치+test_split_used=false+P1 SHA+두 flag false)를 평가 가능. `plan_sha256`은 "computed after freeze commit; the manifest is not part of the plan hash"(L1666) → 자기참조 없이 계산 가능 ✓. binding 충분: golden_sha256/preflight_sha256(재현 ✓)/p1_manifest_sha256/helper_commits 4파일/registered_seeds 3종 ✓.
- 남은 것: freeze manifest **자체** 무결성을 묶는 장치가 없음 — freeze_commit은 manifest 존재 이전 커밋을 가리키는 선행 커밋이므로, "FREEZE.json은 freeze commit 이후 커밋, 검증은 `plan_sha256` vs `git show {freeze_commit}:docs/plan_….md` 내용 해시" 규칙 명시(MF-D) + D0 보고서에 `freeze_manifest_sha256` 기록 권고.
- 다음 단계: (1) MF-D 규칙 1-2줄, (2) D0 출력 필드에 `freeze_manifest_sha256` 추가, (3) freeze 직전 `p1_usage.json`/`golden_vectors.json` 해시 재계산·기입.

## Q4. Phase-7 numeric replay

- 판정: **conditional agree**.
- 근거: `baseline_ce = CE(control_variant[:K_d], target, endpoint)`를 phase-7에서 재계산(§9.6.1), `K_d` bounds assert 포함, `ce`/`baseline_ce`/`delta` numeric `atol=1e-5, rtol=1e-4`(L1313), primary `replay_ok`와 `diagnostic_replay_ok` 분리(L1315) ✓. `hash_record`에서 `baseline_ce`/`delta` 제외는 audit 가능 — 두 값은 저장된 control 텐서+checkpoint+동일 토큰/endpoint로 재도출되며 numeric replay가 v1.0.4 MF-2의 "corrupted baseline/delta 통과" 실패 모드를 닫는다.
- 남은 것: (1) L1313 step-5 문구가 "key-coverage golden(4-record fixture) 확인"과 "600-record numeric replay"를 한 문장에 섞음 → 도메인 재혼동 위험(MF-C), (2) 다이제스트 배열 규칙 미명시(MF-B), (3) numeric 재현은 동일 환경(라이브러리/하드웨어) 전제 — D1/postrun 동일 환경 명시 권고.
- 다음 단계: (1) MF-C 문구 분리, (2) MF-B 규칙 명시, (3) numeric 재현 환경 고정 문구 1줄.

## Q5. Seeds / stats

- 판정: **conditional agree**.
- 근거: §10.2 L1177 `registered_seeds_positive` = registered seed mean > 0 카운트, L1178 P0 `seeds_positive`는 문서 카운트로 명시적 구분, "no P0 helper reuse (seed=20261108, mislabeled doc count)" ✓ — runner `bootstrap_paired`가 실제로 `seeds_positive=(arr>0).sum()`(문서 수) 반환·기본 seed 20261108 확인. 신규 `runner/c5_pm_stats.py`(bootstrap seed 20261109) 미생성 상태 ✓. §13.3 L1537 요구와 §13.5 L1570 금지가 같은 이름을 두고 충돌(MF-A).
- 다음 단계: (1) MF-A 토큰 수정, (2) 구현 시 stats 모듈 테스트에 "legacy 이름 부재" 단정 추가.

## Q6. Golden domains

- 판정: **agree** (배열 규칙 명시를 조건으로).
- 근거: 4 도메인이 목적·scope note로 분리됨 — `replay_base` 3-record `c43ea…`(재현 ✓), `key_coverage_golden` 4-record `8277a7…`(재현 ✓, "not the 600-record phase-7 domain"), `phase7_diagnostic` 600/arm-seed numeric-only atol/rtol, `control_manifest_golden` synthetic `[1,1]` `6b50c2…`(재현 ✓, "real [K_M,512] control_digest is postrun-only"). state/empty `43ecb5…`/`e3b0c4…` 재현 ✓.
- 남은 것: plan §12.3 L1490 라벨 `key_coverage` vs golden 키 `key_coverage_golden`(trivial), 다이제스트 바이트 규칙(MF-B).
- 다음 단계: (1) MF-B 반영, (2) L1490 라벨을 `key_coverage_golden`으로 통일(표기만).

## Q7. P1

- 판정: **agree**.
- 근거: contradiction rule fail-closed(§1.5: `p1_used=true` ∨ `test_split_read=true` ∨ 허용목록 밖 ID → false; missing/malformed → `assay_path_ok=NA`; unknown key `note` 허용) ✓. frozen `p1_usage.json` + 별도 `p1_usage.postrun.json` 구조 확인(파일 실재, postrun은 `not_run` 플레이스홀더) ✓. registry v2가 checkpoints/control/phase7/p1 파일까지 커버 ✓, postrun이 registry 존재 항목 커버 의무 명시 ✓. attestation≠proof를 plan과 파일 note 양쪽이 인정 ✓.
- 남은 것: registry 패턴 전개 규칙 암묵(minor), `checked_artifacts`에 기록해야 할 최소 필드(예: artifact path + 관측 ID 집합) 미정의(minor).
- 다음 단계: (1) postrun 항목 필드 최소 정의 1문장, (2) 패턴 전개 규칙 1문장.

## Q8. Checkpoint / naming

- 판정: **agree**.
- 근거: `reports/provenance/C5_b0a/checkpoints/{arm}/{seed}.pt` §12.1·§11.4 일치 ✓. 12-key map `"arm/seed"`→`sha256:...` ✓. 카운트 전부 검증: common target 96회(4 arms×3 seeds×2 variants×2 endpoints×2 memory kinds), native-only 48회, 15×96+5×48=**1,680** ✓; D1 phase-5 per-unit F/L **120**, P/PA **160**, 합산 **560** ✓; registered per-arm **F=360, L=360, P=480, PA=480** ✓; phase-7 **600**/arm-seed ✓.
- 다음 단계: (1) 구현 시 12-key 맵 키셋 단정 테스트 유지(§13.4).

## Q9. D0/D1/cap

- 판정: **agree**.
- 근거: D0 ≤4 configs(arm당 0-update 1 config)/≤15 min/seed 20261111/`labels_computed:false`/`not_a_result:true`/h-length assert(F/L 캐시, P/PA native 512) ✓. D1 4 arms×1 debug seed×1 update/8 phases(1-8 명시)/step0 선행 또는 복원/phase-5 **560**/phase-7 **600** ✓. `T_proj ≤96 min`, 120-min hard abort, cap "prospective max 1,204 updates / 155 min (not grant)" ✓(1,200+4, 120+20+15).
- 다음 단계: (1) D0 실행 시 8-phase 측정은 D1에서만 수행됨을 유지(D0 projection 금지 확인).

## Q10. 남은 Must-fix

- 판정: **conditional** — v1.0.5가 새로 만든 과학적 문제 없음. 전부 text/schema이며 threshold·seed·donor·step·LR 변경 아님.

| 순위 | 항목 | 내용 |
|---|---|---|
| MF-A (필수, 토큰 1개) | §13.5 L1570 | "no stale `registered_seeds_positive`" → **"no stale `seeds_positive`"**. 현행은 §13.3 L1537가 요구하는 필드를 금지하는 자기모순 |
| MF-B (필수, 1줄) | §12.2 L1445-1446 | multi-record replay digest 바이트 규칙 명시: **정렬 레코드 배열 1개의 canonical JSON에 대한 SHA-256**(재현: 배열 ✓ / 레코드별 연결 ✗). 미명시 시 문자적 구현이 §13.4 golden 테스트를 통과 불가 |
| MF-C (권장, 1줄) | §11.4 L1313 | step-5를 "key-coverage golden fixture 확인"과 "600-record `ce`/`baseline_ce`/`delta` numeric replay"로 분리 표기 |
| MF-D (권장, 1-2줄) | §16.2 | freeze_commit 커밋 순서 규칙 명시 + D0 보고서에 `freeze_manifest_sha256` 기록으로 manifest 무결성 체인 종결 |
| info | §12.3 L1490 / §1.5 / §11.4 | `key_coverage` 라벨 통일, registry 패턴 전개 규칙, postrun 항목 최소 필드, numeric 재현 동일 환경 전제 |

- 다음 단계: (1) freeze 전 plan에 MF-A/B 반영(사전 freeze이므로 ERRATA 불요; freeze 후라면 번호 ERRATA), (2) 반영 내용은 본 보고서가 허용 범위로 문서화 — 이 목록 밖 변경은 신규 리뷰 라운드 필요.

## Q11. 동결·구현 승인

- 판정: **conditional agree** — MF-A/B(필수) 반영 후 동결, MF-C/D 동일 패스 권장. 그 후 구현 + unit tests + D0 zero-update mechanics debug 승인.
- 근거: 잔여가 전부 text/schema이고 golden·preflight·P0·registry·P1이 독립 재현으로 검증됨(§0). 코드 미작성 상태 확인(§16.1 준수).
- 구현 전 필수 test: golden 5종 unit test(배열 규칙 포함), donor_sort/null 정렬·permutation 불변, stored/hash 스키마(8-field flat), `registered_seeds_positive` vs `seeds_positive` 명칭 단정, freeze manifest 스키마+`plan_sha256` 검증, P1 contradiction/allowlist/NA, M_NORM truncation no-renorm, 12-key checkpoint map+base path, phase-7 numeric replay harness(합성 레코드로 baseline 재계산·atol/rtol·diagnostic 분리), F1-F11+fixtures 16-18+9 L pairs+ANDn, zero-margin abort, 1,680 exact key set(96/48).
- 다음 단계: (1) MF-A/B/C/D 반영, (2) freeze commit+FREEZE.json, (3) 상기 테스트 후 D0.

## Q12. B0-B / D1 / 3-seed 경계

- 판정: **agree**.
- 근거: §14 B0-B predicate를 v1.0.5 label로 재진술: `validity_status==VALID ∧ control_status==M_CONTROL_PASS ∧ signal_status==EXPLORATORY_L_SIGNAL ∧ m_valid==true ∧ n_signal>=15(상한 15와 동치) ∧ tail_driven==false ∧ leakage/mode/metric pass ∧ artifact complete ∧ 별도 prereg/approval` — 모든 라벨이 §4.1/§5.4/§6.2/§6.3에 실재. tail gate는 signal tail `top3_abs_share`(+`leave_top3_mean` 규칙, tie rule) ✓, `M_POS_MEAN`/`M_NORM` tail은 descriptive ✓. D1/3-seed/B0-B/B1/B2/Stage C 모두 별도 승인·자동 진행 금지 명시 ✓.
- 다음 단계: (1) B0-B는 별도 prereg 문서로만 진행, (2) `PA_RETENTION`/`full_k_secondary`/P0를 B0-B 증거에서 배제 유지.

## Q13. 최종 판정 및 freeze

- 판정: **CONTINUE (조건부)** — 아래 승인 범위 참조.
- 근거: v1.0.4의 10 잔여 중 9 closed/1 partial(MF-A), golden 5종+preflight+P0 독립 재현, phase-7 numeric replay·P1 fail-closed·카운트 체계 검증. 남은 must-fix는 전부 text/schema.

```text
최종 판정: CONTINUE (조건부)
v1.0.5 freeze: 승인 — MF-A/B 필수, MF-C/D 권장 반영 후 (text-only; 허용 범위는 본 보고서 Q10)
구현+unit tests: 승인 (freeze 후; Q11 필수 test 목록 준수)
D0: 승인 (0-update mechanics debug; seed 20261111; ≤4 configs; ≤15 min; labels_computed:false; not_a_result:true)
D1: 미승인 (별도 승인 필요)
3-seed: 미승인 (별도 승인 필요)
금지 범위: test 163 봉인, P1 미사용, T5Gemma2 D-108 STOP, B0-B/B1/B2/Stage C 자동 진행 금지,
  결과 후 threshold/seed/donor/step/LR 변경 금지, 15→14/native→common 치환 금지,
  primary donor-crop 금지, freeze 전 코드 작성 금지
최대 compute: 구현+unit tests CPU-only; D0 ≤15 min; registered run 미부여
  (T_proj ≤96 min·120 min hard abort·prospective 1,204 updates/155 min은 별도 승인 시에만 적용)
Must-fix (ranked): MF-A §13.5:1570 토큰; MF-B §12.2:1445 배열 규칙; MF-C §11.4:1313 문구 분리; MF-D freeze_commit 규칙+D0에 freeze_manifest_sha256
v1.0.5 self-contained: 예 (MF-B 반영 시); 암묵 잔여 = registry 패턴 전개, numeric 재현 동일 환경 전제
잘못된 전제: 없음 — preflight 해시·golden 5종·P0 수치 독립 재현 확인. 단, P1 비사용은 attestation(문서 자체가 인정),
  P0는 미학습·source_max_length=256의 descriptive 결과로 훈련 P/PA/M의 근거 아님(요청서도 인정)
```

---

## 검증 방법 명시

- 본 보고서의 해시/수치는 워크스페이스 파일 바이트에 대한 순수 계산(SHA-256/frame 직렬화/canonical JSON)이다. 모델 로드·학습·평가·test 163·P1 데이터 접근 없음.
- subagent나 다른 LLM을 사용하지 않았고, 다른 모델의 v1.0.5 답변 파일을 읽거나 재사용하지 않았다.
- repository 수정은 본 파일(`review_GLM.md`) 하나뿐이다.