"""Inventory + per-layer copper-to-copper gap for the PoE tap differential pairs.

Reuses the capsule model from work/p7/pad_gap.py (via capsule.py).

Every copper item on the four POE_TAP nets is reduced to a capsule per layer:
  track segment -> (start, end, width/2)
  via           -> (at, at, size/2) on every layer it spans
  pad           -> spine() from pad_gap.py, on every copper layer it occupies
  zone fill     -> reported separately (polygon, not a capsule) if present

Usage: tap_inv.py [--pcb PATH] [--json OUT]
"""
import argparse
import io
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capsule import blocks, spine, cap_dist   # noqa: E402

DEF_PCB = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb'
CU = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
PAIRS = [('/poe/POE_TAP_A1', '/poe/POE_TAP_A2'),
         ('/poe/POE_TAP_B1', '/poe/POE_TAP_B2')]
NETS = [n for p in PAIRS for n in p]


def num(s):
    return float(s)


def expand(l1, l2):
    """Layer span of a via/pad given its two endpoint layer names."""
    if l1 == '*.Cu' or l2 == '*.Cu':
        return list(CU)
    try:
        i, j = CU.index(l1), CU.index(l2)
    except ValueError:
        return [x for x in (l1, l2) if x in CU]
    return CU[min(i, j):max(i, j) + 1]


def collect(src):
    """items[net][layer] = list of (capsule, tag)"""
    items = {n: {L: [] for L in CU} for n in NETS}
    zones = []
    arcs = []

    # ---- free tracks: segment / arc, top level ----
    for tok in ('segment', 'arc'):
        for (s, e) in blocks(src, tok):
            b = src[s:e]
            nm = re.search(r'\(net\s+(?:\d+\s+)?"([^"]*)"\)', b)
            ln = re.search(r'\(layer\s+"([^"]+)"', b)
            wd = re.search(r'\(width\s+([\d.]+)\)', b)
            st = re.search(r'\(start\s+(-?[\d.]+)\s+(-?[\d.]+)\)', b)
            en = re.search(r'\(end\s+(-?[\d.]+)\s+(-?[\d.]+)\)', b)
            uu = re.search(r'\(uuid\s+"?([0-9a-fA-F-]+)"?\)', b)
            if not (nm and ln and wd and st and en):
                continue
            net = nm.group(1)
            if net not in items or ln.group(1) not in CU:
                continue
            cap = ((num(st.group(1)), num(st.group(2))),
                   (num(en.group(1)), num(en.group(2))),
                   num(wd.group(1)) / 2.0)
            tag = '%s w=%.3f uuid=%s' % (tok, num(wd.group(1)),
                                         uu.group(1) if uu else '?')
            items[net][ln.group(1)].append((cap, tag))
            if tok == 'arc':
                arcs.append(tag)

    # ---- vias ----
    for (s, e) in blocks(src, 'via'):
        b = src[s:e]
        nm = re.search(r'\(net\s+(?:\d+\s+)?"([^"]*)"\)', b)
        at = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)\)', b)
        sz = re.search(r'\(size\s+([\d.]+)\)', b)
        dr = re.search(r'\(drill\s+([\d.]+)\)', b)
        ly = re.search(r'\(layers\s+"([^"]+)"\s+"([^"]+)"\)', b)
        uu = re.search(r'\(uuid\s+"?([0-9a-fA-F-]+)"?\)', b)
        if not (nm and at and sz and ly):
            continue
        net = nm.group(1)
        if net not in items:
            continue
        x, y, d = num(at.group(1)), num(at.group(2)), num(sz.group(1))
        cap = ((x, y), (x, y), d / 2.0)
        tag = 'via d=%.3f drill=%s uuid=%s' % (
            d, dr.group(1) if dr else '?', uu.group(1) if uu else '?')
        for L in expand(ly.group(1), ly.group(2)):
            items[net][L].append((cap, tag))

    # ---- pads inside footprints ----
    for (fs, fe) in blocks(src, 'footprint'):
        fb = src[fs:fe]
        rm = re.search(r'\(property "Reference" "([^"]+)"', fb)
        ref = rm.group(1) if rm else '?'
        fat = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\)', fb)
        if not fat:
            continue
        fx, fy = num(fat.group(1)), num(fat.group(2))
        frot = num(fat.group(3)) if fat.group(3) else 0.0
        for (ps, pe) in blocks(fb, 'pad'):
            pb = fb[ps:pe]
            hd = re.match(r'\(pad\s+"([^"]*)"\s+(\S+)\s+(\S+)', pb)
            pa = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\)', pb)
            sz = re.search(r'\(size\s+([\d.]+)\s+([\d.]+)\)', pb)
            nt = re.search(r'\(net\s+(?:\d+\s+)?"([^"]*)"\)', pb)
            ly = re.findall(r'"((?:F|B|In\d+)\.Cu)"', pb)
            starl = '*.Cu' in pb
            if not (hd and pa and sz and nt):
                continue
            net = nt.group(1)
            if net not in items:
                continue
            # rotate pad offset by footprint rotation
            px, py = num(pa.group(1)), num(pa.group(2))
            a = math.radians(-frot)
            gx = fx + px * math.cos(a) - py * math.sin(a)
            gy = fy + px * math.sin(a) + py * math.cos(a)
            p = dict(x=gx, y=gy, w=num(sz.group(1)), h=num(sz.group(2)),
                     shape=hd.group(3))
            sp = spine(p)
            if sp is None:                      # true rectangle
                sp = ((gx, gy), (gx, gy), max(p['w'], p['h']) / 2.0)
                shp = hd.group(3) + '(circumscribed)'
            else:
                shp = hd.group(3)
            layers = list(CU) if (starl or not ly) else sorted(
                set(ly), key=lambda L: CU.index(L) if L in CU else 99)
            tag = 'pad %s-%s %s %.3fx%.3f' % (ref, hd.group(1), shp,
                                              p['w'], p['h'])
            for L in layers:
                if L in CU:
                    items[net][L].append((sp, tag))

    # ---- zones on tap nets (flag only) ----
    for (s, e) in blocks(src, 'zone'):
        b = src[s:e]
        nt = re.search(r'\(net_name\s+"([^"]*)"\)', b)
        if nt and nt.group(1) in items:
            zones.append(nt.group(1))

    return items, zones, arcs


def measure(items, na, nb):
    out = {}
    for L in CU:
        A, B = items[na][L], items[nb][L]
        best = (9e9, None, None)
        for (ca, ta) in A:
            for (cb, tb) in B:
                d = cap_dist(ca, cb)
                if d < best[0]:
                    best = (d, ta, tb)
        out[L] = dict(gap_mm=None if best[1] is None else round(best[0], 4),
                      a_item=best[1], b_item=best[2],
                      n_a=len(A), n_b=len(B))
    return out


ap = argparse.ArgumentParser()
ap.add_argument('--pcb', default=DEF_PCB)
ap.add_argument('--json', default=None)
ap.add_argument('--dump', action='store_true', help='list every item on A1/A2')
args = ap.parse_args()

src = io.open(args.pcb, encoding='utf-8').read()

items, zones, arcs = collect(src)

report = {'pcb': args.pcb, 'pairs': {}, 'zones_on_tap_nets': sorted(set(zones)),
          'arcs_on_tap_nets': arcs}
print('PCB: %s' % args.pcb)
if zones:
    print('WARNING zones exist on tap nets: %s' % sorted(set(zones)))
if arcs:
    print('NOTE arc tracks on tap nets (capsule model is chord-approx): %s' % arcs)

RULE = {'F.Cu': 0.60, 'B.Cu': 0.60, 'In1.Cu': 0.20, 'In2.Cu': 0.20}
for (na, nb) in PAIRS:
    res = measure(items, na, nb)
    key = '%s <-> %s' % (na, nb)
    report['pairs'][key] = res
    print('\n=== %s ===' % key)
    for L in CU:
        r = res[L]
        if r['gap_mm'] is None:
            print('  %-7s no overlap on this layer (nA=%d nB=%d)'
                  % (L, r['n_a'], r['n_b']))
            continue
        verdict = 'PASS' if r['gap_mm'] >= RULE[L] else 'FAIL'
        print('  %-7s %8.4f mm  (rule %.2f) %s' % (L, r['gap_mm'], RULE[L], verdict))
        print('           A: %s' % r['a_item'])
        print('           B: %s' % r['b_item'])

if args.dump:
    print('\n--- FULL ITEM DUMP, A-side ---')
    for n in ('/poe/POE_TAP_A1', '/poe/POE_TAP_A2'):
        print('\n%s' % n)
        for L in CU:
            for (c, t) in items[n][L]:
                print('  %-7s %-58s  (%.3f,%.3f)-(%.3f,%.3f) r=%.3f'
                      % (L, t, c[0][0], c[0][1], c[1][0], c[1][1], c[2]))

if args.json:
    io.open(args.json, 'w', encoding='utf-8').write(
        json.dumps(report, indent=2))
    print('\nwrote %s' % args.json)
