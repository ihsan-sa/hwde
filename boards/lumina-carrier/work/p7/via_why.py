"""via_why.py - why a candidate via centre is illegal, obstacle by obstacle.

via_spot.py answers yes/no over a window; when it answers "0 legal centres" that
is not actionable. This prints, for one point, the plane-fill containment result
and every obstacle that violates its clearance, with the measured distance and
the required one - so the blocker can be moved, ripped or routed around instead
of guessed at.

usage: python via_why.py <net> <x> <y> [--dia 0.5] [--plane In1.Cu]
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import geom  # noqa: E402
from shapely.geometry import Point  # noqa: E402

HV = {"+48V_SW", "V48_RAW", "V48_RTN"}
TAPS = {"/poe/POE_TAP_A1", "/poe/POE_TAP_A2",
        "/poe/POE_TAP_B1", "/poe/POE_TAP_B2"}
MDI = {"/ETH_TXP", "/ETH_TXN", "/ETH_RXP", "/ETH_RXN"}

ap = argparse.ArgumentParser()
ap.add_argument("net")
ap.add_argument("x", type=float)
ap.add_argument("y", type=float)
ap.add_argument("--dia", type=float, default=0.5)
ap.add_argument("--plane", default="In1.Cu")
ap.add_argument("--pcb", default=str(
    REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_pcb"))
ap.add_argument("--ignore", default="",
                help="comma-separated nets to treat as absent (what-if for a "
                     "planned rip); pads are NEVER ignored")
a = ap.parse_args()
IGN = {s for s in a.ignore.split(",") if s}

bg = geom.BoardGeom.from_file(a.pcb)
r = a.dia / 2.0
pt = Point(a.x, a.y)


def clr_for(other_net):
    c = 0.635 if (a.net in HV or (other_net or "") in HV) else 0.2
    if (a.net in TAPS and (other_net or "") in MDI) or \
       (a.net in MDI and (other_net or "") in TAPS):
        c = max(c, 1.30)
    return c


for ly in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu"):
    f = bg.zone_fill(a.net, ly)
    if f.is_empty:
        print("fill %-7s : none" % ly)
    else:
        print("fill %-7s : contains via pad = %s (dist to fill %.4f)"
              % (ly, f.contains(pt.buffer(r)), f.distance(pt)))

print("\nblockers for a %.2f mm via of %s at (%.4f, %.4f):"
      % (a.dia, a.net, a.x, a.y))
bad = 0
for p in bg.pads_of():
    if (p.net or "") == a.net:
        continue
    need = r + clr_for(p.net)
    d = p.poly.distance(pt)
    if d < need:
        bad += 1
        print("  PAD %-5s %-4s net %-14s d=%.4f need %.4f  short %.4f"
              % (p.ref, p.number, p.net, d, need, need - d))
for t in bg.tracks_of():
    if t.net == a.net or t.net in IGN:
        continue
    need = r + clr_for(t.net)
    d = t.poly.distance(pt)
    if d < need:
        bad += 1
        print("  %-6s net %-14s (%.4f,%.4f)->(%.4f,%.4f) w%.3f d=%.4f "
              "need %.4f  short %.4f"
              % (t.layer, t.net, t.shape.coords[0][0], t.shape.coords[0][1],
                 t.shape.coords[-1][0], t.shape.coords[-1][1], t.width,
                 d, need, need - d))
for v in bg.vias_of():
    if v.net == a.net or v.net in IGN:
        continue
    need = r + clr_for(v.net)
    d = v.poly.distance(pt)
    if d < need:
        bad += 1
        print("  VIA    net %-14s @(%.4f,%.4f) d=%.4f need %.4f  short %.4f"
              % (v.net, v.at[0], v.at[1], d, need, need - d))
if not bad:
    print("  none - point is clear")
