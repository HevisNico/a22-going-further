# Certification of the ±0.3 % / 28-pulse result

This repository preserves one result: **ε = 3e-3 (±0.3 %)**, with 28 source pulses at
0, 8, …, 216 and a terminal cut at 230. The cut is not a training pulse. The procedure is inherited
from the ±0.1 % / 28-pulse result. The published records are in `results/eps3e-3/`.

## 1. Freeze the statement

The protocol calls for recording the statement before a campaign. For the published run,
`results/eps3e-3/STATEMENT.md` was written afterwards, as that file explicitly records;
the launch metadata and engine identity fixed the statement at launch. Its fields are:
- ε and the initial family (δ = 1e-5);
- the calendar;
- the engine commit;
- the future contract (source gaps ≥ 20, global return strictly before 19).

Nothing in the statement changes during the campaign. Reproductions must record it before launch.

## 2. Run the campaign

The published engine is frozen in `engine_eps3e-3/`. To reproduce its campaign, build it cleanly
and use a new output directory (see `engine_eps3e-3/README.md`), explicitly selecting `--epsilon 3e-3`.
The campaign must reach 18/18 layers with no manual intervention. A refusal is a failed
reproduction and must be retained with its inputs and reason.

## 3. Certify the records

```sh
python3 -I certify/certify_box.py <campaign dir> <new records dir> --engine-dir engine_eps3e-3
```

Use a new records directory for a reproduction; preserve `results/eps3e-3/` as published.

Each step runs as a separate process, standard library only, and none imports the engine.

| Step | What it checks |
|---|---|
| Run manifest | Freezes size and SHA-256 of every output file of the campaign |
| Terminal extraction | Every payload against its receipt; exact terminal state at 230 for the 216 cells; exact rest of every active cell |
| Lineage and clocks | Layer decisions, parent receipts, retained time-atom definitions |
| Commutations | Every recorded lemma-E / E2 use |
| Mechanism census | Every recorded use of every mechanism, Fix F leaves, history counts |
| Initial section | Its finite inequalities at the box's ε |
| Future certificate | The regime from the terminal domain, in directed integers; the active/masked partition is recomputed, not imposed. Each gain box is the stored box intersected with [e^(inf z), e^(sup z)], from the stored log-gain bounds (two valid enclosures of the same gain) |
| Independent future check | Directed decimals, a different implementation, including its own exponential for the gain intersection; the contract is gaps ≥ 20 and return strictly before 19 |
| Quiescent domain Q28 | Built from the extraction and the certificate |

The campaign directory and the as-run engine, with its native binaries, are published as
assets of the release `eps3e-3-campaign`. Their SHA-256 and the full verification commands are in
`results/eps3e-3/campaign/RELEASE_ASSETS.md`. The committed records include:
`campaign/campaign.json`, `campaign/RUN_MANIFEST.json`, `campaign/ENGINE`, `campaign/RELEASE_ASSETS.md` and
`terminal/*.json`.

## 4. Verify, as anyone else would

```sh
python3 -I certify/verify.py --box results/eps3e-3                       # committed records only
python3 -I certify/verify.py --box results/eps3e-3 <campaign dir>        # plus every output file
python3 -I certify/verify.py --box results/eps3e-3 <campaign dir> --engine <as-run engine dir>
```

The last form also recomputes the archived `kernel_id` from the as-run engine and checks that its
sources are the box's committed engine directory, named in `results/eps3e-3/campaign/ENGINE`.

Every derived file (initial section, both future certificates, Q28) is regenerated and compared
byte for byte with the committed one, and Q28 is rebuilt from the regenerated certificate, not from
the committed one. The ε of `campaign.json`, of the terminal extraction, of the certificates and of
the log must agree exactly. Every certificate hash cited by the certification log must be the committed certificate's.

## 5. Review the proof of what was used

For every mechanism the census shows as used, its obligation in `MECHANISMS.md` must have a written
argument. These arguments, together with the inherited coverage theorem, the general-ε extensions
and the future-invariance proof, make up the proof for the box. They have not yet been independently
reviewed; `REVIEW.md` lists the review tasks.

## 6. Run the controls

The verification controls are in `CONTROLS.md`. In particular, the point-simulation
inclusion test checks that sampled devices lie inside the certified enclosures.

## What this certified result states

For every device in the box and every admissible initial state:
- at t = 230 the network is in Q28(ε);
- from there, for every source sequence with gaps ≥ 20, each active cell fires exactly once per
  pulse and the network is back in Q28(ε) before the next pulse;
- intervals between source pulses are therefore transmitted exactly through the 18 layers.

This holds under the execution assumptions A1–A4 and the written arguments. It is not
machine-checked as a whole.
