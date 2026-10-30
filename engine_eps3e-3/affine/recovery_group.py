"""Fix R (v3.3): protected recovery return overlapping an exterior event group.

unit() resolves a slow-recovery (p=2) refusal against a SINGLE exterior event
with the kernel's local-cycle resolver (cycle_local_A20.pending_window): it
encloses every admissible order of the return and the pending events, and
joins the forest only when every branch ends READY with no emission. The
group path (several overlapping events) had no such fallback and refused.
This module applies the SAME resolver and the SAME join rule to that path.

Preconditions (otherwise None, and the caller re-raises the original refusal):
  * the state is in slow recovery (p == 2);
  * the resolver certifies the window (its own checks: at most one additional
    fire, window shorter than the fast phase, no terminal event, branch budget);
  * every branch of the forest is READY with no emission.
No kernel map is modified and no branch is discarded.
"""
STATS = {'recovery_groups': 0}


def no_fire_group(b, s, pending, idx, cell, count):
    """Reuse A19's stricter, no-additional-fire resolver after A20 refuses.

    Only raw cuts and ERROR boundaries are admitted. They do not change the
    protected actuation ledger. A19 still enumerates all orders, propagates
    all learning gates, and certifies every post-return READY flow. Nothing
    is accepted merely because an order or branch budget was exhausted.
    """
    if s['p'] != 2 or idx >= len(pending):
        return None
    import branche_retour_A19 as recovery
    from types import FunctionType
    try:
        late = recovery.return_with_marks(s, f'{cell}:{count}:no-fire-return')
        upper = late.box().hi; stop = idx; group = []
        while stop < len(pending) and min(t.box().lo for t, _ in pending[stop:]) < upper:
            tt, actions = pending[stop]
            if any(a not in ('raw_off', 'error_on', 'error_off') for a, _, _ in actions):
                return None
            group.append((tt, actions)); upper = max(upper, tt.box().hi); stop += 1
        if not group:
            return None
        histories = s['actuation']; fire = s['fire'].token()
        original_return = recovery.return_with_marks
        def cached_return(ss, key):
            if (ss['fire'].token() == fire and len(ss['actuation']) == len(histories)
                    and all(x is y for x, y in zip(ss['actuation'], histories))):
                return late
            return original_return(ss, key)
        charge_joins = []
        class KernelView:
            def __getattr__(self, name):
                return getattr(b, name)

            def join_states(self, states, context):
                joined = b.join_states(states, context)
                # Both bounds contain every leaf pointwise. A common-generator
                # affine union can extend beyond all of its leaves' ranges;
                # intersecting with their plain envelope removes that excess.
                envelope = b.I(min(x['q'].lo for x in states),
                               max(x['q'].hi for x in states))
                before = joined['q']
                joined['q'] = before.intersect(envelope)
                charge_joins.append(dict(branches=len(states), affine_q=before.pair(),
                                         leaf_envelope=envelope.pair(), joined_q=joined['q'].pair()))
                return joined
        # Run the unchanged function body with a private binding: no global
        # monkeypatch and no cache shared between cells or parameter boxes.
        original = recovery.resolve
        guarded = FunctionType(original.__code__,
                               {**original.__globals__, 'return_with_marks': cached_return,
                                'b': KernelView()},
                               original.__name__, original.__defaults__, original.__closure__)
        joined, orders = guarded(s, group, upper, late, cell, count)
        if joined['p'] != 0 or joined['q'].hi >= 1:
            return None
    except (b.v.Ambiguous, AssertionError, ArithmeticError, ValueError) as error:
        key = f'{type(error).__name__}: {error}'
        refused = STATS.setdefault('no_fire_declined', {})
        refused[key] = refused.get(key, 0) + 1
        return None
    if b.PROFILE is not None:
        b.PROFILE.relative_order_proofs.append(dict(
            cell=cell, batch=count, guard='A19_no_additional_fire_recovery',
            events=len(group), orders=orders, return_time=late.box().pair(),
            terminal_q=joined['q'].pair(), charge_joins=charge_joins,
            predicate='Complete transitive group; unchanged A19 resolver certifies every surviving READY flow and retains all learning histories'))
    STATS['no_fire_recovery_groups'] = STATS.get('no_fire_recovery_groups', 0) + 1
    return joined, stop, len(group) + 1, orders


def resolve(b, s, pending, idx, cell, count):
    if s['p'] != 2:
        return None
    from cycle_local_A20 import pending_window
    try:
        forest, nextidx, handled = pending_window(s, pending, idx, cell, count)
    except b.v.Ambiguous:
        return no_fire_group(b, s, pending, idx, cell, count)
    if not forest.branches or not all(not x.emissions and x.state['p'] == 0 for x in forest.branches):
        return None
    joined = b.join_states([x.state for x in forest.branches],
                           dict(cell=cell, batch=count, kind='local_cycle_no_emission_group'))
    if b.PROFILE is not None:
        b.PROFILE.relative_order_proofs.append(dict(cell=cell, batch=count, guard='recovery_group_local_cycle',
            events=len(handled), branches=len(forest.branches), certificate=str(forest.certificate)[:2000]))
    STATS['recovery_groups'] += 1
    return joined, nextidx, len(handled) + 1, len(forest.branches)
