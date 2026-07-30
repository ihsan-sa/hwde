"""READ-ONLY probe: exact refdes text geometry from KiCad itself. Run with KiCad bundled python.
Writes JSON {ref: {w,h,bbox_w,bbox_h,angle,pos}} - no board writes.
"""
import json
import sys

import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
out = {}
for fp in board.GetFootprints():
    ref = fp.GetReference()
    t = fp.Reference()
    tb = t.GetTextBox(None)  # unrotated text box (IU)
    bb = t.GetBoundingBox()  # axis-aligned, includes rotation
    pos = t.GetPosition()
    ent = {
        "text": t.GetText(),
        "angle": round(t.GetTextAngleDegrees(), 3),
        "pos": [round(pcbnew.ToMM(pos.x), 4), round(pcbnew.ToMM(pos.y), 4)],
        "textbox_w": round(pcbnew.ToMM(tb.GetWidth()), 4),
        "textbox_h": round(pcbnew.ToMM(tb.GetHeight()), 4),
        "textbox_cx": round(pcbnew.ToMM(tb.GetCenter().x), 4),
        "textbox_cy": round(pcbnew.ToMM(tb.GetCenter().y), 4),
        "bbox_w": round(pcbnew.ToMM(bb.GetWidth()), 4),
        "bbox_h": round(pcbnew.ToMM(bb.GetHeight()), 4),
        "bbox_cx": round(pcbnew.ToMM(bb.GetCenter().x), 4),
        "bbox_cy": round(pcbnew.ToMM(bb.GetCenter().y), 4),
        "layer": board.GetLayerName(t.GetLayer()),
        "visible": t.IsVisible(),
        "mirrored": t.IsMirrored(),
        "thickness": round(pcbnew.ToMM(t.GetTextThickness()), 4),
        "size": [round(pcbnew.ToMM(t.GetTextWidth()), 4),
                 round(pcbnew.ToMM(t.GetTextHeight()), 4)],
    }
    out[ref] = ent
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), indent=1)
print(json.dumps({"n": len(out)}))
