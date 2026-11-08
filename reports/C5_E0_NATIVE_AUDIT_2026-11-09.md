# C5 E0 — native tokenizer / wiring audit

- 날짜: 2026-11-09
- 범위: **E0 only**. 학습·최적화·generation 없음. test 163 미사용.
- 목적: 3-AI review에서 지적된 ① tokenizer provenance, ② mT5 encoder/external-memory wiring, ③ decoder LoRA attach 가능성을 실제 코드·cache로 확인한다.
- 기준 데이터: `data/external/f5_pairs_v3_clean.jsonl`, `reports/provenance/C5_clean/splits.json`, first **300 train / 100 val** (seed 42 split).
- 결과: **tokenizer content는 일치**, **wiring PASS**, **B0 LoRA runner는 아직 BLOCKED**.

---

## 1. Tokenizer audit

### 1.1 대상

| 항목 | 값 |
|---|---|
| legacy tokenizer | `data/models/t5gemma-2-270m-270m` |
| native tokenizer | `data/models/embeddinggemma-2-f9972ac2` |
| class | 둘 다 `GemmaTokenizer` |
| vocab size | 둘 다 **262,144** |
| prompt | `summarize: ` |
| max length | 1,024 |

`tokenizer.json` SHA256은 서로 다르다.

```text
legacy  4c76318660cc87c3029535cc1596717df67132d231ce4ecf088ba2a8ec07c098
native  4d777ef5bdc1aa36227abdfb77c3e49e7b9c892d16e1b6bda41c393504828be4
```

### 1.2 300 train + 100 val 결과

JSON: `reports/provenance/C5_e0/native_tokenizer_audit.json`

| 지표 | 결과 |
|---|---:|
| 문서 수 | **400** |
| full ID sequence 완전 일치 | **0 / 400** |
| **content ID sequence 일치** | **400 / 400** |
| content token mismatch | **0** |
| character-level ID mismatch | **0 / 498,455 chars** |
| digit-span mismatch | **0 / 12,538 digits** |
| native sequence length − legacy | **+1 (모든 문서)** |
| native EOS 있음 | **400 / 400** |
| legacy EOS 있음 | **0 / 400** |
| truncation | **0 / 400** both |

### 1.3 해석

- 이번 데이터에서는 **T5Gemma2 tokenizer와 EG2 native tokenizer의 content token ID가 동일**했다.
- 차이는 **native가 EOS를 추가**하는 것 하나였다. special token config와 tokenizer.json은 다르지만, 300/100 문서의 일반 token·숫자·문자 offset에는 불일치가 없었다.
- 따라서 3-AI review의 “unknown tokenizer mismatch가 PLE를 오염시킨다”는 우려는 **content ID 기준으로는 지지되지 않는다**.
- 그러나 **EOS 추가는 hidden state를 바꾼다**. native cache를 쓰는 이유는 남아 있다.

### 1.4 legacy vs native layer19 hidden 비교

JSON: `reports/provenance/C5_e0/legacy_native_hidden_diff.json`

| split | docs | token pairs | cosine mean | cosine p01 | cosine min | < .99 | < .95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 300 | 229,987 | **.99135** | .9275 | .7209 | 52,647 (22.9%) | 5,743 (2.5%) |
| val | 100 | 76,636 | **.99150** | .9292 | .6262 | 17,165 (22.4%) | 1,825 (2.4%) |

- EOS 하나가 추가되어도 **약 2.4% token은 cosine < .95**로 달라진다.
- **native cache는 “ID 불일치 수정”보다 “EOS/sequence semantics 보존”을 위해 필요**하다.
- Stage A legacy cache는 **content screening artifact**로 유지할 수 있지만, B0/B1은 native cache를 사용해야 한다.

---

## 2. Native layer19 cache

경로: `data/wave2c/eg2_native_layer19/layer19`

| 항목 | 값 |
|---|---|
| model | `data/models/embeddinggemma-2-f9972ac2` |
| tokenizer | native EG2 `GemmaTokenizer` |
| layer | 19, transformer, 512d |
| splits | train 300 / val 100 |
| max length | 1,024 |
| cache size | **401 MB** |
| elapsed | **386.9 s** |
| test used | **false** |
| files | 6 train shards + 2 val shards + meta |

`meta.json`에 `tokenizer_path`, `tokenizer_class`, `test_split_used: false`를 기록했다.
기존 `data/wave2c/eg2_layer19`는 **legacy cache로 보존**했고 덮어쓰지 않았다.

---

## 3. mT5 wiring audit

JSON: `reports/provenance/C5_e0/wiring_audit.json`

### 3.1 native encoder vs external `encoder_outputs`

단일 P0 train 문서, mT5 native tokenizer, source 256 tokens, target 64 tokens.

| 항목 | 값 |
|---|---:|
| normal loss | 12.603192329406738 |
| external loss | 12.603192329406738 |
| loss abs delta | **0.0** |
| logits max abs delta | **0.0** |
| allclose atol 1e-5 | **true** |
| finite | **true** |
| encoder hidden shape | `[1, 256, 512]` |

→ mT5 encoder를 직접 통과한 경로와 `encoder_outputs=BaseModelOutput(...)` 경로가 **완전히 일치**했다.

### 3.2 native EG2 memory를 external memory로 주입

첫 train shard의 native layer19 `[50, 1024, 512]`에서 첫 문서를 사용.

| 항목 | 값 |
|---|---:|
| h shape | `[50, 1024, 512]` |
| h dtype | float16 |
| lengths | 707~875 |
| finite | **true** |
| dim 512 | **true** |
| external memory loss | 24.79705810546875 |
| finite | **true** |
| logits shape | `[1, 64, 250112]` |

→ **shape/wiring은 정상**이다. 이 loss는 품질 판정이 아니며, adapter/LoRA 없이 native memory를 그대로 넣은 진단값이다.

### 3.3 Decoder LoRA module inventory

| 항목 | 값 |
|---|---:|
| decoder linear modules | 88 |
| `q` | 16 |
| `k` | 16 |
| `v` | 16 |
| `o` | 16 |
| **q/k/v/o total** | **64** |
| legacy `q_proj/k_proj/v_proj/o_proj` matches | **0** |

예시 module name:

```text
decoder.block.0.layer.0.SelfAttention.q
decoder.block.0.layer.0.SelfAttention.k
decoder.block.0.layer.0.SelfAttention.v
decoder.block.0.layer.0.SelfAttention.o
decoder.block.0.layer.1.EncDecAttention.q
decoder.block.0.layer.1.EncDecAttention.k
decoder.block.0.layer.1.EncDecAttention.v
decoder.block.0.layer.1.EncDecAttention.o
```

→ 기존 `c5_b1d_b2.py`의 `TARGETS = ("q_proj", "k_proj", "v_proj", "o_proj")`와 `model.decoder.` prefix를 mT5에 그대로 쓰면 **0 modules**다.
→ mT5 LoRA runner는 `decoder.block.*.{SelfAttention,EncDecAttention}.{q,k,v,o}`를 대상으로 해야 하며, **64 modules assert**가 필요하다.

---

## 4. 판정

| 항목 | 판정 |
|---|---|
| tokenizer content IDs | **PASS** — 400/400 content 일치, mismatch 0 |
| tokenizer special/EOS | **DIFFERENCE** — native만 EOS 추가 |
| native cache | **CREATED** — layer19, 300/100, 512d |
| mT5 native/external wiring | **PASS** — loss/logits delta 0 |
| native EG2 memory shape | **PASS** — `[T, 512]`, finite |
| decoder LoRA attach inventory | **BLOCKED** — mT5 runner 미구현, legacy target 0 |
| B0 readiness | **NOT READY** — LoRA runner + B0 preregistration 필요 |

### 핵심 정정

> **3-AI review의 “tokenizer ID mismatch” 우려는 content token 기준으로는 재현되지 않았다.**  
> 실제 차이는 **native EOS 1 token**이며, 이것이 layer19 hidden의 약 2.4% token을 cosine < .95로 바꾼다.  
> 따라서 **native cache는 계속 사용**하되, Stage A cache를 “wrong tokenizer로 오염된 cache”라고 부르면 안 된다.

---

## 5. 다음 단계

1. **mT5 decoder LoRA runner 구현**
   - `decoder.block.*.{SelfAttention,EncDecAttention}.{q,k,v,o}` 대상
   - attach 64 modules assert
   - zero-output LoRA가 frozen forward와 일치하는지 test
   - adapter/LoRA parameter group, dropout, seed, step budget 기록

2. **B0 사전등록서 작성**
   - native layer19 cache
   - frozen adapter-only vs adapter+LoRA
   - native encoder positive control
   - memory-free/mean-memory negative control
   - primary `Δshuffled_copy`, length-matched donors, docs×seeds bootstrap
   - inconclusive branch; underpowered hard STOP 금지

3. **B0 실행은 별도 승인 후**
   - E0에서는 학습을 실행하지 않았다.
   - Stage B1/B2/Stage C는 B0 이후 새 decision이다.

---

## 6. 재현 명령

```bash
cd C:/code/unigem

# tokenizer audit
.venv/Scripts/python.exe runner/c5_e0_native_audit.py

# native layer19 cache
.venv/Scripts/python.exe runner/c5_eg2_all_layers_cache.py \
  --tokenizer-path data/models/embeddinggemma-2-f9972ac2 \
  --layers 19 --train-limit 300 --val-limit 100 --max-length 1024 \
  --out-root data/wave2c/eg2_native_layer19 --out-prefix layer

# legacy vs native hidden difference
.venv/Scripts/python.exe runner/c5_e0_cache_diff.py

# mT5 wiring / LoRA inventory
.venv/Scripts/python.exe runner/c5_e0_wiring_audit.py
```

---

## 7. 산출물

| 경로 | 내용 |
|---|---|
| `reports/provenance/C5_e0/native_tokenizer_audit.json` | 400문서 tokenizer 비교 |
| `reports/provenance/C5_e0/legacy_native_hidden_diff.json` | layer19 hidden cosine 비교 |
| `reports/provenance/C5_e0/wiring_audit.json` | mT5 encoder/external/LoRA inventory |
| `data/wave2c/eg2_native_layer19/layer19/` | native layer19 cache, 401MB |
| `runner/c5_e0_native_audit.py` | tokenizer audit |
| `runner/c5_e0_cache_diff.py` | legacy/native cache 비교 |
| `runner/c5_e0_wiring_audit.py` | wiring/LoRA inventory |
| `runner/c5_eg2_all_layers_cache.py` | `--tokenizer-path` 지원 추가 |

**test split used: false.**

---

## 8. Post-E0 update — B0 runner smoke (D-114, 2026-11-09)

E0 직후 `runner/c5_mt5_lora_b0.py`를 구현하고 **학습 없이 smoke**만 수행했다.

- mT5 decoder q/k/v/o **64/64 modules attach**
- LoRA **458,752** params, adapter **526,336** params
- zero-output LoRA가 frozen forward를 정확히 재현:
  - loss **27.43998146057129** both
  - loss/logits delta **0.0**
  - allclose true, finite
- train/val ablation 경로는 구현됐으나 **실행하지 않음**
- generation/native positive/memory-free/mean/multiple donor/bootstrap은 아직 미구현
- **B0 학습은 미승인·미실행**

상세: `reports/C5_B0_LORA_RUNNER_SMOKE_2026-11-09.md`, `reports/provenance/C5_b0/mt5_lora_smoke.json`.
