"""tap_geo.py - dump the geometry that the magjack barrier depends on.

Prints, for the four cable-side tap nets and the four MDI nets: every pad, and
every routed segment/via, so the barrier conflict can be reasoned about in
coordinates rather than from DRC messages alone.

usage: python tap_geo.py [board.kicad_pcb]
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
import geom  # noqa: E402

BOARD = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_pcb")
TAPS = ("/poe/POE_TAP_A1", "/poe/POE_TAP_A2",
        "/poe/POE_TAP_B1", "/poe/POE_TAP_B2")
MDI = ("/ETH_TXP", "/ETH_TXN", "/ETH_RXP", "/ETH_RXN")
BS = "\\"


def blocks(t, tok, st=0, en=None):
    en = len(t) if en is None else en
    i, pat = st, "(" + tok
    while True:
        i = t.find(pat, i, en)
        if i < 0:
            return
        j, d, q = i, 0, False
        while j < en:
            c = t[j]
            if c == '"' and t[j - 1] != BS:
                q = not q
            elif not q:
                if c == "(":
                    d += 1
                elif c == ")":
                    d -= 1
                    if d == 0:
                        yield (i, j + 1)
                        break
            j += 1
        i = j + 1


txt = BOARD.read_text(encoding="utf-8")
bg = geom.BoardGeom.from_file(str(BOARD))

print("=== PADS ===")
for n in TAPS + MDI:
    for p in bg.pads_of(net=n):
        c = p.poly.centroid
        print("%-22s %-5s pad %-4s (%8.3f,%8.3f)"
              % (n, p.ref, p.number, c.x, c.y))

print()
print("=== FOOTPRINT ORIGINS (context) ===")
for (a, b) in blocks(txt, "footprint"):
    blk = txt[a:b]
    rm = re.search(r'\(property "Reference" "([^"]+)"', blk)
    if not rm or rm.group(1) not in ("J1", "D2", "D3", "D10", "U10",
                                     "C4", "C5", "R1", "R2"):
        continue
    at = re.search(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?", blk)
    print("%-5s (%8.3f,%8.3f) rot %s"
          % (rm.group(1), float(at.group(1)), float(at.group(2)),
             at.group(3) or "0"))

print()
print("=== COPPER ON TAP + MDI NETS ===")
for tag in ("segment", "via", "arc"):
    for (a, b) in blocks(txt, tag):
        blk = txt[a:b]
        nm = re.search(r'\(net_name "([^"]*)"\)', blk) or \
            re.search(r'\(net "([^"]*)"\)', blk)
        if not nm:
            continue
        net = nm.group(1)
        if net not in TAPS + MDI:
            continue
        uu = re.search(r'\(uuid "([^"]+)"\)', blk)
        if tag == "via":
            at = re.search(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)", blk)
            print("VIA  %-22s (%8.3f,%8.3f)          uuid %s"
                  % (net, float(at.group(1)), float(at.group(2)),
                     uu.group(1) if uu else "?"))
        else:
            st = re.search(r"\(start\s+(-?[\d.]+)\s+(-?[\d.]+)", blk)
            en = re.search(r"\(end\s+(-?[\d.]+)\s+(-?[\d.]+)", blk)
            w = re.search(r"\(width\s+([\d.]+)", blk)
            ly = re.search(r'\(layer "([^"]+)"', blk)
            print("%-4s %-22s (%8.3f,%8.3f)->(%8.3f,%8.3f) w %.4f %-6s uuid %s"
                  % (tag.upper(), net, float(st.group(1)), float(st.group(2)),
                     float(en.group(1)), float(en.group(2)),
                     float(w.group(1)), ly.group(1),
                     uu.group(1) if uu else "?"))
