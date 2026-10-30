"""Aggregate the saved pilot, verify pairing and plot an exportable operating map."""
import argparse
import gzip
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np


def work_bound(dev):
    """A conservative instantaneous bound on the declared model's nonnegative work.

    Pulses are canonical, q is reset to 1 on entering FAST, and each port carries at
    most one pulse. READY auxiliary input, section drains and both actuator costs
    are all included, even when their maxima cannot occur simultaneously.
    """
    pars = np.array(dev['params'])
    levels = np.array(dev['auxiliary_thresholds'] or [[1., .8, .1]]*3)
    a = math.log(4)
    main = max(a*sum(pars[:, 0]), a, 1.1)
    aux = sum(max(a*p[4], p[1]*v[0], p[2]*v[1], p[3]*v[2]) for p, v in zip(pars, levels))
    actuators = 8*sum(pars[:, 3]*levels[:, 2]) + .5*sum(pars[:, 1]*levels[:, 0])
    return float(main+aux+actuators)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    args = parser.parse_args()
    summary = json.loads((args.results/'summary.json').read_text())
    protocol = json.loads((args.results/'protocol.json').read_text())
    groups = defaultdict(list)
    pairing = defaultdict(set)
    for row in summary['evaluation']:
        condition = row['condition']
        key = condition['family'], condition['dispersion']
        groups[key, row['arm']].append(row)
        pairing[key, row['draw']['seed']].add(row['device_sha256'])
    assert all(len(x) == 1 for x in pairing.values()), 'unpaired devices across arms'
    assert all(len(rows) == len(protocol['evaluation']) for rows in groups.values())
    largest_work_bound = 0.
    run_count = 0
    with gzip.open(args.results/'runs.jsonl.gz', 'rt') as raw:
        for line in raw:
            record = json.loads(line)
            run_count += 1
            for cell in record.get('records', []):
                largest_work_bound = max(largest_work_bound, work_bound(cell['device']))
    assert largest_work_bound < 500, 'energy-gate-open premise needs explicit investigation'
    aggregate = dict(total_runs=run_count, heldout_devices_per_condition=len(protocol['evaluation']),
                     pairing_verified=True, instantaneous_work_upper=largest_work_bound,
                     raw_sha256=hashlib.sha256((args.results/'runs.jsonl.gz').read_bytes()).hexdigest(),
                     rows=[])
    for condition in protocol['conditions']:
        key = condition['family'], condition['dispersion']
        for arm in protocol['arms']:
            rows = groups[key, arm]
            valid = [r for r in rows if r['error'] is None]
            primary = [r['primary'] for r in valid]
            aggregate['rows'].append(dict(condition=condition, arm=arm,
                successful=sum(r['success'] for r in primary), attempted=len(rows),
                conditioned_successful=sum(r['conditioned']['success'] for r in valid),
                simulation_errors=[r['error'] for r in rows if r['error'] is not None],
                missed=sum(r['missed'] for r in primary), extra=sum(r['extra'] for r in primary),
                final_layer_missed=sum(r['final_layer_missed'] for r in primary),
                final_layer_extra=sum(r['final_layer_extra'] for r in primary),
                interval_error_max=max((r['interval_error_max'] for r in primary
                                        if r['interval_error_max'] is not None), default=None),
                missing_interval_pairs=sum(r['missing_interval_pairs'] for r in primary),
                active_port_gain_mean=float(np.mean([r['active_port_gain_mean'] for r in primary])) if primary else None,
                active_port_gain_max=max((r['active_port_gain_max'] for r in primary), default=None),
                future_work_mean=float(np.mean([r['future_work'] for r in primary])) if primary else None))
    (args.results/'aggregate.json').write_text(json.dumps(aggregate, indent=2)+'\n')
    for condition in protocol['conditions']:
        rows = [r for r in aggregate['rows'] if r['condition'] == condition]
        print(condition['family'], condition['dispersion'],
              [(r['arm'], r['successful'], r['conditioned_successful'], r['missed'], r['extra'],
                r['active_port_gain_mean']) for r in rows])
    print('runs', run_count, 'largest instantaneous work bound', largest_work_bound)
    plot(args.results, protocol, aggregate)


def plot(folder, protocol, aggregate):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    values = np.array([[next(r['successful'] for r in aggregate['rows']
                             if r['condition'] == c and r['arm'] == arm)
                        for arm in protocol['arms']] for c in protocol['conditions']])
    conditioned = np.array([[next(r['conditioned_successful'] for r in aggregate['rows']
                                  if r['condition'] == c and r['arm'] == arm)
                             for arm in protocol['arms']] for c in protocol['conditions']])
    names = dict(physical='Paramètres physiques', main_threshold='Seuil principal',
                 kappa='Fuite κ', auxiliary_thresholds='Seuils auxiliaires')
    labels = [f"{names[c['family']]}  ±{c['dispersion']*100:g} %" for c in protocol['conditions']]
    arms = ['Apprentissage R', 'État initial figé', 'Gains initiaux figés\nb apprend', 'Préréglage calibré']
    supplement = folder/'supplement_uniform.json'
    if supplement.exists():
        extra = json.loads(supplement.read_text())['evaluation']
        for criterion, data in [('primary', values), ('conditioned', conditioned)]:
            column = [sum(r[criterion]['success'] for r in extra if r['condition'] == c and r['error'] is None)
                      for c in protocol['conditions']]
            if criterion == 'primary':
                values = np.column_stack((data, column))
            else:
                conditioned = np.column_stack((data, column))
        arms.append('Uniforme 3,2 †')
    cmap = LinearSegmentedColormap.from_list('operating', ['#f0ece6', '#dbc38a', '#26766b'])
    fig, axs = plt.subplots(1, 2, figsize=(15, 7.6), sharey=True)
    for ax, data, title in zip(axs, (values, conditioned),
                               ('Dès la première impulsion à 230', 'Après une impulsion de conditionnement')):
        ax.imshow(data, vmin=0, vmax=4, cmap=cmap, aspect='auto')
        ax.set_title(title, fontsize=11, pad=14)
        ax.set_xticks(range(len(arms)), arms, rotation=24, ha='right', fontsize=9)
        ax.set_yticks(range(len(labels)), labels, fontsize=10)
        ax.tick_params(length=0)
        for n in range(data.shape[0]):
            for j in range(len(arms)):
                ax.text(j, n, f'{data[n,j]}/4', ha='center', va='center',
                        color='white' if data[n,j] >= 3 else '#262522', fontsize=10)
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.suptitle('A22 · Carte exploratoire de transmission', x=.05, ha='left', fontsize=17, fontweight='bold')
    fig.text(.05, .015, 'Dispositifs appariés distincts de la calibration · 28 impulsions d’entraînement · '
             '6 impulsions futures · erreur ≤ 10⁻⁷\nLes fractions décrivent quatre simulations ; '
             'elles ne mesurent ni une tolérance de fabrication ni un taux de réussite en population.\n'
             '† Contrôle exploratoire ajouté après le pilote ; le protocole primaire reste inchangé.', fontsize=9)
    fig.tight_layout(rect=(0, .1, 1, .94))
    fig.savefig(folder/'operating_map.png', dpi=180, bbox_inches='tight')
    fig.savefig(folder/'operating_map.pdf', bbox_inches='tight')
    fig.savefig(folder/'operating_map.svg', bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    main()
