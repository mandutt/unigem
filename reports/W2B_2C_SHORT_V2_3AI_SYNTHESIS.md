# Wave 2B + 2C-short v2 — 3-AI 검토 종합

- 작성: 2026-11-04
- 라운드: `w2b_2c_short_v2`
- 검토 모델: GLM 5.3 Flash(max), Claude Sonnet 5.5(medium), GPT-6 Luna(xhigh)
- 검토 기준: `e1d6280` (요청서 기준 `1db2d0e` + threads.json)
- 원문:
  - `docs/hoplite/w2b_2c_short_v2/2026-11-04_hoplite-review_w2b_2c_short_v2_GLM.md`
  - `..._SONNET.md`
  - `..._LUNA.md`
- **상태: 3/3 “B — Must-fix 반영 후 pilot”. A(그대로 시작)는 0/3.**

---

## 1. 한눈에 보는 결론

세 모델 모두 **v2 골격은 승인 가능하지만 pilot 즉시 착수는 반대**했다. 공통적으로 다음이 pilot 전에 고쳐져야 한다고 판정했다.

1. **vocab·OOV·reader head 계약의 모순**
2. **B3-nat의 정의 이중성** — 현재 문구로는 sampler 효과를 분리할 수 없다
3. **gate의 후보 선택 편향** — `max(B2,B3)`를 test에서 고르는 방식
4. **B0′/B1 초기화와 online/cached parity의 범위**
5. **test 적격률·0.5초 미만·ID 중복·길이 대표성**
6. **디스크·streaming·LoRA 학습 속도 미실측**

세 모델 모두 **새 P0 holdout 없이 중단(C/D)할 이유는 없다**고 봤다. in-domain sealed holdout 표기를 유지하는 조건이다.

| 항목 | GLM | SONNET | LUNA | 종합 |
|---|---|---|---|---|
| 기본 결론 | B | B | B | **B** |
| vocab/OOV 모순 | 지적 | 지적 | 지적 | **Must-fix** |
| B3-nat 분리 불가 | 지적 | 지적 | 지적 | **Must-fix** |
| gate `max`/최소효과 | 지적 | 지적 | 지적 | **Must-fix** |
| B0′/parity | 지적 | 지적 | 지적 | **Must-fix** |
| test 0.5초/분모 | — | 지적 | 지적 | **Must-fix** |
| 디스크/streaming | 지적 | 지적 | 지적 | **preflight 확장** |
| 일정 5~7일 | 낙관 | 낙관 | 미검증 | **7~10일로 재산정** |

---

## 2. 요청서 자체의 정합 결함(검토 중 실측)

### 2.1 sha256 불일치 — 원인은 CRLF

요청서 §4.4의 `split_candidate.json` sha256 `25eb37f6...d680deb`는 **작업 트리 CRLF 파일의 해시**다. Git에 커밋된 blob은 다음이다.

| 대상 | sha256 |
|---|---|
| 작업 트리(CRLF) | `25eb37f6314072aa9a113b8d6f822ebedb8d6b3a638c42b52de8b7954d680deb` |
| **Git blob** (`5170404`~현재) | **`6805a8de071067502e421c0da96257eaea6ee7b5f2ec6607f51360b885b515f0`** |

GLM이 지적한 `6805...`가 맞다. 데이터 내용(dev 500/test 2,400/spare 90, seed 42)은 동일하며, **줄바꿈 차이**다. v3에서는 Git blob 해시를 정본으로 쓰고, 작업 트리 해시를 병기하거나 `.gitattributes`로 LF를 고정해야 한다.

### 2.2 test 0.5초 미만 28건 — 평가 분모가 줄어든다

`w1_extract.py`는 **0.5초 미만을 제외**한다. 그런데 현재 test 2,400에는 0.5초 미만이 **28건** 있다.

| 세트 | 0.5초 미만 | 0.5초 이하 | 최소 |
|---|---:|---:|---:|
| dev 500 | 2 | 2 | 0.347s |
| **test 2,400** | **28** | **28** | **0.286s** |
| spare 90 | 0 | 0 | 0.589s |

그대로 추출하면 test는 2,400이 아니라 **2,372**가 된다. “test 2,400 1회”와 불일치한다. v3에서 **eval 추출의 최소 길이를 0.28초로 낮추거나**, 28건을 오류로 계산하는 분모 규칙을 사전등록해야 한다. preflight의 CTC 0건은 metadata 기반이므로 실제 feature frame 검사도 필요하다.

### 2.3 test는 eval_other보다 훨씬 짧다

| 세트 | ≤4초 | 0–2초 | 12–16초 |
|---|---:|---:|---:|
| **test 2,400 (eval_clean)** | **74.33%** | 47.96% | **36** |
| eval_other 2,962 | 57.2% | 27.6% | 3.9% |

- GLM/Sonnet/Luna 모두 **“35.14% 기준선을 test에 그대로 이전할 수 없다”**고 지적했다.
- test 12–16초 bin은 36건뿐이라 bin별 결론의 검정력이 낮다.
- test는 **짧은 발화 중심의 in-domain holdout**으로만 해석해야 한다.

### 2.4 test overlap — 일부는 확인됐고 일부는 아직이다

| 비교 | 결과 |
|---|---:|
| test ∩ eval_other | **0** |
| test ∩ Wave 1 train | **0** |
| test ∩ 기존 D-β 100 | **0** |
| test ∩ short 4h | **미생성** |
| test ∩ B3-nat | **미생성** |

preflight는 dev/test/기존 100만 확인했다. short/B3-nat 선별 후 **ID·가능하면 화자 중복 0**을 다시 검사해야 한다. eval_clean에 화자 ID가 없으므로 “화자 중복 0”은 주장할 수 없다.

### 2.5 디스크 수치가 낡았다

- preflight JSON의 `disk_free_gb`는 **null**이다.
- 요청서·검토요청서의 “C: 여유 약 18GB”는 현재 실측과 다르다.
- **2026-11-04 현재 `df -h /c`: 79GB 여유**.
- 실제 feature: `data/wave1/feats` 11GB(그중 `fc.npz` 3.9GB), `feats_dev` 630MB, `feats_kspon_eval_other` 2.6GB.
- 따라서 로컬 디스크는 이전보다 여유가 있지만, **VPS eg2-2 20GB**에서 15GB zip + 10h feature + test feature를 동시에 두는 것은 여전히 불가능하다. VPS는 **audio 선별만** 하고 feature는 로컬에서 만드는 분리가 안전하다.

### 2.6 기타 정합 결함

- plan §5.2의 **“speaker-cluster paired bootstrap”** 잔재 — 화자 ID가 없으므로 **utterance bootstrap**으로 수정해야 한다.
- plan §2.1의 **“1,101자 vocab 밖 문자 클립 제외”**와 §2.5의 **“2B vocab 재구축”**이 상충한다.
- B3-nat이 **“10h natural sampler”**와 **“별도 4h natural”** 두 뜻으로 쓰인다.
- 요청서 §5.7 **5~7일**과 plan §7 **9.5~11.5일**이 모순된다.
- **D-β**가 요청서에서 정의되지 않아 자기완결성이 약하다.
- “eval_clean 60명 화자”는 **화자 ID 부재** 때문에 이 자료만으로 검증되지 않는다.
- 6h train의 출처가 요청서에 명시되지 않았다. 실제 `data/wave1/manifest.jsonl`은 **Zeroth 1,534 + Kconf 850**이며 **Kspon은 0**이다. 따라서 short 4h는 **최초의 Kspon 도메인 데이터**다.

---

## 3. 공통 Must-fix

### MF-1. vocab·OOV·reader head 계약을 하나로 고정

**지적**

- plan §2.1: 1,101자 vocab 밖 문자가 있는 Kspon train 클립은 **제외**.
- plan §2.5/요청서: 2B vocab을 **Kspon train 6h+short에서 새로 build**.
- 2A reader는 1,101자 기준 CTC head를 갖는다. 새 vocab이면 **head 차원·문자 ID·blank index**가 달라져 “reader warm-start”가 성립하지 않는다.
- OOV 클립을 제외하면 Kspon 구어체(밌·껄·쫌·걍 등)가 short 4h에서 빠져 **선택 편향**이 생긴다.

**선택지**

| 안 | 내용 | 장점 | 단점 |
|---|---|---|---|
| **V1** | **2A 1,101자 vocab 유지** | warm-start·비교 완전, 구현 단순 | test OOV 7.7% 행/0.53% 문자, short OOV 제외 |
| **V2** | **6h+short에서 새 vocab**, 2A 행 복사 + 신규 행 초기화 | Kspon coverage 개선 | head remap·신규 행 초기화·B0′ 비교 복잡 |

**권고:** pilot의 비교 가능성을 우선해 **V1(2A vocab 유지)**. 단 short 4h의 OOV 제외율이 **5%를 넘으면** V2를 pilot 전에 채택하고 head remap을 사전등록한다. 어느 쪽이든 **eval/test 문자로 vocab을 확장하지 않는다**.

### MF-2. B3-nat 정의를 하나로 확정

**지적**

- 현재 `B3-nat`은 문헌상 두 가지다.
  - **A**: B3와 **같은 10h 클립**에 natural sampler.
  - **B**: **별도 natural 4h** + natural sampler.
- A면 `B3−B3-nat` = **순수 sampler 효과**.
- B면 `B3−B3-nat` = **클립 구성 + sampler 결합**이며 “sampler 효과”라는 라벨은 거짓이다.
- 세 모델 모두 **A를 권고**했다. B는 별도 4h 선별·디스크·화자 매칭 비용이 추가되고, 화자 ID가 없어 “같은 화자/도메인” 약속도 실행 불가능하다.

**권고:** **B3-nat-A** — B3와 동일한 10h clip ID 집합, natural sampler, 동일 optimizer step/노출량. 이름도 “natural length distribution control”이 아니라 **“fixed short-enriched pool, natural sampler”**로 정확히 표기한다. 원래 Kspon natural 분포가 필요하면 **별도 B3-natB**를 후속 라운드로 둔다.

### MF-3. Gate의 후보 선택과 최소 효과 크기

**지적**

- `max(B2,B3)`가 **CER 최대**인지 **개선량 최대**인지 불명확하다. CER은 낮을수록 좋다.
- test에서 B2/B3 중 큰 쪽을 고르면 **선택 편향**이 CI에 반영되지 않는다.
- full gate에 **절대 pp 최소값**이 없다. 현재는 CI 하한 >0뿐이다.
- pilot의 “절대 1.0%p **또는** 상대 5%+CI” OR 조건은 상대 5%가 더 느슨해질 수 있다.
- plan §5.2의 speaker-cluster bootstrap은 실행 불가.

**권고**

- 개선량을 **Δ = CER(B0′) − CER(candidate)**로 정의(양수=개선).
- **B2/B3 중 primary는 dev 500에서 선택해 freeze**하고, test에서는 그 한 arm만 B0′와 비교한다. 나머지는 탐색적 진단으로 표시한다.
- full 채택: **점추정 Δ ≥ 1.0%p AND paired utterance-bootstrap 95% CI 하한 > 0**.
- pilot: 절대 1.0%p + CI 방향; 미달 시 INCONCLUSIVE. **INCONCLUSIVE는 자동 full이 아니라** 사전 정의한 조건(누출·parity·디스크·시간 상한 통과)에서만 full 고려.
- seed 43은 **경계 결과에서 winner+B0′만** 확장; 그 외에는 seed42 primary.
- FLEURS no-regression은 **CI 상한** 기준; 2A에서 이미 쓴 dev임을 명시.

### MF-4. B0′·B1 초기화와 parity의 범위

**지적**

- “B1 0-step == B0′”는 문구상 **학습된 B0′**와의 일치로 읽힌다. 실제로 성립하는 것은 **공통 초기 상태**의 일치뿐이다.
- B0′가 cached feature, B1/B2가 on-the-fly mel이면 dropout/train mode/SpecAugment/정밀도/패딩이 달라질 수 있다.
- 2A reader warm-start는 2A vocab 기준이다. vocab을 바꾸면 head 호환이 깨진다.
- B0′가 2A 0.20913과 크게 달라졌을 때 “기록 후 진행”은 파이프라인 버그를 수용하는 규칙이다.

**권고**

- “B1 0-step == B0′”를 **“공통 초기화 상태의 고정 배치 logits/CER 일치”**로 재정의하고 허용오차를 사전등록.
- B0′도 **B3와 같은 cached 경로**로 통일.
- parity는 **동일 frozen tower·동일 샘플·동일 전처리**에서 online vs cached feature/logit을 비교. dtype별 허용오차 명시.
- B0′가 2A와 **seed 잡음(약 0.1%p) 이상** 벗어나면 **pilot 중단·원인 조사**.
- 모든 arm의 vocab·문자 ID·blank index·reader 초기화를 고정.

### MF-5. test 적격률·0.5초·split

**지적**

- test 2,400 중 **28건이 0.5초 미만**이라 `w1_extract`에서 조용히 빠진다(2,372).
- preflight CTC 0은 **metadata 기반**이며 실제 feature frame 검사가 아니다.
- test 길이 분포가 eval_other와 다르다(≤4초 74.3% vs 57.2%).
- dev/test는 duration 층화라 같은 화자·세션 인접 발화가 섞일 수 있다.
- test∩eval_other와 test∩Wave1은 0으로 확인했지만, short/B3-nat는 아직이다.

**권고**

- eval extraction의 최소 길이를 0.28초로 낮추거나, 28건을 **오류로 계산하는 분모 규칙**을 사전등록.
- train/dev/test feature 생성 시 `target_len + repeats <= output_frames`를 **실제 feature frame**으로 재검사.
- short/B3-nat 선별 후 test와의 ID 중복 0을 재확인.
- 가능하면 **연속 ID 블록 단위 split**으로 재생성(아직 audio 추출 전). 불가능하면 duration 층화 한계를 명시.
- test 12–16초 bin은 n=36으로 **탐색적**으로만 보고.
- “sealed”는 **절차적 holdout**(라벨·점수를 모델 선택에 쓰지 않음)으로 정의.

### MF-6. 디스크·streaming·일정

**지적**

- VPS 20GB에서 15GB zip + 선별 audio + feature를 동시에 두기 어렵다.
- AI Hub가 range/streaming을 지원하는지 미검증.
- local C:는 현재 79GB 여유로 이전 18GB보다 낫지만, preflight 기록은 null이다.
- LoRA B1/B2의 CPU sec/step은 **전무 실측**이다. 2A 322~356초/20 epoch는 cached reader-only 값이다.
- 요청서 5~7일 vs plan 9.5~11.5일이 모순.

**권고**

- Phase 1 첫 30~60분을 **feasibility spike**로: shard range/throughput, 대표 10파일 추출, duration histogram, peak disk.
- **VPS는 audio 선별만**, feature는 로컬에서 생성하는 분리를 우선. VPS streaming 실패 시 local download fallback.
- fp16 캐시·단계별 peak disk 표·삭제 목록을 사전등록.
- **pilot 첫 시간에 B1 sec/step·RSS를 실측**한 뒤 full 일정 재산정. 그 전에는 **7~10일 + 2일 버퍼**로 표기.
- B1은 채택 gate에 불필요한 귀속 진단이므로 일정 압박 시 **pilot에서 먼저 생략 가능**.
- reader-only B0′/B3/B3-nat를 먼저 돌려 데이터 가설을 확인하고, 그 결과로 LoRA 투자 여부를 결정.

---

## 4. 모델별 이견

| 사안 | GLM | SONNET | LUNA | 종합 |
|---|---|---|---|---|
| vocab | V2(새 vocab, superset) 권고 | **V1(2A 유지)** 우선 | 하나로 freeze | **V1 우선, short OOV>5%면 V2** |
| B3-nat | **A** | **A** (B는 confounded) | **A** | **A** |
| full 최소 Δ | 0.5%p | 1.0%p | 1.0%p | **1.0%p** |
| test split | 유지 가능 | **연속 ID 블록** 권고 | 유지, 누출 검사 | **블록 재생성 검토** |
| 0.5초 | 명시 없음 | 지적 | 실제 CTC 재검사 | **수정 필수** |
| 일정 | plan 모순 지적 | LoRA 속도 미실측 | hard stop 필요 | **7~10일+버퍼** |
| 디스크 | 23GB 추정 | 29GB 추정 | 실측 필요 | **현재 79GB, VPS 분리** |

---

## 5. v3 반영안

| 우선 | 변경 | 담당 문서 |
|---:|---|---|
| P0 | vocab 정책 V1/V2 확정, head remap 규칙 | plan §2.1/§2.5, decisions |
| P0 | B3-nat-A 확정, 이름·귀속 라벨 수정 | plan §1/§3/§6, D-066 |
| P0 | gate: dev primary 선택, Δ 정의, full Δ≥1.0%p | plan §5, gates |
| P0 | B0′/B1 초기화·parity 정의 | plan §3/§4 |
| P0 | test 0.5초 28건 처리, 실제 CTC 재검사 | plan §2/§7, preflight |
| P0 | sha256 Git blob으로 정정, D-β 정의 | 요청서, v3 |
| P1 | short/B3-nat test overlap 검사 | preflight |
| P1 | block split 재생성 검토 | preflight |
| P1 | disk/streaming spike, fp16 정책 | plan §7 |
| P1 | 일정 7~10일+버퍼, B1 조건부 | plan §7 |
| P2 | seed43 경계 규칙, FLEURS CI | gates |
| P2 | `speaker-cluster` 문구를 utterance로 정정 | plan §5.2 |

**pilot 전 금지**

- test 2,400 audio 추출·평가
- vocab 정책 확정 전 short 4h 선별
- B3-nat 정의 확정 전 `b3nat_4h.jsonl` 생성
- 실제 CTC/feature parity/disk spike 전 full 5-arm
- test 점수로 B2/B3/vocab/threshold 선택

---

## 6. 사용자 결정 필요

1. **vocab**: V1(2A 1,101 유지, warm-start 우선) vs V2(6h+short 재구축, coverage 우선)
2. **B3-nat**: A(같은 10h 클립, natural sampler) vs B(별도 natural 4h, domain control)
3. **full gate**: Δ≥1.0%p + CI 하한>0 승인 여부
4. **test split**: 현재 duration 층화 유지 vs 연속 ID 블록 재생성
5. **test 0.5초 28건**: extraction 하한 0.28초 vs 오류 분모
6. **pilot 범위**: reader-only B0′/B3/B3-nat 먼저 vs 5-arm 동시

---

## 7. 검토 비용

| 모델 | 비용 | input | output | runtime |
|---|---:|---:|---:|---:|
| GLM max | $0.107672 | 792,349 | 74,826 | 6.9분 |
| Sonnet medium | $0.644851 | 418,202 | 33,639 | 6.1분 |
| Luna xhigh | $0.074034 | 1,216,183 | 52,594 | 11.1분 |
| **합계** | **$0.826557** | — | — | — |

## 8. 원문·재현

- GLM: `docs/hoplite/w2b_2c_short_v2/2026-11-04_hoplite-review_w2b_2c_short_v2_GLM.md`
- Sonnet: `..._SONNET.md`
- Luna: `..._LUNA.md`
- 검토요청서: `reports/EXTERNAL_REVIEW_W2B_2C_SHORT_V2_2026-11-04.md`
- 설계 v2: `docs/plan_wave2b_2c_short_v2.md`
- Preflight: `reports/W2B_preflight.md`, `reports/provenance/W2B/preflight.json`
- Split: `data/wave2b/preflight/split_candidate.json`
  - Git blob sha256 `6805a8de...b515f0`
  - 작업 트리 CRLF `25eb37f6...d680deb`
