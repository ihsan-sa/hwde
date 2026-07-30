"""via_spot.py - find DRC-legal locations for a plane via of a given net.

Scans a window on a grid and keeps points where a via of the given diameter
holds the required clearance from ALL foreign copper (pads, tracks on any layer,
other vias) and lands INSIDE that net's inner-plane fill, so the via actually
completes the connection. Also honours the 0.635 mm HV rule and the 1.30 mm
magjack barrier rule, since those are the two custom DRU rules on this board.

usage: python via_spot.py <net> x0 y0 x1 y1 [--dia 0.6] [--plane In2.Cu]
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import geom  # noqa: E402
from shapely.geometry import Point  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

HV = {"+48V_SW", "V48_RAW", "V48_RTN"}
TAPS = {"/poe/POE_TAP_A1", "/poe/POE_TAP_A2",
        "/poe/POE_TAP_B1", "/poe/POE_TAP_B2"}
MDI = {"/ETH_TXP", "/ETH_TXN", "/ETH_RXP", "/ETH_RXN"}

ap = argparse.ArgumentParser()
ap.add_argument("net")
ap.add_argument("x0", type=float)
ap.add_argument("y0", type=float)
ap.add_argument("x1", type=float)
ap.add_argument("y1", type=float)
ap.add_argument("--dia", type=float, default=0.6)
ap.add_argument("--plane", default="In2.Cu")
ap.add_argument("--step", type=float, default=0.05)
ap.add_argument("--ignore", default="", help="nets to treat as absent (what-if for a planned rip); pads never ignored")
ap.add_argument("--pcb", default=str(
    REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_pcb"))
a = ap.parse_args()
IGN = {s for s in a.ignore.split(",") if s}

bg = geom.BoardGeom.from_file(a.pcb)
fill = bg.zone_fill(a.net, a.plane)
if fill.is_empty:
    print("no %s fill on %s" % (a.net, a.plane))
    sys.exit(2)

obs = []          # (geom, required clearance)
for t in bg.tracks_of():
    if t.net == a.net or t.net in IGN:
        continue
    clr = 0.635 if (a.net in HV or t.net in HV) else 0.2
    if (a.net in TAPS and t.net in MDI) or (a.net in MDI and t.net in TAPS):
        clr = max(clr, 1.30)
    obs.append((t.poly, clr))
for v in bg.vias_of():
    if v.net == a.net or v.net in IGN:
        continue
    clr = 0.635 if (a.net in HV or v.net in HV) else 0.2
    if (a.net in TAPS and v.net in MDI) or (a.net in MDI and v.net in TAPS):
        clr = max(clr, 1.30)
    obs.append((v.poly, clr))
for p in bg.pads_of():
    if p.net == a.net:
        continue
    clr = 0.635 if (a.net in HV or (p.net or "") in HV) else 0.2
    if (a.net in TAPS and (p.net or "") in MDI) or \
       (a.net in MDI and (p.net or "") in TAPS):
        clr = max(clr, 1.30)
    obs.append((p.poly, clr))

geoms = [g for g, _ in obs]
clrs = [c for _, c in obs]
tree = STRtree(geoms)
r = a.dia / 2.0
found = []
n = 0
y = a.y0
while y <= a.y1 + 1e-9:
    x = a.x0
    while x <= a.x1 + 1e-9:
        n += 1
        pt = Point(x, y)
        if fill.contains(pt.buffer(r)):
            ok = True
            for i in tree.query(pt.buffer(r + 0.8)):
                if geoms[i].distance(pt) < r + clrs[i]:
                    ok = False
                    break
            if ok:
                found.append((x, y))
        x += a.step
    y += a.step
print("scanned %d points, %d legal via centres for %s (dia %.2f) on %s"
      % (n, len(found), a.net, a.dia, a.plane))
found=[p for p in found if p[0]-p[1] <= 16.5007]
print("of which reachable from U10 pad 9 side of the /ETH_RSTn diagonal (x-y<=16.5007): %d" % len(found))
for p in found[:400]:
    print("   (%.3f, %.3f)" % p)
