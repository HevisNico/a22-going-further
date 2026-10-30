# Planned controls

**Verification controls** make sure each certified step is what it claims to be. They are planned
**before** each campaign, and a control is reported whatever its outcome.

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

## 2. When

- Before each campaign: the frozen statement and the target domain.
- After each closed step: all verification controls.
