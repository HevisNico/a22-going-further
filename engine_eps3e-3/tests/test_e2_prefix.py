"""Set-cover regressions for event-relative E2 ordering; no sampling acceptance."""
import os,sys,unittest
from pathlib import Path
from decimal import Decimal as D
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'affine'))
os.environ.setdefault('A22_ARTIFACT_DIR',str(ROOT/'test_diagnostics'))
import engine,commutation,temporal,affine_iv
I=engine.I

class PrefixCover(unittest.TestCase):
    def test_strict_cover_is_complete(self):
        cert=[]
        def f(x):return I('-.01')+I(0,(I(x.width())/10).hi)
        self.assertTrue(commutation._strict_prefix(f,certificate=cert))
        self.assertEqual(D(cert[0][0]),0);self.assertEqual(D(cert[-1][1]),1)
        self.assertTrue(all(D(x[2])<0 for x in cert))
        self.assertTrue(all(a[1]==b[0] for a,b in zip(cert,cert[1:])))
    def test_equality_is_not_discarded(self):
        self.assertFalse(commutation._strict_prefix(lambda x:I(0)))
    def test_hidden_crossing_with_safe_endpoints(self):
        def f(x):return I('.1')-(x-I('.5'))*(x-I('.5'))
        self.assertLess(f(I(0)).hi,0);self.assertLess(f(I(1)).hi,0)
        self.assertFalse(commutation._strict_prefix(f))
    def test_budget_failure_exports_no_partial_certificate(self):
        cert=[]
        self.assertFalse(commutation._strict_prefix(lambda x:I(-1,1),depth=0,certificate=cert))
        self.assertEqual(cert,[])
    def test_actual_early_fire_is_not_ruled_out(self):
        self.assertFalse(commutation._strict_prefix(lambda lam:I('.8')-lam))

class ArrivalClock(unittest.TestCase):
    def setUp(self):
        temporal.begin_producer('e2-prefix-test');affine_iv.FRESH=None
        engine.settings_cell('e2-prefix-test');engine.b.PROFILE=None
    def state(self):
        b=engine.b;t=temporal.Time('now',I(0));g=[I('.3').ln(),I('2.2').ln(),I('.3').ln()]
        s=dict(t=t,q=b.R,z=g,b=I('.08'),p=0,raw=[None]*3,aux=[0]*3,mark=[None]*3,err=[None]*3,caps=[False]*3,bstop=False,fire=None)
        s['memory']=b.new_memory(s);s['actuation']=(b.ac.History(s['b']),)
        s['depot']=tuple((b.dz.History(z),) for z in g)
        return s
    def test_wide_absolute_fire_does_not_imply_mark_overlap(self):
        b=engine.b;s=self.state()
        early=temporal.Time('weak-input',I('.01','.04'))
        center=temporal.Time('strong-input',I('.04','.48'))
        mon=b.shift(center,b.D0_PORTS[1],'mark-on');off=b.shift(mon,b.DM_PORTS[1],'mark-off')
        group=[(early,[('raw_on',0,early),('raw_on',2,early)]),(center,[('raw_on',1,center)]),
               (mon,[('mark_on',1,mon)]),(off,[('mark_off',1,mon)])]
        before=set();rho=commutation._arrival_fire_root(b,s,group,D(1),'synthetic',0,before=before)
        self.assertIsNotNone(rho);self.assertGreater(rho.width(),D('.3'))
        self.assertIn(mon.token(),before);self.assertIn(off.token(),before)
        fire=b.shift(s['t'],rho,'synthetic-fire')
        self.assertLess(off.minus(fire).lo,0);self.assertGreater(off.minus(fire).hi,0)
    def test_ready_error_keeps_original_refusal(self):
        b=engine.b;s=self.state();s['aux'][1]=3
        origin=temporal.Time('input',I('.04','.48'));before=set()
        self.assertIsNone(commutation._arrival_fire_root(b,s,[(origin,[('raw_on',1,origin)])],D(1),'reject',0,before=before))
        self.assertEqual(before,set())
if __name__=='__main__':unittest.main()
