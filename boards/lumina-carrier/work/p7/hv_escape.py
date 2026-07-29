"""hv_escape.py - which 48 V pads can a 0.635 mm-clearance track actually reach?

`HV_48V_clearance` in lumina-carrier.kicad_dru demands 0.635 mm between any
48 V item and anything else, excluding only PAD-to-PAD pairs. A track landing
on an HV pad inherits that pad's own neighbourhood, so any HV pad whose
nearest FOREIGN copper is closer than 0.635 mm cannot be connected without
firing the rule - the pad pitch, not the routing, decides it.

Prints every HV pad with its nearest foreign-copper gap, flagging the
un-escapable ones. Run from the repo root.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import geom  # noqa: E402

HV = {"V48_RAW", "V48_RTN", "+48V_SW"}
LIMIT = 0.635

pcb = sys.argv[1] if len(sys.argv) > 1 else str(
    REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_pcb")
bg = geom.BoardGeom.from_file(pcb)
pads = list(bg.pads_of())

bad = 0
for p in pads:
    if p.net not in HV:
        continue
    best, who = 1e9, None
    for q in pads:
        if q is p or q.net == p.net:
            continue
        if not (set(p.layers) & set(q.layers)):
            continue
        d = p.poly.distance(q.poly)
        if d < best:
            best, who = d, "%s.%s[%s]" % (q.ref, q.number, q.net or "no-net")
    flag = "  <-- UNESCAPABLE" if best < LIMIT else ""
    if best < LIMIT:
        bad += 1
    print("%-4s pad %-3s %-9s nearest foreign %6.3f mm  %s%s"
          % (p.ref, p.number, p.net, best, who, flag))
print("\n%d of the HV pads sit closer than %.3f mm to foreign copper" %
      (bad, LIMIT))
