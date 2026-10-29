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
unchanged, and `engine/reference/` holds another unchanged copy of the reference definition.
`proof/inherited_eps1e-3/` is that repository's `proof/` folder, copied unchanged from the same
commit.

The point-simulation studies summarized in `evidence/` were carried out separately: the
falsification campaign at ±10 %, the prospective 29-pulse cohort, the adversarial search and the
radial ε scans. Their full archives (device values, all output dates, independent ODE replays,
preregistration) are about 100 MB and are not committed here. They can be published as release
assets.
