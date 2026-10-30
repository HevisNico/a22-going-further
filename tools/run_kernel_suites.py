"""Run every test file shipped inside engine/kernel/, on a scratch copy of the engine.

    python -B tools/run_kernel_suites.py <built engine dir>

The kernel R is never modified, so its own test files cannot be edited either. They write
fixtures next to themselves, so each run uses a fresh copy of the engine (with its built native
extensions), and each file runs in its own process from its own directory. unittest files run
under `python -m unittest`; the others are scripts whose exit code is the result.

Every file gates the run. Five unittest files test the cache, memo and provenance layer of the
inherited interval campaign driver (campagne_A22, source_reuse_A22, the identite_temps_A22 registry,
the memo DAG). They load only kernel modules, which are unchanged (KERNEL_SHA256SUMS), and on Python
3.12 / Linux 18 of their tests fail, deterministically. The affine engine does not load these
modules (from the kernel's R_continuation directory it loads only avance_causale_A22 and
ready_general_A22), and this script checks that on every run. For those five files the exact set
of non-passing tests is pinned in EXPECTED_NOT_OK: the run fails if any other test fails, or if a
pinned test changes status, so the list cannot go stale. Every other file must pass entirely.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RC = 'R_continuation_A22_2026-10-18/'
EXPECTED_NOT_OK = {
    RC + 'test_ancestor_reuse.py': {
        'test_ancestor_reuse.ScopeTests.test_distinct_joint_histories_remain_distinct': 'ERROR',
        'test_ancestor_reuse.ScopeTests.test_repeated_checks_reuse_only_complete_success': 'FAIL'},
    RC + 'test_atom_registry_reuse.py': {f'test_atom_registry_reuse.RegistryTests.{t}': 'FAIL' for t in (
        'test_absent_constant_label_dependency_is_also_preserved',
        'test_conflicting_change_detected_on_close_without_next_check',
        'test_conflicting_change_during_close_final_scan_refuses',
        'test_conflicting_change_during_first_final_scan_is_not_pinned_as_truth',
        'test_deletion_refuses_without_restoring_the_entry',
        'test_distant_ancestor_metadata_replacement_refuses')},
    RC + 'test_memo_DAG_A22.py': {f'test_memo_DAG_A22.DAGTests.{t}': 'FAIL' for t in (
        'test_active_hits_preserve_distinct_histories_and_selectors',
        'test_changed_ancestor_between_sessions_and_repeated_failure',
        'test_changed_snapshot_with_active_hit_refuses',
        'test_context_incompatible_and_active_cycle_refuse',
        'test_dense_graph_same_success_with_active_hits',
        'test_each_new_state_link_checked_after_black_parent',
        'test_owner_conflict_on_shared_artifact_refuses')},
    RC + 'test_provenance_A22.py': {},
    RC + 'test_source_reuse_integration_A22.py': {
        'test_source_reuse_integration_A22.BindingTests.test_dispatch_reuses_success_but_default_calls_stay_fresh': 'FAIL',
        'test_source_reuse_integration_A22.BindingTests.test_effective_inventory_covers_new_module_and_integration_functions': 'FAIL',
        'test_source_reuse_integration_A22.PipelineTests.test_layer_prepares_all_histories_then_closes_before_publication': 'FAIL'},
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
                expected = EXPECTED_NOT_OK.get(name, {})
                ran = re.search(r'^Ran (\d+) tests?', text, re.M)
                good = bool(ran) and int(ran.group(1)) == len(results) and not_ok == expected
                detail = f'{len(results)} tests, {len(not_ok)} not ok' + (f' (all {len(expected)} pinned)' if expected and good else '')
                if not good:
                    changed = sorted(set(not_ok.items()) ^ set(expected.items()))
                    failures.append(f'{name}: differs from the pinned status: {changed[:10]}')
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
    print('\nevery kernel test file as expected')


if __name__ == '__main__':
    main()
