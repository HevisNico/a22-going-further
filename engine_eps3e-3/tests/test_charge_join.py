"""Union preservation, threshold neutrality, and learning-history regression."""
from pathlib import Path
import os, sys, unittest
from types import SimpleNamespace
from decimal import Decimal as D
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'affine'))
os.environ.setdefault('A22_ARTIFACT_DIR',str(ROOT/'test_diagnostics'))
import engine, affine_iv as af, temporal, charge_join
I=af.I


class ChargeJoin(unittest.TestCase):
    def setUp(self):
        self.fresh=af.FRESH
        af.FRESH=None
        temporal.begin_producer('charge-join-tests')
        engine.settings_cell('charge-join-tests')
        self.now=temporal.Time('join-clock',I(3))

    def tearDown(self):
        af.FRESH=self.fresh

    def adapter(self):
        def original(states,context):
            return dict(states[0],q=af.hull([s['q'] for s in states]),
                        histories=tuple(s['history'] for s in states))
        b=SimpleNamespace(I=I,join_states=original,
                          PROFILE=SimpleNamespace(relative_order_proofs=[]))
        charge_join.install(b)
        return b

    def states(self,values):
        return [dict(t=self.now,q=q,history=object()) for q in values]

    def test_entire_union_is_kept_both_remainder_modes(self):
        for fresh in (None,'charge-join-remainders'):
            af.FRESH=fresh
            b=self.adapter()
            values=[I('.8')+I.symbol('a','.1'),I('.8')+I.symbol('b','.1')]
            states=self.states(values)
            original=af.hull(values)
            self.assertGreaterEqual(original.hi,D(1))
            result=b.join_states(states,{'kind':'test'})
            self.assertLess(result['q'].hi,D(1))
            self.assertEqual(result['q'].lo,min(x.lo for x in values))
            self.assertEqual(result['q'].hi,max(x.hi for x in values))
            self.assertEqual(result['histories'],tuple(s['history'] for s in states))
            self.assertTrue(all(s['q'] is q for s,q in zip(states,values)))
            self.assertEqual(len(b.PROFILE.relative_order_proofs),1)

    def test_real_threshold_overlap_is_not_removed(self):
        b=self.adapter()
        values=[I('.8')+I.symbol('a','.1'),I('1.2')+I.symbol('b','.1')]
        out=b.join_states(self.states(values),{})
        self.assertGreater(out['q'].hi,D('1.3'))
        self.assertLessEqual(out['q'].lo,min(q.lo for q in values))

    def test_negative_values_are_not_projected_to_a_physical_guess(self):
        b=self.adapter()
        values=[I('-.8')+I.symbol('a','.1'),I('-.8')+I.symbol('b','.1')]
        out=b.join_states(self.states(values),{})
        self.assertLess(out['q'].hi,0)
        self.assertEqual(out['q'].lo,min(q.lo for q in values))

    def test_unchanged_affine_union_retains_shared_dependence(self):
        b=self.adapter();q=I('.8')+I.symbol('shared','.1')
        out=b.join_states(self.states([q,q]),{})
        self.assertIs(out['q'],q)
        self.assertIn('shared',out['q'].d)
        self.assertEqual(b.PROFILE.relative_order_proofs,[])

    def test_real_join_preserves_both_learning_and_actuation_histories(self):
        b=engine.b;profile=b.PROFILE;b.PROFILE=None
        try:
            histories=[b.ac.History(I('.08')),b.ac.History(I('.09'))]
            deposits=[tuple((b.dz.History(I(z).ln()),) for z in zs)
                      for zs in [('.3','1.2','.3'),('.4','1.3','.4')]]
            states=[dict(t=self.now,p=0,q=I('.8')+I.symbol(key,'.1'),
                         actuation=(h,),depot=d,memory=None)
                    for key,h,d in zip(('a','b'),histories,deposits)]
            before=[s['q'].fingerprint() for s in states]
            out=b.join_states(states,{'kind':'learning-regression'})
            self.assertLess(out['q'].hi,1)
            self.assertEqual(set(map(id,out['actuation'])),set(map(id,histories)))
            for j in range(3):
                self.assertEqual(set(map(id,out['depot'][j])),
                                 {id(d[j][0]) for d in deposits})
            self.assertIsNone(out['memory'])
            self.assertEqual(before,[s['q'].fingerprint() for s in states])
        finally:
            b.PROFILE=profile

    def test_empty_ready_memory_restores_residual_instead_of_resetting_to_rest(self):
        b=self.adapter();b.dep=engine.b.dep
        q=I('.2')+I.symbol('residual','.01')
        states=self.states([q,q])
        for s in states:s.update(p=0,memory=None,raw=[None]*3)
        out=b.join_states(states,{})
        self.assertIs(out['memory']['q'],q)
        self.assertIs(out['memory']['anchor'],self.now)
        self.assertEqual(out['memory']['pulses'],{})
        at=self.now.plus(2)
        expected=engine.b.R+(q-engine.b.R)*(-engine.b.K*I(2)).exp()
        actual=b.dep.evaluate(out['memory'],at)
        self.assertLess((actual-expected).width(),D('1e-12'))
        self.assertGreater(actual.lo,engine.b.R.hi)
        # The input states and their disjunction were not overwritten.
        self.assertTrue(all(s['memory'] is None for s in states))

    def test_memory_repair_does_not_assume_empty_or_ready_or_replace_existing_memory(self):
        b=self.adapter();b.dep=engine.b.dep
        for phase,raw,memory in [(1,[None]*3,None),(0,[self.now,None,None],None),
                                 (0,[None]*3,{'existing':'memory'})]:
            states=self.states([I('.2')])
            states[0].update(p=phase,raw=raw,memory=memory)
            out=b.join_states(states,{})
            self.assertIs(out['memory'],memory)


if __name__=='__main__':unittest.main()
