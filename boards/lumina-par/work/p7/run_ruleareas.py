"""Driver: add the ICD s7.6 antenna-column copper keepout as a KiCad rule area.

No pipeline script creates rule areas (planes_gen only makes positive pours),
so this drives the bundled-python SWIG worker through routelib.run_worker,
exactly as planes_gen/route_edit drive theirs.

Run with the repo venv python.  usage: run_ruleareas.py <job.json>
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(r"C:\dev\ai-ee3")
SCRIPTS = ROOT / ".claude" / "skills" / "ai-ee" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))
from lib import env, routelib, geom  # noqa: E402

WORKER = Path(__file__).with_name("add_ruleareas.py")


def main(job_path):
    job = json.loads(Path(job_path).read_text(encoding="utf-8"))
    pcb = Path(job["board"])
    cli = env.find_kicad_cli()
    bp = env.find_kicad_python(cli) if cli else None
    if bp is None:
        raise SystemExit("KiCad bundled python not found (env.py)")

    stage = Path(tempfile.mkdtemp(prefix=".aiee_ra_", dir=str(pcb.parent)))
    try:
        staged = stage / pcb.name
        shutil.copy2(pcb, staged)
        res = routelib.run_worker(
            bp, {"board": str(staged), "out": str(staged),
                 "areas": job["areas"]},
            stage, worker=WORKER)
        # verify the areas landed before swapping the real board
        after = geom.BoardGeom.from_file(staged)
        got = [{"name": ra["name"], "layers": sorted(ra["layers"]),
                "bounds": [round(v, 3) for v in ra["outline"].bounds]}
               for ra in after.rule_areas]
        if len(got) < len(job["areas"]):
            raise SystemExit("rule areas missing after save: %r" % got)
        staged.replace(pcb)
        print(json.dumps({"ok": True, "added": res["areas"],
                          "rule_areas_on_board": got}, indent=1))
    finally:
        shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1])
