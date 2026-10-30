# Numerical evidence (point simulations, not certificates)

These studies simulate individual devices of the full 18 × 12 network with R unchanged, using an
event-driven simulator. Flagged cases were confirmed by an independent direct ODE integration. The
studies can refute a claim. They cannot establish a claim for the whole box.

`numerical_summary.json` is produced from the follow-up study's result archive by
`../tools/summarize_numerical_evidence.py`. It reads recorded outputs only.

## Reproducibility boundary

Only the summary of the follow-up studies is published here. The 256-device prospective plan,
192-proposal adaptive search records, post-hoc proposals, epsilon-scan records and their complete
result archives are not included in this repository or its current release. Their reported
numbers below cannot yet be independently reconstructed from the published material. In
particular, the prospective designation is a report of the study, not a predeclaration whose
chronology this repository authenticates. These exploratory reports do not enter the ±0.3 %
certificate or its 56-device inclusion control.

To make those studies reproducible, a future release must include the exact generating and
search scripts, plans/seeds and chronology, all successes/refusals/errors, ODE confirmations,
source/dependency identities, archive checksums, and commands reproducing `numerical_summary.json`.
No missing records have been reconstructed or inferred from the summary.

## Main findings

**1. The 28-pulse claim fails at ±10 %.** In 224 predeclared devices, the 191-cell active mask and
one response per pulse are always preserved, but 8 devices distort the first future interval, by up
to 4.1 × 10⁻⁵. All 8 were confirmed by the ODE replay.

The simplest witness has every port at C × 0.9, L_m × 1.1, L_s × 1.1, L_e × 1.1, M × 0.9, starts
from the exact nominal initial state, and receives source pulses at 230 and 250. It gives outputs
236.676877580608 and 256.676896858676 at cells (18,5) and (18,7), an interval of 20.000019278. The
two simulators agree to about 10⁻¹³.

Cause: just before their first future input, the cells are READY with q ≈ 0.10018673 instead of
r = 0.1.

**2. The 29-pulse protocol survives a prospective test at ±10 %.** The pulse at 230 is used for
conditioning and the data start at 250. Results:
- 256 new devices, specified before simulation: 80 independent uniform, 80 independent corners and
  96 correlated corners;
- 192 adaptive adversarial proposals, plus 32 post-hoc proposals;
- in every case: the 191-cell mask, one response per data pulse, rest before each local wave, and a
  largest interval error of 3.4 × 10⁻¹³.

The adversary also made previously masked ports arrive before the firing without breaking
transmission. A proof should therefore classify ports device by device (is the ERROR phase under
protection?) rather than freeze the nominal masked/influential partition.

**3. Training history branches beyond about 1 %.** At ±10 %, 98 of 216 cells have a
device-dependent number of training firings, with up to 5 values in one cell. It starts at layer 5,
and every cell of layers 15–18 is affected. Along the 9 radial motifs, the training history is
identical to the nominal one up to ε = 1 % and branches between 1.5 % and 8 %.

**4. Where the 28-pulse claim stops along the tested motifs.** Exact rest at 230 is lost from about
1.48 %. First-interval fidelity is lost from about 3.68 %. At ε = 0.3 % and 1 %, all 9 motifs pass
both tests.

These thresholds hold along the tested directions only. They are not robustness radii of the full
box.
