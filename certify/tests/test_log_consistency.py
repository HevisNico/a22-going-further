"""The certification log must cite the committed future certificate."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'certify'))
import verify


class LogConsistencyTests(unittest.TestCase):
    def run_check(self, log_text):
        with tempfile.TemporaryDirectory() as tmp:
            terminal = Path(tmp)
            shutil.copy(ROOT / 'results' / 'eps3e-3' / 'terminal' / 'future_certificate.json', terminal)
            (terminal / 'certification_log.json').write_text(log_text)
            verify.RESULTS.clear()
            old = verify.TERMINAL
            verify.TERMINAL = terminal
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    verify.log_consistency()
            finally:
                verify.TERMINAL = old
            return verify.RESULTS[-1]

    def test_committed_log_passes(self):
        text = (ROOT / 'results' / 'eps3e-3' / 'terminal' / 'certification_log.json').read_text()
        self.assertTrue(self.run_check(text))

    def test_stale_or_missing_hash_fails(self):
        self.assertFalse(self.run_check(json.dumps({'output': '"certificate_sha256": "' + 'a' * 64 + '"'})))
        self.assertFalse(self.run_check(json.dumps({'output': 'no hash'})))


if __name__ == '__main__':
    unittest.main()
