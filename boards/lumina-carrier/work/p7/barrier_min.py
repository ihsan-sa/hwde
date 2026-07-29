"""barrier_min.py - measure the WORST-CASE cable-side/PHY-side gap on the board.

The DRU rule only reports pass/fail at 1.30 mm. This prints the actual minimum,
with the two items that set it, so the barrier can be reported as a number.

Rule semantics reproduced exactly: A in {POE_TAP_A1,A2,B1,B2}, B in
{ETH_TXP,TXN,RXP,RXN}, pad-pair combinations excluded, clearance is
shape-to-shape with track/via/pad copper inflated to its real outline. Items on
different single layers cannot violate; vias and THT pads span every layer.

usage: python barrier_min.py [board.kicad_pcb]
"""
import math
import re
import sys
from pathlib import Path

from shapely.geometry import LineString, Point

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
BOARD = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_pcb")
TAPS = {"/poe/POE_TAP_A1", "/poe/POE_TAP_A2",
        "/poe/POE_TAP_B1", "/poe/POE_TAP_B2"}
MDI = {"/ETH_TXP", "/ETH_TXN", "/ETH_RXP", "/ETH_RXN"}
ALL = frozenset(["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"])
BS = "\\"


def blocks(t, tok, st=0, en=None):
    en = len(t) if en is None else en
    i, pat = st, "(" + tok
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
                if c == "(":
                    d += 1
                elif c == ")":
                    d -= 1
                    if d == 0:
                        yield (i, j + 1)
                        break
            j += 1
        i = j + 1


txt = BOARD.read_text(encoding="utf-8")
items = []          # (net, kind, layers, shapely geom)

# tracks / arcs
for tag in ("segment", "arc"):
    for (a, b) in blocks(txt, tag):
        blk = txt[a:b]
        nm = re.search(r'\(net "([^"]*)"\)', blk)
        if not nm or nm.group(1) not in TAPS | MDI:
            continue
        st = re.search(r"\(start\s+(-?[\d.]+)\s+(-?[\d.]+)", blk)
        en = re.search(r"\(end\s+(-?[\d.]+)\s+(-?[\d.]+)", blk)
        w = re.search(r"\(width\s+([\d.]+)", blk)
        ly = re.search(r'\(layer "([^"]+)"', blk)
        g = LineString([(float(st.group(1)), float(st.group(2))),
                        (float(en.group(1)), float(en.group(2)))])
        items.append((nm.group(1), "track", frozenset([ly.group(1)]),
                      g.buffer(float(w.group(1)) / 2, cap_style=2)))

# vias
for (a, b) in blocks(txt, "via"):
    blk = txt[a:b]
    nm = re.search(r'\(net "([^"]*)"\)', blk)
    at = re.search(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)", blk)
    sz = re.search(r"\(size\s+([\d.]+)", blk)
    if not (nm and at and sz) or nm.group(1) not in TAPS | MDI:
        continue
    items.append((nm.group(1), "via", ALL,
                  Point(float(at.group(1)), float(at.group(2)))
                  .buffer(float(sz.group(1)) / 2)))

# pads - via geom.BoardGeom, which resolves footprint rotation, pad shape
# (this board's J1 pads are CIRCLES, so a bounding box would overstate them by
# up to 0.22 mm) and the layer set. A hand-rolled parse got this wrong twice.
import geom  # noqa: E402
bg = geom.BoardGeom.from_file(str(BOARD))
for p in bg.pads_of():
    if p.net not in TAPS | MDI:
        continue
    lay = ALL if ("*.Cu" in p.layers or len(p.layers) > 2) else frozenset(p.layers)
    items.append((p.net, "pad %s.%s" % (p.ref, p.number), lay, p.poly))

best = (1e9, None, None)
tap = [i for i in items if i[0] in TAPS]
phy = [i for i in items if i[0] in MDI]
print("tap-side copper items: %d   MDI-side copper items: %d"
      % (len(tap), len(phy)))
for t in tap:
    for p in phy:
        if t[1].startswith("pad") and p[1].startswith("pad"):
            continue                       # rule excludes pad-pair combos
        if not (t[2] & p[2]):
            continue                       # no shared layer
        d = t[3].distance(p[3])
        if d < best[0]:
            best = (d, t, p)

d, t, p = best
print()
print("WORST-CASE tap <-> MDI gap on routed copper: %.4f mm" % d)
print("   A: %-22s %-14s layers %s" % (t[0], t[1], sorted(t[2])))
print("   B: %-22s %-14s layers %s" % (p[0], p[1], sorted(p[2])))
print("   requirement (magjack_isolation_barrier): 1.3000 mm -> %s"
      % ("PASS" if d >= 1.3 else "FAIL short by %.4f mm" % (1.3 - d)))

# also the pad-pair figure, which the rule excludes but the land defines
padbest = (1e9, None, None)
for t in tap:
    for p in phy:
        if not (t[1].startswith("pad") and p[1].startswith("pad")):
            continue
        if not (t[2] & p[2]):
            continue
        dd = t[3].distance(p[3])
        if dd < padbest[0]:
            padbest = (dd, t, p)
if padbest[1]:
    print()
    print("(land geometry, excluded from the rule) closest tap pad <-> MDI pad:"
          " %.4f mm  %s <-> %s"
          % (padbest[0], padbest[1][1], padbest[2][1]))
sys.exit(0 if d >= 1.3 else 1)
