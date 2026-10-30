"""Fix S: case split of one cell on its ports' mark rates LM_j (parameter subdivision).

The cell's 15 port constants are independent, and each port's mark rate is the
affine symbol LM_j = LM_nom (1 + eps u_j), u_j in [-1, 1] (port_symbols.py).
The recovery rate b is learned from marks, so an enclosure of b, and of every
return date that depends on it, widens with the range of u_j. When a cell is
refused, it is recomputed on pieces of the box of (u_0, u_1, u_2): each
refused piece is bisected along one port (port 1, the cell's own lane, first;
then 0, then 2), up to MAX_DEPTH bisections and MAX_LEAVES computed pieces.

Soundness (rule 2, then rule 3). The pieces of a bisection cover their parent,
so the pieces of the final tree cover [-1, 1]^3: every device of the box lies
in some leaf. A leaf is the unchanged computation with u_j restricted to its
piece, under a symbol name of its own (no affine form ever mixes two pieces);
every other occurrence of LM, as the plain cell-level box, still covers the
whole box and so contains the leaf's value. Each leaf therefore encloses the
trajectories of its devices. Leaves are merged as in Fix F (fork.merge): only
when they emit the same number of pulses, emission k becoming the hull of the
leaves' k-th emissions and terminal states being joined. A refusal of a piece
at the maximal depth, or a budget overflow, refuses the cell with the original
error.
"""
from decimal import Decimal as D

STATS = {'splits': 0, 'leaves': 0}
ORDER = (1, 0, 2)
MAX_DEPTH = 6        # each port cut at most twice: pieces of width 1/2 of [-1, 1]
MAX_LEAVES = 64


def install(b, engine, port_symbols, fork):
    once = engine.compute_cell

    def compute_cell(layer, lane, trains, namespace):
        port_symbols.LM_PIECES.clear()
        try:
            return once(layer, lane, trains, namespace)
        except b.v.Ambiguous as error:
            original = error
        whole = {j: (D(-1), D(1)) for j in range(3)}
        stack, leaves, computed = [(whole, 0)], [], 0
        try:
            while stack:
                box, depth = stack.pop()
                if depth > 0:
                    port_symbols.LM_PIECES.clear(); port_symbols.LM_PIECES.update(box)
                    computed += 1
                    try:
                        leaves.append((box, once(layer, lane, trains, namespace)))
                        if __import__('os').environ.get('A22_DEBUG_SPLIT'):print('SPLIT leaf', box, flush=True)
                        continue
                    except b.v.Ambiguous as e:
                        if __import__('os').environ.get('A22_DEBUG_SPLIT'):print('SPLIT refused', box, str(e)[:80], flush=True)
                if depth == MAX_DEPTH or computed + len(stack) + 2 > MAX_LEAVES:
                    raise original
                j = ORDER[depth % 3]
                lo, hi = box[j]; mid = (lo + hi) / 2
                stack.append(({**box, j: (mid, hi)}, depth + 1))
                stack.append(({**box, j: (lo, mid)}, depth + 1))
        finally:
            port_symbols.LM_PIECES.clear()
        STATS['splits'] += 1; STATS['leaves'] += len(leaves)
        merged = fork.merge(b, engine, [x for _, x in leaves], layer, lane, kind='parameter_split_leaves')
        merged['state']['parameter_split_pieces'] = [
            {str(j): [str(lo), str(hi)] for j, (lo, hi) in sorted(box.items())} for box, _ in leaves]
        return merged

    engine.compute_cell = compute_cell
