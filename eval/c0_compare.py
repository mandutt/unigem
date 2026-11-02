"""C0 보조 — T5Gemma2 실제 토크나이저/config 비교."""
import json
import os

from tokenizers import Tokenizer

EG2 = r"C:\code\unigem\data\models\embeddinggemma-2-f9972ac2\tokenizer.json"
T5 = os.path.expanduser(
    r"~/.cache/huggingface/hub/models--google--t5gemma-2-270m-270m/"
    r"snapshots/7c38f16641f455ef0685b18431faf1b17722d5a1/tokenizer.json")
CFG = os.path.expanduser(
    r"~/.cache/huggingface/hub/models--google--t5gemma-2-270m-270m/"
    r"snapshots/7c38f16641f455ef0685b18431faf1b17722d5a1/config.json")

cfg = json.load(open(CFG, encoding="utf-8"))
print(json.dumps(cfg["decoder"], indent=1)[:800])
a = Tokenizer.from_file(EG2)
b = Tokenizer.from_file(T5)
va, vb = a.get_vocab(), b.get_vocab()
sa, sb = set(va), set(vb)
same = sa & sb
diff = [t for t in same if va[t] != vb[t]]
print("shared", len(same), "same-id", len(same) - len(diff), "diff-id", len(diff))
print("only eg2", len(sa - sb), "only t5", len(sb - sa), "examples", list(sa - sb)[:5], list(sb - sa)[:5])
for s in ["The quick brown fox jumps over the lazy dog.", "서버 eg2-1의 api 버전은 v2.15.0입니다."]:
    ea, eb = a.encode(s), b.encode(s)
    print("eg2", ea.tokens)
    print("t5 ", eb.tokens)
    print("ids equal", ea.ids == eb.ids)
