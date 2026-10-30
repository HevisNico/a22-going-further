"""Conservative fallbacks for a refused READY guard with pulse memory.

If the charge is strictly above threshold at the actual external boundary,
reuse the slope-free first-crossing cover. This avoids requiring the legacy
peak-location box to give a common monotone bracket. The normalized clock
boundary - (1-u)*(boundary-start), u in [0,1], preserves the boundary's atoms.
Continuity and the two strict endpoint signs prove a first fire strictly
before that boundary, without any derivative or nominal event ordering.

No new arrival is processed before the requested external boundary. Admitted
pulse amplitudes are constant; the pulse-memory evaluator includes raw cuts.
If its outward enclosure is below1 on every closed piece of[0,H], no first
threshold crossing exists before that boundary. This permits flowing to it.
An undecided piece, finite budget failure, or other refusal propagates the
original exception. This is an experimental kernel addition, not qualification.
"""
def first_fire(b, s, boundary, cell, count):
    """Return a certified first-fire clock, or None; no physical map changes."""
    from commutation import _first_crossing_cover
    from cluster_memory_cover import charge_bound
    if s['p'] != 0 or s.get('memory') is None:
        return None
    duration = boundary.minus(s['t']).nonnegative()
    endpoint = charge_bound(b, s['memory'], boundary) - 1
    if endpoint.lo <= 0:
        return None
    probe = lambda u: b.shift(boundary, -duration * (1-u), f'{cell}:{count}:relative-first-fire')
    charge = lambda u: charge_bound(b, s['memory'], probe(u)) - 1
    rho = None
    route = 'slope_free_cover'
    # Retain the existing affine root when monotonicity is certified on the
    # WHOLE interval. A positive derivative only near a root would not prove
    # that it is the first root.
    derivative = lambda u: duration * b.dep.evaluate(s['memory'], probe(u), True)
    if charge(b.I(0)).hi < 0 and derivative(b.I(0,1)).lo > 0:
        try:
            rho = b.v.root(charge, derivative, b.D(0), b.D(1), b.v.guessroot(charge, b.D(1)))
            route = 'monotone_affine_root'
        except (b.v.Ambiguous, ValueError, AssertionError):
            pass
    if rho is None:
        rho = _first_crossing_cover(charge, b.D(1))
    if rho is None:
        return None
    fire = probe(rho)
    if b.PROFILE is not None:
        b.PROFILE.relative_order_proofs.append(dict(
            cell=cell, batch=count, guard='READY_relative_first_crossing',
            start=s['t'].box().pair(), boundary=boundary.box().pair(),
            start_margin=charge(b.I(0)).pair(), boundary_margin=endpoint.pair(),
            normalized_root=rho.pair(), fire=fire.box().pair(),
            route=route,
            predicate='Continuous fixed-memory READY flow; strict endpoint signs; slope-free cover encloses first crossing before the actual boundary'))
    return fire


def install(engine):
    b,I,D,iv=engine.b,engine.I,engine.D,engine.iv
    original=b.advance
    def advance(s,boundary,cell,count):
        try:return original(s,boundary,cell,count)
        except b.v.Ambiguous as error:
            legacy_overlap = str(error)=='ready guard still overlaps external boundary or possible tangency'
            root_refusal = str(error).startswith('root bracket failed:')
            if (not (legacy_overlap or root_refusal)
                    or s['p']!=0 or s.get('memory') is None):raise
            fire = first_fire(b, s, boundary, cell, count)
            if fire is not None:
                out = b.fire_reset(b.flowing(s, fire))
                if b.PROFILE is not None:b.PROFILE.guard('fire', fire)
                return out, 'fire'
            if not legacy_overlap:
                raise
            H=boundary.minus(s['t']).nonnegative().hi
            stack=[(D(0),H,0)];leaves=[]
            while stack:
                lo,hi,depth=stack.pop()
                t=b.shift(s['t'],I(lo,hi),f'{cell}:{count}:nofire-cover')
                charge=b.dep.evaluate(s['memory'],t)
                if charge.hi<1:
                    leaves.append((lo,hi,charge.hi));continue
                if depth==16 or len(leaves)+len(stack)>65536:raise error
                mid=iv.NEAR.divide(iv.NEAR.add(lo,hi),D(2))
                if not lo<mid<hi:raise error
                stack.append((mid,hi,depth+1));stack.append((lo,mid,depth+1))
            if not leaves or leaves[0][0]!=0 or leaves[-1][1]!=H:raise error
            if any(x[1]!=y[0] for x,y in zip(leaves,leaves[1:])):raise error
            if b.PROFILE is not None:
                b.PROFILE.relative_order_proofs.append(dict(cell=cell,batch=count,guard='no_fire_cover',
                    start=s['t'].box().pair(),boundary=boundary.box().pair(),horizon=str(H),
                    cover=[[str(x) for x in leaf] for leaf in leaves],
                    predicate='Every closed cover piece has memory charge upper bound strictly below1'))
            return b.flowing(s,boundary),'external'
    b.advance=advance
