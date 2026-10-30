# Box ε = 3e-3 (±0.3 %)

## Statement

**Family.** For each cell and each input port independently, the five parameters C, L_m, L_s,
L_e and M are fixed in time within ±0.3 % of nominal. The initial family is the original one:
δ = 1e-5, READY or residual-ERROR auxiliaries, and E in [50, 100].

**Protocol.** 28 training pulses on lane 0, at times 0, 8, …, 216. Terminal cut at 230.

For every device and every admissible initial state:

1. **Training.** At t = 230 the network is in the explicit quiescent domain Q28
   (`terminal/invariant_domain_Q28.json`).
2. **Afterwards, forever.** From Q28, for every source sequence with gaps of at least 20:
   - each of the 191 active cells fires exactly once per pulse;
   - the 25 other cells stay silent;
   - the network is back at rest within 12.7914 time units, and back in Q28 before the next pulse.
3. **Exact transmission.** Each active cell answers with a latency that is fixed for its device and
   learned state. Intervals between source pulses are therefore transmitted exactly through the
   18 layers.

This holds under the execution assumptions A1–A4 and the written arguments listed below. It is not
machine-checked as a whole, and it has not been independently reviewed.

## Campaign

| | |
|---|---|
| Engine | `engine/` of this repository; `kernel_id` `c57d43fc…`, run `afd81b4e…` (`campaign/campaign.json`) |
| Layers accepted | 18 / 18, each re-read by a separate verifier process; no refusal |
| Cells | 216 payloads verified; 191 active cells at exact rest at 230; 540 auxiliary ports at exact rest |
| Network emissions during training | 2,202 |
| Run time | ≈ 32 min of layer computation, 4 workers (layer 18: 13 min) |
| Outputs | release asset; every file listed in `campaign/RUN_MANIFEST.json` (488 files) |

## Certificates (`terminal/`)

| Check | Result |
|---|---|
| Initial section at ε = 3e-3 | PASS; smallest margin 4.3e-5 |
| Future certificate, directed integers | PASS: 191 active cells, 15 masked and 525 influential ports, return before 12.79144 |
| Independent future check, directed decimals | PASS. Contract: gaps ≥ 20, return strictly before 19. Idle margin > 7.2085 |
| Smallest strict local margins | firing before the first raw end: 0.00277; masked arrival after firing: 0.0485; all raw inputs end before reopening: 0.0993 |
| Q28 | built from the extraction and the certificate |

**Gain bounds used by the future certificates.** For each active cell, a port's gain box is the
stored gain box intersected with [e^(inf z), e^(sup z)], from the stored log-gain bounds. Both are
valid enclosures of the same gain. The stored box comes from an affine exponential and can be much
wider: at layer 18 the plain stored boxes do not support the future certificate. The exponential
is computed with directed rounding, independently by each checker.

## Mechanisms used by this campaign (`terminal/mechanism_usage.json`)

| Recorded guard | Uses | Obligation in `proof/going_further/MECHANISMS.md` |
|---|---|---|
| `charge_join_envelope` | 2,762 | 10 |
| `READY_event_relative_no_fire` | 964 | 8 |
| `fire_arrival_commutation` | 17 (lemma E: 10, E2: 7) | inherited lemma E; 2, 4 |
| `empty_READY_memory_restored` | 15 | 5 |
| `E2_subthreshold_prefix` | 11 | 3 |
| `recovery_group_local_cycle` | 9 | inherited Fix R; 1 |
| `READY_relative_first_crossing` | 6 | 9 |
| `A19_no_additional_fire_recovery` | 3 | 12 |
| `no_fire_cover` | 2 | inherited |

Not recorded but active in every cell:
- Fix T and Fix T′ (obligations 15 and 16);
- the gain range at admission (11);
- the fast-window retry (7);
- the peak fallback (6);
- re-anchoring in lemma E (5);
- KMAX (17).

No history fork (14) was needed.

## Controls

`controls/inclusion.json`: point-simulated devices are drawn with the motifs of the falsification
studies, scaled to ±0.3 %. Every one fires the same number of times as the certified cells, with
every firing date inside its certified box.

## Verify

```sh
python3 -I certify/verify.py --box results/eps3e-3                              # records
python3 -I certify/verify.py --box results/eps3e-3 <campaign> --engine <engine>  # everything
```

With the campaign and the as-run engine: 12 PASS, 0 FAIL.
