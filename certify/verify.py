"""One command for every check of one certified box.

    python3 -I certify/verify.py --box results/eps3e-3                 # from the committed records
    python3 -I certify/verify.py --box results/eps3e-3 <campaign dir>  # also re-extract everything
                                               # from the full outputs (release asset of that box)
    python3 -I certify/verify.py --box results/eps3e-3 [<campaign dir>] --engine <engine dir>
        # also check that the as-run engine (release asset, with its native binaries) has the
        # sources of the box's engine directory (named in <box>/campaign/ENGINE, e.g.
        # engine_eps3e-3/) and recompute the archived kernel_id using the recorded environment.
        # This is a static file check: it does not import or execute the archived engine.
    python3 -I certify/verify.py --box ... [<campaign dir>] --engine <engine dir> --check-runtime
        # additionally load the engine and require the actual Python, numpy, scipy and native
        # backend to match the recorded environment, including the loaded binary hashes.

Without a campaign directory: the initial section is recomputed and compared byte for byte; the
future certificate and its independent check are regenerated from terminal/all_terminal_exact.json
and compared byte for byte; Q28 is rebuilt from the regenerated certificate and compared byte for
byte. Every epsilon declaration of the box must agree exactly. All files are those of the box
directory.

With a campaign directory: first every output file is checked against campaign/RUN_MANIFEST.json,
then the terminal extraction, the lineage and clock audit, the commutation audit and the mechanism
census are rerun and compared byte for byte with terminal/, before the checks above.

Standard library only unless --check-runtime is requested. Each check prints PASS or FAIL;
exit code 1 on any FAIL. Runtime loading is skipped when static engine checks fail.
"""
import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
import re
import tempfile
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / 'certify'
BOX = TERMINAL = None   # set from --box in main()
RESULTS = []


def source_identity(engine):
    """Static counterpart of engine/run.py identity(), with the same file selection."""
    top = ('run.py', 'build_native.py', 'build_all_native.py', 'launch_fresh.py',
           'reference/full_model_reference.md')
    paths = [engine / name for name in top]
    for directory in ('affine', 'kernel'):
        paths.extend(p for p in (engine / directory).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts
                     and p.suffix in ('.py', '.c', '.h', '.so', '.pyd', '.dll', '.dylib'))
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(str(path.relative_to(engine)).encode() + b'\0')
        digest.update(path.read_bytes())
    return digest.hexdigest()


def symbol_limit(engine):
    tree = ast.parse((engine / 'affine' / 'affine_iv.py').read_text())
    values = [ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == 'KMAX' for target in node.targets)]
    if len(values) != 1 or type(values[0]) is not int or values[0] <= 0:
        raise ValueError('expected one positive literal KMAX assignment')
    return values[0]


def archived_kernel_id(engine, campaign):
    identity = {'sources': source_identity(engine), 'environment': campaign['environment'],
                'parameters': campaign['parameters'], 'precision': 160, 'symbols': symbol_limit(engine)}
    encoded = json.dumps(identity, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def runtime_environment(engine, campaign):
    """Inspect loaded modules in a fresh process, without substituting recorded values."""
    code = '''
import hashlib, importlib, json, platform, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
import run
run.initialize(Path(sys.argv[2]))
import numpy, scipy, rounding
environment = dict(python=platform.python_version(), numpy=numpy.__version__,
                   scipy=scipy.__version__, arithmetic_backend=rounding.BACKEND)
native_files = {}
if rounding.BACKEND == 'native':
    for name, folder in (('_rounding_native', root / 'affine'),
                         ('_a22_native', root / 'kernel' / 'native')):
        module = importlib.import_module(name)
        path = Path(module.__file__).resolve()
        if path.parent != folder.resolve():
            raise RuntimeError('native module loaded outside the selected engine: ' + name)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        native_files[str(path.relative_to(root))] = digest
        if name == '_rounding_native':
            environment['native_sha256'] = digest
print(json.dumps(dict(environment=environment, native_files=native_files)))
'''
    env = dict(os.environ, A22_PHYSICAL_EPSILON=campaign['parameters']['epsilon_relative'])
    with tempfile.TemporaryDirectory(prefix='a22-runtime-') as diagnostics:
        out = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(engine), diagnostics],
                             env=env, capture_output=True, text=True, timeout=600)
    if out.returncode != 0:
        raise RuntimeError('engine could not be loaded: ' +
                           (out.stderr.strip().splitlines() or ['?'])[-1][:300])
    return json.loads(out.stdout.strip().splitlines()[-1])


def box_engine():
    """The repository engine directory of the box, named in <box>/campaign/ENGINE."""
    name = (BOX / 'campaign' / 'ENGINE').read_text().strip()
    path = (REPO / name).resolve()
    if path.parent != REPO or not name.startswith('engine_') or not (path / 'run.py').is_file():
        raise ValueError(f'invalid engine directory in campaign/ENGINE: {name!r}')
    return path


def report(name, ok, detail=''):
    RESULTS.append(ok)
    print(f'[{"PASS" if ok else "FAIL"}] {name}' + (f': {detail}' if detail else ''), flush=True)


def run(script, *args):
    out = subprocess.run([sys.executable, '-I', str(TOOLS / script)] + [str(a) for a in args],
                         capture_output=True, text=True, cwd=REPO)
    if out.returncode != 0:
        raise RuntimeError(f'{script} exited {out.returncode}: ' + (out.stderr.strip().splitlines() or ['?'])[-1][:300])
    return out.stdout


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def same_bytes(a, b):
    return Path(a).read_bytes() == Path(b).read_bytes()


def check(name, fn):
    try:
        fn()
    except Exception as exc:
        report(name, False, f'{type(exc).__name__}: {exc}')


def outputs_checks(campaign, tmp):
    def manifest():
        files = json.loads((BOX / 'campaign' / 'RUN_MANIFEST.json').read_text())['files']
        bad = [k for k, v in files.items() if not (campaign / k).is_file() or sha(campaign / k) != v['sha256']]
        extra = [str(p.relative_to(campaign)) for p in campaign.rglob('*') if p.is_file() and str(p.relative_to(campaign)) not in files]
        report('campaign outputs against RUN_MANIFEST.json', not bad and not extra,
               f'{len(files)} files, {len(bad)} mismatched, {len(extra)} unlisted')
    check('campaign outputs against RUN_MANIFEST.json', manifest)

    def extraction():
        run('extract_terminal.py', campaign, tmp)
        for name in ('all_terminal_exact.json', 'all_layers_audit.json'):
            report(f'terminal extraction: {name}', same_bytes(tmp / name, TERMINAL / name))
    check('terminal extraction', extraction)

    def lineage():
        run('audit_lineage.py', campaign, tmp / 'lineage_and_clocks.json')
        report('lineage and clock audit', same_bytes(tmp / 'lineage_and_clocks.json', TERMINAL / 'lineage_and_clocks.json'))
    check('lineage and clock audit', lineage)

    def commutations():
        run('audit_commutations.py', campaign, tmp / 'commutation_usage.json')
        report('commutation audit', same_bytes(tmp / 'commutation_usage.json', TERMINAL / 'commutation_usage.json'))
    check('commutation audit', commutations)

    def mechanisms():
        run('audit_mechanisms.py', campaign, tmp / 'mechanism_usage.json')
        report('mechanism census', same_bytes(tmp / 'mechanism_usage.json', TERMINAL / 'mechanism_usage.json'))
    check('mechanism census', mechanisms)


def engine_checks(engine, check_runtime=False):
    start = len(RESULTS)
    top = {'run.py', 'build_native.py', 'build_all_native.py', 'launch_fresh.py', 'reference/full_model_reference.md'}

    binary_suffixes = ('.so', '.pyd', '.dll', '.dylib', '.o')

    def identity_files(base):
        return {str(p.relative_to(base)) for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts
                and (str(p.relative_to(base)) in top or p.relative_to(base).parts[0] in ('affine', 'kernel'))}

    def contents():
        # Sources are compared with the box's engine directory; binaries are taken from the as-run
        # engine only, so native extensions built locally in the repository do not enter the comparison.
        source = box_engine()
        run_files, repo_files = identity_files(engine), identity_files(source)
        a = {x for x in run_files if not x.endswith(binary_suffixes)}
        b = {x for x in repo_files if not x.endswith(binary_suffixes)}
        binaries = {x for x in run_files if x.endswith(binary_suffixes)}
        differ = sorted(x for x in a & b if sha(engine / x) != sha(source / x))
        extra = sorted(a - b) + sorted(b - a)
        campaign = json.loads((BOX / 'campaign' / 'campaign.json').read_text())
        natives = [x for x in binaries if x.startswith('affine/_rounding_native')]
        native_ok = len(natives) == 1 and sha(engine / natives[0]) == campaign['environment']['native_sha256']
        report('as-run engine sources and binaries', not differ and not extra and len(binaries) == 2 and native_ok,
               f'{len(a & b)} sources identical to {source.name}/, {len(binaries)} binaries, rounding binary '
               + ('matches campaign.json' if native_ok else 'DOES NOT match campaign.json'))
    check('as-run engine sources and binaries', contents)

    def identity():
        campaign = json.loads((BOX / 'campaign' / 'campaign.json').read_text())
        got = archived_kernel_id(engine, campaign)
        report('archived kernel_id (files and recorded environment)', got == campaign['kernel_id'],
               f'{got[:16]}... vs {campaign["kernel_id"][:16]}...')
    check('archived kernel_id (files and recorded environment)', identity)

    if check_runtime:
        def runtime():
            if not all(RESULTS[start:]):
                raise RuntimeError('runtime loading skipped because static engine checks failed')
            campaign = json.loads((BOX / 'campaign' / 'campaign.json').read_text())
            loaded = runtime_environment(engine, campaign)
            actual, expected = loaded['environment'], campaign['environment']
            differences = [f'{key}: loaded {actual.get(key)!r}, recorded {expected.get(key)!r}'
                           for key in sorted(set(actual) | set(expected)) if actual.get(key) != expected.get(key)]
            binaries = {str(p.relative_to(engine)): sha(p) for p in engine.rglob('*')
                        if p.is_file() and p.name.endswith(binary_suffixes)}
            if loaded['native_files'] != binaries:
                differences.append('loaded native binaries do not match the archived binaries')
            report('loaded engine runtime', not differences, '; '.join(differences) or 'matches the recorded environment')
        check('loaded engine runtime', runtime)


def box_epsilon():
    """The box's epsilon; every declaration in the box must state the same exact value."""
    campaign = json.loads((BOX / 'campaign' / 'campaign.json').read_text())
    eps = campaign['parameters']['epsilon_relative']
    terminal = json.loads((TERMINAL / 'all_terminal_exact.json').read_text())
    log = json.loads((TERMINAL / 'certification_log.json').read_text())
    declared = {'campaign.json': eps,
                'all_terminal_exact.json': terminal['campaign']['parameters']['epsilon_relative'],
                'certification_log.json': log['campaign']['parameters']['epsilon_relative']}
    if len({Fraction(v) for v in declared.values()}) != 1:
        raise ValueError(f'conflicting epsilon declarations: {declared}')
    if terminal['campaign'] != campaign or log['campaign'] != campaign:
        raise ValueError('campaign metadata differ between campaign.json, the terminal extraction and the log')
    return eps


def log_consistency():
    """Every certificate hash cited by the certification log must be the committed certificate's."""
    cited = set(re.findall(r'certificate_sha256\W+([0-9a-f]{64})', (TERMINAL / 'certification_log.json').read_text()))
    actual = sha(TERMINAL / 'future_certificate.json')
    report('certification log cites the committed certificate', bool(cited) and cited == {actual},
           f'cited {sorted(c[:8] for c in cited)}, committed {actual[:8]}')


def record_checks(tmp):
    def initial():
        eps = box_epsilon()
        run('certify_initial_section.py', tmp / 'initial.json', eps)
        report(f'initial section at eps = {eps}', same_bytes(tmp / 'initial.json', TERMINAL / 'initial_section.json'))
    check('initial section', initial)

    def future():
        eps = box_epsilon()
        terminal = TERMINAL / 'all_terminal_exact.json'
        cert, ind, q = tmp / 'future_certificate.json', tmp / 'independent_check.json', tmp / 'q.json'
        log = json.loads((TERMINAL / 'certification_log.json').read_text())
        run('certify_future.py', terminal, cert, eps)
        run('verify_future_general.py', terminal, cert, ind, eps, log['return_bound'])
        c = json.loads(cert.read_text())
        # Every derived file is regenerated and compared byte for byte with the recorded one; Q28 is
        # rebuilt from the regenerated certificate, so no recorded bound is trusted.
        report('future certificate (directed integers)',
               same_bytes(cert, TERMINAL / 'future_certificate.json') and c['status'].startswith('PASS'),
               f"return before {c['global_quiescent_by'][:10]}, {c['active']} active cells, {c['masked_count']} masked ports")
        i = json.loads(ind.read_text())
        report('independent future check (directed decimals)',
               same_bytes(ind, TERMINAL / 'independent_check.json') and i['status'] == 'PASS'
               and i['certificate_sha256'] == sha(TERMINAL / 'future_certificate.json'))
        run('build_q_domain.py', terminal, cert, q)
        report('Q28 domain', same_bytes(q, TERMINAL / 'invariant_domain_Q28.json'))
    check('future certificates', future)
    check('certification log cites the committed certificate', log_consistency)


def main():
    if not __debug__:
        raise RuntimeError('Run without -O')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--box', type=Path, required=True, help='certified box directory, e.g. results/eps3e-3')
    parser.add_argument('campaign', nargs='?', type=Path)
    parser.add_argument('--engine', type=Path, help='statically verify the archived engine files and identity')
    parser.add_argument('--check-runtime', action='store_true', help='also require the loaded runtime to match the archive')
    args = parser.parse_args()
    if args.check_runtime and args.engine is None:
        parser.error('--check-runtime requires --engine')
    global BOX, TERMINAL
    BOX = args.box.resolve()
    TERMINAL = BOX / 'terminal'
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        if args.engine is not None:
            engine_checks(args.engine.resolve(), args.check_runtime)
        if args.campaign is not None:
            outputs_checks(args.campaign.resolve(), tmp)
        record_checks(tmp)
    failed = RESULTS.count(False)
    print(f'\n{RESULTS.count(True)} PASS, {failed} FAIL')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
