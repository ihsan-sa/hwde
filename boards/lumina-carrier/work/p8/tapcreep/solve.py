"""Search for a legal position for the two A-side transition vias.

The pocket is bounded on every side, so hand algebra is not trustworthy here.
This models EVERY constraint at once and grid-searches the two via positions,
maximising the A1<->A2 outer-layer gap subject to hard limits:

  A1 <-> A2            >= 0.60 mm outer, >= 0.20 mm inner   (the defect)
  POE_TAP <-> SHIELD   >= 0.60 mm   (check_creepage, 57 V, IPC-2221B B2)
  POE_TAP <-> ETH_*    >= 1.30 mm   (DRU rule magjack_isolation_barrier, ERROR)
  POE_TAP <-> anything >= 0.20 mm   (Default netclass clearance)
  via drill to drill   >= 0.25 mm edge-to-edge (min_hole_to_hole)
  via copper to drill  >= 0.25 mm             (min_hole_clearance)

Candidate edit (both nets keep their topology, only the transition moves):
  A1: via 49f94328 + F.Cu 9450339a + B.Cu a5fa8757  ->  via at PA,
      F.Cu (48.500,74.213)-PA, B.Cu PA-(49.650,80.850)
  A2: via 27cb891e + F.Cu e69731be + B.Cu 97a60d10  ->  via at PB,
      F.Cu PB-(50.250,72.250), B.Cu PB-(48.600,74.000)

Vias drop 0.60 -> 0.50 mm (min_via_diameter=0.5, min_via_annular_width=0.1 with
the 0.3 mm drill -> exactly legal; via 40e3f5b2 on this same net is already
0.5/0.3, so this is precedent, not a new risk).
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capsule import cap_dist                      # noqa: E402
from region import collect_all                    # noqa: E402

PCB = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb'
CU = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
A1, A2 = '/poe/POE_TAP_A1', '/poe/POE_TAP_A2'
TAPS = (A1, A2)
ETH = ('/ETH_TXP', '/ETH_TXN', '/ETH_RXP', '/ETH_RXN')
SHIELD = '/poe/SHIELD'

# uuid prefixes of the items the edit deletes
DROP = ('49f94328', '9450339a', 'a5fa8757',      # A1 via + F.Cu stub + B.Cu run
        '27cb891e', 'e69731be', '97a60d10')      # A2 via + F.Cu stub + B.Cu run

VIA_D = 0.50
VIA_DRILL = 0.30
TRK = 0.20
R_V = VIA_D / 2.0
R_T = TRK / 2.0

# fixed endpoints the new copper must still meet
A1_FCU_FROM = (48.500, 74.213)      # end of kept diagonal 3ac043d9
A1_BCU_TO = (49.650, 80.850)        # start of kept d8da1bcb
A2_FCU_FROM = (50.250, 72.250)      # end of kept d47e9eac
A2_BCU_TO = (48.600, 74.000)        # start of kept 3f5d20ff

src = io.open(PCB, encoding='utf-8').read()
ALL = [(L, n, c, t) for (L, n, c, t) in collect_all(src)
       if not any(u in t for u in DROP)]

# split: foreign copper (per layer) and the surviving tap copper (per layer)
FOREIGN = {L: [] for L in CU}
KEPT = {A1: {L: [] for L in CU}, A2: {L: [] for L in CU}}
for (L, n, c, t) in ALL:
    if L not in CU:
        continue
    if n in TAPS:
        KEPT[n][L].append((c, t))
    else:
        FOREIGN[L].append((n, c, t))


def bbox(c, pad=0.0):
    (a, b, r) = c
    return (min(a[0], b[0]) - r - pad, min(a[1], b[1]) - r - pad,
            max(a[0], b[0]) + r + pad, max(a[1], b[1]) + r + pad)


# Locality prefilter: only foreign copper that could possibly come within the
# largest rule (1.30 mm) of ANY candidate new copper can matter.
WIN = (46.9, 70.6, 52.0, 82.5)
for L in CU:
    keep = []
    for (n, c, t) in FOREIGN[L]:
        x0, y0, x1, y1 = bbox(c, 1.35)
        if x1 < WIN[0] or x0 > WIN[2] or y1 < WIN[1] or y0 > WIN[3]:
            continue
        keep.append((n, c, t))
    print('FOREIGN %-7s %d -> %d after locality filter' % (L, len(FOREIGN[L]), len(keep)))
    FOREIGN[L] = keep


def req(net):
    if net in ETH:
        return 1.30
    if net == SHIELD:
        return 0.60
    return 0.20


def build(PA, PB):
    """items[net][layer] = [(capsule, tag)] with the edit applied."""
    it = {A1: {L: list(KEPT[A1][L]) for L in CU},
          A2: {L: list(KEPT[A2][L]) for L in CU}}
    for L in CU:                                   # the two new vias, all layers
        it[A1][L].append(((PA, PA, R_V), 'NEW via A1'))
        it[A2][L].append(((PB, PB, R_V), 'NEW via A2'))
    it[A1]['F.Cu'].append(((A1_FCU_FROM, PA, R_T), 'NEW F.Cu A1 stub'))
    it[A1]['B.Cu'].append(((PA, A1_BCU_TO, R_T), 'NEW B.Cu A1 run'))
    it[A2]['F.Cu'].append(((PB, A2_FCU_FROM, R_T), 'NEW F.Cu A2 stub'))
    it[A2]['B.Cu'].append(((PB, A2_BCU_TO, R_T), 'NEW B.Cu A2 run'))
    return it


def score(PA, PB, detail=False):
    it = build(PA, PB)
    pair = {}
    for L in CU:
        m = (9e9, None, None)
        for (ca, ta) in it[A1][L]:
            for (cb, tb) in it[A2][L]:
                d = cap_dist(ca, cb)
                if d < m[0]:
                    m = (d, ta, tb)
        pair[L] = m
    outer = min(pair['F.Cu'][0], pair['B.Cu'][0])
    inner = min(pair['In1.Cu'][0], pair['In2.Cu'][0])

    worst_for = {}
    ok = True
    for net in TAPS:
        for L in CU:
            for (c, t) in it[net][L]:
                if not t.startswith('NEW'):
                    continue                        # kept copper already passes
                for (fn, fc, ft) in FOREIGN[L]:
                    d = cap_dist(c, fc)
                    need = req(fn)
                    slack = d - need
                    k = (fn, L)
                    if k not in worst_for or slack < worst_for[k][0]:
                        worst_for[k] = (slack, d, need, t, ft)
                    if slack < 0:
                        ok = False
    # hole-to-hole and hole-clearance for the two new drills
    hh = ((PA[0] - PB[0]) ** 2 + (PA[1] - PB[1]) ** 2) ** 0.5 - VIA_DRILL - 0.25
    if hh < 0:
        ok = False
    if detail:
        return pair, outer, inner, worst_for, ok, hh
    return (outer if (ok and outer >= 0.60 and inner >= 0.20) else -1), outer


def own_items(net, P):
    """The NEW copper this via contributes, per layer (depends only on P)."""
    out = {L: [((P, P, R_V), 'NEW via')] for L in CU}
    if net == A1:
        out['F.Cu'].append(((A1_FCU_FROM, P, R_T), 'NEW F.Cu stub'))
        out['B.Cu'].append(((P, A1_BCU_TO, R_T), 'NEW B.Cu run'))
    else:
        out['F.Cu'].append(((P, A2_FCU_FROM, R_T), 'NEW F.Cu stub'))
        out['B.Cu'].append(((P, A2_BCU_TO, R_T), 'NEW B.Cu run'))
    return out


def foreign_slack(net, P):
    """Worst (distance - required) of this via+stubs against every foreign net.
    Negative means illegal; larger is safer."""
    it = own_items(net, P)
    worst = 9e9
    for L in CU:
        for (c, t) in it[L]:
            for (fn, fc, ft) in FOREIGN[L]:
                s = cap_dist(c, fc) - req(fn)
                if s < worst:
                    worst = s
    return worst


def foreign_ok(net, P):
    return foreign_slack(net, P) >= 0.0


def need_for(L):
    return 0.60 if L in ('F.Cu', 'B.Cu') else 0.20


def vs_kept(net, P):
    """Min slack of this via's NEW copper against the OTHER tap's KEPT copper."""
    other = A2 if net == A1 else A1
    it = own_items(net, P)
    worst = 9e9
    for L in CU:
        for (c, t) in it[L]:
            for (kc, kt) in KEPT[other][L]:
                worst = min(worst, cap_dist(c, kc) - need_for(L))
    return worst


def feasible(net, x0, x1, y0, y1, step=0.025):
    """[(P, slack)] - slack = worst margin against foreign nets AND the other
    tap's untouched copper. Only strictly-legal points are returned."""
    out, n = [], 0
    x = x0
    while x <= x1 + 1e-9:
        y = y0
        while y <= y1 + 1e-9:
            n += 1
            P = (round(x, 4), round(y, 4))
            fs = foreign_slack(net, P)
            if fs >= 0.0:
                ks = vs_kept(net, P)
                if ks >= 0.0:
                    out.append((P, min(fs, ks)))
            y += step
        x += step
    print('  %s: %d/%d grid points legal vs foreign nets AND the other tap'
          % (net, len(out), n))
    return out


# Sanity: the copper NEITHER net's edit touches must already be far enough apart,
# otherwise moving vias cannot possibly fix the pair.
print('\nKEPT-vs-KEPT baseline (copper the edit does not touch):')
for L in CU:
    m = (9e9, None, None)
    for (ca, ta) in KEPT[A1][L]:
        for (cb, tb) in KEPT[A2][L]:
            d = cap_dist(ca, cb)
            if d < m[0]:
                m = (d, ta, tb)
    flag = '' if m[0] >= need_for(L) else '   <-- BLOCKER, edit cannot fix this'
    print('  %-7s %.4f mm (need %.2f)%s   %s | %s'
          % (L, m[0], need_for(L), flag, m[1], m[2]))

print('\nscanning feasible via positions...')
FA = feasible(A1, 48.90, 50.05, 73.50, 74.65)
FB = feasible(A2, 48.50, 50.35, 72.50, 74.45)

NA = {P: own_items(A1, P) for (P, s) in FA}
NB = {P: own_items(A2, P) for (P, s) in FB}

# Objective: maximise the WORST margin over everything at once, so the answer is
# not a solution that buys the tap gap by sitting 0.005 mm off the DRU barrier.
# The first optimum found scored 0.7261 mm on the tap gap with only +0.0046 mm
# slack to SHIELD and +0.0101 mm to the ETH barrier - technically legal, but a
# rounding difference between my capsule model and KiCad's own geometry could
# flip either one. Balanced margin is worth more than a bigger headline number.
best = (-9e9, None, None, None)
for (PA, sa) in FA:
    ia = NA[PA]
    for (PB, sb) in FB:
        ib = NB[PB]
        worst_o, worst_i = 9e9, 9e9
        for L in CU:
            m = 9e9
            for (ca, ta) in ia[L]:
                for (cb, tb) in ib[L]:
                    d = cap_dist(ca, cb)
                    if d < m:
                        m = d
            if L in ('F.Cu', 'B.Cu'):
                worst_o = min(worst_o, m)
            else:
                worst_i = min(worst_i, m)
        if worst_i < 0.20 or worst_o < 0.60:
            continue
        hh = ((PA[0] - PB[0]) ** 2 + (PA[1] - PB[1]) ** 2) ** 0.5 - VIA_DRILL - 0.25
        if hh < 0:
            continue
        robust = min(worst_o - 0.60, worst_i - 0.20, sa, sb, hh)
        if robust > best[0]:
            best = (robust, PA, PB, worst_o)
print('\nbest BALANCED solution: worst margin over all rules = %+.4f mm'
      % best[0])
print('  A1<->A2 outer gap at that point = %.4f mm' % best[3])
best = (best[3], best[1], best[2])
print('  PA (A1 via) = %s' % (best[1],))
print('  PB (A2 via) = %s' % (best[2],))

PA, PB = best[1], best[2]
pair, outer, inner, worst_for, ok, hh = score(PA, PB, detail=True)
print('\nlegal=%s  hole-to-hole slack=%.4f mm' % (ok, hh))
print('\nA1<->A2 per layer:')
for L in CU:
    d, ta, tb = pair[L]
    print('  %-7s %.4f mm   %s | %s' % (L, d, ta, tb))
print('\ntightest NEW-copper clearance to each foreign net (slack vs its rule):')
rows = sorted(worst_for.items(), key=lambda kv: kv[1][0])
for (fn, L), (slack, d, need, t, ft) in rows[:14]:
    print('  %-22s %-7s d=%.4f need=%.2f slack=%+.4f   %s | %s'
          % (fn, L, d, need, slack, t, ft))
