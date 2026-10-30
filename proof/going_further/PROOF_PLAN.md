# Proof plan for the ±0.3 % / 28-pulse result

**Status:** the three rules are stated here, every engine mechanism is reduced to one of them in
[`MECHANISMS.md`](MECHANISMS.md), and the written argument of every mechanism used by the ±0.3 %
campaign is in [`MECHANISM_ARGUMENTS.md`](MECHANISM_ARGUMENTS.md). The published result is in
[`../../results/eps3e-3/`](../../results/eps3e-3/README.md). These arguments have not been independently
reviewed. This document concerns that result only.

## 1. The statement

Let B_ε be the box of the five per-port parameters (`../../kernel/README.md`), with **ε = 3e-3**.
The kernel R and initial family are unchanged from the inherited result. The protocol uses
**28 source pulses** on lane 0, at 0, 8, …, 216; terminal cut **T = 230**; domain **Q = Q28(ε)**.
The terminal cut is not an additional training pulse.

For every device in B_ε and every admissible initial state:

- **T1, training.** At t = 230 the network lies in the explicit domain Q28(ε).
- **T2, future.** From Q28(ε), for every sequence of source pulses spaced by at least 20, each
  active cell fires exactly once per pulse, the other cells stay silent, and the network returns
  to Q28(ε) strictly before 19 time units after each source pulse.
- **T3, exact transmission.** Each active cell answers with a latency that is fixed for its device
  and learned state. The intervals between source pulses are therefore transmitted exactly through
  the 18 layers.

The active mask (191 of 216 cells) and explicit domain are outputs of certification. The future
check establishes a global return before 12.79144, satisfying the stated contract.

## 2. The chain of the proof

The chain is the inherited one (`../inherited_eps1e-3/README.md`):

> model → initial section → training coverage → entry into the terminal domain → future regime →
> exact transmission.

| Step | Inherited | Application at ±0.3 % |
|---|---|---|
| Initial section | general-ε argument | Finite inequalities rechecked at ε = 3e-3 |
| Training coverage | coverage theorem, lemma E, C7/C6/P | The engine mechanisms of section 4, each reduced to one rule of section 3 |
| Terminal domain | exact extraction at T | Extraction at T = 230; exact rest of all active cells |
| Future regime | future invariance | The active and masked/influential partitions are recomputed from the terminal domain. Each gain box is intersected with exp of the stored log-gain bounds |
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
The campaign census, `results/eps3e-3/terminal/mechanism_usage.json`, lists which mechanisms were
actually used; only those enter the written argument for this result.

## 5. What is kept from the inherited assumptions

The execution assumptions A1–A4 are unchanged:
- authentic execution of the recorded program;
- correct arithmetic runtime and native binaries;
- fail-closed assertions;
- namespace discipline.

The new code adds no other trusted component.

## 6. Remaining review work

The ±0.3 % campaign, finite certificates and written arguments are published. Independent review
of the arguments and their implementation remains open; the concrete tasks are in
[`../../REVIEW.md`](../../REVIEW.md). The selected inherited Lean lemmas remain part of the
verification material; the proof as a whole is not machine-checked.
