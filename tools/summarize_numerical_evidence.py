"""Compact summary of the numerical (point-simulation) studies, from their result archives.

Usage: python3 -I tools/summarize_numerical_evidence.py <followup results dir> <output json>

<followup results dir> is the `results/` folder of the follow-up study archive
(fresh cohort at epsilon = 0.1 under the 29-pulse protocol, and the radial
epsilon scans of the 28-pulse protocol). The script reads recorded outputs only;
it does not simulate anything. Training emissions are the outputs before t = 229.5
(the 28 pulses at 0, 8, ..., 216).
"""
import collections, glob, gzip, json, sys
from pathlib import Path

root, out = Path(sys.argv[1]), Path(sys.argv[2])

def training_counts(record_file):
    d = json.load(gzip.open(record_file, 'rt'))
    return d['case'], {(r['layer'], r['lane']): sum(1 for t in r['outputs'] if t < 229.5) for r in d['records']}

# 1. Fresh devices at epsilon = 0.1: cells whose training emission count depends on the device.
per_cell = collections.defaultdict(collections.Counter)
fresh = [f for f in sorted(glob.glob(str(root / 'fresh' / '*.json.gz'))) if not f.endswith('_full.json.gz')]
for f in fresh:
    _, counts = training_counts(f)
    for cell, c in counts.items():
        per_cell[cell][c] += 1
varying = {f'{l},{j}': dict(sorted(v.items())) for (l, j), v in sorted(per_cell.items()) if len(v) > 1}

# 2. Radial epsilon scans (28-pulse protocol): cells whose training count differs from epsilon = 0.
scan = collections.defaultdict(dict)
for f in glob.glob(str(root / 'epsilon' / 'eps_*.json.gz')):
    case, counts = training_counts(f)
    if 'bisect' in case['name']:
        continue
    scan[case['seed_motif']][case['epsilon']] = counts
history_vs_eps = {}
for motif, by_eps in sorted(scan.items()):
    base = by_eps[0.0]
    history_vs_eps[motif] = {f'{e:g}': sum(1 for k in base if by_eps[e][k] != base[k]) for e in sorted(by_eps)}

# 3. Epsilon brackets of the 28-pulse claim (first-interval fidelity and rest at 230).
def brackets(name):
    p = root / name
    if not p.exists():
        return None
    return [{k: x[k] for k in ('seed', 'criterion', 'lo', 'hi') if k in x} for x in json.loads(p.read_text())]

fresh_rows = json.loads((root / 'fresh_summary.json').read_text())
summary = {
    'scope': 'point simulations of the full 18x12 network; numerical evidence, not certificates',
    'fresh_cohort_eps_0.1_protocol_29_pulses': {
        'devices': len(fresh),
        'status_ok': sum(1 for r in fresh_rows if r.get('status') == 'OK'),
        'max_interval_error_after_250': max(r.get('max_interval_error', 0) for r in fresh_rows),
        'cells_with_device_dependent_training_count': len(varying),
        'varying_cells_by_layer': dict(sorted(collections.Counter(int(k.split(',')[0]) for k in varying).items())),
        'max_distinct_counts_in_one_cell': max((len(v) for v in varying.values()), default=0),
        'per_cell_count_histogram': varying,
    },
    'protocol_28_pulses_training_cells_differing_from_nominal_by_eps': history_vs_eps,
    'protocol_28_pulses_fidelity_brackets': brackets('epsilon_brackets.json'),
    'protocol_28_pulses_rest_brackets': brackets('rest_brackets.json'),
}
out.write_text(json.dumps(summary, indent=1) + '\n')
print('wrote', out)
