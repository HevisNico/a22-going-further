"""Numerical cross-checks of the exploratory simulator and paired outcome accounting."""
import copy
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent/'point_simulator')]
import numpy as np
import run as study
from engine import Device, NOMINAL, simulate, thresholds
from ode_reference import simulate_ode


def device():
    return Device(np.broadcast_to(NOMINAL, (3, 5)).tolist(), .100005, [.025005]*3,
                  np.log([.3, 1.2, .3]).tolist(), .080005, [0, 3, 0])


class NumericalChecks(unittest.TestCase):
    def test_default_device_matches_original_simulator(self):
        # Golden result from the unmodified simulator at commit 068d0ab.
        result = simulate([[0., 8., 16.], [.2, 8.2, 16.2], [.4, 8.4, 16.4]], device(), 35.)
        np.testing.assert_allclose(result['outputs'], [.8869018902144298, 16.516989947772725], atol=1e-12, rtol=0)
        np.testing.assert_allclose(result['final_gain'], [.3, 2.101462281001765, .5466356401171529], atol=1e-12, rtol=0)
        self.assertAlmostEqual(result['final_b'], .38000499999999426, places=12)

    def test_varied_guards_and_leak_match_direct_ode(self):
        arrivals = [[0., 8., 16.], [.2, 8.2, 16.2], [.4, 8.4, 16.4]]
        for mode in ('a22', 'fixed', 'recovery_only'):
            with self.subTest(mode=mode):
                dev = device()
                dev.main_threshold = 1.08
                dev.kappa = .55
                dev.auxiliary_thresholds = [[1.03, .79, .104], [.98, .82, .097], [1.02, .78, .106]]
                fast = simulate(arrivals, dev, 35., mode=mode)
                ode = simulate_ode(arrivals, dev, 35., mode=mode)
                np.testing.assert_allclose(fast['outputs'], ode['outputs'], atol=2e-7, rtol=0)
                np.testing.assert_allclose(fast['final_gain'], ode['final_gain'], atol=2e-7, rtol=0)
                self.assertAlmostEqual(fast['final_b'], ode['final_b'], places=7)

    def test_whole_error_dose_uses_varied_charge_endpoints(self):
        dev = device()
        dev.initial_aux = [0]*3
        dev.initial_m = [.025]*3
        dev.initial_z = np.log([.05]*3).tolist()
        dev.auxiliary_thresholds = [[1.03, .81, .11]]*3
        result = simulate([[0.], [], []], dev, 2.)
        self.assertEqual(result['outputs'], [])
        self.assertAlmostEqual(math.log(result['final_gain'][0]/.05), 8*(.11-.025), places=10)

    def test_whole_mark_dose_uses_varied_charge_endpoints(self):
        dev = device()
        dev.initial_q = .99
        dev.initial_aux = [0]*3
        dev.initial_m = [.025]*3
        dev.initial_z = np.log([4.]*3).tolist()
        dev.auxiliary_thresholds = [[1.03, .81, .11]]*3
        result = simulate([[0.], [], []], dev, 2.)
        self.assertLess(result['outputs'][0], .02)
        self.assertAlmostEqual(result['final_b']-dev.initial_b, .5*(1.03-.81), places=10)

    def test_invalid_threshold_order_is_refused(self):
        dev = device()
        dev.auxiliary_thresholds = [[.8, .9, .1]]*3
        with self.assertRaises(ValueError):
            thresholds(dev)

    def test_same_draw_is_reused_across_arms(self):
        draw = dict(kind='independent_corner', seed=820003, index=2, initial_policy='endpoint_error')
        condition = dict(family='kappa', dispersion=.2, physical_epsilon=.003)
        _, a = study.devices_for(draw, condition)
        before = study.encoded([[d.__dict__ for d in row] for row in a])
        study.allocation_for(a, dict(gains=[1.8]*3, b=1.1))
        _, b = study.devices_for(draw, condition)
        self.assertEqual(before, study.encoded([[d.__dict__ for d in row] for row in b]))

    def test_missing_spikes_have_no_fictitious_zero_interval_error(self):
        result = dict(outputs=[], energy=[0., 0., 0.],
                      snapshots={'230.0': dict(gain=[1., 1., 1.], energy=[0., 0., 0.])})
        run = dict(future=[230., 250., 273.], end=333.,
                   records=[dict(layer=1, lane=0, result=result)])
        metrics = study.measure(run, 1e-7)
        self.assertFalse(metrics['success'])
        self.assertEqual(metrics['missed'], 3)
        self.assertEqual(metrics['missing_interval_pairs'], 2)
        self.assertIsNone(metrics['interval_error_max'])


if __name__ == '__main__':
    unittest.main()
