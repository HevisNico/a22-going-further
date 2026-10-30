# Next engine candidate — not certified

This directory starts from the frozen `../engine_eps3e-3/` engine and carries development
corrections. It has no certified campaign or terminal domain. Existing ±0.3 % results continue to
name `engine_eps3e-3/`; their sources, native archive, kernel identity and certificates are unchanged.

## Audit correction: history-fork joins

`affine/fork.py` now refuses incompatible terminal clocks, modes and pending activity. It rebuilds
cap flags, saturation flags, scalar enclosures and learning summaries from the joined affine state.
The proof inventory retains records from every recomputed leaf; counts include repeated common
prefixes. Metrics aggregate the leaf executions rather than reporting only the first leaf.

No Fix F fork was used by the published ±0.3 % campaign. The correction is tested on explicit
mixed-cap leaves and refusal cases in `../tests/engine/test_history_fork.py`.
The physical kernel is unchanged and still matches `../kernel/KERNEL_SHA256SUMS`.
The inherited diff files describe the frozen predecessor; the additional source change is the
replacement of `affine/fork.py` in this directory.

## Build and test

Python 3.12 or 3.13, a C compiler and OpenSSL headers:

```sh
cd engine_next
python -m pip install -r requirements.txt
python build_all_native.py
python -B -m unittest discover -s tests
cd ..
A22_TEST_ENGINE=engine_next python -B -m unittest discover -s tests/engine
```

A new full campaign and its full certification procedure are required before claiming a result
with this engine. Use a new campaign directory and explicitly select its epsilon:

```sh
python -u -B engine_next/launch_fresh.py --out /absolute/path/new_campaign --epsilon 1e-2 --workers 4 --memory-mib 2500
```

This command is an attempt at ±1 %, not a claim that the box will pass. If certified, freeze the
engine under a box-specific directory and publish the new as-run archive and identity as described
in `../CERTIFICATION.md`.
