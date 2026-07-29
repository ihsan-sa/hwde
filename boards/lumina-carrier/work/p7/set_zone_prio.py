"""set_zone_prio.py - bundled-python worker: set assigned priority on zones.

Same-net plane regions that merely TOUCH along a shared edge are flagged
`zones_intersect` by KiCad 10 unless their priorities differ (LEARNINGS
2026-07-23 [kicad-cli][drc][zones]); planes_gen only de-conflicts pairs that
actually overlap, so edge-adjacent regions need this.

usage: <kicad bundled python> set_zone_prio.py job.json
job: {"board": pcb, "out": pcb, "result": out.json,
      "set": [{"net": "GND", "layer": "In1.Cu", "near": [x, y], "priority": 1}]}
`near` matches the zone whose outline bbox min corner is closest to that point.
"""
import json
import sys


def main(job_path):
    import pcbnew
    job = json.load(open(job_path, encoding="utf-8"))
    result_path = job["result"]
    try:
        board = pcbnew.LoadBoard(job["board"])
        zones = []
        for z in board.Zones():
            if z.GetIsRuleArea():
                continue
            bb = z.GetBoundingBox()
            zones.append((z, z.GetNetname(), board.GetLayerName(z.GetLayer()),
                          pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())))
        done = []
        for spec in job["set"]:
            cands = [t for t in zones
                     if t[1] == spec["net"] and t[2] == spec["layer"]]
            if not cands:
                raise ValueError("no zone %s/%s" % (spec["net"], spec["layer"]))
            x, y = spec["near"]
            z, net, lay, zx, zy = min(
                cands, key=lambda t: (t[3] - x) ** 2 + (t[4] - y) ** 2)
            z.SetAssignedPriority(int(spec["priority"]))
            done.append({"net": net, "layer": lay, "bbox_min": [zx, zy],
                         "priority": int(spec["priority"])})
        if not board.Save(job["out"]):
            raise RuntimeError("board.Save failed")
        json.dump({"ok": True, "set": done}, open(result_path, "w",
                                                  encoding="utf-8"))
    except Exception as exc:
        json.dump({"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)},
                  open(result_path, "w", encoding="utf-8"))
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
