"""net_inventory.py - every net with its copper counts, for choosing a rip set.

Protected nets (never rip): the MDI diff pairs (hand-routed, skew-checked), the
magjack cable-side taps (their barrier geometry was hand-solved), the three 48 V
nets (0.635 mm DRU) and /poe/SHIELD.

usage: python net_inventory.py [board.kicad_pcb]
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
BOARD = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_pcb")
PROTECT = {"/ETH_TXP", "/ETH_TXN", "/ETH_RXP", "/ETH_RXN",
           "/poe/POE_TAP_A1", "/poe/POE_TAP_A2",
           "/poe/POE_TAP_B1", "/poe/POE_TAP_B2",
           "V48_RAW", "+48V_SW", "V48_RTN", "/poe/SHIELD"}
PLANE = {"GND", "+3V3", "+12V"}

txt = BOARD.read_text(encoding="utf-8")
seg = {}
via = {}
for m in re.finditer(r'\(segment\b[^)]*?\(net "([^"]*)"\)', txt, re.S):
    seg[m.group(1)] = seg.get(m.group(1), 0) + 1
for m in re.finditer(r'\(via\b.*?\(net "([^"]*)"\)', txt, re.S):
    pass
# vias: scan blocks (regex over nested parens is unreliable)
i = 0
while True:
    i = txt.find("\n\t(via", i)
    if i < 0:
        break
    j = txt.find("\n\t)", i)
    blk = txt[i:j]
    nm = re.search(r'\(net "([^"]*)"\)', blk)
    if nm:
        via[nm.group(1)] = via.get(nm.group(1), 0) + 1
    i = j

nets = sorted(set(seg) | set(via))
ripable = []
print("%-24s %6s %5s  %s" % ("net", "segs", "vias", "class"))
for n in nets:
    kind = ("PROTECTED" if n in PROTECT else
            "plane" if n in PLANE else "ripable")
    if kind == "ripable":
        ripable.append(n)
    print("%-24s %6d %5d  %s" % (n, seg.get(n, 0), via.get(n, 0), kind))
print()
print("ripable nets: %d" % len(ripable))
(Path(__file__).resolve().parent / "ripable_nets.json").write_text(
    json.dumps(ripable, indent=1), encoding="utf-8")
