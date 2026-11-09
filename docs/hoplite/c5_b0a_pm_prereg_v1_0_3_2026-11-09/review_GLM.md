# C5 Phase 6 v1.0.3 — External Review (GLM)

- 작성일: 2026-11-09
- 검토자: **GLM 5.3 Flash (reasoning max)** — v1.0.3 신규 독립 라운드. v1.0.2 3-AI 라운드 및 타 모델 판정 재사용 없음(요청서 §0 규칙 준수).
- 요청서: `reports/EXTERNAL_REVIEW_C5_B0A_PM_PREREG_V1_0_3_2026-11-09.md`
- 동기화: `git fetch origin` → `git pull --ff-only origin main` → **"Already up to date"**. 검토 기준 HEAD = **`82648462b087e013fc9d85568d16faefe993ef63`** ("docs: add C5 P/M v1.0.3 review request").
  - plan/golden/preflight/p1 네 파일은 요청서 기준 HEAD `97e9d12`와 byte-identical(`git diff --stat 97e9d12 HEAD` 빈 출력, `97e9d12`는 HEAD의 조상임을 확인).
  - 리뷰 수행 중 origin/main이 `c53ed76`("docs: record C5 P/M v1.0.3 review thread ids", `threads.json` +20 lines)으로 진행했으나 검토 대상(plan/golden/provenance/runner/tests)에는 무영향. 기준 HEAD는 `8264846` 유지.
- 대상: `docs/plan_c5_b0a_pm_prereg_v1_0_3.md`(1,618 lines), `docs/hoplite/c5_b0a_pm_prereg_v1_0_3_2026-11-09/golden_vectors.json`, `reports/C5_B0A_PM_PREREG_V1_0_2_3AI_REVIEW_SYNTHESIS_2026-11-09.md`, `reports/provenance/C5_b0a/{m_cohort_preflight,p0_native_sanity,p1_usage}.json`, `runner/c5_mt5_lora_b0.py`, `eval/tests/test_c5_b0_metric.py`
- 방법: **read-only 컨센테이션**. 학습·평가 미실행, test 163 미개봉, P1 데이터 미사용, 외부 API 미사용, subagent/추가 LLM 미호출, 저장소 수정 없음(본 보고서 파일 1개가 유일한 write).
- 수행한 유일한 "계산": golden 5종 digest·preflight content hash·P0 파생 통계의 **순수 재계산**(sha256 / frame 직렬화 / canonical JSON; `/tmp` 스크래치 스크립트, 저장소 파일 미수정). 이는 학습·평가가 아니라 상수 대조이며, 요청서 §0.2의 "원문 확인" 범위다.

---

## 0. 한 줄 결론

> **CONTINUE.** v1.0.3은 v1.0.2의 10개 blocker를 text/golden/schema 수준에서 **10/10 폐쇄**했다. blocker-class 잔여는 0이다. 필수 golden 5종과 preflight hash를 독립 재계산으로 **전부 재현**했고, 360/480/1,680/560/600 산술, 12-checkpoint map, phase-7 enum/CE binding, P1 fail-closed, P_VALID tri-state, control tensor schema, D0 정의를 확인했다. 잔여는 7건의 1-line clarifications(MF-A~MF-G, 수치·게이트·임계값 변경 0)이며 freeze commit 본문 또는 번호 ERRATA로 흡수 가능하다. **freeze + 구현 + unit tests + D0 승인. D1/3-seed/B0-B 이하는 미승인.**

---

## 1. 독립 재계산 결과 (근거의 근거)

| 항목 | 기대값(Plan §12.3 / §0.4) | 독립 재계산 | 판정 |
|---|---|---|---|
| state full | `43ecb58e…95d65712` | 동일 | ✅ 일치 |
| state empty | `e3b0c442…7852b855` | 동일 | ✅ 일치 |
| replay base (donor_id key, key-asc) | `c43ea35c…851667` | 동일 | ✅ 일치 |
| replay supplemental (key-asc) | `8277a713…97af7a20` | 동일 | ✅ 일치 |
| control manifest frames (name-asc) | `6b50c226…0ec1938` | 동일 | ✅ 일치 |
| preflight content SHA-256 | `3ee3f1ca…69837af` | 동일(파일 + `.sha256` sidecar 동일) | ✅ 일치 |

- 재계산 방법: 레코드를 canonical key `(doc_id, arm, seed, variant, endpoint, memory_kind, donor_id)` 오름차순 정렬 후 `json.dumps(sort_keys=True, separators=(',',':'))` → UTF-8 SHA256. state/control은 §12.1 frame spec(`u32le name_len | name | u8 dtype_len | dtype | u8 ndim | u32le shape | u64le nbytes | LE bytes`) 그대로 구현.
- **control fixture 주의(유일한 미묘점)**: golden JSON의 배열 나열 순서(M_POS_MEAN 먼저)로 직렬화하면 `531ba0ad…33a03bd68`이 나온다. §12.1 규범 규칙(**canonical name 오름차순** — `M_NORM/doc_a` < `M_POS_MEAN`, 'N'(0x4E) < 'P'(0x50))으로 직렬화했을 때만 `6b50c226…c0ec1938`이 재현된다. 즉 규범은 자기일관적이고 상수는 재현되지만, **fixture 나열 순서 ≠ digest 순서**라는 1-line note가 구현자 혼란을 막는다(MF-F).
- replay base/supp는 fixture 배열 순서 == canonical key 오름차순이라 두 규칙이 같은 digest를 준다. `sort_keys`(object key) + record key-asc 정렬의 조합으로 충분하고, permutation-invariance 테스트가 §13.4에 있다.
- **canonical key 전환(donor_sort→donor_id)은 base digest를 깨지 않았다**(재계산으로 확인). base fixture는 null(doc_a)과 0(doc_b)이 섞여 있지만 doc_id가 정렬기를 먼저 결정하므로 null 규칙과 무관하게 동일 digest.
- P0 파생 통계 재계산(artifact per_doc 입력, §10.4 tie rule 적용): train median 4.0680 / positive **14** / top3 signed .4222 / abs .3410; val median **2.9739** / positive **18** / top3 signed **.4862** / abs **.4335**(common-15 **.4548**); ln(250100) = **12.4296** ≈ 12.43. 요청서·artifact 수치와 전부 일치.
- `git status --porcelain` 비어 있음(검토자에 의한 저장소 변경 없음). fresh depth-1 clone이라 `git fetch --deepen=6`으로 history만 확장(read-only).

---

## 2. Q1–Q13

형식: 판정 / 근거 / 다음 단계(요청서 §5).

### Q1. 10 blocker closure — **판정: agree (10/10 closed)**

| # | blocker (v1.0.2 MF) | 상태 | 근거 |
|---|---|---|---|
| 1 | `donor_sort` vs `donor_id` | **closed** | §12.2 key 마지막 축 = `donor_id`(null/0..4); `donor_sort`는 internal only, 미직렬화·미해시(plan L1404, L1512). golden base/supp 레코드가 donor_id이고 재계산 digest 일치. grep상 normative `donor_sort` 잔존 없음 |
| 2 | 단일 checkpoint로 1,680 replay 불가 | **closed** | §11.4 step1 "load `final_checkpoint_hash` map (12 keys: arm/seed)", §12.1 "postrun map: 12 keys; no single-checkpoint replay", §13.4 테스트. 잔여: map 직렬화 포맷 미고정(MF-C) |
| 3 | per-arm 420 → 360/480 | **closed** | §11.5/요청서 §2.2. 재계산: arm-seed F/L 15×2×2×2=120, P/PA 20×2×2×2=160; 등록 arm당 3×120=**360** / 3×160=**480**; 2×(360+480)=**1,680** ✓; D1 phase5 2×120+2×160=**560** ✓; multiplicity common 96(=3seed×4arm×2var×2ep×2kind), native-only 48 ✓; `t_primary_replay_arm` 동일 규정 |
| 4 | phase-7 enum/CE binding | **closed** | 일반 enum `memory_kind∈{control,real,donor}`(§12.2) + phase5 subset `{control,real}`, donor_id=null / phase7 subset `{real,donor}`, donor_id=0..4(§9.6.1); `donor_prefix`=arm 공간 donor 메모리, `K_d=min(len real, len donor)`; 저장 `ce`(raw)/`baseline_ce`/`delta`; replay hash는 `{key,ce}` 전용. 잔여: baseline_ce 출처 1문장(MF-A) |
| 5 | supplemental golden 정렬 `8277a7…` | **closed** | `8277a713…af7a20` 독립 재현 ✓. v1.0.3 golden 배열이 이미 canonical ascending(이전 라운드의 `38e5e2f…` 문제 해소). §13.4 permutation test |
| 6 | P1 strict both flags | **closed** | §4.0: manifest SHA256 일치 ∧ `p1_used=false` ∧ `test_split_read=false` **동시** 요구; malformed/missing→NA; contradictory known-use→false; `test_split_used`는 allowlist 멤버십 판정(봉인 split 스캔 경로 자체가 없음); "attestation, not proof" 명시. 실제 `p1_usage.json`이 스키마와 일치(both false, checked_artifacts=[]) |
| 7 | `P_VALID` tri-state / F9 | **closed** | §4.5 명시 tri-state(false = path false ∨ nonfinite / NA = missing·unreadable / true = 20 native ×2×2×2 per seed finite); F9(`p_step NA + p_valid NA`)/F10(`pa_path NA + pa_valid NA`)이 §7.2에서 reachable NA 조합으로 재작성; §4.6 precedence("p_step NA + p_valid=false → NOT_ASSESSABLE")와 일관 |
| 8 | control tensor schema | **closed** | §12.1: 경로 2종, NPZ key `tensor`, canonical name, `target_id="__shared__"` sentinel, `<f4 [K_M,512]`, manifest v1 필드, **tensor-frame hash(≠ZIP bytes)**, name-asc `control_digest`; golden `6b50c226…` 재현 ✓ |
| 9 | P/PA calibration asymmetry | **closed** | §4.5에 의도적 비대칭 명시: P/PA copy `>= .05`, `2/3 seeds_positive`·paired `L>F` 없음 / L은 copy `>0` + 두 conjunct. "documented arm asymmetry, not a threshold change" — 사전등록 단계 정의이므로 결과 후 변경 금지 원칙과 충돌 없음 |
| 10 | D0/artifact/native assert | **closed** | §11.2: 0 update, ≤4 configs = arm당 1개 0-update config(F/L/P/PA), 중복 금지, ≤15 min, seed 20261111, `labels_computed:false`, `not_a_result:true`, 등록 cap 분리, h-length assert + P/PA native-512 assert, control manifest 경로/보존(~0.3GB, B0-B까지) |

- 다음 단계: (1) MF-A/MF-B를 freeze 본문 또는 ERRATA로 흡수 (2) §13.4에 null-sort·map-format 유닛 테스트 추가 (3) freeze commit에 content SHA-256 기록.

### Q2. Self-containedness — **판정: conditional (구현 가능, 잔여는 1-line clarifications)**

- v1.0.3만으로 구현 가능한 근거: 모델/토크나이저/loss/mask/donor/generation이 §2.5.1–2.5.7에 절차 수준으로 기술됨(same-position token CE·no-shift, copy<5→None, per-arm donor rule + doc_id tiebreak, greedy 256). arm/초모표 §2.1–2.2, cohort 권위 = preflight artifact(§0.4/§1.2), tri-state 연산자 §3, path flags §4.0, control §5, 라벨/dispatch §6, fixtures §7, M §9, 통계 §10, D0/D1 §11, hash/golden §12, 테스트 §13. 참조 외부물은 **데이터 artifact**뿐(preflight JSON, splits.json, EG2 cache, mt5-small, golden_vectors.json, p1_usage.json) — 문서 의존이 아니라 데이터 의존으로 정당.
- 남은 암묵 지식(전부 1-line으로 제거 가능, 과학적 선택 아님): ① phase-7 `baseline_ce` 출처(MF-A) ② donor_id null 정렬 규칙(MF-B) ③ checkpoint map 직렬화 포맷(MF-C) ④ checkpoint frame `dtype_str` 포맷(MF-D) ⑤ `checked_artifacts` completeness 판정자(MF-E) ⑥ D0 수행 연산 목록("no forward" vs "no-grad forward 1회 허용") 명시(MF-H, optional).
- 참고: `runner/c5_mt5_lora_b0.py`는 B0 시대 참조 구현이며 Phase 6 P/M 구현물이 아니다. `make_labels`는 unpadded label ids(EOS 포함, -100 없음)를 반환하므로 §2.5.2 "full CE = out.loss"와 모순 없음. legacy `bootstrap_paired(seed=20261108)` + mislabeled `seeds_positive`는 §10.2가 신규 `runner/c5_pm_stats.py` 재사용 금지로 정확히 차단했다.

### Q3. Canonical hash / golden — **판정: agree**

- §12.2 key와 golden 레코드가 `donor_id`로 일치하고, base `c43ea…` / supp `8277a7…` / state `43ecb…` / empty `e3b0…` / control `6b50…`를 독립 재현했다(§1 표).
- `sort_keys`는 object key만 정렬하므로 record 배열 정렬은 명시적 key-asc가 필요한데 v1.0.3이 그렇게 규정했고 fixture도 이미 정렬돼 있다. permutation/duplicate/missing 테스트가 §13.4에 있다.
- 잔여 1건: donor_id null vs 0..4 혼재 배열의 정렬 규칙 명문화(MF-B). Python tuple sort는 None/int 혼재 시 TypeError를 낸다(예: "내부 sort key로 donor_sort(-1) 사용, null 먼저"의 1문장 필요). 기존 fixture digest에는 영향 없음(재계산 확인).

### Q4. Replay arithmetic — **판정: agree**

- 산술 전부 재확인: arm-seed 120/160, D1 phase5 총 560, 등록 arm당 360/480, 총 1,680, multiplicity 96/48, phase7 600/arm-seed(§2 Q1 표 3행).
- phase-7 격리: §11.4 step6 "replay_ok true only if primary 1,680 coverage and numeric comparison pass", step7 "phase-7 diagnostic failure does not change primary replay_ok; it is reported separately"; §9.6.1 "does not feed m_valid or any gate" ✓.
- T_proj: ×3 seeds, `t_primary_replay_arm` = arm-seed 120/160(D1) / 등록 120/160 per seed·360/480 per arm ✓, phase7 별도 항 `t_replay_15x5x2x2x2_arm` ✓, ≤96 min + 120-min hard abort ✓. prospective 1,204 updates / 155 min = 1,200+4(D1), 120+20+15(D0) — "not grant" 명시 ✓.
- 다음 단계: (1) 없음(산술 자체) (2) watch item: 등록 런 phase7 총 3×4×600=7,200 diagnostic forwards의 wall-clock은 D1이 측정해 T_proj에 반영 — T_proj>96이면 사전등록된 대로 중단(결과 후 변경 아님) (3) D1 보고 체크리스트가 T_proj 9항을 모두 채우는지 확인.

### Q5. Phase-7 measurement — **판정: conditional**

- 실행 가능: `donor_prefix` = donor 문서의 arm 공간 메모리(§9.6.1), `K_d=min`, `control_pos=M_POS_MEAN[:K_d]`, `control_norm=M_NORM(t)[:K_d]`, `ce`=레코드 텐서 raw CE, `delta=baseline_ce−ce`. memory_kind∈{real,donor}, donor_id 0..4, **600 count 유지**.
- variant 축은 raw ce를 중복시킨다(600 중 서로 다른 ce는 300 = 15×5×2×2). plan이 이를 명시적으로 인정("raw ce may duplicate across variants, but delta differs")하고 replay hash는 `{key,ce}` 전용 — variant가 key에 있으므로 key 충돌도 없다.
- 조건부 근거: `baseline_ce`가 (a) phase-7 내에서 K_d-crop control을 재계산한 값인지, (b) phase-5 저장 control CE(K=753/512 full)인지 문장상 양쪽으로 읽힌다. recipe가 control을 K_d crop으로 제시하므로 (a)가 자연 독해지만, 진단 전용 필드라도 레코드 스키마와 테스트가 이를 암호화하므로 freeze 전 1문장 고정 필요(MF-A).
- 다음 단계: (1) MF-A 문장 추가 (2) 유닛 테스트: 600 exact key set, `delta == baseline_ce − ce` 일관성, variant 간 ce 동일 허용 (3) phase7 real CE ≠ phase5 real CE(K 다름, §11.4 "not comparable") 문서화로 오독 방지.

### Q6. P1 / allowlist — **판정: agree**

- fail-closed 위계 확인: 알려진 실패(false)가 먼저(§4.2), assay-tier NA가 그 다음(§4.3). manifest 누락/malformed→NA, 모순적 known-use→false. `test_split_used`는 allowlist 멤버십으로만 판정 — 봉인 test 163을 여는 경로가 정의에 없음 ✓.
- both flags: `p1_used=false` ∧ `test_split_read=false` 동시 요구 + freeze 시 `p1_manifest_sha256` 고정 ✓. 현재 `p1_usage.json` both false, checked_artifacts=[](artifact 존재 전 빈 리스트 유효).
- 잔여: "after artifacts exist, incomplete list → NA"의 completeness 판정자가 암묵적(MF-E). attestation-not-proof 한계가 문서에 명시되어 과잉 주장 없음.
- 다음 단계: (1) freeze/postrun manifest artifact inventory를 completeness 기준으로 명시 (2) 유닛 테스트: flag 누락→NA, flag true→false, allowlist 외 ID→test_split_used=true (3) test 163 미개봉 유지(본 리뷰도 미개봉).

### Q7. P_VALID / M_CONTROL_INVALID — **판정: agree**

- tri-state 일관: false = path false ∨ nonfinite, NA = missing/unreadable, true = 20×2×2×2 per seed present/finite(§4.5). F9/F10 reachable(§7.2) ✓. "known failure first"(§4.2) → assay-tier NA(§4.3) → P/PA(§4.4) 위계와 모순 없음.
- `M_CONTROL_INVALID` conditional reachable 유지: §5.4에서 `m_evaluable=true ∧ p_valid=true ∧ pa_valid=true ∧ m_valid=false`일 때만. `p_valid=false`는 `M_NOT_EVALUABLE` 라우팅(INVALID 아님) ✓. PA veto(§5.3)는 calibration 차단이지 native regime 부정이 아님 ✓.
- asymmetry 정당: 사전등록에서 정의된 arm 비대칭이고 "No post-result change"가 명시됨. 신규 과학적 선택이 아니라 정의의 문서화다.
- 다음 단계: (1) fixture: `m_pass_l=false ∧ m_valid=true → M_CONTROL_FAIL` / `m_valid=false → M_CONTROL_INVALID` (2) F9/F10 회귀 테스트 (3) PA calibration fail이 `M_NOT_EVALUABLE`로 가지 않는 부정 테스트.

### Q8. Control tensors — **판정: agree**

- 스키마 완비: `control_manifest/{arm}/{seed}/M_POS_MEAN.npz`, `.../M_NORM/{target_id}.npz`, NPZ key `tensor`, canonical name, `__shared__` sentinel, `<f4 [K_M,512]`, manifest v1 필드(name/path/array_key/target_id/dtype/shape/sha256), **tensor-frame hash**(ZIP bytes 아님), name-asc `control_digest`, hash-only 재구성 금지 ✓.
- golden `6b50c226…` 독립 재현 ✓ — 단, **name-asc 규칙 하에서만**(§1 참조; MF-F note).
- footprint 재계산: F/L 6유닛×(1+15)×753×512×4B ≈ 137MB + P/PA 6×(1+20)×512×512×4B ≈ 126MB + M_POS_MEAN 등 ≈ **0.27GB ≈ "~0.3GB"** 주장과 일치, cap 내. B0-B까지 보존 명시(§11.2) ✓.
- 다음 단계: (1) MF-F 1-line note (2) 부정 테스트: ZIP-archive-bytes hash는 `6b50…`과 일치하면 안 됨(프레임 hash임을 검증) (3) `__shared__` 메타데이터 검증 테스트.

### Q9. D0/D1/cap — **판정: agree**

- D0: 0 update, ≤4 configs = arm당 1개(중복 금지), ≤15 min, seed 20261111, `labels_computed:false`, `not_a_result:true`, 등록 cap 분리, h-length/native-512 assert, no timing claim ✓.
- D1: 4 arms × 1 debug seed(20261111) × 1 update, ≤20 min, 별도 승인, decision/signal 라벨 없음(target-token CE 라벨은 계산), `not_a_result:true`, no registered seed ✓. 8 phases 전단계 측정, 누락 phase → no projection, step0는 update 전 또는 복원 상태 ✓.
- cap: 등록 1,200 updates / 120 min wall, threads 6, GPU 없음, retry 없음; D0/D1 분리; T_proj ≤96, hard abort 120; prospective 1,204/155는 한도 표기일 뿐 grant 아님 ✓. "D1 없이 3-seed 금지" ✓.
- 다음 단계: (1) D0 수행 연산 목록 1-line(MF-H, optional) (2) D1 결과가 T_proj 9개 시간 항을 모두 제공하는지 체크 (3) phase7 진단의 replay_ok 분리 보고 확인(이미 규정됨).

### Q10. 남은 Must-fix — **판정: conditional (신규 blocker 없음, ranked)**

| 순위 | ID | 내용 | 심각도 |
|---|---|---|---|
| 1 | MF-A | phase-7 `baseline_ce` 출처 고정: "K_d-crop control variant CE를 phase-7 조건에서 재계산한 값"(phase-5 저장 CE(K_M) 아님) — 1문장 | medium(진단 전용이나 스키마/테스트가 암호화) |
| 2 | MF-B | canonical record sort의 donor_id null 규칙 명문화(예: 내부 sort key로 donor_sort(-1), null 먼저) — 1문장 | medium-low(기존 fixture digest 무영향, 재계산 확인) |
| 3 | MF-C | `final_checkpoint_hash` map 직렬화 포맷 고정(postrun manifest JSON object, key `"{arm}/{seed}"` 12개) | low |
| 4 | MF-D | checkpoint frame `dtype_str` 포맷 고정(numpy charcode `"<f4"` 스타일; control 스키마·golden과 정합) | low |
| 5 | MF-E | `checked_artifacts` completeness 판정자 명시(freeze/postrun manifest inventory 기준) | low(실패 시 NA로 안전) |
| 6 | MF-F | golden control fixture 나열 순서 ≠ digest 순서 1-line note(sorted rule이 규범; `531ba0ad…` vs `6b50c226…` 재계산 확인) | cosmetic |
| 7 | MF-G | `p1_usage.json` extra `note` 필드 — 스키마 unknown-keys 허용 명시 또는 freeze 시 제거 | cosmetic |

요청서 Q10 지정 3항 특별 확인:
- canonical key 변경이 base digest를 깨지 않음 — **독립 재계산으로 확인** ✓
- 12 checkpoint map이 manifest에서 실제 표현됨 — §11.4/§12.1 규정됨, 포맷만 MF-C로 잔여
- phase-7 `baseline_ce`가 replay hash와 충돌하지 않음 — hash는 `{key,ce}` 전용이라 baseline/delta는 해시 도메인 외부 ✓(MF-A는 '저장값 의미'의 문제이지 hash 충돌이 아님)

### Q11. 동결·구현 승인 — **판정: agree (조건 포함)**

- 조건: MF-A/MF-B(및 가능하면 MF-C/MF-D)를 freeze commit 본문 또는 ERRATA-001/002로 **구현 시작 전** 반영. 수치·게이트·임계값 변경 0 → 신규 과학적 선택 아님(§16.1 규칙 위반 없음).
- 구현 전 필수 테스트(§13 매트릭스 최소 집합):
  1. state/empty/base/supp/control 5 golden 상수 테스트(구현이 상수를 재생성·덮어쓰지 않음 검증)
  2. permutation-invariance, duplicate/missing key reject
  3. donor_id null/0..4 canonical key + `donor_sort` 비직렬화 테스트(MF-B)
  4. 12-key checkpoint map, per-unit 120/160, aggregate 360/480/1,680 exact key set
  5. phase5 `{control,real}`,donor_id=null vs phase7 `{real,donor}`,donor_id=0..4 subset 분리
  6. P1: both flags strict, malformed→NA, contradictory→false, allowlist 외 ID→true
  7. P_VALID tri-state(nonfinite→false, missing→NA) + F9/F10
  8. `M_CONTROL_INVALID` reachability + `p_valid=false→M_NOT_EVALUABLE` 라우팅
  9. `m_pass_l`(2)/`m_valid`(4)/`m_evaluable`(5) operand 수 + ANDn/NOT3/ORn + §3.4 9 pairs + F1–F11 + fixtures 16–18
  10. tail: top3 tie rule(|d| desc, doc_id asc), abs gate/signed descriptive, `leave_top3` NA 규칙
  11. stats: n_boot 1000, seed 20261109, `documents_positive` vs legacy `seeds_positive` 분리, missing seed→NA(2-of-available 금지)
  12. donor rule: self-exclusion, length-nearest, per-arm, doc_id tiebreak, donor list artifact
  13. copy<5 dual behavior: signal 제외 vs primary M `endpoint_ok=false`(silent omission 금지)
  14. zero-margin: K=754→14 abort, no 15→14/native→common substitution
  15. native-512 assert, NPZ schema(`tensor` key, `<f4`, shape, `__shared__`), frame hash ≠ ZIP hash
- 다음 단계: (1) ERRATA 반영 후 freeze commit + content SHA-256 + `p1_manifest_sha256` 기록 (2) 위 최소 테스트 세트를 구현 코드보다 먼저 착수 (3) decision function은 pure function(모델/데이터 없음) 유지.

### Q12. B0-B / D1 / 3-seed 경계 — **판정: agree (재진술 포함)**

경계는 충분하다: §14가 B0-B를 별도 사전등록/승인으로 고정하고, B1/B2/Stage C 자동 승인을 금지하며, D1(별도 승인) → 3-seed(별도) 순서를 강제한다("D1 없이 3-seed 금지"). EXPLORATORY_L_SIGNAL 단독은 승인이 아니고, full_k_secondary/P0/PA_RETENTION은 evidence가 아니다.

v1.0.3 라벨로 재진술한 B0-B predicate(모든 피연산자 true, NA는 불통):

```text
B0-B eligible ⇔
  assay_path_ok = true ∧ p0_path_ok = true
  ∧ p_step100_path_ok = true ∧ pa_step100_path_ok = true
  ∧ test_split_used = false
  ∧ validity_status = VALID ∧ n_signal = 15          (">=15"의 실질 = exactly 15)
  ∧ signal_status = EXPLORATORY_L_SIGNAL
  ∧ control_status = M_CONTROL_PASS
      (= m_evaluable=true ∧ p_valid=true ∧ pa_valid=true
         ∧ m_valid=true ∧ m_pass_l=true)
  ∧ tail_driven = false                               (true/NA 모두 block)
  ∧ leakage/mode/metric pass ∧ artifact complete
      (control_manifest ~0.3GB B0-B까지 보존 포함)
  ∧ 별도 B0-B prereg + 승인
```

### Q13. 최종 판정 및 freeze — **판정: CONTINUE**

아래 §4 최종 블록 참조. 핵심: freeze + 구현 + unit tests + D0 승인, D1/3-seed/B0-B/B1/B2/Stage C 미승인, test 163 봉인 유지, T5Gemma2 D-108 STOP 유지, 등록 런 compute는 본 라운드가 grant하지 않음.

---

## 3. 검증 한계 (명시적)

- 실행하지 않았다: 학습/평가/생성/유닛테스트 전부 미실행. runner와 test 파일은 문서 대조용으로 **읽기만** 했다.
- digest 재계산은 golden_vectors.json이 제공한 레코드/프레임 값을 규범 직렬화로 다시 해시한 것이다 — 구현 under test가 없는 상태의 상수 검증이다.
- test 163 미개봉. P1은 p1_usage.json manifest만 열람(요청서가 명시한 검토 대상). P1 데이터 그 자체는 사용하지 않았다.
- T5Gemma2 관련 파일은 열지 않았다(D-108 STOP 유지).
- 통계 재계산은 artifact의 per_doc 값을 입력으로 한 순수 후처리다.
- `reports/provenance/C5_b0a/`의 `s2026110{8,9,10}_{frozen,lora}.json` 등은 이전에 승인된 B0-A F/L 라운드의 역사적 artifact다. P/PA/M trained artifact는 존재하지 않는다 — "no trained P/PA/M result has been seen" 전제와 일치.

## 4. 최종 판정

```text
최종 판정: CONTINUE
v1.0.3 freeze: 승인 — MF-A/MF-B를 freeze 본문 또는 ERRATA-001/002로 흡수(수치 변경 0).
               freeze commit + content SHA-256 + p1_manifest_sha256 기록.
구현+unit tests: 승인 — §13 매트릭스, Q11 최소 테스트 세트 우선; pure decision function;
               synthetic fixtures; CPU-only; 모델 의존 테스트는 로컬 mt5-small 존재 시에만(기존 test 파일 관례 유지).
D0: 승인 — ≤4 configs(arm당 1개 0-update), ≤15 min, seed 20261111, not_a_result=true,
    labels_computed:false, h-length/native-512 assert, no timing claim.
D1: 미승인 (D0 통과 후 별도 승인)
3-seed: 미승인 (D1 별도 승인 후 별도 승인)
금지 범위: Phase 6 등록 런 실행, D1, 3-seed, B0-B/B1/B2/Stage C 자동 진행,
    test 163(봉인 유지), P1 사용, T5Gemma2(D-108 STOP),
    결과 후 threshold/seed/donor/step/LR 변경, golden 상수의 구현 측 재생성,
    debug_replay_hash vs final_replay_hash 직접 비교.
최대 compute: 본 라운드 승인분 = D0 ≤4 configs ≤15 min(6 threads, CPU 전용, GPU 없음)
    + unit tests(CPU, 학습 없음). 등록 런 1,200 updates/120 min과
    prospective 1,204 updates/155 min은 등록 프로토콜 상한 표기일 뿐이며 본 리뷰가 grant하지 않음.
Must-fix (ranked): MF-A(baseline_ce 출처) > MF-B(null sort 규칙) > MF-C(checkpoint map 포맷)
    > MF-D(dtype_str 포맷) > MF-E(checked_artifacts 판정자) > MF-F(control fixture 순서 note)
    > MF-G(p1 note 필드)
v1.0.3 self-contained: YES — 데이터 artifact 참조는 정당; 잔여 6건은 전부 1-line clarifications.
잘못된 전제: 없음. 보정 2건: (1) 요청서 "작성 기준 HEAD 97e9d12"는 plan 기준으로 유효하나
    동기화 HEAD는 8264846이고 리뷰 중 origin이 c53ed76(threads.json 추가)으로 진행 — 검토 대상 무영향.
    (2) P0 서술에서 "signed top3 .4862 / absolute .43355"는 val20 기준, common-15 abs는 .4548 —
    축 혼동 방지를 위해 artifact 인용 시 split/cohort를 명시할 것(수치 자체는 재계산으로 전부 확인).
```

## 5. 독립성 선언

본 보고서는 요청서 §0을 그대로 수행한 단일 모델(GLM 5.3 Flash max)의 독립 판정이다. v1.0.2 3-AI synthesis는 요청서가 지정한 필독 자료로서 **blocker 목록의 baseline**으로만 사용했고, 폐쇄 판정은 v1.0.3 원문·golden·artifact에 대한 직접 검증과 독립 재계산에 근거한다. 타 검토자의 v1.0.3 판정(있다면)은 보지 않았거나 반영하지 않았다. 본 리뷰는 Phase 6/B0-B 실행을 승인하지 않는다.