import argparse, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
from runner.c5_pm_phase6 import (
    ARMS, CACHE, CHECKPOINTS, build_arm, native_cache_for, labels_and_copy,
    donors_for, donor_map, build_controls, m_records_for, phase7_records_for,
    load_frozen_inputs, load_layer_cache, assert_cache_lengths,
)

ap = argparse.ArgumentParser()
ap.add_argument('--arm', required=True, choices=ARMS)
ap.add_argument('--seed', type=int, required=True)
ap.add_argument('--threads', type=int, default=2)
args = ap.parse_args()
torch.set_num_threads(args.threads)
started = time.time()
base = Path(r'C:\code\unigem\reports\provenance\C5_b0a')
inputs = load_frozen_inputs(); pre = inputs['preflight']; rows = inputs['rows']
train_ids = inputs['train_ids']; val_ids = inputs['val_ids']
cache = load_layer_cache('train', CACHE); cache.update(load_layer_cache('val', CACHE))
assert_cache_lengths(cache, pre)
built = build_arm(args.arm, args.seed)
p = torch.load(CHECKPOINTS / args.arm / f'{args.seed}.pt', map_location='cpu', weights_only=False)
if built['adapter'] is not None:
    built['adapter'].load_state_dict(p['adapter'])
for name, param in built['model'].named_parameters():
    if name in p['lora']:
        param.data.copy_(p['lora'][name])
native = native_cache_for(built['model'], built['tok'], rows, train_ids + val_ids)
labels, copies = labels_and_copy(built['tok'], rows, val_ids)
donors = donors_for(val_ids, cache) if args.arm in {'F', 'L'} else donor_map({r: int(native[r].shape[0]) for r in val_ids}, val_ids)
targets = list(pre['common_ids']) if args.arm in {'F', 'L'} else val_ids
controls = build_controls(built, train_ids, targets, cache, native)
m = m_records_for(built, targets, controls, labels, copies, args.seed)
p7 = phase7_records_for(built, list(pre['common_ids']), controls, cache, native, labels, copies, donors, args.seed)

def key_m(x): return (x['target_id'], x['variant'], x['memory_kind'], x['endpoint'])
def key_p(x): return (x['target_id'], x['variant'], x['memory_kind'], x['endpoint'], x['donor_id'])
stored_m = json.loads((base / 'registered' / f'm_records_{args.arm}_{args.seed}.json').read_text())
stored_p = json.loads((base / 'phase7_records' / args.arm / f'{args.seed}.json').read_text())
dm = {key_m(x): x for x in m}; sm = {key_m(x): x for x in stored_m}
dp = {key_p(x): x for x in p7}; sp = {key_p(x): x for x in stored_p}
assert set(dm) == set(sm), (args.arm, args.seed, 'm keys')
assert set(dp) == set(sp), (args.arm, args.seed, 'p7 keys')

def close(a, b):
    if a is None or b is None: return a is b
    return abs(a - b) <= 1e-5 + 1e-4 * abs(b)
m_ok = all(close(dm[k]['ce'], sm[k]['ce']) for k in dm)
p_ok = all(close(dp[k]['ce'], sp[k]['ce']) and close(dp[k]['baseline_ce'], sp[k]['baseline_ce']) and close(dp[k]['delta'], sp[k]['delta']) for k in dp)
out = {
    'arm': args.arm, 'seed': args.seed, 'm_records': len(m), 'phase7_records': len(p7),
    'm_keys_ok': set(dm) == set(sm), 'p7_keys_ok': set(dp) == set(sp),
    'm_numeric_ok': m_ok, 'phase7_numeric_ok': p_ok,
    'replay_ok': bool(m_ok and p_ok),
    'atol': 1e-5, 'rtol': 1e-4, 'elapsed_s': time.time() - started,
}
d = base / 'replay'; d.mkdir(parents=True, exist_ok=True)
(d / f'{args.arm}_{args.seed}.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
print(json.dumps(out))
