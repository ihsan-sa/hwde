"""rf-de-20m P7 - finish what Freerouting could not, and undo what it got wrong.

Freerouting (fr_signals.py) closed 15 of the 24 open connections. Three things
were left, and this pass fixes all of them with route_edit ops:

1. HV CLEARANCE. FR reads clearances from the DSN, which KiCad writes from the
   .kicad_pro NETCLASSES; the per-net `aiee_hv_*` rules live in the .kicad_dru
   and never reach it (and pushing them into the classes re-wedges the DSN
   reader - measured). So FR ran /hk/BUCK_SW 0.26 mm from +40V pads. That leg
   is deleted and re-run south of C108, well clear.

2. THE +5V_DRV DETOUR. FR could not join {FB201.2, C213.1, C201.1} to
   {C202.1, U201.A1} and threw a dead-end branch 9 mm east into the FET area
   instead (3 dangling stubs, 2 clearance errors against /SW). Deleted.

3. THE REAL BLOCKER, and it is structural: **U201's OUTL wrap seals the
   driver.** The turn-off fan-out has no planar solution, so P7 ran OUTL west
   around U201 as a 0.55 mm U - a vertical at x 28.91..29.46 spanning
   y 61.485..66.735 and two horizontals at y 61.485..62.035 and 66.185..66.735
   running east to x 33.11. That U is a WALL. U201.C1 (/stage/DRIVE) and the
   C201->C202 link of +5V_DRV both have to cross it, and on F.Cu there is no
   gap: west of the wrap is outside, east is the gate-resistor column, and the
   gate bar GATE_ON (1.3 mm wide at y 63.46..64.76) plugs the R203/R204 gap.
   Neither router failed for lack of effort - the corridor does not exist.

   Fix: two short In2 hops UNDER the wrap. In2, not In1, on purpose - In1 at
   0.2444 mm is the gate loops' and the drive input's return image and must
   stay whole; In2 is the third GND layer and a 1.3 / 3.7 mm slot in it costs
   nothing the design depends on. DRIVE keeps In1 directly above it the whole
   way, so its 50 ohm reference is unchanged.

   COST TO CARRY TO FAB: 4 through vias land inside the bottom-heatsink
   contact land (constraints keepout [11.635,49.335,42.635,109.335]). HS-2
   allows vias there but forbids UNTENTED ones - these MUST stay tented on
   B.Cu or they short to the sink. The board sets no per-via tenting, so the
   project default (tented) governs; P9 must not turn it off.

4. +5V L101.2 -> C109.1 was also blocked (BUCK_SW's own detour around L101's
   body crosses it), but that one has a via-free answer: x 32..40 / y 70..92 is
   completely empty, so +5V goes west and north into the existing y = 74.55
   trunk instead.

Usage: python finish_signals.py [--dry-run]
"""
import json
import subprocess
import sys
from pathlib import Path

S = r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts'
sys.path.insert(0, S)
sys.path.insert(0, S + '/lib')
import geom                                                        # noqa: E402

PCB = Path(r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb')
OPS = Path(r'C:/dev/ai-ee3/boards/rf-de-20m/route/ops_finish.json')
W = 0.2
VIA = {"size": 0.45, "drill": 0.2}

# ---- copper to delete, identified by net + an endpoint (uuids churn) -------
# +5V_DRV: everything east of x = 33 is the dead-end detour.
# /hk/BUCK_SW: the leg from (46.945,85.132) to C107.2 that squeezes between
# U101.1 and U101.2 (+40V, 0.5 mm rule) and past C105.1.
DROP_DRV_EAST_OF = 33.0
DROP_BUCK = [((46.945, 85.132), (48.915, 87.102)),
             ((48.915, 87.102), (48.915, 88.947)),
             ((48.915, 88.947), (50.918, 90.950)),
             ((50.918, 90.950), (51.131, 90.950)),
             ((51.131, 90.950), (51.482, 91.301)),
             ((51.482, 91.301), (51.482, 91.691)),
             ((52.086, 91.691), (51.482, 91.691))]


def polyline(net, pts, layer='F.Cu', width=W):
    return [{"op": "add_track", "start": list(a), "end": list(b),
             "width": width, "layer": layer, "net": net}
            for a, b in zip(pts, pts[1:])]


def build_adds():
    ops = []

    # --- +5V: C109.1 west + north into the existing y=74.55 trunk ----------
    ops += polyline('+5V', [(43.404, 87.487), (38.000, 87.487),
                            (38.000, 74.550), (40.000, 74.550)])

    # --- +5V_DRV: C201.1 -> C202.1, hopping under the OUTL wrap on In2 -----
    ops += polyline('+5V_DRV', [(30.315, 61.035), (29.700, 61.100)])
    ops.append({"op": "add_via", "at": [29.700, 61.100], "net": "+5V_DRV",
                **VIA})
    ops += polyline('+5V_DRV', [(29.700, 61.100), (29.900, 62.400)],
                    layer='In2.Cu')
    ops.append({"op": "add_via", "at": [29.900, 62.400], "net": "+5V_DRV",
                **VIA})
    ops += polyline('+5V_DRV', [(29.900, 62.400), (30.465, 62.335)])

    # --- /stage/DRIVE: R202.1 -> U201.C1, east of FB201 then under the wrap
    # The inside via sits at (29.85,63.20), not 63.60: a GND stitch via at
    # (30.085,64.135) puts the two drills 0.584 mm apart there, under the
    # 0.4995 mm hole-to-hole floor + 2 x 0.1 mm radii.
    ops += polyline('/stage/DRIVE',
                    [(25.745, 54.335), (25.745, 56.200), (32.500, 56.200),
                     (32.500, 59.000), (32.200, 59.000), (32.200, 60.800)])
    ops.append({"op": "add_via", "at": [32.200, 60.800],
                "net": "/stage/DRIVE", **VIA})
    ops += polyline('/stage/DRIVE', [(32.200, 60.800), (29.850, 63.200)],
                    layer='In2.Cu')
    ops.append({"op": "add_via", "at": [29.850, 63.200],
                "net": "/stage/DRIVE", **VIA})
    ops += polyline('/stage/DRIVE', [(29.850, 63.200), (30.335, 63.710)])

    # --- /hk/BST: U101.7 -> C107.1 ----------------------------------------
    # East of U101 is FULL: VCC and FB already use the only lane between
    # C106's body and U101's top row, and RON's diagonal (54.662,84.286)->
    # (52.150,86.798) closes the outside. West is U101.8's own escape. So BST
    # takes the 0.546 mm channel between the top-row pads (bottom 83.499) and
    # the exposed pad (top 84.045) east to open ground, then drops to In2 for
    # the 6.8 mm past the +40V row. Those two vias are at x = 52.9, OUTSIDE
    # the heatsink land (which ends at x = 42.635).
    ops += polyline('/hk/BST', [(49.620, 82.480), (49.620, 83.770),
                                (52.900, 83.770)])
    ops.append({"op": "add_via", "at": [52.900, 83.770], "net": "/hk/BST",
                **VIA})
    ops += polyline('/hk/BST', [(52.900, 83.770), (52.900, 90.600)],
                    layer='In2.Cu')
    ops.append({"op": "add_via", "at": [52.900, 90.600], "net": "/hk/BST",
                **VIA})
    ops += polyline('/hk/BST', [(52.900, 90.600), (50.686, 90.600),
                                (50.686, 91.691)])

    # --- /hk/BUCK_SW: U101.8 -> C107.2, south of C108 well clear of +40V ---
    # x = 53.8 on the return leg, not 52.086: at 52.086 the track swallows the
    # GND stitch via at (51.904,93.17) and steals its net.
    ops += polyline('/hk/BUCK_SW',
                    [(45.900, 85.132), (45.900, 95.500), (53.800, 95.500),
                     (53.800, 91.691), (52.086, 91.691)])
    return ops


def main():
    bg = geom.load_board(PCB)
    removes = []
    for t in bg.tracks_of():
        cs = [tuple(round(v, 3) for v in c) for c in t.shape.coords]
        if t.net == '+5V_DRV' and any(x > DROP_DRV_EAST_OF for x, _ in cs):
            removes.append({"op": "remove", "uuid": t.uuid})
        elif t.net == '/hk/BUCK_SW':
            for a, b in DROP_BUCK:
                if {cs[0], cs[-1]} == {a, b}:
                    removes.append({"op": "remove", "uuid": t.uuid})
                    break
    adds = build_adds()
    print('remove %d, add %d' % (len(removes), len(adds)))
    OPS.write_text(json.dumps({"version": 1, "ops": adds + removes}, indent=1),
                   encoding='utf-8')
    if '--dry-run' in sys.argv:
        return
    r = subprocess.run([r'C:/dev/ai-ee3/.venv/Scripts/python.exe',
                        S + '/route_edit.py', '--pcb', str(PCB),
                        '--ops', str(OPS), '--out-report',
                        str(OPS.with_name('edit_finish.json'))],
                       capture_output=True, text=True)
    print('route_edit exit', r.returncode)
    print((r.stdout or '')[-1500:], (r.stderr or '')[-800:])


main()
