#!/usr/bin/env python3
"""Build a blinded human review sheet for F5.0 checkpoint comparison.

20 documents x 3 systems = 60 summaries. No API calls, no model generation.
"""
from __future__ import annotations

import html
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
PER_DOC = ROOT / "reports/provenance/C5_f5_0/val161_per_doc.jsonl"
STRATA = ROOT / "reports/provenance/C5_f5_0/val161_review_strata.json"
OUT = ROOT / "reports"
PROV = ROOT / "reports/provenance/C5_f5_0"

SYSTEMS = {
    "pilot300": ROOT / "reports/provenance/C5_a1/pilot300_val161/predictions.jsonl",
    "full_1940": ROOT / "reports/provenance/C5_a1/full_2ep/eval_step_1940/eval.jsonl",
    "full_2586": ROOT / "reports/provenance/C5_a1/full_2ep/eval_step_2586/eval.jsonl",
}
CODES = ["A", "B", "C"]
SEED = 20261110


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pick_unique(priority: list[str], selected: list[str], n: int) -> None:
    for rid in priority:
        if rid not in selected and len(selected) < n:
            selected.append(rid)


def main() -> int:
    data = {str(r["id"]): r for r in read_jsonl(DATA)}
    per_doc = {str(r["id"]): r for r in read_jsonl(PER_DOC)}
    strata = json.loads(STRATA.read_text(encoding="utf-8"))
    preds = {name: {str(r["id"]): r for r in read_jsonl(path)} for name, path in SYSTEMS.items()}

    selected: list[str] = []
    pick_unique(strata["highest_copy8"], selected, 5)
    pick_unique(strata["lowest_slot_preservation"], selected, 9)
    pick_unique(strata["highest_repetition"], selected, 13)
    pick_unique(strata["lowest_char_f1"], selected, 16)
    pick_unique(strata["middle_char_f1"], selected, 20)
    # Fill deterministically if strata overlap left fewer than 20.
    for rid in sorted(per_doc):
        if len(selected) >= 20:
            break
        if rid not in selected:
            selected.append(rid)
    selected = selected[:20]

    rng = random.Random(SEED)
    items = []
    for idx, rid in enumerate(selected, 1):
        doc_key = f"D{idx:02d}"
        mapping = CODES[:]
        rng.shuffle(mapping)
        by_code = {code: system for code, system in zip(mapping, SYSTEMS)}
        labels = []
        for flag in per_doc[rid]["flags"]:
            labels.append(flag)
        items.append(
            {
                "doc_key": doc_key,
                "id": rid,
                "strata_flags": labels,
                "source": data[rid]["passage"],
                "summaries": {code: preds[system][rid]["pred"] for code, system in by_code.items()},
                "mapping": by_code,
            }
        )

    sample = {
        "seed": SEED,
        "n_docs": len(items),
        "n_summaries": len(items) * 3,
        "systems": list(SYSTEMS),
        "items": [
            {"doc_key": x["doc_key"], "id": x["id"], "strata_flags": x["strata_flags"]}
            for x in items
        ],
    }
    key = {
        "seed": SEED,
        "systems": list(SYSTEMS),
        "items": [
            {"doc_key": x["doc_key"], "id": x["id"], "mapping": x["mapping"]}
            for x in items
        ],
    }

    cards = []
    for x in items:
        summaries = []
        for code in CODES:
            text = html.escape(x["summaries"][code])
            summaries.append(
                f"""
                <section class="summary" data-doc="{x['doc_key']}" data-code="{code}">
                  <h3>요약 {code}</h3>
                  <div class="pred">{text}</div>
                  <div class="rating-grid">
                    <fieldset>
                      <legend>Overall</legend>
                      <label><input type="radio" name="overall_{x['doc_key']}_{code}" value="1"> 1</label>
                      <label><input type="radio" name="overall_{x['doc_key']}_{code}" value="2"> 2</label>
                      <label><input type="radio" name="overall_{x['doc_key']}_{code}" value="3"> 3</label>
                    </fieldset>
                    <fieldset>
                      <legend>Abstractness</legend>
                      <label><input type="radio" name="abstract_{x['doc_key']}_{code}" value="1"> 1</label>
                      <label><input type="radio" name="abstract_{x['doc_key']}_{code}" value="2"> 2</label>
                      <label><input type="radio" name="abstract_{x['doc_key']}_{code}" value="3"> 3</label>
                    </fieldset>
                    <fieldset>
                      <legend>Factual preservation</legend>
                      <label><input type="radio" name="factual_{x['doc_key']}_{code}" value="1"> 1</label>
                      <label><input type="radio" name="factual_{x['doc_key']}_{code}" value="2"> 2</label>
                      <label><input type="radio" name="factual_{x['doc_key']}_{code}" value="3"> 3</label>
                    </fieldset>
                  </div>
                  <div class="flags">
                    <label><input type="checkbox" name="flag_{x['doc_key']}_{code}" value="copy_heavy"> copy heavy</label>
                    <label><input type="checkbox" name="flag_{x['doc_key']}_{code}" value="key_omission"> key omission</label>
                    <label><input type="checkbox" name="flag_{x['doc_key']}_{code}" value="unsupported_fact"> unsupported fact</label>
                    <label><input type="checkbox" name="flag_{x['doc_key']}_{code}" value="repetition"> repetition</label>
                  </div>
                  <textarea name="note_{x['doc_key']}_{code}" rows="2" placeholder="선택 메모"></textarea>
                </section>
                """
            )
        cards.append(
            f"""
            <article class="doc" id="{x['doc_key']}">
              <h2>{x['doc_key']} <span class="hint">문서 내 A/B/C 순서는 무작위</span></h2>
              <details>
                <summary>원문 보기</summary>
                <div class="source">{html.escape(x['source'])}</div>
              </details>
              <div class="summaries">{''.join(summaries)}</div>
            </article>
            """
        )

    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>C5 F5.0 Human Review</title>
<style>
  :root {{ --fg:#111; --muted:#555; --line:#ccc; --bg:#fff; --soft:#f5f5f5; --accent:#1e5aa8; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; padding:24px 32px 80px; background:var(--bg); color:var(--fg);
          font:15px/1.6 system-ui, -apple-system, "Segoe UI", "Malgun Gothic", sans-serif; }}
  h1 {{ font-size:24px; margin:0 0 8px; }}
  h2 {{ font-size:19px; margin:0 0 12px; border-bottom:1px solid var(--line); padding-bottom:8px; }}
  h3 {{ font-size:15px; margin:0 0 8px; color:var(--accent); }}
  .top {{ max-width:1100px; margin:0 auto 24px; }}
  .hint {{ font-size:12px; color:var(--muted); font-weight:400; }}
  .doc {{ max-width:1100px; margin:0 auto 28px; padding:18px; border:1px solid var(--line); border-radius:8px; }}
  .source {{ white-space:pre-wrap; background:var(--soft); padding:12px; border-radius:6px; font-size:13px; max-height:260px; overflow:auto; }}
  .summaries {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:12px; margin-top:14px; }}
  .summary {{ border:1px solid var(--line); border-radius:6px; padding:12px; }}
  .pred {{ white-space:pre-wrap; min-height:140px; max-height:260px; overflow:auto; font-size:13px; background:#fafafa; padding:8px; border-radius:4px; }}
  .rating-grid {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }}
  fieldset {{ border:1px solid var(--line); border-radius:4px; padding:4px 8px; margin:0; }}
  legend {{ font-size:12px; color:var(--muted); padding:0 4px; }}
  fieldset label {{ margin-right:8px; font-size:13px; }}
  .flags {{ margin-top:8px; font-size:12px; }}
  .flags label {{ margin-right:10px; }}
  textarea {{ width:100%; margin-top:8px; font:13px/1.4 inherit; }}
  .bar {{ position:sticky; top:0; z-index:10; background:rgba(255,255,255,.96); border-bottom:1px solid var(--line);
          padding:10px 0; margin:0 0 18px; display:flex; gap:12px; align-items:center; flex-wrap:wrap; }}
  .bar input[type=text] {{ padding:6px 8px; border:1px solid var(--line); border-radius:4px; width:160px; }}
  button {{ padding:7px 12px; border:1px solid var(--accent); background:var(--accent); color:#fff;
            border-radius:4px; cursor:pointer; font:14px inherit; }}
  button.secondary {{ background:#fff; color:var(--accent); }}
  #progress {{ font-weight:600; }}
  .warn {{ color:#8a3b00; font-size:13px; }}
  @media (max-width:900px) {{ .summaries {{ grid-template-columns:1fr; }} body {{ padding:16px; }} }}
</style>
</head>
<body>
<div class="top">
  <h1>C5 F5.0 — Human Review</h1>
  <p>20개 문서 × 3개 요약 = <b>60개</b>를 평가합니다. 각 문서의 A/B/C는 <b>무작위</b>이며 시스템 이름은 숨겨져 있습니다.
  target summary는 표시하지 않습니다. 원문만 기준으로 평가하세요.</p>
  <p class="warn">이 파일은 P0 공개 뉴스만 포함합니다. test 163은 포함하지 않습니다.</p>
  <details>
    <summary><b>평가 기준 보기</b></summary>
    <p><b>Overall</b>: 3=추상 요약으로 사용 가능, 2=부분 사용 가능, 1=사용 어려움.</p>
    <p><b>Abstractness</b>: 3=원문을 재구성한 추상 요약, 2=추출/추상 혼합, 1=거의 그대로 복사.</p>
    <p><b>Factual preservation</b>: 3=핵심 사실 정확, 2=일부 누락/약화, 1=핵심 누락/왜곡/무근거.</p>
    <p><b>Flags</b>: copy heavy / key omission / unsupported fact / repetition.</p>
  </details>
</div>
<div class="bar">
  <label>Rater <input id="rater" type="text" value="mandu"></label>
  <span id="progress">0 / 60 rated</span>
  <button onclick="saveNow()">저장</button>
  <button class="secondary" onclick="exportJSON()">JSON 내보내기</button>
  <button class="secondary" onclick="resetAll()">초기화</button>
  <span id="status" class="hint"></span>
</div>
{''.join(cards)}
<script>
const STORAGE_KEY = 'c5_f5_0_human_ratings_v1';
const TOTAL = 60;
function summaryNodes() {{ return Array.from(document.querySelectorAll('.summary')); }}
function collect() {{
  const ratings = summaryNodes().map(el => {{
    const doc = el.dataset.doc, code = el.dataset.code;
    const val = (prefix) => {{
      const x = document.querySelector(`input[name="${{prefix}}_${{doc}}_${{code}}"]:checked`);
      return x ? Number(x.value) : null;
    }};
    const flags = Array.from(document.querySelectorAll(`input[name="flag_${{doc}}_${{code}}"]:checked`)).map(x => x.value);
    const note = document.querySelector(`textarea[name="note_${{doc}}_${{code}}"]`);
    return {{ doc_key: doc, system_code: code, overall: val('overall'), abstractness: val('abstract'), factual: val('factual'),
             flags: flags, note: note ? note.value : '' }};
  }});
  return {{ rater: document.getElementById('rater').value, completed: ratings.filter(r => r.overall !== null).length,
           total: TOTAL, ratings: ratings }};
}}
function updateProgress() {{
  const c = collect();
  document.getElementById('progress').textContent = `${{c.completed}} / ${{TOTAL}} rated`;
}}
function saveNow() {{
  const data = collect();
  try {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(data)); document.getElementById('status').textContent = '저장됨'; }}
  catch (e) {{ document.getElementById('status').textContent = 'localStorage 저장 불가 — JSON으로 내보내세요'; }}
  updateProgress();
}}
function restore() {{
  try {{
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);
    if (data.rater) document.getElementById('rater').value = data.rater;
    for (const r of data.ratings || []) {{
      const setRadio = (prefix, value) => {{
        if (value === null) return;
        const x = document.querySelector(`input[name="${{prefix}}_${{r.doc_key}}_${{r.system_code}}"][value="${{value}}"]`);
        if (x) x.checked = true;
      }};
      setRadio('overall', r.overall); setRadio('abstract', r.abstractness); setRadio('factual', r.factual);
      for (const f of r.flags || []) {{
        const x = document.querySelector(`input[name="flag_${{r.doc_key}}_${{r.system_code}}"][value="${{f}}"]`);
        if (x) x.checked = true;
      }}
      const n = document.querySelector(`textarea[name="note_${{r.doc_key}}_${{r.system_code}}"]`);
      if (n && r.note) n.value = r.note;
    }}
    updateProgress();
  }} catch (e) {{}}
}}
function exportJSON() {{
  const data = collect();
  if (data.completed < TOTAL) {{
    if (!confirm(`아직 ${{data.completed}} / ${{TOTAL}}개만 평가했습니다. 그래도 내보낼까요?`)) return;
  }}
  data.exported_at = new Date().toISOString();
  const blob = new Blob([JSON.stringify(data, null, 2)], {{ type: 'application/json' }});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'f5_human_ratings.json';
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(a.href);
}}
function resetAll() {{
  if (!confirm('모든 평가를 지울까요?')) return;
  localStorage.removeItem(STORAGE_KEY);
  location.reload();
}}
document.addEventListener('change', saveNow);
document.addEventListener('input', () => {{ if (event.target.tagName === 'TEXTAREA') saveNow(); }});
restore();
updateProgress();
</script>
</body>
</html>
"""

    OUT.mkdir(parents=True, exist_ok=True)
    PROV.mkdir(parents=True, exist_ok=True)
    (OUT / "C5_F5_0_human_review.html").write_text(html_doc, encoding="utf-8")
    (PROV / "human_review_sample.json").write_text(json.dumps(sample, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PROV / "human_review_key.json").write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"docs": len(items), "summaries": len(items) * 3, "html": str((OUT / "C5_F5_0_human_review.html").relative_to(ROOT)), "sample": str((PROV / "human_review_sample.json").relative_to(ROOT)), "key": str((PROV / "human_review_key.json").relative_to(ROOT))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
