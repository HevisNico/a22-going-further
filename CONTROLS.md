# Planned controls

There are two kinds of controls.
- **Verification controls** make sure each certified step is what it claims to be.
- **Scientific controls** say what a certified result means: in particular, whether learning is
  what makes A22 robust at a given box width, or whether a network without learning would do as
  well.

Both are planned **before** each campaign. A control is reported whatever its outcome.

## 1. Verification controls, for every step of the box ladder

| Control | What it checks |
|---|---|
| Frozen statement | Before a campaign, the protocol, ε, the cut time and the target domain are recorded with a hash, and are not changed during the campaign |
| Layer re-read | Every completed layer is re-read and re-verified by a separate process (already in the engine) |
| Campaign identity | `kernel_id` is reproduced from the published sources and binaries; every output file is checked against the run manifest |
| Kernel unchanged | `kernel/KERNEL_SHA256SUMS` matches the executable kernel |
| Independent audits | Terminal extraction, lineage and clock audit, and an audit of every use of the new mechanisms (E2 firings, M re-anchorings, H splits, F forks), each rerun from the recorded outputs |
| Initial section | Its finite inequalities, rechecked at each ε |
| Future regime | The future certificate, recomputed by two independent programs (directed integers and directed decimals) |
| Inclusion of point simulations | The firing counts and firing dates of sampled devices must lie inside the certified enclosures (`controls/inclusion_check.py`; learned gains are a planned extension). This plays the role of the A14 reference comparison. One sample outside the enclosure is a soundness failure |
| Refusals | Every refusal is kept with its reason. A refusal is never counted as a success; a budget overflow is a refusal |
| Regression tests | Each engine change comes with tests, including at least one case where it must refuse |
| Lean | The abstract core of each generic rule and of each new lemma is checked in Lean 4 without `sorry` |

## 2. Scientific controls, at each closed ε

They use the same protocol and the same, paired devices, sampled from the box that was certified.
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
evidence only. A certificate at ±10 % with no scientific advantage over a preset network is still
a result about R. It must not be presented as evidence that learning helps.

## 3. When

- Before each campaign: the frozen statement and the target domain.
- After each closed step: all verification controls, then the scientific controls on the same box.
- At ±0.3 % and ±1 %, the scientific controls mainly set the reference values. The decisive ones
  are at ±3 % and ±10 %, where devices differ enough for a preset allocation to possibly fail.
