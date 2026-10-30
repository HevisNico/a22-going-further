"""Certify one box from a finished campaign directory, and write its committed records.

Usage: python3 -I certify/certify_box.py <campaign dir> <box dir> [--return-bound 19]

<box dir> is for example results/eps3e-3. The script writes:
  <box dir>/campaign/campaign.json, RUN_MANIFEST.json
  <box dir>/terminal/all_layers_audit.json, all_terminal_exact.json, lineage_and_clocks.json,
                     commutation_usage.json, mechanism_usage.json, initial_section.json,
                     future_certificate.json, independent_check.json, invariant_domain_Q28.json,
                     certification_log.json
Each step runs as a separate process, standard library only, and never imports the engine.
The first failing step stops the script; its output is kept in certification_log.json.
The future contract is: source gaps >= 20, global return strictly before --return-bound.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent


def main():
    if not __debug__:
        raise RuntimeError('Run without -O')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('campaign', type=Path)
    parser.add_argument('box', type=Path)
    parser.add_argument('--return-bound', default='19')
    args = parser.parse_args()
    campaign, box = args.campaign.resolve(), args.box.resolve()
    cfg = json.loads((campaign / 'campaign.json').read_text())
    eps = cfg['parameters']['epsilon_relative']
    (box / 'campaign').mkdir(parents=True, exist_ok=True)
    terminal = box / 'terminal'
    terminal.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(campaign / 'campaign.json', box / 'campaign' / 'campaign.json')
    t = terminal
    steps = [
        ('run manifest', ['make_run_manifest.py', campaign, box / 'campaign' / 'RUN_MANIFEST.json']),
        ('terminal extraction', ['extract_terminal.py', campaign, t]),
        ('lineage and clocks', ['audit_lineage.py', campaign, t / 'lineage_and_clocks.json']),
        ('commutations', ['audit_commutations.py', campaign, t / 'commutation_usage.json']),
        ('mechanisms', ['audit_mechanisms.py', campaign, t / 'mechanism_usage.json']),
        ('initial section', ['certify_initial_section.py', t / 'initial_section.json', eps]),
        ('future certificate (directed integers)', ['certify_future.py', t / 'all_terminal_exact.json', t / 'future_certificate.json']),
        ('independent future check (directed decimals)', ['verify_future_general.py', t / 'all_terminal_exact.json',
                                                          t / 'future_certificate.json', t / 'independent_check.json', eps, args.return_bound]),
        ('quiescent domain Q28', ['build_q_domain.py', t / 'all_terminal_exact.json', t / 'future_certificate.json',
                                  t / 'invariant_domain_Q28.json']),
    ]
    log = []
    for name, (script, *rest) in steps:
        out = subprocess.run([sys.executable, '-I', str(TOOLS / script)] + [str(x) for x in rest],
                             capture_output=True, text=True)
        log.append(dict(step=name, exit_code=out.returncode, output=(out.stdout + out.stderr)[-4000:]))
        print(f'[{"PASS" if out.returncode == 0 else "FAIL"}] {name}', flush=True)
        if out.returncode:
            break
    (t / 'certification_log.json').write_text(json.dumps(dict(campaign=cfg, return_bound=args.return_bound, steps=log), indent=1) + '\n')
    failed = [x for x in log if x['exit_code']]
    print(f'\n{len(log) - len(failed)} PASS, {len(failed)} FAIL' + ('' if len(log) == len(steps) else ' (stopped)'))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
