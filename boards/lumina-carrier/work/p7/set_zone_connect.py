"""set_zone_connect.py - set pad connection mode on the inner plane zones.

planes_gen leaves KiCad's default THERMAL relief on the pours it creates. On
an inner GND/power PLANE that is wrong twice over: it adds series inductance
to every via drop, and KiCad's `starved_thermal` (min 2 resolved spokes) fires
wherever a pad's relief only resolves one spoke - measured here on U22's
vias-in-pad and on J3/J4's THT ground pins. Solid ("full") connection is the
normal choice for an inner plane and clears both.

usage: <kicad bundled python> set_zone_connect.py job.json
job: {"board": pcb, "out": pcb, "result": out.json,
      "layers": ["In1.Cu", "In2.Cu"], "mode": "full"}
"""
import json
import sys

MODES = {"full": "ZONE_CONNECTION_FULL", "thermal": "ZONE_CONNECTION_THERMAL",
         "none": "ZONE_CONNECTION_NONE",
         "thru_only": "ZONE_CONNECTION_THT_THERMAL"}


def main(job_path):
    import pcbnew
    job = json.load(open(job_path, encoding="utf-8"))
    result_path = job["result"]
    try:
        board = pcbnew.LoadBoard(job["board"])
        mode = getattr(pcbnew, MODES[job.get("mode", "full")])
        layers = set(job["layers"])
        done = []
        for z in board.Zones():
            if z.GetIsRuleArea():
                continue
            name = board.GetLayerName(z.GetLayer())
            if name not in layers:
                continue
            z.SetPadConnection(mode)
            done.append({"net": z.GetNetname(), "layer": name})
        if not board.Save(job["out"]):
            raise RuntimeError("board.Save failed")
        json.dump({"ok": True, "zones": done}, open(result_path, "w",
                                                    encoding="utf-8"))
    except Exception as exc:
        json.dump({"ok": False, "error": "%s: %s" % (type(exc).__name__, exc)},
                  open(result_path, "w", encoding="utf-8"))
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
