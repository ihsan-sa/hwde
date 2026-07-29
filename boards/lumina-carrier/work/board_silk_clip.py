"""Clip silkscreen over pads inside the placed board's footprint instances.

board_init embeds footprint geometry into the .kicad_pcb, so the lib/ fixes do
not propagate. Re-running board_init would propagate them but would discard the
P6 placement, which is the expensive artifact.

KiCad 10 writes multi-line pretty-printed s-expressions, so primitives are
extracted with a balanced-paren scan rather than a line regex.

Within each footprint's LOCAL frame (pads and silk share the footprint's `at`
transform, so it cancels), any F/B.SilkS primitive whose bbox overlaps one of
that footprint's own pads - grown by a mask margin - is dropped.

Prints counts only; the board file never enters the caller's context.
Idempotent.
"""
import io
import re
import sys

PCB = r'C:\dev\ai-ee3\boards\lumina-carrier\kicad\lumina-carrier.kicad_pcb'
MARGIN = 0.10
ONLY = {'J1', 'D22'}   # only the refs DRC actually flagged - a blanket sweep
                       # strips legitimate silk from every passive, whose body
                       # outline naturally overlaps its own pad bboxes
NUM = re.compile(r'-?\d+\.?\d*')


def blocks(text, token, start=0, end=None):
    """Yield (start, end) of every balanced (token ...) form."""
    end = len(text) if end is None else end
    i = start
    pat = '(' + token
    while True:
        i = text.find(pat, i, end)
        if i < 0:
            return
        j, depth, instr = i, 0, False
        while j < end:
            c = text[j]
            if c == '"' and text[j - 1] != '\\':
                instr = not instr
            elif not instr:
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        yield (i, j + 1)
                        break
            j += 1
        i = j + 1


def xy_pairs(body, tags=('start', 'end', 'center', 'mid', 'xy', 'at')):
    pts = []
    for t in tags:
        for m in re.finditer(r'\(' + t + r'\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)', body):
            pts.append((float(m.group(1)), float(m.group(2))))
    return pts


src = io.open(PCB, encoding='utf-8').read()
fps = list(blocks(src, 'footprint'))
if not fps:
    print('ABORT - no footprint blocks parsed')
    sys.exit(1)

cuts = []          # (start, end) spans to delete, absolute offsets
per_fp = {}

for (fs, fe) in fps:
    blk = src[fs:fe]
    rm = re.search(r'\(property "Reference" "([^"]+)"', blk)
    ref = rm.group(1) if rm else '?'

    rects = []
    for (ps, pe) in blocks(blk, 'pad'):
        pb = blk[ps:pe]
        at = re.search(r'\(at\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)', pb)
        sz = re.search(r'\(size\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)', pb)
        if at and sz:
            x, y = float(at.group(1)), float(at.group(2))
            w, h = float(sz.group(1)), float(sz.group(2))
            rects.append((x - w / 2 - MARGIN, y - h / 2 - MARGIN,
                          x + w / 2 + MARGIN, y + h / 2 + MARGIN))
    if not rects or ref not in ONLY:
        continue

    n = 0
    for tok in ('fp_line', 'fp_circle', 'fp_arc', 'fp_poly'):
        for (gs, ge) in blocks(blk, tok):
            gb = blk[gs:ge]
            if 'SilkS' not in gb:
                continue
            pts = xy_pairs(gb)
            if not pts:
                continue
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            lo_x, hi_x, lo_y, hi_y = min(xs), max(xs), min(ys), max(ys)
            if any(hi_x >= r[0] and lo_x <= r[2] and hi_y >= r[1] and lo_y <= r[3]
                   for r in rects):
                cuts.append((fs + gs, fs + ge))
                n += 1
    if n:
        per_fp[ref] = n

cuts.sort()
out, prev = [], 0
for (a, b) in cuts:
    out.append(src[prev:a])
    prev = b
out.append(src[prev:])
io.open(PCB, 'w', encoding='utf-8').write(''.join(out))

print('footprint instances scanned : %d' % len(fps))
print('silk primitives clipped     : %d' % len(cuts))
for ref, n in sorted(per_fp.items()):
    print('   %-6s x%d' % (ref, n))
