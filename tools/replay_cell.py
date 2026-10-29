"""Replay one cell of a campaign from its parents' recorded outputs and report commutation declines."""
import sys, os, json, traceback
from pathlib import Path
engine_dir, campaign, layer, lane = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
os.environ['A22_PHYSICAL_EPSILON'] = json.loads((campaign/'campaign.json').read_text())['parameters']['epsilon_relative']
sys.path.insert(0, str(engine_dir)); sys.path.insert(0, str(engine_dir/'affine'))
import run
engine, a, t = run.initialize(Path(sys.argv[5]))
run_id = json.loads((campaign/'campaign.json').read_text())['run_id']
trains = []
for j in range(12):
    if j not in {(lane-1) % 12, lane, (lane+1) % 12}: trains.append(()); continue
    d = campaign/f'layer_{layer-1:02d}'/f'cell_{j:02d}'
    r = json.loads((d/'receipt.json').read_text())
    trains.append(a.read(d/'result.json', r['payload_sha256'])['outputs'])
import commutation
try:
    res = engine.compute_cell(layer, lane, trains, run_id+f'/replay/{layer}/{lane}')
    print('ACCEPTED')
except BaseException as e:
    print("REFUSED", type(e).__name__, e); traceback.print_exc(limit=-4)
print('commutation', json.dumps(commutation.STATS, indent=1))
