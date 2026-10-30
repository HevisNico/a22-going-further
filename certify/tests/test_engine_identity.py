"""Static identities and loaded-runtime checks have separate acceptance conditions."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'certify'))
import verify


class EngineIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # The as-run engine and the repository's engine directory of the box are separate copies.
        self.engine = self.root / 'as_run' / 'engine'
        self.source = self.root / 'engine_test'
        for base in (self.engine, self.source):
            for name in ('run.py', 'build_native.py', 'build_all_native.py', 'launch_fresh.py',
                         'reference/full_model_reference.md', 'affine/affine_iv.py',
                         'kernel/native/a22_native.c'):
                path = base / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('KMAX = 1024\nraise RuntimeError("must not execute during a static check")\n')
        self.binaries = {}
        for name in ('affine/_rounding_native.cpython-312.so', 'kernel/native/_a22_native.cpython-312.so'):
            path = self.engine / name
            path.write_bytes(b'fixture native binary')
            self.binaries[name] = verify.sha(path)
        self.campaign = {
            'environment': {'python': '3.12.14', 'numpy': '2.3.5', 'scipy': '1.17.0',
                            'arithmetic_backend': 'native',
                            'native_sha256': self.binaries['affine/_rounding_native.cpython-312.so']},
            'parameters': {'epsilon_relative': '0.003'},
        }
        self.campaign['kernel_id'] = verify.archived_kernel_id(self.engine, self.campaign)
        self.box = self.root / 'results' / 'box'
        (self.box / 'campaign').mkdir(parents=True)
        (self.box / 'campaign' / 'campaign.json').write_text(json.dumps(self.campaign))
        (self.box / 'campaign' / 'ENGINE').write_text('engine_test\n')
        verify.RESULTS.clear()
        self.addCleanup(verify.RESULTS.clear)

    def check_engine(self, runtime=False):
        with patch.object(verify, 'REPO', self.root), patch.object(verify, 'BOX', self.box), \
                contextlib.redirect_stdout(io.StringIO()):
            verify.engine_checks(self.engine, runtime)
        return list(verify.RESULTS)

    def test_static_check_never_imports_or_executes_engine(self):
        with patch.object(verify.subprocess, 'run', side_effect=AssertionError('unexpected execution')):
            self.assertEqual(self.check_engine(), [True, True])

    def test_sources_are_compared_with_the_box_engine_directory(self):
        (self.source / 'affine' / 'affine_iv.py').write_text('KMAX = 1024\n# changed\n')
        self.assertEqual(self.check_engine(), [False, True])

    def test_engine_directory_must_be_a_top_level_engine_dir(self):
        for name in ('engine', '../engine_test', 'certify'):
            verify.RESULTS.clear()
            (self.box / 'campaign' / 'ENGINE').write_text(name + '\n')
            with self.subTest(name=name):
                self.assertEqual(self.check_engine()[0], False)

    def test_python_fallback_and_wrong_interpreter_fail_runtime_check(self):
        loaded = {'environment': dict(self.campaign['environment'], python='3.13.17', arithmetic_backend='python'),
                  'native_files': {}}
        loaded['environment'].pop('native_sha256')
        with patch.object(verify, 'runtime_environment', return_value=loaded):
            self.assertEqual(self.check_engine(True), [True, True, False])

    def test_matching_loaded_runtime_passes(self):
        loaded = {'environment': self.campaign['environment'], 'native_files': self.binaries}
        with patch.object(verify, 'runtime_environment', return_value=loaded):
            self.assertEqual(self.check_engine(True), [True, True, True])

    def test_wrong_dependency_or_native_binary_is_rejected(self):
        for kind in ('numpy', 'scipy', 'native_sha256', 'kernel_binary'):
            verify.RESULTS.clear()
            loaded = copy.deepcopy({'environment': self.campaign['environment'], 'native_files': self.binaries})
            if kind == 'kernel_binary':
                loaded['native_files']['kernel/native/_a22_native.cpython-312.so'] = 'wrong'
            else:
                loaded['environment'][kind] = 'wrong'
            with self.subTest(kind=kind), patch.object(verify, 'runtime_environment', return_value=loaded):
                self.assertEqual(self.check_engine(True), [True, True, False])

    def test_failed_static_identity_prevents_runtime_loading(self):
        (self.engine / 'run.py').write_text('raise RuntimeError("changed")\n')
        with patch.object(verify, 'runtime_environment') as runtime:
            self.assertEqual(self.check_engine(True), [False, False, False])
            runtime.assert_not_called()

    def test_literal_symbol_limit_required(self):
        (self.engine / 'affine' / 'affine_iv.py').write_text('KMAX = int("1024")\n')
        with self.assertRaises(ValueError):
            verify.archived_kernel_id(self.engine, self.campaign)

    def test_static_source_hash_matches_the_runner(self):
        for engine in sorted(ROOT.glob('engine_*/run.py')):
            spec = importlib.util.spec_from_file_location(f'a22_runner_{engine.parent.name}', engine)
            runner = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(runner)
            with self.subTest(engine=engine.parent.name):
                self.assertEqual(verify.source_identity(engine.parent), runner.identity())

    def test_every_box_names_an_existing_engine_directory(self):
        for box in sorted((ROOT / 'results').glob('*/campaign/campaign.json')):
            name = (box.parent / 'ENGINE').read_text().strip()
            with self.subTest(box=box.parent.parent.name):
                self.assertTrue(name.startswith('engine_') and (ROOT / name / 'run.py').is_file())

    def test_runtime_option_requires_an_engine(self):
        result = subprocess.run([sys.executable, '-I', str(ROOT / 'certify' / 'verify.py'), '--box', 'x',
                                 '--check-runtime'], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--check-runtime requires --engine', result.stderr)


if __name__ == '__main__':
    unittest.main()
