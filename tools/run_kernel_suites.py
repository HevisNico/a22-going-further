"""Run every test file shipped inside engine/kernel/, on a scratch copy of the engine.

    python -B tools/run_kernel_suites.py <built engine dir>

The kernel R is never modified, so its own test files cannot be edited either. They write
fixtures next to themselves, so each run uses a fresh copy of the engine (with its built native
extensions), and each file runs in its own process from its own directory. unittest files run
under `python -m unittest`; the others are scripts whose exit code is the result.

Five unittest files test the cache, memo and provenance layer of the inherited interval campaign
driver (campagne_A22, source_reuse_A22, the identite_temps_A22 registry, the memo DAG). Their
results depend on the environment: on Python 3.12 / Ubuntu, four of them fail; an independent
audit saw only test_provenance_A22 fail, on a mock (AttributeError: __code__). The affine engine
does not load these modules (from engine/kernel/R_continuation_*, run.py loads only
avance_causale_A22 and ready_general_A22), and this script checks that. These five files are run
and their results printed (DRIVER-PASS / DRIVER-FAIL), but they do not gate. Every other kernel
test file must pass.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DRIVER_LAYER = {
    'R_continuation_A22_2026-10-18/test_ancestor_reuse.py',
    'R_continuation_A22_2026-10-18/test_provenance_A22.py',
    'R_continuation_A22_2026-10-18/test_atom_registry_reuse.py',
    'R_continuation_A22_2026-10-18/test_memo_DAG_A22.py',
    'R_continuation_A22_2026-10-18/test_source_reuse_integration_A22.py',
}
# Modules of the inherited campaign driver exercised by those files; the engine must load none.
DRIVER_ONLY = {'campagne_A22', 'source_reuse_A22', 'identite_temps_A22', 'provenance_A22',
               'rejeu_qualifie_A22', 'reprendre_A22', 'temps_symboliques_A22'}


def loaded_kernel_modules(engine):
    code = ('import sys, tempfile; from pathlib import Path; sys.path.insert(0, sys.argv[1]); import run; '
            'run.initialize(Path(tempfile.mkdtemp())); '
            'print(" ".join(sorted(n for n, m in sys.modules.items() '
            'if "/kernel/" in (getattr(m, "__file__", None) or ""))))')
    env = dict(os.environ, A22_PHYSICAL_EPSILON='0.003')
    out = subprocess.run([sys.executable, '-B', '-c', code, str(engine)], env=env,
                         capture_output=True, text=True, timeout=600, check=True)
    return set(out.stdout.split())


def main():
    source = Path(sys.argv[1]).resolve()
    failures = []
    loaded = loaded_kernel_modules(source)
    overlap = loaded & DRIVER_ONLY
    print(f'engine loads {len(loaded)} kernel modules; driver-only modules loaded: {sorted(overlap) or "none"}')
    if overlap:
        failures.append('the engine loads a module tested only by a non-gating driver file')
    with tempfile.TemporaryDirectory(prefix='a22-kernel-suites-') as tmp:
        engine = Path(tmp) / 'engine'
        shutil.copytree(source, engine, ignore=shutil.ignore_patterns('__pycache__', '.venv'))
        for test in sorted((engine / 'kernel').glob('*/test_*.py')):
            name = str(test.relative_to(engine / 'kernel'))
            if 'unittest.TestCase' in test.read_text():
                cmd = [sys.executable, '-B', '-m', 'unittest', test.stem]
            else:
                cmd = [sys.executable, '-B', test.name]
            out = subprocess.run(cmd, cwd=test.parent, capture_output=True, text=True, timeout=1800)
            counts = re.findall(r'^(Ran \d+ tests?.*|OK.*|FAILED.*)$', out.stdout + out.stderr, re.M)
            detail = ', '.join(c for c in counts if not c.startswith('Ran')) or ('exit 0' if out.returncode == 0 else f'exit {out.returncode}')
            passed = out.returncode == 0
            if name in DRIVER_LAYER:
                status = 'DRIVER-PASS' if passed else 'DRIVER-FAIL'
            else:
                status = 'PASS' if passed else 'FAIL'
                if not passed:
                    failures.append(name)
                    print((out.stdout + out.stderr)[-3000:])
            print(f'[{status}] {name}: {detail}', flush=True)
    if failures:
        print('\n'.join(['', 'FAILED:'] + failures))
        sys.exit(1)
    print('\nevery gating kernel test file passed')


if __name__ == '__main__':
    main()
