"""A tighter root may resolve a fast-window refusal; it may not waive it."""
import os, sys, unittest
from pathlib import Path
from decimal import Decimal as D
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'affine'))
os.environ.setdefault('A22_ARTIFACT_DIR',str(ROOT/'test_diagnostics'))
import engine, affine_iv as af, temporal, commutation
I=af.I


class FastWindowRetry(unittest.TestCase):
    def setUp(self):
        self.old_fresh=af.FRESH;self.old_profile=engine.b.PROFILE
        af.FRESH=None;engine.b.PROFILE=None
        temporal.begin_producer('fast-window-tests')
        engine.settings_cell('fast-window-tests')

    def tearDown(self):
        af.FRESH=self.old_fresh;engine.b.PROFILE=self.old_profile

    def recovery_events(self):
        b=engine.b;o=temporal.Time('arrival',I(0));now=o.plus('.2')
        memory=b.dep.add(b.dep.start(o,b.R,[]),0,o,I('1.8'))
        state=dict(t=now,p=0,q=b.dep.evaluate(memory,now),memory=memory,
                   z=[I(g).ln() for g in ('1.8','.3','.3')],caps=[False]*3,
                   raw=[o,None,None],aux=[2,0,0],err=[None]*3,
                   mark=[o.plus('.02'),None,None],bstop=False,b=I('.08'),fire=None)
        state['actuation']=(b.ac.History(state['b']),)
        state['depot']=tuple((b.dz.History(z),) for z in state['z'])
        err=o.plus('1.1')
        group=[(o.plus(1),[('raw_off',0,o)]),
               (err,[('error_on',0,err)]),
               (o.plus('1.25'),[('error_off',0,err)])]
        return state,group

    def resolve_with_roots(self,coarse,tight):
        state,group=self.recovery_events();calls=[]
        def root(*args,**kwargs):
            use_tight=kwargs.get('tight',False);calls.append(use_tight)
            return (tight if use_tight else coarse),lambda u:I(1)
        with patch.object(commutation,'_fire_root',side_effect=root):
            result=commutation._resolve(engine.b,state,group,D(2),'retry-test',0)
        return result,calls,group

    def test_retry_retains_original_strict_fast_section_check(self):
        # The true one-pulse crossing is near .665; both enclosures contain
        # it, but the first one cannot certify completion of the event group.
        result,calls,group=self.resolve_with_roots(I(0,'.8'),I('.45','.48'))
        self.assertIsNotNone(result);self.assertEqual(calls,[False,True])
        joined,fire,_=result
        self.assertGreater(fire.plus(1).box().lo,max(t.box().hi for t,_ in group))
        self.assertEqual(joined['p'],1)
        self.assertEqual(joined['aux'],[0,0,0])

    def test_retry_still_refuses_a_window_without_strict_margin(self):
        result,calls,_=self.resolve_with_roots(I(0,'.8'),I(0,'.8'))
        self.assertIsNone(result);self.assertEqual(calls,[False,True])

    def test_already_accepted_window_does_not_enter_retry(self):
        result,calls,_=self.resolve_with_roots(I('.45','.48'),I(0,'.8'))
        self.assertIsNotNone(result);self.assertEqual(calls,[False])

    def test_real_pulse_intersection_tightens_first_crossing(self):
        b=engine.b;T=temporal.Time
        origins=[T('left',I('-.146807')+I.symbol('left-clock','.106686')),
                 T('center',I('-.47320421','-.08331163')),
                 T('right',I('-.146818')+I.symbol('right-clock','.106694'))]
        gains=[I('.3'),I('1.2'),I('.3')];now=T('now',I(0))
        mem=b.dep.start(T('anchor',I(-4)),b.R,[])
        for j,o in enumerate(origins):mem=b.dep.add(mem,j,o,gains[j])
        state=dict(p=0,t=now,q=b.dep.evaluate(mem,now),memory=mem,
                   z=[g.ln() for g in gains],caps=[False]*3,raw=origins,
                   aux=[2]*3,err=[None]*3,mark=[None]*3,bstop=False)
        coarse,_=commutation._fire_root(b,state,D('.999999999'),'pulse-test',0)
        tight,_=commutation._fire_root(b,state,D('.999999999'),'pulse-test',0,tight=True)
        self.assertGreater(tight.lo,coarse.lo)
        self.assertLess(tight.hi,coarse.hi)
        # Endpoint devices are independent checks, not the acceptance rule.
        for mask in range(8):
            selected=[o.box().hi if mask&(1<<j) else o.box().lo for j,o in enumerate(origins)]
            def charge(at):
                return b.R+sum((g*b.dep.pulse(I(at-t)) for g,t in zip(gains,selected)),I(0))
            self.assertLess(charge(tight.lo).hi,1)
            self.assertGreater(charge(tight.hi).lo,1)
        self.assertIsNone(commutation._fire_root(b,state,D('.1'),'too-short',0,tight=True))


if __name__=='__main__':unittest.main()
