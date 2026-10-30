"""Strict no-fire cover for an already admitted READY pulse memory.

Only used when the legacy q/current peak bound fails. No new input is
admitted within this flow; dep.evaluate preserves the correlations between
the current charge and the ages/amplitudes of admitted pulses. All closed
time pieces must have charge upper bound strictly below one. Otherwise the
original refusal is preserved. Experimental: new campaign identity required.
"""
STATS = {'attempts': 0, 'resolved': 0, 'refused': 0, 'pieces': 0}

def charge_bound(b, memory, t):
    """Intersect the affine range with the existing scalar pulse envelope.

    This extra range is used only for a guard proof; the propagated memory
    retains its affine forms. Common clock differences are taken BEFORE
    dropping correlation. Tail memories keep the original evaluator.
    """
    affine = b.dep.evaluate(memory, t)
    if not isinstance(memory, dict) or 'pulses' not in memory:
        return affine
    if any(term['tail'] for term in memory['pulses'].values()):
        return affine
    elapsed = t.minus(memory['anchor']).nonnegative().plain()
    plain = b.R + (memory['q'] - b.R).plain() * (-b.K * elapsed).exp()
    for term in memory['pulses'].values():
        age = t.minus(term['origin']).nonnegative().plain()
        plain = plain + term['g'].plain() * b.dep.pulse(age)
    return affine.intersect(plain)


def certify(b, s, tt, max_depth=8):
    STATS['attempts'] += 1
    if s['p'] != 0 or s.get('memory') is None:
        STATS['refused'] += 1
        return False
    I, D = b.I, b.D
    # Cover only the actual event-relative segment. The old forward box
    # start+[0,max(end-start)] may extend beyond the end for another member
    # of the parameter set, creating a false crossing inside the cluster.
    from commutation import _strict_prefix
    duration = tt.minus(s['t']).nonnegative()
    def relative_charge(lam):
        STATS['pieces'] += 1
        probe = b.shift(tt, -duration * lam, 'READY-event-relative-cover')
        return charge_bound(b, s['memory'], probe) - 1
    certificate = []
    if _strict_prefix(relative_charge, depth=max_depth, certificate=certificate):
        STATS['resolved'] += 1
        STATS['relative_resolved'] = STATS.get('relative_resolved', 0) + 1
        if getattr(b, 'PROFILE', None) is not None:
            b.PROFILE.relative_order_proofs.append(dict(
                guard='READY_event_relative_no_fire', start=s['t'].box().pair(),
                boundary=tt.box().pair(), cover=certificate,
                predicate='Q(end-lambda*(end-start))<1 on the complete normalized segment'))
        return True
    H = tt.minus(s['t']).nonnegative().hi
    stack = [(D(0), H, 0)]
    import intervalles_decimaux as iv
    while stack:
        lo, hi, depth = stack.pop()
        probe = b.shift(s['t'], I(lo, hi), 'READY-memory-cover')
        charge = charge_bound(b, s['memory'], probe)
        STATS['pieces'] += 1
        if charge.hi < 1:
            continue
        if depth >= max_depth:
            STATS['refused'] += 1
            return False
        mid = iv.NEAR.divide(iv.NEAR.add(lo, hi), D(2))
        if not lo < mid < hi:
            STATS['refused'] += 1
            return False
        stack.append((mid, hi, depth + 1))
        stack.append((lo, mid, depth + 1))
    STATS['resolved'] += 1
    return True
