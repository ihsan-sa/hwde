"""rf-de-20m P7 - generate the planes sidecar for planes_gen.

Rects are authored BOARD-LOCAL (origin = outline top-left) and translated to
absolute here.  The absolute origin is read from the board outline, never
hard-coded (LEARNINGS 2026-08-08 [constraints][COORDINATE TRAP]).

Layer allocation (see reports/route-notes.md):
  In1/In2/B.Cu  GND per architecture (zone A + zone C + the B.Cu bridge)
  F.Cu          GND blanket (lowest priority) + shaped pours for the five
                fat nets, which cannot be tracks (route_critical --pad-window
                exit 1: every fat pad is under its DRU width floor).
  B.Cu          one +40V bridge: on F.Cu the x 39..51 / y 12..34 channel is a
                single corridor that BOTH /SW (drain -> L301) and +40V must
                cross, and they cannot cross on one layer.  /SW keeps F.Cu.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, r'C:/dev/ai-ee3/.claude/skills/ai-ee/scripts')
from lib.geom import load_board                                    # noqa: E402

PCB = Path(r'C:/dev/ai-ee3/boards/rf-de-20m/kicad/rf-de-20m.kicad_pcb')
OUT = Path(r'C:/dev/ai-ee3/boards/rf-de-20m/route/planes.json')

bg = load_board(str(PCB))
OX, OY = bg.outline.bounds[0], bg.outline.bounds[1]


def L(x1, y1, x2, y2):
    """board-local rect -> absolute rect"""
    return [round(x1 + OX, 4), round(y1 + OY, 4),
            round(x2 + OX, 4), round(y2 + OY, 4)]


planes = [
    # ---------------- GND: inner planes + B.Cu (architecture, unchanged) ----
    {"net": "GND", "layer": "In1.Cu", "region": L(0, 0, 51, 80)},
    {"net": "GND", "layer": "In1.Cu", "region": L(96, 0, 120, 80)},
    {"net": "GND", "layer": "In2.Cu", "region": L(0, 0, 51, 80)},
    {"net": "GND", "layer": "In2.Cu", "region": L(92, 0, 120, 80)},
    {"net": "GND", "layer": "B.Cu", "region": L(0, 0, 51, 80)},
    {"net": "GND", "layer": "B.Cu", "region": L(92, 0, 120, 80)},
    {"net": "GND", "layer": "B.Cu", "region": L(49, 30, 94, 48)},

    # ---------------- F.Cu GND blanket (lowest priority) -------------------
    # connect solid: thermal spokes starve on this board (0.4 mm pads next
    # to 0.8 mm-clearance HV pours give 1 spoke, not 2 -> starved_thermal)
    {"net": "GND", "layer": "F.Cu", "region": L(0.3, 0.3, 50.0, 79.7),
     "priority": 0, "connect": "solid"},
    {"net": "GND", "layer": "F.Cu", "region": L(92.2, 0.3, 119.7, 79.7),
     "priority": 0, "connect": "solid"},

    # ---------------- +40V bus (F.Cu) --------------------------------------
    # left column: J101.1 / C101.1 / C102.1 / C103.1 / C104.1
    {"net": "+40V", "layer": "F.Cu", "region": L(0.4, 0.4, 16.2, 79.6),
     "priority": 3, "connect": "solid"},
    # bottom sweep east, then north past the buck
    {"net": "+40V", "layer": "F.Cu", "region": L(16.2, 55.6, 51.0, 79.6),
     "priority": 3, "connect": "solid"},
    {"net": "+40V", "layer": "F.Cu", "region": L(16.2, 31.0, 51.0, 34.2),
     "priority": 3, "connect": "solid"},
    {"net": "+40V", "layer": "F.Cu", "region": L(46.3, 34.2, 51.0, 55.6),
     "priority": 3, "connect": "solid"},
    # buck taps: U101.2/.3 + C105.1
    {"net": "+40V", "layer": "F.Cu", "region": L(41.5, 47.4, 51.0, 51.35),
     "priority": 3, "connect": "solid"},
    # HF bank strips C207..C212
    {"net": "+40V", "layer": "F.Cu", "region": L(28.2, 0.4, 39.3, 19.0),
     "priority": 3, "connect": "solid"},
    # top-right band -> L201.1 (choke bus side)
    {"net": "+40V", "layer": "F.Cu", "region": L(37.4, 0.4, 51.0, 13.5),
     "priority": 3, "connect": "solid"},

    # ---------------- +40V bus bridge on B.Cu ------------------------------
    {"net": "+40V", "layer": "B.Cu", "region": L(42.5, 6.0, 51.3, 33.0),
     "priority": 3, "connect": "solid"},

    # ---------------- /SW drain node (F.Cu) --------------------------------
    # C_shunt bank + the area around the FET pair
    {"net": "/SW", "layer": "F.Cu", "region": L(29.4, 19.2, 39.4, 30.8),
     "priority": 6, "connect": "solid"},
    # east run under L202 to the choke output
    {"net": "/SW", "layer": "F.Cu", "region": L(38.7, 19.2, 51.5, 27.5),
     "priority": 6, "connect": "solid"},
    # north to L202.2 and out to the L301 keepout edge
    {"net": "/SW", "layer": "F.Cu", "region": L(42.9, 12.5, 51.5, 20.0),
     "priority": 6, "connect": "solid"},
    # EPC2019 landing lobes.  MEASURED on this board: a .kicad_dru rule
    # beats a zone's local clearance during fill, so aiee_hv_143v_SW (0.8 mm)
    # governs every pour near the die and NO zone can touch a source or
    # drain bump - the fill stops 0.20 mm short of the source pads and
    # 0.66 mm short of pin4.  These lobes are therefore only the LANDING
    # pads; the last 0.2-1.2 mm is carried by 0.25 mm fan-in tracks
    # (route_edit), which is the widest conductor the 0.6 mm bump pitch
    # admits and introduces no spacing tighter than the 0.35 mm already
    # waived.
    {"net": "GND", "layer": "F.Cu", "region": L(29.90, 19.50, 33.60, 22.90),
     "priority": 8, "connect": "solid", "clearance": 0.33, "min_width": 0.15},
    {"net": "GND", "layer": "F.Cu", "region": L(29.90, 27.10, 33.60, 30.50),
     "priority": 8, "connect": "solid", "clearance": 0.33, "min_width": 0.15},
    {"net": "GND", "layer": "F.Cu", "region": L(32.50, 20.40, 33.60, 23.10),
     "priority": 8, "connect": "solid", "clearance": 0.33, "min_width": 0.15},
    {"net": "GND", "layer": "F.Cu", "region": L(32.50, 26.90, 33.60, 29.60),
     "priority": 8, "connect": "solid", "clearance": 0.33, "min_width": 0.15},
    # west flanks: pin2 of each die.  Tall enough to host a stitch via -
    # the pad itself is boxed in by the gate bump above and the drain bar
    # east, so the lobe has to reach down the free channel to find room.
    {"net": "GND", "layer": "F.Cu", "region": L(29.55, 22.95, 30.42, 26.30),
     "priority": 8, "connect": "solid", "clearance": 0.33, "min_width": 0.15},
    {"net": "GND", "layer": "F.Cu", "region": L(29.55, 27.30, 30.42, 29.60),
     "priority": 8, "connect": "solid", "clearance": 0.33, "min_width": 0.15},

    # ---------------- tank (F.Cu) ------------------------------------------
    # TANK_A: C_s pad-1 column
    {"net": "/tank/TANK_A", "layer": "F.Cu", "region": L(50.9, 31.0, 57.0, 70.6),
     "priority": 5, "connect": "solid"},
    # TANK_A: the ONLY way east is ABOVE the C_s bank - the bank's own
    # TANK_B pads own x 57.0..60.2 from y 36.3 down to y 69.7, and the L301
    # keepout owns everything above y 31.7..34.4 there.  The surviving lane
    # is 4.6 mm wide at x 57 narrowing to 1.9 mm at x 60.1.
    {"net": "/tank/TANK_A", "layer": "F.Cu", "region": L(50.9, 31.0, 61.0, 36.2),
     "priority": 5, "connect": "solid"},
    # TANK_A: the ~6 mm perpendicular gap between the two spiral keepouts
    {"net": "/tank/TANK_A", "layer": "F.Cu", "region": L(60.6, 31.0, 95.8, 44.0),
     "priority": 5, "connect": "solid"},
    # TANK_A: descent east of the L301 keepout to L301.2
    {"net": "/tank/TANK_A", "layer": "F.Cu", "region": L(86.0, 6.0, 95.8, 44.0),
     "priority": 5, "connect": "solid"},
    # TANK_B: C_s pad-2 column, then an arm east to L302.1 that stays BELOW
    # the TANK_A corridor.
    {"net": "/tank/TANK_B", "layer": "F.Cu", "region": L(57.8, 36.4, 60.2, 71.5),
     "priority": 4, "connect": "solid"},
    {"net": "/tank/TANK_B", "layer": "F.Cu", "region": L(60.2, 47.0, 66.6, 71.5),
     "priority": 4, "connect": "solid"},
    # RFOUT: zone C.  Split into columns so the F.Cu GND blanket keeps a
    # solid return between the C_m rows and around the J301 shell.
    {"net": "/tank/RFOUT", "layer": "F.Cu", "region": L(104.6, 38.0, 107.8, 78.0),
     "priority": 5, "connect": "solid"},
    {"net": "/tank/RFOUT", "layer": "F.Cu", "region": L(111.0, 34.0, 114.8, 57.2),
     "priority": 5, "connect": "solid"},
    {"net": "/tank/RFOUT", "layer": "F.Cu", "region": L(111.0, 66.8, 114.8, 78.0),
     "priority": 5, "connect": "solid"},
    # J301 centre-pin feed: threads the 1.28 mm gap between the shell pads
    {"net": "/tank/RFOUT", "layer": "F.Cu", "region": L(105.0, 61.4, 117.0, 62.7),
     "priority": 5, "connect": "solid"},
    # column ties: above the C_m GND column, and through the C314/C315 lane
    {"net": "/tank/RFOUT", "layer": "F.Cu", "region": L(104.6, 34.0, 114.8, 43.3),
     "priority": 5, "connect": "solid"},
    {"net": "/tank/RFOUT", "layer": "F.Cu", "region": L(107.5, 66.7, 114.8, 68.3),
     "priority": 5, "connect": "solid"},
]


# --------------------------------------------------------------------------
# Two-pass output.  A via added into an already-filled zone of a FOREIGN net
# takes that zone's net (KiCad re-derives it from connectivity; the fill has
# no antipad yet).  So the GND pours are laid first, the GND stitch vias go
# in while nothing but GND is poured, and the power pours follow.
mode = sys.argv[1] if len(sys.argv) > 1 else 'all'
if mode == 'gnd':
    planes = [p for p in planes if p['net'] == 'GND']
    OUT = OUT.with_name('planes_gnd.json')
elif mode == 'pwr':
    # the GND pours already exist by now; re-emitting them would duplicate
    # the zones (KiCad 10: same-net same-priority overlap = zones_intersect)
    planes = [p for p in planes if p['net'] != 'GND']
    OUT = OUT.with_name('planes_pwr.json')

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"planes": planes}, indent=1), encoding='utf-8')
print(f'outline origin ({OX:.3f}, {OY:.3f}); wrote {len(planes)} '
      f'{mode} zones -> {OUT}')
