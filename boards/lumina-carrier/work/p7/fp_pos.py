"""Print footprint positions for named refs. Read-only."""
import io
import re
import sys

BS = '\\'
PCB = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb'
WANT = sys.argv[1:] or ['C34', 'R7', 'R30', 'U10', 'Y10']


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
found = {}
for (fs, fe) in blocks(src, 'footprint'):
    blk = src[fs:fe]
    rm = re.search(r'\(property "Reference" "([^"]+)"', blk)
    if not rm:
        continue
    ref = rm.group(1)
    if ref not in WANT:
        continue
    at = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\s*\)', blk)
    fpn = re.match(r'\(footprint\s+"([^"]+)"', blk)
    # bbox from pads
    xs, ys = [], []
    for (ps, pe) in blocks(blk, 'pad'):
        pb = blk[ps:pe]
        pa = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)', pb)
        sz = re.search(r'\(size\s+([\d.]+)\s+([\d.]+)', pb)
        if pa and sz:
            xs += [float(pa.group(1)) - float(sz.group(1)) / 2,
                   float(pa.group(1)) + float(sz.group(1)) / 2]
            ys += [float(pa.group(2)) - float(sz.group(2)) / 2,
                   float(pa.group(2)) + float(sz.group(2)) / 2]
    found[ref] = (at.group(1), at.group(2), at.group(3) or '0',
                  fpn.group(1) if fpn else '?',
                  (min(xs), min(ys), max(xs), max(ys)) if xs else None)

for ref in WANT:
    if ref in found:
        x, y, r, fp, bb = found[ref]
        print('%-5s at (%9s, %9s) rot=%-6s  %s' % (ref, x, y, r, fp[:46]))
        if bb:
            print('        local pad bbox %.3f,%.3f -> %.3f,%.3f  (abs %.3f,%.3f -> %.3f,%.3f)'
                  % (bb[0], bb[1], bb[2], bb[3],
                     float(x) + bb[0], float(y) + bb[1], float(x) + bb[2], float(y) + bb[3]))
    else:
        print('%-5s NOT FOUND' % ref)
