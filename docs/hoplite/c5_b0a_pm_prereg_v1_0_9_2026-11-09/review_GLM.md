# C5 Phase 6 v1.0.9 — Final same-thread Review (GLM 5.3 Flash, reasoning max)

- 작성일: 2026-11-09
- 모델: `z-ai/glm-5.3-flash` (reasoning max), 동일 스레드(`thr_a757d209deae4493985cc2731c5af382`) 연속 최종 확인, 타 모델 답변 미재사용
- **검토 기준 HEAD SHA: `e680c8f`** (full: `e680c8fcb676dbd3d578c9ff7dc0238d08cd66fe`, "docs: add Phase 6 v1.0.9 repair")
- 동기화: `git fetch origin` + `git pull --ff-only origin main` → HEAD `b9fd854` ("docs: add C5 P/M v1.0.9 same-thread final review"). `e680c8f..b9fd854` diff는 리뷰 인프라 7개 파일(dispatch_fup/fup prompts/threads/watch/요청서)뿐 — 검토 대상 5개 문서 바이트는 `e680c8f`와 동일.
- **필수 verbatim 인용:** `c5_pm_stats.bootstrap_paired_v2`
  (§10.2 line 1183 `c5_pm_stats.bootstrap_paired_v2(seed=20261109)`, §17.3 lines 1755/1761 동일 심볼 — 본 보고서 전반에서 그대로 인용)
- 범위 준수: v1.0.8에서 closed로 확인된 7개 항목 재검토 없음(v1.0.8→v1.0.9 diff 25 changed lines 전수 확인 = DS 3개 수정 + 버전/경로/traceability 표기뿐, 과학적 내용 불변). 학습/평가 실행 없음, test 163 미개봉, P1 미사용, 서브에이전트 없음. 실행은 fixture 재해시와 읽기 전용 grep뿐.
- 상태: v1.0.9 final confirmation. **Phase 6/B0-B/B1/B2/Stage C 실행 미승인. test 163 sealed. P1 미사용. T5Gemma2 D-108 STOP 유지.**

---

## 0. 독립 검증 결과 (hash/읽기 전용)

| 항목 | 재계산 | 결과 |
|---|---|---|
| v1_0_9 golden 4 digests (state `43ecb58e…`, replay_base `c43ea35c…`, key_coverage `8277a713…`, control `6b50c226…`) | v1_0_8 스크립트 재실행, golden 파일은 `spec` 문자열만 다름(`C5 Phase 6 P/M v1.0.9`)을 diff로 확인 | **전부 일치** |
| preflight SHA `3ee3f1ca…69837af` | file bytes SHA256 | **일치**, template 선기입값과도 일치 |
| plan line 수 | 1,765 | 요청서와 일치 |
| helper 상태 | `runner/c5_pm_stats.py`, `runner/c5_pm_phase6.py` 미존재; legacy `bootstrap_paired` def는 `c5_mt5_lora_b0.py:384`, 호출 220(p0)/460(evaluate_arm)/653(metric_smoke) | §16.1 준수 상태 유지 확인 |
| v1.0.8→v1.0.9 diff | 전수 검토 | §10.2 심볼, §16.2 hash 정의 2줄, §17.3 timing, 버전 표기 외 변경 없음 |

---

## 1. Q1–Q5

### Q1. Symbol closure

- 판정: **agree — closed**
- 근거: v1.0.8 DS MF-1(§10.2 `bootstrap_paired` vs §17.3 `bootstrap_paired_v2` 충돌)의 원인이던 §10.2 정의가 `c5_pm_stats.bootstrap_paired_v2(seed=20261109)`(line 1183)로 단일화. §17.3 call graph(1755)와 교체 문구(1761)도 동일 심볼. §13.5(1585) "stats module does not import legacy `bootstrap_paired`"는 legacy 금지 선언이며, 이제 긍정적 정의(v2)와 충돌하지 않음. legacy 배제: §10.2 1188 "no legacy `bootstrap_paired`", §17.3 1760 import/call 금지 + 1762 `bootstrap_paired(` 소스/콜그래프 부재 단언. 패턴 정밀성 확인: 부분문자열 `bootstrap_paired(`는 `bootstrap_paired_v2(`와 일치하지 않음(`_v2`가 `(` 앞에 개입) — v2 호출 오탐 없음. §17.3이 검사 범위를 "Phase 6 path"로 한정한 것도 정확: helper 내 non-Phase-6 legacy 사용(220 p0_eval_split, 653 metric_smoke, 384 def)은 단언 대상이 아니며 전체 저장소 grep으로 검사하면 오탐이므로 현 범위 한정이 옳음.
- 다음 단계: (1) 선택 hardening — §13.3/13.5에 `bootstrap_paired_v2` 존재 단언 추가(부재 금지와 짝), (2) 구현 시 §17.3 단언을 "entrypoint에서 import-도달 가능한 전이적 소스"로 명시(v1.0.8 권고 계승).

### Q2. Freeze hash/custody

- 판정: **agree — closed**
- 근거: DS MF-2 해소. §16.2에 `freeze_manifest_sha256` = SHA256 of the committed `_FREEZE.json` bytes(line 1690) 명시적 정의 — 커밋(단계 3) 이후 산출, D0 보고서(단계 5)에 기록, `_FREEZE.json` 내부에 저장되지 않음(schema는 `manifest_commit:null`뿐) → 자기참조 없음. custody chain 완결: (1) final plan commit → (2) `_FREEZE.json` populate(`manifest_commit:null`) → (3) manifest commit → (4) `reports/provenance/C5_b0a/freeze_manifest_commit.txt`에 실제 SHA 기록 **후 커밋**(line 1691) → (5) D0이 `freeze_manifest_sha256` + `manifest_commit`(external 파일에서) + txt의 SHA256까지 병기(1691–1692). 모든 값이 post-commit 유도로 순환 없음. template v1_0_9가 동일 규칙(`manifest_commit:null`, note, preflight 선기입 일치) 반영.
- 다음 단계: (1) cosmetic — line 1691 "D0 also records its SHA256"의 `its`는 `freeze_manifest_commit.txt`를 지시하지만 문상이 모호; ERRATA 수준 한 문장으로 "the SHA256 of `freeze_manifest_commit.txt`"로 특정 권장, (2) 동결 시 단계 4 txt 커밋이 단계 5 D0 이전임을 절차 로그에 남길 것.

### Q3. evaluate_arm replacement before freeze

- 판정: **conditional — 요구 자체는 closed, §16.1과의 정합 하나를 ERRATA로 봉합 필요**
- 근거: DS MF-3 해소 — §17.3 line 1761이 교체 시점을 "**before the freeze commit**"으로 명시. 현 helper 상태: `evaluate_arm`의 legacy 호출은 `c5_mt5_lora_b0.py:460`(def 384, seed 20261108) — 교체 대상 특정됨. 단언 요구(1762) + "no monkeypatch-only workaround"(1763)로 기계적 검증 경로 존재.
- **신규 긴장**: §16.1 "No code before freeze."(line 1659) vs §17.3 "replaced before the freeze commit". 교체를 위해선 (a) `c5_mt5_lora_b0.py` 편집과 (b) import 대상 `c5_pm_stats.bootstrap_paired_v2`의 존재 — 즉 `runner/c5_pm_stats.py` 최소 골격 — 가 freeze commit 이전에 존재해야 하고, 이는 §16.1 문언과 문자적으로 충돌. 해법은 유일하고 명백(§17.3이 특정·의도적 지시이고 §16.1의 취지는 Phase 6 구현 선실행 방지)하지만, 문서 내 우선순위 규칙이 없어 엄격 감사 시 §16.1 위반 논쟁 여지가 남음.
- 다음 단계: (1) **번호 붙은 ERRATA 한 조항**(v1.0.9 + ERRATA는 §0 헤더가 허용)으로 §16.1을 봉합 — 권장 문구: "`No code before freeze` means no Phase 6 implementation beyond the §17.3 pre-freeze bootstrap replacement (`evaluate_arm` call → `c5_pm_stats.bootstrap_paired_v2` and the minimal `runner/c5_pm_stats.py` exporting it), which is part of freeze preparation." (2) 해당 ERRATA를 final plan commit에 포함(동결 준비의 일부), (3) 교체 후 helper는 freeze commit에서 `helper_commits`로 고정되므로 그 시점 이후 helper 재편집 금지 확인.

### Q4. Residual (v1.0.9가 새로 만든 문제)

- 판정: **conditional — 과학적 결함 0, text 항목 3**
- 근거: diff 전수 = DS 3개 수정 + 버전 표기. golden/template/preflight 불변·재현. 발견:
  1. **(medium, text)** §16.1 vs §17.3 pre-freeze 코드 긴장 — Q3 참조. freeze commit에 포함될 ERRATA 한 조항으로 봉합. 동결 자체를 무효화할 모호성은 아님(해법 유일).
  2. **(cosmetic)** line 1691 `its` 문상 모호 — Q2 참조.
  3. **(hardening, 선택)** §13.5 테스트 목록이 `bootstrap_paired_v2` 존재 단언과 Phase-6-path 범위 한정(220/653/384 비대상)을 명문화하지 않음 — §17.3이 규범을 제공하므로 결여는 아님.
- 다음 단계: 1·2를 동결 커밋 동반 ERRATA로, 3을 구현 DoD 반영.

### Q5. Final

- 판정: **CONTINUE (조건부 — §16.1 봉합 ERRATA를 final plan commit에 포함)**
- 근거: DS 3개 잔여(MF-1 심볼, MF-2 hash 정의, MF-3 timing) 전부 폐쇄, 새 text 긴장 1건은 ERRATA 한 조항으로 봉합 가능. v1.0.8에서 합의된 7개 closure는 diff상 불변. golden/preflight/line 수 재현. STOP/NARROW 사유 없음.

---

## 2. Must-fix (ranked)

1. **(ERRATA-1, fold into freeze commit)** §16.1↔§17.3 봉합: pre-freeze 허용 범위를 §17.3 bootstrap 교체(`c5_pm_stats.bootstrap_paired_v2` + 최소 `runner/c5_pm_stats.py`)로 한정하는 한 문장 — Q3 권안 문구.
2. **(cosmetic)** §16.2 line 1691을 "D0 also records the SHA256 of `freeze_manifest_commit.txt`"로 특정.
3. **(hardening)** §13.5에 `bootstrap_paired_v2` 존재 단언 + §17.3 단언의 Phase-6-path 범위 명문화.

과학적 must-fix 없음. threshold/seed/donor/step/LR 변경 제안 없음.

## 3. 최종 판정 블록

```text
최종 판정: CONTINUE (조건부 — ERRATA-1이 final plan commit에 포함되는 조건)
v1.0.9 freeze: 승인 (DS 3개 잔여 폐쇄 확인; ERRATA-1 동반 시 자기참조·심볼·timing 모두 봉합)
구현+unit tests: 승인 (freeze 이후; §13 매트릭스 + golden 5종 + T_proj 산술 + §17.3 Phase-6-path 단언 + §3.5 paired-L>F/NA + key-coverage 4-record)
D0: 승인 (0 update, ≤4 config, ≤15 min, seed 20261111, labels_computed:false; D0에 freeze_manifest_sha256 + manifest_commit + txt SHA256 기록)
D1: 미승인 (별도 승인 필요)
3-seed: 미승인 (D1 이후 별도 등록 실행)
금지 범위: D1/3-seed/B0-B/B1/B2/Stage C 자동 진행, test 163 개봉, P1 사용, T5Gemma2(D-108 STOP), 결과 후 threshold/seed/donor/step/LR 변경, Phase 6 path에서 legacy bootstrap_paired 사용, freeze commit 이후 helper 재편집
최대 compute: 지금 승인분 = 구현+unit tests(CPU, 학습 없음) + D0(0 update, ≤15 min). 등록 Phase 6는 12 units/1,200 updates/120 min wall/6 threads/no GPU/no retry, T_proj ≤96 min, 120-min hard abort; 155 min은 D0 15 + D1 20 + 등록 120의 총 envelope로 단일 cap 아님 — 별도 승인 전까지 미실행
Must-fix (ranked): ERRATA-1 §16.1↔§17.3 봉합 / §16.2 its 문상 특정 / §13.5 v2 존재·범위 단언
v1.0.9 self-contained: 예 — 심볼 단일화로 §10.2/§17.3/§13.5 계약 완결, 외부 참조는 helper 6종(helper_commits 고정)+열거 artifact뿐
잘못된 전제: 없음. 유일한 유보는 §16.1 "No code before freeze"가 §17.3 pre-freeze 교체와 문자적으로 충돌하는 것(해법 유일, ERRATA-1로 봉합)
```
