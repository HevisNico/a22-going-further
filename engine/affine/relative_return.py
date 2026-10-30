"""Fix T': protected-recovery return root in coordinates relative to a mark.

branche_retour_A19.return_with_marks encloses the return to READY as
section + u*, where section = fire + 1 and u* is the zero of ell along the
protected history. When the fire date is uncertain but the return is fixed
mainly by later marks, that coordinate carries the whole fire uncertainty into
u*. The same function ell is solved here in coordinates relative to the
origin a_r of the latest mark of the history: t = a_r + v.

Soundness. Along a protected history, ell(t) = ln 2.5 - capped dose is
nonincreasing in t (the recovery rate b is positive), constant before the
section, and strictly decreasing wherever the rate enclosure is strictly
positive. The kernel root routine accepts a bracket [l, h] only if
-ell(l) <= 0 <= -ell(h) and the rate enclosure on [l, h] is strictly positive
for every parameter point. Then ell is strictly decreasing on [l, h] and
nonincreasing everywhere, so its zero in [l, h] is the unique zero of ell: the
return. The original root is computed first and returned whenever the relative
one fails or is not narrower.
"""
from decimal import Decimal as D

STATS = {'relative_returns': 0, 'relative_return_declined': 0}


def install(b, recovery):
    original = recovery.return_with_marks
    ac = recovery.ac
    hull = recovery.hull

    def return_with_marks(s, key):
        plain = original(s, key)
        marks = [m for h in s['actuation'] for m in h.marks]
        if not marks:
            return plain
        ref = max(marks, key=lambda m: m.origin.box().hi).origin
        probe = lambda w: b.shift(ref, w, key + ':rel-probe')
        g = lambda w: -hull([ac.ell(h, probe(w), False) for h in s['actuation']])
        dg = lambda w: hull([ac.rate(h, probe(w), False) for h in s['actuation']])
        span = plain.minus(ref)
        try:
            rv = b.v.root(g, dg, span.lo, span.hi, b.v.guessroot(g, span.hi) if span.lo <= 0 else (span.lo + span.hi) / 2)
        except (b.v.Ambiguous, AssertionError, ArithmeticError, ValueError):
            STATS['relative_return_declined'] += 1
            return plain
        out = b.shift(ref, rv, key + ':rel-ready')
        if out.box().width() < plain.box().width():
            STATS['relative_returns'] += 1
            return out
        return plain

    recovery.return_with_marks = return_with_marks
