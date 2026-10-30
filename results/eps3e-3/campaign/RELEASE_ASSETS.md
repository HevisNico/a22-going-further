# Release assets of the ±0.3 % campaign

The complete campaign outputs and the as-run engine, with its native binaries, are attached to the
GitHub release **`eps3e-3-campaign`** of this repository, as six ZIP parts:

| File | Bytes | SHA-256 |
|---|---|---|
| `A22_fixT2_partie_01_sur_06.zip` | 28073157 | `1fc3e09a3ef306c5635d9e5f114d5ba8df078e0aec7b1ebd9ff556c1264a4b2b` |
| `A22_fixT2_partie_02_sur_06.zip` | 28394371 | `fec133ddf41397e55f63935ef2540cc3d21c8135f5d60b6c9811548eae087aaf` |
| `A22_fixT2_partie_03_sur_06.zip` | 27208516 | `60d3f17fec591a029208dfa1850bfa0d0405218b0e4de164c1ca4f5886c8e2af` |
| `A22_fixT2_partie_04_sur_06.zip` | 27706384 | `20b84cef506380ef1d0bda3e824c50d99818bd8967cd6ae527bfcdd99255ab98` |
| `A22_fixT2_partie_05_sur_06.zip` | 28550058 | `a59b9ccba5d7e55a319d89ebafb93aed2c069c30ee4462e322ea81fb424f7508` |
| `A22_fixT2_partie_06_sur_06.zip` | 24739828 | `0e5bad5860df8505bb28e929269d457a82e1faa35ce01a7774df58b1f40f7d66` |

Extracted into one directory, they give `campagne/` (the 488 output files listed in
`RUN_MANIFEST.json`), `sources/engine/` (the as-run engine, including
`affine/_rounding_native.cpython-312-x86_64-linux-gnu.so` and
`kernel/native/_a22_native.cpython-312-x86_64-linux-gnu.so`) and `SHA256SUMS_DELIVERY`, which
covers every delivered file.

## Full verification

```sh
sha256sum -c SHA256SUMS.zip-parts            # the six hashes above, saved to a file
mkdir run && for z in A22_fixT2_partie_0*_sur_06.zip; do unzip -q -o "$z" -d run; done
(cd run && sha256sum -c --quiet SHA256SUMS_DELIVERY)
python3 -I certify/verify.py --box results/eps3e-3 run/campagne --engine run/sources/engine
# optional, on Python 3.12 with numpy 2.3.5 and scipy 1.17.0:
python3 -I certify/verify.py --box results/eps3e-3 run/campagne --engine run/sources/engine --check-runtime
```

The third command checks every output file against `RUN_MANIFEST.json`, reruns the terminal
extraction and every audit, checks that the as-run engine has the sources of `engine_eps3e-3/`, recomputes
the archived `kernel_id`, then reruns the record checks. Expected: 12 PASS, 0 FAIL.
