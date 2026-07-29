"""Maximise the J1 cable-side / PHY-side barrier, in both the library and the board.

MEASURED state: pad 2 (/ETH_TXN, 1.524 mm) <-> pad 11 (/poe/POE_TAP_A1, 1.200 mm)
gives a true rectangle gap of 1.148 mm.

My P4 figure of 1.451 mm was WRONG: it used
    hypot(dx_centre, dy_centre) - (w1 + w2)/2
which only holds for a single-axis offset. This pair is diagonal (dx 1.270,
dy 2.510), so that formula overestimated by 0.303 mm.

Shrinking pad 2 from 1.524 -> 1.200 mm (0.150 mm ring on its 0.900 drill, exactly
JLC's PTH minimum) takes the gap to ~1.312 mm.

1.40 mm is UNREACHABLE on this part: pads 2 and 11 are one half-pitch apart in x
and one pitch in y on a 2.54 mm grid, so even with BOTH pads at the annular
minimum the best possible is 2.510 - 1.200 = 1.310 mm in y. HALO's 55 mil figure
is guidance for HALO's parts; this vendor's own recommended land does not achieve
it at any pad size. Residual mitigations: the part's 2250 VDC hipot barrier and
the TPD4E1U06 TVS array on the MDI.

Idempotent.
"""
import io
import math
import re

BS = '\\'
LIB = (r'C:\dev\ai-ee3\boards\lumina-carrier\lib\aiee.pretty'
       r'\RJ45-TH_LPJG0926HENL_C22457393.kicad_mod')
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


def shrink_pad2(text, lo, hi, label):
    """Set pad "2" size to 1.200 within text[lo:hi]."""
    n = 0
    out, prev = [], lo
    for (ps, pe) in blocks(text, 'pad', lo, hi):
        pb = text[ps:pe]
        if not re.match(r'\(pad\s+"2"', pb):
            continue
        new = re.sub(r'\(size\s+[\d.]+\s+[\d.]+\)', '(size 1.2 1.2)', pb, count=1)
        if new != pb:
            out.append(text[prev:ps])
            out.append(new)
            prev = pe
            n += 1
    out.append(text[prev:hi])
    print('  %-10s pad "2" resized: %d' % (label, n))
    return text[:lo] + ''.join(out) + text[hi:], n


# --- library ---------------------------------------------------------------
s = io.open(LIB, encoding='utf-8').read()
if '(size 1.2 1.2)' in s and re.search(r'\(pad\s+"2"[^)]*?\(size 1\.2 1\.2\)', s, re.S):
    print('  library    already applied')
else:
    s, _ = shrink_pad2(s, 0, len(s), 'library')
    io.open(LIB, 'w', encoding='utf-8').write(s)

# --- board -----------------------------------------------------------------
b = io.open(PCB, encoding='utf-8').read()
done = 0
for (fs, fe) in blocks(b, 'footprint'):
    blk = b[fs:fe]
    rm = re.search(r'\(property "Reference" "([^"]+)"', blk)
    if not rm or rm.group(1) != 'J1':
        continue
    b, done = shrink_pad2(b, fs, fe, 'board')
    break
if done:
    io.open(PCB, 'w', encoding='utf-8').write(b)

# --- re-measure ------------------------------------------------------------
b = io.open(PCB, encoding='utf-8').read()
for (fs, fe) in blocks(b, 'footprint'):
    blk = b[fs:fe]
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
    phy = [n for n, p in pads.items() if 'ETH_T' in p[4] or 'ETH_R' in p[4]]
    line = [n for n, p in pads.items() if 'POE_TAP' in p[4]]
    best = (1e9, None)
    for c in phy:
        for l in line:
            x1, y1, w1, h1, _ = pads[c]
            x2, y2, w2, h2, _ = pads[l]
            dx = max(0.0, abs(x1 - x2) - (w1 + w2) / 2)
            dy = max(0.0, abs(y1 - y2) - (h1 + h2) / 2)
            g = math.hypot(dx, dy)
            if g < best[0]:
                best = (g, (c, pads[c][4], l, pads[l][4]))
    c, cn, l, ln = best[1]
    print()
    print('MEASURED cable-side <-> PHY-side gap: %.3f mm' % best[0])
    print('   pad %s (%s) <-> pad %s (%s)' % (c, cn, l, ln))
    print('   HALO guidance 1.40 mm -> %s' % ('PASS' if best[0] >= 1.40 else 'SHORT by %.3f mm'
                                              % (1.40 - best[0])))
    print('   theoretical max on this 2.54 mm grid: 1.310 mm (both pads at annular minimum)')
    break
