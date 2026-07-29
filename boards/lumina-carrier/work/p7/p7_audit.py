"""p7_audit.py - one-shot P7 hand-off audit of the routed board.

Runs the checks P8 will run, plus the antenna-keepout copper measurement, and
prints a compact summary. Read-only; writes only its own JSON reports.

usage: python p7_audit.py [board.kicad_pcb]
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SCRIPTS = REPO / ".claude/skills/ai-ee/scripts"
VENV = REPO / ".venv/Scripts/python.exe"
WORK = REPO / "boards/lumina-carrier/work/p7"
BOARD = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    REPO / "boards/lumina-carrier/kicad/lumina-carrier.kicad_pcb")
CONS = REPO / "boards/lumina-carrier/kicad/constraints.json"
DECOUP = REPO / "boards/lumina-carrier/kicad/decoupling.json"

CHECKS = [
    ("check_diffpair", ["--pcb", str(BOARD), "--constraints", str(CONS)]),
    ("check_current", ["--pcb", str(BOARD), "--constraints", str(CONS)]),
    ("check_return_path", ["--pcb", str(BOARD), "--constraints", str(CONS)]),
    ("check_thermal", ["--pcb", str(BOARD), "--constraints", str(CONS)]),
    ("check_creepage", ["--pcb", str(BOARD), "--constraints", str(CONS)]),
    ("check_decoupling", ["--pcb", str(BOARD), "--decoupling", str(DECOUP)]),
]

for name, args in CHECKS:
    out = WORK / ("audit_%s.json" % name)
    cp = subprocess.run([str(VENV), str(SCRIPTS / (name + ".py"))] + args
                        + ["--out", str(out)],
                        capture_output=True, text=True, encoding="utf-8",
                        errors="replace")
    if not out.is_file():
        print("%-20s COULD NOT RUN: %s" % (name, (cp.stderr or "")[-160:]))
        continue
    d = json.loads(out.read_text(encoding="utf-8"))
    c = d.get("counts", {}).get("by_severity", {})
    print("%-20s %-10s errors=%-3s warnings=%-3s"
          % (name, d.get("status"), c.get("error", 0), c.get("warning", 0)))
    for v in d.get("violations", [])[:6]:
        print("      %-8s %s" % (v.get("severity"), v.get("msg", "")[:105]))

print()
subprocess.run([str(VENV), str(WORK / "antenna_check.py"), str(BOARD)])
