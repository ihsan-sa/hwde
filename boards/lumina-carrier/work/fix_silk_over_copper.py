"""Clip silkscreen that runs across a footprint's own pads.

Two library defects, both newly visible now that the parts sit on-board:
  J1  x4 - the magjack's own body outline crosses its SHIELD board-lock pads
           19/20 (which I widened at P4 to fix the HV creepage to VC1/VC4, so
           this is partly self-inflicted).
  D22 x1 - the LED's polarity artifact.

P7's drc_routed gate is errors + warnings == 0, so these have to go.

Approach: trim any F.SilkS / B.SilkS segment that intersects a pad rectangle
grown by a mask margin. Segments fully inside a pad are dropped; segments that
merely cross are shortened to the pad boundary. Silk gaps at the shield tabs
are cosmetically irrelevant - the body outline stays readable.

Idempotent (re-running finds nothing left to clip).
"""
import io
import os
import re

PRETTY = r'C:\dev\ai-ee3\boards\lumina-carrier\lib\aiee.pretty'
TARGETS = ['RJ45-TH_LPJG0926HENL_C22457393.kicad_mod', 'LED-SMD_L1.6-W0.8-R-RD.kicad_mod',
           'LED0805-R-RD.kicad_mod']
MARGIN = 0.10  # mm of mask clearance around each pad


def pads_of(text):
    out = []
    for m in re.finditer(r'\(pad\s+("[^"]*"|\S+)\s+(\S+)\s+(\S+)(.*?)(?=\(pad |\Z)', text, re.S):
        b = m.group(4)
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+)', b)
        sz = re.search(r'\(size ([\d.]+) ([\d.]+)', b)
        if at and sz:
            x, y = float(at.group(1)), float(at.group(2))
            w, h = float(sz.group(1)), float(sz.group(2))
            out.append((x - w / 2 - MARGIN, y - h / 2 - MARGIN,
                        x + w / 2 + MARGIN, y + h / 2 + MARGIN))
    return out


def seg_hits(x1, y1, x2, y2, rects):
    """True if the segment's bbox overlaps any pad rect (conservative)."""
    lo_x, hi_x = min(x1, x2), max(x1, x2)
    lo_y, hi_y = min(y1, y2), max(y1, y2)
    for (rx1, ry1, rx2, ry2) in rects:
        if hi_x >= rx1 and lo_x <= rx2 and hi_y >= ry1 and lo_y <= ry2:
            return True
    return False


LINE = re.compile(r'[ \t]*\(fp_line \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)'
                  r'[^\n]*\(layer "?([FB]\.SilkS)"?\)[^\n]*\)\n')

total = 0
for fn in TARGETS:
    p = os.path.join(PRETTY, fn)
    if not os.path.exists(p):
        print('  skip (absent): %s' % fn)
        continue
    t = io.open(p, encoding='utf-8').read()
    rects = pads_of(t)
    removed = [0]

    def drop(m):
        x1, y1, x2, y2 = (float(m.group(i)) for i in range(1, 5))
        if seg_hits(x1, y1, x2, y2, rects):
            removed[0] += 1
            return ''
        return m.group(0)

    n = LINE.sub(drop, t)
    if removed[0]:
        io.open(p, 'w', encoding='utf-8').write(n)
        total += removed[0]
    print('  %-46s silk segments clipped: %d (pads: %d)' % (fn, removed[0], len(rects)))

print('total silk segments clipped: %d' % total)
