"""Registered 3-seed unit driver for C5 Phase 6.

Usage:
  python -m runner.c5_pm_registered --arm F --seed 20261108 --threads 2

This is the committed reproducer for the registered unit artifacts. It does
not aggregate the 12 units; use runner/c5_pm_aggregate.py for that.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner.c5_pm_phase6 import ARMS, REGISTERED_SEEDS, run_registered_unit  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=ARMS)
    ap.add_argument("--seed", required=True, type=int, choices=REGISTERED_SEEDS)
    ap.add_argument("--threads", type=int, default=2)
    args = ap.parse_args()
    torch.set_num_threads(args.threads)
    out = run_registered_unit(args.arm, args.seed)
    print(json.dumps({"arm": args.arm, "seed": args.seed, "m_records": out["m_records"], "phase7_records": out["phase7_records"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
