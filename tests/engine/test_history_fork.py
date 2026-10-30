"""Mixed cap flags and proof records from every leaf survive candidate Fix F."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
NAME = os.environ.get('A22_TEST_ENGINE', 'engine_eps3e-3')
ROOT = REPO / NAME
sys.path.insert(0, str(ROOT / 'affine'))
os.environ.setdefault('A22_ARTIFACT_DIR', str(ROOT / 'test_diagnostics'))
import engine
import affine_iv
import temporal
import artifacts
import fork


@unittest.skipIf(NAME == 'engine_eps3e-3', 'the certified engine is deliberately frozen')
class ForkMergeTests(unittest.TestCase):
    def setUp(self):
        leaf = engine.compute_cell(1, 6, [()]*12, self.id())
        self.leaves = [artifacts.decode(artifacts.Encoder().encode(leaf)) for _ in range(2)]
        engine.b.PROFILE = None
        for index, leaf in enumerate(self.leaves):
            state = leaf['state'];literal = state['terminal_affine']
            cap = index == 0
            depots = list(literal['depot'])
            depots[0] = (engine.b.dz.History(engine.I(4 if cap else 3).ln(), clamped=cap),)
            literal['depot'] = tuple(depots)
            literal['z'][0] = engine.b.dz.bounds(depots[0], literal['t'])
            literal['caps'][0] = cap;state['caps'][0] = cap
            state['g'][0] = literal['z'][0].exp().pair()
            # The artifact encoder interns equal lists. Replace these fields
            # rather than mutating an empty list shared with pending/other views.
            profile = state['width_profile']
            profile['relative_order_proofs'] = profile['relative_order_proofs'] + [dict(guard=f'leaf-{index}')]
            profile['recovery_branch_groups'] = profile['recovery_branch_groups'] + [dict(leaf=index)]

    def merge(self):
        return fork.merge(engine.b, engine, self.leaves, 1, 6)

    def test_summary_is_rebuilt_from_joined_histories_and_all_proofs_survive(self):
        merged = self.merge();state = merged['state'];literal = state['terminal_affine']
        self.assertFalse(state['caps'][0])
        self.assertEqual(state['caps'], literal['caps'])
        self.assertEqual(state['b_stop'], literal['bstop'])
        self.assertEqual(state['gain_stops'], sum(literal['caps']))
        self.assertEqual(state['q'], literal['q'].pair())
        self.assertEqual(state['b'], literal['b'].pair())
        self.assertEqual(state['E'], [50, 100])
        self.assertEqual(len(state['deposit_summary'][0]), 2)
        for leaf in self.leaves:
            lo, hi = map(engine.D, leaf['state']['g'][0])
            self.assertLessEqual(engine.D(state['g'][0][0]), lo)
            self.assertGreaterEqual(engine.D(state['g'][0][1]), hi)
        profile = state['width_profile']
        guards = {p['guard'] for p in profile['relative_order_proofs']}
        self.assertTrue({'leaf-0', 'leaf-1'} <= guards)
        self.assertEqual(profile['recovery_branch_groups'], [dict(leaf=0), dict(leaf=1)])
        reread = artifacts.decode(artifacts.Encoder().encode(merged))
        self.assertEqual(reread['state']['caps'], literal['caps'])

    def test_mixed_terminal_modes_or_clocks_and_missing_states_are_refused(self):
        for change in ('phase', 'auxiliary', 'raw', 'clock', 'pending', 'missing'):
            with self.subTest(change=change):
                self.setUp();state = self.leaves[1]['state']
                if change == 'phase':state['terminal_affine']['p'] = 1
                elif change == 'auxiliary':state['terminal_affine']['aux'] = [3, 0, 0]
                elif change == 'raw':state['terminal_affine']['raw'] = [state['terminal_affine']['t'], None, None]
                elif change == 'clock':state['terminal_affine']['t'] = state['terminal_affine']['t'].plus(1)
                elif change == 'pending':state['pending'] = ['unhandled']
                else:del state['terminal_affine']
                with self.assertRaises(engine.v.Ambiguous):self.merge()

    def test_optional_emission_cannot_be_flattened(self):
        self.leaves[1]['outputs'] = (self.leaves[1]['state']['terminal_affine']['t'],)
        with self.assertRaises(engine.v.Ambiguous):self.merge()

    def test_fork_budget_and_pin_cleanup_are_fail_closed(self):
        fake = type('FakeEngine', (), {})()
        fake.compute_cell = lambda *args: (_ for _ in ()).throw(fork.ForkRequest('clock', fork.MAX_LEAVES+1))
        b = type('FakeKernel', (), dict(v=engine.v, advance=lambda *args: None))()
        fork.install(b, fake)
        with self.assertRaisesRegex(engine.v.Ambiguous, 'budget'):
            fake.compute_cell(1, 0, [()]*12, 'budget')
        self.assertEqual(fork.PINS, {})


if __name__ == '__main__':
    unittest.main()
