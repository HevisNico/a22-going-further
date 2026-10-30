# Fix T: the READY fire root in relative coordinates

**Rule used: 1 (exact flow enclosure).** The charge function is unchanged; only the time coordinate
changes.

## Setting

In `advance`, a READY state at clock t0 has a pulse memory, so its charge is
Q(t) = dep.evaluate(memory, t) for t ≥ t0 until the next event. The existing code encloses the first
fire as t0 + u*, where u* is the root of f(u) = Q(t0 + u) − 1 on [0, hi]. Here hi = min(H, peak),
and Q is strictly increasing on [t0, t0 + hi] for every parameter point. This is the existing
premise of that code path (monotone prefix before the certified peak). That root, u_plain, is still
computed and kept.

## The change

Let a_c be the origin of an admitted, non-tail pulse in the memory: its date is an affine time,
correlated with the parameters. The largest amplitude is chosen; any choice is sound. Define

    g(v) = Q(a_c + v) − 1.

For every parameter point, the first fire F satisfies F − a_c ∈ (t0 − a_c) + u_plain, so the
bracket search for g runs on [lo(t0 − a_c) + lo(u_plain), hi(t0 − a_c) + hi(u_plain)]. The kernel's
own root routine (`v.root`) returns an enclosure rv of a zero of g, from a bracket [l, h] on which,
for every parameter point:
- g(l) ≤ 0 ≤ g(h);
- the slope enclosure of g is strictly positive.

## Why the zero found is the first fire

Fix a parameter point. Let W = [t0 − a_c, t0 − a_c + hi]. On W, g is strictly increasing (monotone
prefix) and its unique zero is v* = F − a_c. On [l, h], g is strictly increasing (positive slope)
and has exactly one zero z.

Fix T accepts rv only if [l, h] meets W for every parameter point. The engine checks the sufficient
condition l ≤ lo(t0 − a_c) + hi and h ≥ hi(t0 − a_c). Then [l, h] ∪ W is an interval, and g is
strictly increasing on it: on each piece, hence on the union, since the pieces overlap. Its zero is
unique, so z = v*. Hence F = a_c + v* ∈ a_c + rv.

The returned duration is u = (a_c + rv) − t0, computed with the correlated time arithmetic. It
encloses F − t0 for every parameter point. Fix T returns u only if it is narrower than u_plain;
otherwise it returns u_plain. Any failure to bracket, any arithmetic or domain error (for example a
probe before the memory anchor), and any failure of the meeting condition returns u_plain.

## Why it is tighter

If every arrival is shifted by the same d, then g does not change. Its root depends only on the
differences a_j − a_c and on the parameters, which are small at ε = 3e-3. The previous enclosure
absorbed the whole arrival uncertainty through the division by a plain slope enclosure.

## Scope

- One call site: the READY-with-memory fire root in `advance`. The scalar `ready_root` path without
  memory, lemma E and E2 are unchanged.
- No event order, branch, history, horizon or budget is changed or enlarged.
- Shared regression tests are in `tests/engine/test_relative_coordinates.py`. They exercise the
  frozen engine and `engine_next` separately: independent point/closed-form roots, invariance under
  a common clock translation, and fallback on an undecidable or wider relative enclosure.
