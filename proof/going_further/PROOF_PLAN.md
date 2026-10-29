# Proof plan for wider boxes

**Status: plan and proof obligations. Nothing here is proved yet.**

## 1. The statement, for each ε

Let B_ε be the box of the five per-port parameters (`../../kernel/README.md`). The kernel R and the
initial family are unchanged. Training uses 29 source pulses on lane 0, at 0, 8, …, 216 and 230. The
pulse at 230 is the conditioning pulse; the data start at 250.

For every device in B_ε and every admissible initial state:

- **T1, training.** At t = 250 the network lies in an explicit domain Q29(ε).
- **T2, future.** From Q29(ε), for every sequence of source pulses spaced by at least G, each active
  cell fires exactly once per pulse, and the network returns to Q29(ε) before the next pulse.
- **T3, exact transmission.** Each active cell answers with a latency that is fixed for its device
  and learned state. The intervals between source pulses are therefore transmitted exactly through
  the 18 layers.

The ε ladder is 0.3 %, 1 %, 3 %, 10 %. The gap G, the active mask and the explicit form of Q29 are
outputs of each step, not assumptions. Each step is closed before the next one is attempted.

## 2. The chain of the proof

The chain is the inherited one (`../inherited_eps1e-3/README.md`):

> model → initial section → training coverage → entry into the terminal domain → future regime →
> exact transmission.

What changes:

| Step | Inherited | What is new |
|---|---|---|
| Initial section | general-ε argument | Recheck its inequalities at each ε (finite check) |
| Training coverage | coverage theorem, lemma E, C7/C6/P | The engine changes of section 4, each reduced to one rule of section 3 |
| Terminal domain | exact extraction at T | Cut at 250 instead of 230. Beyond about 1 %, the domain is the **union over training histories** (scenario leaves) |
| Future regime | future invariance with a fixed masked/influential partition | Classify ports **device by device**, by whether the port's ERROR phase falls under protection. Numerically, the nominal partition is not preserved across the box |
| Exact transmission | fixed latencies | Unchanged argument |

## 3. The three rules

Each is a short, generic lemma, proved once. Its abstract core is a candidate for Lean 4.

**Rule 1: exact flow enclosure.** Between two events, with modes and gates fixed, each state
variable is given by the model's closed form:
- variation of constants for q and for the READY auxiliaries;
- exponential decay for the protected phases;
- integrated actuation for z and b, with exact projection onto the caps.

Evaluating the closed form with outward-rounded interval or affine arithmetic encloses the true
value, pointwise, for every parameter point and every initial state represented. *Inherited:*
coverage theorem, sections 4–7.

**Rule 2: exhaustive case split.** If every trajectory satisfies at least one of the cases
C_1, …, C_n, and the computation encloses the trajectories of each case, then the union of the
results encloses all of them.

The cases can be event orders, positions of a firing among arrivals, or actuation histories. A
case may be spurious; no case may be missing. A budget overflow is a refusal.

**Rule 3: monotone comparison and hull.** If a quantity is monotone in an uncertain input on the
relevant window, it is bounded by its values at the extreme inputs. Two kinds of quantity are used:
- a charge, together with its first crossing;
- a return date, which is monotone in b.

A merge replaces several enclosures by their hull, which contains each of them. *Inherited:*
monotone comparison in `ready_root`, C7.

## 4. Obligations of the engine changes

Each change only replaces a former refusal. Computations the base engine accepted are unchanged.

**R2: recovery resolver on the event-group path.** *No new rule.* It reuses the certified local
resolver (`cycle_local_A20.pending_window`) and Fix R's join rule.
- *Obligation:* at the new call site, the state handed to the resolver precedes every event of the
  pending group. The state has just been advanced to the group's lowest date L, and the group's
  events have not been applied.

**E2: firing caused by the group's arrivals.** *Rule 3.*
- *Statement.* Gains are fixed on the window: no READY ERROR deposit is active or starts. Every
  admitted pulse is still raw on the window, so h is increasing. Then Q_late ≤ Q ≤ Q_early
  pointwise, where all arrivals are placed at their latest or earliest dates. Hence F lies between
  the first crossing of Q_early and the first certain crossing of Q_late.
- *Then* every order of the events and every position of the firing among them is enumerated (rule
  2). A position is dropped only if it is impossible for every trajectory, as decided by correlated
  date differences; equalities keep both positions.
- *Planned simplification.* Use the exact correlated charge Q = Q0 + Σ g_j h₊(t − a_j) instead
  (rule 1 only). This also removes the raw-end premise.

**M: re-anchoring a lost pulse memory.** *Rule 1.* For a READY state with no active READY ERROR
deposit, the charge from time t is R + (q(t) − R)e^(−κ(s−t)) + Σ g_j·(tail of pulse j). This holds
exactly for every q(t) in the joined box.

**Peak fallback.** When the position of the charge maximum is not certified, the slope-free
first-crossing cover is used on the whole horizon (`FirstCrossing.lean`). Its premise is checked:
a crossing is certain at the end of the horizon.

**H: one resolution per actuation history.** *Rule 2.* The actuation ledger is a disjunction: the
true trajectory follows exactly one history, and every other field is valid for all histories.
- *Obligation:* the event group is the one formed for the joined ledger, and is the same for every
  history.

**F: recomputing a cell per actuation history.** *Rule 2.* Obligations:
1. The computation is deterministic, so every recomputation reaches the fork state identically. The
   fork state is identified by its exact time token.
2. Pinning restricts that state to one history and nothing else.
3. Leaves merge only if they emit the same number of pulses. Emission k becomes the hull of the
   leaves' k-th emissions (rule 3), and terminal states are joined pointwise.

Different counts are a refusal at this stage. From about 1.5 %, they require scenarios to propagate
between cells: sets of spike trains as the interface between cells.

## 5. What is kept from the inherited assumptions

The execution assumptions A1–A4 are unchanged:
- authentic execution of the recorded program;
- correct arithmetic runtime and native binaries;
- fail-closed assertions;
- namespace discipline.

The new code adds no other trusted component.

## 6. Order of work

1. Switch the engine to 29 pulses with the cut at 250. The obligation is the calendar bridge, as for
   28 pulses.
2. Close ±0.3 % (cell (14,0), see `../../engine/README.md`). Then build the terminal domain, check
   the future regime, and write the written proof of the changes actually used.
3. ±1 %.
4. Scenario propagation between cells, then ±3 % and ±10 %.
5. Lean: the abstract cores of rules 2 and 3 and of E2, next to the inherited `StrictRoot.lean` and
   `FirstCrossing.lean`.
