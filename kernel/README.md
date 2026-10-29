# The physical kernel R

R is the hybrid cell of A22 and the network it forms. **It is not modified in this repository.**
Only the training protocol, the verification engine and the proof change. This page restates R
in English. The authoritative texts are in [`../model/`](../model/):
- `full_model_reference.md` is the original definition, in French; its status banner and section
  7 are historical;
- `CURRENT_SPEC.md` is the specification of the ±0.1 % / 28-pulse result.

The executable kernel is `../engine/kernel/`. `KERNEL_SHA256SUMS` lists its 52 source files. They
are byte-identical to the kernel of the base engine, so any change made for wider boxes lives
outside it, in `../engine/affine/`.

## Network and source

- 18 directed layers of 12 periodic lanes. Cell (n, j) receives, on ports 0, 1, 2, the emissions
  of (n−1, j−1), (n−1, j), (n−1, j+1), with lanes taken modulo 12.
- Layer 0 is the external source; only its lane 0 emits. Contacts have zero delay.
- A firing at time F emits the canonical current p_F(t) = a·e^(−a(t−F)) on [F, F+1), with a = ln 4.
- Each port carries at most one pulse at a time.

## Constants

| Fixed constants | Value |
|---|---|
| a | ln 4 |
| κ | 1/2 |
| r (main rest charge) | 1/10 |
| r_m (auxiliary rest charge) | 1/40 |
| main and auxiliary thresholds | 1 |
| actuation factors | 8 (gain), 1/2 (recovery) |
| b_max | 11/10 |
| energy pump | E′ = 10(100 − E) − W |
| nominal initial gains | (3/10, 6/5, 3/10) |
| nominal initial recovery b₀ | 2/25 |

The five **per-port parameters** are fixed in time and chosen independently for each cell and
each port, within the relative box ±ε. This box is the subject of the repository.

| Parameter | Nominal value |
|---|---|
| gain cap C_i | 4 |
| mark rate L_m,i | ln(5/4)/(1/50) |
| silent rate L_s,i | ln 8/(53/50) |
| error rate L_e,i | ln 4/(3/20) |
| auxiliary input gain M_i | (1 − r_m)/h(1/50) |

Here h(u) = a/(a − κ)·(e^(−κu) − e^(−au)) is the response of a READY charge to one canonical
pulse.

## State of a cell

- the main charge q;
- three auxiliary charges m_i and three log-gains z_i, with gains g_i = e^(z_i);
- the recovery variable b and the energy reserve E;
- a main mode P ∈ {READY, FAST, SLOW} and, for each port, an auxiliary mode
  H_i ∈ {READY, MARK, SILENT, ERROR};
- the incoming and outgoing currents still active.

## Main unit

- **READY**, with admission open: q′ = κ(r − q) + Σ_i g_i p_i(t).
- At the first upward crossing of q = 1, q is set to 1, admission closes and **FAST** begins:
  q′ = −a·q. The cell emits p_F for exactly one time unit. FAST ends at q = 1/4, which takes
  exactly 1 time unit.
- **SLOW**: q′ = −b(t)·q, until the downward crossing q = r. READY then resumes with q = r exactly.
  The return date is not prescribed: it follows from b.
- FAST and SLOW have the same admission and actuation gates.

## Auxiliaries and plasticity

Auxiliary i sees the raw current of its port even while the main unit is protected. While READY,
m_i′ = κ(r_m − m_i) + M_i p_i. Its first upward crossing of 1 starts the cycle below. Each section
ends exactly at the stated charge; at r_m the auxiliary is READY again.

| Mode | Equation | Ends at | Useful current |
|---|---|---|---|
| MARK | m_i′ = −L_m,i m_i | 4/5 | v_m,i = L_m,i m_i |
| SILENT | m_i′ = −L_s,i m_i | 1/10 | 0 |
| ERROR | m_i′ = −L_e,i m_i | r_m | v_e,i = L_e,i m_i |

While E > 0, the actuations are

    z_i′ = 8 v_e,i · 1[P = READY] · 1[z_i < ln C_i]
    b′   = ½ Σ_i v_m,i · 1[P ≠ READY] · 1[b < 1.1]

Both are monotone and are projected exactly onto their caps.
- A whole ERROR section received while the main unit is READY adds exactly Δz = 8(0.1 − 0.025) = 0.6,
  whatever L_e,i is.
- A whole MARK received under protection adds Δb = (1 − 0.8)/2 = 0.1.
- A partial reception contributes the integral over its true endpoints.

The cell consults no target, counter or software failure flag.

## Energy

E′ = 10(100 − E) − W. The work W is non-negative:
- in the main unit, the admitted current when READY, a·q when FAST, and 1.1 when SLOW;
- the currents admitted by READY auxiliaries;
- the drains of protected auxiliaries;
- the actuation movements.

The uniform bound W ≤ (3C + 3M + 1)a + 1.1 + 4.5 L_m + 2.4 L_e stays below 500 throughout the box
(it must be rechecked for each ε). So [50, 100] is invariant, and the power gates never close.

## Initial family

Independently in each cell, with δ = 1e-5:
- P is READY, q ∈ [r − δ, r + δ], z_i ∈ [ln g_i,nom − δ, ln g_i,nom + δ], b ∈ [0.08 − δ, 0.08 + δ],
  E ∈ [50, 100];
- each auxiliary is either READY with m_i ∈ [r_m − δ, r_m + δ], or at the end of its ERROR phase
  with m_i ∈ [r_m, r_m + δ].

There is no hidden earlier pulse.

## Event semantics

- Thresholds are first crossings within the current mode. Continuous states stay continuous at
  external arrivals.
- When enclosures do not fix an order, **every** compatible non-strict order must be covered.
  Equalities may belong to several zero-duration linearizations. No priority comes from a
  floating-point sort.
- Cap contacts are monotone projections.
- An unresolved root or an exhausted budget is a refusal, never a success.
