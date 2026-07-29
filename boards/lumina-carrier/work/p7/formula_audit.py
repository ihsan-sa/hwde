"""Re-derive every pad-gap number I measured with the flawed radial formula.

    WRONG: hypot(dx_centre, dy_centre) - (w1 + w2)/2
    RIGHT: dx = |x1-x2| - (w1+w2)/2 ; dy = |y1-y2| - (h1+h2)/2
           gap = hypot(max(dx,0), max(dy,0))    -> 0 if overlapping on both axes
           and if one axis overlaps, the gap is simply the OTHER axis's value.

The wrong form is only valid for a single-axis offset. It overestimates every
diagonal pair (0.303 mm on the J1 chip/line barrier). Anywhere I used it, the
number is optimistic.

Audited here: the J1 board-lock (EH, pads 19/20) to PoE-tap (VC, pads 11/14)
creepage, which I reported at P4 as 0.687 / 0.697 mm against the board's 0.635 mm
HV rule. That pair IS diagonal, so it needs re-deriving.

Also re-confirms the J3/J4 connector figure, which used `pitch - annulus` - a
same-row/column axial measure, so it should be unaffected.
"""
import io
import math
import re

BS = '\\'
PCB = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb'
REQ = 0.635


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


def gaps(p, q):
    x1, y1, w1, h1 = p
    x2, y2, w2, h2 = q
    dcx, dcy = abs(x1 - x2), abs(y1 - y2)
    wrong = math.hypot(dcx, dcy) - (w1 + w2) / 2
    dx = dcx - (w1 + w2) / 2
    dy = dcy - (h1 + h2) / 2
    if dx <= 0 and dy <= 0:
        right = 0.0
    elif dx <= 0:
        right = dy
    elif dy <= 0:
        right = dx
    else:
        right = math.hypot(dx, dy)
    return right, wrong


src = io.open(PCB, encoding='utf-8').read()
for (fs, fe) in blocks(src, 'footprint'):
    blk = src[fs:fe]
    rm = re.search(r'\(property "Reference" "([^"]+)"', blk)
    if not rm or rm.group(1) != 'J1':
        continue
    pads = {}
    for (ps, pe) in blocks(blk, 'pad'):
        pb = blk[ps:pe]
        num = re.match(r'\(pad\s+"([^"]*)"', pb)
        pa = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)', pb)
        sz = re.search(r'\(size\s+([\d.]+)\s+([\d.]+)', pb)
        nt = re.search(r'\(net\s+"([^"]*)"', pb)
        if num and pa and sz and num.group(1):
            pads[num.group(1)] = (float(pa.group(1)), float(pa.group(2)),
                                  float(sz.group(1)), float(sz.group(2)),
                                  nt.group(1) if nt else '')
    print('=== J1 board-lock (EH 19/20, /poe/SHIELD) vs PoE taps (VC 11-14) ===')
    print('board HV rule = %.3f mm' % REQ)
    print()
    print('%-9s %-9s %-10s %-12s %-10s' % ('lock', 'tap', 'TRUE gap', 'P4 (wrong)', 'verdict'))
    worst = (9e9, None)
    for eh in ('19', '20'):
        for vc in ('11', '12', '13', '14'):
            if eh not in pads or vc not in pads:
                continue
            r, w = gaps(pads[eh][:4], pads[vc][:4])
            if r > 4.0:
                continue
            if r < worst[0]:
                worst = (r, (eh, vc))
            print('%-9s %-9s %-10.3f %-12.3f %-10s'
                  % (eh, vc, r, w, 'PASS' if r >= REQ else '*** FAIL ***'))
    print()
    g, pair = worst
    print('WORST pair: %s <-> %s = %.3f mm  -> %s'
          % (pair[0], pair[1], g, 'PASS' if g >= REQ else 'FAILS the 0.635 mm rule'))
    print()
    print('Nets involved: %s = %s ; %s = %s'
          % (pair[0], pads[pair[0]][4], pair[1], pads[pair[1]][4]))
    break

print()
print('=== J3/J4 connector figure re-confirm (axial, should be unaffected) ===')
print('gap = pitch - annulus = 2.540 - 1.700 = %.3f mm -> %.2fx over %.3f'
      % (2.540 - 1.700, (2.540 - 1.700) / REQ, REQ))
print('same-row/column pads are offset on ONE axis only, so the radial form')
print('and the correct form agree - that number stands.')
