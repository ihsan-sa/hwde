"""Enlarge the ESP32-S3-WROOM-1 thermal-land vias to meet fab minimums.

The pulled footprint carries 12 vias-in-pad at 0.400 mm pad / 0.250 mm drill =
0.075 mm annular ring. That violates both board-setup constraints at once:
  - min annular width 0.100 mm  (actual 0.075) x12 errors
  - min hole size     0.300 mm  (actual 0.250) x12 errors

I had deferred these to the P9 DFM gate at P3, reasoning that DFM should
adjudicate against real fab rules. That was wrong in one respect: they fail the
P5 board-setup self-check, which is upstream of DFM, so they block here.

Fix: drill 0.250 -> 0.300 (JLC PTH minimum) and pad 0.400 -> 0.600, giving a
0.150 mm ring - at JLC's stated minimum and above the 0.100 mm board rule.
Via-in-pad solder-wicking remains a real assembly consideration and stays on
the P9 DFM list, but the geometry is now legal.

Idempotent.
"""
import io
import re
import sys

P = (r'C:\dev\ai-ee3\boards\lumina-carrier\lib\aiee.pretty'
     r'\WIFIM-SMD_ESP32-S3-WROOM-1-N8.kicad_mod')

s = io.open(P, encoding='utf-8').read()
if '(drill 0.3)' in s or '(drill 0.300)' in s:
    print('already applied - no change')
    sys.exit(0)

PAD_RE = re.compile(r'(\(pad\s+("[^"]*"|\S+)\s+(\S+)\s+(\S+))(.*?)(?=\(pad |\Z)', re.S)
n = 0


def edit(m):
    global n
    head, body = m.group(1), m.group(5)
    dr = re.search(r'\(drill ([\d.]+)\)', body)
    sz = re.search(r'\(size ([\d.]+) ([\d.]+)\)', body)
    if dr and sz and abs(float(dr.group(1)) - 0.25) < 1e-6 and abs(float(sz.group(1)) - 0.40) < 1e-6:
        body = re.sub(r'\(size [\d.]+ [\d.]+\)', '(size 0.6 0.6)', body, count=1)
        body = re.sub(r'\(drill [\d.]+\)', '(drill 0.3)', body, count=1)
        n += 1
    return head + body


new = PAD_RE.sub(edit, s)
io.open(P, 'w', encoding='utf-8').write(new)
print('enlarged %d thermal-land vias: pad 0.400 -> 0.600, drill 0.250 -> 0.300' % n)
print('resulting annular ring: 0.150 mm/side (JLC minimum; board rule is 0.100)')
