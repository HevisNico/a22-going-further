"""Certificate widths must agree across inputs, arguments and generated reports."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'certify'
sys.path.insert(0, str(TOOLS))
from certificate_parameters import resolve_epsilon

BOX = ROOT / 'results' / 'eps3e-3' / 'terminal'


class ParameterTests(unittest.TestCase):
    def setUp(self):
        self.terminal = {'campaign': {'parameters': {'epsilon_relative': '0.003'}}}
        self.certificate = dict(copy.deepcopy(self.terminal), eps='3/1000')

    def test_default_uses_campaign_and_equivalent_exact_spellings(self):
        for explicit in (None, '3e-3', '0.003', '3/1000'):
            self.assertEqual(resolve_epsilon(self.terminal, explicit, self.certificate), Fraction(3, 1000))

    def test_explicit_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, 'explicit epsilon'):
            resolve_epsilon(self.terminal, '1e-2', self.certificate)

    def test_certificate_width_and_campaign_width_both_checked(self):
        for field in ('eps', 'campaign'):
            bad = copy.deepcopy(self.certificate)
            if field == 'eps':
                bad['eps'] = '1e-2'
            else:
                bad['campaign']['parameters']['epsilon_relative'] = '1e-2'
            with self.assertRaisesRegex(ValueError, 'certificate epsilon'):
                resolve_epsilon(self.terminal, certificate=bad)

    def test_missing_or_invalid_width_never_uses_a_fallback(self):
        for value in ('NaN', 'Infinity', '0', '-0.003', '1', '2', '1/0', 0.003, True):
            bad = {'campaign': {'parameters': {'epsilon_relative': value}}}
            with self.subTest(value=value), self.assertRaises(ValueError):
                resolve_epsilon(bad)
        with self.assertRaisesRegex(ValueError, 'missing campaign'):
            resolve_epsilon({}, '3e-3')
        with self.assertRaisesRegex(ValueError, 'missing certificate'):
            resolve_epsilon(self.terminal, certificate=self.terminal)

    def test_mismatch_is_exact_even_below_decimal_context_precision(self):
        with self.assertRaises(ValueError):
            resolve_epsilon(self.terminal, '0.0030000000000000000000000000000000000001')


class CommandTests(unittest.TestCase):
    terminal = BOX / 'all_terminal_exact.json'
    certificate = BOX / 'future_certificate.json'

    def run_tool(self, script, *args):
        return subprocess.run([sys.executable, '-I', str(TOOLS / script), *map(str, args)],
                              capture_output=True, text=True, timeout=3600)

    def test_independent_default_matches_explicit_width_and_committed_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            default, explicit = Path(tmp) / 'default.json', Path(tmp) / 'explicit.json'
            for dest, args in ((default, ()), (explicit, ('3e-3', '19'))):
                result = self.run_tool('verify_future_general.py', self.terminal, self.certificate, dest, *args)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(explicit.read_text())['eps'], '0.003')
            self.assertEqual(explicit.read_bytes(), (BOX / 'independent_check.json').read_bytes())

    def test_both_commands_reject_explicit_mismatch_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            for script in ('certify_future.py', 'verify_future_general.py'):
                dest = Path(tmp) / (script + '.json')
                inputs = [self.terminal] + ([self.certificate] if script == 'verify_future_general.py' else [])
                result = self.run_tool(script, *inputs, dest, '1e-2')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('explicit epsilon does not match', result.stderr)
                self.assertFalse(dest.exists())

    def test_verifier_and_domain_reject_inconsistent_certificate_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert = json.loads(self.certificate.read_text())
            cert['eps'] = '1/100'
            changed = Path(tmp) / 'certificate.json'
            changed.write_text(json.dumps(cert))
            for script in ('verify_future_general.py', 'build_q_domain.py'):
                dest = Path(tmp) / (script + '.json')
                result = self.run_tool(script, self.terminal, changed, dest)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('certificate epsilon does not match', result.stderr)
                self.assertFalse(dest.exists())

    def test_campaign_width_mismatch_rejected_by_independent_check(self):
        # The audit's reproduction: campaign declared at 0.01, certificate and argument at 0.003.
        with tempfile.TemporaryDirectory() as tmp:
            import hashlib
            data = json.loads(self.terminal.read_text())
            data['campaign']['parameters']['epsilon_relative'] = '0.01'
            terminal = Path(tmp) / 'terminal.json'
            terminal.write_text(json.dumps(data))
            cert = json.loads(self.certificate.read_text())
            cert['campaign'] = data['campaign']
            cert['terminal_input_sha256'] = hashlib.sha256(terminal.read_bytes()).hexdigest()
            changed = Path(tmp) / 'certificate.json'
            changed.write_text(json.dumps(cert))
            dest = Path(tmp) / 'out.json'
            result = self.run_tool('verify_future_general.py', terminal, changed, dest, '0.003', '19')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('epsilon does not match', result.stderr)
            self.assertFalse(dest.exists())


if __name__ == '__main__':
    unittest.main()
