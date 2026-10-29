# A22: going further, toward wider parameter boxes

A22 is a learning spiking network of 216 coupled hybrid cells (18 layers × 12 lanes), each with
three input ports, local plasticity and a recovery actuator. Its physical kernel, **R**, is fixed.
For every device whose per-port parameters lie within **±0.1 %** of nominal, it is already
established, by a computer-assisted enclosure and a written proof, that training brings the
network into a quiescent domain, and that afterwards the intervals between source pulses are
transmitted **exactly** through all 18 layers.

This repository asks how far that statement extends. The target is **±10 %**. A box that wide is
closer to the variability of real components; ±0.1 % is not. The kernel R stays unchanged
throughout. The training protocol, the verification engine and the proof may change.

> **Status: work in progress.** Nothing in this repository is a certified result yet. The tables
> below separate what is computed, what is only observed in point simulations, and what remains to
> be done.

## What is fixed and what may change

| Fixed | May change |
|---|---|
| The equations of R: main charge, auxiliaries, thresholds, protection, return to rest | The training protocol (number and dates of pulses, terminal cut) |
| The 18 × 12 graph, three parents per cell | The verification engine |
| Fixed constants: a, κ, r, r_m, thresholds, actuation factors, energy pump, b_max | The proof, as long as it stays short and rigorous |
| The initial family: δ = 1e-5, original modes, E in [50, 100] | |

The box: for each cell and each input port independently, the five parameters C, L_m, L_s, L_e
and M are fixed in time, anywhere within ±ε of nominal. All other constants are unchanged.

## The protocol: 29 training pulses, data from t = 250

The original protocol trains with 28 pulses at 0, 8, …, 216 and claims exact transmission from
t = 230. Point simulations at ±10 % refute that claim. In 8 of 224 devices the first future
interval is distorted, by up to 4.1 × 10⁻⁵. One simple witness uses homogeneous parameters and the
exact nominal initial state: an input interval of 20 comes out as 20.000019278.

The mechanism is a property of R itself: **READY is not rest.** A cell can be READY with a
residual charge left by training, without a later threshold–protection–return cycle to reset it
exactly to q = r. That residual decays like e^(−κt) and never reaches zero in finite time. The
next response therefore fires slightly early. The affected cells sit where the two fronts launched
from lane 0 meet, on the far side of the ring.

The revised protocol counts the source pulse at **230 as a 29th training (conditioning) pulse**
and starts the data at **250**. The pulse at 230 makes every active cell fire and return exactly to
rest, so the data start from a reset state. Nothing in R changes.

## The box ladder

The work proceeds by widening the box step by step. Each step must close before the next one is
attempted.

| ε | Certified? | What point simulations show | What the engine needs |
|---|---|---|---|
| ±0.1 % | **Yes** (previous work, 28 pulses) | — | — |
| ±0.3 % | In progress | Along the 9 tested parameter motifs, the training history is identical to the nominal one; both protocols pass | A few local extensions (see below); 13 of 18 layers are reached |
| ±1 % | Not yet | Same as ±0.3 % along the 9 motifs | Probably the same engine as ±0.3 % |
| ±3 % | Not yet | Training histories start to branch: from about 1.5 % on some motifs, 36 or more cells change their number of training firings. Under the 28-pulse protocol, exact rest at t = 230 is lost from about 1.48 %, and first-interval fidelity from about 3.68 %, along the worst motifs found | Scenario propagation (several training histories per cell); the 29-pulse protocol |
| ±10 % | Not yet | 256 prospectively specified devices and 192 adversarial proposals all pass the 29-pulse protocol (largest interval error 3.4 × 10⁻¹³). The 191-cell active mask is preserved, but **98 of 216 cells** have a device-dependent number of training firings, up to 5 different values in one cell | Scenario propagation at scale; convergence of all histories into one terminal domain Q29 |

The thresholds in this table are measured along the parameter directions tested. They are not
robustness radii of the full box, which has 3,240 parameters. A compact summary of the numerical
studies is in [`evidence/`](evidence/README.md).

## How the proof is kept simple

Every change to the engine must be an instance of one of three generic rules. Each rule is proved
once:

1. **Exact flow enclosure.** The model's own closed-form solutions (variation of constants,
   exponential decay), evaluated with outward-rounded arithmetic.
2. **Exhaustive case split.** Every real trajectory belongs to at least one branch: every event
   order, every actuation history, every position of a firing among arrivals.
3. **Monotone comparison and hull.** A quantity monotone in an uncertain input is bounded by its
   extreme cases. A merge of branches takes their hull and never removes a state.

An engine change that cannot be stated as one of these rules is not accepted. The aim is a proof
whose new parts fit in a few pages, with the abstract core of each rule checkable in Lean.

## Why the old engine is not enough beyond about 1 %

The verification engine of the previous work follows **one** training history per cell. Up to
about 1 %, that is also what happens physically. Beyond it, different devices in the box fire a
different number of times during training. No single-history enclosure can then cover the box, so
the statement to prove becomes: *different training histories all converge to the same
transmitting regime after the conditioning pulse.*

The engine therefore needs **scenario propagation**:
- each cell keeps separate branches, one per history;
- branches are merged only when they genuinely rejoin (same number of emissions, exact rest);
- sets of possible spike trains are passed to the next layer.

A first, cell-level version is in [`engine/`](engine/README.md). It is Fix F: a cell is recomputed
once per actuation history.

## Current engine status (±0.3 %, 28-pulse calendar)

| Engine | First refusal | Layers |
|---|---|---|
| Base engine | layer 8: slow recovery inside an uncertain event group | 7 / 18 |
| + R2 (existing recovery resolver on the event-group path) | layer 14: firing inside an uncertain event group | 13 / 18 |
| + E2, M, peak fallback, H, F | layer 14: 11 of 12 cells pass in single-cell replays; cell (14,0) still refuses | ≥ 13 |

The open problem at cell (14,0), and the change proposed next, are described in
[`engine/README.md`](engine/README.md). No full campaign has been run with this engine yet.

## Next steps

1. Switch the engine calendar to the 29-pulse protocol (terminal cut at 250).
2. Close cell (14,0): replace the extreme-date comparison of lemma E2 with the exact correlated
   charge (rule 1). Then run the ±0.3 % campaign and its audits.
3. ±1 %, with the same engine if possible.
4. Scenario propagation between cells, then ±3 % and ±10 %.
5. For each closed step: the terminal domain, the future-invariance check, and a short written
   proof organised by the three rules.
6. For each closed step: the verification controls and the scientific controls of
   [`CONTROLS.md`](CONTROLS.md). The preset-gain control in particular asks whether learning is
   what provides the robustness.

## Repository contents

| Path | What it is |
|---|---|
| `kernel/` | The physical kernel R, restated in English, with the checksums showing that the executable kernel is unchanged |
| `model/` | The original model texts: the reference definition (French) and the ±0.1 % specification |
| `proof/` | The proof plan for wider boxes (`proof/going_further/`) and the complete inherited proof of the ±0.1 % result, with its Lean 4 files |
| `engine/` | Verification engine, work in progress; `engine/CHANGES_FROM_BASE.diff` is the full diff against the base engine |
| `tools/` | Single-cell replay from recorded parent outputs, diagnostics, and the evidence summarizer |
| `evidence/` | Compact summary of the point-simulation studies (numerical evidence, not certificates) |
| `CONTROLS.md` | Planned verification controls and scientific controls (no learning, preset gains, shuffled gains, gate off, energy, selectivity) |
| `HISTORY.md` | Where the base engine, the model and the earlier results come from |

## Limits

- No result here is certified yet. Point simulations can refute a claim; they cannot establish it
  for the whole box.
- The box concerns five per-port parameters. Threshold, leak, waveform or interconnect
  variability, time-varying drift and noise are outside it.
- The result, when obtained, will concern this realization of R. It will not concern spiking
  networks in general.

> **Made with AI.** Code, diagnostics and documents are produced with Claude (Anthropic) and
> ChatGPT (OpenAI) under the direction of Nicolas Breuillaud.

## License

Code: MIT ([`LICENSE`](LICENSE)). Everything else: CC BY 4.0 ([`LICENSE-docs.md`](LICENSE-docs.md)).
