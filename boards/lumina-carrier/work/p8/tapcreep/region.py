"""Dump every copper item (ANY net) inside a window, per layer, with capsules.

Lets me see what free space actually exists before moving a via, so the move
does not trade a POE_TAP creepage error for a clearance error against some
other net. Reuses capsule.py (= work/p7/pad_gap.py model).

Usage: region.py --x0 46 --x1 52 --y0 70 --y1 78 [--layer B.Cu]
       region.py --probe 49.65,74.85,0.3 --layers all   # clearance of a trial via
"""
import argparse
import io
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capsule import blocks, spine, cap_dist   # noqa: E402

PCB = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb'
CU = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
NETRE = r'\(net\s+(?:\d+\s+)?"([^"]*)"\)'


def expand(l1, l2):
    if l1 == '*.Cu' or l2 == '*.Cu':
        return list(CU)
    try:
        i, j = CU.index(l1), CU.index(l2)
    except ValueError:
        return [x for x in (l1, l2) if x in CU]
    return CU[min(i, j):max(i, j) + 1]


def collect_all(src):
    """[(layer, net, capsule, tag)] for every copper item on the board."""
    out = []
    for tok in ('segment', 'arc'):
        for (s, e) in blocks(src, tok):
            b = src[s:e]
            nm = re.search(NETRE, b)
            ln = re.search(r'\(layer\s+"([^"]+)"', b)
            wd = re.search(r'\(width\s+([\d.]+)\)', b)
            st = re.search(r'\(start\s+(-?[\d.]+)\s+(-?[\d.]+)\)', b)
            en = re.search(r'\(end\s+(-?[\d.]+)\s+(-?[\d.]+)\)', b)
            uu = re.search(r'\(uuid\s+"?([0-9a-fA-F-]+)"?\)', b)
            if not (ln and wd and st and en) or ln.group(1) not in CU:
                continue
            cap = ((float(st.group(1)), float(st.group(2))),
                   (float(en.group(1)), float(en.group(2))),
                   float(wd.group(1)) / 2.0)
            out.append((ln.group(1), nm.group(1) if nm else '',
                        cap, '%s w=%.3f %s' % (tok, float(wd.group(1)),
                                               uu.group(1)[:8] if uu else '?')))
    for (s, e) in blocks(src, 'via'):
        b = src[s:e]
        nm = re.search(NETRE, b)
        at = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)\)', b)
        sz = re.search(r'\(size\s+([\d.]+)\)', b)
        dr = re.search(r'\(drill\s+([\d.]+)\)', b)
        ly = re.search(r'\(layers\s+"([^"]+)"\s+"([^"]+)"\)', b)
        uu = re.search(r'\(uuid\s+"?([0-9a-fA-F-]+)"?\)', b)
        if not (at and sz and ly):
            continue
        x, y, d = float(at.group(1)), float(at.group(2)), float(sz.group(1))
        cap = ((x, y), (x, y), d / 2.0)
        for L in expand(ly.group(1), ly.group(2)):
            out.append((L, nm.group(1) if nm else '', cap,
                        'via d=%.3f dr=%s %s' % (d, dr.group(1) if dr else '?',
                                                 uu.group(1)[:8] if uu else '?')))
    for (fs, fe) in blocks(src, 'footprint'):
        fb = src[fs:fe]
        rm = re.search(r'\(property "Reference" "([^"]+)"', fb)
        ref = rm.group(1) if rm else '?'
        fat = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\)', fb)
        if not fat:
            continue
        fx, fy = float(fat.group(1)), float(fat.group(2))
        frot = float(fat.group(3)) if fat.group(3) else 0.0
        for (ps, pe) in blocks(fb, 'pad'):
            pb = fb[ps:pe]
            hd = re.match(r'\(pad\s+"([^"]*)"\s+(\S+)\s+(\S+)', pb)
            pa = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\)', pb)
            sz = re.search(r'\(size\s+([\d.]+)\s+([\d.]+)\)', pb)
            nt = re.search(NETRE, pb)
            ly = re.findall(r'"((?:F|B|In\d+)\.Cu)"', pb)
            if not (hd and pa and sz):
                continue
            px, py = float(pa.group(1)), float(pa.group(2))
            a = math.radians(-frot)
            gx = fx + px * math.cos(a) - py * math.sin(a)
            gy = fy + px * math.sin(a) + py * math.cos(a)
            p = dict(x=gx, y=gy, w=float(sz.group(1)), h=float(sz.group(2)),
                     shape=hd.group(3))
            sp = spine(p)
            shp = hd.group(3)
            if sp is None:
                sp = ((gx, gy), (gx, gy), max(p['w'], p['h']) / 2.0)
                shp += '(circ)'
            layers = list(CU) if ('*.Cu' in pb or not ly) else [x for x in ly if x in CU]
            for L in layers:
                out.append((L, nt.group(1) if nt else '', sp,
                            'pad %s-%s %s %.2fx%.2f' % (ref, hd.group(1), shp,
                                                        p['w'], p['h'])))
    return out


ap = argparse.ArgumentParser()
ap.add_argument('--pcb', default=PCB)
ap.add_argument('--x0', type=float, default=46.0)
ap.add_argument('--x1', type=float, default=52.0)
ap.add_argument('--y0', type=float, default=70.0)
ap.add_argument('--y1', type=float, default=78.0)
ap.add_argument('--layer', default=None)
ap.add_argument('--probe', default=None,
                help='x,y,radius - report nearest copper of every OTHER net')
ap.add_argument('--probe-net', default='/poe/POE_TAP_A1',
                help='net the probe item belongs to (same-net copper ignored)')
ap.add_argument('--ignore-uuid', default='',
                help='comma list of uuid prefixes to treat as already deleted')
ap.add_argument('--near', type=float, default=1.2,
                help='probe: report everything closer than this gap')
args = ap.parse_args()

src = io.open(args.pcb, encoding='utf-8').read()
items = collect_all(src)
ign = [u for u in args.ignore_uuid.split(',') if u]


def kept(tag):
    return not any(u in tag for u in ign)


if args.probe:
    px, py, pr = [float(v) for v in args.probe.split(',')]
    probe = ((px, py), (px, py), pr)
    print('probe (%.3f,%.3f) r=%.3f  net=%s   [ignoring: %s]'
          % (px, py, pr, args.probe_net, ign or 'nothing'))
    for L in CU:
        rows = []
        for (lay, net, cap, tag) in items:
            if lay != L or net == args.probe_net or not kept(tag):
                continue
            g = cap_dist(probe, cap)
            if g < args.near:
                rows.append((g, net, tag))
        rows.sort()
        print('  %-7s worst %s' % (L, ('%.4f  %s  %s' % rows[0][:1] + ''
                                       if False else
                                       ('%.4f  %-24s %s' % (rows[0][0], rows[0][1], rows[0][2])
                                        if rows else '(nothing within %.2f)' % args.near)))) # noqa
        for (g, net, tag) in rows[1:8]:
            print('              %.4f  %-24s %s' % (g, net, tag))
    sys.exit(0)

for L in CU:
    if args.layer and L != args.layer:
        continue
    print('=== %s ===' % L)
    n = 0
    for (lay, net, cap, tag) in items:
        if lay != L:
            continue
        (a, b, r) = cap
        if max(a[0], b[0]) + r < args.x0 or min(a[0], b[0]) - r > args.x1:
            continue
        if max(a[1], b[1]) + r < args.y0 or min(a[1], b[1]) - r > args.y1:
            continue
        print('  %-26s %-30s (%.3f,%.3f)-(%.3f,%.3f) r=%.3f'
              % (net, tag, a[0], a[1], b[0], b[1], r))
        n += 1
    print('  [%d items]' % n)
