"""board_swig.py - SWIG worker for board_init.py. BUNDLED python only.

Runs under KiCad's bundled python.exe (the only interpreter with `pcbnew`),
launched as a subprocess by board_init.py (venv). Consumes a JSON job on argv,
places every footprint from a netlist netmap onto a fresh board, assigns pad
nets, spreads parts on a shelf grid (no courtyard overlaps), draws the outline
and mounting holes, and saves an UNFILLED board. Mirrors the corpus builder
tests/golden/generators/pcb_build.py; zone fill (if any) is a later kicad-cli
step - pcbnew.ZONE_FILLER segfaults headless (LEARNINGS [swig]).

Job JSON (all lengths mm):
  out            output .kicad_pcb path
  layers         2 | 4
  components     [{ref, value, fp:"Lib:Name"}, ...]
  netmap         {"REF.PAD": "netname", ...}
  fp_paths       [dir, ...] searched for "<Lib>.pretty/<Name>.kicad_mod"
  margin         gap between packed parts + border to outline (default 5.0)
  outline        {mode:"auto"} | {mode:"fixed", w, h}
  mounting_holes {count, fp:"Lib:Name", inset} | null

Result JSON to stdout: {status, out, placed, nets, bbox:[x1,y1,x2,y2], notes}.
Exit 0 ok, 2 error.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pcbnew  # noqa: E402  (bundled python only)

DEFAULT_FP_ROOT = Path(sys.executable).parents[1] / "share" / "kicad" / "footprints"


def mm(x: float, y: float) -> "pcbnew.VECTOR2I":
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def load_fp(fpid: str, fp_paths: list[Path]):
    lib, name = fpid.split(":", 1)
    for root in fp_paths:
        cand = root / f"{lib}.pretty"
        if cand.is_dir():
            fp = pcbnew.FootprintLoad(str(cand), name)
            if fp is not None:
                return fp
    return None


def build(job: dict) -> dict:
    notes: list[str] = []
    fp_paths = [Path(p) for p in job.get("fp_paths", [])] + [DEFAULT_FP_ROOT]
    fp_paths = [p for p in fp_paths if p.is_dir()]

    board = pcbnew.CreateEmptyBoard()
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(int(job["layers"]))
    # JLC-compatible DRC minimums (the .kicad_pro / .kicad_dru refine these).
    ds.m_TrackMinWidth = pcbnew.FromMM(0.1)
    ds.m_ViasMinSize = pcbnew.FromMM(0.4)
    ds.m_MinThroughDrill = pcbnew.FromMM(0.2)
    ds.m_MinClearance = pcbnew.FromMM(0.1)

    nets: dict[str, "pcbnew.NETINFO_ITEM"] = {}

    def net_of(name: str):
        if name not in nets:
            item = pcbnew.NETINFO_ITEM(board, name)
            board.Add(item)
            nets[name] = item
        return nets[name]

    netmap = job["netmap"]
    placed = []
    boxes = []  # (fp, w, h)
    for comp in job["components"]:
        fp = load_fp(comp["fp"], fp_paths)
        if fp is None:
            raise RuntimeError(f"footprint not found: {comp['fp']} (ref {comp['ref']})")
        lib, name = comp["fp"].split(":", 1)
        try:
            fp.SetFPID(pcbnew.LIB_ID(lib, name))
        except Exception as exc:
            notes.append(f"SetFPID {comp['ref']}: {exc}")
        fp.SetReference(comp["ref"])
        fp.SetValue(comp.get("value", ""))
        # Custom symbol fields (LCSC, MPN, ...) must exist on the footprint or
        # `drc --schematic-parity` warns footprint_symbol_field_mismatch.
        for fname, fval in (comp.get("fields") or {}).items():
            fp.SetField(fname, fval)
        for field in fp.GetFields():
            if field.GetName() in (comp.get("fields") or {}):
                field.SetVisible(False)  # metadata, not board art
        board.Add(fp)
        for pad in fp.Pads():
            want = netmap.get(f"{comp['ref']}.{pad.GetNumber()}")
            if want:
                pad.SetNet(net_of(want))
        fp.BuildCourtyardCaches()
        bb = fp.GetBoundingBox(False, False)  # copper+courtyard, no text
        boxes.append((fp, pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())))
        placed.append(comp["ref"])

    # ---- shelf-pack parts so no courtyards overlap --------------------
    margin = float(job.get("margin", 5.0))
    x0 = y0 = 15.0
    n = max(len(boxes), 1)
    total_row_len = sum(w for _, w, _ in boxes) + margin * n
    largest_w = max((w for _, w, _ in boxes), default=30.0)
    rows = max(1, round(n ** 0.5))              # ~square arrangement
    row_limit = max(largest_w, total_row_len / rows)
    x = x0
    y = y0
    row_h = 0.0
    for fp, w, h in boxes:
        if x > x0 and x + w > x0 + row_limit:
            x = x0
            y += row_h + margin
            row_h = 0.0
        bb = fp.GetBoundingBox(False, False)
        ox, oy = pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY())
        px, py = pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y)
        fp.SetPosition(mm(px + (x - ox), py + (y - oy)))
        x += w + margin
        row_h = max(row_h, h)

    # component bounding box after placement
    board.BuildListOfNets()
    comp_bb = pcbnew.BOX2I()
    for fp, _, _ in boxes:
        comp_bb.Merge(fp.GetBoundingBox(False, False))
    cx1, cy1 = pcbnew.ToMM(comp_bb.GetX()), pcbnew.ToMM(comp_bb.GetY())
    cx2 = pcbnew.ToMM(comp_bb.GetRight())
    cy2 = pcbnew.ToMM(comp_bb.GetBottom())

    # ---- outline ------------------------------------------------------
    ol = job.get("outline", {"mode": "auto"})
    if ol.get("mode") == "fixed":
        bw, bh = float(ol["w"]), float(ol["h"])
        ex1 = cx1 - (bw - (cx2 - cx1)) / 2.0
        ey1 = cy1 - (bh - (cy2 - cy1)) / 2.0
        ex2, ey2 = ex1 + bw, ey1 + bh
    else:
        ex1, ey1 = cx1 - margin, cy1 - margin
        ex2, ey2 = cx2 + margin, cy2 + margin
    rect = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_RECT)
    rect.SetStart(mm(ex1, ey1))
    rect.SetEnd(mm(ex2, ey2))
    rect.SetLayer(pcbnew.Edge_Cuts)
    rect.SetWidth(pcbnew.FromMM(0.1))
    board.Add(rect)

    # ---- mounting holes at outline corners ----------------------------
    mh = job.get("mounting_holes")
    if mh and int(mh.get("count", 0)) > 0:
        inset = float(mh.get("inset", margin / 2.0))
        fpid = mh.get("fp", "MountingHole:MountingHole_3.2mm_M3")
        corners = [(ex1 + inset, ey1 + inset), (ex2 - inset, ey1 + inset),
                   (ex2 - inset, ey2 - inset), (ex1 + inset, ey2 - inset)]
        for i, (hx, hy) in enumerate(corners[:int(mh["count"])]):
            hole = load_fp(fpid, fp_paths)
            if hole is None:
                notes.append(f"mounting-hole fp not found: {fpid}")
                break
            lib, name = fpid.split(":", 1)
            try:
                hole.SetFPID(pcbnew.LIB_ID(lib, name))
            except Exception:
                pass
            hole.SetReference(f"H{i + 1}")
            # board_only: mechanical, not in the schematic -> parity must ignore
            # it (else every hole is an "extra_footprint" warning).
            attrs = hole.GetAttributes()
            for flag in ("FP_BOARD_ONLY", "FP_EXCLUDE_FROM_POS_FILES",
                         "FP_EXCLUDE_FROM_BOM"):
                attrs |= getattr(pcbnew, flag, 0)
            hole.SetAttributes(attrs)
            board.Add(hole)
            hole.SetPosition(mm(hx, hy))

    out = Path(job["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    if not board.Save(str(out)):
        raise RuntimeError(f"board.Save failed: {out}")
    return {
        "status": "pass", "out": str(out), "placed": placed,
        "nets": len(nets), "bbox": [round(ex1, 3), round(ey1, 3),
                                    round(ex2, 3), round(ey2, 3)],
        "notes": notes,
    }


def main() -> int:
    try:
        job = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        print(json.dumps(build(job)))
        return 0
    except Exception as exc:
        import traceback
        print(json.dumps({"status": "error", "error": str(exc),
                          "trace": traceback.format_exc()}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
