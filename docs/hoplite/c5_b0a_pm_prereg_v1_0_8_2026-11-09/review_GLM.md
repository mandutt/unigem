# C5 Phase 6 v1.0.8 — External Review, same-thread continuation (GLM 5.3 Flash, reasoning max)

- 작성일: 2026-11-09
- 모델: `z-ai/glm-5.3-flash` (reasoning max), v1.0.7 라운드와 동일 스레드 연속, 타 모델 답변 미재사용
- **검토 기준 HEAD SHA: `38a2a81`** (full: `38a2a813978bd9688992fb5425b468fd47f6ca69`, "docs: add Phase 6 v1.0.8 repair")
- 동기화: `git fetch origin` + `git pull --ff-only origin main` → HEAD `d4e9dfa` ("docs: add C5 P/M v1.0.8 same-thread review request"). `38a2a81..d4e9dfa` diff는 리뷰 인프라 7개 파일(dispatch_fup/fup prompts/threads/watch/요청서)뿐 — 검토 대상 4개 문서 바이트는 `38a2a81`과 동일.
- **§16.2 verbatim 인용 (plan line 1688):**
  `manifest_commit` is always `null` inside `_FREEZE.json`; a file cannot contain the SHA of the commit that adds it.
  (요청된 구절 그대로: manifest_commit is always null inside _FREEZE.json)
- 범위 준수: v1.0.7에서 closed로 확인된 항목 재검토 없음(§13 golden/산수/코호트/임계값 불변 — diff 확인). 학습/평가 실행 없음, test 163 미개봉, P1 미사용, 서브에이전트 없음. 유일한 실행은 fixture 재해시와 저장된 `per_doc` 값의 순수 산술 재계산.
- 상태: v1.0.8 review. **Phase 6/B0-B/B1/B2/Stage C 실행 미승인. test 163 sealed. P1 미사용. T5Gemma2 D-108 STOP 유지.**

---

## 0. 독립 검증 결과 (hash/산술 전용)

| 항목 | 재계산 | 결과 |
|---|---|---|
| v1_0_8 golden 4 digests (state `43ecb58e…`, replay_base `c43ea35c…`, key_coverage `8277a713…`, control `6b50c226…`) | v1_0_7 스크립트 재실행(`spec` 문자열만 다름을 diff로 확인) | **전부 일치** |
| preflight SHA `3ee3f1ca…69837af` | file bytes SHA256 | **일치** |
| P0 tail val20 signed top3 | 저장 `per_doc.delta_shuffled_copy` 20개, `\|delta\|` desc + doc_id asc tie rule | **0.4862** (§10.4 `.4862` 일치) |
| P0 tail val20 absolute top3 | 동일 | **0.43355** (§10.4 `.43355` 일치) |
| P0 tail 15-common absolute top3 | common_ids 15개로 제한 | **0.45478 → .455** (§10.4 `.455` 일치) |
| plan diff v1.0.7→v1.0.8 | 102 diff lines 전수 검토 | 변경 = 7개 폐쇄 + 버전/경로/traceability 표기뿐, 과학적 내용 불변 |

P0 tail 세 수치는 "derived, not stored" 주장 그대로 저장 artifact에서 **실제로 재도출됨** — top3 ids: REPORT-news_r-01058-00001, REPORT-news_r-04161-00002, REPORT-news_r-01518-00001 (val20/common 공통). train20은 signed .4222/absolute .34096(참고, 게이트 아님).

---

## 1. Q1–Q9

### Q1. 7 residual closure

- 판정: **agree — 7/7 closed (1개는 test-scope 보강 권고)**
- 근거:
  1. `manifest_commit` self-reference — **closed**. §16.2 schema 필드가 `"manifest_commit": null`(line 1673), 규범 문구 "…is always `null` inside `_FREEZE.json`; a file cannot contain the SHA of the commit that adds it"(line 1688), 외부 파일 `reports/provenance/C5_b0a/freeze_manifest_commit.txt`(line 1689), D0이 `freeze_manifest_sha256` + `manifest_commit` 병기(1690), freeze 순서 5단계(1691). template도 동일 규칙 기술. 자기참조 소거 확인.
  2. legacy `bootstrap_paired` reachability — **closed**. 신규 §17.3: entrypoint `runner/c5_pm_phase6.py` 유일, `c5_pm_stats.bootstrap_paired_v2` 사용, `evaluate_arm` 재사용 시 bootstrap call 교체 의무, `bootstrap_paired(` 소스/콜그래프 부재 단언, monkeypatch-only 금지. legacy 심볼은 `runner/c5_mt5_lora_b0.py:384`(seed 20261108)에 잔존 — helper 유지 신규 차단 구조로 의도대로.
  3. paired `L>F` — **closed**. §3.5 신규 블록: cohort=15 common, variant/endpoint/memory_kind/seed 동일 정렬, per-doc `delta_L(doc)-delta_F(doc)`, seed-average 후 bootstrap, missing pair→NA, no 15→14.
  4. template `note` — **closed**. §16.2 "optional `note` string is allowed in the frozen manifest"(line 1697). template의 `status:"template"`→`"frozen"` 치환 규칙은 §16.2 schema와 note 자체에 명시.
  5. cap 120/155 — **closed**. §11.6 "registered run wall = 120 min (Phase 6 only). 155 min is the aggregate envelope D0 15 + D1 20 + registered 120; it is not a single-run cap."
  6. P0 tail provenance — **closed**. §10.4 "P0 tail values `.4862/.43355/.455` are derived from `p0_native_sanity.json`; they are not stored fields and are descriptive only." — §0에서 재도출로 **사실 확인까지 완료**.
  7. §4.6 — **closed**. bullet이 "`p_step NA + p_valid=NA` → `NOT_ASSESSABLE`"로 수정 — F9 및 §4.4/§4.7 도달 가능 상태와 정합. 다른 unreachable 표기 없음(diff 전수 확인).
- 다음 단계: 동결 진행(§2.2 test-scope 권고 반영 권장).

### Q2. Freeze chain

- 판정: **agree**
- 근거: 5단계 체인이 순환 없이 기계적으로 실행 가능 — (1) final plan commit(freeze_commit = 최종 plan commit, normative bytes + helper sources; plan SHA는 단계 1 이후 산출, manifest 미포함 — v1.0.7 정의 유지) → (2) `_FREEZE.json` populate(`manifest_commit:null`, plan_sha256/freeze_commit/p1_manifest_sha256/golden_sha256/preflight_sha256/helper_commits/registered_seeds; `note` 허용) → (3) manifest commit → (4) 외부 `freeze_manifest_commit.txt`에 실제 SHA 기록 → (5) D0 report가 `freeze_manifest_sha256` + `manifest_commit` 병기. 파일 내 null + 외부 기록 구조이므로 자기참조 없음. template가 v1_0_8 경로·null 규칙과 일치(`preflight_sha256` 선기입값 재해시 일치).
- 다음 단계: (1) 동결 시 단계 4의 txt 파일 커밋 시점을 postrun 전 임의 시점으로 명시(현재는 "after the manifest commit"만 규정 — 불문류 없음, 기록성만 확인), (2) 필요 시 registry expected 목록에 `freeze_manifest_commit.txt` 추가(cosmetic; provenance dir 내부라 §17.2 위반 아님).

### Q3. Legacy bootstrap 차단

- 판정: **agree (closed) — test scope 보강 권고**
- 근거: §17.3이 (a) 유일 entrypoint, (b) `bootstrap_paired_v2` 사용, (c) `evaluate_arm` 재사용 시 교체 의무, (d) `bootstrap_paired(` 소스/콜그래프 부재 단언, (e) monkeypatch-only workaround 금지를 모두 규정. 패턴 `bootstrap_paired(`는 `bootstrap_paired_v2(`와 부분일치하지 않으므로(`_v2`가 `(` 앞에 개입) 오탐 없음. 규범 요구 자체는 완결.
- 남는 것: "Phase 6 path"의 검사 범위 해석. entrypoint 파일만 grep하면 **미수정 `evaluate_arm`를 import하는 경로**(모듈 본문이 여전히 legacy 호출)를 소스 수준에서 놓칠 수 있음 — 다만 (c)가 교체를 의무화하므로 그런 구현은 규범 위반이며, 단언을 "entrypoint에서 import-도달 가능한 전이적 소스"로 정의하거나 런타임 트립와이어 테스트(legacy 심볼을 raise로 패치한 뒤 phase-6 경로가 정상 동작함을 확인 — 규정의 monkeypatch 금지는 '우회 준수' 금지이지 테스트 금지가 아님)를 추가하면 기계적 보장이 됨. text blocker 아님.
- 다음 단계: (1) §13 테스트 구현 시 전이적 소스 단언 또는 트립와이어 테스트 채택, (2) 단언 대상 파일 목록을 `c5_pm_phase6.py` + 재사용 함수 소유 모듈로 명시.

### Q4. Paired L>F

- 판정: **agree**
- 근거: 15 common은 preflight `common_ids`로 고정. F/L은 동일 EG2 layer19 cache `h_len`을 쓰므로 donor 목록이 동일(§2.5.6 donor per arm — F/L은 같은 arm 메모리 공간·같은 길이 원천) → per-doc 쌍이 실제로 대응. `delta`는 copy/full 각각 정의(§3.5)되어 L_COPY_SIGNAL/L_FULL_SIGNAL 두 접속사 모두 계산 가능. seed-average 후 bootstrap(§10.3 seed_average_before_bootstrap=true) 일관. copy CE <5 tokens로 한 arm에서만 탈락한 문서는 missing pair→NA — n_signal(양팔 유효 엔드포인트 문서 수, §6.1)과 모순 없음. 실행 가능.
- 다음 단계: 구현 시 contrast 산출을 15×3(seed)×2(copy/full) 키 구조로 고정하고 missing-pair NA 경로 단위 테스트 추가.

### Q5. Cap/labels

- 판정: **agree**
- 근거: §11.6 신규 2줄이 120(등록 단일 실행 wall, Phase 6 전용)과 155(D0 15 + D1 20 + 등록 120의 총 envelope, 단일 실행 cap 아님)을 명시 분리. §11.1(120 min wall)/§11.2(≤15)/§11.3(≤20)/§11.5(120-min hard abort, T_proj ≤96)와 산술·용어 일치. prospective "1,204 updates / 155 min (not grant)" 문구와도 정합.

### Q6. P0 tail

- 판정: **agree — 검증 강화됨**
- 근거: §10.4 문구 추가 + §0 재도출(val20 signed .4862, absolute .43355, 15-common .45478≈.455 — 세 값 전부 저장 `per_doc`에서 tie rule `\|delta\|` desc + doc_id asc로 재현). descriptive-only 명시, 게이트(`tail_driven`)는 signal tail 전용(§10.4) — P0 수치가 어떤 판정 입력도 아님을 재확인. 참고: val20 leave_top3_mean=+3.1659>0이므로 P0 데이터는 tail_driven=false 방향(descriptive).

### Q7. §4.6

- 판정: **agree**
- 근거: 수정 bullet "`p_step NA + p_valid=NA` → `NOT_ASSESSABLE`"는 §4.5(P_VALID: p_step NA→NA)와 F9("p_step NA + p_valid NA")와 정확히 일치하며 도달 가능 상태만 기술. §4.4 체인·§4.7 불변식·F3("pa_path NA + P invalid → P_STEP100_NOT_VALID")는 v1.0.7에서 검증한 대로 불변(diff 확인). 잔여 unreachable 표기 없음.

### Q8. Self-containedness

- 판정: **agree**
- 근거: v1.0.7 대비 추가된 것은 §17.3 entrypoint call graph — v1.0.7에서 "정의 필요"로 남았던 유일한 미정의 구조. 이제 구현자는 v1.0.8 한 문서로 (a) 엔트리포인트/모듈 구조(§17.3), (b) 측정 경로(§2.5), (c) 판정 체인(§3–7), (d) 통계(§10 — `bootstrap_paired_v2` 계약은 §10.1–10.3 파라미터로 완전), (e) 해시/golden(§12), (f) 테스트(§13), (g) freeze 절차(§16.2)를 전부 얻음. 외부 참조는 §17.1 helper 6종(freeze commit 고정)+열거된 artifact 경로뿐. `runner/c5_pm_stats.py`·`runner/c5_pm_phase6.py` 미존재 확인 — §16.1 "No code before freeze" 준수. 암묵 지식 요구 없음.

### Q9. 최종 판정

- 판정: **CONTINUE**
- 근거: v1.0.7 합성의 7개 잔여(MF-1..7) 전부 폐쇄; 그중 2개(legacy test scope, freeze txt 커밋 시점)는 text blocker가 아닌 구현-시점 보강. v1.0.7 라운드에서 이미 검증된 golden/preflight/산수/코호트/임계값은 diff상 불변. 새로운 과학적 선택 없음(102 diff lines 전수 = 7 폐쇄 + 표기). STOP/NARROW 사유 없음.

---

## 2. Must-fix (ranked)

**동결 차단 must-fix 없음.** 구현/테스트 시점 권고(순위):

1. **(test hardening, low)** §17.3 소스 단언의 검사 범위를 "entrypoint에서 import-도달 가능한 전이적 소스"로 명시하거나 런타임 트립와이어 테스트 추가 — 미수정 `evaluate_arm` import 경로의 소스-검사 회피 방지. 규범 문구 자체는 이미 교체를 의무화하므로 동결 차단 아님.
2. **(cosmetic)** `freeze_manifest_commit.txt`의 커밋 시점/postrun registry 포함 여부 한 줄 명시(선택).
3. **(cosmetic)** §13.4/§13.5 테스트 목록에 §17.3 단언과 §3.5 paired-L>F missing-NA 테스트 항목 추가(구현 DoD 반영).

과학적 must-fix 없음. threshold/seed/donor/step/LR 변경 제안 없음.

## 3. 최종 판정 블록

```text
최종 판정: CONTINUE
v1.0.8 freeze: 승인 (차단 must-fix 없음; §16.2 5단계 체인 자기참조 없음 확인)
구현+unit tests: 승인 (§13 매트릭스 + v1.0.7 필수 묶음 + §17.3 단언 + §3.5 paired-L>F/NA 테스트; 코드는 freeze 이후)
D0: 승인 (0 update, ≤4 config, ≤15 min, seed 20261111, labels_computed:false, freeze_manifest_sha256+manifest_commit 기록)
D1: 미승인 (별도 승인 필요)
3-seed: 미승인 (D1 이후 별도 등록 실행)
금지 범위: D1/3-seed/B0-B/B1/B2/Stage C 자동 진행, test 163 개봉, P1 사용, T5Gemma2(D-108 STOP), 결과 후 threshold/seed/donor/step/LR 변경, legacy bootstrap_paired 사용
최대 compute: 지금 승인분 = 구현+unit tests(CPU, 학습 없음) + D0(0 update, ≤15 min). 등록 Phase 6는 12 units/1,200 updates/120 min wall/6 threads/no GPU/no retry, T_proj ≤96 min, 120-min hard abort; 155 min은 D0+D1+등록 총 envelope로 단일 cap 아님 — 별도 승인 전까지 미실행
Must-fix (ranked): 없음(동결 차단). 권고: §17.3 단언 전이적 소스 명시 / freeze_manifest_commit.txt 커밋 시점 / §13 테스트 항목 추가
v1.0.8 self-contained: 예 — §17.3 call graph 추가로 구조까지 문서 내 완결, 외부 참조는 helper 6종+열거 artifact뿐
잘못된 전제: 없음. P0 tail 세 수치는 저장 artifact에서 실제 재도출됨(본 리뷰 §0), manifest_commit:null 규칙은 template와도 일치
```