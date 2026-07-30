"""READ-ONLY geometry probe via KiCad's own model (board-frame, no transform guessing).

Emits, in board mm:
  footprints[]: ref, x, y, deg, side, pads[] (polygon outline pts, board frame),
                silk[] (polygonized graphic outlines incl. stroke width),
                ref_text: pos, angle, inked bbox w/h (effective text shape),
                          per-angle inked w/h at 0 and 90 deg
  outline[]: board edge polygon(s)
No writes: the board object is mutated in memory only for text-angle probing and
never saved.
"""
import json
import sys

import pcbnew

MAXERR = 5000  # IU = 0.005 mm, matches design_settings max_error
mm = pcbnew.ToMM


def poly_pts(ps):
    out = []
    for i in range(ps.OutlineCount()):
        oc = ps.Outline(i)
        out.append([[round(mm(oc.CPoint(j).x), 4), round(mm(oc.CPoint(j).y), 4)]
                    for j in range(oc.PointCount())])
    return out


def item_poly(item, layer, clearance=0):
    ps = pcbnew.SHAPE_POLY_SET()
    item.TransformShapeToPolygon(ps, layer, clearance, MAXERR,
                                 pcbnew.ERROR_OUTSIDE)
    return poly_pts(ps)


def text_inked(t):
    """Inked (stroke) bbox of the text in board frame -> (cx, cy, w, h)."""
    ps = pcbnew.SHAPE_POLY_SET()
    t.TransformTextToPolySet(ps, 0, MAXERR, pcbnew.ERROR_OUTSIDE)
    bb = ps.BBox()
    return (round(mm(bb.GetCenter().x), 4), round(mm(bb.GetCenter().y), 4),
            round(mm(bb.GetWidth()), 4), round(mm(bb.GetHeight()), 4))


board = pcbnew.LoadBoard(sys.argv[1])
F_SILK = board.GetLayerID("F.Silkscreen")
B_SILK = board.GetLayerID("B.Silkscreen")

fps = []
for fp in board.GetFootprints():
    ref = fp.GetReference()
    pos = fp.GetPosition()
    t = fp.Reference()
    tp = t.GetPosition()
    a0 = t.GetTextAngleDegrees()
    # inked size at 0 and 90 deg (probe by rotating in memory, then restore)
    t.SetTextAngleDegrees(0.0)
    cx0, cy0, w0, h0 = text_inked(t)
    t.SetTextAngleDegrees(90.0)
    cx9, cy9, w90, h90 = text_inked(t)
    t.SetTextAngleDegrees(a0)
    off0 = [round(cx0 - mm(tp.x), 4), round(cy0 - mm(tp.y), 4)]
    off90 = [round(cx9 - mm(tp.x), 4), round(cy9 - mm(tp.y), 4)]
    icx, icy, iw, ih = text_inked(t)
    pads = []
    for p in fp.Pads():
        pp = p.GetPosition()
        lset = p.GetLayerSet().CuStack()
        pads.append({
            "n": p.GetNumber(),
            "x": round(mm(pp.x), 4), "y": round(mm(pp.y), 4),
            "poly": item_poly(p, p.GetPrincipalLayer(), 0),
            "cu": [board.GetLayerName(l) for l in lset],
            "has_mask": p.IsOnLayer(pcbnew.F_Mask) or p.IsOnLayer(pcbnew.B_Mask),
            "on_f_mask": p.IsOnLayer(pcbnew.F_Mask),
        })
    silk = []
    for g in fp.GraphicalItems():
        if g.GetLayer() not in (F_SILK, B_SILK):
            continue
        if isinstance(g, pcbnew.PCB_TEXT) or g.GetClass() in ("PCB_TEXT", "PCB_TEXTBOX"):
            continue
        try:
            silk.append({"cls": g.GetClass(),
                         "layer": board.GetLayerName(g.GetLayer()),
                         "poly": item_poly(g, g.GetLayer(), 0)})
        except Exception as e:  # noqa: BLE001
            silk.append({"cls": g.GetClass(), "err": str(e)})
    fps.append({
        "ref": ref, "name": str(fp.GetFPIDAsString()),
        "x": round(mm(pos.x), 4), "y": round(mm(pos.y), 4),
        "deg": round(fp.GetOrientationDegrees(), 4),
        "side": "back" if fp.IsFlipped() else "front",
        "ref_text": {"text": t.GetText(), "x": round(mm(tp.x), 4),
                     "y": round(mm(tp.y), 4), "angle": round(a0, 3),
                     "layer": board.GetLayerName(t.GetLayer()),
                     "visible": bool(t.IsVisible()),
                     "inked": [icx, icy, iw, ih],
                     "inked_w0": w0, "inked_h0": h0,
                     "inked_w90": w90, "inked_h90": h90,
                     "off0": off0, "off90": off90},
        "pads": pads, "silk": silk,
    })

# board outline
outline = pcbnew.SHAPE_POLY_SET()
board.GetBoardPolygonOutlines(outline, True)
edges = poly_pts(outline)

json.dump({"footprints": fps, "outline": edges},
          open(sys.argv[2], "w", encoding="utf-8"))
print(json.dumps({"footprints": len(fps), "outline_polys": len(edges)}))
