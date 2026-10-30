"""Fix F: case split of a cell on its actuation histories (scenario propagation).

The actuation ledger is a disjunction: every trajectory follows exactly one of
its histories, and every other state field is an enclosure valid for all of
them. When a protected recovery window cannot be resolved for the joined
ledger, even history by history on a common group (Fix H), the cell is
recomputed once per history, with the state restricted to that history at the
state where the refusal occurred (identified by its exact time token). Each
recomputation covers the trajectories of its history; their union covers the
cell. Recomputations are deterministic, so every leaf reaches the fork state
identically. Leaves are merged only when they emit the same number of pulses:
emission k becomes a fresh time whose box is the hull of the leaves' k-th
emissions, and terminal states are joined by the kernel's join_states.
Otherwise, or beyond the leaf budget, the cell is refused.
"""
from decimal import Decimal as D

PINS = {}
STATS = {'forks': 0, 'leaves': 0}
MAX_LEAVES = 16


class ForkRequest(BaseException):
    """Not an Exception: no generic handler may swallow it."""
    def __init__(self, key, histories):
        super().__init__(f'fork on {histories} actuation histories')
        self.key, self.histories = key, histories


def restrict(b, s):
    """Restrict s to its pinned history, if s is a pinned fork state."""
    k = PINS.get(s['t'].token())
    if k is None or len(s.get('actuation', ())) < 2:
        return s
    history = s['actuation'][k]
    single = dict(s)
    single['actuation'] = (history,)
    single['b'] = b.ac.bounds((history,), s['t'])
    return single


def install(b, engine):
    advance = b.advance
    def pinned_advance(s, boundary, cell, count):
        # The fork state may enter advance() or be produced by it (cluster path).
        state, kind = advance(restrict(b, s), boundary, cell, count)
        return restrict(b, state), kind
    b.advance = pinned_advance
    once = engine.compute_cell

    def compute_cell(layer, lane, trains, namespace):
        stack, leaves = [{}], []
        while stack:
            pins = stack.pop()
            PINS.clear(); PINS.update(pins)
            if __import__('os').environ.get('A22_DEBUG_FORK'):print('FORK leaf', sorted(pins.values()), len(pins), flush=True)
            try:
                leaves.append(once(layer, lane, trains, namespace))
            except ForkRequest as request:
                if request.key in pins:
                    raise b.v.Ambiguous('fork state reached again under its own pin')
                stack.extend({**pins, request.key: k} for k in range(request.histories))
                STATS['forks'] += 1
            finally:
                PINS.clear()
            if len(leaves) + len(stack) > MAX_LEAVES:
                raise b.v.Ambiguous('history fork budget exceeded')
        STATS['leaves'] += len(leaves)
        return leaves[0] if len(leaves) == 1 else merge(b, engine, leaves, layer, lane)

    engine.compute_cell = compute_cell


def merge(b, engine, leaves, layer, lane, kind='history_fork_leaves'):
    """Union of leaves that each cover a case of the cell (rule 2), merged by hull (rule 3).

    kind names the split: 'history_fork_leaves' (Fix F) or 'parameter_split_leaves' (Fix S).
    """
    counts = {len(x['outputs']) for x in leaves}
    if len(counts) != 1:
        raise b.v.Ambiguous(f'{kind}: leaves emit different pulse counts {sorted(counts)}')
    hull = lambda xs: engine.I(min(x.lo for x in xs), max(x.hi for x in xs))
    tag = 'fork-out' if kind == 'history_fork_leaves' else 'split-out'
    outputs = tuple(engine.temporal.Time(f'{layer},{lane}:{tag}:{k}', hull([x['outputs'][k].box() for x in leaves]))
                    for k in range(counts.pop()))
    pair = lambda ps: (min(D(p[0]) for p in ps), max(D(p[1]) for p in ps))
    states = [x['state'] for x in leaves]
    state = dict(states[0])
    state['q'] = pair([x['q'] for x in states]); state['b'] = pair([x['b'] for x in states])
    state['g'] = [pair([x['g'][j] for x in states]) for j in range(3)]
    state['m'] = [pair([x['m'][j] for x in states]) for j in range(3)]
    if all('terminal_affine' in x for x in states):
        state['terminal_affine'] = b.join_states([x['terminal_affine'] for x in states],
                                                 dict(cell=f'{layer},{lane}', kind=kind))
    if all('width_profile' in x for x in states):
        # Every leaf's recorded mechanisms are kept, so the census sees all of them.
        profile = dict(states[0]['width_profile'])
        for key in ('relative_order_proofs', 'recovery_branch_groups', 'pruned_recovery_orders'):
            profile[key] = [p for x in states for p in x['width_profile'].get(key, [])]
        for key in ('maximum_distinct_actuation_histories', 'maximum_distinct_deposit_histories'):
            profile[key] = max(x['width_profile'][key] for x in states)
        state['width_profile'] = profile
    state[kind] = len(leaves)
    metrics = dict(leaves[0]['metrics'])
    metrics.update(pulses=len(outputs), max_width=str(max((t.box().width() for t in outputs), default=D(0))))
    metrics[kind] = len(leaves)
    return {'outputs': outputs, 'state': state, 'metrics': metrics}
