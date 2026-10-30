"""Post-hoc diagnostic: the pre-existing grid's largest uniform preset on every held-out device.

This is explicitly additional to the frozen primary protocol; it cannot redefine its outcomes.
"""
import argparse
import gzip
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from run import task


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    protocol = json.loads((args.results/'protocol.json').read_text())
    gain = max(protocol['fixed_candidates']['uniform_gains'])
    candidate = dict(name=f'supplement_uniform_{gain:g}', gains=[gain]*3,
                     b=protocol['fixed_candidates']['recovery_b'])
    plan = dict(status='Post-hoc diagnostic specified after the primary pilot; not a primary preregistered result',
                rule='Use the largest uniform gain already present in the frozen candidate grid; no fitting to evaluation outputs',
                candidate=candidate,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (args.results/'supplement_plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    results = []
    jobs = [(c, d, 'calibrated_fixed', candidate, protocol)
            for c in protocol['conditions'] for d in protocol['evaluation']]
    with ProcessPoolExecutor(max_workers=args.workers) as pool, gzip.open(args.results/'supplement_runs.jsonl.gz', 'wt') as raw:
        for future in as_completed([pool.submit(task, j) for j in jobs]):
            result = future.result()
            raw.write(json.dumps(result, separators=(',', ':'), allow_nan=False)+'\n')
            results.append({k: v for k, v in result.items() if k != 'records'})
            print(result['condition'], result['draw']['seed'], result['error'] or result['primary']['success'], flush=True)
    (args.results/'supplement_uniform.json').write_text(json.dumps(dict(plan=plan, evaluation=results), indent=2)+'\n')


if __name__ == '__main__':
    main()
