# Paired learning controls and exploratory parameter families

This is a numerical pilot, not an interval certificate. The physical kernel and verification
engine are unchanged. The source protocol is [`protocol.json`](protocol.json); its exact copy,
hash and simulator source hashes are recorded before the campaign starts. Results are interpreted
in [`REPORT.md`](REPORT.md).

## Comparison

Each condition uses two calibration devices and four different evaluation devices. Every arm
receives the same physical device and initial state, checked by a device fingerprint:

1. **Learning:** gain and recovery learning, unchanged R at default thresholds/leak.
2. **Initial frozen:** original initial gains and recovery, both frozen.
3. **Initial gains, recovery learns:** gain learning disabled, recovery learning retained. This
   separates the absence of gain adaptation from the absence of recovery adaptation.
4. **Calibrated fixed:** a fixed allocation chosen on calibration devices only. Candidate presets
   include five uniform gains, one port-role allocation and two cell/port templates fitted to
   calibration devices' learned gains. The same selected command is applied to all evaluation
   devices of a condition, with the device's physical cap applied. Recovery is fixed at 1.1.

The template is a strong offline baseline, not a hand allocation obtained without examples.
Selection favors transmission success first, then fewer missing/extra spikes and failing cells,
then smaller average gain. Calibration and evaluation outcomes are both retained. No claim is
made that the finite candidate grid finds the best possible fixed network. Conditions may use
different presets; there is no per-evaluation-device retuning.

The 28 training pulses remain at 0,8,...,216. Six future source pulses begin at 230 with gaps
20,23,41,20,31. The primary test includes every future pulse. A separate secondary test treats
the pulse at 230 as conditioning and evaluates the five remaining pulses. It never replaces a
failed primary test. The absolute interval-error criterion is 1e-7 simulation time units.
Missing intervals are counted as missing and their error is not fabricated as zero.

## Exploratory device definitions

- **Main trigger:** one threshold per cell; the trigger guard varies, while the active reset
  stays at q=1 and the outgoing pulse remains canonical with duration 1. These experiments do not
  cover variation of the reset level or outgoing pulse amplitude/duration.
- **Leak:** one positive coefficient per cell, shared by that cell's main and three auxiliary
  READY equations. The tested range remains below a=ln(4).
- **Auxiliary thresholds:** three independently varied transition charges per port: the firing
  level, MARK end and SILENT end / ERROR start. Rest and actuator factors stay fixed. The MARK
  dose is therefore (firing level - MARK end)/2 and the ERROR dose is
  8*(ERROR start - .025). These are integrated using the actual varied charge endpoints.

The five original per-port parameters also vary independently at ±0.3% in each added-parameter
condition. Separate original-parameter conditions examine ±0.3%, ±1%, ±3% and ±10%.
These percentages are experimental dispersions, not measured manufacturing tolerances.

## Reproduce

Python 3.12, numpy and scipy as pinned in `../../engine/requirements.txt`. From the repository root:

```sh
python -B -m unittest discover -s controls/learning_study -p 'test_*.py'
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -B controls/learning_study/run.py --out /path/new_pilot --workers 4
python -B controls/learning_study/crosscheck.py /path/new_pilot
python -B controls/learning_study/supplement_uniform.py /path/new_pilot --workers 4
python -B controls/learning_study/analyze.py /path/new_pilot
```

The last command additionally needs matplotlib to render the PNG/PDF map. `run.py` refuses to
overwrite an existing output directory. It saves every outcome, including simulator errors, and
every device, spike train and training-terminal state in `runs.jsonl.gz`. `summary.json` retains
candidate-selection scores and evaluation metrics. `analyze.py` checks pairing and a conservative
instantaneous work bound below 500, sufficient to retain the original open energy gates.
`crosscheck.py` independently integrates selected cells with the direct ODE backend, prioritizing
failing devices. Its parents' inputs are those of the fast network: this is a local cross-check,
not an independent full-network reproduction.

The optional `supplement_uniform.py` is a clearly labeled post-hoc control: it applies the largest
uniform gain already present in the candidate grid (3.2) to every held-out device. Its plan is saved
before this supplemental run. It does not replace the primary preset-selection outcome.

The default simulator is checked against a golden result from the original imported simulator.
Varied thresholds/leak and both complete auxiliary doses have targeted numerical tests.

## Limits

Four evaluation devices per condition support examples and failure diagnosis, not a population
success rate or an exhaustive robustness claim. A fixed baseline that matches learning is a valid
outcome. An advantage in average gain need not be an advantage in work or transmission reliability.
Future work here is the declared simulator work, not the reserve E or measured hardware energy.
Windows assigned by source time are diagnostic: delayed or ambiguous spikes need causal inspection.
