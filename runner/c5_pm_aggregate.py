import json, hashlib
from pathlib import Path
root = Path(__file__).resolve().parents[1]
base = root / 'reports/provenance/C5_b0a'
seeds = [20261108, 20261109, 20261110]
arms = ['F', 'L', 'P', 'PA']
units = {}
m_all = []
p7_all = {}
for seed in seeds:
    for arm in arms:
        p = base / 'registered' / 'units' / f'{arm}_{seed}.json'
        units[f'{arm}/{seed}'] = json.loads(p.read_text())
        mp = base / 'registered' / f'm_records_{arm}_{seed}.json'
        rows = json.loads(mp.read_text())
        assert len(rows) == (120 if arm in {'F', 'L'} else 160), (arm, seed, len(rows))
        m_all.extend(rows)
        p7p = base / 'phase7_records' / arm / f'{seed}.json'
        p7 = json.loads(p7p.read_text())
        assert len(p7) == 600, (arm, seed, len(p7))
        p7_all[f'{arm}/{seed}'] = {'path': str(p7p.relative_to(root)), 'records': 600}
assert len(m_all) == 1680, len(m_all)
assert len(p7_all) == 12
(base / 'registered' / 'registered_m_records.json').write_text(
    json.dumps(m_all, indent=2) + '\n', encoding='utf-8')

chk = {}
for arm in arms:
    for seed in seeds:
        p = base / 'checkpoints' / arm / f'{seed}.pt'
        chk[f'{arm}/{seed}'] = 'sha256:' + hashlib.sha256(p.read_bytes()).hexdigest()
(base / 'registered_checkpoint_hash.json').write_text(json.dumps(chk, indent=2) + '\n', encoding='utf-8')

wave_max = {}
for seed in seeds:
    wave_max[seed] = max(units[f'{a}/{seed}']['elapsed_s'] for a in arms)
wall_est = sum(wave_max.values())
control_entries = {k: v['control'] for k, v in units.items()}
cm = {
    'version': 1,
    'experiment': 'C5 Phase 6 P/M',
    'status': 'registered_built',
    'seeds': seeds,
    'arms': {},
    'test_split_used': False,
    'p1_used': False,
    'labels_computed': False,
    'not_a_result': False,
}
for k, e in control_entries.items():
    cm['arms'][k] = {
        'path': e['path'], 'M_POS_MEAN_shape': e['M_POS_MEAN_shape'],
        'M_NORM_count': e['M_NORM_count'], 'contributors': e['contributors'],
        'control_digest': e['control_digest'],
    }
(base / 'control_manifest' / 'control_manifest_registered.json').write_text(
    json.dumps(cm, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

out = {
    'schema_version': 1,
    'experiment': 'C5 Phase 6 P/M',
    'mode': 'registered_3seed',
    'complete': True,
    'seeds': seeds,
    'arms': arms,
    'units': 12,
    'updates_per_arm': 100,
    'total_updates': 1200,
    'parallel_units_per_wave': 4,
    'wave_max_elapsed_s': {str(k): v for k, v in wave_max.items()},
    'wall_estimate_s': wall_est,
    'cap_seconds': 7200,
    'cap_ok': wall_est <= 7200,
    'm_records_total': len(m_all),
    'phase7_total': len(p7_all) * 600,
    'm_records_path': 'reports/provenance/C5_b0a/registered/registered_m_records.json',
    'phase7': p7_all,
    'checkpoint_hash': 'reports/provenance/C5_b0a/registered_checkpoint_hash.json',
    'control_manifest': 'reports/provenance/C5_b0a/control_manifest/control_manifest_registered.json',
    'labels_computed': False,
    'decision_labels_computed': False,
    'not_a_result': False,
    'registered_seed_used': True,
    'test_split_used': False,
    'p1_used': False,
    'units_data': units,
    'freeze': json.loads((root / 'docs/plan_c5_b0a_pm_prereg_v1_0_11_FREEZE.json').read_text()),
}
(base / 'registered' / 'registered_report.json').write_text(
    json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({'m': len(m_all), 'p7': len(p7_all) * 600, 'wall_est': wall_est, 'cap_ok': wall_est <= 7200, 'wave_max': wave_max}))
