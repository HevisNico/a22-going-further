"""Fix T: READY first-fire root in coordinates relative to an admitted pulse.

The READY charge Q(t) = dep.evaluate(memory, t) is unchanged; only the time
coordinate changes. With a_c the origin of an admitted pulse (correlated date),
write t = a_c + v and g(v) = Q(a_c + v) - 1. When every arrival moves with a_c,
g does not move at all, so its root v* is much tighter than the root u* of
f(u) = Q(t0 + u) - 1, whose enclosure absorbs the arrival uncertainty.

Soundness. The original root u* (kept) lies in [0, hi], where Q is strictly
increasing (hi is before the certified peak), so for every parameter point
the first crossing is the unique zero of g on W = [t0 - a_c, t0 - a_c + hi].
The relative root is accepted only from a bracket [l, h] on which g has a
strictly positive slope enclosure and g(l) <= 0 <= g(h) for every parameter
point, and which meets W for every parameter point (l <= lo(t0 - a_c) + hi and
h >= hi(t0 - a_c)). g is then strictly increasing on the interval [l, h] U W,
so its zero in [l, h] is v*. Otherwise the original root is returned.
"""
from decimal import Decimal as D

STATS = {'relative_roots': 0, 'relative_declined': 0}


def install(b, engine):
    v, dep = b.v, b.dep

    def relative_root(s, memory, f, df, hi, cell, count):
        plain = v.root(f, df, D(0), hi, v.guessroot(f, hi))
        refs = [(term['g'].hi, term['origin']) for term in memory['pulses'].values() if not term['tail']]
        if not refs:
            return plain
        t0 = s['t']
        a_c = max(refs, key=lambda x: x[0])[1]
        off = t0.minus(a_c)
        probe = lambda w: b.shift(a_c, w, f'{cell}:{count}:relprobe')
        g = lambda w: dep.evaluate(memory, probe(w)) - 1
        dg = lambda w: dep.evaluate(memory, probe(w), True)
        lo, top = off.lo + plain.lo, off.hi + plain.hi
        try:
            guess = (lo + top) / 2
            rv = v.root(g, dg, lo, top, guess)
            bracket = rv.plain()
        except (v.Ambiguous, AssertionError, ArithmeticError, ValueError):
            STATS['relative_declined'] += 1
            return plain
        # The bracket must meet W for every parameter point (see docstring).
        if not (bracket.lo <= off.lo + hi and bracket.hi >= off.hi):
            STATS['relative_declined'] += 1
            return plain
        u = b.shift(a_c, rv, f'{cell}:{count}:relfire').minus(t0)
        if u.width() < plain.width():
            STATS['relative_roots'] += 1
            return u
        return plain

    b.RELATIVE_ROOT = relative_root
