"""Inclusion control: sampled point-simulated devices must lie inside the certified enclosures.

Usage: python3 controls/inclusion_check.py <campaign dir> <output.json> [--per-kind 4] [--seed 7]

Devices are drawn with the motifs of the falsification studies (controls/point_simulator), scaled
radially to the campaign's epsilon: factor(eps) = 1 + (eps / 0.1) * (factor(0.1) - 1). The
initial states keep the original family (delta = 1e-5, READY or residual ERROR auxiliaries). Each
device is simulated through the 28 training pulses. For every cell, the number of firings before
230 must equal the number of emissions in the campaign payload, and every firing date must lie in
its certified enclosure box.

One device outside an enclosure is a soundness failure of the engine (or of the simulator), and
must be investigated. Passing is evidence, not proof. Needs numpy and scipy (the simulator); the
campaign payloads are read with the standard-library DAG reader of certify/.
"""
import argparse
import json
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'certify'), str(ROOT / 'controls' / 'point_simulator')]
from audit_provenance import DAG  # noqa: E402

KINDS = ['independent_uniform', 'independent_corner', 'homogeneous_corner', 'layer_corner',
         'lane_corner', 'port_role_corner', 'bottleneck']

def positive_count(value):
    count = int(value)
    if count <= 0:
        raise argparse.ArgumentTypeError('must be a positive integer')
    return count


def compare_records(records, boxes, terminal_time):
    """Check the full half-open training interval, including its final half unit."""
    terminal_time = F(terminal_time)
    expected = set(boxes)
    keys = [(rec['layer'], rec['lane']) for rec in records]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError('simulated cells must match every certified cell exactly once')
    bad = []
    for rec in records:
        key = rec['layer'], rec['lane']
        fired = [t for t in rec['result']['outputs'] if F(t) < terminal_time]
        cert = boxes[key]
        if len(fired) != len(cert):
            bad.append(dict(cell=key, reason='count', simulated=len(fired), certified=len(cert)))
            continue
        for n, (t, (lo, hi)) in enumerate(zip(fired, cert)):
            if not lo <= F(t) <= hi:
                bad.append(dict(cell=key, reason='date', emission=n, simulated=t,
                                box=[float(lo), float(hi)]))
    return bad


def certified_boxes(campaign):
    boxes = {}
    for layer in range(1, 19):
        for lane in range(12):
            doc = json.loads((campaign / f'layer_{layer:02d}' / f'cell_{lane:02d}' / 'result.json').read_text())
            d = DAG(doc)
            rows = []
            node = d.ns[d.fields(doc['root'])['outputs']]
            for item in node[1]:
                tn = d.ns[item]
                assert tn[0] == 'time'
                lo, hi = d.affine_bounds(tn[2])
                rows.append((lo + F(tn[3]), hi + F(tn[3])))
            boxes[layer, lane] = rows
    return boxes


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('campaign', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--per-kind', type=positive_count, default=4)
    parser.add_argument('--seed', type=int, default=7)
    args = parser.parse_args()
    import numpy as np
    import campaign as sim
    cfg = json.loads((args.campaign / 'campaign.json').read_text())
    eps = float(cfg['parameters']['epsilon_relative'])
    terminal_time = F(cfg['parameters']['training_calendar']['terminal_time'])
    boxes = certified_boxes(args.campaign)
    results, failures = [], []
    for k, kind in enumerate(KINDS):
        for index in range(args.per_kind):
            case = {'name': f'{kind}_{index:03d}', 'kind': kind, 'index': index,
                    'seed': 900000 + 1000 * args.seed + 100 * k + index, 'epsilon': 0.1,
                    'initial_policy': ['random', 'endpoint_ready', 'endpoint_error', 'endpoint_mixed'][index % 4]}
            devices = sim.make_devices(case)
            nominal = np.array(sim.NOMINAL)
            for row in devices:
                for dev in row:
                    factor = np.array(dev.params) / nominal
                    dev.params = (nominal * (1 + (eps / 0.1) * (factor - 1))).tolist()
            run = sim.run_network(case, devices, checkpoints=False)
            bad = compare_records(run['records'], boxes, terminal_time)
            results.append(dict(case=case['name'], cells_outside=len(bad)))
            failures.extend(dict(case=case['name'], **b) for b in bad)
            print(case['name'], 'OK' if not bad else f'{len(bad)} cells outside', flush=True)
    report = dict(scope='Point-simulation inclusion control; evidence, not proof', epsilon=str(eps),
                  campaign=cfg, devices=len(results), devices_inside=sum(r['cells_outside'] == 0 for r in results),
                  results=results, failures=failures[:200])
    args.output.write_text(json.dumps(report, indent=1) + '\n')
    print(f"{report['devices_inside']}/{report['devices']} devices inside every certified enclosure")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
