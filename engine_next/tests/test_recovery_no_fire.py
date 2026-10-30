"""Recovery fallback contracts and a small real learning-gate regression."""
import os
import sys
import unittest
from pathlib import Path
from types import FunctionType, ModuleType, SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'affine'))
os.environ.setdefault('A22_ARTIFACT_DIR', str(ROOT / 'test_diagnostics'))
import engine
import affine_iv
import temporal
import recovery_group

I = engine.I


def _resolver_body(state, group, upper, coarse, cell, count):
    # Bare globals deliberately model A19's helper lookup. The tested wrapper
    # must bind the cache privately without mutating this function's globals.
    return PROBE(return_with_marks, state, group, upper, coarse, cell, count)


def _resolver_join_body(state, group, upper, coarse, cell, count):
    return b.join_states(LEAVES, dict(kind='test-union')), len(LEAVES)


class RecoveryFallbackContracts(unittest.TestCase):
    def setUp(self):
        temporal.begin_producer('recovery-fallback-contracts')
        affine_iv.FRESH = None
        self.b = SimpleNamespace(v=engine.b.v, PROFILE=None)
        self.fire = temporal.Time('fire', I(0))
        self.late = temporal.Time('return', I(1, 2))
        self.state = dict(p=2, fire=self.fire, actuation=(object(),))
        self.joined = dict(p=0, q=I('.1', '.4'), depot=('retained-learning',))
        self.calls = []
        self.resolutions = []
        self.module = ModuleType('branche_retour_A19')

        def original_return(state, key):
            self.calls.append((state, key))
            return self.late

        def probe(helper, state, group, upper, coarse, cell, count):
            self.resolutions.append((group, upper, coarse))
            return self.joined, 3

        self.module.return_with_marks = original_return
        self.module.PROBE = probe
        self.module.resolve = FunctionType(_resolver_body.__code__, self.module.__dict__)

    def event(self, lo, hi, action='error_on', port=0):
        time = temporal.Time('event', I(lo, hi))
        return time, [(action, port, time)]

    def invoke(self, pending, state=None):
        with patch.dict(sys.modules, {'branche_retour_A19': self.module}):
            return recovery_group.no_fire_group(
                self.b, self.state if state is None else state, pending, 0, 'cell', 7)

    def test_complete_transitive_group_stops_before_excluded_event(self):
        pending = [self.event('1.5', '2.5'),
                   self.event('2.4', '3', 'raw_off'),
                   self.event('2.9', '3.4', 'error_off'),
                   self.event('3.5', '3.6', 'raw_on')]
        result = self.invoke(pending)
        self.assertIsNotNone(result)
        self.assertIs(result[0], self.joined)
        self.assertEqual(result[1:], (3, 4, 3))
        group, upper, coarse = self.resolutions[0]
        self.assertEqual(group, pending[:3])
        self.assertEqual(upper, I('3.4').hi)
        self.assertIs(coarse, self.late)

    def test_ineligible_event_reached_only_by_expansion_is_not_skipped(self):
        for action in ('end', 'raw_on', 'mark_on', 'mark_off'):
            with self.subTest(action=action):
                self.resolutions.clear()
                pending = [self.event('1.5', '2.5'), self.event('2.4', '2.6', action)]
                self.assertIsNone(self.invoke(pending))
                self.assertEqual(self.resolutions, [])

    def test_empty_queue_does_not_touch_missing_physical_state(self):
        self.assertIsNone(self.invoke([], state=dict(p=2)))
        self.assertEqual(self.calls, [])

    def test_cache_requires_both_history_identity_and_fire_identity(self):
        original_return = self.module.return_with_marks
        original_globals = self.module.resolve.__globals__

        def probe(helper, state, group, upper, coarse, cell, count):
            self.assertIs(self.module.return_with_marks, original_return)
            self.assertIs(original_globals['return_with_marks'], original_return)
            self.assertIs(helper(state, 'same-state'), self.late)
            self.assertIs(helper(dict(state, fire=state['fire'].copy()), 'same-clock'), self.late)
            self.assertEqual(len(self.calls), 1)  # Initial certified return only.
            helper(dict(state, actuation=(object(),)), 'different-history')
            helper(dict(state, fire=state['fire'].plus('.1')), 'different-fire')
            self.assertEqual([key for _, key in self.calls[1:]],
                             ['different-history', 'different-fire'])
            return self.joined, 1

        self.module.PROBE = probe
        self.assertIsNotNone(self.invoke([self.event('1.5', '2.5')]))
        self.assertIs(self.module.return_with_marks, original_return)
        self.assertIs(original_globals['return_with_marks'], original_return)

    def test_original_globals_remain_unchanged_after_resolver_refusal(self):
        original = self.module.return_with_marks

        def refuse(helper, *args):
            self.assertIs(self.module.return_with_marks, original)
            raise engine.b.v.Ambiguous('additional fire remains possible')

        self.module.PROBE = refuse
        self.assertIsNone(self.invoke([self.event('1.5', '2.5')]))
        self.assertIs(self.module.return_with_marks, original)
        self.assertIs(self.module.resolve.__globals__['return_with_marks'], original)

    def test_nonready_or_threshold_terminal_state_is_rejected(self):
        for phase, charge in ((1, I('.2')), (0, I('.1', 1)), (0, I('1.01'))):
            with self.subTest(phase=phase, charge=charge.pair()):
                self.joined = dict(p=phase, q=charge)
                self.assertIsNone(self.invoke([self.event('1.5', '2.5')]))

    def test_affine_union_is_intersected_with_every_leafs_range(self):
        # Six independent branch remainders: each leaf is below .61, while
        # the common-generator affine union extends above 1. This reproduces
        # the mechanism observed in the layer-16 recovery group.
        leaves = [dict(p=0, q=I('.5') + I.symbol(f'leaf-{j}', '.1')) for j in range(6)]
        broad = affine_iv.hull([x['q'] for x in leaves])
        self.assertGreater(broad.hi, 1)
        self.assertTrue(all(x['q'].hi < 1 for x in leaves))
        self.b.I = I
        self.b.PROFILE = SimpleNamespace(relative_order_proofs=[])
        original_join = lambda states, context: dict(p=0, q=affine_iv.hull([x['q'] for x in states]))
        self.b.join_states = original_join
        self.module.b = self.b
        self.module.LEAVES = leaves
        self.module.resolve = FunctionType(_resolver_join_body.__code__, self.module.__dict__)
        result = self.invoke([self.event('1.5', '2.5')])
        self.assertIsNotNone(result)
        charge = result[0]['q']
        self.assertLess(charge.hi, 1)
        for leaf in leaves:
            self.assertLessEqual(charge.lo, leaf['q'].lo)
            self.assertGreaterEqual(charge.hi, leaf['q'].hi)
        self.assertIs(self.b.join_states, original_join)
        self.assertIs(self.module.b, self.b)
        proof = self.b.PROFILE.relative_order_proofs[-1]['charge_joins'][0]
        self.assertEqual(proof['branches'], len(leaves))
        self.assertEqual(proof['affine_q'], broad.pair())
        self.assertEqual(proof['joined_q'], charge.pair())
        self.assertEqual(proof['leaf_envelope'], charge.pair())


class RecoveryLearning(unittest.TestCase):
    def setUp(self):
        temporal.begin_producer('recovery-learning')
        affine_iv.FRESH = None
        engine.settings_cell('recovery-learning')
        engine.b.PROFILE = None

    def test_real_error_gate_straddles_return_and_learning_is_retained(self):
        b = engine.b
        fire = temporal.Time('fire', I(0))
        now = temporal.Time('now', I('3.25'))
        rate = I('.38')
        ledger = (b.ac.History(rate, fire=fire),)
        gains = [I('.3').ln(), I('1.2').ln(), I('.3').ln()]
        state = dict(t=now, q=b.R*b.ac.bounds(ledger, now, 'ell').exp(),
                     z=gains, b=rate, p=2, raw=[None]*3, aux=[2, 0, 0],
                     mark=[None]*3, err=[None]*3, caps=[False]*3,
                     bstop=False, fire=fire, memory=None, actuation=ledger,
                     depot=tuple((b.dz.History(z),) for z in gains))
        error_on = temporal.Time('error-on', I('3.3', '3.6'))
        error_off = b.shift(error_on, b.DE_PORTS[0], 'error-off')
        pending = [(error_on, [('error_on', 0, error_on)]),
                   (error_off, [('error_off', 0, error_on)])]
        result = recovery_group.no_fire_group(b, state, pending, 0, 'learning', 0)
        self.assertIsNotNone(result)
        joined, stop, handled, orders = result
        self.assertEqual((stop, handled), (2, 3))
        self.assertGreaterEqual(orders, 2)  # ERROR starts on either side of return.
        self.assertEqual(joined['p'], 0)
        self.assertLess(joined['q'].hi, 1)
        self.assertEqual(joined['aux'], [0, 0, 0])
        # An admissible error start at 3.6 follows the return (~3.4113), so
        # the complete .6 log-gain deposit must survive the union. The broad
        # enclosure is allowed to retain the initial value as a lower bound.
        full_learning = gains[0] + I('.6')
        self.assertGreater(joined['z'][0].hi, gains[0].hi)
        self.assertGreaterEqual(joined['z'][0].hi, full_learning.lo)
        for port in (1, 2):
            self.assertEqual(joined['z'][port].fingerprint(), gains[port].fingerprint())


if __name__ == '__main__':
    unittest.main()
