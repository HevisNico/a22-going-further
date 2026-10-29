# Verification engine (work in progress)

Base: the engine of the ±0.1 % / 28-pulse result (see `../HISTORY.md`). The physical kernel R in
`kernel/` is unchanged; `reference/full_model_reference.md` is the model, in French.
`CHANGES_FROM_BASE.diff` is the complete diff against the base engine. `README_EN.txt`,
`README_C7_EN.txt`, `VALIDATION_EN.txt` and `ENGINE_CHANGES_FROM_V33.diff` are inherited from the
base engine and describe its earlier history.

The calendar is still the 28-pulse protocol (terminal cut 230). Switching to the 29-pulse protocol
(cut 250) is the next engine task.

## Changes, each an instance of one of the three rules

| Change | Where | Rule | What it does |
|---|---|---|---|
| **R2** | `affine/engine.py`, event-group hook | none new (reuses a certified resolver) | The refusal "slow section inside external cluster (actuation ledger)" for a protected-recovery state is routed to the existing recovery resolver (`recovery_group.resolve` → `cycle_local_A20.pending_window`), with the same join rule. `tests/test_v33_ports.py` now expects two call sites |
| **E2** | `affine/commutation.py`, `_arrival_fire_root` | 3 (monotone comparison) | A READY firing **caused by the group's arrivals**; lemma E covers only a firing of the existing charge. While every admitted pulse is still raw, h is increasing, so Q_late ≤ Q ≤ Q_early pointwise, with all arrivals at their latest or earliest dates. The firing lies between the first crossing of Q_early and the first certain crossing of Q_late (slope-free covers). Fire positions that no trajectory can realize are dropped; equalities keep both positions |
| **M** | `commutation._resolve` | 1 (exact flow) | A joined READY state whose pulse memory was lost is re-anchored with the kernel's `new_memory`: the charge box at t plus the active raw inputs as tails. Exact by variation of constants, provided no READY ERROR deposit is active |
| **Peak fallback** | `commutation._fire_root` | 1 (exact flow) | When the peak logarithm has no certified positive argument, the slope-free first-crossing cover runs on the whole horizon, once a crossing at its end is certain |
| **H** | `affine/history_split.py` | 2 (case split) | When the recovery resolver refuses the joined actuation ledger, it is run once per history on the same event group, and the forests are unioned |
| **F** | `affine/fork.py` | 2 (case split) | Cell-level scenario propagation. If H still fails, the cell is recomputed once per actuation history, each recomputation pinned at the fork state (its exact time token). Leaves merge only if they emit the same number of pulses. Output k becomes the hull of the leaves' k-th emissions; terminal states use `join_states`. The budget is 16 leaves |

Each change only replaces a former refusal. Cells that the base engine accepted are computed
exactly as before. All 101 engine tests pass.

## Status at ε = 3e-3 (single-cell replays from recorded parents)

Layers 1–13 are accepted with R2 alone. In layer 14, 11 of 12 cells are accepted; **cell (14,0)
still refuses**.

At t = 174.88, cell (14,0) is in slow recovery with three actuation histories. The reason is that
a mark on port 1 (origin in [173.20, 173.65], duration 0.02) cannot be ordered against the firing
F ∈ [173.488, 173.875] produced by E2:

| History | Mark | Recovery rate b | Return to READY |
|---|---|---|---|
| 0 | entirely under protection | 0.18 | ≈ 179.6–180.0 |
| 1 | straddles the firing (partial dose) | [0.08, 0.18] | up to ≈ 187.4 |
| 2 | entirely before the firing | 0.08 | ≈ 187 |

New arrivals come at 181.15. F splits the three histories. History 2 passes; history 1 refuses,
because its partial dose alone spreads the return over more than 1.83 time units.

Root cause: the firing enclosure, of width 0.39, is too loose. E2 compares extreme arrival dates
and so discards the correlation between the arrival dates and the parameters.

**Proposed next change (not applied).** Replace E2's extreme-date comparison with the exact
correlated charge

    Q(t) = Q0(t) + Σ_j g_j h₊(t − a_j),   h₊(u) = 0 for u ≤ 0,

evaluated with the actual correlated arrival times, followed by a single slope-free cover. This
uses rule 1 only. It is simpler than the monotone comparison, needs no premise about raw ends, and
should be much tighter. If the firing enclosure narrows, the mark histories should separate
cleanly. Fallbacks:
- a case split on the partial mark dose (the return date is monotone in b);
- more fork leaves.

## Running

```sh
cd engine
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt        # numpy 2.3.5, scipy 1.17.0
python build_all_native.py
python -B -m unittest discover -s tests          # 101 tests
python -u -B run.py --out ../campaign_eps3e-3 --through 18 --epsilon 3e-3 --workers 4 --memory-mib 3000
```

Replaying one cell from an existing campaign directory, whose parent layer must be complete:

```sh
python -B ../tools/replay_cell.py <engine dir> <campaign dir> <layer> <lane> <scratch dir>
```

The `tools/debug_*.py` scripts add logging around `_fire_root`, `_resolve`, `pending_window`, the
local-cycle window and the actuation histories. Set `A22_DEBUG_FORK=1` or `A22_DEBUG_SPLIT=1` for
fork and split traces.
