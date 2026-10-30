# Engine mechanisms and their proof obligations

Every mechanism of the engine beyond the base engine of the ±0.1 % result is listed here. For each
one: where it is in the code, what it records in the campaign payloads (`guard` in
`width_profile.relative_order_proofs`, counted by `certify/audit_mechanisms.py`), which of the three
rules of `PROOF_PLAN.md` it instantiates, and its obligation.

The base mechanisms are proved in `../inherited_eps1e-3/`:
- the coverage theorem;
- lemma E (`fire_arrival_commutation`, route E);
- C7, C6 and P;
- Fix R (`recovery_group_local_cycle`);
- the no-fire cover.

A certified box needs a written argument for every mechanism its census shows as used. The census
is `results/<box>/terminal/mechanism_usage.json`. The arguments for the mechanisms of
`engine_eps3e-3/` are in [`MECHANISM_ARGUMENTS.md`](MECHANISM_ARGUMENTS.md).

**Common premise of every intersection below.** If two enclosures are each valid pointwise for
every parameter point, their intersection is valid. Intersecting can lose affine correlation, but
it never removes a represented value.

| # | Mechanism | Code | Recorded as | Rule |
|---|---|---|---|---|
| 1 | R2: Fix R on the event-group path | `affine/engine.py`, cluster hook | `recovery_group_local_cycle` | none new |
| 2 | E2: firing caused by group arrivals | `commutation._arrival_fire_root` | `fire_arrival_commutation`, route E2 | 1 |
| 3 | E2 prefix order | `commutation._strict_prefix` | `E2_subthreshold_prefix` | 1 |
| 4 | Pruning of impossible fire positions | `commutation._resolve`, pass 2 | — | 2 |
| 5 | M: re-anchoring a lost pulse memory | `commutation._resolve`; `charge_join` | `empty_READY_memory_restored` | 1 |
| 6 | Peak fallback | `commutation._fire_root` | — | 1 |
| 7 | Fast-window retry | `commutation._resolve(tight=True)` | `tight_charge` field | 1 + intersection |
| 8 | charge_bound | `cluster_memory_cover.charge_bound` | `READY_event_relative_no_fire` | 1 + intersection |
| 9 | Relative first crossing | `nofire_cover.first_fire` | `READY_relative_first_crossing` | 1 |
| 10 | Charge-join envelope | `affine/charge_join.py` | `charge_join_envelope` | 3 |
| 11 | Gain range at admission | `affine/gain_range.py` | — | 1 + intersection |
| 12 | No-fire recovery group | `recovery_group.no_fire_group` | `recovery_group_local_cycle` | none new |
| 13 | H: one resolution per actuation history | `affine/history_split.py` | — | 2 |
| 14 | F: one recomputation per actuation history | `affine/fork.py` | `history_fork_leaves` in the state | 2 |
| 15 | Fix T: READY fire root relative to an admitted pulse | `affine/relative_root.py` | — | 1 |
| 16 | Fix T′: recovery return relative to the latest mark | `affine/relative_return.py` | — | 1 |
| 17 | KMAX = 1024 | `affine/affine_iv.py` | — | none (precision setting) |

## Obligations

1. **R2.** At the new call site, the state handed to the local resolver precedes every event of the
   pending group. It has just been advanced to the group's lowest date, and the group's events have
   not been applied. The resolver and its join rule are those of Fix R.

2. **E2.** No READY ERROR deposit is active or starts in the window, so the stored amplitudes are
   fixed. The READY charge is then exactly Q0(t) + Σ_j g_j h₊(t − a_j), evaluated pointwise with the
   kernel's maps and the actual, correlated arrival dates. The slope-free first-crossing cover
   encloses its first crossing (`FirstCrossing.lean`). Every event order and every position of the
   firing is then enumerated.

3. **E2 prefix.** If Q < 1 on the whole segment from t0 to an event date tt, for every parameter
   point, then that event strictly precedes the first fire.

4. **Pruning.** A fire position k is dropped only if one of the following holds for every
   parameter point, using correlated date differences:
   - an event placed before the fire is certainly after it;
   - an event placed after it is certainly before it, or is certified by item 3 to precede it.

   Equalities keep both positions.

5. **M.** For a READY state with no active READY ERROR deposit, the charge from t is
   R + (q(t) − R)e^(−κ(s−t)) plus the tails of the active raw inputs. This is exact for every q(t)
   in the joined box. In the empty-input case, no input is active and q0 is the whole joined charge,
   never replaced by R.

6. **Peak fallback.** When the charge's peak position is not certified, the slope-free cover is
   used on the whole horizon. Its premise, a certain crossing at the end of the horizon, is checked.

7. **Fast-window retry.** Only after the strict fast-section check refuses, the same route is
   recomputed with the charge enclosed by the intersection of its affine and scalar evaluations,
   and the same strict checks must pass.

8. **charge_bound.** The same intersection is used for guard proofs only; the propagated memory
   keeps its affine forms. "No fire on [start, tt]" is accepted only if the strict prefix of item 3
   holds on the whole normalized segment.

9. **Relative first crossing.** The charge is strictly below 1 at the start and strictly above 1 at
   the actual boundary, the flow is continuous with a fixed memory, and the first crossing is
   enclosed by the slope-free cover in normalized coordinates of the boundary. The existing affine
   root is kept only when monotonicity is certified on the whole interval.

10. **Charge-join envelope.** Each branch's charge lies both in the affine union and in
    [min_i q_i, max_i q_i], so the join intersects the two. All histories are retained.

11. **Gain range.** For every represented z, e^z lies both in the affine exponential and in
    [e^(inf z), e^(sup z)]. Only admitted amplitudes are intersected; the learning ledger is
    unchanged.

12. **No-fire recovery group.** The base A19 resolver (all orders, every learning gate,
    certified post-return READY flow) is applied only to groups of raw cuts and ERROR boundaries.
    These do not change the actuation ledger. The return passed as the coarse window equals the
    resolver's own coarse enclosure, since there is no mark in the group. Joins use the envelope of
    item 10.

13. **H.** The actuation ledger is a disjunction: every trajectory follows exactly one history, and
    every other field is valid for all of them. The event group is the one formed for the joined
    ledger, and is the same for every history. The forests are unioned.

14. **F.** The recomputation is deterministic, so every leaf reaches the fork state identically.
    That state is identified by its exact time token, and pinning restricts it to one history
    only. Leaves merge only if they emit the same number of pulses. Emission k becomes the hull of
    the leaves' k-th emissions, and terminal states are joined pointwise. Different counts are a
    refusal.

15. **Fix T.** See `PROOF_NOTE_FIX_T.md`. The bracket must meet the monotone prefix for every
    parameter point.

16. **Fix T′.** See `PROOF_NOTE_FIX_T2.md`. ell is nonincreasing on the whole time axis, so the
    zero in any accepted bracket is the return.

17. **KMAX.** Truncation keeps the KMAX largest coefficients and adds the rest, rounded upwards, to
    the remainder. This is sound for every KMAX. It only affects precision and running time.

## Execution assumptions

A1–A4 of the inherited proof are unchanged:
- authentic execution of the recorded program;
- correct arithmetic runtime and native binaries;
- fail-closed assertions;
- namespace discipline.
