"""Fix D1: delay of the first mark of a port whose first pulse arrives after the initial slab.

The kernel encloses the delay of the first mark of every port (k == 0) by D1,
the box of the first-pulse delay at time 0: initial auxiliary charge
RM + eta with |eta| <= delta, possibly attenuated by a residual ERROR phase
ending before U0. For a first pulse arriving at a >= U0, both effects are over:
a residual ERROR has ended (charge exactly RM) and a READY auxiliary has
relaxed to RM + eta e^(-K a). The raw pulse is admitted at once, so the
auxiliary charge after the arrival is
    RM + eta e^(-K a) e^(-K u) + M_j h(u),
and the mark delay is its first crossing of 1: the root that defines D0, with
the decayed eta (eta = 0 in the residual-ERROR case lies in the range). It is
computed by the kernel's own root routine, as D0 is. For a < U0 the kernel's
D1 is kept. Rule 1 (exact flow) and the kernel's root enclosure.
"""
from decimal import Decimal as D

STATS = {'decayed_first_delays': 0}


def install(engine):
    b, I, v = engine.b, engine.I, engine.v
    plain_settings = engine.settings_cell
    b.FIRST_DELAY = lambda j, start: b.D1_PORTS[j]

    def settings(cell):
        plain_settings(cell)
        A, K, RM, U0, DELTA = b.A, b.K, b.RM, b.U0, b.DELTA

        def hh(u): return A / (A - K) * ((-K * u).exp() - (-A * u).exp())

        def dh(u): return A / (A - K) * (A * (-A * u).exp() - K * (-K * u).exp())

        def first_delay(j, start):
            a = start.box().lo
            if a < U0.hi:
                return b.D1_PORTS[j]
            decay = (-K * I(a)).exp().hi
            eta = I(-DELTA.hi, DELTA.hi) * I(decay)
            M = b.M_PORTS[j]
            fn = lambda u: RM + eta * (-K * u).exp() + M * hh(u) - 1
            df = lambda u: -K * eta * (-K * u).exp() + M * dh(u)
            root = v.root(fn, df, D(0), D('.1'), .02)
            STATS['decayed_first_delays'] += 1
            return root
        b.FIRST_DELAY = first_delay
    engine.settings_cell = settings
