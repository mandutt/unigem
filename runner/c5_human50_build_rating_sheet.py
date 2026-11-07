#!/usr/bin/env python3
"""Build the D-085 primary human-50 rating sheet.

The HTML is deliberately blind: it contains no arm names, checkpoint steps,
model metrics, or target summaries. Each document's four summaries are shown
as A-D in the frozen manifest arm order. The export contains only `slot`
(0-3); a separate converter maps slot to arm using the frozen manifest.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data/external/f5_pairs_v3_clean.jsonl"
MANIFEST = ROOT / "reports/provenance/C5_human50/manifest.json"
PILOT = ROOT / "reports/provenance/C5_a1/pilot300_val161/predictions.jsonl"
RUN = ROOT / "reports/provenance/C5_a1/full_2ep"
OUT = ROOT / "reports/C5_human50_primary_rating_sheet.html"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sample = [x["id"] for x in manifest["targeted"] + manifest["random"]]
    data = {str(r["id"]): r for r in load_jsonl(CLEAN) if str(r["id"]) in set(sample)}
    preds = {
        "pilot300": {str(r["id"]): str(r.get("pred") or "") for r in load_jsonl(PILOT)},
        "1293": {str(r["id"]): str(r.get("pred") or "") for r in load_jsonl(RUN / "eval_step_1293/eval.jsonl")},
        "1940": {str(r["id"]): str(r.get("pred") or "") for r in load_jsonl(RUN / "eval_step_1940/eval.jsonl")},
        "2586": {str(r["id"]): str(r.get("pred") or "") for r in load_jsonl(RUN / "eval_step_2586/eval.jsonl")},
    }
    for rid in sample:
        if rid not in data:
            raise SystemExit(f"missing clean row: {rid}")
        for arm, rows in preds.items():
            if rid not in rows:
                raise SystemExit(f"missing {arm} prediction: {rid}")
            if not rows[rid].strip():
                raise SystemExit(f"empty {arm} prediction: {rid}")

    # The manifest order already defines A-D. Do not emit arm names.
    sessions = []
    for sid, ids in manifest["sessions"]["primary"].items():
        docs = []
        for rid in ids:
            arm_order = next(x["arm_order"] for x in manifest["targeted"] + manifest["random"] if x["id"] == rid)
            summaries = [
                {"label": chr(ord("A") + i), "text": preds[arm][rid]}
                for i, arm in enumerate(arm_order)
            ]
            docs.append({
                "id": rid,
                "source": str(data[rid]["passage"]),
                "summaries": summaries,
            })
        sessions.append({"id": int(sid), "docs": docs})

    payload = {
        "protocol": "D-085 human50 single-rater v1.0.0",
        "total_docs": len(sample),
        "total_ratings": len(sample) * 4,
        "sessions": sessions,
    }
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = TEMPLATE.replace("__DATA_JSON__", data_json)
    OUT.write_text(html, encoding="utf-8")
    print(json.dumps({
        "out": str(OUT),
        "docs": len(sample),
        "sessions": len(sessions),
        "ratings": len(sample) * 4,
        "bytes": OUT.stat().st_size,
    }, ensure_ascii=False, indent=2))
    return 0


TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>C5 Human 50 — Primary Rating</title>
<style>
:root {
  --bg: #0f141a;
  --panel: #171e26;
  --panel2: #1d2731;
  --line: #2c3a47;
  --text: #e8eef4;
  --muted: #93a4b4;
  --accent: #5ec2b7;
  --accent2: #f0b45a;
  --danger: #e06c75;
  --ok: #7ec699;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font-family: system-ui, -apple-system, "Segoe UI", "Malgun Gothic", sans-serif;
  font-size: 15px; line-height: 1.55;
}
header {
  position: sticky; top: 0; z-index: 10; background: rgba(15,20,26,.96);
  border-bottom: 1px solid var(--line); padding: 14px 20px;
  display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: space-between;
}
h1 { font-size: 18px; margin: 0; letter-spacing: -.01em; }
.sub { color: var(--muted); font-size: 12px; margin-top: 3px; }
.wrap { max-width: 1180px; margin: 0 auto; padding: 18px 18px 80px; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 16px; margin-bottom: 16px; }
.card h2 { font-size: 14px; margin: 0 0 8px; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: .06em; }
.source {
  white-space: pre-wrap; font-size: 13px; color: #cbd8e3; max-height: 300px; overflow: auto;
  background: #111820; border: 1px solid #24313d; border-radius: 8px; padding: 12px;
}
.summary-card { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 14px; margin-bottom: 14px; }
.summary-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 8px; }
.badge { display: inline-flex; min-width: 30px; height: 30px; align-items: center; justify-content: center; border-radius: 8px; background: #22313d; color: var(--accent); font-weight: 700; }
.summary-text { white-space: pre-wrap; font-size: 14px; color: #dbe6ef; background: #111820; border: 1px solid #24313d; border-radius: 8px; padding: 12px; max-height: 230px; overflow: auto; }
.rating-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 18px; margin-top: 12px; }
.field label { display: block; color: var(--muted); font-size: 12px; margin-bottom: 5px; }
.score-group { display: flex; gap: 5px; flex-wrap: wrap; }
.score { border: 1px solid var(--line); background: #111820; color: var(--text); border-radius: 7px; padding: 7px 11px; cursor: pointer; font-size: 13px; }
.score:hover { border-color: var(--accent); }
.score.active { background: var(--accent); color: #071014; border-color: var(--accent); font-weight: 700; }
select, input[type="text"] { width: 100%; background: #111820; color: var(--text); border: 1px solid var(--line); border-radius: 7px; padding: 7px 9px; font-size: 13px; }
select:focus, input:focus, .score:focus { outline: 2px solid var(--accent); outline-offset: 1px; }
.notes { margin-top: 10px; }
.footer {
  position: fixed; left: 0; right: 0; bottom: 0; background: rgba(15,20,26,.97);
  border-top: 1px solid var(--line); padding: 10px 18px; z-index: 12;
}
.footer-inner { max-width: 1180px; margin: 0 auto; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between; }
.progress { flex: 1 1 260px; min-width: 190px; }
.bar { height: 7px; background: #24313d; border-radius: 99px; overflow: hidden; }
.bar > div { height: 100%; width: 0; background: var(--accent); transition: width .2s; }
.progress-text { font-size: 12px; color: var(--muted); margin-top: 4px; }
button.action { background: #24313d; color: var(--text); border: 1px solid var(--line); border-radius: 8px; padding: 8px 12px; cursor: pointer; font-size: 13px; }
button.action:hover { border-color: var(--accent); }
button.primary { background: var(--accent); color: #071014; border-color: var(--accent); font-weight: 700; }
button:disabled { opacity: .45; cursor: not-allowed; }
.session-row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 14px; }
.session-row select { width: auto; min-width: 150px; }
.hint { color: var(--muted); font-size: 12px; }
.warn { color: var(--accent2); }
.ok { color: var(--ok); }
.danger { color: var(--danger); }
@media (max-width: 760px) {
  .rating-grid { grid-template-columns: 1fr; }
  header { padding: 11px 14px; }
  .wrap { padding: 14px 12px 90px; }
  .footer { padding: 8px 12px; }
}
</style>
</head>
<body>
<header>
  <div>
    <h1>C5 Human 50 — Primary Rating</h1>
    <div class="sub">Single-rater · blind A–D · 200 ratings · 50 docs × 4 summaries</div>
  </div>
  <div class="sub" id="saveStatus">자동 저장 준비</div>
</header>

<div class="wrap">
  <div class="card">
    <h2>평가 안내</h2>
    <div class="hint">
      요약 A–D는 무작위 순서이며 모델·체크포인트 정보는 표시되지 않습니다. 각 요약을 독립적으로 읽고
      <b>adequacy</b>를 고른 뒤, 해당되는 경우에만 flags를 “있음”으로 바꾸세요.
      fluency와 utility는 필수입니다. 모든 항목은 자동 저장됩니다.
    </div>
    <div class="hint" style="margin-top:8px">
      adequacy: 4=핵심 거의 전부 보존 · 3=핵심 보존/경미한 손실 · 2=일부 보존/중요 생략 · 1=대부분 손실 · 0=요약 불가
    </div>
  </div>

  <div class="session-row">
    <label class="hint" for="sessionSelect">세션</label>
    <select id="sessionSelect"></select>
    <span class="hint" id="docPosition"></span>
    <span class="hint" id="docProgress"></span>
  </div>

  <div class="card">
    <h2>원문</h2>
    <div class="source" id="source"></div>
  </div>

  <div id="summaries"></div>
</div>

<div class="footer">
  <div class="footer-inner">
    <div class="progress">
      <div class="bar"><div id="progressBar"></div></div>
      <div class="progress-text" id="progressText"></div>
    </div>
    <div style="display:flex; gap:8px; flex-wrap:wrap;">
      <button class="action" id="prevBtn">← 이전</button>
      <button class="action primary" id="nextBtn">저장 후 다음 →</button>
      <button class="action" id="exportBtn">JSONL 내보내기</button>
    </div>
  </div>
</div>

<script>
const DATA = __DATA_JSON__;
const STORAGE_KEY = "d085_primary_v1";
const DEFAULT_RATING = {
  adequacy: null,
  critical_unsupported: 0,
  critical_omission: 0,
  wrong_unit_qualifier: 0,
  entity_relation: 0,
  fluency: null,
  utility: null,
  notes: ""
};

let state = loadState();

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const s = JSON.parse(raw);
      if (s && s.ratings && s.session) return s;
    }
  } catch (e) {}
  return { session: DATA.sessions[0].id, index: 0, ratings: {} };
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  const el = document.getElementById("saveStatus");
  if (el) el.textContent = "저장됨 " + new Date().toLocaleTimeString();
}

function currentSession() {
  return DATA.sessions.find(s => s.id === Number(state.session)) || DATA.sessions[0];
}

function currentDoc() {
  const s = currentSession();
  if (state.index < 0) state.index = 0;
  if (state.index >= s.docs.length) state.index = s.docs.length - 1;
  return s.docs[state.index];
}

function ratingFor(docId, slot) {
  if (!state.ratings[docId]) state.ratings[docId] = {};
  if (!state.ratings[docId][slot]) state.ratings[docId][slot] = {...DEFAULT_RATING};
  return {...DEFAULT_RATING, ...state.ratings[docId][slot]};
}

function setField(docId, slot, field, value) {
  const r = ratingFor(docId, slot);
  r[field] = value;
  state.ratings[docId][slot] = r;
  saveState();
  renderProgress();
}

function isSummaryComplete(r) {
  return Number.isInteger(r.adequacy) && r.adequacy >= 0 && r.adequacy <= 4
    && Number.isInteger(r.fluency) && r.fluency >= 1 && r.fluency <= 5
    && Number.isInteger(r.utility) && r.utility >= 1 && r.utility <= 5;
}

function countComplete() {
  let n = 0;
  for (const s of DATA.sessions) {
    for (const d of s.docs) {
      for (let slot = 0; slot < 4; slot++) {
        if (isSummaryComplete(ratingFor(d.id, slot))) n++;
      }
    }
  }
  return n;
}

function renderProgress() {
  const total = DATA.total_ratings;
  const done = countComplete();
  const pct = total ? (100 * done / total) : 0;
  document.getElementById("progressBar").style.width = pct.toFixed(1) + "%";
  document.getElementById("progressText").textContent = done + " / " + total + " ratings 완료";
  const d = currentDoc();
  let docDone = 0;
  for (let slot = 0; slot < 4; slot++) if (isSummaryComplete(ratingFor(d.id, slot))) docDone++;
  document.getElementById("docProgress").textContent = "현재 문서: " + docDone + "/4 완료";
  document.getElementById("exportBtn").disabled = done !== total;
}

function makeScoreGroup(docId, slot, field, max) {
  const wrap = document.createElement("div");
  wrap.className = "score-group";
  for (let v = 0; v <= max; v++) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "score";
    b.textContent = String(v);
    b.setAttribute("data-value", String(v));
    if (ratingFor(docId, slot)[field] === v) b.classList.add("active");
    b.addEventListener("click", () => {
      setField(docId, slot, field, v);
      for (const x of wrap.querySelectorAll(".score")) x.classList.remove("active");
      b.classList.add("active");
    });
    wrap.appendChild(b);
  }
  return wrap;
}

function makeSelect(docId, slot, field, options) {
  const sel = document.createElement("select");
  for (const [value, label] of options) {
    const o = document.createElement("option");
    o.value = value;
    o.textContent = label;
    sel.appendChild(o);
  }
  const cur = ratingFor(docId, slot)[field];
  sel.value = cur === null ? "" : String(cur);
  sel.addEventListener("change", () => {
    const v = sel.value === "" ? null : Number(sel.value);
    setField(docId, slot, field, v);
  });
  return sel;
}

function render() {
  const s = currentSession();
  state.session = s.id;
  const sel = document.getElementById("sessionSelect");
  if (!sel.options.length) {
    for (const sess of DATA.sessions) {
      const o = document.createElement("option");
      o.value = String(sess.id);
      o.textContent = "세션 " + sess.id + " (" + sess.docs.length + "문서)";
      sel.appendChild(o);
    }
    sel.addEventListener("change", () => {
      state.session = Number(sel.value);
      state.index = 0;
      saveState();
      render();
    });
  }
  sel.value = String(s.id);

  const d = currentDoc();
  document.getElementById("docPosition").textContent = "문서 " + (state.index + 1) + " / " + s.docs.length;
  document.getElementById("source").textContent = d.source;

  const host = document.getElementById("summaries");
  host.textContent = "";
  d.summaries.forEach((summary, slot) => {
    const card = document.createElement("section");
    card.className = "summary-card";

    const head = document.createElement("div");
    head.className = "summary-head";
    const badge = document.createElement("span");
    badge.className = "badge";
    badge.textContent = summary.label;
    const hint = document.createElement("span");
    hint.className = "hint";
    hint.textContent = "독립적으로 평가";
    head.appendChild(badge);
    head.appendChild(hint);
    card.appendChild(head);

    const text = document.createElement("div");
    text.className = "summary-text";
    text.textContent = summary.text;
    card.appendChild(text);

    const grid = document.createElement("div");
    grid.className = "rating-grid";

    const adequacy = document.createElement("div");
    adequacy.className = "field";
    adequacy.innerHTML = "<label>Adequacy (0–4)</label>";
    adequacy.appendChild(makeScoreGroup(d.id, slot, "adequacy", 4));
    grid.appendChild(adequacy);

    const flags = [
      ["critical_unsupported", "Critical unsupported"],
      ["critical_omission", "Critical omission"],
      ["wrong_unit_qualifier", "Wrong unit/qualifier"],
      ["entity_relation", "Entity/relation error"]
    ];
    for (const [field, label] of flags) {
      const f = document.createElement("div");
      f.className = "field";
      const l = document.createElement("label");
      l.textContent = label;
      f.appendChild(l);
      f.appendChild(makeSelect(d.id, slot, field, [["0", "없음"], ["1", "있음"]]));
      grid.appendChild(f);
    }

    const fluency = document.createElement("div");
    fluency.className = "field";
    const fl = document.createElement("label");
    fl.textContent = "Fluency (1–5)";
    fluency.appendChild(fl);
    fluency.appendChild(makeSelect(d.id, slot, "fluency", [["", "선택"], ["1", "1"], ["2", "2"], ["3", "3"], ["4", "4"], ["5", "5"]]));
    grid.appendChild(fluency);

    const utility = document.createElement("div");
    utility.className = "field";
    const ul = document.createElement("label");
    ul.textContent = "Utility (1–5)";
    utility.appendChild(ul);
    utility.appendChild(makeSelect(d.id, slot, "utility", [["", "선택"], ["1", "1"], ["2", "2"], ["3", "3"], ["4", "4"], ["5", "5"]]));
    grid.appendChild(utility);

    card.appendChild(grid);

    const notes = document.createElement("div");
    notes.className = "field notes";
    const nl = document.createElement("label");
    nl.textContent = "Notes (선택)";
    notes.appendChild(nl);
    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = "선택 사항";
    input.value = ratingFor(d.id, slot).notes || "";
    input.addEventListener("input", () => setField(d.id, slot, "notes", input.value));
    notes.appendChild(input);
    card.appendChild(notes);

    host.appendChild(card);
  });

  document.getElementById("prevBtn").disabled = state.index <= 0 && s.id === DATA.sessions[0].id;
  document.getElementById("nextBtn").disabled = state.index >= s.docs.length - 1 && s.id === DATA.sessions[DATA.sessions.length - 1].id;
  renderProgress();
}

function goNext() {
  const s = currentSession();
  if (state.index < s.docs.length - 1) {
    state.index++;
  } else {
    const idx = DATA.sessions.findIndex(x => x.id === s.id);
    if (idx < DATA.sessions.length - 1) {
      state.session = DATA.sessions[idx + 1].id;
      state.index = 0;
    }
  }
  saveState();
  render();
}

function goPrev() {
  const s = currentSession();
  if (state.index > 0) {
    state.index--;
  } else {
    const idx = DATA.sessions.findIndex(x => x.id === s.id);
    if (idx > 0) {
      state.session = DATA.sessions[idx - 1].id;
      state.index = DATA.sessions[idx - 1].docs.length - 1;
    }
  }
  saveState();
  render();
}

function firstIncomplete() {
  for (const s of DATA.sessions) {
    for (let i = 0; i < s.docs.length; i++) {
      for (let slot = 0; slot < 4; slot++) {
        if (!isSummaryComplete(ratingFor(s.docs[i].id, slot))) {
          return {session: s.id, index: i, doc: s.docs[i].id, slot};
        }
      }
    }
  }
  return null;
}

function exportJsonl() {
  const missing = firstIncomplete();
  if (missing) {
    alert("아직 완료되지 않은 rating이 있습니다. 첫 미완료 문서로 이동합니다.");
    state.session = missing.session;
    state.index = missing.index;
    saveState();
    render();
    return;
  }
  const lines = [];
  for (const s of DATA.sessions) {
    for (const d of s.docs) {
      for (let slot = 0; slot < 4; slot++) {
        const r = ratingFor(d.id, slot);
        lines.push(JSON.stringify({
          version: "D085-primary-v1",
          rater_id: "rater-1",
          doc_id: d.id,
          slot: slot,
          pass: 1,
          session: s.id,
          adequacy: r.adequacy,
          critical_unsupported: r.critical_unsupported,
          critical_omission: r.critical_omission,
          wrong_unit_qualifier: r.wrong_unit_qualifier,
          entity_relation: r.entity_relation,
          fluency: r.fluency,
          utility: r.utility,
          notes: r.notes || ""
        }));
      }
    }
  }
  const blob = new Blob([lines.join("\n") + "\n"], {type: "application/x-ndjson;charset=utf-8"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "c5_human50_primary_ratings.jsonl";
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

document.getElementById("nextBtn").addEventListener("click", goNext);
document.getElementById("prevBtn").addEventListener("click", goPrev);
document.getElementById("exportBtn").addEventListener("click", exportJsonl);

render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    raise SystemExit(main())
