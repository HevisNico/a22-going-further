# Written arguments for the mechanisms of the ±0.3 % engine

This document gives the argument for every mechanism of `engine_eps3e-3/` beyond the base engine
(list and code locations: [`MECHANISMS.md`](MECHANISMS.md)). It covers every mechanism that the
census of the ±0.3 % campaign records (`results/eps3e-3/terminal/mechanism_usage.json`) and every
mechanism that is active without being recorded. Code locations are relative to `engine_eps3e-3/`.

**Status.** Written against the code, not yet independently reviewed (see `../../REVIEW.md`). The
abstract cores cited from Lean are machine-checked; the bridge from the code to their hypotheses is
argued here, not machine-checked.

| Mechanism (item of `MECHANISMS.md`) | Recorded uses at ±0.3 % | Section |
|---|---|---|
| 10 Charge-join envelope | 2,762 (`charge_join_envelope`) | 2 |
| 8 `charge_bound` guard proofs | 964 (`READY_event_relative_no_fire`) | 3 |
| 2–4 E2, E2 prefix, pruning | 7 (route E2), 11 (`E2_subthreshold_prefix`) | 4 |
| 5 M: restored READY memory | 15 (`empty_READY_memory_restored`) | 5 |
| 9 Relative first crossing | 6 (`READY_relative_first_crossing`) | 6 |
| 12 No-fire recovery group | 3 (`A19_no_additional_fire_recovery`) | 7 |
| 1 R2 | part of 9 (`recovery_group_local_cycle`) | 8 |
| 6 Peak fallback, 7 fast-window retry | not recorded separately | 9 |
| 11 Gain range at admission | not recorded (every admission) | 10 |
| 13 H, 14 F | 14: none (no fork); 13: not recorded | 11 |
| 15 Fix T, 16 Fix T′ | not recorded (every cell) | `PROOF_NOTE_FIX_T.md`, `PROOF_NOTE_FIX_T2.md` |
| 17 KMAX | — | 12 |

Route E of `fire_arrival_commutation` (10 uses), `no_fire_cover` (2) and the base
`recovery_group_local_cycle` path are inherited: lemma E, the no-fire cover and Fix R in
`../inherited_eps1e-3/`.

---

## 1. Common facts

**Enclosure.** A computed quantity X *encloses* a physical quantity x if, for every parameter
point ε and every admissible initial state represented, x(ε) ∈ X(ε). For an affine form,
X(ε) = c + Σ dₖ εₖ + [−e, e]; for a plain interval, X(ε) is the interval itself.

**F1 (intersection).** If X and Y both enclose x, then any Z with Z(ε) ⊇ X(ε) ∩ Y(ε) for every ε
encloses x. `I.intersect` (`affine/affine_iv.py`, `intersect`) returns one of: the second operand
when it lies inside the first box, the first operand when it lies inside the second box, or the
plain interval [max lo, min hi]. In the first two cases the result is one of the two enclosures;
in the third it is a constant interval containing X(ε) ∩ Y(ε) for every ε, because X(ε) lies in
the box of X and Y(ε) in the box of Y. All bounds are the operands' own outward-rounded bounds; no
new rounding occurs. So intersection never removes a represented value. It may lose affine
correlation.

**F2 (strictness is kept).** If X(ε) and Y(ε) each contain an open neighbourhood of x(ε), so does
their intersection. Hence the open-image hypothesis of the inherited strict-root lemma
(`../inherited_eps1e-3/lean/StrictRoot.lean`) survives every intersection used below.

**F3 (READY charge with a pulse memory).** In READY, between two events, the main charge obeys
q′ = κ(R − q) + Σ_j g_j p_j(t), where p_j is the raw current of the pulses of port j. The kernel's
memory (`kernel/R_cycle_local_A20_2026-10-18/dependances_A17.py`, `evaluate`) stores the anchor t₀,
the charge q(t₀) and, for each admitted pulse, its origin and amplitude, and returns the
variation-of-constants solution: R + (q(t₀) − R)e^(−κ(t−t₀)) plus one term per pulse, including the
raw cut at age 1 and the decay after it. This is the inherited closed form (coverage theorem,
Sections 4–7; lemma C6). It is exact as long as no amplitude changes, which F4 guarantees.

**F4 (separation of raw pulses and deposits on a port).** A gain g_j changes only through a READY
ERROR deposit of port j. That deposit starts at the arrival plus D + DM_j + DS_j, with D the mark
delay. It ends at the arrival plus D + DM_j + DS_j + DE_j. Every cell asserts at set-up that
(D0_j + DM_j + DS_j).lo > 1, (D1 + DM_j + DS_j).lo > 1 and (D1 + DM_j + DS_j + DE_j).hi < 1.3
(`affine/port_symbols.py`, lines 87–89), and `unit` asserts that the pulses of a port are more
than 1.3 apart (`validation_A15.py`, line 412). So on each port a deposit never overlaps a raw
pulse of that port, and an amplitude stored at admission is the amplitude during the whole raw
pulse.

**F5 (slope-free first-crossing cover, and the upward crossing).** The model fires at the first
*upward* crossing of the threshold, not at a contact. On a READY segment, define

    F↑ = inf{ t ≥ t₀ : Q(t) > 1 }.

(a) *Structure of Q.* Between consecutive breakpoints (arrival dates and raw ends, finitely many on
the segment), F3 and F4 give Q(t) = R + α e^(−κt) + β e^(−At), with constant α and β. With R = 0.1
and κ ≠ A, Q − 1 is a nonzero exponential sum with three distinct exponents (0, −κ, −A) on each
piece, so it has at most two zeros there. Hence Q − 1 has finitely many zeros on the segment, and Q
is never equal to 1 on an interval. A tangency (a contact without crossing) is therefore an
isolated point. Since Q(t₀) < 1, F↑ is the first time at which Q passes above 1: Q ≤ 1 on [t₀, F↑],
Q(F↑) = 1, and Q > 1 on (F↑, F↑ + η) for some η > 0. This is the model's firing time.

(b) *The cover.* `_first_crossing_cover(f, hi)` (`affine/commutation.py`, line 135) requires
f(0) < 0 for every ε. It bisects [0, hi] depth-first, left piece first, and evaluates f on closed
pieces. It returns [lower, upper]:
- *lower* is the left end of the leftmost piece that is not certified negative. Every point
  before it has Q < 1, so F↑ ≥ lower.
- If a piece [a, z] with a < z has f.lo ≥ 0, then Q ≥ 1 on it. By (a), Q > 1 at all but finitely
  many points of [a, z], hence at points arbitrarily close to a, so F↑ ≤ a. *upper* is the
  smallest such a.
- If no such piece is found, upper = hi. Then F↑ ≤ hi requires **Q(t₀ + hi) > 1 strictly**: a
  contact at hi alone could be a tangency, after which the cell need not fire. This strict sign is
  established on every path by F7.

So [lower, upper] encloses F↑, the first upward crossing, and not merely the first contact. The
abstract core (`FirstCrossing.lean`) encloses the first contact. Points (a) and F7 are what make
that contact an upward crossing on these paths.

**F7 (strict sign at the right end).** The cover is called with three kinds of right end:
- `first_fire` (Section 6) checks `(Q(boundary) − 1).lo > 0`. The enclosure contains the true value,
  so Q(boundary) > 1 strictly, with no further argument.
- `_crossing_witness` (E2, Section 4, and the peak fallback, Section 9), and the end `hi` in
  `_fire_root`, check `f(u).lo ≥ 0` at a single time u > 0. This is non-strict. Strictness comes
  from the inherited open-image lemma (theorem, Section 5; `StrictRoot.lean`, two-point form):
  at a fixed positive time, the computed enclosure of the charge contains an open neighbourhood of
  the true value, for every ε. f(u).lo ≥ 0 then gives Q(u) > 1.

  The lemma applies because Q(u) − R is a sum of terms that each contain a fresh exponential at a
  nonzero argument: the homogeneous term at elapsed time u > 0, and every pulse term with positive
  age. Terms of zero age are exactly 0. If all terms were 0, Q(u) = R < 1, so the witness test
  would fail. In tight mode, the charge is `charge_bound`, the intersection of two such enclosures
  (both computed with the same outward arithmetic), and F2 keeps the open neighbourhood.

  The inherited proof uses the same argument for the same function on route E (review guide of
  the base result, task 2).

**F6 (normalized segment cover).** For an affine time τ with τ ≥ t₀, the probe
τ − λ(τ − t₀), with λ an interval, encloses every point of [t₀(ε), τ(ε)] whose normalized position
lies in λ. A bisection of [0, 1] into closed pieces therefore covers the whole segment for every ε,
including both ends. Working in normalized coordinates keeps the dependence of τ on its atoms.

---

## 2. Charge-join envelope (item 10)

**Code.** `affine/charge_join.py`, wrapping every `join_states`; the same envelope inside
`affine/recovery_group.py` (`KernelView.join_states`).

**Claim.** After a join of branch states S₁, …, S_n at a common time, the joined charge may be
replaced by `joined.q ∩ [min_i q_i.lo, max_i q_i.hi]`.

**Argument.** For a trajectory that follows branch i, its charge lies in q_i(ε), hence in the
envelope, which is a constant interval. It also lies in the original joined charge, which encloses
every branch pointwise (inherited, Section 9). By F1 the intersection encloses it. Only q changes;
the time, the actuation and deposit histories and every other field are those of the original join,
so all histories are retained. The envelope bounds are the branches' own outward bounds. The
recorded entry (`affine_q`, `leaf_envelope`, `joined_q`) lets the census recheck that the joined
charge lies inside both.

## 3. Guard proofs with `charge_bound` (item 8)

**Code.** `affine/cluster_memory_cover.py`: `charge_bound`, `certify`; called from `flowing` when
the kernel's peak bound cannot exclude an internal crossing inside an uncertain external cluster
(`affine/engine.py`, line 39).

**Claim.** If, for every closed piece of [0, 1], the bound of Q(τ − λ(τ − t₀)) − 1 is strictly
negative, then the cell does not fire on [t₀, τ], for every ε.

**Argument.**
1. `flowing(s, τ)` is called on a READY segment that ends at the next event τ, so no input is
   admitted inside it. By F3 and F4, Q(t) = `dep.evaluate(memory, t)` exactly on the segment.
2. `charge_bound` evaluates the same closed form a second time with every factor replaced by its
   plain box: R + (q₀ − R)e^(−κ·elapsed) + Σ g_j·pulse(age_j). Each box contains the true value, and
   `dep.pulse` encloses the pulse map for every age in its argument, so this is a second enclosure
   of Q(t). Tail memories (pulses admitted during protection) are not re-evaluated; the affine
   evaluator is used alone. By F1 the intersection encloses Q(t). It is used for the guard only: the
   memory that is propagated keeps its affine forms.
3. `_strict_prefix` (`affine/commutation.py`, line 238) bisects [0, 1] until every closed piece
   has a strictly negative upper bound, and refuses otherwise. By F6 the pieces cover [t₀, τ] for
   every ε. So Q < 1 on the closed segment: no contact, hence no fire.

The fallback in `certify` (absolute pieces [t₀ + lo, t₀ + hi] up to the horizon H) is the same
argument with absolute coordinates. H is the upper bound of τ − t₀, so the pieces cover the
segment, and possibly more, which only adds conditions.

## 4. E2: a fire caused by the group's arrivals (items 2–4)

**Code.** `affine/commutation.py`: `_arrival_fire_root` (line 168), `_strict_prefix`, `_resolve`
(line 295). Called when the kernel refuses a READY state against a group of events.

**Premises, checked in the code.** The state is READY with a memory. The group contains no
`error_on`/`error_off`, and no uncapped port has an active READY ERROR deposit. Any `raw_off` in
the group is the cut, at exactly origin + 1, of a pulse in the memory or in the group. Other
auxiliary actions do not change q in READY. No group event precedes the state.

**Claim (item 2).** The fire date is enclosed by t₀ + ρ, where ρ is the first-crossing cover of
Q(t) = Q₀(t) + Σ_j g_j h₊(t − a_j).

**Argument.** Before the first fire, the cell is READY, so every arrival a_j of the group that
precedes it is admitted, with the amplitude that `act` stores (the same call is made). Gains are
fixed on the window (the premises and F4). By F3, Q above is the exact charge up to the first fire.
The raw cuts are inside the pulse terms. Arrivals after t contribute h₊ = 0, and `dep.pulse` of an
age box that reaches below 0 evaluates `nonnegative()`, whose range contains 0. A certified
witness date with Q ≥ 1 for every ε is searched on [0, H], H being strictly before the next
pending event. If none is found, the route declines. F5 then encloses the first upward crossing,
with the strict sign at the witness given by F7.

**Claim (item 3).** If Q < 1 on the whole segment from t₀ to an event date τ, then τ strictly
precedes the fire.

**Argument.** This is F6 and `_strict_prefix` applied to the same exact Q: Q < 1 on the closed
segment [t₀, τ], hence by continuity on [t₀, τ + η) for some η > 0, so F↑ > τ.

**Claim (item 4).** Each admissible order of the group's events is computed with every possible
fire position k. A position is dropped only if no trajectory realizes it.

**Argument.** `admissible_orders` is the kernel's enumeration (inherited, Section 8). Position k
is dropped only in two cases, both evaluated on the correlated difference τ − fire:
- an event placed before the fire satisfies (τ − fire).lo > 0, so it is after the fire for every ε;
- an event placed after the fire satisfies (τ − fire).hi < 0, or item 3 proved it precedes the fire.

Equality keeps both positions. For the remaining branches, the kernel maps (`act`, `flowing`,
`fire_reset`) are applied with the common fire enclosure, valid in every branch by item 2. The
branches are then joined at U, after every event of the group, before the next pending event and
before the end of the fast section (all three are checked). The join keeps every history and uses
the envelope of Section 2.

## 5. Restored READY memory (item 5)

**Code.** `affine/charge_join.py` (after a join; recorded as `empty_READY_memory_restored`) and
`affine/commutation.py` (`_resolve`, first lines; not recorded).

**Claim.** A READY state that lost its memory in a join can be given the memory
`dep.start(t, q, active raw inputs)`.

**Argument.** In `charge_join`, the restoration happens only when no raw input is active. Then, by
F3 with no pulse term, q(s) = R + (q(t) − R)e^(−κ(s−t)) until the next admission, for every q(t)
in the joined box. The joined q itself is kept, never replaced by R. Later admissions use the
unchanged `dep.add`. In `_resolve`, the kernel's `new_memory` re-anchors the active raw inputs as
tails at t. This is again the variation-of-constants solution from t, exact provided no amplitude
changes: no uncapped READY ERROR deposit may be active (checked), and F4.

## 6. Relative first crossing (item 9)

**Code.** `affine/nofire_cover.py`, `first_fire`; used only after the kernel refuses an advance to
a boundary with "ready guard still overlaps external boundary" or a root-bracket failure.

**Claim.** If Q(t₀) < 1 and Q(boundary) > 1 for every ε, the first fire is enclosed by the cover
in normalized coordinates of the boundary.

**Argument.** The advance is to the next event, so no input is admitted before the boundary. Q is
`charge_bound` of the memory, an enclosure by Section 3 (F3, F4). The endpoint check
`(Q(boundary) − 1).lo > 0`, which is strict (F7), and F5 on the normalized segment (F6) enclose the first upward crossing strictly
before the boundary. The affine root is used instead only when the derivative is positive on the
whole normalized interval, so its root is the unique crossing, and it is upward. The kernel then
applies the unchanged `fire_reset`.

## 7. No-fire recovery group (item 12)

**Code.** `affine/recovery_group.py`, `no_fire_group`.

**Claim.** A protected recovery state whose return overlaps a group consisting only of raw cuts and
ERROR boundaries is resolved by the base A19 resolver, with every branch ending READY below
threshold.

**Argument.** Raw cuts and ERROR boundaries do not change the actuation ledger. During protection,
a raw cut ends a pulse that admission already ignores, and an ERROR boundary only opens or closes a
deposit gate, which is closed while the cell is protected. So the return computed for the state,
`late`, is the return of every branch that has the same fire and the same histories. Only for those
branches is it reused, and the reuse is checked by identity of the history objects. The resolver
itself (`branche_retour_A19.resolve`) is the inherited one: it enumerates every order, propagates
every learning gate and certifies every post-return READY flow. It runs with a private binding, so
no global state changes. Its joins use the envelope of Section 2. The result is accepted only if
the joined state is READY with q < 1.

## 8. R2 (item 1)

**Code.** `affine/engine.py`, the cluster hooks (lines 208–268); `affine/recovery_group.py`,
`resolve`.

**Claim.** The inherited Fix R resolver may be applied on the group path.

**Argument.** In both hooks the resolver receives the state as it was before the refused step: the
exception leaves `s` unchanged, and in the cluster hook no order has been applied to `s`. So it
precedes every event of the pending group, which is the premise of
`cycle_local_A20.pending_window`. The resolver and its join rule (every branch READY with no
emission) are those of Fix R, whose argument is inherited.

## 9. Peak fallback and fast-window retry (items 6, 7)

**Peak fallback** (`_fire_root`, branch `ratio.lo <= 0`, and the witness branch). No monotone
prefix is used. A crossing at a witness date, certified for every ε (`_crossing_witness`), and
f(0) < 0 are the premises of F5, which encloses the first upward crossing (strict sign at the
witness: F7).

**Fast-window retry** (`_resolve(..., tight=True)`). It is entered only after the strict
end-of-fast-section check refused. The same route is recomputed with the guard function evaluated
by `charge_bound` instead of `dep.evaluate`. By Section 3 this is another enclosure of the same
charge, and by F2 the strict-root hypotheses still hold. The horizon, the fast-section bound and
every strict check are unchanged and must pass again.

## 10. Gain range at admission (item 11)

**Code.** `affine/gain_range.py`.

**Claim.** The stored amplitude of an admitted pulse on an uncapped port may be intersected with
[e^(inf z), e^(sup z)].

**Argument.** On an uncapped port, the amplitude is g = e^z, with z the port's log-gain. The stored
amplitude encloses g by construction (affine exponential of z). `z.plain().exp()` is the
exponential, rounded outwards, of a box containing z, hence another enclosure of g. F1 applies. The
log-gain ledger z and every learning history are unchanged; only the amplitude in the memory is
tightened. Capped ports keep their cap box.

## 11. History split and fork (items 13, 14)

The ±0.3 % campaign recorded no fork (item 14): `mechanism_usage.json` lists no
`history_fork_cells`. Item 13 is rule 2: the actuation ledger is a disjunction of histories, every
other field is valid for all of them, and the forests computed for each history on the same event
group are unioned. A trajectory follows exactly one history, so it is covered by that history's
forest.

## 12. KMAX (item 17)

`truncate_coeff` (`affine/rounding.py`; `affine/rounding_native.c`) keeps the KMAX largest
coefficients and adds the absolute values of the others, rounded upwards, to the remainder e. For
every ε, the dropped part Σ dₖεₖ lies in [−Σ|dₖ|, Σ|dₖ|], so the truncated form encloses the
original one. This holds for every KMAX; the value only changes precision and running time.
