"""Replay one cell, logging pending_window / Fix R outcomes and commutation declines."""
import sys, os, json, runpy, traceback
from pathlib import Path
engine_dir = Path(sys.argv[1]); sys.path.insert(0, str(engine_dir)); sys.path.insert(0, str(engine_dir/'affine'))
os.environ['A22_PHYSICAL_EPSILON'] = json.loads((Path(sys.argv[2])/'campaign.json').read_text())['parameters']['epsilon_relative']
import run; run.initialize(Path(sys.argv[5]))
import cycle_local_A20, recovery_group, engine
orig_pw = cycle_local_A20.pending_window
def pw(s, pending, idx, cell, count):
    try:
        r = orig_pw(s, pending, idx, cell, count)
        print('PENDING_WINDOW ok', count, 'branches', len(r[0].branches), [(len(x.emissions), x.state['p']) for x in r[0].branches][:8], flush=True); return r
    except Exception as e:
        print('PENDING_WINDOW refused', count, type(e).__name__, str(e)[:200], flush=True); raise
cycle_local_A20.pending_window = pw
engine.b.__dict__['pending_window'] = pw
runpy.run_path(str(Path(__file__).with_name('replay_cell.py')), run_name='__main__')
