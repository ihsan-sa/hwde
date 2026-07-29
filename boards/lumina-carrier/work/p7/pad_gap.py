"""ONE correct pad-to-pad gap measurement, shape-aware. Settles the record.

I have now produced three different numbers for the J1 barrier and two for the
shield-to-tap gap, because I twice used a formula that did not match the pad
SHAPE:

  circle  : gap = hypot(dx,dy) - (r1 + r2)                  <- "radial" form
  oval    : stadium; distance between the two spine segments minus radii
  rect    : per-axis, gap = hypot(max(dx,0), max(dy,0))

The radial form is EXACT for circle-circle and WRONG for rect-rect (it
overestimates diagonals). The rect form is EXACT for rect-rect and WRONG for
circle-circle (it underestimates diagonals). I applied each to the wrong shape
in turn.

KiCad pad shapes here: J1 signal/tap pads are `circle`; the board-lock pads
19/20 I edited to `oval`.

Prints the shape it used for every pair, so the number is auditable.
"""
import io
import math
import re

BS = '\\'
PCB = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb'


def blocks(t, tok, st=0, en=None):
    en = len(t) if en is None else en
    i, pat = st, '(' + tok
    while True:
        i = t.find(pat, i, en)
        if i < 0:
            return
        j, d, q = i, 0, False
        while j < en:
            c = t[j]
            if c == '"' and t[j - 1] != BS:
                q = not q
            elif not q:
                if c == '(':
                    d += 1
                elif c == ')':
                    d -= 1
                    if d == 0:
                        yield (i, j + 1)
                        break
            j += 1
        i = j + 1


def spine(p):
    """Return (a, b, r) - a capsule: segment a-b with radius r.
    circle -> degenerate segment. oval -> segment along the long axis.
    rect/roundrect -> approximated by its inscribed capsule ONLY if square."""
    x, y, w, h, shape = p['x'], p['y'], p['w'], p['h'], p['shape']
    if shape == 'circle' or abs(w - h) < 1e-9:
        return (x, y), (x, y), w / 2.0
    if shape in ('oval', 'roundrect'):
        if w >= h:                      # long axis horizontal
            r = h / 2.0
            half = (w - h) / 2.0
            return (x - half, y), (x + half, y), r
        r = w / 2.0
        half = (h - w) / 2.0
        return (x, y - half), (x, y + half), r
    return None                          # rectangle: handled separately


def seg_seg_dist(a1, a2, b1, b2):
    def clamp(v, lo, hi):
        return max(lo, min(hi, v))

    def pt_seg(p, s1, s2):
        vx, vy = s2[0] - s1[0], s2[1] - s1[1]
        L2 = vx * vx + vy * vy
        if L2 == 0:
            return math.hypot(p[0] - s1[0], p[1] - s1[1])
        t = clamp(((p[0] - s1[0]) * vx + (p[1] - s1[1]) * vy) / L2, 0.0, 1.0)
        return math.hypot(p[0] - (s1[0] + t * vx), p[1] - (s1[1] + t * vy))
    return min(pt_seg(a1, b1, b2), pt_seg(a2, b1, b2),
               pt_seg(b1, a1, a2), pt_seg(b2, a1, a2))


def gap(p, q):
    sp, sq = spine(p), spine(q)
    if sp and sq:
        (a1, a2, r1), (b1, b2, r2) = sp, sq
        return seg_seg_dist(a1, a2, b1, b2) - r1 - r2, 'capsule'
    dx = max(0.0, abs(p['x'] - q['x']) - (p['w'] + q['w']) / 2)
    dy = max(0.0, abs(p['y'] - q['y']) - (p['h'] + q['h']) / 2)
    return math.hypot(dx, dy), 'rect'


src = io.open(PCB, encoding='utf-8').read()
for (fs, fe) in blocks(src, 'footprint'):
    blk = src[fs:fe]
    rm = re.search(r'\(property "Reference" "([^"]+)"', blk)
    if not rm or rm.group(1) != 'J1':
        continue
    at = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)', blk)
    pads = {}
    for (ps, pe) in blocks(blk, 'pad'):
        pb = blk[ps:pe]
        hd = re.match(r'\(pad\s+"([^"]*)"\s+(\S+)\s+(\S+)', pb)
        pa = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)', pb)
        sz = re.search(r'\(size\s+([\d.]+)\s+([\d.]+)', pb)
        nt = re.search(r'\(net\s+"([^"]*)"', pb)
        if hd and pa and sz and hd.group(1):
            pads[hd.group(1)] = dict(x=float(pa.group(1)), y=float(pa.group(2)),
                                     w=float(sz.group(1)), h=float(sz.group(2)),
                                     shape=hd.group(3), net=nt.group(1) if nt else '')
    print('J1 pad shapes: ' + ', '.join('%s=%s %.3fx%.3f' % (k, v['shape'], v['w'], v['h'])
                                        for k, v in sorted(pads.items(), key=lambda kv: (len(kv[0]), kv[0]))
                                        if k in ('1', '2', '11', '14', '19', '20')))
    print()

    print('--- BARRIER: MDI (PHY side) vs PoE taps (cable side), rule 1.30 / HALO 1.40 ---')
    worst = (9e9, None, None)
    for m in ('1', '2', '3', '6'):
        for t in ('11', '12', '13', '14'):
            if m in pads and t in pads:
                g, how = gap(pads[m], pads[t])
                if g < worst[0]:
                    worst = (g, (m, t), how)
    g, (m, t), how = worst
    print('worst pair: pad %s (%s) <-> pad %s (%s)  =  %.4f mm   [%s model]'
          % (m, pads[m]['net'], t, pads[t]['net'], g, how))
    print('   vs 1.30 mm rule : %s' % ('PASS' if g >= 1.30 else 'FAIL'))
    print('   vs 1.40 mm HALO : %s' % ('PASS' if g >= 1.40 else 'FAIL'))
    print('   what it would be with pad 2 restored to 1.524 mm:')
    save = pads['2']['w'], pads['2']['h']
    pads['2']['w'] = pads['2']['h'] = 1.524
    g2, _ = gap(pads['2'], pads['11'])
    pads['2']['w'], pads['2']['h'] = save
    print('      pad 2 <-> pad 11 = %.4f mm  -> HALO %s' % (g2, 'PASS' if g2 >= 1.40 else 'FAIL'))
    print()

    print('--- SHIELD board-locks (19/20, oval) vs PoE taps (11-14, circle), rule 0.635 ---')
    w2 = (9e9, None, None)
    for e in ('19', '20'):
        for t in ('11', '12', '13', '14'):
            if e in pads and t in pads:
                g, how = gap(pads[e], pads[t])
                if g < w2[0]:
                    w2 = (g, (e, t), how)
                if g < 4.0:
                    print('   %s <-> %s = %.4f mm  [%s]' % (e, t, g, how))
    g, (e, t), how = w2
    print('worst: pad %s (%s) <-> pad %s (%s) = %.4f mm  -> %s the 0.635 mm rule'
          % (e, pads[e]['net'], t, pads[t]['net'], g, 'PASSES' if g >= 0.635 else 'FAILS'))
    break
