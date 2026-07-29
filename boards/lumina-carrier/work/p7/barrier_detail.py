"""Cross-check the J1 barrier with BOTH formulas, to settle which is right.

At P4 I reported 1.451 mm using
    hypot(dx_centre, dy_centre) - (w1 + w2)/2
which is only correct when the two pads are separated along ONE axis. For a
DIAGONAL offset it overestimates, because it subtracts the half-widths along the
radial direction rather than per-axis.

The correct rectangle-to-rectangle gap is
    dx = |x1-x2| - (w1+w2)/2 ; dy = |y1-y2| - (h1+h2)/2
    gap = hypot(max(dx,0), max(dy,0))   (0 if they overlap on both axes)
"""
import io
import math
import re

PCB = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb'
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
    pads = {}
    for (ps, pe) in blocks(blk, 'pad'):
        pb = blk[ps:pe]
        num = re.match(r'\(pad\s+"([^"]*)"', pb)
        pa = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)', pb)
        sz = re.search(r'\(size\s+([\d.]+)\s+([\d.]+)', pb)
        if num and pa and sz and num.group(1):
            pads[num.group(1)] = (float(pa.group(1)), float(pa.group(2)),
                                  float(sz.group(1)), float(sz.group(2)))

    chip = [n for n in pads if n in list('12345678') or n in ('9', '10')]
    line = [n for n in pads if n in ('11', '12', '13', '14')]

    rows = []
    for c in chip:
        for l in line:
            x1, y1, w1, h1 = pads[c]
            x2, y2, w2, h2 = pads[l]
            dcx, dcy = abs(x1 - x2), abs(y1 - y2)
            radial = math.hypot(dcx, dcy) - (w1 + w2) / 2          # P4 formula
            dx = dcx - (w1 + w2) / 2
            dy = dcy - (h1 + h2) / 2
            true = math.hypot(max(dx, 0.0), max(dy, 0.0))          # correct
            rows.append((true, radial, c, l, dcx, dcy, w1, w2))
    rows.sort()
    print('J1 chip-side(1-10) vs line-side(11-14) pad gaps, closest 6:')
    print('%-6s %-6s %-9s %-9s %-8s %-8s' % ('chip', 'line', 'TRUE', 'P4-formula', 'dx_c', 'dy_c'))
    for (true, radial, c, l, dcx, dcy, w1, w2) in rows[:6]:
        print('%-6s %-6s %-9.3f %-9.3f  %-8.3f %-8.3f' % (c, l, true, radial, dcx, dcy))
    print()
    t, r, c, l = rows[0][0], rows[0][1], rows[0][2], rows[0][3]
    print('CLOSEST PAIR: pad %s <-> pad %s' % (c, l))
    print('   TRUE rectangle gap      : %.3f mm   %s 1.40 mm guidance'
          % (t, 'PASS' if t >= 1.40 else 'BELOW'))
    print('   P4 radial approximation : %.3f mm   (overestimates by %.3f mm)' % (r, r - t))
    break
