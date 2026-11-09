import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from runner.c5_pm_labels import (
    l_predicate, l_signal_consensus, signal_tail, m_evaluable,
    m_valid as m_valid_fn, control_status, validity_status, signal_status,
)
from runner.c5_pm_stats import bootstrap_paired_v2

root = Path(__file__).resolve().parents[1]
base = root / 'reports/provenance/C5_b0a'
rep = json.loads((base / 'registered/registered_report.json').read_text())
units = rep['units_data']
seeds = rep['seeds']
common = sorted({x['target_id'] for x in json.loads((base / 'registered/registered_m_records.json').read_text()) if x['arm'] == 'L' and x['seed'] == seeds[0]})

# L/F per-doc, seed-average; require all 3 seeds
l_copy, l_full, f_copy, f_full = [], [], [], []
per_seed_l_copy, per_seed_l_full, per_seed_f_copy, per_seed_f_full = [], [], [], []
for seed in seeds:
    l = units[f'L/{seed}']['final']['per_doc']
    f = units[f'F/{seed}']['final']['per_doc']
    per_seed_l_copy.append(float(np.mean([l[t]['delta_shuffled_copy'] for t in common])))
    per_seed_l_full.append(float(np.mean([l[t]['delta_shuffled_full'] for t in common])))
    per_seed_f_copy.append(float(np.mean([f[t]['delta_shuffled_copy'] for t in common])))
    per_seed_f_full.append(float(np.mean([f[t]['delta_shuffled_full'] for t in common])))
for t in common:
    lc = [units[f'L/{s}']['final']['per_doc'][t]['delta_shuffled_copy'] for s in seeds]
    lf = [units[f'L/{s}']['final']['per_doc'][t]['delta_shuffled_full'] for s in seeds]
    fc = [units[f'F/{s}']['final']['per_doc'][t]['delta_shuffled_copy'] for s in seeds]
    ff = [units[f'F/{s}']['final']['per_doc'][t]['delta_shuffled_full'] for s in seeds]
    l_copy.append(float(np.mean(lc))); l_full.append(float(np.mean(lf)))
    f_copy.append(float(np.mean(fc))); f_full.append(float(np.mean(ff)))
paired_copy = [a - b for a, b in zip(l_copy, f_copy)]
paired_full = [a - b for a, b in zip(l_full, f_full)]
L_COPY = l_predicate(l_copy, per_seed_l_copy, paired_copy, copy=True)
L_FULL = l_predicate(l_full, per_seed_l_full, paired_full, copy=False)
cons = l_signal_consensus(L_COPY['value'], L_FULL['value'])

# n_signal: per seed, valid L copy/full endpoints among common 15
n_by_seed = {}
for s in seeds:
    pd = units[f'L/{s}']['final']['per_doc']
    n_by_seed[str(s)] = sum(1 for t in common if t in pd)
n_signal = min(n_by_seed.values())
tail = signal_tail({t: v for t, v in zip(common, l_copy)})

# M endpoint/key coverage
rows = json.loads((base / 'registered/registered_m_records.json').read_text())
def key(x): return (x['arm'], x['seed'], x['target_id'], x['variant'], x['memory_kind'], x['endpoint'])
keys = [key(x) for x in rows]
endpoint_ok = len(keys) == 1680 and len(set(keys)) == 1680 and all(x['endpoint_ok'] for x in rows) and all((x['copy_tokens'] or 0) >= 5 for x in rows)
cohort_ok = len(common) == 15 and all(sum(1 for x in rows if x['arm'] == 'P' and x['seed'] == s and x['memory_kind'] == 'real' and x['endpoint'] == 'full' and x['variant'] == 'M_POS_MEAN') == 20 for s in seeds)
seed_ok = set(x['seed'] for x in rows) == set(seeds)
replay = {}
for s in seeds:
    for a in ['F', 'L', 'P', 'PA']:
        replay[f'{a}/{s}'] = json.loads((base / 'replay' / f'{a}_{s}.json').read_text())
replay_ok = all(v['replay_ok'] for v in replay.values())

# builder_ok: control entries + tensors finite/nonzero
cm = json.loads((base / 'control_manifest/control_manifest_registered.json').read_text())
builder_ok = True
for unit, e in cm['arms'].items():
    if int(e['contributors'] if not isinstance(e['contributors'], list) else len(e['contributors'])) < 10:
        builder_ok = False
    arm, seed = unit.split('/')
    pos = np.load(base / 'control_manifest' / arm / seed / 'M_POS_MEAN.npz')['tensor']
    if not np.isfinite(pos).all() or float(np.linalg.norm(pos)) <= 0:
        builder_ok = False
    for tid in common if arm in {'F', 'L'} else [x for x in {r['target_id'] for r in rows if r['arm'] == arm and r['seed'] == int(seed)}]:
        p = base / 'control_manifest' / arm / seed / 'M_NORM' / f'{tid}.npz'
        if not p.exists():
            builder_ok = False; continue
        t = np.load(p)['tensor']
        if not np.isfinite(t).all():
            builder_ok = False
M_EVAL = m_evaluable(cohort_ok, endpoint_ok, seed_ok, replay_ok, builder_ok)

# P/PA validity from artifacts
p_units = [units[f'P/{s}'] for s in seeds]
pa_units = [units[f'PA/{s}'] for s in seeds]
p_path = all(u['updates'] == 100 and u['checkpoint'] for u in p_units)
pa_path = all(u['updates'] == 100 and u['checkpoint'] for u in pa_units)
p_valid = bool(p_path and all(sum(1 for x in rows if x['arm'] == 'P' and x['seed'] == s) == 160 for s in seeds))
pa_valid = bool(pa_path and all(sum(1 for x in rows if x['arm'] == 'PA' and x['seed'] == s) == 160 for s in seeds))
p0 = json.loads((base / 'p0_native_sanity.json').read_text())
p0_ok = p0.get('mode') == 'p0_sanity_no_training' and p0.get('test_split_used') is False
freeze = json.loads((root / 'docs/plan_c5_b0a_pm_prereg_v1_0_11_FREEZE.json').read_text())
p1 = json.loads((base / 'p1_usage.json').read_text())
assay_ok = p1.get('p1_used') is False and p1.get('test_split_read') is False
test_split_used = False
validity = validity_status(assay_ok, p0_ok, p_path, pa_path, p_valid, pa_valid, test_split_used)

mp = rep['m_pass']
M_VALID = m_valid_fn(mp['P']['M_PASS_POS'], mp['P']['M_PASS_NORM'], mp['PA']['M_PASS_POS'], mp['PA']['M_PASS_NORM'])
M_PASS_L = rep['m_pass_l']
control = control_status(M_EVAL, p_valid, pa_valid, M_VALID, M_PASS_L)
signal = signal_status(n_signal, cons['l_signal'], cons['copy_only'], cons['full_only'], validity, control)
b0b = bool(validity == 'VALID' and control == 'M_CONTROL_PASS' and signal == 'EXPLORATORY_L_SIGNAL' and M_VALID is True and n_signal >= 15 and tail['tail_driven'] is False)

out = {
    'schema_version': 1,
    'phase': 'C5 Phase 6 P/M',
    'seeds': seeds,
    'cohort': {'common_ids': common, 'n_common': len(common), 'n_signal_by_seed': n_by_seed, 'n_signal': n_signal},
    'L_COPY_SIGNAL': L_COPY,
    'L_FULL_SIGNAL': L_FULL,
    'consensus': cons,
    'tail': tail,
    'm': {
        'endpoint_ok': endpoint_ok, 'cohort_ok': cohort_ok, 'seed_ok': seed_ok,
        'replay_ok': replay_ok, 'builder_ok': builder_ok, 'm_evaluable': M_EVAL,
        'm_valid': M_VALID, 'm_pass_l': M_PASS_L,
    },
    'p_valid': p_valid, 'pa_valid': pa_valid,
    'p_step100_path_ok': p_path, 'pa_step100_path_ok': pa_path,
    'p0_path_ok': p0_ok, 'assay_path_ok': assay_ok, 'test_split_used': test_split_used,
    'validity_status': validity,
    'control_status': control,
    'signal_status': signal,
    'b0_b_candidate_gate': b0b,
    'labels_computed': True,
    'note': 'Pure label computation from registered artifacts; B0-B still requires separate prereg/approval.',
}
d = base / 'labels'; d.mkdir(parents=True, exist_ok=True)
(d / 'labels.json').write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
(d / 'replay_report.json').write_text(json.dumps({'replay': replay, 'all_ok': replay_ok, 'count': len(replay)}, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'L_COPY': L_COPY['value'], 'L_FULL': L_FULL['value'], 'consensus': cons, 'n_signal': n_signal, 'tail_driven': tail['tail_driven'], 'm_evaluable': M_EVAL, 'm_valid': M_VALID, 'validity': validity, 'control': control, 'signal': signal, 'b0b': b0b}, indent=2))
