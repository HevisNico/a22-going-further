"""Replay one cell and log every lemma-E _fire_root call (read-only instrumentation)."""
import sys, runpy
from pathlib import Path
engine_dir = Path(sys.argv[1]); sys.path.insert(0, str(engine_dir)); sys.path.insert(0, str(engine_dir/'affine'))
import os, json
os.environ['A22_PHYSICAL_EPSILON'] = json.loads((Path(sys.argv[2])/'campaign.json').read_text())['parameters']['epsilon_relative']
import run; run.initialize(Path(sys.argv[5]))
import commutation
from affine_iv import I
from decimal import Decimal as D
orig = commutation._fire_root
def wrapped(b, s, H, cell, count):
    v, dep = b.v, b.dep; A, K, R = b.A, b.K, b.R
    q = s['q']; J, _, _ = b.coefficients(s); memory = s.get('memory')
    info = dict(count=count, t=[str(x)[:10] for x in s['t'].box().pair()], H=str(H)[:10], q=[str(x)[:10] for x in q.pair()], J=[str(x)[:10] for x in J.pair()], memory=memory is not None)
    try:
        bb = J/(A-K); aa = q-R+bb; info['aa'] = [str(x)[:10] for x in aa.pair()]
        ratio = A*bb/(K*aa); info['ratio'] = [str(x)[:10] for x in ratio.pair()]
        pk = ratio.ln()/(A-K); info['pk'] = [str(x)[:10] for x in pk.pair()]
        probe = lambda u: b.shift(s['t'], u, f'{cell}:{count}:dbg')
        info['memory_max_hi'] = str(dep.evaluate(memory, probe(I(0, H))).hi)[:12]
        hi = min(H, max(D(0), pk.lo)); info['hi'] = str(hi)[:10]
        if hi > 0: info['f_hi'] = [str(x)[:12] for x in (dep.evaluate(memory, probe(I(hi)))-1).pair()]
    except Exception as e: info['err'] = repr(e)[:120]
    r = orig(b, s, H, cell, count); info['result'] = None if r is None else [str(x)[:10] for x in r[0].pair()]
    print('FIRE_ROOT', json.dumps(info), flush=True); return r
commutation._fire_root = wrapped
sys.argv = [sys.argv[0]] + sys.argv[1:]
runpy.run_path(str(Path(__file__).with_name('replay_cell.py')), run_name='__main__')
