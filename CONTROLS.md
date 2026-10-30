# Controls for the ±0.3 % / 28-pulse result

**Verification controls** make sure each certified step is what it claims to be.

The published inclusion control contains 56 devices and passed (`results/eps3e-3/controls/inclusion.json`).
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

## 2. Reproduction and reporting

Use the published 28-pulse protocol and ε = 3e-3. Keep reproduction outputs separate from the
published records. Verification commands are in `CERTIFICATION.md`; retain all refusals and errors.
Any additional control must report its predeclared sample, criteria and full outcome.
