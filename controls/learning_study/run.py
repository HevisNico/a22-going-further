"""Paired, held-out numerical pilot. Run from the repository root.

    python -B controls/learning_study/run.py --out controls/learning_study/results --workers 4

No certified engine is imported. Protocol, seeds, source hashes and every outcome are saved.
"""
import argparse
import copy
import gzip
import hashlib
import json
import platform
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIM = ROOT / 'controls' / 'point_simulator'
sys.path.insert(0, str(SIM))
import numpy as np
import scipy
import campaign
from engine import K


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def graph():
    previous = [True] + [False]*11
    active, ports = set(), set()
    for n in range(1, 19):
        current = []
        for j in range(12):
            ins = [p for p in range(3) if previous[(j+p-1) % 12]]
            current.append(bool(ins))
            if ins:
                active.add((n, j))
                ports.update((n, j, p) for p in ins)
        previous = current
    return active, ports


ACTIVE, PORTS = graph()


def devices_for(draw, condition):
    case = dict(draw, name=str(draw['seed']), epsilon=condition['physical_epsilon'])
    devices = campaign.make_devices(case)
    rng = np.random.default_rng(draw['seed'] + 910000001)
    shape = (18, 12, 3, 3)
    noise = (rng.choice([-1., 1.], size=shape) if draw['kind'] == 'independent_corner'
             else rng.uniform(-1., 1., size=shape))
    for n, row in enumerate(devices):
        for j, dev in enumerate(row):
            dev.params = (campaign.NOMINAL * (1 + condition['physical_epsilon']/.1
                          * (np.array(dev.params)/campaign.NOMINAL - 1))).tolist()
            width = condition['dispersion']
            if condition['family'] == 'main_threshold':
                dev.main_threshold = 1 + width*noise[n, j, 0, 0]
            elif condition['family'] == 'kappa':
                dev.kappa = K*(1 + width*noise[n, j, 0, 0])
            elif condition['family'] == 'auxiliary_thresholds':
                dev.auxiliary_thresholds = (np.array([1., .8, .1])
                                           * (1 + width*noise[n, j])).tolist()
    return case, devices


def allocation_for(devices, candidate):
    allocation = []
    for n, row in enumerate(devices):
        allocation.append([])
        for j, dev in enumerate(row):
            requested = candidate.get('gains', candidate.get('template'))
            if 'template' in candidate:
                requested = requested[n][j]
            # The same commanded preset for all devices, projected onto each physical cap.
            gains = np.minimum(requested, np.array(dev.params)[:, 0]).tolist()
            allocation[-1].append(dict(g=gains, b=candidate['b']))
    return allocation


def measure(run, tolerance, skip=0):
    future = run['future'][skip:]
    totals = dict(missed=0, extra=0, failing_cells=0, missing_interval_pairs=0,
                  final_layer_missed=0, final_layer_extra=0)
    errors, gains, work, cell_rows = [], [], 0., []
    for rec in run['records']:
        key = rec['layer'], rec['lane']
        expected = int(key in ACTIVE)
        result = rec['result']
        windows = []
        for k, source in enumerate(future):
            end = future[k+1] if k+1 < len(future) else run['end']
            windows.append([t for t in result['outputs'] if source-tolerance <= t < end-tolerance])
        counts = [len(w) for w in windows]
        lost = sum(max(expected-c, 0) for c in counts)
        extra = sum(max(c-expected, 0) for c in counts)
        local_errors = []
        if expected:
            for k in range(len(future)-1):
                if counts[k] == counts[k+1] == 1:
                    local_errors.append(abs((windows[k+1][0]-windows[k][0])
                                            - (future[k+1]-future[k])))
                else:
                    totals['missing_interval_pairs'] += 1
        failure = lost or extra or any(e > tolerance for e in local_errors)
        totals['missed'] += lost
        totals['extra'] += extra
        totals['failing_cells'] += int(bool(failure))
        if rec['layer'] == 18:
            totals['final_layer_missed'] += lost
            totals['final_layer_extra'] += extra
        errors.extend(local_errors)
        at_training_end = result['snapshots']['230.0']
        gains.extend(at_training_end['gain'][p] for p in range(3) if (*key, p) in PORTS)
        work += sum(result['energy']) - sum(at_training_end['energy'])
        if failure:
            cell_rows.append(dict(cell=list(key), counts=counts, missed=lost, extra=extra,
                                  interval_error_max=max(local_errors, default=None)))
    return dict(totals, success=totals['failing_cells'] == 0,
                interval_error_max=max(errors, default=None),
                active_port_gain_mean=float(np.mean(gains)), active_port_gain_sum=float(sum(gains)),
                active_port_gain_max=float(max(gains)), future_work=float(work), failures=cell_rows)


def task(job):
    condition, draw, arm, candidate, protocol = job
    case, devices = devices_for(draw, condition)
    fingerprint = hashlib.sha256(encoded([[d.__dict__ for d in row] for row in devices])).hexdigest()
    mode = {'learning': 'a22', 'initial_frozen': 'fixed',
            'initial_gains_recovery_learning': 'recovery_only', 'calibrated_fixed': 'fixed'}[arm]
    fixed = allocation_for(devices, candidate) if candidate is not None else None
    identity = dict(condition=condition, draw=draw, arm=arm, candidate=candidate and candidate['name'],
                    device_sha256=fingerprint)
    try:
        run = campaign.run_network(case, devices, mode=mode, fixed=fixed,
                                   gaps=protocol['future']['gaps'], first=protocol['future']['first'])
        primary = measure(run, protocol['tolerance'])
        conditioned = measure(run, protocol['tolerance'], skip=1)
        # Keep every device, spike train and training-terminal state for replay and inspection.
        records = [dict(layer=r['layer'], lane=r['lane'], device=r['device'],
                        outputs=r['result']['outputs'], at_230=r['result']['snapshots']['230.0'],
                        final_gain=r['result']['final_gain'], final_b=r['result']['final_b'])
                   for r in run['records']]
        return dict(identity, primary=primary, conditioned=conditioned, records=records,
                    elapsed_seconds=run['elapsed_seconds'], error=None)
    except Exception as exc:
        return dict(identity, error=f'{type(exc).__name__}: {exc}', primary=None, conditioned=None)


def candidates(protocol, learned):
    b = protocol['fixed_candidates']['recovery_b']
    out = [dict(name=f'uniform_{g:g}', gains=[g]*3, b=b)
           for g in protocol['fixed_candidates']['uniform_gains']]
    out += [dict(name='role_'+'_'.join(map(str, g)), gains=g, b=b)
            for g in protocol['fixed_candidates']['port_role_gains']]
    if all(r['error'] is None for r in learned):
        template = np.max([np.array([r['at_230']['gain'] for r in run['records']]).reshape(18, 12, 3)
                           for run in learned], axis=0)
        for multiplier in protocol['fixed_candidates']['learned_template_multipliers']:
            out.append(dict(name=f'template_max_{multiplier:g}',
                            template=(template*multiplier).tolist(), b=b))
    return out


def score(rows):
    valid = [r['primary'] for r in rows if r['error'] is None]
    return (-sum(r['success'] for r in valid),
            (len(rows)-len(valid))*100000 + sum(r['missed']+r['extra'] for r in valid),
            (len(rows)-len(valid))*216 + sum(r['failing_cells'] for r in valid),
            float(np.mean([r['active_port_gain_mean'] for r in valid])) if valid else 1e99)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    path = Path(__file__).with_name('protocol.json')
    protocol = json.loads(path.read_text())
    (args.out/'protocol.json').write_bytes(path.read_bytes())
    sources = [Path(__file__), path, SIM/'engine.py', SIM/'campaign.py', SIM/'ode_reference.py']
    manifest = dict(protocol_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    source_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in sources},
                    python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__)
    (args.out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    summary = dict(manifest=manifest, calibration=[], evaluation=[], diagnostics=[])
    with gzip.open(args.out/'runs.jsonl.gz', 'wt') as raw, ProcessPoolExecutor(max_workers=args.workers) as pool:
        def execute(jobs, stage):
            completed = []
            for future in as_completed([pool.submit(task, j) for j in jobs]):
                result = future.result()
                raw.write(json.dumps(dict(stage=stage, **result), separators=(',', ':'), allow_nan=False)+'\n')
                raw.flush()
                completed.append(result)
            return completed

        for condition in protocol['conditions']:
            name = f"{condition['family']}:{condition['dispersion']:g}"
            print('START', name, flush=True)
            learned = execute([(condition, d, 'learning', None, protocol) for d in protocol['calibration']], 'calibration_learning')
            choices = candidates(protocol, learned)
            calibration = execute([(condition, d, 'calibrated_fixed', c, protocol)
                                   for c in choices for d in protocol['calibration']], 'calibration_fixed')
            selected = min(choices, key=lambda c: score([r for r in calibration if r['candidate'] == c['name']]))
            summary['calibration'].append(dict(condition=condition, selected=selected,
                                               scores={c['name']: score([r for r in calibration if r['candidate'] == c['name']])
                                                       for c in choices}))
            evaluation = execute([(condition, d, arm, selected if arm == 'calibrated_fixed' else None, protocol)
                                  for d in protocol['evaluation'] for arm in protocol['arms']], 'evaluation')
            for result in evaluation:
                summary['evaluation'].append({k: v for k, v in result.items() if k != 'records'})
            # Search the same failing draws at smaller added perturbations, without retuning.
            failures = [r for r in evaluation if r['arm'] == 'learning'
                        and (r['error'] is not None or not r['primary']['success'])]
            if condition['family'] != 'physical' and failures:
                jobs = [(dict(condition, dispersion=width), r['draw'], 'learning', None, protocol)
                        for r in failures for width in (0., condition['dispersion']/2)]
                diagnostics = execute(jobs, 'posthoc_failure_search')
                summary['diagnostics'].extend({k: v for k, v in r.items() if k != 'records'} for r in diagnostics)
            (args.out/'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
            totals = {arm: sum(r['primary']['success'] for r in evaluation
                              if r['arm'] == arm and r['error'] is None) for arm in protocol['arms']}
            print('DONE', name, selected['name'], totals, flush=True)
    print('Saved', args.out, flush=True)


if __name__ == '__main__':
    main()
