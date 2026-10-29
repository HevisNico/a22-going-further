# Tools

| Script | What it does |
|---|---|
| `replay_cell.py` | Recomputes one cell from its parents' recorded outputs in an existing campaign directory, and prints ACCEPTED or REFUSED with the lemma-E statistics |
| `debug_fire_root.py`, `debug_resolve.py`, `debug_recovery.py`, `debug_window.py`, `debug_hist.py` | The same replay with logging around lemma E's root search, `_resolve`, `pending_window`, the local-cycle window, and the actuation histories |
| `summarize_numerical_evidence.py` | Builds `../evidence/numerical_summary.json` from the follow-up study's result archive |

Usage of the replay tools:

```sh
python -B tools/replay_cell.py <engine dir> <campaign dir> <layer> <lane> <scratch dir>
```

They load the engine from `<engine dir>`, read ε from the campaign's `campaign.json`, and write
nothing in the campaign directory.
