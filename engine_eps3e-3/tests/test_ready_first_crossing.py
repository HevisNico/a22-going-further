"""Strict first-crossing regressions; exact interval arguments, no sampling."""
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
import commutation
import cluster_memory_cover
import nofire_cover
import temporal

I = engine.I


class ReadyFirstCrossing(unittest.TestCase):
    def setUp(self):
        temporal.begin_producer('ready-first-crossing-test')
        affine_iv.FRESH = None
        engine.settings_cell('ready-first-crossing-test')
        engine.b.PROFILE = None

    def synthetic(self, margin, clock=None, derivative=None):
        """Continuous counterfactual charge with an exact shared time origin."""
        clock = clock or temporal.Time('origin', I(0))
        # A deliberately uninformative but valid slope enclosure for the
        # small polynomial examples preserves the slope-free test route.
        derivative = derivative or (lambda x: I(-10, 10))
        b = SimpleNamespace(
            I=I, D=D, shift=temporal.shift, v=engine.b.v,
            PROFILE=SimpleNamespace(relative_order_proofs=[]),
            dep=SimpleNamespace(evaluate=lambda memory, t, deriv=False:
                                derivative(t.minus(clock)) if deriv else 1 + margin(t.minus(clock))))
        return b, dict(p=0, t=clock, memory={}), clock.plus(1)

    def test_shared_uncertain_clock_keeps_relative_first_fire(self):
        b = engine.b
        origin = temporal.Time('wide-arrival', I(10, 11))
        memory = b.dep.start(origin, b.R, [])
        memory = b.dep.add(memory, 0, origin, I('1.8'))
        state = dict(p=0, t=origin.plus('.2'), memory=memory)
        boundary = origin.plus(1)
        fire = nofire_cover.first_fire(b, state, boundary, 'shared', 0)
        self.assertIsNotNone(fire)
        age = fire.minus(origin)
        self.assertLess(age.width(), D('.002'))
        self.assertLess(age.hi, 1)
        self.assertGreater(age.lo, D('.2'))
        # Absolute date boxes overlap widely, yet the actual order is strict.
        self.assertGreater(fire.box().hi, boundary.box().lo)
        self.assertLess(fire.minus(boundary).hi, 0)
        self.assertLessEqual((b.R + I('1.8') * b.dep.pulse(I(age.lo))).lo, 1)
        self.assertGreaterEqual((b.R + I('1.8') * b.dep.pulse(I(age.hi))).hi, 1)

    def test_certain_fire_survives_unusable_legacy_peak_bracket(self):
        b = engine.b
        anchor = temporal.Time('anchor', I(-1))
        now = temporal.Time('now', I('.234'))
        boundary = temporal.Time('boundary', I(1))
        origins = [temporal.Time('left', I('.076', '.194')),
                   temporal.Time('center', I(0, '.19')),
                   temporal.Time('right', I('.076', '.194'))]
        gains = [I('.3'), I('1.2'), I('.3')]
        memory = b.dep.start(anchor, b.R, [])
        for j, origin in enumerate(origins):
            memory = b.dep.add(memory, j, origin, gains[j])
        # These deliberately coarse rectangular bounds include the exact
        # memory charge/current, but lose their common parameter dependence.
        q, current = I('.1', '.9'), I('1.2', '2.4')
        exact_q = b.dep.evaluate(memory, now)
        exact_current = sum((gains[j] * b.A * (-b.A * now.minus(o)).exp()
                             for j, o in enumerate(origins)), I(0))
        self.assertLessEqual(q.lo, exact_q.lo)
        self.assertGreaterEqual(q.hi, exact_q.hi)
        self.assertLessEqual(current.lo, exact_current.lo)
        self.assertGreaterEqual(current.hi, exact_current.hi)
        bb = current / (b.A - b.K)
        peak = (b.A * bb / (b.K * (q - b.R + bb))).ln() / (b.A - b.K)
        legacy_hi = min(boundary.minus(now).hi, peak.lo)
        self.assertLess(b.dep.evaluate(memory, b.shift(now, I(legacy_hi), 'peak')).lo, 1)
        self.assertGreater(b.dep.evaluate(memory, boundary).lo, 1)
        fire = nofire_cover.first_fire(b, dict(p=0, t=now, memory=memory), boundary, 'peak', 0)
        self.assertIsNotNone(fire)
        # Strict physical order comes from the positive boundary margin;
        # an outward root box is allowed to touch the boundary.
        self.assertLessEqual(fire.box().hi, boundary.box().lo)

    def test_strict_start_uses_scalar_pulse_bound_when_affine_overshoots(self):
        b = engine.b
        origin = temporal.Time('pulse-origin', I(0))
        memory = b.dep.add(b.dep.start(origin, b.R, []), 0, origin, I('1.8'))
        start = b.shift(origin, I('.3')+I.symbol('uncertain-start-age', '.29'), 'start')
        boundary = origin.plus(1)
        state = dict(p=0, t=start, memory=memory)
        self.assertGreater(b.dep.evaluate(memory, start).hi, 1)
        self.assertLess(cluster_memory_cover.charge_bound(b, memory, start).hi, 1)
        self.assertGreater(cluster_memory_cover.charge_bound(b, memory, boundary).lo, 1)
        profile = SimpleNamespace(relative_order_proofs=[])
        b.PROFILE = profile
        try:
            fire = nofire_cover.first_fire(b, state, boundary, 'tight-start', 0)
        finally:
            b.PROFILE = None
        self.assertIsNotNone(fire)
        proof = profile.relative_order_proofs[-1]
        self.assertLess(D(proof['start_margin'][1]), 0)
        self.assertGreater(D(proof['boundary_margin'][0]), 0)
        # The fixed physical pulse has its first crossing between .66 and
        # .67; uncertainty concerns only when this READY state is observed.
        self.assertLess((b.R+I('1.8')*b.dep.pulse(I('.66'))).hi, 1)
        self.assertGreater((b.R+I('1.8')*b.dep.pulse(I('.67'))).lo, 1)
        self.assertLess(fire.box().lo, D('.67'))
        self.assertGreater(fire.box().hi, D('.66'))

    def test_commutation_reuses_full_horizon_after_peak_bracket_failure(self):
        b = engine.b
        anchor = temporal.Time('anchor', I(-1))
        now = temporal.Time('now', I('.234'))
        origins = [temporal.Time('left', I('.076', '.194')),
                   temporal.Time('center', I(0, '.19')),
                   temporal.Time('right', I('.076', '.194'))]
        gains = [I('.3'), I('1.2'), I('.3')]
        memory = b.dep.start(anchor, b.R, [])
        for j, origin in enumerate(origins):
            memory = b.dep.add(memory, j, origin, gains[j])
        state = dict(t=now, q=I('.1', '.9'), p=0, memory=memory,
                     z=[g.ln() for g in gains], caps=[False]*3,
                     raw=origins, aux=[2]*3, err=[None]*3,
                     mark=[None]*3, bstop=False)
        # Current is computed by the actual engine, not a mocked bound.
        current, _, _ = b.coefficients(state)
        bb = current / (b.A-b.K)
        peak = (b.A*bb / (b.K*(state['q']-b.R+bb))).ln() / (b.A-b.K)
        margin = lambda u: b.dep.evaluate(memory, b.shift(now, I(u), 'margin'))-1
        self.assertLess(margin(peak.lo).lo, 0)
        self.assertGreater(margin(D('.766')).lo, 0)
        before = commutation.STATS.get('peak_bracket_fallback', 0)
        result = commutation._fire_root(b, state, D('.766'), 'full-horizon', 0)
        self.assertIsNotNone(result)
        self.assertEqual(commutation.STATS['peak_bracket_fallback'], before+1)
        self.assertGreater(result[0].lo, 0)
        self.assertLess(result[0].hi, D('.766'))
        # A possible crossing does not suffice: all parameter points must
        # have crossed at the full endpoint before this fallback may return.
        self.assertLess(margin(D('.61')).lo, 0)
        self.assertGreater(margin(D('.61')).hi, 0)
        self.assertIsNone(commutation._fire_root(b, state, D('.61'), 'uncertain-horizon', 0))
        self.assertEqual(commutation.STATS['peak_bracket_fallback'], before+1)

    def test_nonmonotone_flow_returns_first_of_three_crossings(self):
        b, s, boundary = self.synthetic(
            lambda x: (x-I('.2')) * (x-I('.5')) * (x-I('.8')),
            derivative=lambda x: 3*x*x-3*x+I('.66'))
        fire = nofire_cover.first_fire(b, s, boundary, 'nonmonotone', 0)
        self.assertIsNotNone(fire)
        self.assertLessEqual(fire.box().lo, D('.2'))
        self.assertGreaterEqual(fire.box().hi, D('.2'))
        self.assertLess(fire.box().hi, D('.21'))
        self.assertEqual(b.PROFILE.relative_order_proofs[-1]['route'], 'slope_free_cover')

    def test_e_route_prunes_arrival_certainly_after_first_fire(self):
        b = engine.b
        origin = temporal.Time('admitted-origin', I(0))
        now, late = origin.plus('.2'), origin.plus('.9')
        gains = [I('1.8'), I('.3'), I('.3')]
        memory = b.dep.start(origin, b.R, [])
        memory = b.dep.add(memory, 0, origin, gains[0])
        state = dict(t=now, q=b.dep.evaluate(memory, now), p=0, memory=memory,
                     z=[g.ln() for g in gains], caps=[False]*3,
                     raw=[origin, None, None], aux=[2, 0, 0], err=[None]*3,
                     mark=[origin.plus('.02'), None, None], bstop=False,
                     b=I('.08'), fire=None)
        state['actuation'] = (b.ac.History(state['b']),)
        state['depot'] = tuple((b.dz.History(z),) for z in state['z'])
        profile = SimpleNamespace(relative_order_proofs=[],
                                  guard=lambda *args: None, observe=lambda *args: None)
        b.PROFILE = profile
        try:
            result = commutation._resolve(b, state, [(late, [('raw_on', 1, late)])],
                                          D(1), 'E-position-pruning', 0)
        finally:
            b.PROFILE = None
        self.assertIsNotNone(result)
        joined, fire, branches = result
        self.assertEqual(profile.relative_order_proofs[-1]['route'], 'E')
        self.assertGreater(late.minus(fire).lo, 0)
        self.assertEqual(branches, 1)
        self.assertEqual(joined['p'], 1)
        self.assertEqual(joined['raw'][1].token(), late.token())
        # The discarded alternative would flow from the late arrival
        # backwards to the earlier fire and is physically impossible.
        self.assertLess(fire.minus(late).hi, 0)

    def test_whole_interval_monotonicity_preserves_affine_root(self):
        crossing = I('.5') + I.symbol('crossing-parameter', '.1')
        b, s, boundary = self.synthetic(lambda x: x-crossing, derivative=lambda x: I(1))
        fire = nofire_cover.first_fire(b, s, boundary, 'monotone', 0)
        self.assertIsNotNone(fire)
        self.assertEqual(b.PROFILE.relative_order_proofs[-1]['route'], 'monotone_affine_root')
        # Dependence survives the root calculation, not just its date box.
        residual = fire.minus(s['t']) - crossing
        self.assertLess(residual.width(), D('1e-10'))
        self.assertLessEqual(residual.lo, 0)
        self.assertGreaterEqual(residual.hi, 0)

    def test_failed_monotone_solver_keeps_slope_free_fallback(self):
        b, s, boundary = self.synthetic(lambda x: x-I('.5'), derivative=lambda x: I(1))
        def refuse(*args):
            raise engine.b.v.Ambiguous('synthetic root solver refusal')
        b.v = SimpleNamespace(root=refuse, guessroot=lambda *args: .5, Ambiguous=engine.b.v.Ambiguous)
        fire = nofire_cover.first_fire(b, s, boundary, 'fallback', 0)
        self.assertIsNotNone(fire)
        self.assertEqual(b.PROFILE.relative_order_proofs[-1]['route'], 'slope_free_cover')
        self.assertLessEqual(fire.box().lo, D('.5'))
        self.assertGreaterEqual(fire.box().hi, D('.5'))

    def test_threshold_equality_at_boundary_is_not_strict_order(self):
        b, s, boundary = self.synthetic(lambda x: x-1)
        self.assertIsNone(nofire_cover.first_fire(b, s, boundary, 'equality', 0))

    def test_possible_but_not_certain_endpoint_crossing_refuses(self):
        b, s, boundary = self.synthetic(lambda x: x-I('.9', '1.1'))
        self.assertIsNone(nofire_cover.first_fire(b, s, boundary, 'possible', 0))

    def test_tangency_without_positive_endpoint_refuses(self):
        b, s, boundary = self.synthetic(lambda x: -(x-I('.5'))*(x-I('.5')))
        self.assertIsNone(nofire_cover.first_fire(b, s, boundary, 'tangent', 0))

    def test_missing_strict_subthreshold_start_refuses(self):
        b, s, boundary = self.synthetic(lambda x: x)
        self.assertIsNone(nofire_cover.first_fire(b, s, boundary, 'start-equality', 0))

    def test_nonready_or_missing_memory_refuses(self):
        b, s, boundary = self.synthetic(lambda x: x-I('.5'))
        self.assertIsNone(nofire_cover.first_fire(b, dict(s, p=1), boundary, 'protected', 0))
        self.assertIsNone(nofire_cover.first_fire(b, dict(s, memory=None), boundary, 'no-memory', 0))

    def test_crossing_witness_finds_transient_interior_positive_charge(self):
        f = lambda x: I('.04') - (x-I('.5'))*(x-I('.5'))
        self.assertLess(f(I(0)).hi, 0)
        self.assertLess(f(I(1)).hi, 0)
        witness = commutation._crossing_witness(f, D(1))
        self.assertIsNotNone(witness)
        self.assertGreater(f(I(witness)).lo, 0)
        root = commutation._first_crossing_cover(f, witness)
        self.assertIsNotNone(root)
        self.assertLessEqual(root.lo, D('.3'))
        self.assertGreaterEqual(root.hi, D('.3'))
        self.assertLess(root.hi, D('.31'))

    def test_crossing_witness_requires_whole_parameter_box_above(self):
        amplitude = I('.05') + I.symbol('uncertain-transient-height', '.1')
        f = lambda x: amplitude - (x-I('.5'))*(x-I('.5'))
        self.assertLess(f(I('.5')).lo, 0)
        self.assertGreater(f(I('.5')).hi, 0)
        self.assertIsNone(commutation._crossing_witness(f, D(1)))

    def test_crossing_witness_refuses_without_witness(self):
        self.assertIsNone(commutation._crossing_witness(lambda x: I('-.1'), D(1)))
        self.assertIsNone(commutation._crossing_witness(lambda x: I(1), D(0)))

    def test_finite_grid_missing_a_narrow_peak_does_not_accept(self):
        # There is a true crossing, but no default dyadic candidate proves
        # it. Failure must stay undecided, rather than manufacture a bracket.
        f = lambda x: I('1e-8') - (x-I('.31'))*(x-I('.31'))
        self.assertGreater(f(I('.31')).lo, 0)
        self.assertIsNone(commutation._crossing_witness(f, D(1)))

    def install_refusal_hook(self, margin, error):
        b, s, boundary = self.synthetic(margin, derivative=lambda x: I(1))
        calls = []
        def original(*args):
            raise error
        def flowing(state, at):
            calls.append(('flow', at))
            return dict(state, t=at)
        def fire_reset(state):
            calls.append(('reset', state['t']))
            return dict(state, p=1, memory=None)
        b.advance = original
        b.flowing = flowing
        b.fire_reset = fire_reset
        b.PROFILE.guard = lambda *args: None
        nofire_cover.install(SimpleNamespace(b=b, I=I, D=D, iv=engine.iv))
        return b, s, boundary, calls

    def test_root_bracket_refusal_uses_strict_first_crossing_proof(self):
        error = engine.b.v.Ambiguous('root bracket failed: 0,1')
        b, state, boundary, calls = self.install_refusal_hook(lambda x: x-I('.5'), error)
        result, kind = b.advance(state, boundary, 'hook', 0)
        self.assertEqual(kind, 'fire')
        self.assertEqual(result['p'], 1)
        self.assertEqual(state['p'], 0)
        self.assertEqual([call[0] for call in calls], ['flow', 'reset'])
        proof = b.PROFILE.relative_order_proofs[-1]
        self.assertLess(D(proof['start_margin'][1]), 0)
        self.assertGreater(D(proof['boundary_margin'][0]), 0)
        self.assertLessEqual(result['t'].box().lo, D('.5'))
        self.assertGreaterEqual(result['t'].box().hi, D('.5'))

    def test_root_bracket_refusal_without_strict_crossing_keeps_exception(self):
        # In particular, a subthreshold interval must not be accepted by
        # the older no-fire fallback for this distinct root-solver refusal.
        for threshold in ('.9', '1', '2'):
            error = engine.b.v.Ambiguous('root bracket failed: preserve this instance')
            uncertain = I(threshold, '1.1') if threshold == '.9' else I(threshold)
            b, state, boundary, calls = self.install_refusal_hook(lambda x: x-uncertain, error)
            with self.assertRaises(engine.b.v.Ambiguous) as raised:
                b.advance(state, boundary, 'hook-refuse', 0)
            self.assertIs(raised.exception, error)
            self.assertEqual(calls, [])

    def test_unrelated_ambiguity_does_not_enter_first_crossing_fallback(self):
        error = engine.b.v.Ambiguous('unrelated event-order budget refusal')
        b, state, boundary, calls = self.install_refusal_hook(lambda x: x-I('.5'), error)
        with self.assertRaises(engine.b.v.Ambiguous) as raised:
            b.advance(state, boundary, 'unrelated', 0)
        self.assertIs(raised.exception, error)
        self.assertEqual(calls, [])
        self.assertEqual(b.PROFILE.relative_order_proofs, [])


if __name__ == '__main__':
    unittest.main()
