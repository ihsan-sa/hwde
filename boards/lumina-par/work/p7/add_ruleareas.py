"""add_ruleareas.py - bundled-python worker: add copper KEEPOUT rule areas.

No pipeline script creates rule areas (planes_gen only makes positive pours),
so this uses the same SWIG mechanism route_swig.py add_zones uses.

usage: <kicad bundled python> add_ruleareas.py job.json
job: {"board": pcb, "out": pcb, "result": out.json,
      "areas": [{"name": str, "rect": [x1,y1,x2,y2] | "poly": [[x,y],...],
                 "layers": ["F.Cu", ...],
                 "no_tracks": true, "no_vias": true, "no_pours": true,
                 "no_pads": false, "no_footprints": false}]}
Result written to job["result"], never stdout (wx noise tears stdout).
"""
import json
import sys


def main(job_path):
    import pcbnew
    job = json.load(open(job_path, encoding="utf-8"))
    result_path = job["result"]
    try:
        board = pcbnew.LoadBoard(job["board"])
        made = []
        for i, a in enumerate(job["areas"]):
            zone = pcbnew.ZONE(board)
            zone.SetIsRuleArea(True)
            zone.SetZoneName(a.get("name", "keepout_%d" % i))
            ls = pcbnew.LSET()
            for lname in a["layers"]:
                lid = board.GetLayerID(str(lname))
                if lid < 0:
                    raise ValueError("unknown layer: %s" % lname)
                ls.AddLayer(lid)
            zone.SetLayerSet(ls)
            zone.SetDoNotAllowTracks(bool(a.get("no_tracks", True)))
            zone.SetDoNotAllowVias(bool(a.get("no_vias", True)))
            zone.SetDoNotAllowZoneFills(bool(a.get("no_pours", True)))
            zone.SetDoNotAllowPads(bool(a.get("no_pads", False)))
            zone.SetDoNotAllowFootprints(bool(a.get("no_footprints", False)))
            pts = a.get("poly")
            if pts is None:
                x1, y1, x2, y2 = a["rect"]
                pts = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
            outline = zone.Outline()
            outline.NewOutline()
            for x, y in pts:
                outline.Append(int(pcbnew.pcbIUScale.mmToIU(float(x))),
                               int(pcbnew.pcbIUScale.mmToIU(float(y))))
            zone.SetIsFilled(False)
            board.Add(zone)
            made.append({"name": zone.GetZoneName(),
                         "layers": list(a["layers"]), "points": len(pts)})
        if not board.Save(job["out"]):
            raise RuntimeError("board.Save failed: %s" % job["out"])
        json.dump({"ok": True, "areas": made, "out": job["out"]},
                  open(result_path, "w", encoding="utf-8"))
    except Exception as exc:
        json.dump({"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)},
                  open(result_path, "w", encoding="utf-8"))
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
