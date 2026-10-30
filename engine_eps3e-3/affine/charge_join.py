"""Keep the charge union inside the envelope of ALL its constituent states.

The original affine join remains pointwise valid but its scalar range can
exceed every leaf range. The envelope [min(q_i.lo), max(q_i.hi)] is a second
valid enclosure of the entire union. Their intersection preserves every
branch. No physical threshold is used, and no learning history is changed.
"""

STATS = {'joins': 0, 'tightened': 0, 'empty_memories_restored': 0}


def install(b):
    original = b.join_states

    def join_states(states, context):
        states = list(states)
        joined = original(states, context)
        STATS['joins'] += 1
        before = joined['q']
        lo = min(state['q'].lo for state in states)
        hi = max(state['q'].hi for state in states)
        if before.lo < lo or before.hi > hi:
            envelope = b.I(lo, hi)
            joined['q'] = before.intersect(envelope)
            STATS['tightened'] += 1
            if getattr(b, 'PROFILE', None) is not None:
                b.PROFILE.relative_order_proofs.append(dict(
                    guard='charge_join_envelope', context=context,
                    branches=len(states), time=joined['t'].box().pair(),
                    affine_q=before.pair(), leaf_envelope=envelope.pair(),
                    joined_q=joined['q'].pair(),
                    predicate='Both enclosures contain every leaf charge; their intersection retains the entire union'))
        # Different return clocks can make dep.join forget every memory.
        # With no active raw input, q(t) is exactly R+(q0-R)exp(-K(t-t0))
        # until the next admission. Re-anchor that existing formula at the
        # actual joined q0; do not replace the residual charge by R.
        if (joined.get('p') == 0 and joined.get('memory') is None
                and joined.get('raw') == [None, None, None]):
            joined['memory'] = b.dep.start(joined['t'], joined['q'], [])
            STATS['empty_memories_restored'] += 1
            if getattr(b, 'PROFILE', None) is not None:
                b.PROFILE.relative_order_proofs.append(dict(
                    guard='empty_READY_memory_restored', context=context,
                    time=joined['t'].box().pair(), charge=joined['q'].pair(),
                    predicate='READY with no raw input: retain q0 and re-anchor the existing homogeneous solution; later admissions use unchanged dep.add'))
        return joined

    b.join_states = join_states
