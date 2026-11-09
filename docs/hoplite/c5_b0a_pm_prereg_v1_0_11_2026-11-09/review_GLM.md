# C5 Phase 6 v1.0.11 — Own-Loop Final Confirmation (GLM 5.3 Flash, reasoning max)

- 작성일: 2026-11-09
- 모델: `z-ai/glm-5.3-flash` (reasoning max), 동일 스레드(`thr_a757d209deae4493985cc2731c5af382`) 연속, 타 모델 답변 미재사용
- **검토 기준 HEAD SHA: `6fad89e`** (full: `6fad89e59e4aa2222010f2360e5eb4c2572c4023`, "docs: add Phase 6 v1.0.11 own-loop repair")
- 동기화: `git fetch origin` + `git pull --ff-only origin main` → HEAD `9954c98` ("docs: add C5 P/M v1.0.11 same-thread final review"). `6fad89e..9954c98` diff는 리뷰 인프라 7개 파일뿐 — 검토 대상 5개 문서 바이트는 `6fad89e`와 동일.
- **필수 verbatim 인용 (plan line 1756, 행 전체 공백 일치 기계 확인):**
  ```
    -> own training loop
  ```
  (요청 구절 `-> own training loop` 포함, §17.3 line 1756; 짝인 `-> own eval loop`는 line 1757)
- 범위 준수: v1.0.10에서 closed된 심볼/hash/custody·pre-freeze 충돌 재검토 없음(v1.0.10→v1.0.11 diff 전수 확인 — §10.2/§16.2 무변경). 학습/평가 실행 없음, test 163 미개봉, P1 미사용, 서브에이전트 없음. 실행은 fixture 재해시와 읽기 전용 grep/line 확인뿐.
- 상태: v1.0.11 own-loop final confirmation. **Phase 6/B0-B/B1/B2/Stage C 실행 미승인. test 163 sealed. P1 미사용. T5Gemma2 D-108 STOP.**

---

## 0. 독립 검증 결과 (hash/읽기 전용)

| 항목 | 재계산 | 결과 |
|---|---|---|
| v1_0_11 golden 4 digests (state `43ecb58e…`, replay_base `c43ea35c…`, key_coverage `8277a713…`, control `6b50c226…`) | 재해시; v1_0_10과 `spec` 문자열만 다름(`C5 Phase 6 P/M v1.0.11`)을 diff로 확인 | **전부 일치** |
| preflight SHA `3ee3f1ca…69837af` | file bytes SHA256 | **일치**, template 선기입 일치 |
| plan line 수 | 1,773 | 요청서와 일치 |
| verbatim quote | `'  -> own training loop'` 정확 행 일치 line 1756 | **확인** |
| §17.1 helper 표 | 7종(Adapter/make_labels/load_layer_cache/LoRALinear/attach_decoder_lora_mt5/native_memory/repeated_4gram_rate), `train_arm`/`evaluate_arm` **미기재** 확인 | v1.0.10 MF-3 해소 상태 유지 |
| pinned helper 전이 청결 | §17.1 7종 본문에서 `train_arm`/`evaluate_arm`/`bootstrap_paired` 부재(grep exit 1) | 배제 단언이 충족 가능함을 실증 |
| v1.0.10→v1.0.11 diff | 전수 검토 | §13.5 1줄, §17.3 교체, 버전 표기 외 없음. §2/§10/§16.2 불변 |

---

## 1. Q1–Q5

### Q1. Own-loop lifecycle

- 판정: **agree — closed**
- 근거: v1.0.10 NARROW(3/3)의 원인이던 §17.3 "`train_arm` may be reused for training" 조항이 **삭제**되고 call graph가 `own training loop / own eval loop / c5_pm_stats.bootstrap_paired_v2`(lines 1756–1758)로 교체. "Phase 6 owns training and evaluation loops; §2.7 mode/RNG rules apply"(line 1765) 신설. 구현(`c5_pm_phase6.py`/`c5_pm_stats.py` 생성)은 freeze 이후 승인 단계이고 "no pre-freeze helper edit is required"(1767) 유지 — §16.1 "No code before freeze."와 문자적·취지 모두 정합. v1.0.10 GLM ERRATA-A의 의도한 최종 상태와 동일.
- 다음 단계: (1) 동결, (2) 구현은 freeze 이후 새 모듈 생성으로 진행.

### Q2. train_arm/evaluate_arm 배제 + transitive path

- 판정: **agree — closed**
- 근거: 규정 3중 — §17.3 "it must not import or call `runner.c5_mt5_lora_b0.evaluate_arm`"(1761) + "…`train_arm`"(1762) + legacy `bootstrap_paired` 금지(1763 유지). 정의 명문화 — ""Phase 6 path" = transitive call graph rooted at `runner/c5_pm_phase6.py`"(1768) — v1.0.10 GLM ERRATA-B 그대로. test — "no `train_arm`, `evaluate_arm`, or legacy `bootstrap_paired(` in that transitive path"(1769). `train_arm` composite 사실도 명시(1766: "calls `evaluate_arm`; it is not training-only and must not be reused") — 헬퍼 사실(line 665→723→460)과 문서가 정합. 단언의 충족 가능성 실증: §17.1 pinned 7종 본문은 3 심볼 전부 부재(본 리뷰 grep) — 규정 준수 구현이 존재하며 test가 공허하거나 불가능하지 않음. `bootstrap_paired(` 패턴은 `bootstrap_paired_v2(`와 비일치 유지(오탐 없음).
- 미세 문언: §13.5(1586)는 "does not **import**", §17.3 test는 transitive path(호출 포함) — §17.3이 더 엄격한 규범이고 import는 path의 부분집합이라 모순 아님(cosmetic 정렬 여지).
- 다음 단계: (1) 구현 시 §17.3 정의 기준 단언을 유닛 테스트로 착지, (2) §13.5 문언을 §17.3 정의 참조로 정렬(cosmetic).

### Q3. §2.7/§2.5 하의 훈련 정확성

- 판정: **agree — own loop로 전부 구현 가능, 규범 참조 완결**
- 근거: v1.0.11은 §2를 전혀 변경하지 않았고(diff 전수), 다음 규범 세트가 own training loop를 완전 지정:
  - **§2.7 mode/RNG**: 모드 표(F/L/P/PA × base decoder/native encoder/adapter/LoRA), base decoder eval 필수 + `model.train()`이 frozen 층 재활성 금지, LoRA dropout train 전용, 평가 시 전체 eval 복원, arm별 fresh state, RNG 순서 `torch.manual_seed(seed) → Adapter(512,512) → LoRA attach, 재시드 없음`, 파라미터 인벤터리 단언, "P has no adapter".
  - **§2.5.1–2.5.6**: 토크나이저/손실(내장 CE + token CE 동일 위치), 메모리 구성(F/L EG2 `A(h)[:753]`, P/PA native `[:512]`, P `A=identity`), adapter/LoRA 초기화(kaiming a=sqrt(5), B zeros, r8 α16 dropout .05, scale=alpha/r, 64모듈), copyable mask, donor 규칙.
  - **§2.1/§2.2/§2.4/§2.6**: arm 표(P decoder-LoRA only, PA random-init adapter+LoRA), 하이퍼파라미터(AdamW, lr 분리, order `train20_ids[step % 20]`, clip 1.0), P/PA 초기화, h_len/데이터 경로.
  - own eval loop의 CE 산출도 §2.5.2/§2.5.5가 규범으로 지정(토큰 CE 공식 + copy mask) — §17.1 공백 아님(`make_labels`는 pinned, CE 공식은 §2.5.2 본문).
  - 헬퍼 `train_arm`이 frozen/lora만 지원하고 F/L EG2 경로 전용인 점은 P/PA native 경로가 신규 구현이어야 하는 이유이며, "Phase 6 owns training and evaluation loops"가 이를 정확히 반영 — v1.0.10 발견과 정합.
- 다음 단계: (1) 구현 시 §2.7 RNG 순서/모드 정책을 단언 테스트로 고정, (2) P/PA native 경로(§2.4/§2.5.3) 별도 구현, (3) D0의 h-length assert(F/L cache / P/PA 512)로 경로 검증.

### Q4. Residual

- 판정: **conditional — 과학적 결함 0, 경미 표기 3**
- 근거:
  1. **(low/cosmetic)** §13.5 "does not import" vs §17.3 transitive-path test 문언 차이 — §17.3이 규범·더 엄격; 정렬 권장.
  2. **(cosmetic)** `Adapter` 클래스가 두 모듈에 존재(`c5_mt5_layer_probe.py:52`, `c5_a2null_eval.py:28`) — §17.1이 layer_probe 쪽을 pin하므로 모호성 없음. import 경로 주의 한 줄 여지.
  3. **(observation)** helper 내 P0 경유 legacy `bootstrap_paired`(`p0_eval_split`, line 220)는 Phase 6 path 밖 — "P0 is unaffected: it uses `p0_eval_split`"(1770) 문구가 사실과 정확히 일치(직접 확인). §10.2(신규 stats 모듈 금지)와 무충돌.
  - v1.0.10 GLM ERRATA-A/B는 모두 문언 등가로 반영됨; cosmetic이었던 P/PA 신규 경로 명시는 "Phase 6 owns training and evaluation loops"로 자연 해소. MF-4(P0) 라인도 반영.

### Q5. Final

- 판정: **CONTINUE**
- 근거: v1.0.10 3/3 NARROW의 유일한 blocker(MF-1 train_arm composite)와 정의 공백(MF-2), §17.1 정합(MF-3), P0 명시(MF-4)가 전부 폐쇄 — 각각 본 리뷰가 원문 행 단위로 대응 확인. 신규 과학적 내용 없음(diff 전수 = text/표기). golden/preflight/line 수 재현. pinned helper의 전이 청결 실증으로 배제 단언이 실행 가능. STOP/NARROW 사유 없음.

---

## 2. Must-fix (ranked)

**동결 차단 must-fix 없음.** 구현 시점 권고(순위):
1. **(low)** §13.5 문언을 §17.3 transitive-path 정의 참조로 정렬.
2. **(cosmetic)** §17.1에 `Adapter` import 경로(`c5_mt5_layer_probe.py`) 주의 한 줄(두 모듈에 동명 클래스 존재).
3. **(hardening)** 구현 유닛 테스트: §2.7 RNG 순서/모드 정책 단언 + transitive-path 3-심볼 부재 단언 착지.

과학적 must-fix 없음. threshold/seed/donor/step/LR 변경 제안 없음.

## 3. 최종 판정 블록

```text
최종 판정: CONTINUE
v1.0.11 freeze: 승인 (v1.0.10 3/3 NARROW 잔여 전부 폐쇄; §17.3 자기일관, §16.1 정합, 배제 단언 충족 가능 실증)
구현+unit tests: 승인 (freeze 이후; §13 매트릭스 + §2.7 RNG/모드 단언 + transitive-path 3-심볼 부재 + paired-L>F/NA + golden 5종 + T_proj 산술; own train/eval loop는 §2.1/2.2/2.4/2.5/2.6/2.7 규범으로 구현)
D0: 승인 (0 update, ≤4 config, ≤15 min, seed 20261111, labels_computed:false; D0에 freeze_manifest_sha256 + manifest_commit + txt SHA256 기록)
D1: 미승인 (별도 승인 필요)
3-seed: 미승인 (D1 이후 별도 등록 실행)
금지 범위: D1/3-seed/B0-B/B1/B2/Stage C 자동 진행, test 163 개봉, P1 사용, T5Gemma2(D-108 STOP), 결과 후 threshold/seed/donor/step/LR 변경, Phase 6 path에서 train_arm·evaluate_arm·legacy bootstrap_paired 사용, pre-freeze helper 편집, freeze 이후 helper 재편집(ERRATA 제외)
최대 compute: 지금 승인분 = 구현+unit tests(CPU, 학습 없음) + D0(0 update, ≤15 min). 등록 Phase 6는 12 units/1,200 updates/120 min wall/6 threads/no GPU/no retry, T_proj ≤96 min, 120-min hard abort; 155 min은 D0 15+D1 20+등록 120 총 envelope로 단일 cap 아님 — 별도 승인 전까지 미실행
Must-fix (ranked): 없음(동결 차단). 권고: §13.5 문언 정렬 / Adapter import 경로 주의 / RNG·배제 단언 유닛 테스트 착지
v1.0.11 self-contained: 예 — own loop 훈련·평가 계약이 §2 전체로 문서 내 완결, 외부 참조는 §17.1 pinned 7종(helper_commits 고정)+열거 artifact뿐
잘못된 전제: 없음. v1.0.10의 "train_arm training-only 재사용 가능" 전제는 본 버전에서 제거·교정됨("composite helper… must not be reused")
```