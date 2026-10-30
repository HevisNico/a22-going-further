# Call for review

This repository certifies the ±0.3 % box ([`results/eps3e-3/`](results/eps3e-3/README.md)): a
campaign, finite certificates rechecked by independent programs, and **written arguments** that the
campaign covers every admissible trajectory, under stated execution assumptions. The arguments have
**not yet been reviewed by an independent expert**. Each task below is a small, self-contained
piece that can be checked without knowing the rest.

**What helps most:** one of three answers, given as a GitHub issue titled `Review: <task>`:
- "the argument holds";
- "there is a gap at <file:section or file:line>, because ...";
- "here is a counterexample".

Partial reviews are welcome. Tasks are listed **most important first**.

Background: the [README](README.md), the three generic rules in
[`proof/going_further/PROOF_PLAN.md`](proof/going_further/PROOF_PLAN.md), and the mechanisms with
their obligations in [`proof/going_further/MECHANISMS.md`](proof/going_further/MECHANISMS.md)
("item n" below). *Affine form* means *c + Σ dₖ εₖ + [−e, e]*, valid for every ε in [−1, 1]^N. The
engine is [`engine_eps3e-3/`](engine_eps3e-3/README.md); code locations below are relative to it.
How often the campaign used each mechanism is in
[`results/eps3e-3/terminal/mechanism_usage.json`](results/eps3e-3/terminal/mechanism_usage.json).

The base engine, its coverage theorem, lemma E, C7/C6/P and the future-invariance proof are
inherited from the ±0.1 % result. They are in [`proof/inherited_eps1e-3/`](proof/README.md), with
their own review guide; reviewing them is just as useful.

---

## Task 1 — Charge-join envelope (item 10; used 2,762 times)

**Claim.** When branches are joined, each branch's charge lies both in the affine union and in
[min_i q_i, max_i q_i], so the joined charge may be the intersection of the two. All actuation and
deposit histories are retained.

**Where:** `affine/charge_join.py`; the joins it wraps (`join_states` in
`kernel/R_cycle_local_A20_2026-10-18/validation_A15.py`, `affine/recovery_group.py`).

**Questions.**
1. Is every field that the envelope intersects really a quantity common to the branches (and not,
   for example, a field whose meaning differs between branches)?
2. Does the intersection ever drop a branch's value through rounding (inward-rounded min/max)?

## Task 2 — Guard proofs with `charge_bound` (item 8; used 964 times)

**Claim.** "No fire on [start, tt]" is accepted only if the charge, enclosed by the intersection of
its affine and scalar evaluations, is strictly below 1 on the whole normalized segment. The
propagated memory keeps its affine forms; the intersection is used for the guard only.

**Where:** `affine/cluster_memory_cover.py` (`charge_bound`), its callers recorded as
`READY_event_relative_no_fire`.

**Questions.**
1. Is the scalar evaluation a valid enclosure for every parameter point, with outward rounding?
2. Does the segment cover really reach both ends, so that no fire can hide between two pieces?

## Task 3 — Fix T: the READY fire root in relative coordinates (item 15; every cell)

**Claim.** The READY fire root is solved as g(v) = Q(a_c + v) − 1, where a_c is the origin of the
admitted pulse with the largest gain. The relative root is accepted only if its bracket meets the
monotone prefix for every parameter point; then the zero found is the first fire. The plain root is
the fallback.

**Where:** [`proof/going_further/PROOF_NOTE_FIX_T.md`](proof/going_further/PROOF_NOTE_FIX_T.md);
`affine/relative_root.py`; its installation in `affine/engine.py`.

**Questions.**
1. Is the acceptance test (`bracket.lo <= off.lo + hi and bracket.hi >= off.hi`) enough to exclude
   an earlier crossing?
2. Is the change of origin (shift by a_c, then back) exact on the affine forms, with no lost
   remainder?

## Task 4 — Fix T′: the recovery return relative to the latest mark (item 16; every cell)

**Claim.** The return to READY is the unique zero of ell along the protected history. Solved
relative to the origin of the latest mark, it is the same zero, and it is kept only if narrower.

**Where:** [`proof/going_further/PROOF_NOTE_FIX_T2.md`](proof/going_further/PROOF_NOTE_FIX_T2.md);
`affine/relative_return.py`.

**Questions.** Is ell nonincreasing on the whole time axis for every history, including capped
recovery? Is the strict positivity of the rate on the accepted bracket checked for every parameter
point?

## Task 5 — E2: a fire caused by a group's own arrivals (items 2–4; used 7 times)

**Claim.** With no READY ERROR deposit active in the window, the READY charge is exactly
Q0(t) + Σ_j g_j h₊(t − a_j), evaluated with the actual correlated arrival dates. Its first crossing
is enclosed by the slope-free cover (`proof/inherited_eps1e-3/lean/FirstCrossing.lean`); every
event order and fire position is then enumerated, and a position is pruned only if it is
impossible for every parameter point.

**Where:** `affine/commutation.py` (`_arrival_fire_root`, `_strict_prefix`, `_resolve`), recorded
as `fire_arrival_commutation` route E2 and `E2_subthreshold_prefix`.

**Questions.**
1. Is the "no READY ERROR deposit in the window" premise checked at every call?
2. Can pruning (item 4) ever drop a position realized by some device, for example at equal dates?

## Task 6 — Restored READY memory, relative first crossing, no-fire recovery group (items 5, 9, 12)

**Claims.**
- *M (15 uses).* For a READY state with no active READY ERROR deposit, the charge from t is
  R + (q(t) − R)e^(−κ(s−t)) plus the tails of the active raw inputs, exactly, for every q(t) of
  the joined box.
- *Relative first crossing (6 uses).* Strict signs at both ends, a continuous flow with fixed
  memory, and the slope-free cover in normalized coordinates enclose the first crossing.
- *No-fire recovery group (3 uses).* The base resolver is applied only to groups of raw cuts and
  ERROR boundaries, which cannot change the actuation ledger.

**Where:** `affine/commutation.py`, `affine/charge_join.py`, `affine/nofire_cover.py`
(`first_fire`), `affine/recovery_group.py` (`no_fire_group`).

## Task 7 — Gain bounds of the future certificates

**Claim.** For each active cell, a port's gain is bounded by the stored gain box intersected with
[e^(inf z), e^(sup z)], from the stored log-gain bounds. Both are valid enclosures of the same gain,
and each checker computes the exponential with its own directed rounding. Without the intersection,
the stored boxes do not support the certificate at layer 18.

**Where:** `certify/certify_future.py` (directed integers), `certify/verify_future_general.py` and
`certify/general_contract.py` (directed decimals), `certify/build_q_domain.py`.

**Questions.** Are the stored z bounds (exact fractions) converted with outward rounding? Is every
premise of the future proof checked by both programs?

## Task 8 — The verification chain

**Claim.** `certify/verify.py` regenerates every derived file (initial section, both future
certificates, Q28) and compares it byte for byte with the committed one; Q28 is rebuilt from the
regenerated certificate. Every ε declaration of the box must agree exactly. With the campaign
outputs and the as-run engine (release assets), it also checks every output file against the run
manifest, reruns the extraction and the audits, and recomputes the archived `kernel_id` from the
box's engine directory.

**Where:** `certify/verify.py`, `certify/certificate_parameters.py`,
`results/eps3e-3/campaign/RELEASE_ASSETS.md`.

**Questions.** Can a modified certificate, terminal file or campaign metadata still pass? Is any
file used by a check not covered by a hash?

## Task 9 — Per-port parameter symbols and KMAX (item 17)

**Claim.** Each port's constants get their own affine symbols, used only for that port. Truncation
to KMAX = 1024 symbols keeps the largest coefficients and adds the rest, rounded upwards, to the
remainder; this is sound for every KMAX.

**Where:** `affine/port_symbols.py`, `affine/affine_iv.py`, `affine/rounding.py`,
`affine/rounding_native.c`.

## Task 10 — Kernel test files and the inherited campaign driver

**Claim.** Every test file shipped in the kernel passes on the CI runner, and the CI requires it.
The affine engine loads, from the kernel's `R_continuation_A22_2026-10-18/`, only
`avance_causale_A22` and `ready_general_A22`; the cache, memo and provenance layer of the inherited
campaign driver takes no part in the certified computation.

**Where:** `tools/run_kernel_suites.py` (run in CI on each engine directory).

**Question.** Five of these files (the driver's cache and provenance layer) pass on the CI runner
but fail in some other environments. Is any module they exercise used, directly or indirectly, by
the certified computation?
