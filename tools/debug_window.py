"""Replay one cell, logging the local-cycle window widths and the recovery state where it refuses."""
import sys, os, json, runpy
from pathlib import Path
engine_dir = Path(sys.argv[1]); sys.path.insert(0, str(engine_dir)); sys.path.insert(0, str(engine_dir/'affine'))
os.environ['A22_PHYSICAL_EPSILON'] = json.loads((Path(sys.argv[2])/'campaign.json').read_text())['parameters']['epsilon_relative']
import run; run.initialize(Path(sys.argv[5]))
import cycle_local_A20
orig = cycle_local_A20.no_new_fire_bound
def logged(coarse, upper):
    print('WINDOW coarse', [str(x)[:10] for x in coarse.box().pair()], 'upper', str(upper)[:10], flush=True)
    return orig(coarse, upper)
cycle_local_A20.no_new_fire_bound = logged
orig_pw = cycle_local_A20.pending_window
def pw(s, pending, idx, cell, count):
    print('STATE p', s['p'], 't', [str(x)[:10] for x in s['t'].box().pair()], 'b', [str(x)[:8] for x in s['b'].pair()],
          'histories', len(s['actuation']), 'next events', [(str(t.box().lo)[:8], [a for a, _, _ in acts]) for t, acts in pending[idx:idx+4]], flush=True)
    return orig_pw(s, pending, idx, cell, count)
cycle_local_A20.pending_window = pw
runpy.run_path(str(Path(__file__).with_name('replay_cell.py')), run_name='__main__')
