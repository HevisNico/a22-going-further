"""Fix H: resolve a protected recovery window once per actuation history.

The actuation ledger s['actuation'] is a disjunction of histories: the true
trajectory follows exactly one of them, and every other state field is an
enclosure valid for all of them. Hulling the ledger into one recovery rate can
make the return window wider than the local-cycle resolver accepts. When the
resolver refuses the joined ledger, the exterior group is formed exactly as
pending_window forms it for the joined ledger (transitive overlap through the
latest return), and the kernel's own resolver is applied to that same group
once per history. Each history's forest covers the trajectories of that
history; their union covers every trajectory. Any refusal of a part raises the
original refusal unchanged. No branch is discarded and no emission count is
merged here.
"""
import os
import sys

import fork

STATS = {'splits': 0}


def install(b, local):
    original = local.pending_window
    recovery = local.recovery

    def pending_window(s, pending, index, cell, count):
        # Under a Fix F pin, the kernel's exception path passes the unrestricted
        # state: restrict it to the pinned history first.
        s = fork.restrict(b, s)
        try:
            return original(s, pending, index, cell, count)
        except b.v.Ambiguous:
            if s['p'] != 2 or len(s.get('actuation', ())) < 2:
                raise
            refusal = sys.exc_info()[1]
        # Same group construction as pending_window, for the joined ledger.
        late = recovery.return_with_marks(s, f'{cell}:{count}:pending')
        upper = late.box().hi; stop = index; group = []
        while stop < len(pending):
            if min(t.box().lo for t, _ in pending[stop:]) >= upper:
                break
            t, actions = pending[stop]; upper = max(upper, t.box().hi)
            group.append((t, actions)); stop += 1
        if not group:
            raise refusal
        parts = []
        for k, history in enumerate(s['actuation']):
            single = dict(s)
            single['actuation'] = (history,)
            single['b'] = b.ac.bounds((history,), s['t'])
            key = f'{count}:h{k}'
            try:
                coarse = recovery.enclosure(single, group, f'{cell}:{key}:pending')
                parts.append(local.resolve(single, group, upper, coarse, cell, key))
            except b.v.Ambiguous as e:
                if os.environ.get('A22_DEBUG_SPLIT'):
                    print('SPLIT part', k, 'refused:', e, flush=True)
                # Fix F: recompute the cell once per history (affine/fork.py).
                raise fork.ForkRequest(s['t'].token(), len(s['actuation']))
        branches = tuple(x for f in parts for x in f.branches)
        certificate = dict(status='history_split_union', histories=len(parts),
                           parts=[f.certificate for f in parts])
        STATS['splits'] += 1
        return local.Forest(branches, certificate), stop, group

    local.pending_window = pending_window
