"""Event-relative READY no-fire covers preserve the actual end boundary."""
import os
import sys
import unittest
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'affine'))
os.environ.setdefault('A22_ARTIFACT_DIR', str(ROOT / 'test_diagnostics'))
import engine
import affine_iv
import cluster_memory_cover
import temporal

I = engine.I


class RelativeClusterCover(unittest.TestCase):
    def setUp(self):
        self.old_fresh = affine_iv.FRESH
        self.old_profile = engine.b.PROFILE
        affine_iv.FRESH = None
        temporal.begin_producer('relative-cluster-test')
        engine.settings_cell('relative-cluster-test')
        engine.b.PROFILE = None

    def tearDown(self):
        affine_iv.FRESH = self.old_fresh
        engine.b.PROFILE = self.old_profile

    def check_uncertain_start(self, fresh):
        b = engine.b
        affine_iv.FRESH = 'relative-cluster-remainder' if fresh else None
        old_count = affine_iv._COUNTER[0]
        origin = temporal.Time('shared-wide-clock', I(10, 11))
        start = b.shift(origin, I(0, '.3'), 'uncertain-start')
        end = origin.plus('.5')
        memory = b.dep.start(origin, b.R + I.symbol('initial-charge', '1e-5'), [])
        memory = b.dep.add(memory, 0, origin, I('1.8')+I.symbol('admitted-gain', '.001'))
        state = dict(p=0, t=start, memory=memory)
        horizon = end.minus(start).nonnegative().hi
        overextended = b.shift(start, I(horizon), 'old-forward-end')
        self.assertGreater(overextended.minus(end).hi, 0)
        self.assertGreater(b.dep.evaluate(memory, overextended).hi, 1)
        self.assertLess(b.dep.evaluate(memory, end).hi, 1)
        profile = SimpleNamespace(relative_order_proofs=[])
        b.PROFILE = profile
        self.assertTrue(cluster_memory_cover.certify(b, state, end))
        proof = profile.relative_order_proofs[-1]
        self.assertEqual(proof['guard'], 'READY_event_relative_no_fire')
        cover = proof['cover']
        self.assertEqual(D(cover[0][0]), 0)
        self.assertEqual(D(cover[-1][1]), 1)
        self.assertTrue(all(D(piece[2]) < 0 for piece in cover))
        self.assertTrue(all(a[1] == z[0] for a, z in zip(cover, cover[1:])))
        if fresh:
            self.assertGreater(affine_iv._COUNTER[0], old_count)

    def test_actual_prefix_safe_while_forward_rectangle_crosses(self):
        self.check_uncertain_start(fresh=False)

    def test_actual_prefix_safe_with_fresh_remainder_symbols(self):
        self.check_uncertain_start(fresh=True)

    def synthetic(self, charge):
        origin = temporal.Time('origin', I(0))
        b = SimpleNamespace(I=I, D=D, shift=temporal.shift, PROFILE=None,
                            dep=SimpleNamespace(evaluate=lambda memory, t: charge(t.minus(origin))))
        # Tail memories deliberately retain the original evaluator; this
        # lets these arbitrary continuous test curves exercise the cover.
        memory = {'pulses': {'synthetic': {'tail': True}}}
        return b, dict(p=0, t=origin, memory=memory), origin.plus(1)

    def test_interior_crossing_with_safe_endpoints_refuses(self):
        charge = lambda x: I('1.1')-(x-I('.5'))*(x-I('.5'))
        self.assertLess(charge(I(0)).hi, 1)
        self.assertLess(charge(I(1)).hi, 1)
        self.assertGreater(charge(I('.5')).lo, 1)
        b, state, end = self.synthetic(charge)
        self.assertFalse(cluster_memory_cover.certify(b, state, end))

    def test_threshold_equality_refuses(self):
        b, state, end = self.synthetic(lambda x: I('.5')+x/2)
        self.assertFalse(cluster_memory_cover.certify(b, state, end))

    def test_scalar_pulse_envelope_tightens_only_guard_bound(self):
        b = engine.b
        origin = temporal.Time('origin', I(0))
        gain = I('1.3')
        memory = b.dep.add(b.dep.start(origin, b.R, []), 0, origin, gain)
        probe = temporal.Time('wide-pulse-age', I('.5')+I.symbol('age', '.4'))
        affine = b.dep.evaluate(memory, probe)
        self.assertGreater(affine.hi, 1)
        bound = cluster_memory_cover.charge_bound(b, memory, probe)
        self.assertLess(bound.hi, 1)
        self.assertLess(bound.width(), affine.width())
        self.assertGreaterEqual(bound.lo, affine.lo)
        self.assertLessEqual(bound.hi, affine.hi)
        # The scalar response is increasing on this entire age interval.
        # Check its endpoint enclosures and interior values as regressions;
        # acceptance itself uses the full interval, never these test points.
        for age in ('.1', '.3', '.5', '.7', '.9'):
            value = b.R+gain*b.dep.pulse(I(age))
            self.assertLessEqual(bound.lo, value.lo)
            self.assertGreaterEqual(bound.hi, value.hi)
        self.assertIs(memory['pulses'][(0, origin.token())]['g'], gain)
        self.assertGreater(b.dep.evaluate(memory, probe).hi, 1)

    def test_tail_memory_keeps_original_affine_evaluator(self):
        b = engine.b
        origin = temporal.Time('origin', I(0))
        anchor = origin.plus('.2')
        memory = b.dep.start(anchor, b.R, [(0, origin, I('1.3'))])
        probe = b.shift(anchor, I('.1')+I.symbol('tail-age', '.02'), 'tail-probe')
        self.assertTrue(next(iter(memory['pulses'].values()))['tail'])
        original = b.dep.evaluate(memory, probe)
        bound = cluster_memory_cover.charge_bound(b, memory, probe)
        self.assertEqual(bound.fingerprint(), original.fingerprint())


if __name__ == '__main__':
    unittest.main()
