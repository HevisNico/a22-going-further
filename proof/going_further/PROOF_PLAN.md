# Proof plan for wider boxes

**Status:** the three rules are stated here and every engine mechanism is reduced to one of them in
[`MECHANISMS.md`](MECHANISMS.md). The ±0.3 % box is certified (`../../results/eps3e-3/`). The written
arguments for the mechanisms it used are being completed.

## 1. The statement, for each ε

Let B_ε be the box of the five per-port parameters (`../../kernel/README.md`). The kernel R and the
initial family are unchanged. The protocol depends on the box:

- **±0.3 % and ±1 %:** 28 source pulses on lane 0, at 0, 8, …, 216; terminal cut at T = 230; domain
  Q = Q28(ε).
- **From ±3 %:** a 29th, conditioning pulse at 230; terminal cut and data start at T = 250; domain
  Q = Q29(ε). It is needed because a READY cell can keep a residual charge at 230 (`../../evidence/`).

For every device in B_ε and every admissible initial state:

- **T1, training.** At t = T the network lies in the explicit domain Q.
- **T2, future.** From Q, for every sequence of source pulses spaced by at least G, each active
  cell fires exactly once per pulse, and the network returns to Q before the next pulse.
- **T3, exact transmission.** Each active cell answers with a latency that is fixed for its device
  and learned state. The intervals between source pulses are therefore transmitted exactly through
  the 18 layers.

The ε ladder is 0.3 %, 1 %, 3 %, 10 %. The gap G, the active mask and the explicit form of Q are
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
| Terminal domain | exact extraction at T | From ±3 %, cut at 250. Beyond about 1.5 %, the domain is the **union over training histories** (scenario leaves) |
| Future regime | future invariance with a fixed masked/influential partition | The partition is recomputed from the terminal domain, not imposed. Each gain box is the stored box intersected with exp of the stored log-gain bounds. From ±3 %, ports may have to be classified **device by device** |
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
The 17 mechanisms, their code locations, what each records and the rule it instantiates are listed
in [`MECHANISMS.md`](MECHANISMS.md). Fix T and Fix T′ have their own notes
([`PROOF_NOTE_FIX_T.md`](PROOF_NOTE_FIX_T.md), [`PROOF_NOTE_FIX_T2.md`](PROOF_NOTE_FIX_T2.md)).
For each certified box, `terminal/mechanism_usage.json` lists which mechanisms were actually used;
only those need a written argument for that box.

## 5. What is kept from the inherited assumptions

The execution assumptions A1–A4 are unchanged:
- authentic execution of the recorded program;
- correct arithmetic runtime and native binaries;
- fail-closed assertions;
- namespace discipline.

The new code adds no other trusted component.

## 6. Order of work

1. ±0.3 %: **done** (`../../results/eps3e-3/`). Remaining: the written arguments for the
   mechanisms its census lists.
2. ±1 %: same engine, same 28-pulse protocol; certify with `certify/certify_box.py`.
3. The 29-pulse protocol (cut at 250) and its calendar bridge, as for 28 pulses.
4. Scenario propagation between cells, then ±3 % and ±10 %.
5. Lean: the abstract cores of rules 2 and 3, next to the inherited `StrictRoot.lean` and
   `FirstCrossing.lean`.
