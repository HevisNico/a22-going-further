# Controls

| Path | What it is |
|---|---|
| `inclusion_check.py` | Verification control: point-simulated devices, drawn with the falsification-study motifs scaled to the campaign's ε, must fire the same number of times as the certified cells, with every firing date inside its certified box |
| `point_simulator/` | The event-driven point simulator of R (`engine.py`), its network driver and device generator (`campaign.py`), and the independent direct-ODE integrator (`ode_reference.py`), copied unchanged from the point-simulation studies. They also provide fixed-gain and gain-only / recovery-only modes |

The simulator uses floating point and numerical root finding: its outputs are evidence, never
certificates. Requirements: numpy and scipy (versions in `../engine_eps3e-3/requirements.txt`).

```sh
python3 controls/inclusion_check.py <campaign dir> <new inclusion report.json> --per-kind 4
```

The committed report is `results/eps3e-3/controls/inclusion.json` (56 devices, 8 per motif, seed 11).
Preserve it when running new controls. For that sample size and seed, select `--per-kind 8 --seed 11`.

SHA-256 of the copied simulator files, as received:

    d42e0ac03b83d24228f1ec9ea8791d0003109b052b5ed221ea8cb901926469cf  engine.py
    4ef8772451be94f5b07d92bd1cb46856eef5143c35e0ab4b1aec91a1ece5c2de  campaign.py
    c204ddaf68f6881178f5bb1bcd9de3e343931636cf5e7123593aea1b2a3efc92  ode_reference.py
