# Statement of the ±0.3 % box

**This file was written after the campaign.** `CERTIFICATION.md` asks for the statement to be
frozen in this file before the campaign; for this box that step was not done as a separate file.
The statement was nevertheless fixed at launch, by records that the campaign could not change
afterwards:

- `campaign/campaign.json`, written by the engine when the campaign started. It holds ε, δ, the
  calendar and the environment, and they enter the `kernel_id`
  (`c57d43fcf8ce1227dddddc566fac1df939860d994e34f0b7696819dcb2b4ce46`), which every layer receipt
  and every payload repeats.
- The engine's source identity, which also enters the `kernel_id`. `certify/verify.py --engine`
  recomputes it from the as-run engine and checks that its sources are `engine_eps3e-3/`.

Nothing below differs from those records. This repository preserves this published campaign
and its statement; it makes no claim that this separate statement file predates the run.

## Box

- ε = 3e-3: for every cell and every input port independently, C, L_m, L_s, L_e and M are fixed in
  time within ±0.3 % of nominal.
- Initial family: δ = 1e-5, READY or residual-ERROR auxiliaries, E in [50, 100].

## Calendar

28 source pulses on lane 0, at 0, 8, …, 216. Terminal cut at T = 230.

## Engine

`engine_eps3e-3/` of this repository (named in `campaign/ENGINE`): its sources were committed in
9bb1410 and moved to this directory in daabd62, unchanged. Campaign identity: `kernel_id` above,
run `afd81b4e96cf4b8e81bade234c919e9f`.

## Future contract

From the terminal domain Q28(ε): source gaps of at least 20, and a global return to rest strictly
before 19 after each pulse.

## Target statement

For every device in the box and every admissible initial state: at t = 230 the network is in
Q28(ε); from there, under the future contract, each active cell fires exactly once per pulse and
the network is back in Q28(ε) before the next pulse, so source intervals are transmitted exactly.
The active set and Q28(ε) are outputs of the certification, not assumptions.
