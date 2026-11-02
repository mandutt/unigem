"""원격에서 두 임베딩 JSON을 비교해 요약만 출력."""
import json
import sys

import numpy as np

a = json.load(open(sys.argv[1]))
b = json.load(open(sys.argv[2]))
A = {r["id"]: np.array(r["v"]) for r in a["rows"]}
B = {r["id"]: np.array(r["v"]) for r in b["rows"]}
cs = []
for k in A:
    x, y = A[k], B[k]
    cs.append(float(x @ y / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-12)))
print(json.dumps({"n": len(cs), "min": min(cs), "mean": sum(cs) / len(cs),
                  "below_0.999": sum(1 for c in cs if c < 0.999)}))
