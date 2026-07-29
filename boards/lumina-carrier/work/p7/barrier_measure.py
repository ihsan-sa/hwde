"""Measure the J1 magjack isolation barrier geometrically.

check_creepage derives spacing purely from working voltage (0.635 mm at 57 V),
so it structurally CANNOT see this barrier - the requirement is HALO's 55 mil
(1.40 mm) land-pattern guidance for cable-side vs PHY-side copper, which exists
for surge withstand across the transformer, not for a DC potential difference.
This board is non-isolated (48 V and logic share a ground), so it is explicitly
surge geometry rather than galvanic isolation.

Reports a MEASURED number, not an assertion.
"""
import io
import math
import re
import sys

PCB = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb'
GUIDANCE = 1.40
BS = '\\'


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


src = io.open(PCB, encoding='utf-8').read()

for (a, b) in blocks(src, 'footprint'):
    blk = src[a:b]
    rm = re.search(r'\(property "Reference" "([^"]+)"', blk)
    if not rm or rm.group(1) != 'J1':
        continue

    pads = []
    for (ps, pe) in blocks(blk, 'pad'):
        pb = blk[ps:pe]
        num = re.match(r'\(pad\s+"([^"]*)"', pb)
        pa = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)', pb)
        sz = re.search(r'\(size\s+([\d.]+)\s+([\d.]+)', pb)
        nt = re.search(r'\(net\s+"([^"]*)"', pb)
        if pa and sz:
            pads.append({
                'n': num.group(1) if num else '?',
                'x': float(pa.group(1)), 'y': float(pa.group(2)),
                'w': float(sz.group(1)), 'h': float(sz.group(2)),
                'net': nt.group(1) if nt else '<none>'})

    print('J1 = LPJG0926HENL, %d pads' % len(pads))
    print()
    print('pads carrying a net:')
    for p in pads:
        if p['net'] != '<none>':
            print('   pad %-4s (%8.3f, %8.3f)  size %.3f x %.3f  net %s'
                  % (p['n'], p['x'], p['y'], p['w'], p['h'], p['net']))

    cable = [p for p in pads if '48' in p['net']]
    phy = [p for p in pads if 'ETH_T' in p['net'] or 'ETH_R' in p['net']]
    print()
    print('CABLE-side (48 V domain, from VC taps via the bridges): %s'
          % ([p['n'] for p in cable] or 'none carrying a net'))
    print('PHY-side  (MDI to the W5500)                          : %s'
          % ([p['n'] for p in phy] or 'none carrying a net'))

    def gap(p, q):
        dx = max(0.0, abs(p['x'] - q['x']) - (p['w'] + q['w']) / 2)
        dy = max(0.0, abs(p['y'] - q['y']) - (p['h'] + q['h']) / 2)
        return math.hypot(dx, dy) if (dx or dy) else -1.0

    best = (1e9, None)
    for c in cable:
        for m in phy:
            g = gap(c, m)
            if g < best[0]:
                best = (g, (c, m))
    print()
    if best[1]:
        c, m = best[1]
        print('MEASURED minimum CABLE-side to PHY-side pad gap: %.3f mm' % best[0])
        print('   pad %s (%s)  <->  pad %s (%s)' % (c['n'], c['net'], m['n'], m['net']))
        print('   vs HALO 1.40 mm guidance -> %s'
              % ('PASS' if best[0] >= GUIDANCE else '*** BELOW GUIDANCE ***'))
        sys.exit(0 if best[0] >= GUIDANCE else 1)
    else:
        # Fall back to raw land geometry: the two physical pad ROWS, regardless
        # of which nets happen to be assigned.
        chip = [p for p in pads if p['n'] in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10')]
        line = [p for p in pads if p['n'] in ('11', '12', '13', '14')]
        best2 = (1e9, None)
        for cc in chip:
            for ll in line:
                g = gap(cc, ll)
                if g < best2[0]:
                    best2 = (g, (cc, ll))
        cc, ll = best2[1]
        print('No net-carrying pad pair spans the barrier; measuring the LAND rows instead.')
        print('MEASURED minimum chip-side(1-10) to line-side(11-14) pad gap: %.3f mm' % best2[0])
        print('   pad %s (%s)  <->  pad %s (%s)' % (cc['n'], cc['net'], ll['n'], ll['net']))
        print('   vs HALO 1.40 mm guidance -> %s'
              % ('PASS' if best2[0] >= GUIDANCE else '*** BELOW GUIDANCE ***'))
        sys.exit(0 if best2[0] >= GUIDANCE else 1)
    break
