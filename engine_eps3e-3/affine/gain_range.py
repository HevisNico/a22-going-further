"""Range tightening at pulse admission; the logarithmic learning ledger stays intact.

For every represented z, exp(z) belongs both to the affine exponential
and to [exp(inf z), exp(sup z)]. Their intersection removes nonlinear
remainder overshoot. Only admitted gains are tightened; exp arithmetic,
the physical maps, and the learning histories are unchanged.
"""
from decimal import Decimal


def enclose(gain, log_gain):
    scalar = log_gain.plain().exp()
    # Preserve useful affine dependence for narrow gains. The 5% threshold
    # only chooses between two valid enclosures; it is not a physical bound
    # or an acceptance margin. Tiny range improvements need not discard the
    # correlations carried by the original affine amplitude.
    if gain.width() <= scalar.width() * Decimal('1.05'):
        return gain
    return gain.intersect(scalar)


def install(b):
    original_act = b.act
    original_memory = b.new_memory

    def act(s, changes):
        result = original_act(s, changes)
        if s['p'] != 0 or result.get('memory') is None:
            return result
        admitted = [(j, origin) for action, j, origin in changes
                    if action == 'raw_on' and not s['caps'][j]]
        if not admitted:
            return result
        memory = dict(result['memory']); pulses = dict(memory['pulses'])
        for j, origin in admitted:
            key = (j, origin.token()); term = dict(pulses[key])
            term['g'] = enclose(term['g'], s['z'][j]); pulses[key] = term
        memory['pulses'] = pulses; result['memory'] = memory
        return result

    def new_memory(s):
        memory = original_memory(s)
        pulses = dict(memory['pulses'])
        for key, old in pulses.items():
            j = key[0]
            if not s['caps'][j]:
                term = dict(old); term['g'] = enclose(old['g'], s['z'][j])
                pulses[key] = term
        return dict(memory, pulses=pulses)

    b.act = act
    b.new_memory = new_memory
