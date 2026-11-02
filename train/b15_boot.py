"""문장 클러스터 부트스트랩 — 두 모델의 F1 차이 CI."""
import argparse
import json
import os

import numpy as np


def f1_at(p, y, thr):
    pred = p >= thr
    tp = np.sum(pred & (y == 1)); fp = np.sum(pred & (y == 0)); fn = np.sum(~pred & (y == 1))
    pr = tp / max(1, tp + fp); rc = tp / max(1, tp + fn)
    return 2 * pr * rc / max(1e-9, pr + rc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--thr_a", type=float, required=True)
    ap.add_argument("--thr_b", type=float, required=True)
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    A, B = np.load(a.a), np.load(a.b)
    assert np.array_equal(A["y"], B["y"]), "labels differ"
    y, sent = A["y"], A["sent"]
    ids = np.unique(sent)
    # 문장별 인덱스 그룹
    groups = {s: np.where(sent == s)[0] for s in ids}
    rng = np.random.default_rng(0)
    deltas = []
    for _ in range(a.n):
        pick = rng.choice(ids, size=len(ids), replace=True)
        idx = np.concatenate([groups[s] for s in pick])
        deltas.append(f1_at(B["p"][idx], y[idx], a.thr_b) - f1_at(A["p"][idx], y[idx], a.thr_a))
    deltas = np.array(deltas)
    res = {"delta_point": float(f1_at(B["p"], y, a.thr_b) - f1_at(A["p"], y, a.thr_a)),
           "mean": float(deltas.mean()), "ci_low": float(np.percentile(deltas, 2.5)),
           "ci_high": float(np.percentile(deltas, 97.5)), "n_boot": a.n,
           "a": os.path.basename(a.a), "b": os.path.basename(a.b)}
    print(json.dumps(res, indent=1))
    if a.out:
        json.dump(res, open(a.out, "w", encoding="utf-8"), indent=2)


if __name__ == "__main__":
    main()
