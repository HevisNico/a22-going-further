# Verification engine

The engine of the ±0.1 % / 28-pulse result, extended for wider boxes. The physical kernel R in
`kernel/` is unchanged: `../kernel/KERNEL_SHA256SUMS` lists its 52 files, byte-identical to the
base. `reference/full_model_reference.md` is the model, in French. `CHANGES_FROM_BASE.diff` is the
complete diff against the base engine. `README_EN.txt`, `README_C7_EN.txt`, `VALIDATION_EN.txt` and
`ENGINE_CHANGES_FROM_V33.diff` are inherited from the base engine and describe its history.

Every mechanism added beyond the base engine, with its code location, what it records and its
proof obligation, is listed in [`../proof/going_further/MECHANISMS.md`](../proof/going_further/MECHANISMS.md).

The calendar is the 28-pulse protocol (sources at 0, 8, …, 216; terminal cut at 230).

## Status at ε = 3e-3

| Engine | Fresh campaign | Layer 18 |
|---|---|---|
| Fix T | layers 1–17 accepted | (18,0), (18,1), (18,11), (18,4) and (18,8) refused |
| Fix T + KMAX 1024 | layers 1–17 accepted (≈ 20 min, 4 workers) | 9 of 12 accepted; (18,0), (18,5), (18,7) refused |
| Fix T + KMAX 1024 + Fix T′ (this engine) | not yet run | (18,0), (18,5), (18,7) accepted in targeted replays from the previous campaign |

A box is certified only by a fresh campaign with this exact engine, followed by
`certify/certify_box.py` (see `../CERTIFICATION.md`).

## Build, test, launch

Python 3.12 or 3.13, a C compiler, OpenSSL headers.

```sh
cd engine
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt        # numpy 2.3.5, scipy 1.17.0
python build_all_native.py
python -B -m unittest discover -s tests
python -u -B launch_fresh.py --out /absolute/path/new_campaign --epsilon 3e-3 --workers 4 --memory-mib 2500
```

The output directory must not exist. Keep the first refusal, its inputs and the engine's source
identity. To replay or trace one cell, use `../tools/` (see `../tools/README.md`).
