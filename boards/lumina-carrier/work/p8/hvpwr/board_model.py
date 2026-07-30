"""Shared board geometry model for the hvpwr work order.

Reuses the capsule model (work/p8/tapcreep/capsule.py = work/p7/pad_gap.py
functions verbatim) so gap numbers match the record that settled the J1
barrier. Adds:
  * zone FILLED polygon collection (region.py ignores zones)
  * a per-pair required-clearance table derived from the .kicad_dru + the
    IPC-2221B 0.60 mm creepage number the work order targets
  * path_eval(): min gap from a candidate polyline to every other net
"""
import io
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tapcreep'))
from capsule import blocks, spine, cap_dist            # noqa: E402

PCB = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb'
CU = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
NETRE = r'\(net\s+(?:\d+\s+)?"([^"]*)"\)'

TAPS = ['/poe/POE_TAP_A1', '/poe/POE_TAP_A2',
        '/poe/POE_TAP_B1', '/poe/POE_TAP_B2']
HV48 = ['+48V_SW', 'V48_RAW', 'V48_RTN']
MDI = ['/ETH_TXP', '/ETH_TXN', '/ETH_RXP', '/ETH_RXN']
# nets declared >30 V in constraints.json voltages
HV_ALL = set(TAPS) | set(HV48)
DEFAULT_CLR = 0.20      # board netclass minimum (DRC)


def required(net_a, net_b):
    """Clearance this pair must hold, mm. max(DRC rule, creepage)."""
    if not net_a or not net_b or net_a == net_b:
        return 0.0
    r = DEFAULT_CLR
    # HV_48V_* DRU rules (0.635 mm), courtyard exclusions ignored -> we never
    # route inside U1/U20/U22/C1/C6x courtyards in this order.
    if net_a in HV48 or net_b in HV48:
        r = max(r, 0.635)
    # magjack_isolation_barrier 1.30 mm
    if (net_a in TAPS and net_b in MDI) or (net_b in TAPS and net_a in MDI):
        r = max(r, 1.30)
    # poe_tap_differential_pair 0.60 mm
    pairs = [('/poe/POE_TAP_A1', '/poe/POE_TAP_A2'),
             ('/poe/POE_TAP_B1', '/poe/POE_TAP_B2')]
    for (p, q) in pairs:
        if {net_a, net_b} == {p, q}:
            r = max(r, 0.60)
    # IPC-2221B B2 creepage, 51-100 V band: any >30 V net against a net at a
    # different potential.  check_creepage models exactly this.
    hv_a, hv_b = net_a in HV_ALL, net_b in HV_ALL
    if hv_a != hv_b:
        r = max(r, 0.60)
    return r


PADS_POLY = []          # [(layer, net, pts, tag, '')] - true rect/roundrect pads


def collect(src, want_zones=True):
    """[(layer, net, capsule, tag, uuid)] plus zone polys [(layer,net,pts)].

    Rectangular pads go to PADS_POLY as rotated 4-point polygons instead."""
    del PADS_POLY[:]
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
            out.append((ln.group(1), nm.group(1) if nm else '', cap,
                        '%s w=%.3f' % (tok, float(wd.group(1))),
                        uu.group(1) if uu else ''))
    for (s, e) in blocks(src, 'via'):
        b = src[s:e]
        nm = re.search(NETRE, b)
        at = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)\)', b)
        sz = re.search(r'\(size\s+([\d.]+)\)', b)
        ly = re.search(r'\(layers\s+"([^"]+)"\s+"([^"]+)"\)', b)
        uu = re.search(r'\(uuid\s+"?([0-9a-fA-F-]+)"?\)', b)
        if not (at and sz and ly):
            continue
        x, y, d = float(at.group(1)), float(at.group(2)), float(sz.group(1))
        cap = ((x, y), (x, y), d / 2.0)
        l1, l2 = ly.group(1), ly.group(2)
        if l1 == '*.Cu' or l2 == '*.Cu':
            layers = list(CU)
        else:
            try:
                i, j = CU.index(l1), CU.index(l2)
                layers = CU[min(i, j):max(i, j) + 1]
            except ValueError:
                layers = [x for x in (l1, l2) if x in CU]
        for L in layers:
            out.append((L, nm.group(1) if nm else '', cap,
                        'via d=%.3f' % d, uu.group(1) if uu else ''))
    for (fs, fe) in blocks(src, 'footprint'):
        fb = src[fs:fe]
        rm = re.search(r'\(property "Reference" "([^"]+)"', fb)
        ref = rm.group(1) if rm else '?'
        fat = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\)',
                        fb)
        if not fat:
            continue
        fx, fy = float(fat.group(1)), float(fat.group(2))
        frot = float(fat.group(3)) if fat.group(3) else 0.0
        for (ps, pe) in blocks(fb, 'pad'):
            pb = fb[ps:pe]
            hd = re.match(r'\(pad\s+"([^"]*)"\s+(\S+)\s+(\S+)', pb)
            pa = re.search(
                r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\)', pb)
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
            shp = hd.group(3)
            layers = list(CU) if ('*.Cu' in pb or not ly) \
                else [q for q in ly if q in CU]
            tag = 'pad %s-%s %s %.2fx%.2f' % (ref, hd.group(1), shp,
                                              p['w'], p['h'])
            if shp in ('circle', 'oval') or abs(p['w'] - p['h']) < 1e-9:
                sp = spine(p)          # exact: circle / obround stadium
                for L in layers:
                    out.append((L, nt.group(1) if nt else '', sp, tag, ''))
                continue
            # rect / roundrect / trapezoid / custom -> TRUE rotated rectangle.
            # A circumscribed circle (the old fallback) is wildly pessimistic
            # for long thin pads: L21-2 is 1.90x2.50 and U22-21 is 3.40x6.50,
            # and both are the binding constraint on a cluster-B widen.
            prot = float(pa.group(3)) if pa.group(3) else 0.0
            th = math.radians(-(frot + prot))
            hw, hh = p['w'] / 2.0, p['h'] / 2.0
            rr = 0.0
            if shp == 'roundrect':
                rm2 = re.search(r'\(roundrect_rratio\s+([\d.]+)\)', pb)
                rr = (float(rm2.group(1)) if rm2 else 0.25) \
                    * min(p['w'], p['h'])
            local = []
            if rr > 1e-6:
                # rounded corners matter: on U22's 1.575x0.40 pins the corner
                # arc IS the nearest copper to the 48 V diagonal, and a sharp
                # rectangle overstates the pad by ~0.04 mm there.
                for (cx, cy, a0) in ((hw - rr, hh - rr, 0.0),
                                     (-(hw - rr), hh - rr, 90.0),
                                     (-(hw - rr), -(hh - rr), 180.0),
                                     (hw - rr, -(hh - rr), 270.0)):
                    for k in range(5):
                        a = math.radians(a0 + 22.5 * k)
                        local.append((cx + rr * math.cos(a),
                                      cy + rr * math.sin(a)))
            else:
                local = [(hw, hh), (-hw, hh), (-hw, -hh), (hw, -hh)]
            pts = []
            for (sx, sy) in local:
                pts.append((gx + sx * math.cos(th) - sy * math.sin(th),
                            gy + sx * math.sin(th) + sy * math.cos(th)))
            for L in layers:
                PADS_POLY.append((L, nt.group(1) if nt else '', pts, tag, ''))
    zones = []
    if want_zones:
        for (s, e) in blocks(src, 'zone'):
            b = src[s:e]
            nt = re.search(r'\(net\s+"([^"]*)"\)', b) or \
                re.search(r'\(net_name\s+"([^"]*)"\)', b)
            net = nt.group(1) if nt else ''
            for (ls, le) in blocks(b, 'filled_polygon'):
                zb = b[ls:le]
                lm = re.search(r'\(layer\s+"([^"]+)"', zb)
                if not lm or lm.group(1) not in CU:
                    continue
                pts = [(float(x), float(y)) for (x, y) in
                       re.findall(r'\(xy\s+(-?[\d.]+)\s+(-?[\d.]+)\)', zb)]
                if pts:
                    zones.append((lm.group(1), net, pts))
    return out, zones


def edge_segments(src):
    """Edge.Cuts line/arc segments as (a,b) pairs (arcs -> chord)."""
    segs = []
    for tok in ('gr_line', 'gr_arc'):
        for (s, e) in blocks(src, tok):
            b = src[s:e]
            if '"Edge.Cuts"' not in b:
                continue
            st = re.search(r'\(start\s+(-?[\d.]+)\s+(-?[\d.]+)\)', b)
            en = re.search(r'\(end\s+(-?[\d.]+)\s+(-?[\d.]+)\)', b)
            md = re.search(r'\(mid\s+(-?[\d.]+)\s+(-?[\d.]+)\)', b)
            if not (st and en):
                continue
            a = (float(st.group(1)), float(st.group(2)))
            c = (float(en.group(1)), float(en.group(2)))
            if md:
                m = (float(md.group(1)), float(md.group(2)))
                segs.append((a, m))
                segs.append((m, c))
            else:
                segs.append((a, c))
    return segs


def _orient(p, q, r):
    return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])


def seg_cross(a1, a2, b1, b2):
    """True if the two centrelines properly intersect.

    capsule.seg_seg_dist (and therefore cap_dist) is a MINIMUM-OVER-ENDPOINTS
    formula.  That is exact for disjoint segments, but for two segments that
    cross it silently returns a POSITIVE number - the nearest endpoint
    distance - so a short looks like clearance.  Two LED_Y_A/LED_G_A crossings
    passed both the solver and the pre-flight this way and were caught only by
    DRC ("Tracks crossing").  Every gap query in this work order now goes
    through gap_of() instead.
    """
    d1, d2 = _orient(b1, b2, a1), _orient(b1, b2, a2)
    d3, d4 = _orient(a1, a2, b1), _orient(a1, a2, b2)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return True
    return False


def gap_of(A, B):
    """Copper gap between two capsules, -1.0 if their centrelines cross."""
    if seg_cross(A[0], A[1], B[0], B[1]):
        return -1.0
    return cap_dist(A, B)


def poly_dist(pt_cap, pts):
    """capsule -> closed polygon boundary distance (0 if inside)."""
    (a1, a2, r) = pt_cap
    best = 9e9
    n = len(pts)
    for i in range(n):
        b1, b2 = pts[i], pts[(i + 1) % n]
        from capsule import seg_seg_dist
        best = min(best, seg_seg_dist(a1, a2, b1, b2))
    return best - r


def path_caps(way, width):
    """polyline waypoints -> list of capsules."""
    r = width / 2.0
    return [(way[i], way[i + 1], r) for i in range(len(way) - 1)]


def eval_path(items, zones, edges, way, width, net, layer='F.Cu',
              ignore=(), near=2.0):
    """Return worst gap per foreign net for a candidate polyline."""
    caps = path_caps(way, width)
    ign = set(ignore)
    per = {}
    for (lay, onet, cap, tag, uu) in items:
        if lay != layer or onet == net or uu in ign:
            continue
        g = min(cap_dist(c, cap) for c in caps)
        if g > near:
            continue
        key = onet or '(no net)'
        rec = per.get(key)
        if rec is None or g < rec[0]:
            per[key] = (g, tag, required(net, onet))
    for (lay, znet, pts) in zones:
        if lay != layer or znet == net:
            continue
        g = min(poly_dist(c, pts) for c in caps)
        if g > near:
            continue
        key = 'ZONE ' + (znet or '(no net)')
        rec = per.get(key)
        if rec is None or g < rec[0]:
            per[key] = (g, 'zone fill', required(net, znet))
    for (lay, pnet, pts, tag, _u) in PADS_POLY:
        if lay != layer or pnet == net:
            continue
        g = min(poly_dist(c, pts) for c in caps)
        if g > near:
            continue
        key = pnet or '(no net)'
        rec = per.get(key)
        if rec is None or g < rec[0]:
            per[key] = (g, tag, required(net, pnet))
    eg = 9e9
    for (a, b) in edges:
        from capsule import seg_seg_dist
        for c in caps:
            eg = min(eg, seg_seg_dist(c[0], c[1], a, b) - c[2])
    return per, eg


def load(pcb=PCB):
    src = io.open(pcb, encoding='utf-8').read()
    items, zones = collect(src)
    return src, items, zones, edge_segments(src)
