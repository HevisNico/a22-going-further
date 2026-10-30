"""Read-only census of every recorded proof mechanism of a campaign directory.

For each of the 216 cells: checks the payload against its receipt, then counts the
guards recorded in width_profile.relative_order_proofs (lemma E and E2 commutations,
charge-join envelopes, restored READY memories, relative first crossings, local
recovery cycles, ...), the recovery branch groups, the largest number of distinct
actuation and deposit histories, and the number of history-fork leaves (Fix F).
Fix T and Fix T' only change how a root is enclosed and record nothing.

It summarizes what the campaign used, so that every mechanism actually used has a
written proof obligation. It does not prove any of them. No engine import.
Usage: python3 -I audit_mechanisms.py <campaign dir> <output.json>
"""
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_provenance import DAG, canonical, dump, sha


def main(root, dest):
    if not __debug__:
        raise RuntimeError('Run without -O')
    root, dest = Path(root), Path(dest)
    cfg = json.loads((root / 'campaign.json').read_text())
    guards, routes = Counter(), Counter()
    cells = []
    for layer in range(1, 19):
        for lane in range(12):
            folder = root / f'layer_{layer:02d}' / f'cell_{lane:02d}'
            receipt = json.loads((folder / 'receipt.json').read_bytes())
            raw = (folder / 'result.json').read_bytes()
            assert sha(raw) == receipt['payload_sha256'], (layer, lane)
            doc = json.loads(raw)
            assert sha(canonical(doc)) == receipt['check']['typed_content_sha256'], (layer, lane)
            d = DAG(doc)
            state = d.fields(d.fields(doc['root'])['state'])
            profile = d.fields(state['width_profile'])
            proofs = d.simple(profile['relative_order_proofs'])
            counts = Counter(p.get('guard') for p in proofs)
            for p in proofs:
                if p.get('guard') == 'fire_arrival_commutation':
                    routes[p.get('route') or 'E'] += 1
            guards.update(counts)
            row = dict(layer=layer, lane=lane, guards=dict(sorted(counts.items())),
                       recovery_branch_groups=len(d.simple(profile['recovery_branch_groups'])),
                       max_actuation_histories=d.simple(profile['maximum_distinct_actuation_histories']),
                       max_deposit_histories=d.simple(profile['maximum_distinct_deposit_histories']))
            if 'history_fork_leaves' in state:
                row['history_fork_leaves'] = d.simple(state['history_fork_leaves'])
            cells.append(row)
            del d, doc, raw
    forks = [c for c in cells if c.get('history_fork_leaves')]
    report = dict(
        scope='Census of recorded mechanisms; payloads checked against receipts; no engine import; not a proof',
        campaign=cfg, cells_checked=len(cells),
        guards=dict(sorted(guards.items())), commutation_routes=dict(sorted(routes.items())),
        recovery_branch_groups=sum(c['recovery_branch_groups'] for c in cells),
        max_actuation_histories=max(c['max_actuation_histories'] for c in cells),
        max_deposit_histories=max(c['max_deposit_histories'] for c in cells),
        history_fork_cells=[dict(layer=c['layer'], lane=c['lane'], leaves=c['history_fork_leaves']) for c in forks],
        not_recorded=['Fix T (READY fire root relative to an admitted pulse)',
                      "Fix T' (recovery return relative to the latest mark)"],
        cells=cells)
    dump(dest, report)
    print(json.dumps({k: report[k] for k in ('cells_checked', 'guards', 'commutation_routes',
                                             'recovery_branch_groups', 'max_actuation_histories',
                                             'max_deposit_histories')}))


if __name__ == '__main__':
    main(*sys.argv[1:3])
