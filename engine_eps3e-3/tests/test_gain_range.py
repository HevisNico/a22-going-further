"""Local admission gain bounds preserve learning state and global correlations."""
import os
import sys
import unittest
from decimal import Decimal as D, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'affine'))
os.environ.setdefault('A22_ARTIFACT_DIR', str(ROOT / 'test_diagnostics'))
import engine
import affine_iv
import artifacts
import gain_range
import temporal

I = engine.I


class AdmissionGainRange(unittest.TestCase):
    def setUp(self):
        self.old_fresh = affine_iv.FRESH
        self.old_profile = engine.b.PROFILE
        affine_iv.FRESH = None
        temporal.begin_producer('gain-range-test')
        engine.settings_cell('gain-range-test')
        engine.b.PROFILE = None

    def tearDown(self):
        affine_iv.FRESH = self.old_fresh
        engine.b.PROFILE = self.old_profile

    def wide_log_gain(self):
        return I('.1823615567939546262', '.5377610122466839') + I.symbol('learning-log-gain', '.00005')

    def state(self):
        b = engine.b
        origin = temporal.Time('older-arrival', I(0))
        now = origin.plus('.2')
        z = [I('.3').ln(), self.wide_log_gain(), I('.3').ln()]
        memory = b.dep.add(b.dep.start(origin, b.R, []), 0, origin, I('.3'))
        s = dict(t=now, q=b.dep.evaluate(memory, now), z=z, b=I('.08'),
                 p=0, raw=[origin, None, None], aux=[2, 0, 0],
                 mark=[origin.plus('.02'), None, None], err=[None]*3,
                 caps=[False]*3, bstop=False, fire=None, memory=memory)
        s['actuation'] = (b.ac.History(s['b']),)
        s['depot'] = tuple((b.dz.History(value),) for value in z)
        return s

    def test_wide_exp_tightening_contains_exact_monotone_range_both_modes(self):
        for fresh in (None, 'gain-bound-remainder'):
            with self.subTest(fresh=fresh):
                affine_iv.FRESH = fresh
                z = self.wide_log_gain()
                old = z.exp()
                bound = gain_range.enclose(old, z)
                self.assertGreater(bound.lo, old.lo)
                self.assertLess(bound.hi, old.hi)
                scalar = z.plain().exp()
                self.assertGreaterEqual(bound.lo, scalar.lo)
                self.assertLessEqual(bound.hi, scalar.hi)
                with localcontext() as ctx:
                    ctx.prec = 400
                    low_truth, high_truth = z.lo.exp(), z.hi.exp()
                self.assertLessEqual(bound.lo, low_truth)
                self.assertGreaterEqual(bound.hi, high_truth)

    def test_admission_preserves_old_state_memory_and_pulses_both_modes(self):
        b = engine.b
        for fresh in (None, 'admission-remainder'):
            with self.subTest(fresh=fresh):
                affine_iv.FRESH = fresh
                s = self.state()
                before = artifacts.canonical_hash(artifacts.Encoder().encode(s))
                old_memory = s['memory']
                old_key, old_term = next(iter(old_memory['pulses'].items()))
                old_z, old_depot = s['z'], s['depot']
                incoming = s['t']
                out = b.act(s, [('raw_on', 1, incoming)])
                new = out['memory']['pulses'][(1, incoming.token())]['g']
                self.assertEqual(before, artifacts.canonical_hash(artifacts.Encoder().encode(s)))
                self.assertIs(s['memory'], old_memory)
                self.assertIs(s['z'], old_z)
                self.assertIs(s['depot'], old_depot)
                self.assertIs(out['memory']['pulses'][old_key], old_term)
                self.assertNotIn((1, incoming.token()), old_memory['pulses'])
                self.assertGreaterEqual(new.lo, s['z'][1].plain().exp().lo)
                self.assertLessEqual(new.hi, s['z'][1].plain().exp().hi)

    def test_capped_gain_is_left_as_physical_cap(self):
        b = engine.b
        s = self.state()
        s['caps'][1] = True
        s['z'][1] = b.Z
        s['depot'] = tuple((b.dz.History(b.Z, clamped=True),) if j == 1 else hs
                           for j, hs in enumerate(s['depot']))
        origin = s['t']
        out = b.act(s, [('raw_on', 1, origin)])
        self.assertIs(out['memory']['pulses'][(1, origin.token())]['g'], b.C)
        self.assertIs(b.new_memory(out)['pulses'][(1, origin.token())]['g'], b.C)

    def test_protected_arrival_does_not_admit_a_pulse(self):
        b = engine.b
        s = self.state()
        s.update(p=1, memory=None, fire=s['t'])
        incoming = s['t']
        out = b.act(s, [('raw_on', 1, incoming)])
        self.assertIsNone(out['memory'])
        self.assertEqual(out['raw'][1].token(), incoming.token())
        self.assertEqual(out['p'], 1)

    def test_tail_reconstruction_uses_current_log_gain_without_mutation(self):
        b = engine.b
        s = self.state()
        s['raw'][1] = s['t'].plus('-.1')
        before = artifacts.canonical_hash(artifacts.Encoder().encode(s))
        memory = b.new_memory(s)
        term = memory['pulses'][(1, s['raw'][1].token())]
        self.assertTrue(term['tail'])
        self.assertEqual(memory['anchor'].token(), s['t'].token())
        scalar = s['z'][1].plain().exp()
        self.assertGreaterEqual(term['g'].lo, scalar.lo)
        self.assertLessEqual(term['g'].hi, scalar.hi)
        self.assertEqual(before, artifacts.canonical_hash(artifacts.Encoder().encode(s)))

    def test_global_exponential_keeps_affine_dependence_both_modes(self):
        for fresh in (None, 'ordinary-exp-remainder'):
            with self.subTest(fresh=fresh):
                affine_iv.FRESH = fresh
                x = I.symbol('small-input', '.01')
                value = x.exp()
                self.assertIn('small-input', value.d)
                self.assertLess((value-(1+x)).width(), D('.0003'))
                self.assertIs(gain_range.enclose(value, x), value)

    def test_routine_narrow_gain_keeps_original_correlated_form(self):
        for fresh in (None, 'narrow-admission-remainder'):
            for radius in ('1e-5', '.001', '.01'):
                with self.subTest(fresh=fresh, radius=radius):
                    affine_iv.FRESH = fresh
                    z = I('1.2').ln()+I.symbol('narrow-log-gain', radius)
                    original = z.exp()
                    self.assertIs(gain_range.enclose(original, z), original)
                    self.assertIn('narrow-log-gain', original.d)


if __name__ == '__main__':
    unittest.main()
