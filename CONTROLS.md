# Controls for the ±0.3 % / 28-pulse result

There are two kinds of controls.
- **Verification controls** make sure each certified step is what it claims to be.
- **Scientific controls** say what a certified result means: in particular, whether learning is
  what makes A22 robust at a given box width, or whether a network without learning would do as
  well.

The published inclusion control contains 56 devices and passed (`results/eps3e-3/controls/inclusion.json`).
The scientific controls below remain planned; no completed result for them is claimed here.
Reproductions and additional controls must declare their protocol and outcome criteria before running
and report every outcome.

## 1. Verification controls

| Control | What it checks |
|---|---|
| Frozen statement | Launch metadata and engine identity fix ε = 3e-3, the 28-pulse calendar and T = 230. The separate `STATEMENT.md` was written afterwards, as it explicitly records |
| Layer re-read | Every completed layer is re-read and re-verified by a separate process (already in the engine) |
| Campaign identity | `kernel_id` is reproduced from the published sources and binaries; every output file is checked against the run manifest |
| Kernel unchanged | `kernel/KERNEL_SHA256SUMS` matches the executable kernel |
| Independent audits | Terminal extraction, lineage and clock audit, and an audit of every use of the new mechanisms (E2 firings, M re-anchorings, H splits, F forks), each rerun from the recorded outputs |
| Initial section | Its finite inequalities, rechecked at ε = 3e-3 |
| Future regime | The future certificate, recomputed by two independent programs (directed integers and directed decimals) |
| Inclusion of point simulations | The firing counts and firing dates of sampled devices must lie inside the certified enclosures (`controls/inclusion_check.py`; learned gains are a planned extension). This plays the role of the A14 reference comparison. One sample outside the enclosure is a soundness failure |
| Refusals | Every refusal is kept with its reason. A refusal is never counted as a success; a budget overflow is a refusal |
| Regression tests | Each engine change comes with tests, including at least one case where it must refuse |
| Lean | Selected inherited lemmas are checked in Lean 4 without `sorry`; the full proof and the three-rule plan are not wholly formalized |

## 2. Planned scientific controls at ±0.3 %

They use the same protocol and the same, paired devices, sampled from the certified ±0.3 % box.
The sample sizes and the outcome criteria are declared before the runs.

| Control | Question | What would weaken the claim |
|---|---|---|
| No learning (gains frozen at their initial values) | Is learning needed at all? | The network transmits without learning |
| Preset gains, no learning: a uniform sweep and the best hand-designed allocation | Can a network without learning do as well on the same box? | A preset allocation transmits across the box at a lower or equal gain or energy cost |
| Learned gains, shuffled within each layer and port | Does the learned placement matter? | Shuffled gains transmit as well |
| Protection gate off (plasticity active during protection) | What does the gate contribute? | No difference in transmission or gain level |
| Energy | Work W per data pulse, learned versus preset | The learned network costs more for the same task |
| Selectivity | Response to isolated lateral probes, learned versus preset | No difference |
| Noise and decoys | Outside the certified box: is the behaviour gradual? | An abrupt loss just outside the box |

These controls are point simulations. They are not certified, and they are reported as numerical
evidence only. The certificate alone does not establish an advantage of learning over a preset network.
That comparison requires the scientific controls.

## 3. Reproduction and reporting

Use the published 28-pulse protocol and ε = 3e-3. Keep reproduction outputs separate from the
published records. Verification commands are in `CERTIFICATION.md`; retain all refusals and errors.
Any additional scientific control must report its predeclared sample, criteria and full outcome.
