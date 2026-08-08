"""P6 structural placement for rf-de-20m - emits absolute place_edit ops.

Board-local coords (0..120 x, 0..80 y); translated by outline_bbox origin.
Everything emitted here is LOCKED: it is geometry the annealer cannot invent.
"""
import json
import sys
from pathlib import Path

OX, OY = 6.634999, 39.334999          # outline_bbox origin (board-local -> board)

ops = []


def place(ref, x, y, deg=0):
    ops.append({"op": "place", "ref": ref, "x": round(x + OX, 4),
                "y": round(y + OY, 4), "deg": deg})
    ops.append({"op": "lock", "ref": ref, "locked": True})


# ---------------------------------------------------------------- zone A: GaN
# Mirror axis y = 24.775 (the two gate pads). Dies at angle 0, stacked in y so
# drains escape INWARD (shared /SW channel) and sources OUTWARD (two GND
# islands with the thermal via fields). Gates + their pin-2 source returns both
# escape -x on the same column -> minimum-area gate loop.
place("Q201", 31.5, 22.9, 0)          # gate pin1 -> (30.3, 22.675)
place("Q202", 31.5, 27.1, 0)          # gate pin1 -> (30.3, 26.875)

# LMG1020 at 270 deg: OUTH (24.5,24.775) and OUTL (24.1,24.775) both land ON
# the mirror axis, so all four gate legs are exact mirror images.
# North row (24.375) = VDD/GND/IN+, south row (24.775) = OUTH/OUTL/IN-.
place("U201", 24.1, 24.575, 270)

# Gate legs. OUTH (7 A source, 400 ps) gets the SHORT inner pair.
place("R203", 27.5, 23.575, 0)        # OUTH -> GATE_Q1
place("R204", 27.5, 25.975, 0)        # OUTH -> GATE_Q2
place("R205", 27.5, 21.275, 0)        # OUTL -> GATE_Q1
place("R206", 27.5, 28.275, 0)        # OUTL -> GATE_Q2

# VDD chain, north of U201 (the VDD/GND row).  FB201 is UPSTREAM of all three.
place("C202", 24.1, 23.35, 0)         # 10 nF 0201, closest to the VDD ball
place("C201", 24.1, 22.10, 0)         # 100 nF 0402
place("C213", 24.1, 20.60, 0)         # 1 uF 0603 (TI s9 reservoir)
place("FB201", 24.1, 18.70, 0)        # bead: +5V -> +5V_DRV, upstream of C201/2/213

# C_shunt trim bank: pad1 (/SW) faces the inner drain channel, pad2 (GND) the
# outer source island -> the cap sits IN the power loop, not on a stub.
place("C203", 35.0, 22.0, 90)
place("C204", 37.8, 22.0, 90)
place("C205", 35.0, 28.0, 270)
place("C206", 37.8, 28.0, 270)

# ------------------------------------------------------------- connectors
place("J101", 3.7, 40.0, 270)         # KF128 opens out the LEFT edge; pins x<5 (HS-3)
place("J201", 24.0, 5.0, 0)           # SMA drive in, top edge pos 0.2
place("J301", 115.3, 62.0, 0)         # SMA RF out, right edge, next to L302

# ------------------------------------------------------------- zone B: spirals
# Both at 180 deg: pad1 (winding + east land in local frame) carries /SW resp.
# TANK_B and must face WEST; pad2 (west land + inner bridge) carries TANK_A
# resp. RFOUT and must face EAST.
place("L301", 72.0, 18.0, 180)        # /SW land (53.7,18); TANK_A land (90.3,18)
place("L302", 85.0, 62.0, 180)        # TANK_B land (66.965,62); RFOUT land (103.035,62)

# C_s bank - zone B west free pocket, clear of both 20.55 mm spiral keepouts.
CS = ["C301", "C302", "C303", "C304", "C305", "C306", "C307", "C308", "C309",
      "C320", "C321"]
for i, ref in enumerate(CS):
    place(ref, 57.0, 38.0 + 3.0 * i, 0)   # pad1 TANK_A west, pad2 TANK_B east

# C_m bank - zone C, straddling RFOUT between L302's east land and J301.
CM = ["C310", "C311", "C312", "C313", "C314", "C315", "C316", "C317", "C318",
      "C319", "C322", "C323"]
for i, ref in enumerate(CM):
    place(ref, 108.0, 44.5 + 3.0 * i, 0)  # pad1 RFOUT west, pad2 GND east

out = Path(sys.argv[1])
out.write_text(json.dumps({"version": 1, "ops": ops}, indent=1), encoding="utf-8")
print(json.dumps({"ops": len(ops), "out": str(out)}))
