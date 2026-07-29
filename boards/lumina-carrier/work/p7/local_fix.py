"""local_fix.py - hand-route the short local connections KRT cannot reach.

Each of these is a pad that A* declared "boxed in by static obstacles": the
escape corridor is narrower than KRT's grid+clearance model can thread, but a
hand-computed 0.1 mm neckdown (the idiom the rest of this board's LQFP taps
already use) does fit. Every number below was measured off the board.

  U10 pad 19 (GND, east edge, 0.5 mm pitch)
      The east-edge pad column ends at x 101.4258 and the +3V3 fan-out via at
      (102.25, 78.50) occupies x 101.95-102.55, leaving a 0.5242 mm slot. A
      0.1 mm track centred at x 101.6879 holds 0.2121 mm to both sides. It runs
      south to y 79.60 and lands on the existing GND chain at (101.65, 79.70).

  U10 pad 23 (GND, east edge)
      Same slot, but southward is blocked by the /eth/TOCAP escape (needs
      0.495 mm perpendicular; only 0.35 available), so this one goes NORTH past
      C32's pad (x >= 101.945, y 75.325-76.675 - the same 0.5242 mm slot) and
      drops to the In1 GND plane through a via at (101.6879, 74.60), which
      clears C32's pad by 0.425 mm and the /eth/1V2O diagonal by 0.263 mm.

  V48_RAW B.Cu/F.Cu junction at (41.15, 93.4818)
      The B.Cu run to C62 ENDS there with no via - that is the `track_dangling`
      warning. The F.Cu 0.8 mm trunk already passes through the same point, so a
      single via closes it.

  V48_RAW via at (37.6, 94.75)  -> REMOVED
      Every segment on it is B.Cu; nothing lands on its F.Cu side, so it is a
      leftover and the source of the `via_dangling` warning.

  U22 pads 2-3 (V48_RAW) and 18-19 (+48V_SW)
      Adjacent same-net pins, 0.65 mm pitch, 0.4 mm tall. A 0.4 mm track along
      the pad centreline links them; the nearest foreign copper is U22's own
      no-net pins 4/17 at 0.25 mm, which the .kicad_dru's per-refdes
      same-courtyard exclusion covers (and which no routing choice can widen).

  U22 pad 6 (V48_RAW)
      Cannot reach pads 1-3 on F.Cu: passing pins 4/5 needs x <= 39.95 while the
      pins themselves start at x 40.35. So it goes west 1.34 mm, drops to B.Cu at
      (39.8, 96.325) - 1.03 mm clear of R66's /pwr/UVLO pad, well over the
      0.635 mm HV rule - and rejoins the existing B.Cu trunk at (39.8, 93.5).

usage: python local_fix.py [--pcb P] [--dry-run]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
VENV = REPO / ".venv/Scripts/python.exe"
ROUTE_EDIT = REPO / ".claude/skills/ai-ee/scripts/route_edit.py"
HERE = Path(__file__).resolve().parent

T = "add_track"
V = "add_via"
OPS = [
    # --- U10 pad 19 GND -> existing GND chain ---------------------------------
    {"op": T, "start": [100.6758, 78.4319], "end": [101.6879, 78.4319],
     "width": 0.1, "layer": "F.Cu", "net": "GND"},
    {"op": T, "start": [101.6879, 78.4319], "end": [101.6879, 79.60],
     "width": 0.1, "layer": "F.Cu", "net": "GND"},
    {"op": T, "start": [101.6879, 79.60], "end": [101.65, 79.70],
     "width": 0.1, "layer": "F.Cu", "net": "GND"},
    # --- U10 pad 23 GND -> In1 plane via -------------------------------------
    {"op": T, "start": [100.6758, 76.4319], "end": [101.6879, 76.4319],
     "width": 0.1, "layer": "F.Cu", "net": "GND"},
    {"op": T, "start": [101.6879, 76.4319], "end": [101.6879, 74.60],
     "width": 0.1, "layer": "F.Cu", "net": "GND"},
    {"op": V, "at": [101.6879, 74.60], "size": 0.6, "drill": 0.3, "net": "GND"},
    # --- V48_RAW layer junction + leftover via -------------------------------
    {"op": V, "at": [41.15, 93.4818], "size": 0.6, "drill": 0.3,
     "net": "V48_RAW"},
    {"op": "remove", "uuid": "d0ada395-7f58-4b55-8118-c5240642a1b2"},
    # --- U22 V48_RAW pads 2-3 -----------------------------------------------
    {"op": T, "start": [41.1375, 93.725], "end": [41.1375, 94.375],
     "width": 0.4, "layer": "F.Cu", "net": "V48_RAW"},
    # --- U22 V48_RAW pad 6 via B.Cu ------------------------------------------
    {"op": T, "start": [41.1375, 96.325], "end": [39.8, 96.325],
     "width": 0.4, "layer": "F.Cu", "net": "V48_RAW"},
    {"op": V, "at": [39.8, 96.325], "size": 0.6, "drill": 0.3,
     "net": "V48_RAW"},
    {"op": T, "start": [39.8, 96.325], "end": [39.8, 93.5],
     "width": 0.4, "layer": "B.Cu", "net": "V48_RAW"},
    # --- U22 +48V_SW pads 18-19 ---------------------------------------------
    {"op": T, "start": [46.8625, 93.725], "end": [46.8625, 94.375],
     "width": 0.4, "layer": "F.Cu", "net": "+48V_SW"},
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pcb", default=str(
        REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_pcb"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    f = HERE / "local_fix_ops.json"
    f.write_text(json.dumps({"version": 1, "ops": OPS}, indent=1),
                 encoding="utf-8")
    print("%d ops" % len(OPS))
    if a.dry_run:
        return
    cp = subprocess.run(
        [str(VENV), str(ROUTE_EDIT), "--pcb", a.pcb, "--ops", str(f),
         "--out-report", str(HERE / "local_fix_report.json")],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    print((cp.stdout or cp.stderr)[-1500:])
    sys.exit(cp.returncode)


if __name__ == "__main__":
    main()
