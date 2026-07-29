"""Fix two library defects blocking the P5 board-setup self-check.

1. U30 ESP32-S3-WROOM-1 thermal-land vias-in-pad.
   As pulled: 12 vias at 0.400 mm pad / 0.250 mm drill = 0.075 mm ring, which
   fails BOTH the min-annular (0.100) and min-hole (0.300) board rules.
   Enlarging them to 0.600/0.300 fixed those two but created 24 clearance and
   24 solder-mask-bridge errors instead - the via pads then touch the thermal
   sub-pads (clearance actual 0.000 mm).

   Correct fix: REMOVE the vias from the footprint. Thermal vias under a
   ground/thermal land belong to the board, not the footprint - P7 stitching
   places them against the real GND pour, with correct net assignment and fab-
   legal geometry. This also removes the via-in-pad solder-wicking risk that
   was already on the P9 DFM list.

2. D1 SMBJ58A courtyard is "malformed (self-intersecting)" - it contains
   zero-length segments (start == end), an easyeda2kicad artifact. Scans every
   footprint for the same defect and drops the degenerate lines.

Idempotent.
"""
import glob
import io
import os
import re

PRETTY = r'C:\dev\ai-ee3\boards\lumina-carrier\lib\aiee.pretty'

# --- 1. strip the ESP32 thermal-land vias -----------------------------------
esp = os.path.join(PRETTY, 'WIFIM-SMD_ESP32-S3-WROOM-1-N8.kicad_mod')
s = io.open(esp, encoding='utf-8').read()
PAD_RE = re.compile(r'\(pad\s+("[^"]*"|\S+)\s+(\S+)\s+(\S+)(.*?)(?=\n\t\(pad |\n\t\(fp_|\n\t\(model|\Z)', re.S)

removed = 0
out, pos = [], 0
for m in PAD_RE.finditer(s):
    body = m.group(4)
    dr = re.search(r'\(drill ([\d.]+)\)', body)
    sz = re.search(r'\(size ([\d.]+) ([\d.]+)\)', body)
    is_via = bool(dr and sz
                  and float(sz.group(1)) <= 0.65
                  and float(dr.group(1)) <= 0.35)
    if is_via:
        out.append(s[pos:m.start()])
        pos = m.end()
        removed += 1
out.append(s[pos:])
if removed:
    io.open(esp, 'w', encoding='utf-8').write(''.join(out))
    print('U30: removed %d thermal-land vias-in-pad (P7 stitching will place '
          'real GND vias)' % removed)
else:
    print('U30: no vias matched (already removed?)')

# --- 2. drop zero-length courtyard/graphic segments, board-wide -------------
ZERO = re.compile(r'[ \t]*\(fp_line \(start ([-\d.]+) ([-\d.]+)\) '
                  r'\(end ([-\d.]+) ([-\d.]+)\)[^\n]*\)\n')
total = 0
for fp in sorted(glob.glob(os.path.join(PRETTY, '*.kicad_mod'))):
    t = io.open(fp, encoding='utf-8').read()

    def drop(m):
        global total
        if (m.group(1), m.group(2)) == (m.group(3), m.group(4)):
            total += 1
            return ''
        return m.group(0)

    n = ZERO.sub(drop, t)
    if n != t:
        io.open(fp, 'w', encoding='utf-8').write(n)
        print('  %-52s cleaned' % os.path.basename(fp))
print('zero-length fp_line segments removed board-wide: %d' % total)
