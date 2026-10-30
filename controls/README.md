# Controls

| Path | What it is |
|---|---|
| `inclusion_check.py` | Verification control: point-simulated devices, drawn with the falsification-study motifs scaled to the campaign's ε, must fire the same number of times as the certified cells, with every firing date inside its certified box |
| `point_simulator/` | The event-driven point simulator of R (`engine.py`), its network driver and device generator (`campaign.py`), and the independent direct-ODE integrator (`ode_reference.py`). Defaults retain R; optional per-cell trigger/leak and per-port auxiliary thresholds support exploratory numerical families. Fixed-gain and gain-only / recovery-only modes support scientific controls |
| `learning_study/` | A predeclared paired pilot, disjoint calibration/evaluation devices, fixed preset selection, simulator cross-checks and a numerical operating map; see its protocol and README |

The simulator uses floating point and numerical root finding: its outputs are evidence, never
certificates. Requirements: numpy and scipy (versions in `../engine/requirements.txt`).

```sh
python3 controls/inclusion_check.py <campaign dir> results/<box>/controls/inclusion.json --per-kind 4
```

SHA-256 of the original simulator files as received (before the optional exploratory extensions;
these are provenance hashes, not checksums of the extended files):

    d42e0ac03b83d24228f1ec9ea8791d0003109b052b5ed221ea8cb901926469cf  engine.py
    4ef8772451be94f5b07d92bd1cb46856eef5143c35e0ab4b1aec91a1ece5c2de  campaign.py
    c204ddaf68f6881178f5bb1bcd9de3e343931636cf5e7123593aea1b2a3efc92  ode_reference.py
