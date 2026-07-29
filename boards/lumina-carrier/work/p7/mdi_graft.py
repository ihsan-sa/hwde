"""mdi_graft.py - graft one branch's MDI copper onto another branch's board.

usage: python mdi_graft.py <base.kicad_pcb> <donor.kicad_pcb> <out.kicad_pcb>
Copies every segment/via of the four MDI nets from <donor> onto a copy of
<base> via route_edit (atomic, verified), then reports the resulting chains.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE))
from mdi_merge import copper_of  # noqa: E402
from mdi_chain import MDI  # noqa: E402

VENV = REPO / ".venv/Scripts/python.exe"
ROUTE_EDIT = REPO / ".claude/skills/ai-ee/scripts/route_edit.py"

base, donor, out = (Path(p).resolve() for p in sys.argv[1:4])
shutil.copy2(base, out)
ops = copper_of(donor, set(MDI))
print("grafting", len(ops), "items from", donor.name)
ops_file = out.parent / (out.stem + "_graft_ops.json")
ops_file.write_text(json.dumps({"version": 1, "ops": ops}), encoding="utf-8")
cp = subprocess.run(
    [str(VENV), str(ROUTE_EDIT), "--pcb", str(out), "--ops", str(ops_file),
     "--out-report", str(out.parent / (out.stem + "_graft.json"))],
    capture_output=True, text=True, encoding="utf-8", errors="replace")
print((cp.stdout or cp.stderr)[-500:])
