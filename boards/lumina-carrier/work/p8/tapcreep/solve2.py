"""Second A1<->A2 outer-layer defect: A1's SOUTH transition via, in the D2 fan-in.

Not the violation named in the work order, but the same defect on the same net
pair: via 17a75fde (0.6 mm at 47.450,81.250) sits 0.5500 mm from A2's B.Cu run
74189a96 (48.300,80.300)-(44.600,80.300), and A1's B.Cu run d8da1bcb is 0.5826 mm
from A2's corner 3c097738. Both are below the 0.60 mm outer requirement the work
order sets for ANY A1/A2 copper, so the pair does not pass on B.Cu until these
move too.

Fix shape: slide the via SOUTH (away from A2's westward run) and re-lay its two
attached stubs. Same balanced-margin objective as solve.py.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capsule import cap_dist                      # noqa: E402

# region.py parses argv at module level, so hide this script's own args from it
_argv, sys.argv = sys.argv, sys.argv[:1]
from region import collect_all                    # noqa: E402
sys.argv = _argv

PCB = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb'
CU = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
A1, A2 = '/poe/POE_TAP_A1', '/poe/POE_TAP_A2'
TAPS = (A1, A2)
ETH = ('/ETH_TXP', '/ETH_TXN', '/ETH_RXP', '/ETH_RXN')
SHIELD = '/poe/SHIELD'

DROP = ('17a75fde',      # A1 south via 0.6 @ (47.450,81.250)
        'd8da1bcb',      # A1 B.Cu (49.650,80.850)-(47.450,81.250)
        '5ca2efef')      # A1 F.Cu (47.450,81.250)-(47.000,81.700)

VIA_D, VIA_DRILL, TRK = 0.50, 0.30, 0.20
R_V, R_T = VIA_D / 2.0, TRK / 2.0
BCU_FROM = (49.650, 80.850)      # start of kept run cc8b4114's far end
FCU_TO = (47.000, 81.700)        # D2 pad 1 centre

src = io.open(PCB, encoding='utf-8').read()
ALL = [(L, n, c, t) for (L, n, c, t) in collect_all(src)
       if not any(u in t for u in DROP)]

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


WIN = (44.0, 78.5, 51.5, 84.5)
for L in CU:
    FOREIGN[L] = [(n, c, t) for (n, c, t) in FOREIGN[L]
                  if not (bbox(c, 1.35)[2] < WIN[0] or bbox(c, 1.35)[0] > WIN[2]
                          or bbox(c, 1.35)[3] < WIN[1] or bbox(c, 1.35)[1] > WIN[3])]
    print('FOREIGN %-7s %d items after locality filter' % (L, len(FOREIGN[L])))


def req(net):
    if net in ETH:
        return 1.30
    if net == SHIELD:
        return 0.60
    return 0.20


def need_for(L):
    return 0.60 if L in ('F.Cu', 'B.Cu') else 0.20


def own(P):
    it = {L: [((P, P, R_V), 'NEW via')] for L in CU}
    it['B.Cu'].append(((BCU_FROM, P, R_T), 'NEW B.Cu run'))
    it['F.Cu'].append(((P, FCU_TO, R_T), 'NEW F.Cu stub'))
    return it


def slacks(P):
    it = own(P)
    fs, ks = 9e9, 9e9
    for L in CU:
        for (c, t) in it[L]:
            for (fn, fc, ft) in FOREIGN[L]:
                fs = min(fs, cap_dist(c, fc) - req(fn))
            for (kc, kt) in KEPT[A2][L]:
                ks = min(ks, cap_dist(c, kc) - need_for(L))
    return fs, ks


# baseline: A1 copper the edit keeps, vs A2 - tells me the ceiling
print('\nKEPT A1 vs A2 (untouched copper) per layer:')
for L in CU:
    m = (9e9, None, None)
    for (ca, ta) in KEPT[A1][L]:
        for (cb, tb) in KEPT[A2][L]:
            d = cap_dist(ca, cb)
            if d < m[0]:
                m = (d, ta, tb)
    flag = '' if m[0] >= need_for(L) else '   <-- still blocking'
    print('  %-7s %.4f (need %.2f)%s  %s | %s' % (L, m[0], need_for(L), flag,
                                                  m[1], m[2]))

# D2 pad 1 is a 0.84 x 1.695 rect at (47.000,81.680), i.e. x 46.58..47.42,
# y 80.83..82.53. An unconstrained search walks the via INTO that pad (via-in-pad
# on a THT bridge-rectifier land - solder wicking, and not something this fix
# needs). Keep the via east of the pad edge and only slide it far enough SOUTH to
# clear A2's westward run, which is the whole point.
PAD_E = 47.42
if len(sys.argv) > 2:
    P = (float(sys.argv[1]), float(sys.argv[2]))
    if len(sys.argv) > 3:
        VIA_D = float(sys.argv[3])
        R_V = VIA_D / 2.0
    fs, ks = slacks(P)
    print('\nEVALUATING %s with via d=%.2f -> foreign %+.4f / A2 %+.4f'
          % (P, VIA_D, fs, ks))
else:
    best = (-9e9, None, None)
    x = PAD_E + 0.03
    while x <= 47.95 + 1e-9:
        y = 81.10
        while y <= 81.95 + 1e-9:
            Pc = (round(x, 4), round(y, 4))
            fs, ks = slacks(Pc)
            if fs >= 0 and ks >= 0:
                robust = min(fs, ks)
                if robust > best[0]:
                    best = (robust, Pc, (fs, ks))
            y += 0.025
        x += 0.025
    print('\nbest balanced margin = %+.4f mm at %s   (foreign %+.4f / A2 %+.4f)'
          % (best[0], best[1], best[2][0], best[2][1]))
    P = best[1]
it = own(P)
print('\nper-layer A1(new copper) vs A2:')
for L in CU:
    m = (9e9, None, None)
    for (c, t) in it[L]:
        for (kc, kt) in KEPT[A2][L]:
            d = cap_dist(c, kc)
            if d < m[0]:
                m = (d, t, kt)
    print('  %-7s %.4f mm (need %.2f)  %s | %s' % (L, m[0], need_for(L), m[1], m[2]))

print('\ntightest foreign clearances for the new copper:')
rows = []
for L in CU:
    for (c, t) in it[L]:
        for (fn, fc, ft) in FOREIGN[L]:
            d = cap_dist(c, fc)
            rows.append((d - req(fn), fn, L, d, req(fn), t, ft))
rows.sort()
for (s, fn, L, d, nd, t, ft) in rows[:10]:
    print('  %-14s %-7s d=%.4f need=%.2f slack=%+.4f  %s | %s'
          % (fn, L, d, nd, s, t, ft))
