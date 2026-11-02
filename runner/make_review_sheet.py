"""G-DATA 검토 시트 HTML 생성 — 모바일 카드형, localStorage, JSON 내보내기."""
from __future__ import annotations

import json
import os
import random

ROOT = r"C:\code\unigem"
D = os.path.join(ROOT, "data", "external")
OUT = os.path.join(ROOT, "assets", "gdata_review_sheet.html")

HTML = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>G-DATA 1단계 검토</title>
<style>
:root{--bg:#0f1115;--card:#171a21;--fg:#e8eaf0;--mut:#9aa3b2;--acc:#4f8cff;--ok:#37c26a;--bad:#e05555;--line:#262b36}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans KR",sans-serif}
header{position:sticky;top:0;z-index:5;background:rgba(15,17,21,.95);backdrop-filter:blur(8px);padding:12px 14px;border-bottom:1px solid var(--line)}
h1{font-size:16px;margin:0 0 8px}
.bar{height:6px;background:#222838;border-radius:99px;overflow:hidden}
.bar>i{display:block;height:100%;width:0;background:var(--acc);transition:width .2s}
.meta{display:flex;justify-content:space-between;color:var(--mut);font-size:12px;margin-top:6px}
.tabs{display:flex;gap:6px;padding:10px 14px 0}
.tabs button{flex:1;padding:8px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--mut);font-size:13px}
.tabs button.on{color:#fff;border-color:var(--acc);background:#1b2740}
main{padding:12px 14px 96px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;margin:0 0 12px}
.kind{display:inline-block;font-size:11px;padding:2px 8px;border-radius:99px;background:#23304a;color:#9dc0ff;margin-bottom:8px}
.id{color:var(--mut);font-size:11px;margin-left:8px}
.label{color:var(--mut);font-size:12px;margin:10px 0 4px}
.text{white-space:pre-wrap;word-break:break-word;background:#11141b;border:1px solid var(--line);border-radius:10px;padding:10px;max-height:220px;overflow:auto;font-size:14px}
.rate{display:flex;gap:8px;margin-top:10px}
.rate button{flex:1;padding:12px 0;border-radius:10px;border:1px solid var(--line);background:#11141b;color:var(--fg);font-size:14px}
.rate button.sel{background:var(--acc);border-color:var(--acc);color:#fff;font-weight:600}
.rate button.bad.sel{background:var(--bad);border-color:var(--bad)}
.rate button.ok.sel{background:var(--ok);border-color:var(--ok)}
textarea{width:100%;margin-top:8px;background:#11141b;border:1px solid var(--line);border-radius:10px;color:var(--fg);padding:10px;font:inherit;resize:vertical;min-height:44px}
footer{position:fixed;left:0;right:0;bottom:0;background:rgba(15,17,21,.97);border-top:1px solid var(--line);padding:10px 14px;display:flex;gap:8px}
footer button{flex:1;padding:13px;border-radius:12px;border:0;background:var(--acc);color:#fff;font-size:15px;font-weight:600}
footer button.ghost{background:#222838;color:var(--fg)}
.hint{color:var(--mut);font-size:12px;text-align:center;margin:8px 0 0}
</style></head><body>
<header>
  <h1>G-DATA 1단계 검토 <span style="color:var(--mut);font-weight:400;font-size:12px">— 출력이 입력에 비추어 적절한가?</span></h1>
  <div class="bar"><i id="pb"></i></div>
  <div class="meta"><span id="prog">0 / 0</span><span>1=부적합 · 2=보통 · 3=적합</span></div>
</header>
<div class="tabs">
  <button data-f="all" class="on">전체</button><button data-f="F6">F6 교정</button><button data-f="F5">F5 요약</button>
  <button id="unrated">미평가만</button>
</div>
<main id="list"></main>
<footer>
  <button class="ghost" id="reset">초기화</button>
  <button id="export">결과 내보내기 (JSON)</button>
</footer>
<p class="hint">자동 저장됩니다. 완료 후 JSON을 채팅에 올려주세요.</p>
<script>
const ITEMS = __DATA__;
const KEY = "gdata_review_v1";
let state = JSON.parse(localStorage.getItem(KEY) || "{}");
let filter = "all", onlyUnrated = false;
const list = document.getElementById("list");

function save(){ localStorage.setItem(KEY, JSON.stringify(state)); renderProgress(); }
function renderProgress(){
  const done = ITEMS.filter(i => state[i.id] && state[i.id].rating).length;
  document.getElementById("prog").textContent = `${done} / ${ITEMS.length}`;
  document.getElementById("pb").style.width = (100*done/ITEMS.length).toFixed(1) + "%";
}
function visible(){
  return ITEMS.filter(i => (filter==="all"||i.kind===filter) && (!onlyUnrated || !(state[i.id]&&state[i.id].rating)));
}
function render(){
  const items = visible();
  list.innerHTML = "";
  if(!items.length){ list.innerHTML = '<p style="color:#9aa3b2;text-align:center;padding:40px 0">표시할 항목이 없습니다.</p>'; return; }
  for(const it of items){
    const st = state[it.id] || {};
    const card = document.createElement("section");
    card.className = "card";
    card.innerHTML = `
      <span class="kind">${it.kind}</span><span class="id">${it.id}</span>
      <div class="label">입력</div><div class="text">${esc(it.input)}</div>
      <div class="label">출력</div><div class="text">${esc(it.output)}</div>
      <div class="rate">
        <button data-r="1" class="bad ${st.rating==1?'sel':''}">1 부적합</button>
        <button data-r="2" class="${st.rating==2?'sel':''}">2 보통</button>
        <button data-r="3" class="ok ${st.rating==3?'sel':''}">3 적합</button>
      </div>
      <textarea placeholder="메모(선택)">${esc(st.note||"")}</textarea>`;
    card.querySelectorAll(".rate button").forEach(b=>b.onclick=()=>{
      state[it.id] = {rating:Number(b.dataset.r), note: card.querySelector("textarea").value};
      save(); render();
    });
    card.querySelector("textarea").oninput = e => {
      state[it.id] = Object.assign({}, state[it.id], {note:e.target.value}); save();
    };
    list.appendChild(card);
  }
}
function esc(s){ return String(s).replace(/[&<>"]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
document.querySelectorAll(".tabs button[data-f]").forEach(b=>b.onclick=()=>{
  filter=b.dataset.f; document.querySelectorAll(".tabs button[data-f]").forEach(x=>x.classList.toggle("on",x===b)); render();
});
document.getElementById("unrated").onclick = e => { onlyUnrated=!onlyUnrated; e.target.classList.toggle("on",onlyUnrated); render(); };
document.getElementById("reset").onclick = ()=>{ if(confirm("모든 판정을 지울까요?")){ state={}; save(); render(); } };
document.getElementById("export").onclick = ()=>{
  const rows = ITEMS.map(i=>({kind:i.kind,id:i.id,input:i.input,output:i.output,rating:(state[i.id]||{}).rating||null,note:(state[i.id]||{}).note||""}));
  const blob = new Blob([JSON.stringify(rows,null,1)],{type:"application/json"});
  const a = document.createElement("a"); a.href=URL.createObjectURL(blob); a.download="gdata_review.json"; a.click();
};
render(); renderProgress();
</script></body></html>
"""


def main():
    f6 = [json.loads(l) for l in open(os.path.join(D, "f6_pairs.jsonl"), encoding="utf-8")]
    f5 = [json.loads(l) for l in open(os.path.join(D, "f5_pairs.jsonl"), encoding="utf-8")]
    rng = random.Random(0)
    items = []
    for r in rng.sample(f6, 50):
        items.append({"kind": "F6", "id": r["id"], "input": r["correct"], "output": r["error"]})
    for r in rng.sample(f5, 50):
        items.append({"kind": "F5", "id": r["id"], "input": r["passage"][:1500], "output": r["summary"]})
    rng.shuffle(items)
    html = HTML.replace("__DATA__", json.dumps(items, ensure_ascii=False))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(html)
    print("items", len(items), "->", OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
