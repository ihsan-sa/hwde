"""Find a legal y for C34 that opens the U10 MDI channel without hitting U30.

Constraints:
  1. channel = C34_top - U10_bottom  must be >= 2.1 mm (two coupled 100 ohm
     pairs abreast need ~1.8 mm plus clearance)
  2. C34 courtyard must not overlap U30's (the ESP32 module)
  3. C34 must stay near U10 pin 4 for check_decoupling
"""
import io
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


src = io.open(PCB, encoding='utf-8').read()
info = {}
for (fs, fe) in blocks(src, 'footprint'):
    blk = src[fs:fe]
    rm = re.search(r'\(property "Reference" "([^"]+)"', blk)
    if not rm or rm.group(1) not in ('C34', 'U10', 'U30', 'R130', 'C41', 'C35'):
        continue
    ref = rm.group(1)
    at = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?', blk)
    ox, oy = float(at.group(1)), float(at.group(2))
    rot = float(at.group(3) or 0)
    xs, ys = [], []
    # courtyard lines take priority; fall back to pads
    for tok in ('fp_line', 'fp_poly', 'fp_rect'):
        for (gs, ge) in blocks(blk, tok):
            gb = blk[gs:ge]
            if 'CrtYd' not in gb:
                continue
            for m in re.finditer(r'\((?:start|end|xy)\s+(-?[\d.]+)\s+(-?[\d.]+)\)', gb):
                xs.append(float(m.group(1)))
                ys.append(float(m.group(2)))
    kind = 'courtyard'
    if not xs:
        kind = 'pads'
        for (ps, pe) in blocks(blk, 'pad'):
            pb = blk[ps:pe]
            pa = re.search(r'\(at\s+(-?[\d.]+)\s+(-?[\d.]+)', pb)
            sz = re.search(r'\(size\s+([\d.]+)\s+([\d.]+)', pb)
            if pa and sz:
                xs += [float(pa.group(1)) - float(sz.group(1)) / 2,
                       float(pa.group(1)) + float(sz.group(1)) / 2]
                ys += [float(pa.group(2)) - float(sz.group(2)) / 2,
                       float(pa.group(2)) + float(sz.group(2)) / 2]
    # rotate local extents about origin
    import math
    th = math.radians(-rot)
    pts = [(x * math.cos(th) - y * math.sin(th), x * math.sin(th) + y * math.cos(th))
           for x in (min(xs), max(xs)) for y in (min(ys), max(ys))]
    ax = [ox + p[0] for p in pts]
    ay = [oy + p[1] for p in pts]
    info[ref] = dict(o=(ox, oy), rot=rot, kind=kind,
                     bb=(min(ax), min(ay), max(ax), max(ay)))

for ref in ('U10', 'C34', 'U30', 'C35', 'C41', 'R130'):
    if ref in info:
        i = info[ref]
        print('%-6s origin (%8.3f,%8.3f) rot %-7.1f %-9s abs bbox %8.3f,%8.3f -> %8.3f,%8.3f'
              % (ref, i['o'][0], i['o'][1], i['rot'], i['kind'],
                 i['bb'][0], i['bb'][1], i['bb'][2], i['bb'][3]))

u10 = info['U10']['bb']
u30 = info['U30']['bb']
c34 = info['C34']
h = c34['bb'][3] - c34['bb'][1]
w = c34['bb'][2] - c34['bb'][0]
print()
print('U10 bottom edge : %.3f' % u10[3])
print('U30 bbox        : %.3f,%.3f -> %.3f,%.3f' % u30)
print('C34 size        : %.3f x %.3f' % (w, h))
print()
print('%-8s %-10s %-12s %-10s' % ('C34 y', 'top edge', 'channel', 'U30 overlap?'))
for dy in (0.0, 0.5, 0.8, 1.0, 1.2, 1.5):
    y = 85.4461 + dy
    top = y - h / 2
    bot = y + h / 2
    left = c34['o'][0] - w / 2
    right = c34['o'][0] + w / 2
    ch = top - u10[3]
    ov = not (right < u30[0] or left > u30[2] or bot < u30[1] or top > u30[3])
    print('%-8.3f %-10.3f %-12.3f %-10s %s'
          % (y, top, ch, 'YES' if ov else 'no',
             'OK' if (ch >= 2.1 and not ov) else ''))
