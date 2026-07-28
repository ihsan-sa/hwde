"""place_swig - BUNDLED-python SWIG worker for place_edit.py (S9).

Runs inside KiCad's bundled python (the only interpreter with pcbnew); invoked
as `python place_swig.py job.json` by the venv driver. stdlib only.

job JSON: {"board": in_path, "out": out_path, "ops": [op, ...]}
ops are ABSOLUTE (idempotent by construction - re-applying is a no-op):
  {"op": "place",  "ref": R, "x": mm, "y": mm, ["deg": d], ["side": front|back]}
  {"op": "move",   "ref": R, "x": mm, "y": mm}
  {"op": "rotate", "ref": R, "deg": d}
  {"op": "flip",   "ref": R, "side": "front"|"back"}   # absolute side, not toggle
  {"op": "lock",   "ref": R, "locked": true|false}
Text ops (S14, closes V17 - silk labels/refdes moves were previously
unscriptable):
  {"op": "add_text",  "text": T, "x": mm, "y": mm, "layer": "F.SilkS",
   ["deg": d], ["size": mm], ["thickness": mm]}
     - board-frame graphic text. Idempotent: an existing text with the same
       string on the same layer within 0.01 mm is UPDATED, never duplicated.
  {"op": "move_text", "ref": R, "field": "reference"|"value", "x": mm,
   "y": mm, ["deg": d]}
     - repositions a footprint's Reference/Value field text (board frame;
       stored angle is ABSOLUTE per LEARNINGS [geometry]).

The board is saved ONLY if every op applied; any failure exits 3 with a JSON
error and writes nothing (the driver treats the staged copy as garbage).
Save() may drop a default .kicad_pro next to `out` - the driver stages in a
scratch dir and moves only the .kicad_pcb back, so real project files are
never clobbered. mm->IU uses pcbIUScale.mmToIU (FromMM truncates: prior-
attempt fact, e.g. 32.3 mm -> 32299999 nm).
"""
import json
import sys

import pcbnew


def iu(mm: float) -> int:
    return int(pcbnew.pcbIUScale.mmToIU(float(mm)))


def side_of(fp) -> str:
    return "back" if fp.GetLayer() == pcbnew.B_Cu else "front"


def set_side(fp, want: str) -> None:
    if side_of(fp) != want:
        try:
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFTRIGHT)
        except AttributeError:  # 10.0.3 SWIG has no enum; bool = left/right
            fp.Flip(fp.GetPosition(), True)


def _layer_id(board, name: str) -> int:
    lid = board.GetLayerID(name)
    if lid < 0:
        raise KeyError(f"unknown layer '{name}'")
    return lid


def apply_text_op(board, op: dict) -> dict:
    kind = op["op"]
    if kind == "add_text":
        lid = _layer_id(board, op["layer"])
        tol = iu(0.01)
        txt = None
        for d in board.GetDrawings():
            if (isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == lid
                    and d.GetText() == op["text"]
                    and abs(d.GetPosition().x - iu(op["x"])) <= tol
                    and abs(d.GetPosition().y - iu(op["y"])) <= tol):
                txt = d          # idempotent re-apply: update, don't duplicate
                break
        if txt is None:
            txt = pcbnew.PCB_TEXT(board)
            board.Add(txt)
        txt.SetText(op["text"])
        txt.SetLayer(lid)
        txt.SetPosition(pcbnew.VECTOR2I(iu(op["x"]), iu(op["y"])))
        if op.get("deg") is not None:
            txt.SetTextAngleDegrees(float(op["deg"]))
        size = float(op.get("size", 1.0))
        txt.SetTextSize(pcbnew.VECTOR2I(iu(size), iu(size)))
        txt.SetTextThickness(iu(float(op.get("thickness", 0.15))))
        if op["layer"].startswith("B."):
            txt.SetMirrored(True)
        pos = txt.GetPosition()
        return {"text": op["text"], "layer": op["layer"],
                "x": round(pcbnew.ToMM(pos.x), 6),
                "y": round(pcbnew.ToMM(pos.y), 6),
                "deg": round(txt.GetTextAngleDegrees(), 4)}
    if kind == "move_text":
        fp = board.FindFootprintByReference(op["ref"])
        if fp is None:
            raise KeyError(f"footprint '{op['ref']}' not on board")
        item = fp.Reference() if op["field"] == "reference" else fp.Value()
        item.SetPosition(pcbnew.VECTOR2I(iu(op["x"]), iu(op["y"])))
        if op.get("deg") is not None:
            item.SetTextAngleDegrees(float(op["deg"]))
        pos = item.GetPosition()
        return {"ref": op["ref"], "field": op["field"],
                "x": round(pcbnew.ToMM(pos.x), 6),
                "y": round(pcbnew.ToMM(pos.y), 6),
                "deg": round(item.GetTextAngleDegrees(), 4)}
    raise KeyError(f"unknown text op '{kind}'")


def apply_op(board, op: dict) -> dict:
    kind = op["op"]
    if kind in ("add_text", "move_text"):
        return apply_text_op(board, op)
    ref = op["ref"]
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        raise KeyError(f"footprint '{ref}' not on board")
    if kind in ("place", "move"):
        fp.SetPosition(pcbnew.VECTOR2I(iu(op["x"]), iu(op["y"])))
    if kind == "place" and op.get("side") is not None:
        set_side(fp, op["side"])
    if kind in ("place", "rotate") and op.get("deg") is not None:
        fp.SetOrientationDegrees(float(op["deg"]))
    if kind == "flip":
        set_side(fp, op["side"])
    if kind == "lock":
        fp.SetLocked(bool(op["locked"]))
    pos = fp.GetPosition()
    return {"ref": ref,
            "x": round(pcbnew.ToMM(pos.x), 6), "y": round(pcbnew.ToMM(pos.y), 6),
            "deg": round(fp.GetOrientationDegrees(), 4),
            "side": side_of(fp), "locked": fp.IsLocked()}


def main() -> int:
    job = json.loads(open(sys.argv[1], encoding="utf-8").read())
    board = pcbnew.LoadBoard(job["board"])
    results = []
    for i, op in enumerate(job["ops"]):
        try:
            results.append(apply_op(board, op))
        except Exception as e:  # no save on ANY failure
            print(json.dumps({"ok": False, "index": i,
                              "error": f"{type(e).__name__}: {e}"}))
            return 3
    if not board.Save(job["out"]):
        print(json.dumps({"ok": False, "index": None,
                          "error": f"board.Save failed: {job['out']}"}))
        return 3
    print(json.dumps({"ok": True, "results": results}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
