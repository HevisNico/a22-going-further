"""Parameter boxes must enclose the exact requested width, including tiny widths."""
import json
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'certify'))
from verify_future_general import parameter_factor


class ParameterRoundingTests(unittest.TestCase):
    widths = ('0.003', '0.01', '0.1', '1e-40', '1e-100',
              '0.003000000000000000000000000001')

    def test_decimal_factor_is_outward_even_with_a_small_ambient_context(self):
        for precision in (6, 28):
            with localcontext() as ctx:
                ctx.prec = precision
                for text in self.widths:
                    with self.subTest(precision=precision, epsilon=text):
                        factor = parameter_factor(Decimal(text))
                        eps = Fraction(text)
                        self.assertLessEqual(Fraction(factor.l), 1-eps)
                        self.assertGreaterEqual(Fraction(factor.u), 1+eps)

    def test_initial_certificate_encloses_width_before_fixed_scale_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            for text in (text for text in self.widths if text != '0.1'):
                with self.subTest(epsilon=text):
                    output = Path(tmp) / 'initial.json'
                    result = subprocess.run([sys.executable, '-I',
                        str(ROOT / 'certify/certify_initial_section.py'), str(output), text],
                        capture_output=True, text=True, timeout=60)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    data = json.loads(output.read_text())
                    lo, hi = map(Fraction, data['relative_parameter_factor'])
                    eps = Fraction(text)
                    self.assertLessEqual(lo, 1-eps)
                    self.assertGreaterEqual(hi, 1+eps)

    def test_decimal_factor_rejects_invalid_widths(self):
        for text in ('0', '-0.1', '1', 'Infinity', 'NaN'):
            with self.subTest(epsilon=text), self.assertRaises(AssertionError):
                parameter_factor(text)


if __name__ == '__main__':
    unittest.main()
