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


def apply_op(board, op: dict) -> dict:
    ref = op["ref"]
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        raise KeyError(f"footprint '{ref}' not on board")
    kind = op["op"]
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
