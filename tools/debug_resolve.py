"""Replay one cell, printing the traceback of any exception inside commutation._resolve."""
import sys, os, json, runpy, traceback
from pathlib import Path
engine_dir = Path(sys.argv[1]); sys.path.insert(0, str(engine_dir)); sys.path.insert(0, str(engine_dir/'affine'))
os.environ['A22_PHYSICAL_EPSILON'] = json.loads((Path(sys.argv[2])/'campaign.json').read_text())['parameters']['epsilon_relative']
import run; run.initialize(Path(sys.argv[5]))
import commutation
orig = commutation._resolve
def wrapped(*a, **k):
    try:
        return orig(*a, **k)
    except commutation._Extend:
        raise
    except Exception:
        traceback.print_exc(limit=-6); raise
commutation._resolve = wrapped
runpy.run_path(str(Path(__file__).with_name('replay_cell.py')), run_name='__main__')
