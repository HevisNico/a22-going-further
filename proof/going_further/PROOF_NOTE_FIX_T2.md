# Fix T′: the recovery return in relative coordinates

**Rule used: 1 (exact flow enclosure).** The function whose zero is the return is unchanged; only
the time coordinate changes.

## Setting

In slow recovery, the return to READY is the zero of ell(t) = ln 2.5 − (capped recovery dose up to
t), along each actuation history h of the state.
`branche_retour_A19.return_with_marks` solves −hull_h ell_h(section + u) = 0 for u. Here section =
F + 1 is the end of the fast section after the last firing F. The returned date is section + u*.
That result is still computed and kept.

## The change

Let a_r be the origin of the latest mark among the histories' recorded marks: its date is an affine
time, correlated with the parameters. Any reference is sound; the latest mark is chosen because,
once marks have arrived, the return depends on them much more than on F. The same function is
solved in coordinates relative to a_r:

    g(v) = −hull_h ell_h(a_r + v),   with derivative enclosure hull_h rate_h(a_r + v),

on the range of (original return − a_r), using the kernel's own root routine `v.root`. The result
a_r + rv is returned when it is narrower than the original. Otherwise, and on any failure, the
original is returned.

## Why the zero found is the return

Fix a parameter point and the history h that the trajectory actually follows. Along h, the dose is
nondecreasing in time, because the recovery rate b is positive, so ell_h is nonincreasing
everywhere. Before the section it is constant, equal to ln 2.5 > 0.

`v.root` accepts a bracket [l, h_end] only if, for every parameter point and therefore for every
history in the hull:
- ell_h(a_r + l) ≥ 0 ≥ ell_h(a_r + h_end);
- the rate enclosure is strictly positive on the bracket.

So ell_h is strictly decreasing on the bracket and nonincreasing everywhere. Its zero in the bracket
is its unique zero on the whole time axis: the return of this trajectory. The enclosure returned by
the routine contains it, exactly as in the original call, which uses the same hull over histories.

The argument is simpler than for Fix T. No overlap condition is needed, because ell is monotone on
the whole axis rather than only on a prefix.

## Why it is tighter

When the last firing F is uncertain (width 0.59 in cell (18,5)) but marks received later fix most
of the dose, the return is nearly independent of F. In coordinates relative to F + 1, the root u*
absorbs the whole uncertainty of F, and the division by a slope enclosure that is not correlated
with it does not cancel it. In coordinates relative to the latest mark, the uncertainty of F
enters only through the small dose accumulated at the base rate before the marks.

## Scope

- One function: `return_with_marks`. It is used by the local-cycle resolver (coarse window and
  every branch return) and by the recovery paths that call it.
- No event order, branch, history, horizon or budget is changed or enlarged.
- Shared regression tests are in `tests/engine/test_relative_coordinates.py`. They exercise the
  frozen engine and `engine_next` separately: independent point/closed-form roots, invariance under
  a common clock translation, and fallback on an undecidable or wider relative enclosure.
