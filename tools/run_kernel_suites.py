"""Run every test file shipped inside engine/kernel/, on a scratch copy of the engine.

    python -B tools/run_kernel_suites.py <built engine dir>

The kernel R is never modified, so its own test files cannot be edited either. They write
fixtures next to themselves, so each run uses a fresh copy of the engine (with its built native
extensions), and each file runs in its own process from its own directory. unittest files run
under `python -m unittest`; the others are scripts whose exit code is the result.

Every file gates the run: unittest files must have every test pass, scripts must exit 0. On the CI
runner (ubuntu-latest, Python 3.12) every kernel test file passes. Five of them test the cache,
memo and provenance layer of the inherited interval campaign driver; they are sensitive to the
environment (in some local containers 18 of their tests fail), which is why the CI result is the
reference. The affine engine does not load that driver layer (from the kernel's R_continuation
directory it loads only avance_causale_A22 and ready_general_A22); this script checks it.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

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
        failures.append('the engine loads a module of the inherited campaign driver')
    with tempfile.TemporaryDirectory(prefix='a22-kernel-suites-') as tmp:
        engine = Path(tmp) / 'engine'
        shutil.copytree(source, engine, ignore=shutil.ignore_patterns('__pycache__', '.venv'))
        for test in sorted((engine / 'kernel').glob('*/test_*.py')):
            name = str(test.relative_to(engine / 'kernel'))
            unit = 'unittest.TestCase' in test.read_text()
            cmd = ([sys.executable, '-B', '-m', 'unittest', '-v', test.stem] if unit
                   else [sys.executable, '-B', test.name])
            out = subprocess.run(cmd, cwd=test.parent, capture_output=True, text=True, timeout=1800)
            text = out.stdout + out.stderr
            if unit:
                results = dict(re.findall(r'^\w+ \(([\w.]+)\) \.\.\. (ok|FAIL|ERROR|skipped.*|expected failure|unexpected success)$',
                                          text, re.M))
                not_ok = {k: v for k, v in results.items() if v != 'ok'}
                ran = re.search(r'^Ran (\d+) tests?', text, re.M)
                good = out.returncode == 0 and bool(ran) and int(ran.group(1)) == len(results) > 0 and not not_ok
                detail = f'{len(results)} tests, {len(not_ok)} not ok'
                if not good:
                    failures.append(f'{name}: {sorted(not_ok.items())[:10]}')
            else:
                good = out.returncode == 0
                detail = 'exit 0' if good else f'exit {out.returncode}'
                if not good:
                    failures.append(name)
            if not good:
                print(text[-3000:])
            print(f'[{"PASS" if good else "FAIL"}] {name}: {detail}', flush=True)
    if failures:
        print('\n'.join(['', 'FAILED:'] + failures))
        sys.exit(1)
    print('\nevery kernel test file passed')


if __name__ == '__main__':
    main()
