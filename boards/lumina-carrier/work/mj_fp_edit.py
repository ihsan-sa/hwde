"""Library edit + gap measurement for J1 RJ45-TH_LPJG0926HENL_C22457393.

Three edits, all recorded in lib/EDITS.md:

  A. ISOLATION MITIGATION (mandatory). Pads 9/10 = TD4+/TD4- are the chip-side
     winding ends of the J7/J8 spare pair, which the W5500 never drives, and
     they are left as BARE no-connect pads by poe.py.  Shrink them 1.524 ->
     1.300 mm so the nearest copper to the 48 V line-side taps belongs to a
     dead net.
     Measurement showed that alone is NOT enough: the closest ENERGISED chip
     pad is pad 2 (TD1- = /ETH_TXN) at 2.8130 mm c-c from pad 11 (VC1), which
     at the as-pulled 1.524 mm pads is only 1.289 mm - under HALO's 1.40 mm
     land guidance at this pitch.  So VC1 (11) and VC4 (14), the two 48 V pads
     that set every minimum, are shrunk 1.524 -> 1.300 mm as well.  They carry
     0.6 A on a 0.90 mm drill; 1.300 mm leaves 0.200 mm/side annular ring,
     above JLC's 0.15 mm PTH floor.

  B. Mounting holes -> np_thru_hole.  The pull made the two dia-3.20 mm holes
     PLATED with pad size == drill, i.e. zero annular ring, which trips DRC at
     P7.  Same defect and same fix as EDITS.md edit 4 on the HY931147C land.

  C. Courtyard.  The pull omitted F.CrtYd; 29 of the library's 30 footprints
     carry one.  Drawn on the silk body outline + 0.25 mm.
"""
from __future__ import annotations

import io
import json
import math
import re
from itertools import combinations

FP = (r"C:\dev\ai-ee3\boards\lumina-carrier\lib\aiee.pretty"
      r"\RJ45-TH_LPJG0926HENL_C22457393.kicad_mod")

# pad -> net role on the poe sheet (see kicad/gen/poe.py)
ROLE = {
    "1": "live /ETH_TXP", "2": "live /ETH_TXN", "3": "live /ETH_RXP",
    "4": "live +3V3 (CT)", "5": "live +3V3 (CT)", "6": "live /ETH_RXN",
    "7": "dead NC (TD3+)", "8": "dead NC (TD3-)",
    "9": "dead NC (TD4+)", "10": "dead NC (TD4-)",
    "11": "HV VC1", "12": "HV VC2", "13": "HV VC3", "14": "HV VC4",
    "15": "live LED_G_A", "16": "live /ETH_LED_LINK",
    "17": "live LED_Y_A", "18": "live /ETH_LED_ACT",
    "19": "SHIELD (EH)", "20": "SHIELD (EH)",
}
HV = {"11", "12", "13", "14"}

PAD_RE = re.compile(
    r'\(pad (?P<num>"[^"]*"|\S+) (?P<type>\S+) (?P<shape>\S+) '
    r'\(at (?P<x>[-0-9.]+) (?P<y>[-0-9.]+)(?P<rot>[^)]*)\) '
    r'\(size (?P<w>[-0-9.]+) (?P<h>[-0-9.]+)\)')


def pads(txt):
    out = []
    for m in PAD_RE.finditer(txt):
        num = m.group("num").strip('"')
        out.append({"num": num, "x": float(m.group("x")),
                    "y": float(m.group("y")), "w": float(m.group("w")),
                    "h": float(m.group("h")), "type": m.group("type")})
    return out


def gaps(ps, title):
    """Every pad-pair copper gap, circular pads (all pads here are circles)."""
    rows = []
    by = {p["num"]: p for p in ps}
    for a, b in combinations([p for p in ps if p["num"]], 2):
        cc = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
        g = cc - a["w"] / 2 - b["w"] / 2
        rows.append((g, cc, a["num"], b["num"]))
    rows.sort()
    print("\n=== %s ===" % title)
    print("%-6s %-6s %-8s %-22s %-22s" % ("gap", "c-c", "pads", "A", "B"))
    for g, cc, a, b in rows[:14]:
        print("%6.3f %6.3f  %-3s-%-3s %-22s %-22s"
              % (g, cc, a, b, ROLE.get(a, "?"), ROLE.get(b, "?")))
    # the two numbers that matter
    def mn(pred):
        c = [(g, a, b) for g, cc, a, b in rows if pred(a, b)]
        return min(c) if c else None
    live = mn(lambda a, b: ((a in HV) != (b in HV))
              and str(ROLE.get(a, "")).startswith("live")
              or ((a in HV) != (b in HV))
              and str(ROLE.get(b, "")).startswith("live"))
    dead = mn(lambda a, b: ((a in HV) != (b in HV))
              and ("dead" in ROLE.get(a, "") or "dead" in ROLE.get(b, "")))
    shld = mn(lambda a, b: ((a in HV) != (b in HV))
              and ("SHIELD" in ROLE.get(a, "") or "SHIELD" in ROLE.get(b, "")))
    print(" min HV <-> ENERGISED chip net : %.3f mm  (%s-%s)" % live)
    print(" min HV <-> bare NC pad        : %.3f mm  (%s-%s)" % dead)
    print(" min HV <-> SHIELD board lock  : %.3f mm  (%s-%s)" % shld)
    return {"live": live, "dead": dead, "shield": shld}


txt = io.open(FP, encoding="utf-8").read()
before = gaps(pads(txt), "AS PULLED (all pads 1.524 mm)")

# --- edit A: shrink pads 9, 10 (bare NC) and 11, 14 (the 48 V taps) --------
for num in ("9", "10", "11", "14"):
    pat = (r'(\(pad %s thru_hole circle \(at [-0-9.]+ [-0-9.]+ [-0-9.]+\) '
           r'\(size )1\.524 1\.524(\))' % num)
    txt, n = re.subn(pat, r"\g<1>1.300 1.300\g<2>", txt)
    assert n == 1, "pad %s: %d substitutions" % (num, n)

# --- edit B: the two dia-3.20 mounting holes -> non-plated ----------------
txt, n = re.subn(r'\(pad "" thru_hole circle', '(pad "" np_thru_hole circle',
                 txt)
assert n == 2, "mounting holes: %d substitutions" % n

# --- edit C: courtyard on the silk body outline + 0.25 mm ----------------
X, Y0, Y1 = 7.96 + 0.25, -8.03 - 0.25, 13.21 + 0.25
crt = "\n".join(
    "\t(fp_line (start %.2f %.2f) (end %.2f %.2f) (layer F.CrtYd) (width 0.05))"
    % seg for seg in [(-X, Y0, X, Y0), (X, Y0, X, Y1),
                      (X, Y1, -X, Y1), (-X, Y1, -X, Y0)])
assert "F.CrtYd" not in txt
txt = txt.replace("\n\t(model ", "\n" + crt + "\n\t(model ")

io.open(FP, "w", encoding="utf-8", newline="\n").write(txt)
after = gaps(pads(txt), "AFTER EDIT (9/10/11/14 = 1.300 mm)")

print("\nHALO land guidance at 2.54 mm pitch = 1.40 mm")
print("board creepage rule (constraints.json voltages, 57 V) = 0.635 mm")
print(json.dumps({"before": {k: v[0] for k, v in before.items()},
                  "after": {k: v[0] for k, v in after.items()}}, indent=1))
