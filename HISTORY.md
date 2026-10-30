# Where this work comes from

- **The ±0.1 % result (28 pulses, T = 230)**: certified enclosure of the training of every device
  in the box, written coverage proof, future invariance, exact transmission, and Lean 4
  formalizations of selected lemmas. The base engine of this repository is its `engine/`, at commit
  `c88c2fff178a8925b34185547930a9246c49c662`.
  https://github.com/HevisNico/a22-28-pulses
- **The first complete version and its extensions**: ±1e-4 with 128 pulses, the extension to
  ±1e-3, arbitrary depth, and the box-width sweeps with the earlier engines (v3.3 and the scenario
  launcher v2.3.1).
  https://github.com/HevisNico/a22-interval-replay

The physical model is the one specified in the first repository. `model/` here holds its two files
unchanged, and `engine_eps3e-3/reference/` holds another unchanged copy of the reference definition.
`proof/inherited_eps1e-3/` is that repository's `proof/` folder, copied unchanged from the same
commit.

This repository now preserves only the ±0.3 % / 28-pulse result. The development engine and
exploratory studies for other boxes were removed from the working tree; they remain available in
the Git history preceding this scope change. The certified engine, campaign records and certificates
are unchanged. Historical descriptions inside the frozen engine and inherited sources are retained
verbatim for provenance; they do not extend the scope of this repository.
