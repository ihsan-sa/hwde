"""region_dump.py - list every copper item inside a rectangular window.

Needed because the magjack barrier has to be fixed by ROUTING, and a routing
decision needs the whole obstacle field in coordinates: pads (all footprints),
tracks, vias and zone outlines that fall inside the window.

usage: python region_dump.py x0 y0 x1 y1 [board.kicad_pcb] [--nets N,N]
"""
import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
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


ap = argparse.ArgumentParser()
ap.add_argument("x0", type=float)
ap.add_argument("y0", type=float)
ap.add_argument("x1", type=float)
ap.add_argument("y1", type=float)
ap.add_argument("--pcb", default=str(
    REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_pcb"))
ap.add_argument("--pads-only", action="store_true")
a = ap.parse_args()
X0, Y0, X1, Y1 = a.x0, a.y0, a.x1, a.y1


def hit(x, y, m=1.5):
    return X0 - m <= x <= X1 + m and Y0 - m <= y <= Y1 + m


txt = Path(a.pcb).read_text(encoding="utf-8")

print("=== PADS in window [%g %g %g %g] ===" % (X0, Y0, X1, Y1))
import math
for (fs, fe) in blocks(txt, "footprint"):
    blk = txt[fs:fe]
    rm = re.search(r'\(property "Reference" "([^"]+)"', blk)
    ref = rm.group(1) if rm else "?"
    at = re.search(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?", blk)
    if not at:
        continue
    ox, oy = float(at.group(1)), float(at.group(2))
    rot = math.radians(-float(at.group(3) or 0))
    for (ps, pe) in blocks(blk, "pad"):
        pb = blk[ps:pe]
        num = re.match(r'\(pad\s+"([^"]*)"', pb)
        pa = re.search(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)", pb)
        sz = re.search(r"\(size\s+([\d.]+)\s+([\d.]+)", pb)
        nt = re.search(r'\(net\s+\d+\s+"([^"]*)"', pb) or \
            re.search(r'\(net\s+\d+\s*\n?\s*"([^"]*)"', pb) or \
            re.search(r'\(net[^)]*?"([^"]*)"\)', pb)
        ly = re.findall(r'"([FB]\.Cu|\*\.Cu|In\d\.Cu)"', pb)
        if not (pa and sz):
            continue
        lx, ly_ = float(pa.group(1)), float(pa.group(2))
        gx = ox + lx * math.cos(rot) - ly_ * math.sin(rot)
        gy = oy + lx * math.sin(rot) + ly_ * math.cos(rot)
        if not hit(gx, gy):
            continue
        thru = "*.Cu" in pb or "(pad " in pb and "thru_hole" in pb
        print("PAD %-5s %-4s (%9.4f,%9.4f) size %.3f x %.3f %-5s net %s"
              % (ref, num.group(1) if num else "?", gx, gy,
                 float(sz.group(1)), float(sz.group(2)),
                 "THRU" if thru else "SMD", nt.group(1) if nt else "-"))

if a.pads_only:
    sys.exit(0)

print()
print("=== TRACKS / VIAS / ARCS in window ===")
rows = []
for tag in ("segment", "arc", "via"):
    for (s, e) in blocks(txt, tag):
        blk = txt[s:e]
        nm = re.search(r'\(net "([^"]*)"\)', blk) or \
            re.search(r'\(net_name "([^"]*)"\)', blk)
        net = nm.group(1) if nm else None
        if net is None:
            nn = re.search(r"\(net (\d+)\)", blk)
            net = "net#" + nn.group(1) if nn else "?"
        uu = re.search(r'\(uuid "([^"]+)"\)', blk)
        if tag == "via":
            at = re.search(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)", blk)
            sz = re.search(r"\(size\s+([\d.]+)", blk)
            if not (at and sz):
                continue
            x, y = float(at.group(1)), float(at.group(2))
            if hit(x, y):
                rows.append((y, x, "VIA  %-22s (%9.4f,%9.4f) size %.3f %-12s %s"
                             % (net, x, y, float(sz.group(1)), "all",
                                uu.group(1) if uu else "")))
        else:
            st = re.search(r"\(start\s+(-?[\d.]+)\s+(-?[\d.]+)", blk)
            en = re.search(r"\(end\s+(-?[\d.]+)\s+(-?[\d.]+)", blk)
            w = re.search(r"\(width\s+([\d.]+)", blk)
            lyr = re.search(r'\(layer "([^"]+)"', blk)
            x1, y1 = float(st.group(1)), float(st.group(2))
            x2, y2 = float(en.group(1)), float(en.group(2))
            if hit(x1, y1) or hit(x2, y2):
                rows.append((min(y1, y2), min(x1, x2),
                             "%-4s %-22s (%9.4f,%9.4f)->(%9.4f,%9.4f) w %.4f %-8s %s"
                             % (tag[:4].upper(), net, x1, y1, x2, y2,
                                float(w.group(1)),
                                lyr.group(1) if lyr else "?",
                                uu.group(1) if uu else "")))
rows.sort()
for r in rows:
    print(r[2])
