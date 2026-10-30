"""Post-run local direct-ODE checks, using saved parents' spike trains as inputs.

These validate selected cells, not an independent full-network campaign.
"""
import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent/'point_simulator')]
from engine import Device
from ode_reference import simulate_ode
from run import allocation_for, devices_for


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    args = parser.parse_args()
    summary = json.loads((args.results/'summary.json').read_text())
    protocol = json.loads((args.results/'protocol.json').read_text())
    future = [float(protocol['future']['first'])]
    for gap in protocol['future']['gaps']:
        future.append(future[-1]+gap)
    training = [8.*k for k in range(28)]
    selected = set()
    checks = []
    targets = {}
    for row in sorted(summary['evaluation'], key=lambda r: (r['error'] is not None,
                       r['primary']['success'] if r['primary'] is not None else True, r['draw']['seed'])):
        if row['error'] is None:
            key = row['condition']['family'], row['condition']['dispersion'], row['arm']
            targets.setdefault(key, row['draw']['seed'])
    with gzip.open(args.results/'runs.jsonl.gz', 'rt') as raw:
        for line in raw:
            row = json.loads(line)
            if row['stage'] != 'evaluation' or row['arm'] not in ('learning', 'calibrated_fixed'):
                continue
            key = row['condition']['family'], row['condition']['dispersion'], row['arm']
            if key in selected or row['error'] is not None or row['draw']['seed'] != targets[key]:
                continue
            selected.add(key)
            cell = row['primary']['failures'][0]['cell'] if row['primary']['failures'] else [18, 0]
            n, j = cell
            cells = {(r['layer'], r['lane']): r for r in row['records']}
            rec = cells[n, j]
            previous = [training+future]+[[] for _ in range(11)] if n == 1 else [cells[n-1, lane]['outputs'] for lane in range(12)]
            arrivals = [previous[(j+p-1) % 12] for p in range(3)]
            dev = Device(**rec['device'])
            fixed = None
            if row['arm'] == 'calibrated_fixed':
                candidate = next(r['selected'] for r in summary['calibration'] if r['condition'] == row['condition'])
                _, devices = devices_for(row['draw'], row['condition'])
                fixed = allocation_for(devices, candidate)[n-1][j]
            ode = simulate_ode(arrivals, dev, future[-1]+60., mode='a22' if fixed is None else 'fixed', fixed=fixed)
            same_count = len(ode['outputs']) == len(rec['outputs'])
            error = max((abs(a-b) for a, b in zip(ode['outputs'], rec['outputs'])), default=0.) if same_count else None
            gain_error = float(np.max(np.abs(np.array(ode['final_gain'])-rec['final_gain'])))
            b_error = abs(ode['final_b']-rec['final_b'])
            passed = same_count and error < 2e-6 and gain_error < 2e-6 and b_error < 2e-6
            result = dict(condition=row['condition'], arm=row['arm'], draw=row['draw'], cell=cell,
                          outputs_fast=len(rec['outputs']), outputs_ode=len(ode['outputs']),
                          output_time_error_max=error, gain_error_max=gain_error, recovery_error=b_error,
                          passed=passed)
            checks.append(result)
            print(key, cell, 'PASS' if passed else 'FAIL', error, flush=True)
    report = dict(scope='Selected local cells integrated directly, using saved fast-network parent inputs; not a full-network ODE replication',
                  tolerance=2e-6, checks=checks, passed=all(r['passed'] for r in checks))
    (args.results/'ode_crosschecks.json').write_text(json.dumps(report, indent=2)+'\n')
    sys.exit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
