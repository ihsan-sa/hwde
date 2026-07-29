"""Fix the board-lock <-> VC creepage defect on the LPJG0926HENL land.

Found by the magjack-swap agent: pads 19/20 (EH, the shell board-locks and the
only shell-to-board copper path - the dia-3.20 mounting holes are NPTH) sit
2.287 / 2.297 mm centre-to-centre from VC1/VC4, giving only 0.487 / 0.497 mm of
copper against the board's 0.635 mm HV rule.

Unlike the chip-side/line-side isolation barrier, this one IS voltage-derived,
so check_creepage WOULD have caught it at P8 - after routing. Fixing it now.

Geometry is tight in both directions at once:
  gap = c_c - (w_EH + w_VC)/2,  and JLC's minimum annular ring is 0.15 mm/side.
  EH drill 1.70 -> min width 2.00;  VC drill 0.90 -> min width 1.20.
  Best simultaneous result: 2.287 - (2.00 + 1.20)/2 = 0.687 mm.

EH is made OVAL (2.00 wide x 2.60 tall) rather than a 2.00 circle: the EH->VC
vector is almost entirely in X, so narrowing X buys the clearance while the
extra Y keeps copper under a board-lock that takes insertion force. VC1/VC4 go
to 1.20 mm circular (0.15 mm/side, 0.6 A - ample).

Idempotent.
"""
import io
import math
import re
import sys

P = (r'C:\dev\ai-ee3\boards\lumina-carrier\lib\aiee.pretty'
     r'\RJ45-TH_LPJG0926HENL_C22457393.kicad_mod')

s = io.open(P, encoding='utf-8').read()
if '(size 2.000 2.600)' in s or '(size 2 2.6)' in s:
    print('already applied - no change')
    sys.exit(0)

PAD_RE = re.compile(r'(\(pad\s+("[^"]*"|\S+)\s+(\S+)\s+(\S+))(.*?)(?=\(pad |\Z)', re.S)


def edit(m):
    head, num, ptype, shape, body = m.group(1), m.group(2).strip('"'), m.group(3), m.group(4), m.group(5)
    if num in ('19', '20'):
        body = re.sub(r'\(size [\d.]+ [\d.]+\)', '(size 2.000 2.600)', body, count=1)
        head = head.rsplit(shape, 1)[0] + 'oval'
    elif num in ('11', '14'):
        body = re.sub(r'\(size [\d.]+ [\d.]+\)', '(size 1.200 1.200)', body, count=1)
    return head + body


new = PAD_RE.sub(edit, s)
io.open(P, 'w', encoding='utf-8').write(new)

# --- verify by re-measuring -------------------------------------------------
pads = {}
for m in PAD_RE.finditer(new):
    num = m.group(2).strip('"')
    body = m.group(5)
    at = re.search(r'\(at ([-\d.]+) ([-\d.]+)', body)
    sz = re.search(r'\(size ([\d.]+) ([\d.]+)', body)
    dr = re.search(r'\(drill ([\d.]+)', body)
    if at and sz:
        pads[num] = (float(at.group(1)), float(at.group(2)),
                     float(sz.group(1)), float(sz.group(2)),
                     float(dr.group(1)) if dr else None)

print('%-6s %-9s %-9s %-9s' % ('pair', 'c-c', 'gap', 'verdict'))
ok = True
for a, b in (('19', '11'), ('20', '14')):
    xa, ya, wa, ha, da = pads[a]
    xb, yb, wb, hb, db = pads[b]
    cc = math.hypot(xa - xb, ya - yb)
    gap = cc - (wa + wb) / 2
    good = gap >= 0.635
    ok &= good
    print('%s-%s  %-9.3f %-9.3f %s' % (a, b, cc, gap, 'PASS' if good else '*** FAIL ***'))

print()
for n in ('19', '20', '11', '14'):
    x, y, w, h, d = pads[n]
    print('pad %-3s size %.3f x %.3f drill %.3f -> annular %.3f/side %s'
          % (n, w, h, d, (w - d) / 2, 'OK' if (w - d) / 2 >= 0.1499 else 'THIN'))

sys.exit(0 if ok else 1)
