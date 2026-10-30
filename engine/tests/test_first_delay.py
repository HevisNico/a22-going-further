"""Fix D1: the first mark of a late first pulse uses the decayed initial charge."""
import math
import os
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'affine'))
os.environ.setdefault('A22_ARTIFACT_DIR', str(ROOT / 'test_diagnostics'))
import engine
import affine_iv
import temporal

I = engine.I
b = engine.b


class FirstDelay(unittest.TestCase):
    def setUp(self):
        self.old_fresh = affine_iv.FRESH
        affine_iv.FRESH = None
        temporal.begin_producer('first-delay-test')
        engine.settings_cell('first-delay-test')

    def tearDown(self):
        affine_iv.FRESH = self.old_fresh

    def arrival(self, t):
        return temporal.Time(f'first-delay-test:a:{t}', I(t))

    def test_early_first_pulse_keeps_D1(self):
        start = engine.v.T('clock', I(0), D(0))
        self.assertIs(b.FIRST_DELAY(1, start), b.D1_PORTS[1])

    def test_late_first_pulse_is_D0_up_to_the_decayed_charge(self):
        late = b.FIRST_DELAY(1, self.arrival(D(122)))
        self.assertLess(late.width(), b.D1_PORTS[1].width())
        # Encloses the exact-rest delay of every parameter point of the port (D0).
        self.assertLessEqual(late.lo, b.D0_PORTS[1].lo)
        self.assertGreaterEqual(late.hi, b.D0_PORTS[1].hi)

    def test_point_root_inside(self):
        # Nominal port constant, initial charge at either end of the family, arrival at 5.
        A, K, RM = (float(b.A.mid()), float(b.K.mid()), float(b.RM.mid()))
        M = float(engine.v.M.mid())
        h = lambda u: A / (A - K) * (math.exp(-K * u) - math.exp(-A * u))
        enclosure = b.FIRST_DELAY(1, self.arrival(D(5)))
        for eta in (-1e-5, 0.0, 1e-5):
            f = lambda u: RM + eta * math.exp(-K * (5 + u)) + M * h(u) - 1
            lo, hi = 0.0, 0.1
            for _ in range(80):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
            self.assertTrue(float(enclosure.lo) - 1e-12 <= lo <= float(enclosure.hi) + 1e-12)


if __name__ == '__main__':
    unittest.main()
