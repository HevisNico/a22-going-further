# Proof

| Folder | What it is |
|---|---|
| [`going_further/`](going_further/PROOF_PLAN.md) | The proof of the ±0.3 % / 28-pulse result: its statement, three generic rules, and the 17 mechanisms and their obligations. The written arguments are in `going_further/MECHANISM_ARGUMENTS.md`. The historical directory name is retained so existing references remain valid. |
| `inherited_eps1e-3/` | The complete proof of the ±0.1 % / 28-pulse result (written argument, extensions, Lean 4 files), copied unchanged from the base repository (see `../HISTORY.md`). |

`inherited_eps1e-3/` is kept byte-identical because its documents cite each other and are cited by
hash. As a consequence, some relative links inside it point to files of the base repository that
are not copied here (for example `REVIEW.md` or `campaign/`). Read its links to `../model/` as
[`../model/`](../model/) at the root of this repository, which holds the same two files, unchanged.

The new proof reuses the inherited one wherever possible. The flow formulas, the coverage of event
orders, the strict-root lemma, the first-crossing facts and the future-wave argument carry over
unchanged. What is new is listed, obligation by obligation, in
[`going_further/PROOF_PLAN.md`](going_further/PROOF_PLAN.md).
