"""Replay one cell, printing the actuation histories at each pending_window call."""
import sys, os, json, runpy
from pathlib import Path
engine_dir = Path(sys.argv[1]); sys.path.insert(0, str(engine_dir)); sys.path.insert(0, str(engine_dir/'affine'))
os.environ['A22_PHYSICAL_EPSILON'] = json.loads((Path(sys.argv[2])/'campaign.json').read_text())['parameters']['epsilon_relative']
import run; run.initialize(Path(sys.argv[5]))
import cycle_local_A20, engine
ac = engine.b.ac
orig = cycle_local_A20.pending_window
def pw(s, pending, idx, cell, count):
    for k, h in enumerate(s['actuation']):
        print('HIST', k, 'initial', [str(x)[:8] for x in h.initial.pair()], 'full', h.full, 'partial', len(h.partial),
              'marks', len(h.marks), 'baseline', [str(x)[:8] for x in ac.baseline(h).pair()],
              'partials', [[str(x)[:8] for x in ac.transfer(p).pair()] for p in h.partial],
              'fire', [str(x)[:9] for x in h.fire.box().pair()] if h.fire else None,
              'mk', [(m.port, [str(x)[:9] for x in m.origin.box().pair()], [str(x)[:9] for x in m.start.box().pair()], m.full_start,
                      None if m.end is None else [str(x)[:9] for x in m.end.box().pair()], m.full_end) for m in h.marks],
              't', [str(x)[:9] for x in s['t'].box().pair()],
              'rate', [str(x)[:8] for x in ac.rate(h, s['t']).pair()], 'ell', [str(x)[:8] for x in ac.ell(h, s['t']).pair()], flush=True)
    return orig(s, pending, idx, cell, count)
cycle_local_A20.pending_window = pw
runpy.run_path(str(Path(__file__).with_name('replay_cell.py')), run_name='__main__')
