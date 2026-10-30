"""Exercise T/T' on either the frozen engine or the next candidate, without modifying either."""
import os
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from decimal import Decimal as D
from scipy.optimize import brentq
import math

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / os.environ.get('A22_TEST_ENGINE', 'engine_eps3e-3')
sys.path.insert(0, str(ROOT / 'affine'))
os.environ.setdefault('A22_ARTIFACT_DIR', str(ROOT / 'test_diagnostics'))
import engine
import affine_iv
import temporal
import relative_root
import relative_return
import branche_retour_A19 as recovery

I = engine.I


class RelativeCoordinates(unittest.TestCase):
    def setUp(self):
        temporal.begin_producer(self.id())
        affine_iv.FRESH = None
        engine.settings_cell(self.id())
        engine.b.PROFILE = None

    def ready_problem(self, shift='0'):
        b = engine.b
        origin = temporal.Time('arrival', I(shift) + I.symbol('common-clock', '.01'))
        memory = b.dep.add(b.dep.start(origin, b.R, []), 0, origin, I(3))
        state = dict(t=origin.plus('.05'))
        probe = lambda u: b.shift(state['t'], u, 'plain-probe')
        f = lambda u: b.dep.evaluate(memory, probe(u))-1
        df = lambda u: b.dep.evaluate(memory, probe(u), True)
        return state, memory, f, df

    def test_ready_root_contains_independent_point_root_and_ignores_common_translation(self):
        a = math.log(4)
        h = lambda u: a/(a-.5)*(math.exp(-.5*u)-math.exp(-a*u))
        expected = brentq(lambda u: .1+3*h(u)-1, 0, 1, xtol=1e-14)-.05
        answers = []
        for shift in ('0', '1000'):
            state, memory, f, df = self.ready_problem(shift)
            root = engine.b.RELATIVE_ROOT(state, memory, f, df, D('.5'), 'test', 0)
            self.assertLessEqual(float(root.lo)-1e-12, expected)
            self.assertGreaterEqual(float(root.hi)+1e-12, expected)
            answers.append(root.pair())
        self.assertEqual(answers[0], answers[1])

    def test_ready_relative_failure_returns_original_certified_root(self):
        state, memory, f, df = self.ready_problem()
        original = engine.v.root(f, df, D(0), D('.5'), engine.v.guessroot(f, D('.5')))
        with patch.object(engine.v, 'root', side_effect=[original, engine.v.Ambiguous('relative refusal')]):
            self.assertIs(engine.b.RELATIVE_ROOT(state, memory, f, df, D('.5'), 'test', 0), original)

    def test_ready_accepts_tighter_coordinates_and_encloses_arrival_endpoints(self):
        b = engine.b
        origin = temporal.Time('arrival', I('.05')+I.symbol('arrival-width', '.05'))
        memory = b.dep.add(b.dep.start(origin, b.R, []), 0, origin, I(3))
        state = dict(t=temporal.Time('now', I('.15')))
        probe = lambda u: b.shift(state['t'], u, 'plain-probe')
        f = lambda u: b.dep.evaluate(memory, probe(u))-1
        df = lambda u: b.dep.evaluate(memory, probe(u), True)
        before = relative_root.STATS['relative_roots']
        root = b.RELATIVE_ROOT(state, memory, f, df, D('.5'), 'test', 0)
        self.assertEqual(relative_root.STATS['relative_roots'], before+1)
        a = math.log(4)
        age = brentq(lambda u: .1+3*a/(a-.5)*(math.exp(-.5*u)-math.exp(-a*u))-1,
                     0, 1, xtol=1e-14)
        self.assertLessEqual(float(root.lo)-1e-12, age-.15)
        self.assertGreaterEqual(float(root.hi)+1e-12, age-.05)

    def test_ready_bracket_disjoint_from_original_monotone_window_is_rejected(self):
        state, memory, f, df = self.ready_problem()
        original = I('.2', '.4')
        with patch.object(engine.v, 'root', side_effect=[original, I(0, '.01')]):
            self.assertIs(engine.b.RELATIVE_ROOT(state, memory, f, df, D('.5'), 'test', 0), original)

    def test_ready_without_non_tail_reference_keeps_original(self):
        state, memory, f, df = self.ready_problem()
        original = I('.3', '.4')
        with patch.object(engine.v, 'root', return_value=original) as root:
            result = engine.b.RELATIVE_ROOT(state, dict(pulses={}), f, df, D('.5'), 'test', 0)
        self.assertIs(result, original)
        self.assertEqual(root.call_count, 1)

    def recovery_state(self, shift='0'):
        b = engine.b
        fire = temporal.Time('fire', I(shift) + I.symbol('common-clock', '.01'))
        mark = fire.plus('.02')
        segment = b.ac.Segment(0, mark, mark, True, b.shift(mark, b.DM_PORTS[0], 'mark-end'), True)
        return dict(fire=fire, actuation=(b.ac.History(I('.5'), fire=fire, marks=(segment,)),))

    def test_recovery_root_contains_closed_form_and_ignores_common_translation(self):
        # Full mark finishes during FAST; recovery is subsequently constant at .6.
        expected = 1+math.log(2.5)/.6
        results = []
        for shift in ('0', '1000'):
            state = self.recovery_state(shift)
            clock = recovery.return_with_marks(state, 'return')
            delta = clock.minus(state['fire'])
            self.assertLessEqual(float(delta.lo)-1e-12, expected)
            self.assertGreaterEqual(float(delta.hi)+1e-12, expected)
            results.append(delta.pair())
        self.assertEqual(results[0], results[1])

    def test_recovery_relative_refusal_and_wider_result_keep_original(self):
        state = self.recovery_state()
        plain = state['fire'].plus(3)
        for outcome in (engine.v.Ambiguous('relative refusal'), I(-100, 100)):
            fake = SimpleNamespace(return_with_marks=lambda *_: plain,
                                   ac=recovery.ac, hull=recovery.hull)
            relative_return.install(engine.b, fake)
            with patch.object(engine.v, 'root', side_effect=[outcome]):
                self.assertIs(fake.return_with_marks(state, 'return'), plain)

    def test_recovery_accepts_a_tighter_real_root_from_a_valid_loose_original(self):
        state = self.recovery_state()
        expected = 1+math.log(2.5)/.6
        plain = engine.b.shift(state['fire'], I(str(expected-.1), str(expected+.1)), 'loose-original')
        fake = SimpleNamespace(return_with_marks=lambda *_: plain,
                               ac=recovery.ac, hull=recovery.hull)
        relative_return.install(engine.b, fake)
        before = relative_return.STATS['relative_returns']
        result = fake.return_with_marks(state, 'return')
        self.assertEqual(relative_return.STATS['relative_returns'], before+1)
        self.assertLess(result.box().width(), plain.box().width())
        duration = result.minus(state['fire'])
        self.assertLessEqual(float(duration.lo)-1e-12, expected)
        self.assertGreaterEqual(float(duration.hi)+1e-12, expected)

    def test_recovery_without_marks_keeps_original(self):
        state = self.recovery_state()
        state['actuation'] = (engine.b.ac.History(I('.5'), fire=state['fire']),)
        plain = state['fire'].plus(3)
        fake = SimpleNamespace(return_with_marks=lambda *_: plain,
                               ac=recovery.ac, hull=recovery.hull)
        relative_return.install(engine.b, fake)
        with patch.object(engine.v, 'root', side_effect=AssertionError('unexpected relative root')):
            self.assertIs(fake.return_with_marks(state, 'return'), plain)


if __name__ == '__main__':
    unittest.main()
