"""barrier_reroute.py - re-route the A-side magjack taps clear of the MDI band.

WHY (measured, not asserted): the `magjack_isolation_barrier` DRU rule fired 47
times, every hit between /poe/POE_TAP_A1|A2 copper and /ETH_TXP|TXN|RXP|RXN
copper, worst case 0.635 mm against a 1.30 mm requirement. B1/B2 were already
clean - they cross the MDI fan in the WEST channel at x ~ 31/33.5. A1/A2 were
threading the SAME F.Cu neighbourhood the MDI escapes use.

GEOMETRY OF THE PROBLEM (all coordinates measured off the board):
  J1 cable-side taps  : pad 11 (46.300,72.013) pad 12 (43.760,70.743)
  J1 MDI (PHY side)   : pad 1 (46.300,77.063) pad 2 (45.030,74.523)
                        pad 3 (43.760,77.063) pad 6 (39.950,74.523)
  bridges             : D2.1 (47.000,81.680)  D2.2 (43.000,81.680)
The taps sit NORTH of the MDI pad rows and the bridges sit SOUTH of them, so
every tap route MUST cross the MDI fan. Only two gates hold 1.30 mm from an MDI
PTH pad (all four are through-hole, so they block every layer):
    west  x <= 39.188 - 1.30 - 0.10 = 37.788   (used by B1 and B2)
    east  x >= 47.062 + 1.30 + 0.10 = 48.462   (pad 1 is the binding one)
A2 cannot reach the west gate: passing pad 14 needs y >= 72.913 while holding
1.30 mm off pad 6 needs y <= 72.361. So both A-side taps take the east gate.

The crossing itself is legal on B.Cu - the MDI escapes near J1 are F.Cu only and
track-to-track clearance is per layer. What is NOT free is a VIA (all layers) or
a THT pad, so both transitions are placed clear of every MDI item by >= 1.30 mm.

A1 enters the gate from the west (pad 11) and needs the EAST bridge pad; A2
enters from the east (its P7 north detour lands at the via at 49.200,73.400) and
needs the WEST bridge pad. That is a forced crossing, so A1 takes the OUTER lane
(x 49.65) and A2 the INNER lane (x 48.60), and the two cross where A1 is on F.Cu
north of the band while A2 is on B.Cu - no shared layer at the crossing.

usage: python barrier_reroute.py [--pcb P] [--dry-run]
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

A1 = "/poe/POE_TAP_A1"
A2 = "/poe/POE_TAP_A2"
W = 0.2
VIA = dict(size=0.6, drill=0.3)

# --- copper to rip (uuid, why) ---------------------------------------------
RIP = [
    # A1: F.Cu escape that ran down to y 74.95 and its via at y 75.00, both
    # inside 1.30 mm of the ETH_TXN/TXP east trunks at y 76.065 / 76.535.
    ("f30afd0e-81c7-45b9-874a-e2d9d6d7efcc", "A1 F.Cu pad11 -> 48.60,74.30"),
    ("3646f8ad-2d06-4145-8757-45aef4fa90fa", "A1 F.Cu jog"),
    ("8f361f23-e503-475e-bddd-4f7af34ebaec", "A1 F.Cu jog"),
    ("289dce94-deda-45a3-939a-d186a35037c1", "A1 F.Cu 1.085 mm to TXN"),
    ("22d4b14b-bed5-4572-9055-c0bec953b97d", "A1 F.Cu 0.885 mm to TXN"),
    ("5e0ec7bb-4207-4868-a383-569309e4a6e9", "A1 via 0.635 mm to TXN"),
    ("59cd62d8-10d8-483d-a524-613953f8131e", "A1 B.Cu lane at x 48.85"),
    ("751398e9-13fd-48ef-8016-06fc7f43be2f", "A1 B.Cu turn to the via"),
    # A2: the whole B.Cu descent hugged J1 pad 1 (/ETH_TXP) at 0.675-0.688 mm,
    # and its exit via + F.Cu diagonal sat 0.677-1.170 mm off ETH_RXN/RXP.
    ("a2b7bd08-705c-4fc5-86a9-8bfed6b4cb45", "A2 B.Cu entry diagonal"),
    ("d1b1a3c9-b8a8-485b-83d2-d69064dda58b", "A2 B.Cu entry stub"),
    ("3cc642b2-5464-400f-829a-5635685ff087", "A2 B.Cu"),
    ("e96a0fd9-30ac-4359-951e-7f80fb0fcfd9", "A2 B.Cu"),
    ("695d3f7d-7543-4b49-b99e-8b63947da1b3", "A2 B.Cu past J1 pad 1"),
    ("66b6e94a-cd74-4a53-8768-c54ba76b9cd7", "A2 B.Cu 0.688 mm to pad 1"),
    ("0f5ed738-4c28-4de6-9ece-5adeae00a61f", "A2 B.Cu 0.675 mm to pad 1"),
    ("9baed70a-5abe-4e33-be9e-afa123e607f4", "A2 B.Cu 0.678 mm to pad 1"),
    ("d0e99a7d-f221-412e-9324-7e24026849e8", "A2 via 0.677 mm to RXN"),
    ("270c5eec-66ed-4246-80f5-1be0419ef275", "A2 F.Cu 0.913 mm to RXN"),
]

# --- new copper -------------------------------------------------------------
# A1: pad 11 -> F.Cu south-east under the SHIELD tab -> east to the outer lane
# -> via at y 74.213 (1.42 mm clear of the ETH_TXN trunk) -> B.Cu down the
# outer lane -> the EXISTING via at 47.45,81.25 -> the existing stub into D2.1.
A1_TRACKS = [
    ("F.Cu", (46.300, 72.013), (48.500, 74.213)),
    ("F.Cu", (48.500, 74.213), (49.650, 74.213)),
    ("B.Cu", (49.650, 74.213), (49.650, 80.850)),
    ("B.Cu", (49.650, 80.850), (47.450, 81.250)),
]
A1_VIAS = [(49.650, 74.213)]

# A2: from its existing via at 49.20,73.40 into the INNER lane at x 48.60
# (1.44 mm clear of J1 pad 1), down past the whole MDI fan on B.Cu, then west
# below it to a via at 44.60,80.30 (1.67 mm clear of ETH_RXN) and a short F.Cu
# hop into D2.2.
A2_TRACKS = [
    ("B.Cu", (49.200, 73.400), (48.600, 74.000)),
    ("B.Cu", (48.600, 74.000), (48.600, 80.000)),
    ("B.Cu", (48.600, 80.000), (48.300, 80.300)),
    ("B.Cu", (48.300, 80.300), (44.600, 80.300)),
    ("F.Cu", (44.600, 80.300), (43.000, 81.680)),
]
A2_VIAS = [(44.600, 80.300)]


def build_ops():
    ops = [{"op": "remove", "uuid": u} for u, _ in RIP]
    for net, tracks, vias in ((A1, A1_TRACKS, A1_VIAS),
                              (A2, A2_TRACKS, A2_VIAS)):
        for lay, s, e in tracks:
            ops.append({"op": "add_track", "start": list(s), "end": list(e),
                        "width": W, "layer": lay, "net": net})
        for at in vias:
            ops.append({"op": "add_via", "at": list(at), "net": net, **VIA})
    return ops


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pcb", default=str(
        REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_pcb"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ops = build_ops()
    f = HERE / "barrier_reroute_ops.json"
    f.write_text(json.dumps({"version": 1, "ops": ops}, indent=1),
                 encoding="utf-8")
    print("%d ops (%d remove, %d add)"
          % (len(ops), len(RIP), len(ops) - len(RIP)))
    if a.dry_run:
        return
    cp = subprocess.run(
        [str(VENV), str(ROUTE_EDIT), "--pcb", a.pcb, "--ops", str(f),
         "--out-report", str(HERE / "barrier_reroute_report.json")],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    print((cp.stdout or cp.stderr)[-1200:])
    sys.exit(cp.returncode)


if __name__ == "__main__":
    main()
