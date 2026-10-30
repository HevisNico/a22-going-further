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


def merge_profiles(profiles):
    """Inventory every recomputed leaf; shared prefixes may be counted repeatedly."""
    from copy import deepcopy
    out = deepcopy(profiles[0])
    for key in ('relative_order_proofs', 'recovery_branch_groups', 'pruned_recovery_orders',
                'recovery_saturation_observations', 'gain_saturation_observations',
                'largest_increases'):
        out[key] = [entry for profile in profiles for entry in profile[key]]
    for key in ('categories', 'guard_dates'):
        out[key] = {}
        for profile in profiles:
            for name, values in profile[key].items():
                total = out[key].setdefault(name, {})
                for field, value in values.items():
                    if field == 'count':
                        total[field] = total.get(field, 0) + value
                    else:
                        total[field] = str(max(D(total.get(field, value)), D(value)))
    out['inputs']['maximum_arrival_width'] = str(max(
        D(profile['inputs']['maximum_arrival_width']) for profile in profiles))
    for key in ('maximum_distinct_actuation_histories', 'maximum_distinct_deposit_histories'):
        out[key] = max(profile[key] for profile in profiles)
    out['history_fork_inventory'] = dict(leaves=len(profiles),
        counting='All leaf executions, including repeated common prefixes; no leaf proof discarded')
    return out


def merge(b, engine, leaves, layer, lane):
    if not leaves:
        raise b.v.Ambiguous('no history fork leaves')
    counts = {len(x['outputs']) for x in leaves}
    if len(counts) != 1:
        raise b.v.Ambiguous(f'history leaves emit different pulse counts {sorted(counts)}')
    states = [x['state'] for x in leaves]
    if not all('terminal_affine' in x for x in states):
        raise b.v.Ambiguous('history leaf lacks its terminal affine state')
    literal = [x['terminal_affine'] for x in states]
    # join_states does not check these discrete fields itself. Mixed modes or
    # unfinished queues must remain separate scenarios instead of using leaf 0.
    for x in literal:
        if (x['p'] != 0 or x['aux'] != [0]*3 or x['raw'] != [None]*3
                or x['t'].token() != literal[0]['t'].token()):
            raise b.v.Ambiguous('history leaves do not share a quiescent terminal clock')
    for x in states:
        if x['main_phase'] != 0 or x['aux_phases'] != [0]*3 or x['pending']:
            raise b.v.Ambiguous('history leaf has pending terminal activity')
    joined = b.join_states(literal, dict(cell=f'{layer},{lane}', kind='history_fork_leaves'))
    hull = lambda xs: engine.I(min(x.lo for x in xs), max(x.hi for x in xs))
    outputs = tuple(engine.temporal.Time(f'{layer},{lane}:fork-out:{k}',
                    hull([x['outputs'][k].box() for x in leaves]))
                    for k in range(counts.pop()))
    pair = lambda ps: (min(D(p[0]) for p in ps), max(D(p[1]) for p in ps))
    gains = [(b.C if joined['caps'][j] else joined['z'][j].exp()) for j in range(3)]
    profile = merge_profiles([x['width_profile'] for x in states])
    profile['maximum_distinct_actuation_histories'] = max(
        profile['maximum_distinct_actuation_histories'], len(joined['actuation']))
    profile['maximum_distinct_deposit_histories'] = max(
        profile['maximum_distinct_deposit_histories'], max(map(len, joined['depot'])))
    state = dict(terminal_affine=joined, q=joined['q'].pair(), b=joined['b'].pair(),
        g=[g.pair() for g in gains], m=[pair([x['m'][j] for x in states]) for j in range(3)],
        E=[min(x['E'][0] for x in states), max(x['E'][1] for x in states)], main_phase=joined['p'], aux_phases=list(joined['aux']),
        pending=[], caps=list(joined['caps']), b_stop=joined['bstop'], gain_stops=sum(joined['caps']),
        clusters=sum(x['clusters'] for x in states), orders_enclosed=sum(x['orders_enclosed'] for x in states),
        events=sum(x['events'] for x in states), width_profile=profile,
        actuation_summary=[dict(full_marks=h.full, partial_marks=len(h.partial), saturated=h.saturated)
                           for h in joined['actuation']],
        deposit_summary=[[dict(full_errors=h.full, partial_errors=len(h.partial), clamped=h.clamped)
                          for h in hs] for hs in joined['depot']],
        width=str(max(g.width() for g in gains)), q_width=str(joined['q'].width()),
        b_width=str(joined['b'].width()),
        maximum_time_width=str(max((t.box().width() for t in outputs), default=D(0))),
        history_fork_leaves=len(leaves))
    root_search = {}
    for leaf in leaves:
        for key, value in leaf['metrics']['root_search'].items():
            root_search[key] = root_search.get(key, 0) + value
    metrics = dict(layer=layer, lane=lane, pulses=len(outputs), clusters=state['clusters'],
        orders=state['orders_enclosed'], max_width=state['maximum_time_width'],
        elapsed_seconds=sum(x['metrics']['elapsed_seconds'] for x in leaves),
        cpu_seconds=sum(x['metrics']['cpu_seconds'] for x in leaves), root_search=root_search,
        peak_rss_kib=max(x['metrics']['peak_rss_kib'] for x in leaves), history_fork_leaves=len(leaves))
    return {'outputs': outputs, 'state': state, 'metrics': metrics}
