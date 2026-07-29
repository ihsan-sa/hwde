"""mdi_merge.py - route each MDI leg on its OWN branch, then merge the copper.

KRT will only close an MDI leg when it is routed FIRST: whichever leg runs
second sees the other leg's copper already hanging off D10 and defers the pair
("electrically-short"/multipoint). Measured both ways at P7 - J1<->D10 first
closes and D10<->U10 then defers; D10<->U10 first closes and J1<->D10 then
defers. So each leg is routed from the SAME clean board on its own branch and
the two disjoint copper sets are merged with route_edit.

  branch A (J1's MDI pads detached):  D10 <-> U10, the congested PHY fan-in
  branch B (U10's MDI pads detached): J1  <-> D10, the 38 mm open-board haul

usage: python mdi_merge.py <clean.kicad_pcb> <out.kicad_pcb>
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts"))
sys.path.insert(0, str(REPO / ".claude/skills/ai-ee/scripts/lib"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mdi_chain import MDI, leg  # noqa: E402

VENV = REPO / ".venv/Scripts/python.exe"
ROUTE_EDIT = REPO / ".claude/skills/ai-ee/scripts/route_edit.py"


def copper_of(board: Path, nets) -> list[dict]:
    """route_edit ops recreating every segment/via of `nets` on `board`."""
    txt = board.read_text(encoding="utf-8")
    ops = []
    for tag in ("segment", "via"):
        i = 0
        while True:
            i = txt.find("\n\t(%s" % tag, i)
            if i < 0:
                break
            s, d, j = i + 1, 0, i + 1
            while j < len(txt):
                if txt[j] == "(":
                    d += 1
                elif txt[j] == ")":
                    d -= 1
                    if d == 0:
                        break
                j += 1
            blk = txt[s:j + 1]
            nm = re.search(r'\(net "([^"]*)"\)', blk)
            if nm and nm.group(1) in nets:
                if tag == "segment":
                    st = re.search(r"\(start ([-\d.]+) ([-\d.]+)\)", blk)
                    en = re.search(r"\(end ([-\d.]+) ([-\d.]+)\)", blk)
                    w = re.search(r"\(width ([\d.]+)\)", blk)
                    ly = re.search(r'\(layer "([^"]+)"\)', blk)
                    ops.append({"op": "add_track",
                                "start": [float(st.group(1)), float(st.group(2))],
                                "end": [float(en.group(1)), float(en.group(2))],
                                "width": float(w.group(1)), "layer": ly.group(1),
                                "net": nm.group(1)})
                else:
                    at = re.search(r"\(at ([-\d.]+) ([-\d.]+)\)", blk)
                    sz = re.search(r"\(size ([\d.]+)\)", blk)
                    dr = re.search(r"\(drill ([\d.]+)\)", blk)
                    ops.append({"op": "add_via",
                                "at": [float(at.group(1)), float(at.group(2))],
                                "size": float(sz.group(1)),
                                "drill": float(dr.group(1)), "net": nm.group(1)})
            i = j
    return ops


def main():
    src, dst = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    work = src.parent
    a_in = work / "brA_start.kicad_pcb"
    b_in = work / "brB_start.kicad_pcb"
    shutil.copy2(src, a_in)
    shutil.copy2(src, b_in)
    print("branch A: D10 <-> U10 (J1 detached)")
    a = leg(a_in, work, "J1", "brA")
    print("branch B: J1 <-> D10 (U10 detached)")
    b = leg(b_in, work, "U10", "brB")

    ops = copper_of(b, set(MDI))
    print("branch B copper to graft:", len(ops), "items")
    ops_file = work / "ops_mdi_merge.json"
    ops_file.write_text(json.dumps({"version": 1, "ops": ops}), encoding="utf-8")
    shutil.copy2(a, dst)
    cp = subprocess.run(
        [str(VENV), str(ROUTE_EDIT), "--pcb", str(dst), "--ops", str(ops_file),
         "--out-report", str(work / "merge_report.json")],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(cp.stdout[-400:] or cp.stderr[-400:])
    print("wrote", dst)


if __name__ == "__main__":
    main()
