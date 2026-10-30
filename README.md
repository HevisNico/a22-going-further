# A22: a learning spiking network certified on wider parameter boxes

A22 is a spiking network of 216 coupled hybrid cells (18 layers × 12 lanes) that learns while it
runs. Its cells follow a fixed physical kernel, **R**. This repository proves, for **every device**
in a box of independent per-port parameter variations, that training brings the network into an
explicit quiescent domain, and that afterwards it transmits the intervals between source pulses
**exactly** through all 18 layers. The box is widened step by step: ±0.3 %, ±1 %, ±3 %, ±10 %.

| Box | Status |
|---|---|
| ±0.3 % | **Certified**: 18/18 layers, both future certificates pass ([`results/eps3e-3/`](results/eps3e-3/README.md)) |
| ±1 % | Next: same engine, same protocol |
| ±3 %, ±10 % | Planned: 29-pulse protocol and scenario propagation (see [Beyond ±1 %](#beyond-1-)) |

"Certified" means a computer-assisted enclosure of every admissible trajectory, finite
certificates rechecked by independent programs, and written arguments. They hold under the
explicit execution assumptions A1–A4. The proof is not machine-checked as a whole and has not been
independently reviewed ([Limits](#limits)). Reviews are welcome: see [`REVIEW.md`](REVIEW.md).

## The kernel R

Full statement in English: [`kernel/README.md`](kernel/README.md). The original definition, in
French, is in [`model/`](model/). The executable kernel, `engine_eps3e-3/kernel/`, is byte-identical to its
reference (`kernel/KERNEL_SHA256SUMS`).

Each cell has a main unit and, on each of its three input ports, an auxiliary unit.

- **Main unit: threshold, protection, return.** While READY, the charge integrates its inputs:
  q′ = κ(r − q) + Σ g_i p_i(t). At q = 1 the cell fires: q is set to 1, admission closes, and a FAST
  phase (q′ = −aq, exactly one time unit, during which the output pulse is emitted) is followed by a
  SLOW phase (q′ = −b q). The cell reopens at **exactly** q = r. The return date is not prescribed:
  it follows from the recovery variable b.
- **Auxiliary units: a delayed sensory chain.** An auxiliary sees its port's raw input even while
  the main unit is protected. When it crosses its own threshold, it runs MARK → SILENT → ERROR, each
  section ending at an exact charge.
- **Learning on failure.** The ERROR section of an auxiliary deposits log-gain on its port, but only
  while the main unit is READY. A whole section adds exactly Δz = 0.6, whatever the port's decay
  rate.
  - If the cell fired on that input, the ERROR arrives during protection and is masked: the gain
    does not change.
  - If the cell missed, the gain grows.

  Gains thus grow on misses and stay put on hits, with no teacher, no target and no counter.
  Gains are capped at C_i.
- **Learned recovery.** A MARK received while the main unit is protected increases b (whole mark:
  Δb = 0.1, capped at 1.1), which shortens later protections.
- **Energy.** A reserve E′ = 10(100 − E) − W gates all actuations. A uniform work bound keeps E in
  [50, 100], so the gates stay open.
- **Variability.** Five physical parameters per port (C, L_m, L_s, L_e, M) are fixed in time and
  chosen independently in every cell and every port. Initial states vary by δ = 1e-5, and residual
  ERROR phases are allowed.

The network is feedforward. Cell (n, j) listens to (n−1, j−1), (n−1, j) and (n−1, j+1), lanes modulo
12. The source is lane 0 of layer 0.

### How R relates to the literature

- **Spiking neurons and plasticity.** Leaky integrate-and-fire neurons trained by
  spike-timing-dependent plasticity use pair-based, Hebbian timing rules. R's learning signal is
  different. It is a delayed, self-generated error current, gated by the cell's own protection
  state: an input that succeeded in firing the cell is masked, and an input that failed is
  reinforced. Refractoriness is not a dead time: it is a protected dynamical phase with a learned
  recovery rate and an exact return to rest.
- **Temporal coding through layers.** Stable propagation of synchronous volleys (synfire chains;
  Diesmann, Gewaltig and Aertsen, *Nature*, 1999), and their emergence through plasticity in
  simulation (for example Fiete, Senn, Wang and Hahnloser, *Neuron*, 2010), are classical. A22 makes
  a stronger, exact statement, for every device of a box: after learning, each active cell answers
  every pulse with a fixed latency, so source intervals are preserved exactly.
- **Verification.** Reachability tools for hybrid systems (Flow*, CORA, JuliaReach, DynIbex) enclose
  hybrid trajectories. Neural-network verification (Reluplex, Katz et al., 2017; formal methods for
  trained spiking networks) checks networks whose weights are already fixed. Here the object
  certified is the **learning dynamics itself**: 216 coupled hybrid cells, plasticity, event orders
  that vary inside the enclosure, and independent uncertainty on every port. We know of no earlier
  certificate of this kind; pointers are welcome.

## What a certified box states

For every device in the box and every admissible initial state, with 28 training pulses on lane 0
at 0, 8, …, 216:

1. **Training.** At t = 230 the network is in the explicit quiescent domain Q28.
2. **Afterwards, forever.** From Q28, for every source sequence with gaps of at least 20:
   - each active cell (191 of 216) fires exactly once per pulse;
   - the other cells stay silent;
   - the network is back at rest, and back in Q28, before the next pulse.
3. **Exact transmission.** Each active cell has a latency fixed by its device and learned state.
   The intervals between pulses are therefore transmitted exactly through the 18 layers. Latencies
   differ between devices.

## How it is certified

1. **Enclosure of training.** `engine_eps3e-3/` propagates outward-rounded affine enclosures of every
   admissible trajectory, cell by cell and layer by layer. It covers every compatible event order
   and refuses when it cannot decide. Each layer is re-read by a separate process.
2. **Three generic rules.** Every mechanism of the engine instantiates one of three rules, each
   proved once:
   - exact flow enclosure (the model's own closed-form solutions);
   - exhaustive case split (every trajectory lies in some branch);
   - monotone comparison and hull.

   The 17 mechanisms beyond the base engine, with their obligations, are listed in
   [`proof/going_further/MECHANISMS.md`](proof/going_further/MECHANISMS.md), and the written
   argument of each one is in
   [`proof/going_further/MECHANISM_ARGUMENTS.md`](proof/going_further/MECHANISM_ARGUMENTS.md). The
   census of a campaign shows which mechanisms it used; the arguments show why they are correct. The base coverage
   theorem and its extensions are in [`proof/inherited_eps1e-3/`](proof/README.md).
3. **Finite certificates.** `certify/` extracts the exact terminal state and audits lineage, clocks
   and every recorded mechanism. It then certifies the initial section and the future regime twice:
   in directed integers, and in directed decimals with a different implementation. Neither imports
   the engine.
4. **Controls.** Point-simulated devices must lie inside the certified enclosures
   ([`controls/`](controls/README.md), [`CONTROLS.md`](CONTROLS.md)).

The full procedure is [`CERTIFICATION.md`](CERTIFICATION.md).

## Verify it

```sh
python3 -I certify/verify.py --box results/eps3e-3
```

This recomputes the initial section, both future certificates and Q28 from the committed records.
It uses the standard library only, and CI runs it. With the campaign outputs and the as-run engine
(release assets of the box), it also checks every output file against the run manifest, re-extracts
and re-audits everything, and recomputes the engine's `kernel_id`:

```sh
python3 -I certify/verify.py --box results/eps3e-3 <campaign dir> --engine <engine dir>
```

To run a campaign yourself, see [`engine_eps3e-3/README.md`](engine_eps3e-3/README.md).

## Beyond ±1 %

Point simulations of the full network (numerical evidence, summarized in
[`evidence/`](evidence/README.md)) set the plan for wider boxes.

- **READY is not rest.** At ±10 %, a few devices end training with a cell READY but carrying a
  residual charge. It decays like e^(−κt) and never vanishes, so the first future response fires
  slightly early. Along the motifs tested, exact rest at 230 is lost beyond about 1.5 % and
  first-interval fidelity beyond about 3.7 %. From ±3 %, the source
  pulse at 230 is therefore used as a **29th, conditioning pulse**: it resets every active cell
  exactly, and the data start at 250. Under this protocol, 256 prospectively specified devices and
  192 adversarial ones all transmit exactly at ±10 %.
- **Training histories branch.** Beyond about 1.5 %, devices fire a different number of times
  during training: at ±10 %, 98 of 216 cells. Certification then needs **scenario propagation**:
  separate branches per history, merged only when they rejoin, and sets of spike trains between
  cells. The engine's history fork (mechanism 14) is a first, cell-level step.

## Repository contents

| Path | What it is |
|---|---|
| `kernel/` | The kernel R in English, and the checksums of the executable kernel |
| `model/` | The original model definition (French) and specification |
| `engine_next/` | Uncertified development copy with the audit fixes; the certified engine stays frozen |
| `engine_eps3e-3/` | The verification engine of the ±0.3 % box, frozen; `CHANGES_FROM_BASE.diff` against the base engine. Each box has its own engine directory |
| `certify/` | Certification tools and `verify.py` |
| `results/` | One folder per certified box: statement, campaign identity, run manifest, certificates, controls |
| `proof/` | `going_further/`: proof plan, mechanisms and their obligations, notes. `inherited_eps1e-3/`: the base coverage theorem, its extensions and Lean 4 files |
| `controls/` | Inclusion control and the point simulator |
| `evidence/` | Summary of the point-simulation studies |
| `tools/` | Single-cell replay and diagnostics |
| `CERTIFICATION.md`, `CONTROLS.md` | Certification procedure; planned verification and scientific controls |
| `REVIEW.md` | Call for review: self-contained tasks on the written arguments |
| `HISTORY.md` | Sources of the base engine, model and proof |

## Limits

- The box covers five per-port parameters. Threshold, leak, waveform or interconnect variability,
  time-varying drift and noise are outside it. ±0.3 % is still far tighter than real components.
- The proof holds under A1–A4:
  - authentic execution of the recorded program;
  - correct arithmetic runtime and native binaries;
  - fail-closed assertions;
  - namespace discipline.
- The written arguments for the mechanisms (`proof/going_further/MECHANISM_ARGUMENTS.md`) have not
  been independently reviewed. Only selected lemmas are machine-checked in Lean.
- The result concerns this realization R, with this graph and this protocol. It is not a statement
  about spiking networks in general. Whether learning gives an advantage over a network with preset
  gains is a separate question: see the scientific controls in `CONTROLS.md`.

## How this was built

This work is done with two AI assistants, **Claude** (Anthropic) and **ChatGPT** (OpenAI), under the direction of Nicolas Breuillaud.

## License

Code: MIT ([`LICENSE`](LICENSE)). Everything else: CC BY 4.0 ([`LICENSE-docs.md`](LICENSE-docs.md)).
